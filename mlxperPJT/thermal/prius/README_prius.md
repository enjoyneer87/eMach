# Prius 모터 열해석 패키지 (실제 Toyota Prius geometry)

IcepakFEA 워크샵 모터와 **다른 실제 Prius**(OD 269mm / 스택 83.8mm / 8극 48슬롯 V-IPM).
Maxwell 전자계 손실 → 형상 → MAPDL 하이브리드 열해석 → 시각화 → **Fluent CFD 대조**까지
전 과정을 코드로 재현·보존.

## 소스 파일
- **Maxwell 손실**: `Prius_Model_24R2.aedt` (Maxwell 2D Transient, full 360, depth 83.8mm,
  250A/3000rpm/gamma60). 19R2 원본 → 24R2 재저장으로 v261 마이그레이션.
- **형상**: `PriusMotor_3D45degree.stp` (Fluent EM-Thermal 훈련 M02, 45° 섹터)
- **Fluent CFD 참조**: `PriusMotor_3D45degree.cas.h5` / `.dat.h5` (켤레열전달 정상해)

## 파이프라인 (scripts/, 번호순 실행)

| # | 스크립트 | 역할 | 환경 |
|---|----------|------|------|
| 01 | `01_maxwell_extract_losses.py` | Maxwell 2D 오픈+솔브 → StrandedLoss/SolidLoss/CoreLoss (시간평균) | pyaedt+AEDT |
| 01b | `01b_maxwell_per_object_coreloss.py` | OutputPerObjectCoreLoss → 스테이터/로터 철손 분리 시도 | pyaedt+AEDT |
| 02 | `02_step_to_cdb.py` | STEP → active part 자동분류 → gmsh 컨포멀 → 45°×8 → SOLID87 CDB | gmsh |
| 02b | `02b_mesh_check_render.py` | CDB CDREAD 검증 + 재료별 메시 렌더 | pymapdl+pyvista |
| 03 | `03_mapdl_thermal.py` | 열해석: 이방성코일+정션결합+CEND회로+냉각 → 과도 900s | pymapdl |
| 04 | `04_mapdl_viz.py` | 코일/자석/부품이력 시각화 | pyvista |
| 05 | `05_fluent_extract_zone_temps.py` | Fluent .h5 → 존별 온도 통계 (h5py, Fluent 불요) | h5py |
| 06 | `06_fluent_plots_and_compare.py` | Fluent 존 온도 바 + Fluent vs MAPDL 비교 | matplotlib |
| 07 | `07_fluent_pyfluent_contour.py` | pyfluent로 CFD 온도 컨투어 (Fluent 라이선스) | pyfluent |

## 손실 (data/prius_losses.json)
- 슬롯 동손 **2311.7 W** (2D StrandedLoss = 슬롯분, FEM HGEN)
- 엔드 동손 **1038.7 W** (슬롯 × V_end/V_slot=0.449, CEND 회로 주입)
  - 2D는 슬롯만 주므로 엔드는 형상 체적비로 산정 (엔드 형상은 별도 볼륨)
- 자석 23.8 W, 철손 650 W (스테이터 585 / 로터 65, ⚠ 90/10 추정 — 01b 정밀화 시도)

## 메시 (prius_motor_mesh.cdb, git 미포함 93MB)
- 402,229 노드 / 263,384 SOLID87. active part 자동분류(바운딩박스):
  스테이터·로터·자석 2개·코일 6슬롯·샤프트. 코일엔드·하우징·프레임 제외.
- 45° 섹터 ×8 회전(full axial, z미러 없음). V자형 IPM 자석 확인.

## MAPDL 결과 (t=900s, 250A 고부하)
| 부품 | max °C |
|------|--------|
| 코일 | 185.6 (H급 180°C 초과) |
| 스테이터 | 181.8 |
| 로터 | 166.0 |
| 자석 | 161.6 (감자 주의) |
| 샤프트 | 133.0 |

## Fluent CFD 참조 (data/fluent_prius_zone_temps.json)
셀존 10개: stator / rotor / magnet / shaft / airgap / frame / insulation /
**phase(=코일)** / **fluid_jacket(워터재킷)** / cover.

| 존 | max °C |
|----|--------|
| coil (phase) | 88.3 |
| stator | 76.2 |
| rotor | 70.2 |
| magnet | 70.0 |
| fluid_jacket | 41.9 (실제 워터재킷 냉각) |

**⚠ MAPDL vs Fluent 절대값 직접비교 불가**: 손실 레벨(운전점)과 냉각 조건이 다름.
- Fluent: 자체 매핑 손실 + 실제 워터재킷(33°C) 켤레열전달 → 저온
- MAPDL: 250A 고부하 2D 손실 + JAC279식 회로 냉각 → 고온
- **경향은 일치**: 두 해석 모두 코일 > 스테이터 > 로터 ≈ 자석 > 샤프트.
- 동일조건 비교하려면: Fluent 매핑 손실 + 워터재킷 HTC 를 MAPDL 에 반영.

## 유의
- 냉각은 JAC279식 회로(WJ 상90°/ATF 하90°/하우징) — Prius 실제 냉각과 다름(HTC 조정 가능)
- 철손 스테이터/로터 분리 90/10 추정. per-object(01b)는 2D 리포트 API 제약
- 250A/3000rpm은 이 2D 모델 운전점. 열정상상태(900s) 값
