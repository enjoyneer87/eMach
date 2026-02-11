from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Union

PathLike = Union[str, Path]


def find_files(
    root: PathLike,
    pattern: str = "*",
    *,
    recursive: bool = True,
    absolute: bool = True,
    sort: bool = True,
) -> List[str]:
    root_path = Path(root)
    if not root_path.exists():
        return []

    iterator = root_path.rglob(pattern) if recursive else root_path.glob(pattern)

    results: List[str] = []
    for p in iterator:
        try:
            if not p.is_file():
                continue
        except OSError:
            continue

        results.append(str(p.resolve()) if absolute else str(p.relative_to(root_path)))

    if sort:
        results.sort()
    return results


def find_first(root: PathLike, pattern: str, *, recursive: bool = True) -> str | None:
    files = find_files(root, pattern, recursive=recursive, absolute=True, sort=True)
    return files[0] if files else None


def find_many(
    roots: Sequence[PathLike],
    pattern: str,
    *,
    recursive: bool = True,
    absolute: bool = True,
    sort: bool = True,
) -> List[str]:
    out: List[str] = []
    for r in roots:
        out.extend(find_files(r, pattern, recursive=recursive, absolute=absolute, sort=False))
    if sort:
        out.sort()
    return out
