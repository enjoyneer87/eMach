"""Filament discretization of rectangular hairpin conductors.

Subdivides each conductor into uniform filaments whose edge lengths
are small compared to the skin depth, ensuring homogeneous current
distribution within each filament (Morisco eq. 1, Section II-A).
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass


@dataclass
class FilamentGrid:
    """Filament grid for a set of rectangular conductors.

    Attributes:
        n_conductors: number of conductors in the model
        n_filaments_per_cond: filaments per conductor (nx * ny)
        nx: subdivisions along tangential (b) direction
        ny: subdivisions along radial (h) direction
        a_fil: filament tangential width [m]
        b_fil: filament radial height [m]
        area_fil: filament cross-section area [m²]
        centers: (n_total_filaments, 2) array of (x, y) centers [m]
        conductor_ids: (n_total_filaments,) int array — which conductor each belongs to
        conductor_centers: (n_conductors, 2) array of conductor center positions [m]
        length: axial length [m]
    """
    n_conductors: int
    n_filaments_per_cond: int
    nx: int
    ny: int
    a_fil: float
    b_fil: float
    area_fil: float
    centers: np.ndarray
    conductor_ids: np.ndarray
    conductor_centers: np.ndarray
    length: float

    @property
    def n_total(self) -> int:
        return self.n_conductors * self.n_filaments_per_cond

    @property
    def rho_equiv(self) -> float:
        """Equivalent circular cross-section radius (for inductance formulas)."""
        return np.sqrt(self.area_fil / np.pi)


def skin_depth(frequency: float, sigma: float, mu_0: float = 4e-7 * np.pi) -> float:
    """Calculate skin depth δ = 1/√(μ₀·σ·ω) [m].

    Args:
        frequency: electrical frequency [Hz]
        sigma: conductivity [S/m]
        mu_0: permeability of free space [H/m]
    """
    omega = 2 * np.pi * frequency
    if omega <= 0:
        return np.inf
    return 1.0 / np.sqrt(mu_0 * sigma * omega)


def build_filament_grid(
    conductor_centers: np.ndarray,
    cond_width: float,
    cond_height: float,
    length: float,
    frequency: float,
    sigma: float,
    subdivision_ratio: float = 0.1,
    min_subdivisions: int = 3,
    max_subdivisions: int = 50,
) -> FilamentGrid:
    """Build filament grid for all conductors.

    Each conductor is subdivided so that filament edge < subdivision_ratio * δ.

    Args:
        conductor_centers: (n_cond, 2) array of (x, y) center positions [m]
        cond_width: tangential width b [m]
        cond_height: radial height h [m]
        length: axial stack length [m]
        frequency: operating electrical frequency [Hz]
        sigma: copper conductivity [S/m]
        subdivision_ratio: target a_Λ/δ ratio (paper uses 0.1)
        min_subdivisions: minimum subdivisions per direction
        max_subdivisions: maximum subdivisions per direction

    Returns:
        FilamentGrid with all filament positions computed.
    """
    conductor_centers = np.asarray(conductor_centers, dtype=float)
    if conductor_centers.ndim == 1:
        conductor_centers = conductor_centers.reshape(1, 2)
    n_cond = len(conductor_centers)

    delta = skin_depth(frequency, sigma)

    # Determine subdivision counts
    target_size = subdivision_ratio * delta
    nx = max(min_subdivisions, min(max_subdivisions, int(np.ceil(cond_width / target_size))))
    ny = max(min_subdivisions, min(max_subdivisions, int(np.ceil(cond_height / target_size))))

    a_fil = cond_width / nx
    b_fil = cond_height / ny
    area_fil = a_fil * b_fil
    n_fil_per_cond = nx * ny

    # Generate local filament positions relative to conductor center
    # x: tangential, y: radial
    x_local = np.linspace(
        -cond_width / 2 + a_fil / 2,
        cond_width / 2 - a_fil / 2,
        nx,
    )
    y_local = np.linspace(
        -cond_height / 2 + b_fil / 2,
        cond_height / 2 - b_fil / 2,
        ny,
    )
    xx, yy = np.meshgrid(x_local, y_local, indexing="xy")
    local_grid = np.column_stack([xx.ravel(), yy.ravel()])  # (nx*ny, 2)

    # Build global filament centers
    all_centers = np.zeros((n_cond * n_fil_per_cond, 2))
    cond_ids = np.zeros(n_cond * n_fil_per_cond, dtype=int)

    for ci in range(n_cond):
        start = ci * n_fil_per_cond
        end = start + n_fil_per_cond
        all_centers[start:end] = conductor_centers[ci] + local_grid
        cond_ids[start:end] = ci

    return FilamentGrid(
        n_conductors=n_cond,
        n_filaments_per_cond=n_fil_per_cond,
        nx=nx,
        ny=ny,
        a_fil=a_fil,
        b_fil=b_fil,
        area_fil=area_fil,
        centers=all_centers,
        conductor_ids=cond_ids,
        conductor_centers=conductor_centers,
        length=length,
    )
