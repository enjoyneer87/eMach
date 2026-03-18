"""
pyMotorGeo.half_unit
===================
Half-unit (half-pole / half-slot) extraction and reconstruction utilities.
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional

from .core import EntityInfo


def detect_circular_array_pattern(entities: List[EntityInfo],
                                   origin: Tuple[float, float] = (0.0, 0.0),
                                   min_repeats: int = 4) -> Dict:
    """
    엔티티들에서 Circular Array 패턴을 감지합니다.

    Returns
    -------
    dict with:
        - 'has_pattern': bool - 패턴 감지 여부
        - 'n_poles': int - 추정 극수
        - 'pole_pitch_deg': float - 극 피치 (도)
        - 'entity_groups': dict - 시그니처별 엔티티 그룹
        - 'angular_positions': dict - 그룹별 각도 위치
    """
    ox, oy = origin

    def get_signature(ei):
        radii = [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]
        r_min, r_max = min(radii), max(radii)
        r_bin = round((r_min + r_max) / 2, 0)
        return f"{ei.etype}_{r_bin}"

    groups = {}
    for ei in entities:
        sig = get_signature(ei)
        angles = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360 for p in ei.points]
        avg_angle = np.mean(angles)
        groups.setdefault(sig, []).append({'entity': ei, 'angle': avg_angle})

    repeating_groups = {k: v for k, v in groups.items() if len(v) >= min_repeats}
    if not repeating_groups:
        return {'has_pattern': False, 'n_poles': 0, 'pole_pitch_deg': 0}

    pitches = []
    angular_positions = {}
    for sig, items in repeating_groups.items():
        angles = sorted([item['angle'] for item in items])
        angular_positions[sig] = angles
        if len(angles) >= 2:
            diffs = []
            for i in range(len(angles) - 1):
                diffs.append(angles[i + 1] - angles[i])
            diffs.append(360 - angles[-1] + angles[0])
            avg_pitch = np.median(diffs)
            pitches.append(avg_pitch)

    if not pitches:
        return {'has_pattern': False, 'n_poles': 0, 'pole_pitch_deg': 0}

    pole_pitch = np.median(pitches)
    n_poles = int(round(360 / pole_pitch))

    return {
        'has_pattern': True,
        'n_poles': n_poles,
        'pole_pitch_deg': pole_pitch,
        'entity_groups': {k: [item['entity'] for item in v] for k, v in repeating_groups.items()},
        'angular_positions': angular_positions,
        'all_groups': groups,
    }


# ═══════════════════════════════════════════════════════════════
# Half-Unit 추출 함수 (최소 반복 단위)
# ═══════════════════════════════════════════════════════════════

def _extract_half_entities(entities: List[EntityInfo],
                           origin: Tuple[float, float],
                           full_pitch_deg: float,
                           reference_angle: float = 0.0,
                           normalize_to_zero: bool = True,
                           angle_tol: float = 0.05) -> Dict:
    """
    엔티티에서 [reference_angle, reference_angle + full_pitch/2] 범위를 추출.
    반극/반슬롯 공통 로직.

    Returns
    -------
    dict : half_entities, normalized_entities, concentric_arcs, half_pitch_deg
    """
    ox, oy = origin
    half_pitch = full_pitch_deg / 2.0
    ang_start = reference_angle

    half_entities = []
    concentric_arcs = []

    for ei in entities:
        # 동심원/호(원점 중심) → 별도 보관
        if ei.etype in ('CIRCLE', 'ARC') and ei.center:
            cx, cy = ei.center
            if math.hypot(cx - ox, cy - oy) < 1e-3:
                concentric_arcs.append(ei)
                continue

        if not ei.points:
            continue

        angles = [math.degrees(math.atan2(p[1] - oy, p[0] - ox)) % 360
                  for p in ei.points]
        avg_angle = float(np.mean(angles))

        a_rel = (avg_angle - ang_start + 360) % 360
        if a_rel <= half_pitch + angle_tol:
            half_entities.append({
                'entity': ei,
                'original_angle': avg_angle,
                'relative_angle': a_rel,
            })

    normalized = []
    if normalize_to_zero and half_entities:
        rot_rad = math.radians(-reference_angle)
        cos_r, sin_r = math.cos(rot_rad), math.sin(rot_rad)

        for item in half_entities:
            ei = item['entity']
            new_points = []
            for px, py in ei.points:
                dx, dy = px - ox, py - oy
                new_points.append((ox + dx * cos_r - dy * sin_r,
                                   oy + dx * sin_r + dy * cos_r))

            new_center = None
            if ei.center:
                dx, dy = ei.center[0] - ox, ei.center[1] - oy
                new_center = (ox + dx * cos_r - dy * sin_r,
                              oy + dx * sin_r + dy * cos_r)

            new_sa = (ei.start_angle - reference_angle) if ei.start_angle is not None else None
            new_ea = (ei.end_angle - reference_angle) if ei.end_angle is not None else None

            new_ei = EntityInfo(
                etype=ei.etype, layer=ei.layer, points=new_points,
                radius=ei.radius, center=new_center,
                start_angle=new_sa, end_angle=new_ea,
                is_closed=ei.is_closed, raw=None
            )
            normalized.append(new_ei)

    return {
        'half_entities': half_entities,
        'normalized_entities': normalized,
        'concentric_arcs': concentric_arcs,
        'half_pitch_deg': half_pitch,
    }


def _angle_in_sector(angle_deg: float, start_deg: float, end_deg: float) -> bool:
    a = angle_deg % 360
    s = start_deg % 360
    e = end_deg % 360
    if s <= e:
        return s <= a <= e
    return a >= s or a <= e


def _angle_in_arc(angle_deg: float, start_deg: float, end_deg: float) -> bool:
    a = angle_deg % 360
    s = start_deg % 360
    e = end_deg % 360
    if s <= e:
        return s <= a <= e
    return a >= s or a <= e


def _arc_overlaps_sector(ei: EntityInfo, start_deg: float, end_deg: float,
                         origin: Tuple[float, float]) -> bool:
    if ei.points:
        ox, oy = origin
        for px, py in ei.points:
            ang = math.degrees(math.atan2(py - oy, px - ox)) % 360
            if _angle_in_sector(ang, start_deg, end_deg):
                return True
    if ei.start_angle is None or ei.end_angle is None:
        return False
    if _angle_in_sector(ei.start_angle, start_deg, end_deg):
        return True
    if _angle_in_sector(ei.end_angle, start_deg, end_deg):
        return True
    if _angle_in_arc(start_deg, ei.start_angle, ei.end_angle):
        return True
    if _angle_in_arc(end_deg, ei.start_angle, ei.end_angle):
        return True
    return False


def _clip_concentric_arc(ei: EntityInfo,
                          sect_start: float,
                          sect_end: float,
                          origin: Tuple[float, float]) -> Optional[EntityInfo]:
    """동심 ARC를 섹터 범위로 클리핑하여 새 EntityInfo를 반환.
    완전히 범위 밖이면 None."""
    if ei.etype == 'CIRCLE':
        cx, cy = ei.center
        r = ei.radius
        new_arc = EntityInfo(
            etype='ARC', layer=ei.layer, points=[],
            radius=r, center=ei.center,
            start_angle=sect_start, end_angle=sect_end,
            is_closed=False, raw=None,
        )
        n_pts = max(3, int((sect_end - sect_start) / 2))
        pts = []
        for j in range(n_pts + 1):
            a = math.radians(sect_start + (sect_end - sect_start) * j / n_pts)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        new_arc.points = pts
        return new_arc

    if ei.etype != 'ARC' or ei.radius is None or ei.center is None:
        return ei

    arc_s = ei.start_angle if ei.start_angle is not None else 0.0
    arc_e = ei.end_angle if ei.end_angle is not None else 360.0
    arc_s = arc_s % 360
    arc_e = arc_e % 360
    if arc_e <= arc_s:
        arc_e += 360
    s_s = sect_start % 360
    s_e = sect_end % 360
    if s_e <= s_s:
        s_e += 360

    clipped_s = max(arc_s, s_s)
    clipped_e = min(arc_e, s_e)
    if clipped_e <= clipped_s + 0.01:
        return None

    cx, cy = ei.center
    r = ei.radius
    new_arc = EntityInfo(
        etype='ARC', layer=ei.layer, points=[],
        radius=r, center=ei.center,
        start_angle=clipped_s % 360, end_angle=clipped_e % 360,
        is_closed=False, raw=None,
    )
    span = clipped_e - clipped_s
    n_pts = max(3, int(span / 2))
    pts = []
    for j in range(n_pts + 1):
        a = math.radians(clipped_s + span * j / n_pts)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    new_arc.points = pts
    return new_arc


def _make_radial_line(r0: float, r1: float, angle_deg: float,
                       origin: Tuple[float, float], layer: str) -> EntityInfo:
    ox, oy = origin
    rad = math.radians(angle_deg)
    x0 = ox + r0 * math.cos(rad)
    y0 = oy + r0 * math.sin(rad)
    x1 = ox + r1 * math.cos(rad)
    y1 = oy + r1 * math.sin(rad)
    return EntityInfo(
        etype='LINE', layer=layer,
        points=[(x0, y0), (x1, y1)],
        radius=None, center=None,
        start_angle=None, end_angle=None,
        is_closed=False, raw=None,
    )


def _make_concentric_radials(concentric_arcs: List[EntityInfo],
                             sect_start: float,
                             sect_end: float,
                             origin: Tuple[float, float],
                             layer: str = '_HALF_RADIAL_') -> List[EntityInfo]:
    radii = sorted({float(ei.radius) for ei in concentric_arcs if ei.radius is not None})
    if len(radii) < 2:
        return []

    radials = []
    for ang in (sect_start, sect_end):
        for i in range(len(radii) - 1):
            r0 = radii[i]
            r1 = radii[i + 1]
            radials.append(_make_radial_line(r0, r1, ang, origin, layer))
    return radials


def extract_half_pole_entities(entities: List[EntityInfo],
                               origin: Tuple[float, float] = (0.0, 0.0),
                               pole_pitch_deg: float = None,
                               reference_angle: float = None,
                               normalize_to_zero: bool = True) -> Dict:
    """
    반극(Half-Pole) 엔티티 추출 — 로터 최소 반복 단위.

    Returns
    -------
    dict:
        - half_entities
        - normalized_entities
        - concentric_arcs
        - concentric_radials
        - half_pitch_deg
        - pole_pitch_deg
        - n_poles
        - mirror_axis_deg
        - reference_angle
    """
    if pole_pitch_deg is None:
        pattern = detect_circular_array_pattern(entities, origin)
        if pattern['has_pattern']:
            pole_pitch_deg = pattern['pole_pitch_deg']
        else:
            pole_pitch_deg = 30.0

    n_poles = int(round(360.0 / pole_pitch_deg))
    half_pitch = pole_pitch_deg / 2.0

    if reference_angle is None:
        reference_angle = 0.0

    result = _extract_half_entities(
        entities, origin, pole_pitch_deg, reference_angle, normalize_to_zero
    )

    sector_start = reference_angle
    sector_end = reference_angle + half_pitch
    result['concentric_arcs'] = [
        ei for ei in result['concentric_arcs']
        if _arc_overlaps_sector(ei, sector_start, sector_end, origin)
    ]

    processed_arcs = []
    for ei in result['concentric_arcs']:
        clipped = _clip_concentric_arc(ei, sector_start, sector_end, origin)
        if clipped is not None:
            processed_arcs.append(clipped)
    result['concentric_arcs'] = processed_arcs

    result['concentric_radials'] = _make_concentric_radials(
        result['concentric_arcs'], sector_start, sector_end, origin
    )

    result.update({
        'pole_pitch_deg': pole_pitch_deg,
        'n_poles': n_poles,
        'reference_angle': reference_angle,
        'mirror_axis_deg': half_pitch,
    })
    return result


def extract_half_slot_entities(entities: List[EntityInfo],
                               origin: Tuple[float, float] = (0.0, 0.0),
                               slot_pitch_deg: float = None,
                               n_slots: int = None,
                               reference_angle: float = None,
                               normalize_to_zero: bool = True) -> Dict:
    """
    반슬롯(Half-Slot) 엔티티 추출 — 스테이터 최소 반복 단위.
    """
    from .analysis import count_slots as _count_slots

    if slot_pitch_deg is None:
        if n_slots is not None:
            slot_pitch_deg = 360.0 / n_slots
        else:
            _ns = _count_slots(entities, origin)
            if _ns and _ns > 0:
                n_slots = _ns
                slot_pitch_deg = 360.0 / n_slots
            else:
                slot_pitch_deg = 10.0

    if n_slots is None:
        n_slots = int(round(360.0 / slot_pitch_deg))

    half_pitch = slot_pitch_deg / 2.0

    if reference_angle is None:
        reference_angle = 0.0

    result = _extract_half_entities(
        entities, origin, slot_pitch_deg, reference_angle, normalize_to_zero
    )

    stator_outer_r = None
    circle_radii = [ei.radius for ei in result['concentric_arcs'] if ei.etype == 'CIRCLE' and ei.radius]
    if circle_radii:
        stator_outer_r = max(circle_radii)

    processed_arcs = []
    for ei in result['concentric_arcs']:
        if ei.etype == 'ARC':
            if stator_outer_r and abs(ei.radius - stator_outer_r) < 1e-2:
                new_arc = EntityInfo(
                    etype='ARC',
                    layer=ei.layer,
                    points=[],
                    radius=ei.radius,
                    center=ei.center,
                    start_angle=reference_angle,
                    end_angle=reference_angle + half_pitch,
                    raw=None,
                )
                cx, cy = new_arc.center
                r = new_arc.radius
                n_pts = max(3, int(half_pitch / 2))
                pts = []
                for j in range(n_pts + 1):
                    a = math.radians(reference_angle + half_pitch * j / n_pts)
                    pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
                new_arc.points = pts
                processed_arcs.append(new_arc)
            else:
                processed_arcs.append(ei)
        else:
            processed_arcs.append(ei)
    result['concentric_arcs'] = processed_arcs
    result.update({
        'slot_pitch_deg': slot_pitch_deg,
        'n_slots': n_slots,
        'reference_angle': reference_angle,
        'mirror_axis_deg': half_pitch,
    })
    return result


def reconstruct_from_half(half_result: Dict,
                          origin: Tuple[float, float] = (0.0, 0.0),
                          n_repeats: int = 1,
                          include_concentric: bool = True) -> List[EntityInfo]:
    """
    반극/반슬롯에서 mirror + circular array로 기하를 재구성합니다.
    """
    from .core import rotate_entity, mirror_entity

    half_ents = half_result['normalized_entities']
    mirror_axis = half_result['mirror_axis_deg']
    full_pitch = mirror_axis * 2

    one_unit = list(half_ents)
    for ei in half_ents:
        mirrored = mirror_entity(ei, mirror_axis, origin)
        one_unit.append(mirrored)

    reconstructed = []
    for i in range(n_repeats):
        rot_deg = i * full_pitch
        for ei in one_unit:
            if i == 0:
                reconstructed.append(ei)
            else:
                reconstructed.append(rotate_entity(ei, rot_deg, origin))

    if include_concentric:
        for ei in half_result.get('concentric_radials', []):
            if ei.etype in ('LINE', 'ARC', 'CIRCLE'):
                for i in range(n_repeats):
                    rot_deg = i * full_pitch
                    if i == 0:
                        reconstructed.append(ei)
                    else:
                        reconstructed.append(rotate_entity(ei, rot_deg, origin))
        for ei in half_result.get('concentric_arcs', []):
            if ei.etype == 'CIRCLE':
                reconstructed.append(ei)
            elif ei.etype == 'ARC':
                total_deg = n_repeats * full_pitch
                new_arc = EntityInfo(
                    etype='ARC', layer=ei.layer, points=[],
                    radius=ei.radius, center=ei.center,
                    start_angle=0, end_angle=min(total_deg, 360),
                    is_closed=False, raw=None
                )
                cx, cy = new_arc.center
                r = new_arc.radius
                n_pts = max(3, int(total_deg / 2))
                pts = []
                for j in range(n_pts + 1):
                    a = math.radians(total_deg * j / n_pts)
                    pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
                new_arc.points = pts
                reconstructed.append(new_arc)

    return reconstructed
