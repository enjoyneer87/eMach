"""Thin wrapper around the Motor-CAD Lab BPM FMU (fmpy): evaluate operating points.

    from lab_fmu import LabFMU
    fmu = LabFMU(lab_path)
    fmu.torque_speed(T, rpm)                    # mode 0: Lab's own control strategy
    fmu.current_advance(I_rms, gamma_deg, rpm)  # mode 2: forced current and phase advance

Each call instantiates the FMU once (one co-simulation step); outputs are returned as a dict
of all FMU output variables.
"""
import os
import shutil
import tempfile

from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave

FMU_PATH = r"C:\Program Files\ANSYS Inc\v261\motorcad\FMU\Ansys_Motor-CAD_Lab_BPM.fmu"


class LabFMU:
    def __init__(self, lab_path, fmu_path=FMU_PATH, vdc=720.0, t_wind=80.0, t_mag=80.0, verbose=False):
        self.lab = lab_path
        self.md = read_model_description(fmu_path)
        self.unzip = extract(fmu_path, unzipdir=tempfile.mkdtemp(prefix="labfmu_"))
        self.vr = {v.name: v.valueReference for v in self.md.modelVariables}
        self.outputs = [v.name for v in self.md.modelVariables if v.causality == "output"]
        self.defaults = dict(DC_Bus_Voltage=vdc, Stator_Winding_Temperature=t_wind, Magnet_Temperature=t_mag,
                             Airgap_Temperature=t_mag, Bearing_F_Temperature=40.0, Bearing_R_Temperature=40.0,
                             Max_Stator_Current_RMS=460.0)
        self.verbose = verbose

    def _run(self, mode, inputs):
        fmu = FMU2Slave(guid=self.md.guid, unzipDirectory=self.unzip,
                        modelIdentifier=self.md.coSimulation.modelIdentifier, instanceName="lab")
        fmu.instantiate()
        fmu.setString([self.vr["ModelFilePath"]], [self.lab])
        fmu.setInteger([self.vr["OperatingPointDefinition"]], [int(mode)])
        fmu.setBoolean([self.vr["ShowInputOutputInTerminal"]], [bool(self.verbose)])
        vals = dict(self.defaults)
        vals.update(inputs)
        fmu.setupExperiment(startTime=0.0)
        fmu.enterInitializationMode()
        fmu.setReal([self.vr[k] for k in vals], list(vals.values()))
        fmu.exitInitializationMode()
        fmu.setReal([self.vr[k] for k in vals], list(vals.values()))
        fmu.doStep(currentCommunicationPoint=0.0, communicationStepSize=1.0)
        out = dict(zip(self.outputs, fmu.getReal([self.vr[k] for k in self.outputs])))
        fmu.terminate()
        fmu.freeInstance()
        return out

    def torque_speed(self, torque, rpm, **kw):
        return self._run(0, dict(Requested_Shaft_Torque=torque, Shaft_Speed=rpm, **kw))

    def max_current(self, rpm, i_rms, **kw):
        return self._run(1, dict(Shaft_Speed=rpm, Max_Stator_Current_RMS=i_rms, **kw))

    def current_advance(self, i_rms, gamma_deg, rpm, **kw):
        return self._run(2, dict(Max_Stator_Current_RMS=i_rms, Requested_Phase_Advance=gamma_deg,
                                 Shaft_Speed=rpm, **kw))

    def close(self):
        shutil.rmtree(self.unzip, ignore_errors=True)


if __name__ == "__main__":
    import time
    lab = r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\e10Turn6V261.lab"
    f = LabFMU(lab, verbose=False)
    keys = ["Shaft_Torque", "Phase_Advance", "Stator_Current_Phase_RMS", "Phase_Voltage_RMS", "Efficiency",
            "Armature_Copper_Loss_DC", "Armature_Copper_Loss_AC", "Stator_Back_Iron_Loss", "Stator_Tooth_Loss",
            "Magnet_Loss", "Power_Factor"]
    t0 = time.time()
    r0 = f.torque_speed(20.0, 16000.0)
    print("mode0 T=20 16k (%.1fs):" % (time.time() - t0), {k: round(r0[k], 3) for k in keys})
    t0 = time.time()
    r2 = f.current_advance(r0["Stator_Current_Phase_RMS"], r0["Phase_Advance"], 16000.0)
    print("mode2 same I,gamma (%.1fs):" % (time.time() - t0), {k: round(r2[k], 3) for k in keys})
    r3 = f.current_advance(r0["Stator_Current_Phase_RMS"], 85.0, 16000.0)
    print("mode2 gamma 85:", {k: round(r3[k], 3) for k in keys})
    f.close()
