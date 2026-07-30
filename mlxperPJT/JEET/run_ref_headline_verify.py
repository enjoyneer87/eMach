# -*- coding: utf-8 -*-
"""Ref 헤드라인 0.5/0.6 병존의 근본 원인 확정 (B안 통일 근거).

같은 34점 예산에서 (a) 결정론 구조 배치(Table 3 경로), (b) 무작위 10시드,
(c) 파이프라인 채택(대표 시드) 모델의 전맵 wMAE 를 나란히 산출하고,
form_study 의 무보정 값도 함께 확인한다(37.7 vs 38.6 세트 판별).
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                        # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline       # noqa: E402
from jeet_acloss_rbf.form_study import run_form_study     # noqa: E402

OUT = os.path.join(HERE, "map_exports", "e10",
                   "ref_headline_verify.json")


def main() -> int:
    pl = AcLossPipeline()
    res = run_form_study(pl, n_seeds=10)

    out = {}
    for sc in ("Ref", "HalfSC", "SC"):
        e = res["scales"][sc]
        row = {"uncorrected_full_wmae": round(
            e["uncorrected"]["full_wmae"], 2)}
        for plc, blk in e["placement"].items():
            expo = blk["forms"]["exponent"] if "forms" in blk else blk.get(
                "exponent")
            if expo is None:
                row[plc] = "?"
                continue
            vals = expo["full_wmae"]
            if isinstance(vals, list):
                row[f"{plc}_exponent_wmae"] = [round(float(np.nanmean(vals)), 2),
                                               round(float(np.nanmin(vals)), 2)]
            else:
                row[f"{plc}_exponent_wmae"] = round(float(vals), 2)
        # 파이프라인 채택(대표 시드) 모델
        ds = pl.load_dataset(sc)
        m = pl.build_model(sc)
        pred = ds.h_ac_arr * m.predict(ds.speeds_k * 1000.0,
                                       ds.irms_arr, ds.phase_arr)
        err = np.abs((pred - ds.f_ac_arr) / (ds.f_ac_arr + 1e-12) * 100.0)
        row["pipeline_adopted_wmae"] = round(
            float(np.sum(ds.f_ac_arr * err) / np.sum(ds.f_ac_arr)), 2)
        out[sc] = row
        print(sc, row, flush=True)

    json.dump(out, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
