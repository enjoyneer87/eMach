"""Kim et al. 2026 (IEEE TIE 73/3, 'Fast Calculation of AC Copper Losses
With PWM Current in EV Propulsion Motors') — sinusoidal part only
(PWM carrier harmonics deliberately excluded).

Implemented pieces, equation numbers per the paper:

* Skin, reactance-limited 2-D (eqs 4-9): solve the complex spatial decay
  constants (M, L) from
      M^2 + L^2 = 2*pi*j*f_n*mu0*sigma
      M*sinh(M*w/2) = L*sinh(L*h/2)
  then E_z = C*cosh(Mx)*cosh(Ly),
      C = (I_n/(4*sigma)) * (M*L)/(sinh(M*w/2)*sinh(L*h/2))
  and P_sk = l * sum_n integral |J_n|^2/sigma dxdy  (J = sigma*E).
  NOTE: P_sk includes the transport (DC) loss of each harmonic; use
  `excess=True` to subtract I_rms^2 * R_dc.

* Proximity, reactance-limited (eq 13):
      P_px = l * sum_{k=r,theta} sum_n
             u_i * B_n(k)^2 / (sigma*mu0^2*delta_n)
             * (sinh(u_j/delta_n)-sin(u_j/delta_n))
             / (cosh(u_j/delta_n)+cos(u_j/delta_n))
  with (B_r: u_i=w, u_j=h) and (B_theta: u_i=h, u_j=w) — the direction
  mapping EXACTLY as printed in the paper (note: this is the transpose
  of the Dowell layer convention; flag `dowell_mapping=True` swaps it
  for sensitivity checks).

* Representative field via KDE (eqs 14-15): Gaussian kernel density of
  the element-wise harmonic field amplitudes, Silverman bandwidth,
  B_rep = argmax of the estimated PDF (the mode), evaluated per
  conductor, per direction, per harmonic.

B amplitude convention: PEAK harmonic amplitudes (matching eq (13)'s
use with the /24-family limit).

Terminology: what the paper calls "MQS-FEA" is the rotor-position
MAGNETOSTATIC sweep (no conductor eddy currents) — identical to the
MS-FEA of our manuscript's nomenclature. Strictly, MQS denotes the
quasi-static formulation WITH the induced-current term (what TS-FEA
solves), so the field source here is MS, not MQS.

Frozen permeability: in the paper FP is used ONLY for the PWM stage
(freeze mu from the fundamental MS solution, solve the linear
perturbation for carrier-harmonic slot leakage). This sinusoidal-only
implementation needs no FP step — the element B(t) comes from the
nonlinear MS rotor-position sweep, so saturation is already embedded.
For a future PWM extension the FEA export's per-element Mur column
provides the frozen-permeability map directly.

Direction-mapping empirics (kim_mapping_check.py, HalfSC 460 A):
the as-printed (u_i, u_j) assignment of eq (13) overestimates TS-FEA
by 2.3x at low speed, while the Dowell layer mapping (swap) reproduces
TS-FEA within +-15% at all speeds — pending confirmation against the
original manuscript, prefer `dowell_mapping=True`.

Skin validity domain (kim_skin_check.py cross-validation, HalfSC):
the low-frequency excess coefficient of the manuscript's k_s^rect
(Lin 2022, P = 2 k_s (f J_rms)^2 V_cu) and of the 1-D Dowell factor
M(xi)-1 (xi = h/delta) agree to 0.05% — mutually validated. The
cosh(Mx)cosh(Ly) form here is a CORNER-crowding solution: at the
sinusoidal fundamental (xi ~ 0.4-1.3) it yields only ~0.17x the
Dowell excess (~0.12x the Motor-CAD skin column), and NO eq (5)
constraint variant (tanh forms, swapped dims, Ampere-weighted) reaches
the 1-D slot law (best 0.70x). It crosses ~1x Dowell only around
xi ~ 4-5, i.e. in the PWM carrier band the paper targets. For
fundamental-only totals use Dowell / k_s^rect for skin; keep
`skin_loss_kim` for PWM-band harmonics. (Motor-CAD's own skin column
sits ~1.5x above copper-dims Dowell — closest simple explanation is
insulated-dims Dowell at 0.86-0.90x, exact recipe unidentified.)
"""
from __future__ import annotations

import numpy as np

MU0 = 4e-7 * np.pi


# ── skin: complex decay constants (eq 5) ───────────────────────────────

def solve_ml(f_hz: float, w: float, h: float, sigma: float,
             n_iter: int = 60) -> tuple[complex, complex]:
    """Solve M, L of eq (5) by damped fixed-point iteration.

    Start from the symmetric guess M = L = sqrt(c/2) and alternate
    M -> from the transcendental constraint with L = sqrt(c - M^2).
    """
    c = 2j * np.pi * f_hz * MU0 * sigma
    w2, h2 = w / 2.0, h / 2.0

    m = np.sqrt(c / 2.0)
    for _ in range(n_iter):
        el = np.sqrt(c - m * m)
        # residual g(M) = M sinh(M w2) - L sinh(L h2); Newton in M with
        # dL/dM = -M/L
        g = m * np.sinh(m * w2) - el * np.sinh(el * h2)
        dg = (np.sinh(m * w2) + m * w2 * np.cosh(m * w2)
              + (m / el) * (np.sinh(el * h2)
                            + el * h2 * np.cosh(el * h2)))
        step = g / dg
        # damping keeps the iteration on the principal branch
        m = m - 0.7 * step
        if abs(step) < 1e-14 * max(1.0, abs(m)):
            break
    el = np.sqrt(c - m * m)
    return m, el


def skin_loss_kim(i_amp: float, f_hz: float, w: float, h: float,
                  l_active: float, sigma: float, n_grid: int = 80,
                  excess: bool = False) -> float:
    """Reactance-limited skin loss of one conductor [W] (eqs 6-9).

    i_amp : PEAK amplitude of the (fundamental) current harmonic.
    excess=True subtracts the transport loss I_rms^2 * R_dc.
    """
    m, el = solve_ml(f_hz, w, h, sigma)
    w2, h2 = w / 2.0, h / 2.0
    c_const = (i_amp / (4.0 * sigma)) * (m * el
                                         / (np.sinh(m * w2)
                                            * np.sinh(el * h2)))
    x = np.linspace(-w2, w2, n_grid)
    y = np.linspace(-h2, h2, n_grid)
    xg, yg = np.meshgrid(x, y)
    j_abs2 = np.abs(sigma * c_const
                    * np.cosh(m * xg) * np.cosh(el * yg)) ** 2
    # time-average of a phasor field: <|J|^2>/2
    p = l_active * np.trapz(np.trapz(j_abs2, x, axis=1), y) / (2.0 * sigma)
    if excess:
        r_dc = l_active / (sigma * w * h)
        p -= 0.5 * i_amp**2 * r_dc
    return float(p)


# ── proximity: reactance-limited kernel (eq 13) ────────────────────────

def _kernel(u_over_delta: np.ndarray) -> np.ndarray:
    return ((np.sinh(u_over_delta) - np.sin(u_over_delta))
            / (np.cosh(u_over_delta) + np.cos(u_over_delta)))


def prox_loss_kim(b_r: np.ndarray, b_th: np.ndarray, f_n: np.ndarray,
                  w: float, h: float, l_active: float, sigma: float,
                  dowell_mapping: bool = False) -> float:
    """Proximity loss of one conductor [W] per eq (13).

    b_r, b_th : PEAK amplitudes of the radial / tangential field
                harmonics (arrays over harmonic order, aligned with f_n).
    Paper mapping: (B_r: u_i=w, u_j=h), (B_theta: u_i=h, u_j=w).
    dowell_mapping=True swaps u_j to the Dowell layer convention.
    """
    delta = 1.0 / np.sqrt(np.pi * MU0 * sigma * f_n)
    if not dowell_mapping:
        p_r = w * b_r**2 / (sigma * MU0**2 * delta) * _kernel(h / delta)
        p_t = h * b_th**2 / (sigma * MU0**2 * delta) * _kernel(w / delta)
    else:
        p_r = h * b_r**2 / (sigma * MU0**2 * delta) * _kernel(w / delta)
        p_t = w * b_th**2 / (sigma * MU0**2 * delta) * _kernel(h / delta)
    return float(l_active * np.sum(p_r + p_t))


# ── KDE representative field (eqs 14-15) ───────────────────────────────

def kde_representative(samples: np.ndarray,
                       n_eval: int = 256) -> float:
    """Mode of the Gaussian-KDE PDF with Silverman bandwidth (eq 15)."""
    x = np.asarray(samples, float).ravel()
    n = x.size
    if n == 0:
        return 0.0
    if n == 1 or np.ptp(x) < 1e-15:
        return float(x[0])
    sd = np.std(x, ddof=1)
    iqr = np.subtract(*np.percentile(x, [75, 25]))
    a = min(sd, iqr / 1.349) if iqr > 0 else sd
    bw = 0.9 * a * n ** (-0.2)
    if bw <= 0:
        return float(np.mean(x))
    grid = np.linspace(x.min() - 3 * bw, x.max() + 3 * bw, n_eval)
    pdf = np.exp(-0.5 * ((grid[:, None] - x[None, :]) / bw) ** 2).sum(axis=1)
    return float(grid[np.argmax(pdf)])


def region_representative_harmonics(elements: list, n_keep: int | None
                                    = None) -> tuple[np.ndarray, np.ndarray]:
    """Per-harmonic KDE-representative PEAK amplitudes (Bx, By).

    elements : list of dicts with 'Bx_T'/'By_T' time series (equal step
    count); returns (rep_bx[m], rep_by[m]) for m = 1..N/2.
    """
    bx = np.array([e['Bx_T'] for e in elements])
    by = np.array([e['By_T'] for e in elements])
    n = bx.shape[1]
    ax = 2.0 * np.abs(np.fft.rfft(bx, axis=1))[:, 1:] / n   # peak amps
    ay = 2.0 * np.abs(np.fft.rfft(by, axis=1))[:, 1:] / n
    if n_keep is not None:
        ax, ay = ax[:, :n_keep], ay[:, :n_keep]
    rep_x = np.array([kde_representative(ax[:, m])
                      for m in range(ax.shape[1])])
    rep_y = np.array([kde_representative(ay[:, m])
                      for m in range(ay.shape[1])])
    return rep_x, rep_y
