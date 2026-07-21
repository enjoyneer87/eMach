# -*- coding: utf-8 -*-
"""Icepak 발산 진단: 부품 간 실제 접촉(공유면/gap) 여부 확인."""
import json, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\Prius_work\Prius_Icepak.aedt"
log = open(SP + r"\ipk_diag.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
groups = json.load(open(SP + r"\ipk_groups.json"))
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="Prius_CHT", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("objects:", ipk.modeler.object_names)
    # 각 오브젝트의 solve_inside 속성 확인
    for role, names in groups.items():
        for n in names:
            try:
                si = ipk.modeler[n].solve_inside
            except Exception as e:
                si = f"ERR {e!r}"[:60]
            P(f"  {role:12s} {n:12s} solve_inside={si}")
    # 소스가 붙은 오브젝트가 실제로 다른 solid와 접촉하는지 (touching_objects)
    P("--- touching check (coil/stator/rotor/magnet) ---")
    for role in ("coil","stator","rotor","magnet","shaft"):
        for n in groups.get(role,[])[:2]:
            try:
                faces = ipk.modeler[n].faces
                touch=set()
                for f in faces:
                    t = f.touching_objects
                    if t: touch.update(t)
                touch.discard(n)
                P(f"  {role} {n}: touches {sorted(touch)}")
            except Exception as e:
                P(f"  {role} {n}: ERR {repr(e)[:100]}")
    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
import os; os._exit(0)
