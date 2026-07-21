# -*- coding: utf-8 -*-
"""Icepak stage E: tight region (thin air) + frame-OD HTC wall, re-solve, extract."""
import os, math, json, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\Prius_work\Prius_Icepak.aedt"
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\data\icepak_prius_250A_temps.json"
log = open(SP + r"\ipk_E.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
COOLANT_T, HTC = 27.0, 3000.0
groups = json.load(open(SP + r"\ipk_groups.json"))
role_of = {n:role for role,names in groups.items() for n in names}
allobjs=[n for names in groups.values() for n in names]
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="Prius_CHT", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened. objs:", len(ipk.modeler.object_names))
    # delete old region + jacket wall
    for nm in list(ipk.modeler.object_names):
        if nm.lower()=="region":
            try: ipk.modeler.delete(nm); P("deleted Region obj")
            except Exception as e: P("del region fail",repr(e)[:80])
    for b in list(ipk.boundaries):
        if b.name=="water_jacket":
            try: b.delete(); P("deleted old water_jacket wall")
            except Exception: pass
    # tight region: 1mm absolute pad all sides
    try:
        reg = ipk.modeler.create_region(pad_value=[1,1,1,1,1,1], pad_type="Absolute Offset")
        P("tight region created:", reg.name if reg else None, "bbox:", ipk.modeler[reg.name].bounding_box if reg else None)
    except Exception as e:
        P("create_region fail:", repr(e)[:150])
    # frame OD faces (curved, outer band)
    fname = groups["frame"][0]
    cand=[]
    for f in ipk.modeler[fname].faces:
        c=f.center; r=math.hypot(c[0],c[1])
        try: planar=f.is_planar
        except Exception: planar=True
        cand.append((f.id, r, f.area, planar))
    cyl=[c for c in cand if c[3] is False]
    rmx=max((c[1] for c in cyl), default=0)
    ids=[c[0] for c in cyl if c[1]>=rmx-15]
    P("frame OD faces:", len(ids), "rmax", round(rmx,1))
    try:
        w=ipk.assign_stationary_wall(ids,"Heat Transfer Coefficient",name="water_jacket",
              htc=f"{HTC}w_per_m2kel", ref_temperature=f"{COOLANT_T}cel")
        P("jacket HTC wall:", bool(w))
    except Exception as e: P("jacket fail",repr(e)[:150])
    ipk.save_project()
    # re-solve
    P("analyzing...")
    ok = ipk.analyze_setup("SolveTemp", cores=4)
    P("analyze:", ok)
    ipk.save_project()
    # extract
    df=None
    try:
        fs = ipk.post.create_field_summary()
        for n in allobjs: fs.add_calculation("Object","Volume",n,"Temperature")
        df = fs.get_field_summary_data(setup="SolveTemp : SteadyState", pandas_output=True)
    except Exception as e: P("summary err", repr(e)[:120])
    if df is not None and hasattr(df,"columns"):
        df.to_csv(SP+r"\ipk_summary_E.csv", index=False)
        ecol="Entity"; 
        get=lambda row,key: float(row[key])
        per_obj={}; per_role={}
        for _,row in df.iterrows():
            ent=str(row[ecol]); mx=get(row,"Max"); me=get(row,"Mean"); mn=get(row,"Min")
            per_obj[ent]=dict(max=mx,mean=me,min=mn)
            per_role.setdefault(role_of.get(ent,"?"),[]).append((mx,me))
        role_temps={r:dict(max=max(v[0] for v in vs), mean=sum(v[1] for v in vs)/len(vs)) for r,vs in per_role.items()}
        P("role_temps:", json.dumps(role_temps, ensure_ascii=False))
        json.dump(dict(load="250A_high", cooling="tight-region + frame-OD HTC3000 27C",
                       per_role=role_temps, per_object=per_obj),
                  open(OUTJSON,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
        P("saved JSON")
    else:
        P("no summary df")
    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
