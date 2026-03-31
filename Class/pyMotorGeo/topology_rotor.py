"""
pyMotorGeo.topology_rotor
=========================
로터 토폴로지 분석: SPM / IPM / SynRM / PMa-SynRM 판별.

엔티티 분류 → 각도 클러스터링 → 논리 자석/배리어 그룹 산출 → 토폴로지 결정.
영역별(region) 이름 할당 및 GUI 재지정 지원.
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional
from collections import defaultdict, Counter

from .core import EntityInfo
from .region_closing import create_radial_line, create_arc_boundary, detect_closed_faces


# ═══════════════════════════════════════════════════════════════
# 유틸리티
# ═══════════════════════════════════════════════════════════════

def _entity_radii(ei: EntityInfo,
                  origin: Tuple[float, float]) -> List[float]:
    """엔티티의 모든 점에 대한 반경 리스트."""
    ox, oy = origin
    return [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]


def _entity_avg_angle(ei: EntityInfo,
                      origin: Tuple[float, float]) -> float:
    """엔티티 대표 각도 (deg, 0–360)."""
    ox, oy = origin
    if not ei.points:
        return 0.0
    angles = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360
              for p in ei.points]
    return float(np.mean(angles))


def _cluster_by_angle(items: List[Dict],
                      origin: Tuple[float, float],
                      gap_deg: float = 5.0) -> List[List[Dict]]:
    """
    엔티티를 각도 기준으로 클러스터링합니다.
    인접 엔티티 사이 각도 차이가 gap_deg 이하이면 같은 그룹.
    """
    if not items:
        return []
    ox, oy = origin
    ang_list = []
    for item in items:
        ei = item['entity']
        ang_list.append(_entity_avg_angle(ei, origin))

    idx_sorted = np.argsort(ang_list)
    clusters: List[List[int]] = [[idx_sorted[0]]]
    for i in range(1, len(idx_sorted)):
        diff = ang_list[idx_sorted[i]] - ang_list[idx_sorted[i - 1]]
        if diff < gap_deg:
            clusters[-1].append(idx_sorted[i])
        else:
            clusters.append([idx_sorted[i]])
    return [[items[j] for j in c] for c in clusters]


# ═══════════════════════════════════════════════════════════════
# 핵심: 로터 영역 분류
# ═══════════════════════════════════════════════════════════════

# 로터 영역 이름 상수
ROTOR_REGION_NAMES = {
    'magnet':        'Magnet',
    'air_barrier':   'Air Barrier',
    'rotor_core':    'Rotor Core',
    'shaft':         'Shaft',
    'airgap_rotor':  'Airgap (rotor side)',
    'unknown':       'Unknown',
}

ROTOR_REGION_COLORS = {
    'magnet':        '#FF4444',
    'air_barrier':   '#C0C0C0',
    'rotor_core':    '#FF8C42',
    'shaft':         '#8B8B8B',
    'airgap_rotor':  '#E0E0E0',
    'unknown':       '#D0D0D0',
}


def classify_rotor_entities(
    pole_entities: List[Dict],
    origin: Tuple[float, float] = (0.0, 0.0),
    airgap_r: float = None,
    pole_pitch_deg: float = None,
    r_shaft: float = None,
    verbose: bool = False,
) -> Dict:
    """
    한 극 영역의 로터 엔티티들을 분류하여 토폴로지를 판별합니다.

    Parameters
    ----------
    pole_entities : List[Dict]
        [{'entity': EntityInfo, 'original_angle': float, 'relative_angle': float}, ...]
    origin : 원점
    airgap_r : 에어갭 반경 (inner rotor = 로터 외경 쪽)
    pole_pitch_deg : 극 피치 (클러스터 간격 자동 결정)
    r_shaft : 샤프트 반경 (None이면 자동 추정)
    verbose : 상세 출력

    Returns
    -------
    Dict : topology, regions (tagged entities), n_magnets, n_barriers, ...
    """
    ox, oy = origin

    _empty = {
        'topology': 'UNKNOWN',
        'regions': [],
        'magnets': [], 'air_barriers': [], 'core': [],
        'n_magnets': 0, 'n_magnet_entities': 0,
        'n_barriers': 0,
        'magnet_near_surface': False, 'magnet_embedded': False,
        'magnet_clusters': [],
        'detail': 'No entities',
    }
    if not pole_entities:
        return _empty

    # ── 반경 범위 파악 ──
    all_radii = []
    for item in pole_entities:
        all_radii.extend(_entity_radii(item['entity'], origin))
    if not all_radii:
        _empty['detail'] = 'No points'
        return _empty

    r_min_all = min(all_radii)
    r_max_all = max(all_radii)
    radial_range = r_max_all - r_min_all

    if airgap_r is None:
        airgap_r = r_max_all * 0.95
    if r_shaft is None:
        r_shaft = r_min_all * 1.05  # 최소 반경 ≈ 샤프트 근처

    # ── 임계치 ──
    surface_threshold = airgap_r * 0.90
    thin_threshold = radial_range * 0.15

    # ── 엔티티 분류 ──
    magnets = []
    air_barriers = []
    core = []
    regions = []  # [{entity, region_name, ...}, ...]

    for item in pole_entities:
        ei = item['entity']
        radii = _entity_radii(ei, origin)
        if not radii:
            tag = 'rotor_core'
            core.append(item)
            regions.append({**item, 'region': tag})
            continue

        r_min, r_max = min(radii), max(radii)
        r_avg = np.mean(radii)
        radial_span = r_max - r_min

        is_near_surface = r_avg > surface_threshold
        is_arc = ei.etype == 'ARC'
        is_line = ei.etype == 'LINE'
        is_closed = ei.is_closed
        is_thin = radial_span < thin_threshold

        # 샤프트 영역
        if r_max < r_shaft * 1.2 and is_closed:
            tag = 'shaft'
        # 닫힌 도형 — 표면 근처 → 자석, 내부 → 배리어
        elif is_closed and is_near_surface:
            tag = 'magnet'
        elif is_closed and not is_near_surface:
            tag = 'air_barrier'
        # 열린 ARC — 표면 + 얇은 → 자석
        elif is_arc and is_near_surface and is_thin:
            tag = 'magnet'
        # 표면 근처 LINE — 방사형이면 자석 측면 경계
        elif is_line and is_near_surface and is_thin:
            pts = ei.points
            if len(pts) >= 2:
                dr = abs(max(radii) - min(radii))
                seg_len = np.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
                if seg_len > 1e-6 and dr / seg_len > 0.6:
                    tag = 'magnet'
                else:
                    tag = 'rotor_core'
            else:
                tag = 'rotor_core'
        else:
            tag = 'rotor_core'

        # 등록
        if tag == 'magnet':
            magnets.append(item)
        elif tag == 'air_barrier':
            air_barriers.append(item)
        else:
            core.append(item)
        regions.append({**item, 'region': tag})

    # ── 각도 클러스터링 → 논리 자석 수 ──
    cluster_gap = (pole_pitch_deg / 4) if pole_pitch_deg else 8.0
    magnet_clusters = _cluster_by_angle(magnets, origin, gap_deg=cluster_gap)
    n_magnet_groups = len(magnet_clusters)
    n_magnet_entities = len(magnets)
    n_barriers = len(air_barriers)

    # ── 자석 위치 분석 ──
    magnet_near_surface = False
    magnet_embedded = False
    if magnets:
        mag_radii = []
        for item in magnets:
            mag_radii.extend(_entity_radii(item['entity'], origin))
        if np.mean(mag_radii) > airgap_r * 0.88:
            magnet_near_surface = True
        else:
            magnet_embedded = True

    # ── 최종 판별 ──
    if n_magnet_groups > 0 and n_barriers == 0 and magnet_near_surface:
        topology = 'SPM'
        detail = (f'Surface-mounted PM '
                  f'({n_magnet_groups} magnet{"s" if n_magnet_groups > 1 else ""}, '
                  f'{n_magnet_entities} ent)')
    elif n_magnet_groups > 0 and (n_barriers > 0 or magnet_embedded):
        if n_barriers > n_magnet_groups:
            topology = 'PMa-SynRM'
            detail = f'PM-assisted SynRM ({n_magnet_groups} magnets, {n_barriers} barriers)'
        else:
            topology = 'IPM'
            detail = f'Interior PM ({n_magnet_groups} magnets, {n_barriers} barriers)'
    elif n_magnet_groups == 0 and n_barriers > 0:
        topology = 'SynRM'
        detail = f'Synchronous Reluctance ({n_barriers} flux barriers)'
    elif n_magnet_groups == 0 and n_barriers == 0:
        topology = 'UNKNOWN'
        detail = 'No magnets or barriers detected'
    else:
        topology = 'OTHER'
        detail = f'{n_magnet_groups} magnets, {n_barriers} barriers'

    if verbose:
        print(f"[rotor_topology] {topology}: {detail}")
        print(f"  자석 그룹: {n_magnet_groups}, 자석 엔티티: {n_magnet_entities}")
        print(f"  배리어: {n_barriers}, 코어: {len(core)}")

    return {
        'topology': topology,
        'regions': regions,
        'magnets': magnets,
        'air_barriers': air_barriers,
        'core': core,
        'n_magnets': n_magnet_groups,
        'n_magnet_entities': n_magnet_entities,
        'n_barriers': n_barriers,
        'magnet_near_surface': magnet_near_surface,
        'magnet_embedded': magnet_embedded,
        'magnet_clusters': magnet_clusters,
        'detail': detail,
    }


def classify_rotor_entities_with_closing_compare(
    pole_entities: List[Dict],
    origin: Tuple[float, float] = (0.0, 0.0),
    airgap_r: float = None,
    pole_pitch_deg: float = None,
    r_shaft: float = None,
    min_area: float = 1.0,
    verbose: bool = False,
) -> Dict:
    """
    1) 기존 엔티티로 분류
    2) 한극 경계를 닫아 face 생성 후 재분류
    3) 두 결과를 상세 비교
    """
    raw = classify_rotor_entities(
        pole_entities,
        origin=origin,
        airgap_r=airgap_r,
        pole_pitch_deg=pole_pitch_deg,
        r_shaft=r_shaft,
        verbose=verbose,
    )

    if not pole_entities or airgap_r is None or pole_pitch_deg is None:
        return {
            'raw': raw,
            'closed': None,
            'comparison': {'note': 'insufficient inputs for closing'},
        }

    r_inner = r_shaft if (r_shaft is not None and r_shaft > 0) else 0.0
    boundaries = [
        create_radial_line(r_inner, airgap_r, 0.0, origin),
        create_radial_line(r_inner, airgap_r, float(pole_pitch_deg), origin),
        create_arc_boundary(airgap_r, 0.0, float(pole_pitch_deg), origin),
    ]
    if r_inner > 0:
        boundaries.append(
            create_arc_boundary(r_inner, 0.0, float(pole_pitch_deg), origin)
        )

    base_entities = [item['entity'] for item in pole_entities]
    closed_entities = list(base_entities) + boundaries
    faces = detect_closed_faces(closed_entities, origin, min_area=min_area)

    face_entities = []
    for fi in faces:
        verts = fi.get('vertices', [])
        if len(verts) < 3:
            continue
        face_entities.append(EntityInfo(
            etype='LWPOLYLINE',
            layer='_FACE_',
            points=verts,
            is_closed=True,
        ))

    closed_items = [
        {'entity': ei, 'original_angle': 0.0, 'relative_angle': 0.0}
        for ei in face_entities
    ]

    closed = classify_rotor_entities(
        closed_items,
        origin=origin,
        airgap_r=airgap_r,
        pole_pitch_deg=pole_pitch_deg,
        r_shaft=r_shaft,
        verbose=verbose,
    )

    raw_regions = Counter(r['region'] for r in raw.get('regions', []))
    closed_regions = Counter(r['region'] for r in closed.get('regions', []))
    all_keys = sorted(set(raw_regions) | set(closed_regions))
    region_diff = {
        k: {'raw': raw_regions.get(k, 0), 'closed': closed_regions.get(k, 0)}
        for k in all_keys
    }

    comparison = {
        'topology': {'raw': raw.get('topology'), 'closed': closed.get('topology')},
        'magnets': {'raw': raw.get('n_magnets'), 'closed': closed.get('n_magnets')},
        'barriers': {'raw': raw.get('n_barriers'), 'closed': closed.get('n_barriers')},
        'magnet_entities': {
            'raw': raw.get('n_magnet_entities'),
            'closed': closed.get('n_magnet_entities'),
        },
        'region_counts': region_diff,
        'face_count': len(faces),
    }

    return {
        'raw': raw,
        'closed': closed,
        'faces': faces,
        'comparison': comparison,
    }


# ═══════════════════════════════════════════════════════════════
# GUI 영역 재지정 지원
# ═══════════════════════════════════════════════════════════════

def reassign_rotor_region(regions: List[Dict],
                          entity_index: int,
                          new_region: str) -> List[Dict]:
    """
    regions 리스트에서 특정 엔티티의 영역 이름을 재지정합니다.

    Parameters
    ----------
    regions : classify_rotor_entities 결과의 'regions'
    entity_index : 변경할 엔티티 인덱스 (0-based)
    new_region : 새 영역 이름 (magnet, air_barrier, rotor_core, shaft, ...)

    Returns
    -------
    변경된 regions 리스트 (in-place)
    """
    if 0 <= entity_index < len(regions):
        regions[entity_index]['region'] = new_region
    return regions


def get_rotor_region_summary(regions: List[Dict]) -> Dict:
    """영역별 엔티티 수 요약."""
    from collections import Counter
    cnt = Counter(r['region'] for r in regions)
    return dict(cnt)
