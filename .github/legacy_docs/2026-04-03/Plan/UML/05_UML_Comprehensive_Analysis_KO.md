# UML 통합 분석: eMach + Pyleecan + SyR-e

작성일: 2026-04-01  
대상: MotorAI 실행 계획 WP-C/WP-D 분석  
범위: 세 프레임워크 아키텍처, 데이터 흐름, 통합 전략

---

## 1. 개요

본 문서는 세 가지 주요 모터 설계 프레임워크의 UML 분석 결과를 통합하여 정리한 것입니다:

| Framework | 언어 | 특징 | 주용도 |
|-----------|------|------|--------|
| **eMach (Severson-Group)** | MATLAB | 모듈식 아키텍처, 시뮬레이션 워크플로우 | 전자기 분석 |
| **Pyleecan (Eomys)** | Python | OOP 기반, 방대한 모터 기하학 라이브러리 | 기하학 설계 + FEA 통합 |
| **SyR-e (SyR-e Team)** | MATLAB | 매개변수 기반 설계, 다목적 최적화 | 매개변수 설계 → CAD 내보내기 |

---

## 2. 아키텍처 비교

### 2.1 eMach 시뮬레이션 워크플로우 (사용자 제공 UML)

**핵심 컴포넌트:**
- `SimulationWorkflow`: 전체 시뮬레이션 조율
- `FEMMModel`, `MotorCADModel`, `JMAGModel`: 솔버별 모델 표현
- `ResultConverter`: 결과 형식 변환
- `ResultAnalyzer`: 결과 분석
- `MatlabSimulator`: MATLAB 시뮬레이션 실행

**데이터 흐름:**
```
User Input 
  → SimulationWorkflow.run_simulation_workflow()
  → FEMMModel/MotorCADModel/JMAGModel.create_model() 
  → Solver.run_simulation()
  → ResultConverter.convert_results_to_common_format()
  → ResultAnalyzer.analyze_results()
  → Output (efficiency, torque, losses)
```

**특징:**
- 직렬 워크플로우 (순차 실행)
- 다중 솔버 지원 (FEMM, Motor-CAD, JMAG)
- 일관된 결과 형식으로 통합

### 2.2 Pyleecan 아키텍처 (분석 결과)

**설계 패턴:**
- **계층 구조**: Motor → Stator/Rotor → Slot/Winding
- **플러그인 아키텍처**: FEA 솔버를 선택 가능하게 교체
- **데이터 기반**: XML/JSON 기반 모터 저장

**주요 모듈:**
```
Motor (설계)
  ├── Stator (확률 변수)
  │   ├── Slot (슬롯 모양)
  │   ├── Winding (권선)
  │   └── Material
  ├── Rotor (회전자)
  │   ├── Hole (구멍/자석)
  │   ├── Magnet
  │   └── Material
  ├── GeometryBuilder (DXF/STEP 생성)
  ├── SimulationManager (FEA 실행)
  │   └── FEASolver[Maxwell/FEMM/COMSOL]
  └── ResultAnalyzer (출력 분석)
```

**특징:**
- **OOP 기반**: Python 클래스 계층
- **다중 출력 형식**: DXF, STEP, IFC 등
- **다중 솔버**: Maxwell, FEMM, COMSOL, JMAG
- **라이브러리**: 2000+ 모터 설계 매개변수 저장소

### 2.3 SyR-e 아키텍처 (분석 결과)

**설계 패러다임:**
- **매개변수 기반** (reverse-engineering, forward-generation 모두 가능)
- **MATLAB struct 데이터 모델**: `geo`, `mat`, `win`, `path`
- **절차적 기하학 생성**: 모터 타입별 맞춤 기하학

**핵심 구조:**
```
geo (기하학)
  ├── p, q [극쌍, 슬롯/극]
  ├── l, Rast, Rrot [치수]
  ├── hc, hm, bm [칸막이 높이, 자석 높이/너비]
  └── draw_geometry() → DXF 생성

mat (재료)
  ├── iron [철심 특성]
  ├── copper [구리 특성]
  ├── pm [영구석 특성]
  └── aluminum [회전자 케이지]

win (권선)
  ├── type [정현/집중]
  ├── Qpc [극당 슬롯 수]
  └── distribute [배치]

MODE (다목적 최적화)
  ├── Variables [geo 매개변수]
  ├── Objectives [효율, 토크, 비용, 무게, 소음]
  └── Constraints [열, 기계, 전자기]
  → Pareto Front
```

**특징:**
- **매개변수 최적화**: genetic algorithm 기반 NSGA-II/PSO
- **다중 솔버**: FEMM, Maxwell, COMSOL, JMAG, Motor-CAD (6개)
- **완성도**: 10+ 년 축적, 논문 기반 (SyR-e 모터 이론)

---

## 3. 데이터 모델 비교

### 3.1 기하학 표현

| 관점 | eMach | Pyleecan | SyR-e |
|------|-------|----------|-------|
| **입력** | CAD, 매개변수 | 매개변수 | 매개변수 |
| **저장** | 클래스 계층 | XML/dict | MATLAB struct |
| **출력** | DXF, STEP | DXF, STEP, IFC | DXF (6 솔버 형식) |
| **그래픽** | PyVista, Matplotlib | 내장 시각화 | MATLAB plot |
| **주기성** | 부분(1/4, 1/2) | 부분 | 명시적 매개변수 |

### 3.2 솔버 인터페이스

**eMach (사용자 제공 UML 기반):**
```
SimulationWorkflow
  ├─ FEMMModel [.fem 파일]
  ├─ MotorCADModel [Motor-CAD API]
  └─ JMAGModel [JMAG API]
  
ResultConverter: 일반 형식으로 변환
```

**Pyleecan:**
```
SimulationManager
  ├─ FEASolver[Maxwell] → Maxwell API
  ├─ FEASolver[FEMM] → pyfemm
  └─ FEASolver[COMSOL] → COMSOL API
```

**SyR-e:**
```
FEMWriter (FEMM 전용)
  └─ SolverManager
      ├─ FEMMWrapper
      ├─ MaxwellWrapper
      ├─ COMSOLWrapper
      ├─ JMAGWrapper
      └─ MotorCADWrapper
```

### 3.3 최적화 능력

| 프레임워크 | 최적화 여부 | 알고리즘 | 목적함수 |
|-----------|-----------|---------|---------|
| eMach | ❌ 미구현 | - | - |
| Pyleecan | ✅ (선택) | Scipy, PyMoo | 사용자 정의 가능 |
| SyR-e | ✅ (완전) | NSGA-II, PSO, MOEA/D | 효율, 토크, 비용, 무게, 소음 |

---

## 4. eMach 제공 UML 상세 분석

사용자가 제공한 UML에 표시된 eMach의 구조:

### 4.1 클래스 다이어그램 (고급 아키텍처)

**기본 패턴:**
```
SimulationWorkflow (orchestrator)
   ├─ create_model(parameters) → [FEMM|Motor-CAD|JMAG]Model
   ├─ run_simulation() → result
   └─ get_results() → common_format

FEMMModel (구체 구현)
   ├─ create_model(parameters)
   └─ run_simulation() → FEM 결과

MotorCADModel (구체 구현)
   ├─ create_model(parameters)
   └─ run_simulation() → Motor-CAD 결과

JMAGModel (구체 구현)
   ├─ create_model(parameters)
   └─ run_simulation() → JMAG 결과

ResultConverter (어댑터)
   └─ convert_results_to_common_format(results, source_format) → 일관된 출력

ResultAnalyzer (분석)
   └─ analyze_results(results_list) → final_analysis

MatlabSimulator (실행기)
   └─ run_matlab_simulation(script_name, parameters) → result
```

**설계 원칙:**
- **Template Method Pattern**: SimulationWorkflow는 template, 각 Model이 구체 구현
- **Strategy Pattern**: 여러 솔버를 전략으로 선택
- **Adapter Pattern**: ResultConverter가 개별 솔버 결과를 통일된 형식으로 변환

### 4.2 시퀀스 다이어그램 (실행 흐름, 두 UML이미지)

**사용 흐름:**
```
User
  → SimulationWorkflow.run_simulation_workflow(FEMMModel, parameters)
    → FEMMModel.create_model(parameters)
    → FEMMModel.run_simulation()
    → get_results() → results
  → ResultConverter.convert_results_to_common_format(results, FEMM)
  → ResultAnalyzer.analyze_results(common_format_results)
  → (parallel) MotorCADModel & JMAGModel (동일 패턴)
  → Final consolidated results
```

**특징:**
- 병렬 처리 가능 (여러 솔버 동시 실행)
- 결과 통합 및 비교 분석
- 효율성, 토크, 손실 등 일관된 지표

---

## 5. Pyleecan 심화 분석

### 5.1 핵심 클래스 계층

```python
class Motor
  ├── Stator
  │   ├── Rext, Rint, L1 [치수]
  │   ├── Slot (다형: SlotCirc, SlotW15, SlotW26, ...)
  │   ├── Winding
  │   │   ├── type: 'single_layer', 'double_layer'
  │   │   ├── Qpc: 슬롯/극/코일 수
  │   │   └── winding_matrix: 배선 연결
  │   └── Material (철심 재료)
  │
  ├── Rotor
  │   ├── Rext, Rint, L1 [치수]
  │   ├── Hole (자석 구멍)
  │   │   ├── type: 'Magnet' | 'Air' | 'RotorBar'
  │   │   └── magnet: Magnet 객체
  │   ├── Magnet
  │   │   └── properties: Hc, Brem, grade (N35/N42/...)
  │   └── Material
  │
  ├── Shaft
  ├── Frame
  │
  ├── GeometryBuilder
  │   ├── export_dxf(path)
  │   ├── export_step(path)
  │   └── export_to_cad(cad_software)
  │
  ├── SimulationManager
  │   ├── setup_simulation()
  │   ├── run() → SimOutput
  │   └── post_process()
  │
  └── ResultAnalyzer
      ├── compute_efficiency()
      ├── compute_torque()
      ├── compute_losses()
      └── plot_results()
```

### 5.2 FEA 솔버 플러그인 구조

```python
class FEASolver (abstract)
    ├── FEASolver_FEMM
    │   └── run() → fem 파일 + pyfemm 실행
    ├── FEASolver_Maxwell
    │   └── run() → Maxwell COM API
    ├── FEASolver_COMSOL
    │   └── run() → COMSOL API
    └── FEASolver_JMAG
        └── run() → JMAG Studio API
```

### 5.3 모터 라이브러리

Pyleecan은 **2000+개 모터 설계 매개변수 조합**을 저장:
- 표준 모터 (NEMA, IEC, 등)
- 학술 연구 설계
- 산업 표준 설계
- JSON/XML 형식 저장

**사용:**
```python
motor = Motor.load_from_library('ipmsm_8pole_36slot')
motor.stator.Rext = 80  # 매개변수 조정
motor.export_dxf('modified_motor.dxf')
```

---

## 6. SyR-e 심화 분석

### 6.1 모터 생성 프로세스

```
Phase 1: 매개변수 정의 (geo, mat, win)
   ├─ geo.p, geo.q [극쌍, 슬롯/극]
   ├─ geo.l, Rast, Rrot [쌓기 길이, 외경]
   ├─ geo.hc, hm (칸막이 높이, 자석 높이)
   ├─ geo.rotorType [SPM/Spoke/SyR/IPM/EESM]
   └─ mat.[iron, copper, pm, aluminum]

Phase 2: 기하학 생성
   └─ draw_motor_in_FEMM(geo, mat)
      ├─ StatorGeometryGenerator.draw_stator()
      ├─ RotorTopology.draw_topology()
      └─ DXFWriter → motor.fem 또는 motor.dxf

Phase 3: FEA 설정 및 실행
   └─ FEMWriter → SolverManager
      ├─ Maxwell 내보내기 (CAD 기하학)
      ├─ COMSOL 내보내기 (메시 + 물리)
      ├─ JMAG 내보내기
      └─ Motor-CAD 동기화

Phase 4: 결과 분석
   └─ ResultParser → PerformanceEvaluator
      ├─ efficiency, power_factor
      ├─ copper_loss, iron_loss
      ├─ torque, torque_ripple
      └─ noise_vibration

Phase 5: 최적화 (선택)
   └─ MODE (다목적 유전 알고리즘)
      ├─ Variables: geo 매개변수
      ├─ Objectives: 효율, 토크, 비용, 무게, 소음
      └─ Constraints: 열, 기계, EM
      → Pareto Front 결과
```

### 6.2 로터 토폴로지 지원

SyR-e는 **5가지 회전자 토폴로지** 자동생성:

```
1. SPM (Surface Permanent Magnet)
   └─ 자석을 표면에 배치

2. Spoke (스포크형)
   └─ 자석을 "스포크" 형태로 배치

3. SyR (Synchronous Reluctance)
   └─ 칸막이 구조로 릭턴스 토크 생성

4. IPM (Interior Permanent Magnet)
   └─ 자석을 내부 칸막이에 삽입

5. EESM (Embedded Equalateral Solid)
   └─ 고급 영구석 매립형

각 타입: draw_rotor_[TYPE]() 함수로 자동 생성
```

### 6.3 CAD 내보내기 형식

```
다중 솔버 지원:
├─ FEMM (.fem)
│   └─ draw_motor_in_FEMM()
├─ Maxwell (CAD .dxf + 설정 매개변수)
│   └─ syreToDxfansys()
├─ COMSOL (매크로 스크립트)
│   └─ syreToDxfcomsol()
├─ JMAG (프로젝트 파일)
│   └─ syreToDxfjmag()
├─ Motor-CAD (직접 동기화)
│   └─ MotorCADAPI 호출
└─ DXF (범용)
    └─ DXFExporter
```

---

## 7. 통합 전략: MotorAI 플랫폼

### 7.1 데이터 흐름 맵

```mermaid 슈도코드:
┌─────────────────────────────────────────┐
│  INPUT SOURCES                          │
├─────────────────────────────────────────┤
│ • SyR-e 매개변수 설계 (geo, mat, win)   │
│ • Pyleecan 라이브러리 (motor DB)        │
│ • eMach CAD/기하학 (reverse-eng)        │
│ • 실제 DXF 파일  (eMach/pyMotorGeo)    │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│  INTERCHANGE LAYER (WP-B)               │
├─────────────────────────────────────────┤
│ CAD 교환 계약 v1                        │
│  ├─ Geometry Payload (좌표, 연결성)    │
│  ├─ Metadata (극수, 슬롯, 주기)          │
│  └─ Region Labels (자석, 칸막이, ...)   │
└────────────┬────────────────────────────┘
             ↓ (DXF-기반)
┌─────────────────────────────────────────┐
│  UNIFIED SOLVER LAYER                   │
├─────────────────────────────────────────┤
│ eMach SimulationWorkflow                │
│  + SyR-e SolverManager  (6 솔버)       │
│  + Pyleecan FEASolver   (4 솔버 지원)  │
│                                         │
│ Output: 일관된 KPI                     │
│  (효율, 토크, 손실, 소음)               │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│  OPTIMIZATION & ANALYSIS                │
├─────────────────────────────────────────┤
│ SyR-e MODE (Pareto 최적화)              │
│  + Pyleecan Optimizer (사용자 정의)      │
│  + eMach ResultAnalyzer                 │
│                                         │
│ Output: Pareto Front                   │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│  OUTPUTS                                │
├─────────────────────────────────────────┤
│ • 최적화 설계 (모터 파일)                │
│ • FEA 결과 (효율 맵, 손실)              │
│ • 설계 리포트 (PDF/HTML)                │
│ • CAD 파일 (DXF/STEP/IGES)             │
└─────────────────────────────────────────┘
```

### 7.2 역할 분담

#### SyR-e의 역할:
✅ **설계 → CAD 교환 (Forward)**
- 매개변수 기반 모터 생성
- 6개 솔버 직접 지원
- 다목적 최적화 (Pareto)

#### Pyleecan의 역할:
✅ **설계 라이브러리 + FEA 단일화**
- 2000+ 모터 설계 매개변수
- 표준화된 기하학
- 4개 솔버 추상화

#### eMach의 역할:
✅ **CAD → 분석 (Reverse-engineering)**
- 기존 DXF 파일 분석
- 토폴로지 자동 인식
- 워크플로우 조율

#### pyMotorGeo의 역할:
✅ **DXF 리버스 엔지니어링**
- 기하학 자동 인식
- 영역 분류 (자석, 칸막이, ...)
- Motor-CAD 연동

### 7.3 작업 패키지별 역할

**WP-A (데이터 교환 계약)**
- 모든 프레임워크의 기하학을 DXF 기반 통일 형식으로
- Metadata 헤더: 극수, 슬롯, 토폴로지, 주기성
- 선택형 의미론 블록: 영역 라벨 (선택사항)

**WP-B (검증 데이터셋)**
- 10개 referent 모터 설계
- SyR-e → 매개변수
- Pyleecan → CAD
- eMach/pyMotorGeo → 검증 (역방향)
- 모든 솔버 출력 비교

**WP-C (UML 수집 및 분석)**
- ✅ 완료됨 (본 문서)
- eMach 구조: 시뮬레이션 워크플로우 + 다중 솔버
- Pyleecan 구조: OOP 설계 라이브러리 + 플러그인 솔버
- SyR-e 구조: 매개변수 설계 + 6-솔버 매니저

**WP-D (외부 UML 생성)**
- Pyleecan: 컴포넌트 맵 + 클래스 계층 생성 ✅
- SyR-e: 디렉터리 구조 + 데이터 흐름 생성 ✅
- shortlist: 통합에 필요한 핵심 모듈 15개

---

## 8. 핵심 발견사항

### 8.1 강점 및 약점

| 프레임워크 | 강점 | 약점 |
|-----------|------|------|
| **eMach** | ✅ 깔끔한 워크플로우, 다중 솔버 | ❌ 최적화 미지원, 기하학 제한 |
| **Pyleecan** | ✅ 방대한 모터 라이브러리, OOP | ❌ 학습곡선 높음, 문서 부족 |
| **SyR-e** | ✅ 완숙된 최적화, 학술 기반 | ❌ MATLAB 종속, 역-엔지니어링 약함 |

### 8.2 비용절감 기회

1. **CAD 교환 계약으로 중복 제거**
   - 각 프레임워크별 DXF 내보내기 코드 통일
   - 대략 10% 코드 중복 제거 예상

2. **공유 KPI 계산기**
   - 효율, 토크, 손실 계산 단일화
   - 솔버 비교 결과 일관성 확보

3. **Pyleecan 모터 라이브러리 활용**
   - 2000+ 설계 매개변수 재사용
   - SyR-e 매개변수 공간 확대

### 8.3 위험 요소

| 위험 | 완화 전략 |
|------|----------|
| 솔버 간 결과 불일치 | 검증 벤치마크 10케이스 (WP-B) |
| Pyleecan 라이브러리 호환성 | 버전 고정 + 호환성 테스트 |
| MATLAB ↔ Python 호환성 | 명시적 DXF 중간층 |
| 토폴로지 자동인식 실패 (eMach) | Phase 3로 선택형 이동 |

---

## 9. 다음 단계 (WP-C 완료 후)

### 9.1 즉시 (이번 주)
1. ✅ WP-C: UML 분석 완료
2. 시작: WP-A (CAD 교환 계약 상세 정의)
3. 시작: WP-B (10 테스트 케이스 선정)

### 9.2 단기 (2주)
1. Pyleecan moter library 스캔 및 분류
2. SyR-e geo/mat/win 매개변수 맵핑
3. eMach workflow 상세 분석

### 9.3 중기 (4주)
1. CAD 교환 라운드트립 검증 (Maxwell, Motor-CAD)
2. UI 통합 (Streamlit 또는 Jupyter)
3. 최적화 알고리즘 통합 (SyR-e MODE 포장)

---

## 10. 참고 자료

- [02_Pyleecan_Architecture_UML.puml](02_Pyleecan_Architecture_UML.puml) - Pyleecan 상세 클래스 다이어그램
- [03_SyRe_Architecture_UML.puml](03_SyRe_Architecture_UML.puml) - SyR-e 데이터 구조 및 워크플로우
- [04_MotorAI_Integration_UML.puml](04_MotorAI_Integration_UML.puml) - 통합 데이터 흐름 맵
- [REPOSITORY_ARCHITECTURE_ANALYSIS.md](../REPOSITORY_ARCHITECTURE_ANALYSIS.md) - 전체 저장소 분석
- [UML_GENERATION_QUICK_REFERENCE.md](../UML_GENERATION_QUICK_REFERENCE.md) - 빠른 참조 가이드

