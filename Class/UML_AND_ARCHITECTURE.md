# pyMotorGeo Architecture & Documentation (v1.5.1)

## Overview

**pyMotorGeo** is a Python library for automated motor geometry analysis from CAD (DXF) files. It extracts motor topology (poles, slots, rotor/stator regions) and detects region boundaries through topological face closure.

**Version**: v1.5.1 (Post-Documentation Phase)  
**Status**: ✅ Fully documented with NumPy/Google docstrings  
**Target Users**: Motor designers, control engineers, FEA analysts

---

## 📊 UML Diagrams

A comprehensive set of PlantUML diagrams has been created to visualize the architecture:

### 1. **pyMotorGeo_Architecture.puml** — Class & Component Diagram
- Shows all major classes and their relationships
- Packages: Core, Analysis, Topology, UI, Pipeline, Advanced Features
- Best for: Understanding class hierarchy and overall structure

### 2. **pyMotorGeo_Workflow.puml** — Sequence Diagram
- Illustrates step-by-step analysis workflow
- 7 phases: Read → Analyze → Detect → Classify → Refine → Export
- Best for: Understanding execution flow and when functions are called

### 3. **pyMotorGeo_Dependencies.puml** — Module Dependency Graph
- Shows which modules import/depend on others
- External dependencies: numpy, matplotlib, shapely, ezdxf, pyleecan
- Best for: Understanding import structure and optional features

### 4. **pyMotorGeo_DataTransform.puml** — Data Flow Diagram
- Visualizes data transformations: DXF → EntityInfo → StatorRotorSplit → Face → Region
- Shows input/output of major pipeline stages
- Best for: Understanding data structures and transformations

### 5. **pyMotorGeo_RotorTopologies.puml** — Rotor Classification Logic
- Decision tree for classifying rotor topology (SPM, IPM, SynRM)
- Shows classification heuristics by face properties
- Best for: Understanding rotor topology detection

### 6. **pyMotorGeo_StatorTopologies.puml** — Stator Classification Logic
- Multi-zone analysis for stator slot classification
- Shows how faces are labeled (slot, tooth, yoke, conductor, wedge)
- Best for: Understanding stator region classification

### 7. **pyMotorGeo_Refactoring_Plan.puml** — Future OOP Refactoring
- Current state: Code duplication in analysis & topology modules
- Proposed solution: Base class hierarchy (ComponentCounter, ComponentTopologyClassifier)
- Timeline: Post-v1.5.1 (Optional, planned for v1.6+)

### 8. **pyMotorGeo_CompletionStatus.puml** — Documentation Completion Map
- Phase-by-phase module status with ✓ checkmarks
- Green boxes: Fully documented
- Orange boxes: Architecture/base classes created
- Best for: Quick reference on what's documented

---

## 📁 Module Organization

### **Phase 1: Core Foundation** ✅
```
core.py
├── EntityInfo          (DXF line/arc entity wrapper)
├── StatorRotorSplit    (Split result container)
└── Utilities: rotate, mirror, distance functions

reader.py
├── read_entity_list()  (DXF parsing)
└── Layer/block/color extraction
```

### **Phase 2: Geometry Extraction** ✅
```
half_unit.py
├── extract_half_pole_entities()
├── extract_half_slot_entities()
├── compute_polygon_area_shoelace()
└── detect_mirror_symmetry()
```

### **Phase 3-4: Analysis** ✅
```
analysis_rotor.py
├── count_poles()
├── count_poles_by_pattern()
├── detect_pole_pattern() [ARC, FFT]
└── estimate_poles_robust()

analysis_stator.py
├── count_slots()
├── count_slots_by_regions()
├── detect_slot_conductors()
└── estimate_slots_robust()

analysis_airgap.py
├── find_origin_candidates()
├── find_concentric_radii()
├── analyze_closed_regions_for_motor_type()
└── split_stator_rotor()  ← Main split function

analysis_base.py  [Future]
└── ComponentCounter (abstract base class)
```

### **Phase 5-1: Core Topology** ✅
```
topology.py
├── detect_circular_array_pattern()
├── classify_pole_topology()  [SPM, IPM, SynRM]
├── analyze_rotor_topology()
└── reconstruct_from_half()   [Expand MRU]

topology_base.py  [Future]
└── ComponentTopologyClassifier (abstract base class)
```

### **Phase 5-2: Specialized Topology** ✅
```
topology_stator.py
├── classify_stator_entities()
├── classify_stator_entities_with_closing_compare()
├── reassign_stator_region()
└── get_stator_region_summary()
   [Yoke, Tooth, Slot, Conductor, Wedge]

topology_rotor.py
├── classify_rotor_entities()
├── reassign_rotor_region()
└── get_rotor_region_summary()
   [Magnet, AirBarrier, Core, Shaft]
```

### **Phase 5-3: Region Closure & Visualization** ✅
```
region_closing.py
├── create_radial_line()          [Synthetic boundary]
├── create_arc_boundary()         [Arc closure]
├── close_one_pole()              [Entire workflow]
├── detect_closed_faces()         [Shapely/Planar graph]
├── auto_name_faces()             [Region classification]
└── get_face_summary()            [Statistics]

face_detection.py  [Shapely backend]
├── entity_to_linestring()
├── find_interior_point()         [Grid + centroid fallback]
└── check_polygon_feasibility()

gui_region.py
├── FaceRegionGUI                 [Jupyter + matplotlib]
│  ├── show()                     [Interactive plot]
│  ├── get_faces()                [Export results]
│  └── _on_click(), _on_assign()  [Event handlers]
└── FaceRegionGUILite             [VS Code + matplotlib]
   ├── show()
   └── keyboard_controls()        [1-9 keys, 'e' cycle]

plotting.py
├── plot_period()
├── plot_reconstructed_motor()
└── plot_named_faces()
```

### **Phase 5-4: Export & Integration** ✅
```
symmetry.py
├── identify_symmetry_break()
├── extract_one_period()
├── expand_sector()
└── reconstruct_full_motor()     [Rotation + mirroring]

export.py
├── export_regions_to_dxf()
└── export_to_ansys_maxwell_dxf()

pyleecan_bridge.py
├── extract_dimensions_from_dxf()
├── create_pyleecan_machine()    [Main export]
├── build_rotor_from_faces()
└── build_stator_from_faces()
   [Targets: MachineSIPMSM, MachineIPMSM, MachineSyRM]

pipeline.py
├── analyze_dxf_v2()             [Modern, recommended]
├── analyze_motor_dxf()          [Legacy v1.0]
└── quick_analyze()              [Lightweight]

cli.py
├── command_analyze()
├── command_export()
└── command_quick()
   Entry: python -m pyMotorGeo
```

---

## 🔄 Data Pipeline

```
motor.dxf (CAD Model)
    ↓
[reader.py] read_entity_list()
    ↓
list[EntityInfo]  (100-1000 entities)
    ↓
[analysis_airgap] split_stator_rotor()
    ↓
StatorRotorSplit {
    stator: list[EntityInfo],
    rotor: list[EntityInfo],
    airgap_inner_r, airgap_outer_r
}
    ↓
[analysis_rotor] count_poles()
[analysis_stator] count_slots()
[topology] classify_pole_topology()
    ↓
Topology Info {
    n_poles: int,
    n_slots: int,
    rotor_topo: 'SPM|IPM|SynRM',
    confidence: float
}
    ↓
[region_closing] close_one_pole() + detect_closed_faces()
    ↓
list[Face] {
    vertices: list[(x,y)],
    area, centroid, centroid_r, ...,
    name: 'unknown'  ← To be filled
}
    ↓
[auto_name_faces] + [topology_rotor/stator]
    ↓
list[Face_Classified] {
    vertices, area, centroid, ...,
    name: 'magnet|slot|tooth|...'
}
    ↓
[gui_region.FaceRegionGUI] ← Optional user refinement
    ↓
[export] Export to DXF, JSON, Pyleecan
    ↓
motor_analyzed.dxf, machine.pkl, results.json
```

---

## 📊 Rotor Topology Classification

```
Detected Closed Faces
    ↓
Analyze each face:
  - centroid_r (distance from origin)
  - area (face size)
  - r_max (outer extent)
    ↓
Decision Tree:
  ├─ Surface magnets? (r_max > 0.85*R_outer)
  │  └─ YES → SPM (Surface Permanent Magnet)
  │  └─ NO  ↓
  ├─ Interior magnets?
  │  └─ YES → IPM (Interior PM with air barriers)
  │  └─ NO  ↓
  └─ Air barriers?
     └─ YES → SynRM (Reluctance motor)
     └─ NO  → Unknown hybrid
```

---

## 🎯 Stator Region Classification

```
One Slot's Faces
    ↓
Partition by radial zones:
  Zone 1: Near airgap  [r_inner, mid]
  Zone 2: Deep slot    [mid, tooth]
  Zone 3: Near yoke    [tooth, r_outer]
    ↓
Classify by area + radial extent:
  ├─ area > 100 → SLOT (main region)
  ├─ area < 5   → SLOT_OPENING (edge)
  ├─ Δr > 30%   → STATOR_TOOTH (pole piece)
  ├─ Δr < 30%   → STATOR_YOKE (back iron) or WEDGE
  └─ Centroid near surface → CONDUCTOR
```

---

## 🚀 Quick Start Examples

### CLI Usage
```bash
# Basic analysis
python -m pyMotorGeo analyze motor.dxf

# Export to JSON
python -m pyMotorGeo analyze motor.dxf --export json --output result.json

# Export to Pyleecan
python -m pyMotorGeo analyze motor.dxf --export pyleecan --output machine.pkl
```

### Python API
```python
from pyMotorGeo.pipeline import analyze_dxf_v2

result = analyze_dxf_v2(
    dxf_path='motor.dxf',
    n_poles=4,
    n_slots=24,
    rotor_topology='IPMSM'
)

print(f"Poles: {result['rotor']['n_poles']}")
print(f"Slot summary: {result['face_summary']}")

# Optional: Launch GUI for refinement
from pyMotorGeo.gui_region import FaceRegionGUI
gui = FaceRegionGUI(
    faces=result['faces'],
    origin=(0, 0),
    region_names=...,
    region_colors=...
)
gui.show()
```

---

## 🏗️ Architecture Highlights

### Strengths
- ✅ **Modular Design**: Clear separation of concerns (Read → Analyze → Classify → Export)
- ✅ **OOP Ready**: Base classes prepared for future refactoring
- ✅ **Flexible Input**: Supports multiple DXF layer/block/color schemes
- ✅ **Multiple Rotor Types**: SPM, IPM, SynRM, hybrid detection
- ✅ **GUI + CLI**: Both interactive and batch workflows
- ✅ **Shapely Integration**: Optional advanced topological analysis

### Areas for Improvement (Future)
- 🔄 **Code Duplication**: analysis & topology modules share ~70-80% code
  - **Plan**: Implement base class hierarchy (Option A, v1.6+)
- 📚 **Limited Winding Definition**: Basic lamination geometry only
- 🧮 **Thermal/Mechanical**: Extracted but not validated

---

## 📖 Documentation Standards

All modules follow **NumPy/Google Hybrid Docstring Format**:

```python
def classify_stator_entities(
    slot_entities: List[Dict],
    origin: Tuple[float, float] = (0.0, 0.0),
    airgap_r: float = None,
    ...
) -> Dict:
    """
    Short summary (one sentence).
    
    Longer description (1-3 paragraphs) with context,
    background, and motivation.

    Parameters
    ----------
    slot_entities : List[Dict]
        Detailed parameter description with types
    origin : Tuple[float, float], optional
        Optional parameter with default
    ...

    Returns
    -------
    Dict
        Return value description with structure

    Algorithm
    ---------
    Step-by-step algorithm explanation with formulas
    
    Examples
    --------
    >>> result = classify_stator_entities(...)
    >>> print(result['regions'])
    
    Use Cases
    ---------
    - Use case 1 (e.g., GUI integration)
    - Use case 2 (e.g., batch processing)
    
    Notes
    -----
    - Important caveat or limitation
    - Performance characteristic
    - Integration hint
    """
```

---

## 🔗 Integration Ecosystem

```
pyMotorGeo (Geometry Analysis)
    ↓
[pyleecan_bridge] → Pyleecan (FEA, loss, thermal analysis)
    ↓
[export] → ANSYS Maxwell, FEA solver scripts
    ↓
Results: Efficiency maps, torque curves, thermal distribution
```

---

## 📋 Completion Status (v1.5.1)

| Phase | Module | Status | Docstrings | Examples | Notes |
|-------|--------|--------|-----------|----------|-------|
| 1 | core.py, reader.py | ✅ | ✅ | ✅ | Foundation |
| 2 | half_unit.py | ✅ | ✅ | ✅ | MRU extraction |
| 3 | analysis_rotor.py | ✅ | ✅ | ✅ | Pole detection |
| 4 | analysis_stator.py, analysis_airgap.py | ✅ | ✅ | ✅ | Slot detection, split |
| 5-0 | analysis_base.py, topology_base.py | ✅ | ✅ | - | Future OOP |
| 5-1 | topology.py | ✅ | ✅ | ✅ | Topology classification |
| 5-2 | topology_stator.py, topology_rotor.py | ✅ | ✅ | ✅ | Region classification |
| 5-3 | region_closing.py, face_detection.py | ✅ | ✅ | ✅ | Face detection |
| 5-3 | gui_region.py, plotting.py | ✅ | ✅ | ✅ | Visualization |
| 5-4 | export.py, symmetry.py, pyleecan_bridge.py | ✅ | ✅ | ✅ | Integration |
| 5-4 | pipeline.py, cli.py | ✅ | ✅ | ✅ | Orchestration |

**Overall: ~95% Complete** (Documentation finished, UML diagrams added)

---

## 🎓 Learning Path

1. **Quick Overview** → Read `pyMotorGeo_CompletionStatus.puml` (module map)
2. **Architecture** → View `pyMotorGeo_Architecture.puml` (class diagram)
3. **Workflow** → Study `pyMotorGeo_Workflow.puml` (execution sequence)
4. **Data** → Explore `pyMotorGeo_DataTransform.puml` (data structures)
5. **Classification** → Review `pyMotorGeo_RotorTopologies.puml` (rotor logic)
6. **Implementation** → Dive into individual module docstrings

---

## 📝 References

- **Rotor Topologies**: SPM (Surface PM), IPM (Interior PM), SynRM (Synchronous Reluctance), PMa-SynRM (Hybrid)
- **Motor Geometry**: Half-pole, quarter-pole, MRU (Minimum Repeating Unit), circular array pattern
- **Stator Regions**: Yoke, Tooth, Slot, Slot Opening, Conductor, Wedge
- **Face Detection**: Shapely `polygonize()`, planar graph traversal, interior point via grid crossing
- **FEA Integration**: Pyleecan (electromagnetics), ANSYS Maxwell (Maxwell FEA)

---

## 📅 Future Work

- **v1.6** (Post-Release): Implement base class refactoring (Option A)
- **v1.7** (Optional): Winding definition and coil topology
- **v1.8** (Optional): Thermal parameters extraction from CAD

---

**Last Updated**: 2026-03-31  
**Documentation Version**: v1.5.1  
**Created by**: Automated Documentation System
