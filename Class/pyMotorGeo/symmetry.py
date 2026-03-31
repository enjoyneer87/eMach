"""
pyMotorGeo.symmetry
===================

Motor symmetry analysis, periodic pattern reconstruction, and minimum repeating unit extraction.

This module provides tools for:
- **Symmetry Detection**: Identify rotational and mirror symmetries in motor geometry
- **Periodic Pattern Analysis**: Extract minimum repeating units (half-pole, quarter-pole, full-pole)
- **Geometry Reconstruction**: Expand minimum units back to full motor via rotation and mirroring
- **Symmetry Breaking**: Detect and report asymmetries (useful for motor design validation)

**Key Concepts**:

- **Minimum Repeating Unit (MRU)**: Smallest sector that, when rotated/mirrored, reconstructs the motor
  - Half-pole: 180°/poles (often used for symmetric rotor)
  - Quarter-pole: 90°/poles (for doubly-symmetric designs)
  - Full-pole: 360°/poles (no symmetry; sector is the pole itself)
  
- **Symmetry Types**:
  - **Rotational**: Motor pattern repeats every `period_deg`
  - **Mirror/Bilateral**: Motor is symmetric about a radial plane (0°-180° line, etc.)

- **Use Cases**:
  - Reduce CAD model complexity by storing only MRU
  - Speed up FEA analysis by exploiting symmetry
  - Validate motor design (e.g., ensure 4-pole motor has 4-fold symmetry)
  - Reconstruct full motor for visualization or export

**Typical Workflow**:

1. Load full motor geometry from DXF
2. Detect period/symmetry via `identify_symmetry()` or user specification
3. Extract MRU: `extract_half_pole_entities()` or similar
4. Perform analysis on MRU (lighter computation)
5. Reconstruct full motor for visualization: `expand_sector()` or `reconstruct_from_half()`
"""

import math
import numpy as np
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Optional

from .core import (
    EntityInfo, StatorRotorSplit,
    rotate_entity, mirror_entity, entity_angle
)


def identify_symmetry_break(entities: List[EntityInfo],
                            period_deg: float,
                            origin: Tuple[float, float] = (0.0, 0.0),
                            angle_tol: float = 1.0) -> Dict:
    """
    섹터별 엔티티 수를 비교하여 대칭 깨짐을 식별합니다.
    
    Parameters
    ----------
    entities : List[EntityInfo]
        엔티티 리스트
    period_deg : float
        한 주기 각도 (도)
    origin : Tuple[float, float]
        원점 좌표
    angle_tol : float
        각도 허용 오차
    
    Returns
    -------
    Dict
        broken_sectors, sector_counts, reference_sector, n_sectors
    """
    ox, oy = origin
    n_sectors = max(1, round(360.0 / period_deg))
    sector_counts = Counter()
    sector_entities = defaultdict(list)

    for ei in entities:
        a = ei.angle_deg
        if ei.center:
            a = math.degrees(math.atan2(ei.center[1] - oy, ei.center[0] - ox)) % 360
        sector_idx = int(a // period_deg) % n_sectors
        sector_counts[sector_idx] += 1
        sector_entities[sector_idx].append(ei)

    if not sector_counts:
        return {'broken_sectors': [], 'sector_counts': {}, 'reference_sector': 0}

    ref_sector = sector_counts.most_common(1)[0][0]
    ref_count = sector_counts[ref_sector]

    broken = []
    for s in range(n_sectors):
        c = sector_counts.get(s, 0)
        if abs(c - ref_count) > 1:
            broken.append({'sector': s, 'angle_start': s * period_deg,
                           'angle_end': (s + 1) * period_deg,
                           'count': c, 'expected': ref_count})

    result = {
        'broken_sectors': broken,
        'sector_counts': dict(sector_counts),
        'reference_sector': ref_sector,
        'n_sectors': n_sectors,
    }
    print(f'[identify_symmetry_break] {len(broken)} broken sectors out of {n_sectors}')
    if broken:
        for b in broken:
            print(f'  sector {b["sector"]}: {b["angle_start"]:.1f}°~{b["angle_end"]:.1f}° '
                  f'count={b["count"]} (expected {b["expected"]})')
    return result


def extract_one_period(entities: List[EntityInfo],
                       period_deg: float,
                       reference_sector: int = 0,
                       origin: Tuple[float, float] = (0.0, 0.0)) -> List[EntityInfo]:
    """
    한 주기(reference_sector)에 해당하는 엔티티만 추출합니다.
    
    Parameters
    ----------
    entities : List[EntityInfo]
        엔티티 리스트
    period_deg : float
        한 주기 각도 (도)
    reference_sector : int
        추출할 섹터 번호
    origin : Tuple[float, float]
        원점 좌표
    
    Returns
    -------
    List[EntityInfo]
        한 주기 엔티티 리스트
    """
    ox, oy = origin
    ang_start = reference_sector * period_deg
    ang_end = ang_start + period_deg

    one_period = []
    for ei in entities:
        a = ei.angle_deg
        if ei.center:
            a = math.degrees(math.atan2(ei.center[1] - oy, ei.center[0] - ox)) % 360
        if ei.etype == 'CIRCLE' and ei.center:
            d = math.hypot(ei.center[0] - ox, ei.center[1] - oy)
            if d < 1e-3:
                one_period.append(ei)
                continue
        if ang_start <= a < ang_end:
            one_period.append(ei)

    print(f'[extract_one_period] sector {reference_sector} '
          f'({ang_start:.1f}°~{ang_end:.1f}°): {len(one_period)} entities')
    return one_period


def extract_half_unit(entities: List[EntityInfo],
                      split: StatorRotorSplit,
                      poles_slots: Dict,
                      periodicity: Dict,
                      origin: Tuple[float, float] = (0.0, 0.0)) -> Dict:
    """
    최소 반복 단위(반슬롯 고정자 + 반극 회전자)를 추출합니다.
    
    Parameters
    ----------
    entities : List[EntityInfo]
        전체 엔티티 리스트
    split : StatorRotorSplit
        고정자/회전자 분리 결과
    poles_slots : Dict
        극수/슬롯수 정보
    periodicity : Dict
        주기성 분석 결과
    origin : Tuple[float, float]
        원점 좌표
    
    Returns
    -------
    Dict
        half_slot_stator, half_pole_rotor, concentric_circles,
        half_slot_deg, half_pole_deg, slot_pitch_deg, pole_pitch_deg,
        ref_angle_start
    """
    ox, oy = origin
    n_poles = poles_slots['n_poles']
    n_slots = poles_slots['n_slots']

    slot_pitch = 360.0 / n_slots if n_slots > 0 else 10.0
    pole_pitch = 360.0 / n_poles if n_poles > 0 else 45.0
    half_slot = slot_pitch / 2.0
    half_pole = pole_pitch / 2.0

    sym = identify_symmetry_break(entities, periodicity['period_deg'], origin)
    ref_sector = sym['reference_sector']
    ref_start = ref_sector * periodicity['period_deg']

    # 동심원 분리
    concentric = []
    stator_non_conc = []
    rotor_non_conc = []

    for ei in split.stator_entities:
        if (ei.etype in ('CIRCLE', 'ARC') and ei.center
                and math.hypot(ei.center[0] - ox, ei.center[1] - oy) < 1e-3):
            concentric.append(ei)
        else:
            stator_non_conc.append(ei)

    for ei in split.rotor_entities:
        if (ei.etype in ('CIRCLE', 'ARC') and ei.center
                and math.hypot(ei.center[0] - ox, ei.center[1] - oy) < 1e-3):
            concentric.append(ei)
        else:
            rotor_non_conc.append(ei)

    # 반슬롯/반극 추출
    ang_s = ref_start
    ang_e = ref_start + half_slot

    def _in_sector(ei, a_start, a_end):
        a = entity_angle(ei, origin)
        a_s = a_start % 360
        a_e = a_end % 360
        if a_s < a_e:
            return a_s <= a < a_e
        else:
            return a >= a_s or a < a_e

    half_slot_stator = [ei for ei in stator_non_conc if _in_sector(ei, ang_s, ang_e)]
    half_pole_rotor = [ei for ei in rotor_non_conc if _in_sector(ei, ang_s, ang_s + half_pole)]

    result = {
        'half_slot_stator': half_slot_stator,
        'half_pole_rotor': half_pole_rotor,
        'concentric_circles': concentric,
        'half_slot_deg': half_slot,
        'half_pole_deg': half_pole,
        'slot_pitch_deg': slot_pitch,
        'pole_pitch_deg': pole_pitch,
        'ref_angle_start': ref_start,
    }
    print(f'[extract_half_unit]')
    print(f'  slot_pitch={slot_pitch:.2f}°, half_slot={half_slot:.2f}°')
    print(f'  pole_pitch={pole_pitch:.2f}°, half_pole={half_pole:.2f}°')
    print(f'  half_slot_stator: {len(half_slot_stator)} entities')
    print(f'  half_pole_rotor:  {len(half_pole_rotor)} entities')
    print(f'  concentric:       {len(concentric)} circles')
    return result


def reconstruct_geometry(half_unit: Dict,
                         origin: Tuple[float, float] = (0.0, 0.0),
                         coverage: str = 'period',
                         n_poles: Optional[int] = None,
                         n_slots: Optional[int] = None,
                         period_deg: Optional[float] = None) -> List[EntityInfo]:
    """
    반슬롯/반극 최소 단위에서 mirror + circular pattern으로
    원하는 범위의 기하를 재구성합니다.
    
    Parameters
    ----------
    half_unit : Dict
        extract_half_unit 결과
    origin : Tuple[float, float]
        원점 좌표
    coverage : str
        'period', 'full', 또는 각도 (도)
    n_poles, n_slots : int
        전체 극수/슬롯수
    period_deg : float
        한 주기 각도
    
    Returns
    -------
    List[EntityInfo]
        재구성된 엔티티 리스트
    """
    half_slot_deg = half_unit['half_slot_deg']
    half_pole_deg = half_unit['half_pole_deg']
    slot_pitch = half_unit['slot_pitch_deg']
    pole_pitch = half_unit['pole_pitch_deg']
    ref_start = half_unit['ref_angle_start']

    if coverage == 'full':
        target_deg = 360.0
    elif coverage == 'period':
        target_deg = period_deg if period_deg else 90.0
    else:
        target_deg = float(coverage)

    n_slots_to_build = max(1, round(target_deg / slot_pitch))
    n_poles_to_build = max(1, round(target_deg / pole_pitch))

    result_entities = []

    # 고정자
    half_s = half_unit['half_slot_stator']
    mirror_axis = ref_start + half_slot_deg

    one_slot = list(half_s)
    for ei in half_s:
        mirrored = mirror_entity(ei, mirror_axis, origin)
        one_slot.append(mirrored)

    for i in range(n_slots_to_build):
        rot_angle = i * slot_pitch
        for ei in one_slot:
            if i == 0:
                result_entities.append(ei)
            else:
                rotated = rotate_entity(ei, rot_angle, origin)
                result_entities.append(rotated)

    # 회전자
    half_p = half_unit['half_pole_rotor']
    pole_mirror_axis = ref_start + half_pole_deg

    one_pole = list(half_p)
    for ei in half_p:
        mirrored = mirror_entity(ei, pole_mirror_axis, origin)
        one_pole.append(mirrored)

    for i in range(n_poles_to_build):
        rot_angle = i * pole_pitch
        for ei in one_pole:
            if i == 0:
                result_entities.append(ei)
            else:
                rotated = rotate_entity(ei, rot_angle, origin)
                result_entities.append(rotated)

    # 동심원: CIRCLE은 그대로, ARC는 shaft/rotor 외경 반경만 pole-pitch 각도만큼 확장, 나머지는 원본 각도만 추가
    # shaft/rotor 외경 반경 추출 (가장 작은/큰 반경)
    shaft_r = None
    rotor_outer_r = None
    # CIRCLE 기준으로 shaft/rotor 외경 추정
    circle_radii = [ei.radius for ei in half_unit['concentric_circles'] if ei.etype == 'CIRCLE' and ei.radius]
    if circle_radii:
        shaft_r = min(circle_radii)
        rotor_outer_r = max(circle_radii)
    for ei in half_unit['concentric_circles']:
        if ei.etype == 'CIRCLE':
            result_entities.append(ei)
        elif ei.etype == 'ARC':
            # shaft/rotor 외경 반경이면 pole-pitch 각도만큼 확장 ARC 생성
            if (shaft_r and abs(ei.radius - shaft_r) < 1e-2) or (rotor_outer_r and abs(ei.radius - rotor_outer_r) < 1e-2):
                new_arc = EntityInfo(
                    etype='ARC',
                    layer=ei.layer,
                    points=[],
                    radius=ei.radius,
                    center=ei.center,
                    start_angle=ref_start,
                    end_angle=ref_start + pole_pitch,
                    raw=None,
                )
                cx, cy = new_arc.center
                r = new_arc.radius
                n_pts = max(3, int(pole_pitch / 2))
                pts = []
                for j in range(n_pts + 1):
                    a = math.radians(ref_start + pole_pitch * j / n_pts)
                    pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
                new_arc.points = pts
                result_entities.append(new_arc)
            else:
                # 그 외 ARC는 원본 각도 그대로 추가
                result_entities.append(ei)

    print(f'[reconstruct_geometry] coverage={coverage} ({target_deg:.0f}°)')
    print(f'  stator: {n_slots_to_build} slots × 2×{len(half_s)} = '
          f'{n_slots_to_build * len(half_s) * 2} entities')
    print(f'  rotor:  {n_poles_to_build} poles × 2×{len(half_p)} = '
          f'{n_poles_to_build * len(half_p) * 2} entities')
    print(f'  concentric: {len(half_unit["concentric_circles"])}')
    print(f'  total: {len(result_entities)} entities')
    return result_entities
