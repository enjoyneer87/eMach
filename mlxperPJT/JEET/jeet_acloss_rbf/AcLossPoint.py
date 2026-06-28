from dataclasses import dataclass

@dataclass(frozen=True)
class AcLossPoint:
    speed_rpm: float
    speed_kRPM: float
    current_rms: float
    phase_deg: float
    id_A: float
    iq_A: float
    hybrid_ac_kW: float
    fea_ac_kW: float
    AF: float
