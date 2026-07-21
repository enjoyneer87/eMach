# -*- coding: utf-8 -*-
"""Motor-CAD 해로 T_em 을 확인한다 (.mes Maxwell 적분 검증용).

새 Motor-CAD COM 인스턴스를 열어 모델을 로드하고, .mes 추출본과 같은
운전점(16 kRPM, beta=36deg)에서 자기 해석을 돌려 토크를 읽는다.
``AvTorqueMS`` 는 본 리포지토리의 ``field_metrics.maxwell_torque`` 와
동일한 Maxwell 응력 방법이므로 직접 비교 대상이 된다.

모델 파일은 저장하지 않는다 (읽기 전용으로 다룬다).

  python run_torque_check.py [--speed 16000] [--phase 36]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")

MODELS = {
    "Ref": {"mot": r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot",
            "irms": 460.0,
            "mes": (r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports"
                    r"\e10\fields\Magnetic_Ref_16k_36deg_OnLoadTorque.txt")},
    "SC": {"mot": r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot",
           "irms": 920.0,
           "mes": (r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports"
                   r"\e10\fields\Magnetic_SC_16k_36deg_OnLoadTorque.txt")},
    # HalfSC 는 자체 전류한계 690 A 케이스의 FEA 결과가 없어 .mes 대조가
    # 불가하다. Motor-CAD 해만 읽는다.
    "HalfSC": {"mot": (r"D:\KangDH\Thesis\e10\SLFEA_Half"
                       r"\e10Turn6V261SLFEA_Half.mot"),
               "irms": 690.0, "mes": None},
}

TORQUE_VARS = ["AvTorqueMS", "AvTorqueVW", "AvTorqueMsVw", "AvTorqueDQ",
               "OnLoadDQTorque", "AvTorqueAlignment", "AvTorqueReluctance",
               "ShaftTorque", "TorquePerVolume"]

DRIVE_OUT = (r"J:\내 드라이브\EveryMotor_JEET_data\results"
             r"\torque_check_6turn.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=16000.0)
    ap.add_argument("--phase", type=float, default=36.0)
    ap.add_argument("--models", default="Ref,SC")
    ap.add_argument("--out", default=DRIVE_OUT)
    a = ap.parse_args()

    import ansys.motorcad.core as pymotorcad
    from jeet_acloss_rbf.field_metrics import parse_mes_txt, maxwell_torque

    mc = pymotorcad.MotorCAD(open_new_instance=True,
                             enable_success_variable=False)
    print("Motor-CAD COM 연결됨")

    out = {"operating_point": {"speed_rpm": a.speed, "phase_deg": a.phase},
           "models": {}}
    try:
        for name in [s.strip() for s in a.models.split(",") if s.strip()]:
            cfg = MODELS[name]
            print(f"\n=== {name} ===")
            print("  load:", cfg["mot"])
            mc.load_from_file(cfg["mot"])
            mc.set_variable("ShaftSpeed", a.speed)
            mc.set_variable("RMSCurrent", cfg["irms"])
            mc.set_variable("PhaseAdvance", a.phase)
            print(f"  해석 중 ({cfg['irms']:.0f} A_rms, "
                  f"{a.speed:.0f} rpm, {a.phase:.0f} deg) ...")
            mc.do_magnetic_calculation()

            vals = {}
            for v in TORQUE_VARS:
                try:
                    vals[v] = float(mc.get_variable(v))
                except Exception as exc:
                    vals[v] = f"(읽기 실패: {exc})"
            for v in ("Resistance_MotorLAB", "EndWindingResistance_Lab",
                      "RMSCurrentDensity", "ParallelPaths", "WindingLayers"):
                try:
                    vals[v] = float(mc.get_variable(v))
                except Exception:
                    pass

            mx = float("nan")
            if cfg["mes"] and os.path.exists(cfg["mes"]):
                mx = maxwell_torque(parse_mes_txt(cfg["mes"]))["torque_Nm"]

            out["models"][name] = {"i_rms_a": cfg["irms"],
                                   "motorcad": vals,
                                   "mes_maxwell_Nm": mx}
            print(f"  {'변수':<22}{'값':>12}")
            for v in TORQUE_VARS:
                x = vals.get(v)
                if isinstance(x, float):
                    print(f"  {v:<22}{x:>12.2f}")
                else:
                    print(f"  {v:<22}{str(x)[:30]:>12}")
            print(f"  {'.mes Maxwell 적분':<22}{abs(mx):>12.2f}")
            ms = vals.get("AvTorqueMS")
            if isinstance(ms, float) and ms and mx == mx:
                print(f"  -> .mes/MCAD 비 = {abs(mx) / abs(ms):.3f}")
    finally:
        try:
            mc.quit()
            print("\nMotor-CAD 종료 (모델 저장하지 않음)")
        except Exception:
            pass

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("JSON 저장:", a.out)


if __name__ == "__main__":
    main()
