# -*- coding: utf-8 -*-
"""e4a 새 설계에서 §4.2 레시피 검증 — maximin 순차 + truth-free D(n) vs 실측.

배치 A 데이터(기준 속도 14,850 rpm): 적합 후보 24점(전류 4티어 x β6) +
held-out 링 6점(156.25 A — 적합에 불사용). maximin 순서로 κ(TPS)를 순차 적합해
  D(n)   = Σh|κ_n−κ_{n−2}| / Σh·κ_n   (하이브리드 가중, 진리값 불사용)
  wMAE_h = held-out 링의 와트 가중 오차 (채점 전용)
  wMAE_u = 미사용 후보의 와트 가중 오차 (자연 held-out)
를 나란히 놓아 e10의 사전값 창(18--24) 성립 여부를 판정한다.

산출: map_exports/e10/e4a_seq_validation.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from scipy.interpolate import RBFInterpolator               # noqa: E402
from jeet_acloss_rbf import RbfModelBuilder                 # noqa: E402

SRC = r"D:\KangDH\Thesis\e4a\newfam_results\kturn4\JEET_ACLoss_kturn4_Map_Summary.json"
OUT = os.path.join(HERE, "map_exports", "e10", "e4a_seq_validation.json")
I_MAX, HELD_I = 250.0, 156.25
D_TOL = 1.0


def main() -> int:
    d = json.load(open(SRC, encoding="utf-8"))
    hyb = {(r["current"], r["phase"]): r["hybrid_total_kW"]
           for r in d["records"] if r["proximity_model"] == 1}
    ts = {(r["current"], r["phase"]): r["ts_ac_active_only_kW"]
          for r in d["records"] if r["proximity_model"] == 3}
    keys = sorted(set(hyb) & set(ts))
    cur = np.array([k[0] for k in keys])
    ph = np.array([k[1] for k in keys])
    h = np.array([hyb[k] for k in keys])
    f = np.array([ts[k] for k in keys])
    af = f / h
    print(f"OP {len(keys)}개, AF 범위 {af.min():.3f}~{af.max():.3f} "
          f"(평균 {af.mean():.3f})")

    fit_m = np.abs(cur - HELD_I) > 1.0
    held_m = ~fit_m
    xy = np.column_stack([cur / I_MAX, ph / 90.0])
    fit_idx = np.where(fit_m)[0]

    # 그리디 farthest-point 순서 (RbfModelBuilder._maximin_indices 동일 알고리즘 —
    # 단 k>=len 쇼트컷이 순서를 보존하지 않아 전체 순서는 직접 계산)
    X = xy[fit_idx]
    picked = [int(np.argmin(((X - X.mean(0)) ** 2).sum(1)))]
    dist = np.sqrt(((X - X[picked[0]]) ** 2).sum(1))
    for _ in range(len(fit_idx) - 1):
        nxt = int(np.argmax(dist))
        picked.append(nxt)
        dist = np.minimum(dist, np.sqrt(((X - X[nxt]) ** 2).sum(1)))
    order = fit_idx[picked]
    print(f"적합 후보 {len(fit_idx)}점 (maximin 순서), held-out 링 "
          f"{int(held_m.sum())}점 ({HELD_I} A)")

    rows, prev = [], None
    ns = list(range(4, len(order) + 1, 2))
    for n in ns:
        sel = order[:n]
        mdl = RBFInterpolator(xy[sel], af[sel],
                              kernel="thin_plate_spline")
        pred = mdl(xy)
        if prev is None:
            D = np.nan
        else:
            D = float(np.sum(h * np.abs(pred - prev))
                      / np.sum(h * pred) * 100.0)
        prev = pred

        def wmae(mask):
            if not mask.any():
                return None
            e = np.abs(pred[mask] * h[mask] - f[mask]) / f[mask] * 100.0
            return float(np.sum(f[mask] * e) / np.sum(f[mask]))

        unused = fit_m.copy()
        unused[sel] = False
        rows.append({"n": n, "D_pct": None if np.isnan(D) else round(D, 2),
                     "wmae_held_pct": round(wmae(held_m), 2),
                     "wmae_unused_pct": (round(wmae(unused), 2)
                                         if unused.any() else None)})

    print(f"{'n':>4} {'D(n)%':>7} {'held-out%':>10} {'미사용%':>8}")
    for r in rows:
        d_s = "--" if r["D_pct"] is None else format(r["D_pct"], "7.2f")
        u_s = ("--" if r["wmae_unused_pct"] is None
               else format(r["wmae_unused_pct"], "8.2f"))
        print(f"{r['n']:>4} {d_s} {r['wmae_held_pct']:>10.2f} {u_s}")

    dv = [r["D_pct"] for r in rows]
    n_settle = None
    for i in range(1, len(rows)):
        if dv[i] is not None and dv[i] < D_TOL and \
           (i + 1 >= len(rows) or all((x or 0) < D_TOL for x in dv[i:])):
            n_settle = rows[i]["n"]
            break
    print(f"\nD(n) 최종 정착(끝까지 <{D_TOL}%) 시작점: n = {n_settle}")
    json.dump({"rows": rows, "af_range": [round(float(af.min()), 3),
                                          round(float(af.max()), 3)],
               "n_settle": n_settle,
               "_meta": {"machine": "e4a 48s8p 4cond", "base_rpm": 14850,
                         "held_ring_A": HELD_I}},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
