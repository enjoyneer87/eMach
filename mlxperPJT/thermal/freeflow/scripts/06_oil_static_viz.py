# -*- coding: utf-8 -*-
"""FreeFlow 오일 SPH 입자(속도 컬러) + 형상 컨텍스트 - 정적 렌더."""
import os, glob, traceback
import numpy as np, h5py
GEO=r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry"
SIM=r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project.freeflow.files\simulation"
OUT=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_oil"
os.makedirs(OUT, exist_ok=True)
log=open(os.path.join(OUT,"log.txt"),"w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
try:
    import pyvista as pv
    pv.OFF_SCREEN=True
    # 형상(컨텍스트)
    geo={}
    for n in ("Housing","Stator","Winding","Rotating"):
        geo[n]=pv.read(os.path.join(GEO,n+".stl"))
    sphs=sorted([s for s in glob.glob(os.path.join(SIM,"*.sph")) if not s.endswith("rocky_simulation.sph")])
    # 거의 채워진 후반 타임스텝
    f=sphs[750]
    with h5py.File(f,"r") as h:
        pos=h["free/position"][:]; vx=h["free/velocity_x"][:]; vy=h["free/velocity_y"][:]; vz=h["free/velocity_z"][:]
    xyz=np.column_stack([pos["x"],pos["y"],pos["z"]]).astype(np.float32)
    vmag=np.sqrt(vx**2+vy**2+vz**2)
    P(f"oil particles={len(xyz)} vmag min/mean/max={vmag.min():.2f}/{vmag.mean():.2f}/{vmag.max():.2f} m/s")
    cloud=pv.PolyData(xyz); cloud["|v| (m/s)"]=vmag
    clim=[0.0, float(np.percentile(vmag,97))]
    sb=dict(title="|velocity| (m/s)",title_font_size=14,label_font_size=12,n_labels=6,fmt="%.1f",color="black")
    for fn,view in [("ff_oil_iso.png","iso"),("ff_oil_front.png","xz")]:
        pl=pv.Plotter(off_screen=True,window_size=(1300,1050)); pl.set_background("white")
        pl.add_mesh(geo["Housing"],color="#c9c2ae",opacity=0.07,lighting=True)
        pl.add_mesh(geo["Stator"],color="#8a9bb0",opacity=0.18,lighting=True)
        pl.add_mesh(geo["Winding"],color="#c8791f",opacity=0.30,lighting=True)
        pl.add_mesh(geo["Rotating"],color="#1baf7a",opacity=0.35,lighting=True)
        pl.add_mesh(cloud,scalars="|v| (m/s)",cmap="turbo",clim=clim,point_size=3.5,
                    render_points_as_spheres=True,scalar_bar_args=sb)
        pl.add_text("FreeFlow 오일 유동 (SPH, 속도) - 형상 위 오버레이",font_size=11,color="black")
        pl.view_isometric() if view=="iso" else pl.view_xz()
        pl.camera.zoom(1.25); pl.screenshot(os.path.join(OUT,fn)); pl.close()
        P("saved",fn)
    P("DONE-OK")
except Exception:
    P("EXC:",traceback.format_exc())
finally:
    log.close()
os._exit(0)
