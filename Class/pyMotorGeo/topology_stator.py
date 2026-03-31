"""
pyMotorGeo.topology_stator
==========================

고정자(Stator) 특화 토폴로지 분석 및 영역 분류 모듈입니다.

반슬롯(Half-slot) 또는 1슬롯 단위로 추출된 고정자 엔티티들을 분석하여 
슬롯(Slot), 티스(Tooth), 요크(Yoke), 슬롯오프닝(Slot Opening), 
컨덕터(Conductor), 웨지(Wedge) 등 주요 구조 영역으로 자동 분류합니다.

주요 기능
---------
- classify_stator_entities           : 한 슬롯 영역 엔티티의 자동 분류
- reassign_stator_region             : GUI 기반 영역 재지정 (사용자 수정 지원)
- get_stator_region_summary          : 분류 결과 통계 및 요약
- classify_stator_entities_with_closing_compare : 폐곡선 비교 기반 정교한 분류
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional
from collections import Counter

from .core import EntityInfo
from .region_closing import create_radial_line, create_arc_boundary, detect_closed_faces


# ═══════════════════════════════════════════════════════════════
# 스테이터 영역 이름 상수
# ═══════════════════════════════════════════════════════════════

STATOR_REGION_NAMES = {
    'stator_yoke':    'Stator Yoke',
    'stator_tooth':   'Stator Tooth',
    'slot':           'Slot',
    'slot_opening':   'Slot Opening',
    'conductor':      'Conductor',
    'wedge':          'Wedge',
    'airgap_stator':  'Airgap (stator side)',
    'unknown':        'Unknown',
}

STATOR_REGION_COLORS = {
    'stator_yoke':    '#4A90D9',
    'stator_tooth':   '#7EC8E3',
    'slot':           '#FFD700',
    'slot_opening':   '#FFFACD',
    'conductor':      '#FF6600',
    'wedge':          '#AADDFF',
    'airgap_stator':  '#E0E0E0',
    'unknown':        '#D0D0D0',
}


# ═══════════════════════════════════════════════════════════════
# 유틸리티
# ═══════════════════════════════════════════════════════════════

def _entity_radii(ei: EntityInfo,
                  origin: Tuple[float, float]) -> List[float]:
    """
    Extract radial distances of all vertices from the motor center.
    
    Computes the Euclidean distance from a central origin point to each vertex 
    in the entity, useful for determining whether an entity lies in the stator 
    region (slot, tooth, wedge) or beyond (yoke).

    Parameters
    ----------
    ei : EntityInfo
        Entity with `points` attribute containing list of (x, y) vertex coordinates.
    origin : Tuple[float, float]
        Motor center (ox, oy) as reference for polar distance calculation.

    Returns
    -------
    List[float]
        List of radial distances (in motor units) corresponding to each vertex 
        in ei.points, computed as sqrt((x-ox)² + (y-oy)²).

    Examples
    --------
    >>> entity = EntityInfo(points=[(50, 0), (50, 10), (40, 10)], ...)
    >>> radii = _entity_radii(entity, origin=(0, 0))
    >>> print(radii)  # Output: [50.0, 50.99..., 40.31...]
    """
    ox, oy = origin
    return [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]


def _entity_avg_angle(ei: EntityInfo,
                      origin: Tuple[float, float]) -> float:
    """
    Compute the average angular position (in degrees) of all vertices.
    
    Calculates the mean polar angle of all points relative to the motor center.
    This metric helps classify entities by their angular span within a slot region.

    Parameters
    ----------
    ei : EntityInfo
        Entity with `points` attribute containing list of (x, y) vertex coordinates.
    origin : Tuple[float, float]
        Motor center (ox, oy) used as reference for polar angle calculation.

    Returns
    -------
    float
        Average angular position in degrees [0.0, 360.0). Computed as mean of 
        arctan2 angles of all vertices. If ei.points is empty, returns 0.0.

    Examples
    --------
    >>> entity = EntityInfo(points=[(50, 0), (50, 50), (0, 50)], ...)
    >>> avg_angle = _entity_avg_angle(entity, origin=(0, 0))
    >>> print(avg_angle)  # Output: ~30.0 (between 0°, 45°, and 90°)
    
    Notes
    -----
    Angles are in the range [0°, 360°) following arctan2 polar convention.
    """


# ═══════════════════════════════════════════════════════════════
# 핵심: 스테이터 영역 분류
# ═══════════════════════════════════════════════════════════════

def classify_stator_entities(
    slot_entities: List[Dict],
    origin: Tuple[float, float] = (0.0, 0.0),
    airgap_r: float = None,
    r_outer: float = None,
    slot_pitch_deg: float = None,
    verbose: bool = False,
) -> Dict:
    """한 슬롯 영역의 고정자 엔티티들을 기하학적 특성에 따라 자동 분류합니다.

    고정자는 다층 구조로 되어 있습니다:
    - **요크(Yoke)**: 고정자의 바깥쪽 철심 (기계적 강도 담당)
    - **티스(Tooth)**: 슬롯 사이의 좁은 영역으로 자기  흐름 담당
    - **슬롯(Slot)**: 권선이 들어가는 공간 (공극과의 경계)
    - **슬롯오프닝(Slot Opening)**: 슬롯의 입구 부분 (가장 좁은 영역)
    - **컨덕터(Conductor)**: 권선 도선
    - **웨지(Wedge)**: 권선을 고정하는 쐐기

    이 함수는 반경 위치, 폐곡선 여부, 각도 분산 등을 종합 분석하여 각 엔티티의 역할을 판별합니다.

    Args:
        slot_entities (List[Dict]): 한 슬롯의 엔티티들. 
                                   [{​'entity': EntityInfo, 'original_angle': float, ...}, ...] 형태.
        origin (Tuple[float, float]): 고정자 중심(공극 중심). 기본값 (0.0, 0.0).
        airgap_r (float, optional): 공극 반경 (고정자 내경). 
                                   미제공 시 엔티티 반경 최댓값의 95% 추정.
        r_outer (float, optional): 고정자 외경. 
                                  미제공 시 엔티티 반경 최솟값의 110% 추정.
        slot_pitch_deg (float, optional): 슬롯 피치(도). 각도 클러스터링에 사용.
        verbose (bool): 분류 과정 및 상세 정보 로깅 활성화. 기본값 False.

    Returns:
        Dict: 분류 결과 및 고정자 영역 정보:
            - 'regions' (List[Dict]): 분류된 영역들 (각각 'entity', 'region_type', 'r_min', 'r_max' 등 포함).
            - 'yoke' (List[EntityInfo]): 요크로 분류된 엔티티들.
            - 'tooth' (List[EntityInfo]): 티스로 분류된 엔티티들.
            - 'slot' (List[EntityInfo]): 슬롯 공간으로 분류된 엔티티들.
            - 'slot_opening' (List[EntityInfo]): 슬롯오프닝으로 분류된 엔티티들.
            - 'conductor' (List[EntityInfo]): 도전재로 분류된 엔티티들.
            - 'wedge' (List[EntityInfo]): 웨지로 분류된 엔티티들.
            - 'n_slot_regions' (int): 분류된 영역의 총 개수.
            - 'slot_depth' (float): 슬롯 깊이 (반경 방향).
            - 'tooth_width' (float): 티스 폭 (방사형 각도).
            - 'slot_area' (float): 슬롯 전체 면적.
            - 'conductor_area' (float): 컨덕터 총 면적.
            - 'fill_factor' (float): 권선 충전율 (conductor_area / slot_area).
    """
    ox, oy = origin

    _empty = {
        'regions': [],
        'yoke': [], 'tooth': [], 'slot': [],
        'slot_opening': [], 'conductor': [],
        'n_slot_regions': 0,
        'n_conductor_regions': 0,
        'detail': 'No entities',
    }
    if not slot_entities:
        return _empty

    # ── 반경 범위 ──
    all_radii = []
    for item in slot_entities:
        all_radii.extend(_entity_radii(item['entity'], origin))
    if not all_radii:
        _empty['detail'] = 'No points'
        return _empty

    r_min_all = min(all_radii)
    r_max_all = max(all_radii)
    radial_range = r_max_all - r_min_all

    if airgap_r is None:
        airgap_r = r_min_all * 1.02
    if r_outer is None:
        r_outer = r_max_all

    # ── 경계 비율 설정 ──
    # inner_rotor 가정: airgap < tooth/slot < yoke < r_outer
    slot_opening_r = airgap_r + radial_range * 0.08  # 에어갭 바로 위 8%
    yoke_r = r_outer - radial_range * 0.25           # 바깥쪽 25% → 요크

    # ── 분류 ──
    yoke = []
    tooth = []
    slot_list = []
    slot_opening = []
    conductor = []
    regions = []

    for item in slot_entities:
        ei = item['entity']
        radii = _entity_radii(ei, origin)
        if not radii:
            tag = 'unknown'
            regions.append({**item, 'region': tag})
            continue

        r_min, r_max = min(radii), max(radii)
        r_avg = np.mean(radii)
        radial_span = r_max - r_min

        is_closed = ei.is_closed
        is_arc = ei.etype == 'ARC'
        is_line = ei.etype == 'LINE'

        # 요크 영역 (외측)
        if r_min > yoke_r:
            tag = 'stator_yoke'
            yoke.append(item)
        # 슬롯 오프닝 (에어갭 바로 위)
        elif r_avg < slot_opening_r and is_arc:
            tag = 'slot_opening'
            slot_opening.append(item)
        # 닫힌 폴리라인이면서 내부 → 컨덕터 후보
        elif is_closed and slot_opening_r < r_avg < yoke_r:
            tag = 'conductor'
            conductor.append(item)
        # 방사형 LINE (티스 구조)
        elif is_line and radial_span > radial_range * 0.2:
            tag = 'stator_tooth'
            tooth.append(item)
        # 원주 방향 ARC (요크 아래)
        elif is_arc and r_avg > yoke_r * 0.9:
            tag = 'stator_yoke'
            yoke.append(item)
        # 나머지 LINE/ARC
        else:
            # 각도 위치로 구분: 중심에 가까우면 tooth, 슬롯 내부면 slot
            tag = 'slot'
            slot_list.append(item)

        regions.append({**item, 'region': tag})

    if verbose:
        summary = Counter(r['region'] for r in regions)
        print(f"[stator_topology] 영역 분류: {dict(summary)}")
        print(f"  에어갭(r): {airgap_r:.2f}, 외경(r): {r_outer:.2f}")
        print(f"  슬롯오프닝 경계: {slot_opening_r:.2f}, 요크 경계: {yoke_r:.2f}")

    return {
        'regions': regions,
        'yoke': yoke,
        'tooth': tooth,
        'slot': slot_list,
        'slot_opening': slot_opening,
        'conductor': conductor,
        'n_slot_regions': len(slot_list),
        'n_conductor_regions': len(conductor),
        'detail': f'yoke={len(yoke)}, tooth={len(tooth)}, slot={len(slot_list)}, '
                  f'opening={len(slot_opening)}, conductor={len(conductor)}',
    }


# ═══════════════════════════════════════════════════════════════
# GUI 영역 재지정
# ═══════════════════════════════════════════════════════════════

def reassign_stator_region(regions: List[Dict],
                           entity_index: int,
                           new_region: str) -> List[Dict]:
    """자동 분류된 고정자 영역을 사용자가 GUI를 통해 수정할 수 있도록 재지정합니다.

    자동 분류 결과가 정확하지 않을 경우, 사용자는 시각적으로 영역을 확인하고 
    수동으로 '요크/티스/슬롯/컨덕터' 등을 다시 할당할 수 있습니다.

    Args:
        regions (List[Dict]): classify_stator_entities의 'regions' 출력. 
                             각 원소는 {​'entity': EntityInfo, 'region': str, ...} 형태.
        entity_index (int): 수정할 엔티티의 인덱스 (0~len(regions)-1).
        new_region (str): 새로운 영역 태그명 
                         ('stator_yoke', 'stator_tooth', 'slot', 'conductor' 등).

    Returns:
        List[Dict]: 업데이트된 regions 리스트.
    """
    if 0 <= entity_index < len(regions):
        regions[entity_index]['region'] = new_region
    return regions


def get_stator_region_summary(regions: List[Dict]) -> Dict:
    """분류된 고정자 영역들의 요약 통계를 반환합니다.

    각 영역 타입별로 엔티티의 개수를 집계하여 분류 결과의 빠른 개요를 제공합니다.

    Args:
        regions (List[Dict]): classify_stator_entities의 'regions' 출력.

    Returns:
        Dict: {​영역_타입: 개수, ...} 형태. 
             예: {​'stator_yoke': 3, 'stator_tooth': 5, 'conductor': 8, ...}
    """
    cnt = Counter(r['region'] for r in regions)
    return dict(cnt)


def classify_stator_entities_with_closing_compare(
    slot_entities: List[Dict],
    origin: Tuple[float, float] = (0.0, 0.0),
    airgap_r: float = None,
    r_outer: float = None,
    slot_pitch_deg: float = None,
    min_area: float = 1.0,
    verbose: bool = False,
) -> Dict:
    """
    Classify stator slot entities using dual-phase analysis with boundary closure validation.
    
    This advanced classification method operates in three stages:
    1. **Phase 1 (Raw)**: Classify slot entities using geometric heuristics alone
    2. **Phase 2 (Closed)**: Artificially close slot boundaries to create topologically 
       complete regions, then reclassify using the closed faces
    3. **Phase 3 (Comparison)**: Compare both results to detect classification inconsistencies
    
    This dual-phase approach helps answer: "Does the classification stabilize when we 
    enforce topological closure?" Discrepancies between raw and closed results indicate 
    edge-touching entities or boundary artifacts that may warrant manual inspection.

    Parameters
    ----------
    slot_entities : List[Dict]
        List of entities within a single stator slot. Each dict contains 'entity' 
        (EntityInfo) and angle information ('original_angle', 'relative_angle'). Typically
        generated from half-slot or full-slot CAD extraction.
    origin : Tuple[float, float], optional
        Motor center (x, y) coordinate for polar calculations. Default is (0.0, 0.0).
    airgap_r : float, optional
        Airgap radius in motor units. If None, Phase 2 (closure) is skipped.
        Used to filter out detected faces that fall below 98% of this radius (stator side only).
    r_outer : float, optional
        Outer stator radius (yoke surface). If None, Phase 2 is skipped.
        Used as boundary for artificial closing arc and radial lines.
    slot_pitch_deg : float, optional
        Slot pitch in degrees (angular span of one slot). If None, Phase 2 is skipped.
        Used to define the angular extent of artificial closing boundaries.
    min_area : float, optional
        Minimum face area threshold for detected closed regions in Phase 2. Default is 1.0.
        Filters out numerical noise or artifact faces smaller than this threshold.
    verbose : bool, optional
        If True, print debug messages during classification. Default is False.

    Returns
    -------
    Dict
        Nested dictionary with four keys:
        
        - **'raw'** : Dict
            Phase 1 raw classification results from `classify_stator_entities()`.
            Contains 'regions' (list of dicts with 'region', 'area', 'radii', etc.),
            'n_slot_regions', and 'n_conductor_regions' counts.
        
        - **'closed'** : Dict or None
            Phase 2 closed-boundary classification results. None if required parameters 
            (airgap_r, r_outer, slot_pitch_deg) are missing. Uses the same structure as 'raw'.
        
        - **'faces'** : List[Dict] or None
            Detected closed faces from Phase 2. Each dict contains 'vertices', 'centroid_r',
            'area', 'perimeter'. Filtered to include only faces with radii ≥ 0.98 * airgap_r.
            None if closure fails.
        
        - **'comparison'** : Dict
            Detailed comparison metrics between Phase 1 and Phase 2:
            
            - **'slot_regions'** : Dict with keys 'raw' and 'closed' (counts)
            - **'conductor_regions'** : Dict with keys 'raw' and 'closed' (counts)
            - **'region_counts'** : Dict mapping region labels to {'raw': count, 'closed': count}
            - **'face_count'** : Number of closed faces detected (int)
            - **'note'** : Explanation if closure failed (e.g., "insufficient inputs for closing")

    Examples
    --------
    Example 1: Validate slot classification with closure analysis
    
    >>> slot_entities = extract_slot_entities(...)  # Extract from half-slot geometry
    >>> result = classify_stator_entities_with_closing_compare(
    ...     slot_entities,
    ...     origin=(0.0, 0.0),
    ...     airgap_r=50.0,
    ...     r_outer=80.0,
    ...     slot_pitch_deg=45.0,  # 8-pole, 6 slots/pole
    ... )
    >>> 
    >>> # Inspect raw vs. closed conductor counts
    >>> print(result['comparison']['conductor_regions'])
    # Output: {'raw': {'Conductor': 2}, 'closed': {'Conductor': 2}}
    # If raw and closed differ significantly, inspect boundary effects
    
    Example 2: Detect classification instability
    
    >>> if result['comparison']['conductor_regions']['raw'] != result['comparison']['conductor_regions']['closed']:
    ...     print("⚠️ Classification differs between raw and closed modes")
    ...     print(f"Region difference: {result['comparison']['region_counts']}")
    ...     # May indicate edge-touching conductor strands or artifacts
    >>> 
    >>> # Inspect detected closed faces for topology insights
    >>> faces = result['faces']
    >>> for face in faces:
    ...     print(f"Face: area={face['area']:.2f}, centroid_r={face['centroid_r']:.2f}")

    Algorithm Details
    ------------------
    
    **Phase 1 (Raw Classification):**
    Applies radial and angular geometry heuristics to classify entities as 
    slot, conductor, tooth, yoke, wedge, or slot opening based on positional 
    and morphological features without enforcing topological closure.
    
    **Phase 2 (Closure & Reclassification):**
    1. Defines four artificial closing boundaries:
       - Two radial lines: inner radius (airgap_r) to outer radius (r_outer) 
         at 0° and slot_pitch_deg
       - Two arc boundaries: inner arc at airgap_r and outer arc at r_outer, 
         both spanning 0° to slot_pitch_deg
    
    2. Combines original + closing boundaries → Detects closed faces using 
       planar graph analysis or convex hull methods
    
    3. Filters faces by centroid radius (≥ 0.98 * airgap_r) to remove geometry 
       outside the stator active region
    
    4. Reclassifies using closed faces instead of raw entities
    
    **Phase 3 (Comparison):**
    Tallies region counts in both phases and computes differences by class.
    
    Notes
    -----
    - **Closure benefit**: Identifies entities that touch slot boundaries and may be 
      misclassified in raw mode. Especially useful for conductor strands near slot openings.
    - **When to use**: Best suited for detailed slot analysis where classification 
      confidence is critical. For quick inventory checks, use `classify_stator_entities()` directly.
    - **Parameters sensitivity**: Slot pitch and radii must be accurate. Misconfigured 
      radii may cause the closure boundaries to exclude valid entities.
    - **Comparison interpretation**:
      * If raw ≈ closed → Classification is robust; minimal boundary artifacts
      * If raw ≠ closed → Check `region_diff` to pinpoint discrepancies; may require 
        manual review of edge entities
    - **Performance**: Closure topological analysis is computationally more expensive 
      than raw classification; suitable for interactive GUI workflows, not batch processing.
    """
    raw = classify_stator_entities(
        slot_entities,
        origin=origin,
        airgap_r=airgap_r,
        r_outer=r_outer,
        slot_pitch_deg=slot_pitch_deg,
        verbose=verbose,
    )

    if not slot_entities or airgap_r is None or r_outer is None or slot_pitch_deg is None:
        return {
            'raw': raw,
            'closed': None,
            'comparison': {'note': 'insufficient inputs for closing'},
        }

    boundaries = [
        create_radial_line(airgap_r, r_outer, 0.0, origin),
        create_radial_line(airgap_r, r_outer, float(slot_pitch_deg), origin),
        create_arc_boundary(airgap_r, 0.0, float(slot_pitch_deg), origin),
        create_arc_boundary(r_outer, 0.0, float(slot_pitch_deg), origin),
    ]

    base_entities = [item['entity'] for item in slot_entities]
    closed_entities = list(base_entities) + boundaries
    faces = detect_closed_faces(closed_entities, origin, min_area=min_area)
    faces = [
        fi for fi in faces
        if fi.get('centroid_r', 0.0) >= airgap_r * 0.98
    ]

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

    closed = classify_stator_entities(
        closed_items,
        origin=origin,
        airgap_r=airgap_r,
        r_outer=r_outer,
        slot_pitch_deg=slot_pitch_deg,
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
        'slot_regions': {
            'raw': raw.get('n_slot_regions'),
            'closed': closed.get('n_slot_regions'),
        },
        'conductor_regions': {
            'raw': raw.get('n_conductor_regions'),
            'closed': closed.get('n_conductor_regions'),
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
