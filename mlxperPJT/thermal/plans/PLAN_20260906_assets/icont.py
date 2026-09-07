# -*- coding: utf-8 -*-
"""icont.py -- continuous-rating mathematics for D1 (e10 thermal, PLAN_20260906).

WHAT THIS IS
------------
Pure, side-effect-free math for the continuous current rating I_cont(n).  No Ansys,
no file IO, no globals mutated.  Everything here is offline-testable: run

    python icont.py --self-test

STDLIB ONLY.  numpy is allowed by the plan but is deliberately not used: the whole
module is closed-form arithmetic and bisection, so keeping it import-light means it
can be imported from a MAPDL runner, from a plotting script, or from a bare python
on any machine.

THE PHYSICS THAT MAKES THIS WORK -- SUPERPOSITION
-------------------------------------------------
The MAPDL hybrid model (04_mapdl_thermal.py) is *exactly linear* in steady state:

  * constant material conductivities  (04:43-47)
  * constant SURF152 convection coefficients (SFE ... CONV)
  * constant COMBIN14 circuit conductances
  * no radiation
  * exactly one Dirichlet condition, D,OIL,TEMP,70

Therefore every nodal temperature is an AFFINE functional of the loss vector:

    T_node(P) = T_OIL + sum_s ( P_s * G[node][s] )                       (1)

with s ranging over SOURCES and G[node][s] in K/W ("influence coefficients").
Consequence for D1: instead of 64 brute-force solves, run FIVE unit solves per
h-set (1 W into each source in turn) and reconstruct all 64 grid entries from (1)
in closed form, exactly.  I_cont then becomes a continuous root-find in I rather
than an interpolation between four grid currents -- which matters, because at
16 krpm the winding exceeds 180 degC even at the lowest grid current (115.075 A),
so the plan's 4-point interpolation would be a pure extrapolation.

FIVE unit solves, not six: ac_slot is injected into the SAME element set as
cu_slot in D1 (uniform slot-copper HGEN), so G[node]["ac_slot"] == G[node]["cu_slot"]
identically.  solve_influence() applies that alias for you (see the keyword
alias_ac_slot_to_cu_slot).
    *** THAT ALIAS IS INVALID FOR D2 ***  D2 injects AC loss turn-by-turn into six
    different radial bands, so its influence coefficients differ from cu_slot's.
    Pass alias_ac_slot_to_cu_slot=False (and a real ac_slot unit solve) for D2.

Superposition must be VERIFIED, never assumed: check_superposition() compares a
reconstruction against a direct full-load solve.  The D1 runner is required to do
two such direct solves and assert < 0.05 K.

STATUS VOCABULARY
-----------------
    ok            root lies inside the plan grid [115.075, 460.0] A
    extrap_low    root below 115.075 A  (the finding at 16 krpm -- report the number)
    extrap_high   root above 460.0 A
    non_monotonic T(I) decreases somewhere -> solver problem, refuse to answer
    degenerate    T does not respond to I at all (bracket path only; suspect the
                  loss injection never happened)

The first four are the ones the plan cares about; "degenerate" is a fifth,
strictly-more-informative branch that only fires where the other four would lie.

WHY LINEAR IN I^2 AND NOT IN I
-------------------------------
DC copper loss is exactly quadratic in current (verified over all 120 FullFEA map
records to 5 significant figures), and the thermal model is linear, so

    T(I) - T_OIL = a + b * I^2                                           (2)

is an identity for Case DC, not a fit.  Interpolating T linearly in I instead of
in I^2 biases I_cont LOW by up to 5.7 % on the lowest grid bracket (115-230 A),
which is exactly the bracket the answer falls in.  i_cont_bracket() therefore
interpolates in I^2 and reports the naive linear-in-I number alongside it so the
size of the error is on the record.

Case AC is NOT exactly quadratic (saturation flattens fea_total_ac_kW at high
current), so (2) is only approximate there; the LSQ residual reported by
i_cont_bracket is the honest measure of how approximate.

UNITS
-----
    losses          W          temperatures  degC
    influence G     K/W        currents      A_rms
    limits          degC       tolerances    K

python 3.10 compatible (no match, no X | Y annotations, no 3.11+ stdlib).
"""

import argparse
import math
import sys

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

T_OIL = 70.0                 # degC, the single Dirichlet node (04_mapdl_thermal.py OIL_T)
LIM_WINDING_C = 180.0        # degC, plan section 1 D1
LIM_MAGNET_C = 150.0         # degC, plan section 1 D1

SOURCES = ("cu_slot", "cu_end", "ac_slot", "fe_s", "fe_r", "pm")

STATUSES = ("ok", "extrap_low", "extrap_high", "non_monotonic", "degenerate")

# The plan's current grid.  Used ONLY to label a root as inside/outside the grid;
# the root-find itself is continuous and unconstrained by it.
GRID_I_LO_A = 115.075
GRID_I_HI_A = 460.0

# DC copper loss is exactly quadratic and independent of speed and phase.
# Verified over all 120 FullFEA records of JEET_ACLoss_Ref_Map_Summary.json:
#     ts_dc_active_only_kW * 1000 = K_DC_SLOT_W_PER_A2 * I^2
#     ts_dc_end_kW         * 1000 = K_DC_END_W_PER_A2  * I^2
# These are exact map identities, not fitted values.  jeet_map_loader.py is the
# authority for loss construction; these live here so that icont.py is testable
# standalone and so a runner can build a continuous p_of_I without the map.
K_DC_SLOT_W_PER_A2 = 0.1484500725968904
K_DC_END_W_PER_A2 = 0.08723750151056191
DC_END_OVER_SLOT = 0.5876554991485352

# Tolerances
MONO_TOL_K = 0.05            # K, a drop larger than this is "non_monotonic"
DEFAULT_N_MONO_SAMPLES = 65  # samples used to verify monotonicity before bisecting
SUPERPOSITION_TOL_K = 0.05   # K, the plan's acceptance threshold


# --------------------------------------------------------------------------
# Small validators (kept private; they raise loudly rather than degrade quietly)
# --------------------------------------------------------------------------

def _as_float(x, what):
    """float(x) with a useful message, rejecting nan/inf."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError("%s: expected a number, got %r" % (what, x))
    if not math.isfinite(v):
        raise ValueError("%s: expected a finite number, got %r "
                         "(a nan/inf here usually means a solve did not converge)"
                         % (what, x))
    return v


def _validate_source_dict(d, name):
    """Copy a {source: value} mapping, rejecting unknown keys and non-finite values."""
    if not hasattr(d, "items"):
        raise ValueError("%s must be a mapping keyed by %s, got %r"
                         % (name, list(SOURCES), type(d).__name__))
    out = {}
    for k, v in d.items():
        if k not in SOURCES:
            raise ValueError("%s: unknown source key %r (allowed: %s)"
                             % (name, k, ", ".join(SOURCES)))
        out[k] = _as_float(v, "%s[%r]" % (name, k))
    return out


def _validate_node_dict(d, name):
    """Copy a {node: temperature} mapping, rejecting non-finite values."""
    if not hasattr(d, "items"):
        raise ValueError("%s must be a mapping keyed by node name, got %r"
                         % (name, type(d).__name__))
    out = {}
    for k, v in d.items():
        out[str(k)] = _as_float(v, "%s[%r]" % (name, k))
    return out


def _grid_status(current, grid_lo, grid_hi):
    if current < grid_lo:
        return "extrap_low"
    if current > grid_hi:
        return "extrap_high"
    return "ok"


def _bisect(f, lo, hi, tol, max_iter=400):
    """Bisect f (increasing, f(lo) <= 0 <= f(hi)) for the root.

    Bisection is used rather than Newton because it cannot diverge and needs no
    derivative of p_of_I (which is piecewise, from a table).  The final bracket is
    then polished by one false-position step: for a smooth f that is far more
    accurate than the midpoint and costs no extra evaluation of f, so the returned
    root is typically ~1e-10 A rather than the tol/2 the bracket guarantees.
    Pure; f must be pure too.
    """
    a = float(lo)
    b = float(hi)
    fa = f(a)
    fb = f(b)
    if fa > 0.0 or fb < 0.0:
        raise ValueError("_bisect: bracket [%g, %g] does not straddle the root "
                         "(f(lo)=%g, f(hi)=%g)" % (a, b, fa, fb))
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    n = 0
    while (b - a) > tol and n < max_iter:
        m = 0.5 * (a + b)
        fm = f(m)
        if fm == 0.0:
            return m
        if fm < 0.0:
            a, fa = m, fm
        else:
            b, fb = m, fm
        n += 1
    if fb != fa:
        root = a - fa * (b - a) / (fb - fa)
        if a <= root <= b:
            return root
    return 0.5 * (a + b)


# --------------------------------------------------------------------------
# 1. Reconstruction (equation 1)
# --------------------------------------------------------------------------

def reconstruct(influence, loss_vec, t_oil=T_OIL):
    """Temperature of ONE monitored quantity from its influence coefficients.

    influence : {source: K per watt} for a single node/quantity
    loss_vec  : {source: watts}
    returns   : degC, float

    T = t_oil + sum_s influence[s] * loss_vec[s]

    Raises ValueError if loss_vec carries a NON-ZERO loss for a source that has no
    influence coefficient -- silently dropping the AC slot loss (37 kW at the rated
    point) because the unit solve was missing is exactly the failure this guards.
    A source present in influence but absent from loss_vec contributes 0.
    """
    inf = _validate_source_dict(influence, "influence")
    los = _validate_source_dict(loss_vec, "loss_vec")
    total = _as_float(t_oil, "t_oil")
    for s in SOURCES:                      # fixed order -> deterministic summation
        p = los.get(s, 0.0)
        if p == 0.0:
            continue
        if s not in inf:
            raise ValueError(
                "reconstruct: loss_vec[%r] = %g W but the influence dict has no %r "
                "coefficient. Run the unit solve for %r, or (D1 only) let "
                "solve_influence alias ac_slot to cu_slot." % (s, p, s, s))
        total += inf[s] * p
    return total


def reconstruct_all(influence_by_node, loss_vec, t_oil=T_OIL):
    """Reconstruct every monitored quantity at once.

    influence_by_node : {node: {source: K/W}}
    loss_vec          : {source: watts}
    returns           : {node: degC}
    """
    if not hasattr(influence_by_node, "items"):
        raise ValueError("influence_by_node must be a mapping {node: {source: K/W}}")
    out = {}
    for node in sorted(influence_by_node):
        out[str(node)] = reconstruct(influence_by_node[node], loss_vec, t_oil)
    return out


def solve_influence(unit_temps, t_oil=T_OIL, unit_W=1.0,
                    alias_ac_slot_to_cu_slot=True):
    """Influence coefficients from the unit solves.

    unit_temps : {source: {node: degC}} -- one entry per unit solve, i.e. the
                 temperatures measured with unit_W watts injected into that source
                 alone and every other source zero.
    unit_W     : watts injected in each unit solve.  Scalar, or {source: watts} if
                 they differ.  1.0 is the plan's "1 W unit solve"; a larger value is
                 legitimate and is divided out here.
                 *** RECOMMENDED: inject 1000.0 W, not 1.0 W. ***  G is recovered by
                 subtracting the 70 degC oil temperature from a solve whose rise is
                 ~2e-2 K at 1 W, so a 1 W unit solve throws away about three decimal
                 digits to cancellation before MAPDL's own output precision is even
                 considered.  Measured on the synthetic self-test, 1000 W conditions
                 the reconstruction ~800x better (6.8e-13 K vs 5.6e-10 K).  Both are
                 far inside the 0.05 K acceptance band, so 1 W is not wrong -- but
                 1000 W costs nothing and buys margin against MAPDL round-off.
    returns    : {node: {source: K/W}}

    G[node][s] = (T_unit[s][node] - t_oil) / unit_W[s]

    With alias_ac_slot_to_cu_slot=True (default) an absent ac_slot entry is filled
    from cu_slot.  That is EXACT for D1, where the AC slot loss is injected
    uniformly over the same mat-3 in-stack element set as the DC slot loss, and it
    is what reduces D1 to five unit solves per h-set.  It is WRONG for D2's
    turn-wise injection -- pass False there.
    """
    if not hasattr(unit_temps, "items"):
        raise ValueError("unit_temps must be a mapping {source: {node: degC}}")

    src_temps = {}
    for s, node_map in unit_temps.items():
        if s not in SOURCES:
            raise ValueError("unit_temps: unknown source key %r (allowed: %s)"
                             % (s, ", ".join(SOURCES)))
        src_temps[s] = _validate_node_dict(node_map, "unit_temps[%r]" % s)
    if not src_temps:
        raise ValueError("unit_temps is empty: no unit solve was recorded")

    # per-source injected power
    if hasattr(unit_W, "items"):
        pw = {}
        for s in src_temps:
            if s not in unit_W:
                raise ValueError("unit_W is a mapping but has no entry for %r" % s)
            pw[s] = _as_float(unit_W[s], "unit_W[%r]" % s)
    else:
        v = _as_float(unit_W, "unit_W")
        pw = dict((s, v) for s in src_temps)
    for s in sorted(pw):
        if pw[s] == 0.0:
            raise ValueError("unit_W[%r] == 0 W: cannot divide out a zero unit load" % s)

    # every unit solve must report the same node set
    nodes = set()
    for d in src_temps.values():
        nodes |= set(d)
    for s in sorted(src_temps):
        missing = sorted(nodes - set(src_temps[s]))
        if missing:
            raise ValueError("unit_temps[%r] is missing node(s) %s that other unit "
                             "solves report -- the extraction is inconsistent"
                             % (s, missing))

    t0 = _as_float(t_oil, "t_oil")
    out = {}
    for node in sorted(nodes):
        row = {}
        for s in SOURCES:
            if s in src_temps:
                row[s] = (src_temps[s][node] - t0) / pw[s]
        if alias_ac_slot_to_cu_slot and "ac_slot" not in row and "cu_slot" in row:
            row["ac_slot"] = row["cu_slot"]
        out[node] = row
    return out


def check_superposition(influence_by_node, loss_vec, direct_temps,
                        tol_K=SUPERPOSITION_TOL_K, t_oil=T_OIL):
    """Compare a reconstruction against a DIRECT full-load solve.

    returns {"ok": bool, "max_abs_err_K": float, "per_node": {node: signed K}, ...}

    Sign convention: per_node[n] = reconstructed - direct.
    ok is False (and max_abs_err_K is inf) when the two dicts share no node name --
    that is a key-naming bug, not a passing check.
    """
    recon = reconstruct_all(influence_by_node, loss_vec, t_oil)
    direct = _validate_node_dict(direct_temps, "direct_temps")
    tol = _as_float(tol_K, "tol_K")

    common = sorted(set(recon) & set(direct))
    if not common:
        return {"ok": False,
                "max_abs_err_K": float("inf"),
                "per_node": {},
                "worst_node": None,
                "n_nodes": 0,
                "tol_K": tol,
                "reconstructed_C": recon,
                "direct_C": direct,
                "note": "no node name is common to the reconstruction (%s) and the "
                        "direct solve (%s) -- check the extraction keys"
                        % (sorted(recon), sorted(direct))}

    per_node = {}
    for n in common:
        per_node[n] = recon[n] - direct[n]
    worst = max(common, key=lambda n: abs(per_node[n]))
    max_abs = abs(per_node[worst])
    ok = max_abs <= tol
    if ok:
        note = ("superposition verified: max |reconstructed - direct| = %.4g K "
                "over %d node(s), tol %.4g K" % (max_abs, len(common), tol))
    else:
        note = ("SUPERPOSITION CHECK FAILED: max |reconstructed - direct| = %.4g K "
                "at %r, tol %.4g K. The model is not behaving linearly (or a unit "
                "solve is wrong / a selection was left over before SOLVE). Fall "
                "back to --mode brute." % (max_abs, worst, tol))
    return {"ok": ok,
            "max_abs_err_K": max_abs,
            "per_node": per_node,
            "worst_node": worst,
            "n_nodes": len(common),
            "tol_K": tol,
            "reconstructed_C": recon,
            "direct_C": direct,
            "note": note}


# --------------------------------------------------------------------------
# 2. Continuous root-find (the superposition path)
# --------------------------------------------------------------------------

def _empty_rootfind_result(status, notes, lo, hi, lim_w, lim_m, grid_lo, grid_hi,
                           n_mono, monotonic):
    return {"I_cont_Arms": None,
            "I_cont_winding_Arms": None,
            "I_cont_magnet_Arms": None,
            "limited_by": None,
            "status": status,
            "T_at_I_cont": {"winding": None, "magnet": None},
            "P_W_at_I_cont": None,
            "status_winding": status,
            "status_magnet": status,
            "limits_C": {"winding": lim_w, "magnet": lim_m},
            "search_range_Arms": [lo, hi],
            "grid_Arms": [grid_lo, grid_hi],
            "n_mono_samples": n_mono,
            "monotonic": monotonic,
            "infeasible_at_zero_current": False,
            "method": "superposition + bisection",
            "notes": notes}


def _solve_one_limit(fT, limit, lo, hi, tol, grid_lo, grid_hi, max_expand, tag, notes):
    """Bisect fT(I) = limit.  Returns (I or None, status, infeasible_flag)."""
    t_lo = fT(lo)
    if t_lo >= limit:
        notes.append("%s: T(%.4g A) = %.2f degC is already at/above the %.1f degC "
                     "limit -- the current-independent losses alone exceed it. "
                     "No continuous operation at this speed; reporting I_cont = %.4g A."
                     % (tag, lo, t_lo, limit, lo))
        return lo, _grid_status(lo, grid_lo, grid_hi), True

    h = float(hi)
    t_h = fT(h)
    n_exp = 0
    while t_h < limit and n_exp < max_expand:
        h *= 2.0
        n_exp += 1
        t_h = fT(h)
    if t_h < limit:
        notes.append("%s: T(%.4g A) = %.2f degC is still below the %.1f degC limit "
                     "after %d bracket doubling(s); no root found -> I_cont is None."
                     % (tag, h, t_h, limit, n_exp))
        return None, "extrap_high", False
    if n_exp:
        notes.append("%s: search bracket expanded from %.4g A to %.4g A to capture "
                     "the root (the loss model is being evaluated well outside the "
                     "115-460 A map grid -- treat the number as indicative)."
                     % (tag, hi, h))

    root = _bisect(lambda cur: fT(cur) - limit, lo, h, tol)
    return root, _grid_status(root, grid_lo, grid_hi), False


def i_cont_rootfind(influence_w, influence_m, p_of_I, lo=0.0, hi=600.0, tol=1e-4,
                    lim_w=LIM_WINDING_C, lim_m=LIM_MAGNET_C, t_oil=T_OIL,
                    n_mono=DEFAULT_N_MONO_SAMPLES,
                    grid_lo=GRID_I_LO_A, grid_hi=GRID_I_HI_A,
                    max_expand=2):
    """Continuous I_cont by bisection on the reconstructed temperatures.

    influence_w : {source: K/W} for the winding monitored quantity (winding_max)
    influence_m : {source: K/W} for the magnet monitored quantity (magnet_max)
    p_of_I      : callable, A_rms -> {source: watts}.  Must be pure.  Supplied by
                  jeet_map_loader (exact DC quadratic + monotone AC interpolation +
                  the speed-only iron/magnet rule).
    lo, hi      : initial search bracket in A_rms.  hi is doubled up to max_expand
                  times if the limit has not been reached.
    tol         : bisection tolerance in A (returned error <= tol/2).

    returns
        {"I_cont_Arms", "I_cont_winding_Arms", "I_cont_magnet_Arms",
         "limited_by", "status", "T_at_I_cont", ...}

    I_cont_Arms is min(winding-limited, magnet-limited); limited_by names the
    binding one; status is the binding one's status.  A root outside the plan's
    115-460 A grid is still returned as a REAL NUMBER with status extrap_low /
    extrap_high -- at 16 krpm that out-of-grid number is the finding, and reporting
    None there would throw the result away.

    Monotonicity of T(I) is verified by sampling BEFORE bisecting; a decrease larger
    than MONO_TOL_K aborts with status "non_monotonic" and every current None,
    because bisection on a non-monotone function returns a meaningless root.
    """
    lo = _as_float(lo, "lo")
    hi = _as_float(hi, "hi")
    tol = _as_float(tol, "tol")
    lim_w = _as_float(lim_w, "lim_w")
    lim_m = _as_float(lim_m, "lim_m")
    t0 = _as_float(t_oil, "t_oil")
    if not hi > lo:
        raise ValueError("i_cont_rootfind: need hi > lo, got lo=%g hi=%g" % (lo, hi))
    if tol <= 0.0:
        raise ValueError("i_cont_rootfind: tol must be > 0, got %g" % tol)
    n_mono = int(n_mono)
    if n_mono < 3:
        raise ValueError("i_cont_rootfind: n_mono must be >= 3, got %d" % n_mono)
    if not callable(p_of_I):
        raise ValueError("i_cont_rootfind: p_of_I must be callable (A_rms -> loss dict)")

    inf_w = _validate_source_dict(influence_w, "influence_w")
    inf_m = _validate_source_dict(influence_m, "influence_m")

    cache = {}

    def _losses(cur):
        key = float(cur)
        if key not in cache:
            lv = p_of_I(key)
            if not hasattr(lv, "items"):
                raise ValueError("p_of_I(%g) returned %r; expected a {source: watts} "
                                 "mapping" % (key, type(lv).__name__))
            cache[key] = _validate_source_dict(lv, "p_of_I(%g)" % key)
        return cache[key]

    def _tw(cur):
        return reconstruct(inf_w, _losses(cur), t0)

    def _tm(cur):
        return reconstruct(inf_m, _losses(cur), t0)

    notes = []

    # ---- monotonicity guard -------------------------------------------------
    step = (hi - lo) / float(n_mono - 1)
    prev_i = lo
    prev_w = _tw(lo)
    prev_m = _tm(lo)
    for k in range(1, n_mono):
        cur = lo + step * k
        tw = _tw(cur)
        tm = _tm(cur)
        for tag, a, b in (("winding", prev_w, tw), ("magnet", prev_m, tm)):
            if b - a < -MONO_TOL_K:
                notes.append(
                    "%s temperature DECREASES from %.3f degC at %.4g A to %.3f degC "
                    "at %.4g A (drop %.3f K > %.3g K tolerance). T(I) must increase "
                    "monotonically; bisection is invalid. Suspect a non-monotone AC "
                    "loss interpolation, a bad influence coefficient (negative K/W), "
                    "or a stale MAPDL reconnect that solved zero elements."
                    % (tag, a, prev_i, b, cur, a - b, MONO_TOL_K))
                return _empty_rootfind_result("non_monotonic", notes, lo, hi,
                                              lim_w, lim_m, grid_lo, grid_hi,
                                              n_mono, False)
        prev_i, prev_w, prev_m = cur, tw, tm

    # ---- two independent root-finds ----------------------------------------
    i_w, st_w, infeas_w = _solve_one_limit(_tw, lim_w, lo, hi, tol,
                                           grid_lo, grid_hi, max_expand,
                                           "winding", notes)
    i_m, st_m, infeas_m = _solve_one_limit(_tm, lim_m, lo, hi, tol,
                                           grid_lo, grid_hi, max_expand,
                                           "magnet", notes)

    cands = []
    if i_w is not None:
        cands.append((i_w, "winding"))
    if i_m is not None:
        cands.append((i_m, "magnet"))

    if not cands:
        notes.append("neither limit is reached inside the search range -- I_cont is "
                     "above %.4g A for both winding and magnet." % hi)
        res = _empty_rootfind_result("extrap_high", notes, lo, hi, lim_w, lim_m,
                                     grid_lo, grid_hi, n_mono, True)
        res["status_winding"] = st_w
        res["status_magnet"] = st_m
        return res

    # On an exact tie "magnet" sorts first, so a tie is reported as magnet-limited.
    i_cont, limited_by = min(cands)
    status = st_w if limited_by == "winding" else st_m

    notes.append("I_cont = %.4f A, limited by the %s (%s). winding-limited %s A, "
                 "magnet-limited %s A."
                 % (i_cont, limited_by, status,
                    "None" if i_w is None else "%.4f" % i_w,
                    "None" if i_m is None else "%.4f" % i_m))
    if status == "extrap_low":
        notes.append("I_cont is BELOW the plan grid low point %.3f A: the machine "
                     "cannot run continuously anywhere on the plan's current grid at "
                     "this speed. Report the number with the extrap_low label."
                     % grid_lo)
    elif status == "extrap_high":
        notes.append("I_cont is ABOVE the plan grid high point %.1f A: the AC loss "
                     "model is being extrapolated past the map, where saturation "
                     "makes it least trustworthy. Quote as '> %.0f A' in the thesis."
                     % (grid_hi, grid_hi))

    loss_at = _losses(i_cont)
    p_out = {}
    for s in SOURCES:
        p_out[s] = loss_at.get(s, 0.0)

    return {"I_cont_Arms": i_cont,
            "I_cont_winding_Arms": i_w,
            "I_cont_magnet_Arms": i_m,
            "limited_by": limited_by,
            "status": status,
            "T_at_I_cont": {"winding": _tw(i_cont), "magnet": _tm(i_cont)},
            "P_W_at_I_cont": p_out,
            "status_winding": st_w,
            "status_magnet": st_m,
            "limits_C": {"winding": lim_w, "magnet": lim_m},
            "search_range_Arms": [lo, hi],
            "grid_Arms": [grid_lo, grid_hi],
            "n_mono_samples": n_mono,
            "monotonic": True,
            "infeasible_at_zero_current": bool(infeas_w or infeas_m),
            "method": "superposition + bisection",
            "notes": notes}


# --------------------------------------------------------------------------
# 3. Plan-literal 4-point bracket (the --mode brute path)
# --------------------------------------------------------------------------

def _lsq_in_I2(currents, temps, t_oil):
    """Ordinary least squares of (T - t_oil) on I^2.  Returns (a, b, rms, r2)."""
    n = len(currents)
    xs = [c * c for c in currents]
    ys = [t - t_oil for t in temps]
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) * (x - mx) for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0.0:
        return None, None, None, None
    b = sxy / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    rms = math.sqrt(sum(r * r for r in resid) / n)
    sst = sum((y - my) * (y - my) for y in ys)
    r2 = 1.0 - sum(r * r for r in resid) / sst if sst > 0.0 else 1.0
    return a, b, rms, r2


def _root_in_I2(i1, t1, i2, t2, limit):
    """Interpolate/extrapolate linearly in I^2 through (i1,t1),(i2,t2).

    Returns (I or None, note).  A negative I^2 means the limit is exceeded even at
    zero current, which is reported as 0.0 A.
    """
    if t2 == t1:
        return None, ("the two points used have identical temperatures (%.3f degC), "
                      "so the slope is undefined" % t1)
    frac = (limit - t1) / (t2 - t1)
    i_sq = i1 * i1 + (i2 * i2 - i1 * i1) * frac
    if i_sq <= 0.0:
        return 0.0, ("linear-in-I^2 extrapolation gives I^2 = %.4g <= 0: the "
                     "current-independent losses alone exceed the limit. "
                     "Reported as 0 A." % i_sq)
    return math.sqrt(i_sq), None


def i_cont_bracket(currents, temps, limit, t_oil=T_OIL, label="monitored",
                   grid_lo=GRID_I_LO_A, grid_hi=GRID_I_HI_A):
    """Plan-literal 4-point interpolation, LINEAR IN I^2.

    currents : sequence of A_rms (the plan's {115.075, 230.05, 345.025, 460.0})
    temps    : matching monitored temperatures in degC
    limit    : degC
    label    : "winding" | "magnet" | anything, only used to shape the result so it
               matches i_cont_rootfind's

    T - t_oil = a + b*I^2 is an identity for Case DC (DC copper loss is exactly
    quadratic and the thermal model is linear), so bracketing in I^2 is exact there
    and merely a good approximation for Case AC.  Bracketing linearly in I instead
    biases I_cont low by up to 5.7 % on the 115-230 A bracket; that naive value is
    returned as I_cont_naive_linear_in_I_Arms so the bias stays on the record.

    Branches:
        bracket found            -> status ok,          I_cont_Arms = number
        all temps below limit    -> status extrap_high, I_cont_Arms = None
                                    (the number is in I_cont_extrap_Arms; quote it
                                     as "> grid_hi" -- extrapolating the AC loss
                                     above 460 A is not defensible)
        all temps above limit    -> status extrap_low,  I_cont_Arms = number
                                    (extrapolating DOWN is defensible: a+b*I^2 is
                                     exact for Case DC)
        T(I) decreases           -> status non_monotonic, I_cont_Arms = None
        slope undefined          -> status degenerate,    I_cont_Arms = None
    """
    cur = [_as_float(c, "currents[%d]" % i) for i, c in enumerate(currents)]
    tmp = [_as_float(t, "temps[%d]" % i) for i, t in enumerate(temps)]
    if len(cur) != len(tmp):
        raise ValueError("i_cont_bracket: currents and temps differ in length "
                         "(%d vs %d)" % (len(cur), len(tmp)))
    if len(cur) < 2:
        raise ValueError("i_cont_bracket: need at least 2 (I, T) points, got %d"
                         % len(cur))
    limit = _as_float(limit, "limit")
    t0 = _as_float(t_oil, "t_oil")

    order = sorted(range(len(cur)), key=lambda k: cur[k])
    cur = [cur[k] for k in order]
    tmp = [tmp[k] for k in order]
    for k in range(1, len(cur)):
        if cur[k] == cur[k - 1]:
            raise ValueError("i_cont_bracket: duplicate current %g A in the grid"
                             % cur[k])

    notes = []
    a, b, rms, r2 = _lsq_in_I2(cur, tmp, t0)
    fit = {"a_K": a, "b_K_per_A2": b, "fit_rms_K": rms, "fit_r2": r2}
    i_lsq = None
    if b is not None and b > 0.0 and (limit - t0 - a) > 0.0:
        i_lsq = math.sqrt((limit - t0 - a) / b)
    if rms is not None and rms > 1.0:
        notes.append("least-squares residual rms = %.2f K on the a + b*I^2 model. "
                     "Case DC should sit under 0.1 K (the model is linear and the DC "
                     "loss is exactly quadratic); a large value means either Case AC "
                     "saturation or a solve that did not converge." % rms)

    def _result(i_cont, status):
        limited = label if (i_cont is not None and label in ("winding", "magnet")) else None
        return {"I_cont_Arms": i_cont,
                "I_cont_winding_Arms": i_cont if label == "winding" else None,
                "I_cont_magnet_Arms": i_cont if label == "magnet" else None,
                "limited_by": limited,
                "status": status,
                "T_at_I_cont": {label: (limit if i_cont is not None else None)},
                "label": label,
                "limit_C": limit,
                "method": "4-point bracket, linear in I^2",
                "I_cont_naive_linear_in_I_Arms": naive,
                "I_cont_extrap_Arms": extrap,
                "I_cont_lsq_I2_Arms": i_lsq,
                "bracket": bracket,
                "fit": fit,
                "I_pts_Arms": list(cur),
                "T_pts_C": list(tmp),
                "grid_Arms": [grid_lo, grid_hi],
                "notes": notes}

    naive = None
    extrap = None
    bracket = None

    # ---- monotonicity ------------------------------------------------------
    for k in range(1, len(tmp)):
        if tmp[k] - tmp[k - 1] < -MONO_TOL_K:
            notes.append("temperature DECREASES from %.3f degC at %.4g A to %.3f "
                         "degC at %.4g A (drop %.3f K). Interpolation is invalid; "
                         "suspect a stale MAPDL reconnect (zero elements solved) or "
                         "a non-converged run."
                         % (tmp[k - 1], cur[k - 1], tmp[k], cur[k],
                            tmp[k - 1] - tmp[k]))
            return _result(None, "non_monotonic")

    # ---- locate the bracket ------------------------------------------------
    k_hit = None
    for k in range(len(tmp)):
        if tmp[k] >= limit:
            k_hit = k
            break

    if k_hit is None:
        # every point below the limit
        i1, t1, i2, t2 = cur[-2], tmp[-2], cur[-1], tmp[-1]
        extrap, why = _root_in_I2(i1, t1, i2, t2, limit)
        if extrap is None:
            notes.append("all %d points are below the %.1f degC limit and %s"
                         % (len(cur), limit, why))
            return _result(None, "degenerate")
        notes.append("all %d points are below the %.1f degC limit (T_max = %.2f degC "
                     "at %.4g A). I_cont is above the grid; the linear-in-I^2 "
                     "extrapolation gives %.2f A but AC saturation makes that "
                     "untrustworthy -- quote as '> %.0f A'. I_cont_Arms is left None "
                     "on purpose."
                     % (len(cur), limit, tmp[-1], cur[-1], extrap, grid_hi))
        return _result(None, "extrap_high")

    if k_hit == 0:
        # every point at/above the limit -> extrapolate DOWN from the two lowest
        i1, t1, i2, t2 = cur[0], tmp[0], cur[1], tmp[1]
        val, why = _root_in_I2(i1, t1, i2, t2, limit)
        if val is None:
            notes.append("all %d points are at/above the %.1f degC limit and %s"
                         % (len(cur), limit, why))
            return _result(None, "degenerate")
        bracket = {"I1": i1, "T1": t1, "I2": i2, "T2": t2, "kind": "extrapolated down"}
        notes.append("all %d points are at/above the %.1f degC limit (T_min = %.2f "
                     "degC at %.4g A). I_cont = %.3f A is extrapolated BELOW the grid "
                     "low point %.3f A. That extrapolation is defensible -- a + b*I^2 "
                     "is exact for Case DC -- but it must carry the extrap_low label."
                     % (len(cur), limit, tmp[0], cur[0], val, grid_lo))
        return _result(val, "extrap_low")

    i1, t1 = cur[k_hit - 1], tmp[k_hit - 1]
    i2, t2 = cur[k_hit], tmp[k_hit]
    val, why = _root_in_I2(i1, t1, i2, t2, limit)
    if val is None:
        notes.append("the bracketing pair (%.4g A, %.3f degC) - (%.4g A, %.3f degC) "
                     "is degenerate: %s" % (i1, t1, i2, t2, why))
        return _result(None, "degenerate")
    bracket = {"I1": i1, "T1": t1, "I2": i2, "T2": t2, "kind": "interpolated"}
    naive = i1 + (i2 - i1) * (limit - t1) / (t2 - t1)
    notes.append("bracket %.4g-%.4g A: I_cont = %.3f A (linear in I^2). The naive "
                 "linear-in-I interpolation would give %.3f A, i.e. %+.2f A "
                 "(%+.2f %%) -- linear-in-I always reads low."
                 % (i1, i2, val, naive, naive - val, 100.0 * (naive - val) / val))
    return _result(val, "ok")


def i_cont_bracket_pair(currents, temps_w, temps_m,
                        lim_w=LIM_WINDING_C, lim_m=LIM_MAGNET_C, t_oil=T_OIL,
                        grid_lo=GRID_I_LO_A, grid_hi=GRID_I_HI_A):
    """Both limits through the bracket path; result shaped like i_cont_rootfind's.

    This is the plan-literal path used by --mode brute.  Prefer i_cont_rootfind
    whenever the influence coefficients exist.
    """
    w = i_cont_bracket(currents, temps_w, lim_w, t_oil, "winding", grid_lo, grid_hi)
    m = i_cont_bracket(currents, temps_m, lim_m, t_oil, "magnet", grid_lo, grid_hi)
    i_w = w["I_cont_Arms"]
    i_m = m["I_cont_Arms"]
    cands = []
    if i_w is not None:
        cands.append((i_w, "winding"))
    if i_m is not None:
        cands.append((i_m, "magnet"))
    notes = list(w["notes"]) + list(m["notes"])
    if not cands:
        status = w["status"] if w["status"] == m["status"] else "extrap_high"
        return {"I_cont_Arms": None, "I_cont_winding_Arms": None,
                "I_cont_magnet_Arms": None, "limited_by": None, "status": status,
                "T_at_I_cont": {"winding": None, "magnet": None},
                "status_winding": w["status"], "status_magnet": m["status"],
                "limits_C": {"winding": lim_w, "magnet": lim_m},
                "method": "4-point bracket, linear in I^2",
                "winding": w, "magnet": m, "notes": notes}
    i_cont, limited_by = min(cands)
    status = w["status"] if limited_by == "winding" else m["status"]
    return {"I_cont_Arms": i_cont,
            "I_cont_winding_Arms": i_w,
            "I_cont_magnet_Arms": i_m,
            "limited_by": limited_by,
            "status": status,
            "T_at_I_cont": {"winding": lim_w if i_w is not None else None,
                            "magnet": lim_m if i_m is not None else None},
            "status_winding": w["status"],
            "status_magnet": m["status"],
            "limits_C": {"winding": lim_w, "magnet": lim_m},
            "method": "4-point bracket, linear in I^2",
            "winding": w,
            "magnet": m,
            "notes": notes}


# --------------------------------------------------------------------------
# 4. Self-test
# --------------------------------------------------------------------------

class _Tally(object):
    """Tiny assertion recorder so the self-test reports every check, not just the
    first failure."""

    def __init__(self):
        self.n_pass = 0
        self.n_fail = 0

    def check(self, ok, msg):
        if ok:
            self.n_pass += 1
            print("    [PASS] %s" % msg)
        else:
            self.n_fail += 1
            print("    [FAIL] %s" % msg)
        return bool(ok)


# A synthetic but physically plausible influence matrix.  The scale comes from the
# repo's own measured lumped sensitivity, 20.4 K/kW = 0.0204 K/W
# (ff_mapdl_hybrid_temps.json: 4.024 kW -> winding 152.2 degC over 70 degC oil).
_G_SCALE = 0.0212

_G_TRUE = {
    "winding_max": {"cu_slot": 1.00 * _G_SCALE, "cu_end": 0.80 * _G_SCALE,
                    "ac_slot": 1.00 * _G_SCALE, "fe_s": 0.30 * _G_SCALE,
                    "fe_r": 0.20 * _G_SCALE, "pm": 0.25 * _G_SCALE},
    "winding_mean": {"cu_slot": 0.82 * _G_SCALE, "cu_end": 0.66 * _G_SCALE,
                     "ac_slot": 0.82 * _G_SCALE, "fe_s": 0.27 * _G_SCALE,
                     "fe_r": 0.18 * _G_SCALE, "pm": 0.22 * _G_SCALE},
    "stator_max": {"cu_slot": 0.61 * _G_SCALE, "cu_end": 0.34 * _G_SCALE,
                   "ac_slot": 0.61 * _G_SCALE, "fe_s": 0.55 * _G_SCALE,
                   "fe_r": 0.21 * _G_SCALE, "pm": 0.24 * _G_SCALE},
    "magnet_max": {"cu_slot": 0.50 * _G_SCALE, "cu_end": 0.30 * _G_SCALE,
                   "ac_slot": 0.50 * _G_SCALE, "fe_s": 0.40 * _G_SCALE,
                   "fe_r": 0.60 * _G_SCALE, "pm": 3.00 * _G_SCALE},
    "rotor_max": {"cu_slot": 0.44 * _G_SCALE, "cu_end": 0.26 * _G_SCALE,
                  "ac_slot": 0.44 * _G_SCALE, "fe_s": 0.36 * _G_SCALE,
                  "fe_r": 0.90 * _G_SCALE, "pm": 2.10 * _G_SCALE},
}


def _synth_direct(influence_by_node, loss_vec, t_oil=T_OIL):
    """Ground truth computed independently of reconstruct() (different loop order,
    explicit sorted-key summation) so the comparison is not circular."""
    out = {}
    for node in influence_by_node:
        acc = 0.0
        for s in sorted(influence_by_node[node]):
            acc += influence_by_node[node][s] * loss_vec.get(s, 0.0)
        out[node] = t_oil + acc
    return out


def _synth_unit_temps(influence_by_node, sources, unit_w=1.0, t_oil=T_OIL):
    """Fabricate what a set of 1 W unit solves would have reported."""
    out = {}
    for s in sources:
        node_map = {}
        for node in influence_by_node:
            node_map[node] = t_oil + influence_by_node[node][s] * unit_w
        out[s] = node_map
    return out


def _make_p_of_I(fe_s, fe_r, pm, ac_coef=0.0):
    """Pure-DC (ac_coef = 0) or DC + quadratic-AC loss vector builder."""
    def p_of_I(cur):
        return {"cu_slot": K_DC_SLOT_W_PER_A2 * cur * cur,
                "cu_end": K_DC_END_W_PER_A2 * cur * cur,
                "ac_slot": ac_coef * cur * cur,
                "fe_s": fe_s, "fe_r": fe_r, "pm": pm}
    return p_of_I


def _analytic_root(influence, fe_s, fe_r, pm, limit, ac_coef=0.0, t_oil=T_OIL):
    """Closed-form I where T = limit for a purely quadratic loss model."""
    a = (influence["fe_s"] * fe_s + influence["fe_r"] * fe_r + influence["pm"] * pm)
    b = (influence["cu_slot"] * K_DC_SLOT_W_PER_A2
         + influence["cu_end"] * K_DC_END_W_PER_A2
         + influence.get("ac_slot", 0.0) * ac_coef)
    return math.sqrt((limit - t_oil - a) / b), a, b


def _self_test():
    """Offline proof of correctness.  Returns True if everything passed."""
    t = _Tally()
    line = "=" * 78

    print(line)
    print("icont.py self-test  (python %d.%d.%d, stdlib only)"
          % sys.version_info[:3])
    print("T_OIL = %.1f degC | winding limit %.1f degC | magnet limit %.1f degC"
          % (T_OIL, LIM_WINDING_C, LIM_MAGNET_C))
    print("SOURCES = %s" % (", ".join(SOURCES),))
    print(line)

    # ---------------------------------------------------------------- (a) ---
    print("")
    print("(a) SUPERPOSITION / RECONSTRUCTION IS EXACT FOR A LINEAR MODEL")
    # rated cell 16000 rpm / 460 A / Case AC, phase 36 (real map numbers)
    loss_rated = {"cu_slot": 31412.035361502007,
                  "cu_end": 18459.4553196349,
                  "ac_slot": 37171.8430714458,
                  "fe_s": 2044.6957808069, "fe_r": 81.5285757304,
                  "pm": 654.7377777778}
    direct = _synth_direct(_G_TRUE, loss_rated)

    # six unit solves -> influence -> reconstruct
    unit6 = _synth_unit_temps(_G_TRUE, SOURCES, 1.0)
    g6 = solve_influence(unit6)
    err_g = 0.0
    for node in _G_TRUE:
        for s in SOURCES:
            err_g = max(err_g, abs(g6[node][s] - _G_TRUE[node][s]))
    # 1e-13 K/W, not 0: G is recovered as (T - 70)/1 W, so a ~2e-2 K rise is read
    # off a ~70 K number and loses ~3 digits to cancellation. See solve_influence's
    # unit_W note -- this is exactly why a 1000 W unit solve is preferable.
    t.check(err_g < 1e-13, "solve_influence recovers G to %.3e K/W (float "
                           "cancellation against the 70 degC datum, not an error)"
            % err_g)

    recon6 = reconstruct_all(g6, loss_rated)
    err6 = max(abs(recon6[n] - direct[n]) for n in direct)
    t.check(err6 < 1e-9,
            "reconstruct_all matches the linear ground truth (max err %.3e K)" % err6)
    print("        winding_max reconstructed %.6f degC, direct %.6f degC"
          % (recon6["winding_max"], direct["winding_max"]))

    # five unit solves + the ac_slot -> cu_slot alias (the D1 saving)
    unit5 = _synth_unit_temps(_G_TRUE,
                              ("cu_slot", "cu_end", "fe_s", "fe_r", "pm"), 1.0)
    g5 = solve_influence(unit5)
    recon5 = reconstruct_all(g5, loss_rated)
    err5 = max(abs(recon5[n] - direct[n]) for n in direct)
    t.check(err5 < 1e-9,
            "5 unit solves + ac_slot alias reproduce the 6-source answer "
            "(max err %.3e K)" % err5)
    t.check(len(unit5) == 5, "only %d unit solves were needed per h-set" % len(unit5))

    # unit_W = 1000 W conditioning variant
    unit5k = _synth_unit_temps(_G_TRUE,
                               ("cu_slot", "cu_end", "fe_s", "fe_r", "pm"), 1000.0)
    g5k = solve_influence(unit5k, unit_W=1000.0)
    err5k = max(abs(reconstruct_all(g5k, loss_rated)[n] - direct[n]) for n in direct)
    t.check(err5k < 1e-8,
            "a 1000 W unit solve divides out correctly (max err %.3e K)" % err5k)

    chk = check_superposition(g5, loss_rated, direct)
    t.check(chk["ok"] and chk["max_abs_err_K"] < 1e-9,
            "check_superposition passes: max_abs_err_K = %.3e K"
            % chk["max_abs_err_K"])

    # 200 ppm on one coefficient moves winding_max by ~0.13 K, i.e. just past the
    # plan's 0.05 K acceptance band -- the smallest error the check must still catch.
    bad = dict((n, dict(g5[n])) for n in g5)
    bad["winding_max"]["cu_slot"] *= 1.0002
    chk_bad = check_superposition(bad, loss_rated, direct)
    t.check((not chk_bad["ok"]) and chk_bad["worst_node"] == "winding_max",
            "check_superposition rejects a 200 ppm coefficient error "
            "(%.4f K at %r, tol %.2f K)"
            % (chk_bad["max_abs_err_K"], chk_bad["worst_node"], chk_bad["tol_K"]))

    try:
        reconstruct({"cu_slot": 1e-3}, {"cu_slot": 1000.0, "ac_slot": 37171.8})
        guarded = False
    except ValueError:
        guarded = True
    t.check(guarded,
            "reconstruct refuses to silently drop a 37 kW ac_slot loss that has "
            "no influence coefficient")

    # ---------------------------------------------------------------- (b) ---
    print("")
    print("(b) ROOT-FIND RECOVERS THE ANALYTIC I_cont FOR A PURE-DC QUADRATIC CASE")
    fe_s, fe_r, pm = 722.9, 28.8, 163.7          # 8000 rpm, plan section 1 rule
    p_dc = _make_p_of_I(fe_s, fe_r, pm, 0.0)
    inf_w = _G_TRUE["winding_max"]
    inf_m = _G_TRUE["magnet_max"]
    i_an, a_w, b_w = _analytic_root(inf_w, fe_s, fe_r, pm, LIM_WINDING_C)
    r = i_cont_rootfind(inf_w, inf_m, p_dc)
    err_b = abs(r["I_cont_winding_Arms"] - i_an)
    print("        analytic  I_w = %.9f A   (a = %.4f K, b = %.6e K/A^2)"
          % (i_an, a_w, b_w))
    print("        bisection I_w = %.9f A   status %s, limited_by %s"
          % (r["I_cont_winding_Arms"], r["status"], r["limited_by"]))
    t.check(err_b < 1e-3, "bisection error %.3e A < 1e-3 A" % err_b)
    t.check(r["status"] == "ok", "status is 'ok' (root inside the 115-460 A grid)")
    t.check(abs(r["T_at_I_cont"]["winding"] - LIM_WINDING_C) < 1e-6,
            "T_winding at I_cont is %.10f degC (= the 180 degC limit, residual "
            "%.2e K)" % (r["T_at_I_cont"]["winding"],
                         abs(r["T_at_I_cont"]["winding"] - LIM_WINDING_C)))
    t.check(r["limited_by"] == "winding" and abs(r["I_cont_Arms"] - i_an) < 1e-3,
            "winding binds here (magnet-limited would be %.3f A)"
            % r["I_cont_magnet_Arms"])

    # ---------------------------------------------------------------- (c) ---
    print("")
    print("(c) BRACKET IN I^2 BEATS BRACKET IN I ON A QUADRATIC GROUND TRUTH")
    grid = [115.075, 230.05, 345.025, 460.0]
    i_truth = 162.29                              # lands in the worst bracket
    b_c = (LIM_WINDING_C - T_OIL) / (i_truth * i_truth)
    temps_c = [T_OIL + b_c * c * c for c in grid]
    rb = i_cont_bracket(grid, temps_c, LIM_WINDING_C, label="winding")
    err_i2 = abs(rb["I_cont_Arms"] - i_truth)
    err_naive = abs(rb["I_cont_naive_linear_in_I_Arms"] - i_truth)
    print("        grid T   = %s degC"
          % ", ".join("%.2f" % v for v in temps_c))
    print("        truth            I_cont = %.6f A" % i_truth)
    print("        linear in I^2    I_cont = %.6f A   error %.3e A (%+.3f %%)"
          % (rb["I_cont_Arms"], err_i2, 100.0 * (rb["I_cont_Arms"] - i_truth) / i_truth))
    print("        naive linear I   I_cont = %.6f A   error %.3e A (%+.3f %%)"
          % (rb["I_cont_naive_linear_in_I_Arms"], err_naive,
             100.0 * (rb["I_cont_naive_linear_in_I_Arms"] - i_truth) / i_truth))
    print("        LSQ on all 4 pts I_cont = %.6f A   (fit rms %.3e K)"
          % (rb["I_cont_lsq_I2_Arms"], rb["fit"]["fit_rms_K"]))
    t.check(err_i2 < 1e-9, "linear-in-I^2 is exact (error %.3e A)" % err_i2)
    t.check(err_naive > 1.0,
            "linear-in-I is wrong by %.3f A (%.2f %%), and always low"
            % (err_naive, 100.0 * err_naive / i_truth))
    t.check(err_i2 < err_naive, "linear-in-I^2 beats linear-in-I by %.1e x"
            % (err_naive / max(err_i2, 1e-15)))
    t.check(abs(rb["I_cont_lsq_I2_Arms"] - i_truth) < 1e-9,
            "the least-squares cross-check agrees to %.3e A"
            % abs(rb["I_cont_lsq_I2_Arms"] - i_truth))

    # ---------------------------------------------------------------- (d) ---
    print("")
    print("(d) ALL FOUR STATUS BRANCHES FIRE -- i_cont_rootfind")
    tiny_m = dict((s, 1e-9) for s in SOURCES)     # magnet that never binds

    # ok  (reuse case b)
    t.check(r["status"] == "ok", "ok            : I_cont = %.3f A" % r["I_cont_Arms"])

    # extrap_low : 10x the thermal resistance -> root far below 115 A
    hot = dict((s, 10.0 * v) for s, v in inf_w.items())
    r_lo = i_cont_rootfind(hot, tiny_m, p_dc)
    t.check(r_lo["status"] == "extrap_low" and r_lo["I_cont_Arms"] is not None,
            "extrap_low    : I_cont = %.3f A (< %.3f A) and is still a REAL NUMBER"
            % (r_lo["I_cont_Arms"], GRID_I_LO_A))

    # extrap_high : 1/12 the thermal resistance -> root above 460 A
    cold = dict((s, v / 12.0) for s, v in inf_w.items())
    r_hi = i_cont_rootfind(cold, tiny_m, p_dc)
    t.check(r_hi["status"] == "extrap_high" and r_hi["I_cont_Arms"] is not None,
            "extrap_high   : I_cont = %.3f A (> %.1f A) and is still a REAL NUMBER"
            % (r_hi["I_cont_Arms"], GRID_I_HI_A))

    # non_monotonic : a loss model that falls with current
    def p_bad(cur):
        return {"cu_slot": 40000.0 / (1.0 + cur), "cu_end": 0.0, "ac_slot": 0.0,
                "fe_s": fe_s, "fe_r": fe_r, "pm": pm}
    r_nm = i_cont_rootfind(inf_w, inf_m, p_bad)
    t.check(r_nm["status"] == "non_monotonic" and r_nm["I_cont_Arms"] is None,
            "non_monotonic : I_cont is None and the run is flagged")
    t.check(len(r_nm["notes"]) > 0 and "DECREASES" in r_nm["notes"][0],
            "non_monotonic carries a diagnostic note")

    # infeasible at zero current -> extrap_low with I_cont = 0
    scorch = dict((s, 200.0 * v) for s, v in inf_w.items())
    r_zero = i_cont_rootfind(scorch, tiny_m, p_dc)
    t.check(r_zero["I_cont_Arms"] == 0.0
            and r_zero["status"] == "extrap_low"
            and r_zero["infeasible_at_zero_current"],
            "infeasible    : iron+magnet loss alone exceeds 180 degC -> I_cont = 0 A")

    print("")
    print("(d) ALL FOUR STATUS BRANCHES FIRE -- i_cont_bracket")
    t.check(rb["status"] == "ok", "ok            : I_cont = %.3f A" % rb["I_cont_Arms"])

    b_hi = i_cont_bracket(grid, [90.0, 110.0, 140.0, 175.0], LIM_WINDING_C,
                          label="winding")
    t.check(b_hi["status"] == "extrap_high" and b_hi["I_cont_Arms"] is None
            and b_hi["I_cont_extrap_Arms"] is not None,
            "extrap_high   : I_cont None, extrapolated value %.1f A kept aside "
            "(quote as '> %.0f A')" % (b_hi["I_cont_extrap_Arms"], GRID_I_HI_A))

    b_lo = i_cont_bracket(grid, [191.0, 382.0, 700.0, 1146.0], LIM_WINDING_C,
                          label="winding")
    t.check(b_lo["status"] == "extrap_low" and b_lo["I_cont_Arms"] is not None,
            "extrap_low    : I_cont = %.3f A extrapolated below the grid "
            "(this is the 16 krpm / Case DC finding)" % b_lo["I_cont_Arms"])

    b_nm = i_cont_bracket(grid, [120.0, 200.0, 190.0, 400.0], LIM_WINDING_C,
                          label="winding")
    t.check(b_nm["status"] == "non_monotonic" and b_nm["I_cont_Arms"] is None,
            "non_monotonic : I_cont is None and the run is flagged")

    b_dg = i_cont_bracket(grid, [200.0, 200.0, 200.0, 200.0], LIM_WINDING_C,
                          label="winding")
    t.check(b_dg["status"] == "degenerate" and b_dg["I_cont_Arms"] is None,
            "degenerate    : flat T(I) -> I_cont None (suspect the loss injection)")

    fired_rf = set([r["status"], r_lo["status"], r_hi["status"], r_nm["status"]])
    fired_br = set([rb["status"], b_hi["status"], b_lo["status"], b_nm["status"]])
    want = set(["ok", "extrap_low", "extrap_high", "non_monotonic"])
    t.check(fired_rf == want, "rootfind fired all four: %s" % sorted(fired_rf))
    t.check(fired_br == want, "bracket  fired all four: %s" % sorted(fired_br))

    # ---------------------------------------------------------------- (e) ---
    print("")
    print("(e) THE MAGNET LIMIT WINS WHEN IT SHOULD, AND limited_by SAYS SO")
    # A rotor with 3x the baseline magnet self-coupling (9.0 * _G_SCALE vs 3.0):
    # the magnet is then thermally isolated enough that the 150 degC magnet limit
    # is reached before the 180 degC winding limit. Physically this is the 16 krpm
    # case the survey warns about -- magnet loss scales as n^2 and the only path
    # out of the magnet is GAP_R -> GAP_S -> stator through still air.
    inf_m_hot = dict(inf_m)
    inf_m_hot["pm"] = 9.0 * _G_SCALE
    r_mag = i_cont_rootfind(inf_w, inf_m_hot, p_dc)
    i_m_an, a_m, b_m = _analytic_root(inf_m_hot, fe_s, fe_r, pm, LIM_MAGNET_C)
    print("        winding-limited %.3f A | magnet-limited %.3f A "
          "(analytic %.3f A) -> limited_by = %s"
          % (r_mag["I_cont_winding_Arms"], r_mag["I_cont_magnet_Arms"],
             i_m_an, r_mag["limited_by"]))
    t.check(r_mag["limited_by"] == "magnet", "limited_by == 'magnet'")
    t.check(r_mag["I_cont_Arms"] == r_mag["I_cont_magnet_Arms"],
            "I_cont_Arms is the magnet-limited value, i.e. the min()")
    t.check(abs(r_mag["I_cont_magnet_Arms"] - i_m_an) < 1e-3,
            "magnet root matches its analytic value to %.3e A"
            % abs(r_mag["I_cont_magnet_Arms"] - i_m_an))
    t.check(r_mag["I_cont_magnet_Arms"] < r_mag["I_cont_winding_Arms"],
            "and it really is the smaller of the two")

    t.check(r["limited_by"] == "winding",
            "the baseline rotor is winding-limited (%.3f A vs %.3f A)"
            % (r["I_cont_winding_Arms"], r["I_cont_magnet_Arms"]))

    # the same decision through the plan-literal bracket path
    temps_w_g = [reconstruct(inf_w, p_dc(c)) for c in grid]
    temps_m_g = [reconstruct(inf_m_hot, p_dc(c)) for c in grid]
    bp = i_cont_bracket_pair(grid, temps_w_g, temps_m_g)
    t.check(bp["limited_by"] == "magnet",
            "i_cont_bracket_pair agrees: limited_by = %s, I_cont = %s A"
            % (bp["limited_by"],
               "None" if bp["I_cont_Arms"] is None else "%.3f" % bp["I_cont_Arms"]))

    # ---------------------------------------------------------------- (f) ---
    print("")
    print("(f) THE TWO PATHS AGREE ON THE SAME PHYSICS (bracket vs root-find)")
    # Case DC is exactly quadratic, so the bracket must reproduce the root-find.
    # Force the bracket to have a real bracketing pair by using the 'hot' winding.
    temps_hot = [reconstruct(hot, p_dc(c)) for c in grid]
    bb = i_cont_bracket(grid, temps_hot, LIM_WINDING_C, label="winding")
    print("        rootfind %.6f A vs bracket %s A (status %s)"
          % (r_lo["I_cont_winding_Arms"],
             "None" if bb["I_cont_Arms"] is None else "%.6f" % bb["I_cont_Arms"],
             bb["status"]))
    t.check(bb["I_cont_Arms"] is not None
            and abs(bb["I_cont_Arms"] - r_lo["I_cont_winding_Arms"]) < 1e-3,
            "Case DC: bracket and root-find agree to %.3e A"
            % abs(bb["I_cont_Arms"] - r_lo["I_cont_winding_Arms"]))

    print("")
    print(line)
    print("SELF-TEST: %d passed, %d failed" % (t.n_pass, t.n_fail))
    print(line)
    return t.n_fail == 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Continuous-rating mathematics for D1 (superposition + "
                    "root-find, plus the plan-literal 4-point bracket). "
                    "Pure math, no Ansys, no file IO.")
    ap.add_argument("--self-test", action="store_true",
                    help="run the offline self-test and exit non-zero on failure")
    args = ap.parse_args(argv)

    if args.self_test:
        return 0 if _self_test() else 1

    print(__doc__.strip())
    print("")
    print("Nothing to do. Run with --self-test, or import this module:")
    print("    import icont")
    print("    G = icont.solve_influence(unit_temps)          # {node: {source: K/W}}")
    print("    T = icont.reconstruct_all(G, loss_vec)         # {node: degC}")
    print("    r = icont.i_cont_rootfind(G['winding_max'], G['magnet_max'], p_of_I)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
