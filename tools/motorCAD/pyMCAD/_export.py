from __future__ import annotations

import pathlib
import re
import tempfile
import uuid


def safe_stem(s: str, *, max_len: int = 80) -> str:
    """Return a filesystem-safe stem string."""
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", str(s).strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return s[: int(max_len)] if len(s) > int(max_len) else s


def unique_path(path: pathlib.Path) -> pathlib.Path:
    """Return `path` or a numbered variant if it already exists."""
    path = pathlib.Path(path)
    if not path.exists():
        return path

    base = path.with_suffix("")
    suffix = path.suffix
    for i in range(1, 1000):
        candidate = pathlib.Path(f"{base}_{i}{suffix}")
        if not candidate.exists():
            return candidate

    return pathlib.Path(tempfile.gettempdir()) / (
        f"{safe_stem(path.stem)}_{uuid.uuid4().hex}{suffix}"
    )


def ensure_text_export_path(filename: str | pathlib.Path) -> pathlib.Path:
    """Normalize a text export path and ensure its parent directory exists."""
    export_path = pathlib.Path(filename)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    if export_path.suffix.lower() != ".txt":
        export_path = export_path.with_suffix(".txt")
    return export_path


def mcad_default_export_dir(mc) -> pathlib.Path:
    """Best-effort default directory for Motor-CAD exports."""
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


def resolve_export_dir(
    *,
    mc=None,
    out_dir: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """Resolve and create the export directory for a workflow run."""
    if out_dir is None:
        if mc is None:
            raise ValueError("mc is required when out_dir is not provided")
        export_dir = mcad_default_export_dir(mc)
    else:
        export_dir = pathlib.Path(out_dir)

    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def mcad_make_temp_txt_path(mc) -> pathlib.Path:
    """Return a temporary txt export path near the active .mot when possible."""
    return mcad_default_export_dir(mc) / pathlib.Path(f"{uuid.uuid4()}.txt")


def save_fea_text_export(
    mc,
    *,
    filename: str | pathlib.Path,
    first_step: int,
    final_step: int,
    columns: str,
    sep: str = ",",
) -> pathlib.Path:
    """Shared wrapper around `mc.save_fea_data` for text exports."""
    export_path = ensure_text_export_path(filename)
    mc.save_fea_data(
        str(export_path),
        int(first_step),
        int(final_step),
        str(columns),
        "",
        str(sep),
    )
    return export_path