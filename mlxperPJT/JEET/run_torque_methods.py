# -*- coding: utf-8 -*-
"""Three torques (Maxwell stress / flux-linkage dq / virtual work) from the
time-stepped FEA exports, for the truth-data self-consistency check of §5.1.

All three come from the element tables alone — no Motor-CAD variable is
read — so the agreement between them is a property of the exported field,
not of the solver's own post-processing.  Motor-CAD's cycle-average
``AvTorqueMS`` is kept only as a reference column.

  python run_torque_methods.py                 # Ref, HalfSC, SC at 16 kRPM
  python run_torque_methods.py --models Ref    # one model
  JEET_FEA_ROOT=... overrides the export root.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

from jeet_acloss_rbf.torque_methods import three_torques  # noqa: E402

ROOT = os.environ.get("JEET_FEA_ROOT", r"D:\KangDH\Thesis\e10")
# (export path, pole pairs, speed, Motor-CAD AvTorqueMS cycle average [Nm])
MODELS = {
    "Ref": (os.path.join(ROOT, "_txt_backfill", "Ref",
                         "FullFEA_Speed_16000RPM_460.0A_36.0deg",
                         "FEA_data.txt.gz"), 4, 16000.0, 807.05),
    # HalfSC's own limit (690 A) is not in the Full-FEA campaign grid; the
    # top tier 460 A is used and no solver value is attached to it.
    "HalfSC": (os.path.join(ROOT, "_txt_backfill", "HalfSC",
                            "FullFEA_Speed_16000RPM_460.0A_36.0deg",
                            "FEA_data.txt.gz"), 4, 16000.0, None),
    "SC": (os.path.join(ROOT, "_txt_backfill", "SC",
                        "FullFEA_Speed_16000RPM_920.0A_36.0deg",
                        "FEA_data.txt.gz"), 4, 16000.0, 3284.29),
}
OUT_JSON = os.path.join(HERE, "map_exports", "e10", "torque_methods.json")
OUT_NPZ = os.path.join(HERE, "map_exports", "e10", "torque_methods_series.npz")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="Ref,HalfSC,SC")
    ap.add_argument("--out", default=OUT_JSON)
    a = ap.parse_args()

    summary, series = {}, {}
    for name in [s.strip() for s in a.models.split(",") if s.strip()]:
        path, pp, rpm, t_mcad = MODELS[name]
        if not os.path.exists(path):
            alt = path[:-3] if path.endswith(".gz") else path + ".gz"
            if os.path.exists(alt):
                path = alt
            else:
                print(f"[{name}] export not found: {path}")
                continue
        print(f"\n=== {name}: {os.path.basename(os.path.dirname(path))} ===")
        r = three_torques(path, pp, rpm)
        ser = r.pop("series")
        series[name] = ser
        mx = r["maxwell"]["mean_settled"]
        r["reference_AvTorqueMS_Nm"] = t_mcad
        keys = ("maxwell", "dq_raw", "dq", "virtual_work_raw", "virtual_work")
        r["dev_vs_maxwell_pct"] = {
            k: 100.0 * (abs(r[k]["mean_settled"]) / abs(mx) - 1.0)
            for k in keys}
        r["dev_vs_mcad_pct"] = {
            k: (100.0 * (abs(r[k]["mean_settled"]) / t_mcad - 1.0)
                if t_mcad else float("nan"))
            for k in keys}
        summary[name] = r

        hmax = max(r["h_semantics_max_relerr"].values())
        print(f"  steps {r['n_steps']}, sectors x{r['n_sect']}, "
              f"mesh drift {r['mesh_drift_max_mm']:.2e} mm, "
              f"H check max rel.err {hmax:.1e}, "
              f"sides/phase {r['phase_sides']}, I_rms {r['i_rms_A']:.1f} A")
        print(f"  {'method':<24}{'T [Nm]':>9}{'ripple':>9}"
              f"{'vs Maxwell':>12}{'vs MCAD':>10}")
        labels = {"maxwell": "Maxwell stress (Arkkio)",
                  "dq_raw": "flux-linkage dq, raw",
                  "dq": "flux-linkage dq, -P_eddy",
                  "virtual_work_raw": "virtual work, no eddy",
                  "virtual_work": "virtual work, filaments"}
        for k in keys:
            st = r[k]
            print(f"  {labels[k]:<24}{abs(st['mean_settled']):>9.2f}"
                  f"{st['ripple_pp_pct']:>8.1f}%"
                  f"{r['dev_vs_maxwell_pct'][k]:>+11.2f}%"
                  f"{r['dev_vs_mcad_pct'][k]:>+9.2f}%")
        print(f"  VW vs Maxwell, instantaneous RMS: "
              f"{r['vw_vs_maxwell_inst_rms_pct']:.2f}% of mean torque")
        print(f"  P_eddy {r['P_eddy_mean_W']/1e3:.1f} kW "
              f"(filament term {r['eddy_term_mean_W']/1e3:.1f} kW) vs "
              f"P_mech {abs(r['P_mech_mean_W'])/1e3:.0f} kW "
              f"({100*r['P_eddy_mean_W']/abs(r['P_mech_mean_W']):.2f}%)")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    np.savez_compressed(OUT_NPZ, **{f"{m}__{k}": v
                                    for m, s in series.items()
                                    for k, v in s.items()})
    print("\nsaved:", a.out, "and", OUT_NPZ)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
