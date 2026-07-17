"""
El-Hajji step (B) - stage 2: 2D hybrid AC loss from extracted FEA B(t).

Consumes elhajji_b_data/<case>.json (from elhajji_2d_fea_extract.py) and
computes, per conductor and machine total:

  2D G2 : P = L * sum_k [ g2(gw,gh)|f_k * Bw_k^2 + g2(gh,gw)|f_k * Bh_k^2 ]
  2D G1 : thin-conductor split form
          P = sigma*L*omega_k^2*(Bw_k^2 * w*h^3 + Bh_k^2 * w^3*h)/24
  1D /24: P = sigma*L*omega_k^2*(w*h^3/24) * |B|_k^2   (MCAD Hybrid style,
          no direction split - reproduces ACConductorLoss_MagneticMethod)

Frame convention:
  Conductor width w (3.7 mm) lies along the machine TANGENTIAL direction,
  height h (1.6 mm) along RADIAL.  The component paired with w*h^3 is the
  field along the width -> B_w = B_tangential, B_h = B_radial.

Harmonics: the 128 time-indexed steps span exactly one electrical cycle
(128 x 0.7031 deg mech = 90 deg mech = 360 deg elec), so rFFT bin k is
harmonic order k of f_e.  Peak amplitude A_k = 2|c_k|/N (Nyquist |c|/N).

Machine scaling: model is a 1/8 sector (6 of 48 slots) -> factor 8.

Validation anchor: the 1D /24 column evaluated at the same grid phase should
land near the Motor-CAD hybrid_prox_W of the summary JSON (same formula,
same B source; differences come from cuboid-vs-region averaging and
fundamental-vs-harmonic-sum handling).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from volpe_hybrid_acloss import (  # noqa: E402
    SIGMA_CU_20C,
    calc_prox_1D_G1,
    calc_prox_2D_G1,
    calc_prox_2D_G2,
    calc_prox_MCAD_1D,
)

DATA_DIR = Path(__file__).resolve().parent / "elhajji_b_data"

# conductor dims from e10Turn6V261.mot (Copper_Width/Copper_Height)
W_COND = 3.711e-3
H_COND = 1.686e-3
L_ACTIVE = 0.150
SIGMA = SIGMA_CU_20C
POLE_PAIRS = 4
MODEL_SYMMETRY = 8          # 6 of 48 slots modelled
PHASE_TARGET = 43.33

# Region naming note (verified from centroids): the LETTER A..F is the radial
# layer (A = slot bottom r=126 mm, F = slot opening r=110 mm), the NUMBER 1..6
# is the slot index (7.5 deg pitch). Each region is the homogenised winding
# cell of one turn (~6.95 x 3.14 mm); copper (3.711 x 1.686 mm) sits inside.

CASES = {
    2000: [36.0, 54.0],
    4000: [36.0, 54.0],
    8000: [18.0, 54.0],
    16000: [36.0, 54.0],
}


def fft_peak_amplitudes(x: np.ndarray) -> np.ndarray:
    """Periodic samples -> harmonic peak amplitudes (DC dropped, len N//2)."""
    n = len(x)
    spec = np.fft.rfft(np.asarray(x, dtype=float))
    amp = 2.0 * np.abs(spec) / n
    if n % 2 == 0:
        amp[-1] = np.abs(spec[-1]) / n
    return amp[1:]


def load_case(speed: int, phase: float) -> dict:
    p = DATA_DIR / f"Hybrid_Speed_{speed}RPM_460.0A_{phase}deg.json"
    if not p.exists():
        raise FileNotFoundError(p)
    return json.load(open(p, encoding="utf-8"))


def analyze_case(speed: int, phase: float) -> dict:
    data = load_case(speed, phase)
    f_e = speed * POLE_PAIRS / 60.0

    per_cond = []
    tot = {"P_2D_G2": 0.0, "P_2D_G1": 0.0, "P_1D_24_harm": 0.0,
           "P_1D_24_fund": 0.0, "P_2D_G2_meanB": 0.0}

    for reg in data["regions"]:
        # conductor orientation frame from region centroid
        cx, cy = reg["centroid_xy_mm"]
        r = float(np.hypot(cx, cy))
        ct, st = cx / r, cy / r

        def to_frame(bx, by):
            b_rad = bx * ct + by * st      # along conductor HEIGHT h
            b_tan = -bx * st + by * ct     # along conductor WIDTH  w
            return b_tan, b_rad

        def trim(x):
            n = len(x)
            return x[-(n - 1):] if n % 2 == 1 else x

        # --- area-weighted <B^2> per harmonic (per-element FFT) ------------
        elements = reg.get("elements") or []
        if elements:
            w_e = np.array([e["w_mm2"] for e in elements])
            Aw2 = None
            Ah2 = None
            for e, w in zip(elements, w_e):
                bx = trim(np.array(e["Bx_T"], dtype=float))
                by = trim(np.array(e["By_T"], dtype=float))
                b_w, b_h = to_frame(bx, by)
                aw = fft_peak_amplitudes(b_w)
                ah = fft_peak_amplitudes(b_h)
                if Aw2 is None:
                    Aw2 = w * aw**2
                    Ah2 = w * ah**2
                else:
                    Aw2 += w * aw**2
                    Ah2 += w * ah**2
            Aw2 /= w_e.sum()               # <Bw^2> per harmonic [T^2]
            Ah2 /= w_e.sum()
        else:  # fallback: region-mean series (v1 data)
            bx = trim(np.array(reg["Bx_T"], dtype=float))
            by = trim(np.array(reg["By_T"], dtype=float))
            b_w, b_h = to_frame(bx, by)
            Aw2 = fft_peak_amplitudes(b_w) ** 2
            Ah2 = fft_peak_amplitudes(b_h) ** 2

        k = np.arange(1, len(Aw2) + 1)
        f_k = k * f_e

        # loss coefficients are linear in B^2 -> pass sqrt(<B^2>)
        Aw = np.sqrt(Aw2)
        Ah = np.sqrt(Ah2)
        p_2d_g2 = float(np.sum(calc_prox_2D_G2(
            W_COND, H_COND, f_k, L_ACTIVE, Br=Aw, Btheta=Ah)))
        p_2d_g1 = float(np.sum(calc_prox_2D_G1(
            W_COND, H_COND, f_k, L_ACTIVE, Br=Aw, Btheta=Ah)))
        A_mag = np.sqrt(Aw2 + Ah2)
        p_24_harm = float(np.sum(calc_prox_MCAD_1D(
            W_COND, H_COND, f_k, L_ACTIVE, A_mag)))
        p_24_fund = float(calc_prox_MCAD_1D(
            W_COND, H_COND, f_e, L_ACTIVE, float(A_mag[0])))

        # region-mean variant (for the <B>^2 vs <B^2> spatial-variance effect)
        bx = trim(np.array(reg["Bx_T"], dtype=float))
        by = trim(np.array(reg["By_T"], dtype=float))
        b_w, b_h = to_frame(bx, by)
        Aw_m = fft_peak_amplitudes(b_w)
        Ah_m = fft_peak_amplitudes(b_h)
        p_2d_g2_meanB = float(np.sum(calc_prox_2D_G2(
            W_COND, H_COND, f_k, L_ACTIVE, Br=Aw_m, Btheta=Ah_m)))

        per_cond.append({
            "name": reg["name"],
            "Bw_fund_T": float(Aw[0]), "Bh_fund_T": float(Ah[0]),
            "P_2D_G2_W": p_2d_g2, "P_2D_G1_W": p_2d_g1,
            "P_1D_24_harm_W": p_24_harm, "P_1D_24_fund_W": p_24_fund,
        })
        tot["P_2D_G2"] += p_2d_g2
        tot["P_2D_G1"] += p_2d_g1
        tot["P_1D_24_harm"] += p_24_harm
        tot["P_1D_24_fund"] += p_24_fund
        tot["P_2D_G2_meanB"] += p_2d_g2_meanB

    return {
        "speed": speed, "phase": phase, "f_e": f_e,
        "machine": {k: v * MODEL_SYMMETRY for k, v in tot.items()},
        "per_conductor": per_cond,
        "n_regions": len(data["regions"]),
    }


def load_mcad_reference() -> list[dict]:
    p = Path(r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10"
             r"\JEET_ACLoss_4Speed_Map_Summary_20260620_204151.json")
    return json.load(open(p, encoding="utf-8"))


def mcad_prox_at(records, speed, phase) -> float | None:
    rows = [r for r in records
            if r["mode"] == "Hybrid" and r["speed"] == speed
            and abs(r["current"] - 460.0) < 0.5]
    rows.sort(key=lambda r: r["phase"])
    if not rows:
        return None
    ph = np.array([r["phase"] for r in rows])
    v = np.array([r["hybrid_prox_W"] for r in rows])
    return float(np.interp(phase, ph, v))


def main():
    ref = load_mcad_reference()

    print("=" * 96)
    print(" El-Hajji 2D hybrid AC loss from FEA B(t)  (e10, 460 A, machine level [W])")
    print(f"   conductor {W_COND*1e3:.1f} x {H_COND*1e3:.1f} mm, L={L_ACTIVE*1e3:.0f} mm, "
          f"1/{MODEL_SYMMETRY} model x {MODEL_SYMMETRY}, 128-step FFT harmonic sum")
    print("=" * 96)

    hdr = (f"{'rpm':>6} {'phase':>6} {'f[Hz]':>7} | {'2D G2':>9} {'2DG2<B>':>9} "
           f"{'2D G1':>9} {'1D/24harm':>10} {'1D/24fund':>10} | {'MCADprox':>9} {'1D/MCAD':>8}")
    print(hdr)
    print("-" * len(hdr))

    results = {}
    for speed, phases in CASES.items():
        for ph in phases:
            try:
                r = analyze_case(speed, ph)
            except FileNotFoundError:
                print(f"{speed:>6} {ph:>6} : data not extracted yet - skip")
                continue
            m = r["machine"]
            mcad = mcad_prox_at(ref, speed, ph)
            ratio = m["P_1D_24_harm"] / mcad if mcad else float("nan")
            print(f"{speed:>6} {ph:>6.1f} {r['f_e']:>7.1f} | "
                  f"{m['P_2D_G2']:>9.1f} {m['P_2D_G2_meanB']:>9.1f} {m['P_2D_G1']:>9.1f} "
                  f"{m['P_1D_24_harm']:>10.1f} {m['P_1D_24_fund']:>10.1f} | "
                  f"{mcad if mcad else float('nan'):>9.1f} {ratio:>8.2f}")
            results.setdefault(speed, {})[ph] = {**m, "mcad_prox_W": mcad}

    # interpolate to PHASE_TARGET
    print(f"\n Interpolated to phase = {PHASE_TARGET} deg:")
    hdr2 = (f"{'rpm':>6} | {'2D G2':>9} {'2D G1':>9} {'1D/24harm':>10} | "
            f"{'MCADprox':>9} {'2DG2/MCAD':>9} {'2DG2/1D':>8}")
    print(hdr2)
    print("-" * len(hdr2))
    summary = []
    for speed, by_ph in sorted(results.items()):
        phases = sorted(by_ph.keys())
        if len(phases) < 2:
            continue
        p0, p1 = phases[0], phases[-1]
        t = (PHASE_TARGET - p0) / (p1 - p0)

        def lerp(key):
            return (1 - t) * by_ph[p0][key] + t * by_ph[p1][key]

        g2 = lerp("P_2D_G2")
        g1 = lerp("P_2D_G1")
        h24 = lerp("P_1D_24_harm")
        mc = lerp("mcad_prox_W")
        print(f"{speed:>6} | {g2:>9.1f} {g1:>9.1f} {h24:>10.1f} | "
              f"{mc:>9.1f} {g2/mc:>9.2f} {g2/h24:>8.3f}")
        summary.append({"speed": speed, "P_2D_G2_W": g2, "P_2D_G1_W": g1,
                        "P_1D_24_harm_W": h24, "mcad_prox_W": mc})

    out = DATA_DIR / "elhajji_2d_summary.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    print(f"\n [Saved] {out}")

    print("""
 Notes
 -----
 * '1D/MCAD' ~ 1 validates the extraction pipeline: same /24 formula and the
   same magnetostatic B source as Motor-CAD's magnetic method (differences:
   region-mean vs cuboid B, harmonic sum vs MCAD's handling).
 * 2D G2 vs 1D/24: direction split + high-frequency saturation. 2DG2/1D < 1
   at high speed shows the G2 penetration correction; the split itself
   matters when Bh (radial) is significant (slot-opening conductors).
""")


if __name__ == "__main__":
    main()
