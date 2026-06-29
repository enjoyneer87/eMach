# Dispatch 작업 현황 (2026-06-29)

## 오늘 완료된 작업
- ✅ verify_phase_angle.py 작성 완료 (Task 1-A)
- ✅ EfficiencyMap.phase_deg 프로퍼티 추가 (Task 1-B)  
- ✅ test_mcad_to_syre.m 버그 2개 수정

## 수정된 파일
- `mlxperPJT/JEET/verify_phase_angle.py` - β_opt 계산, SC 경로 버그 수정
- `tools/motor_scaling/model/EfficiencyMap.py` - phase_deg, i_amp 프로퍼티 추가
- `mlxperPJT/JEET/test_mcad_to_syre.m` - buildMotorModel 위치, outMat_A 참조 수정

## 다음 예정 작업 (07-01)
- Task 2-A: run_efficiency_map.py 작성

## 🏛️ eMach/Class 리팩토링 계획 (UML & OOP)

### 1순위 (높음 - 지금 바로 수정 가능)
1. **`ElecUnit.m` 생성자 오타 버그 수정**
   - **문제**: 생성자가 `myData`로 잘못 정의되어 정상적인 객체 생성 불가.
   - **조치**: 생성자명을 `ElecUnit`으로 변경.
2. **`EddyCoefficientData` & `HysCoefficientData` 통합**
   - **문제**: 두 클래스의 프로퍼티와 생성자 로직이 99% 동일 (완전한 코드 중복).
   - **조치**: `IronLossCoefficientData` 공통 모델로 통합하고 서브클래스화 또는 매개변수화.
3. **`DataPkBetaMap.m` 메서드 및 파일명 불일치 수정**
   - **문제**: 클래스에는 `compMatFile`로 선언되었으나, 실제 파일명은 `compMatiFilePsi.m`이고 호출 시에도 `compMatiFilePsi()`로 사용됨. 또한 `obj`를 파라미터로 받는데 `Static` 메서드로 지정된 설계 결함 존재.
   - **조치**: 메서드 선언 및 파일명을 일치시키고 일반 인스턴스 메서드로 전환.

### 2순위 (중간 - 논문 완료 후 진행 권장)
4. **`emlab_MachineData`로 3상 전기 속성 끌어올리기 (Pull Up Field)**
   - **문제**: `MotorcadData`, `JmagData`, `measureddata` 3개 클래스에 3상 전압/전류/자속 등 속성 15개가 동일하게 중복 정의됨.
   - **조치**: 상위 추상 클래스인 `emlab_MachineData`로 필드를 이동하여 중복 제거.
5. **`ResultMotorcadData` 복사-생성자 안티패턴 개선**
   - **문제**: 부모 객체의 값을 수동으로 30줄 넘게 복사하는 값 계층 설계 결함.
   - **조치**: `MotorcadData`를 `handle` 클래스로 상속 선언한 뒤, 상위 생성자 위임(`obj@MotorcadData(...)`) 방식을 사용하도록 리팩토링.

### 3순위 (낮음 - 장기 개선 과제)
6. **`BasisModel`에 Strategy 패턴 적용**
   - **문제**: `fit()`과 `evaluate()` 내부에 6가지 회귀 모드 스위치 케이스가 중복되어 존재하며, `degree` 프로퍼티의 의미가 컨텍스트별로 왜곡됨.
   - **조치**: 개별 기저 모델을 클래스(RBF, Poly 등)로 분리하고 Strategy 패턴으로 계산을 위임.

## 알림
- Windows OS 파일 핸들 락(VS Code LSPs/MATLAB 프로세스 점유)으로 인해 `Class` 폴더의 물리적 이름 변경이 차단되어, 대신 `Class/DEPRECATED.txt` 경고 파일을 배치하여 레거시 클래스 사용 제한을 명시했습니다.
- 모든 신규 논문용 스크립트는 `Class` 폴더를 완전히 우회하고 `+mcad` 함수형 네임스페이스만 명시적으로 사용하도록 격리 조치를 적용했습니다.
- Dispatch 채팅 메시지 렌더링 문제가 있어 이 파일로 상태를 공유합니다.
