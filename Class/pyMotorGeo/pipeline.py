"""
pyMotorGeo.pipeline
===================

High-level analysis pipelines for end-to-end motor geometry processing.

This module provides convenience functions that orchestrate the full pyMotorGeo workflow:

1. **Read** motor geometry from DXF file
2. **Analyze** topology (poles, slots, rotor/stator split, symmetry)
3. **Detect** closed regions and classify them
4. **Export** results (geometry info, region faces, statistics)

**Available Pipelines**:

- **analyze_dxf_v2()**: Recommended v1.5.1+ workflow using topological face closure
  - Modern: Per-pole/slot closure, topological face detection
  - Supports rotor topology (SPM, IPM, SynRM)
  - Outputs faces with region labels, region summary
  
- **analyze_motor_dxf()**: Legacy v1.0 pipeline for backward compatibility
  - Direct region analysis without explicit closure
  - Suitable for motors with already-closed geometry
  
- **quick_analyze()**: Rapid lightweight analysis
  - Minimal processing, basic geometry info only
  - Best for quick validation or batch checking

**End-to-End Usage Example**::

    from pyMotorGeo.pipeline import analyze_dxf_v2
    
    result = analyze_dxf_v2(
        dxf_path='motor.dxf',
        n_poles=4,
        n_slots=24,
        rotor_topology='IPMSM'
    )
    
    print(f"Rotor: {result['rotor']['topology']}")
    print(f"Stator: {result['stator']['topology']}")
    print(f"Detected regions: {result['face_summary']}")

**Output Structure**:

The result dictionary contains:

- **'geometry'**: Motor dimensions (radii, stack length, etc.)
- **'rotor'**: Rotor analysis (topology, pole count, magnet/barrier regions)
- **'stator'**: Stator analysis (slot count, conductor regions, tooth geometry)
- **'airgap'**: Airgap boundary and characteristics
- **'faces'**: Detected closed regions with properties
- **'face_summary'**: Summary counts of regions by type
- **'dxf_path'**: Input file reference
- **'errors'**: Any warnings or errors during analysis (empty if successful)

**API Stability**:

- v1.5.1+ recommends `analyze_dxf_v2()` for all new code
- `analyze_motor_dxf()` maintained for backward compatibility
- Internal implementation may change, but v1.5.1 API is frozen
"""

import json
from typing import Dict, List, Optional, Tuple

from .reader import read_entity_list


# ═══════════════════════════════════════════════════════════════
# v1.5.1 파이프라인 (권장)
# ═══════════════════════════════════════════════════════════════

def analyze_dxf_v2(
    dxf_path: str,
    origin: Optional[Tuple[float, float]] = (0.0, 0.0),
    n_poles: Optional[int] = None,
    n_slots: Optional[int] = None,
    enable_radius_fallback: bool = False,
    fallback_r_shaft_mm: Optional[float] = None,
    fallback_r_stator_outer_mm: Optional[float] = None,
    verbose: bool = True,
) -> Dict:
    """
    v1.5.1 권장 워크플로우 — face 기반 1극/1슬롯 분석.

    Parameters
    ----------
    dxf_path  : DXF 파일 경로
    origin    : 회전 원점 (기본 (0,0))
    n_poles   : 극수 강제 지정 (None이면 자동 추정)
    n_slots   : 슬롯수 강제 지정 (None이면 자동 추정)
    enable_radius_fallback : 경계 닫기 반경 fallback 사용 여부
    fallback_r_shaft_mm    : 샤프트 반경 fallback (mm, 선택)
    fallback_r_stator_outer_mm : 스테이터 외경 fallback (mm, 선택)
    verbose   : 진행 상황 출력 여부

    Returns
    -------
    dict
        - dxf_path, origin
        - all_entities
        - airgap          : find_airgap_by_arc_span 결과
        - airgap_r_inner  : float (로터 외경)
        - airgap_r_outer  : float (스테이터 내경)
        - rotor_entities, stator_entities
        - n_poles, n_slots, pole_pitch_deg, slot_pitch_deg
        - half_pole, half_slot
        - one_pole_ents, one_slot_ents
        - pole_result, slot_result    : close_one_pole/slot 결과
        - rotor_faces, stator_faces   : detect_closed_faces 결과
        - rotor_topo                  : classify_rotor_entities 결과
        - r_shaft, r_rotor_outer, r_stator_inner, r_stator_outer
        - dims                        : 치수 요약 dict
        - fallback_info               : fallback 적용 정보
    """
    from .analysis_airgap import find_airgap_by_arc_span, split_stator_rotor_by_arc_span
    from .analysis import classify_inner_outer_rotor, find_concentric_radii
    from .analysis_rotor import estimate_poles_robust
    from .analysis_stator import estimate_slots_robust
    from .half_unit import (extract_half_pole_entities, extract_half_slot_entities,
                            reconstruct_from_half)
    from .region_closing import (close_one_pole, close_one_slot,
                                 detect_closed_faces, auto_name_faces,
                                 auto_name_faces_v2)
    from .face_detection import detect_closed_faces_v2
    from .topology import extract_single_pole_entities, extract_single_slot_entities
    from .topology_rotor import classify_rotor_entities

    def _log(msg):
        if verbose:
            print(msg)

    _log(f"\n{'='*62}")
    _log(f"  pyMotorGeo v1.5.1 — DXF 분석")
    _log(f"{'='*62}")
    _log(f"  파일: {dxf_path}")
    _log(f"{'='*62}")

    # ── 1. DXF 읽기 ──
    _log("[1/8] DXF 파싱 중...")
    all_entities, _ = read_entity_list(dxf_path)
    _log(f"      엔티티 {len(all_entities)}개 로드")

    # ── 2. 에어갭 분석 ──
    _log("[2/8] 에어갭 탐지 중...")
    airgap = find_airgap_by_arc_span(all_entities, origin=origin, verbose=False)
    airgap_r_inner = float(airgap.get('airgap_r_inner') or airgap.get('r_inner', 0))
    airgap_r_outer = float(airgap.get('airgap_r_outer') or airgap.get('r_outer', 0))
    _log(f"      에어갭: {airgap_r_inner:.3f} mm (inner) / {airgap_r_outer:.3f} mm (outer)")

    # ── 3. Stator / Rotor 분리 ──
    _log("[3/8] Stator / Rotor 분리 중...")
    sr = split_stator_rotor_by_arc_span(all_entities, origin=origin, verbose=False)
    rotor_entities  = sr.get('rotor_entities', [])
    stator_entities = sr.get('stator_entities', [])

    split_fallback_used = False
    split_fallback_source = None

    if enable_radius_fallback and (not rotor_entities or not stator_entities):
        motor_type = classify_inner_outer_rotor(all_entities, origin)
        concentric = find_concentric_radii(all_entities, origin)

        if len(concentric) >= 2:
            gaps = [
                (concentric[i + 1] - concentric[i], i)
                for i in range(len(concentric) - 1)
            ]
            min_gap, airgap_idx = min(gaps, key=lambda x: x[0])
            airgap_r = (concentric[airgap_idx] + concentric[airgap_idx + 1]) / 2
            _ = min_gap
        else:
            r_max_all = [ei.r_max for ei in all_entities if ei.r_max]
            airgap_r = float(sum(r_max_all) / len(r_max_all)) if r_max_all else 0.0

        if airgap_r > 0.0:
            if motor_type == 'inner_rotor':
                stator_guess = [ei for ei in all_entities if ei.r_min and ei.r_min > airgap_r * 0.9]
                rotor_guess = [ei for ei in all_entities if ei.r_max and ei.r_max < airgap_r * 1.1]
            else:
                stator_guess = [ei for ei in all_entities if ei.r_max and ei.r_max < airgap_r * 1.1]
                rotor_guess = [ei for ei in all_entities if ei.r_min and ei.r_min > airgap_r * 0.9]

            if rotor_guess and stator_guess:
                rotor_entities = rotor_guess
                stator_entities = stator_guess
                split_fallback_used = True
                split_fallback_source = 'radius_threshold_split'
                _log(
                    f"      [fallback] split: Rotor {len(rotor_entities)}개 / "
                    f"Stator {len(stator_entities)}개"
                )

    _log(f"      Rotor {len(rotor_entities)}개 / Stator {len(stator_entities)}개")

    # ── 4. 극수 / 슬롯수 추정 ──
    _log("[4/8] 극수 / 슬롯수 추정 중...")
    if n_poles is None:
        poles_result = estimate_poles_robust(
            rotor_entities, origin=origin,
            airgap_r_inner=airgap_r_inner, verbose=False)
        n_poles = int(poles_result.get('n_poles', 0))
    if n_slots is None:
        slots_result = estimate_slots_robust(
            stator_entities, origin=origin,
            airgap_r_outer=airgap_r_outer, verbose=False)
        n_slots = int(slots_result.get('n_slots', 0))

    pole_pitch_deg = 360.0 / n_poles if n_poles else 0.0
    slot_pitch_deg = 360.0 / n_slots if n_slots else 0.0
    _log(f"      극수: {n_poles}  슬롯수: {n_slots}")
    _log(f"      극 피치: {pole_pitch_deg:.3f}°  슬롯 피치: {slot_pitch_deg:.3f}°")

    # ── 5. 반극 / 반슬롯 추출 ──
    _log("[5/8] 반극 / 반슬롯 추출 중...")
    half_pole = None
    half_slot = None
    one_pole_ents: List = []
    one_slot_ents: List = []

    if rotor_entities and pole_pitch_deg:
        half_pole = extract_half_pole_entities(
            rotor_entities, origin, pole_pitch_deg=pole_pitch_deg,
            reference_angle=0.0, normalize_to_zero=True,
        )
        one_pole_ents = reconstruct_from_half(half_pole, origin, n_repeats=1)
        _log(f"      반극 엔티티: {len(half_pole['normalized_entities'])}개"
             f"  동심원: {len(half_pole['concentric_arcs'])}개")

    if stator_entities and slot_pitch_deg:
        half_slot = extract_half_slot_entities(
            stator_entities, origin, slot_pitch_deg=slot_pitch_deg,
            n_slots=n_slots, reference_angle=0.0, normalize_to_zero=True,
        )
        one_slot_ents = reconstruct_from_half(half_slot, origin, n_repeats=1)
        _log(f"      반슬롯 엔티티: {len(half_slot['normalized_entities'])}개"
             f"  동심원: {len(half_slot['concentric_arcs'])}개")

    # half-unit 기반 추출이 비는 경우, legacy single-pole/slot 추출로 보완
    if enable_radius_fallback and pole_pitch_deg and not one_pole_ents and rotor_entities:
        legacy_pole = extract_single_pole_entities(
            rotor_entities,
            origin=origin,
            pole_pitch_deg=pole_pitch_deg,
            reference_angle=0.0,
            normalize_to_zero=True,
        )
        one_pole_ents = legacy_pole.get('one_pole_entities', [])
        if one_pole_ents:
            _log(f"      [fallback] legacy 1극 추출: {len(one_pole_ents)}개")

    if enable_radius_fallback and slot_pitch_deg and not one_slot_ents and stator_entities:
        legacy_slot = extract_single_slot_entities(
            stator_entities,
            origin=origin,
            slot_pitch_deg=slot_pitch_deg,
            n_slots=n_slots,
            reference_angle=0.0,
            normalize_to_zero=True,
        )
        one_slot_ents = legacy_slot.get('slot_entities', [])
        if one_slot_ents:
            _log(f"      [fallback] legacy 1슬롯 추출: {len(one_slot_ents)}개")

    # ── 6. 1극 / 1슬롯 닫기 ──
    _log("[6/8] 1극 / 1슬롯 경계 닫기 중...")
    r_shaft = min(
        (ei.r_min for ei in rotor_entities if ei.r_min and ei.r_min > 0),
        default=0.0,
    )
    r_rotor_outer   = airgap_r_inner
    r_stator_inner  = airgap_r_outer
    r_stator_outer  = max(
        (ei.r_max for ei in stator_entities if ei.r_max),
        default=0.0,
    )

    fallback_info = {
        'enabled': bool(enable_radius_fallback),
        'split_fallback_used': split_fallback_used,
        'split_fallback_source': split_fallback_source,
        'r_shaft_applied': False,
        'r_stator_outer_applied': False,
        'r_shaft_source': None,
        'r_stator_outer_source': None,
    }

    if enable_radius_fallback:
        if r_shaft <= 0.0:
            if fallback_r_shaft_mm is not None and fallback_r_shaft_mm > 0.0:
                r_shaft = float(fallback_r_shaft_mm)
                fallback_info['r_shaft_applied'] = True
                fallback_info['r_shaft_source'] = 'user_fallback'
                _log(f"      [fallback] r_shaft <- {r_shaft:.3f} mm (user)")
            elif r_rotor_outer > 0.0:
                # 보수적 기본값: 로터 외경의 30%를 샤프트 반경으로 가정
                r_shaft = float(r_rotor_outer) * 0.30
                fallback_info['r_shaft_applied'] = True
                fallback_info['r_shaft_source'] = 'heuristic_30pct_rotor_outer'
                _log(f"      [fallback] r_shaft <- {r_shaft:.3f} mm (heuristic)")

        if r_stator_outer <= 0.0:
            if fallback_r_stator_outer_mm is not None and fallback_r_stator_outer_mm > 0.0:
                r_stator_outer = float(fallback_r_stator_outer_mm)
                fallback_info['r_stator_outer_applied'] = True
                fallback_info['r_stator_outer_source'] = 'user_fallback'
                _log(f"      [fallback] r_stator_outer <- {r_stator_outer:.3f} mm (user)")
            else:
                outer_candidates = [
                    ei.r_max for ei in stator_entities
                    if ei.r_max and ei.r_max > r_stator_inner
                ]
                if not outer_candidates:
                    outer_candidates = [
                        ei.r_max for ei in all_entities
                        if ei.r_max and ei.r_max > r_stator_inner
                    ]
                if outer_candidates:
                    r_stator_outer = float(max(outer_candidates))
                    fallback_info['r_stator_outer_applied'] = True
                    fallback_info['r_stator_outer_source'] = 'max_outer_candidate'
                    _log(f"      [fallback] r_stator_outer <- {r_stator_outer:.3f} mm (derived)")

    pole_result: Dict = {}
    slot_result: Dict = {}

    if one_pole_ents and pole_pitch_deg and r_shaft and r_rotor_outer:
        pole_result = close_one_pole(
            one_pole_ents, origin,
            pole_pitch_deg=pole_pitch_deg,
            r_shaft=r_shaft,
            r_rotor_outer=r_rotor_outer,
        )
        _log(f"      1극 경계선: {len(pole_result.get('boundaries', []))}개 추가")

    if one_slot_ents and slot_pitch_deg and r_stator_inner and r_stator_outer:
        slot_result = close_one_slot(
            one_slot_ents, origin,
            slot_pitch_deg=slot_pitch_deg,
            r_stator_inner=r_stator_inner,
            r_stator_outer=r_stator_outer,
        )
        _log(f"      1슬롯 경계선: {len(slot_result.get('boundaries', []))}개 추가")

    # ── 7. 닫힌 Face 탐지 + 토폴로지 분류 ──
    _log("[7/8] 닫힌 영역 탐지 + 토폴로지 분류 중...")
    rotor_faces:  List[Dict] = []
    stator_faces: List[Dict] = []
    rotor_topo:   Dict       = {}

    if pole_result.get('closed_entities'):
        rotor_faces = detect_closed_faces(
            pole_result['closed_entities'], origin, min_area=1.0
        )
        if enable_radius_fallback and not rotor_faces:
            rotor_faces = detect_closed_faces_v2(
                pole_result['closed_entities'], origin=origin, min_area=1.0
            )
            if rotor_faces:
                _log(f"      [fallback] 로터 face(v2): {len(rotor_faces)}개")
        _log(f"      로터 face: {len(rotor_faces)}개")

    if slot_result.get('closed_entities'):
        stator_faces = detect_closed_faces(
            slot_result['closed_entities'], origin, min_area=1.0
        )
        if enable_radius_fallback and not stator_faces:
            stator_faces = detect_closed_faces_v2(
                slot_result['closed_entities'], origin=origin, min_area=1.0
            )
            if stator_faces:
                _log(f"      [fallback] 스테이터 face(v2): {len(stator_faces)}개")
        _log(f"      스테이터 face: {len(stator_faces)}개")

    if one_pole_ents:
        one_pole_items = [
            {'entity': ei, 'original_angle': 0.0, 'relative_angle': 0.0}
            for ei in one_pole_ents
        ]
        rotor_topo = classify_rotor_entities(
            one_pole_items, origin,
            airgap_r=float(airgap_r_inner),
            pole_pitch_deg=pole_pitch_deg,
            verbose=False,
        )
        topology = rotor_topo.get('topology', 'UNKNOWN')
        _log(f"      로터 토폴로지: {topology}  ({rotor_topo.get('detail', '')})")

        if rotor_faces and r_shaft and r_rotor_outer:
            if enable_radius_fallback:
                auto_name_faces_v2(
                    rotor_faces, r_shaft, r_rotor_outer,
                    r_stator_inner, r_stator_outer,
                    rotor_topology=topology,
                )
            else:
                auto_name_faces(
                    rotor_faces, r_shaft, r_rotor_outer,
                    r_stator_inner, r_stator_outer,
                    rotor_topology=topology,
                )
        if stator_faces and r_shaft and r_stator_outer:
            if enable_radius_fallback:
                auto_name_faces_v2(
                    stator_faces, r_shaft, r_rotor_outer,
                    r_stator_inner, r_stator_outer,
                    rotor_topology=topology,
                )
            else:
                auto_name_faces(
                    stator_faces, r_shaft, r_rotor_outer,
                    r_stator_inner, r_stator_outer,
                    rotor_topology=topology,
                )

    # ── 8. 치수 요약 ──
    _log("[8/8] 치수 요약 산출 중...")
    topology_str = rotor_topo.get('topology', 'UNKNOWN')
    dims = {
        'n_poles':           n_poles,
        'n_slots':           n_slots,
        'pole_pitch_deg':    round(pole_pitch_deg, 4),
        'slot_pitch_deg':    round(slot_pitch_deg, 4),
        'r_shaft_mm':        round(r_shaft, 4),
        'r_rotor_outer_mm':  round(r_rotor_outer, 4),
        'r_stator_inner_mm': round(r_stator_inner, 4),
        'r_stator_outer_mm': round(r_stator_outer, 4),
        'airgap_mm':         round(r_stator_inner - r_rotor_outer, 4),
        'topology':          topology_str,
        'n_magnet_groups':   rotor_topo.get('n_magnets', 0),
        'n_barriers':        rotor_topo.get('n_barriers', 0),
        'n_rotor_faces':     len(rotor_faces),
        'n_stator_faces':    len(stator_faces),
    }

    _log(f"\n{'─'*62}")
    _log(f"  [결과 요약]")
    _log(f"  극수 / 슬롯수   : {n_poles}P / {n_slots}S")
    _log(f"  토폴로지        : {topology_str}")
    _log(f"  에어갭          : {dims['airgap_mm']:.3f} mm")
    _log(f"  로터 외경       : {r_rotor_outer:.3f} mm")
    _log(f"  스테이터 내경   : {r_stator_inner:.3f} mm")
    _log(f"  스테이터 외경   : {r_stator_outer:.3f} mm")
    _log(f"  자석 그룹       : {dims['n_magnet_groups']}  배리어: {dims['n_barriers']}")
    _log(f"  로터 face       : {dims['n_rotor_faces']}개")
    _log(f"  스테이터 face   : {dims['n_stator_faces']}개")
    _log(f"{'='*62}\n")

    return {
        'dxf_path':        dxf_path,
        'origin':          origin,
        'all_entities':    all_entities,
        'airgap':          airgap,
        'airgap_r_inner':  airgap_r_inner,
        'airgap_r_outer':  airgap_r_outer,
        'rotor_entities':  rotor_entities,
        'stator_entities': stator_entities,
        'n_poles':         n_poles,
        'n_slots':         n_slots,
        'pole_pitch_deg':  pole_pitch_deg,
        'slot_pitch_deg':  slot_pitch_deg,
        'half_pole':       half_pole,
        'half_slot':       half_slot,
        'one_pole_ents':   one_pole_ents,
        'one_slot_ents':   one_slot_ents,
        'pole_result':     pole_result,
        'slot_result':     slot_result,
        'rotor_faces':     rotor_faces,
        'stator_faces':    stator_faces,
        'rotor_topo':      rotor_topo,
        'r_shaft':         r_shaft,
        'r_rotor_outer':   r_rotor_outer,
        'r_stator_inner':  r_stator_inner,
        'r_stator_outer':  r_stator_outer,
        'fallback_info':   fallback_info,
        'dims':            dims,
    }


def export_result_json(result: Dict, output_path: str) -> None:
    """
    analyze_dxf_v2 결과의 치수/토폴로지 정보를 JSON으로 저장합니다.
    (EntityInfo 객체 등 직렬화 불가 항목 제외)
    """
    exportable = {
        'dxf_path':     result.get('dxf_path', ''),
        'origin':       list(result.get('origin', [0, 0])),
        'dims':         result.get('dims', {}),
        'rotor_faces':  [
            {k: v for k, v in f.items() if k not in ('vertices',)}
            for f in result.get('rotor_faces', [])
        ],
        'stator_faces': [
            {k: v for k, v in f.items() if k not in ('vertices',)}
            for f in result.get('stator_faces', [])
        ],
    }
    with open(output_path, 'w', encoding='utf-8') as fp:
        json.dump(exportable, fp, ensure_ascii=False, indent=2, default=str)
    print(f"[export] JSON 저장 완료: {output_path}")


def analyze_motor_dxf(dxf_path: str,
                      origin: Optional[Tuple[float, float]] = None,
                      airgap_ratio: float = 0.5,
                      verbose: bool = True) -> Dict:
    """
    모터 DXF 파일에 대한 종합 분석을 수행합니다.

    Parameters
    ----------
    dxf_path : str
        분석할 DXF 파일 경로.
    origin : Tuple[float, float], optional
        회전 중심 좌표. None이면 자동 감지.
    airgap_ratio : float, optional
        에어갭 분할 비율 (0.0~1.0). 기본 0.5.
    verbose : bool, optional
        진행 상황 출력 여부. 기본 True.

    Returns
    -------
    dict
        분석 결과를 담은 딕셔너리:
        - 'doc': ezdxf Document 객체
        - 'entities': EntityInfo 리스트
        - 'origins': 원점 후보 정보
        - 'rotor_type': 'inner_rotor' or 'outer_rotor'
        - 'stator_rotor_split': StatorRotorSplit 정보
        - 'periodicity': 주기성 정보
        - 'poles_slots': 극/슬롯 수 정보
        - 'symmetry_break': 대칭 파괴 분석
        - 'one_period': 1주기 엔티티
        - 'half_unit': half-slot/half-pole 정보
        - 'half_unit_regions': 영역 분류 결과
        - 'topology': 토폴로지 분류 결과

    Examples
    --------
    >>> from pyMotorGeo import analyze_motor_dxf
    >>> result = analyze_motor_dxf("motor.dxf")
    >>> print(result['poles_slots'])
    {'n_poles': 8, 'n_slots': 48}
    """
    import ezdxf
    from .analysis_airgap import find_origin_candidates
    from .analysis import (classify_inner_outer_rotor, split_stator_rotor,
                           group_identical_entities, classify_group_patterns,
                           detect_model_periodicity, infer_poles_and_slots,
                           classify_motor_topology)
    from .symmetry import (identify_symmetry_break, extract_one_period,
                           extract_half_unit)
    from .regions import classify_half_unit_regions

    if verbose:
        print(f"\n{'='*60}")
        print(f"  pyMotorGeo - 모터 DXF 분석")
        print(f"{'='*60}")
        print(f"  파일: {dxf_path}")
        print(f"{'='*60}\n")
    
    # 1. DXF 읽기
    if verbose:
        print("[1/9] DXF 파일 읽는 중...")
    
    doc = ezdxf.readfile(dxf_path)
    entities = read_entity_list(doc)
    
    if verbose:
        print(f"      → 엔티티 {len(entities)}개 로드 완료")
    
    # 2. 원점 찾기
    if verbose:
        print("[2/9] 회전 원점 탐색 중...")
    
    origins = find_origin_candidates(entities)
    
    if origin is not None:
        best_origin = origin
    else:
        best_origin = origins['best_origin']
    
    if verbose:
        print(f"      → 원점: ({best_origin[0]:.4f}, {best_origin[1]:.4f})")
    
    # 3. Inner/Outer rotor 판별
    if verbose:
        print("[3/9] 로터 타입 판별 중...")
    
    rotor_type = classify_inner_outer_rotor(entities, best_origin)
    
    if verbose:
        print(f"      → 로터 타입: {rotor_type}")
    
    # 4. Stator/Rotor 분리
    if verbose:
        print("[4/9] Stator/Rotor 엔티티 분리 중...")
    
    sr_split = split_stator_rotor(entities, best_origin, rotor_type, airgap_ratio)
    
    if verbose:
        print(f"      → Stator: {len(sr_split.stator_entities)}개")
        print(f"      → Rotor:  {len(sr_split.rotor_entities)}개")
        print(f"      → Airgap: {len(sr_split.airgap_entities)}개")
    
    # 5. 주기성 탐지
    if verbose:
        print("[5/9] 모델 주기성 분석 중...")
    
    # 엔티티 그룹화
    groups, entity_group_map = group_identical_entities(entities, best_origin)
    group_patterns = classify_group_patterns(groups, best_origin)
    
    # 주기성 탐지
    periodicity = detect_model_periodicity(group_patterns, best_origin)
    
    if verbose:
        print(f"      → 추정 주기: {periodicity['period_deg']:.2f}°")
        print(f"      → 주기 수:   {periodicity['n_periods']}")
    
    # 6. 극/슬롯 수 추정
    if verbose:
        print("[6/9] 극수/슬롯수 추정 중...")
    
    poles_slots = infer_poles_and_slots(
        sr_split, group_patterns, periodicity, best_origin
    )
    
    if verbose:
        print(f"      → 극수:   {poles_slots['n_poles']}")
        print(f"      → 슬롯수: {poles_slots['n_slots']}")
    
    # 7. 대칭 파괴 분석
    if verbose:
        print("[7/9] 대칭 파괴점 분석 중...")
    
    symmetry_break = identify_symmetry_break(entities, best_origin, periodicity)
    
    if verbose:
        break_type = symmetry_break.get('break_type', 'none')
        print(f"      → 대칭 파괴: {break_type}")
    
    # 8. 1주기 추출 및 half-unit 분석
    if verbose:
        print("[8/9] 1주기 및 half-unit 추출 중...")
    
    one_period = extract_one_period(entities, best_origin, periodicity, symmetry_break)
    
    half_unit = extract_half_unit(
        one_period, sr_split, poles_slots, periodicity, best_origin
    )
    
    if verbose:
        print(f"      → 1주기 엔티티: {len(one_period['entities'])}개")
        print(f"      → Half-slot: {half_unit['half_slot_deg']:.2f}°")
        print(f"      → Half-pole: {half_unit['half_pole_deg']:.2f}°")
    
    # 9. 닫힌 영역 탐지 및 분류
    if verbose:
        print("[9/9] 닫힌 영역 탐지 및 분류 중...")
    
    half_unit_regions = classify_half_unit_regions(
        half_unit, sr_split, poles_slots, rotor_type, best_origin
    )
    
    n_stator = len(half_unit_regions.get('stator_faces', []))
    n_rotor = len(half_unit_regions.get('rotor_faces', []))
    
    if verbose:
        print(f"      → Stator 영역: {n_stator}개")
        print(f"      → Rotor 영역:  {n_rotor}개")
    
    # 토폴로지 분류
    topology = classify_motor_topology(sr_split, poles_slots, rotor_type, best_origin)
    
    # 결과 종합
    result = {
        'doc': doc,
        'entities': entities,
        'origins': {
            'best_origin': best_origin,
            'candidates': origins.get('candidates', []),
        },
        'rotor_type': rotor_type,
        'stator_rotor_split': sr_split,
        'groups': groups,
        'group_patterns': group_patterns,
        'periodicity': periodicity,
        'poles_slots': poles_slots,
        'symmetry_break': symmetry_break,
        'one_period': one_period,
        'half_unit': half_unit,
        'half_unit_regions': half_unit_regions,
        'topology': topology,
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"  분석 완료!")
        print(f"{'='*60}")
        print(f"  모터 타입:    {rotor_type}")
        print(f"  극수/슬롯수:  {poles_slots['n_poles']}P / {poles_slots['n_slots']}S")
        print(f"  주기:         {periodicity['period_deg']:.2f}° × {periodicity['n_periods']}")
        print(f"  토폴로지:     {topology.get('stator_type', 'unknown')} + {topology.get('rotor_type', 'unknown')}")
        print(f"  닫힌 영역:    Stator {n_stator}개, Rotor {n_rotor}개")
        print(f"{'='*60}\n")
    
    return result


def quick_analyze(dxf_path: str, verbose: bool = False) -> Dict:
    """
    빠른 분석 - 기본 정보만 반환합니다.

    Parameters
    ----------
    dxf_path : str
        분석할 DXF 파일 경로.
    verbose : bool
        진행 상황 출력 여부.

    Returns
    -------
    dict
        기본 분석 정보:
        - 'n_poles': 극수
        - 'n_slots': 슬롯수
        - 'rotor_type': 로터 타입
        - 'period_deg': 1주기 각도
    """
    result = analyze_motor_dxf(dxf_path, verbose=verbose)
    
    return {
        'n_poles': result['poles_slots']['n_poles'],
        'n_slots': result['poles_slots']['n_slots'],
        'rotor_type': result['rotor_type'],
        'period_deg': result['periodicity']['period_deg'],
    }
