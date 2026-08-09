# -*- coding: utf-8 -*-
"""보정 형태 비교 연구 (calibration-form study).

동일한 자체 TS-FEA 예산에서 다음 형태를 비교하고, 전체 dq 평면과
실제 운전영역(효율맵 beta 궤적 기반) 양쪽에서 오차를 산출한다.

  1. ``kcc``       : k_cc(w, I) 2변수 다항식            (R1 기준선)
  2. ``tps3d``     : 비분리 3-D TPS RBF
  3. ``scalar``    : 분리 스칼라      AF = f(w)*kappa(I,b)
  4. ``exponent``  : 분리 멱지수      AF = f(w)*kappa(I,b)^p(w)   (채택)
  5. ``perspeed``  : 속도별 독립 저차 적합 (FEAfix 방식)

결과는 JSON으로 보존한다 (``run_form_study(..., out_json=...)``).
"""
from __future__ import annotations

import contextlib
import io
import json
import os
from typing import Dict, Optional

import numpy as np

__all__ = ["operating_beta_band", "region_mask", "run_form_study"]

# Ref 36 = n_base 24 + 4x3. AF 밴드 해제로 앵커 후보가 24가 되었다.
_DEFAULT_BUDGET = {"Ref": 36, "HalfSC": 27, "SC": 27}
_DEFAULT_NS_OWN = {"Ref": 4, "HalfSC": 3, "SC": 3}
_PLACEMENTS = ("random", "structured")
_EFFMAP = (r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET"
           r"\efficiency_map_results.mat")


# ── 운전영역 ──────────────────────────────────────────────────────────
def operating_beta_band(effmap_mat: str = _EFFMAP) -> Dict[float, tuple]:
    """효율맵(MTPA/FW 해)에서 속도별 실제 사용 beta 범위를 추출한다."""
    try:
        import scipy.io as sio
        m = sio.loadmat(effmap_mat, squeeze_me=True)
        spd = np.asarray(m["speed_rpm"], float).ravel()
        bet = np.asarray(m["beta_deg"], float)
    except Exception:
        return {}
    # beta 배열에서 속도에 대응하는 축을 찾아 맨 앞으로 옮긴다
    ax = next((i for i, n in enumerate(bet.shape) if n == spd.size), None)
    if ax is None:
        return {}
    bet = np.moveaxis(bet, ax, 0)

    band: Dict[float, tuple] = {}
    for i, s in enumerate(spd):
        b = np.asarray(bet[i], float).ravel()
        b = b[np.isfinite(b)]
        if b.size:
            key = float(np.round(s))
            lo, hi = float(b.min()), float(b.max())
            if key in band:
                lo = min(lo, band[key][0])
                hi = max(hi, band[key][1])
            band[key] = (lo, hi)
    return band


def region_mask(dataset, band: Dict[float, tuple],
                margin_deg: float = 12.0) -> np.ndarray:
    """표본이 해당 속도의 운전 beta 범위(+-margin) 안인지."""
    if not band:
        return np.ones(len(dataset.af_arr), bool)
    keys = np.array(sorted(band))
    spd_rpm = np.asarray(dataset.speeds_k, float) * 1000.0
    out = np.zeros(spd_rpm.size, bool)
    for i, (s, b) in enumerate(zip(spd_rpm, dataset.phase_arr)):
        lo, hi = band[float(keys[np.argmin(np.abs(keys - s))])]
        out[i] = (lo - margin_deg) <= float(b) <= (hi + margin_deg)
    return out


# ── 오차 ──────────────────────────────────────────────────────────────
def _err(ds, pred_af, mask=None):
    pred = ds.h_ac_arr * np.asarray(pred_af, float)
    e = np.abs((pred - ds.f_ac_arr) / (ds.f_ac_arr + 1e-12) * 100.0)
    w = ds.f_ac_arr
    if mask is not None:
        e, w = e[mask], w[mask]
    if e.size == 0:
        return float("nan"), float("nan")
    return (float(np.sum(w * e) / np.sum(w)), float(np.mean(e)))


# ── 형태별 적합기 ─────────────────────────────────────────────────────
def _fit_kcc(ds, idx):
    """AF ~ 1 + c1 w + c2 w^2 + c3 I + c4 w I  (R1 의 k_cc 형태)."""
    w, I, y = ds.speeds_k[idx], ds.irms_arr[idx], ds.af_arr[idx]
    A = np.column_stack([np.ones_like(w), w, w ** 2, I, w * I])
    c = np.linalg.lstsq(A, y, rcond=None)[0]

    def pred(sp, ii, ph):
        W = np.asarray(sp, float) / 1000.0
        II = np.asarray(ii, float)
        return c[0] + c[1] * W + c[2] * W ** 2 + c[3] * II + c[4] * W * II
    return pred


def _fit_tps3d(ds, idx, lam: float = 1e-6):
    """예산 부분집합 위의 비분리 3-D TPS RBF."""
    S, I, P = ds.speeds_k[idx], ds.irms_arr[idx], ds.phase_arr[idx]
    y = ds.af_arr[idx]
    LS_S, LS_I, LS_P = ds.LS_S, ds.LS_I, ds.LS_P
    n = len(idx)
    Phi = np.zeros((n, n))
    for j in range(n):
        r2 = ((S - S[j]) ** 2 / LS_S ** 2 + (I - I[j]) ** 2 / LS_I ** 2
              + (P - P[j]) ** 2 / LS_P ** 2)
        Phi[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
    w = np.linalg.solve(Phi + lam * np.eye(n), y)

    def pred(sp, ii, ph):
        Sv = np.asarray(sp, float).ravel()[:, None] / 1000.0
        Iv = np.asarray(ii, float).ravel()[:, None]
        Pv = np.asarray(ph, float).ravel()[:, None]
        r2 = ((Sv - S) ** 2 / LS_S ** 2 + (Iv - I) ** 2 / LS_I ** 2
              + (Pv - P) ** 2 / LS_P ** 2)
        return (r2 * np.log(np.sqrt(r2) + 1e-12)) @ w
    return pred


def _fit_perspeed(ds, idx, deg: int = 2):
    """속도마다 (I, beta) 저차 다항식을 독립 적합 (FEAfix 방식)."""
    models = {}
    for s in sorted(set(np.round(ds.speeds_k, 3))):
        sel = [j for j in idx if abs(ds.speeds_k[j] - s) < 0.1]
        if len(sel) < 3:
            continue
        I, B, y = ds.irms_arr[sel], ds.phase_arr[sel], ds.af_arr[sel]
        cols = [np.ones_like(I), I, B]
        if deg >= 2 and len(sel) >= 6:
            cols += [I ** 2, I * B, B ** 2]
        c = np.linalg.lstsq(np.column_stack(cols), y, rcond=None)[0]
        models[float(s)] = (c, len(cols))
    keys = sorted(models)

    def pred(sp, ii, ph):
        W = np.asarray(sp, float).ravel() / 1000.0
        II = np.asarray(ii, float).ravel()
        BB = np.asarray(ph, float).ravel()
        out = np.ones_like(II)
        if not keys:
            return out
        for k in range(II.size):
            s = min(keys, key=lambda t: abs(t - W[k]))
            c, nc = models[s]
            v = [1.0, II[k], BB[k]]
            if nc == 6:
                v += [II[k] ** 2, II[k] * BB[k], BB[k] ** 2]
            out[k] = float(np.dot(c, v[:nc]))
        return out
    return pred


# ── 본체 ──────────────────────────────────────────────────────────────
def run_form_study(pipeline,
                   scales=("Ref", "HalfSC", "SC"),
                   budget: Optional[Dict[str, int]] = None,
                   ns_own: Optional[Dict[str, int]] = None,
                   n_seeds: int = 10,
                   margin_deg: float = 12.0,
                   out_json: Optional[str] = None) -> dict:
    """다섯 보정 형태를 동일 예산·동일 표본점에서 비교한다.

    각 (scale, placement)에서 샘플링 계획을 한 번 세우고 그 점 집합을
    다섯 형태 전부에 그대로 적용하므로, 남는 차이는 오직 함수 형태이다.
    분리 형태의 기준 커널 점수는 ``n_base = B - n_spd * n_other`` 로
    역산되어 총 TS-FEA 사용량이 예산 ``B``와 정확히 일치한다.

    ``placement='structured'`` 는 결정론적이라 시드 평균이 없다(1회).

    Returns a JSON-serialisable dict; also writes it to ``out_json``.
    """
    from .RbfModelBuilder import RbfModelBuilder

    budget = dict(budget or _DEFAULT_BUDGET)
    ns_own = dict(ns_own or _DEFAULT_NS_OWN)
    band = operating_beta_band()
    base_speed = pipeline.cfg["base_speed"]
    forms = ["kcc", "tps3d", "scalar", "exponent", "perspeed"]

    result = {
        "meta": {
            "n_seeds": n_seeds, "budget": budget, "ns_own": ns_own,
            "margin_deg": margin_deg, "base_speed_kRPM": base_speed,
            "operating_band_deg": {str(k): list(v)
                                   for k, v in sorted(band.items())},
            "forms": forms, "placements": list(_PLACEMENTS),
            "note": "wMAE/MAE in %; every form is fitted on the *same* "
                    "point set at each (scale, placement), and n_ts_used "
                    "equals the stated budget. 'random' is averaged over "
                    "seeds, 'structured' is deterministic (single run). "
                    "'region' = operating band from the efficiency-map "
                    "beta trajectory.",
        },
        "scales": {},
    }

    for scale in scales:
        with contextlib.redirect_stdout(io.StringIO()):
            ds = pipeline.load_dataset(scale)
        mask = region_mask(ds, band, margin_deg)
        n = int(len(ds.af_arr))
        pool = int(np.sum(np.abs(ds.speeds_k - base_speed) < 0.1))
        n_other = len([s for s in sorted(set(np.round(ds.speeds_k, 3)))
                       if abs(s - base_speed) >= 0.1])
        B, ns = int(budget[scale]), int(ns_own[scale])
        n_base = max(3, min(pool, B - ns * n_other))   # 예산 역산

        fw, fm = _err(ds, np.ones(n))
        rw, rm = _err(ds, np.ones(n), mask)
        entry = {
            "n_points": n, "n_region": int(mask.sum()),
            "base_pool": pool, "n_other_speeds": n_other,
            "budget": B, "ns_own": ns, "n_base": n_base,
            "uncorrected": {"full_wmae": fw, "full_mae": fm,
                            "region_wmae": rw, "region_mae": rm},
            "placement": {},
        }

        for placement in _PLACEMENTS:
            seeds = range(n_seeds) if placement == "random" else [0]
            acc = {f: {"full_wmae": [], "full_mae": [],
                       "region_wmae": [], "region_mae": []} for f in forms}
            n_used, spans = [], {}

            for seed in seeds:
                plan = RbfModelBuilder.plan_sampling_indices(
                    ds, n_base=n_base, n_spd=ns, base_speed=base_speed,
                    placement=placement, seed=seed)
                idx = plan["all"]
                n_used.append(int(idx.size))
                if plan["log_kappa_span"]:
                    spans = {str(k): v
                             for k, v in plan["log_kappa_span"].items()}

                preds = {}
                for nm, fn in (("kcc", _fit_kcc), ("tps3d", _fit_tps3d),
                               ("perspeed", _fit_perspeed)):
                    try:
                        preds[nm] = fn(ds, idx)(ds.speeds_k * 1000.0,
                                                ds.irms_arr, ds.phase_arr)
                    except Exception:
                        pass
                for expo, nm in ((False, "scalar"), (True, "exponent")):
                    try:
                        with contextlib.redirect_stdout(io.StringIO()):
                            m = RbfModelBuilder.build_separable_rbf(
                                ds, base_speed=base_speed,
                                exponent=expo, index_plan=plan)
                        preds[nm] = m.predict(ds.speeds_k * 1000.0,
                                              ds.irms_arr, ds.phase_arr)
                    except Exception:
                        pass

                for nm, p in preds.items():
                    a, b = _err(ds, p)
                    c, d = _err(ds, p, mask)
                    for k, v in zip(("full_wmae", "full_mae",
                                     "region_wmae", "region_mae"),
                                    (a, b, c, d)):
                        acc[nm][k].append(
                            min(v, 1e3) if np.isfinite(v) else np.nan)

            blk = {"n_ts_used": int(np.mean(n_used)) if n_used else 0,
                   "n_runs": len(list(seeds)),
                   "log_kappa_span": spans, "forms": {}}
            for f, d in acc.items():
                blk["forms"][f] = ({k: float(np.nanmean(v))
                                    for k, v in d.items()}
                                   if d["full_wmae"] else None)
            entry["placement"][placement] = blk

        result["scales"][scale] = entry

    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
    return result
