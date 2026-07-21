# -*- coding: utf-8 -*-
"""Table(Compareloading) 용 공극/도체 자속밀도 재산출기 (6턴 e10 기준).

Motor-CAD 실행 없이 기존 .mes 추출본(Magnetic_*.txt)만으로 산출한다.
코드는 eMach 에, 산출 데이터(JSON)는 Google Drive 에 보존한다.

  python run_loading_metrics.py [--out <json>]
"""
import argparse
import os
import sys

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")

from jeet_acloss_rbf.field_metrics import compare_models

FIELDS = (r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET"
          r"\map_exports\e10\fields")
DRIVE_OUT = (r"J:\내 드라이브\EveryMotor_JEET_data\results"
             r"\loading_metrics_6turn.json")

PATHS = {
    "Ref": os.path.join(FIELDS, "Magnetic_Ref_16k_36deg_OnLoadTorque.txt"),
    "SC": os.path.join(FIELDS, "Magnetic_SC_16k_36deg_OnLoadTorque.txt"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DRIVE_OUT)
    a = ap.parse_args()

    res = compare_models(PATHS, out_json=a.out)

    for name, m in res["models"].items():
        g = m["airgap"]
        print(f"\n=== {name} · {m['source']} · {m['n_turns']}턴 ===")
        print(f"  공극 {g['regions']} r={g['r_min_mm']:.2f}~"
              f"{g['r_max_mm']:.2f}mm  n={g['n_elem']}")
        print(f"    |B| 면적가중평균 {g['b_mean_T']:.3f} T   "
              f"|B|max {g['b_max_T']:.3f} T   "
              f"B_r peak {g['br_peak_T']:.3f} T")
        print(f"  도체 전류밀도 [A/mm2] {m['j_phase_a_mm2']}")
        print(f"  {'층':>3}{'r[mm]':>8}{'|B|평균[T]':>11}{'|B|max[T]':>11}"
              f"{'면적[mm2]':>11}{'슬롯수':>7}   (층1=개구부)")
        for k, v in m["per_turn"].items():
            print(f"  {k:>3}{v['r_mean_mm']:>8.2f}{v['b_mean_T']:>11.3f}"
                  f"{v['b_max_T']:>11.3f}{v['area_mm2']:>11.2f}"
                  f"{v['n_slots']:>7}")
        print(f"    도체 전체 평균 B_Cu {m['b_cu_mean_T']:.3f} T  "
              f"(최대 도체 {m['b_cu_max_turn_T']:.3f} T)")

    if "ratio_to_ref" in res:
        print("\n=== Ref 대비 비율 ===")
        for k, v in res["ratio_to_ref"].items():
            print(f"  {k:<8} B_g {v['b_g']:.3f}   B_Cu {v['b_cu']:.3f}")
    print("\nJSON 저장:", a.out)


if __name__ == "__main__":
    main()
