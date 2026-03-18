"""
pyMotorGeo.topology
===================
로터 토폴로지 분석 함수: SPM/IPM/SynRM/PMa-SynRM 판별.
Circular Array 역변환 및 극(Pole) 기준 분석.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

from .core import EntityInfo
from .half_unit import (
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
    """
    한 극(Pole) 영역의 엔티티를 추출하고, 기준 각도(0°)로 역변환합니다.
    
    Parameters
    ----------
    entities : 전체 엔티티 목록
    origin : 원점
    pole_pitch_deg : 극 피치 (None이면 자동 감지)
    reference_angle : 기준 극의 시작 각도
    normalize_to_zero : True면 모든 엔티티를 0° 기준으로 역회전
    
    Returns
    -------
    dict with:
        - 'pole_entities': 한 극 영역의 엔티티들 (dict list)
        - 'normalized_entities': 0° 기준으로 역회전된 엔티티들
        - 'one_pole_entities': 1극 재구성 EntityInfo 리스트
        - 'pole_pitch_deg': 사용된 극 피치
        - 'n_poles': 극수
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
    """
    한 슬롯(Slot) 영역의 스테이터 엔티티를 추출합니다.
    
    Parameters
    ----------
    entities : 스테이터 엔티티 목록
    origin : 원점
    slot_pitch_deg : 슬롯 피치 (None이면 자동 감지)
    n_slots : 슬롯 수 (None이면 자동 감지)
    reference_angle : 기준 슬롯 시작 각도
    normalize_to_zero : True면 모든 엔티티를 0° 기준으로 역회전
    
    Returns
    -------
    dict with:
        - 'slot_entities': 한 슬롯 영역의 엔티티들
        - 'normalized_entities': 0° 기준으로 역회전된 엔티티들
        - 'slot_pitch_deg': 사용된 슬롯 피치
        - 'n_slots': 슬롯 수
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
    """
    한 극 영역의 엔티티들을 분석하여 토폴로지를 판별합니다.
    
    개선 사항 (v1.2.1):
    - 표면 근처 임계치 강화 (0.80 → 0.90)
    - 개별 엔티티가 아닌 **각도 클러스터** 기반 논리 자석 개수 산출
    - pole_pitch_deg 파라미터로 클러스터 간격 자동 조정

    토폴로지 판별 기준:
    - SPM: 에어갭 근처에 자석만 있음 (표면 부착)
    - IPM: 에어갭에서 떨어진 내부에 자석 + 공기 배리어
    - SynRM: 자석 없이 공기 배리어만 (플럭스 배리어)
    - PMa-SynRM: IPM 구조 + 추가 플럭스 배리어
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
    """
    로터 엔티티들을 분석하여 토폴로지를 종합 판별합니다.
    
    Parameters
    ----------
    entities : 전체 엔티티 목록
    origin : 원점
    motor_type : 'inner_rotor' 또는 'outer_rotor'
    airgap_r : 에어갭 반경 (None이면 자동 추정)
    verbose : 상세 출력 여부
    
    Returns
    -------
    dict with comprehensive topology analysis
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
