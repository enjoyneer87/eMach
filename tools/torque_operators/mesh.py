"""Plain-numpy triangular mesh + element materials.

Deliberately not tied to any solver. Anything that can hand over node
coordinates, a triangle table, per-element reluctivity and (optionally) magnet
remanence can drive the torque operators in this package -- a Motor-CAD export,
a FEMM/gmsh model, or a hand-built test mesh.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

from .bh import BHCurve


@dataclass(frozen=True)
class TriMesh:
    """Linear (P1) triangles. Coordinates in METRES, node indices counter-clockwise."""

    x: np.ndarray                     # (N,)
    y: np.ndarray                     # (N,)
    tri: np.ndarray                   # (E, 3)

    @property
    def n_nodes(self) -> int:
        return int(self.x.size)

    @property
    def n_elements(self) -> int:
        return int(self.tri.shape[0])

    def centroid_radius(self) -> np.ndarray:
        return np.hypot(self.x[self.tri].mean(1), self.y[self.tri].mean(1))

    def node_radius(self) -> np.ndarray:
        return np.hypot(self.x, self.y)


@dataclass(frozen=True)
class ElementMaterials:
    """Per-element constitutive data.

    ``nu_linear`` applies wherever ``curve_index < 0``; elements with a curve use
    the matching `BHCurve`. ``br`` is the magnet remanence in tesla (zero rows
    elsewhere), under the convention H = nu (B - Br) -- the same one the usual
    magnet load-vector assembly implies.
    """

    nu_linear: np.ndarray             # (E,)
    br: np.ndarray                    # (E, 2)
    curve_index: np.ndarray           # (E,) index into `curves`, -1 = linear
    curves: Tuple[BHCurve, ...] = ()

    @staticmethod
    def all_air(n_elements: int, nu: float) -> "ElementMaterials":
        return ElementMaterials(
            nu_linear=np.full(n_elements, float(nu)),
            br=np.zeros((n_elements, 2)),
            curve_index=np.full(n_elements, -1, dtype=np.int64),
        )


def element_b_and_area(mesh: TriMesh, a_nodal: np.ndarray,
                       x: Optional[np.ndarray] = None,
                       y: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """(B (E,2) tesla, area (E,) m^2) from nodal A, at OPTIONALLY moved coordinates.

    Convention Bx = dA/dy, By = -dA/dx. The coordinates are an argument rather
    than baked in because the whole point of a virtual displacement is that the
    shape-function gradients and the element areas move with the nodes.
    """
    xs = mesh.x if x is None else x
    ys = mesh.y if y is None else y
    tri = mesh.tri
    xe, ye = xs[tri], ys[tri]
    b0, b1, b2 = ye[:, 1] - ye[:, 2], ye[:, 2] - ye[:, 0], ye[:, 0] - ye[:, 1]
    c0, c1, c2 = xe[:, 2] - xe[:, 1], xe[:, 0] - xe[:, 2], xe[:, 1] - xe[:, 0]
    two_a = xe[:, 0] * b0 + xe[:, 1] * b1 + xe[:, 2] * b2
    ae = np.asarray(a_nodal, dtype=np.float64)[tri]
    dady = (c0 * ae[:, 0] + c1 * ae[:, 1] + c2 * ae[:, 2]) / two_a
    dadx = (b0 * ae[:, 0] + b1 * ae[:, 1] + b2 * ae[:, 2]) / two_a
    return np.stack([dady, -dadx], axis=1), np.abs(0.5 * two_a)


def annulus_sector_mesh(r_in: float, r_out: float, span_rad: float,
                        n_r: int, n_theta: int) -> TriMesh:
    """A structured triangulated annular sector. Used by the self-test."""
    r = np.linspace(r_in, r_out, n_r + 1)
    t = np.linspace(0.0, span_rad, n_theta + 1)
    R, T = np.meshgrid(r, t, indexing="ij")
    x, y = (R * np.cos(T)).ravel(), (R * np.sin(T)).ravel()

    def nid(i, j):
        return i * (n_theta + 1) + j

    tris = []
    for i in range(n_r):
        for j in range(n_theta):
            a, b, c, d = nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1)
            tris += [[a, b, c], [a, c, d]]        # counter-clockwise
    return TriMesh(x=x, y=y, tri=np.asarray(tris, dtype=np.int64))
