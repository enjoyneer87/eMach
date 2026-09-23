"""Stage 3(a): Lab FMU constant-torque phase-advance sweep.

For each (speed, torque, gamma) find the stator current that gives the requested shaft torque at
that forced phase advance (FMU mode 2, bisection), and record losses, phase voltage and whether the
point is voltage-feasible (Lab's own limit = mode-0 phase voltage ceiling, 285.12 V rms at 720 V).
Also records Lab's own optimum (mode 0) for every (speed, torque).

python lab_gamma_sweep.py [out.json]
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

LAB = r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\e10Turn6V261.lab"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\lab_gamma_sweep.json"
SPEEDS = [16000.0, 8000.0, 4000.0]
TORQUES = [20.0, 60.0]
GAMMAS = [40, 50, 60, 65, 70, 75, 80, 82, 84, 85, 86, 87, 88, 88.5, 89, 89.5]
KEYS = ["Shaft_Torque", "Phase_Advance", "Stator_Current_Phase_RMS", "Phase_Voltage_RMS", "Efficiency",
        "Armature_Copper_Loss_DC", "Armature_Copper_Loss_AC", "Stator_Back_Iron_Loss", "Stator_Tooth_Loss",
        "Rotor_Back_Iron_Loss", "Rotor_Iron_Loss_Embedded_Magnet_Pole", "Magnet_Loss", "Windage_Loss",
        "Friction_Loss_F", "Friction_Loss_R", "Shaft_Power", "Terminal_Power", "Power_Factor",
        "Electromagnetic_Torque"]


def total_loss(r):
    return sum(r[k] for k in KEYS[5:15])


def point(args):
    from lab_fmu import LabFMU
    rpm, T, g = args
    f = LabFMU(LAB)
    try:
        lo, hi = 0.5, 460.0
        rhi = f.current_advance(hi, g, rpm)
        if rhi["Shaft_Torque"] < T:
            return dict(rpm=rpm, T_req=T, gamma=g, status="current_limit", **{k: rhi[k] for k in KEYS},
                        P_loss=total_loss(rhi))
        r = rhi
        for _ in range(22):                       # bisection on current (T increases with I at fixed gamma)
            mid = 0.5*(lo + hi)
            r = f.current_advance(mid, g, rpm)
            if r["Shaft_Torque"] < T:
                lo = mid
            else:
                hi = mid
            if hi - lo < 0.02:
                break
        r = f.current_advance(hi, g, rpm)
        return dict(rpm=rpm, T_req=T, gamma=g, status="ok", **{k: r[k] for k in KEYS}, P_loss=total_loss(r))
    finally:
        f.close()


def optimum(args):
    from lab_fmu import LabFMU
    rpm, T = args
    f = LabFMU(LAB)
    try:
        r = f.torque_speed(T, rpm)
        return dict(rpm=rpm, T_req=T, **{k: r[k] for k in KEYS}, P_loss=total_loss(r))
    finally:
        f.close()


if __name__ == "__main__":
    t0 = time.time()
    with ProcessPoolExecutor(6) as ex:
        opt = list(ex.map(optimum, [(s, T) for s in SPEEDS for T in TORQUES]))
        sweep = list(ex.map(point, [(s, T, g) for s in SPEEDS for T in TORQUES for g in GAMMAS]))
    vlim = max(o["Phase_Voltage_RMS"] for o in opt if o["rpm"] == 16000.0)
    for p in sweep:
        p["V_feasible"] = bool(p["status"] == "ok" and p["Phase_Voltage_RMS"] <= vlim*1.001)
    json.dump(dict(lab=LAB, V_limit_rms=vlim, optimum=opt, sweep=sweep, seconds=time.time() - t0),
              open(OUT, "w"), indent=1)
    print("wrote", OUT, "%.0f s" % (time.time() - t0))
    for o in opt:
        print("opt %5.0f rpm %4.0f Nm: gamma %.2f I %.1f V %.1f loss %.0f W eff %.2f" % (
            o["rpm"], o["T_req"], o["Phase_Advance"], o["Stator_Current_Phase_RMS"], o["Phase_Voltage_RMS"],
            o["P_loss"], o["Efficiency"]))
