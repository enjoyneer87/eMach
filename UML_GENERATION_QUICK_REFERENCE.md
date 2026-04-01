# UML Diagram Generation Guide - Quick Reference

## For SyR-e Motor Design Framework

### Core Data Model (Recommend as Classes)

```
┌─────────────────────────────────────────┐
│ MotorDesign                             │
├─────────────────────────────────────────┤
│ geo: GeometricParameters                │
│ mat: MaterialProperties                 │
│ win: WindingScheme                      │
│ path: MotorPath                         │
├─────────────────────────────────────────┤
│ drawGeometry()                          │
│ exportToFEMM()                          │
│ optimizeDesign()                        │
└─────────────────────────────────────────┘
```

### Geometry Parameters (geo struct → class)

```
┌─────────────────────────────────────────┐
│ GeometricParameters                     │
├─────────────────────────────────────────┤
│ p: int              [pole pairs]        │
│ q: int              [slots/pole/phase]  │
│ l: float            [stack length]      │
│ Rast: float         [stator outer]      │
│ Rrot: float         [rotor outer]       │
│ rotorType: str      [SPM/Spoke/SyR]     │
│ w: int              [winding branches]  │
│ periodicity: int                        │
│ th0: float          [d-axis offset]     │
│ ...12 more fields                       │
├─────────────────────────────────────────┤
│ getAirgap()                             │
│ validateGeometry()                      │
│ scaleTo(targetPower)                    │
└─────────────────────────────────────────┘
```

### Material Properties (mat struct → class)

```
┌─────────────────────────────────────────┐
│ MaterialProperties                      │
├─────────────────────────────────────────┤
│ [iron]                                  │
│   density, cost, bsat, muHc, ...        │
│ [copper]                                │
│   resistivity, density, cost, temp_coef │
│ [pm]  (permanent magnet)                │
│   Hc, Brem, density, cost, temp_coef    │
│ [aluminum]                              │
│   density, resistivity, cost            │
├─────────────────────────────────────────┤
│ getProperty(material, prop)             │
│ getTempCorrection(T)                    │
│ calcCost()                              │
└─────────────────────────────────────────┘
```

### Winding Scheme (win struct → class)

```
┌─────────────────────────────────────────┐
│ WindingScheme                           │
├─────────────────────────────────────────┤
│ type: str           [sinusoidal/...]    │
│ Qpc: int            [slots/phase/coil]  │
│ n3phase: int        [3-phase windings]  │
│ distribute: array   [slot distribution]│
│ ...                                     │
├─────────────────────────────────────────┤
│ getWindingFactor()                      │
│ simulateHarmonics()                     │
│ buildMatrix()                           │
└─────────────────────────────────────────┘
```

### FEA Export Architecture (Plug-in Pattern)

```
                    ┌──────────────────┐
                    │ FEAExporter      │
                    │ (abstract)       │
                    ├──────────────────┤
                    │ draw()           │
                    │ assignMaterials()│
                    │ saveSolver()     │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────────┐  ┌──────▼──────┐    ┌──────▼──────┐
    │ FEMMExporter │  │ MaxwellExpt │    │ COMSOLExptr │
    ├──────────────┤  ├─────────────┤    ├─────────────┤
    │ .fem output  │  │ .py script  │    │ .m script   │
    │ FEMM-specific│  │ CAD geometry│    │ FE + struct │
    └──────────────┘  └─────────────┘    └─────────────┘
    
    [+ JMAGExporter, MagNetExporter, MotorCADExporter, DXFExporter]
```

### Design & Optimization Workflow

```
START: Motor Parameters (geo, mat, win)
   │
   ├─→ draw_motor_in_FEMM() ──→ .fem file  ──→ [FEMM solver]
   │                                              │
   ├─→ FEMMfitness(solution) ──→ [Evaluate KPIs]
   │       (flux, torque, loss, efficiency)      │
   │                                              ↓
   └─→ MODE optimization ──────────→ [Pareto Front]
       (maximize efficiency, torque,
        minimize cost, volume, noise)
```

---

## For pyMotorGeo - DXF Analysis Framework

### Class Hierarchy

```
┌─────────────────────────────────┐
│ EntityInfo (dataclass)          │  ← Core DXF entity
├─────────────────────────────────┤
│ etype: str (LINE/ARC/CIRCLE)    │
│ points: List[(x,y)]             │
│ radius: Optional[float]         │
│ center: Optional[(x,y)]         │
│ is_closed: bool                 │
├─────────────────────────────────┤
│ r_min, r_max: float [properties]│
│ angle_deg: float [property]     │
│ get_area()                      │
│ rotate(), mirror(), transform() │
└────────────┬────────────────────┘
             │
             ├─→ Reader
             │   └─→ read_entity_list(dxf_path)
             │
             ├─→ Analysis
             │   ├─→ find_origin_candidates()
             │   ├─→ find_concentric_radii()
             │   ├─→ find_airgap_radius()
             │   ├─→ count_poles(), count_slots()
             │   ├─→ find_closed_regions()
             │   └─→ split_stator_rotor()
             │
             ├─→ Topology
             │   ├─→ RotorTopologyClassifier
             │   │   ├─→ classify_rotor_entities()
             │   │   └─→ detect_poles() [SPM/IPM/SynRM]
             │   │
             │   └─→ StatorTopologyClassifier
             │       ├─→ classify_stator_entities()
             │       └─→ detect_slot_conductors()
             │
             └─→ Export
                 ├─→ export_regions_to_dxf()
                 ├─→ motorcad_bridge()
                 └─→ symmetry.apply()
```

### Motor Analysis Result Data Model

```
┌──────────────────────────────────────────────┐
│ MotorAnalysisResult (Dict)                   │
├──────────────────────────────────────────────┤
│ geometry: {                                  │
│   ro, ri, l               [motor dimensions] │
│   Rast, Rrot             [radii]             │
│ }                                            │
│                                              │
│ rotor: {                                     │
│   topology: 'SPM'|'IPM'|'SynRM'             │
│   n_poles: int,                             │
│   magnet_area: float,                       │
│   regions_summary: {...}                    │
│ }                                            │
│                                              │
│ stator: {                                    │
│   n_slots: int,                             │
│   conductor_area: float,                    │
│   regions_summary: {...}                    │
│ }                                            │
│                                              │
│ airgap: {                                    │
│   radius: float,                            │
│   estimate_method: str                      │
│ }                                            │
│                                              │
│ faces: [                  [Detected geometry]│
│   { region_name, area, centroid, ... }      │
│ ]                                            │
│                                              │
│ face_summary: {           [Statistics]      │
│   'magnet': count,                          │
│   'barrier': count,                         │
│   'conductor': count,                       │
│   ...                                       │
│ }                                            │
│                                              │
│ errors: []                [Warnings/issues]  │
└──────────────────────────────────────────────┘
```

### Analysis Pipeline (Recommended: analyze_dxf_v2)

```
    [DXF File]
        │
        ├─→ reader.read_entity_list()
        │   └─→ EntityInfo list
        │
        ├─→ analysis.find_origin_candidates()
        │   └─→ Motor axis origin
        │
        ├─→ analysis.find_concentric_radii()
        │   └─→ Radii distribution
        │
        ├─→ analysis.split_stator_rotor()
        │   ├─→ rotor_entities
        │   └─→ stator_entities
        │
        ├─→ analysis.count_poles() + count_slots()
        │   ├─→ n_poles
        │   └─→ n_slots
        │
        ├─→ region_closing.find_closed_regions()
        │   └─→ Closed region faces
        │
        ├─→ RotorTopologyClassifier.classify()
        │   └─→ SPM/IPM/SynRM detection
        │
        ├─→ StatorTopologyClassifier.classify()
        │   └─→ Conductor/insulation/tooth classification
        │
        └─→ [MotorAnalysisResult]
            │
            ├─→ export_regions_to_dxf()
            │   └─→ [Colored DXF with regions]
            │
            └─→ motorcad_bridge()
                └─→ [Motor-CAD formatted DXF]
```

### Region Type Taxonomy

**Rotor Regions:**
```
├─ MAGNET              [Permanent magnet areas]
├─ MAGNET_BASE
├─ BARRIER             [Flux barriers (SynRM)]
├─ FLUX_BARRIER
├─ BRIDGE              [Mechanical rib]
├─ PM_SLEEVE_ASSIST    [Assist magnet in sleeve]
├─ SPOKE_SHAFT         [Shaft/spoke interface]
├─ IRON_CORE           [Lamination iron]
└─ SLOT                [Rotor slot]
```

**Stator Regions:**
```
├─ CONDUCTOR           [Copper winding]
├─ SLOT_INSULATION     [Slot wedge/liner]
├─ TOOTH               [Stator tooth]
├─ TOOTH_TIP           [Tooth tip region]
├─ YOKE                [Back-iron]
├─ YOKE_INSULATION     [Insulation coating]
├─ WINDING_HEADER_      [Overhang space]
│  SPACE
└─ EPOXY               [Potting compound]
```

---

## Typical PlantUML Diagrams to Generate

### For SyR-e:

1. **Data Flow Diagram**
   ```
   (geo, mat, win) → draw_motor_in_FEMM() → .fem → FEMMfitness() → (flux, loss, ...)
   ```

2. **Export Plug-in Architecture**
   ```
   FEAExporter (abstract)
   ├─ FEMMExporter
   ├─ MaxwellExporter
   ├─ COMSOLExporter
   ├─ JMAGExporter
   └─ MotorCADExporter
   ```

3. **Optimization Loop**
   ```
   geo/mat/win → evaluate() → fitness() → MODE → [Pareto set]
   ```

### For pyMotorGeo:

1. **Analysis Pipeline**
   ```
   DXF → EntityInfo[] → [Origin/Radii/Split] → [Poles/Slots] → [Topology Classify] → Result
   ```

2. **Class Inheritance**
   ```
   AnalysisBase
   ├─ RotorCounter
   ├─ StatorCounter
   └─ AnalysisAirgap
   
   TopologyClassifier
   ├─ RotorTopologyClassifier
   └─ StatorTopologyClassifier
   ```

3. **Data Model**
   ```
   EntityInfo → MotorAnalysisResult → [Rotor/Stator/Airgap/Faces]
   ```

---

## Tools for Automated UML Generation

### For SyR-e (MATLAB):
- **Enterprise Architect** - Reads MATLAB source
- **PlantUML (manual)** - Hand-write from code inspection
- **Draw.io** - Manual diagramming with library shapes
- **Pylint/pyreverse** - If MATLAB → Python conversion done first

### For pyMotorGeo (Python):
- **`py2puml`**
  ```bash
  py2puml pyMotorGeo output.puml
  ```
  
- **`pyreverse`** (Pylint)
  ```bash
  pyreverse -o puml pyMotorGeo/
  ```
  
- **`pydot` + AST**
  ```python
  import pydot
  # Generate from AST inspection
  ```

- **Manual PlantUML** (recommended for clarity)
  ```plantuml
  @startuml
  class EntityInfo {
    etype: str
    points: List[(float, float)]
    center: Optional[Tuple[float, float]]
    get_area()
  }
  
  class RotorCounter {
    classify_rotor_entities()
    detect_poles()
  }
  
  EntityInfo --> RotorCounter
  @enduml
  ```

---

## Information Density by Diagram Level

### Level 1: High-Level Architecture
- Boxes: Main components (Reader, Analyzer, Classifier, Exporter)
- Arrows: Data flow
- Good for: Executive overview, integration understanding

### Level 2: Class Structure
- Boxes: Classes with key attributes & methods
- Inheritance: ← arrows
- Composition: → arrows
- Good for: Developers understanding relationships

### Level 3: Detailed Design
- All attributes, all methods (private/public)
- Sequence diagrams for complex workflows
- State machines for topology detection
- Good for: Deep code study, extension points

---

## Session Recommendations

1. **Start with pyMotorGeo** - Has clear OOP structure, smaller scope
   - Use `py2puml` to auto-generate base diagram
   - Refine for clarity (remove private methods if needed)

2. **Then document SyR-e** as procedural with modular groups
   - Group functions by purpose (geometry, FEA, export, optimize)
   - Highlight data structures (geo, mat, win, matrix)
   - Show export plug-in architecture

3. **Create integration diagram** showing:
   - SyR-e (MATLAB) → DXF export
   - DXF → pyMotorGeo (Python) → regions + Motor-CAD

This approach maximizes reuse and clarity for UML documentation.

