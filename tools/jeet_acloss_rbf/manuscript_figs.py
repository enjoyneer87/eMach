"""Manuscript figure builders for the JEET paper.

Consolidates the session scripts into reusable functions:

* ``extract_mes_fields``     — element-wise (x, y, |B|, A) from Motor-CAD
  ``.mes`` solutions via an existing COM instance, saved as ``.npz``
* ``plot_field_panels``      — journal 2xN |B| / MVP panel figure from the
  extracted ``.npz`` snapshots (no Motor-CAD required)
* ``plot_motor_geometry_dxf``— dimensioned cross-section figure from a DXF
  (bulge arcs are honored via ezdxf path flattening, mirroring the MATLAB
  ``DXFtool/readDXF.m`` bulge handling)

All plots use the shared journal style: sans-serif lettering at
8--12 pt, matching the Springer figure requirements (Helvetica/Arial,
2--3 mm lettering, minimal size variance within an illustration).
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


# Springer 그림 규격: 글자는 Helvetica/Arial 계열 sans-serif, 인쇄 시
# 8--12 pt (2--3 mm), 한 그림 안에서 크기 편차 최소화. 선화 1200 dpi /
# 하프톤 300 / 혼합 600. 벡터(PDF)로 내보내므로 dpi 는 산점도처럼
# 래스터화되는 요소에만 걸린다.
FS_MIN, FS_MAX = 8.0, 12.0

# 치수 라벨이 도면 선 위에 놓일 때 가독성 확보용 흰 배경
_LBL_BOX = {'fc': 'white', 'ec': 'none', 'alpha': 0.85,
            'pad': 0.4}


def _fs(pt: float) -> float:
    """요청 글자 크기를 저널 허용 범위로 클램프한다."""
    return float(min(FS_MAX, max(FS_MIN, pt)))


def _journal_rc():
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 9, 'axes.titlesize': 9, 'axes.labelsize': 9,
        'xtick.labelsize': 8, 'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'axes.linewidth': 0.7, 'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.03,
        'savefig.dpi': 600,               # 혼합 아트 기준
        'mathtext.fontset': 'dejavusans',  # 본문 sans 와 정합
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
        ax.set_title(f'({chr(97 + col)}) {title}\n$|B|$', fontsize=10.9)

        ax2 = axes[1, col]
        h_a = ax2.scatter(d['x_mm'], d['y_mm'], c=d['a_Wbm'], s=point_size,
                          marker='.', cmap='RdBu_r',
                          vmin=-a_lim[col], vmax=a_lim[col],
                          rasterized=True, linewidths=0)
        ax2.set_title(f'({chr(97 + n + col)}) {title}\nMVP $A$',
                      fontsize=10.9)
        last_of_pair = (col % 2 == 1) if share_a_pairs else True
        if last_of_pair:
            lo = col - 1 if share_a_pairs else col
            cb = fig.colorbar(h_a, ax=list(axes[1, lo:col + 1]), shrink=0.8)
            cb.set_label('A [Wb/m]', fontsize=9.4)
            cb.ax.tick_params(labelsize=8.7)

        for a in (ax, ax2):
            a.set_aspect('equal')
            a.set_xticks([])
            a.set_yticks([])

    cb = fig.colorbar(h_b, ax=list(axes[0, :]), shrink=0.8)
    cb.set_label('|B| [T]', fontsize=9.4)
    cb.ax.tick_params(labelsize=8.7)

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
        ax.clabel(ct, fmt='%.2f', fontsize=8)
        sc = ax.scatter(id_v, iq_v, c=af_v, cmap='plasma', s=14,
                        edgecolors='k', linewidths=0.3,
                        vmin=vmin, vmax=vmax, zorder=3)
        # square dq plane: same A-per-inch on both current axes
        ax.set_aspect('equal', adjustable='box')
        ax.set_title(f'{spd / 1000:.0f} kRPM', fontsize=11.6)
        ax.set_xlabel('$i_d$ [A, pk]')
        if ax is axes[0]:
            ax.set_ylabel('$i_q$ [A, pk]')
        ax.grid(True, ls=':', lw=0.4, color='#cccccc')
        ax.set_axisbelow(True)
    cb = fig.colorbar(sc, ax=list(axes), shrink=0.85)
    cb.set_label('AF [-]', fontsize=10.2)
    cb.ax.tick_params(labelsize=9.4)

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
        ax.set_title(f'{spd / 1000:.0f} kRPM', fontsize=11.6, pad=0)
        ax.set_xlabel('$i_d$ [A]', fontsize=8.7, labelpad=-4)
        ax.set_ylabel('$i_q$ [A]', fontsize=8.7, labelpad=-4)
        ax.set_zlabel('AF', fontsize=8.7, labelpad=-4)
        ax.tick_params(labelsize=8, pad=-2)
        ax.view_init(28, -50)
    cb = fig.colorbar(surf, ax=fig.axes, shrink=0.7)
    cb.set_label('AF [-]', fontsize=10.2)
    cb.ax.tick_params(labelsize=9.4)

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
    # 0.95*columnwidth = 3.14 in 로 배치되므로 캔버스도 같게 잡는다.
    fig, ax = plt.subplots(figsize=(3.14, 2.50))
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
                ha='center', va='top', fontsize=10.9)

    hdim(0.0, r_rotor, -7.0, rf'$D_r/2 = {r_rotor:.1f}$')
    hdim(0.0, r_out, -15.0, rf'$D_s/2 = {r_out:.0f}$')

    # slot inset
    axins = ax.inset_axes([0.00, 0.46, 0.60, 0.54])
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
    axins.annotate(rf'$w_c={w_c:.1f}$', xy=((x0 + x1v) / 2, yy),
                   xytext=(0.62, 0.04), textcoords='axes fraction',
                   fontsize=10.2, ha='left', va='bottom',
                   bbox=_LBL_BOX,
                   arrowprops={'arrowstyle': '-', 'lw': 0.5,
                               'color': '0.4'})
    xx = x0 - 0.9
    axins.annotate('', xy=(xx, y1v), xytext=(xx, y0),
                   arrowprops={'arrowstyle': '<->', 'lw': 0.7,
                               'color': 'black'})
    # 리더선 끝만 데이터 좌표로 두고 글자는 축 비율로 배치해, 라벨이
    # 길어져도(예: h -> h_c) 인셋 밖으로 잘리지 않게 한다.
    axins.annotate(rf'$h_c={h_c:.1f}$', xy=(xx, (y0 + y1v) / 2),
                   xytext=(0.36, 0.97), textcoords='axes fraction',
                   fontsize=10.2, ha='left', va='top',
                   bbox=_LBL_BOX,
                   arrowprops={'arrowstyle': '-', 'lw': 0.5,
                               'color': '0.4'})
    a_sl = np.radians(slot_ang)
    gxm = 0.5 * (r_rotor + r_bore) * np.cos(a_sl)
    gym = 0.5 * (r_rotor + r_bore) * np.sin(a_sl)
    if x_lo < gxm < x_hi and y_lo < gym < y_hi:
        axins.annotate(rf'$l_g={g_air:.1f}$', xy=(gxm, gym),
                       xytext=(0.02, 0.06), textcoords='axes fraction',
                       fontsize=10.2, ha='left', va='bottom',
                       bbox=_LBL_BOX,
                       arrowprops={'arrowstyle': '->', 'lw': 0.6,
                                   'color': 'black'})
    ax.text(0.99, 0.01, 'unit: mm', transform=ax.transAxes,
            ha='right', va='bottom', fontsize=9.4, style='italic')

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
                          n_seeds: int = 10,
                          show_titles: bool = True,
                          placement: str = 'random') -> str:
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
    from .RbfModelBuilder import RbfModelBuilder

    plt = _journal_rc()
    if placement == 'structured':
        n_seeds = 1
    ns_by = n_spd_by_scale or {'Ref': 4, 'HalfSC': 3, 'SC': 4}
    kr_by = {'Ref': 1.0, 'HalfSC': 1.5, 'SC': 2.0}
    base_speed = pipeline.cfg['base_speed']

    # 캔버스 폭 = 논문에서의 인쇄 폭(0.31*textwidth = 2.12 in). 배율 1이
    # 되어야 rcParams 의 pt 값이 인쇄 크기와 일치한다.
    fig, axes = plt.subplots(1, len(scales),
                             figsize=(2.12 * len(scales), 2.12),
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
                                       label=r'Scalar $f\cdot\kappa$')),
                          (True, dict(color='#e65100', ls='-',
                                      marker='o',
                                      label=r'Exponent $f\cdot\kappa^{p}$'))):
            ys = []
            for nb in nbs:
                vals = []
                for seed in range(n_seeds):
                    try:
                        with contextlib.redirect_stdout(io.StringIO()):
                            if placement == 'structured':
                                plan = RbfModelBuilder.plan_sampling_indices(
                                    ds, n_base=nb, n_spd=ns,
                                    base_speed=base_speed,
                                    placement='structured', seed=seed)
                                m = RbfModelBuilder.build_separable_rbf(
                                    ds, base_speed=base_speed,
                                    exponent=expo, index_plan=plan)
                            else:
                                m = AcLossEvaluator.\
                                    rebuild_sep_model_with_subsampling(
                                        ds, nb, ns, seed,
                                        base_speed=base_speed,
                                        exponent=expo)
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
            ax.legend(fontsize=8.7, frameon=False, loc='lower left')
        if show_titles:
            tag = chr(ord('a') + k)
            ax.set_title(f'({tag}) {scale} '
                         f'($k_r{{=}}{kr_by.get(scale, 1):g}$, '
                         f'{ns}/speed)', fontsize=11.6)
        ax.grid(True, which='both', ls=':', lw=0.4, color='#dddddd')
        ax.set_axisbelow(True)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_transfer_ablation(pipeline, out_path: str, scale: str,
                           n_base_list=(8, 10, 12, 16, 20, 24),
                           n_spd_list=(0, 1, 2, 3, 4),
                           n_seeds: int = 10,
                           placement: str = 'structured',
                           adopted=(24, 3),
                           show_titles: bool = True) -> str:
    """wMAE heat map of the transfer plan over (n_base, n_spd8).

    Rows are 16-kRPM base-kernel points, columns are own calibration points
    at 8 kRPM.  ``placement='structured'`` uses the deterministic maximin +
    kappa-span rule, so each cell is a single run rather than a seed mean.
    The adopted cell is outlined.
    """
    from matplotlib.colors import LogNorm
    from matplotlib.patches import Rectangle

    plt = _journal_rc()
    grid = pipeline.transfer_ablation_grid(
        scale, list(n_base_list), list(n_spd_list),
        n_seeds=n_seeds, placement=placement)
    G = np.clip(np.asarray(grid['wmae_pct'], float), None, 1e3)

    fig, ax = plt.subplots(figsize=(3.1, 2.5), layout='constrained')
    vmin = max(np.nanmin(G), 1e-2)
    im = ax.imshow(G, cmap='RdYlGn_r', aspect='auto', origin='lower',
                   norm=LogNorm(vmin=vmin, vmax=np.nanmax(G)))

    for i in range(G.shape[0]):
        for j in range(G.shape[1]):
            v = G[i, j]
            if not np.isfinite(v):
                continue
            ax.text(j, i, f'{v:.0f}' if v >= 100 else f'{v:.1f}',
                    ha='center', va='center', fontsize=8.1,
                    color='white' if v > 10 * vmin else '#222222')

    if adopted is not None:
        try:
            ai = list(n_base_list).index(adopted[0])
            aj = list(n_spd_list).index(adopted[1])
            ax.add_patch(Rectangle((aj - 0.5, ai - 0.5), 1, 1, fill=False,
                                   edgecolor='#1a1a1a', lw=1.6))
        except ValueError:
            pass

    ax.set_xticks(range(len(n_spd_list)))
    ax.set_xticklabels([str(v) for v in n_spd_list])
    ax.set_yticks(range(len(n_base_list)))
    ax.set_yticklabels([str(v) for v in n_base_list])
    ax.set_xlabel(r'$n_{spd8}$ (own 8-kRPM points)')
    ax.set_ylabel(r'$n_{base}$ (16-kRPM base points)')
    if show_titles:
        ax.set_title(f'{scale} ({placement})', fontsize=11.6)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label('wMAE [%]', fontsize=9.4)
    cb.ax.tick_params(labelsize=8.4)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_cost_accuracy(sweep, out_path: str, scale: str,
                       show_titles: bool = True,
                       annotate_adopted: bool = True) -> str:
    """Cost--accuracy Pareto front of the sampling plan for one scale.

    x = own TS-FEA points actually spent (transferred probes are free),
    y = full-map wMAE.  One curve per plan variant (own / transfer x
    random / structured).  ``sweep`` is the dict from
    ``cost_accuracy.sweep_cost_accuracy``.
    """
    plt = _journal_rc()
    e = sweep['scales'][scale]

    sty = {
        'own/random': dict(color='#8d8d8d', ls='--', marker='s',
                           label='Own, random'),
        'own/structured': dict(color='#2e7d32', ls='-', marker='s',
                               label='Own, structured'),
        'transfer/random': dict(color='#b28ad8', ls='--', marker='o',
                                label='Transfer, random'),
        'transfer/structured': dict(color='#e65100', ls='-', marker='o',
                                    label='Transfer, structured'),
    }

    fig, ax = plt.subplots(figsize=(3.08, 2.5), layout='constrained')
    for name, front in e['pareto_by_variant'].items():
        if not front:
            continue
        xs = [r['budget'] for r in front]
        ys = [r['wmae'] for r in front]
        ax.plot(xs, ys, lw=1.2, ms=3.2,
                **sty.get(name, dict(label=name)))

    ax.axhline(e['hybrid_wmae'], color='#888888', ls=':', lw=0.9,
               label='Hybrid, uncorrected')
    if annotate_adopted:
        best = e['pareto_by_variant'].get('transfer/structured') or []
        pick = next((r for r in best if r['budget'] == 27), None)
        if pick:
            ax.annotate(f"adopted: {pick['budget']} pts, "
                        f"{pick['wmae']:.2f}%",
                        xy=(pick['budget'], pick['wmae']),
                        xytext=(-52, -1), textcoords='offset points',
                        fontsize=8.7, ha='right', va='center',
                        arrowprops=dict(arrowstyle='->', lw=0.7,
                                        color='#444444'))
    ax.set_yscale('log')
    ax.set_xlabel('own TS-FEA points (cost)')
    ax.set_ylabel(r'wMAE [%] (log)')
    ax.legend(fontsize=8.4, frameon=False, loc='upper right')
    if show_titles:
        ax.set_title(f"{scale} ($k_r{{=}}{e['k_r']:g}$)", fontsize=11.6)
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
    ax.clabel(c1, fmt='%.2f', fontsize=8)
    ax.set_title(r'(a) $\lambda_d$ (dark), $\lambda_q$ (light) [Vs]',
                 fontsize=10.9)

    ax = axes[1]
    lv_t = np.linspace(200, np.nanmax(t_sc), 8)
    c1 = ax.contour(sid, siq, t_sc, levels=lv_t, **kw_sc)
    ax.contour(sid, siq, t_s, levels=lv_t, **kw_s)
    ax.clabel(c1, fmt='%.0f', fontsize=8)
    ax.set_title('(b) electromagnetic torque [Nm]', fontsize=10.9)

    ax = axes[2]
    pm = ax.pcolormesh(sid, siq, err_t, cmap='YlOrRd', vmin=0,
                       vmax=max(1.0, np.nanpercentile(err_t, 99.5)),
                       shading='auto')
    cb = fig.colorbar(pm, ax=ax, shrink=0.85)
    cb.set_label(r'$|\Delta T| / T_{max}$ [%]', fontsize=9.4)
    cb.ax.tick_params(labelsize=8.7)
    ax.set_title(f"(c) torque deviation "
                 f"(mean {metrics['torque_norm_mean_pct']:.2f}%"
                 f" of $T_{{max}}$)", fontsize=10.9)

    from matplotlib.lines import Line2D
    axes[0].legend(handles=[
        Line2D([], [], color='#1a3a5c', lw=0.9, label='SC, FEA'),
        Line2D([], [], color='#e65100', lw=0.9, ls='--',
               label=r'Ref, scaled ($k_r{=}2$)')],
        fontsize=8.4, frameon=False, loc='upper left')
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
    ax.clabel(c1, fmt='%.2f', fontsize=8)
    ax.scatter(sc['Id_pk'], sc['Iq_pk'], s=4, c='#1a3a5c', marker='o',
               zorder=5, linewidths=0)
    ax.set_title(r'(a) $\lambda_d$ (dark), $\lambda_q$ (light) [Vs]',
                 fontsize=10.9)

    ax = axes[1]
    lv_t = np.linspace(200, np.nanmax(t_c), 8)
    c1 = ax.contour(ID, IQ, t_c, levels=lv_t, **kw_sc)
    ax.contour(ID, IQ, t_s, levels=lv_t, **kw_s)
    ax.clabel(c1, fmt='%.0f', fontsize=8)
    ax.set_title('(b) electromagnetic torque [Nm]', fontsize=10.9)

    ax = axes[2]
    pm = ax.pcolormesh(ID, IQ, err_t, cmap='YlOrRd', vmin=0,
                       vmax=max(1.0, np.nanpercentile(err_t, 99.5)),
                       shading='auto')
    cb = fig.colorbar(pm, ax=ax, shrink=0.85)
    cb.set_label(r'$|\Delta T_{em}| / T_{em,max}$ [%]', fontsize=9.4)
    cb.ax.tick_params(labelsize=8.7)
    ax.set_title(f"(c) torque deviation "
                 f"(mean {metrics['torque_norm_mean_pct']:.2f}%"
                 f" of $T_{{em,max}}$)", fontsize=10.9)

    from matplotlib.lines import Line2D
    axes[0].legend(handles=[
        Line2D([], [], color='#1a3a5c', lw=0.9,
               label='SC, FEA build nodes (TPS)'),
        Line2D([], [], color='#e65100', lw=0.9, ls='--',
               label=r'Ref, scaled ($k_r{=}2$, TPS)')],
        fontsize=8, frameon=False, loc='upper left')
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


# ── Fig 2: single-slot eddy-current-density contour (TS-FEA vs Hybrid) ──

# svjour3 twocolumn 의 \columnwidth = 238.96 pt = 3.31 in.
# 캔버스 폭을 실제 인쇄 폭에 맞춰야 선언한 pt 가 그대로 인쇄된다
# (안 맞추면 \includegraphics 축소 배율만큼 글자가 작아진다).
_COLW_IN = 3.31


_AIRGAP_R2 = {
    # 1차 회전 후 로컬 +x = 반경 바깥쪽(슬롯 바닥), -x = 반경 안쪽(공극).
    # 이 표는 공극이 화면의 어느 쪽에 오는지에 따른 2차 회전이다.
    'left':   np.array([[1.0, 0.0], [0.0, 1.0]]),
    'right':  np.array([[-1.0, 0.0], [0.0, -1.0]]),
    'top':    np.array([[0.0, 1.0], [-1.0, 0.0]]),
    'bottom': np.array([[0.0, -1.0], [1.0, 0.0]]),
}


def _is_slot_filler(name: str) -> bool:
    """도체는 아니지만 **슬롯 내부**를 채우는 영역인가.

    함침/절연(``Impreg_LossSlot``), 웨지(``StatorWedge``), 슬롯 개구부
    공기(``StatorAir``). 철심(``Stator``)과 공극(``a1``..)은 제외한다 ---
    철심은 |B| 가 1.5 T 대라 슬롯 내부 스케일을 완전히 덮어버린다.
    """
    s = name.lower().replace('_', '')
    return ('impreg' in s or 'wedge' in s
            or 'statorair' in s or 'slotair' in s)


def _slot_frame(p: dict, slot_id: int, airgap_side: str = 'bottom',
                domain: str = 'conductors', margin_mm: float = 1.5,
                R_override: Optional[np.ndarray] = None):
    """한 슬롯을 로컬(회전) 좌표로 변환하고 삼각분할·화살표 위치를 만든다.

    Fig 9(``plot_motor_geometry_dxf``)와 동일한 1차 회전 관례 위에,
    ``airgap_side`` 로 공극이 화면의 어느 쪽에 오는지 고른다
    ('left','right','top','bottom').

    ``domain='conductors'`` (기본): 도체 요소만 --- Je 비교(Fig 2)용.
    ``domain='slot'``: 도체 + 함침/웨지/슬롯공기까지, 즉 **슬롯 내부 전체
    메시**. B 는 도체 밖에도 존재하므로 B 그림에는 이쪽을 쓴다. 회전
    기준각은 두 경우 모두 도체 무게중심으로 잡아 프레임이 일치한다.
    """
    import matplotlib.tri as mtri
    from .field_metrics import slot_conductor_codes

    if airgap_side not in _AIRGAP_R2:
        raise ValueError("airgap_side must be one of %s"
                         % sorted(_AIRGAP_R2))
    if domain not in ('conductors', 'slot'):
        raise ValueError("domain must be 'conductors' or 'slot'")

    codes = slot_conductor_codes(p, slot_id)
    cond_mask = np.isin(p['reg'], list(codes))
    if not cond_mask.any():
        raise ValueError('slot %d: no conductor elements matched' % slot_id)

    if R_override is not None:
        R = R_override
    else:
        xc, yc = p['x_mm'][cond_mask], p['y_mm'][cond_mask]
        ang = float(np.degrees(np.arctan2(yc.mean(), xc.mean())))
        th = np.radians(-ang)
        R1 = np.array([[np.cos(th), -np.sin(th)],
                       [np.sin(th), np.cos(th)]])
        R = _AIRGAP_R2[airgap_side] @ R1

    if domain == 'conductors':
        mask = cond_mask
    else:
        # 도체 bbox 를 margin 만큼 넓힌 창 안의 "슬롯 채움" 영역을 더한다
        pr_all = np.column_stack([p['x_mm'], p['y_mm']]) @ R.T
        pc = pr_all[cond_mask]
        cx0, cx1 = pc[:, 0].min(), pc[:, 0].max()
        cy0, cy1 = pc[:, 1].min(), pc[:, 1].max()
        win = ((pr_all[:, 0] >= cx0 - margin_mm)
               & (pr_all[:, 0] <= cx1 + margin_mm)
               & (pr_all[:, 1] >= cy0 - margin_mm)
               & (pr_all[:, 1] <= cy1 + margin_mm))
        filler = np.array([_is_slot_filler(p['names'].get(c, ''))
                           for c in p['reg']])
        mask = cond_mask | (win & filler)

    x, y = p['x_mm'][mask], p['y_mm'][mask]
    tri = p['tri'][mask]
    node_ids = np.unique(tri.ravel())
    id_map = {nid: i for i, nid in enumerate(node_ids)}
    tri_local = np.vectorize(id_map.get)(tri)
    nd_pr = p['node_xy'][node_ids] @ R.T
    triang = mtri.Triangulation(nd_pr[:, 0], nd_pr[:, 1], tri_local)

    pr = np.column_stack([x, y]) @ R.T
    x0, x1v = float(pr[:, 0].min()), float(pr[:, 0].max())
    y0, y1v = float(pr[:, 1].min()), float(pr[:, 1].max())
    anchor = {'left': (x0, 0.5 * (y0 + y1v)),
             'right': (x1v, 0.5 * (y0 + y1v)),
             'top': (0.5 * (x0 + x1v), y1v),
             'bottom': (0.5 * (x0 + x1v), y0)}[airgap_side]

    return {'triang': triang, 'mask': mask, 'R': R,
            'bbox': (x0, x1v, y0, y1v), 'anchor': anchor,
            'airgap_side': airgap_side}


def _node_average(tri_local, n_nodes, elem_values):
    """요소값을 그 요소가 공유하는 절점에 평균해 절점값으로 만든다."""
    node_val = np.zeros(n_nodes)
    node_cnt = np.zeros(n_nodes)
    for k in range(3):
        np.add.at(node_val, tri_local[:, k], elem_values)
        np.add.at(node_cnt, tri_local[:, k], 1)
    return node_val / np.maximum(node_cnt, 1)


def _boundary_segments(triang) -> np.ndarray:
    """삼각분할의 **외곽 경계** 선분들을 뽑는다 (N, 2, 2).

    삼각형 하나에만 속한 변이 곧 경계다. DXF 를 따로 읽어 정합시킬 필요가
    없다 --- 메시 자체가 이미 필드 데이터와 같은 좌표계에 있으므로
    회전·원점 정합 오차가 원천적으로 생기지 않는다.
    """
    tris = triang.triangles
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    e = np.sort(e, axis=1)
    uniq, cnt = np.unique(e, axis=0, return_counts=True)
    b = uniq[cnt == 1]
    return np.stack([np.column_stack([triang.x[b[:, 0]], triang.y[b[:, 0]]]),
                     np.column_stack([triang.x[b[:, 1]], triang.y[b[:, 1]]])],
                    axis=1)


def _draw_slot_contour(ax, frame: dict, je_values: np.ndarray,
                       vlim: float, cmap: str = 'plasma',
                       n_levels: int = 21, show_airgap_label: bool = True,
                       vmin: Optional[float] = None,
                       outline: Optional[np.ndarray] = None,
                       extent: Optional[tuple] = None):
    """``_slot_frame`` 결과 위에 매끄러운 등고선(tricontourf)을 그린다.

    ``je_values`` 는 이미 ``frame['mask']`` 로 선택된(즉 도메인 요소 개수와
    같은 길이의) 값이어야 한다 --- 두 패널이 서로 다른 데이터셋에서 온
    값을 같은 ``frame``(같은 도메인/삼각분할) 위에 그릴 수 있게 하기
    위해, 이 함수는 원본 전체 배열이 아니라 선택된 값만 받는다.

    ``vmin`` 생략 시 ``-vlim``(부호 있는 Je 용 발산 스케일), 0 을 주면
    크기값(|B| 등) 용 순차 스케일이 된다.

    ``outline`` 은 ``_boundary_segments`` 가 만든 슬롯 외곽선(선분 배열),
    ``extent`` 는 축 범위 계산에 쓸 bbox 다. 둘을 슬롯 도메인 기준으로
    넘기면 Je 그림(도체만)과 B 그림(슬롯 전체)이 **같은 축척**으로 그려져
    같은 슬롯임이 눈에 보인다.
    """
    triang = frame['triang']
    n_nodes = triang.x.size
    node_je = _node_average(triang.triangles, n_nodes, je_values)
    levels = np.linspace(-vlim if vmin is None else vmin, vlim, n_levels)
    cf = ax.tricontourf(triang, node_je, levels=levels, cmap=cmap,
                        extend='both')
    ax.tricontour(triang, node_je, levels=levels, colors='k',
                 linewidths=0.15, alpha=0.35)

    if outline is not None and len(outline):
        from matplotlib.collections import LineCollection
        ax.add_collection(LineCollection(outline, colors='0.25',
                                         linewidths=0.6, zorder=5))

    x0, x1v, y0, y1v = extent if extent is not None else frame['bbox']
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    side = frame['airgap_side']
    if side in ('top', 'bottom'):
        pad_main, pad_arrow = 0.10 * (x1v - x0), 0.085 * (y1v - y0)
        ax.set_xlim(x0 - pad_main, x1v + pad_main)
        lo = y0 - pad_arrow if side == 'bottom' else y0
        hi = y1v + pad_arrow if side == 'top' else y1v
        ax.set_ylim(lo, hi)
    else:
        pad_main, pad_arrow = 0.10 * (y1v - y0), 0.20 * (x1v - x0)
        ax.set_ylim(y0 - pad_main, y1v + pad_main)
        lo = x0 - pad_arrow if side == 'left' else x0
        hi = x1v + pad_arrow if side == 'right' else x1v
        ax.set_xlim(lo, hi)

    if show_airgap_label:
        if extent is not None:
            # 공유 extent 를 쓸 땐 화살표도 그 경계에 붙어야 한다
            ax0, ay0 = {'left': (x0, 0.5 * (y0 + y1v)),
                        'right': (x1v, 0.5 * (y0 + y1v)),
                        'top': (0.5 * (x0 + x1v), y1v),
                        'bottom': (0.5 * (x0 + x1v), y0)}[frame['airgap_side']]
        else:
            ax0, ay0 = frame['anchor']
        d = {'left': (-1, 0), 'right': (1, 0),
            'top': (0, 1), 'bottom': (0, -1)}[side]
        # 짧게: 화살표 길이·여백을 줄이고 라벨도 'gap' 으로
        scale = 0.055 * max(x1v - x0, y1v - y0)
        tip = (ax0 + d[0] * scale, ay0 + d[1] * scale)
        ax.annotate('', xy=tip, xytext=(ax0, ay0),
                   arrowprops={'arrowstyle': '-|>', 'lw': 1.0,
                               'color': 'black',
                               'shrinkA': 0, 'shrinkB': 0})
        # 텍스트 없이 화살표만 --- 하단 (a)/(b) 라벨과 겹치지 않게 하고
        # 공극 방향은 캡션에서 설명한다(공간도 아낀다).
    return cf


def plot_fig2_slot_comparison(ts_path: str, hybrid_path: str,
                              out_path: str, slot_id: int = 1,
                              step: int = 70,
                              freq_hz: float = 1066.67,
                              airgap_side: str = 'bottom',
                              show_titles: bool = False,
                              vlim_percentile: float = 98.0,
                              copper_height_mm: Optional[float] = 1.686
                              ) -> dict:
    """Fig 2: 단일 슬롯의 TS-FEA 실측 Je vs Hybrid 참고 재구성 Je (정적).

    두 패널 모두 **TS-FEA 의 도체 메시(형상·삼각분할)** 를 도메인으로
    쓴다 --- Hybrid 는 자신의(더 거칠거나 이상화된) 메시가 아니라, 그
    B 로부터 재구성한 값을 TS-FEA 도체 요소의 좌표에서 평가해 얹는다
    (``hybrid_je_at_points``). 두 데이터셋이 물리적으로 같은 슬롯을
    가리키는지는 REPRODUCE.md 의 각도 대조 방법으로 미리 확인해 둘 것.

    ``ts_path``/``hybrid_path`` 는 전 주기 export(다중 Solution 블록)
    텍스트. ``step`` 은 1-based 블록 번호(둘 다 같은 회전각 격자로
    동기화돼 있어야 한다).

    Returns dict with the per-element field data actually plotted (for
    JSON export alongside the figure).
    """
    from .field_metrics import parse_mes_txt, hybrid_je_at_points

    plt = _journal_rc()
    p_ts = parse_mes_txt(ts_path, block=step)
    p_hy = parse_mes_txt(hybrid_path, block=step)

    f_ts = _slot_frame(p_ts, slot_id, airgap_side)      # 유일한 도메인
    m_ts = f_ts['mask']
    je_ts = np.abs(p_ts['je_am2'][m_ts]) / 1e6          # A/mm2, 크기

    xy_ts = np.column_stack([p_ts['x_mm'][m_ts], p_ts['y_mm'][m_ts]])
    # signed=False --- 재구성값의 위상 기준은 임의라 Re[J] 를 그리면 그
    # 임의 위상에서의 단면(여기서는 |J| 의 1/8~1/10)만 보여 실제보다
    # 훨씬 평탄해진다. 두 패널 모두 크기로 비교한다 (REPRODUCE.md 14).
    je_hy = hybrid_je_at_points(p_hy, xy_ts, freq_hz, slot_id=slot_id,
                               signed=False,
                               thickness_mm=copper_height_mm) / 1e6

    geom = slot_reference_geometry(p_ts, slot_id, airgap_side,
                                   p_outline=p_hy)
    # 최댓값으로 자르면 공극 코너의 단일 핫스폿(738)이 스케일을 독점해
    # 나머지가 전부 검게 뭉갠다. 분위수로 잘라 상단은 포화시키고
    # (extend='both') 본체 구조가 보이게 한다.
    vlim = float(np.percentile(np.concatenate([je_ts, je_hy]),
                               vlim_percentile))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(_COLW_IN, 2.6),
                                  layout='constrained')
    kw = {'cmap': 'plasma', 'vmin': 0.0,
          'outline': geom['outline'], 'extent': geom['extent']}
    cf = _draw_slot_contour(ax1, f_ts, je_ts, vlim, **kw)
    _draw_slot_contour(ax2, f_ts, je_hy, vlim, **kw)
    if show_titles:
        ax1.set_xlabel('(a)', fontsize=9)
        ax2.set_xlabel('(b)', fontsize=9)
    cb = fig.colorbar(cf, ax=(ax1, ax2), shrink=0.85)
    cb.set_label(r'$|J_e|$ [A/mm$^2$]', fontsize=9)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)

    return {
        'slot_id': slot_id, 'step': step, 'freq_hz': freq_hz,
        'airgap_side': airgap_side, 'vlim_A_mm2': float(vlim),
        'rotate_deg': p_ts.get('rotate_deg'),
        'quantity': 'magnitude |Je| (reconstruction phase reference is'
                    ' arbitrary, so Re[J] is not comparable)',
        'domain': 'TS-FEA conductor mesh (both panels); slot outline and'
                  ' axis extent shared with the |B| figure',
        'x_mm': xy_ts[:, 0].tolist(), 'y_mm': xy_ts[:, 1].tolist(),
        'ts_fea': {'je_A_mm2': je_ts.tolist()},
        'hybrid_reference': {'je_A_mm2': je_hy.tolist()},
    }


def make_fig2_slot_gif(ts_path: str, hybrid_path: str, out_gif: str,
                       slot_id: int = 1, freq_hz: float = 1066.67,
                       airgap_side: str = 'bottom', fps: int = 10,
                       out_json: Optional[str] = None,
                       copper_height_mm: Optional[float] = 1.686) -> dict:
    """Fig 2 소재의 128스텝 동기 애니메이션(TS-FEA 실측 vs Hybrid 참고).

    ``plot_fig2_slot_comparison`` 과 같은 원칙으로, 매 스텝 두 패널
    모두 **그 스텝 TS-FEA 의 도체 메시**를 도메인으로 쓴다. Hybrid 는
    그 스텝의 B 로 재구성한 값을 TS-FEA 좌표에서 평가해 얹는다.

    ``ts_path``/``hybrid_path`` 는 같은 회전각 격자로 export 된 전 주기
    데이터여야 한다. 매 스텝 색상 스케일은 전 스텝 공통(99.5th
    percentile)으로 고정한다.

    ``out_json`` 이 주어지면 스텝별 |Je| 최댓값 등 요약 시계열을 저장한다
    (원시 프레임 전체를 JSON 에 담기엔 너무 커서, 그림의 재현에 필요한
    것은 이 함수 자체이고 JSON 은 스텝 선택 근거 요약임을 명시).
    """
    from .field_metrics import iter_mes_blocks, hybrid_je_at_points
    from matplotlib.animation import PillowWriter

    plt = _journal_rc()

    print('TS-FEA/Hybrid 동기 파싱 중 ...')
    frames = []
    for (step_ts, p_ts), (step_hy, p_hy) in zip(iter_mes_blocks(ts_path),
                                                iter_mes_blocks(hybrid_path)):
        f_ts = _slot_frame(p_ts, slot_id, airgap_side)
        m_ts = f_ts['mask']
        je_ts = np.abs(p_ts['je_am2'][m_ts]) / 1e6
        xy_ts = np.column_stack([p_ts['x_mm'][m_ts], p_ts['y_mm'][m_ts]])
        je_hy = hybrid_je_at_points(p_hy, xy_ts, freq_hz, slot_id=slot_id,
                                    signed=False,
                                    thickness_mm=copper_height_mm) / 1e6
        geom = slot_reference_geometry(p_ts, slot_id, airgap_side,
                                       p_outline=p_hy)
        frames.append({'step': step_ts, 'rotate_deg': p_ts['rotate_deg'],
                       'frame': f_ts, 'je_ts': je_ts, 'je_hy': je_hy,
                       'geom': geom})
    n = len(frames)
    print('동기화 프레임 %d개' % n)

    all_je = np.concatenate([f['je_ts'] for f in frames]
                            + [f['je_hy'] for f in frames])
    vlim = float(np.percentile(np.abs(all_je), 99.5))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(_COLW_IN, 2.6),
                                  layout='constrained')

    def kw_of(rec):
        return {'cmap': 'inferno', 'vmin': 0.0,
                'outline': rec['geom']['outline'],
                'extent': rec['geom']['extent']}

    cf = _draw_slot_contour(ax1, frames[0]['frame'], frames[0]['je_ts'],
                            vlim, **kw_of(frames[0]))
    _draw_slot_contour(ax2, frames[0]['frame'], frames[0]['je_hy'], vlim,
                       **kw_of(frames[0]))
    ax1.set_title('TS-FEA', fontsize=9)
    ax2.set_title('Hybrid (reference, on TS-FEA mesh)', fontsize=9)
    cb = fig.colorbar(cf, ax=(ax1, ax2), shrink=0.85)
    cb.set_label(r'$|J_e|$ [A/mm$^2$]', fontsize=9)
    suptitle = fig.suptitle('', fontsize=8)

    step_max = []

    def update(i):
        rec = frames[i]
        ax1.clear()
        _draw_slot_contour(ax1, rec['frame'], rec['je_ts'], vlim,
                          show_airgap_label=True, **kw_of(rec))
        ax2.clear()
        _draw_slot_contour(ax2, rec['frame'], rec['je_hy'], vlim,
                          show_airgap_label=True, **kw_of(rec))
        # ax.clear() 가 라벨도 지우므로 매 프레임 다시 붙인다
        ax1.set_xlabel('(a) TS-FEA', fontsize=9)
        ax2.set_xlabel('(b) Hybrid (reference)', fontsize=9)
        suptitle.set_text('slot %d   step %d/%d   rotate %.2f deg'
                          % (slot_id, i + 1, n, rec['rotate_deg']))
        step_max.append({
            'step': i + 1, 'rotate_deg': rec['rotate_deg'],
            'ts_fea_max_A_mm2': float(np.abs(rec['je_ts']).max()),
            'hybrid_ref_max_A_mm2': float(np.abs(rec['je_hy']).max()),
        })

    os.makedirs(os.path.dirname(os.path.abspath(out_gif)), exist_ok=True)
    writer = PillowWriter(fps=fps)
    with writer.saving(fig, out_gif, dpi=110):
        for i in range(n):
            update(i)
            writer.grab_frame()
    plt.close(fig)
    print('GIF 저장:', out_gif)

    summary = {'slot_id': slot_id, 'freq_hz': freq_hz,
              'airgap_side': airgap_side, 'n_frames': n,
              'vlim_A_mm2': vlim,
              'domain': 'TS-FEA conductor mesh (both panels)',
              'per_step': step_max}
    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)),
                   exist_ok=True)
        with open(out_json, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=1)
        print('요약 JSON 저장:', out_json)
    return summary


def slot_reference_geometry(p: dict, slot_id: int = 1,
                            airgap_side: str = 'bottom',
                            p_outline: Optional[dict] = None) -> dict:
    """Je 그림과 B 그림이 **공유할** 슬롯 외곽선·축범위를 만든다.

    슬롯 내부 전체 도메인(도체+함침+웨지+공기)의 경계선과 bbox 를 돌려
    준다. Je 그림은 도체만 색칠하지만 이 외곽선과 bbox 를 함께 쓰면 두
    그림이 같은 축척·같은 형상으로 그려져 같은 슬롯임이 드러난다.

    DXF 대신 메시에서 뽑는 이유는 ``_boundary_segments`` 참조 (좌표계
    정합 문제가 없다).

    ``p_outline`` 을 주면 외곽선만 그 데이터셋에서 뽑되 **회전 프레임은
    ``p`` 것을 그대로 쓴다**(두 그림의 정합 유지). TS-FEA 의 슬롯 개구부
    는 ``StatorAir`` 메시가 거칠어 경계가 톱니처럼 뜯겨 보이므로, 개구부
    형상이 매끈한 MS-FEA 메시를 외곽선 소스로 넘기는 용도다.
    """
    f_slot = _slot_frame(p, slot_id, airgap_side, domain='slot')
    if p_outline is None:
        return {'outline': _boundary_segments(f_slot['triang']),
                'extent': f_slot['bbox'], 'frame': f_slot}
    f_out = _slot_frame(p_outline, slot_id, airgap_side, domain='slot',
                        R_override=f_slot['R'])
    return {'outline': _boundary_segments(f_out['triang']),
            'extent': f_out['bbox'], 'frame': f_slot}


def plot_fig2_slot_rms(ts_path: str, hybrid_path: str, out_path: str,
                       slot_id: int = 1, freq_hz: float = 1066.67,
                       airgap_side: str = 'bottom',
                       show_titles: bool = True,
                       vlim_percentile: float = 98.0,
                       copper_height_mm: Optional[float] = 1.686,
                       out_json: Optional[str] = None) -> dict:
    """Fig 2 의 **주기-RMS** 판 --- 순시 스냅샷 비교의 사과-오렌지 문제 해소.

    ``plot_fig2_slot_comparison`` 은 한 스텝의 TS-FEA **순시** Je 를
    재구성의 **페이저 진폭**과 나란히 놓는다. 두 양은 정의가 달라서
    그대로 비교하면 안 되고, 게다가 그 스텝은 |Je| 전역 최댓값 스텝으로
    고른 것이라(REPRODUCE.md 주의 8) **구성상 쏠림이 최대로 보이는
    시점**이다. 두 효과가 겹쳐 Hybrid 의 결함이 실제보다 크게 보인다.

    이 함수는 전 주기(128블록)를 훑어 요소별 RMS 를 만든다. TS 는 순시값
    의 RMS, 재구성은 진폭/sqrt(2) 의 RMS 로 **같은 정의**가 된다.

    이 기준에서 관측되는 것(실측): 재구성은 반경방향 쏠림 **기울기**를
    거의 맞춘다(공극층/슬롯바닥층 비 TS 2.52 vs 재구성 2.44). 못 맞추는
    것은 **크기**로, 손실 대리 지표에서 약 15배 낮다. 즉 Hybrid 의 결함은
    "쏠림을 못 본다"가 아니라 "쏠림의 세기를 과소평가한다"이다.
    """
    from .field_metrics import (iter_mes_blocks, slot_conductor_codes,
                                hybrid_je_at_points)

    plt = _journal_rc()
    print('전 주기 RMS 누적 중 ...')
    sq_ts = sq_hy = None
    n = 0
    p_last = None
    for (_, p_ts), (_, p_hy) in zip(iter_mes_blocks(ts_path),
                                    iter_mes_blocks(hybrid_path)):
        m = np.isin(p_ts['reg'], list(slot_conductor_codes(p_ts, slot_id)))
        if sq_ts is None:
            sq_ts = np.zeros(int(m.sum()))
            sq_hy = np.zeros(int(m.sum()))
        xy = np.column_stack([p_ts['x_mm'][m], p_ts['y_mm'][m]])
        sq_ts += (p_ts['je_am2'][m] / 1e6) ** 2
        amp = hybrid_je_at_points(p_hy, xy, freq_hz, slot_id=slot_id,
                                  signed=False,
                                  thickness_mm=copper_height_mm) / 1e6
        sq_hy += (amp / np.sqrt(2.0)) ** 2
        n += 1
        p_last, p_ms_last = p_ts, p_hy
    rms_ts = np.sqrt(sq_ts / n)
    rms_hy = np.sqrt(sq_hy / n)
    print('블록 %d개 누적 완료' % n)

    f_ts = _slot_frame(p_last, slot_id, airgap_side)
    geom = slot_reference_geometry(p_last, slot_id, airgap_side,
                                   p_outline=p_ms_last)
    vlim = float(np.percentile(np.concatenate([rms_ts, rms_hy]),
                               vlim_percentile))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(_COLW_IN, 2.6),
                                  layout='constrained')
    kw = {'cmap': 'plasma', 'vmin': 0.0,
          'outline': geom['outline'], 'extent': geom['extent']}
    cf = _draw_slot_contour(ax1, f_ts, rms_ts, vlim, **kw)
    _draw_slot_contour(ax2, f_ts, rms_hy, vlim, **kw)
    if show_titles:
        ax1.set_xlabel('(a)', fontsize=9)
        ax2.set_xlabel('(b)', fontsize=9)
    cb = fig.colorbar(cf, ax=(ax1, ax2), shrink=0.85)
    cb.set_label(r'$J_{e,\mathrm{rms}}$ [A/mm$^2$]', fontsize=9)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    print('RMS 그림 저장:', out_path)

    # 층별 지표 (쏠림 기울기 근거)
    reg = p_last['reg'][f_ts['mask']]
    r = np.hypot(p_last['x_mm'][f_ts['mask']], p_last['y_mm'][f_ts['mask']])
    order = sorted(np.unique(reg), key=lambda c: r[reg == c].mean())
    layers = [{'region': p_last['names'].get(int(c), str(c)),
               'r_mean_mm': float(r[reg == c].mean()),
               'ts_rms_A_mm2': float(rms_ts[reg == c].mean()),
               'hybrid_rms_A_mm2': float(rms_hy[reg == c].mean())}
              for c in order]
    grad_ts = layers[0]['ts_rms_A_mm2'] / layers[-1]['ts_rms_A_mm2']
    grad_hy = layers[0]['hybrid_rms_A_mm2'] / layers[-1]['hybrid_rms_A_mm2']
    summary = {
        'slot_id': slot_id, 'n_blocks': n, 'freq_hz': freq_hz,
        'quantity': 'cycle RMS (TS instantaneous RMS; reconstruction'
                    ' amplitude/sqrt(2) RMS) -- same definition both panels',
        'copper_height_mm': copper_height_mm,
        'vlim_A_mm2': vlim, 'per_layer': layers,
        'crowding_gradient_airgap_over_slotbottom': {
            'ts_fea': grad_ts, 'hybrid_reference': grad_hy},
        'loss_proxy_ratio_ts_over_hybrid':
            float((rms_ts ** 2).sum() / (rms_hy ** 2).sum()),
    }
    print('쏠림 기울기  TS %.3f  vs  재구성 %.3f' % (grad_ts, grad_hy))
    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)),
                   exist_ok=True)
        with open(out_json, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=1)
        print('RMS 요약 JSON 저장:', out_json)
    return summary


def _draw_bar_grids(ax, frame, grids, vlim, cmap='plasma',
                    outline=None, extent=None, show_airgap_label=True):
    """막대별 구조격자(2-D 해)를 슬롯 프레임 위에 pcolormesh 로 얹는다.

    2-D 해는 TS-FEA 메시가 아니라 막대마다의 (nx, ny) 격자 위에 있으므로
    삼각등고선 대신 격자별로 그린다. ``grids`` 는
    ``[(x_mm, y_mm, values), ...]`` (전역 좌표).
    """
    R = frame['R']
    im = None
    for gx, gy, gv in grids:
        pr = np.column_stack([gx.ravel(), gy.ravel()]) @ R.T
        X = pr[:, 0].reshape(gx.shape)
        Y = pr[:, 1].reshape(gx.shape)
        im = ax.pcolormesh(X, Y, gv, cmap=cmap, vmin=0.0, vmax=vlim,
                           shading='gouraud')
    if outline is not None and len(outline):
        from matplotlib.collections import LineCollection
        ax.add_collection(LineCollection(outline, colors='0.25',
                                         linewidths=0.6, zorder=5))
    x0, x1v, y0, y1v = extent if extent is not None else frame['bbox']
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    side = frame['airgap_side']
    pad_main, pad_arrow = 0.10 * (x1v - x0), 0.085 * (y1v - y0)
    ax.set_xlim(x0 - pad_main, x1v + pad_main)
    ax.set_ylim(y0 - pad_arrow if side == 'bottom' else y0,
                y1v + pad_arrow if side == 'top' else y1v)
    if show_airgap_label and side == 'bottom':
        # 화살표만 --- 하단 (a)/(b) 라벨과 겹치지 않게, 방향은 캡션에서
        cx = 0.5 * (x0 + x1v)
        scale = 0.055 * max(x1v - x0, y1v - y0)
        ax.annotate('', xy=(cx, y0 - scale), xytext=(cx, y0),
                    arrowprops={'arrowstyle': '-|>', 'lw': 1.0,
                                'color': 'black',
                                'shrinkA': 0, 'shrinkB': 0})
    return im


def plot_fig2_kernel_comparison(ts_path: str, hybrid_path: str,
                                out_path: str, slot_id: int = 1,
                                freq_hz: float = 1066.67,
                                airgap_side: str = 'bottom',
                                every: int = 4,
                                copper_w_mm: float = 3.711,
                                copper_h_mm: float = 1.686,
                                n_strips: int = 20,
                                vlim_percentile: float = 98.0,
                                panels: Sequence[str] = ('ts', '1d',
                                                         'strips', '2d'),
                                out_json: Optional[str] = None) -> dict:
    """커널 차원수 비교 3-패널: TS-FEA / 1-D 재구성 / 2-D 재구성 (주기 RMS).

    (b)와 (c)는 **같은 MS-FEA 여기**를 쓰고 커널 차원수만 다르다 ---
    (b)는 반경 방향 1-D 닫힌형, (c)는 막대 단면 2-D 확산 수치해
    (``conductor_je_2d``). 크기 격차가 여기 자계 탓인지 커널 탓인지를
    눈으로 가르는 것이 목적이다.
    """
    from .field_metrics import (iter_mes_blocks, slot_conductor_codes,
                                hybrid_je_at_points, conductor_je_2d,
                                conductor_je_strips, slot_mean_angle,
                                slot_bar_geometry)

    plt = _journal_rc()
    print('커널 비교 누적 중 (매 %d블록) ...' % every)
    sq_ts = sq_1d = None
    sq_st, sq_2d, gxy = {}, {}, {}
    n = 0
    p_last = p_ms_last = None
    for (bi, p_ts), (_, p_ms) in zip(iter_mes_blocks(ts_path),
                                     iter_mes_blocks(hybrid_path)):
        if (bi - 1) % every:
            continue
        m = np.isin(p_ts['reg'], list(slot_conductor_codes(p_ts, slot_id)))
        if sq_ts is None:
            sq_ts = np.zeros(int(m.sum()))
            sq_1d = np.zeros(int(m.sum()))
        xy = np.column_stack([p_ts['x_mm'][m], p_ts['y_mm'][m]])
        sq_ts += (p_ts['je_am2'][m] / 1e6) ** 2
        amp = hybrid_je_at_points(p_ms, xy, freq_hz, slot_id=slot_id,
                                  signed=False,
                                  thickness_mm=copper_h_mm) / 1e6
        sq_1d += (amp / np.sqrt(2.0)) ** 2
        # 기하 기준은 TS-FEA (순수 구리). MS-FEA 영역은 함침 포함이라
        # 25% 크므로 그대로 쓰면 (a) 패널과 도체 영역이 어긋난다.
        a_slot = slot_mean_angle(p_ts, slot_id)
        bars = slot_bar_geometry(p_ts, slot_id, angle_rad=a_slot)
        ms_codes = sorted(slot_conductor_codes(p_ms, slot_id),
                          key=lambda c: np.hypot(
                              p_ms['x_mm'][p_ms['reg'] == c],
                              p_ms['y_mm'][p_ms['reg'] == c]).mean())
        for bar, code in zip(bars, ms_codes):
            ctr = (bar['r_c'], bar['t_c'])
            rs = conductor_je_strips(p_ms, code, freq_hz, bar['w_mm'],
                                     bar['h_mm'], n_strips=n_strips,
                                     angle_rad=a_slot, center_rt=ctr)
            sq_st[code] = sq_st.get(code, 0.0) + (
                np.abs(rs['je']) / np.sqrt(2.0) / 1e6) ** 2
            r2 = conductor_je_2d(p_ms, code, freq_hz, bar['w_mm'],
                                 bar['h_mm'], angle_rad=a_slot,
                                 center_rt=ctr)
            sq_2d[code] = sq_2d.get(code, 0.0) + (
                np.abs(r2['je']) / np.sqrt(2.0) / 1e6) ** 2
            gxy[code] = ((rs['x_mm'], rs['y_mm']),
                         (r2['x_mm'], r2['y_mm']))
        n += 1
        p_last, p_ms_last = p_ts, p_ms
    rms_ts = np.sqrt(sq_ts / n)
    rms_1d = np.sqrt(sq_1d / n)
    g_st = [(gxy[c][0][0], gxy[c][0][1], np.sqrt(sq_st[c] / n))
            for c in sq_st]
    g_2d = [(gxy[c][1][0], gxy[c][1][1], np.sqrt(sq_2d[c] / n))
            for c in sq_2d]
    print('블록 %d개 누적 완료' % n)

    f_ts = _slot_frame(p_last, slot_id, airgap_side)
    geom = slot_reference_geometry(p_last, slot_id, airgap_side,
                                   p_outline=p_ms_last)
    allv = np.concatenate([rms_ts, rms_1d]
                          + [g[2].ravel() for g in g_st]
                          + [g[2].ravel() for g in g_2d])
    vlim = float(np.percentile(allv, vlim_percentile))

    npan = len(panels)
    wide = _COLW_IN * (1.05 if npan <= 2 else 2.1)
    fig, axs = plt.subplots(1, npan, figsize=(wide, 2.7),
                            layout='constrained')
    axs = np.atleast_1d(axs)
    kw = {'cmap': 'plasma', 'vmin': 0.0,
          'outline': geom['outline'], 'extent': geom['extent']}
    cf = None
    for ax, key in zip(axs, panels):
        if key == 'ts':
            cf = _draw_slot_contour(ax, f_ts, rms_ts, vlim, **kw)
        elif key == '1d':
            c2 = _draw_slot_contour(ax, f_ts, rms_1d, vlim, **kw)
            cf = cf or c2
        else:
            _draw_bar_grids(ax, f_ts, g_st if key == 'strips' else g_2d,
                            vlim, cmap='plasma', outline=geom['outline'],
                            extent=geom['extent'])
    if cf is None:                       # 등고선 패널이 없으면 스칼라맵 생성
        cf = axs[0].tricontourf(f_ts['triang'],
                                np.zeros(f_ts['triang'].x.size),
                                levels=np.linspace(0, vlim, 21),
                                cmap='plasma')
    for ax, lab in zip(axs, '(a) (b) (c) (d)'.split()):
        ax.set_xlabel(lab, fontsize=9)
    cb = fig.colorbar(cf, ax=list(axs), shrink=0.85)
    cb.set_label(r'$J_{e,\mathrm{rms}}$ [A/mm$^2$]', fontsize=9)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    print('커널 비교 그림 저장:', out_path)

    def gsum(gs):
        return float(sum((g[2] ** 2).mean() * g[2].size for g in gs))

    summary = {
        'slot_id': slot_id, 'n_blocks': n, 'every': every,
        'freq_hz': freq_hz, 'vlim_A_mm2': vlim, 'n_strips': n_strips,
        'panels': {'a': 'TS-FEA', 'b': '1-D, 2-point boundary',
                   'c': '1-D, %d strips (Motor-CAD style)' % n_strips,
                   'd': '2-D'},
        'mean_sq_A_mm2': {
            'ts_fea': float((rms_ts ** 2).mean()),
            'kernel_1d_2pt': float((rms_1d ** 2).mean()),
            'kernel_1d_strips': float(np.mean(
                [(g[2] ** 2).mean() for g in g_st])),
            'kernel_2d': float(np.mean(
                [(g[2] ** 2).mean() for g in g_2d]))},
    }
    r = summary['mean_sq_A_mm2']
    print('평균제곱 비 (TS 기준):  1-D 2pt %.2f   1-D strips %.2f   2-D %.2f'
          % (r['ts_fea'] / r['kernel_1d_2pt'],
             r['ts_fea'] / r['kernel_1d_strips'],
             r['ts_fea'] / r['kernel_2d']))
    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)),
                   exist_ok=True)
        with open(out_json, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=1)
    return summary


def make_fig2_kernel_gif(ts_path: str, hybrid_path: str, out_gif: str,
                         slot_id: int = 1, freq_hz: float = 1066.67,
                         airgap_side: str = 'bottom', every: int = 2,
                         copper_w_mm: float = 3.711,
                         copper_h_mm: float = 1.686,
                         n_strips: int = 20, fps: int = 8,
                         panels: Sequence[str] = ('ts', '1d',
                                                  'strips', '2d')) -> dict:
    """커널 비교 3-패널의 주기 애니메이션 (순시 크기 기준)."""
    from .field_metrics import (iter_mes_blocks, slot_conductor_codes,
                                hybrid_je_at_points, conductor_je_2d,
                                conductor_je_strips, slot_mean_angle,
                                slot_bar_geometry)
    from matplotlib.animation import PillowWriter

    plt = _journal_rc()
    print('커널 비교 GIF 프레임 수집 중 (매 %d블록) ...' % every)
    frames = []
    for (bi, p_ts), (_, p_ms) in zip(iter_mes_blocks(ts_path),
                                     iter_mes_blocks(hybrid_path)):
        if (bi - 1) % every:
            continue
        f_ts = _slot_frame(p_ts, slot_id, airgap_side)
        geom = slot_reference_geometry(p_ts, slot_id, airgap_side,
                                       p_outline=p_ms)
        m = f_ts['mask']
        xy = np.column_stack([p_ts['x_mm'][m], p_ts['y_mm'][m]])
        je_ts = np.abs(p_ts['je_am2'][m]) / 1e6
        je_1d = hybrid_je_at_points(p_ms, xy, freq_hz, slot_id=slot_id,
                                    signed=False,
                                    thickness_mm=copper_h_mm) / 1e6
        g_st, g_2d = [], []
        a_slot = slot_mean_angle(p_ts, slot_id)
        bars = slot_bar_geometry(p_ts, slot_id, angle_rad=a_slot)
        ms_codes = sorted(slot_conductor_codes(p_ms, slot_id),
                          key=lambda c: np.hypot(
                              p_ms['x_mm'][p_ms['reg'] == c],
                              p_ms['y_mm'][p_ms['reg'] == c]).mean())
        for bar, code in zip(bars, ms_codes):
            ctr = (bar['r_c'], bar['t_c'])
            rs = conductor_je_strips(p_ms, code, freq_hz, bar['w_mm'],
                                     bar['h_mm'], n_strips=n_strips,
                                     angle_rad=a_slot, center_rt=ctr)
            g_st.append((rs['x_mm'], rs['y_mm'], np.abs(rs['je']) / 1e6))
            r2 = conductor_je_2d(p_ms, code, freq_hz, bar['w_mm'],
                                 bar['h_mm'], angle_rad=a_slot,
                                 center_rt=ctr)
            g_2d.append((r2['x_mm'], r2['y_mm'], np.abs(r2['je']) / 1e6))
        frames.append({'frame': f_ts, 'geom': geom, 'ts': je_ts,
                       'd1': je_1d, 'dst': g_st, 'd2': g_2d,
                       'rotate_deg': p_ts['rotate_deg']})
    n = len(frames)
    print('프레임 %d개' % n)
    allv = np.concatenate([f['ts'] for f in frames]
                          + [f['d1'] for f in frames]
                          + [g[2].ravel() for f in frames
                             for g in f['dst']]
                          + [g[2].ravel() for f in frames
                             for g in f['d2']])
    vlim = float(np.percentile(allv, 99.0))

    npan = len(panels)
    wide = _COLW_IN * (1.05 if npan <= 2 else 2.1)
    fig, axs = plt.subplots(1, npan, figsize=(wide, 2.7),
                            layout='constrained')
    axs = np.atleast_1d(axs)
    kw0 = {'cmap': 'plasma', 'vmin': 0.0,
           'outline': frames[0]['geom']['outline'],
           'extent': frames[0]['geom']['extent']}
    cf = _draw_slot_contour(axs[0], frames[0]['frame'], frames[0]['ts'],
                            vlim, **kw0)
    for ax in axs:
        ax.clear()
    cb = fig.colorbar(cf, ax=list(axs), shrink=0.85)
    cb.set_label(r'$|J_e|$ [A/mm$^2$]', fontsize=9)
    suptitle = fig.suptitle('', fontsize=8)

    def update(i):
        rec = frames[i]
        kw = {'cmap': 'plasma', 'vmin': 0.0,
              'outline': rec['geom']['outline'],
              'extent': rec['geom']['extent']}
        for ax in axs:
            ax.clear()
        _draw_slot_contour(axs[0], rec['frame'], rec['ts'], vlim, **kw)
        lut = {'ts': rec['ts'], '1d': rec['d1'],
               'strips': rec['dst'], '2d': rec['d2']}
        names = {'ts': 'TS-FEA', '1d': '1-D 2pt',
                 'strips': '1-D strips', '2d': '2-D'}
        for ax, key in zip(axs, panels):
            if key in ('ts', '1d'):
                _draw_slot_contour(ax, rec['frame'], lut[key], vlim, **kw)
            else:
                _draw_bar_grids(ax, rec['frame'], lut[key], vlim,
                                cmap='plasma',
                                outline=rec['geom']['outline'],
                                extent=rec['geom']['extent'])
        for ax, lab in zip(axs, ['(%s) %s' % (c, names[k]) for c, k
                                 in zip('abcd', panels)]):
            ax.set_xlabel(lab, fontsize=9)
        suptitle.set_text('slot %d   frame %d/%d   rotate %.2f deg'
                          % (slot_id, i + 1, n, rec['rotate_deg']))

    os.makedirs(os.path.dirname(os.path.abspath(out_gif)), exist_ok=True)
    writer = PillowWriter(fps=fps)
    with writer.saving(fig, out_gif, dpi=110):
        for i in range(n):
            update(i)
            writer.grab_frame()
    plt.close(fig)
    print('커널 비교 GIF 저장:', out_gif)
    return {'slot_id': slot_id, 'n_frames': n, 'vlim_A_mm2': vlim,
            'every': every}


def plot_kernel_sampling_map(hybrid_path: str, out_path: str,
                             ts_path: Optional[str] = None,
                             slot_id: int = 1, step: int = 70,
                             airgap_side: str = 'bottom',
                             copper_w_mm: float = 3.711,
                             copper_h_mm: float = 1.686,
                             n_strips: int = 20,
                             face_frac: float = 0.2,
                             nx: int = 40, ny: int = 26) -> dict:
    """세 커널이 **B 를 어디서 뽑는지** 를 그림으로 보여준다 (진단용).

    (a) ``hybrid_je_at_points`` --- 막대당 안/바깥 반경면의 얇은 띠
        (두께의 ``face_frac``) 요소들을 평균해 **경계 2점**을 만든다.
        띠에 든 요소는 옅게, 그 평균 위치는 진한 마커로 표시한다.
    (b) ``conductor_je_strips`` --- 접선 방향 ``n_strips`` 개 스트립마다
        안/바깥 두 점을 보간해 뽑는다 (막대당 2*N 점).
    (c) ``conductor_je_2d`` --- 격자 **둘레 전체**에 벡터 퍼텐셜을 준다
        (네 면 모두 --- 좌/우 접선면 포함).

    (a)->(b) 는 샘플링 밀도의 차이, (b)->(c) 는 커널 차원수의 차이를
    가른다. 왜 (c)만 B 의 반경 성분을 쓸 수 있는지도 이 그림에서 보인다.
    """
    from .field_metrics import (parse_mes_txt, slot_conductor_codes,
                                _conductor_layers, slot_mean_angle,
                                slot_bar_geometry)

    plt = _journal_rc()
    p = parse_mes_txt(hybrid_path, block=step)
    # 기하 기준은 TS-FEA(순수 구리). 없으면 MS-FEA 자체 영역으로 폴백.
    p_geom = parse_mes_txt(ts_path, block=step) if ts_path else p
    f = _slot_frame(p_geom, slot_id, airgap_side, domain='slot')
    R = f['R']
    geom = slot_reference_geometry(p_geom, slot_id, airgap_side,
                                   p_outline=p)
    a_slot = slot_mean_angle(p_geom, slot_id)
    bars = slot_bar_geometry(p_geom, slot_id, angle_rad=a_slot)
    codes = sorted(slot_conductor_codes(p_geom, slot_id),
                   key=lambda c: np.hypot(
                       p_geom['x_mm'][p_geom['reg'] == c],
                       p_geom['y_mm'][p_geom['reg'] == c]).mean())
    layers = _conductor_layers(p_geom, codes, 4e-7 * np.pi,
                               face_frac=face_frac)
    r_all = np.hypot(p_geom['x_mm'], p_geom['y_mm'])
    p = p_geom

    fig, axs = plt.subplots(1, 3, figsize=(_COLW_IN * 2.0, 3.0),
                            layout='constrained')
    counts = {}
    for ax in axs:
        from matplotlib.collections import LineCollection
        ax.add_collection(LineCollection(geom['outline'], colors='0.55',
                                         linewidths=0.6))

    def to_local(gx, gy):
        pr = np.column_stack([np.ravel(gx), np.ravel(gy)]) @ R.T
        return pr[:, 0], pr[:, 1]

    # ---- (a) 막대당 경계 2점 (얇은 띠 평균) ----
    n_a = 0
    for lay in layers:
        m = p['reg'] == lay['code']
        rr = r_all[m]
        span = lay['r_hi'] - lay['r_lo']
        for sel, col in ((rr <= lay['r_lo'] + face_frac * span, '#1f77b4'),
                         (rr >= lay['r_hi'] - face_frac * span, '#d62728')):
            gx, gy = p['x_mm'][m][sel], p['y_mm'][m][sel]
            lx, ly = to_local(gx, gy)
            axs[0].plot(lx, ly, '.', ms=1.2, color=col, alpha=0.45)
            axs[0].plot(lx.mean(), ly.mean(), 'o', ms=3.5, color=col,
                        mec='k', mew=0.4)
            n_a += 1

    # ---- (b) 스트립별 2점 ----
    n_b = 0
    cb_, sb_ = np.cos(-a_slot), np.sin(-a_slot)
    Rb = np.array([[cb_, -sb_], [sb_, cb_]])
    for bar in bars:
        tt = np.linspace(-bar['w_mm'] / 2, bar['w_mm'] / 2,
                         n_strips) + bar['t_c']
        for sgn, col in ((-1, '#1f77b4'), (+1, '#d62728')):
            q = np.column_stack([np.full(n_strips,
                                         bar['r_c']
                                         + sgn * bar['h_mm'] / 2),
                                 tt]) @ Rb
            lx, ly = to_local(q[:, 0], q[:, 1])
            axs[1].plot(lx, ly, '.', ms=2.2, color=col)
            n_b += n_strips

    # ---- (c) 격자 둘레 전체 ----
    n_c = 0
    for bar in bars:
        r_c, t_c = bar['r_c'], bar['t_c']
        rr_off = np.linspace(-bar['h_mm'] / 2, bar['h_mm'] / 2, ny)
        tt_off = np.linspace(-bar['w_mm'] / 2, bar['w_mm'] / 2, nx) + t_c
        RR, TT = np.meshgrid(rr_off, tt_off, indexing='ij')
        edge = np.zeros(RR.shape, bool)
        edge[0, :] = edge[-1, :] = True
        edge[:, 0] = edge[:, -1] = True
        q = np.column_stack([(RR[edge] + r_c).ravel(),
                             TT[edge].ravel()]) @ Rb
        lx, ly = to_local(q[:, 0], q[:, 1])
        # 반경면(파랑/빨강)과 접선면(초록)을 구분해 칠한다
        radial_face = np.zeros(RR.shape, bool)
        radial_face[0, :] = radial_face[-1, :] = True
        tang_face = edge & ~radial_face
        for msk, col in ((radial_face, '#1f77b4'), (tang_face, '#2ca02c')):
            qq = np.column_stack([(RR[msk] + r_c).ravel(),
                                  TT[msk].ravel()]) @ Rb
            ux, uy = to_local(qq[:, 0], qq[:, 1])
            axs[2].plot(ux, uy, '.', ms=1.8, color=col)
        n_c += int(edge.sum())

    counts = {'a_2point': n_a, 'b_strips': n_b, 'c_perimeter': n_c}
    titles = ('(a) 2-point / bar\n(%d pts)' % n_a,
              '(b) %d strips / bar\n(%d pts)' % (n_strips, n_b),
              '(c) full perimeter\n(%d pts)' % n_c)
    x0, x1v, y0, y1v = geom['extent']
    for ax, t in zip(axs, titles):
        ax.set_title(t, fontsize=8)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        pad = 0.12 * (x1v - x0)
        ax.set_xlim(x0 - pad, x1v + pad)
        ax.set_ylim(y0 - pad, y1v + pad)
    fig.suptitle('boundary sampling used by each kernel'
                 '   (blue/red = radial faces, green = tangential faces)',
                 fontsize=7.5)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    print('샘플링 위치 그림 저장:', out_path)
    return counts


def _slot_b_panel(p: dict, slot_id: int, airgap_side: str):
    """슬롯 내부 전체 메시 프레임과 그 위의 |B| 를 함께 만든다."""
    frame = _slot_frame(p, slot_id, airgap_side, domain='slot')
    m = frame['mask']
    b_mag = np.hypot(p['bx'][m], p['by'][m])
    return frame, b_mag


def plot_fig_b_slot_comparison(ts_path: str, hybrid_path: str,
                               out_path: str, slot_id: int = 1,
                               step: int = 70,
                               airgap_side: str = 'bottom',
                               show_titles: bool = True) -> dict:
    """슬롯 내부 전체 메시 위의 |B| 비교 (TS-FEA vs MS-FEA/Hybrid, 정적).

    Je 그림(``plot_fig2_slot_comparison``)과 두 가지가 다르다:

    1. **도메인이 도체가 아니라 슬롯 내부 전체**(도체 + 함침 + 웨지 +
       슬롯 공기, 철심 제외)다 --- B 는 도체 밖에도 존재하기 때문이다.
    2. **각 패널이 자기 데이터셋의 메시를 쓴다.** Je 는 Hybrid 에 실측값이
       없어 TS-FEA 메시 위에 재구성해 얹었지만, B 는 두 해석 모두 자기
       메시에서 실제로 푼 값이라 그대로 그리는 편이 정직하다 --- 덤으로
       MS-FEA 슬롯 모델이 함침 영역 없이 이상화돼 있다는 점도 드러난다.

    색상 스케일은 두 패널 공통(0..max)이다.
    """
    from .field_metrics import parse_mes_txt

    plt = _journal_rc()
    p_ts = parse_mes_txt(ts_path, block=step)
    p_hy = parse_mes_txt(hybrid_path, block=step)

    f_ts, b_ts = _slot_b_panel(p_ts, slot_id, airgap_side)
    f_hy, b_hy = _slot_b_panel(p_hy, slot_id, airgap_side)
    vmax = float(max(b_ts.max(), b_hy.max()))

    # Je 그림과 같은 축척·외곽선 (같은 슬롯임이 보이도록)
    geom = slot_reference_geometry(p_ts, slot_id, airgap_side,
                                   p_outline=p_hy)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(_COLW_IN, 2.6),
                                  layout='constrained')
    kw = {'cmap': 'viridis', 'vmin': 0.0,
          'outline': geom['outline'], 'extent': geom['extent']}
    cf = _draw_slot_contour(ax1, f_ts, b_ts, vmax, **kw)
    _draw_slot_contour(ax2, f_hy, b_hy, vmax, **kw)
    if show_titles:
        ax1.set_xlabel('(a)', fontsize=9)
        ax2.set_xlabel('(b)', fontsize=9)
    cb = fig.colorbar(cf, ax=(ax1, ax2), shrink=0.85)
    cb.set_label(r'$|B|$ [T]', fontsize=9)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    print('B 정적 그림 저장:', out_path)

    def pack(p, frame, b):
        m = frame['mask']
        return {'x_mm': p['x_mm'][m].tolist(),
                'y_mm': p['y_mm'][m].tolist(),
                'b_mag_T': b.tolist(),
                'n_elements': int(m.sum())}

    return {
        'slot_id': slot_id, 'step': step, 'airgap_side': airgap_side,
        'vmax_T': vmax, 'rotate_deg': p_ts.get('rotate_deg'),
        'domain': 'slot interior (conductors + impregnation + wedge + air),'
                  ' each panel on its own mesh',
        'ts_fea': pack(p_ts, f_ts, b_ts),
        'ms_fea_hybrid': pack(p_hy, f_hy, b_hy),
    }


def make_fig_b_slot_gif(ts_path: str, hybrid_path: str, out_gif: str,
                        slot_id: int = 1, airgap_side: str = 'bottom',
                        fps: int = 10,
                        out_json: Optional[str] = None) -> dict:
    """슬롯 내부 전체 메시 |B| 의 128스텝 동기 애니메이션.

    ``plot_fig_b_slot_comparison`` 과 같은 도메인·관례를 쓰되 전 주기를
    훑는다. 색상 스케일은 전 스텝 공통(99.5th percentile)으로 고정한다.
    """
    from .field_metrics import iter_mes_blocks
    from matplotlib.animation import PillowWriter

    plt = _journal_rc()
    print('TS-FEA/MS-FEA |B| 동기 파싱 중 ...')
    frames = []
    for (_, p_ts), (_, p_hy) in zip(iter_mes_blocks(ts_path),
                                    iter_mes_blocks(hybrid_path)):
        f_ts, b_ts = _slot_b_panel(p_ts, slot_id, airgap_side)
        f_hy, b_hy = _slot_b_panel(p_hy, slot_id, airgap_side)
        geom = slot_reference_geometry(p_ts, slot_id, airgap_side,
                                       p_outline=p_hy)
        frames.append({'rotate_deg': p_ts['rotate_deg'],
                       'f_ts': f_ts, 'b_ts': b_ts,
                       'f_hy': f_hy, 'b_hy': b_hy, 'geom': geom})
    n = len(frames)
    print('동기화 프레임 %d개' % n)

    all_b = np.concatenate([f['b_ts'] for f in frames]
                           + [f['b_hy'] for f in frames])
    vmax = float(np.percentile(all_b, 99.5))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(_COLW_IN, 2.6),
                                  layout='constrained')

    def kw_of(rec):
        return {'cmap': 'viridis', 'vmin': 0.0,
                'outline': rec['geom']['outline'],
                'extent': rec['geom']['extent']}

    cf = _draw_slot_contour(ax1, frames[0]['f_ts'], frames[0]['b_ts'], vmax,
                            **kw_of(frames[0]))
    _draw_slot_contour(ax2, frames[0]['f_hy'], frames[0]['b_hy'], vmax,
                       **kw_of(frames[0]))
    ax1.set_title('TS-FEA', fontsize=9)
    ax2.set_title('MS-FEA (Hybrid)', fontsize=9)
    cb = fig.colorbar(cf, ax=(ax1, ax2), shrink=0.85)
    cb.set_label(r'$|B|$ [T]', fontsize=9)
    suptitle = fig.suptitle('', fontsize=8)

    step_max = []

    def update(i):
        rec = frames[i]
        ax1.clear()
        _draw_slot_contour(ax1, rec['f_ts'], rec['b_ts'], vmax, **kw_of(rec))
        ax2.clear()
        _draw_slot_contour(ax2, rec['f_hy'], rec['b_hy'], vmax, **kw_of(rec))
        ax1.set_xlabel('(a) TS-FEA', fontsize=9)
        ax2.set_xlabel('(b) MS-FEA (Hybrid)', fontsize=9)
        suptitle.set_text('slot %d   step %d/%d   rotate %.2f deg'
                          % (slot_id, i + 1, n, rec['rotate_deg']))
        step_max.append({
            'step': i + 1, 'rotate_deg': rec['rotate_deg'],
            'ts_fea_max_T': float(rec['b_ts'].max()),
            'ms_fea_max_T': float(rec['b_hy'].max()),
            'ts_fea_mean_T': float(rec['b_ts'].mean()),
            'ms_fea_mean_T': float(rec['b_hy'].mean()),
        })

    os.makedirs(os.path.dirname(os.path.abspath(out_gif)), exist_ok=True)
    writer = PillowWriter(fps=fps)
    with writer.saving(fig, out_gif, dpi=110):
        for i in range(n):
            update(i)
            writer.grab_frame()
    plt.close(fig)
    print('B GIF 저장:', out_gif)

    summary = {'slot_id': slot_id, 'airgap_side': airgap_side,
              'n_frames': n, 'vmax_T': vmax,
              'domain': 'slot interior, each panel on its own mesh',
              'per_step': step_max}
    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)),
                   exist_ok=True)
        with open(out_json, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=1)
        print('B 요약 JSON 저장:', out_json)
    return summary
