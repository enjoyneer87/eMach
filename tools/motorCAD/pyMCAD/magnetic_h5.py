"""Magnetic FEA HDF5 export, load, and inspection functions.

Handles reading/writing Motor-CAD electromagnetic data in HDF5 format.
"""
from __future__ import annotations

import pathlib
from typing import Sequence

import numpy as np

from .magnetic_model import MagElement, MagneticRegion, MagneticRegions, MagneticRegionsTimeSeries


def export_magnetic_timeseries_h5(
    nts: MagneticRegionsTimeSeries,
    h5_path: str | pathlib.Path,
    *,
    dtype: str = "float32",
    compression: str | None = "gzip",
    compression_opts: int | None = 4,
    chunk_elements: int = 200_000,
    mesh_coords: str = "static",
    moving_region_name_prefixes: Sequence[str] | None = None,
    moving_reg_codes: Sequence[int] | None = None,
    moving_node_motion_tol_mm: float = 1e-4,
) -> pathlib.Path:
    """Export an already-parsed magnetic time series (`MagneticRegionsTimeSeries`) to HDF5.

    This avoids re-parsing the large text export later and is typically much smaller
    than the original `.txt` when using compression.

        Dataset layout
    ------------------
    - /steps: int32 [n_steps]
    - /meta/time_s, /meta/rotate_step, /meta/solution: float/int arrays when available
        - /mesh/node_id: int32 [n_nodes]
        - /mesh/node_x_mm, /mesh/node_y_mm: float32 [n_nodes] (static mesh)
        - /mesh/node_x_mm_by_step, /mesh/node_y_mm_by_step: float32 [n_steps, n_nodes] (moving mesh, optional)
        - /mesh/moving_node_indices: int32 [n_moving_nodes] (indices into node_id)
        - /mesh/node_x_mm_by_step_moving, /mesh/node_y_mm_by_step_moving: float32 [n_steps, n_moving_nodes]
    - /mesh/tri_index, /mesh/node_1, /mesh/node_2, /mesh/node_3, /mesh/reg_code
    - /fields/bx, /fields/by, /fields/b, /fields/a, /fields/j, /fields/je : [n_steps, n_elements]

        Notes
        -----
        - If `mesh_coords="static"`, node coordinates are stored once (reference step).
        - If `mesh_coords="by_step"`, node coordinates are stored for every step when available,
            allowing the H5-derived `MagneticRegions` to match the TXT-derived geometry.
        - If `mesh_coords="by_step_moving_nodes"`, only node coordinates for moving regions
            are stored per-step (rotor + default a2/a3/a4 name prefixes), and other nodes use
            the static fallback coordinates.
    """

    try:
        import h5py  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "h5py is required to write .h5 files. Install with: pip install h5py"
        ) from e

    import numpy as np

    h5_path = pathlib.Path(h5_path)
    h5_path.parent.mkdir(parents=True, exist_ok=True)

    steps = list(getattr(nts, "steps", []) or [])
    if not steps:
        raise ValueError("Empty time series")

    ref_step = int(steps[0])
    mr_ref = getattr(nts, "by_step")[ref_step]

    # Build a stable element list from the reference step
    ref_elements: list[MagElement] = []
    for region in getattr(mr_ref, "_regions", []) or []:
        ref_elements.extend(getattr(region, "elements", []) or [])
    if not ref_elements:
        raise ValueError("No elements found in reference step")

    tri_index = np.asarray([int(getattr(e, "tri_index")) for e in ref_elements], dtype=np.int32)
    node_1 = np.asarray([int(getattr(e, "node_1")) for e in ref_elements], dtype=np.int32)
    node_2 = np.asarray([int(getattr(e, "node_2")) for e in ref_elements], dtype=np.int32)
    node_3 = np.asarray([int(getattr(e, "node_3")) for e in ref_elements], dtype=np.int32)
    reg_code = np.asarray([int(getattr(e, "reg_code")) for e in ref_elements], dtype=np.int32)

    index_of_tri = {int(tri): i for i, tri in enumerate(tri_index.tolist())}
    n_el = int(tri_index.size)
    n_steps = int(len(steps))

    # Per-step quantities (float, typically)
    def _empty():
        return np.full((n_steps, n_el), np.nan, dtype=np.float32)

    bx_mat = _empty()
    by_mat = _empty()
    b_mat = _empty()
    a_mat = _empty()
    j_mat = _empty()
    je_mat = _empty()

    for si, step in enumerate(steps):
        mr = getattr(nts, "by_step")[int(step)]
        # Flatten elements for this step
        els: list[MagElement] = []
        for region in getattr(mr, "_regions", []) or []:
            els.extend(getattr(region, "elements", []) or [])
        for e in els:
            idx = index_of_tri.get(int(getattr(e, "tri_index")))
            if idx is None:
                continue
            # bx/by may be absent for older export formats (only |B| provided)
            bx = getattr(e, "bx", None)
            by = getattr(e, "by", None)
            if bx is not None and by is not None:
                bx_mat[si, idx] = float(bx)
                by_mat[si, idx] = float(by)
            # always try to store |B|
            try:
                b_mat[si, idx] = float(getattr(e, "b"))
            except Exception:
                pass
            # A, J, Je are expected in our default export spec
            try:
                a_mat[si, idx] = float(getattr(e, "a", 0.0) or 0.0)
            except Exception:
                pass
            try:
                j_mat[si, idx] = float(getattr(e, "j", 0.0) or 0.0)
            except Exception:
                pass
            try:
                je_mat[si, idx] = float(getattr(e, "je", 0.0) or 0.0)
            except Exception:
                pass

    def _infer_moving_reg_codes(mr: MagneticRegions) -> list[int]:
        # Best-effort: pick regions that likely rotate with rotor.
        # Default includes any region name containing "rotor" and name prefixes a2/a3/a4.
        prefixes = (
            tuple(str(s).strip().lower() for s in (moving_region_name_prefixes or ("a2", "a3", "a4")) if str(s).strip())
            or ("a2", "a3", "a4")
        )
        out_codes: set[int] = set()
        for idx, region in enumerate(getattr(mr, "_regions", []) or []):
            els = getattr(region, "elements", []) or []
            if not els:
                continue
            name = str(getattr(region, "region_name", "") or "").strip().lower()
            # Determine region code robustly
            rc = int(getattr(region, "reg_code", 0) or 0)
            if rc <= 0:
                try:
                    rc = int(getattr(els[0], "reg_code"))
                except Exception:
                    rc = int(idx + 1)
            if "rotor" in name:
                out_codes.add(int(rc))
                continue
            for p in prefixes:
                if name == p or name.startswith(p):
                    out_codes.add(int(rc))
                    break
        return sorted(out_codes)

    def _regions_name_map(mr: MagneticRegions) -> dict[int, str]:
        out: dict[int, str] = {}
        for idx, region in enumerate(getattr(mr, "_regions", []) or []):
            els = getattr(region, "elements", []) or []
            if not els:
                continue
            name = str(getattr(region, "region_name", "") or "").strip()
            if not name:
                continue
            rc = int(getattr(region, "reg_code", 0) or 0)
            if rc <= 0:
                try:
                    rc = int(getattr(els[0], "reg_code"))
                except Exception:
                    rc = int(idx + 1)
            out[int(rc)] = name
        return out

    mesh_coords_mode = str(mesh_coords or "static").strip().lower()
    if mesh_coords_mode not in {"static", "by_step", "by_step_moving_nodes"}:
        raise ValueError("mesh_coords must be 'static', 'by_step', or 'by_step_moving_nodes'")

    # Node coordinates (optional)
    node_xy_ref = dict(getattr(mr_ref, "node_xy", {}) or {})
    if node_xy_ref:
        node_id = np.asarray(sorted(node_xy_ref.keys()), dtype=np.int32)
        node_x_mm = np.asarray([float(node_xy_ref[i][0]) for i in node_id.tolist()], dtype=np.float32)
        node_y_mm = np.asarray([float(node_xy_ref[i][1]) for i in node_id.tolist()], dtype=np.float32)
    else:
        node_id = np.asarray([], dtype=np.int32)
        node_x_mm = np.asarray([], dtype=np.float32)
        node_y_mm = np.asarray([], dtype=np.float32)

    # Optional per-step mesh coordinates
    # - Full moving mesh: aligned to node_id [n_steps, n_nodes]
    # - Partial moving nodes: only moving indices [n_steps, n_moving_nodes]
    node_x_by_step = None
    node_y_by_step = None
    moving_node_indices = None
    moving_node_id = None
    node_x_by_step_moving = None
    node_y_by_step_moving = None

    region_name_by_code = _regions_name_map(mr_ref)

    if int(node_id.size) > 0 and mesh_coords_mode in {"by_step", "by_step_moving_nodes"}:
        node_id_list = node_id.tolist()
        if mesh_coords_mode == "by_step":
            node_x_by_step = np.full((n_steps, int(node_id.size)), np.nan, dtype=np.float32)
            node_y_by_step = np.full((n_steps, int(node_id.size)), np.nan, dtype=np.float32)
            for si, step in enumerate(steps):
                mr = getattr(nts, "by_step")[int(step)]
                node_xy = dict(getattr(mr, "node_xy", {}) or {})
                if not node_xy:
                    continue
                for j, nid in enumerate(node_id_list):
                    xy = node_xy.get(int(nid))
                    if xy is None:
                        continue
                    try:
                        node_x_by_step[si, j] = float(xy[0])
                        node_y_by_step[si, j] = float(xy[1])
                    except Exception:
                        continue
        else:
            # Determine which nodes should be treated as moving.
            # Priority:
            # 1) explicit moving_reg_codes (element-based)
            # 2) region-name inference if moving_region_name_prefixes was provided
            # 3) coordinate-motion detection (robust, works even if RegionsTable names are missing)

            node_pos = {int(nid): int(i) for i, nid in enumerate(node_id_list)}
            moving_node_ids: set[int] = set()
            moving_reg_codes_used: list[int] = []
            moving_selection_method = ""

            def _add_nodes_for_reg_codes(reg_codes: set[int] | list[int] | tuple[int, ...]):
                """Add *all* node ids belonging to any element in reg_codes.

                Using the global mesh arrays (node_1/node_2/node_3/reg_code) is more robust
                than relying on per-step region element lists, and prevents partial-rotation
                artifacts for regions like a2 (e.g., reg_code=94).
                """
                if not reg_codes:
                    return
                try:
                    rc_arr = np.asarray(list(reg_codes), dtype=np.int32)
                    mask = np.isin(np.asarray(reg_code, dtype=np.int32), rc_arr)
                    if not bool(np.any(mask)):
                        return
                    n1 = np.asarray(node_1, dtype=np.int32)[mask]
                    n2 = np.asarray(node_2, dtype=np.int32)[mask]
                    n3 = np.asarray(node_3, dtype=np.int32)[mask]
                    for v in np.concatenate((n1, n2, n3), axis=0).tolist():
                        moving_node_ids.add(int(v))
                except Exception:
                    # Fallback: slower element iteration
                    for e in ref_elements:
                        try:
                            rc = int(getattr(e, "reg_code"))
                        except Exception:
                            continue
                        if rc not in set(int(x) for x in reg_codes):
                            continue
                        moving_node_ids.add(int(getattr(e, "node_1")))
                        moving_node_ids.add(int(getattr(e, "node_2")))
                        moving_node_ids.add(int(getattr(e, "node_3")))

            use_reg_codes = list(int(x) for x in (moving_reg_codes or []) if int(x) > 0)
            if use_reg_codes:
                moving_selection_method = "explicit_reg_codes"
                moving_reg_codes_used = sorted(set(use_reg_codes))
                _add_nodes_for_reg_codes(set(use_reg_codes))
            elif moving_region_name_prefixes is not None:
                use_reg_codes = _infer_moving_reg_codes(mr_ref)
                if not use_reg_codes:
                    raise ValueError(
                        "mesh_coords='by_step_moving_nodes' was asked to use region-name inference, "
                        "but no regions matched. Pass moving_reg_codes=[...] or omit moving_region_name_prefixes "
                        "to use coordinate-motion detection."
                    )
                moving_selection_method = "name_inference"
                moving_reg_codes_used = sorted(set(use_reg_codes))
                _add_nodes_for_reg_codes(set(use_reg_codes))
            else:
                # Motion detection (REGION-based): if any node in a region moves,
                # include the entire region's nodes to avoid partial-rotation artifacts (e.g. reg_code=94 a2).
                moving_selection_method = "motion_by_reg_code"
                tol = float(moving_node_motion_tol_mm)
                if tol <= 0:
                    tol = 1e-6
                tol2 = tol * tol

                # Use a few samples to avoid cases where step0==step1.
                sample_steps: list[int] = []
                if int(n_steps) >= 2:
                    sample_steps.append(int(steps[-1]))
                if int(n_steps) >= 3:
                    sample_steps.append(int(steps[int(n_steps // 2)]))

                node_xy0 = dict(getattr(mr_ref, "node_xy", {}) or {})
                moving_rc: set[int] = set()
                for step_s in sample_steps:
                    mr_s = getattr(nts, "by_step")[int(step_s)]
                    node_xys = dict(getattr(mr_s, "node_xy", {}) or {})
                    if not node_xys:
                        continue
                    for e in ref_elements:
                        try:
                            rc = int(getattr(e, "reg_code"))
                            nids = (int(getattr(e, "node_1")), int(getattr(e, "node_2")), int(getattr(e, "node_3")))
                        except Exception:
                            continue
                        if rc in moving_rc:
                            continue
                        for nid in nids:
                            xy0 = node_xy0.get(int(nid))
                            xys = node_xys.get(int(nid))
                            if xy0 is None or xys is None:
                                continue
                            try:
                                dx = float(xys[0]) - float(xy0[0])
                                dy = float(xys[1]) - float(xy0[1])
                                if (dx * dx + dy * dy) > tol2:
                                    moving_rc.add(int(rc))
                                    break
                            except Exception:
                                continue

                moving_reg_codes_used = sorted(moving_rc)
                _add_nodes_for_reg_codes(moving_rc)

            idxs = []
            for nid in moving_node_ids:
                ii = node_pos.get(int(nid))
                if ii is not None:
                    idxs.append(int(ii))
            moving_node_indices = np.asarray(sorted(set(idxs)), dtype=np.int32)
            moving_node_id = node_id[moving_node_indices] if int(moving_node_indices.size) > 0 else np.asarray([], dtype=np.int32)
            n_moving = int(moving_node_id.size)
            node_x_by_step_moving = np.full((n_steps, n_moving), np.nan, dtype=np.float32)
            node_y_by_step_moving = np.full((n_steps, n_moving), np.nan, dtype=np.float32)
            moving_node_id_list = moving_node_id.tolist()
            for si, step in enumerate(steps):
                mr = getattr(nts, "by_step")[int(step)]
                node_xy = dict(getattr(mr, "node_xy", {}) or {})
                if not node_xy:
                    continue
                for j, nid in enumerate(moving_node_id_list):
                    xy = node_xy.get(int(nid))
                    if xy is None:
                        continue
                    try:
                        node_x_by_step_moving[si, j] = float(xy[0])
                        node_y_by_step_moving[si, j] = float(xy[1])
                    except Exception:
                        continue

            # Fill missing coords so moving nodes don't partially fall back to static.
            # This is important for regions like a2 where missing values would look like
            # only a subset of elements rotating.
            try:
                for j in range(int(n_moving)):
                    xcol = node_x_by_step_moving[:, j]
                    ycol = node_y_by_step_moving[:, j]
                    mask = np.isfinite(xcol) & np.isfinite(ycol)
                    if not bool(mask.any()):
                        continue
                    first = int(np.argmax(mask))
                    # back-fill leading
                    if first > 0:
                        xcol[:first] = xcol[first]
                        ycol[:first] = ycol[first]
                    # forward-fill
                    for i in range(first + 1, int(n_steps)):
                        if not (np.isfinite(xcol[i]) and np.isfinite(ycol[i])):
                            xcol[i] = xcol[i - 1]
                            ycol[i] = ycol[i - 1]
                    node_x_by_step_moving[:, j] = xcol
                    node_y_by_step_moving[:, j] = ycol
            except Exception:
                pass

    steps_arr = np.asarray([int(s) for s in steps], dtype=np.int32)

    # Chunking: optimize for reading single-step slabs (shape ~ [1, n_el]).
    chunk_el = int(max(1, min(int(chunk_elements), n_el)))
    chunks_2d = (1, chunk_el)

    with h5py.File(h5_path, "w") as f:
        # Explicit format naming (no v1/v2 in the name). Readers still accept legacy formats.
        if mesh_coords_mode == "by_step" and node_x_by_step is not None and node_y_by_step is not None:
            f.attrs["format"] = "pyMCAD.magnetic.timeseries.moving_mesh"
            f.attrs["mesh_coords_mode"] = "by_step"
        elif mesh_coords_mode == "by_step_moving_nodes" and node_x_by_step_moving is not None and node_y_by_step_moving is not None:
            f.attrs["format"] = "pyMCAD.magnetic.timeseries.moving_mesh"
            f.attrs["mesh_coords_mode"] = "by_step_moving_nodes"
            try:
                # best-effort provenance for debugging
                f.attrs["moving_node_motion_tol_mm"] = float(moving_node_motion_tol_mm)
            except Exception:
                pass
        else:
            f.attrs["format"] = "pyMCAD.magnetic.timeseries.static_mesh"
            f.attrs["mesh_coords_mode"] = "static"
        f.create_dataset("steps", data=steps_arr)

        # Meta arrays (best-effort)
        meta_g = f.create_group("meta")
        meta = getattr(nts, "meta", {}) or {}
        def _meta_arr(key, dtype_out):
            out = []
            for s in steps_arr.tolist():
                m = meta.get(int(s), {}) if isinstance(meta, dict) else {}
                out.append(m.get(key, None))
            # store as float with NaN for missing
            if dtype_out == "f8":
                arr = np.asarray([np.nan if v is None else float(v) for v in out], dtype=np.float64)
            else:
                arr = np.asarray([-1 if v is None else int(v) for v in out], dtype=np.int32)
            return arr

        meta_g.create_dataset("solution", data=_meta_arr("solution", "i4"))
        meta_g.create_dataset("time_s", data=_meta_arr("time_s", "f8"))
        meta_g.create_dataset("rotate_step", data=_meta_arr("rotate_step", "f8"))

        mesh_g = f.create_group("mesh")
        mesh_g.create_dataset("node_id", data=node_id)
        mesh_g.create_dataset("node_x_mm", data=node_x_mm)
        mesh_g.create_dataset("node_y_mm", data=node_y_mm)

        # Region code -> name mapping (optional, enables nicer interactive dropdowns)
        if region_name_by_code:
            try:
                rc_list = np.asarray(sorted(region_name_by_code.keys()), dtype=np.int32)
                name_list = [str(region_name_by_code[int(rc)]) for rc in rc_list.tolist()]
                rg = f.create_group("regions")
                rg.create_dataset("reg_code", data=rc_list)
                rg.create_dataset("name", data=np.asarray(name_list, dtype=h5py.string_dtype(encoding="utf-8")))
            except Exception:
                pass

        # Moving mesh coordinates (optional)
        if node_x_by_step is not None and node_y_by_step is not None:
            # Chunking: optimize for reading a single step slice: [1, n_nodes]
            n_nodes = int(node_id.size)
            if n_nodes > 0:
                mesh_chunks_2d = (1, int(max(1, min(int(chunk_elements), n_nodes))))
            else:
                mesh_chunks_2d = None
            mesh_write_kwargs = {
                "compression": compression,
                "compression_opts": compression_opts,
                "shuffle": True,
            }
            if mesh_chunks_2d is not None:
                mesh_write_kwargs["chunks"] = mesh_chunks_2d
            mesh_g.create_dataset("node_x_mm_by_step", data=node_x_by_step.astype(dtype, copy=False), **mesh_write_kwargs)
            mesh_g.create_dataset("node_y_mm_by_step", data=node_y_by_step.astype(dtype, copy=False), **mesh_write_kwargs)

        # Moving nodes only (optional)
        if (
            moving_node_indices is not None
            and moving_node_id is not None
            and node_x_by_step_moving is not None
            and node_y_by_step_moving is not None
        ):
            mesh_g.create_dataset("moving_node_indices", data=np.asarray(moving_node_indices, dtype=np.int32))
            mesh_g.create_dataset("moving_node_id", data=np.asarray(moving_node_id, dtype=np.int32))
            # Also store reg_code list used (if any). Helpful when diagnosing weird rotation.
            try:
                if "moving_reg_codes_used" in locals() and locals()["moving_reg_codes_used"]:
                    mesh_g.create_dataset("moving_reg_codes", data=np.asarray(locals()["moving_reg_codes_used"], dtype=np.int32))
                if "moving_selection_method" in locals() and str(locals()["moving_selection_method"]):
                    f.attrs["moving_selection_method"] = str(locals()["moving_selection_method"])
            except Exception:
                pass
            # Chunking: optimize for reading a single step slice: [1, n_moving_nodes]
            n_moving = int(moving_node_id.size)
            if n_moving > 0:
                mesh_chunks_2d = (1, int(max(1, min(int(chunk_elements), n_moving))))
            else:
                mesh_chunks_2d = None
            mesh_write_kwargs = {
                "compression": compression,
                "compression_opts": compression_opts,
                "shuffle": True,
            }
            if mesh_chunks_2d is not None:
                mesh_write_kwargs["chunks"] = mesh_chunks_2d
            mesh_g.create_dataset(
                "node_x_mm_by_step_moving",
                data=node_x_by_step_moving.astype(dtype, copy=False),
                **mesh_write_kwargs,
            )
            mesh_g.create_dataset(
                "node_y_mm_by_step_moving",
                data=node_y_by_step_moving.astype(dtype, copy=False),
                **mesh_write_kwargs,
            )
        mesh_g.create_dataset("tri_index", data=tri_index)
        mesh_g.create_dataset("node_1", data=node_1)
        mesh_g.create_dataset("node_2", data=node_2)
        mesh_g.create_dataset("node_3", data=node_3)
        mesh_g.create_dataset("reg_code", data=reg_code)

        fields_g = f.create_group("fields")
        write_kwargs = {
            "compression": compression,
            "compression_opts": compression_opts,
            "shuffle": True,
            "chunks": chunks_2d,
        }

        def _ds(name: str, arr: np.ndarray):
            fields_g.create_dataset(name, data=arr.astype(dtype, copy=False), **write_kwargs)

        _ds("bx", bx_mat)
        _ds("by", by_mat)
        _ds("b", b_mat)
        _ds("a", a_mat)
        _ds("j", j_mat)
        _ds("je", je_mat)

    return h5_path


def diagnose_magnetic_h5_mesh_motion(
    h5_path: str | pathlib.Path,
    *,
    rot_key: str = "meta/rotate_step",
) -> dict:
    """Diagnose whether a magnetic H5 includes per-step mesh motion.

    This is mainly to validate cases where Motor-CAD TXT export contains step-dependent
    node positions (e.g., rotor rotation) but H5 looks static.

    Returns a dict with:
    - format
    - n_steps (if any)
    - mesh_coords_mode (attr if present)
    - has_node_coords
    - node_coord_shape
    - has_per_step_node_coords (heuristic)
    - rotate_step_stats (if present)
    - conclusion (human-readable)
    """

    try:
        import h5py  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("h5py is required to read .h5 files. Install with: pip install h5py") from e

    import numpy as np

    h5_path = pathlib.Path(h5_path)
    out: dict = {
        "path": str(h5_path),
        "format": "",
        "n_steps": None,
        "mesh_coords_mode": None,
        "has_node_coords": False,
        "node_coord_shape": None,
        "has_per_step_node_coords": False,
        "moving_node_count": None,
        "moving_node_coord_shape": None,
        "moving_reg_codes": None,
        "moving_reg_codes_labeled": None,
        "region_name_by_code": None,
        "rotate_step_stats": None,
        "conclusion": "",
    }

    with h5py.File(h5_path, "r") as f:
        fmt = f.attrs.get("format", "")
        if isinstance(fmt, (bytes, bytearray)):
            fmt = fmt.decode(errors="replace")
        out["format"] = str(fmt)

        mcm = f.attrs.get("mesh_coords_mode", None)
        if isinstance(mcm, (bytes, bytearray)):
            mcm = mcm.decode(errors="replace")
        out["mesh_coords_mode"] = mcm

        steps = None
        if "steps" in f:
            steps = np.asarray(f["steps"][:])
            out["n_steps"] = int(steps.size)
        elif "step" in f:
            out["n_steps"] = 1

        # Node coords presence/shape
        if "mesh/node_x_mm" in f and "mesh/node_y_mm" in f:
            out["has_node_coords"] = True
            out["node_coord_shape"] = tuple(f["mesh/node_x_mm"].shape)

        # Heuristic: per-step coords would typically be [n_steps, n_nodes]
        has_per_step = False
        if steps is not None and out["has_node_coords"]:
            shp = tuple(f["mesh/node_x_mm"].shape)
            if len(shp) == 2 and int(shp[0]) == int(out["n_steps"]):
                has_per_step = True
        # Also check for alternate dataset names (future-proof)
        if steps is not None:
            for cand in (
                "mesh/node_x_mm_by_step",
                "mesh/node_y_mm_by_step",
                "mesh/node_xy_mm_by_step",
                "mesh/node_x_mm_step",
                "mesh/node_y_mm_step",
                "mesh/node_x_mm_by_step_moving",
                "mesh/node_y_mm_by_step_moving",
            ):
                if cand in f:
                    has_per_step = True
                    break
        out["has_per_step_node_coords"] = bool(has_per_step)

        if "mesh/moving_node_indices" in f:
            try:
                out["moving_node_count"] = int(np.asarray(f["mesh/moving_node_indices"][:]).size)
            except Exception:
                out["moving_node_count"] = None
        if "mesh/node_x_mm_by_step_moving" in f:
            try:
                out["moving_node_coord_shape"] = tuple(f["mesh/node_x_mm_by_step_moving"].shape)
            except Exception:
                out["moving_node_coord_shape"] = None

        if "mesh/moving_reg_codes" in f:
            try:
                out["moving_reg_codes"] = [
                    int(x)
                    for x in np.asarray(f["mesh/moving_reg_codes"][:], dtype=np.int32).tolist()
                ]
            except Exception:
                out["moving_reg_codes"] = None

        # Region code -> name mapping
        try:
            if "regions" in f and "reg_code" in f["regions"] and "name" in f["regions"]:
                rc_arr = np.asarray(f["regions/reg_code"][:], dtype=np.int32)
                nm_arr = np.asarray(f["regions/name"][:])
                name_map: dict[int, str] = {}
                for rc_i, nm_i in zip(rc_arr.tolist(), nm_arr.tolist()):
                    if isinstance(nm_i, (bytes, bytearray)):
                        nm_s = nm_i.decode("utf-8", errors="replace")
                    else:
                        nm_s = str(nm_i)
                    nm_s = nm_s.strip()
                    if nm_s:
                        name_map[int(rc_i)] = nm_s
                out["region_name_by_code"] = name_map
        except Exception:
            out["region_name_by_code"] = None

        if out.get("moving_reg_codes") and out.get("region_name_by_code"):
            try:
                nm = out["region_name_by_code"] or {}
                out["moving_reg_codes_labeled"] = [
                    (f"{int(rc)} ({nm[int(rc)]})" if int(rc) in nm else str(int(rc)))
                    for rc in (out["moving_reg_codes"] or [])
                ]
            except Exception:
                out["moving_reg_codes_labeled"] = None

        # Rotation meta stats (if present)
        if rot_key in f:
            rot = np.asarray(f[rot_key][:], dtype=np.float64)
            mask = np.isfinite(rot)
            if mask.any():
                rv = rot[mask]
                # unique count (rounded to reduce float noise)
                uniq = int(np.unique(np.round(rv, 12)).size)
                out["rotate_step_stats"] = {
                    "count": int(rv.size),
                    "min": float(np.min(rv)),
                    "max": float(np.max(rv)),
                    "unique_approx": uniq,
                }

    # Conclusion
    fmt_l = str(out["format"]).lower()
    if "timeseries" in fmt_l:
        if out["has_node_coords"] and not out["has_per_step_node_coords"]:
            out["conclusion"] = (
                "H5 stores node coordinates only once (static). "
                "Step-dependent mesh motion (e.g., rotor rotation) is not preserved in this H5 v1."
            )
        elif not out["has_node_coords"]:
            out["conclusion"] = (
                "H5 has no node coordinates; you cannot reproduce the mesh geometry from this file alone."
            )
        else:
            if out.get("moving_node_count"):
                out["conclusion"] = (
                    "H5 includes per-step node coordinates for a subset of nodes (moving nodes). "
                    "Other nodes use static fallback coordinates."
                )
            else:
                out["conclusion"] = "H5 appears to include per-step node coordinates (mesh motion present)."
    elif "static" in fmt_l or "snapshot" in fmt_l:
        out["conclusion"] = "Snapshot H5 represents a single state; mesh motion across steps is not applicable."
    else:
        out["conclusion"] = "Unknown/unsupported H5 format for motion diagnosis."

    return out


def export_magnetic_snapshot_h5(
    mr: MagneticRegions,
    h5_path: str | pathlib.Path,
    *,
    dtype: str = "float32",
    compression: str | None = "gzip",
    compression_opts: int | None = 4,
    chunk_elements: int = 200_000,
) -> pathlib.Path:
    """Export a snapshot magnetic field (`MagneticRegions`) to HDF5.

    This is for StaticLoad/StaticOC-like results (single state), i.e. *not* a time series.

    Dataset layout (v1)
    ------------------
    - /step: int32 scalar (defaults to 1 if unknown)
    - /mesh/node_id, /mesh/node_x_mm, /mesh/node_y_mm
    - /mesh/tri_index, /mesh/node_1, /mesh/node_2, /mesh/node_3, /mesh/reg_code
    - /fields/bx, /fields/by, /fields/b, /fields/a, /fields/j, /fields/je : [n_elements]
    """

    try:
        import h5py  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "h5py is required to write .h5 files. Install with: pip install h5py"
        ) from e

    import numpy as np

    h5_path = pathlib.Path(h5_path)
    h5_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten all elements
    elements: list[MagElement] = []
    for region in getattr(mr, "_regions", []) or []:
        elements.extend(getattr(region, "elements", []) or [])
    if not elements:
        raise ValueError("No elements found in snapshot")

    tri_index = np.asarray([int(getattr(e, "tri_index")) for e in elements], dtype=np.int32)
    node_1 = np.asarray([int(getattr(e, "node_1")) for e in elements], dtype=np.int32)
    node_2 = np.asarray([int(getattr(e, "node_2")) for e in elements], dtype=np.int32)
    node_3 = np.asarray([int(getattr(e, "node_3")) for e in elements], dtype=np.int32)
    reg_code = np.asarray([int(getattr(e, "reg_code")) for e in elements], dtype=np.int32)

    n_el = int(tri_index.size)

    def _vec(getter):
        arr = np.full((n_el,), np.nan, dtype=np.float32)
        for i, e in enumerate(elements):
            try:
                v = getter(e)
                if v is None:
                    continue
                arr[i] = float(v)
            except Exception:
                continue
        return arr

    bx_vec = _vec(lambda e: getattr(e, "bx", None))
    by_vec = _vec(lambda e: getattr(e, "by", None))
    b_vec = _vec(lambda e: getattr(e, "b", None))
    a_vec = _vec(lambda e: getattr(e, "a", None))
    j_vec = _vec(lambda e: getattr(e, "j", None))
    je_vec = _vec(lambda e: getattr(e, "je", None))

    # Node coordinates (optional)
    node_xy = dict(getattr(mr, "node_xy", {}) or {})
    if node_xy:
        node_id = np.asarray(sorted(node_xy.keys()), dtype=np.int32)
        node_x_mm = np.asarray([float(node_xy[i][0]) for i in node_id.tolist()], dtype=np.float32)
        node_y_mm = np.asarray([float(node_xy[i][1]) for i in node_id.tolist()], dtype=np.float32)
    else:
        node_id = np.asarray([], dtype=np.int32)
        node_x_mm = np.asarray([], dtype=np.float32)
        node_y_mm = np.asarray([], dtype=np.float32)

    # Chunking: optimize for slicing element ranges.
    chunk_el = int(max(1, min(int(chunk_elements), n_el)))

    with h5py.File(h5_path, "w") as f:
        # Explicit naming: snapshot == static.
        f.attrs["format"] = "pyMCAD.magnetic.static_mesh"
        # Unknown step for snapshots from text exports; keep a placeholder.
        f.create_dataset("step", data=np.asarray(1, dtype=np.int32))

        mesh_g = f.create_group("mesh")
        mesh_g.create_dataset("node_id", data=node_id)
        mesh_g.create_dataset("node_x_mm", data=node_x_mm)
        mesh_g.create_dataset("node_y_mm", data=node_y_mm)
        mesh_g.create_dataset("tri_index", data=tri_index)
        mesh_g.create_dataset("node_1", data=node_1)
        mesh_g.create_dataset("node_2", data=node_2)
        mesh_g.create_dataset("node_3", data=node_3)
        mesh_g.create_dataset("reg_code", data=reg_code)

        fields_g = f.create_group("fields")
        write_kwargs = {
            "compression": compression,
            "compression_opts": compression_opts,
            "shuffle": True,
            "chunks": (chunk_el,),
        }

        def _ds(name: str, arr: np.ndarray):
            fields_g.create_dataset(name, data=arr.astype(dtype, copy=False), **write_kwargs)

        _ds("bx", bx_vec)
        _ds("by", by_vec)
        _ds("b", b_vec)
        _ds("a", a_vec)
        _ds("j", j_vec)
        _ds("je", je_vec)

    return h5_path


def inspect_magnetic_timeseries_h5(
    h5_path: str | pathlib.Path,
    *,
    max_items: int = 50,
) -> dict:
    """Inspect a `Mag_*.h5` file written by `export_magnetic_timeseries_h5`.

    Returns a lightweight dict describing datasets (name, shape, dtype).
    """
    try:
        import h5py  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("h5py is required to read .h5 files. Install with: pip install h5py") from e

    h5_path = pathlib.Path(h5_path)
    info: dict = {"path": str(h5_path), "attrs": {}, "datasets": []}

    with h5py.File(h5_path, "r") as f:
        info["attrs"] = {k: (v.decode() if isinstance(v, (bytes, bytearray)) else v) for k, v in dict(f.attrs).items()}
        count = 0
        def _visit(name, obj):
            nonlocal count
            if count >= int(max_items):
                return
            if isinstance(obj, h5py.Dataset):
                info["datasets"].append(
                    {
                        "name": str(name),
                        "shape": tuple(obj.shape),
                        "dtype": str(obj.dtype),
                    }
                )
                count += 1
        f.visititems(_visit)

    return info


def load_magnetic_timeseries_h5_arrays(
    h5_path: str | pathlib.Path,
    *,
    fields: Sequence[str] = ("b", "a", "j", "je", "bx", "by"),
    astype: str | None = None,
) -> dict:
    """Load arrays from a `Mag_*.h5` file written by `export_magnetic_timeseries_h5`.

    This returns numpy arrays (not a fully reconstructed `MagneticRegionsTimeSeries`).

    Returns keys:
    - steps
    - meta_solution, meta_time_s, meta_rotate_step
    - mesh_* (node_id/node_x_mm/node_y_mm/tri_index/node_1/node_2/node_3/reg_code)
    - field_<name> for each requested field
    """
    try:
        import h5py  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("h5py is required to read .h5 files. Install with: pip install h5py") from e

    import numpy as np

    h5_path = pathlib.Path(h5_path)
    out: dict = {"path": str(h5_path)}

    with h5py.File(h5_path, "r") as f:
        out["format"] = f.attrs.get("format", "")
        out["mesh_coords_mode"] = f.attrs.get("mesh_coords_mode", None)
        out["steps"] = np.asarray(f["steps"][:])
        # meta
        out["meta_solution"] = np.asarray(f["meta/solution"][:]) if "meta/solution" in f else None
        out["meta_time_s"] = np.asarray(f["meta/time_s"][:]) if "meta/time_s" in f else None
        out["meta_rotate_step"] = np.asarray(f["meta/rotate_step"][:]) if "meta/rotate_step" in f else None
        # mesh
        for k in (
            "node_id",
            "node_x_mm",
            "node_y_mm",
            "moving_node_indices",
            "moving_node_id",
            "tri_index",
            "node_1",
            "node_2",
            "node_3",
            "reg_code",
        ):
            path = f"mesh/{k}"
            out[f"mesh_{k}"] = np.asarray(f[path][:]) if path in f else None

        # optional per-step mesh coords
        out["mesh_node_x_mm_by_step"] = (
            np.asarray(f["mesh/node_x_mm_by_step"][:]) if "mesh/node_x_mm_by_step" in f else None
        )
        out["mesh_node_y_mm_by_step"] = (
            np.asarray(f["mesh/node_y_mm_by_step"][:]) if "mesh/node_y_mm_by_step" in f else None
        )
        out["mesh_node_x_mm_by_step_moving"] = (
            np.asarray(f["mesh/node_x_mm_by_step_moving"][:]) if "mesh/node_x_mm_by_step_moving" in f else None
        )
        out["mesh_node_y_mm_by_step_moving"] = (
            np.asarray(f["mesh/node_y_mm_by_step_moving"][:]) if "mesh/node_y_mm_by_step_moving" in f else None
        )

        # fields
        for name in tuple(fields):
            name_s = str(name).strip().lower()
            path = f"fields/{name_s}"
            if path not in f:
                out[f"field_{name_s}"] = None
                continue
            arr = np.asarray(f[path][:])
            if astype is not None:
                arr = arr.astype(astype, copy=False)
            out[f"field_{name_s}"] = arr

    return out


def load_magnetic_timeseries_h5_datasets(
    h5_path: str | pathlib.Path,
    *,
    fields: Sequence[str] = ("b", "a", "j", "je", "bx", "by"),
    astype: str | None = None,
) -> dict:
    """Alias of `load_magnetic_timeseries_h5_arrays` with a more explicit name.

    This loads the HDF5 datasets into numpy arrays; it does not just read the `format` string.
    Use `read_magnetic_h5_format()` if you only need to branch on file type.
    """

    return load_magnetic_timeseries_h5_arrays(h5_path, fields=fields, astype=astype)


def load_magnetic_snapshot_h5_arrays(
    h5_path: str | pathlib.Path,
    *,
    fields: Sequence[str] = ("b", "a", "j", "je", "bx", "by"),
    astype: str | None = None,
) -> dict:
    """Load arrays from a snapshot `Mag_*.h5` written by `export_magnetic_snapshot_h5`.

    Returns keys:
    - step
    - mesh_* (node_id/node_x_mm/node_y_mm/tri_index/node_1/node_2/node_3/reg_code)
    - field_<name> for each requested field
    """

    try:
        import h5py  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("h5py is required to read .h5 files. Install with: pip install h5py") from e

    import numpy as np

    h5_path = pathlib.Path(h5_path)
    out: dict = {"path": str(h5_path)}

    with h5py.File(h5_path, "r") as f:
        out["format"] = f.attrs.get("format", "")
        out["step"] = int(np.asarray(f["step"][()])) if "step" in f else None

        for k in (
            "node_id",
            "node_x_mm",
            "node_y_mm",
            "tri_index",
            "node_1",
            "node_2",
            "node_3",
            "reg_code",
        ):
            path = f"mesh/{k}"
            out[f"mesh_{k}"] = np.asarray(f[path][:]) if path in f else None

        for name in tuple(fields):
            name_s = str(name).strip().lower()
            path = f"fields/{name_s}"
            if path not in f:
                out[f"field_{name_s}"] = None
                continue
            arr = np.asarray(f[path][:])
            if astype is not None:
                arr = arr.astype(astype, copy=False)
            out[f"field_{name_s}"] = arr

    return out


def read_magnetic_h5_format(h5_path: str | pathlib.Path) -> str:
    """Read the `format` attribute from a magnetic HDF5 file (best-effort)."""
    try:
        import h5py  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("h5py is required to read .h5 files. Install with: pip install h5py") from e

    h5_path = pathlib.Path(h5_path)
    with h5py.File(h5_path, "r") as f:
        fmt = f.attrs.get("format", "")
        if isinstance(fmt, (bytes, bytearray)):
            try:
                fmt = fmt.decode()
            except Exception:
                fmt = str(fmt)
        return str(fmt)


# Backward-compatible alias (older notebook code used underscore name)
_read_magnetic_h5_format = read_magnetic_h5_format


def _nan_to_none(x):
    try:
        if x is None:
            return None
        xf = float(x)
        if np.isnan(xf):
            return None
        return xf
    except Exception:
        return None


def _node_xy_from_mesh_arrays(data: dict) -> dict[int, tuple[float, float]]:
    node_id = data.get("mesh_node_id")
    node_x = data.get("mesh_node_x_mm")
    node_y = data.get("mesh_node_y_mm")
    if node_id is None or node_x is None or node_y is None:
        return {}
    if len(node_id) == 0:
        return {}
    out: dict[int, tuple[float, float]] = {}
    for i, nid in enumerate(node_id.tolist()):
        try:
            out[int(nid)] = (float(node_x[i]), float(node_y[i]))
        except Exception:
            continue
    return out


def _magnetic_regions_from_snapshot_h5(h5_path: str | pathlib.Path) -> MagneticRegions:
    data = load_magnetic_snapshot_h5_arrays(h5_path, fields=("b", "a", "j", "je", "bx", "by"), astype=None)

    tri_index = data.get("mesh_tri_index")
    node_1 = data.get("mesh_node_1")
    node_2 = data.get("mesh_node_2")
    node_3 = data.get("mesh_node_3")
    reg_code = data.get("mesh_reg_code")
    if tri_index is None or node_1 is None or node_2 is None or node_3 is None or reg_code is None:
        raise ValueError(f"Invalid snapshot h5 (missing mesh arrays): {h5_path}")

    b = data.get("field_b")
    a = data.get("field_a")
    j = data.get("field_j")
    je = data.get("field_je")
    bx = data.get("field_bx")
    by = data.get("field_by")

    n_el = int(len(tri_index))
    mr = MagneticRegions()
    for i in range(n_el):
        rc = int(reg_code[i])
        mr.ensure_region(rc)

        bx_i = _nan_to_none(bx[i]) if bx is not None else None
        by_i = _nan_to_none(by[i]) if by is not None else None
        b_i = _nan_to_none(b[i]) if b is not None else None
        if b_i is None and (bx_i is not None) and (by_i is not None):
            try:
                b_i = float((bx_i**2 + by_i**2) ** 0.5)
            except Exception:
                b_i = None

        mr[rc - 1].add_element(
            tri_index=int(tri_index[i]),
            node_1=int(node_1[i]),
            node_2=int(node_2[i]),
            node_3=int(node_3[i]),
            reg_code=rc,
            bx=bx_i,
            by=by_i,
            a=_nan_to_none(a[i]) if a is not None else None,
            j=_nan_to_none(j[i]) if j is not None else None,
            je=_nan_to_none(je[i]) if je is not None else None,
            b=b_i,
        )

    mr.set_node_xy(_node_xy_from_mesh_arrays(data))
    return mr


class _H5ByStep:
    def __init__(self, parent):
        self._parent = parent

    def __getitem__(self, step):
        return self._parent._load_step(int(step))


class MagneticRegionsTimeSeriesH5:
    """Lazy HDF5-backed time series adapter.

    This is designed so existing functions like `export_magnetic_timeseries_gif(ts, ...)`
    can work without re-parsing the large txt.
    """

    def __init__(self, h5_path: str | pathlib.Path):
        self.meta: dict[int, dict] = {}
        self._h5_path = pathlib.Path(h5_path)
        self._step_to_index: dict[int, int] = {}
        self._steps: list[int] = []
        self._mesh: dict[str, np.ndarray] = {}
        # Static fallback coordinates (reference step) and optional per-step coordinates.
        self._node_xy: dict[int, tuple[float, float]] = {}
        self._node_id: np.ndarray | None = None
        self._coords_by_step: bool = False
        self._coords_by_step_moving_nodes: bool = False
        self._moving_node_indices: np.ndarray | None = None
        self._region_name_by_code: dict[int, str] = {}
        self._field_names: set[str] = set()
        self._cache: dict[int, MagneticRegions] = {}
        self._cache_order: list[int] = []

        try:
            import h5py  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("h5py is required to read .h5 files. Install with: pip install h5py") from e

        with h5py.File(self._h5_path, "r") as f:
            steps_arr = np.asarray(f["steps"][:], dtype=np.int32)
            self._steps = [int(s) for s in steps_arr.tolist()]
            self._step_to_index = {int(s): int(i) for i, s in enumerate(self._steps)}

            # meta arrays (best-effort)
            sol = np.asarray(f["meta/solution"][:]) if "meta/solution" in f else None
            t_s = np.asarray(f["meta/time_s"][:]) if "meta/time_s" in f else None
            rot = np.asarray(f["meta/rotate_step"][:]) if "meta/rotate_step" in f else None
            for i, step in enumerate(self._steps):
                self.meta[int(step)] = {
                    "solution": int(sol[i]) if sol is not None else None,
                    "time_index": int(step),
                    "time_s": (float(t_s[i]) if t_s is not None else None),
                    "rotate_step": (float(rot[i]) if rot is not None else None),
                }

            # mesh arrays
            for k in ("tri_index", "node_1", "node_2", "node_3", "reg_code"):
                p = f"mesh/{k}"
                if p not in f:
                    raise ValueError(f"Invalid timeseries h5 (missing {p}): {self._h5_path}")
                self._mesh[k] = np.asarray(f[p][:])

            # node coords optional (static or moving)
            if "mesh/node_id" in f:
                self._node_id = np.asarray(f["mesh/node_id"][:], dtype=np.int32)

            # Always try to load a static fallback coordinate table if present
            if "mesh/node_x_mm" in f and "mesh/node_y_mm" in f and self._node_id is not None:
                node_x0 = np.asarray(f["mesh/node_x_mm"][:], dtype=float)
                node_y0 = np.asarray(f["mesh/node_y_mm"][:], dtype=float)
                if int(self._node_id.size) > 0:
                    for idx0, nid in enumerate(self._node_id.tolist()):
                        try:
                            x0 = float(node_x0[idx0])
                            y0 = float(node_y0[idx0])
                            if np.isfinite(x0) and np.isfinite(y0):
                                self._node_xy[int(nid)] = (x0, y0)
                        except Exception:
                            continue

            # Moving mesh: coords are stored per step
            if "mesh/node_x_mm_by_step" in f and "mesh/node_y_mm_by_step" in f and self._node_id is not None:
                self._coords_by_step = True

            # Moving nodes only: coords are stored per step for selected nodes
            if (
                "mesh/moving_node_indices" in f
                and "mesh/node_x_mm_by_step_moving" in f
                and "mesh/node_y_mm_by_step_moving" in f
                and self._node_id is not None
            ):
                try:
                    idxs = np.asarray(f["mesh/moving_node_indices"][:], dtype=np.int32)
                    # Validate indices are in-range
                    if int(idxs.size) > 0:
                        idxs = idxs[(idxs >= 0) & (idxs < int(self._node_id.size))]
                    self._moving_node_indices = idxs
                    self._coords_by_step = True
                    self._coords_by_step_moving_nodes = True
                except Exception:
                    self._moving_node_indices = None
                    self._coords_by_step_moving_nodes = False

            # available fields
            if "fields" in f:
                try:
                    self._field_names = set(str(k).lower() for k in f["fields"].keys())
                except Exception:
                    self._field_names = set()

            # Optional: region code -> name (from RegionsTable)
            try:
                if "regions" in f and "reg_code" in f["regions"] and "name" in f["regions"]:
                    rc_arr = np.asarray(f["regions/reg_code"][:], dtype=np.int32)
                    nm_arr = np.asarray(f["regions/name"][:])
                    name_map: dict[int, str] = {}
                    for rc_i, nm_i in zip(rc_arr.tolist(), nm_arr.tolist()):
                        if isinstance(nm_i, (bytes, bytearray)):
                            nm_s = nm_i.decode("utf-8", errors="replace")
                        else:
                            nm_s = str(nm_i)
                        nm_s = nm_s.strip()
                        if nm_s:
                            name_map[int(rc_i)] = nm_s
                    self._region_name_by_code = name_map
            except Exception:
                self._region_name_by_code = {}

        # dict-like lazy accessor expected by existing plotting/export utilities
        self.by_step = _H5ByStep(self)

    @property
    def steps(self):
        return list(self._steps)

    def __len__(self):
        return len(self._steps)

    def _cache_put(self, step: int, mr: MagneticRegions, *, max_items: int = 2):
        self._cache[step] = mr
        if step in self._cache_order:
            self._cache_order.remove(step)
        self._cache_order.append(step)
        while len(self._cache_order) > int(max_items):
            old = self._cache_order.pop(0)
            self._cache.pop(old, None)

    def _load_step(self, step: int) -> MagneticRegions:
        if step in self._cache:
            return self._cache[step]

        if step not in self._step_to_index:
            raise KeyError(f"step not found in h5: {step}")
        si = int(self._step_to_index[step])

        try:
            import h5py  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("h5py is required to read .h5 files. Install with: pip install h5py") from e

        tri_index = self._mesh["tri_index"]
        node_1 = self._mesh["node_1"]
        node_2 = self._mesh["node_2"]
        node_3 = self._mesh["node_3"]
        reg_code = self._mesh["reg_code"]

        with h5py.File(self._h5_path, "r") as f:
            def _read_field(name: str):
                name_s = str(name).lower().strip()
                if name_s not in self._field_names:
                    return None
                arr = np.asarray(f[f"fields/{name_s}"][si, :])
                return arr

            b_arr = _read_field("b")
            a_arr = _read_field("a")
            j_arr = _read_field("j")
            je_arr = _read_field("je")
            bx_arr = _read_field("bx")
            by_arr = _read_field("by")

            # Load mesh coordinates for this step (if stored)
            node_xy_step = None
            if self._coords_by_step and self._node_id is not None:
                # Start from static fallback coords, then override if per-step coords exist.
                try:
                    if self._coords_by_step_moving_nodes and self._moving_node_indices is not None:
                        node_xy_step = dict(self._node_xy)
                        node_xm = np.asarray(f["mesh/node_x_mm_by_step_moving"][si, :])
                        node_ym = np.asarray(f["mesh/node_y_mm_by_step_moving"][si, :])
                        moving_idxs = self._moving_node_indices
                        # moving arrays are aligned with moving_idxs order
                        for local_i, node_i in enumerate(moving_idxs.tolist()):
                            try:
                                nid = int(self._node_id[int(node_i)])
                                x = float(node_xm[int(local_i)])
                                y = float(node_ym[int(local_i)])
                                if np.isfinite(x) and np.isfinite(y):
                                    node_xy_step[nid] = (x, y)
                            except Exception:
                                continue
                    else:
                        node_x = np.asarray(f["mesh/node_x_mm_by_step"][si, :])
                        node_y = np.asarray(f["mesh/node_y_mm_by_step"][si, :])
                        node_xy_step = {}
                        for node_i, nid in enumerate(self._node_id.tolist()):
                            try:
                                x = float(node_x[node_i])
                                y = float(node_y[node_i])
                                # If this step is missing a node coordinate (NaN), fall back to static.
                                if np.isfinite(x) and np.isfinite(y):
                                    node_xy_step[int(nid)] = (x, y)
                                else:
                                    xy0 = self._node_xy.get(int(nid))
                                    if xy0 is not None:
                                        node_xy_step[int(nid)] = xy0
                            except Exception:
                                continue
                except Exception:
                    node_xy_step = None

        n_el = int(len(tri_index))
        mr = MagneticRegions()
        if node_xy_step is not None:
            mr.set_node_xy(node_xy_step)
        else:
            mr.set_node_xy(self._node_xy)

        for i in range(n_el):
            rc = int(reg_code[i])
            mr.ensure_region(rc)

            if self._region_name_by_code and rc in self._region_name_by_code:
                try:
                    r = mr[rc - 1]
                    if not str(getattr(r, "region_name", "") or "").strip():
                        r.region_name = self._region_name_by_code[int(rc)]
                except Exception:
                    pass

            bx_i = _nan_to_none(bx_arr[i]) if bx_arr is not None else None
            by_i = _nan_to_none(by_arr[i]) if by_arr is not None else None
            b_i = _nan_to_none(b_arr[i]) if b_arr is not None else None
            if b_i is None and (bx_i is not None) and (by_i is not None):
                try:
                    b_i = float((bx_i**2 + by_i**2) ** 0.5)
                except Exception:
                    b_i = None

            mr[rc - 1].add_element(
                tri_index=int(tri_index[i]),
                node_1=int(node_1[i]),
                node_2=int(node_2[i]),
                node_3=int(node_3[i]),
                reg_code=rc,
                bx=bx_i,
                by=by_i,
                a=_nan_to_none(a_arr[i]) if a_arr is not None else None,
                j=_nan_to_none(j_arr[i]) if j_arr is not None else None,
                je=_nan_to_none(je_arr[i]) if je_arr is not None else None,
                b=b_i,
            )

        self._cache_put(step, mr)
        return mr


