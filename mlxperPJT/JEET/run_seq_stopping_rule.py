# -*- coding: utf-8 -*-
"""Truth-free 순차 정지 규칙 검증 — 새 설계에서 수렴 분석(전 스윕) 없이 무릎 찾기.

가설: 결정론적 maximin 배치는 중첩(nested)이므로 기준 속도 표본을 순차 추가하며
보정 표면의 변화량 D(n) = Σ h·|AF_n−AF_{n−2}| / Σ h·AF_n (하이브리드 가중,
진리값 불사용)이 정체하는 지점이 실제 wMAE 무릎과 일치한다.
검증: 스윕 진리값은 채점(wMAE)에만 쓰고 규칙 D(n)은 보지 않는다.

산출: map_exports/e10/seq_stopping_rule.json + 표 stdout
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline         # noqa: E402
from jeet_acloss_rbf import RbfModelBuilder                 # noqa: E402

OUT = os.path.join(HERE, "map_exports", "e10", "seq_stopping_rule.json")
CFG = {"Ref": {"n_spd": 4, "n_max": 22}, "SC": {"n_spd": 3, "n_max": 24}}
BASE_SPEED = 16.0            # [kRPM] — form_study/RbfModelBuilder 규약
D_TOL = 1.0          # [%] 정지 임계
KNEE_FACTOR = 1.10   # wMAE가 바닥의 110% 안이면 무릎 통과로 간주


def main() -> int:
    pl = AcLossPipeline()
    out = {}
    for scale, cfg in CFG.items():
        ds = pl.load_dataset(scale)
        h = ds.h_ac_arr
        f_true = ds.f_ac_arr
        preds = {}
        prev_base = None
        nested_ok = True
        ns = list(range(6, cfg["n_max"] + 1, 2))
        for n in ns:
            plan = RbfModelBuilder.plan_sampling_indices(
                ds, n_base=n, n_spd=cfg["n_spd"], base_speed=BASE_SPEED,
                placement="structured", seed=0)
            base_idx = set(np.asarray(plan.get("base", plan["all"])).tolist())
            if prev_base is not None and not prev_base.issubset(base_idx):
                nested_ok = False
            prev_base = base_idx
            with contextlib.redirect_stdout(io.StringIO()):
                m = RbfModelBuilder.build_separable_rbf(
                    ds, base_speed=BASE_SPEED, exponent=True,
                    index_plan=plan)
            preds[n] = m.predict(ds.speeds_k * 1000.0, ds.irms_arr,
                                 ds.phase_arr)

        rows = []
        print(f"\n=== {scale} (n_spd={cfg['n_spd']}, 중첩={nested_ok}) ===")
        print(f"{'n_base':>7} {'D(n) [%]':>9} {'wMAE [%]':>9}")
        for i, n in enumerate(ns):
            p = preds[n]
            loss = p * h
            err = np.abs(p * h - f_true) / (f_true + 1e-12) * 100.0
            wmae = float(np.sum(f_true * err) / np.sum(f_true))
            if i == 0:
                d = np.nan
            else:
                p0 = preds[ns[i - 1]]
                d = float(np.sum(h * np.abs(p - p0)) / np.sum(h * p) * 100.0)
            rows.append({"n_base": n, "D_pct": None if np.isnan(d)
                         else round(d, 2), "wmae_pct": round(wmae, 2)})
            print(f"{n:7d} {('--' if np.isnan(d) else f'{d:9.2f}')} "
                  f"{wmae:9.2f}")

        dv = [r["D_pct"] for r in rows]
        wv = [r["wmae_pct"] for r in rows]
        n_stop = next((rows[i]["n_base"] for i in range(2, len(rows))
                       if dv[i] is not None and dv[i] < D_TOL
                       and dv[i - 1] is not None and dv[i - 1] < D_TOL),
                      None)
        floor = min(wv)
        n_knee = next((r["n_base"] for r, w in zip(rows, wv)
                       if w <= KNEE_FACTOR * floor), None)
        print(f"  -> 정지 규칙 n* = {n_stop} (D<{D_TOL}% 2연속), "
              f"실제 무릎 n_knee = {n_knee} (wMAE ≤ 바닥x{KNEE_FACTOR})")
        out[scale] = {"rows": rows, "n_stop": n_stop, "n_knee": n_knee,
                      "nested": nested_ok, "wmae_floor": floor}

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print("\n저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
