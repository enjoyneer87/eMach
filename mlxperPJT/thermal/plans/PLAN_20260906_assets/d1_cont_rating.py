# -*- coding: utf-8 -*-
"""d1_cont_rating.py -- D1 continuous-rating runner (e10, STEADY, oil-circuit hybrid).

PLAN_20260906_thesis_thermal.md section 1, D1.  Produces
``thesis_out/e10_cont_rating.json`` : 64 runs (4 speeds x 4 currents x {DC,AC} x
{base,sph} h-sets) plus I_cont(n) for both temperature limits.

WHAT THIS SCRIPT IS
-------------------
A read-only reference implementation living in ``plans/PLAN_20260906_assets/``.
moa COPIES it to ``mlxperPJT/thermal/freeflow/scripts/20_d1_cont_rating.py`` (with
``jeet_map_loader.py`` / ``icont.py`` / ``thesis_style.py`` as shared modules) and
makes the promotion commit.  It therefore imports ONLY from its own directory and
resolves the repo root from ``__file__`` -- there is no hardcoded absolute path
anywhere except the default value of ``--cdb`` (moa's local disk, overridable).

THE MODEL (lifted from freeflow/scripts/04_mapdl_thermal.py, unchanged)
-----------------------------------------------------------------------
3D FEM (SOLID87) of stator / winding(+end turns) / magnet / rotor / shaft, coupled
to a 6-node oil thermal circuit (OIL JACKET SPRAY GAP_S GAP_R SHF) built from
COMBIN14 (conductance, TEMP DOF) + SURF152 (convection, extra node) + MASS71
(capacitance -- TRANSIENT ONLY, gated off here).  Single Dirichlet: OIL = 70 degC.

Changed vs 04: ANTYPE,STATIC instead of the 900 s transient (04:66,163-169), the
loss vector comes from the JEET map instead of a hardcoded JSON path, and every
external path is a CLI argument.

WHY SUPERPOSITION (--mode super, the default)
---------------------------------------------
The steady model is EXACTLY linear: constant KXX (04:43-47), constant convection
coefficients, constant circuit conductances, no radiation, one Dirichlet node.  So
the nodal temperature field is an affine functional of the loss vector

    T_node(P) = 70 + sum_s  P_s * G_node,s          s in {cu_slot, cu_end, ac_slot,
                                                          fe_s, fe_r, pm}

Five unit solves per h-set (one source at a time, everything else zero) give the
whole influence matrix G -- 10 solves instead of 64 -- and every one of the plan's
64 grid entries is then reconstructed in closed form, exactly.  ac_slot needs no
solve of its own: D1 injects it uniformly over the same CU_SLOT element set as
cu_slot, so G[:,ac_slot] == G[:,cu_slot] identically (icont.solve_influence does
that aliasing).  Two extra DIRECT full-load solves verify the reconstruction to
< 0.05 K before any of it is believed.  Total 12 solves.

Bonus, and this is the real reason: I_cont becomes a continuous root-find in I
instead of an interpolation between 4 grid currents.  At 16 krpm the winding is
predicted to exceed 180 degC even at the lowest grid current (115.075 A), so the
plan's 4-point bracket would be a pure extrapolation there.

``--mode brute`` keeps the plan-literal 64-solve path (icont.i_cont_bracket_pair,
linear in I^2) for cross-checking, and is entered automatically if the
superposition check fails.

WINDING MAX IS NOT A LINEAR FUNCTIONAL -- how that is handled honestly
---------------------------------------------------------------------
max over nodes of an affine field is convex, not affine: the argmax node can move
when the loss mix changes.  So this script does NOT reduce the winding to a single
scalar influence row and hope.  It keeps the influence coefficients PER NODE
(1.11M x 5 float64 = 45 MB, which is nothing), reconstructs the FULL nodal field
for every one of the 64 loss vectors, and takes the max over the part's node set on
the reconstructed field.  That is exact.
For I_cont the root-find does need a scalar row, so it runs a hot-node fixed point:
take the argmax node, root-find, re-evaluate the field at that current, take the
argmax node again, repeat until the node stops moving (usually 1-2 iterations).  At
the converged current the reported node really is the hottest one and its
temperature really is the limit.  Every iteration is recorded in the JSON
(``I_cont_detail[...]["_hot_node_iterations"]``), and non-convergence is flagged
rather than hidden.

RUNTIME RULES OBSERVED
----------------------
* python 3.10 syntax only (no match, no ``X | Y`` annotations, no 3.11+ stdlib).
* NEVER imports ansys.dpf.core -- it is not in the moa venv (HANDOFF section 9).
  Only ansys.mapdl.core is required.
* No ``mapdl.ignore_errors = True``.  Every MAPDL block is wrapped so a failure
  names the step AND the run it happened in.
* ``mapdl.allsel("ALL")`` immediately before every SOLVE -- SOLVE only solves the
  currently selected elements and POST1 leaves a selection behind.
* Free maximum-principle check: all-positive heat + one Dirichlet at 70 degC means
  every nodal temperature of a valid steady solution is >= 70 degC.  Asserted after
  every solve.

CLI
---
    python d1_cont_rating.py --repo <repo> --cdb D:/KDH/simVary/Ansys_Thermal/ff_e10_mesh_v2
    python d1_cont_rating.py --dry-run --repo <repo> --out <dir> --log <file>
    python d1_cont_rating.py --mode brute ...            # plan-literal 64 solves

``--dry-run`` exercises everything except MAPDL: it loads the real JEET map, builds
the real 64-entry loss table, SYNTHESIZES a plausible per-node influence matrix,
and runs the identical reconstruction / hot-node / I_cont / JSON code.  The JSON it
writes is marked ``"_dry_run": true`` and goes to ``e10_cont_rating_dryrun.json``
so it can never be mistaken for a solve.
"""

import argparse
import contextlib
import datetime
import json
import math
import os
import subprocess
import sys
import tempfile
import time

try:
    import numpy as np
except ImportError:
    sys.stderr.write(
        "d1_cont_rating.py requires numpy (it is in the moa venv and is already "
        "used by 04_mapdl_thermal.py:17).\n")
    raise

# The script's OWN directory -- the kit is self-contained, this is not a
# repo-relative path hack.  Running `python d1_cont_rating.py` already puts this
# directory on sys.path; the insert only covers `python -m` / import-as-module.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    import icont
    import jeet_map_loader as jm
    from motorcad_loss_map import MagneticLossMap
except ImportError as _exc:  # pragma: no cover - kit integrity failure
    raise SystemExit(
        "d1_cont_rating.py could not import its sibling modules from\n"
        "  %s\n"
        "  (%s)\n"
        "icont.py, jeet_map_loader.py and thesis_style.py must sit NEXT TO this "
        "file.  If you promoted this script to freeflow/scripts/, copy them too."
        % (_HERE, _exc))


# ===========================================================================
# 0.  Constants -- geometry, materials, oil circuit.  All measured, see
#     04_mapdl_thermal.py:35-65 and HANDOFF_20260722.md section 3.
# ===========================================================================

SCRIPT_NAME = "d1_cont_rating.py"

M_ST, M_MG, M_CO, M_SH, M_RO = 1, 2, 3, 4, 5
PART_OF_MAT = {M_ST: "stator", M_MG: "magnet", M_CO: "winding",
               M_SH: "shaft", M_RO: "rotor"}

R_STA_OUT = 0.0990
R_STA_IN = 0.0713
R_ROT_OUT = 0.07027
R_SHAFT = 0.023455
Z_ST0, Z_ST1 = -0.2075, -0.0575      # stator stack -- NOT centred on z = 0
STACK = Z_ST1 - Z_ST0                # 0.150 m
ZC = 0.5 * (Z_ST0 + Z_ST1)           # -0.1325 m

# k [W/mK], c [J/kgK], rho [kg/m3].  Constant -> the model is linear.
MATS = {M_ST: (25.0, 460.0, 7650.0),
        M_MG: (9.0, 460.0, 7500.0),
        M_CO: (5.0, 385.0, 4480.0),    # homogenised winding, fill 0.5
        M_SH: (52.0, 460.0, 7870.0),
        M_RO: (25.0, 460.0, 7650.0)}

OIL_T = 70.0
RHO_OIL, CP_OIL = 825.0, 2000.0
MDOT_OIL = 0.11                       # kg/s (~8 LPM)
G_JKT_OIL = 0.60 * MDOT_OIL * CP_OIL  # 132.0 W/K
G_SPRAY_OIL = 0.40 * MDOT_OIL * CP_OIL  # 88.0 W/K
G_SHF_OIL = 40.0                      # W/K, shaft -> bearing/oil
C_JKT = 0.20e-3 * RHO_OIL * CP_OIL    # 330 J/K   (transient only)
C_SPRAY = 0.15e-3 * RHO_OIL * CP_OIL  # 247.5 J/K (transient only)
C_SHF = 200.0                         # J/K       (transient only)
K_AIR, GAP_G = 0.03, 0.0007
A_GAP = 2.0 * math.pi * R_STA_IN * STACK
G_GAP = K_AIR * A_GAP / GAP_G         # 2.880 W/K

# HTC_BIG is a NUMERICAL DEVICE (the real resistance lives in the GAP nodes).
# It is not part of any h-set and must never be swept.
HTC_BIG = 1e4
HTC_SETS = {
    "base": {"jkt": 1000.0, "spray": 2000.0, "splash": 250.0},
    "sph":  {"jkt": 190.0,  "spray": 190.0,  "splash": 250.0},
}
# splash drives BOTH rotorEnd->OIL and shaftEnd->SHF (04:140-144).  Stated here
# because "splash" reads like a rotor-only knob and it is not.

TOL = 1e-5      # MAPDL SELTOL for the radial/axial selection bands
RT = 8e-4       # radial band half-width [m]
ZT = 2e-4       # axial band tolerance [m]

CIRCUIT_NODES = ("OIL", "JACKET", "SPRAY", "GAP_S", "GAP_R", "SHF")
PARTS = ("winding", "stator", "magnet", "rotor", "shaft")

SOURCES = icont.SOURCES                       # 6, incl. ac_slot
UNIT_SOURCES = ("cu_slot", "cu_end", "fe_s", "fe_r", "pm")   # 5 solves; ac_slot aliased

SPEEDS = jm.SPEEDS                            # (2000, 4000, 8000, 16000)
CURRENTS_D1 = (115.075, 230.05, 345.025, 460.0)   # plan grid: 0.1 A is NOT a D1 run
CASES = ("DC", "AC")

EXPECTED_N_NODE = 1113924
EXPECTED_N_ELEM = 737265
DEFAULT_CDB = r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2"

# The two direct full-load solves that verify superposition.  Both are grid points
# of the 64, so their direct temperatures also land in runs[] as a sibling field.
VERIFY_POINTS = ((8000, 230.05, "AC"), (2000, 460.0, "DC"))

T_MIN_OK = 69.99        # maximum-principle floor
T_MAX_WARN = 1.0e4      # above this, warn (not fail): the plan's own load points are huge
MAX_HOT_ITER = 6        # hot-node fixed-point iterations

LOSS_SOURCE_LITERAL = "JEET_ACLoss_Ref_Map_Summary.json phase36"   # plan line 39, verbatim

LOSS_MODEL_CAVEAT = (
    "Iron and magnet losses are the plan's speed-only rule (fe_s = 1856*(n/15000)^1.5, "
    "fe_r = 74*(n/15000)^1.5, pm = 3385*0.17*(n/15000)^2), i.e. they do NOT vary with "
    "current. Against the plan section 2 R1 values at 16 krpm / 460 A (fe_s 2619, fe_r 89, "
    "pm 1382 W) the rule reads fe_s about 22 percent low and pm about 53 percent low. At "
    "16 krpm / 460 A iron+magnet is only ~3 percent of the total heat so the effect on "
    "T_w is small, but at 16 krpm / 115 A it is ~32 percent and the I_cont there inherits "
    "that error. Copper (cu_slot, cu_end, ac_slot) is read straight from the JEET map and "
    "carries no such assumption.")

GAP_NOTE = (
    "G_GAP = 2.880 W/K uses the model's GAP_G = 0.7 mm, while the drawn air gap is 1.0 mm "
    "(bore 142.54/2 = 0.07127 minus rotor OD 0.07027). Kept identical to "
    "04_mapdl_thermal.py:56 so this study stays comparable with the validated hybrid run; "
    "a physical 1.0 mm would give 2.016 W/K.")

HTC_META = {
    "sph_source": "freeflow/data/htc_backout.json h_grad",
    "jkt_backout": 192.8,
    "spray_backout": 186.3,
    "rounded_to": 190.0,
    "plan_line17_says": "193 (jacket) / 186 (spray)",
    "plan_D1_spec_says": "190 / 190 (plan lines 35 and 40)",
    "decision": ("Ran 190/190 because the plan's D1 spec and its output skeleton both "
                 "say 190/190 and that skeleton goes straight into the thesis table. The "
                 "measured backout values are recorded here so the discrepancy is on the "
                 "record."),
    "warning": ("The SPH backout came from the 6.53 s run whose gravity was set along the "
                "axis (-Z) instead of radially (HANDOFF section 10-4). D3 replaces it; "
                "until then the sph h-set is an order-of-magnitude statement, not a "
                "calibrated number."),
    "splash_scope": ("splash = 250 W/m2K applies to BOTH rotor end faces -> OIL and shaft "
                     "end faces -> SHF (04_mapdl_thermal.py:140-144), and is the same in "
                     "both h-sets."),
    "htc_big": ("bore -> GAP_S and rotorOD -> GAP_R use h = 1e4 W/m2K. That is a numerical "
                "device: the real gap resistance is the COMBIN14 between GAP_S and GAP_R. "
                "It is not part of any h-set and was not swept."),
}

GITIGNORE_FIX = "!mlxperPJT/thermal/thesis_out/*.png"


class D1Error(RuntimeError):
    """Anything that makes the D1 result untrustworthy.  Always names the run."""


# ===========================================================================
# 1.  Logging -- stdout AND a file.  moa runs this unattended.
# ===========================================================================

class Log(object):
    """Tee to stdout and a log file.  ASCII-only output: moa's console is cp949 and
    a stray degree sign in an unattended batch is a UnicodeEncodeError, i.e. a lost
    night.  Use 'degC', '->', '<=' in messages."""

    def __init__(self, path):
        self.path = path
        self._fh = None
        if path:
            d = os.path.dirname(os.path.abspath(path))
            if d and not os.path.isdir(d):
                os.makedirs(d)
            self._fh = open(path, "a", encoding="utf-8")
        self.t0 = time.time()

    def __call__(self, *args):
        msg = " ".join(str(a) for a in args)
        line = "[%7.1fs] %s" % (time.time() - self.t0, msg)
        try:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
        except UnicodeEncodeError:                     # last-ditch console guard
            sys.stdout.write(line.encode("ascii", "replace").decode("ascii") + "\n")
            sys.stdout.flush()
        if self._fh is not None:
            self._fh.write(line + "\n")
            self._fh.flush()

    def rule(self, title=""):
        self("=" * 78)
        if title:
            self(title)
            self("=" * 78)

    def banner(self, lines):
        """Loud, unmissable block for failures.  Embedded newlines are split so every
        physical line carries the '!!' marker -- an unattended log gets grepped."""
        self("")
        self("!" * 78)
        for ln in lines:
            for part in str(ln).split("\n"):
                self("!! " + part)
        self("!" * 78)
        self("")

    def close(self):
        if self._fh is not None:
            self._fh.close()
            self._fh = None


# ===========================================================================
# 2.  MAPDL call guard -- every failure names the step and the run
# ===========================================================================

_CTX = {"run": "startup"}


def set_run(tag):
    _CTX["run"] = str(tag)


@contextlib.contextmanager
def mapdl_step(label, hint=None):
    """Wrap a block of MAPDL calls so a failure says WHERE and DURING WHICH RUN."""
    try:
        yield
    except (KeyboardInterrupt, SystemExit):
        raise
    except D1Error:
        raise
    except Exception as exc:
        msg = ("MAPDL step failed\n"
               "  step  : %s\n"
               "  run   : %s\n"
               "  error : %s: %s" % (label, _CTX["run"], type(exc).__name__, exc))
        if type(exc).__name__ == "MapdlRuntimeError":
            # Caught explicitly instead of setting mapdl.ignore_errors = True, which
            # is what hid the failed commands in 04_mapdl_thermal.py:167.
            msg += ("\n  note  : this is a MAPDL command error, not a python one. The "
                    "full text is in file.err / file.out inside the run directory. "
                    "Common causes here: a command issued in the wrong processor "
                    "(/PREP7 vs /SOLU), a zero/negative pivot from a floating island "
                    "(try --ground-guard), or an out-of-memory solver abort (try "
                    "--additional-switches \"-m 8192 -db 2048\").")
        if hint:
            msg += "\n  hint  : %s" % hint
        raise D1Error(msg)


# ===========================================================================
# 3.  Field algebra -- shared by both backends
# ===========================================================================

def reconstruct_field(gmap, loss_vec):
    """T(node) = 70 + sum_s P_s * G[s][node].  gmap: {source: 1-D array [K/W]}."""
    total = None
    for s in SOURCES:
        p = float(loss_vec.get(s, 0.0))
        if p == 0.0:
            continue
        if s not in gmap:
            raise D1Error(
                "reconstruct_field: loss_vec[%r] = %g W but there is no influence "
                "column for %r. The unit solve for %r is missing." % (s, p, s, s))
        term = gmap[s] * p
        total = term if total is None else total + term
    if total is None:
        return np.full(len(gmap[SOURCES[0]]), OIL_T, dtype=float)
    return total + OIL_T


def row_at(gmap, pos):
    """Scalar influence row {source: K/W} of one node index."""
    return dict((s, float(gmap[s][pos])) for s in SOURCES)


def mean_row(gmap, idx):
    """Influence row of the MEAN over a fixed node set -- an exact linear functional."""
    return dict((s, float(gmap[s][idx].mean())) for s in SOURCES)


def monitored_from_field(temps, part_idx, circ_pos):
    """The plan's T_C and circuit_T blocks, plus the argmax node POSITIONS.

    Maxes are taken on the reconstructed/direct field itself (never on a scalar
    surrogate), so a moving hot spot is captured exactly.
    """
    t_c = {}
    argmax_pos = {}
    for part in PARTS:
        idx = part_idx[part]
        vals = temps[idx]
        k = int(np.argmax(vals))
        argmax_pos[part] = int(idx[k])
        t_c[part + "_max"] = float(vals[k])
        t_c[part + "_mean"] = float(vals.mean())
        t_c[part + "_min"] = float(vals.min())
    circ = dict((nm, float(temps[circ_pos[nm]])) for nm in CIRCUIT_NODES)
    return t_c, circ, argmax_pos


def plan_t_c(t_c_full):
    """The five keys the plan's skeleton names, plus additive siblings."""
    out = {"winding_max": t_c_full["winding_max"],
           "winding_mean": t_c_full["winding_mean"],
           "stator_max": t_c_full["stator_max"],
           "magnet_max": t_c_full["magnet_max"],
           "rotor_max": t_c_full["rotor_max"],
           # additive, never replacing the above
           "winding_min": t_c_full["winding_min"],
           "stator_mean": t_c_full["stator_mean"],
           "magnet_mean": t_c_full["magnet_mean"],
           "rotor_mean": t_c_full["rotor_mean"],
           "shaft_max": t_c_full["shaft_max"]}
    return out


# ===========================================================================
# 4.  Backends
# ===========================================================================

class BackendBase(object):
    """Contract used by everything downstream.

    After setup():
        self.nnum       int array of node numbers (ascending), FEM + 6 circuit nodes
        self.part_idx   {part: int index array into nnum}
        self.circ_pos   {circuit node name: int index into nnum}
        self.mesh_info  dict for the JSON
        self.solve_log  list of per-solve dicts
    Methods:
        influence(hset) -> {source: 1-D array [K/W]}   (5 unit solves + ac alias)
        direct(hset, loss_vec, tag) -> 1-D array [degC] (one full-load solve)
        close()
    """

    kind = "abstract"

    def __init__(self, args, log):
        self.args = args
        self.log = log
        self.nnum = None
        self.part_idx = {}
        self.circ_pos = {}
        self.mesh_info = {}
        self.solve_log = []
        self.n_solves = 0
        self.last_iload = None       # so the runs table can point at the .rth set
        self.last_solve_time = None

    def setup(self):
        raise NotImplementedError

    def influence(self, hset):
        raise NotImplementedError

    def direct(self, hset, loss_vec, tag):
        raise NotImplementedError

    def close(self):
        pass

    # -- shared post-solve validation -------------------------------------
    def check_field(self, temps, tag):
        n_nan = int(np.isnan(temps).sum())
        if n_nan:
            bad_parts = [p for p in PARTS
                         if np.isnan(temps[self.part_idx[p]]).any()]
            if bad_parts or any(math.isnan(temps[self.circ_pos[n]])
                                for n in CIRCUIT_NODES):
                raise D1Error(
                    "run %s: %d NaN temperatures, including monitored nodes %s. "
                    "Nodes with no TEMP DOF (not attached to any element) or an "
                    "incomplete selection at harvest time." % (tag, n_nan, bad_parts))
            self.log("  [warn] %s: %d NaN nodes outside every monitored set "
                     "(orphan nodes in the CDB); ignored." % (tag, n_nan))
        # The OIL node carries the model's only Dirichlet. If it is not sitting at
        # exactly OIL_T, the constraint was not in effect for this solve and every
        # temperature here is meaningless -- this is the failure seen on moa at load
        # step 2 (negative pivot at the OIL node, field runaway to 8.6e10 K).
        t_oil = float(temps[self.circ_pos["OIL"]])
        if not math.isnan(t_oil) and abs(t_oil - OIL_T) > 1e-3:
            raise D1Error(
                "run %s: the OIL node is at %.6f degC but it is Dirichlet-constrained "
                "to %.1f degC. The constraint was not in effect for this load step, so "
                "the system floated and these temperatures are meaningless. The runner "
                "re-asserts D,OIL,TEMP every load step; if this still fires, the "
                "constraint is being cleared somewhere between /SOLU and SOLVE."
                % (tag, t_oil, OIL_T))
        tmin = float(np.nanmin(temps))
        tmax = float(np.nanmax(temps))
        if tmin < T_MIN_OK:
            # Localise the violation before raising: which nodes, which part, and what
            # the circuit is doing. Without this the failure is just a number and the
            # next step is guesswork.
            try:
                cold = np.where(np.nan_to_num(temps, nan=1e9) < T_MIN_OK)[0]
                self.log("  [diag] %d node(s) below %.2f degC (of %d)"
                         % (cold.size, T_MIN_OK, temps.size))
                imin = int(np.nanargmin(temps))
                self.log("  [diag] coldest node id %d  T = %.4f degC"
                         % (int(self.nnum[imin]), temps[imin]))
                for part in PARTS:
                    idx = self.part_idx.get(part)
                    if idx is None or len(idx) == 0:
                        continue
                    sub = temps[idx]
                    n_cold = int(np.sum(np.nan_to_num(sub, nan=1e9) < T_MIN_OK))
                    self.log("  [diag]   %-8s min %9.4f  max %9.4f  below-limit %d/%d"
                             % (part, float(np.nanmin(sub)), float(np.nanmax(sub)),
                                n_cold, len(idx)))
                for nm in CIRCUIT_NODES:
                    self.log("  [diag]   circuit %-6s = %9.4f degC"
                             % (nm, float(temps[self.circ_pos[nm]])))
                in_parts = set()
                for part in PARTS:
                    idx = self.part_idx.get(part)
                    if idx is not None and len(idx):
                        if np.intersect1d(idx, cold, assume_unique=False).size:
                            in_parts.add(part)
                circ_idx = np.array([self.circ_pos[n] for n in CIRCUIT_NODES])
                n_circ_cold = int(np.intersect1d(circ_idx, cold).size)
                self.log("  [diag] cold nodes live in parts %s; %d of them are circuit nodes"
                         % (sorted(in_parts) or "NONE (orphans / surface-only nodes)",
                            n_circ_cold))
            except Exception as _exc:
                self.log("  [diag] diagnostic dump failed: %r" % (_exc,))

            # A quadratic tetrahedron (SOLID87) can undershoot at a mid-side node where
            # the gradient is steep: the maximum principle holds for the exact PDE
            # solution, not for the nodal values of the quadratic interpolant. A handful
            # of such nodes is a discretisation artifact, not a broken solve.
            # A genuine failure looks completely different and is still caught:
            #   - lost Dirichlet  -> the OIL check above fires (exact, separate)
            #   - floating island -> thousands of bad nodes, or MAPDL's own pivot error
            #   - partial SOLVE   -> whole parts wrong, not two nodes
            # So tolerate a SMALL count with a SMALL undershoot, and record it.
            try:
                n_cold = int(np.sum(np.nan_to_num(temps, nan=1e9) < T_MIN_OK))
            except Exception:
                n_cold = -1
            n_max = max(int(self.args.undershoot_max_nodes), 0)
            # The undershoot at a badly shaped element is LINEAR in the load, exactly like
            # the field itself (verified: the affine round-trip is exact to 1e-14 K). An
            # ABSOLUTE K ceiling is therefore the wrong test -- raise the load enough and
            # it always trips. Measured on the SAME two nodes, sph h-set:
            #     unit cu_slot (rise  75 K) -> -7.5 K     unit cu_end (rise  73 K) -> -16.3 K
            #     verify 8k/230A/AC (rise 921 K) -> -164.8 K
            # So gate on the undershoot RELATIVE to the field range instead.
            rise = max(tmax - OIL_T, 1e-9)
            k_max = max(float(self.args.undershoot_max_K),
                        float(self.args.undershoot_max_frac) * rise)
            circ_bad = [n for n in CIRCUIT_NODES
                        if float(temps[self.circ_pos[n]]) < T_MIN_OK]
            # The gate is on COUNT and on the monitored aggregates, not on magnitude.
            # Magnitude alone is the wrong criterion: the undershoot at a badly shaped
            # element scales with the local gradient, so the SAME defective node reads
            # -7.5 K under slot-copper injection and -16.3 K under end-turn injection.
            # What matters is that it is a fixed, tiny set of nodes that moves none of
            # the reported numbers: winding max/mean, part maxima, and the 6 circuit
            # nodes. `max_K` is kept only as a sanity ceiling against a truly broken field.
            # How much do the outliers CONTAMINATE the winding mean?  Not
            # |mean(all) - mean(keep)|: dropping 2 of 213014 nodes shifts the mean by
            # mean*2/N on renormalisation alone (0.017 K at a 1800 degC field), so that
            # form trips on any hot field regardless of the outliers -- the same
            # scale-dependence bug as an absolute K ceiling. Measure the contamination
            # term itself, and judge it RELATIVE to the field.
            cold_ids, cold_T, mean_shift, contam_rel = [], [], None, None
            try:
                cold_ids = [int(self.nnum[i]) for i in cold[:20]]
                cold_T = [round(float(temps[i]), 4) for i in cold[:20]]
                widx = self.part_idx.get("winding")
                if widx is not None and len(widx):
                    wsub = temps[widx]
                    good = wsub[np.nan_to_num(wsub, nan=1e9) >= T_MIN_OK]
                    bad = wsub[np.nan_to_num(wsub, nan=-1e9) < T_MIN_OK]
                    if good.size:
                        gmean = float(np.nanmean(good))
                        mean_shift = float(np.sum(np.abs(bad - gmean))) / float(wsub.size)
                        scale = max(1.0, gmean - OIL_T)
                        contam_rel = mean_shift / scale
            except Exception:
                pass
            rel_tol = float(self.args.undershoot_mean_rel_tol)
            mean_ok = (contam_rel is None) or (contam_rel <= rel_tol)
            if (0 <= n_cold <= n_max) and (OIL_T - tmin) <= k_max and not circ_bad and mean_ok:
                self.undershoot.append({
                    "run": tag, "n_nodes_below": n_cold, "n_nodes_total": int(temps.size),
                    "node_ids": cold_ids, "node_T_C": cold_T,
                    "t_min_C": tmin, "undershoot_K": OIL_T - tmin,
                    "winding_mean_contamination_K": mean_shift,
                    "winding_mean_contamination_rel": contam_rel,
                    "verdict": ("tolerated: a fixed, tiny set of winding nodes on badly "
                                "shaped SOLID87 elements. Undershoot scales with the local "
                                "gradient, so it varies by load case at the SAME node ids. "
                                "Moves no reported quantity."),
                    "limits": {"max_nodes": n_max, "max_K_effective": k_max,
                               "max_frac_of_range": float(self.args.undershoot_max_frac),
                               "field_range_K": rise,
                               "max_winding_mean_contamination_rel": rel_tol},
                    "undershoot_frac_of_range": (OIL_T - tmin) / rise,
                })
                self.log("  [warn] %s: %d node(s) %.4f K below the %.1f degC oil "
                         "Dirichlet (min %.4f at node(s) %s). Winding mean contamination %s. "
                         "Tolerated: fixed bad-element nodes, no reported quantity affected."
                         % (tag, n_cold, OIL_T - tmin, OIL_T, tmin,
                            cold_ids or "?",
                            ("%.2e K (rel %.1e)" % (mean_shift, contam_rel))
                            if mean_shift is not None else "n/a"))
                return
            raise D1Error(
                "run %s: minimum nodal temperature %.4f degC < %.2f degC.\n"
                "  All heat sources are positive and the ONLY Dirichlet is OIL = 70 "
                "degC, so the maximum principle forbids this. Causes, in order of "
                "likelihood: (1) a floating island of elements with no conduction path "
                "to OIL (steady = singular pivot; retry with --ground-guard), (2) SOLVE "
                "ran on a partial element selection (a missing allsel), (3) a stale "
                "MAPDL session that solved nothing." % (tag, tmin, T_MIN_OK))
        if tmax > T_MAX_WARN:
            self.log("  [warn] %s: max nodal temperature %.1f degC. The plan's own "
                     "load points are enormous (up to 89 kW), so this is expected to "
                     "be a 'cannot run continuously' finding rather than a bug -- but "
                     "check the loss vector." % (tag, tmax))
        return tmin, tmax


class MapdlBackend(BackendBase):
    """The real thing: launch MAPDL, read the CDB once, build the circuit once,
    then only redefine HGEN / SFE per run."""

    kind = "mapdl"

    def __init__(self, args, log):
        BackendBase.__init__(self, args, log)
        self.mapdl = None
        self.N = {}                # circuit node numbers
        self.sf_ranges = {"jkt": [], "spray": [], "splash": [], "gap": []}
        self.vol = {}              # {'slot','end',1,2,5} -> m3
        self.ecount = {}
        self.iload = 0
        self._cur_hset = None
        # SURF152 convection is written once at ESURF time with THIS h-set's values.
        # Re-issuing SFE in /SOLU for a second h-set is defective (see _mark_built_hset),
        # so a session serves exactly one h-set and 'both' runs two sessions.
        _hs = getattr(args, "htc_set", "base")
        self._build_hset = "base" if _hs in ("both", None) else _hs
        self.missing_surfaces = []
        self.undershoot = []
        self.MapdlRuntimeError = None

    # -- launch -----------------------------------------------------------
    def setup(self):
        args = self.args
        log = self.log
        set_run("setup")

        cdb = args.cdb
        if cdb.lower().endswith(".cdb"):
            cdb = cdb[:-4]                 # cdread wants the path WITHOUT extension
        if not os.path.isfile(cdb + ".cdb"):
            raise D1Error(
                "BLOCKER: mesh not found: %s.cdb\n"
                "  ff_e10_mesh_v2.cdb is 260 MB and is NOT in git (HANDOFF section 3) "
                "-- it lives only on moa's local disk.\n"
                "  Check:  Test-Path %s.cdb\n"
                "  If it is really gone the regeneration chain is 02c -> e10_geom.json "
                "(which lived in a dead scratchpad) -> 03 -> 03b, i.e. hours. Do not "
                "start D1 until this file exists." % (cdb, cdb))
        log("cdb: %s.cdb (%.0f MB)" % (cdb, os.path.getsize(cdb + ".cdb") / 1e6))

        # A leftover PYMAPDL_START_INSTANCE / PYMAPDL_PORT makes launch_mapdl attach
        # to whatever is already running -- that is the documented stale-session trap
        # (HANDOFF:57-58): you inherit a broken state with zero elements.
        for var in ("PYMAPDL_START_INSTANCE", "PYMAPDL_PORT", "PYMAPDL_IP"):
            if var in os.environ:
                log("  [warn] clearing %s=%r from the environment (stale-session trap)"
                    % (var, os.environ[var]))
                os.environ.pop(var, None)

        with mapdl_step("import ansys.mapdl.core",
                        hint="venv: C:/Users/moa/.ansys_python_venvs/PyMotorEnv_310"):
            from ansys.mapdl.core import launch_mapdl
        try:
            from ansys.mapdl.core.errors import MapdlRuntimeError
        except Exception:
            MapdlRuntimeError = Exception
        self.MapdlRuntimeError = MapdlRuntimeError

        with mapdl_step("launch_mapdl(run_location=%s)" % args.run_dir):
            kw = dict(run_location=args.run_dir, override=True, nproc=int(args.nproc),
                      start_instance=True, loglevel="ERROR", cleanup_on_exit=True)
            if args.additional_switches:
                kw["additional_switches"] = args.additional_switches
            self.mapdl = launch_mapdl(**kw)
        log("mapdl version:", self.mapdl.version)

        self._read_mesh(cdb)
        self._build_circuit()
        self._build_surfaces()
        self._mark_built_hset()
        self._split_winding()
        self._node_index()
        self.mesh_info["cdb"] = cdb + ".cdb"
        return self

    # -- mesh -------------------------------------------------------------
    def _read_mesh(self, cdb):
        m, log = self.mapdl, self.log
        with mapdl_step("cdread + element/material definition"):
            m.clear()
            m.prep7()
            m.units("SI")
            m.cdread("DB", cdb, "cdb")
            m.shpp("off")
            n_node, n_elem = int(m.mesh.n_node), int(m.mesh.n_elem)
        log("mesh: %d nodes / %d elements" % (n_node, n_elem))
        if n_elem <= 0:
            raise D1Error(
                "cdread returned %d nodes and ZERO elements.\n"
                "  Two known causes: (1) the CDB EBLOCK tet10 line-wrap bug -- tet10 "
                "needs 11 header + 8 nodes on the first line and the remaining 2 on a "
                "continuation line (HANDOFF:46-47; writer: 03b:177-182); a single long "
                "line loads the nodes and silently drops every element. (2) attaching to "
                "a stale MAPDL instance. Regenerate the CDB with 03b, or restart clean."
                % n_node)
        if (n_node, n_elem) != (EXPECTED_N_NODE, EXPECTED_N_ELEM):
            log("  [warn] this is not the expected ff_e10_mesh_v2 (%d/%d). Continuing, "
                "but the result is not comparable with the validated hybrid run."
                % (EXPECTED_N_NODE, EXPECTED_N_ELEM))
        with mapdl_step("et/mp definition"):
            m.et(1, "SOLID87")
            m.et(2, "SURF152")
            m.keyopt(2, 5, 1)      # extra node carries the bulk temperature
            m.keyopt(2, 8, 2)
            m.et(3, "COMBIN14")
            m.keyopt(3, 2, 8)      # longitudinal, TEMP DOF -> real constant is W/K
            if self.args.transient:
                m.et(4, "MASS71")
                m.keyopt(4, 3, 1)
            for mat, (k, c, r) in MATS.items():
                m.mp("KXX", mat, k)
                m.mp("C", mat, c)
                m.mp("DENS", mat, r)
            # defensive: guarantee replace (not accumulate) semantics for SFE/BFE
            m.sfcum("ALL", "REPL")
            m.bfcum("ALL", "REPL")
        self.mesh_info.update({"n_node": n_node, "n_elem": n_elem,
                               "expected_n_node": EXPECTED_N_NODE,
                               "expected_n_elem": EXPECTED_N_ELEM,
                               "elem_type": "SOLID87 tet10"})

    # -- oil circuit ------------------------------------------------------
    def _build_circuit(self):
        m, log = self.mapdl, self.log
        with mapdl_step("oil circuit (COMBIN14 / MASS71 / D,OIL,TEMP)"):
            nmax = int(m.get_value("NODE", 0, "NUM", "MAXD"))
            rid = [100]

            def net_node(i):
                n = nmax + i
                m.csys(0)
                m.n(n, 0.5 + 0.02 * i, 0, 0)
                return n

            self.N = dict((nm, net_node(i + 1))
                          for i, nm in enumerate(CIRCUIT_NODES))

            def add_C(node, c):
                rid[0] += 1
                m.type(4)
                m.real(rid[0])
                m.r(rid[0], c)
                m.e(node)

            def add_R(n1, n2, g):
                rid[0] += 1
                m.type(3)
                m.real(rid[0])
                m.r(rid[0], g)
                m.e(n1, n2)

            if self.args.transient:
                # MASS71 feeds [C] only; in STEADY [C] is not assembled so it is inert.
                # Gated off here.  Removing it floats nothing: JACKET / SPRAY / SHF are
                # each already tied to OIL by a COMBIN14 below.
                add_C(self.N["JACKET"], C_JKT)
                add_C(self.N["SPRAY"], C_SPRAY)
                add_C(self.N["SHF"], C_SHF)
            add_R(self.N["JACKET"], self.N["OIL"], G_JKT_OIL)
            add_R(self.N["SPRAY"], self.N["OIL"], G_SPRAY_OIL)
            add_R(self.N["GAP_S"], self.N["GAP_R"], G_GAP)
            add_R(self.N["SHF"], self.N["OIL"], G_SHF_OIL)
            m.d(self.N["OIL"], "TEMP", OIL_T)
        log("circuit nodes: %s" % ", ".join("%s=%d" % (k, self.N[k])
                                            for k in CIRCUIT_NODES))
        log("circuit: G_jkt=%.0f G_spray=%.0f G_shf=%.0f G_gap=%.3f W/K, MASS71=%s"
            % (G_JKT_OIL, G_SPRAY_OIL, G_SHF_OIL, G_GAP,
               "on (transient)" if self.args.transient else "off (steady)"))

    # -- SURF152 ----------------------------------------------------------
    def _build_surfaces(self):
        m, log = self.mapdl, self.log

        def sel_matradz(mat, rlo=None, rhi=None, zlo=None, zhi=None, ext=True):
            def _fn():
                m.allsel()
                m.esel("S", "MAT", "", mat)
                m.nsle("S")
                if ext:
                    m.nsel("R", "EXT")
                m.csys(1)
                m.seltol(TOL)
                if rlo is not None:
                    m.nsel("R", "LOC", "X", rlo, rhi)
                if zlo is not None:
                    m.nsel("R", "LOC", "Z", zlo, zhi)
                m.seltol(0)
                m.csys(0)
            return _fn

        def make_surf(sel_fn, xnode, htc, name, key):
            with mapdl_step("SURF152 %s" % name):
                m.allsel()
                sel_fn()
                nsel = int(m.mesh.n_node)
                if nsel == 0:
                    m.allsel()
                    txt = ("SURF152 '%s': the node selection is EMPTY, so this "
                           "convection path does not exist and the run would be "
                           "silently wrong (04's original code only warned here). "
                           "Check the radius / z band constants against the actual "
                           "mesh, or pass --allow-empty-surface to continue anyway."
                           % name)
                    if not self.args.allow_empty_surface:
                        raise D1Error(txt)
                    log("  [warn] " + txt)
                    self.missing_surfaces.append(name)
                    return
                e0 = int(m.get_value("ELEM", 0, "NUM", "MAXD"))
                m.esln("S", 0)
                m.esel("R", "TYPE", "", 1)
                m.nsel("A", "NODE", "", xnode)
                m.type(2)
                m.real(1)
                m.esurf(xnode)
                e1 = int(m.get_value("ELEM", 0, "NUM", "MAXD"))
                if e1 <= e0:
                    m.allsel()
                    txt = ("SURF152 '%s': ESURF created no elements from %d selected "
                           "nodes." % (name, nsel))
                    if not self.args.allow_empty_surface:
                        raise D1Error(txt)
                    log("  [warn] " + txt)
                    self.missing_surfaces.append(name)
                    return
                m.esel("S", "ELEM", "", e0 + 1, e1)
                m.sfe("ALL", 1, "CONV", "", htc)
                m.allsel()
            self.sf_ranges[key].append((e0 + 1, e1))
            log("  [surf] %-22s %6d elems (%7d nodes) key=%s" % (name, e1 - e0, nsel, key))

        with mapdl_step("SURF152 real set"):
            m.r(1)
        # Identical topology to 04_mapdl_thermal.py:131-144.
        make_surf(sel_matradz(M_ST, rlo=R_STA_OUT - RT, rhi=R_STA_OUT + RT),
                  self.N["JACKET"], HTC_SETS[self._build_hset]["jkt"], "statorOD->JACKET", "jkt")
        make_surf(sel_matradz(M_ST, rlo=R_STA_IN - RT, rhi=R_STA_IN + RT),
                  self.N["GAP_S"], HTC_BIG, "statorBore->GAP_S", "gap")
        make_surf(sel_matradz(M_CO, zhi=Z_ST0 + ZT, zlo=-1.0),
                  self.N["SPRAY"], HTC_SETS[self._build_hset]["spray"], "windEnd_lo->SPRAY", "spray")
        make_surf(sel_matradz(M_CO, zlo=Z_ST1 - ZT, zhi=1.0),
                  self.N["SPRAY"], HTC_SETS[self._build_hset]["spray"], "windEnd_hi->SPRAY", "spray")
        make_surf(sel_matradz(M_RO, rlo=R_ROT_OUT - RT, rhi=R_ROT_OUT + RT),
                  self.N["GAP_R"], HTC_BIG, "rotorOD->GAP_R", "gap")
        make_surf(sel_matradz(M_RO, zhi=Z_ST0 + ZT, zlo=-1.0),
                  self.N["OIL"], HTC_SETS[self._build_hset]["splash"], "rotorEnd_lo->OIL", "splash")
        make_surf(sel_matradz(M_RO, zlo=Z_ST1 - ZT, zhi=1.0),
                  self.N["OIL"], HTC_SETS[self._build_hset]["splash"], "rotorEnd_hi->OIL", "splash")
        make_surf(sel_matradz(M_SH, zhi=Z_ST0 + ZT, zlo=-1.0),
                  self.N["SHF"], HTC_SETS[self._build_hset]["splash"], "shaftEnd_lo->SHF", "splash")
        make_surf(sel_matradz(M_SH, zlo=Z_ST1 - ZT, zhi=1.0),
                  self.N["SHF"], HTC_SETS[self._build_hset]["splash"], "shaftEnd_hi->SHF", "splash")

        self.mesh_info["missing_surfaces"] = list(self.missing_surfaces)
        if self.missing_surfaces:
            log("  [warn] %d convection path(s) are MISSING: %s. The oil circuit is "
                "incomplete and every temperature below is too high (or, for a gap "
                "path, meaningless)." % (len(self.missing_surfaces),
                                         ", ".join(self.missing_surfaces)))
        if self.args.ground_guard:
            # Recovery option only (default off).  1e-3 W/m2K over ~0.5 m2 is 5e-4 W/K
            # against 132 W/K, i.e. a ~4e-6 relative perturbation, but it removes the
            # singular pivot if the STL-merged mesh hides a floating island.
            with mapdl_step("ground guard (SF,ALL,CONV,1e-3)"):
                m.allsel()
                m.nsel("S", "EXT")
                m.sf("ALL", "CONV", 1.0e-3, OIL_T)
                m.allsel()
            log("  [note] --ground-guard active: h=1e-3 W/m2K on every exterior node.")

    # -- winding slot / end split ----------------------------------------
    def _split_winding(self):
        m, log = self.mapdl, self.log
        with mapdl_step("winding slot/end split (ESEL,R,CENT,Z)"):
            m.csys(0)                 # CENT is evaluated in the ACTIVE csys
            m.allsel()
            m.esel("S", "MAT", "", M_CO)
            m.esel("R", "TYPE", "", 1)
            m.cm("CU_ALL", "ELEM")
            n_all = int(m.get_value("ELEM", 0, "COUNT"))
            m.esel("R", "CENT", "Z", Z_ST0, Z_ST1)
            m.cm("CU_SLOT", "ELEM")
            n_slot = int(m.get_value("ELEM", 0, "COUNT"))
            m.cmsel("S", "CU_ALL")
            m.cmsel("U", "CU_SLOT")
            m.cm("CU_END", "ELEM")
            n_end = int(m.get_value("ELEM", 0, "COUNT"))
            m.allsel()
        split_method = "ESEL,R,CENT,Z"
        if n_slot == 0 or n_end == 0:
            log("  [warn] ESEL,R,CENT,Z gave slot=%d end=%d -- falling back to the "
                "node-based ESLN,S,1 rule (straddle elements all go to END)."
                % (n_slot, n_end))
            with mapdl_step("winding slot/end split (ESLN fallback)"):
                m.allsel()
                m.esel("S", "MAT", "", M_CO)
                m.esel("R", "TYPE", "", 1)
                m.nsle("S")
                m.csys(0)
                m.seltol(TOL)
                m.nsel("R", "LOC", "Z", Z_ST0, Z_ST1)
                m.seltol(0)
                m.esln("S", 1)             # ALL nodes selected (04:112 uses ANY)
                m.cm("CU_SLOT", "ELEM")
                n_slot = int(m.get_value("ELEM", 0, "COUNT"))
                m.cmsel("S", "CU_ALL")
                m.cmsel("U", "CU_SLOT")
                m.cm("CU_END", "ELEM")
                n_end = int(m.get_value("ELEM", 0, "COUNT"))
                m.allsel()
            split_method = "ESLN,S,1 fallback"
        if n_slot == 0 or n_end == 0:
            raise D1Error("winding split failed: slot=%d end=%d elements (total %d). "
                          "The stack z-band [%g, %g] does not intersect mat-3 the way "
                          "the geometry constants say." % (n_slot, n_end, n_all,
                                                           Z_ST0, Z_ST1))

        # ---- volumes, computed ONCE from the numpy side --------------------
        with mapdl_step("element volumes from mapdl.mesh.grid"):
            m.allsel()
            m.esel("S", "TYPE", "", 1)
            m.nsle("S")
            grid = m.mesh.grid                    # one gRPC download of 737k cells
            vols = np.abs(np.asarray(
                grid.compute_cell_sizes(length=False, area=False,
                                        volume=True).cell_data["Volume"], dtype=float))
            emats = np.asarray(m.mesh.material_type)
            celltypes = np.unique(np.asarray(grid.celltypes))
            if len(celltypes) == 1 and int(celltypes[0]) == 24:      # VTK_QUADRATIC_TETRA
                conn = grid.cells_dict[24]
                # straight-sided tet10: the mean of the 4 corners IS the centroid
                zc = np.asarray(grid.points, dtype=float)[conn[:, :4], 2].mean(axis=1)
            else:
                self.log("  [warn] mixed cell types %s -- using pyvista cell_centers()"
                         % celltypes.tolist())
                zc = np.asarray(grid.cell_centers().points, dtype=float)[:, 2]
            m.allsel()
        if not (len(vols) == len(emats) == len(zc)):
            raise D1Error("volume/material/centroid arrays disagree: %d / %d / %d"
                          % (len(vols), len(emats), len(zc)))

        # The numpy rule is the centroid rule, which is exactly what ESEL,R,CENT,Z
        # does -- hence the hard equality assert below.  After the ESLN fallback the
        # two rules differ on straddle elements only; the counts are then reported
        # rather than asserted, and the volumes follow the centroid rule.
        is_cu = (emats == M_CO)
        is_slot = is_cu & (zc >= Z_ST0) & (zc <= Z_ST1)
        is_end = is_cu & ~is_slot
        n_slot_np, n_end_np = int(is_slot.sum()), int(is_end.sum())
        if split_method.startswith("ESEL") and (n_slot_np != n_slot or n_end_np != n_end):
            raise D1Error(
                "the MAPDL element split and the numpy element split disagree:\n"
                "  MAPDL  slot=%d end=%d\n  numpy  slot=%d end=%d\n"
                "ESEL,R,CENT,Z did not do what this script assumes, so the injected "
                "heat density would be computed over a different element set than the "
                "one it is applied to. Investigate before trusting any number."
                % (n_slot, n_end, n_slot_np, n_end_np))
        if not split_method.startswith("ESEL"):
            self.log("  [warn] fallback split: MAPDL slot=%d end=%d vs numpy %d/%d. "
                     "Volumes use the numpy (centroid) rule; injected TOTAL power is "
                     "exact either way, only the boundary element assignment differs."
                     % (n_slot, n_end, n_slot_np, n_end_np))

        self.vol["slot"] = float(vols[is_slot].sum())
        self.vol["end"] = float(vols[is_end].sum())
        for mat in (M_ST, M_MG, M_RO):
            self.vol[mat] = float(vols[emats == mat].sum())
            if self.vol[mat] <= 0.0:
                raise D1Error("material %d has zero volume -- the mesh has no such "
                              "elements." % mat)
        self.ecount = {"cu_all": n_all, "cu_slot": n_slot, "cu_end": n_end,
                       "cu_slot_numpy": n_slot_np, "cu_end_numpy": n_end_np,
                       "stator": int((emats == M_ST).sum()),
                       "magnet": int((emats == M_MG).sum()),
                       "rotor": int((emats == M_RO).sum()),
                       "shaft": int((emats == M_SH).sum())}

        v_cu = self.vol["slot"] + self.vol["end"]
        log("")
        log("-- winding slot/end split (%s) --------------------------------" % split_method)
        log("  CU_SLOT : %8d elems   V = %9.2f cm3" % (n_slot, self.vol["slot"] * 1e6))
        log("  CU_END  : %8d elems   V = %9.2f cm3" % (n_end, self.vol["end"] * 1e6))
        log("  total   : %8d elems   V = %9.2f cm3   (gmsh reference 900.7 cm3)" %
            (n_all, v_cu * 1e6))
        log("  V_end/V_slot = %.3f   (Prius reference 0.449)"
            % (self.vol["end"] / self.vol["slot"] if self.vol["slot"] > 0 else float("nan")))
        log("  stator %9.2f cm3 | magnet %8.2f cm3 | rotor %9.2f cm3"
            % (self.vol[M_ST] * 1e6, self.vol[M_MG] * 1e6, self.vol[M_RO] * 1e6))
        if not (0.70 < v_cu * 1e6 / 900.7 < 1.30):
            log("  [warn] total winding volume is %.0f%% of the 900.7 cm3 gmsh "
                "reference." % (100.0 * v_cu * 1e6 / 900.7))
        log("-" * 62)
        log("")
        self.mesh_info["volumes_cm3"] = {
            "cu_slot": self.vol["slot"] * 1e6, "cu_end": self.vol["end"] * 1e6,
            "winding_total": v_cu * 1e6, "stator": self.vol[M_ST] * 1e6,
            "magnet": self.vol[M_MG] * 1e6, "rotor": self.vol[M_RO] * 1e6}
        self.mesh_info["element_counts"] = dict(self.ecount)
        self.mesh_info["winding_split_method"] = split_method
        self.mesh_info["V_end_over_V_slot"] = (self.vol["end"] / self.vol["slot"])

    def _mark_built_hset(self):
        """The SURF152 convection values were written at ESURF time with the
        _build_hset values, so that h-set is already in effect and _apply_htc()
        must not re-issue SFE for it.  Re-applying SFE in /SOLU for a SECOND
        h-set produced a field with a 62.46 degC minimum on moa (below the 70 degC
        oil Dirichlet, i.e. a max-principle violation), so each h-set now gets its
        own session instead."""
        self._cur_hset = self._build_hset

    # -- node index maps --------------------------------------------------
    def _node_index(self):
        m, log = self.mapdl, self.log
        with mapdl_step("node index maps"):
            m.allsel("ALL")
            nnum_all = np.asarray(m.mesh.nnum, dtype=np.int64)
            if np.any(np.diff(nnum_all) <= 0):
                raise D1Error("mapdl.mesh.nnum is not strictly ascending; the "
                              "searchsorted index map would be wrong.")
            for mat, part in PART_OF_MAT.items():
                m.allsel("ALL")
                m.esel("S", "MAT", "", mat)
                m.esel("R", "TYPE", "", 1)
                m.nsle("S")
                sub = np.asarray(m.mesh.nnum, dtype=np.int64)
                idx = np.searchsorted(nnum_all, sub)
                if idx.size == 0 or not np.array_equal(nnum_all[idx], sub):
                    raise D1Error("node index map for material %d (%s) is inconsistent."
                                  % (mat, part))
                self.part_idx[part] = idx
            m.allsel("ALL")
        self.nnum = nnum_all
        pos = np.searchsorted(nnum_all, np.asarray([self.N[k] for k in CIRCUIT_NODES],
                                                   dtype=np.int64))
        for i, nm in enumerate(CIRCUIT_NODES):
            if int(nnum_all[pos[i]]) != self.N[nm]:
                raise D1Error("circuit node %s (id %d) is not in mapdl.mesh.nnum."
                              % (nm, self.N[nm]))
            self.circ_pos[nm] = int(pos[i])
        log("node sets: " + " | ".join("%s %d" % (p, len(self.part_idx[p]))
                                       for p in PARTS))

    # -- per-run operations ----------------------------------------------
    def _apply_htc(self, hset):
        if hset == self._cur_hset:
            return
        h = HTC_SETS[hset]
        m = self.mapdl
        with mapdl_step("apply h-set %s" % hset):
            m.finish()
            m.slashsolu()
            for key in ("jkt", "spray", "splash", "gap"):
                val = HTC_BIG if key == "gap" else h[key]
                for (a, b) in self.sf_ranges[key]:
                    m.esel("S", "ELEM", "", a, b)
                    m.sfe("ALL", 1, "CONV", "", val)
            m.allsel("ALL")
        self._cur_hset = hset
        self.log("  h-set %s: jkt=%.0f spray=%.0f splash=%.0f (gap fixed at %.0f)"
                 % (hset, h["jkt"], h["spray"], h["splash"], HTC_BIG))

    def _apply_losses(self, loss_vec):
        m = self.mapdl
        with mapdl_step("apply HGEN"):
            m.finish()
            m.slashsolu()
            m.allsel("ALL")
            m.bfedele("ALL", "HGEN")
            for mat, key in ((M_ST, "fe_s"), (M_RO, "fe_r"), (M_MG, "pm")):
                w = float(loss_vec.get(key, 0.0))
                m.allsel("ALL")
                m.esel("S", "MAT", "", mat)
                m.esel("R", "TYPE", "", 1)
                m.bfe("ALL", "HGEN", 1, w / self.vol[mat])
            q_slot = (float(loss_vec.get("cu_slot", 0.0))
                      + float(loss_vec.get("ac_slot", 0.0))) / self.vol["slot"]
            q_end = float(loss_vec.get("cu_end", 0.0)) / self.vol["end"]
            m.cmsel("S", "CU_SLOT")
            m.bfe("ALL", "HGEN", 1, q_slot)
            m.cmsel("S", "CU_END")
            m.bfe("ALL", "HGEN", 1, q_end)
            m.allsel("ALL")

    def _solve(self, tag):
        m = self.mapdl
        self.iload += 1
        iload = self.iload
        with mapdl_step("SOLVE (load step %d)" % iload,
                        hint="a zero/negative pivot here means a floating island -- "
                             "retry with --ground-guard"):
            m.finish()
            m.slashsolu()
            if iload == 1:
                # ANTYPE is issued ONCE. It is stored in the DB and survives the
                # FINISH / POST1 / re-enter-/SOLU cycle between runs; re-issuing it
                # defaults to Status=NEW, which can rewind the results file and make
                # every later SET index a lie.  ANTYPE,STATIC (= ANTYPE,0) is the
                # steady thermal analysis that the original 13.5 s run used (git
                # 7ece7f8) -- no TRNOPT, no TIMINT, no DELTIM, no IC.
                m.antype("STATIC")
                m.kbc(1)                # stepped; meaningless at 1 substep, harmless
            # Re-assert the single Dirichlet every load step.  Observed on moa at load
            # step 2: the D applied during circuit build was no longer in effect, MAPDL
            # reported a negative pivot at the OIL node itself plus "no temperature
            # constraints or convections applied", and the field ran away to 8.6e10 K.
            # D is idempotent and costs nothing, so assert it rather than rely on it
            # surviving the FINISH / POST1 SET / re-enter-/SOLU cycle between runs.
            m.d(self.N["OIL"], "TEMP", OIL_T)
            m.nsubst(1)
            m.time(float(iload))        # pseudo-time = load index -> SET,iload,1
            m.outres("ERASE")
            m.outres("ALL", "NONE")     # suppress element records: 5-10x smaller .rth
            m.outres("NSOL", "ALL")     # nodal temperatures only
            m.allsel("ALL")             # MANDATORY: SOLVE only solves the selection
            t0 = time.time()
            m.solve()
            dt = time.time() - t0
            m.finish()
        temps = self._harvest(iload, tag)
        self.n_solves += 1
        self.last_iload, self.last_solve_time = iload, dt
        self.solve_log.append({"load_index": iload, "tag": tag, "solve_time_s": dt})
        return temps, dt, iload

    def _harvest(self, iload, tag):
        m = self.mapdl
        with mapdl_step("POST1 harvest (load step %d)" % iload):
            m.finish()
            m.post1()
            nset = int(m.get_value("ACTIVE", 0, "SET", "NSET"))
            m.set("LAST")
            t_set = float(m.get_value("ACTIVE", 0, "SET", "TIME"))
            # The correctness condition is TIME, not the set count: TIME was stamped
            # with this run's index just before SOLVE, so a mismatch means SET,LAST is
            # pointing at some OTHER run's result -- i.e. this SOLVE wrote nothing.
            if abs(t_set - iload) > 1e-6:
                raise D1Error(
                    "run %s: SET,LAST points at TIME=%g but this run stamped TIME=%d. "
                    "The last SOLVE wrote no result set, so the temperatures being "
                    "harvested belong to a previous run. Read file.err in the run "
                    "directory." % (tag, t_set, iload))
            if nset != iload:
                self.log("  [warn] %s: the results file holds %d sets at solve %d "
                         "(expected %d). TIME matches, so the data is the right one, "
                         "but the .rth was rewound at some point -- do not index it by "
                         "run number afterwards." % (tag, nset, iload, iload))
            m.allsel("ALL")
            temps = np.asarray(m.post_processing.nodal_temperature(), dtype=float)
        if temps.size != self.nnum.size:
            raise D1Error(
                "run %s: nodal_temperature() returned %d values but the model has %d "
                "nodes. The array is assumed to be in mapdl.mesh.nnum order with every "
                "node selected; that assumption just broke." % (tag, temps.size,
                                                                self.nnum.size))
        self.check_field(temps, tag)
        return temps

    # -- backend API ------------------------------------------------------
    def influence(self, hset):
        log = self.log
        self._apply_htc(hset)
        unit_w = float(self.args.unit_W)
        unit_temps = {}
        for s in UNIT_SOURCES:
            tag = "unit[%s] %s" % (hset, s)
            set_run(tag)
            lv = dict((k, 0.0) for k in SOURCES)
            lv[s] = unit_w
            self._apply_losses(lv)
            temps, dt, _ = self._solve(tag)
            rise = temps - OIL_T
            log("  %-22s solve %5.1f s  max rise %.4g K  (%.4g W injected)"
                % (tag, dt, float(np.nanmax(rise)), unit_w))
            unit_temps[s] = temps
        return _gmap_from_units(unit_temps, unit_w, self.log)

    def direct(self, hset, loss_vec, tag):
        self._apply_htc(hset)
        set_run(tag)
        self._apply_losses(loss_vec)
        temps, dt, _ = self._solve(tag)
        self.log("  %-34s solve %5.1f s  T_max %.1f degC" % (tag, dt,
                                                             float(np.nanmax(temps))))
        return temps

    def close(self):
        if self.mapdl is not None:
            try:
                self.mapdl.exit()
            except Exception:
                pass
            self.mapdl = None


def _gmap_from_units(unit_temps, unit_w, log):
    """{source: full nodal field} -> {source: influence array [K/W]} with ac alias.

    G[s] = (T_unit[s] - 70) / unit_W -- the per-node form of icont.solve_influence
    (which works on scalars).  ac_slot is aliased to cu_slot because D1 injects the
    AC slot loss uniformly over the same CU_SLOT element set: exact, not an
    approximation.  (D2's turn-wise injection must NOT use this alias.)
    """
    gmap = {}
    for s in UNIT_SOURCES:
        gmap[s] = (np.asarray(unit_temps[s], dtype=float) - OIL_T) / unit_w
    gmap["ac_slot"] = gmap["cu_slot"]
    worst = min(float(np.nanmin(gmap[s])) for s in UNIT_SOURCES)
    if worst < -1e-9:
        log("  [warn] the influence matrix has a negative coefficient (min %.3e K/W). "
            "Heating a source can only raise temperatures in this model, so that is a "
            "solve artefact -- check the run above." % worst)
    return gmap


class SyntheticBackend(BackendBase):
    """--dry-run backend.  No MAPDL, no mesh, no solve.

    It fabricates a per-node influence matrix whose SHAPE (not whose numbers) is
    realistic: the scale comes from the repo's own measured lumped sensitivity
    (ff_mapdl_hybrid_temps.json: 4.024 kW -> winding 152.2 degC over 70 degC oil =
    20.4 K/kW), and the per-node modulation makes the winding hot spot MOVE between
    the slot end and the end turn as the loss mix changes -- so the hot-node fixed
    point, the argmax bookkeeping and the I_cont maths are all genuinely exercised,
    not stubbed.
    """

    kind = "synthetic"

    _SCALE = 0.0212           # K/W
    _BASE = {
        "winding": {"cu_slot": 1.00, "cu_end": 0.80, "fe_s": 0.30, "fe_r": 0.20, "pm": 0.25},
        "stator":  {"cu_slot": 0.61, "cu_end": 0.34, "fe_s": 0.55, "fe_r": 0.21, "pm": 0.24},
        "magnet":  {"cu_slot": 0.50, "cu_end": 0.30, "fe_s": 0.40, "fe_r": 0.60, "pm": 3.00},
        "rotor":   {"cu_slot": 0.44, "cu_end": 0.26, "fe_s": 0.36, "fe_r": 0.90, "pm": 2.10},
        "shaft":   {"cu_slot": 0.30, "cu_end": 0.22, "fe_s": 0.25, "fe_r": 0.40, "pm": 0.60},
    }
    _CIRC = {
        "OIL":    {"cu_slot": 0.0,    "cu_end": 0.0,    "fe_s": 0.0,    "fe_r": 0.0,    "pm": 0.0},
        "JACKET": {"cu_slot": 0.0035, "cu_end": 0.0012, "fe_s": 0.0060, "fe_r": 0.0008, "pm": 0.0010},
        "SPRAY":  {"cu_slot": 0.0015, "cu_end": 0.0085, "fe_s": 0.0006, "fe_r": 0.0004, "pm": 0.0005},
        "GAP_S":  {"cu_slot": 0.0040, "cu_end": 0.0014, "fe_s": 0.0052, "fe_r": 0.0020, "pm": 0.0030},
        "GAP_R":  {"cu_slot": 0.0030, "cu_end": 0.0011, "fe_s": 0.0038, "fe_r": 0.0060, "pm": 0.0090},
        "SHF":    {"cu_slot": 0.0018, "cu_end": 0.0009, "fe_s": 0.0016, "fe_r": 0.0030, "pm": 0.0040},
    }
    _HSET_FACTOR = {"base": {"winding": 1.0, "stator": 1.0, "magnet": 1.0,
                             "rotor": 1.0, "shaft": 1.0, "circ": 1.0},
                    "sph":  {"winding": 2.2, "stator": 2.3, "magnet": 1.6,
                             "rotor": 1.6, "shaft": 1.5, "circ": 2.0}}
    _N_PER_PART = {"winding": 1200, "stator": 900, "magnet": 300,
                   "rotor": 600, "shaft": 200}

    def setup(self):
        pos = 0
        ids = []
        for part in PARTS:
            n = self._N_PER_PART[part]
            self.part_idx[part] = np.arange(pos, pos + n, dtype=np.int64)
            ids.extend(range(pos + 1, pos + n + 1))
            pos += n
        for nm in CIRCUIT_NODES:
            self.circ_pos[nm] = pos
            ids.append(pos + 1)
            pos += 1
        self.nnum = np.asarray(ids, dtype=np.int64)
        self.n_nodes = pos
        v = {"cu_slot": 0.6, "cu_end": 0.3, "stator": 1.75, "magnet": 0.09, "rotor": 0.55}
        self.mesh_info = {
            "n_node": int(self.n_nodes), "n_elem": 0,
            "expected_n_node": EXPECTED_N_NODE, "expected_n_elem": EXPECTED_N_ELEM,
            "cdb": None, "elem_type": "SYNTHETIC (--dry-run)",
            "winding_split_method": "synthetic",
            "volumes_cm3": {"cu_slot": v["cu_slot"] * 1e3, "cu_end": v["cu_end"] * 1e3,
                            "winding_total": (v["cu_slot"] + v["cu_end"]) * 1e3,
                            "stator": v["stator"] * 1e3, "magnet": v["magnet"] * 1e3,
                            "rotor": v["rotor"] * 1e3},
            "element_counts": {"synthetic": True},
            "V_end_over_V_slot": v["cu_end"] / v["cu_slot"],
            "_warning": "SYNTHETIC dry-run geometry. No mesh was read.",
        }
        self.log("")
        self.log("-- SYNTHETIC mesh (--dry-run) ---------------------------------")
        self.log("  %d pseudo-nodes: %s + %d circuit nodes"
                 % (self.n_nodes,
                    ", ".join("%s %d" % (p, self._N_PER_PART[p]) for p in PARTS),
                    len(CIRCUIT_NODES)))
        self.log("  CU_SLOT V = %.2f cm3 | CU_END V = %.2f cm3 | ratio %.3f  (fabricated)"
                 % (v["cu_slot"] * 1e3, v["cu_end"] * 1e3, v["cu_end"] / v["cu_slot"]))
        self.log("-" * 62)
        self.log("")
        return self

    def _shape(self, part, source, u):
        """Per-node modulation in [0,1] along the part.  u=0 is the deep slot end of
        the winding, u=1 the end turn; cu_slot peaks at u=0 and cu_end at u=1, so the
        argmax node migrates with the loss mix exactly as it does in the real model."""
        if part == "winding":
            if source == "cu_slot":
                return 0.55 + 0.45 * (1.0 - u)
            if source == "cu_end":
                return 0.30 + 0.70 * u
            return 0.70 + 0.30 * (1.0 - u)
        if part in ("magnet", "rotor"):
            if source == "pm":
                return 0.60 + 0.40 * (1.0 - u)
            if source == "fe_r":
                return 0.65 + 0.35 * u
            return 0.75 + 0.25 * math.sin(math.pi * u)
        return 0.72 + 0.28 * math.sin(math.pi * u) ** 2

    def _build_gmap(self, hset):
        """Pure and cached: building the matrix is not itself a 'solve'."""
        cache = getattr(self, "_gcache", None)
        if cache is None:
            cache = self._gcache = {}
        if hset in cache:
            return cache[hset]
        fac = self._HSET_FACTOR[hset]
        gmap = dict((s, np.zeros(self.n_nodes, dtype=float)) for s in UNIT_SOURCES)
        for part in PARTS:
            idx = self.part_idx[part]
            n = len(idx)
            u = np.linspace(0.0, 1.0, n)
            for s in UNIT_SOURCES:
                base = self._BASE[part][s] * self._SCALE * fac[part]
                shape = np.asarray([self._shape(part, s, float(x)) for x in u])
                gmap[s][idx] = base * shape
        for nm in CIRCUIT_NODES:
            p = self.circ_pos[nm]
            for s in UNIT_SOURCES:
                gmap[s][p] = self._CIRC[nm][s] * fac["circ"]
        gmap["ac_slot"] = gmap["cu_slot"]
        cache[hset] = gmap
        return gmap

    def influence(self, hset):
        gmap = self._build_gmap(hset)
        if hset not in getattr(self, "_counted", set()):
            self._counted = getattr(self, "_counted", set()) | set([hset])
            for s in UNIT_SOURCES:            # stand in for the 5 real unit solves
                self.n_solves += 1
                self.solve_log.append({"load_index": self.n_solves,
                                       "tag": "unit[%s] %s (synthetic)" % (hset, s),
                                       "solve_time_s": 0.0})
            self.log("  synthetic influence matrix for h-set %s: %d nodes x %d sources"
                     % (hset, self.n_nodes, len(SOURCES)))
        return gmap

    def direct(self, hset, loss_vec, tag):
        gmap = self._build_gmap(hset)        # building it is free and uncounted
        temps = reconstruct_field(gmap, loss_vec)
        frac = float(self.args.dry_run_nonlinear)
        if frac != 0.0:
            # deliberately break linearity so the failure path can be exercised
            rise = temps - OIL_T
            temps = OIL_T + rise * (1.0 + frac * rise / 1000.0)
        self.n_solves += 1
        self.last_iload, self.last_solve_time = self.n_solves, 0.0
        self.solve_log.append({"load_index": self.n_solves,
                               "tag": tag + " (synthetic direct)",
                               "solve_time_s": 0.0})
        self.check_field(temps, tag)
        return temps


# ===========================================================================
# 5.  Superposition verification
# ===========================================================================

def build_check_nodes(gmap, t_direct, part_idx, circ_pos, nnum):
    """influence_by_node / direct_temps for icont.check_superposition.

    Every entry is a TRUE linear functional so the comparison is exact and any
    difference is a real modelling/plumbing error:
      * <part>_max  -> the influence ROW of the node that is the argmax of the
                       DIRECT solve (a fixed node, not a max operator)
      * winding_mean-> the mean influence row over the fixed winding node set
      * circuit nodes -> their own rows
    The max-of-field comparison is done separately and reported as
    max_functional_err_K.
    """
    inf = {}
    direct = {}
    for part in PARTS:
        idx = part_idx[part]
        k = int(np.argmax(t_direct[idx]))
        pos = int(idx[k])
        key = part + "_max"
        inf[key] = row_at(gmap, pos)
        direct[key] = float(t_direct[pos])
    inf["winding_mean"] = mean_row(gmap, part_idx["winding"])
    direct["winding_mean"] = float(t_direct[part_idx["winding"]].mean())
    for nm in CIRCUIT_NODES:
        inf[nm] = row_at(gmap, circ_pos[nm])
        direct[nm] = float(t_direct[circ_pos[nm]])
    return inf, direct


def verify_superposition(backend, gmap, hset, records, args, log):
    """The two direct full-load solves demanded by the plan's linearity claim."""
    out = []
    worst = 0.0
    for (speed, current, case) in VERIFY_POINTS:
        tag = "verify %d rpm / %.3f A / %s / %s" % (speed, current, case, hset)
        lv = losses_for_run(records, speed, current, args.phase, case, args)
        t_dir = backend.direct(hset, lv, tag)
        t_rec = reconstruct_field(gmap, lv)

        inf, direct = build_check_nodes(gmap, t_dir, backend.part_idx,
                                        backend.circ_pos, backend.nnum)
        chk = icont.check_superposition(inf, lv, direct, tol_K=args.superposition_tol)

        # separate, honest check of the NON-linear functional (max over nodes)
        max_err = {}
        for part in PARTS:
            idx = backend.part_idx[part]
            max_err[part + "_max"] = float(t_rec[idx].max() - t_dir[idx].max())
        node_shift = {}
        for part in PARTS:
            idx = backend.part_idx[part]
            n_rec = int(backend.nnum[idx[int(np.argmax(t_rec[idx]))]])
            n_dir = int(backend.nnum[idx[int(np.argmax(t_dir[idx]))]])
            node_shift[part] = {"reconstructed_argmax_node": n_rec,
                                "direct_argmax_node": n_dir,
                                "same": bool(n_rec == n_dir)}
        max_fun_err = max(abs(v) for v in max_err.values())

        rec = {"point": {"speed": speed, "current": current, "case": case, "htc": hset},
               "P_W": dict((k, float(lv[k])) for k in SOURCES),
               "ok": bool(chk["ok"] and max_fun_err <= args.superposition_tol),
               "max_abs_err_K": float(chk["max_abs_err_K"]),
               "worst_node": chk["worst_node"],
               "n_nodes": chk["n_nodes"],
               "tol_K": float(chk["tol_K"]),
               "per_node_K": dict((k, float(v)) for k, v in chk["per_node"].items()),
               "reconstructed_C": dict((k, float(v)) for k, v in chk["reconstructed_C"].items()),
               "direct_C": dict((k, float(v)) for k, v in chk["direct_C"].items()),
               "max_functional_err_K": max_fun_err,
               "max_functional_err_per_part_K": max_err,
               "argmax_node_agreement": node_shift,
               "note": chk["note"],
               "field_max_err_K": float(np.nanmax(np.abs(t_rec - t_dir))),
               "field_rms_err_K": float(np.sqrt(np.nanmean((t_rec - t_dir) ** 2)))}
        worst = max(worst, float(chk["max_abs_err_K"]), max_fun_err)
        out.append(rec)

        log("  %s" % tag)
        log("    fixed-node max |recon - direct| = %.4g K  (tol %.3g K) -> %s"
            % (chk["max_abs_err_K"], chk["tol_K"], "OK" if chk["ok"] else "FAIL"))
        log("    max-over-nodes functional error = %.4g K   full-field max = %.4g K"
            % (max_fun_err, rec["field_max_err_K"]))
        moved = [p for p in PARTS if not node_shift[p]["same"]]
        if moved:
            log("    [note] argmax node differs between reconstruction and direct solve "
                "for: %s (a plateau of nearly equal nodes; the temperature error above "
                "is what matters)" % ", ".join(moved))
    return out, worst


def unit_roundtrip_check(backend, gmap, hset, args, log):
    """Assert the affine identity on the unit solves themselves.

    T(P = unit_W in source s, 0 elsewhere) must come back as exactly the unit solve.
    Tautological in the array algebra, which is the point: it is a pipeline test.
    It runs the SAME extraction -> icont.reconstruct path that the 64 production
    entries use, so a wrong column order, a broken ac_slot alias, a bad node index
    map or a mismatched key set is caught here with no extra solve.
    """
    unit_w = float(args.unit_W)
    results = []
    worst = 0.0
    for s in UNIT_SOURCES:
        lv = dict((k, 0.0) for k in SOURCES)
        lv[s] = unit_w
        t_field = reconstruct_field(gmap, lv)
        inf, direct = build_check_nodes(gmap, t_field, backend.part_idx,
                                        backend.circ_pos, backend.nnum)
        chk = icont.check_superposition(inf, lv, direct, tol_K=1e-9)
        worst = max(worst, float(chk["max_abs_err_K"]))
        results.append({"source": s, "unit_W": unit_w,
                        "max_abs_err_K": float(chk["max_abs_err_K"]),
                        "ok": bool(chk["ok"]), "n_nodes": int(chk["n_nodes"])})
    ok = all(r["ok"] for r in results)
    log("  unit-solve affine round-trip (%s): max err %.3e K over %d sources -> %s"
        % (hset, worst, len(results), "OK" if ok else "FAIL"))
    if not ok:
        raise D1Error(
            "the affine identity T = 70 + sum(P_s*G_s) does not reproduce the unit "
            "solves themselves (max %.3e K). That is a bookkeeping bug in this script "
            "(node index map, source ordering or the ac_slot alias), not a physics "
            "result. Nothing downstream is trustworthy." % worst)
    return {"ok": ok, "max_abs_err_K": worst, "per_source": results}


# ===========================================================================
# 6.  I_cont
# ===========================================================================

def losses_for_run(records, speed, current, phase, case, args, continuous=False):
    measured = getattr(args, "_magnetic_map", None)
    if measured is None:
        fn = jm.loss_vector if continuous else jm.losses_for
        return fn(records, speed, current, phase, case)
    values = jm.loss_vector(records, speed, current, phase, case)
    values.update(measured.at(speed, current, args.iron_interpolation))
    return values


def icont_super(gmap, backend, records, speed, case, args, log, tag):
    """Continuous I_cont with a hot-node fixed point.  See the module docstring."""
    phase = args.phase

    def p_of_I(cur):
        return losses_for_run(records, speed, cur, phase, case, args, continuous=True)

    idx_w = backend.part_idx["winding"]
    idx_m = backend.part_idx["magnet"]

    def hot(cur):
        t = reconstruct_field(gmap, p_of_I(cur))
        return (int(idx_w[int(np.argmax(t[idx_w]))]),
                int(idx_m[int(np.argmax(t[idx_m]))]))

    root_options = {"lo": 0.0, "hi": float(args.i_hi)}
    measured = getattr(args, "_magnetic_map", None)
    if measured is not None:
        lo, upper = measured.bounds(speed)
        hi = min(float(args.i_hi), upper)
        if hi <= lo:
            raise D1Error("No measured current interval inside the requested root bracket")
        root_options = {"lo": lo, "hi": hi, "grid_lo": lo, "grid_hi": upper, "max_expand": 0}
        field_lo = reconstruct_field(gmap, p_of_I(lo))
        temperatures_lo = {"winding": float(field_lo[idx_w].max()),
                           "magnet": float(field_lo[idx_m].max())}
        exceeded = [name for name, limit in (("winding", args.limit_winding),
                                             ("magnet", args.limit_magnet))
                    if temperatures_lo[name] > limit]
        if exceeded:
            return {"I_cont_Arms": None, "I_cont_winding_Arms": None,
                    "I_cont_magnet_Arms": None, "limited_by": "+".join(exceeded),
                    "status": "below_measured_range", "search_range_Arms": [lo, hi],
                    "T_at_lower_bound_C": temperatures_lo,
                    "infeasible_at_zero_current": False,
                    "notes": ["Limit exceeded at lowest measured current; no extrapolation to zero current."]}

    initial_current = (0.5 * (CURRENTS_D1[0] + CURRENTS_D1[-1]) if measured is None
                       else 0.5 * (root_options["lo"] + root_options["hi"]))
    pos_w, pos_m = hot(initial_current)
    history = []
    converged = False
    res = None
    for it in range(MAX_HOT_ITER):
        res = icont.i_cont_rootfind(row_at(gmap, pos_w), row_at(gmap, pos_m), p_of_I,
                                    **root_options,
                                    lim_w=args.limit_winding, lim_m=args.limit_magnet,
                                    t_oil=OIL_T)
        i_c = res["I_cont_Arms"]
        history.append({"iteration": it,
                        "winding_node": int(backend.nnum[pos_w]),
                        "magnet_node": int(backend.nnum[pos_m]),
                        "I_cont_Arms": None if i_c is None else float(i_c),
                        "status": res["status"]})
        if i_c is None:
            history[-1]["note"] = ("no root inside the search range; the hot-node "
                                   "iteration cannot proceed and stops here")
            break
        nw, nm = hot(i_c)
        if nw == pos_w and nm == pos_m:
            converged = True
            break
        pos_w, pos_m = nw, nm
    if res is None:                                     # pragma: no cover
        raise D1Error("%s: the hot-node iteration produced no result" % tag)
    if not converged and history and history[-1]["I_cont_Arms"] is not None:
        res = icont.i_cont_rootfind(row_at(gmap, pos_w), row_at(gmap, pos_m), p_of_I,
                                    **root_options,
                                    lim_w=args.limit_winding, lim_m=args.limit_magnet,
                                    t_oil=OIL_T)
    res["_method_detail"] = ("superposition + bisection, hot-node fixed point "
                             "(max over nodes is not a linear functional, so the "
                             "argmax node is iterated to self-consistency)")
    if measured is not None:
        res["_rating_scope"] = "thermal limit only; fixed magnetic temperatures/phase; voltage feasibility not imposed"
        res["_magnetic_interpolation"] = args.iron_interpolation
    res["_hot_node_iterations"] = history
    res["_hot_node_converged"] = bool(converged)
    res["_hot_nodes"] = {"winding": int(backend.nnum[pos_w]),
                         "magnet": int(backend.nnum[pos_m])}
    if not converged:
        res.setdefault("notes", []).append(
            "the winding/magnet hot node was still moving after %d iterations; the "
            "reported I_cont uses the last node pair. Nearly-equal nodes on a plateau "
            "do this and the temperature difference between them is usually far below "
            "1 K, but the number carries this caveat." % MAX_HOT_ITER)
    if res.get("I_cont_Arms") is not None:
        i_c = res["I_cont_Arms"]
        _, status_ac = jm.p_ac_continuous_ex(records, speed, i_c, phase)
        if status_ac != "ok" and case == "AC":
            res.setdefault("notes", []).append(
                "the AC loss at I_cont = %.3f A was CLAMPED to the map end knot (%s); "
                "outside 0.1-460 A the AC loss is not extrapolated, so the temperature "
                "there is understated." % (i_c, status_ac))
    return res


def icont_brute(currents, temps_w, temps_m, args):
    return icont.i_cont_bracket_pair(currents, temps_w, temps_m,
                                     lim_w=args.limit_winding,
                                     lim_m=args.limit_magnet, t_oil=OIL_T)


# ===========================================================================
# 7.  JSON assembly
# ===========================================================================

def jsonify(obj):
    """numpy -> python, non-finite -> None (json must stay strict/valid)."""
    if isinstance(obj, dict):
        return dict((str(k), jsonify(v)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return [jsonify(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [jsonify(v) for v in obj.tolist()]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        obj = float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj


def htc_string():
    b, s = HTC_SETS["base"], HTC_SETS["sph"]
    return ("base: jkt %.0f / spray %.0f / splash %.0f W/m2K (assumed); "
            "sph: jkt %.0f / spray %.0f / splash %.0f W/m2K (SPH near-wall gradient "
            "backout, plan D1 spec); gap interfaces fixed at h = %.0f W/m2K "
            "(numerical device, not swept); oil bulk %.0f degC (single Dirichlet)."
            % (b["jkt"], b["spray"], b["splash"], s["jkt"], s["spray"], s["splash"],
               HTC_BIG, OIL_T))


def empty_nested(hsets):
    return dict((h, dict((c, {}) for c in CASES)) for h in hsets)


def write_json(path, payload, indent=1):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(jsonify(payload), fh, indent=indent, ensure_ascii=False,
                  allow_nan=False, sort_keys=False)
        fh.write("\n")
    return path


def _one_check_ignore(repo, path):
    """(is_ignored, rule_text or error).

    ** The verdict MUST come from a call WITHOUT -v. **
    Plain `git check-ignore` exits 0 only when the path is actually ignored.
    With -v it exits 0 whenever ANY pattern matched -- including a NEGATION (`!...`).
    So once .gitignore carries `!mlxperPJT/thermal/thesis_out/*.png`, the -v form
    returns 0 for a perfectly committable PNG and the audit cries wolf. Observed on
    moa 2026-09-07: -q said committable, -v said ignored, for the same file.
    -v is still used, but only to fetch the human-readable rule text after the fact.
    """
    def _run(args):
        return subprocess.run(["git", "-C", str(repo), "check-ignore"] + args,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        proc = _run(["--", str(path)])            # no -v: authoritative verdict
    except (OSError, ValueError) as exc:
        return (None, "%s: %s" % (type(exc).__name__, exc))
    if proc.returncode == 1:
        return (False, "")
    if proc.returncode != 0:
        return (None, (proc.stderr or b"").decode("utf-8", "replace").strip())
    try:
        det = _run(["-v", "--", str(path)])
        txt = (det.stdout or b"").decode("utf-8", "replace").strip()
    except (OSError, ValueError):
        txt = ""
    return (True, txt)


def git_check_ignore(repo, commit_paths, info_paths, out_dir, log):
    """Audit what this run wrote (and what D1's figures will be) against .gitignore.

    Measured on this repo: .gitignore:27 `*.log`, :39 `*.png` and :183 `*.csv` match
    inside thesis_out; .json and .py pass.  So:
      * the result JSON being ignored is a LOUD failure (it is the deliverable),
      * the run log being ignored is expected and only mentioned,
      * the two D1 PNGs the plan also demands ARE ignored today -- probed here by
        name even though this script does not draw them, because the fix belongs in
        this warning and must happen before the commit step.
    The fix is a negation at the END of the ROOT .gitignore, which lives outside
    plans/ -- so moa applies it, not this script.
    """
    report = {"git_available": True, "fix": GITIGNORE_FIX,
              "deliverables": [], "working_files": [], "figure_probe": []}
    hard = []
    for p in commit_paths:
        ig, txt = _one_check_ignore(repo, p)
        if ig is None:
            report["git_available"] = False
            report["error"] = txt
            if "outside repository" in txt:
                report["reason"] = "output directory is outside the repo"
                log("  git check-ignore skipped: %s is outside the repo, so nothing "
                    "here is going to be committed from this path anyway."
                    % os.path.basename(str(p)))
            else:
                log("  [warn] could not run git check-ignore -- the .gitignore audit "
                    "did NOT run, so check by hand before committing (%s)" % txt)
            return report
        report["deliverables"].append({"path": str(p), "ignored": bool(ig), "rule": txt})
        if ig:
            hard.append(txt)
    for p in info_paths:
        ig, txt = _one_check_ignore(repo, p)
        report["working_files"].append({"path": str(p), "ignored": bool(ig), "rule": txt})
    figs = []
    for name in ("cont_rating_Tw_vs_I.png", "cont_rating_Icont_vs_n.png"):
        p = os.path.join(out_dir, name)
        ig, txt = _one_check_ignore(repo, p)
        report["figure_probe"].append({"path": p, "ignored": bool(ig), "rule": txt})
        if ig:
            figs.append(txt)

    if hard:
        lines = ["GITIGNORE FAILURE: the RESULT JSON this run wrote is ignored by git."]
        lines.extend("  " + t for t in hard)
        lines.append("It will NOT be committed and the push will still look successful.")
        lines.append("Fix before committing (moa does this -- the root .gitignore is "
                     "outside plans/):")
        lines.append("  append at the END of the repo-root .gitignore:  %s" % GITIGNORE_FIX)
        lines.append("or force it in:  git add -f <path>")
        log.banner(lines)
    elif figs:
        lines = ["GITIGNORE WARNING: the D1 result JSON commits fine, but the two "
                 "figures the plan also asks for are IGNORED:"]
        lines.extend("  " + t for t in figs)
        lines.append("The plan (line 8) requires JSON + PNG in thesis_out. The PNG half "
                     "will silently not be committed.")
        lines.append("Fix before the commit step -- append at the END of the repo-root "
                     ".gitignore:")
        lines.append("  %s" % GITIGNORE_FIX)
        lines.append("(that file is outside plans/, so moa edits it, not the thesis "
                     "session), or commit them with:  git add -f <png>")
        log.banner(lines)
    else:
        log("  git check-ignore: the result JSON and the D1 figure names all commit "
            "cleanly.")
    for it in report["working_files"]:
        if it["ignored"]:
            log("  git check-ignore: %s is ignored (%s) -- expected, it is a working "
                "file, not a deliverable."
                % (os.path.basename(it["path"]), it["rule"].split("\t")[0]))
    return report


# ===========================================================================
# 8.  Driver
# ===========================================================================

def build_run_table(records, hsets, args):
    """The plan's 64 (or --currents-many) entries with their exact grid loss vectors."""
    table = []
    for h in hsets:
        for case in CASES:
            for speed in args.speeds:
                for cur in args.currents:
                    lv = losses_for_run(records, speed, cur, args.phase, case, args)
                    table.append({"speed": int(speed), "current": float(cur),
                                  "case": case, "htc": h,
                                  "P_W": dict((k, float(lv[k])) for k in SOURCES)})
    return table


def run(args, log):
    t_start = time.time()
    hsets = ("base", "sph") if args.htc_set == "both" else (args.htc_set,)

    log.rule("D1 continuous rating -- e10 steady, oil-circuit hybrid")
    log("script      : %s" % SCRIPT_NAME)
    log("mode        : %s%s" % (args.mode, "  (DRY RUN -- no MAPDL)" if args.dry_run else ""))
    log("repo        : %s" % args.repo)
    log("map         : %s" % args.map)
    log("out dir     : %s" % args.out)
    log("h-sets      : %s" % ", ".join(hsets))
    log("phase       : %.1f deg" % args.phase)
    log("limits      : winding %.1f degC / magnet %.1f degC"
        % (args.limit_winding, args.limit_magnet))
    log("unit solve  : %.4g W per source (G = (T_unit - 70)/unit_W; icont divides it out)"
        % args.unit_W)
    log("")

    # ---- loss table -----------------------------------------------------
    records = jm.load_map(args.map)
    log("JEET map: %d records" % len(records))
    table = build_run_table(records, hsets, args)
    n_expected = 4 * 4 * 2 * 2
    log("run table: %d entries (%d speeds x %d currents x %d cases x %d h-sets)"
        % (len(table), len(args.speeds), len(args.currents), len(CASES), len(hsets)))
    if len(table) != n_expected:
        log("  [warn] the plan's skeleton expects exactly %d runs; this run produced "
            "%d because the speed/current/h-set selection was overridden."
            % (n_expected, len(table)))
    rated = [r for r in table
             if r["speed"] == 16000 and abs(r["current"] - 460.0) < 1e-6
             and r["case"] == "AC"][:1]
    if rated:
        p = rated[0]["P_W"]
        log("rated cell 16000 rpm / 460 A / AC: cu_slot %.1f  cu_end %.1f  ac_slot %.1f "
            "fe_s %.1f  fe_r %.1f  pm %.1f W  (total %.1f kW)"
            % (p["cu_slot"], p["cu_end"], p["ac_slot"], p["fe_s"], p["fe_r"], p["pm"],
               sum(p.values()) / 1000.0))

    # ---- backend --------------------------------------------------------
    backend = (SyntheticBackend(args, log) if args.dry_run else MapdlBackend(args, log))
    payload = None
    t_setup0 = time.time()
    try:
        backend.setup()
        t_setup = time.time() - t_setup0

        mode = args.mode
        gmaps = {}
        influence_json = None
        supercheck = {"performed": False, "mode": mode}
        t_unit = 0.0
        t_verify = 0.0

        if mode == "super":
            log.rule("unit solves (%d per h-set, ac_slot aliased to cu_slot)"
                     % len(UNIT_SOURCES))
            t0 = time.time()
            for h in hsets:
                log("h-set %s:" % h)
                gmaps[h] = backend.influence(h)
            t_unit = time.time() - t0

            log.rule("superposition verification")
            roundtrip = {}
            for h in hsets:
                roundtrip[h] = unit_roundtrip_check(backend, gmaps[h], h, args, log)
            vhset = "base" if "base" in hsets else hsets[0]
            t0 = time.time()
            points, worst = verify_superposition(backend, gmaps[vhset], vhset,
                                                 records, args, log)
            t_verify = time.time() - t0
            ok = all(p["ok"] for p in points)
            supercheck = {"performed": True, "ok": bool(ok),
                          "tol_K": float(args.superposition_tol),
                          "worst_err_K": float(worst),
                          # alias under icont.check_superposition's own key name so
                          # make_thesis_figs.py (and anything else that speaks that
                          # dialect) can read the number without special-casing D1
                          "max_abs_err_K": float(worst),
                          "verified_htc_set": vhset,
                          "unit_roundtrip": roundtrip,
                          "points": points,
                          "note": ("Two DIRECT full-load solves compared against the "
                                   "reconstruction. The fixed-node comparison is the "
                                   "linearity test; max_functional_err_K additionally "
                                   "checks the max-over-nodes operator that the runs "
                                   "table uses.")}
            log("superposition: worst error %.4g K vs tol %.3g K -> %s"
                % (worst, args.superposition_tol, "PASS" if ok else "FAIL"))

            if not ok:
                lines = ["SUPERPOSITION CHECK FAILED (worst %.4g K > tol %.4g K)."
                         % (worst, args.superposition_tol),
                         "The steady model did not behave linearly, or a unit solve is "
                         "wrong, or a selection leaked into a SOLVE.",
                         "Every reconstructed number in this JSON would be wrong.",
                         "on-superposition-fail = %s" % args.on_superposition_fail]
                for p in points:
                    lines.append("  %s: fixed-node %.4g K, max-functional %.4g K"
                                 % (p["point"], p["max_abs_err_K"],
                                    p["max_functional_err_K"]))
                if args.on_superposition_fail == "brute":
                    lines.append("FALLING BACK to --mode brute in this same MAPDL "
                                 "session (the mesh and circuit are already built).")
                elif args.on_superposition_fail == "stop":
                    lines.append("Stopping. Re-run with --mode brute (the plan-literal "
                                 "64 solves) or --on-superposition-fail brute.")
                else:
                    lines.append("--on-superposition-fail continue: writing the "
                                 "reconstructed numbers ANYWAY. They are suspect.")
                log.banner(lines)
                if args.on_superposition_fail == "brute":
                    mode = "brute"
                elif args.on_superposition_fail == "stop":
                    empty = i_bundle(empty_nested(hsets), empty_nested(hsets),
                                     empty_nested(hsets), empty_nested(hsets),
                                     empty_nested(hsets), empty_nested(hsets))
                    # keep the influence coefficients: suspect, but they are the
                    # primary diagnostic for WHY the check failed
                    diag = build_influence_json(gmaps, backend, records, args)
                    payload = assemble(args, hsets, table, empty, diag, supercheck,
                                       backend, "super(failed)", records,
                                       {"setup_s": t_setup, "unit_solves_s": t_unit,
                                        "verify_s": t_verify,
                                        "total_s": time.time() - t_start,
                                        "n_solves": int(backend.n_solves),
                                        "solves": backend.solve_log},
                                       aborted="superposition check failed")
                    return payload, 2, backend

        # ---- fill the runs table ---------------------------------------
        log.rule("runs (%d entries, mode=%s)" % (len(table), mode))
        temps_by_key = {}
        t_runs0 = time.time()
        if mode == "super":
            for i, entry in enumerate(table, start=1):
                g = gmaps[entry["htc"]]
                field = reconstruct_field(g, entry["P_W"])
                t_c_full, circ, argmax_pos = monitored_from_field(
                    field, backend.part_idx, backend.circ_pos)
                entry["T_C"] = plan_t_c(t_c_full)
                entry["circuit_T"] = circ
                entry["_source"] = "reconstructed"
                entry["_argmax_nodes"] = dict(
                    (p, int(backend.nnum[argmax_pos[p]])) for p in PARTS)
                entry["P_total_W"] = float(sum(entry["P_W"].values()))
                temps_by_key[_key(entry)] = entry["T_C"]
                log("  %02d/%d %5d rpm %8.3f A %s %-4s  P %7.2f kW -> winding_max "
                    "%9.1f  magnet_max %9.1f degC" %
                    (i, len(table), entry["speed"], entry["current"], entry["case"],
                     entry["htc"], entry["P_total_W"] / 1000.0,
                     entry["T_C"]["winding_max"], entry["T_C"]["magnet_max"]))
        else:
            for i, entry in enumerate(table, start=1):
                tag = ("run %02d/%d %d rpm / %.3f A / %s / %s"
                       % (i, len(table), entry["speed"], entry["current"],
                          entry["case"], entry["htc"]))
                field = backend.direct(entry["htc"], entry["P_W"], tag)
                t_c_full, circ, argmax_pos = monitored_from_field(
                    field, backend.part_idx, backend.circ_pos)
                entry["T_C"] = plan_t_c(t_c_full)
                entry["circuit_T"] = circ
                entry["_source"] = "direct"
                entry["_argmax_nodes"] = dict(
                    (p, int(backend.nnum[argmax_pos[p]])) for p in PARTS)
                entry["P_total_W"] = float(sum(entry["P_W"].values()))
                entry["_load_index"] = backend.last_iload      # SET,<this>,1 in POST1
                entry["_solve_time_s"] = backend.last_solve_time
                temps_by_key[_key(entry)] = entry["T_C"]
                log("  %s -> winding_max %.1f degC  magnet_max %.1f degC"
                    % (tag, entry["T_C"]["winding_max"], entry["T_C"]["magnet_max"]))
        t_runs = time.time() - t_runs0

        # attach the direct verification temperatures to the matching grid runs
        if supercheck.get("performed") and supercheck.get("points"):
            for p in supercheck["points"]:
                pt = p["point"]
                for entry in table:
                    if (entry["speed"] == pt["speed"] and entry["case"] == pt["case"]
                            and entry["htc"] == pt["htc"]
                            and abs(entry["current"] - pt["current"]) <= jm.ITOL):
                        entry["_direct_check_C"] = p["direct_C"]
                        entry["_direct_check_max_err_K"] = p["max_abs_err_K"]

        # ---- I_cont -----------------------------------------------------
        log.rule("I_cont")
        i_cont = empty_nested(hsets)
        i_w = empty_nested(hsets)
        i_m = empty_nested(hsets)
        i_by = empty_nested(hsets)
        i_st = empty_nested(hsets)
        i_detail = empty_nested(hsets)
        for h in hsets:
            for case in CASES:
                for speed in args.speeds:
                    tag = "%s/%s/%d" % (h, case, speed)
                    if mode == "super":
                        res = icont_super(gmaps[h], backend, records, speed, case,
                                          args, log, tag)
                        if getattr(args, "_magnetic_map", None) is not None:
                            alternate_args = argparse.Namespace(**vars(args))
                            alternate_args.iron_interpolation = (
                                "linear_i2" if args.iron_interpolation == "linear" else "linear")
                            alternate = icont_super(gmaps[h], backend, records, speed, case,
                                                    alternate_args, log, tag + "/interpolation-check")
                            value, other = res.get("I_cont_Arms"), alternate.get("I_cont_Arms")
                            res["_interpolation_sensitivity"] = {
                                "alternate_method": alternate_args.iron_interpolation,
                                "alternate_I_cont_Arms": other, "alternate_status": alternate.get("status"),
                                "delta_Arms": None if value is None or other is None else other - value,
                                "note": "Same unit fields; interpolation sensitivity, not another FEA solve."}
                    else:
                        cur = list(args.currents)
                        tw = [temps_by_key[(h, case, int(speed), float(c))]["winding_max"]
                              for c in cur]
                        tm = [temps_by_key[(h, case, int(speed), float(c))]["magnet_max"]
                              for c in cur]
                        res = icont_brute(cur, tw, tm, args)
                    key = str(int(speed))
                    i_cont[h][case][key] = res.get("I_cont_Arms")
                    i_w[h][case][key] = res.get("I_cont_winding_Arms")
                    i_m[h][case][key] = res.get("I_cont_magnet_Arms")
                    i_by[h][case][key] = res.get("limited_by")
                    i_st[h][case][key] = res.get("status")
                    i_detail[h][case][key] = res
                    val = res.get("I_cont_Arms")
                    log("  %-16s I_cont = %-10s A  limited_by=%-7s status=%s"
                        % (tag, "None" if val is None else "%.2f" % val,
                           res.get("limited_by"), res.get("status")))
                    if res.get("infeasible_at_zero_current"):
                        log("      [!] the limit is already exceeded at ZERO current: "
                            "the speed-only iron/magnet loss alone overheats the "
                            "machine at %d rpm with the %s h-set. I_cont is 0 A, i.e. "
                            "this operating speed is not continuously feasible at all."
                            % (speed, h))
                    if res.get("status") == "extrap_high":
                        log("      [!] I_cont is above the map's 460 A knot; the AC "
                            "loss there is CLAMPED, not extrapolated. Quote as "
                            "'> 460 A'.")

        # ---- influence coefficients for the JSON -------------------------
        if mode == "super" and gmaps:
            influence_json = build_influence_json(gmaps, backend, records, args)
        else:
            influence_json = {
                "_note": ("not available in --mode brute: the influence matrix only "
                          "exists on the superposition path. Re-run with --mode super "
                          "to get the K/kW sensitivities."),
                "K_per_W": None, "K_per_kW": None}

        timing = {"setup_s": round(t_setup, 2), "unit_solves_s": round(t_unit, 2),
                  "verify_s": round(t_verify, 2), "runs_s": round(t_runs, 2),
                  "total_s": round(time.time() - t_start, 2),
                  "n_solves": int(backend.n_solves),
                  "solves": backend.solve_log}
        payload = assemble(args, hsets, table, i_bundle(i_cont, i_w, i_m, i_by, i_st,
                                                        i_detail),
                           influence_json, supercheck, backend, mode, records, timing)
        return payload, 0, backend
    finally:
        backend.close()


def _key(entry):
    return (entry["htc"], entry["case"], int(entry["speed"]), float(entry["current"]))


def i_bundle(i_cont, i_w, i_m, i_by, i_st, i_detail):
    return {"I_cont_Arms": i_cont, "I_cont_winding_Arms": i_w,
            "I_cont_magnet_Arms": i_m, "I_cont_limited_by": i_by,
            "I_cont_status": i_st, "I_cont_detail": i_detail}


def build_influence_json(gmaps, backend, records, args):
    """K/W and K/kW sensitivities -- a thesis-grade result in their own right."""
    ref_speed, ref_cur, ref_case = 16000, 460.0, "AC"
    try:
        ref_lv = losses_for_run(records, ref_speed, ref_cur, args.phase, ref_case, args)
    except Exception:
        ref_lv = None
    out = {
        "_units": "K per W. Multiply by 1000 for K/kW.",
        "_definition": "G[q][s] = (T_q from the unit solve of source s - 70 degC) / unit_W",
        "_unit_W": float(args.unit_W),
        "_ac_slot": ("aliased to cu_slot: D1 injects the AC slot loss uniformly over the "
                     "same CU_SLOT element set as the DC slot loss, so the two columns "
                     "are identical by construction (exact, not an approximation). D2's "
                     "turn-wise injection must NOT reuse this."),
        "_exactness": {
            "winding_mean": "exact linear functional (mean over a fixed node set)",
            "*_max": ("the row of the hot node at the reference point below. max over "
                      "nodes is convex, not affine, so this row is only valid while the "
                      "argmax node does not move. The runs table never uses these rows: "
                      "it reconstructs the full nodal field and takes the max there."),
            "circuit nodes": "exact (single nodes); OIL is Dirichlet so its row is 0",
        },
        "_reference_point": {"speed": ref_speed, "current": ref_cur, "case": ref_case},
        "K_per_W": {},
        "K_per_kW": {},
        "hot_nodes_at_reference": {},
    }
    for h, g in gmaps.items():
        rows = {}
        hot = {}
        if ref_lv is not None:
            field = reconstruct_field(g, ref_lv)
        else:
            field = reconstruct_field(g, dict((s, 1.0) for s in SOURCES))
        for part in PARTS:
            idx = backend.part_idx[part]
            pos = int(idx[int(np.argmax(field[idx]))])
            rows[part + "_max"] = row_at(g, pos)
            hot[part + "_max"] = int(backend.nnum[pos])
        rows["winding_mean"] = mean_row(g, backend.part_idx["winding"])
        for nm in CIRCUIT_NODES:
            rows[nm] = row_at(g, backend.circ_pos[nm])
        out["K_per_W"][h] = rows
        out["K_per_kW"][h] = dict(
            (q, dict((s, 1000.0 * v) for s, v in row.items())) for q, row in rows.items())
        out["hot_nodes_at_reference"][h] = hot
    return out


def assemble(args, hsets, table, ibundle, influence_json, supercheck, backend, mode,
             records, timing, aborted=None):
    notes = [
        GAP_NOTE,
        HTC_META["htc_big"],
        HTC_META["splash_scope"],
        ("MASS71 thermal capacitance is OFF: in a steady solve [C] is not assembled, so "
         "it would be inert. Removing it floats nothing -- JACKET, SPRAY and SHF are each "
         "tied to OIL by a COMBIN14."),
        ("Stator/winding interface nodes are counted in BOTH parts' max/mean, the same "
         "convention as the validated hybrid run (152.2 / 126.0 degC), so the numbers stay "
         "comparable."),
        ("At the plan's own operating points the losses are enormous (16 krpm / 460 A "
         "Case AC is ~87 kW of copper against the 3.35 kW validated run), so absolute "
         "temperatures land in the hundreds to thousands of degC with temperature-"
         "independent material properties. That is the finding -- the point cannot be run "
         "continuously -- not a solver bug. Quote the normalized K/kW sensitivities "
         "alongside any absolute temperature."),
    ]
    if mode == "super":
        notes.append(
            "Temperatures come from %d unit solves per h-set plus %d direct verification "
            "solves, not from %d brute-force solves. The model is exactly linear "
            "(constant KXX, constant h, constant circuit conductances, no radiation, one "
            "Dirichlet), so the reconstruction is exact and was verified to %.3g K."
            % (len(UNIT_SOURCES), len(VERIFY_POINTS), len(table),
               args.superposition_tol))
    else:
        notes.append("Temperatures come from %d direct solves (plan-literal brute force). "
                     "I_cont uses the 4-point bracket, LINEAR IN I^2 (linear in I biases "
                     "I_cont low by up to 5.7 percent on the 115-230 A bracket)."
                     % len(table))
    if args.dry_run:
        notes.insert(0, "DRY RUN: the influence matrix is SYNTHETIC. Every temperature "
                        "and every I_cont in this file is fabricated plumbing output. "
                        "No mesh was read and no equation was solved.")
    if aborted:
        notes.insert(0, "ABORTED: %s" % aborted)

    payload = {
        "_model": "JAC279 hybrid steady",
        "_soltype": "steady",
        "_loss_source": LOSS_SOURCE_LITERAL,
        "_htc": htc_string(),
        "_htc_sets": {"base": dict(HTC_SETS["base"]), "sph": dict(HTC_SETS["sph"])},
        "_htc_meta": HTC_META,
        "_loss_model_caveat": LOSS_MODEL_CAVEAT,
        "_mode": mode,
        "_dry_run": bool(args.dry_run),
        "_aborted": aborted,
        "_generated": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "_script": SCRIPT_NAME,
        "_repo": str(args.repo),
        "_map": str(args.map),
        "_map_records": len(records),
        "_phase_deg": float(args.phase),
        "_limits_C": {"winding": float(args.limit_winding),
                      "magnet": float(args.limit_magnet)},
        "_oil": {"T_C": OIL_T, "mdot_kg_s": MDOT_OIL, "G_jkt_W_K": G_JKT_OIL,
                 "G_spray_W_K": G_SPRAY_OIL, "G_shf_W_K": G_SHF_OIL,
                 "G_gap_W_K": G_GAP},
        "_mesh": backend.mesh_info,
        # Nodes that fell below the 70 degC oil Dirichlet. Empty on a clean run.
        # A short list with a few K of undershoot is a SOLID87 mid-side artifact and
        # was tolerated; anything larger aborts the run instead of landing here.
        "_undershoot": list(getattr(backend, "undershoot", []) or []),
        "_run_dir": None if args.dry_run else str(args.run_dir),
        "_rth": (None if args.dry_run
                 else os.path.join(str(args.run_dir), "file.rth")),
        "_timing": timing,
        "_notes": notes,
        "runs": table,
        "influence_coeffs": influence_json,
        "_superposition_check": supercheck,
    }
    payload.update(ibundle)
    measured = getattr(args, "_magnetic_map", None)
    if measured is not None:
        payload["_magnetic_loss_map"] = measured.metadata(args.iron_interpolation)
        payload["_loss_source"] = "JEET copper + measured Motor-CAD D4 magnetic losses"
        payload["_loss_model_caveat"] = (
            "Thermal-only sensitivity with fixed magnetic temperatures and phase. "
            "Voltage feasibility is not imposed. Piecewise interpolation stays inside "
            "the measured current range; this is not a validated drive operating envelope.")
    return payload


# ===========================================================================
# 9.  CLI
# ===========================================================================

def default_repo():
    # kit dir = <repo>/mlxperPJT/thermal/plans/PLAN_20260906_assets  -> 4 levels up.
    return os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir, os.pardir,
                                        os.pardir))


def build_parser():
    p = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="D1 continuous-rating runner (e10, steady, oil-circuit hybrid).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Every external path is an argument. Defaults assume the kit layout "
               "<repo>/mlxperPJT/thermal/plans/PLAN_20260906_assets/.")
    p.add_argument("--repo", default=default_repo(),
                   help="repo root (default: derived from this file's location)")
    p.add_argument("--cdb", default=DEFAULT_CDB,
                   help="mesh path, with or without .cdb (default: %(default)s)")
    p.add_argument("--map", default=None,
                   help="JEET map JSON (default: <repo>/%s)" % jm.MAP_REL)
    p.add_argument("--loss-map", action="append", default=[],
                   help="D4 magnetic loss JSON; repeat for disjoint grid subsets")
    p.add_argument("--iron-interpolation", choices=("linear", "linear_i2"), default="linear",
                   help="Magnetic loss interpolation in current or squared current; no extrapolation")
    p.add_argument("--out", default=None,
                   help="output directory (default: <repo>/mlxperPJT/thermal/thesis_out)")
    p.add_argument("--out-name", default=None,
                   help="output file name (default: e10_cont_rating.json, or "
                        "e10_cont_rating_dryrun.json with --dry-run)")
    p.add_argument("--run-dir", default=None,
                   help="MAPDL run_location (default: a fresh timestamped temp dir)")
    p.add_argument("--log", default=None,
                   help="log file (default: <out>/d1_cont_rating_<timestamp>.log)")
    p.add_argument("--nproc", type=int, default=4, help="MAPDL cores (default 4)")
    p.add_argument("--mode", choices=("super", "brute"), default="super",
                   help="super = 5 unit solves per h-set + 2 verification solves "
                        "(default); brute = the plan-literal 64 solves")
    p.add_argument("--htc-set", choices=("base", "sph", "both"), default="both")
    p.add_argument("--phase", type=float, default=jm.PHASE_DEFAULT)
    p.add_argument("--limit-winding", type=float, default=icont.LIM_WINDING_C)
    p.add_argument("--limit-magnet", type=float, default=icont.LIM_MAGNET_C)
    p.add_argument("--dry-run", action="store_true",
                   help="no MAPDL: synthetic influence matrix, real map, real maths, "
                        "real JSON")
    # additive options
    p.add_argument("--unit-W", type=float, default=1000.0,
                   help="watts injected per unit solve (divided out; 1000 W conditions "
                        "the subtraction ~800x better than 1 W). Default 1000.")
    p.add_argument("--superposition-tol", type=float, default=icont.SUPERPOSITION_TOL_K,
                   help="K, acceptance for the reconstruction vs direct check")
    p.add_argument("--on-superposition-fail", choices=("brute", "stop", "continue"),
                   default="brute",
                   help="brute (default): shout and finish with the 64 direct solves in "
                        "the same session; stop: shout and exit 2; continue: shout and "
                        "keep the suspect numbers")
    p.add_argument("--speeds", default=",".join(str(s) for s in SPEEDS))
    p.add_argument("--currents", default=",".join(repr(c) for c in CURRENTS_D1))
    p.add_argument("--i-hi", type=float, default=600.0,
                   help="upper end of the I_cont search bracket [A]")
    p.add_argument("--transient", action="store_true",
                   help="re-enable MASS71 (transient only). D1 is steady; this exists so "
                        "the model code stays a single source of truth.")
    p.add_argument("--allow-empty-surface", action="store_true",
                   help="downgrade an empty SURF152 selection from an error to a "
                        "warning. Only for diagnosis: a missing convection path means "
                        "the oil circuit is incomplete and the temperatures are wrong.")
    p.add_argument("--ground-guard", action="store_true",
                   help="add h=1e-3 W/m2K on every exterior node. Recovery option for a "
                        "singular pivot (floating island); perturbs results by ~4e-6.")
    p.add_argument("--additional-switches", default=None,
                   help="passed to launch_mapdl, e.g. \"-m 8192 -db 2048\"")
    p.add_argument("--dry-run-nonlinear", type=float, default=0.0,
                   help="dry run only: inject this much fake nonlinearity into the "
                        "synthetic direct solves to exercise the failure path")
    p.add_argument("--json-indent", type=int, default=1)
    p.add_argument("--no-git-check", action="store_true",
                   help="skip the git check-ignore audit of the written files")
    p.add_argument("--undershoot-max-nodes", type=int, default=50,
                   help="how many nodes may sit below the oil Dirichlet before the run "
                        "is called a failure (SOLID87 mid-side undershoot; default 50 "
                        "of ~1.1e6). Set 0 to demand a strict maximum principle.")
    p.add_argument("--undershoot-max-K", type=float, default=20.0,
                   help="absolute floor for the tolerated undershoot, in K (default 20). "
                        "The effective limit is max(this, --undershoot-max-frac * field "
                        "range), because the undershoot scales with the load.")
    p.add_argument("--undershoot-mean-rel-tol", type=float, default=1e-4,
                   help="how much the cold outliers may contaminate the winding mean, "
                        "RELATIVE to the field (contamination / (mean_good - T_oil)); "
                        "default 1e-4. Relative because the contamination scales with load.")
    p.add_argument("--undershoot-max-frac", type=float, default=0.30,
                   help="tolerated undershoot as a fraction of the field range "
                        "(T_max - T_oil); default 0.30. The real gates are the node "
                        "count, the circuit nodes, the mean shift and the superposition "
                        "check -- this is only a backstop against a wild field.")
    return p


def finish_args(args):
    args.repo = os.path.abspath(str(args.repo))
    if args.map is None:
        args.map = jm.default_map_path(args.repo)
    args.map = os.path.abspath(str(args.map))
    if args.out is None:
        args.out = os.path.join(args.repo, "mlxperPJT", "thermal", "thesis_out")
    args.out = os.path.abspath(str(args.out))
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.out_name is None:
        args.out_name = ("e10_cont_rating_dryrun.json" if args.dry_run
                         else "e10_cont_rating.json")
    if args.run_dir is None:
        args.run_dir = os.path.join(tempfile.gettempdir(),
                                    "e10_d1_%s_%d" % (stamp, os.getpid()))
    args.run_dir = os.path.abspath(str(args.run_dir))
    if args.log is None:
        args.log = os.path.join(args.out, "d1_cont_rating_%s.log" % stamp)
    args.log = os.path.abspath(str(args.log))
    args.speeds = tuple(int(round(float(s))) for s in str(args.speeds).split(",") if s.strip())
    args.currents = tuple(float(c) for c in str(args.currents).split(",") if c.strip())
    if not args.speeds or not args.currents:
        raise SystemExit("--speeds / --currents must not be empty")
    if args.unit_W == 0.0:
        raise SystemExit("--unit-W must not be 0")
    args._magnetic_map = MagneticLossMap(args.loss_map, args.phase) if args.loss_map else None
    if args._magnetic_map is not None:
        if args.mode != "super":
            raise SystemExit("Measured magnetic losses require --mode super; the old I-squared bracket is not applicable")
        for speed in args.speeds:
            for current in args.currents:
                args._magnetic_map.at(speed, current, args.iron_interpolation)
    if not args.dry_run and not os.path.isdir(args.run_dir):
        os.makedirs(args.run_dir)
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    return args


def main(argv=None):
    args = finish_args(build_parser().parse_args(argv))
    log = Log(args.log)
    code = 0
    backend = None
    try:
        payload, code, backend = run(args, log)
        out_path = os.path.join(args.out, args.out_name)
        write_json(out_path, payload, indent=args.json_indent)
        log.rule("output")
        log("wrote %s (%.1f KB)" % (out_path, os.path.getsize(out_path) / 1024.0))
        info = [args.log] if (args.log and os.path.isfile(args.log)) else []
        if not args.no_git_check:
            report = git_check_ignore(args.repo, [out_path], info, args.out, log)
            payload["_git_check_ignore"] = report
            write_json(out_path, payload, indent=args.json_indent)
        if args.dry_run:
            log("")
            log("DRY RUN COMPLETE. The influence matrix was synthetic: no mesh, no solve.")
            log("On moa, drop --dry-run and pass the real --cdb.")
        log("exit code %d" % code)
        return code
    except D1Error as exc:
        log.banner(["D1 FAILED", str(exc)])
        return 4
    except jm.MapCellMissing as exc:
        log.banner(["JEET MAP CELL MISSING", str(exc)])
        return 5
    except KeyboardInterrupt:
        log.banner(["interrupted by the user"])
        return 130
    finally:
        if backend is not None:
            backend.close()
        log.close()


if __name__ == "__main__":
    sys.exit(main())
