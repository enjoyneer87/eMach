# -*- coding: utf-8 -*-
"""Section 5.2 check: similarity-transformed vs directly solved fields.

Reports the field-level comparison of the similarity-scaled SC solution
against the directly solved HalfSC sweep (24 loaded (I, beta)
combinations, 16 kRPM anchor speed).  Manuscript claims: fundamental
amplitude agrees within 1.8 % on average, proximity-excitation-field
energy (sum B^2) within 2.0 %, the tangential energy fraction f_theta
within 0.005, and the element-resolved (Volpe) loss on the two fields
differs by -0.7 to -4.8 %, the gap narrowing as current and phase angle
grow.

Modes
-----
default            read the shipped ``checks/scaled_vs_solved_compare.
                   json`` and judge the manuscript numbers.
``--recompute``    re-run ``compare_scaled_vs_solved`` on the raw HalfSC
                   sweeps.  Those sweeps are NOT part of the data
                   deposit (author decision, 2026-08-03), so without a
                   ``JEET_FEA_ROOT`` raw tree this exits with code 2.

Exit codes: 0 pass / 1 missing input or tolerance exceeded / 2 raw data
not part of the deposit.

``--tol`` is the slack added to each manuscript bound: percent points
for the three loss/energy bounds, and ``tol/100`` for the f_theta bound
(default 0.05, i.e. half a unit of the printed precision).
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

N_EXPECTED = 24
AMP_BOUND = 1.8              # % -- mean fundamental-amplitude deviation
B2_BOUND = 2.0               # % -- mean sum-B^2 deviation
FTH_BOUND = 0.005            # tangential energy fraction |delta|
VOLPE_RANGE = (-4.8, -0.7)   # % -- signed element-resolved loss deviation
CLAIM = ("manuscript Sec. 5.2: fields agree within 1.8% on average in "
         "fundamental amplitude and within 2.0% in proximity-excitation-"
         "field energy, f_theta within 0.005; element-resolved loss "
         "differs by -0.7 to -4.8%, the gap narrowing as current and "
         "phase angle grow")
# raw trees needed for --recompute, relative to JEET_FEA_ROOT
RAW_SUBDIRS = (os.path.join("_txt_backfill", "HalfSC_scaledSC"),
               os.path.join("_txt_backfill", "HalfSC_campaign"),
               os.path.join("SLFEA_Half", "ACLossCalcExport_Map"))


def report(res: dict, tol: float) -> int:
    rows = res["rows"]
    n = len(rows)
    amp = [100.0 * r["amp1_tan_meanrel"] for r in rows]
    b2 = [100.0 * r["sumB2_rel"] for r in rows]
    fth = [abs(r["f_theta_scaled"] - r["f_theta_solved"]) for r in rows]
    vol = [100.0 * (r["volpe_scaled_W"] / r["volpe_solved_W"] - 1.0)
           for r in rows]
    amp_mean, amp_max = sum(amp) / n, max(amp)
    b2_mean, b2_max = sum(b2) / n, max(b2)
    fth_max = max(fth)
    vol_min, vol_max = min(vol), max(vol)

    print("  %d loaded (I, beta) combinations (expected %d)"
          % (n, N_EXPECTED))
    print("  fundamental amplitude   mean %.2f%%  max %.2f%%   "
          "(claim: within %.1f%% on average)" % (amp_mean, amp_max,
                                                 AMP_BOUND))
    print("  sum B^2 (prox. energy)  mean %.2f%%  max %.2f%%   "
          "(claim: within %.1f%%)" % (b2_mean, b2_max, B2_BOUND))
    print("  |delta f_theta|         max %.4f            "
          "(claim: within %.3f)" % (fth_max, FTH_BOUND))
    if fth_max > FTH_BOUND:
        print("    note: the exact maximum is %.4f; it rounds to %.3f at "
              "the manuscript's printed precision." % (fth_max, FTH_BOUND))
    print("  element-resolved loss   %+.2f .. %+.2f%%      "
          "(claim: %+.1f to %+.1f%%)"
          % (vol_min, vol_max, VOLPE_RANGE[1], VOLPE_RANGE[0]))

    currents = sorted({r["current_A"] for r in rows})
    phases = sorted({r["phase_deg"] for r in rows})
    cell = {(r["current_A"], r["phase_deg"]): v for r, v in zip(rows, vol)}
    print("\n  element-resolved loss deviation [%], current x phase:")
    print("  %8s |" % "I [A]" + "".join("%7.0f" % p for p in phases)
          + "  deg")
    for c in currents:
        print("  %8.1f |" % c + "".join(
            "%+7.2f" % cell[(c, p)] if (c, p) in cell else "    ---"
            for p in phases))
    by_cur = [sum(abs(cell[(c, p)]) for p in phases if (c, p) in cell)
              / sum(1 for p in phases if (c, p) in cell) for c in currents]
    top = [cell[(currents[-1], p)] for p in phases
           if (currents[-1], p) in cell]
    narrow_cur = all(a > b for a, b in zip(by_cur, by_cur[1:]))
    narrow_ph = all(abs(a) > abs(b) for a, b in zip(top, top[1:]))
    print("  mean |dev| per current ring: "
          + "  ".join("%.2f" % v for v in by_cur)
          + "  -> %s with current" % ("narrows" if narrow_cur else
                                      "does NOT narrow"))
    print("  top ring along phase: %s with phase angle"
          % ("narrows" if narrow_ph else "does NOT narrow"))

    checks = {
        "n rows == %d" % N_EXPECTED: n == N_EXPECTED,
        "amp mean <= %.1f%%" % AMP_BOUND: amp_mean <= AMP_BOUND + tol,
        "sum B^2 mean <= %.1f%%" % B2_BOUND: b2_mean <= B2_BOUND + tol,
        "f_theta max <= %.3f" % FTH_BOUND:
            fth_max <= FTH_BOUND + tol / 100.0,
        "loss dev within %+.1f..%+.1f%%" % VOLPE_RANGE:
            (VOLPE_RANGE[0] - tol <= vol_min
             and vol_max <= VOLPE_RANGE[1] + tol),
        "gap narrows with current and phase": narrow_cur and narrow_ph,
    }
    bad = [k for k, v in checks.items() if not v]
    ok = not bad
    print("%s%s -- %s"
          % ("PASS" if ok else "FAIL",
             "" if ok else " (" + "; ".join(bad) + ")", CLAIM))
    return 0 if ok else 1


def recompute(out_path: str) -> dict:
    fea = os.environ.get("JEET_FEA_ROOT")
    missing = [s for s in RAW_SUBDIRS
               if not (fea and os.path.isdir(os.path.join(fea, s)))]
    if missing:
        repro_env.require(
            None, "HalfSC scaled/solved raw sweeps (%s)"
            % ", ".join(missing), in_deposit=False)      # exits 2
    import compare_scaled_vs_solved as cs
    cs.main()
    res = json.load(open(cs.OUT, encoding="utf-8"))
    if os.path.abspath(cs.OUT) != os.path.abspath(out_path):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
        print("saved:", out_path)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--recompute", action="store_true",
                    help="re-run compare_scaled_vs_solved on the raw "
                         "HalfSC sweeps (author-only; not in the deposit)")
    ap.add_argument("--out", default=os.path.join(
        repro_env.checks_dir(), "scaled_vs_solved_compare.json"))
    ap.add_argument("--tol", type=float, default=0.05,
                    help="slack added to each manuscript bound (percent "
                         "points; f_theta uses tol/100)")
    a = ap.parse_args()

    print("Check (Sec. 5.2): similarity-scaled SC field vs directly "
          "solved HalfSC field, 24 loaded (I, beta) combinations")
    if a.recompute:
        res = recompute(a.out)
    else:
        if not os.path.isfile(a.out):
            print("[missing input] %s\n  Restore the shipped checks/ JSON "
                  "(the raw HalfSC sweeps behind --recompute are not part "
                  "of the deposit)." % a.out)
            return 1
        res = json.load(open(a.out, encoding="utf-8"))
    return report(res, a.tol)


if __name__ == "__main__":
    raise SystemExit(main())
