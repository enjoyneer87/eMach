# -*- coding: utf-8 -*-
"""FreeFlow 1-way 커플드 오일 온도장 transient GIF (형상 오버레이).

ORIENT: "horizontal"(기본) = 모터 축(Z)을 가로로 눕히고 스프레이(오일 유입, z_min) 단이
        카메라 앞으로 오게 함. "vertical" = 원래 Z 수직.
출력: freeflow/viz/ (mapdl 폴더는 MAPDL 결과 전용이므로 분리)."""
import os, glob, tempfile, traceback
import numpy as np, h5py

GEO = r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry"
SIM = r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project_thermal.freeflow.files\simulation"
OUT = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\viz\freeflow"  # 툴별 서브폴더
ORIENT = os.environ.get("FF_ORIENT", "horizontal")   # "horizontal" | "vertical"
LOG = os.environ.get("FF_LOG", os.path.join(tempfile.gettempdir(), "ff_thermal_gif.txt"))
CLIM = [70.0, 72.2]
STRIDE = 3            # 서브샘플(164/3 ~ 55프레임)
DT_STEP = 0.01        # 스텝당 물리시간
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

# 모터 축(Z)을 X축(가로)으로 눕히는 회전. -90deg면 z_min(스프레이 유입단)이 카메라 앞으로.
_ROT_Y = -90.0 if ORIENT == "horizontal" else 0.0
def _orient(mesh):
    if _ROT_Y:
        mesh.rotate_y(_ROT_Y, point=(0.0, 0.0, 0.0), inplace=True)
    return mesh

try:
    import pyvista as pv
    import imageio.v2 as imageio
    pv.OFF_SCREEN = True
    geo = {n: _orient(pv.read(os.path.join(GEO, n + ".stl")))
           for n in ("Housing", "Stator", "Winding", "Rotating")}
    P(f"orientation={ORIENT} (rotate_y={_ROT_Y}deg, spray-front)")
    sphs = sorted(s for s in glob.glob(os.path.join(SIM, "*.sph"))
                  if not s.endswith("rocky_simulation.sph"))
    P(f"steps={len(sphs)} stride={STRIDE}")

    # 고정 카메라(첫 유효 프레임에서 산출)
    sb = dict(title="Oil Temperature (degC)", title_font_size=13, label_font_size=11,
              n_labels=6, fmt="%.1f", color="black")
    frames = []
    idxs = list(range(0, len(sphs), STRIDE))
    if (len(sphs) - 1) not in idxs:
        idxs.append(len(sphs) - 1)
    for k in idxs:
        f = sphs[k]
        try:
            with h5py.File(f, "r") as h:
                if "sph_scalars/temperature" not in h:
                    continue
                pos = h["free/position"][:]
                temp = h["sph_scalars/temperature"][:]
            n = min(len(pos), len(temp))
            if n == 0:
                continue
            pos = pos[:n]; temp = temp[:n]
            xyz = np.column_stack([pos["x"], pos["y"], pos["z"]]).astype(np.float32)
        except Exception as e:
            P(f"step {k} skip:", repr(e)[:80]); continue
        cloud = _orient(pv.PolyData(xyz)); cloud["Temperature"] = temp
        pl = pv.Plotter(off_screen=True, window_size=(1150, 950)); pl.set_background("white")
        pl.add_mesh(geo["Housing"], color="#c9c2ae", opacity=0.06, lighting=True)
        pl.add_mesh(geo["Stator"], color="#8a9bb0", opacity=0.14, lighting=True)
        pl.add_mesh(geo["Winding"], color="#c8791f", opacity=0.22, lighting=True)
        pl.add_mesh(geo["Rotating"], color="#1baf7a", opacity=0.28, lighting=True)
        pl.add_mesh(cloud, scalars="Temperature", cmap="inferno", clim=CLIM, point_size=4.0,
                    render_points_as_spheres=True, scalar_bar_args=sb)
        tmax = float(temp.max())
        pl.add_text(f"t={k*DT_STEP:.2f}s  oil max={tmax:.2f}C  (1-way coupled, MAPDL wall BC)",
                    font_size=11, color="black")
        pl.view_isometric(); pl.reset_camera(); pl.camera.zoom(1.3)
        frames.append(pl.screenshot(return_img=True)); pl.close()
    P(f"frames={len(frames)}")
    gif = os.path.join(OUT, "ff_thermal_oil_transient.gif")
    imageio.mimsave(gif, frames, fps=6, loop=0)
    P("saved", gif, f"{os.path.getsize(gif)/1e6:.1f}MB")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
