"""
Ju Hybrid Analytical-FEA Method for AC Copper Loss in Hairpin Windings.

Reference:
  X. Ju et al. (and related works by Volpe et al. 2019):
  "A Hybrid Analytical and FE-Based Method for Calculating AC Eddy Current Losses
  in Hairpin Windings of Electrical Machines"

Physical model overview:
  The Ju hybrid method separates the loss into two mechanisms and handles each analytically:

  1. Skin-effect loss (P_skin):
     Driven by the conductor's own current. Modelled by Dowell's modified formula
     for rectangular conductors (kR_skin).

  2. Proximity-effect loss (P_prox):
     Driven by the external B-field from neighbouring conductors.
     The slot leakage B at each layer is obtained from FEA (or an analytical
     1-D Ampere model) on a no-conductor (empty-slot) mesh for efficiency.

  3. Superposition of current harmonics (Popescu principle):
     Each harmonic current ν contributes independently.  Total loss is obtained by
     superimposing per-harmonic losses, each using a harmonic-specific kR.

  Advantage over Morisco: no PEEC circuit is solved; the FEA is done once (empty-slot),
  making the method highly efficient for design-space exploration.

Key equations
─────────────
  Normalised conductor height:  ξ_ν = h · √(π · ν · f_e · μ₀ · σ)  =  h / δ_ν

  Dowell skin-effect factor:
    M(ξ) = ξ · (sinh 2ξ + sin 2ξ) / (cosh 2ξ − cos 2ξ)

  Dowell proximity-effect factor:
    Q(ξ) = 2ξ · (sinh ξ − sin ξ) / (cosh ξ + cos ξ)

  Total kR for layer m (1 = slot bottom, counting from 1):
    kR(m, ξ) = M(ξ) + ((2m − 1)² / 3) · Q(ξ)   [Dowell layer-position formula]

  Skin-effect loss per conductor at layer m:
    P_skin_m = R_dc · I_ν² · M(ξ_ν)

  Proximity-effect loss per conductor at layer m:
    P_prox_m = σ · (ν·ω_e)² · B_m² · b · h³ / 24 · F_prox(ξ_ν)

  where F_prox corrects the thin-conductor approximation for larger ξ.

  Superposition total (Popescu):
    P_total = Σ_ν  [P_skin(ν) + P_prox(ν)]   summed over all current harmonics

Nomenclature (paper-consistent):
  b, h   : conductor width and height [m]
  n_L    : number of conductor layers in slot
  σ      : conductivity [S/m]
  ω_e    : fundamental angular electrical frequency [rad/s]
  ν      : harmonic order (integer ≥ 1)
  I_ν    : RMS amplitude of ν-th current harmonic [A]
  B_m    : peak slot leakage B at layer m (from FEA or Ampere model) [T]
  L_a    : active stack length [m]
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional
import warnings

MU_0 = 4.0 * np.pi * 1e-7  # [H/m]


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HairpinConductor:
    """Rectangular hairpin conductor properties."""
    b: float        # width [m]  (tangential, ≈ slot width / conductors per row)
    h: float        # height [m] (radial)
    sigma: float    # conductivity [S/m]
    L_a: float      # active stack length [m]


@dataclass(frozen=True)
class SlotLayout:
    """Slot winding arrangement."""
    w_slot: float       # net slot width [m]
    n_L: int            # number of radial conductor layers (= turns per slot here)
    n_slot_phase: int = 1  # number of slots per phase (for phase-level scaling)


@dataclass(frozen=True)
class FEASlotField:
    """
    Slot leakage B-field data extracted from FEA (empty-slot simulation).

    B_layers : array of shape (n_L,) — peak B [T] at each layer (bottom to top).
               If None, the analytical Ampere-law estimate is used automatically.

    Use AnalyticalSlotField to generate B_layers without a real FEA run.
    """
    B_layers: Optional[np.ndarray]  # None → use analytical fallback


@dataclass(frozen=True)
class CurrentHarmonic:
    """A single current harmonic component."""
    order: int        # harmonic order ν (1 = fundamental)
    I_rms: float      # RMS amplitude [A]


@dataclass(frozen=True)
class WindingCurrentSpec:
    """
    Full current specification including fundamental and harmonics.

    Parameters
    ----------
    f_e        : fundamental electrical frequency [Hz]
    harmonics  : list of CurrentHarmonic objects.
                 Must include the fundamental (order=1).
    """
    f_e: float
    harmonics: tuple[CurrentHarmonic, ...]

    @classmethod
    def sinusoidal(cls, f_e: float, I_rms: float) -> "WindingCurrentSpec":
        """Convenience constructor for pure sinusoidal supply."""
        return cls(f_e=f_e, harmonics=(CurrentHarmonic(order=1, I_rms=I_rms),))

    @classmethod
    def with_pwm_harmonics(cls, f_e: float, I1_rms: float,
                           harmonic_pairs: list[tuple[int, float]]) -> "WindingCurrentSpec":
        """
        Convenience constructor for PWM supply.

        Parameters
        ----------
        f_e              : fundamental electrical frequency [Hz]
        I1_rms           : fundamental current RMS [A]
        harmonic_pairs   : list of (order, I_rms_fraction) tuples.
                           I_rms_fraction is a ratio relative to I1_rms.

        Example
        -------
        >>> spec = WindingCurrentSpec.with_pwm_harmonics(
        ...     f_e=266.67, I1_rms=240.0,
        ...     harmonic_pairs=[(3, 0.05), (5, 0.03), (7, 0.02)]
        ... )
        """
        h_list = [CurrentHarmonic(1, I1_rms)]
        for (nu, frac) in harmonic_pairs:
            h_list.append(CurrentHarmonic(order=nu, I_rms=I1_rms * frac))
        return cls(f_e=f_e, harmonics=tuple(h_list))


# ---------------------------------------------------------------------------
# Analytical slot field (Ampere's law 1-D, empty slot)
# ---------------------------------------------------------------------------

def analytical_slot_B(layer_idx: int, n_L: int, w_slot: float,
                      I_rms: float, n_par: int = 1) -> float:
    """
    Peak slot leakage B at mid-height of *layer_idx* (1-based, bottom=1).

    From 1-D Ampere's law in an empty rectangular slot:
      B(y) = μ₀ · H(y),  H(y) = (J · y) / w_slot

    Integrated over layers below layer k, the enclosed peak current is:
      I_enc = layer_idx · n_par · √2 · I_rms

    Returns B_peak [T].
    """
    I_peak = np.sqrt(2.0) * I_rms
    return MU_0 * layer_idx * n_par * I_peak / w_slot


# ---------------------------------------------------------------------------
# Dowell correction functions
# ---------------------------------------------------------------------------

def _dowell_M(xi_val: float) -> float:
    """Skin-effect Dowell factor M(ξ)."""
    if xi_val < 1e-6:
        return 1.0
    return xi_val * (np.sinh(2 * xi_val) + np.sin(2 * xi_val)) / (
        np.cosh(2 * xi_val) - np.cos(2 * xi_val)
    )


def _dowell_Q(xi_val: float) -> float:
    """Proximity-effect Dowell factor Q(ξ)."""
    if xi_val < 1e-6:
        return 0.0
    return 2.0 * xi_val * (np.sinh(xi_val) - np.sin(xi_val)) / (
        np.cosh(xi_val) + np.cos(xi_val)
    )


def skin_depth_nu(f_e: float, nu: int, sigma: float, mu_r: float = 1.0) -> float:
    """Skin depth at ν-th harmonic frequency [m]."""
    f_nu = f_e * nu
    if f_nu <= 0.0:
        return np.inf
    return 1.0 / np.sqrt(np.pi * f_nu * mu_r * MU_0 * sigma)


def xi_nu(h: float, f_e: float, nu: int, sigma: float) -> float:
    """Normalised conductor height ξ_ν = h / δ_ν."""
    return h / skin_depth_nu(f_e, nu, sigma)


# ---------------------------------------------------------------------------
# Per-layer AC loss calculation (Ju hybrid approach)
# ---------------------------------------------------------------------------

def _proximity_correction(xi_val: float) -> float:
    """
    Ratio of actual proximity-effect power to the thin-conductor approximation.

    thin-cond limit of Q:  Q(ξ) = 2ξ·(sinh ξ − sin ξ)/(cosh ξ + cos ξ) → 2ξ·ξ³/6 = ξ⁴/3
    exact (Dowell):        p_prox ∝ Q(ξ)

    Correction factor = Q(ξ) · 3 / ξ⁴   (→ 1 as ξ → 0)

    [FIX 2026-07-14] was Q·3/ξ³, which tends to ξ (→0) at low frequency instead
    of 1, under-estimating the thin-conductor regime by exactly a factor ξ.
    """
    if xi_val < 1e-4:
        return 1.0
    return _dowell_Q(xi_val) * 3.0 / (xi_val ** 4)


def skin_effect_loss_per_cond(cond: HairpinConductor, I_rms: float,
                              f_e: float, nu: int) -> float:
    """
    Skin-effect AC loss for one conductor carrying harmonic current I_ν.

    P_skin = R_dc · I_ν² · M(ξ_ν)   [W]
    """
    R_dc = cond.L_a / (cond.sigma * cond.b * cond.h)
    xi_val = xi_nu(cond.h, f_e, nu, cond.sigma)
    M = _dowell_M(xi_val)
    return R_dc * I_rms**2 * M


def proximity_effect_loss_per_cond(cond: HairpinConductor, B_peak: float,
                                   f_e: float, nu: int) -> float:
    """
    Proximity-effect AC loss for one conductor in external field B_peak.

    p_prox_exact = σ · (ν·ω_e)² · B_peak² · b · h³ / 24 · F_prox(ξ_ν) · L_a  [W]

    The Dowell correction factor F_prox accounts for field penetration at high frequency.
    """
    omega_nu = 2.0 * np.pi * f_e * nu
    xi_val = xi_nu(cond.h, f_e, nu, cond.sigma)
    F_prox = _proximity_correction(xi_val)
    p_per_m = cond.sigma * omega_nu**2 * B_peak**2 * cond.b * cond.h**3 / 24.0 * F_prox
    return p_per_m * cond.L_a


def dowell_kr_at_layer(m: int, xi_val: float) -> float:
    """
    Dowell kR = Rac/Rdc for layer m (1-based from slot bottom).

    kR(m, ξ) = M(ξ) + ((2m − 1)² / 3) · Q(ξ)

    This combines skin effect (M) and proximity effect due to layers below (Q term).
    """
    return _dowell_M(xi_val) + ((2.0 * m - 1.0) ** 2 / 3.0) * _dowell_Q(xi_val)


# ---------------------------------------------------------------------------
# Main Ju hybrid calculation function
# ---------------------------------------------------------------------------

def calculate_acloss_ju(cond: HairpinConductor,
                        slot: SlotLayout,
                        current_spec: WindingCurrentSpec,
                        fea_field: Optional[FEASlotField] = None) -> dict:
    """
    Ju hybrid AC loss calculation (per slot).

    Algorithm
    ---------
    For each harmonic ν:
      For each conductor layer m (1…n_L):
        1. Get B_m : from FEA field or analytical Ampere model.
        2. Compute P_skin_m  = R_dc · I_ν² · M(ξ_ν)
        3. Compute P_prox_m  = σ·(νω)²·B_m²·b·h³/24 · F_prox(ξ_ν) · L_a
        4. Total per conductor: P_m = P_skin_m + P_prox_m

    Superpose over all harmonics (Popescu principle):
      P_total = Σ_ν Σ_m P_m(ν)

    Parameters
    ----------
    cond         : HairpinConductor
    slot         : SlotLayout
    current_spec : WindingCurrentSpec (fundamental + harmonics)
    fea_field    : FEASlotField — if B_layers is None or fea_field is None,
                   analytical Ampere model is used

    Returns
    -------
    dict:
      'P_skin_per_layer_W'      : np.ndarray (n_L,) skin-effect loss per conductor per layer [W]
      'P_prox_per_layer_W'      : np.ndarray (n_L,) proximity-effect loss per conductor per layer [W]
      'P_total_per_layer_W'     : np.ndarray (n_L,) total loss per conductor per layer [W]
      'P_total_slot_W'          : float  total AC loss per slot [W]
      'P_total_phase_W'         : float  total AC loss per phase [W]
      'kR_per_layer'            : np.ndarray (n_L,) effective kR per layer (fundamental only)
      'B_per_layer_T'           : np.ndarray (n_L,) peak B per layer used in calculation [T]
      'P_per_harmonic_W'        : list of (order, P_W) — per-harmonic slot loss
      'R_dc_per_cond_Ohm'       : float  DC resistance per conductor [Ω]
    """
    R_dc = cond.L_a / (cond.sigma * cond.b * cond.h)
    n_L = slot.n_L

    # Determine I_fundamental for DC reference
    I_fund = next((h.I_rms for h in current_spec.harmonics if h.order == 1), 0.0)
    f_e = current_spec.f_e

    # Build B-field per layer (FEA or analytical)
    use_fea = (fea_field is not None and fea_field.B_layers is not None)
    if use_fea:
        if len(fea_field.B_layers) != n_L:
            warnings.warn(
                f"FEA B_layers length {len(fea_field.B_layers)} ≠ n_L={n_L}. "
                "Falling back to analytical Ampere model."
            )
            use_fea = False

    # B-field array (fundamental current only — used for kR display)
    B_per_layer = np.zeros(n_L)
    if use_fea:
        B_per_layer = np.array(fea_field.B_layers, dtype=float)
    else:
        for m in range(1, n_L + 1):
            B_per_layer[m - 1] = analytical_slot_B(m, n_L, slot.w_slot, I_fund)

    # Accumulate loss per layer over all harmonics
    P_skin_per_layer = np.zeros(n_L)
    P_prox_per_layer = np.zeros(n_L)
    per_harmonic = []

    for harm in current_spec.harmonics:
        nu = harm.order
        I_nu = harm.I_rms
        xi_val = xi_nu(cond.h, f_e, nu, cond.sigma)

        P_harm_slot = 0.0
        for m in range(1, n_L + 1):
            # Skin-effect loss for this harmonic at layer m
            p_skin = R_dc * I_nu**2 * _dowell_M(xi_val)

            # Proximity B at layer m for harmonic ν
            if use_fea:
                # Scale FEA B (obtained at I_fund) by the harmonic amplitude ratio
                B_m_nu = B_per_layer[m - 1] * (I_nu / I_fund) if I_fund > 0 else B_per_layer[m - 1]
            else:
                B_m_nu = analytical_slot_B(m, n_L, slot.w_slot, I_nu)

            p_prox = proximity_effect_loss_per_cond(cond, B_m_nu, f_e, nu)

            P_skin_per_layer[m - 1] += p_skin
            P_prox_per_layer[m - 1] += p_prox
            P_harm_slot += p_skin + p_prox

        per_harmonic.append((nu, P_harm_slot))

    P_total_per_layer = P_skin_per_layer + P_prox_per_layer
    P_total_slot = float(np.sum(P_total_per_layer))
    P_total_phase = P_total_slot * slot.n_slot_phase

    # Effective kR per layer (fundamental only, for diagnostic display)
    P_dc_per_cond = R_dc * I_fund**2
    kR_per_layer = P_total_per_layer / P_dc_per_cond if P_dc_per_cond > 0 else np.ones(n_L)

    return {
        "P_skin_per_layer_W": P_skin_per_layer,
        "P_prox_per_layer_W": P_prox_per_layer,
        "P_total_per_layer_W": P_total_per_layer,
        "P_total_slot_W": P_total_slot,
        "P_total_phase_W": P_total_phase,
        "kR_per_layer": kR_per_layer,
        "B_per_layer_T": B_per_layer,
        "P_per_harmonic_W": per_harmonic,
        "R_dc_per_cond_Ohm": R_dc,
    }


def calculate_acloss_ju_popescu(cond: HairpinConductor,
                                slot: SlotLayout,
                                f_e: float,
                                I1_rms: float,
                                harmonic_pairs: list[tuple[int, float]],
                                fea_field: Optional[FEASlotField] = None) -> dict:
    """
    Ju method with Popescu superposition for PWM harmonics.

    P_ac = ρ · (n_L / (b·h)) · [l_e·I_tot² + l_s · Σ_ν kR_ν · I_ν²]

    This is a convenience wrapper around calculate_acloss_ju() that presents
    results in the Popescu formulation for clarity.

    Parameters
    ----------
    f_e             : fundamental electrical frequency [Hz]
    I1_rms          : fundamental RMS current [A]
    harmonic_pairs  : [(order, I_rms), ...] for all harmonics (excluding fundamental)
    fea_field       : optional FEA B-field per layer

    Returns
    -------
    dict (same keys as calculate_acloss_ju, plus Popescu-specific entries)
    """
    all_harmonics = [CurrentHarmonic(1, I1_rms)]
    all_harmonics.extend(CurrentHarmonic(nu, I_nu) for (nu, I_nu) in harmonic_pairs)
    spec = WindingCurrentSpec(f_e=f_e, harmonics=tuple(all_harmonics))

    result = calculate_acloss_ju(cond, slot, spec, fea_field)

    # Popescu-style breakdown
    rho = 1.0 / cond.sigma   # resistivity [Ω·m]
    n_L = slot.n_L
    b, h, L_a = cond.b, cond.h, cond.L_a
    R_dc = cond.L_a / (cond.sigma * b * h)

    popescu_skin = sum(R_dc * (harm.I_rms ** 2) * _dowell_M(xi_nu(h, f_e, harm.order, cond.sigma))
                       for harm in spec.harmonics) * n_L
    popescu_prox = result["P_total_slot_W"] - popescu_skin

    result["P_skin_total_slot_W"] = popescu_skin
    result["P_prox_total_slot_W"] = max(0.0, popescu_prox)

    return result


# ---------------------------------------------------------------------------
# Demonstration  (OP1: 4000 rpm / OP2: 16000 rpm)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("=" * 65)
    print("  Ju Hybrid Analytical-FEA AC Loss Calculator")
    print("  Method: Dowell kR + FEA/Ampere B-field + Popescu superposition")
    print("=" * 65)

    # ── Geometry ─────────────────────────────────────────────────────────────
    cond = HairpinConductor(
        b=5.5e-3,
        h=2.0e-3,
        sigma=5.8e7,
        L_a=0.150,
    )
    slot = SlotLayout(w_slot=6.0e-3, n_L=6, n_slot_phase=8)

    # ── OP1: pure sinusoidal supply ──────────────────────────────────────────
    spec1 = WindingCurrentSpec.sinusoidal(f_e=266.67, I_rms=240.0)

    # ── OP2: sinusoidal (higher speed) ──────────────────────────────────────
    spec2 = WindingCurrentSpec.sinusoidal(f_e=1066.67, I_rms=185.0)

    # ── OP1 with representative PWM harmonics ────────────────────────────────
    spec1_pwm = WindingCurrentSpec.with_pwm_harmonics(
        f_e=266.67, I1_rms=240.0,
        harmonic_pairs=[(5, 0.04), (7, 0.03), (11, 0.02), (13, 0.015)]
    )

    for label, spec in [("OP1 (266.67 Hz, 240 Arms) — sinusoidal", spec1),
                        ("OP2 (1066.67 Hz, 185 Arms) — sinusoidal", spec2),
                        ("OP1 (266.67 Hz) — PWM harmonics included", spec1_pwm)]:
        res = calculate_acloss_ju(cond, slot, spec)
        print(f"\n── {label} ──")
        print(f"  R_dc per conductor = {res['R_dc_per_cond_Ohm']*1e6:.2f} μΩ")
        print(f"  B per layer [mT]: "
              + ", ".join(f"{b*1e3:.2f}" for b in res["B_per_layer_T"]))
        print(f"  {'Layer':<7} {'B [mT]':>10} {'P_skin [mW]':>14} "
              f"{'P_prox [mW]':>14} {'P_total [mW]':>14} {'kR':>8}")
        print("  " + "-" * 67)
        for m in range(slot.n_L):
            print(f"  {m+1:<7} {res['B_per_layer_T'][m]*1e3:>10.3f} "
                  f"{res['P_skin_per_layer_W'][m]*1e3:>14.4f} "
                  f"{res['P_prox_per_layer_W'][m]*1e3:>14.4f} "
                  f"{res['P_total_per_layer_W'][m]*1e3:>14.4f} "
                  f"{res['kR_per_layer'][m]:>8.4f}")

        print(f"\n  Harmonic breakdown (slot total):")
        for (nu, P_nu) in res["P_per_harmonic_W"]:
            print(f"    ν={nu:>3}: {P_nu*1e3:.4f} mW")

        print(f"\n  P_total (slot)  = {res['P_total_slot_W']*1e3:.4f} mW")
        print(f"  P_total (phase) = {res['P_total_phase_W']:.4f} W")

    # ── Frequency sweep: Dowell kR vs frequency per layer ───────────────────
    freqs = np.logspace(1, 4, 300)
    h = cond.h
    sigma = cond.sigma

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, slot.n_L))
    for m in range(1, slot.n_L + 1):
        kR_f = []
        for f in freqs:
            xi_val = xi_nu(h, f, 1, sigma)
            kR_f.append(dowell_kr_at_layer(m, xi_val))
        ax.semilogx(freqs, kR_f, color=colors[m - 1], lw=2,
                    label=f"Layer {m} (m={m})")

    ax.axvline(266.67, ls="--", color="gray", alpha=0.6, label="OP1: 266.67 Hz")
    ax.axvline(1066.67, ls=":", color="gray", alpha=0.6, label="OP2: 1066.67 Hz")
    ax.set_xlabel("Electrical Frequency [Hz]", fontsize=12)
    ax.set_ylabel("Dowell kR = Rac / Rdc", fontsize=12)
    ax.set_title("Ju Method — Dowell kR per Layer vs Frequency", fontsize=13)
    ax.legend(fontsize=9, ncol=2)
    ax.grid(True, which="both", ls="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig("ju_kr_per_layer.png", dpi=150)
    print("\n[Saved] ju_kr_per_layer.png")

    # ── Skin vs Proximity split at OP1 ──────────────────────────────────────
    res1 = calculate_acloss_ju(cond, slot, spec1)
    layers_idx = np.arange(1, slot.n_L + 1)
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.bar(layers_idx - 0.2, res1["P_skin_per_layer_W"] * 1e3,
            width=0.4, label="Skin effect", color="tab:orange", alpha=0.85)
    ax2.bar(layers_idx + 0.2, res1["P_prox_per_layer_W"] * 1e3,
            width=0.4, label="Proximity effect", color="tab:blue", alpha=0.85)
    ax2.set_xlabel("Conductor Layer (1 = slot bottom)", fontsize=12)
    ax2.set_ylabel("AC Loss per Conductor [mW]", fontsize=12)
    ax2.set_title("Ju Method — Skin vs Proximity Loss per Layer\n"
                  "(OP1: 266.67 Hz, 240 Arms)", fontsize=12)
    ax2.legend()
    ax2.grid(True, axis="y", ls="--", alpha=0.5)
    fig2.tight_layout()
    fig2.savefig("ju_skin_vs_prox.png", dpi=150)
    print("[Saved] ju_skin_vs_prox.png")
