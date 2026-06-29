import numpy as np
from ..model.ScaledMotorMap import ScaledMotorMap
from ..model.RbfModelParams import RbfModelParams

def correct_ac_loss(scaled: ScaledMotorMap, rbf: RbfModelParams, speed_rpm: float) -> np.ndarray:
    """
    Evaluates the RBF correction factor (AF) for all points in the grid and multiplies
    it by the scaled hybrid AC copper loss to obtain the physical AC copper loss map.
    """
    # 1. Calculate Irms and Phase advance from id_grid, iq_grid
    # note: id = amp * cos(phase + 90), iq = amp * sin(phase + 90)
    # amplitude = sqrt(id^2 + iq^2)
    # phase_rad = atan2(iq, id) - pi/2
    # irms = amplitude / sqrt(2)
    amp = np.sqrt(scaled.id_grid**2 + scaled.iq_grid**2)
    irms = amp / np.sqrt(2.0)
    
    # Calculate phase in degrees. Since phase_rad = atan2(iq, id) - pi/2,
    # phase_deg = atan2(iq, id)*180/pi - 90
    phase_deg = np.arctan2(scaled.iq_grid, scaled.id_grid) * 180.0 / np.pi - 90.0
    
    # 2. Predict AF using the RBF model
    af_grid = rbf.predict(speed_rpm, irms, phase_deg)
    
    # 3. Correct the AC copper loss grid
    # Corrected = Hybrid_AC * AF
    corrected_ac_loss = scaled.p_cu_ac_hybrid * af_grid
    return corrected_ac_loss
