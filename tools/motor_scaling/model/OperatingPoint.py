from dataclasses import dataclass

@dataclass(frozen=True)
class OperatingPoint:
    speed_rpm: float
    torque_ref: float
