from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class RbfModel3D:
    weights: np.ndarray
    centers_s: np.ndarray  # speed_kRPM centers
    centers_i: np.ndarray  # current_rms centers
    centers_p: np.ndarray  # phase_deg centers
    ls_s: float
    ls_i: float
    ls_p: float

    def predict(self, speed_rpm, irms_a, phase_deg):
        """Predicts the Adjustment Factor (AF) using the 3D TPS RBF model."""
        s = np.asarray(speed_rpm, float) / 1000.0
        irm = np.asarray(irms_a, float)
        ph = np.asarray(phase_deg, float)
        s, irm, ph = np.broadcast_arrays(s, irm, ph)
        
        orig = s.shape
        sv = s.ravel()[:, None]
        irmv = irm.ravel()[:, None]
        phv = ph.ravel()[:, None]
        
        r2 = (sv - self.centers_s)**2 / self.ls_s**2 + \
             (irmv - self.centers_i)**2 / self.ls_i**2 + \
             (phv - self.centers_p)**2 / self.ls_p**2
        r = np.sqrt(r2)
        K = r2 * np.log(r + 1e-12)
        result = K @ self.weights
        return result.reshape(orig) if orig else float(result[0])

    @property
    def mcad_formula(self) -> str:
        """Generates the Motor-CAD Lab formula for 3D RBF model."""
        terms = []
        n = len(self.weights)
        for j in range(n):
            w = self.weights[j]
            s_c = self.centers_s[j]
            i_c = self.centers_i[j]
            p_c = self.centers_p[j]
            
            r2_expr = (f"((Speed/1000-{s_c:.4f})**2/{self.ls_s**2:.4f}+"
                       f"(Stator_Current_Phase_RMS-{i_c:.4f})**2/{self.ls_i**2:.4f}+"
                       f"(Phase_Advance-{p_c:.4f})**2/{self.ls_p**2:.4f})")
            term = f"({w:+.6f})*({r2_expr})*log({r2_expr}**0.5+1e-12)"
            terms.append(term)
        
        formula = "Stator_Copper_Loss_AC * (\n  " + "\n  + ".join(terms) + "\n) - Stator_Copper_Loss_AC"
        return formula
