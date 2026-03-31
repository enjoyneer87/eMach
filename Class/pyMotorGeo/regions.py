"""
pyMotorGeo.regions
==================
Planar graph 기반 닫힌 영역 탐지 및 영역 자동 네이밍.
"""

import math
import numpy as np
from collections import defaultdict
from typing import List, Tuple, Dict, Optional

from core import EntityInfo, StatorRotorSplit, endpoint_key
from symmetry import extract_one_period, identify_symmetry_break


# ═══════════════════════════════════════════════════════════════
# 상수 정의
# ═══════════════════════════════════════════════════════════════

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
    'stator_yoke':    '#4A90D9',   # 진한 파랑
    'stator_tooth':   '#7EC8E3',   # 연한 파랑
    'slot':           '#FFD700',   # 금색
    'slot_opening':   '#FFFACD',   # 레몬색
    'airgap':         '#FFFFFF',   # 흰색
    'rotor_core':     '#FF8C42',   # 주황
    'magnet':         '#FF4444',   # 빨강
    'air_barrier':    '#C0C0C0',   # 은색
    'shaft':          '#8B8B8B',   # 회색
    'unknown':        '#D0D0D0',
}

SHORT_NAMES = {
    'stator_yoke': 'Yoke', 'stator_tooth': 'Tooth',
    'slot': 'Slot', 'slot_opening': 'SlotOp',
    'airgap': 'Gap', 'rotor_core': 'RotCore',
    'magnet': 'Mag', 'air_barrier': 'AirB',
    'shaft': 'Shaft', 'unknown': '?',
}


# ═══════════════════════════════════════════════════════════════
# 그래프 유틸리티
# ═══════════════════════════════════════════════════════════════

def _entity_endpoints(ei: EntityInfo,
                      origin: Tuple[float, float] = (0.0, 0.0)) -> Optional[Tuple]:
    """
    엔티티의 시작점·끝점을 반환합니다.
    CIRCLE은 단일 closed loop이므로 None을 반환.
    """
    if ei.etype == 'CIRCLE':
        return None
    elif ei.etype == 'LINE':
        return (ei.points[0], ei.points[1])
    elif ei.etype == 'ARC' and ei.center and ei.radius:
        cx, cy = ei.center
        r = ei.radius
        sa = math.radians(ei.start_angle)
        ea = math.radians(ei.end_angle)
        p0 = (cx + r * math.cos(sa), cy + r * math.sin(sa))
        p1 = (cx + r * math.cos(ea), cy + r * math.sin(ea))
        return (p0, p1)
    elif ei.etype == 'LWPOLYLINE' and len(ei.points) >= 2:
        return (ei.points[0], ei.points[-1])
    return None


def _add_boundary_segments(period_entities: List[EntityInfo],
                           period_deg: float,
                           reference_sector: int,
                           origin: Tuple[float, float],
                           split: StatorRotorSplit,
                           tol_digits: int = 2) -> List[Tuple]:
    """
    한 주기의 경계(radial cut line + 동심원 arc)를 가상 세그먼트로 추가합니다.
    """
    ox, oy = origin
    ang_s = reference_sector * period_deg
    ang_e = ang_s + period_deg

    r_vals = set()
    for ei in period_entities:
        if ei.etype in ('CIRCLE', 'ARC') and ei.center:
            d = math.hypot(ei.center[0] - ox, ei.center[1] - oy)
            if d < 1e-3 and ei.radius:
                r_vals.add(round(ei.radius, tol_digits))

    boundary_edges = []
    r_sorted = sorted(r_vals)
    if not r_sorted:
        return boundary_edges

    for angle_deg in [ang_s, ang_e]:
        rad = math.radians(angle_deg)
        for i in range(len(r_sorted) - 1):
            r1, r2 = r_sorted[i], r_sorted[i + 1]
            p1 = endpoint_key(ox + r1 * math.cos(rad), oy + r1 * math.sin(rad), tol_digits)
            p2 = endpoint_key(ox + r2 * math.cos(rad), oy + r2 * math.sin(rad), tol_digits)
            boundary_edges.append((p1, p2))

    return boundary_edges


def _build_planar_graph(one_period: List[EntityInfo],
                        origin: Tuple[float, float],
                        split: StatorRotorSplit,
                        period_deg: float,
                        reference_sector: int,
                        tol_digits: int = 2) -> Tuple[Dict, Dict, List]:
    """
    한 주기 엔티티로부터 평면 그래프를 구성합니다.
    """
    ox, oy = origin

    circles = [ei for ei in one_period if ei.etype == 'CIRCLE']
    independent_circles = [ei for ei in circles
                           if ei.center and math.hypot(ei.center[0] - ox, ei.center[1] - oy) > 1e-3]

    adj = defaultdict(set)
    edge_to_entity = {}

    non_circle = [ei for ei in one_period if ei.etype != 'CIRCLE']

    for ei in non_circle:
        ep = _entity_endpoints(ei, origin)
        if ep is None:
            continue
        k0 = endpoint_key(*ep[0], tol_digits)
        k1 = endpoint_key(*ep[1], tol_digits)
        if k0 == k1:
            continue
        edge = tuple(sorted([k0, k1]))
        if edge not in edge_to_entity:
            edge_to_entity[edge] = ei
            adj[k0].add(k1)
            adj[k1].add(k0)

    if split is not None:
        boundary_edges = _add_boundary_segments(
            one_period, period_deg, reference_sector, origin, split, tol_digits)
        for (k0, k1) in boundary_edges:
            edge = tuple(sorted([k0, k1]))
            if edge not in edge_to_entity:
                if k0 in adj or k1 in adj:
                    edge_to_entity[edge] = None
                    adj[k0].add(k1)
                    adj[k1].add(k0)

    return adj, edge_to_entity, independent_circles


def _traverse_faces(adj: Dict,
                    origin: Tuple[float, float] = (0.0, 0.0)) -> List[List]:
    """
    평면 그래프의 모든 면(face)을 찾습니다.
    """
    ox, oy = origin

    sorted_neighbors = {}
    for node in adj:
        neighbors = list(adj[node])
        if not neighbors:
            continue
        neighbors.sort(key=lambda nb: math.atan2(nb[1] - node[1], nb[0] - node[0]))
        sorted_neighbors[node] = neighbors

    used_half_edges = set()
    faces = []

    for node in sorted_neighbors:
        for start_nb in sorted_neighbors[node]:
            half_edge = (node, start_nb)
            if half_edge in used_half_edges:
                continue

            face = []
            cur = node
            nxt = start_nb
            max_steps = len(adj) + 2

            for _ in range(max_steps):
                used_half_edges.add((cur, nxt))
                face.append(cur)

                if nxt not in sorted_neighbors:
                    break
                nbs = sorted_neighbors[nxt]
                try:
                    idx = nbs.index(cur)
                except ValueError:
                    break
                next_idx = (idx - 1) % len(nbs)
                prev = cur
                cur = nxt
                nxt = nbs[next_idx]

                if cur == node and nxt == start_nb:
                    break

            if len(face) >= 3:
                faces.append(face)

    return faces


def _face_area_signed(face: List) -> float:
    """다각형 면의 부호 있는 면적 (Shoelace formula)."""
    n = len(face)
    area = 0.0
    for i in range(n):
        x0, y0 = face[i]
        x1, y1 = face[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area / 2.0


def _compute_face_geometry(fi: Dict,
                           origin: Tuple[float, float] = (0.0, 0.0)) -> None:
    """face dict에 기하학적 특성을 추가."""
    ox, oy = origin
    verts = fi['vertices']
    n = len(verts)
    rs = [math.hypot(v[0] - ox, v[1] - oy) for v in verts]
    fi['r_min'] = min(rs)
    fi['r_max'] = max(rs)
    fi['r_mean'] = sum(rs) / n
    fi['r_span'] = fi['r_max'] - fi['r_min']
    fi['cx'] = sum(v[0] for v in verts) / n
    fi['cy'] = sum(v[1] for v in verts) / n
    fi['centroid_r'] = math.hypot(fi['cx'] - ox, fi['cy'] - oy)
    fi['centroid_ang'] = math.degrees(math.atan2(fi['cy'] - oy, fi['cx'] - ox)) % 360


# ═══════════════════════════════════════════════════════════════
# 주요 함수
# ═══════════════════════════════════════════════════════════════

def find_closed_regions_in_period(entities: List[EntityInfo],
                                  period_deg: float,
                                  reference_sector: int = 0,
                                  origin: Tuple[float, float] = (0.0, 0.0),
                                  split: Optional[StatorRotorSplit] = None,
                                  tol_digits: int = 2,
                                  plot: bool = True) -> Dict:
    """
    한 주기 내 엔티티로부터 closed region(닫힌 영역) 수를 탐지합니다.
    
    Parameters
    ----------
    entities : List[EntityInfo]
        엔티티 리스트
    period_deg : float
        한 주기 각도
    reference_sector : int
        분석할 섹터 번호
    origin : Tuple[float, float]
        원점 좌표
    split : StatorRotorSplit
        고정자/회전자 분리 결과
    tol_digits : int
        좌표 반올림 자릿수
    plot : bool
        시각화 여부
    
    Returns
    -------
    Dict
        n_closed_regions, n_graph_regions, n_circles 등
    """
    one_period = extract_one_period(entities, period_deg, reference_sector, origin)
    ox, oy = origin

    circles = [ei for ei in one_period if ei.etype == 'CIRCLE']
    independent_circles = [ei for ei in circles
                           if ei.center and math.hypot(ei.center[0] - ox, ei.center[1] - oy) > 1e-3]
    n_circles = len(independent_circles)

    adj = defaultdict(set)
    edge_set = set()

    non_circle = [ei for ei in one_period if ei.etype != 'CIRCLE']

    for ei in non_circle:
        ep = _entity_endpoints(ei, origin)
        if ep is None:
            continue
        k0 = endpoint_key(*ep[0], tol_digits)
        k1 = endpoint_key(*ep[1], tol_digits)
        if k0 == k1:
            continue
        edge = tuple(sorted([k0, k1]))
        if edge not in edge_set:
            edge_set.add(edge)
            adj[k0].add(k1)
            adj[k1].add(k0)

    if split is not None:
        boundary_edges = _add_boundary_segments(
            one_period, period_deg, reference_sector, origin, split, tol_digits)
        for (k0, k1) in boundary_edges:
            edge = tuple(sorted([k0, k1]))
            if edge not in edge_set:
                if k0 in adj or k1 in adj:
                    edge_set.add(edge)
                    adj[k0].add(k1)
                    adj[k1].add(k0)

    V = len(adj)
    E = len(edge_set)

    visited = set()
    n_components = 0
    for node in adj:
        if node not in visited:
            n_components += 1
            queue = [node]
            while queue:
                cur = queue.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                for nb in adj[cur]:
                    if nb not in visited:
                        queue.append(nb)

    n_graph_faces = E - V + n_components + 1
    n_graph_regions = max(0, n_graph_faces - 1)

    n_closed_total = n_graph_regions + n_circles

    result = {
        'n_closed_regions': n_closed_total,
        'n_graph_regions': n_graph_regions,
        'n_circles': n_circles,
        'n_vertices': V,
        'n_edges': E,
        'n_components': n_components,
    }

    print(f'\n[find_closed_regions_in_period] sector {reference_sector} '
          f'({reference_sector * period_deg:.1f}°~'
          f'{(reference_sector + 1) * period_deg:.1f}°):')
    print(f'  Graph: V={V}, E={E}, Components={n_components}')
    print(f'  Euler: F = E-V+C+1 = {E}-{V}+{n_components}+1 = {n_graph_faces}')
    print(f'  → graph regions (F-1): {n_graph_regions}')
    print(f'  → independent circles: {n_circles}')
    print(f'  → total closed regions: {n_closed_total}')

    return result


def _find_half_unit_faces_from_period(entities: List[EntityInfo],
                                      origin: Tuple[float, float],
                                      split: StatorRotorSplit,
                                      period_deg: float,
                                      half_unit: Dict,
                                      tol_digits: int = 2,
                                      min_area: float = 0.5) -> Dict:
    """
    한 주기에서 검증된 face 탐지를 수행한 뒤,
    반슬롯/반극 각도 범위에 해당하는 face만 필터링합니다.
    """
    ox, oy = origin
    ref_start = half_unit['ref_angle_start']
    half_slot_deg = half_unit['half_slot_deg']
    half_pole_deg = half_unit['half_pole_deg']
    ref_sector = int(ref_start / period_deg) if period_deg > 0 else 0

    one_period = extract_one_period(entities, period_deg, ref_sector, origin)
    adj, edge_to_entity, indep_circles = _build_planar_graph(
        one_period, origin, split, period_deg, ref_sector, tol_digits)

    raw_faces = _traverse_faces(adj, origin)
    r_mid = (split.airgap_r_inner + split.airgap_r_outer) / 2

    all_faces = []
    for face in raw_faces:
        area = _face_area_signed(face)
        if abs(area) < min_area or area <= 0:
            continue
        nv = len(face)
        centroid_x = sum(v[0] for v in face) / nv
        centroid_y = sum(v[1] for v in face) / nv
        centroid_r = math.hypot(centroid_x - ox, centroid_y - oy)
        centroid_ang = math.degrees(math.atan2(centroid_y - oy, centroid_x - ox)) % 360

        vert_rs = [math.hypot(v[0] - ox, v[1] - oy) for v in face]

        fi = {
            'vertices': face,
            'area': area,
            'n_edges': nv,
            'part': 'stator' if centroid_r > r_mid else 'rotor',
            'centroid_ang': centroid_ang,
            'centroid_r': centroid_r,
            'r_min': min(vert_rs),
            'r_max': max(vert_rs),
        }
        all_faces.append(fi)

    def _in_half_range(ang, start, half_deg_):
        end = (start + half_deg_) % 360
        s = start % 360
        if s < end:
            return s <= ang <= end
        else:
            return ang >= s or ang <= end

    stator_faces = [fi for fi in all_faces
                    if fi['part'] == 'stator'
                    and _in_half_range(fi['centroid_ang'], ref_start, half_slot_deg)]
    rotor_faces = [fi for fi in all_faces
                   if fi['part'] == 'rotor'
                   and _in_half_range(fi['centroid_ang'], ref_start, half_pole_deg)]

    stator_half_ids = set(id(f) for f in stator_faces)
    rotor_half_ids = set(id(f) for f in rotor_faces)

    period_end = (ref_start + period_deg) % 360

    def _in_period(ang):
        s = ref_start % 360
        e = period_end % 360
        if s < e:
            return s <= ang <= e
        else:
            return ang >= s or ang <= e

    stator_wide_faces = [fi for fi in all_faces
                         if fi['part'] == 'stator'
                         and id(fi) not in stator_half_ids
                         and _in_period(fi['centroid_ang'])
                         and fi['r_min'] > r_mid]

    rotor_wide_faces = [fi for fi in all_faces
                        if fi['part'] == 'rotor'
                        and id(fi) not in rotor_half_ids
                        and _in_period(fi['centroid_ang'])
                        and fi['r_max'] < r_mid * 3]

    return {
        'stator_faces': stator_faces,
        'rotor_faces': rotor_faces,
        'stator_wide_faces': stator_wide_faces,
        'rotor_wide_faces': rotor_wide_faces,
        'adj': adj,
        'edge_to_entity': edge_to_entity,
    }


def classify_half_unit_regions(half_unit: Dict,
                               split: StatorRotorSplit,
                               entities: List[EntityInfo],
                               period_deg: float,
                               topology: Optional[Dict] = None,
                               origin: Tuple[float, float] = (0.0, 0.0),
                               min_area: float = 0.5) -> Dict:
    """
    반슬롯/반극 최소 단위 내에서 닫힌 영역을 찾고 이름을 부여합니다.
    
    Parameters
    ----------
    half_unit : Dict
        extract_half_unit 결과
    split : StatorRotorSplit
        고정자/회전자 분리 결과
    entities : List[EntityInfo]
        전체 엔티티 리스트
    period_deg : float
        한 주기 각도
    topology : Dict
        classify_motor_topology 결과
    origin : Tuple[float, float]
        원점 좌표
    min_area : float
        최소 면적 필터
    
    Returns
    -------
    Dict
        stator_faces, rotor_faces, *_adj, *_edge_map
    """
    ox, oy = origin
    topo = (topology or {}).get('topology', 'IPMSM')
    is_inner = (split.motor_type == 'inner_rotor')
    r_ag_in = split.airgap_r_inner
    r_ag_out = split.airgap_r_outer

    all_entities = split.stator_entities + split.rotor_entities
    concentric_r = sorted(set(
        round(ei.radius, 2)
        for ei in all_entities
        if ei.etype in ('CIRCLE', 'ARC') and ei.center
        and math.hypot(ei.center[0] - ox, ei.center[1] - oy) < 1e-3
        and ei.radius))

    if is_inner:
        rotor_radii = sorted([r for r in concentric_r if r <= r_ag_in + 0.5])
        stator_radii = sorted([r for r in concentric_r if r >= r_ag_out - 0.5])
        r_shaft = rotor_radii[0] if rotor_radii else 0
        r_stator_outer = stator_radii[-1] if stator_radii else r_ag_out + 50
    else:
        rotor_radii = sorted([r for r in concentric_r if r >= r_ag_out - 0.5])
        stator_radii = sorted([r for r in concentric_r if r <= r_ag_in + 0.5])
        r_shaft = 0
        r_stator_outer = stator_radii[0] if stator_radii else r_ag_in - 50

    period_result = _find_half_unit_faces_from_period(
        entities, origin, split, period_deg, half_unit,
        tol_digits=2, min_area=min_area)

    s_faces = period_result['stator_faces']
    r_faces = period_result['rotor_faces']
    s_wide = period_result['stator_wide_faces']
    r_wide = period_result['rotor_wide_faces']
    shared_adj = period_result['adj']
    shared_emap = period_result['edge_to_entity']

    for fi in s_faces:
        _compute_face_geometry(fi, origin)
    for fi in s_wide:
        _compute_face_geometry(fi, origin)

    # 광역 고정자 분류
    for fi in s_wide:
        fi['scope'] = 'period'
        if abs(fi['r_max'] - r_stator_outer) < 2.0:
            fi['name'] = 'stator_yoke'
        elif is_inner and abs(fi['r_min'] - r_ag_out) < 3.0 and fi['area'] < 200:
            fi['name'] = 'slot_opening'
        else:
            fi['name'] = 'slot'

    # 반슬롯 고정자 분류
    if s_faces:
        for fi in s_faces:
            fi['scope'] = 'half'
            if abs(fi['r_max'] - r_stator_outer) < 2.0:
                fi['name'] = 'stator_yoke'
            elif is_inner and abs(fi['r_min'] - r_ag_out) < 3.0 and fi['area'] < 200:
                fi['name'] = 'slot_opening'
            else:
                fi['name'] = '_stator_unclassified'

        unclassified_s = [fi for fi in s_faces if fi['name'] == '_stator_unclassified']
        if unclassified_s:
            unc_sorted = sorted(unclassified_s, key=lambda f: f['area'], reverse=True)
            unc_sorted[0]['name'] = 'slot'
            for fi in unc_sorted[1:]:
                if fi['r_span'] > 10 and fi['area'] > 50:
                    fi['name'] = 'stator_tooth'
                else:
                    fi['name'] = 'slot_opening'

        for fi in s_faces:
            if fi.get('name', '').startswith('_'):
                fi['name'] = 'slot_opening'

    s_faces = s_faces + s_wide

    # 회전자 분류
    for fi in r_faces:
        _compute_face_geometry(fi, origin)
    for fi in r_wide:
        _compute_face_geometry(fi, origin)

    if r_faces:
        for fi in r_faces:
            fi['scope'] = 'half'
            if is_inner:
                if fi['r_max'] <= r_shaft + 1.0:
                    fi['name'] = 'shaft'
                else:
                    fi['name'] = '_rotor_unclassified'
            else:
                fi['name'] = '_rotor_unclassified'

        shaft_faces = [fi for fi in r_faces if fi['name'] == 'shaft']
        for fi in shaft_faces:
            fi['scope'] = 'period'
            r_faces.remove(fi)
            r_wide.append(fi)

        unclassified_r = [fi for fi in r_faces if fi['name'] == '_rotor_unclassified']
        if unclassified_r:
            unc_r_sorted = sorted(unclassified_r, key=lambda f: f['area'], reverse=True)
            
            if topo == 'SPMSM':
                for fi in unc_r_sorted:
                    fi['name'] = 'magnet'
            else:  # IPMSM / PMa-SynRM
                if unc_r_sorted:
                    unc_r_sorted[0]['name'] = 'magnet'
                    for fi in unc_r_sorted[1:]:
                        fi['name'] = 'air_barrier'

        for fi in r_faces:
            if fi.get('name', '').startswith('_'):
                fi['name'] = 'unknown'

    # 광역 회전자 분류
    for fi in r_wide:
        fi['scope'] = 'period'
        if is_inner:
            if fi['r_max'] <= r_shaft + 1.0:
                fi['name'] = 'shaft'
            elif fi['r_min'] >= r_ag_in - 3.0:
                fi['name'] = 'airgap'
            else:
                fi['name'] = 'rotor_core'
        else:
            fi['name'] = 'rotor_core'

    r_faces = r_faces + r_wide

    print(f'\n[classify_half_unit_regions] 반슬롯/반극 기준 영역 분류 (topology={topo}):')
    print(f'  고정자: {len(s_faces)}개 영역')
    for fi in sorted(s_faces, key=lambda f: f['area'], reverse=True):
        scope_mark = ' [P]' if fi.get('scope') == 'period' else ''
        print(f'    {REGION_NAMES.get(fi["name"], fi["name"]):20s} '
              f'area={fi["area"]:8.1f}  r=[{fi["r_min"]:.1f}~{fi["r_max"]:.1f}]{scope_mark}')
    print(f'  회전자: {len(r_faces)}개 영역')
    for fi in sorted(r_faces, key=lambda f: f['area'], reverse=True):
        scope_mark = ' [P]' if fi.get('scope') == 'period' else ''
        print(f'    {REGION_NAMES.get(fi["name"], fi["name"]):20s} '
              f'area={fi["area"]:8.1f}  r=[{fi["r_min"]:.1f}~{fi["r_max"]:.1f}]{scope_mark}')

    return {
        'stator_faces': s_faces,
        'rotor_faces': r_faces,
        'stator_adj': shared_adj,
        'stator_edge_map': shared_emap,
        'rotor_adj': shared_adj,
        'rotor_edge_map': shared_emap,
    }
