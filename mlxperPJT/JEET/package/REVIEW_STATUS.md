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
| Predicted-loss transfer before exact anchor (historical) | 0.6308 / 1.9911 | 0.8424 / 2.6374 | 0.7616 / 2.2001 |

Values are wMAE in percent. Full-map evaluation includes calibration points;
held-out excludes the target's own training indices only. These are not new
independent FEA validation results. The submitted rounded numbers match the
existing author implementation, not the older public release.

The previous author implementation directly read four Ref truth points outside
its stated 36-point training set when transferring to SC. The adopted method always
uses the frozen donor prediction times donor hybrid loss. The author tests
confirm that hiding all 60 unselected Ref truth values leaves the SC pipeline
prediction unchanged, and a hybrid-only donor object is sufficient for transfer.
The raw datasets are retained. A separate submission-based author-review manuscript now records the Ref-only calculation.

The author clarified that M4-2 concerns empirical robustness after refitting
AF to the same Full-FEA samples, not exact invariance of every prediction.
The historical pre-anchor 2.7x denominator diagnostic changed predictions by
about 1.86%; it is retained as history, not an unresolved requirement to force
exact invariance. The new Ref-only exact-anchor comparison gives a maximum
pointwise change of 0.56% for that numerical rescaling diagnostic. This does
not establish robustness to arbitrary physical evaluators.

## Efficiency result

The author cached shaft-map array has SHA-256
`3e448bbb2f606e0b7542e597a33803d22b81df88481d177cc566d54f24869bf2`.
On 4370 common feasible nodes, mean absolute residuals are 0.469716 and
0.226422 percentage points (uncalibrated and calibrated). The older panel masks
give 0.467260 and 0.225219. Both round to 0.47 / 0.23. This is a stored-array
recheck; the solver/input chain is not yet packaged. The old H/F MotorLAB arrays
are a different calculation and must not be substituted.

## Still open

- Remaining figures and final abstract after full workflow validation; transfer and exact-anchor decisions are complete.
- Public packaging of the locally verified Ref-only field-to-loss calculation, independent test grid, and FEA convergence.
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

## Exact speed anchor adopted, 2026-09-20

The default speed fit now enforces f(base)=p(base)=1 using
q=1+a*x+b*x^2 with x=s/base-1 and equal weight per speed. The per-speed
regressions, RBF fit, training budgets and predicted-loss transfer are unchanged.
Exported speed expressions retain the shifted basis so coefficient serialization
preserves the anchor. This is exact preservation of the fitted RBF shape; its
regularization still allows residuals against Full-FEA at calibration points.

| Current exact-anchor path | Ref full / own-held-out | HalfSC full / own-held-out | SC full / own-held-out |
|---|---|---|---|
| Bundled deposited-hybrid evaluator | 0.613050 / 1.991268 | 0.814834 / 2.638148 | 0.716587 / 2.199438 |
| Author Ref-only public evaluator | 0.982584 / 3.295904 | 1.203463 / 4.009746 | 1.155889 / 3.449489 |

Values are wMAE in percent. All-grid improvement mainly reflects preservation
of the already-trained 16 kRPM plane. No independent generalization improvement
is inferred. The Ref-only row is calculated in the author worktree; its complete
input/runner packaging is still part of M8. The older tables and stored figures
above remain historical comparisons. In particular the efficiency and denominator
invariance diagnostics predate this change and have not been recomputed here.

The Windows test suite now has 10 passing contracts, including an independent
KKT optimum, sparse-speed fits, native/exported anchors, donor truth masking,
and consistency between the default/ablation/cost paths. Linux/macOS execution
of this exact-anchor revision is not claimed. No public release was pushed.

## Evaluator-robustness comparison, 2026-09-20

An optional validated `index_plan` now freezes both target Full-FEA coordinates
and donor-probe coordinates in transfer fits. Default placement and adopted
results are unchanged. Invalid/duplicate/wrong-speed plans are rejected.
The Windows suite now has 11 passing tests.

The author Ref-only comparison holds the field spectra, truth, coordinates,
RBF regularization and exact anchor fixed. SC all-grid / own-held-out wMAE is
1.1559/3.4495% (capped /24), 1.1156/3.2727% (G2), and 0.6663/1.9227%
(G2 with modified skin depth). The uncapped /24 evaluator gives
7.0771/22.1647%. These are retrospective comparisons, not new independent FEA.
All planned regression samples were admitted; truth masking leaves all outputs
unchanged. The physical kernels were not tuned to these results.

The main capped evaluator has not been changed. The author is being interviewed
on retaining the alternatives as appendix robustness evidence versus considering
a new primary evaluator. The full Ref-only input/runner release remains an M8
item. `run_evaluator_robustness.py` and its kernel checks are in the author tree;
the portable transfer API and its regression check are mirrored here.
