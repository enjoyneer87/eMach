# -*- coding: utf-8 -*-
"""iso/슬라이스 재생성: 솔리드 clim + 이산밴드 + 좁은범위(표면 구조) 뷰."""
import os, glob, traceback
import numpy as np
log = open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\iso_banded.txt", "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()
try:
    import pyvista as pv
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN = True
    SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
    OUT = os.path.join(SP, "viz_real")
    rth = sorted(glob.glob(os.path.join(SP, "real_*", "file.rth")),
                 key=os.path.getmtime)[-1]
    res = rd.read_binary(rth)
    grid = res.grid.copy()
    solid = grid.extract_cells(np.isin(grid.celltypes, (10, 24)))
    opid = solid.point_data["vtkOriginalPointIds"]
    _, T = res.nodal_temperature(res.nsets - 1)
    Ts = np.asarray(T, float)[opid]
    solid.point_data["Temperature (degC)"] = Ts
    P("body:", round(float(np.nanmin(Ts)),1), "~", round(float(np.nanmax(Ts)),1))
    sb = dict(title="Temperature (degC)", title_font_size=16,
              label_font_size=13, n_labels=7, fmt="%.0f", color="black")
    surf = solid.extract_surface()
    tmin, tmax = float(np.nanmin(Ts)), float(np.nanmax(Ts))
    views = [
        # 전체 범위 밴드 (경계층 포함)
        ("real_contour_iso.png", surf, [tmin, tmax], 14, True),
        # 좁은 범위: 표면(140~) 구조 강조, WJ 패치는 하한색 클립
        ("real_contour_iso_band.png", surf, [140.0, tmax], 12, True),
        ("real_contour_slice_x0.png", solid.slice(normal="x"),
         [tmin, tmax], 14, False),
        ("real_contour_slice_z0.png", solid.slice(normal="z"),
         [tmin, tmax], 14, False),
    ]
    for fname, mesh, clim, nc, lit in views:
        p = pv.Plotter(off_screen=True, window_size=(1280, 960))
        p.set_background("white")
        kw = dict(cmap="inferno", clim=clim, n_colors=nc,
                  scalar_bar_args=sb, below_color="#3987e5")
        if lit:
            kw.update(smooth_shading=True, ambient=0.62, diffuse=0.38,
                      specular=0.0)
        else:
            kw.update(lighting=False)
        p.add_mesh(mesh, **kw)
        p.add_text(f"REAL geometry @ t=900s  (range {clim[0]:.0f}~{clim[1]:.0f})",
                   font_size=12, color="black")
        if "slice_x0" in fname:
            p.view_vector((1, 0, 0), viewup=(0, 1, 0))
        elif "slice_z0" in fname:
            p.view_xy()
        else:
            p.view_isometric()
        p.screenshot(os.path.join(OUT, fname))
        p.close()
        P("saved", fname)
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
