# -*- coding: utf-8 -*-
"""직교이방성 코일 z=0 단면 시간전개 GIF (슬롯 내부 hotspot 발달)."""
import os, traceback
import numpy as np
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT = os.path.join(SP, "viz_real_aniso")
log = open(os.path.join(SP, "coilz0_gif.txt"), "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
try:
    import pyvista as pv, imageio.v2 as imageio
    from ansys.mapdl import reader as rd
    pv.OFF_SCREEN = True
    res = rd.read_binary(os.path.join(SP, "real_17904", "file.rth"))
    g = res.grid.copy()
    solid = g.extract_cells(np.isin(g.celltypes, (10, 24)))
    mats = np.asarray(solid.cell_data["ansys_material_type"])
    coil = solid.extract_cells(np.where(mats == 3)[0])
    cpid = np.asarray(coil.point_data["vtkOriginalPointIds"])
    times = np.asarray(res.time_values, float)
    _, Te = res.nodal_temperature(res.nsets - 1)
    clim = [70.0, float(np.asarray(Te, float)[cpid].max())]
    P("clim:", clim)
    sb = dict(title="Coil T (degC)", title_font_size=14, label_font_size=12,
              n_labels=6, fmt="%.0f", color="black")
    frames = []
    for i in range(res.nsets):
        _, T = res.nodal_temperature(i)
        coil.point_data["Temperature (degC)"] = np.asarray(T, float)[cpid]
        sl = coil.slice(normal="z", origin=(0, 0, 0))
        pl = pv.Plotter(off_screen=True, window_size=(1000, 1000))
        pl.set_background("white")
        pl.add_mesh(sl, scalars="Temperature (degC)", cmap="inferno",
                    clim=clim, n_colors=16, lighting=False,
                    scalar_bar_args=sb)
        cmax = float(np.asarray(T, float)[cpid].max())
        pl.add_text(f"t = {times[i]:5.0f} s   coil max {cmax:5.1f} C  "
                    f"(orthotropic - transverse hotspot)",
                    font_size=12, color="black")
        pl.view_xy(); pl.camera.zoom(1.3)
        frames.append(pl.screenshot(return_img=True)); pl.close()
    gif = os.path.join(OUT, "real_transient_coil_z0.gif")
    imageio.mimsave(gif, frames, fps=4, loop=0)
    P("saved:", f"{os.path.getsize(gif)/1e6:.1f} MB")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
