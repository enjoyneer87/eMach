# -*- coding: utf-8 -*-
"""Icepak stage B3: fix water-jacket wall to true frame OUTER cylindrical faces."""
import os, math, json, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\Prius_work\Prius_Icepak.aedt"
log = open(SP + r"\ipk_B3.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
COOLANT_T, HTC = 27.0, 3000.0
groups = json.load(open(SP + r"\ipk_groups.json"))
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="Prius_CHT", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened.")
    # delete wrong jacket wall
    for b in list(ipk.boundaries):
        if b.name == "water_jacket":
            try: b.delete(); P("deleted old water_jacket")
            except Exception as e: P("del fail:", repr(e)[:80])

    fname = groups["frame"][0]
    P(f"frame={fname}")
    cand=[]
    for f in ipk.modeler[fname].faces:
        c=f.center; r=math.hypot(c[0],c[1])
        try: planar=f.is_planar
        except Exception: planar=None
        try: touch=[o for o in (f.touching_objects or []) if o!=fname]
        except Exception: touch=None
        try: n=f.normal; nz=abs(n[2]) if n else None
        except Exception: nz=None
        row=(f.id, round(r,1), round(f.area,0), planar, nz if nz is None else round(nz,2),
             touch, round(c[2],1))
        # 외부 원통 OD: 비평면 + 반경 큰편 + 다른 솔리드 안 닿음(외부)
        is_od = (planar is False) and (r>155) and (not touch)
        cand.append((is_od,)+row)
    P("frame faces (is_od,id,r,area,planar,|nz|,touch,cz):")
    for row in sorted(cand,key=lambda x:(-x[0],-x[2])): P("   ",row)
    ids=[row[1] for row in cand if row[0]]
    area=sum(row[3] for row in cand if row[0])
    P("OD faces picked:", ids, "| total area mm2:", area)
    if not ids:  # fallback: 비평면 최대반경 band
        cyl=[row for row in cand if row[4] is False]  # planar False
        cyl.sort(key=lambda x:-x[2])
        rmx=cyl[0][2] if cyl else 0
        ids=[row[1] for row in cyl if row[2]>=rmx-15]
        P("fallback OD:", ids)
    try:
        w=ipk.assign_stationary_wall(ids,"Heat Transfer Coefficient",name="water_jacket",
              htc=f"{HTC}w_per_m2kel", ref_temperature=f"{COOLANT_T}cel")
        P("jacket wall reassigned:", bool(w), "n_faces:", len(ids))
    except Exception as e: P("jacket fail:", repr(e)[:200])
    ipk.save_project()
    P("boundaries:", [(b.name,b.type) for b in ipk.boundaries])
    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
