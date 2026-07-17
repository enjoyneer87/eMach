"""
Morisco et al. (2020) FEA-PEEC Hybrid Model for AC Copper Loss in Hairpin Windings.

Reference:
  D. Morisco, A. Möckel, H. Rapp, and H. Schwertfeger,
  "Hybrid Analytical Model for AC Copper Loss Computation of Hairpin Winding,"
  in Proc. IEEE ICEM, 2020.

Physical model overview:
  Total AC loss = Slot leakage field loss (P_slot) + Rotor PM field loss (P_rotor)

  1. P_slot  : Eddy current loss driven by the slot leakage B-field (due to stator currents).
               Each layer sees a linearly increasing B proportional to the enclosed current.
               Computed per conductor and summed over all layers.

  2. P_rotor : Additional eddy current loss driven by the rotor PM flux that penetrates the
               stator slot.  The rotor B oscillates at harmonics of the electrical frequency
               and must be averaged over one electrical period.

Key rectangular-conductor eddy current formula (low-ξ, i.e., h << δ):
  p_eddy = σ · ω² · B² · w · h³ / 24   [W/m]   (loss per unit axial length, per conductor)

For higher ξ (h comparable to δ), a Dowell correction function F(ξ) is applied.

Naming follows paper Nomenclature:
  b   = conductor width  [m]   (= w_slot / n_parallel_per_row)
  h   = conductor height [m]
  n_L = number of conductor layers in slot
  σ   = electrical conductivity [S/m]
  ω   = angular electrical frequency [rad/s]
  L_a = active (axial) length [m]
  B_k = peak slot leakage B at mid-height of layer k [T]
  B_r = peak rotor PM flux density in the slot [T]
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConductorGeometry:
    """Geometric and material parameters for one rectangular hairpin conductor."""
    b: float          # conductor width  [m]
    h: float          # conductor height [m]
    sigma: float      # electrical conductivity [S/m]  (Cu @ 20°C ≈ 5.8e7)
    L_a: float        # active stack length [m]


@dataclass(frozen=True)
class SlotGeometry:
    """Slot layout for Morisco layer analysis."""
    w_slot: float         # slot width (inner, net) [m]
    n_L: int              # number of conductor layers (radial, bottom→top)
    n_par: int = 1        # parallel conductors per row (typically 1 for hairpin)


@dataclass(frozen=True)
class OperatingPoint:
    """Electrical operating condition."""
    f_e: float            # fundamental electrical frequency [Hz]
    I_rms: float          # phase RMS current [A]
    n_harmonic: int = 1   # highest harmonic order to include (default: fundamental only)
    harmonics: tuple[tuple[int, float], ...] = ()
    # harmonics: sequence of (order ν, amplitude_rms [A]) for current harmonics.
    # If empty, only the fundamental is used.


@dataclass(frozen=True)
class RotorFieldInput:
    """
    Rotor PM field data extracted from FEA (or analytically estimated).

    B_rotor_harmonics: list of (harmonic_order ν_r, B_peak [T]) tuples.
      The rotor field in the slot is dominated by the first few spatial harmonics
      of the PM field.  For a p-pole motor, the dominant slot-penetrating harmonic
      has order p (fundamental) and odd multiples thereof.
    """
    B_rotor_harmonics: tuple[tuple[int, float], ...]  # (order, B_peak [T])


# ---------------------------------------------------------------------------
# Physical helper functions
# ---------------------------------------------------------------------------

MU_0 = 4.0 * np.pi * 1e-7  # [H/m]


def skin_depth(f: float, sigma: float, mu_r: float = 1.0) -> float:
    """
    Skin depth δ [m] for a good conductor.

    δ = 1 / √(π · f · μ · σ)
    """
    if f <= 0.0:
        return np.inf
    mu = mu_r * MU_0
    return 1.0 / np.sqrt(np.pi * f * mu * sigma)


def xi(h: float, f: float, sigma: float, mu_r: float = 1.0) -> float:
    """
    Normalised conductor height ξ = h / δ.

    Used to distinguish thin-conductor (ξ << 1) from thick-conductor (ξ >> 1) regimes.
    """
    delta = skin_depth(f, sigma, mu_r)
    return h / delta


def dowell_M(xi_val: float) -> float:
    """
    Dowell M(ξ): skin-effect correction factor.

    M(ξ) = ξ · (sinh 2ξ + sin 2ξ) / (cosh 2ξ − cos 2ξ)
    """
    if xi_val < 1e-6:
        return 1.0
    return xi_val * (np.sinh(2 * xi_val) + np.sin(2 * xi_val)) / (
        np.cosh(2 * xi_val) - np.cos(2 * xi_val)
    )


def dowell_Q(xi_val: float) -> float:
    """
    Dowell Q(ξ): proximity-effect correction factor per layer.

    Q(ξ) = 2ξ · (sinh ξ − sin ξ) / (cosh ξ + cos ξ)
    """
    if xi_val < 1e-6:
        return 0.0
    return 2.0 * xi_val * (np.sinh(xi_val) - np.sin(xi_val)) / (
        np.cosh(xi_val) + np.cos(xi_val)
    )


def dowell_kr(m: float, xi_val: float) -> float:
    """
    Total AC resistance factor kR = Rac / Rdc for Dowell model.

    kR = M(ξ) + ((2m − 1)² / 3) · Q(ξ)

    Parameters
    ----------
    m   : position index (1 = bottom layer, counted as "m-th group of 1 conductor")
    xi_val : normalised conductor height ξ = h/δ
    """
    return dowell_M(xi_val) + ((2.0 * m - 1.0) ** 2 / 3.0) * dowell_Q(xi_val)


# ---------------------------------------------------------------------------
# Morisco Slot Field Loss  (Step 1)
# ---------------------------------------------------------------------------

def slot_leakage_B(layer_index: int, n_L: int, w_slot: float,
                   I_rms: float, n_par: int = 1) -> float:
    """
    Peak slot leakage B at the mid-height of *layer_index* (1-based, bottom=1).

    Assumes uniform current distribution across all layers (simplified FEA replacement):
      B_k = μ₀ · (k · n_par · I_rms · √2) / w_slot

    This is the 1-D Ampere's law approximation valid for a rectangular slot when
    conductors are uniformly distributed.

    Returns peak (amplitude) B [T].
    """
    I_peak = I_rms * np.sqrt(2.0)
    B_peak = MU_0 * layer_index * n_par * I_peak / w_slot
    return B_peak


def eddy_loss_per_conductor_m_per_m(B_peak: float, omega: float,
                                    b: float, h: float, sigma: float) -> float:
    """
    Eddy current loss per conductor per unit axial length [W/m] for a rectangular
    conductor in an external field B (thin-conductor low-ξ approximation).

    p = σ · ω² · B² · b · h³ / 24

    Valid when ξ = h/δ << 1.  For larger ξ use the Dowell-corrected version.
    """
    return sigma * omega**2 * B_peak**2 * b * h**3 / 24.0


def eddy_loss_per_conductor_m_per_m_dowell(B_peak: float, omega: float,
                                           b: float, h: float, sigma: float,
                                           f: float, layer: int) -> float:
    """
    Dowell-corrected eddy current loss per conductor per unit axial length [W/m].

    Applies the proximity-effect correction D(ξ) to the thin-conductor formula.
    The skin-effect (self-field) term is handled separately via dowell_kr.

    p_prox = (σ · ω² · B² · b · h³ / 24) · F_prox(ξ)

    where F_prox(ξ) = Q(ξ) / (ξ⁴/3)  (ratio of actual proximity loss to thin-cond approx)

    [FIX 2026-07-14] was Q·3/ξ³; Q(ξ) → ξ⁴/3 as ξ→0, so the correct
    normalisation is Q·3/ξ⁴ (F_prox → 1 in the thin-conductor limit).
    """
    xi_val = xi(h, f, sigma)
    if xi_val < 1e-3:
        F_prox = 1.0
    else:
        # Exact proximity loss density (Stoll & Hammond form)
        # P_prox_exact ∝ Q(ξ); thin-conductor approximation ∝ ξ⁴/3
        # → correction factor = Q(ξ) · 3/ξ⁴
        F_prox = dowell_Q(xi_val) * 3.0 / xi_val**4

    return sigma * omega**2 * B_peak**2 * b * h**3 / 24.0 * F_prox


def calculate_slot_field_loss(cond: ConductorGeometry, slot: SlotGeometry,
                              op: OperatingPoint) -> dict:
    """
    Compute AC loss due to slot leakage field (stator current contribution).

    Strategy
    --------
    For each layer k (1 … n_L):
      1. Compute slot leakage B at mid-height of layer k.
      2. Apply Dowell correction for conductor height.
      3. Accumulate total loss [W] per conductor and per slot.

    Parameters
    ----------
    cond : ConductorGeometry
    slot : SlotGeometry
    op   : OperatingPoint  (fundamental + harmonics)

    Returns
    -------
    dict with keys:
      'P_slot_per_conductor_W' : np.ndarray of shape (n_L,) — loss per conductor [W]
      'P_slot_total_W'         : float — total slot field AC loss over all layers [W]
      'B_per_layer_T'          : np.ndarray — peak B at each layer [T]
      'xi_fundamental'         : float — normalised height at fundamental frequency
    """
    omega_e = 2.0 * np.pi * op.f_e
    xi_fund = xi(cond.h, op.f_e, cond.sigma)

    # Build harmonic list: fundamental + optional additional harmonics
    harmonic_list: list[tuple[int, float]] = [(1, op.I_rms)]
    harmonic_list.extend(op.harmonics)

    P_per_layer = np.zeros(slot.n_L)
    B_per_layer = np.zeros(slot.n_L)

    for k in range(1, slot.n_L + 1):
        for (nu, I_nu) in harmonic_list:
            f_nu = op.f_e * nu
            omega_nu = 2.0 * np.pi * f_nu
            B_k = slot_leakage_B(k, slot.n_L, slot.w_slot, I_nu, slot.n_par)
            p_k = eddy_loss_per_conductor_m_per_m_dowell(
                B_peak=B_k, omega=omega_nu,
                b=cond.b, h=cond.h, sigma=cond.sigma,
                f=f_nu, layer=k
            )
            P_per_layer[k - 1] += p_k * cond.L_a   # [W]

        B_per_layer[k - 1] = slot_leakage_B(k, slot.n_L, slot.w_slot, op.I_rms, slot.n_par)

    return {
        "P_slot_per_conductor_W": P_per_layer,
        "P_slot_total_W": float(np.sum(P_per_layer)),
        "B_per_layer_T": B_per_layer,
        "xi_fundamental": xi_fund,
    }


# ---------------------------------------------------------------------------
# Morisco Rotor Field Loss  (Step 2)
# ---------------------------------------------------------------------------

def calculate_rotor_field_loss(cond: ConductorGeometry, slot: SlotGeometry,
                               op: OperatingPoint,
                               rotor: RotorFieldInput) -> dict:
    """
    Compute AC loss due to rotor PM flux penetrating the stator slot.

    The rotor PM produces a B-field that sweeps through the slot at the
    electrical angular velocity ω_e (and its spatial harmonics).
    In the conductor frame, each harmonic ν_r appears at frequency ν_r · f_e.

    The rotor B is assumed uniform across all layers (conservative estimate).
    For more accuracy, pass layer-specific B_rotor from FEA post-processing.

    Formula (per conductor, per unit length):
      p_rotor = σ · (ν_r · ω_e)² · B_r² · b · h³ / 24   · F_prox(ξ_rotor)

    Loss is identical for each layer (no layer dependence for rotor field).

    Returns
    -------
    dict with keys:
      'P_rotor_per_conductor_W' : float — rotor loss per conductor [W]
      'P_rotor_total_W'         : float — total rotor AC loss over all conductors [W]
      'P_rotor_per_harmonic_W'  : list  — breakdown per rotor harmonic
    """
    P_rotor_harmonic = []

    for (nu_r, B_r_peak) in rotor.B_rotor_harmonics:
        f_r_nu = op.f_e * nu_r
        omega_r_nu = 2.0 * np.pi * f_r_nu
        p_rotor_per_m = eddy_loss_per_conductor_m_per_m_dowell(
            B_peak=B_r_peak, omega=omega_r_nu,
            b=cond.b, h=cond.h, sigma=cond.sigma,
            f=f_r_nu, layer=1   # rotor B is not layer-dependent in this model
        )
        P_rotor_harmonic.append(p_rotor_per_m * cond.L_a)

    P_rotor_per_cond = sum(P_rotor_harmonic)
    P_rotor_total = P_rotor_per_cond * slot.n_L  # all conductors in slot

    return {
        "P_rotor_per_conductor_W": P_rotor_per_cond,
        "P_rotor_total_W": float(P_rotor_total),
        "P_rotor_per_harmonic_W": P_rotor_harmonic,
    }


# ---------------------------------------------------------------------------
# Morisco Total AC Loss  (Combined)
# ---------------------------------------------------------------------------

def calculate_total_acloss_morisco(cond: ConductorGeometry, slot: SlotGeometry,
                                   op: OperatingPoint,
                                   rotor: Optional[RotorFieldInput] = None,
                                   n_slots_per_phase: int = 1) -> dict:
    """
    Morisco FEA-PEEC total AC copper loss.

    P_total = P_slot + P_rotor  (per slot, then scaled to per phase)

    Parameters
    ----------
    cond              : conductor geometry and material
    slot              : slot layout
    op                : operating point (frequency, current, harmonics)
    rotor             : rotor PM field data (None → rotor contribution ignored)
    n_slots_per_phase : number of slots per phase (for phase-level total)

    Returns
    -------
    dict with full breakdown
    """
    slot_res = calculate_slot_field_loss(cond, slot, op)
    rotor_res = (calculate_rotor_field_loss(cond, slot, op, rotor)
                 if rotor is not None
                 else {"P_rotor_total_W": 0.0, "P_rotor_per_conductor_W": 0.0,
                       "P_rotor_per_harmonic_W": []})

    P_slot_total = slot_res["P_slot_total_W"]
    P_rotor_total = rotor_res["P_rotor_total_W"]
    P_total_per_slot = P_slot_total + P_rotor_total
    P_total_per_phase = P_total_per_slot * n_slots_per_phase

    return {
        "P_slot_total_W": P_slot_total,
        "P_rotor_total_W": P_rotor_total,
        "P_total_per_slot_W": P_total_per_slot,
        "P_total_per_phase_W": P_total_per_phase,
        "slot_result": slot_res,
        "rotor_result": rotor_res,
        "xi_fundamental": slot_res["xi_fundamental"],
    }


# ---------------------------------------------------------------------------
# Utility: DC resistance for reference
# ---------------------------------------------------------------------------

def dc_resistance_per_conductor(cond: ConductorGeometry) -> float:
    """R_dc [Ω] = L_a / (σ · b · h)"""
    return cond.L_a / (cond.sigma * cond.b * cond.h)


def dc_loss_per_conductor(cond: ConductorGeometry, I_rms: float) -> float:
    """P_dc [W] = R_dc · I²"""
    return dc_resistance_per_conductor(cond) * I_rms**2


# ---------------------------------------------------------------------------
# Demonstration  (OP1: 4000 rpm / OP2: 16000 rpm)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("=" * 65)
    print("  Morisco FEA-PEEC Hybrid AC Loss Calculator")
    print("  Reference: Morisco et al., ICEM 2020")
    print("=" * 65)

    # ── Motor geometry (8p-48s hairpin, representative values) ──────────────
    cond = ConductorGeometry(
        b=5.5e-3,       # conductor width [m]
        h=2.0e-3,       # conductor height [m]
        sigma=5.8e7,    # Cu conductivity at 20°C [S/m]
        L_a=0.150,      # stack length [m]
    )
    slot = SlotGeometry(
        w_slot=6.0e-3,  # slot width [m]
        n_L=6,          # 6 layers (hairpin turns per slot)
        n_par=1,        # 1 parallel conductor per row
    )

    # ── Rotor PM field (from FEA or analytically estimated) ─────────────────
    # Assume fundamental PM B in slot ≈ 0.05 T (typical for open-slot hairpin)
    rotor_field = RotorFieldInput(
        B_rotor_harmonics=(
            (1, 0.05),   # fundamental PM harmonic, 0.05 T peak
            (3, 0.015),  # 3rd spatial harmonic
            (5, 0.008),  # 5th spatial harmonic
        )
    )

    # ── Operating Points ─────────────────────────────────────────────────────
    op1 = OperatingPoint(f_e=266.67, I_rms=240.0)   # 4000 rpm, 240 Arms
    op2 = OperatingPoint(f_e=1066.67, I_rms=185.0)  # 16000 rpm, 185 Arms

    n_slots_phase = 8   # e.g., 48-slot 3-phase → 16 slots/phase, 2-layer → 8

    for label, op in [("OP1 (4000 rpm, 240 Arms)", op1),
                      ("OP2 (16000 rpm, 185 Arms)", op2)]:
        res = calculate_total_acloss_morisco(
            cond, slot, op, rotor_field, n_slots_per_phase=n_slots_phase
        )
        sr = res["slot_result"]
        rr = res["rotor_result"]

        print(f"\n── {label} ──")
        print(f"  f_e = {op.f_e:.2f} Hz,  I_rms = {op.I_rms:.1f} Arms")
        print(f"  Skin depth δ = {skin_depth(op.f_e, cond.sigma)*1e6:.2f} μm,  "
              f"ξ = h/δ = {res['xi_fundamental']:.4f}")
        print(f"\n  [Slot Leakage Field Contribution]")
        for k, (B_k, P_k) in enumerate(zip(sr["B_per_layer_T"],
                                           sr["P_slot_per_conductor_W"]), 1):
            R_dc = dc_resistance_per_conductor(cond)
            P_dc = dc_loss_per_conductor(cond, op.I_rms)
            print(f"    Layer {k}: B={B_k*1e3:.3f} mT,  "
                  f"P_eddy={P_k*1e3:.4f} mW,  "
                  f"kR_effective={P_k/P_dc:.4f}")
        print(f"  Σ P_slot  = {res['P_slot_total_W']*1e3:.4f} mW / slot")

        print(f"\n  [Rotor PM Field Contribution]")
        for idx, (nu_r, B_r) in enumerate(rotor_field.B_rotor_harmonics):
            print(f"    Harmonic {nu_r}: B_r={B_r*1e3:.1f} mT,  "
                  f"P={rr['P_rotor_per_harmonic_W'][idx]*1e3:.4f} mW / cond")
        print(f"  Σ P_rotor = {res['P_rotor_total_W']*1e3:.4f} mW / slot")

        print(f"\n  [Total]")
        print(f"  P_total (slot) = {res['P_total_per_slot_W']*1e3:.4f} mW")
        print(f"  P_total (phase)= {res['P_total_per_phase_W']:.4f} W")

        P_dc_slot = dc_loss_per_conductor(cond, op.I_rms) * slot.n_L
        kR_eff = res["P_total_per_slot_W"] / P_dc_slot
        print(f"  Effective kR   = {kR_eff:.4f}  (P_AC/P_DC per slot)")

    # ── Frequency sweep: kR vs frequency ────────────────────────────────────
    freqs = np.logspace(1, 4, 200)   # 10 Hz → 10 kHz
    kR_list = []
    for f in freqs:
        op_sweep = OperatingPoint(f_e=f, I_rms=240.0)
        res_sweep = calculate_total_acloss_morisco(
            cond, slot, op_sweep, rotor=None, n_slots_per_phase=1
        )
        P_dc_s = dc_loss_per_conductor(cond, 240.0) * slot.n_L
        kR_list.append(res_sweep["P_total_per_slot_W"] / P_dc_s)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.semilogx(freqs, kR_list, color="tab:red", lw=2.5, label="Morisco kR (slot field only)")
    ax.axvline(266.67, ls="--", color="gray", alpha=0.6, label="OP1: 266.67 Hz")
    ax.axvline(1066.67, ls=":", color="gray", alpha=0.6, label="OP2: 1066.67 Hz")
    ax.set_xlabel("Electrical Frequency [Hz]", fontsize=12)
    ax.set_ylabel("Effective kR = P_AC / P_DC", fontsize=12)
    ax.set_title("Morisco Method — AC Resistance Factor vs Frequency", fontsize=13)
    ax.legend()
    ax.grid(True, which="both", ls="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig("morisco_kr_vs_freq.png", dpi=150)
    print("\n[Saved] morisco_kr_vs_freq.png")
