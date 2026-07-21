import os, traceback
log=open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\pyf_contour.txt","w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
CAS=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.cas.h5"
OUT=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\viz_prius"
sv=None
try:
    import ansys.fluent.core as pf
    P("launching fluent solver (post)...")
    sv=pf.launch_fluent(mode="solver", processor_count=2, ui_mode="no_gui", precision="double",
                        product_version="26.1.0" if hasattr(pf,'') else None) \
       if False else pf.launch_fluent(mode="solver", processor_count=2, ui_mode="no_gui")
    P("fluent up:", sv.get_fluent_version() if hasattr(sv,'get_fluent_version') else "?")
    sv.settings.file.read_case_data(file_name=CAS.replace(".cas.h5",".cas.h5"))
    P("case+data read")
    # 온도 컨투어 (전체 solid)
    g=sv.settings.results.graphics
    g.contour["T"]={"field":"temperature","surfaces_list":[],"filled":True}
    P("contour created")
    sv.settings.results.graphics.contour["T"].display()
    sv.settings.results.graphics.picture.save_picture(file_name=os.path.join(OUT,"fluent_contour_pyf.png"))
    P("saved contour")
    sv.exit()
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    try:
        if sv is not None: sv.exit()
    except: pass
    log.close(); os._exit(0)
