# Motor Repository Comparison Matrix & Entry Points

## Quick Comparison Table

| Aspect | **SyR-e (MATLAB)** | **pyMotorGeo (Python)** | **Integration** |
|--------|---|---|---|
| **Location** | `d:\KangDH\gitSyREpub\syre_public` | `d:\KangDH\Emlab_emach\Class\pyMotorGeo` | Both accessible |
| **Language** | MATLAB/Octave | Python 3.7+ | DXF bridge |
| **Primary I/O** | geo/mat/win → FEMM → .fem | .dxf → EntityInfo → Regions | geo→DXF→analyze |
| **Workflow** | **Design-first**: parametric → FEA | **Reverse-engineer**: CAD → topology | Complementary |
| **Geometry** | Equation-based (parametric) | Entity-based (topological) | Different approaches |
| **Optimization** | ✅ MODE (Pareto) | ❌ Not applicable | Sequential |
| **FEA Solvers** | ✅ FEMM, Maxwell, COMSOL, JMAG | ❌ No integrated FEA | SyR-e solves |
| **CAD Export** | ✅ DXF, Maxwell, COMSOL, etc. | ✅ DXF, Motor-CAD format | Export focus |
| **DXF Import** | ❌ No (generate geometry only) | ✅ Core feature | pyMotorGeo reads |
| **Topology Detection** | ❌ Manual specification | ✅ Auto-detect SPM/IPM/SynRM | Auto vs. manual |
| **Region Classification** | ❌ Not explicitly | ✅ Magnet, barrier, conductor, etc. | pyMotorGeo labels |
| **Maturity** | ✅ 10+ years (published) | ⏳ 1-2 years (research-grade) | SyR-e more stable |
| **Code Style** | Procedural MATLAB | OOP Python | Different paradigms |
| **GUI** | ✅ GUI_Syre.mlapp | ⏳ gui_region.py (experimental) | Both available |
| **Documentation** | ✅ Extensive (papers, wiki) | ⏳ Docstrings + notebooks | Asymmetric |

---

## Execution Matrix: How to Run Each

### SyR-e Entry Points

**Option 1: Graphical User Interface (Easiest)**
```matlab
% 1. Open MATLAB in syre_public directory
cd d:\KangDH\gitSyREpub\syre_public

% 2. Run setup
setupPath()

% 3. Open GUI
appdesigner('GUI_Syre.mlapp')
% Or: Launch from "Open" button in MATLAB GUI
```
→ **Use case:** Interactive design, parameter adjustment, visualization

**Option 2: Scripted Design**
```matlab
% 1. Setup
setupPath()

% 2. Load or define motor
load('motorExamples/syreDefaultMotor.mat')  % geo, mat, win

% 3. Modify parameters
geo.l = 50;  % Stack length [mm]
geo.Rast = 75;  % Stator radius [mm]

% 4. Draw in FEMM
[geo, mat] = draw_motor_in_FEMM(geo, mat, pwd, 'my_motor.fem')

% 5. Evaluate (after FEMM solve)
fluxMap = eval_fluxMap(geo, mat)
loss = evalIronLossFEMM(geo, mat)

% 6. Export
syreToDxfansys(geo, mat, 'motor_export.dxf')
```
→ **Use case:** Batch design, parameter sweeps, optimization loop

**Option 3: Optimization Design**
```matlab
setupPath()

% Configure optimization problem
prob = eval_OptimizatioProblem(geo, mat, win, cost_weight, efficiency_weight);

% Run MODE
MODE(prob, max_generations, population_size)

% Result: Pareto front in MODEplotter
```
→ **Use case:** Multi-objective design, Pareto frontier search

---

### pyMotorGeo Entry Points

**Option 1: Python Pipeline (Recommended)**
```python
from pyMotorGeo.pipeline import analyze_dxf_v2
from pyMotorGeo.export import export_regions_to_dxf

# Read DXF, auto-detect topology
result = analyze_dxf_v2(
    dxf_path='my_motor.dxf',
    n_poles=4,              # If known
    n_slots=24,             # If known
    rotor_topology='IPMSM', # Or: auto-detect
    origin=None             # Auto-find if None
)

# Inspect
print(result['rotor']['topology'])
print(result['geometry'])
print(result['face_summary'])

# Export for Motor-CAD
export_regions_to_dxf(result, output_path='motor_regions.dxf')
```
→ **Use case:** Quick DXF analysis, region detection, CAD interchange

**Option 2: Low-Level Analysis**
```python
from pyMotorGeo import (
    read_entity_list, 
    find_origin_candidates,
    find_concentric_radii,
    split_stator_rotor,
    count_poles,
    count_slots
)

# Read DXF
entities, dxf_doc = read_entity_list('motor.dxf', expand_inserts=True)

# Manual analysis steps
origins = find_origin_candidates(entities)
best_origin = min(origins, key=lambda o: o['score'])

radii = find_concentric_radii(entities, best_origin, n_arcs=10)

rotor_ents, stator_ents = split_stator_rotor(
    entities, 
    origin=best_origin, 
    airgap_radius=50
)

poles = count_poles(rotor_ents, best_origin, 30, 50)
slots = count_slots(stator_ents, best_origin, 55, 75)
```
→ **Use case:** Custom analysis, research, debugging

**Option 3: Interactive GUI**
```python
from pyMotorGeo.gui_region import launch_editor

# Analyze first
result = analyze_dxf_v2('motor.dxf')

# Edit regions interactively
edited = launch_editor(result['half_unit_regions'])

# Save edited regions
export_regions_to_dxf(result, half_unit_regions=edited)
```
→ **Use case:** Manual region correction, visualization tuning

**Option 4: CLI Interface**
```bash
cd d:\KangDH\Emlab_emach\Class

# Analyze DXF
python -m pyMotorGeo analyze motor.dxf --poles 4 --slots 24

# Export
python -m pyMotorGeo export motor.dxf --output motor_regions.dxf --coverage full
```
→ **Use case:** Batch processing, scripting, automation

---

## Detailed Component Mapping

### SyR-e Core Functions Organized by Purpose

#### **Motor Geometry (Input)**
```
defineBlockCenters()      ← Mesh block positions
defineBlockNames()        ← Block naming conventions
buildDefaultRQ()          ← Default reluctance network
interpretRQ()             ← Parse reluctance parameters
```

#### **Rotor Geometry Generation**
```
build_matrix_SPM()        → Surface-mounted PM rotor
build_matrix_Spoke()      → Spoke-type PM
build_matrix_Circ()       → Circular SyR barriers
build_matrix_Seg()        → Segmented SyR barriers
build_matrix_Vtype()      → V-shaped PM
build_matrix_EESM()       → External rotor SR
build_matrix_Fluid()      → Fluid-cooled design
nodes_rotor_*()           ← FEA node generation
```

#### **Stator Geometry Generation**
```
build_matrix_stat()       ← Stator slot/pole layout
nodes_rotor_*()           ← Stator node generation
WindingDefinition()       ← Winding scheme definition
windingCheck()            ← Harmonics & balance check
calcKwTh0()               ← Winding factor & offset
```

#### **Drawing & Meshing**
```
draw_motor_in_FEMM()      ← Main FEA mesh generator
drawSlot()                ← Individual slot shape
drawBar()                 ← Bar winding (cage)
drawPole()                ← Rotor pole shape
draw_airgap()             ← Airgap meshing
dimMesh()                 ← Mesh sizing
```

#### **FEA Evaluation**
```
FEMM_initialize()         ← FEMM interface setup
mi_addboundprop()         ← Boundary conditions
mi_loadsolution_parfor()  ← Parallel solution reading
evalIronLossFEMM()        ← Core losses
FEMMfitness()             ← Objective function
```

#### **Design Equations (SyR/PM-SyR)**
```
syrmDesign/xbPlane_analyticalDesign()  ← PM flux trajectory
syrmDesign/FEAfix()                     ← FEA-correction
syrmDesign/staircaseRegular()           ← Barrier staircase
syrmDesign/evalPMfluxSyrmDesign()       ← PM design
```

#### **Optimization**
```
MODE/jMODE()              ← Multi-objective optimization
MODE/paretoset()          ← Pareto frontier
MODE/nonDominationSort()  ← NSGA-II ranking
FastParetoEstimation()    ← Surrogate model
```

#### **Export Modules**
```
syre_AnsysMaxwell/        ← ANSYS Maxwell CAD/FEA export
syre_COMSOL/              ← COMSOL structural FEA export
syre_JMAG/                ← JMAG CAD parameters
syre_MagNet/              ← MagNet CAD/FEA export
syre_MotorCAD/            ── MCAD thermal/EM analysis
syre_Dxf/syreToDxf.m      ← DXF geometry export
```

---

### pyMotorGeo Core Functions Organized by Purpose

#### **File I/O**
```
read_entity_list()        → Load DXF, return EntityInfo[]
                            optional: expand_inserts
export_regions_to_dxf()   → Save classified regions to DXF
                            options: coverage, part_filter, layer_by_name
```

#### **Origin & Reference Detection**
```
find_origin_candidates()  → Find motor axis from geometry
                            returns: [(x, y, score), ...]
find_concentric_radii()   → Group entities by shared radius
                            returns: [(radius, count), ...]
```

#### **Rotor/Stator Separation**
```
find_airgap_radius()      → Locate rotor/stator boundary
split_stator_rotor()      → Separate entities by radius
                            returns: (rotor_ents, stator_ents)
find_airgap_by_arc_span() → Alternative: gap via angular features
```

#### **Pole & Slot Counting**
```
count_poles()             → Determine n_poles from rotor features
count_slots()             → Determine n_slots from stator features
count_poles_by_regions()  → Alternative: count from closed regions
estimate_poles_robust()   → Robust multi-method estimation
detect_slot_conductors()  → Identify conductor locations
```

#### **Closed Region Detection**
```
find_closed_regions()     → Topologically find closed loops
                            returns: [face1, face2, ...]
face_detection.py         → Advanced topological closure
region_closing.py         → Closure algorithm options
```

#### **Topology Classification**
```
RotorCounter.classify()   → Identify SPM vs. IPM vs. SynRM
                            returns: topology string + detail dict
RotorTopologyClassifier   → Region-level classification
  .classify_rotor_entities()  per region: magnet/barrier/iron
  
StatorCounter.classify()  → Slot & conductor detection
StatorTopologyClassifier  → Region classification
  .classify_stator_entities() per region: conductor/tooth/yoke
```

#### **Symmetry & Replication**
```
symmetry.detect_rotational_symmetry()  → Find repeat angle
symmetry.apply_symmetry()              → Replicate features
half_unit.extract_half_pole_entities() → Extract single pole
half_unit.extract_half_slot_entities() → Extract single slot
half_unit.reconstruct_from_half()      → Full motor from sector
```

#### **Export Formats**
```
export_regions_to_dxf()   → Standard DXF with color/layer
motorcad_bridge()         → Motor-CAD Adaptive Geometry format
pyleecan_bridge()         → Pyleecan model (future)
```

#### **Visualization**
```
plotting.py               → Matplotlib figures
gui_region.py             → Interactive region editor
palantir_viz/             → 3D interactive view
```

---

## Workflow Integration Scenarios

### Scenario 1: Parametric Design → FEA → CAD Export

```
SyR-e MATLAB workflow
├─ Define: geo.p=4, geo.q=6, geo.l=50, etc.
├─ Draw: [geo,mat] = draw_motor_in_FEMM(geo,mat,...)
├─ Solve: openfemm(1); (FEMM computes flux/torque/loss)
├─ Export: syreToDxfansys(geo, mat, 'output.dxf')
└─ Downstream: Import output.dxf to ANSYS, Motor-CAD, etc.
```

### Scenario 2: DXF Reverse-Engineering → Region Analysis → Import

```
pyMotorGeo Python workflow
├─ Start: Existing motor CAD file (motor.dxf)
├─ Analyze: analyze_dxf_v2(motor.dxf, n_poles=4, n_slots=24)
├─ Inspect: Check result['rotor']['topology'], result['geometry']
├─ Export: export_regions_to_dxf(result, output='regions.dxf')
└─ Downstream: regions.dxf → Motor-CAD, ANSYS, visualization
```

### Scenario 3: SyR-e → DXF → pyMotorGeo → Motor-CAD

```
Sequential integration
┌─────────────────────────┐
│ SyR-e parametric design │
│ (geo, mat, win defined) │
└────────────┬────────────┘
             │
             ↓ syreToDxf.m
        [motor.dxf]
             │
             ↓ analyze_dxf_v2()
    ┌────────────────────────┐
    │ pyMotorGeo analysis    │
    │ (topology detected)    │
    └────────────┬───────────┘
                 │
                 ↓ export_regions_to_dxf()
            [motor_regions.dxf]
                 │
                 ↓ Motor-CAD import
        ✓ Ready for thermal analysis
```

### Scenario 4: Design Space Exploration

```
Multi-objective optimization (SyR-e MODE)
┌──────────────────────────┐
│ Parameter ranges:        │
│ - Barrier count          │
│ - PM amount              │
│ - Stator bore (Rast)     │
│ - Stack length (l)       │
└──────────────┬───────────┘
               │
               ↓ MODE.jMODE()
         (1000s evaluations)
               │
               ↓ Pareto frontier
        ┌──────────────────┐
        │ 100 best designs │
        │ (efficiency vs.  │
        │  cost trade-off) │
        └────────┬─────────┘
                 │
                 ↓ Select best
         [Final geometry]
                 │
                 ↓ syreToDxf()
            Export CAD


Multi-topology exploration (pyMotorGeo)
[CAD library]
    │
    ├─→ motor_spm.dxf  → analyze_dxf_v2() → [SPM regions]
    ├─→ motor_ipm.dxf  → analyze_dxf_v2() → [IPM regions]
    └─→ motor_synrm.dxf → analyze_dxf_v2() → [SynRM regions]
         │
         → Compare geometries, region distributions
```

---

## Directory Quick Navigation

### SyR-e

| Path | Contents | Start With |
|------|----------|-----------|
| `mfiles/` | Core functions | `draw_motor_in_FEMM.m` |
| `syreExport/` | Multi-tool export | `syre_Dxf/syreToDxf.m` |
| `motorExamples/` | Reference designs | `syreDefaultMotor.mat` |
| `mfiles/MODE/` | Optimization | `jMODE.m` |
| `mfiles/syrmDesign/` | SyR / PM-SyR design | `xbPlane_analyticalDesign.m` |
| `GUI_Syre.mlapp` | Interactive interface | Run `setupPath()` first |

### pyMotorGeo

| Path | Contents | Start With |
|------|----------|-----------|
| `pipeline.py` | High-level workflow | `analyze_dxf_v2()` |
| `core.py` | Data structures | `EntityInfo` class |
| `reader.py` | DXF I/O | `read_entity_list()` |
| `analysis.py` | Geometry analysis | `find_origin_candidates()` |
| `analysis_rotor.py` | Rotor detection | `RotorCounter.classify()` |
| `analysis_stator.py` | Stator detection | `StatorCounter.classify()` |
| `export.py` | DXF export | `export_regions_to_dxf()` |
| `palantir_viz/` | 3D visualization | (experimental) |

---

## Key Code Examples (Copy-Paste Ready)

### SyR-e: Save & Load Motor

```matlab
% Setup
setupPath()

% Load example
load('motorExamples/syreDefaultMotor.mat')

% View geo structure
geo  % [p=4, q=6, l=50, ...]

% Modify
geo.l = 60;  % New stack length

% Save
save('my_motor_design.mat', 'geo', 'mat', 'win')
```

### pyMotorGeo: Quick Analysis

```python
from pyMotorGeo.pipeline import analyze_dxf_v2

result = analyze_dxf_v2('motor.dxf', n_poles=4, n_slots=24)

print(f"✓ Topology: {result['rotor']['topology']}")
print(f"  Geometry: Rast={result['geometry']['Rast']}mm, "
      f"l={result['geometry']['l']}mm")
print(f"  Magnet area: {result['rotor']['magnet_area']:.1f}mm²")
```

### Integration: Export SyR-e to Motor-CAD

```matlab
% In SyR-e
setupPath()
load('syreDefaultMotor.mat')
[geo, mat] = draw_motor_in_FEMM(geo, mat, pwd, 'motor.fem')

% Export to DXF (ANSYS/Maxwell format)
syreToDxfansys(geo, mat, 'motor_for_ansys.dxf')
```

```python
# In Python (read that DXF)
from pyMotorGeo.pipeline import analyze_dxf_v2
from pyMotorGeo.export import export_regions_to_dxf

result = analyze_dxf_v2('motor_for_ansys.dxf', 
                        n_poles=4, n_slots=24, 
                        rotor_topology='SPM')

export_regions_to_dxf(result, 
                     output_path='motor_for_mcad.dxf',
                     layer_by_name=True)

# Import motor_for_mcad.dxf in Motor-CAD GUI
```

---

## Performance Notes

| Operation | SyR-e | pyMotorGeo | Time |
|-----------|-------|-----------|------|
| Load motor | `load('*.mat')` | N/A | <1 sec |
| Draw in FEMM | `draw_motor_in_FEMM()` | N/A | 5-20 sec |
| FEMM solve | `openfemm(1)` → solver | N/A | 30 sec - 5 min |
| Read DXF | N/A | `read_entity_list()` | 0.5-2 sec |
| Analyze DXF | N/A | `analyze_dxf_v2()` | 1-5 sec |
| Export DXF | `syreToDxf()` | `export_regions_to_dxf()` | 0.5-2 sec |
| MODE optimization | `MODE()` | N/A | varies (1000s evals) |

---

## Summary of Key Takeaways

| Aspect | Use **SyR-e** | Use **pyMotorGeo** |
|--------|---|---|
| I have motor **parameters**... | ✅ Design from scratch OR modify existing | ❌ Not applicable |
| I have a **DXF file**... | ❌ Can't directly read | ✅ Analyze & auto-classify |
| I need **FEA analysis**... | ✅ FEMM/Maxwell/COMSOL built-in | ❌ Export only, need external solver |
| I need **CAD for Motor-CAD**... | ✅ Via DXF export | ✅ Direct region export |
| I need **region classification**... | ❌ Manual specification | ✅ Auto-detect SPM/IPM/SynRM |
| I need **optimization**... | ✅ MODE (Pareto frontier) | ❌ Not applicable |
| I want **Python workflow**... | ❌ MATLAB-dependent | ✅ Pure Python |
| I want **batch processing**... | ✅ MATLAB scripting | ✅ Python loops/batch |

