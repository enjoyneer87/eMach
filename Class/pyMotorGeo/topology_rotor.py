"""
pyMotorGeo.topology_rotor
=========================

회전자(Rotor) 특화 토폴로지 분석 및 영역 분류 모듈입니다.

반극(Half-pole) 또는 1극 단위로 추출된 회전자 엔티티들을 분석하여 
자석(Magnet), 공기 배리어(Air Barrier), 회전자 철심(Rotor Core), 
축(Shaft) 등 주요 구조 영역으로 자동 분류합니다.

특히 IPM 모터의 경우 자석 개수, 배리어 배치, 플럭스 방향 등을 정확히 추출하여 
설계 분석에 활용됩니다.

주요 기능
---------
- classify_rotor_entities            : 한 극 영역 엔티티의 자동 분류 및 토폴로지 판별
- reassign_rotor_region              : GUI 기반 영역 재지정 (사용자 수정 지원)
- get_rotor_region_summary           : 분류 결과 통계 및 요약
- classify_rotor_entities_with_closing_compare : 폐곡선 비교 기반 정교한 분류
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
    """한 극 영역의 회전자 엔티티들을 기하학적 특성에 따라 자동 분류하고 토폴로지를 판별합니다.

    회전자는 자석(Magnet), 공기 배리어(Air Barrier), 철심(Rotor Core), 축(Shaft)으로 구성됩니다:
    - **자석(Magnet)**: 회전 토크의 주요 원천 (영구 자석)
    - **공기 배리어(Air Barrier)**: IPM/SynRM에서 릭턴스(열린 형태 플럭스)를 조정하는 빈 공간
    - **철심(Rotor Core)**: 자기 경로의 주요 부분 (강자성 재료)
    - **축(Shaft)**: 회전 중심축

    이 함수는 다음을 수행합니다:
    1. 엔티티를 반경 위치에 따라 자석/배리어/코어로 초분류.
    2. 자석 엔티티들을 각도로 클러스터링하여 논리 자석 개수 산출.
    3. 반경 프로파일과 배리어 유무를 종합 판별 → SPM/IPM/SynRM/PMa-SynRM 결정.

    Args:
        pole_entities (List[Dict]): 한 극의 엔티티들. 
                                   [{​'entity': EntityInfo, 'original_angle': float, ...}, ...] 형태.
        origin (Tuple[float, float]): 회전 중심축 (반경 및 각도 계산 원점). 기본값 (0.0, 0.0).
        airgap_r (float, optional): 공극 반경 (회전자 외경). 
                                   미제공 시 엔티티 반경 최댓값 추정.
        pole_pitch_deg (float, optional): 극 피치(도). 자석 클러스터 간격 자동 설정에 사용.
        r_shaft (float, optional): 축 반경. 미제공 시 엔티티 반경 최솟값 추정.
        verbose (bool): 분류 과정 및 상세 정보 로깅 활성화. 기본값 False.

    Returns:
        Dict: 분류 및 토폴로지 판별 결과:
            - 'topology' (str): 판별된 토폴로지 ('SPM', 'IPM', 'SynRM', 'PMa-SynRM', 'UNKNOWN').
            - 'regions' (List[Dict]): 분류된 영역들 (각각 'entity', 'region_type', 'r_min', 'r_max' 등 포함).
            - 'magnet' (List[EntityInfo]): 자석으로 분류된 엔티티들.
            - 'air_barrier' (List[EntityInfo]): 공기 배리어로 식별된 엔티티들.
            - 'rotor_core' (List[EntityInfo]): 철심으로 분류된 엔티티들.
            - 'shaft' (List[EntityInfo]): 축으로 분류된 엔티티들.
            - 'n_magnets' (int): 자석 클러스터의 논리적 개수 (각도 기반).
            - 'n_magnet_entities' (int): 자석으로 분류된 개별 엔티티 수.
            - 'n_barriers' (int): 공기 배리어의 개수.
            - 'n_regions' (int): 분류된 영역의 총 개수.
            - 'magnet_area' (float): 자석의 총 면적.
            - 'barrier_area' (float): 공기 배리어의 총 면적.
            - 'detail' (str): 토폴로지 판별 근거 상세 설명.
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
        # 열린 ARC — 내부 (concentric_arcs 포함): 반경 구간으로 air_barrier 판별
        # IPM/SynRM에서 동심원 호는 배리어 경계선 → air_barrier
        elif is_arc and not is_near_surface and not is_closed:
            # 반경이 shaft~surface 사이의 내부 구간이면 air_barrier 후보
            r_frac = r_avg / airgap_r if airgap_r else 0
            if 0.35 < r_frac < 0.90:
                tag = 'air_barrier'
            else:
                tag = 'rotor_core'
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
    Reassign the rotor region label for a specific entity in the regions list.
    
    This function supports interactive GUI correction where users can manually override 
    the automated rotor classification when the algorithm misclassifies magnet, air barrier, 
    or rotor core regions. The function updates the region type in-place and returns the 
    modified list.

    Parameters
    ----------
    regions : List[Dict]
        Region classification results from `classify_rotor_entities()`. Each dict contains
        keys: 'index' (entity index), 'region' (classification label), 'radii' (min_r, max_r),
        'angles' (min_angle, max_angle), 'area', 'perimeter', 'color', etc.
    entity_index : int
        Zero-based index of the entity to relabel within the regions list.
        Must be in range [0, len(regions)).
    new_region : str
        New rotor region classification. Valid values include:
        - 'magnet': Permanent magnet material (NdFeB, ferrite, etc.)
        - 'air_barrier': Air-filled slot or pocket (flux barrier in IPM rotor)
        - 'rotor_core': Rotor steel core (laminated electrical steel)
        - 'shaft': Central rotor shaft
        Other custom labels are technically allowed but should follow the classification schema.

    Returns
    -------
    List[Dict]
        The same `regions` list with the specified entity's 'region' field updated to 
        `new_region`. The modification is in-place and the reference to the same list 
        object is returned. If `entity_index` is out of bounds, the list is returned 
        unchanged.

    Examples
    --------
    >>> result = classify_rotor_entities(roi_rotor)
    >>> regions = result['regions']
    >>> # User corrects misclassified magnet to air barrier in GUI
    >>> regions = reassign_rotor_region(regions, entity_index=3, new_region='air_barrier')
    >>> print(regions[3]['region'])  # Output: 'air_barrier'
    
    >>> # Perform multiple corrections
    >>> regions = reassign_rotor_region(regions, entity_index=1, new_region='magnet')
    >>> regions = reassign_rotor_region(regions, entity_index=5, new_region='rotor_core')
    
    Notes
    -----
    This function is primarily used in GUI workflows where users need to:
    1. Review automatically classified rotor regions
    2. Correct misclassified entities (e.g., algorithm incorrectly labeled a magnet as core)
    3. Handle edge cases near rotor boundaries or overlapping regions
    4. Fine-tune classification before proceeding to detailed analysis
    
    The function does not validate whether `new_region` is a standard label; it accepts 
    any string value. Users should ensure consistency with the motor's actual rotor 
    topology (SPM, IPM, SynRM, etc.).
    """
    if 0 <= entity_index < len(regions):
        regions[entity_index]['region'] = new_region
    return regions


def get_rotor_region_summary(regions: List[Dict]) -> Dict:
    """
    Aggregate and count rotor regions by classification type.
    
    This function provides a high-level overview of the rotor topology by tallying 
    the number of entities in each classification category (magnet, air barrier, rotor core, etc.). 
    It is commonly used for visualization, validation, and statistical analysis of the 
    rotor structure.

    Parameters
    ----------
    regions : List[Dict]
        Region classification results from `classify_rotor_entities()`. Each dict contains
        at minimum a 'region' field with the classification label.

    Returns
    -------
    Dict
        A dictionary mapping region labels (e.g., 'magnet', 'air_barrier', 'rotor_core') 
        to their counts (int). Keys are the unique region labels found in the input list, 
        and values are the number of distinct entities with that label.

    Examples
    --------
    Example 1: IPM (Interior Permanent Magnet) Rotor
    
    >>> result = classify_rotor_entities(roi_rotor)
    >>> regions = result['regions']
    >>> summary = get_rotor_region_summary(regions)
    >>> print(summary)
    {'magnet': 4, 'air_barrier': 4, 'rotor_core': 1}
    # Interpretation: 4 magnets arranged with 4 flux barriers, embedded in rotor core
    
    Example 2: SPM (Surface Permanent Magnet) Rotor
    
    >>> summary = get_rotor_region_summary(regions)
    >>> print(summary)
    {'magnet': 16, 'rotor_core': 1}
    # Interpretation: 16 surface magnets arranged on the rotor core (no air barriers)
    
    Example 3: SynRM (Synchronous Reluctance Motor) Rotor
    
    >>> summary = get_rotor_region_summary(regions)
    >>> print(summary)
    {'air_barrier': 3, 'rotor_core': 1}
    # Interpretation: 3 flux barriers (no permanent magnets) for reluctance torque
    
    Notes
    -----
    - The function uses Python's `collections.Counter` for efficient counting
    - Empty regions list returns an empty dictionary {}
    - The summary is useful for:
      * Validating motor rotor topology (e.g., checking expected magnet count for a 4-pole motor)
      * Generating rotor composition statistics for reporting
      * Debugging region classification if unexpected counts appear
      * GUI display of rotor structure overview
    - The count represents the number of topologically distinct entities, not actual 
      physical count (e.g., 4 magnet entities in summary may represent 16 physical magnets
      if the input uses half-pole or quarter-pole minimum repeating units)
    """
    from collections import Counter
    cnt = Counter(r['region'] for r in regions)
    return dict(cnt)
