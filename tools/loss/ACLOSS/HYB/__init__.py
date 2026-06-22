"""Morisco Hybrid FEA-PEEC AC Loss Package.

Implements the extended hybrid FEA-PEEC approach for calculating
eddy current losses in hairpin winding conductors, following:

    D. P. Morisco et al., "Extended Modelling Approach of Hairpin Winding
    Eddy Current Losses in High Power Density Traction Machines," IEEE ECCE 2020.

Pipeline:
    1. Quasi-static FEA (Motor-CAD Hybrid mode) → B, H, μr per element
    2. Conductor filament subdivision
    3. Impedance matrix (Dirichlet boundary inductances)
    4. Magnetization currents from FEA mesh
    5. PEEC solve → filament currents
    6. Loss calculation (P_ℓ, k_ih)
"""

from .filament import FilamentGrid, build_filament_grid, skin_depth
from .impedance import build_impedance_matrix
from .magnetization import (
    extract_magnetization_currents,
    extract_magnetization_fundamental,
    precompute_boundary_edges,
    BoundaryEdgeCache,
)
from .solver import solve_peec
from .loss import calculate_losses, current_displacement_factor
from .morisco_pipeline import MoriscoPipeline
