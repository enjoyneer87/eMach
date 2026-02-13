"""
pyMotorGeo.region_closing
==========================
주기모델(periodic sector) 경계선 생성 → 닫힌 영역(closed region) 탐지 → 이름 할당.

주기모델에서 stator core, rotor core, shaft 영역은 주기 경계(0°, period_deg)에서
열린 상태이므로, 방사 직선(boundary line)과 호(arc)를 추가하여 닫힌 영역을 형성합니다.
에어갭 경계는 별도로 추가하지 않습니다.

핵심 흐름:
  1) close_period_model() → 경계선(boundary) EntityInfo 추가
  2) detect_closed_faces()  → planar graph 기반 닫힌 면(face) 탐지
  3) auto_name_faces()      → 반경/위치 기반 자동 이름 할당
"""

import math
import numpy as np
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional
from .core import EntityInfo, endpoint_key


# ═══════════════════════════════════════════════════════════════
# 경계 직선 생성
# ═══════════════════════════════════════════════════════════════

def create_radial_line(r_start: float, r_end: float,
                       angle_deg: float,
                       origin: Tuple[float, float] = (0.0, 0.0),
                       layer: str = '_BOUNDARY_',
                       n_segments: int = 1) -> EntityInfo:
    """
    주어진 각도에서 r_start ~ r_end 사이의 방사 직선 EntityInfo 생성.

    Parameters
    ----------
    r_start : 시작 반경
    r_end : 끝 반경
    angle_deg : 직선 각도 (deg)
    origin : 원점
    layer : 레이어 이름
    n_segments : 분할 수 (1이면 단일 직선)

    Returns
    -------
    EntityInfo (LINE)
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
    주어진 반경에서 start_deg ~ end_deg 사이의 호(arc) EntityInfo 생성.

    Parameters
    ----------
    radius : 반경
    start_deg, end_deg : 시작/끝 각도 (deg)
    origin : 원점
    layer : 레이어 이름
    n_points : 호 위 점 수 (선분 근사)

    Returns
    -------
    EntityInfo (ARC)
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
) -> List[Dict]:
    """
    엔티티 리스트에서 planar graph 기반 닫힌 면(face)을 탐지합니다.

    Parameters
    ----------
    entities : 경계선 포함 엔티티 리스트
    origin : 원점
    min_area : 최소 면적 필터
    tol_digits : endpoint 반올림 자릿수

    Returns
    -------
    List[Dict] : 각 face 정보
        vertices, area, centroid, centroid_r, centroid_ang, r_min, r_max, name
    """
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
            'vertices': list(verts),
            'area': area,
            'n_edges': n,
            'centroid': (cx, cy),
            'centroid_r': math.hypot(cx - ox, cy - oy),
            'centroid_ang': math.degrees(math.atan2(cy - oy, cx - ox)) % 360,
            'r_min': min(rs),
            'r_max': max(rs),
            'r_mean': float(np.mean(rs)),
            'name': 'unknown',
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
    탐지된 face에 반경/위치 기반으로 이름을 자동 할당합니다.

    Parameters
    ----------
    faces : detect_closed_faces() 결과
    r_shaft, r_rotor_outer, r_stator_inner, r_stator_outer : 경계 반경
    rotor_topology : 'SPM', 'IPM', 'SynRM' 등

    Returns
    -------
    faces (in-place 수정 + 반환)
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


def get_face_summary(faces: List[Dict]) -> Dict[str, int]:
    """face 이름별 개수 요약."""
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
