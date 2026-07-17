"""
Volpe (Motor-CAD) 1D/2D Hybrid AC Copper Loss - corrected MATLAB port.

References:
  G. Volpe, F. Marignetti, M. Popescu, J. Goss,
  "AC Winding Losses in Automotive Traction E-Machines: a New Hybrid
  Calculation Method," 2019.  (= Motor-CAD Hybrid, ProximityLossModel=1)
    eq.(1) circular   : P = L * pi * d^4  * sigma * (w*B)^2 / 128
    eq.(2) rectangular: P = L * w  * h^3  * sigma * (w*B)^2 / 24

  El-Hajji et al., ICEM 2020, "Hybrid model for AC Losses in High Speed
  PMSM for arbitrary flux density waveforms."  (2D Br/Btheta split)
    P = sigma * L * omega^2 * (Br^2 * b*h^3 + Btheta^2 * b^3*h) / 24

MATLAB sources ported (D:/KangDH/EveryMotor/eMach/tools/loss/ACLOSS/):
  calcSkinDepth.m           -> calc_skin_depth          (NOTE: MATLAB returns mm)
  skin/calcSkinDepthModi.m  -> calc_modified_skin_depth
  calcHybridProx1D.m        -> calc_prox_1D_G1          (** bug corrected, see below)
  calcHybridProxImproved1D.m / AnaProx/calcProxg2.m -> calc_prox_1D_G2
  calcHybridACLossWave.m:60-64 (2D combination)     -> calc_prox_2D_G1 / _G2
  MCAD/calcHybridProx1DMCAD.m                       -> calc_prox_MCAD_1D

============================================================================
MATLAB BUG AUDIT (2026-07-14 review) - corrections applied in this module
============================================================================
Correct reference (standard Volpe/El-Hajji, in gamma form with
delta = sqrt(2/(omega*mu*sigma)), gamma = dim/delta):

    P_prox = gamma_w * gamma_h^3 / (6 * mu^2 * sigma) * L * B^2
           = sigma * omega^2 * w * h^3 * L * B^2 / 24          (identical)

[X] calcHybridProx1D.m
      P = (gw*gh^3)/(12*pi^2*mu^2*sigma)*L*B^2
      denominator 12*pi^2 instead of 6  ->  2*pi^2 (~19.7x) UNDER-estimate.
      -> corrected here: /(6*mu^2*sigma)

[X] g1_func in calcHybridACLossWave.m (= AnaProx/calcProxg1.m)
      P = (gw*gh^3)/(6*pi^2*mu^2*sigma)
      denominator 6*pi^2 instead of 6  ->  pi^2 (~9.87x) UNDER-estimate.
      -> corrected here: /(6*mu^2*sigma)

[OK] g2_func (calcProxg2.m / calcHybridProxImproved1D.m)
      g2 = (gw/(sigma*mu^2))*(sinh(gh)-sin(gh))/(cosh(gh)+cos(gh))
      low-xi limit -> gw*gh^3/(6*mu^2*sigma) = correct.  Ported as-is.

[OK] calcHybridProx1DMCAD.m
      P = (1/2)*(1/12)*L*w*h^3*sigma*omega^2*B^2 = /24 formula.  Ported as-is.

[X] calcHybridJouleLossJuHa.m
      kr = varphiXi + (NtCoil^2-0.2)/9 * coeffixi.^4
      coeffixi comes from calckXi4EddyLoss(hc,bc,bm) *without* frequency, so
      the proximity term is frequency-INDEPENDENT (and the Dowell layer form
      (m^2-1)/3 * psi(xi) is replaced by an ad-hoc /9 * xi^4).
      Correct form: kR(m,xi) = M(xi) + ((2m-1)^2/3) * Q(xi)  -- this is what
      ju_hybrid_acloss.dowell_kr_at_layer() implements; use that instead.
============================================================================

All functions are numpy-vectorised over freq_hz and/or B.
Units: SI everywhere (m, Hz, T, W).  B is the PEAK amplitude of a sinusoid.
"""
from __future__ import annotations

import numpy as np

MU_0 = 4.0 * np.pi * 1e-7        # [H/m]
SIGMA_CU_20C = 1.0 / 1.724e-8    # [S/m]  (matches MATLAB elec.T0)


# ---------------------------------------------------------------------------
# Skin depth
# ---------------------------------------------------------------------------

def calc_skin_depth(freq_hz, sigma: float = SIGMA_CU_20C, mu: float = MU_0):
    """
    Classical skin depth  delta = sqrt(2 / (omega * mu * sigma))  [m].

    Port of calcSkinDepth.m (which returns mm; this returns METERS).
    """
    omega = 2.0 * np.pi * np.maximum(np.asarray(freq_hz, dtype=float), 1e-300)
    return np.sqrt(2.0 / (omega * mu * sigma))


def calc_modified_skin_depth(dim1, dim2, freq_hz,
                             sigma: float = SIGMA_CU_20C, mu: float = MU_0):
    """
    Rectangular-conductor anisotropic skin depth (calcSkinDepthModi.m):

        delta' = delta * sqrt((dim1 + dim2) / (2 * dim2))   [m]

    Called as (w, h, f) for the width direction and (h, w, f) for height.
    """
    delta = calc_skin_depth(freq_hz, sigma, mu)
    return delta * np.sqrt((dim1 + dim2) / (2.0 * dim2))


# ---------------------------------------------------------------------------
# Hyperbolic kernel (numerically guarded)
# ---------------------------------------------------------------------------

def _sinh_sin_ratio(x):
    """
    (sinh x - sin x) / (cosh x + cos x), guarded:
      x < 1e-2 : series  x^3/6   (avoids catastrophic cancellation)
      x > 20   : asymptote 1     (avoids overflow)
    """
    x = np.asarray(x, dtype=float)
    scalar = x.ndim == 0
    x = np.atleast_1d(x)
    out = np.empty_like(x)
    small = x < 1e-2
    large = x > 20.0
    mid = ~(small | large)
    xm = x[mid]
    out[mid] = (np.sinh(xm) - np.sin(xm)) / (np.cosh(xm) + np.cos(xm))
    out[small] = x[small] ** 3 / 6.0
    out[large] = 1.0
    return float(out[0]) if scalar else out


def dowell_M(xi):
    """
    Dowell/Field skin-effect factor M(xi) = xi*(sinh 2xi + sin 2xi)/(cosh 2xi - cos 2xi).

    M -> 1 (xi -> 0),  M -> xi (xi -> inf).  Same as calcSkinEffFun.m.
    """
    xi = np.asarray(xi, dtype=float)
    scalar = xi.ndim == 0
    xi = np.atleast_1d(xi)
    out = np.empty_like(xi)
    small = xi < 1e-3
    large = xi > 20.0
    mid = ~(small | large)
    xm = xi[mid]
    out[mid] = xm * (np.sinh(2 * xm) + np.sin(2 * xm)) / (np.cosh(2 * xm) - np.cos(2 * xm))
    out[small] = 1.0 + 4.0 * xi[small] ** 4 / 45.0
    out[large] = xi[large]
    return float(out[0]) if scalar else out


# ---------------------------------------------------------------------------
# 1D proximity  (uniform |B|, no direction split)
# ---------------------------------------------------------------------------

def calc_prox_1D_G1(w, h, freq_hz, lactive, B,
                    sigma: float = SIGMA_CU_20C, mu: float = MU_0,
                    variant: str = "corrected"):
    """
    G1: gamma-form thin-conductor proximity loss [W].

        P = gamma_w * gamma_h^3 / (6 * mu^2 * sigma) * lactive * B^2
          = sigma * omega^2 * w * h^3 * lactive * B^2 / 24     (exactly)

    variant:
      'corrected'    : /(6*mu^2*sigma)          <- correct (default)
      'matlab_12pi2' : /(12*pi^2*mu^2*sigma)    <- calcHybridProx1D.m bug (2pi^2 under)
      'matlab_6pi2'  : /(6*pi^2*mu^2*sigma)     <- g1_func / calcProxg1.m bug (pi^2 under)
    """
    delta = calc_skin_depth(freq_hz, sigma, mu)
    gw = w / delta
    gh = h / delta
    if variant == "corrected":
        den = 6.0 * mu**2 * sigma
    elif variant == "matlab_12pi2":
        den = 12.0 * np.pi**2 * mu**2 * sigma
    elif variant == "matlab_6pi2":
        den = 6.0 * np.pi**2 * mu**2 * sigma
    else:
        raise ValueError(f"unknown variant: {variant!r}")
    return (gw * gh**3) / den * lactive * np.asarray(B, dtype=float) ** 2


def calc_prox_1D_G2(w, h, freq_hz, lactive, B,
                    sigma: float = SIGMA_CU_20C, mu: float = MU_0,
                    use_modified_delta: bool = False):
    """
    G2: broadband hyperbolic proximity loss [W]  (calcProxg2.m - correct as-is).

        g2 = (gamma_w / (sigma*mu^2)) * (sinh gh - sin gh)/(cosh gh + cos gh)
        P  = g2 * lactive * B^2

    Low-xi limit == calc_prox_1D_G1('corrected') == MCAD /24 formula.
    use_modified_delta=True applies the calcSkinDepthModi anisotropic delta'
    (the "prime" gammas of calcProx2DG2Prime.m).
    """
    if use_modified_delta:
        delta_w = calc_modified_skin_depth(w, h, freq_hz, sigma, mu)
        delta_h = calc_modified_skin_depth(h, w, freq_hz, sigma, mu)
    else:
        delta_w = delta_h = calc_skin_depth(freq_hz, sigma, mu)
    gw = w / delta_w
    gh = h / delta_h
    g2 = (gw / (sigma * mu**2)) * _sinh_sin_ratio(gh)
    return g2 * lactive * np.asarray(B, dtype=float) ** 2


def calc_prox_MCAD_1D(w, h, freq_hz, lactive, B,
                      sigma: float = SIGMA_CU_20C):
    """
    Motor-CAD Hybrid 1D rectangular formula [W]  (calcHybridProx1DMCAD.m,
    devCalcMCADHybridACLoss.m - correct as-is; Volpe 2019 eq.(2)):

        P = lactive * w * h^3 * sigma * (omega*B)^2 / 24
    """
    omega = 2.0 * np.pi * np.asarray(freq_hz, dtype=float)
    return lactive * w * h**3 * sigma * (omega * np.asarray(B, dtype=float)) ** 2 / 24.0


def calc_prox_MCAD_1D_round(d, freq_hz, lactive, B,
                            sigma: float = SIGMA_CU_20C):
    """
    Motor-CAD Hybrid 1D circular formula [W]  (Volpe 2019 eq.(1)):

        P = lactive * pi * d^4 * sigma * (omega*B)^2 / 128
    """
    omega = 2.0 * np.pi * np.asarray(freq_hz, dtype=float)
    return lactive * np.pi * d**4 * sigma * (omega * np.asarray(B, dtype=float)) ** 2 / 128.0


# ---------------------------------------------------------------------------
# 2D proximity  (Br / Btheta split, El-Hajji / calcHybridACLossWave.m:60-64)
# ---------------------------------------------------------------------------
# Component pairing convention (matches MATLAB):
#   the B component paired with w*h^3 is the field ALONG the conductor width w
#   ("Br" in calcHybridACLossWave.m); the component paired with w^3*h is the
#   field along the height h ("Btheta").

def calc_prox_2D_G1(w, h, freq_hz, lactive, Br, Btheta,
                    sigma: float = SIGMA_CU_20C, mu: float = MU_0):
    """
    2D G1 (El-Hajji thin-conductor, pi^2 bug corrected) [W]:

        P = lactive * [ gw*gh^3 * Br^2  +  gh*gw^3 * Btheta^2 ] / (6*mu^2*sigma)
          = sigma * lactive * omega^2 * (Br^2 * w*h^3 + Btheta^2 * w^3*h) / 24
    """
    delta = calc_skin_depth(freq_hz, sigma, mu)
    gw = w / delta
    gh = h / delta
    den = 6.0 * mu**2 * sigma
    Br = np.asarray(Br, dtype=float)
    Bt = np.asarray(Btheta, dtype=float)
    return lactive * ((gw * gh**3) * Br**2 + (gh * gw**3) * Bt**2) / den


def calc_prox_2D_G2(w, h, freq_hz, lactive, Br, Btheta,
                    sigma: float = SIGMA_CU_20C, mu: float = MU_0,
                    use_modified_delta: bool = False):
    """
    2D G2 (broadband, calcHybridACLossWave.m:63 - correct as-is) [W]:

        P = lactive * [ g2(gw,gh)*Br^2 + g2(gh,gw)*Btheta^2 ]

    use_modified_delta=True reproduces the "prime" variant (calcProx2DG2Prime.m).
    """
    if use_modified_delta:
        delta_w = calc_modified_skin_depth(w, h, freq_hz, sigma, mu)
        delta_h = calc_modified_skin_depth(h, w, freq_hz, sigma, mu)
    else:
        delta_w = delta_h = calc_skin_depth(freq_hz, sigma, mu)
    gw = w / delta_w
    gh = h / delta_h
    g2_r = (gw / (sigma * mu**2)) * _sinh_sin_ratio(gh)   # pairs with Br^2
    g2_t = (gh / (sigma * mu**2)) * _sinh_sin_ratio(gw)   # pairs with Btheta^2
    Br = np.asarray(Br, dtype=float)
    Bt = np.asarray(Btheta, dtype=float)
    return lactive * (g2_r * Br**2 + g2_t * Bt**2)


# ---------------------------------------------------------------------------
# Volpe 1D Hybrid wrapper: skin (current) + proximity (per-layer B) separate
# ---------------------------------------------------------------------------

def calc_skin_loss(w, h, freq_hz, lactive, I_rms,
                   sigma: float = SIGMA_CU_20C, mu: float = MU_0) -> dict:
    """
    Skin-effect loss of one rectangular conductor carrying I_rms [W].

        P_skin = R_dc * I_rms^2 * M(xi),   xi = h / delta

    Returns dict: P_skin_W, P_dc_W, P_excess_W, M, xi.
    """
    delta = calc_skin_depth(freq_hz, sigma, mu)
    xi = h / delta
    M = dowell_M(xi)
    R_dc = lactive / (sigma * w * h)
    P_dc = R_dc * I_rms**2
    return {
        "P_skin_W": P_dc * M,
        "P_dc_W": P_dc * np.ones_like(np.asarray(M, dtype=float)),
        "P_excess_W": P_dc * (M - 1.0),
        "M": M,
        "xi": xi,
    }


def calc_volpe_1D_hybrid(w, h, freq_hz, lactive, I_rms, B_layers,
                         sigma: float = SIGMA_CU_20C, mu: float = MU_0) -> dict:
    """
    Volpe 1D Hybrid (Motor-CAD ProximityLossModel=1 style), per slot [W].

    - Skin: each of the n_L conductors carries I_rms -> P = n_L * R_dc*I^2*M(xi)
    - Proximity: per-layer peak B (from FEA on a sigma=0 / uniform-J mesh, or
      an Ampere slot model) -> P_k = L * w * h^3 * sigma * (omega*B_k)^2 / 24

    B_layers : array-like of peak |B| per conductor layer [T].

    Returns dict: P_skin_W, P_skin_excess_W, P_prox_W, P_total_W (= skin+prox),
                  P_ac_extra_W (= skin_excess+prox), P_prox_per_layer_W, M, xi.
    """
    B_layers = np.asarray(B_layers, dtype=float)
    n_L = B_layers.size
    skin = calc_skin_loss(w, h, freq_hz, lactive, I_rms, sigma, mu)
    P_prox_layers = calc_prox_MCAD_1D(w, h, freq_hz, lactive, B_layers, sigma)
    P_prox = float(np.sum(P_prox_layers))
    P_skin = float(n_L * skin["P_skin_W"])
    P_skin_excess = float(n_L * skin["P_excess_W"])
    return {
        "P_skin_W": P_skin,
        "P_skin_excess_W": P_skin_excess,
        "P_prox_W": P_prox,
        "P_total_W": P_skin + P_prox,
        "P_ac_extra_W": P_skin_excess + P_prox,
        "P_prox_per_layer_W": P_prox_layers,
        "M": float(skin["M"]),
        "xi": float(skin["xi"]),
    }


# ---------------------------------------------------------------------------
# Self-check demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    w, h, L = 3.7e-3, 1.6e-3, 0.150
    B = 0.05
    print("Volpe hybrid AC-loss module - self checks")
    print(f"  conductor {w*1e3:.1f} x {h*1e3:.1f} mm, L={L*1e3:.0f} mm, B={B} T\n")

    d50 = float(calc_skin_depth(50.0)) * 1e3
    d1k = float(calc_skin_depth(1000.0)) * 1e3
    print(f"  skin depth: delta(50 Hz) = {d50:.3f} mm (ref 9.346), "
          f"delta(1 kHz) = {d1k:.3f} mm (ref 2.090)")

    # Identity 1: corrected G1 == MCAD /24 (exact, all frequencies)
    for f in (10.0, 1000.0, 4000.0):
        g1 = float(calc_prox_1D_G1(w, h, f, L, B))
        m24 = float(calc_prox_MCAD_1D(w, h, f, L, B))
        print(f"  f={f:>6.0f} Hz: G1corr={g1:.6e}  /24={m24:.6e}  "
              f"relerr={abs(g1-m24)/m24:.2e}")

    # Identity 2: G2 low-frequency limit == /24
    f = 1.0
    g2 = float(calc_prox_1D_G2(w, h, f, L, B))
    m24 = float(calc_prox_MCAD_1D(w, h, f, L, B))
    print(f"  G2(1 Hz) vs /24: relerr = {abs(g2-m24)/m24:.2e}")

    # Bug magnitude illustration
    f = 1000.0
    g1c = float(calc_prox_1D_G1(w, h, f, L, B, variant="corrected"))
    g1a = float(calc_prox_1D_G1(w, h, f, L, B, variant="matlab_12pi2"))
    g1b = float(calc_prox_1D_G1(w, h, f, L, B, variant="matlab_6pi2"))
    print(f"\n  MATLAB bug factors @1 kHz: corrected/matlab_12pi2 = {g1c/g1a:.3f} "
          f"(expected {2*np.pi**2:.3f}), corrected/matlab_6pi2 = {g1c/g1b:.3f} "
          f"(expected {np.pi**2:.3f})")

    # 2D consistency: (B, 0) reduces to 1D
    p2d = float(calc_prox_2D_G2(w, h, f, L, B, 0.0))
    p1d = float(calc_prox_1D_G2(w, h, f, L, B))
    print(f"  2D G2(Br=B, Bt=0) == 1D G2: relerr = {abs(p2d-p1d)/p1d:.2e}")

    # Volpe 1D hybrid wrapper smoke test
    res = calc_volpe_1D_hybrid(w, h, 266.67, L, 230.0,
                               B_layers=[0.06, 0.12, 0.18, 0.24, 0.30, 0.36])
    print(f"\n  Volpe 1D hybrid per slot @266.67 Hz, 230 A: "
          f"P_skin={res['P_skin_W']:.2f} W (excess {res['P_skin_excess_W']:.3f} W), "
          f"P_prox={res['P_prox_W']:.2f} W, xi={res['xi']:.3f}")
