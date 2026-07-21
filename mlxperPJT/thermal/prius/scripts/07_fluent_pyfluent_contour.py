import os, traceback
log=open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\pyf_contour.txt","w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
CAS=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.cas.h5"
OUT=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\viz_prius"
sv=None
try:
    import ansys.fluent.core as pf
    P("launching fluent (gui hidden for rendering)...")
    sv=pf.launch_fluent(mode="solver", processor_count=2, ui_mode="no_gui")
    sv.settings.file.read_case_data(file_name=CAS)
    P("case+data read")
    g=sv.settings.results.graphics
    # 사용 가능 surface 확인
    try:
        surfs=list(sv.settings.results.surfaces.plane_surface.keys())
        P("existing plane surfaces:", surfs)
    except Exception as e: P("surf list:", str(e)[:80])
    # z=0 평면 surface 생성
    made=False
    try:
        sv.settings.results.surfaces.plane_surface["z0"]={}
        ps=sv.settings.results.surfaces.plane_surface["z0"]
        ps.method="xy-plane"; ps.z=0.0
        P("plane z0 created (xy-plane z=0)")
        made=True
    except Exception as e:
        P("plane create fail:", str(e)[:150])
    slist=["z0"] if made else []
    # 벽면도 후보로 추가
    try:
        walls=[w for w in sv.settings.results.graphics.contour["dummy"].surfaces_list.allowed_values()][:0]
    except Exception: pass
    # 컨투어
    cname="temp_contour"
    g.contour[cname]={}
    ct=g.contour[cname]
    ct.field="temperature"
    ct.filled=True
    try:
        av=ct.surfaces_list.allowed_values()
        P("allowed surfaces (first 20):", av[:20])
        # solid wall 계열 + z0
        pick=[s for s in av if any(k in s.lower() for k in ("z0","wall-stator","wall-rotor","wall-magnet","wall-coil","stator","rotor","magnet","coil","phase")) ][:12]
        if made and "z0" not in pick: pick=["z0"]+pick
        ct.surfaces_list=pick if pick else av[:8]
        P("contour surfaces:", pick if pick else av[:8])
    except Exception as e:
        P("surfaces_list set fail:", str(e)[:150])
    # 그래픽스 해상도
    try:
        pic=g.picture
        pic.use_window_resolution=False; pic.x_resolution=1400; pic.y_resolution=1100
    except Exception as e: P("pic res:", str(e)[:80])
    try:
        ct.display()
        P("displayed")
    except Exception as e:
        P("display fail:", str(e)[:200])
    try:
        g.picture.save_picture(file_name=os.path.join(OUT,"fluent_contour_pyf.png"))
        P("saved picture:", os.path.exists(os.path.join(OUT,"fluent_contour_pyf.png")))
    except Exception as e:
        P("save fail:", str(e)[:200])
    sv.exit(); P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    try:
        if sv is not None: sv.exit()
    except: pass
    log.close(); os._exit(0)
