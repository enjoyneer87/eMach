# -*- coding: utf-8 -*-
"""Section 5.1 check: conductor-current reconstruction from the FEA export.

Summing the exported element current density over each conductor cross
section, I_c(t) = sum_e J_e A_e, must reproduce the impressed phase
current (the fundamental amplitude over sqrt(2) equals the commanded
460 / 920 A rms) with no circuit information involved.  The manuscript
states the reconstruction holds "to four significant digits".

Modes
-----
default            read the shipped ``checks/conductor_currents.json``,
                   print the numbers, judge against ``--tol``.
``--recompute``    parse the two rated Full-FEA exports (Ref 16 kRPM
                   460 A and SC 16 kRPM 920 A, both at beta = 36 deg)
                   and rewrite the JSON.  The exports resolve through
                   ``jeet_acloss_rbf.repro_env.raw_export`` (Zenodo
                   ``fea/`` layout first, then ``JEET_FEA_ROOT``).

Exit codes: 0 pass / 1 missing input or tolerance exceeded.

Note: the time-domain rms stored in ``torque_methods.json`` (458.6 A) is
0.3 % low because the export spans a non-integer number of periods; the
least-squares fundamental used here is free of that bias.
"""
from __future__ import annotations

import argparse
import json
import math
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
from jeet_acloss_rbf.torque_methods import (                # noqa: E402
    conductor_codes, iter_fea_blocks)

POLE_PAIRS = 4
# (model, mode, rpm, amp, phase) -> impressed phase current [A rms]
CASES = {
    "Ref_16k": (("Ref", "FullFEA", 16000.0, 460.0, 36.0), 460.0),
    "SC_16k": (("SC", "FullFEA", 16000.0, 920.0, 36.0), 920.0),
}
CLAIM = ("manuscript Sec. 5.1: conductor-current reconstruction reproduces "
         "the impressed current to four significant digits")


def recompute_case(tag: str, spec, i_exp: float) -> dict:
    path = repro_env.require(
        repro_env.raw_export(*spec),
        "%s Full-FEA export %s" % (tag, repro_env.zenodo_name(*spec)))
    blocks = [b for b in iter_fea_blocks(path) if b["time_s"] is not None]
    p0 = blocks[0]
    codes = sorted(conductor_codes(p0), key=lambda c: float(np.hypot(
        p0["x_mm"][p0["reg"] == c], p0["y_mm"][p0["reg"] == c]).mean()))
    masks = [p0["reg"] == c for c in codes]
    areas = [p0["area_mm2"][m] * 1e-6 for m in masks]           # m^2
    a_reg = np.array([a.sum() for a in areas])                  # m^2

    i_elem = np.array([[float(np.sum(b["j_am2"][m] * a))
                        for m, a in zip(masks, areas)] for b in blocks])
    jmap = [dict(zip(b["rcode"], b["rjval"])) for b in blocks]
    i_tbl = np.array([[jm.get(int(c), np.nan) * a_reg[k]
                       for k, c in enumerate(codes)] for jm in jmap])

    rot = next(abs(b["rotate_deg"]) for b in blocks if b["rotate_deg"])
    th_e = np.deg2rad((np.array([b["step"] for b in blocks], float) - 1.0)
                      * rot) * POLE_PAIRS
    A = np.column_stack([np.ones_like(th_e), np.cos(th_e), np.sin(th_e)])
    coef, *_ = np.linalg.lstsq(A, i_elem, rcond=None)
    amp1 = np.hypot(coef[1], coef[2])                           # peak [A]
    i_fund = amp1 / np.sqrt(2.0)                                # rms  [A]
    rel_dev = np.abs(i_fund / i_exp - 1.0)

    # parsing consistency: the RegionsTable current density times the
    # region area must equal the element sum at every step
    tbl_mismatch = float(np.nanmax(np.abs(i_tbl - i_elem)) / amp1.min())
    rmax = float(rel_dev.max())
    return {
        "file": os.path.basename(os.path.dirname(path)) or
        os.path.basename(path),
        "i_expected_Arms": i_exp,
        "n_steps": len(blocks),
        "n_conductors": len(codes),
        "i_fund_Arms": [float(v) for v in i_fund],
        "rel_dev": [float(v) for v in rel_dev],
        "rel_dev_max": rmax,
        "sig_digits": int(math.floor(-math.log10(rmax))) if rmax > 0 else 16,
        "region_table_vs_element_sum_max_rel": tbl_mismatch,
    }


def judge(res: dict, tol: float) -> int:
    worst = 0.0
    for tag, r in sorted(res.items()):
        if tag.startswith("_"):
            continue
        print("[%s]  %s  impressed %g A rms, %d conductors, %d steps"
              % (tag, r["file"], r["i_expected_Arms"], r["n_conductors"],
                 r["n_steps"]))
        print("  fundamental/sqrt(2): %.2f .. %.2f A rms   "
              "max |rel.dev| %.2e   region-table consistency %.1e"
              % (min(r["i_fund_Arms"]), max(r["i_fund_Arms"]),
                 r["rel_dev_max"], r["region_table_vs_element_sum_max_rel"]))
        worst = max(worst, r["rel_dev_max"])
    ok = worst <= tol
    print("%s: worst relative deviation %.2e vs tolerance %.0e "
          "(agreement to four significant digits in the 5e-4 half-unit "
          "convention) -- %s" % ("PASS" if ok else "FAIL", worst, tol,
                                 CLAIM))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--recompute", action="store_true",
                    help="re-parse the raw exports instead of reading the "
                         "shipped JSON")
    ap.add_argument("--out", default=os.path.join(
        repro_env.checks_dir(), "conductor_currents.json"))
    ap.add_argument("--tol", type=float, default=5e-4,
                    help="max allowed relative deviation of the "
                         "reconstructed fundamental (5e-4 = 4 s.f.)")
    a = ap.parse_args()

    print("Check (Sec. 5.1): conductor-current reconstruction "
          "I_c(t) = sum_e J_e A_e vs the impressed 460/920 A rms")
    if a.recompute:
        res = {}
        for tag, (spec, i_exp) in CASES.items():
            res[tag] = recompute_case(tag, spec, i_exp)
        res["_meta"] = {
            "pole_pairs": POLE_PAIRS,
            "method": "least-squares fundamental of sum_e J_e A_e per "
                      "conductor region vs electrical angle",
            "note": "sig_digits = floor(-log10(max rel.dev)); the static "
                    "pre-solve block is excluded",
        }
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, indent=1)
        print("saved:", a.out)
    else:
        if not os.path.isfile(a.out):
            print("[missing input] %s\n  Run with --recompute (raw exports "
                  "required), or restore the shipped checks/ JSON." % a.out)
            return 1
        res = json.load(open(a.out, encoding="utf-8"))
    return judge(res, a.tol)


if __name__ == "__main__":
    raise SystemExit(main())
