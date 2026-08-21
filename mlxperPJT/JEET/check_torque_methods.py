# -*- coding: utf-8 -*-
"""Section 5.1 check: three torques from one time-stepped FEA export.

Maxwell stress, flux-linkage (dq), and virtual-work torque are computed
from the element tables alone -- no solver post-processing variable is
read -- so their agreement is a property of the exported field.  The
manuscript states the three agree within 1 % once the eddy-current loss
is accounted for in the power balance; the raw (eddy-uncorrected) dq and
virtual-work values, 3-7 % high, are printed alongside to show the size
of that term.

Modes
-----
default            read the shipped ``checks/torque_methods.json``,
                   print the table, judge against ``--tol`` (percent).
``--recompute``    re-run :func:`jeet_acloss_rbf.torque_methods.
                   three_torques` on the exports.  Ref and SC resolve
                   from the data deposit (Zenodo ``fea/`` layout) or
                   ``JEET_FEA_ROOT``; the two HalfSC exports are not
                   part of the deposit (author decision, 2026-08-03), so
                   without ``JEET_FEA_ROOT`` they are reported as not
                   reproducible and their shipped values are kept.

Exit codes: 0 pass / 1 missing input or tolerance exceeded / 2 only
raw data absent from the deposit was requested.

Derived from ``run_torque_methods.py`` (same algorithm); only the file
resolution and the reporting front differ.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.abspath(os.path.join(HERE, "..", "..", "tools")),
              os.path.abspath(os.path.join(HERE, ".."))):
    if os.path.isdir(os.path.join(_cand, "jeet_acloss_rbf")) \
            and _cand not in sys.path:
        sys.path.insert(0, _cand)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from jeet_acloss_rbf import repro_env                       # noqa: E402
from jeet_acloss_rbf.torque_methods import three_torques    # noqa: E402

# name -> ((model, mode, rpm, amp, phase), pole pairs, speed,
#          Motor-CAD AvTorqueMS cycle average [Nm] or None, in_deposit)
MODELS = {
    "Ref": (("Ref", "FullFEA", 16000.0, 460.0, 36.0),
            4, 16000.0, 807.05, True),
    # HalfSC's own limit (690 A) is not in the Full-FEA campaign grid;
    # the top tier 460 A is used and no solver value is attached to it.
    "HalfSC": (("HalfSC", "FullFEA", 16000.0, 460.0, 36.0),
               4, 16000.0, None, False),
    # HalfSC at its own 690 A limit exists only as the rotor-stepped MS
    # (Hybrid-mode) export of the campaign back-fill: Je = 0 there, so
    # the eddy corrections vanish and Table 3's 1797 Nm is the reference.
    "HalfSC_690_MS": (("HalfSC", "Hybrid", 16000.0, 690.0, 36.0),
                      4, 16000.0, 1797.0, False),
    "SC": (("SC", "FullFEA", 16000.0, 920.0, 36.0),
           4, 16000.0, 3284.29, True),
}
KEYS = ("maxwell", "dq_raw", "dq", "virtual_work_raw", "virtual_work")
JUDGED = ("dq", "virtual_work")     # eddy-corrected methods vs Maxwell
LABELS = {"maxwell": "Maxwell stress (Arkkio)",
          "dq_raw": "flux-linkage dq, raw",
          "dq": "flux-linkage dq, -P_eddy",
          "virtual_work_raw": "virtual work, no eddy",
          "virtual_work": "virtual work, filaments"}
CLAIM = ("manuscript Sec. 5.1: Maxwell-stress, flux-linkage, and "
         "virtual-work torques agree within 1% once the eddy-current "
         "loss is accounted for")


def print_model(name: str, r: dict) -> None:
    hmax = max(r["h_semantics_max_relerr"].values())
    print("\n=== %s: %s ===" % (name, r["path"]))
    print("  steps %d, sectors x%d, mesh drift %.2e mm, "
          "H check max rel.err %.1e, I_rms %.1f A"
          % (r["n_steps"], r["n_sect"], r["mesh_drift_max_mm"], hmax,
             r["i_rms_A"]))
    print("  %-24s%9s%9s%12s%10s"
          % ("method", "T [Nm]", "ripple", "vs Maxwell", "vs MCAD"))
    for k in KEYS:
        st = r[k]
        print("  %-24s%9.2f%8.1f%%%+11.2f%%%+9.2f%%"
              % (LABELS[k], abs(st["mean_settled"]), st["ripple_pp_pct"],
                 r["dev_vs_maxwell_pct"][k], r["dev_vs_mcad_pct"][k]))
    print("  VW vs Maxwell, instantaneous RMS: %.2f%% of mean torque"
          % r["vw_vs_maxwell_inst_rms_pct"])
    print("  P_eddy %.1f kW vs P_mech %.0f kW (%.2f%%)"
          % (r["P_eddy_mean_W"] / 1e3, abs(r["P_mech_mean_W"]) / 1e3,
             100 * r["P_eddy_mean_W"] / abs(r["P_mech_mean_W"])))


def judge(summary: dict, tol_pct: float) -> int:
    worst, worst_at = 0.0, ""
    for name in MODELS:
        r = summary.get(name)
        if r is None:
            print("[%s] no result stored" % name)
            print("FAIL: incomplete result set -- %s" % CLAIM)
            return 1
        print_model(name, r)
        for k in JUDGED:
            d = abs(r["dev_vs_maxwell_pct"][k])
            if d > worst:
                worst, worst_at = d, "%s/%s" % (name, k)
    ok = worst <= tol_pct
    print("\n%s: worst eddy-corrected deviation vs Maxwell %.2f%% (%s) "
          "vs tolerance %.1f%% -- %s"
          % ("PASS" if ok else "FAIL", worst, worst_at, tol_pct, CLAIM))
    return 0 if ok else 1


def recompute(names, out_json, out_npz):
    prev = {}
    if os.path.isfile(out_json):
        prev = json.load(open(out_json, encoding="utf-8"))
    summary, series = dict(prev), {}
    n_done, n_absent = 0, 0
    for name in names:
        spec, pp, rpm, t_mcad, in_dep = MODELS[name]
        path = repro_env.raw_export(*spec)
        if path is None:
            if in_dep:
                repro_env.require(None, "%s export %s"
                                  % (name, repro_env.zenodo_name(*spec)))
            print("[%s] raw export not available: the HalfSC sweep is not "
                  "part of the data deposit (%s); the shipped result is "
                  "kept." % (name, repro_env.ZENODO_URL))
            n_absent += 1
            continue
        print("\nrecomputing %s from %s ..." % (name, path))
        r = three_torques(path, pp, rpm)
        series[name] = r.pop("series")
        mx = r["maxwell"]["mean_settled"]
        r["path"] = os.path.basename(os.path.dirname(path)) or \
            os.path.basename(path)
        r["reference_AvTorqueMS_Nm"] = t_mcad
        r["dev_vs_maxwell_pct"] = {
            k: 100.0 * (abs(r[k]["mean_settled"]) / abs(mx) - 1.0)
            for k in KEYS}
        r["dev_vs_mcad_pct"] = {
            k: (100.0 * (abs(r[k]["mean_settled"]) / t_mcad - 1.0)
                if t_mcad else float("nan"))
            for k in KEYS}
        summary[name] = r
        n_done += 1
    if n_done == 0 and n_absent > 0:
        print("[not reproducible from the deposit] every requested export "
              "is outside the deposit (%s)." % repro_env.ZENODO_URL)
        raise SystemExit(2)
    if n_done == 0:
        repro_env.require(None, "torque-methods raw exports")

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=1)
    merged = {}
    if os.path.isfile(out_npz):
        with np.load(out_npz) as old:
            merged.update({k: old[k] for k in old.files})
    merged.update({"%s__%s" % (m, k): v
                   for m, s in series.items() for k, v in s.items()})
    np.savez_compressed(out_npz, **merged)
    print("\nsaved:", out_json, "and", out_npz)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--recompute", action="store_true",
                    help="re-run three_torques on the raw exports instead "
                         "of reading the shipped JSON")
    ap.add_argument("--models", default=",".join(MODELS),
                    help="comma list of models to recompute")
    ap.add_argument("--out", default=os.path.join(
        repro_env.checks_dir(), "torque_methods.json"))
    ap.add_argument("--tol", type=float, default=1.0,
                    help="max allowed |dev| of the eddy-corrected dq and "
                         "virtual-work torques vs Maxwell, in percent")
    a = ap.parse_args()
    out_npz = os.path.join(os.path.dirname(a.out) or ".",
                           "torque_methods_series.npz")

    print("Check (Sec. 5.1): Maxwell / flux-linkage dq / virtual-work "
          "torque from the exported field, Ref/HalfSC/SC at 16 kRPM")
    if a.recompute:
        names = [s.strip() for s in a.models.split(",") if s.strip()]
        summary = recompute(names, a.out, out_npz)
    else:
        if not os.path.isfile(a.out):
            print("[missing input] %s\n  Run with --recompute (raw exports "
                  "required), or restore the shipped checks/ JSON." % a.out)
            return 1
        summary = json.load(open(a.out, encoding="utf-8"))
    return judge(summary, a.tol)


if __name__ == "__main__":
    raise SystemExit(main())
