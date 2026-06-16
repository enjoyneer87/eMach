"""PEEC solver for filament currents.

Solves Morisco eq. 3:
    i_Λ = Z_Λ^{-1} · C · (C^T · Z_Λ^{-1} · C)^{-1} · I

where:
    Z_Λ: impedance matrix (n_filaments × n_filaments)
    C: connectivity matrix (n_filaments × n_conductors)
    I: conductor total currents (n_conductors,) — imposed

Extended (Morisco 2020 PhD Ch.5 ELMO):
    - FFT decomposition of i_mag(t) → per-harmonic PEEC solve
    - Faithful to Morisco method: no leakage subtraction applied
"""
from __future__ import annotations

import numpy as np
from numpy.linalg import solve, inv
from numpy.fft import rfft
from dataclasses import dataclass

from .filament import FilamentGrid
from .impedance import build_impedance_matrix, build_connectivity_matrix
from .magnetization import MagnetizationCurrent


MU_0 = 4e-7 * np.pi


@dataclass
class PEECResult:
    """Result of the PEEC solve.

    Attributes:
        filament_currents: (n_filaments,) complex filament currents [A]
        conductor_currents: (n_conductors,) imposed total currents [A]
        impedance_matrix: Z_Λ matrix used
        grid: FilamentGrid used
        frequency: operating frequency [Hz]
    """
    filament_currents: np.ndarray
    conductor_currents: np.ndarray
    impedance_matrix: np.ndarray
    grid: FilamentGrid
    frequency: float


def solve_peec(
    grid: FilamentGrid,
    conductor_currents: np.ndarray,
    frequency: float,
    sigma: float,
    slot_boundary_radius: float | None = None,
    magnetization_currents: MagnetizationCurrent | None = None,
) -> PEECResult:
    """Solve the PEEC system for filament currents.

    Implements Morisco eq. 3:
        i_Λ = Z_Λ^{-1} · C · (C^T · Z_Λ^{-1} · C)^{-1} · I

    For the extended model with magnetization currents, the magnetization
    current contribution is added as additional voltage sources in the
    impedance equation (mutual inductance coupling to magnetization filaments).

    Args:
        grid: FilamentGrid describing conductor discretization
        conductor_currents: (n_conductors,) complex total currents [A]
        frequency: electrical frequency [Hz]
        sigma: copper conductivity [S/m]
        slot_boundary_radius: slot boundary radius for Dirichlet formulas [m]
        magnetization_currents: optional magnetization currents from FEA

    Returns:
        PEECResult with filament current distribution
    """
    conductor_currents = np.asarray(conductor_currents, dtype=complex)
    n_cond = grid.n_conductors
    assert len(conductor_currents) == n_cond, (
        f"Expected {n_cond} conductor currents, got {len(conductor_currents)}"
    )

    # Build impedance matrix
    Z = build_impedance_matrix(
        grid, frequency, sigma,
        slot_boundary_radius=slot_boundary_radius,
    )

    # Build connectivity matrix
    C = build_connectivity_matrix(grid)

    # Add magnetization voltage sources if provided
    V_mag = np.zeros(grid.n_total, dtype=complex)
    if magnetization_currents is not None and len(magnetization_currents.currents) > 0:
        omega = 2.0 * np.pi * frequency
        V_mag = _compute_magnetization_voltage(
            grid, magnetization_currents, omega,
            dirichlet_radius=slot_boundary_radius,
        )

    # Solve: Z·i = C·u + V_mag
    # where u = Lagrange multiplier (conductor voltage)
    # Using the formula: i_Λ = Z^{-1}·C·(C^T·Z^{-1}·C)^{-1}·I + Z^{-1}·V_mag correction

    # Standard PEEC solve (eq. 3)
    Z_inv = inv(Z)
    Z_inv_C = Z_inv @ C  # (n_fil × n_cond)
    CZ_inv_C = C.T @ Z_inv_C  # (n_cond × n_cond)

    # Filament currents from imposed conductor currents
    i_imposed = Z_inv_C @ solve(CZ_inv_C, conductor_currents)

    # Filament currents from magnetization voltage sources
    if np.any(V_mag != 0):
        # Magnetization effect: additional current = Z^{-1}·V_mag
        # projected to maintain conductor current constraints
        i_mag_raw = Z_inv @ V_mag
        # Remove the component that changes total conductor currents
        delta_I = C.T @ i_mag_raw
        i_correction = Z_inv_C @ solve(CZ_inv_C, -delta_I)
        i_magnetization = i_mag_raw + i_correction
    else:
        i_magnetization = np.zeros(grid.n_total, dtype=complex)

    filament_currents = i_imposed + i_magnetization

    return PEECResult(
        filament_currents=filament_currents,
        conductor_currents=conductor_currents,
        impedance_matrix=Z,
        grid=grid,
        frequency=frequency,
    )


def _compute_magnetization_voltage(
    grid: FilamentGrid,
    mag_currents: MagnetizationCurrent,
    omega: float,
    dirichlet_radius: float | None = None,
) -> np.ndarray:
    """Compute induced voltage on each filament from magnetization currents.

    Morisco 2019 Section II-F.2: The mutual inductance between magnetization
    filaments (n+1...n+q) and conductor filaments (1...n) uses the SAME
    Dirichlet Green's function (eq. 27/43) as filament-filament coupling.

    V_v = jω · Σ_θ L(v, mag_θ) · i_mag,θ

    Args:
        grid: FilamentGrid with conductor filament positions
        mag_currents: MagnetizationCurrent with positions and currents
        omega: angular frequency [rad/s]
        dirichlet_radius: R for Dirichlet boundary. If None, uses Neumann.

    Returns:
        V: (n_filaments,) complex voltage vector [V]
    """
    n_fil = grid.n_total
    length = grid.length
    mag_pos = mag_currents.positions  # (n_mag, 2)
    mag_I = mag_currents.currents  # (n_mag,) complex

    if len(mag_I) == 0:
        return np.zeros(n_fil, dtype=complex)

    # Vectorized mutual inductance computation
    # fil_centers: (n_fil, 2), mag_pos: (n_mag, 2)
    if dirichlet_radius is not None:
        R = dirichlet_radius
        # Dirichlet mutual inductance (Morisco eq. 27/43, vectorized)
        # L_vw = -(μ₀l)/(2π) · [ln|ξ_v - ξ_w| - 0.5·ln(|ξ_v|²|ξ_w|² - 2·Re(ξ_v·conj(ξ_w)) + 1)]
        xi_fil = (grid.centers[:, 0] + 1j * grid.centers[:, 1]) / R  # (n_fil,)
        xi_mag = (mag_pos[:, 0] + 1j * mag_pos[:, 1]) / R  # (n_mag,)

        # Pairwise: (n_fil, n_mag)
        xi_f = xi_fil[:, np.newaxis]  # (n_fil, 1)
        xi_m = xi_mag[np.newaxis, :]  # (1, n_mag)

        diff = np.abs(xi_f - xi_m)  # (n_fil, n_mag)
        diff = np.maximum(diff, 1e-15)

        abs_f_sq = np.abs(xi_fil)**2  # (n_fil,)
        abs_m_sq = np.abs(xi_mag)**2  # (n_mag,)

        image_arg = (abs_f_sq[:, np.newaxis] * abs_m_sq[np.newaxis, :]
                     - 2.0 * np.real(xi_f * np.conj(xi_m)) + 1.0)
        image_arg = np.maximum(image_arg, 1e-30)

        L_mutual_mat = -(MU_0 * length) / (2 * np.pi) * (
            np.log(diff) - 0.5 * np.log(image_arg)
        )  # (n_fil, n_mag)
    else:
        # Neumann (free-space) mutual inductance, vectorized
        dx = grid.centers[:, 0, np.newaxis] - mag_pos[np.newaxis, :, 0]  # (n_fil, n_mag)
        dy = grid.centers[:, 1, np.newaxis] - mag_pos[np.newaxis, :, 1]
        dist_mat = np.sqrt(dx**2 + dy**2)
        dist_mat = np.maximum(dist_mat, 1e-10)

        L_mutual_mat = (MU_0 * length) / (2 * np.pi) * (
            np.log(2 * length / dist_mat) - 1.0
        )  # (n_fil, n_mag)

    # V_v = jω · Σ_θ L(v, θ) · i_mag,θ
    V = 1j * omega * (L_mutual_mat @ mag_I)

    return V


def subtract_slot_leakage(
    mag_currents: MagnetizationCurrent,
    grid: FilamentGrid,
    conductor_currents: np.ndarray,
    slot_width: float,
    mur_at_edges: np.ndarray,
    radial_axis: int = 1,
) -> MagnetizationCurrent:
    """DEPRECATED: Not part of Morisco's method.

    Morisco PhD thesis (2020) Ch.5 ELMO program does NOT include
    slot leakage subtraction. The overestimation from uniform-J
    assumption in static FEM is acknowledged (p.144) but not corrected.

    This function is retained as a no-op stub for API compatibility.
    """
    return mag_currents


def compute_leakage_voltage(
    grid: FilamentGrid,
    conductor_currents: np.ndarray,
    slot_width: float,
    mur_at_edges: np.ndarray,
    mag_positions: np.ndarray,
    edge_lengths: np.ndarray,
    omega: float,
    dirichlet_radius: float | None = None,
    radial_axis: int = 1,
) -> np.ndarray:
    """DEPRECATED: Not part of Morisco's method.

    Morisco PhD thesis (2020) Ch.5 does NOT include V_leak subtraction.
    Returns zeros for API compatibility.

    See thesis p.144: overestimation is acknowledged but deemed negligible
    at Morisco's operating points (1-4%).
    """
    n_fil = grid.n_total
    return np.zeros(n_fil, dtype=complex)


@dataclass
class FFTPEECResult:
    """Result of the FFT-based harmonic PEEC solve.

    Attributes:
        filament_currents_per_harmonic: dict {n: (n_fil,) complex phasor}
        k_ih: current displacement factor (time-averaged)
        power_per_harmonic: dict {n: float [W]}
        power_total: total AC loss [W]
        power_dc: homogeneous DC loss [W]
        harmonic_indices: array of significant harmonic orders
    """
    filament_currents_per_harmonic: dict
    k_ih: float
    power_per_harmonic: dict
    power_total: float
    power_dc: float
    harmonic_indices: np.ndarray


def solve_peec_fft(
    grid: FilamentGrid,
    conductor_currents: np.ndarray,
    frequency: float,
    sigma: float,
    i_mag_timeseries: np.ndarray,
    mag_positions: np.ndarray,
    slot_boundary_radius: float | None = None,
    slot_width: float | None = None,
    mur_at_edges: np.ndarray | None = None,
    edge_lengths: np.ndarray | None = None,
    significance_threshold: float = 0.01,
    radial_axis: int = 1,
) -> FFTPEECResult:
    """FFT-based harmonic PEEC solver (Morisco 2020, Ch.5 ELMO).

    Decomposes the magnetization current time series via DFT, removes
    DC, and solves PEEC independently for each significant harmonic
    with the correct Z(nω₁).

    Note: slot_width, mur_at_edges, edge_lengths are retained for API
    compatibility but ignored (leakage subtraction removed — not part
    of Morisco's method).

    Args:
        grid: FilamentGrid with conductor geometry
        conductor_currents: (n_cond,) complex terminal currents [A] (fundamental)
        frequency: fundamental electrical frequency [Hz]
        sigma: copper conductivity [S/m]
        i_mag_timeseries: (n_steps, n_mag) real magnetization currents per step
        mag_positions: (n_mag, 2) edge midpoint positions [m] (slot-local)
        slot_boundary_radius: R for Dirichlet boundary [m]
        slot_width: DEPRECATED (ignored). Retained for API compatibility.
        mur_at_edges: DEPRECATED (ignored). Retained for API compatibility.
        edge_lengths: DEPRECATED (ignored). Retained for API compatibility.
        significance_threshold: fraction of fundamental to include harmonic
        radial_axis: 0=x or 1=y for radial in slot-local coords

    Returns:
        FFTPEECResult with per-harmonic filament currents and loss data.
    """
    from .impedance import build_impedance_matrix, build_connectivity_matrix

    conductor_currents = np.asarray(conductor_currents, dtype=complex)
    n_cond = grid.n_conductors
    n_fil = grid.n_total
    n_steps = i_mag_timeseries.shape[0]
    omega = 2.0 * np.pi * frequency
    length = grid.length

    # ─── (1) FFT decomposition ───
    I_mag_fft = rfft(i_mag_timeseries, axis=0)  # (n_freq, n_mag)
    n_freq = I_mag_fft.shape[0]

    # Phasor normalization (peak amplitude)
    I_mag_phasor = I_mag_fft * (2.0 / n_steps)
    I_mag_phasor[0] /= 2.0  # DC: no doubling
    if n_steps % 2 == 0:
        I_mag_phasor[-1] /= 2.0  # Nyquist

    # Select significant harmonics (exclude DC=0)
    spectrum_max = np.abs(I_mag_phasor).max(axis=1)
    fund_mag = spectrum_max[1] if n_freq > 1 else 1.0
    significant = spectrum_max > (significance_threshold * fund_mag)
    significant[0] = False  # Remove DC — no dΦ/dt from static M
    harmonic_indices = np.where(significant)[0]

    # ─── (2) Pre-compute L_mutual (filament ↔ mag source) ───
    n_mag = mag_positions.shape[0]
    if slot_boundary_radius is not None:
        R = slot_boundary_radius
        xi_fil = (grid.centers[:, 0] + 1j * grid.centers[:, 1]) / R
        xi_mag = (mag_positions[:, 0] + 1j * mag_positions[:, 1]) / R
        xi_f = xi_fil[:, np.newaxis]
        xi_m = xi_mag[np.newaxis, :]
        diff = np.maximum(np.abs(xi_f - xi_m), 1e-15)
        abs_f_sq = np.abs(xi_fil)**2
        abs_m_sq = np.abs(xi_mag)**2
        image_arg = np.maximum(
            abs_f_sq[:, np.newaxis] * abs_m_sq[np.newaxis, :]
            - 2.0 * np.real(xi_f * np.conj(xi_m)) + 1.0,
            1e-30,
        )
        L_mutual = -(MU_0 * length) / (2 * np.pi) * (
            np.log(diff) - 0.5 * np.log(image_arg)
        )
    else:
        dx = grid.centers[:, 0, np.newaxis] - mag_positions[np.newaxis, :, 0]
        dy = grid.centers[:, 1, np.newaxis] - mag_positions[np.newaxis, :, 1]
        dist = np.maximum(np.sqrt(dx**2 + dy**2), 1e-10)
        L_mutual = (MU_0 * length) / (2 * np.pi) * (
            np.log(2 * length / dist) - 1.0
        )

    # ─── (3) Build R and L matrices (frequency-independent) ───
    Z_base = build_impedance_matrix(
        grid, frequency, sigma,
        slot_boundary_radius=slot_boundary_radius,
    )
    R_matrix = np.real(Z_base)
    L_matrix = np.imag(Z_base) / omega
    C = build_connectivity_matrix(grid)

    # DC loss reference
    R_fil = length / (sigma * grid.area_fil)
    # i_imposed at fundamental (for P_dc reference)
    Z_inv_base = inv(Z_base)
    ZiC = Z_inv_base @ C
    CZiC = C.T @ ZiC
    i_imposed = ZiC @ solve(CZiC, conductor_currents)
    P_dc = 0.5 * R_fil * np.sum(np.abs(i_imposed)**2)
    # Better P_dc: uniform distribution
    A_cond = grid.area_fil * grid.n_filaments_per_cond
    R_dc_cond = length / (sigma * A_cond)
    P_dc = 0.5 * R_dc_cond * np.sum(np.abs(conductor_currents)**2)

    # ─── (4) Per-harmonic PEEC solve ───
    i_per_harmonic = {}
    P_per_harmonic = {}

    for n_h in harmonic_indices:
        omega_n = n_h * omega
        Z_n = R_matrix + 1j * omega_n * L_matrix
        Z_n_inv = inv(Z_n)
        ZnC = Z_n_inv @ C
        CZnC = C.T @ ZnC

        # V_mag,n = jnω · L · Î_mag[n]
        I_mag_n = I_mag_phasor[n_h]
        V_n = 1j * omega_n * (L_mutual @ I_mag_n)

        # Constrained solve
        i_raw = Z_n_inv @ V_n
        delta_I = C.T @ i_raw
        i_corr = ZnC @ solve(CZnC, -delta_I)
        i_mag_n = i_raw + i_corr

        if n_h == 1:
            # Fundamental: add imposed (terminal) current
            i_imp = ZnC @ solve(CZnC, conductor_currents)
            i_per_harmonic[n_h] = i_imp + i_mag_n
        else:
            # Higher harmonics: magnetization-only (net I_cond = 0)
            i_per_harmonic[n_h] = i_mag_n

        P_per_harmonic[n_h] = 0.5 * R_fil * np.sum(
            np.abs(i_per_harmonic[n_h])**2
        )

    P_total = sum(P_per_harmonic.values())
    k_ih = P_total / P_dc if P_dc > 0 else float('inf')

    return FFTPEECResult(
        filament_currents_per_harmonic=i_per_harmonic,
        k_ih=k_ih,
        power_per_harmonic=P_per_harmonic,
        power_total=P_total,
        power_dc=P_dc,
        harmonic_indices=harmonic_indices,
    )
