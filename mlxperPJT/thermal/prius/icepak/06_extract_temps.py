# -*- coding: utf-8 -*-
"""Icepak stage D2: robust per-object Temperature extraction (export_csv + summary data)."""
import os, json, csv, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PROJ = r"D:\KDH\simVary\Ansys_Thermal\Prius_work\Prius_Icepak.aedt"
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\data\icepak_prius_250A_temps.json"
log = open(SP + r"\ipk_D2.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
groups = json.load(open(SP + r"\ipk_groups.json"))
role_of = {n:role for role,names in groups.items() for n in names}
allobjs=[n for names in groups.values() for n in names]
try:
    from ansys.aedt.core import Icepak
    ipk = Icepak(project=PROJ, design="Prius_CHT", version="2026.1",
                 non_graphical=True, new_desktop=True)
    P("opened. setups:", ipk.setup_names)
    try: sweeps = ipk.existing_analysis_sweeps
    except Exception as e: sweeps=None; P("sweeps err", repr(e)[:80])
    P("existing_analysis_sweeps:", sweeps)
    try: P("nominal_adaptive:", ipk.nominal_adaptive)
    except Exception: pass

    cand = []
    if sweeps: cand += list(sweeps)
    cand += ["SolveTemp : SteadyState", "SolveTemp", None]
    P("candidates:", cand)

    df=None; used=None
    for s in cand:
        try:
            fs = ipk.post.create_field_summary()
            for n in allobjs:
                fs.add_calculation("Object","Volume",n,"Temperature")
            d = fs.get_field_summary_data(setup=s, pandas_output=True)
            if hasattr(d,"columns"):
                df=d; used=s; P(f"OK setup={s!r} cols={list(d.columns)} rows={len(d)}"); break
            else:
                P(f"setup={s!r} -> {type(d)} {str(d)[:60]}")
        except Exception as e:
            P(f"setup={s!r} EXC {repr(e)[:100]}")
    # export_csv fallback
    if df is None:
        for s in cand:
            try:
                fs = ipk.post.create_field_summary()
                for n in allobjs:
                    fs.add_calculation("Object","Volume",n,"Temperature")
                csvp = SP + r"\ipk_summary.csv"
                r = fs.export_csv(csvp, setup=s)
                if os.path.exists(csvp) and os.path.getsize(csvp)>0:
                    used=s; P(f"export_csv OK setup={s!r}")
                    with open(csvp) as f: P("CSV head:", f.read()[:500])
                    break
            except Exception as e:
                P(f"export_csv setup={s!r} EXC {repr(e)[:100]}")

    results={}
    if df is not None:
        df.to_csv(SP+r"\ipk_summary.csv", index=False)
        cols={c.lower():c for c in df.columns}
        ecol=cols.get("entity") or list(df.columns)[0]
        maxc=next((df.columns[i] for i,c in enumerate(df.columns) if "max" in c.lower()), None)
        meanc=next((df.columns[i] for i,c in enumerate(df.columns) if "mean" in c.lower()), None)
        minc=next((df.columns[i] for i,c in enumerate(df.columns) if "min" in c.lower()), None)
        P("cols map:", ecol, maxc, meanc, minc)
        per_obj={}; per_role={}
        for _,row in df.iterrows():
            ent=str(row[ecol])
            mx=float(row[maxc]) if maxc else None
            me=float(row[meanc]) if meanc else None
            mn=float(row[minc]) if minc else None
            per_obj[ent]=dict(max=mx,mean=me,min=mn)
            role=role_of.get(ent,"?")
            per_role.setdefault(role,[]).append((mx,me))
        role_temps={}
        for role,vals in per_role.items():
            mxs=[v[0] for v in vals if v[0] is not None]; mes=[v[1] for v in vals if v[1] is not None]
            role_temps[role]=dict(max=max(mxs) if mxs else None, mean=sum(mes)/len(mes) if mes else None)
        results=dict(load="250A_high", cooling="water-jacket frame-OD HTC3000 27C",
                     setup_used=str(used), per_role=role_temps, per_object=per_obj)
        P("role_temps:", json.dumps(role_temps, ensure_ascii=False))
        os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)
        json.dump(results, open(OUTJSON,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
        P("saved JSON")
    else:
        P("FAILED to get field summary via all candidates")
    P("DONE-OK")
    ipk.release_desktop(close_projects=True, close_desktop=True)
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
