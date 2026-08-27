# -*- coding: utf-8 -*-
r"""수렴 무릎 --- 6t(k_r 축) vs 턴 축(4t/8t), 같은 프로토콜로 (2026-08-27).

12.12 는 "턴 축 무릎은 6t(12~20 포화)보다 오른쪽" 이라 적었으나, 그 6t
무릎은 Fig B.2 의 **다중 시드** 곡선이고 턴 축은 결정론 maximin 이라
프로토콜이 달랐다.  여기서는 run_kturn_design_strategy 의 fit_grid_model
을 6t(Ref/HalfSC/SC)에 그대로 먹여 조건을 통일한다.

결과: 다섯 곡선이 같은 모양 --- 6t 도 전량(24)에서야 바닥. 판정 철회,
턴 축 페널티는 무릎 위치가 아니라 정체 구간 높이(1.2~2배)다.

실행:  python run_kturn_knee_6t_compare.py
산출:  map_exports/e10/kturn/knee_6t_compare.json
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
os.environ.setdefault("JEET_DATA_ROOT",
                      os.path.join(HERE, "map_exports", "e10"))

import numpy as np                                          # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline         # noqa: E402
from run_kturn_design_strategy import fit_grid_model, wmae  # noqa: E402

OUT = os.path.join(HERE, "map_exports", "e10", "kturn",
                   "knee_6t_compare.json")
N_BASE = [6, 10, 14, 18, 22, 24]
SPEEDS = (2.0, 4.0, 8.0, 16.0)


def arrays_6t(pl, scale):
    """kturn 의 arrays() 와 같은 키·같은 필터로 6t 데이터를 낸다."""
    ds = pl.load_dataset(scale)
    a = {"speed_k": np.asarray(ds.speeds_k, float),
         "irms": np.asarray(ds.irms_arr, float),
         "beta": np.asarray(ds.phase_arr, float),
         "hyb_kW": np.asarray(ds.h_ac_arr, float),
         "fea_kW": np.asarray(ds.f_ac_arr, float)}
    keep = (a["irms"] > 1.0) & (a["hyb_kW"] > 0) & (a["fea_kW"] > 0)
    return {k: v[keep] for k, v in a.items()}


def main() -> int:
    pl = AcLossPipeline()
    out = {}
    for scale in ("Ref", "HalfSC", "SC"):
        a = arrays_6t(pl, scale)
        pool = int((a["speed_k"] == 16.0).sum())
        curve = {}
        for nb in N_BASE:
            if nb > pool:
                continue
            spd_fp = {16.0: ("anchor", None)}
            for s in SPEEDS:
                if s != 16.0:
                    spd_fp[s] = ("own3", None)
            pred, cost = fit_grid_model(a, nb, spd_fp)
            curve[nb] = {"wmae_pct": round(
                wmae(a["fea_kW"], pred * a["hyb_kW"]), 2),
                "own_pts": cost}
        out[scale] = {"anchor_pool": pool, "knee_curve": curve}
        print("%-7s (16k 후보 %d)  %s" % (
            scale, pool,
            "  ".join("%d:%5.2f%%" % (n, c["wmae_pct"])
                      for n, c in curve.items())), flush=True)

    io.open(OUT, "w", encoding="utf-8").write(
        json.dumps(out, indent=1, ensure_ascii=False))
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
