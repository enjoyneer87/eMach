from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Sequence, Tuple

import matplotlib
import matplotlib.pyplot as plt

from .magnetic import MagneticRegions, mcad_make_temp_txt_path


try:
    import ipywidgets as widgets
    from IPython.display import display
except Exception:
    widgets = None
    display = None


@dataclass(frozen=True)
class ElementRecord:
    tri_index: int
    node_1: int
    node_2: int
    node_3: int
    reg_code: int


@dataclass
class ElementMesh:
    """Mesh snapshot for element-wise post-processing.

    This is intentionally decoupled from time/step. It only stores geometry/topology
    (node coordinates + element connectivity + region codes).
    """

    node_xy: Dict[int, Tuple[float, float]]
    elements: Tuple[ElementRecord, ...]
    region_name_by_code: Dict[int, str] = field(default_factory=dict)

    @classmethod
    def from_magnetic_regions(cls, mr: MagneticRegions) -> "ElementMesh":
        node_xy = dict(getattr(mr, "node_xy", {}) or {})

        region_name_by_code: Dict[int, str] = {}

        elements: list[ElementRecord] = []
        regions = getattr(mr, "_regions", [])
        for idx, region in enumerate(regions):
            code = int(getattr(region, "reg_code", 0) or (idx + 1))
            name = (getattr(region, "region_name", "") or "").strip()
            if code > 0 and name:
                region_name_by_code[code] = name
            for el in getattr(region, "elements", []) or []:
                elements.append(
                    ElementRecord(
                        tri_index=int(getattr(el, "tri_index")),
                        node_1=int(getattr(el, "node_1")),
                        node_2=int(getattr(el, "node_2")),
                        node_3=int(getattr(el, "node_3")),
                        reg_code=int(getattr(el, "reg_code")),
                    )
                )

                return cls(node_xy=node_xy, elements=tuple(elements), region_name_by_code=region_name_by_code)

    def element_centroid_xy(self, element: ElementRecord) -> Optional[Tuple[float, float]]:
        n1 = self.node_xy.get(element.node_1)
        n2 = self.node_xy.get(element.node_2)
        n3 = self.node_xy.get(element.node_3)
        if n1 is None or n2 is None or n3 is None:
            return None
        x = (n1[0] + n2[0] + n3[0]) / 3.0
        y = (n1[1] + n2[1] + n3[1]) / 3.0
        return x, y

    def iter_elements(self, reg_code: Optional[int] = None) -> Iterable[ElementRecord]:
        if reg_code is None:
            return iter(self.elements)
        return (el for el in self.elements if int(el.reg_code) == int(reg_code))


@dataclass
class ElementScalarField:
    """Element-wise scalar field defined on an ElementMesh.

    `values_by_tri` maps tri_index -> scalar value (e.g., loss density [W/kg]).
    """

    mesh: ElementMesh
    values_by_tri: Dict[int, float]
    name: str = "loss"
    unit: str = "W/kg"

    def to_w_per_m3(self, rho_kg_per_m3: float, *, unit: str = "W/m^3") -> "ElementScalarField":
        """Convert from W/kg to W/m^3 using density rho [kg/m^3].

        For future use when you want volumetric loss density.
        """

        rho = float(rho_kg_per_m3)
        return ElementScalarField(
            mesh=self.mesh,
            values_by_tri={k: float(v) * rho for k, v in self.values_by_tri.items()},
            name=self.name,
            unit=unit,
        )

    def plot(
        self,
        reg_code: Optional[int] = None,
        *,
        cmap: str = "jet",
        s: float = 2,
        ax=None,
        show: bool = True,
        mesh: bool = False,
        title: Optional[str] = None,
        vmin=None,
        vmax=None,
    ):
        """Scatter plot element-wise scalar field.

        If node coordinates are available, plots element centroid (x,y) colored by value.
        Otherwise falls back to tri_index vs value.
        """

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        xs = []
        ys = []
        cs = []
        used_xy = False

        for el in self.mesh.iter_elements(reg_code=reg_code):
            v = self.values_by_tri.get(int(el.tri_index))
            if v is None:
                continue

            c_xy = self.mesh.element_centroid_xy(el)
            if c_xy is not None:
                xs.append(c_xy[0])
                ys.append(c_xy[1])
                cs.append(float(v))
                used_xy = True
            else:
                xs.append(int(el.tri_index))
                ys.append(float(v))
                cs.append(float(v))

        if not xs:
            ax.set_title("No data to plot")
            if show:
                plt.show()
            return ax

        sc = ax.scatter(xs, ys, c=cs, cmap=cmap, s=float(s), vmin=vmin, vmax=vmax)
        cb = plt.colorbar(sc, ax=ax)
        cb.set_label(f"{self.name} [{self.unit}]")

        if title is None:
            title = f"{self.name} [{self.unit}]"
            if reg_code is not None:
                title += f" (reg_code={reg_code})"
        ax.set_title(title)

        if used_xy:
            ax.set_xlabel("x [mm]")
            ax.set_ylabel("y [mm]")
            ax.set_aspect("equal")
        else:
            ax.set_xlabel("TriIndex")
            ax.set_ylabel(f"{self.name} [{self.unit}]")

        if show:
            plt.show()

        return ax


def _is_table_header(line: str, table_name: str) -> bool:
    tokens = line.strip().split()
    return len(tokens) >= 3 and tokens[1].isdigit() and tokens[2].strip() == table_name


def _scan_to_table(in_file, table_name: str):
    while True:
        line = in_file.readline()
        if not line:
            return None
        if _is_table_header(line, table_name):
            return line


def _skip_header_lines(in_file, n: int = 4):
    for _ in range(int(n)):
        in_file.readline()


def _read_table_column_names(header_lines: Sequence[str], sep: str = ",") -> Optional[list[str]]:
    """Try to extract CSV column names from Motor-CAD table header lines."""

    for line in header_lines:
        if sep not in line:
            continue
        cols = [c.strip() for c in line.strip().split(sep) if c.strip()]
        if cols:
            return cols
    return None


_MCAD_STEP_HEADER_RE = re.compile(
    r"^\s*(?P<prefix>\d+)\s+Solution\s+(?P<solution>\d+)"
    r"(?:\s+Time\s+index\s+(?P<time_index>-?\d+)\s+Time\s+(?P<time_s>[-+0-9.Ee]+)\s+\[s\])?"
    r"\s+Rotate\s+Step\s+(?P<rotate_step>[-+0-9.Ee]+)\s*$",
    re.IGNORECASE,
)


def _parse_first_block_loss_file(
    filename: pathlib.Path,
    *,
    sep: str = ",",
    unit: str = "W/kg",
) -> Dict[str, ElementScalarField]:
    """Parse an element-wise loss export (single block) into scalar fields.

    Expected format is a Motor-CAD FEA export containing an ElementsTable
    with at least TriIndex/Node1/Node2/Node3/RegCode and one or more loss columns.

    Returns
    -------
    dict[str, ElementScalarField]
        Keys are column names (e.g. 'Pt', 'Phys', 'Pj', 'Peddy').
    """

    filename = pathlib.Path(filename)

    with open(filename, "r") as in_file:
        # If this is a multi-block file, it may start with a step header.
        # For a single-block export, ElementsTable may appear on the first line.
        pos0 = in_file.tell()
        first_line = in_file.readline()
        if first_line and _is_table_header(first_line, "ElementsTable"):
            elements_header = first_line
        else:
            in_file.seek(pos0)
            elements_header = _scan_to_table(in_file, "ElementsTable")
        if elements_header is None:
            try:
                in_file.seek(0)
                preview = "".join([in_file.readline() for _ in range(30)])
            except Exception:
                preview = ""
            msg = f"ElementsTable not found in file: {filename}"
            if preview.strip():
                msg += "\n--- file preview (first ~30 lines) ---\n" + preview
            raise ValueError(msg)

        n_elements = int(elements_header.strip().split()[1])

        header_lines = [in_file.readline() for _ in range(4)]
        columns = _read_table_column_names(header_lines, sep=sep)

        # Fall back to the common Motor-CAD layout if column names aren't in the header.
        if columns is None:
            columns = [
                "TriIndex",
                "Node1",
                "Node2",
                "Node3",
                "RegCode",
            ]

        # Prepare mesh snapshot
        mr = MagneticRegions()

        # Prepare value maps for any loss-like columns we see
        known_loss_names = {"pt", "phys", "pj", "peddy", "p", "ploss", "ploss_total"}
        loss_cols = [c for c in columns if c.strip().lower() in known_loss_names or c.strip().lower().startswith("p")]
        # We don't want to treat connectivity columns as loss columns
        connectivity = {"triindex", "node1", "node2", "node3", "regcode"}
        loss_cols = [c for c in loss_cols if c.strip().lower() not in connectivity]
        values_by_name: Dict[str, Dict[int, float]] = {c: {} for c in loss_cols}

        # Build column index map when we have a proper header
        col_index = {c: i for i, c in enumerate(columns)}
        # If we didn't get a header, assume standard layout, and treat remaining columns generically
        has_full_header = ("TriIndex" in col_index and "RegCode" in col_index)

        for _ in range(n_elements):
            row = in_file.readline().split(sep=sep)
            if not row or len(row) < 5:
                continue

            # Connectivity
            try:
                tri_index = int(row[col_index.get("TriIndex", 0)])
                node_1 = int(row[col_index.get("Node1", 1)])
                node_2 = int(row[col_index.get("Node2", 2)])
                node_3 = int(row[col_index.get("Node3", 3)])
                reg_code = int(row[col_index.get("RegCode", 4)])
            except Exception:
                # fallback to positional
                try:
                    tri_index = int(row[0])
                    node_1 = int(row[1])
                    node_2 = int(row[2])
                    node_3 = int(row[3])
                    reg_code = int(row[4])
                except Exception:
                    continue

            mr.ensure_region(reg_code)
            mr[reg_code - 1].add_element(
                tri_index=tri_index,
                node_1=node_1,
                node_2=node_2,
                node_3=node_3,
                reg_code=reg_code,
                # loss exports might not contain Bx/By; keep them empty
                b=0.0,
                a=0.0,
                j=0.0,
            )

            # Values
            if has_full_header and loss_cols:
                for name in loss_cols:
                    idx = col_index.get(name)
                    if idx is None or idx >= len(row):
                        continue
                    try:
                        values_by_name[name][tri_index] = float(row[idx])
                    except ValueError:
                        continue
            else:
                # If we don't know the header, assume any extra columns after RegCode are loss-like
                for i in range(5, len(row)):
                    try:
                        v = float(row[i])
                    except ValueError:
                        continue
                    values_by_name.setdefault(f"P{i-4}", {})[tri_index] = v

        # NodesTable for coordinates
        node_xy: Dict[int, Tuple[float, float]] = {}
        nodes_header = _scan_to_table(in_file, "NodesTable")
        if nodes_header is not None:
            n_nodes = int(nodes_header.strip().split()[1])
            _skip_header_lines(in_file, 4)
            for _ in range(n_nodes):
                row = in_file.readline().split(sep=sep)
                try:
                    node_idx = int(row[0])
                    x_mm = float(row[1])
                    y_mm = float(row[2])
                    node_xy[node_idx] = (x_mm, y_mm)
                except Exception:
                    pass

        mr.set_node_xy(node_xy)

        # RegionsTable: map reg_code -> region_name if present in the export
        regions_header = _scan_to_table(in_file, "RegionsTable")
        if regions_header is not None:
            try:
                n_regions = int(regions_header.strip().split()[1])
            except Exception:
                n_regions = 0
            _skip_header_lines(in_file, 4)
            for _ in range(int(n_regions)):
                row = in_file.readline().split(sep=sep)
                try:
                    reg_code = int(row[0])
                except Exception:
                    continue
                if 1 <= reg_code <= len(mr):
                    mr[reg_code - 1].reg_code = reg_code
                    mr[reg_code - 1].region_name = row[-1].strip()

        mesh = ElementMesh.from_magnetic_regions(mr)

        fields: Dict[str, ElementScalarField] = {}
        for name, values in values_by_name.items():
            if not values:
                continue
            fields[name] = ElementScalarField(mesh=mesh, values_by_tri=values, name=name, unit=unit)

        if not fields:
            raise ValueError(
                "No loss columns were parsed from ElementsTable. "
                "Check the export column list (e.g. 'RegCode,Pt,Phys,Pj,Peddy') and file format."
            )

        return fields


def get_element_loss_fields(
    mc,
    *,
    filename: Optional[str | pathlib.Path] = None,
    step: Optional[int] = None,
    first_step: int = 1,
    final_step: int = 1,
    columns: Sequence[str] = ("Pt", "Phys", "Pj", "Peddy"),
    unit: str = "W/kg",
    clean_up: bool = True,
    sep: str = ",",
) -> Dict[str, ElementScalarField]:
    """Export element-wise losses from Motor-CAD and parse into scalar fields.

    Notes
    -----
    - Motor-CAD exports Tri/Node connectivity automatically; we request loss columns.
    - If you only want a single snapshot (recommended for loss), pass `step=...`.
    """

    if step is not None:
        first_step = int(step)
        final_step = int(step)

    if filename is None:
        export_path = mcad_make_temp_txt_path(mc)
        is_temp = True
    else:
        export_path = pathlib.Path(filename)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        if export_path.suffix.lower() != ".txt":
            export_path = export_path.with_suffix(".txt")
        is_temp = False

    col_spec = "RegCode," + ",".join(columns)
    mc.save_fea_data(str(export_path), int(first_step), int(final_step), col_spec, "", sep)

    fields = _parse_first_block_loss_file(export_path, sep=sep, unit=unit)

    if clean_up and is_temp:
        try:
            export_path.unlink()
        except FileNotFoundError:
            pass

    return fields


def get_element_loss_fields_from_file(
    filename,
    *,
    unit: str = "W/kg",
    clean_up: bool = False,
    sep: str = ",",
) -> Dict[str, ElementScalarField]:
    filename = pathlib.Path(filename)
    fields = _parse_first_block_loss_file(filename, sep=sep, unit=unit)
    if clean_up:
        try:
            filename.unlink()
        except FileNotFoundError:
            pass
    return fields


def interactive_loss_fields_plot(
    fields: Dict[str, ElementScalarField],
    *,
    initial_name: Optional[str] = None,
    initial_reg_code: Optional[int] = None,
    s: float = 2,
    cmap: str = "jet",
):
    """Interactive plot for multiple loss components (dropdown + reg_code + size)."""

    if widgets is None or display is None:
        raise RuntimeError("ipywidgets is required for interactive plotting")
    if not fields:
        raise ValueError("fields is empty")

    names = list(fields.keys())
    if initial_name is None:
        initial_name = names[0]
    if initial_name not in fields:
        initial_name = names[0]

    name_dd = widgets.Dropdown(options=names, value=initial_name, description="loss")
    # Try to expose region names (if present in export) via dropdown.
    sample_field = fields[initial_name]
    codes = sorted({int(el.reg_code) for el in sample_field.mesh.elements if int(el.reg_code) > 0})
    options = [("all", None)]
    for code in codes:
        name = (sample_field.mesh.region_name_by_code.get(int(code), "") or "").strip()
        label = f"{int(code)}: {name}" if name else str(int(code))
        options.append((label, int(code)))
    reg_dd = widgets.Dropdown(options=options, value=(None if initial_reg_code is None else int(initial_reg_code)), description="reg_code")
    if reg_dd.value not in [v for (_, v) in reg_dd.options]:
        reg_dd.value = None
    size_slider = widgets.FloatSlider(
        value=float(s),
        min=0.1,
        max=20.0,
        step=0.1,
        description="size",
        continuous_update=False,
        readout_format=".1f",
    )
    out = widgets.Output()

    def _draw(*_):
        with out:
            out.clear_output(wait=True)
            fig, ax = plt.subplots(layout="constrained")
            rc = reg_dd.value
            fields[name_dd.value].plot(reg_code=rc, ax=ax, show=False, cmap=cmap, s=size_slider.value)
            plt.show()
            backend = str(matplotlib.get_backend()).lower()
            if "inline" in backend or backend.endswith("agg") or "agg" in backend:
                plt.close(fig)

    name_dd.observe(_draw, names="value")
    reg_dd.observe(_draw, names="value")
    size_slider.observe(_draw, names="value")

    display(widgets.VBox([widgets.HBox([name_dd, reg_dd, size_slider]), out]))
    _draw()


def interactive_scalar_field_plot(
    field: ElementScalarField,
    *,
    initial_reg_code: Optional[int] = None,
    s: float = 2,
    cmap: str = "jet",
):
    """Interactive plot helper for element-wise scalar fields (no time/step slider)."""

    if widgets is None or display is None:
        raise RuntimeError("ipywidgets is required for interactive plotting")

    codes = sorted({int(el.reg_code) for el in field.mesh.elements if int(el.reg_code) > 0})
    options = [("all", None)]
    for code in codes:
        name = (field.mesh.region_name_by_code.get(int(code), "") or "").strip()
        label = f"{int(code)}: {name}" if name else str(int(code))
        options.append((label, int(code)))
    reg_dd = widgets.Dropdown(options=options, value=(None if initial_reg_code is None else int(initial_reg_code)), description="reg_code")
    if reg_dd.value not in [v for (_, v) in reg_dd.options]:
        reg_dd.value = None
    size_slider = widgets.FloatSlider(
        value=float(s),
        min=0.1,
        max=20.0,
        step=0.1,
        description="size",
        continuous_update=False,
        readout_format=".1f",
    )
    out = widgets.Output()

    def _draw(*_):
        with out:
            out.clear_output(wait=True)
            fig, ax = plt.subplots(layout="constrained")
            rc = reg_dd.value
            field.plot(reg_code=rc, ax=ax, show=False, cmap=cmap, s=size_slider.value)
            plt.show()
            backend = str(matplotlib.get_backend()).lower()
            if "inline" in backend or backend.endswith("agg") or "agg" in backend:
                plt.close(fig)

    reg_dd.observe(_draw, names="value")
    size_slider.observe(_draw, names="value")

    display(widgets.VBox([widgets.HBox([reg_dd, size_slider]), out]))
    _draw()
