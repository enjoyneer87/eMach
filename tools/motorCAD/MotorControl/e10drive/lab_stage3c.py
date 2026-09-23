"""Stage 3(c): loss cost of the operating points the switching drive actually reaches.

For every stage-2 / stage-2b run at 16 000 rpm take the realized (I_rms, gamma), evaluate it in the
Lab FMU (mode 2: forced current and phase advance) and compare with Lab's own optimum (mode 0) at
the torque the FMU reports for that point. The ratio is what the drive's voltage margin, deadtime
and angle error cost in losses, separated from the torque error.

python lab_stage3c.py [drive_dir] [out.json]
"""
import csv
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

from lab_gamma_sweep import KEYS, LAB, total_loss

DRV = sys.argv[1] if len(sys.argv) > 1 else r"D:\KangDH\Thesis\e10\work_lab_pc1\drive"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\lab_stage3c.json"
RPM = 16000.0


def evaluate(args):
    from lab_fmu import LabFMU
    tag, i_rms, gamma = args
    f = LabFMU(LAB)
    try:
        r = f.current_advance(i_rms, gamma, RPM)
        T = r["Shaft_Torque"]
        o = f.torque_speed(max(T, 0.5), RPM) if T > 0.5 else None
        res = dict(tag=tag, I_rms=i_rms, gamma=gamma, **{k: r[k] for k in KEYS}, P_loss=total_loss(r))
        if o is not None:
            res.update(opt_gamma=o["Phase_Advance"], opt_I_rms=o["Stator_Current_Phase_RMS"],
                       opt_V=o["Phase_Voltage_RMS"], opt_P_loss=total_loss(o), opt_T=o["Shaft_Torque"])
        return res
    finally:
        f.close()


if __name__ == "__main__":
    jobs = []
    for r in csv.DictReader(open(os.path.join(DRV, "stage2_results.csv"))):
        if r["kind"] not in ("deadtime", "dt_comp", "offset_delay"):
            continue
        jobs.append(("s2|%s|T%s|td%s|dc%s|off%s|nd%s" % (r["kind"], r["T_ref"], r["td_us"], r["dt_comp"],
                                                        r["offset_deg"], r["delay_samples"]),
                     float(r["I_rms"]), float(r["gamma"])))
    p2b = os.path.join(DRV, "stage2b_results.csv")
    if os.path.exists(p2b):
        for r in csv.DictReader(open(p2b)):
            jobs.append(("s2b|%s|T%s|td%s|dc%s" % (r["table"], r["T_ref"], r["td_us"], r["dt_comp"]),
                         float(r["I_rms"]), float(r["gamma"])))
            jobs.append(("s2bref|%s|T%s" % (r["table"], r["T_ref"]), float(r["I_ref_rms"]), float(r["gamma_ref"])))
    seen, uniq = set(), []
    for j in jobs:
        if j[0] not in seen:
            seen.add(j[0])
            uniq.append(j)
    t0 = time.time()
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(evaluate, uniq))
    json.dump(dict(lab=LAB, rpm=RPM, points=res, seconds=time.time() - t0), open(OUT, "w"), indent=1)
    print("wrote", OUT, len(res), "points, %.0f s" % (time.time() - t0))
