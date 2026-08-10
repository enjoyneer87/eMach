"""Arkkio air-gap torque -- the annulus-averaged Maxwell stress tensor.

Arkkio is not a separate principle from MST. The single-contour Maxwell stress
torque at radius r is

    T(r) = (L r^2 / mu0) * closed integral of Br Btheta dtheta

and averaging that over the radial extent of the gap, with dS = r dr dtheta,
gives

    T = L / (mu0 (r_out - r_in)) * integral over S of r Br Btheta dS

which is what this module computes. Same stress tensor, integrated over the
annulus instead of one circle -- which is precisely why it is far less sensitive
to where you place the contour than plain MST is.

Take the radial extent from the band's NODE radii, not its centroid radii:
centroids understate the thickness and inflate the torque.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from .bh import MU0
from .mesh import TriMesh


@dataclass(frozen=True)
class AirgapBand:
    element_index: np.ndarray         # (M,) positions within the full element arrays
    radius: np.ndarray                # (M,) centroid radius, m
    area: np.ndarray                  # (M,) m^2
    cos_theta: np.ndarray             # (M,)
    sin_theta: np.ndarray             # (M,)
    r_inner: float
    r_outer: float
    sector_span_rad: float
    symmetry_multiplier: int

    @property
    def thickness(self) -> float:
        return self.r_outer - self.r_inner

    @property
    def n_elements(self) -> int:
        return int(self.element_index.size)


def build_band(mesh: TriMesh, element_mask: np.ndarray,
               symmetry_multiplier: Optional[int] = None) -> AirgapBand:
    """Precompute the Arkkio operator for a chosen set of air-gap elements.

    ``element_mask`` selects a STATIONARY annular layer. Do not include a sliding
    band: it is often drawn over a wider arc than the modelled sector, which
    corrupts both the radial extent and the symmetry count.
    """
    idx = np.flatnonzero(np.asarray(element_mask, dtype=bool))
    if idx.size == 0:
        raise ValueError("empty air-gap band")
    tri = mesh.tri[idx]
    xe, ye = mesh.x[tri], mesh.y[tri]
    cx, cy = xe.mean(1), ye.mean(1)
    r = np.hypot(cx, cy)
    two_a = ((xe[:, 1] - xe[:, 0]) * (ye[:, 2] - ye[:, 0])
             - (xe[:, 2] - xe[:, 0]) * (ye[:, 1] - ye[:, 0]))
    area = np.abs(0.5 * two_a)

    node_r = np.hypot(mesh.x[np.unique(tri)], mesh.y[np.unique(tri)])
    r_in, r_out = float(node_r.min()), float(node_r.max())

    ang = np.arctan2(mesh.y[np.unique(tri)], mesh.x[np.unique(tri)])
    span = float(ang.max() - ang.min())
    if symmetry_multiplier is None:
        ratio = 2.0 * np.pi / span
        symmetry_multiplier = int(round(ratio))
        if abs(ratio - symmetry_multiplier) > 0.05:
            raise ValueError(
                f"sector span {np.degrees(span):.3f} deg does not divide 360 "
                f"({ratio:.4f} sectors); pass symmetry_multiplier explicitly")
    return AirgapBand(idx, r, area, cx / r, cy / r, r_in, r_out, span,
                      max(1, int(symmetry_multiplier)))


def arkkio_torque(band: AirgapBand, bx_elem: np.ndarray, by_elem: np.ndarray,
                  axial_length_m: float = 1.0) -> float:
    """Torque of the FULL machine, N*m (per metre of stack at the default length).

    ``bx_elem``/``by_elem`` may be indexed over the full element array or already
    sliced to the band.
    """
    bx = np.asarray(bx_elem, dtype=np.float64).ravel()
    by = np.asarray(by_elem, dtype=np.float64).ravel()
    if bx.shape != by.shape:
        raise ValueError(f"bx/by shape mismatch: {bx.shape} vs {by.shape}")
    if bx.size != band.n_elements:
        bx, by = bx[band.element_index], by[band.element_index]

    b_r = bx * band.cos_theta + by * band.sin_theta
    b_t = -bx * band.sin_theta + by * band.cos_theta
    integrand = band.radius * b_r * b_t * band.area
    finite = np.isfinite(integrand)
    if not np.any(finite):
        return float("nan")
    scale = axial_length_m * band.symmetry_multiplier / (MU0 * band.thickness)
    return float(scale * np.sum(integrand[finite]))
