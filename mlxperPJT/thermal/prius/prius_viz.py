# -*- coding: utf-8 -*-
"""Prius 부품별 시각화: 코일/자석 3D(자체스케일) + z=0 코일단면 + 부품 이력."""
import os, glob, traceback
import numpy as np
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT=os.path.join(SP,"viz_prius")
log=open(os.path.join(SP,"prius_viz.txt"),"w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
try:
    import pyvista as pv, matplotlib
    matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN=True
    rth=sorted(glob.glob(os.path.join(SP,"real_*","file.rth")),key=os.path.getmtime)[-1]
    P("rth:",rth)
    res=rd.read_binary(rth)
    g=res.grid.copy(); solid=g.extract_cells(np.isin(g.celltypes,(10,24)))
    mats=np.asarray(solid.cell_data["ansys_material_type"]); opid=solid.point_data["vtkOriginalPointIds"]
    times=np.asarray(res.time_values,float)
    _,Te=res.nodal_temperature(res.nsets-1); Te=np.asarray(Te,float)
    def part(m):
        pm=solid.extract_cells(np.where(mats==m)[0]); return pm, np.asarray(pm.point_data["vtkOriginalPointIds"])
    coil,cpid=part(3); mag,mpid=part(2); rotor,rpid=part(5)
    sb=dict(title="Temperature (degC)",title_font_size=15,label_font_size=12,n_labels=7,fmt="%.1f",color="black")
    def render3d(mesh,pid,fname,title,ghost=None):
        tv=Te[pid]; mesh.point_data["Temperature (degC)"]=tv
        p=pv.Plotter(off_screen=True,window_size=(1400,1000)); p.set_background("white")
        if ghost is not None: p.add_mesh(ghost.extract_surface(),color="#d9d6c8",opacity=0.1,lighting=True,ambient=0.5)
        p.add_mesh(mesh,scalars="Temperature (degC)",cmap="inferno",clim=[float(tv.min()),float(tv.max())],
                   n_colors=14,lighting=True,ambient=0.55,diffuse=0.45,scalar_bar_args=sb)
        p.add_text(f"{title} (max {tv.max():.1f} C)",font_size=12,color="black")
        p.view_vector((1,-0.4,0.55),viewup=(0,1,0)); p.camera.zoom(1.15)
        p.screenshot(os.path.join(OUT,fname)); p.close(); P("saved",fname)
    render3d(coil,cpid,"prius_coil_only.png","Prius COIL (orthotropic)")
    render3d(mag,mpid,"prius_magnet_only.png","Prius MAGNET (V-IPM 16seg)",ghost=rotor)
    # z=0 코일단면
    coil.point_data["Temperature (degC)"]=Te[cpid]
    sl=coil.slice(normal="z",origin=(0,0,0)); tv=Te[cpid]
    p=pv.Plotter(off_screen=True,window_size=(1200,1200)); p.set_background("white")
    p.add_mesh(sl,scalars="Temperature (degC)",cmap="inferno",clim=[float(tv.min()),float(tv.max())],
               n_colors=16,show_edges=True,edge_color="#555555",line_width=0.3,lighting=False,scalar_bar_args=sb)
    p.add_text("Prius coil z=0 (transverse hotspot per slot)",font_size=12,color="black")
    p.view_xy(); p.camera.zoom(1.3); p.screenshot(os.path.join(OUT,"prius_coil_z0.png")); p.close()
    P("saved prius_coil_z0.png")
    # 부품 이력
    comp={"Coil":3,"Magnet":2,"RotorCore":5,"StatorCore":1}
    pid={k:opid[np.unique(solid.extract_cells(np.where(mats==m)[0]).point_data["vtkOriginalPointIds"])] for k,m in comp.items()}
    hist={k:{"avg":[],"max":[]} for k in comp}
    for i in range(res.nsets):
        _,T=res.nodal_temperature(i); T=np.asarray(T,float)
        for k in comp:
            v=T[pid[k]]; hist[k]["avg"].append(float(np.nanmean(v))); hist[k]["max"].append(float(np.nanmax(v)))
    INK,GRIDC="#333333","#e5e5e0"
    COLS={"Coil":"#2a78d6","Magnet":"#e34948","RotorCore":"#1baf7a","StatorCore":"#eda100"}
    fig,ax=plt.subplots(figsize=(9.5,6))
    for k,c in COLS.items():
        ax.plot(times,hist[k]["max"],color=c,lw=2,label=f"{k} max")
        ax.plot(times,hist[k]["avg"],color=c,lw=1.3,ls="--",alpha=0.75)
        ax.annotate(f"{k} max {hist[k]['max'][-1]:.1f}",xy=(times[-1],hist[k]["max"][-1]),
                    xytext=(times[-1]*1.01,hist[k]["max"][-1]),va="center",fontsize=9,color=INK)
    ax.axhline(180,color="#c0392b",lw=1,ls=":",alpha=0.7); ax.text(20,181,"H-class 180C",fontsize=8,color="#c0392b")
    ax.axhline(150,color="#8e44ad",lw=1,ls=":",alpha=0.6); ax.text(20,151,"NdFeB magnet ~150C",fontsize=8,color="#8e44ad")
    ax.set_xlabel("Time, s",color=INK); ax.set_ylabel("Temperature, degC",color=INK)
    ax.set_title("Prius component temps (Maxwell 2D loss, 250A/3000rpm)",color=INK,fontsize=12)
    ax.grid(True,color=GRIDC,lw=0.8)
    for s_ in ("top","right"): ax.spines[s_].set_visible(False)
    ax.legend(frameon=False,fontsize=9,labelcolor=INK,ncol=2); ax.set_xlim(0,times[-1]*1.28)
    fig.tight_layout(); fig.savefig(os.path.join(OUT,"prius_component_history.png"),dpi=150); plt.close(fig)
    P("saved history; coil/mag/stator/rotor max:",
      *[round(hist[k]["max"][-1],1) for k in comp])
    P("DONE-OK")
except Exception:
    P("EXC:",traceback.format_exc())
finally:
    log.close(); os._exit(0)
