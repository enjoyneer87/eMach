# pyMotorGeo v1.5.1 마이그레이션 가이드

## 개요

pyMotorGeo v1.5.1부터 **OOP(객체지향) 기반 구조**를 도입하여 더욱 체계적이고 유지보수하기 쉬운 아키텍처로 재설계되었습니다.

✅ **중요**: 모든 기존 코드는 **100% 하위 호환성**을 유지하므로, 기존 프로젝트를 변경할 필요가 없습니다.

---

## 1. 분석 모듈 (Analysis) 마이그레이션

### 기존 코드 (함수형)

```python
from pyMotorGeo.analysis_rotor import count_poles, estimate_poles_robust
from pyMotorGeo.analysis_stator import count_slots, estimate_slots_robust

# 극수 추정
poles = count_poles(rotor_entities, origin=(0, 0))
result = estimate_poles_robust(rotor_entities, verbose=True)
n_poles = result['n_poles']

# 슬롯수 추정
slots = count_slots(stator_entities, origin=(0, 0))
result = estimate_slots_robust(stator_entities, verbose=True)
n_slots = result['n_slots']
```

### 신규 코드 (OOP 기반)

```python
from pyMotorGeo.analysis_rotor import RotorCounter
from pyMotorGeo.analysis_stator import StatorCounter

# RotorCounter 사용
rotor_counter = RotorCounter()
poles = rotor_counter.count(rotor_entities, origin=(0, 0))
result = rotor_counter.estimate_robust(rotor_entities, verbose=True)
n_poles = result['n_poles']

# StatorCounter 사용
stator_counter = StatorCounter()
slots = stator_counter.count(stator_entities, origin=(0, 0))
result = stator_counter.estimate_robust(stator_entities, verbose=True)
n_slots = result['n_slots']
```

### 제공되는 메서드

#### RotorCounter
- `count(entities, origin, **kwargs) → int`: ARC 분포 기반 극수 추정
- `count_by_regions(entities, origin, **kwargs) → Dict`: 닫힌 영역 기반 극수 추정
- `estimate_robust(entities, origin, verbose, **kwargs) → Dict`: 교차 검증 극수 추정

#### StatorCounter
- `count(entities, origin, **kwargs) → int`: 방사형 선분 기반 슬롯수 추정
- `count_by_regions(entities, origin, **kwargs) → Dict`: 닫힌 영역 기반 슬롯수 추정
- `estimate_robust(entities, origin, verbose, **kwargs) → Dict`: 교차 검증 슬롯수 추정
- `detect_conductors(entities, origin, n_slots, slot_pitch_deg, **kwargs) → Dict`: 슬롯 내 컨덕터 탐지

---

## 2. 토폴로지 모듈 (Topology) 마이그레이션

### 기존 코드 (함수형)

```python
from pyMotorGeo.topology_rotor import classify_rotor_entities
from pyMotorGeo.topology_stator import classify_stator_entities

# 회전자 분류
rotor_result = classify_rotor_entities(
    pole_entities, 
    origin=(0, 0), 
    airgap_r=50, 
    verbose=True
)

# 고정자 분류
stator_result = classify_stator_entities(
    slot_entities,
    origin=(0, 0),
    airgap_r=50,
    verbose=True
)
```

### 신규 코드 (OOP 기반)

```python
from pyMotorGeo.topology_rotor import RotorTopologyClassifier
from pyMotorGeo.topology_stator import StatorTopologyClassifier

# RotorTopologyClassifier 사용
rotor_classifier = RotorTopologyClassifier()
rotor_result = rotor_classifier.classify_entities(
    pole_entities,
    origin=(0, 0),
    airgap_r=50,
    verbose=True
)

# StatorTopologyClassifier 사용
stator_classifier = StatorTopologyClassifier()
stator_result = stator_classifier.classify_entities(
    slot_entities,
    origin=(0, 0),
    airgap_r=50,
    verbose=True
)
```

### 제공되는 메서드

#### RotorTopologyClassifier
- `classify_entities(component_entities, origin, **kwargs) → Dict`: 회전자 엔티티 분류
- `classify_with_closing_compare(component_entities, origin, **kwargs) → Dict`: 폐곡선 비교 기반 정교한 분류

#### StatorTopologyClassifier
- `classify_entities(component_entities, origin, **kwargs) → Dict`: 고정자 엔티티 분류
- `classify_with_closing_compare(component_entities, origin, **kwargs) → Dict`: 폐곡선 비교 기반 정교한 분류

---

## 3. 기존 코드와의 호환성

### 모두 동시에 사용 가능 ✅

```python
# 기존 방식
from pyMotorGeo.analysis_rotor import count_poles
poles1 = count_poles(rotor_entities)

# 신규 방식
from pyMotorGeo.analysis_rotor import RotorCounter
counter = RotorCounter()
poles2 = counter.count(rotor_entities)

# 결과는 동일
assert poles1 == poles2  ✅
```

### 단계적 마이그레이션 가능 ✅

```python
# 기존 함수를 사용하는 레거시 코드
result1 = estimate_poles_robust(entities, verbose=True)

# 일부만 OOP로 변경
counter = RotorCounter()
result2 = counter.estimate_robust(entities, verbose=True)

# 두 방식 모두 동일하게 작동합니다
```

---

## 4. 마이그레이션 전략

### 단계 1: 테스트 실행 (선택사항)

```bash
cd d:\KangDH\Emlab_emach\Class\pyMotorGeo
python test_refactoring.py
```

예상 출력:
```
======================================================================
  pyMotorGeo 리팩토링 테스트 시작
======================================================================

✅ test_rotor_counter_instantiation: PASS
✅ test_stator_counter_instantiation: PASS
✅ test_rotor_topology_classifier_instantiation: PASS
✅ test_stator_topology_classifier_instantiation: PASS
✅ test_backward_compatibility_analysis_rotor: PASS
✅ test_backward_compatibility_analysis_stator: PASS
✅ test_backward_compatibility_topology_rotor: PASS
✅ test_backward_compatibility_topology_stator: PASS
✅ test_pipeline_imports: PASS

======================================================================
  테스트 결과: 9/9 PASS
======================================================================
```

### 단계 2: 기존 코드 유지 (권장)

⚠️ **호환성 유지 기간**: v1.5.1 → v2.0 (약 6개월)

기존 프로젝트에서는 현재 코드를 그대로 유지해도 무방합니다.

### 단계 3: 점진적 마이그레이션 (향후)

새로운 모듈/기능부터 OOP 방식을 적용:

```python
# 새로운 기능: OOP 기반
class MotorAnalyzer:
    def __init__(self):
        self.rotor_counter = RotorCounter()
        self.stator_counter = StatorCounter()
    
    def analyze(self, dxf_path):
        entities = read_entity_list(dxf_path)
        n_poles = self.rotor_counter.estimate_robust(entities)['n_poles']
        n_slots = self.stator_counter.estimate_robust(entities)['n_slots']
        return {'n_poles': n_poles, 'n_slots': n_slots}
```

---

## 5. 추상 기본 클래스 (Abstract Base Classes)

### ComponentCounter (분석용)

모든 카운터 클래스의 부모 클래스입니다:

```python
from pyMotorGeo.analysis_base import ComponentCounter

class MyCustomCounter(ComponentCounter):
    def __init__(self):
        super().__init__(component_type="custom", count_keyword="components")
    
    def count(self, entities, origin=(0, 0), **kwargs):
        # 사용자 정의 로직
        pass
    
    def count_by_regions(self, entities, origin=(0, 0), **kwargs):
        pass
    
    def estimate_robust(self, entities, origin=(0, 0), verbose=True, **kwargs):
        pass
```

### ComponentTopologyClassifier (분류용)

모든 분류기 클래스의 부모 클래스입니다:

```python
from pyMotorGeo.topology_base import ComponentTopologyClassifier

class MyCustomClassifier(ComponentTopologyClassifier):
    def __init__(self):
        super().__init__(
            component_type="custom",
            region_names={'region1': 'Region 1'},
            region_colors={'region1': '#FF0000'}
        )
    
    def classify_entities(self, component_entities, origin=(0, 0), **kwargs):
        # 사용자 정의 분류 로직
        pass
```

---

## 6. 자주 묻는 질문 (FAQ)

### Q1: 기존 코드를 수정해야 하나요?
**A**: 아니요. 모든 기존 함수는 여전히 작동하며 100% 하위 호환성을 유지합니다.

### Q2: 새 클래스를 언제 사용해야 하나요?
**A**: 
- 새로운 프로젝트 시작 시
- 코드 재사용성이 중요한 경우
- 테스트하기 쉬운 구조를 원할 때

### Q3: 성능 차이가 있나요?
**A**: 아니요. OOP 래핑에 오버헤드가 최소화되어 성능 차이가 무시할 수준입니다.

### Q4: 두 방식을 섞어 쓸 수 있나요?
**A**: 네! 완전히 호환되므로 같은 코드 내에서 섞어 써도 됩니다.

### Q5: 향후 v2.0에서 어떻게 되나요?
**A**: 함수형 API를 deprecated 처리하고 OOP 기반만 유지할 예정입니다.

---

## 7. 트러블슈팅

### 문제 1: ImportError: cannot import name 'RotorCounter'

**원인**: 파이썬 경로가 최신 코드를 가리키지 않음

**해결책**:
```python
# 1. 파이썬 캐시 삭제
import shutil
shutil.rmtree('__pycache__')
shutil.rmtree('.pytest_cache')

# 2. IDE 재시작
# 3. 다시 import 시도
```

### 문제 2: 기존 코드가 안 먹히는 경우

**원인**: 하위 호환성 문제 (매우 드문 경우)

**해결책**:
1. REFACTORING_PROGRESS.md 확인
2. test_refactoring.py 실행
3. GitHub Issues에 보고

### 문제 3: 성능 저하 (느린 처리)

**원인**: 대량의 엔티티 처리 시 verbose=True로 인한 출력

**해결책**:
```python
# verbose=False로 설정
result = counter.estimate_robust(entities, verbose=False)
```

---

## 8. 참고 자료

- **Architecture Documentation**: [UML_AND_ARCHITECTURE.md](UML_AND_ARCHITECTURE.md)
- **PlantUML Diagrams**: `Class/pyMotorGeo_*.puml` 파일들
- **Base Classes**: [analysis_base.py](pyMotorGeo/analysis_base.py), [topology_base.py](pyMotorGeo/topology_base.py)
- **Test Cases**: [test_refactoring.py](pyMotorGeo/test_refactoring.py)

---

## 9. 지원 정보

문제가 발생하거나 질문이 있으면:

1. **REFACTORING_PROGRESS.md** 참고
2. **test_refactoring.py** 실행하여 호환성 확인
3. **PLANTUML_SETUP_GUIDE.md**로 문제 해결

**최종 업데이트**: 2026-04-01
**상태**: ✅ v1.5.1 (안정화 완료)
