import os, json, time, traceback
log=open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\prius_coreloss2.txt","w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
PATH=r"D:\KDH\simVary\Ansys_Thermal\SyC_Mxwl_Fluent_eMachine_2022r2\Initial_ProjectFiles\Prius_Model_24R2.aedt"
d=None
try:
    import numpy as np
    from ansys.aedt.core import Desktop, Maxwell2d
    d=Desktop(version="2026.1", new_desktop=True, non_graphical=True)
    P("pid:", d.aedt_process_id)
    m2d=Maxwell2d(project=PATH)
    setup=m2d.setups[0]
    P("setup:", setup.name, "solved:", setup.is_solved)
    # OutputPerObjectCoreLoss / SolidLoss 활성화
    try:
        setup.props["OutputPerObjectCoreLoss"]=True
        setup.props["OutputPerObjectSolidLoss"]=True
        setup.update()
        P("per-object loss flags set")
    except Exception as e:
        P("prop set fail:", str(e)[:150])
    # 강제 재솔브
    P("re-solving...")
    t0=time.time()
    ok=m2d.analyze(setup=setup.name, cores=4)
    P(f"analyze: {ok} ({(time.time()-t0)/60:.1f}min)")
    sweep=f"{setup.name} : Transient"
    objs=m2d.modeler.object_names
    stator=[o for o in objs if o.lower().startswith("stator")]
    rotor=[o for o in objs if o.lower().startswith("rotor")]
    P("stator n:", len(stator), "rotor:", rotor)
    def avg(expr, cat=None, frac=0.5):
        try:
            sd=m2d.post.get_solution_data(expressions=expr, setup_sweep_name=sweep,
                domain="Sweep", report_category=cat, primary_sweep_variable="Time")
            if sd is None or isinstance(sd,bool): P(f"  {expr}: no data"); return None
            t=np.array(sd.primary_sweep_values,float); v=np.array(sd.data_real(),float)
            u="s"
            try:u=sd.units_sweeps.get("Time","s")
            except:pass
            t=t*{"s":1,"ms":1e-3,"us":1e-6}.get(u,1); m=t>=t.max()*frac
            uv="W"
            try:uv=sd.units_data.get(expr,"W")
            except:pass
            v=v*{"W":1,"mW":1e-3,"kW":1e3}.get(uv,1); a=float(v[m].mean())
            P(f"  {expr}: unit={uv} avg={a:.2f} W"); return a
        except Exception as e:
            P(f"  [fail] {expr}: {str(e)[:120]}"); return None
    # per-object 활성화되면 "CoreLoss(<obj>)" 리포트 가능. 로터 합산 -> 스테이터=전체-로터
    res={}
    res["CoreLoss_total"]=avg("CoreLoss")
    # 로터 오브젝트별 CoreLoss 합
    rot_sum=0.0; got=False
    for ro in rotor:
        vv=avg(f"CoreLoss({ro})")
        if vv is not None: rot_sum+=vv; got=True
    if got:
        res["CoreLoss_Rotor"]=round(rot_sum,1)
        res["CoreLoss_Stator"]=round((res["CoreLoss_total"] or 0)-rot_sum,1)
        P(f"SPLIT: stator={res['CoreLoss_Stator']} rotor={res['CoreLoss_Rotor']}")
    else:
        P("per-object CoreLoss(obj) 미지원 -> 리포트 카테고리 시도")
        # 대안: EddyCurrentLoss/HysteresisLoss per object 등
    P("RESULT:", json.dumps(res))
    # JSON 갱신
    jp=r"D:\KDH\simVary\Ansys_Thermal\prius_losses.json"
    data=json.load(open(jp,encoding="utf-8"))
    if got:
        data["CoreLoss_Stator"]=res["CoreLoss_Stator"]
        data["CoreLoss_Rotor"]=res["CoreLoss_Rotor"]
        data["_core_split_note"]="OutputPerObjectCoreLoss 재솔브로 정밀분리"
    json.dump(data, open(jp,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    m2d.save_project()
    m2d.release_desktop(close_projects=True, close_on_exit=True)
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    try:
        if d is not None: d.release_desktop(close_projects=True, close_on_exit=True)
    except: pass
    log.close(); os._exit(0)
