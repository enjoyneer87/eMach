# Prius 모터 열해석 (실제 Toyota Prius geometry)

IcepakFEA 워크샵 모터와 **다른 실제 Prius**(OD 269mm/스택 83.8mm/8극48슬롯 V-IPM).
손실은 Prius 2D Maxwell, 형상은 SpaceClaim `PriusMotor_3D45degree`. JAC279식
MAPDL 하이브리드 파이프라인(정션결합/CEND회로/직교이방성 코일) 재사용.

## 소스
- 손실: `Prius_Model_24R2.aedt` (Maxwell 2D Transient, full 360, depth 83.8mm,
  250A/3000rpm/gamma60). 19R2 원본을 24R2로 저장해 v261 마이그레이션.
- 형상: `PriusMotor_3D45degree.stp` (Fluent EM-Thermal 훈련, 45° 섹터)

## 파이프라인
1. `prius_step2cdb.py`: STEP → active part 자동분류(바운딩박스: 스테이터/로터/
   자석/코일슬롯 6개/샤프트, 코일엔드·하우징 제외) → gmsh 컨포멀 → 45°×8 회전
   → `prius_motor_mesh.cdb` (402,229노드 / 263,384 SOLID87). z미러 없음(full axial).
2. 손실(prius_losses.json): 슬롯동손 2311.7W(2D 직접) + 엔드동손 1038.7W
   (슬롯×V_end/V_slot=0.449) + 자석 23.8W + 철손 스585/로65W(90/10 추정)
3. `prius_thermal.py`: CDREAD → 직교이방성 코일(KZZ250/KXX2.5) → 슬롯 정션(2×TCC)
   → CEND 회로 → 냉각(WJ/ATF/하우징/공극) → 과도 900s

## 결과 (t=900s, 250A 고부하)
| 부품 | max °C | 비고 |
|------|--------|------|
| 코일 | 185.6 | H급 절연 180°C 초과 |
| 스테이터 코어 | 181.8 | |
| 로터 코어 | 166.0 | |
| 자석 | 161.6 | NdFeB 감자 주의 |
| 샤프트 | 133.0 | |

## 유의
- 냉각은 JAC279식 회로(WJ 상90°/ATF 하90°/하우징) 적용 — Prius 실제 냉각과
  다를 수 있음(HTC 조정 가능)
- 철손 스테이터/로터 분리는 추정(90/10). 정밀화: Maxwell OutputPerObjectCoreLoss
- 250A/3000rpm은 이 2D 모델 운전점. 열정상상태(900s) 값
