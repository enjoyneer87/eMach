"""
Unified AC copper-loss method comparison for the e10 motor.

Fixed operating point: I_phase = 460 A rms, current phase = 43.33 deg,
speeds = [2000, 4000, 8000, 16000] rpm  (f_e = speed/60 * 4 pole-pairs).

Columns (machine-level AC EXTRA loss, i.e. excluding DC):
  P_skin      : Dowell skin-effect excess, n_cond * R_dc*I^2*(M(xi)-1)
  1D G1corr   : corrected gamma-form thin-conductor prox (== /24 exactly)
  1D G2       : broadband hyperbolic prox (volpe_hybrid_acloss)
  2D G2       : El-Hajji split with (B_w = slot B, B_h = 0)  -> equals 1D G2
                until real FEA Br/Btheta data is plugged in (step B)
  MCAD /24    : Motor-CAD 1D rectangular formula (Volpe 2019 eq.2)
  Ju prox     : ju_hybrid_acloss (Dowell-corrected /24 per layer)
  Cauer       : Cauer ladder P_dc*(Fr-1)  (skin+prox combined, slot diffusion)
  MCAD Hybrid : reference from JEET_ACLoss_4Speed_Map_Summary JSON
                (prox / skin / total), phase-interpolated to 43.33 deg.

B-field model for the analytic columns: 1-D Ampere slot-leakage
  B_k = mu0 * k * I_cond_peak / w_slot   (k = 1..n_L, bottom -> top)
i.e. the same "simple FEA replacement" used by ju/morisco modules.  The
Motor-CAD Hybrid reference instead uses real FEA B per cuboid, which includes
rotor PM field and saturation -> phase dependence that the Ampere model
cannot capture.  Interpretation guidance is printed at the end.

e10 parameters (AF_MCAD_CONTEXT.md, deve10_Comparison_MQS_MS.m):
  48 slots / 8 poles (4 pole pairs), 6-turn hairpin, 2 parallel paths,
  conductor 3.7 x 1.6 mm, active length 150 mm, sigma = 1/1.724e-8 S/m.
  Slot width: Copper_Width + liner/insulation margins ~ 4.5 mm (estimate,
  W_SLOT_MM below - adjust if the exact Slot_Width is known).
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from volpe_hybrid_acloss import (  # noqa: E402
    MU_0,
    SIGMA_CU_20C,
    calc_prox_1D_G1,
    calc_prox_1D_G2,
    calc_prox_2D_G2,
    calc_prox_MCAD_1D,
    calc_skin_loss,
)
from ju_hybrid_acloss import (  # noqa: E402
    HairpinConductor,
    SlotLayout,
    WindingCurrentSpec,
    calculate_acloss_ju,
)
from cauer_modeling import (  # noqa: E402
    calculate_cauer_parameters,
    compute_input_impedance,
)

# ---------------------------------------------------------------------------
# e10 motor fixed parameters (verified against e10Turn6V261.mot + FEA mesh)
# ---------------------------------------------------------------------------
# ── model: e10 HalfSC (k_r = 1.5) ──────────────────────────────────────
# The FEA reference (212-record 4Speed JSON) and the elhajji_b_data mesh
# both come from the SLFEA_Half model, swept at the ABSOLUTE Ref current
# grid (0.1..460 A, i.e. 2/3 of the HalfSC 690 A rating). The previous
# Ref-sized conductor dims here were a model mix-up: the winding-cell
# centroids sit at r = 110-126 mm and the cell width 6.95 mm is 1.5 x the
# Ref slot width (4.63 mm, paper tab:Radial b = 4.6).
W_COND = 5.5665e-3       # conductor width  [m] (1.5 x Ref 3.711 mm)
H_COND = 2.529e-3        # conductor height [m] (1.5 x Ref 1.686 mm)
L_ACTIVE = 0.150         # active stack length [m] (k_a = 1)
SIGMA = SIGMA_CU_20C     # [S/m]
N_SLOTS = 48
POLE_PAIRS = 4
N_LAYERS = 6             # hairpin turns (conductors) per slot (.mot WindingLayers)
PARALLEL_PATHS = 1       # .mot ParallelPaths=1 -> conductor carries full 460 A
W_SLOT_MM = 6.95         # HalfSC slot winding-cell width (measured on this mesh)
W_SLOT = W_SLOT_MM * 1e-3

I_PHASE_RMS = 460.0      # [A]
PHASE_DEG = 43.33        # current phase [deg] (reference interpolation target)
SPEEDS_RPM = [2000, 4000, 8000, 16000]

I_COND_RMS = I_PHASE_RMS / PARALLEL_PATHS   # current per conductor [A]
N_COND_MACHINE = N_SLOTS * N_LAYERS

JSON_CANDIDATES = [
    Path(r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10"
         r"\JEET_ACLoss_4Speed_Map_Summary_20260620_204151.json"),
    Path(__file__).resolve().parent / "JEET_ACLoss_4Speed_Map_Summary_20260620_204151.json",
]


def speed_to_freq(speed_rpm: float) -> float:
    return speed_rpm * POLE_PAIRS / 60.0


def ampere_slot_B(n_L: int = N_LAYERS, w_slot: float = W_SLOT,
                  I_rms: float = I_COND_RMS) -> np.ndarray:
    """Per-layer peak slot-leakage B [T], 1-D Ampere model (bottom=1)."""
    k = np.arange(1, n_L + 1)
    return MU_0 * k * np.sqrt(2.0) * I_rms / w_slot


# ---------------------------------------------------------------------------
# Motor-CAD Hybrid reference from JSON
# ---------------------------------------------------------------------------

def load_mcad_reference(phase_deg: float = PHASE_DEG) -> dict:
    """
    {speed: {'prox_W', 'skin_W', 'total_W', 'mode_rows'}} interpolated in phase.

    Also returns FullFEA totals when present (same hybrid_* key naming in JSON).
    """
    path = next((p for p in JSON_CANDIDATES if p.exists()), None)
    if path is None:
        raise FileNotFoundError(f"reference JSON not found: {JSON_CANDIDATES}")
    records = json.load(open(path, encoding="utf-8"))

    out = {}
    for mode in ("Hybrid", "FullFEA"):
        for spd in SPEEDS_RPM:
            rows = [r for r in records
                    if r["mode"] == mode and r["speed"] == spd
                    and abs(r["current"] - I_PHASE_RMS) < 0.5]
            if not rows:
                continue
            rows.sort(key=lambda r: r["phase"])
            ph = np.array([r["phase"] for r in rows])

            def interp(key):
                vals = [r.get(key) for r in rows]
                if any(v is None for v in vals):
                    return None
                return float(np.interp(phase_deg, ph, np.array(vals, dtype=float)))

            entry = out.setdefault(spd, {})
            if mode == "Hybrid":
                entry["hybrid_prox_W"] = interp("hybrid_prox_W")
                entry["hybrid_skin_W"] = interp("hybrid_skin_W")
                entry["hybrid_total_W"] = interp("hybrid_total_W")
            else:
                # FullFEA(TS) records use ts_* keys in kW
                v = interp("ts_ac_active_only_kW")
                entry["fullfea_total_W"] = v * 1e3 if v is not None else None
                v = interp("ts_dc_active_kW")
                entry["mcad_dc_active_W"] = v * 1e3 if v is not None else None
    out["_json_path"] = str(path)
    return out


# ---------------------------------------------------------------------------
# Per-method machine-level AC extra loss at one speed
# ---------------------------------------------------------------------------

def compute_methods_at_speed(speed_rpm: float) -> dict:
    f_e = speed_to_freq(speed_rpm)
    B_layers = ampere_slot_B()

    # Skin (Dowell M), machine level
    skin = calc_skin_loss(W_COND, H_COND, f_e, L_ACTIVE, I_COND_RMS, SIGMA)
    P_skin = N_COND_MACHINE * float(skin["P_excess_W"])
    P_dc = N_COND_MACHINE * float(np.asarray(skin["P_dc_W"]))

    # Proximity per layer -> slot -> machine
    def per_machine(per_layer):
        return N_SLOTS * float(np.sum(per_layer))

    p_g1 = per_machine(calc_prox_1D_G1(W_COND, H_COND, f_e, L_ACTIVE, B_layers))
    p_g1_m12 = per_machine(calc_prox_1D_G1(W_COND, H_COND, f_e, L_ACTIVE, B_layers,
                                           variant="matlab_12pi2"))
    p_g2 = per_machine(calc_prox_1D_G2(W_COND, H_COND, f_e, L_ACTIVE, B_layers))
    p_2d_g2 = per_machine(calc_prox_2D_G2(W_COND, H_COND, f_e, L_ACTIVE,
                                          Br=B_layers, Btheta=np.zeros_like(B_layers)))
    p_mcad24 = per_machine(calc_prox_MCAD_1D(W_COND, H_COND, f_e, L_ACTIVE, B_layers))

    # Ju hybrid (Dowell-corrected /24 per layer, analytical Ampere B fallback)
    cond = HairpinConductor(b=W_COND, h=H_COND, sigma=SIGMA, L_a=L_ACTIVE)
    slot = SlotLayout(w_slot=W_SLOT, n_L=N_LAYERS, n_slot_phase=N_SLOTS // 3)
    spec = WindingCurrentSpec.sinusoidal(f_e=f_e, I_rms=I_COND_RMS)
    ju = calculate_acloss_ju(cond, slot, spec)
    p_ju_prox = N_SLOTS * float(np.sum(ju["P_prox_per_layer_W"]))
    p_ju_skin = N_SLOTS * float(np.sum(ju["P_skin_per_layer_W"])) - P_dc  # excess only

    # Cauer ladder: Fr = Rac(f)/Rac(DC) of the ladder itself -> AC extra = P_dc*(Fr-1)
    # NOTE: cauer_modeling.analyze_frequency_response normalises by R_dc_per_turn,
    # but the coded ladder has Z(0) = R1 = 24*R_dc (R_c = 8*R_dc, r_coeff(1)=3),
    # which would give Fr(DC) ~ 24. Self-normalising by the ladder's own DC value
    # keeps Fr(DC) = 1; the ladder R_c/L_c derivation itself needs review.
    cauer = calculate_cauer_parameters(d_cond=H_COND, w_slot=W_SLOT, sigma=SIGMA,
                                       l_core=L_ACTIVE, num_turns=N_LAYERS,
                                       num_stages=5)
    Z_in = compute_input_impedance(f_e, cauer["Cauer_R_stages"], cauer["Cauer_L_stages"])
    Z_dc = compute_input_impedance(1e-3, cauer["Cauer_R_stages"], cauer["Cauer_L_stages"])
    Fr = float(np.real(Z_in)) / float(np.real(Z_dc))
    p_cauer = P_dc * (Fr - 1.0)

    return {
        "speed": speed_rpm,
        "f_e": f_e,
        "P_dc_W": P_dc,
        "P_skin_W": P_skin,
        "P_g1_corr_W": p_g1,
        "P_g1_matlab12pi2_W": p_g1_m12,
        "P_g2_W": p_g2,
        "P_2d_g2_W": p_2d_g2,
        "P_mcad24_W": p_mcad24,
        "P_ju_prox_W": p_ju_prox,
        "P_ju_skin_excess_W": p_ju_skin,
        "P_cauer_W": p_cauer,
        "Fr_cauer": Fr,
        "B_top_layer_T": float(B_layers[-1]),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 100)
    print(" e10 AC copper-loss method comparison")
    print(f"   I_phase = {I_PHASE_RMS:.0f} A rms ({I_COND_RMS:.0f} A/conductor, "
          f"a={PARALLEL_PATHS}), phase = {PHASE_DEG} deg")
    print(f"   conductor {W_COND*1e3:.1f} x {H_COND*1e3:.1f} mm, L = {L_ACTIVE*1e3:.0f} mm, "
          f"{N_SLOTS} slots x {N_LAYERS} layers, w_slot = {W_SLOT_MM} mm (estimate)")
    print("=" * 100)

    try:
        ref = load_mcad_reference()
        print(f" MCAD reference: {ref['_json_path']}")
        print(f"   (phase grid 0..90 deg step 18 -> linear interp at {PHASE_DEG} deg)")
    except FileNotFoundError as e:
        print(f" WARNING: {e}\n MCAD reference columns will be empty.")
        ref = {}

    rows = [compute_methods_at_speed(s) for s in SPEEDS_RPM]

    # El-Hajji FEA-B based results (step B), if available
    elhajji_path = Path(__file__).resolve().parent / "elhajji_b_data" / "elhajji_2d_summary.json"
    elhajji = {}
    if elhajji_path.exists():
        for row in json.load(open(elhajji_path, encoding="utf-8")):
            elhajji[row["speed"]] = row
        print(f" El-Hajji FEA-B columns: {elhajji_path}")

    hdr = (f"{'rpm':>6} {'f[Hz]':>7} {'P_dc':>8} | {'P_skin':>8} "
           f"{'G1corr':>9} {'G2':>9} {'MCAD/24':>9} "
           f"{'Ju prox':>9} {'Cauer':>9} | {'2DG1FEA':>9} {'2DG2FEA':>9} | "
           f"{'MCADprox':>9} {'MCADskin':>9} "
           f"{'MCADtot':>9} {'FullFEA':>9}")
    print("\n Machine-level AC extra loss [W] (analytic columns: Ampere slot B model)")
    print(hdr)
    print("-" * len(hdr))
    csv_rows = []
    for r in rows:
        m = ref.get(r["speed"], {})
        mp = m.get("hybrid_prox_W")
        ms = m.get("hybrid_skin_W")
        mt = m.get("hybrid_total_W")
        ff = m.get("fullfea_total_W")

        def s(v, w=9):
            return f"{v:>{w}.1f}" if v is not None else f"{'-':>{w}}"

        eh = elhajji.get(r["speed"], {})
        eh_g1 = eh.get("P_2D_G1_W")
        eh_g2 = eh.get("P_2D_G2_W")
        print(f"{r['speed']:>6} {r['f_e']:>7.1f} {r['P_dc_W']:>8.1f} | "
              f"{r['P_skin_W']:>8.2f} {r['P_g1_corr_W']:>9.1f} {r['P_g2_W']:>9.1f} "
              f"{r['P_mcad24_W']:>9.1f} {r['P_ju_prox_W']:>9.1f} "
              f"{r['P_cauer_W']:>9.1f} | {s(eh_g1)} {s(eh_g2)} | "
              f"{s(mp)} {s(ms)} {s(mt)} {s(ff)}")
        csv_rows.append({**{k: v for k, v in r.items()},
                         "P_2D_G1_FEA_W": eh_g1, "P_2D_G2_FEA_W": eh_g2,
                         "mcad_hybrid_prox_W": mp, "mcad_hybrid_skin_W": ms,
                         "mcad_hybrid_total_W": mt, "fullfea_total_W": ff})

    # MATLAB bug magnitude illustration
    print("\n MATLAB calcHybridProx1D.m bug check (12*pi^2 denominator, now fixed):")
    for r in rows:
        print(f"   {r['speed']:>6} rpm: buggy G1 = {r['P_g1_matlab12pi2_W']:>8.1f} W "
              f"vs corrected {r['P_g1_corr_W']:>9.1f} W "
              f"(x{r['P_g1_corr_W']/max(r['P_g1_matlab12pi2_W'],1e-12):.2f})")

    # Ratios vs MCAD Hybrid prox
    if ref:
        print("\n Analytic prox / MCAD Hybrid prox ratio:")
        print(f"{'rpm':>6} {'G1corr':>8} {'G2':>8} {'MCAD/24':>8} {'Ju':>8} {'Cauer*':>8}")
        for r in rows:
            m = ref.get(r["speed"], {})
            mp = m.get("hybrid_prox_W")
            if not mp:
                continue
            print(f"{r['speed']:>6} {r['P_g1_corr_W']/mp:>8.2f} {r['P_g2_W']/mp:>8.2f} "
                  f"{r['P_mcad24_W']/mp:>8.2f} {r['P_ju_prox_W']/mp:>8.2f} "
                  f"{r['P_cauer_W']/mp:>8.2f}")
        print("   (* Cauer includes skin+prox combined)")

    out_csv = Path(__file__).resolve().parent / "compare_all_methods_result.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"\n [Saved] {out_csv}")

    print("""
 Interpretation notes
 --------------------
 * Analytic columns use the 1-D Ampere slot-leakage B (armature self-field
   only, no rotor PM field / saturation) -> no phase dependence.  The MCAD
   Hybrid reference uses FEA B per cuboid, so exact agreement is not expected;
   same order of magnitude and same frequency trend is the success criterion.
 * G1corr == MCAD/24 exactly (identity).  G2 / Ju saturate at high frequency
   (field penetration), G1 keeps growing with f^2.
 * 2DG1FEA / 2DG2FEA columns come from real FEA B(t) per conductor
   (elhajji_2d_acloss.py, area-weighted <B^2>, 128-step harmonic sum).
   2DG1FEA ~ MCADprox (within ~10% at 2-8 krpm) confirms Motor-CAD's
   magnetic method implements the component-split /24 formula; the gap at
   16 krpm is MCAD's inductance-limited frequency adjustment, which the
   El-Hajji G2 kernel (2DG2FEA) models analytically.
 * Ampere columns use w_slot measured from the FEA mesh (6.95 mm) and the
   .mot winding data (ParallelPaths=1 -> 460 A per conductor).
""")


if __name__ == "__main__":
    main()
