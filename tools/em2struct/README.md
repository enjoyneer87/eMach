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

# 3) 파이프라인: 2D→3D → LSQ → 진단
pipe = (EMStructMapper()
        .load_source(src)
        .set_target(tgt)
        .extrude(z_stations=np.linspace(0, 0.150, 20), skew_rate=0.0)  # 사구시 rad/m
        .map("lsq", k=6)
        .report())

# 4) export — export() 는 self 가 아니라 **생성된 파일 경로**를 반환하므로 체이닝하지 말 것
pipe.export("emforce.inp",        solver="ansys_mechanical")   # + mode="external"
pipe.export("emforce.k",          solver="lsdyna")
pipe.export("emforce_motion.csv", solver="ansys_motion")
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
#   스테이터: forceR/T(극좌표)→치각도로 x,y. 로터(part="rotor"): forceX/Y(직교) 그대로.
#   실 e10 검증됨(48치/8극, nT스텝, 성분규약 자동감지).

# ④ VWP(가상일법) 체적력 — 철심·자석 내부 분포력(MST 표면트랙션과 상보)
read_vwp_force("vwp_force.csv", density=True, stack_length=0.150)  # N/m³ × 체적 → 절점력
```

리더는 **열이름 매핑(`col_map`)** 이나 in-memory 배열을 받으므로 export 헤더가
달라도 코드 수정 없이 대응된다. 모두 SI(m, N, Pa)로 정규화.

## 솔버 라이터 3종

- **ANSYS Mechanical** — `mode="apdl"`: `F` 커맨드 시간이력(`antype,trans` +
  스텝루프) 또는 단일스텝. `mode="external"`: External Data용 long-format CSV.
- **LS-DYNA** — 절점·성분별 `*DEFINE_CURVE`(시간 vs 힘) + `*LOAD_NODE_POINT`.
- **Ansys Motion** — 플렉시블 바디 절점하중 CSV(NodeID,Time,Fx,Fy,Fz).
- **LS-DYNA `*LOAD_SEGMENT`** — `write_lsdyna_segment`: 세그먼트 법선압력 F·n/A.
- **ANSYS 원격힘(Remote Force)** — `write_ansys_remote_force`: 소스 힘점(극/치)마다
  pilot 절점 + **RBE3**(또는 CERIG) 로 표면섹터에 결합, 합력을 분산 전달. 비컨포멀
  절점맞춤 불필요, 파일 극소(8 pilot vs 수만 절점력). 로터 8극에 적합.

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

## 문헌 근거 및 검증 기준 (2026-08-11 조사)

세 학위논문 + 핵심 논문 원문을 확인해 본 패키지의 설계를 대조했다.

| 출처 | 요지 |
|---|---|
| **Pile (2021, Univ. Lille/EOMYS)** — *magnetic force projection and model reduction* | 투영은 **L² Galerkin**을 권장(총력 보존에 적합). 투영 정확도 기준으로 **토크는 부적합**(Annex C.4) — **불평형 합력**과 **치별 힘**으로 판정할 것. **VWP 절점력은 Dirac 진폭이라 보간 불가** → 밀도로 변환 후 투영. 치 lumping은 **합력만이면 10·f_s 에서 ~4 dB 손실, 토서(힘+모멘트)로 <1 dB 회복**(§3.4.2/§3.5). 반경 오차 4% vs **접선 오차 15%**(접선이 치 끝 모서리에 집중) |
| **Kotter (2019, ETH Zurich)** — *Vibroacoustics of Electrical Drive Systems* | supermesh 기반 L² 투영, 총력 보존은 타깃 기저의 **분할단위(partition of unity)**에서 따라나옴. 상용 맵퍼의 "보존형 or 형상보존형 택일" 구도를 비판(둘 다 가능). **접선력 배제 금지** — ~2 kHz 이하는 접선(비틀림)이 지배 |
| **Chauvicourt (2018, KU Leuven/Siemens)** — *Vibro-acoustics of rotating electric machines* | 에어갭 MST + **치별 합력 lumping**(8슬롯 SRM → 32절점에 인가), 축방향 균일 분배. 상용 "보존형 맵핑"은 블랙박스. 원주 8점 lumping 탓에 **홀수 공간차수가 소거**되어 A(3,0) 모드가 거의 여기되지 않음(이산화 아티팩트) |
| **Pile·Devillers·Le Besnerais (IEEE TMag 2018)** | 방법 간 **국소 분포는 불일치, 치별 적분력은 유사**. 국소 자기압력이 필요하면 **VWP 강력 권장**. MST를 **치 끝**에서 적분하면 반경 lumped force를 **33~64% 과소평가** — 적분 위치가 결정적 |

**이 패키지가 이미 만족하는 것**
- **불평형 합력 보존** — Pile이 보고한 실패모드(투영 후 잔차 2e−5 → 8e−2 N이 허위 (3,0) 모드 여기)에 대해, `lsq` 맵퍼는 잔차를 **기계정밀(~1e−11 N)** 로 유지. `report()` 가 이 절대 잔차를 명시 출력한다.
- **토크에 의존하지 않는 판정** — 보존 진단이 합력을 우선 표시(토크는 관대해 기준으로 부적합).
- **2D→3D 축방향 균일 분배** — Pile·Chauvicourt 모두 동일 접근(단, 축 비대칭 모드는 원리상 여기 불가).

**문헌 반영으로 추가한 것**
- `lump_torsor(field, centers)` — 분포 힘장에서 치별 **(F, M) 토서** 산출 → `write_ansys_remote_force(..., moments=M)`. Pile의 4 dB 손실 회복 경로.
- `coverage_report()` — 하중이 소수 절점에 집중되는지 진단(보존만으론 절대 안 드러남).
- 불평형 합력 **절대 잔차[N]** 를 보존 진단에 명시.

**문헌 반영 구현(2026-08-11 완료)**
- **`l2` 맵퍼(`L2ProjectionMapper`)** — Pile/Kotter 권장 **L² Galerkin 일관하중**:
  타깃 표면요소(tri/quad, 곡면 야코비안) Gauss 구적으로 F_i=∫φ_i·t dΓ 조립.
  분할단위 ⇒ ΣF 기계정밀 보존(검증). Gauss 밀도는 `n_gauss` 로(늘려도 선형계
  불변 — Pile의 저비용 손잡이). **타깃 표면요소 연결성 필요**(`TargetMesh(segments=)`
  또는 `make_segment_target`); 절점 클라우드만 있으면 lsq/idw 사용.
- **`nodal_to_density(F, nodes, segments)`** — VWP 절점력→연속 밀도 복원
  ([M]{ρ}={F} 일관질량 역산, 라운드트립 기계정밀 검증). Pile §1.4.6.1 의
  "절점력은 Dirac 진폭이라 보간 불가" 원칙을 코드로 강제: `l2` 는 areas 없는
  NODAL_FORCE 를 거부하고 이 함수를 안내한다.

**알려진 한계(문헌 대비)**
- Kotter식 **supermesh 교차적분 미구현** — 다점 Gauss 구적(Pile의 대안 경로)으로 대체.
- **접선 성분이 오차 핫스팟**(Pile: 반경 4% vs 접선 15%). 반경 오차가 작다고 접선이 정확하다는 보장은 없다.
- 치별 lumping의 **공간차수 한계 = N_teeth/2**(e10: 48치 → 24차까지). Chauvicourt의 8점 사례처럼 소스가 성기면 홀수차가 소거된다.

## 한계 / TODO

- `read_motorcad_multiforce` 는 Motor-CAD v2026 네이티브 JSON 에 정합(실 e10 검증).
  구형/타버전 CSV 는 `read_motorcad_nvh` + `col_map` 으로 대응.
- 2-way(구조 변형 → 전자계 되먹임) 미지원(1-way 하중 전달 전용).
- 축방향: 현재 export 는 단일 축슬라이스(axialSlice=1)를 `extrude_field` 로 분배.
  Motor-CAD 다중 축슬라이스/사구 데이터가 있으면 슬라이스별 소스로 확장 가능.
