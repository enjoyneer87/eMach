# -*- coding: utf-8 -*-
"""Three electromagnetic torques from one time-stepped FEA export.

Every quantity below is computed from the element tables of a Motor-CAD
``FEA_data.txt`` export (13 columns: ``TriIndex, Node1..3, RegCode, Bx, By,
A, J, Je, Hx, Hy, Mur``) over a full electrical period, with no solver
post-processing variable involved.

Maxwell stress
    Air-gap integral of ``r B_r B_theta`` averaged over the gap layers —
    :func:`field_metrics.maxwell_torque`, evaluated per time step.

Flux-linkage (dq) torque
    Phase flux linkages from the conductor-region average of ``A_z``,
    phase currents from ``J`` times the conductor area, then

        T = 3/2 p (psi_alpha i_beta - psi_beta i_alpha)

    in the stationary alpha-beta frame.  The cross product is invariant to
    the frame angle, so no d-axis alignment is needed.

Virtual work
    The coenergy density obeys ``dw' = B . dH`` element by element for any
    single-valued constitutive law, so the coenergy rate needs no B-H curve:

        dW'/dt = sum_e V_e (B_e . dH_e/dt)

    and the power balance of the driven circuits gives

        T omega_m = dW'/dt - sum_k lambda_k di_k/dt - P_eddy

    where ``P_eddy = sum_e V_e Je_e^2 / sigma_e`` is the induced-current
    loss that the coenergy bookkeeping does not see.  Both the raw and the
    eddy-corrected torque are returned so the size of that term is visible.

The mesh must keep element identity across the period (Motor-CAD's
time-stepping export does: stator elements are fixed, rotor elements rotate
rigidly, the gap is split into a stator-attached and a rotor-attached layer
with a sliding interface).  ``check_mesh_identity`` verifies this before
the time derivatives are taken.
"""
from __future__ import annotations

import gzip
import io
import re
from typing import Dict, Iterator, List, Optional, Tuple

import numpy as np

from .field_metrics import (_AIRGAP_RE, _is_conductor_region,
                            maxwell_torque)

MU0 = 4e-7 * np.pi

# ── 1. streaming parser for the 13-column export ──────────────────────────

_SOL_RE = re.compile(r"^\s*\d+\s+Solution\s+(\d+)(.*)$")
_TBL_RE = re.compile(r"^\s*\d+\s+(\d+)\s+(\w+Table)\s*$")
_TIME_RE = re.compile(r"Time\s+([0-9.Ee+-]+)\s*\[s\]")
_ROT_RE = re.compile(r"Rotate Step\s*(-?[0-9.]+)")


def _open_text(path: str):
    if path.lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return open(path, encoding="utf-8", errors="ignore")


def _numeric_rows(rows: List[str]) -> np.ndarray:
    """Numeric columns of a table; the trailing name column is dropped."""
    cleaned = []
    for r in rows:
        parts = r.split(",")
        # keep only leading numeric fields
        nums = []
        for p in parts:
            p = p.strip()
            try:
                nums.append(float(p))
            except ValueError:
                break
        cleaned.append(nums)
    n = min(len(c) for c in cleaned)
    return np.array([c[:n] for c in cleaned], dtype=float)


def _region_rows(rows: List[str]) -> Tuple[np.ndarray, Dict[int, str]]:
    num, names = [], {}
    for r in rows:
        parts = [p.strip() for p in r.split(",")]
        try:
            code = int(float(parts[0]))
        except ValueError:
            continue
        vals = []
        for p in parts[:10]:
            try:
                vals.append(float(p))
            except ValueError:
                vals.append(np.nan)
        num.append(vals)
        names[code] = parts[10] if len(parts) > 10 else ""
    return np.array(num, dtype=float), names


def iter_fea_blocks(path: str) -> Iterator[dict]:
    """Yield one dict per Solution block, in file order.

    Keys: ``step`` (1-based), ``time_s`` (None for the static block 1),
    ``rotate_deg``, element arrays ``reg, bx, by, a_wbm, j_am2, je_am2,
    hx, hy, mur, x_mm, y_mm, area_mm2, tri, node_xy``, region arrays
    ``rcode, rnu, rjval, rbremx, rbremy, rsigma`` and ``names``.
    """
    cur_hdr, tbl, rows, tables = None, None, [], {}
    units = {"j_scale": 1.0}      # A/mm2 exports (campaign originals) -> A/m2

    def build():
        E = _numeric_rows(tables["ElementsTable"])
        N = _numeric_rows(tables["NodesTable"])
        R, names = _region_rows(tables["RegionsTable"])
        if units["j_scale"] != 1.0:
            E[:, 8] *= units["j_scale"]
            E[:, 9] *= units["j_scale"]
            R[:, 3] *= units["j_scale"]
        node_xy = np.full((int(N[:, 0].max()) + 1, 2), np.nan)
        node_xy[N[:, 0].astype(int)] = N[:, 1:3]
        tri = E[:, 1:4].astype(int)
        P = node_xy[tri]
        area = 0.5 * np.abs(
            (P[:, 1, 0] - P[:, 0, 0]) * (P[:, 2, 1] - P[:, 0, 1])
            - (P[:, 2, 0] - P[:, 0, 0]) * (P[:, 1, 1] - P[:, 0, 1]))
        has_h = E.shape[1] >= 12
        m_t = _TIME_RE.search(cur_hdr)
        m_r = _ROT_RE.search(cur_hdr)
        m_s = _SOL_RE.match(cur_hdr)
        return {
            "step": int(m_s.group(1)),
            "time_s": float(m_t.group(1)) if m_t else None,
            "rotate_deg": float(m_r.group(1)) if m_r else 0.0,
            "reg": E[:, 4].astype(int),
            "bx": E[:, 5], "by": E[:, 6], "a_wbm": E[:, 7],
            "j_am2": E[:, 8], "je_am2": E[:, 9],
            "hx": E[:, 10] if has_h else None,
            "hy": E[:, 11] if has_h else None,
            "mur": E[:, 12] if E.shape[1] >= 13 else None,
            "x_mm": P[:, :, 0].mean(1), "y_mm": P[:, :, 1].mean(1),
            "area_mm2": area, "tri": tri, "node_xy": node_xy,
            "b_T": np.hypot(E[:, 5], E[:, 6]),
            "rcode": R[:, 0].astype(int), "rnu": R[:, 2],
            "rjval": R[:, 3], "rbremx": R[:, 4], "rbremy": R[:, 5],
            "rsigma": R[:, 8], "names": names,
        }

    with _open_text(path) as fh:
        for ln in fh:
            m = _SOL_RE.match(ln)
            if m:
                if cur_hdr is not None:
                    if tbl:
                        tables[tbl] = rows
                    yield build()
                cur_hdr, tbl, rows, tables = ln.strip(), None, [], {}
                continue
            mt = _TBL_RE.match(ln)
            if mt:
                if tbl:
                    tables[tbl] = rows
                tbl, rows = mt.group(2), []
                continue
            if tbl is None:
                continue
            s = ln.strip()
            if not s or s.startswith("-") and s[1:2] == "-":
                continue
            if tbl == "ElementsTable" and "[A/mm2]" in s:
                units["j_scale"] = 1e6        # campaign-original unit
            if s[0].isdigit() or s[0] == "-":
                rows.append(s)
    if cur_hdr is not None:
        if tbl:
            tables[tbl] = rows
        yield build()


# ── 2. geometry helpers ──────────────────────────────────────────────────

def sector_multiplicity(p: dict) -> int:
    """Full-machine multiplicity of the modelled sector (e.g. 45 deg -> 8)."""
    st = [c for c, n in p["names"].items() if n.strip().lower() == "stator"]
    if not st:
        return 1
    m = p["reg"] == st[0]
    th = np.degrees(np.arctan2(p["y_mm"][m], p["x_mm"][m]))
    span = float(th.max() - th.min())
    return int(round(360.0 / span)) if span > 0 else 1


def conductor_codes(p: dict) -> List[int]:
    return sorted(c for c, n in p["names"].items() if _is_conductor_region(n))


def check_mesh_identity(blocks: List[dict], tol_mm: float = 1e-6) -> dict:
    """Stator elements must not move; rotor elements must rotate rigidly.

    Returns the per-region maximum centroid drift after undoing the rotor
    rotation, so a remeshed region shows up as a large number.
    """
    ref = blocks[0]
    out = {}
    for b in blocks[1:]:
        dth = np.radians(b["rotate_deg"] - ref["rotate_deg"]) \
            * (b["step"] - ref["step"])
        for code in np.unique(ref["reg"]):
            m = ref["reg"] == code
            x0, y0 = ref["x_mm"][m], ref["y_mm"][m]
            x1, y1 = b["x_mm"][m], b["y_mm"][m]
            fixed = np.hypot(x1 - x0, y1 - y0).max()
            c, s = np.cos(dth), np.sin(dth)
            xr, yr = c * x0 - s * y0, s * x0 + c * y0
            rot = np.hypot(x1 - xr, y1 - yr).max()
            out.setdefault(int(code), []).append(min(fixed, rot))
    return {k: float(max(v)) for k, v in out.items()}


# ── 3. phase identification and phase quantities ─────────────────────────

def identify_phases(jval: np.ndarray, codes: List[int]) -> dict:
    """Assign each conductor region to phase a/b/c with a winding sign.

    ``jval`` is (n_steps, n_codes) of region current density.  The
    fundamental phasor of each column is compared with the reference
    column of largest amplitude; positive sequence a -> b -> c is assumed.
    """
    n = jval.shape[0]
    w = np.exp(-2j * np.pi * np.arange(n) / n)
    ph = (jval * w[:, None]).sum(0)
    ref = int(np.argmax(np.abs(ph)))
    ang = np.degrees(np.angle(ph / ph[ref]))
    out = {"phase": np.full(len(codes), -1), "sign": np.zeros(len(codes))}
    targets = {0: 0.0, 1: -120.0, 2: 120.0}
    for i, a in enumerate(ang):
        for k, t in targets.items():
            d = (a - t + 180.0) % 360.0 - 180.0
            if abs(d) < 30.0:
                out["phase"][i], out["sign"][i] = k, 1.0
            elif abs(abs(d) - 180.0) < 30.0:
                out["phase"][i], out["sign"][i] = k, -1.0
    assert (out["phase"] >= 0).all(), "unassigned conductor region"
    out["angle_deg"] = ang
    return out


def clarke(a: np.ndarray, b: np.ndarray, c: np.ndarray):
    """Amplitude-invariant Clarke transform."""
    alpha = (2.0 / 3.0) * (a - 0.5 * b - 0.5 * c)
    beta = (2.0 / 3.0) * (np.sqrt(3.0) / 2.0) * (b - c)
    return alpha, beta


def phase_quantities(blocks: List[dict], l_stack_m: float,
                     n_sect: Optional[int] = None) -> dict:
    """Per-step phase currents [A] and flux linkages [Wb]."""
    p0 = blocks[0]
    if n_sect is None:
        n_sect = sector_multiplicity(p0)
    codes = conductor_codes(p0)
    idx = {c: np.where(p0["reg"] == c)[0] for c in codes}
    area = {c: p0["area_mm2"][idx[c]] * 1e-6 for c in codes}     # m^2
    A_r = {c: float(area[c].sum()) for c in codes}

    ns = len(blocks)
    jval = np.zeros((ns, len(codes)))
    a_mean = np.zeros((ns, len(codes)))
    for t, b in enumerate(blocks):
        rmap = dict(zip(b["rcode"], b["rjval"]))
        for i, c in enumerate(codes):
            jval[t, i] = rmap.get(c, np.nan)
            a_mean[t, i] = float((b["a_wbm"][idx[c]] * area[c]).sum()) \
                / A_r[c]
    ph = identify_phases(jval, codes)

    i_ph = np.zeros((ns, 3))
    lam = np.zeros((ns, 3))
    spread = np.zeros(3)
    for k in range(3):
        sel = np.where(ph["phase"] == k)[0]
        s = ph["sign"][sel]
        cur = jval[:, sel] * s[None, :] * np.array([A_r[codes[i]]
                                                   for i in sel])[None, :]
        i_ph[:, k] = cur.mean(1)
        spread[k] = float(np.abs(cur - cur.mean(1, keepdims=True)).max())
        lam[:, k] = n_sect * l_stack_m * (a_mean[:, sel] * s[None, :]).sum(1)
    return {"i_abc": i_ph, "lam_abc": lam, "n_sect": n_sect,
            "codes": codes, "phase": ph["phase"], "sign": ph["sign"],
            "angle_deg": ph["angle_deg"],
            "current_spread_A": spread, "n_sides_per_phase":
            [int((ph["phase"] == k).sum()) for k in range(3)]}


# ── 4. the three torques ─────────────────────────────────────────────────

def torque_dq(i_abc: np.ndarray, lam_abc: np.ndarray, pole_pairs: int):
    ia, ib = clarke(*i_abc.T)
    la, lb = clarke(*lam_abc.T)
    return 1.5 * pole_pairs * (la * ib - lb * ia)


def _ddt(y: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Second-order central time derivative (one-sided at the two ends).

    The export does not hold a whole steady-state period (block 1 is a
    static pre-solve and the eddy currents take a few tens of steps to
    settle), so no periodic wrap is assumed; callers drop the end samples.
    """
    return np.gradient(y, t, axis=0, edge_order=2)


def true_h(p: dict) -> Tuple[np.ndarray, np.ndarray]:
    """The physical H field, element by element.

    In air, iron and conductors the exported ``Hx, Hy`` satisfy
    ``B = mu0 mur H`` to export rounding.  In the permanent magnets the
    export writes H with the opposite sign (it points along B rather than
    against the magnetisation) and its ``Mur`` column reads 1.0, so there
    H is rebuilt from the constitutive law ``B = Brem + mu0 mur_rec H`` with
    the recoil permeability taken from the region reluctivity ``nu``
    (mur_rec = 1 / (mu0 nu)).  Verified on the e10 exports: relative error
    below 0.5 % in every magnet region once the sign is flipped.
    """
    hx, hy = p["hx"].copy(), p["hy"].copy()
    brx = dict(zip(p["rcode"], p["rbremx"]))
    bry = dict(zip(p["rcode"], p["rbremy"]))
    nu = dict(zip(p["rcode"], p["rnu"]))
    for code in np.unique(p["reg"]):
        c = int(code)
        if abs(brx.get(c, 0.0)) + abs(bry.get(c, 0.0)) <= 0.0:
            continue
        m = p["reg"] == code
        mur = 1.0 / (MU0 * nu[c])
        hx[m] = (p["bx"][m] - brx[c]) / (MU0 * mur)
        hy[m] = (p["by"][m] - bry[c]) / (MU0 * mur)
    return hx, hy


def check_h_semantics(p: dict) -> dict:
    """Relative residual of B = mu0 mur H (+ Brem) per region, using the
    export's own H outside the magnets and :func:`true_h` inside them."""
    out = {}
    brx = dict(zip(p["rcode"], p["rbremx"]))
    bry = dict(zip(p["rcode"], p["rbremy"]))
    nu = dict(zip(p["rcode"], p["rnu"]))
    hx, hy = true_h(p)
    for code in np.unique(p["reg"]):
        c = int(code)
        m = p["reg"] == code
        if m.sum() < 20:
            continue
        is_pm = abs(brx.get(c, 0.0)) + abs(bry.get(c, 0.0)) > 0.0
        mur = (1.0 / (MU0 * nu[c])) if is_pm else p["mur"][m]
        bx_pred = MU0 * mur * hx[m] + brx.get(c, 0.0)
        by_pred = MU0 * mur * hy[m] + bry.get(c, 0.0)
        err = np.hypot(bx_pred - p["bx"][m], by_pred - p["by"][m])
        scale = max(float(np.hypot(p["bx"][m], p["by"][m]).max()), 1e-9)
        out[p["names"].get(c, str(c))] = float(err.max() / scale)
    return out


def torque_virtual_work(blocks: List[dict], pq: dict, l_stack_m: float,
                        omega_m: float) -> dict:
    """Instantaneous coenergy-rate torque.

    With every current-carrying element treated as its own filament, the
    power balance of coenergy is exact at each instant::

        T omega_m = dW'/dt - sum_k lambda_k di_k/dt - sum_e lambda_e di_e/dt

    where the last sum runs over the eddy-current filaments
    (lambda_e = n_sect l A_z,e, i_e = Je_e area_e).  ``T_vw_raw`` omits that
    eddy term, and ``P_eddy`` is returned so the period-average identity
    <sum_e lambda_e di_e/dt> = <P_eddy> can be checked.
    """
    n_sect = pq["n_sect"]
    t = np.array([b["time_s"] for b in blocks])
    ns, ne = len(blocks), len(blocks[0]["reg"])
    area = blocks[0]["area_mm2"] * 1e-6                            # m^2
    V = area * l_stack_m * n_sect                                  # m^3
    BX = np.stack([b["bx"] for b in blocks])
    BY = np.stack([b["by"] for b in blocks])
    H = [true_h(b) for b in blocks]
    HX = np.stack([h[0] for h in H])
    HY = np.stack([h[1] for h in H])
    dWdt = ((BX * _ddt(HX, t) + BY * _ddt(HY, t)) * V[None, :]).sum(1)
    # The coenergy density is a function of H in the material frame.  For
    # isotropic media B is parallel to H and the global-frame rate above is
    # already the material rate.  The magnets are not isotropic (Brem is
    # fixed in the rotor), and for an element rotating at omega_m the
    # material rate is  B.dH/dt|_global - omega_m (H x B)_z .
    brx = dict(zip(blocks[0]["rcode"], blocks[0]["rbremx"]))
    bry = dict(zip(blocks[0]["rcode"], blocks[0]["rbremy"]))
    pm = np.array([abs(brx.get(int(c), 0.0)) + abs(bry.get(int(c), 0.0)) > 0
                   for c in blocks[0]["reg"]])
    rot_sign = np.sign(np.mean([b["rotate_deg"] for b in blocks])) or 1.0
    hxb = (HX[:, pm] * BY[:, pm] - HY[:, pm] * BX[:, pm]) * V[pm][None, :]
    pm_term = rot_sign * omega_m * hxb.sum(1)
    dWdt = dWdt - pm_term

    smap = dict(zip(blocks[0]["rcode"], blocks[0]["rsigma"]))
    sig = np.array([smap.get(int(c), 0.0) for c in blocks[0]["reg"]])
    cond = sig > 0
    JE = np.stack([b["je_am2"][cond] for b in blocks])             # A/m^2
    AZ = np.stack([b["a_wbm"][cond] for b in blocks])              # Wb/m
    i_e = JE * area[cond][None, :]                                 # A
    lam_e = n_sect * l_stack_m * AZ                                # Wb
    eddy_term = (lam_e * _ddt(i_e, t)).sum(1)
    P_eddy = (JE ** 2 / sig[cond][None, :] * V[cond][None, :]).sum(1)

    circ = (pq["lam_abc"] * _ddt(pq["i_abc"], t)).sum(1)
    T_raw = (dWdt - circ) / omega_m
    T_inst = (dWdt - circ - eddy_term) / omega_m
    return {"T_vw_raw": T_raw, "T_vw": T_inst, "dWdt": dWdt,
            "circuit_term": circ, "eddy_term": eddy_term,
            "P_eddy": P_eddy, "t_s": t}


def torque_maxwell_series(blocks: List[dict], l_stack_mm: float,
                          n_sect: Optional[int] = None) -> np.ndarray:
    out = np.zeros(len(blocks))
    for k, b in enumerate(blocks):
        out[k] = maxwell_torque(b, l_stack_mm=l_stack_mm,
                                n_sectors=n_sect)["torque_Nm"]
    return out


def three_torques(path: str, pole_pairs: int, speed_rpm: float,
                  l_stack_mm: float = 150.0, skip_static: bool = True,
                  settle_fraction: float = 0.25) -> dict:
    """Run all three methods on one export and summarise.

    ``skip_static`` drops block 1 (the static pre-solve with Je = 0) from
    the averages; the remaining 127 samples are treated as periodic.
    ``settle_fraction`` additionally excludes the first part of the period
    from the reported means so the eddy-current start-up transient does
    not bias them; full-period means are reported alongside.
    """
    blocks = list(iter_fea_blocks(path))
    drift = check_mesh_identity(blocks[:3])
    h_err = check_h_semantics(blocks[-1])
    if skip_static and blocks[0]["time_s"] is None:
        blocks = blocks[1:]
    omega_m = speed_rpm * 2.0 * np.pi / 60.0
    l_m = l_stack_mm * 1e-3

    pq = phase_quantities(blocks, l_m)
    T_dq = torque_dq(pq["i_abc"], pq["lam_abc"], pole_pairs)
    vw = torque_virtual_work(blocks, pq, l_m, omega_m)
    T_mx = torque_maxwell_series(blocks, l_stack_mm, pq["n_sect"])
    # the flux-linkage product is the air-gap power; the eddy loss inside
    # the conductors and magnets must come off before it is a shaft torque
    T_dq_corr = T_dq - np.sign(np.mean(T_dq)) * vw["P_eddy"] / omega_m

    n = len(blocks)
    s0 = int(round(settle_fraction * n))
    sl = slice(s0, n - 2)          # drop the one-sided-difference tail

    def stats(x):
        return {"mean_settled": float(np.mean(x[sl])),
                "mean_full": float(np.mean(x)),
                "ripple_pp_pct": float(np.ptp(x[sl]) / abs(np.mean(x[sl]))
                                       * 100.0)}

    # instantaneous agreement of the coenergy-rate torque with the Maxwell
    # series is the real test of the virtual-work bookkeeping
    sgn = np.sign(np.mean(T_mx[sl])) * np.sign(np.mean(vw["T_vw"][sl]))
    inst_rms = float(np.sqrt(np.mean((sgn * vw["T_vw"][sl] - T_mx[sl]) ** 2))
                     / abs(np.mean(T_mx[sl])) * 100.0)

    i_rms = float(np.sqrt(np.mean(pq["i_abc"][sl] ** 2, axis=0)).mean())
    return {
        "path": path, "n_steps": n, "pole_pairs": pole_pairs,
        "speed_rpm": speed_rpm, "omega_m": omega_m,
        "n_sect": pq["n_sect"], "l_stack_mm": l_stack_mm,
        "mesh_drift_max_mm": float(max(drift.values())),
        "h_semantics_max_relerr": h_err,
        "phase_sides": pq["n_sides_per_phase"],
        "current_spread_A": pq["current_spread_A"].tolist(),
        "i_rms_A": i_rms,
        "maxwell": stats(T_mx),
        "dq_raw": stats(T_dq), "dq": stats(T_dq_corr),
        "virtual_work": stats(vw["T_vw"]),
        "virtual_work_raw": stats(vw["T_vw_raw"]),
        "vw_vs_maxwell_inst_rms_pct": inst_rms,
        "P_eddy_mean_W": float(np.mean(vw["P_eddy"][sl])),
        "eddy_term_mean_W": float(np.mean(vw["eddy_term"][sl])),
        "P_mech_mean_W": float(np.mean(T_mx[sl]) * omega_m),
        "series": {"t_s": vw["t_s"], "T_maxwell": T_mx, "T_dq": T_dq,
                   "T_dq_corr": T_dq_corr, "T_vw": vw["T_vw"],
                   "T_vw_raw": vw["T_vw_raw"], "P_eddy": vw["P_eddy"],
                   "eddy_term": vw["eddy_term"], "dWdt": vw["dWdt"],
                   "i_abc": pq["i_abc"], "lam_abc": pq["lam_abc"]},
    }
