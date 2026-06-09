"""
sl_scale_machine.py — MATLAB SLScaleMachine 대응

Similarity Law(유사 법칙) 스케일링을 적용하여 ScaledMachineData를 반환한다.

저항 스케일링 법칙:
    R_active(sc) = (kw² / kr²) * ka * R_active(ref, 20°C)
    R_ew(sc)     = (kw² / kr²) * kr * R_ew(ref, 20°C)
"""
from .models import ScalingFactor, MotorCADGeo, ScaledMachineData
from .helpers import scale_resistance_by_temp


def sl_scale_machine(
    factor: ScalingFactor,
    geo: MotorCADGeo,
) -> ScaledMachineData:
    """Similarity Law 스케일링 적용.

    Parameters
    ----------
    factor : ScalingFactor   — def_scaling_factor()로 생성
    geo    : MotorCADGeo     — get_mcad_machine_data()로 생성

    Returns
    -------
    ScaledMachineData

    스케일링 법칙 요약
    ------------------
    형상 (radial)  : × k_radial
    형상 (axial)   : × k_axial
    저항 (active)  : × (k_winding² / k_radial²) × k_axial
    저항 (end-wdg) : × (k_winding² / k_radial²) × k_radial
    인덕턴스 (EW)  : × k_radial
    """
    kr = factor.k_radial
    ka = factor.k_axial
    kw = factor.k_winding

    # ref 권선 파라미터
    n_c_ref = (geo.MagTurnsConductor if geo.Armature_CoilStyle == 0
               else geo.WindingLayers)
    a_p_ref = geo.ParallelPaths

    sd = ScaledMachineData()

    # ── 공통 Lab 속성 (변경 없음) ──
    sd.NumberOfCuboids_LossModel_Lab = geo.NumberOfCuboids_LossModel_Lab
    sd.NumberStrandsHand             = geo.NumberStrandsHand
    sd.ACConductorLossProportion_Lab = geo.ACConductorLossProportion_Lab

    # ── 절연 (radial 스케일) ──
    sd.Insulation_Thickness = kr * geo.Insulation_Thickness
    sd.Liner_Thickness      = kr * geo.Liner_Thickness
    sd.ConductorSeparation  = kr * geo.ConductorSeparation

    # ── 형상 (axial) ──
    l_stk_sc             = ka * geo.Stator_Lam_Length
    sd.Stator_Lam_Length = l_stk_sc
    sd.Rotor_Lam_Length  = l_stk_sc
    sd.Magnet_Length     = l_stk_sc
    sd.Motor_Length      = l_stk_sc + (geo.Motor_Length - geo.Stator_Lam_Length)

    # ── 형상 (radial) ──
    sd.Stator_Lam_Dia       = kr * geo.Stator_Lam_Dia
    sd.Tooth_Tip_Depth      = kr * geo.Tooth_Tip_Depth
    sd.MinBackIronThickness = kr * geo.MinBackIronThickness
    sd.Housing_Dia          = sd.Stator_Lam_Dia + (geo.Housing_Dia - geo.Stator_Lam_Dia)

    # ── 자석 배열 ──
    sd.MagnetSeparation_Array = [kr * v for v in geo.MagnetSeparation_Array]
    sd.MagnetThickness_Array  = [kr * v for v in geo.MagnetThickness_Array]

    # ── 권선 ──
    sd.n_c_per_ap    = kw * (n_c_ref / a_p_ref)
    sd.ParallelPaths = factor.a_p if factor.a_p is not None else a_p_ref

    if geo.Armature_CoilStyle == 0:   # 환선
        sd.MagTurnsConductor = factor.n_c if factor.n_c is not None else n_c_ref
        sd.WindingLayers     = geo.WindingLayers
    else:                              # Hairpin
        sd.WindingLayers = factor.n_c if factor.n_c is not None else n_c_ref
        sd.Copper_Width  = kr * geo.Copper_Width
        sd.Copper_Height = kr * geo.Copper_Height

    # ── 저항 계산 (먼저 20°C 기준으로 환산) ──
    T_op    = geo.ArmatureConductor_Temperature
    R_act20 = scale_resistance_by_temp(geo.ResistanceActivePart,     20.0, T_op)
    R_ew20  = scale_resistance_by_temp(geo.EndWindingResistance_Lab, 20.0, T_op)

    kR = kw ** 2 / kr ** 2
    sd.ResistanceActivePart20        = kR * ka * R_act20
    sd.EndWindingResistance_Lab20    = kR * kr * R_ew20
    sd.Resistance_MotorLAB20         = sd.ResistanceActivePart20 + sd.EndWindingResistance_Lab20
    sd.ArmatureWindingResistancePh20 = sd.Resistance_MotorLAB20

    # ── 동작 온도로 재보정 ──
    sd.ResistanceActivePart      = scale_resistance_by_temp(sd.ResistanceActivePart20,     T_op, 20.0)
    sd.EndWindingResistance_Lab  = scale_resistance_by_temp(sd.EndWindingResistance_Lab20, T_op, 20.0)
    sd.Resistance_MotorLAB       = scale_resistance_by_temp(sd.Resistance_MotorLAB20,      T_op, 20.0)
    sd.ArmatureWindingResistancePh = sd.Resistance_MotorLAB

    # ── 인덕턴스 ──
    sd.EndWindingInductance_Lab = kr * geo.EndWindingInductance_Lab

    # ── 온도 ──
    sd.Twdg_MotorLAB                 = geo.Twdg_MotorLAB
    sd.ArmatureConductor_Temperature = T_op
    sd.TwindingCalc_MotorLAB         = geo.Twdg_MotorLAB

    # ── 참조 데이터 보존 ──
    sd.scalingFactor  = factor
    sd.refMachineData = geo

    return sd
