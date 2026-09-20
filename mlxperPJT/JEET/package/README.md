# JEET-repro — sparse AC-loss calibration, reproduced

[![Data DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21775297.svg)](https://doi.org/10.5281/zenodo.21775297)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Code and data to reproduce *Efficient AC Winding Loss Calibration via Sparse
Full Finite-Element Analysis and Separable Radial Basis Function for Scaled
Traction Motor Design* (submitted to the Journal of Electrical Engineering &
Technology).

## What this is

This package rebuilds selected figures and reduced-data calibration results.
It does not yet reproduce every figure or every number of the 2026-09-02
submission. See `FIGURE_STATUS.csv` and `REVIEW_STATUS.md` for the exact gaps.
The raw-data deposit is [10.5281/zenodo.21775297](https://doi.org/10.5281/zenodo.21775297).
Raw solver exports are required for raw verification, not cached-result checks.

The original tree was generated from eMach. `PROVENANCE.txt` preserves that
historical record; this review branch applies bounded maintenance patches
whose source counterparts are recorded in `REVIEW_STATUS.md`. It is not a
new submission-matched release.

## Quick start

```bash
pip install -r requirements.txt
python repro.py all --quick     # figures (fast subset) + checks + audit
python repro.py figs            # all Python-drawn figures (slow sweeps too)
```

or open `notebooks/01…03` in Jupyter. Four environment variables relocate
everything; all are optional:

| variable | meaning | default |
|---|---|---|
| `JEET_DATA_ROOT` | reduced data root; if it also holds a `fea/` directory in the Zenodo layout, raw exports are read from there | `data/e10` |
| `JEET_FIGDIR` | where figures are written | `fig_out/` |
| `JEET_FEA_ROOT` | the author's raw export tree (pre-deposit layout) | unset |
| `JEET_EFFMAP` | efficiency-map `.mat` (`efficiency_map_results.mat`, author-side, not deposited); Table B.1 operating-band rows need it; unavailable input produces null region metrics | unset |

## Figure map

`FIGURE_STATUS.csv` maps the submitted figure numbers to package scripts,
inputs and limitations. In particular, submitted Fig. 9 (field transfer),
Fig. 12 (calibrated efficiency), Fig. 13 (cost), and Fig. B.2 (screening)
are not rebuilt by the legacy default entry point.

`scripts/plotFig15Effmaps.m` renders the older two-MotorLAB-map comparison.
It is not the submitted calibrated Fig. 12. The author-side shaft-map array
can be audited without MATLAB using:

```bash
python scripts/audit_efficiency_array.py --input /path/to/effmap_shaft_SC.npz
```

This command reports a common three-model feasibility mask and the older
per-panel masks separately. It rechecks stored arrays; it does not execute
the shaft-torque trajectory solver, and a missing array exits 2.

## Verification checks

Section 5.1 of the paper states that the Full-FEA solutions pass internal
self-consistency checks before they serve as the reference. The scripts
behind that sentence live in `checks/` and run in three modes:

1. `python repro.py checks` rechecks six shipped result JSON files. It does
   not run a solver or reparse the raw exports.
2. `python repro.py checks --recompute` requests recomputation from the
   configured input sources. The similarity-pair check uses shipped map
   summaries; other checks require raw field or timing files. Set
   `JEET_DATA_ROOT` / `JEET_FEA_ROOT` as appropriate. Missing sources fail.

Exit code 0 indicates that the requested checks passed; nonzero indicates
a failure or unavailable input. Individual scripts distinguish missing
inputs and unavailable raw-source layouts in their diagnostic messages.

| Check | Manuscript number | Recompute source |
|---|---|---|
| `check_conductor_currents.py` | impressed current reproduced to 4 significant figures (460.0 / 920.0 A) | deposit (Ref, SC at 16 kRPM) |
| `check_parseval.py` | Parseval sum of the harmonic decomposition closes within 0.6% | deposit (8 exports) |
| `check_torque_methods.py` | Maxwell-stress, flux-linkage, and virtual-work torques agree within 1% | deposit (Ref, SC); HalfSC needs the author tree |
| `check_similarity_pairs.py` | absolute Full-FEA loss within 1.6% across the 24 grid-matched operating points | none — Map_Summary JSONs ship here |
| `check_field_similarity.py` | mean fundamental-amplitude error about 1.8%, mean proximity-energy error about 2.0%, tangential fraction within 0.005, element-resolved loss −0.7 to −4.8% | HalfSC raw sweep — **not in the deposit**, recompute exits `2` |

The HalfSC raw sweep was deliberately left out of the deposit (the Ref and
SC exports already carry the similarity argument at both ends of the scale
axis); its shipped result JSON documents the numbers, and
`check_field_similarity.py --recompute` says so explicitly instead of
failing silently.

## Numbers audit

```bash
python repro.py audit
```

recomputes, per machine, the sample-candidate pool, the evaluated load
points (96 per machine), and the loss-weighted full-map error before and
after calibration including calibration points. These are the legacy public implementation results, not an independent unseen-point accuracy claim:

| machine | uncorrected wMAE | calibrated wMAE | own Full-FEA samples |
|---|---|---|---|
| Ref (donor) | 45.5% | 0.63% | 36 |
| HalfSC | 33.3% | 0.83% | 27 |
| SC | 26.9% | 0.84% | 27 |

The variants inherit their low-speed calibration from Ref through the
similarity mapping, which is what cuts the two-model computation time by
about 70% against exhaustive Full-FEA. Point `JEET_TEX` at the manuscript
source and the audit also greps the printed text for these strings.

## Data

`data/e10/<machine>/JEET_ACLoss_<machine>_Map_Summary.json` holds, for each
swept operating point, the Full-FEA AC winding loss and the hybrid
prediction at the same point; their ratio is the amplification factor the
calibration learns. Points enter the sample-candidate pool only under load
(`I_rms >= 50 A`; low-current cases are outside the fitted coordinate
domain, and PM-induced AC loss can remain at near-zero armature current); accuracy is reported over every load point regardless.

The rest of `data/` is one file per figure, named after what it carries:

- `fields/` — single-position field snapshots behind Fig. 3;
- `fields/reduced/` — the Fig. 2 inputs: about 650 kB cut from 1.4 GB of
  full-period element exports (slot-1 neighbourhood, every fourth rotor
  position) by `scripts/from_raw/run_cut_fig1_slot_reduction.py`;
- `effmaps/` — the two LAB electrical datasets behind Fig. 11,
  byte-identical to their deposited copies;
- `checks/` — the shipped verification results the `checks/` scripts
  re-evaluate by default;
- the loss-comparison and flux/torque `.mat` summaries behind Figs. 1, 4
  and 9, and the geometry DXF behind Fig. 8.

## Raw data

The full solver exports are deposited separately as the primary record:
[10.5281/zenodo.21775297](https://doi.org/10.5281/zenodo.21775297)
(the DOI resolves after publication of the deposit). The deposit is flat:

```
fea/{Model}_{Mode}_Speed_{rpm}RPM_{amp}A_{beta}deg.txt.gz   (490 files, ~37 GB)
effmaps/*.mat, models/*
```

Download any subset into `$JEET_DATA_ROOT/fea/` and the checks and
reduction scripts pick it up; `jeet_acloss_rbf/repro_env.py` is the single
path resolver all of them share. The HalfSC sweep is not part of the
deposit (see above).

## Provenance

`PROVENANCE.txt` records the eMach source commit, generation time (UTC),
file count, and total size of this tree; `MANIFEST.sha256` lists the
SHA-256 of every shipped file (`sha256sum -c MANIFEST.sha256`). Figures are
compared against the published ones during development; small rendering
differences across matplotlib versions are expected (the published set used
3.10.8) — the plotted values are what the notebooks and checks verify.

## Requirements

`numpy` and `matplotlib` throughout; `scipy` for the figures that read
MATLAB v5 files (Figs. 1, 4, 9, 11-inputs); `ezdxf` for the geometry
section (Fig. 8). MATLAB only for drawing Fig. 11. See
`requirements.txt`.

## License

Code: [MIT](LICENSE). The accompanying data files in `data/` mirror the
Zenodo deposit and are, like it, CC-BY-4.0.

## Citation

See `CITATION.cff` — please cite the paper; the data deposit is
[10.5281/zenodo.21775297](https://doi.org/10.5281/zenodo.21775297).

## Maintenance checks

```bash
python scripts/check_manifest.py
python -m unittest discover -s tests -v
```

The manifest checks exact stored bytes. Normalize text to LF before creating
hashes; a verifier must not silently normalize a damaged checkout.
The CI workflow covers Linux, macOS and Windows when run by GitHub Actions.
Adding the workflow alone is not evidence that those remote jobs passed.
