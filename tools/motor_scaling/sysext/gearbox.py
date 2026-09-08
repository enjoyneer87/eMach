# -*- coding: utf-8 -*-
"""Single-stage planetary reducer loss law — Aroua, Defreyne, Verbelen, Lhomme, Bouscayrol, Sergeant, Stockman,
"Power loss scaling laws of high-speed planetary reducers", Mechanism and Machine Theory 189 (2023) 105434.

Overall model (paper eqs. 18, 20, 21; Table 4):

    P_loss [W] = a · T_in [N·m] · N_in [rpm]  +  b(ρ, N_max) · N_in [rpm] ^ c(ρ)
    b = b1 + b2 ρ + b3 N_max          c = c1 + c2 ρ
    a = 2.1443e-3   b1 = 9.234e-4   b2 = 6.382e-5   b3 = -8.32e-8   c1 = 2.39   c2 = -0.12

ρ is the gear ratio (N_in/N_out > 1), N_max the maximal input speed [rpm]. The first term is ≈ 2.05 % of the
transmitted power (a·60/2π), the second is the load-independent (churning/windage) loss.
Validity stated by the paper: torque scaling ≤ 4, speed scaling ≥ 0.6, ratio scaling ≤ 2 relative to the tested
reducers (max input speed up to 14,000 rpm, output torque of small planetary units). A traction motor at
130–310 N·m is far outside the torque range — ``validity()`` reports the extrapolation factors so the thesis
can state it. Note also that c(ρ) → 1.26 at ρ = 9.45, which makes the spin term small; the law is used here as
the published reference form, not as a validated prediction.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

COEF = dict(a=2.1443e-3, b1=9.234e-4, b2=6.382e-5, b3=-8.32e-8, c1=2.39, c2=-0.12)
#: the paper's tested envelope used for the extrapolation report (max input speed 14 krpm; torque/ratio of
#: the reference units are not reproduced here — the torque factor is reported against ``t_out_ref``)
REF = dict(n_max_rpm=14000.0, t_out_ref_Nm=50.0, rho_ref=5.0)


def coefficients(rho, n_max_rpm, coef=COEF):
    b = coef["b1"] + coef["b2"] * rho + coef["b3"] * n_max_rpm
    c = coef["c1"] + coef["c2"] * rho
    return coef["a"], b, c


def power_loss(t_in_Nm, n_in_rpm, rho, n_max_rpm, coef=COEF):
    """Reducer loss [W] for input (motor-side) torque and speed arrays."""
    a, b, c = coefficients(rho, n_max_rpm, coef)
    T = np.abs(np.asarray(t_in_Nm, float)); N = np.clip(np.asarray(n_in_rpm, float), 0.0, None)
    return a * T * N + b * np.power(N, c)


def cycle_energy_Wh(n_in_rpm, t_in_Nm, rho, n_max_rpm, dt_s=1.0, coef=COEF):
    """Cycle loss energy [Wh] and its split (load-dependent, load-independent)."""
    a, b, c = coefficients(rho, n_max_rpm, coef)
    T = np.abs(np.asarray(t_in_Nm, float)); N = np.clip(np.asarray(n_in_rpm, float), 0.0, None)
    e_load = float(np.sum(a * T * N) * dt_s / 3600.0)
    e_spin = float(np.sum(b * np.power(N, c)) * dt_s / 3600.0)
    return dict(E_gb_Wh=e_load + e_spin, E_load_Wh=e_load, E_spin_Wh=e_spin, a=a, b=b, c=c)


@dataclass
class Validity:
    k_T: float
    k_N: float
    k_rho: float

    @property
    def inside(self):
        return self.k_T <= 4.0 and self.k_N >= 0.6 and self.k_rho <= 2.0


def validity(t_out_max_Nm, n_max_rpm, rho, ref=REF) -> Validity:
    return Validity(k_T=t_out_max_Nm / ref["t_out_ref_Nm"], k_N=n_max_rpm / ref["n_max_rpm"], k_rho=rho / ref["rho_ref"])
