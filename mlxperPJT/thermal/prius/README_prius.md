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

---

## 교차검증: MAPDL ↔ Fluent CFD (2026-07-21)

Fluent CFD를 정답지로, MAPDL 하이브리드를 **동일 조건**(Fluent 손실 + 워터재킷 냉각)에
맞춰 검증. 냉각을 JAC279 회로 → 스테이터 OD 균일 워터재킷 대류(냉각수 27°C, 유효
HTC 3000)로 교체 (`08_mapdl_waterjacket.py`, PRIUS_LOAD=low/high).

### 손실 (Fluent case에서 pyfluent로 추출한 W/m³ 소스)
- 저부하(Fluent 원본): 코일 2.0e6 / 스테이터 188,657 / 로터 74,731 / 자석 83,655
- 고부하(250A): 코일 3.077e6 / 스테이터 265,900 / 로터 93,400 / 자석 171,200
- Fluent-250A: 소스항을 250A 밀도로 교체 후 CHT 재솔브 (`09_fluent_250A_resolve.py`)

### 검증 매트릭스 (코일 max °C)
| | 저부하 (Fluent 조건) | 고부하 (250A) |
|---|---|---|
| **MAPDL + 워터재킷** | 88.3 | 119.2 |
| **Fluent CFD + 워터재킷** | 88.3 | 118.2 |
| MAPDL + JAC279 (보존, 참조) | — | 185.6 |

**핵심: 코일 최고온이 양 부하 모두 1°C 이내 일치** (저부하 Δ0.0, 250A Δ1.0). MAPDL
하이브리드 방법이 Fluent CFD를 정량적으로 재현함을 검증. 워터재킷은 반경방향
온도구배(외곽 40°C ~ 코일 116°C)를 만들어 JAC279 균일장과 확연히 다름.

### 한계
- 로터/자석은 MAPDL이 ~13-20°C 높음: 공극을 순수 전도(0.75mm)로만 봐서 회전유동
  대류를 미반영. 개선: 공극 유효전도율 상향 또는 하우징+워터재킷 실기하 추가.
- 유효 재킷 HTC(3000)는 Fluent 결과 역산 보정값. 실제는 프레임 전도+재킷 대류.

---

## 표준 시각화 패키지 (thermal_viz)

어떤 GIF/PNG를 뽑을지 **규격화**해 재현성 확보. `mlxperPJT/thermal/thermal_viz.py`
(재사용 패키지) + `scripts/render_prius_viz.py`(Prius 드라이버).

```
python scripts/render_prius_viz.py all      # 워터재킷 저/고부하 표준세트 일괄
python ../../thermal_viz.py <file.rth> <out_dir> [label] [clim_lo]   # 범용 CLI
```

### 표준 출력 세트
**GIF (과도)**
| 파일 | 내용 |
|---|---|
| `transient_3d_cut.gif` | 3D 반단면 컷어웨이(외피 반쪽 clip + x=0 단면 slice) — 대표 뷰 |
| `transient_dashboard.gif` | **종합 대시보드**: 상단[3d_cut 온도장 \| circuit_3d 회로] + 하단[온도이력 곡선·현재시각 커서], 세 뷰 시점동기 |
| `transient_circuit_3d.gif` | 열등가회로 3D 오버레이 과도(노드 색=온도 시간전개) |
| `transient_core.gif` | z=0 정단면, 전 부품 온도컬러(가림 없음) |
| `transient_coilmag.gif` | 코일+자석 내부부품(스테이터/로터 반투명 고스트) |
| `transient_coil_z0.gif` | 코일 z=0 슬라이스 |

**PNG (최종 t)**
| 파일 | 내용 |
|---|---|
| `contour_iso.png` / `contour_z0.png` | 3D iso 표면 / z=0 반경단면 |
| `cut_3d.png` | 3D 반단면 컷어웨이(마지막 프레임) |
| `coil_only.png` / `magnet_only.png` | 코일 / 자석(+로터 고스트) 단독 |
| `component_history.png` | 부품별 온도 시간이력 |
| `circuit_3d.png` | 열등가회로 3D 오버레이(반투명 형상+튜브 저항+색구 노드) |

### 핵심 기법 (재현 노트)
- **3d_cut**: 볼륨 clip 은 VTK 크래시 → 외피(surface) 반쪽 clip + 단면 slice 조합.
  `ext.clip(normal=(1,0,0), invert=True)` + `solid.slice(normal="x")`,
  `view_vector((1,-0.45,0.35))`.
- **z_trim**: Prius 메시는 미터 단위, 샤프트가 축방향 돌출(±0.1m) → 활성부(±0.045m)로
  트림해 깔끔한 반단면. 셀 중심 기준 마스킹 + 원본 grid 인덱스를 `gid` point_data로
  실어 이중추출에도 온도매핑 보존.
- **circuit_3d**: 노드 위치는 형상 반경 `tv.R`·스택반길이에 스케일, 노드 온도는 실제
  부품 최고온에서 도출(`node_T_fn(T)`) → 어떤 형상에도 자동 적응. PNG(최종)와
  과도 GIF 공용 렌더(`_render_circuit`).
- **dashboard**: 기존 3d_cut 프레임 렌더 + 이력곡선(`_draw_history`, 현재시각 세로
  커서·현재값 점)을 매 프레임 좌우 결합(`_hstack`, PIL 높이맞춤) → 필드와 곡선을
  동시에 보는 직관적 뷰.
- 재료번호 규약(MAPDL): 1 stator 2 magnet 3 coil 4 shaft 5 rotor.
