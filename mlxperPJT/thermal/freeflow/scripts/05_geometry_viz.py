# -*- coding: utf-8 -*-
"""FreeFlow(오일냉각) STL 형상 시각화 - MAPDL viz 스타일."""
import os, glob, traceback
import numpy as np
GEO = r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry"
OUT = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_geom"
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, "log.txt"), "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
# 부품별 색/불투명도/렌더순서
STYLE = {
    "Housing":  dict(color="#c9c2ae", opacity=0.12, lit=True),
    "Stator":   dict(color="#8a9bb0", opacity=1.0,  lit=True),
    "Winding":  dict(color="#c8791f", opacity=1.0,  lit=True),
    "Rotating": dict(color="#1baf7a", opacity=1.0,  lit=True),
    "Inlet":    dict(color="#2a78d6", opacity=1.0,  lit=True),
    "Outlet1":  dict(color="#e34948", opacity=1.0,  lit=True),
    "Outlet2":  dict(color="#e34948", opacity=1.0,  lit=True),
    "Outlet3":  dict(color="#e34948", opacity=1.0,  lit=True),
}
try:
    import pyvista as pv
    pv.OFF_SCREEN = True
    meshes = {}
    for f in sorted(glob.glob(os.path.join(GEO, "*.stl"))):
        name = os.path.splitext(os.path.basename(f))[0]
        m = pv.read(f)
        meshes[name] = m
        b = m.bounds
        P(f"{name:10s} pts={m.n_points:7d} cells={m.n_cells:7d} "
          f"x[{b[0]:.3f},{b[1]:.3f}] y[{b[2]:.3f},{b[3]:.3f}] z[{b[4]:.3f},{b[5]:.3f}]")
    # 전체 bounds
    allpts = np.vstack([m.points for m in meshes.values()])
    P("ALL bounds mm?:", [round(v,2) for v in [allpts[:,0].min(),allpts[:,0].max(),
       allpts[:,1].min(),allpts[:,1].max(),allpts[:,2].min(),allpts[:,2].max()]])

    def render(fname, view, cutaway=False):
        pl = pv.Plotter(off_screen=True, window_size=(1300, 1050)); pl.set_background("white")
        for name, m in meshes.items():
            st = STYLE.get(name, dict(color="gray", opacity=1.0, lit=True))
            mm = m
            if cutaway and name in ("Housing","Stator","Winding","Rotating"):
                # 절반 컷어웨이(y>0 유지)
                try: mm = m.clip(normal="y", origin=m.center, invert=False)
                except Exception: mm = m
            op = st["opacity"]
            if cutaway and name=="Housing": op = 0.06
            pl.add_mesh(mm, color=st["color"], opacity=op, smooth_shading=True,
                        lighting=st["lit"], ambient=0.45, diffuse=0.55,
                        label=name if not cutaway else None)
        pl.add_text(f"FreeFlow 오일냉각 형상 {'(cutaway)' if cutaway else ''}",
                    font_size=12, color="black")
        if view=="iso": pl.view_isometric()
        elif view=="xy": pl.view_xy()
        elif view=="xz": pl.view_xz()
        if not cutaway: pl.add_legend(bcolor="white", size=(0.18,0.22))
        pl.camera.zoom(1.2)
        pl.screenshot(os.path.join(OUT, fname)); pl.close()
        P("saved", fname)

    render("ff_geom_iso.png", "iso")
    render("ff_geom_xy.png", "xy")
    render("ff_geom_cutaway.png", "iso", cutaway=True)
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
