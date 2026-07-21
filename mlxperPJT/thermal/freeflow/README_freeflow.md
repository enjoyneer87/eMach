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
| 03 | `03_stl_to_cdb.py` | watertight STL → gmsh 체적메시 → SOLID87 CDB (로터는 실린더) | gmsh |
| 04 | `04_mapdl_thermal.py` | CDB + 손실(HGEN) + 오일 대류(외곽 NSEL,EXT) → 정상상태 온도 | pymapdl |
| 05 | `05_geometry_viz.py` | STL 형상 부품별 렌더(iso/cutaway) | pyvista |
| 06 | `06_oil_static_viz.py` | 오일 SPH 입자(속도) + 형상 오버레이 | pyvista+h5py |
| 07 | `07_oil_transient_gif.py` | 오일 나선유동 transient GIF | pyvista+h5py+imageio |
| 08 | `08_mapdl_result_viz.py` | MAPDL 결과 시각화 — **`thermal_viz.ThermalViz` 재사용**(코드 재사용 원칙) | thermal_viz |
| 09 | `09_timing_comparison.py` | Icepak/FreeFlow/MAPDL 계산시간 비교차트 | matplotlib |

## MAPDL 열해석 결과 (250A급 460A RMS 운전점, 오일 70°C)
| 부품 | max °C | min °C |
|---|---|---|
| **Winding(권선)** | **95.6** | 54.5 |
| Stator | 74.8 | 70.1 |
| Rotor | 72.1 | 70.2 |

솔브 13.5초(544,400절점/316,733 SOLID87 tet10). 권선 손실(3350W, 작은 체적)이 지배적이라
엔드턴부(스택 밖 돌출부)가 최고온 — `cut_3d.png`/`coil_only.png`에서 확인됨.
스테이터·로터는 손실이 작아 오일온도(70°C)에 근접.

### 메시 파이프라인 트러블슈팅 (재현 노트, 중요)
gmsh STL→tet10 메시에서 "Zero volume in element" 로 MAPDL 솔브가 반복 실패했음.
**근본 원인**: 부품 결합 시 좌표 반올림(1e-6m) 노드 병합이 **개별 부품 단위 퇴화검사 이후**
일어나, 서로 다른 두 코너가 병합으로 겹쳐 요소가 퇴화되는 케이스를 못 잡음(병합 전 필터는 무의미).
**해결**(`03_stl_to_cdb.py`):
1. 3부품 tet10 생성(필터 없이) → 좌표 병합
2. **병합 후** 코너 부호체적으로 퇴화요소 제거(임계값 1e-2×중앙값) — 6634개(2%) 제거
3. 모든 중간노드를 변의 두 코너 평균으로 **직선화**(곡면 STL 추종으로 인한 2차요소 자코비안
   음수/영 문제 방지, SOLID87 IJKLMNOPQR 컨벤션 M=IJ N=JK O=KI P=IL Q=JL R=KL)
→ 이후 안정적으로 솔브(13.5s, 재현 확인). **교훈: STL 기반 tet10 메시는 병합 후 필터링 +
중간노드 직선화를 표준으로 할 것.**

⚠️ 로터는 STL 자체가 자석포켓 자기교차(non-manifold)로 체적메시 불가 → **단순 실린더**로 대체
(OD 71.4mm, 활성구간). 로터 철손+자석손을 이 실린더에 뭉쳐 주입(물리적으로는 근사).

## 손실 처리 (data/e10_losses.json)
- **운전점은 e10 .mot에서 실측**(16000rpm/460A). 
- **손실값은 Prius 250A 추정 분포**(구리3350/고정자철585/로터철65/자석24 W): e10 활성체적
  이 Prius의 ~0.97배로 유사. **사유**: Motor-CAD `do_magnetic_calculation`/`do_magnetic_
  thermal_calculation` 이 injected-loss 출력을 0 반환(자기↔열 연동/계산옵션 미설정, 헤드리스).
  파라미터명은 ActiveX 참조로 정확(에러 아닌 0). **실측 손실은 GUI 솔브 후 재추출로 대체 가능.**
- Motor-CAD 손실 정확 파라미터명: 구리 `Armature_Winding_Loss_Total`, 고정자철손
  `Loss_[Stator_Back_Iron]`+`Loss_[Stator_Tooth]`, 회전자철손 `Loss_[Rotor_Back_Iron]`+
  `Loss_[Rotor_Tooth]`, 자석 `Loss_[Magnet]`.

## 냉각 모델
오일(ATF) 대류: 어셈블리 외곽면(`NSEL,,EXT`)에 HTC≈2000 W/m²K, 오일온도 70°C.
FreeFlow는 오일이 나선채널+엔드턴 분사+캐비티 충전으로 외면을 냉각.

## 계산시간 비교 (Icepak / FreeFlow / MAPDL)
서로 다른 물리·스코프라 직접비교보다는 **계산 스케일 참고용**(`viz/timing_comparison.png`).

| 방법 | 솔브시간 | 스코프 |
|---|---|---|
| **MAPDL** (e10 오일냉각, 정상상태 전도) | **13.5 s** | 544k노드/317k tet10, 전도+표면대류 |
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
