from dataclasses import dataclass
import numpy as np
from typing import Optional

@dataclass(frozen=True)
class RbfModelParams:
    model_type: str                   # '3D_TPS_RBF' or 'Separable_1D_2D_RBF'
    weights: np.ndarray               # RBF weights
    centers_i: np.ndarray             # current centers [A]
    centers_p: np.ndarray             # phase centers [deg]
    ls_i: float                       # length scale current
    ls_p: float                       # length scale phase
    
    # 3D RBF specific
    centers_s: Optional[np.ndarray] = None  # speed centers [kRPM]
    ls_s: Optional[float] = None            # length scale speed
    
    # Separable RBF specific
    p_coeffs: Optional[np.ndarray] = None   # speed scale polynomial coefficients [a2, a1, a0]

    def predict(self, speed_rpm: float, irms: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
        """
        Predicts the Adjustment Factor (AF) at given speed, Irms, and phase.
        """
        if self.model_type == '3D_TPS_RBF':
            return self._predict_3d(speed_rpm, irms, phase_deg)
        elif self.model_type == 'Separable_1D_2D_RBF':
            return self._predict_separable(speed_rpm, irms, phase_deg)
        else:
            raise ValueError(f"Unknown RBF model type: {self.model_type}")

    def _predict_3d(self, speed_rpm: float, irms: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
        s = np.asarray(speed_rpm, float) / 1000.0
        irm = np.asarray(irms, float)
        ph = np.asarray(phase_deg, float)
        s, irm, ph = np.broadcast_arrays(s, irm, ph)
        
        orig = s.shape
        sv = s.ravel()[:, None]
        irmv = irm.ravel()[:, None]
        phv = ph.ravel()[:, None]
        
        r2 = ((sv - self.centers_s)**2 / self.ls_s**2 +
              (irmv - self.centers_i)**2 / self.ls_i**2 +
              (phv - self.centers_p)**2 / self.ls_p**2)
        r = np.sqrt(r2)
        K = r2 * np.log(r + 1e-12)
        result = K @ self.weights
        return result.reshape(orig) if orig else float(result[0])

    def _predict_separable(self, speed_rpm: float, irms: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
        s = np.asarray(speed_rpm, float) / 1000.0
        irm = np.asarray(irms, float)
        ph = np.asarray(phase_deg, float)
        s, irm, ph = np.broadcast_arrays(s, irm, ph)
        
        orig = s.shape
        sv = s.ravel()
        irmv = irm.ravel()[:, None]
        phv = ph.ravel()[:, None]
        
        # 2D base RBF at 2 kRPM
        r2 = ((irmv - self.centers_i)**2 / self.ls_i**2 +
              (phv - self.centers_p)**2 / self.ls_p**2)
        r = np.sqrt(r2)
        K = r2 * np.log(r + 1e-12)
        g_vals = (K @ self.weights).ravel()
        
        # Speed scaling polynomial f(speed)
        f_vals = np.polyval(self.p_coeffs, sv)
        result = f_vals * g_vals
        return result.reshape(orig) if orig else float(result[0])
