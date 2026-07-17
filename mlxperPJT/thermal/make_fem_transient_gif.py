# -*- coding: utf-8 -*-
"""FEM 3D 형상 시간전개 GIF: ① 반단면 컷어웨이 ② 코일+자석 내부 부품."""
import os
import glob
import traceback
import numpy as np

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT = os.path.join(SP, "viz_real")
log = open(os.path.join(SP, "fem_gif.txt"), "w", encoding="utf-8")
def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

try:
    import pyvista as pv
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN = True

    rth = sorted(glob.glob(os.path.join(SP, "real_*", "file.rth")),
                 key=os.path.getmtime)[-1]
    res = rd.read_binary(rth)
    nsets = res.nsets
    times = np.asarray(res.time_values, float)
    grid = res.grid.copy()
    solid = grid.extract_cells(np.isin(grid.celltypes, (10, 24)))
    opid = solid.point_data["vtkOriginalPointIds"]
    mats = np.asarray(solid.cell_data["ansys_material_type"])

    coil = solid.extract_cells(np.where(mats == 3)[0])
    cpid = np.asarray(coil.point_data["vtkOriginalPointIds"])
    mag = solid.extract_cells(np.where(mats == 2)[0])
    mpid = np.asarray(mag.point_data["vtkOriginalPointIds"])
    ghost = solid.extract_cells(
        np.where((mats == 1) | (mats == 5))[0]).extract_surface()

    _, T_end = res.nodal_temperature(nsets - 1)
    T_end = np.asarray(T_end, float)
    clim = [70.0, float(np.nanmax(T_end[opid]))]
    P("clim:", [round(c, 1) for c in clim])
    sb = dict(title="Temperature (degC)", title_font_size=14,
              label_font_size=12, n_labels=6, fmt="%.0f", color="black")

    # ── ① 3D 반단면 컷어웨이 GIF (프레임별 독립 렌더 + imageio 조립) ─────
    import imageio.v2 as imageio
    # 볼륨 clip 은 VTK 크래시 -> 외피(폴리데이터) clip + x=0 슬라이스 조합
    solid.point_data["pid"] = opid.astype(np.float64)
    ext = solid.extract_surface()
    ext_half = ext.clip(normal=(1, 0, 0), origin=(0, 0, 0), invert=True)  # x<0 유지, +x에서 단면 조망
    epid = np.clip(np.rint(np.asarray(ext_half.point_data["pid"])
                           ).astype(np.int64), 0, len(T_end) - 1)
    P("ext_half pts:", ext_half.n_points)
    frames = []
    for i in range(nsets):
        _, T = res.nodal_temperature(i)
        T = np.asarray(T, float)
        ext_half.point_data["Temperature (degC)"] = T[epid]
        solid.point_data["Temperature (degC)"] = T[opid]
        sl = solid.slice(normal="x")
        pl = pv.Plotter(off_screen=True, window_size=(1000, 780))
        pl.set_background("white")
        pl.add_mesh(ext_half, scalars="Temperature (degC)", cmap="inferno", clim=clim, n_colors=14,
                    lighting=True, ambient=0.6, diffuse=0.4, specular=0.0,
                    scalar_bar_args=sb)
        pl.add_mesh(sl, scalars="Temperature (degC)", cmap="inferno", clim=clim, n_colors=14,
                    lighting=False, show_scalar_bar=False)
        pl.add_text(f"t = {times[i]:5.0f} s   half-section "
                    f"(top: WJ / bottom: ATF)", font_size=13, color="black")
        pl.view_vector((1, -0.45, 0.35), viewup=(0, 1, 0))   # 절단면을 정면으로
        pl.camera.zoom(1.05)
        frames.append(pl.screenshot(return_img=True))
        pl.close()
    gif1 = os.path.join(OUT, "real_transient_3d_cut.gif")
    imageio.mimsave(gif1, frames, fps=4, loop=0)
    P("gif1 saved:", f"{os.path.getsize(gif1)/1e6:.1f} MB")

    # ── ② 코일+자석 내부 부품 GIF ───────────────────────────────────────
    gif2 = os.path.join(OUT, "real_transient_internal.gif")
    frames = []
    for i in range(nsets):
        _, T = res.nodal_temperature(i)
        T = np.asarray(T, float)
        coil.point_data["Temperature (degC)"] = T[cpid]
        mag.point_data["Temperature (degC)"] = T[mpid]
        pl = pv.Plotter(off_screen=True, window_size=(1000, 780))
        pl.set_background("white")
        pl.add_mesh(ghost, color="#d9d6c8", opacity=0.08, lighting=True,
                    ambient=0.5)
        pl.add_mesh(coil, scalars="Temperature (degC)", cmap="inferno", clim=clim, n_colors=14,
                    lighting=True, ambient=0.6, diffuse=0.4, specular=0.0,
                    scalar_bar_args=sb)
        pl.add_mesh(mag, scalars="Temperature (degC)", cmap="inferno", clim=clim, n_colors=14,
                    lighting=True, ambient=0.6, diffuse=0.4, specular=0.0,
                    show_scalar_bar=False)
        cm_, mm_ = float(np.nanmax(T[cpid])), float(np.nanmax(T[mpid]))
        pl.add_text(f"t = {times[i]:5.0f} s   coil max {cm_:5.1f} C | "
                    f"magnet max {mm_:5.1f} C", font_size=13, color="black")
        pl.view_vector((1, -0.4, 0.55), viewup=(0, 1, 0))
        pl.camera.zoom(1.2)
        frames.append(pl.screenshot(return_img=True))
        pl.close()
    imageio.mimsave(gif2, frames, fps=4, loop=0)
    P("gif2 saved:", f"{os.path.getsize(gif2)/1e6:.1f} MB")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
