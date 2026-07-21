# -*- coding: utf-8 -*-
"""워터재킷 저/고부하 시각화: 컨투어3뷰 + 코일/자석 + 이력 + GIF."""
import os, traceback
import numpy as np
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
log=open(os.path.join(SP,"wj_viz.txt"),"w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
RUNS=[("real_37072","viz_prius_wj_low","LOW load (Fluent-match)"),
      ("real_18456","viz_prius_wj_high","HIGH load (250A)")]
try:
    import pyvista as pv, imageio.v2 as imageio
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN=True
    for rdir,odir,label in RUNS:
        OUT=os.path.join(SP,odir); os.makedirs(OUT,exist_ok=True)
        res=rd.read_binary(os.path.join(SP,rdir,"file.rth"))
        g=res.grid.copy(); solid=g.extract_cells(np.isin(g.celltypes,(10,24)))
        mats=np.asarray(solid.cell_data["ansys_material_type"]); opid=solid.point_data["vtkOriginalPointIds"]
        times=np.asarray(res.time_values,float)
        _,Te=res.nodal_temperature(res.nsets-1); Te=np.asarray(Te,float)
        coil=solid.extract_cells(np.where(mats==3)[0]); cpid=np.asarray(coil.point_data["vtkOriginalPointIds"])
        mag=solid.extract_cells(np.where(mats==2)[0]); mpid=np.asarray(mag.point_data["vtkOriginalPointIds"])
        rotor=solid.extract_cells(np.where(mats==5)[0])
        sb=dict(title="Temperature (degC)",title_font_size=15,label_font_size=12,n_labels=7,fmt="%.1f",color="black")
        # 컨투어 3뷰 (전체 solid)
        solid.point_data["Temperature (degC)"]=Te[opid]
        clim=[float(Te[opid].min()),float(Te[opid].max())]
        for fn,mesh,view,lit in [("wj_contour_iso.png",solid.extract_surface(),"iso",True),
                                  ("wj_contour_z0.png",solid.slice(normal="z"),"xy",False),
                                  ("wj_contour_x0.png",solid.slice(normal="x"),"x0",False)]:
            tv=mesh.point_data["Temperature (degC)"]
            p=pv.Plotter(off_screen=True,window_size=(1200,1000)); p.set_background("white")
            kw=dict(scalars="Temperature (degC)",cmap="inferno",clim=[float(tv.min()),float(tv.max())],n_colors=14,scalar_bar_args=sb)
            if lit: kw.update(smooth_shading=True,ambient=0.6,diffuse=0.4)
            else: kw.update(lighting=False)
            p.add_mesh(mesh,**kw)
            p.add_text(f"Prius water-jacket {label} @900s",font_size=11,color="black")
            if view=="xy": p.view_xy()
            elif view=="x0": p.view_vector((1,0,0),viewup=(0,1,0))
            else: p.view_isometric()
            p.camera.zoom(1.15); p.screenshot(os.path.join(OUT,fn)); p.close()
        # 코일/자석
        for mesh,pid,fn,tt,gh in [(coil,cpid,"wj_coil_only.png","COIL",None),
                                   (mag,mpid,"wj_magnet_only.png","MAGNET",rotor)]:
            tv=Te[pid]; mesh.point_data["Temperature (degC)"]=tv
            p=pv.Plotter(off_screen=True,window_size=(1300,1000)); p.set_background("white")
            if gh is not None: p.add_mesh(gh.extract_surface(),color="#d9d6c8",opacity=0.1,lighting=True,ambient=0.5)
            p.add_mesh(mesh,scalars="Temperature (degC)",cmap="inferno",clim=[float(tv.min()),float(tv.max())],n_colors=14,lighting=True,ambient=0.55,diffuse=0.45,scalar_bar_args=sb)
            p.add_text(f"Prius {tt} water-jacket {label} (max {tv.max():.1f}C)",font_size=11,color="black")
            p.view_vector((1,-0.4,0.55),viewup=(0,1,0)); p.camera.zoom(1.15); p.screenshot(os.path.join(OUT,fn)); p.close()
        # 부품 이력
        comp={"Coil":3,"Magnet":2,"RotorCore":5,"StatorCore":1}
        pid={k:opid[np.unique(solid.extract_cells(np.where(mats==m)[0]).point_data["vtkOriginalPointIds"])] for k,m in comp.items()}
        hist={k:{"avg":[],"max":[]} for k in comp}
        for i in range(res.nsets):
            _,T=res.nodal_temperature(i); T=np.asarray(T,float)
            for k in comp: v=T[pid[k]]; hist[k]["avg"].append(float(np.nanmean(v))); hist[k]["max"].append(float(np.nanmax(v)))
        INK,GRIDC="#333333","#e5e5e0"; COLS={"Coil":"#2a78d6","Magnet":"#e34948","RotorCore":"#1baf7a","StatorCore":"#eda100"}
        fig,ax=plt.subplots(figsize=(9.5,6))
        for k,c in COLS.items():
            ax.plot(times,hist[k]["max"],color=c,lw=2,label=f"{k} max"); ax.plot(times,hist[k]["avg"],color=c,lw=1.3,ls="--",alpha=0.7)
            ax.annotate(f"{k} {hist[k]['max'][-1]:.1f}",xy=(times[-1],hist[k]["max"][-1]),xytext=(times[-1]*1.01,hist[k]["max"][-1]),va="center",fontsize=9,color=INK)
        ax.set_xlabel("Time, s",color=INK); ax.set_ylabel("Temperature, degC",color=INK)
        ax.set_title(f"Prius water-jacket {label} - component temps",color=INK,fontsize=12)
        ax.grid(True,color=GRIDC,lw=0.8)
        for s in ("top","right"): ax.spines[s].set_visible(False)
        ax.legend(frameon=False,fontsize=9,labelcolor=INK,ncol=2); ax.set_xlim(0,times[-1]*1.28)
        fig.tight_layout(); fig.savefig(os.path.join(OUT,"wj_component_history.png"),dpi=150); plt.close(fig)
        # GIF 2종
        cl=[27.0,float(Te[opid].max())]
        frames=[]
        for i in range(res.nsets):
            _,T=res.nodal_temperature(i); T=np.asarray(T,float); coil.point_data["Temperature (degC)"]=T[cpid]
            sl=coil.slice(normal="z",origin=(0,0,0))
            pl=pv.Plotter(off_screen=True,window_size=(950,950)); pl.set_background("white")
            pl.add_mesh(sl,scalars="Temperature (degC)",cmap="inferno",clim=cl,n_colors=16,lighting=False,scalar_bar_args=sb)
            pl.add_text(f"t={times[i]:5.0f}s coil {float(T[cpid].max()):5.1f}C  WJ {label}",font_size=11,color="black")
            pl.view_xy(); pl.camera.zoom(1.3); frames.append(pl.screenshot(return_img=True)); pl.close()
        imageio.mimsave(os.path.join(OUT,"wj_transient_coil_z0.gif"),frames,fps=4,loop=0)
        ghost=solid.extract_cells(np.where((mats==1)|(mats==5))[0]).extract_surface()
        frames=[]
        for i in range(res.nsets):
            _,T=res.nodal_temperature(i); T=np.asarray(T,float); coil.point_data["Temperature (degC)"]=T[cpid]; mag.point_data["Temperature (degC)"]=T[mpid]
            pl=pv.Plotter(off_screen=True,window_size=(1000,780)); pl.set_background("white")
            pl.add_mesh(ghost,color="#d9d6c8",opacity=0.08,lighting=True,ambient=0.5)
            pl.add_mesh(coil,scalars="Temperature (degC)",cmap="inferno",clim=cl,n_colors=14,lighting=True,ambient=0.6,diffuse=0.4,scalar_bar_args=sb)
            pl.add_mesh(mag,scalars="Temperature (degC)",cmap="inferno",clim=cl,n_colors=14,lighting=True,ambient=0.6,diffuse=0.4,show_scalar_bar=False)
            pl.add_text(f"t={times[i]:5.0f}s coil {float(T[cpid].max()):5.1f} | mag {float(T[mpid].max()):5.1f}C  WJ {label}",font_size=11,color="black")
            pl.view_vector((1,-0.4,0.55),viewup=(0,1,0)); pl.camera.zoom(1.2); frames.append(pl.screenshot(return_img=True)); pl.close()
        imageio.mimsave(os.path.join(OUT,"wj_transient_internal.gif"),frames,fps=4,loop=0)
        P(f"{label}: done. coil max {Te[cpid].max():.1f}")
    P("DONE-OK")
except Exception:
    P("EXC:",traceback.format_exc())
finally:
    log.close(); os._exit(0)
