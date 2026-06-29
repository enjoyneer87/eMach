from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class SeparableRbfModel:
    w_g: np.ndarray
    base_centers_i: np.ndarray  # current_rms base centers (2kRPM)
    base_centers_p: np.ndarray  # phase_deg base centers (2kRPM)
    ls_i: float
    ls_p: float
    p_coeffs: np.ndarray        # coefficients of speed scale polynomial: [a2, a1, a0]

    def predict_g(self, irms, phase):
        """Predicts the base 2D TPS RBF model g(Irms, phase_deg) at 2 kRPM."""
        I = np.asarray(irms, float)
        theta = np.asarray(phase, float)
        I, theta = np.broadcast_arrays(I, theta)
        
        orig = I.shape
        Iv = I.ravel()[:, None]
        thv = theta.ravel()[:, None]
        
        r2 = (Iv - self.base_centers_i)**2 / self.ls_i**2 + \
             (thv - self.base_centers_p)**2 / self.ls_p**2
        r = np.sqrt(r2)
        K = r2 * np.log(r + 1e-12)
        result = K @ self.w_g
        return result.reshape(orig) if orig else float(result[0])

    def predict(self, speed_rpm, irms, phase):
        """Predicts the Adjustment Factor (AF) = f(speed) * g(Irms, phase_deg)."""
        s = np.asarray(speed_rpm, float) / 1000.0
        irm = np.asarray(irms, float)
        ph = np.asarray(phase, float)
        s, irm, ph = np.broadcast_arrays(s, irm, ph)
        
        orig = s.shape
        sv = s.ravel()
        irmv = irm.ravel()
        phv = ph.ravel()
        
        g_vals = self.predict_g(irmv, phv)
        
        # Evaluate f(speed) polyval
        f_vals = np.polyval(self.p_coeffs, sv)
        result = f_vals * g_vals
        return result.reshape(orig) if orig else float(result[0])

    @property
    def mcad_formula(self) -> str:
        """Generates the Motor-CAD Lab formula for Separable RBF model."""
        terms_g = []
        n_base = len(self.w_g)
        for j in range(n_base):
            w = self.w_g[j]
            i_c = self.base_centers_i[j]
            p_c = self.base_centers_p[j]
            
            r2_expr = (f"((Stator_Current_Phase_RMS-{i_c:.4f})**2/{self.ls_i**2:.4f}+"
                       f"(Phase_Advance-{p_c:.4f})**2/{self.ls_p**2:.4f})")
            term = f"({w:+.6f})*({r2_expr})*log({r2_expr}**0.5+1e-12)"
            terms_g.append(term)
            
        g_expr = " + ".join(terms_g)
        
        # f_expr format coefficients
        a2, a1, a0 = self.p_coeffs
        f_expr = f"({a2:+.6f}*(Speed/1000)**2{a1:+.6f}*(Speed/1000){a0:+.6f})"
        
        formula = f"Stator_Copper_Loss_AC * (\n  ({f_expr}) * (\n    {g_expr}\n  )\n) - Stator_Copper_Loss_AC"
        return formula
