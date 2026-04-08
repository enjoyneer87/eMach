from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import numpy as np

from ._export import (
	mcad_make_temp_txt_path,
	safe_stem as _safe_stem,
	save_fea_text_export,
	unique_path as _unique_path,
)


def export_thermal_svgs(
	thermal_regions: "ThermalRegions",
	*,
	out_dir: str | pathlib.Path,
	stem: str,
	fields: Sequence[str] = ("t", "g", "q"),
	cmap: str = "jet",
	point_size: float = 4.0,
	dpi: int = 140,
	show_mesh: bool = True,
	mesh_alpha: float = 0.25,
	colorbar_location: str = "top",
) -> Dict[str, pathlib.Path]:
	"""Export thermal fields as SVGs (one per field)."""

	import matplotlib.pyplot as plt

	out_dir = pathlib.Path(out_dir)
	out_dir.mkdir(parents=True, exist_ok=True)

	exported: Dict[str, pathlib.Path] = {}
	for f in tuple(fields):
		fig_ax_list = plot_mesh_thermal_fields(
			thermal_regions,
			fields=(str(f),),
			cmap=cmap,
			point_size=float(point_size),
			show_mesh=bool(show_mesh),
			mesh_alpha=float(mesh_alpha),
			colorbar_location=str(colorbar_location),
			title_suffix=f"({stem})",
		)
		if not fig_ax_list:
			continue
		svg_path = _unique_path(out_dir / f"Thermal_{str(f)}_{_safe_stem(stem)}.svg")
		fig_ax_list[0][0].savefig(svg_path, dpi=int(dpi))
		exported[str(f)] = svg_path
		for fig, _ax in fig_ax_list:
			plt.close(fig)

	return exported


@dataclass
class ThermalElement:
	tri_index: int
	node_1: int
	node_2: int
	node_3: int
	reg_code: int
	x: float
	y: float
	t: float
	g: float
	q: float


class ThermalRegion:
	def __init__(self):
		self.region_name = ""
		self.reg_code = 0
		self.elements: list[ThermalElement] = []

	def add_element(
		self,
		*,
		tri_index: int,
		node_1: int,
		node_2: int,
		node_3: int,
		reg_code: int,
		x: float,
		y: float,
		t: float,
		g: float,
		q: float,
	) -> None:
		self.elements.append(
			ThermalElement(
				tri_index=int(tri_index),
				node_1=int(node_1),
				node_2=int(node_2),
				node_3=int(node_3),
				reg_code=int(reg_code),
				x=float(x),
				y=float(y),
				t=float(t),
				g=float(g),
				q=float(q),
			)
		)

	def get_number_elements(self) -> int:
		return len(self.elements)

	def get_x(self) -> list[float]:
		return [el.x for el in self.elements]

	def get_y(self) -> list[float]:
		return [el.y for el in self.elements]

	def get_t(self) -> list[float]:
		return [el.t for el in self.elements]

	def get_g(self) -> list[float]:
		return [el.g for el in self.elements]

	def get_q(self) -> list[float]:
		return [el.q for el in self.elements]


class ThermalRegions:
	def __init__(self):
		self._regions: list[ThermalRegion] = []
		# NodeIndex -> (x_mm, y_mm) from NodesTable (if present)
		self.node_xy: dict[int, tuple[float, float]] = {}

	def __len__(self) -> int:
		return len(self._regions)

	def __getitem__(self, region_number: int) -> ThermalRegion:
		return self._regions[region_number]

	def __setitem__(self, region_number: int, data: ThermalRegion) -> None:
		self._regions[region_number] = data

	def add_region(self) -> None:
		self._regions.append(ThermalRegion())

	def ensure_region(self, reg_code: int) -> None:
		while int(reg_code) > len(self._regions):
			self.add_region()

	def _element_centroid_xy(self, node_1: int, node_2: int, node_3: int) -> Optional[tuple[float, float]]:
		n1 = self.node_xy.get(int(node_1))
		n2 = self.node_xy.get(int(node_2))
		n3 = self.node_xy.get(int(node_3))
		if n1 is None or n2 is None or n3 is None:
			return None
		return (
			(n1[0] + n2[0] + n3[0]) / 3.0,
			(n1[1] + n2[1] + n3[1] + 0.0) / 3.0,
		)


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


def _parse_first_block_thermal_file(filename: pathlib.Path) -> ThermalRegions:
	regions = ThermalRegions()
	filename = pathlib.Path(filename)

	with open(filename, "r") as in_file:
		elements_header = _read_until_table_header(in_file, "ElementsTable")
		if elements_header is None:
			raise ValueError(f"ElementsTable not found in file: {filename}")

		n_elements = int(elements_header.strip().split()[1])
		_skip_header_lines(in_file, 4)

		# Parse elements first. The export format typically starts with:
		# TriIndex, Node1, Node2, Node3, RegCode, ...requested columns...
		pending_rows: list[tuple[int, int, int, int, int, list[str]]] = []
		for _ in range(n_elements):
			row = in_file.readline().split(sep=",")
			if len(row) < 6:
				continue
			try:
				tri_index = int(row[0])
				n1 = int(row[1])
				n2 = int(row[2])
				n3 = int(row[3])
				reg_code = int(row[4])
			except ValueError:
				continue
			if reg_code <= 0:
				continue
			regions.ensure_region(reg_code)
			pending_rows.append((tri_index, n1, n2, n3, reg_code, row[5:]))

		# NodesTable: keep node coordinates (for mesh + centroid fallback)
		nodes_header = _read_until_table_header(in_file, "NodesTable")
		if nodes_header is not None:
			n_nodes = int(nodes_header.strip().split()[1])
			_skip_header_lines(in_file, 4)
			for _ in range(n_nodes):
				row = in_file.readline().split(sep=",")
				if len(row) < 3:
					continue
				try:
					node_id = int(row[0])
					x = float(row[1])
					y = float(row[2])
				except ValueError:
					continue
				regions.node_xy[int(node_id)] = (float(x), float(y))

		# RegionsTable: map reg_code->region_name if present
		regions_header = _read_until_table_header(in_file, "RegionsTable")
		if regions_header is not None:
			n_regions = int(regions_header.strip().split()[1])
			_skip_header_lines(in_file, 4)
			for _ in range(n_regions):
				row = in_file.readline().split(sep=",")
				if len(row) < 2:
					continue
				try:
					reg_code = int(row[0])
				except ValueError:
					continue
				if 1 <= reg_code <= len(regions):
					regions[reg_code - 1].reg_code = reg_code
					regions[reg_code - 1].region_name = row[-1].strip()

	# Finalize elements by decoding requested columns.
	# We default to requesting X,Y,T,G,q so expected tail is [X,Y,T,G,q].
	for tri_index, n1, n2, n3, reg_code, tail in pending_rows:
		x = y = np.nan
		t = g = q = np.nan

		floats: list[float] = []
		for tok in tail:
			tok_s = tok.strip()
			if tok_s == "":
				continue
			try:
				floats.append(float(tok_s))
			except ValueError:
				# Some exports can include trailing text; ignore.
				continue

		if len(floats) >= 5:
			x, y, t, g, q = floats[0], floats[1], floats[2], floats[3], floats[4]
		elif len(floats) >= 3:
			# Fallback for exports without X,Y (requested: T,G,q)
			t, g, q = floats[0], floats[1], floats[2]
			cxy = regions._element_centroid_xy(n1, n2, n3)
			if cxy is not None:
				x, y = cxy

		regions[reg_code - 1].add_element(
			tri_index=tri_index,
			node_1=n1,
			node_2=n2,
			node_3=n3,
			reg_code=reg_code,
			x=float(x),
			y=float(y),
			t=float(t),
			g=float(g),
			q=float(q),
		)

	return regions


def get_thermal_data(
	mc,
	*,
	step: int = 1,
	variables: str = "RegCode,X,Y,T,G,q",
	clean_up: bool = True,
	filename: str | pathlib.Path | None = None,
) -> ThermalRegions:
	"""Export thermal FEA data from Motor-CAD and parse into ThermalRegions.

	By default, requests X/Y so plots have spatial coordinates. If your Motor-CAD
	export does not include X/Y, the parser falls back to centroid-from-NodesTable
	when possible.
	"""

	if filename is None:
		temp_filename = mcad_make_temp_txt_path(mc)
	else:
		temp_filename = pathlib.Path(filename)

	save_fea_text_export(
		mc,
		filename=temp_filename,
		first_step=int(step),
		final_step=int(step),
		columns=str(variables),
		sep=",",
	)
	regions = _parse_first_block_thermal_file(pathlib.Path(temp_filename))

	if clean_up and filename is None:
		try:
			temp_filename.unlink()
		except FileNotFoundError:
			pass

	return regions


def export_thermal_txt(
	mc,
	*,
	step: int = 1,
	variables: str = "RegCode,X,Y,T,G,q",
	filename: str | pathlib.Path,
	sep: str = ",",
) -> pathlib.Path:
	"""Export thermal FEA data to a txt file (no parsing).

	Use :func:`get_thermal_data_from_file` later when you actually need to parse/plot.
	"""

	export_path = pathlib.Path(filename)
	return save_fea_text_export(
		mc,
		filename=export_path,
		first_step=int(step),
		final_step=int(step),
		columns=str(variables),
		sep=str(sep),
	)


def get_thermal_data_from_file(filename: str | pathlib.Path, *, clean_up: bool = False) -> ThermalRegions:
	filename_p = pathlib.Path(filename)
	regions = _parse_first_block_thermal_file(filename_p)
	if clean_up:
		try:
			filename_p.unlink()
		except FileNotFoundError:
			pass
	return regions


def plot_mesh_thermal_fields(
	thermal_regions: ThermalRegions,
	region_names: Optional[Sequence[str]] = None,
	*,
	fields: Sequence[str] = ("t",),
	cmap: str = "jet",
	marker: str = ".",
	point_size: float = 4.0,
	vmin: float | None = None,
	vmax: float | None = None,
	field_clim: dict[str, tuple[float | None, float | None]] | None = None,
	show_mesh: bool = False,
	mesh_color: str = "k",
	mesh_linewidth: float = 0.2,
	mesh_alpha: float = 0.35,
	colorbar: bool = True,
	colorbar_location: str = "right",
	colorbar_size: str = "3%",
	colorbar_pad: float = 0.06,
	subplot_wspace: float = 0.35,
	subplot_hspace: float = 0.2,
	share_axes: bool = True,
    
	title_suffix: str = "",
):
	"""Plot element-wise thermal scalar fields over X/Y.

	fields supports: "t" (temperature), "g" (thermal conductivity), "q" (heat gen).
	"""

	import matplotlib.pyplot as plt

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
		# Always try to place colorbar OUTSIDE the axes box.
		# Preferred: axes_grid1 divider (robust, works with constrained layout).
		if make_axes_locatable is None:
			cb = plt.colorbar(mappable, ax=ax)
			if label:
				cb.set_label(label)
			return

		# Normalize aliases
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
			# Best-effort: put bar outside on the nearest side, then align to corner.
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
			# Fallback to right
			cb, _cax = _append("right", orientation="vertical")

		if label:
			cb.set_label(label)

	def _plot_mesh_edges(region: ThermalRegion, ax):
		if not bool(show_mesh):
			return
		if mtri is None:
			raise RuntimeError("matplotlib.tri is required for mesh plotting")
		if not getattr(thermal_regions, "node_xy", None):
			raise ValueError(
				"NodesTable coordinates not available (thermal_regions.node_xy is empty). "
				"Re-export thermal data including NodesTable."
			)

		node_to_local: dict[int, int] = {}
		xs: list[float] = []
		ys: list[float] = []
		triangles: list[tuple[int, int, int]] = []

		def _get_local(node_id: int):
			if int(node_id) in node_to_local:
				return node_to_local[int(node_id)]
			xy = thermal_regions.node_xy.get(int(node_id))
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
		"t": (lambda r: r.get_t(), "Temperature"),
		"g": (lambda r: r.get_g(), "Thermal conductivity"),
		"q": (lambda r: r.get_q(), "Heat generation"),
	}

	unknown = [f for f in fields if f not in field_getters]
	if unknown:
		raise ValueError(f"Unknown fields: {unknown}. Supported: {sorted(field_getters.keys())}")

	if region_names is not None:
		region_names_set = set(region_names)
	else:
		region_names_set = None

	results = []
	for region in (thermal_regions[i] for i in range(len(thermal_regions))):
		if region.get_number_elements() <= 0:
			continue
		if region_names_set is not None and region.region_name not in region_names_set:
			continue

		ncols = max(1, len(fields))
		fig, ax = plt.subplots(1, ncols, sharex=share_axes, sharey=share_axes)
		try:
			fig.subplots_adjust(wspace=float(subplot_wspace), hspace=float(subplot_hspace))
		except Exception:
			pass
		if ncols == 1:
			ax = [ax]

		title = f"{region.region_name}" if region.region_name else f"reg_code={region.reg_code}"
		if title_suffix:
			title = f"{title} {title_suffix}".strip()
		fig.suptitle(title)

		x = region.get_x()
		y = region.get_y()

		for j, field in enumerate(fields):
			getter, label = field_getters[field]
			values = getter(region)
			if field_clim is not None and field in field_clim:
				vmin_j, vmax_j = field_clim[field]
			else:
				vmin_j, vmax_j = vmin, vmax
			_plot_mesh_edges(region, ax[j])
			sc = ax[j].scatter(
				x,
				y,
				c=values,
				s=point_size,
				marker=marker,
				cmap=cmap,
				vmin=vmin_j,
				vmax=vmax_j,
				zorder=2,
			)
			_add_colorbar(ax[j], sc, loc=colorbar_location, label=None)
			ax[j].set_title(label)
			ax[j].set_aspect("equal", adjustable="box")

		results.append((fig, ax))

	return results


def interactive_mesh_thermal_fields_plot(
	thermal_regions: ThermalRegions,
	region_names: Optional[Sequence[str]] = None,
	*,
	fields: Sequence[str] = ("t",),
	cmap: str = "jet",
	marker: str = ".",
	point_size: float = 4.0,
	vmin: float | None = None,
	vmax: float | None = None,
	field_clim: dict[str, tuple[float | None, float | None]] | None = None,
	show_mesh: bool = False,
	mesh_color: str = "k",
	mesh_linewidth: float = 0.2,
	mesh_alpha: float = 0.35,
	colorbar: bool = True,
	colorbar_location: str = "right",
	colorbar_size: str = "3%",
	colorbar_pad: float = 0.06,
	subplot_wspace: float = 0.35,
	subplot_hspace: float = 0.2,
	share_axes: bool = True,
	title_suffix: str = "",
):
	"""Interactive (dropdown) thermal field plot.

	Renders a single figure and allows selecting the region via a dropdown.
	If ipywidgets is not available, falls back to plotting the first available region.
	"""

	import matplotlib.pyplot as plt

	try:
		import ipywidgets as widgets
		from IPython.display import display
	except Exception:
		widgets = None
		display = None

	# Filter regions
	if region_names is not None:
		region_names_set = set(region_names)
	else:
		region_names_set = None

	regions: list[ThermalRegion] = []
	for region in (thermal_regions[i] for i in range(len(thermal_regions))):
		if region.get_number_elements() <= 0:
			continue
		if region_names_set is not None and region.region_name not in region_names_set:
			continue
		regions.append(region)

	if not regions:
		raise ValueError("No regions to plot")

	def _region_label(r: ThermalRegion) -> str:
		name = (r.region_name or "").strip()
		if name:
			return name
		return f"reg_code={int(r.reg_code)}"

	def _plot_single(region: ThermalRegion):
		one = ThermalRegions()
		one.node_xy = dict(getattr(thermal_regions, "node_xy", {}) or {})
		one._regions = [region]
		return plot_mesh_thermal_fields(
			one,
			region_names=None,
			fields=fields,
			cmap=cmap,
			marker=marker,
			point_size=point_size,
			vmin=vmin,
			vmax=vmax,
			field_clim=field_clim,
			show_mesh=show_mesh,
			mesh_color=mesh_color,
			mesh_linewidth=mesh_linewidth,
			mesh_alpha=mesh_alpha,
			colorbar=colorbar,
			colorbar_location=colorbar_location,
			colorbar_size=colorbar_size,
			colorbar_pad=colorbar_pad,
			subplot_wspace=subplot_wspace,
			subplot_hspace=subplot_hspace,
			share_axes=share_axes,
			title_suffix=title_suffix,
		)[0]

	def _plot_all(regions_to_plot: Sequence[ThermalRegion]):
		all_region = ThermalRegion()
		all_region.region_name = "ALL"
		all_region.reg_code = 0
		for r in regions_to_plot:
			all_region.elements.extend(list(getattr(r, "elements", []) or []))
		return _plot_single(all_region)

	if widgets is None or display is None:
		fig, ax = _plot_single(regions[0])
		plt.show()
		return fig, ax

	out = widgets.Output()
	options = [("all", -1)] + [(_region_label(r), i) for i, r in enumerate(regions)]
	dd = widgets.Dropdown(options=options, value=-1, description="region")

	def _update(index: int):
		with out:
			out.clear_output(wait=True)
			idx = int(index)
			if idx < 0:
				fig, ax = _plot_all(regions)
			else:
				fig, ax = _plot_single(regions[idx])
			plt.show()

	display(widgets.HBox([dd]), out)
	widgets.interactive_output(_update, {"index": dd})
	_update(dd.value)
	return dd, out
