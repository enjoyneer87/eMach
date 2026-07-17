# TRANSITION_GUIDE.md — Workspace Transition & Sizing Optimization Guide

본 문서는 타 워크스페이스(또는 신규 개발 환경)의 Antigravity 어시스턴트가 본 연구 프로젝트의 **학술적 맥락, 최근 문헌 분석 결과, 그리고 E-Axle 최적화 시나리오 설계 방향**을 즉각 파악하고 개발을 이어갈 수 있도록 정리한 전이 마스터 가이드입니다.

---

## 1. 프로젝트 현재 상태 (Project State)

1.  **논문 원고 수정 완료**:
    *   [JEET_KDH_rev1.tex](file:///Users/kdh2021-air/Library/CloudStorage/GoogleDrive-phareal87@gmail.com/내%20드라이브/ACloss/JEET/JEET-2024_rev1/JEET_KDH_rev1.tex) 및 마크다운 버전에 기존 하이브리드 필드-회로 기법(FEA-PEEC/Morisco 등)의 근본적인 학술적 한계점을 성공적으로 기술하였습니다.
    *   **핵심 비판**: 도체 내의 비균일 전류 밀집(Current Crowding)이 강자성체 국부 자화에 미치는 상호 피드백 반응을 무시하는 일방향 피드백 결합(Unidirectional coupling)의 물리적 가정을 인용하여 비판하였습니다.
    *   **중요**: 개인 구현 단계에서의 디버깅 이슈(예: 이중 계수 오류, 100배 과대평가 등)는 학술적 가치 보존을 위해 원고에서 완벽히 배제하고 정제된 이론적 리뷰만 남겼습니다.
2.  **서지 정보(Bibliography) 업데이트 완료**:
    *   [sn-bibliography2_full.bib](file:///Users/kdh2021-air/Library/CloudStorage/GoogleDrive-phareal87@gmail.com/내%20드라이브/ACloss/JEET/JEET-2024_rev1/sn-bibliography2_full.bib) 파일의 끝에 Morisco 학위논문 서지 정보(`morisco2020extended`)를 삽입하였습니다.

---

## 2. iCloud `MNDocs` 내 신규 스케일링 문헌 분석 요약
이전 세션에서 iCloud MarginNote 폴더 내에서 발굴하여 [ac_loss_paper_analysis.md](file:///Users/kdh2021-air/Library/CloudStorage/GoogleDrive-phareal87@gmail.com/내%20드라이브/ACLoss_REF/ACLoss_Ref/ac_loss_paper_analysis.md)에 통합한 주요 학위논문들의 핵심 요지입니다:

*   **Rafal Wrobel (2014, PhD)**: 모터 열 등가 네트워크(LPTN)에서 AC 저항 저하 및 동손의 기하학적/열적 스케일링 관계 수립 (본 연구의 스케일링 법칙 물리적 타당성 지원).
*   **Olaf Borsboom & Theo Hofman (TUE, 2022/2025 PhD)**: 변속기/기어비와 모터 스케일링을 동시에 탐색하는 RBF 대리 모델 및 볼록 최적화 프레임워크 제시 (본 연구의 실시간 효율 맵 공급 필요성 입증).
*   **Jansson & Lund (Chalmers, 2020/2023 PhD)**: 고속 약자속 제어 영역에서 고정자 치(teeth)의 비선형 국부 포화에 의한 누설 자속 왜곡 분석 (보정 인자 $k_{cc}(\omega, I)$의 물리적 원인 제공).
*   **Ayoub (Ghent Univ., 2024 PhD)**: E-Axle 플랫폼 초기 단계를 위한 모터 스케일링-기어비 다목적 최적화 설계 프레임워크 (본 연구의 파워트레인 레벨 최적화 벤치마크).

---

## 3. E-Axle 시스템 최적화 시나리오 설계 (Phase 7 계획)

다른 워크스페이스에서 구현하게 될 **시스템 레벨 파워트레인 최적화 프로그램**의 아키텍처 가이드라인입니다.

### 3.1 모터 및 전원 기준 사양 (Table 2 일치)
*   **기준 모터 (REF)**: 8극 48슬롯 IPMSM ($D_s = 200\text{ mm}$, $l_{st} = 150\text{ mm}$), Hairpin winding (8층, 2병렬).
*   **인버터 전원**: $800\text{ V}$ DC link ($V_{max} = 800/\sqrt{3}$), 최대 공급 전류 $I_{max} = 460\text{ A}_{pk}$, SVPWM 변조.

### 3.2 설계 변수 및 탐색 범위
*   **반경 방향 스케일 ($K_R$)**: **0.8 ~ 1.5** (외경 $160\text{ mm} \sim 300\text{ mm}$ 연속형 변수)
*   **축 방향 스케일 ($K_A$)**: **0.6 ~ 1.6** (철심 적층 $90\text{ mm} \sim 240\text{ mm}$ 연속형 변수)
*   **감속기 기어비 ($G_R$)**: **6.0 ~ 12.0** (0.5 간격 스윕)

### 3.3 핵심 알고리즘 아키텍처

#### ① 스케일링 모터 효율 맵 생성기 (MTPA & Field Weakening Solver)
각 그리드 $[K_R, K_A]$ 마다 아래 최적 제어 수치 알고리즘을 수행하여 효율 맵을 30초 내에 생성합니다.
*   **입력**: SCL-M 및 RBF 보정을 통해 대수적으로 도출된 2D 자속 맵 $\lambda_{d,q}(i_d,i_q)$ 및 보정된 2D 손실 맵 $P_{loss}(i_d,i_q,\omega)$.
*   **제어 추적**:
    *   **MTPA 대역**: 요구 토크 $T_{ref}$를 생산하는 최소 전류 벡터 $(i_d, i_q)$ 검색.
    *   **약자속 제어 대역 (FW)**: 회전 속도 상승으로 유도전압 $\sqrt{v_d^2+v_q^2} > V_{max}$가 될 때, 전류 한계 $I_{max}$ 내에서 전압 한계를 만족하도록 $i_d$를 음의 방향으로 증가시키며 토크 매칭점 추적.
    *   *주의*: 전압 계산 시 고주파 전압 강하를 고려한 $R_{ac}(\omega)$ 저항 매개변수 적용 필수.

#### ② 1Hz 역방향 차량 동역학 시뮬레이터 (Backward-Facing Vehicle Model)
대리 모델의 초고속 전비 계산을 위해 Python으로 구현하는 가벼운 차량 전비 해석기입니다.
*   **입력**: WLTP 차속 프로파일 $v(t)$ (1800초 데이터).
*   **연산 시퀀스**:
    1.  가속 저항, 공기 저항, 구름 저항식에 기반해 휠 구동력 $F_{trac}(t)$ 계산.
    2.  감속비 $G_R$을 대입하여 매 초마다 모터 축의 운전점 $(\omega_{motor}(t), T_{motor}(t))$ 결정.
    3.  생성된 모터 2D 효율 맵을 2D Interpolation하여 초당 소모 전력(Wh)을 합산하여 최종 전비(Wh/km) 계산.
*   **차량 중량 업데이트**: 모터 외형 치수($K_R, K_A$) 및 감속비 $G_R$ 변화에 따른 모터 활물질 질량 및 감속기 질량 변화를 차량 공차 중량에 실시간으로 가산.

### 3.4 비교 분석 및 Pareto Front 시각화
*   **비교 대조군**:
    *   **Case 1**: 고속 AC 동손을 상수로 보거나 누락한 모델 $\rightarrow$ 고속 운전이 필요한 소형 모터 + 큰 기어비를 최적으로 오도하는 경향 증명.
    *   **Case 2 (제안 기법)**: 정확한 고속 AC 동손을 반영하여, 진정한 WLTP 최고 효율 및 최소 중량의 최적점 제시.
*   **최종 출력물**: 
    1.  X축(파워트레인 중량/재료비) - Y축(WLTP 전비 소모량 Wh/km)의 **다목적 파레토 프론트 곡선 비교 그래프 (fig10.png 등)**.
    2.  최적 설계 수치 결과 정리 표 (Table 4 등).
