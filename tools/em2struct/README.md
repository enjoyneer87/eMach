# em2struct — 전자계 가진력 ↔ 구조해석 메시투메시 맵핑

Motor-CAD(Maxwell) 전자계 가진력을 **ANSYS Mechanical / Ansys Motion / LS-DYNA**
구조 메시로 **보존적으로** 전달하는 eMach 파이썬 패키지. 모터 **NVH(진동·소음)**
1-way 커플링용. 소스와 타깃 메시가 비컨포멀(절점 불일치)이어도 합력·모멘트를
보존하며 하중을 넘긴다.

```
전자계(Maxwell/Motor-CAD)  ──리더──▶  ForceField(공통표현)
                                          │
                                   (선택) 2D→3D 축방향 분배
                                          │
                                   메시투메시 맵퍼
                                     · nearest  (기준선)
                                     · idw      (합력 보존, 빠름)
                                     · lsq      (합력+모멘트 보존, 권장)
                                     · rbf      (부드러운 필드 보간)
                                          │
                                   MappingResult(타깃 절점력)
                                          │
                              ──라이터──▶  ANSYS Mechanical (.inp / External CSV)
                                          ▶  LS-DYNA (*LOAD_NODE_POINT + *DEFINE_CURVE)
                                          ▶  Ansys Motion (nodal force CSV)
```

## 왜 필요한가 — 물리와 두 패러다임

전자계 해석 메시(에어갭 밀집, 회전자 정렬)와 구조 해석 메시(모드/응답용)는
서로 다르다. 힘을 그냥 최근접으로 던지면 **합력·토크가 어긋나** 구조 응답이
틀어진다. 그래서 물리량 종류에 따라 두 방식을 구분한다.

| 물리량 | 종류 | 맵핑 패러다임 |
|---|---|---|
| 절점력 `NODAL_FORCE` [N] | extensive | **보존형** — 각 소스 힘을 인접 타깃 절점으로 완전 재분배(열 합=1) → 합력 보존. LSQ 는 모멘트까지. |
| 트랙션/압력 `TRACTION` [Pa] | intensive | **일관형** — 필드를 타깃 위치로 보간(행 합=1) 후 타깃 면적으로 절점력 환산. |
| 체적력 `FORCE_DENSITY` [N/m³] | intensive | 일관형 보간 후 체적/면적 적분. |

**맵핑 연산자는 기하만으로 한 번 구성**되고, 시간스텝·하모닉이 몇 개든(NVH 는
수백) `apply()` 한 번에 일괄 변환된다.

## 맵퍼 정확도 (e10 에어갭 MST → 스테이터 보어, 검증됨)

| 맵퍼 | 합력 상대오차 | 모멘트 상대오차 | 비고 |
|---|---|---|---|
| `lsq`   | 3e-16 | **7e-16** | 합력+모멘트 동시 정확 보존. **NVH 권장.** |
| `idw`   | 2e-16 | 7.5e-5 | 합력 정확, 국소 분배라 모멘트 근사. 대형 메시에 빠름. |
| `nearest` | 5e-16 | 9.6e-4 | 기준선. |
| `rbf`   | 2e-6 | 2.5e-2 | 부드러운 필드 보간(일관형). 압력장 시각화·평활화용. |

> 상대오차 분모는 **총 힘 처리량 Σ‖fᵢ‖** — 회전 반경압력파처럼 알짜 합력이 ≈0
> 이어도 의미 있는 지표가 나오도록.

## LSQ 알고리즘 (핵심)

각 소스 점힘 **F**(위치 xₛ)를 인접 k개 타깃 절점 {xᵢ}에 실을 절점력 {fᵢ}로,
‖f‖ 최소화 + 제약 하에 분배:

```
Σ fᵢ = F                    (합력)
Σ (xᵢ − xₛ) × fᵢ = 0        (모멘트: 등가 합력이 xₛ 에 작용)
```

최소norm 해 `f = Cᵀ(CCᵀ)⁺ d`, `d=[F;0]`. 성분이 모멘트로 결합되므로 (3M×3N)
희소 연산자로 조립 → 전 시간스텝에 재사용.

## 설치 / 임포트

의존성: `numpy`, `scipy`, `matplotlib`(viz). eMach `PyMotorEnv_310` 에 포함.

```python
import sys; sys.path.insert(0, "tools")   # 레포 루트에서
import em2struct
```

## 사용 예 — 체이닝 API

```python
import numpy as np
from em2struct import read_airgap_mst, TargetMesh, EMStructMapper

# 1) 소스: 에어갭 Maxwell 응력 σ_r,σ_t (θ, t)
src = read_airgap_mst(theta, sigma_r, sigma_t,
                      radius=0.0712, stack_length=0.150, times=t)

# 2) 타깃: 구조 메시 절점(솔버에서 export)
tgt = TargetMesh(nodes=struct_nodes, node_ids=struct_ids)

# 3) 파이프라인: 2D→3D → LSQ → 진단 → export
(EMStructMapper()
    .load_source(src)
    .set_target(tgt)
    .extrude(z_stations=np.linspace(0, 0.150, 20), skew_rate=0.0)  # 사구시 rad/m
    .map("lsq", k=6)
    .report()
    .export("emforce.inp",        solver="ansys_mechanical")   # + mode="external"
    .export("emforce.k",          solver="lsdyna")
    .export("emforce_motion.csv", solver="ansys_motion"))
```

원샷 함수형: `map_forces(src, tgt, mapper="lsq", z_stations=...)`.

## 소스 리더 3종

```python
# ① Maxwell/FE 절점·요소 힘 벡터 (2D/3D)
read_maxwell_nodal("forces.csv", col_map={"x":"X [mm]","Fx":"Force_x", ...},
                   scale_len=1e-3)   # mm→m

# ② 에어갭 Maxwell 응력텐서 (NVH 표준)
read_airgap_mst(theta, sigma_r, sigma_t, radius=..., stack_length=..., times=...)

# ③ Motor-CAD NVH 치(teeth) 힘 — 일반 CSV
read_motorcad_nvh("nvh_teeth.csv", representation="polar")  # Fr,Ft → x,y

# ③b Motor-CAD 네이티브 멀티포스 JSON (export_multi_force_data 출력, 권장)
read_motorcad_multiforce("e10_multiforce.json", load_point=0, part="stator")
#   → 48치 × nT스텝, forceRValues/forceTValues 를 치 각도로 x,y 변환. 실 e10 검증됨.
```

리더는 **열이름 매핑(`col_map`)** 이나 in-memory 배열을 받으므로 export 헤더가
달라도 코드 수정 없이 대응된다. 모두 SI(m, N, Pa)로 정규화.

## 솔버 라이터 3종

- **ANSYS Mechanical** — `mode="apdl"`: `F` 커맨드 시간이력(`antype,trans` +
  스텝루프) 또는 단일스텝. `mode="external"`: External Data용 long-format CSV.
- **LS-DYNA** — 절점·성분별 `*DEFINE_CURVE`(시간 vs 힘) + `*LOAD_NODE_POINT`.
- **Ansys Motion** — 플렉시블 바디 절점하중 CSV(NodeID,Time,Fx,Fy,Fz).

`tol` 로 미소 힘 절점 생략(파일 축소), `col` 로 특정 스텝만 export.

## 2D → 3D 축방향 분배 (`extrude_field`)

2D Maxwell 단면 힘을 스택 길이에 걸쳐 z 방향 스테이션들로 분배. `per_unit_length`,
트리뷰터리 길이 가중, 엔드이펙트 커스텀 가중, **사구(skew_rate [rad/m])** 지원.
총력 보존.

## 검증 / 예제

```bash
python tools/em2struct/tests/test_em2struct.py                    # 9/9 통과
python tools/em2struct/examples/example_airgap_to_structural.py   # e10 데모 + QA png
```

테스트가 검증하는 것: IDW/nearest 합력 보존, LSQ 합력+모멘트 보존, LSQ<IDW 모멘트
오차, 에어갭 리더 해석해 일치, 축방향 총력 보존, 3종 라이터 파일 생성.

## 구성 파일

| 파일 | 역할 |
|---|---|
| `core.py` | `ForceField`·`TargetMesh`·`MappingResult`, 보존 진단 |
| `readers.py` | Maxwell nodal / air-gap MST / Motor-CAD NVH |
| `mappers.py` | Nearest / InverseDistance / **LeastSquares** / RBF |
| `writers.py` | ANSYS Mechanical / LS-DYNA / Ansys Motion |
| `axial.py` | 2D→3D 축방향 분배(사구) |
| `pipeline.py` | `EMStructMapper`(체이닝), `map_forces`(원샷) |
| `viz.py` | `plot_mapping` (QA 그림) |

## 한계 / TODO

- `read_motorcad_multiforce` 는 Motor-CAD v2026 네이티브 JSON 에 정합(실 e10 검증).
  구형/타버전 CSV 는 `read_motorcad_nvh` + `col_map` 으로 대응.
- 2-way(구조 변형 → 전자계 되먹임) 미지원(1-way 하중 전달 전용).
- 축방향: 현재 export 는 단일 축슬라이스(axialSlice=1)를 `extrude_field` 로 분배.
  Motor-CAD 다중 축슬라이스/사구 데이터가 있으면 슬라이스별 소스로 확장 가능.
