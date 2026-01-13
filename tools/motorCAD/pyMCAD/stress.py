from __future__ import annotations

import math
import pathlib
import tempfile
import uuid
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np


def plot_mesh_stress_fields(
	stress_regions: "StressRegions",
	region_names: Optional[Sequence[str]] = None,
	*,
	fields: Sequence[str] = ("svm", "sp1", "sp2"),
	cmap: str = "jet",
	marker: str = ".",
	point_size: float = 4.0,
	show_mesh: bool = False,
	mesh_color: str = "k",
	mesh_linewidth: float = 0.2,
	mesh_alpha: float = 0.35,
	colorbar: bool = True,
	colorbar_location: str = "right",
	colorbar_size: str = "3%",
	colorbar_pad: float = 0.02,
	share_axes: bool = True,
	title_suffix: str = "",
):
	"""Plot mesh-wise stress fields (scatter over X/Y) for the selected regions.

	This is intended for quick inspection in notebooks. It does not modify data.

	Parameters
	----------
	stress_regions:
		Parsed stress data returned by :func:`get_stress_data`.
	region_names:
		Region names to plot. If None, plots all regions with elements.
	fields:
		Any of: "svm", "sp1", "sp2", "sx", "sy", "txy".
	show_mesh:
		If True, overlay the triangular element mesh (edges) on the same axes.
		Requires that NodesTable coordinates were available in the export.
	colorbar:
		If True, draw a colorbar for each subplot.
	colorbar_location:
		Where to place the colorbar. Supports values like "right", "left", "top", "bottom",
		and corner inset positions like "top right", "top left", "bottom right", "bottom left".
	"""

	import matplotlib.pyplot as plt
	from matplotlib.cm import ScalarMappable
	from matplotlib.colors import Normalize

	try:
		from mpl_toolkits.axes_grid1 import make_axes_locatable
	except Exception:
		make_axes_locatable = None

	try:
		import matplotlib.tri as mtri
	except Exception:
		mtri = None

	def _norm_location(loc: str) -> str:
		return " ".join(str(loc).strip().lower().split())

	def _add_colorbar(ax, mappable, *, loc: str, label: str | None = None):
		if not bool(colorbar):
			return

		loc_n = _norm_location(loc)
		# Always try to place the colorbar OUTSIDE the axes box (like thermal.py).
		# Preferred: axes_grid1 divider (robust with constrained layout).
		if make_axes_locatable is None:
			cb = plt.colorbar(mappable, ax=ax)
			if label:
				cb.set_label(label)
			return

		# Normalize corner aliases
		corner_locs = {
			"top right": "top right",
			"upper right": "top right",
			"bottom right": "bottom right",
			"lower right": "bottom right",
			"top left": "top left",
			"upper left": "top left",
			"bottom left": "bottom left",
			"lower left": "bottom left",
		}
		loc_n = corner_locs.get(loc_n, loc_n)

		divider = make_axes_locatable(ax)

		def _append(side: str, *, orientation: str):
			cax = divider.append_axes(side, size=colorbar_size, pad=float(colorbar_pad))
			cb = plt.colorbar(mappable, cax=cax, orientation=orientation)
			return cb, cax

		if loc_n in {"top", "bottom"}:
			cb, _cax = _append(loc_n, orientation="horizontal")
			cb.ax.xaxis.set_ticks_position("bottom")
			cb.ax.xaxis.set_label_position("bottom")
		elif loc_n in {"left", "right"}:
			cb, _cax = _append(loc_n, orientation="vertical")
		elif loc_n in {"top right", "bottom right", "top left", "bottom left"}:
			# Best-effort: put bar outside on nearest side, then align to corner.
			side = "right" if "right" in loc_n else "left"
			cb, cax = _append(side, orientation="vertical")
			try:
				pos = cax.get_position()
				corner_frac = 0.6
				height = pos.height * corner_frac
				if "top" in loc_n:
					y0 = pos.y1 - height
				else:
					y0 = pos.y0
				cax.set_position([pos.x0, y0, pos.width, height])
			except Exception:
				pass
		else:
			cb, _cax = _append("right", orientation="vertical")

		if label:
			cb.set_label(label)

	def _plot_mesh_edges(region: "StressRegion", ax):
		if not bool(show_mesh):
			return
		if mtri is None:
			raise RuntimeError("matplotlib.tri is required for mesh plotting")
		if not getattr(stress_regions, "node_xy", None):
			raise ValueError(
				"NodesTable coordinates not available (stress_regions.node_xy is empty). "
				"Re-export mechanical data including NodesTable."
			)

		node_to_local = {}
		xs: list[float] = []
		ys: list[float] = []
		triangles: list[tuple[int, int, int]] = []

		def _get_local(node_id: int):
			if node_id in node_to_local:
				return node_to_local[node_id]
			xy = stress_regions.node_xy.get(int(node_id))
			if xy is None:
				return None
			node_to_local[int(node_id)] = len(xs)
			xs.append(float(xy[0]))
			ys.append(float(xy[1]))
			return node_to_local[int(node_id)]

		for el in region.elements:
			i1 = _get_local(el.node_1)
			i2 = _get_local(el.node_2)
			i3 = _get_local(el.node_3)
			if i1 is None or i2 is None or i3 is None:
				continue
			triangles.append((i1, i2, i3))

		if not triangles:
			return

		tri = mtri.Triangulation(xs, ys, triangles=triangles)
		ax.triplot(tri, color=mesh_color, linewidth=float(mesh_linewidth), alpha=float(mesh_alpha), zorder=1)

	field_getters = {
		"svm": (lambda r: r.get_svm(), "Von Mises [MPa]"),
		"sp1": (lambda r: r.get_sp1(), "Principal stress 1 [MPa]"),
		"sp2": (lambda r: r.get_sp2(), "Principal stress 2 [MPa]"),
		"sx": (lambda r: [el.s_x for el in r.elements], "Sx [MPa]"),
		"sy": (lambda r: [el.s_y for el in r.elements], "Sy [MPa]"),
		"txy": (lambda r: [el.t_xy for el in r.elements], "Txy [MPa]"),
	}

	unknown = [f for f in fields if f not in field_getters]
	if unknown:
		raise ValueError(f"Unknown fields: {unknown}. Supported: {sorted(field_getters.keys())}")

	if region_names is not None:
		region_names_set = set(region_names)
	else:
		region_names_set = None

	results = []
	for region in (stress_regions[i] for i in range(len(stress_regions))):
		if region.get_number_elements() <= 0:
			continue
		if region_names_set is not None and region.region_name not in region_names_set:
			continue

		ncols = max(1, len(fields))
		fig, ax = plt.subplots(
			1,
			ncols,
			layout="constrained",
			sharex=share_axes,
			sharey=share_axes,
		)
		if ncols == 1:
			ax = [ax]

		title = f"{region.region_name}"
		if title_suffix:
			title = f"{title} {title_suffix}".strip()
		fig.suptitle(title)

		x = region.get_x()
		y = region.get_y()

		for j, field in enumerate(fields):
			getter, label = field_getters[field]
			values = getter(region)
			_plot_mesh_edges(region, ax[j])
			sc = ax[j].scatter(x, y, c=values, s=point_size, marker=marker, cmap=cmap, zorder=2)
			_add_colorbar(ax[j], sc, loc=colorbar_location, label=None)
			ax[j].set_title(label)
			ax[j].set_aspect("equal", adjustable="box")

		results.append((fig, ax))

	return results


def interactive_mesh_stress_fields_plot(
	stress_regions: "StressRegions",
	region_names: Optional[Sequence[str]] = None,
	*,
	fields: Sequence[str] = ("svm", "sp1", "sp2"),
	cmap: str = "jet",
	marker: str = ".",
	point_size: float = 4.0,
	show_mesh: bool = False,
	mesh_color: str = "k",
	mesh_linewidth: float = 0.2,
	mesh_alpha: float = 0.35,
	colorbar: bool = True,
	colorbar_location: str = "right",
	colorbar_size: str = "3%",
	colorbar_pad: float = 0.02,
	share_axes: bool = True,
	title_suffix: str = "",
):
	"""Interactive (dropdown) version of :func:`plot_mesh_stress_fields`.

	Instead of creating one figure per region, this renders a single figure and lets you
	select the region via a dropdown (ipywidgets).
	
	If ipywidgets is not available, it falls back to plotting the first available region.
	"""

	import matplotlib.pyplot as plt

	try:
		import ipywidgets as widgets
		from IPython.display import display
	except Exception:
		widgets = None
		display = None

	field_getters = {
		"svm": (lambda r: r.get_svm(), "Von Mises [MPa]"),
		"sp1": (lambda r: r.get_sp1(), "Principal stress 1 [MPa]"),
		"sp2": (lambda r: r.get_sp2(), "Principal stress 2 [MPa]"),
		"sx": (lambda r: [el.s_x for el in r.elements], "Sx [MPa]"),
		"sy": (lambda r: [el.s_y for el in r.elements], "Sy [MPa]"),
		"txy": (lambda r: [el.t_xy for el in r.elements], "Txy [MPa]"),
	}

	unknown = [f for f in fields if f not in field_getters]
	if unknown:
		raise ValueError(f"Unknown fields: {unknown}. Supported: {sorted(field_getters.keys())}")

	# Filter regions
	if region_names is not None:
		region_names_set = set(region_names)
	else:
		region_names_set = None

	regions: list[StressRegion] = []
	for region in (stress_regions[i] for i in range(len(stress_regions))):
		if region.get_number_elements() <= 0:
			continue
		if region_names_set is not None and region.region_name not in region_names_set:
			continue
		regions.append(region)

	if not regions:
		raise ValueError("No regions to plot")

	def _region_label(r: StressRegion) -> str:
		name = (r.region_name or "").strip()
		if name:
			return name
		return f"reg_code={int(r.reg_code)}"

	# Reuse helpers from plot_mesh_stress_fields by calling it for one region and
	# returning the first fig/ax. To keep plotting consistent, we use the same logic.
	def _plot_single(region: StressRegion):
		# Build a lightweight StressRegions container for a single region
		one = StressRegions()
		one.node_xy = dict(getattr(stress_regions, "node_xy", {}) or {})
		one._regions = [region]
		return plot_mesh_stress_fields(
			one,
			region_names=None,
			fields=fields,
			cmap=cmap,
			marker=marker,
			point_size=point_size,
			show_mesh=show_mesh,
			mesh_color=mesh_color,
			mesh_linewidth=mesh_linewidth,
			mesh_alpha=mesh_alpha,
			colorbar=colorbar,
			colorbar_location=colorbar_location,
			colorbar_size=colorbar_size,
			colorbar_pad=colorbar_pad,
			share_axes=share_axes,
			title_suffix=title_suffix,
		)[0]

	if widgets is None or display is None:
		# Fallback: first region only
		fig, ax = _plot_single(regions[0])
		plt.show()
		return fig, ax

	out = widgets.Output()
	options = [(_region_label(r), i) for i, r in enumerate(regions)]
	dd = widgets.Dropdown(options=options, value=0, description="region")

	def _update(index: int):
		with out:
			out.clear_output(wait=True)
			fig, ax = _plot_single(regions[int(index)])
			plt.show()

	display(widgets.HBox([dd]), out)
	widgets.interactive_output(_update, {"index": dd})
	_update(dd.value)
	return dd, out


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


def check_youngs_modulus(
	non_linear_strain: Sequence[float],
	non_linear_stress: Sequence[float],
	youngs_modulus_mpa: float,
	*,
	rel_tol: float = 0.01,
	abs_tol: float = 0.1,
) -> None:
	"""Validate that the initial slope of non-linear stress/strain matches Young's modulus."""

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
	"""Return last stress point still on the initial linear (elastic) part of the curve."""

	for i in range(1, len(non_linear_stress)):
		strain_i = float(non_linear_strain[i])
		if math.isclose(strain_i, 0.0):
			continue
		if not math.isclose(float(non_linear_stress[i]) / strain_i, float(youngs_modulus_mpa), rel_tol=rel_tol):
			return float(non_linear_stress[i - 1])

	return float(non_linear_stress[-1])


@dataclass
class StressElement:
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
	def __init__(self):
		self._regions: List[StressRegion] = []
		# NodeIndex -> (x_mm, y_mm) from NodesTable (if present)
		self.node_xy: dict[int, tuple[float, float]] = {}

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
				row = in_file.readline().split(sep=",")
				if len(row) < 3:
					continue
				try:
					node_id = int(row[0])
					x = float(row[1])
					y = float(row[2])
				except ValueError:
					continue
				stress_regions.node_xy[int(node_id)] = (float(x), float(y))

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



def get_stress_data(
	mc,
	*,
	filename: str | pathlib.Path | None = None,
	clean_up: bool = True,
) -> StressRegions:
	"""Export mechanical stress data from Motor-CAD and parse into StressRegions.

	If `filename` is provided, the export is written there (and not deleted).
	Otherwise a temporary file is used.
	"""

	if filename is None:
		export_path = mcad_make_temp_txt_path(mc)
		is_temp = True
	else:
		export_path = pathlib.Path(filename)
		export_path.parent.mkdir(parents=True, exist_ok=True)
		if export_path.suffix.lower() != ".txt":
			export_path = export_path.with_suffix(".txt")
		is_temp = False

	mc.save_fea_data(
		str(export_path),
		0,
		0,
		"RegCode,X,Y,Sx,Sy,Txy,Sp1,Sp2,SVM,Ux,Uy",
		"",
		",",
	)

	stress_regions = _parse_first_block_stress_file(export_path)

	if clean_up and is_temp:
		try:
			export_path.unlink()
		except FileNotFoundError:
			pass
	elif is_temp:
		print(f"Temporary file not deleted: {export_path}")

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
	"""Return temperature-adjusted stress curve and scaled Young's modulus."""

	adjusted = np.asarray(stress, dtype=float).copy()
	youngs_scaled = float(base_youngs_mpa) * (1.0 + float(youngs_temp_coeff) * float(delta_t_c))

	linear_limit = find_divergence_point(strain, stress, base_youngs_mpa)
	linear_mask = np.asarray(stress, dtype=float) <= float(linear_limit)

	adjusted[linear_mask] *= youngs_scaled / float(base_youngs_mpa)
	adjusted[~linear_mask] *= 1.0 + float(plastic_temp_coeff) * float(delta_t_c)

	return adjusted, youngs_scaled
