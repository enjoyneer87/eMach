# -*- coding: utf-8 -*-
"""비용--정확도 파레토 스윕 실행기.

코드는 eMach 에, 산출 데이터(JSON)는 Google Drive 에 보존한다.

  python run_cost_accuracy.py [--seeds 6] [--out <json>]
"""
import argparse
import sys

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.pipeline import AcLossPipeline
from jeet_acloss_rbf.cost_accuracy import sweep_cost_accuracy

DRIVE_OUT = (r"J:\내 드라이브\EveryMotor_JEET_data\results"
             r"\cost_accuracy.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--out", default=DRIVE_OUT)
    a = ap.parse_args()

    pl = AcLossPipeline()
    pl.cfg["plan"]["HalfSC"]["seed"] = 3

    res = sweep_cost_accuracy(pl, n_seeds=a.seeds, out_json=a.out)

    for scale, e in res["scales"].items():
        print(f"\n=== {scale} (k_r={e['k_r']}, 기준풀 {e['base_pool']}, "
              f"무보정 wMAE {e['hybrid_wmae']:.1f}%) ===")
        print(f"{'변형':<22}{'예산':>5}{'n_base':>7}{'n_spd':>6}"
              f"{'wMAE':>8}{'최악':>8}")
        for name, front in e["pareto_by_variant"].items():
            for r in front:
                print(f"{name:<22}{r['budget']:>5}{r['n_base']:>7}"
                      f"{r['n_spd']:>6}{r['wmae']:>8.2f}"
                      f"{r['wmae_worst']:>8.2f}")
            print()
    print("JSON 저장:", a.out)


if __name__ == "__main__":
    main()
