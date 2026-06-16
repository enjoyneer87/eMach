"""Impedance matrix construction for the PEEC model.

Builds the complex impedance matrix Z_Λ ∈ C^{n×n} containing:
  - Diagonal: R_vv + jωL_vv (filament resistance + self inductance)
  - Off-diagonal: jωL_vw (mutual inductance between filaments)

Inductances use the Dirichlet boundary value problem for the 2D Laplacian
(Morisco eqs. 9, 10).

Note on slot_boundary_radius (= R):
    Per Morisco 2019 (IEEE Trans. Mag., Vol.55 No.9), Section IV:
    R = l (axial length of the calculation domain), NOT the slot wall radius.
    The iron wall effect enters ONLY via magnetization currents (Section II-F).
    Using the slot wall dimension as R double-counts the iron confinement effect.
"""
from __future__ import annotations

import numpy as np
from .filament import FilamentGrid


MU_0 = 4e-7 * np.pi


def _dirichlet_self_inductance(
    length: float,
    xi_norm: complex,
    rho_norm: float,
) -> float:
    """Self inductance via Dirichlet boundary (Morisco eq. 9).

    L_vv = -(μ₀·l)/(2π) · [log_e(ρ) - 0.5·log_e((1-|ξ'|²)² + (|ξ'|·ρ)²)]

    Args:
        length: filament axial length [m]
        xi_norm: normalized filament center position ξ'/R (complex)
        rho_norm: normalized cross-section radius ρ/R
    """
    abs_xi = abs(xi_norm)
    term1 = np.log(rho_norm)
    term2 = 0.5 * np.log((1.0 - abs_xi**2)**2 + (abs_xi * rho_norm)**2)
    return -(MU_0 * length) / (2 * np.pi) * (term1 - term2)


def _dirichlet_mutual_inductance(
    length: float,
    xi_v: complex,
    xi_w: complex,
) -> float:
    """Mutual inductance via Dirichlet boundary (Morisco eq. 10).

    L_vw = -(μ₀·l)/(2π) · [log_e|ξ-ξ'| - 0.5·log_e(|ξ|²|ξ'|² - 2·ξ·ξ' + 1)]

    Args:
        length: filament axial length [m]
        xi_v: normalized position of filament v (complex)
        xi_w: normalized position of filament w (complex)
    """
    diff = abs(xi_v - xi_w)
    if diff < 1e-15:
        diff = 1e-15
    term1 = np.log(diff)
    # Image term: |ξ|²|ξ'|² - 2·Re(ξ·conj(ξ')) + 1
    image_arg = (abs(xi_v)**2 * abs(xi_w)**2
                 - 2.0 * (xi_v * np.conj(xi_w)).real + 1.0)
    if image_arg < 1e-30:
        image_arg = 1e-30
    term2 = 0.5 * np.log(image_arg)
    return -(MU_0 * length) / (2 * np.pi) * (term1 - term2)


def _neumann_self_inductance(length: float, rho: float) -> float:
    """Neumann formula self inductance (free-space, no boundary).

    L_vv ≈ (μ₀·l)/(2π) · [ln(2l/ρ) - 1 + ρ/(4l)]
    Simplified for l >> ρ.
    """
    if rho < 1e-15:
        rho = 1e-15
    return (MU_0 * length) / (2 * np.pi) * (np.log(2 * length / rho) - 1.0)


def _neumann_mutual_inductance(length: float, distance: float) -> float:
    """Neumann formula mutual inductance (free-space, parallel filaments).

    L_vw ≈ (μ₀·l)/(2π) · [ln(2l/d) - 1]  for l >> d
    """
    if distance < 1e-15:
        distance = 1e-15
    return (MU_0 * length) / (2 * np.pi) * (np.log(2 * length / distance) - 1.0)


def build_impedance_matrix(
    grid: FilamentGrid,
    frequency: float,
    sigma: float,
    slot_boundary_radius: float | None = None,
    use_dirichlet: bool = True,
) -> np.ndarray:
    """Build the PEEC impedance matrix Z_Λ ∈ C^{n×n} (vectorized).

    Z_Λ[v,v] = R_vv + jω·L_vv
    Z_Λ[v,w] = jω·L_vw   (v ≠ w)

    Args:
        grid: FilamentGrid with filament positions
        frequency: electrical frequency [Hz]
        sigma: conductor conductivity [S/m]
        slot_boundary_radius: radius R for Dirichlet boundary normalization [m].
            Morisco 2019: R = l (axial stack length) = calculation domain radius.
            NOT the slot wall distance. Iron confinement enters via magnetization currents.
            If None, uses free-space (Neumann) approximation.
        use_dirichlet: if True and slot_boundary_radius provided, use Dirichlet formulas.

    Returns:
        Z_Λ: complex impedance matrix (n_total × n_total)
    """
    n = grid.n_total
    omega = 2.0 * np.pi * frequency
    length = grid.length

    # Filament resistance: R = l / (σ · A)
    R_fil = length / (sigma * grid.area_fil)

    if use_dirichlet and slot_boundary_radius is not None:
        R_bound = slot_boundary_radius
        rho_norm = grid.rho_equiv / R_bound

        # Normalized positions as complex array
        xi_all = (grid.centers[:, 0] + 1j * grid.centers[:, 1]) / R_bound
        abs_xi = np.abs(xi_all)

        # --- Self inductance (vectorized, eq. 9) ---
        term1 = np.log(rho_norm)
        term2 = 0.5 * np.log((1.0 - abs_xi**2)**2 + (abs_xi * rho_norm)**2)
        L_self_vec = -(MU_0 * length) / (2 * np.pi) * (term1 - term2)

        # --- Mutual inductance (vectorized, eq. 10) ---
        # Pairwise |ξ_v - ξ_w|
        xi_row = xi_all[:, np.newaxis]  # (n, 1)
        xi_col = xi_all[np.newaxis, :]  # (1, n)
        diff_mat = np.abs(xi_row - xi_col)  # (n, n)
        diff_mat = np.maximum(diff_mat, 1e-15)

        # Image term: |ξ_v|²|ξ_w|² - 2·Re(ξ_v·conj(ξ_w)) + 1
        abs_v_sq = np.abs(xi_all)**2
        image_arg = (abs_v_sq[:, np.newaxis] * abs_v_sq[np.newaxis, :]
                     - 2.0 * np.real(xi_row * np.conj(xi_col)) + 1.0)
        image_arg = np.maximum(image_arg, 1e-30)

        L_mutual_mat = -(MU_0 * length) / (2 * np.pi) * (
            np.log(diff_mat) - 0.5 * np.log(image_arg)
        )

        # Build Z
        Z = 1j * omega * L_mutual_mat
        np.fill_diagonal(Z, R_fil + 1j * omega * L_self_vec)

    else:
        # Free-space (Neumann) approximation — vectorized
        rho = grid.rho_equiv
        L_self = (MU_0 * length) / (2 * np.pi) * (np.log(2 * length / rho) - 1.0)

        # Pairwise distances
        dx = grid.centers[:, 0, np.newaxis] - grid.centers[np.newaxis, :, 0]
        dy = grid.centers[:, 1, np.newaxis] - grid.centers[np.newaxis, :, 1]
        dist_mat = np.sqrt(dx**2 + dy**2)
        dist_mat = np.maximum(dist_mat, 1e-15)

        L_mutual_mat = (MU_0 * length) / (2 * np.pi) * (
            np.log(2 * length / dist_mat) - 1.0
        )

        Z = 1j * omega * L_mutual_mat
        np.fill_diagonal(Z, R_fil + 1j * omega * L_self)

    return Z


def build_connectivity_matrix(grid: FilamentGrid) -> np.ndarray:
    """Build connectivity matrix C that maps filaments to conductors.

    C ∈ R^{n_filaments × n_conductors}, where C[v, k] = 1 if filament v
    belongs to conductor k.

    Used in: i_Λ = Z_Λ^{-1}·C·(C^T·Z_Λ^{-1}·C)^{-1}·I  (Morisco eq. 3)
    """
    n = grid.n_total
    n_cond = grid.n_conductors
    C = np.zeros((n, n_cond))
    for v in range(n):
        C[v, grid.conductor_ids[v]] = 1.0
    return C
