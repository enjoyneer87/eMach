# -*- coding: utf-8 -*-
"""e10 Icepak 커플드 network transient — 온도 모니터 심고 FRESH 솔브 후 solution-data로 추출.
헤드리스 필드 후처리 6종 실패 -> Maxwell식 monitor/solution-data 경로. 네트워크 재구성 포함
(엔드팁삭제+오일회로+transient) -> 모니터 -> fresh 솔브(모니터 기록) -> get_solution_data(Monitor)."""
import os, json, inspect, traceback, tempfile
LOG = os.environ.get("M2_LOG", os.path.join(tempfile.gettempdir(), "icepak_mon2.txt"))
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_icepak_network_transient_temps.json"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
DESIGN = "e10_net"; CORES = 16
HTC_JKT, HTC_SPRAY = 1000.0, 2000.0
G_FLOW_JKT, G_FLOW_SPRAY = 132.0, 88.0
C_JKT, C_SPRAY, CP_OIL, OIL_T = 330.0, 248.0, 2000.0, 70.0
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()
from ansys.aedt.core.modules.boundary.icepak_boundary import NetworkObject
def _cf(self, arg):
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
NetworkObject._clean_list = _cf
def mesherr(ipk):
    try: m = ipk.odesktop.GetMessages(ipk.project_name, ipk.design_name, 2) or []
    except Exception: m = []
    return [x for x in m if any(s in x for s in ("Invalid Body", "terminated unexpectedly", "BodyCache"))]

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
    P("opened", ipk.solution_type)
    oed = ipk.modeler.oeditor
    et = list(oed.GetMatchedObjectName("*EndTip*"))
    if et: oed.Delete(["NAME:Selections", "Selections:=", ",".join(et)]); P("endtips del", len(et))

    # rebuild oil network (idempotent: delete old walls/net if present)
    wf = {b.name: [int(x) for x in b.props.get("Faces", [])]
          for b in ipk.boundaries if b.name in ("cool_jacket", "cool_spray")}
    if wf:
        jf, sf = wf["cool_jacket"], wf["cool_spray"]
        fa = lambda f: (float(ipk.modeler.get_face_area(f)) / 1e6) or 1e-6
        for b in list(ipk.boundaries):
            if b.name in ("cool_jacket", "cool_spray"):
                try: b.delete()
                except Exception: pass
        net = ipk.create_network_object(name="OilCircuit")
        net.add_boundary_node("OIL", "Temperature", OIL_T)
        net.add_internal_node("JACKET", 0.0, mass=C_JKT / CP_OIL, specific_heat=CP_OIL)
        net.add_internal_node("SPRAY", 0.0, mass=C_SPRAY / CP_OIL, specific_heat=CP_OIL)
        net.add_face_node(jf[0], name="JKTf", thermal_resistance="Specified", resistance=float(1.0 / (HTC_JKT * fa(jf[0]))))
        for i, f in enumerate(sf):
            net.add_face_node(f, name=f"SPf{i}", thermal_resistance="Specified", resistance=float(1.0 / (HTC_SPRAY * fa(f))))
        net.add_link("JKTf", "JACKET", 1e-6)
        for i in range(len(sf)): net.add_link(f"SPf{i}", "SPRAY", 1e-6)
        net.add_link("JACKET", "OIL", float(1.0 / G_FLOW_JKT))
        net.add_link("SPRAY", "OIL", float(1.0 / G_FLOW_SPRAY))
        net.create(); P("network rebuilt present:", "OilCircuit" in [b.name for b in ipk.boundaries])
    else:
        P("walls absent (network already there):", "OilCircuit" in [b.name for b in ipk.boundaries])

    # ensure transient setup
    if "SolveTrans" not in ipk.setup_names:
        ipk.solution_type = "Transient"
        try: ipk.delete_setup("SolveNet")
        except Exception: pass
        st = ipk.create_setup(name="SolveTrans")
        if not hasattr(st, "props"): st = ipk.get_setup("SolveTrans")
        st.props["Stop Time"] = "900s"; st.props["Time Step"] = "45s"
        st.props["Solution Initialization - Temperature"] = "70cel"; st.update()
    P("setups", ipk.setup_names, "soltype", ipk.solution_type)

    # temperature monitors in representative objects
    roles = {"coil": [], "stator": [], "rotor": [], "magnet": [], "shaft": []}
    for o in ipk.modeler.object_names:
        try: mat = (ipk.modeler[o].material_name or "").lower()
        except Exception: mat = ""
        for r in roles:
            if r in mat or r in o.lower(): roles[r].append(o); break
    monnames = []
    for r, objs in roles.items():
        for i, o in enumerate(objs[:6] if r == "coil" else objs[:1]):
            try:
                nm = ipk.assign_point_monitor_in_object(o, monitor_quantity="Temperature", monitor_name=f"m_{r}_{i}")
                monnames.append((nm if isinstance(nm, str) else f"m_{r}_{i}", r))
            except Exception as e: P("mon fail", o, repr(e)[:50])
    P("monitors", len(monnames))
    ipk.save_project()

    # FRESH solve: force by re-mesh (invalidates) then analyze
    if mesherr(ipk): P("VERDICT: MESH-FAIL"); raise SystemExit
    P("meshing+solving (fresh, with monitors)...")
    ipk.odesign.GenerateMesh("SolveTrans")
    if mesherr(ipk): P("VERDICT: MESH-FAIL"); raise SystemExit
    try: ipk.analyze_setup("SolveTrans", cores=CORES)
    except TypeError: ipk.analyze_setup("SolveTrans", num_cores=CORES)
    P("analyze done"); ipk.save_project()

    # read monitors via solution-data (robust: all categories)
    sol = list(ipk.existing_analysis_sweeps)[0]
    post = ipk.post
    role_vals = {}
    try:
        cats = post.available_report_types or ["Monitor"]
    except Exception: cats = ["Monitor"]
    for cat in cats:
        try: qs = post.available_report_quantities(report_category=cat, solution=sol) or []
        except Exception: qs = []
        tqs = [q for q in qs if q.startswith("m_") or "Temperature" in q]
        if tqs: P(f"cat {cat} temp-mon quantities:", tqs[:15])
        for q in tqs:
            try:
                d = post.get_solution_data(expressions=[q], setup_sweep_name=sol, report_category=cat)
                vals = d.data_real(q) if (d and hasattr(d, "data_real")) else None
                v = float(vals[-1]) if vals else None
                r = next((rr for rr in roles if f"_{rr}_" in q or q.startswith("m_" + rr)), None)
                if r and v is not None:
                    role_vals.setdefault(r, []).append(v); P(f"  {q}={v}")
            except Exception as e: P("  rd EXC", q, repr(e)[:50])
    temps = {r: {"point_max_C": round(max(v), 2), "n": len(v)} for r, v in role_vals.items() if v}
    P("TEMPS:", temps)

    base = json.load(open(OUTJSON, encoding="utf-8")) if os.path.exists(OUTJSON) else {}
    if temps: base["per_part_pointmon"] = temps
    base["_extract"] = "point monitors fresh-solve get_solution_data"
    json.dump(base, open(OUTJSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    P("wrote ok=" + str(bool(temps)))
    ipk.release_desktop(close_projects=True, close_desktop=True)
except SystemExit: pass
except Exception:
    P("FATAL:\n" + traceback.format_exc())
finally:
    try:
        if ipk is not None: ipk.release_desktop(close_projects=True, close_desktop=True)
    except Exception: pass
    log.close(); os._exit(0)
