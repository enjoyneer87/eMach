# -*- coding: utf-8 -*-
"""등방성 vs 직교이방성 코일 비교: z=0 코일 단면 나란히 + 이방성 부품/이력."""
import os
import csv
import traceback
import numpy as np

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT = os.path.join(SP, "viz_real_aniso")
os.makedirs(OUT, exist_ok=True)
ISO_RTH = os.path.join(SP, "real_133476", "file.rth")     # 등방성 v5
ANI_RTH = os.path.join(SP, "real_17904", "file.rth")      # 직교이방성
log = open(os.path.join(SP, "aniso_cmp.txt"), "w", encoding="utf-8")
def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

try:
    import pyvista as pv
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN = True

    def coil_slice(rth):
        res = rd.read_binary(rth)
        g = res.grid.copy()
        solid = g.extract_cells(np.isin(g.celltypes, (10, 24)))
        mats = np.asarray(solid.cell_data["ansys_material_type"])
        opid = solid.point_data["vtkOriginalPointIds"]
        _, T = res.nodal_temperature(res.nsets - 1)
        solid.point_data["Temperature (degC)"] = np.asarray(T, float)[opid]
        coil = solid.extract_cells(np.where(mats == 3)[0])
        return coil, res

    coil_i, res_i = coil_slice(ISO_RTH)
    coil_a, res_a = coil_slice(ANI_RTH)
    ti = coil_i.point_data["Temperature (degC)"]
    ta = coil_a.point_data["Temperature (degC)"]
    P(f"iso  coil: {ti.min():.1f} ~ {ti.max():.1f} (span {ti.max()-ti.min():.1f})")
    P(f"ani  coil: {ta.min():.1f} ~ {ta.max():.1f} (span {ta.max()-ta.min():.1f})")
    # 공용 컬러범위 (두 케이스 포괄)
    clim = [min(ti.min(), ta.min()), max(ti.max(), ta.max())]
    sb = dict(title="Temperature (degC)", title_font_size=14,
              label_font_size=12, n_labels=6, fmt="%.0f", color="black")

    # ── z=0 코일 단면 나란히 (공용 스케일) ──────────────────────────────
    p = pv.Plotter(off_screen=True, shape=(1, 2), window_size=(1700, 900),
                   border=False)
    for col, (coil, lab, tt) in enumerate([
            (coil_i, "ISOTROPIC k=380 (baseline)", ti),
            (coil_a, "ORTHOTROPIC k_trans=2.5 / k_axial=250", ta)]):
        p.subplot(0, col)
        p.set_background("white")
        sl = coil.slice(normal="z", origin=(0, 0, 0))
        p.add_mesh(sl, scalars="Temperature (degC)", cmap="inferno",
                   clim=clim, n_colors=16, show_edges=False, lighting=False,
                   scalar_bar_args=sb if col == 1 else None,
                   show_scalar_bar=(col == 1))
        p.add_text(f"{lab}\nz=0 slot conductors  "
                   f"(max {tt.max():.1f} C, spread {tt.max()-tt.min():.1f} K)",
                   font_size=11, color="black")
        p.view_xy()
        p.camera.zoom(1.3)
    p.link_views()
    p.screenshot(os.path.join(OUT, "coil_iso_vs_aniso_z0.png"))
    p.close()
    P("saved coil_iso_vs_aniso_z0.png")

    # ── 단일 슬롯 확대: 이방성 횡방향 구배 (상부 슬롯) ─────────────────
    p = pv.Plotter(off_screen=True, window_size=(1200, 1200))
    p.set_background("white")
    sl = coil_a.slice(normal="z", origin=(0, 0, 0))
    p.add_mesh(sl, scalars="Temperature (degC)", cmap="inferno",
               clim=[float(ta.min()), float(ta.max())], n_colors=16,
               show_edges=True, edge_color="#555555", line_width=0.4,
               lighting=False, scalar_bar_args=sb)
    p.add_text("ORTHOTROPIC coil - transverse gradient now resolved "
               "within each slot", font_size=12, color="black")
    p.view_xy()
    p.camera.focal_point = (0.0, 0.075, 0.0)
    p.camera.position = (0.0, 0.075, 0.14)
    p.camera.zoom(1.0)
    p.screenshot(os.path.join(OUT, "coil_aniso_slot_zoom.png"))
    p.close()
    P("saved coil_aniso_slot_zoom.png")

    # ── 이방성 코일 3D (자체 스케일) ─────────────────────────────────────
    p = pv.Plotter(off_screen=True, window_size=(1400, 1000))
    p.set_background("white")
    p.add_mesh(coil_a, scalars="Temperature (degC)", cmap="inferno",
               clim=[float(ta.min()), float(ta.max())], n_colors=14,
               lighting=True, ambient=0.55, diffuse=0.45, scalar_bar_args=sb)
    p.add_text(f"ORTHOTROPIC coil @ t=900s  (max {ta.max():.1f} C)",
               font_size=12, color="black")
    p.view_vector((1, -0.4, 0.55), viewup=(0, 1, 0))
    p.camera.zoom(1.15)
    p.screenshot(os.path.join(OUT, "real_coil_only_aniso.png"))
    p.close()
    P("saved real_coil_only_aniso.png")

    # ── 이방성 부품별 avg/max 이력 ───────────────────────────────────────
    solid = res_a.grid.extract_cells(
        np.isin(res_a.grid.celltypes, (10, 24)))
    mats = np.asarray(solid.cell_data["ansys_material_type"])
    opid = solid.point_data["vtkOriginalPointIds"]
    times = np.asarray(res_a.time_values, float)
    comp = {"Coil": 3, "Magnet": 2, "RotorCore": 5, "StatorCore": 1}
    pid = {k: opid[np.unique(solid.extract_cells(
        np.where(mats == m)[0]).point_data["vtkOriginalPointIds"])]
        for k, m in comp.items()}
    hist = {k: {"avg": [], "max": []} for k in comp}
    for i in range(res_a.nsets):
        _, T = res_a.nodal_temperature(i)
        T = np.asarray(T, float)
        for k in comp:
            v = T[pid[k]]
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
    ax.axhline(180, color="#c0392b", lw=1, ls=":", alpha=0.7)
    ax.text(20, 181, "H-class insulation 180 C", fontsize=8,
            color="#c0392b")
    ax.set_xlabel("Time, s", color=INK)
    ax.set_ylabel("Temperature, degC", color=INK)
    ax.set_title("Component temps - ORTHOTROPIC coil (solid=max, dashed=avg)",
                 color=INK, fontsize=12)
    ax.grid(True, color=GRIDC, lw=0.8); ax.tick_params(colors=INK2)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    for s_ in ("left", "bottom"):
        ax.spines[s_].set_color(GRIDC)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, ncol=2)
    ax.set_xlim(0, times[-1] * 1.28)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "real_component_history_aniso.png"), dpi=150)
    plt.close(fig)
    P("saved history; coil max iso->ani: "
      f"{ti.max():.1f} -> {ta.max():.1f} (+{ta.max()-ti.max():.1f}K)")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
