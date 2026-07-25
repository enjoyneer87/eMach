# -*- coding: utf-8 -*-
"""e10 Icepak 함침(impregnation) 슬롯충전체 생성 — 코일↔스테이터 동적 연동 복원.
함침 elan-protect UP142: k=0.13, cp=1700, rho=2170.
함침체 = 슬롯밴드(r71.2~91, z±75) − 스테이터 − 코일144.
이 스크립트는 형상 boolean만(솔브X) — 성공/부피 확인용. 성공시 저장."""
import os, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\e10_icepak_hybrid.aedt"
LOG = os.path.join(SP, "e10_ipk_impreg_build.txt")
_l = open(LOG, "w", encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a)+"\n"); _l.flush()
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="e10_net", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened.", ipk.solution_type, ipk.problem_type)
    mod=ipk.modeler
    names=mod.object_names
    stator="Stator_Lamination_Primitive"
    coils=[n for n in names if n.startswith("Ph")]
    P("coils:", len(coils), "stator?", stator in names, "기존 impreg?", "impregnation" in names)

    # 기존 함침 있으면 삭제
    for n in ("impregnation","imp_outer","imp_inner"):
        if n in mod.object_names:
            try: mod.delete(n)
            except Exception: pass

    # 함침 재료
    mn="impreg_elanUP142"
    try:
        mm = ipk.materials.add_material(mn) if not ipk.materials.exists_material(mn) else ipk.materials[mn]
        mm.thermal_conductivity=0.13; mm.specific_heat=1700; mm.mass_density=2170
        P("material", mn, "k=0.13 cp=1700 rho=2170 OK")
    except Exception as e: P("material err:", repr(e)[:100])

    # 슬롯밴드 annulus: 실린더 r91 − r71.2, z=-75..75
    try:
        outer=mod.create_cylinder(orientation="Z", origin=[0,0,-75], radius=91.0, height=150.0,
                                  name="imp_outer", material=mn)
        inner=mod.create_cylinder(orientation="Z", origin=[0,0,-75], radius=71.2, height=150.0,
                                  name="imp_inner", material=mn)
        P("cylinders:", bool(outer), bool(inner))
        mod.subtract("imp_outer", "imp_inner", keep_originals=False)
        P("annulus(band) 생성. vol=", round(mod["imp_outer"].volume,1) if hasattr(mod["imp_outer"],"volume") else "?")
    except Exception as e: P("cylinder/annulus err:", repr(e)[:150])

    # − 스테이터 (teeth 제거 → 슬롯개구만)
    try:
        mod.subtract("imp_outer", stator, keep_originals=True)
        P("−stator OK. vol=", round(mod["imp_outer"].volume,1))
    except Exception as e: P("−stator err:", repr(e)[:150])

    # − 코일144 (구리 제외공간=함침)
    try:
        mod.subtract("imp_outer", coils, keep_originals=True)
        P("−coils OK. vol=", round(mod["imp_outer"].volume,1))
    except Exception as e: P("−coils err:", repr(e)[:150])

    # 이름/재료 확정
    try:
        mod["imp_outer"].name="impregnation"
    except Exception: pass
    try:
        ipk.assign_material(["impregnation" if "impregnation" in mod.object_names else "imp_outer"], mn)
        P("함침 재료 부여 완료. 최종객체수:", len(mod.object_names))
    except Exception as e: P("assign_material err:", repr(e)[:100])

    # 함침이 코일/스테이터에 닿는지 확인
    impn = "impregnation" if "impregnation" in mod.object_names else "imp_outer"
    try:
        touch=mod[impn].touching_objects
        P(f"{impn} touching_objects({len(touch)}):", touch[:10])
    except Exception as e: P("touch err", repr(e)[:60])
    ipk.save_project()
    P("saved. DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
os._exit(0)
