# -*- coding: utf-8 -*-
"""e4a 전체 레시피 검증 — §4 워크플로를 새 설계에 그대로: 12(κ)+3+3 = 18점.

배치 A+B 데이터(3속도 x 전류 4티어 x β6 + 기준 held-out 링 6점):
  1) κ: 기준 속도(14,850) maximin 12점 TPS  [D(n) 감시가 고른 예산]
  2) 저속(3,712/7,425)마다 κ-스팬 3점: 기준 κ를 그 속도 후보에 평가해
     log κ 랭크 {argmin, 중위, argmax} — 결정론, 해석 전 확정
  3) (f_s, p_s): 3점 로그공간 회귀 (기준 속도는 f=1, p=1 앵커)
  4) 채점: 사용 18점을 제외한 전 TS 쌍(60점)의 와트 가중 wMAE
비교선: 전량 사용 상한(κ 24점 + 저속 전점 회귀).

산출: map_exports/e10/e4a_full_recipe.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from scipy.interpolate import RBFInterpolator               # noqa: E402

SRC = r"D:\KangDH\Thesis\e4a\newfam_results\kturn4\JEET_ACLoss_kturn4_Map_Summary.json"
OUT = os.path.join(HERE, "map_exports", "e10", "e4a_full_recipe.json")
BASE_RPM, I_MAX, HELD_I = 14850, 250.0, 156.25


def maximin_order(X):
    picked = [int(np.argmin(((X - X.mean(0)) ** 2).sum(1)))]
    dist = np.sqrt(((X - X[picked[0]]) ** 2).sum(1))
    for _ in range(len(X) - 1):
        nxt = int(np.argmax(dist))
        picked.append(nxt)
        dist = np.minimum(dist, np.sqrt(((X - X[nxt]) ** 2).sum(1)))
    return np.array(picked)


def main() -> int:
    d = json.load(open(SRC, encoding="utf-8"))
    hyb = {(r["speed"], r["current"], r["phase"]): r["hybrid_total_kW"]
           for r in d["records"] if r["proximity_model"] == 1}
    ts = {(r["speed"], r["current"], r["phase"]): r["ts_ac_active_only_kW"]
          for r in d["records"] if r["proximity_model"] == 3}
    keys = sorted(set(hyb) & set(ts))
    spd = np.array([k[0] for k in keys], float)
    cur = np.array([k[1] for k in keys], float)
    ph = np.array([k[2] for k in keys], float)
    h = np.array([hyb[k] for k in keys])
    f = np.array([ts[k] for k in keys])
    af = f / h
    xy = np.column_stack([cur / I_MAX, ph / 90.0])
    print(f"TS 쌍 {len(keys)}개 (속도 {sorted(set(spd.astype(int)))})")

    # 1) 기준 κ: held-out 링 제외 24 후보의 maximin 앞 12점
    base_m = (spd == BASE_RPM) & (np.abs(cur - HELD_I) > 1.0)
    base_idx = np.where(base_m)[0]
    order = base_idx[maximin_order(xy[base_idx])]
    used = {"base": order[:12].tolist()}
    kap = RBFInterpolator(xy[used["base"]], af[used["base"]],
                          kernel="thin_plate_spline")

    # 2)+3) 저속 κ-스팬 3점 + (f,p) 회귀
    fp = {BASE_RPM: (1.0, 1.0)}
    for s in sorted(set(spd.astype(int))):
        if s == BASE_RPM:
            continue
        cand = np.where(spd == s)[0]
        kv = np.log(np.clip(kap(xy[cand]), 1e-6, None))
        rk = np.argsort(kv)
        picks = cand[[rk[0], rk[len(rk) // 2], rk[-1]]]
        used[str(s)] = picks.tolist()
        y = np.log(af[picks])
        x = kv[[rk[0], rk[len(rk) // 2], rk[-1]]]
        A = np.vstack([np.ones(3), x]).T
        (lf, p_s), *_ = np.linalg.lstsq(A, y, rcond=None)
        fp[s] = (float(np.exp(lf)), float(p_s))
        print(f"  {s:>5d} rpm: κ-스팬 {len(picks)}점, f={fp[s][0]:.3f}, "
              f"p={fp[s][1]:.3f}")

    used_all = set(used["base"])
    for s in fp:
        if s != BASE_RPM:
            used_all |= set(used[str(s)])
    print(f"사용 표본 총 {len(used_all)}점 (12+3+3)")

    # 4) 채점
    kv_all = np.clip(kap(xy), 1e-6, None)
    af_pred = np.array([fp[int(s)][0] * kv_all[i] ** fp[int(s)][1]
                        for i, s in enumerate(spd)])
    pred = af_pred * h
    err = np.abs(pred - f) / f * 100.0
    res = {"n_used": len(used_all)}
    hold = np.array([i not in used_all for i in range(len(keys))])
    for tag, m in (("heldout_all", hold),
                   ("full_map", np.ones(len(keys), bool))):
        wmae = float(np.sum(f[m] * err[m]) / np.sum(f[m]))
        res[f"wmae_{tag}_pct"] = round(wmae, 2)
    for s in sorted(set(spd.astype(int))):
        m = hold & (spd == s)
        res[f"wmae_held_{s}"] = round(
            float(np.sum(f[m] * err[m]) / np.sum(f[m])), 2)
    unc = np.abs(h - f) / f * 100.0
    res["wmae_uncorrected_pct"] = round(
        float(np.sum(f * unc) / np.sum(f)), 2)

    # 상한: 전량 사용
    kap2 = RBFInterpolator(xy[base_idx], af[base_idx],
                           kernel="thin_plate_spline")
    kv2 = np.clip(kap2(xy), 1e-6, None)
    fp2 = {BASE_RPM: (1.0, 1.0)}
    for s in sorted(set(spd.astype(int))):
        if s == BASE_RPM:
            continue
        cand = np.where(spd == s)[0]
        A = np.vstack([np.ones(len(cand)), np.log(kv2[cand])]).T
        (lf, p_s), *_ = np.linalg.lstsq(A, np.log(af[cand]), rcond=None)
        fp2[s] = (float(np.exp(lf)), float(p_s))
    pred2 = np.array([fp2[int(s)][0] * kv2[i] ** fp2[int(s)][1]
                      for i, s in enumerate(spd)]) * h
    err2 = np.abs(pred2 - f) / f * 100.0
    m = (spd == BASE_RPM) & ~base_m & (np.abs(cur - HELD_I) < 1.0)
    res["wmae_fullbudget_ring_pct"] = round(
        float(np.sum(f[m] * err2[m]) / np.sum(f[m])), 2)
    res["wmae_fullbudget_map_pct"] = round(
        float(np.sum(f * err2) / np.sum(f)), 2)

    print("\n무보정:", res["wmae_uncorrected_pct"], "%")
    print(f"레시피 18점: held-out {res['wmae_heldout_all_pct']}% / "
          f"전 맵 {res['wmae_full_map_pct']}%")
    for s in sorted(set(spd.astype(int))):
        print(f"  held {s:>5d} rpm: {res[f'wmae_held_{s}']}%")
    print(f"전량 상한(72점): 전 맵 {res['wmae_fullbudget_map_pct']}%")
    json.dump({**res, "fp": {str(k): v for k, v in fp.items()},
               "used": used}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
