# JEET-repro — sparse AC-loss calibration, reproduced

[![Data DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21775297.svg)](https://doi.org/10.5281/zenodo.21775297)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Code and data to reproduce *Efficient AC Winding Loss Calibration via Sparse
Full Finite-Element Analysis and Separable Radial Basis Function for Scaled
Traction Motor Design* (submitted to the Journal of Electrical Engineering &
Technology).

## What this is

This repository is reference [32] of the paper: every figure, the five
self-consistency checks of Section 5.1, and the headline error numbers are
rebuilt from this clone (about 9 MB). Reference [31] is the raw-data deposit
([10.5281/zenodo.21775297](https://doi.org/10.5281/zenodo.21775297), about
37 GB) — needed only to re-run the reduction and verification steps from the
solver exports, never for the figures.

This tree is *generated*: a manifest-driven generator inside the eMach
development branch copies each file from its worktree original
(`PROVENANCE.txt` records the exact source commit). Nothing here is edited
by hand.

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
| `JEET_EFFMAP` | efficiency-map `.mat` (`efficiency_map_results.mat`, author-side, not deposited); Table C's operating-band rows need it — without it they fall back to the full-plane numbers | unset |

## Figure map

Numbers follow the submitted manuscript.

| Paper | Output file(s) | Script |
|---|---|---|
| Fig. 1 | `ACDC_ratio_scaling.png` | `scripts/run_fig2_acdc_ratio.py` |
| Fig. 2 | `fig2_{Ref,SC}_ts_vs_2d.png` | `scripts/run_fig1_shared_scale.py` |
| Fig. 3 | `Bfield_MVP_mesh.pdf` | `scripts/run_fig11_mvp_field.py` |
| Fig. 4 | `TS_Hybrid_ratio.png` | `scripts/run_fig4_ts_hyb_ratio.py` |
| Fig. 5 | `proposed_framework_v3.pdf` | `scripts/run_workflow_fig.py` |
| Fig. 6 | `af_transfer_map_hybrid.pdf` | `scripts/run_af_transfer_fig.py` |
| Fig. 7 | `transfer_ablation_{HalfSC,SC}.pdf` | `scripts/run_manuscript_figs78.py` |
| Fig. 8 | `motor_geometry_e10.pdf` | `scripts/run_geometry_fig.py` |
| Fig. 9 | `flux_torque_scaling.pdf` | `scripts/run_flux_torque_fig.py` |
| Fig. 10 | `RBF_correction_validation_SC.png` | `scripts/run_fig10_validation.py` |
| Fig. 11 | `effmap_SC_compare.pdf` | `scripts/plotFig15Effmaps.m` (MATLAB) |
| Fig. A.1 | `eddy_factors_eta.pdf` | `scripts/run_figA1_eddy_factors.py` |
| Fig. B.1 | `hybrid_variants_{speed,compare}.pdf` | `scripts/run_fig_hybrid_variants.py` |
| Fig. C.1 | `form_convergence_{Ref,HalfSC,SC}.pdf` | `scripts/run_manuscript_figs78.py` |
| Fig. C.2 | `ref_ablation.pdf` | `scripts/run_ref_ablation.py` |
| App. B refit | `SC/open_denominator_refit.json` | `scripts/run_open_denominator_refit.py` |
| Table C | `results/form_study.json` | `scripts/run_form_study.py` |

Fig. 11 is the one MATLAB-drawn figure. Its inputs are the two LAB
electrical datasets in `data/e10/effmaps/` (MATLAB v5 files, byte-identical
to the deposited copies — `scipy.io.loadmat` reads them fine, only the
drawing is MATLAB):

```matlab
setenv('JEET_DATA_ROOT', fullfile(pwd, 'data', 'e10'))
setenv('JEET_FIGDIR',    fullfile(pwd, 'fig_out'))
run('scripts/plotFig15Effmaps.m')
```

`scripts/from_raw/run_cut_fig1_slot_reduction.py` rebuilds the reduced
Fig. 2 inputs from the full solver exports (deposit or author tree), so the
reduction step itself can be audited.

## Verification checks

Section 5.1 of the paper states that the Full-FEA solutions pass internal
self-consistency checks before they serve as the reference. The scripts
behind that sentence live in `checks/` and run in three modes:

1. **default** — re-evaluate the shipped result JSONs in `data/e10/checks/`
   and print the manuscript numbers with a pass/fail verdict;
2. **deposit** — when `JEET_DATA_ROOT/fea/` holds files from the Zenodo
   deposit, recompute from the raw exports;
3. **author tree** — when `JEET_FEA_ROOT` points at the pre-deposit layout.

Exit codes: `0` pass, `1` a needed input is not downloaded, `2` the raw
data behind the check is not part of the deposit at all.

| Check | Manuscript number | Recompute source |
|---|---|---|
| `check_conductor_currents.py` | impressed current reproduced to 4 significant figures (460.0 / 920.0 A) | deposit (Ref, SC at 16 kRPM) |
| `check_parseval.py` | Parseval sum of the harmonic decomposition closes within 0.6% | deposit (8 exports) |
| `check_torque_methods.py` | Maxwell-stress, flux-linkage, and virtual-work torques agree within 1% | deposit (Ref, SC); HalfSC needs the author tree |
| `check_similarity_pairs.py` | absolute Full-FEA loss within 1.6% across the 24 grid-matched operating points | none — Map_Summary JSONs ship here |
| `check_field_similarity.py` | fundamental amplitude within 1.8%, proximity-excitation energy within 2.0%, tangential fraction within 0.005, element-resolved loss −0.7 to −4.8% | HalfSC raw sweep — **not in the deposit**, recompute exits `2` |

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
after calibration — the paper's headline **27–45% → 0.6–0.8%**:

| machine | uncorrected wMAE | calibrated wMAE | own Full-FEA samples |
|---|---|---|---|
| Ref (donor) | 45.5% | 0.63% | 36 |
| HalfSC | 33.3% | 0.83% | 27 |
| SC | 26.9% | 0.84% | 27 |

The variants inherit their low-speed calibration from Ref through the
similarity mapping, which is what cuts the two-model computation time by
about 71% against exhaustive Full-FEA. Point `JEET_TEX` at the manuscript
source and the audit also greps the printed text for these strings.

## Data

`data/e10/<machine>/JEET_ACLoss_<machine>_Map_Summary.json` holds, for each
swept operating point, the Full-FEA AC winding loss and the hybrid
prediction at the same point; their ratio is the amplification factor the
calibration learns. Points enter the sample-candidate pool only under load
(`I_rms >= 50 A` — at no load both losses vanish and the ratio is
undefined); accuracy is reported over every load point regardless.

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
