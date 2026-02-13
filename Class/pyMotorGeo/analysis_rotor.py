"""
pyMotorGeo.analysis_rotor
=========================
회전자(로터) 분석: 극수 추정, 닫힌 영역 기반 극수 추정.

주요 함수
---------
- count_poles               : ARC 각도 분포 기반 극수 추정
- count_poles_by_regions    : 닫힌 영역(closed region) 기반 극수 추정
- estimate_poles_robust     : 두 방법 교차 검증 → 강건한 극수 반환
"""

import math
import numpy as np
from collections import Counter
from typing import List, Tuple, Dict, Optional

from .core import EntityInfo


# ═══════════════════════════════════════════════════════════════
# ARC 각도 분포 기반 극수
# ═══════════════════════════════════════════════════════════════

def count_poles(entities: List[EntityInfo],
                origin: Tuple[float, float] = (0.0, 0.0),
                tol_r: float = 0.5,
                tol_angle: float = 3.0) -> int:
    """에어갭 근처 호/원을 각도 분포로 분석해 극수를 추정."""
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
    """
    닫힌 영역(닫힌 폴리라인 + 반복 ARC 그룹)으로 극수를 추정합니다.

    알고리즘
    --------
    1. 로터 내 닫힌 폴리라인(LWPOLYLINE/POLYLINE) → 자석 후보
    2. 자석 후보의 centroid 각도 분포 → 등간격 반복 → 극수
    3. 닫힌 폴리라인이 없으면 → 특정 반경 ARC의 반복 패턴 → 극수
    4. entity 각도 히스토그램 피크 → 극수

    Parameters
    ----------
    entities : 로터 엔티티 목록
    origin : 원점
    airgap_r_inner : 에어갭 내측 반경 (자석 후보 필터링에 사용)
    tol_angle : 각도 클러스터 허용 오차
    verbose : 상세 출력

    Returns
    -------
    dict with:
        - 'n_poles'        : int — 극수
        - 'method'         : str — 사용된 방법
        - 'pole_pitch_deg' : float — 극 피치 (도)
        - 'magnet_regions' : list — 식별된 자석 영역 정보
        - 'confidence'     : str — 'high' / 'medium' / 'low'
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
    """
    각도 리스트에서 등간격 반복 패턴을 분석해 (극수, 피치, confidence) 반환.
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
    """
    여러 방법으로 극수를 추정하고 교차 검증합니다.

    1. detect_circular_array_pattern (topology 모듈)  — 있으면 사용
    2. count_poles (ARC 각도 기반)
    3. count_poles_by_regions (닫힌 영역 / FFT 기반)

    Returns
    -------
    dict with:
        - 'n_poles'     : int   — 최종 극수
        - 'results'     : list  — 각 방법별 (method, n_poles, confidence)
        - 'agreement'   : bool  — 방법 간 합의 여부
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
