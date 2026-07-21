# -*- coding: utf-8 -*-
"""FreeFlow 오일 SPH 유동 transient GIF (속도 컬러) + 형상 컨텍스트. 영문 타이틀."""
import os, glob, traceback
import numpy as np, h5py
GEO=r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry"
SIM=r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project.freeflow.files\simulation"
OUT=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_oil"
os.makedirs(OUT, exist_ok=True)
log=open(os.path.join(OUT,"gif_log.txt"),"w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
try:
    import pyvista as pv, imageio.v2 as imageio
    pv.OFF_SCREEN=True
    geo={n:pv.read(os.path.join(GEO,n+".stl")) for n in ("Housing","Stator","Winding","Rotating")}
    sphs=sorted([s for s in glob.glob(os.path.join(SIM,"*.sph")) if not s.endswith("rocky_simulation.sph")])
    idxs=list(range(0,len(sphs),20))  # ~40 frames
    P(f"n timesteps={len(sphs)} -> {len(idxs)} frames")
    sb=dict(title="|velocity| (m/s)",title_font_size=14,label_font_size=11,n_labels=5,fmt="%.1f",color="black")
    clim=[0.0,3.0]
    frames=[]
    for k,i in enumerate(idxs):
        with h5py.File(sphs[i],"r") as h:
            if "free/position" not in h: continue
            pos=h["free/position"][:]; vx=h["free/velocity_x"][:]; vy=h["free/velocity_y"][:]; vz=h["free/velocity_z"][:]
        xyz=np.column_stack([pos["x"],pos["y"],pos["z"]]).astype(np.float32)
        vmag=np.sqrt(vx**2+vy**2+vz**2)
        cloud=pv.PolyData(xyz); cloud["|v| (m/s)"]=vmag
        pl=pv.Plotter(off_screen=True,window_size=(1000,1050)); pl.set_background("white")
        pl.add_mesh(geo["Housing"],color="#c9c2ae",opacity=0.06,lighting=True)
        pl.add_mesh(geo["Stator"],color="#8a9bb0",opacity=0.15,lighting=True)
        pl.add_mesh(geo["Winding"],color="#c8791f",opacity=0.22,lighting=True)
        pl.add_mesh(geo["Rotating"],color="#1baf7a",opacity=0.28,lighting=True)
        pl.add_mesh(cloud,scalars="|v| (m/s)",cmap="turbo",clim=clim,point_size=3.0,
                    render_points_as_spheres=True,scalar_bar_args=sb)
        pl.add_text(f"FreeFlow oil flow (SPH)  frame {i:04d}  n={len(xyz)}",font_size=11,color="black")
        pl.view_vector((1,-0.5,0.25),viewup=(0,0,1)); pl.camera.zoom(1.25)
        frames.append(pl.screenshot(return_img=True)); pl.close()
        if k%10==0: P(f"  frame {k}/{len(idxs)} (ts {i})")
    imageio.mimsave(os.path.join(OUT,"ff_oil_transient.gif"),frames,fps=6,loop=0)
    P(f"saved ff_oil_transient.gif ({os.path.getsize(os.path.join(OUT,'ff_oil_transient.gif'))/1e6:.1f}MB, {len(frames)}f)")
    P("DONE-OK")
except Exception:
    P("EXC:",traceback.format_exc())
finally:
    log.close()
os._exit(0)
