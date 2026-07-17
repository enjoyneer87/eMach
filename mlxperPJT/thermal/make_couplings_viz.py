# -*- coding: utf-8 -*-
"""SURF152 결합 시각화: FEM 표면 패치(노드별 색) <-> 회로 노드."""
import os
import glob
import traceback
import numpy as np

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT = os.path.join(SP, "viz_real")
log = open(os.path.join(SP, "viz_coup.txt"), "w", encoding="utf-8")
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
    tets = np.isin(grid.celltypes, (10, 24))
    solid = grid.extract_cells(tets)
    mats = np.asarray(solid.cell_data["ansys_material_type"])
    surf = solid.extract_surface(pass_cellid=True)
    oc = np.asarray(surf.cell_data["vtkOriginalCellIds"])
    smat = mats[oc]
    cc = surf.cell_centers().points
    r = np.hypot(cc[:, 0], cc[:, 1])
    th = np.degrees(np.arctan2(cc[:, 1], cc[:, 0]))
    z = cc[:, 2]

    R_SO, R_SI, R_RO = 0.099, 0.066, 0.065
    STACK, ROT_ST = 0.160, 0.150
    atf_q = (th > -135) & (th < -45)
    wj_q = (th > 45) & (th < 135)

    # 분류 (러너의 SURF152 선택 로직과 동일 기준)
    cat = np.full(len(cc), -1, dtype=int)
    names = {}
    def C(idx, mask, name):
        cat[mask & (cat == -1)] = idx
        names[idx] = name
    C(0, (smat == 1) & (r > R_SO - 8e-4) & wj_q, "stator OD -> H_WJ (h=3000)")
    C(1, (smat == 1) & (r > R_SO - 8e-4) & atf_q, "stator OD -> ATF (h=300)")
    C(2, (smat == 1) & (r > R_SO - 8e-4), "stator OD -> H_RST (h=3000)")
    C(3, (smat == 1) & (np.abs(r - R_SI) < 8e-4), "stator bore -> GAP_S")
    C(4, (smat == 5) & (r > R_RO - 8e-4) & (np.abs(z) < ROT_ST / 2 - 1e-3),
      "rotor OD -> GAP_R")
    C(5, (smat == 4) & (np.abs(z) > ROT_ST / 2 + 1e-4), "shaft ext -> SHF")
    C(6, (smat == 5) & (np.abs(np.abs(z) - ROT_ST / 2) < 5e-4),
      "rotor end -> AIR (h=10)")
    C(7, (smat == 1) & (np.abs(np.abs(z) - STACK / 2) < 5e-4),
      "stator end -> AIR (h=10)")
    C(8, (smat == 3) & (np.abs(np.abs(z) - STACK / 2) < 5e-4) & atf_q,
      "coil cut -> CEND_ATF")
    C(9, (smat == 3) & (np.abs(np.abs(z) - STACK / 2) < 5e-4),
      "coil cut -> CEND_AIR")
    C(10, (smat == 3), "coil<->core slot junction (2xTCC)")
    C(11, (smat == 1) & (r > R_SI) & (r < R_SO - 1e-3),
      "slot wall<->junction (2xTCC)")
    P("category cells:", {names.get(k, k): int((cat == k).sum())
                          for k in sorted(set(cat.tolist()))})
    surf.cell_data["coupling"] = cat

    # 카테고리 색 (검증된 팔레트 8 + 보조)
    PAL = {0: "#2a78d6", 2: "#1baf7a", 1: "#eda100", 3: "#4a3aa7",
           4: "#e34948", 5: "#e87ba4", 6: "#008300", 7: "#7bbf6a",
           8: "#eb6834", 9: "#b45309", 10: "#8a8878", 11: "#c3c2b7",
           -1: "#eeede6"}
    node_of = {0: "H_WJ", 1: "ATF", 2: "H_RST", 3: "GAP_S", 4: "GAP_R",
               5: "SHF", 6: "AIR", 7: "AIR", 8: "CEND_ATF", 9: "CEND_AIR"}
    P3 = {"WJ": (0, R_SO + 0.055, 0), "H_WJ": (0, R_SO + 0.025, 0),
          "ATF": (0, -(R_SO + 0.055), 0), "H_ATF": (0, -(R_SO + 0.025), 0),
          "H_RST": (R_SO + 0.025, 0, 0), "AMB": (R_SO + 0.095, 0, 0.02),
          "AIR": (R_SO * 0.55, 0, STACK / 2 + 0.045),
          "SHF": (0, 0, -(STACK / 2 + 0.06)),
          "GAP_S": (R_SI + 0.006, 0, STACK * 0.30),
          "GAP_R": (R_RO - 0.006, 0, -STACK * 0.30),
          "CEND_ATF": (0, -0.075, STACK / 2 + 0.035),
          "CEND_AIR": (0, 0.075, STACK / 2 + 0.035)}

    p = pv.Plotter(off_screen=True, window_size=(1500, 1100))
    p.set_background("white")
    # 패치별로 add (categorical 고정색)
    for k in sorted(names):
        m = cat == k
        if not m.any():
            continue
        part = surf.extract_cells(np.where(m)[0])
        p.add_mesh(part, color=PAL[k], opacity=1.0 if k < 10 else 0.35,
                   lighting=True, smooth_shading=False,
                   ambient=0.55, diffuse=0.45,
                   label=names[k])
    # 미결합 면 (반투명 배경)
    rest = surf.extract_cells(np.where(cat == -1)[0])
    if rest.n_cells:
        p.add_mesh(rest, color="#eeede6", opacity=0.15, lighting=True,
                   ambient=0.5)
    # 회로 노드 구체 (해당 패치색) + 패치 중심 -> 노드 연결 튜브
    for k, nd in node_of.items():
        m = cat == k
        if not m.any() or nd not in P3:
            continue
        cen = cc[m].mean(axis=0)
        p.add_mesh(pv.Line(tuple(cen), P3[nd]).tube(radius=0.0015),
                   color=PAL[k], opacity=0.85)
    drawn = set()
    for k, nd in node_of.items():
        if nd in drawn or nd not in P3:
            continue
        drawn.add(nd)
        p.add_mesh(pv.Sphere(radius=0.010, center=P3[nd]), color=PAL[k],
                   smooth_shading=True, ambient=0.5)
    pts = np.array([P3[n] for n in drawn]) + np.array([0.012, 0.010, 0])
    p.add_point_labels(pts, list(drawn), font_size=15, text_color="black",
                       shape_color="white", shape_opacity=0.8,
                       always_visible=True, show_points=False)
    p.add_legend(bcolor="white", face=None, size=(0.32, 0.30),
                 loc="lower right")
    p.add_text("SURF152 couplings: FEM faces -> circuit nodes "
               "(patch color = target node)", font_size=12, color="black")
    p.view_vector((1, -0.4, 0.5), viewup=(0, 1, 0))
    p.camera.zoom(1.15)
    p.screenshot(os.path.join(OUT, "real_couplings_3d.png"))
    p.close()

    # 반단면 뷰(내부 결합이 보이게): x>0 절반 클립
    p = pv.Plotter(off_screen=True, window_size=(1500, 1100))
    p.set_background("white")
    clipped = surf.clip(normal=(1, 0, 0), origin=(0, 0, 0), invert=False)
    ccat = np.asarray(clipped.cell_data["coupling"])
    for k in sorted(names):
        m = ccat == k
        if not m.any():
            continue
        part = clipped.extract_cells(np.where(m)[0])
        p.add_mesh(part, color=PAL[k], lighting=True,
                   ambient=0.55, diffuse=0.45, label=names[k])
    rest = clipped.extract_cells(np.where(ccat == -1)[0])
    if rest.n_cells:
        p.add_mesh(rest, color="#eeede6", opacity=0.25, lighting=True)
    p.add_legend(bcolor="white", face=None, size=(0.32, 0.30),
                 loc="lower right")
    p.add_text("SURF152 couplings - half-section view", font_size=12,
               color="black")
    p.view_vector((-1, -0.35, 0.4), viewup=(0, 1, 0))
    p.camera.zoom(1.2)
    p.screenshot(os.path.join(OUT, "real_couplings_3d_cut.png"))
    p.close()
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
