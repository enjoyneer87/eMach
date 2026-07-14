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
- **4장**: 열등가회로 노드 (하우징 세그먼트·샤프트·공극·냉각 고정온도) — `NET_NODES`/`NET_EDGES`/`NET_CAPS` 로 구조화 (10장 시각화 재사용)
- **5장**: `SURF152` 로 FEM 경계면 ↔ 회로 노드 연결 (스테이터 외경 상/하 90° 비대칭 냉각)
- **6장**: 발열 — 재료군별 총손실 → 체적발열률(HGEN). 링/CAD 공통 (MAT 기반)
- **7장**: 과도 해석 (transient)
- **8장**: 후처리 — 코일 온도 이력 4점 (팔레트 고정 4색 + 직접 라벨)
- **9장**: FEA 컨투어 시각화 (pyvista, inferno 순차램프) — 외표면 등각 / x=0 수직 절단(WJ↔ATF 비대칭) / z=0 횡단면. percentile clim + 범위 밖 하한색 클립
- **10장**: 열등가회로 다이어그램 (matplotlib) — 노드색=온도(FEA 와 공용 램프), 사각=고정온도, 원=부동, 실선=COMBIN14(G 라벨), 점선=SURF152 결합, FEM 영역 박스(avg/max)

## 4. 이전(초기) 버전에서 고친 오류들

1. **pyaedt API 버전 불일치**: `specified_version`/`new_desktop_session` (구 API) → **`version`/`new_desktop`** (0.24). AEDT 버전 `2025.1` → **`2026.1`** (실행 세션 v261).
2. **`export_3d_model`**: 기본 포맷 `.step` → `file_format=".sat"`, `assignment_to_export=objs` 로 명시.
3. **오브젝트 필터**: 실제 이름 기준(`Stator_Lamination`, `Rotor_Lamination`, `Magnet*`, `Ph1/2/3*`, `Shaft*`), 공기영역(`Rotating_Band_out`,`Whole_Region`) 제외. 솔리드만(`GetObjectsInGroup("Solids")`).
4. **VATT 무시 버그(구 10번 셀)**: `VSEL,LOC,X`(centroid) 대신 재료군을 임포트/패턴 단위로 추적해 `VATT` → `VGLUE` 후 MAT 속성 유지.
5. **섹터↔360° 불일치**: MAPDL `VGEN` 회전복제로 360° 패턴 후 비대칭 냉각.
6. **발열 할당**: 링 전용 BANDS → **재료(MAT) 기반**으로 통일 (링·CAD 공통).

### 4b. 링 경로 end-to-end 실행으로 잡은 솔버 버그 3건 (2026-07-14)

7. **SURF152 `KEYOPT(8)` 기본값은 대류 무시** — 증상: 회로 노드 전부 초기온도 고정,
   GAP 노드 부동(small pivot), 솔리드 단열 과열. **`KEYOPT(2,8,2)` (대류 포함) 필수.**
   큐브 검증: extra node 온도가 해석해(20 + 1000 W / 50 W/K = 40.00°C)와 정확히 일치
   → extra node 열수지는 대칭으로 성립.
8. **ESURF 가 '현재 REAL 상수'를 SURF152 에 물림** — 4장 회로(COMBIN14, real 101+)
   직후 ESURF 하면 real 공유로 SOLVE 에서
   "Real constant N referenced by element types 3 and 2" 에러. → SURF152 전용
   `R,1` 정의 후 ESURF 전에 `REAL,1` 고정.
9. **곡면 midside 노드 sagitta** — 정확반경 `NSEL`(±1e-5)로는 2차 사면체 midside
   노드(현 위에 위치, 반경 오차 ~ESIZE²/8R)가 빠져 면이 불완전 → ESURF 미생성
   (스테이터 보어에서 발생). → 반경 허용오차를 `1.6·ESIZE²/(8R)` 로 확대.

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

## 7. 세션 핸드오프 — 현재 상태 요약 (2026-07-14 기준)

새 세션이 이어받을 때 이 절만 읽어도 되도록 정리.

### 환경

| 항목 | 값 |
| --- | --- |
| Python | `PyMotorEnv_310` venv, Python 3.10.11 |
| pyaedt | 0.24.1 → **`version=`/`new_desktop=` 신 API 사용** (구 `specified_version`/`new_desktop_session` 은 이 버전에서 오류) |
| pymapdl | 0.73.2 |
| AEDT | **2026.1 (v261)** 세션에 대상 프로젝트가 열려 있어야 함 |
| MAPDL 라이선스 | 서버 미체크아웃 시 *VERIFICATION RUN* 으로 떠서 `~SATIN`/대형 솔브가 막힘 → `ANSYSLMD_LICENSE_FILE` 확인 |

### 검증 완료 (라이브 테스트 통과)

- **3B-1 AEDT export**: 실제 2026.1 세션 attach + 재료군별 `.sat` 생성 확인
  (자석 36 / 코일 5 / 적층 2 / 샤프트 1, 공기영역 `Rotating_Band_out`/`Whole_Region` 제외 정상)
- **6장 MAT 기반 손실**: `VSEL,MAT` → `VSUM` → `BFV,HGEN` idiom 검증.
  선택 볼륨수 판정은 `*GET,,VOLU,0,COUNT` 사용 (`NUM,MAXD` 는 선택 무관이라 가드로 부적합 — 수정됨)
- **링 경로 end-to-end (2026-07-14)**: 메시(18.8k 노드) → 회로 → SURF152 → 과도해석(900 s, 20 스텝)
  → 후처리/시각화까지 전체 통과. 결과 경향이 JAC279 와 일치:
  - 회로 노드: H_WJ 72.3 / H_ATF 71.3 (냉각측) vs H_RST 106.6 / AIR 106.7 (공기측)
  - 코일 4점(t=900 s): Center_WJ 106.2 < Center_ATF 109.6 (WJ 가 중앙부 냉각),
    Tip_ATF 107.2 < Tip_WJ 109.7 (ATF 가 코일엔드 직접 냉각) — JAC279 Table 3-1 경향 재현
- **SURF152 extra node 열수지**: 큐브 검증에서 해석해와 일치 (40.00°C 정확)
- 노트북 33셀 전체 Python 문법 검증 통과

### 미검증 (다음 세션에서 실행 필요)

- **3B-2 `~SATIN` 임포트 → VGEN 360° 패턴 → VGLUE → 메시**: 라이선스 세션에서 미실행
  (이 환경의 MAPDL 이 VERIFICATION RUN 으로만 떠서 ACIS 번역기가 비활성. 로직/구문은 검증됨)
- **CAD 실형상 경로의 7~10장**: 링 경로로는 검증됐으나 실형상 메시로는 미실행

### git 상태

- `enjoyneer87/eMach` (develop) 커밋 `aeae8e7` 로 푸시 완료: 이 문서 + 노트북 (`mlxperPJT/thermal/`)
- 상위 리포(NvidiaNemo)의 서브모듈 포인터는 **미커밋** (`M eMach` 상태)

### 관련 파일

- `WS01_2_AEDT_Mechanical_Thermal_build.ipynb` (같은 폴더): AEDT **GUI 안에서** 360° 패턴+열모델을 만드는 별도 워크플로우.
  본 노트북(MAPDL 경로)은 패턴을 MAPDL `VGEN` 으로 하므로 **이 노트북 실행에는 불필요** — 참고용.
- 작업본 사본: `D:\KDH\simVary\Ansys_Thermal\jac279_fem_network_pymapdl.ipynb` (동일 내용)
