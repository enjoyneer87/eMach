# CONTEXT_GUIDE.md — AC Loss Hybrid Method Master Guide

본 문서는 전기차용 Hairpin Winding 모터의 **AC 권선 손실(AC Winding Loss) 및 행동 모델(ROM) 전력 평형**을 연구하는 지식 베이스의 메인 컨트롤 마스터 가이드입니다. 본 프로젝트의 전체 문서 구조 및 핵심 방법론을 정리합니다.

---

## 1. 문서 맵 및 바로가기 링크

본 레포지토리의 연구 테마별 하위 마크다운 링크입니다. 각 파일명을 클릭하여 상세 문서를 볼 수 있습니다.

| 연구 테마 | 문서 링크 | 핵심 다루는 내용 |
|:---|:---|:---|
| **마스터 가이드 (본 문서)** | [CONTEXT_GUIDE.md](file:///d:/KangDH/Thesis/ACloss_Ref/CONTEXT_GUIDE.md) | Morisco 10-Step 절차, 이중계수(Double-Counting) 오류 분석 및 해결책 |
| **최신 논문 분석** | [ac_loss_paper_analysis.md](file:///d:/KangDH/Thesis/ACloss_Ref/ac_loss_paper_analysis.md) | JMAG 2025 (CLN/ECMC), Sazhu 2026 (복소투자율), Ju 2023 (하이브리드/Frozen Core) 비교 |
| **철손 & 파스발 정리** | [ac_loss_power_balance_analysis.md](file:///d:/KangDH/Thesis/ACloss_Ref/ac_loss_power_balance_analysis.md) | JMAG 2018 (비히스테리시스 전력 불평형), ROM에서의 파스발 정리 한계 및 ECMC의 역할 |
| **고속 맵 정합 & 정현파 매칭** | [ac_loss_steady_state_calibration.md](file:///d:/KangDH/Thesis/ACloss_Ref/ac_loss_steady_state_calibration.md) | **1단계: 정현파 기본파 검증(Sinusoidal Match)**, 2단계: 해석적 PWM + CLN 복소 임피던스 고속 정합 |

---

## 2. Morisco PhD Thesis — 완전한 10-Step 절차

본 프로젝트의 기준선이 되는 Morisco 하이브리드 PEEC-FEA 해석 방법론의 완전한 10단계 시퀀스입니다.

### Step 1: Filament 분할
도체를 $n_x \times n_y$ 균일 filament으로 분할. 필라멘트 변 길이 목표: $a_\Lambda \leq 0.1\delta$
$$\delta = \frac{1}{\sqrt{\pi f \mu_0 \sigma}}$$

### Step 2: MQS FEA 수행 (도체 내 eddy 미계산)
* 도체를 **stranded** (와전류 없는 균일 전류밀도)로 설정
* Rotor 회전 포함, 시간 도메인 magnetostatic (quasi-static), 128 rotor positions (1 electrical period)
* 출력: $B(x,y,t)$, $H(x,y,t)$, $\mu_r$ per element

### Step 3: 자화(Magnetization) 추출
$$M = \frac{B}{\mu_0} - H$$

### Step 4: 등가 면전류밀도(Surface Current)
Iron-air 경계면에서 tangential jump:
$$K_{mag} = M \times \hat{n} = M_x n_y - M_y n_x$$

### Step 5: 등가 자화전류(Magnetization Current)
$$i_{mag,\theta} = K_{mag} \cdot |s_\theta| \quad \text{(edge segment length)}$$

### Step 6: Impedance Matrix 구성 $Z_\Lambda$
**Dirichlet Green's function** (원형 경계 R에서 $A_z=0$):
$$L_{vw} = -\frac{\mu_0 l}{2\pi}\left[\ln|\xi_v - \xi_w| - \frac{1}{2}\ln\left(|\xi_v|^2|\xi_w|^2 - 2\text{Re}(\xi_v\overline{\xi_w}) + 1\right)\right]$$
여기서 $\xi = (x + jy)/R$, $R = l$ (축 방향 길이)
$$Z_\Lambda = R + j\omega L$$

### Step 6b: L_ext — Rectangular Image Green's Function (Method 3+4)
Method 3+4 구현에서는 **filament↔boundary edge** 커플링 행렬을 직사각형 Image Method로 계산:
* 경계 형상: 직사각형 슬롯 벽 + Tooth-tip extension 포함 (143개 소스)
* Region weight ($w_{ag} > 1$, $w_{tw} = 1$, $w_{yk} < 1$) 적용으로 에어갭 측 자화 강도 차이 보정.

### Step 7: 일방향 피드백 결합의 물리적 한계 — Morisco §4.7 명시

**[방법 자체의 한계 — Morisco §4.7.1 명시]**  
FEA-PEEC 하이브리드 결합 모델은 도체 영역 내 비균일 전류 밀집(current crowding) 현상이 역으로 주변 강자성체의 국부 자화에 미치는 상호 피드백 반응을 무시합니다.
Morisco가 직접 기술하였듯이: *"In this context, the effect of the inhomogeneity of the current density distribution in the conductor area on its local magnetization is neglected."*  
이로 인해 고속/고부하 운전 영역에서 극심한 전류 밀집이 발생하여 슬롯 주변 누설 자속 왜곡이 심화될 때, 이러한 자계 분포 변화가 강자성체의 국부 포화 상태에 미치는 실시간 결합 효과를 모사하는 데 태생적인 물리적 제약을 가집니다.

### Step 8: V_mag 계산 (자화전압)
$$V_v = j\omega \sum_\theta L_{weighted}(v, \theta) \cdot i_{mag,\theta}$$

### Step 9: PEEC 풀기 (Constrained Network Solve)
* Imposed current: $i_{imposed} = Z^{-1}C(C^T Z^{-1}C)^{-1} \cdot I$
* Magnetization response: $i_{mag,raw} = Z^{-1} \cdot V_{mag}$
* Constraint projection: $i_{total} = i_{imposed} + i_{magnetization} \quad (\text{Constraint: } C^T i_{total} = I)$

### Step 10: FFT 시계열 확장 (ECCE 2020)
* $i_{mag}(t)$ → DFT → 고조파별 phasor $\hat{I}_{mag}[n]$
* 고조파 n에 대해 $Z(n\omega)$로 독립 PEEC solve (DC 제거)
* 시간 평균 총 손실: $P = \sum_n P_n$

---

## 3. 단순화 방법들 (PEEC 불필요)

### Volpe/Ju Method (Layer-Based Dowell)
$$k_R(m, \xi) = M(\xi) + \frac{(2m-1)^2}{3}Q(\xi)$$
* $M(\xi) = \xi \frac{\sinh 2\xi + \sin 2\xi}{\cosh 2\xi - \cos 2\xi}$ (skin)
* $Q(\xi) = 2\xi \frac{\sinh\xi - \sin\xi}{\cosh\xi + \cos\xi}$ (proximity)

### El Hajji Direct / Ju 2023 (Centroid B)
$$P_{prox} = \sigma l \omega_i^2 B_{r_i}^2 \cdot \frac{bh^3}{24} + \sigma l \omega_i^2 B_{\theta_i}^2 \cdot \frac{b^3h}{24}$$

### Popescu Superposition (PWM)
$$P_{total} = \sum_\nu [P_{skin}(\nu) + P_{prox}(\nu)]$$

---

## 4. 코드 구현 지침

### 변수 명명 (논문 Nomenclature)
* $b$: 도체 접선방향 폭 (Motor-CAD: `Copper_Height`) [m]
* $h$: 도체 반경방향 높이 (Motor-CAD: `Copper_Width`) [m]
* $n_L$: 슬롯당 도체 층수
* $\sigma$: 구리 도전율 (Cu@20°C ≈ 5.8e7 S/m)
* $l$: 유효 스택 길이 [m]

### e10 모터 운전점 데이터
* **OP1 (기본속도)**: 4000 rpm, 240 Arms, $f_e$ = 266.67 Hz, $\delta$ = 4.04 mm, $\xi$ = 0.62
* **OP2 (최고속도)**: 16000 rpm, 185 Arms, $f_e$ = 1066.67 Hz, $\delta$ = 2.02 mm, $\xi$ = 1.24

---

## 5. E-Axle 파워트레인 시스템 사이징 최적화 응용 (System-Level Application)

본 스케일링 및 고속 보정 프레임워크(SCL-M + Sparse Calibration)의 핵심 효용성을 입증하기 위해, 차량 시스템 단위의 공동 최적화 시나리오를 구상하고 프로젝트 계획에 추가합니다.

### 5.1 최적화 설계 문제 정의
*   **설계 변수**: 
    *   고정자 외경 반경 스케일 $K_R \in [0.8, 1.5]$ (외경 $160\text{ mm} \sim 300\text{ mm}$)
    *   철심 적층 길이 축 스케일 $K_A \in [0.6, 1.6]$ (적층 $90\text{ mm} \sim 240\text{ mm}$)
    *   감속기 기어비 $G_R \in [6.0, 12.0]$
*   **요구 사양**: C/D 세그먼트 승용 EV, 150 kW peak, 350 Nm peak torque, WLTP 사이클 추종.
*   **전원 사양**: $800\text{ V}$ DC link, Max current $460\text{ A}_{pk}$ (Table 2의 M1/M2/REF 스펙과 100% 일치).

### 5.2 역방향 차량 동역학 시뮬레이션 (Backward-Facing Vehicle Model)
대규모 설계 공간 탐색을 위해 1 Hz 단위의 대수식 기반 전비 시뮬레이터를 Python으로 구현합니다.
1.  차량 차속 프로파일 $v(t) \rightarrow$ 요구 구동력 $F_{trac}(t)$ 및 휠 토크/속도 산출.
2.  감속비 $G_R$을 대입하여 모터 요구 동작점 $(\omega_m(t), T_{ref}(t))$ 결정.
3.  스케일링된 모터의 2D 효율/손실 맵에서 동작점별 손실을 실시간으로 2D Interpolation하여 합산.

### 5.3 목적 함수 및 파레토 프론트 (Multi-Objective Pareto Front)
*   **목적 함수**: 
    1.  WLTP 사이클 총 소모 전력량 (Wh/km) 최소화
    2.  모터 활물질 재료비 및 감속기 무게 최소화
*   **비교 대조군**:
    *   **Case 1 (기존 하이브리드)**: 약자속 고속 AC 동손이 과소평가되어, 고속 기어비와 작은 모터가 최적이라고 잘못 판정하는 오설계 분석.
    *   **Case 2 (제안 기법)**: 고속 포화에 따른 Current Crowding을 정확히 교정하여, 시스템 효율과 중량을 균형 있게 최적화하는 진정한 파레토 프론트 제시.
