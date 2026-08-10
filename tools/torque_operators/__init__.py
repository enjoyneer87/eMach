"""Torque operators for 2D electrical-machine field solutions. numpy only.

Two independent routes from a field to a torque, plus the diagnostics needed to
tell whether they disagree for a real reason:

    arkkio        annulus-averaged Maxwell stress tensor
    virtual_work  Coulomb local virtual work, from ONE solved field
    coenergy      the energy functional virtual work differentiates
    airgap_harmonics   how much of the gap field harmonics can actually express

Independent in principle, so agreement is evidence. Cross-checked on a 48-slot/
8-pole IPM (Motor-CAD field, 6 held-out geometries): the two operators agree to
+0.475% with a spread of 0.024 pp over five rotor positions -- a systematic
offset, not scatter.

Nothing here imports a solver, a mesher or a CAD package. Feed it node
coordinates, a triangle table, per-element materials and a nodal A.
"""
from .airgap_harmonics import (
    admissible_orders,
    age_fit,
    harmonic_residual,
    smoothness_report,
)
from .arkkio import AirgapBand, arkkio_torque, build_band
from .bh import MU0, NU0, BHCurve, linear_curve
from .coenergy import coenergy_density, total_coenergy
from .mesh import (
    ElementMaterials,
    TriMesh,
    annulus_sector_mesh,
    element_b_and_area,
)
from .virtual_work import VirtualDisplacement, coulomb_torque, radial_blend

__all__ = [
    "MU0", "NU0", "BHCurve", "linear_curve",
    "TriMesh", "ElementMaterials", "annulus_sector_mesh", "element_b_and_area",
    "coenergy_density", "total_coenergy",
    "AirgapBand", "build_band", "arkkio_torque",
    "VirtualDisplacement", "radial_blend", "coulomb_torque",
    "admissible_orders", "harmonic_residual", "age_fit", "smoothness_report",
]
