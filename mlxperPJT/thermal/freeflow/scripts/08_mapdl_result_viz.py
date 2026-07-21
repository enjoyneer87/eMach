# -*- coding: utf-8 -*-
"""e10 FreeFlow MAPDL 결과 시각화 - thermal_viz.py(ThermalViz) 재사용."""
import sys, os, traceback
sys.path.insert(0, r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal")
L=open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_viz.txt","w",encoding="utf-8")
def P(*a): L.write(" ".join(str(x) for x in a)+"\n"); L.flush()
try:
    from thermal_viz import ThermalViz
    RTH=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_mapdl_run10\file.rth"
    OUT=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\viz"
    os.makedirs(OUT, exist_ok=True)
    tv=ThermalViz(RTH, OUT, label="e10 FreeFlow (oil-cooled, 460A/16000rpm)",
                  clim_lo=70.0, mats=dict(stator=1, coil=3, rotor=5))
    P(f"loaded. clim={tv.clim} nsets={tv.nsets} parts={list(tv._sub)} R={tv.R:.3f}")
    tv.contour_png(); P("contour_iso/z0 ok")
    tv.cut3d_png(); P("cut_3d ok")
    tv.component_png(); P("coil_only(+magnet_only skip) ok")
    tv.history_png(); P("component_history ok (single point)")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    L.close()
os._exit(0)
