"""
models.py — SL Scaling 데이터 클래스 정의
MATLAB scalingFactorStruct / MotorCADGeo / ScaledMachineData 대응
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScalingFactor:
    """MATLAB scalingFactorStruct 대응.

    Attributes
    ----------
    k_radial  : 반경 방향 스케일  (Stator_Lam_Dia 등)
    k_axial   : 축 방향 스케일    (Stator_Lam_Length)
    k_winding : 권선 스케일       = (n_c/a_p) / (n_c_ref/a_p_ref)
    n_c       : 스케일드 turn per coil
    a_p       : 스케일드 병렬 경로 수
    """
    k_radial:  float
    k_axial:   float
    k_winding: float = 0.0
    n_c:       Optional[float] = None
    a_p:       Optional[float] = None


@dataclass
class MotorCADGeo:
    """MATLAB MotorCADGeo 구조체 대응 (스케일링에 필요한 필드).

    Armature_CoilStyle
        0 = 환선 (round wire)
        1 = Hairpin
    """
    # ── 기본 형상 ──
    Stator_Lam_Dia:       float = 0.0
    Stator_Lam_Length:    float = 0.0
    Motor_Length:         float = 0.0
    Housing_Dia:          float = 0.0
    Tooth_Tip_Depth:      float = 0.0
    MinBackIronThickness: float = 0.0
    # ── 절연 ──
    Insulation_Thickness: float = 0.0
    Liner_Thickness:      float = 0.0
    ConductorSeparation:  float = 0.0
    # ── 권선 ──
    Armature_CoilStyle:  int   = 0
    MagTurnsConductor:   float = 0.0   # 환선: turns per coil
    WindingLayers:       float = 0.0   # Hairpin: layers
    ParallelPaths:       float = 1.0
    Copper_Width:        float = 0.0
    Copper_Height:       float = 0.0
    NumberStrandsHand:   float = 1.0
    NumberOfCuboids_LossModel_Lab: float = 0.0
    ACConductorLossProportion_Lab: float = 0.0
    # ── 자석 배열 ──
    MagnetSeparation_Array: list = field(default_factory=list)
    MagnetThickness_Array:  list = field(default_factory=list)
    # ── 저항 / 인덕턴스 ──
    Resistance_MotorLAB:       float = 0.0
    EndWindingResistance_Lab:  float = 0.0
    EndWindingInductance_Lab:  float = 0.0
    ResistanceActivePart:      float = 0.0
    ArmatureConductorCSA:      float = 0.0
    # ── 온도 ──
    ArmatureConductor_Temperature: float = 20.0
    Twdg_MotorLAB:                 float = 20.0
    # ── Lab 파라미터 ──
    Imaxpk:            float = 0.0
    Imaxrms:           float = 0.0
    referenceSpeed:    float = 0.0
    SpeedMax_MotorLAB: float = 0.0


@dataclass
class ScaledMachineData:
    """MATLAB SLScaleMachine 반환값 구조체 대응."""
    # ── 형상 ──
    Stator_Lam_Length:    float = 0.0
    Stator_Lam_Dia:       float = 0.0
    Rotor_Lam_Length:     float = 0.0
    Magnet_Length:        float = 0.0
    Motor_Length:         float = 0.0
    Housing_Dia:          float = 0.0
    Tooth_Tip_Depth:      float = 0.0
    MinBackIronThickness: float = 0.0
    # ── 절연 ──
    Insulation_Thickness: float = 0.0
    Liner_Thickness:      float = 0.0
    ConductorSeparation:  float = 0.0
    # ── 권선 ──
    MagTurnsConductor:   float = 0.0
    WindingLayers:       float = 0.0
    ParallelPaths:       float = 1.0
    n_c_per_ap:          float = 0.0
    Copper_Width:        float = 0.0
    Copper_Height:       float = 0.0
    NumberStrandsHand:   float = 1.0
    NumberOfCuboids_LossModel_Lab: float = 0.0
    ACConductorLossProportion_Lab: float = 0.0
    # ── 자석 배열 ──
    MagnetSeparation_Array: list = field(default_factory=list)
    MagnetThickness_Array:  list = field(default_factory=list)
    # ── 저항 (20°C 기준) ──
    ResistanceActivePart20:        float = 0.0
    EndWindingResistance_Lab20:    float = 0.0
    Resistance_MotorLAB20:         float = 0.0
    ArmatureWindingResistancePh20: float = 0.0
    # ── 저항 (동작 온도 기준) ──
    ResistanceActivePart:          float = 0.0
    EndWindingResistance_Lab:      float = 0.0
    Resistance_MotorLAB:           float = 0.0
    ArmatureWindingResistancePh:   float = 0.0
    # ── 인덕턴스 ──
    EndWindingInductance_Lab: float = 0.0
    # ── 온도 ──
    Twdg_MotorLAB:                 float = 20.0
    ArmatureConductor_Temperature: float = 20.0
    TwindingCalc_MotorLAB:         float = 20.0
    # ── 참조 데이터 ──
    scalingFactor:  Optional[ScalingFactor] = None
    refMachineData: Optional[MotorCADGeo]   = None
