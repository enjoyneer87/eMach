# JAC279 방식 IPM 모터 열해석 — 작업 컨텍스트

> 이 문서는 `jac279_fem_network_pymapdl.ipynb` 가 만들어지고 수정된 배경을 정리한 것입니다.
> 원 대화 세션: **"IcePak model from Maxwell design"** (Claude Code, 2026-07-13)

## 1. 목표

JMAG **JAC279** *"Thermal Analysis Accounting for Cooling of the IPM Motor"* 의 해석 개념
— **3D 열 FEM + 열등가회로 하이브리드** — 을 Ansys **PyMAPDL** 로 재현한다.

개념 매핑 (JMAG → MAPDL):

| JMAG | MAPDL |
|------|-------|
| 3D 솔리드 열 FEM | `SOLID87` (10절점 사면체 열요소) |
| Heat Transfer Boundary (Referred by Circuit Component) | `SURF152` + extra node (`KEYOPT(5)=1`) |
| Thermal Resistor (R) | `COMBIN14`, `KEYOPT(2)=8` (TEMP DOF), 실상수=열컨덕턴스 |
| Heat Capacity (C) | `MASS71`, `KEYOPT(3)=1`, 실상수=열용량 |
| Fixed Temperature (WJ/ATF/외기) | `D, TEMP` 구속 |

하우징·워터재킷·ATF 풀 등 **냉각계는 열등가회로(lumped)** 로, **모터 능동부(적층코어·자석·코일·샤프트)는 3D FEM** 으로 푼다.

## 2. 대상 모델 (확정)

- **AEDT 프로젝트**: `Electric_Motor_Mechanical_AEDT_3D_part1`
- **디자인**: `IcepakFEADesign1` (Factory=IcepakFEA = AEDT Mechanical Thermal)
  - 사용자 워크플로우(`WS01_2_AEDT_Mechanical_Thermal_build.ipynb`)에서 `DESIGN_INDEX=2` 로 지칭한 **"3번째 디자인"** 이 바로 이 열디자인이다.
- **형상**: 8극 / 48슬롯 IPM, 원 모델은 **1/8 주기섹터**(1극, `Boundary_Master`/`Boundary_Slave`).
  - JAC279식 냉각(상부 90° 워터재킷 / 하부 90° ATF)은 **원주 비대칭**이라 섹터에 직접 못 얹는다.
  - → **결정: 1/8 섹터를 360°로 8배 패턴한 뒤 JAC279식 비대칭 냉각을 적용**한다.

### 실측 기하 (AEDT 설계변수)

| 항목 | 값 | 반경(m) |
|------|-----|---------|
| DiaShaft | 44.45 mm | R_SHAFT = 0.022225 |
| RotorDia (로터 외경) | 130 mm | R_ROT_OUT = 0.065 |
| Airgap | 1 mm | GAP = 0.001 |
| DiaGap (스테이터 보어) | 132 mm | R_STA_IN = 0.066 |
| DiaOuter/DiaStatorYoke | 198 mm | R_STA_OUT = 0.099 |
| Stator_Lam_Length | 160 mm | STACK = 0.160 |
| Rotor_Lam_Length | 150 mm | ROT_STACK = 0.150 |
| EndWindingLength | 60 mm | — |
| MachineRPM / IPeak | 4000 rpm / 267 A | — |

### 재료 (AEDT)

| 부품 | 재료 | MAPDL mat# |
|------|------|-----------|
| Stator_Lamination_1 | M350-50A | 1 |
| Rotor_Lamination_1 | M350-50A | 5 (동일물성, 손실분리용 별도번호) |
| Magnet_* (36 세그) | N30UH (NdFeB) | 2 |
| Ph1/Ph2/Ph3_* (코일 5) | Copper | 3 |
| Shaft_1 | Steel_1008 (k=52) | 4 |
| Rotating_Band_out / Whole_Region | (공기 영역 — **임포트 제외**) | — |

## 3. 노트북 구조 (`jac279_fem_network_pymapdl.ipynb`)

- **0~2장**: 파라미터(실측 기하) / MAPDL 기동 / 요소·재료(mat 1~5)
- **3장 (링 경로, 검증용 fallback)**: 실측 치수 기반 동심 링 360° — 즉시 실행 가능한 참조 해석
- **3B장 (CAD 경로, 실형상 — 본 타깃)**:
  - **3B-1**: PyAEDT(0.24 API)로 열린 IcepakFEA 디자인에 attach → 재료군별 `.sat` export
  - **3B-2**: MAPDL `~SATIN` 임포트 → `VGEN` 로 45°×8 회전복제(360° 패턴) → `VGLUE` → 재료할당 → 메시
- **4장**: 열등가회로 노드 (하우징 세그먼트·샤프트·공극·냉각 고정온도)
- **5장**: `SURF152` 로 FEM 경계면 ↔ 회로 노드 연결 (스테이터 외경 상/하 90° 비대칭 냉각)
- **6장**: 발열 — 재료군별 총손실 → 체적발열률(HGEN). 링/CAD 공통 (MAT 기반)
- **7장**: 과도 해석 (transient)
- **8장**: 후처리 — 코일 온도 이력 (JAC279 Table 3-1 비교)

## 4. 이전(초기) 버전에서 고친 오류들

1. **pyaedt API 버전 불일치**: `specified_version`/`new_desktop_session` (구 API) → **`version`/`new_desktop`** (0.24). AEDT 버전 `2025.1` → **`2026.1`** (실행 세션 v261).
2. **`export_3d_model`**: 기본 포맷 `.step` → `file_format=".sat"`, `assignment_to_export=objs` 로 명시.
3. **오브젝트 필터**: 실제 이름 기준(`Stator_Lamination`, `Rotor_Lamination`, `Magnet*`, `Ph1/2/3*`, `Shaft*`), 공기영역(`Rotating_Band_out`,`Whole_Region`) 제외. 솔리드만(`GetObjectsInGroup("Solids")`).
4. **VATT 무시 버그(구 10번 셀)**: `VSEL,LOC,X`(centroid) 대신 재료군을 임포트/패턴 단위로 추적해 `VATT` → `VGLUE` 후 MAT 속성 유지.
5. **섹터↔360° 불일치**: MAPDL `VGEN` 회전복제로 360° 패턴 후 비대칭 냉각.
6. **발열 할당**: 링 전용 BANDS → **재료(MAT) 기반**으로 통일 (링·CAD 공통).

## 5. 실행 방법

```bash
conda activate pymotorenv_310      # 또는 PyMotorEnv_310 venv
jupyter lab jac279_fem_network_pymapdl.ipynb
```

- **AEDT 세션을 먼저 띄워** 대상 프로젝트를 열어 둔다 (`IcepakFEADesign1` 활성 불필요, 이름으로 attach).
- **CAD(실형상) 경로**: 3장(링) 스킵 → 3B-1, 3B-2 실행 → 4장부터 계속.
- **링(검증) 경로**: 3B 스킵 → 3장 실행 → 4장부터. 처음엔 링으로 전체 흐름을 한 번 확인 권장.
- 마지막 `mapdl.exit()` 셀은 결과 검토가 끝난 뒤에만 실행.

## 6. 남은 검증 포인트 (실행하며 확인 필요)

- **손실값**: 6장 `LOSS_*` 는 JAC279 예시값(placeholder). 이 모터의 **Maxwell 손실 리포트** 값으로 교체.
- **`~SATIN` / `VGLUE`**: 임베디드 자석·슬롯 코일이 있어, 임포트 형상이 지저분하면 `VGLUE` 가 실패할 수 있음 → `mapdl.btol` 조정 또는 AEDT 에서 형상 단순화.
- **`SURF152` 면 선택**: 코일엔드 냉각은 재료(구리)+축위치(|z|>STACK/2) 기반으로 근사. 실제 노출면과 GUI 대조 권장.
- **하우징 회로 정수**(C_HOUSING, R_HOUS_*): JAC279 하우징 기준값 — 이 모터 하우징(`Motor Housing` 프로젝트)에 맞게 조정 가능.
