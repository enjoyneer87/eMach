"""Coulomb local virtual work torque, from ONE solved field.

Virtual work says T = dW'/dtheta at constant current. There are two ways to take
that derivative and they are the same principle, not competing methods:

  global  -- evaluate W' at two separately solved rotor positions and difference.
             Needs >= 2 solves, two meshes, and (see the warning below) genuinely
             constant current between them.
  local   -- Coulomb (1983). ONE solve. Give the rotor an infinitesimal VIRTUAL
             rotation, let a layer of air-gap elements absorb the distortion, and
             differentiate the discrete coenergy with the nodal A held fixed.

Holding A fixed is exact, not an approximation: at the FE solution the functional
is stationary in A, so the implicit term dW'/dA . dA/dtheta vanishes and only the
explicit geometric derivative survives. That is why one solve suffices.

WARNING about the global route on a synchronous sweep. dW'/dtheta must be taken
at CONSTANT CURRENT. In an on-load synchronous rotor sweep the stator current
wave advances with the rotor, so differencing adjacent steps measures the
derivative along the synchronous trajectory -- mechanical and electrical
contributions together -- and they very nearly cancel. Measured on a 48-slot/
8-pole IPM it returns O(10) N*m/m where the true torque is O(2500). Coulomb's
route freezes the currents by construction and has no such failure mode. That,
not cost, is the reason to prefer it.

The derivative here is taken numerically IN THE VIRTUAL ANGLE. That is not a
finite difference between solves: there is no second solve and no second mesh,
only an exact re-evaluation of the discrete coenergy at perturbed coordinates.
It carries no solver noise, so eps can be pushed to where round-off rather than
truncation dominates, and a central difference makes truncation O(eps^2).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional

import numpy as np

from .coenergy import total_coenergy
from .mesh import ElementMaterials, TriMesh, element_b_and_area


@dataclass(frozen=True)
class VirtualDisplacement:
    """Per-node rotation weight: 1 on the rotor, 0 on the stator, blended in the gap.

    Virtual work is invariant to the blend. `coulomb_torque(..., self_test=True)`
    exploits that: if two different profiles disagree, the displacement field is
    touching something it should not (usually it is deforming iron, or the layer
    is only one element thick so there is no interior to absorb the shear).
    """

    weight: np.ndarray                # (N,)
    rotor_element: np.ndarray         # (E,) bool, moves rigidly with the rotor
    r_inner: float
    r_outer: float


def radial_blend(mesh: TriMesh, r_inner: float, r_outer: float,
                 profile: str = "linear") -> VirtualDisplacement:
    """Rigid rotor rotation blended to zero across the annulus [r_inner, r_outer].

    The rotor side must move RIGIDLY (weight exactly 1): if it shears, its own
    elements change shape and inject energy that has nothing to do with torque.
    For the same reason magnets must carry their easy axis around with them,
    which `coulomb_torque` does.
    """
    if not (r_outer > r_inner > 0.0):
        raise ValueError(f"need 0 < r_inner < r_outer, got {r_inner}, {r_outer}")
    r = mesh.node_radius()
    t = np.clip((r_outer - r) / (r_outer - r_inner), 0.0, 1.0)
    if profile == "linear":
        w = t
    elif profile == "smoothstep":
        w = t * t * (3.0 - 2.0 * t)
    else:
        raise ValueError(f"unknown profile {profile!r}")
    w[r <= r_inner] = 1.0
    w[r >= r_outer] = 0.0
    return VirtualDisplacement(w, mesh.centroid_radius() < r_inner, r_inner, r_outer)


def coulomb_torque(mesh: TriMesh, materials: ElementMaterials, a_nodal: np.ndarray,
                   displacement: VirtualDisplacement,
                   axial_length_m: float = 1.0,
                   symmetry_multiplier: int = 1,
                   eps_rad: float = 1e-6,
                   self_test: bool = False) -> Dict[str, float]:
    """T = dW'/dtheta by virtual rotor rotation. Returns a dict with diagnostics.

    ``symmetry_multiplier`` is the number of modelled sectors in the full machine.
    Measure it on a STATIONARY region whose angular extent really is the sector --
    a sliding-band region is often drawn wider than the sector, and an
    anti-periodic image layer extends the node cloud further still. Getting it
    from the raw node cloud is how you silently scale every torque you report.
    """
    a = np.asarray(a_nodal, dtype=np.float64).reshape(-1)
    if a.size != mesh.n_nodes:
        raise ValueError(f"a_nodal has {a.size} entries, mesh has {mesh.n_nodes} nodes")

    def coenergy_at(delta: float) -> float:
        ang = displacement.weight * delta
        ca, sa = np.cos(ang), np.sin(ang)
        xr = mesh.x * ca - mesh.y * sa
        yr = mesh.x * sa + mesh.y * ca
        b_elem, area = element_b_and_area(mesh, a, x=xr, y=yr)
        mats = materials
        rot = displacement.rotor_element
        if np.any(rot) and np.any(materials.br != 0.0):
            br = materials.br.copy()
            c, s = np.cos(delta), np.sin(delta)
            bx, by = br[rot, 0].copy(), br[rot, 1].copy()
            br[rot, 0] = c * bx - s * by
            br[rot, 1] = s * bx + c * by
            mats = ElementMaterials(materials.nu_linear, br,
                                    materials.curve_index, materials.curves)
        return total_coenergy(mats, b_elem, area)

    dwd = (coenergy_at(+eps_rad) - coenergy_at(-eps_rad)) / (2.0 * eps_rad)
    # Sign. Freezing the nodal A while the geometry moves is a CONSTANT-FLUX
    # operation, and at constant flux linkage the torque is -dW/dtheta, not
    # +dW'/dtheta. The two differ by exactly this sign (in magnitude they agree,
    # since W = W' for the linear part and stationarity kills the implicit term).
    # Verified twice: on the synthetic annulus in selftest.py, and against the
    # annulus-averaged MST on Motor-CAD IPM fields, where the magnitudes match to
    # 0.475% with a 0.024 pp spread and the raw sign is consistently opposite.
    # Negating here puts this operator in the same +theta convention as
    # `arkkio.arkkio_torque`, so callers can compare the two directly.
    torque = -axial_length_m * symmetry_multiplier * dwd
    out = {
        "torque": float(torque),
        "dW_dtheta_per_sector": float(dwd),
        "coenergy_J_per_m": float(coenergy_at(0.0)),
        "eps_rad": float(eps_rad),
        "symmetry_multiplier": int(symmetry_multiplier),
        "r_inner": displacement.r_inner,
        "r_outer": displacement.r_outer,
    }
    if self_test:
        alt = radial_blend(mesh, displacement.r_inner, displacement.r_outer,
                           profile="smoothstep")
        other = coulomb_torque(mesh, materials, a, alt, axial_length_m,
                               symmetry_multiplier, eps_rad, self_test=False)
        out["torque_alt_profile"] = other["torque"]
        out["profile_invariance_pct"] = float(
            100.0 * abs(other["torque"] - torque) / max(abs(torque), 1e-30))
    return out
