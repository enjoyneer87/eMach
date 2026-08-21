# -*- coding: utf-8 -*-
"""Section 5.1 check: Parseval closure of the harmonic loss decomposition.

The induced-current loss of the slot-1 conductors is computed twice from
the same Full-FEA export: directly in the time domain,

    p_direct = mean_t sum_e A_e Je_e(t)^2 / sigma        [W/m]

and through the order-domain (Parseval) sum of the least-squares harmonic
fit of Je(t),

    p_harm = sum_e A_e (a0_e^2 + sum_n |C_n,e|^2 / 2) / sigma.

The manuscript states the two close within 0.6 %.  The same script also
reproduces the per-order AF_n table (the scalar-AF order-structure study
of Sec. 4.1): TS-side P_n from the element Je harmonics, hybrid-side P_n
from g(eta_n) |B_n|^2 on the conductor-average field of the matching
rotor-stepped (Hybrid-mode) export.

Modes
-----
default            read the shipped ``checks/ts_harmonic_af.json``, print
                   the closures, judge against ``--tol`` (percent).
``--recompute``    re-parse the eight exports (Ref/SC x FullFEA/Hybrid x
                   16k/8k, rated current, beta = 36 deg) and rewrite the
                   JSON.  Resolution: Zenodo ``fea/`` layout first, then
                   ``JEET_FEA_ROOT``.

Exit codes: 0 pass / 1 missing input or tolerance exceeded.

Derived from ``run_ts_harmonic_af.py`` (same algorithm and constants);
only the file resolution, the closure bookkeeping, and the reporting
front are new.
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
from jeet_acloss_rbf.field_metrics import slot_conductor_codes  # noqa: E402
from jeet_acloss_rbf.torque_methods import iter_fea_blocks  # noqa: E402

SLOT = 1
SIGMA = 4.709e7
MU0 = 4e-7 * np.pi
POLE_PAIRS = 4                       # e10: 8 poles -- electrical = 4 x mech
NH = 24                              # highest fitted electrical order
BETA = 36.0

# tag -> (model, rpm, amp[A], f_e[Hz], w_c[mm], h_c[mm])
CASES = {
    "Ref_16k": ("Ref", 16000.0, 460.0, 1066.67, 3.711, 1.686),
    "Ref_8k": ("Ref", 8000.0, 460.0, 533.33, 3.711, 1.686),
    "SC_16k": ("SC", 16000.0, 920.0, 1066.67, 7.422, 3.372),
    "SC_8k": ("SC", 8000.0, 920.0, 533.33, 7.422, 3.372),
}
CLAIM = ("manuscript Sec. 5.1: the Parseval sum of the harmonic "
         "decomposition closes within 0.6%")


def harm_fit(theta_e: np.ndarray, Y: np.ndarray, nh: int):
    """Harmonic LSQ: Y (nt, m) -> (a0 (m,), C (nh, m) complex peaks)."""
    cols = [np.ones_like(theta_e)]
    for n in range(1, nh + 1):
        cols += [np.cos(n * theta_e), np.sin(n * theta_e)]
    A = np.column_stack(cols)                       # (nt, 1+2nh)
    coef, *_ = np.linalg.lstsq(A, Y, rcond=None)
    a0 = coef[0]
    C = coef[1::2] + 1j * coef[2::2]                # (nh, m)
    return a0, C


def g_kernel(eta: np.ndarray, w_c_m: float, h_c_m: float) -> np.ndarray:
    """Manuscript eq. (g_kernel): g = w/(h sigma mu0^2) eta K(eta)."""
    K = (np.sinh(eta) - np.sin(eta)) / (np.cosh(eta) + np.cos(eta))
    return w_c_m / (h_c_m * SIGMA * MU0 ** 2) * eta * K


def load_series(path: str, want_je: bool):
    """Slot-1 conductor series: Je(t) per element, or mean B(t) per bar.

    Returns theta_mech_deg (nt,) plus either (JE (nt, n_elem),
    area_mm2 (n_elem,)) or (BX, BY (nt, 6)) -- six bars in radial order.
    ``rotate_deg`` is the per-block "Rotate Step" (a constant increment),
    so the accumulated angle is rebuilt as (block - 1) x |step|.
    """
    thetas, rows = [], []
    codes = mask = None
    area = None
    cond_masks = None
    step_deg = None
    n_ref = None
    for p in iter_fea_blocks(path):
        bi = p['step']
        if codes is None:
            codes = sorted(slot_conductor_codes(p, SLOT),
                           key=lambda c: np.hypot(
                               p['x_mm'][p['reg'] == c],
                               p['y_mm'][p['reg'] == c]).mean())
            mask = np.isin(p['reg'], codes)
            area = p['area_mm2'][mask]
            cond_masks = [(p['reg'][mask] == c) for c in codes]
            n_ref = len(p['reg'])
        assert len(p['reg']) == n_ref, "mesh mismatch at block %d" % bi
        if step_deg is None and p['rotate_deg']:
            step_deg = abs(p['rotate_deg'])
        if want_je:
            je = p['je_am2'][mask]
            if np.abs(je).max() < 1.0:           # block-1 Je=0 artifact
                continue
            rows.append(je)
        else:
            w = p['area_mm2'][mask]
            bx, by = p['bx'][mask], p['by'][mask]
            rows.append([
                (np.sum(w[m] * bx[m]) / np.sum(w[m]),
                 np.sum(w[m] * by[m]) / np.sum(w[m])) for m in cond_masks])
        thetas.append(bi - 1)                    # 0-based block index
    assert step_deg, "Rotate Step not found: %s" % path
    theta = np.asarray(thetas, float) * step_deg
    if want_je:
        return theta, np.asarray(rows), area
    B = np.asarray(rows)                         # (nt, 6, 2)
    return theta, B[:, :, 0], B[:, :, 1]


def run_case(tag, model, rpm, amp, f_e, w_c_mm, h_c_mm):
    ts_spec = (model, "FullFEA", rpm, amp, BETA)
    hy_spec = (model, "Hybrid", rpm, amp, BETA)
    ts_path = repro_env.require(
        repro_env.raw_export(*ts_spec),
        "%s Full-FEA export %s" % (tag, repro_env.zenodo_name(*ts_spec)))
    hy_path = repro_env.require(
        repro_env.raw_export(*hy_spec),
        "%s Hybrid-mode export %s" % (tag, repro_env.zenodo_name(*hy_spec)))

    # --- TS: element-wise Je harmonics -> per-order loss [W/m]
    th, JE, area = load_series(ts_path, want_je=True)
    theta_e = np.deg2rad(th) * POLE_PAIRS
    span = (theta_e.max() - theta_e.min()) / (2 * np.pi)
    a0, C = harm_fit(theta_e, JE, NH)            # (n_elem,), (NH, n_elem)
    a_m2 = area * 1e-6
    p_ts = np.array([np.sum(a_m2 * np.abs(C[n - 1]) ** 2) / (2 * SIGMA)
                     for n in range(1, NH + 1)])

    # --- Parseval closure: direct time-domain loss vs the harmonic sum
    p_direct = float(np.mean(np.sum(a_m2[None, :] * JE ** 2, axis=1))
                     / SIGMA)
    p_harm = float(np.sum(a_m2 * a0 ** 2) / SIGMA + p_ts.sum())
    closure_pct = 100.0 * (p_harm / p_direct - 1.0)

    # --- HYB: conductor-average B harmonics -> g(eta_n) |B_n|^2 [W/m]
    th_h, BX, BY = load_series(hy_path, want_je=False)
    theta_eh = np.deg2rad(th_h) * POLE_PAIRS
    _, CX = harm_fit(theta_eh, BX, NH)
    _, CY = harm_fit(theta_eh, BY, NH)
    ns = np.arange(1, NH + 1)
    delta = 1.0 / np.sqrt(np.pi * ns * f_e * MU0 * SIGMA)
    eta = (h_c_mm * 1e-3) / delta
    g = g_kernel(eta, w_c_mm * 1e-3, h_c_mm * 1e-3)
    B2 = np.abs(CX) ** 2 + np.abs(CY) ** 2       # (NH, 6) peak^2
    p_hy = g * B2.sum(axis=1)

    af_n = np.where(p_hy > 0, p_ts / np.maximum(p_hy, 1e-30), np.nan)
    tot_ts, tot_hy = p_ts.sum(), p_hy.sum()

    print("\n[%s]  TS blocks %d (span %.3f periods)  HY blocks %d"
          "  f_e=%g Hz" % (tag, len(th), span, len(th_h), f_e))
    print("%3s %6s %11s %11s %9s %9s %7s"
          % ("n", "eta_n", "P_TS[W/m]", "P_HY[W/m]", "shareTS%",
             "shareHY%", "AF_n"))
    for i, n in enumerate(ns):
        if p_ts[i] / tot_ts < 0.002 and p_hy[i] / tot_hy < 0.002:
            continue
        af_s = ("%7.3f" % af_n[i] if p_hy[i] / tot_hy > 1e-3 else "    ---")
        print("%3d %6.2f %11.4g %11.4g %9.2f %9.2f %s"
              % (n, eta[i], p_ts[i], p_hy[i], 100 * p_ts[i] / tot_ts,
                 100 * p_hy[i] / tot_hy, af_s))
    print("    totals: TS %.4g  HY %.4g  ratio %.3f   "
          "Parseval closure %+.3f%% (direct %.4g, harmonic %.4g W/m)"
          % (tot_ts, tot_hy, tot_ts / tot_hy, closure_pct, p_direct, p_harm))

    return {
        "n": ns.tolist(), "eta_n": eta.tolist(),
        "p_ts_Wpm": p_ts.tolist(), "p_hy_Wpm": p_hy.tolist(),
        "af_n": af_n.tolist(),
        "total_ratio": float(tot_ts / tot_hy),
        "n_blocks_ts": int(len(th)), "n_blocks_hy": int(len(th_h)),
        "span_periods_ts": float(span),
        "p_direct_Wpm": p_direct, "p_harm_Wpm": p_harm,
        "parseval_closure_pct": float(closure_pct),
        "files": [os.path.basename(os.path.dirname(ts_path)),
                  os.path.basename(os.path.dirname(hy_path))],
    }


def judge(res: dict, tol_pct: float) -> int:
    worst = 0.0
    missing = False
    for tag in CASES:
        r = res.get(tag)
        if r is None:
            print("[%s] no result stored" % tag)
            missing = True
            continue
        c = r.get("parseval_closure_pct")
        if c is None:
            print("[%s] total ratio %.3f -- closure not stored (JSON "
                  "predates this check); run --recompute"
                  % (tag, r["total_ratio"]))
            missing = True
            continue
        print("[%s] closure %+.3f%%  (direct %.4g, harmonic %.4g W/m; "
              "TS/HY total ratio %.3f)"
              % (tag, c, r["p_direct_Wpm"], r["p_harm_Wpm"],
                 r["total_ratio"]))
        worst = max(worst, abs(c))
    if missing:
        print("FAIL: closure values missing -- %s" % CLAIM)
        return 1
    ok = worst <= tol_pct
    print("%s: max |closure| %.3f%% vs tolerance %.2f%% -- %s"
          % ("PASS" if ok else "FAIL", worst, tol_pct, CLAIM))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--recompute", action="store_true",
                    help="re-parse the eight raw exports instead of "
                         "reading the shipped JSON")
    ap.add_argument("--out", default=os.path.join(
        repro_env.checks_dir(), "ts_harmonic_af.json"))
    ap.add_argument("--tol", type=float, default=0.6,
                    help="max allowed |Parseval closure| in percent")
    a = ap.parse_args()

    print("Check (Sec. 5.1): Parseval closure of the harmonic loss "
          "decomposition, slot-1 conductors, Ref/SC x 16k/8k")
    if a.recompute:
        res = {}
        for tag, (model, rpm, amp, f_e, w_c, h_c) in CASES.items():
            res[tag] = run_case(tag, model, rpm, amp, f_e, w_c, h_c)
        res["_meta"] = {
            "slot": SLOT, "sigma": SIGMA, "pole_pairs": POLE_PAIRS,
            "nh": NH,
            "note": "P_n = Parseval order decomposition of the slot-1 "
                    "induced (proximity) loss; HYB uses a single "
                    "g(eta_n)|B_n|^2 (production-hybrid convention). "
                    "parseval_closure_pct = 100 (p_harm / p_direct - 1).",
        }
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
        print("\nsaved:", a.out)
    else:
        if not os.path.isfile(a.out):
            print("[missing input] %s\n  Run with --recompute (raw exports "
                  "required), or restore the shipped checks/ JSON." % a.out)
            return 1
        res = json.load(open(a.out, encoding="utf-8"))
    return judge(res, a.tol)


if __name__ == "__main__":
    raise SystemExit(main())
