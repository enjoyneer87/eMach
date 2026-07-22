# -*- coding: utf-8 -*-
"""e10 Icepak abort 수정 + 재솔브.
근본원인(진단 확정): 헤어핀 코일 엔드팁 18개(Ph1_P1_C*_EndTip)가 Invalid Body ID(-1)
= degenerate 지오메트리 → Icepak COM 메셔 크래시 → 해 0개.
수정: 엔드팁 바디 삭제(코일 손실은 나머지 코일 바디가 유지) → 재메시 → (메시 정상 확인시)
재솔브 → 부품별 온도 추출 → freeflow/data/e10_icepak_temps.json.
솔브는 무거움(GPU/CPU OK). 메시가 여전히 크래시하면 솔브 전에 중단."""
import os, sys, json, inspect, traceback, tempfile

LOG = os.environ.get("ICEPAK_LOG", os.path.join(tempfile.gettempdir(), "icepak_resolve.txt"))
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_icepak_temps.json"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
DESIGN = "e10_net"; SETUP = "SolveNet"; CORES = 16

log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

def open_icepak():
    from ansys.aedt.core import Icepak
    sig = inspect.signature(Icepak.__init__).parameters
    kw = dict(non_graphical=True)
    kw["project" if "project" in sig else "projectname"] = PROJ
    kw["design" if "design" in sig else "designname"] = DESIGN
    if "version" in sig: kw["version"] = "2026.1"
    elif "specified_version" in sig: kw["specified_version"] = "2026.1"
    if "new_desktop" in sig: kw["new_desktop"] = True
    elif "new_desktop_session" in sig: kw["new_desktop_session"] = True
    return Icepak(**kw)

def errs(ipk, tag):
    """return list of error(sev2) messages"""
    try:
        m = ipk.odesktop.GetMessages(ipk.project_name, ipk.design_name, 2) or []
    except Exception as e:
        P(f"[{tag}] GetMessages EXC {repr(e)[:120]}"); return []
    for x in m: P(f"[{tag}][err] {x}")
    return list(m)

ipk = None
try:
    ipk = open_icepak()
    P("OPENED", ipk.design_name, "| setups", ipk.setup_names)
    oed = ipk.modeler.oeditor
    allobj = list(ipk.modeler.object_names)
    P("n objects (open):", len(allobj))
    # structure dump for fix design
    try:
        udc = list(ipk.modeler.user_defined_component_names)
        P("user_defined_components:", len(udc), udc[:10])
    except Exception as e:
        P("udc EXC", repr(e)[:100])
    try:
        allmatch = list(oed.GetMatchedObjectName("*"))
        P("oEditor GetMatchedObjectName(*):", len(allmatch))
        coilish = [n for n in allmatch if ("Ph" in n or "Coil" in n or "Tip" in n or "Hairpin" in n)]
        P("  coil/hairpin/tip-like names:", len(coilish), coilish[:12])
    except Exception as e:
        P("GetMatchedObjectName(*) EXC", repr(e)[:120])

    # --- locate degenerate hairpin end-tip bodies via native matcher ---
    endtips = []
    for pat in ("*EndTip*", "*_EndTip", "*EndTip"):
        try:
            m = list(oed.GetMatchedObjectName(pat))
            if m: endtips = m; P(f"matched {pat}:", len(m), m[:6]); break
        except Exception as e:
            P(f"match {pat} EXC", repr(e)[:80])
    endtips = sorted(set(endtips))
    P("endtips to delete:", len(endtips))

    # coil loss source (preserve 3350W on remaining conductor bodies)
    try:
        for b in ipk.boundaries:
            if b.name == "loss_coil":
                P("loss_coil Total Power", b.props.get("Total Power", "?"),
                  "| nobj", len(b.props.get("Objects", []) or []))
    except Exception as e:
        P("loss_coil inspect EXC", repr(e)[:120])

    # --- native delete of end-tips ---
    if endtips:
        try:
            oed.Delete(["NAME:Selections", "Selections:=", ",".join(endtips)])
            P("native oEditor.Delete issued for", len(endtips), "endtips")
        except Exception as e:
            P("native Delete EXC:", repr(e)[:200])
            done = 0
            for n in endtips:
                try: oed.Delete(["NAME:Selections", "Selections:=", n]); done += 1
                except Exception: pass
            P("native delete one-by-one:", done)
    else:
        P("WARNING: native matcher found NO endtips — dumping full name list for design")
        try:
            for n in (allmatch if 'allmatch' in dir() else []):
                P("  OBJ:", n)
        except Exception: pass

    P("n objects (after delete):", len(ipk.modeler.object_names))
    ipk.save_project()
    P("saved project after deletion")

    # --- remesh (gate) ---
    P("generating mesh...")
    rc = ipk.odesign.GenerateMesh(SETUP)
    P("GenerateMesh rc =", rc)
    me = errs(ipk, "MESH")
    bad = [m for m in me if ("Invalid Body" in m or "terminated unexpectedly" in m
                             or "non-responsive" in m or "BodyCache" in m)]
    if bad:
        P("MESH STILL FAILING — aborting before solve. bad msgs:", len(bad))
        P("VERDICT: FIX-INSUFFICIENT")
        raise SystemExit(0)
    P("MESH CLEAN (no invalid-body / engine crash). proceeding to solve.")

    # --- solve ---
    P(f"solving setup {SETUP} on {CORES} cores (blocking)...")
    try:
        ipk.analyze_setup(SETUP, cores=CORES)
    except TypeError:
        ipk.analyze_setup(SETUP, num_cores=CORES)
    P("analyze returned")
    se = errs(ipk, "SOLVE")
    ipk.save_project()

    # --- extract per-part temperatures (best effort) ---
    temps = {}
    roles = {"coil": [], "stator": [], "rotor": [], "magnet": [], "shaft": []}
    # map objects to roles by material assignment
    try:
        for o in ipk.modeler.object_names:
            mat = (ipk.modeler[o].material_name or "").lower()
            for r in roles:
                if r in mat or r in o.lower():
                    roles[r].append(o); break
    except Exception as e:
        P("role map EXC", repr(e)[:120])
    P("role object counts:", {k: len(v) for k, v in roles.items()})

    try:
        fs = ipk.post.create_field_summary()
        for r, objs in roles.items():
            for o in objs[:400]:
                try: fs.add_calculation("Object", "Volume", o, "Temperature")
                except Exception: pass
        data = fs.get_field_summary_data(pandas=False)
        P("field summary keys:", list(data.keys()) if hasattr(data, "keys") else type(data))
        temps["_raw_field_summary"] = data
    except Exception as e:
        P("field summary EXC:", repr(e)[:200])
        # fallback: scalar min/max via post
        try:
            for r, objs in roles.items():
                vals = []
                for o in objs[:400]:
                    v = ipk.post.get_scalar_field_value("Temperature", "Maximum", object_name=o,
                                                        object_type="volume")
                    if v is not None: vals.append(v)
                if vals: temps[r] = {"max": max(vals)}
        except Exception as e2:
            P("scalar fallback EXC:", repr(e2)[:200])

    out = {"_model": "e10 Icepak (endtip-fixed)", "_setup": SETUP,
           "_cores": CORES, "temps": temps,
           "_note": "hairpin endtip bodies deleted; remeshed+solved"}
    with open(OUTJSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    P("wrote", OUTJSON)
    P("VERDICT: SOLVED")
except SystemExit:
    pass
except Exception:
    P("FATAL:\n" + traceback.format_exc())
finally:
    try:
        if ipk is not None:
            ipk.release_desktop(close_projects=True, close_desktop=True)
            P("released desktop")
    except Exception as e:
        P("release EXC", repr(e)[:120])
    log.close()
    os._exit(0)
