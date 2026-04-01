"""
pyMotorGeo.face_detection
=========================

Shapely-based topological face (closed region) detection and interior point computation.

This module implements robust face detection using shapely's geometric algorithms, with 
special handling for finding guaranteed interior points for downstream region classification. 
Logic is adapted from BanGeoCode (MATLAB) for reliability and proven robustness.

**Background**:

Face detection requires two key challenges to be solved:

1. **Topological Face Identification**: Given a network of entity edges (lines, arcs), 
   identify all minimal closed cycles (faces) forming the boundaries of motor regions
   
2. **Interior Point Computation**: For each face, find a point *guaranteed* to be inside 
   the polygon, useful for point-in-polygon tests and region containment checks

**Algorithm Sources**:

- Shapely `polygonize()`: Converts edge networks to polygons using planar graph algebra
- BanGeoCode `find_best_region()`: Robust interior point detection via grid-crossing analysis
- BanGeoCode `check_feasibility()`: Polygon validation (non-degenerate, non-self-intersecting)

**Key Functions**:

- `entity_to_linestring()`: Convert pyMotorGeo EntityInfo to shapely LineString
- `entities_to_polygons()`: Use shapely.ops.polygonize to find all faces
- `find_interior_point()`: Compute guaranteed interior point via grid/centroid/recursion
- `check_polygon_feasibility()`: Validate polygon (overlap, self-intersection, topology)
- `detect_closed_faces_v2()`: Complete face detection pipeline (modern alternative to region_closing)

**Advantages Over Planar Graph Method**:

- Handles CoLinear edges and edge overlaps more robustly
- Shapely uses highly optimized C++ backends (GEOS)
- Fewer numerical precision issues
- Better support for complex geometries (spirals, curved boundaries)

**Fallback Behavior**:

If shapely is unavailable or fails, `region_closing.detect_closed_faces()` falls back to 
planar graph method, ensuring robustness across environments.

**Integration**:

Called by `region_closing.detect_closed_faces()` with `use_shapely=True` (default).
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional

from shapely.geometry import LineString, Point, MultiPolygon, Polygon, box
from shapely.ops import polygonize, unary_union, split
from shapely.validation import make_valid

from core import EntityInfo


# ═══════════════════════════════════════════════════════════════
# 1. EntityInfo → shapely LineString 변환
# ═══════════════════════════════════════════════════════════════

def entity_to_linestring(ei: EntityInfo,
                         arc_n_pts: int = 32) -> Optional[LineString]:
    """
    EntityInfo 하나를 shapely LineString으로 변환.

    ARC/CIRCLE은 arc_n_pts 점으로 근사합니다.
    점이 2개 미만이면 None 반환.
    """
    pts = ei.points
    if not pts or len(pts) < 2:
        return None
    try:
        ls = LineString(pts)
        if ls.is_empty or ls.length < 1e-9:
            return None
        return ls
    except Exception:
        return None


def entities_to_linestrings(entities: List[EntityInfo],
                             arc_n_pts: int = 32) -> List[LineString]:
    """EntityInfo 리스트 → 유효한 LineString 리스트."""
    result = []
    for ei in entities:
        ls = entity_to_linestring(ei, arc_n_pts)
        if ls is not None:
            result.append(ls)
    return result


# ═══════════════════════════════════════════════════════════════
# 2. shapely polygonize → Polygon 리스트
# ═══════════════════════════════════════════════════════════════

def entities_to_polygons(entities: List[EntityInfo],
                          origin: Tuple[float, float] = (0.0, 0.0),
                          min_area: float = 1.0,
                          arc_n_pts: int = 32) -> List[Polygon]:
    """
    BanGeoCode polyshape(X, Y) 방식의 Python 대응.

    EntityInfo → LineString → shapely.ops.polygonize → Polygon 리스트.

    Parameters
    ----------
    entities  : EntityInfo 리스트 (경계선 포함)
    origin    : 원점 (미사용, 호환성 유지)
    min_area  : 최소 면적 필터 (mm²)
    arc_n_pts : ARC 근사 점 수

    Returns
    -------
    List[Polygon]  — 면적 내림차순 정렬
    """
    linestrings = entities_to_linestrings(entities, arc_n_pts)
    if not linestrings:
        return []

    # 교차점에서 정확히 분할되도록 node (unary_union + individual extraction)
    merged = unary_union(linestrings)
    polys = list(polygonize(merged))

    # 유효성 보정 + 면적 필터
    result = []
    for p in polys:
        p = make_valid(p)
        if p.is_empty:
            continue
        # MultiPolygon이면 개별 Polygon으로 분해
        if isinstance(p, MultiPolygon):
            for sub in p.geoms:
                if sub.area >= min_area:
                    result.append(sub)
        else:
            if p.area >= min_area:
                result.append(p)

    result.sort(key=lambda p: p.area, reverse=True)
    return result


# ═══════════════════════════════════════════════════════════════
# 3. BanGeoCode find_best_region() 완전 이식
# ═══════════════════════════════════════════════════════════════

def find_interior_point(polygon: Polygon,
                        n_grid: int = 4,
                        _depth: int = 0,
                        _max_depth: int = 6) -> Tuple[float, float]:
    """
    BanGeoCode Shape.m find_best_region() 완전 이식.

    MATLAB 로직 대응
    ----------------
    1. bbox 계산 → 정사각 그리드(max(A,B) 기준) 생성
    2. N×N 셀 × polygon 교차 → max 면적 셀 선택
    3. 해당 셀에서 가장 큰 sub-polygon 추출
       (MATLAB: sortregions + regions → R2(1))
    4. centroid 계산
    5. isinterior(final, x, y) 검증
       - 실패 시: find_best_region(final, ...) 재귀 호출
    6. 재귀 한도 초과 시 representative_point() fallback

    Parameters
    ----------
    polygon   : 내부점을 찾을 Polygon
    n_grid    : 그리드 분할 수 (MATLAB N=4)
    _depth    : 현재 재귀 깊이 (내부용)
    _max_depth: 최대 재귀 깊이 (무한 재귀 방지)

    Returns
    -------
    (x, y) — polygon 내부에 있는 대표점
    """
    # 재귀 한도 초과 → shapely representative_point() fallback
    if _depth >= _max_depth or polygon.is_empty:
        rp = polygon.representative_point()
        return rp.x, rp.y

    # ── 1. Bounding box + 정사각 그리드 ──
    minx, miny, maxx, maxy = polygon.bounds
    A = maxx - minx
    B = maxy - miny

    # MATLAB: if A>B → x 방향 기준, else y 방향 기준 (정사각형)
    if A >= B:
        lim_x = (minx, maxx)
        lim_y = (miny, miny + A)
    else:
        lim_x = (minx, minx + B)
        lim_y = (miny, maxy)

    grid_x = np.linspace(lim_x[0], lim_x[1], n_grid + 1)
    grid_y = np.linspace(lim_y[0], lim_y[1], n_grid + 1)

    # ── 2. N×N 셀 생성 + intersection 면적 계산 ──
    best_area = -1.0
    best_inter = None

    for i in range(n_grid):
        for j in range(n_grid):
            cell = box(grid_x[i], grid_y[j], grid_x[i + 1], grid_y[j + 1])
            inter = cell.intersection(polygon)
            if inter.is_empty:
                continue
            a = inter.area
            if a > best_area:
                best_area = a
                best_inter = inter

    if best_inter is None or best_inter.is_empty:
        rp = polygon.representative_point()
        return rp.x, rp.y

    # ── 3. 가장 큰 sub-polygon 추출 (MATLAB sortregions + regions(R1)(1)) ──
    if isinstance(best_inter, MultiPolygon):
        final = max(best_inter.geoms, key=lambda g: g.area)
    else:
        final = best_inter

    final = make_valid(final)
    if final.is_empty:
        rp = polygon.representative_point()
        return rp.x, rp.y

    # ── 4. centroid ──
    cx, cy = final.centroid.x, final.centroid.y

    # ── 5. isinterior 검증 (MATLAB isinterior) ──
    if final.contains(Point(cx, cy)):
        return cx, cy

    # ── 5-fail. 재귀 (MATLAB: find_best_region(final, name, enable)) ──
    return find_interior_point(final, n_grid, _depth + 1, _max_depth)


# ═══════════════════════════════════════════════════════════════
# 4. BanGeoCode check_feasibility.m 이식
# ═══════════════════════════════════════════════════════════════

def check_polygon_feasibility(polygons: List[Polygon],
                               symmetry_angle_deg: Optional[float] = None,
                               buffer_dist: float = 0.0) -> Dict:
    """
    BanGeoCode check_feasibility.m 이식.

    MATLAB 로직 대응
    ----------------
    flag1 : overlaps(polyvec) == eye  →  쌍별 겹침 없음
    flag2 : all(NumRegions < 2)       →  모든 polygon이 단일 connected region
    flag3 : 대칭선(0°~symmetry_angle) 내에 모든 꼭짓점 존재
    flag5 : buffer 확장 후 겹침 없음  (DstChk)

    Parameters
    ----------
    polygons          : Polygon 리스트
    symmetry_angle_deg: 대칭 반피치 각도 (deg). None이면 검사 생략
    buffer_dist       : 최소 이격 거리 검사용 buffer (MATLAB: Epoxy 0.25 mm)

    Returns
    -------
    dict
        feasible       : bool — 전체 통과 여부
        flag_overlap   : bool — 겹침 없음
        flag_single    : bool — 단일 connected region
        flag_symmetry  : bool — 대칭선 내 존재
        flag_buffer    : bool — 최소 이격 통과
        overlapping_pairs : List[Tuple[int,int]] — 겹치는 인덱스 쌍
        invalid_indices   : List[int] — 다중 region polygon 인덱스
        out_of_sector_idx : List[int] — 대칭선 위반 인덱스
    """
    n = len(polygons)
    overlapping_pairs = []
    invalid_indices   = []
    out_of_sector_idx = []

    # ── flag2: NumRegions 검사 (MATLAB polyvec(i).NumRegions) ──
    # shapely: is_valid + 단순 연결 여부
    for i, p in enumerate(polygons):
        if not p.is_valid or isinstance(make_valid(p), MultiPolygon):
            invalid_indices.append(i)

    flag2 = len(invalid_indices) == 0

    # ── flag1: 쌍별 겹침 (MATLAB overlaps(polyvec)) ──
    for i in range(n):
        for j in range(i + 1, n):
            if polygons[i].overlaps(polygons[j]):
                overlapping_pairs.append((i, j))

    flag1 = len(overlapping_pairs) == 0

    # ── flag3: 대칭선 범위 내 꼭짓점 (MATLAB beta > angle+eps || beta < 0) ──
    flag3 = True
    if symmetry_angle_deg is not None:
        sym_rad = math.radians(symmetry_angle_deg)
        for i, p in enumerate(polygons):
            coords = list(p.exterior.coords)
            for x, y in coords:
                beta = math.atan2(y, x)  # -π ~ π
                # MATLAB: if any(beta > angle+eps) || any(beta < 0)
                if beta > sym_rad + 1e-9 or beta < -1e-9:
                    out_of_sector_idx.append(i)
                    break
        flag3 = len(out_of_sector_idx) == 0

    # ── flag5: buffer 거리 검사 (MATLAB polybuffer + overlaps) ──
    flag5 = True
    if buffer_dist > 0 and n > 1:
        buffered = [p.buffer(buffer_dist) for p in polygons]
        buf_overlaps = []
        for i in range(n):
            for j in range(i + 1, n):
                if buffered[i].overlaps(buffered[j]):
                    buf_overlaps.append((i, j))
        flag5 = len(buf_overlaps) == 0

    feasible = flag1 and flag2 and flag3 and flag5

    return {
        'feasible':           feasible,
        'flag_overlap':       flag1,
        'flag_single_region': flag2,
        'flag_symmetry':      flag3,
        'flag_buffer':        flag5,
        'overlapping_pairs':  overlapping_pairs,
        'invalid_indices':    invalid_indices,
        'out_of_sector_idx':  out_of_sector_idx,
    }


# ═══════════════════════════════════════════════════════════════
# 5. detect_closed_faces_v2 — shapely 기반 face 탐지
# ═══════════════════════════════════════════════════════════════

def detect_closed_faces_v2(
    entities: List[EntityInfo],
    origin: Tuple[float, float] = (0.0, 0.0),
    min_area: float = 1.0,
    arc_n_pts: int = 32,
    n_grid: int = 4,
) -> List[Dict]:
    """
    shapely polygonize 기반 닫힌 face 탐지. (region_closing.detect_closed_faces 개선판)

    region_closing.detect_closed_faces 와의 차이
    --------------------------------------------
    기존 : planar graph 순회 → 직선 엣지만, endpoint 정밀도 의존성 높음
    신규 : shapely polygonize → ARC 곡선 지원, 위상 견고성 향상

    각 face 에 find_interior_point() 로 내부 대표점 계산
    (BanGeoCode: region_point = find_best_region(poly, ...))

    Parameters
    ----------
    entities  : EntityInfo 리스트 (close_one_pole/slot 결과)
    origin    : 회전 원점
    min_area  : 최소 면적 필터 (mm²)
    arc_n_pts : ARC 근사 점 수
    n_grid    : find_interior_point 그리드 분할 수 (MATLAB N=4)

    Returns
    -------
    List[Dict]  — 각 face:
        vertices        : List[(x,y)]  외곽선 좌표 (Polygon.exterior)
        area            : float        면적 (mm²)
        n_edges         : int          꼭짓점 수
        centroid        : (cx, cy)     도심
        interior_point  : (ix, iy)     내부 대표점 (find_best_region 결과)
        centroid_r      : float        도심 반경
        centroid_ang    : float        도심 각도 (deg)
        r_min           : float        최소 반경
        r_max           : float        최대 반경
        r_mean          : float        평균 반경
        name            : str          영역 이름 (초기값 'unknown')
        polygon         : Polygon      shapely 객체 (후처리용)
    """
    ox, oy = origin

    polygons = entities_to_polygons(entities, origin, min_area, arc_n_pts)
    if not polygons:
        return []

    faces = []
    for poly in polygons:
        # exterior 좌표
        verts = list(poly.exterior.coords)

        # 반경 계산
        rs = [math.hypot(x - ox, y - oy) for x, y in verts]

        # centroid
        c = poly.centroid
        cx, cy = c.x, c.y

        # interior_point (BanGeoCode find_best_region)
        ix, iy = find_interior_point(poly, n_grid=n_grid)

        faces.append({
            'vertices':       verts,
            'area':           poly.area,
            'n_edges':        len(verts) - 1,   # 마지막 점 = 첫 점
            'centroid':       (cx, cy),
            'interior_point': (ix, iy),
            'centroid_r':     math.hypot(cx - ox, cy - oy),
            'centroid_ang':   math.degrees(math.atan2(cy - oy, cx - ox)) % 360,
            'r_min':          min(rs),
            'r_max':          max(rs),
            'r_mean':         float(np.mean(rs)),
            'name':           'unknown',
            'polygon':        poly,
        })

    faces.sort(key=lambda f: f['area'], reverse=True)
    return faces


# ═══════════════════════════════════════════════════════════════
# 6. 편의 함수
# ═══════════════════════════════════════════════════════════════

def polygon_to_face_dict(poly: Polygon,
                         origin: Tuple[float, float] = (0.0, 0.0),
                         n_grid: int = 4) -> Dict:
    """
    단일 Polygon → face dict 변환 (detect_closed_faces_v2 내부 로직 노출).
    외부에서 Polygon 객체를 직접 갖고 있을 때 사용.
    """
    ox, oy = origin
    verts = list(poly.exterior.coords)
    rs = [math.hypot(x - ox, y - oy) for x, y in verts]
    c = poly.centroid
    ix, iy = find_interior_point(poly, n_grid=n_grid)
    return {
        'vertices':       verts,
        'area':           poly.area,
        'n_edges':        len(verts) - 1,
        'centroid':       (c.x, c.y),
        'interior_point': (ix, iy),
        'centroid_r':     math.hypot(c.x - ox, c.y - oy),
        'centroid_ang':   math.degrees(math.atan2(c.y - oy, c.x - ox)) % 360,
        'r_min':          min(rs),
        'r_max':          max(rs),
        'r_mean':         float(np.mean(rs)),
        'name':           'unknown',
        'polygon':        poly,
    }
