# Pyleecan & eMach - Method Signatures & Data Flow Details

## 1. PYLEECAN KEY METHOD SIGNATURES

### 1.1 Machine Hierarchy Methods

```python
# ═══════════════════════════════════════════════════════
# Machine (Base)
# ═══════════════════════════════════════════════════════

class Machine(FrozenClass):
    # Properties
    stator: Lamination
    rotor: Lamination
    frame: Frame = None
    shaft: Shaft = None
    type_machine: int = 1
    name: str
    desc: str
    
    # Key Methods
    def build_geometry(self) -> None:
        """Build complete machine geometry from component definitions.
        
        Returns:
            None (modifies self in-place)
        
        Dependencies:
            - stator.build_geometry()
            - rotor.build_geometry()
        
        Sets:
            - Internal curves, surfaces, volumes
        """
        
    def comp_angle_rotor_initial(self) -> float:
        """Calculate initial rotor angle.
        
        Returns:
            float: Initial rotor angle [rad]
        """
        
    def comp_output_geo(self, output: Output) -> Output:
        """Compute geometric outputs and populate OutGeo.
        
        Parameters:
            output (Output): Result container to populate
            
        Returns:
            Output: Modified output with geometry results
            
        Computes:
            - Radii (Rint, Rext, Rgap, Ryoke, Rbo)
            - Masses (stator, rotor, total)
            - Moments of inertia
            - Surface areas
            - Core volumes
        """
        
    def comp_Rgap_mec(self) -> float:
        """Calculate mechanical air gap radius [m].
        
        Returns:
            float: Mechanical air gap radius
            
        Formula:
            Rgap_mec = (Rotor.Rext + Stator.Rint) / 2
        """
        
    def get_material_dict(self) -> Dict[str, Material]:
        """Get all materials in machine.
        
        Returns:
            Dict: {'stator_core': Material, 'rotor_core': Material, ...}
        """
        
    def check(self) -> None:
        """Validate machine definition (no geometric checks).
        
        Raises:
            ValueError: If machine definition invalid
        """


# ═══════════════════════════════════════════════════════
# MachineAsync (Asynchronous/Induction)
# ═══════════════════════════════════════════════════════

class MachineAsync(Machine):
    
    def is_synchronous(self) -> bool:
        """Check if machine is synchronous.
        
        Returns:
            bool: False (asynchronous machine)
        """


# ═══════════════════════════════════════════════════════
# MachineSync (Synchronous)
# ═══════════════════════════════════════════════════════

class MachineSync(Machine):
    
    def is_synchronous(self) -> bool:
        """Check if machine is synchronous.
        
        Returns:
            bool: True
        """


# ═══════════════════════════════════════════════════════
# MachineIPMSM (Interior Permanent Magnet)
# ═══════════════════════════════════════════════════════

class MachineIPMSM(MachineSync):
    """Interior permanent magnet synchronous motor.
    
    Stator: Slotted with concentrated/distributed winding
    Rotor: Holes with embedded magnets + flux barriers
    """
    
    # Properties specific to IPMSM
    rotor: LamHole  # Rotor with magnet pockets
    
    def comp_angle_rotor_initial(self) -> float:
        """Initial rotor position (0° aligned with magnet)."""


# ═══════════════════════════════════════════════════════
# MachineSyRM (Synchronous Reluctance)
# ═══════════════════════════════════════════════════════

class MachineSyRM(MachineSync):
    """Synchronous reluctance motor (no permanent magnets).
    
    Stator: Slotted with winding
    Rotor: Flux barriers (air pockets) for reluctance torque
    """
    
    rotor: LamHole  # Rotor with flux barriers
    
    def comp_angle_rotor_initial(self) -> float:
        """Initial rotor position (aligned with d-axis)."""
```

---

### 1.2 Lamination Methods

```python
# ═══════════════════════════════════════════════════════
# Lamination (Base)
# ═══════════════════════════════════════════════════════

class Lamination(FrozenClass):
    # Properties
    Rext: float  # External radius [m]
    Rint: float  # Internal radius [m]
    L_stack: float  # Stack length [m]
    material: Material
    
    # Geometric primitives (set by build_geometry)
    curves: List[Arc]  # Boundary curves
    surfaces: List[Surface]  # Core & slot surfaces
    
    def build_geometry(self) -> None:
        """Generate lamination 2D geometry from slot/hole definitions.
        
        Process:
            1. Generate bore shape (rotor outer profile)
            2. Generate slot profiles (stator/rotor slots)
            3. Generate tooth geometry
            4. Create closed surfaces
            5. Compute geometric properties
            
        Sets:
            - self.curves (list of geometric primitives)
            - self.surfaces (list of closed 2D regions)
        """
        
    def comp_length(self, L_from_tooth_pitch: bool = False) -> None:
        """Calculate stack length [m].
        
        Parameters:
            L_from_tooth_pitch (bool): If True, compute from tooth pitch
            
        Sets:
            self.L_stack: Calculated length
        """
        
    def comp_masses(self) -> None:
        """Calculate lamination mass [kg].
        
        Dependencies:
            - material.struct.rho (density)
            - comp_volumes() executed
            
        Computes:
            - core_mass [kg]
            - slot_mass [kg]
            - total_mass [kg]
        """
        
    def comp_surfaces(self) -> None:
        """Calculate lamination surface areas [m²].
        
        Computes:
            - yoke_surface
            - bore_surface
            - tooth_surface
            - slot_surface
        """
        
    def comp_volumes(self) -> None:
        """Calculate lamination volumes [m³].
        
        Computes:
            - core_volume
            - slot_volume
            - yoke_volume
            - total_volume
        """
        
    def get_Rbo(self) -> float:
        """Get bore radius (rotor outer) [m].
        
        Returns:
            float: Bore radius = Rext - height_yoke_rotor
        """
        
    def get_Ryoke(self) -> float:
        """Get yoke radius [m].
        
        Returns:
            float: Yoke inner radius
        """


# ═══════════════════════════════════════════════════════
# LamSlot (Slotted Lamination)
# ═══════════════════════════════════════════════════════

class LamSlot(Lamination):
    # Properties
    slot: Slot  # Slot geometry definition
    
    def build_geometry(self) -> None:
        """Generate slotted lamination geometry.
        
        Process:
            1. Generate slot profile (by slot.build_geometry_*)
            2. Replicate slot around circumference (Nslot times)
            3. Generate bore shape between slots
            4. Generate tooth geometry
            5. Create surfaces
        """


# ═══════════════════════════════════════════════════════
# LamSlotWind (Slotted with Winding - Stator)
# ═══════════════════════════════════════════════════════

class LamSlotWind(LamSlot):
    # Properties
    winding: Winding  # Winding definition
    
    def build_geometry(self) -> None:
        """Generate stator geometry with winding slots."""


# ═══════════════════════════════════════════════════════
# LamHole (Lamination with Holes - Rotor)
# ═══════════════════════════════════════════════════════

class LamHole(Lamination):
    # Properties
    hole: List[Hole]  # List of magnet pocket definitions
    
    def build_geometry(self) -> None:
        """Generate rotor geometry with magnet pockets.
        
        Process:
            1. Generate bore shape (rotor outer surface)
            2. Generate magnet cavity profiles (holes)
            3. Generate magnetic pole faces
            4. Generate flux barriers (air gaps within magnet pockets)
            5. Create surfaces for core, magnets, barriers
        """


class HoleM50(Hole):
    """Standard IPM V-shaped magnet hole.
    
    Geometric parameters:
        - W0: Opening width [m]
        - W1, W2: Magnet width sections [m]
        - H0, H1, H2: Depth sections [m]
    """


class HoleM51(Hole):
    """IPM U-shaped magnet hole."""


class HoleM57(Hole):
    """Multi-piece magnet hole (2 embedded magnets)."""
```

---

### 1.3 Slot Methods

```python
# ═══════════════════════════════════════════════════════
# Slot (Base Class)
# ═══════════════════════════════════════════════════════

class Slot(FrozenClass):
    # Properties (vary by slot type)
    # SlotW11: H0, H1, H2, W0, W1, W2 (height & width dimensions)
    # SlotM10: H0, H1, H2, W0, W1, W2 (magnet slot dimensions)
    
    def build_geometry_active(self) -> None:
        """Generate active slot area profile (where winding sits).
        
        Returns:
            None (modifies internal curves)
            
        Sets:
            - Active slot boundaries
            - Opening profile
        """
        
    def build_geometry_half_tooth(self) -> None:
        """Generate tooth profile (non-slot region).
        
        Returns:
            None
            
        Sets:
            - Tooth tip geometry
            - Tooth body geometry
        """
        
    def comp_height(self) -> float:
        """Calculate total slot height [m].
        
        Returns:
            float: H_slot = H0 + H1 + H2 + ... (dimensions summed)
        """
        
    def comp_height_active(self) -> float:
        """Calculate active (winding) slot height [m].
        
        Returns:
            float: H_active (typically H1 + H2, excluding opening H0)
        """
        
    def comp_height_opening(self) -> float:
        """Calculate slot opening height [m].
        
        Returns:
            float: H0
        """
        
    def comp_surface(self) -> float:
        """Calculate slot cross-section area [m²].
        
        Returns:
            float: Slot active area
        """
        
    def comp_surface_active(self) -> float:
        """Calculate active slot surface [m²]."""
        
    def comp_angle_opening(self) -> float:
        """Calculate slot opening angle [rad].
        
        Returns:
            float: Angular width of opening (opening_width / Rbore)
        """
        
    def comp_angle_active_eq(self) -> float:
        """Calculate equivalent active slot angle [rad]."""


# ═══════════════════════════════════════════════════════
# SlotW11 (Induction Motor Trapezoidal Slot)
# ═══════════════════════════════════════════════════════

class SlotW11(Slot):
    """Standard induction motor slot (IEC/ISO standard).
    
    Geometric Parameters:
        H0 [m]: Slot opening height (above wedge)
        H1 [m]: Wedge height (closed section)
        H2 [m]: Active slot height (body)
        W0 [m]: Opening width at bore
        W1 [m]: Slot bottom width
        W2 [m]: Slot top width
    
    Cross-section: Trapezoid with rounded opening
    """
    
    H0: float  # Opening height
    H1: float  # Wedge height
    H2: float  # Active height
    W0: float  # Opening width
    W1: float  # Bottom width
    W2: float  # Top width


# ═══════════════════════════════════════════════════════
# SlotM10 (IPM Magnet Slot)
# ═══════════════════════════════════════════════════════

class SlotM10(Slot):
    """IPM magnet pocket (rectangular simple).
    
    Geometric Parameters:
        H0 [m]: Pocket opening width (radial)
        W0 [m]: Pocket width at top
        W1 [m]: Pocket width at bottom
        W2 [m]: Pocket depth
    """
    
    H0: float
    W0: float
    W1: float
    W2: float
```

---

### 1.4 Winding Methods

```python
# ═══════════════════════════════════════════════════════
# Winding (Base)
# ═══════════════════════════════════════════════════════

class Winding(FrozenClass):
    # Properties
    is_stator: bool  # True for stator, False for rotor
    Nlayer: int  # Number of conductor layers per slot (1 or 2)
    Nphase: int  # Number of phases (typically 3)
    Npcpp: int  # Number of parallel paths (typically 1 or 2)
    Ntsp: int  # Number of turns per slot per phase
    
    # Connection info
    connection_matrix: np.ndarray  # Slot-to-phase connectivity
    
    def comp_connection_mat(self) -> None:
        """Generate connection matrix showing slot→phase mapping.
        
        Sets:
            connection_matrix [Nslot × Nphase] with +1/-1 for polarity
        """
        
    def comp_Ntsp(self) -> int:
        """Calculate turns per slot per phase [count].
        
        Returns:
            int: N_turns = (N_conductor_per_slot) / Nphase
        """
        
    def comp_Ncspc(self) -> int:
        """Calculate conductors per slot per phase.
        
        Returns:
            int: N_conductor_per_slot_phase
        """
        
    def comp_periodicity(self) -> int:
        """Calculate periodicity (number of identical pole pairs).
        
        Returns:
            int: Periodicity factor (for FEA symmetry reduction)
        """
        
    def comp_winding_factor(self) -> float:
        """Calculate winding factor (k_w, effects harmonic content).
        
        Returns:
            float: Winding factor [0..1]
            
        Formula:
            k_w = k_d × k_p (distribution × pitch factor)
        """
        
    def comp_phasor_angle(self) -> np.ndarray:
        """Calculate phase angle shift between phases.
        
        Returns:
            np.ndarray: Phase angles [rad] for each phase
        """
        
    def comp_length_endwinding(self) -> float:
        """Calculate end-winding length [m] (axial extension).
        
        Returns:
            float: End winding length per pole
        """
        
    def get_connection_mat(self) -> np.ndarray:
        """Get connection matrix (already computed).
        
        Returns:
            np.ndarray: Connection matrix
        """


# ═══════════════════════════════════════════════════════
# WindingSC (Squirrel Cage)
# ═══════════════════════════════════════════════════════

class WindingSC(Winding):
    """Squirrel cage winding (distributed rotor bars)."""
    
    Nbar: int  # Number of rotor bars
    
    def comp_Ntsp(self) -> int:
        """Return 1 (cage has 1 "turn" per bar)."""
```

---

### 1.5 Simulation & Solver Methods

```python
# ═══════════════════════════════════════════════════════
# Simulation (Base)
# ═══════════════════════════════════════════════════════

class Simulation(FrozenClass):
    # Properties
    name: str
    machine: Machine
    input: Input
    var_load: VarLoad
    var_param: VarParam
    output: Output
    
    def run(self) -> Output:
        """Execute simulation.
        
        Process:
            1. Validate input & machine (call check())
            2. For each parameter variation:
                a. Rebuild machine geometry (if parametric)
                b. For each load point:
                    - Solve electromagnetics (magnetics.solve())
                    - Compute electrical quantities
                    - Compute losses
                    - Compute forces/torque
                c. Store results in output
            3. Return output object
            
        Returns:
            Output: Results container with all computed quantities
        """
        
    def init_logger(self, logger_name: str) -> None:
        """Initialize logging system."""
        
    def get_var_load(self) -> List[Dict]:
        """Get load variation cases.
        
        Returns:
            List: Load cases (current/torque/speed variations)
        """
        
    def get_OP_array(self) -> List[OP]:
        """Get operating point array.
        
        Returns:
            List[OP]: Array of OP objects (if OPMatrix)
        """


# ═══════════════════════════════════════════════════════
# Magnetics (FEA Solver Interface)
# ═══════════════════════════════════════════════════════

class Magnetics(FrozenClass):
    
    def solve(self, output: Output) -> Output:
        """Run FEA magnetic field computation.
        
        Parameters:
            output (Output): Result container to populate
            
        Returns:
            Output: Populated with magnetic field solution
            
        Sets in OutMag:
            - B_mag [T]: Magnetic flux density field
            - H_mag [A/m]: Magnetic field strength
            - flux_linkage [Wb]: Flux through winding
            - back_emf [V]: Back-EMF from rotor motion
            - torque_em [N⋅m]: Electromagnetic torque
            - cogging_torque: Cogging/detent torque
        """


class MagFEMM(Magnetics):
    """FEMM (Finite Element Method Magnetics) solver wrapper.
    
    Process:
        1. Export machine geometry to FEMM format
        2. Create 2D mesh with periodic BC
        3. Solve Laplace equation: ∇² A = 0
        4. Extract B field from potential A
        5. Post-process: integrate forces, torques
    """
    
    def solve(self, output: Output) -> Output:
        """Run FEMM 2D FEA solver."""


class MagElmer(Magnetics):
    """Elmer FEA solver wrapper.
    
    More advanced than FEMM:
        - 2D/3D capability
        - Non-linear B-H curves
        - Transient analysis
        - Multi-physics (thermal, structural)
    """
    
    def solve(self, output: Output) -> Output:
        """Run Elmer solver."""
```

---

### 1.6 Loss Calculation Methods

```python
# ═══════════════════════════════════════════════════════
# Loss (Result Container)
# ═══════════════════════════════════════════════════════

class Loss(FrozenClass):
    # Component losses [W]
    loss_core: float = 0  # Iron losses (hysteresis + eddy)
    loss_joule: float = 0  # Copper losses (I²R)
    loss_windage: float = 0  # Friction + ventilation
    loss_magnet: float = 0  # Magnet eddy current
    loss_proximity: float = 0  # Skin effect proximity
    
    @property
    def loss_total(self) -> float:
        """Total losses [W]."""
        return (self.loss_core + self.loss_joule +
                self.loss_windage + self.loss_magnet)


# ═══════════════════════════════════════════════════════
# LossModelJoule (Copper Loss)
# ═══════════════════════════════════════════════════════

class LossModelJoule(FrozenClass):
    
    def comp_loss_Joule(self, I_rms: float, R_wind: float) -> float:
        """Calculate Joule loss in winding [W].
        
        Parameters:
            I_rms (float): RMS current [A]
            R_wind (float): Winding resistance [Ω]
            
        Returns:
            float: Power loss [W]
            
        Formula:
            P_joule = I_rms² × R_wind
        """


# ═══════════════════════════════════════════════════════
# LossModelSteinmetz (Iron Loss - Empirical)
# ═══════════════════════════════════════════════════════

class LossModelSteinmetz(FrozenClass):
    
    def comp_loss_Steinmetz(self, B_peak: float, f: float,
                           V_core: float) -> float:
        """Calculate core loss using Steinmetz equation [W].
        
        Parameters:
            B_peak (float): Peak magnetic flux density [T]
            f (float): Frequency [Hz]
            V_core (float): Core volume [m³]
            
        Returns:
            float: Power loss [W]
            
        Formula:
            P_core = k_h × B_peak^2 × f × V_core + k_e × (B_peak × f)^2 × V_core
              (hysteresis + eddy current components)
        """


# ═══════════════════════════════════════════════════════
# LossModelWindage (Friction & Ventilation)
# ═══════════════════════════════════════════════════════

class LossModelWindagePyrhonen(FrozenClass):
    
    def comp_loss_Windage(self, N_rpm: float, D_rotor: float,
                         L_stack: float) -> float:
        """Calculate windage loss (Pyrhonen model) [W].
        
        Parameters:
            N_rpm (float): Rotational speed [RPM]
            D_rotor (float): Rotor diameter [m]
            L_stack (float): Stack length [m]
            
        Returns:
            float: Power loss [W]
            
        Formula:
            P_windage ∝ ρ_air × (ω × D)³ × A_gap
        """


# ═══════════════════════════════════════════════════════
# OutLoss (Loss Results Container)
# ═══════════════════════════════════════════════════════

class OutLoss(FrozenClass):
    
    # Loss breakdown [W]
    loss_joule: float = 0  # Winding loss
    loss_core: float = 0  # Iron loss (stator + rotor)
    loss_stator_core: float = 0  # Stator core loss detail
    loss_rotor_core: float = 0  # Rotor core loss detail
    loss_magnet: float = 0  # Permanent magnet loss
    loss_windage: float = 0  # Friction/ventilation
    loss_other: float = 0  # Other losses
    
    @property
    def loss_total(self) -> float:
        """Total losses [W]."""
        return (self.loss_joule + self.loss_core +
                self.loss_magnet + self.loss_windage)
    
    @property
    def efficiency(self) -> float:
        """Efficiency [0..1].
        
        Returns:
            float: η = P_out / (P_out + P_loss)
        """
```

---

### 1.7 Output & Results Methods

```python
# ═══════════════════════════════════════════════════════
# Output (Root Results Container)
# ═══════════════════════════════════════════════════════

class Output(FrozenClass):
    # Sub-results objects
    outgeo: OutGeo = None  # Geometry results
    outelec: OutElec = None  # Electrical results
    outmag: OutMag = None  # Magnetic field results
    outloss: OutLoss = None  # Loss breakdown
    outforce: OutForce = None  # Force/torque results
    outstruct: OutStruct = None  # Structural (optional)
    outpost: OutPost = None  # Post-processing
    
    # Metadata
    name: str = ""
    path_result: str = ""  # Storage path
    
    def export_to_mat(self, filepath: str) -> None:
        """Export results to MATLAB .mat file.
        
        Parameters:
            filepath (str): Path to .mat file
            
        Saves:
            - All OutGeo, OutElec, OutMag, OutLoss data
            - Metadata & machine definition
        """
        
    def plot_B_mesh(self) -> None:
        """Plot magnetic flux density field on mesh."""
        
    def get_data_from_str(self, data_path: str) -> np.ndarray:
        """Extract data from nested output structure.
        
        Parameters:
            data_path (str): Path like "outmag.B_mag" or "outloss.loss_joule"
            
        Returns:
            np.ndarray: Requested data
        """


# ═══════════════════════════════════════════════════════
# OutGeo (Geometric Results)
# ═══════════════════════════════════════════════════════

class OutGeo(FrozenClass):
    
    # Radii [m]
    Rint_stator: float = 0  # Stator bore radius
    Rext_stator: float = 0  # Stator outer radius
    Rint_rotor: float = 0  # Rotor bore radius
    Rext_rotor: float = 0  # Rotor outer radius (Rbo)
    Rgap_mec: float = 0  # Mechanical air gap
    
    # Dimensions [m]
    L_stack: float = 0  # Stack length
    H_slot_stator: float = 0  # Stator slot height
    H_slot_rotor: float = 0  # Rotor slot height
    
    # Areas [m²]
    A_slot_stator: float = 0  # Stator slot area
    A_tooth_stator: float = 0  # Stator tooth area
    A_slot_rotor: float = 0  # Rotor slot area
    
    # Masses [kg]
    mass_stator_core: float = 0
    mass_rotor_core: float = 0
    mass_magnet: float = 0


# ═══════════════════════════════════════════════════════
# OutMag (Magnetic Results from FEA)
# ═══════════════════════════════════════════════════════

class OutMag(FrozenClass):
    
    # Field solution
    B_mag: np.ndarray = None  # Flux density on mesh [T]
    H_mag: np.ndarray = None  # Field strength on mesh [A/m]
    
    # Integrated quantities [Wb, V, N⋅m]
    flux_linkage: float = 0  # λ [Wb]
    back_emf: float = 0  # Back-EMF RMS [V]
    torque_em: float = 0  # Electromagnetic torque [N⋅m]
    torque_cogging: float = 0  # Cogging torque [N⋅m]
    torque_ripple: float = 0  # Torque ripple [%]
    
    # Detailed torque
    torque_mag: float = 0  # Magnetic torque [N⋅m]
    torque_reluctance: float = 0  # Reluctance torque (SynRM) [N⋅m]


# ═══════════════════════════════════════════════════════
# OutElec (Electrical Results)
# ═══════════════════════════════════════════════════════

class OutElec(FrozenClass):
    
    # Voltages [V]
    V_phase: float = 0  # Phase voltage (RMS)
    V_line: float = 0  # Line voltage (RMS)
    
    # Currents [A]
    I_phase: float = 0  # Phase current (RMS)
    I_peak: float = 0  # Peak phase current
    
    # Power [W]
    P_input: float = 0  # Electrical input power
    P_gap: float = 0  # Air gap power
    P_output: float = 0  # Mechanical output power (P_input - losses)
    
    # Efficiency
    efficiency: float = 0  # η = P_output / P_input


# ═══════════════════════════════════════════════════════
# OutForce (Force & Torque Results)
# ═══════════════════════════════════════════════════════

class OutForce(FrozenClass):
    
    # Torques [N⋅m]
    torque: float = 0  # Total electromagnetic torque
    torque_ripple: float = 0  # Peak-to-peak ripple [%]
    torque_cogging: float = 0  # Cogging torque (no current)
    
    # Forces [N]
    force_radial: float = 0  # Radial magnetic force
    force_tangential: float = 0  # Tangential force
    
    # Torque map (for multiple operating points)
    torque_map: np.ndarray = None  # Torque vs current/speed
```

---

## 2. EMACH PYMOTOR GEO KEY METHOD SIGNATURES

### 2.1 Analysis Module Functions

```python
# ═══════════════════════════════════════════════════════
# analysis_airgap.py
# ═══════════════════════════════════════════════════════

def find_origin_candidates(entities: List[EntityInfo],
                          method: str = 'average') -> List[Tuple[float, float]]:
    """Find candidate motor centers from geometry.
    
    Parameters:
        entities (List[EntityInfo]): DXF entities
        method (str): 'average', 'centroid', or 'optimization'
        
    Returns:
        List[Tuple[float, float]]: Candidate origin points [(x, y), ...]
        
    Methods:
        - average: Average of all entity centroids
        - centroid: Weighted centroid by area
        - optimization: Minimize radius variance across all entities
    """


def find_concentric_radii(entities: List[EntityInfo],
                         origin: Tuple[float, float] = (0.0, 0.0),
                         step: float = 1.0) -> List[float]:
    """Find concentric circular bands (motor layers).
    
    Parameters:
        entities (List[EntityInfo]): Motor geometry
        origin (Tuple[float, float]): Motor center
        step (float): Radial bin width [mm]
        
    Returns:
        List[float]: Sorted radii [mm] with entity concentrations
        
    Process:
        1. Project all entity points to radii from origin
        2. Bin by radius (step-size bins)
        3. Find peaks in bin histogram (radial discontinuities)
        4. Return peaks as characteristic radii
        
    Output Examples:
        [20.0, 35.5, 36.2, 45.0, 47.0, 50.0]  # Inner bore, airgap, stator outer
    """


def split_stator_rotor(entities: List[EntityInfo],
                      origin: Tuple[float, float] = (0.0, 0.0),
                      airgap_tolerance: float = 1.0) -> Tuple[List[EntityInfo], List[EntityInfo]]:
    """Separate stator and rotor entities by radius from motor center.
    
    Parameters:
        entities (List[EntityInfo]): All entities
        origin (Tuple[float, float]): Motor center
        airgap_tolerance (float): Gap width [mm] between components
        
    Returns:
        Tuple[List[EntityInfo], List[EntityInfo]]: (stator_entities, rotor_entities)
        
    Logic:
        1. find_concentric_radii() to find radial bands
        2. Identify air gap by largest radial discontinuity
        3. Split: entities below airgap → rotor, above → stator
        
    Example:
        Radii: [20.0, 35.0, 36.5, 45.0, 50.0]  # Gap at 35-36.5
        → Rotor: entities with r < 35.0
        → Stator: entities with r > 36.5
    """


def analyze_closed_regions_for_motor_type(entities: List[EntityInfo]) -> str:
    """Classify motor type from closed region patterns.
    
    Parameters:
        entities (List[EntityInfo]): Rotor or stator entities
        
    Returns:
        str: Motor type classification
               'inner_rotor', 'outer_rotor', 'linear', or 'unknown'
    """


# ═══════════════════════════════════════════════════════
# analysis_rotor.py (RotorCounter Class)
# ═══════════════════════════════════════════════════════

class RotorCounter(ComponentCounter):
    """Multi-method rotor pole counter using cross-validation."""
    
    def count(self, entities: List[EntityInfo],
             origin: Tuple[float, float] = (0.0, 0.0),
             **kwargs) -> int:
        """Count poles from arc distribution.
        
        Parameters:
            entities (List[EntityInfo]): Rotor entities
            origin (Tuple[float, float]): Motor center
            **kwargs:
                - tol_r (float): Radius tolerance [mm]
                - tol_angle (float): Angle tolerance [deg]
                
        Returns:
            int: Estimated pole count
            
        Algorithm:
            1. Group ARC entities by radius band
            2. Analyze angular spacing within each band
            3. Find most consistent period (360/N_poles)
            4. Return mode of period distribution
        """
    
    def count_by_regions(self, entities: List[EntityInfo],
                        origin: Tuple[float, float],
                        **kwargs) -> Dict:
        """Count poles from closed region centroids.
        
        Parameters:
            entities (List[EntityInfo]): Rotor entities (usually containing closed regions)
            origin (Tuple[float, float]): Motor center
            **kwargs:
                - airgap_r_inner (float): Inner airgap radius [mm] (optional)
                
        Returns:
            Dict: {
                'n_poles': int,  # Estimated pole count
                'confidence': str,  # 'high', 'medium', 'low'
                'region_angles': List[float],  # Centroid angles [deg]
                'angular_pitch': float  # Average angular spacing [deg]
            }
            
        Algorithm:
            1. find_closed_regions(entities) → List of closed polygons
            2. For each region: compute centroid (cx, cy)
            3. Calculate angle of each centroid from origin
            4. Analyze angular distribution for periodicity
            5. Infer pole count from period
        """
    
    def estimate_robust(self,
                       entities: List[EntityInfo],
                       origin: Tuple[float, float],
                       verbose: bool = True,
                       **kwargs) -> Dict:
        """Cross-validated pole count estimation.
        
        Parameters:
            entities (List[EntityInfo]): Rotor entities
            origin (Tuple[float, float]): Motor center
            verbose (bool): Print analysis details
            **kwargs: Additional method parameters
            
        Returns:
            Dict: {
                'n_poles': int,  # Final estimated pole count
                'method_arc': int,  # Count from ARC distribution
                'method_region': int,  # Count from closed regions
                'method_fft': int,  # Count from FFT harmonics (if implemented)
                'confidence': str,  # How well methods agree
                'agreement_score': float  # 0..1 (1 = all methods agree)
            }
            
        Process:
            1. count() — Pole count from arc spacing
            2. count_by_regions() — Pole count from region periodicity
            3. FFT analysis of entity distribution (if available)
            4. Compare methods: return consensus estimate
            5. If disagreement: return median + warning
        """


# ═══════════════════════════════════════════════════════
# analysis_stator.py (StatorCounter Class)
# ═══════════════════════════════════════════════════════

class StatorCounter(ComponentCounter):
    """Multi-method stator slot counter."""
    
    def count_slots(self, entities: List[EntityInfo],
                   origin: Tuple[float, float] = (0.0, 0.0),
                   **kwargs) -> int:
        """Count slots from conductor (copper) regions.
        
        Parameters:
            entities (List[EntityInfo]): Stator entities
            origin (Tuple[float, float]): Motor center
            **kwargs:
                - tol_r (float): Radius tolerance [mm]
                
        Returns:
            int: Estimated slot count
            
        Algorithm:
            1. detect_slot_conductors(entities) → conductor locations
            2. Project conductors to angle vs radius
            3. Count distinct angular positions at conductor radius
            4. Return conductor count (= slot count)
        """
    
    def count_slots_by_regions(self,
                              entities: List[EntityInfo],
                              **kwargs) -> Dict:
        """Count slots from closed conductor regions.
        
        Parameters:
            entities (List[EntityInfo]): Stator entities
            **kwargs: Region analysis options
            
        Returns:
            Dict: {
                'n_slots': int,
                'conductor_count': int,  # Detected copper regions
                'slot_pitch_deg': float  # Angular spacing
            }
        """


def detect_slot_conductors(entities: List[EntityInfo],
                          layer_pattern: str = 'CONDUCTOR|COPPER') -> List[EntityInfo]:
    """Identify conductor (copper winding) regions in stator.
    
    Parameters:
        entities (List[EntityInfo]): Stator entities
        layer_pattern (str): DXF layer name pattern (regex)
        
    Returns:
        List[EntityInfo]: Entities on conductor layers
        
    Logic:
        1. Filter entities by layer name matching pattern
        2. Find closed regions on those layers
        3. Return as list
        
    Note:
        Assumes DXF layers are named systematically:
            'CONDUCTOR', 'WINDING', 'COPPER', or similar
    """
```

---

### 2.2 Topology Classification

```python
# ═══════════════════════════════════════════════════════
# topology_rotor.py
# ═══════════════════════════════════════════════════════

class RotorTopologyClassifier:
    """Classify rotor type from geometry (SPM, IPM, SynRM, PMa-SynRM)."""
    
    def classify(self, entities: List[EntityInfo],
                n_poles: int = None,
                verbose: bool = False) -> Dict:
        """Determine rotor topology type.
        
        Parameters:
            entities (List[EntityInfo]): Rotor entities
            n_poles (int): Number of poles (helpful hint)
            verbose (bool): Print analysis details
            
        Returns:
            Dict: {
                'topology': str,  # 'SPM', 'IPM', 'SynRM', 'PMa-SynRM', 'unknown'
                'pole_regions': List[PoleRegionInfo],  # Per-pole breakdown
                'magnet_volume': float,  # Total magnet volume estimate [mm³]
                'barrier_count': int,  # Number of flux barriers
                'confidence': str  # 'high', 'medium', 'low'
            }
            
        Classification Logic:
            1. extract_single_pole_entities() → One-pole geometry
            2. Analyze magnet pocket location:
               - Surface (r_magnet ≈ r_rotor_outer) → SPM
               - Buried (r_magnet < r_rotor_outer) → IPM or SynRM
            3. Check for magnet presence:
               - Magnets present → IPM or SPM or PMa-SynRM
               - No magnets → SynRM (flux barriers only)
            4. Check flux barriers:
               - Barriers present → PMa-SynRM (if magnets too)
        """


# ═══════════════════════════════════════════════════════
# topology_stator.py
# ═══════════════════════════════════════════════════════

class StatorTopologyClassifier:
    """Classify stator slot type from geometry."""
    
    def classify(self, entities: List[EntityInfo],
                n_slots: int = None) -> Dict:
        """Determine stator topology.
        
        Parameters:
            entities (List[EntityInfo]): Stator entities
            n_slots (int): Number of slots (if known)
            
        Returns:
            Dict: {
                'topology': str,  # 'slotted', 'smooth', 'hybrid'
                'slot_type': str,  # 'W11', 'W22', 'open', 'closed', etc.
                'slot_geometry': Dict,  # Estimated slot dimensions
                'conductor_locations': List[Tuple],  # (radius, angle) of conductors
                'confidence': str
            }
        """


# ═══════════════════════════════════════════════════════
# topology.py — Low-level topology analysis
# ═══════════════════════════════════════════════════════

def detect_circular_array_pattern(entities: List[EntityInfo],
                                 origin: Tuple[float, float] = (0.0, 0.0),
                                 min_repeats: int = 4) -> Dict:
    """Detect repeating circular array pattern (poles or slots).
    
    Parameters:
        entities (List[EntityInfo]): Motor entities
        origin (Tuple[float, float]): Motor center
        min_repeats (int): Minimum repetitions to consider pattern
        
    Returns:
        Dict: {
            'has_pattern': bool,  # Pattern found?
            'n_poles': int,  # Number of poles/periods
            'pole_pitch_deg': float,  # Angular spacing [deg]
            'entity_groups': Dict,  # Entities by type/radius group
            'angular_positions': Dict,  # Angles of each group
            'confidence': str  # High/medium/low
        }
        
    Algorithm:
        1. Group entities by "signature" (type + radius band)
        2. For each signature: extract angular positions
        3. Analyze angular spacing (regular stepping?)
        4. Calculate period from spacing: pole_pitch = 360 / n_repeats
        5. Return n_poles = 360 / pole_pitch
    """


def extract_single_pole_entities(entities: List[EntityInfo],
                                origin: Tuple[float, float] = (0.0, 0.0),
                                pole_pitch_deg: float = None,
                                reference_angle: float = 0.0) -> Dict:
    """Extract one pole worth of entities and rotate to reference (0°).
    
    Parameters:
        entities (List[EntityInfo]): Rotor entities
        origin (Tuple[float, float]): Motor center
        pole_pitch_deg (float): Angular width of one pole [deg]
        reference_angle (float): Rotation angle [deg] to align pole
        
    Returns:
        Dict: {
            'entities': List[EntityInfo],  # Rotated one-pole entities
            'pole_index': int,  # Which pole (0, 1, 2, ...)
            'angle_rotated': float,  # Rotation applied [deg]
            'bounds': Dict  # Bounding box of pole
        }
        
    Use Case:
        Extract geometry of one magnet pole for:
        1. Detailed analysis (magnet size, barrier shapes)
        2. Topology classification (SPM vs IPM vs SynRM)
        3. Symmetry-reduction in FEA
        4. Pyleecan conversion (one-pole → parametric slot type)
    """


def reconstruct_from_half(half_entities: List[EntityInfo],
                         n_repeats: int = None,
                         mirror_axis: str = 'x') -> List[EntityInfo]:
    """Reconstruct full geometry from half-unit (1/2 pole or 1/2 slot).
    
    Parameters:
        half_entities (List[EntityInfo]): One-half unit
        n_repeats (int): Number of times to repeat (poles / 2, slots / 2)
        mirror_axis (str): 'x', 'y', or 'xy', or custom angle
        
    Returns:
        List[EntityInfo]: Full reconstructed entities
        
    Process:
        1. Mirror half_entities across mirror_axis → create symmetric pair
        2. Rotate pair by 180° → create full unit (pole or slot)
        3. Rotate full unit by angular pitch
        4. Repeat n_repeats times
        5. Return union of all copies
        
    Benefit:
        Reduce CAD creation effort for symmetric motors:
        Draw 1/4 or 1/2 → auto-generate full motor geometry
    """
```

---

### 2.3 High-Level Pipeline

```python
# ═══════════════════════════════════════════════════════
# pipeline.py — Main entry points
# ═══════════════════════════════════════════════════════

def analyze_dxf_v2(
    dxf_path: str,
    origin: Optional[Tuple[float, float]] = None,
    n_poles: Optional[int] = None,
    n_slots: Optional[int] = None,
    enable_radius_fallback: bool = False,
    fallback_r_shaft_mm: Optional[float] = None,
    fallback_r_stator_outer_mm: Optional[float] = None,
    verbose: bool = True,
) -> Dict:
    """Recommended v1.5.1+ end-to-end DXF analysis pipeline.
    
    Parameters:
        dxf_path (str): Path to motor DXF file
        origin (Tuple or None): Motor center [mm] (auto-detect if None)
        n_poles, n_slots (int or None): Pole/slot count (auto-estimate if None)
        enable_radius_fallback (bool): Use radius-based boundary fallback
        fallback_r_shaft_mm, fallback_r_stator_outer_mm: Boundary radius hints [mm]
        verbose (bool): Print progress & results
        
    Returns:
        Dict: Complete analysis result:
        {
            'geometry': {
                'r_shaft': float,          # Shaft radius [mm]
                'r_rotor_outer': float,    # Rotor outer radius (Rbo)
                'r_stator_inner': float,   # Stator bore radius
                'r_stator_outer': float,   # Stator outer radius
                'stack_length_assumed': float,  # Assumed [mm]
            },
            'rotor': {
                'n_poles': int,             # Estimated pole count
                'pole_pitch_deg': float,    # Angle per pole [deg]
                'topology': str,            # SPM/IPM/SynRM/PMa-SynRM
                'estimated_poles_methods': {  # Cross-check
                    'by_arc': int,
                    'by_region': int,
                    'by_fft': int,
                },
                'confidence': str,          # high/medium/low
                'pole_regions': [...],      # PoleRegionInfo list
                'magnets': [...],           # Magnet entity groups
                'flux_barriers': [...],     # Barrier entity groups
                'rotor_core': [...],        # Core entities
            },
            'stator': {
                'n_slots': int,              # Estimated slot count
                'slot_pitch_deg': float,     # Angle per slot [deg]
                'topology': str,             # slotted/smooth/hybrid
                'estimated_slots_methods': {  # Cross-check
                    'by_conductor': int,
                    'by_tooth': int,
                },
                'conductors': [...],        # Conductor entity groups
                'slot_geometry': {...},     # Estimated slot params
                'tooth_geometry': [...],    # Tooth profiles
            },
            'airgap': {
                'radius_inner': float,      # Rotor outer [mm]
                'radius_outer': float,      # Stator inner [mm]
                'width': float,             # Gap width [mm]
                'center_candidates': [...], # Possible motor centers
            },
            'faces': [Region(...), ...],     # Closed topological faces
            'face_summary': {
                'magnets': int,               # Count of magnet regions
                'flux_barriers': int,         # Count of barriers
                'conductors': int,            # Count of winding regions
                'cores': int,                 # Count of iron regions
            },
            'dxf_path': str,                # Input file path
            'analysis_time_sec': float,     # Computation time
            'errors': [],                   # Any warnings/errors during analysis
            'warnings': [],                 # Non-fatal issues
        }
        
    Execution Flow:
        1. read_entity_list(dxf_path) → EntityInfo[]
        2. find_origin_candidates() → Possible motor centers
        3. split_stator_rotor() → Separate components
        4. RotorCounter().estimate_robust() → Pole count
        5. StatorCounter().estimate_robust() → Slot count
        6. RotorTopologyClassifier().classify() → Rotor type (SPM/IPM/SynRM)
        7. StatorTopologyClassifier().classify() → Stator type
        8. extract_single_pole_entities() → One-pole geometry
        9. region_closing.py → Topological face closure per pole
        10. regions.py → Region classification (magnet/barrier/conductor/core)
        11. Return comprehensive result dict
        
    Outputs Ready For:
        - pyleecan_bridge.create_machine_*() → MachineSIPMSM, MachineIPMSM, etc.
        - motorcad_bridge.export_to_motorcad_geometry() → MotorCAD project
        - Direct geometric analysis & validation
        - Visualization & reporting
    """


def analyze_motor_dxf(
    dxf_path: str,
    n_poles: int = None,
    n_slots: int = None,
    origin: Tuple = None,
) -> Dict:
    """Legacy v1.0 analysis pipeline (backward compatibility).
    
    Simpler than analyze_dxf_v2():
        - No explicit face closure
        - Assumes pre-closed geometry in DXF
        - Faster but less robust
        
    Use analyze_dxf_v2() for new code.
    """


def quick_analyze(dxf_path: str) -> Dict:
    """Lightweight rapid analysis (minimal computation).
    
    Returns:
        Dict: Basic geometry info only (topology, rough dimensions)
        
    Use for:
        - Quick validation before detailed analysis
        - Batch checking multiple DXF files
        - Mobile/web app scenarios (speed-critical)
    """
```

---

### 2.4 Region & Face Detection

```python
# ═══════════════════════════════════════════════════════
# regions.py — Region/Face representation
# ═══════════════════════════════════════════════════════

@dataclass
class Region:
    """Topologically-closed 2D face with semantic labels."""
    
    # Identity
    region_id: str  # Unique ID ("magnet_0", "conductor_12", etc.)
    region_type: str  # 'magnet', 'conductor', 'flux_barrier', 'core', 'yoke', 'shaft'
    
    # Geometry
    vertices: List[Tuple[float, float]]  # Closed polygon points [mm]
    centroid: Tuple[float, float]  # Center of mass (x, y) [mm]
    area: float  # Polygon area [mm²]
    
    # Hierarchy & Relations
    parent_pole: int = -1  # Which pole (0, 1, 2, ..., or -1 if N/A)
    parent_slot: int = -1  # Which slot (0, 1, 2, ..., or -1 if N/A)
    
    # Semantic properties
    properties: Dict[str, Any] = None  # Custom tags/metadata
    
    def __post_init__(self):
        """Compute properties after initialization."""
        if self.properties is None:
            self.properties = {}
    
    def get_angular_position(self, origin=(0, 0)) -> float:
        """Get centroid angle from origin [deg, 0-360]."""
        x, y = self.centroid
        ox, oy = origin
        angle_rad = math.atan2(y - oy, x - ox)
        return math.degrees(angle_rad) % 360


# ═══════════════════════════════════════════════════════
# region_closing.py — Topological face closure
# ═══════════════════════════════════════════════════════

def find_closed_regions(entities: List[EntityInfo]) -> List[List[EntityInfo]]:
    """Identify closed region boundaries from entities.
    
    Parameters:
        entities (List[EntityInfo]): All geometric entities
        
    Returns:
        List[List[EntityInfo]]: Each inner list is one closed region boundary
        
    Algorithm:
        1. Filter to LWPOLYLINE/POLYLINE entities
        2. Check if each polyline forms closed loop (%1==0)
        3. Group connected segments into discrete loops
        4. Return list of loops
        
    Note:
        Some DXF files may have open polylines or incomplete boundaries.
        region_closing.py handles closure reconstruction.
    """


def reconstruct_closed_faces(entities: List[EntityInfo],
                            enable_toplevel_closure: bool = True) -> List[Region]:
    """Construct closed Region objects from partial/unclosed DXF entities.
    
    Parameters:
        entities (List[EntityInfo]): DXF entities (may be unclosed)
        enable_toplevel_closure (bool): Attempt closure of gaps
        
    Returns:
        List[Region]: Complete closed faces ready for analysis
        
    Process:
        1. Extract LINE/ARC/polyline boundary segments
        2. Stitch segments into continuous curves
        3. Close any gaps (via fallback radius or snapping)
        4. Classify inside/outside via winding number algorithm
        5. Create Region objects with centroid & area
        
    Handles:
        - Open polylines (gap at endpoint)
        - Disconnected segments (bridges gap via arc)
        - Multiple nested regions (concentric faces)
    """


def classify_regions(regions: List[Region],
                    layer_info: Dict[str, str] = None) -> List[Region]:
    """Assign semantic type (magnet, conductor, core, barrier, etc.) to regions.
    
    Parameters:
        regions (List[Region]): Unclassified Region objects
        layer_info (Dict): Mapping {DXF_layer_name: region_type}
        
    Returns:
        List[Region]: Regions with updated region_type property
        
    Heuristics (if layer_info unavailable):
        - Layer name contains 'MAGNET', 'MAG', 'PM' → 'magnet'
        - Layer name contains 'CONDUCTOR', 'COPPER', 'WIND' → 'conductor'
        - Layer name contains 'BARRIER', 'AIR_BARRIER' → 'flux_barrier'
        - Layer name contains 'CORE', 'IRON' → 'core'
        - Layer name contains 'ROTOR' + no parent_pole → 'rotor_core'
        - Layer name contains 'STATOR' + no parent_pole → 'stator_core'
        - Else → 'unknown'
    """
```

---

## 3. EMACH-TO-PYLEECAN CONVERSION

### 3.1 Bridge Function Signatures

```python
# ═══════════════════════════════════════════════════════
# pyleecan_bridge.py — DXF → Pyleecan conversion
# ═══════════════════════════════════════════════════════

def create_machine_from_rotor_entities(
    rotor_entities: List[EntityInfo],
    stator_entities: List[EntityInfo],
    rotor_topology: str,  # 'SPM', 'IPM', 'SynRM', 'PMa-SynRM'
    n_poles: int,
    n_slots: int,
    rotor_outer_radius_mm: float,
    stator_outer_radius_mm: float,
    stack_length_mm: float,
    verbose: bool = False,
) -> Machine:
    """Convert pyMotorGeo rotor+stator entities to Pyleecan Machine.
    
    Parameters:
        rotor_entities (List[EntityInfo]): Rotor geometry from DXF
        stator_entities (List[EntityInfo]): Stator geometry from DXF
        rotor_topology (str): 'SPM', 'IPM', 'SynRM', or 'PMa-SynRM'
        n_poles, n_slots (int): Pole and slot counts
        rotor_outer_radius_mm, stator_outer_radius_mm (float): Radii [mm]
        stack_length_mm (float): Axial length [mm]
        verbose (bool): Print conversion details
        
    Returns:
        Machine: Pyleecan machine object
        
    Conversion Steps:
        1. create_lamination_from_geometry(rotor_entities, ...)
           → Rotor: LamSlotM or LamHole
        2. create_lamination_from_geometry(stator_entities, ...)
           → Stator: LamSlotWind
        3. create_hole_from_magnet_region(magnet_regions, ...)
           → Holes: HoleM50, HoleM51, HoleM52, ... (detected from magnet size)
        4. create_slot_from_geometry(stator_slot_entities, ...)
           → SlotW11, SlotW22, SlotW60, etc. (matched to geometry profile)
        5. create_winding_from_analysis(stator_entities, n_slots, ...)
           → Winding (phases, turns, distribution)
        6. Assemble: Machine(stator=..., rotor=..., frame=Frame(), shaft=Shaft())
        
    Returns:
        - 'SPM' → MachineSIPMSM (surface magnet)
        - 'IPM' → MachineIPMSM (interior magnet + barriers)
        - 'SynRM' → MachineSyRM (no magnets, only barriers)
        - 'PMa-SynRM' → MachineIPMSM (hybrid magnet + barriers)
    """


def create_lamination_from_geometry(
    entities: List[EntityInfo],
    lam_type: str,  # 'stator_slotted', 'rotor_slotted', 'rotor_holes'
    n_poles: int,
    n_slots: int,
    Rext: float,  # External radius [m]
    Rint: float,  # Internal radius [m]
    L_stack: float,  # Stack length [m]
    material_name: str = 'Steel',  # Material name for lookup
) -> Lamination:
    """Convert DXF geometry → Pyleecan Lamination object.
    
    Parameters:
        entities (List[EntityInfo]): DXF geometry entities
        lam_type (str): 'stator_slotted' → LamSlotWind
                        'rotor_slotted' → LamSlotM
                        'rotor_holes' → LamHole
        n_poles, n_slots (int): Pole/slot counts
        Rext, Rint (float): Radii [m]
        L_stack (float): Stack length [m]
        material_name (str): Steel/NdFeB/etc.
        
    Returns:
        Lamination: Configured Pyleecan lamination
        
    Process:
        1. If 'stator' in lam_type:
           → create_slot_from_geometry(entities)
           → LamSlotWind with Slot + Winding
        2. If 'rotor' in lam_type:
           → Detect magnet vs barrier regions
           → create_hole_from_magnet_region() for each magnet
           → LamHole with Holes array or LamSlotM with Slots
        3. Assign material by name (lookup from Pyleecan library)
        4. Set radii & length
        5. Call build_geometry()
        6. Return configured object
    """


def create_slot_from_geometry(
    slot_entities: List[EntityInfo],
    geometry_type: str = 'auto',  # 'auto', 'SlotW11', 'SlotW22', etc.
    H_slot: float = None,  # Total slot height [m]
    W_opening: float = None,  # Opening width [m]
) -> Slot:
    """Convert slot outline → Pyleecan Slot type.
    
    Parameters:
        slot_entities (List[EntityInfo]): Entities forming one slot
        geometry_type (str): 'auto' = infer type from shape
                             'SlotW11', 'SlotW22', etc. = explicit type
        H_slot (float): Slot height hint [m]
        W_opening (float): Opening width hint [m]
        
    Returns:
        Slot: SlotW11, SlotW22, SlotM10, SlotM50, etc.
        
    Auto-Detection Algorithm:
        1. Compute slot geometry: height, opening width, body width, angle
        2. Check aspect ratios & angles against known Pyleecan slots
        3. Match to closest Slot type (geometric signature matching)
        4. Extract parameters (H0, H1, H2, W0, W1, W2, ...)
        5. Create and return Slot instance
        
    Supported Conversions:
        Standard IEC slots:
            - Trapezoid with wedge → SlotW10-W30 (20+ types)
            - Rectangular → SlotCirc
        IPM/Rotor slots:
            - Magnet pocket (rectangular) → SlotM10, SlotM11, ...
            - V-shaped pocket → SlotM50, SlotM51, SlotM52, ...
            - Deep pocket → SlotM57, SlotM58, ...
    """


def create_hole_from_magnet_region(
    magnet_region: Region,
    magnet_type: str = 'auto',  # 'auto', 'HoleM50', 'HoleM51', etc.
    magnet_material: str = 'NdFeB35',  # Material grade
) -> Hole:
    """Convert magnet cavity/pocket → Pyleecan Hole object.
    
    Parameters:
        magnet_region (Region): Topological face from region_closing.py
        magnet_type (str): 'auto' = infer from shape
                           'HoleM50', 'HoleM51', etc. = explicit
        magnet_material (str): NdFeB35, NdFeB50, AlNiCo, etc.
        
    Returns:
        Hole: HoleM50, HoleM51, HoleM52, etc. (with embedded Magnet)
        
    Auto-Detection Algorithm:
        1. Compute magnet pocket outline: width, depth, opening angle
        2. Detect pocket shape pattern:
           - Rectangular simple → HoleM10
           - V-shaped (two magnet) → HoleM50, HoleM51
           - U-shaped (one magnet) → HoleM52, HoleM53
           - Complex (multi-piece) → HoleM57, HoleM58, HoleM60+
        3. Extract dimensions (W0, W1, H0, H1, H2, ...)
        4. Create Hole instance with Magnet child object
        5. Assign magnet material properties
        
    Supported Conversions:
        V-shaped (2-magnet IPM): HoleM50 → HoleM63 (14 variants)
        Special torque optimized: HoleM57, HoleM58, HoleM60, HoleM61, HoleM62, HoleM63
    """


def create_winding_from_analysis(
    stator_entities: List[EntityInfo],
    n_slots: int,
    n_poles: int = None,
    conductor_layer_pattern: str = 'CONDUCTOR|COPPER',
) -> Winding:
    """Infer winding definition from stator geometry.
    
    Parameters:
        stator_entities (List[EntityInfo]): Stator entities
        n_slots (int): Number of slots
        n_poles (int): Number of poles (optional, for pitch calculation)
        conductor_layer_pattern (str): DXF layer pattern for conductors
        
    Returns:
        Winding: Configured Winding object
        
    Heuristics:
        1. detect_slot_conductors(stator_entities, conductor_layer_pattern)
           → Find conductor regions
        2. Count conductors per slot & per phase
           → Infer Ntsp (turns per slot per phase)
        3. Determine phase distribution:
           - If 3 conductors evenly spaced in circumference → 3-phase
           - If 2 → 2-phase or 2-pole single-phase
           - If 1 → single-phase
        4. Determine winding type:
           - If conductors distributed → distributed winding (Nlayer=2 typically)
           - If concentrated → concentrated winding (Nlayer=1)
        5. Create Winding object
        
    Limitations:
        - Cannot fully infer coil connections (connection_matrix) from DXF
        - Creates simplified winding; user may need manual refinement
        - For highest accuracy, provide n_poles hint
    """
```

---

**END OF METHOD SIGNATURES & DATA FLOW DETAILS**

*This document provides function/method signatures, parameters, return types, and usage examples needed for detailed PlantUML sequence diagrams and activity diagrams.*

Use in conjunction with:
- `CODEBASE_ARCHITECTURE_ANALYSIS.md` (class hierarchies, data flow)
- `COMPLETE_CLASS_REFERENCE.md` (complete class list)
