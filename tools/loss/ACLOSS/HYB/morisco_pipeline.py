"""End-to-end Morisco Hybrid FEA-PEEC pipeline.

Accepts Motor-CAD FEA data via pyMCAD's MagneticRegionsTimeSeries
and calculates AC losses using the extended PEEC model with
magnetization currents from ferromagnetic boundaries.

Typical usage:
    from HYB import MoriscoPipeline

    pipe = MoriscoPipeline(
        cond_width=3.0e-3,
        cond_height=2.5e-3,
        stack_length=0.120,
        sigma_copper=5.8e7,
        n_poles=8,
    )
    results = pipe.run(mag_ts, conductor_currents, speed_rpm=8000)
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field

from .filament import FilamentGrid, build_filament_grid, skin_depth
from .impedance import build_impedance_matrix, build_connectivity_matrix
from .magnetization import extract_magnetization_currents, MagnetizationCurrent
from .solver import solve_peec, PEECResult
from .loss import calculate_losses, LossResult


@dataclass
class MoriscoConfig:
    """Configuration for the Morisco pipeline.

    Attributes:
        cond_width: conductor tangential width [m]
        cond_height: conductor radial height [m]
        stack_length: motor axial stack length [m]
        sigma_copper: copper conductivity at operating temperature [S/m]
        n_poles: number of poles (for f_e = n_poles/2 * n_rpm/60)
        dirichlet_radius: radius R for Dirichlet boundary condition [m].
            Morisco 2019 (Section IV): R = l (axial length).
            This is the FEA calculation domain boundary, NOT the slot wall.
            Iron wall effects enter ONLY via magnetization currents.
            If None, defaults to stack_length.
        slot_boundary_radius: DEPRECATED. Use dirichlet_radius instead.
        subdivision_ratio: filament size / skin_depth target (default 0.1)
        iron_mur_threshold: elements with μr > threshold are treated as iron
        winding_j_threshold: elements with |J| > threshold are winding [A/mm²]
    """
    cond_width: float
    cond_height: float
    stack_length: float
    sigma_copper: float = 5.8e7  # pure copper at 20°C
    n_poles: int = 8
    dirichlet_radius: float | None = None
    slot_boundary_radius: float | None = None  # deprecated, use dirichlet_radius
    subdivision_ratio: float = 0.1
    iron_mur_threshold: float = 10.0
    winding_j_threshold: float = 0.1  # A/mm²

    def get_dirichlet_radius(self) -> float:
        """Get the effective Dirichlet radius R.

        Priority: dirichlet_radius > slot_boundary_radius > stack_length.
        Morisco 2019 paper uses R = l (axial length of model).
        """
        if self.dirichlet_radius is not None:
            return self.dirichlet_radius
        if self.slot_boundary_radius is not None:
            return self.slot_boundary_radius
        return self.stack_length


@dataclass
class MoriscoStepResult:
    """Result for a single time step."""
    step_index: int
    peec_result: PEECResult
    loss_result: LossResult
    magnetization: MagnetizationCurrent | None


@dataclass
class MoriscoTimeseriesResult:
    """Full timeseries result.

    Attributes:
        step_results: list of per-step results
        average_loss: time-averaged total loss [W]
        average_k_ih: time-averaged current displacement factor
        config: pipeline configuration used
    """
    step_results: list[MoriscoStepResult] = field(default_factory=list)
    average_loss: float = 0.0
    average_k_ih: float = 1.0
    config: MoriscoConfig | None = None


class MoriscoPipeline:
    """Morisco Hybrid FEA-PEEC pipeline.

    Takes Motor-CAD FEA mesh data (from pyMCAD MagneticRegionsTimeSeries)
    and computes AC winding losses using the extended PEEC approach.
    """

    def __init__(self, **kwargs):
        """Initialize with MoriscoConfig parameters."""
        self.config = MoriscoConfig(**kwargs)

    def electrical_frequency(self, speed_rpm: float) -> float:
        """Compute electrical frequency from mechanical speed."""
        return (self.config.n_poles / 2) * speed_rpm / 60.0

    def run(
        self,
        mag_timeseries,
        conductor_currents: np.ndarray | list,
        speed_rpm: float,
        winding_reg_codes: list[int] | None = None,
        iron_reg_codes: list[int] | None = None,
        include_magnetization: bool = True,
    ) -> MoriscoTimeseriesResult:
        """Run Morisco pipeline on a full timeseries.

        Args:
            mag_timeseries: pyMCAD MagneticRegionsTimeSeries object
                (has .by_step dict, .steps list, .meta)
            conductor_currents: (n_conductors,) or (n_steps, n_conductors)
                complex conductor currents [A]. If 1D, same current used for all steps.
            speed_rpm: mechanical speed [RPM]
            winding_reg_codes: list of region codes for winding conductors.
                If None, auto-detect from elements with |J| > threshold.
            iron_reg_codes: list of region codes for ferromagnetic regions.
                If None, auto-detect from elements with μr > threshold.
            include_magnetization: whether to include rotor/stator magnetization effect.

        Returns:
            MoriscoTimeseriesResult
        """
        freq = self.electrical_frequency(speed_rpm)
        steps = list(mag_timeseries.steps)

        conductor_currents = np.asarray(conductor_currents, dtype=complex)
        if conductor_currents.ndim == 1:
            # Same current for all steps
            conductor_currents = np.tile(conductor_currents, (len(steps), 1))

        # Get reference step for geometry extraction
        ref_step = steps[0]
        ref_mr = mag_timeseries.by_step[ref_step]

        # Extract conductor centers from winding region elements
        cond_centers = self._extract_conductor_centers(
            ref_mr, winding_reg_codes
        )
        n_cond = len(cond_centers)

        if n_cond == 0:
            raise ValueError(
                "No winding conductors found. Check winding_reg_codes or J threshold."
            )

        # Build filament grid
        grid = build_filament_grid(
            conductor_centers=cond_centers,
            cond_width=self.config.cond_width,
            cond_height=self.config.cond_height,
            length=self.config.stack_length,
            frequency=freq,
            sigma=self.config.sigma_copper,
            subdivision_ratio=self.config.subdivision_ratio,
        )

        # Dirichlet radius R (Morisco 2019: R = l = axial length)
        # This is the calculation domain boundary, NOT the slot wall.
        # Iron effects enter only via magnetization currents.
        slot_r = self.config.get_dirichlet_radius()

        # Process each time step
        step_results = []
        for si, step in enumerate(steps):
            mr = mag_timeseries.by_step[step]
            I_step = conductor_currents[si, :n_cond]

            # Extract magnetization if requested
            mag_current = None
            if include_magnetization:
                mag_current = self._extract_magnetization(
                    mr, iron_reg_codes
                )

            # Solve PEEC
            peec_result = solve_peec(
                grid=grid,
                conductor_currents=I_step,
                frequency=freq,
                sigma=self.config.sigma_copper,
                slot_boundary_radius=slot_r,
                magnetization_currents=mag_current,
            )

            # Calculate losses
            loss_result = calculate_losses(peec_result, self.config.sigma_copper)

            step_results.append(MoriscoStepResult(
                step_index=step,
                peec_result=peec_result,
                loss_result=loss_result,
                magnetization=mag_current,
            ))

        # Time-average
        avg_loss = np.mean([sr.loss_result.total_loss for sr in step_results])
        avg_k_ih = np.mean([sr.loss_result.k_ih for sr in step_results])

        return MoriscoTimeseriesResult(
            step_results=step_results,
            average_loss=avg_loss,
            average_k_ih=avg_k_ih,
            config=self.config,
        )

    def run_single_step(
        self,
        mag_regions,
        conductor_currents: np.ndarray,
        speed_rpm: float,
        winding_reg_codes: list[int] | None = None,
        iron_reg_codes: list[int] | None = None,
        include_magnetization: bool = True,
    ) -> MoriscoStepResult:
        """Run Morisco pipeline on a single MagneticRegions snapshot.

        Args:
            mag_regions: pyMCAD MagneticRegions object (single step)
            conductor_currents: (n_conductors,) complex currents [A]
            speed_rpm: mechanical speed [RPM]

        Returns:
            MoriscoStepResult
        """
        freq = self.electrical_frequency(speed_rpm)
        conductor_currents = np.asarray(conductor_currents, dtype=complex)

        cond_centers = self._extract_conductor_centers(
            mag_regions, winding_reg_codes
        )
        n_cond = len(cond_centers)

        grid = build_filament_grid(
            conductor_centers=cond_centers,
            cond_width=self.config.cond_width,
            cond_height=self.config.cond_height,
            length=self.config.stack_length,
            frequency=freq,
            sigma=self.config.sigma_copper,
            subdivision_ratio=self.config.subdivision_ratio,
        )

        slot_r = self.config.get_dirichlet_radius()

        mag_current = None
        if include_magnetization:
            mag_current = self._extract_magnetization(
                mag_regions, iron_reg_codes
            )

        peec_result = solve_peec(
            grid=grid,
            conductor_currents=conductor_currents[:n_cond],
            frequency=freq,
            sigma=self.config.sigma_copper,
            slot_boundary_radius=slot_r,
            magnetization_currents=mag_current,
        )

        loss_result = calculate_losses(peec_result, self.config.sigma_copper)

        return MoriscoStepResult(
            step_index=0,
            peec_result=peec_result,
            loss_result=loss_result,
            magnetization=mag_current,
        )

    def _extract_conductor_centers(
        self,
        mag_regions,
        winding_reg_codes: list[int] | None,
    ) -> np.ndarray:
        """Extract conductor center positions from FEA mesh.

        Each unique reg_code in the winding region represents one conductor.
        The center is the centroid of all elements with that reg_code.
        """
        node_xy = mag_regions.node_xy
        regions = mag_regions._regions

        # Identify winding regions
        if winding_reg_codes is not None:
            winding_indices = [rc - 1 for rc in winding_reg_codes if 0 < rc <= len(regions)]
        else:
            # Auto-detect: regions where elements have |J| > threshold
            winding_indices = []
            threshold = self.config.winding_j_threshold
            for ri, region in enumerate(regions):
                elements = getattr(region, "elements", []) or []
                if not elements:
                    continue
                avg_j = np.mean([abs(getattr(e, "j", 0) or 0) for e in elements])
                if avg_j > threshold:
                    winding_indices.append(ri)

        # Compute centroid per winding region (each region = one conductor)
        centers = []
        for ri in winding_indices:
            region = regions[ri]
            elements = getattr(region, "elements", []) or []
            if not elements or not node_xy:
                continue
            # Compute element centroids
            cx_list, cy_list = [], []
            for el in elements:
                n1 = getattr(el, "node_1")
                n2 = getattr(el, "node_2")
                n3 = getattr(el, "node_3")
                if n1 in node_xy and n2 in node_xy and n3 in node_xy:
                    pts = [node_xy[n1], node_xy[n2], node_xy[n3]]
                    cx_list.append(np.mean([p[0] for p in pts]))
                    cy_list.append(np.mean([p[1] for p in pts]))
            if cx_list:
                centers.append([np.mean(cx_list), np.mean(cy_list)])

        return np.array(centers) if centers else np.zeros((0, 2))

    def _extract_magnetization(
        self,
        mag_regions,
        iron_reg_codes: list[int] | None,
    ) -> MagnetizationCurrent:
        """Extract magnetization currents from iron regions.

        Uses the FEA H-field and B-field data to compute M, then
        finds boundary edges and computes equivalent line currents.
        """
        node_xy_dict = mag_regions.node_xy
        regions = mag_regions._regions

        if not node_xy_dict:
            return MagnetizationCurrent(
                positions=np.zeros((0, 2)),
                currents=np.zeros(0, dtype=complex),
                edge_normals=np.zeros((0, 2)),
            )

        # Build node array and element arrays
        # Collect all elements across regions
        all_elements = []
        all_reg_indices = []
        for ri, region in enumerate(regions):
            elements = getattr(region, "elements", []) or []
            for el in elements:
                all_elements.append(el)
                all_reg_indices.append(ri)

        if not all_elements:
            return MagnetizationCurrent(
                positions=np.zeros((0, 2)),
                currents=np.zeros(0, dtype=complex),
                edge_normals=np.zeros((0, 2)),
            )

        # Build node index mapping
        unique_nodes = sorted(node_xy_dict.keys())
        node_id_map = {nid: idx for idx, nid in enumerate(unique_nodes)}
        node_xy = np.array([node_xy_dict[nid] for nid in unique_nodes])

        # Build triangles and field arrays
        n_elem = len(all_elements)
        triangles = np.zeros((n_elem, 3), dtype=int)
        bx = np.zeros(n_elem)
        by = np.zeros(n_elem)
        hx = np.zeros(n_elem)
        hy = np.zeros(n_elem)
        mur = np.ones(n_elem)

        for ei, el in enumerate(all_elements):
            n1 = getattr(el, "node_1")
            n2 = getattr(el, "node_2")
            n3 = getattr(el, "node_3")
            triangles[ei] = [
                node_id_map.get(n1, 0),
                node_id_map.get(n2, 0),
                node_id_map.get(n3, 0),
            ]
            bx[ei] = getattr(el, "bx", 0) or 0
            by[ei] = getattr(el, "by", 0) or 0
            hx[ei] = getattr(el, "hx", 0) or 0
            hy[ei] = getattr(el, "hy", 0) or 0
            mur[ei] = getattr(el, "mur", 1) or 1

        # Identify iron elements
        if iron_reg_codes is not None:
            iron_mask = np.array([
                (all_reg_indices[ei] + 1) in iron_reg_codes
                for ei in range(n_elem)
            ])
        else:
            # Auto-detect: μr > threshold
            iron_mask = mur > self.config.iron_mur_threshold

        return extract_magnetization_currents(
            node_xy=node_xy,
            triangles=triangles,
            bx=bx,
            by=by,
            hx=hx,
            hy=hy,
            mur=mur,
            iron_mask=iron_mask,
            axial_length=self.config.stack_length,
            region_label="iron_combined",
        )
