"""
pyMotorGeo.plotting
===================
시각화 함수: 주기 플롯, 재구성 플롯, 닫힌 영역 플롯, 네이밍된 영역 플롯.
"""

import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Patch, Arc as MplArc
from typing import List, Tuple, Dict, Optional

from .core import EntityInfo, StatorRotorSplit, rotate_point, mirror_point
from .regions import REGION_NAMES, REGION_COLORS, SHORT_NAMES
from .symmetry import extract_one_period


def _edge_to_patch_points(ei: EntityInfo, k0: Tuple, k1: Tuple, n_arc_pts: int = 20) -> List:
    """엔티티의 실제 형상에 따른 중간 점들을 반환합니다."""
    if ei is None:
        return [k0, k1]
    if ei.etype == 'LINE':
        return [k0, k1]
    elif ei.etype == 'ARC' and ei.center and ei.radius:
        cx, cy = ei.center
        r = ei.radius
        sa = ei.start_angle
        ea = ei.end_angle
        if ea < sa:
            ea += 360.0
        p_start = (cx + r * math.cos(math.radians(sa)),
                   cy + r * math.sin(math.radians(sa)))
        d_start = math.hypot(k0[0] - p_start[0], k0[1] - p_start[1])
        if d_start < 0.5:
            angles = [math.radians(sa + (ea - sa) * t / n_arc_pts)
                      for t in range(n_arc_pts + 1)]
        else:
            angles = [math.radians(ea - (ea - sa) * t / n_arc_pts)
                      for t in range(n_arc_pts + 1)]
        return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]
    elif ei.etype == 'LWPOLYLINE':
        pts = [(p[0], p[1]) for p in ei.points]
        d0 = math.hypot(k0[0] - pts[0][0], k0[1] - pts[0][1])
        if d0 > 0.5:
            pts = pts[::-1]
        return pts
    return [k0, k1]


def _get_face_render_pts(fi: Dict, edge_to_entity: Dict) -> List:
    """face의 ARC를 반영한 렌더링 좌표를 반환합니다."""
    if '_render_pts' in fi:
        return fi['_render_pts']
    verts = fi['vertices']
    nv = len(verts)
    poly_pts = []
    for j in range(nv):
        k0 = verts[j]
        k1 = verts[(j + 1) % nv]
        edge_key = tuple(sorted([k0, k1]))
        ei = edge_to_entity.get(edge_key, None)
        seg_pts = _edge_to_patch_points(ei, k0, k1)
        if j == 0:
            poly_pts.extend(seg_pts)
        else:
            poly_pts.extend(seg_pts[1:])
    fi['_render_pts'] = poly_pts
    return poly_pts


def _render_face_patch(ax, fi: Dict, edge_to_entity: Dict,
                       alpha: float = 0.7, zorder: int = 3):
    """face 한 개를 ARC 반영하여 패치로 그립니다."""
    name = fi.get('name', 'unknown')
    color = REGION_COLORS.get(name, '#D0D0D0')
    poly_pts = _get_face_render_pts(fi, edge_to_entity)

    patch = MplPolygon(poly_pts, closed=True, fc=color,
                       ec='black', lw=0.6, alpha=alpha, zorder=zorder)
    ax.add_patch(patch)
    return patch, poly_pts


def plot_one_period(entities: List[EntityInfo],
                    period_deg: float,
                    reference_sector: int = 0,
                    origin: Tuple[float, float] = (0.0, 0.0),
                    figsize: Tuple = (9, 9)):
    """한 주기의 엔티티만 matplotlib으로 시각화합니다."""
    one_period = extract_one_period(entities, period_deg, reference_sector, origin)
    fig, ax = plt.subplots(figsize=figsize)
    ox, oy = origin

    for ei in one_period:
        xs = [p[0] for p in ei.points]
        ys = [p[1] for p in ei.points]
        if ei.etype == 'LINE':
            ax.plot(xs, ys, 'b-', lw=0.8)
        elif ei.etype == 'CIRCLE' and ei.center and ei.radius:
            ax.add_patch(plt.Circle(ei.center, ei.radius, fill=False, ec='green', lw=0.8))
        elif ei.etype == 'ARC' and ei.center and ei.radius:
            ax.add_patch(MplArc(
                ei.center, 2 * ei.radius, 2 * ei.radius,
                angle=0, theta1=ei.start_angle, theta2=ei.end_angle,
                ec='orange', lw=0.8))
        elif ei.etype == 'LWPOLYLINE':
            ax.plot(xs, ys, 'r-', lw=0.8)
        else:
            ax.plot(xs, ys, 'k.', ms=2)

    ang_s = math.radians(reference_sector * period_deg)
    ang_e = math.radians((reference_sector + 1) * period_deg)
    r_max = max((ei.r_max for ei in one_period), default=1) * 1.1
    ax.plot([ox, ox + r_max * math.cos(ang_s)], [oy, oy + r_max * math.sin(ang_s)], 'r--', lw=0.6)
    ax.plot([ox, ox + r_max * math.cos(ang_e)], [oy, oy + r_max * math.sin(ang_e)], 'r--', lw=0.6)
    ax.set_aspect('equal')
    ax.set_title(f'One period (sector {reference_sector}, {period_deg:.1f}°)')
    ax.grid(True, lw=0.3)
    plt.show()
    return fig, ax


def plot_reconstructed(half_unit: Dict,
                       origin: Tuple[float, float] = (0.0, 0.0),
                       coverage: str = 'period',
                       n_poles: Optional[int] = None,
                       n_slots: Optional[int] = None,
                       period_deg: Optional[float] = None,
                       split: Optional[StatorRotorSplit] = None,
                       figsize: Tuple = (10, 10)):
    """반슬롯/반극에서 재구성한 기하를 시각화합니다."""
    from .symmetry import reconstruct_geometry
    
    recon = reconstruct_geometry(half_unit, origin, coverage,
                                 n_poles, n_slots, period_deg)

    fig, ax = plt.subplots(figsize=figsize)
    ox, oy = origin

    r_mid = (split.airgap_r_inner + split.airgap_r_outer) / 2 if split else 80

    for ei in recon:
        if ei.etype in ('CIRCLE', 'ARC') and ei.center:
            d_from_origin = math.hypot(ei.center[0] - ox, ei.center[1] - oy)
            if d_from_origin < 1e-3:
                color = '#2ecc71'
            elif ei.radius and ei.radius > r_mid:
                color = '#3498db'
            else:
                color = '#e67e22'
        else:
            c_r = sum(math.hypot(p[0] - ox, p[1] - oy) for p in ei.points) / max(len(ei.points), 1)
            color = '#3498db' if c_r > r_mid else '#e67e22'

        xs = [p[0] for p in ei.points]
        ys = [p[1] for p in ei.points]

        if ei.etype == 'LINE':
            ax.plot(xs, ys, color=color, lw=0.8)
        elif ei.etype == 'CIRCLE' and ei.center and ei.radius:
            ax.add_patch(plt.Circle(ei.center, ei.radius, fill=False,
                                    ec=color, lw=0.8))
        elif ei.etype == 'ARC' and ei.center and ei.radius:
            ax.add_patch(MplArc(
                ei.center, 2 * ei.radius, 2 * ei.radius,
                angle=0, theta1=ei.start_angle, theta2=ei.end_angle,
                ec=color, lw=0.8))
        elif ei.etype == 'LWPOLYLINE':
            ax.plot(xs, ys, color=color, lw=0.8)
        else:
            ax.plot(xs, ys, 'k.', ms=2)

    if coverage == 'full':
        target_deg = 360.0
    elif coverage == 'period':
        target_deg = period_deg if period_deg else 90.0
    else:
        target_deg = float(coverage)

    ref_start = half_unit['ref_angle_start']
    r_max = max((ei.r_max for ei in recon if ei.points), default=1) * 1.1

    if target_deg < 360:
        a1 = math.radians(ref_start)
        a2 = math.radians(ref_start + target_deg)
        ax.plot([ox, ox + r_max * math.cos(a1)], [oy, oy + r_max * math.sin(a1)],
                'r--', lw=0.6, alpha=0.7)
        ax.plot([ox, ox + r_max * math.cos(a2)], [oy, oy + r_max * math.sin(a2)],
                'r--', lw=0.6, alpha=0.7)

    legend_elements = [
        Patch(fc='#3498db', alpha=0.7, label='Stator'),
        Patch(fc='#e67e22', alpha=0.7, label='Rotor'),
        Patch(fc='#2ecc71', alpha=0.7, label='Boundary'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)

    slot_p = half_unit['slot_pitch_deg']
    pole_p = half_unit['pole_pitch_deg']
    ax.set_aspect('equal')
    ax.set_title(f'Reconstructed from half-unit — {coverage} ({target_deg:.0f}°)\n'
                 f'Slot pitch={slot_p:.2f}°, Pole pitch={pole_p:.2f}°',
                 fontsize=12, fontweight='bold')
    ax.grid(True, lw=0.3, alpha=0.4)
    plt.tight_layout()
    plt.show()
    return fig, ax, recon


def plot_closed_regions(entities: List[EntityInfo],
                        period_deg: float,
                        reference_sector: int = 0,
                        origin: Tuple[float, float] = (0.0, 0.0),
                        split: Optional[StatorRotorSplit] = None,
                        tol_digits: int = 2,
                        min_area: float = 0.5,
                        figsize: Tuple = (12, 12)):
    """한 주기의 닫힌 영역(closed region)들을 각각 색칠하여 시각화합니다."""
    from .regions import _build_planar_graph, _traverse_faces, _face_area_signed
    
    ox, oy = origin
    one_period = extract_one_period(entities, period_deg, reference_sector, origin)

    adj, edge_to_entity, independent_circles = _build_planar_graph(
        one_period, origin, split, period_deg, reference_sector, tol_digits)

    raw_faces = _traverse_faces(adj, origin)

    faces_info = []
    for face in raw_faces:
        area = _face_area_signed(face)
        abs_area = abs(area)
        if abs_area < min_area:
            continue
        if area > 0:
            faces_info.append({
                'vertices': face,
                'area': area,
                'n_edges': len(face),
            })

    if split is not None:
        r_mid = (split.airgap_r_inner + split.airgap_r_outer) / 2
        for fi in faces_info:
            centroid_r = sum(math.hypot(v[0] - ox, v[1] - oy) for v in fi['vertices']) / len(fi['vertices'])
            fi['part'] = 'stator' if centroid_r > r_mid else 'rotor'
    else:
        for fi in faces_info:
            fi['part'] = 'unknown'

    fig, ax = plt.subplots(figsize=figsize)

    for ei in one_period:
        xs = [p[0] for p in ei.points]
        ys = [p[1] for p in ei.points]
        if ei.etype == 'LINE':
            ax.plot(xs, ys, color='#888888', lw=0.4, zorder=1)
        elif ei.etype == 'CIRCLE' and ei.center and ei.radius:
            ax.add_patch(plt.Circle(ei.center, ei.radius, fill=False,
                                    ec='#888888', lw=0.4, zorder=1))
        elif ei.etype == 'ARC' and ei.center and ei.radius:
            ax.add_patch(MplArc(
                ei.center, 2 * ei.radius, 2 * ei.radius,
                angle=0, theta1=ei.start_angle, theta2=ei.end_angle,
                ec='#888888', lw=0.4, zorder=1))
        elif ei.etype == 'LWPOLYLINE':
            ax.plot(xs, ys, color='#888888', lw=0.4, zorder=1)

    stator_faces = [fi for fi in faces_info if fi['part'] == 'stator']
    rotor_faces = [fi for fi in faces_info if fi['part'] == 'rotor']

    stator_cmap = plt.cm.Blues
    rotor_cmap = plt.cm.Oranges

    def _render_faces(face_list, cmap, label_prefix, alpha=0.45):
        if not face_list:
            return
        n = len(face_list)
        for i, fi in enumerate(face_list):
            verts = fi['vertices']
            poly_pts = []
            nv = len(verts)
            for j in range(nv):
                k0 = verts[j]
                k1 = verts[(j + 1) % nv]
                edge_key = tuple(sorted([k0, k1]))
                ei = edge_to_entity.get(edge_key, None)
                seg_pts = _edge_to_patch_points(ei, k0, k1)
                if j == 0:
                    poly_pts.extend(seg_pts)
                else:
                    poly_pts.extend(seg_pts[1:])

            color = cmap(0.3 + 0.5 * i / max(n - 1, 1))
            patch = MplPolygon(poly_pts, closed=True, fc=color,
                               ec='black', lw=0.6, alpha=alpha, zorder=3)
            ax.add_patch(patch)

            cx = sum(p[0] for p in verts) / nv
            cy = sum(p[1] for p in verts) / nv
            ax.text(cx, cy, f'{label_prefix}{i + 1}', fontsize=6,
                    ha='center', va='center', fontweight='bold',
                    color='black', zorder=5)

    _render_faces(stator_faces, stator_cmap, 'S')
    _render_faces(rotor_faces, rotor_cmap, 'R')

    for i, ci in enumerate(independent_circles):
        ax.add_patch(plt.Circle(ci.center, ci.radius, fill=True,
                                fc='lime', ec='black', lw=0.8,
                                alpha=0.4, zorder=3))
        ax.text(ci.center[0], ci.center[1], f'C{i + 1}', fontsize=6,
                ha='center', va='center', fontweight='bold', zorder=5)

    ang_s = math.radians(reference_sector * period_deg)
    ang_e = math.radians((reference_sector + 1) * period_deg)
    r_max = max((ei.r_max for ei in one_period), default=1) * 1.1
    ax.plot([ox, ox + r_max * math.cos(ang_s)],
            [oy, oy + r_max * math.sin(ang_s)], 'r--', lw=0.8, zorder=2)
    ax.plot([ox, ox + r_max * math.cos(ang_e)],
            [oy, oy + r_max * math.sin(ang_e)], 'r--', lw=0.8, zorder=2)

    n_stator = len(stator_faces)
    n_rotor = len(rotor_faces)
    n_circ = len(independent_circles)
    total = n_stator + n_rotor + n_circ

    ax.set_aspect('equal')
    ax.set_title(f'Closed Regions in 1 Period: {total}  '
                 f'(Stator={n_stator}, Rotor={n_rotor}, Circle={n_circ})',
                 fontsize=12)
    ax.grid(True, lw=0.3, alpha=0.5)

    legend_elements = []
    if stator_faces:
        legend_elements.append(Patch(fc=stator_cmap(0.5), alpha=0.45, ec='k', label=f'Stator ({n_stator})'))
    if rotor_faces:
        legend_elements.append(Patch(fc=rotor_cmap(0.5), alpha=0.45, ec='k', label=f'Rotor ({n_rotor})'))
    if independent_circles:
        legend_elements.append(Patch(fc='lime', alpha=0.4, ec='k', label=f'Circle ({n_circ})'))
    if legend_elements:
        ax.legend(handles=legend_elements, loc='best', fontsize=9)

    plt.tight_layout()
    plt.show()

    print(f'\n[plot_closed_regions] 총 {total}개 닫힌 영역 표시')
    print(f'  Stator: {n_stator},  Rotor: {n_rotor},  Circle: {n_circ}')

    return fig, ax, faces_info


def plot_named_half_unit(half_unit_regions: Dict,
                         half_unit: Dict,
                         split: StatorRotorSplit,
                         origin: Tuple[float, float] = (0.0, 0.0),
                         figsize: Tuple = (10, 10)):
    """반슬롯/반극의 네이밍된 영역을 시각화합니다."""
    ox, oy = origin
    fig, axes = plt.subplots(1, 2, figsize=(figsize[0] * 2, figsize[1]))

    for ax_idx, (part, title_str) in enumerate([
            ('stator', f'Half-Slot Stator ({half_unit["half_slot_deg"]:.1f}°)'),
            ('rotor', f'Half-Pole Rotor ({half_unit["half_pole_deg"]:.1f}°)')]):
        ax = axes[ax_idx]
        all_faces = half_unit_regions[f'{part}_faces']
        faces = [fi for fi in all_faces if fi.get('scope') != 'period']
        emap = half_unit_regions[f'{part}_edge_map']

        ents = (half_unit['half_slot_stator'] if part == 'stator'
                else half_unit['half_pole_rotor'])
        for ei in ents:
            xs = [p[0] for p in ei.points]
            ys = [p[1] for p in ei.points]
            if ei.etype == 'LINE':
                ax.plot(xs, ys, color='#888', lw=0.4, zorder=1)
            elif ei.etype == 'ARC' and ei.center and ei.radius:
                ax.add_patch(MplArc(
                    ei.center, 2 * ei.radius, 2 * ei.radius,
                    angle=0, theta1=ei.start_angle, theta2=ei.end_angle,
                    ec='#888', lw=0.4, zorder=1))

        used_names = set()
        for fi in faces:
            _render_face_patch(ax, fi, emap)
            used_names.add(fi.get('name', 'unknown'))
            nv = len(fi['vertices'])
            cx = sum(v[0] for v in fi['vertices']) / nv
            cy = sum(v[1] for v in fi['vertices']) / nv
            label = SHORT_NAMES.get(fi.get('name'), '?')
            fs = 6 if fi['area'] < 50 else 8
            ax.text(cx, cy, label, fontsize=fs, ha='center', va='center',
                    fontweight='bold', zorder=5,
                    bbox=dict(boxstyle='round,pad=0.15', fc='white',
                              alpha=0.7, ec='none'))

        legend_els = [Patch(fc=REGION_COLORS.get(n, '#D0D0D0'), alpha=0.7, ec='k',
                            label=REGION_NAMES.get(n, n))
                      for n in sorted(used_names)]
        ax.legend(handles=legend_els, loc='upper left', fontsize=7)
        ax.set_aspect('equal')
        ax.set_title(title_str, fontsize=11, fontweight='bold')
        ax.grid(True, lw=0.3, alpha=0.4)

    plt.tight_layout()
    plt.show()
    return fig, axes


def plot_reconstructed_named(half_unit: Dict,
                             half_unit_regions: Dict,
                             split: StatorRotorSplit,
                             origin: Tuple[float, float] = (0.0, 0.0),
                             coverage: str = 'period',
                             n_poles: Optional[int] = None,
                             n_slots: Optional[int] = None,
                             period_deg: Optional[float] = None,
                             figsize: Tuple = (12, 12)):
    """반슬롯/반극 영역을 mirror + circular pattern으로 재구성하여 시각화."""
    ox, oy = origin
    half_slot_deg = half_unit['half_slot_deg']
    half_pole_deg = half_unit['half_pole_deg']
    slot_pitch = half_unit['slot_pitch_deg']
    pole_pitch = half_unit['pole_pitch_deg']
    ref_start = half_unit['ref_angle_start']

    if coverage == 'full':
        target_deg = 360.0
    elif coverage == 'period':
        target_deg = period_deg if period_deg else 90.0
    else:
        target_deg = float(coverage)

    n_slots_to_build = max(1, round(target_deg / slot_pitch))
    n_poles_to_build = max(1, round(target_deg / pole_pitch))
    n_periods_to_build = max(1, round(target_deg / period_deg)) if period_deg else 1

    fig, ax = plt.subplots(figsize=figsize)

    def _draw_transformed_face(fi, transform_fn, emap=None):
        if emap is not None:
            render_pts = _get_face_render_pts(fi, emap)
        elif '_render_pts' in fi:
            render_pts = fi['_render_pts']
        else:
            render_pts = fi['vertices']
        transformed_pts = [transform_fn(p[0], p[1]) for p in render_pts]
        name = fi.get('name', 'unknown')
        color = REGION_COLORS.get(name, '#D0D0D0')
        patch = MplPolygon(transformed_pts, closed=True, fc=color,
                           ec='black', lw=0.4, alpha=0.65, zorder=3)
        ax.add_patch(patch)

    def _make_mirror_fn(axis_deg):
        rad = math.radians(axis_deg)
        def fn(x, y):
            return mirror_point(x, y, rad, ox, oy)
        return fn

    def _make_rotate_fn(angle_deg):
        rad = math.radians(angle_deg)
        def fn(x, y):
            return rotate_point(x, y, rad, ox, oy)
        return fn

    s_faces = half_unit_regions['stator_faces']
    r_faces = half_unit_regions['rotor_faces']
    s_emap = half_unit_regions['stator_edge_map']
    r_emap = half_unit_regions['rotor_edge_map']

    s_half = [fi for fi in s_faces if fi.get('scope') == 'half']
    s_period = [fi for fi in s_faces if fi.get('scope') == 'period']
    r_half = [fi for fi in r_faces if fi.get('scope') == 'half']
    r_period = [fi for fi in r_faces if fi.get('scope') == 'period']

    mirror_s_axis = ref_start + half_slot_deg
    mirror_r_axis = ref_start + half_pole_deg

    # 고정자 반슬롯
    for i in range(n_slots_to_build):
        rot_angle = i * slot_pitch
        for fi in s_half:
            if i == 0:
                _render_face_patch(ax, fi, s_emap, alpha=0.65)
            else:
                _draw_transformed_face(fi, _make_rotate_fn(rot_angle), s_emap)
            if i == 0:
                mirror_fn = _make_mirror_fn(mirror_s_axis)
            else:
                def mirror_then_rotate(x, y, _mf=_make_mirror_fn(mirror_s_axis),
                                       _rf=_make_rotate_fn(rot_angle)):
                    mx, my = _mf(x, y)
                    return _rf(mx, my)
                mirror_fn = mirror_then_rotate
            _draw_transformed_face(fi, mirror_fn, s_emap)

    # 고정자 광역
    for p in range(n_periods_to_build):
        rot_angle = p * period_deg
        for fi in s_period:
            if p == 0:
                _render_face_patch(ax, fi, s_emap, alpha=0.65)
            else:
                _draw_transformed_face(fi, _make_rotate_fn(rot_angle), s_emap)

    # 회전자 반극
    for i in range(n_poles_to_build):
        rot_angle = i * pole_pitch
        for fi in r_half:
            if i == 0:
                _render_face_patch(ax, fi, r_emap, alpha=0.65)
            else:
                _draw_transformed_face(fi, _make_rotate_fn(rot_angle), r_emap)
            if i == 0:
                mirror_fn = _make_mirror_fn(mirror_r_axis)
            else:
                def mirror_then_rotate(x, y, _mf=_make_mirror_fn(mirror_r_axis),
                                       _rf=_make_rotate_fn(rot_angle)):
                    mx, my = _mf(x, y)
                    return _rf(mx, my)
                mirror_fn = mirror_then_rotate
            _draw_transformed_face(fi, mirror_fn, r_emap)

    # 회전자 광역
    for p in range(n_periods_to_build):
        rot_angle = p * period_deg
        for fi in r_period:
            if p == 0:
                _render_face_patch(ax, fi, r_emap, alpha=0.65)
            else:
                _draw_transformed_face(fi, _make_rotate_fn(rot_angle), r_emap)

    # 동심원
    for ei in half_unit['concentric_circles']:
        if ei.etype == 'CIRCLE' and ei.center and ei.radius:
            ax.add_patch(plt.Circle(ei.center, ei.radius, fill=False,
                                    ec='#2ecc71', lw=0.8, zorder=2))
        elif ei.etype == 'ARC' and ei.center and ei.radius:
            ax.add_patch(MplArc(
                ei.center, 2 * ei.radius, 2 * ei.radius,
                angle=0, theta1=ref_start, theta2=ref_start + target_deg,
                ec='#2ecc71', lw=0.8, zorder=2))

    concentric_r = sorted(set(
        round(ei.radius, 2)
        for ei in split.stator_entities + split.rotor_entities
        if ei.etype in ('CIRCLE', 'ARC') and ei.center
        and math.hypot(ei.center[0] - ox, ei.center[1] - oy) < 1e-3
        and ei.radius))
    r_max = max(concentric_r) * 1.05 if concentric_r else 130

    if target_deg < 360:
        a1 = math.radians(ref_start)
        a2 = math.radians(ref_start + target_deg)
        ax.plot([ox, ox + r_max * math.cos(a1)], [oy, oy + r_max * math.sin(a1)],
                'r--', lw=0.6, alpha=0.7)
        ax.plot([ox, ox + r_max * math.cos(a2)], [oy, oy + r_max * math.sin(a2)],
                'r--', lw=0.6, alpha=0.7)

    all_faces = s_faces + r_faces
    used_names = sorted(set(fi.get('name', 'unknown') for fi in all_faces))
    legend_elements = [Patch(fc=REGION_COLORS.get(n, '#D0D0D0'), alpha=0.7, ec='k',
                             label=REGION_NAMES.get(n, n))
                       for n in used_names]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.9)

    margin = r_max * 0.08
    ax.set_xlim(ox - r_max - margin, ox + r_max + margin)
    ax.set_ylim(oy - r_max - margin, oy + r_max + margin)

    ax.set_aspect('equal')
    ax.set_title(f'Named Regions — {coverage} ({target_deg:.0f}°)\n'
                 f'{n_slots_to_build} slots × {n_poles_to_build} poles',
                 fontsize=12, fontweight='bold')
    ax.grid(True, lw=0.3, alpha=0.4)
    plt.tight_layout()
    plt.show()
    return fig, ax
