"""Magnetic FEA Motor-CAD API export functions.

Functions that interact with the Motor-CAD API to export electromagnetic data.
"""
from __future__ import annotations

import pathlib

from ._export import save_fea_text_export, mcad_make_temp_txt_path


def _mcad_value_to_int(raw) -> int | None:
    """Best-effort cast for Motor-CAD API return values to int."""

    val = raw
    if isinstance(val, tuple) and len(val) >= 1:
        # COM wrappers often return (ok, value) or (value, unit).
        val = val[-1]
    if isinstance(val, list) and len(val) >= 1:
        val = val[-1]

    try:
        out = int(float(val))
    except Exception:
        return None
    return out if out >= 0 else None


def infer_magnetic_final_step(mc, *, default_step: int = 1) -> int:
    """Infer a reasonable magnetic final step from Motor-CAD variables.

    The exact variable name can differ by Motor-CAD version/setup, so this
    checks several known candidates and falls back to `default_step`.
    """

    candidates = (
        "MagneticTransient_NumberOfTimeSteps",
        "MagneticTransientNumberOfTimeSteps",
        "NumberOfTimeSteps",
        "NumberofTimeSteps",
        "CyclePoints",
        "TorquePointsPerCycle",
        "MagneticTimeStepNumber",
    )

    for name in candidates:
        try:
            raw = mc.get_variable(name)
        except Exception:
            continue
        step = _mcad_value_to_int(raw)
        if step is not None and step > 0:
            return step

    return max(1, int(default_step))


def export_magnetic_txt(
    mc,
    *,
    first_step: int = 1,
    final_step: int | None = 1,
    filename: str | pathlib.Path,
    columns: str = "RegCode,Bx,By,A,J,Je",
    sep: str = ",",
    auto_final_step: bool = True,
) -> pathlib.Path:
    """Export magnetic FEA data to a txt file (no parsing).

    If `auto_final_step=True` and `final_step` is None/invalid, this function
    tries to infer the magnetic end step from Motor-CAD variables.
    """
    step0 = int(first_step)
    step1 = int(final_step) if final_step is not None else int(step0)
    if bool(auto_final_step) and step1 <= 0:
        step1 = infer_magnetic_final_step(mc, default_step=step0)
    if step1 < step0:
        step1 = step0

    return save_fea_text_export(
        mc,
        filename=filename,
        first_step=int(step0),
        final_step=int(step1),
        columns=str(columns),
        sep=str(sep),
    )
