# 논문 2 골격 — 강한 상사와 약한 상사: 설계축 간 보정 전달

> 작성 2026-08-27. 논문 1(JEET 재제출본)의 후속.
> 구도는 §12.12 저자 문답에서 확정: **"강한 상사(k_r·σ) vs 약한 상사(턴)"**.
> 아래 수치는 전부 기존 산출물에서 나온 실측 — 신규 시뮬레이션 0.

## 제목 후보

- Strong and weak similarity in AC winding-loss calibration transfer:
  radial scaling, rewinding, and their composition
- One reference, a design plane: transferring loss calibration across
  scale and turn count at near-zero simulation cost

## 핵심 주장 (3문장)

1. 설계축마다 상사의 강도가 다르다 — 반경 축은 손실 자체가 보존되는 강한
   상사이고(제로샷 2~6%), 턴 축은 약한 상사다(11~16%).
2. 약한 축의 전달 실패는 분해 가능하다 — 분모의 턴 구조는 슬롯 필드
   재분할로 공짜로 재구성되고, 남는 잔차는 **턴수당 곱셈 스칼라 1개(f_c)로
   압축**된다 (TS 1~3점에 4~5%, 전 대역).
3. 두 축은 합성된다 — k_r 걸음의 추가 비용 ≤1%p, f_c 는 도너 k_r 에
   1% 내 불변 = **f_c 는 k_w 만의 함수**. (k_r, k_w) 설계 평면 전체가
   기준기 하나 + 축당 스칼라로 평가된다.

## 절 구성

### 1. 서론
- DSE 에서 후보당 전수 Full-FEA 는 성립하지 않음. 논문 1이 반경 축 전달을
  세움 — 질문: 어느 설계축이 보정을 보존하는가.

### 2. 상사 분류 (이론)
- 정확 상사: k_r (ξ 보존, 손실 불변. 논문 1 + e4a 2차 패밀리 §12.21:
  제로샷 인밴드 0.43~1.65%)
- 주파수 재색인: σ 축 — AF_σα(ω,I,β) = AF(αω,I,β), 반작용 포함 정확
  (§12.12 유도). α_Al≈0.61 → 16k→9.8k 전 대역 인밴드. **미실증 — 본
  논문에서 검증 항목인지 저자 결정**
- 분할 사상: k_w(턴) — MMF 재색인 + 창 재평균. 정확하지 않음(아래 3절)

### 3. 턴 축은 왜 약한가 — 기전 3종의 실측 분해
- 도체평균 분모의 Jensen 면: 4t 1.17~1.27 / 6t 1.10~1.19 / 8t 1.09~1.16,
  전류 단조 감소 (`kturn_spectrum.json`)
- MMF 계단 비불변성: MMF 짝의 조화 진폭 편차 4t 13.6% / 8t 5.5% — §12.11
  "기하 비스케일" 가설의 첫 정량화
- 반작용 몫의 ξ 이동: AF_el 레벨 4t 0.45 / 6t 0.7 / 8t 0.9
- 무릎 소거: 프로토콜 통일 시 다섯 기계의 수렴 곡선이 같은 모양
  (`knee_6t_compare.json`) — 턴 축 페널티는 무릎 위치가 아니라 정체 구간
  높이(1.2~2배)

### 4. 인수분해 전달 (본 논문의 방법 기여)
- P_TS^Nt = AF_el^6t(k_h²ω, MMF, β) × P_el^Nt(ω,I,β)
- P_el: 슬롯 총 조화 스펙트럼(분할 무관) + prox_g2 천이 커널 + 전역 상수
  1개 (full_G2_solid 재현 잔차 2.0%)
- **f_c 압축**: 순수 0점 4t 28.9/8t 10.6% → f_c 1개로 4.77/3.98%
  (`kturn_af_reuse.json`). f_c = 0.777/1/1.117, k_h 단조
- 속도별 오차 평탄 (4t 4.4~5.8%) — §12.11 의 대역한정 단서 불필요화

### 5. 축 합성 (k_r × k_w)
- 도너 HalfSC/SC → kturn4/8: 4~6%, k_r 걸음 비용 ≤1%p
  (`kturn_kr_kw_compose.json`)
- f_c 도너 불변 (0.777/0.766/0.768) → f_c = f(k_w) 뿐
- 도너 사다리의 대역 확장: Ref 가 못 닿던 4t 34.8k 등가를 HalfSC 가 인밴드
- kW 패리티: 정격 유사점 ±2~3%, 0.04~47 kW 세 자릿수

### 6. DSE 사다리 (운영 규율)
- 고르기 0점 (순위 재현 쌍별 98.8%/전순위 96.9%)
- 평가 TS 1~3점 → 4~5% (증턴·감턴 무관, 전 대역)
- 확정 27점 → 1.7~2.6%
- 후보 10개: 전수 1200점 → ≤42점 (≥96% 절감)

### 7. 한계
- f_c 의 0점 예측 미해결 (표본 2점 — 과적합 위험으로 보류)
- 실효 두께비 클램프 (8t 총동 93.2%) = 제조 비스케일의 최소 사례
- σ 축 미실증 / 진리값은 여전히 시뮬레이션

## 그림 후보 (전부 생성 스크립트 보유)

| 후보 | 원본 |
|---|---|
| 방법 사다리 + f_c 압축 4패널 | `kturn_summary_fig.py` (scratchpad → 이관 필요) |
| 합성 3패널 (대역/wMAE/f_c 불변) | `kr_kw_fig.py` (〃) |
| kW 패리티 + 손실-속도 | `kr_kw_kW_fig.py` (〃) |
| Jensen 면 / 계단 편차 | `kturn_spectrum.json` 에서 신규 작도 |
| 무릎 5곡선 | `knee_6t_compare.json` 에서 신규 작도 |

## 데이터·스크립트 (eMach `mlxperPJT/JEET/`)

- 스윕: `G:\KangDH\JEET\kturn_results\` (240×2, 필드 188 GB)
- 분석: `run_kturn_af_analysis.py` / `run_kturn_design_strategy.py` /
  `run_kturn_spectrum_extract.py` / `run_kturn_af_reuse.py` /
  `run_kturn_knee_6t_compare.py` / `run_kturn_kr_kw_compose.py`
- 산출: `map_exports/e10/kturn/*.json` (6종)
- 노트: context_review_notes §12.11 / §12.12 / §12.29 / §12.29-A

## 저자 결정 대기

1. σ 축(재질 재색인)을 이 논문에 넣나, 이론 절만 두나 — 실증하려면 Al 권선
   TS 캠페인 (신규 시뮬레이션, 유일한 신규 비용)
2. 투고처 — JEET 연작 / IEEE TIA·TIE / COMPEL
3. 저자 구성 — 논문 1과 동일한가
4. e4a 2차 패밀리를 2절 근거로 어느 깊이까지 쓰나 (논문 1과 중복 조정)
