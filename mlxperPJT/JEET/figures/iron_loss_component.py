"""
IronLoss OpenMDAO component for FAST-UAV
=========================================
Geometric scaling of iron losses based on:
  Aroua et al., eTransportation 2023 (eq.15):  P_fer = KA·KR²·P⁰_fer
  For isotropic UAV scaling: KA=KR=(m/m_ref)^(1/3)  →  KA·KR² = m/m_ref

Speed-frequency scaling from SyRE calcIronLoss:
  P_fer(f) = Ph_ref·(f/f0)^expH + Pc_ref·(f/f0)^expC
  (typical: expH=1.0 for hysteresis, expC=2.0 for eddy current)

Integration into FAST-UAV performance:
  η = T·ω / (T·ω + R·I² + P_fer)

Usage
-----
Add to estimation_models.py and register in the motor group.
Reference coefficients (Ph_ref, Pc_ref, n0) must be extracted
from IronPMLossMap_dq of the reference motor (SyRE MMM .mat file).

  matlab_cmd:
    m = load('e10Turn6V261_SyreMMM_B.mat');
    whos -file 'e10Turn6V261_SyreMMM_B.mat'
    % If IronPMLossMap_dq exists:
    iron = m.IronPMLossMap_dq;
    % Sum over MTPA trajectory for representative Ph, Pc
"""

import numpy as np
import openmdao.api as om


class IronLoss(om.ExplicitComponent):
    """
    Motor iron loss scaled from a reference design using geometric scaling.

    Inputs
    ------
    data:weight:propulsion:motor:mass:estimated       [kg]   scaled motor mass
    models:weight:propulsion:motor:mass:reference     [kg]   reference motor mass
    data:propulsion:motor:speed:estimated             [rpm]  operating speed
    models:propulsion:motor:iron:Ph_ref               [W]    ref hysteresis loss at n0
    models:propulsion:motor:iron:Pc_ref               [W]    ref eddy current loss at n0
    models:propulsion:motor:iron:n0                   [rpm]  reference speed for iron map
    models:propulsion:motor:pole_pairs                [-]    number of pole pairs

    Outputs
    -------
    data:propulsion:motor:iron_loss:estimated         [W]    scaled iron loss
    """

    def setup(self):
        # --- mass scaling inputs ---
        self.add_input(
            "data:weight:propulsion:motor:mass:estimated",
            val=np.nan, units="kg"
        )
        self.add_input(
            "models:weight:propulsion:motor:mass:reference",
            val=np.nan, units="kg"
        )

        # --- operating point ---
        self.add_input(
            "data:propulsion:motor:speed:estimated",
            val=np.nan, units="rpm"
        )

        # --- reference iron loss coefficients (from SyRE IronPMLossMap_dq) ---
        self.add_input(
            "models:propulsion:motor:iron:Ph_ref",
            val=np.nan, units="W",
        )
        self.add_input(
            "models:propulsion:motor:iron:Pc_ref",
            val=np.nan, units="W",
        )
        self.add_input(
            "models:propulsion:motor:iron:n0",
            val=np.nan, units="rpm",
        )
        self.add_input(
            "models:propulsion:motor:pole_pairs",
            val=7.0, units=None,       # e10 motor: 7 pole pairs
        )

        # --- output ---
        self.add_output(
            "data:propulsion:motor:iron_loss:estimated",
            val=0.0, units="W"
        )

        self.declare_partials("*", "*")

    def compute(self, inputs, outputs):
        m     = inputs["data:weight:propulsion:motor:mass:estimated"]
        m_ref = inputs["models:weight:propulsion:motor:mass:reference"]
        n     = inputs["data:propulsion:motor:speed:estimated"]
        Ph0   = inputs["models:propulsion:motor:iron:Ph_ref"]
        Pc0   = inputs["models:propulsion:motor:iron:Pc_ref"]
        n0    = inputs["models:propulsion:motor:iron:n0"]
        p     = inputs["models:propulsion:motor:pole_pairs"]

        # Geometric scaling factor (Aroua eq.15, isotropic)
        KT = m / m_ref                  # = KA·KR²

        # Electrical frequency ratio
        f_ratio = n / n0                # f/f0  (p cancels)

        # Steinmetz: expH=1 (hysteresis), expC=2 (eddy current)
        P_fer = KT * (Ph0 * f_ratio**1 + Pc0 * f_ratio**2)

        outputs["data:propulsion:motor:iron_loss:estimated"] = P_fer

    def compute_partials(self, inputs, partials):
        m     = inputs["data:weight:propulsion:motor:mass:estimated"]
        m_ref = inputs["models:weight:propulsion:motor:mass:reference"]
        n     = inputs["data:propulsion:motor:speed:estimated"]
        Ph0   = inputs["models:propulsion:motor:iron:Ph_ref"]
        Pc0   = inputs["models:propulsion:motor:iron:Pc_ref"]
        n0    = inputs["models:propulsion:motor:iron:n0"]

        KT      = m / m_ref
        f_ratio = n / n0
        P_h     = Ph0 * f_ratio
        P_c     = Pc0 * f_ratio**2

        out = "data:propulsion:motor:iron_loss:estimated"

        partials[out, "data:weight:propulsion:motor:mass:estimated"] = \
            (P_h + P_c) / m_ref

        partials[out, "models:weight:propulsion:motor:mass:reference"] = \
            -KT * (P_h + P_c) / m_ref

        partials[out, "data:propulsion:motor:speed:estimated"] = \
            KT * (Ph0 / n0 + 2 * Pc0 * n / n0**2)

        partials[out, "models:propulsion:motor:iron:Ph_ref"] = \
            KT * f_ratio

        partials[out, "models:propulsion:motor:iron:Pc_ref"] = \
            KT * f_ratio**2

        partials[out, "models:propulsion:motor:iron:n0"] = \
            KT * (-Ph0 * n / n0**2 - 2 * Pc0 * n**2 / n0**3)


# ---------------------------------------------------------------------------
# Patch for performance_analysis.py: update efficiency calculation
# ---------------------------------------------------------------------------
# In the existing MotorEfficiency (or equivalent) component, change:
#
#   BEFORE:
#       P_loss = R * I**2
#       eta = T * omega / (T * omega + P_loss)
#
#   AFTER:
#       self.add_input("data:propulsion:motor:iron_loss:estimated", units="W")
#       P_loss = R * I**2 + inputs["data:propulsion:motor:iron_loss:estimated"]
#       eta = T * omega / (T * omega + P_loss)
#
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Extracting Ph_ref, Pc_ref from SyRE IronPMLossMap_dq (MATLAB → Python)
# ---------------------------------------------------------------------------
def extract_iron_loss_coefficients(mat_path, n0_rpm=None):
    """
    Load IronPMLossMap_dq from SyRE .mat file and return
    representative Ph_ref, Pc_ref [W] along the MTPA trajectory.

    Parameters
    ----------
    mat_path : str
        Path to SyRE MMM .mat file (e.g. e10Turn6V261_SyreMMM_B.mat)
    n0_rpm : float, optional
        Override reference speed [rpm]. If None, uses map's n0.

    Returns
    -------
    dict with keys: Ph_ref, Pc_ref, n0, f0
    """
    import scipy.io

    mat = scipy.io.loadmat(mat_path, squeeze_me=True, struct_as_record=False)

    if "IronPMLossMap_dq" not in mat:
        raise KeyError(
            "IronPMLossMap_dq not found in .mat file.\n"
            "Run Motor-CAD Lab FEA with iron loss enabled, then re-export."
        )

    iron = mat["IronPMLossMap_dq"]

    n0 = float(iron.n0) if n0_rpm is None else n0_rpm
    f0 = float(iron.f0)

    # Sum stator + rotor losses (at reference frequency f0)
    Ph_map = iron.Pfes_h + iron.Pfer_h   # hysteresis  [W] on (Id, Iq) grid
    Pc_map = iron.Pfes_c + iron.Pfer_c   # eddy current [W]

    # Representative value: mean over valid (non-NaN) dq region
    # For a proper implementation, interpolate along MTPA trajectory.
    Ph_ref = float(np.nanmean(Ph_map))
    Pc_ref = float(np.nanmean(Pc_map))

    print(f"IronPMLossMap_dq loaded from: {mat_path}")
    print(f"  n0 = {n0:.0f} rpm,  f0 = {f0:.1f} Hz")
    print(f"  Ph_ref (mean over dq) = {Ph_ref:.1f} W")
    print(f"  Pc_ref (mean over dq) = {Pc_ref:.1f} W")

    return {"Ph_ref": Ph_ref, "Pc_ref": Pc_ref, "n0": n0, "f0": f0}


if __name__ == "__main__":
    # Quick standalone test
    prob = om.Problem()
    prob.model.add_subsystem("iron", IronLoss(), promotes=["*"])
    prob.setup(force_alloc_complex=True)

    # e10 reference motor example values (adjust to actual)
    prob.set_val("data:weight:propulsion:motor:mass:estimated",       2.5, units="kg")
    prob.set_val("models:weight:propulsion:motor:mass:reference",     2.5, units="kg")
    prob.set_val("data:propulsion:motor:speed:estimated",          6000.0, units="rpm")
    prob.set_val("models:propulsion:motor:iron:Ph_ref",              30.0, units="W")
    prob.set_val("models:propulsion:motor:iron:Pc_ref",              20.0, units="W")
    prob.set_val("models:propulsion:motor:iron:n0",                6000.0, units="rpm")
    prob.set_val("models:propulsion:motor:pole_pairs",                7.0)

    prob.run_model()
    P_fer = prob.get_val("data:propulsion:motor:iron_loss:estimated", units="W")
    print(f"\nIron loss (same motor, same speed) = {P_fer[0]:.2f} W  [expect ~50 W]")

    # Scale up 2×
    prob.set_val("data:weight:propulsion:motor:mass:estimated", 5.0, units="kg")
    prob.run_model()
    P_fer2 = prob.get_val("data:propulsion:motor:iron_loss:estimated", units="W")
    print(f"Iron loss (2× mass)                = {P_fer2[0]:.2f} W  [expect ~100 W]")

    data = prob.check_partials(method="cs", compact_print=True)
