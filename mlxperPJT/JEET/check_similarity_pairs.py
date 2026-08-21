# -*- coding: utf-8 -*-
"""Section 5.2 check: absolute Full-FEA loss on similarity-mapped pairs.

Under the k_r = 2 similarity, the SC point (omega/4, 2I, beta) carries
the same absolute AC loss as the Ref point (omega, I, beta).  This check
pairs the Full-FEA records of the two campaign summaries under exactly
that rule and reports the deviation

    dev_pct = 100 (P_SC / P_Ref - 1).

Three aggregates are printed:

* ``grid``   -- the 24 pairs at the current levels where the Ref and SC
               current grids coincide (about 230 A and 460 A on the Ref
               side), i.e. both machines sit on native grid points; the
               manuscript states these agree within 1.6 %.
* ``rated``  -- the 12 pairs at 460 A <-> 920 A (2 speeds x 6 phases).
* ``loaded`` -- all 48 loaded pairs (I > 0.1 A) the rule produces.

Modes
-----
default            read the shipped ``checks/similarity_pairs.json``,
                   print the aggregates, judge ``--subset`` vs ``--tol``.
``--recompute``    rebuild the pair table from the two Map_Summary files
                   under the data root (they ship with the package, so
                   no raw field export is needed).

Exit codes: 0 pass / 1 missing input or tolerance exceeded.
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

from jeet_acloss_rbf import repro_env                       # noqa: E402

LOSS_KEY = "fea_total_ac_kW"
SPEED_RATIO = 4.0            # omega_Ref = 4 omega_SC  (k_r^2)
CURRENT_RATIO = 2.0          # I_SC = 2 I_Ref          (k_r)
CURRENT_TOL_A = 0.2          # pairing tolerance on 2 I_Ref vs I_SC
GRID_COINCIDE_TOL_A = 0.1    # Ref current also on the SC current grid
MIN_CURRENT_A = 0.1          # exclude the no-load ring
EXPECTED = {"grid": 24, "rated": 12, "loaded": 48}
CLAIM = ("manuscript Sec. 5.2: absolute Full-FEA loss agrees within "
         "1.6% across the 24 operating points that map onto each other "
         "under the similarity")


def load_records(model: str):
    path = os.path.join(repro_env.data_root(), model,
                        "JEET_ACLoss_%s_Map_Summary.json" % model)
    repro_env.require(path if os.path.isfile(path) else None,
                      "%s campaign summary %s" % (model,
                                                  os.path.basename(path)))
    d = json.load(open(path, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    out = {}
    for r in recs:                       # rerun entries overwrite in order
        if r.get("mode") != "FullFEA" or r["current"] <= MIN_CURRENT_A:
            continue
        out[(float(r["speed"]), round(float(r["current"]), 3),
             float(r["phase"]))] = float(r[LOSS_KEY])
    return out


def build_pairs():
    ref = load_records("Ref")
    sc = load_records("SC")
    sc_currents = sorted({k[1] for k in sc})
    rated_ref = max(k[1] for k in ref)
    rows = []
    for (spd_r, cur_r, ph_r), p_ref in sorted(ref.items()):
        for (spd_s, cur_s, ph_s), p_sc in sc.items():
            if abs(spd_s - spd_r / SPEED_RATIO) > 1e-6:
                continue
            if abs(cur_s - CURRENT_RATIO * cur_r) > CURRENT_TOL_A:
                continue
            if abs(ph_s - ph_r) > 1e-9:
                continue
            subsets = ["loaded"]
            if any(abs(cur_r - c) <= GRID_COINCIDE_TOL_A
                   for c in sc_currents):
                subsets.append("grid")
            if abs(cur_r - rated_ref) <= CURRENT_TOL_A:
                subsets.append("rated")
            rows.append({
                "speed_ref_rpm": spd_r, "current_ref_A": cur_r,
                "phase_deg": ph_r,
                "speed_sc_rpm": spd_s, "current_sc_A": cur_s,
                "p_ref_kW": p_ref, "p_sc_kW": p_sc,
                "dev_pct": 100.0 * (p_sc / p_ref - 1.0),
                "subsets": subsets,
            })
    agg = {}
    for name in ("grid", "rated", "loaded"):
        dv = [r["dev_pct"] for r in rows if name in r["subsets"]]
        ab = [abs(v) for v in dv]
        agg[name] = {
            "n": len(dv),
            "dev_min_pct": min(dv), "dev_max_pct": max(dv),
            "absdev_min_pct": min(ab), "absdev_max_pct": max(ab),
            "absdev_mean_pct": sum(ab) / len(ab),
        } if dv else {"n": 0}
    return {"rows": rows, "aggregate": agg, "_meta": {
        "rule": "mode FullFEA, I > %.1f A, speed_SC = speed_Ref/%g, "
                "I_SC = %g I_Ref (tol %.1f A), same beta; dev_pct = "
                "100 (P_SC/P_Ref - 1) on %s"
                % (MIN_CURRENT_A, SPEED_RATIO, CURRENT_RATIO,
                   CURRENT_TOL_A, LOSS_KEY),
        "grid_subset": "Ref current also lies on the SC current grid "
                       "(within %.1f A), so both machines are evaluated "
                       "on native grid points at I and %gI"
                       % (GRID_COINCIDE_TOL_A, CURRENT_RATIO),
        "rated_subset": "Ref 460 A <-> SC 920 A",
    }}


def judge(res: dict, subset: str, tol_pct: float) -> int:
    agg = res["aggregate"]
    for name in ("grid", "rated", "loaded"):
        s = agg[name]
        if s["n"] == 0:
            print("  %-6s  n=0" % name)
            continue
        print("  %-6s  n=%2d   |dev| %.2f .. %.2f%%  (mean %.2f%%)   "
              "signed %+.2f .. %+.2f%%"
              % (name, s["n"], s["absdev_min_pct"], s["absdev_max_pct"],
                 s["absdev_mean_pct"], s["dev_min_pct"], s["dev_max_pct"]))
    s = agg[subset]
    ok = (s.get("n") == EXPECTED[subset]
          and s.get("absdev_max_pct", 1e9) <= tol_pct)
    print("%s: subset '%s' has %d pairs (expected %d), max |dev| %.2f%% "
          "vs tolerance %.1f%% -- %s"
          % ("PASS" if ok else "FAIL", subset, s.get("n", 0),
             EXPECTED[subset], s.get("absdev_max_pct", float("nan")),
             tol_pct, CLAIM))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--recompute", action="store_true",
                    help="rebuild the pair table from the Map_Summary "
                         "files instead of reading the shipped JSON")
    ap.add_argument("--out", default=os.path.join(
        repro_env.checks_dir(), "similarity_pairs.json"))
    ap.add_argument("--subset", default="grid",
                    choices=("grid", "rated", "loaded"),
                    help="which aggregate the PASS/FAIL verdict uses")
    ap.add_argument("--tol", type=float, default=1.6,
                    help="max allowed |dev| of the judged subset, percent")
    a = ap.parse_args()

    print("Check (Sec. 5.2): absolute Full-FEA loss on similarity-mapped "
          "pairs, SC (omega/4, 2I, beta) vs Ref (omega, I, beta)")
    if a.recompute:
        res = build_pairs()
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, indent=1)
        print("saved:", a.out)
    else:
        if not os.path.isfile(a.out):
            print("[missing input] %s\n  Run with --recompute (needs only "
                  "the shipped Map_Summary files), or restore the shipped "
                  "checks/ JSON." % a.out)
            return 1
        res = json.load(open(a.out, encoding="utf-8"))
    return judge(res, a.subset, a.tol)


if __name__ == "__main__":
    raise SystemExit(main())
