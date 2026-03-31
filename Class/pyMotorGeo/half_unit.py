"""
pyMotorGeo.half_unit
===================

모터 단면 데이터의 최소 반복 단위(Minimum Repeating Unit)인 Half-Pole 및 Half-Slot을 
추출하고, 이를 거울 반사(Mirroring) 및 원형 배열(Circular Array)을 통해 
전체 모델이나 주기 모델로 복원하는 기능들을 제공합니다.
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional

from core import EntityInfo


def detect_circular_array_pattern(entities: List[EntityInfo],
                                   origin: Tuple[float, float] = (0.0, 0.0),
                                   min_repeats: int = 4) -> Dict:
    """엔티티 집합 내에 존재하는 원형 배열(Circular Array) 패턴을 감지하여 극수를 추정합니다.

    각 엔티티의 중심 이격 반경과 타입을 기준으로 '시그니처'를 생성하여 그룹화합니다. 
    동일한 시그니처를 가진 그룹들이 원형 배열을 이룰 때, 각도 사이의 간격(Pitch)을 계산합니다.
    중앙값을 통해 모터의 극수(Pole)나 슬롯수를 1차적으로 추정하는 휴리스틱 기반 탐지기입니다.

    Args:
        entities (List[EntityInfo]): 패턴을 분석할 대상 엔티티 리스트.
        origin (Tuple[float, float]): 원형 배열의 기준 중심점. 기본값은 (0.0, 0.0).
        min_repeats (int): 패턴으로 간주하기 위한 최소 반복 등장 횟수. 기본값은 4.

    Returns:
        Dict: 다음 정보를 포함하는 딕셔너리:
            - 'has_pattern' (bool): 원형 배열 패턴의 감지 여부
            - 'n_poles' (int): 추정된 극수 (또는 슬롯수)
            - 'pole_pitch_deg' (float): 추정된 단일 주기(극 피치) 각도 (도)
            - 'entity_groups' (dict): 패턴에 부합하는 시그니처별 엔티티들의 리스트
            - 'angular_positions' (dict): 시그니처별 발견된 위상 각도 리스트
            - 'all_groups' (dict): 필터링 전의 모든 시그니처별 엔티티 및 각도 정보
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
    """반극(Half-Pole) 및 반슬롯(Half-Slot)을 추출하는 공통 코어 함수입니다.

    지정된 `reference_angle`을 기준으로 전체 피치의 절반(half_pitch)에 해당하는 각도 
    섹터 내부의 엔티티들을 모두 수집합니다. 
    로터 및 스테이터의 형상이 가진 대칭성(Mirror Symmetry)을 이용하여 기하 중복을 제거합니다.

    Args:
        entities (List[EntityInfo]): 필터링 대상이 될 원본 엔티티 리스트.
        origin (Tuple[float, float]): 모터 극좌표계의 원점.
        full_pitch_deg (float): 로터의 1극 피치 / 스테이터의 1슬롯 전체 피치 각도.
        reference_angle (float): 엔티티를 수집할 부채꼴의 시작 기준 각도. 기본값은 0.0.
        normalize_to_zero (bool): 추출된 엔티티들을 물리적 x축(0도)을 기준으로 회전하여 반환할지 여부.
        angle_tol (float): 경계선상에 걸친 요소 포함을 여부를 판단할 논리적 마진 각도.

    Returns:
        Dict: 분석된 엔티티 및 속성이 담긴 딕셔너리
            - 'half_entities' (List[Dict]): 추출된 원본 엔티티와 상대각도 기록 객체들.
            - 'normalized_entities' (List[EntityInfo]): x축에 정렬된 새로운 엔티티 리스트 (옵션 적용시).
            - 'concentric_arcs' (List[EntityInfo]): 각도 판별에서 예외 처리된 동심원 및 에어갭 궤적들.
            - 'half_pitch_deg' (float): 산출된 반극/반슬롯의 섹터 각도 사이즈.
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
    """단일 점의 각도가 호(Sector)의 시작과 끝 각도 내에 존재하는지(포함 여부)를 검증합니다.
    360도를 넘어가는 구간이 겹치는 경우(wrap-around)를 처리합니다.
    """
    a = angle_deg % 360
    s = start_deg % 360
    e = end_deg % 360
    if s <= e:
        return s <= a <= e
    return a >= s or a <= e


def _angle_in_arc(angle_deg: float, start_deg: float, end_deg: float) -> bool:
    """호(Arc)의 각도 구간 안에 주어진 각도가 위치하는지 판별하는 래퍼 함수입니다."""
    a = angle_deg % 360
    s = start_deg % 360
    e = end_deg % 360
    if s <= e:
        return s <= a <= e
    return a >= s or a <= e


def _arc_overlaps_sector(ei: EntityInfo, start_deg: float, end_deg: float,
                         origin: Tuple[float, float]) -> bool:
    """기하 엔티티(주로 호 또는 선분) 중 일부가 주어진 각도 섹터 안에 포함되어 교차하는지 검사합니다.
    시작점, 끝점 또는 중간점이 하나라도 섹터의 내부 궤적에 걸치면 True를 반환합니다.
    """
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
    """동심원(CIRCLE) 또는 호(ARC)를 모터 해석의 1극/1슬롯 각도 구간만큼으로 클리핑(수정)하여 
    시작점과 끝점을 재생성한 새로운 EntityInfo 사본을 반환합니다.

    단일 모터 주기 범위를 벗어나는 외부 객체라면 None을 반환합니다. 이 함수는 연속된 에어갭의 
    동심원이 다른 형상과 겹치지 않게 해석 주기 단위로 쪼개기 위해 사용됩니다.

    Args:
        ei (EntityInfo): 자를 대상인 원/호 객체.
        sect_start (float): 남길 섹터의 시작 각도.
        sect_end (float): 남길 섹터의 종료 각도.
        origin (Tuple[float, float]): 원점 좌표.

    Returns:
        Optional[EntityInfo]: 클리핑 처리된 새로운 ARC 객체. 허용 범위를 완전히 벗어나면 None.
    """
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
    """원형 구조물(주기 모델)의 열린 양측 단면 경계를 닫기 위해 원점으로부터
    특정 방위각을 향해 일직선으로 뻗어나가는 인위적인 선분(Boundary Line)을 생성합니다.

    Args:
        r0 (float): 선분이 시작하는 내부 원 반경.
        r1 (float): 선분이 끝나는 외부 원 반경.
        angle_deg (float): 선의 도달 궤적이 되는 방위각.
        origin (Tuple[float, float]): 극좌표 기준이 되는 중심점의 좌표.
        layer (str): 가상으로 생성된 선분이 소속될 이름/레이어 속성.

    Returns:
        EntityInfo: 경계선 역할을 수행하기 위해 인위로 생성된 `LINE` 엔티티 객체.
    """
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
    """동심원으로 식별된 호들의 반경 간격 사이를 직교하며 메워주는 시각적/물리적 분리 경계선들을 생성합니다.
    주로 스테이터와 로터 혹은 다양한 컴포넌트 간의 레이어를 닫힌 영역(Planar Graph)으로 완성하기 위해 사용합니다.

    Args:
        concentric_arcs (List[EntityInfo]): 동심원 기하 특성을 가진 에어갭/샤프트 호의 리스트.
        sect_start (float): 동심원 부채꼴 조각이 시작되는 각도.
        sect_end (float): 동심원 부채꼴 조각이 닫히는 끝 각도.
        origin (Tuple[float, float]): 원 중심 좌표.
        layer (str): 가상 경계들이 편입될 임시 레이어 식별자. 기본값은 '_HALF_RADIAL_'.

    Returns:
        List[EntityInfo]: 생성된 일련의 `LINE` 엔티티들. 반경 그룹이 2개 미만이면 즉 열린 영역이 불가능하면 빈 리스트 반환.
    """
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
    """회전자(Rotor)의 최소 반복 단위인 **반극(Half-Pole)** 기계를 구성하는 엔티티들을 필터링 추출합니다.
    
    1극 내에서도 자석이나 공극 배리어는 좌우 대칭성(Mirror Symmetry)을 가지므로 전체 모델을 해석하기 위한 
    가장 작은 조각 단위로 사용할 수 있도록 `pole_pitch_deg / 2` 각도로 절반을 슬라이싱합니다.

    Args:
        entities (List[EntityInfo]): 로터로 분류된 전체 엔티티 리스트.
        origin (Tuple[float, float]): 기준이 되는 로터 회전 중심.
        pole_pitch_deg (float): 1극(Pole) 기계 각도. 미제공시 내부적으로 패턴 탐지를 통해 자동 추정됨.
        reference_angle (float): 반극 슬라이스 시작 축. 미제공시 자동 추정됨.
        normalize_to_zero (bool): 추출된 원본 조각들을 물리적 0도 좌표축으로 밀착(회전)시킬지 여부. 기본값은 True.

    Returns:
        Dict: 분석 및 변환된 반극 컴포넌트들을 담은 딕셔너리 리스트 등
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
    partial_arcs = []
    for ei in result['concentric_arcs']:
        clipped = _clip_concentric_arc(ei, sector_start, sector_end, origin)
        if clipped is not None:
            span = (clipped.end_angle - clipped.start_angle) % 360 if clipped.end_angle is not None else 0
            if abs(span - half_pitch) < 1e-2 or ei.etype == 'CIRCLE':
                processed_arcs.append(clipped)
            else:
                partial_arcs.append(clipped)
    result['concentric_arcs'] = processed_arcs

    if partial_arcs:
        rot_rad = math.radians(-reference_angle) if normalize_to_zero else 0.0
        cos_r, sin_r = math.cos(rot_rad), math.sin(rot_rad)
        ox, oy = origin
        for arc in partial_arcs:
            new_points = []
            for px, py in arc.points:
                dx, dy = px - ox, py - oy
                new_points.append((ox + dx * cos_r - dy * sin_r,
                                   oy + dx * sin_r + dy * cos_r))
            new_center = None
            if arc.center:
                dx, dy = arc.center[0] - ox, arc.center[1] - oy
                new_center = (ox + dx * cos_r - dy * sin_r,
                              oy + dx * sin_r + dy * cos_r)
            new_sa = (arc.start_angle - reference_angle) if (arc.start_angle is not None and normalize_to_zero) else arc.start_angle
            new_ea = (arc.end_angle - reference_angle) if (arc.end_angle is not None and normalize_to_zero) else arc.end_angle
            new_arc = EntityInfo(
                etype=arc.etype, layer=arc.layer, points=new_points,
                radius=arc.radius, center=new_center,
                start_angle=new_sa, end_angle=new_ea,
                is_closed=arc.is_closed, raw=None
            )
            result['normalized_entities'].append(new_arc)

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
    """고정자(Stator)의 최소 반복 단위인 **반슬롯(Half-Slot)** 기하 정보를 추출합니다.
    
    내부적으로 `_extract_half_entities`를 사용하여 `reference_angle`부터 `slot_pitch_deg / 2` 
    영역 내에 존재하는 모든 선분과 호를 분리해 수집하여 하나의 단위 섹터를 형성합니다. 이는 고정자 
    요소의 주기성과 거울 대칭성(Mirror Symmetry)을 나타내는 가장 기초적인 공간 데이터입니다.

    Args:
        entities (List[EntityInfo]): 분리해 낸 고정자 전체 요소 리스트.
        origin (Tuple[float, float]): 원형 구조의 회전 중심.
        slot_pitch_deg (float): 단일 슬롯이 차지하는 피치 각도 (360 / n_slots).
        n_slots (int): 고정자의 전체 슬롯 개수.
        reference_angle (float): 반슬롯 절단의 기준 축 각도. 기본값은 0.0.
        normalize_to_zero (bool): 단면을 x축 양의 방향(0도)부터 시작하도록 회전 정렬할지 여부. 기본값은 True.

    Returns:
        Dict: 반슬롯 구성 요소들과 대칭 정보가 기록된 출력 딕셔너리:
            - 'half_pitch_deg': 추출된 반슬롯 각도(절반 피치)
            - 'mirror_axis_deg': 대칭면(Mirroring) 생성을 위한 기준선 각도
            - 'normalized_entities': 정규화 처리가 된 도면 요소 리스트
            - 'concentric_arcs': 원점에 대한 동심원(또는 에어갭 경계)으로 잘라낸 특수 객체 리스트
            - 'n_slots': 계산에 사용된 슬롯 수
    """
    if slot_pitch_deg is None:
        if n_slots and n_slots > 0:
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

    sector_start = reference_angle
    sector_end = reference_angle + half_pitch

    processed_arcs = []
    partial_arcs = []
    for ei in result['concentric_arcs']:
        clipped = _clip_concentric_arc(ei, sector_start, sector_end, origin)
        if clipped is not None:
            span = (clipped.end_angle - clipped.start_angle) % 360 if clipped.end_angle is not None else 0
            if abs(span - half_pitch) < 1e-2 or ei.etype == 'CIRCLE':
                processed_arcs.append(clipped)
            else:
                partial_arcs.append(clipped)
    result['concentric_arcs'] = processed_arcs

    if partial_arcs:
        rot_rad = math.radians(-reference_angle) if normalize_to_zero else 0.0
        cos_r, sin_r = math.cos(rot_rad), math.sin(rot_rad)
        ox, oy = origin
        for arc in partial_arcs:
            new_points = []
            for px, py in arc.points:
                dx, dy = px - ox, py - oy
                new_points.append((ox + dx * cos_r - dy * sin_r,
                                   oy + dx * sin_r + dy * cos_r))
            new_center = None
            if arc.center:
                dx, dy = arc.center[0] - ox, arc.center[1] - oy
                new_center = (ox + dx * cos_r - dy * sin_r,
                              oy + dx * sin_r + dy * cos_r)
            new_sa = (arc.start_angle - reference_angle) if (arc.start_angle is not None and normalize_to_zero) else arc.start_angle
            new_ea = (arc.end_angle - reference_angle) if (arc.end_angle is not None and normalize_to_zero) else arc.end_angle
            new_arc = EntityInfo(
                etype=arc.etype, layer=arc.layer, points=new_points,
                radius=arc.radius, center=new_center,
                start_angle=new_sa, end_angle=new_ea,
                is_closed=arc.is_closed, raw=None
            )
            result['normalized_entities'].append(new_arc)
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
                          include_concentric: bool = True,
                          include_boundaries: bool = True) -> List[EntityInfo]:
    """
    반극/반슬롯에서 mirror + circular array로 기하를 재구성합니다.
    
    Parameters
    ----------
    include_boundaries : bool, default True
        전체 재구성 시 concentric_radials (경계선)를 포함할지 여부.
        False로 하면 face 탐지 시 분절 방지.
    """
    from core import rotate_entity, mirror_entity

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
        if include_boundaries:
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
