from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import configparser


@dataclass(frozen=True)
class GraphSpec:
        """Lightweight spec for a Motor-CAD graph entry parsed from a *.ini.

        Notes
        -----
        - The INI section name is treated as the graph name.
        - This module intentionally treats the INI as a static catalog (name, DataType,
            and optional Legend). It does not read XValue/YValue arrays from the INI.
        - Field names in Motor-CAD INIs are not perfectly consistent across versions,
            so parsing is best-effort.
        """

        name: str
        data_type: str
        legend: str = ""


def _read_graph_ini(path: str | Path) -> configparser.ConfigParser:
    ini_path = Path(path)
    if not ini_path.exists():
        raise FileNotFoundError(str(ini_path))

    # Motor-CAD INIs can be large; keep parsing simple and predictable.
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    # Preserve case of keys (Motor-CAD uses specific capitalization).
    parser.optionxform = str  # type: ignore[assignment]

    # Motor-CAD INIs are often ANSI/UTF-8 without BOM; try a few Windows-friendly fallbacks.
    raw = ini_path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp949", "latin1"):
        try:
            text = raw.decode(enc)
            parser.read_string(text)
            return parser
        except Exception:
            continue

    # Last resort: decode with replacement so we can still recover section names.
    parser.read_string(raw.decode("utf-8", errors="replace"))
    return parser


def iter_graph_specs(path: str | Path) -> Iterable[GraphSpec]:
    """Yield GraphSpec entries from a Motor-CAD testGraph.ini-like file."""

    parser = _read_graph_ini(path)
    for section in parser.sections():
        data_type = (parser.get(section, "DataType", fallback="") or "").strip()
        legend = (parser.get(section, "Legend", fallback="") or "").strip()
        yield GraphSpec(name=str(section).strip(), data_type=data_type, legend=legend)


def graph_type_map(path: str | Path) -> dict[str, str]:
    """Return a mapping: graph name -> DataType.

    Intended usage
    --------------
    Use a single, baseline testGraph.ini as a catalog of graph names and their
    DataType. Actual waveform data should be fetched from Motor-CAD via API.
    """

    out: dict[str, str] = {}
    for spec in iter_graph_specs(path):
        if spec.name and spec.name not in out:
            out[spec.name] = spec.data_type
    return out


def list_graph_names(
    path: str | Path,
    *,
    data_type: Optional[str] = None,
    contains: Optional[Sequence[str]] = None,
) -> list[str]:
    """List graph names from INI, optionally filtered by data_type and substring(s)."""

    contains_norm = None
    if contains:
        contains_norm = [c.lower() for c in contains if str(c).strip()]

    names: list[str] = []
    for spec in iter_graph_specs(path):
        if data_type is not None and spec.data_type.lower() != str(data_type).lower():
            continue
        if contains_norm is not None:
            hay = (spec.name + " " + spec.legend).lower()
            if not any(tok in hay for tok in contains_norm):
                continue
        names.append(spec.name)
    return names


def list_magnetic_graph_names(path: str | Path, *, contains: Optional[Sequence[str]] = None) -> list[str]:
    return list_graph_names(path, data_type="MagneticDataSource", contains=contains)


def list_fea_path_graph_names(path: str | Path, *, contains: Optional[Sequence[str]] = None) -> list[str]:
    return list_graph_names(path, data_type="FEAPathDataSource", contains=contains)


def _candidate_graph_names(name: str) -> list[str]:
    """Generate common Motor-CAD naming variants.

    Many Motor-CAD INIs contain names like 'BackEMFPh1_M' while the API often accepts
    'BackEMFPh1'. We try a few variants to be robust.
    """

    s = str(name).strip()
    if not s:
        return []

    candidates = [s]

    # Strip a common suffix
    if s.endswith("_M"):
        candidates.append(s[:-2])
    else:
        candidates.append(s + "_M")

    # Some INIs include variant numbering
    if s.endswith("_1_M"):
        candidates.append(s.replace("_1_M", "_M"))
        candidates.append(s.replace("_1_M", ""))

    # De-dup while preserving order
    out: list[str] = []
    for c in candidates:
        if c and c not in out:
            out.append(c)
    return out


def get_graph_xy(
    mc,
    graph_name: str,
    *,
    data_type: Optional[str] = None,
    ini_path: str | Path | None = None,
):
    """Fetch an (x,y) graph from Motor-CAD.

    Parameters
    ----------
    mc:
        ansys.motorcad.core MotorCAD instance
    graph_name:
        Graph identifier.
    data_type:
        If provided, chooses the correct API: 'MagneticDataSource' -> get_magnetic_graph,
        'FEAPathDataSource' -> get_fea_graph.
    ini_path:
        If provided and data_type is None, DataType is inferred from the INI.
        The INI is used only as a catalog; no waveform values are read from it.

    Returns
    -------
    (x, y)
    """

    dt = str(data_type).strip() if data_type is not None else ""
    if not dt and ini_path is not None:
        # Infer from ini
        for spec in iter_graph_specs(ini_path):
            if spec.name == graph_name:
                dt = spec.data_type
                break

    dt_lower = dt.lower()
    if dt_lower == "feapathdatasource":
        # For FEA path graphs Motor-CAD exposes get_fea_graph().
        return mc.get_fea_graph(graph_name)

    # Default: magnetic graph
    last_err: Exception | None = None
    for cand in _candidate_graph_names(graph_name):
        try:
            return mc.get_magnetic_graph(cand)
        except Exception as e:
            last_err = e

    if last_err is not None:
        raise last_err
    raise ValueError("graph_name is empty")
