# -*- coding: utf-8 -*-
"""Stator/Rotating STL z-단면 -> 전자계 형상 detail 확인."""
import os, traceback, numpy as np
GEO=r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry"
OUT=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_sec"
os.makedirs(OUT, exist_ok=True)
log=open(os.path.join(OUT,"log.txt"),"w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
try:
    import pyvista as pv
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    pv.OFF_SCREEN=True
    for zc in (-0.13,):  # 활성스택 중앙
        fig,axes=plt.subplots(1,2,figsize=(14,7))
        for ax,name,col in [(axes[0],"Stator","#3b6ea5"),(axes[1],"Rotating","#1baf7a")]:
            m=pv.read(os.path.join(GEO,name+".stl"))
            sl=m.slice(normal="z",origin=(0,0,zc))
            pts=sl.points
            P(f"{name} z={zc}: slice pts={sl.n_points} lines={sl.n_cells}")
            # 단면 점 산포 + 반경 히스토그램 정보
            r=np.sqrt(pts[:,0]**2+pts[:,1]**2)
            P(f"  r(mm): min={r.min()*1000:.1f} max={r.max()*1000:.1f} "
              f"n_unique_r_bins={len(np.unique(np.round(r*1000)))}")
            ax.scatter(pts[:,0]*1000, pts[:,1]*1000, s=2, c=col)
            ax.set_aspect("equal"); ax.set_title(f"{name} z={zc*1000:.0f}mm  (r {r.min()*1000:.0f}-{r.max()*1000:.0f}mm)")
            ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
        fig.suptitle(f"FreeFlow Stator/Rotor cross-section @ z={zc*1000:.0f}mm")
        fig.tight_layout(); fig.savefig(os.path.join(OUT,f"section_z{int(zc*1000)}.png"),dpi=140); plt.close(fig)
        P("saved section png")
    P("DONE-OK")
except Exception:
    P("EXC:",traceback.format_exc())
finally:
    log.close()
os._exit(0)
