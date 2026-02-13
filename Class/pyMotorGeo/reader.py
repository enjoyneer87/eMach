"""
pyMotorGeo.reader
=================
DXF 파일 읽기 및 엔티티 추출 함수.
INSERT/BLOCK 확장, 다양한 엔티티 타입 지원.
"""

import math
import numpy as np
import ezdxf
from collections import Counter
from typing import List, Tuple, Dict

from .core import EntityInfo

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
    """INSERT 변환 적용: 스케일 → 회전 → 이동."""
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


def explode_insert(insert_entity, doc, depth: int = 0, max_depth: int = 5) -> List[dict]:
    """INSERT 엔티티를 전개(explode)하여 기본 엔티티 목록으로 변환."""
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
    """
    DXF 파일의 modelspace 엔티티를 읽어 EntityInfo 리스트로 반환합니다.

    Parameters
    ----------
    dxf_path : str
        DXF 파일 경로
    skip_text : bool
        TEXT, MTEXT 등 주석 엔티티 제외 (기본값 True)
    expand_inserts : bool
        INSERT(BLOCK 참조) 전개 (기본값 True)
    verbose : bool
        로딩 정보 출력 (기본값 True)
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
