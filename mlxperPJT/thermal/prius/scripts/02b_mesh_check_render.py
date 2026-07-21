import os, traceback
import numpy as np
log=open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\prius_meshchk.txt","w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
OUT=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
mapdl=None
try:
    from ansys.mapdl.core import launch_mapdl
    import pyvista as pv
    pv.OFF_SCREEN=True
    SP=OUT
    mapdl=launch_mapdl(run_location=os.path.join(SP,f"pchk_{os.getpid()}"),override=True,loglevel="ERROR")
    mapdl.prep7()
    mapdl.cdread("DB", r"D:\KDH\simVary\Ansys_Thermal\prius_motor_mesh", "cdb")
    P("nodes:",mapdl.mesh.n_node,"elems:",mapdl.mesh.n_elem)
    names={1:"StatorLam",2:"Magnet",3:"Coil",4:"Shaft",5:"RotorLam"}
    for m in sorted(names):
        mapdl.esel("S","MAT","",m); P(f"  mat{m} {names[m]}: {mapdl.mesh.n_elem}")
    mapdl.allsel()
    # 재료별 렌더 (z=0 슬라이스 + iso)
    grid=mapdl.mesh.grid
    mats=np.asarray(grid.cell_data["ansys_material_type"]) if "ansys_material_type" in grid.cell_data else None
    mapdl.exit()
    COLS={1:"#2a78d6",2:"#e34948",3:"#eda100",4:"#e87ba4",5:"#1baf7a"}
    def render(mesh_getter, fname, view):
        p=pv.Plotter(off_screen=True,window_size=(1300,1200)); p.set_background("white")
        for m in sorted(names):
            part=mesh_getter(m)
            if part is None or part.n_cells==0: continue
            p.add_mesh(part,color=COLS[m],show_edges=True,edge_color="#555555",
                       line_width=0.3,lighting=(view!="xy"),label=names[m])
        p.add_legend(bcolor="white",size=(0.16,0.16),loc="lower right")
        p.add_text("Prius active-part mesh",font_size=12,color="black")
        if view=="xy": p.view_xy()
        else: p.view_isometric()
        p.screenshot(os.path.join(OUT,fname)); p.close()
    solid=grid
    def by_mat_slice(m):
        sl=solid.slice(normal="z",origin=(0,0,0))
        sm=np.asarray(sl.cell_data["ansys_material_type"])
        return sl.extract_cells(np.where(sm==m)[0])
    def by_mat_iso(m):
        return solid.extract_cells(np.where(mats==m)[0]).extract_surface()
    render(by_mat_slice,"prius_mesh_z0.png","xy")
    render(by_mat_iso,"prius_mesh_iso.png","iso")
    P("rendered"); P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    try:
        if mapdl is not None: mapdl.exit()
    except Exception: pass
    log.close(); os._exit(0)
