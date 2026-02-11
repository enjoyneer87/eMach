from __future__ import annotations

import os
import pathlib
import re
import tempfile
from dataclasses import dataclass
from typing import Dict, Literal, Optional, Sequence


@dataclass(frozen=True)
class FEAProcessResult:
	mes_path: pathlib.Path
	mes_kind: str
	mag_export_path: Optional[pathlib.Path]
	mag_h5_path: Optional[pathlib.Path]
	mag_gif_path: Optional[pathlib.Path]
	mag_svg_path: Optional[pathlib.Path]
	mag_gif_paths: Dict[str, pathlib.Path]
	mag_svg_paths: Dict[str, pathlib.Path]
	loss_export_path: Optional[pathlib.Path]
	loss_svg_path: Optional[pathlib.Path]
	loss_svg_paths: Dict[str, pathlib.Path]
	thermal_export_path: Optional[pathlib.Path]
	thermal_svg_path: Optional[pathlib.Path]
	thermal_svg_paths: Dict[str, pathlib.Path]
	stress_export_path: Optional[pathlib.Path]
	stress_svg_path: Optional[pathlib.Path]
	stress_svg_paths: Dict[str, pathlib.Path]
	cogging_svg_path: Optional[pathlib.Path]


def _safe_stem(s: str, *, max_len: int = 80) -> str:
	s = re.sub(r"[^A-Za-z0-9._-]+", "_", str(s).strip())
	s = re.sub(r"_+", "_", s).strip("_")
	return s[: int(max_len)] if len(s) > int(max_len) else s


def _unique_path(path: pathlib.Path) -> pathlib.Path:
	"""Create a unique filename if `path` exists (timestamp + counter fallback)."""
	path = pathlib.Path(path)
	if not path.exists():
		return path

	base = path.with_suffix("")
	suffix = path.suffix

	for i in range(1, 1000):
		candidate = pathlib.Path(f"{base}_{i}{suffix}")
		if not candidate.exists():
			return candidate

	return pathlib.Path(tempfile.gettempdir()) / f"{_safe_stem(path.stem)}_{os.getpid()}{suffix}"

def process_fea_result_from_mes(
	mc,
	*,
	mes_path: str | os.PathLike,
	plot_mode: Literal["interactive", "gif", "none"] = "interactive",
	out_dir: str | os.PathLike | None = None,
	first_step: int = 1,
	final_step: int = 45,
	mag_columns: str = "RegCode,Bx,By,A,J",
	export_magnetic_h5: bool = False,
	mag_h5_mesh_coords: Literal["static", "by_step", "by_step_moving_nodes"] = "by_step",
	mag_h5_dtype: str = "float32",
	mag_h5_compression: str | None = "gzip",
	mag_h5_compression_opts: int | None = 4,
	loss_columns: Sequence[str] = ("Pt", "Phys", "Pj", "Peddy"),
	loss_step: int | None = None,
	loss_unit: str = "W/kg",
	thermal_step: int = 1,
	thermal_variables: str = "RegCode,X,Y,T,G,q",
	cmap: str = "jet",
	point_size: float = 2,
	gif_fps: int = 6,
	gif_quantity: str = "b",
	mag_quantities: Sequence[str] = ("b", "a", "j"),
	include_magnetic_export: bool = True,
	svg_dpi: int = 140,
) -> FEAProcessResult:
	"""Load a `.mes`, export FEA data, then plot (interactive) or export GIF.

	Behavior is inferred from the `.mes` filename (best-effort):
	- If name contains "thermal" -> exports thermal snapshot (not time series).
	- If name contains "loss" -> exports loss snapshot; optionally also magnetic time series.
	- Otherwise -> exports magnetic time series and plots/exports GIF.
	"""
	from .magnetic import mcad_default_export_dir
	from .results import _classify_mes_kind
	from .thermal import get_thermal_data
	from .loss import get_element_loss_fields
	mes_p = pathlib.Path(mes_path)
	if not mes_p.exists():
		raise FileNotFoundError(f".mes not found: {mes_p}")

	mes_kind = _classify_mes_kind(mes_p)
	name_l = mes_p.stem.lower()
	wants_thermal = "thermal" in name_l
	wants_loss = ("loss" in name_l) or (mes_kind == "OnLoadLoss")
	# In this workflow, only OnLoadTorque is treated as a true transient/time-series export.
	# (Most other result types are effectively snapshots for post-processing purposes.)
	wants_transient = (mes_kind == "OnLoadTorque") or ("onloadtorque" in name_l)
	# Static* results are typically snapshots (single state), not time series
	# and often do not include the multi-step headers that the time-series parser expects.
	wants_magnetic_snapshot = mes_kind in {"StaticLoad", "StaticOC"}
	magnetic_is_snapshot = bool(wants_magnetic_snapshot)
	wants_mechanical = (mes_kind == "Centrifugal") or ("stress" in name_l) or ("mech" in name_l)
	wants_cogging = (mes_kind == "Cogging") or ("cogging" in name_l)
	# Only run magnetic export for magnetic-type results.
	# Loss/Thermal/Mechanical .mes files are snapshots and should not go through
	# the magnetic time-series pipeline.
	wants_magnetic_transient = (
		bool(include_magnetic_export)
		and wants_transient
		and (not wants_thermal)
		and (not wants_loss)
		and (not wants_mechanical)
	)
	wants_magnetic = wants_magnetic_transient or bool(wants_magnetic_snapshot)

	if out_dir is None:
		export_dir = pathlib.Path(mcad_default_export_dir(mc))
	else:
		export_dir = pathlib.Path(out_dir)
	export_dir.mkdir(parents=True, exist_ok=True)

	# 1) Load into GUI
	mc.load_fea_result(str(mes_p), 1)

	export_only = (str(plot_mode).lower().strip() == "none")

	# 2) Thermal snapshot export (NOT time series)
	thermal_export_path: Optional[pathlib.Path] = None
	thermal_svg_path: Optional[pathlib.Path] = None
	thermal_svg_paths: dict[str, pathlib.Path] = {}
	if wants_thermal:
		from .thermal import export_thermal_txt, get_thermal_data_from_file

		thermal_base = export_dir / f"Thermal_{_safe_stem(mes_p.stem)}.txt"
		thermal_export_path = _unique_path(thermal_base)
		thermal_export_path = export_thermal_txt(
			mc,
			step=int(thermal_step),
			variables=str(thermal_variables),
			filename=thermal_export_path,
		)

		thermal_regions = None
		if not export_only:
			thermal_regions = get_thermal_data_from_file(thermal_export_path, clean_up=False)

		if plot_mode == "interactive" and thermal_regions is not None:
			from .thermal import interactive_mesh_thermal_fields_plot
			interactive_mesh_thermal_fields_plot(
				thermal_regions,
				fields=("t", "g", "q"),
				show_mesh=True,
				mesh_alpha=0.25,
				colorbar_location="top",
				title_suffix=f"({mes_p.stem})",
			)
		elif plot_mode == "gif" and thermal_regions is not None:
			from .thermal import export_thermal_svgs
			thermal_svg_paths = export_thermal_svgs(
				thermal_regions,
				out_dir=export_dir,
				stem=str(mes_p.stem),
				fields=("t", "g", "q"),
				cmap=cmap,
				point_size=float(point_size),
				dpi=int(svg_dpi),
				show_mesh=True,
				mesh_alpha=0.25,
				colorbar_location="top",
			)
			thermal_svg_path = next(iter(thermal_svg_paths.values()), None)

	# 2.5) Mechanical (stress) snapshot export (NOT time series)
	stress_export_path: Optional[pathlib.Path] = None
	stress_svg_path: Optional[pathlib.Path] = None
	stress_svg_paths: dict[str, pathlib.Path] = {}
	if wants_mechanical:
		from .stress import export_stress_txt, get_stress_data_from_file

		stress_base = export_dir / f"Stress_{_safe_stem(mes_p.stem)}.txt"
		stress_export_path = _unique_path(stress_base)
		stress_export_path = export_stress_txt(mc, filename=stress_export_path)

		stress_regions = None
		if not export_only:
			stress_regions = get_stress_data_from_file(stress_export_path, clean_up=False)

		if plot_mode == "interactive" and stress_regions is not None:
			from .stress import interactive_mesh_stress_fields_plot
			interactive_mesh_stress_fields_plot(
				stress_regions,
				fields=("svm", "sp1", "sp2"),
				show_mesh=True,
				mesh_alpha=0.25,
				colorbar_location="top",
				title_suffix=f"({mes_p.stem})",
			)
		elif plot_mode == "gif" and stress_regions is not None:
			from .stress import export_stress_svgs
			stress_svg_paths = export_stress_svgs(
				stress_regions,
				out_dir=export_dir,
				stem=str(mes_p.stem),
				fields=("svm", "sp1", "sp2", "sx", "sy", "txy"),
				cmap=cmap,
				point_size=float(point_size),
				dpi=int(svg_dpi),
				show_mesh=True,
				mesh_alpha=0.25,
				colorbar_location="top",
			)
			stress_svg_path = next(iter(stress_svg_paths.values()), None)

	# 3) Export + parse magnetic time series (if requested)
	mag_export_path: Optional[pathlib.Path] = None
	mag_h5_path: Optional[pathlib.Path] = None
	mag_gif_path: Optional[pathlib.Path] = None
	mag_svg_path: Optional[pathlib.Path] = None
	mag_gif_paths: dict[str, pathlib.Path] = {}
	mag_svg_paths: dict[str, pathlib.Path] = {}
	if wants_magnetic:
		from .magnetic import (
			export_magnetic_txt,
			export_magnetic_snapshot_svgs,
			export_magnetic_timeseries_gif,
			export_magnetic_timeseries_h5,
			export_magnetic_snapshot_h5,
			get_magnetic_data_from_file,
			get_magnetic_timeseries_from_file,
			interactive_magnetic_plot,
			interactive_magnetic_quiver,
		)
		from .b_locus import interactive_b_locus_field_plot

		mag_base = export_dir / f"Mag_{_safe_stem(mes_p.stem)}.txt"
		mag_export_path = _unique_path(mag_base)
		# For transient: export a range. For snapshot: export a single step.
		_step0 = int(first_step)
		_step1 = int(final_step) if wants_magnetic_transient else int(first_step)
		mag_export_path = export_magnetic_txt(
			mc,
			first_step=int(_step0),
			final_step=int(_step1),
			filename=mag_export_path,
			columns=str(mag_columns),
		)

		# If we're not plotting/exporting GIF/SVG/H5, don't parse now.
		needs_parse = (not export_only) or bool(export_magnetic_h5)
		if not needs_parse:
			# return with txt only (mag_export_path is set)
			pass
		else:
			ts = get_magnetic_timeseries_from_file(mag_export_path, key="time_index", verbose=False)

			# If the export isn't a true time series (common for StaticLoad/StaticOC),
			# fall back to single-block parsing.
			if len(ts) == 0:
				magnetic_is_snapshot = True

			# Optional: export to HDF5 once (no re-parse later)
			if bool(export_magnetic_h5):
				mag_h5_path = _unique_path(export_dir / f"Mag_{_safe_stem(mes_p.stem)}.h5")
				if (not magnetic_is_snapshot) and bool(wants_magnetic_transient) and len(ts) > 0:
					mag_h5_path = export_magnetic_timeseries_h5(
						ts,
						mag_h5_path,
						mesh_coords=str(mag_h5_mesh_coords),
						dtype=str(mag_h5_dtype),
						compression=mag_h5_compression,
						compression_opts=mag_h5_compression_opts,
					)
				else:
					# Snapshot: parse single-block regions and store a 1D fields layout
					mr_h5 = get_magnetic_data_from_file(mag_export_path, clean_up=False)
					mag_h5_path = export_magnetic_snapshot_h5(
						mr_h5,
						mag_h5_path,
						dtype=str(mag_h5_dtype),
						compression=mag_h5_compression,
						compression_opts=mag_h5_compression_opts,
					)

			if not magnetic_is_snapshot and wants_magnetic_transient:
				if plot_mode == "interactive":
					interactive_magnetic_plot(ts, quantity=gif_quantity, s=point_size, cmap=cmap)
					interactive_magnetic_quiver(ts, stride=1, scale=1, normalize=False)
					interactive_b_locus_field_plot(ts)
				elif plot_mode == "gif":
					for q in tuple(mag_quantities):
						q_s = str(q).lower().strip()
						gif_path = _unique_path(export_dir / f"Mag_{q_s}_{_safe_stem(mes_p.stem)}.gif")
						mag_gif_paths[q_s] = export_magnetic_timeseries_gif(
							ts,
							gif_path,
							quantity=q_s,
							s=point_size,
							cmap=cmap,
							fps=gif_fps,
						)
						if mag_gif_path is None:
							mag_gif_path = mag_gif_paths[q_s]
			else:
				# Snapshot magnetic export: parse first block and plot/save a static figure.
				mr = get_magnetic_data_from_file(mag_export_path, clean_up=False)
				if plot_mode == "interactive":
					# Simple static plots (no step slider)
					try:
						mr.plot(quantity=gif_quantity, cmap=cmap, s=point_size)
					except Exception:
						pass
					try:
						mr.plot_quiver(stride=1, scale=1, normalize=False)
					except Exception:
						pass
				elif plot_mode == "gif":
					mag_svg_paths = export_magnetic_snapshot_svgs(
						mr,
						out_dir=export_dir,
						stem=str(mes_p.stem),
						quantities=tuple(mag_quantities),
						cmap=cmap,
						point_size=float(point_size),
						dpi=int(svg_dpi),
					)
					mag_svg_path = next(iter(mag_svg_paths.values()), None)

	# 4) Optional: loss fields (snapshot)
	loss_export_path: Optional[pathlib.Path] = None
	loss_svg_path: Optional[pathlib.Path] = None
	loss_svg_paths: dict[str, pathlib.Path] = {}
	if wants_loss:
		if loss_step is None:
			loss_step = int(final_step)

		from .loss import export_element_loss_txt, get_element_loss_fields_from_file

		loss_base = export_dir / f"LossElement_{_safe_stem(mes_p.stem)}.txt"
		loss_export_path = _unique_path(loss_base)
		loss_export_path = export_element_loss_txt(
			mc,
			filename=loss_export_path,
			step=int(loss_step),
			columns=tuple(loss_columns),
		)

		loss_fields = None
		if not export_only:
			loss_fields = get_element_loss_fields_from_file(loss_export_path, unit=str(loss_unit), clean_up=False)

		if plot_mode == "interactive" and loss_fields is not None:
			from .loss import interactive_loss_fields_plot
			interactive_loss_fields_plot(loss_fields, cmap=cmap, s=point_size)
		elif plot_mode == "gif" and loss_fields is not None:
			from .loss import export_loss_svgs
			loss_svg_paths = export_loss_svgs(
				loss_fields,
				out_dir=export_dir,
				stem=str(mes_p.stem),
				cmap=cmap,
				point_size=float(point_size),
				dpi=int(svg_dpi),
				clip_percentiles=(1.0, 99.0),
			)
			loss_svg_path = loss_svg_paths.get("Pt") or next(iter(loss_svg_paths.values()), None)

	# 5) Cogging waveform (snapshot-like)
	cogging_svg_path: Optional[pathlib.Path] = None
	if wants_cogging and (not export_only):
		from .melec_req_check import plot_cogging_torque_waveform
		if plot_mode == "interactive":
			plot_cogging_torque_waveform(mc)
		elif plot_mode == "gif":
			fig, _ax = plot_cogging_torque_waveform(mc)
			cogging_svg_path = _unique_path(export_dir / f"Cogging_{_safe_stem(mes_p.stem)}.svg")
			fig.savefig(cogging_svg_path, dpi=int(svg_dpi))
			try:
				import matplotlib.pyplot as plt
				plt.close(fig)
			except Exception:
				pass

	return FEAProcessResult(
		mes_path=mes_p,
		mes_kind=str(mes_kind),
		mag_export_path=mag_export_path,
		mag_h5_path=mag_h5_path,
		mag_gif_path=mag_gif_path,
		mag_svg_path=mag_svg_path,
		mag_gif_paths=dict(mag_gif_paths),
		mag_svg_paths=dict(mag_svg_paths),
		loss_export_path=loss_export_path,
		loss_svg_path=loss_svg_path,
		loss_svg_paths=dict(loss_svg_paths),
		thermal_export_path=thermal_export_path,
		thermal_svg_path=thermal_svg_path,
		thermal_svg_paths=dict(thermal_svg_paths),
		stress_export_path=stress_export_path,
		stress_svg_path=stress_svg_path,
		stress_svg_paths=dict(stress_svg_paths),
		cogging_svg_path=cogging_svg_path,
	)


__all__ = [
	"FEAProcessResult",
	"process_fea_result_from_mes",
]
