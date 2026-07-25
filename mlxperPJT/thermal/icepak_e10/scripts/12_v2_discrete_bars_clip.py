# -*- coding: utf-8 -*-
"""V2 = discrete 구리바(144 하이핀, k387) 컨포멀 매칭 + 대류벽(MAPDL 오일노드ref) + STEADY 테스트.
새 디자인 e10_net_v2: e10_net서 stator/rotor/shaft/magnet 복사 + Maxwell서 코일 복사.
함침 = 슬롯밴드 − stator − coils (subtract → coil·stator면 coincident=컨포멀 브리지).
V1b가 subtract-컨포멀 성립을 증명 → V2는 imported 코일도 컨포멀되는지 테스트.
1) copy+정렬검증(early abort) 2) 함침/재료/손실/대류벽 3) STEADY 솔브.
"""
import os, math, json, traceback
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ=r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
MAXW=r"D:\KDH\simVary\e10_6TSweep\refModel\e10Turn6V261_3D_Script_ANSYSEM_3D.aedt"
MDESIGN="Motor-CAD e10Turn6V261_3D_Script"
LOG=os.path.join(SP,"e10_ipk_v2_bars.txt")
_l=open(LOG,"w",encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
CORES=8
R_SB=71.2; R_SO=99.0; R_RO=70.0
REF={"JACKET":84.4,"SPRAY":91.9,"GAP_S":122.3,"GAP_R":87.0,"SHF":70.3}
HTC={"JACKET":1000.0,"SPRAY":2000.0,"GAP_S":1e4,"GAP_R":1e4,"SHF":250.0}
stator="Stator_Lamination_Primitive"; rotor="Rotor_Lamination_Primitive"; shaft="Shaft"
try:
    from ansys.aedt.core import Icepak, Maxwell3d
    # --- 소스 e10_net (geometry + loss 값) ---
    ipk=Icepak(project=PROJ,design="e10_net",version="2026.1",non_graphical=True,new_desktop=True)
    P("opened src e10_net",ipk.solution_type)
    src_names=list(ipk.modeler.object_names)
    magnets=[n for n in src_names if "Magnet" in n]
    P("src objs:",len(src_names),"magnets:",magnets)
    # loss 값 읽기
    lossW={}
    for b in ipk.boundaries:
        if b.name in ("loss_stator","loss_rotor","loss_magnet"):
            for k in ("Total Power","Total Power ","Power"):
                v=b.props.get(k)
                if v: lossW[b.name]=v; break
    P("src loss:",lossW)
    LS=lossW.get("loss_stator","585W"); LR=lossW.get("loss_rotor","65W"); LM=lossW.get("loss_magnet","24W")

    # --- 새 디자인 (유니크명: 삭제후 동일명 재생성 modeler-None 버그 원천차단) ---
    import time
    DES2="e10bars"+str(int(time.time())%100000)
    for d in list(ipk.design_list):
        if d.startswith("e10bars") or d in ("e10_net_v2","e10_bars"):
            try: ipk.delete_design(d); P("del leftover",d)
            except Exception: pass
    ipk2=Icepak(project=PROJ,design=DES2,version="2026.1")
    ipk2.solution_type="SteadyState"
    P("created",DES2,"modeler_ok:",ipk2.modeler is not None)
    open(os.path.join(SP,"v2_design.txt"),"w").write(DES2)
    keep=[stator,rotor,shaft]+magnets
    ok=ipk2.copy_solid_bodies_from(ipk,assignment=keep)
    for junk in ("winding","wdg_o","wdg_i","Region"):
        if junk in ipk2.modeler.object_names:
            try: ipk2.modeler.delete(junk); P("del junk",junk)
            except Exception: pass
    P("copy geom:",ok,"→ v2 objs:",ipk2.modeler.object_names)

    # --- Maxwell 코일 복사 (get_pyaedt_app: 디자인 타입 자동) ---
    from ansys.aedt.core import get_pyaedt_app
    mproj_name=os.path.splitext(os.path.basename(MAXW))[0]
    if mproj_name not in list(ipk2.odesktop.GetProjectList()):
        ipk2.odesktop.OpenProject(MAXW); P("opened maxwell proj",mproj_name)
    mxw=get_pyaedt_app(project_name=mproj_name,design_name=MDESIGN)
    P("maxwell app:",type(mxw).__name__,"design:",mxw.design_name)
    msolids=list(mxw.modeler.solid_names)
    coil_src=[n for n in msolids if n.startswith("Ph")]
    P("maxwell solids:",len(msolids),"coil-like(Ph*):",len(coil_src),coil_src[:6])
    if not coil_src:
        coil_src=[n for n in msolids if ("Coil" in n or "Wind" in n or "Cond" in n)]
        P("fallback coil names:",len(coil_src),coil_src[:6])
    ok2=ipk2.copy_solid_bodies_from(mxw,assignment=coil_src)
    P("copy coils from maxwell:",ok2)
    try:
        _op=ipk2.odesktop.SetActiveProject("e10_icepak_hybrid"); _op.SetActiveDesign(DES2)
    except Exception as e: P("reactivate v2 err",repr(e)[:50])
    v2names=list(ipk2.modeler.object_names)
    coils=[n for n in v2names if n.startswith("Ph")]
    P("v2 objs:",len(v2names),"coils:",len(coils))
    if not coils: P("VERDICT: COPY-FAIL (코일 없음)"); raise SystemExit

    # --- 정렬 검증: 코일 bbox r,z ---
    rs=[]; zs=[]
    for c in coils[:200]:
        try:
            bb=ipk2.modeler[c].bounding_box  # [xmin,ymin,zmin,xmax,ymax,zmax]
            for (x,y) in ((bb[0],bb[1]),(bb[3],bb[4])):
                rs.append(math.hypot(x,y))
            zs+=[bb[2],bb[5]]
        except Exception: continue
    if rs:
        rmin,rmax,zmin,zmax=min(rs),max(rs),min(zs),max(zs)
        P(f"coil bbox: r[{rmin:.1f},{rmax:.1f}] z[{zmin:.1f},{zmax:.1f}]")
        aligned=(40<rmax<130) and (abs(zmin)<160 and abs(zmax)<160)
        if not aligned:
            P("VERDICT: MISALIGNED (코일이 슬롯밴드 밖 → 변환/단위 문제)"); raise SystemExit
        P("정렬 OK (슬롯밴드 내)")
    else:
        P("VERDICT: NO-BBOX"); raise SystemExit

    # --- EndTip 삭제 ---
    oed=ipk2.modeler.oeditor
    try:
        et=[n for n in coils if "EndTip" in n or "Tip" in n]
        if not et:
            et=list(oed.GetMatchedObjectName("*EndTip*"))
        if et:
            ipk2.modeler.delete(et); P("del endtip",len(et))
    except Exception as e: P("endtip del err",repr(e)[:60])
    coils=[n for n in ipk2.modeler.object_names if n.startswith("Ph")]
    P("코일(엔드팁후):",len(coils))

    # --- 엔드턴 클립(z±75 절단): 엔드턴 facet 폭증=메시 킬러 제거 → active 바만(슬롯 discrete 전도 유지) ---
    mod=ipk2.modeler
    mod.create_box(origin=[-130,-130,75.002],sizes=[260,260,80],name="clip_top")
    mod.create_box(origin=[-130,-130,-155.002],sizes=[260,260,80],name="clip_bot")
    try:
        mod.subtract(coils,["clip_top","clip_bot"],keep_originals=False)
    except Exception as e: P("clip err",repr(e)[:70])
    coils=[n for n in mod.object_names if n.startswith("Ph")]
    try:
        zz=[]
        for c in coils[:200]:
            bb=mod[c].bounding_box; zz+=[bb[2],bb[5]]
        P(f"엔드턴 클립후 코일:{len(coils)} z[{min(zz):.1f},{max(zz):.1f}]")
    except Exception: P("엔드턴 클립후 코일:",len(coils))

    # --- 재료 ---
    def mat(nm,k,cp,rho):
        m=ipk2.materials.add_material(nm) if not ipk2.materials.exists_material(nm) else ipk2.materials[nm]
        m.thermal_conductivity=k; m.specific_heat=cp; m.mass_density=rho; return nm
    m_cu=mat("cu_bar",387.0,385.0,8933.0)
    m_imp=mat("imp_elan",0.13,1700.0,2170.0)
    m_st=mat("steel_st",25.0,460.0,7650.0)
    m_ro=mat("steel_ro",25.0,460.0,7650.0)
    m_mg=mat("magnet_nd",9.0,460.0,7500.0)
    m_sh=mat("steel_sh",52.0,460.0,7870.0)
    ipk2.assign_material(coils,m_cu)
    ipk2.assign_material([stator],m_st); ipk2.assign_material([rotor],m_ro)
    ipk2.assign_material([shaft],m_sh)
    for mg in magnets:
        if mg in ipk2.modeler.object_names: ipk2.assign_material([mg],m_mg)
    P("재료 할당 완료")

    # --- 함침 = 슬롯밴드 − stator − coils (컨포멀 브리지) ---
    ipk2.modeler.create_cylinder(orientation="Z",origin=[0,0,-75],radius=91.0,height=150.0,name="imp_o",material=m_imp)
    ipk2.modeler.create_cylinder(orientation="Z",origin=[0,0,-75],radius=R_SB,height=150.0,name="imp_i",material=m_imp)
    ipk2.modeler.subtract("imp_o","imp_i",keep_originals=False)
    ipk2.modeler.subtract("imp_o",[stator]+coils,keep_originals=True)  # coincident=컨포멀
    ipk2.assign_material(["imp_o"],m_imp)
    P("함침 vol=",round(ipk2.modeler["imp_o"].volume,1))

    # --- 손실 ---
    ipk2.assign_solid_block(coils,"3350W",boundary_name="loss_coil")
    ipk2.assign_solid_block([stator],LS,boundary_name="loss_stator")
    ipk2.assign_solid_block([rotor],LR,boundary_name="loss_rotor")
    if magnets: ipk2.assign_solid_block([magnets[0]] if len(magnets)==1 else magnets,LM,boundary_name="loss_magnet")
    P("손실: coil3350",LS,LR,LM)

    # --- 냉각면 + 대류벽 ---
    mod=ipk2.modeler
    def curved(o,rlo,rhi):
        out=[]
        for f in mod[o].faces:
            try:
                c=f.center; r=math.hypot(c[0],c[1])
                if f.is_planar is False and rlo<=r<=rhi: out.append(f.id)
            except Exception: continue
        return out
    def coil_ends():
        out=[]
        for c in coils:
            for f in mod[c].faces:
                try:
                    if f.is_planar and abs(f.center[2])>73.0: out.append(f.id)
                except Exception: continue
        return out
    def allf(o):
        try: return [f.id for f in mod[o].faces]
        except Exception: return []
    def rotor_ends():
        out=[]
        for f in mod[rotor].faces:
            try:
                if f.is_planar and abs(abs(f.center[2])-75.0)<3.0: out.append(f.id)
            except Exception: continue
        return out
    groups={"JACKET":curved(stator,R_SO-6,R_SO+3),"GAP_S":curved(stator,R_SB-4,R_SB+3),
            "GAP_R":curved(rotor,R_RO-5,R_RO+2),"SHF":allf(shaft)}
    P("faces(non-spray):",{k:len(v) for k,v in groups.items()})
    nwall=0
    def wallg(g,faces,htc,ref):
        if not faces: P(f"  wall {g}: 0(skip)"); return 0
        try:
            ipk2.assign_stationary_wall_with_htc(faces,name=f"htc_{g}",htc=float(htc),ref_temperature=f"{ref}cel")
            P(f"  wall {g}: {len(faces)}f OK"); return 1
        except Exception as e:
            P(f"  wall {g} ERR({len(faces)}f):",repr(e)[:90]); return 0
    for g,faces in groups.items():
        nwall+=wallg(g,faces,HTC[g],REF[g])
    nwall+=wallg("ROTEND",rotor_ends(),250.0,70.0)
    # SPRAY: 코일당 1벽 (엔드턴 facet 폭증 → 단일 거대boundary 회피)
    nspray=0; spray_tot=0
    for c in coils:
        try:
            ef=[f.id for f in mod[c].faces if getattr(f,'is_planar',False) and abs(f.center[2])>74.0]
        except Exception: ef=[]
        if ef:
            try:
                ipk2.assign_stationary_wall_with_htc(ef,name=f"htc_SPRAY_{c}",htc=float(HTC['SPRAY']),ref_temperature=f"{REF['SPRAY']}cel")
                nspray+=1; spray_tot+=len(ef)
            except Exception as e:
                if nspray==0: P("  SPRAY per-coil ERR:",repr(e)[:80])
    P(f"  SPRAY: {nspray}코일 {spray_tot}면"); nwall+=(1 if nspray else 0)
    P("대류벽 그룹수:",nwall)

    # Region 재삭제 (대류벽 외부면 보장 + 공기셀 제거로 메시 경량화)
    if "Region" in ipk2.modeler.object_names:
        try: ipk2.modeler.delete("Region"); P("del Region(pre-setup)")
        except Exception: pass
    # --- STEADY ---
    st=ipk2.create_setup(name="SolveSS",setup_type="SteadyStateTemperatureOnly")
    if "SolveSS" not in ipk2.setup_names: st=ipk2.create_setup(name="SolveSS")
    st.update(); ipk2.save_project()
    P("solving V2 STEADY...")
    ok=ipk2.analyze_setup("SolveSS",cores=CORES); ipk2.save_project()
    P("analyze:",ok)
    try: P("is_solved:",ipk2.setups[0].is_solved)
    except Exception: pass
    sol=ipk2.existing_analysis_sweeps[0] if ipk2.existing_analysis_sweeps else "SolveSS : SteadyState"
    def gextr(o):
        for q in ("Temp","Temperature"):
            try:
                r=ipk2.post.get_field_extremum(o,"Max","Volume",q,setup=sol)
                if isinstance(r,(list,tuple)): return round(float(r[1]),1)
            except Exception: pass
        return None
    res={"coil":gextr(coils[0]) if coils else None,"stator":gextr(stator),
         "rotor":gextr(rotor),"shaft":gextr(shaft)}
    # coil max over all bars
    cmax=None
    for c in coils:
        v=gextr(c)
        if v is not None: cmax=v if cmax is None else max(cmax,v)
    res["coil_max_allbars"]=cmax
    if magnets: res["magnet"]=gextr(magnets[0])
    P("V2 STEADY:",res)
    json.dump(res,open(os.path.join(SP,"e10_v2_steady.json"),"w"),indent=2)
    w=res.get("coil_max_allbars") or res.get("coil")
    if w is not None and w<800: P("VERDICT: V2-COOLED-OK (imported 코일 컨포멀 성립!) coil_ss=",w)
    elif w is not None: P("VERDICT: V2-RUNAWAY (imported 코일 비컨포멀) coil=",w)
    else: P("VERDICT: V2-NO-TEMP")
    P("DONE")
    ipk2.release_desktop(close_projects=True,close_desktop=True)
except SystemExit:
    P("STOPPED")
except Exception:
    P("EXC:",traceback.format_exc())
finally:
    for app in ("ipk2","ipk"):
        try:
            eval(app).release_desktop(close_projects=True,close_desktop=True); break
        except Exception: continue
os._exit(0)
