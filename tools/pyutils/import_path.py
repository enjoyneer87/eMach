from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable


def _walk_parents(start: Path) -> Iterable[Path]:
    start = start.resolve()
    yield start
    yield from start.parents


def ensure_repo_root_on_path(
    start: str | Path | None = None,
    *,
    markers: tuple[str, ...] = ("tools", "tool", "pyAEDT"),
) -> Path:
    """Ensure repo root is on sys.path.

    Finds the nearest parent directory that contains any of *markers* as a child
    folder and inserts that directory into sys.path.

    This avoids hard-coded absolute paths and prevents shadowing issues like
    having multiple 'tools' packages.
    """
    here = Path(start).resolve() if start is not None else Path.cwd().resolve()

    for p in _walk_parents(here):
        if any((p / m).exists() for m in markers):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
            return p

    raise FileNotFoundError(f"Could not find repo root containing any of: {markers}")


def ensure_package_parent_on_path(package_dir_name: str, start: str | Path | None = None) -> Path:
    """Ensure the parent directory of a given package folder is on sys.path.

    Example: if you have '<repo>/pyAEDT', call ensure_package_parent_on_path('pyAEDT').
    """
    here = Path(start).resolve() if start is not None else Path.cwd().resolve()
    for p in _walk_parents(here):
        if (p / package_dir_name).is_dir():
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
            return p
    raise FileNotFoundError(f"Could not find a '{package_dir_name}' folder in any parent directory")
