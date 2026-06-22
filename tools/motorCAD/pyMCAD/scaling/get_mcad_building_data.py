"""
get_mcad_building_data.py — MATLAB getMCADBuildingData 대응

Motor-CAD Lab 모델 빌드 데이터 전체(형상 + 온도 + 저항 + 보정계수)를
dict로 반환한다.
"""
import math
from .models import MotorCADGeo
from .get_mcad_machine_data import get_mcad_machine_data


def get_mcad_building_data(mcad) -> dict:
    """Motor-CAD 인스턴스에서 Lab 빌드 데이터를 읽어 dict로 반환.

    Parameters
    ----------
    mcad : ansys.motorcad.core.MotorCAD

    Returns
    -------
    dict with keys:
        'MotorCADGeo'             : MotorCADGeo
        'Twdg_MotorLAB'           : float
        'ArmatureConductor_Temperature' : float
        'TwindingCalc_MotorLAB'   : float
        'WindingTemp_ACLoss_Ref_Lab' : float
        'Tmag_MotorLAB'           : float
        'TmagnetCalc_MotorLAB'    : float
        'Airgap_Temperature'      : float
        'Bearing_Temperature_F'   : float
        'Bearing_Temperature_R'   : float
        'Resistance_MotorLAB'     : float
        'EndWindingResistance_Lab': float
        'EndWindingInductance_Lab': float
        'RacRdc_MotorLAB'         : float
        'coeffi'                  : dict
        'T0data'                  : dict
    """
    gv = mcad.get_variable

    # ── 형상 데이터 ──
    geo: MotorCADGeo = get_mcad_machine_data(mcad)

    # ── Lab 전류 스펙 ──
    current_spec = int(gv("CurrentSpec_MotorLAB"))
    if current_spec == 0:
        imaxpk  = float(gv("MaxModelCurrent_MotorLAB"))
        imaxrms = imaxpk / math.sqrt(2)
    else:
        imaxrms = float(gv("MaxModelCurrent_RMS_MotorLAB"))
        imaxpk  = imaxrms * math.sqrt(2)

    geo.Imaxpk            = imaxpk
    geo.Imaxrms           = imaxrms
    geo.referenceSpeed    = float(gv("FEALossMap_RefSpeed_Lab"))
    geo.SpeedMax_MotorLAB = float(gv("SpeedMax_MotorLAB"))

    bd: dict = {"MotorCADGeo": geo}

    # ── 온도 / 빌드 조건 ──
    for key in [
        "Twdg_MotorLAB",
        "ArmatureConductor_Temperature",
        "TwindingCalc_MotorLAB",
        "WindingTemp_ACLoss_Ref_Lab",
        "Tmag_MotorLAB",
        "TmagnetCalc_MotorLAB",
        "Airgap_Temperature",
        "Bearing_Temperature_F",
        "Bearing_Temperature_R",
    ]:
        bd[key] = float(gv(key))

    # ── 저항 / 인덕턴스 ──
    bd["Resistance_MotorLAB"]      = float(gv("Resistance_MotorLAB"))
    bd["EndWindingResistance_Lab"] = float(gv("EndWindingResistance_Lab"))
    bd["EndWindingInductance_Lab"] = float(gv("EndWindingInductance_Lab"))
    bd["RacRdc_MotorLAB"]          = float(gv("RacRdc_MotorLAB"))

    # ── 보정 계수 ──
    bd["coeffi"] = {
        "HybridAdjustmentFactor_ACLosses":  float(gv("HybridAdjustmentFactor_ACLosses")),
        "WindingAlpha_MotorLAB":            float(gv("WindingAlpha_MotorLAB")),
        "StatorCopperFreqCompTempExponent": float(gv("StatorCopperFreqCompTempExponent")),
        "BrTempCoeff_MotorLAB":             float(gv("BrTempCoeff_MotorLAB")),
    }

    # ── T0 기준 데이터 ──
    bd["T0data"] = {
        "Twdg_MotorLAB":            bd["Twdg_MotorLAB"],
        "Resistance_MotorLAB":      bd["Resistance_MotorLAB"],
        "EndWindingResistance_Lab": bd["EndWindingResistance_Lab"],
        "ResistanceActivePart":     bd["Resistance_MotorLAB"] - bd["EndWindingResistance_Lab"],
    }

    return bd
