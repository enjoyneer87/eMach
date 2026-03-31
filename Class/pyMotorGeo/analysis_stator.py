"""
pyMotorGeo.analysis_stator
==========================

고정자(Stator) 기하 데이터로부터 모터의 슬롯수(Slot Number)를 추정하고 
슬롯 내부의 컨덕터 배열 패턴을 탐지하는 모듈입니다.

주요 클래스
-----------
- StatorCounter            : 고정자 슬롯수 분석 클래스 (ComponentCounter 상속)

주요 함수 (하위 호환성)
-----------------------
- count_slots               : 방사형 선분(Radial Line)을 클러스터링하여 슬롯수 단면 벽면 감지
- count_slots_by_regions    : 고정자 체적 내부의 닫힌 면적(슬롯 / 권선) 주기 패턴을 통한 슬롯수 감지
- estimate_slots_robust     : 두 방법의 신뢰도를 교차 검증하여 최종 슬롯 피치와 개수 판별
- detect_slot_conductors    : 식별된 1슬롯 내에 위치한 동일 패턴의 컨덕터 요소 개수 분석
"""

import math
import numpy as np
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Optional

from core import EntityInfo
from analysis_base import ComponentCounter


# ═══════════════════════════════════════════════════════════════
# StatorCounter 클래스 (OOP 기반)
# ═══════════════════════════════════════════════════════════════

class StatorCounter(ComponentCounter):
    """
    고정자(Stator)의 슬롯 수를 다양한 방법으로 추정하고 
    슬롯 내 컨덕터를 탐지하는 클래스입니다.
    
    ComponentCounter 추상 클래스를 구현하며, 방사형 선분, 닫힌 영역,
    FFT 분석 등 여러 알고리즘을 조합하여 가장 신뢰도 높은 슬롯 수를 도출합니다.
    
    Attributes:
        component_type (str): "stator"
        count_keyword (str): "slots"
    """
    
    def __init__(self):
        """StatorCounter 초기화."""
        super().__init__(component_type="stator", count_keyword="slots")
    
    def count(self, 
              entities: List[EntityInfo],
              origin: Tuple[float, float] = (0.0, 0.0),
              **kwargs) -> int:
        """
        방사형 선분 기반 슬롯수 추정 (count_slots와 동일).
        
        Args:
            entities (List[EntityInfo]): 고정자 엔티티 리스트.
            origin (Tuple[float, float]): 회전 중심 좌표.
            **kwargs: tol_angle 등.
        
        Returns:
            int: 추정된 슬롯수.
        """
        tol_angle = kwargs.get('tol_angle', 2.0)
        return count_slots(entities, origin, tol_angle)
    
    def count_by_regions(self,
                        entities: List[EntityInfo],
                        origin: Tuple[float, float] = (0.0, 0.0),
                        **kwargs) -> Dict:
        """
        닫힌 영역 기반 슬롯수 추정 (count_slots_by_regions와 동일).
        
        Args:
            entities (List[EntityInfo]): 고정자 엔티티 리스트.
            origin (Tuple[float, float]): 회전 중심 좌표.
            **kwargs: airgap_r_outer, r_outer_max, tol_angle, verbose 등.
        
        Returns:
            Dict: 분석 결과.
        """
        airgap_r_outer = kwargs.get('airgap_r_outer', None)
        r_outer_max = kwargs.get('r_outer_max', None)
        tol_angle = kwargs.get('tol_angle', 2.0)
        verbose = kwargs.get('verbose', False)
        return count_slots_by_regions(entities, origin, airgap_r_outer, r_outer_max, tol_angle, verbose)
    
    def estimate_robust(self,
                       entities: List[EntityInfo],
                       origin: Tuple[float, float] = (0.0, 0.0),
                       verbose: bool = True,
                       **kwargs) -> Dict:
        """
        교차 검증을 통한 강건한 슬롯수 추정 (estimate_slots_robust와 동일).
        
        Args:
            entities (List[EntityInfo]): 고정자 엔티티 리스트.
            origin (Tuple[float, float]): 회전 중심 좌표.
            verbose (bool): 상세 로깅 여부.
            **kwargs: airgap_r_outer 등.
        
        Returns:
            Dict: 검증 결과.
        """
        airgap_r_outer = kwargs.get('airgap_r_outer', None)
        return estimate_slots_robust(entities, origin, airgap_r_outer, verbose)
    
    def detect_conductors(self,
                         entities: List[EntityInfo],
                         origin: Tuple[float, float] = (0.0, 0.0),
                         n_slots: int = 0,
                         slot_pitch_deg: float = 0.0,
                         verbose: bool = True,
                         **kwargs) -> Dict:
        """
        슬롯 내 컨덕터 탐지 (detect_slot_conductors와 동일).
        
        Args:
            entities (List[EntityInfo]): 고정자 엔티티 리스트.
            origin (Tuple[float, float]): 회전 중심 좌표.
            n_slots (int): 슬롯 수.
            slot_pitch_deg (float): 슬롯 피치 각도.
            verbose (bool): 상세 로깅 여부.
            **kwargs: airgap_r_outer, r_outer_max, area_tol 등.
        
        Returns:
            Dict: 컨덕터 탐지 결과.
        """
        airgap_r_outer = kwargs.get('airgap_r_outer', None)
        r_outer_max = kwargs.get('r_outer_max', None)
        area_tol = kwargs.get('area_tol', 0.3)
        return detect_slot_conductors(entities, origin, n_slots, slot_pitch_deg, 
                                      airgap_r_outer, r_outer_max, area_tol, verbose)


# ═══════════════════════════════════════════════════════════════
# Radial LINE 기반 슬롯수 (함수형 인터페이스 - 하위 호환성)
# ═══════════════════════════════════════════════════════════════

def count_slots(entities: List[EntityInfo],
                origin: Tuple[float, float] = (0.0, 0.0),
                tol_angle: float = 2.0) -> int:
    """방사형으로 뻗어있는 원형 배열 선분(LINE)의 각도 분포를 사용하여 슬롯 수를 추정합니다.

    알고리즘:
    1. 고정자 엔티티 중 수직 방향으로 그어진(반경 방향 차이가 큰) 선분들을 찾아 방위각을 기록.
    2. 매우 좁은 각도 편차(`tol_angle`) 내에 모여있는 선분들을 단일 '슬롯 벽면(Slot Wall)' 클러스터로 묶음.
    3. 일반적인 모터에서 하나의 슬롯(Open Space)은 2개의 양측 벽면으로 이루어지므로, 
       도출된 독립 벽면 클러스터의 개수를 2로 나누어 슬롯 수를 추정함.

    Args:
        entities (List[EntityInfo]): 고정자로 속하는 형상 엔티티.
        origin (Tuple[float, float]): 원형 구조의 중심 좌표. 기본값은 (0.0, 0.0).
        tol_angle (float): 같은 벽면으로 취급할 선형 분산의 허용 치수(도 단위). 기본값은 2.0.

    Returns:
        int: 방사형 벽면들을 카운트하여 추산한 전체 슬롯 수. 측정 실패시 0.
    """
    ox, oy = origin

    slot_angles = []
    for ei in entities:
        if ei.etype != 'LINE':
            continue
        (x1, y1), (x2, y2) = ei.points[:2]
        r1, r2 = math.hypot(x1 - ox, y1 - oy), math.hypot(x2 - ox, y2 - oy)
        dr = abs(r2 - r1)
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 1e-6:
            continue
        if dr / length > 0.9:
            mid_angle = math.degrees(
                math.atan2((y1 + y2) / 2 - oy, (x1 + x2) / 2 - ox)) % 360
            slot_angles.append(mid_angle)

    if not slot_angles:
        return 0

    slot_angles = np.array(sorted(slot_angles))
    if len(slot_angles) < 2:
        return len(slot_angles)

    # 클러스터링
    clusters = []
    current_cluster = [slot_angles[0]]
    for i in range(1, len(slot_angles)):
        if slot_angles[i] - slot_angles[i-1] <= tol_angle:
            current_cluster.append(slot_angles[i])
        else:
            clusters.append(np.mean(current_cluster))
            current_cluster = [slot_angles[i]]
    clusters.append(np.mean(current_cluster))

    # 순환 체크
    if len(clusters) > 1 and (360 - clusters[-1] + clusters[0]) <= tol_angle:
        merged = np.mean([clusters[-1] - 360, clusters[0]])
        clusters = [merged % 360] + clusters[1:-1]

    n_walls = len(clusters)
    if n_walls < 2:
        return 0

    cluster_arr = np.array(sorted(clusters))
    diffs = np.diff(cluster_arr)
    if len(diffs) == 0:
        return max(1, n_walls // 2)

    wrap_diff = 360 - cluster_arr[-1] + cluster_arr[0]
    all_diffs = np.append(diffs, wrap_diff)

    median_diff = np.median(all_diffs)
    small_diffs = all_diffs[all_diffs < median_diff * 0.7]
    large_diffs = all_diffs[all_diffs >= median_diff * 0.7]

    if len(small_diffs) > 0 and len(large_diffs) > 0:
        slot_pitch = np.median(small_diffs) + np.median(large_diffs)
        n_slots = int(round(360.0 / slot_pitch))
    else:
        slot_pitch = median_diff * 2
        n_slots = (int(round(360.0 / slot_pitch))
                   if slot_pitch > tol_angle else n_walls // 2)

    return max(1, n_slots)


# ═══════════════════════════════════════════════════════════════
# 닫힌 영역 기반 슬롯수
# ═══════════════════════════════════════════════════════════════

def count_slots_by_regions(entities: List[EntityInfo],
                           origin: Tuple[float, float] = (0.0, 0.0),
                           airgap_r_outer: float = None,
                           r_outer_max: float = None,
                           tol_angle: float = 2.0,
                           verbose: bool = True) -> Dict:
    """고정자 내부의 닫힌 다각형(Closed Polylines) 면적 및 배열 패턴 분석을 통해 슬롯(Slot) 수를 추정합니다.

    고정자에는 권선이 들어가는 슬롯이 일정한 각도의 피치를 두고 원형 배열로 반복됩니다.
    이 함수는 먼저 고정자 철심 내부에 존재하는 닫힌 면적들을 찾아내고(슬롯 및 권선 후보), 
    해당 후보군들의 면적 중심점(Centroid)이 이루는 각도 주기성을 통해 슬롯의 총 개수를 역산합니다.

    알고리즘:
    1. 고정자 형상 중 `is_closed=True` 인 폴리라인/스플라인을 선별하여 슬롯 또는 코일 단면으로 간주함.
    2. 필터링된 도형들의 면적 및 중심점을 계산하고 방위각(도 단위) 분포를 산출.
    3. 측정된 방위각이 균등한 피치 각도로 반복 배치된 패턴을 분석하여 슬롯 개수 도출.
    4. 명확한 닫힌 영역이 발견되지 않을 경우 ARC 엔티티나 Radial Line 쌍을 통한 보조(Fallback) 분석 수행.

    Args:
        entities (List[EntityInfo]): 고정자 도면 엔티티들.
        origin (Tuple[float, float]): 원형 구조의 회전 기준방향 좌표. 기본값 (0.0, 0.0).
        airgap_r_outer (float, optional): 공극(Airgap)의 외측 반경. 슬롯 데이터 필터링 시 너무 안쪽 형상을 배제하기 위함.
        r_outer_max (float, optional): 고정자 전체의 외부 반경 최댓값. 스크랩 형상을 배제하기 위함.
        tol_angle (float): 동일한 각도로 취급하기 위한 병합 오차 한계. 기본값 2.0도.
        verbose (bool): 콘솔 진행상황 로깅 여부. 기본값 True.

    Returns:
        Dict: 분석 결과를 담은 딕셔너리로, 다음 키들을 포함:
            - 'n_slots' (int): 최종 도출된 슬롯의 수.
            - 'method' (str): 추정에 사용된 최종 성공 알고리즘 (예: 'closed_polylines', 'radial_lines').
            - 'slot_pitch_deg' (float): 산출된 슬롯간 핏치 각도 (단위: Degree).
            - 'slot_regions' (List[Dict]): 분석 과정에서 확보된 권선/슬롯의 닫힌 면적 정보 리스트.
            - 'confidence' (float): 해당 결과에 대한 알고리즘적 신뢰도 평가 점수 (0.0 ~ 1.0).
    """
    ox, oy = origin

    # ── 1) 닫힌 폴리라인(슬롯 후보) ──
    closed_polys = []
    for ei in entities:
        if ei.is_closed and ei.etype in ('LWPOLYLINE', 'POLYLINE', 'SPLINE'):
            centroid_x = np.mean([p[0] for p in ei.points])
            centroid_y = np.mean([p[1] for p in ei.points])
            r_centroid = math.hypot(centroid_x - ox, centroid_y - oy)
            angle_deg = math.degrees(
                math.atan2(centroid_y - oy, centroid_x - ox)) % 360
            area = abs(ei.get_area(origin))

            # 반경 필터: airgap 바깥 ~ 스테이터 외경 안쪽
            if airgap_r_outer and r_centroid < airgap_r_outer * 0.9:
                continue
            if r_outer_max and r_centroid > r_outer_max * 1.1:
                continue

            closed_polys.append({
                'entity': ei,
                'centroid': (centroid_x, centroid_y),
                'r_centroid': r_centroid,
                'angle_deg': angle_deg,
                'area': area,
            })

    if closed_polys and len(closed_polys) >= 2:
        # 면적 기준 그룹핑 → 가장 큰 면적 = 슬롯 (코일 포함 슬롯 vs 작은 슬롯 오프닝)
        areas = np.array([cp['area'] for cp in closed_polys])
        if areas.max() > 0:
            # 큰 것 = 슬롯, 작은 것 = 코일/컨덕터
            area_median = np.median(areas)
            slot_candidates = [cp for cp in closed_polys
                               if cp['area'] >= area_median * 0.3]
        else:
            slot_candidates = closed_polys

        if len(slot_candidates) >= 2:
            angles = sorted(cp['angle_deg'] for cp in slot_candidates)
            n_slots, pitch, confidence = _slots_from_angles(angles, tol_angle)

            if n_slots > 0:
                if verbose:
                    print(f"[count_slots_by_regions] 닫힌 폴리라인 {len(slot_candidates)}개"
                          f" → 슬롯수={n_slots}, pitch={pitch:.2f}°, "
                          f"conf={confidence}")
                return {
                    'n_slots': n_slots,
                    'method': 'closed_polyline',
                    'slot_pitch_deg': pitch,
                    'slot_regions': slot_candidates,
                    'confidence': confidence,
                }

    # ── 2) ARC 배열 각도 분석 ──
    #    같은 반경의 ARC가 등간격으로 배치되면 → 슬롯수
    arc_angles_by_r = defaultdict(list)
    for ei in entities:
        if ei.etype == 'ARC' and ei.center and ei.radius:
            d = math.hypot(ei.center[0] - ox, ei.center[1] - oy)
            if d < 0.5:
                mid_a = ((ei.start_angle or 0) + (ei.end_angle or 360)) / 2
                r_key = round(ei.radius, 1)
                arc_angles_by_r[r_key].append(mid_a % 360)

    best_result = None
    for r_key, angles in sorted(arc_angles_by_r.items()):
        if len(angles) < 4:
            continue
        n_s, pitch, conf = _slots_from_angles(sorted(angles), tol_angle)
        if n_s > 0 and (best_result is None or conf == 'high'):
            best_result = {
                'n_slots': n_s,
                'method': f'arc_array_r{r_key:.1f}',
                'slot_pitch_deg': pitch,
                'slot_regions': [],
                'confidence': conf,
            }
            if conf == 'high':
                break

    if best_result:
        if verbose:
            print(f"[count_slots_by_regions] ARC 배열 → "
                  f"슬롯수={best_result['n_slots']}, conf={best_result['confidence']}")
        return best_result

    # ── 3) 전체 엔티티 각도 FFT ──
    all_angles = []
    for ei in entities:
        for p in ei.points:
            a = math.degrees(math.atan2(p[1] - oy, p[0] - ox)) % 360
            all_angles.append(a)

    if len(all_angles) >= 20:
        n_bins = 360
        counts, _ = np.histogram(all_angles, bins=n_bins, range=(0, 360))
        fft_mag = np.abs(np.fft.rfft(counts))
        freqs = np.fft.rfftfreq(n_bins, d=1.0)

        if len(fft_mag) > 1:
            fft_mag[0] = 0
            peak_idx = np.argmax(fft_mag)
            n_slots_fft = int(round(freqs[peak_idx] * 360))

            if 3 <= n_slots_fft <= 200:
                if verbose:
                    print(f"[count_slots_by_regions] FFT → 슬롯수={n_slots_fft}")
                return {
                    'n_slots': n_slots_fft,
                    'method': 'angle_fft',
                    'slot_pitch_deg': 360.0 / n_slots_fft,
                    'slot_regions': [],
                    'confidence': 'low',
                }

    if verbose:
        print("[count_slots_by_regions] 슬롯수 추정 실패")
    return {
        'n_slots': 0, 'method': 'none',
        'slot_pitch_deg': 0.0, 'slot_regions': [],
        'confidence': 'none',
    }


def _slots_from_angles(angles: List[float],
                       tol_angle: float = 2.0) -> Tuple[int, float, str]:
    """각도 리스트에서 등간격 반복 패턴 → (슬롯수, 피치, confidence)."""
    if len(angles) < 2:
        return (0, 0.0, 'none')

    angles = sorted(angles)

    # 클러스터링
    clusters = []
    current = [angles[0]]
    for i in range(1, len(angles)):
        if angles[i] - angles[i-1] <= tol_angle:
            current.append(angles[i])
        else:
            clusters.append(np.mean(current))
            current = [angles[i]]
    clusters.append(np.mean(current))

    # wrap-around merge
    if len(clusters) > 1 and (360 - clusters[-1] + clusters[0]) <= tol_angle:
        merged = np.mean([clusters[-1] - 360, clusters[0]])
        clusters = [merged % 360] + clusters[1:-1]

    if len(clusters) < 2:
        return (0, 0.0, 'none')

    cluster_arr = np.array(sorted(clusters))
    diffs = np.diff(cluster_arr)
    wrap_diff = 360 - cluster_arr[-1] + cluster_arr[0]
    all_diffs = np.append(diffs, wrap_diff)

    median_diff = np.median(all_diffs)
    if median_diff < 1.0:
        return (0, 0.0, 'none')

    n_slots = int(round(360.0 / median_diff))
    pitch = 360.0 / n_slots if n_slots > 0 else 0.0

    if len(all_diffs) > 2:
        cv = np.std(all_diffs) / median_diff
        confidence = 'high' if cv < 0.15 else ('medium' if cv < 0.35 else 'low')
    else:
        confidence = 'medium'

    return (n_slots, pitch, confidence)


# ═══════════════════════════════════════════════════════════════
# 강건한 슬롯수 추정 (교차 검증)
# ═══════════════════════════════════════════════════════════════

def estimate_slots_robust(entities: List[EntityInfo],
                          origin: Tuple[float, float] = (0.0, 0.0),
                          airgap_r_outer: float = None,
                          verbose: bool = True) -> Dict:
    """여러 모터 분석 알고리즘(방사형 선분 패턴 검사, 닫힌 면적 클러스터 반복 검사)을 
    동시에 수행하고 다수결/신뢰도 원칙으로 최종 고정자 슬롯 개수를 교차 검증(Cross-validation)합니다.

    단일 방법론에 비해 파손된 도면의 DXF나 엔티티에서도 누락 없이 정확한 슬롯 수를 
    판별할 수 있도록 다방면으로 기하학적 형상을 분석합니다.

    Args:
        entities (List[EntityInfo]): 고정자에 속하는 모든 단면 분석 엔티티.
        origin (Tuple[float, float]): 모터 회전 축의 중심 좌표점 (기본값: (0.0, 0.0)).
        airgap_r_outer (float, optional): 공극 반경 값으로 주어질 시 이보다 내부의 엔티티는 검증에서 배제함.
        verbose (bool): 콘솔에 추정된 알고리즘의 세부 결과 로깅 여부를 제어. 기본값 True.

    Returns:
        Dict: 다음 정보를 포함하는 분석 결과 검증 딕셔너리:
            - 'n_slots' (int): 최종적으로 여러 방법에 의해 가장 유력하게 합의된 슬롯 수. 측정 불가 시 0.
            - 'results' (List[Tuple[str, int, str]]): 사용된 방식의 이름, 추정된 개수, 각 기법별 신뢰수준 내역.
            - 'agreement' (bool): 복수의 기법의 결과가 일치하여 확정되었는지 여부를 나타내는 참/거짓 값.
    """
    results = []

    # 방법 1: Radial LINE 기반
    n1 = count_slots(entities, origin)
    if n1 > 0:
        results.append(('radial_line', n1, 'medium'))

    # 방법 2: 닫힌 영역 기반
    r2 = count_slots_by_regions(entities, origin,
                                airgap_r_outer=airgap_r_outer,
                                verbose=False)
    if r2['n_slots'] > 0:
        results.append((r2['method'], r2['n_slots'], r2['confidence']))

    if not results:
        if verbose:
            print("[slots_robust] 슬롯수 추정 실패 (모든 방법)")
        return {'n_slots': 0, 'results': results, 'agreement': False}

    # ── confidence 우선 선택 ──
    high   = [(m, n, c) for m, n, c in results if c == 'high']
    medium = [(m, n, c) for m, n, c in results if c == 'medium']

    if high:
        best_n = Counter(r[1] for r in high).most_common(1)[0][0]
    elif medium:
        best_n = Counter(r[1] for r in medium).most_common(1)[0][0]
    else:
        best_n = results[0][1]

    agreement = all(r[1] == best_n for r in results)

    if verbose:
        print(f"[slots_robust] 방법별 결과:")
        for method, n_s, conf in results:
            marker = " ★" if n_s == best_n else ""
            print(f"  {method}: {n_s}슬롯 (conf={conf}){marker}")
        print(f"  → 최종: {best_n}슬롯, agreement={agreement}")

    return {
        'n_slots': best_n,
        'results': results,
        'agreement': agreement,
    }


# ═══════════════════════════════════════════════════════════════
# 슬롯 내 컨덕터 탐지
# ═══════════════════════════════════════════════════════════════

def detect_slot_conductors(entities: List[EntityInfo],
                           origin: Tuple[float, float] = (0.0, 0.0),
                           n_slots: int = 0,
                           slot_pitch_deg: float = 0.0,
                           airgap_r_outer: float = None,
                           r_outer_max: float = None,
                           area_tol: float = 0.3,
                           verbose: bool = True) -> Dict:
    """고정자의 각 슬롯 내부에 반복적으로 배치된 컨덕터(Conductor/Coil) 객체를 탐지합니다.

    단일 슬롯 공간 안에 배치된 개별 권선의 가닥(도선 단면)을 분석하여 슬롯 1개당 속해 있는 
    도체의 총 가닥 수와 그 배열(반경 방향 직렬/병렬 분할 등)을 도출합니다.

    알고리즘:
    1. 고정자 설계 평면에서 작은 면적을 보유한 폐곡선(닫힌 폴리라인)들을 수집.
    2. 수집된 다각형들의 면적 편차가 `area_tol` 허용 범위 안에 드는 것들을 동일 도체 그룹으로 묶음.
    3. 확보된 고정자 슬롯 피치 정보(`slot_pitch_deg`)를 기준으로 전체 도체들의 방위각을 
       슬롯 각도 단위의 모듈로 연산(`% pitch`)하여 단일 슬롯 좌표계 안으로 사상(Mapping)시킴.
    4. 중첩된 도체들의 반경(R) 위치와 각도 분포를 군집화하여 단일 슬롯 내 도체의 총 개수(N) 산출.

    Args:
        entities (List[EntityInfo]): 고정자 도면 엔티티 리스트.
        origin (Tuple[float, float]): 회전 중심(0.0, 0.0) 기본값.
        n_slots (int): 사전 분석된 모터의 슬롯 수 (선택사항, 입력 시 슬롯 할당 최적화에 사용).
        slot_pitch_deg (float): 사전 분석된 슬롯 간 각도 간격 (입력 시 군집화 성능 향상).
        airgap_r_outer (float, optional): 해당 값보다 안쪽의 형상은 도체가 아니라고 간주하여 무시(에어갭 경계).
        r_outer_max (float, optional): 해당 값보다 먼 외곽 데이터(고정자 요크/외피) 무시.
        area_tol (float): 컨덕터 면적 편차의 상대 허용치. 0.3 이면 ±30% 면적 간 같은 도체로 인정함. 기본값 0.3.
        verbose (bool): 세부 진행 로깅 활성화. 기본값 True.

    Returns:
        Dict: 단면 검사를 통해 파악한 권선 컨덕터 데이터셋. 주요 키:
            - 'has_conductors' (bool): 컨덕터 형상 탐지 성공 여부.
            - 'conductors_per_slot' (int): 슬롯 1개 내부에서 검출된 컨덕터 가닥들의 평균 수량.
            - 'total_conductors' (int): 전체 360도 공간에서 탐지된 모든 도체의 총 수.
            - 'conductor_entities' (List[EntityInfo]): 컨덕터로 식별 통과된 원본 형상 엔티티들.
            - 'conductor_area' (float): 추출된 단일 도체 단면들의 평균 면적.
            - 'conductor_groups' (List[Dict]): 슬롯 번호별로 소속된 컨덕터들의 로컬 정보 딕셔너리 리스트.
            - 'confidence' (str): 추론 결과의 신뢰수준 ('high', 'medium', 'low').
    """
    ox, oy = origin

    # ── 경계 반경 자동 추정 ──
    if airgap_r_outer is None or r_outer_max is None:
        all_r = [math.hypot(p[0] - ox, p[1] - oy) for ei in entities for p in ei.points]
        if all_r:
            if airgap_r_outer is None:
                airgap_r_outer = min(all_r) * 0.95
            if r_outer_max is None:
                r_outer_max = max(all_r) * 1.05

    if slot_pitch_deg <= 0 and n_slots > 0:
        slot_pitch_deg = 360.0 / n_slots

    # ── 1) 슬롯 영역 내 닫힌 폴리라인 수집 ──
    candidate_conductors = []
    for ei in entities:
        if not (ei.is_closed and ei.etype in ('LWPOLYLINE', 'POLYLINE', 'SPLINE', 'CIRCLE')):
            continue

        if ei.etype == 'CIRCLE' and ei.center:
            cx, cy = ei.center
            r_c = math.hypot(cx - ox, cy - oy)
            # 에어갭 근처의 원은 동심원일 가능성 → 제외
            if ei.radius and math.hypot(cx - ox, cy - oy) < 1.0:
                continue
            area = math.pi * (ei.radius or 0) ** 2
            angle_deg = math.degrees(math.atan2(cy - oy, cx - ox)) % 360
        else:
            if len(ei.points) < 3:
                continue
            cx = np.mean([p[0] for p in ei.points])
            cy = np.mean([p[1] for p in ei.points])
            r_c = math.hypot(cx - ox, cy - oy)
            area = abs(ei.get_area(origin))
            angle_deg = math.degrees(math.atan2(cy - oy, cx - ox)) % 360

        # 반경 필터: 슬롯 영역 이내
        if r_c < (airgap_r_outer or 0):
            continue
        if r_outer_max and r_c > r_outer_max:
            continue

        # 면적 필터: 너무 크거나 너무 작으면 제외
        if area < 0.01:
            continue
        # 슬롯 전체 면적의 절반보다 큰 것은 슬롯 자체일 수 있으므로 후처리에서 필터링

        candidate_conductors.append({
            'entity': ei,
            'centroid': (cx, cy),
            'r_centroid': r_c,
            'angle_deg': angle_deg,
            'area': area,
        })

    if not candidate_conductors:
        if verbose:
            print("[detect_conductors] 닫힌 폴리라인 없음 → 컨덕터 탐지 불가")
        return _empty_conductor_result()

    if verbose:
        print(f"[detect_conductors] 닫힌 폴리라인 후보: {len(candidate_conductors)}개")

    # ── 2) 면적 클러스터링 → 같은 타입의 객체 그룹 ──
    areas = np.array([c['area'] for c in candidate_conductors])
    area_sorted = np.sort(areas)

    # 면적 기준으로 그룹핑 (같은 면적 ±tol_area)
    area_groups = []  # list of (rep_area, [indices])
    used = set()
    for i, a in enumerate(areas):
        if i in used:
            continue
        group_idx = [i]
        used.add(i)
        for j in range(i + 1, len(areas)):
            if j in used:
                continue
            if abs(areas[j] - a) / max(a, 1e-6) < area_tol:
                group_idx.append(j)
                used.add(j)
        if len(group_idx) >= 2:  # 최소 2개이상 반복해야 컨덕터
            rep_area = np.mean(areas[group_idx])
            area_groups.append((rep_area, group_idx))

    if not area_groups:
        if verbose:
            print("[detect_conductors] 반복되는 면적 그룹 없음")
        return _empty_conductor_result()

    # 가장 많이 반복되는 면적 그룹 = 컨덕터
    area_groups.sort(key=lambda g: len(g[1]), reverse=True)
    best_area, best_indices = area_groups[0]
    conductor_items = [candidate_conductors[i] for i in best_indices]

    if verbose:
        print(f"[detect_conductors] 주요 컨덕터 그룹: 면적≈{best_area:.3f}, "
              f"{len(conductor_items)}개")

    # ── 3) 슬롯별 그룹핑 ──
    if slot_pitch_deg > 0:
        # 각 컨덕터의 slot index 계산
        for c in conductor_items:
            c['slot_idx'] = int(c['angle_deg'] / slot_pitch_deg) % max(n_slots, 1)

        slot_groups = defaultdict(list)
        for c in conductor_items:
            slot_groups[c['slot_idx']].append(c)

        # 슬롯당 컨덕터 수 = 가장 흔한 개수
        counts_per_slot = [len(v) for v in slot_groups.values()]
        if counts_per_slot:
            conductors_per_slot = int(np.median(counts_per_slot))
        else:
            conductors_per_slot = len(conductor_items) // max(n_slots, 1)
    else:
        # 슬롯 정보 없으면 전체 각도 분포로 추정
        angles = sorted(c['angle_deg'] for c in conductor_items)
        if len(angles) >= 4:
            diffs = np.diff(angles)
            diffs = np.append(diffs, 360 - angles[-1] + angles[0])
            # 큰 간격 = 슬롯 경계, 작은 간격 = 같은 슬롯 내 컨덕터
            median_diff = np.median(diffs)
            small_count = np.sum(diffs < median_diff * 0.5)
            large_count = np.sum(diffs >= median_diff * 0.5)
            if large_count > 0:
                conductors_per_slot = max(1, int(round(small_count / large_count)) + 1)
            else:
                conductors_per_slot = len(conductor_items)
        else:
            conductors_per_slot = len(conductor_items)
        slot_groups = {}

    # ── 4) radial 방향 반복 확인 ──
    #    같은 슬롯 내에서 r_centroid가 등간격으로 증가하면 → 컨덕터 확실
    radial_repeats = False
    for slot_idx, items in (slot_groups.items() if slot_groups else [(0, conductor_items)]):
        if len(items) < 2:
            continue
        r_values = sorted(c['r_centroid'] for c in items)
        r_diffs = np.diff(r_values)
        if len(r_diffs) >= 1:
            cv = np.std(r_diffs) / np.mean(r_diffs) if np.mean(r_diffs) > 0 else 999
            if cv < 0.5:  # 등간격이면 cv가 작음
                radial_repeats = True
                break

    confidence = 'high' if radial_repeats else ('medium' if len(conductor_items) >= 6 else 'low')

    conductor_entities = [c['entity'] for c in conductor_items]

    if verbose:
        print(f"[detect_conductors] ★ 결과:")
        print(f"  컨덕터 탐지: True")
        print(f"  전체 컨덕터: {len(conductor_items)}개")
        print(f"  슬롯당 컨덕터: {conductors_per_slot}개")
        print(f"  개별 면적: {best_area:.3f}")
        print(f"  radial 반복: {radial_repeats}")
        print(f"  confidence: {confidence}")
        if slot_groups:
            print(f"  슬롯 분포: {dict(Counter(len(v) for v in slot_groups.values()))}")

    return {
        'has_conductors': True,
        'conductors_per_slot': conductors_per_slot,
        'total_conductors': len(conductor_items),
        'conductor_entities': conductor_entities,
        'conductor_area': best_area,
        'conductor_groups': dict(slot_groups) if slot_groups else {},
        'radial_repeat': radial_repeats,
        'confidence': confidence,
    }


def _empty_conductor_result() -> Dict:
    """빈 컨덕터 탐지 결과."""
    return {
        'has_conductors': False,
        'conductors_per_slot': 0,
        'total_conductors': 0,
        'conductor_entities': [],
        'conductor_area': 0.0,
        'conductor_groups': {},
        'radial_repeat': False,
        'confidence': 'none',
    }
