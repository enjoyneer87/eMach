# -*- coding: utf-8 -*-
"""V1b = V1 컨포멀 homogenized winding + 대류벽(HTC, MAPDL 오일노드온도 ref) 교체.
Network(solver-input 실패 2회 확정) 폐기. MAPDL과 동일 Robin BC.
빠른 STEADY 테스트: (a)대류벽 냉각 여부 (b)컨포멀 winding 폭주 여부.
MAPDL 오일노드: JACKET84.4 SPRAY91.9 GAP_S122.3 GAP_R87.0 SHF70.3 / htc 1000/2000/1e4/1e4/250.
"""
import os, glob, math, json, traceback
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ=r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
LOG=os.path.join(SP,"e10_ipk_v1b_htc.txt")
_l=open(LOG,"w",encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
CORES=8
R_SB=71.2; R_SO=99.0; R_RO=70.0
# MAPDL 오일노드 온도(ref) / htc
REF={"JACKET":84.4,"SPRAY":91.9,"GAP_S":122.3,"GAP_R":87.0,"SHF":70.3}
HTC={"JACKET":1000.0,"SPRAY":2000.0,"GAP_S":1e4,"GAP_R":1e4,"SHF":250.0}
try:
    from ansys.aedt.core import Icepak
    ipk=Icepak(project=PROJ,design="e10_net",version="2026.1",non_graphical=True,new_desktop=True)
    P("opened.",ipk.solution_type)
    mod=ipk.modeler
    stator="Stator_Lamination_Primitive"; rotor="Rotor_Lamination_Primitive"; shaft="Shaft"
    wn="winding" if "winding" in mod.object_names else ("wdg_o" if "wdg_o" in mod.object_names else None)
    P("winding obj:",wn,"objs:",len(mod.object_names))
    if wn is None: P("NO WINDING - abort"); raise SystemExit

    # --- Network/기존 대류·고정BC/셋업 제거 ---
    for b in list(ipk.boundaries):
        if getattr(b,"type",None)=="Network" or b.name.startswith(("fixT_","cool_","htc_","OilCircuit")):
            try: b.delete(); P("del bc",b.name)
            except Exception: pass
    for sn in list(ipk.setup_names):
        try: ipk.delete_setup(sn); P("del setup",sn)
        except Exception: pass
    ipk.solution_type="SteadyState"
    P("경계 후:",[b.name for b in ipk.boundaries],"셋업:",ipk.setup_names)

    # --- 냉각면 식별 ---
    def curved(o,rlo,rhi):
        out=[]
        for f in mod[o].faces:
            try:
                c=f.center; r=math.hypot(c[0],c[1])
                if f.is_planar is False and rlo<=r<=rhi: out.append(f.id)
            except Exception: continue
        return out
    def wdg_ends():
        out=[]
        for f in mod[wn].faces:
            try:
                if f.is_planar and abs(abs(f.center[2])-75.0)<2.0: out.append(f.id)
            except Exception: continue
        return out
    def allf(o):
        try: return [f.id for f in mod[o].faces]
        except Exception: return []
    groups={"JACKET":curved(stator,R_SO-6,R_SO+3),"GAP_S":curved(stator,R_SB-4,R_SB+3),
            "SPRAY":wdg_ends(),"GAP_R":curved(rotor,R_RO-5,R_RO+2),"SHF":allf(shaft)}
    P("faces:",{k:len(v) for k,v in groups.items()})

    # --- 대류벽(HTC) ---
    nwall=0
    for gname,faces in groups.items():
        for i,fid in enumerate(faces):
            try:
                ipk.assign_stationary_wall_with_htc(fid,name=f"htc_{gname}_{i}",
                    htc=float(HTC[gname]),ref_temperature=f"{REF[gname]}cel")
                nwall+=1
            except Exception as e:
                if i==0: P(f"  wall err {gname}:",repr(e)[:80])
    P("대류벽 수:",nwall)

    # --- STEADY 솔브 ---
    st=ipk.create_setup(name="SolveSS",setup_type="SteadyStateTemperatureOnly")
    if "SolveSS" not in ipk.setup_names:
        st=ipk.create_setup(name="SolveSS")
    try: st.props["Convergence Criteria - Max Iterations"]=100
    except Exception: pass
    st.update(); ipk.save_project()
    P("steady setup:",ipk.setup_names)
    P("solving STEADY htc-wall test...")
    ok=ipk.analyze_setup("SolveSS",cores=CORES); ipk.save_project()
    P("analyze:",ok)
    try: P("is_solved:",ipk.setups[0].is_solved)
    except Exception: pass

    sol=ipk.existing_analysis_sweeps[0] if ipk.existing_analysis_sweeps else "SolveSS : SteadyState"
    P("sweep:",sol)
    def gextr(o):
        for q in ("Temp","Temperature"):
            try:
                r=ipk.post.get_field_extremum(o,"Max","Volume",q,setup=sol)
                if isinstance(r,(list,tuple)): return round(float(r[1]),1)
            except Exception: pass
        return None
    res={}
    names=list(mod.object_names)
    magnet=[n for n in names if "Magnet" in n]
    for role,o in {"winding":wn,"stator":stator,"rotor":rotor,"shaft":shaft}.items():
        res[role]=gextr(o); P(f"  {role}_max:",res[role])
    if magnet: res["magnet"]=gextr(magnet[0]); P("  magnet_max:",res["magnet"])
    P("STEADY-RESULT:",res)
    # 판정
    w=res.get("winding")
    if w is not None and w<800: P("VERDICT: COOLED-OK (컨포멀 작동, 대류벽 냉각). transient 진행 가능. winding_ss=",w)
    elif w is not None: P("VERDICT: RUNAWAY (winding=",w,"). fixed-T 폴백 필요")
    else: P("VERDICT: NO-TEMP (추출실패/미솔브)")
    json.dump(res,open(os.path.join(SP,"e10_v1b_steady.json"),"w"),indent=2)
    P("DONE")
    ipk.release_desktop(close_projects=True,close_desktop=True)
except SystemExit:
    P("STOPPED")
except Exception:
    P("EXC:",traceback.format_exc())
os._exit(0)
