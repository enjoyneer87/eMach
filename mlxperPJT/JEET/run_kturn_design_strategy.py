# -*- coding: utf-8 -*-
"""Kturn 설계단계 상사 전략 채점 — Tier 0/1/2 실측 (신규 TS-FEA 0점).

§12.11 1차 분석의 후속. 설계단계 의사결정 흐름의 각 계층을 기존 4t/8t 전수
데이터(각 96 유효점)로 채점한다:

  Tier 0 (TS-FEA 0점/턴) — MS 재사용(MMF 재색인) + 사상 AF 제로샷.
      절대 오차는 11~16%지만 설계단계 용도는 *변형체 간 비교*이므로,
      per-unit 전류 정렬 격자에서 {4t, 6t, 8t} 손실 순위 재현율을 채점.
  Tier 1 (+3점/턴, k_h<=1 한정) — 16k κ-스팬 3점 재앵커를 **대역 한정**
      적용(16k만 보정, 저속은 제로샷 유지 — §12.11의 전대역 일괄 역효과 교정).
  Tier 2 (자체 커널) — (a) 수렴 무릎 재확인: n_base 스윕(결정론 greedy
      maximin, 자체 3점/속도 κ-스팬 (f,p)) → 6t의 무릎 20~24 가 턴 축에서
      유지되는지. (b) 효율 플랜 채점: plan27 = 자체 24@16k + 3@8k + 저속
      (f,p) donor 전달 / plan24(8t) = 8k 까지 전달(전 저속 사상권 내).

적합기는 논문 채택형(멱지수 분리형)의 그리드-속도 판: κ = 16k 자체점 TPS
(f=p=1 앵커), 비기준 속도는 (f,p) 로그 회귀 — 길이 스케일은 AcLossDataset
규약(std)과 동일.

실행:  python run_kturn_design_strategy.py
산출:  map_exports/e10/kturn/kturn_design_strategy.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import numpy as np                                    # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline   # noqa: E402

from run_kturn_af_analysis import DIMS, H6, load_pairs  # noqa: E402

OUT = os.path.join(HERE, "map_exports", "e10", "kturn",
                   "kturn_design_strategy.json")
SPEEDS = (2.0, 4.0, 8.0, 16.0)


# ──────────────────────────────────────────────────────────────────────
# 공통: 배열 추출 / 지표
# ──────────────────────────────────────────────────────────────────────

def arrays(turn: int):
    rows, _, _ = load_pairs(turn)
    v = [r for r in rows
         if r["irms"] > 1.0 and r["hyb_kW"] > 0 and r["fea_kW"] > 0]
    return {k: np.array([r[k] for r in v]) for k in
            ("speed_k", "irms", "beta", "hyb_kW", "fea_kW")}


def wmae(fea, pred, mask=None):
    m = np.ones(len(fea), bool) if mask is None else mask
    e = np.abs(pred[m] - fea[m]) / fea[m] * 100.0
    return float(np.sum(fea[m] * e) / np.sum(fea[m]))


# ──────────────────────────────────────────────────────────────────────
# 멱지수 분리형(그리드-속도 판) 적합기
# ──────────────────────────────────────────────────────────────────────

def make_kappa(i_pts, p_pts, af_pts, ls_i, ls_p, lam=1e-6):
    """16k 자체점 TPS 보간면 κ(I,β) (f=p=1 앵커)."""
    n = len(i_pts)
    r2 = ((i_pts[:, None] - i_pts[None, :]) ** 2 / ls_i ** 2
          + (p_pts[:, None] - p_pts[None, :]) ** 2 / ls_p ** 2)
    K = r2 * np.log(np.sqrt(r2) + 1e-12)
    w = np.linalg.solve(K + lam * np.eye(n), af_pts)

    def kappa(I, P):
        I, P = np.asarray(I, float), np.asarray(P, float)
        r2q = ((I[:, None] - i_pts) ** 2 / ls_i ** 2
               + (P[:, None] - p_pts) ** 2 / ls_p ** 2)
        return np.clip((r2q * np.log(np.sqrt(r2q) + 1e-12)) @ w, 1e-3, None)
    return kappa


def fp_regress(kap_vals, af_vals):
    x = np.log(np.clip(kap_vals, 1e-3, None))
    y = np.log(np.clip(af_vals, 1e-3, None))
    p, logf = np.polyfit(x, y, 1)
    return float(np.exp(logf)), float(p)


def greedy_maximin(In, Pn, n_sel):
    """정규화 (I,β) 평면 farthest-point 순회 — 결정론 maximin 커버."""
    pts = np.stack([In, Pn], 1)
    c = pts.mean(0)
    sel = [int(np.argmax(((pts - c) ** 2).sum(1)))]
    d = ((pts - pts[sel[0]]) ** 2).sum(1)
    while len(sel) < min(n_sel, len(pts)):
        k = int(np.argmax(d))
        sel.append(k)
        d = np.minimum(d, ((pts - pts[k]) ** 2).sum(1))
    return np.array(sel)


def kspan_pick(vals, n_s):
    """식 (eq:kspan): 정렬 랭크 등분위 n_s 점 (양 극단 포함)."""
    order = np.argsort(vals)
    N = len(order)
    ranks = [int(round(m * (N - 1) / (n_s - 1))) for m in range(n_s)]
    return order[sorted(set(ranks))]


def fit_grid_model(a, n_base, spd_fp):
    """자체 κ(n_base, maximin) + 속도별 (f,p) 테이블 → AF 예측 배열.

    spd_fp: {speed: ("own3", None) | ("donor", donor_af_fn) | ("anchor", None)}
      own3  — 자체 3점 κ-스팬 실측 AF 회귀 (TS-FEA 3점 소비)
      donor — 사상 donor AF 를 κ-스팬 6 프로브로 회귀 (비용 0)
    반환: (af_pred, own_cost)
    """
    m16 = a["speed_k"] == 16.0
    ls_i, ls_p = a["irms"].std(), a["beta"].std()
    i16, p16, af16 = (a["irms"][m16], a["beta"][m16],
                      (a["fea_kW"] / a["hyb_kW"])[m16])
    sel = greedy_maximin(i16 / ls_i, p16 / ls_p, n_base)
    kappa = make_kappa(i16[sel], p16[sel], af16[sel], ls_i, ls_p)
    own_cost = len(sel)

    af_pred = np.empty(len(a["speed_k"]))
    af_true = a["fea_kW"] / a["hyb_kW"]
    for s, (mode, donor_fn) in spd_fp.items():
        m = a["speed_k"] == s
        kap = kappa(a["irms"][m], a["beta"][m])
        if mode == "anchor":
            f_s, p_s = 1.0, 1.0
        elif mode == "own3":
            pick = kspan_pick(kap, 3)
            f_s, p_s = fp_regress(kap[pick], af_true[m][pick])
            own_cost += len(pick)
        else:  # donor
            pick = kspan_pick(kap, 6)
            af_probe = donor_fn(np.full(pick.shape, s),
                                a["irms"][m][pick], a["beta"][m][pick])
            f_s, p_s = fp_regress(kap[pick], af_probe)
        af_pred[m] = f_s * kap ** p_s
    return af_pred, own_cost


# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    pl = AcLossPipeline()
    m_ref = pl.build_model("Ref")
    ds_ref = pl.load_dataset("Ref")
    res = {}

    def donor_fn_for(turn):
        k_h = DIMS[turn][0] / H6

        def fn(spd_k, irms, beta):
            return m_ref.predict(np.asarray(spd_k) * k_h ** 2 * 1000.0,
                                 np.asarray(irms) * (turn / 6.0), beta)
        return fn, k_h

    A = {t: arrays(t) for t in (4, 8)}
    ZS = {}
    for t in (4, 8):
        fn, k_h = donor_fn_for(t)
        ZS[t] = fn(A[t]["speed_k"], A[t]["irms"], A[t]["beta"])

    # ── Tier 0b: 변형체 손실 순위 재현율 (per-unit 전류 정렬 격자) ────
    lv_frac = (0.25, 0.5, 0.75, 1.0)
    imax = {4: 690.0, 6: 460.0, 8: 345.0}
    ref_true, ref_pred = {}, {}
    af_ref_prod = m_ref.predict(ds_ref.speeds_k * 1000.0,
                                ds_ref.irms_arr, ds_ref.phase_arr)
    for i in range(len(ds_ref)):
        key = (float(ds_ref.speeds_k[i]),
               round(float(ds_ref.irms_arr[i]) / imax[6], 3),
               float(ds_ref.phase_arr[i]))
        ref_true[key] = float(ds_ref.f_ac_arr[i])
        ref_pred[key] = float(ds_ref.h_ac_arr[i] * af_ref_prod[i])
    n_cell = n_full = n_pair_ok = n_pair = 0
    delta_err = []
    for s in SPEEDS:
        for fr in lv_frac:
            for b in (0., 18., 36., 54., 72., 90.):
                tru, prd = {}, {}
                k6 = (s, round(fr, 3), b)
                if k6 in ref_true:
                    tru[6], prd[6] = ref_true[k6], ref_pred[k6]
                for t in (4, 8):
                    a = A[t]
                    m = ((a["speed_k"] == s) & (a["beta"] == b)
                         & (np.abs(a["irms"] / imax[t] - fr) < 0.01))
                    if m.any():
                        j = int(np.where(m)[0][0])
                        tru[t] = float(a["fea_kW"][j])
                        prd[t] = float(a["hyb_kW"][j] * ZS[t][j])
                if len(tru) < 2:
                    continue
                n_cell += 1
                ks = sorted(tru)
                ok_all = True
                for x in range(len(ks)):
                    for y in range(x + 1, len(ks)):
                        n_pair += 1
                        same = ((tru[ks[x]] - tru[ks[y]])
                                * (prd[ks[x]] - prd[ks[y]]) > 0)
                        n_pair_ok += int(same)
                        ok_all &= same
                        dt = tru[ks[x]] / tru[ks[y]] - 1.0
                        dp = prd[ks[x]] / prd[ks[y]] - 1.0
                        delta_err.append(abs(dp - dt) / max(abs(dt), 1e-9))
                n_full += int(ok_all)
    res["tier0_ranking"] = {
        "n_cells": n_cell,
        "full_order_ok_pct": round(100.0 * n_full / n_cell, 1),
        "pairwise_ok_pct": round(100.0 * n_pair_ok / n_pair, 1),
        "rel_delta_err_median_pct": round(
            100.0 * float(np.median(delta_err)), 1),
        "rel_delta_err_p90_pct": round(
            100.0 * float(np.percentile(delta_err, 90)), 1),
    }

    # ── Tier 1: 대역 한정 +3 재앵커 (16k 만 보정, 저속 zs 유지) ───────
    for t in (4, 8):
        a, af_zs = A[t], ZS[t]
        af_true = a["fea_kW"] / a["hyb_kW"]
        hi = a["speed_k"] == 16.0
        idx = np.where(hi)[0]
        pick = idx[kspan_pick(af_zs[idx], 3)]
        f_c, p_c = fp_regress(af_zs[pick], af_true[pick])
        af_t1 = np.where(hi, f_c * np.clip(af_zs, 1e-3, None) ** p_c, af_zs)
        res.setdefault(f"kturn{t}", {})["tier1_band_limited_plus3"] = {
            "f_c": round(f_c, 3), "p_c": round(p_c, 3),
            "wmae_all_pct": round(wmae(a["fea_kW"], a["hyb_kW"] * af_t1), 2),
            "wmae_16k_pct": round(
                wmae(a["fea_kW"], a["hyb_kW"] * af_t1, hi), 2),
            "own_pts": 3,
        }

    # ── Tier 2a: 수렴 무릎 (n_base 스윕, 전 저속 own3) ────────────────
    for t in (4, 8):
        a = A[t]
        curve = {}
        for nb in (6, 10, 14, 18, 22, 24):
            spd_fp = {16.0: ("anchor", None)}
            for s in (2.0, 4.0, 8.0):
                spd_fp[s] = ("own3", None)
            af_p, cost = fit_grid_model(a, nb, spd_fp)
            curve[nb] = {"wmae_pct": round(
                wmae(a["fea_kW"], a["hyb_kW"] * af_p), 2), "own_pts": cost}
        res[f"kturn{t}"]["tier2_knee_curve"] = curve

    # ── Tier 2b: 효율 플랜 (donor 저속 전달) ──────────────────────────
    for t in (4, 8):
        a = A[t]
        fn, k_h = donor_fn_for(t)
        plans = {"plan27_own24_own8k_donor_low": {
            16.0: ("anchor", None), 8.0: ("own3", None),
            4.0: ("donor", fn), 2.0: ("donor", fn)}}
        if k_h <= 1.0:            # 전 저속이 사상권 내 → 8k 도 전달 가능
            plans["plan24_own24_donor_all_low"] = {
                16.0: ("anchor", None), 8.0: ("donor", fn),
                4.0: ("donor", fn), 2.0: ("donor", fn)}
        for name, spd_fp in plans.items():
            af_p, cost = fit_grid_model(a, 24, spd_fp)
            per = {f"{s:g}k": round(wmae(a["fea_kW"], a["hyb_kW"] * af_p,
                                         a["speed_k"] == s), 2)
                   for s in SPEEDS}
            res[f"kturn{t}"][name] = {
                "own_pts": cost,
                "wmae_all_pct": round(
                    wmae(a["fea_kW"], a["hyb_kW"] * af_p), 2),
                "by_speed": per}

    # ── 출력 ──────────────────────────────────────────────────────────
    r0 = res["tier0_ranking"]
    print(f"[Tier0 스크리닝] 셀 {r0['n_cells']}: 전순위 재현 "
          f"{r0['full_order_ok_pct']}%, 쌍별 {r0['pairwise_ok_pct']}%, "
          f"상대격차 오차 중앙 {r0['rel_delta_err_median_pct']}% "
          f"/ p90 {r0['rel_delta_err_p90_pct']}%")
    for t in (4, 8):
        e = res[f"kturn{t}"]
        t1 = e["tier1_band_limited_plus3"]
        print(f"\n[kturn{t}] Tier1 대역한정 +3: 전체 {t1['wmae_all_pct']}% "
              f"(16k {t1['wmae_16k_pct']}%)")
        print("  Tier2a 무릎:", {k: v["wmae_pct"]
                                for k, v in e["tier2_knee_curve"].items()})
        for name in ("plan27_own24_own8k_donor_low",
                     "plan24_own24_donor_all_low"):
            if name in e:
                p = e[name]
                print(f"  Tier2b {name}: own {p['own_pts']}점 → "
                      f"{p['wmae_all_pct']}%  {p['by_speed']}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
