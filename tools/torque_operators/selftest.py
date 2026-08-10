"""Self-contained regression test: no solver, no CAD, no data files.

Builds an air annulus, imposes a vector potential whose harmonics produce a
known non-zero Maxwell stress, and checks that the two independent operators --
annulus-averaged MST and Coulomb local virtual work -- return the same torque.
They share no code path beyond the mesh, so agreement is a real cross-check.

    python -m tools.torque_operators.selftest
"""
from __future__ import annotations

import numpy as np

from .arkkio import arkkio_torque, build_band
from .bh import NU0
from .coenergy import total_coenergy
from .mesh import ElementMaterials, annulus_sector_mesh, element_b_and_area
from .virtual_work import coulomb_torque, radial_blend

FAIL = []


def check(name: str, got: float, want: float, tol_pct: float) -> None:
    err = 100.0 * abs(got - want) / max(abs(want), 1e-30)
    ok = err <= tol_pct
    print(f"  [{'ok ' if ok else 'FAIL'}] {name:44s} {got:14.6g} vs {want:14.6g}  ({err:.3f}% <= {tol_pct}%)")
    if not ok:
        FAIL.append(name)


def main() -> int:
    # A 2-pole-pair pattern on a quarter annulus: p=2 admits orders 2, 6, 10, ...
    # Two orders are needed for a non-zero average Br*Btheta product.
    p, span = 2, np.pi / 2
    mesh = annulus_sector_mesh(r_in=0.060, r_out=0.064, span_rad=span,
                               n_r=12, n_theta=180)
    r = mesh.node_radius()
    th = np.arctan2(mesh.y, mesh.x)
    a = (0.02 * (r / 0.062) ** p * np.cos(p * th)
         + 0.004 * (r / 0.062) ** (3 * p) * np.sin(3 * p * th))

    mats = ElementMaterials.all_air(mesh.n_elements, NU0)
    b_elem, area = element_b_and_area(mesh, a)

    print("air annulus, quarter sector, p = 2")
    print(f"  {mesh.n_elements} elements, {mesh.n_nodes} nodes, "
          f"|B| rms {np.sqrt(np.mean((b_elem ** 2).sum(1))):.4f} T")

    band = build_band(mesh, np.ones(mesh.n_elements, dtype=bool), symmetry_multiplier=4)
    t_ark = arkkio_torque(band, b_elem[:, 0], b_elem[:, 1])

    disp = radial_blend(mesh, band.r_inner, band.r_outer)
    cou = coulomb_torque(mesh, mats, a, disp, symmetry_multiplier=4, self_test=True)

    print("\ncross-check")
    # Both operators report about +theta (virtual_work negates internally; see the
    # constant-flux note there). The tolerance is loose because B on P1 triangles
    # is only first-order accurate and this annulus is deliberately coarse -- the
    # tight number is the one measured on real fields, 0.475%.
    check("Coulomb VW vs Arkkio MST", cou["torque"], t_ark, 25.0)
    check("virtual-displacement profile invariance",
          cou["torque_alt_profile"], cou["torque"], 1.0)

    print("\ninvariances")
    # eps must not matter: a central difference of an exact function.
    for eps in (1e-5, 1e-7):
        alt = coulomb_torque(mesh, mats, a, disp, symmetry_multiplier=4, eps_rad=eps)
        check(f"eps independence (eps={eps:g})", alt["torque"], cou["torque"], 0.5)
    # A pure single harmonic carries no net torque analytically (<sin*cos> = 0 over
    # the sector). On a discrete mesh it is not exactly zero -- B is piecewise
    # constant and first-order -- so the meaningful check is that it CONVERGES to
    # zero under refinement, which also proves the residual is discretisation and
    # not a formulation error.
    print("\nsingle-harmonic torque must vanish under refinement")
    prev = None
    for n_t in (90, 180, 360):
        m2 = annulus_sector_mesh(0.060, 0.064, span, n_r=12, n_theta=n_t)
        r2 = m2.node_radius()
        th2 = np.arctan2(m2.y, m2.x)
        a1 = 0.02 * (r2 / 0.062) ** p * np.cos(p * th2)
        b1, _ = element_b_and_area(m2, a1)
        band2 = build_band(m2, np.ones(m2.n_elements, dtype=bool), symmetry_multiplier=4)
        t1 = abs(arkkio_torque(band2, b1[:, 0], b1[:, 1]))
        print(f"  n_theta {n_t:4d}   |T| = {t1:.6g}")
        if prev is not None and t1 > prev * 0.75:
            FAIL.append(f"single-harmonic torque not converging at n_theta={n_t}")
        prev = t1

    # Coenergy of linear air must be nu0/2 * integral |B|^2 -- guards the material path.
    w_ref = float(np.sum(0.5 * NU0 * (b_elem ** 2).sum(1) * area))
    check("coenergy matches nu0/2 |B|^2 for air",
          total_coenergy(mats, b_elem, area), w_ref, 1e-9)

    print("\nTORQUE_OPERATORS_SELFTEST_" + ("PASS" if not FAIL else f"FAIL {FAIL}"))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
