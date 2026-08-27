# PWM 대역분할 계획 — 스칼라 AF 의 주파수 한계를 넘는다

> 작성 2026-08-27. 논문 1이 정직하게 그어 둔 경계(정현파 여자 한정)를 여는
> 작업. 논문 2(턴 축)와 별개 갈래이며, 결합 여부는 분량을 보고 결정.

## 1. 왜 필요한가 — 실측 근거 (기존 데이터)

`map_exports/e10/checks/ts_harmonic_af.json` (§12.4, Parseval 검증 0.6%):

| | n=1,3,5 손실 비중 | n=1~5 AF | 홀수 n≥9 AF |
|---|---|---|---|
| Ref 16k | 93.2% | 1.36~1.93 | 1.02 ~ **6.2** |
| SC 16k | 96.3% | 1.46~2.37 | 2.25 ~ **13 이상** |

- 정현파 구동에서는 n≥9 비중이 <4% 라 스칼라 AF 가 성립한다 (논문 1).
- PWM 은 캐리어 측대역에 **큰 에너지를 정확히 그 대역에 주입**한다.
  AF_n 이 2~15로 폭주하는 대역이므로 스칼라 AF 외삽은 정의상 실패 —
  이것이 논문 1 결론이 PWM 을 배제한 이유이자, 이 계획의 출발 실측이다.
- 짝수 n 의 AF(10^4 대)는 분모(MS 필드)가 대칭상 0이라 생기는 잡음 —
  분석에서 제외한다.

## 2. 정식화 — 대역분할 AF

    P_wdg,AC = Σ_저대역 AF(ω,I,β)·P_hyb,n  +  Σ_고대역 AF_hi·P_cap,n

- **저대역** (기본파~슬롯 조화, n≲7): 논문 1의 AF(ω,I,β) 그대로.
- **고대역** (캐리어 측대역): 분모를 캡 커널로 교체 —
  f² → f_t·f,  f_t = 1/(π μ0 σ h_c²)  (Volpe 전환 감지, §12.16에서 생산
  하이브리드 재현 평균비 0.950·corr 0.9953 로 이미 검증된 커널).
- **가설 H1**: 캡 분모 위에서 AF_hi 는 상수에 가깝다 (유도 지배역에서
  반작용 몫이 포화 — §12.13 의 1/AF_BVP−1 = 반작용 몫 실측과 정합).
- **가설 H2**: 고대역 손실의 축척 법칙은 k_r¹ (논문 1 결론 문장, Kim TIE
  2026 과 정합) — 즉 고대역 AF_hi 는 상사 전달이 **더 쉽다**.

## 3. 0단계 — 기존 데이터 선별 (2026-08-27 실행, **경로 폐쇄로 판정**)

`run_bandsplit_screen.py` 로 정현파 조화 꼬리(홀수 n=9~23)에 캡 분모를
적용해 봤다. **결과: 부적격.**

| | 원래 logstd | 캡 logstd | 캡 AF 가중평균 |
|---|---|---|---|
| Ref 16k | 0.655 | **0.904 (악화)** | 23.0 |
| SC 16k | 0.809 | **1.033 (악화)** | 253.4 |

- 캡 분모는 꼬리를 평탄하게 만들지 않고 악화시킨다. 원인은 §12.4 가 이미
  경고한 **원천 귀속**: 정현파 구동의 고조파 꼬리는 주입된 f_n 에 대한
  응답이 아니라 **전류 집중이 기본파에서 생성한 혼합 산물**이다. 주파수
  전달함수의 프로브로 쓸 수 없다.
- 따라서 **H1 은 기각이 아니라 미검증** — 프로브가 무효였다. 정현파 데이터
  재활용 경로는 닫혔고, PWM 캠페인(4절)이 유일한 검증 경로임이 확정됐다.
- 교훈 → 캠페인 설계 반영: 여자를 **주입 전류 스펙트럼**으로 정의해야
  혼합 산물과 주입 응답이 분리된다. 전압원 PWM 만 돌리면 같은 귀속 문제가
  재발한다. (주입 실험 + 전압원 실험을 각 1점씩 비교하는 항목을 M2 파일럿에
  추가.)
- 부수 관찰(H2 방향): 혼합 산물 꼬리의 크기가 k_r 에 강하게 증가한다
  (캡 가중평균 SC/Ref ≈ 11배). 전류 집중 산물이 대형기에서 지배적이라는
  논문 1 서사와 정합 — 캠페인 동기 문장에 쓸 수 있다.
- 산출: `map_exports/e10/checks/bandsplit_screen.json`

## 4. 1단계 — JMAG FP-Fq 캠페인 (2026-08-27 경로 전환)

**Motor-CAD 라이선스 불가 → JMAG 경로로 전환** (저자 지시). 전환이 오히려
유리하다: 0단계가 요구한 **주입 스펙트럼 실험**이 FP(고정 투자율)+Fq(주파수)
해석의 정의 그 자체다 — 온로드 동작점에서 투자율을 얼리고 임의 주파수 전류를
주입해 선형 응답을 읽는다. 혼합 산물과 주입 응답이 구조적으로 분리된다.

**2024년 JMAG 자산 (전부 확인됨, 이 PC = 포트 38100)**:

| 자산 | 위치 |
|---|---|
| FP-Fq 프로젝트 REF | `D:\KangDH\Thesis\e10\JMAG\REF_e10_WTPM_PatternD_R1_FqMap_MSFp.jproj` |
| FP-Fq 프로젝트 SCL | 〃 `SCL_e10_WTPM_PatternD_R1_16kMapZM_FqwMSFP.jproj` |
| FP 조건 배선 스크립트 | 〃 `FqSetting.py` (JSOL 2024-09 생성) |
| FP-Fq 스윕 원형 | `Other/deve10_FqFPSCL.m` (200 Hz~20 kRPM 등가) |
| 도체별 줄손실 프로브 | `Calc/devSettingProbeJouleLoss.m` |
| MQS 과도 원형 | `Calc/deve10_JMAG_MQS_ACLoss*.m` |
| MS 도체 모델 (FP 참조해) | `E:\KDH\e10\MSConductorModel\*_FPMag.jproj` |
| MATLAB | R2026a CLI + `tools/jmag/callJmag.m` (Designer 23.1 COM) |
| **MQS 과도 전체 구축 (P4)** | `tools/jmag/dev_e10_ACLoss.mlx` — Transient2D 'Sin' 스터디, FEM 도체, 3상 정현 회로(`mkJmag3phaseConductorSinCircuit` + 진폭/주파수/위상 주입) |
| **PWM 회로 템플릿 (P4/M3)** | `tools/jmag/circuit/PWM_CurrentControl.jcir` + `loadJMAG_PWMInput.m` — PWM 전류제어 회로를 스터디에 로드하는 기성 헬퍼 |
| 파형역 하이브리드 커널 | `tools/loss/ACLOSS/devcalcHybridACLossWave.mlx` — [P_rect, P_1DInstant, P_1DrectG1, …] 시간역 평가 (대역분할 분모의 시간역 판) |
| MCAD↔JMAG 교차검증 선례 | `tools/loss/VeriCalcHybridACLossModelwithSlotB.mlx` (2024) |

**MLX 읽기** — 라이브 스크립트는 ZIP 컨테이너라 `matlab/document.xml` 에서
코드를 추출하면 된다. 추출기: `tools/jmag/mlx2m.py` (2026-08-27 추가).
관련 mlx 18종의 역할 지도는 이 표와 mlx2m 스캔으로 재생성 가능.

**메인 코드 계보** (저자 확인 2026-08-27: 브랜치 = `devVeriACLoss`, 당시
`JEET*.mlx` 를 메인처럼 써서 함수들을 호출):

- 오케스트레이터: `JEETResult_rev1.mlx` — 속도당 1실행. MCAD 기계정보 →
  JMAG e10MS(정자기) → 메시 추출 → 하이브리드 계산 → e10MQS(과도, 회로) →
  FP Method → MCAD/JMAG/Pyleecan 비교. 후속판 `JEETResult_summary*.mlx`.
- ⚠ **클론 분기 주의**: 이 mlx 들은 `D:\KangDH\Emlab_emach` 클론에만 추적된다.
  두 클론이 같은 브랜치 이름(devVeriACLoss)인데 이력이 갈라져 있다 —
  Emlab HEAD 5a57fe90(07-26)은 EveryMotor 저장소에 없고, EveryMotor 쪽은
  3cd1cd7(06-01)에서 JEET mlx 들을 삭제했다. **파일럿 참조는 Emlab 경로로.**
  2024년 JMAG TS 결과 원본도 Emlab 쪽 `mlxperPJT/JEET/From38100/`
  (`JEET_ref_e10_WirePeriodic_Load_18k_*` — 18k rgh 케이스, jlog·MPTool 포함).
- 파일럿에서 MCAD 의존은 기계정보 취득뿐 — 상수(460 A, β 36°, 4극쌍)와
  보관 .mat(`From38100REF_TSFEA.mat`, `e10MS_ConductorModel.mat`)으로 대체.
- FP Method 스텁이 "MS > FP > **Noload & Armature Only**" 를 언급 — 2024년
  FP 참조가 분리판으로도 만들어졌다는 뜻. **온로드 총자계 참조 확인 관문**
  (5절 첫 항목)이 그래서 필수다.

**오픈소스 폴백** (저자 지정): JMAG 라이선스까지 막히면 **GetDP(ONELAB) 또는
Elmer** — 둘 다 비선형 과도 와전류 full FEA 가 가능해 FP-Fq 와 MQS 교차까지
대체할 수 있다. FEMM 은 시간조화·고정 μ 한정이라 P4(과도 교차)를 못 세워
후보에서 제외.

**M2 파일럿** — 드라이버 작성 완료: `Other/deve10_FqFP_PWMPilot.m`

- 주파수 12점/기계: 저대역 앵커 {0.5, 1, 2} kHz + 캐리어 3대역
  {5, 10, 20} kHz ± 0.5 kHz. 총 24 **선형** 해석 — Fq 는 점당 분 단위라
  파일럿 전체가 **1시간 미만** (Motor-CAD PWM 과도 추정 20~40h 대비 격감).
- P1 실행성 → P2 AF_hi(f) 평탄성(진짜 H1 선별) → P3 REF/SCL 비(H2)
  → P4 MQS 과도 1점 교차(선형 중첩 직접 판정). P4 경로가 예상보다 짧다 —
  `dev_e10_ACLoss.mlx` 의 'Sin' 스터디에 `loadJMAG_PWMInput` 으로
  `PWM_CurrentControl.jcir` 를 로드하면 PWM 전류 구동 과도가 되고, 2톤
  검증은 그 회로의 지령 파형만 바꾸면 된다.
- 후처리 `run_pwm_pilot_score.py` (export CSV → AF_hi 채점) — P1 통과 후 작성.

**M3 본 캠페인** (파일럿 통과 시): 운전점 확장은 (I,β) 격자 × 주파수인데
FP 참조해(MS)가 이미 24 (I,β) 조합으로 존재하므로, 케이스 곱만 늘리면 된다.
선형 해석이라 전수도 감당 가능 — 24 (I,β) × 12 f × 2기계 ≈ 576 선형 해석.

## 4b. COM 정찰 결과 (2026-08-28, 상주 MATLAB 세션에서 실측)

REF `FqMap_MSFp` 프로젝트를 COM 으로 열어 구조를 해독했다.

- 스터디: `REF_e10_WirePeriodic_Load_FqWithShiftAvgDiffMu_til18k` (1개)
- **30 케이스 = 전류 6레벨(0.1~460.1 A) × 위상 5** — Lab30 격자 그대로.
  각 케이스가 **자기 (I,γ) 의 온로드 FP 케이스를 1:1 참조** (설계표 col22).
  → **온로드 참조 관문 통과.** 관문이 케이스 구조 자체에 박혀 있다.
- FP 조건: FPType 3, **UseAverage=1, Step 1→121** — 참조해의 회전자 121스텝
  전체를 평균한 **시프트 평균 미분 투자율** (스터디명 그대로).
- 설계표 방정식에 **Cfreq=6000 Hz** — 2024년에 이미 캐리어 6 kHz 겨냥.
- 스텝 제어 StepType 2 / N 6 — 케이스당 주파수 6점 내부 스윕 구조인데
  Frequency 표는 비어 있음 (시작/간격 속성 또는 케이스 방정식 구동으로
  추정). **정확한 6점은 첫 실행 또는 2024 export CSV 로 확인** —
  `Emlab_emach/mlxperPJT/JEET/From38100/JEET_ref_..._case1_Jloss.csv` 등이
  당시 결과의 생존본.
- 프로젝트에 저장된 결과 없음 (AnyCaseHasResult=0) — P1 은 실제 실행 필요.
- SCL 도 대칭 프로젝트 `SCL_..._FqMap_MSFp.jproj` 존재 — 드라이버의
  `16kMapZM_FqwMSFP` 대신 이쪽이 짝이 맞다.

**세션 구조**: COM 로컬 서버는 클라이언트 종료 시 함께 내려가므로, 상주
MATLAB(`scratchpad/mlab_server.m` 파일 REPL) + `send_mlab.py` 로 구동한다.
JMAG COM 객체(app)가 그 세션 안에 산다.

## 5. 리스크 (JMAG 경로 기준)

- ~~FP 참조해 확인이 첫 관문~~ → **해소 (4b)**: 케이스별 온로드 1:1 참조 실측.
- FP-Fq 는 **선형(소신호) 응답** — 캐리어 진폭이 커서 국부 포화를 움직이는
  영역은 못 담는다. P4 의 MQS 교차가 그 경계를 정한다. (Zhu THFEA 와 같은
  전제 — 논문에서 인용으로 연결.)
- 스터디 케이스 확장 방식(단일 실행 vs 설계표 일괄)이 프로젝트 설정에 따라
  다름 — 드라이버에 양쪽 경로 주석. JMAG COM 은 GUI 를 띄우므로 라이선스
  좌석 1개를 점유한다.
- 저대역/고대역 경계 선택 민감도 — M3 에서 경계 스윕.
