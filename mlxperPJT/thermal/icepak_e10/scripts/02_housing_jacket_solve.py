# -*- coding: utf-8 -*-
"""e10 Icepak: 하우징(oil jacket) 추가 — MAPDL JACKET 노드 미러.
현재 stator OD에 직접 fixT84.4(하우징 생략). → 하우징 금속링(r99-110, Al) 부울생성
(스테이터 OD와 컨포멀 접촉) + 하우징 외면 오일자켓 84.4C 고정. stator OD fixT 제거.
코일 등방성387·함침k0.13 유지. SteadyState 검증(스테이터 드레인 개선 여부도)."""
import os, json, math, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_icepak_housing.json"
VIZ = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\viz\icepak"
LOG = os.path.join(SP, "e10_ipk_housing.txt")
_l = open(LOG, "w", encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
CORES=8; R_STA_OD=99.0; R_HOUS=110.0; JACKET_T=84.4
try:
    from ansys.aedt.core import Icepak
    os.makedirs(VIZ, exist_ok=True)
    ipk = Icepak(project=PROJ, design="e10_net", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened.", ipk.solution_type, ipk.problem_type, "bnds:", [b.name for b in ipk.boundaries])
    mod=ipk.modeler; names=mod.object_names
    stator="Stator_Lamination_Primitive"; rotor="Rotor_Lamination_Primitive"; shaft="Shaft"
    magnet=[n for n in names if "Magnet" in n]; coils=[n for n in names if n.startswith("Ph")]
    impn="impregnation" if "impregnation" in names else None

    # 기존 하우징/자켓 제거
    for n in ("housing","hous_o","hous_i"):
        if n in mod.object_names:
            try: mod.delete(n)
            except Exception: pass
    for b in list(ipk.boundaries):
        if b.name in ("fixT_jacket","fixT_housing"):
            try: b.delete(); P("del",b.name)
            except Exception: pass

    # 알루미늄 하우징 재료
    mn="housing_al"
    mm = ipk.materials.add_material(mn) if not ipk.materials.exists_material(mn) else ipk.materials[mn]
    mm.thermal_conductivity=237.0; mm.specific_heat=900.0; mm.mass_density=2700.0
    # 하우징 링 = 실린더r110 − r99 (스테이터OD와 컨포멀)
    mod.create_cylinder(orientation="Z",origin=[0,0,-75],radius=R_HOUS,height=150.0,name="hous_o",material=mn)
    mod.create_cylinder(orientation="Z",origin=[0,0,-75],radius=R_STA_OD,height=150.0,name="hous_i",material=mn)
    mod.subtract("hous_o","hous_i",keep_originals=False)
    try: mod["hous_o"].name="housing"
    except Exception: pass
    hn="housing" if "housing" in mod.object_names else "hous_o"
    ipk.assign_material([hn],mn)
    P(f"하우징 생성 vol={round(mod[hn].volume,1)} 객체수={len(mod.object_names)}")

    # 하우징 외면(r110 곡면)에 오일자켓 고정온도
    def outer_face(o,rmin):
        for f in mod[o].faces:
            try:
                c=f.center; r=math.hypot(c[0],c[1])
                if f.is_planar is False and r>=rmin: return f.id
            except Exception: continue
        return None
    of=outer_face(hn, R_HOUS-3)
    P("하우징 외면 id:", of)
    if of is not None:
        b=ipk.assign_stationary_wall_with_temperature([of],name="fixT_jacket",temperature=f"{JACKET_T}cel")
        P("자켓 고정온도(하우징외면):", bool(b))
    ipk.save_project()
    P("bnds:", [b.name for b in ipk.boundaries])

    # SteadyState 보장 + 솔브
    if ipk.solution_type!="SteadyState":
        try: ipk.solution_type="SteadyState"
        except Exception: pass
    try: ipk.problem_type="TemperatureOnly"
    except Exception: pass
    for sn in list(ipk.setup_names):
        if "trans" in sn.lower():
            try: ipk.delete_setup(sn)
            except Exception: pass
    if not ipk.setup_names: ipk.create_setup("SolveSS")
    setup=ipk.setup_names[0]
    P(f"solving {setup}...")
    ok=ipk.analyze_setup(setup,cores=CORES); ipk.save_project()
    P("analyze:", ok)
    try: P("is_solved:", ipk.setups[0].is_solved)
    except Exception: pass
    sol=ipk.existing_analysis_sweeps[0] if ipk.existing_analysis_sweeps else setup
    def gextr(o):
        for q in ("Temp","Temperature"):
            try:
                r=ipk.post.get_field_extremum(o,"Max","Volume",q,setup=sol)
                if isinstance(r,(list,tuple)): return round(float(r[1]),2)
            except Exception: pass
        return None
    def gmean(o):
        for q in ("Temperature","Temp"):
            try:
                v=ipk.post.get_scalar_field_value(q,scalar_function="Mean",object_name=o,object_type="volume")
                if v not in (None,False): return round(float(v),2)
            except Exception: pass
        return None
    pp={}
    for role,o in {"housing":hn,"stator":stator,"rotor":rotor,"shaft":shaft}.items():
        pp[role]={"max":gextr(o),"mean":gmean(o)}; P(f"  {role}:",pp[role])
    if magnet: pp["magnet"]={"max":gextr(magnet[0]),"mean":gmean(magnet[0])}; P("  magnet:",pp.get("magnet"))
    cx=[gextr(c) for c in coils[::8]]; cx=[x for x in cx if x]
    pp["coil"]={"max":max(cx) if cx else None,"mean":gmean(coils[0])}; P("  COIL:",pp["coil"])
    res={"_model":"하우징(oil jacket) 추가: Al링 r99-110 + 외면 자켓84.4C. 코일등방387·함침0.13.",
         "_vs_mapdl":{"winding":152.2,"stator":126.0,"magnet":86.9,"rotor":86.9},**pp}
    json.dump(res,open(OUTJSON,"w",encoding="utf-8"),indent=2,ensure_ascii=False); P("saved json")
    try:
        allobj=[hn,stator,rotor,shaft]+([impn] if impn else [])+(magnet[:1] if magnet else [])+coils
        fp=ipk.post.create_fieldplot_volume(allobj,"Temperature",sol)
        if fp and getattr(fp,"name",None):
            for v in ("isometric","top"):
                png=os.path.join(VIZ,f"e10_icepak_housing_{v}.png")
                ipk.post.export_field_jpg(png,fp.name,getattr(fp,"plot_folder","Temp"),orientation=v)
                P(f"  PNG {v}:", os.path.exists(png))
    except Exception as e: P("png fail:",repr(e)[:120])
    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
os._exit(0)
