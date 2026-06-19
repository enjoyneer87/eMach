# pyMorisco_FFT_PEEC_Method34.ipynb — Execution Pipeline Plan

> Last updated: 2026-06-19  
> Companion notebook: `pyMorisco_Hybrid_clean.ipynb` (exploratory, 77 cells)  
> This streamlined notebook: **21 cells** (5 markdown + 16 code)
> Thesis refs: `morisco_Thesis_6p3.pdf`, `morisco_Thesis_E1.pdf`

## 1. Goal
Establish a **Pure Morisco PEEC baseline** before interpreting any Method 3+4 result.

The execution order is now:

1. Reproduce the Morisco baseline with Dirichlet circular Green's functions, slot-wall source only, and uniform weight.
2. Verify `i_mag`, `L_mutual`, harmonic spectrum, and `k_ih` scale.
3. Only after the baseline is physically reasonable, run **Method 3+4** (tooth-tip source + region weighting) as an experimental extension to improve the FEA C1/C6 eddy current gradient.

Method 3+4 is not an acceptance target by itself. It is a refinement path after the Morisco baseline gate passes.

## 2. Data Source Contract

| Variable | Source File | FEA Mode | Je 포함 | 용도 |
|----------|-----------|----------|--------|------|
| `ts_morisco` | `halfsc/hybrid/hybrid_halfsc_16000RPM` | Hybrid (Je=0) | ❌ | PEEC B/H 소스 |
| `ts_fullfea` | `halfsc/fullfea/fullfea_halfsc_16000RPM` | FullFEA (Je≠0) | ✅ | 비교 reference |

- 둘 다 **128 steps**, step index 1:1 대응
- PEEC는 Hybrid FEA의 B/H → magnetization current → filament eddy current 산출
- FullFEA의 Je는 비교용 reference로만 사용

## 3. Target Slot

| 항목 | 값 |
|------|-----|
| `TARGET_SLOT` | `0` (DXF 각도순 첫 번째) |
| 슬롯 중심 (global) | (88.76, -77.84) mm |
| 슬롯 각도 | ≈ -41° (318.8°) |
| 도체 수 | 6 (C1=airgap측, C6=yoke측) |
| 모델 | halfsc (half symmetry, 6슬롯 가시) |

---

## 4. Pipeline Architecture (Mermaid UML)

```mermaid
flowchart TD
    subgraph A["Phase A: Environment Setup"]
        A1["Cell 3 [A1]<br/>Imports<br/>(numpy, HYB.*, pyMCAD)"]
        A2["Cell 4 [A2]<br/>MotorCAD + Constants<br/>(COND_WIDTH, L_a, R_slot)"]
        A3["Cell 5 [A3]<br/>TXT Discovery + Parse<br/>(ts_morisco, freq, n_steps)"]
        A4["Cell 6 [A4]<br/>DXF Polygons + Slot Local<br/>(all_cond_paths, cond_local_rotated)"]
        A5["Cell 7 [A5]<br/>FEA Mesh + B/H Timeseries<br/>(triangles_arr, bx/by/hx/hy_ts_all)"]
    end

    subgraph B["Phase B: PEEC Model"]
        B1["Cell 9 [B1]<br/>Filament Grid + Z matrix<br/>(grid_local, Z, C, I_test)"]
        B2["Cell 10 [B2]<br/>Slot Filter + Geometry<br/>(filter_slot_wall, to_slot_local)"]
        B3["Cell 11 [B3]<br/>Boundary Cache + Mag Ref<br/>(boundary_cache, mag_ref)"]
    end

    subgraph C["Phase C: FEA Reference"]
        C1["Cell 13 [C1]<br/>FullFEA Load + Mesh<br/>(ts_fullfea, triangles_ff)"]
        C2["Cell 14 [C2]<br/>Step Select + Je Extract<br/>(_tri_to_idx, je_slot)"]
    end

    subgraph D0["Phase D0: Pure Morisco Baseline Gate"]
        D0A["Cell 16 [D0]<br/>L_mutual (Dirichlet circular)<br/>+ slot-wall I_mag FFT"]
        D0B["Cell 16 [D0]<br/>Baseline PEEC solve<br/>→ k_ih_fft + spectrum checks"]
    end

    subgraph D1["Phase D1: Method 3+4 Extension"]
        D1A["Cell 17 [D1]<br/>L_ext (Rect Image Green's)<br/>+ tooth-tip extension<br/>+ region weight (w_ag/w_yk)"]
        D1B["Cell 18 [D1]<br/>V_mag = jω·L_ext·I_mag_fft<br/>→ PEEC solve → k_ih"]
        D4["Cell 19 [D4]<br/>Static Plot (step-selectable)<br/>(FEA vs PEEC tripcolor/contourf)"]
        D5["Cell 20 [D5] ★<br/>Interactive Widget<br/>(ipywidgets slider, signed Je)"]
    end

    A1 --> A2 --> A3 --> A4 --> A5
    A4 --> B1; A5 --> B1
    B1 --> B2; A5 --> B2
    B2 --> B3; A5 --> B3

    A3 --> C1; A4 --> C1
    C1 --> C2

    B1 --> D0A; B3 --> D0A; A5 --> D0A; B2 --> D0A
    D0A --> D0B
    D0B --> D1A; B2 --> D1A; B3 --> D1A
    B1 --> D1B; D1A --> D1B; C2 --> D1B
    D1B --> D4; C2 --> D4
    D1B --> D5; C2 --> D5
```

---

## 5. Critical Path — Cell Execution Order

### Phase A: Setup (Cells 3–7)

| Step | Cell | ID | Role | Key Outputs |
|------|------|----|------|-------------|
| 1 | 3 | A1 | Imports | numpy, HYB.*, pyMCAD |
| 2 | 4 | A2 | MotorCAD + SI constants | SIGMA_CU, h_m, b_m, L_a, R_slot_inner/outer_mm |
| 3 | 5 | A3 | TXT discovery + parse | ts_morisco (hybrid), freq, omega, n_steps=128 |
| 4 | 6 | A4 | DXF polygons + slot local | all_cond_paths, cond_local_rotated, TARGET_SLOT=0 |
| 5 | 7 | A5 | FEA mesh + B/H timeseries | triangles_arr, iron_mask_arr, bx/by/hx/hy_ts_all |

### Phase B: PEEC Model (Cells 9–11)

| Step | Cell | ID | Role | Key Outputs |
|------|------|----|------|-------------|
| 6 | 9 | B1 | Filament grid + Z | grid_local (26×12=312/cond), Z, C, R_boundary=128.2mm |
| 7 | 10 | B2 | Slot filter + geometry | filter_slot_wall(), to_slot_local(), slot_angle_center |
| 8 | 11 | B3 | Boundary cache + mag ref | boundary_cache, mag_ref, mask_fixed (100 edges) |

### Phase C: FEA Reference (Cells 13–14)

| Step | Cell | ID | Role | Key Outputs |
|------|------|----|------|-------------|
| 9 | 13 | C1 | FullFEA TXT + mesh | ts_fullfea (128 steps), triangles_ff (21272 elem) |
| 10 | 14 | C2 | Step select + Je extract | **_tri_to_idx** (node-matched), target_step_idx, je_slot |

### Phase D0: Pure Morisco Baseline Gate (Cell 16)

| Step | Cell | ID | Role | Key Outputs |
|------|------|----|------|-------------|
| 11 | 16 | D0 | `L_mutual` (**Dirichlet circular** G.F.) + slot-wall `I_mag` FFT + baseline PEEC solve | L_mutual_mat (n_fil×80), I_mag_phasor, mag_spectrum, **k_ih_fft** |

### Phase D1: Method 3+4 Extension (Cells 17–20)

| Step | Cell | ID | Role | Key Outputs |
|------|------|----|------|-------------|
| 12 | 17 | D1 | `L_ext` (**Rectangular image** G.F.) + tooth-tip ext. | L_ext (n_fil×143), mask_airgap/tooth/yoke, **replacement** for L_mutual |
| 13 | 18 | D1 | V_mag = jω·L_weighted·I_mag_fft → PEEC solve | results_g (4 weight cases), k_ih |
| 14 | 19 | D4 | Static comparison plot | FEA vs PEEC tripcolor/contourf (개별 vmax) |
| 15 | 20 | D5 | **Interactive widget** | ipywidgets slider, signed Je (RdBu_r) |

> ⚠️ **D0→D1 관계**: `L_ext`는 `L_mutual`을 concat/extend하는 것이 아님. **완전히 다른 Green's function**으로 재계산한 대체 행렬이다. Cell 16의 `L_mutual`은 더 이상 단순 debug가 아니라 **Pure Morisco baseline gate**이다. 이 gate에서 `i_mag`, spectrum, `k_ih_fft`가 비현실적이면 Cell 17-18의 Method 3+4 결과는 절대값 기준으로 해석하지 않는다.

---

## 6. Quick-Run Recipe

```
Cell 3 → 4 → 5 → 6 → 7 → 9 → 10 → 11 → 13 → 14 → 16 → 17 → 18 → 19 → 20
```

**Total: 15 cells** (모든 코드 셀 = 순차 실행, 스킵 없음)

### 6.1 Baseline Gate Checkpoint

After **Cell 16**, stop and inspect the Pure Morisco baseline before running Method 3+4:

| Check | Expected Decision / Concrete Benchmarks |
|-------|-------------------|
| `k_ih_fft` | Must enter a physically plausible range before Method 3+4 is trusted.<br/>- **Simple Slot (BP1: 162.5 A, 300 Hz)**: expected $k_{ih} \approx 1.19 - 1.20$.<br/>- **Simple Slot (BP2: 126 A, 1066 Hz)**: expected $k_{ih} \approx 3.48 - 3.52$.<br/>- **Simple Stator (10 kHz, 25 A)**: expected $k_{ih} \approx 1.31$.<br/>- **Traction Motor Active Part (BP1)**: expected $k_{ih} \approx 1.51 - 1.58$.<br/>- **Traction Motor Active Part (BP2)**: expected $k_{ih} \approx 3.45 - 3.62$. |
| `i_mag` fundamental / RMS | Must not be orders of magnitude larger than Morisco thesis §6.3/E.1 benchmarks imply.<br/>- **BP1 stator $i_{mag}$ fundamental peak**: ~400 A (stator surface max), ~10 A (stator core max) (Fig. 6.12).<br/>- **BP1 rotor $i_{mag}$ fundamental peak**: ~4000 A (rotor surface max), ~100 A (rotor core max) (Fig. 6.17). |
| Harmonic spectrum | Significant harmonics should be explainable by the quasi-static sequence:<br/>- **Stator magnetization**: only fundamental and 3rd harmonic are > 5% of fundamental.<br/>- **Rotor magnetization**: DC component in rotor coordinate system converts into significant harmonics (fundamental, 3rd, 5th, 7th, 9th, 11th) in stator target grid system. |
| `L_mutual_mat` scale | Verify Dirichlet circular equation, axial length factor, and `R_boundary` normalization before changing weights. |

Only continue to **Cell 17-18** when this checkpoint is acceptable. If it fails, debug `i_mag`, `L_mutual`, `Z`, and units first.

---

## 7. Key Fixes Applied (2026-06-18)

### 7.1 FEA Element Indexing: `_tri_to_idx` (Cells 14, 19, 20)

**문제:** FEA Je를 순차 인덱스(`ei++`)로 채우면, step간 region 순회 순서가 다를 때 Je가 엉뚱한 element에 매핑.

**수정:** `_tri_to_idx = {(n1,n2,n3): flat_index}` 룩업 테이블로 node triplet 기반 정확한 매핑.

```python
# Before (broken):
je_arr[ei] = getattr(el, 'je', 0) or 0
ei += 1

# After (node-matched):
idx = _tri_to_idx.get((n1, n2, n3))
if idx is not None:
    je_arr[idx] = getattr(el, 'je', 0) or 0
```

적용 셀: C2 (14), D4 (19), D5 (20)

### 7.2 FEA 플롯 Axis 범위 (Cells 19, 20)

**문제:** `ax.autoscale()`가 전체 mesh 노드 좌표(21,272 elements)를 포함 → 도체가 점으로 보임.

**수정:** 도체 범위 기반 명시적 axis limits:
```python
_margin_m = max(cw_m, ch_m) * 1.2
_xlim = ((cond_local_rotated[:, 0].min() - _margin_m) * 1e3, ...)
ax.set_xlim(_xlim); ax.set_ylim(_ylim)
```

### 7.3 개별 vmax (Cells 19, 20)

**문제:** FEA(~300 A/mm²)와 PEEC(~3000 A/mm²) 스케일 차이 → 공유 vmax로는 FEA가 보이지 않음.

**수정:** FEA/PEEC 각각 독립 vmax + 독립 colorbar.

### 7.4 Signed Je 시각화 (Cell 20)

**변경:** `|Je|` (jet, 0~vmax) → signed Je (RdBu_r, -vmax~+vmax)  
- 빨간색 = +Je (z+ 방향), 파란색 = -Je (z- 방향)  
- bar chart는 `|Je|_max` 유지 (크기 비교용)

---

## 8. Known Issues

### 8.1 PEEC 크기 과대: baseline gate 미통과

| Method | FEA C1 | PEEC C1 | PEEC/FEA |
|--------|--------|---------|----------|
| uniform (w_ag=1) | 313 | 825 | **2.6x** |
| w_ag=3, w_yk=0.3 | 313 | 2444 | **7.8x** |

- 데이터 소스 분리는 정상 (hybrid→PEEC, fullfea→비교)
- Cell 16 Pure Morisco baseline도 `k_ih_fft`가 과대 → Method 3+4 이전 문제가 존재
- 기본 i_mag 기본파 944A, 14개 유의미 고조파 → source current 또는 커플링 스케일이 과대
- `L_mutual` Dirichlet circular 식, `Z = R + jωL`, `R_boundary`, axial length factor 검토 필요
- `L_ext` / region weight 튜닝으로 절대값을 맞추면 안 됨
- k_ih = 615~4761 (물리적으로 비현실적, 기대값 ~10-50)

### 8.2 Hybrid_clean과 동일 증상

Hybrid_clean 노트북도 PEEC uniform C1=1317 vs FEA C1=929 (1.4x), C6에서는 7.5x.  
→ PEEC 모델링 자체의 구조적 문제 (Green's function 과대 커플링).

---

## 9. Current Diagnostic Output (Cell 18 D1 Extension)

```
w_ag=1 (uniform):   k_ih=615,  C1/C6=1.10x  (symmetric, no gradient)
w_ag=2, w_yk=0.5:   k_ih=1069, C1/C6=3.85x  
w_ag=3, w_yk=0.3:   k_ih=1952, C1/C6=7.89x  
w_ag=5, w_yk=0.1:   k_ih=4761, C1/C6=16.6x  (over-weighted)
```

FEA target: C1/C6 ≈ 2.1× (step 65 기준). Ratio 매칭은 w_ag=2~3이 가장 가깝지만 절대값은 ~3-8x 과대.

Interpretation:
- These are **diagnostic outputs**, not accepted results.
- Method 3+4 may improve the C1/C6 shape, but it must not be used to hide a failed Pure Morisco baseline.
- The next accepted milestone is Cell 16/EXP-1 entering a plausible `k_ih` range with traceable `i_mag` and `L_mutual` scale.

---

## 10. Variable Dependency Graph

```mermaid
graph LR
    subgraph "Raw Data"
        ts_m["ts_morisco<br/>hybrid, 128 steps<br/>(Cell 5)"]
        ts_f["ts_fullfea<br/>fullfea, 128 steps<br/>(Cell 13)"]
        dxf["conductor_polygons_dxf.pkl<br/>(Cell 6)"]
    end

    subgraph "Mesh Arrays (from hybrid)"
        nxy["node_xy_arr<br/>(Cell 7)"]
        tri["triangles_arr<br/>(Cell 7)"]
        iron["iron_mask_arr<br/>(Cell 7)"]
        bh["bx/by/hx/hy_ts_all<br/>(Cell 7)"]
    end

    subgraph "PEEC Model"
        grid["grid_local<br/>(Cell 9)"]
        zmat["Z, C, I_test<br/>(Cell 9)"]
        bc["boundary_cache<br/>(Cell 11)"]
    end

    subgraph "FEA Reference (from fullfea)"
        tri_idx["_tri_to_idx<br/>(Cell 14)"]
        je["je_slot<br/>(Cell 14)"]
        nlocal["node_x/y_local_mm<br/>(Cell 14)"]
    end

    subgraph "Pure Morisco Gate (D0: Dirichlet)"
        mag["mag_ref + I_mag_phasor<br/>(Cell 16)"]
        lm["L_mutual_mat<br/>Dirichlet circular G.F.<br/>(Cell 16, required baseline)"]
    end

    subgraph "Method 3+4 Extension (D1: Rect Image)"
        lext["L_ext (143 sources)<br/>Rectangular Image G.F.<br/>(Cell 17, experimental replacement)"]
        wvec["w_vec (region weight)<br/>mask_airgap/tooth/yoke"]
    end

    subgraph "PEEC Solve"
        vmag["V_mag = jω·L·I_mag_fft<br/>(baseline: L_mutual, extension: L_ext)"]
        res["i_fil → J_eddy → k_ih<br/>(Cell 18)"]
    end

    ts_m --> bh --> mag
    ts_m --> nxy --> grid
    dxf --> iron
    tri --> bc --> mag
    zmat --> lm
    grid --> lm
    grid --> lext
    bc --> lext
    mag --> lext
    lext --> wvec --> vmag
    mag --> vmag
    zmat --> res
    vmag --> res

    ts_f --> tri_idx --> je
    je --> D4D5["Cells 19-20<br/>Visualization"]
    res --> D4D5
    nlocal --> D4D5
```

> **Note**: `L_mutual_mat`(D0)과 `L_ext`(D1)는 **대체 경로**임. `L_mutual_mat`은 Morisco 기본 방법(Dirichlet circular)의 필수 baseline이고, `L_ext`는 Method 3+4(Rectangular image + tooth-tip)의 실험적 확장이다. Baseline이 실패하면 `L_ext` 결과는 shape diagnostic으로만 본다.

---

## 11. PEEC Formulation — Morisco Ch.4/Ch.5 → Code Mapping

### 11.1 이론 개요 (Morisco PhD, Ch.4)

PEEC 방법의 핵심은 도체 단면을 **filament** (부분 도체, partial conductor)로 분할하고, 각 filament 사이의 **전자기 커플링**을 Green's function으로 계산하는 것:

$$Z_\Lambda = R_\Lambda + j\omega L_\Lambda \quad \text{(eq 4.5, 4.35)}$$

여기서:
- $R_\Lambda$: 대각 저항 행렬 (filament의 기하학적 저항)
- $L_\Lambda$: filament 간 상호 인덕턴스 행렬 (Green's function으로 계산)

### 11.2 Green's Function 선택지

| 방법 | Green's Function | 경계 조건 | Morisco 참조 | 본 구현 위치 |
|------|-----------------|-----------|-------------|-------------|
| **Pure Morisco baseline** | Dirichlet Circular | 원형 경계 $R_\Omega$ | eq 4.36-4.37 | Cell 9 (Z), Cell 16 (`L_mutual`, required gate) |
| **Method 3+4 extension** | Rectangular Image | 직사각형 슬롯 벽 + tooth-tip | Ahagon/Dowell 확장 | Cell 17 (`L_ext`, experimental replacement) |

### 11.3 핵심 수식 → 코드 매핑

| Morisco Eq. | 수식 | 코드 변수 | Cell | 설명 |
|:-----------:|-------|-----------|:----:|------|
| 4.36 | $L_{vv} = -\frac{\mu_0 l}{2\pi}\left[\ln\rho_\Omega - \frac{1}{2}\ln\left((1-|\xi|^2)^2 + (\xi/\rho_\Omega)^2\right)\right]$ | `L_matrix` (대각) | B1 (9) | Self-inductance (Dirichlet circular) |
| 4.37 | $L_{vw} = -\frac{\mu_0 l}{2\pi}\left[-\ln|\xi_v-\xi_w| - \frac{1}{2}\ln(...)\right]$ | `L_matrix` (off-diag) | B1 (9) | Mutual (filament↔filament) |
| 4.37 | 동일 Dirichlet, $\xi = (x+jy)/R_\Omega$ | `L_mutual_mat` | D0 (16) | Filament↔boundary edge (circular), baseline gate |
| *(Method 3+4)* | 직사각형 Image Green's function | `L_ext` | D1 (17) | Filament↔boundary+tooth-tip (rectangular), extension |
| 4.5 | $Z_\Lambda = R + j\omega L$ | `Z_n = R_matrix + 1j*omega_n*L_matrix` | D0/D1 (16/18) | Frequency-dependent impedance |
| 4.44-4.51 | $M = B/\mu_0 - H$ | `mag_ref[step]` | B3 (11) | Magnetization from FEA B, H |
| 4.52 | $k_{mag} = \frac{1}{\mu_0}(M_\nu - M_\xi)\times \hat{n}_\theta$ | `boundary_cache` | B3 (11) | Surface magnetization current density |
| 4.53 | $i_{mag} = k_{mag} \cdot |w_\theta|$ | `I_mag_phasor` (FFT후) | D0 (16) | Equivalent mag. source current |
| 4.18 | $i = Z^{-1} C (C^T Z^{-1} C)^{-1} I$ | `i_raw + i_corr` | D0/D1 (16/18) | Constraint-projected PEEC solve |
| 4.27 | $k_{ih} = P_{total} / P_{DC}$ | `k_ih`, `k_ih_fft` | D0/D1 (16/18) | AC loss factor |

### 11.4 D0 vs D1: 두 Green's Function의 관계

```
┌─────────────────────────────────────────────────────────────┐
│ Cell 16 (D0): L_mutual_mat — Dirichlet Circular             │
│  • Morisco 원래 방법 (eq 4.37 그대로)                          │
│  • ξ = (x+jy) / R_boundary (=128.2mm)                       │
│  • 소스: slot-wall boundary edges only (~80개)                │
│  • 용도: 필수 baseline gate, Morisco thesis 대비 정합성 확인     │
│  • k_ih/i_mag/L scale이 실패하면 D1 결과를 절대값으로 해석 금지   │
└─────────────────────────────────────────────────────────────┘
         ↓ (baseline 통과 후 실험적 대체)
┌─────────────────────────────────────────────────────────────┐
│ Cell 17 (D1): L_ext — Rectangular Image Method               │
│  • Method 3: tooth-tip 엣지를 추가 자화원으로 포함 (80→143)     │
│  • Method 4: 영역별 가중치 (w_ag > 1, w_tw = 1, w_yk < 1)    │
│  • Green's function: 직사각형 슬롯 경계의 Image 전개            │
│  • Morisco 원식이 아니라 gradient 개선용 실험 확장              │
└─────────────────────────────────────────────────────────────┘
```

### 11.5 PEEC Solve 알고리즘 (Cell 16 baseline, Cell 18 extension)

두 가지 모드를 명확히 분리한다.

- **Baseline mode (D0/Cell 16):** `L = L_mutual_mat`, source = slot-wall `I_mag_phasor`, weight = uniform.
- **Extension mode (D1/Cells 17-18):** `L = L_ext`, source = extended `I_mag_fft_ext`, optional region weight.

```python
for n_h in harmonic_indices:               # 14개 유의미 고조파
    omega_n = n_h * omega                   # 주파수별 ω
    Z_n = R_matrix + 1j * omega_n * L_matrix  # eq 4.5: Z_Λ(ω)
    
    # V_mag: 자화 소스로부터의 유기 전압
    # Baseline: L_weighted = L_mutual_mat
    # Extension: L_weighted = L_ext * w_vec[np.newaxis, :]
    V_n = 1j * omega_n * (L_weighted @ I_mag_fft_selected[n_h])
    
    # 제약조건 없는 기본 응답
    i_raw = np.linalg.solve(Z_n, V_n)
    
    # 순전류=0 제약 (C^T · i = I_imposed)
    ZinvC = np.linalg.solve(Z_n, C)
    i_corr = ZinvC @ np.linalg.solve(C.T @ ZinvC, -C.T @ i_raw)
    
    # 총 filament 전류 (n_h=1일 때 imposed current 추가)
    i_fil_harmonics[n_h] = (i_imposed if n_h == 1 else 0) + i_raw + i_corr
```

### 11.6 Green's Function 불일치 문제 (Known Issue)

현재 구현의 잠재적 불일치:

| 행렬 | Green's Function | 경계 형상 |
|-------|-----------------|-----------|
| `Z_n` 내부의 `L_matrix` (Cell 9) | Dirichlet **Circular** | R=128.2mm 원형 |
| `L_ext` (Cell 17) | **Rectangular** Image | 직사각형 슬롯 벽 |

Morisco 원논문에서는 Z와 L_ΓV 모두 **동일한** Dirichlet circular boundary를 사용.  
본 구현에서는 L_ext만 rectangular로 변경 → **이론적 불일치**가 존재할 수 있음.

**가능한 해석:**
1. Rectangular image가 실제 슬롯 형상을 더 잘 근사 → 의도적 개선
2. Z matrix의 filament↔filament 커플링은 슬롯 경계와 무관하게 circular로 충분
3. 과대추정(k_ih=615~4761)의 원인 중 하나일 가능성 → 추가 검증 필요

**검증 원칙:**
- 먼저 `Z_n`과 `L_mutual_mat`을 모두 Dirichlet circular로 둔 Pure Morisco baseline을 통과시킨다.
- 그 다음 `L_ext`로 바꿨을 때의 변화량을 비교한다.
- `L_ext`와 region weight는 C1/C6 shape 개선용이며, baseline 스케일 오류를 보정하는 knob로 쓰지 않는다.

---

## 12. §4.8/§4.9 구현 계획 및 k_ih 과대추정 수정 계획

> Added: 2026-06-18  
> 근거: Morisco PhD §4.8 (pp.71-75), §4.9 (pp.76-90), §4.10 (pp.91-93)

### 12.1 §4.8 재해석 — Quasi-Static FEA 동일성 확인

#### 기존 오해
"Morisco는 Static FEA 1회 → 코드에서 로터 회전 변환"으로 오해했으나, 논문 재확인 결과:

#### 정정된 이해 (PDF p.91-93, footnote 12)
> "the time history of the local magnetization of the ferromagnetic material is therefore
> determined by means of **a sequence of static FEM calculations**"
> — Morisco §4.10, p.91

**즉, Morisco도 quasi-static transient (n_s=120 정적 계산 시퀀스)를 사용.**  
Motor-CAD의 128-step quasi-static과 **본질적으로 동일한 방식**.

| 항목 | Morisco (JMAG) | 현재 (Motor-CAD) |
|------|---------------|-----------------|
| FEA 방식 | Quasi-static (n_s=120 magnetostatic) | Quasi-static transient (128 steps) |
| 로터 위치 | 매 스텝 회전 후 정적 solve | 매 스텝 회전 후 정적 solve |
| 포화도 반영 | ✅ 각 스텝별 비선형 B-H solve | ✅ 각 스텝별 비선형 B-H solve |

**사용자 지적 확인**: "고정된 로터를 임의로 회전변환하면 자석위치변화에 따른 포화도 반영이 안된다" — 맞음.  
Morisco는 이를 해결하기 위해 **각 로터 위치에서 독립 정적 FEM을 수행**한 것이지, 1회 계산 결과를 회전변환한 것이 아님.

#### §4.8의 실제 목적 — L 행렬 위치독립성 보장

§4.8의 mesh 변환은 FEM을 1회만 하기 위한 것이 **아님**. 목적:
1. 로터 FEM mesh는 회전 → 로터 철심의 boundary edge 위치가 매 스텝 변경
2. L 행렬(filament↔자화소스 상호인덕턴스)은 **위치에 의존**하면 매 스텝 재계산 필요
3. 따라서 **정적 target mesh**(Z)를 생성하고, 회전하는 source mesh(S)의 자화를 Z로 변환
4. 결과: L 행렬은 정적 target mesh 기준으로 **1회만** 계산하면 됨

#### 회전자 자화의 고주파 고조파 생성 원리
회전자의 영구자석 및 회전자 포화에 의한 자화 $M$은 회전자 자체의 회전 좌표계에서는 시간에 무관한 DC 성분이지만, 이를 정적 타겟 고착 격자(고정자 타겟 프레임)로 변환할 때, 공간적 회전에 의해 고정자 프레임 상에서 시변 고조파 성분들로 변환됩니다 (§4.8).
이 변환을 통해 회전자 자화 전류 $i_{mag,rotor}$에 회전 주파수의 홀수배 고조파(1, 3, 5, 7, 9, 11차 등)가 생성되게 되며, 특히 11차 고조파까지 전체 기본파 크기의 5%를 초과하는 상당한 비중을 가지게 됩니다.

#### 현재 구현에서의 §4.8 필요성 평가

| 시나리오 | §4.8 필요? | 이유 |
|---------|-----------|------|
| 스테이터 철심만 자화소스로 사용 (현재) | ❌ 불필요 | 스테이터 mesh는 회전하지 않음 → L 자동으로 위치독립 |
| **로터 철심도** 자화소스로 추가 (§4.8 완전 구현) | ✅ 필요 | 로터 edge가 회전 → source→target 변환 필수 |

#### 현재 구현의 물리적 갭

**Morisco는 로터 철심 자화전류를 명시적으로 PEEC 소스에 포함:**
- 로터 iron mesh 경계면에 $i_{mag,rotor}$ 할당 (eq.4.52-4.53 동일 적용)
- 로터↔filament 상호인덕턴스 $L_{\Gamma V,rot}$ 계산
- 결과: 로터 permanent magnet + 로터 포화의 **직접적 proximity effect** 모델링

**현재 구현은 스테이터 경계만 사용:**
- 로터의 영향은 FEA B/H를 통해 **간접적**으로만 스테이터 경계에 반영
- 로터↔filament 직접 커플링 없음
- 특히 airgap-side conductor (C1)에 대한 로터 proximity 과소평가 가능성

### 12.2 §4.8 구현 계획 (우선순위: 중)

**단계적 접근 (Phase 0 과대추정 해결 후 진행):**

```
Phase A: 로터 자화소스 추가 가능성 평가
  ┌─ 1. Motor-CAD FEA mesh에서 로터 iron 영역 식별
  │     - iron_mask_arr에서 rotor region elements 분리
  │     - 로터-스테이터 경계면 (airgap boundary) edge 추출
  │
  ├─ 2. Rotor magnetization current 계산
  │     - 동일 eq.4.52: K_mag = (M_ν - M_ξ) × n_θ / μ₀
  │     - 로터 element의 M(t)는 FEA에서 이미 128 step 보유
  │
  ├─ 3. Target mesh 생성 (§4.8.1)
  │     - 로터 영역에 structured cylindrical target mesh 생성
  │     - 원 mesh→target mesh 자화 변환 (eq.4.57-4.60)
  │     - 또는: 각 스텝에서 로터 edge를 직접 사용 → L_rot 매 스텝 계산 (비효율적)
  │
  └─ 4. L_ΓV,rot 계산 + PEEC 확장
        - 기존 L_ext에 rotor source 열 추가
        - Z matrix 크기 변경 없음 (filament만 풀이 대상)
        - V_mag += jω·L_rot·i_mag_rotor
```

**선결 조건:**  Phase 0 (Green's function 불일치/i_mag 스케일 수정) 완료 후 진행.  
로터 자화를 추가해도 과대추정 문제가 해결되지 않으면 무의미.

### 12.3 §4.9 대칭성 활용 계획 (우선순위: 중-하)

#### 현재 상태
- TARGET_SLOT = 0 (1슬롯만 모델링)
- 인접 슬롯 도체의 proximity effect 미반영
- 8P/48S (q=2): 전자기 대칭 = 1 pole pitch = 6 slots

#### Morisco의 대칭 공식 (eq.4.65)

$$L_{total,sym} = \sum_{k=1}^{n_{sym}} k_{sym} \cdot L_{k-1}$$

$$k_{sym} = (-1)^{k+1} \quad \text{(antiperiodic, eq.4.66)}$$

우리 모터 (8P/48S, full-pitch):
- $n_{sym}$ = 6 (6 slots per pole pitch)
- Antiperiodic: slot 1,3,5 → $k_{sym}=+1$; slot 2,4,6 → $k_{sym}=-1$

#### 구현 계획

```
Phase B: Adjacent-slot symmetry
  ┌─ 1. Position matrix 확장
  │     - slot 0 filaments의 위치를 rotation operator로 복제 (eq.4.76)
  │     - α_sym = π/4 (45° = 1 pole pitch / 6 slots × ...)
  │     - 실제: slot pitch angle = 360°/48 = 7.5°
  │
  ├─ 2. 인접 슬롯 L_k 계산
  │     - L_k-1 = L(slot_0_filaments ↔ slot_k_filaments)  
  │     - k=1,...,5 (slot 0 기준 양쪽 인접 슬롯)
  │     - Morisco eq.4.65: 부호는 전류 방향에 의존
  │
  ├─ 3. L_total,sym 구성
  │     - L_total,sym = L_self + Σ k_sym · L_k-1
  │     - Z_total = R + jω·L_total,sym
  │
  └─ 4. 자화소스도 인접 슬롯 경계 포함
        - 인접 슬롯의 iron boundary edges도 i_mag 소스로 추가
        - L_ext도 인접 슬롯 source edge 포함하여 확장
```

**영향 예상:**
- 인접 슬롯 도체 전류의 proximity effect → C1/C6 gradient 개선
- 논문 Fig.4.19: rotational symmetry L_total,sym 예시 (6 conductor)
- 그러나 과대추정 문제와는 **독립적** (L 크기 자체는 증가)
- 우선순위: 과대추정 해결 후, C1/C6 gradient 정밀도 개선 시 적용

### 12.4 k_ih 과대추정 수정 계획 (우선순위: 최고)

#### 실험 결과 (2026-06-18 실행 완료)

| EXP | 가설 | 결과 | 판정 |
|-----|------|------|------|
| EXP-1 | L_ext(rect) vs L_mutual(circular) 불일치가 원인 | L_mutual로 교체 시 k_ih **615 → 1424** (악화) | ❌ **G.F. 불일치는 원인 아님** |
| EXP-2 | i_mag 절대 크기 과대 (μ₀ 누락?) | i_mag 기본파 max=944A, |M|=1.3e6 A/m (1.9T 포화 → 물리적 정상) | ❌ **코드 버그 아님, 스케일 차이** |
| EXP-3 | V_mag 스케일 검증 | V_mag(circular)=19.2, V_mag(rect)=2.5, ωL/R=2.4% (저항 지배) | ✅ **V_mag이 과대 → 근본 원인 확인** |

#### 실험 상세 수치

```
EXP-2: i_mag Magnitude
  i_mag_timeseries: (128, 100) — 128 steps × 100 boundary edges
  Per-edge RMS:  mean=609 A, max=698 A
  FFT fundamental max: 944 A
  |M| at boundary: mean=1,293,000 A/m, max=1,515,000 A/m
  |M|·μ₀ = 1.9 T (포화 철심 — 물리적으로 정상)
  edge_length mean = 0.502 mm

  왜 Morisco는 0.6A이고 우리는 944A?
  → Morisco 모터: edge~0.1mm, |M|~1e6 → i_mag = 1e6 × 0.1e-3 = 0.1 A
  → 우리 모터:    edge~0.5mm, |M|~1.3e6 → i_mag = 1.3e6 × 0.5e-3 = 650 A
  → 스케일 차이 (~1000x)이지 코드 오류 아님

EXP-1: Pure Morisco (Dirichlet circular, 100 sources, uniform w=1)
  |L_mutual| mean=8.69e-8, max=1.62e-7  (Dirichlet circular)
  |L_ext|    mean=7.66e-9, max=1.06e-7  (Rectangular image)
  → L_mutual이 L_ext보다 11x 크다!
  → k_ih = 1424 (Method34의 615보다 악화)

EXP-3: V_mag Scale
  |V_mag| (Morisco circular): mean=19.2, max=20.9
  |V_mag| (Method34 rect):    mean=2.5,  max=4.1
  Z matrix: R_fil=0.0573Ω, ωL_self=0.0014Ω, ωL/R=2.44%
  → 저항 지배 시스템: V_mag 크기가 직접 i_eddy 크기 결정
```

#### ★ 근본 원인 진단: **이중 계수 (Double-Counting)**

| 경로 | 포함 여부 | 비고 |
|------|---------|------|
| Z matrix (L_ΓΓ) | 도체↔도체 mutual inductance | ✅ filament 자체 leakage 포함 |
| i_mag (from Hybrid FEA) | PM flux + **도체전류 leakage** | ⚠️ 도체전류 기여분 포함! |
| V_mag = jω·L_ΓV·i_mag | PM proximity + **leakage proximity** | ⚠️ leakage 이중계수 |

**Motor-CAD Hybrid 모드**: 도체에 전류를 인가한 상태에서 MQS solve → B/H에 도체전류 leakage flux 포함.
따라서 M = B/μ₀ - H에는 PM 기여 + 도체전류 leakage 기여가 모두 포함됨.
Z matrix의 L_ΓΓ도 이미 도체간 커플링을 모델링하므로, **동일한 leakage가 두 번 계수**.

**Morisco의 해결책** (§4.7.2, p.66):
> "eddy currents in the ferromagnetic material... are neglected"
> → FEM에서 도체 σ=0 또는 uniform J 인가 (도체 내 와전류 없음)
> → M에 도체 와전류 기여분 미포함

**우리의 차이점**:
- Motor-CAD Hybrid는 proximity loss를 **별도로** 계산하는 모드 (도체 σ≠0)
- 따라서 FEA B/H에 도체전류의 self-flux가 이미 포함됨
- 이것이 i_mag → V_mag → PEEC solve로 전파 → ~100x 과대추정

#### 수정 방안 (우선순위순)

```
[FIX-1] No-Load FEA (I_cond=0) — 최우선
  • Motor-CAD에서 RMSCurrent=0 또는 ConductorCurrent=[0]*6 설정
  • PM flux만의 B/H → M → i_mag 추출
  • 도체전류 leakage 완전 제거
  • pyMotorCAD_Hybrid_AClossCode.ipynb에서 이미 export 인프라 구축됨
  ★ 기대: i_mag 크기 10~100x 감소, k_ih ∈ [3, 15]

[FIX-2] Time-domain regression — 대안
  • i_mag(t)를 도체전류 I(t)에 대해 regression
  • i_mag = i_mag_PM(t) + α·I(t) 분해
  • i_mag_PM만 PEEC에 사용
  • 추가 FEA 불필요 (기존 128-step 데이터 활용)
  • 단, 비선형 포화로 인해 선형 regression의 정확도 제한

[FIX-3] V_leak explicit subtraction (Morisco Step 7)
  • V_leak = jω·L_ΓΓ·i_conductor (도체전류에 의한 leakage voltage)
  • V_mag_corrected = V_mag - V_leak
  • solver.py에 이미 deprecated `subtract_slot_leakage()` 존재
  • 단, L_ΓΓ와 L_ΓV가 다른 Green's function이면 정확한 차감 불가
```

#### 수정 로드맵 (업데이트)

```mermaid
flowchart TD
    A["EXP-1~3 완료 ✅<br/>근본 원인: 이중계수"]
    B["FIX-1: No-Load FEA<br/>(I=0, PM only i_mag)"]
    C["FIX-2: Regression<br/>(i_mag_PM 분리)"]
    D["k_ih 재계산<br/>(L_mutual circular + PM-only i_mag)"]
    E["k_ih ∈ [4, 10]?"]
    F["§4.9 symmetry 적용"]
    G["§4.8 rotor mag 추가"]
    H["k_ih ≈ 6.06 ±10%"]
    X["FIX-3: V_leak 차감<br/>(fallback)"]

    A --> B
    A --> C
    B --> D
    C --> D
    D --> E
    E -->|Yes| F --> G --> H
    E -->|No| X --> D
```
| EXP-4 튜닝 후 | 4.5 ~ 8.0 | 6.06 | ±30% |
| EXP-5 + §4.9 후 | 5.5 ~ 6.5 | 6.06 | ±10% (Morisco 수준) |

### 12.5 전체 로드맵 요약 (진단 후 업데이트)

```mermaid
flowchart TD
    A["EXP-1~3 완료 ✅<br/>H1(G.F.불일치)=❌<br/>H2(i_mag 스케일)=❌<br/>근본원인: 이중계수"]
    B["FIX-1: No-Load FEA<br/>(Motor-CAD I=0, PM only)"]
    C["FIX-2: Regression<br/>(i_mag에서 conductor 기여 분리)"]
    D["k_ih 재계산<br/>(PM-only i_mag + Dirichlet circular)"]
    E{"k_ih ∈ [4, 10]?"}
    F["§4.9 symmetry 적용<br/>(6-slot coupling)"]
    G["§4.8 rotor mag 추가<br/>(L_rot + target mesh)"]
    H["검증: k_ih ≈ 6.06 ±10%"]
    X["FIX-3: V_leak 차감<br/>(deprecated solver 복원)"]

    A --> B
    A --> C
    B --> D
    C --> D
    D --> E
    E -->|Yes| F --> G --> H
    E -->|No| X --> D
```

**핵심 결론:** ~~Green's function 불일치도, i_mag 수식 오류도 아님~~
**수정된 진단 (2026-06-19):**

- FIX-1: i_mag 이중계수 (on-load → PM-only) — ✅ 완료 — k_ih 615→277 (2.2x)
- FIX-B1: I_test 정규화 오류 — ✅ 완료 (이번 세션) — I_test[0]=I → all-I; P_dc 6배 증가
- FIX-D2: 직사각형 G.F. → 원형 G.F. — ✅ 완료 (이번 세션) — 근본 원인 제거

**FIX-D2 근본 원인 분석:**
직사각형 이미지 G.F.에서 `xm_ext=0` (좌치아) 및 `ym_ext=0` (에어갭 측) 소스는
대수적으로 L_ext=0 → 물리적으로 중요한 소스의 기여가 완전히 누락.
`xm_ext=W` (우치아) / `ym_ext=H` (요크) 소스만 급수 절단 오차에 의한
허위 비-zero L_ext로 k_ih=277 전체를 구성. Morisco 원래 원형 G.F.(eq.27/43)로 교체.

**다음 단계:** D1→D2→D3 셀 재실행하여 k_ih 확인.
k_ih ∈ [4,10] 이면 → §4.9 (6-slot 대칭성) → §4.8 (rotor M 소스)
k_ih > 10 이면 → i_mag 크기 재진단 (EXP-4 출력 확인)
