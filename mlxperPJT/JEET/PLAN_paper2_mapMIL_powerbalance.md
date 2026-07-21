# Paper 2 실행계획 — Power-Consistent Map-Based MIL Model with Calibrated AC-Loss Impedance

> JEET 논문 1(AC손실 스케일링·RBF 보정)의 **후속 논문**.
> 작성 2026-07-19. 상위 맥락: `functional-humming-yao.md`(논문 1), `context_review_notes.md`.

---

## 0. 논문 포지셔닝 (한 문장 thesis)

> 표준 map-based(LUT) 기계모델은 시스템레벨 MIL에서 **순시 전력수지를 두 가지 구조적 이유로 위반**한다 —
> (1) λ_d, λ_q를 독립 보간하면 **비가역(non-reciprocal) 자속맵**이 공에너지를 생성/소멸시키고,
> (2) **사이클 평균 손실맵**을 순시 sink로 주입하면 과도상태에서 에너지를 이중계상한다.
> 본 논문은 자속맵을 가역성으로 투영하고, 손실(특히 논문 1의 AF-보정 AC 동손 + 철손)을
> **주파수·전류 의존 임피던스 소자**로 삽입하여, 매 timestep에서
> `P_elec = dW_m/dt + T_e·ω + ΣP_loss` 가 닫히는 **에너지 정합 map-based 모델**을 구성하고,
> 그 효율맵·드라이브사이클 에너지를 Motor-CAD Lab·TS-FEA와 대조 검증한다.

**논문 1과의 비중복성**: 논문 1 = 정확한 AC손실 맵을 *싸게 얻는 법*(스케일링+RBF). 논문 2 = 그 맵을
*동역학적으로 정합되게 쓰는 법*. AF-보정 `R_AC(ω,i)`가 두 논문을 잇는 다리.

**차별 대상**: Simscape "FEM-Parameterized PMSM" 블록, 일반 LUT 모델 — 둘 다 가역성 미보장 +
손실은 후처리 sink. (Phase D1에서 정확히 무엇을 보장/미보장하는지 확인 후 포지셔닝.)

---

## 1. 이미 구축된 자산 (검증 완료)

| 자산 | 경로 | 역할 |
|---|---|---|
| `e10_SatuMap.mat` | `eMach/tools/SystemSimulationModel/` | λ_d, λ_q, P_Fe, R_dc LUT (Id_Peak/Iq_Peak/Flux_Linkage_D·Q/Iron_Loss/Stator_Copper_Loss_AC/Phase_Resistance_DC_at_20C) |
| `MtpaFwSolver.py` | `eMach/tools/motor_scaling/morphisms/` | **정상상태 EEC**: R_ac 직렬 + I_fe 병렬. SyRE MMM calcTnPoint 근거. ← Phase C/D의 씨앗 |
| `run_efficiency_map.py` | `eMach/mlxperPJT/JEET/` | 3모델 η/β_opt/손실성분 맵 생성 (⚠ 구 AF_RBF_model_*.json 참조 → 갱신 필요) |
| `AF_model_SC_exponent.json` | `.../map_exports/e10/SC/` | 논문1 Step 6-Q 산출 멱지수 분리모델 (export_model_json 라운드트립 검증) |
| `MotorLAB_elecdata_{Ref,SC_hyb,SC_fullfea,SC_calibrated}.mat` | `.../map_exports/e10/effmaps/` | **Lab 효율맵 ground truth** (원장 Terminal=Shaft+ΣLoss 폐합 검증됨) |
| `pybridge/` | `eMach/mlxperPJT/JEET/` | MATLAB↔Python 브릿지 (Phase D에서 맵→Simscape 전달) |

**핵심 함의**: 정상상태 "손실=임피던스" 표현(R_ac 직렬 + 철손 병렬)이 이미 존재하고 Lab의
"Iron Loss in Voltage Vector" 옵션과 정합. 과도 MIL은 여기에 `dλ/dt` 항만 더해 시간전진하면 됨.

---

## 2. Phase 계획

### Phase A — 정상상태 map-based 효율맵 & Lab 벤치마크  [대부분 구축됨]
논문 1 Step 8과 **공유 산출물**(효율맵 Fig).
- **A1** `run_efficiency_map.py`를 현행 AF 모델(멱지수 분리형, `AF_model_*_exponent.json`)로 갱신.
  `e10_SatuMap.mat` 필드·경로 확인.
- **A2** η / β_opt / 손실성분을 Motor-CAD Lab(`effmaps/MotorLAB_elecdata_{Ref,SC}.mat`)과 대조.
  parity plot, Δη 분포, β_opt 편차. (Ref & SC. HalfSC는 460A↑ FEA 미수집으로 제외.)
- **A3** 정상상태 원장 폐합 문서화: 각 운전점 `P_elec = P_mech + ΣP_loss` (EEC에 이미 내재).
  → 순시수지의 정상상태 극한.
- **산출**: 검증된 효율맵 패키지 + Lab parity 그림. **기존 데이터로 지금 실행 가능**, 백그라운드 배치와 무충돌.

### Phase B — 자속맵 가역성 & 보존장 재구성  [신규·연구]
- **B1** 가역성 잔차 `r(i_d,i_q) = ∂λ_d/∂i_q − ∂λ_q/∂i_d` 를 SatuMap 그리드에서 측정.
- **B2** 0이 아니면, 단일 공에너지 포텐셜 `W'(i_d,i_q)`에서 보존 λ 재구성:
  ∇W'=(λ_d,λ_q) 최소자승 적합, 또는 (λ_d,λ_q) 벡터장 Helmholtz 투영으로 curl-free 성분만 유지.
- **B3** 정상상태 토크/η 영향 정량화(작아야 함) → 재구성이 FEA 정합 정확도를 훼손하지 않음을 입증.
- **산출**: 보존 λ 맵 + 가역성 연구 그림. **과도 에너지 폐합의 enabling step.** 순수 Python·기존 데이터.

### Phase C — 손실→임피던스 소자 (정상→순시)  [부분 구축됨]
- **C1** `R_AC(ω,i_d,i_q)` 맵을 AF-보정 P_AC에서 정식화 (솔버의 점별 R_ac를 ω 포함 전체 맵으로 사전계산).
- **C2** 철손 소자 **과도용 토폴로지** 결정. 정상상태 I_fe 페이저형 → 시간영역 소자로:
  1차안 = 역기전력 뒤 병렬 `R_c(ω)`(무기억). 히스테리시스 이력의존성은 잔차오차로 문서화(연구 caveat).
  P_Fe = k_h·f·B² + k_e·f²·B² 분해 → eddy 성분은 ω-정합, 히스테리시스는 난제(→ Matsuo CLN 확장 여지).
- **C3** 정합성 검사: 순시소자를 정현파 운전점에서 사이클 평균 → 맵의 P_AC, P_Fe 정확 재현 (Phase A와 연결).
- **산출**: R_AC, R_c 맵 생성기 + 토폴로지 정의 + 평균-정합 증명.

### Phase D — 과도 MIL 모델 (Simscape/Simulink)  [신규·greenfield, 최대 신규작업]
- **D1** dq 회로: `v_d = R_s i_d + dλ_d/dt − ω_e λ_q`, `v_q = R_s i_q + dλ_q/dt + ω_e λ_d`,
  λ는 보존 LUT(Phase B), R_AC 직렬 + R_c 병렬(Phase C), T_e는 공에너지 정합식.
- **D2** 두 twin: **Simscape**(에너지 포트, 구조적으로 보존 — 기준) + **Simulink MATLAB-Function**
  (신호레벨, 투명, 수동 감사). 권장: Simscape="닫히는가"의 기준, Simulink="왜/어떻게"의 계측기.
- **D3** 구동: v_d,v_q 규정 또는 전류제어기 폐루프 + 속도 프로파일.
- **D4** map container → pybridge로 Simscape 빌드 스크립트.
- **선행 확인**: Simscape/Powertrain Blockset 라이선스, FEM-Parameterized PMSM 블록의 보장범위.
- **산출**: `.slx` 모델 + 빌드 스크립트.

### Phase E — 순시 전력수지 감사  [신규·연구 핵심]
- **E1** timestep별 로깅: `P_elec=(3/2)(v_d i_d+v_q i_q)`, `dW_m/dt`, `P_mech=T_e·ω_mech`,
  `P_Cu,DC`, `P_Cu,AC`, `P_Fe`; 잔차 `ε(t) = P_elec − dW_m/dt − P_mech − ΣP_loss`. 목표 |ε|/P_elec < tol.
- **E2** ablation: (i) 비가역 vs 가역 λ → ε(t) 스퓨리어스 리플 소거; (ii) 평균손실-합산 vs 임피던스-소자
  → 이중계상 제거; (iii) 스텝 + 드라이브사이클 구간 → 누적 `∫ε dt`.
- **E3** "지켜지게 하는 법" = 가역성 투영 + 손실=임피던스 + 정합 평균 → **논문의 Method 섹션**.
- **산출**: 잔차 vs 시간 그림, 에너지 원장 폐합, ablation.

### Phase F — 검증 & 집필
- **F1** 정상상태: map η vs Motor-CAD Lab (Phase A 재사용).
- **F2** 과도: MIL i_d,i_q,T_e,에너지 vs TS-FEA (몇 운전점 / 짧은 사이클).
- **F3** 드라이브사이클: 총 에너지 vs 기준. 정합 모델은 일치, 나이브 map-based는 drift
  (Dhakal/Graz 프레이밍 — 논문1 intro에서 이미 인용).
- **F4** 집필.

---

## 3. 자산 → Phase 매핑

| 자산 | A | B | C | D | E | F |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| e10_SatuMap.mat (λ, P_Fe, R_dc) | ● | ● | ● | ● | | |
| AF_model_*_exponent.json + export_model_json | ● | | ● | | | |
| MtpaFwSolver.py (EEC R_ac + I_fe) | ● | | ● | ● | | |
| run_efficiency_map.py | ● | | | | | ● |
| effmaps/MotorLAB_elecdata_*.mat (Lab GT) | ● | | | | | ● |
| pybridge (MATLAB↔Python) | | | | ● | | |
| Carstensen §4.3.1/Fig4.27 (전력흐름도) | | | | | ● | |
| MILS/Cauer(Sano/Ahagon), Zhu, Matsuo CLN | | | ● | ● | | |
| SyRE MMM calcTnPoint (EEC 근거) | ● | | ● | | | |

---

## 4. 리스크 & 미결

- **철손 순시 표현 (최대 기술 리스크)**: 히스테리시스는 이력의존 → 무기억 R_c는 근사.
  완화: eddy(ω-정확)/히스테리시스(잔차 문서화) 분해, 또는 단순 동적 히스테리시스(Cauer/CLN→Matsuo) 확장.
- **Simscape FEM-Param PMSM 중복 우려**: 정확히 무엇을 보장/미보장하는지 D1에서 확인 후 포지셔닝
  (가역성 미강제 + AC-R 미보정으로 예상 — 차별점).
- **PWM 고조파 AC손실**: 기본파 R_AC는 OK, PWM은 `R_AC(f)` 필요 → **범위 결정**:
  논문 2는 기본파 한정, PWM(Zhu 어드미턴스)은 논문 3 또는 확장절.
- **가역성 재구성이 FEA 정합 정확도 훼손 금지**: B3가 가드.

---

## 5. 범위·순서 권고

- **논문 2 코어 = A+B+C+D+E+F (기본파 한정 손실).**
- **지금 착수 가능** (순수 Python·기존 데이터·백그라운드 배치 무충돌): **A**(효율맵 vs Lab), **B**(SatuMap 가역성).
- **D(Simscape)** = 대형 신규 빌드, MATLAB/Simscape 라이선스 확인 선행.
- **PWM/Zhu + 동적 히스테리시스/CLN** = 논문 3 또는 확장절.

### 마일스톤 분할 옵션 (증분 출판)
- **M1 = A+B+C** "가역성 강제 + 임피던스 손실 정상상태 효율맵, Lab 검증" → 컴팩트한 letter/conference 급.
- **M2 = D+E+F** "과도 MIL + 순시 전력수지" → 전체 저널 논문.
- M1을 먼저 닫으면 논문 1 Fig(효율맵)도 동시 확보, M2 리스크 격리.

---

## 6. 즉시 실행 첫 스텝 (승인 시)

1. `run_efficiency_map.py` AF 모델 형식 갱신 (A1) — 멱지수 분리형 로더 연결.
2. Ref/SC 효율맵 재계산 → `effmaps/MotorLAB_elecdata_{Ref,SC}.mat` parity 대조 (A2).
3. SatuMap 가역성 잔차 히트맵 (B1) — 순수 Python, 즉시.
→ 이 3개는 백그라운드 정규화/kturn 배치와 무관하게 병렬 진행 가능.

---

## 7. Phase A/B 1차 실행 결과 (2026-07-19) — A1·A2·B1 완료

**산출물** (`map_exports/e10/paper2_phaseA/`):
- `effmap_vs_lab_{Ref,SC}.png`, `PhaseA_effmap_vs_lab_report.md`
- `reciprocity_residual.png`, `PhaseB_reciprocity_report.md`
- 스크립트: `run_efficiency_map.py`(갱신), `compare_effmap_vs_lab.py`(신규),
  `reciprocity_check.py`(신규), 멱지수 JSON `AF_model_{Ref,HalfSC,SC}_exponent.json`

### A1 — run_efficiency_map.py 갱신
- 구 `AF_RBF_model_*`(base@2k scalar) → `AF_model_*_exponent`(base@16k 멱지수) 로드.
- 모델별 k_r/I_max/토크축 물리부여 + **권선온도 80°C R_dc 보정**(Lab 정합) + I_rms 저장.

### A2 — map-based vs Motor-CAD Lab (Δ = map − Lab, 80°C 보정 후)
| 채널 | Ref mean | Ref MAE | SC mean | SC MAE |
|---|---|---|---|---|
| η (iso, Lab철손) | +0.78% | 1.29% | +3.86% | 3.86% |
| I_rms | −4.5 A | 9.7 A | −7.1 A | 17.2 A |
| Cu_DC | −0.56 kW | 1.08 | −3.09 kW | 3.09 |
| **Cu_AC** | −0.63 kW | 0.63 | **−6.35 kW** | 6.35 |
| Iron | −0.70 kW | 0.70 | −1.95 kW | 1.95 |

**검증된 것**: (1) 80°C 온도보정으로 Cu_DC·효율 대폭 개선(Ref eta_iso +2.14→+0.78%),
(2) I_rms parity가 Ref에서 대각선 밀착 → **SatuMap λ + MTPA/FW EEC 솔버 자체는 유효**,
(3) Ref 효율맵(iso)이 Lab과 시각적 일치.

**구조적 결함(→Phase C 최우선)**: **AC동손·철손이 map≈0**. 효율맵 AC base가
e10_SatuMap의 단일조건 Stator_Copper_Loss_AC(Ref ~26W)를 k_a/k_r² 스케일한 값이라,
AF(비율 ~1-3)만으론 **주파수 스케일링(∝f²)·SC 후막도체 근접효과의 절대크기**가 빠짐.
→ Lab AC동손 최대 60 kW(SC) vs map ~0. **논문1은 손실레벨(물리 h_ac,f_ac)에서 AF를
검증했지만 효율맵 파이프라인은 Ref-SatuMap 작은 값을 base로 써 크기를 잃음.**
철손도 동일(단일조건 → 속도스케일 부재, Lab 최대 16 kW vs map ~0).
→ **처방**: 속도분해 hybrid AC·철손 맵(모델별 물리값) × AF 재구성.

### B1 — 자속맵 가역성 잔차
- e10_SatuMap(6×8) `r = ∂λ_d/∂i_q − ∂λ_q/∂i_d`: max|r| 0.097 mH, **상대잔차 중앙값 30.6%**,
  스퓨리어스 공에너지 |∬r| 2.43 J → 비보존장 존재 확인(Phase B 정당화). 단 저해상도
  이산화오차 포함 → 정밀값은 고해상 SatuMap 재수집 시 갱신.

### Phase 우선순위 재조정 (1차 결과 반영)
- **Phase C가 효율맵 정확도의 지배요인**(속도분해 손실맵). Ref eta_iso 0.78%는 이미 양호,
  SC 3.86%의 대부분이 AC/철손 크기 결손 → Phase C로 해소.
- **Phase B는 우선순위 하향**: Ref 수준에서 flux/토크당전류 편차가 이미 작음(I_rms 대각선).
  가역성 강제는 과도 MIL 에너지 폐합 *보증*용으로 여전히 필요하나 정상상태 개선폭은 작음.
- 다음 스텝 후보: (C1) 속도분해 AC동손 맵 재구성(모델별 물리 hybrid base × AF),
  (C2) Lab 철손 LUT 또는 에디/히스테리시스 분해 속도맵.
