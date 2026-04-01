"""
pyMotorGeo.reader
=================

ezdxf를 기반으로 DXF 파일을 파싱하여 내부 구조체(`EntityInfo`)로 변환해 주는 모듈입니다.
단순 기본 엔티티(LINE, ARC, CIRCLE 등) 외에도 INSERT(블록 참조)를 재귀적으로 전개(Explode)하여 
동일한 평면 엔티티로 평탄화하는 기능을 포함하고 있습니다.
"""

import math
import numpy as np
import ezdxf
from collections import Counter
from typing import List, Tuple, Dict, Any

from core import EntityInfo

# ═══════════════════════════════════════════════════════════════
# 상수 정의
# ═══════════════════════════════════════════════════════════════

SKIP_ENTITY_TYPES = {
    'TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF', 'DIMENSION',
    'LEADER', 'MLEADER', 'VIEWPORT'
}

EXPANDABLE_ENTITY_TYPES = {
    'LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'POLYLINE',
    'SPLINE', 'ELLIPSE', 'POINT'
}


# ═══════════════════════════════════════════════════════════════
# INSERT/BLOCK 변환 함수
# ═══════════════════════════════════════════════════════════════

def transform_point(x: float, y: float,
                    insert_x: float, insert_y: float,
                    rotation_deg: float = 0.0,
                    scale_x: float = 1.0, scale_y: float = 1.0) -> Tuple[float, float]:
    """블록 참조(INSERT) 시 적용된 공간 변환(스케일, 회전, 평행 이동) 행렬을 점 좌표에 적용합니다.

    스케일 변환이 가장 먼저 적용되고, 지정된 회전 각도로 원점(0,0) 기준 회전을 수행한 후, 
    최종 위치에 기반해 좌표를 평행 이동합니다.

    Args:
        x (float): 원본 x 좌표.
        y (float): 원본 y 좌표.
        insert_x (float): 블록이 삽입된 기준 x 좌표 (평행 이동량).
        insert_y (float): 블록이 삽입된 기준 y 좌표 (평행 이동량).
        rotation_deg (float): 블록에 적용된 회전 각도 (도 단위). 기본값은 0.0.
        scale_x (float): x축 방향의 스케일 팩터. 기본값은 1.0.
        scale_y (float): y축 방향의 스케일 팩터. 기본값은 1.0.

    Returns:
        Tuple[float, float]: 공간 변환이 완료된 새로운 (x', y') 좌표.
    """
    x_scaled = x * scale_x
    y_scaled = y * scale_y

    if rotation_deg != 0:
        rad = math.radians(rotation_deg)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        x_rot = x_scaled * cos_r - y_scaled * sin_r
        y_rot = x_scaled * sin_r + y_scaled * cos_r
    else:
        x_rot, y_rot = x_scaled, y_scaled

    return (x_rot + insert_x, y_rot + insert_y)


def explode_insert(insert_entity, doc: Any, depth: int = 0, max_depth: int = 5) -> List[Dict[str, Any]]:
    """DXF 문서 내의 INSERT(블록 참조) 엔티티를 재귀적으로 분석하여 기본 기하 평면 엔티티로 전개합니다.

    중첩된 블록 구조를 처리하기 위해 `max_depth`에 도달할 때까지 재귀 호출을 수행합니다. 전개 과정에서 
    각 하위 엔티티의 기하(포인트, 중점 등)에는 블록의 Scale, Rotation, Translation 변환이 누적 적용됩니다.

    Args:
        insert_entity (ezdxf.entities.Insert): 전개할 대상 INSERT 엔티티 객체.
        doc (ezdxf.document.Drawing): 원본 DXF 블록과 데이터를 들고 있는 문서 객체.
        depth (int): 현재 재귀 계층의 깊이. 무한 루프 방지를 위해 사용됨. 기본값은 0.
        max_depth (int): 최대 허용 재귀 깊이. 이 값을 넘어가면 빈 리스트를 반환함. 기본값은 5.

    Returns:
        List[Dict[str, Any]]: 블록에서 풀려나온 평탄화(flattened)된 엔티티 속성 딕셔너리 리스트. 
                              내부에 `type`, `points`, `radius`, `center`, `start_angle`, `end_angle`, 
                              `is_closed`, `layer`, `source_block` 등의 키를 가집니다.
    """
    if depth > max_depth:
        return []

    block_name = insert_entity.dxf.name
    block = doc.blocks.get(block_name)
    if block is None:
        return []

    ins_x = float(insert_entity.dxf.insert.x)
    ins_y = float(insert_entity.dxf.insert.y)
    rotation = float(getattr(insert_entity.dxf, 'rotation', 0.0))
    scale_x = float(getattr(insert_entity.dxf, 'xscale', 1.0))
    scale_y = float(getattr(insert_entity.dxf, 'yscale', 1.0))
    layer = getattr(insert_entity.dxf, 'layer', '(no layer)')

    row_count = int(getattr(insert_entity.dxf, 'row_count', 1))
    col_count = int(getattr(insert_entity.dxf, 'column_count', 1))
    row_spacing = float(getattr(insert_entity.dxf, 'row_spacing', 0.0))
    col_spacing = float(getattr(insert_entity.dxf, 'column_spacing', 0.0))

    exploded = []

    for row in range(row_count):
        for col in range(col_count):
            current_ins_x = ins_x + col * col_spacing
            current_ins_y = ins_y + row * row_spacing

            for e in block:
                t = e.dxftype()

                if t == 'INSERT':
                    nested = explode_insert(e, doc, depth + 1, max_depth)
                    for item in nested:
                        new_pts = [transform_point(px, py, current_ins_x, current_ins_y,
                                                   rotation, scale_x, scale_y)
                                   for px, py in item['points']]
                        item['points'] = new_pts
                        if item.get('center'):
                            cx, cy = item['center']
                            item['center'] = transform_point(cx, cy, current_ins_x, current_ins_y,
                                                             rotation, scale_x, scale_y)
                    exploded.extend(nested)
                    continue

                if t not in EXPANDABLE_ENTITY_TYPES:
                    continue

                pts = []
                radius = center = sa = ea = None
                is_closed = False
                ent_layer = getattr(e.dxf, 'layer', layer)

                if t == 'LINE':
                    pts = [(float(e.dxf.start.x), float(e.dxf.start.y)),
                           (float(e.dxf.end.x), float(e.dxf.end.y))]
                elif t == 'CIRCLE':
                    cx, cy = float(e.dxf.center.x), float(e.dxf.center.y)
                    r = float(e.dxf.radius) * abs(scale_x)
                    center = (cx, cy)
                    radius = r
                    pts = [(cx + r, cy), (cx - r, cy), (cx, cy + r), (cx, cy - r)]
                    is_closed = True
                elif t == 'ARC':
                    cx, cy = float(e.dxf.center.x), float(e.dxf.center.y)
                    r = float(e.dxf.radius) * abs(scale_x)
                    center = (cx, cy)
                    radius = r
                    sa = float(e.dxf.start_angle) + rotation
                    ea = float(e.dxf.end_angle) + rotation
                    for ang_deg in [sa, ea, (sa + ea) / 2]:
                        rad = math.radians(ang_deg)
                        pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
                elif t == 'LWPOLYLINE':
                    pts = [(float(x), float(y)) for x, y in e.get_points(format='xy')]
                    is_closed = e.closed
                elif t == 'POLYLINE':
                    try:
                        pts = [(float(v.dxf.location.x), float(v.dxf.location.y))
                               for v in e.vertices]
                        is_closed = e.is_closed
                    except Exception:
                        continue
                elif t == 'SPLINE':
                    try:
                        ctrl = list(e.control_points)
                        pts = [(float(p[0]), float(p[1])) for p in ctrl]
                        is_closed = e.closed
                    except Exception:
                        continue
                elif t == 'ELLIPSE':
                    try:
                        cx, cy = float(e.dxf.center.x), float(e.dxf.center.y)
                        center = (cx, cy)
                        pts = []
                        for ang in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                            px, py, _ = e.vertex(ang)
                            pts.append((float(px), float(py)))
                        is_closed = True
                    except Exception:
                        continue
                elif t == 'POINT':
                    pts = [(float(e.dxf.location.x), float(e.dxf.location.y))]

                if not pts:
                    continue

                transformed_pts = [transform_point(px, py, current_ins_x, current_ins_y,
                                                   rotation, scale_x, scale_y)
                                   for px, py in pts]

                transformed_center = None
                if center:
                    transformed_center = transform_point(center[0], center[1],
                                                         current_ins_x, current_ins_y,
                                                         rotation, scale_x, scale_y)

                exploded.append({
                    'type': t,
                    'points': transformed_pts,
                    'radius': radius,
                    'center': transformed_center,
                    'start_angle': sa,
                    'end_angle': ea,
                    'is_closed': is_closed,
                    'layer': ent_layer,
                    'source_block': block_name
                })

    return exploded


# ═══════════════════════════════════════════════════════════════
# 메인 DXF 읽기 함수
# ═══════════════════════════════════════════════════════════════

def read_entity_list(dxf_path: str,
                     skip_text: bool = True,
                     expand_inserts: bool = True,
                     verbose: bool = True) -> Tuple[List[EntityInfo], 'ezdxf.document.Drawing']:
    """DXF 파일을 파싱하여 내부 구조망인 `EntityInfo` 리스트로 반환합니다.

    `ezdxf`를 사용하여 DXF의 modelspace 엔티티를 순회하며 지정된 타입(LINE, ARC, CIRCLE 등)의 좌표와
    기하학적 속성들을 추출합니다. 불필요한 주석 엔티티는 건너뛰며, BLOCK과 같은 복합 요소는 
    기본 평면 기하로 전개할 수 있습니다.

    Args:
        dxf_path (str): 읽어들일 DXF 파일의 절대 또는 상대 경로.
        skip_text (bool, optional): TEXT, MTEXT, DIMENSION 등 텍스트 주석 보조 객체들의 
                                    무시 여부. 기본값은 True.
        expand_inserts (bool, optional): INSERT(블록 참조) 객체가 나타났을 때 전개(flattening)하여 
                                         기본 기하들로 풀어버릴지 여부. 기본값은 True.
        verbose (bool, optional): 로딩 과정의 통계치(예: 남겨진/무시된 요소 개수)를 콘솔(stdout)에 
                                  출력할지 여부. 기본값은 True.

    Returns:
        Tuple[List[EntityInfo], ezdxf.document.Drawing]: 
            - 파싱된 추상화된 원본 지오메트리 데이터를 담은 `EntityInfo` 객체들의 리스트.
            - 로드된 `ezdxf.document.Drawing` 원본 파싱 문서 객체.
    """
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    entities: List[EntityInfo] = []
    skipped_types = Counter()
    insert_stats = {'count': 0, 'expanded': 0, 'blocks': Counter()}

    for e in msp:
        t = e.dxftype()

        if t == 'INSERT':
            insert_stats['count'] += 1
            if expand_inserts:
                block_name = e.dxf.name
                insert_stats['blocks'][block_name] += 1
                exploded = explode_insert(e, doc)
                insert_stats['expanded'] += len(exploded)
                for item in exploded:
                    entities.append(EntityInfo(
                        etype=item['type'], layer=item['layer'], points=item['points'],
                        radius=item['radius'], center=item['center'],
                        start_angle=item['start_angle'], end_angle=item['end_angle'],
                        is_closed=item['is_closed'], raw=None
                    ))
            else:
                skipped_types['INSERT'] += 1
            continue

        if t == 'HATCH':
            skipped_types['HATCH'] += 1
            continue

        if skip_text and t in SKIP_ENTITY_TYPES:
            skipped_types[t] += 1
            continue

        layer = getattr(e.dxf, 'layer', '(no layer)')
        pts = []
        radius = center = sa = ea = None
        is_closed = False

        if t == 'LINE':
            pts = [(float(e.dxf.start.x), float(e.dxf.start.y)),
                   (float(e.dxf.end.x), float(e.dxf.end.y))]
        elif t == 'CIRCLE':
            cx, cy = float(e.dxf.center.x), float(e.dxf.center.y)
            r = float(e.dxf.radius)
            center = (cx, cy)
            radius = r
            pts = [(cx + r, cy), (cx - r, cy), (cx, cy + r), (cx, cy - r)]
            is_closed = True
        elif t == 'ARC':
            cx, cy = float(e.dxf.center.x), float(e.dxf.center.y)
            r = float(e.dxf.radius)
            center = (cx, cy)
            radius = r
            sa = float(e.dxf.start_angle)
            ea = float(e.dxf.end_angle)
            for ang_deg in [sa, ea, (sa + ea) / 2]:
                rad = math.radians(ang_deg)
                pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
        elif t == 'LWPOLYLINE':
            pts = [(float(x), float(y)) for x, y in e.get_points(format='xy')]
            is_closed = e.closed
        elif t == 'POLYLINE':
            try:
                pts = [(float(v.dxf.location.x), float(v.dxf.location.y))
                       for v in e.vertices]
                is_closed = e.is_closed
            except Exception:
                pass
        elif t == 'SPLINE':
            try:
                ctrl = list(e.control_points)
                pts = [(float(p[0]), float(p[1])) for p in ctrl]
                is_closed = e.closed
            except Exception:
                pass
        elif t == 'POINT':
            pts = [(float(e.dxf.location.x), float(e.dxf.location.y))]
        elif t == 'ELLIPSE':
            try:
                cx, cy = float(e.dxf.center.x), float(e.dxf.center.y)
                center = (cx, cy)
                pts = []
                for ang in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                    px, py, _ = e.vertex(ang)
                    pts.append((float(px), float(py)))
                is_closed = True
            except Exception:
                pass
        elif t in ('SOLID', '3DFACE'):
            try:
                pts = []
                for attr in ['vtx0', 'vtx1', 'vtx2', 'vtx3']:
                    v = getattr(e.dxf, attr, None)
                    if v:
                        pts.append((float(v.x), float(v.y)))
                is_closed = True
            except Exception:
                pass
        else:
            continue

        if pts:
            entities.append(EntityInfo(
                etype=t, layer=layer, points=pts,
                radius=radius, center=center,
                start_angle=sa, end_angle=ea,
                is_closed=is_closed, raw=e
            ))

    if verbose:
        print(f"[read_entity_list] {len(entities)} entities loaded from {dxf_path}")
        if skipped_types:
            print(f"  [Skipped] {dict(skipped_types)}")
        if insert_stats['count'] > 0:
            print(f"  [INSERT] {insert_stats['count']} found, {insert_stats['expanded']} entities expanded")
            if insert_stats['blocks']:
                print(f"    Blocks: {dict(insert_stats['blocks'])}")
        type_cnt = Counter(ei.etype for ei in entities)
        print(f"  Entity types: {dict(type_cnt)}")
        closed_cnt = sum(1 for ei in entities if ei.is_closed)
        if closed_cnt > 0:
            print(f"  Closed entities: {closed_cnt}")
        layer_cnt = Counter(ei.layer for ei in entities)
        for name, cnt in layer_cnt.most_common(10):
            print(f"  {name:30s}  {cnt}")

    return entities, doc


def manual_parse_dxf_entities(dxf_path: str,
                              encoding: str = 'cp932',
                              errors: str = 'ignore') -> List[EntityInfo]:
    """ezdxf 로드에 실패한 경우를 위한 최소 수동 DXF 파서입니다.

    Notes:
        - ENTITIES 섹션에서 LINE/LWPOLYLINE/ARC/CIRCLE만 파싱합니다.
        - 엔티티 속성은 핵심 좌표 정보 위주로 추출합니다.
        - fallback 경로를 위한 유틸 함수이므로 복잡 엔티티는 의도적으로 제외합니다.

    Args:
        dxf_path (str): DXF 파일 경로.
        encoding (str): 파일 읽기 인코딩. 기본값은 'cp932'.
        errors (str): 인코딩 오류 처리 방식. 기본값은 'ignore'.

    Returns:
        List[EntityInfo]: 파싱된 엔티티 리스트.
    """
    entities: List[EntityInfo] = []

    with open(dxf_path, 'r', encoding=encoding, errors=errors) as f:
        lines = [ln.strip() for ln in f.readlines()]

    i = 0
    in_entities = False
    while i < len(lines) - 1:
        code = lines[i]
        val = lines[i + 1]

        if code == '2' and val == 'ENTITIES':
            in_entities = True
            i += 2
            continue
        if in_entities and code == '0' and val == 'ENDSEC':
            break

        if in_entities and code == '0' and val in ('LINE', 'LWPOLYLINE', 'ARC', 'CIRCLE'):
            etype = val
            j = i + 2
            layer = 'DEFAULT'
            pts = []
            center = None
            radius = None
            start_angle = None
            end_angle = None
            x_tmp = None

            x1 = y1 = x2 = y2 = None
            cx = cy = None

            while j < len(lines) - 1:
                c = lines[j]
                v = lines[j + 1]
                if c == '0':
                    break
                try:
                    ci = int(c)
                except Exception:
                    j += 2
                    continue

                if ci == 8:
                    layer = v
                elif etype == 'LINE':
                    if ci == 10:
                        x1 = float(v)
                    elif ci == 20:
                        y1 = float(v)
                    elif ci == 11:
                        x2 = float(v)
                    elif ci == 21:
                        y2 = float(v)
                elif etype == 'LWPOLYLINE':
                    if ci == 10:
                        x_tmp = float(v)
                    elif ci == 20 and x_tmp is not None:
                        pts.append((x_tmp, float(v)))
                        x_tmp = None
                elif etype in ('ARC', 'CIRCLE'):
                    if ci == 10:
                        cx = float(v)
                    elif ci == 20:
                        cy = float(v)
                    elif ci == 40:
                        radius = float(v)
                    elif ci == 50:
                        start_angle = float(v)
                    elif ci == 51:
                        end_angle = float(v)

                j += 2

            if etype == 'LINE' and None not in (x1, y1, x2, y2):
                pts = [(x1, y1), (x2, y2)]

            if etype in ('ARC', 'CIRCLE') and (cx is not None and cy is not None):
                center = (cx, cy)
                if radius is not None:
                    # core.EntityInfo의 r_min/r_max는 points 기반 property이므로 샘플 포인트를 생성합니다.
                    pts = [
                        (cx + radius, cy),
                        (cx - radius, cy),
                        (cx, cy + radius),
                        (cx, cy - radius),
                    ]
                else:
                    pts = [(cx, cy)]

            if pts:
                entities.append(EntityInfo(
                    etype=etype,
                    layer=layer,
                    points=pts,
                    center=center,
                    radius=radius,
                    start_angle=start_angle,
                    end_angle=end_angle,
                    is_closed=(etype == 'CIRCLE'),
                    raw=None,
                ))

            i = j
            continue

        i += 2

    return entities
