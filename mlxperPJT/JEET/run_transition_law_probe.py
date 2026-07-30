# -*- coding: utf-8 -*-
"""상용 전환 조정의 치수 규약 판별 1단계 — 감쇠비 S의 collapse 변수 탐색.

S(f; model) = mcad_prox / P24_cuboid6(비캡 m² 가중, 전면적 <B^2>) 를
3모델(h_c 3.711/5.5665/7.422 mm) x 4속도에서 뽑고, 후보 축
  x1 = f_e/f_t(h)  (f_t ∝ h^-2, 우리 물리 캡)
  x2 = f_e         (치수 무관 고정 전환)
  x3 = f_e/f_t(w)  (폭 기준)
각각에 대해 log S ~ log x 단일 곡선 적합 R^2 로 collapse 정도를 채점한다.
주의: P24 열은 20°C σ 기준(meshb JSON) — 상수 1.236 편의는 축 판별에 무영향.

산출: map_exports/e10/transition_law_probe.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402

E10 = os.path.join(HERE, "map_exports", "e10")
SRC = {
    "Ref": os.path.join(E10, "Ref", "meshb_hybrid_losses_Ref.json"),
    "HalfSC": os.path.join(E10, "HalfSC",
                           "meshb_hybrid_losses_HalfSC_campaign.json"),
    "SC": os.path.join(E10, "SC", "meshb_hybrid_losses_SC.json"),
}
DIMS = {"Ref": (3.711e-3, 1.686e-3), "HalfSC": (5.5665e-3, 2.529e-3),
        "SC": (7.422e-3, 3.372e-3)}
POLE_PAIRS = 4
SIGMA80 = (1.0 / 1.724e-8) / (1.0 + 3.93e-3 * 60.0)
MU0 = 4e-7 * np.pi
OUT = os.path.join(E10, "transition_law_probe.json")


def f_t(dim_m):
    return 1.0 / (np.pi * MU0 * SIGMA80 * dim_m ** 2)


def main() -> int:
    rows = []
    for model, path in SRC.items():
        if not os.path.exists(path):
            print(f"[{model}] JSON 없음: {path}")
            continue
        d = json.load(open(path, encoding="utf-8"))
        h, w = DIMS[model]
        by_spd = {}
        for r in d["rows"]:
            if (r["current_A"] > 1 and r.get("mcad_prox_W")
                    and r.get("P24_cuboid6_W")):
                by_spd.setdefault(int(r["speed_rpm"]), []).append(
                    r["mcad_prox_W"] / r["P24_cuboid6_W"])
        for spd in sorted(by_spd):
            v = np.array(by_spd[spd])
            f_e = spd * POLE_PAIRS / 60.0
            rows.append({
                "model": model, "speed_rpm": spd, "f_e": round(f_e, 1),
                "S_mean": round(float(v.mean()), 4),
                "S_std": round(float(v.std()), 4), "n": len(v),
                "x_fth": round(f_e / f_t(h), 3),
                "x_f": round(f_e, 1),
                "x_ftw": round(f_e / f_t(w), 3),
            })

    print(f"{'model':>7} {'rpm':>6} {'f_e':>7} {'S':>7} {'±':>6} "
          f"{'f/ft(h)':>8} {'f/ft(w)':>8}")
    for r in rows:
        print(f"{r['model']:>7} {r['speed_rpm']:>6} {r['f_e']:>7.0f} "
              f"{r['S_mean']:>7.3f} {r['S_std']:>6.3f} {r['x_fth']:>8.2f} "
              f"{r['x_ftw']:>8.2f}")

    # collapse 채점: log S ~ 2차 다항(log x) 단일 곡선의 R^2
    scores = {}
    ls = np.log([r["S_mean"] for r in rows])
    for cand in ("x_fth", "x_f", "x_ftw"):
        lx = np.log([r[cand] for r in rows])
        A = np.vstack([np.ones_like(lx), lx, lx ** 2]).T
        coef, *_ = np.linalg.lstsq(A, ls, rcond=None)
        resid = ls - A @ coef
        r2 = 1.0 - resid.var() / ls.var()
        scores[cand] = round(float(r2), 4)
    print("\ncollapse R^2 (높을수록 그 변수 규약):", scores)

    json.dump({"rows": rows, "collapse_r2": scores,
               "_meta": {"S": "mcad_prox / P24_cuboid6 (uncapped m^2, "
                              "full-area, 20C sigma basis)"}},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
