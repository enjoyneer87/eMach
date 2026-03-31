"""
pyMotorGeo.topology_stator
===========================
스테이터 토폴로지 분석: 슬롯/티스/요크/슬롯오프닝/컨덕터 영역 분류.

반슬롯(half-slot) 또는 1-슬롯 재구성 엔티티에서 영역을 자동 분류합니다.
GUI 재지정 지원.
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
    ox, oy = origin
    return [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]


def _entity_avg_angle(ei: EntityInfo,
                      origin: Tuple[float, float]) -> float:
    ox, oy = origin
    if not ei.points:
        return 0.0
    angles = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360
              for p in ei.points]
    return float(np.mean(angles))


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
    """
    한 슬롯 영역의 스테이터 엔티티들을 분류합니다.

    Parameters
    ----------
    slot_entities : [{'entity': EntityInfo, ...}, ...]
    origin : 원점
    airgap_r : 에어갭 반경 (inner rotor = 스테이터 내경 쪽)
    r_outer : 스테이터 외경
    slot_pitch_deg : 슬롯 피치
    verbose : 상세 출력

    Returns
    -------
    Dict : regions (tagged entities), slot_depth, tooth_width, ...
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
    """특정 엔티티의 영역 이름을 재지정합니다."""
    if 0 <= entity_index < len(regions):
        regions[entity_index]['region'] = new_region
    return regions


def get_stator_region_summary(regions: List[Dict]) -> Dict:
    """영역별 엔티티 수 요약."""
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
    1) 기존 엔티티로 분류
    2) 한 슬롯 경계를 닫아 face 생성 후 재분류
    3) 두 결과를 상세 비교
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
