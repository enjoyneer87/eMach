# -*- coding: utf-8 -*-
"""FreeFlow 커플드(1-way solid->fluid) 검증솔브 결과 - 오일 SPH 온도장 시각화.
기존 06_oil_static_viz.py 패턴 재사용(형상 오버레이 + SPH 입자 컬러).

ORIENT: 표시 방향. "horizontal"(기본) = 모터 축(Z)을 가로로 눕혀 실제 취부처럼 표시하고
        스프레이(오일 유입, z_min) 단이 카메라 앞으로 오게 함. "vertical" = 원래 Z 수직.
출력: freeflow/viz/ (mapdl 폴더는 MAPDL 결과 전용이므로 여기서 분리)."""
import os, glob, tempfile, traceback
import numpy as np, h5py

GEO = r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry"
SIM = r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project_thermal.freeflow.files\simulation"
OUT = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\viz\freeflow"  # 툴별 서브폴더
ORIENT = os.environ.get("FF_ORIENT", "horizontal")   # "horizontal" | "vertical"
LOG = os.environ.get("FF_LOG", os.path.join(tempfile.gettempdir(), "ff_thermal_viz.txt"))
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

# 모터 축(Z)을 X축(가로)으로 눕히는 회전. -90deg면 z_min(스프레이 유입단)이 +X=카메라
# 앞쪽으로 온다. geo(pyvista)·cloud 모두 동일 적용.
_ROT_Y = -90.0 if ORIENT == "horizontal" else 0.0
def _orient(mesh):
    if _ROT_Y:
        mesh.rotate_y(_ROT_Y, point=(0.0, 0.0, 0.0), inplace=True)
    return mesh

try:
    import pyvista as pv
    pv.OFF_SCREEN = True
    geo = {}
    for n in ("Housing", "Stator", "Winding", "Rotating"):
        geo[n] = _orient(pv.read(os.path.join(GEO, n + ".stl")))
    P(f"orientation={ORIENT} (rotate_y={_ROT_Y}deg, spray-front)")

    sphs = sorted(s for s in glob.glob(os.path.join(SIM, "*.sph"))
                  if not s.endswith("rocky_simulation.sph"))
    P(f"available steps: {len(sphs)}")
    f_last = sphs[-1]
    P("last step file:", f_last)
    with h5py.File(f_last, "r") as h:
        pos = h["free/position"][:]
        temp = h["sph_scalars/temperature"][:]
        vx, vy, vz = h["free/velocity_x"][:], h["free/velocity_y"][:], h["free/velocity_z"][:]
    # position(free) 과 sph_scalars 길이가 다를 수 있음(released 입자 등) -> 최소길이로 정렬
    n = min(len(pos), len(temp), len(vx))
    pos = pos[:n]; temp = temp[:n]; vx, vy, vz = vx[:n], vy[:n], vz[:n]
    xyz = np.column_stack([pos["x"], pos["y"], pos["z"]]).astype(np.float32)
    vmag = np.sqrt(vx**2 + vy**2 + vz**2)
    P(f"n particles={len(xyz)} T min/mean/max={temp.min():.2f}/{temp.mean():.2f}/{temp.max():.2f} "
      f"|v| min/mean/max={vmag.min():.2f}/{vmag.mean():.2f}/{vmag.max():.2f}")

    cloud = _orient(pv.PolyData(xyz))
    cloud["Temperature"] = temp
    clim = [float(np.percentile(temp, 1)), float(np.percentile(temp, 99))]
    sb = dict(title="Oil SPH Temperature (deg)", title_font_size=14, label_font_size=12,
              n_labels=6, fmt="%.1f", color="black")
    for fn, view in [("ff_thermal_oil_iso.png", "iso"), ("ff_thermal_oil_front.png", "xz")]:
        pl = pv.Plotter(off_screen=True, window_size=(1300, 1050)); pl.set_background("white")
        pl.add_mesh(geo["Housing"], color="#c9c2ae", opacity=0.07, lighting=True)
        pl.add_mesh(geo["Stator"], color="#8a9bb0", opacity=0.18, lighting=True)
        pl.add_mesh(geo["Winding"], color="#c8791f", opacity=0.30, lighting=True)
        pl.add_mesh(geo["Rotating"], color="#1baf7a", opacity=0.35, lighting=True)
        pl.add_mesh(cloud, scalars="Temperature", cmap="inferno", clim=clim, point_size=3.5,
                    render_points_as_spheres=True, scalar_bar_args=sb)
        pl.add_text("FreeFlow oil temperature (1-way coupled, MAPDL wall BC)",
                    font_size=11, color="black")
        pl.view_isometric() if view == "iso" else pl.view_xz()
        pl.reset_camera(); pl.camera.zoom(1.25)
        pl.screenshot(os.path.join(OUT, fn)); pl.close()
        P("saved", fn)

    # 시간이력: 각 스텝의 평균/최대 온도 (초기 스텝엔 temperature 필드 없을 수 있음)
    hist = []
    for f in sphs:
        try:
            with h5py.File(f, "r") as h:
                if "sph_scalars/temperature" not in h:
                    hist.append((np.nan, np.nan)); continue
                t = h["sph_scalars/temperature"][:]
            hist.append((float(t.mean()), float(t.max())))
        except Exception:
            hist.append((np.nan, np.nan))
    means = [h[0] for h in hist]; maxs = [h[1] for h in hist]
    P("history mean(first->last):", means[0], "->", means[-1])
    P("history max (first->last):", maxs[0], "->", maxs[-1])

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 5))
    tsteps = np.arange(len(hist)) * 0.01
    ax.plot(tsteps, means, label="oil mean T", color="#3987e5")
    ax.plot(tsteps, maxs, label="oil max T", color="#eb6834")
    ax.set_xlabel("time, s"); ax.set_ylabel("Temperature, degC")
    ax.set_title("FreeFlow oil temperature (1-way coupled validation)")
    ax.legend(); ax.grid(True, color="#e5e5e0")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ff_thermal_oil_history.png"), dpi=150)
    P("saved ff_thermal_oil_history.png")

    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close()
os._exit(0)
