"""Isotropic BH curve with an exact coenergy integral. numpy only.

The coenergy integral is the piece most implementations get slightly wrong by
reaching for quadrature. If the reluctivity your solver used is a piecewise
linear interpolant of a tabulated H(B), then the coenergy of that same material
is the closed-form integral of that interpolant -- anything else makes the
energy and the stiffness disagree about what the material is.
"""
from __future__ import annotations

import numpy as np

MU0 = 4e-7 * np.pi
NU0 = 1.0 / MU0


class BHCurve:
    """H(B) as a piecewise-linear interpolant with a fully saturated tail.

    Above the last tabulated point the steel is saturated, so dH/dB -> 1/mu0 and
    H(B) = H_max + (B - B_max) * NU0. Below the first, the initial slope holds,
    which keeps nu finite at B = 0.
    """

    def __init__(self, H: np.ndarray, B: np.ndarray):
        H = np.asarray(H, dtype=np.float64)
        B = np.asarray(B, dtype=np.float64)
        if B[0] != 0.0 or H[0] != 0.0:
            raise ValueError("expected the (H, B) table to start at the origin")
        if np.any(np.diff(B) <= 0.0):
            raise ValueError("B column must be strictly increasing")
        self.B, self.H = B, H
        self.Bmax, self.Hmax = float(B[-1]), float(H[-1])
        self.nu_init = float(H[1] / B[1])
        # cumulative trapezoid of H dB at each table point, reused by coenergy
        seg = 0.5 * (H[1:] + H[:-1]) * np.diff(B)
        self._cum = np.concatenate([[0.0], np.cumsum(seg)])

    def H_of_B(self, b: np.ndarray) -> np.ndarray:
        b = np.asarray(b, dtype=np.float64)
        h = np.interp(b, self.B, self.H)                    # clamps at both ends
        tail = b > self.Bmax
        return np.where(tail, self.Hmax + (b - self.Bmax) * NU0, h)

    def nu(self, b: np.ndarray) -> np.ndarray:
        b = np.asarray(b, dtype=np.float64)
        small = b < 1e-9
        safe = np.where(small, 1.0, b)
        return np.where(small, self.nu_init, self.H_of_B(safe) / safe)

    def coenergy_density(self, b: np.ndarray) -> np.ndarray:
        """integral of H dB' from 0 to |B|, in J/m^3. Exact for this interpolant."""
        b = np.asarray(b, dtype=np.float64)
        out = np.empty_like(b)
        inside = b <= self.Bmax
        if np.any(inside):
            bi = b[inside]
            i = np.clip(np.searchsorted(self.B, bi, side="right") - 1, 0, self.B.size - 2)
            db = bi - self.B[i]
            slope = (self.H[i + 1] - self.H[i]) / (self.B[i + 1] - self.B[i])
            out[inside] = self._cum[i] + self.H[i] * db + 0.5 * slope * db * db
        tail = ~inside
        if np.any(tail):
            db = b[tail] - self.Bmax
            out[tail] = self._cum[-1] + self.Hmax * db + 0.5 * NU0 * db * db
        return out


def linear_curve(mu_r: float, b_max: float = 5.0) -> BHCurve:
    """A straight H = B / (mu0 mu_r) law wrapped in the same interface."""
    b = np.array([0.0, b_max])
    return BHCurve(np.array([0.0, b_max / (MU0 * mu_r)]), b)
