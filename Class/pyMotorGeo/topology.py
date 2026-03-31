"""
pyMotorGeo.topology
===================

회전자(Rotor)의 전자기적 배치 형태(Topology)를 분석하고 분류하는 모듈입니다.

회전자의 구조는 제조 방식(표면 자석, 내부 자석, 동기식 등)과 플럭스 배리어(Flux Barrier) 배치에 따라 
SPM(Surface Permanent Magnet), IPM(Interior Permanent Magnet), SynRM(Synchronous Reluctance), 
PMa-SynRM(Permanent Magnet Assisted Synchronous Reluctance) 등으로 분류됩니다.

주요 함수
---------
- detect_circular_array_pattern      : 엔티티 배열에서 회전자 극(Pole) 반복 주기 검출
- extract_single_pole_entities       : 한 극 내의 엔티티들을 추출 및 분류(자석/코어/배리어)
- extract_single_slot_entities       : 한 슬롯(고정자) 내 엔티티 추출 및 구성 분석
- classify_pole_topology             : 극 내 자석/배리어 배치 패턴으로부터 토폴로지 타입 판별
- analyze_rotor_topology             : 전체 회전자 도형 분석 및 종합 토폴로지 평가
- reconstruct_from_half              : 1/2극 또는 1극 단위로부터 전체 회전자 기하학적 복원
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

from core import EntityInfo
from half_unit import (
    extract_half_pole_entities,
    extract_half_slot_entities,
    reconstruct_from_half,
)


@dataclass
class PoleRegionInfo:
    """한 극(Pole) 영역 내의 구성요소 정보"""
    pole_index: int              # 극 인덱스 (0, 1, 2, ...)
    pole_pitch_deg: float        # 극 피치 (도)
    angle_start: float           # 시작 각도
    angle_end: float             # 끝 각도
    entities: List[EntityInfo]   # 해당 극의 엔티티들
    
    # 분류된 구성요소
    magnets: List[EntityInfo] = None       # 자석 (호 형태, 표면 근처)
    air_barriers: List[EntityInfo] = None  # 공기 배리어 (내부 빈 영역)
    rotor_core: List[EntityInfo] = None    # 로터 코어 (철심)
    flux_barriers: List[EntityInfo] = None # 플럭스 배리어 (IPM 내부)


def detect_circular_array_pattern(entities: List[EntityInfo], 
                                   origin: Tuple[float, float] = (0.0, 0.0),
                                   min_repeats: int = 4) -> Dict:
    """회전자 도면의 엔티티들에서 극(Pole) 반복 패턴을 자동으로 감지하여 극수와 극 피치를 추정합니다.

    회전자는 일반적으로 N개의 극으로 구성된 원형 배열입니다. 각 극은 같은 형태의 자석, 플럭스 배리어, 
    코어 패턴을 반복합니다. 이 함수는 엔티티의 기하학적 특성(타입, 반경)과 각도 분포를 분석하여 
    반복되는 단위(극)를 자동으로 찾습니다.

    알고리즘:
    1. 엔티티를 타입과 반경 범위 기반으로 '시그니처(Signature)'로 분류.
    2. 같은 시그니처를 가진 엔티티들의 각도 분포 분석.
    3. min_repeats 이상 반복되는 시그니처 그룹 검출.
    4. 도출된 각도 피치들로부터 극수 및 극 피치 계산.

    Args:
        entities (List[EntityInfo]): 회전자의 모든 도형 엔티티.
        origin (Tuple[float, float]): 각도 계산의 기준 원점(회전축 중심). 기본값 (0.0, 0.0).
        min_repeats (int): 극 패턴으로 간주하는 최소 반복 수. 기본값 4.

    Returns:
        Dict: 원형 배열 패턴 분석 결과:
            - 'has_pattern' (bool): 극 반복 패턴이 명확하게 감지되었는지 여부.
            - 'n_poles' (int): 감지된 극의 수. 패턴이 없으면 0.
            - 'pole_pitch_deg' (float): 극 사이의 각도 간격(도). 예: 360 / n_poles.
            - 'entity_groups' (Dict): 시그니처별로 분류 및 그룹화된 엔티티 딕셔너리.
            - 'angular_positions' (Dict): 각 시그니처 그룹의 엔티티들의 평균 각도 리스트.
            - 'confidence' (str): 패턴 감지 신뢰도 ('high', 'medium', 'low').
    """
    ox, oy = origin
    
    # 엔티티 시그니처 생성 (타입 + 반경 범위)
    def get_signature(ei):
        radii = [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]
        r_min, r_max = min(radii), max(radii)
        r_bin = round((r_min + r_max) / 2, 0)  # 반경 중심 (1mm 단위)
        return f"{ei.etype}_{r_bin}"
    
    # 시그니처별 그룹핑
    groups = defaultdict(list)
    for ei in entities:
        sig = get_signature(ei)
        # 각도 계산
        angles = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360 for p in ei.points]
        avg_angle = np.mean(angles)
        groups[sig].append({'entity': ei, 'angle': avg_angle})
    
    # 반복되는 그룹 찾기 (min_repeats 이상)
    repeating_groups = {k: v for k, v in groups.items() if len(v) >= min_repeats}
    
    if not repeating_groups:
        return {'has_pattern': False, 'n_poles': 0, 'pole_pitch_deg': 0}
    
    # 각 그룹의 각도 간격 분석
    pitches = []
    angular_positions = {}
    
    for sig, items in repeating_groups.items():
        angles = sorted([item['angle'] for item in items])
        angular_positions[sig] = angles
        
        if len(angles) >= 2:
            # 각도 차이 계산
            diffs = []
            for i in range(len(angles) - 1):
                diffs.append(angles[i+1] - angles[i])
            # 마지막 → 첫번째 (360도 순환)
            diffs.append(360 - angles[-1] + angles[0])
            
            avg_pitch = np.median(diffs)
            pitches.append(avg_pitch)
    
    if not pitches:
        return {'has_pattern': False, 'n_poles': 0, 'pole_pitch_deg': 0}
    
    # 가장 많이 나타나는 피치 찾기
    pole_pitch = np.median(pitches)
    n_poles = int(round(360 / pole_pitch))
    
    return {
        'has_pattern': True,
        'n_poles': n_poles,
        'pole_pitch_deg': pole_pitch,
        'entity_groups': {k: [item['entity'] for item in v] for k, v in repeating_groups.items()},
        'angular_positions': angular_positions,
        'all_groups': groups
    }


def extract_single_pole_entities(entities: List[EntityInfo],
                                  origin: Tuple[float, float] = (0.0, 0.0),
                                  pole_pitch_deg: float = None,
                                  reference_angle: float = 0.0,
                                  normalize_to_zero: bool = True) -> Dict:
    """회전자 전체에서 한 극(Pole)에 해당하는 엔티티들을 추출하고, 이들을 기준 각도(0°) 좌표계로 역회전시킵니다.

    원리는 half-unit 추출과 유사하나, 반극(Half-pole)이 아닌 전극(Full-pole, 360도/극수)을 대상으로 합니다.
    추출된 1극 디자인은 토폴로지 분석(극 내 자석/배리어 배치) 및 설계 매개변수 계산에 사용됩니다.

    Args:
        entities (List[EntityInfo]): 회전자의 전체 엔티티.
        origin (Tuple[float, float]): 각도 계산 원점. 기본값 (0.0, 0.0).
        pole_pitch_deg (float, optional): 극 사이의 각도 간격(도). 
                                          미제공 시 `detect_circular_array_pattern`으로 자동 감지.
        reference_angle (float): 추출할 첫 번째 극의 시작 각도(도). 기본값 0.0.
        normalize_to_zero (bool): True이면 추출된 모든 엔티티를 0° 기준으로 역회전변환. 기본값 True.

    Returns:
        Dict: 극 단위 추출 및 정규화 결과:
            - 'pole_entities' (List[Dict]): 한 극 내 모든 엔티티 (angle 정보 포함).
            - 'normalized_entities' (List[Dict]): 0°로 역회전된 엔티티들.
            - 'one_pole_entities' (List[EntityInfo]): 1극 영역의 대표 EntityInfo 객체들.
            - 'pole_pitch_deg' (float): 사용된 극 피치.
            - 'n_poles' (int): 추정된 회전자의 극수.
            - 'angel_span' (float): 추출된 극의 총 각도 범위.
    """
    ox, oy = origin

    # 극 피치 자동 감지
    if pole_pitch_deg is None:
        pattern = detect_circular_array_pattern(entities, origin)
        if pattern['has_pattern']:
            pole_pitch_deg = pattern['pole_pitch_deg']
        else:
            pole_pitch_deg = 30.0

    n_poles = int(round(360 / pole_pitch_deg))

    # half-unit 기반 1극 재구성
    half_pole = extract_half_pole_entities(
        entities,
        origin,
        pole_pitch_deg=pole_pitch_deg,
        reference_angle=reference_angle,
        normalize_to_zero=normalize_to_zero,
    )
    one_pole_entities = reconstruct_from_half(half_pole, origin, n_repeats=1)

    # 1극 엔티티를 dict list로 변환
    pole_entities = []
    for ei in one_pole_entities:
        if not ei.points:
            continue
        angles = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360 for p in ei.points]
        avg_angle = float(np.mean(angles))
        angle_diff = (avg_angle - reference_angle + 180) % 360 - 180
        pole_entities.append({
            'entity': ei,
            'original_angle': avg_angle,
            'relative_angle': angle_diff,
        })

    normalized_entities = []
    if normalize_to_zero and pole_entities:
        rot_rad = np.radians(-reference_angle)
        cos_r, sin_r = np.cos(rot_rad), np.sin(rot_rad)
        for item in pole_entities:
            ei = item['entity']
            new_points = []
            for px, py in ei.points:
                dx, dy = px - ox, py - oy
                new_x = ox + dx * cos_r - dy * sin_r
                new_y = oy + dx * sin_r + dy * cos_r
                new_points.append((new_x, new_y))
            new_center = None
            if ei.center:
                dx, dy = ei.center[0] - ox, ei.center[1] - oy
                new_center = (ox + dx * cos_r - dy * sin_r,
                              oy + dx * sin_r + dy * cos_r)
            new_sa = (ei.start_angle - reference_angle) if ei.start_angle is not None else None
            new_ea = (ei.end_angle - reference_angle) if ei.end_angle is not None else None
            new_ei = EntityInfo(
                etype=ei.etype,
                layer=ei.layer,
                points=new_points,
                radius=ei.radius,
                center=new_center,
                start_angle=new_sa,
                end_angle=new_ea,
                is_closed=ei.is_closed,
                raw=None,
            )
            normalized_entities.append({
                'entity': new_ei,
                'original_angle': item['original_angle'],
                'relative_angle': item['relative_angle'],
            })

    return {
        'pole_entities': pole_entities,
        'normalized_entities': normalized_entities,
        'one_pole_entities': one_pole_entities,
        'pole_pitch_deg': pole_pitch_deg,
        'n_poles': n_poles,
        'reference_angle': reference_angle,
    }


def extract_single_slot_entities(entities: List[EntityInfo],
                                  origin: Tuple[float, float] = (0.0, 0.0),
                                  slot_pitch_deg: float = None,
                                  n_slots: int = None,
                                  reference_angle: float = 0.0,
                                  normalize_to_zero: bool = True) -> Dict:
    """고정자 도전(권선)의 한 슬롯(Slot) 영역에 속하는 모든 엔티티를 추출하고 정규화합니다.

    두 인접한 슬롯 벽면 사이의 공간이 1개 슬롯입니다. 이 함수는 슬롯 수와 피치 각도를 추정하고,
    첫 번째 슬롯의 엔티티들을 모두 수집하여 0° 기준점으로 역회전시킵니다.

    Args:
        entities (List[EntityInfo]): 고정자의 모든 엔티티.
        origin (Tuple[float, float]): 각도 계산 원점. 기본값 (0.0, 0.0).
        slot_pitch_deg (float, optional): 슬롯 사이의 각도 간격(도). 
                                          미제공 시 radial LINE 분석으로 자동 감지.
        n_slots (int, optional): 이미 알려진 슬롯 수. 이를 제공하면 slot_pitch_deg = 360 / n_slots.
        reference_angle (float): 추출할 첫 번째 슬롯의 시작 각도(도). 기본값 0.0.
        normalize_to_zero (bool): True이면 추출된 엔티티들을 0° 기준으로 역회전. 기본값 True.

    Returns:
        Dict: 슬롯 단위 추출 및 정규화 결과:
            - 'slot_entities' (List[Dict]): 한 슬롯 내 모든 엔티티 (angle 정보 포함).
            - 'normalized_entities' (List[Dict]): 0°로 역회전된 엔티티들.
            - 'slot_pitch_deg' (float): 사용된 슬롯 피치.
            - 'n_slots' (int): 고정자의 전체 슬롯 수.
            - 'reference_angle' (float): 추출 기준 각도.
            - 'angle_span' (float): 추출된 슬롯의 총 각도 범위.
    """
    ox, oy = origin
    
    # 슬롯 피치 자동 감지 (radial LINE의 각도 분포)
    if slot_pitch_deg is None:
        if n_slots is not None:
            slot_pitch_deg = 360.0 / n_slots
        else:
            # 방사형 LINE 각도 분석으로 슬롯 피치 추정
            slot_angles = []
            for ei in entities:
                if ei.etype != 'LINE':
                    continue
                p1, p2 = ei.points[0], ei.points[1]
                r1 = np.hypot(p1[0] - ox, p1[1] - oy)
                r2 = np.hypot(p2[0] - ox, p2[1] - oy)
                span = abs(r2 - r1)
                length = np.hypot(p2[0] - p1[0], p2[1] - p1[1])
                if length < 1e-6:
                    continue
                if span / length > 0.8:  # 방사형 LINE
                    mid_angle = np.degrees(np.arctan2(
                        (p1[1] + p2[1]) / 2 - oy,
                        (p1[0] + p2[0]) / 2 - ox)) % 360
                    slot_angles.append(mid_angle)
            
            if len(slot_angles) >= 4:
                slot_angles = np.sort(slot_angles)
                diffs = np.diff(slot_angles)
                # 작은 간격(같은 슬롯 내 2개 LINE)과 큰 간격(슬롯 간)을 구분
                diffs = diffs[diffs > 1.0]
                if len(diffs) > 0:
                    # 슬롯 피치 = 가장 빈번한 간격
                    from collections import Counter
                    pitch_bins = Counter(round(d, 0) for d in diffs)
                    slot_pitch_deg = float(pitch_bins.most_common(1)[0][0])
                else:
                    slot_pitch_deg = 10.0  # 기본값
            else:
                # ARC 패턴으로 시도
                pattern = detect_circular_array_pattern(entities, origin, min_repeats=4)
                if pattern['has_pattern']:
                    slot_pitch_deg = pattern['pole_pitch_deg']
                else:
                    slot_pitch_deg = 10.0
    
    n_slots = int(round(360 / slot_pitch_deg))
    half_pitch = slot_pitch_deg / 2
    
    # 한 슬롯 영역에 속하는 엔티티 추출
    slot_entities = []
    for ei in entities:
        angles = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360 for p in ei.points]
        avg_angle = np.mean(angles)
        angle_diff = (avg_angle - reference_angle + 180) % 360 - 180
        if -half_pitch <= angle_diff <= half_pitch:
            slot_entities.append({
                'entity': ei,
                'original_angle': avg_angle,
                'relative_angle': angle_diff
            })
    
    # 역회전 정규화
    normalized_entities = []
    if normalize_to_zero and slot_entities:
        for item in slot_entities:
            ei = item['entity']
            rotation_angle = -reference_angle
            rad = np.radians(rotation_angle)
            cos_r, sin_r = np.cos(rad), np.sin(rad)
            
            new_points = []
            for px, py in ei.points:
                dx, dy = px - ox, py - oy
                new_x = ox + dx * cos_r - dy * sin_r
                new_y = oy + dx * sin_r + dy * cos_r
                new_points.append((new_x, new_y))
            
            new_center = None
            if ei.center:
                dx, dy = ei.center[0] - ox, ei.center[1] - oy
                new_center = (ox + dx * cos_r - dy * sin_r,
                              oy + dx * sin_r + dy * cos_r)
            
            new_sa = ei.start_angle + np.degrees(rotation_angle) if ei.start_angle is not None else None
            new_ea = ei.end_angle + np.degrees(rotation_angle) if ei.end_angle is not None else None
            
            new_ei = EntityInfo(
                etype=ei.etype, layer=ei.layer, points=new_points,
                radius=ei.radius, center=new_center,
                start_angle=new_sa, end_angle=new_ea,
                is_closed=ei.is_closed, raw=None
            )
            normalized_entities.append({
                'entity': new_ei,
                'original_angle': item['original_angle'],
                'relative_angle': item['relative_angle']
            })
    
    return {
        'slot_entities': slot_entities,
        'normalized_entities': normalized_entities,
        'slot_pitch_deg': slot_pitch_deg,
        'n_slots': n_slots,
        'reference_angle': reference_angle
    }


# ═══════════════════════════════════════════════════════════════
# Half-Unit 추출 함수 (최소 반복 단위)
# ═══════════════════════════════════════════════════════════════

def _find_best_reference_angle(entities: List[EntityInfo],
                                origin: Tuple[float, float],
                                full_pitch_deg: float) -> float:
    """
    엔티티 각도 분포에서 가장 적합한 극/슬롯 경계 각도를 찾습니다.
    
    로직: 엔티티가 가장 적은 각도(gap) 위치를 경계로 선택.
    즉, 극/슬롯 사이의 빈 공간이 경계가 됩니다.
    
    Returns
    -------
    float : 가장 좋은 경계 각도 (도, 0~full_pitch_deg)
    """
    ox, oy = origin
    
    # 엔티티 각도 수집 (동심원 제외)
    angles = []
    for ei in entities:
        if ei.etype in ('CIRCLE', 'ARC') and ei.center:
            if math.hypot(ei.center[0] - ox, ei.center[1] - oy) < 1e-3:
                continue
        if not ei.points:
            continue
        pts_angles = [math.degrees(math.atan2(p[1] - oy, p[0] - ox)) % 360
                      for p in ei.points]
        angles.append(float(np.mean(pts_angles)))
    
    if not angles:
        return 0.0
    
    # 각도를 pitch 기준으로 정규화 (0 ~ full_pitch_deg)
    normalized = [(a % full_pitch_deg) for a in angles]
    normalized.sort()
    
    if len(normalized) < 2:
        return 0.0
    
    # 각 위치에서의 엔티티 밀도가 가장 낮은 곳 = 경계
    # 히스토그램 방식: 1° 빈으로 나누고 가장 비어있는 구간 찾기
    n_bins = max(4, int(full_pitch_deg))
    bin_size = full_pitch_deg / n_bins
    hist = [0] * n_bins
    for a in normalized:
        b = int(a / bin_size) % n_bins
        hist[b] += 1
    
    # 가장 빈 빈의 중심 = 경계 후보
    min_count = min(hist)
    min_bins = [i for i, c in enumerate(hist) if c == min_count]
    
    # 연속된 빈 빈 중 중간을 선택
    best_bin = min_bins[len(min_bins) // 2]
    boundary_in_pitch = (best_bin + 0.5) * bin_size
    
    return boundary_in_pitch


def _extract_half_entities(entities: List[EntityInfo],
                           origin: Tuple[float, float],
                           full_pitch_deg: float,
                           reference_angle: float = 0.0,
                           normalize_to_zero: bool = True,
                           angle_tol: float = 0.05) -> Dict:
    """
    엔티티에서 [reference_angle, reference_angle + full_pitch/2] 범위를 추출.
    반극/반슬롯 공통 로직.
    
    Parameters
    ----------
    entities : 엔티티 리스트
    origin : 원점
    full_pitch_deg : 풀 피치 (극 피치 또는 슬롯 피치)
    reference_angle : 기준 각도 (도)
    normalize_to_zero : 0° 기준으로 역회전
    angle_tol : 경계 허용 오차 (도)
    
    Returns
    -------
    dict : half_entities, normalized_entities, concentric_arcs, half_pitch_deg
    """
    import math
    ox, oy = origin
    half_pitch = full_pitch_deg / 2.0
    ang_start = reference_angle
    ang_end = reference_angle + half_pitch

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

        # 엔티티 대표 각도
        angles = [math.degrees(math.atan2(p[1] - oy, p[0] - ox)) % 360
                  for p in ei.points]
        avg_angle = float(np.mean(angles))

        # [ang_start, ang_end] 범위 체크 (순환 고려)
        a_rel = (avg_angle - ang_start + 360) % 360
        if a_rel <= half_pitch + angle_tol:
            half_entities.append({
                'entity': ei,
                'original_angle': avg_angle,
                'relative_angle': a_rel,
            })

    # 중복 동심원 제거는 여기서 하지 않음 (각 extract_half_*에서 처리)

    # 0° 기준으로 역회전 정규화
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


def extract_half_pole_entities(entities: List[EntityInfo],
                                origin: Tuple[float, float] = (0.0, 0.0),
                                pole_pitch_deg: float = None,
                                reference_angle: float = None,
                                normalize_to_zero: bool = True) -> Dict:
    """
    반극(Half-Pole) 엔티티 추출 — 로터 최소 반복 단위.
    
    극 피치의 절반 [ref, ref + pole_pitch/2] 범위의 엔티티만 추출합니다.
    로터 극은 mirror symmetry를 가지므로, 반극이 최소 고유 기하입니다.
    
    복원 방법: mirror(반극, axis=half_pitch) → 1극 → circular_array(n_poles)
    
    Parameters
    ----------
    entities : 로터 엔티티 리스트
    origin : 원점
    pole_pitch_deg : 극 피치 (None이면 자동 감지)
    reference_angle : 기준 극 시작 각도 (None이면 자동 감지)
    normalize_to_zero : True면 0° 기준으로 역회전
    
    Returns
    -------
    dict:
        - half_entities: 반극 엔티티 [{entity, original_angle, relative_angle}, ...]
        - normalized_entities: 0° 기준 정규화된 EntityInfo 리스트
        - concentric_arcs: 동심원/호 리스트
        - half_pitch_deg: 반극 피치 (= pole_pitch / 2)
        - pole_pitch_deg: 극 피치
        - n_poles: 극수
        - mirror_axis_deg: mirror 대칭축 각도 (정규화 후, = half_pitch)
        - reference_angle: 사용된 기준 각도
    """
    # 극 피치 자동 감지
    if pole_pitch_deg is None:
        pattern = detect_circular_array_pattern(entities, origin)
        if pattern['has_pattern']:
            pole_pitch_deg = pattern['pole_pitch_deg']
        else:
            pole_pitch_deg = 30.0

    n_poles = int(round(360.0 / pole_pitch_deg))
    half_pitch = pole_pitch_deg / 2.0

    # reference_angle: 기본 0° (x축 오른쪽)
    # mirror 축 = pole_pitch / 2 = half_pitch (극수에서 명시적 계산)
    if reference_angle is None:
        reference_angle = 0.0

    result = _extract_half_entities(
        entities, origin, pole_pitch_deg, reference_angle, normalize_to_zero
    )

    # shaft/rotor 외경 ARC만 half-pitch 각도 ARC 생성, 나머지는 원본 각도 그대로
    shaft_r = None
    rotor_outer_r = None
    # split_result에서 airgap_r_inner/airgap_r_outer 우선 사용
    import inspect
    frame = inspect.currentframe()
    while frame:
        if 'split_result' in frame.f_locals:
            split_result = frame.f_locals['split_result']
            shaft_r = split_result.get('airgap_r_inner', None)
            rotor_outer_r = split_result.get('airgap_r_outer', None)
            break
        frame = frame.f_back
    # fallback: ARC/CIRCLE에서 추출
    if shaft_r is None or rotor_outer_r is None:
        all_radii = [ei.radius for ei in result['concentric_arcs'] if ei.radius]
        if all_radii:
            # shaft_r: 가장 작은 반경 (shaft 또는 중심부)
            if shaft_r is None:
                shaft_r = min(all_radii)
            # rotor_outer_r: ARC/CIRCLE 중 가장 큰 반경
            if rotor_outer_r is None:
                rotor_outer_r = max(all_radii)
    processed_arcs = []
    for ei in result['concentric_arcs']:
        if ei.etype == 'ARC':
            # shaft/rotor 외경 ARC는 half-pitch ARC 추가 + 원본 ARC도 반드시 포함
            is_shaft = shaft_r and abs(ei.radius - shaft_r) < 1e-2
            is_rotor_outer = rotor_outer_r and abs(ei.radius - rotor_outer_r) < 1e-2
            if is_shaft or is_rotor_outer:
                # half-pitch ARC 생성
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
            # 원본 ARC는 무조건 포함 (air barrier 등 누락 방지)
            processed_arcs.append(ei)
        else:
            processed_arcs.append(ei)
    result['concentric_arcs'] = processed_arcs
    result.update({
        'pole_pitch_deg': pole_pitch_deg,
        'n_poles': n_poles,
        'reference_angle': reference_angle,
        'mirror_axis_deg': half_pitch,  # = pole_pitch / 2
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
    
    슬롯 피치의 절반 [ref, ref + slot_pitch/2] 범위의 엔티티만 추출합니다.
    스테이터 슬롯은 mirror symmetry를 가지므로, 반슬롯이 최소 고유 기하입니다.
    
    복원 방법: mirror(반슬롯, axis=half_pitch) → 1슬롯 → circular_array(n_slots)
    
    Parameters
    ----------
    entities : 스테이터 엔티티 리스트
    origin : 원점
    slot_pitch_deg : 슬롯 피치 (None이면 자동 감지)
    n_slots : 슬롯 수 (None이면 slot_pitch에서 계산)
    reference_angle : 기준 슬롯 시작 각도
    normalize_to_zero : True면 0° 기준으로 역회전
    
    Returns
    -------
    dict:
        - half_entities: 반슬롯 엔티티
        - normalized_entities: 정규화된 EntityInfo 리스트
        - concentric_arcs: 동심원/호
        - half_pitch_deg: 반슬롯 피치 (= slot_pitch / 2)
        - slot_pitch_deg: 슬롯 피치
        - n_slots: 슬롯수
        - mirror_axis_deg: mirror 대칭축 각도
    """
    from analysis import count_slots as _count_slots

    # 슬롯 피치 자동 감지
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

    # reference_angle: 기본 0° (x축 오른쪽)
    # mirror 축 = slot_pitch / 2 = half_pitch (슬롯수에서 명시적 계산)
    if reference_angle is None:
        reference_angle = 0.0

    result = _extract_half_entities(
        entities, origin, slot_pitch_deg, reference_angle, normalize_to_zero
    )

    # stator 외경 ARC만 half-pitch ARC 생성, 나머지는 원본 각도 그대로
    stator_outer_r = None
    circle_radii = [ei.radius for ei in result['concentric_arcs'] if ei.etype == 'CIRCLE' and ei.radius]
    if circle_radii:
        stator_outer_r = max(circle_radii)
    processed_arcs = []
    for ei in result['concentric_arcs']:
        if ei.etype == 'ARC':
            if stator_outer_r and abs(ei.radius - stator_outer_r) < 1e-2:
                # half-pitch ARC 생성
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
        'mirror_axis_deg': half_pitch,  # = slot_pitch / 2
    })
    return result


def reconstruct_from_half(half_result: Dict,
                          origin: Tuple[float, float] = (0.0, 0.0),
                          n_repeats: int = 1,
                          include_concentric: bool = True) -> List[EntityInfo]:
    """반극(Half-pole) 또는 반슬롯(Half-slot) 추출 결과로부터 거울 대칭 및 원형 배열을 통해 
    전체 기하를 재구성합니다.

    최소 반복 단위(반극/반슬롯)에서 출발하여:
    1. 거울 연산(Mirror): 반극/반슬롯 → 1극/1슬롯
    2. 원형 배열(Circular Array): 1극 × N → 전체 회전자/고정자

    이를 통해 큰 극수/슬롯수를 가진 복잡한 설계를 간단한 1/2극 추출로부터 
    빠르게 재구성할 수 있습니다.

    Args:
        half_result (Dict): `extract_half_pole_entities` 또는 `extract_half_slot_entities`의 결과 딕셔너리.
                           'normalized_entities', 'mirror_axis_deg', 'concentric_arcs' 등을 포함.
        origin (Tuple[float, float]): 거울 및 회전 중심점. 기본값 (0.0, 0.0).
        n_repeats (int): 원형 배열 반복 횟수. 
                        1인 경우 1극/1슬롯, n_poles/n_slots인 경우 전체 회전자/고정자 재구성. 
                        기본값 1.
        include_concentric (bool): 동심원(원, 호) 엔티티 포함 여부. 
                                  True이면 shaft 및 외경 원호도 재구성에 포함. 기본값 True.

    Returns:
        List[EntityInfo]: 재구성된 엔티티 리스트. 거울 대칭 및 N번 원형 배열이 적용됨.

    예:
        - half_result = extract_half_pole_entities(...)  # 반극 추출
        - reconstructed = reconstruct_from_half(half_result, n_repeats=6)  # 6극 전체 복원
    """
    from core import rotate_entity, mirror_entity

    half_ents = half_result['normalized_entities']
    mirror_axis = half_result['mirror_axis_deg']
    full_pitch = mirror_axis * 2  # pole_pitch or slot_pitch

    # 1) mirror → 1단위 (1극 또는 1슬롯)
    one_unit = list(half_ents)
    for ei in half_ents:
        mirrored = mirror_entity(ei, mirror_axis, origin)
        one_unit.append(mirrored)

    # 2) circular array → n_repeats 단위
    reconstructed = []
    for i in range(n_repeats):
        rot_deg = i * full_pitch
        for ei in one_unit:
            if i == 0:
                reconstructed.append(ei)
            else:
                reconstructed.append(rotate_entity(ei, rot_deg, origin))

    # 3) 동심원/호
    if include_concentric:
        for ei in half_result.get('concentric_arcs', []):
            if ei.etype == 'CIRCLE':
                reconstructed.append(ei)
            elif ei.etype == 'ARC':
                import math
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


def _cluster_by_angle(items: List[Dict],
                      origin: Tuple[float, float],
                      gap_deg: float = 5.0) -> List[List[Dict]]:
    """
    엔티티를 각도 기준으로 클러스터링합니다.
    
    인접 엔티티 사이 각도 차이가 gap_deg 이하이면 같은 그룹.
    
    Returns
    -------
    List[List[Dict]] : 각도 순 클러스터 리스트
    """
    if not items:
        return []
    ox, oy = origin
    # 각 엔티티의 대표 각도
    ang_list = []
    for item in items:
        ei = item['entity']
        angles = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360
                  for p in ei.points]
        ang_list.append(np.mean(angles) if angles else 0.0)

    idx_sorted = np.argsort(ang_list)
    clusters: List[List[int]] = [[idx_sorted[0]]]
    for i in range(1, len(idx_sorted)):
        diff = ang_list[idx_sorted[i]] - ang_list[idx_sorted[i - 1]]
        if diff < gap_deg:
            clusters[-1].append(idx_sorted[i])
        else:
            clusters.append([idx_sorted[i]])
    return [[items[j] for j in c] for c in clusters]


def classify_pole_topology(pole_entities: List[Dict],
                            origin: Tuple[float, float] = (0.0, 0.0),
                            airgap_r: float = None,
                            pole_pitch_deg: float = None) -> Dict:
    """추출된 한 극(Pole) 내의 자석, 공기 배리어, 철심 엔티티들을 분석하여 회전자 토폴로지를 판별합니다.

    회전자의 전자기적 특성은 극 내 자석의 배치 위치(표면 또는 내부)와 플럭스 배리어의 존재 여부로 결정됩니다.
    구체적으로:
    
    - **SPM (Surface Permanent Magnet)**: 공극(Airgap)에 인접하여 자석이 부착된 형태.
    - **IPM (Interior Permanent Magnet)**: 자석이 극 내부에 매장되고 추가로 공기 배리어가 있음.
    - **SynRM (Synchronous Reluctance Motor)**: 자석 없이 공기 배리어(플럭스 배리어)로만 릭턴스 토크 생성.
    - **PMa-SynRM (PM-Assisted SynRM)**: IPM 구조에 추가 플럭스 배리어를 결합한 하이브리드 형태.

    이 함수는 극 내 엔티티들의 반경 위치와 기하학적 분포를 분석하여 위 네 가지 중 하나로 분류합니다.

    알고리즘:
    1. 극 내 모든 엔티티의 반경 범위 파악 (r_min_all ~ r_max_all).
    2. 反경 위치 기반으로 자석/배리어/코어를 식별 (에어갭 기준).
    3. 자석 엔티티를 각도로 클러스터링하여 논리 자석 개수 산출.
    4. 자석 위치(표면/내부), 배리어 유무 → 최종 토폴로지 판별.

    Args:
        pole_entities (List[Dict]): 한 극의 엔티티들. 각 원소는 {'entity': EntityInfo, 'original_angle': float, ...} 형태.
        origin (Tuple[float, float]): 반경 및 각도 계산 원점. 기본값 (0.0, 0.0).
        airgap_r (float, optional): 공극(Airgap) 반경. 미제공 시 극 내 최대 반경의 95% 사용.
        pole_pitch_deg (float, optional): 극 피치(도). 클러스터 간격을 결정할 때 사용. 기본값 None.

    Returns:
        Dict: 극 내 구성요소 및 토폴로지 판별 결과:
            - 'topology' (str): 판별된 토폴로지 타입 ('SPM', 'IPM', 'SynRM', 'PMa-SynRM', 'UNKNOWN').
            - 'magnets' (List[EntityInfo]): 자석으로 식별된 엔티티들.
            - 'air_barriers' (List[EntityInfo]): 공기 배리어(빈 공간)로 식별된 엔티티들.
            - 'core' (List[EntityInfo]): 철심(코어)으로 식별된 엔티티들.
            - 'n_magnets' (int): 자석 클러스터의 논리적 개수.
            - 'n_magnet_entities' (int): 자석으로 분류된 개별 엔티티 수.
            - 'n_barriers' (int): 공기 배리어의 수.
            - 'magnet_near_surface' (bool): 자석이 공극에 인접해 있는지 여부 (SPM 판별 기준).
            - 'magnet_embedded' (bool): 자석이 극 내부에 매장되어 있는지 여부 (IPM 판별 기준).
            - 'magnet_clusters' (List[Dict]): 자석 클러스터 정보 (위치, 면적, 개수).
            - 'detail' (str): 판별 상세 내용 및 근거.
    """
    ox, oy = origin
    
    _empty = {
        'topology': 'UNKNOWN',
        'magnets': [],
        'air_barriers': [],
        'core': [],
        'detail': 'No entities',
        'n_magnets': 0,
        'n_magnet_entities': 0,
        'n_barriers': 0,
        'magnet_near_surface': False,
        'magnet_embedded': False,
        'magnet_clusters': [],
    }
    if not pole_entities:
        return _empty
    
    # 모든 엔티티의 반경 범위 파악
    all_radii = []
    for item in pole_entities:
        ei = item['entity']
        for p in ei.points:
            all_radii.append(np.hypot(p[0] - ox, p[1] - oy))
    
    if not all_radii:
        _empty['detail'] = 'No points'
        return _empty
    
    r_min_all = min(all_radii)
    r_max_all = max(all_radii)
    radial_range = r_max_all - r_min_all
    
    # 에어갭 반경 추정 (가장 바깥쪽 = 에어갭 근처)
    if airgap_r is None:
        airgap_r = r_max_all * 0.95
    
    # ── 엔티티 분류 (표면 임계치 강화) ──
    surface_threshold = airgap_r * 0.90   # r_avg 기준 — 상위 ~10%만 자석 후보
    thin_threshold = radial_range * 0.15  # 반경 스팬 얇은 것만 (15% of range)
    magnets = []        # 자석 후보 엔티티
    air_barriers = []   # 공기 배리어 후보
    core = []           # 코어
    
    for item in pole_entities:
        ei = item['entity']
        radii = [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]
        if not radii:
            core.append(item)
            continue
        r_min, r_max = min(radii), max(radii)
        r_avg = np.mean(radii)
        radial_span = r_max - r_min
        
        is_near_surface = r_avg > surface_threshold
        is_arc = ei.etype == 'ARC'
        is_line = ei.etype == 'LINE'
        is_closed = ei.is_closed
        is_thin = radial_span < thin_threshold
        
        # 닫힌 도형(폴리라인 자석, 배리어 등)
        if is_closed and is_near_surface:
            magnets.append(item)
        elif is_closed and not is_near_surface:
            air_barriers.append(item)
        # 열린 ARC — 표면 근처이면서 얇은 것만 자석 후보
        elif is_arc and is_near_surface and is_thin:
            magnets.append(item)
        # 표면 근처 LINE — 반경 방향이면 자석 측면 경계
        elif is_line and is_near_surface and is_thin:
            # 방사형(라인 양 끝의 r차이 > 길이 80%)이면 자석 측면 후보
            pts = ei.points
            if len(pts) >= 2:
                dr = abs(max(radii) - min(radii))
                seg_len = np.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
                if seg_len > 1e-6 and dr / seg_len > 0.6:
                    magnets.append(item)
                else:
                    core.append(item)
            else:
                core.append(item)
        else:
            core.append(item)
    
    # ── 각도 클러스터링 → 논리 자석 개수 ──
    cluster_gap = (pole_pitch_deg / 4) if pole_pitch_deg else 8.0
    magnet_clusters = _cluster_by_angle(magnets, origin, gap_deg=cluster_gap)
    n_magnet_groups = len(magnet_clusters)
    n_magnet_entities = len(magnets)
    n_barriers = len(air_barriers)
    
    # ── 자석 위치 분석 ──
    magnet_near_surface = False
    magnet_embedded = False
    
    if magnets:
        magnet_radii = []
        for item in magnets:
            ei = item['entity']
            for p in ei.points:
                magnet_radii.append(np.hypot(p[0] - ox, p[1] - oy))
        avg_magnet_r = np.mean(magnet_radii)
        
        if avg_magnet_r > airgap_r * 0.88:
            magnet_near_surface = True
        else:
            magnet_embedded = True
    
    # ── 최종 판별 (논리 자석 그룹 수 기준) ──
    if n_magnet_groups > 0 and n_barriers == 0 and magnet_near_surface:
        topology = 'SPM'
        detail = (f'Surface-mounted PM '
                  f'({n_magnet_groups} magnet{"s" if n_magnet_groups > 1 else ""}, '
                  f'{n_magnet_entities} ent)')
    elif n_magnet_groups > 0 and (n_barriers > 0 or magnet_embedded):
        if n_barriers > n_magnet_groups:
            topology = 'PMa-SynRM'
            detail = (f'PM-assisted SynRM '
                      f'({n_magnet_groups} magnets, {n_barriers} barriers)')
        else:
            topology = 'IPM'
            detail = (f'Interior PM '
                      f'({n_magnet_groups} magnets, {n_barriers} barriers)')
    elif n_magnet_groups == 0 and n_barriers > 0:
        topology = 'SynRM'
        detail = f'Synchronous Reluctance ({n_barriers} flux barriers)'
    elif n_magnet_groups == 0 and n_barriers == 0:
        topology = 'UNKNOWN'
        detail = 'No magnets or barriers detected'
    else:
        topology = 'OTHER'
        detail = f'{n_magnet_groups} magnets, {n_barriers} barriers'
    
    return {
        'topology': topology,
        'magnets': magnets,
        'air_barriers': air_barriers,
        'core': core,
        'n_magnets': n_magnet_groups,        # 논리 자석 수 (클러스터)
        'n_magnet_entities': n_magnet_entities,  # 개별 엔티티 수
        'n_barriers': n_barriers,
        'magnet_near_surface': magnet_near_surface,
        'magnet_embedded': magnet_embedded,
        'magnet_clusters': magnet_clusters,
        'detail': detail
    }


def analyze_rotor_topology(entities: List[EntityInfo],
                           origin: Tuple[float, float] = (0.0, 0.0),
                           motor_type: str = 'inner_rotor',
                           airgap_r: float = None,
                           verbose: bool = True) -> Dict:
    """전체 회전자 도면 엔티티를 분석하여 극 반복 패턴을 역변환하고 최종 토폴로지를 판별합니다.

    극수가 많은 회전자 도면은 파싱하기 어렵습니다. 이 함수는 한 극만 추출·정규화하여 
    극 내 자석/배리어 분포를 분석한 후, 원형 배열(Circular Array) 원리로 
    전체 극의 토폴로지를 추정합니다.

    알고리즘:
    1. 엔티티 배열 패턴 감지 → 극수 및 극 피치 산출.
    2. 한 극 영역 추출 및 0° 기준으로 정규화.
    3. 정규화된 극 내 엔티티 분류 (자석/배리어/코어).
    4. 극 토폴로지 판별 → SPM/IPM/SynRM/PMa-SynRM 결정.
    5. 필요 시 반극(Half-pole) 기반 역변환 및 복원.

    Args:
        entities (List[EntityInfo]): 회전자의 모든 도면 엔티티.
        origin (Tuple[float, float]): 각도 및 반경 계산 원점. 기본값 (0.0, 0.0).
        motor_type (str): 모터 타입. 'inner_rotor' 또는 'outer_rotor'. 기본값 'inner_rotor'.
        airgap_r (float, optional): 공극 반경. 미제공 시 자동 추정.
        verbose (bool): 진행 과정 및 중간 결과 로깅 활성화. 기본값 True.

    Returns:
        Dict: 회전자 토폴로지 종합 분석 결과:
            - 'has_pattern' (bool): 극 반복 패턴이 감지되었는지 여부.
            - 'n_poles' (int): 추정된 회전자 극수.
            - 'pole_pitch_deg' (float): 극 사이의 각도 간격(도).
            - 'topology' (str): 판별된 토폴로지 ('SPM', 'IPM', 'SynRM', 'PMa-SynRM', 'UNKNOWN').
            - 'magnets' (List[EntityInfo]): 자석으로 분류된 엔티티들 (1극 단위).
            - 'air_barriers' (List[EntityInfo]): 공기 배리어로 분류된 엔티티들.
            - 'rotor_core' (List[EntityInfo]): 회전자 철심으로 분류된 엔티티들.
            - 'one_pole_entities' (List[EntityInfo]): 추출·분류된 1극 엔티티 (기준각도).
            - 'normalized_pole_entities' (List[EntityInfo]): 정규화된 1극 엔티티 (0° 기준).
            - 'reconstructed_entities' (List[EntityInfo]): 반극/극 역변환으로부터 복원된 전체 회전자.
            - 'pole_analysis' (Dict): classify_pole_topology의 상세 결과.
            - 'motor_type' (str): 입력된 모터 타입.
            - 'airgap_r' (float): 사용된 공극 반경.
            - 'analysis_detail' (str): 분석 과정 및 판별 근거 상세 설명.
    """
    # 1. Circular Array 패턴 감지
    pattern = detect_circular_array_pattern(entities, origin)
    
    if verbose:
        print("=" * 70)
        print("Rotor Topology Analysis (Circular Array 역변환)")
        print("=" * 70)
        print(f"\n[1] Circular Array 패턴 감지")
        print(f"    패턴 감지: {pattern['has_pattern']}")
        if pattern['has_pattern']:
            print(f"    추정 극수: {pattern['n_poles']}")
            print(f"    극 피치: {pattern['pole_pitch_deg']:.2f}°")
            print(f"    반복 그룹 수: {len(pattern['entity_groups'])}")
    
    # 2. 한 극 영역 추출 및 정규화
    pole_result = extract_single_pole_entities(
        entities, origin, 
        pole_pitch_deg=pattern['pole_pitch_deg'] if pattern['has_pattern'] else None,
        reference_angle=0.0,
        normalize_to_zero=True
    )
    
    if verbose:
        print(f"\n[2] 한 극(Pole) 영역 추출")
        print(f"    극 피치: {pole_result['pole_pitch_deg']:.2f}°")
        print(f"    극수: {pole_result['n_poles']}")
        print(f"    한 극 내 엔티티 수: {len(pole_result['pole_entities'])}")
    
    # 3. 토폴로지 분류
    topo_result = classify_pole_topology(
        pole_result['normalized_entities'], 
        origin, 
        airgap_r
    )
    
    if verbose:
        print(f"\n[3] 토폴로지 판별")
        print(f"    ★ 토폴로지: {topo_result['topology']}")
        print(f"    상세: {topo_result['detail']}")
        print(f"    - 자석 수: {topo_result['n_magnets']}")
        print(f"    - 공기 배리어 수: {topo_result['n_barriers']}")
    
    return {
        'pattern': pattern,
        'pole_result': pole_result,
        'topology': topo_result,
        'motor_type': motor_type,
        'n_poles': pole_result['n_poles'],
        'pole_pitch_deg': pole_result['pole_pitch_deg']
    }
