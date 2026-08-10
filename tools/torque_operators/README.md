# torque_operators

Two independent routes from a 2D field to a torque, plus the diagnostics needed
to tell whether a disagreement between them is real. numpy only — no solver, no
mesher, no CAD package, no Motor-CAD.

```python
from tools.torque_operators import (
    TriMesh, ElementMaterials, BHCurve,
    build_band, arkkio_torque,
    radial_blend, coulomb_torque,
    smoothness_report,
)
```

## Why both

`arkkio_torque` integrates the Maxwell stress tensor; `coulomb_torque`
differentiates the magnetic coenergy. They share no code path beyond the mesh,
so when they agree it is evidence, and when they do not, one of them is wrong.

Cross-checked on a 48-slot / 8-pole IPM (Motor-CAD field, five rotor positions,
same mesh and same nodal A fed to both):

```
mean difference  -0.475 %      spread  0.024 pp
```

A spread of 0.024 pp means the residual is a **systematic offset, not scatter** —
consistent with air-gap band discretisation rather than with either operator
being unreliable.

## Arkkio is MST, not an alternative to it

The single-contour Maxwell stress torque at radius `r` is

```
T(r) = (L r^2 / mu0) * closed_integral( Br Bt dtheta )
```

Averaging over the radial extent of the gap, with `dS = r dr dtheta`:

```
T = L / (mu0 (r_out - r_in)) * integral_S( r Br Bt dS )
```

Same stress tensor, integrated over the annulus instead of one circle — which is
exactly why it barely cares where in the gap you put the contour, while plain MST
does. Take the radial extent from the band's **node** radii; centroid radii
understate the thickness and inflate the torque.

## Coulomb local virtual work IS the virtual work principle

Both are `T = dW'/dtheta` at constant current. The difference is only how the
derivative is taken:

| | global (textbook) | Coulomb (local) |
|---|---|---|
| derivative | numerical difference of two solutions | analytic derivative of one |
| solves | ≥ 2 | **1** |
| meshes | two (the rotor moved) | one |

One solve suffices because at the FE solution the functional is stationary in
`A`, so the implicit term `dW'/dA · dA/dtheta` vanishes and only the explicit
geometric derivative survives. Holding `A` fixed is exact, not an approximation.

The derivative here is taken numerically **in the virtual angle** — which is not
a finite difference between solves. There is no second solve and no second mesh,
only an exact re-evaluation of the discrete coenergy at perturbed coordinates, so
it carries no solver noise and `eps` can go to where round-off dominates.

### Sign

Freezing the nodal `A` while the geometry moves is a **constant-flux** operation,
and at constant flux linkage the torque is `-dW/dtheta`, not `+dW'/dtheta`. The
magnitudes agree; the sign does not. `coulomb_torque` negates internally so that
it returns torque about `+theta`, the same convention as `arkkio_torque`, and
callers can compare the two directly. This was verified twice — on the synthetic
annulus in `selftest.py` and against MST on Motor-CAD fields.

## Three traps this package is built to avoid

**1. The global route is invalid on a synchronous sweep.** `dW'/dtheta` must be
taken at *constant current*. In an on-load synchronous rotor sweep the stator
current wave advances with the rotor, so differencing adjacent steps measures the
derivative along the synchronous trajectory — mechanical and electrical
contributions together — and they very nearly cancel. Measured on the IPM above
it returns O(10) N·m/m where the true torque is O(2500). Coulomb's route freezes
the currents by construction. That, not cost, is the reason to prefer it.

**2. Symmetry measured off the raw node cloud is wrong.** A sliding band is often
drawn over a wider arc than the modelled sector, and an anti-periodic image layer
extends the point cloud further still. On the IPM above the node cloud spans
65.5° while the true sector is 44.9° — enough to return 4 sectors instead of 8
and silently halve every torque. Measure it on a **stationary** gap region, or
pass `symmetry_multiplier` explicitly.

**3. The rotor must rotate rigidly.** If the virtual displacement shears the iron
instead of the gap, rotor elements change shape and inject energy unrelated to
torque; and magnets must carry their easy axis with them or a rigid rotation
fakes a change in the `Br·B` term. `coulomb_torque(..., self_test=True)` catches
both by re-running with a different blend profile — virtual work is invariant to
that choice, so a disagreement means the displacement field is touching something
it should not.

## Air-gap harmonics

`airgap_harmonics` answers "how much of the gap field can harmonics actually
express", which is a measurable definition of air-gap noise. In a source-free
annulus `A` satisfies Laplace, so the exact solution space is
`sum_n (a_n r^n + b_n r^-n) exp(i n theta)`, and on an anti-periodic one-pole
sector only odd multiples of `p` can exist. Anything outside that is
discretisation.

Measured on the same IPM (6 held-out geometries × 5 rotor positions, 752 band
elements, 0.17 mm band), residual as a fraction of field RMS:

| component | admissible (4·odd, 24 orders) | all n ≤ 200 | all n ≤ 350 |
|---|---|---|---|
| `Br` | 11.33 % | 9.12 % | **7.13 %** |
| `Btheta` | 23.78 % | 16.45 % | **11.49 %** |

Two conclusions worth carrying to any similar machine:

- **A thin band cannot identify the radial basis.** With `u = r/r0` in
  `[0.9988, 1.0012]`, `u^n` and `u^-n` are numerically the same function. Adding
  the air-gap-element radial degrees of freedom moved the `Br` residual from
  8.33 % to 8.45 % — it got *worse*, from collinearity. An AGE representation
  pays when it *replaces* the gap mesh, not when fitted on top of one already 29
  layers deep.
- **The gap field is not a function of theta alone.** Even a basis with 700
  parameters on 752 elements leaves `Br` at 7.13 %: elements at the same angle
  but different radius genuinely disagree. Any scheme that projects the gap onto
  harmonics and uses the reconstruction as a guide throws that away.

## Self-test

```
python -m tools.torque_operators.selftest
```

No data files. Builds an air annulus, imposes a known harmonic potential, and
checks the two operators against each other, plus profile invariance, `eps`
independence, first-order convergence of an analytically-zero torque, and the
linear-air coenergy identity.

The tolerance on the operator cross-check is loose there (25 %) because `B` on P1
triangles is first-order and the test annulus is deliberately coarse. The tight
number is the one measured on real fields: **0.475 %**.
