# 1D/2D Hybrid AC Loss — MATLAB→Python 포팅 요약

작성: 2026-07-14 | 산출물: [`ac_loss_hybrid.py`](ac_loss_hybrid.py), [`test_ac_loss_hybrid.py`](test_ac_loss_hybrid.py)

## 1. 개요

Motor-CAD Hybrid 방식(skin effect = 1D 해석식, proximity effect = 2D FEA 자속밀도 기반)의
AC 동손 계산을 기존 eMach MATLAB 코드에서 Python으로 이식했다.
검증은 (a) MATLAB 수식 1:1 대조, (b) 논문 원전(Volpe/Popescu 2019) 수식 대조,
(c) 해석적 항등성 기반 단위 테스트 25종으로 수행했다 (전부 통과).

```
python mlxperPJT/JEET/test_ac_loss_hybrid.py   # 25/25 passed
python mlxperPJT/JEET/ac_loss_hybrid.py        # 데모 스윕
```

## 2. MATLAB ↔ Python ↔ 논문 대응표

| 물리량 | MATLAB 원본 | Python (`ac_loss_hybrid.py`) | 논문 근거 |
|---|---|---|---|
| skin depth δ=√(2/(ωμ₀σ)) | `tools/loss/ACLOSS/calcSkinDepth.m` (**mm 반환**) | `calc_skin_depth()` (**m 반환**) | 교과서; Taha2020 eq.6 |
| 보정 skin depth δ′=δ·√((d1+d2)/(2d2)) | `skin/calcSkinDepthModi.m` | `calc_skin_depth_modified()` | Morisco 2019 (사각도체 이방성) |
| γ = dim/δ | `AnaProx/calcNonDimParaGamma.m` | `calc_gamma()` | — |
| 하이퍼볼릭 커널 | `eqHyperbolic.m` | `eq_hyperbolic()` (급수/점근 가드 추가) | Field/Emde 고전식 |
| skin factor φ(ξ)=ξ·(sinh2ξ+sin2ξ)/(cosh2ξ−cos2ξ) | `calcSkinEffFun.m` | `skin_effect_factor()` | Pyrhönen §5.2 (k_R) |
| proximity factor ψ(ξ) | `calcProxyEffFun.m` | `proximity_effect_factor()` | 동일 |
| g1 = γ_w·γ_h³/(6π²μ²σ) | `AnaProx/calcProxg1.m` | `prox_coeff_g1()` | (원 논문 정규화, §4 주의) |
| g2 = (γ_w/(σμ²))·(sinh γ_h−sin γ_h)/(cosh γ_h+cos γ_h) | `AnaProx/calcProxg2.m` | `prox_coeff_g2()` | Morisco 2019 광대역식 |
| 2D 계수쌍 (radial, theta) | `AnaProx/calcProx2DG2Prime.m` | `calc_prox_2d_g2_prime()` | — |
| 2D 결합 P=L[g2(γw′,γh′)Br²+g2(γh′,γw′)Bθ²] | `calcHybridACLossWave.m:60-64` | `calc_proximity_effect_2D()` | — |
| MCAD 1D 사각 P=L·w·h³σ(ωB)²/**24** | `MCAD/calcHybridProx1DMCAD.m:13`, `MCAD/devCalcMCADHybridACLoss.m:137-139` | `calc_hybrid_ac_loss_1D()`, `method='mcad24'` | **Volpe 2019 eq.(2)** ✔ |
| MCAD 1D 원형 P=L·πd⁴σ(ωB)²/**128** | `devCalcMCADHybridACLoss.m:129` (주석) | `shape='round'` 분기 | **Volpe 2019 eq.(1)** ✔ |
| 하모닉 로지스틱 블렌드 + HF gain | `Calc/calcACLossHybridFromPDF.m:74-88` | `_pdf_blend_factor()`, `apply_pdf_blend=True` | Volpe 2019 §III.C 서술* |
| 메시 txt 파싱 | `Calc/loadMESviaPythonForMATLAB.m` (Python 브리지) | `parse_magnetic_snapshot/timeseries()` — `tools/motorCAD/pyMCAD/magnetic_parse.py` **재사용** | — |

\* Volpe 2019: "The proposed hybrid FEA method detects the frequency at which the eddy
currents become inductance limited and adjusts the scaling of the AC losses with frequency."
→ `calcACLossHybridFromPDF.m`의 전이주파수 f_T = 2/(2πμ₀μ_rσh²) + 로지스틱 블렌드가 이 서술의 구현.

## 3. 논문 수식 검증 결과 (Step 4)

### 3.1 /24, /128 계수 — MATLAB과 논문 **일치** ✔

Volpe/Popescu 2019 (Motor-CAD Hybrid 원전) eq.(1),(2):

- 원형: P = ℓ·π·h_c⁴·σ·(ωB)²/128 (h_c = 지름)
- 사각: P = ℓ·w_r·h_r³·σ·(ωB)²/24

MATLAB `devCalcMCADHybridACLoss.m:137-139`의 큐보이드별 공식
`lactive*Cuboid_Width*Cuboid_Height^3*sigma*(omegaE*B)^2/24` 및
`calcHybridProx1DMCAD.m`의 `(1/2)*(1/12)` = **1/24 — 논문과 정확히 일치**.
주파수 의존은 ω² = (2πf)² 로 **f²** — Lin 규약의 (f·J_rms)², (f·B)² 스케일링과 일관.

### 3.2 핵심 항등성: g2 저주파 극한 = MCAD /24 (수치 검증 ✔)

(sinh x − sin x)/(cosh x + cos x) → x³/6 (x→0), γ_w·γ_h³ = w·h³/δ⁴ = w·h³·ω²μ²σ²/4 이므로

```
L·g2(γw,γh)·B² → L·(γw/(σμ²))·(γh³/3)·B² = L·w·h³·σ·ω²·B²/24     (정확 항등)
```

테스트 `test_g2_lowfreq_equals_mcad24`: 1 Hz에서 상대오차 **1.4e-8** ✔
→ g2는 /24 공식의 광대역 일반화(고주파 포화 포함)이며, Motor-CAD Hybrid와 자기일관적.

### 3.3 ⚠ MATLAB π² 버그 — 확인 및 수정 완료 (2026-07-14)

수식 검토 결과 아래는 정규화 차이가 아니라 **버그**로 확정되어 MATLAB 원본을 직접 수정했다:

| MATLAB 파일 | 버그 | 수정 |
|---|---|---|
| `calcHybridProx1D.m` | 분모 12π²μ²σ → **2π²(19.7배) 과소** | `/(6*mu^2*sigma)` |
| `calcHybridACLossWave.m` g1_func | 분모 6π²μ²σ → **π²(9.87배) 과소** | `/(6*mu_c^2*sigma)` |
| `AnaProx/calcProxg1.m` | 분모 6π²μ²σ → 동일 | `/(6*mu_c^2*sigma)` |
| `calcHybridJouleLossJuHa.m` | `kr=φ+(Nt²−0.2)/9·ξ⁴` — ξ에 주파수 미포함, Dowell 계층식 훼손 | `kr=φ+(Nt²−1)/3·ψ(ξ)` |

수정 후 g1 == g2 저주파 극한 == MCAD /24 (전 주파수 항등, `test_g1_equals_mcad24`).
Python `prox_coeff_g1()`도 동일하게 수정됨. 관련 Python 파일
`D:\KangDH\Thesis\ACloss_Ref\ACloss\ju_hybrid_acloss.py` / `morisco_acloss.py`의
`F_prox = Q·3/ξ³` 정규화 오류(올바른 극한은 Q→ξ⁴/3이므로 Q·3/ξ⁴)도 함께 수정.

### 3.4 JEET 식(5) 항별 매핑

> **주의**: `JEET rev3.tex`는 디스크(D:\ 전체)에 존재하지 않아 원문 대조 불가.
> 아래는 요청서에 주어진 식 기준. "lin2022efficient"는
> `D:\KangDH\Thesis\ACloss_Ref\ACloss\2022_ansys_An_Efficient_Method_for_Litz-Wire_AC_Loss_Computation...pdf`
> (ANSYS, Lin et al.)로 식별됨.

```
P_wdg_AC = k_r⁴ · k_a · [ 2·k_s·(f·J_rms)²·V_cu  +  g·l_a·B² ]
```

| 항 | 본 모듈 대응 | 유도 |
|---|---|---|
| **2k_s(fJ_rms)²V_cu** (skin, 전류 기인) | `calc_skin_effect_1D()`의 초과손실 P_dc·(φ−1) | φ(ξ) ≈ 1 + (4/45)ξ⁴ (저주파 전개). ξ⁴ = h⁴ω²μ²σ²/4, P_dc = J²V_cu/σ 대입 → P_excess = (4π²/45)·μ₀²σ·h⁴·(f·J_rms)²·V_cu. 즉 **k_s = 2π²μ₀²σh⁴/45** (ξ=h/δ 규약 기준; ξ=h/2δ 규약이면 h⁴/16으로 축소 — `xi_dim` 옵션) |
| **g·l_a·B²** (proximity, 외부장 기인) | `calc_proximity_effect_2D()`의 L·g2·B² | 저주파에서 g → w·h³σω²/24 = (π²/6)·w·h³·σ·f² (f² 의존). 광대역에서는 g2의 하이퍼볼릭 포화 |
| **k_r⁴, k_a** (반경/축방향 스케일링) | 본 모듈 범위 밖 (기하 스케일링 계수) | Stipetic 2016 스케일링 법칙: 손실밀도 보존 하 반경 스케일 s_r⁴, 축길이 비례 — `defScalingFactor`/`SLScaleMachine` (deve10_MCAD_refACLoss_v24.m) 쪽 파이프라인에서 적용 |

**결론**: MATLAB 구현은 (a) skin 항의 f² 의존(ω² 통해), (b) proximity /24 계수 모두
논문 규약과 일치한다. 단 ξ의 특성치수 규약(h vs h/2)은 MATLAB 주석만으로 확정 불가하여
기본 h/δ + `xi_dim='h/2'` 옵션으로 노출했다.

## 4. Python API

```python
from ac_loss_hybrid import (ConductorParams, MotorParams, OperatingPoint,
                            calc_skin_effect_1D, calc_proximity_effect_2D,
                            calc_hybrid_ac_loss_1D, calc_hybrid_ac_loss_2D)

cond = ConductorParams(width_mm=3.7, height_mm=1.6, active_length_mm=150.0)

# (1) 1D skin effect (해석식): P = P_dc·φ(ξ)  [W/도체]
P_skin = calc_skin_effect_1D(freq=1000.0, J_rms=5.0, conductor_params=cond)

# (2) 2D proximity: 스칼라 |B| 또는 (Br, Bθ) 튜플  [W/도체]
P_prox = calc_proximity_effect_2D(1000.0, (0.05, 0.02), cond)          # g2' 기본
P_mcad = calc_proximity_effect_2D(1000.0, 0.05, cond, method="mcad24")  # MCAD /24

# (3) Hybrid 1D — 도체 형상 + 전류밀도 + 큐보이드별 B (MCAD 재현)
motor = MotorParams(conductor=cond, n_conductors=48)
op = OperatingPoint(speed_rpm=6000, pole_pairs=4, J_rms_A_per_mm2=5.0,
                    B_cuboids_T=B_array)       # 또는 B_peak_T=0.05
r1 = calc_hybrid_ac_loss_1D(motor, op)          # P_skin_W, P_prox_W, P_ac_total_W, ...

# (4) Hybrid 2D — Motor-CAD 메시 내보내기 txt 기반
r2 = calc_hybrid_ac_loss_2D(motor, op, mesh_file="Mag_export.txt",
                            mode="peak")                       # 단일 스냅샷
r3 = calc_hybrid_ac_loss_2D(motor, op, mesh_file="Mag_ts.txt",
                            mode="fft", cycle_fraction=1.0,    # rotate-step 시계열
                            apply_pdf_blend=True)              # 로지스틱 블렌드 옵션
```

메시 파싱은 `tools/motorCAD/pyMCAD/magnetic_parse.py`를 재사용한다
(정규 패키지 import 실패 시 `magnetic_model`+`magnetic_parse`만 합성 패키지로 로드하는 폴백 내장).
래퍼: `parse_magnetic_snapshot()`, `parse_magnetic_timeseries()`, `extract_conductor_B()`.

## 5. 검증 요약 (테스트 25종 전부 통과)

| 검증 항목 | 결과 |
|---|---|
| δ(50 Hz)=9.346 mm, δ(1 kHz)=2.090 mm (교과서) | ✔ |
| φ(ξ) 점근: ξ→0 → 1, ξ→∞ → ξ, 저주파 전개 1+4ξ⁴/45 | ✔ |
| **g2(non-prime) 저주파 == MCAD /24** (상대오차 1.4e-8) | ✔ 핵심 |
| g1(버그 수정판) == MCAD /24 전 주파수 항등 | ✔ |
| 2D 결합식 Br²/Bθ² 선형성, w↔h 스왑 대칭 | ✔ |
| 사각 /24 vs 원형 /128 비율 | ✔ |
| 순수 정현파 FFT 모드 == peak 모드 (1e-9) | ✔ 핵심 |
| cycle_fraction=1/6 → 하모닉 차수 6, 12, … | ✔ |
| 합성 MCAD 포맷 txt 파싱 (Elements/Nodes/Regions, 시계열 8스텝) | ✔ |
| σ 온도보정 (120 °C → P_dc +39.3 %) | ✔ |

정성 비교: `AC_Loss_Correction_Context.md` 기준 Hybrid(해석) < FullFEA, AF≈1.1~4.5 범위 —
본 모듈은 Hybrid 쪽 재현이므로 FullFEA 대비 과소평가가 정상이며, AF 보정은 기존
`pyMotorCAD_Hybrid_AClossCode_Template.py`의 RBF/poly3d 파이프라인 담당.

## 6. 알려진 한계 / 옵션

- **ξ 규약**: 기본 ξ=h/δ. 반높이 규약 필요 시 `xi_dim='h/2'`.
- **메시 B의 peak/RMS**: MCAD magnetostatic 스냅샷은 순시값=peak 가정(기본). RMS 데이터면 `b_is_rms=True`.
- **도체 그루핑**: 영역(RegCode)당 1도체 가정. 영역명 패턴 `copper_region_pattern`
  (기본 `copper|conduct|wind|coil|armature|slot`, 대소문자 무시) 또는 `copper_reg_codes`로 명시 선택.
- **좌표계**: `field_frame='radial'` 기본 — 도체 중심각 기준 (Br, Bθ) 회전. g2 계수가
  방향별로 다르므로 frame 선택이 결과에 영향(단면이 반경방향 정렬이 아니면 `'xy'` 검토).
- 실측 Motor-CAD 내보내기 파일이 리포에 없어 end-to-end는 합성 파일로 검증
  (`test_real_export_file_if_present`가 실측 파일 발견 시 자동 검증).
