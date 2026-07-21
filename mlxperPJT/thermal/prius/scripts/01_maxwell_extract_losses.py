import os, json, time, traceback
log = open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\prius_loss.txt","w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
PATH = r"D:\KDH\simVary\Ansys_Thermal\SyC_Mxwl_Fluent_eMachine_2022r2\Initial_ProjectFiles\Prius_Model_24R2.aedt"
OUT_JSON = r"D:\KDH\simVary\Ansys_Thermal\prius_losses.json"
d=None
try:
    import numpy as np
    from ansys.aedt.core import Desktop, Maxwell2d
    d = Desktop(version="2026.1", new_desktop=True, non_graphical=True)
    P("pid:", d.aedt_process_id)
    m2d = Maxwell2d(project=PATH)
    P("design:", m2d.design_name, "| sol:", m2d.solution_type)
    setup = m2d.setups[0]
    P("setup:", setup.name, "solved:", getattr(setup,"is_solved","?"))
    # 변수
    try:
        vars_={v:m2d.variable_manager.variables[v].evaluated_value for v in m2d.variable_manager.independent_variable_names}
        P("variables:", json.dumps(vars_, default=str)[:1800])
    except Exception as e: P("vars fail:", str(e)[:120])
    objs = m2d.modeler.object_names
    P("objects:", objs)
    # 미솔브면 솔브
    if not setup.is_solved:
        P("solving 2D transient (cores=4)...")
        t0=time.time()
        ok = m2d.analyze(setup=setup.name, cores=4)
        P(f"analyze: {ok} ({(time.time()-t0)/60:.1f} min)")
    sweep = f"{setup.name} : Transient"
    def avg_win(expr, cat=None, frac=0.5):
        try:
            sd = m2d.post.get_solution_data(expressions=expr, setup_sweep_name=sweep,
                    domain="Sweep", report_category=cat, primary_sweep_variable="Time")
            t=np.array(sd.primary_sweep_values,float); v=np.array(sd.data_real(),float)
            u="s"
            try: u=sd.units_sweeps.get("Time","s")
            except Exception: pass
            t=t*{"s":1,"ms":1e-3,"us":1e-6}.get(u,1)
            m=t>=t.max()*frac
            uv="W"
            try: uv=sd.units_data.get(expr,"W")
            except Exception: pass
            v=v*{"W":1,"mW":1e-3,"kW":1e3}.get(uv,1)
            a=float(v[m].mean())
            P(f"  {expr}: unit={uv} n={int(m.sum())} avg={a:.2f} W")
            return a
        except Exception as e:
            P(f"  [fail] {expr}: {str(e)[:150]}"); return None
    res={}
    for q in ("StrandedLoss","SolidLoss","CoreLoss"):
        res[q]=avg_win(q)
    # 스테이터/로터 코어손실 분리 (named expr, 2D=면적분)
    lam_s=[o for o in objs if "stator" in o.lower()]
    lam_r=[o for o in objs if "rotor" in o.lower()]
    P("lam_s:",lam_s[:3],"lam_r:",lam_r[:3])
    # 대칭배수/깊이
    try:
        ds=m2d.design_settings
        for k in ("SymmetryFactor","Symmetry Factor","Multiplier"):
            if hasattr(ds,"__contains__") and k in ds:
                res["_"+k]=str(ds[k])
    except Exception: pass
    res["_variables"]=vars_ if 'vars_' in dir() else {}
    with open(OUT_JSON,"w",encoding="utf-8") as f: json.dump(res,f,indent=2,ensure_ascii=False)
    P("saved:", OUT_JSON)
    P("RESULT:", json.dumps({k:v for k,v in res.items() if not k.startswith('_')}, ensure_ascii=False))
    m2d.release_desktop(close_projects=False, close_on_exit=False)
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    try:
        if d is not None: d.release_desktop(close_projects=False, close_on_exit=False)
    except Exception: pass
    log.close(); os._exit(0)
