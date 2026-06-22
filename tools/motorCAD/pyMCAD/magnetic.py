from __future__ import annotations

import pathlib

from ._export import (
    mcad_default_export_dir,
    mcad_make_temp_txt_path,
)
from .magnetic_parse import (
    _parse_first_block_magnetic_file,
    _parse_magnetic_timeseries_txt,
)
from .magnetic_export import (
    export_magnetic_txt,
    infer_magnetic_final_step,
    _mcad_value_to_int,
)

from .magnetic_plot import (
    export_magnetic_timeseries_gif,
    export_magnetic_snapshot_svgs,
    interactive_magnetic_plot,
    interactive_magnetic_quiver,
)

from .magnetic_h5 import (
    export_magnetic_timeseries_h5,
    export_magnetic_snapshot_h5,
    load_magnetic_snapshot_h5_arrays,
    load_magnetic_timeseries_h5_arrays,
    load_magnetic_timeseries_h5_datasets,
    read_magnetic_h5_format,
    inspect_magnetic_timeseries_h5,
    diagnose_magnetic_h5_mesh_motion,
    _magnetic_regions_from_snapshot_h5,
    MagneticRegionsTimeSeriesH5,
)

from .magnetic_model import (  # noqa: E402
    MagElement,
    MagneticRegion,
    MagneticRegions,
    MagneticRegionsTimeSeries,
)

_mcad_default_export_dir = mcad_default_export_dir
_mcad_make_temp_txt_path = mcad_make_temp_txt_path


def get_magnetic_data(
    mc,
    first_step=1,
    final_step: int | None = 1,
    *,
    filename: str | pathlib.Path | None = None,
    clean_up: bool = True,
    auto_final_step: bool = True,
) -> MagneticRegions:
    """Export Motor-CAD electromagnetic element data and return MagneticRegions (first block).

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

    export_path = export_magnetic_txt(
        mc,
        first_step=int(first_step),
        final_step=(None if final_step is None else int(final_step)),
        filename=export_path,
        columns="RegCode,Bx,By,A,J,Je",
        sep=",",
        auto_final_step=bool(auto_final_step),
    )

    mag_regions = get_magnetic_data_from_file(export_path, clean_up=False)

    if clean_up and is_temp:
        try:
            export_path.unlink()
        except FileNotFoundError:
            pass
    elif is_temp:
        print(f"Temporary file not deleted: {export_path}")

    return mag_regions


def get_magnetic_data_from_file(filename, clean_up=False, *, step: int | None = None) -> MagneticRegions:
    """Load magnetic data from an existing export file.

    Supports:
    - `.txt`: parses first block into `MagneticRegions`
    - `.h5`: loads snapshot format, or for timeseries `.h5` loads a specific step (defaults to first)
    """

    filename = pathlib.Path(filename)
    suf = filename.suffix.lower()

    if suf in {".h5", ".hdf5"}:
        fmt = read_magnetic_h5_format(filename).lower()
        # Order matters: timeseries formats may include the substring "static_mesh".
        if "timeseries" in fmt:
            ts = MagneticRegionsTimeSeriesH5(filename)
            steps = ts.steps
            if not steps:
                raise ValueError(f"Empty timeseries h5: {filename}")
            use_step = int(steps[0] if step is None else step)
            mag_regions = ts.by_step[use_step]
        elif "static" in fmt or "snapshot" in fmt:
            mag_regions = _magnetic_regions_from_snapshot_h5(filename)
        else:
            raise ValueError(f"Unrecognized magnetic h5 format: {fmt}")

        if clean_up:
            try:
                filename.unlink()
            except FileNotFoundError:
                pass
        return mag_regions

    mag_regions = _parse_first_block_magnetic_file(filename)
    if clean_up:
        try:
            filename.unlink()
        except FileNotFoundError:
            pass
    return mag_regions


def get_magnetic_timeseries_from_file(
    filename,
    key="time_index",
    clean_up=False,
    max_blocks=None,
    verbose=False,
) -> MagneticRegionsTimeSeries:
    """Parse a Motor-CAD multi-step electromagnetic txt into MagneticRegionsTimeSeries."""

    filename = pathlib.Path(filename)
    suf = filename.suffix.lower()
    if suf in {".h5", ".hdf5"}:
        fmt = read_magnetic_h5_format(filename).lower()
        if "timeseries" in fmt:
            return MagneticRegionsTimeSeriesH5(filename)
        if "static" in fmt or "snapshot" in fmt:
            mr = _magnetic_regions_from_snapshot_h5(filename)
            ts1 = MagneticRegionsTimeSeries(by_step={1: mr}, meta={1: {"solution": None, "time_index": 1}})
            return ts1
        raise ValueError(f"Unrecognized magnetic h5 format: {fmt}")

    ts = _parse_magnetic_timeseries_txt(filename, key=key, max_blocks=max_blocks, verbose=verbose)

    if clean_up:
        try:
            filename.unlink()
        except FileNotFoundError:
            pass

    return ts


