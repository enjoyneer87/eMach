# -*- coding: utf-8 -*-
"""내부 부품(코일/자석) 전용 시각화: 자체 스케일 3D + avg/max 시간이력."""
import os
import glob
import traceback
import numpy as np

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT = os.path.join(SP, "viz_real")
log = open(os.path.join(SP, "internal_viz.txt"), "w", encoding="utf-8")
def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

try:
    import pyvista as pv
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN = True

    rth = sorted(glob.glob(os.path.join(SP, "real_*", "file.rth")),
                 key=os.path.getmtime)[-1]
    res = rd.read_binary(rth)
    grid = res.grid.copy()
    tets = np.isin(grid.celltypes, (10, 24))
    solid = grid.extract_cells(tets)
    mats = np.asarray(solid.cell_data["ansys_material_type"])
    opid_solid = solid.point_data["vtkOriginalPointIds"]
    nsets = res.nsets
    times = np.asarray(res.time_values, float)

    def part(mat):
        m = solid.extract_cells(np.where(mats == mat)[0])
        return m, np.asarray(m.point_data["vtkOriginalPointIds"])

    coil, cpid = part(3)
    mag, mpid = part(2)
    rotor, rpid = part(5)
    stat, spid = part(1)
    P("coil pts:", coil.n_points, "| magnet pts:", mag.n_points)

    _, T_last = res.nodal_temperature(nsets - 1)
    T_last = np.asarray(T_last, float)

    sb = dict(title="Temperature (degC)", title_font_size=16,
              label_font_size=13, n_labels=7, fmt="%.1f", color="black")

    def render(mesh, pid, fname, title, ghost=None, view=None):
        tv = T_last[pid]
        mesh.point_data["Temperature (degC)"] = tv
        clim = [float(np.nanmin(tv)), float(np.nanmax(tv))]
        p = pv.Plotter(off_screen=True, window_size=(1400, 1000))
        p.set_background("white")
        if ghost is not None:
            p.add_mesh(ghost.extract_surface(), color="#d9d6c8",
                       opacity=0.10, lighting=True, ambient=0.5)
        kw = dict(cmap="inferno", clim=clim, n_colors=12,
                  scalar_bar_args=sb)
        if view == "xy":
            kw.update(lighting=False)          # 평면 뷰는 무조명 평면색
        else:
            kw.update(smooth_shading=False, ambient=0.55, diffuse=0.45,
                      specular=0.0)
        p.add_mesh(mesh, **kw)
        p.add_text(f"{title}  (range {clim[0]:.1f} ~ {clim[1]:.1f} degC)",
                   font_size=12, color="black")
        if view == "xy":
            p.view_xy()
        else:
            p.view_vector((1, -0.4, 0.55), viewup=(0, 1, 0))
        p.camera.zoom(1.15)
        p.screenshot(os.path.join(OUT, fname))
        p.close()
        P("saved", fname, "clim", [round(c, 1) for c in clim])

    # ① 코일만 (자체 스케일): iso + 축방향 뷰(슬롯별 편차)
    render(coil, cpid, "real_coil_only_iso.png",
           "COIL only - slot conductors @ t=900s")
    render(coil, cpid, "real_coil_only_axial.png",
           "COIL only - axial view (WJ top / ATF bottom)", view="xy")
    # ② 자석만 (+로터 고스트)
    render(mag, mpid, "real_magnet_only.png",
           "MAGNET only @ t=900s (36 seg x 8 pole)", ghost=rotor)

    # ③ 부품별 avg/max 시간이력
    comp = {"Coil": cpid, "Magnet": mpid, "RotorCore": rpid,
            "StatorCore": spid}
    hist = {k: {"avg": [], "max": []} for k in comp}
    for i in range(nsets):
        _, T = res.nodal_temperature(i)
        T = np.asarray(T, float)
        for k, pid in comp.items():
            v = T[pid]
            hist[k]["avg"].append(float(np.nanmean(v)))
            hist[k]["max"].append(float(np.nanmax(v)))
    INK, INK2, GRIDC = "#333333", "#666666", "#e5e5e0"
    COLS = {"Coil": "#2a78d6", "Magnet": "#e34948",
            "RotorCore": "#1baf7a", "StatorCore": "#eda100"}
    fig, ax = plt.subplots(figsize=(9.5, 6))
    for k, c in COLS.items():
        ax.plot(times, hist[k]["max"], color=c, lw=2, label=f"{k} max")
        ax.plot(times, hist[k]["avg"], color=c, lw=1.3, ls="--", alpha=0.75)
        ax.annotate(f"{k} max {hist[k]['max'][-1]:.1f}",
                    xy=(times[-1], hist[k]["max"][-1]),
                    xytext=(times[-1] * 1.01, hist[k]["max"][-1]),
                    va="center", fontsize=9, color=INK)
    ax.set_xlabel("Time, s", color=INK)
    ax.set_ylabel("Temperature, degC", color=INK)
    ax.set_title("Component temperatures (solid=max, dashed=avg) - "
                 "Maxwell 3D loss", color=INK, fontsize=12)
    ax.grid(True, color=GRIDC, lw=0.8)
    ax.tick_params(colors=INK2)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    for s_ in ("left", "bottom"):
        ax.spines[s_].set_color(GRIDC)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, ncol=2)
    ax.set_xlim(0, times[-1] * 1.28)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "real_component_history.png"), dpi=150)
    plt.close(fig)
    P("component history saved")
    for k in comp:
        P(f"  {k}: avg {hist[k]['avg'][-1]:.1f} / max {hist[k]['max'][-1]:.1f}")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
