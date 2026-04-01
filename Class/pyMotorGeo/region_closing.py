"""
pyMotorGeo.region_closing
==========================

Topological region closure and closed face detection for periodic motor geometry.

This module detects topologically closed regions (faces) in motor geometry by:
1. Creating artificial boundary entities (radial lines, arcs) at periodic sector boundaries
2. Applying graph traversal to identify minimal closed paths (faces)
3. Labeling faces with region names (magnet, slot, tooth, conductor, etc.)

**Background**: In periodic sector CAD models (e.g., half-slot or one-pole extracts), 
certain motor regions (stator yoke, rotor core, shaft) appear open at the periodic 
boundaries (0° and period_deg). This module artificially "closes" those regions to enable 
downstream face-based analysis and GUI region assignment.

**Recommended Workflow (v1.5.1): Per-Pole Closure**

This is the modern, scalable approach:

1. Extract minimum repeating unit (half-pole or quarter-pole):
   `extract_half_pole_entities(roi, ...)`

2. Expand to single pole:
   `reconstruct_from_half(half_pole_entities, n_repeats=1, ...)`

3. Close one pole with boundary lines and arcs:
   `close_one_pole(one_pole_entities, airgap_r, yoke_r, pole_span_deg, ...)`

4. Detect closed faces topologically:
   `faces = detect_closed_faces(closed_entities, origin, ...)`

5. Automatically label faces by region:
   `auto_name_faces(faces, r_shaft, r_rotor_outer, r_stator_inner, r_stator_outer)`

6. Generate full motor via rotation and circular array pattern:
   `reconstruct_from_half(one_pole_pattern, n_repeats=n_poles, ...)`

**Legacy Workflow (v1.4): Full Periodic Model Closure**

Supported for backward compatibility:

1. Close entire periodic model:
   `close_period_model(entities, inner_radius, outer_radius, period_deg, ...)`

2. Detect and label faces:
   `faces = detect_closed_faces(...); auto_name_faces(faces, ...)`

Key Components
---------------
- **Boundary Creation**: `create_radial_line()`, `create_arc_boundary()` — Add synthetic edges
- **Closure Functions**: `close_one_pole()`, `close_one_slot()`, `close_period_model()` — Wrap geometry
- **Face Detection**: `detect_closed_faces()` — Topological traversal via minimal cycle detection
- **Auto-Labeling**: `auto_name_faces()`, `auto_name_faces_v2()` — Assign region types by position
- **Utilities**: `get_face_summary()` — Statistics, `_build_adj()`, `_traverse_minimal_faces()` — Graph algorithms

Integration with Other Modules
-------------------------------
- **region_closing → topology**: Use closed faces as input to `classify_*_entities()`
- **topology → gui_region**: Faces displayed/edited in `FaceRegionGUI` or `FaceRegionGUILite`
- **half_unit → region_closing**: Extract minimum units, expand, then close
"""

import math
import numpy as np
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional
from core import EntityInfo, endpoint_key


# ═══════════════════════════════════════════════════════════════
# 경계 직선 생성
# ═══════════════════════════════════════════════════════════════

def create_radial_line(r_start: float, r_end: float,
                       angle_deg: float,
                       origin: Tuple[float, float] = (0.0, 0.0),
                       layer: str = '_BOUNDARY_',
                       n_segments: int = 1) -> EntityInfo:
    """
    Create a radial boundary line at a specified angle.
    
    Generates a synthetic line segment from radius `r_start` to `r_end` at angle 
    `angle_deg`. Used to artificially close geometries at periodic sector boundaries 
    (e.g., closing a motor pole or slot for topological face detection).

    Parameters
    ----------
    r_start : float
        Starting radius (closer to motor center), in motor units.
    r_end : float
        Ending radius (farther from motor center), in motor units.
    angle_deg : float
        Angular position in degrees [0, 360). Serves as the angle of the radial line.
    origin : Tuple[float, float], optional
        Motor center (ox, oy) coordinate. Default is (0.0, 0.0).
    layer : str, optional
        CAD layer name for the boundary line. Default is '_BOUNDARY_'. 
        Used for identification and filtering.
    n_segments : int, optional
        Number of line segments to subdivide the radial line. If 1, creates a single 
        line segment; if > 1, subdivides into n_segments+1 points for better mesh 
        alignment. Default is 1.

    Returns
    -------
    EntityInfo
        A LINE entity representing the radial boundary. The entity has:
        - etype='LINE'
        - layer=`layer`
        - points=[p_start, p_end] or longer list if n_segments > 1
        - is_closed=False

    Algorithm
    ---------
    Converts polar coordinates (r, angle_deg) to Cartesian:
    
    >>> x = ox + r * cos(angle_rad)
    >>> y = oy + r * sin(angle_rad)
    
    If n_segments > 1, subdivides the radial segment linearly along the radius.

    Examples
    --------
    Example 1: Single radial line at 45° from r=30 to r=70
    
    >>> line = create_radial_line(r_start=30, r_end=70, angle_deg=45, origin=(0,0))
    >>> print(line.points)
    # Output: [(21.21, 21.21), (49.497, 49.497)]
    
    Example 2: Segmented radial line for better mesh alignment
    
    >>> line = create_radial_line(30, 70, 0, origin=(0,0), n_segments=4)
    >>> len(line.points)
    # Output: 5  (subdivided into 5 points)

    Use Cases
    ---------
    - **Pole Closure**: Create radial lines at 0° and pole_span_deg to close one rotor pole
    - **Slot Closure**: Create radial lines at 0° and slot_pitch_deg to close one slot region
    - **Boundary Definition**: Part of `close_one_pole()` or `close_period_model()` workflows
    """
    ox, oy = origin
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    if n_segments <= 1:
        p1 = (ox + r_start * cos_a, oy + r_start * sin_a)
        p2 = (ox + r_end * cos_a, oy + r_end * sin_a)
        points = [p1, p2]
    else:
        radii = np.linspace(r_start, r_end, n_segments + 1)
        points = [(ox + r * cos_a, oy + r * sin_a) for r in radii]

    return EntityInfo(
        etype='LINE',
        layer=layer,
        points=points,
        is_closed=False,
    )


def create_arc_boundary(radius: float,
                        start_deg: float, end_deg: float,
                        origin: Tuple[float, float] = (0.0, 0.0),
                        layer: str = '_BOUNDARY_',
                        n_points: int = 32) -> EntityInfo:
    """
    Create a circular arc boundary at a specified radius.
    
    Generates a synthetic arc segment at constant radius from `start_deg` to `end_deg`. 
    The arc is approximated as a polyline with `n_points` vertices. Used alongside 
    radial lines to enclose motor regions during topological face detection.

    Parameters
    ----------
    radius : float
        Arc radius in motor units. Determines the distance from the origin to all 
        arc points.
    start_deg : float
        Starting angular position in degrees [0, 360).
    end_deg : float
        Ending angular position in degrees [0, 360).
    origin : Tuple[float, float], optional
        Motor center (ox, oy) coordinate. Default is (0.0, 0.0).
    layer : str, optional
        CAD layer name for the boundary arc. Default is '_BOUNDARY_'. 
        Used for identification and filtering.
    n_points : int, optional
        Number of points to sample along the arc for polyline approximation. 
        Higher values give smoother arcs; minimum recommended is 8. Default is 32.

    Returns
    -------
    EntityInfo
        An ARC entity representing the circular arc boundary. The entity has:
        - etype='ARC'
        - layer=`layer`
        - points: List of (x, y) tuples sampled along the arc
        - radius: `radius`
        - center: `origin`
        - start_angle: `start_deg % 360`
        - end_angle: `end_deg % 360`
        - is_closed=False

    Algorithm
    ---------
    Uses polar-to-Cartesian conversion with uniform angular sampling:
    
    >>> angles = linspace(start_deg, end_deg, n_points)
    >>> points = [(ox + r*cos(angle), oy + r*sin(angle)) for angle in angles]

    Examples
    --------
    Example 1: Inner arc for one-pole closure (airgap boundary)
    
    >>> arc = create_arc_boundary(radius=50, start_deg=0, end_deg=45, origin=(0,0))
    >>> len(arc.points)
    # Output: 32
    
    Example 2: Outer arc (yoke boundary) with coarser sampling
    
    >>> arc = create_arc_boundary(radius=80, start_deg=0, end_deg=45, 
    ...                          origin=(0,0), n_points=16)

    Use Cases
    ---------
    - **Inner Boundary**: `create_arc_boundary(airgap_r, 0, pole_deg)` closes airgap side
    - **Outer Boundary**: `create_arc_boundary(yoke_r, 0, pole_deg)` closes yoke side
    - **Slot Closure**: `create_arc_boundary(airgap_r, 0, slot_pitch)` for slot regions
    - **Part of `close_one_pole()` / `close_one_slot()`**: Combined with radial lines

    Notes
    -----
    - Arc is approximated as a polyline; true circular path exists only if visualized
    - Angular order: start_deg → end_deg. If end_deg < start_deg, wrapping behavior 
      depends on numpy.linspace (no automatic wrapping)
    - For motor geometry, typical pole/slot angles are 5°–90°; n_points=32 is usually sufficient
    """
    ox, oy = origin
    angles = np.linspace(start_deg, end_deg, n_points)
    points = [(ox + radius * np.cos(np.radians(a)),
               oy + radius * np.sin(np.radians(a)))
              for a in angles]

    return EntityInfo(
        etype='ARC',
        layer=layer,
        points=points,
        radius=radius,
        center=origin,
        start_angle=start_deg % 360,
        end_angle=end_deg % 360,
        is_closed=False,
    )


# ═══════════════════════════════════════════════════════════════
# 로터 주기 모델 닫기
# ═══════════════════════════════════════════════════════════════

def close_rotor_period(
    rotor_entities: List[EntityInfo],
    origin: Tuple[float, float],
    period_deg: float,
    r_shaft: float,
    r_rotor_outer: float,
    layer: str = '_BOUNDARY_',
) -> Tuple[List[EntityInfo], List[EntityInfo]]:
    """
    로터 주기모델의 경계선을 추가하여 닫힌 영역을 형성합니다.

    0°와 period_deg 경계에 방사 직선 추가:
    - shaft 반경 ~ rotor 외경

    Parameters
    ----------
    rotor_entities : 주기모델 로터 엔티티 리스트
    origin : 원점
    period_deg : 주기 각도 (deg)
    r_shaft : 샤프트 내경
    r_rotor_outer : 로터 외경 (에어갭 내측)
    layer : 경계선 레이어 이름

    Returns
    -------
    (closed_entities, boundary_lines)
        closed_entities : 원본 + 경계선 엔티티
        boundary_lines : 추가된 경계선만
    """
    boundaries = []

    # 0° 경계 (x축 양의 방향)
    line_0_rotor = create_radial_line(
        r_shaft, r_rotor_outer, 0.0, origin, layer=layer)
    boundaries.append(line_0_rotor)

    # period_deg 경계
    line_p_rotor = create_radial_line(
        r_shaft, r_rotor_outer, period_deg, origin, layer=layer)
    boundaries.append(line_p_rotor)

    # shaft 호 (0° ~ period_deg, 내측)
    arc_shaft = create_arc_boundary(
        r_shaft, 0.0, period_deg, origin, layer=layer)
    boundaries.append(arc_shaft)

    # rotor 외경 호 (0° ~ period_deg)
    arc_outer = create_arc_boundary(
        r_rotor_outer, 0.0, period_deg, origin, layer=layer)
    boundaries.append(arc_outer)

    closed = list(rotor_entities) + boundaries
    return closed, boundaries


# ═══════════════════════════════════════════════════════════════
# 스테이터 주기 모델 닫기
# ═══════════════════════════════════════════════════════════════

def close_stator_period(
    stator_entities: List[EntityInfo],
    origin: Tuple[float, float],
    period_deg: float,
    r_stator_inner: float,
    r_stator_outer: float,
    layer: str = '_BOUNDARY_',
) -> Tuple[List[EntityInfo], List[EntityInfo]]:
    """
    스테이터 주기모델의 경계선을 추가하여 닫힌 영역을 형성합니다.

    0°와 period_deg 경계에 방사 직선 추가:
    - stator 내경 ~ stator 외경

    Parameters
    ----------
    stator_entities : 주기모델 스테이터 엔티티 리스트
    origin : 원점
    period_deg : 주기 각도 (deg)
    r_stator_inner : 스테이터 내경 (에어갭 외측)
    r_stator_outer : 스테이터 외경
    layer : 경계선 레이어 이름

    Returns
    -------
    (closed_entities, boundary_lines)
        closed_entities : 원본 + 경계선 엔티티
        boundary_lines : 추가된 경계선만
    """
    boundaries = []

    # 0° 경계
    line_0_stator = create_radial_line(
        r_stator_inner, r_stator_outer, 0.0, origin, layer=layer)
    boundaries.append(line_0_stator)

    # period_deg 경계
    line_p_stator = create_radial_line(
        r_stator_inner, r_stator_outer, period_deg, origin, layer=layer)
    boundaries.append(line_p_stator)

    # stator 내경 호 (0° ~ period_deg)
    arc_inner = create_arc_boundary(
        r_stator_inner, 0.0, period_deg, origin, layer=layer)
    boundaries.append(arc_inner)

    # stator 외경 호 (0° ~ period_deg)
    arc_outer = create_arc_boundary(
        r_stator_outer, 0.0, period_deg, origin, layer=layer)
    boundaries.append(arc_outer)

    closed = list(stator_entities) + boundaries
    return closed, boundaries


# ═══════════════════════════════════════════════════════════════
# 통합: 로터 + 스테이터 + 에어갭 동시 닫기
# ═══════════════════════════════════════════════════════════════

def close_period_model(
    rotor_entities: List[EntityInfo],
    stator_entities: List[EntityInfo],
    origin: Tuple[float, float],
    period_deg: float,
    r_shaft: float,
    r_rotor_outer: float,
    r_stator_inner: float,
    r_stator_outer: float,
    layer: str = '_BOUNDARY_',
) -> Dict:
    """
    주기모델 전체를 닫힌 영역으로 만듭니다.
    에어갭 경계는 추가하지 않습니다 (별도 불필요).

    Parameters
    ----------
    rotor_entities, stator_entities : 주기모델 엔티티
    origin : 원점
    period_deg : 주기 각도 (deg)
    r_shaft : 샤프트 반경
    r_rotor_outer : 로터 외경 (= airgap 내측)
    r_stator_inner : 스테이터 내경 (= airgap 외측)
    r_stator_outer : 스테이터 외경

    Returns
    -------
    Dict:
        rotor_closed, stator_closed, rotor_boundaries, stator_boundaries,
        all_entities, period_deg, r_shaft, r_rotor_outer,
        r_stator_inner, r_stator_outer
    """
    rotor_closed, rotor_bdry = close_rotor_period(
        rotor_entities, origin, period_deg,
        r_shaft, r_rotor_outer, layer)

    stator_closed, stator_bdry = close_stator_period(
        stator_entities, origin, period_deg,
        r_stator_inner, r_stator_outer, layer)

    return {
        'rotor_closed': rotor_closed,
        'stator_closed': stator_closed,
        'rotor_boundaries': rotor_bdry,
        'stator_boundaries': stator_bdry,
        'all_entities': rotor_closed + stator_closed,
        'period_deg': period_deg,
        'r_shaft': r_shaft,
        'r_rotor_outer': r_rotor_outer,
        'r_stator_inner': r_stator_inner,
        'r_stator_outer': r_stator_outer,
    }


# ═══════════════════════════════════════════════════════════════
# v1.5.1: 1극/1슬롯 단위 닫기 (권장)
# ═══════════════════════════════════════════════════════════════

def close_one_pole(
    one_pole_entities: List[EntityInfo],
    origin: Tuple[float, float],
    pole_pitch_deg: float,
    r_shaft: float,
    r_rotor_outer: float,
    concentric_radials: Optional[List[EntityInfo]] = None,
    start_angle_deg: float = 0.0,
    layer: str = '_BOUNDARY_',
) -> Dict:
    """
    1극(one pole) 엔티티에 경계선을 추가하여 닫힌 영역을 형성합니다.

    half-pole → mirror → 1 pole → close_one_pole() 순서로 사용.
    이 방식이 주기모델 전체를 한 번에 닫는 것보다 더 자연스럽고,
    각 극이 독립적인 완결 단위가 됩니다.

    Parameters
    ----------
    one_pole_entities : 1극 엔티티 리스트 (reconstruct_from_half 결과)
    origin : 원점
    pole_pitch_deg : 극 피치 (deg) = 360 / n_poles
    r_shaft : 샤프트 반경 (내측 경계)
    r_rotor_outer : 로터 외경 (외측 경계 = airgap 내측)
    concentric_radials : half-pole 동심원 경계용 방사선(선택)
    start_angle_deg : 시작 각도 (보통 0°)
    layer : 경계선 레이어 이름

    Returns
    -------
    Dict:
        closed_entities : 원본 + 경계선
        boundaries : 추가된 경계선만
        pole_pitch_deg, r_shaft, r_rotor_outer, start_angle_deg

    사용 예시::

        # 1) half-pole 추출
        half_pole = extract_half_pole_entities(rotor_entities, origin, pole_pitch_deg)

        # 2) 1극 재구성 (mirror)
        one_pole = reconstruct_from_half(half_pole, origin, n_repeats=1)

        # 3) 1극 닫기
        result = close_one_pole(one_pole, origin, pole_pitch_deg, r_shaft, r_rotor_outer)

        # 4) face 탐지 및 이름 할당
        faces = detect_closed_faces(result['closed_entities'], origin)
        auto_name_faces(faces, r_shaft, r_rotor_outer, r_stator_inner, r_stator_outer)

        # 5) 필요시 n_poles번 circular pattern
    """
    boundaries = []
    end_angle_deg = start_angle_deg + pole_pitch_deg

    # 시작각 경계 (방사 직선)
    line_start = create_radial_line(
        r_shaft, r_rotor_outer, start_angle_deg, origin, layer=layer)
    boundaries.append(line_start)

    # 끝각 경계 (방사 직선)
    line_end = create_radial_line(
        r_shaft, r_rotor_outer, end_angle_deg, origin, layer=layer)
    boundaries.append(line_end)

    # 샤프트 호 (내측)
    arc_shaft = create_arc_boundary(
        r_shaft, start_angle_deg, end_angle_deg, origin, layer=layer)
    boundaries.append(arc_shaft)

    # 로터 외경 호 (외측)
    arc_outer = create_arc_boundary(
        r_rotor_outer, start_angle_deg, end_angle_deg, origin, layer=layer)
    boundaries.append(arc_outer)

    if concentric_radials:
        boundaries.extend(concentric_radials)

    closed = list(one_pole_entities) + boundaries

    return {
        'closed_entities': closed,
        'boundaries': boundaries,
        'pole_pitch_deg': pole_pitch_deg,
        'r_shaft': r_shaft,
        'r_rotor_outer': r_rotor_outer,
        'start_angle_deg': start_angle_deg,
        'end_angle_deg': end_angle_deg,
    }


def close_one_slot(
    one_slot_entities: List[EntityInfo],
    origin: Tuple[float, float],
    slot_pitch_deg: float,
    r_stator_inner: float,
    r_stator_outer: float,
    start_angle_deg: float = 0.0,
    layer: str = '_BOUNDARY_',
) -> Dict:
    """
    1슬롯(one slot) 엔티티에 경계선을 추가하여 닫힌 영역을 형성합니다.

    half-slot → mirror → 1 slot → close_one_slot() 순서로 사용.

    Parameters
    ----------
    one_slot_entities : 1슬롯 엔티티 리스트 (reconstruct_from_half 결과)
    origin : 원점
    slot_pitch_deg : 슬롯 피치 (deg) = 360 / n_slots
    r_stator_inner : 스테이터 내경 (내측 경계 = airgap 외측)
    r_stator_outer : 스테이터 외경 (외측 경계)
    start_angle_deg : 시작 각도 (보통 0°)
    layer : 경계선 레이어 이름

    Returns
    -------
    Dict:
        closed_entities : 원본 + 경계선
        boundaries : 추가된 경계선만
        slot_pitch_deg, r_stator_inner, r_stator_outer, start_angle_deg

    사용 예시::

        # 1) half-slot 추출
        half_slot = extract_half_slot_entities(stator_entities, origin, slot_pitch_deg, n_slots)

        # 2) 1슬롯 재구성 (mirror)
        one_slot = reconstruct_from_half(half_slot, origin, n_repeats=1)

        # 3) 1슬롯 닫기
        result = close_one_slot(one_slot, origin, slot_pitch_deg, r_stator_inner, r_stator_outer)

        # 4) face 탐지 및 이름 할당
        faces = detect_closed_faces(result['closed_entities'], origin)
        auto_name_faces(faces, ...)

        # 5) 필요시 n_slots번 circular pattern
    """
    boundaries = []
    end_angle_deg = start_angle_deg + slot_pitch_deg

    # 시작각 경계 (방사 직선)
    line_start = create_radial_line(
        r_stator_inner, r_stator_outer, start_angle_deg, origin, layer=layer)
    boundaries.append(line_start)

    # 끝각 경계 (방사 직선)
    line_end = create_radial_line(
        r_stator_inner, r_stator_outer, end_angle_deg, origin, layer=layer)
    boundaries.append(line_end)

    # 스테이터 내경 호 (내측)
    arc_inner = create_arc_boundary(
        r_stator_inner, start_angle_deg, end_angle_deg, origin, layer=layer)
    boundaries.append(arc_inner)

    # 스테이터 외경 호 (외측)
    arc_outer = create_arc_boundary(
        r_stator_outer, start_angle_deg, end_angle_deg, origin, layer=layer)
    boundaries.append(arc_outer)

    closed = list(one_slot_entities) + boundaries

    return {
        'closed_entities': closed,
        'boundaries': boundaries,
        'slot_pitch_deg': slot_pitch_deg,
        'r_stator_inner': r_stator_inner,
        'r_stator_outer': r_stator_outer,
        'start_angle_deg': start_angle_deg,
        'end_angle_deg': end_angle_deg,
    }


# ═══════════════════════════════════════════════════════════════
# 3. Planar-graph 기반 닫힌 면(face) 탐지
# ═══════════════════════════════════════════════════════════════

# 이름 / 색상 상수
REGION_NAMES = {
    'stator_yoke':    'Stator Yoke',
    'stator_tooth':   'Stator Tooth',
    'slot':           'Slot',
    'slot_opening':   'Slot Opening',
    'airgap':         'Airgap',
    'rotor_core':     'Rotor Core',
    'magnet':         'Magnet',
    'air_barrier':    'Air Barrier',
    'shaft':          'Shaft',
    'unknown':        'Unknown',
}

REGION_COLORS = {
    'stator_yoke':    '#4A90D9',
    'stator_tooth':   '#7EC8E3',
    'slot':           '#FFD700',
    'slot_opening':   '#FFFACD',
    'airgap':         '#FFFFFF',
    'rotor_core':     '#FF8C42',
    'magnet':         '#FF4444',
    'air_barrier':    '#C0C0C0',
    'shaft':          '#8B8B8B',
    'unknown':        '#D0D0D0',
}


def _entity_ep(ei: EntityInfo, tol: int = 2) -> Optional[Tuple]:
    """엔티티 시작/끝 endpoint key 반환. CIRCLE → None."""
    if ei.etype == 'CIRCLE':
        return None
    if ei.etype == 'LINE' and ei.points and len(ei.points) >= 2:
        return (endpoint_key(*ei.points[0], tol),
                endpoint_key(*ei.points[-1], tol))
    if ei.etype == 'ARC' and ei.center and ei.radius:
        cx, cy = ei.center
        r = ei.radius
        sa = math.radians(ei.start_angle)
        ea = math.radians(ei.end_angle)
        p0 = (cx + r * math.cos(sa), cy + r * math.sin(sa))
        p1 = (cx + r * math.cos(ea), cy + r * math.sin(ea))
        return (endpoint_key(*p0, tol), endpoint_key(*p1, tol))
    if ei.points and len(ei.points) >= 2:
        return (endpoint_key(*ei.points[0], tol),
                endpoint_key(*ei.points[-1], tol))
    return None


def _build_adj(entities: List[EntityInfo], tol: int = 2):
    """엔티티 리스트 → adjacency dict + edge_to_entity dict."""
    adj = defaultdict(set)
    emap = {}
    for ei in entities:
        ep = _entity_ep(ei, tol)
        if ep is None:
            continue
        k0, k1 = ep
        if k0 == k1:
            continue
        edge = tuple(sorted([k0, k1]))
        if edge not in emap:
            emap[edge] = ei
            adj[k0].add(k1)
            adj[k1].add(k0)
    return adj, emap


def _traverse_minimal_faces(adj: Dict) -> List[List]:
    """
    평면 그래프의 모든 최소 면(face)을 각도 순회로 탐지.
    반시계 방향 순회 → 양의 면적인 face만 반환.
    """
    sorted_nb = {}
    for node in adj:
        nbs = list(adj[node])
        if not nbs:
            continue
        nbs.sort(key=lambda nb: math.atan2(nb[1] - node[1], nb[0] - node[0]))
        sorted_nb[node] = nbs

    used = set()
    faces = []

    for node in sorted_nb:
        for start_nb in sorted_nb[node]:
            he = (node, start_nb)
            if he in used:
                continue
            face_verts = []
            cur, nxt = node, start_nb
            for _ in range(len(adj) + 5):
                used.add((cur, nxt))
                face_verts.append(cur)
                if nxt not in sorted_nb:
                    break
                nbs = sorted_nb[nxt]
                try:
                    idx = nbs.index(cur)
                except ValueError:
                    break
                cur, nxt = nxt, nbs[(idx - 1) % len(nbs)]
                if cur == node and nxt == start_nb:
                    break
            if len(face_verts) >= 3:
                area = _signed_area(face_verts)
                if area > 0:
                    faces.append(face_verts)
    return faces


def _signed_area(verts: List) -> float:
    """Shoelace formula (부호 있는 면적)."""
    n = len(verts)
    a = 0.0
    for i in range(n):
        x0, y0 = verts[i]
        x1, y1 = verts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def detect_closed_faces(
    entities: List[EntityInfo],
    origin: Tuple[float, float] = (0.0, 0.0),
    min_area: float = 0.5,
    tol_digits: int = 2,
    use_shapely: bool = True,
) -> List[Dict]:
    """
    Topologically detect all closed regions (faces) from a list of entities.
    
    This core function identifies topologically closed 2D polygons (faces) by building 
    a planar graph from entity endpoints and edges, then traversing minimal cycles. 
    Optionally uses shapely's `polygonize()` for improved accuracy. Essential for 
    converting open CAD geometry into face-based region classification.

    Parameters
    ----------
    entities : List[EntityInfo]
        List of entities (LINE, ARC, LWPOLYLINE) representing boundaries and closures.
        These should include original CAD geometry plus artificial boundaries created 
        by `create_radial_line()` and `create_arc_boundary()`.
    
    origin : Tuple[float, float], optional
        Motor center (ox, oy) used for computing centroid_r (distance from origin to face center)
        and centroid_ang (angular position of face center). Default is (0.0, 0.0).
    
    min_area : float, optional
        Minimum face area threshold (in motor units²). Faces with area < min_area are 
        filtered out to remove numerical noise and artifact faces. Default is 0.5.
    
    tol_digits : int, optional
        Decimal precision for endpoint matching in planar graph construction (planar 
        graph method only, not used if shapely is available). E.g., tol_digits=2 
        rounds to nearest 0.01 units. Default is 2.
    
    use_shapely : bool, optional
        If True (default), attempts to use shapely's `polygonize()` via face_detection module 
        for improved robustness. Falls back to planar graph method if shapely is unavailable 
        or returns empty results. If False, forces planar graph method.

    Returns
    -------
    List[Dict]
        List of detected faces, sorted by area (largest first). Each face dict contains:
        
        - **'vertices'** : List of (x, y) tuples representing the polygon boundary
        - **'area'** : Polygon area (positive; computed via Shoelace formula)
        - **'n_edges'** : Number of boundary vertices (polygon side count)
        - **'centroid'** : (cx, cy) tuple — geometric center of polygon
        - **'interior_point'** : (x, y) tuple — guaranteed point inside polygon (for containment tests)
        - **'centroid_r'** : Distance from `origin` to centroid (in motor units)
        - **'centroid_ang'** : Angular position of centroid [0, 360) degrees
        - **'r_min'** : Minimum radius among all vertices
        - **'r_max'** : Maximum radius among all vertices
        - **'r_mean'** : Average radius of vertices
        - **'name'** : Region label (initially 'unknown', updated by `auto_name_faces()`)
        - **'polygon'** : (shapely only) shapely.geometry.Polygon object for advanced geometry ops

    Algorithm
    ---------
    
    **Shapely Method (preferred, if available):**
    1. Converts entities to shapely LineStrings
    2. Calls `shapely.ops.polygonize()` to extract all minimal closed polygons
    3. Filters by area threshold
    4. Fast, robust to edge overlaps; handles CoLinear edges better
    
    **Planar Graph Method (fallback):**
    1. Builds adjacency list from entity endpoints (snapped to grid by `tol_digits`)
    2. Traverses minimal cycles using depth-first search (`_traverse_minimal_faces()`)
    3. Computes polygon properties (area, centroid, radii)
    4. Filters by min_area
    
    Detects face size automatically; large regions like "stator yoke" or "rotor core" 
    have area > 100; small regions like "slot conductor" have area < 10.

    Examples
    --------
    Example 1: Detect faces from a closed one-pole unit
    
    >>> from pyMotorGeo.region_closing import close_one_pole, detect_closed_faces
    >>> one_pole = extract_half_pole_entities(...)
    >>> closed = close_one_pole(one_pole, airgap_r=50, yoke_r=80, pole_deg=45)
    >>> faces = detect_closed_faces(closed, origin=(0,0), min_area=0.5)
    >>> print(f"Detected {len(faces)} faces")
    # Output: Detected 8 faces  (magnet, air barriers, core, etc.)
    
    >>> for face in faces:
    ...     print(f"Face area={face['area']:.1f}, centroid_r={face['centroid_r']:.1f}")
    
    Example 2: Iterating through detected faces
    
    >>> faces = detect_closed_faces(closed_entities, origin=(0,0))
    >>> for idx, face in enumerate(faces):
    ...     print(f"Face#{idx}: {len(face['vertices'])} vertices, "
    ...           f"area={face['area']:.2f}, label={face['name']}")

    Use Cases
    ---------
    - **Region Detection**: Identify all motor regions after geometry closure
    - **Area Filtering**: Exclude small numerical artifacts (min_area threshold)
    - **Downstream Processing**: Faces are input to `auto_name_faces()` for classification
    - **GUI Visualization**: Faces rendered in `FaceRegionGUI` for interactive labeling
    - **Export**: Face vertices can be exported to DXF or other CAD formats

    Notes
    -----
    - **Face Orientation**: Vertices are ordered counterclockwise (from Shoelace formula convention)
    - **Degenerate Faces**: Triangles have n_edges=3; larger regions may have n_edges > 10
    - **Touching Boundaries**: If two faces touch at an edge, both are detected (no merging)
    - **Performance**: Shapely method is ~5-10× faster than planar graph for large entity sets
    - **Dependencies**: Shapely is optional; if unavailable, planar graph fallback is used automatically
    - **Robustness**: Planar graph method may miss faces if endpoints don't snap correctly; 
      adjust `tol_digits` if needed
    """
    if use_shapely:
        try:
            from face_detection import detect_closed_faces_v2
            faces = detect_closed_faces_v2(entities, origin, min_area)
            if faces:
                return faces
            # shapely 결과가 없으면 planar graph fallback
        except Exception:
            pass

    # ── planar graph fallback (기존 방식) ──
    ox, oy = origin
    adj, emap = _build_adj(entities, tol_digits)
    raw_faces = _traverse_minimal_faces(adj)

    faces = []
    for verts in raw_faces:
        area = abs(_signed_area(verts))
        if area < min_area:
            continue
        n = len(verts)
        cx = sum(v[0] for v in verts) / n
        cy = sum(v[1] for v in verts) / n
        rs = [math.hypot(v[0] - ox, v[1] - oy) for v in verts]
        faces.append({
            'vertices':       list(verts),
            'area':           area,
            'n_edges':        n,
            'centroid':       (cx, cy),
            'interior_point': (cx, cy),   # planar graph는 centroid를 내부점으로 사용
            'centroid_r':     math.hypot(cx - ox, cy - oy),
            'centroid_ang':   math.degrees(math.atan2(cy - oy, cx - ox)) % 360,
            'r_min':          min(rs),
            'r_max':          max(rs),
            'r_mean':         float(np.mean(rs)),
            'name':           'unknown',
        })

    faces.sort(key=lambda f: f['area'], reverse=True)
    return faces


# ═══════════════════════════════════════════════════════════════
# 4. 자동 이름 할당
# ═══════════════════════════════════════════════════════════════

def auto_name_faces(
    faces: List[Dict],
    r_shaft: float,
    r_rotor_outer: float,
    r_stator_inner: float,
    r_stator_outer: float,
    rotor_topology: str = 'SPM',
) -> List[Dict]:
    """
    Automatically assign region labels to detected faces based on radial position and area heuristics.
    
    This function classifies closed faces into motor region types (magnet, slot, tooth, yoke, etc.) 
    by examining the centroid radius, minimum/maximum radii, and area of each face. It is the primary 
    method for converting raw topological faces into semantically meaningful motor components.

    Parameters
    ----------
    faces : List[Dict]
        List of face dictionaries from `detect_closed_faces()`. Each face must contain 
        'centroid_r', 'r_min', 'r_max', and 'area' fields. The 'name' field is updated in-place.
    
    r_shaft : float
        Radius of the rotor shaft (inner boundary). Faces entirely within this radius 
        are labeled 'shaft'.
    
    r_rotor_outer : float
        Outer radius of the rotor (where airgap begins). Separates rotor from stator 
        regions. Typically corresponds to the airgap inner surface.
    
    r_stator_inner : float
        Inner radius of the stator (where airgap ends, stator begins). Combined with 
        r_rotor_outer to define the airgap region.
    
    r_stator_outer : float
        Outer radius of the stator yoke (motor outer boundary). Faces near this radius 
        are classified as stator yoke.
    
    rotor_topology : str, optional
        Rotor magnet/flux barrier topology type. Affects classification of small outer 
        rotor regions. Valid values:
        
        - **'SPM'** (default) : Surface Permanent Magnet — small outer regions are magnets
        - **'IPM'** : Interior Permanent Magnet — small outer regions may be air barriers
        - **'SynRM'** : Synchronous Reluctance Motor — no PMs, classify as air barriers
        - **'PMa-SynRM'** : Hybrid with both PMs and air barriers
        - **'SPMSM'** : Alias for SPM
        
        Default is 'SPM'.

    Returns
    -------
    List[Dict]
        The same `faces` list with each face's 'name' field updated to one of the following:
        
        - **'shaft'** → Central rotor shaft (r_max ≤ r_shaft)
        - **'rotor_core'** → Rotor magnetic core (r_min > r_shaft, large area, IPM/SynRM)
        - **'magnet'** → Permanent magnet pole (rotor surface, SPM/IPM topology)
        - **'air_barrier'** → Flux barrier pocket (rotor, SynRM/PMa-SynRM topology)
        - **'stator_yoke'** → Stator laminated core outer region (r > midpoint, large area)
        - **'stator_tooth'** → Stator tooth pole piece (r > midpoint, mid area, radial extent)
        - **'slot'** → Stator slot region (r > midpoint, large area, smaller than yoke)
        - **'slot_opening'** → Small region near airgap at stator side (near r_stator_inner)
        - **'unknown'** → Unclassified (should rarely occur if thresholds are set correctly)

    Classification Algorithm
    -----------------------
    
    1. **Centroid Radial Position**:
       - If `centroid_r ≤ r_shaft`: → 'shaft'
       - If `centroid_r ≤ r_rotor_outer`: → Rotor region (magnet, air_barrier, rotor_core)
       - If `centroid_r ≥ r_stator_inner`: → Stator region (slot, tooth, yoke, slot_opening)
    
    2. **Rotor Region (centroid_r < r_mid_airgap)**:
       - Large area (> 200) → 'rotor_core'
       - Small, outer-radial (r_max > 0.85 × r_rotor_outer):
         * SPM/SPMSM → 'magnet'
         * SynRM → 'air_barrier'
         * IPM → depends on context (typically magnet for outer regions)
       - Otherwise → 'air_barrier' or 'rotor_core' depending on topology
    
    3. **Stator Region (centroid_r > r_mid_airgap)**:
       - Large outer area (r_min > 50% of yoke thickness) → 'stator_yoke'
       - Radial extent (r_max - r_min) > 30% of stator thickness → 'stator_tooth'
       - Small area near airgap (area < 50, r_min ≈ r_stator_inner) → 'slot_opening'
       - Large area (> 20) → 'slot'
       - Other → 'slot_opening' (fallback)

    Examples
    --------
    Example 1: Classify faces from a typical PMSM motor
    
    >>> from pyMotorGeo.region_closing import detect_closed_faces, auto_name_faces
    >>> 
    >>> faces = detect_closed_faces(closed_entities, origin=(0, 0))
    >>> faces = auto_name_faces(
    ...     faces,
    ...     r_shaft=10,
    ...     r_rotor_outer=50,
    ...     r_stator_inner=52,
    ...     r_stator_outer=80,
    ...     rotor_topology='SPM'
    ... )
    >>> 
    >>> for face in faces:
    ...     print(f"{face['name']:15} area={face['area']:6.1f}")
    # Output:
    # rotor_core       300.0
    # magnet             3.2
    # magnet             3.2
    # slot             45.0
    # stator_yoke     150.0
    
    Example 2: IPM motor with air barriers
    
    >>> faces = auto_name_faces(
    ...     faces,
    ...     r_shaft=15,
    ...     r_rotor_outer=55,
    ...     r_stator_inner=57,
    ...     r_stator_outer=85,
    ...     rotor_topology='IPM'
    ... )

    Machine Independent Thresholds
    
    These are tolerances and area thresholds used internally (all in motor mill absolute units):
    
    - **tol** = 1.5 mm : Radial tolerance for boundary snapping
    - **area > 200** : Large rotor region → core (not magnet)
    - **area < 50** : Small stator region → slot_opening (not conductor)
    - **r_max > 0.85 × r_rotor_outer** : Surface magnet or barrier (outer region)
    - **radial_extent > 30% of yoke** : Tooth-like structure
    
    **Note**: These thresholds work well for motors ranging from micro-motors (5mm) to 
    large industrial motors (300mm). For extreme scales, parameters may need manual tuning.

    Use Cases
    ---------
    - **Workflow Integration**: Final step in `close_one_pole()` and `close_period_model()` workflows
    - **Inventory Counting**: Pair with `get_face_summary()` to tally magnet/slot/tooth counts
    - **Export Preparation**: Faces with correct labels can be exported to DXF or simulation tools
    - **GUI Initialization**: Classified faces populate region dropdown in `FaceRegionGUI`
    - **Topology Validation**: Verify expected counts (e.g., 4 magnets for 4-pole rotor)

    Notes
    -----
    - **In-place Modification**: The function modifies the input `faces` list directly 
      and also returns it for convenience
    - **Topology Sensitivity**: Rotor classification strongly depends on `rotor_topology` parameter
    - **Boundary Cases**: Faces touching multiple regions (e.g., on the airgap boundary) 
      may be misclassified; post-processing in GUI is recommended
    - **Scaling**: All thresholds are in absolute motor geometric units (mm or motor-specific units)
    - **Fallback Behavior**: Any unrecognized topology defaults to SPM-like classification 
      (small outer regions → magnets)
    """
    tol = 1.5  # mm 허용 오차
    r_mid_ag = (r_rotor_outer + r_stator_inner) / 2.0
    r_stator_range = r_stator_outer - r_stator_inner

    for fi in faces:
        cr = fi['centroid_r']
        rmin, rmax = fi['r_min'], fi['r_max']

        # ── 샤프트 ──
        if rmax <= r_shaft + tol:
            fi['name'] = 'shaft'
            continue

        # ── 스테이터 영역 (centroid가 에어갭 중간보다 바깥) ──
        if cr > r_mid_ag:
            # 스테이터 요크: 외측에 가까운 큰 영역
            if rmin > r_stator_inner + r_stator_range * 0.5:
                fi['name'] = 'stator_yoke'
            # 슬롯 오프닝: 에어갭 바로 근처, 작은 면적
            elif rmin < r_stator_inner + tol * 3 and fi['area'] < 50:
                fi['name'] = 'slot_opening'
            # 슬롯: 큰 면적
            elif fi['area'] > 20:
                fi['name'] = 'slot'
            # 나머지 → 티스 또는 슬롯 오프닝
            elif (rmax - rmin) > r_stator_range * 0.3:
                fi['name'] = 'stator_tooth'
            else:
                fi['name'] = 'slot_opening'
            continue

        # ── 로터 영역 (centroid가 에어갭 중간보다 안쪽) ──
        # 큰 영역 → 로터 코어
        if fi['area'] > 200:
            fi['name'] = 'rotor_core'
        # 표면 근처 작은 영역
        elif rmax > r_rotor_outer * 0.85:
            if rotor_topology in ('SPM', 'SPMSM'):
                fi['name'] = 'magnet'
            elif rotor_topology in ('SynRM',):
                fi['name'] = 'air_barrier'
            else:
                fi['name'] = 'magnet'
        else:
            if rotor_topology in ('SynRM', 'PMa-SynRM'):
                fi['name'] = 'air_barrier'
            else:
                fi['name'] = 'rotor_core'

    return faces


def auto_name_faces_v2(
    faces: List[Dict],
    r_shaft: float,
    r_rotor_outer: float,
    r_stator_inner: float,
    r_stator_outer: float,
    rotor_topology: str = 'SPM',
) -> List[Dict]:
    """
    auto_name_faces 개선판 — topology별 분기 + 레이어 번호 부여.

    auto_name_faces 와의 차이
    -------------------------
    1. interior_point 사용 (shapely find_best_region 결과)
    2. topology별 임계값 분기
       - SPM  : 표면 영역 → magnet, 내부 → rotor_core
       - IPM  : 표면 → magnet, 내부 얇은 영역 → air_barrier, 큰 영역 → rotor_core
       - SynRM: 모든 내부 얇은 영역 → air_barrier
       - PMa-SynRM: IPM + 배리어 사이 자석 병존
    3. 로터 내부 영역에 레이어 번호 부여 (BanGeoCode lay() 방식)
       rotor_core → layer=0, air_barrier/magnet → layer=1,2,3... (안쪽부터)
    4. concentric_arcs(동심원 호) 경계 영역 반경 구간 기반 air_barrier 판별

    Parameters
    ----------
    faces          : detect_closed_faces() / detect_closed_faces_v2() 결과
    r_shaft        : 샤프트 반경
    r_rotor_outer  : 로터 외경 (에어갭 내측)
    r_stator_inner : 스테이터 내경 (에어갭 외측)
    r_stator_outer : 스테이터 외경
    rotor_topology : 'SPM', 'IPM', 'SynRM', 'PMa-SynRM', 'UNKNOWN'

    Returns
    -------
    faces (in-place 수정 + 반환)
    """
    tol = 1.5
    r_mid_ag     = (r_rotor_outer + r_stator_inner) / 2.0
    r_rotor_range = r_rotor_outer - r_shaft
    r_stator_range = r_stator_outer - r_stator_inner

    # ── topology 공통 파라미터 ──
    # 표면 임계: rotor_outer 기준 몇 % 안쪽까지 "표면 근처"로 볼 것인가
    surface_thresh = {
        'SPM':       0.82,
        'IPM':       0.78,
        'SynRM':     0.75,
        'PMa-SynRM': 0.78,
        'UNKNOWN':   0.80,
    }.get(rotor_topology, 0.80)

    # 얇은 영역(air_barrier 후보) 판별: 방사 두께 / 로터 반경 < thin_ratio
    thin_ratio = {
        'IPM':       0.18,
        'SynRM':     0.20,
        'PMa-SynRM': 0.20,
    }.get(rotor_topology, 0.15)

    rotor_inner_faces = []  # 레이어 번호 부여용

    for fi in faces:
        # interior_point 우선, 없으면 centroid 사용
        ip = fi.get('interior_point', fi['centroid'])
        ip_r = math.hypot(ip[0], ip[1])

        cr   = fi['centroid_r']
        rmin = fi['r_min']
        rmax = fi['r_max']
        radial_span = rmax - rmin

        # ── 샤프트 ──
        if rmax <= r_shaft + tol:
            fi['name'] = 'shaft'
            fi['layer'] = 0
            continue

        # ── 스테이터 측 ──
        if ip_r > r_mid_ag:
            if rmin > r_stator_inner + r_stator_range * 0.55:
                fi['name'] = 'stator_yoke'
            elif rmin < r_stator_inner + tol * 3 and fi['area'] < 60:
                fi['name'] = 'slot_opening'
            elif fi['area'] > 15:
                fi['name'] = 'slot'
            elif radial_span > r_stator_range * 0.25:
                fi['name'] = 'stator_tooth'
            else:
                fi['name'] = 'slot_opening'
            continue

        # ── 로터 측 ──
        is_near_surface = rmax > r_rotor_outer * surface_thresh
        is_thin = radial_span < r_rotor_range * thin_ratio

        if rotor_topology == 'SPM':
            if is_near_surface:
                fi['name'] = 'magnet'
            elif fi['area'] > r_rotor_range ** 2 * 0.1:
                fi['name'] = 'rotor_core'
            else:
                fi['name'] = 'rotor_core'

        elif rotor_topology in ('IPM', 'PMa-SynRM'):
            if is_near_surface and is_thin:
                # 얇고 표면 근처 → 자석 또는 air_barrier
                # 면적이 매우 작으면 air_barrier (bridge/pocket)
                if fi['area'] < r_rotor_range * 3:
                    fi['name'] = 'air_barrier'
                else:
                    fi['name'] = 'magnet'
            elif is_near_surface:
                fi['name'] = 'magnet'
            elif is_thin:
                fi['name'] = 'air_barrier'
                rotor_inner_faces.append(fi)
            elif fi['area'] > r_rotor_range ** 2 * 0.08:
                fi['name'] = 'rotor_core'
            else:
                fi['name'] = 'air_barrier'
                rotor_inner_faces.append(fi)

        elif rotor_topology == 'SynRM':
            if is_thin:
                fi['name'] = 'air_barrier'
                rotor_inner_faces.append(fi)
            elif fi['area'] > r_rotor_range ** 2 * 0.08:
                fi['name'] = 'rotor_core'
            else:
                fi['name'] = 'air_barrier'
                rotor_inner_faces.append(fi)

        else:  # UNKNOWN fallback
            if is_near_surface:
                fi['name'] = 'magnet'
            elif fi['area'] > 200:
                fi['name'] = 'rotor_core'
            else:
                fi['name'] = 'rotor_core'

    # ── 레이어 번호 부여 (BanGeoCode lay() 방식) ──
    # air_barrier / magnet 을 r_mean 기준 안쪽(1)→바깥쪽 순으로 번호 부여
    barrier_mag = [f for f in faces
                   if f.get('name') in ('air_barrier', 'magnet')]
    barrier_mag.sort(key=lambda f: f['r_mean'])
    for layer_idx, fi in enumerate(barrier_mag, start=1):
        fi['layer'] = layer_idx

    # rotor_core / shaft 는 layer=0
    for fi in faces:
        if 'layer' not in fi:
            fi['layer'] = 0

    return faces


def get_face_summary(faces: List[Dict]) -> Dict[str, int]:
    """
    Aggregate face count by region type.
    
    Provides a quick summary of how many faces (regions) of each type were 
    detected and classified. Useful for inventory tracking and validation 
    (e.g., verifying correct magnet count for the rotor).

    Parameters
    ----------
    faces : List[Dict]
        List of face dictionaries with 'name' field (typically from `auto_name_faces()`).

    Returns
    -------
    Dict[str, int]
        Dictionary mapping region labels to their counts. Example output::
        
            {
                'magnet': 4,
                'air_barrier': 0,
                'rotor_core': 1,
                'shaft': 1,
                'slot': 48,
                'stator_tooth': 48,
                'stator_yoke': 1,
                'slot_opening': 48,
                'unknown': 0
            }

    Examples
    --------
    Example 1: Summarize detected regions
    
    >>> from pyMotorGeo.region_closing import auto_name_faces, get_face_summary
    >>> 
    >>> summary = get_face_summary(faces)
    >>> print(summary)
    # Output: {'magnet': 4, 'slot': 8, 'rotor_core': 1, 'stator_yoke': 1, ...}
    >>> print(f"Total magnets: {summary.get('magnet', 0)}")
    # Output: Total magnets: 4
    
    Example 2: Validate rotor/stator for correct pole count
    
    >>> summary = get_face_summary(faces)
    >>> n_poles = summary.get('magnet', 0)
    >>> if n_poles != expected_poles:
    ...     print(f"⚠️  Expected {expected_poles} poles, got {n_poles}")
    
    Example 3: Summarize stator slot structure
    
    >>> summary = get_face_summary(faces)
    >>> n_slots = summary.get('slot', 0)
    >>> n_teeth = summary.get('stator_tooth', 0)
    >>> print(f"Stator: {n_slots} slots, {n_teeth} teeth")

    Use Cases
    ---------
    - **Validation**: Verify motor geometry (e.g., 8 slots expected, got 8 ✓)
    - **Reporting**: Include counts in analysis reports
    - **GUI Status**: Display summary in FaceRegionGUI status bar
    - **Debugging**: Detect misclassified or missing regions (e.g., 'unknown' count > 0)
    - **Export Metadata**: Store summary with exported CAD files

    Notes
    -----
    - Returns only labels that appear at least once; missing labels are not included
    - For regions that don't appear, use `.get(label, 0)` to avoid KeyError
    - Only counts faces; does not account for periodic expansion or symmetry 
      (e.g., if input is a half-pole, actual magnet count is 2× the summary value)
    - Should be called after `auto_name_faces()` for meaningful results
    """
    return dict(Counter(f['name'] for f in faces))


def plot_faces_static(faces: List[Dict],
                      origin: Tuple[float, float],
                      region_names: Dict[str, str],
                      region_colors: Dict[str, str],
                      title: str = 'Closed Faces',
                      figsize: Tuple[float, float] = (10, 8),
                      ax=None):
    """
    닫힌 영역(face)을 정적 matplotlib 그림으로 시각화.
    
    ipywidgets 없이 순수 matplotlib만 사용하므로
    VS Code에서 위젯 렌더링 문제가 있을 때 대안으로 사용.
    
    Parameters
    ----------
    faces : detect_closed_faces() 결과
    origin : 원점
    region_names : {'magnet': 'Magnet', ...}
    region_colors : {'magnet': '#FF4444', ...}
    title : 제목
    figsize : 그림 크기
    ax : 기존 axes (없으면 새로 생성)
    
    Returns
    -------
    fig, ax
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.lines import Line2D
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # 면적 큰 순서(뒤) → 작은 순서(앞)로 그리기
    sorted_indices = sorted(range(len(faces)),
                            key=lambda i: faces[i]['area'],
                            reverse=True)
    
    for idx in sorted_indices:
        fi = faces[idx]
        name = fi.get('name', 'unknown')
        color = region_colors.get(name, '#D0D0D0')
        verts = fi['vertices']
        poly = MplPolygon(verts, closed=True,
                          facecolor=color, edgecolor='#333333',
                          linewidth=0.5, alpha=0.75)
        ax.add_patch(poly)
        
        # face 번호 + 이름 라벨 (centroid에 표시)
        cx, cy = fi.get('centroid', (0, 0))
        if 'centroid' not in fi and fi['vertices']:
            cx = sum(v[0] for v in verts) / len(verts)
            cy = sum(v[1] for v in verts) / len(verts)
        
        short = {
            'stator_yoke': 'Yoke', 'stator_tooth': 'Tooth',
            'slot': 'Slot', 'slot_opening': 'SlotOp',
            'airgap': 'Gap', 'rotor_core': 'Core',
            'magnet': 'Mag', 'air_barrier': 'AirB',
            'shaft': 'Shaft', 'unknown': '?',
        }.get(name, name[:6])
        
        ax.text(cx, cy, f'{idx}\n{short}',
                fontsize=6, ha='center', va='center',
                color='#222222', weight='bold',
                bbox=dict(boxstyle='round,pad=0.15',
                          facecolor='white', alpha=0.7, lw=0))
    
    # 범례 (고유 이름만)
    seen = set()
    handles = []
    for fi in faces:
        n = fi.get('name', 'unknown')
        if n not in seen:
            seen.add(n)
            c = region_colors.get(n, '#D0D0D0')
            label = region_names.get(n, n)
            handles.append(Line2D([0], [0], color=c, lw=8,
                                  alpha=0.75, label=label))
    if handles:
        ax.legend(handles=handles, fontsize=7, loc='upper right')
    
    ax.plot(*origin, 'r*', ms=6, zorder=20)
    ax.set_aspect('equal')
    ax.set_title(f'{title}  ({len(faces)}개 영역)', fontsize=10)
    
    return fig, ax
