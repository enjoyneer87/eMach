from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class ScaledMotorMap:
    id_grid: np.ndarray        # 2D grid of d-axis currents [A]
    iq_grid: np.ndarray        # 2D grid of q-axis currents [A]
    lambda_d: np.ndarray       # 2D flux linkage d-axis [Vs]
    lambda_q: np.ndarray       # 2D flux linkage q-axis [Vs]
    r_dc: float                # DC resistance [Ohm]
    p_fe_grid: np.ndarray      # 2D base iron loss grid [kW]
    p_cu_ac_hybrid: np.ndarray # 2D hybrid AC copper loss grid [kW]
    k_r: float                 # radial scaling factor
    k_a: float                 # axial scaling factor
    pole_pairs: int
