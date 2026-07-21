# -*- coding: utf-8 -*-
"""Prius transient GIF: 코일 z=0 단면 + 내부부품(코일+자석) 시간전개."""
import os, glob, traceback
import numpy as np
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT=os.path.join(SP,"viz_prius")
log=open(os.path.join(SP,"prius_gif.txt"),"w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
try:
    import pyvista as pv, imageio.v2 as imageio
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN=True
    rth=sorted(glob.glob(os.path.join(SP,"real_*","file.rth")),key=os.path.getmtime)[-1]
    P("rth:",rth)
    res=rd.read_binary(rth)
    g=res.grid.copy(); solid=g.extract_cells(np.isin(g.celltypes,(10,24)))
    mats=np.asarray(solid.cell_data["ansys_material_type"]); opid=solid.point_data["vtkOriginalPointIds"]
    times=np.asarray(res.time_values,float)
    coil=solid.extract_cells(np.where(mats==3)[0]); cpid=np.asarray(coil.point_data["vtkOriginalPointIds"])
    mag=solid.extract_cells(np.where(mats==2)[0]); mpid=np.asarray(mag.point_data["vtkOriginalPointIds"])
    ghost=solid.extract_cells(np.where((mats==1)|(mats==5))[0]).extract_surface()
    _,Te=res.nodal_temperature(res.nsets-1); Te=np.asarray(Te,float)
    clim=[70.0,float(Te[opid].max())]
    P("clim:",clim)
    sb=dict(title="Temperature (degC)",title_font_size=14,label_font_size=12,n_labels=6,fmt="%.0f",color="black")
    # ① 코일 z=0 단면
    frames=[]
    for i in range(res.nsets):
        _,T=res.nodal_temperature(i); T=np.asarray(T,float)
        coil.point_data["Temperature (degC)"]=T[cpid]
        sl=coil.slice(normal="z",origin=(0,0,0))
        pl=pv.Plotter(off_screen=True,window_size=(1000,1000)); pl.set_background("white")
        pl.add_mesh(sl,scalars="Temperature (degC)",cmap="inferno",clim=clim,n_colors=16,lighting=False,scalar_bar_args=sb)
        pl.add_text(f"t={times[i]:5.0f}s  Prius coil max {float(T[cpid].max()):5.1f}C  (orthotropic)",font_size=12,color="black")
        pl.view_xy(); pl.camera.zoom(1.3); frames.append(pl.screenshot(return_img=True)); pl.close()
    imageio.mimsave(os.path.join(OUT,"prius_transient_coil_z0.gif"),frames,fps=4,loop=0)
    P("saved coil_z0 gif")
    # ② 내부부품(코일+자석)
    frames=[]
    for i in range(res.nsets):
        _,T=res.nodal_temperature(i); T=np.asarray(T,float)
        coil.point_data["Temperature (degC)"]=T[cpid]; mag.point_data["Temperature (degC)"]=T[mpid]
        pl=pv.Plotter(off_screen=True,window_size=(1000,780)); pl.set_background("white")
        pl.add_mesh(ghost,color="#d9d6c8",opacity=0.08,lighting=True,ambient=0.5)
        pl.add_mesh(coil,scalars="Temperature (degC)",cmap="inferno",clim=clim,n_colors=14,lighting=True,ambient=0.6,diffuse=0.4,scalar_bar_args=sb)
        pl.add_mesh(mag,scalars="Temperature (degC)",cmap="inferno",clim=clim,n_colors=14,lighting=True,ambient=0.6,diffuse=0.4,show_scalar_bar=False)
        cm_,mm_=float(T[cpid].max()),float(T[mpid].max())
        pl.add_text(f"t={times[i]:5.0f}s  coil {cm_:5.1f}C | magnet {mm_:5.1f}C  (Prius)",font_size=12,color="black")
        pl.view_vector((1,-0.4,0.55),viewup=(0,1,0)); pl.camera.zoom(1.2); frames.append(pl.screenshot(return_img=True)); pl.close()
    imageio.mimsave(os.path.join(OUT,"prius_transient_internal.gif"),frames,fps=4,loop=0)
    P("saved internal gif")
    P("DONE-OK")
except Exception:
    P("EXC:",traceback.format_exc())
finally:
    log.close(); os._exit(0)
