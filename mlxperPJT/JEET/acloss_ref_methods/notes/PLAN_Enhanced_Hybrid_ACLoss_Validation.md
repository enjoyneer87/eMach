# Plan: Unified & Enhanced AC Loss Validation (6-Method Comparison)

> **Date**: 2026-06-20 (Updated)  
> **Motor**: e10 (8-pole 48-slot hairpin PMSM)  
> **Scaling**: k_Radial = {1.0 (Ref, 460A), 1.5 (HalfSC, 690A), 2.0 (SC, 920A)}  
> **Speeds**: [2000, 4000, 8000, 16000] RPM, Phase advance = 43.33°

---

## TL;DR

Motor-CAD TS (ground truth) 대비 AC loss 예측 정확도를 **6가지 방법론**으로 비교 검증:

| ID | 방법 | 모델링 관점 | 손실 공식 핵심 | 구현 상태 | 실행 노트북 |
|----|------|------------|---------------|-----------|------------|
| **(A)** | Volpe 1D Hybrid (Motor-CAD) | **1D Hybrid** (σ=0 FEA → Prox만) | Prox: $L_a w_r h_r^3 \sigma(\omega B)^2/24$ + Skin: 별도 | 미구현 (별도) | [pyMotorCAD_Hybrid_AClossCode.ipynb](../EveryMotor/eMach/mlxperPJT/JEET/pyMotorCAD_Hybrid_AClossCode.ipynb) |
| **(B)** | El Hajji 2D Hybrid | **2D Hybrid** (Full FEA → Br,Bθ 분해) | $\sigma l \omega_i^2 (B_r^2 bh^3 + B_\theta^2 b^3h)/24$ | 미구현 | [pyMaxwell_MotorCAD_MQS.ipynb](../EveryMotor/eMach/mlxperPJT/JEET/pyMaxwell_MotorCAD_MQS.ipynb) |
| **(C)** | Maxwell 2D μ_eff Enhanced | **2D Hybrid** + back-reaction 보정 | El Hajji + $G_{rect}(\xi)$ 보정 | 미구현 | [pyMaxwell_MotorCAD_MQS.ipynb](../EveryMotor/eMach/mlxperPJT/JEET/pyMaxwell_MotorCAD_MQS.ipynb) |
| **(D)** | Morisco FEA-PEEC | Analytical+PEEC (FEA 불필요) | Slot + Rotor field 분리 | ✅ `morisco_acloss.py` | [acloss_morisco_vs_ju.ipynb](../EveryMotor/eMach/mlxperPJT/JEET/acloss_morisco_vs_ju.ipynb) |
| **(E)** | Ju 1D Hybrid (Dowell+Popescu) | **1D Hybrid** (σ=0 FEA → Dowell 분리) | Skin: $R_{dc}I^2 M(\xi)$ + Prox: $F_{prox}(\xi)$ | ✅ `ju_hybrid_acloss.py` | [acloss_morisco_vs_ju.ipynb](../EveryMotor/eMach/mlxperPJT/JEET/acloss_morisco_vs_ju.ipynb) |
| **(F)** | Cauer Ladder Circuit | Circuit-equivalent (lumped) | $F_r = \text{Re}[Z_{in}]/R_{dc}$ | ✅ `cauer_modeling.py` | [cauer_modeling_example.ipynb](../EveryMotor/eMach/mlxperPJT/JEET/cauer_modeling_example.ipynb) |

### (A) Volpe vs (B) El Hajji vs (E) Ju — Hybrid 방법 세분 비교

| 구분 | (A) Volpe 1D Hybrid | (B) El Hajji 2D Hybrid | (E) Ju 1D Hybrid |
|------|--------------------|-----------------------|-----------------|
| **FEA 유형** | Simple FEA (σ=0, empty-slot) | Full transient FEA (σ≠0) | Simple FEA (σ=0) or Ampere 해석 |
| **B 측정 차원** | **1D**: B_tangential만 | **2D**: Br + Bθ 분리 | **1D**: B_tangential만 |
| **시간 처리** | 시간 평균 B_rms | B(t) → FFT → 고조파별 | 단일 주파수 or Popescu 중첩 |
| **Proximity 공식** | $L_a w_r h_r^3 \sigma(\omega B)^2/24$ | $\sigma l \omega_i^2(B_r^2 bh^3 + B_\theta^2 b^3h)/24$ | $\sigma \omega^2 B^2 bh^3/24 \cdot F_{prox}(\xi)$ |
| **Skin effect** | **별도 계산** (Motor-CAD 내부 kR) | ❌ Proximity에 통합 (2D이므로 자연 포함) | $R_{dc} I^2 M(\xi)$ 명시적 |
| **Skin/Prox 분리** | ✅ (**분리**: FEA→Prox, kR→Skin) | ❌ (합산) | ✅ 명시적 분리 |
| **고주파 보정** | Inductance-limited 스케일링 | FFT 자체가 반영 | $F_{prox}(\xi)$ Dowell 보정 |
| **PWM 고조파** | ❌ 미지원 | ✅ (FFT에 자연 포함) | ✅ Popescu 중첩 |
| **Multi-strand** | ✅ Bundle-level 확장 | ✅ (요소별 개별 계산) | ❌ 단일 도체 기준 |
| **FEA 시간** | 30 sec/OP | 15~20 min/OP | 0 sec (해석 fallback 시) |
| **정확도 (논문)** | TS 대비 3.5~15% | Ground truth급 | Volpe와 유사 (동일 B 사용 시) |
| **구현 위치** | Motor-CAD (+ pyMCAD 재구현) | 미구현 (Phase 2) | `ju_hybrid_acloss.py` (독립) |

> **핵심 통찰**:
> - **(A) Volpe**는 "심플 FEA에서 추출한 B로 **proximity loss만** 계산"하고, skin effect는 Motor-CAD 내부에서 별도로 처리 (kR 또는 DC loss 위에 추가). Motor-CAD 설계 루프의 기준선.
> - **(E) Ju**는 동일 B를 사용하되 Dowell 프레임워크로 skin ($M(\xi)$)과 prox ($Q(\xi)$)를 하나의 통합 모델 내에서 모두 계산.
> - **(B) El Hajji**는 full FEA에서 2D B(t)를 추출하므로 skin+prox가 자연스럽게 통합됨 (Br → 주로 skin, Bθ → 주로 prox).

### 방법론 분류 체계

```
                            AC Loss 계산 방법론
                                  │
        ┌─────────────────────────┼─────────────────────────┐
   1D Hybrid                 2D Hybrid                 Non-FEA
 (σ=0 FEA → 1D B)       (Full FEA → 2D B)        (FEA 불필요)
        │                       │                       │
   ┌────┼────┐            ┌────┼────┐            ┌────┼────┐
  (A)       (E)          (B)       (C)          (D)       (F)
Volpe      Ju         El Hajji  μ_eff       Morisco    Cauer
(Prox만)  (Dowell+    (Br+Bθ)  Enhanced     (PEEC)   (R-L래더)
+Skin별도  Popescu)             (+G_rect)            Fr=Re[Z]/Rdc
          Skin/Prox분리
```

**분류 기준** (Motor-CAD 기준선에서 확장 순):
- **(A)**: Motor-CAD 내장 Hybrid — **기준선**. σ=0 "Simple FEA"에서 1D B → proximity식 + 별도 skin
- **(E)**: (A)와 동일 패러다임이나 Dowell로 통합 처리 + PWM 고조파 확장
- **(B)(C)**: Full transient FEA (σ≠0) 후처리 → 2D B(Br+Bθ) — 가장 정확, 시간 多
- **(D)**: PEEC 회로 이론 + 해석 B-field → FEA 완전 불필요 (가장 빠름)
- **(F)**: 기하 치수만으로 R-L 래더 구성 → 임피던스에서 직접 Fr 계산 (회로 관점)

---

## 노트북 매핑

| 노트북 | 커버 방법 | 위치 |
|--------|-----------|------|
| `pyMotorCAD_Hybrid_AClossCode.ipynb` | (A) Volpe Hybrid — Motor-CAD simple FEA → 해석식 재현 | `eMach/mlxperPJT/JEET/` |
| `acloss_morisco_vs_ju.ipynb` | (D) Morisco vs (E) Ju — 층별 손실, kR sweep, PWM 고조파 | `eMach/mlxperPJT/JEET/` |
| `cauer_modeling_example.ipynb` | (F) Cauer — Fr 주파수 응답, 회로도 시각화 | `eMach/mlxperPJT/JEET/` |
| `pyMaxwell_MotorCAD_MQS.ipynb` | (B) El Hajji + (C) μ_eff Enhanced (예정) | `eMach/mlxperPJT/JEET/` |

---

## 현재 상태 요약 (2026-06-20)

### Morisco PEEC 구현 (pyMorisco_FFT_PEEC_Method34.ipynb)

| Step | 상태 | 결과 |
|------|------|------|
| 1. Filament 분할 (12×26×6) | ✅ 완료 | 1872 filaments |
| 2. MQS FEA (Motor-CAD Hybrid) | ✅ 완료 | 128 steps, B/H 추출 |
| 3-5. K_tang → i_mag (eq.4.52-4.53) | ✅ 완료 | boundary_cache (100 edges) |
| 6. Z_Λ (Dirichlet Circular, R=128.2mm) | ✅ 완료 | 1872×1872 |
| 6b. L_mutual (Dirichlet Circular) | ✅ 완료 | 1872×80 (검증/비교용) |
| 6b. L_ext (**Rect Image**, Method 3+4) | ✅ 완료 | 1872×143 (**실제 사용**) |
| 7. V_mag = jω·L_weighted·I_mag_fft_ext | ✅ 완료 | region weight 적용 |
| 8-9. FFT PEEC solve (DC제거, 고조파별) | ✅ 완료 | 14 harmonics |
| **검증** | ❌ k_ih=615~4761 | **~100x 과대** |

**Note**: 
- Morisco 논문 자체에 V_leak subtraction, (μr-1)·H_leak, PM/Load separation은 없음 (PhD thesis Ch.5 ELMO 확인 완료)
- Method34에서 `L_mutual_mat`(Dirichlet circular)와 `L_ext`(Rectangular image)는 **병렬 대안**이며, PEEC solve는 **L_ext만** 사용
- `L_ext`는 L_mutual을 확장한 것이 아닌, **다른 Green's function**으로 완전히 재계산한 독립 행렬

### 핵심 문제: V_mag 과대추정

Morisco thesis p.144 인정: *"Static FEM의 uniform J 가정으로 인해 conductor edge 근방의 자화가 과대 → i_mag 과대 → V_mag 과대."*

Morisco 자신의 OP (267~1067 Hz)에서는 1-4% 무시 가능했으나, 우리 IPM (8P/48S hairpin, 강한 PM)에서 39x 과대.

**R_dirichlet sweep 결과 (논문 내 파라미터 탐색):**
| R_dirichlet [mm] | k_ih | 비고 |
|------|------|------|
| 150 (현재, R=l) | 237 | 논문 default |
| 50 | ~120 | image 효과 약간 |
| 20 | ~50 | |
| 12 | ~30 | slot-size 수준 |
| **FEA Ground Truth** | **6.06** | — |

→ R_dirichlet 단독으로는 해결 불가. 근본적 접근 필요.

---

## Phase 0: V_mag 과대추정 근본 해결

### 논문 분석 결과 (2026-06-13 확정)

Morisco PhD thesis Chapter 5 "Beschreibung des Berechnungsprogrammes ELMO" 전문 검토 결과:
- **V_leak subtraction**: 논문에 없음
- **(μr-1)·H_leak**: 논문에 없음 (M을 직접 사용, eq.4.52)
- **PM/Load 분리**: 논문에 없음 (combined FEM 1회)

Morisco의 과대추정 해결 전략: **없음** (1-4% 수준이라 무시)

### 우리의 과대추정 원인 재분석

Morisco의 IPM traction drive 예제(§6.4):
- 결과: BP1 k_ih=1.37, BP2 k_ih=3.57 (PEEC) vs FEA reference 1.35, 3.62 → **오차 -1.3~-1.4%**
- 즉, Morisco의 구현에서는 PEEC가 **정확**함

우리 구현에서만 39x 과대 → **구현 오류 가능성**:

1. **R_dirichlet 설정 오류?**
   - Morisco: R = l (axial length) = 100mm (그의 모터)
   - 우리: R = l = 150mm → 이것은 맞지만, slot 크기 대비 비율이 다를 수 있음
   - Morisco 모터: 1mm×1mm conductor in 100mm length → slot ≪ R
   - 우리 모터: 7.4mm×1.2mm hairpin → slot geometry 고려 필요?

2. **L_mutual 계산 검증 필요**
   - Morisco eq.3.166: G(ξ,ξ') with normalized coordinates ξ = r/R
   - 현재 구현에서 ξ normalization이 올바른지 확인

3. **i_mag 크기 검증**
   - Morisco Fig.5.12: boundary에서 |i_mag| 분포 예시
   - 우리의 i_mag_timeseries와 스케일 비교

### 해결 전략 (우선순위)

1. **[우선] L_mutual 수식 검증**: Morisco eq.3.166과 코드의 정합성 라인별 대조
2. **[우선] i_mag 크기 단위계 확인**: [A/m]→[A] 변환이 올바른지
3. **[탐색] R_dirichlet**: 논문의 Fig.5.13 예시에서 R vs slot size 비율 확인
4. **[보류] Iterative correction**: 논문에 없으므로 당분간 보류

### 검증 기준
- 목표: 보정 없이 k_ih ∈ [4.0, 10.0] (FEA 6.06 기준 ±65%)
- Morisco 수준: PEEC ≈ FEA ±5% (이상적)

---

## Phase 1: Volpe Hybrid 재현 + Motor-CAD Hybrid 검증 (기준선 확립)

**목적**: Motor-CAD Hybrid 내부 알고리즘을 Python으로 재현하여 기준선 확보

| Step | 내용 | 도구 |
|------|------|------|
| 1-1 | Motor-CAD simple FEA 실행 (σ=0 empty-slot) → 층별 B 추출 | pymotorcad API |
| 1-2 | 추출 B를 Volpe proximity 식에 대입: $P_{prox} = L_a \frac{w_r h_r^3 \sigma (\omega B)^2}{24}$ | Python |
| 1-3 | Skin effect 별도 계산 (Dowell kR 또는 Motor-CAD 내부 로직 역공학) | Python |
| 1-4 | Inductance-limited 스케일링 적용 (ξ > 1 영역) | Motor-CAD 내부 로직 역공학 |
| 1-5 | Motor-CAD Hybrid 결과(.mat)와 ±5% 이내 일치 확인 | MAT 파일 대조 |
| 1-6 | 다중 전류 레벨 (50A, 100A, 200A) 오차 경향 분석 | 논문 Fig.3~5 재현 |

### Key Formula (Volpe 2019 — proximity only)

$$P_{prox} = L_a \frac{w_r h_r^3 \sigma (\omega B)^2}{24}$$

Where B is obtained from **simple FEA** (σ=0, empty-slot) at each conductor layer position.  
Skin effect is handled separately by Motor-CAD via kR scaling on the DC resistance.

---

## Phase 2: El Hajji 2D Hybrid 후처리

**목적**: Motor-CAD Hybrid가 실제로 어떤 B-field을 사용하는지 역추적 + 고조파별 기여도 분해

| Step | 내용 | 도구 |
|------|------|------|
| 2-1 | `backup_fea_result`로 저장된 `.mes` 파일 로드 | `eMach/tools/motorCAD/pyMCAD/magnetic_model.py` |
| 2-2 | 도체 RegCode 식별 → 도체 요소만 필터링 | `.mes` 파서의 `reg_code` 필드 |
| 2-3 | 도체 centroid에서 (Bx, By) → (Br, Bθ) 좌표 변환 | numpy 극좌표 변환 |
| 2-4 | 시간 스텝별 B(t) 구성 → FFT 고조파 분해 | numpy.fft |
| 2-5 | El Hajji 식 적용 (rectangular): $$P = \sigma l \omega_i^2 B_{r_i}^2 \cdot \frac{bh^3}{24} + \sigma l \omega_i^2 B_{\theta_i}^2 \cdot \frac{b^3 h}{24}$$ | Python |
| 2-6 | Motor-CAD Hybrid 결과와 비교 | MAT 파일 대조 |
| 2-7 | **No-Load FEA i_mag 추출** (Phase 0-A용) | Motor-CAD API `set_array_variable("ConductorCurrent", [0]*6)` |

**선행 확인 사항**: Hybrid FEA backup에 시간 스텝별 .mes가 있는지? (없으면 Motor-CAD API로 B(t) 직접 추출)

### Key Formula (El Hajji eq.12 — rectangular adaptation)

$$P_{prox} = \sum_{i=1}^{N} \left(\frac{\sigma l \omega_i^2 B_{r_{i,m}}^2 \cdot b h^3}{24} + \frac{\sigma l \omega_i^2 B_{\theta_{i,m}}^2 \cdot b^3 h}{24}\right)$$

Where:
- $b$: conductor tangential width [m]
- $h$: conductor radial height [m]  
- $\sigma$: Cu conductivity [S/m]
- $l$: active length [m]
- $\omega_i = 2\pi f_i$: angular frequency of i-th harmonic
- $B_{r_{i,m}}, B_{\theta_{i,m}}$: amplitude of i-th harmonic (radial/tangential)

---

## Phase 3: Maxwell 2D μ_eff Enhanced Hybrid

**목적**: 와전류 back-reaction에 의한 자속 재분포를 반영하여 TS와의 갭을 축소

| Step | 내용 | 도구 |
|------|------|------|
| 3-1 | 속도별 ξ = h/δ 계산 | Python |
| 3-2 | μ_eff 계산 | Python |
| 3-3 | Maxwell 2D 새 design 복제, conductor σ=0 + μ_r=\|μ_eff\|/μ₀ 할당 | pyAEDT |
| 3-4 | Transient 해석 → 도체 centroid B(t) 추출 | pyAEDT post |
| 3-5 | El Hajji + G_rect(ξ) correction 적용 | Python |
| 3-6 | TS 대비 정확도 평가 → 갭 축소량 정량화 | Plot |

### μ_eff Formula

$$\mu_{eff}(f) = \mu_0 \cdot \text{Re}\left[\frac{\tanh\left(\frac{(1+j)\xi}{2}\right)}{\frac{(1+j)\xi}{2}}\right]$$

Where $\xi = h / \delta$, $\delta = 1/\sqrt{\pi f \mu_0 \sigma}$

### G_rect Correction (Ferreira)

$$G_{rect}(\xi) = \xi \cdot \frac{\sinh\xi + \sin\xi}{\cosh\xi + \cos\xi}$$

**핵심**: $\sigma=0$으로 설정(또는 MQS 해석)한 상태에서 권선 도메인의 투자율 $\mu_r$을 $\mu_{eff}$ 수치로 감축시키면, FEA 실시간 와전류 메싱 없이도 자속이 도체를 피해 슬롯 외부로 밀려나는 **와전류 반작용(Back-reaction) 현상을 수치적으로 모사**할 수 있습니다.

> [!NOTE]  
> **이론적 혼동 주의: 복소 투자율법(μ_eff) vs. 동결 투자율법(FCP)**
> * **복소 투자율법 ($\mu_{eff}$)**: **구리 권선**에 적용되며, 고주파 전류로 유도되는 도선 내부의 자계 차폐(Shielding) 효과를 묘사하기 위해 구리 도선의 상대 투자율을 $1.0$ 미만의 복소수($\mu = \mu_0(\mu_{rr} + j\mu_{ri})$)로 낮추는 기법입니다.
> * **동결 투자율법 (FCP)**: **철심(Steel Core)**에 적용되며, 비선형 자기 포화 상태를 동결하여 포화 효과가 반영된 상태로 PM 자속 기여분과 전기자 전류 자속 기여분을 공간상에서 선형 분리/중첩하는 기법입니다.

---

## Phase 4: Morisco PEEC 완전 구현 — Double-Counting 해결 및 해석 모델 비교

**목적**: 학위논문 10-Step을 정확히 따라 α calibration 없이 k_ih ≈ 6.06 달성 및 Ju 1D Hybrid와의 교차 검증

### 4A: Morisco FEA-PEEC 디버깅 & 검증 (D)

| Step | 내용 | 도구 | 상태 |
|------|------|------|------|
| 4A-1 | e10 모터 파라미터 추출 (Motor-CAD API) | pymotorcad | ✅ |
| 4A-2 | No-load FEA → i_mag_PM(t) 분리 (Phase 0-A) | Motor-CAD API | ❌ |
| 4A-3 | 개선된 Regression (Phase 0-B) | numpy | ⚠️ (+45%) |
| 4A-4 | V_leak 정밀 계산 (1D Ampere → μ_r 반영) | Python | ❌ |
| 4A-5 | PEEC solve with corrected V_mag | solver.py | 대기중 |
| 4A-6 | k_ih 검증 vs FullFEA | compare | |

#### 학위논문 vs 현재 구현 GAP 분석

| 논문 Step | 학위논문 방식 | 현재 구현 (Method34) | GAP |
|-----------|-------------|-----------|-----|
| Static FEM | JMAG, uniform J, 1 period | Motor-CAD Hybrid, ✓ | OK |
| M 추출 | element-wise M from FEM | bx/by → M = B/μ₀ - H | OK |
| K_mag (eq.4.52) | (M_ν-M_ξ)×n_θ / μ₀ | boundary_cache 구현 | OK |
| i_mag (eq.4.53) | K_mag × \|w_θ\| | edge_lengths_filt | OK |
| FFT (eq.4.83) | DFT of i_mag(t) | rfft, DC 제거, 14 harmonics | OK |
| Z matrix | Dirichlet BVP (circular), R=l | Dirichlet circular, R=128.2mm | **OK** |
| L_ΓV (커플링) | Dirichlet circular (Z와 동일 G.F.) | **L_ext: Rectangular Image** (다른 G.F.!) | **불일치** |
| L 소스 확장 | slot-wall edges only | slot-wall + **tooth-tip** (80→143) | Method 3 개선 |
| Region weight | 없음 (균일) | w_ag / w_tw / w_yk (Method 4) | Method 4 개선 |
| PEEC solve | $i = Z^{-1}C(C^TZ^{-1}C)^{-1}I$ | ✓ constraint-projected | OK |
| 결과 | k_ih=1.37 (FEA=1.35, -1.4%) | k_ih=615~4761 (과대) | **~100x 과대** |
| R_dirichlet | R=l=100mm (자신의 모터) | R=128.2mm (slot outer+margin) | 비율 검증 |
| Overestimation | 인정하되 무시 (1-4%) | ~100x → **이중계수 확정** (EXP-1~3) | **핵심 이슈 — 원인 확정** |
| **§4.8 Rotor iron** | **로터 철심 자화전류 포함** (source mesh→target mesh 변환) | **스테이터 경계만** 자화소스 | **미구현** |
| **§4.9 Symmetry** | **L_total,sym = Σ k_sym·L_{k-1}** (인접 슬롯 coupling) | **1 slot only** (TARGET_SLOT=0) | **미구현** |
| **Double-counting** | **σ=0 FEM** (도체 와전류 미포함 → PM-only i_mag) | **Hybrid FEA** (도체전류 leakage 포함) | **★ 근본 원인** |

> ⚠️ **GAP 핵심 (2026-06-18 확정)**: ~~Z/L_ext Green's function 불일치가 원인~~ → **EXP-1에서 기각** (L_mutual circular 사용 시 k_ih 악화).
> **진짜 원인**: Motor-CAD Hybrid FEA의 B/H에 도체전류 leakage flux가 포함 → i_mag에 PM+leakage 혼합 → Z matrix leakage와 이중계수.
> **해결**: No-Load FEA (I=0) 또는 time-domain regression으로 PM-only i_mag 분리.

#### 핵심 실험 계획 및 결과 (2026-06-18 완료)

```
실험 1 (EXP-1): Green's Function 일관성 검증 → ❌ 원인 아님
  - L_mutual(circular) 사용: k_ih = 1424 (Method34=615보다 악화!)
  - L_mutual이 L_ext보다 11x 큼 → circular G.F.가 V_mag을 더 증폭
  - 결론: G.F. 불일치는 오히려 k_ih를 낮추는 방향으로 작용

실험 2 (EXP-2): i_mag 크기 검증 → ❌ 코드 버그 아님
  - i_mag 기본파 max = 944 A (Morisco: 0.6 A)
  - |M| = 1.3e6 A/m (1.9T 포화 철심 → 물리적 정상)
  - 차이 원인: 우리 edge=0.5mm vs Morisco edge=0.1mm → 스케일 차이
  - 1/μ₀ factor: 적용하면 더 커짐 → NOT the fix

실험 3: i_mag 크기 검증
  - Morisco Fig.5.12 예시: |i_mag| distribution at boundaries
  - 우리의 i_mag_timeseries RMS와 스케일 대조
  - K_tang 계산에서 μ₀ division 확인 (eq.4.52에 1/μ₀ 있음)
  - tooth-tip 확장(143 sources)이 i_mag 총 크기에 미치는 영향

실험 4: R_dirichlet 물리적 결정 + 비율 비교
  - Morisco: R=l for axial-infinite conductor approximation
  - 그의 모터: slot width ≈ 1mm, R=100mm → R/slot=100
  - 우리 모터: slot width ≈ 7.4mm, R=128.2mm → R/slot≈17
  - 비율이 다르면 image term 영향이 다름
  - Z matrix의 R과 L_ext의 boundary geometry 일치 필요성 검토

실험 5: Morisco §6.4와 동일 조건 재현
  - 가능하면 단순한 single conductor model로 먼저 검증
  - k_ih ≈ 1.26 (PEEC=FEA) 재현 후 IPM으로 확장
  - Z와 L 모두 동일 circular boundary로 계산하는 "pure Morisco" 재현

실험 6: §4.8 로터 철심 자화소스 추가 (EXP-1~5 해결 후)
  - Motor-CAD FEA mesh에서 rotor iron region 분리
  - 로터-스테이터 airgap boundary edge 추출
  - Rotor i_mag 계산: 동일 eq.4.52-4.53 적용
  - L_ΓV,rot (filament↔rotor_boundary) 계산
  - V_mag += jω·L_rot·i_mag_rotor → PEEC resolve
  - 목표: C1(airgap-side) proximity 정밀도 개선
  - ★ 선결: EXP-1~5로 k_ih가 합리적 범위 진입 후 수행

실험 7: §4.9 대칭성 확장 (인접 슬롯 커플링)
  - 8P/48S antiperiodic: n_sym=6, slot pitch=7.5°
  - L_total,sym = L_self + Σ k_sym·L_k-1 (k_sym=(-1)^{k+1})
  - 인접 슬롯 도체 위치: rotation by 7.5°×k
  - 인접 슬롯 iron boundary도 source에 추가
  - 목표: C1/C6 gradient 개선 (현 FEA target C1/C6≈2.1x)
  - ★ 선결: single-slot k_ih가 ±50% 내 진입

실험 8: 통합 검증 (Pure Morisco + §4.8 + §4.9)
  - 모든 fix 적용 후 최종 k_ih 검증
  - 목표: k_ih ≈ 6.06 ±10% (Morisco 수준)
  - 6-layer별 loss distribution vs FEA 대조
  - 속도별 k_ih(RPM) 추이 vs FEA reference curve
```

### 4B: Ju 1D Hybrid Dowell+Popescu (E)

| Step | 내용 | 도구 | 상태 |
|------|------|------|------|
| 4B-1 | Dowell kR 층별 계산 (M(ξ) + Q(ξ) 함수) | ju_hybrid_acloss.py | ✅ |
| 4B-2 | B-field 소스: 해석 Ampere 모델 (Phase 1 FEA 결과도 가능) | analytical_slot_B() | ✅ |
| 4B-3 | PWM 고조파 중첩 (Popescu superposition) | WindingCurrentSpec.with_pwm_harmonics() | ✅ |
| 4B-4 | `calculate_acloss_ju()` 4속도점 실행 | ju_hybrid_acloss.py | ✅ |
| 4B-5 | Skin vs Proximity 분리 비교 | 층별 분해 plot | ✅ |

### 4C: Steady-State Calibration 및 정현파 대조군 검증

**목적**: 시간 영역 과도 시뮬레이션(ECMC)과 동일한 전압 RMS, 전류 RMS, 종합 역률을 대수적으로 고속 계산(Parseval 정리 강제)하고, 이를 정현파 입력 조건에서 사전 검증

| Step | 내용 | 도구 | 상태 |
|------|------|------|------|
| 4C-1 | **정현파 기본파 매칭(Sinusoidal Match)**: PWM 오프 상태의 이상적 정현파 입력 하에 시간 영역과 정적 전압/출력/손실 매칭 | Python/ECMC | 계획중 |
| 4C-2 | Cauer 복소 임피던스 $Z_{Cauer}(j\omega_e)$ 및 기본파 철손 저항 $R_{i,1}$의 저주파 임피던스/위상 캘리브레이션 | Python | 계획중 |
| 4C-3 | **해석적 PWM 이중 푸리에 스펙트럼 생성**: 스위칭 주파수 $f_c$ 및 변조 지수 $m_a$에 기반한 전압 고조파 $V_n$ 연산 모듈 | Python | 계획중 |
| 4C-4 | 복소 임피던스 수식 $Z_{input}(j\omega_n)$을 통한 캐리어 전류 리플 $I_n$ 고속 산출 | Python | 계획중 |
| 4C-5 | **Parseval 정리 기반 단자 보정**: 전력 평형 및 $V_{rms, total}$, $I_{rms, total}$, 종합 역률 $\cos\phi_{total}$ 강제 매칭 | Python | 계획중 |
| 4C-6 | 효율맵 전압 제한 조건 개정: $V_{rms, total} \le V_{limit}$ 적용에 따른 약자속 운전 영역 재평가 | Python | 계획중 |

---

## Phase 5: Cauer Ladder Circuit 모델 평가

**목적**: 회로 등가 모델의 Fr=Rac/Rdc 예측이 필드 기반 방법들과 정합하는지 검증 + 시스템 시뮬레이션 연계 가능성 확인

**구현 노트북**: `cauer_modeling_example.ipynb`  
**구현 모듈**: `cauer_modeling.py`

### 방법론 원리

Cauer 래더는 도체를 **다단 R-L 직병렬 네트워크**로 분해하여 주파수 의존 임피던스를 직접 계산:

```
──[ R₁ ]──┬──[ R₂ ]──┬──[ R₃ ]──┬── ···
           │          │          │
          (L₁)       (L₂)       (L₃)
           │          │          │
 ───────────┴──────────┴──────────┴── ···
```

$$Z_{in}(f) = R_1 + \frac{j\omega L_1 \cdot (R_2 + Z_{rest})}{j\omega L_1 + R_2 + Z_{rest}}$$

$$F_r(f) = \frac{\text{Re}[Z_{in}(f)]}{R_{dc}}$$

### Cauer 파라미터 공식

$$L_k = \frac{\mu_0 \cdot d \cdot l_{core}}{w_{slot} \cdot (4k-3)}, \quad R_k = \frac{(4k-1) \cdot 8 \cdot l_{core}}{\sigma \cdot d \cdot w_{slot}}$$

### 실행 계획

| Step | 내용 | 도구 |
|------|------|------|
| 5-1 | e10 파라미터로 Cauer 파라미터 계산 (5-stage) | cauer_modeling.py |
| 5-2 | 주파수 응답 Fr(f) 계산 (0~5 kHz) | analyze_frequency_response() |
| 5-3 | Phase 4의 kR(f)와 동일 주파수 축에서 비교 | matplotlib overlay |
| 5-4 | 단수(stages) 수렴성 분석: 3단/5단/7단/10단 | 파라미터 스윕 |
| 5-5 | Multi-turn 확장: 층간 coupling 효과 반영 여부 검토 | 논문 대조 |
| 5-6 | Drive-level 시뮬레이션 연계: Z(f) → inverter+motor 연성 | (향후 과제) |

### Cauer vs 기타 방법 비교 포인트

| 비교 항목 | Cauer (F) | Volpe (A) | Ju (E) | Morisco (D) |
|-----------|-----------|-----------|--------|-------------|
| 입력 | 기하 치수 + σ만 | + B from FEA 필수 | + B (FEA or 해석) | + Rotor 고조파 |
| 출력 | Fr (스칼라) | P_prox [W] + P_skin별도 | P_skin + P_prox 분리 | P_slot + P_rotor 분리 |
| 근접 효과 | 암묵적 (회로 내재) | 명시적 (Volpe식 전용) | 명시적 Q(ξ) | 명시적 PEEC |
| PWM 고조파 | Z(f) 임의 파형 | ❌ 미지원 | ✅ Popescu 중첩 | 확장 가능 |
| 고주파 보정 | 자동 (래더 수렴) | Inductance-limited | F_prox(ξ) Dowell | ξ별 보정 |
| 열모델 연계 | 동일 래더 구조 | 별도 필요 | 별도 필요 | 별도 필요 |
| 시스템 시뮬 | SPICE/Simulink 가능 | Motor-CAD 전용 | 후처리 전용 | 후처리 전용 |

---

## Phase 6: 통합 비교 및 RBF 대리 모델 수립

**목적**: 6가지 방법 + Motor-CAD TS 기준값을 정량 비교하고, RBF 기반 3차원/차원분리형 대리 모델 검증

| Step | 내용 |
|------|------|
| 6-1 | 4속도점 × 3스케일링 × 6방법 결과 통합 DataFrame 구성 |
| 6-2 | Overlay plot: P_AC vs Speed (6-method + TS baseline) |
| 6-3 | 오차 히트맵: 각 방법의 TS 대비 오차율 (%) |
| 6-4 | 계산 비용 비교: FEA 시간 vs 해석 시간 정리 |
| 6-5 | 최종 추천 매트릭스: 정확도/속도/구현난이도 기준 방법 선택 가이드 |
| 6-6 | Volpe vs Ju 상세 비교: 동일 B-field 입력 시 결과 차이 원인 분석 |

### RBF & Polynomial Surrogate Model Convergence Study (대리 모델 수렴성 검토)

우리는 기존의 106개 FullFEA 데이터셋(2k/4k/16k RPM의 90개 포인트 + 8k RPM의 16개 포인트)을 활용하여, 무작위 서브샘플링 교차검증(100회 Monte Carlo Cross-Validation) 및 Leave-One-Out Cross-Validation (LOOCV)을 수행하고 각 커널별 샘플 수($N$)에 따른 예측 정확도 수렴성과 글로벌 RBF 커널의 타당성을 검증했습니다.

#### 1. 커널별 예측 성능 및 수렴도 비교 (Monte Carlo Test MAE)

| 샘플 수 ($N$) | Gaussian (Local) | Linear (Global) | TPS (Global) | Cubic (Global) |
|:---:|:---:|:---:|:---:|:---:|
| 20 | 39.67% | 24.66% | 24.93% | 25.52% |
| 30 | 31.84% | 20.97% | 17.97% | 16.98% |
| 40 | 25.54% | 18.25% | 14.19% | 12.41% |
| 50 | 20.29% | 15.87% | 11.12% | 9.17% |
| 70 | 13.33% | 12.53% | 7.95% | 5.87% |
| 90 | 7.31% | 10.41% | 6.22% | 4.23% |

#### 2. 전체 데이터셋(106 Points) 기준 LOOCV (Leave-One-Out Cross-Validation) 오차

전체 106개 데이터 포인트를 센터로 사용하는 완전 보정(Full Interpolation) 모델에 대한 LOOCV 검증 결과입니다:
- **Gaussian (Local)**: Train MAE $pprox$ 0.00%, LOOCV MAE = **3.51%**
- **Linear (Global)**: Train MAE $pprox$ 0.00%, LOOCV MAE = **9.27%**
- **Thin-Plate Spline (TPS, Global)**: Train MAE $pprox$ 0.00%, LOOCV MAE = **4.95%**
- **Cubic (Global)**: Train MAE $pprox$ 0.00%, LOOCV MAE = **3.12%**

> [!NOTE]
> 글로벌 RBF 커널인 Thin-Plate Spline(TPS) 및 Cubic 커널은 데이터가 성긴(Sparse) 영역에서도 0으로 감쇠하지 않고 공간을 안정적으로 보간하므로, 적은 샘플 수($N=30\sim50$)에서도 가우시안 커널 대비 오차를 절반 이하로 줄일 수 있음을 확인했습니다.

#### 3. 글로벌 RBF 커널 도입 및 Truncation 제약사항 해결

글로벌 RBF 커널을 도입하면서 발생한 두 가지 주요 과제와 해결 방식입니다:

1. **단순 가중치 절단(Truncation) 시의 경계 발산**:
   - 가우시안 RBF는 국부 커널이므로 영향력이 작은 센터의 가중치를 버려도(Top 20 추출) 안정적이지만, 글로벌 RBF(TPS, Linear, Cubic)는 모든 센터 가중치 간의 상쇄 효과에 의존해 보간면을 생성합니다.
   - 전체 106개 포인트 피팅 모델에서 단순히 $|w|$ 상위 20개 항만 추출해 수식화하면, **경계 영역에서 극심한 보간 함수 발산(MAE > 1000%)**이 일어납니다.
2. **해결책: Farthest Point Sampling (FPS) 기반 최소자승 피팅**:
   - 수식 길이 제한(Motor-CAD Lab GUI 수식 입력 제한)을 충족하면서도 정확도와 안전성을 유지하기 위해, 입력 공간(Speed, Irms, Phase)에서 점들 간 거리를 극대화하는 **Farthest Point Sampling (FPS)** 방식을 통해 대표 센터 30개를Deterministic하게 추출했습니다.
   - 이 30개 대표 센터를 기저로 삼고 전체 106개 데이터셋에 대해 최소자승법(Least-Squares Fit, `lstsq`)으로 가중치를 재학습하여 **30-Term 축소형 글로벌 RBF 모델**을 빌드했습니다.
   - 이 모델은 가중치 절단으로 인한 발산 없이 전체 영역에서 안정적으로 거동하며, **10.19% MAE (TPS)**의 우수한 정확도를 제공합니다.
3. **최종 산출 및 JSON 내보내기**:
   - 노트북 및 JSON 모델 내보내기 시, 다음 두 가지 수식을 모두 저장하여 사용자의 필요에 맞춰 유연하게 선택할 수 있게 했습니다:
     - `mcad_formula_full` (106개 전체 센터, LOOCV 4.95% 초고정밀, 식 길이 ~28k)
     - `mcad_formula_reduced_30` (30개 FPS 센터, MAE 10.19% 축소형, 식 길이 ~8k)

#### 4. 1D x 2D 차원 분리형 스케일링 모델 (Separable Scaling Model)

12~16개의 극소수 신규 FullFEA 해석점만으로 오차 상승 없이 성공적인 보정을 수행할 수 있도록 **1D x 2D 차원 분리형 스케일링 모델**을 구축하고 검증했습니다:
- **수식 구조**: $AF(speed, Irms, phase) = f(speed) \times g(Irms, phase)$
- **베이스 2D 형상 $g(I, \theta)$**: 단일 속도인 2.0 kRPM의 모든 격자 데이터(30점)를 활용해 2D Thin-Plate Spline (TPS) RBF로 형상을 완벽히 모델링합니다 (Base MAE = 0.00%).
- **1D 속도 배율 $f(speed)$**: 속도가 올라감에 따라 나타나는 AC 와전류 포화 특성(와전류 반작용)을 보정하는 1차원 배율 함수입니다.
  - 4k, 8k, 16k RPM of 3개 속도점에 대해 속도당 단 4개 대표 전류값(115A, 230A, 345A, 460A) 총 12점의 FullFEA를 사용해 측정된 배율을 평균화합니다.
  - 2.0 kRPM에서의 약속값 $f(2.0) = 1.0$ 제약조건을 포함한 총 4개 속도 좌표에 대해 2차 다항식을 피팅하여 연속 함수를 수립합니다:
    $$f(speed) = 0.002081 \cdot \left(\frac{Speed}{1000}\right)^2 - 0.066949 \cdot \left(\frac{Speed}{1000}\right) + 1.122778$$
- **검증 결과 및 비교**:
  - **3D TPS RBF**: Train MAE = 0.00%, MaxAE = 0.00%, LOOCV MAE = **4.95%** (106점 전체 사용)
  - **Separable (분리형 RBF)**: Train MAE = **5.02%**, MaxAE = **40.69%**, LOOCV MAE = **8.49%** (2.0 kRPM 30점 base + 타 속도 영역 12점 대표점 calibration)
- **Motor-CAD Lab 수식 크기**:
  - 1D 속도 2차 다항식 식과 2D RBF의 곱으로 표현되며, 전체 식 길이는 **약 5.5k 캐릭터**로 매우 슬림하고 강건합니다.

---

## Execution Priority & Parallel Workflows (병렬 실행 아키텍처)

본 프로젝트의 Phase들은 서로 완전히 종속된 직렬 구조가 아니며, **세 개의 독립적인 병렬 작업 스트림(Decoupled Parallel Streams)**으로 나누어 효율적으로 추진할 수 있습니다. 

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    3개 병렬 작업 스트림 (Decoupled Streams)                 │
└────────────────────────────────────────────────────────────────────────────┘
     │
     ├─► [Stream A: 전자기 필드 해석 검증] ──────────────────► (Phase 1, Phase 2)
     │   • 도체 Centroid 자속 밀도 시계열을 바탕으로 한 포스트프로세싱 검증
     │   • 툴: Motor-CAD FEA Backup 파싱 + Maxwell μ_eff 해석 (pyAEDT)
     │   • 특징: PEEC 회로 구성 없이 필드(Mesh) 데이터를 직접 다룸
     │
     ├─► [Stream B: 제어-회로 단자 정합 프레임워크] ─────────► (Phase 4)
     │   • 정현파 기본파 검증(Sinusoidal Match) 및 Parseval 정리 강제 루프 구축
     │   • 툴: Python 등가회로 스윕 코딩, PWM 전압 고조파 해석식 구현
     │   • 특징: 손실 모듈의 종류(PEEC, El Hajji 등)에 무관하게 작동하는 
     │           '단자 보정 아우터 프레임워크'로, 먼저 임의 데이터로 빌드 가능
     │
     └─► [Stream C: PEEC 솔버 개선 및 버그 수정] ──────────► (Phase 0, Phase 3)
         • Morisco PEEC의 100배 과대추정 원인 해결 및 No-load PM-only i_mag 분리
         • 툴: `solver.py`, `magnetization.py` 디버깅
         • 특징: 순수 필드-회로 커플링 코드의 수치해석적 정밀도 개선 작업
```

### 병렬 실행 우선순위 (Execution Priority)

1. **Phase 1 먼저** (Volpe 기준선 확립 — Motor-CAD API 접근 필요, `volpe_hybrid_acloss.py` 구현)
2. **Phase 4A+4B 동시** (morisco_acloss.py + ju_hybrid_acloss.py 이미 완성, 노트북 실행만)
3. **Phase 5 동시** (cauer_modeling.py 이미 완성, Phase 4 결과와 비교)
4. **Phase 2 다음** (.mes 데이터 이미 존재, El Hajji 파싱 구현)
5. **Phase 6 수시** (Phase 1+4+5 완료 후 1차 통합, Phase 2 추가 후 2차 통합)
6. **Phase 3 마지막** (Maxwell 2D 해석 필요, 시간 소요)

---

## Appendix: 학위논문 vs 저널논문 vs 구현 코드 대조표

| 항목 | 학위논문 (2020 PhD) | 저널 (ICEM 2019/ECCE 2020) | morisco_acloss.py | Method34 notebook |
|------|-------|--------|---------|---------|
| 도체 분할 | n_x×n_y filaments, a≤0.1δ | 동일 | **없음** (layer 단위) | ✅ 12×26 |
| Green function (Z) | Dirichlet circular (R=l) | 동일 | **없음** | ✅ Circular (R=128.2mm) |
| Green function (L_ΓV) | Dirichlet circular (동일) | 동일 | **없음** | ⚠️ **Rectangular Image** |
| V_mag | L_mutual × i_mag | 동일 | **없음** (해석식 직접) | ✅ L_ext × I_mag_fft |
| Tooth-tip source | 없음 | 없음 | 없음 | ✅ Method 3 (80→143 sources) |
| Region weight | 없음 | 없음 | 없음 | ✅ Method 4 (w_ag/w_tw/w_yk) |
| V_leak 제거 | 명시 (Step 7) | 언급만 | 해당 없음 | ❌ 미구현 |
| Source 분리 | PM-only FEA 가능 | 암시 | P_slot + P_rotor 분리 | ❌ 혼합 |
| FFT 확장 | ECCE 2020 | ECCE 2020 | 없음 | ✅ 14 harmonics |
| Dowell correction | 불필요 (PEEC 자동) | 불필요 | F_prox(ξ) 사용 | 불필요 |
| Rotor influence | i_mag에 자연 포함 | 동일 | 별도 B_rotor 입력 | ✅ |
| 결과 (OP2) | k_ih=2.31 (200kW ref) | 동일 | 스케일링 모델 | k_ih=237→6.06(α) |

### 참고 논문 (ACloss_Ref/ACloss/)

| 논문 | 방법 연관 |
|------|-----------|
| `2019_volpe_AC Winding Losses...` | Phase 1 (Volpe) |
| `El-Hajji_ICEM2020Hybrid model...` | Phase 2 (El Hajji) |
| `2020_morisco_Extended_Modelling_Approach_...` | Phase 4A (Morisco) |
| `A Hybrid Analytical and FE-Based Method...` (Ju) | Phase 4B (Ju) |
| `2019_Popescu_AC Winding Losses...` | Phase 4B (Ju + PWM) |
| `Investigation_on_Behavior_Model_of_PMSMs_Considering_AC_Copper_Losses_with_Cauer_Circuit.pdf` | Phase 5 |
| `Reduced_Order_Modeling_Based_on_Multiport_Cauer_Ladder_Network...` | Phase 5 (확장) |
| `Dynamic_Hysteresis_Modeling_...Cauers_Equivalent_Circuit_Theory.pdf` | Phase 5 (열모델 연계) |
