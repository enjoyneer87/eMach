"""Manuscript figure builders for the JEET paper.

Consolidates the session scripts into reusable functions:

* ``extract_mes_fields``     — element-wise (x, y, |B|, A) from Motor-CAD
  ``.mes`` solutions via an existing COM instance, saved as ``.npz``
* ``plot_field_panels``      — journal 2xN |B| / MVP panel figure from the
  extracted ``.npz`` snapshots (no Motor-CAD required)
* ``plot_motor_geometry_dxf``— dimensioned cross-section figure from a DXF
  (bulge arcs are honored via ezdxf path flattening, mirroring the MATLAB
  ``DXFtool/readDXF.m`` bulge handling)

All plots use the shared journal style (Times New Roman, STIX math).
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


def _journal_rc():
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
        'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 7.5,
        'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
        'axes.linewidth': 0.6, 'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.03, 'mathtext.fontset': 'stix',
    })
    return plt


# ── Motor-CAD .mes field extraction ────────────────────────────────────

def extract_mes_fields(
    mc,
    jobs: Sequence[Tuple[str, str, str]],
    out_dir: str,
    first_step: int = 1,
    final_step: int = 1,
) -> List[str]:
    """Extract element-wise (x, y, |B|, A) snapshots from .mes solutions.

    mc    : live ansys.motorcad.core.MotorCAD instance
    jobs  : sequence of (tag, mot_path, mes_path). Use a *transient EMag*
            solution (e.g. OnLoadTorque_result_1.mes); OnLoadLoss .mes
            stores loss densities only and reads back zero B/A.
    Saves ``fields_<tag>.npz`` (keys x_mm, y_mm, b_T, a_Wbm) per job and
    returns the written paths.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'motorCAD'))
    from pyMCAD.fea_workflow import prepare_fea_export_session
    from pyMCAD.magnetic import get_magnetic_data

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for tag, mot, mes in jobs:
        mc.load_from_file(str(mot))
        prepare_fea_export_session(mc, mes_path=str(mes), out_dir=str(out))
        mag = get_magnetic_data(mc, first_step=first_step,
                                final_step=final_step,
                                filename=out / f'Magnetic_{tag}.txt',
                                clean_up=False)
        xs, ys, bs, as_ = [], [], [], []
        for region in mag._regions:
            for el in region.elements:
                c = mag._element_centroid_xy(el)
                if c is None:
                    continue
                xs.append(c[0])
                ys.append(c[1])
                bs.append(el.b)
                as_.append(el.a)
        p = out / f'fields_{tag}.npz'
        np.savez_compressed(p, x_mm=np.asarray(xs), y_mm=np.asarray(ys),
                            b_T=np.asarray(bs), a_Wbm=np.asarray(as_))
        written.append(str(p))
    return written


# ── |B| / MVP panel figure ─────────────────────────────────────────────

def plot_field_panels(
    cases: Sequence[Tuple[str, str]],
    out_path: str,
    share_a_pairs: bool = True,
    point_size: float = 0.35,
    raster_dpi: int = 600,
) -> str:
    """2xN journal figure from field .npz files.

    cases : sequence of (npz_path, panel_title), N columns.
    Row 1 = |B| on one shared scale; row 2 = MVP A (diverging). With
    ``share_a_pairs`` adjacent column pairs share the A scale (useful for
    Hybrid-vs-FullFEA pairs of the same model).
    Saving to .pdf keeps text vector and rasterizes the point clouds at
    ``raster_dpi``.
    """
    plt = _journal_rc()
    D = [(np.load(p), t) for p, t in cases]
    n = len(D)

    b_max = max(np.percentile(d['b_T'], 99.5) for d, _ in D)
    a_lim = [np.percentile(np.abs(d['a_Wbm']), 99.5) for d, _ in D]
    if share_a_pairs:
        for i in range(0, n - 1, 2):
            m = max(a_lim[i], a_lim[i + 1])
            a_lim[i] = a_lim[i + 1] = m

    fig, axes = plt.subplots(2, n, figsize=(1.9 * n, 4.4),
                             layout='constrained')
    if n == 1:
        axes = axes.reshape(2, 1)

    h_b = None
    for col, (d, title) in enumerate(D):
        ax = axes[0, col]
        h_b = ax.scatter(d['x_mm'], d['y_mm'], c=d['b_T'], s=point_size,
                         marker='.', cmap='jet', vmin=0, vmax=b_max,
                         rasterized=True, linewidths=0)
        ax.set_title(f'({chr(97 + col)}) {title}\n$|B|$', fontsize=7.5)

        ax2 = axes[1, col]
        h_a = ax2.scatter(d['x_mm'], d['y_mm'], c=d['a_Wbm'], s=point_size,
                          marker='.', cmap='RdBu_r',
                          vmin=-a_lim[col], vmax=a_lim[col],
                          rasterized=True, linewidths=0)
        ax2.set_title(f'({chr(97 + n + col)}) {title}\nMVP $A$',
                      fontsize=7.5)
        last_of_pair = (col % 2 == 1) if share_a_pairs else True
        if last_of_pair:
            lo = col - 1 if share_a_pairs else col
            cb = fig.colorbar(h_a, ax=list(axes[1, lo:col + 1]), shrink=0.8)
            cb.set_label('A [Wb/m]', fontsize=6.5)
            cb.ax.tick_params(labelsize=6)

        for a in (ax, ax2):
            a.set_aspect('equal')
            a.set_xticks([])
            a.set_yticks([])

    cb = fig.colorbar(h_b, ax=list(axes[0, :]), shrink=0.8)
    cb.set_label('|B| [T]', fontsize=6.5)
    cb.ax.tick_params(labelsize=6)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path, dpi=raster_dpi)
    plt.close(fig)
    return out_path


# ── AF map / 3-D surface (journal style) ───────────────────────────────

def plot_af_map_dq(dataset, model, out_path: str,
                   contour_levels: int = 8) -> str:
    """Journal-style AF map on the id-iq plane, one panel per speed.

    Measured AF samples (scatter) overlaid with the fitted Separable-RBF
    contours. `dataset`/`model` come from AcLossPipeline.load_dataset /
    build_model. Save to .pdf for a vector figure.
    """
    plt = _journal_rc()
    speeds = sorted(set(p.speed_rpm for p in dataset.points))
    n = len(speeds)
    vmin = max(0.4, float(dataset.af_arr.min()) - 0.05)
    vmax = float(dataset.af_arr.max()) + 0.05

    fig, axes = plt.subplots(1, n, figsize=(1.85 * n, 2.4),
                             layout='constrained')
    if n == 1:
        axes = [axes]
    sc = None
    for ax, spd in zip(axes, speeds):
        pts = [p for p in dataset.points if p.speed_rpm == spd]
        id_v = np.array([p.id_A for p in pts])
        iq_v = np.array([p.iq_A for p in pts])
        af_v = np.array([p.AF for p in pts])

        pad = 80.0
        id_g = np.linspace(id_v.min() - pad, id_v.max() + pad, 60)
        iq_g = np.linspace(max(0.0, iq_v.min() - pad),
                           iq_v.max() + pad, 60)
        ID, IQ = np.meshgrid(id_g, iq_g)
        irms_g = np.sqrt(ID**2 + IQ**2) / np.sqrt(2)
        phase_g = np.degrees(np.arctan2(IQ, ID)) - 90.0
        AF = model.predict(spd, irms_g.ravel(),
                           phase_g.ravel()).reshape(ID.shape)
        # blank the unsampled low-current core (RBF extrapolation)
        rmin = 0.85 * min(p.current_rms for p in pts)
        AF[irms_g < rmin] = np.nan

        ct = ax.contour(ID, IQ, AF, levels=contour_levels,
                        cmap='plasma', vmin=vmin, vmax=vmax,
                        linewidths=0.8)
        ax.clabel(ct, fmt='%.2f', fontsize=5.5)
        sc = ax.scatter(id_v, iq_v, c=af_v, cmap='plasma', s=14,
                        edgecolors='k', linewidths=0.3,
                        vmin=vmin, vmax=vmax, zorder=3)
        ax.set_title(f'{spd / 1000:.0f} kRPM', fontsize=8)
        ax.set_xlabel('$i_d$ [A, pk]')
        if ax is axes[0]:
            ax.set_ylabel('$i_q$ [A, pk]')
        ax.grid(True, ls=':', lw=0.4, color='#cccccc')
        ax.set_axisbelow(True)
    cb = fig.colorbar(sc, ax=list(axes), shrink=0.85)
    cb.set_label('AF [-]', fontsize=7)
    cb.ax.tick_params(labelsize=6.5)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_af_surface_3d(dataset, model, out_path: str) -> str:
    """Journal-style 3-D AF(id, iq) surfaces, one panel per speed."""
    plt = _journal_rc()
    speeds = sorted(set(p.speed_rpm for p in dataset.points))
    n = len(speeds)
    vmin = max(0.4, float(dataset.af_arr.min()) - 0.05)
    vmax = float(dataset.af_arr.max()) + 0.05

    fig = plt.figure(figsize=(1.95 * n, 2.6), layout='constrained')
    surf = None
    for k, spd in enumerate(speeds):
        ax = fig.add_subplot(1, n, k + 1, projection='3d')
        pts = [p for p in dataset.points if p.speed_rpm == spd]
        id_v = np.array([p.id_A for p in pts])
        iq_v = np.array([p.iq_A for p in pts])
        af_v = np.array([p.AF for p in pts])

        pad = 60.0
        id_g = np.linspace(id_v.min() - pad, id_v.max() + pad, 40)
        iq_g = np.linspace(max(0.0, iq_v.min() - pad),
                           iq_v.max() + pad, 40)
        ID, IQ = np.meshgrid(id_g, iq_g)
        irms_g = np.sqrt(ID**2 + IQ**2) / np.sqrt(2)
        phase_g = np.degrees(np.arctan2(IQ, ID)) - 90.0
        AF = model.predict(spd, irms_g.ravel(),
                           phase_g.ravel()).reshape(ID.shape)
        # blank the unsampled low-current core (RBF extrapolation)
        rmin = 0.85 * min(p.current_rms for p in pts)
        AF[irms_g < rmin] = np.nan

        surf = ax.plot_surface(ID, IQ, AF, cmap='plasma', vmin=vmin,
                               vmax=vmax, alpha=0.75, linewidth=0,
                               rstride=1, cstride=1)
        ax.scatter(id_v, iq_v, af_v, c='k', s=6, depthshade=False)
        ax.set_title(f'{spd / 1000:.0f} kRPM', fontsize=8, pad=0)
        ax.set_xlabel('$i_d$ [A]', fontsize=6, labelpad=-4)
        ax.set_ylabel('$i_q$ [A]', fontsize=6, labelpad=-4)
        ax.set_zlabel('AF', fontsize=6, labelpad=-4)
        ax.tick_params(labelsize=5, pad=-2)
        ax.view_init(28, -50)
    cb = fig.colorbar(surf, ax=fig.axes, shrink=0.7)
    cb.set_label('AF [-]', fontsize=7)
    cb.ax.tick_params(labelsize=6.5)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


# ── DXF cross-section with dimensions ──────────────────────────────────

def plot_motor_geometry_dxf(
    dxf_path: str,
    out_path: str,
    slot_angle_max_deg: float = 6.0,
    conductor_area_max: float = 10.0,
    magnet_area_range: Tuple[float, float] = (20.0, 120.0),
    copper_color: str = '#c87f42',
    magnet_color: str = '#9aa2ab',
) -> Dict[str, float]:
    """Dimensioned sector cross-section from a DXF file.

    Draws the lamination outlines (bulge arcs honored), fills conductors
    and magnets, adds engineering dimensions D_r/2 and D_s/2 below the
    bottom edge, and a top-left slot inset with conductor w/h and airgap g
    measured from the geometry. Returns the measured dimensions [mm].
    """
    import ezdxf
    from ezdxf import path as ezpath
    from matplotlib.patches import Polygon as MplPolygon

    plt = _journal_rc()

    doc = ezdxf.readfile(str(dxf_path))
    polys = []
    for e in doc.modelspace():
        n_raw = len(list(e.vertices))
        pts = np.array([(v.x, v.y)
                        for v in ezpath.make_path(e).flattening(0.02)])
        x, y = pts[:, 0], pts[:, 1]
        area = 0.5 * abs(np.dot(x, np.roll(y, 1))
                         - np.dot(y, np.roll(x, 1)))
        polys.append({'pts': pts, 'area': area, 'n_raw': n_raw,
                      'c': (x.mean(), y.mean()),
                      'r': float(np.hypot(x.mean(), y.mean()))})

    conductors = [p for p in polys if p['area'] < conductor_area_max]
    magnets = [p for p in polys
               if magnet_area_range[0] < p['area'] < magnet_area_range[1]
               and p['n_raw'] <= 10]
    used = {id(p) for p in conductors} | {id(p) for p in magnets}
    others = [p for p in polys if id(p) not in used]

    # measured dimensions
    r_out = max(np.hypot(p['pts'][:, 0], p['pts'][:, 1]).max()
                for p in polys)
    stator = max(others, key=lambda p: p['n_raw'])
    r_bore = np.hypot(stator['pts'][:, 0], stator['pts'][:, 1]).min()
    rotor_polys = [p for p in others
                   if np.hypot(p['pts'][:, 0],
                               p['pts'][:, 1]).max() < r_bore]
    r_rotor = max(np.hypot(p['pts'][:, 0], p['pts'][:, 1]).max()
                  for p in rotor_polys)
    g_air = r_bore - r_rotor

    ang = np.degrees(np.arctan2([p['c'][1] for p in conductors],
                                [p['c'][0] for p in conductors]))
    slot_conds = [c for c, a in zip(conductors, ang)
                  if a < slot_angle_max_deg]
    slot_ang = float(np.mean(
        [np.degrees(np.arctan2(p['c'][1], p['c'][0]))
         for p in slot_conds]))
    th = np.radians(-slot_ang)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    c0 = min(slot_conds, key=lambda p: p['r'])
    pr = c0['pts'] @ R.T
    w_c = pr[:, 0].max() - pr[:, 0].min()      # radial thickness
    h_c = pr[:, 1].max() - pr[:, 1].min()      # tangential width

    # figure
    fig, ax = plt.subplots(figsize=(5.4, 4.3))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

    def draw(axis, lw_steel=0.7):
        for p in others:
            axis.add_patch(MplPolygon(p['pts'], closed=True, fill=False,
                                      ec='black', lw=lw_steel))
        for p in magnets:
            axis.add_patch(MplPolygon(p['pts'], closed=True,
                                      fc=magnet_color, ec='black',
                                      lw=0.5, alpha=0.9))
        for p in conductors:
            axis.add_patch(MplPolygon(p['pts'], closed=True,
                                      fc=copper_color, ec='black',
                                      lw=0.4, alpha=0.95))

    draw(ax)
    ax.set_xlim(-6, 118)
    ax.set_ylim(-22, 88)
    ax.set_aspect('equal')
    ax.axis('off')

    def hdim(x_from, x_to, y_dim, label):
        for xv in (x_from, x_to):
            ax.plot([xv, xv], [-0.8, y_dim - 1.2], color='0.45', lw=0.5)
        ax.annotate('', xy=(x_to, y_dim), xytext=(x_from, y_dim),
                    arrowprops={'arrowstyle': '<->', 'lw': 0.7,
                                'color': 'black',
                                'shrinkA': 0, 'shrinkB': 0})
        ax.text((x_from + x_to) / 2, y_dim - 1.0, label,
                ha='center', va='top', fontsize=7.5)

    hdim(0.0, r_rotor, -7.0, rf'$D_r/2 = {r_rotor:.1f}$')
    hdim(0.0, r_out, -15.0, rf'$D_s/2 = {r_out:.0f}$')

    # slot inset
    axins = ax.inset_axes([0.00, 0.56, 0.46, 0.44])
    draw(axins, lw_steel=0.8)
    sx = [p['pts'][:, 0] for p in slot_conds]
    sy = [p['pts'][:, 1] for p in slot_conds]
    x_lo = min(a.min() for a in sx) - 7.0
    x_hi = max(a.max() for a in sx) + 1.2
    y_lo = min(a.min() for a in sy) - 2.8
    y_hi = max(a.max() for a in sy) + 3.8
    axins.set_xlim(x_lo, x_hi)
    axins.set_ylim(y_lo, y_hi)
    axins.set_aspect('equal')
    axins.set_xticks([])
    axins.set_yticks([])
    for spine in axins.spines.values():
        spine.set_linewidth(0.8)
    ax.indicate_inset_zoom(axins, edgecolor='black', lw=0.7)

    p_in = c0['pts']
    x0, x1v = p_in[:, 0].min(), p_in[:, 0].max()
    y0, y1v = p_in[:, 1].min(), p_in[:, 1].max()
    yy = y0 - 0.55
    axins.annotate('', xy=(x1v, yy), xytext=(x0, yy),
                   arrowprops={'arrowstyle': '<->', 'lw': 0.7,
                               'color': 'black'})
    axins.text((x0 + x1v) / 2, yy - 0.25, rf'$w={w_c:.1f}$',
               ha='center', va='top', fontsize=7)
    xx = x0 - 0.9
    axins.annotate('', xy=(xx, y1v), xytext=(xx, y0),
                   arrowprops={'arrowstyle': '<->', 'lw': 0.7,
                               'color': 'black'})
    axins.annotate(rf'$h={h_c:.1f}$', xy=(xx, (y0 + y1v) / 2),
                   xytext=(x0 - 3.4, y1v + 1.7), fontsize=7,
                   ha='center', va='bottom',
                   arrowprops={'arrowstyle': '-', 'lw': 0.5,
                               'color': '0.4'})
    a_sl = np.radians(slot_ang)
    gxm = 0.5 * (r_rotor + r_bore) * np.cos(a_sl)
    gym = 0.5 * (r_rotor + r_bore) * np.sin(a_sl)
    if x_lo < gxm < x_hi and y_lo < gym < y_hi:
        axins.annotate(rf'$g={g_air:.1f}$', xy=(gxm, gym),
                       xytext=(gxm - 4.0, gym - 2.8), fontsize=7,
                       ha='center', va='top',
                       arrowprops={'arrowstyle': '->', 'lw': 0.6,
                                   'color': 'black'})
    axins.text(0.97, 0.04, 'unit: mm', transform=axins.transAxes,
               ha='right', va='bottom', fontsize=6.5, style='italic')

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return {'Ds_mm': 2 * float(r_out), 'Dr_mm': 2 * float(r_rotor),
            'g_mm': float(g_air), 'w_mm': float(w_c), 'h_mm': float(h_c),
            'slot_angle_deg': slot_ang}
