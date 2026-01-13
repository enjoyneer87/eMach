"""Compatibility shim.

Implementation moved to `tools.motorCAD.pyMCAD.stress`.
"""

from tools.motorCAD.pyMCAD.stress import *  # noqa: F401,F403


def check_youngs_modulus(
    non_linear_strain: Sequence[float],
    non_linear_stress: Sequence[float],
    youngs_modulus_mpa: float,
    *,
    rel_tol: float = 0.01,
    abs_tol: float = 0.1,
) -> None:
    """Validate that the initial slope of non-linear stress/strain matches Young's modulus.

    Parameters
    ----------
    non_linear_strain, non_linear_stress:
        Stress-strain curve samples. Stress is in MPa, strain is dimensionless.
    youngs_modulus_mpa:
        Young's modulus in MPa.

    Raises
    ------
    ValueError
        If the initial slope is not consistent with the Young's modulus.
    """

    if len(non_linear_strain) < 2 or len(non_linear_stress) < 2:
        raise ValueError("Non-linear stress/strain data must have at least 2 points")

    ds = float(non_linear_stress[1]) - float(non_linear_stress[0])
    de = float(non_linear_strain[1]) - float(non_linear_strain[0])
    if math.isclose(de, 0.0):
        raise ValueError("Non-linear strain data has zero delta at index 0->1")

    initial_youngs = ds / de
    if not math.isclose(initial_youngs, float(youngs_modulus_mpa), rel_tol=rel_tol, abs_tol=abs_tol):
        raise ValueError(
            "Young's modulus and initial slope of non-linear data are different; "
            f"initial slope is {initial_youngs} MPa, Young's modulus is {youngs_modulus_mpa} MPa"
        )


def find_divergence_point(
    non_linear_strain: Sequence[float],
    non_linear_stress: Sequence[float],
    youngs_modulus_mpa: float,
    *,
    rel_tol: float = 1e-4,
) -> float:
    """Return last stress point still on the initial linear (elastic) part of the curve.

    This mirrors the notebook logic: it compares stress/strain ratio against the
    supplied Young's modulus and returns the previous stress when it diverges.

    Returns
    -------
    float
        Stress [MPa] at the last linear sample.
    """

    for i in range(1, len(non_linear_stress)):
        strain_i = float(non_linear_strain[i])
        if math.isclose(strain_i, 0.0):
            continue
        if not math.isclose(float(non_linear_stress[i]) / strain_i, float(youngs_modulus_mpa), rel_tol=rel_tol):
            return float(non_linear_stress[i - 1])

    return float(non_linear_stress[-1])


@dataclass
class StressElement:
    """Data for a 1st order triangular element and its associated stress/strain."""

    tri_index: int
    node_1: int
    node_2: int
    node_3: int
    x: float
    y: float
    s_x: float
    s_y: float
    t_xy: float
    sp_1: float
    sp_2: float
    svm: float
    u_x: float
    u_y: float

    stress_nonlinear_neuber: float = 0.0
    strain_nonlinear_neuber: float = 0.0
    strain_plastic_neuber: float = 0.0

    stress_nonlinear_glinka: float = 0.0
    strain_nonlinear_glinka: float = 0.0
    strain_plastic_glinka: float = 0.0

    def apply_neuber_correction(
        self,
        youngs_modulus_mpa: float,
        non_linear_strain: np.ndarray,
        non_linear_stress: np.ndarray,
    ) -> None:
        """Update Neuber correction estimates from Von Mises stress."""

        elastic_stress = float(self.svm)
        elastic_strain = elastic_stress / float(youngs_modulus_mpa)
        elastic_product = elastic_stress * elastic_strain

        check_youngs_modulus(non_linear_strain, non_linear_stress, youngs_modulus_mpa)

        if elastic_stress < find_divergence_point(non_linear_strain, non_linear_stress, youngs_modulus_mpa):
            self.strain_nonlinear_neuber = elastic_strain
            self.stress_nonlinear_neuber = elastic_stress
            self.strain_plastic_neuber = 0.0
            return

        nl_product = non_linear_stress * non_linear_strain
        if elastic_product > float(np.max(nl_product)):
            raise ValueError(
                "Input too large (elastic stress*strain product > maximum in non-linear data). "
                f"Elastic stress is {elastic_stress}, elastic product is {elastic_product}, "
                f"maximum plastic product is {float(np.max(nl_product))}"
            )

        eq_strain = float(np.interp(elastic_product, nl_product, non_linear_strain))
        eq_stress = float(np.interp(eq_strain, non_linear_strain, non_linear_stress))

        plastic_strain = eq_strain - elastic_strain

        self.strain_nonlinear_neuber = eq_strain
        self.stress_nonlinear_neuber = eq_stress
        self.strain_plastic_neuber = plastic_strain

    def apply_glinka_correction(
        self,
        youngs_modulus_mpa: float,
        non_linear_strain: np.ndarray,
        non_linear_stress: np.ndarray,
    ) -> None:
        """Update Glinka correction estimates from Von Mises stress."""

        elastic_stress = float(self.svm)
        elastic_strain = elastic_stress / float(youngs_modulus_mpa)
        elastic_integral = 0.5 * elastic_strain * elastic_stress

        check_youngs_modulus(non_linear_strain, non_linear_stress, youngs_modulus_mpa)

        if elastic_stress < find_divergence_point(non_linear_strain, non_linear_stress, youngs_modulus_mpa):
            self.strain_nonlinear_glinka = elastic_strain
            self.stress_nonlinear_glinka = elastic_stress
            self.strain_plastic_glinka = 0.0
            return

        nl_integral = np.zeros(len(non_linear_stress), dtype=float)
        for i in range(1, len(non_linear_stress)):
            nl_integral[i] = (
                nl_integral[i - 1]
                + (non_linear_strain[i] - non_linear_strain[i - 1])
                * (non_linear_stress[i] + non_linear_stress[i - 1])
                / 2.0
            )

        if elastic_integral > float(np.max(nl_integral)):
            raise ValueError(
                "Input too large (elastic stress-strain integral > maximum in non-linear data). "
                f"Elastic stress is {elastic_stress}, elastic integral is {elastic_integral}, "
                f"maximum plastic integral is {float(np.max(nl_integral))}"
            )

        eq_strain = float(np.interp(elastic_integral, nl_integral, non_linear_strain))
        eq_stress = float(np.interp(eq_strain, non_linear_strain, non_linear_stress))

        plastic_strain = eq_strain - elastic_strain

        self.strain_nonlinear_glinka = eq_strain
        self.stress_nonlinear_glinka = eq_stress
        self.strain_plastic_glinka = plastic_strain


class StressRegion:
    """Stressed region: element list + material properties."""

    def __init__(self):
        self.region_name = ""
        self.reg_code = 0
        self.youngs_modulus = 0.0
        self.poissons_ratio = 0.0
        self.elements: List[StressElement] = []

    def add_element(
        self,
        tri_index: int,
        node_1: int,
        node_2: int,
        node_3: int,
        x: float,
        y: float,
        s_x: float,
        s_y: float,
        t_xy: float,
        sp_1: float,
        sp_2: float,
        svm: float,
        u_x: float,
        u_y: float,
    ) -> None:
        self.elements.append(
            StressElement(
                tri_index=int(tri_index),
                node_1=int(node_1),
                node_2=int(node_2),
                node_3=int(node_3),
                x=float(x),
                y=float(y),
                s_x=float(s_x),
                s_y=float(s_y),
                t_xy=float(t_xy),
                sp_1=float(sp_1),
                sp_2=float(sp_2),
                svm=float(svm),
                u_x=float(u_x),
                u_y=float(u_y),
            )
        )

    def get_number_elements(self) -> int:
        return len(self.elements)

    def get_sp1(self) -> List[float]:
        return [el.sp_1 for el in self.elements]

    def get_sp2(self) -> List[float]:
        return [el.sp_2 for el in self.elements]

    def get_svm(self) -> List[float]:
        return [el.svm for el in self.elements]

    def get_stress_nonlinear_neuber(self) -> List[float]:
        return [el.stress_nonlinear_neuber for el in self.elements]

    def get_strain_nonlinear_neuber(self) -> List[float]:
        return [el.strain_nonlinear_neuber for el in self.elements]

    def get_strain_plastic_neuber(self) -> List[float]:
        return [el.strain_plastic_neuber for el in self.elements]

    def get_stress_nonlinear_glinka(self) -> List[float]:
        return [el.stress_nonlinear_glinka for el in self.elements]

    def get_strain_nonlinear_glinka(self) -> List[float]:
        return [el.strain_nonlinear_glinka for el in self.elements]

    def get_strain_plastic_glinka(self) -> List[float]:
        return [el.strain_plastic_glinka for el in self.elements]

    def get_x(self) -> List[float]:
        return [el.x for el in self.elements]

    def get_y(self) -> List[float]:
        return [el.y for el in self.elements]

    def apply_corrections(self, non_linear_strain: np.ndarray, non_linear_stress: np.ndarray) -> None:
        for el in self.elements:
            el.apply_neuber_correction(self.youngs_modulus, non_linear_strain, non_linear_stress)
            el.apply_glinka_correction(self.youngs_modulus, non_linear_strain, non_linear_stress)


class StressRegions:
    """Collection of StressRegion objects indexed by region code-1."""

    def __init__(self):
        self._regions: List[StressRegion] = []

    def __len__(self):
        return len(self._regions)

    def __getitem__(self, region_number: int) -> StressRegion:
        return self._regions[region_number]

    def __setitem__(self, region_number: int, data: StressRegion) -> None:
        self._regions[region_number] = data

    def add_region(self) -> None:
        self._regions.append(StressRegion())

    def ensure_region(self, reg_code: int) -> None:
        while reg_code > len(self._regions):
            self.add_region()


def _is_table_header(line: str, table_name: str) -> bool:
    tokens = line.strip().split()
    return len(tokens) >= 3 and tokens[1].isdigit() and tokens[2].strip() == table_name


def _skip_header_lines(in_file, n: int) -> None:
    for _ in range(int(n)):
        in_file.readline()


def _read_until_table_header(in_file, table_name: str) -> Optional[str]:
    while True:
        line = in_file.readline()
        if not line:
            return None
        if _is_table_header(line, table_name):
            return line


def _parse_first_block_stress_file(filename: pathlib.Path) -> StressRegions:
    stress_regions = StressRegions()
    filename = pathlib.Path(filename)

    with open(filename, "r") as in_file:
        elements_header = _read_until_table_header(in_file, "ElementsTable")
        if elements_header is None:
            raise ValueError(f"ElementsTable not found in file: {filename}")

        number_of_elements = int(elements_header.strip().split()[1])
        _skip_header_lines(in_file, 4)

        for _ in range(number_of_elements):
            row = in_file.readline().split(sep=",")
            if len(row) < 15:
                continue

            try:
                reg_code = int(row[4])
            except ValueError:
                continue

            if reg_code <= 0:
                continue

            stress_regions.ensure_region(reg_code)
            stress_regions[reg_code - 1].add_element(
                tri_index=int(row[0]),
                node_1=int(row[1]),
                node_2=int(row[2]),
                node_3=int(row[3]),
                x=float(row[5]),
                y=float(row[6]),
                s_x=float(row[7]),
                s_y=float(row[8]),
                t_xy=float(row[9]),
                sp_1=float(row[10]),
                sp_2=float(row[11]),
                svm=float(row[12]),
                u_x=float(row[13]),
                u_y=float(row[14]),
            )

        nodes_header = _read_until_table_header(in_file, "NodesTable")
        if nodes_header is not None:
            number_of_nodes = int(nodes_header.strip().split()[1])
            _skip_header_lines(in_file, 4)
            for _ in range(number_of_nodes):
                in_file.readline()

        regions_header = _read_until_table_header(in_file, "RegionsTable")
        if regions_header is None:
            return stress_regions

        number_of_regions = int(regions_header.strip().split()[1])
        _skip_header_lines(in_file, 4)

        if number_of_regions > len(stress_regions):
            raise ValueError("RegionsTable and element region codes do not match")

        for _ in range(number_of_regions):
            row = in_file.readline().split(sep=",")
            if len(row) < 4:
                continue
            try:
                reg_code = int(row[0])
            except ValueError:
                continue
            if reg_code <= 0 or reg_code > len(stress_regions):
                raise ValueError("RegionsTable and element region codes do not match")

            stress_regions[reg_code - 1].reg_code = reg_code
            stress_regions[reg_code - 1].youngs_modulus = float(row[1])
            stress_regions[reg_code - 1].poissons_ratio = float(row[2])
            stress_regions[reg_code - 1].region_name = row[-1].strip()

    return stress_regions


def get_stress_data(mc, *, clean_up: bool = True) -> StressRegions:
    """Export mechanical stress data from Motor-CAD and parse into StressRegions."""

    temp_filename = mcad_make_temp_txt_path(mc)

    mc.save_fea_data(
        str(temp_filename),
        0,
        0,
        "RegCode,X,Y,Sx,Sy,Txy,Sp1,Sp2,SVM,Ux,Uy",
        "",
        ",",
    )

    stress_regions = _parse_first_block_stress_file(temp_filename)

    if clean_up:
        try:
            temp_filename.unlink()
        except FileNotFoundError:
            pass
    else:
        print(f"Temporary file not deleted: {temp_filename}")

    return stress_regions


def get_stress_data_from_file(filename: str | pathlib.Path, *, clean_up: bool = False) -> StressRegions:
    filename_p = pathlib.Path(filename)
    regions = _parse_first_block_stress_file(filename_p)
    if clean_up:
        try:
            filename_p.unlink()
        except FileNotFoundError:
            pass
    return regions


def temperature_adjusted_curve(
    strain: np.ndarray,
    stress: np.ndarray,
    base_youngs_mpa: float,
    delta_t_c: float,
    *,
    youngs_temp_coeff: float = -3.5e-4,
    plastic_temp_coeff: float = -8e-4,
) -> Tuple[np.ndarray, float]:
    """Return temperature-adjusted stress curve and scaled Young's modulus.

    Parameters
    ----------
    strain, stress:
        Base curve (stress in MPa).
    base_youngs_mpa:
        Young's modulus at reference temperature in MPa.
    delta_t_c:
        Temperature rise relative to reference in degC.
    youngs_temp_coeff:
        Fractional change in Young's modulus per degC.
    plastic_temp_coeff:
        Fractional change applied to the plastic portion per degC.
    """

    adjusted = np.asarray(stress, dtype=float).copy()

    youngs_scaled = float(base_youngs_mpa) * (1.0 + float(youngs_temp_coeff) * float(delta_t_c))

    linear_limit = find_divergence_point(strain, stress, base_youngs_mpa)
    linear_mask = np.asarray(stress, dtype=float) <= float(linear_limit)

    adjusted[linear_mask] *= youngs_scaled / float(base_youngs_mpa)
    adjusted[~linear_mask] *= 1.0 + float(plastic_temp_coeff) * float(delta_t_c)

    return adjusted, youngs_scaled
