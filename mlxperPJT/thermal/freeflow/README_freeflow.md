# FreeFlow(e10) 오일냉각 열해석 패키지

Ansys **FreeFlow**(GPU SPH 자유표면 CFD) 오일냉각 모델(`FreeFlowProject`)의 모터 =
**e10 모터**(JEET AC손실 논문 모터, Motor-CAD→Maxwell). 형상·오일유동 시각화 +
e10 손실 → MAPDL 열해석 → (추후) FreeFlow 온도장 재솔브 커플링.

> **산출물(이미지·GIF·데이터)은 Google Drive** 보관 (코드만 Git). thermal_viz 규약과 동일.

## 모터 = e10 (FreeFlow STL ↔ e10 Maxwell 치수 일치)
| 항목 | 값 | 출처 |
|---|---|---|
| 스테이터 OD / bore | 198 / 142.5 mm | STL & e10 2D Maxwell 일치 |
| 스택 길이 | 150 mm | 동일 |
| 로터 OD / 샤프트 | 142.5 / 46.9 mm | e10 Maxwell |
| 슬롯 / 극 | 48 / 8 | e10 Maxwell |
| 운전점 | **16000 RPM, 460A RMS(650A peak), 720V, 진각 43.3°** | e10Turn6V261.mot (실측) |

## 소스
- 형상: `FreeFlowProject/Geometry/*.stl` (Housing/Stator/Winding/Rotating/Inlet/Outlet)
- 오일 SPH 결과: `Project.freeflow.files/simulation/*.sph` (HDF5, 801 스텝, 위치+속도+온도)
  - ⚠️ **온도 미해석(전부 0K), 유동만** 계산됨 → viz는 속도 기반
- e10 손실/운전점: `e10_6TSweep/refModel/e10Turn6V261.mot` (Motor-CAD)
- e10 EM: `e10_20251226/..._ANSYSEM_2D.aedt`(2D), `e10Turn6V261_3D_..._3D.aedt`(3D)

## 파이프라인 (scripts/, 번호순)
| # | 스크립트 | 역할 | 도구 |
|---|---|---|---|
| 01 | `01_e10_motorcad_losses.py` | e10 .mot → 운전점+손실 (**ActiveXParametersMotorCADv261.txt** 파라미터명) | ansys.motorcad |
| 02 | `02_ff_dimensions.py` | STL 치수·극수 추출 | pyvista |
| 02b | `02b_ff_section.py` | 고정자·회전자 z단면 (전자계 형상 확인) | pyvista |
| 02c | `02c_maxwell_geom_extract.py` | **e10 Maxwell 2D → 로터적층·V자석·샤프트 단면 폴리곤 추출** | pyaedt |
| 03 | `03_stl_to_cdb.py` | 스테이터+권선 watertight STL → gmsh 체적메시 → SOLID87 CDB | gmsh |
| 03b | `03b_rotor_from_maxwell.py` | **Maxwell 2D 45°섹터(샤프트+로터+더블V자석 ×8) gmsh OCC 3D + 스테이터/권선 병합** | gmsh OCC |
| 04 | `04_mapdl_thermal.py` | **JAC279식 하이브리드: 3D FEM(1~5) + 오일냉각 열등가회로(자켓+스프레이) 과도해석** | pymapdl |
| 05 | `05_geometry_viz.py` | STL 형상 부품별 렌더(iso/cutaway) | pyvista |
| 06 | `06_oil_static_viz.py` | 오일 SPH 입자(속도) + 형상 오버레이 | pyvista+h5py |
| 07 | `07_oil_transient_gif.py` | 오일 나선유동 transient GIF | pyvista+h5py+imageio |
| 09 | `09_timing_comparison.py` | Icepak/FreeFlow/MAPDL 계산시간 비교차트 | matplotlib |
| 10 | `10_mapdl_dashboard_viz.py` | **하이브리드 결과 표준세트+dashboard GIF — `thermal_viz` 재사용 + FreeFlow 냉각회로빌더** | thermal_viz |

## MAPDL 열해석 = JAC279식 하이브리드 (FEM + 오일냉각 열등가회로)
**Prius(JAC279)와 동일 방식**: 3D FEM 능동부 + 열등가회로 냉각계. 냉각회로만 FreeFlow
오일냉각 토폴로지로 이식 — **OIL(공급 70°C) → JACKET(스파이럴 자켓, 스테이터 OD 대류)
+ SPRAY(엔드턴 오일 스프레이) + GAP_S/GAP_R(공극) + SHF(샤프트/베어링)**.
회로소자: `MASS71`(열용량)·`COMBIN14`(열컨덕턴스)·`SURF152`(FEM표면↔회로노드 대류결합).

### 형상: 로터+자석+샤프트를 Maxwell 2D에서 재구축 (v2 메시)
1차 메시는 FreeFlow STL의 로터(Rotating.stl)가 자석포켓 자기교차(non-manifold)라
**단순 실린더**로 대체 → 자석·샤프트·로터적층이 없었음. **v2에서 근본 개선**:
- `02c` e10 Maxwell 2D(45°섹터, 8극)에서 **로터적층(R23.5~70.27mm)+더블V 자석 4개/폴
  (n42eh)+샤프트(R23.455mm)** 단면 폴리곤 추출(스테이터 OD 99mm로 STL과 좌표계 일치 확인).
- `03b` gmsh OCC로 샤프트·로터·자석 프리즘(섹터 ×8 회전=**32자석**) 생성·fragment(컨포멀)
  → tet10, 재료 분류(bbox반경/COM 근접). **엔드턴 포함 스테이터+권선 STL 메시(1/3)와 병합**.
- 결과 v2 메시: **1,113,924절점 / 737,265 tet10**, 재료 **1 stator·2 magnet·3 winding·
  4 shaft·5 rotor**. (`viz/mapdl/mesh_v2_zsection.png`에서 더블-V 8극 확인)

### 결과 (460A RMS/16000rpm, 오일 70°C, 과도 900s)
| 부품 | max °C | mean °C |
|---|---|---|
| **Winding(권선)** | **152.2** | 114.0 |
| **Stator** | 126.0 | 115.7 |
| **Magnet** | 86.9 | 86.2 |
| **Rotor** | 86.9 | 85.5 |
| **Shaft** | 84.9 | 83.8 |

회로노드: OIL 70 → JACKET 84.4 / SPRAY 91.9 / GAP_S 122.3 / GAP_R 87.0 / SHF 70.3°C.
솔브 13.3분(1.1M절점, 22스텝). **슬롯 구리(코어 내부, 절연제한 k=5)가 152°C로 최고**
— 스프레이는 엔드턴만 직접 냉각, 슬롯분은 코어 통해서만 배열. 자석 86.9°C(N42EH
감자한계 여유). `viz/mapdl/transient_dashboard.gif`(좌 FEM반단면+냉각회로 / 우 온도이력).

### 단순 균일-HTC 모델(참조, 1차)
초기엔 외곽면 균일 HTC(2000)로 정상상태만: winding 95.6/stator 74.8/rotor 72.1°C(13.5s).
오일이 전 표면을 70°C로 직접 냉각한다고 본 낙관적 근사 → 하이브리드가 실제 열구배 반영.

### 메시 트러블슈팅 (재현 노트, 중요)
- **STL→tet10** "Zero volume" 반복실패: 부품결합 노드병합이 병합前 퇴화검사를 무력화가
  근본원인. `03_stl_to_cdb.py`: 병합**後** 코너부호체적 필터(2% 제거)+중간노드 직선화로 해결.
- **CDB EBLOCK(SOLID87 tet10)**: 10노드는 `(19i10)`에서 **11헤더+8노드 / 나머지2노드
  줄바꿈** 필수. 한 줄에 다 쓰면 노드는 로드되나 **요소 0개**(무증상 실패). `03b` writer 참조.
- **stale MAPDL 재연결**: 실패한 이전 run의 인스턴스에 붙으면 깨진 상태 그대로 → 매 솔브
  전 ANSYS 프로세스 완전종료 + 새 run_location.

## 손실 처리 (data/e10_losses.json)
- **운전점은 e10 .mot에서 실측**(16000rpm/460A). 
- **손실값은 Prius 250A 추정 분포**(구리3350/고정자철585/로터철65/자석24 W): e10 활성체적
  이 Prius의 ~0.97배로 유사. **사유**: Motor-CAD `do_magnetic_calculation`/`do_magnetic_
  thermal_calculation` 이 injected-loss 출력을 0 반환(자기↔열 연동/계산옵션 미설정, 헤드리스).
  파라미터명은 ActiveX 참조로 정확(에러 아닌 0). **실측 손실은 GUI 솔브 후 재추출로 대체 가능.**
- Motor-CAD 손실 정확 파라미터명: 구리 `Armature_Winding_Loss_Total`, 고정자철손
  `Loss_[Stator_Back_Iron]`+`Loss_[Stator_Tooth]`, 회전자철손 `Loss_[Rotor_Back_Iron]`+
  `Loss_[Rotor_Tooth]`, 자석 `Loss_[Magnet]`.

## 냉각 모델 (열등가회로 = FreeFlow 오일냉각)
오일(ATF, ρ825/cp2000) 공급 70°C, 유량 ~0.11 kg/s(≈8 LPM). FreeFlow 실제 냉각을 회로화:
- **JACKET**: 스파이럴 자켓 오일이 스테이터 OD 냉각(HTC≈1000), 오일유동 G=mdot·cp로 OIL 복귀.
- **SPRAY**: 엔드턴 오일 스프레이(HTC≈2000) — 스택 밖 권선 돌출부 직접 냉각.
- **GAP_S/GAP_R**: 공극(공기전도 G=k·A/g), 로터↔스테이터 약결합.
- **SHF**: 샤프트 단면→베어링/오일. 로터·자석·샤프트는 메시 컨포멀(FEM 직접전도).
FreeFlow SPH 뷰(`viz/ff_oil_iso.png`)의 나선채널+엔드턴 분사가 이 회로 토폴로지의 근거.

## 계산시간 비교 (Icepak / FreeFlow / MAPDL)
서로 다른 물리·스코프라 직접비교보다는 **계산 스케일 참고용**(`viz/timing_comparison.png`).

| 방법 | 솔브시간 | 스코프 |
|---|---|---|
| **MAPDL** (단순 균일HTC, 정상상태) | **13.5 s** | 544k노드/317k tet10, 전도+표면대류 |
| **MAPDL** (JAC279 하이브리드 v2, 과도 900s) | **≈800 s** (13.3m) | 1.1M노드/737k tet10, FEM+회로 22스텝 |
| **Icepak** (Prius 고정온도, 전도+재킷) | **94 s** (1m34s) | 250A, 전도+대류 |
| **FreeFlow** (Rocky SPH, 오일채움 유동) | **18,313 s** (≈5.09h) | GPU, 28.8만 입자, 물리시간 8s(온도 미해석) |

FreeFlow가 압도적으로 큰 건 **입자기반 자유표면 유동**을 GPU로 explicit 시간적분하기
때문(FEM 정상상태 전도와 근본적으로 다른 계산량). 향후 온도장까지 풀면 더 늘어남.

## 산출물 위치
이미지·GIF·데이터는 Google Drive `Prius_thermal_viz/freeflow/` (코드는 이 Git).
`viz/`, `data/` 폴더 내용을 rclone 으로 동기화: `rclone copy freeflow gdrive:Prius_thermal_viz/freeflow`.

## 추후 (커플드)
MAPDL 솔리드 온도 → FreeFlow **온도장 활성화** 재솔브(벽면 온도 경계) → 오일 흡열.
Rocky/FreeFlow 스크립팅(v261) 필요.
