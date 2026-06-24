# pyMotorCAD_Hybrid_AClossCode_ReducedRBF_SC.ipynb — 수정 이력

> 대상 파일: `d:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\pyMotorCAD_Hybrid_AClossCode_ReducedRBF_SC.ipynb`
> (비-SC 버전: `pyMotorCAD_Hybrid_AClossCode_ReducedRBF.ipynb` 에도 일부 동일 변경 적용)

---

## 1. 노트북 셀 구조 (현재)

| 셀 인덱스 | 구분 | 내용 |
|---|---|---|
| 0 | md | [1] Imports & Setup |
| 1 | code | [1] 코드 |
| 2 | md | [2] Motor Model & Run Mode Config |
| 3 | code | [2] 코드 |
| 4 | code | Path existence check |
| 5 | code | Helper functions (SIGMA_CU 등) |
| 6 | md | [4] id-iq Plane AC Loss Surface |
| 7 | code | [4] 코드 — 대화형 3D 플롯 |
| 8 | code | (빈 셀) |
| 9 | md | [5] AF (Adjustment Factor) Modeling |
| 10 | code | [5] AF 데이터 로드 + 유효성 필터 |
| 11 | md | [5.5] RBF Model Build |
| 12 | code | [5.5] RBF 빌드 (3D TPS + Separable) |
| 13 | md | [6] Method A: 속도-전용 다항식 |
| 14 | code | [6] 코드 |
| 15 | md | [6.5 + 8] AF id-iq 분포 + Ablation Study |
| 16 | code | [6.5] AF id-iq 시각화 |
| 17 | code | [8] Ablation Study |
| 18 | md | [9] Exhaustive Calibration Search |
| 19 | code | [9] 코드 |
| 20 | md | [10] Coordinate Comparison |
| 21 | code | [10] 코드 |
| 22 | md | [6.6] 3D Surface Visualization |
| 23 | code | [6.6] 코드 |
| 24 | md | [7] Final Model Validation |
| 25 | code | [7] 코드 |

---

## 2. 주요 개념 정리

### AF (Adjustment Factor)
```
AF = FullFEA_AC / Hybrid_AC
```
Hybrid 모델의 AC 손실을 FullFEA 수준으로 보정하기 위한 배율.

### Separable RBF 구조
- `g(Irms, θ)` : 2kRPM 기준점만 사용하는 2D TPS RBF (형상 포착)
- `f(speed)` : 비기준 속도 보정점으로 피팅하는 1D 2차 다항식 (속도 스케일링)
- `AF(speed, Irms, θ) ≈ f(speed) × g(Irms, θ)`

### 데이터 포인트 수 공식
```
전체 = n_base + n_spd × len(other_speeds)
예: n_base=30, n_spd=1, 비기준속도 3개(4k/8k/16k) → 30 + 1×3 = 33점
```

### 배열 변수 의미
| 변수 | 의미 |
|---|---|
| `h_ac_arr` | Hybrid 모델 AC 손실 [kW] |
| `f_ac_arr` | FullFEA AC 손실 [kW] |
| `af_arr` | AF = f_ac / h_ac |
| `irms_arr` | Irms [A] |
| `phase_arr` | 위상각 [deg] |
| `speeds_k` | 속도 [kRPM] |
| `base_idx` | 2kRPM 인덱스 (g() 학습용) |
| `selected_other_idx` | 비기준속도 보정점 인덱스 |

---

## 3. 수정 이력

### [이전 세션]

#### (A) PNG 저장 경로 수정
- **셀**: 14, 16, 18
- `"map_exports/AF_*.png"` → `out_dir / "AF_*.png"` (json_summary_path와 동일 폴더)

#### (B) AF 유효성 필터 추가 (cell 10)
무부하/저전류에서 AF가 불안정해지는 문제 방지:
```python
IRMS_MIN = 50.0
AF_MIN, AF_MAX = 0.3, 3.0
if curr < IRMS_MIN: continue
if not (AF_MIN <= af <= AF_MAX): continue
```

#### (C) f_val 클립 + 진단 출력 추가 (cell 12)
```python
f_val = af_actual / (g_val + 1e-12)
if not (0.3 <= f_val <= 3.0): continue   # 이상치 제거
```
속도별 f 값 분포 진단 출력 (n, mean, range).

#### (D) 셀 순서 재배치
- 분석 셀 [8], [9], [10]을 [7] 앞으로 이동
- [6.5] md + [8] md 병합 → 셀 15

#### (E) 영문화
- 모든 figure suptitle, xlabel, ylabel, legend를 한글→영문

#### (F) n_base / n_spd 표시 추가
- [7] (cell 25), [10] (cell 21): 헤더 출력, suptitle, scatter label에 n_base/n_spd 명기

#### (G) CUSTOM_N_BASE / CUSTOM_N_SPD 파라미터 블록
- [7]과 [10] 상단에 아래 블록 추가:
```python
CUSTOM_N_BASE = None   # e.g. 20
CUSTOM_N_SPD  = None   # e.g. 2
CUSTOM_SEED   = 42
```
`None`이면 [5.5]의 기본 모델 사용, 값 지정 시 해당 설정으로 재빌드.

#### (H) [9] 전수탐색 셀 추가 (cell 19)
- 30³ = 27,000 조합 전수탐색
- MAE 히스토그램 + 속도별 marginal 히트맵

#### (I) [10] 좌표계 비교 셀 추가 (cell 21)
- `(Irms, phase)` vs `(Id, Iq)` 기준 Separable RBF 성능 비교

---

### [현재 세션]

#### (J) 16kRPM FEA 미완료 진단 (cell 10)
누락 포인트 확인용 진단 코드 추가:
```python
[누락 포인트 진단]
  16000RPM  FEA 미완료 1건: [(460.1, 90.0)]
```
- 실제 누락 포인트: **Irms=460.1A, phase=90.0°** at 16kRPM
- 이유: 최대 field-weakening (Iq≈0, 토크≈0) 영역으로 FEA 미완료

#### (K) Phase ≥ 85° 보정점 제외 (cell 12)
FEA 미완료 점의 대체 선택으로 이상 보정점이 잡히는 문제 수정:
```python
# target_currents 선택 시 phase < 85° 제한
_phase_mask = phase_arr[spd_idx] < 85.0
_valid_idx  = spd_idx[_phase_mask] if _phase_mask.any() else spd_idx
diffs = (irms_arr[_valid_idx] - i_val)**2
best_idx = _valid_idx[np.argmin(diffs)]
```
- 근거: phase=90°는 Iq≈0 (무부하)로 AF 정의 자체가 불안정

#### (L) Interactive matplotlib backend 자동 설정 (cell 7)
Map.ipynb와 동일한 backend 자동 감지 블록 추가:
```python
PLOT_BACKEND = 'auto'  # 'auto' | 'inline' | 'widget' | 'notebook'
# VS Code 환경 → widget, 브라우저 → inline 자동 선택
```
- 효과: click + Spacebar 대화형 3D 플롯 동작 복구

#### (M) `ea` 미정의 에러 수정 (cell 17)
`ea`는 cell 25에서 정의되어 cell 17에서 참조 불가:
```python
# 수정 전
hybrid_baseline = float(np.abs(ea).mean())

# 수정 후
hybrid_baseline = float(np.abs((h_ac_arr - f_ac_arr) / (f_ac_arr + 1e-12) * 100).mean())
```

#### (N) `h_ac_arr` / `f_ac_arr` 정의 누락 (cell 12)
cell 17, 21, 25에서 필요하나 cell 12에 없던 배열 추가:
```python
h_ac_arr  = np.array([p["hybrid_ac_kW"] for p in af_points])
f_ac_arr  = np.array([p["fea_ac_kW"]    for p in af_points])
```

#### (O) `_n_base` / `_n_spd` else 분기 누락 수정 (cell 21, 25)
`CUSTOM_N_BASE = None` 기본값일 때 변수 미정의 에러:
```python
# 수정 전
else:
    print(f'... n_base={_n_base} ...')   # NameError!

# 수정 후
else:
    _n_base = len(base_idx)
    _n_spd  = len(selected_other_idx) // len(other_speeds)
    print(f'... n_base={_n_base} ...')
```

---

## 4. 권장 실행 순서

```
cell 1  → [1] imports
cell 3  → [2] motor config
cell 4  → path check
cell 5  → helpers
cell 7  → [4] 대화형 AC loss 플롯  (interactive)
cell 10 → [5] AF 데이터 로드 (누락 포인트 진단 포함)
cell 12 → [5.5] RBF 빌드  ← h_ac_arr / f_ac_arr 여기서 정의
cell 14 → [6] Method A
cell 16 → [6.5] AF 분포 시각화
cell 17 → [8] Ablation study
cell 19 → [9] 전수탐색 (시간 소요: ~수십 초)
cell 21 → [10] 좌표계 비교
cell 23 → [6.6] 3D surface
cell 25 → [7] 최종 모델 비교 검증
```

---

## 5. 주요 파라미터 위치

| 파라미터 | 셀 | 설명 |
|---|---|---|
| `MODEL_SCALE` | cell 3 | SC / non-SC 스케일 선택 |
| `IRMS_MIN`, `AF_MIN/MAX` | cell 10 | AF 유효성 필터 임계값 |
| `target_currents` | cell 12 | f(speed) 보정점 목표 전류 |
| `CUSTOM_N_BASE/N_SPD` | cell 21, 25 | 사용자 지정 n_base / n_spd/spd |
| `PLOT_BACKEND` | cell 7 | matplotlib 백엔드 (`auto`/`inline`/`widget`) |
