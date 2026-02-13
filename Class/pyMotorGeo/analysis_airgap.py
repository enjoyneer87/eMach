"""
pyMotorGeo.analysis_airgap
==========================
공극(에어갭) 탐지, 동심원 분석, 원점 탐지, 내/외전형 판별, Stator/Rotor 분리.

주요 함수
---------
- find_origin_candidates        : DXF 헤더 + 엔티티 기반 원점 후보
- find_concentric_radii         : 동심원 반경 대표값 목록
- find_closed_regions           : 닫힌 폴리라인 / 원 분석
- analyze_closed_regions_for_motor_type : 닫힌 영역으로 모터 타입 판별
- classify_inner_outer_rotor     : 내전형/외전형 판별
- find_airgap_radius            : 동심원 간격 기반 에어갭
- find_airgap_by_arc_span       : ARC angular span 기반 에어갭
- split_by_layer                : 레이어 기반 분리
- split_by_radius               : 반경 기반 분리
- split_stator_rotor            : 자동 분리 (레이어 → 반경 fallback)
- split_stator_rotor_by_arc_span: arc_span 에어갭 + midpoint 분리
"""

import math
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional

from .core import EntityInfo


# ═══════════════════════════════════════════════════════════════
# 원점 탐지
# ═══════════════════════════════════════════════════════════════

def find_origin_candidates(doc, entities: List[EntityInfo],
                           plot: bool = True) -> Dict[str, Tuple[float, float]]:
    """DXF 헤더 + 엔티티 기반으로 원점 후보를 반환합니다."""
    def _hdr_pt(name):
        v = doc.header.get(name, None)
        if v is None:
            return None
        return (float(v[0]), float(v[1]))

    cands: Dict[str, Tuple[float, float]] = {}
    for nm in ('$INSBASE', '$EXTMIN', '$EXTMAX', '$LIMMIN', '$LIMMAX'):
        pt = _hdr_pt(nm)
        if pt:
            cands[nm] = pt
    cands['(0,0)'] = (0.0, 0.0)

    circ_centers = [ei.center for ei in entities if ei.etype == 'CIRCLE' and ei.center]
    if circ_centers:
        cands['CIRCLE_mean'] = (
            float(np.mean([c[0] for c in circ_centers])),
            float(np.mean([c[1] for c in circ_centers]))
        )

    if plot:
        fig, ax = plt.subplots(figsize=(6, 6))
        for ei in entities[:500]:
            xs, ys = zip(*ei.points) if ei.points else ([], [])
            ax.plot(xs, ys, 'k-', lw=0.3)
        markers = 'os^vD<>ph*'
        for i, (name, (cx, cy)) in enumerate(cands.items()):
            ax.scatter(cx, cy, marker=markers[i % len(markers)], s=120, label=name)
        ax.legend(fontsize=7)
        ax.set_aspect('equal')
        ax.set_title('Origin candidates')
        plt.show()
    return cands


# ═══════════════════════════════════════════════════════════════
# 동심원 반경 탐지
# ═══════════════════════════════════════════════════════════════

def _group_radii(radii: list, tol: float) -> List[float]:
    """정렬된 radii를 tol 이내 그룹으로 묶어 대표값(평균) 반환."""
    if not radii:
        return []
    arr = np.array(radii)
    arr = arr[arr > 1e-3]
    arr = np.sort(arr)
    if len(arr) == 0:
        return []

    groups = []
    current = [arr[0]]
    for r in arr[1:]:
        if r - current[-1] < tol:
            current.append(r)
        else:
            groups.append(np.mean(current))
            current = [r]
    groups.append(np.mean(current))
    return list(groups)


def find_concentric_radii(entities: List[EntityInfo],
                          origin: Tuple[float, float] = (0.0, 0.0),
                          tol: float = 0.125,
                          center_tol: float = 0.5) -> List[float]:
    """원점 기준 동심원(ARC/CIRCLE) 및 LINE 끝점 반경 대표값 목록을 반환합니다.

    2단계 탐지:
      1차 — center-based: center≈origin 인 ARC/CIRCLE 반경 (정확)
      2차 — density-based: LINE 끝점 반경 중 히트 수가 많은 피크만 보완
    """
    ox, oy = origin

    # ── 1차: center-based ──
    center_radii = []
    for ei in entities:
        if ei.center and ei.radius:
            dist_center = math.hypot(ei.center[0] - ox, ei.center[1] - oy)
            if dist_center < center_tol:
                center_radii.append(ei.radius)

    # ── 2차: endpoint-based ──
    endpoint_radii = []
    for ei in entities:
        for x, y in ei.points:
            endpoint_radii.append(math.hypot(x - ox, y - oy))

    primary = _group_radii(center_radii, tol) if center_radii else []

    if endpoint_radii:
        ep_arr = np.array(endpoint_radii)
        ep_arr = ep_arr[ep_arr > 1e-3]
        if len(ep_arr) > 0:
            r_min, r_max = ep_arr.min(), ep_arr.max()
            n_bins = max(int((r_max - r_min) / tol), 10)
            counts, bin_edges = np.histogram(ep_arr, bins=n_bins)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            threshold = max(np.median(counts) * 2, len(ep_arr) * 0.005)
            for i, cnt in enumerate(counts):
                if cnt >= threshold:
                    r_peak = bin_centers[i]
                    if not any(abs(r_peak - pr) < tol for pr in primary):
                        primary.append(r_peak)

    primary.sort()
    result = _group_radii(primary, tol)
    return [round(r, 3) for r in result]


# ═══════════════════════════════════════════════════════════════
# 닫힌 영역 분석
# ═══════════════════════════════════════════════════════════════

def find_closed_regions(entities: List[EntityInfo],
                        origin: Tuple[float, float] = (0.0, 0.0)) -> Dict:
    """닫힌 LWPOLYLINE/POLYLINE/CIRCLE을 분석하여 자석/로터 영역 식별."""
    ox, oy = origin

    closed_polys = [ei for ei in entities
                    if ei.is_closed and ei.etype in ('LWPOLYLINE', 'POLYLINE', 'SPLINE')]
    circles = [ei for ei in entities if ei.etype == 'CIRCLE']

    result = {
        'closed_polys': closed_polys,
        'circles': circles,
        'by_radius_zone': defaultdict(list),
        'potential_magnets': [],
    }

    if not closed_polys:
        return result

    poly_info = []
    for ei in closed_polys:
        radii = [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]
        r_min, r_max = min(radii), max(radii)
        r_avg = np.mean(radii)
        area = ei.get_area(origin)
        poly_info.append({
            'entity': ei,
            'r_min': r_min, 'r_max': r_max, 'r_avg': r_avg,
            'area': area, 'radial_span': r_max - r_min
        })

    poly_info.sort(key=lambda x: x['r_avg'])

    r_min_all = min(p['r_min'] for p in poly_info) if poly_info else 0
    r_max_all = max(p['r_max'] for p in poly_info) if poly_info else 100

    for pi in poly_info:
        r_avg = pi['r_avg']
        radial_span = pi['radial_span']
        if 0.3 * r_max_all < r_avg < 0.7 * r_max_all:
            if radial_span < 0.2 * r_max_all:
                result['potential_magnets'].append(pi)

    return result


def analyze_closed_regions_for_motor_type(entities: List[EntityInfo],
                                          origin: Tuple[float, float] = (0.0, 0.0),
                                          concentric_radii: List[float] = None) -> Dict:
    """닫힌 영역으로 모터 타입 판별."""
    regions = find_closed_regions(entities, origin)

    result = {
        'has_closed_magnets': False,
        'magnet_zone': None,
        'num_closed_polys': len(regions['closed_polys']),
        'num_circles': len(regions['circles']),
        'closed_region_analysis': regions
    }

    if not regions['potential_magnets']:
        return result

    result['has_closed_magnets'] = True
    magnet_r_avg = np.mean([m['r_avg'] for m in regions['potential_magnets']])

    if concentric_radii and len(concentric_radii) >= 2:
        gaps = [(concentric_radii[i+1] - concentric_radii[i], i)
                for i in range(len(concentric_radii)-1)]
        min_gap, airgap_idx = min(gaps, key=lambda x: x[0])
        airgap_r = (concentric_radii[airgap_idx] + concentric_radii[airgap_idx+1]) / 2

        result['magnet_zone'] = 'inner' if magnet_r_avg < airgap_r else 'outer'
    else:
        all_radii = []
        for ei in entities:
            for p in ei.points:
                all_radii.append(np.hypot(p[0] - origin[0], p[1] - origin[1]))
        r_mid = np.median(all_radii) if all_radii else 50
        result['magnet_zone'] = 'inner' if magnet_r_avg < r_mid else 'outer'

    return result


# ═══════════════════════════════════════════════════════════════
# Inner/Outer Rotor 판별
# ═══════════════════════════════════════════════════════════════

def classify_inner_outer_rotor(entities: List[EntityInfo],
                               origin: Tuple[float, float] = (0.0, 0.0),
                               concentric_radii: List[float] = None) -> str:
    """
    내전형(inner_rotor)/외전형(outer_rotor) 판별.

    판별 로직:
    1. 닫힌 폴리라인(자석 영역) 분석
    2. 방사형 LINE 분석 (슬롯 벽면 방향)
    3. 동심원 갭 분석 (Fallback)
    """
    ox, oy = origin

    # 방법 1: 닫힌 폴리라인 분석
    closed_analysis = analyze_closed_regions_for_motor_type(entities, origin, concentric_radii)

    if closed_analysis['has_closed_magnets']:
        n_mag = len(closed_analysis['closed_region_analysis']['potential_magnets'])
        print(f"[classify] 닫힌 영역으로 자석 감지됨: {n_mag}개")
        if closed_analysis['magnet_zone'] == 'inner':
            print("[classify] → 자석이 안쪽 → inner_rotor")
            return 'inner_rotor'
        else:
            print("[classify] → 자석이 바깥쪽 → outer_rotor")
            return 'outer_rotor'

    # 방법 2: 방사형 LINE 분석
    radial_lines = []
    for ei in entities:
        if ei.etype != 'LINE':
            continue
        p1, p2 = ei.points[0], ei.points[1]
        r1 = np.hypot(p1[0] - ox, p1[1] - oy)
        r2 = np.hypot(p2[0] - ox, p2[1] - oy)
        span = abs(r2 - r1)
        length = np.hypot(p2[0] - p1[0], p2[1] - p1[1])

        if span > 1.0 and span > 0.8 * length:
            radial_lines.append({'r_inner': min(r1, r2), 'r_outer': max(r1, r2)})

    if len(radial_lines) >= 4:
        inner_avg = np.mean([rl['r_inner'] for rl in radial_lines])
        outer_avg = np.mean([rl['r_outer'] for rl in radial_lines])
        slot_center = (inner_avg + outer_avg) / 2

        all_radii = [np.hypot(p[0] - ox, p[1] - oy) for ei in entities for p in ei.points]
        r_min_all, r_max_all = min(all_radii), max(all_radii)
        r_mid = (r_min_all + r_max_all) / 2

        print(f"[classify] radial LINE count: {len(radial_lines)}")
        print(f"[classify] slot walls: inner_avg={inner_avg:.1f}, "
              f"outer_avg={outer_avg:.1f}, slot_center={slot_center:.1f}")
        print(f"[classify] model radius range: [{r_min_all:.1f}, {r_max_all:.1f}], mid={r_mid:.1f}")

        if slot_center > r_mid:
            print("[classify] → slot center OUTER → inner_rotor")
            return 'inner_rotor'
        else:
            print("[classify] → slot center INNER → outer_rotor")
            return 'outer_rotor'

    # 방법 3: 동심원 갭 분석
    if concentric_radii is None:
        concentric_radii = find_concentric_radii(entities, origin)

    if len(concentric_radii) < 2:
        print("[classify] 동심원 부족, 기본값 inner_rotor 반환")
        return 'inner_rotor'

    gaps = [(concentric_radii[i+1] - concentric_radii[i], i)
            for i in range(len(concentric_radii) - 1)]
    min_gap, airgap_idx = min(gaps, key=lambda x: x[0])
    airgap_r = concentric_radii[airgap_idx]

    inner_ents = sum(1 for ei in entities if ei.r_max < airgap_r)
    outer_ents = sum(1 for ei in entities if ei.r_min > airgap_r)

    print(f"[classify] Gap analysis: airgap at r={airgap_r:.1f}")
    print(f"[classify] inner entities: {inner_ents}, outer entities: {outer_ents}")

    return 'inner_rotor' if outer_ents > inner_ents else 'outer_rotor'


# ═══════════════════════════════════════════════════════════════
# 에어갭 반경 추정
# ═══════════════════════════════════════════════════════════════

def find_airgap_radius(entities: List[EntityInfo],
                       origin: Tuple[float, float] = (0.0, 0.0),
                       concentric_radii: List[float] = None) -> Tuple[float, float]:
    """동심원 간격 기반 에어갭 반경(내측, 외측) 추정."""
    if concentric_radii is None:
        concentric_radii = find_concentric_radii(entities, origin)

    if len(concentric_radii) < 2:
        all_radii = []
        ox, oy = origin
        for ei in entities:
            for p in ei.points:
                all_radii.append(np.hypot(p[0] - ox, p[1] - oy))
        if not all_radii:
            return (0.0, 0.0)
        r_mid = np.median(all_radii)
        return (r_mid * 0.95, r_mid * 1.05)

    gaps = [(concentric_radii[i+1] - concentric_radii[i], i)
            for i in range(len(concentric_radii) - 1)]
    valid_gaps = [(g, i) for g, i in gaps if g > 0.1]

    if not valid_gaps:
        r_mid = np.median(concentric_radii)
        return (r_mid * 0.95, r_mid * 1.05)

    min_gap, airgap_idx = min(valid_gaps, key=lambda x: x[0])
    return (concentric_radii[airgap_idx], concentric_radii[airgap_idx + 1])


def find_airgap_by_arc_span(entities: List[EntityInfo],
                            origin: Tuple[float, float] = (0.0, 0.0),
                            center_tol: float = 0.5,
                            r_tol: float = 0.125,
                            verbose: bool = True) -> Dict:
    """
    ARC angular span 기반으로 에어갭을 추정합니다.

    알고리즘
    --------
    1. center≈origin인 동심 ARC를 반경별로 그룹핑
    2. 같은 반경 그룹 내 ARC들의 총 angular span 계산
    3. 1주기(=360°/반복수) 대비 span coverage 계산
       → 코어 경계는 span≈100% (거의 채움)
    4. 두 core 경계 사이 최소 gap = airgap
    """
    ox, oy = origin

    # ── 1) 동심 ARC 수집 & 반경별 그룹핑 ──
    concentric_arcs = []
    for ei in entities:
        if ei.etype == 'ARC' and ei.center and ei.radius:
            dist_c = math.hypot(ei.center[0] - ox, ei.center[1] - oy)
            if dist_c < center_tol:
                sa = ei.start_angle if ei.start_angle is not None else 0
                ea = ei.end_angle if ei.end_angle is not None else 360
                span = (ea - sa) % 360
                if span < 1e-6:
                    span = 360.0
                concentric_arcs.append({
                    'entity': ei, 'radius': ei.radius,
                    'start_angle': sa, 'end_angle': ea, 'span_deg': span,
                })

    if not concentric_arcs:
        if verbose:
            print("[arc_span] 동심 ARC 없음 → 에어갭 추정 실패")
        return {'airgap_r_inner': 0.0, 'airgap_r_outer': 0.0,
                'airgap_length': 0.0, 'radii_info': [], 'core_candidates': [],
                'method': 'arc_span'}

    concentric_arcs.sort(key=lambda x: x['radius'])
    radius_groups = []
    current_group = [concentric_arcs[0]]
    for arc in concentric_arcs[1:]:
        if arc['radius'] - current_group[-1]['radius'] < r_tol:
            current_group.append(arc)
        else:
            rep_r = np.mean([a['radius'] for a in current_group])
            radius_groups.append((rep_r, current_group))
            current_group = [arc]
    rep_r = np.mean([a['radius'] for a in current_group])
    radius_groups.append((rep_r, current_group))

    # ── 2) 반복 주기 추정 ──
    max_count_group = max(radius_groups, key=lambda g: len(g[1]))
    n_repeat_est = len(max_count_group[1])
    period_deg = 360.0 / max(n_repeat_est, 1)

    if verbose:
        print(f"[arc_span] 동심 ARC 총 {len(concentric_arcs)}개, "
              f"반경 그룹 {len(radius_groups)}개")
        print(f"[arc_span] 추정 반복 수: {n_repeat_est}, 주기: {period_deg:.2f}°")

    # ── 3) span coverage 계산 ──
    radii_info = []
    for rep_r, arcs in radius_groups:
        n_arcs = len(arcs)
        total_span = sum(a['span_deg'] for a in arcs)
        coverage_360 = min(total_span / 360.0, 1.0)
        avg_span = total_span / n_arcs if n_arcs > 0 else 0
        coverage_period = min(avg_span / period_deg, 1.0) if period_deg > 0 else 0

        radii_info.append({
            'radius': round(rep_r, 3), 'n_arcs': n_arcs,
            'total_span_deg': round(total_span, 2),
            'avg_span_deg': round(avg_span, 2),
            'coverage_360': round(coverage_360, 4),
            'coverage_period': round(coverage_period, 4),
        })

    # ── 4) 코어 경계 후보 식별 ──
    COVERAGE_THRESH = 0.80
    core_candidates = []
    for ri in radii_info:
        is_core_boundary = False
        reason = ''

        if (ri['coverage_period'] >= COVERAGE_THRESH and
                abs(ri['n_arcs'] - n_repeat_est) <= max(2, n_repeat_est * 0.3)):
            is_core_boundary = True
            reason = f"period_cov={ri['coverage_period']:.2f}, n_arcs={ri['n_arcs']}"

        if ri['coverage_360'] >= COVERAGE_THRESH:
            is_core_boundary = True
            reason = f"full_cov={ri['coverage_360']:.2f}"

        if is_core_boundary:
            core_candidates.append({**ri, 'reason': reason})

    if verbose:
        print(f"\n[arc_span] 코어 경계 후보 ({len(core_candidates)}개):")
        for cc in core_candidates:
            print(f"  r={cc['radius']:.3f}  n_arcs={cc['n_arcs']}  "
                  f"avg_span={cc['avg_span_deg']:.1f}°  "
                  f"cov_period={cc['coverage_period']:.2f}  "
                  f"cov_360={cc['coverage_360']:.2f}  "
                  f"({cc['reason']})")

    # ── 5) 에어갭 쌍 추출 ──
    if len(core_candidates) < 2:
        if verbose:
            print("[arc_span] 코어 후보 2개 미만 → fallback")
        inner, outer = find_airgap_radius(entities, origin)
        return {'airgap_r_inner': inner, 'airgap_r_outer': outer,
                'airgap_length': outer - inner,
                'radii_info': radii_info, 'core_candidates': core_candidates,
                'method': 'arc_span_fallback'}

    candidate_radii = sorted(set(cc['radius'] for cc in core_candidates))
    gaps = []
    for i in range(len(candidate_radii) - 1):
        gap = candidate_radii[i + 1] - candidate_radii[i]
        gaps.append((gap, candidate_radii[i], candidate_radii[i + 1]))

    valid_gaps = [(g, r_in, r_out) for g, r_in, r_out in gaps if g > r_tol]
    if not valid_gaps:
        valid_gaps = gaps

    airgap_gap, airgap_r_inner, airgap_r_outer = min(valid_gaps, key=lambda x: x[0])

    if verbose:
        print(f"\n[arc_span] ★ 에어갭 추정:")
        print(f"  내측 반경: {airgap_r_inner:.3f} mm")
        print(f"  외측 반경: {airgap_r_outer:.3f} mm")
        print(f"  에어갭 길이: {airgap_gap:.3f} mm")

    return {
        'airgap_r_inner': airgap_r_inner,
        'airgap_r_outer': airgap_r_outer,
        'airgap_length': airgap_gap,
        'radii_info': radii_info,
        'core_candidates': core_candidates,
        'method': 'arc_span',
        'n_repeat_est': n_repeat_est,
        'period_deg': period_deg,
    }


# ═══════════════════════════════════════════════════════════════
# Stator / Rotor 분리
# ═══════════════════════════════════════════════════════════════

def split_by_layer(entities: List[EntityInfo],
                   stator_layers: List[str] = None,
                   rotor_layers: List[str] = None) -> Dict:
    """레이어 이름 기반으로 스테이터/로터를 분리합니다."""
    layer_counts = Counter(ei.layer for ei in entities)
    all_layers = list(layer_counts.keys())

    stator_keywords = ['stator', 'stat', 'armature', 'st_', '고정자']
    rotor_keywords = ['rotor', 'rot', 'field', 'rt_', 'magnet', '회전자']

    if stator_layers is None:
        stator_layers = [l for l in all_layers
                         if any(kw in l.lower() for kw in stator_keywords)]
    if rotor_layers is None:
        rotor_layers = [l for l in all_layers
                        if any(kw in l.lower() for kw in rotor_keywords)]

    stator_entities = [ei for ei in entities if ei.layer in stator_layers]
    rotor_entities = [ei for ei in entities if ei.layer in rotor_layers]
    unknown_entities = [ei for ei in entities
                        if ei.layer not in stator_layers and ei.layer not in rotor_layers]

    return {
        'stator': stator_entities,
        'rotor': rotor_entities,
        'unknown': unknown_entities,
        'stator_layers': stator_layers,
        'rotor_layers': rotor_layers,
        'has_layer_info': len(stator_layers) > 0 or len(rotor_layers) > 0
    }


def split_stator_rotor_by_arc_span(
    entities: List[EntityInfo],
    origin: Tuple[float, float] = (0.0, 0.0),
    motor_type: str = 'inner_rotor',
    center_tol: float = 0.5,
    r_tol: float = 0.125,
    verbose: bool = True,
) -> Dict:
    """
    arc_span 에어갭 감지 + midpoint 경계 기반 Stator/Rotor 분리.

    Returns
    -------
    dict with stator, rotor, gap_entities, airgap_r_inner/outer/mid, ...
    """
    ag = find_airgap_by_arc_span(
        entities, origin,
        center_tol=center_tol, r_tol=r_tol, verbose=verbose,
    )
    r_inner = ag['airgap_r_inner']
    r_outer = ag['airgap_r_outer']
    mid = (r_inner + r_outer) / 2.0

    inner_ents: List[EntityInfo] = []
    outer_ents: List[EntityInfo] = []
    gap_ents: List[EntityInfo] = []

    for ei in entities:
        if ei.r_max <= mid:
            inner_ents.append(ei)
        elif ei.r_min > mid:
            outer_ents.append(ei)
        else:
            gap_ents.append(ei)

    if motor_type == 'inner_rotor':
        stator, rotor = outer_ents, inner_ents
    else:
        stator, rotor = inner_ents, outer_ents

    if verbose:
        print(f"\n[split_stator_rotor_by_arc_span]")
        print(f"  에어갭: {r_inner:.3f} ~ {r_outer:.3f} mm  (mid={mid:.3f})")
        print(f"  모터 타입: {motor_type}")
        print(f"  스테이터: {len(stator)} entities")
        print(f"  로터:     {len(rotor)} entities")
        if gap_ents:
            print(f"  에어갭 걸침: {len(gap_ents)} entities (미분류)")

    return {
        'stator': stator, 'rotor': rotor, 'gap_entities': gap_ents,
        'airgap_r_inner': r_inner, 'airgap_r_outer': r_outer,
        'airgap_r_mid': mid, 'airgap_length': r_outer - r_inner,
        'motor_type': motor_type, 'method': 'arc_span',
    }


def split_by_radius(entities: List[EntityInfo],
                    origin: Tuple[float, float] = (0.0, 0.0),
                    airgap_r_inner: float = None,
                    airgap_r_outer: float = None,
                    motor_type: str = 'inner_rotor') -> Dict:
    """반경 기준으로 스테이터/로터를 분리합니다."""
    ox, oy = origin

    if airgap_r_inner is None or airgap_r_outer is None:
        airgap_r_inner, airgap_r_outer = find_airgap_radius(entities, origin)

    airgap_mid = (airgap_r_inner + airgap_r_outer) / 2

    inner_entities, outer_entities = [], []
    for ei in entities:
        radii = [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]
        r_min, r_max = min(radii), max(radii)

        if r_max < airgap_r_inner:
            inner_entities.append(ei)
        elif r_min > airgap_r_outer:
            outer_entities.append(ei)
        else:
            r_avg = np.mean(radii)
            if r_avg < airgap_mid:
                inner_entities.append(ei)
            else:
                outer_entities.append(ei)

    if motor_type == 'inner_rotor':
        return {'stator': outer_entities, 'rotor': inner_entities,
                'airgap_r_inner': airgap_r_inner, 'airgap_r_outer': airgap_r_outer,
                'motor_type': motor_type}
    else:
        return {'stator': inner_entities, 'rotor': outer_entities,
                'airgap_r_inner': airgap_r_inner, 'airgap_r_outer': airgap_r_outer,
                'motor_type': motor_type}


def split_stator_rotor(entities: List[EntityInfo],
                       origin: Tuple[float, float] = (0.0, 0.0),
                       method: str = 'auto',
                       motor_type: str = None,
                       stator_layers: List[str] = None,
                       rotor_layers: List[str] = None,
                       verbose: bool = True) -> Dict:
    """단일 DXF에서 스테이터/로터 엔티티를 분리합니다 (auto: layer → radius fallback)."""
    if verbose:
        print("=" * 70)
        print("Stator/Rotor Split")
        print("=" * 70)
        print(f"총 엔티티 수: {len(entities)}")

    layer_result = split_by_layer(entities, stator_layers, rotor_layers)

    if verbose:
        print(f"\n[레이어 분석]  스테이터: {layer_result['stator_layers']}, "
              f"로터: {layer_result['rotor_layers']}, "
              f"info={layer_result['has_layer_info']}")

    if method == 'auto':
        if (layer_result['has_layer_info']
                and len(layer_result['stator']) > 0
                and len(layer_result['rotor']) > 0):
            method = 'layer'
        else:
            method = 'radius'

    if verbose:
        print(f"[분리 방법]: {method}")

    if motor_type is None:
        concentric = find_concentric_radii(entities, origin)
        motor_type = classify_inner_outer_rotor(entities, origin, concentric)

    if verbose:
        print(f"[모터 타입]: {motor_type}")

    if method == 'layer':
        result = {
            'stator': layer_result['stator'],
            'rotor': layer_result['rotor'],
            'motor_type': motor_type,
            'method_used': 'layer',
            'stator_layers': layer_result['stator_layers'],
            'rotor_layers': layer_result['rotor_layers'],
        }
        all_ents = layer_result['stator'] + layer_result['rotor']
        if all_ents:
            result['airgap_r_inner'], result['airgap_r_outer'] = find_airgap_radius(
                all_ents, origin)
        else:
            result['airgap_r_inner'] = result['airgap_r_outer'] = 0.0
    else:
        radius_result = split_by_radius(entities, origin, motor_type=motor_type)
        result = {
            'stator': radius_result['stator'],
            'rotor': radius_result['rotor'],
            'motor_type': motor_type,
            'method_used': 'radius',
            'airgap_r_inner': radius_result['airgap_r_inner'],
            'airgap_r_outer': radius_result['airgap_r_outer'],
        }

    if verbose:
        print(f"\n[분리 결과]  스테이터: {len(result['stator'])}개, "
              f"로터: {len(result['rotor'])}개, "
              f"에어갭: {result['airgap_r_inner']:.2f}~{result['airgap_r_outer']:.2f} mm")

    return result
