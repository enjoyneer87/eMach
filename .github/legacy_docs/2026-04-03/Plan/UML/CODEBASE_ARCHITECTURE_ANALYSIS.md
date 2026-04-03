# Codebase Architecture Analysis: Pyleecan & eMach

**Generated**: 2026-04-01  
**Scope**: Comprehensive analysis of class hierarchy, dependencies, and data flow  
**Focus**: Geometry pipeline (input → stator/rotor generation → FEA → analysis)

---

## 1. PYLEECAN (d:\gitfolder\pyleecan)

### 1.1 Overview
Pyleecan is a comprehensive open-source software for motor design and multiphysics simulation. It provides:
- **271 Classes** organized in `Classes/` directory
- **14 Method directories** for domain-specific operations
- Modular architecture supporting multiple motor types and simulation approaches

### 1.2 Top-Level Architecture

```
pyleecan/
├── Classes/           # 271 class definitions
├── Methods/           # Implementation organized by domain
├── Functions/         # Utility functions
├── GUI/               # GUI components
├── Tests/             # Unit tests
└── Generator/         # Code generation tools
```

---

## 2. PYLEECAN CLASS HIERARCHY

### 2.1 Core Machine Classes (Base → Derived)

#### **Inheritance Hierarchy**
```
Machine (Abstract Base)
  ├── MachineAsync (Asynchronous - Squirrel Cage/DFIM)
  │    ├── MachineSCIM (Squirrel Cage Induction Motor)
  │    └── MachineDFIM (Double-Fed Induction Motor)
  ├── MachineSync (Synchronous)
  │    ├── MachineIPMSM (Interior Permanent Magnet Synchronous Motor)
  │    ├── MachineSIPMSM (Surface Interior PMSM)
  │    ├── MachineSyRM (Synchronous Reluctance Motor)
  │    ├── MachineLSPM (Line Start Reluctance Motor)
  │    └── MachineSRM (Switched Reluctance Motor)
  └── MachineUD (User-Defined)
```

**Key Machine Properties:**
- `frame`: Frame class (mechanical housing)
- `shaft`: Shaft class (mechanical transmission)
- `stator`: Lamination (stator stack)
- `rotor`: Lamination (rotor stack)
- `name`, `desc`, `type_machine`

---

### 2.2 Lamination & Geometric Components

#### **Lamination Class Hierarchy** (271 files total)
```
Lamination (Abstract Base)
  ├── LamSlot (Lamination with slots for stator)
  │    ├── LamSlotWind (Slotted stator with winding)
  │    ├── LamSlotM (Slotted with magnets - rotor)
  │    ├── LamSlotMag (Slotted magnet rotor)
  │    ├── LamSlotMagNS (Slotted magnet, no symmetry)
  │    ├── LamSlotMulti (Multiple slot types)
  │    ├── LamSlotMultiWind (Multi-slot with windings)
  │    └── LamSlot + M = LamSlotM variants
  ├── LamHole (Lamination with holes for magnets)
  │    ├── LamHole (Base - rotor with holes)
  │    ├── LamHoleNS (No symmetry)
  │    └── LamSlotM variants
  ├── LamSquirrelCage (Squirrel cage rotor)
  │    └── LamSquirrelCageMag (Cage + permanent magnets)
  ├── LamH (Special high-pole rotor)
  └── LamUD (User-Defined)
```

**Key Lamination Properties:**
- `slot`: Slot object (slot type)
- `hole`: Hole object (for embedded magnets)
- `winding`: Winding object (for stator)
- `material`: Material object
- `L_stack`: Stack length
- `Rext`: External radius
- `Rint`: Internal radius

---

### 2.3 Slot Class Hierarchy (50+ Types)

#### **Slot Base**
```
Slot (Abstract Base)
  ├── Rectangular Slots (Simple geometry)
  │    └── SlotCirc (Circular - Motor)
  ├── Trapezoidal Slots (W-series, standard in induction motors)
  │    ├── SlotW10 → SlotW30 (W10-W30 standards)
  │    ├── SlotW60, SlotW61, SlotW62, SlotW63 (Wide-mouth slots)
  │    └── SlotW21-SlotW29 (Induction motor variants)
  ├── Magazine/Inner Slots (M-series, permanent magnet rotors)
  │    ├── SlotM10 → SlotM19 (Inner magnet slots)
  │    ├── SlotM18_2 (Double-magnet variant)
  │    ├── SlotM50-SlotM63 (High-power variants)
  │    └── SlotMLSRPM (Line-start reluctance)
  ├── Interior Magnet Slots (Specialized)
  │    ├── Slot19 (Specialized 19-tooth)
  │    ├── SlotDC (DC machine slot)
  │    └── SlotUD (User-Defined)
  └── Advanced Geometries
       ├── SlotWLSRPM (Line-start motor)
       └── SlotW60-SlotW63 (Open-slot types)
```

**Key Slot Methods:**
- `build_geometry_active()`: Generate active slot area
- `build_geometry_half_tooth()`: Generate tooth/wedge geometry
- `comp_height()`: Calculate height
- `comp_surface()`: Calculate surface area
- `comp_angle_opening()`: Calculate opening angle

---

### 2.4 Shape/Geometry Classes

#### **Curve & Line Primitives**
```
Geometry Classes:
├── Arc (Base arc)
│    ├── Arc1 (Simple arc by start/end points)
│    ├── Arc2 (Arc by center + start + end)
│    └── Arc3 (Arc by start + end + center angle)
├── Line
├── Circle
├── Segment
├── Trapeze (Trapezoidal region)
├── Surface (2D closed surface)
│    ├── SurfLine (Surface from line ensemble)
│    ├── SurfRing (Annular/ring surface)
│    └── other surface types
└── Bore Classes (Rotor bore geometry)
     ├── Bore (Base)
     ├── BoreFlower (Flower-shaped bore)
     ├── BoreLSRPM (Line-start bore)
     ├── BoreSinePole (Sinusoidal pole face)
     └── BoreUD (User-defined)
```

---

### 2.5 Winding & Conductor Classes

#### **Windings**
```
Winding (Abstract Base)
  ├── Winding (Base with connection matrix)
  ├── WindingSC (Squirrel Cage)
  └── WindingUD (User-Defined)
```

**Properties:**
- `is_stator`: Boolean (stator vs rotor winding)
- `Nlayer`: Number of layers
- `Nphase`: Number of phases
- `Npcpp`: Number of parallel paths
- `connection_matrix`: Connectivity pattern

#### **Conductors**
```
CondType11/12/13 (Series wound)
CondType21/22    (Parallel wound)
Conductor        (Base conductor)
EndWinding*      (End connections)
  ├── EndWindingCirc (Circular)
  └── EndWindingRect (Rectangular)
```

---

### 2.6 Material Classes

#### **Material Type Classes**
```
Material (Base - aggregate)
  ├── MatElectrical
  ├── MatMagnetics
  ├── MatStructural
  ├── MatHT (Heat Transfer)
  └── MatEconomical

Magnetic Property Models:
  ├── ModelBH (B-H curves)
  │    ├── ModelBH_linear_sat (Linear + saturation)
  │    ├── ModelBH_arctangent (Arc-tangent saturation)
  │    ├── ModelBH_exponential (Exponential)
  │    └── ModelBH_Langevin (Langevin)
  └── Magnetics (Material magnetics container)
```

---

### 2.7 Simulation & Input Classes

#### **Simulation Framework**
```
Simulation (Abstract Base)
  ├── Simu1 (Single-point simulation)
  └── Other simulation types
```

**Input Classes:**
```
Input (Base)
  ├── InputCurrent (Current source)
  ├── InputVoltage (Voltage source)
  ├── InputFlux (Flux source)
  └── InputForce (Force source)

Variable Loading:
  ├── VarLoad (Base variable)
  │    ├── VarLoadCurrent
  │    └── VarLoadVoltage
  ├── VarOpti (Optimization variable)
  ├── VarParam (Parameter sweep)
  ├── VarSimu (Simulation variable)
  └── VarParamSweep (Parameter sweep)

Operating Point:
  ├── OP (Single operating point)
  ├── OPMatrix (Multi-point condition)
  ├── OPdq (dq-axis operating point)
  ├── OPdqf, OPslip (Variants)
  └── OPdq, OPslip (Various motor conditions)
```

---

### 2.8 Output & Results Classes

#### **Result Container Classes**
```
Output (Base result container)
  ├── OutElec (Electrical results)
  ├── OutMag (Magnetic results)
  │    ├── OutMagFEMM (FEMM solver results)
  │    └── OutMagElmer (Elmer solver results)
  ├── OutGeo (Geometric results)
  │    └── OutGeoLam (Lamination geometry)
  ├── OutLoss (Loss calculation results)
  │    ├── OutLossModel (Loss model results)
  │    ├── OutLossPerWinding
  │    └── Other loss types
  ├── OutForce (Force results)
  ├── OutStruct (Structural results)
  ├── OutInternal (Internal computation)
  └── OutPost (Post-processing results)

Solution & Data:
  ├── Solution (Result wrapper)
  │    ├── SolutionMat (MATLAB format)
  │    └── SolutionVector (Vector format)
  ├── SolutionData (Time-domain solution)
  └── MeshSolution (FEA mesh solution)
```

---

### 2.9 FEA & Mesh Classes

#### **FEA Solvers**
```
Magnetics
  ├── MagFEMM (FEMM solver wrapper)
  ├── MagElmer (Elmer solver wrapper)
  └── Magnetics (Base interface)

Mesh Components:
  ├── Mesh (Base mesh)
  ├── MeshMat (MATLAB format mesh)
  ├── MeshVTK (VTK format mesh)
  ├── RefElement (Reference element for FEA)
  │    ├── RefTriangle3 (3-node triangle)
  │    ├── RefTriangle6 (6-node triangle)
  │    ├── RefQuad4 (4-node quad)
  │    ├── RefQuad9 (9-node quad)
  │    └── others
  ├── NodeMat (Node matrix data)
  ├── ElementMat (Element matrix data)
  └── GaussPoint (Gauss quadrature points)
```

---

### 2.10 Loss & Efficiency Classes

#### **Loss Models**
```
Loss (Base loss model)
  ├── LossModel (Abstract base)
  │    ├── LossModelJoule (Copper/winding loss)
  │    ├── LossModelSteinmetz (Iron core loss)
  │    ├── LossModelWindage (Windage/friction)
  │    │    └── LossModelWindagePyrhonen
  │    ├── LossModelBertotti (Hysteresis + eddy)
  │    ├── LossModelMagnet (Magnet eddy loss)
  │    ├── LossModelProximity (Proximity effect)
  │    └── LossModelWinding (Winding-specific)
  └── LossFEA (FEA-computed losses)
```

---

### 2.11 Electrical Equivalent Circuit Classes

#### **Equivalent Circuit**
```
EEC (Electrical Equivalent Circuit - Base)
  ├── EEC_SCIM (Squirrel Cage Induction Motor)
  ├── EEC_LSRPM (Line-Start Reluctance Motor)
  ├── EEC_PMSM (Permanent Magnet Synchronous Motor)
  └── ElecLUTdq (dq-axis lookup table)

Electrical Properties:
  ├── Electrical (Electrical properties)
  ├── Drive (Inverter/power electronics)
  ├── DriveWave (Waveform modulation)
  └── Frame (Mechanical frame)
```

---

### 2.12 Optimization & Design Classes

#### **Optimization**
```
OptiProblem (Optimization problem definition)
  ├── OptiObjective (Objective function)
  ├── OptiConstraint (Constraint specifications)
  ├── OptiDesignVar (Design variable)
  │    ├── OptiDesignVarInterval (Interval variable)
  │    ├── OptiDesignVarSet (Discrete set)
  │    └── OptiDesignVarArithmetic
  └── OptiSolver (Base solver)

Optimization Algorithms:
  ├── OptiGenAlg (Genetic algorithm)
  │    └── OptiGenAlgNsga2Deap (NSGA-II with DEAP)
  ├── OptiBayesAlg (Bayesian optimization)
  │    └── OptiBayesAlgSmoot (Smooth kernel)
  └── others
```

---

### 2.13 Import/Export Classes

#### **Data Import**
```
Import (Base importer)
  ├── ImportData (Generic data import)
  ├── ImportMatrix (Load matrix files)
  ├── ImportMatrixVal (Matrix with values)
  ├── ImportMatrixXls (Excel import)
  ├── ImportMatlab (MATLAB file import)
  ├── ImportMeshMat (MATLAB mesh import)
  ├── ImportMeshUnv (UNV mesh import)
  ├── ImportVectorField (Vector field data)
  ├── ImportGenPWM (PWM signal generation)
  ├── ImportGenMatrixSin (Sine matrix)
  ├── ImportGenVectLin (Linear vector)
  ├── ImportGenVectSin (Sine vector)
  ├── ImportGenToothSaw (Sawtooth pattern)
  └── DXFImport (DXF CAD import)

Data Exchange:
  ├── Convert (Base converter)
  ├── ConvertMC (MotorCAD converter)
  ├── XOutput (Extended output)
  └── Rule (Data transformation rules)
```

---

### 2.14 Utility & Helper Classes

#### **Data & Structure**
```
DataKeeper (Result storage)
LUT (Lookup table - 1D)
LUTdq (Lookup table - dq axis)
LUTslip (Lookup table - slip)
ScalarProduct (Dot product class)
├── ScalarProductL2 (L2 norm)
Mode (Modal analysis class)
OP (Operating point)
Unit (Unit conversion)
SimInit (Simulation initialization)
```

---

### 2.15 Key Relationships & Hierarchies

#### **Composition Structure**
```
Machine
  ├─ contains: Stator (Lamination)
  │             ├─ contains: Slot (geometry)
  │             ├─ contains: Winding (coil distribution)
  │             └─ contains: Material
  ├─ contains: Rotor (Lamination)
  │             ├─ contains: Slot or Hole (geometry)
  │             ├─ contains: Bore (rotor surface)
  │             ├─ contains: Magnet (permanent magnet)
  │             └─ contains: Material
  ├─ contains: Frame
  ├─ contains: Shaft
  └─ contains: Electrical parameters

Simulation
  ├─ contains: Machine
  ├─ contains: Input (current/voltage/force)
  ├─ contains: Variable (parametric sweep)
  ├─ contains: Output (results container)
  │             ├─ OutGeo (geometry calculations)
  │             ├─ OutMag (magnetic field solution)
  │             ├─ OutElec (electrical calculations)
  │             ├─ OutLoss (loss calculations)
  │             ├─ OutForce (force/torque)
  │             └─ OutStruct (structural)
  └─ contains: Material (as reference)
```

---

## 3. PYLEECAN METHODS ORGANIZATION

### 3.1 Methods Directory Structure (14 main areas)

```
Methods/
├── Converter/          # Data format conversion
├── Elmer/              # Elmer FEA solver interface
├── Geometry/           # Geometric calculation methods
├── GUI_Option/         # GUI-related utilities
├── Import/             # Data import operations
├── Loss/               # Loss calculation methods
├── Machine/            # Machine operation methods
│   ├── Machine/        # Base machine methods
│   ├── MachineAsync/   # Async-specific
│   ├── MachineIPMSM/   # IPMSM-specific
│   ├── MachineSyRM/    # SyRM-specific
│   ├── Lamination/     # Lamination methods
│   ├── Winding/        # Winding methods
│   ├── Slot/           # Slot methods
│   └── [other types]/
├── Material/           # Material property methods
├── Mesh/               # Mesh generation/processing
├── Optimization/       # Optimization algorithms
├── Output/             # Result processing methods
├── Post/               # Post-processing visualization
├── Simulation/         # Simulation execution
└── Slot/               # Slot geometry methods
```

---

### 3.2 Key Methods by Domain

#### **Geometry Methods**
```
Machine::
  - build_geometry()           # Build complete geometry
  - comp_output_geo()          # Compute geometry outputs
  - comp_Rgap_mec()            # Air gap radius
  - comp_angle_rotor_initial() # Initial rotor angle
  - get_material_dict()        # Material properties

Lamination::
  - build_geometry()           # Layer geometry
  - comp_length()              # Stack length
  - comp_masses()              # Mass calculation
  - comp_radius_mec()          # Mechanical radius
  - comp_surfaces()            # Surface areas
  - comp_volumes()             # Volume calculations
  - get_Rbo()                  # Bore radius
  - get_Ryoke()                # Yoke radius

Slot::
  - build_geometry_active()    # Active slot area
  - build_geometry_half_tooth()# Tooth geometry
  - comp_height()              # Slot height
  - comp_height_active()       # Active height
  - comp_height_opening()      # Opening height
  - comp_surface()             # Slot surface
  - comp_angle_opening()       # Opening angle
```

#### **Electromagnetic Methods**
```
Magnetics (FEA Interface)::
  - solve()                    # Run FEA solver
  - build_input_file()         # Create solver input
  - import_result()            # Read solver output

Winding::
  - comp_connection_mat()      # Connection matrix
  - comp_Ntsp()                # Turns/slot/phase
  - comp_Ncspc()               # Conductors/slot/phase
  - comp_winding_factor()      # Winding factor
  - comp_length_endwinding()   # End winding length
  - get_connection_mat()       # Get connections
```

#### **Loss Calculation Methods**
```
Loss Models::
  - comp_loss_Core()           # Iron losses
  - comp_loss_Joule()          # Winding losses
  - comp_loss_Windage()        # Friction/windage
  - comp_loss_Magnet()         # Magnet eddy loss

FEA Loss::
  - comp_power_loss_from_B()   # Loss from field
  - comp_power_loss_from_B_2D()# 2D field loss
```

#### **Simulation Control**
```
Simulation::
  - run()                      # Execute simulation
  - init_logger()              # Log initialization
  - get_var_load()             # Load variables
  - get_OP_array()             # Operating points
```

---

## 4. DATA FLOW IN PYLEECAN

### 4.1 Main Pipeline: Input → Processing → Output

```
┌─────────────────────────────────────────────────────────────────┐
│                   INPUT STAGE                                    │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Design Parameters (Dimensions, Materials, Winding, Slots)
                               ↓
  Machine Object Creation + Lamination + Slot definitions
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              GEOMETRY GENERATION STAGE                           │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  build_geometry() on Machine/Stator/Rotor/Laminations
                               ↓
  Generate 2D Curves (Arc, Line, Circle, Surface)
                               ↓
  Create Slot profiles + Tooth geometry + Bore shape
                               ↓
  Calculate Geometric Properties:
    - Radii (Rbo, Ryoke, Rgap)
    - Areas (slot, tooth, core)
    - Masses, Inertias
    - Periodicity & Symmetries
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              WINDING & ELECTRICAL STAGE                          │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Define Winding object (phase, parallel paths, turns per slot)
                               ↓
  Compute connection matrix + winding factors
                               ↓
  Calculate end-winding length + resistance
                               ↓
  Define Input (Current/Voltage/Force source)
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│           FEA MESH GENERATION & SETUP STAGE                      │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Choose FEA Solver (FEMM or Elmer)
                               ↓
  Generate 2D Mesh from geometry
                               ↓
  Define Material properties (BH-curves, electrical conductivity)
                               ↓
  Set Boundary conditions (Periodic, Neumann, Dirichlet)
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│             FEA SOLVING & ANALYSIS STAGE                         │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Run Magnetics FEA (MagFEMM or MagElmer)
                               ↓
  Compute Magnetic Field (B, H, flux density)
                               ↓
  Calculate Results:
    - Flux linkage, Back-EMF
    - Cogging torque, Electromagnetic torque
    - Magnetic forces
    - Iron losses (Steinmetz, Bertotti)
    - Winding losses (Joule)
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│             LOSS & EFFICIENCY STAGE                              │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Aggregate losses:
    - Core: Hysteresis + Eddy currents
    - Joule: Winding resistance
    - Windage: Friction, ventilation
    - Magnet: Eddy in permanent magnets
                               ↓
  Calculate Efficiency & Power balance
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT & RESULT STAGE                               │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Collect Results in Output object:
    - OutGeo: Geometry summary
    - OutMag: Magnetic field results
    - OutElec: Electrical quantities (voltage, current, EMF)
    - OutLoss: Loss breakdown
    - OutForce: Torque/Force
    - OutStruct: Structural analysis (optional)
                               ↓
  Export/Visualize:
    - Field plots (B, H, flux density)
    - Torque ripple analysis
    - Loss maps
    - Performance curves
    - Save to MATLAB, HDF5, or custom formats
```

---

### 4.2 Variable Loading & Parametric Sweep

```
Simulation Setup
  ├─ Input (Reference source: voltage/current)
  ├─ Variable (Parametric variation)
  │   ├─ VarParam (Sweep machine design parameter)
  │   ├─ VarSimu (Sweep simulation parameter)
  │   ├─ VarLoad (Sweep load/current/voltage)
  │   ├─ VarOpti (Optimization variable)
  │   └─ VarParamSweep (Multi-parameter sweep)
  └─ Operating Point (OP, OPMatrix, OPdq, OPslip, ...)
       ├─ defines load point (speed, torque, current)
       └─ can be array for range of conditions

Execution:
  for each param variation:
    for each operating point:
      → Geometry rebuild (if needed)
      → FEA solve
      → Compute losses
      → Extract outputs
      → Store in Output/SolutionData
```

---

## 5. EMACH (d:\KangDH\Emlab_emach)

### 5.1 Overview
eMach is an active motor design and analysis framework under development. It emphasizes:
- **Geometry-first design** from CAD (DXF) files
- **Modern Python architecture** (not MATLAB-only like older versions)
- **Integration with commercial tools** (MotorCAD, JMAG)
- **Workflow automation** through Jupyter notebooks

**Key Directory Structure:**
```
eMach/
├── Class/
│   ├── pyMotorGeo/           (Main Python geometry analysis library)
│   ├── @DataDqMap/           (Data mapping for dq-axis)
│   ├── @DataLUT/             (Lookup table data)
│   ├── @MotorcadData/        (MotorCAD integration)
│   ├── @ResultMotorcadLabData/ (MotorCAD results)
│   ├── Motorcad/             (MATLAB MotorCAD wrapper)
│   ├── Jmag/                 (MATLAB JMAG wrapper)
│   └── [MATLAB files]        (Legacy MATLAB implementations)
├── mlxperPJT/                (Jupyter notebook workflows)
├── tools/                    (Utility scripts)
├── tests/                    (Unit tests)
├── examples/                 (Usage examples)
└── Plan/                     (Documentation & UML)
```

---

### 5.2 pyMotorGeo Module Structure (Main Python Module)

#### **Core Architecture** (32 Python modules)

```
pyMotorGeo/
├── Core Layer
│   ├── core.py               # Data structures (EntityInfo, geometric primitives)
│   ├── reader.py             # DXF file parsing (ezdxf wrapper)
│   └── fix_imports.py        # Module import resolution
├── Analysis Layer
│   ├── analysis/__init__.py  # Hub re-exporting submodules
│   ├── analysis_airgap.py    # Air gap detection, origin, concentric radii
│   ├── analysis_base.py      # Base component counter class
│   ├── analysis_rotor.py     # Rotor pole count estimation
│   └── analysis_stator.py    # Stator slot count estimation
├── Topology Classification
│   ├── topology.py           # Circular array pattern detection
│   ├── topology_base.py      # Base topology classifier
│   ├── topology_rotor.py     # Rotor topology (SPM, IPM, SynRM, PMa-SynRM)
│   ├── topology_stator.py    # Stator topology classification
│   └── half_unit.py          # Half-pole/half-slot extraction
├── Region & Geometry
│   ├── regions.py            # Region/face definitions
│   ├── region_closing.py     # Topological face closure algorithm
│   ├── face_detection.py     # Closed region detection
│   └── symmetry.py           # Symmetry detection (polar, mirror)
├── Geometric Transform
│   ├── plot.py (aliased from plotting)
│   ├── plotting.py           # Visualization (matplotlib)
│   └── [geometric utilities]
├── Integration & Bridges
│   ├── pyleecan_bridge.py    # Export to Pyleecan Machine objects
│   ├── motorcad_bridge.py    # MotorCAD integration
│   └── [CAD bridging]
├── Pipeline & Workflow
│   ├── pipeline.py           # High-level analysis pipelines
│   │                          # - analyze_dxf_v2() [recommended]
│   │                          # - analyze_motor_dxf() [legacy]
│   │                          # - quick_analyze()
│   ├── editor.py             # DXF editing/export
│   ├── export.py             # Result export formats
│   └── cli.py                # Command-line interface
├── AI & Detection
│   ├── gui_region.py         # Region GUI (interactive selection)
│   └── [ML-based detection]
└── Tests & Development
    └── test_refactoring.py   # Refactoring test suite
```

---

### 5.3 pyMotorGeo Class & Function Organization

#### **Core Data Structures** (core.py)
```
EntityInfo (dataclass)
  - etype: Entity type (LINE, ARC, CIRCLE, LWPOLYLINE)
  - layer: DXF layer name
  - points: List of (x, y) coordinates
  - radius: Arc/circle radius
  - center: Arc/circle center
  - start_angle, end_angle: Arc angles
  - is_closed: Closure status
  - raw: [ezdxf entity object, non-serialized]
  - Properties:
    · coords: Alias for points
    · r_min, r_max: Radial distance from origin
    · angle_deg: Average angle (degrees)
    · get_area(): Shoelace formula for polygon area
```

#### **Analysis Classes** (analysis_*.py)

**ComponentCounter (Base - analysis_base.py)**
```
ComponentCounter (Abstract base for counting/analyzing)
  Methods (override in subclasses):
    - count(): Count entities
    - count_by_regions(): Regional counting
    - estimate_robust(): Cross-validated estimation
```

**RotorCounter (analysis_rotor.py)**
```
RotorCounter(ComponentCounter)
  Methods:
    - count(*): Estimate poles from Arc distribution
    - count_by_regions(): Estimate poles from closed region centroids
    - estimate_robust(): Cross-validate multiple methods
  Functions (module-level):
    - count_poles(entities, origin, tol_r, tol_angle)
    - count_poles_by_regions(entities, origin, airgap_r_inner, tol_angle)
    - estimate_poles_robust(entities, origin, verbose=True)
```

**StatorCounter (analysis_stator.py)**
```
StatorCounter(ComponentCounter)
  Methods:
    - count_slots(): Count slots from conductor regions
    - count_slots_by_regions(): Conductor-based counting
    - estimate_slots_robust(): Cross-validated estimation
  Functions (module-level):
    - count_slots(entities, origin, tol_r)
    - count_slots_by_regions(entities)
    - estimate_slots_robust(entities, origin)
    - detect_slot_conductors(): Identify conductor locations
```

**Air Gap Analysis (analysis_airgap.py)**
```
Functions (not classes):
  - find_origin_candidates(entities) → List candidate motor centers
  - find_concentric_radii(entities, origin) → Radii bands
  - find_closed_regions(entities) → Closed polygon regions
  - analyze_closed_regions_for_motor_type(entities, origin) → Motor type
  - classify_inner_outer_rotor(entities, origin) → Rotor position
  - find_airgap_radius(entities, origin) → Airgap boundaries
  - find_airgap_by_arc_span(entities, origin, n_poles) → Arc-based airgap
  - split_by_layer(entities) → Entities by DXF layer
  - split_by_radius(entities, origin) → Entities by radial bands
  - split_stator_rotor(stator_entities, rotor_entities) → Separate components
```

---

#### **Topology Classification Classes** (topology_*.py)

**RotorTopologyClassifier (topology_rotor.py)**
```
PoleRegionInfo (dataclass)
  - pole_index: Pole number (0, 1, 2, ...)
  - pole_pitch_deg: Pole pitch angle
  - angle_start, angle_end: Pole region bounds
  - entities: All entities in pole
  - magnets: Magnet regions
  - air_barriers: Air barriers (IPM)
  - rotor_core: Iron core regions
  - flux_barriers: Flux barriers (IPM specific)

Main Analysis Functions:
  - detect_circular_array_pattern() → Circular array period/n_poles
  - extract_single_pole_entities() → Extract one-pole geometry
  - extract_single_slot_entities() → Extract one-slot geometry
  - classify_pole_topology() → Determine SPM/IPM/SynRM/PMa-SynRM
  - analyze_rotor_topology() → Comprehensive rotor analysis
  - reconstruct_from_half() → Reconstruct full rotor from half-pole
```

**Topology Types (Enum/String Categories)**
```
Rotor Topologies:
  - 'SPM': Surface Permanent Magnet (magnets on surface)
  - 'SPMSM': Surface Magnet Synchronous Motor
  - 'IPM': Interior Permanent Magnet (buried inside)
  - 'IPMSM': IPMSM (with flux barriers)
  - 'SynRM': Synchronous Reluctance (no magnets, flux barriers)
  - 'PMa-SynRM': PM-assisted SynRM (hybrid)
  - 'Bare': No magnets detected

Stator Topologies:
  - 'Slotted': Gear-like slots for winding
  - 'Smooth': No visible slots
  - 'Hybrid': Mixed slot/pole structure
```

**StatorTopologyClassifier (topology_stator.py)**
```
Analyzes:
  - Slot geometry (rectangular, trapezoidal, etc.)
  - Conductor placement
  - Winding distribution
  - End-winding space
```

---

#### **Region & Face Detection** (regions.py, region_closing.py, face_detection.py)

**Region Classes**
```
Region (Base region info)
  - type: 'magnet', 'conductor', 'air_barrier', 'core', 'yoke', 'shaft'
  - centroid: Center of mass (x, y)
  - area: Polygon area
  - vertices: Bounding polygon points
  - parent_pole, parent_slot: Hierarchical relationship
  - properties: Property map (temperature, material, etc.)

Face Detection Algorithm:
  1. Extract closed LWPOLYLINE/POLYLINE entities
  2. Construct topological face from boundary segments
  3. Identify inside/outside by wind number algorithm
  4. Classify region type from location/layer info
  5. Create Region objects with properties
```

#### **Symmetry & Periodicity** (symmetry.py)

```
Functions:
  - detect_polar_symmetry(entities, origin) → Polar symmetry axes
  - detect_mirror_symmetry(entities, origin) → Mirror planes
  - apply_symmetry_reconstruction() → Reconstruct full geometry
  - symmetry_factor() → Periodicity for FEA reduction
```

---

### 5.4 Integration & Export Modules

#### **Pyleecan Bridge** (pyleecan_bridge.py)

```
Main Functions:
  - create_machine_from_rotor_entities() → MachineSIPMSM/IPMSM/SyRM
  - create_lamination_from_geometry()
  - create_slot_from_geometry()
  - create_hole_from_magnet_region()
  - create_winding_from_analysis()

Conversion Flow:
  pyMotorGeo geometry → Pyleecan class instances
  ├─ Rotor pole/magnet info → Hole objects (HoleM50, HoleM51, etc.)
  ├─ Rotor flux barriers → Flux barrier geometry
  ├─ Stator slot geometry → Slot type (SlotW11, SlotW22, etc.)
  ├─ Winding topology → Winding object (phases, parallel paths, turns)
  └─ Complete structure → Machine (IPMSM/SyRM/SPMSM)

Supported Conversions:
  ├─ SIPMM (Surface IPM) ↔ MachineSIPMSM
  ├─ IPMSM (Interior PM) ↔ MachineIPMSM
  ├─ SyRM (Sync Reluctance) ↔ MachineSyRM
  └─ Wound Motors (future): Stator with coil winding
```

#### **MotorCAD Bridge** (motorcad_bridge.py)

```
Functions:
  - export_to_motorcad_geometry()
  - import_motorcad_results()
  - create_motorcad_project()

Interfaces:
  - MATLAB MotorCAD engine (COM interface)
  - Design optimization loop with MotorCAD FEA
```

#### **Editor & Export** (editor.py, export.py)

```
editor.py:
  - DXFDrawing (wrapper for ezdxf DXFDocument)
  - Methods: add_entity(), remove_entity(), modify_layer()
  - Export to new DXF or visualization

export.py:
  - Export formats: DXF, JSON, CSV, pickle
  - Region export: Face summary, property maps
  - Geometry export: Vertices, topology info
```

---

### 5.5 High-Level Pipeline (pipeline.py)

#### **analyze_dxf_v2()** (Recommended v1.5.1+ API)
```
Input:
  - dxf_path: Motor CAD file
  - origin: Motor center (optional, auto-detected)
  - n_poles, n_slots: Optional hints (auto-estimated if omitted)
  - enable_radius_fallback: Boundary closure fallback
  - verbose: Logging level

Execution Flow:
  1. read_entity_list() → Load all DXF entities
  2. find_origin_candidates() → Detect motor center
  3. split_stator_rotor() → Separate components by radius
  4. RotorCounter.estimate_robust() → Estimate poles
  5. StatorCounter.estimate_robust() → Estimate slots
  6. RotorTopologyClassifier.classify() → Determine rotor type (SPM/IPM/SynRM)
  7. StatorTopologyClassifier.classify() → Determine stator type
  8. extract_single_pole_entities() + region_closing() → One-pole faces
  9. extract_single_slot_entities() → One-slot faces
  10. Create output summary

Output:
  Dict {
    'geometry': {'radii': {...}, 'stack_length': ...},
    'rotor': {
      'n_poles': 4,
      'topology': 'IPMSM',
      'pole_pitch_deg': 90.0,
      'estimated_poles_by_arc': 4,
      'estimated_poles_by_region': 4,
      'confidence': 'high',
      'magnets': [...],
      'flux_barriers': [...],
      'rotor_core': [...]
    },
    'stator': {
      'n_slots': 24,
      'slot_pitch_deg': 15.0,
      'estimated_slots_by_conductor': 24,
      'conductors': [...],
      'tooth_geometry': [...]
    },
    'airgap': {'radius_inner': 45.0, 'radius_outer': 46.5, 'width': 1.5},
    'faces': [Region(...), Region(...), ...],
    'face_summary': {'magnets': 4, 'conductors': 24, ...},
    'dxf_path': 'path/to/motor.dxf',
    'errors': []
  }
```

#### **analyze_motor_dxf()** (Legacy API)

```
Simpler, backward-compatible pipeline for pre-closed geometries.
Skips explicit face closure; assumes all regions already closed in DXF.
```

---

### 5.6 eMach Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT STAGE: DXF CAD                          │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Motor DXF file with:
    - Stator core outline + slots
    - Rotor core + magnet/barrier inserts
    - Air gap region
    - Shaft bore
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│          ANALYSIS STAGE: pyMotorGeo Geometry Parsing             │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  1. READ: Load DXF entities via reader.py (ezdxf wrapper)
                               ↓
  2. ANALYZE TOPOLOGY:
     - find_origin_candidates() → Motor center
     - split_stator_rotor() → Component separation by radius
     - RotorCounter.estimate_robust() → Pole count (ARC/region/FFT)
     - StatorCounter.estimate_robust() → Slot count
                               ↓
  3. CLASSIFY TYPES:
     - RotorTopologyClassifier → SPM/IPM/SynRM/PMa-SynRM
     - StatorTopologyClassifier → Slotted/smooth
                               ↓
  4. EXTRACT GEOMETRY:
     - extract_single_pole_entities() → One-pole geometry + rotation
     - extract_single_slot_entities() → One-slot geometry
     - region_closing.py → Topological face closure
     - detect closed regions → Region/Face objects
                               ↓
  5. SYMMETRY & PERIODICITY:
     - detect_polar_symmetry() → Symmetry axes
     - symmetry_factor() → FEA periodicity
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│      CONVERSION STAGE: Export to Pyleecan or MotorCAD            │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Option A) Pyleecan Bridge:
    - create_machine_from_rotor_entities()
    - create_lamination_from_geometry()
    - create_slot_from_geometry()
    → Produces: Machine (IPMSM, SyRM, SPMSM)
    → Next: Pyleecan FEA pipeline
                               ↓
  Option B) MotorCAD Bridge:
    - export_to_motorcad_geometry()
    - Run MotorCAD FEA/thermal/structural
    - import_motorcad_results()
    → Rich multiphysics results
                               ↓
  Option C) Direct Analysis:
    - Region summary statistics
    - Topology validation
    - Geometric properties
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│          WORKFLOW: Jupyter Notebooks (mlxperPJT)                 │
└─────────────────────────────────────────────────────────────────┘
                               ↓
  Notebooks orchestrate:
    - Load DXF → DXFImport or pyMotorGeo
    - Interactive analysis with visualizations
    - Design parameter sweeps
    - Result post-processing & reporting
```

---

### 5.7 eMach Legacy & Integration Components

#### **MATLAB wrappers** (in Class/ directory)

```
MATLAB Class Definitions:
  - Class_Motor.m             # Motor definition base class
  - Machinedata.m             # Machine data container
  - @MotorcadData/            # MotorCAD result wrapper
  - @ResultMotorcadLabData/   # Lab/test result wrapper
  - @DataDqMap/               # dq-axis mapping (eddy current, etc.)
  - @DataLUT/                 # Lookup table implementation
  - FEASimul.m               # FEA simulation wrapper
  - FEASimulJmag.m           # JMAG-specific wrapper
  - BasisModel.m             # Basis function model
  - ResultData.m              # Generic result data
  - Result***.m               # Specialized result handlers
```

#### **Integration Points**

```
eMach → MotorCAD:
  - MATLAB COM interface to MotorCAD
  - Geometry export from pyMotorGeo
  - Design optimization loop
  - Result import (electromagnetic, thermal, structural)

eMach → JMAG:
  - MATLAB JMAG wrapper via Jmag/ directory
  - FEA mesh generation & solving
  - Post-processing results

eMach → Pyleecan:
  - pyleecan_bridge.py converts geometry to Pyleecan Machine
  - Run Pyleecan FEA/loss/efficiency analysis
  - Combined workflow validation
```

---

## 6. DEPENDENCY & RELATIONSHIP SUMMARY

### 6.1 Pyleecan Core Dependencies

```
Class Dependencies (Composition):
  Machine
    ├─→ Stator : Lamination (with Slot, Winding, Material)
    ├─→ Rotor  : Lamination (with Hole/Magnet, Material)
    ├─→ Frame
    └─→ Shaft

  Simulation
    ├─→ Machine
    ├─→ Input (Current/Voltage/Force/Flux)
    ├─→ Variable (Param sweep: VarParam, VarLoad, VarOpti)
    └─→ Output (OutGeo, OutMag, OutElec, OutLoss, OutForce, OutStruct)

  Lamination
    ├─→ Slot (slotted stator/rotor)
    ├─→ Hole (magnet pockets in rotor)
    ├─→ Bore (rotor surface)
    ├─→ Winding (stator winding)
    └─→ Material

  Slot (50+ types)
    └─→ Arc, Line, Circle (geometric primitives)

  Material
    ├─→ MatElectrical
    ├─→ MatMagnetics (with ModelBH)
    ├─→ MatStructural
    ├─→ MatHT
    └─→ MatEconomical
```

### 6.2 eMach Core Dependencies

```
pyMotorGeo Workflow:
  DXF File
    ↓
  reader.py → EntityInfo[] (core.py dataclass)
    ↓
  analysis_airgap.py → Origin + Radii + Split stator/rotor
    ↓
  analysis_rotor.py (RotorCounter) → n_poles estimate
    analysis_stator.py (StatorCounter) → n_slots estimate
    ↓
  topology_rotor.py (RotorTopologyClassifier) → SPM/IPM/SynRM
    topology_stator.py (StatorTopologyClassifier) → Slot type
    ↓
  half_unit.py → Extract one-pole geometry
    region_closing.py → Topological face closure
    ↓
  regions.py → Region objects with properties
    ↓
  pyleecan_bridge.py → Machine (Pyleecan)
      OR
  motorcad_bridge.py → MotorCAD project
      OR
  export.py → DXF/JSON/CSV export

Integration Bridges:
  pyMotorGeo → Pyleecan: Convert geometric regions to Pyleecan classes
  pyMotorGeo → MotorCAD: Export geometry for commercial FEA
  pyMotorGeo → MATLAB: Export via @DataDqMap, @MotorcadData wrappers
```

---

## 7. KEY ARCHITECTURAL PATTERNS

### 7.1 Pyleecan Patterns

1. **Method Injection Pattern**
   - Class definition in `Classes/*.py`
   - Methods implemented separately in `Methods/Class/method_name.py`
   - Methods dynamically imported and attached to class
   - Allows flexible method organization w/o circular imports

2. **FrozenClass Base**
   - All Pyleecan objects inherit `FrozenClass`
   - Prevents undefined attribute assignment
   - Enforces strict class definition

3. **Lazy Import Pattern**
   - Methods wrapped in try/except ImportError
   - Methods only available if dependencies installed
   - Graceful degradation if optional solvers unavailable

4. **Data Model Serialization**
   - `save()` method: Save to HDF5 or init_dict
   - `load_init_dict()`: Load from file
   - All objects support pickle serialization

5. **Polymorphic Solver Interface**
   - Base `Magnetics` class with multiple implementations
   - `MagFEMM`: FEMM solver wrapper
   - `MagElmer`: Elmer solver wrapper
   - Interchangeable without changing simulation code

### 7.2 eMach Patterns

1. **Dataclass-First Design**
   - `EntityInfo` dataclass for DXF geometry abstraction
   - `Region`, `PoleRegionInfo` for semantic geometry
   - Type-safe, serializable data structures

2. **Strategy Pattern for Counters**
   - `ComponentCounter` abstract base
   - `RotorCounter`, `StatorCounter` implementations
   - Pluggable counting strategies (Arc, Region, FFT)

3. **Bridge Pattern for CAD Integration**
   - `pyleecan_bridge.py`: Geometry → Pyleecan
   - `motorcad_bridge.py`: Geometry → MotorCAD
   - Decoupled from internal representation

4. **Topology Classification as Pipeline**
   - Functional pipeline modules (topology.py, analysis_*.py)
   - Composable analysis stages
   - Stateless operations (functional style)

5. **Face Detection via Topological Closure**
   - region_closing.py: Construct closed faces from boundary segments
   - Wind number algorithm for inside/outside classification
   - Supports partial/unclosed DXF geometries

---

## 8. KEY METRICS

### Pyleecan

| Metric | Value |
|--------|-------|
| Total Classes | 271 |
| Machine Types | 12 (Async, Sync, UD variants) |
| Slot Types | 50+ (W-series, M-series) |
| FEA Solvers | 2 (FEMM, Elmer) |
| Loss Models | 7+ (Joule, Steinmetz, Bertotti, Windage, etc.) |
| Methods Directories | 14 |
| Optimization Algorithms | 3+ (Genetic, Bayesian, etc.) |

### eMach pyMotorGeo

| Metric | Value |
|--------|-------|
| Python Modules | 32+ |
| Core Data Structures | EntityInfo, Region, Face |
| Rotor Topology Types | 6+ (SPM, IPM, SynRM, PMa-SynRM, etc.) |
| Analysis Methods | 20+ (pole count, slot count, origin detection, etc.) |
| Export Targets | Pyleecan, MotorCAD, DXF, JSON, CSV |
| Symmetry Detection | Polar + Mirror |

---

## 9. DATA FLOW DIAGRAMS - QUICK REFERENCE

### UML-Ready Summary for PlantUML

```
PYLEECAN CLASS DIAGRAM (Simplified):

@startuml
abstract class Lamination {
  -material: Material
  -L_stack: float
  -Rext: float
  -Rint: float
  +build_geometry()
  +comp_masses()
}

class LamSlot extends Lamination {
  -slot: Slot
  -winding: Winding
  +build_geometry()
}

class LamSlotM extends Lamination {
  -slot: Slot
  -magnet: Magnet
  +build_geometry()
}

class Slot {
  +build_geometry_active()
  +comp_height()
  +comp_surface()
}

class SlotW11 extends Slot {
  -H0: float
  -H1: float
  -H2: float
  -W0: float
}

class Machine {
  -stator: Lamination
  -rotor: Lamination
  -frame: Frame
  -shaft: Shaft
  +build_geometry()
}

class Simulation {
  -machine: Machine
  -input: Input
  -output: Output
  +run()
}

class Output {
  -outgeo: OutGeo
  -outelec: OutElec
  -outmag: OutMag
  -outloss: OutLoss
  -outforce: OutForce
}

Machine *-- Lamination
Lamination o-- Slot
Lamination o-- Winding
Lamination o-- Material
Simulation *-- Machine
Simulation *-- Output

@enduml

─────────────────────────────────────────────────────

EMACH PYMOTOR GEO CLASS DIAGRAM (Simplified):

@startuml
class EntityInfo {
  -etype: str
  -layer: str
  -points: List[Tuple]
  -radius: float
  -center: Tuple
  +get_area()
}

class Region {
  -type: str (magnet|conductor|barrier|core)
  -centroid: Tuple
  -area: float
  -vertices: List[Tuple]
  -properties: Dict
}

abstract class ComponentCounter {
  +count()
  +count_by_regions()
  +estimate_robust()
}

class RotorCounter extends ComponentCounter {
  +count_poles()
  +estimate_poles_robust()
}

class StatorCounter extends ComponentCounter {
  +count_slots()
  +detect_slot_conductors()
}

class RotorTopologyClassifier {
  +classify()
  -detect_circular_array_pattern()
  -extract_single_pole_entities()
}

class Pipeline {
  +analyze_dxf_v2(dxf_path)
  +analyze_motor_dxf(dxf_path)
  +quick_analyze(dxf_path)
}

class PyleecanBridge {
  +create_machine_from_rotor_entities()
  +create_lamination_from_geometry()
  +create_slot_from_geometry()
}

RotorCounter --> EntityInfo
StatorCounter --> EntityInfo
RotorTopologyClassifier --> EntityInfo
RotorTopologyClassifier --> Region
Pipeline --> RotorCounter
Pipeline --> StatorCounter
Pipeline --> RotorTopologyClassifier
PyleecanBridge --> Region
PyleecanBridge --> EntityInfo

@enduml
```

---

## 10. WORKFLOW COMPARISON: PYLEECAN vs EMACH

| Step | Pyleecan | eMach |
|------|----------|-------|
| **Design Input** | Parametric (dimensions, slots, poles) | CAD/DXF file |
| **Geometry Generation** | Procedural (arc, line primitives) | Parsed from DXF (EntityInfo) |
| **Topology Parsing** | Manual specification (MachineIPMSM) | Automatic (RotorTopologyClassifier) |
| **Slot Definition** | Explicit class (SlotW11, SlotM10, etc.) | Inferred from geometry |
| **Material Properties** | Assigned to laminations | Assigned by region classification |
| **FEA Mesh** | Generated by FEMM/Elmer | Generated by FEMM/Elmer (via bridge) |
| **Simulation** | Python-native Simu1.run() | Via Pyleecan or MotorCAD bridge |
| **Output** | Pyleecan Output object | Geometry summary + region tags |
| **Export** | HDF5, MATLAB, Pickle | DXF, JSON, CSV, via bridges |

---

## 11. INTEGRATION ROADMAP

### Current State
1. **Pyleecan**: Mature, ~15 year project, comprehensive simulation
2. **eMach**: Modern, geometry-first approach, bridges to commercial tools
3. **Integration**: Via `pyleecan_bridge.py` only (partial)

### Recommended Usage

**Option A: Pyleecan-First Design**
```
Parameters → Machine() → build_geometry() → FEA → Output → Visualization
```

**Option B: eMach CAD-First Design**
```
DXF → analyze_dxf_v2() → classify topology → 
  {Option B1: Export to Pyleecan → FEA
   Option B2: Export to MotorCAD → Analysis
   Option B3: Direct geometry analysis}
```

**Option C: Hybrid Workflow**
```
DXF (pyMotorGeo) ↓ → Geometry extraction
                ↓
    Pyleecan (convert via bridge) ↓ → FEA Simulation
                                  ↓
    MotorCAD (via motorcad_bridge) ↓ → Validation
                                   ↓
                          Results Comparison
```

---

## 12. UML GENERATION PRIORITIES

For accurate PlantUML UML diagrams, prioritize:

### **Pyleecan UML**
1. **Machine hierarchy** (base → async/sync → specific types)
2. **Lamination hierarchy** (base → slot/hole → specific types)
3. **Slot hierarchy** (50+ types organized by category)
4. **Winding & Material** (properties & composition)
5. **Simulation & Output** (execution & results)
6. **FEA Solvers** (FEMM, Elmer, abstract interface)

### **eMach UML**
1. **Data Structures** (EntityInfo, Region)
2. **Analysis Pipeline** (Reader → Counter → Classifier)
3. **Topology Classification** (RotorTopologyClassifier, StatorTopologyClassifier)
4. **Bridges** (PyleecanBridge, MotorCADbridge)
5. **High-Level Pipeline** (analyze_dxf_v2 orchestration)

---

**END OF ANALYSIS**

*This document provides sufficient detail to generate accurate, hierarchically-structured PlantUML class and sequence diagrams for both Pyleecan and eMach architectures.*
