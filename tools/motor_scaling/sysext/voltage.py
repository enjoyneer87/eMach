# -*- coding: utf-8 -*-
"""DC-link voltage axis: rewind (turn scaling), inverter current, and the insulation-system discrete choice.

Rewind rule (thesis ch. 4 §4.9 turn axis): at constant slot area and constant ampere-turns the machine keeps its
flux-map behaviour when N_s ∝ V_dc — the phase current scales 1/k_N, resistance k_N², DC copper loss unchanged,
AC copper loss changes with conductor height (thesis overlay ratio(k_N)), inverter current I_max/k_N.

Insulation system: 800 V drives move from a 0.20–0.25 mm aramid/polyimide (NKN) liner + enamel to thinner
high-PDIV systems (extruded PEEK liner 0.15 mm, PDIV 1.6–1.7 kV). Thinner insulation widens the copper: the slot
allowance of the reference winding is 0.919 mm = 2·0.20 (liner) + 2·0.10 (enamel) + 0.319 (separation/clearance).
Effects modelled: DC loss ∝ 1/w_cu; proximity (AC) loss ∝ w_cu² (rectangular-conductor small-η limit);
thermal path not modelled (stated in the thesis).
"""
from __future__ import annotations

from dataclasses import dataclass

V_REF, NS_REF = 720.0, 6
ALLOWANCE_REF = dict(liner_mm=0.20, enamel_mm=0.10, other_mm=0.319)

INSULATION = {
    "NKN": dict(liner_mm=0.20, enamel_mm=0.10, pdiv_V=900.0, k_W_mK=0.16, note="기준 권선 (aramid/polyimide 라이너)"),
    "PEEK": dict(liner_mm=0.15, enamel_mm=0.10, pdiv_V=1650.0, k_W_mK=0.25, note="압출 PEEK 라이너 150 μm, PDIV 1.6–1.7 kV"),
}


@dataclass
class Rewind:
    v_dc: float
    k_N: float
    Ns: float
    i_scale: float          # phase current relative to the 720 V machine at the same ampere-turns

    @classmethod
    def for_voltage(cls, v_dc, v_ref=V_REF, ns_ref=NS_REF):
        k = v_dc / v_ref
        return cls(v_dc=v_dc, k_N=k, Ns=ns_ref * k, i_scale=1.0 / k)


def allowance_mm(system="NKN"):
    s = INSULATION[system]
    return 2 * s["liner_mm"] + 2 * s["enamel_mm"] + ALLOWANCE_REF["other_mm"]


def copper_width_mm(bs1_mm, system="NKN"):
    return bs1_mm - allowance_mm(system)


def loss_scales(bs1_mm, system="PEEK", ref="NKN"):
    """(DC copper loss scale, AC proximity loss scale, copper width ratio) of ``system`` relative to ``ref``."""
    w0, w1 = copper_width_mm(bs1_mm, ref), copper_width_mm(bs1_mm, system)
    r = w1 / w0
    return dict(dc_scale=1.0 / r, ac_scale=r ** 2, width_ratio=r, w_cu_ref_mm=w0, w_cu_mm=w1)


def pdiv_margin(v_dc, system, overshoot=2.0):
    """PDIV margin against the worst-case turn-to-turn stress (2·V_dc overshoot at the first turns)."""
    return INSULATION[system]["pdiv_V"] / (overshoot * v_dc)
