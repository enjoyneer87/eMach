"""
apply_scaled_data.py — MATLAB setMcadVariable(ScaledMachineData, mcad) 대응

ScaledMachineData의 값을 Motor-CAD 인스턴스에 set_variable로 적용한다.
"""
from .models import ScaledMachineData


def apply_scaled_data_to_mcad(sd: ScaledMachineData, mcad) -> None:
    """ScaledMachineData를 Motor-CAD 인스턴스에 적용.

    Parameters
    ----------
    sd   : ScaledMachineData  — sl_scale_machine()로 생성
    mcad : ansys.motorcad.core.MotorCAD
    """
    sv = mcad.set_variable

    # ── 형상 ──
    sv("Stator_Lam_Length", sd.Stator_Lam_Length)
    sv("Stator_Lam_Dia",    sd.Stator_Lam_Dia)
    sv("Motor_Length",      sd.Motor_Length)
    sv("Housing_Dia",       sd.Housing_Dia)
    sv("Tooth_Tip_Depth",   sd.Tooth_Tip_Depth)

    # ── 절연 ──
    sv("Insulation_Thickness", sd.Insulation_Thickness)
    sv("Liner_Thickness",      sd.Liner_Thickness)
    sv("ConductorSeparation",  sd.ConductorSeparation)

    # ── 권선 ──
    sv("ParallelPaths", int(sd.ParallelPaths))

    geo = sd.refMachineData
    if geo is not None and geo.Armature_CoilStyle == 0:   # 환선
        sv("MagTurnsConductor", int(sd.MagTurnsConductor))
    else:                                                   # Hairpin
        sv("WindingLayers",  int(sd.WindingLayers))
        sv("Copper_Width",   sd.Copper_Width)
        sv("Copper_Height",  sd.Copper_Height)

    # ── 결과 요약 출력 ──
    print("스케일링 파라미터 적용 완료")
    print(f"  Stator_Lam_Dia        = {sd.Stator_Lam_Dia:.4f} mm")
    print(f"  Stator_Lam_Length     = {sd.Stator_Lam_Length:.4f} mm")
    print(f"  Resistance_MotorLAB   = {sd.Resistance_MotorLAB * 1e3:.4f} mΩ")
    print(f"  ResistanceActivePart  = {sd.ResistanceActivePart * 1e3:.4f} mΩ")
    print(f"  EndWindingResistance  = {sd.EndWindingResistance_Lab * 1e3:.4f} mΩ")
