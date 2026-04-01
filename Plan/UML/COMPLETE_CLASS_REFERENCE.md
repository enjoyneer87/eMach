# Pyleecan & eMach - Complete Class Reference

## Pyleecan: All 271 Classes (Alphabetical Listing)

### Categories & Classes

#### **Geometry & Primitives** (20 classes)
```
Arc                 - Base arc class
Arc1                - Arc by start/end points
Arc2                - Arc by center + start + end
Arc3                - Arc by start + end + angle
Circle              - Circle geometry
Line                - Line segment
Segment             - Generic segment
Trapeze             - Trapezoidal region
Surface             - Closed 2D surface
SurfLine            - Surface from line ensemble
SurfRing            - Ring/annular surface
PolarArc            - Polar coordinate arc
Section             - Cross-section
Bore                - Rotor surface (3 types below)
BoreFlower          - Flower-shaped bore (IPM)
BoreLSRPM           - Line-start reluctance bore
BoreSinePole        - Sinusoidal pole face
BoreUD              - User-defined bore
Point               - (implicit - used in curves)
```

#### **Slot Classes - Standard (50+ types)** 

**Circular Slots**
```
SlotCirc            - Circular slot (motor type)
```

**Trapzoidal Slots - W-Series** (Standard IEC/ISO induction motor)
```
SlotW10 - SlotW30   - Standard W-series slots (20 types)
SlotW60, SlotW61    - Wide-mouth slots
SlotW62, SlotW63    - Additional wide-mouth variants
```

**Inner Magnet Slots - M-Series** (Rotor slots for magnets)
```
SlotM10 - SlotM19   - Standard M-series (10 types)
SlotM18_2           - Double-layer magnet slot
SlotM50 - SlotM63   - High-performance variants (14 types)
SlotMLSRPM          - Line-start PMSM variant
```

**Specialized Slots**
```
Slot19              - 19-tooth specialized
SlotDC              - DC machine slot
SlotUD              - User-defined slot
SlotUD2             - Alternative user-defined
```

#### **Lamination Classes** (20+ types)

**Base**
```
Lamination          - Abstract base (iron stack)
LamH                - High-pole variant
```

**Slotted Laminations (Stator-type)**
```
LamSlot             - Base slotted lamination
LamSlotWind         - Slotted with winding (stator)
LamSlotM            - Slotted rotor with magnets
LamSlotMag          - Slotted magnet rotor
LamSlotMagNS        - Slotted magnet, no symmetry
LamSlotMulti        - Multiple slot types
LamSlotMultiWind    - Multi-slot with windings
```

**Hole Laminations (Rotor-type - magnets in pockets)**
```
LamHole             - Base hole lamination
LamHoleNS           - Hole lamination, no symmetry
```

**Cage Laminations (Squirrel cage rotor)**
```
LamSquirrelCage     - Squirrel cage bar rotor
LamSquirrelCageMag  - Cage with permanent magnets
```

**User-defined**
```
LamUD               - User-defined lamination
```

#### **Machine Classes - Hierarchy**

**Base**
```
Machine             - Abstract base machine
```

**Asynchronous (Induction Motors)**
```
MachineAsync        - Abstract async base
MachineSCIM         - Squirrel Cage Induction Motor
MachineDFIM         - Double-Fed Induction Motor
```

**Synchronous (Permanent Magnet & Reluctance)**
```
MachineSync         - Abstract sync base
MachineIPMSM        - Interior Permanent Magnet Synchronous Motor
MachineSIPMSM       - Surface Interior PMSM
MachineSyRM         - Synchronous Reluctance Motor (no magnets)
MachineLSPM         - Line-Start Permanent Magnet
MachineSRM          - Switched Reluctance Motor
```

**Special Cases**
```
MachineUD           - User-defined machine
MachineWRSM         - Wound Rotor Synchronous Motor
```

#### **Winding & Conductor Classes** (10 types)

**Winding Classes**
```
Winding             - Base winding class
WindingSC           - Squirrel Cage (distributed bar)
WindingUD           - User-defined winding
```

**Conductor Types**
```
Conductor           - Base conductor
CondType11          - Series-wound type 1
CondType12          - Series-wound type 2
CondType13          - Series-wound type 3
CondType21          - Parallel-wound type 1
CondType22          - Parallel-wound type 2
```

**End Windings**
```
EndWinding          - Base end-winding connector
EndWindingCirc      - Circular end-winding path
EndWindingRect      - Rectangular end-winding path
```

#### **Material Classes** (15+ types)

**Material & Properties**
```
Material            - Base material container
MatElectrical       - Electrical properties (σ, ρ)
MatMagnetics        - Magnetic properties (μ, B-H curves)
MatStructural       - Structural properties (E, σ_yield, density)
MatHT               - Heat transfer properties (k, ρ_c)
MatEconomical       - Cost/economic properties
```

**B-H and Magnetic Models**
```
ModelBH             - Base B-H curve model
ModelBH_linear_sat  - Linear + saturation knees
ModelBH_exponential - Exponential saturation
ModelBH_arctangent  - Arc-tangent saturation
ModelBH_Langevin    - Langevin magnetization model
Magnetics           - Magnetic material container
```

#### **Simulation & Input Classes** (25+ types)

**Simulation Framework**
```
Simulation          - Abstract simulation base
Simu1               - Single-case simulation
```

**Input Sources**
```
Input               - Base input
InputCurrent        - Current source/constraint
InputVoltage        - Voltage source
InputFlux           - Flux linkage source
InputForce          - Force/torque source
```

**Variable Loading (Parametric Variation)**
```
VarLoad             - Base variable load
VarLoadCurrent      - Current variation
VarLoadVoltage      - Voltage variation
VarOpti             - Optimization variable
VarParam            - Design parameter sweep
VarParamSweep       - Multi-param sweep
VarSimu             - Simulation parameter variation
```

**Operating Points**
```
OP                  - Single operating point
OPMatrix            - Multi-point operating condition matrix
OPdq                - dq-axis operating point
OPdqf               - dq-axis with frequency
OPslip              - Slip-based operating point
SimpleOP            - Simplified OP (if exists)
```

#### **Output & Results Classes** (30+ types)

**Main Output Container**
```
Output              - Root results container
```

**Result Types**
```
OutGeo              - Geometric calculation results
OutGeoLam           - Lamination geometry results
OutElec             - Electrical results (voltage, current, EMF)
OutMag              - Magnetic field results
OutMagFEMM          - FEMM FEA results
OutMagElmer         - Elmer FEA results
OutLoss             - Loss breakdown results
OutLossModel        - Loss model parameters
OutGeoLam           - Lamination geometry
OutForce            - Force/torque results
ForceMT             - Maxwell tensor forces
ForceTensor         - General force tensor (?)
OutStruct           - Structural analysis results
OutInternal         - Internal computation results
OutPost             - Post-processing results
```

**Solution Data**
```
Solution            - Result solution wrapper
SolutionMat         - MATLAB format solution
SolutionVector      - Vector format solution
SolutionData        - Time-domain solution data
SolutionData        - (may have variants)
XOutput             - Extended output
```

#### **FEA & Mesh Classes** (20+ types)

**Solvers**
```
Magnetics           - Base FEA interface
MagFEMM             - FEMM solver wrapper
MagElmer            - Elmer FEA wrapper
MagElmer (Elmer)    - Alias or subclass
```

**Mesh Components**
```
Mesh                - Base mesh class
MeshMat             - MATLAB format mesh
MeshVTK             - VTK format mesh
MeshSolution        - Solution on mesh
```

**FEA Elements**
```
RefElement          - Reference element base
RefTriangle3        - 3-node triangle
RefTriangle6        - 6-node triangle (2nd order)
RefQuad4            - 4-node quadrilateral
RefQuad9            - 9-node quad (2nd order)
RefLine3            - 3-node line
RefSegmentP1        - P1 segment element
NodeMat             - Node coordinate matrix
ElementMat          - Element connectivity matrix
GaussPoint          - Gaussian quadrature points
FPGNTri             - Finite point Gauss tri (?)
FPGNSeg             - Finite point Gauss segment (?)
```

#### **Loss & Efficiency Classes** (15 types)

**Loss Models**
```
Loss                - Base loss model
LossModel           - Abstract loss model base
LossModelJoule      - Joule/copper loss (I²R)
LossModelSteinmetz  - Steinmetz iron loss (hysteresis + eddy)
LossModelBertotti   - Bertotti iron loss model (hysteresis + eddy variants)
LossModelWindage    - Friction/windage loss
LossModelWindagePyrhonen - Pyrhonen windage model
LossModelMagnet     - Permanent magnet eddy loss
LossModelProximity  - Proximity effect loss
LossModelWinding    - Winding-specific loss
LossFEA             - FEA-computed loss results
```

**Power & Efficiency**
```
ElecLUTdq           - dq-axis lookup table for electrical
```

#### **Electrical Equivalent Circuit** (5 types)

```
EEC                 - Electrical Equivalent Circuit base
EEC_SCIM            - SCIM equivalent circuit
EEC_LSRPM           - Line-start PMSM circuit
EEC_PMSM            - PMSM equivalent circuit
Electrical          - Electrical properties container
```

#### **Drive & Frame** (5 types)

```
Drive               - Base drive/inverter class
DriveWave           - Drive waveform/modulation
Frame               - Mechanical frame
FrameBar            - Frame bar (structural element)
Shaft               - Rotating shaft
```

#### **Mechanical & Cooling** (5 types)

```
Ventilation*        (may be present)
VentilationCirc     - Circular ventilation ducts
VentilationPolar    - Polar ventilation
VentilationTrap     - Trapezoidal ventilation
Skew                - Rotor skew angle
Notch               - Stator notch/slot opening
NotchEvenDist       - Even-distributed notches
```

#### **Data & Import/Export** (20+ types)

**Data Containers**
```
DataKeeper          - Result storage/keeper
LUT                 - 1D lookup table
LUTdq               - dq-axis lookup table
LUTslip             - Slip-based lookup table
```

**Import Classes**
```
Import              - Base importer
ImportData          - Generic data import
ImportMatrix        - Load matrix files
ImportMatrixVal     - Matrix with value pairs
ImportMatrixXls     - Excel spreadsheet import
ImportMatlab        - MATLAB file (.mat) import
ImportMeshMat       - Mesh in MATLAB format
ImportMeshUnv       - Mesh in UNV format (IDEAS)
ImportVectorField   - Vector field data
DXFImport           - DXF CAD import
```

**Generator Imports**
```
ImportGenMatrixSin  - Generated sine matrix
ImportGenPWM        - Generated PWM signal
ImportGenVectLin    - Generated linear vector
ImportGenVectSin    - Generated sine vector
ImportGenToothSaw   - Generated sawtooth/tooth pattern
```

**Conversion & Export**
```
Convert             - Base converter
ConvertMC           - MotorCAD converter
Rule                - Transformation rule base
RuleSimple          - Simple rule
RuleEquation        - Equation-based rule
RuleComplex         - Complex rule
```

#### **Optimization & Design** (20+ types)

**Problem Definition**
```
OptiProblem         - Optimization problem definition
OptiObjective       - Objective function
OptiConstraint      - Constraint definition
OptiDesignVar       - Base design variable
OptiDesignVarInterval - Range/interval variable (min-max)
OptiDesignVarSet    - Discrete set variable
```

**Algorithms**
```
OptiSolver          - Base solver interface
OptiGenAlg          - Genetic algorithm
OptiGenAlgNsga2Deap - NSGA-II with DEAP library
OptiBayesAlg        - Bayesian optimization
OptiBayesAlgSmoot   - Smooth kernel Bayesian
```

#### **Analysis & Post-Processing** (15 types)

```
Mode                - Modal analysis
Post                - Post-processing base
PostMethod          - Post-processing method
PostFunction        - Post-processing function
PostPlot            - Plot generation
PostLUT             - LUT post-processing
ScalarProduct       - Scalar/dot product
ScalarProductL2     - L2 norm product
```

#### **Utility & Base Classes** (10+ types)

```
Unit                - Unit conversion
DataKeeper          - (listed above under Data)
OP (subset)         - (listed above under OP)
Electrical          - (listed above)
ParamExplorer       - Parameter exploration base
ParamExplorerInterval - Interval parameter sweep
ParamExplorerSet    - Discrete set parameter sweep
```

#### **Infrastructure & Helper** (5+ types)

```
_ClassInfo          - Class metadata
_FEMMHandler        - FEMM interface helper
_frozen             - Frozen class base (all inherit from this)
_check              - Type checking utilities
__init__            - Package initialization
import_all          - Mass import utility
```

---

## eMach pyMotorGeo: Complete Module List

### Core Analysis Modules (32 Python files)

#### **1. Core Data Structures**
```
core.py              - EntityInfo (dataclass for DXF geometry abstraction)
                      - Geometric mathematical utilities
                      - Spatial transform functions
```

#### **2. DXF Reading & Parsing**
```
reader.py            - read_entity_list()
                      - DXF file I/O via ezdxf wrapper
                      - Entity normalization to EntityInfo
```

#### **3. Analysis Pipeline Base**
```
analysis/__init__.py  - Module hub re-exporting submodules
analysis_base.py      - ComponentCounter abstract class
                       - Base methods for counting components
```

#### **4. Air Gap & Motor Geometry Analysis**
```
analysis_airgap.py    - find_origin_candidates() [motor center detection]
                       - find_concentric_radii() [radial bands]
                       - find_closed_regions() [topology detection]
                       - analyze_closed_regions_for_motor_type()
                       - classify_inner_outer_rotor()
                       - find_airgap_radius()
                       - find_airgap_by_arc_span()
                       - split_by_layer() [by DXF layer]
                       - split_by_radius() [by radial position]
                       - split_stator_rotor() [component separation]
```

#### **5. Rotor Pole Analysis**
```
analysis_rotor.py     - RotorCounter class (OOP version)
                       - count_poles() [from ARC distribution]
                       - count_poles_by_regions() [from closed regions]
                       - estimate_poles_robust() [multi-method]
                       - FFT-based harmonic analysis (implicit)
```

#### **6. Stator Slot Analysis**
```
analysis_stator.py    - StatorCounter class (OOP)
                       - count_slots() [from conductor regions]
                       - count_slots_by_regions()
                       - estimate_slots_robust()
                       - detect_slot_conductors() [identify copper]
```

#### **7. Topology Classification**
```
topology.py           - PoleRegionInfo (dataclass)
                       - detect_circular_array_pattern() [extreme level polar detail]
                       - extract_single_pole_entities()
                       - extract_single_slot_entities()
                       - classify_pole_topology() [SPM vs IPM vs SynRM]
                       - analyze_rotor_topology()
                       - reconstruct_from_half()
```

#### **8. Rotor Topology Types**
```
topology_rotor.py     - RotorTopologyClassifier class
                       - Rotor type classification:
                         * SPM (Surface PM)
                         * IPM (Interior PM)
                         * SynRM (Synchronous Reluctance)
                         * PMa-SynRM (PM-assisted SynRM)
                       - Magnet & flux barrier detection
```

#### **9. Stator Topology Types**
```
topology_stator.py    - StatorTopologyClassifier class
                       - Slot geometry classification
                       - Winding distribution analysis
                       - Conductor placement detection
```

#### **10. Base Topology**
```
topology_base.py      - TopologyClassifier abstract base
                       - Generic topology classification interface
```

#### **11. Half-Unit Extraction**
```
half_unit.py          - extract_half_pole_entities()
                       - extract_half_slot_entities()
                       - reconstruct_from_half() [full from half]
                       - 180°/120° symmetry exploitation
```

#### **12. Region & Face Detection**
```
regions.py            - Region class (face representation)
                       - Face properties & hierarchy
                       - region_type classification
                       - parent_pole, parent_slot relationships
```

#### **13. Topological Face Closure**
```
region_closing.py     - Face closure algorithm
                       - Boundary segment stitching
                       - Topological face construction
                       - Inside/outside classification (winding number)
                       - Handles partial/unclosed DXF geometries
```

#### **14. Closed Region Detection**
```
face_detection.py     - find_closed_regions()
                       - Closed LWPOLYLINE detection
                       - Topological integrity checking
                       - Region typing & labeling
```

#### **15. Symmetry & Periodicity**
```
symmetry.py           - detect_polar_symmetry()
                       - detect_mirror_symmetry()
                       - apply_symmetry_reconstruction()
                       - symmetry_factor() [FEA reduction]
```

#### **16. Visualization**
```
plotting.py           - Motor geometry plots (matplotlib)
                       - Entity layer visualization
                       - Region color-coding
                       - Pole/slot highlighting
```

#### **17. GUI & Interactive Selection**
```
gui_region.py         - Interactive region selection
                       - GUI for region classification correction
                       - User-guided topology confirmation
```

#### **18. High-Level Analysis Pipeline**
```
pipeline.py           - analyze_dxf_v2() [recommended v1.5.1+]
                       - analyze_motor_dxf() [legacy]
                       - quick_analyze() [lightweight]
                       - Full orchestration of analysis steps
                       - Output result dictionary
```

#### **19. DXF Editing & Modification**
```
editor.py             - DXFDrawing class (ezdxf wrapper)
                       - add_entity(), remove_entity()
                       - modify_layer(), modify_properties()
                       - Export to new DXF
```

#### **20. Result Export**
```
export.py             - Export formats:
                         * DXF (update CAD)
                         * JSON (web/portable)
                         * CSV (spreadsheet)
                         * Pickle (Python serialization)
                       - Region summary export
                       - Geometry property export
```

#### **21. Integration: Pyleecan Bridge**
```
pyleecan_bridge.py    - create_machine_from_rotor_entities()
                       - create_lamination_from_geometry()
                       - create_slot_from_geometry() [SlotW11, SlotM10, etc.]
                       - create_hole_from_magnet_region()
                       - create_winding_from_analysis()
                       - Exports to: MachineSIPMSM, MachineIPMSM, MachineSyRM
```

#### **22. Integration: MotorCAD Bridge**
```
motorcad_bridge.py    - export_to_motorcad_geometry()
                       - import_motorcad_results()
                       - create_motorcad_project()
                       - MATLAB COM interface to MotorCAD
```

#### **23. Command-Line Interface**
```
cli.py                - Command-line argument parsing
                       - Batch processing support
                       - Direct DXF analysis without Python code
```

#### **24-32. Utility & Support**
```
fix_imports.py        - Module import path resolution
test_refactoring.py   - Unit tests for refactored modules
__init__.py           - Package initialization & API exports
[helper modules]      - Math utilities, constants, etc.
```

---

## eMach MATLAB Legacy Classes (in Class/ directory)

### MATLAB Class-Based Components
```
Class_Motor.m               - Motor class definition
Machinedata.m               - Machine data container
machinedata.m               - (lowercase variant)
BasisModel.m                - Basis function/model
ResultData.m                - Generic result storage
ResultMotorcadData.m        - MotorCAD result wrapper
ResultMotorcadEmagData.m    - MotorCAD EM results
FEASimul.m                  - FEA simulation wrapper (generic)
FEASimulJmag.m              - JMAG-specific FEA wrapper
DataMap.m                   - Data mapping utility
Calibration.m               - Calibration model
CalibrationMotorCAD.m       - MotorCAD calibration
Unit.m                      - Unit definitions
```

### eMach Data & Result Classes (@ prefix = package directory)
```
@DataDqMap/                 - dq-axis data mapping package
  - Contains: DataDqMap class, methods
  
@DataLUT/                   - Lookup table package
  - Contains: DataLUT class, table operations
  
@DataPkBetaMap/             - Peak/beta angle mapping package
  
@measureddata/              - Measured test data package
  
@MotorcadData/              - MotorCAD data wrapper package
  - Interfaces with MotorCAD results
  
@ResultMotorcadLabData/     - Lab test results package
  - Experimental/measured motor data
```

### eMach Function Libraries (MATLAB .m files)
```
fcn_fft_circuit.py          - FFT analysis for circuits
fcn_read_dat.m              - Data file reader
fcn_One_period_sampling.m   - Single-period sampling
file_list_get.m             - File list generation

motorcadGraphAnalysisFFT.m      - FFT harmonics analysis
motorcadResultPhasorDiagram.m   - Phasor diagram generation
ResultMotorcadEmagPhasorDiagram.m - EM phasor results

variableNumInputAndOutput.m  - Variable argument handling
acceptVariableNumInputs.m    - Input validation
BasisModel.m                 - Basis expansion
dq_trans.m                   - dq transformation
ElecUnit.m                   - Electrical units
EddyCoefficientData.m        - Eddy current coefficients
HysCoefficientData.m         - Hysteresis model coefficients
```

---

## Integration & Data Flow Summary

### Pyleecan Complete Data Dependencies
```
Machine
  ├─→ Stator: LamSlot
  │    ├─→ Slot: SlotW11 (or any W/M type)
  │    ├─→ Winding: Winding
  │    └─→ Material: MatElectrical + MatMagnetics + ...
  ├─→ Rotor: LamSlotM OR LamHole
  │    ├─→ Slot: SlotM10, SlotM50, HoleM50 (magnet pockets)
  │    ├─→ Bore: BoreFlower, BoreSinePole, ...
  │    ├─→ Magnet: (implicit in Hole)
  │    └─→ Material: MatMagnetics (rare earth) + ...
  ├─→ Frame: Frame
  │    └─→ Material: MatStructural
  └─→ Shaft: Shaft
       └─→ Material: MatStructural

Simulation
  ├─→ Machine (see above)
  ├─→ Input: InputCurrent, InputVoltage, ...
  ├─→ Variable: VarParam, VarLoad, VarOpti, ...
  ├─→ Output
  │    ├─→ OutGeo: Geometric properties
  │    ├─→ OutMag: B, H, flux (from MagFEMM, MagElmer)
  │    ├─→ OutElec: Voltage, current, EMF
  │    ├─→ OutLoss: Joule, iron, windage, magnet losses
  │    ├─→ OutForce: Torque, cogging
  │    └─→ OutStruct: Stress, deformation (optional)
  └─→ (implicit) Material: Lookup by name
```

### eMach Complete Data Dependencies
```
DXF File
  ↓
reader.py: read_entity_list() → EntityInfo[]
  ↓
  ├─→ analysis_airgap.py: split_stator_rotor()
  │    ├─→ RotorCounter.estimate_poles_robust()
  │    └─→ StatorCounter.estimate_slots_robust()
  ├─→ topology_rotor.py: RotorTopologyClassifier.classify()
  │    └─→ PoleRegionInfo[] + magnet/barrier lists
  └─→ topology_stator.py: StatorTopologyClassifier.classify()
       └─→ Slot geometry + conductor locations

region_closing.py: Topological face closure
  → Region[] (classified by type)

pyleecan_bridge.py: Convert to Pyleecan
  ├─→ create_lamination_from_geometry()
  ├─→ create_slot_from_geometry() → SlotW11, SlotM10, ...
  ├─→ create_hole_from_magnet_region() → HoleM50, HoleM51, ...
  └─→ create_machine_from_rotor_entities() → MachineIPMSM, MachineSyRM, ...

motorcad_bridge.py: Export to MotorCAD
  → MotorCAD geometry project
  → Run analysis → Results back

OR

export.py: Export results
  ├─→ DXF (updated geometry)
  ├─→ JSON (web-portable)
  ├─→ CSV (tables)
  └─→ Pickle (Python serialization)
```

---

**END OF COMPLETE CLASS REFERENCE**

*Use this document alongside CODEBASE_ARCHITECTURE_ANALYSIS.md for comprehensive PlantUML diagram generation.*
