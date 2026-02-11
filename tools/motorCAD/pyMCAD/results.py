from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence


DEFAULT_MES_KIND_ALIASES: dict[str, tuple[str, ...]] = {
	"OnLoadLoss": ("onloadloss", "on_load_loss"),
	"OnLoadTorque": ("onloadtorque", "on_load_torque"),
	"StaticLoad": ("staticload", "static_load"),
	"StaticOC": ("staticoc", "static_oc", "staticopen", "static_open"),
	"Thermal": ("thermal", "therm"),
	"Centrifugal": ("centrifugal",),
	"Cogging": ("cogging",),
}


@dataclass(frozen=True)
class MesSearchResult:
	mes_path: pathlib.Path
	search_roots: tuple[pathlib.Path, ...]
	searched_dirs: tuple[pathlib.Path, ...]


def _get_current_mot_path(mc) -> Optional[pathlib.Path]:
	"""Best-effort currently-loaded .mot path.

	Motor-CAD exposes this in Motor-LAB variable namespace.
	"""
	try:
		mot_path = mc.get_variable("CurrentMotFilePath_MotorLAB")
	except Exception:
		mot_path = ""

	if not mot_path:
		return None

	try:
		p = pathlib.Path(str(mot_path))
		return p if p.suffix.lower() == ".mot" else p
	except Exception:
		return None


def find_latest_mes(
	mc=None,
	*,
	mot_path: str | os.PathLike | None = None,
	name_contains: str | None = None,
	result_dir_names: Sequence[str] = (
		"FEResultsData",
		"FEResultData",
		"FEAResultsData",
		"FE_ResultsData",
		"ResultsData",
	),
	search_roots: Iterable[str | os.PathLike] | None = None,
	include_immediate_subdirs: bool = True,
) -> pathlib.Path:
	"""Find the newest `.mes` generated for the active/selected `.mot`.

	Strategy:
	- Determine the `.mot` folder (either from `mot_path`, or from Motor-CAD via `mc`).
	- Look for common FEA results folders under that root.
	- Choose the newest `.mes` by modification time (optionally filtered by `name_contains`).

	Raises
	------
	FileNotFoundError
		If no matching `.mes` file is found.
	ValueError
		If neither `mot_path` nor `mc` is provided/usable.
	"""
	if mot_path is None:
		if mc is None:
			raise ValueError("Provide either mot_path=... or mc=MotorCAD instance")
		mot_p = _get_current_mot_path(mc)
		if mot_p is None:
			raise ValueError(
				"Unable to determine current .mot path from Motor-CAD; "
				"pass mot_path=... explicitly"
			)
	else:
		mot_p = pathlib.Path(mot_path)

	# Build list of candidate roots
	if search_roots is None:
		roots = [mot_p.parent]
	else:
		roots = [pathlib.Path(p) for p in search_roots]

	# In many Motor-CAD workflows, results are written under a project subfolder
	# (e.g. <parent>/<project_name>/FEResultsData). To support that without requiring
	# callers to hardcode the subfolder name, we optionally scan one level down.
	project_roots: list[pathlib.Path] = []
	for root in roots:
		project_roots.append(root)
		if bool(include_immediate_subdirs):
			try:
				for child in root.iterdir():
					if child.is_dir():
						project_roots.append(child)
			except Exception:
				# Best-effort: if permissions or missing directory, just skip.
				pass

	searched_dirs: list[pathlib.Path] = []
	candidates: list[pathlib.Path] = []

	name_contains_n = (str(name_contains).strip().lower() if name_contains else "")

	for root in project_roots:
		for dname in result_dir_names:
			d = root / str(dname)
			searched_dirs.append(d)
			if not d.exists() or not d.is_dir():
				continue
			for p in d.glob("*.mes"):
				if name_contains_n and name_contains_n not in p.name.lower():
					continue
				candidates.append(p)

	if not candidates:
		raise FileNotFoundError(
			"No .mes file found. Searched: "
			+ ", ".join(str(p) for p in searched_dirs)
		)

	# Pick newest by mtime
	return max(candidates, key=lambda p: p.stat().st_mtime)


def _classify_mes_kind(
	mes_path: pathlib.Path,
	*,
	kind_aliases: Optional[dict[str, Sequence[str]]] = None,
) -> str:
	name = mes_path.stem.lower()
	aliases = kind_aliases or DEFAULT_MES_KIND_ALIASES
	for kind, keys in aliases.items():
		for k in keys:
			if str(k).lower() in name:
				return str(kind)
	return "Other"


def list_mes_files(
	mc=None,
	*,
	mot_path: str | os.PathLike | None = None,
	result_dir_names: Sequence[str] = (
		"FEResultsData",
		"FEResultData",
		"FEAResultsData",
		"FE_ResultsData",
		"ResultsData",
	),
	search_roots: Iterable[str | os.PathLike] | None = None,
	include_immediate_subdirs: bool = True,
	kind_aliases: Optional[dict[str, Sequence[str]]] = None,
) -> dict[str, list[pathlib.Path]]:
	"""Return `.mes` files grouped by result kind.

	Groups include (by default): OnLoadLoss, OnLoadTorque, StaticLoad, StaticOC,
	Centrifugal, Cogging, and Other.

	Each list is sorted by modification time (newest first).
	"""
	# Reuse the same root/subdir scanning logic as find_latest_mes.
	# We implement it here directly so we can return *all* matches.
	if mot_path is None:
		if mc is None:
			raise ValueError("Provide either mot_path=... or mc=MotorCAD instance")
		mot_p = _get_current_mot_path(mc)
		if mot_p is None:
			raise ValueError(
				"Unable to determine current .mot path from Motor-CAD; "
				"pass mot_path=... explicitly"
			)
	else:
		mot_p = pathlib.Path(mot_path)

	if search_roots is None:
		roots = [mot_p.parent]
	else:
		roots = [pathlib.Path(p) for p in search_roots]

	project_roots: list[pathlib.Path] = []
	for root in roots:
		project_roots.append(root)
		if bool(include_immediate_subdirs):
			try:
				for child in root.iterdir():
					if child.is_dir():
						project_roots.append(child)
			except Exception:
				pass

	all_mes: list[pathlib.Path] = []
	for root in project_roots:
		for dname in result_dir_names:
			d = root / str(dname)
			if not d.exists() or not d.is_dir():
				continue
			all_mes.extend([p for p in d.glob("*.mes") if p.is_file()])

	grouped: dict[str, list[pathlib.Path]] = {}
	for p in all_mes:
		kind = _classify_mes_kind(p, kind_aliases=kind_aliases)
		grouped.setdefault(kind, []).append(p)

	# Ensure default kinds exist in output (even if empty)
	for k in list((kind_aliases or DEFAULT_MES_KIND_ALIASES).keys()) + ["Other"]:
		grouped.setdefault(k, [])

	for k, paths in grouped.items():
		paths.sort(key=lambda x: x.stat().st_mtime, reverse=True)

	return grouped


def find_latest_mes_by_kind(
	kind: str,
	mc=None,
	*,
	mot_path: str | os.PathLike | None = None,
	search_roots: Iterable[str | os.PathLike] | None = None,
	include_immediate_subdirs: bool = True,
	kind_aliases: Optional[dict[str, Sequence[str]]] = None,
) -> pathlib.Path:
	"""Find the newest `.mes` for a specific kind (e.g. "OnLoadLoss")."""
	mes_map = list_mes_files(
		mc,
		mot_path=mot_path,
		search_roots=search_roots,
		include_immediate_subdirs=include_immediate_subdirs,
		kind_aliases=kind_aliases,
	)
	paths = mes_map.get(str(kind), [])
	if not paths:
		raise FileNotFoundError(f"No .mes found for kind={kind!r}")
	return paths[0]


__all__ = [
	"MesSearchResult",
	"DEFAULT_MES_KIND_ALIASES",
	"find_latest_mes",
	"list_mes_files",
	"find_latest_mes_by_kind",
]
