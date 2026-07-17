# -*- coding: utf-8 -*-
"""v5 rth -> ① transient GIF ② 코일 이력 차트 ③ 실형상 3D 회로 오버레이."""
import os
import glob
import csv
import math
import traceback
import numpy as np

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT = os.path.join(SP, "viz_real")
log = open(os.path.join(SP, "real_tviz.txt"), "w", encoding="utf-8")
def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

try:
    import pyvista as pv
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN = True

    rth = sorted(glob.glob(os.path.join(SP, "real_*", "file.rth")),
                 key=os.path.getmtime)[-1]
    P("rth:", rth)
    res = rd.read_binary(rth)
    nsets = res.nsets
    times = res.time_values
    P("sets:", nsets, "t:", times[0], "..", times[-1])
    grid = res.grid.copy()
    solid = grid.extract_cells(np.isin(grid.celltypes, (10, 24)))
    # solid 는 point 매핑 유지: extract_cells 는 vtkOriginalPointIds 보존
    opid = solid.point_data["vtkOriginalPointIds"]

    # 전 시간 최대/최소 (고정 컬러스케일)
    _, T_last = res.nodal_temperature(nsets - 1)
    T_last = np.asarray(T_last, float)
    tmax = float(np.nanmax(T_last))
    clim = [70.0, tmax]
    P("clim:", clim)

    # ── ① transient GIF (x=0 슬라이스, y-위) ────────────────────────────
    gif = os.path.join(OUT, "real_transient_x0.gif")
    p = pv.Plotter(off_screen=True, window_size=(900, 680))
    p.open_gif(gif, fps=4)
    for i in range(nsets):
        _, T = res.nodal_temperature(i)
        T = np.asarray(T, float)
        solid.point_data["Temperature (degC)"] = T[opid]
        sl = solid.slice(normal="x")
        p.clear()
        p.set_background("white")
        p.add_mesh(sl, cmap="inferno", clim=clim, lighting=False,
                   scalar_bar_args=dict(title="Temperature (degC)",
                                        title_font_size=14,
                                        label_font_size=12, n_labels=6,
                                        fmt="%.0f", color="black"))
        p.add_text(f"t = {times[i]:5.0f} s   (top: WJ / bottom: ATF)",
                   font_size=13, color="black")
        p.view_vector((1, 0, 0), viewup=(0, 1, 0))
        p.write_frame()
    p.close()
    P("gif saved:", gif, f"({os.path.getsize(gif)/1e6:.1f} MB)")

    # ── ② 코일 이력 차트 ─────────────────────────────────────────────────
    hist = list(csv.DictReader(open(os.path.join(OUT, "real_coil_temp.csv"))))
    ts = [float(r["time_s"]) for r in hist]
    INK, INK2, GRIDC = "#333333", "#666666", "#e5e5e0"
    SERIES = {"Center_WJ": "#2a78d6", "Center_ATF": "#1baf7a",
              "Tip_WJ": "#eda100", "Tip_ATF": "#008300"}
    finals = sorted((float(hist[-1][k]), k) for k in SERIES)
    gap = max((finals[-1][0] - finals[0][0] + 4) / 3, 3.0)
    lab_y, yp = {}, None
    for v, k in finals:
        y = v if yp is None else max(v, yp + gap)
        lab_y[k] = y; yp = y
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for k, c in SERIES.items():
        ys = [float(r[k]) for r in hist]
        ax.plot(ts, ys, color=c, lw=2, label=k)
        ax.annotate(f"{k}  {ys[-1]:.1f}", xy=(ts[-1], ys[-1]),
                    xytext=(ts[-1] * 1.01, lab_y[k]), textcoords="data",
                    va="center", fontsize=9, color=INK)
    ax.set_xlabel("Time, s", color=INK)
    ax.set_ylabel("Temperature, degC", color=INK)
    ax.set_title("REAL geometry - coil temperature history (Maxwell 3D loss)",
                 color=INK, fontsize=12)
    ax.grid(True, color=GRIDC, lw=0.8); ax.tick_params(colors=INK2)
    for sp_ in ("top", "right"):
        ax.spines[sp_].set_visible(False)
    for sp_ in ("left", "bottom"):
        ax.spines[sp_].set_color(GRIDC)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    ax.set_xlim(0, max(ts) * 1.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "real_coil_history.png"), dpi=150)
    plt.close(fig)
    P("history chart saved")

    # ── ③ 실형상 3D 회로 오버레이 ────────────────────────────────────────
    node_T = {"WJ": 70.0, "ATF": 70.0, "AMB": 70.0, "AIR": 178.4,
              "SHF": 93.8, "H_WJ": 74.3, "H_ATF": 72.9, "H_RST": 150.8,
              "GAP_S": 157.5, "GAP_R": 155.4,
              "CEND_ATF": 92.5, "CEND_AIR": 219.9}
    R_SO, R_SI, R_RO = 0.099, 0.066, 0.065
    STACK = 0.160
    P3 = {
        "WJ":    (0,  R_SO + 0.055, 0),
        "H_WJ":  (0,  R_SO + 0.025, 0),
        "ATF":   (0, -(R_SO + 0.055), 0),
        "H_ATF": (0, -(R_SO + 0.025), 0),
        "H_RST": (R_SO + 0.025, 0, 0),
        "AMB":   (R_SO + 0.095, 0, 0.02),
        "AIR":   (R_SO * 0.55, 0, STACK / 2 + 0.045),
        "SHF":   (0, 0, -(STACK / 2 + 0.05)),
        "GAP_S": (R_SI + 0.006, 0, STACK * 0.30),
        "GAP_R": (R_RO - 0.006, 0, -STACK * 0.30),
        "CEND_ATF": (0, -0.075, STACK / 2 + 0.03),
        "CEND_AIR": (0, 0.075, STACK / 2 + 0.03),
    }
    E3 = [("GAP_S", "GAP_R"), ("H_WJ", "WJ"), ("H_ATF", "ATF"),
          ("H_WJ", "AMB"), ("H_ATF", "AMB"), ("H_RST", "AMB"),
          ("H_WJ", "H_RST"), ("H_ATF", "H_RST"), ("SHF", "AIR"),
          ("AIR", "H_RST"), ("CEND_ATF", "ATF"), ("CEND_AIR", "AIR")]
    norm = mcolors.Normalize(70.0, max(node_T.values()))
    cmap = cm.get_cmap("inferno")
    solid.point_data["Temperature (degC)"] = T_last[opid]
    surf = solid.extract_surface()
    p = pv.Plotter(off_screen=True, window_size=(1400, 1050))
    p.set_background("white")
    p.add_mesh(surf, color="#c9c2ae", opacity=0.18, lighting=True,
               smooth_shading=True, ambient=0.5)
    for a, b in E3:
        p.add_mesh(pv.Line(P3[a], P3[b]).tube(radius=0.0022),
                   color="#b9b8ad", opacity=0.9)
    for k, xyz in P3.items():
        p.add_mesh(pv.Sphere(radius=0.0105, center=xyz),
                   color=cmap(norm(node_T[k]))[:3], smooth_shading=True,
                   ambient=0.45, diffuse=0.6)
    pts = np.array([P3[k] for k in P3]) + np.array([0.013, 0.010, 0.0])
    labels = [f"{k} {node_T[k]:.1f}" for k in P3]
    p.add_point_labels(pts, labels, font_size=15, text_color="black",
                       shape_color="white", shape_opacity=0.78,
                       always_visible=True, show_points=False)
    p.add_text("REAL geometry - thermal circuit overlay @ t=900s "
               "(node color = temperature)", font_size=12, color="black")
    p.view_vector((1, -0.35, 0.45), viewup=(0, 1, 0))
    p.camera.zoom(1.2)
    p.screenshot(os.path.join(OUT, "real_thermal_circuit_3d.png"))
    p.close()
    P("3D overlay saved")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
