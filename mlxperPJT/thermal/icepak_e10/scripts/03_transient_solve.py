# -*- coding: utf-8 -*-
"""e10 Icepak TRANSIENT (함침모델) — MAPDL transient@900s와 정당 비교.
정정: steady(1196) vs transient(MAPDL152@900s) 비교는 오류. 함침 高저항으로 권선이
뜨겁게 유지되는 건 실제 물리(단시간운전 ~160C, 포화 전 종료). transient끼리 비교.
IC 70C, dt 45s → 900s (MAPDL와 동일). 함침 elan-UP142 k0.13, 코일 k387."""
import os, glob, json, math, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_icepak_transient_result.json"
VIZ = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\viz\icepak"
LOG = os.path.join(SP, "e10_ipk_transient.txt")
_l = open(LOG, "w", encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
CORES=8
try:
    from ansys.aedt.core import Icepak
    os.makedirs(VIZ, exist_ok=True)
    ipk = Icepak(project=PROJ, design="e10_net", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened.", ipk.solution_type, ipk.problem_type, "bnds:", [b.name for b in ipk.boundaries])
    names=ipk.modeler.object_names
    stator="Stator_Lamination_Primitive"; rotor="Rotor_Lamination_Primitive"; shaft="Shaft"
    magnet=[n for n in names if "Magnet" in n]; coils=[n for n in names if n.startswith("Ph")]
    impn="impregnation" if "impregnation" in names else ("imp_outer" if "imp_outer" in names else None)
    P("impreg?", impn, "coils", len(coils))

    # Transient 전환 + 셋업
    try: ipk.solution_type="Transient"; P("soltype->",ipk.solution_type)
    except Exception as e: P("soltype err",repr(e)[:80])
    try: ipk.problem_type="TemperatureOnly"; P("problem->",ipk.problem_type)
    except Exception as e: P("problem err",repr(e)[:80])
    for sn in list(ipk.setup_names):
        try: ipk.delete_setup(sn)
        except Exception: pass
    stp=None
    for stype in ("IcepakTransient","Transient"):
        try:
            stp=ipk.create_setup("SolveTr", setup_type=stype)
            if "SolveTr" in ipk.setup_names: P("setup_type OK:", stype); break
            else: P("setup_type", stype, "-> setups still", ipk.setup_names)
        except Exception as e: P(f"create_setup({stype}) err:", repr(e)[:100])
    if "SolveTr" not in ipk.setup_names:
        P("!! setup 생성 실패 - 중단"); raise RuntimeError("no transient setup")
    for k,v in {"Stop Time":"900s","Time Step":"45s",
                "Solution Initialization - Temperature":"70cel"}.items():
        try: stp.props[k]=v
        except Exception as e: P(f"prop {k} err",repr(e)[:50])
    try: stp.update()
    except Exception: pass
    P("SolveTr 생성확인. setups:", ipk.setup_names, "props Stop/Step:",
      stp.props.get("Stop Time"), stp.props.get("Time Step"))

    P("solving TRANSIENT (dt45s→900s, cores=%d)... 오래걸림"%CORES)
    ok=ipk.analyze_setup("SolveTr", cores=CORES)
    ipk.save_project()
    P("analyze:", ok)
    try: P("is_solved:", ipk.setups[0].is_solved)
    except Exception: pass
    NDIR=PROJ.replace(".aedt",".aedtresults")+r"\e10_net.results"
    tot=sum(os.path.getsize(f) for f in glob.glob(os.path.join(NDIR,"**","*"),recursive=True) if os.path.isfile(f))
    P("결과크기 MB:", round(tot/1e6,1))
    sol=ipk.existing_analysis_sweeps[0] if ipk.existing_analysis_sweeps else "SolveTr : Transient"
    P("sol:", sol)

    def tmax(o,t):
        for q in ("Temp","Temperature"):
            try:
                r=ipk.post.get_field_extremum(o,"Max","Volume",q,setup=sol,intrinsics={"Time":t})
                if isinstance(r,(list,tuple)): return round(float(r[1]),2)
            except Exception: pass
        return None
    def tmean(o,t):
        for q in ("Temperature","Temp"):
            try:
                v=ipk.post.get_scalar_field_value(q,scalar_function="Mean",object_name=o,
                        object_type="volume",intrinsics={"Time":t})
                if v not in (None,False): return round(float(v),2)
            except Exception: pass
        return None
    # 시간이력: 코일 max, stator/rotor/magnet mean
    times=["45s","135s","270s","450s","675s","900s"]
    hist={"time_s":[], "coil_max":[], "stator_mean":[], "rotor_mean":[], "magnet_mean":[]}
    for t in times:
        cm=max([x for x in [tmax(c,t) for c in coils[::16]] if x] or [None]) if coils else None
        hist["time_s"].append(int(t.replace("s","")))
        hist["coil_max"].append(cm)
        hist["stator_mean"].append(tmean(stator,t))
        hist["rotor_mean"].append(tmean(rotor,t))
        hist["magnet_mean"].append(tmean(magnet[0],t) if magnet else None)
        P(f"  t={t}: coil_max={cm} stator={hist['stator_mean'][-1]} rotor={hist['rotor_mean'][-1]} magnet={hist['magnet_mean'][-1]}")

    res={"_model":"e10 Icepak TRANSIENT 함침모델(elan-UP142 k0.13)+코일k387. IC70 dt45s→900s.",
         "_note":"transient끼리 비교(steady 1196은 미도달 포화값). 단시간운전 실제.",
         "_mapdl_transient_900s":{"winding":152.2,"stator":126.0,"magnet":86.9,"rotor":86.9},
         "_at_900s":{"coil_max":hist["coil_max"][-1],"stator_mean":hist["stator_mean"][-1],
                     "rotor_mean":hist["rotor_mean"][-1],"magnet_mean":hist["magnet_mean"][-1]},
         "history":hist}
    json.dump(res,open(OUTJSON,"w",encoding="utf-8"),indent=2,ensure_ascii=False)
    P("saved", OUTJSON)

    # PNG @900s
    try:
        allobj=[stator,rotor,shaft]+([impn] if impn else [])+(magnet[:1] if magnet else [])+coils
        fp=ipk.post.create_fieldplot_volume(allobj,"Temperature",sol,intrinsics={"Time":"900s"})
        if fp and getattr(fp,"name",None):
            for v in ("isometric","top"):
                png=os.path.join(VIZ,f"e10_icepak_transient_{v}.png")
                ipk.post.export_field_jpg(png,fp.name,getattr(fp,"plot_folder","Temp"),orientation=v)
                P(f"  PNG {v}:", os.path.exists(png))
    except Exception as e: P("png fail:",repr(e)[:130])
    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
os._exit(0)
