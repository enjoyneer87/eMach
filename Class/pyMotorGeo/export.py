"""
pyMotorGeo.export
=================

Export motor geometry analysis results to CAD formats (DXF).

This module provides utilities to save analyzed motor geometry and classified regions 
back to DXF files, with support for standard DXF and simulation tool-specific formats 
(e.g., ANSYS Maxwell). Region colors and layers are preserved for visualization in CAD editors.

**Export Modes**:

- **Coverage**: Control which parts of the motor are exported
  - 'period': Single periodic sector (default)
  - 'full': Complete motor with all poles/slots
  
- **Filtering**: Include/exclude regions by type or name
  - part_filter: Export stator or rotor only
  - name_filter: Include specific region types (magnet, slot, conductor, etc.)

**Target Tools**:
- ANSYS Maxwell FEA: Maxwell-compatible DXF with special layer naming
- Standard CAD: AutoCAD, LibreCAD, etc. via standard DXF format
- Manufacturing: Layer-based export for CNC toolpath generation
"""

import math
import ezdxf
import os
from typing import Dict, List, Optional, Tuple

from .regions import SHORT_NAMES


def export_regions_to_dxf(result: Dict,
                          half_unit_regions: Optional[Dict] = None,
                          output_path: Optional[str] = None,
                          coverage: str = 'period',
                          part_filter: Optional[str] = None,
                          name_filter: Optional[List[str]] = None,
                          include_labels: bool = True,
                          layer_by_name: bool = True) -> str:
    """
    인식된 영역을 DXF 파일로 내보냅니다.
    
    Parameters
    ----------
    result : Dict
        analyze_motor_dxf() 반환값
    half_unit_regions : Dict or None
        편집된 regions. None이면 result에서 가져옴.
    output_path : str or None
        출력 DXF 경로. None이면 자동 생성.
    coverage : str
        'half_slot', 'half_pole', 'slot', 'pole', 'period', 'full'
    part_filter : str or None
        'stator', 'rotor', None(전부)
    name_filter : List[str] or None
        특정 region name만 내보내기
    include_labels : bool
        영역 중심에 이름 텍스트 추가
    layer_by_name : bool
        True면 region name별로 레이어 분리
    
    Returns
    -------
    str
        생성된 DXF 파일 경로
    """
    hur = half_unit_regions or result['half_unit_regions']
    origin = result['origins']['best_origin']
    ox, oy = origin
    
    half_unit = result['half_unit']
    ps = result['poles_slots']
    period_deg = result['periodicity']['period_deg']
    
    half_slot_deg = half_unit['half_slot_deg']
    half_pole_deg = half_unit['half_pole_deg']
    slot_pitch = half_unit['slot_pitch_deg']
    pole_pitch = half_unit['pole_pitch_deg']
    ref_start = half_unit['ref_angle_start']
    
    n_slots = ps['n_slots']
    n_poles = ps['n_poles']
    n_periods = max(1, round(360.0 / period_deg))

    coverage_map = {
        'half_slot': (1, 0, half_slot_deg, 'stator'),
        'half_pole': (1, 0, half_pole_deg, 'rotor'),
        'slot': (1, 0, slot_pitch, 'stator'),
        'pole': (1, 0, pole_pitch, 'rotor'),
        'period': (1, 0, period_deg, None),
        'full': (n_periods, period_deg, 360.0, None),
    }
    
    if coverage not in coverage_map:
        raise ValueError(f"coverage must be one of {list(coverage_map.keys())}")
    
    n_copies, copy_step_deg, total_deg, default_part = coverage_map[coverage]
    
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(result['doc'].filename))[0]
        output_path = f"{base_name}_{coverage}.dxf"
    
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    layer_colors = {
        'stator_yoke': 5, 'stator_tooth': 4, 'slot': 2, 'slot_opening': 3,
        'rotor_core': 30, 'magnet': 1, 'air_barrier': 8, 'shaft': 9, 'airgap': 7, 'unknown': 7,
    }
    
    for name, color in layer_colors.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color)
    
    all_faces = hur['stator_faces'] + hur['rotor_faces']
    emap = hur.get('stator_edge_map', {})
    emap_r = hur.get('rotor_edge_map', emap)
    
    if part_filter:
        all_faces = [f for f in all_faces if f.get('part') == part_filter]
    if name_filter:
        all_faces = [f for f in all_faces if f.get('name') in name_filter]
    
    if coverage in ('half_slot', 'slot'):
        all_faces = [f for f in all_faces 
                     if f.get('part') == 'stator' and f.get('scope') == 'half']
    elif coverage in ('half_pole', 'pole'):
        all_faces = [f for f in all_faces 
                     if f.get('part') == 'rotor' and f.get('scope') == 'half']
    
    def _transform_point(x, y, angle_deg):
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        dx, dy = x - ox, y - oy
        nx = ox + dx * cos_a - dy * sin_a
        ny = oy + dx * sin_a + dy * cos_a
        return nx, ny
    
    def _mirror_point_axis(x, y, axis_deg):
        rad = math.radians(axis_deg)
        cos_2a = math.cos(2 * rad)
        sin_2a = math.sin(2 * rad)
        dx, dy = x - ox, y - oy
        nx = ox + dx * cos_2a + dy * sin_2a
        ny = oy + dx * sin_2a - dy * cos_2a
        return nx, ny
    
    def _draw_face_to_dxf(fi, em, transform_fn=None, copy_idx=0):
        verts = fi['vertices']
        nv = len(verts)
        rname = fi.get('name', 'unknown')
        layer = rname if layer_by_name else '0'
        
        for j in range(nv):
            k0 = verts[j]
            k1 = verts[(j + 1) % nv]
            edge_key = tuple(sorted([k0, k1]))
            ei = em.get(edge_key, None)
            
            if transform_fn:
                p0 = transform_fn(k0[0], k0[1])
                p1 = transform_fn(k1[0], k1[1])
            else:
                p0, p1 = k0, k1
            
            if ei is not None and ei.etype == 'ARC' and ei.center and ei.radius:
                cx, cy = ei.center
                r = ei.radius
                if transform_fn:
                    c_new = transform_fn(cx, cy)
                else:
                    c_new = (cx, cy)
                
                ang0 = math.degrees(math.atan2(p0[1] - c_new[1], p0[0] - c_new[0]))
                ang1 = math.degrees(math.atan2(p1[1] - c_new[1], p1[0] - c_new[0]))
                
                if ang0 < 0: ang0 += 360
                if ang1 < 0: ang1 += 360
                
                orig_sa = ei.start_angle
                orig_ea = ei.end_angle
                if orig_ea < orig_sa:
                    orig_ea += 360
                orig_span = orig_ea - orig_sa
                
                if orig_span <= 180:
                    if ang1 < ang0:
                        ang1 += 360
                else:
                    if ang0 < ang1:
                        ang0 += 360
                
                msp.add_arc(c_new, r, ang0, ang1, dxfattribs={'layer': layer})
            else:
                msp.add_line(p0, p1, dxfattribs={'layer': layer})
        
        if include_labels and copy_idx == 0:
            cx = sum(v[0] for v in verts) / nv
            cy = sum(v[1] for v in verts) / nv
            if transform_fn:
                cx, cy = transform_fn(cx, cy)
            label = SHORT_NAMES.get(rname, rname[:4])
            msp.add_text(label, height=1.5, 
                        dxfattribs={'layer': layer, 'insert': (cx, cy)})
    
    mirror_s_axis = ref_start + half_slot_deg
    mirror_r_axis = ref_start + half_pole_deg
    
    for copy_i in range(n_copies):
        base_angle = copy_i * copy_step_deg
        
        for fi in all_faces:
            scope = fi.get('scope', 'half')
            part = fi.get('part', 'stator')
            em = emap_r if part == 'rotor' else emap
            
            if scope == 'half':
                if coverage in ('half_slot', 'half_pole'):
                    if base_angle == 0:
                        _draw_face_to_dxf(fi, em, None, copy_i)
                    else:
                        tf = lambda x, y, a=base_angle: _transform_point(x, y, a)
                        _draw_face_to_dxf(fi, em, tf, copy_i)
                else:
                    if part == 'stator':
                        n_unit = max(1, round(total_deg / slot_pitch))
                        unit_pitch = slot_pitch
                        mirror_axis = mirror_s_axis
                    else:
                        n_unit = max(1, round(total_deg / pole_pitch))
                        unit_pitch = pole_pitch
                        mirror_axis = mirror_r_axis
                    
                    for u in range(n_unit):
                        rot_angle = base_angle + u * unit_pitch
                        if rot_angle == 0:
                            _draw_face_to_dxf(fi, em, None, copy_i)
                        else:
                            tf = lambda x, y, a=rot_angle: _transform_point(x, y, a)
                            _draw_face_to_dxf(fi, em, tf, copy_i)
                        def mirror_then_rotate(x, y, ma=mirror_axis, ra=rot_angle):
                            mx, my = _mirror_point_axis(x, y, ma)
                            return _transform_point(mx, my, ra)
                        _draw_face_to_dxf(fi, em, mirror_then_rotate, copy_i)
            
            else:
                if coverage in ('half_slot', 'half_pole', 'slot', 'pole'):
                    continue
                
                n_period_copies = max(1, round(total_deg / period_deg))
                for p in range(n_period_copies):
                    rot_angle = base_angle + p * period_deg
                    if rot_angle == 0:
                        _draw_face_to_dxf(fi, em, None, copy_i)
                    else:
                        tf = lambda x, y, a=rot_angle: _transform_point(x, y, a)
                        _draw_face_to_dxf(fi, em, tf, copy_i)
    
    doc.saveas(output_path)
    
    print(f"\n[export_regions_to_dxf] DXF 내보내기 완료")
    print(f"  출력 파일  : {output_path}")
    print(f"  coverage   : {coverage} ({total_deg:.1f}°)")
    print(f"  영역 개수  : {len(all_faces)}")
    
    return output_path


def export_regions_to_dxf_maxwell(result: Dict,
                                  half_unit_regions: Optional[Dict] = None,
                                  output_path: Optional[str] = None,
                                  coverage: str = 'period',
                                  part_filter: Optional[str] = None,
                                  name_filter: Optional[List[str]] = None,
                                  layer_by_name: bool = True) -> str:
    """
    ANSYS Maxwell에서 import 가능한 형식으로 영역을 DXF로 내보냅니다.
    각 영역을 닫힌 폴리라인(LWPOLYLINE)으로 내보내며, 텍스트 라벨은 제외합니다.
    
    Parameters
    ----------
    result : Dict
        analyze_motor_dxf() 반환값
    half_unit_regions : Dict or None
        편집된 regions. None이면 result에서 가져옴.
    output_path : str or None
        출력 DXF 경로. None이면 자동 생성.
    coverage : str
        'half_slot', 'half_pole', 'slot', 'pole', 'period', 'full'
    part_filter : str or None
        'stator', 'rotor', None(전부)
    name_filter : List[str] or None
        특정 region name만 내보내기
    layer_by_name : bool
        True면 region name별로 레이어 분리
    
    Returns
    -------
    str
        생성된 DXF 파일 경로
    """
    hur = half_unit_regions or result['half_unit_regions']
    origin = result['origins']['best_origin']
    ox, oy = origin
    
    half_unit = result['half_unit']
    ps = result['poles_slots']
    period_deg = result['periodicity']['period_deg']
    
    half_slot_deg = half_unit['half_slot_deg']
    half_pole_deg = half_unit['half_pole_deg']
    slot_pitch = half_unit['slot_pitch_deg']
    pole_pitch = half_unit['pole_pitch_deg']
    ref_start = half_unit['ref_angle_start']
    
    n_slots = ps['n_slots']
    n_poles = ps['n_poles']
    n_periods = max(1, round(360.0 / period_deg))

    coverage_map = {
        'half_slot': (1, 0, half_slot_deg, 'stator'),
        'half_pole': (1, 0, half_pole_deg, 'rotor'),
        'slot': (1, 0, slot_pitch, 'stator'),
        'pole': (1, 0, pole_pitch, 'rotor'),
        'period': (1, 0, period_deg, None),
        'full': (n_periods, period_deg, 360.0, None),
    }
    
    if coverage not in coverage_map:
        raise ValueError(f"coverage must be one of {list(coverage_map.keys())}")
    
    n_copies, copy_step_deg, total_deg, default_part = coverage_map[coverage]
    
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(result['doc'].filename))[0]
        output_path = f"{base_name}_{coverage}_maxwell.dxf"
    
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    layer_colors = {
        'stator_yoke': 5, 'stator_tooth': 4, 'slot': 2, 'slot_opening': 3,
        'rotor_core': 30, 'magnet': 1, 'air_barrier': 8, 'shaft': 9, 'airgap': 7, 'unknown': 7,
    }
    
    for name, color in layer_colors.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color)
    
    all_faces = hur['stator_faces'] + hur['rotor_faces']
    emap = hur.get('stator_edge_map', {})
    emap_r = hur.get('rotor_edge_map', emap)
    
    if part_filter:
        all_faces = [f for f in all_faces if f.get('part') == part_filter]
    if name_filter:
        all_faces = [f for f in all_faces if f.get('name') in name_filter]
    
    if coverage in ('half_slot', 'slot'):
        all_faces = [f for f in all_faces 
                     if f.get('part') == 'stator' and f.get('scope') == 'half']
    elif coverage in ('half_pole', 'pole'):
        all_faces = [f for f in all_faces 
                     if f.get('part') == 'rotor' and f.get('scope') == 'half']
    
    def _transform_point(x, y, angle_deg):
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        dx, dy = x - ox, y - oy
        return ox + dx * cos_a - dy * sin_a, oy + dx * sin_a + dy * cos_a
    
    def _mirror_point_axis(x, y, axis_deg):
        rad = math.radians(axis_deg)
        cos_2a, sin_2a = math.cos(2 * rad), math.sin(2 * rad)
        dx, dy = x - ox, y - oy
        return ox + dx * cos_2a + dy * sin_2a, oy + dx * sin_2a - dy * cos_2a
    
    def _face_to_polyline_points(fi, em, transform_fn=None):
        verts = fi['vertices']
        nv = len(verts)
        points_with_bulge = []
        
        for j in range(nv):
            k0 = verts[j]
            k1 = verts[(j + 1) % nv]
            edge_key = tuple(sorted([k0, k1]))
            ei = em.get(edge_key, None)
            
            if transform_fn:
                p0 = transform_fn(k0[0], k0[1])
                p1 = transform_fn(k1[0], k1[1])
            else:
                p0, p1 = k0, k1
            
            if ei is not None and ei.etype == 'ARC' and ei.center and ei.radius:
                cx, cy = ei.center
                r = ei.radius
                if transform_fn:
                    c_new = transform_fn(cx, cy)
                else:
                    c_new = (cx, cy)
                
                ang0 = math.atan2(p0[1] - c_new[1], p0[0] - c_new[0])
                ang1 = math.atan2(p1[1] - c_new[1], p1[0] - c_new[0])
                
                delta = ang1 - ang0
                if delta > math.pi:
                    delta -= 2 * math.pi
                elif delta < -math.pi:
                    delta += 2 * math.pi
                
                bulge = math.tan(delta / 4)
                points_with_bulge.append((p0[0], p0[1], 0, 0, bulge))
            else:
                points_with_bulge.append((p0[0], p0[1], 0, 0, 0))
        
        return points_with_bulge
    
    def _draw_face_as_polyline(fi, em, transform_fn=None):
        rname = fi.get('name', 'unknown')
        layer = rname if layer_by_name else '0'
        
        points_with_bulge = _face_to_polyline_points(fi, em, transform_fn)
        
        if len(points_with_bulge) < 3:
            return
        
        msp.add_lwpolyline(
            points_with_bulge,
            close=True,
            dxfattribs={'layer': layer},
            format='xyseb'
        )
    
    region_count = 0
    mirror_s_axis = ref_start + half_slot_deg
    mirror_r_axis = ref_start + half_pole_deg
    
    for copy_i in range(n_copies):
        base_angle = copy_i * copy_step_deg
        
        for fi in all_faces:
            scope = fi.get('scope', 'half')
            part = fi.get('part', 'stator')
            em = emap_r if part == 'rotor' else emap
            
            if scope == 'half':
                if coverage in ('half_slot', 'half_pole'):
                    if base_angle == 0:
                        _draw_face_as_polyline(fi, em, None)
                        region_count += 1
                    else:
                        tf = lambda x, y, a=base_angle: _transform_point(x, y, a)
                        _draw_face_as_polyline(fi, em, tf)
                        region_count += 1
                else:
                    if part == 'stator':
                        n_unit = max(1, round(total_deg / slot_pitch))
                        unit_pitch = slot_pitch
                        mirror_axis = mirror_s_axis
                    else:
                        n_unit = max(1, round(total_deg / pole_pitch))
                        unit_pitch = pole_pitch
                        mirror_axis = mirror_r_axis
                    
                    for u in range(n_unit):
                        rot_angle = base_angle + u * unit_pitch
                        if rot_angle == 0:
                            _draw_face_as_polyline(fi, em, None)
                        else:
                            tf = lambda x, y, a=rot_angle: _transform_point(x, y, a)
                            _draw_face_as_polyline(fi, em, tf)
                        region_count += 1
                        
                        def mirror_then_rotate(x, y, ma=mirror_axis, ra=rot_angle):
                            mx, my = _mirror_point_axis(x, y, ma)
                            return _transform_point(mx, my, ra)
                        _draw_face_as_polyline(fi, em, mirror_then_rotate)
                        region_count += 1
            
            else:
                if coverage in ('half_slot', 'half_pole', 'slot', 'pole'):
                    continue
                
                n_period_copies = max(1, round(total_deg / period_deg))
                for p in range(n_period_copies):
                    rot_angle = base_angle + p * period_deg
                    if rot_angle == 0:
                        _draw_face_as_polyline(fi, em, None)
                    else:
                        tf = lambda x, y, a=rot_angle: _transform_point(x, y, a)
                        _draw_face_as_polyline(fi, em, tf)
                    region_count += 1
    
    doc.saveas(output_path)
    
    print(f"\n[export_regions_to_dxf_maxwell] ANSYS Maxwell용 DXF 내보내기 완료")
    print(f"  출력 파일  : {output_path}")
    print(f"  coverage   : {coverage} ({total_deg:.1f}°)")
    print(f"  폴리라인 수: {region_count}")
    
    return output_path
