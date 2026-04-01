"""
pyMotorGeo.motorcad_bridge
==========================
Motor-CAD Adaptive Geometry 연동: Region 변환 및 적용.
"""

import math
from typing import List, Dict, Optional, Tuple

from regions import REGION_NAMES


# ═══════════════════════════════════════════════════════════════
# Motor-CAD 매핑 테이블
# ═══════════════════════════════════════════════════════════════

REGION_TYPE_MAP = {
    'stator_yoke':   ('Stator Lam (Back Iron)', 'M19_29G',  (0, 102, 204),   'stator'),
    'stator_tooth':  ('Stator Lam (Tooth)',     'M19_29G',  (0, 153, 204),   'stator'),
    'slot':          ('Stator Slot',            'Air',      (255, 204, 0),   'stator'),
    'slot_opening':  ('Stator Slot Opening',    'Air',      (255, 230, 153), 'stator'),
    'rotor_core':    ('Rotor Lam (Back Iron)',   'M19_29G',  (204, 136, 68),  'rotor'),
    'magnet':        ('Magnet',                 'N42SH',    (204, 51, 51),   'rotor'),
    'air_barrier':   ('Air',                    'Air',      (210, 210, 210), 'rotor'),
    'shaft':         ('Shaft',                  'Steel',    (139, 139, 139), 'rotor'),
    'airgap':        ('Airgap',                 'Air',      (240, 240, 240), 'rotor'),
}


def _face_edges_to_mc_entities(fi: Dict, edge_to_entity: Dict,
                               origin: Tuple[float, float] = (0.0, 0.0)) -> List:
    """
    face의 edge 정보를 Motor-CAD Line/Arc 엔티티 리스트로 변환합니다.
    
    Parameters
    ----------
    fi : Dict
        face 정보
    edge_to_entity : Dict
        edge -> EntityInfo 매핑
    origin : Tuple[float, float]
        원점 좌표
    
    Returns
    -------
    List
        Motor-CAD Line/Arc 엔티티 리스트
    """
    try:
        from ansys.motorcad.core.geometry import Line as MCLine, Arc as MCArc, Coordinate
    except ImportError:
        print("[경고] ansys.motorcad.core를 찾을 수 없습니다. Motor-CAD 변환을 건너뜁니다.")
        return []

    verts = fi['vertices']
    nv = len(verts)
    mc_entities = []

    edge_info = []
    for j in range(nv):
        k0 = verts[j]
        k1 = verts[(j + 1) % nv]
        edge_key = tuple(sorted([k0, k1]))
        ei = edge_to_entity.get(edge_key, None)

        if ei is not None and ei.etype == 'ARC' and ei.center and ei.radius:
            cx, cy = ei.center
            r = ei.radius
            ang0 = math.atan2(k0[1] - cy, k0[0] - cx)
            ang1 = math.atan2(k1[1] - cy, k1[0] - cx)
            p0 = Coordinate(cx + r * math.cos(ang0), cy + r * math.sin(ang0))
            p1 = Coordinate(cx + r * math.cos(ang1), cy + r * math.sin(ang1))
            edge_info.append(('arc', p0, p1, Coordinate(cx, cy)))
        else:
            p0 = Coordinate(k0[0], k0[1])
            p1 = Coordinate(k1[0], k1[1])
            edge_info.append(('line', p0, p1, None))

    # Chain stitching
    for j in range(nv):
        j_next = (j + 1) % nv
        _, _, end_j, _ = edge_info[j]
        _, start_next, _, _ = edge_info[j_next]
        avg = Coordinate((end_j.x + start_next.x) / 2,
                         (end_j.y + start_next.y) / 2)
        
        etype_j, s_j, _, c_j = edge_info[j]
        if etype_j == 'arc' and c_j is not None:
            r_j = abs(s_j - c_j)
            ang = math.atan2(avg.y - c_j.y, avg.x - c_j.x)
            avg_on_arc_j = Coordinate(c_j.x + r_j * math.cos(ang),
                                       c_j.y + r_j * math.sin(ang))
            edge_info[j] = (etype_j, s_j, avg_on_arc_j, c_j)
        else:
            edge_info[j] = (etype_j, s_j, avg, c_j)

        etype_next, _, e_next, c_next = edge_info[j_next]
        if etype_next == 'arc' and c_next is not None:
            ref_pt = edge_info[j][2]
            ang = math.atan2(ref_pt.y - c_next.y, ref_pt.x - c_next.x)
            r_next = abs(Coordinate(0, 0) - c_next) if c_next else 1
            start_on_arc = Coordinate(c_next.x + r_next * math.cos(ang),
                                       c_next.y + r_next * math.sin(ang))
            edge_info[j_next] = (etype_next, start_on_arc, e_next, c_next)
        else:
            edge_info[j_next] = (etype_next, edge_info[j][2], e_next, c_next)

    # Motor-CAD 엔티티 생성
    for etype, start, end, centre in edge_info:
        if etype == 'arc':
            try:
                mc_entities.append(MCArc(start, end, centre=centre))
            except Exception:
                mc_entities.append(MCLine(start, end))
        else:
            mc_entities.append(MCLine(start, end))

    return mc_entities


def faces_to_motorcad_regions(result: Dict,
                              half_unit_regions: Optional[Dict] = None,
                              scope_filter: Optional[str] = None) -> List:
    """
    analyze_motor_dxf 결과의 face dict들을 Motor-CAD Region 객체 리스트로 변환합니다.
    
    Parameters
    ----------
    result : Dict
        analyze_motor_dxf() 반환값
    half_unit_regions : Dict or None
        편집된 regions. None이면 result에서 가져옴.
    scope_filter : str or None
        'half', 'period', None(전부)
    
    Returns
    -------
    List
        Motor-CAD Region 객체 리스트
    """
    try:
        from ansys.motorcad.core.geometry import Region, RegionType, EntityList
    except ImportError:
        print("[오류] ansys.motorcad.core를 찾을 수 없습니다.")
        return []

    hur = half_unit_regions or result['half_unit_regions']
    all_faces = hur['stator_faces'] + hur['rotor_faces']
    emap = hur.get('stator_edge_map', {})
    emap_r = hur.get('rotor_edge_map', emap)

    origin = result['origins']['best_origin']
    ps = result['poles_slots']
    n_slots = ps['n_slots']
    n_poles = ps['n_poles']
    period_deg = result['periodicity']['period_deg']
    n_periods = max(1, round(360.0 / period_deg))

    mc_regions = []
    name_counters = {}

    for fi in all_faces:
        rname = fi.get('name', 'unknown')
        scope = fi.get('scope', 'half')
        part = fi.get('part', 'rotor')

        if scope_filter and scope != scope_filter:
            continue

        mapping = REGION_TYPE_MAP.get(rname, ('Unknown', 'Air', (200, 200, 200), part))
        mc_label_base, material, colour, _ = mapping

        # RegionType 결정
        if rname in ('stator_yoke', 'stator_tooth'):
            rt = RegionType.stator
        elif rname in ('slot', 'slot_opening'):
            rt = RegionType.slot_area_stator
        elif rname in ('rotor_core',):
            rt = RegionType.rotor
        elif rname == 'magnet':
            rt = RegionType.magnet
        elif rname == 'air_barrier':
            rt = RegionType.rotor_pocket
        elif rname == 'shaft':
            rt = RegionType.shaft
        elif rname == 'airgap':
            rt = RegionType.airgap
        else:
            rt = RegionType.adaptive

        name_counters[rname] = name_counters.get(rname, 0) + 1
        idx = name_counters[rname]
        mc_name = f"DXF_{mc_label_base}_{idx}"

        # Duplications 결정
        if scope == 'half':
            if part == 'stator':
                duplications = n_slots
            else:
                duplications = n_poles
        else:
            duplications = n_periods

        em = emap_r if part == 'rotor' else emap
        mc_ents = _face_edges_to_mc_entities(fi, em, origin)

        region = Region(region_type=rt)
        region.name = mc_name
        region.material = material
        region.colour = colour
        region.duplications = duplications
        for ent in mc_ents:
            region.add_entity(ent)

        region._dxf_face = fi
        region._dxf_scope = scope
        region._dxf_part = part
        region._dxf_region_name = rname

        mc_regions.append(region)

    return mc_regions


def apply_regions_to_motorcad(mc_regions: List,
                              mc=None,
                              open_new_instance: bool = False,
                              parent_stator_name: str = 'Stator',
                              parent_rotor_name: str = 'Rotor'):
    """
    faces_to_motorcad_regions()로 만든 Region 리스트를 Motor-CAD에 적용합니다.
    
    Parameters
    ----------
    mc_regions : List
        Motor-CAD Region 객체 리스트
    mc : MotorCAD instance or None
        기존 Motor-CAD 연결. None이면 새로 연결.
    open_new_instance : bool
        Motor-CAD 새 인스턴스 열기
    parent_stator_name, parent_rotor_name : str
        부모 region 이름
    
    Returns
    -------
    MotorCAD instance
    """
    try:
        import ansys.motorcad.core as pymotorcad
    except ImportError:
        print("[오류] ansys.motorcad.core를 찾을 수 없습니다.")
        return None

    if mc is None:
        mc = pymotorcad.MotorCAD(open_new_instance=open_new_instance)
    mc.set_variable("MessageDisplayState", 2)

    mc.reset_adaptive_geometry()

    try:
        parent_stator = mc.get_region(parent_stator_name)
    except Exception:
        parent_stator = None
        print(f"[경고] '{parent_stator_name}' region을 찾을 수 없습니다")
    try:
        parent_rotor = mc.get_region(parent_rotor_name)
    except Exception:
        parent_rotor = None
        print(f"[경고] '{parent_rotor_name}' region을 찾을 수 없습니다")

    success = 0
    fail = 0
    for region in mc_regions:
        part = getattr(region, '_dxf_part', 'rotor')
        rname = getattr(region, '_dxf_region_name', 'unknown')

        if part == 'stator' and parent_stator is not None:
            region.parent = parent_stator
        elif part == 'rotor' and parent_rotor is not None:
            region.parent = parent_rotor

        if not region.is_closed():
            print(f"  [SKIP] {region.name}: 닫힌 영역이 아닙니다 ({len(region.entities)} entities)")
            fail += 1
            continue

        try:
            mc.set_region(region)
            print(f"  [OK] {region.name}  (type={rname}, dupl={region.duplications})")
            success += 1
        except Exception as e:
            print(f"  [FAIL] {region.name}: {e}")
            fail += 1

    print(f"\n[apply_regions_to_motorcad] 완료: {success} 성공, {fail} 실패")
    return mc


def export_regions_summary(mc_regions: List) -> None:
    """Motor-CAD Region 리스트의 요약 테이블을 출력합니다."""
    print(f"{'Name':<35s} {'Type':<15s} {'Material':<12s} "
          f"{'Dupl':>5s} {'Scope':<7s} {'Closed':>6s} {'Ents':>5s}")
    print('-' * 95)
    for r in mc_regions:
        rname = getattr(r, '_dxf_region_name', '?')
        scope = getattr(r, '_dxf_scope', '?')
        closed = 'Yes' if r.is_closed() else 'NO'
        print(f"{r.name:<35s} {rname:<15s} {r.material:<12s} "
              f"{r.duplications:>5d} {scope:<7s} {closed:>6s} {len(r.entities):>5d}")
