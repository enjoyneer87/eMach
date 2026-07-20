# -*- coding: utf-8 -*-
"""Fig 7 (form convergence) + Fig 8 (cost--accuracy Pareto) 재생성기.

두 그림 모두 결정론적 구조 배치(maximin + kappa-스팬) 기준으로 그린다.
그림에는 제목을 넣지 않는다 --- 서브캡션 (a)/(b)/(c)는 tex 에서 단다.

  python run_manuscript_figs78.py [--seeds 10] [--reuse-sweep]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.pipeline import AcLossPipeline
from jeet_acloss_rbf.manuscript_figs import (plot_form_convergence,
                                             plot_cost_accuracy)
from jeet_acloss_rbf.cost_accuracy import sweep_cost_accuracy

FIGDIR = r"E:\KDH\Overleaf\JEET-2024_rev1\fig"
DRIVE = r"J:\내 드라이브\EveryMotor_JEET_data\results"
SWEEP_JSON = os.path.join(DRIVE, "cost_accuracy.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--reuse-sweep", action="store_true",
                    help="기존 cost_accuracy.json 재사용 (스윕 생략)")
    a = ap.parse_args()

    pl = AcLossPipeline()
    pl.cfg["plan"]["HalfSC"]["seed"] = 3

    # ── Fig 7: 스칼라 vs 멱지수 수렴 (스케일당 1패널, 제목 없음) ──────
    for scale in ("Ref", "HalfSC", "SC"):
        out = os.path.join(FIGDIR, f"form_convergence_{scale}.pdf")
        plot_form_convergence(pl, out, scales=(scale,), n_seeds=a.seeds,
                              show_titles=False, placement="structured")
        print("Fig7:", out)

    # ── Fig 8: 비용--정확도 파레토 ────────────────────────────────────
    if a.reuse_sweep and os.path.exists(SWEEP_JSON):
        with open(SWEEP_JSON, encoding="utf-8") as fh:
            sweep = json.load(fh)
        print("스윕 재사용:", SWEEP_JSON)
    else:
        sweep = sweep_cost_accuracy(pl, n_seeds=6, out_json=SWEEP_JSON)
        print("스윕 저장:", SWEEP_JSON)

    for scale in ("HalfSC", "SC"):
        out = os.path.join(FIGDIR, f"cost_accuracy_{scale}.pdf")
        plot_cost_accuracy(sweep, out, scale, show_titles=False)
        print("Fig8:", out)

    # 본문 인용용 요약
    print("\n[파레토 요약 · transfer/structured]")
    for scale in ("HalfSC", "SC"):
        e = sweep["scales"][scale]
        front = e["pareto_by_variant"].get("transfer/structured", [])
        s = "  ".join(f"{r['budget']}pt:{r['wmae']:.2f}%" for r in front)
        print(f"  {scale} (무보정 {e['hybrid_wmae']:.1f}%) {s}")


if __name__ == "__main__":
    main()
