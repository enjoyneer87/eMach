# -*- coding: utf-8 -*-
"""Icepak stage F: 프레임 OD를 고정온도(Dirichlet) 경계로 - HTC벽 단락 회피 검증."""
import os, math, json, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\Prius_work\Prius_Icepak.aedt"
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\data\icepak_prius_250A_temps.json"
log = open(SP + r"\ipk_F.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
FRAME_T = 40.0   # Fluent frame_mean ~44.8, jacket-contact side ~40C
groups = json.load(open(SP + r"\ipk_groups.json"))
role_of = {n:role for role,names in groups.items() for n in names}
allobjs=[n for names in groups.values() for n in names]
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="Prius_CHT", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened. problem_type:", ipk.problem_type)
    for b in list(ipk.boundaries):
        if b.name=="water_jacket":
            try: b.delete(); P("deleted old wall")
            except Exception: pass
    fname = groups["frame"][0]
    cyl=[]
    for f in ipk.modeler[fname].faces:
        c=f.center; r=math.hypot(c[0],c[1])
        try: planar=f.is_planar
        except Exception: planar=True
        if planar is False: cyl.append((f.id,r))
    rmx=max((r for _,r in cyl), default=0)
    ids=[fid for fid,r in cyl if r>=rmx-15]
    P("frame OD faces:", len(ids), "rmax", round(rmx,1))
    try:
        w=ipk.assign_stationary_wall(ids,"Temperature",name="jacket_fixedT",
              temperature=f"{FRAME_T}cel")
        P("fixed-T wall:", bool(w), "T=", FRAME_T)
    except Exception as e: P("wall fail", repr(e)[:150])
    ipk.save_project()
    P("analyzing...")
    ok=ipk.analyze_setup("SolveTemp", cores=4)
    P("analyze:", ok)
    ipk.save_project()
    df=None
    try:
        fs=ipk.post.create_field_summary()
        for n in allobjs: fs.add_calculation("Object","Volume",n,"Temperature")
        df=fs.get_field_summary_data(setup="SolveTemp : SteadyState", pandas_output=True)
    except Exception as e: P("summary err", repr(e)[:120])
    if df is not None and hasattr(df,"columns"):
        df.to_csv(SP+r"\ipk_summary_F.csv", index=False)
        per_obj={}; per_role={}
        for _,row in df.iterrows():
            ent=str(row["Entity"]); mx=float(row["Max"]); me=float(row["Mean"]); mn=float(row["Min"])
            per_obj[ent]=dict(max=mx,mean=me,min=mn)
            per_role.setdefault(role_of.get(ent,"?"),[]).append((mx,me))
        role_temps={r:dict(max=max(v[0] for v in vs),mean=sum(v[1] for v in vs)/len(vs)) for r,vs in per_role.items()}
        P("role_temps:", json.dumps(role_temps, ensure_ascii=False))
        json.dump(dict(load="250A_high", cooling=f"frame-OD fixed {FRAME_T}C (Dirichlet)",
                       per_role=role_temps, per_object=per_obj),
                  open(OUTJSON,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
        P("saved JSON")
    else:
        P("no summary")
    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
