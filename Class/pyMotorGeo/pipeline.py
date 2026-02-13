"""
pyMotorGeo.pipeline
===================
고수준 분석 파이프라인 함수.
DXF를 읽고 모든 분석을 수행하는 편의 함수를 제공합니다.
"""

from typing import Dict, Optional, Tuple

from .reader import read_entity_list, find_origin_candidates
from .analysis import (classify_inner_outer_rotor, split_stator_rotor,
                       group_identical_entities, classify_group_patterns,
                       detect_model_periodicity, infer_poles_and_slots,
                       check_closed_regions, classify_motor_topology)
from .symmetry import (identify_symmetry_break, extract_one_period,
                       extract_half_unit, reconstruct_geometry)
from .regions import find_closed_regions_in_period, classify_half_unit_regions


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
