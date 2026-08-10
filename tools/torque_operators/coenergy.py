"""Magnetic coenergy of a 2D triangulated domain. numpy only.

    W' = integral over V of ( integral from 0 to B of H . dB' )

Per element, matching the constitutive laws an assembler normally uses:

    linear (air, slot, non-steel):  H = nu B          -> w' = nu |B|^2 / 2
    magnet:                         H = nu (B - Br)   -> w' = nu (|B|^2/2 - Br.B)
    steel with a BH curve:          H = H(|B|)        -> w' = integral H dB', exact

This is the quantity virtual work differentiates, so it has to agree with the
material model the field was solved with -- not approximately, exactly.
"""
from __future__ import annotations

import numpy as np

from .mesh import ElementMaterials, TriMesh


def coenergy_density(materials: ElementMaterials, b_elem: np.ndarray) -> np.ndarray:
    """(E,) coenergy density in J/m^3."""
    b_elem = np.asarray(b_elem, dtype=np.float64)
    b_mag = np.hypot(b_elem[:, 0], b_elem[:, 1])
    w = np.zeros(b_mag.size, dtype=np.float64)

    linear = materials.curve_index < 0
    if np.any(linear):
        w[linear] = 0.5 * materials.nu_linear[linear] * b_mag[linear] ** 2
        # magnets live among the linear elements; subtract the Br.B work term
        br = materials.br[linear]
        has_br = np.any(br != 0.0, axis=1)
        if np.any(has_br):
            idx = np.flatnonzero(linear)[has_br]
            w[idx] -= materials.nu_linear[idx] * (
                materials.br[idx, 0] * b_elem[idx, 0]
                + materials.br[idx, 1] * b_elem[idx, 1])

    for k, curve in enumerate(materials.curves):
        sel = materials.curve_index == k
        if np.any(sel):
            w[sel] = curve.coenergy_density(b_mag[sel])
    return w


def total_coenergy(materials: ElementMaterials, b_elem: np.ndarray,
                   area: np.ndarray) -> float:
    """Coenergy of the modelled region, J per metre of stack."""
    return float(np.sum(coenergy_density(materials, b_elem) * np.asarray(area)))
