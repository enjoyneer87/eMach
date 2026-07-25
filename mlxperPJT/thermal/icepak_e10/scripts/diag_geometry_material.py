# -*- coding: utf-8 -*-
"""e10 Icepak 기하/재료 확인: 코일 현재 k, 코일-스테이터 접촉/틈 여부, 슬롯 반경관계.
transient+접촉모델 구성 전 진단(솔브 없음)."""
import os, math, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
LOG = os.path.join(SP, "e10_ipk_geomcheck.txt")
_l = open(LOG, "w", encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="e10_net", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened.", ipk.solution_type, ipk.problem_type)
    names=ipk.modeler.object_names
    stator="Stator_Lamination_Primitive"
    coils=[n for n in names if n.startswith("Ph")]
    magnet=[n for n in names if "Magnet" in n]
    P("coil수:", len(coils), "magnet수:", len(magnet))

    # 코일 재료 k
    for cn in coils[:1]+ [stator]:
        try:
            mat=ipk.modeler[cn].material_name
            mm=ipk.materials[mat]
            k=mm.thermal_conductivity.value if hasattr(mm.thermal_conductivity,"value") else mm.thermal_conductivity
            P(f"  {cn}: material={mat} k={k}")
        except Exception as e: P(f"  {cn} mat err {repr(e)[:70]}")

    # 샘플 코일 기하: bbox + 면 r범위 + z범위
    cn=coils[0]
    o=ipk.modeler[cn]
    bb=o.bounding_box   # [x1,y1,z1,x2,y2,z2]
    P(f"코일 {cn} bbox:", [round(v,2) for v in bb])
    rs=[]; zs=[]
    for f in o.faces:
        try:
            c=f.center; rs.append(math.hypot(c[0],c[1])); zs.append(c[2])
        except Exception: continue
    P(f"  면 r범위: {round(min(rs),2)}~{round(max(rs),2)}  z범위: {round(min(zs),2)}~{round(max(zs),2)}  면수:{len(o.faces)}")

    # 스테이터 내경(슬롯바닥) 확인: 곡면 r들
    so=ipk.modeler[stator]
    srs=set()
    for f in so.faces:
        try:
            c=f.center; r=math.hypot(c[0],c[1])
            if f.is_planar is False: srs.add(round(r,1))
        except Exception: continue
    P("스테이터 곡면 r들(내경/외경):", sorted(srs)[:12])

    # 접촉 판정: 코일 외곽점 바깥으로 조금 이동해 어떤 바디인지
    cx=0.5*(bb[0]+bb[3]); cy=0.5*(bb[1]+bb[4]); cz=0.5*(bb[2]+bb[5])
    rr=math.hypot(cx,cy)
    if rr>1:
        ux,uy=cx/rr,cy/rr
        for d in (0.5,1.0,2.0):
            px,py=cx+ux*d, cy+uy*d
            try:
                bn=ipk.modeler.get_bodynames_from_position([px,py,cz])
                P(f"  코일중심에서 반경+{d}mm 위치 바디: {bn}")
            except Exception as e: P(f"  pos체크 err {repr(e)[:50]}")

    # 코일-스테이터 접촉면(coincident) 존재? touching_objects
    try:
        touch=ipk.modeler[cn].touching_objects
        P(f"  {cn} touching_objects:", touch[:8] if touch else touch)
    except Exception as e: P("  touching err", repr(e)[:60])

    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
os._exit(0)
