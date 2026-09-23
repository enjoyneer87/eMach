# -*- coding: utf-8 -*-
"""How Motor-CAD E-Magnetic splits losses between shaft torque and input power (for loss_torque_convention.html).

Runs E-Magnetic on-load calculations at a few 16 krpm points of e10 (copy of the reference .mot, NEW hidden
instance) with the AC copper loss model Hybrid and, for comparison, FullFEA, and records average torques
(Maxwell-stress/virtual-work, flux-linkage), ShaftTorque, every loss term, input/electromagnetic power and
terminal voltages (waveform peak vs phasor). The loss split is then inferred by matching
(AvTorque - ShaftTorque)*w_mech to sums of loss terms.

  python emag_loss_check.py [out.json]
"""
import json
import math
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mc_launch import launch  # noqa: E402

SRC = r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot"
WORK = r"D:\KangDH\Thesis\e10\work_lab_pc1\emag_check"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "emag_loss_check.json")
# (label, peak current A, phase advance deg, AC loss model 1 Hybrid / 3 FullFEA)
POINTS = [("noload_hyb", 0.0, 0.0, 1), ("T20_hyb", 195.8, 88.01, 1), ("T60_hyb", 222.2, 85.27, 1),
          ("noload_ffea", 0.0, 0.0, 3), ("T20_ffea", 195.8, 88.01, 3)]
OUTS = ["AvTorqueMsVw", "AvTorqueVW", "AvTorqueMS", "AvTorqueDQ", "AvTorqueEC", "ShaftTorque",
        "StatorIronLoss_Total", "StatorIronLoss_Total_Adj", "RotorIronLoss_Total", "RotorIronLoss_Total_Adj",
        "MagnetLoss", "ConductorLoss", "ACLoss_Hybrid_Total", "ACLoss_FEA_OnLoad_Total", "ACLoss_FEA_OC_Total",
        "TotalLoss", "ElectromagneticPower", "InputPower", "PeakPhaseVoltage", "RmsPhaseVoltage",
        "PhasorRmsPhaseVoltage", "PeakLineLineVoltage", "FluxLinkageLoad_D", "FluxLinkageLoad_Q",
        "PhaseCurrent", "RMSPhaseCurrent", "TorqueRippleMsVw", "ShaftTorqueCalculationMethod",
        "Windage_Loss", "Friction_Loss_F", "Friction_Loss_R", "WindageLoss", "FrictionLoss"]


def main():
    os.makedirs(WORK, exist_ok=True)
    mot = os.path.join(WORK, "e10_emag_check.mot")
    if not os.path.exists(mot):
        shutil.copy2(SRC, mot)
        d = os.path.splitext(SRC)[0]
        if os.path.isdir(d):
            shutil.copytree(d, os.path.splitext(mot)[0])
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    mc = launch(mot, "emagcheck")
    try:
        sv = mc.set_variable
        sv("MagneticThermalCoupling", 0)
        for v in ("ArmatureConductor_Temperature", "Magnet_Temperature", "Shaft_Temperature"):
            sv(v, 80.0)
        for v, x in (("BackEMFCalculation", False), ("CoggingTorqueCalculation", False),
                     ("TorqueCalculation", True), ("TorqueSpeedCalculation", False)):
            sv(v, x)
        sv("ShaftSpeed", 16000.0)
        sv("TorquePointsPerCycle", 120)
        sv("TorqueNumberCycles", 1)
        sv("CurrentDefinition", 0)                     # peak line current (= phase current, star)
        for lab, ipk, gam, acm in POINTS:
            if lab in res:
                continue
            sv("ProximityLossModel", acm)
            sv("PeakCurrent", ipk)
            sv("PhaseAdvance", gam)
            t0 = time.time()
            mc.do_magnetic_calculation()
            r = dict(I_pk=ipk, gamma=gam, acloss_model=acm, seconds=round(time.time() - t0, 1))
            for v in OUTS:
                try:
                    r[v] = mc.get_variable(v)
                except Exception as exc:  # noqa: BLE001
                    r[v] = "n/a"
            res[lab] = r
            json.dump(res, open(OUT, "w"), indent=1)
            print("%-12s %5.0f s  AvTorqueMsVw %s  ShaftTorque %s" % (lab, r["seconds"], r["AvTorqueMsVw"],
                                                                     r["ShaftTorque"]), flush=True)
    finally:
        try:
            mc.quit()
        except Exception:
            pass
    wm = 16000*2*math.pi/60
    for lab, r in res.items():
        try:
            print("%-12s drag (AvT - Tshaft)*wm = %.1f W" % (lab, (r["AvTorqueMsVw"] - r["ShaftTorque"])*wm))
        except Exception:
            pass


if __name__ == "__main__":
    main()
