from __future__ import annotations

import pathlib
import re
import tempfile
import uuid

import matplotlib.pyplot as plt


class MagElement:
    """Motor-CAD electromagnetic element data.

    Columns (ElementsTable)
    - TriIndex, Node1, Node2, Node3, RegCode, Bx, By, A, J

    Units
    - Bx, By: [T]
    - B (magnitude): [T] computed as sqrt(Bx^2 + By^2)
    - A: [Wb/m]
    - J: [A/mm^2]
    """

    def __init__(
        self,
        tri_index,
        node_1,
        node_2,
        node_3,
        reg_code,
        bx=None,
        by=None,
        a=None,
        j=None,
        b=None,
    ):
        self.tri_index = int(tri_index)
        self.node_1 = int(node_1)
        self.node_2 = int(node_2)
        self.node_3 = int(node_3)
        self.reg_code = int(reg_code)

        if bx is not None and by is not None:
            self.bx = float(bx)
            self.by = float(by)
            self._b = float((self.bx**2 + self.by**2) ** 0.5)
        elif b is not None:
            # Backward compatibility for old exports that provided only B.
            self.bx = None
            self.by = None
            self._b = float(b)
        else:
            raise ValueError("Either (bx, by) or b must be provided")

        self.a = float(a) if a is not None else 0.0
        self.j = float(j) if j is not None else 0.0

    @property
    def b(self) -> float:
        """Magnetic flux density magnitude [T]."""
        return self._b

    @classmethod
    def from_csv_row(cls, row):
        # Accept both formats:
        # - New: ... RegCode,Bx,By,A,J (len>=9)
        # - Old: ... RegCode,B,A,J (len>=8)
        if len(row) >= 9:
            return cls(
                tri_index=row[0],
                node_1=row[1],
                node_2=row[2],
                node_3=row[3],
                reg_code=row[4],
                bx=row[5],
                by=row[6],
                a=row[7],
                j=row[8],
            )
        if len(row) >= 8:
            return cls(
                tri_index=row[0],
                node_1=row[1],
                node_2=row[2],
                node_3=row[3],
                reg_code=row[4],
                b=row[5],
                a=row[6],
                j=row[7],
            )
        raise ValueError("Invalid row format for MagElement")


class MagneticRegion:
    """Container for magnetic elements belonging to the same region code."""

    def __init__(self):
        self.region_name = ""
        self.reg_code = 0
        self.elements = []  # list[MagElement]

    def add_element(
        self,
        tri_index,
        node_1,
        node_2,
        node_3,
        reg_code,
        bx=None,
        by=None,
        a=None,
        j=None,
        b=None,
    ):
        self.elements.append(
            MagElement(
                tri_index=tri_index,
                node_1=node_1,
                node_2=node_2,
                node_3=node_3,
                reg_code=reg_code,
                bx=bx,
                by=by,
                a=a,
                j=j,
                b=b,
            )
        )

    def get_b(self):
        """Return B magnitude list [T]."""
        return [el.b for el in self.elements]

    def get_bx(self):
        """Return Bx list [T] (may contain None)."""
        return [el.bx for el in self.elements]

    def get_by(self):
        """Return By list [T] (may contain None)."""
        return [el.by for el in self.elements]

    def get_a(self):
        """Return vector potential A list [Wb/m]."""
        return [el.a for el in self.elements]

    def get_j(self):
        """Return current density J list [A/mm^2]."""
        return [el.j for el in self.elements]

    def get_tri_index(self):
        return [el.tri_index for el in self.elements]

    def get_nodes(self):
        return [(el.node_1, el.node_2, el.node_3) for el in self.elements]


class MagneticRegions:
    """Collection of MagneticRegion objects indexed by region code-1."""

    def __init__(self):
        self._regions = []
        # NodeIndex -> (x_mm, y_mm) from NodesTable
        self.node_xy = {}

    def __len__(self):
        return len(self._regions)

    def __getitem__(self, region_number):
        return self._regions[region_number]

    def __setitem__(self, region_number, data):
        self._regions[region_number] = data

    def add_region(self):
        self._regions.append(MagneticRegion())

    def ensure_region(self, reg_code: int):
        while reg_code > len(self._regions):
            self.add_region()

    def set_node_xy(self, node_xy):
        """Attach node coordinate map (NodeIndex -> (x_mm, y_mm))."""
        self.node_xy = dict(node_xy)

    def _element_centroid_xy(self, element: MagElement):
        """Return (x,y) centroid for a MagElement based on node coordinates."""
        n1 = self.node_xy.get(element.node_1)
        n2 = self.node_xy.get(element.node_2)
        n3 = self.node_xy.get(element.node_3)
        if n1 is None or n2 is None or n3 is None:
            return None
        x = (n1[0] + n2[0] + n3[0]) / 3.0
        y = (n1[1] + n2[1] + n3[1]) / 3.0
        return x, y

    def plot(
        self,
        reg_code=None,
        quantity="b",
        cmap="jet",
        s=2,
        ax=None,
        show=True,
        mesh=False,
        mesh_kwargs=None,
    ):
        """Scatter plot magnetic data.

        If NodesTable coordinates are available, plots element centroid (x,y) colored by quantity.
        Otherwise falls back to tri_index vs quantity.
        """

        quantity = str(quantity).lower()
        if quantity not in {"b", "a", "j"}:
            raise ValueError("quantity must be one of: 'b', 'a', 'j'")

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        if mesh:
            self.plot_mesh(reg_code=reg_code, ax=ax, show=False, **(mesh_kwargs or {}))

        xs = []
        ys = []
        cs = []
        used_xy = False

        if reg_code is None:
            regions_to_iterate = [r for r in self._regions if r.elements]
        else:
            if reg_code <= 0:
                raise ValueError("reg_code must be >= 1")
            if reg_code <= len(self._regions):
                regions_to_iterate = [self._regions[reg_code - 1]]
            else:
                regions_to_iterate = []

        for region in regions_to_iterate:
            for el in region.elements:
                v = getattr(el, quantity)
                c_xy = self._element_centroid_xy(el)
                if c_xy is not None:
                    xs.append(c_xy[0])
                    ys.append(c_xy[1])
                    cs.append(v)
                    used_xy = True
                else:
                    xs.append(el.tri_index)
                    ys.append(v)
                    cs.append(v)

        if not xs:
            ax.set_title("No data to plot")
            if show:
                plt.show()
            return ax

        if used_xy:
            sc = ax.scatter(xs, ys, c=cs, s=s, cmap=cmap, marker=".")
            ax.set_xlabel("X [mm]")
            ax.set_ylabel("Y [mm]")
            cb = ax.figure.colorbar(sc, ax=ax)
            cb.set_label({"b": "|B| [T]", "a": "A [Wb/m]", "j": "J [A/mm^2]"}[quantity])
            title_region = f"reg_code={reg_code}" if reg_code is not None else "all regions"
            ax.set_title(f"Magnetic scatter ({title_region})")
            ax.set_aspect("equal")
        else:
            ax.scatter(xs, ys, s=s, marker=".")
            ax.set_xlabel("TriIndex")
            ax.set_ylabel({"b": "|B| [T]", "a": "A [Wb/m]", "j": "J [A/mm^2]"}[quantity])
            title_region = f"reg_code={reg_code}" if reg_code is not None else "all regions"
            ax.set_title(f"Magnetic scatter (fallback: {title_region})")
            ax.grid(True)

        if show:
            plt.show()
        return ax

    def plot_quiver(
        self,
        reg_code=None,
        normalize=False,
        stride=10,
        cmap="jet",
        ax=None,
        show=True,
        scale=None,
        width=0.002,
        mesh=False,
        mesh_kwargs=None,
    ):
        """Quiver plot of the magnetic flux density vector (Bx, By)."""

        if stride is None:
            stride = 1
        stride = int(stride)
        if stride <= 0:
            raise ValueError("stride must be >= 1")

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        if mesh:
            self.plot_mesh(reg_code=reg_code, ax=ax, show=False, **(mesh_kwargs or {}))

        xs = []
        ys = []
        us = []
        vs = []
        mags = []

        if reg_code is None:
            regions_to_iterate = [r for r in self._regions if r.elements]
        else:
            if reg_code <= 0:
                raise ValueError("reg_code must be >= 1")
            if reg_code <= len(self._regions):
                regions_to_iterate = [self._regions[reg_code - 1]]
            else:
                regions_to_iterate = []

        idx = 0
        for region in regions_to_iterate:
            for el in region.elements:
                idx += 1
                if (idx - 1) % stride != 0:
                    continue
                c_xy = self._element_centroid_xy(el)
                if c_xy is None:
                    continue
                if el.bx is None or el.by is None:
                    continue
                bx = float(el.bx)
                by = float(el.by)
                mag = float((bx**2 + by**2) ** 0.5)
                if normalize:
                    if mag > 0:
                        u = bx / mag
                        v = by / mag
                    else:
                        u = 0.0
                        v = 0.0
                else:
                    u = bx
                    v = by

                xs.append(c_xy[0])
                ys.append(c_xy[1])
                us.append(u)
                vs.append(v)
                mags.append(mag)

        if not xs:
            raise ValueError(
                "No Bx/By vector data to plot. Export with 'RegCode,Bx,By,A,J' and ensure NodesTable exists."
            )

        q = ax.quiver(
            xs,
            ys,
            us,
            vs,
            mags,
            cmap=cmap,
            angles="xy",
            scale_units="xy",
            scale=scale,
            width=width,
        )
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        ax.set_aspect("equal")
        cb = ax.figure.colorbar(q, ax=ax)
        cb.set_label("|B| [T]")
        title_region = f"reg_code={reg_code}" if reg_code is not None else "all regions"
        ax.set_title(f"B vector quiver ({title_region}, normalize={bool(normalize)}, stride={stride})")

        if show:
            plt.show()
        return ax

    def plot_mesh(self, reg_code=None, ax=None, show=True, color="k", linewidth=0.2, alpha=0.7):
        """Plot element mesh (triangle edges) using NodesTable coordinates."""
        if not self.node_xy:
            raise ValueError("NodesTable coordinates not available (node_xy is empty).")
        try:
            import matplotlib.tri as mtri
        except Exception as e:
            raise RuntimeError(f"matplotlib.tri is required for mesh plotting: {e}")

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        if reg_code is None:
            regions_to_iterate = [r for r in self._regions if r.elements]
        else:
            if reg_code <= 0:
                raise ValueError("reg_code must be >= 1")
            if reg_code <= len(self._regions):
                regions_to_iterate = [self._regions[reg_code - 1]]
            else:
                regions_to_iterate = []

        node_to_local = {}
        xs = []
        ys = []
        triangles = []

        def _get_local(node_id):
            if node_id in node_to_local:
                return node_to_local[node_id]
            xy = self.node_xy.get(node_id)
            if xy is None:
                return None
            node_to_local[node_id] = len(xs)
            xs.append(float(xy[0]))
            ys.append(float(xy[1]))
            return node_to_local[node_id]

        for region in regions_to_iterate:
            for el in region.elements:
                i1 = _get_local(el.node_1)
                i2 = _get_local(el.node_2)
                i3 = _get_local(el.node_3)
                if i1 is None or i2 is None or i3 is None:
                    continue
                triangles.append((i1, i2, i3))

        if not triangles:
            raise ValueError("No triangles to plot (missing node coords or empty region).")

        tri = mtri.Triangulation(xs, ys, triangles=triangles)
        ax.triplot(tri, color=color, linewidth=linewidth, alpha=alpha)
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        ax.set_aspect("equal")
        title_region = f"reg_code={reg_code}" if reg_code is not None else "all regions"
        ax.set_title(f"Mesh (tri edges, {title_region})")
        ax.grid(False)
        if show:
            plt.show()
        return ax


class MagneticRegionsTimeSeries:
    """Container for transient/step-based magnetic data parsed from a multi-step txt."""

    def __init__(self, by_step=None, meta=None):
        self.by_step = dict(by_step or {})
        self.meta = dict(meta or {})

    @property
    def steps(self):
        return sorted(self.by_step.keys())

    def __len__(self):
        return len(self.by_step)

    def __getitem__(self, step):
        return self.by_step[step]

    def plot(self, step, **kwargs):
        return self.by_step[step].plot(**kwargs)

    def plot_quiver(self, step, **kwargs):
        return self.by_step[step].plot_quiver(**kwargs)

    def plot_mesh(self, step, **kwargs):
        return self.by_step[step].plot_mesh(**kwargs)


def mcad_default_export_dir(mc) -> pathlib.Path:
    """Best-effort directory for temporary exports.

    Prefer the folder containing the active .mot file (CurrentMotFilePath_MotorLAB).
    Falls back to the OS temp directory if unavailable.
    """

    try:
        mot_path = mc.get_variable("CurrentMotFilePath_MotorLAB")
    except Exception:
        mot_path = ""

    if mot_path:
        try:
            return pathlib.Path(mot_path).parent
        except Exception:
            pass

    return pathlib.Path(tempfile.gettempdir())


def mcad_make_temp_txt_path(mc) -> pathlib.Path:
    return mcad_default_export_dir(mc) / pathlib.Path(f"{uuid.uuid4()}.txt")


# Backward-compatible aliases (notebook code used underscore names)
_mcad_default_export_dir = mcad_default_export_dir
_mcad_make_temp_txt_path = mcad_make_temp_txt_path


def _parse_first_block_magnetic_file(filename) -> MagneticRegions:
    """Parse the first Elements/Nodes/Regions tables found in a Motor-CAD export txt."""

    mag_regions = MagneticRegions()
    node_xy = {}
    filename = pathlib.Path(filename)

    def _scan_to_table(in_file, table_name):
        while True:
            line = in_file.readline()
            if not line:
                return None
            if _is_table_header(line, table_name):
                return line

    with open(filename, "r") as in_file:
        elements_header = _scan_to_table(in_file, "ElementsTable")
        if elements_header is None:
            raise ValueError(f"ElementsTable not found in file: {filename}")

        number_of_elements = int(elements_header.strip().split()[1])
        _skip_header_lines(in_file, 4)

        for _ in range(number_of_elements):
            row = in_file.readline().split(sep=",")
            # New format: RegCode,Bx,By,A,J -> total len >= 9
            # Old format: RegCode,B,A,J -> total len >= 8
            if len(row) >= 9:
                try:
                    reg_code = int(row[4])
                except ValueError:
                    continue
                mag_regions.ensure_region(reg_code)
                mag_regions[reg_code - 1].add_element(
                    tri_index=row[0],
                    node_1=row[1],
                    node_2=row[2],
                    node_3=row[3],
                    reg_code=row[4],
                    bx=row[5],
                    by=row[6],
                    a=row[7],
                    j=row[8],
                )
            elif len(row) >= 8:
                try:
                    reg_code = int(row[4])
                except ValueError:
                    continue
                mag_regions.ensure_region(reg_code)
                mag_regions[reg_code - 1].add_element(
                    tri_index=row[0],
                    node_1=row[1],
                    node_2=row[2],
                    node_3=row[3],
                    reg_code=row[4],
                    b=row[5],
                    a=row[6],
                    j=row[7],
                )
            else:
                continue

        nodes_header = _scan_to_table(in_file, "NodesTable")
        if nodes_header is not None:
            number_of_nodes = int(nodes_header.strip().split()[1])
            _skip_header_lines(in_file, 4)
            for _ in range(number_of_nodes):
                row = in_file.readline().split(sep=",")
                try:
                    node_idx = int(row[0])
                    x_mm = float(row[1])
                    y_mm = float(row[2])
                    node_xy[node_idx] = (x_mm, y_mm)
                except (ValueError, IndexError):
                    pass

        regions_header = _scan_to_table(in_file, "RegionsTable")
        if regions_header is not None:
            number_of_regions = int(regions_header.strip().split()[1])
            _skip_header_lines(in_file, 4)
            for _ in range(number_of_regions):
                row = in_file.readline().split(sep=",")
                try:
                    reg_code = int(row[0])
                except (ValueError, IndexError):
                    continue
                if reg_code <= len(mag_regions):
                    mag_regions[reg_code - 1].reg_code = reg_code
                    mag_regions[reg_code - 1].region_name = row[-1].strip()

    mag_regions.set_node_xy(node_xy)
    return mag_regions


def get_magnetic_data(mc, first_step=1, final_step=1, clean_up=True) -> MagneticRegions:
    """Export Motor-CAD electromagnetic element data and return MagneticRegions (first block)."""

    temp_filename = mcad_make_temp_txt_path(mc)
    mc.save_fea_data(
        str(temp_filename),
        int(first_step),
        int(final_step),
        "RegCode,Bx,By,A,J",
        "",
        ",",
    )
    mag_regions = _parse_first_block_magnetic_file(temp_filename)

    if clean_up:
        try:
            temp_filename.unlink()
        except FileNotFoundError:
            pass
    else:
        print(f"Temporary file not deleted: {temp_filename}")

    return mag_regions


def get_magnetic_data_from_file(filename, clean_up=False) -> MagneticRegions:
    """Parse an existing Motor-CAD export file into MagneticRegions (first block)."""

    filename = pathlib.Path(filename)
    mag_regions = _parse_first_block_magnetic_file(filename)
    if clean_up:
        try:
            filename.unlink()
        except FileNotFoundError:
            pass
    return mag_regions


_MCAD_STEP_HEADER_RE = re.compile(
    r"^\s*(?P<prefix>\d+)\s+Solution\s+(?P<solution>\d+)"
    r"(?:\s+Time\s+index\s+(?P<time_index>-?\d+)\s+Time\s+(?P<time_s>[-+0-9.Ee]+)\s+\[s\])?"
    r"\s+Rotate\s+Step\s+(?P<rotate_step>[-+0-9.Ee]+)\s*$",
    re.IGNORECASE,
)


def _is_table_header(line: str, table_name: str) -> bool:
    tokens = line.strip().split()
    return len(tokens) >= 3 and tokens[1].isdigit() and tokens[2].strip() == table_name


def _read_until_table_header(in_file, table_name: str):
    """Advance until a '<idx> <N> {table_name}' line is found; return that line or None."""

    while True:
        pos = in_file.tell()
        line = in_file.readline()
        if not line:
            return None
        if _is_table_header(line, table_name):
            return line
        if _MCAD_STEP_HEADER_RE.match(line.strip()):
            in_file.seek(pos)
            return None


def _skip_header_lines(in_file, n=4):
    for _ in range(n):
        in_file.readline()


def get_magnetic_timeseries_from_file(
    filename,
    key="time_index",
    clean_up=False,
    max_blocks=None,
    verbose=False,
) -> MagneticRegionsTimeSeries:
    """Parse a Motor-CAD multi-step electromagnetic txt into MagneticRegionsTimeSeries."""

    filename = pathlib.Path(filename)
    ts = MagneticRegionsTimeSeries()

    with open(filename, "r") as in_file:
        while True:
            line = in_file.readline()
            if not line:
                break

            m = _MCAD_STEP_HEADER_RE.match(line.strip())
            if not m:
                continue

            meta = {
                "raw_header": line.strip(),
                "solution": int(m.group("solution")),
                "time_index": int(m.group("time_index")) if m.group("time_index") is not None else None,
                "time_s": float(m.group("time_s")) if m.group("time_s") is not None else None,
                "rotate_step": float(m.group("rotate_step")) if m.group("rotate_step") is not None else None,
            }

            if key == "time_index":
                if meta["time_index"] is not None:
                    step_key = meta["time_index"]
                else:
                    step_key = 0 if 0 not in ts.by_step else meta["solution"]
            elif key == "solution":
                step_key = meta["solution"]
            else:
                step_key = meta["solution"]

            elements_header = _read_until_table_header(in_file, "ElementsTable")
            if elements_header is None:
                if verbose:
                    print("No ElementsTable after:", meta["raw_header"])
                continue

            n_elements = int(elements_header.strip().split()[1])
            _skip_header_lines(in_file, 4)

            mag_regions = MagneticRegions()
            for _ in range(n_elements):
                row = in_file.readline().split(sep=",")
                if len(row) >= 9:
                    try:
                        reg_code = int(row[4])
                    except ValueError:
                        continue
                    mag_regions.ensure_region(reg_code)
                    mag_regions[reg_code - 1].add_element(
                        tri_index=row[0],
                        node_1=row[1],
                        node_2=row[2],
                        node_3=row[3],
                        reg_code=row[4],
                        bx=row[5],
                        by=row[6],
                        a=row[7],
                        j=row[8],
                    )
                elif len(row) >= 8:
                    try:
                        reg_code = int(row[4])
                    except ValueError:
                        continue
                    mag_regions.ensure_region(reg_code)
                    mag_regions[reg_code - 1].add_element(
                        tri_index=row[0],
                        node_1=row[1],
                        node_2=row[2],
                        node_3=row[3],
                        reg_code=row[4],
                        b=row[5],
                        a=row[6],
                        j=row[7],
                    )
                else:
                    continue

            node_xy = {}
            nodes_header = _read_until_table_header(in_file, "NodesTable")
            if nodes_header is not None:
                n_nodes = int(nodes_header.strip().split()[1])
                _skip_header_lines(in_file, 4)
                for _ in range(n_nodes):
                    row = in_file.readline().split(sep=",")
                    try:
                        node_idx = int(row[0])
                        x_mm = float(row[1])
                        y_mm = float(row[2])
                        node_xy[node_idx] = (x_mm, y_mm)
                    except (ValueError, IndexError):
                        pass
            mag_regions.set_node_xy(node_xy)

            regions_header = _read_until_table_header(in_file, "RegionsTable")
            if regions_header is not None:
                n_regions = int(regions_header.strip().split()[1])
                _skip_header_lines(in_file, 4)
                for _ in range(n_regions):
                    row = in_file.readline().split(sep=",")
                    try:
                        reg_code = int(row[0])
                    except (ValueError, IndexError):
                        continue
                    if reg_code <= len(mag_regions):
                        mag_regions[reg_code - 1].reg_code = reg_code
                        mag_regions[reg_code - 1].region_name = row[-1].strip()

            ts.by_step[step_key] = mag_regions
            ts.meta[step_key] = meta

            if verbose:
                print(f"Parsed block key={step_key}: elements={n_elements}, nodes={len(node_xy)}")

            if max_blocks is not None and len(ts) >= int(max_blocks):
                break

    if clean_up:
        try:
            filename.unlink()
        except FileNotFoundError:
            pass

    return ts


# -------- Interactive plotting helpers (optional dependency: ipywidgets) --------
try:
    import ipywidgets as widgets
    from IPython.display import display
except Exception:
    widgets = None
    display = None


def interactive_magnetic_plot(ts: MagneticRegionsTimeSeries, initial_step=None, quantity="b", reg_code=None, s=2, cmap="jet"):
    """Interactive step toggle plot for MagneticRegionsTimeSeries."""

    if widgets is None or display is None:
        raise RuntimeError("ipywidgets is required for interactive plotting")
    if len(ts) == 0:
        raise ValueError("Empty time series.")

    steps = ts.steps
    if initial_step is None:
        initial_step = steps[0]

    step_slider = widgets.SelectionSlider(
        options=steps,
        value=initial_step,
        description="step",
        continuous_update=False,
        layout=widgets.Layout(width="650px"),
    )
    qty_dd = widgets.Dropdown(
        options=[("B", "b"), ("A", "a"), ("J", "j")],
        value=str(quantity).lower(),
        description="qty",
    )
    mesh_chk = widgets.Checkbox(value=False, description="mesh", indent=False)
    reg_text = widgets.Text(
        value="" if reg_code is None else str(reg_code),
        description="reg_code",
        placeholder="(blank = all)",
    )
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

    def _parse_reg_code(text):
        t = str(text).strip()
        if t == "":
            return None
        return int(t)

    def _draw(*_):
        with out:
            out.clear_output(wait=True)
            fig, ax = plt.subplots(layout="constrained")
            step = int(step_slider.value)
            qty = str(qty_dd.value).lower()
            rc = _parse_reg_code(reg_text.value)
            ax = ts.by_step[step].plot(
                reg_code=rc,
                quantity=qty,
                s=size_slider.value,
                cmap=cmap,
                ax=ax,
                show=False,
                mesh=bool(mesh_chk.value),
            )
            header = ts.meta.get(step, {}).get("raw_header")
            if header:
                ax.set_title(f"{ax.get_title()}\n{header}")
            plt.show()
            plt.close(fig)
            return ax

    step_slider.observe(_draw, names="value")
    qty_dd.observe(_draw, names="value")
    mesh_chk.observe(_draw, names="value")
    reg_text.observe(_draw, names="value")
    size_slider.observe(_draw, names="value")

    display(widgets.VBox([widgets.HBox([step_slider, qty_dd, mesh_chk]), widgets.HBox([reg_text, size_slider]), out]))
    _draw()


def interactive_magnetic_quiver(
    ts: MagneticRegionsTimeSeries,
    initial_step=None,
    reg_code=None,
    normalize=False,
    stride=20,
    scale=None,
    width=0.002,
    cmap="jet",
    layout_width="650px",
):
    """Interactive step toggle quiver plot for MagneticRegionsTimeSeries."""

    if widgets is None or display is None:
        raise RuntimeError("ipywidgets is required for interactive plotting")
    if len(ts) == 0:
        raise ValueError("Empty time series.")

    steps = ts.steps
    if initial_step is None:
        initial_step = steps[0]

    step_slider = widgets.SelectionSlider(
        options=steps,
        value=initial_step,
        description="step",
        continuous_update=False,
        layout=widgets.Layout(width=layout_width),
    )
    normalize_chk = widgets.Checkbox(value=bool(normalize), description="normalize", indent=False)
    mesh_chk = widgets.Checkbox(value=False, description="mesh", indent=False)
    stride_slider = widgets.IntSlider(
        value=int(stride),
        min=1,
        max=200,
        step=1,
        description="stride",
        continuous_update=False,
    )
    scale_text = widgets.Text(value="" if scale is None else str(scale), description="scale", placeholder="(blank=None)")
    width_text = widgets.FloatText(value=float(width), description="width")
    out = widgets.Output()

    def _parse_scale(text):
        t = str(text).strip()
        if t == "":
            return None
        return float(t)

    def _region_options_for_step(step):
        mr = ts.by_step[int(step)]
        options = [("all", None)]
        regions = getattr(mr, "_regions", [])
        for idx, region in enumerate(regions):
            if not getattr(region, "elements", None):
                continue
            code = getattr(region, "reg_code", 0) or (idx + 1)
            name = (getattr(region, "region_name", "") or "").strip()
            label = f"{code}: {name}" if name else str(code)
            options.append((label, int(code)))
        return options

    reg_dd = widgets.Dropdown(options=_region_options_for_step(step_slider.value), value=(None if reg_code is None else int(reg_code)), description="reg_code")
    if reg_dd.value not in [v for (_, v) in reg_dd.options]:
        reg_dd.value = None

    def _sync_reg_options(*_):
        current = reg_dd.value
        new_options = _region_options_for_step(step_slider.value)
        reg_dd.options = new_options
        values = [v for (_, v) in new_options]
        reg_dd.value = current if current in values else None

    def _draw(*_):
        with out:
            out.clear_output(wait=True)
            fig, ax = plt.subplots(layout="constrained")
            step = int(step_slider.value)
            sc = _parse_scale(scale_text.value)
            ax = ts.by_step[step].plot_quiver(
                reg_code=reg_dd.value,
                normalize=bool(normalize_chk.value),
                stride=int(stride_slider.value),
                cmap=cmap,
                ax=ax,
                show=False,
                scale=sc,
                width=float(width_text.value),
                mesh=bool(mesh_chk.value),
            )
            header = ts.meta.get(step, {}).get("raw_header")
            if header:
                ax.set_title(f"{ax.get_title()}\n{header}")
            plt.show()
            plt.close(fig)
            return ax

    step_slider.observe(_sync_reg_options, names="value")
    step_slider.observe(_draw, names="value")
    reg_dd.observe(_draw, names="value")
    normalize_chk.observe(_draw, names="value")
    mesh_chk.observe(_draw, names="value")
    stride_slider.observe(_draw, names="value")
    scale_text.observe(_draw, names="value")
    width_text.observe(_draw, names="value")

    display(
        widgets.VBox(
            [
                widgets.HBox([step_slider]),
                widgets.HBox([reg_dd, normalize_chk, mesh_chk]),
                widgets.HBox([stride_slider, scale_text, width_text]),
                out,
            ]
        )
    )
    _sync_reg_options()
    _draw()
