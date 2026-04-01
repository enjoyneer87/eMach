# 통합 UML 분석: 실제 Pyleecan + eMach 아키텍처

작성일: 2026-04-01  
상태: **실제 코드베이스 분석 기반** (airAgent 분석 완료)  
범위: 271개 Pyleecan 클래스 + 32개 eMach 모듈

---

## 1. Pyleecan 실제 아키텍처

### 1.1 클래스 계층 (271개 전체)

**머신 타입 (12개):**
```
Machine (abstract)
├── MachineAsync (비동기)
│   ├── MachineSCIM (Squirrel Cage Induction)
│   └── MachineDFIM (Double-Fed Induction)
├── MachineSync (동기식)
│   ├── MachineIPMSM (Interior PM Sync)
│   ├── MachineSIPMSM (Surface-Interior PMSM)
│   ├── MachineSyRM (Synchronous Reluctance)
│   ├── MachineLSRM (Line-Start Reluctance)
│   └── MachineSRM (Switched Reluctance)
└── MachineUD (User-Defined Custom)
```

**라미네이션 (적층) 타입:**
```
Lamination (abstract base)
├── LamSlot (슬롯 적층)
│   ├── LamSlotWind (슬롯 + 권선)
│   └── LamSlotM (슬롯 + 자석)
├── LamHole (구멍 적층, 자석용)
└── LamSquirrelCage (cage rotor)
```

**슬롯 타입 (50+ 종류):**
- **W-series (W10~W30)**: 유도 모터 표준 슬롯
- **M-series (M10~M63)**: PM 회전자 자석 슬롯
- **특수형**: SlotUD (사용자정의), SlotDC (DC), SlotWLSRPM (Line-Start)

### 1.2 기하학 프리미티브

```
Arc (3가지): Arc1 (시작/끝), Arc2 (중심+시작+끝), Arc3 (각도)
Line: 직선
Circle: 원
Surface: 폐곡면 (SurfLine, SurfRing)
Bore Types: BoreFlower, BoreLSRPM, BoreSinePole
```

### 1.3 권선 및 전기

```
Winding
├── type: 정현/집중
├── Qpc: 극당 슬롯/코일
├── Ntcoil: 코일당 회전수
└── Conductor (CondType11~CondType22)
    └── 전선 타입 및 저항 계산
```

### 1.4 Methods 디렉터리 (14개)

```
Methods/
├── Converter/        (DXF ↔ Pyleecan 변환)
├── Elmer/            (FEA 솔버)
├── Geometry/         (기하학 생성)
├── Import/           (외부 포맷 임포트)
├── Loss/             (손실 계산: 철심, 구리)
├── Machine/          (머신 타입별 방법)
├── Material/         (재료 특성)
├── Mesh/             (메시 생성)
├── Optimization/     (설계 최적화)
├── Output/           (결과 출력)
├── Post/             (후처리)
├── Simulation/       (시뮬레이션 관리)
└── Slot/             (슬롯별 기하학)
```

---

## 2. eMach/pyMotorGeo 실제 아키텍처

### 2.1 32개 핵심 모듈

**1단계: DXF 읽기**
```
reader.py
  ├── DXFReader: ezdxf 기반 파싱
  ├── EntityInfo: 기하학 primitive (LINE/ARC/CIRCLE)
  └── manual_parse_dxf_entities: Fallback 파서 (이미 패키지 이동됨)
```

**2단계: 기하학 분석**
```
analysis_*.py (5개)
  ├── find_origin_candidates() → origin scoring
  ├── find_concentric_radii() → 반경 감지
  ├── find_airgap_radius() → gap 추정
  ├── estimate_periodicity() → 주기성
  └── count_poles() / count_slots() → 극수/슬롯 수 자동계산
```

**3단계: 토폴로지 분류 (선택형, Phase 3 이동)**
```
topology_rotor.py
  └── classify_rotor_entities() → 회전자 타입 감지
      (SPM/IPM/SyRM/Spoke/EESM)
      **현재 상태**: Fallback 반환 (미구현)

topology_stator.py
  └── classify_stator_entities() → 고정자 분류
```

**4단계: 영역 감지 & 라벨링**
```
region_closing.py
  ├── find_closed_regions() → 폐곡면 탐지
  ├── close_gaps() → 불완전한 기하학 보정
  └── detect_boundary()

face_detection.py
  └── detect_faces() → 면 감지 (3D로의 확장)
```

**5단계: 반주기 추출**
```
half_unit.py
  ├── extract_half_unit() → 1/2 모터 추출
  ├── extract_quarter_unit() → 1/4 모터 추출
  └── reconstruct_full_motor() → 비상 복원
```

**6단계: 내보내기 & 연결**
```
export.py
  ├── export_regions_to_dxf() → 라벨링된 DXF 저장
  └── export_to_motorcad() → Motor-CAD 형식

pyleecan_bridge.py
  ├── to_machine_ipmsm() → IPMSM 인스턴스 생성
  ├── to_machine_syrm() → SyRM 인스턴스 생성
  └── extract_parameters() → 매개변수 추출

plotting.py
  └── create_interactive_visualization() → PyVista 뷰
```

### 2.2 11단계 실행 파이프라인 (자동화)

```
Call: analyze_dxf_v2(dxf_path)
  ↓ Step 1: Read DXF → entities (2000+)
  ↓ Step 2: Find origin candidates → ranked
  ↓ Step 3: Estimate airgap radius
  ↓ Step 4: Count poles & slots → (극수, 슬롯수)
  ↓ Step 5: Split rotor/stator entities
  ↓ Step 6: Classify rotor topology [OPTIONAL, returns fallback]
  ↓ Step 7: Detect closed regions (자석, 칸막이, 등)
  ↓ Step 8: Close open regions (gap filling)
  ↓ Step 9: Extract half-unit geometry
  ↓ Step 10: Detect faces
  ↓ Step 11: Export DXF or bridge
  → AnalysisResult (구조화된 출력)
```

---

## 3. 비교: Pyleecan vs eMach

| 관점 | Pyleecan (271 classes) | eMach (32 modules) |
|------|--------|--------|
| **입력** | 매개변수 기반 (설계) | DXF 기반 (역-설계) |
| **아키텍처** | 클래스 계층 (OOP) | 함수형 파이프라인 |
| **머신 타입** | 12가지 (지원 가능) | 자동 감지 (SPM/IPM/SyRM) |
| **슬롯 타입** | 50+ (매우 상세) | 자동 인식 (형태 기반) |
| **기하학** | Primitive 명확함 | EntityInfo로 통일 |
| **FEA** | FEMM, Elmer 통합 | MotorCAD 브릿지 |
| **최적화** | Scipy 기반 선택 | 미구현 |
| **토폴로지** | 명시적 선택 | 자동 감지 (선택형) |

---

## 4. 데이터 흐름 통합

### 4.1 Forward (설계중심)

```
Pyleecan 매개변수
  → Machine(IPMSM) 생성
  → Stator/Rotor 기하학
  → DXF 내보내기
  → Motor-CAD로 임포트
  → FEA 솔버 (FEMM/Elmer)
  → 효율, 손실, 토크 분석
```

### 4.2 Reverse (역-설계, CAD 분석중심)

```
실제 DXF 파일
  → eMach analyze_dxf_v2()
  → 극수, 슬롯 자동감지
  → 토폴로지 분류 (회전자/고정자)
  → 영역 감지 (자석, 칸막이)
  → Pyleecan Bridge
  → Machine(auto-detected type) 생성
  → 매개변수 추출 (극수, 슬롯, 차원)
  → SyR-e로 매개변수 전달 (최적화용)
```

### 4.3 Round-Trip (WP-B 검증)

```
SyR-e 매개변수
  → DXF 생성
  → eMach 분석
  → Pyleecan 변환
  → 검증: 극수 일치, 슬롯 일치, 차원 일치
  → 모든 솔버 비교 (FEMM, Maxwell, Motor-CAD)
  → 효율 ±5% 오차 범위 확인
```

---

## 5. 핵심 모듈 매핑 (WP-D Shortlist)

### Pyleecan (15개 우선 모듈):

1. **Machine** - 머신 베이스 클래스 (모든 타입의 기초)
2. **Lamination** - 적층 구조 (stator/rotor)
3. **Slot** - 슬롯 기하학 (50+ 타입)
4. **Winding** - 권선 배치
5. **Material** - 재료 데이터베이스
6. **Simulation** - FEA 실행
7. **SimInput** - 입력 설정
8. **Output** - 결과 저장
9. **Loss** - 손실 계산 (핵심 KPI)
10. **Convert** - DXF ↔ Pyleecan 변환
11. **DXFImport** - DXF 파일 읽기
12. **Geometry** - 기하학 primitive (Arc, Line, Surface)
13. **Bore** - 회전자 표면 형태
14. **Electrical** - 전기 특성 (저항, 인덕턴스)
15. **Post** - 후처리 및 시각화

### eMach (15개 우선 모듈):

1. **reader.py** - DXF 읽기 (ezdxf)
2. **analysis_airgap.py** - 스타터/로터 분리
3. **analysis_geometry.py** - 기하학 primitive
4. **topology_rotor.py** - 회전자 분류 (선택형)
5. **topology_stator.py** - 고정자 분류
6. **region_closing.py** - 폐곡면 감지
7. **half_unit.py** - 반주기 추출
8. **face_detection.py** - 면 감지
9. **export.py** - DXF 내보내기
10. **pyleecan_bridge.py** - Pyleecan 연동
11. **core.py** - EntityInfo 및 변환
12. **plotting.py** - 시각화 (PyVista)
13. **analysis_periodicity.py** - 주기성 감지
14. **entity_properties.py** - 기하학 특성 계산
15. **validation.py** - 입력 검증

---

## 6. 실행 상태

### Pyleecan (gitfolder/pyleecan)
- ✅ **완성도**: 90%+ (산업 수준, 학술 게시)
- ✅ **문서**: 광범위 (튜토리얼 10+개, Class 문서)
- ✅ **테스트**: 단위 테스트 완비
- ✅ **지원 솔버**: FEMM, Elmer, 메시 생성기
- ⏳ **제한사항**: 학습곡선 높음, Python-heavy

### eMach/pyMotorGeo (Emlab_emach/Class/pyMotorGeo)
- ✅ **완성도**: 70% (활발한 개발)
- ✅ **Cells 1-20**: 작동 (DXF 로드 ~ 반주기 추출)
- ⚠️  **Cells 21-27**: 토폴로지 부분 실패 (fallback 반환)
- ✅ **결정**: Phase 3로 선택형 이동 (비차단)
- ✅ **장점**: DXF-first, 자동 인식, 빠른 피드백

---

## 7. 통합 실행 계획

### WP-A (데이터 교환 계약 정의)
- DXF 레이어/블록 표준화
- 메타데이터 헤더 (극수, 슬롯, 타입)
- 선택형 의미론 블록 (영역 라벨)

### WP-B (10케이스 검증 벤치마크)
1. Pyleecan library motor (SCIM)
2. Pyleecan library motor (IPMSM)
3. SyR-e export (SPM)
4. SyR-e export (SyRM)
5. eMach실제 DXF (미분류)
6-10. 추가 변형

**검증 절차:**
```
Motor → DXF (export)
      → eMach분석 (극수/슬롯 추출)
      → Pyleecan 변환
      → Motor-CAD 임포트
      → FEMM 솔버
      → 효율 ±5% 검증
```

### WP-C (UML 수집 분석)
- ✅ **완료**: 본 문서 (Pyleecan 271 + eMach 32)

### WP-D (shortlist & 통합 계획)
- 우선모듈 15개/프레임워크
- 의존성 맵
- 다음 단계: PlantUML 다이어그램 생성

---

## 8. 다음 단계 (이번 주)

1. **PlantUML 작성** (Pyleecan + eMach 실제 UML 다이어그램)
   - [02_Pyleecan_Architecture_UML.puml](02_Pyleecan_Architecture_UML.puml) ✅ 업데이트 완료
   - [06_eMach_pyMotorGeo_Real_Architecture.puml](06_eMach_pyMotorGeo_Real_Architecture.puml) ✅ 새로 작성

2. **WP-A 상세 정의**: CAD 교환 계약 v1.0
   - DXF 구조 명세
   - 메타데이터 스키마
   - 검증 규칙

3. **WP-B 신청**: 10 참조 모터 세트 선정
   - 극수/슬롯 조합 다양성
   - 토폴로지 다양성 (SPM, IPM, SyRM)

4. **통합 테스트**: eMach → Pyleecan 브릿지 검증
   - analyze_dxf_v2() → pyleecan_bridge() 흐름
   - 매개변수 추출 정확도 확인

---

## 참고

- **CODEBASE_ARCHITECTURE_ANALYSIS.md**: 전체 271 클래스 상세 목록
- **COMPLETE_CLASS_REFERENCE.md**: 알파벳 순 클래스 레퍼런스
- **METHOD_SIGNATURES_AND_DATAFLOW.md**: 메서드 시그니처 및 11단계 분석 흐름
- **GUIDE_AND_SUMMARY.md**: PlantUML 작성 가이드
