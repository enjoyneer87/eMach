"""Export the built Motor-CAD Lab model of e10 to a standalone .lab file for the Lab BPM FMU.

Opens a NEW, hidden Motor-CAD instance (never reuses the user's window), loads the .mot whose Lab
model is already built, checks the build flag, exports <out>.lab and closes the instance.

python export_lab_model.py [mot] [out.lab]
"""
import os
import sys
import time

import ansys.motorcad.core as pymotorcad

MOT = sys.argv[1] if len(sys.argv) > 1 else r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\e10Turn6V261.lab"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

mc = pymotorcad.MotorCAD(open_new_instance=True, keep_instance_open=False)
try:
    mc.set_variable("MessageDisplayState", 2)
    mc.load_from_file(MOT)
    built = mc.get_model_built_lab()
    print("model built (Lab):", built)
    if not built:
        raise SystemExit("Lab model is not built in %s" % MOT)
    for v in ("Imax_RMS_MotorLAB", "Speed_Max_MotorLAB", "DCBusVoltage", "CalcTypeCuLoss_MotorLAB",
              "ACLossMethod_Lab", "ModelType_MotorLAB"):
        try:
            print("  %s = %s" % (v, mc.get_variable(v)))
        except Exception as e:  # noqa: BLE001
            print("  %s : n/a (%s)" % (v, e))
    t0 = time.time()
    mc.export_lab_model(OUT)
    print("exported %s (%.1f s, %d bytes)" % (OUT, time.time() - t0, os.path.getsize(OUT)))
finally:
    mc.quit()
