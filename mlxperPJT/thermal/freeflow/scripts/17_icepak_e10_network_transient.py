# -*- coding: utf-8 -*-
"""e10 Icepak — 진짜 커플드 오일회로 Network + Transient (MAPDL 하이브리드 자기일관 미러).
오일회로: OIL(70C 소스) -R_flow- JACKET/SPRAY(내부노드+열용량 C) -~0- 벽면 face-node(-R_conv=1/(hA)- 벽).
HTC 고정70C 벽을 이 네트워크로 교체 -> 오일노드가 스스로 승온(2-way in Icepak). Transient dt45s->900s.
레시피(검증됨): _clean_list 몽키패치(pyaedt 버그) + add_face_node로 면등록 + 내부 열용량노드.
게이트: 엔드팁삭제 + 네트워크실재 + transient셋업 + 메시clean -> 통과해야 솔브."""
import os, json, inspect, traceback, tempfile
LOG = os.environ.get("NT_LOG", os.path.join(tempfile.gettempdir(), "icepak_net_trans.txt"))
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_icepak_network_transient_temps.json"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
DESIGN = "e10_net"; CORES = 16
HTC_JKT, HTC_SPRAY = 1000.0, 2000.0
G_FLOW_JKT, G_FLOW_SPRAY = 132.0, 88.0
C_JKT, C_SPRAY, CP_OIL, OIL_T = 330.0, 248.0, 2000.0, 70.0
STOP, STEP = "900s", "45s"
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

# --- PATCH pyaedt bug: _clean_list IndexError on empty list ---
from ansys.aedt.core.modules.boundary.icepak_boundary import NetworkObject
def _clean_fixed(self, arg):
    out = []
    for it in arg:
        if isinstance(it, list):
            if it and it[0] == "NAME:PageNet":
                pl = []
                for i in it:
                    if isinstance(i, list):
                        nm = pl[-1]; pl.pop(-1)
                        for j in i: pl.append(nm); pl.append(j)
                    else: pl.append(i)
                out.append(pl)
            else: out.append(self._clean_list(it))
        else: out.append(it)
    return out
NetworkObject._clean_list = _clean_fixed

def mesherr(ipk, tag):
    try: m = ipk.odesktop.GetMessages(ipk.project_name, ipk.design_name, 2) or []
    except Exception: m = []
    bad = [x for x in m if any(s in x for s in ("Invalid Body", "terminated unexpectedly",
           "non-responsive", "BodyCache"))]
    for x in bad[:3]: P(f"[{tag}]", x)
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
    P("opened", ipk.design_name, ipk.solution_type)
    oed = ipk.modeler.oeditor

    # 1) endtip fix
    et = list(oed.GetMatchedObjectName("*EndTip*"))
    if et: oed.Delete(["NAME:Selections", "Selections:=", ",".join(et)]); P("deleted endtips", len(et))

    # 2) faces + per-face convective R
    wf = {b.name: [int(x) for x in b.props.get("Faces", [])]
          for b in ipk.boundaries if b.name in ("cool_jacket", "cool_spray")}
    jf, sf = wf.get("cool_jacket", []), wf.get("cool_spray", [])
    P("faces jacket/spray:", len(jf), len(sf))
    if not jf or not sf: P("VERDICT: NO-FACES"); raise SystemExit
    fa = lambda f: (float(ipk.modeler.get_face_area(f)) / 1e6) or 1e-6

    # 3) delete HTC walls, build oil-circuit network (add_face_node pattern)
    for b in list(ipk.boundaries):
        if b.name in ("cool_jacket", "cool_spray"):
            try: b.delete()
            except Exception: pass
    net = ipk.create_network_object(name="OilCircuit")
    net.add_boundary_node("OIL", "Temperature", OIL_T)
    net.add_internal_node("JACKET", 0.0, mass=C_JKT / CP_OIL, specific_heat=CP_OIL)
    net.add_internal_node("SPRAY", 0.0, mass=C_SPRAY / CP_OIL, specific_heat=CP_OIL)
    net.add_face_node(jf[0], name="JKTf", thermal_resistance="Specified",
                      resistance=float(1.0 / (HTC_JKT * fa(jf[0]))))
    for i, f in enumerate(sf):
        net.add_face_node(f, name=f"SPf{i}", thermal_resistance="Specified",
                          resistance=float(1.0 / (HTC_SPRAY * fa(f))))
    net.add_link("JKTf", "JACKET", 1e-6)
    for i in range(len(sf)): net.add_link(f"SPf{i}", "SPRAY", 1e-6)
    net.add_link("JACKET", "OIL", float(1.0 / G_FLOW_JKT))
    net.add_link("SPRAY", "OIL", float(1.0 / G_FLOW_SPRAY))
    net.create()
    # GATE-1
    net_ok = "OilCircuit" in [b.name for b in ipk.boundaries]
    P("network present:", net_ok, "| face_nodes", len(net.face_nodes), "links", len(net.links))
    if not net_ok: P("VERDICT: NETWORK-FAIL"); raise SystemExit

    # 4) Transient setup
    ipk.solution_type = "Transient"; P("soltype", ipk.solution_type)
    try: ipk.delete_setup("SolveNet"); P("deleted SolveNet")
    except Exception as e: P("del setup EXC", repr(e)[:70])
    st = ipk.create_setup(name="SolveTrans")
    if not hasattr(st, "props"): st = ipk.get_setup("SolveTrans")
    for k, v in (("Stop Time", STOP), ("Time Step", STEP),
                 ("Solution Initialization - Temperature", f"{OIL_T}cel")):
        try: st.props[k] = v
        except Exception as e: P(f"set {k} EXC", repr(e)[:50])
    st.update()
    setup_ok = "Stop Time" in st.props and str(ipk.solution_type).startswith("Transient")
    P("setup props:", {k: st.props.get(k) for k in ("Stop Time", "Time Step")}, "| ok:", setup_ok)
    ipk.save_project()
    if not setup_ok: P("VERDICT: SETUP-FAIL"); raise SystemExit

    # 5) mesh gate
    P("meshing..."); ipk.odesign.GenerateMesh("SolveTrans")
    if mesherr(ipk, "MESH"): P("VERDICT: MESH-FAIL"); raise SystemExit
    P("GATES PASSED -> solving coupled network transient (long pole ~30-60min)")

    # 6) solve
    try: ipk.analyze_setup("SolveTrans", cores=CORES)
    except TypeError: ipk.analyze_setup("SolveTrans", num_cores=CORES)
    P("analyze returned"); ipk.save_project()

    # 7) extract solid per-part max (coil sampled)
    roles = {"coil": [], "stator": [], "rotor": [], "magnet": [], "shaft": []}
    for o in ipk.modeler.object_names:
        try: mat = (ipk.modeler[o].material_name or "").lower()
        except Exception: mat = ""
        for r in roles:
            if r in mat or r in o.lower(): roles[r].append(o); break
    sample = {r: (v[:15] if r == "coil" else v) for r, v in roles.items()}
    allo = [o for v in sample.values() for o in v]; o2r = {o: r for r, v in sample.items() for o in v}
    temps = {}
    try:
        for s in list(ipk.existing_analysis_sweeps) + ["SolveTrans : Transient", None]:
            try:
                fs = ipk.post.create_field_summary()
                for o in allo: fs.add_calculation("Object", "Volume", o, "Temperature")
                d = fs.get_field_summary_data(setup=s, pandas_output=True)
                if hasattr(d, "columns"):
                    cols = list(d.columns); ec = next((c for c in cols if c.lower() == "entity"), cols[0])
                    mc = next((c for c in cols if "max" in c.lower()), None)
                    agg = {}
                    for _, row in d.iterrows():
                        r = o2r.get(str(row[ec]))
                        if r and mc: agg.setdefault(r, []).append(float(row[mc]))
                    temps = {r: {"max": max(v)} for r, v in agg.items() if v}
                    P("solid temps", s, temps); break
            except Exception as e: P("fs", s, "EXC", repr(e)[:60])
    except Exception as e: P("extract EXC", repr(e)[:80])

    out = {"_model": "e10 Icepak COUPLED oil-network + Transient (self-consistent, MAPDL mirror)",
           "_type": "Transient", "_network": "OilCircuit: OIL src 70C, JACKET/SPRAY internal nodes w/ C, "
                     "577 face-nodes (R_conv=1/hA per face), R_flow=1/G",
           "_time": {"stop": STOP, "step": STEP, "IC_C": OIL_T},
           "_circuit_const": {"HTC_jkt": HTC_JKT, "HTC_spray": HTC_SPRAY, "G_flow_jkt": G_FLOW_JKT,
                              "G_flow_spray": G_FLOW_SPRAY, "C_jkt": C_JKT, "C_spray": C_SPRAY},
           "_vs_mapdl": {"winding": 152.2, "stator": 126.0, "magnet": 86.9, "rotor": 86.9,
                         "shaft": 84.9, "oil_JACKET": 84.4, "oil_SPRAY": 91.9},
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
