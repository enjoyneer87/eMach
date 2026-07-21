# -*- coding: utf-8 -*-
"""요소 단위 필드(.mes) 를 텍스트로 내보내고 부하 지표를 산출한다.

Motor-CAD 의 ``.mes`` 는 바이너리이므로, COM 세션에서
``prepare_fea_export_session`` + ``get_magnetic_data`` 로
Solution/ElementsTable/NodesTable/RegionsTable 텍스트를 받아야
``field_metrics.parse_mes_txt`` 로 읽을 수 있다.

  python run_field_export.py --model HalfSC --current 690 --phase 36

``--no-solve`` 를 주면 이미 있는 .mes 를 그대로 내보낸다(재해석 없음).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")
sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools\motorCAD")  # pyMCAD

FIELDS = Path(r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET"
              r"\map_exports\e10\fields")
DRIVE = Path(r"J:\내 드라이브\EveryMotor_JEET_data\results")

MODELS = {
    "Ref": r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot",
    "SC": r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot",
    "HalfSC": r"D:\KangDH\Thesis\e10\SLFEA_Half\e10Turn6V261SLFEA_Half.mot",
}
PROX = {"fullfea": 3, "hybrid": 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="HalfSC", choices=sorted(MODELS))
    ap.add_argument("--speed", type=float, default=16000.0)
    ap.add_argument("--current", type=float, default=690.0)
    ap.add_argument("--phase", type=float, default=36.0)
    ap.add_argument("--mode", default="fullfea", choices=sorted(PROX))
    ap.add_argument("--no-solve", action="store_true")
    a = ap.parse_args()

    import ansys.motorcad.core as pymotorcad
    from pyMCAD.fea_workflow import prepare_fea_export_session
    from pyMCAD.magnetic import get_magnetic_data
    from jeet_acloss_rbf.field_metrics import (parse_mes_txt, loading_metrics,
                                               maxwell_torque)

    mot = MODELS[a.model]
    tag = "%s%s_%dk_%ddeg" % (a.model,
                              "" if a.mode == "fullfea" else "_Hybrid",
                              round(a.speed / 1000), round(a.phase))
    out_txt = FIELDS / ("Magnetic_%s_OnLoadTorque.txt" % tag)

    mc = pymotorcad.MotorCAD(open_new_instance=True,
                             enable_success_variable=False)
    try:
        try:
            mc.set_variable("MessageDisplayState", 2)
        except Exception:
            pass
        mc.load_from_file(mot)
        print("loaded:", mot)

        if not a.no_solve:
            mc.set_variable("ProximityLossModel", PROX[a.mode])
            mc.set_variable("ShaftSpeed", a.speed)
            mc.set_variable("RMSCurrent", a.current)
            mc.set_variable("PhaseAdvance", a.phase)
            print("해석 중 (%.0f A, %.0f rpm, %.0f deg, %s) ..."
                  % (a.current, a.speed, a.phase, a.mode))
            mc.do_magnetic_calculation()

        res = Path(mot).with_suffix("") / "FEResultsData"
        mes = res / "OnLoadTorque_result_1.mes"
        if not mes.exists():
            cand = sorted(res.glob("OnLoadTorque_result_*.mes"),
                          key=lambda p: p.stat().st_mtime, reverse=True)
            if not cand:
                sys.exit("OnLoadTorque .mes 없음: %s" % res)
            mes = cand[0]
        print("mes:", mes.name)

        FIELDS.mkdir(parents=True, exist_ok=True)
        prepare_fea_export_session(mc, mes_path=mes)
        # final_step=0 + auto_final_step: 마지막 스텝을 자동 추론한다
        get_magnetic_data(mc, first_step=1, final_step=0,
                          auto_final_step=True, filename=out_txt,
                          clean_up=False)
        print("exported:", out_txt)
    finally:
        try:
            mc.quit()
            print("Motor-CAD 종료 (모델 저장 안 함)")
        except Exception:
            pass

    p = parse_mes_txt(str(out_txt))
    m = loading_metrics(p)
    t = maxwell_torque(p)
    g = m["airgap"]
    print("\n=== %s · %.0f A · %.0f deg ===" % (a.model, a.current, a.phase))
    print("  공극 |B| 평균 %.3f T   B_r peak %.3f T"
          % (g["b_mean_T"], g["br_peak_T"]))
    print("  %-4s%-11s%-11s" % ("층", "|B|평균[T]", "|B|max[T]"))
    for k, v in m["per_turn"].items():
        print("  %-4s%-11.3f%-11.3f" % (k, v["b_mean_T"], v["b_max_T"]))
    print("  Maxwell 토크 %.1f Nm (층간 %.1f%%)"
          % (abs(t["torque_Nm"]), t["layer_spread_pct"]))

    DRIVE.mkdir(parents=True, exist_ok=True)
    out_json = DRIVE / ("field_metrics_%s.json" % tag)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"model": a.model, "speed_rpm": a.speed,
                   "current_a": a.current, "phase_deg": a.phase,
                   "mode": a.mode, "metrics": m,
                   "torque": t}, fh, ensure_ascii=False, indent=1)
    print("JSON 저장:", out_json)
    print("txt 크기: %.1f MB" % (out_txt.stat().st_size / 1e6))


if __name__ == "__main__":
    main()
