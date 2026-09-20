# M1: Ref-only field-to-loss verification

This is a review experiment. It does not change the default manuscript model.
It evaluates the existing public line-sampled capped proximity kernel plus
skin excess at 80 C, using Ref MS fields for every target denominator.
This public evaluation variant is not an exact copy of the deposited
commercial hybrid.

## Run

From `mlxperPJT/JEET`, with the repository's NumPy/SciPy environment:

```powershell
python run_ref_only_field_spectra.py --ref-fields <Ref-backfill-directory> --out <output>/spectra --workers 2
python run_ref_only_field_pipeline.py --spectra <output>/spectra/ref_ms_spectra.json --data <e10-Map-Summary-directory> --out <output>/ref_only_pipeline.json
python -m unittest test_ref_only_field_pipeline -v
```

The first command requires 30 `Hybrid_Speed_16000RPM_*/FEA_data.txt.gz`
Ref exports. It fingerprints each compressed input, checks 128 samples
and 36 conductor regions, and verifies the line-sampling operator under
1.5 and 2.0 geometry dilation. Its per-point cache is reusable only when
both raw hashes and the relevant processing-code hashes match.

The second command uses 36 Ref and 27 target Full-FEA training values.
Non-training truth is masked and the whole fit repeated as an access check.
All 96 loaded points must have a unique Ref-field coordinate match.
The explicit current tolerance is 0.2 A in Ref coordinates to accommodate
recorded rounding; missing or ambiguous matches stop the calculation.
Kernel frequencies are reevaluated at scaled conductor dimensions.

## Results, 2026-09-20

All values below are wMAE in percent, not efficiency percentage points.

| Machine | Deposited hybrid, all 96 | Ref-only public hybrid, all 96 | Deposited own-held-out | Ref-only own-held-out |
|---|---:|---:|---:|---:|
| Ref | 0.630763 | 1.042090 | 1.991090 | 3.294842 |
| HalfSC | 0.842394 | 1.278366 | 2.637442 | 4.006599 |
| SC | 0.761632 | 1.420463 | 2.200053 | 3.445096 |

These columns change both field provenance and the hybrid evaluator.
They must not be interpreted as a pure field-transfer error. With the
public Ref donor fixed, SC's public own-field case gives 1.026592/2.552924%
(all/held-out), versus 1.420463/3.445096% for transferred fields. These
use the same sampling rule and budget, but one 8 kRPM calibration point
changes because its selection depends on the fitted anchor kernel.

The existing HalfSC own-field cache does not cover 74 of the current
96 target coordinates. That comparison is explicitly unavailable;
the Ref-only HalfSC prediction itself covers all 96 points.

No new FEA was solved. All-point metrics include calibration points.
Own-held-out values are not independent external tests. Raw fields retain
the existing sampling/FFT convention; this is not a mesh/time-step
convergence study. The original Full-FEA reference values are unchanged.

Detailed input manifests, predictions, training coordinates, checks and
plots are in the manuscript review folder's `evidence/M1` artifacts.

## Exact-anchor update, 2026-09-20

The author adopted f(16)=p(16)=1 as an exact constraint after reviewing the
full comparison. The native production runner now gives full-grid wMAE
0.982584/1.203463/1.155889% and own-withheld wMAE
3.295904/4.009746/3.449489% (Ref/HalfSC/SC). These replace the pre-anchor
headline for the current model. Previously recorded results remain comparison
history. No inputs, RBF smoothing, training budgets, truth values or FEA solves
changed. The whole-grid decrease is primarily an already-trained anchor-plane
effect, not independent validation. `plot_ref_only_calibration.py` regenerates
the SC figure directly from a pipeline JSON using `--results` and `--out`.
