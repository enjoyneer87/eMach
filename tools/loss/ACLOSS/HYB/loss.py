"""Loss calculation from PEEC filament currents.

Computes:
  - Homogeneous loss: P_ℓ,h (uniform current in each conductor)
  - Inhomogeneous (actual) loss: P_ℓ from filament current distribution
  - Current displacement factor: k_ih = P_ℓ / P_ℓ,h  (Morisco eq. 8)
  - Per-conductor and total losses
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass

from .solver import PEECResult


@dataclass
class LossResult:
    """AC loss calculation results.

    Attributes:
        total_loss: total winding copper loss [W]
        homogeneous_loss: DC-equivalent loss (uniform current) [W]
        k_ih: current displacement factor (total_loss / homogeneous_loss)
        per_conductor_loss: (n_conductors,) loss per conductor [W]
        per_conductor_k_ih: (n_conductors,) k_ih per conductor
        per_filament_loss: (n_filaments,) loss per filament [W]
        frequency: operating frequency [Hz]
    """
    total_loss: float
    homogeneous_loss: float
    k_ih: float
    per_conductor_loss: np.ndarray
    per_conductor_k_ih: np.ndarray
    per_filament_loss: np.ndarray
    frequency: float


def calculate_losses(
    result: PEECResult,
    sigma: float,
) -> LossResult:
    """Calculate AC losses from PEEC result.

    P_ℓ = Σ_v R_vv · |i_Λ,v|² / 2   (Morisco eq. 7, time-average)

    Args:
        result: PEECResult from solve_peec()
        sigma: copper conductivity [S/m]

    Returns:
        LossResult with total and per-conductor losses
    """
    grid = result.grid
    n_fil = grid.n_total
    n_cond = grid.n_conductors
    length = grid.length

    # Filament DC resistance
    R_fil = length / (sigma * grid.area_fil)

    # Per-filament loss: P_v = R · |i_v|² / 2  (RMS for sinusoidal)
    i_abs_sq = np.abs(result.filament_currents) ** 2
    per_filament_loss = 0.5 * R_fil * i_abs_sq

    # Per-conductor loss
    per_conductor_loss = np.zeros(n_cond)
    for ci in range(n_cond):
        mask = grid.conductor_ids == ci
        per_conductor_loss[ci] = np.sum(per_filament_loss[mask])

    total_loss = np.sum(per_conductor_loss)

    # Homogeneous loss: if current were uniform in each conductor
    # P_h,k = R_dc,k · |I_k|² / 2
    # R_dc,k = l / (σ · A_conductor)
    A_cond = grid.n_filaments_per_cond * grid.area_fil
    R_dc_cond = length / (sigma * A_cond)
    I_abs_sq = np.abs(result.conductor_currents) ** 2
    per_conductor_homogeneous = 0.5 * R_dc_cond * I_abs_sq
    homogeneous_loss = np.sum(per_conductor_homogeneous)

    # Current displacement factor
    if homogeneous_loss > 0:
        k_ih = total_loss / homogeneous_loss
    else:
        k_ih = 1.0

    # Per-conductor k_ih
    per_conductor_k_ih = np.ones(n_cond)
    for ci in range(n_cond):
        if per_conductor_homogeneous[ci] > 0:
            per_conductor_k_ih[ci] = per_conductor_loss[ci] / per_conductor_homogeneous[ci]

    return LossResult(
        total_loss=total_loss,
        homogeneous_loss=homogeneous_loss,
        k_ih=k_ih,
        per_conductor_loss=per_conductor_loss,
        per_conductor_k_ih=per_conductor_k_ih,
        per_filament_loss=per_filament_loss,
        frequency=frequency_from_result(result),
    )


def current_displacement_factor(result: PEECResult, sigma: float) -> float:
    """Quick helper: return k_ih scalar from PEEC result."""
    lr = calculate_losses(result, sigma)
    return lr.k_ih


def frequency_from_result(result: PEECResult) -> float:
    """Extract frequency from PEEC result."""
    return result.frequency
