#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Entry point of the reproduction package.

::

    python repro.py figs [--quick]   rebuild the Python-drawn figures
    python repro.py checks           run the five verification checks
    python repro.py audit            recompute the headline wMAE table
    python repro.py all              figs + checks + audit

Everything runs against the shipped ``data/e10`` tree; set ``JEET_DATA_ROOT``
and ``JEET_FIGDIR`` to relocate input and output.  Fig. 11 is the one
MATLAB-drawn figure (``scripts/plotFig15Effmaps.m``); see the README.
"""
from __future__ import annotations

import argparse
import os
import runpy
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

os.environ.setdefault("JEET_DATA_ROOT", os.path.join(ROOT, "data", "e10"))
os.environ.setdefault("JEET_FIGDIR", os.path.join(ROOT, "fig_out"))
os.environ.setdefault("MPLBACKEND", "Agg")

DATA = os.environ["JEET_DATA_ROOT"]
FIGDIR = os.environ["JEET_FIGDIR"]
RESULTS = os.environ.setdefault("JEET_RESULTS_DIR",
                                os.path.join(DATA, "results"))

#: (script, label, extra argv, slow).  ``figs --quick`` skips the slow ones
#: (multi-seed sweeps that take tens of minutes).
FIGS = [
    ("scripts/run_fig2_acdc_ratio.py",     "Fig 1",          [], False),
    ("scripts/run_fig1_shared_scale.py",   "Fig 2",          [], False),
    ("scripts/run_fig11_mvp_field.py",     "Fig 3",          [], False),
    ("scripts/run_fig4_ts_hyb_ratio.py",   "Fig 4",          [], False),
    ("scripts/run_workflow_fig.py",        "Fig 5",          [], False),
    ("scripts/run_af_transfer_fig.py",     "Fig 6",          [], False),
    ("scripts/run_manuscript_figs78.py",   "Fig 7 + C.1",    [], True),
    ("scripts/run_geometry_fig.py",        "Fig 8",          [], False),
    ("scripts/run_flux_torque_fig.py",     "Fig 9",          [], False),
    ("scripts/run_fig10_validation.py",    "Fig 10",         [], False),
    ("scripts/run_figA1_eddy_factors.py",  "Fig A.1",        [], False),
    ("scripts/run_fig_hybrid_variants.py", "Fig B.1",        [], False),
    ("scripts/run_ref_ablation.py",        "Fig C.2",        [], False),
    ("scripts/run_open_denominator_refit.py", "Appendix B",  [], False),
    ("scripts/run_form_study.py",          "Table C",
     ["--out", os.path.join(RESULTS, "form_study.json")],        True),
]

CHECKS = [
    ("checks/check_conductor_currents.py", "conductor currents (4 s.f.)"),
    ("checks/check_parseval.py",           "Parseval closure (0.6%)"),
    ("checks/check_torque_methods.py",     "three torques (1%)"),
    ("checks/check_similarity_pairs.py",   "24 similarity pairs (1.6%)"),
    ("checks/check_field_similarity.py",   "field-level similarity"),
]


def run_script(rel, extra_argv):
    """Execute one script as ``__main__``; return its exit code."""
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        print("[absent] %s" % rel)
        return 1
    argv_save = sys.argv
    sys.argv = [path] + list(extra_argv)
    t0 = time.time()
    try:
        runpy.run_path(path, run_name="__main__")
        code = 0
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else \
            (0 if exc.code is None else 1)
    except Exception:                                  # noqa: BLE001
        traceback.print_exc()
        code = 1
    finally:
        sys.argv = argv_save
    print("[%s] %s  (%.0f s, exit %d)"
          % ("ok" if code == 0 else "FAIL", rel, time.time() - t0, code))
    return code


def cmd_figs(quick):
    os.makedirs(FIGDIR, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)
    failed = []
    for rel, label, extra, slow in FIGS:
        if quick and slow:
            print("[skip] %s  (%s -- slow, rerun without --quick)"
                  % (rel, label))
            continue
        print("\n=== %s  (%s) ===" % (label, rel))
        code = run_script(rel, extra)
        if code != 0:
            failed.append((rel, code))
    print("\nFig 11 is MATLAB-drawn: run scripts/plotFig15Effmaps.m "
          "(see README).")
    return summarize("figs", failed)


def cmd_checks():
    failed = []
    for rel, label in CHECKS:
        print("\n=== %s  (%s) ===" % (label, rel))
        code = run_script(rel, [])
        if code != 0:
            failed.append((rel, code))
    return summarize("checks", failed)


def summarize(what, failed):
    print()
    if not failed:
        print("[%s] all passed" % what)
        return 0
    print("[%s] %d failure(s):" % (what, len(failed)))
    for rel, code in failed:
        print("   exit %d  %s" % (code, rel))
    return 1


def cmd_audit():
    """Headline numbers recomputed from the shipped Map_Summary JSONs.

    Prints, per machine, the sample-candidate pool, the evaluated load
    points, and the loss-weighted map error before and after calibration.
    With ``JEET_TEX`` pointing at the manuscript source, the printed
    headline strings are also searched for in the text.
    """
    import io
    import numpy as np
    from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder as RB
    from jeet_acloss_rbf.AcLossJsonReader import AcLossJsonReader
    from jeet_acloss_rbf.pipeline import AcLossPipeline, DEFAULT_CONFIG

    tex_path = os.environ.get("JEET_TEX")
    big = 1e9

    def wmae(e, w):
        return float(np.sum(np.abs(e) * w) / np.sum(w))

    rows = []
    for scale in ("Ref", "HalfSC", "SC"):
        path = os.path.join(DEFAULT_CONFIG["data_root"],
                            DEFAULT_CONFIG["json"][scale])
        recs, err = AcLossJsonReader.read(path, scale)
        assert err is None, err
        m = AcLossPipeline().build_model(scale)
        pool = RB.match_records_and_create_dataset(recs, 50.0, 0.3, 3.0)
        ds = RB.match_records_and_create_dataset(recs, 50.0, 0.0, big)
        af = m.predict(ds.speeds_k * 1000.0, ds.irms_arr, ds.phase_arr)
        e = (ds.h_ac_arr * af - ds.f_ac_arr) / (ds.f_ac_arr + 1e-12) * 100
        r = (ds.h_ac_arr - ds.f_ac_arr) / (ds.f_ac_arr + 1e-12) * 100
        rows.append((scale, len(pool), len(ds),
                     wmae(r, ds.f_ac_arr), wmae(e, ds.f_ac_arr)))

    print("%-8s %6s %6s %12s %12s" % ("model", "pool", "eval",
                                      "uncorr.%", "corrected%"))
    for s, npool, neval, r, w in rows:
        print("%-8s %6d %6d %12.1f %12.2f" % (s, npool, neval, r, w))

    tex = ""
    if tex_path and os.path.exists(tex_path):
        tex = io.open(tex_path, encoding="utf-8", errors="replace").read()
    if tex:
        lo, hi = min(x[4] for x in rows), max(x[4] for x in rows)
        rlo, rhi = min(x[3] for x in rows), max(x[3] for x in rows)
        want = "%.0f--%.0f" % (round(rlo), round(rhi))
        want2 = "%.1f--%.1f" % (lo, hi)
        print("\nheadline strings in the manuscript:")
        for pat in (want, want2):
            print("   %-12s %s" % (pat,
                                   "found" if pat in tex else ">>> MISMATCH"))
        for s, _npool, _neval, _r, w in rows:
            tag = "%.2f" % w
            print("   %-8s %-6s %s"
                  % (s, tag,
                     "found" if tag in tex else "(not printed -- verify)"))
    elif tex_path:
        print("\n[!] JEET_TEX points at a missing file: %s" % tex_path)
    else:
        print("\n(set JEET_TEX to the manuscript .tex to diff the "
              "headline strings)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_figs = sub.add_parser("figs", help="rebuild the Python-drawn figures")
    p_figs.add_argument("--quick", action="store_true",
                        help="skip the slow multi-seed sweeps")
    sub.add_parser("checks", help="run the five verification checks")
    sub.add_parser("audit", help="recompute the headline wMAE table")
    p_all = sub.add_parser("all", help="figs + checks + audit")
    p_all.add_argument("--quick", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "figs":
        return cmd_figs(a.quick)
    if a.cmd == "checks":
        return cmd_checks()
    if a.cmd == "audit":
        return cmd_audit()
    code = cmd_figs(a.quick)
    code = cmd_checks() or code
    return cmd_audit() or code


if __name__ == "__main__":
    raise SystemExit(main())
