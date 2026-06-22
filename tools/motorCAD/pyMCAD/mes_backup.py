"""Backup .mes file discovery and export utilities for AC-loss workflows.

Provides helpers to locate Motor-CAD .mes files in FEResultsData_backup
directory trees and export them to text format via the Motor-CAD API.
"""
from __future__ import annotations

import pathlib
import re
from typing import Dict, List, Sequence, Tuple

from ._export import save_fea_text_export

# Default column set for magnetic FEA AC-loss export.
# Includes Hx, Hy, Mur beyond the basic set so magnetization M = B/mu0 - H
# can be computed for PEEC boundary current extraction.
EXPORT_COLUMNS: str = "RegCode,Bx,By,A,J,Je,Hx,Hy,Mur"

_SPEED_RE = re.compile(r"Speed_(\d+)RPM", re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _find_mes_in_folder(
    folder: pathlib.Path,
    mes_filename: str,
) -> pathlib.Path | None:
    """Search for a .mes file inside *folder* using a priority cascade.

    Priority:
      1. ``folder / mes_filename``
      2. ``folder / FEResultsData / mes_filename``
      3. Largest ``OnLoad*result*.mes`` anywhere under *folder*
      4. Largest ``*.mes`` anywhere under *folder*
    """
    candidate = folder / mes_filename
    if candidate.exists():
        return candidate

    candidate = folder / "FEResultsData" / mes_filename
    if candidate.exists():
        return candidate

    found = list(folder.rglob("OnLoad*result*.mes"))
    if found:
        return max(found, key=lambda p: p.stat().st_size)

    found = list(folder.rglob("*.mes"))
    if found:
        return max(found, key=lambda p: p.stat().st_size)

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def find_backup_roots(mot_path: str | pathlib.Path) -> List[pathlib.Path]:
    """Return FEResultsData_backup* directories for a .mot file, priority-ordered.

    Checks (in order):
      1. ``{mot_stem}/FEResultsData_backup``   (exact)
      2. ``{mot_stem}/FEResultsData_backup_*`` (versioned variants, sorted by name)
      3. ``{mot_parent}/FEResultsData_backup`` (sibling fallback)

    Args:
        mot_path: Path to the ``.mot`` Motor-CAD model file.

    Returns:
        Ordered list of existing backup root directories (may be empty).
    """
    mot_p = pathlib.Path(mot_path)
    model_dir = mot_p.parent / mot_p.stem
    roots: List[pathlib.Path] = []

    exact = model_dir / "FEResultsData_backup"
    if exact.exists():
        roots.append(exact)

    if model_dir.exists():
        for d in sorted(model_dir.iterdir()):
            if d.is_dir() and d.name.startswith("FEResultsData_backup_"):
                roots.append(d)

    alt = mot_p.parent / "FEResultsData_backup"
    if alt.exists() and alt not in roots:
        roots.append(alt)

    return roots


def find_backup_mes_files(
    backup_root: str | pathlib.Path,
    speed_list: Sequence[int],
    *,
    mes_filename: str = "OnLoadTorque_result_1.mes",
    prefer_hybrid: bool = True,
    latest_only: bool = True,
) -> Dict[int, pathlib.Path] | Dict[int, List[pathlib.Path]]:
    """Search a FEResultsData_backup tree for speed-matched .mes files.

    Supported folder structures:
    * ``Speed_{rpm}RPM/FEResultsData/{mes_filename}``  (Ref model)
    * ``Hybrid_*Speed_{rpm}RPM_*/{mes_filename}``      (HalfSC model)
    * ``*Speed_{rpm}RPM*/*``                           (fallback glob)

    Args:
        backup_root:   Root directory to search.
        speed_list:    Speeds [RPM] to find.
        mes_filename:  Preferred .mes filename.
        prefer_hybrid: If True, ``Hybrid_`` folders rank above others.
        latest_only:   If True, return only the most recent folder per speed.

    Returns:
        ``{speed_rpm: Path}`` when *latest_only* is True,
        ``{speed_rpm: [Path, ...]}`` when False.
    """
    backup_root = pathlib.Path(backup_root)
    if not backup_root.exists():
        return {}

    speed_set = set(speed_list)
    candidates: Dict[int, List[Tuple]] = {s: [] for s in speed_list}

    for folder in backup_root.iterdir():
        if not folder.is_dir():
            continue
        m = _SPEED_RE.search(folder.name)
        if not m:
            continue
        speed_val = int(m.group(1))
        if speed_val not in speed_set:
            continue

        mes_file = _find_mes_in_folder(folder, mes_filename)
        if mes_file is None:
            continue

        is_hybrid = folder.name.lower().startswith("hybrid")
        is_ts = folder.name.lower().startswith("ts")
        candidates[speed_val].append((folder, mes_file, is_hybrid, is_ts))

    for spd in candidates:
        candidates[spd].sort(key=lambda t: (
            0 if (prefer_hybrid and t[2]) else (2 if t[3] else 1),
            -t[0].stat().st_mtime,
        ))

    if latest_only:
        return {s: paths[0][1] for s, paths in candidates.items() if paths}
    return {s: [p[1] for p in paths] for s, paths in candidates.items() if paths}


def find_all_backup_mes_files(
    backup_root: str | pathlib.Path,
    speed_list: Sequence[int],
    *,
    mes_filename: str = "OnLoadTorque_result_1.mes",
) -> Dict[str, Dict[int, pathlib.Path]]:
    """Search a backup tree for both Hybrid and FullFEA .mes files.

    Classifies results by folder prefix:
    * ``Hybrid_*`` → ``"hybrid"``
    * ``TS_*``     → ``"fullfea"``
    * others       → ``"hybrid"`` (Ref model convention: no Hybrid_ prefix)

    Args:
        backup_root:  Root directory to search.
        speed_list:   Speeds [RPM] to find.
        mes_filename: Preferred .mes filename.

    Returns:
        ``{"hybrid": {speed: Path}, "fullfea": {speed: Path}}``
    """
    backup_root = pathlib.Path(backup_root)
    if not backup_root.exists():
        return {"hybrid": {}, "fullfea": {}}

    speed_set = set(speed_list)
    candidates: Dict[int, list] = {s: [] for s in speed_list}

    for folder in backup_root.iterdir():
        if not folder.is_dir():
            continue
        m = _SPEED_RE.search(folder.name)
        if not m:
            continue
        speed_val = int(m.group(1))
        if speed_val not in speed_set:
            continue

        mes_file = _find_mes_in_folder(folder, mes_filename)
        if mes_file is None:
            continue

        is_hybrid = folder.name.lower().startswith("hybrid")
        is_ts = folder.name.lower().startswith("ts")
        candidates[speed_val].append((folder, mes_file, is_hybrid, is_ts))

    result: Dict[str, Dict[int, pathlib.Path]] = {"hybrid": {}, "fullfea": {}}
    for spd, entries in candidates.items():
        if not entries:
            continue

        hybrid_entries = sorted(
            [e for e in entries if e[2]], key=lambda t: -t[0].stat().st_mtime
        )
        ts_entries = sorted(
            [e for e in entries if e[3]], key=lambda t: -t[0].stat().st_mtime
        )
        unknown_entries = sorted(
            [e for e in entries if not e[2] and not e[3]],
            key=lambda t: -t[0].stat().st_mtime,
        )

        # Hybrid: explicit Hybrid_ folders first; fall back to unknown (Ref convention)
        if hybrid_entries:
            result["hybrid"][spd] = hybrid_entries[0][1]
        elif unknown_entries:
            result["hybrid"][spd] = unknown_entries[0][1]

        if ts_entries:
            result["fullfea"][spd] = ts_entries[0][1]

    return result


def export_mes_to_txt(
    mc,
    mes_path: str | pathlib.Path,
    txt_out_path: str | pathlib.Path,
    *,
    first_step: int = 1,
    final_step: int = 128,
    columns: str = EXPORT_COLUMNS,
) -> pathlib.Path:
    """Load a .mes result into Motor-CAD and export to a text file.

    Wraps ``mc.load_fea_result`` + ``mc.save_fea_data`` in a single call.

    Args:
        mc:           Motor-CAD API object.
        mes_path:     Path to the ``.mes`` result file.
        txt_out_path: Destination ``.txt`` path (parent directory is created).
        first_step:   First time step to export.
        final_step:   Last time step to export.  Default 128 matches a full
                      electrical cycle at ``BackEMFPointsPerCycle=128`` or the
                      128-step hybrid transient used for PEEC AC-loss analysis.
        columns:      Comma-separated column names.  Default
                      ``EXPORT_COLUMNS`` includes Hx/Hy/Mur needed for
                      magnetization-current extraction.

    Returns:
        Resolved path of the exported text file.
    """
    mc.load_fea_result(str(pathlib.Path(mes_path)), 1)
    return save_fea_text_export(
        mc,
        filename=txt_out_path,
        first_step=int(first_step),
        final_step=int(final_step),
        columns=str(columns),
    )


__all__ = [
    "EXPORT_COLUMNS",
    "find_backup_roots",
    "find_backup_mes_files",
    "find_all_backup_mes_files",
    "export_mes_to_txt",
]
