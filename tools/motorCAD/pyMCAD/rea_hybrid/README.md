# REA-derived rectangular Hybrid AC-loss evaluator

This package contains an independent mathematical reconstruction of the
inspected Motor-CAD v261 rectangular Hybrid path and an offline Elmer adapter.
The original `hybrid_kernel.py` is preserved byte for byte. `PROVENANCE.json`
identifies the source and validation scope. No executable, decompiler output,
Motor-CAD installation, license, COM call, REA runtime, or new FEA is required.

The evaluated quantity is AC excess, proximity plus skin. DC transport loss
is excluded. The Elmer adapter uses a 0.15 m active stack and actual bar areas,
not the native total-armature copper volume. Native-output parity and agreement
with Full-FEA are separate comparisons.

## Calculation contract

- Input is `ALL_A_HISTORY.npz` from a homogenized-slot MS case, with node IDs,
  `node_xy_m`, triangular connectivity, physical tags, and nodal A at every phase.
- Supply the corresponding `MS_MANIFEST.json`. One complete cycle of 128
  post-step phases is used for the current campaign. No duplicated initial point.
- Scalar B is the magnitude of the exact curl of P1 triangular A at each sample.
  This is an Elmer field adapter, not a clone of the proprietary point interpolator.
- Sample the resolved Ref insulated geometry with 30 polynomially distributed
  lines, ten interior points on each side, 600 points total. Per-cuboid line
  counts are 2/3/3/4/5/13. Loss coefficients use bare copper dimensions.
- Use spatial **mean(B squared)** with area and valid-slot weights, then average
  the phase losses. Do not square a line-mean B or apply FFT/harmonic weights.
- Use the recovered fundamental-frequency high-frequency branch, not the old
  public capped approximation. Do not multiply by an additional peak-to-RMS 1/2.
- Copper conductivity is 47,092,391.429245 S/m, already temperature adjusted.
  Active skin is computed per actual Elmer bar area and prescribed RMS current.
- Ref-only target fields use exact radial factors 1, 1.5, 2, with current factors
  1, 1.5, 2 and constant length. No full-loss labels enter this calculation.
- Only the resolved e10 six-cuboid, single-strand geometry is supported by this
  adapter. Generic geometry, PWM and other native versions are not validated.

The immutable numerical inputs in `examples/e10_ref_input.json` include all
36 Ref bar areas. They reproduce the independently exported Ref DC transport
loss, 31,412.87388612683 W at 460 Arms, without fitting.

## Run on another host

Use a fresh checkout/worktree and pin the exact commit supplied by the handoff.
Install `requirements.txt` in the existing postprocessing Python environment.

PowerShell, from the eMach checkout:

```powershell
$env:PYTHONPATH = (Resolve-Path tools/motorCAD/pyMCAD).Path
python -B -m rea_hybrid.verify_kernel
python -B -m rea_hybrid.postprocess_elmer --field PATH/ALL_A_HISTORY.npz --manifest PATH/MS_MANIFEST.json --out OUTPUT/Ref_P117_REA --targets Ref HalfSC SC --speeds 2000 4000 8000 16000
```

Linux, from the eMach checkout:

```bash
export PYTHONPATH="$PWD/tools/motorCAD/pyMCAD"
python -B -m rea_hybrid.verify_kernel
python -B -m rea_hybrid.postprocess_elmer --field PATH/ALL_A_HISTORY.npz --manifest PATH/MS_MANIFEST.json --out OUTPUT/Ref_P117_REA --targets Ref HalfSC SC --speeds 2000 4000 8000 16000
```

Replace the paths with the actual existing field and its matching manifest.
An existing output directory is rejected rather than overwritten. At no load,
current-dependent skin is zero while PM-field proximity loss remains evaluated.

For all 30 Ref points, enumerate the verified field/manifest pairs and invoke
the command once per point. For independent SC MS, provide the SC field and its
own SC manifest, and use `--targets SC`. Its actual source radial factor and
current are read from the manifest. Do not use SC fields as Ref-only predictions.

Each output contains `LOSSES.csv/json`, `SAMPLES.npz`, `WAVEFORMS.npz`, and
`RECEIPT.json`. Receipts bind the code, input potential, manifest, and contract
by SHA256. Never substitute preaggregated `MS_SPECTRUM.json` for the A history.

## Validation and limits

The original 19 algebra/manufactured-field checks are runnable with
`verify_kernel`. Recorded independent getter inputs reproduce native skin
outputs at 120 Ref and 120 SC points to approximately 5e-15 relative error.
Those checks use native copper volume and do not certify active-only Full-FEA
accuracy. Native HalfSC total copper volume is not established by that audit.

The Elmer representative CLI and the Fig. 4 calculation agree for all 12 target
model/speed pairs. Ref 8k / SC 2k and Ref 16k / SC 4k Hybrid similarity identities
also hold numerically. Solver spatial/time convergence and the HalfSC 16k
period-2 current gate remain separate evidence requirements.

Changing this evaluator changes the AF denominator. Refit AF using this same
evaluator for fitting and application; do not reuse old capped AF parameters.
Report evaluation populations and held-out/calibration points separately.

This module is the eMach maintenance source. The JEET public reproduction
package may include a byte-identical copy pinned to this source commit.
