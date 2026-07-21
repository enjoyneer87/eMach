# -*- coding: utf-8 -*-
"""워터재킷 internal GIF를 용도별 2종으로 분리 생성.
   1) wj_transient_coilmag.gif : 코일+자석만 온도컬러, 스테이터/로터는 회색 고스트(기존 스타일)
   2) wj_transient_core.gif    : z=0 단면 슬라이스 - 스테이터/로터/코일/자석/샤프트 전부 온도컬러
                                  (축방향 클립은 코일 막대가 카메라를 가려 코어가 안 보이는 문제 있었음
                                   -> 단면 슬라이스로 교체, 가림 없음)
   wj_transient_internal.gif는 core버전으로 최종 교체.
"""
import os, shutil, traceback
import numpy as np
OSP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
NSP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
REPO = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\viz"
log = open(os.path.join(NSP, "wj_twogifs.txt"), "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()
RUNS = [("real_37072", "waterjacket_low", "LOW load (Fluent-match)"),
        ("real_18456", "waterjacket_high", "HIGH load (250A)")]
try:
    import pyvista as pv, imageio.v2 as imageio
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN = True
    sb = dict(title="Temperature (degC)", title_font_size=15, label_font_size=12,
              n_labels=7, fmt="%.1f", color="black")
    for rdir, odir, label in RUNS:
        res = rd.read_binary(os.path.join(OSP, rdir, "file.rth"))
        g = res.grid.copy(); solid = g.extract_cells(np.isin(g.celltypes, (10, 24)))
        mats = np.asarray(solid.cell_data["ansys_material_type"])
        opid = np.asarray(solid.point_data["vtkOriginalPointIds"])
        times = np.asarray(res.time_values, float)
        _, Tend = res.nodal_temperature(res.nsets - 1); Tend = np.asarray(Tend, float)
        cl = [27.0, float(np.nanmax(Tend[opid]))]

        coil = solid.extract_cells(np.where(mats == 3)[0]); cpid = np.asarray(coil.point_data["vtkOriginalPointIds"])
        mag  = solid.extract_cells(np.where(mats == 2)[0]); mpid = np.asarray(mag.point_data["vtkOriginalPointIds"])
        ghost = solid.extract_cells(np.where((mats == 1) | (mats == 5))[0]).extract_surface()

        # ---------- GIF 1: 코일+자석만 (스테이터/로터 고스트) ----------
        frames = []
        for i in range(res.nsets):
            _, T = res.nodal_temperature(i); T = np.asarray(T, float)
            coil.point_data["Temperature (degC)"] = T[cpid]
            mag.point_data["Temperature (degC)"] = T[mpid]
            pl = pv.Plotter(off_screen=True, window_size=(1000, 780)); pl.set_background("white")
            pl.add_mesh(ghost, color="#d9d6c8", opacity=0.08, lighting=True, ambient=0.5)
            pl.add_mesh(coil, scalars="Temperature (degC)", cmap="inferno", clim=cl, n_colors=14,
                        lighting=True, ambient=0.6, diffuse=0.4, scalar_bar_args=sb)
            pl.add_mesh(mag, scalars="Temperature (degC)", cmap="inferno", clim=cl, n_colors=14,
                        lighting=True, ambient=0.6, diffuse=0.4, show_scalar_bar=False)
            pl.add_text(f"t={times[i]:5.0f}s coil {float(T[cpid].max()):5.1f} | mag {float(T[mpid].max()):5.1f}C  WJ {label}",
                        font_size=10, color="black")
            pl.view_vector((1, -0.4, 0.55), viewup=(0, 1, 0)); pl.camera.zoom(1.2)
            frames.append(pl.screenshot(return_img=True)); pl.close()
        out1 = os.path.join(NSP, f"wj_coilmag_{odir}.gif")
        imageio.mimsave(out1, frames, fps=4, loop=0)
        dst1 = os.path.join(REPO, odir, "wj_transient_coilmag.gif")
        shutil.copy(out1, dst1)
        P(f"{label}: coilmag -> {dst1} ({os.path.getsize(out1)/1e6:.2f}MB, {len(frames)}f)")

        # ---------- GIF 2: z=0 단면슬라이스, 전부품(스테이터/로터/코일/자석/샤프트) 온도컬러 ----------
        pid_role = {"Stator": np.where(mats == 1)[0], "Rotor": np.where(mats == 5)[0],
                    "Coil": np.where(mats == 3)[0], "Magnet": np.where(mats == 2)[0]}
        npid_role = {}
        for k, cidx in pid_role.items():
            sub = solid.extract_cells(cidx)
            npid_role[k] = np.asarray(sub.point_data["vtkOriginalPointIds"])
        frames = []
        for i in range(res.nsets):
            _, T = res.nodal_temperature(i); T = np.asarray(T, float)
            solid.point_data["Temperature (degC)"] = T[opid]
            sl = solid.slice(normal="z", origin=(0, 0, 0))
            pl = pv.Plotter(off_screen=True, window_size=(1000, 1000)); pl.set_background("white")
            pl.add_mesh(sl, scalars="Temperature (degC)", cmap="inferno", clim=cl, n_colors=16,
                        lighting=False, scalar_bar_args=sb)
            txt = f"t={times[i]:5.0f}s  " + "  ".join(
                f"{k[:4]} {float(np.nanmax(T[npid_role[k]])):.0f}" for k in ("Stator", "Coil", "Rotor", "Magnet"))
            pl.add_text(txt + f"C  WJ {label}", font_size=10, color="black")
            pl.view_xy(); pl.camera.zoom(1.3)
            frames.append(pl.screenshot(return_img=True)); pl.close()
        out2 = os.path.join(NSP, f"wj_core_{odir}.gif")
        imageio.mimsave(out2, frames, fps=4, loop=0)
        dst2 = os.path.join(REPO, odir, "wj_transient_core.gif")
        shutil.copy(out2, dst2)
        dst3 = os.path.join(REPO, odir, "wj_transient_internal.gif")
        shutil.copy(out2, dst3)
        P(f"{label}: core -> {dst2} & {dst3} ({os.path.getsize(out2)/1e6:.2f}MB, {len(frames)}f)")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
