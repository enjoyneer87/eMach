# -*- coding: utf-8 -*-
"""V1c = V1b(컨포멀 homog winding + 대류벽 HTC) 를 TRANSIENT 로. MAPDL과 same-model+conditions.
V1b STEADY가 COOLED-OK(winding136.5) 확인됨. 이제 IC70→dt45→900s transient.
+ 로터 축단면 splash 대류벽(htc250,ref70) 추가(MAPDL 로터단 냉각 미러).
MAPDL transient@900s: winding152.2 stator126 magnet86.9 rotor86.9 shaft84.9.
"""
import os, glob, math, json, traceback
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ=r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
OUTJSON=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_icepak_v1_homog.json"
LOG=os.path.join(SP,"e10_ipk_v1c_trans.txt")
_l=open(LOG,"w",encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
CORES=8
R_SB=71.2; R_SO=99.0; R_RO=70.0
try:
    from ansys.aedt.core import Icepak
    ipk=Icepak(project=PROJ,design="e10_net",version="2026.1",non_graphical=True,new_desktop=True)
    P("opened.",ipk.solution_type)
    mod=ipk.modeler
    stator="Stator_Lamination_Primitive"; rotor="Rotor_Lamination_Primitive"; shaft="Shaft"
    wn="winding" if "winding" in mod.object_names else "wdg_o"
    names=list(mod.object_names); magnet=[n for n in names if "Magnet" in n]
    P("winding:",wn,"objs:",len(names))

    # 로터 축단면 splash 대류벽 추가 (MAPDL 로터단→OIL, htc250 ref70)
    def rotor_ends():
        out=[]
        for f in mod[rotor].faces:
            try:
                if f.is_planar and abs(abs(f.center[2])-75.0)<3.0: out.append(f.id)
            except Exception: continue
        return out
    re_faces=rotor_ends(); nadd=0
    have=set(b.name for b in ipk.boundaries)
    for i,fid in enumerate(re_faces):
        nm=f"htc_ROTEND_{i}"
        if nm in have: continue
        try:
            ipk.assign_stationary_wall_with_htc(fid,name=nm,htc=250.0,ref_temperature="70cel"); nadd+=1
        except Exception as e:
            if i==0: P("rotend wall err:",repr(e)[:70])
    P("로터단 대류벽 추가:",nadd,"/ 총벽:",len([b for b in ipk.boundaries if b.name.startswith('htc_')]))

    # --- Transient 셋업 ---
    for sn in list(ipk.setup_names):
        try: ipk.delete_setup(sn)
        except Exception: pass
    ipk.solution_type="Transient"
    st=ipk.create_setup(name="SolveTr",setup_type="IcepakTransient")
    if "SolveTr" not in ipk.setup_names: P("SETUP-FAIL"); raise SystemExit
    for k,v in (("Stop Time","900s"),("Time Step","45s"),
                ("Solution Initialization - Temperature","70cel")):
        try: st.props[k]=v
        except Exception: pass
    st.update(); ipk.save_project()
    P("transient setup:",{k:st.props.get(k) for k in ("Stop Time","Time Step")})

    P("meshing+solving TRANSIENT (~30-60min)...")
    ok=ipk.analyze_setup("SolveTr",cores=CORES); ipk.save_project()
    P("analyze:",ok)
    try: P("is_solved:",ipk.setups[0].is_solved)
    except Exception: pass
    sol=ipk.existing_analysis_sweeps[0] if ipk.existing_analysis_sweeps else "SolveTr : Transient"
    P("sweep:",sol)

    TIMES=["900s","855s","810s","765s","720s"]
    def gextr(o):
        for t in TIMES:
            for q in ("Temp","Temperature"):
                try:
                    r=ipk.post.get_field_extremum(o,"Max","Volume",q,setup=sol,intrinsics={"Time":t})
                    if isinstance(r,(list,tuple)): return round(float(r[1]),1),t
                except Exception: pass
        for q in ("Temp","Temperature"):
            try:
                r=ipk.post.get_field_extremum(o,"Max","Volume",q,setup=sol)
                if isinstance(r,(list,tuple)): return round(float(r[1]),1),"last"
            except Exception: pass
        return None,None
    res={"_model":"V1 Icepak: homog winding k5(스테이터 컨포멀)+대류벽(MAPDL 오일노드 ref)+transient",
         "_note":"동적오일회로 Network는 solver-input 실패(전도-only)로 폐기 → MAPDL과 동일 Robin(HTC) BC로 재현. τ_oil≈2.5s≪900s라 준정상 등가.",
         "_vs_mapdl_at900s":{"winding":152.2,"stator":126.0,"magnet":86.9,"rotor":86.9,"shaft":84.9},
         "_v1b_steady":{"winding":136.5,"stator":133.7,"rotor":128.7,"magnet":105.5,"shaft":91.5},
         "at_900s":{}}
    for role,o in {"winding":wn,"stator":stator,"rotor":rotor,"shaft":shaft}.items():
        v,t=gextr(o); res["at_900s"][role]={"max":v,"t":t}; P(f"  {role}:",v,"@",t)
    if magnet:
        v,t=gextr(magnet[0]); res["at_900s"]["magnet"]={"max":v,"t":t}; P("  magnet:",v,"@",t)
    json.dump(res,open(OUTJSON,"w",encoding="utf-8"),indent=2,ensure_ascii=False)
    P("saved",OUTJSON)
    w=res["at_900s"].get("winding",{}).get("max")
    if w is not None and w<800: P("VERDICT: V1-TRANSIENT-OK winding@900s=",w,"vs MAPDL152.2")
    else: P("VERDICT: check winding=",w)
    P("DONE")
    ipk.release_desktop(close_projects=True,close_desktop=True)
except SystemExit:
    P("STOPPED")
except Exception:
    P("EXC:",traceback.format_exc())
os._exit(0)
