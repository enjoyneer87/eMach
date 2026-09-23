# -*- coding: utf-8 -*-
"""Rotor-position-resolved FEA flux/torque map of e10 around the 16 krpm operating band.

Motor-CAD Saturation Map export with Calculation Method = FEA Calculations (not "Interpolate Lab Model")
and Result Type = Varying with rotor position (the settings of the Motor-CAD Twin Builder ECE tutorial).
Each (id, iq) point is a full electrical cycle of static FEA with TorquePointsPerCycle rotor positions.
  (a) the position-averaged psi_d, psi_q and torque check the Lab model, which interpolates 48 FEA
      points (6 currents x 8 phase advances) and so has only one cell over the whole 16 krpm band;
  (b) the position-resolved tables feed the Simscape fem_motor_dq0 block (slot harmonics, cogging).

A copy of the reference .mot is used (the original is never saved over), in a NEW hidden Motor-CAD
instance. Motor-CAD requires the id grid to contain id = 0 ("Saturation and Loss Map Export requires a
point at Id = 0"), so the id grid always runs from the lowest id up to 0, and the grid is split into
chunks of iq values instead; finished chunks are skipped, so a killed run resumes where it stopped.
Progress = number of posmap_<tag>_<k>.mat files, not the log.

  python fea_posmap.py --tag test --id=-26:13:0 --iq=0 --ppc 72
  python fea_posmap.py --tag band --id=-364:13:0 --iq=-13:13:52 --ppc 120 --chunk 1
Currents are peak A (Lab/FMU grid step 13 A, so the points coincide with the Lab export).
"""
import argparse
import io
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mc_launch import launch  # noqa: E402

SRC = r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot"
WORK = r"D:\KangDH\Thesis\e10\work_lab_pc1\fea_pos"


def rng(s):
    if ":" in s:
        a, st, b = [float(x) for x in s.split(":")]
        n = int(round((b - a)/st)) + 1
        return [round(a + k*st, 6) for k in range(n)]
    return [float(x) for x in s.split(",")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--id", required=True, help="peak A, 'a:step:0' (must end at 0, equally spaced)")
    ap.add_argument("--iq", required=True)
    ap.add_argument("--ppc", type=int, default=72, help="rotor positions per electrical cycle")
    ap.add_argument("--chunk", type=int, default=0, help="iq values per Motor-CAD call (0 = all)")
    ap.add_argument("--symmetry", type=int, default=0, help="MagneticSymmetry (reference model: 0)")
    ap.add_argument("--acloss", type=int, default=1, help="ProximityLossModel: 0 off, 1 Hybrid (default), 3 FullFEA")
    ap.add_argument("--loss-speed", type=float, default=16000.0,
                    help="export the loss map (iron, magnet, AC copper) at this speed [rpm]; 0 = no loss map")
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    mot = os.path.join(WORK, "e10_fea_pos.mot")
    if not os.path.exists(mot):
        shutil.copy2(SRC, mot)
        d = os.path.splitext(SRC)[0]
        if os.path.isdir(d):
            shutil.copytree(d, os.path.splitext(mot)[0])
    ids, iqs = rng(a.id), rng(a.iq)
    stepd = (ids[1] - ids[0]) if len(ids) > 1 else 13.0
    if abs(ids[-1]) > 1e-9:
        raise SystemExit("id grid must end at 0 (Motor-CAD requirement), e.g. --id=%g:%g:0" % (ids[0], stepd))
    n = a.chunk if a.chunk > 0 else len(iqs)
    chunks = [iqs[k:k + n] for k in range(0, len(iqs), n)]
    logf = os.path.join(WORK, "posmap_%s_log.jsonl" % a.tag)
    todo = [(k, c) for k, c in enumerate(chunks)
            if not os.path.exists(os.path.join(WORK, "posmap_%s_%02d.mat" % (a.tag, k)))]
    print("grid %d id x %d iq = %d points, %d chunks, %d to do, ppc %d"
          % (len(ids), len(iqs), len(ids)*len(iqs), len(chunks), len(todo), a.ppc), flush=True)
    if not todo:
        return
    mc = launch(mot, "feapos-" + a.tag)
    try:
        sv = mc.set_variable
        sv("MagneticThermalCoupling", 0)
        for v in ("ArmatureConductor_Temperature", "Magnet_Temperature", "Shaft_Temperature"):
            sv(v, 80.0)                                   # same as the reference model / Lab export
        sv("ProximityLossModel", a.acloss)                # AC copper loss: Hybrid, as the Lab model (ACLossMethod 0)
        sv("MagneticSymmetry", a.symmetry)
        sv("TorquePointsPerCycle", a.ppc)
        sv("ShaftSpeed", a.loss_speed if a.loss_speed > 0 else 16000.0)
        sv("SaturationMap_InputDefinition", 1)            # D/Q axis currents
        sv("SaturationMap_CalculationMethod", 1)          # FEA calculations
        sv("SaturationMap_FEACalculationType", 1)         # full cycle
        sv("SaturationMap_ResultType", 1)                 # varying with rotor position
        sv("SaturationMap_Export", True)
        sv("SaturationMap_ExportToCSV", False)
        # loss map at the operating speed: stator/rotor iron, magnet and AC copper loss per (id, iq), needed to
        # split braking and input-side losses (loss_torque_convention.html)
        sv("LossMap_Export", a.loss_speed > 0)
        if a.loss_speed > 0:
            sv("LossMap_Speed", a.loss_speed)
        stepq = (iqs[1] - iqs[0]) if len(iqs) > 1 else 13.0
        sv("SaturationMap_Current_D_Min", ids[0])
        sv("SaturationMap_Current_D_Max", 0.0)
        sv("SaturationMap_Current_D_Step", stepd)
        info = {v: mc.get_variable(v) for v in ("TorquePointsPerCycle", "MagneticSymmetry", "ProximityLossModel",
                                                 "Magnet_Temperature", "SaturationMap_CalculationMethod",
                                                 "SaturationMap_ResultType", "Pole_Number", "LossMap_Export",
                                                 "LossMap_Speed")}
        print("settings", info, flush=True)
        for k, c in todo:
            out = os.path.join(WORK, "posmap_%s_%02d.mat" % (a.tag, k))
            tmp = out + ".part.mat"
            sv("SaturationMap_Current_Q_Min", c[0])
            sv("SaturationMap_Current_Q_Max", c[-1])
            sv("SaturationMap_Current_Q_Step", stepq)
            sv("SaturationMap_ExportFile", tmp)
            t0 = time.time()
            mc.calculate_saturation_map()
            dt = time.time() - t0
            done = bool(mc.get_variable("SaturationMap_CalculationComplete"))
            status = mc.get_variable("SaturationMap_CalculationStatus")
            ok = done and os.path.exists(tmp)
            if ok:
                os.replace(tmp, out)
            rec = dict(time=time.strftime("%Y-%m-%d %H:%M:%S"), chunk=k, iq=c, id=[ids[0], 0.0, stepd],
                       ppc=a.ppc, seconds=round(dt, 1), per_point=round(dt/(len(c)*len(ids)), 1),
                       complete=done, status=str(status), file=out if ok else None)
            io.open(logf, "a", encoding="utf-8").write(json.dumps(rec) + "\n")
            print("chunk %d/%d iq %s: %.0f s (%.1f s/point) complete=%s %s"
                  % (k + 1, len(chunks), c, dt, rec["per_point"], done, status), flush=True)
            if not ok:
                raise RuntimeError("saturation map chunk %d failed: %s" % (k, status))
    finally:
        try:
            mc.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
