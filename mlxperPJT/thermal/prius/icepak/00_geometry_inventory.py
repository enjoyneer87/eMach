# -*- coding: utf-8 -*-
"""STEP 전체 볼륨 인벤토리 (하우징+재킷 포함) - Icepak 재료/소스 매핑용."""
import math, json, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
STP = (r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019"
       r"\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.stp")
log = open(SP + r"\ipk_inventory.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
try:
    import gmsh
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
    occ = gmsh.model.occ
    occ.importShapes(STP); occ.synchronize()
    rows=[]
    for (dim,tag) in gmsh.model.getEntities(3):
        xmn,ymn,zmn,xmx,ymx,zmx = gmsh.model.getBoundingBox(3,tag)
        V = occ.getMass(3,tag)/1e3   # cm3
        rmn = min(math.hypot(xmn,ymn),math.hypot(xmx,ymx),math.hypot(xmn,ymx),math.hypot(xmx,ymn))
        rmx = max(math.hypot(xmn,ymn),math.hypot(xmx,ymx),math.hypot(xmn,ymx),math.hypot(xmx,ymn))
        rows.append((tag,V,rmn,rmx,zmn,zmx))
    rows.sort(key=lambda r:-r[1])
    P(f"{'tag':>4} {'V_cm3':>9} {'r_in':>7} {'r_out':>7} {'z_min':>8} {'z_max':>8}")
    for tag,V,rmn,rmx,zmn,zmx in rows:
        P(f"{tag:4d} {V:9.2f} {rmn:7.1f} {rmx:7.1f} {zmn:8.1f} {zmx:8.1f}")
    P("N_volumes:", len(rows))
    P("DONE-OK")
    gmsh.finalize()
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
import os; os._exit(0)
