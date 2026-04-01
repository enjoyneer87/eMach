"""
pyMotorGeo 리팩토링 테스트 모듈

OOP 기반 클래스들의 기본 기능과 하위 호환성을 검증합니다.

테스트 항목:
1. RotorCounter 클래스 테스트
2. StatorCounter 클래스 테스트
3. RotorTopologyClassifier 클래스 테스트
4. StatorTopologyClassifier 클래스 테스트
5. 하위 호환성 검증 (기존 함수형 API)
6. 통합 테스트 (pipeline.py와의 호환)
"""

import sys
from typing import Dict, List, Optional, Tuple

# 테스트용 더미 엔티티 생성 함수
def create_dummy_rotor_entities(n_poles: int = 4) -> List[Dict]:
    """
    테스트용 회전자 엔티티 생성.
    """
    # 실제 구현에서는 DXF 파일로부터 읽어옴
    # 여기서는 최소한의 더미 데이터만 생성
    from pyMotorGeo.core import EntityInfo
    
    entities = []
    pole_pitch = 360 / n_poles
    
    for p in range(n_poles):
        angle = p * pole_pitch
        # ARC 엔티티를 대표로 추가
        arc = EntityInfo(
            etype='ARC',
            points=[(50, 0), (50, 10)],  # 더미 포인트
            center=(0, 0),
            radius=50,
            start_angle=angle,
            end_angle=angle + pole_pitch,
            angle_deg=pole_pitch,
        )
        entities.append(arc)
    
    return entities


def create_dummy_stator_entities(n_slots: int = 24) -> List[Dict]:
    """
    테스트용 고정자 엔티티 생성.
    """
    from pyMotorGeo.core import EntityInfo
    
    entities = []
    slot_pitch = 360 / n_slots
    
    for s in range(n_slots):
        angle = s * slot_pitch
        # LINE 엔티티를 대표로 추가 (방사형 선분)
        line = EntityInfo(
            etype='LINE',
            points=[(60, 0), (80, 0)],  # 반경 60~80 사이
        )
        entities.append(line)
    
    return entities


# ═══════════════════════════════════════════════════════════════
# 테스트 케이스
# ═══════════════════════════════════════════════════════════════

def test_rotor_counter_instantiation():
    """
    RotorCounter 클래스 인스턴스 생성 테스트.
    """
    from pyMotorGeo.analysis_rotor import RotorCounter
    
    try:
        counter = RotorCounter()
        assert counter.component_type == "rotor"
        assert counter.count_keyword == "poles"
        print("✅ test_rotor_counter_instantiation: PASS")
        return True
    except Exception as e:
        print(f"❌ test_rotor_counter_instantiation: FAIL - {e}")
        return False


def test_stator_counter_instantiation():
    """
    StatorCounter 클래스 인스턴스 생성 테스트.
    """
    from pyMotorGeo.analysis_stator import StatorCounter
    
    try:
        counter = StatorCounter()
        assert counter.component_type == "stator"
        assert counter.count_keyword == "slots"
        print("✅ test_stator_counter_instantiation: PASS")
        return True
    except Exception as e:
        print(f"❌ test_stator_counter_instantiation: FAIL - {e}")
        return False


def test_rotor_topology_classifier_instantiation():
    """
    RotorTopologyClassifier 클래스 인스턴스 생성 테스트.
    """
    from pyMotorGeo.topology_rotor import RotorTopologyClassifier, ROTOR_REGION_NAMES
    
    try:
        classifier = RotorTopologyClassifier()
        assert classifier.component_type == "rotor"
        assert len(classifier.region_names) > 0
        assert ROTOR_REGION_NAMES['magnet'] == 'Magnet'
        print("✅ test_rotor_topology_classifier_instantiation: PASS")
        return True
    except Exception as e:
        print(f"❌ test_rotor_topology_classifier_instantiation: FAIL - {e}")
        return False


def test_stator_topology_classifier_instantiation():
    """
    StatorTopologyClassifier 클래스 인스턴스 생성 테스트.
    """
    from pyMotorGeo.topology_stator import StatorTopologyClassifier, STATOR_REGION_NAMES
    
    try:
        classifier = StatorTopologyClassifier()
        assert classifier.component_type == "stator"
        assert len(classifier.region_names) > 0
        assert STATOR_REGION_NAMES['stator_tooth'] == 'Stator Tooth'
        print("✅ test_stator_topology_classifier_instantiation: PASS")
        return True
    except Exception as e:
        print(f"❌ test_stator_topology_classifier_instantiation: FAIL - {e}")
        return False


def test_backward_compatibility_analysis_rotor():
    """
    analysis_rotor.py의 하위 호환성 테스트 (함수형 API 보존).
    """
    try:
        # 기존 방식: 함수 import
        from pyMotorGeo.analysis_rotor import count_poles, count_poles_by_regions, estimate_poles_robust
        
        # callable인지 확인
        assert callable(count_poles)
        assert callable(count_poles_by_regions)
        assert callable(estimate_poles_robust)
        
        print("✅ test_backward_compatibility_analysis_rotor: PASS")
        return True
    except Exception as e:
        print(f"❌ test_backward_compatibility_analysis_rotor: FAIL - {e}")
        return False


def test_backward_compatibility_analysis_stator():
    """
    analysis_stator.py의 하위 호환성 테스트 (함수형 API 보존).
    """
    try:
        # 기존 방식: 함수 import
        from pyMotorGeo.analysis_stator import (
            count_slots, count_slots_by_regions, 
            estimate_slots_robust, detect_slot_conductors
        )
        
        # callable인지 확인
        assert callable(count_slots)
        assert callable(count_slots_by_regions)
        assert callable(estimate_slots_robust)
        assert callable(detect_slot_conductors)
        
        print("✅ test_backward_compatibility_analysis_stator: PASS")
        return True
    except Exception as e:
        print(f"❌ test_backward_compatibility_analysis_stator: FAIL - {e}")
        return False


def test_backward_compatibility_topology_rotor():
    """
    topology_rotor.py의 하위 호환성 테스트 (함수형 API 보존).
    """
    try:
        # 기존 방식: 함수 import
        from pyMotorGeo.topology_rotor import (
            classify_rotor_entities,
            classify_rotor_entities_with_closing_compare
        )
        
        # callable인지 확인
        assert callable(classify_rotor_entities)
        assert callable(classify_rotor_entities_with_closing_compare)
        
        print("✅ test_backward_compatibility_topology_rotor: PASS")
        return True
    except Exception as e:
        print(f"❌ test_backward_compatibility_topology_rotor: FAIL - {e}")
        return False


def test_backward_compatibility_topology_stator():
    """
    topology_stator.py의 하위 호환성 테스트 (함수형 API 보존).
    """
    try:
        # 기존 방식: 함수 import
        from pyMotorGeo.topology_stator import (
            classify_stator_entities,
            classify_stator_entities_with_closing_compare
        )
        
        # callable인지 확인
        assert callable(classify_stator_entities)
        assert callable(classify_stator_entities_with_closing_compare)
        
        print("✅ test_backward_compatibility_topology_stator: PASS")
        return True
    except Exception as e:
        print(f"❌ test_backward_compatibility_topology_stator: FAIL - {e}")
        return False


def test_pipeline_imports():
    """
    pipeline.py의 새로운 클래스 import 검증.
    """
    try:
        from pyMotorGeo.pipeline import (
            RotorCounter, StatorCounter, 
            RotorTopologyClassifier, StatorTopologyClassifier
        )
        
        # 모두 class인지 확인
        assert isinstance(RotorCounter, type)
        assert isinstance(StatorCounter, type)
        assert isinstance(RotorTopologyClassifier, type)
        assert isinstance(StatorTopologyClassifier, type)
        
        print("✅ test_pipeline_imports: PASS")
        return True
    except Exception as e:
        print(f"❌ test_pipeline_imports: FAIL - {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# 통합 테스트 러너
# ═══════════════════════════════════════════════════════════════

def run_all_tests() -> Tuple[int, int]:
    """
    모든 테스트를 실행하고 성공/실패 개수를 반환합니다.
    
    Returns:
        Tuple[int, int]: (성공 개수, 전체 개수)
    """
    tests = [
        # OOP 클래스 인스턴스 생성 테스트
        test_rotor_counter_instantiation,
        test_stator_counter_instantiation,
        test_rotor_topology_classifier_instantiation,
        test_stator_topology_classifier_instantiation,
        
        # 하위 호환성 테스트
        test_backward_compatibility_analysis_rotor,
        test_backward_compatibility_analysis_stator,
        test_backward_compatibility_topology_rotor,
        test_backward_compatibility_topology_stator,
        
        # 통합 테스트
        test_pipeline_imports,
    ]
    
    print("\n" + "="*70)
    print("  pyMotorGeo 리팩토링 테스트 시작")
    print("="*70 + "\n")
    
    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)
    
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*70)
    print(f"  테스트 결과: {passed}/{total} PASS")
    print("="*70 + "\n")
    
    return passed, total


if __name__ == '__main__':
    passed, total = run_all_tests()
    
    # 종료 코드
    exit_code = 0 if passed == total else 1
    sys.exit(exit_code)
