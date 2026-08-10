"""How well is the air-gap field described by harmonics? A diagnostic, not an operator.

In a source-free annular gap A satisfies Laplace, so the exact solution space is

    A(r, theta) = sum_n ( a_n r^n + b_n r^-n ) exp(i n theta)

and on an anti-periodic 1/(2p) sector only certain orders can exist at all
(4, 12, 20, ... for an 8-pole machine modelled over one pole). Anything outside
that set is discretisation, not physics. That makes "how much energy sits outside
the admissible orders" a measurable definition of air-gap noise, instead of an
impression.

Two cautions this module exists to make concrete, both measured on a 48-slot/
8-pole IPM (752 band elements, 0.17 mm band, 6 held-out geometries x 5 rotor
positions):

1. The radial r^(+/-n) basis is UNIDENTIFIABLE in a thin band. With
   u = r/r0 in [0.9988, 1.0012], u^n and u^-n are numerically the same function,
   so adding the radial degrees of freedom is pure collinearity: it moved the Br
   residual from 8.33% to 8.45%, i.e. it got worse. An air-gap-element style
   representation pays off when it replaces the gap mesh, not when it is fitted
   on top of one already 29 layers deep.

2. The field is not a function of theta alone. Even an essentially interpolating
   basis (all n <= 350, 700 parameters on 752 elements) leaves Br at 7.13% and
   Btheta at 11.49%: elements at the same angle but different radius genuinely
   disagree. Any "project the gap onto harmonics and use it as a guide" scheme
   discards that, and it is a large fraction of the signal.

Measured residuals (mean over the 6 geometries, fraction of field RMS):

    component   admissible 4*odd   all n<=200   all n<=350
    Br                   11.33%        9.12%        7.13%
    Btheta               23.78%       16.45%       11.49%
"""
from __future__ import annotations

from typing import Dict, Iterable, Sequence

import numpy as np


def admissible_orders(pole_pairs: int, n_harmonics: int = 24) -> np.ndarray:
    """Spatial orders permitted on an anti-periodic one-pole sector.

    For a machine with ``pole_pairs`` p modelled over one pole, the anti-periodic
    condition admits odd multiples of p: p, 3p, 5p, ... An 8-pole machine (p = 4)
    therefore admits 4, 12, 20, ...
    """
    return np.array([pole_pairs * (2 * m + 1) for m in range(n_harmonics)], dtype=int)


def _design(phi: np.ndarray, orders: Iterable[int]) -> np.ndarray:
    cols = []
    for n in orders:
        cols += [np.cos(n * phi), np.sin(n * phi)]
    return np.column_stack(cols)


def harmonic_residual(phi: np.ndarray, values: np.ndarray,
                      orders: Iterable[int]) -> Dict[str, object]:
    """Least-squares fit of ``values(phi)`` to the given orders.

    Returns the coefficients and the residual as a fraction of the signal norm --
    the share of the field that those orders cannot express.
    """
    d = _design(np.asarray(phi, float), orders)
    v = np.asarray(values, dtype=np.float64)
    coef, *_ = np.linalg.lstsq(d, v, rcond=None)
    fit = d @ coef
    resid = v - fit
    return {
        "coefficients": coef,
        # The reconstruction is returned so callers can score it as a PREDICTOR
        # against the truth field, in whatever metric their gate uses. A residual
        # norm and a pooled nRMSE of |B| are not the same statistic, and only the
        # latter is comparable to a benchmark number.
        "reconstruction": fit,
        "residual_pct": float(100.0 * np.linalg.norm(resid) / np.linalg.norm(v)),
        "n_params": int(d.shape[1]),
    }


def age_fit(phi: np.ndarray, r: np.ndarray, b_r: np.ndarray, b_theta: np.ndarray,
            orders: Iterable[int]) -> Dict[str, object]:
    """Air-gap-element style fit: one coefficient set for BOTH components.

    A = sum ( a_n u^n + b_n u^-n ) cos(n theta) + ( c_n u^n + d_n u^-n ) sin(n theta),
    with u = r / mean(r) for conditioning, then Br = (1/r) dA/dtheta and
    Btheta = -dA/dr. Fitting both components from one coefficient set is what
    makes it a field representation rather than two independent curve fits.

    Expect this to be ill-conditioned on a thin band -- see the module docstring.
    """
    phi = np.asarray(phi, float)
    r = np.asarray(r, float)
    u = r / r.mean()
    dbr, dbt = [], []
    for n in orders:
        for rad, dsign in ((u ** n, n), (u ** (-n), -n)):
            g = rad / r
            dbr += [-n * g * np.sin(n * phi), n * g * np.cos(n * phi)]
            dbt += [-dsign * g * np.cos(n * phi), -dsign * g * np.sin(n * phi)]
    d = np.vstack([np.array(dbr).T, np.array(dbt).T])
    v = np.concatenate([np.asarray(b_r, float), np.asarray(b_theta, float)])
    coef, *_ = np.linalg.lstsq(d, v, rcond=None)
    resid = v - d @ coef
    n1 = np.asarray(b_r).size
    return {
        "coefficients": coef,
        "residual_pct": float(100.0 * np.linalg.norm(resid) / np.linalg.norm(v)),
        "residual_pct_br": float(100.0 * np.linalg.norm(resid[:n1]) / np.linalg.norm(b_r)),
        "residual_pct_btheta": float(100.0 * np.linalg.norm(resid[n1:]) / np.linalg.norm(b_theta)),
        "n_params": int(d.shape[1]),
        "u_range": (float(u.min()), float(u.max())),
    }


def smoothness_report(phi: np.ndarray, r: np.ndarray, b_r: np.ndarray,
                      b_theta: np.ndarray, pole_pairs: int,
                      free_orders: Sequence[int] = (200, 350)) -> Dict[str, object]:
    """Admissible-order residual against progressively freer bases.

    The gap between the admissible residual and the free-basis residual is
    content in orders symmetry forbids; whatever the freest basis still cannot
    explain is radial variation and element-level scatter. Report both -- they
    have different causes and different remedies.
    """
    adm = admissible_orders(pole_pairs)
    out: Dict[str, object] = {"pole_pairs": pole_pairs, "n_band_elements": int(np.size(phi))}
    for name, vals in (("b_r", b_r), ("b_theta", b_theta)):
        entry = {"admissible": harmonic_residual(phi, vals, adm)["residual_pct"]}
        for m in free_orders:
            entry[f"all_n_le_{m}"] = harmonic_residual(phi, vals, range(1, m + 1))["residual_pct"]
        entry["rms_T"] = float(np.sqrt(np.mean(np.asarray(vals, float) ** 2)))
        out[name] = entry
    out["age_admissible"] = age_fit(phi, r, b_r, b_theta, adm)["residual_pct_br"]
    return out
