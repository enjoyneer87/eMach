# Notebook Function Migration Plan

Date: 2026-03-31
Scope: mlxperPJT/pyMotorGeo_v1.ipynb -> Class/pyMotorGeo package modules

## 1) Goal

Reduce notebook-defined business logic and keep notebook as an orchestration/demo layer only.

Target end state:
- Notebook cells mainly call package APIs.
- Domain logic exists in package modules only.
- Repeated fallback implementations are removed from notebook.

## 2) Current Baseline

Observed in notebook:
- Approximately 47 inline function definitions.
- Major concentration in environment/fallback block and DXF parsing helper.
- One visualization block already migrated to package wrapper (`create_interactive_visualization`).

## 3) Migration Principles

- Keep behavior stable first, then simplify internals.
- Migrate in small batches with notebook execution checks after each batch.
- Preserve variable names used by downstream cells to avoid breakage.
- Prefer package imports over inline notebook function definitions.

## 4) Batch Plan

### Batch A (Low Risk): Reader and lightweight helpers

Actions:
- Remove notebook-local `_manual_parse_dxf_entities` by moving equivalent logic to package reader API.
- Replace notebook calls with package import and function call.

Target module:
- Class/pyMotorGeo/reader.py

Validation:
- Notebook cell sequence for DXF load executes without NameError.
- Entity counts remain within expected tolerance.

### Batch B (Low Risk): Visualization and plotting leftovers

Actions:
- Keep notebook visualization as wrapper-only cells.
- Ensure any remaining drawing helpers used in later cells are provided by package plotting API.

Target module:
- Class/pyMotorGeo/plotting.py

Validation:
- Interactive cell renders and downstream plots execute.

### Batch C (Medium Risk): Analysis fallback block split

Actions:
- Remove inline fallback analysis functions from notebook cell 5.
- Replace with imports from analysis/airgap/topology/half_unit/face modules.

Target modules:
- Class/pyMotorGeo/analysis_airgap.py
- Class/pyMotorGeo/analysis.py
- Class/pyMotorGeo/half_unit.py
- Class/pyMotorGeo/topology.py
- Class/pyMotorGeo/face_detection.py
- Class/pyMotorGeo/region_closing.py

Validation:
- Pole/slot detection, split, and half-unit extraction cells run successfully.
- Key numeric outputs (n_poles, n_slots, airgap range) match baseline behavior.

### Batch D (Medium Risk): Bridge and topology wrappers

Actions:
- Remove notebook fallback wrappers for pyleecan bridge and region summary functions.
- Use package API only.

Target modules:
- Class/pyMotorGeo/pyleecan_bridge.py
- Class/pyMotorGeo/regions.py

Validation:
- pyleecan availability branch behaves as before.
- Region summary outputs are present.

### Batch E (Finalize): Notebook cleanup and docs sync

Actions:
- Remove obsolete inline function definitions entirely.
- Keep notebook cells concise and task-oriented.
- Update progress/report markdown.

Validation:
- End-to-end notebook run (core path) completes.
- No inline business-logic function definitions remain (except optional temporary experiment stubs).

## 5) Risks and Mitigations

Risk: Existing notebook depends on variable side effects from inline functions.
Mitigation: Preserve outputs/variable names in wrapper cells during each batch.

Risk: Import path differences in notebook/package execution contexts.
Mitigation: Use package-relative import with safe fallback where needed.

Risk: Regression in geometry counts and reconstruction entities.
Mitigation: Compare baseline metrics after each batch.

## 6) Acceptance Criteria

- Notebook runs through core analysis path without inline business-logic functions.
- Package modules contain migrated logic and compile successfully.
- Interactive visualization and reconstruction outputs remain functional.

## 7) Progress Log

- [x] Plan document created.
- [x] Baseline function inventory recorded.
- [x] Batch A started (reader helper migration).
- [x] Batch A step 1 done: `manual_parse_dxf_entities` migrated to package.
- [x] Batch A step 2 done: notebook DXF load cells switched to `manual_parse_dxf_entities` package call.
- [ ] Batch B completed.
- [ ] Batch C completed.
- [ ] Batch D completed.
- [ ] Batch E completed.
