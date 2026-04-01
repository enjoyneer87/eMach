"""
pyMotorGeo.analysis_rotor
=========================

회전자(Rotor) 기하 데이터로부터 모터의 극수(Pole Number)를 추정하는 모듈입니다.
닫힌 영역(매입 자석 등)의 방위각 분포, 원호(구조물 경계) 배열의 주기성, 혹은 선분들의 
조화 해석(FFT) 등 다양한 알고리즘을 혼합하여 가장 신뢰도 높은 극수를 도출합니다.

주요 클래스
-----------
- RotorCounter             : 회전자 극수 분석 클래스 (ComponentCounter 상속)

주요 함수 (하위 호환성)
-----------------------
- count_poles               : 원점 기준 반경 분포 내의 ARC 배열 간격을 통한 극수 추정
- count_poles_by_regions    : 닫힌 폴리라인(자석 후보 영역등)의 중심점 주기성을 통한 극수 추정
- estimate_poles_robust     : 여러 추정 방식을 교차 검증하여 최종적으로 가장 강건한 극수를 반환
"""

import math
import numpy as np
from collections import Counter
from typing import List, Tuple, Dict, Optional

from core import EntityInfo
from analysis_base import ComponentCounter


# ═══════════════════════════════════════════════════════════════
# RotorCounter 클래스 (OOP 기반)
# ═══════════════════════════════════════════════════════════════

class RotorCounter(ComponentCounter):
    """
    회전자(Rotor)의 극수를 다양한 방법으로 추정하는 클래스입니다.
    
    ComponentCounter 추상 클래스를 구현하며, ARC 분포, 닫힌 영역 패턴,
    FFT 주파수 분석 등 여러 알고리즘을 조합하여 가장 신뢰도 높은 극수를 도출합니다.
    
    Attributes:
        component_type (str): "rotor"
        count_keyword (str): "poles"
    """
    
    def __init__(self):
        """RotorCounter 초기화."""
        super().__init__(component_type="rotor", count_keyword="poles")
    
    def count(self, 
              entities: List[EntityInfo],
              origin: Tuple[float, float] = (0.0, 0.0),
              **kwargs) -> int:
        """
        ARC 기반 극수 추정 (count_poles와 동일).
        
        Args:
            entities (List[EntityInfo]): 회전자 엔티티 리스트.
            origin (Tuple[float, float]): 회전 중심 좌표.
            **kwargs: tol_r, tol_angle 등.
        
        Returns:
            int: 추정된 극수.
        """
        tol_r = kwargs.get('tol_r', 0.5)
        tol_angle = kwargs.get('tol_angle', 3.0)
        return count_poles(entities, origin, tol_r, tol_angle)
    
    def count_by_regions(self,
                        entities: List[EntityInfo],
                        origin: Tuple[float, float] = (0.0, 0.0),
                        **kwargs) -> Dict:
        """
        닫힌 영역 기반 극수 추정 (count_poles_by_regions와 동일).
        
        Args:
            entities (List[EntityInfo]): 회전자 엔티티 리스트.
            origin (Tuple[float, float]): 회전 중심 좌표.
            **kwargs: airgap_r_inner, tol_angle, verbose 등.
        
        Returns:
            Dict: 분석 결과.
        """
        airgap_r_inner = kwargs.get('airgap_r_inner', None)
        tol_angle = kwargs.get('tol_angle', 3.0)
        verbose = kwargs.get('verbose', False)
        return count_poles_by_regions(entities, origin, airgap_r_inner, tol_angle, verbose)
    
    def estimate_robust(self,
                       entities: List[EntityInfo],
                       origin: Tuple[float, float] = (0.0, 0.0),
                       verbose: bool = True,
                       **kwargs) -> Dict:
        """
        교차 검증을 통한 강건한 극수 추정 (estimate_poles_robust와 동일).
        
        Args:
            entities (List[EntityInfo]): 회전자 엔티티 리스트.
            origin (Tuple[float, float]): 회전 중심 좌표.
            verbose (bool): 상세 로깅 여부.
            **kwargs: airgap_r_inner 등.
        
        Returns:
            Dict: 검증 결과.
        """
        airgap_r_inner = kwargs.get('airgap_r_inner', None)
        return estimate_poles_robust(entities, origin, airgap_r_inner, verbose)


# ═══════════════════════════════════════════════════════════════
# ARC 각도 분포 기반 극수 (함수형 인터페이스 - 하위 호환성)
# ═══════════════════════════════════════════════════════════════

def count_poles(entities: List[EntityInfo],
                origin: Tuple[float, float] = (0.0, 0.0),
                tol_r: float = 0.5,
                tol_angle: float = 3.0) -> int:
    """원점을 중심으로 하는 호(ARC) 요소들의 방위각 분포를 분석하여 극수를 추정합니다.

    회전자의 외경 경계면이나 특정 에어갭 근처에 위치한 원호들은 대개 1극당 1개씩 혹은
    대칭적인 패턴으로 배열되어 있습니다. 이들 사이의 각도 차이(Pitch)를 계산해 전체 360도에 
    몇 개의 패턴이 들어가는지(극수) 산출합니다.

    Args:
        entities (List[EntityInfo]): 로터로 분류된 엔티티 리스트.
        origin (Tuple[float, float]): 로터의 회전 중심 좌표. 기본값은 (0.0, 0.0).
        tol_r (float): 호의 중심점이 반경 원점에 위치한다고 판단할 거리 오차 허용범위. 기본값은 0.5.
        tol_angle (float): 최소 유효 각도 간격(pitch). 기본값은 3.0도.

    Returns:
        int: 계산된 회전자의 극수 (Pole Number). 패턴을 찾지 못하면 0 반환.
    """
    mag_arcs = []
    for ei in entities:
        if ei.etype == 'ARC' and ei.center:
            d = math.hypot(ei.center[0] - origin[0], ei.center[1] - origin[1])
            if d < tol_r:
                mag_arcs.append(ei.angle_deg)
    if not mag_arcs:
        return 0
    mag_arcs.sort()
    diffs = [mag_arcs[i+1] - mag_arcs[i] for i in range(len(mag_arcs)-1)]
    if not diffs:
        return len(mag_arcs)
    pitch = float(np.median(diffs))
    if pitch < tol_angle:
        pitch = 360 / max(len(mag_arcs), 1)
    return int(round(360 / pitch))


# ═══════════════════════════════════════════════════════════════
# 닫힌 영역(closed region) 기반 극수
# ═══════════════════════════════════════════════════════════════

def count_poles_by_regions(entities: List[EntityInfo],
                           origin: Tuple[float, float] = (0.0, 0.0),
                           airgap_r_inner: float = None,
                           tol_angle: float = 3.0,
                           verbose: bool = True) -> Dict:
    """닫힌 영역(면적) 또는 원형 배열(ARC 패턴), 그리고 FFT 방식을 총동원하여 극수를 단계적으로 추정합니다.

    알고리즘:
    1. 로터 내 닫힌 폴리라인(LWPOLYLINE 등)을 후보 자석 영역으로 탐지합니다.
    2. 후보들의 면적을 비교해 주된 영역(Magnet)을 걸러내고, 각 영역의 질량중심(Centroid) 방위각의 등간격 주기를 통해 극수를 계산합니다.
    3. 만약 닫힌 폴리라인을 찾지 못했다면 동일한 중심 거리를 가진 `ARC`들의 반복 주기를 계산합니다.
    4. 위 방법들이 모두 통하지 않으면 전역 엔티티 노드들의 히스토그램 스펙트럼에서 FFT를 수행하여 주요 주파수를 극수로 반환합니다.

    Args:
        entities (List[EntityInfo]): 로터로 분류된 엔티티 리스트.
        origin (Tuple[float, float]): 로터의 회전 중심 좌표. 기본값은 (0.0, 0.0).
        airgap_r_inner (float, optional): 에어갭의 내부 반경(공극 면). (현재 구현에서 명시적 제약보단 정보용으로 전달됨.)
        tol_angle (float): 같은 위상 클러스터로 묶을 각도(도 단위) 최대 허용 오차. 기본값은 3.0.
        verbose (bool): 과정이나 추정 성공 사유를 콘솔에 출력할지 여부. 기본값은 True.

    Returns:
        Dict: 추정된 극수와 방법론 등을 담은 딕셔너리
            - 'n_poles' (int): 산출된 모터의 극수 (실패시 0).
            - 'method' (str): 채택된 알고리즘의 이름 (예: 'closed_polyline', 'arc_group_r...', 'fft_histogram', 'empty').
            - 'pole_pitch_deg' (float): 추정된 1극에 해당하는 기계각 (도 단위).
            - 'magnet_regions' (List[Dict]): 분석 과정에서 자석이라고 간주된 후보의 정보 리스트.
            - 'confidence' (str): 추정치에 대한 신뢰도 지표 ('high', 'medium', 'low').
    """
    ox, oy = origin

    # ── 1) 닫힌 폴리라인에서 자석 후보 탐지 ──
    closed_polys = []
    for ei in entities:
        if ei.is_closed and ei.etype in ('LWPOLYLINE', 'POLYLINE', 'SPLINE'):
            centroid_x = np.mean([p[0] for p in ei.points])
            centroid_y = np.mean([p[1] for p in ei.points])
            r_centroid = math.hypot(centroid_x - ox, centroid_y - oy)
            angle_deg = math.degrees(math.atan2(centroid_y - oy, centroid_x - ox)) % 360
            area = abs(ei.get_area(origin))
            closed_polys.append({
                'entity': ei,
                'centroid': (centroid_x, centroid_y),
                'r_centroid': r_centroid,
                'angle_deg': angle_deg,
                'area': area,
            })

    if closed_polys and len(closed_polys) >= 2:
        # 면적이 비슷한(같은 타입) 그룹으로 묶기
        areas = np.array([cp['area'] for cp in closed_polys])
        if areas.max() > 0:
            # 가장 흔한 면적 그룹 = 자석
            area_median = np.median(areas)
            magnet_candidates = [cp for cp in closed_polys
                                 if 0.3 * area_median < cp['area'] < 3.0 * area_median]
        else:
            magnet_candidates = closed_polys

        if len(magnet_candidates) >= 2:
            angles = sorted(cp['angle_deg'] for cp in magnet_candidates)
            n_poles, pitch, confidence = _poles_from_angles(
                angles, tol_angle, method_name='closed_poly')

            if n_poles > 0:
                if verbose:
                    print(f"[count_poles_by_regions] 닫힌 폴리라인 {len(magnet_candidates)}개"
                          f" → 극수={n_poles}, pitch={pitch:.2f}°, conf={confidence}")
                return {
                    'n_poles': n_poles, 'method': 'closed_polyline',
                    'pole_pitch_deg': pitch,
                    'magnet_regions': magnet_candidates,
                    'confidence': confidence,
                }

    # ── 2) 에어갭 근처 ARC 그룹 ──
    #    특정 반경의 ARC가 등간격으로 반복되면 → 극수
    concentric_arcs = []
    for ei in entities:
        if ei.etype == 'ARC' and ei.center and ei.radius:
            d = math.hypot(ei.center[0] - ox, ei.center[1] - oy)
            if d < 0.5:
                mid_angle = ((ei.start_angle or 0) + (ei.end_angle or 360)) / 2
                mid_angle = mid_angle % 360
                concentric_arcs.append({
                    'radius': ei.radius,
                    'mid_angle': mid_angle,
                    'span_deg': ei.angle_deg,
                })

    # 같은 반경끼리 그룹
    if concentric_arcs:
        from collections import defaultdict
        r_groups = defaultdict(list)
        for arc in concentric_arcs:
            r_key = round(arc['radius'], 1)
            r_groups[r_key].append(arc['mid_angle'])

        # ARC 수가 4개 이상인 반경 그룹에서 극수 추정
        best_result = None
        for r_key, angles in sorted(r_groups.items()):
            if len(angles) < 4:
                continue
            angles_sorted = sorted(angles)
            n_p, pitch, conf = _poles_from_angles(angles_sorted, tol_angle, 'arc_group')
            if n_p > 0 and (best_result is None or conf == 'high'):
                best_result = {
                    'n_poles': n_p, 'method': f'arc_group_r{r_key:.1f}',
                    'pole_pitch_deg': pitch,
                    'magnet_regions': [],
                    'confidence': conf,
                }
                if conf == 'high':
                    break

        if best_result:
            if verbose:
                print(f"[count_poles_by_regions] ARC 그룹 → "
                      f"극수={best_result['n_poles']}, conf={best_result['confidence']}")
            return best_result

    # ── 3) 전체 엔티티 각도 히스토그램 ──
    all_angles = []
    for ei in entities:
        for p in ei.points:
            a = math.degrees(math.atan2(p[1] - oy, p[0] - ox)) % 360
            all_angles.append(a)

    if len(all_angles) >= 10:
        n_bins = 360
        counts, bin_edges = np.histogram(all_angles, bins=n_bins, range=(0, 360))
        # FFT로 주요 주파수 추출
        fft_mag = np.abs(np.fft.rfft(counts))
        freqs = np.fft.rfftfreq(n_bins, d=1.0)  # cycles per degree bin

        # DC 제외, 가장 큰 피크 주파수
        if len(fft_mag) > 1:
            fft_mag[0] = 0  # DC 제거
            peak_idx = np.argmax(fft_mag)
            peak_freq = freqs[peak_idx]  # cycles per bin
            n_poles_fft = int(round(peak_freq * 360))

            if 2 <= n_poles_fft <= 200:
                if verbose:
                    print(f"[count_poles_by_regions] FFT 기반 → 극수={n_poles_fft}")
                return {
                    'n_poles': n_poles_fft, 'method': 'angle_fft',
                    'pole_pitch_deg': 360.0 / n_poles_fft,
                    'magnet_regions': [],
                    'confidence': 'low',
                }

    if verbose:
        print("[count_poles_by_regions] 극수 추정 실패")
    return {
        'n_poles': 0, 'method': 'none',
        'pole_pitch_deg': 0.0, 'magnet_regions': [],
        'confidence': 'none',
    }


def _poles_from_angles(angles: List[float],
                       tol_angle: float = 3.0,
                       method_name: str = '') -> Tuple[int, float, str]:
    """1차원으로 나열된 각도 세트의 간격(Pitch) 균일도를 분석하여 극수를 도출하는 헬퍼 함수입니다.

    인접한 각도 데이터들 간의 차이 리스트에서 중앙값을 취해 평균 간격을 구합니다. 
    도출된 피치 간격을 360도로 나누어 정수 배의 극수가 나오면 `high` 또는 `medium`의 평점을 부여하고, 
    오차 범위를 초과하는 불규칙한 데이터의 경우 `low`나 0을 반환합니다.

    Args:
        angles (List[float]): 오름차순 또는 무작위로 정렬된 방위각 리스트.
        tol_angle (float): 간격 계산 시 균일하다고 판단할 허용 오차 한계. 기본값은 3.0도.
        method_name (str): 디버깅 출력을 위한 호출 메서드명 (내부 무방).

    Returns:
        Tuple[int, float, str]: 
            - 추정된 극수 (정수)
            - 단일 극의 피치 기계각 (실수)
            - 신뢰 평점 문자열 ('high', 'medium', 'low', 'none')
    """
    if len(angles) < 2:
        return (0, 0.0, 'none')

    angles = sorted(angles)
    diffs = []
    for i in range(len(angles) - 1):
        diffs.append(angles[i+1] - angles[i])
    # wrap-around
    diffs.append(360 - angles[-1] + angles[0])

    diffs = np.array(diffs)
    median_diff = np.median(diffs)

    if median_diff < 1.0:
        return (0, 0.0, 'none')

    n_poles = int(round(360.0 / median_diff))
    pitch = 360.0 / n_poles if n_poles > 0 else 0.0

    # confidence: 간격의 std / median 이 작으면 high
    if len(diffs) > 2:
        cv = np.std(diffs) / median_diff
        if cv < 0.15:
            confidence = 'high'
        elif cv < 0.35:
            confidence = 'medium'
        else:
            confidence = 'low'
    else:
        confidence = 'medium'

    return (n_poles, pitch, confidence)


# ═══════════════════════════════════════════════════════════════
# 강건한 극수 추정 (교차 검증)
# ═══════════════════════════════════════════════════════════════

def estimate_poles_robust(entities: List[EntityInfo],
                          origin: Tuple[float, float] = (0.0, 0.0),
                          airgap_r_inner: float = None,
                          verbose: bool = True) -> Dict:
    """여러 가지 추정 알고리즘을 사용해 도출된 극수들을 교차 검증하고 가장 신뢰도 높은 최종 극수를 계산합니다.

    내부적으로 3가지 접근법을 조합합니다:
    1. Circular Array Pattern 기반 (`topology` 모듈)
    2. 에어갭 근처 호(ARC)의 방위각 간격 분포 (`count_poles`)
    3. 닫힌 영역 폴리라인 또는 FFT 주파수 기반 (`count_poles_by_regions`)

    여러 방법들이 동일한 극수 결과를 보고하는 빈도(Majority Vote)와 각 방법 단독이 가지는 
    confidence 점수를 비교하여 최종 극수를 확정합니다.

    Args:
        entities (List[EntityInfo]): 로터의 도면 엔티티 리스트.
        origin (Tuple[float, float]): 중심 원점 좌표.
        airgap_r_inner (float, optional): 공극 내부 반경.
        verbose (bool): 과정 상세 출력 여부.

    Returns:
        Dict: 검증 결과 요약 딕셔너리
            - 'n_poles' (int): 모든 알고리즘 결과를 취합하여 내린 최종 극수. 신뢰되는 결과가 없으면 0.
            - 'results' (List[Tuple[str, int, str]]): 각 방법의 (메서드명, 추정된 극수, 신뢰도) 튜플 리스트.
            - 'agreement' (bool): 서로 다른 방법들이 한 가지 극수에 만장일치 또는 다수결 판정으로 합의했는지 여부.
    """
    results = []

    # 방법 1: count_poles (ARC 분포)
    n1 = count_poles(entities, origin)
    if n1 > 0:
        results.append(('arc_distribution', n1, 'medium'))

    # 방법 2: count_poles_by_regions (닫힌 영역 + FFT)
    r2 = count_poles_by_regions(entities, origin,
                                airgap_r_inner=airgap_r_inner,
                                verbose=False)
    if r2['n_poles'] > 0:
        results.append((r2['method'], r2['n_poles'], r2['confidence']))

    if not results:
        if verbose:
            print("[poles_robust] 극수 추정 실패 (모든 방법)")
        return {'n_poles': 0, 'results': results, 'agreement': False}

    # ── confidence 우선 선택 ──
    _conf_order = {'high': 3, 'medium': 2, 'low': 1, 'none': 0}
    high   = [(m, n, c) for m, n, c in results if c == 'high']
    medium = [(m, n, c) for m, n, c in results if c == 'medium']

    if high:
        # high 내에서 합의 여부 확인 후 최빈값
        best_n = Counter(r[1] for r in high).most_common(1)[0][0]
    elif medium:
        best_n = Counter(r[1] for r in medium).most_common(1)[0][0]
    else:
        best_n = results[0][1]

    agreement = all(r[1] == best_n for r in results)

    if verbose:
        print(f"[poles_robust] 방법별 결과:")
        for method, n_p, conf in results:
            marker = " ★" if n_p == best_n else ""
            print(f"  {method}: {n_p}극 (conf={conf}){marker}")
        print(f"  → 최종: {best_n}극, agreement={agreement}")

    return {
        'n_poles': best_n,
        'results': results,
        'agreement': agreement,
    }
