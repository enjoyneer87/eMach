# Fig 8(transfer ablation) 추적 문서 — Motor-CAD 원시데이터 → 폭주 셀

_작성 2026-07-20 · 대상: 논문 Fig 8 `fig:transfer_ablation`, 그리고 그 하부 데이터 전체_

**왜 이 문서인가**: Fig 8의 SC 패널에서 `n_spd8=2` 열만 계통적으로 튄다(78%, >10³).
"점을 더 줬는데 더 나빠지는" 역전이라 원인 규명이 필요했고, 아래에서 원시데이터부터
그 셀까지 단계별로 추적한다. **결론은 Stage 4의 회귀 조건수 문제이며 데이터 결함이 아니다.**

---

## Stage 0 — Motor-CAD 원시 모델

| 항목 | 경로 |
|---|---|
| Ref (기준) | `D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot` |
| 턴수 변형 | 같은 폴더의 `e10Turn4V261.mot`, `e10Turn8V261.mot` |
| SC (k_r=2) | `D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot` |

- `.mot`은 **평문 INI**라 형상·설정값은 텍스트로 직접 읽힌다
  (`Copper_Width` Turn4=3.73 / Turn6=3.711, `Slot_Depth`=13.83 동일).
- 단 **R_DC·T_em·손실은 저장값이 아니라 계산 출력**이므로 Motor-CAD 실행이 필요하다.
- ⚠️ 논문 Table(Compareloading)의 값이 **Turn4 시절 기준일 가능성** — 별도 확인 과제.

FEA 실행 결과는 운전점별 backup 디렉터리로 떨어지고, 그 경로가 아래 JSON의
`backup_dir` 필드에 남아 **모델 판별 근거**로 쓰인다(`AcLossJsonReader`, E-IO-003).

---

## Stage 1 — 요약 JSON (원시 → 표 형태)

| 모델 | 파일 | 레코드 | 운전점 | 비고 |
|---|---|---|---|---|
| Ref | `map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary.json` | 240 | 120 | 4속도 × 5전류 × 6위상 |
| HalfSC | `map_exports/e10/HalfSC/JEET_ACLoss_HalfSC_Map_Summary.json` | 372 | 186 | **8전류**(690A 포함, 07-18 보강) |
| SC | `map_exports/e10/SC/JEET_ACLoss_SC_Map_Summary.json` | 240 | 120 | 4속도 × 5전류 × 6위상 |

- 레코드는 운전점당 **2건**(`mode`= `Hybrid` / `FullFEA`)이다. AF는 이 둘의 비.
- 속도 [2, 4, 8, 16] kRPM · 위상 [0, 18, 36, 54, 72, 90]°
- 전류: Ref [0,115,230,345,460] / SC [0,230,460,690,920] /
  **HalfSC [0,115,172,230,345,460,517.5,690]**
- HalfSC 백업 파일명 `*_690pre.json`이 690A 보강 이전 상태를 보존한다.

> ⚠️ **HalfSC 수치 스테일**: 위 보강으로 AF 산출점이 82 → **149점**이 되었으나
> 논문은 아직 82로 기술한다. Ref(74)·SC(89)는 파이프라인 실측과 일치.

---

## Stage 2 — AF 매칭과 필터

`AcLossPipeline.load_dataset(scale)` 이 Hybrid ↔ FullFEA를 운전점 기준으로 짝지어
`AF = P_TS / P_HYB` 를 만든다. 이때 제거되는 점:

| 사유 | 예시 | 성격 |
|---|---|---|
| 무부하 | `I=0.1A` × 6위상 × 4속도 = 24점 | AF 미정의 (정상) |
| 저전류·저위상각 | (230A, 0°), (345A, 0/18°) 등 | 손실이 작아 비가 불안정 (정상) |

실측 결과 **Ref 120→74 · SC 120→89 · HalfSC 186→149**.
격자 자체의 결손은 거의 없다(HalfSC만 192칸 중 186칸 = 97%).
즉 리뷰어가 지적한 "데이터 ~20% 누락"은 **세미나 당시 HalfSC의 460A 상한**을 가리킨
것이며, 현재는 690A까지 채워져 해소된 상태다.

---

## Stage 3 — 기준 커널 κ 적합 (16 kRPM)

`RbfModelBuilder.build_separable_rbf_transfer` (RbfModelBuilder.py ~355행):

1. 16 kRPM 풀(SC 기준 24점)에서 `n_base`개를 무작위 추출
2. 그 점들로 **TPS(박판 스플라인) 보간면 `g_local` = κ(I, β)** 를 푼다
   (`Phi_g` 조립 → `np.linalg.solve(Phi_g + λI, yb)`)
3. 이 속도에서 f=1, p=1로 앵커링

→ Fig 8의 **세로축 `n_base`** 가 이 단계의 표본 수다.

---

## Stage 4 — 속도별 (f, p) 로그회귀 ★ 폭주 지점 ★

같은 함수의 뒷부분에서 다른 속도마다 표본을 모은다:

- **상사 전달 가능**(`spd·k_r² ≤ 16 kRPM`)이면 Ref 도너 모델에서 AF를 사상 → TS-FEA 비용 0
  - SC: 2k(→8k), 4k(→16k) 는 전달 가능
  - **SC의 8 kRPM은 8×2²=32 > 16 이라 전달 불가 → 자체 TS-FEA 표본이 필수**
    ← Fig 8의 **가로축 `n_spd8`** 이 바로 이것
- 표본마다 `g_val = κ(I,β)`, `f_val = AF/g` 를 구하고 **`0.3 ≤ f_val ≤ 3.0` 만 채택**

이어 `_fit_speed_scaling` (RbfModelBuilder.py 112–159행):

```python
if exponent and len(pairs) >= 2 and float(np.ptp(lg)) > 1e-3:
    p_s, logf_s = np.polyfit(lg, la, 1)     # log AF = log f + p·log κ
else:
    p_s, f_s = 1.0, float(np.mean(ratios))  # 스칼라 폴백 (p=1)
```

마지막에 속도별 p를 모아 **`np.polyfit(s_arr, p_exps, 2)` 로 p(ω) 2차 적합**을 한다.
→ **한 속도의 p가 튀면 그 왜곡이 전 속도로 전파된다.**

### 실데이터 재현 (SC, n_base=16, 300 시드)

스크립트: `scratchpad/trace_p.py`

| n_spd8 | p 중앙 | p 5% | p 95% | **\|p\|>5 비율** | log κ 간격 중앙 |
|---|---|---|---|---|---|
| **1** | 1.00 | 1.00 | 1.00 | **0.0 %** | — (폴백) |
| **2** | 1.59 | **0.07** | **3.35** | **3.7 %** | 0.218 |
| **3** | 1.62 | 0.47 | 2.35 | 0.7 % | 0.379 |
| **4** | 1.61 | 0.60 | 2.25 | **0.0 %** | 0.419 |

**해석**

- `n_spd8=1` → `len(pairs)>=2` 가 거짓이라 **스칼라로 자동 축퇴**. p는 항상 정확히 1.
  퇴화이긴 하나 **수치적으로는 완전히 안전**하다.
- `n_spd8=2` → 기울기가 **잉여 없이 정확 결정**된다. 두 표본의 log κ 간격(지렛대)이
  중앙 0.218에 불과해, 간격이 좁게 뽑힌 시드에서 기울기 오차가 크게 증폭된다.
  **300 시드 중 3.7 %가 |p|>5로 발산.**
- `n_spd8≥3` → 최소제곱이 과잉결정되며 간격도 0.38~0.42로 넓어져 발산이 사라진다.
- 중앙값은 2점부터 이미 ≈1.6으로 옳다. 즉 **편향이 아니라 분산 문제**이며,
  그래서 열 전체가 균일하게 나쁜 게 아니라 **특정 셀만 튄다**.

### Fig 8 셀과의 연결

Fig 8은 **10-시드 평균 wMAE**다. 발산 확률 3.7 %면 10개 중 1개가 터질 확률이 약 31 %.
한 시드가 |p|>5로 터지면 그 시드의 wMAE가 수백 %가 되어 평균을 끌어올린다.
→ SC `n_base=16, n_spd8=2` 셀의 **78 %**, `n_base=8` 행의 **>10³** 이 그 결과다.
가드 `np.ptp(lg) > 1e-3` 는 *거의 동일한* 경우만 걸러 너무 느슨하다.

---

## Stage 5 — 절제 그리드 → Fig 8

`AcLossPipeline.transfer_ablation_grid(scale, ...)` 가 (n_base × n_spd8) 격자를
10-시드로 돌려 wMAE를 채우고, `fig/transfer_ablation.png` 로 그린다.
채택 셀은 `n_spd8=3` (HalfSC 24+3, SC 24+3).

---

## 결론 및 조치 후보

1. **데이터 결함 없음.** 격자는 완전하고 폭주는 Stage 4의 조건수 문제다.
2. **본문 서술이 부정확**: 현재 "1–2점은 회귀 퇴화·불안정"으로 묶여 있으나,
   실제로는 **1점은 폴백이라 안전, 2점이 위험**하다. → 정밀화 권장.
3. **선택적 코드 개선**: 가드를 `ptp(lg)` 절대값이 아니라
   조건수/지렛대 기준(예: `ptp(lg) > 0.3`)으로 바꾸면 2점 셀의 발산이 완화된다.
   단 채택값은 3점이므로 논문 결과에는 영향이 없다.
4. **별건**: HalfSC 82→149 스테일, Table(Compareloading) 4턴 의심.

## 재현 스크립트

| 목적 | 위치 |
|---|---|
| 데이터셋 점수·격자 완결성 | `scratchpad/fig8_data2.py`, `fig8_af.py` |
| 파이프라인 기준 점수 대조 | `scratchpad/pipe_counts.py` |
| **p 폭주 재현** | `scratchpad/trace_p.py` |
