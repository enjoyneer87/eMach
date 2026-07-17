from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass(frozen=True)
class SeparableRbfModel:
    """Separable AF model: AF = f(speed) * g(I, beta) ** p(speed).

    q_coeffs is the polynomial of the spread exponent p(speed_kRPM); when it
    is None the model degenerates to the scalar-f form AF = f * g (p = 1).
    p(base_speed) = 1 by construction, so at the anchor speed the two forms
    coincide. p != 1 lets the surface's operating-point spread widen (p > 1)
    or compress (p < 1) relative to the base-speed shape, which a scalar f
    cannot express.
    """
    w_g: np.ndarray
    base_centers_i: np.ndarray  # current_rms base centers (base speed)
    base_centers_p: np.ndarray  # phase_deg base centers (base speed)
    ls_i: float
    ls_p: float
    p_coeffs: np.ndarray        # speed level polynomial f(s): [a2, a1, a0]
    q_coeffs: Optional[np.ndarray] = None  # spread exponent p(s): [b2, b1, b0]

    #: g is clamped here before exponentiation — TPS extrapolation outside
    #: the sampled hull can dip to zero/negative, and p > 1 amplifies it.
    G_CLIP = 1e-3

    def predict_g(self, irms, phase):
        """Predicts the base 2D TPS RBF model g(Irms, phase_deg)."""
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
        """Predicts AF = f(speed) * g(Irms, phase_deg) ** p(speed)."""
        s = np.asarray(speed_rpm, float) / 1000.0
        irm = np.asarray(irms, float)
        ph = np.asarray(phase, float)
        s, irm, ph = np.broadcast_arrays(s, irm, ph)

        orig = s.shape
        sv = s.ravel()
        irmv = irm.ravel()
        phv = ph.ravel()

        g_vals = self.predict_g(irmv, phv)
        f_vals = np.polyval(self.p_coeffs, sv)
        if self.q_coeffs is None:
            result = f_vals * g_vals
        else:
            p_vals = np.polyval(self.q_coeffs, sv)
            g_pos = np.clip(g_vals, self.G_CLIP, None)
            result = f_vals * g_pos**p_vals
        return result.reshape(orig) if orig else float(result[0])

    @property
    def mcad_formula(self) -> str:
        """Generates the Motor-CAD Lab formula for Separable RBF model.

        Exponent form assumes g > 0 over the Lab operating region (holds
        inside the sampled current range; the low-current core where TPS
        extrapolation may cross zero carries negligible AC loss).
        """
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

        if self.q_coeffs is None:
            core = f"({f_expr}) * (\n    {g_expr}\n  )"
        else:
            b2, b1, b0 = self.q_coeffs
            p_expr = (f"({b2:+.6f}*(Speed/1000)**2{b1:+.6f}*(Speed/1000)"
                      f"{b0:+.6f})")
            core = f"({f_expr}) * (\n    {g_expr}\n  )**({p_expr})"

        formula = (f"Stator_Copper_Loss_AC * (\n  {core}\n)"
                   f" - Stator_Copper_Loss_AC")
        return formula
