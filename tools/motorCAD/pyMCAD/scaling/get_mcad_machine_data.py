"""
get_mcad_machine_data.py — MATLAB defMCADMachineData4Scaling 대응

Motor-CAD 인스턴스에서 스케일링에 필요한 기하/권선/저항 변수를 읽어
MotorCADGeo 객체로 반환한다.
"""
from .models import MotorCADGeo
from .helpers import parse_mcad_colon_str


def get_mcad_machine_data(mcad) -> MotorCADGeo:
    """Motor-CAD 인스턴스에서 스케일링 관련 변수를 읽어 MotorCADGeo를 반환.

    Parameters
    ----------
    mcad : ansys.motorcad.core.MotorCAD

    Returns
    -------
    MotorCADGeo
    """
    gv = mcad.get_variable
    geo = MotorCADGeo()

    # ── 기본 형상 ──
    geo.Stator_Lam_Dia    = float(gv("Stator_Lam_Dia"))
    geo.Stator_Lam_Length = float(gv("Stator_Lam_Length"))
    geo.Motor_Length      = float(gv("Motor_Length"))
    geo.Housing_Dia       = float(gv("Housing_Dia"))
    geo.Tooth_Tip_Depth   = float(gv("Tooth_Tip_Depth"))

    # ── 권선 타입 공통 ──
    geo.Armature_CoilStyle = int(gv("Armature_CoilStyle"))
    geo.ParallelPaths      = float(gv("ParallelPaths"))
    geo.WindingLayers      = float(gv("WindingLayers"))
    geo.NumberStrandsHand  = float(gv("NumberStrandsHand"))
    geo.ArmatureConductorCSA = float(gv("ArmatureConductorCSA"))

    # ── 권선 타입별 ──
    if geo.Armature_CoilStyle == 0:   # 환선
        geo.MagTurnsConductor = float(gv("MagTurnsConductor"))
    else:                              # Hairpin
        geo.Copper_Width  = float(gv("Copper_Width"))
        geo.Copper_Height = float(gv("Copper_Height"))

    # ── 절연 ──
    geo.Insulation_Thickness = float(gv("Insulation_Thickness"))
    geo.Liner_Thickness      = float(gv("Liner_Thickness"))
    geo.ConductorSeparation  = float(gv("ConductorSeparation"))

    # ── 자석 배열 ──
    geo.MagnetSeparation_Array = parse_mcad_colon_str(gv("MagnetSeparation_Array"))
    geo.MagnetThickness_Array  = parse_mcad_colon_str(gv("MagnetThickness_Array"))

    # ── 저항 / 인덕턴스 ──
    geo.Resistance_MotorLAB      = float(gv("Resistance_MotorLAB"))
    geo.EndWindingResistance_Lab = float(gv("EndWindingResistance_Lab"))
    geo.EndWindingInductance_Lab = float(gv("EndWindingInductance_Lab"))
    geo.ResistanceActivePart     = geo.Resistance_MotorLAB - geo.EndWindingResistance_Lab

    # ── 온도 ──
    geo.ArmatureConductor_Temperature = float(gv("ArmatureConductor_Temperature"))
    geo.Twdg_MotorLAB                 = float(gv("Twdg_MotorLAB"))

    # ── Lab 손실 파라미터 ──
    geo.NumberOfCuboids_LossModel_Lab = float(gv("NumberOfCuboids_LossModel_Lab"))
    geo.ACConductorLossProportion_Lab = float(gv("ACConductorLossProportion_Lab"))

    return geo
