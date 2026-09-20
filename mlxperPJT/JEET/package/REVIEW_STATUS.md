# Review maintenance branch, 2026-09-20

This is a local review candidate based on public commit
`c11164cf73e773532029ea708646686fe09fde8f`. It is not a submission-matched release.
The historical `PROVENANCE.txt` has deliberately not been rewritten to imply
that the old package was generated from a clean source tree.

The counterpart author branch is `codex/jeet-review-20260920`, based on eMach
`fceb1fb`. Common packaging fixes are maintained in its source library and
package directory. The author accepted removal of the four extra donor truth lookups. Both
branches now default to `predicted_loss`; direct truth lookup (`numerator`)
is rejected. Historical implementations remain reproducible from earlier commits.
Full regeneration still awaits the remaining figure/input provenance work.

## Repairs in this branch

- OS-neutral relative paths in the dataset configuration.
- Candidate counts use the pipeline's actual admission rule (96 loaded points).
- Explicit cached-result versus requested recomputation modes.
- Missing operating-band inputs produce unavailable/null region metrics.
- Exact-byte manifest verifier and LF-normalized maintenance manifest.
- Submission figure coverage map; unavailable generators are explicitly marked.
- Common-mask efficiency-array audit, distinct from solving trajectories.
- Regression checks and a Linux/macOS/Windows CI workflow.
- Author generator normalizes text even when LF-folded content already matches.

## Scientific reconciliation (same bundled map summaries)

| Implementation | Ref full / held-out | HalfSC full / held-out | SC full / held-out |
|---|---|---|---|
| Reviewed public direct-AF transfer | 0.6308 / 1.9911 | 0.8285 / 2.6323 | 0.8399 / 2.5459 |
| Existing author numerator transfer | 0.6308 / 1.9911 | 0.8424 / 2.6374 | 0.7868 / 2.2190 |
| Adopted predicted-loss transfer (both branches) | 0.6308 / 1.9911 | 0.8424 / 2.6374 | 0.7616 / 2.2001 |

Values are wMAE in percent. Full-map evaluation includes calibration points;
held-out excludes the target's own training indices only. These are not new
independent FEA validation results. The submitted rounded numbers match the
existing author implementation, not the older public release.

The previous author implementation directly read four Ref truth points outside
its stated 36-point training set when transferring to SC. The adopted method always
uses the frozen donor prediction times donor hybrid loss. The author tests
confirm that hiding all 60 unselected Ref truth values leaves the SC pipeline
prediction unchanged, and a hybrid-only donor object is sufficient for transfer.
The raw datasets are retained. The manuscript has not yet been edited.

Global denominator-scale invariance is **open**: scaling both hybrid baselines by
2.7 changes the fitted SC prediction by up to about 1.86% in this diagnostic.
The author test records this as an expected failure, not a passed requirement.
The independent polynomial speed fits are not closed under the corresponding
transformation of the level function; transferring a consistent quantity alone
does not establish invariance of the fitted model family.

## Efficiency result

The author cached shaft-map array has SHA-256
`3e448bbb2f606e0b7542e597a33803d22b81df88481d177cc566d54f24869bf2`.
On 4370 common feasible nodes, mean absolute residuals are 0.469716 and
0.226422 percentage points (uncalibrated and calibrated). The older panel masks
give 0.467260 and 0.225219. Both round to 0.47 / 0.23. This is a stored-array
recheck; the solver/input chain is not yet packaged. The old H/F MotorLAB arrays
are a different calculation and must not be substituted.

## Still open

- Manuscript wording and exact-value updates after adoption; transfer decision is complete.
- Reference-only field-to-final-loss validation, independent test grid, and FEA convergence.
- TPS formulation/full-model comparison and denominator-refit consistency.
- Packaging the calibrated efficiency solver and remaining submitted figures.
- Clean-source full regeneration, exact submitted PDF/source binding, release tag.
- Actual macOS execution. A configured CI job is not a completed test.

## Adoption checks

The default, ablation and cost-accuracy paths use the same predicted-loss
transfer. Regression checks cover the full pipeline with all 60 unselected Ref
truth/AF values hidden, a donor object containing hybrid data only, and agreement
of the adopted ablation/cost cell with the main model. Historical direct-AF
comparison remains available with explicit `rule='ratio'`; direct truth lookup
is no longer an available transfer rule.

The old workflow diagram still prints a direct-AF equation. Its author-approved
manuscript replacement is pending, and FIGURE_STATUS.csv flags that limitation.
The stored efficiency-array result above predates adoption; it has not been
recomputed with the adopted AF model in this change.
