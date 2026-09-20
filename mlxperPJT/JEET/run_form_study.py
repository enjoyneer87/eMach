# -*- coding: utf-8 -*-
"""보정 형태 비교 연구 실행기.

코드는 eMach 에, 산출 데이터(JSON)는 Google Drive 에 보존한다.

  python run_form_study.py [--seeds 10] [--out <json>]
"""
import argparse
import os
import sys

# Direct invocation from a package checkout must find its sibling library.
_package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_package_root, 'jeet_acloss_rbf')):
    sys.path.insert(0, _package_root)

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "tools")))   # 워크트리의 tools 를 쓴다

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.pipeline import AcLossPipeline
from jeet_acloss_rbf.form_study import run_form_study
from jeet_acloss_rbf.repro_env import results_dir

DRIVE_OUT = os.path.join(results_dir(), 'form_study.json')


def fmt(value, digits=2):
    return "unavailable" if value is None else f"{value:.{digits}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--margin", type=float, default=12.0)
    ap.add_argument("--out", default=DRIVE_OUT)
    a = ap.parse_args()

    pl = AcLossPipeline()
    pl.cfg["plan"]["HalfSC"]["seed"] = 3      # 격자 정규화 후 대표 시드

    res = run_form_study(pl, n_seeds=a.seeds, margin_deg=a.margin,
                         out_json=a.out)

    band = res["meta"]["operating_band_deg"]
    print(f"Operating band: {res['meta']['operating_band_status']}; {len(band)} speeds")
    hdr = (f"{'모델':<8}{'형태':<10}{'배치':<11}"
           f"{'전체wMAE':>9}{'전체MAE':>9}{'영역wMAE':>9}{'영역MAE':>9}")
    print(hdr)
    print("-" * len(hdr))
    for scale, e in res["scales"].items():
        u = e["uncorrected"]
        print(f"{scale:<8}{'무보정':<10}{'-':<11}{u['full_wmae']:>9.1f}"
              f"{u['full_mae']:>9.1f}{fmt(u['region_wmae'],1):>11}"
              f"{fmt(u['region_mae'],1):>11}")
        print(f"{'':<8}[영역 {e['n_region']}/{e['n_points']}점 · 예산 "
              f"{e['budget']} = n_base {e['n_base']} + {e['ns_own']}x"
              f"{e['n_other_speeds']}속도 · 기준풀 {e['base_pool']}]")
        for f in res["meta"]["forms"]:
            for pl, blk in e["placement"].items():
                v = blk["forms"].get(f)
                if v is None:
                    print(f"{'':<8}{f:<10}{pl:<11}{'실패':>9}")
                    continue
                print(f"{'':<8}{f:<10}{pl:<11}{v['full_wmae']:>9.2f}"
                      f"{v['full_mae']:>9.2f}{fmt(v['region_wmae']):>11}"
                      f"{fmt(v['region_mae']):>11}")
        for pl, blk in e["placement"].items():
            sp = blk["log_kappa_span"]
            if sp:
                s = "  ".join(f"{k}k:{v:.3f}" for k, v in sorted(sp.items()))
                print(f"{'':<8}[{pl} log-kappa 스팬] {s}")
            print(f"{'':<8}[{pl} 실사용 TS-FEA] {blk['n_ts_used']}점 "
                  f"({blk['n_runs']}회)")
        print()
    print("JSON 저장:", a.out)


if __name__ == "__main__":
    main()
