# -*- coding: utf-8 -*-
"""Motor-CAD Lab 의 Saturation & Loss Map 을 dq 격자로 내보낸다 (구동 모델 플랜트 입력).

도움말 *Saturation and Loss Maps Export*:
  Input Definition = D/Q Axis Currents  (Id = 0 을 반드시 포함해야 인덕턴스가 맞다)
  Calculation Method = Interpolate Lab Model  (이미 빌드된 Lab 모델을 보간 — FEA 재실행 없음)
  Export Loss Map 은 속도별이므로 속도마다 한 번씩 돌린다.

빌드된 Lab 모델의 상한이 460 A rms(650.5 Apk)이므로 격자도 그 안에서 잡고,
모서리(|I| > 650)는 뒤에서 마스킹한다.

  python export_lab_satmap.py [--speeds 16000,8000,4000] [--step 26]
"""
import argparse
import io
import os
import shutil
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mc_launch import launch, mc_pids  # 새 인스턴스 기동·PID 기록 (저장소 내 도우미)

SRC = r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot"
WORK = r"D:\KangDH\Thesis\e10\work_lab_pc1\drive"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speeds", default="16000,8000,4000")
    ap.add_argument("--step", type=float, default=26.0, help="dq 전류 격자 간격 [Apk]")
    ap.add_argument("--imax", type=float, default=650.0, help="dq 축 최대 [Apk]")
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)

    mot = os.path.join(WORK, "e10_satmap.mot")
    if not os.path.exists(mot):
        shutil.copy2(SRC, mot)
        d = os.path.splitext(SRC)[0]
        if os.path.isdir(d):
            shutil.copytree(d, os.path.splitext(mot)[0])

    mc = launch(mot, "satmap")
    log = []
    try:
        mc.set_motorlab_context()
        built = mc.get_model_built_lab()
        print("Lab 빌드 상태 %s, 빌드 전류 %s A rms, AC 맵 최대속도 %s rpm"
              % (built, mc.get_variable("LabModel_Saturation_StatorCurrent_RMS"),
                 mc.get_variable("LabModel_ACLoss_MaxSpeed")), flush=True)
        if not built:
            raise RuntimeError("Lab 모델이 빌드돼 있지 않다")

        mc.set_variable("SaturationMap_InputDefinition", 1)      # D/Q Axis Currents
        mc.set_variable("SaturationMap_CalculationMethod", 0)    # Interpolate Lab Model
        mc.set_variable("SaturationMap_Export", True)
        mc.set_variable("LossMap_Export", True)
        mc.set_variable("SaturationMap_ExportToCSV", False)
        mc.set_variable("SaturationMap_Current_D_Min", -a.imax)
        mc.set_variable("SaturationMap_Current_D_Max", 0.0)
        mc.set_variable("SaturationMap_Current_D_Step", a.step)
        mc.set_variable("SaturationMap_Current_Q_Min", 0.0)
        mc.set_variable("SaturationMap_Current_Q_Max", a.imax)
        mc.set_variable("SaturationMap_Current_Q_Step", a.step)
        for v in ("SaturationMap_InputDefinition", "SaturationMap_CalculationMethod",
                  "SaturationMap_Current_D_Min", "SaturationMap_Current_D_Max",
                  "SaturationMap_Current_D_Step", "SaturationMap_Current_Q_Max"):
            print("   %-38s = %s" % (v, mc.get_variable(v)), flush=True)

        for spd in [float(x) for x in a.speeds.split(",")]:
            out = os.path.join(WORK, "e10_satloss_%d.mat" % int(spd))
            mc.set_variable("LossMap_Speed", spd)
            mc.set_variable("SaturationMap_ExportFile", out)
            t0 = time.time()
            print("\n%.0f rpm 계산 시작 -> %s" % (spd, os.path.basename(out)), flush=True)
            mc.calculate_saturation_map()
            dt = time.time() - t0
            done = mc.get_variable("SaturationMap_CalculationComplete")
            size = os.path.getsize(out)/1e6 if os.path.exists(out) else 0.0
            print("   완료=%s  %.0f s  파일 %.1f MB  상태 '%s'"
                  % (done, dt, size, mc.get_variable("SaturationMap_CalculationStatus")), flush=True)
            log.append(dict(speed=spd, file=out, seconds=dt, complete=bool(done), MB=size))
    finally:
        try:
            mc.quit()
        except Exception:
            pass
    io.open(os.path.join(WORK, "export_log.txt"), "a", encoding="utf-8").write(
        time.strftime("%Y-%m-%d %H:%M:%S ") + repr(log) + "\n")
    print("\n" + "\n".join("%(speed).0f rpm: %(file)s (%(seconds).0f s)" % r for r in log))


if __name__ == "__main__":
    main()
