# -*- coding: utf-8 -*-
"""메시 상태 플롯: 재료별 색 + 요소 에지 (개요 반단면 / z=0 단면 / 슬롯 확대)."""
import os
import glob
import traceback
import numpy as np

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT = os.path.join(SP, "viz_real")
log = open(os.path.join(SP, "mesh_viz.txt"), "w", encoding="utf-8")
def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

try:
    import pyvista as pv
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN = True

    rth = sorted(glob.glob(os.path.join(SP, "real_*", "file.rth")),
                 key=os.path.getmtime)[-1]
    res = rd.read_binary(rth)
    grid = res.grid.copy()
    solid = grid.extract_cells(np.isin(grid.celltypes, (10, 24)))
    mats = np.asarray(solid.cell_data["ansys_material_type"])
    MATN = {1: "Stator lam", 2: "Magnet", 3: "Coil(slot)", 4: "Shaft",
            5: "Rotor lam"}
    COLS = {1: "#2a78d6", 2: "#e34948", 3: "#eda100", 4: "#e87ba4",
            5: "#1baf7a"}
    for m in sorted(MATN):
        n = int((mats == m).sum())
        P(f"mat{m} {MATN[m]}: {n} tets")
    P("total:", solid.n_cells, "tets /", solid.n_points, "nodes")

    def parts_of(mesh, marr):
        return {m: mesh.extract_cells(np.where(marr == m)[0])
                for m in sorted(MATN) if (marr == m).any()}

    # ── ① 개요: 반단면(x<0 유지) 재료별 색 + 에지 ───────────────────────
    p = pv.Plotter(off_screen=True, window_size=(1500, 1100))
    p.set_background("white")
    for m, part in parts_of(solid, mats).items():
        surf = part.extract_surface()
        half = surf.clip(normal=(1, 0, 0), origin=(0, 0, 0), invert=True)
        if half.n_cells == 0:
            continue
        p.add_mesh(half, color=COLS[m], show_edges=True,
                   edge_color="#3a3a35", line_width=0.4,
                   lighting=True, ambient=0.55, diffuse=0.45,
                   label=f"{MATN[m]}")
    p.add_legend(bcolor="white", face=None, size=(0.20, 0.16),
                 loc="lower right")
    p.add_text(f"MESH by material - half section  "
               f"({solid.n_cells:,} SOLID87 tets / {solid.n_points:,} nodes)",
               font_size=12, color="black")
    p.view_vector((1, -0.45, 0.35), viewup=(0, 1, 0))
    p.camera.zoom(1.1)
    p.screenshot(os.path.join(OUT, "real_mesh_overview.png"))
    p.close()
    P("saved overview")

    # ── ② z=0 단면: 재료별 색 + 에지 ─────────────────────────────────────
    sl = solid.slice(normal="z", origin=(0, 0, 0))
    smat = np.asarray(sl.cell_data["ansys_material_type"])
    p = pv.Plotter(off_screen=True, window_size=(1400, 1200))
    p.set_background("white")
    for m, part in parts_of(sl, smat).items():
        p.add_mesh(part, color=COLS[m], show_edges=True,
                   edge_color="#3a3a35", line_width=0.5, lighting=False,
                   label=MATN[m])
    p.add_legend(bcolor="white", face=None, size=(0.18, 0.15),
                 loc="lower right")
    p.add_text("MESH z=0 cross-section (element edges)", font_size=12,
               color="black")
    p.view_xy()
    p.camera.zoom(1.25)
    p.screenshot(os.path.join(OUT, "real_mesh_slice_z0.png"))
    p.close()
    P("saved slice z0")

    # ── ③ 슬롯 확대 (상부 슬롯 부근): 코일-슬롯벽 간극 가시화 ────────────
    p = pv.Plotter(off_screen=True, window_size=(1400, 1200))
    p.set_background("white")
    for m, part in parts_of(sl, smat).items():
        p.add_mesh(part, color=COLS[m], show_edges=True,
                   edge_color="#3a3a35", line_width=0.7, lighting=False,
                   label=MATN[m])
    p.add_legend(bcolor="white", face=None, size=(0.18, 0.15),
                 loc="lower right")
    p.add_text("MESH slot zoom @ z=0 (coil-slot liner gap visible)",
               font_size=12, color="black")
    p.view_xy()
    p.camera.focal_point = (0.0, 0.0755, 0.0)      # 상부 슬롯 밴드
    p.camera.position = (0.0, 0.0755, 0.16)
    p.camera.zoom(1.0)
    p.screenshot(os.path.join(OUT, "real_mesh_slot_zoom.png"))
    p.close()
    P("saved slot zoom")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
