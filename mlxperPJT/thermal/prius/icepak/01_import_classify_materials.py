# -*- coding: utf-8 -*-
"""Icepak stage A: launch, import Prius STEP, classify by bbox, assign materials, save."""
import os, math, json, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
STP = (r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019"
       r"\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.stp")
PROJ = r"D:\KDH\simVary\Ansys_Thermal\Prius_work\Prius_Icepak.aedt"
log = open(SP + r"\ipk_A.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()

try:
    os.makedirs(os.path.dirname(PROJ), exist_ok=True)
    from ansys.aedt.core import Icepak
    P("launching Icepak 2026.1 non-graphical...")
    ipk = Icepak(project=PROJ, design="Prius_CHT", solution_type="SteadyState",
                 version="2026.1", non_graphical=True, new_desktop=True)
    P("Icepak launched. design:", ipk.design_name)
    ipk.modeler.model_units = "mm"

    # import STEP
    P("importing STEP...")
    before = set(ipk.modeler.object_names)
    ipk.modeler.import_3d_cad(STP)
    after = ipk.modeler.object_names
    new = [n for n in after if n not in before]
    P("imported objects:", len(new))

    # classify by bbox (same logic as gmsh pipeline)
    def cls(name):
        bb = ipk.modeler[name].bounding_box  # xmin ymin zmin xmax ymax zmax (mm)
        xmn,ymn,zmn,xmx,ymx,zmx = bb
        V = ipk.modeler[name].volume/1e3  # mm3 -> cm3
        corners = [(xmn,ymn),(xmx,ymx),(xmn,ymx),(xmx,ymn)]
        rmx = max(math.hypot(a,b) for a,b in corners)
        active = abs(zmn+41.9)<3 and abs(zmx-41.9)<3
        return V,rmx,zmn,zmx,active

    groups = {}  # role -> [names]
    info = {}
    for n in new:
        V,rmx,zmn,zmx,active = cls(n)
        info[n]=(round(V,1),round(rmx,1),round(zmn,0),round(zmx,0),active)
        role=None
        if active:
            if V>200 and rmx>140: role="stator"
            elif 60<V<130 and 85<rmx<110: role="rotor"
            elif 10<V<25 and 100<rmx<135: role="coil"
            elif 5<V<15 and 60<rmx<90: role="magnet"
        if role is None:
            if rmx<75 and abs(zmn)>100: role="shaft"
            elif V>250 and rmx>180 and abs(zmx)<70: role="frame"
            elif V>120 and abs(zmn)>45 and rmx>180: role="cover"
            elif abs(zmx)>70 and 100<rmx<140: role="endwdg"
            elif 60<rmx<120 and abs(zmx)<70: role="insulation"
            else: role="other"
        groups.setdefault(role,[]).append(n)
    for role,names in groups.items():
        P(f"  {role}: {len(names)} -> {[(nm,info[nm]) for nm in names]}")

    # material assignment
    mat_map = {"stator":"steel_stainless","rotor":"steel_stainless","frame":"Al-Extruded",
               "cover":"Al-Extruded","coil":"copper","endwdg":"copper","magnet":"Ceramic_material",
               "shaft":"steel_stainless","insulation":"epoxy","other":"epoxy"}
    for role,names in groups.items():
        m = mat_map.get(role,"steel_stainless")
        for n in names:
            try: ipk.assign_material(n, m)
            except Exception as e: P("   matfail",n,m,repr(e)[:80])
    P("materials assigned")

    json.dump({r:groups[r] for r in groups}, open(SP+r"\ipk_groups.json","w"), indent=1)
    ipk.save_project()
    P("saved:", PROJ)
    P("DONE-OK")
    ipk.release_desktop(close_projects=False, close_desktop=False)
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
