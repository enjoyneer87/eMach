# -*- coding: utf-8 -*-
"""e10 Icepak Transient (회로 커플드, 1-way MAPDL 회로->Icepak).
MAPDL 하이브리드 미러: HTC벽 Ref Temp = MAPDL 오일회로 노드온도(JACKET84.4/SPRAY91.9),
Transient(IC70C, dt45s->900s, 손실 상수). 엔드팁 재삭제 + 셋업/메시 게이트 후 솔브.
게이트 실패 시 솔브 전 중단(40분 낭비 방지)."""
import os, json, inspect, traceback, tempfile
LOG = os.environ.get("TR_LOG", os.path.join(tempfile.gettempdir(), "icepak_transient.txt"))
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_icepak_transient_temps.json"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
DESIGN = "e10_net"; CORES = 16
JACKET_T, SPRAY_T, OIL_IC = 84.4, 91.9, 70.0
STOP, STEP = "900s", "45s"
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

def errs(ipk, tag):
    try: m = ipk.odesktop.GetMessages(ipk.project_name, ipk.design_name, 2) or []
    except Exception: m = []
    bad = [x for x in m if ("Invalid Body" in x or "terminated unexpectedly" in x
                            or "non-responsive" in x or "BodyCache" in x)]
    for x in bad[:4]: P(f"[{tag}] {x}")
    return bad

ipk = None
try:
    from ansys.aedt.core import Icepak
    sig = inspect.signature(Icepak.__init__).parameters
    kw = dict(non_graphical=True)
    kw["project" if "project" in sig else "projectname"] = PROJ
    kw["design" if "design" in sig else "designname"] = DESIGN
    kw["version" if "version" in sig else "specified_version"] = "2026.1"
    kw["new_desktop" if "new_desktop" in sig else "new_desktop_session"] = True
    ipk = Icepak(**kw)
    P("opened", ipk.design_name, "soltype", ipk.solution_type)
    oed = ipk.modeler.oeditor

    # 1) re-delete endtips (UDP가 open시 재생성될 수 있음)
    et = list(oed.GetMatchedObjectName("*EndTip*"))
    if et:
        oed.Delete(["NAME:Selections", "Selections:=", ",".join(et)])
        P("deleted endtips:", len(et))
    else:
        P("no endtips (already clean)")

    # 2) HTC 벽 Reference Temperature = MAPDL 회로 노드온도 (1-way 회로 커플)
    for b in ipk.boundaries:
        if b.name == "cool_jacket":
            b.props["Reference Temperature"] = f"{JACKET_T}cel"; b.update(); P("cool_jacket RefT ->", JACKET_T)
        elif b.name == "cool_spray":
            b.props["Reference Temperature"] = f"{SPRAY_T}cel"; b.update(); P("cool_spray RefT ->", SPRAY_T)

    # 3) design -> Transient, create transient setup
    try:
        ipk.solution_type = "Transient"; P("solution_type set Transient")
    except Exception as e:
        P("set solution_type EXC", repr(e)[:120])
    # remove old steady setup name clash; create transient
    stp = None
    for stype in ("TransientTemperatureAndFlow", "Transient",
                  "TransientTemperatureOnly"):
        try:
            stp = ipk.create_setup(name="SolveTrans", setup_type=stype)
            P("created setup type", stype); break
        except Exception as e:
            P(f"create_setup {stype} EXC", repr(e)[:100])
    if stp is None:
        P("VERDICT: SETUP-FAIL (no transient setup)"); raise SystemExit
    # set transient time controls (여러 키 후보)
    for k, v in (("Stop Time", STOP), ("Time Step", STEP),
                 ("Solution Initialization - Temperature", f"{OIL_IC}cel"),
                 ("Convergence Criteria - Max Iterations", 20)):
        try: stp.props[k] = v
        except Exception as e: P(f"set {k} EXC", repr(e)[:60])
    try: stp.update(); P("setup updated")
    except Exception as e: P("setup.update EXC", repr(e)[:100])

    # 4) GATE-A: verify transient props
    pk = {k: stp.props.get(k) for k in ("SetupType", "Stop Time", "Time Step",
          "Solution Initialization - Temperature") if k in stp.props}
    P("setup props:", pk)
    ok_setup = ("Stop Time" in stp.props) or ("Transient" in str(ipk.solution_type))
    P("GATE-A transient setup ok:", ok_setup, "| soltype", ipk.solution_type)
    ipk.save_project()

    # 5) GATE-B: mesh clean
    P("generating mesh...")
    rc = ipk.odesign.GenerateMesh("SolveTrans")
    P("GenerateMesh rc", rc)
    if errs(ipk, "MESH"):
        P("VERDICT: MESH-FAIL"); raise SystemExit
    if not ok_setup:
        P("VERDICT: SETUP-UNVERIFIED (not solving)"); raise SystemExit
    P("GATES PASSED -> solving transient")

    # 6) solve
    try: ipk.analyze_setup("SolveTrans", cores=CORES)
    except TypeError: ipk.analyze_setup("SolveTrans", num_cores=CORES)
    P("analyze returned"); errs(ipk, "SOLVE"); ipk.save_project()

    # 7) light extraction (coil sampled to avoid 148-obj hang)
    roles = {"coil": [], "stator": [], "rotor": [], "magnet": [], "shaft": []}
    for o in ipk.modeler.object_names:
        try: mat = (ipk.modeler[o].material_name or "").lower()
        except Exception: mat = ""
        for r in roles:
            if r in mat or r in o.lower(): roles[r].append(o); break
    sample = {r: (v[:20] if r == "coil" else v) for r, v in roles.items()}
    allo = [o for v in sample.values() for o in v]
    P("extract objs:", {r: len(v) for r, v in sample.items()})
    temps = {}
    try:
        sweeps = list(ipk.existing_analysis_sweeps)
        P("sweeps", sweeps)
        for s in sweeps + ["SolveTrans : Transient", None]:
            try:
                fs = ipk.post.create_field_summary()
                for o in allo: fs.add_calculation("Object", "Volume", o, "Temperature")
                d = fs.get_field_summary_data(setup=s, pandas_output=True)
                if hasattr(d, "columns"):
                    cols = list(d.columns)
                    ec = next((c for c in cols if c.lower() == "entity"), cols[0])
                    mc = next((c for c in cols if "max" in c.lower()), None)
                    o2r = {o: r for r, v in sample.items() for o in v}
                    agg = {}
                    for _, row in d.iterrows():
                        r = o2r.get(str(row[ec]))
                        if r and mc: agg.setdefault(r, []).append(float(row[mc]))
                    temps = {r: {"max": max(v)} for r, v in agg.items() if v}
                    P("temps setup", s, temps); break
            except Exception as e:
                P("fs", s, "EXC", repr(e)[:80])
    except Exception as e:
        P("extract EXC", repr(e)[:120])

    out = {"_model": "e10 Icepak Transient (circuit-coupled 1-way MAPDL)",
           "_type": "Transient", "_time": {"stop": STOP, "step": STEP, "IC_C": OIL_IC},
           "_cooling_refT": {"jacket": JACKET_T, "spray": SPRAY_T, "src": "MAPDL oil-circuit nodes"},
           "_loss_W": {"coil": 3350, "stator": 585, "rotor": 65, "magnet": 24},
           "_vs_mapdl": {"winding": 152.2, "stator": 126.0, "magnet": 86.9, "rotor": 86.9, "shaft": 84.9},
           "per_part_max": temps}
    json.dump(out, open(OUTJSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    P("wrote", OUTJSON, "| VERDICT: SOLVED ok=" + str(bool(temps)))
except SystemExit:
    pass
except Exception:
    P("FATAL:\n" + traceback.format_exc())
finally:
    try:
        if ipk is not None: ipk.release_desktop(close_projects=True, close_desktop=True)
    except Exception: pass
    log.close(); os._exit(0)
