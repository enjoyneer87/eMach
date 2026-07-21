# Prius Icepak (전도+워터재킷) 열해석 — 상태: 발산 진단완료, 고정온도로 수렴

Prius 형상(IcepakFEA STEP, 45° 섹터, 20볼륨)을 Icepak 으로 임포트해 전도+재킷대류
열해석. pyaedt `Icepak`, v261.

## 파이프라인 (번호순)
| # | 스크립트 | 역할 |
|---|---|---|
| 00 | `00_geometry_inventory.py` | STEP 20볼륨 bbox 인벤토리(재료매핑용) |
| 01 | `01_import_classify_materials.py` | STEP 임포트 + bbox 자동분류 + 재료 |
| 02 | `02_materials_sources.py` | 이방성코일 재료 + 손실 14블록(assign_solid_block) |
| 03 | `03_jacket_wall.py` | 프레임 OD 곡면 워터재킷 대류벽(HTC) |
| 03b| `03b_contact_diagnostic.py` | solve_inside/부품간 접촉(touching_objects) 진단 |
| 04 | `04_tight_region_htc.py` | 타이트 Region + 프레임OD HTC벽 |
| 05 | `05_fixedT_solve_extract.py` | 프레임OD **고정온도(Dirichlet)** 솔브+추출 |
| 06 | `06_extract_temps.py` | FieldSummary 부품별 온도 추출 |
| 07 | `07_threeway_compare.py` | Fluent/MAPDL/Icepak 3-way 비교차트 |

## 핵심 진단 (발산 원인)
- HTC 대류벽을 프레임 OD(유체 Region 접함)에 걸면 **Region 공기가 벽을 단락** →
  열이 대류벽 대신 단열 Region에 갇혀 **전 부품 5000K(=Icepak 발산 상한)** 발산.
  자동 Region 패딩 300%가 악화. 부품 접촉(coil→stator→frame)은 정상 확인.
- **고정온도(Dirichlet) 경계**로 바꾸면 수렴: coil 176 / stator 160 / rotor 159 /
  magnet 80 / frame 48.8°C (250A, 프레임OD 40°C 고정). endwdg/insulation 과열(격리).
- 물리적 HTC 워터재킷으로 마무리하려면 **실제 유동 CHT(유체 재킷+inlet/outlet)** 또는
  Region 아키텍처 조정 필요(대화형 튜닝 권장).

⚠️ 산출물(png/json)은 Google Drive. 재사용은 상위 `thermal_viz.py` 규약 따름.
