# -*- coding: utf-8 -*-
"""Table(Compareloading) 용 공극/도체 자속밀도 재산출기 (6턴 e10 기준).

Motor-CAD 실행 없이 기존 .mes 추출본(Magnetic_*.txt)만으로 산출한다.
코드는 eMach 에, 산출 데이터(JSON)는 Google Drive 에 보존한다.

  python run_loading_metrics.py [--out <json>]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "tools")))  # 이 체크아웃의 tools

from jeet_acloss_rbf.field_metrics import (compare_models, read_mot,
                                           winding_losses, parse_mes_txt,
                                           maxwell_torque)

FIELDS = (r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET"
          r"\map_exports\e10\fields")
DRIVE_OUT = (r"J:\내 드라이브\EveryMotor_JEET_data\results"
             r"\loading_metrics_6turn.json")

PATHS = {
    "Ref": os.path.join(FIELDS, "Magnetic_Ref_16k_36deg_OnLoadTorque.txt"),
    "SC": os.path.join(FIELDS, "Magnetic_SC_16k_36deg_OnLoadTorque.txt"),
}

# 권선 저항은 .mot 에서 직접 읽는다 (Motor-CAD 실행 불필요).
MOT = {
    "Ref": r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot",
    "SC": r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot",
}
I_RMS = {"Ref": 460.0, "SC": 920.0}      # 모델별 전류 한계


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
        print("\n=== Ref 대비 비율 (자속밀도) ===")
        for k, v in res["ratio_to_ref"].items():
            print(f"  {k:<8} B_g {v['b_g']:.3f}   B_Cu {v['b_cu']:.3f}")

    # ── 권선 저항·동손 (.mot) + 공극 Maxwell 토크 (.mes) ───────────────
    print("\n=== 권선 저항·동손 (.mot 직접 읽기) ===")
    wind = {}
    for k, f in MOT.items():
        if not os.path.exists(f):
            print(f"  {k}: .mot 없음 {f}")
            continue
        m = read_mot(f)
        w = winding_losses(m, I_RMS[k])
        t = maxwell_torque(parse_mes_txt(PATHS[k]))
        wind[k] = {"mot": {kk: vv for kk, vv in m.items() if kk != "path"},
                   "i_rms_a": I_RMS[k], "loss_kW": w,
                   "torque_maxwell_Nm": t["torque_Nm"],
                   "torque_layer_spread_pct": t["layer_spread_pct"]}
        print(f"  {k:<5} ({I_RMS[k]:.0f} A_rms, "
              f"{m.get('ArmatureConductor_Temperature', 0):.0f}C) "
              f"R_co {m['R_active_mOhm']:6.2f}  R_end {m['R_end_mOhm']:6.2f}"
              f"  R_DC {m['R_total_mOhm']:6.2f} mOhm")
        print(f"        P_act {w['p_active_kW']:6.2f}  "
              f"P_DC {w['p_total_kW']:6.2f} kW   "
              f"T(Maxwell) {abs(t['torque_Nm']):7.1f} Nm "
              f"(층간 {t['layer_spread_pct']:.1f}%)")
    if "Ref" in wind and "SC" in wind:
        r, s = wind["Ref"], wind["SC"]
        print("  SC/Ref  R_co %.3f  R_end %.3f  R_DC %.3f  P_act %.3f  "
              "P_DC %.3f  T %.3f" % (
                  s["mot"]["R_active_mOhm"] / r["mot"]["R_active_mOhm"],
                  s["mot"]["R_end_mOhm"] / r["mot"]["R_end_mOhm"],
                  s["mot"]["R_total_mOhm"] / r["mot"]["R_total_mOhm"],
                  s["loss_kW"]["p_active_kW"] / r["loss_kW"]["p_active_kW"],
                  s["loss_kW"]["p_total_kW"] / r["loss_kW"]["p_total_kW"],
                  s["torque_maxwell_Nm"] / r["torque_maxwell_Nm"]))
        print("  주의: Maxwell 토크는 층간 일관성과 k_r^2 비는 재현하나 "
              "절대값 검증은 Motor-CAD 해가 필요하다.")
    res["winding"] = wind

    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print("\nJSON 저장:", a.out)


if __name__ == "__main__":
    main()
