# -*- coding: utf-8 -*-
"""Icepak stage B2: proper materials, frame-OD jacket convection, verify sources."""
import os, math, json, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\Prius_work\Prius_Icepak.aedt"
log = open(SP + r"\ipk_B2.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
COOLANT_T, HTC = 27.0, 3000.0
groups = json.load(open(SP + r"\ipk_groups.json"))
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="Prius_CHT", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened. problem_type:", ipk.problem_type)

    # ---- materials (proper API) ----
    def mkmat(name, k, rho, cp):
        try:
            if not ipk.materials.exists_material(name):
                m = ipk.materials.add_material(name)
            else:
                m = ipk.materials[name]
            m.thermal_conductivity = k   # scalar or [kx,ky,kz]
            m.mass_density = rho; m.specific_heat = cp
            return name
        except Exception as e:
            P("  mkmat fail", name, repr(e)[:100]); return "Al-Extruded"
    M = dict(
        lam=mkmat("lam_steel",25.0,7650,460),
        mag=mkmat("ndfeb",9.0,7500,460),
        al =mkmat("al_hous",200.0,2700,900),
        shf=mkmat("shaft_steel",45.0,7850,475),
        ins=mkmat("epoxy_ins",0.3,1400,1000),
        coil=mkmat("coil_aniso",[2.5,2.5,250.0],8300,385),
    )
    P("materials:", M)
    role_mat = {"stator":M["lam"],"rotor":M["lam"],"magnet":M["mag"],"frame":M["al"],
                "cover":M["al"],"shaft":M["shf"],"insulation":M["ins"],
                "coil":M["coil"],"endwdg":M["coil"],"other":M["ins"]}
    for role,names in groups.items():
        for n in names:
            try: ipk.assign_material(n, role_mat.get(role,M["al"]))
            except Exception as e: P("  assignmat fail",n,repr(e)[:80])
    P("materials reassigned")

    # ---- frame OD faces: dump then pick ----
    fname = groups["frame"][0]
    rows=[]
    for f in ipk.modeler[fname].faces:
        c=f.center; r=math.hypot(c[0],c[1]); rows.append((f.id, round(r,1), round(f.area,0), [round(x,1) for x in c]))
    rows.sort(key=lambda x:-x[1])
    P(f"frame '{fname}' faces (id, r_center, area, center) sorted by radius:")
    for row in rows: P("   ", row)
    rmax = rows[0][1] if rows else 0
    # 외곽 원통면: 반경 최상위 band + 면적 큰 것 (플랜지 코너 제외)
    picked = [r for r in rows if r[1] >= rmax-25 and r[2] > 2000]
    if not picked: picked = rows[:2]
    ids=[r[0] for r in picked]; area=sum(r[2] for r in picked)
    P("picked OD faces:", picked, "| total area mm2:", area)
    try:
        w=ipk.assign_stationary_wall(ids, "Heat Transfer Coefficient",
              name="water_jacket", htc=f"{HTC}w_per_m2kel", ref_temperature=f"{COOLANT_T}cel")
        P("jacket wall assigned:", bool(w), "faces:", ids)
    except Exception as e: P("jacket wall fail:", repr(e)[:200])

    # ---- verify sources ----
    try:
        srcs = ipk.get_all_sources()
        P("sources count:", len(srcs) if srcs else 0, "->", srcs)
    except Exception as e: P("get_all_sources err:", repr(e)[:100])
    # boundaries list
    try:
        P("boundaries:", [(b.name, b.type) for b in ipk.boundaries])
    except Exception as e: P("boundaries err:", repr(e)[:100])

    ipk.save_project()
    P("saved. DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
