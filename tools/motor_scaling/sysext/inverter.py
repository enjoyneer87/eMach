# -*- coding: utf-8 -*-
"""Two-level VSI losses and a rating-based power-module cost.

``vsi_loss`` is a line-by-line port of ``tools/loss/PE/calcVSILoss.m`` (IGBT + diode, conduction + switching,
third-harmonic injection m3 = m1/6). Default module data are the MATLAB defaults (I_cn = 800 A class); pass a
``module`` dict to override. Current ``i_pk`` is the phase-current *amplitude* (the MATLAB comment says RMS but
the formulas are the standard peak-current expressions).

``module_cost`` prices the inverter by apparent-power rating with a US DRIVE roadmap figure
(power electronics 2020 target 3.3 USD/kW; 2025 integrated inverter target 2.7 USD/kW; DOE EETT roadmap 2017 /
EDTT roadmap 2024). It is a placeholder for a supplier quote — the thesis states it as an assumption.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, Optional

import numpy as np

DEFAULT_MODULE = dict(
    I_cn=800.0, I_ref=400.0,
    Vt_IGBT=0.695, Vt_diode=0.797,
    Ron_IGBT=990.07 * 800.0 ** (-1.003) * 1e-3, Ron_diode=675.61 * 800.0 ** (-1.004) * 1e-3,   # mm2m -> Ohm
    K_i_igbt=0.6, K_i_diode=0.6, Kv_IGBT=1.35, Kv_diode=0.6,
)


def _energies_mJ(i_pk):
    i = np.asarray(i_pk, float)
    e_on = 9.964e-6 * i ** 2 + 0.0156 * i + 0.6221
    e_off = 2.4259e-8 * i ** 3 - 5.7183e-6 * i ** 2 + 0.0357 * i + 1.8700
    e_d = 2.8029e-6 * i ** 2 + 0.0139 * i + 0.9973
    return e_on, e_off, e_d


def vsi_loss(v_dc, f_sw, i_pk, theta_rad, m1, module: Optional[Dict] = None):
    """-> dict(P_cond_IGBT, P_cond_diode, P_sw_IGBT, P_sw_diode, total) [W] — all six switches."""
    md = dict(DEFAULT_MODULE, **(module or {}))
    i = np.asarray(i_pk, float); th = np.asarray(theta_rad, float); m1 = np.asarray(m1, float)
    m3 = m1 / 6.0
    p_ci = 6.0 * ((1 / (2 * math.pi) + m1 * np.cos(th) / 8) * md["Vt_IGBT"] * i
                  + (1 / 8 + m1 * np.cos(th) / (3 * math.pi) - m3 * np.cos(3 * th) / (15 * math.pi)) * md["Ron_IGBT"] * i ** 2)
    p_cd = 6.0 * ((1 / (2 * math.pi) - m1 * np.cos(th) / 8) * md["Vt_diode"] * i
                  + (1 / 8 - m1 * np.cos(th) / (3 * math.pi) + m3 * np.cos(3 * th) / (15 * math.pi)) * md["Ron_diode"] * i ** 2)
    e_on, e_off, e_d = _energies_mJ(i)
    p_si = (f_sw / math.pi) * (e_on + e_off) * (i / md["I_ref"]) ** md["K_i_igbt"] * (v_dc / 300.0) ** md["Kv_IGBT"] / 1e3
    p_sd = (f_sw / math.pi) * e_d * (i / md["I_ref"]) ** md["K_i_diode"] * (v_dc / 300.0) ** md["Kv_diode"] / 1e3
    # MATLAB returns per-leg switching loss (/1000 from mJ); six switches share the same average -> ×6
    p_si, p_sd = 6.0 * p_si, 6.0 * p_sd
    return dict(P_cond_IGBT=p_ci, P_cond_diode=p_cd, P_sw_IGBT=p_si, P_sw_diode=p_sd, total=p_ci + p_cd + p_si + p_sd)


def operating_point(v_d, v_q, i_d, i_q, v_dc):
    """dq (peak) -> (i_pk, theta [rad] between current and voltage vectors, m1 = |v| / (v_dc/2))."""
    i_pk = np.hypot(i_d, i_q); v_pk = np.hypot(v_d, v_q)
    theta = np.arctan2(v_q, v_d) - np.arctan2(i_q, i_d)
    return i_pk, theta, v_pk / (v_dc / 2.0)


@dataclass
class ModuleCost:
    usd_per_kW: float = 3.3          # US DRIVE EETT 2020 power-electronics target; 2.7 = 2025 integrated inverter target
    v_dc: float = 720.0
    fixed_usd: float = 0.0

    def rating_kVA(self, i_max_rms):
        """Inverter apparent rating at the SVPWM linear limit: 3 · (V_dc/√6) · I_rms."""
        return 3.0 * (self.v_dc / math.sqrt(6.0)) * float(i_max_rms) / 1e3

    def cost(self, i_max_rms):
        return self.fixed_usd + self.usd_per_kW * self.rating_kVA(i_max_rms)

    def as_dict(self):
        return asdict(self)
