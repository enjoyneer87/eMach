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
    k_r: Optional[Sequence[float]] = None,
    show_axes: bool = True,
    compact_labels: bool = False,
    group_labels: Optional[Sequence[str]] = None,
    tick_step: Optional[Sequence[float]] = None,
    tag_pos: str = 'top',
) -> str:
    """2xN journal figure from field .npz files.

    cases : sequence of (npz_path, panel_title), N columns.
    Row 1 = |B| on one shared scale; row 2 = MVP A (diverging). With
    ``share_a_pairs`` adjacent column pairs share the A scale (useful for
    Hybrid-vs-FullFEA pairs of the same model).
    Saving to .pdf keeps text vector and rasterizes the point clouds at
    ``raster_dpi``.

    k_r : per-column radial scale factor. When given, row 2 plots
        ``A / k_r`` on a **single shared** diverging scale instead of
        per-pair scales. Because SCL-M predicts ``A -> k_a k_r A``, the
        normalised panels must look identical across models — the figure
        then *shows* the scaling law rather than asking the reader to
        compare two colourbar ranges (seminar-2: "Ref/SC 구분이 어렵다").
    show_axes : draw the mm axis box with ticks. The stored coordinates are
        already in mm, and the tick box also conveys the k_r size ratio
        directly (seminar-2 / journal reviewer: "add x-y dimensions").
    tick_step : per-column tick interval in mm for both axes. Without it
        matplotlib picks per-panel steps and the models end up with
        different grids (Ref every 20 mm, SC every 50 mm) — seminar-6
        asked for one rule across the models.
    tag_pos : ``'top'`` keeps the ``(a)`` tags as panel titles, ``'bottom'``
        moves them under each panel (seminar-6, author preference).
    compact_labels : 그림 내부 텍스트 최소화 규칙(2026-07-26) — 열 제목은
        상단 행 한 줄만, 하단 행은 (e)~(h) 태그만, 행 식별($|B|$,
        MVP $A/k_r$)은 최좌측에 1회(회전 라벨). 절약된 공간만큼 패널이
        커진다. 모델 식별은 ``group_labels`` 그룹 헤더가 담당.
    group_labels : k_r 그룹 헤더 텍스트(그룹당 1개, 예: ["Ref", "SC"]).
        미지정 시 패널 제목의 공통 접두어를 사용(기존 동작).
    """
    plt = _journal_rc()
    D = [(np.load(p), t) for p, t in cases]
    n = len(D)
    if k_r is not None and len(k_r) != n:
        raise ValueError(f"k_r must have one entry per case (got {len(k_r)} for {n})")

    b_max = max(np.percentile(d['b_T'], 99.5) for d, _ in D)

    # row-2 values: raw A, or A/k_r on a single common scale
    a_vals = [d['a_Wbm'] if k_r is None else d['a_Wbm'] / float(k_r[i])
              for i, (d, _) in enumerate(D)]
    if k_r is None:
        a_lim = [np.percentile(np.abs(v), 99.5) for v in a_vals]
        if share_a_pairs:
            for i in range(0, n - 1, 2):
                m = max(a_lim[i], a_lim[i + 1])
                a_lim[i] = a_lim[i + 1] = m
    else:
        m = max(np.percentile(np.abs(v), 99.5) for v in a_vals)
        a_lim = [m] * n

    fig, axes = plt.subplots(
        2, n, figsize=((2.05 if compact_labels else 1.9) * n,
                       3.35 if compact_labels else 4.4),
        layout='constrained')
    if n == 1:
        axes = axes.reshape(2, 1)

    h_b = None
    for col, (d, title) in enumerate(D):
        ax = axes[0, col]
        h_b = ax.scatter(d['x_mm'], d['y_mm'], c=d['b_T'], s=point_size,
                         marker='.', cmap='jet', vmin=0, vmax=b_max,
                         rasterized=True, linewidths=0)
        tag_top, tag_bot = f'({chr(97 + col)})', f'({chr(97 + n + col)})'
        if compact_labels:
            # 열 식별(기법명)은 tex 캡션이 담당 — 그림엔 태그만(중앙 정렬)
            if tag_pos != 'bottom':
                ax.set_title(tag_top, fontsize=9.8, pad=2)
        else:
            ax.set_title(f'({chr(97 + col)}) {title}\n$|B|$', fontsize=10.9)

        ax2 = axes[1, col]
        h_a = ax2.scatter(d['x_mm'], d['y_mm'], c=a_vals[col], s=point_size,
                          marker='.', cmap='RdBu_r',
                          vmin=-a_lim[col], vmax=a_lim[col],
                          rasterized=True, linewidths=0)
        a_title = 'MVP $A/k_r$' if k_r is not None else 'MVP $A$'
        if compact_labels:
            if tag_pos != 'bottom':
                ax2.set_title(tag_bot, fontsize=9.8, pad=2)
        else:
            ax2.set_title(f'({chr(97 + n + col)}) {title}\n{a_title}',
                          fontsize=10.9)
        if k_r is None:
            last_of_pair = (col % 2 == 1) if share_a_pairs else True
            if last_of_pair:
                lo = col - 1 if share_a_pairs else col
                cb = fig.colorbar(h_a, ax=list(axes[1, lo:col + 1]), shrink=0.8)
                cb.set_label('A [Wb/m]', fontsize=9.4)
                cb.ax.tick_params(labelsize=8.7)

        for a in (ax, ax2):
            a.set_aspect('equal')
            if show_axes:
                a.tick_params(labelsize=7.6, length=2.2, pad=1.5)
                for sp in a.spines.values():
                    sp.set_visible(True)
                if tick_step is not None:
                    from matplotlib.ticker import MultipleLocator
                    st = float(tick_step[col] if np.ndim(tick_step)
                               else tick_step)
                    a.xaxis.set_major_locator(MultipleLocator(st))
                    a.yaxis.set_major_locator(MultipleLocator(st))
            else:
                a.set_xticks([])
                a.set_yticks([])
        if show_axes and compact_labels:
            # 상단 행은 눈금 숫자 생략(하단 행과 동일 축) — 행 간격 절약
            ax.tick_params(labelbottom=False)
        if tag_pos == 'bottom' and compact_labels:
            # 태그를 패널 아래로 (저자 선호, 세미나 6). 상단 행은 눈금 숫자가
            # 없으므로 xlabel 자리가 비어 있고, 하단 행은 축 라벨 아래 줄에 둔다.
            ax.set_xlabel(tag_top, fontsize=9.8, labelpad=2)
        if show_axes:
            # 축 라벨은 좌측 열에만 — 반복 표기로 지면 낭비하지 않는다
            xlab = 'x [mm]'
            if tag_pos == 'bottom' and compact_labels:
                xlab = f'x [mm]\n{tag_bot}'
            axes[1, col].set_xlabel(xlab, fontsize=8.2, labelpad=1.5)
            if col == 0:
                # 행 물리량 식별은 우측 컬러바 라벨(+캡션)이 담당 — y[mm]만
                for r in (0, 1):
                    axes[r, 0].set_ylabel('y [mm]', fontsize=8.2,
                                          labelpad=1.5)

    cb = fig.colorbar(h_b, ax=list(axes[0, :]), shrink=0.8)
    cb.set_label('|B| [T]', fontsize=9.4)
    cb.ax.tick_params(labelsize=8.7)

    if k_r is not None:
        # 전 열 공통 스케일이므로 컬러바도 하나 — 색이 같다는 것 자체가 근거다
        cb = fig.colorbar(h_a, ax=list(axes[1, :]), shrink=0.8)
        cb.set_label(r'$A/k_r$ [Wb/m]', fontsize=9.4)
        cb.ax.tick_params(labelsize=8.7)

    # ── 상단 그룹 헤더: 같은 k_r 열을 모델 단위로 묶어 표시 ──
    # 세미나2 "좌4=KR1/우4=KR2 (상단 KR 라벨)". k_r 이 주어질 때만.
    need_layout = (k_r is not None and n >= 2) or compact_labels
    rnd = None
    if need_layout:
        fig.draw_without_rendering()
        try:
            rnd = fig.canvas.get_renderer()
        except Exception:
            rnd = None
    if k_r is not None and n >= 2:
        c, gi = 0, 0
        while c < n:
            c2 = c
            while c2 + 1 < n and float(k_r[c2 + 1]) == float(k_r[c]):
                c2 += 1
            pos = [axes[0, cc].get_position() for cc in range(c, c2 + 1)]
            xc = 0.5 * (pos[0].x0 + pos[-1].x1)
            if rnd is not None:
                ytop = max(axes[0, cc].title.get_window_extent(rnd).ymax
                           for cc in range(c, c2 + 1)) / fig.bbox.height
            else:
                ytop = max(p.y1 for p in pos) + 0.09
            if group_labels is not None and gi < len(group_labels):
                prefix = str(group_labels[gi])
            else:
                prefix = os.path.commonprefix(
                    [D[cc][1] for cc in range(c, c2 + 1)]).strip(' —-').strip()
            lbl = ((prefix + '  ') if prefix else '') \
                + f'($k_r{{=}}{float(k_r[c]):g}$)'
            fig.text(xc, min(ytop + 0.012, 0.998), lbl, ha='center',
                     va='bottom', fontsize=12, fontweight='bold')
            c = c2 + 1
            gi += 1

    # (compact 행 식별은 좌측 열 y라벨에 병합되어 별도 텍스트 불필요)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path, dpi=raster_dpi,
                bbox_inches='tight' if k_r is not None else None)
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
                          n_base_list=(8, 12, 16, 20, 24, 28),
                          n_spd_by_scale=None,
                          n_seeds: int = 10,
                          show_titles: bool = True,
                          placement: str = 'random',
                          adopted_by_scale=None) -> str:
    """Scalar vs exponent separable convergence: full-map wMAE vs n_base.

    Own-sampling protocol (16-kRPM base kernel + n_spd calibration points
    per non-base speed), multi-seed mean, log scale. The two curves share
    the identical sample placement, so their gap isolates the contribution
    of the spread exponent p(w). Degenerate low-count regressions are
    capped at 10^3 for display.

    Seminar-3: the swept grid is evenly spaced and the x ticks are exactly
    the evaluated counts (marker = actual run); the adopted base-kernel
    size (24 for all three) is starred on the exponent curve under the
    same own-sampling protocol.
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
    adopted_by = adopted_by_scale or {'Ref': 24, 'HalfSC': 24, 'SC': 24}
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

        def eval_wmae(nb, expo):
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
            return min(np.mean(vals), 1e3) if vals else np.nan

        for expo, sty in ((False, dict(color='#2e7d32', ls='--',
                                       marker='s',
                                       label=r'Scalar $f\cdot\kappa$')),
                          (True, dict(color='#e65100', ls='-',
                                      marker='o',
                                      label=r'Proposed $f\cdot\kappa^{p}$'))):
            ys = [eval_wmae(nb, expo) for nb in nbs]
            ax.plot(nbs, ys, lw=1.2, ms=4.2, **sty)

        # 채택 base-kernel 규모 별표 (동일 자체 샘플링 프로토콜의 지점 강조)
        nb_a = min(int(adopted_by.get(scale, nbs[-1])), pool)
        y_a = eval_wmae(nb_a, True)
        if np.isfinite(y_a):
            ax.plot([nb_a], [y_a], marker='*', ms=10, ls='none',
                    color='#e65100', mec='#4d2600', mew=0.5, zorder=5,
                    label=r'adopted $n_{base}$')
            if nb_a not in nbs:
                ax.annotate(f'{nb_a}', (nb_a, y_a), textcoords='offset points',
                            xytext=(0, 6), ha='center', fontsize=7.8,
                            color='#4d2600')
        ax.set_xticks(list(nbs))

        ax.axhline(hyb_w, color='#888888', ls=':', lw=0.9,
                   label='Hybrid, uncorrected')
        ax.axvline(pool, color='#2c6fad', ls=':', lw=0.9,
                   label=r'available $n_{base}$')
        ax.set_yscale('log')
        ax.set_xlabel(r'$n_{base}$ (16-kRPM base points)')
        if k == 0:
            ax.set_ylabel(r'wMAE [%] (log)')
            ax.legend(fontsize=7.5, loc='upper right', frameon=True,
                      framealpha=0.85, edgecolor='none',
                      handlelength=1.7, labelspacing=0.3, borderpad=0.3)
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

    # (a) d-axis flux linkage --- own panel so solid(SC)/dashed(scaled)
    # is the only distinction (no dark/light overlay to resolve in B&W).
    ax = axes[0]
    lv_d = np.round(np.linspace(np.nanmin(lam_d_c),
                                np.nanmax(lam_d_c), 8), 2)
    c1 = ax.contour(ID, IQ, lam_d_c, levels=lv_d, **kw_sc)
    ax.contour(ID, IQ, lam_d_s, levels=lv_d, **kw_s)
    ax.clabel(c1, fmt='%.2f', fontsize=8)
    ax.scatter(sc['Id_pk'], sc['Iq_pk'], s=4, c='#1a3a5c', marker='o',
               zorder=5, linewidths=0)
    ax.set_title(r'(a) $\lambda_d$ [Vs]', fontsize=10.9)

    # (b) q-axis flux linkage
    ax = axes[1]
    lv_q = np.round(np.linspace(np.nanmin(lam_q_c),
                                np.nanmax(lam_q_c), 8), 2)
    c1 = ax.contour(ID, IQ, lam_q_c, levels=lv_q, **kw_sc)
    ax.contour(ID, IQ, lam_q_s, levels=lv_q, **kw_s)
    ax.clabel(c1, fmt='%.2f', fontsize=8)
    ax.scatter(sc['Id_pk'], sc['Iq_pk'], s=4, c='#1a3a5c', marker='o',
               zorder=5, linewidths=0)
    ax.set_title(r'(b) $\lambda_q$ [Vs]', fontsize=10.9)

    # (c) electromagnetic torque (contours) over its deviation (color):
    # the two torque surfaces coincide (lines overlap) while the color
    # shows the residual --- torque agreement and its error in one panel.
    ax = axes[2]
    pm = ax.pcolormesh(ID, IQ, err_t, cmap='YlOrRd', vmin=0,
                       vmax=max(1.0, np.nanpercentile(err_t, 99.5)),
                       shading='auto', zorder=0)
    cb = fig.colorbar(pm, ax=ax, shrink=0.85)
    cb.set_label(r'$|\Delta T_{em}| / T_{em,max}$ [%]', fontsize=9.0)
    cb.ax.tick_params(labelsize=8.7)
    lv_t = np.linspace(200, np.nanmax(t_c), 8)
    c1 = ax.contour(ID, IQ, t_c, levels=lv_t, colors='#08306b',
                    linewidths=0.9, linestyles='solid', zorder=3)
    ax.contour(ID, IQ, t_s, levels=lv_t, colors='#08306b',
               linewidths=0.9, linestyles='dashed', zorder=3)
    ax.clabel(c1, fmt='%.0f', fontsize=7.5)
    ax.set_title(r"(c) $T_{em}$ [Nm] & deviation", fontsize=10.9)

    # 범례는 등고선 위에 얹히므로 흰 배경을 준다. (TPS) 는 뺀다 — 캡션이
    # "same TPS reconstruction" 을 이미 말하고 TPS 는 4.2 절에서 정의된다.
    # 두 계열 모두 SC 를 가리킨다 — 하나는 직접 푼 것, 하나는 Ref 를 스케일해
    # 얻은 것. 'Ref, scaled' 는 그것이 SC 가 된다는 말을 하지 않으므로 둘 다
    # SC 로 시작하게 쓴다 (저자 지시 2026-08-22).
    from matplotlib.lines import Line2D
    axes[0].legend(handles=[
        Line2D([], [], color='#1a3a5c', lw=0.9,
               label='SC, MS-FEA sweep'),
        Line2D([], [], color='#e65100', lw=0.9, ls='--',
               label='SC, scaled from Ref')],
        fontsize=8, loc='upper left',
        frameon=True, facecolor='white', framealpha=0.85,
        edgecolor='#cccccc', borderpad=0.35, handlelength=1.7,
        handletextpad=0.5, labelspacing=0.3)
    for ax in axes:
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('$i_d$ [A, pk]')
    for ax in (axes[0], axes[1]):
        ax.grid(True, ls=':', lw=0.4, color='#dddddd')
        ax.set_axisbelow(True)
    axes[0].set_ylabel('$i_q$ [A, pk]')

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return metrics


def plot_eddy_factors(out_path: str, h_c_ref_mm: float = 3.711,
                      k_r: float = 2.0, pole_pairs: int = 4,
                      speed_max_rpm: float = 20000.0,
                      sigma: float = 1.0 / 1.724e-8) -> dict:
    """Appendix Fig.: dimensionless skin/proximity resistance factors vs speed.

    Rebuilt on the manuscript convention ``eta = h_c/delta`` (eq:g_kernel),
    replacing the legacy porosity argument ``xi = (h_c/delta) sqrt(b_c/b)`` so
    the figure supports the body claim that hairpins sit in the transition
    regime ``eta ~ 2--4``.  Two panels share the layout: left axis = resistance
    factor ``F(eta)`` for the Ref (``k_r=1``, solid) and the scaled variant
    (``k_r``, dashed); right (red) axis = the scaled/Ref ratio.

    Skin  ``F_skin(eta) = (eta/2)(sinh eta + sin eta)/(cosh eta - cos eta)``
          --> 1 at DC, ~eta/2 at high speed.
    Prox  ``F_prox(eta) = eta (sinh eta - sin eta)/(cosh eta + cos eta)``
          --> eta^4/6 at DC (the dimensionless kernel of g(gamma_w, eta)),
          so the scaled/Ref ratio starts at k_r^4 and relaxes toward k_r.
    """
    mu0 = 4.0 * np.pi * 1e-7
    plt = _journal_rc()

    spd = np.linspace(50.0, speed_max_rpm, 400)   # 50 RPM floor avoids 0/0
    f_e = spd / 60.0 * pole_pairs
    delta = 1.0 / np.sqrt(np.pi * f_e * mu0 * sigma)      # skin depth [m]
    hc = h_c_ref_mm * 1e-3
    eta_ref = hc / delta
    eta_scl = (k_r * hc) / delta

    def f_skin(e):
        return 0.5 * e * (np.sinh(e) + np.sin(e)) / (np.cosh(e) - np.cos(e))

    def f_prox(e):
        return e * (np.sinh(e) - np.sin(e)) / (np.cosh(e) + np.cos(e))

    panels = [('a', 'skin', r'$F_\mathrm{skin}(\eta)$', f_skin),
              ('b', 'proximity', r'$F_\mathrm{prox}(\eta)$', f_prox)]
    # canvas ≈ svjour3 \textwidth so a figure* spans two columns at scale 1.
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.85), layout='constrained')
    out = {}
    for ax, (tag, name, ylab, fun) in zip(axes, panels):
        f_ref, f_scl = fun(eta_ref), fun(eta_scl)
        ax.plot(spd / 1e3, f_ref, color='#1a3a5c', lw=1.3, ls='-',
                label=rf'Ref ($k_r{{=}}1$, $\eta\!\leq\!{eta_ref[-1]:.1f}$)')
        ax.plot(spd / 1e3, f_scl, color='#1a3a5c', lw=1.3, ls='--',
                label=(rf'scaled ($k_r{{=}}{k_r:g}$, '
                       rf'$\eta\!\leq\!{eta_scl[-1]:.1f}$)'))
        ax.set_xlabel('Rotational speed [kRPM]')
        ax.set_ylabel(f'Resistance factor {ylab}')
        ax.set_xlim(0, speed_max_rpm / 1e3)
        ax.set_ylim(bottom=0)
        ax.grid(True, ls=':', lw=0.4, color='#dddddd')
        ax.set_axisbelow(True)
        ax.set_title(f'({tag}) {name} effect', fontsize=10.9)
        ax.legend(fontsize=7.6, frameon=False, loc='upper left')

        axr = ax.twinx()
        ratio = f_scl / f_ref
        axr.plot(spd / 1e3, ratio, color='#c62828', lw=1.5, ls='-')
        axr.set_ylabel('scaled / Ref ratio', color='#c62828')
        axr.tick_params(axis='y', colors='#c62828')
        axr.spines['right'].set_color('#c62828')
        out[name] = {'ratio_dc': float(ratio[0]),
                     'ratio_top': float(ratio[-1]),
                     'eta_ref_top': float(eta_ref[-1]),
                     'eta_scl_top': float(eta_scl[-1])}

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out


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
                                vlim: Optional[float] = None,
                                panels: Sequence[str] = ('ts', '1d',
                                                         'strips', '2d'),
                                panel_labels: Optional[Sequence[str]] = None,
                                radial_axis_mm: bool = False,
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
        a_slot0 = slot_mean_angle(p_ts, slot_id)
        bars_h = slot_bar_geometry(p_ts, slot_id,
                                   angle_rad=a_slot0)[0]['h_mm']
        # 두께도 TS 기하에서 --- copper_h_mm 기본값(Ref 1.686)을 SC 에
        # 그대로 흘리면 1-D 값만 조용히 틀어진다(실제로 겪음).
        amp = hybrid_je_at_points(p_ms, xy, freq_hz, slot_id=slot_id,
                                  signed=False,
                                  thickness_mm=bars_h) / 1e6
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
    # vlim 을 직접 주면 모델 간(예: Ref/SC) 색 스케일을 통일할 수 있다.
    vlim = (float(vlim) if vlim is not None
            else float(np.percentile(allv, vlim_percentile)))

    npan = len(panels)
    wide = _COLW_IN * ((1.20 if radial_axis_mm else 1.05)
                       if npan <= 2 else 2.1)
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
    if radial_axis_mm:
        # 슬롯 크기로 변형체를 구분할 수 있도록 반경 방향(=플롯 y)에만
        # 물리 눈금을 되살린다. 원점은 최내측 도체면, 눈금 간격은 두 모델
        # 공통 5 mm — 눈금 개수 자체가 k_r 를 드러낸다.
        from matplotlib.ticker import FuncFormatter
        y_ref = bars[0]['r_c'] - 0.5 * bars[0]['h_mm']
        y_top = geom['extent'][3]
        ax0 = axs[0]
        ax0.set_yticks(y_ref + np.arange(0.0, y_top - y_ref, 5.0))
        ax0.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _p: '%g' % (v - y_ref)))
        ax0.tick_params(axis='y', labelsize=8, length=2.2, pad=1.5)
        ax0.set_ylabel('radial position [mm]', fontsize=8.5, labelpad=1.5)

    labs = (panel_labels if panel_labels is not None
            else '(a) (b) (c) (d)'.split())
    for ax, lab in zip(axs, labs):
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




# ── Section 5 computational-cost stacked bar ───────────────────────────

# 실측값 (2026-08-21). 종전 원고 수치는 모든 Full-FEA 점에 일률 556 s 를
# 적용한 것이었다 (5.56/36 = 4.17/27 = 556 s). 실제 운전점당 시간은 속도에
# 따라 285 s(2 kRPM)에서 935 s(16 kRPM)까지 벌어지고, 보정 플랜은 앵커
# 16 kRPM 에 22~24 점이 몰려 있어 가장 비싼 대역이다. 전수 기준선은 속도가
# 고르게 섞여 일률 요율이 얼추 맞지만, 보정 비용은 과소평가된다.
#
# 출처:
#   운전점당 시간   ACLossCalcExport_{Ref,SC}_no_txt 의 운전점 폴더 mtime 스팬 중앙값.
#                   Ref 16 kRPM 그룹은 저전류 3단(14.4/28.8/57.6 A)이 더 있는 8전류
#                   격자라, 다른 속도와 같은 5전류로 제한해 잰다 (935 -> 579 s).
#   채택 플랜       AF_model_{Ref,SC}_exponent.json _meta.plan
#                   Ref 22@16k + 4@2/4/8k, SC 24@16k + 3@8k (= 27, 원고와 일치)
#   MS-FEA 30 점    Lab30 메시지 로그, Ref 22.5 분 = 0.375 h
#   맵 연산         슬롯 B 는 별도 해석이 아니라 위 MS-FEA 와 보정용 TS Full-FEA
#                   의 메시 데이터에서 추출한다 (저자 지적 2026-08-21). 남는 비용은
#                   그 필드를 꺼내는 export 뿐 — _txt_backfill 실측 2.60 h/240 점을
#                   30 점분으로 환산해 0.33 h. 막대에는 넣지 않는다: 이는 Motor-CAD 가
#                   자기 바이너리를 다시 여는 몫(39 s/점)이고, 해가 그대로 읽히는
#                   형식이면 파일 읽기(74.6 MB gz 2.7 s)로 수렴하는, 솔버가 아니라
#                   도구에 붙는 비용이기 때문이다. 각주로만 적는다.
#   SC 가 점당 비싼 이유는 스케일링이 아니라 메시다 — Motor-CAD 가 SC 를 23,818
#   요소로 끊었고 Ref 는 19,616 이다(비 1.21). 점당 시간 비 1.27 이 거의 그것으로
#   설명된다. HalfSC 는 21,272 로 그 사이에 있다.
# 저자 지시(2026-08-21): 와전류가 없는 시간이산 해석은 TS MS-FEA 로 분류한다.
#
# 색은 모델이 아니라 *단계* 를 뜻한다. 같은 단계는 어느 막대에서나 같은
# 색이라 높이 차이가 곧 절감이다. 쌓는 순서는 워크플로 순서이고, 맵 연산이
# 마지막이므로 맨 위에 온다 (저자 지시 2026-08-21).
#
# 무보정 하이브리드는 별도 막대가 아니라 제안 막대에서 Full-FEA 를 뺀
# 부분이다 (저자 지시 2026-08-21) — 제안 기법은 그 위에 희소 Full-FEA
# 보정을 얹은 것이다.
#
# 각 구간은 (라벨, 시간[h], 색, 해석 점수) 이며, 점수는 그 구간 옆에
# 꺾쇠와 함께 적는다 (저자 지시 2026-08-21) — 점수는 막대 총계가 아니라
# 단계에 붙는 양이기 때문이다.
COST_STACKBAR_DEFAULT = {
    'Exhaustive Full-FEA': [
        ('Full-FEA, Ref', 16.84, '#2e7d32', '120 pts'),
        ('Full-FEA, SC', 21.14, '#7cb342', '120 pts'),
    ],
    'Proposed': [
        ('MS-FEA', 0.38, '#4f7ea8', '30 pts'),
        ('Full-FEA, Ref', 5.46, '#2e7d32', '36 pts'),
        ('Full-FEA, SC', 5.49, '#7cb342', '27 pts'),
    ],
}

# label -> 막대 위에 적을 정확도
COST_STACKBAR_NOTES = {
    'Exhaustive Full-FEA': '(reference)',
    'Proposed': 'wMAE 0.6-0.8 %',
}

# 본 축에서 선으로만 보이는 바닥 구간을 확대해 보여 준다.
COST_STACKBAR_INSET = {
    'bar': 'Proposed',
    'ylim': 1.5,
    'text': 'Proposed, base',
}

_BRACKET_MIN_H = 2.0     # 이보다 얇은 구간은 꺾쇠 대신 지시선으로 뺀다


def _stack_bars(ax, bars, width, seen=None, inner_labels=True, positions=None):
    """Draw the stacked bars on ``ax``; return {label: cumulative total}."""
    totals = {}
    positions = positions or list(range(len(bars)))
    for x, lab in zip(positions, bars):
        bottom = 0.0
        for seg, hours, colour, _pts in bars[lab]:
            ax.bar(x, hours, bottom=bottom, width=width, color=colour,
                   edgecolor='white', linewidth=0.6)
            if seen is not None:
                seen.setdefault(seg, colour)
            if inner_labels and hours >= 3.0:
                ax.text(x, bottom + hours / 2, f'{hours:.1f}',
                        ha='center', va='center', fontsize=_fs(7.6),
                        color='white')
            bottom += hours
        totals[lab] = bottom
    return totals


def _bracket(ax, x, y0, y1, text, side='right', tick=0.035, gap=0.055,
             fs=7.4, colour='#666666'):
    """A bracket spanning y0..y1 at ``x``, labelled ``text`` beside it.

    ``side`` says which way the label goes; the ticks always point back
    towards the bar, so a left-side bracket is the mirror image.
    """
    s = 1.0 if side == 'right' else -1.0
    ax.plot([x, x], [y0, y1], lw=0.7, color=colour, clip_on=False)
    for y in (y0, y1):
        ax.plot([x - s * tick, x], [y, y], lw=0.7, color=colour,
                clip_on=False)
    ax.text(x + s * gap, (y0 + y1) / 2, text,
            ha='left' if side == 'right' else 'right', va='center',
            fontsize=_fs(fs), color='#333333', clip_on=False)


def plot_cost_stackbar(out_path: str,
                       bars: Optional[Dict] = None,
                       notes: Optional[Dict] = None,
                       inset: Optional[Dict] = None,
                       figsize: Tuple[float, float] = (_COLW_IN, 2.9)
                       ) -> str:
    """Stacked bar of the two-model study cost, replacing the cost table.

    Each bar stacks the stages that make up its total wall-clock time in
    workflow order, so the height difference is the saving.  ``bars`` maps
    a bar label to a list of ``(segment label, hours, colour, point
    count)``; the point count is written beside its own segment with a
    bracket, because points attach to a stage and not to the bar total.
    ``notes`` maps a bar label to the accuracy printed above it.
    ``inset`` names the bar whose bottom stage is too thin to read on the
    main axis and is magnified.  Defaults come from the body of the
    manuscript's Section 5.
    """
    plt = _journal_rc()
    bars = bars or COST_STACKBAR_DEFAULT
    notes = notes if notes is not None else COST_STACKBAR_NOTES
    inset = inset if inset is not None else COST_STACKBAR_INSET

    fig, ax = plt.subplots(figsize=figsize, layout='constrained')
    labels = list(bars)
    WIDTH = 0.42
    # 막대를 1 간격으로 두면 오른쪽 꺾쇠 라벨이 다음 막대에 닿는다. 라벨
    # 한 폭만큼 벌린다.
    POS = [1.35 * i for i in range(len(labels))]
    seen: Dict[str, str] = {}
    totals = _stack_bars(ax, bars, WIDTH, seen, positions=POS)

    # 꺾쇠는 두 막대 모두 오른쪽에 둔다 (저자 지시 2026-08-21). 확대 인셋은
    # 막대 사이가 아니라 그림 오른쪽 아래, 두 막대의 라벨을 다 지난 자리에
    # 놓아 연결선이 라벨을 가로지르지 않게 한다.
    for x, lab in zip(POS, labels):
        side, s = 'right', 1.0
        bottom = 0.0
        segs = bars[lab]
        for i, (seg, hours, colour, pts) in enumerate(segs):
            if hours >= _BRACKET_MIN_H:
                if pts:
                    _bracket(ax, x + s * (WIDTH / 2 + 0.05), bottom,
                             bottom + hours, pts, side=side)
            elif i == len(segs) - 1:
                # 최상단의 얇은 구간은 지시선으로 빼서 적는다.
                y = bottom + hours / 2
                ax.annotate(f'{hours:.2f} h',
                            xy=(x + WIDTH / 2, y),
                            xytext=(x + WIDTH / 2 + 0.30, y + 3.4),
                            fontsize=_fs(7.0), color='#333333',
                            ha='left', va='center',
                            arrowprops=dict(arrowstyle='-', lw=0.6,
                                            color='#666666',
                                            shrinkA=0, shrinkB=1))
            bottom += hours
        ax.text(x, bottom + 1.4, f'{totals[lab]:.1f} h', ha='center',
                va='bottom', fontsize=_fs(8.6), fontweight='bold')
        if lab in notes:
            ax.text(x, bottom + 4.9, notes[lab], ha='center', va='bottom',
                    fontsize=_fs(7.8), color='#444444')

    ax.set_xticks(POS)
    ax.set_xticklabels(labels, fontsize=_fs(8.2))
    ax.set_xlim(-0.50, POS[-1] + 1.75)
    ax.set_ylabel('Wall-clock time [h]')
    ax.set_ylim(0, 52)
    ax.set_yticks([0, 10, 20, 30, 40])
    ax.grid(axis='y', ls=':', lw=0.6, color='#bbbbbb')
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)

    # 바닥 구간 확대 — 본 축에서 MS-FEA 0.28 h 는 선으로만 보인다.
    if inset and inset.get('bar') in bars:
        bl = inset['bar']
        ytop = inset.get('ylim', 1.5)
        axins = ax.inset_axes([0.790, 0.090, 0.185, 0.245])
        _stack_bars(axins, {bl: bars[bl]}, WIDTH, inner_labels=False)
        axins.set_xlim(-WIDTH * 1.7, WIDTH * 1.7)
        axins.set_ylim(0, ytop)
        # 눈금은 두지 않는다 — 확대 구간의 값은 옆에 적어 두므로 축이
        # 중복이고, 작은 인셋에서 눈금 라벨은 본 축 눈금과 헷갈린다.
        axins.set_xticks([])
        axins.set_yticks([])
        for side in ('top', 'right', 'left'):
            axins.spines[side].set_visible(False)
        axins.spines['bottom'].set_linewidth(0.6)
        # 값은 인셋 아래 한 줄로 — 막대 옆에 붙이면 인셋 폭을 넘어
        # 본 축의 라벨과 부딪힌다.
        seg, hours, _c, pts = bars[bl][0]
        axins.set_xlabel(f'{hours:.2f} h\n{pts}' if pts else f'{hours:.2f} h',
                         fontsize=_fs(6.6), color='#333333', labelpad=2,
                         linespacing=1.15)
        axins.set_title(inset.get('text', ''), fontsize=_fs(6.8),
                        color='#444444', pad=2)

        # 확대한 자리를 본 축에 표시하고 인셋으로 잇는다.
        # indicate_inset_zoom 은 못 쓴다 — 인셋이 막대를 x=0 에 다시 그리므로
        # 그 x 범위를 본 축 좌표로 읽으면 두 막대를 가로지르는 사각형이 된다.
        bi = POS[labels.index(bl)]
        rx0, rx1 = bi - WIDTH / 2 - 0.03, bi + WIDTH / 2 + 0.03
        ry1 = ytop
        ax.add_patch(plt.Rectangle((rx0, 0), rx1 - rx0, ry1, fill=False,
                                   edgecolor='#999999', lw=0.6, zorder=5))
        # 인셋은 막대 오른쪽 아래에 있다. 사각형 오른쪽 변에서 인셋 왼쪽
        # 아래 모서리로 낮게 잇는다 — 꺾쇠 라벨(가장 낮은 것이 y≈3)보다
        # 아래로 지나가야 선이 글자를 가로지르지 않는다.
        ip = axins.get_position()
        inv = ax.transData.inverted()
        ix0, iy0 = inv.transform(fig.transFigure.transform((ip.x0, ip.y0)))
        ax.plot([rx1, ix0], [ry1 * 0.5, iy0], lw=0.6, color='#999999',
                zorder=5, clip_on=False)

    # 범례는 그려진 순서가 아니라 워크플로 순서로 세운다.
    from matplotlib.patches import Patch
    order = [s for s in ('MS-FEA', 'Full-FEA, Ref', 'Full-FEA, SC',
                         'Map computation') if s in seen]
    order += [s for s in seen if s not in order]
    ax.legend(handles=[Patch(facecolor=seen[s], label=s) for s in order],
              loc='upper right', frameon=False, fontsize=_fs(7.2),
              handlelength=1.0, handletextpad=0.45, labelspacing=0.24,
              borderaxespad=0.0)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path)
    stem = os.path.splitext(out_path)[0]
    if out_path.lower().endswith('.pdf'):
        fig.savefig(stem + '.png', dpi=220)
    plt.close(fig)
    print('비용 누적막대 저장:', out_path)
    return out_path


# ── Similarity-transfer error, as a field (Section 5.2) ────────────────

# Fig 3 은 상사 대응점의 필드를 나란히 보일 뿐 오차를 정량화하지 않는다.
# 회로 수준에는 Fig 9 가 그 일을 해 주는데 필드 수준에는 대응 그림이
# 없다는 것이 저자 지적(2026-08-22)이었다.
#
# 차분을 어떻게 그리느냐가 그림의 정직성을 가른다. 두 모델은 Motor-CAD 가
# 각자 메시를 끊어(Ref MS 14,792 요소 / SC MS 22,690) 요소가 서로 겹치지
# 않는다. 한쪽을 다른 쪽 메시에 최근접으로 얹으면 요소 간 결맞음이 0.43 —
# 사실상 소금후추 잡음이고, 그것도 공극·치선단에 몰려 독자가 보는 자리에
# 얼룩이 앉는다. 최근접을 선형 보간으로 바꿔도 6.59 % -> 5.90 % 로 거의
# 안 줄어드는데, 이는 남는 차이가 매칭 오차가 아니라 불연속면 해상도라는
# 뜻이다. 그래서 **양쪽을 제3의 공통 극좌표 격자로 보낸다** (결맞음 0.89).
#
# 그리고 두 양을 함께 보인다. A 는 재질 경계에서 연속이라 차분장이
# 매끄럽고(전 범위의 1.3 %), 식~(MVPScaling) 의 A -> k_r A 주장과 직결된다.
# |B| 는 경계에서 불연속이라 차분에 밝은 선이 남는데, 그것은 잡음이 아니라
# 이산화가 불연속을 다르게 끊는 실제 효과다 — 캡션이 그렇게 말한다.

_DIFF_RASTER = (400, 600)        # (반경 방향, 각 방향) — 외경에서 셀 0.5 x 0.75 mm, 요소(0.44~0.69 mm)와 동급


from .field_metrics import (mesh_element_to_raster, mesh_field_to_raster,
                            periodic_region_to_raster,
                            periodic_vector_to_raster)


def _polar_raster(clouds, n_r=None, n_t=None, pad=0.995):
    """Common polar grid covering the overlap of several point clouds.

    Returns (R, T, X, Y) meshes. Both fields are interpolated onto this,
    rather than one onto the other's mesh, so neither model's
    discretisation is privileged.
    """
    n_r = n_r or _DIFF_RASTER[0]
    n_t = n_t or _DIFF_RASTER[1]
    rr = [np.hypot(c[0], c[1]) for c in clouds]
    tt = [np.arctan2(c[1], c[0]) for c in clouds]
    r0 = max(r.min() for r in rr) / pad
    r1 = min(r.max() for r in rr) * pad
    t0 = max(t.min() for t in tt)
    t1 = min(t.max() for t in tt)
    R, T = np.meshgrid(np.linspace(r0, r1, n_r),
                       np.linspace(t0, t1, n_t), indexing='ij')
    return R, T, R * np.cos(T), R * np.sin(T)


def _to_raster(x, y, v, X, Y):
    """Linear interpolation of a scattered field onto the raster."""
    from scipy.interpolate import LinearNDInterpolator
    f = LinearNDInterpolator(np.column_stack([x, y]), np.asarray(v, float))
    return f(X, Y)


def _curl_z_mag(A, R, T):
    """|B| from a z-directed vector potential on a polar raster.

    In two dimensions B_r = (1/r) dA/dtheta and B_theta = -dA/dr, so a
    difference field in A yields the corresponding difference in B by one
    stencil on one grid.  A arrives in Wb/m and R in mm, so the radius
    converts to metres for the result to come out in tesla.
    """
    r_m = R[:, 0] / 1000.0
    t_rad = T[0, :]
    dA_dr = np.gradient(A, r_m, axis=0)
    dA_dt = np.gradient(A, t_rad, axis=1)
    b_r = dA_dt / np.maximum(R / 1000.0, 1e-9)
    b_t = -dA_dr
    return np.hypot(b_r, b_t)


_PARULA_STOPS = [
    (0.2422, 0.1504, 0.6603), (0.2810, 0.3228, 0.9579),
    (0.1786, 0.5289, 0.9682), (0.0689, 0.6948, 0.8394),
    (0.2161, 0.7843, 0.5923), (0.6720, 0.7793, 0.2227),
    (0.9763, 0.7831, 0.0538), (0.9769, 0.9839, 0.0805),
]


def _parula():
    """Fig 11 draws its delta-eta map in MATLAB's parula; the error panels
    here use the same ramp so the two figures read alike."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list('parula', _PARULA_STOPS)


_SECTOR_DEG = 45.0               # e10: 8 poles, so one sector is one pole
_SECTOR_FOLDS = [0, 1, 2, -1, 3, -2, 4, -3, 5]


def _diff_row(ref_npz, sc_npz, k_r, window_deg=(-40.0, 0.0)):
    """Everything one row of the similarity-error figure needs.

    The stored sector is folded into a single angular window so that the
    rotor sits inside the stator bore, the way a solver assembles a
    cross-section from a periodic model.

    window_deg : the window to draw.  It has to be narrow enough that the
        rotor reaches it in one fold, or the picture carries a seam where
        two folds meet -- exact in the field, but the region codes change
        across it and every region-wise step then treats it as an
        interface.  e10 at block 91 stores the rotor at -130..-85 and the
        stator at -45..0 degrees, so one +90-degree fold covers -40..0
        and that is the widest seamless window.
    """
    dr, ds = np.load(ref_npz), np.load(sc_npz)
    # 상사 변환: 좌표(노드까지)는 k_r 배, B 는 불변.
    r_nodes, r_tri = dr['node_xy'] * k_r, dr['tri']
    s_nodes, s_tri = ds['node_xy'], ds['tri']
    rr = np.hypot(dr['x_mm'], dr['y_mm']) * k_r
    rs = np.hypot(ds['x_mm'], ds['y_mm'])

    # 창 하나짜리 극좌표 격자. 두 모델이 같은 격자를 쓰므로 어느 쪽
    # 메시도 특별대우를 받지 않는다.
    n_r, n_t = _DIFF_RASTER
    r0, r1 = max(rr.min(), rs.min()), min(rr.max(), rs.max())
    R, T = np.meshgrid(np.linspace(r0, r1, n_r),
                       np.radians(np.linspace(*window_deg, n_t)),
                       indexing='ij')
    X, Y = R * np.cos(T), R * np.sin(T)

    def sample(nodes, tri, d, scale_area):
        # 값은 솔버 등고선처럼 메시 연결 정보 위에서 영역별로 뽑는다.
        # 영역별로 나누지 않으면 구리/철 계면이 요소 하나만큼 번지고,
        # 밀도가 다른 두 메시는 다르게 번져서 필드가 아니라 메시를
        # 비교하게 된다.
        bx, by = periodic_vector_to_raster(
            nodes, tri, d['bx_T'], d['by_T'], X, Y,
            _SECTOR_DEG, _SECTOR_FOLDS, region=d['reg'])
        code, base = periodic_region_to_raster(
            nodes, tri, d['reg'], X, Y, _SECTOR_DEG, _SECTOR_FOLDS)
        return bx, by, code, base

    Bx_r, By_r, code_r, base_r = sample(r_nodes, r_tri, dr, k_r ** 2)
    Bx_s, By_s, code_s, base_s = sample(s_nodes, s_tri, ds, 1.0)
    B_r, B_s = np.hypot(Bx_r, By_r), np.hypot(Bx_s, By_s)
    # 성분을 각각 빼서 참 벡터차를 만든다. |B_1| - |B_2| (크기의 차) 가
    # 아니고, A 를 미분하지도 않는다 — 내보낸 A 는 1e-4 Wb/m 로 양자화돼
    # 있어(B 는 2.3e-7 T) 0.8 mm 격자에서 한 양자가 0.12 T 로 증폭된다.
    dB = np.hypot(Bx_r - Bx_s, By_r - By_s)
    ok = np.isfinite(dB)

    # 계면 띠: 이웃 셀과 코드가 다른 곳 한 칸 양옆까지, 두 메시 합집합.
    edge = np.zeros_like(ok)
    for arr in (code_r, code_s):
        edge[1:, :] |= arr[1:, :] != arr[:-1, :]
        edge[:-1, :] |= arr[1:, :] != arr[:-1, :]
        edge[:, 1:] |= arr[:, 1:] != arr[:, :-1]
        edge[:, :-1] |= arr[:, 1:] != arr[:, :-1]
    interior = ok & ~edge
    # 번호는 두 모델이 다르게 매기므로(같은 도체가 Ref 264, SC 266) 모델
    # 간 비교는 코드가 아니라 도체 플래그로 한다.
    cond = (ok & np.isin(base_s, ds['conductor_codes'])
            & np.isin(base_r, dr['conductor_codes']))

    def block(m):
        # 셀 평균 |dB| / 셀 평균 |B| 가 아니라 L2 노름 비 — 경계의 소수
        # 셀이 평균을 끌지 않도록 에너지 무게로 잰다.
        b_rms = float(np.sqrt(np.nanmean(B_s[m] ** 2)))
        d_rms = float(np.sqrt(np.nanmean(dB[m] ** 2)))
        return {
            'n': int(m.sum()),
            'dB_rms_T': d_rms,
            'dB_mean_T': float(np.nanmean(dB[m])),
            'dB_p95_T': float(np.nanpercentile(dB[m], 95)),
            'B_rms_T': b_rms,
            'dB_L2_pct': float(100 * d_rms / b_rms),
            'share_of_sum_dB2_pct': float(100 * np.nansum(dB[m] ** 2)
                                          / np.nansum(dB[ok] ** 2)),
        }

    # 도체별 평균 벡터의 차 — 원고의 진폭 지표처럼 도체 평균 수준에서
    # 재는 값이라 화소 단위 비와 급이 다르다. 같은 셀을 양쪽에 쓰므로
    # 도체 경계를 두 메시가 달리 놓는 문제가 평균 안에서 사라진다.
    codes = np.unique(code_s[cond])
    counts = np.array([(cond & (code_s == c)).sum() for c in codes])
    # 창 가장자리에 걸쳐 잘린 도체는 평균이 반쪽이라 뺀다.
    whole = counts > 0.75 * np.median(counts)
    cb_r, cb_s, centres = [], [], []
    for c in codes[whole]:
        m = cond & (code_s == c)
        cb_r.append([np.nanmean(Bx_r[m]), np.nanmean(By_r[m])])
        cb_s.append([np.nanmean(Bx_s[m]), np.nanmean(By_s[m])])
        centres.append((c, float(X[m].mean()), float(Y[m].mean())))
    cb_r, cb_s = np.asarray(cb_r), np.asarray(cb_s)
    d_c = np.hypot(*(cb_r - cb_s).T)
    b_c = np.hypot(*cb_s.T)
    per_conductor = {
        'n_conductors': int(len(b_c)),
        'dBbar_L2_pct': float(100 * np.sqrt(np.sum(d_c ** 2))
                              / np.sqrt(np.sum(b_c ** 2))),
        'dBbar_rel_mean_pct': float(100 * np.mean(d_c / b_c)),
        'dBbar_rel_max_pct': float(100 * np.max(d_c / b_c)),
        'Bbar_mean_T': float(np.mean(b_c)),
    }
    # 접힌 복제 번호가 곧 회전자/고정자 구분이다: 고정자는 저장된
    # 섹터(k=0)에서, 회전자는 창을 덮는 복제에서 온다.
    lo, span = int(ds['reg'].min()), int(ds['reg'].max()) - int(ds['reg'].min()) + 1
    slot = np.where(code_s >= 0, (code_s - lo) // span, -1)
    stator = ok & (slot == 0)
    rotor = ok & (slot > 0)
    stats = {
        'all': block(ok),
        'rotor': block(rotor),
        'stator': block(stator),
        'interior': block(interior),
        'interface': block(ok & ~interior),
        'conductor_cells': block(cond),
        'conductor_mean': per_conductor,
    }
    return dict(X=X, Y=Y, B_r=B_r, B_s=B_s, dB=dB, ok=ok, stats=stats,
                r_nodes=r_nodes, r_tri=r_tri, s_nodes=s_nodes, s_tri=s_tri,
                reg_s=code_s, centres=centres)


def _zoom_box(row, half_mm=3.4):
    """A box on one conductor, the same one in every row: the gap-side
    layer of the middle slot, found by geometry rather than by region name
    since the two export formats name conductors differently."""
    codes, cx, cy = zip(*row['centres'])
    cx, cy = np.asarray(cx), np.asarray(cy)
    r, th = np.hypot(cx, cy), np.degrees(np.arctan2(cy, cx))
    mid = -22.5 if th.min() < -10 else th.mean()
    near = np.abs(th - mid) < 4.0
    if not near.any():
        near = np.ones_like(th, bool)
    k = np.flatnonzero(near)[np.argmax(r[near])]
    m = row['reg_s'] == codes[k]
    return (float(row['X'][m].mean()), float(row['Y'][m].mean()), half_mm)


def _draw_mesh_zoom(ax, row, box, aspect=1.9, legend=False):
    """Both meshes and the common raster inside ``box``.

    The box is widened to the panel aspect so the zoom fills the same
    frame as the field panels beside it.
    """
    from matplotlib.tri import Triangulation
    x0, y0, h = box
    hx, hy = h * aspect, h
    X, Y = row['X'], row['Y']
    # 공통 격자: 셀 경계선을 r 방향·θ 방향으로 그린다. 상자를 넘는
    # 선분은 잘라 두어 축 밖으로 새지 않게 한다.
    inside = (np.abs(X - x0) < hx * 1.3) & (np.abs(Y - y0) < hy * 1.3)
    ii, jj = np.nonzero(inside)
    i0, i1, j0, j1 = ii.min(), ii.max() + 1, jj.min(), jj.max() + 1
    for i in range(i0, i1):
        ax.plot(X[i, j0:j1], Y[i, j0:j1], color='0.6', lw=0.3, zorder=1)
    for j in range(j0, j1):
        ax.plot(X[i0:i1, j], Y[i0:i1, j], color='0.6', lw=0.3, zorder=1)
    for nodes, tri, colour, z in ((row['r_nodes'], row['r_tri'], '#1f77b4', 2),
                                  (row['s_nodes'], row['s_tri'], '#d62728', 3)):
        P = nodes[tri]
        keep = ((np.abs(P[:, :, 0].mean(1) - x0) < hx * 1.4)
                & (np.abs(P[:, :, 1].mean(1) - y0) < hy * 1.4))
        t = tri[keep]
        used, inv = np.unique(t, return_inverse=True)
        T = Triangulation(nodes[used, 0], nodes[used, 1],
                          inv.reshape(t.shape))
        ax.triplot(T, color=colour, lw=0.45, zorder=z)
    if legend:
        from matplotlib.lines import Line2D
        ax.legend(handles=[Line2D([], [], color='#1f77b4', lw=0.8,
                                  label='Ref, scaled'),
                           Line2D([], [], color='#d62728', lw=0.8,
                                  label='SC'),
                           Line2D([], [], color='0.6', lw=0.8,
                                  label='common raster')],
                  loc='upper left', fontsize=_fs(5.6), frameon=True,
                  facecolor='white', framealpha=0.85, borderpad=0.25,
                  handlelength=1.3, handletextpad=0.4,
                  labelspacing=0.25).get_frame().set_linewidth(0.3)
    ax.set_xlim(x0 - hx, x0 + hx)
    ax.set_ylim(y0 - hy, y0 + hy)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])


def plot_field_diff_panels(rows, out_path: str,
                           figsize: Optional[Tuple[float, float]] = None,
                           raster_dpi: int = 600,
                           show_mesh: bool = True) -> Dict:
    """Similarity-transfer error as a field, one row per solver level.

    ``rows`` is a sequence of ``(label, ref_npz, sc_npz, k_r)``.  The Ref
    field is carried onto SC by the similarity transform -- coordinates
    by k_r, B invariant -- and both are then projected onto a common
    polar raster through their own mesh connectivity.  Each row draws the
    transferred |B|, the directly solved |B| on the same scale, and the
    vector difference |B_ref - B_sc|; with ``show_mesh`` a fourth panel
    zooms on one conductor to show the two meshes and the common raster
    the comparison lives on.  Colour scales are shared across rows and
    sit above the panels.  The MVP is not drawn: the export quantises A
    at 1e-4 Wb/m, so its difference is four quanta of structureless
    noise.

    Returns the per-row difference statistics, so the caption and the
    body can quote the same numbers the figure draws.
    """
    plt = _journal_rc()
    data = [(label, _diff_row(ref_npz, sc_npz, k_r))
            for label, ref_npz, sc_npz, k_r in rows]
    n_row, n_col = len(data), 4 if show_mesh else 3

    # 눈금은 행 공용: 두 수준이 같은 자로 읽히게.
    b_max = max(np.nanpercentile(np.concatenate([d['B_r'][d['ok']],
                                                 d['B_s'][d['ok']]]), 99.5)
                for _, d in data)
    dB_lim = max(np.nanpercentile(d['dB'][d['ok']], 99) for _, d in data)
    parula = _parula()

    fig, axes = plt.subplots(
        n_row, n_col,
        figsize=figsize or (2.1 * n_col, 1.28 * n_row + 0.85),
        layout='constrained')
    axes = np.asarray(axes).reshape(n_row, n_col)

    h_b = h_d = None
    box = _zoom_box(data[0][1]) if show_mesh else None
    for i, (label, d) in enumerate(data):
        X, Y = d['X'], d['Y']
        panels = [(d['B_r'], 'jet', 0.0, b_max),
                  (d['B_s'], 'jet', 0.0, b_max),
                  (d['dB'], parula, 0.0, dB_lim)]
        for j, (V, cmap, lo, hi) in enumerate(panels):
            ax = axes[i, j]
            h = ax.pcolormesh(X, Y, np.ma.masked_invalid(V), cmap=cmap,
                              vmin=lo, vmax=hi, shading='auto',
                              rasterized=True)
            if j == 0:
                h_b = h
            elif j == 2:
                h_d = h
            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])
        if show_mesh:
            _draw_mesh_zoom(axes[i, 3], d, box, legend=(i == 0))
            # 확대 위치를 차분 패널에 상자로 표시
            x0, y0, hh = box
            axes[i, 2].add_patch(plt.Rectangle(
                (x0 - 1.9 * hh, y0 - hh), 3.8 * hh, 2 * hh, fill=False,
                ec='k', lw=0.6))
        for j in range(n_col):
            ax = axes[i, j]
            for sp in ax.spines.values():
                sp.set_linewidth(0.4)
            # 패널 태그는 하단, 그림 내부 제목은 두지 않는다.
            ax.set_xlabel(f'({chr(97 + i * n_col + j)})',
                          fontsize=_fs(8.0), labelpad=2)
        axes[i, 0].set_ylabel(label, fontsize=_fs(8.2))

    # 컬러바는 행 공용으로 상단에: |B| 는 (a)(b) 열 위, |dB| 는 (c) 열 위.
    for h, cols in ((h_b, [0, 1]), (h_d, [2])):
        cb = fig.colorbar(h, ax=list(axes[:, cols].ravel()),
                          location='top', shrink=0.9, aspect=40 if len(cols) > 1 else 20,
                          pad=0.02)
        cb.ax.tick_params(labelsize=_fs(6.4), length=2, pad=1)
        cb.ax.xaxis.set_ticks_position('top')

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path, dpi=raster_dpi)
    stem = os.path.splitext(out_path)[0]
    if out_path.lower().endswith('.pdf'):
        fig.savefig(stem + '.png', dpi=220)
    plt.close(fig)

    stats = {label: d['stats'] for label, d in data}
    print('상사 전달 오차 필드 저장:', out_path)
    for k, v in stats.items():
        print(f'  {k}:')
        for sub, w in v.items():
            if 'n' not in w:
                print(f"    {sub:16s} {w['n_conductors']} conductors  "
                      f"||dB_bar||/||B_bar|| {w['dBbar_L2_pct']:.2f} %  "
                      f"rel mean {w['dBbar_rel_mean_pct']:.2f} %  "
                      f"max {w['dBbar_rel_max_pct']:.2f} %  "
                      f"B_bar {w['Bbar_mean_T']:.3f} T")
                continue
            print(f"    {sub:16s} n {w['n']:6d}  |dB| rms {w['dB_rms_T']:.4f} "
                  f"mean {w['dB_mean_T']:.4f} p95 {w['dB_p95_T']:.4f} T  "
                  f"||dB||/||B|| {w['dB_L2_pct']:5.2f} %  "
                  f"share of sum dB^2 {w['share_of_sum_dB2_pct']:5.1f} %")
    return stats
