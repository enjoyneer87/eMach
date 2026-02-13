"""
pyMotorGeo.analysis_stator
===========================
고정자(스테이터) 분석: 슬롯수 추정, 닫힌 영역 기반 슬롯수 추정, 컨덕터 탐지.

주요 함수
---------
- count_slots               : Radial LINE 각도 분포 기반 슬롯수 추정
- count_slots_by_regions    : 닫힌 영역(closed region) 기반 슬롯수 추정
- estimate_slots_robust     : 두 방법 교차 검증 → 강건한 슬롯수
- detect_slot_conductors    : 슬롯 내 반복 객체(컨덕터) 탐지
"""

import math
import numpy as np
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Optional

from .core import EntityInfo


# ═══════════════════════════════════════════════════════════════
# Radial LINE 기반 슬롯수
# ═══════════════════════════════════════════════════════════════

def count_slots(entities: List[EntityInfo],
                origin: Tuple[float, float] = (0.0, 0.0),
                tol_angle: float = 2.0) -> int:
    """
    방사형 LINE의 각도 분포로 슬롯 수를 추정합니다.

    개선 로직:
    1. 방사형 LINE 각도 수집
    2. 근접 각도 클러스터링 → 개별 슬롯 벽(slot wall) 위치
    3. 인접 클러스터 쌍(pair) 감지 → 한 슬롯 = 2 벽
    4. 슬롯 수 = 슬롯 쌍 수
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
    """
    닫힌 영역 분석으로 슬롯수를 추정합니다.

    알고리즘
    --------
    1. 스테이터 내 닫힌 폴리라인 → 슬롯/코일 후보
    2. 후보의 centroid 각도 분포 → 등간격 반복 → 슬롯수
    3. 닫힌 폴리라인이 없으면 → ARC 배열 각도 분석
    4. Radial LINE 벽 쌍 분석 (fallback)

    Parameters
    ----------
    entities     : 스테이터 엔티티
    origin       : 원점
    airgap_r_outer : 에어갭 외측 반경 (슬롯은 이 바깥)
    r_outer_max  : 스테이터 외경 (슬롯은 이 안쪽)
    tol_angle    : 각도 클러스터 허용 오차
    verbose      : 상세 출력

    Returns
    -------
    dict with n_slots, method, slot_pitch_deg, slot_regions, confidence
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
    """
    여러 방법으로 슬롯수를 추정하고 교차 검증합니다.

    Returns
    -------
    dict with n_slots, results, agreement
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
    """
    스테이터 슬롯 내 반복 객체(컨덕터/코일)를 탐지합니다.

    알고리즘
    --------
    1. 슬롯 영역 내 닫힌 폴리라인 수집
    2. 면적이 비슷한 그룹 → 같은 타입의 객체
    3. 같은 슬롯 내에서 radial 방향 반복 → 컨덕터
    4. 각 슬롯에 N개 컨덕터 → 권선 정보 추출

    Parameters
    ----------
    entities       : 스테이터 엔티티
    origin         : 원점
    n_slots        : 슬롯수 (미리 알고 있으면)
    slot_pitch_deg : 슬롯 피치 (미리 알고 있으면)
    airgap_r_outer : 에어갭 외측 반경
    r_outer_max    : 스테이터 외경
    area_tol       : 면적 비교 허용 오차 (비율, 기본 0.3 = ±30%)
    verbose        : 상세 출력

    Returns
    -------
    dict with:
        - 'has_conductors'       : bool
        - 'conductors_per_slot'  : int — 슬롯당 컨덕터 수
        - 'total_conductors'     : int — 전체 컨덕터 수
        - 'conductor_entities'   : list[EntityInfo] — 컨덕터로 식별된 엔티티
        - 'conductor_area'       : float — 개별 컨덕터 면적 (대표값)
        - 'conductor_groups'     : list[dict] — 슬롯별 컨덕터 정보
        - 'confidence'           : str
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
