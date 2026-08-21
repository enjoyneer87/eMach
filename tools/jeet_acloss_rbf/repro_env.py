# -*- coding: utf-8 -*-
"""Path resolution shared by the eMach worktree and the reproduction package.

The same script must run in three places without edits:

* inside the published package (``<pkg>/jeet_acloss_rbf/`` next to
  ``<pkg>/data/e10`` and ``<pkg>/repro.py``),
* inside the eMach worktree (``<wt>/tools/jeet_acloss_rbf`` with data under
  ``<wt>/mlxperPJT/JEET/map_exports/e10``),
* on the author's machine with the raw field exports.

Environment variables, all optional:

``JEET_DATA_ROOT``   reduced data root (``data/e10`` layout).  When it also
                     holds a ``fea/`` directory in the Zenodo layout
                     (``fea/{Model}_{Mode}_Speed_{rpm}RPM_{I}A_{beta}deg.txt.gz``),
                     raw exports are resolved from there.
``JEET_FEA_ROOT``    author's raw tree (``D:\\KangDH\\Thesis\\e10``) holding
                     ``_txt_backfill/<Model>/<Mode>_Speed_...deg/FEA_data.txt.gz``.
``JEET_FIGDIR``      where figures are written (default ``<root>/fig_out``).
``JEET_RESULTS_DIR`` where long sweeps cache their JSON (default
                     ``<data_root>/results``).
"""
from __future__ import annotations

import os
from typing import Optional

ZENODO_DOI = "10.5281/zenodo.21775297"
ZENODO_URL = "https://doi.org/" + ZENODO_DOI

_HERE = os.path.dirname(os.path.abspath(__file__))


def package_root() -> Optional[str]:
    """``<pkg>`` when this module lives in the published package."""
    up = os.path.dirname(_HERE)
    if os.path.isdir(os.path.join(up, "data", "e10")) and \
            os.path.isfile(os.path.join(up, "repro.py")):
        return up
    return None


def worktree_jeet() -> Optional[str]:
    """``<wt>/mlxperPJT/JEET`` when this module lives in the eMach worktree."""
    wt = os.path.dirname(os.path.dirname(_HERE))
    j = os.path.join(wt, "mlxperPJT", "JEET")
    return j if os.path.isdir(j) else None


def data_root() -> str:
    env = os.environ.get("JEET_DATA_ROOT")
    if env:
        return env
    pkg = package_root()
    if pkg:
        return os.path.join(pkg, "data", "e10")
    j = worktree_jeet()
    if j:
        return os.path.join(j, "map_exports", "e10")
    return os.path.join(os.getcwd(), "data", "e10")


def fig_dir() -> str:
    env = os.environ.get("JEET_FIGDIR")
    if env:
        return env
    base = package_root() or worktree_jeet() or os.getcwd()
    return os.path.join(base, "fig_out")


def results_dir() -> str:
    return os.environ.get("JEET_RESULTS_DIR",
                          os.path.join(data_root(), "results"))


def checks_dir() -> str:
    return os.path.join(data_root(), "checks")


# ── raw field exports ─────────────────────────────────────────────────────

def op_stem(mode: str, rpm: float, amp_a: float, phase_deg: float) -> str:
    """``FullFEA_Speed_16000RPM_460.0A_36.0deg`` — the campaign naming."""
    return "%s_Speed_%dRPM_%.1fA_%.1fdeg" % (mode, int(round(rpm)), amp_a,
                                             phase_deg)


def zenodo_name(model: str, mode: str, rpm: float, amp_a: float,
                phase_deg: float) -> str:
    """File name inside the Zenodo deposit's ``fea/`` directory."""
    return "%s_%s.txt.gz" % (model, op_stem(mode, rpm, amp_a, phase_deg))


# author-side trees that hold exports the campaign grid did not
_BACKFILL_ALIASES = {
    # (model, mode) -> sub-directory under _txt_backfill
    ("HalfSC", "Hybrid"): ("HalfSC", "HalfSC_campaign"),
}


def raw_export(model: str, mode: str, rpm: float, amp_a: float,
               phase_deg: float) -> Optional[str]:
    """Path of one time-stepped export, or ``None`` if not present locally.

    Search order: ``JEET_DATA_ROOT/fea`` (Zenodo layout), then
    ``JEET_FEA_ROOT/_txt_backfill/...`` and the campaign folders.
    """
    name = zenodo_name(model, mode, rpm, amp_a, phase_deg)
    stem = op_stem(mode, rpm, amp_a, phase_deg)
    cands = [os.path.join(data_root(), "fea", name)]
    fea = os.environ.get("JEET_FEA_ROOT")
    if fea:
        subs = _BACKFILL_ALIASES.get((model, mode), (model,))
        for sub in subs:
            for fn in ("FEA_data.txt.gz", "FEA_data.txt"):
                cands.append(os.path.join(fea, "_txt_backfill", sub, stem, fn))
        campaign = {"Ref": "refModel", "HalfSC": "SLFEA_Half", "SC": "SLFEA"}
        if model in campaign:
            for fn in ("FEA_data.txt.gz", "FEA_data.txt"):
                cands.append(os.path.join(fea, campaign[model],
                                          "ACLossCalcExport_Map", stem, fn))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def require(path: Optional[str], what: str, in_deposit: bool = True) -> str:
    """Return ``path`` or stop with a message that says where to get it.

    Exit code 1 when the file is simply not downloaded; exit code 2 when
    the raw data behind ``what`` is not part of the Zenodo deposit at all
    (the HalfSC sweep was left out of the deposit by the author).
    """
    if path and os.path.isfile(path):
        return path
    if in_deposit:
        print("[missing input] %s\n"
              "  Download it from the data deposit (%s) into "
              "$JEET_DATA_ROOT/fea/, or point JEET_FEA_ROOT at the raw tree."
              % (what, ZENODO_URL))
        raise SystemExit(1)
    print("[not reproducible from the deposit] %s\n"
          "  The HalfSC raw sweep is not part of %s (author decision, "
          "2026-08-03); only the shipped result JSON is available."
          % (what, ZENODO_URL))
    raise SystemExit(2)
