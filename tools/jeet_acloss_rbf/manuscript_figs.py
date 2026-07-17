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
        # square dq plane: same A-per-inch on both current axes
        ax.set_aspect('equal', adjustable='box')
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


def plot_form_convergence(pipeline, out_path: str,
                          scales=('Ref', 'HalfSC', 'SC'),
                          n_base_list=(8, 10, 12, 16, 20, 24, 28),
                          n_spd_by_scale=None,
                          n_seeds: int = 10) -> str:
    """Scalar vs exponent separable convergence: full-map wMAE vs n_base.

    Own-sampling protocol (16-kRPM base kernel + n_spd calibration points
    per non-base speed), multi-seed mean, log scale. The two curves share
    the identical sample placement, so their gap isolates the contribution
    of the spread exponent p(w). Degenerate low-count regressions are
    capped at 10^3 for display.
    """
    import contextlib
    import io

    from .AcLossEvaluator import AcLossEvaluator

    plt = _journal_rc()
    ns_by = n_spd_by_scale or {'Ref': 4, 'HalfSC': 3, 'SC': 4}
    kr_by = {'Ref': 1.0, 'HalfSC': 1.5, 'SC': 2.0}
    base_speed = pipeline.cfg['base_speed']

    fig, axes = plt.subplots(1, len(scales),
                             figsize=(2.35 * len(scales), 2.35),
                             layout='constrained', sharey=True)
    if len(scales) == 1:
        axes = [axes]

    for k, (ax, scale) in enumerate(zip(axes, scales)):
        with contextlib.redirect_stdout(io.StringIO()):
            ds = pipeline.load_dataset(scale)
        ns = ns_by.get(scale, 4)
        pool = int(np.sum(np.abs(ds.speeds_k - base_speed) < 0.1))
        nbs = sorted({min(n, pool) for n in n_base_list})

        eh = np.abs((ds.h_ac_arr - ds.f_ac_arr)
                    / (ds.f_ac_arr + 1e-12) * 100.0)
        hyb_w = float(np.sum(ds.f_ac_arr * eh) / np.sum(ds.f_ac_arr))

        for expo, sty in ((False, dict(color='#2e7d32', ls='--',
                                       marker='s',
                                       label=r'Scalar $f\cdot g$')),
                          (True, dict(color='#e65100', ls='-',
                                      marker='o',
                                      label=r'Exponent $f\cdot g^{p}$'))):
            ys = []
            for nb in nbs:
                vals = []
                for seed in range(n_seeds):
                    try:
                        with contextlib.redirect_stdout(io.StringIO()):
                            m = AcLossEvaluator.\
                                rebuild_sep_model_with_subsampling(
                                    ds, nb, ns, seed,
                                    base_speed=base_speed, exponent=expo)
                    except np.linalg.LinAlgError:
                        continue
                    pred = ds.h_ac_arr * m.predict(
                        ds.speeds_k * 1000.0, ds.irms_arr, ds.phase_arr)
                    e = np.abs((pred - ds.f_ac_arr)
                               / (ds.f_ac_arr + 1e-12) * 100.0)
                    vals.append(float(np.sum(ds.f_ac_arr * e)
                                      / np.sum(ds.f_ac_arr)))
                ys.append(min(np.mean(vals), 1e3) if vals else np.nan)
            ax.plot(nbs, ys, lw=1.2, ms=3.2, **sty)

        ax.axhline(hyb_w, color='#888888', ls=':', lw=0.9,
                   label='Hybrid, uncorrected')
        ax.axvline(pool, color='#2c6fad', ls=':', lw=0.9,
                   label=r'available $n_{base}$')
        ax.set_yscale('log')
        ax.set_xlabel(r'$n_{base}$ (16-kRPM base points)')
        if k == 0:
            ax.set_ylabel(r'wMAE [%] (log)')
            ax.legend(fontsize=6.0, frameon=False, loc='lower left')
        tag = chr(ord('a') + k)
        ax.set_title(f'({tag}) {scale} '
                     f'($k_r{{=}}{kr_by.get(scale, 1):g}$, '
                     f'{ns}/speed)', fontsize=8)
        ax.grid(True, which='both', ls=':', lw=0.4, color='#dddddd')
        ax.set_axisbelow(True)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_flux_torque_scaling(ref_fluxmap_mat: str, sc_satmap_mat: str,
                             out_path: str, k_r: float = 2.0,
                             k_a: float = 1.0, pole_pairs: int = 4,
                             ref_axes_rms: bool = True) -> dict:
    """Circuit-level scaling validation (Fig 11): scaled-Ref vs actual SC.

    ref_fluxmap_mat : FluxMap_Py export of the reference model
        (``FluxMap_dq`` struct with Id/Iq/Fd/Fq; dq axes in the Motor-CAD
        RMS-amplitude convention when ``ref_axes_rms``).
    sc_satmap_mat   : Motor-CAD Lab SaturationLossMap of the scaled model
        (peak dq axes, Flux_Linkage_D/Q, Electromagnetic_Torque).

    The reference map is converted to peak axes and scaled with
    ``motor_scaling.morphisms.scale_motor_map`` (I x k_r, lambda x
    k_a*k_r); torque is recomputed as 1.5 p (lam_d iq - lam_q id) so the
    comparison uses only scaled flux linkages. Panels: (a) flux-linkage
    contours, (b) torque contours (actual solid vs scaled dashed),
    (c) torque relative-error map. Returns the deviation metrics.
    """
    from scipy.interpolate import griddata
    from scipy.io import loadmat

    from motor_scaling.model.BaseMotorMap import BaseMotorMap
    from motor_scaling.morphisms.MotorScaler import scale_motor_map

    plt = _journal_rc()

    fm = loadmat(ref_fluxmap_mat)['FluxMap_dq'][0, 0]
    conv = np.sqrt(2.0) if ref_axes_rms else 1.0
    base = BaseMotorMap(
        id_grid=np.squeeze(fm['Id']) * conv,
        iq_grid=np.squeeze(fm['Iq']) * conv,
        lambda_d=np.squeeze(fm['Fd']),
        lambda_q=np.squeeze(fm['Fq']),
        r_dc=0.0,
        p_fe_grid=np.zeros_like(np.squeeze(fm['Fd'])),
        p_cu_ac_hybrid=np.zeros_like(np.squeeze(fm['Fd'])),
        pole_pairs=pole_pairs)
    scaled = scale_motor_map(base, k_r, k_a)

    d = loadmat(sc_satmap_mat)
    sid = np.squeeze(d['Id_Peak'])
    siq = np.squeeze(d['Iq_Peak'])
    lam_d_sc = np.squeeze(d['Flux_Linkage_D'])
    lam_q_sc = np.squeeze(d['Flux_Linkage_Q'])
    t_sc = np.squeeze(d['Electromagnetic_Torque'])

    pts = (scaled.id_grid.ravel(), scaled.iq_grid.ravel())
    lam_d_s = griddata(pts, scaled.lambda_d.ravel(), (sid, siq))
    lam_q_s = griddata(pts, scaled.lambda_q.ravel(), (sid, siq))
    t_s = 1.5 * pole_pairs * (lam_d_s * siq - lam_q_s * sid)

    valid = np.isfinite(lam_d_s)
    t_hi = np.abs(t_sc) > 0.05 * np.nanmax(np.abs(t_sc))
    m_t = valid & t_hi
    metrics = {
        'lam_d_rmse_mVs': float(np.sqrt(np.nanmean(
            (lam_d_s - lam_d_sc)[valid] ** 2)) * 1e3),
        'lam_q_rmse_mVs': float(np.sqrt(np.nanmean(
            (lam_q_s - lam_q_sc)[valid] ** 2)) * 1e3),
        'lam_q_mape_pct': float(np.nanmean(np.abs(
            (lam_q_s - lam_q_sc)[valid & (lam_q_sc > 0.05)]
            / lam_q_sc[valid & (lam_q_sc > 0.05)])) * 100),
        'torque_mape_pct': float(np.nanmean(np.abs(
            (t_s - t_sc)[m_t] / t_sc[m_t])) * 100),
        'torque_max_pct': float(np.nanmax(np.abs(
            (t_s - t_sc)[m_t] / t_sc[m_t])) * 100),
        # normalized by the map peak torque: avoids the blow-up where the
        # magnet and reluctance terms cancel (iq -> 0, deep-id corner,
        # far outside any operating trajectory)
        'torque_norm_mean_pct': float(np.nanmean(np.abs(
            (t_s - t_sc)[valid])) / np.nanmax(np.abs(t_sc)) * 100),
        'torque_norm_max_pct': float(np.nanmax(np.abs(
            (t_s - t_sc)[valid])) / np.nanmax(np.abs(t_sc)) * 100),
        'coverage_pct': float(np.mean(valid) * 100),
    }

    err_t = np.where(valid, np.abs(t_s - t_sc)
                     / np.nanmax(np.abs(t_sc)) * 100, np.nan)

    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.55),
                             layout='constrained')
    kw_sc = dict(colors='#1a3a5c', linewidths=0.9, linestyles='solid')
    kw_s = dict(colors='#e65100', linewidths=0.9, linestyles='dashed')

    ax = axes[0]
    lv_d = np.round(np.linspace(np.nanmin(lam_d_sc),
                                np.nanmax(lam_d_sc), 7), 2)
    lv_q = np.round(np.linspace(0.05, np.nanmax(lam_q_sc), 6), 2)
    c1 = ax.contour(sid, siq, lam_d_sc, levels=lv_d, **kw_sc)
    ax.contour(sid, siq, lam_d_s, levels=lv_d, **kw_s)
    ax.contour(sid, siq, lam_q_sc, levels=lv_q,
               colors='#5a7ea3', linewidths=0.7, linestyles='solid')
    ax.contour(sid, siq, lam_q_s, levels=lv_q,
               colors='#f0a860', linewidths=0.7, linestyles='dashed')
    ax.clabel(c1, fmt='%.2f', fontsize=5)
    ax.set_title(r'(a) $\lambda_d$ (dark), $\lambda_q$ (light) [Vs]',
                 fontsize=7.5)

    ax = axes[1]
    lv_t = np.linspace(200, np.nanmax(t_sc), 8)
    c1 = ax.contour(sid, siq, t_sc, levels=lv_t, **kw_sc)
    ax.contour(sid, siq, t_s, levels=lv_t, **kw_s)
    ax.clabel(c1, fmt='%.0f', fontsize=5)
    ax.set_title('(b) electromagnetic torque [Nm]', fontsize=7.5)

    ax = axes[2]
    pm = ax.pcolormesh(sid, siq, err_t, cmap='YlOrRd', vmin=0,
                       vmax=max(1.0, np.nanpercentile(err_t, 99.5)),
                       shading='auto')
    cb = fig.colorbar(pm, ax=ax, shrink=0.85)
    cb.set_label(r'$|\Delta T| / T_{max}$ [%]', fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    ax.set_title(f"(c) torque deviation "
                 f"(mean {metrics['torque_norm_mean_pct']:.2f}%"
                 f" of $T_{{max}}$)", fontsize=7.5)

    from matplotlib.lines import Line2D
    axes[0].legend(handles=[
        Line2D([], [], color='#1a3a5c', lw=0.9, label='SC, FEA'),
        Line2D([], [], color='#e65100', lw=0.9, ls='--',
               label=r'Ref, scaled ($k_r{=}2$)')],
        fontsize=5.8, frameon=False, loc='upper left')
    for ax in axes:
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('$i_d$ [A, pk]')
        ax.grid(True, ls=':', lw=0.4, color='#dddddd')
        ax.set_axisbelow(True)
    axes[0].set_ylabel('$i_q$ [A, pk]')

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return metrics


def plot_flux_torque_scaling_tps(comparison_mat: str, out_path: str,
                                 k_r: float = 2.0, pole_pairs: int = 4,
                                 n_grid: int = 121) -> dict:
    """Fig 11 from the .mot-embedded Lab build nodes, TPS-reconstructed.

    comparison_mat : lab_scaling_comparison_e10.mat written by
        extractLabScalingComparison_e10.m — structs ``scaledS`` (Ref build
        nodes with the SCL-M laws applied) and ``scS`` (actual SC build
        nodes), fields Is/Gamma/Id_pk/Iq_pk/PsiD/PsiQ.

    Both flux-linkage surfaces are rebuilt with the SAME thin-plate-spline
    interpolant on the (id, iq) nodes, so the comparison contains no
    Lab map-generation chain and no asymmetric gridding; the
    electromagnetic torque is recomputed from each side's fluxes as
    T_em = 1.5 p (psi_d iq - psi_q id). Returns deviation metrics.
    """
    from scipy.io import loadmat

    plt = _journal_rc()

    d = loadmat(comparison_mat)

    def unpack(name):
        s = d[name][0, 0]
        return {k: np.asarray(s[k]).ravel().astype(float)
                for k in ('Is', 'Gamma', 'Id_pk', 'Iq_pk', 'PsiD', 'PsiQ')}

    sca = unpack('scaledS')
    sc = unpack('scS')

    # The Lab build samples form a tensor grid in (Is, gamma), where the
    # flux surfaces are smooth and gently curved; fitting the TPS in that
    # polar domain (instead of scattered dq) avoids inter-node wiggle from
    # the coarse gamma spacing and involves no extrapolation anywhere
    # inside the quarter disc.
    ls_i = max(sc['Is'].max(), sca['Is'].max())
    ls_g = 90.0

    def tps_fit(s, g, v, lam=1e-10):
        n = len(s)
        r2 = (((s[:, None] - s[None, :]) / ls_i) ** 2
              + ((g[:, None] - g[None, :]) / ls_g) ** 2)
        phi = r2 * np.log(np.sqrt(r2) + 1e-12)
        w = np.linalg.solve(phi + lam * np.eye(n), v)

        def ev(s_g, g_g):
            r2g = (((s_g.ravel()[:, None] - s[None, :]) / ls_i) ** 2
                   + ((g_g.ravel()[:, None] - g[None, :]) / ls_g) ** 2)
            k = r2g * np.log(np.sqrt(r2g) + 1e-12)
            return (k @ w).reshape(s_g.shape)
        return ev

    f_d_sca = tps_fit(sca['Is'], sca['Gamma'], sca['PsiD'])
    f_q_sca = tps_fit(sca['Is'], sca['Gamma'], sca['PsiQ'])
    f_d_sc = tps_fit(sc['Is'], sc['Gamma'], sc['PsiD'])
    f_q_sc = tps_fit(sc['Is'], sc['Gamma'], sc['PsiQ'])

    amp = float(min(sc['Is'].max(), sca['Is'].max()))
    id_g = np.linspace(-amp, 0.0, n_grid)
    iq_g = np.linspace(0.0, amp, n_grid)
    ID, IQ = np.meshgrid(id_g, iq_g)
    IS_G = np.sqrt(ID**2 + IQ**2)
    # dq -> (Is, gamma): id = -Is sin(gamma), iq = Is cos(gamma)
    GA_G = np.degrees(np.arctan2(-ID, IQ))
    inside = IS_G <= amp * 1.0001

    lam_d_s, lam_q_s = f_d_sca(IS_G, GA_G), f_q_sca(IS_G, GA_G)
    lam_d_c, lam_q_c = f_d_sc(IS_G, GA_G), f_q_sc(IS_G, GA_G)
    for a in (lam_d_s, lam_q_s, lam_d_c, lam_q_c):
        a[~inside] = np.nan

    t_s = 1.5 * pole_pairs * (lam_d_s * IQ - lam_q_s * ID)
    t_c = 1.5 * pole_pairs * (lam_d_c * IQ - lam_q_c * ID)

    valid = inside & np.isfinite(t_c)
    t_hi = np.abs(t_c) > 0.05 * np.nanmax(np.abs(t_c))
    m_t = valid & t_hi
    metrics = {
        'lam_d_rmse_mVs': float(np.sqrt(np.nanmean(
            (lam_d_s - lam_d_c)[valid] ** 2)) * 1e3),
        'lam_q_rmse_mVs': float(np.sqrt(np.nanmean(
            (lam_q_s - lam_q_c)[valid] ** 2)) * 1e3),
        'lam_q_mape_pct': float(np.nanmean(np.abs(
            (lam_q_s - lam_q_c)[valid & (lam_q_c > 0.05)]
            / lam_q_c[valid & (lam_q_c > 0.05)])) * 100),
        'torque_mape_pct': float(np.nanmean(np.abs(
            (t_s - t_c)[m_t] / t_c[m_t])) * 100),
        'torque_norm_mean_pct': float(np.nanmean(np.abs(
            (t_s - t_c)[valid])) / np.nanmax(np.abs(t_c)) * 100),
        'torque_norm_max_pct': float(np.nanmax(np.abs(
            (t_s - t_c)[valid])) / np.nanmax(np.abs(t_c)) * 100),
    }

    err_t = np.where(valid, np.abs(t_s - t_c)
                     / np.nanmax(np.abs(t_c)) * 100, np.nan)

    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.55),
                             layout='constrained')
    kw_sc = dict(colors='#1a3a5c', linewidths=0.9, linestyles='solid')
    kw_s = dict(colors='#e65100', linewidths=0.9, linestyles='dashed')

    ax = axes[0]
    lv_d = np.round(np.linspace(np.nanmin(lam_d_c),
                                np.nanmax(lam_d_c), 7), 2)
    lv_q = np.round(np.linspace(0.05, np.nanmax(lam_q_c), 6), 2)
    c1 = ax.contour(ID, IQ, lam_d_c, levels=lv_d, **kw_sc)
    ax.contour(ID, IQ, lam_d_s, levels=lv_d, **kw_s)
    ax.contour(ID, IQ, lam_q_c, levels=lv_q,
               colors='#5a7ea3', linewidths=0.7, linestyles='solid')
    ax.contour(ID, IQ, lam_q_s, levels=lv_q,
               colors='#f0a860', linewidths=0.7, linestyles='dashed')
    ax.clabel(c1, fmt='%.2f', fontsize=5)
    ax.scatter(sc['Id_pk'], sc['Iq_pk'], s=4, c='#1a3a5c', marker='o',
               zorder=5, linewidths=0)
    ax.set_title(r'(a) $\lambda_d$ (dark), $\lambda_q$ (light) [Vs]',
                 fontsize=7.5)

    ax = axes[1]
    lv_t = np.linspace(200, np.nanmax(t_c), 8)
    c1 = ax.contour(ID, IQ, t_c, levels=lv_t, **kw_sc)
    ax.contour(ID, IQ, t_s, levels=lv_t, **kw_s)
    ax.clabel(c1, fmt='%.0f', fontsize=5)
    ax.set_title('(b) electromagnetic torque [Nm]', fontsize=7.5)

    ax = axes[2]
    pm = ax.pcolormesh(ID, IQ, err_t, cmap='YlOrRd', vmin=0,
                       vmax=max(1.0, np.nanpercentile(err_t, 99.5)),
                       shading='auto')
    cb = fig.colorbar(pm, ax=ax, shrink=0.85)
    cb.set_label(r'$|\Delta T_{em}| / T_{em,max}$ [%]', fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    ax.set_title(f"(c) torque deviation "
                 f"(mean {metrics['torque_norm_mean_pct']:.2f}%"
                 f" of $T_{{em,max}}$)", fontsize=7.5)

    from matplotlib.lines import Line2D
    axes[0].legend(handles=[
        Line2D([], [], color='#1a3a5c', lw=0.9,
               label='SC, FEA build nodes (TPS)'),
        Line2D([], [], color='#e65100', lw=0.9, ls='--',
               label=r'Ref, scaled ($k_r{=}2$, TPS)')],
        fontsize=5.5, frameon=False, loc='upper left')
    for ax in axes:
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('$i_d$ [A, pk]')
        ax.grid(True, ls=':', lw=0.4, color='#dddddd')
        ax.set_axisbelow(True)
    axes[0].set_ylabel('$i_q$ [A, pk]')

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return metrics
