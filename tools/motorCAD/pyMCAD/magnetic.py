from __future__ import annotations

import pathlib
import re
import tempfile
from contextlib import contextmanager
import io
from typing import Dict, Iterable, Sequence

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from ._export import (
    mcad_default_export_dir,
    mcad_make_temp_txt_path,
    save_fea_text_export,
    safe_stem as _safe_stem,
    unique_path as _unique_path,
)


@contextmanager
def _open_mcad_text(path: str | pathlib.Path):
    """Open a Motor-CAD exported text file robustly across Windows locales.

    Motor-CAD exports may be UTF-16 (BOM) or locale-encoded. On Korean Windows,
    the default `open(..., 'r')` uses cp949 and will fail on UTF-16 files.
    """

    p = pathlib.Path(path)

    # Detect BOM / UTF-16 by peeking bytes (no full read, supports large files).
    with open(p, "rb") as fb:
        head = fb.read(4)
        fb.seek(0)

        if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
            encoding = "utf-16"
        elif head.startswith(b"\xef\xbb\xbf"):
            encoding = "utf-8-sig"
        elif b"\x00" in head:
            # Heuristic: many NUL bytes usually indicates UTF-16 without BOM
            encoding = "utf-16"
        else:
            # Korean Windows default; use replacement to avoid hard failures on rare chars.
            encoding = "cp949"

        wrapper = io.TextIOWrapper(fb, encoding=encoding, errors="replace", newline="")
        try:
            yield wrapper
        finally:
            try:
                wrapper.detach()
            except Exception:
                pass


def export_magnetic_timeseries_gif(
    ts,
    gif_path: str | pathlib.Path,
    *,
    quantity: str = "b",
    reg_code: int | None = None,
    s: float = 2,
    cmap: str = "jet",
    mesh: bool = False,
    fps: int = 6,
    max_frames: int | None = None,
) -> pathlib.Path:
    """Export a simple GIF by rendering each time/step frame (non-interactive).

    Requires Pillow (`pip install pillow`).
    """

    from PIL import Image  # type: ignore

    gif_path = pathlib.Path(gif_path)
    gif_path.parent.mkdir(parents=True, exist_ok=True)

    steps = list(getattr(ts, "steps", []))
    if not steps:
        raise ValueError("Empty time series")

    if max_frames is not None:
        steps = steps[: int(max_frames)]

    frames: list[Image.Image] = []
    tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="mcad_gif_"))

    for step in steps:
        fig, ax = plt.subplots(layout="constrained")
        mr = ts.by_step[int(step)]
        mr.plot(reg_code=reg_code, quantity=quantity, cmap=cmap, s=s, ax=ax, show=False, mesh=mesh)
        ax.set_title(f"{str(quantity).upper()} step={step}")
        png_path = tmp_dir / f"frame_{int(step):06d}.png"
        fig.savefig(png_path, dpi=140)
        plt.close(fig)
        frames.append(Image.open(png_path).convert("P"))

    duration_ms = int(1000 / max(1, int(fps)))
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
    )
    return gif_path


def export_magnetic_snapshot_svgs(
    mr,
    *,
    out_dir: str | pathlib.Path,
    stem: str,
    quantities: Sequence[str] = ("b", "a", "j"),
    cmap: str = "jet",
    point_size: float = 2,
    dpi: int = 140,
) -> Dict[str, pathlib.Path]:
    """Export snapshot magnetic fields to separate SVGs for each quantity."""

    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    exported: Dict[str, pathlib.Path] = {}
    for q in tuple(quantities):
        q_s = str(q).lower().strip()
        fig, ax = plt.subplots(layout="constrained")
        mr.plot(quantity=q_s, cmap=cmap, s=float(point_size), ax=ax, show=False)
        ax.set_title(f"Magnetic snapshot {q_s} ({stem})")
        svg_path = _unique_path(out_dir / f"Mag_{q_s}_{_safe_stem(stem)}.svg")
        fig.savefig(svg_path, dpi=int(dpi))
        plt.close(fig)
        exported[q_s] = svg_path

    return exported


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
    slideband_reg_codes: Sequence[int] | None = None,
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
    - /slideband/reg_codes: int32 [n_sb_codes]  (when slideband per-step data stored)
    - /slideband/offsets: int64 [n_steps + 1]   (CSR offsets into flat arrays)
    - /slideband/tri_index, node_1, node_2, node_3, reg_code: int32 [total_sb_elements]
    - /slideband/bx, by, a, j, je: float32 [total_sb_elements]

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

    # ---- Per-step node-level A from NodesTable (raw FEM solution) ----
    # node_id is built later; we collect per-step node_a dicts first,
    # then align to the ref-step node_id array before writing.
    _node_a_by_step: list[dict[int, float]] = []
    for si, step in enumerate(steps):
        mr = getattr(nts, "by_step")[int(step)]
        _node_a_by_step.append(dict(getattr(mr, "node_a", {}) or {}))

    # ---- Per-step sliding band node coordinates (CSR format) ----
    # Each step may introduce virtual nodes not in the ref-step mesh.
    # We collect (node_id, x_mm, y_mm) for SB-only extra nodes per step.
    _sb_node_offsets: list[int] = [0]
    _sb_node_ids: list[int] = []
    _sb_node_x: list[float] = []
    _sb_node_y: list[float] = []
    _sb_node_a_vals: list[float] = []

    # ---- Per-step sliding band connectivity (CSR format) ----
    # Sliding band elements are re-meshed each step by the FEM solver.
    # The main mesh/fields arrays above store only ref_step connectivity,
    # so SB elements with new TriIndex values in later steps are silently
    # dropped.  This block collects the full per-step SB connectivity +
    # field values in a CSR-like flat layout so downstream readers can
    # reconstruct the correct air-gap mesh at any step.
    _SLIDEBAND_NAME_PREFIXES = ("a1", "a2", "a3", "a4")

    def _detect_slideband_codes(mr_ref_arg: MagneticRegions) -> frozenset[int]:
        """Auto-detect sliding band region codes by name (a1-a4)."""
        codes: set[int] = set()
        for region in getattr(mr_ref_arg, "_regions", []) or []:
            name = str(getattr(region, "region_name", "") or "").strip().lower()
            els = getattr(region, "elements", []) or []
            if not name or not els:
                continue
            if name in _SLIDEBAND_NAME_PREFIXES:
                rc = int(getattr(region, "reg_code", 0) or 0)
                if rc <= 0:
                    try:
                        rc = int(getattr(els[0], "reg_code"))
                    except Exception:
                        continue
                codes.add(rc)
        return frozenset(codes)

    if slideband_reg_codes is not None:
        _sb_codes = frozenset(int(c) for c in slideband_reg_codes)
    else:
        _sb_codes = _detect_slideband_codes(mr_ref)
    _sb_offsets: list[int] = [0]
    _sb_tri: list[int] = []
    _sb_n1: list[int] = []
    _sb_n2: list[int] = []
    _sb_n3: list[int] = []
    _sb_rc: list[int] = []
    _sb_bx: list[float] = []
    _sb_by: list[float] = []
    _sb_b: list[float] = []
    _sb_a: list[float] = []
    _sb_j: list[float] = []
    _sb_je: list[float] = []

    for si, step in enumerate(steps):
        mr = getattr(nts, "by_step")[int(step)]
        for region in getattr(mr, "_regions", []) or []:
            for e in getattr(region, "elements", []) or []:
                rc = int(getattr(e, "reg_code"))
                if rc not in _sb_codes:
                    continue
                _sb_tri.append(int(getattr(e, "tri_index")))
                _sb_n1.append(int(getattr(e, "node_1")))
                _sb_n2.append(int(getattr(e, "node_2")))
                _sb_n3.append(int(getattr(e, "node_3")))
                _sb_rc.append(rc)
                bx_v = getattr(e, "bx", None)
                by_v = getattr(e, "by", None)
                _sb_bx.append(float(bx_v) if bx_v is not None else float("nan"))
                _sb_by.append(float(by_v) if by_v is not None else float("nan"))
                try:
                    _sb_b.append(float(getattr(e, "b")))
                except Exception:
                    _sb_b.append(float("nan"))
                try:
                    _sb_a.append(float(getattr(e, "a", 0.0) or 0.0))
                except Exception:
                    _sb_a.append(0.0)
                try:
                    _sb_j.append(float(getattr(e, "j", 0.0) or 0.0))
                except Exception:
                    _sb_j.append(0.0)
                try:
                    _sb_je.append(float(getattr(e, "je", 0.0) or 0.0))
                except Exception:
                    _sb_je.append(0.0)
        _sb_offsets.append(len(_sb_tri))

    _has_sb = len(_sb_tri) > 0

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

    # ---- Per-step node-level A: align to ref-step node_id ----
    n_nodes_ref = int(node_id.size)
    a_node_mat = None
    if n_nodes_ref > 0 and _node_a_by_step:
        node_id_list = node_id.tolist()
        a_node_mat = np.full((n_steps, n_nodes_ref), np.nan, dtype=np.float32)
        for si in range(n_steps):
            na = _node_a_by_step[si]
            if not na:
                continue
            for j, nid in enumerate(node_id_list):
                val = na.get(int(nid))
                if val is not None:
                    a_node_mat[si, j] = float(val)

    # ---- Per-step sliding band extra node coordinates (CSR) ----
    # Collect nodes that exist in this step's NodesTable but NOT in ref-step.
    ref_node_set = set(node_id.tolist()) if n_nodes_ref > 0 else set()
    for si, step in enumerate(steps):
        mr = getattr(nts, "by_step")[int(step)]
        step_node_xy = dict(getattr(mr, "node_xy", {}) or {})
        step_node_a = dict(getattr(mr, "node_a", {}) or {})
        for nid in sorted(step_node_xy.keys()):
            if int(nid) not in ref_node_set:
                xy = step_node_xy[nid]
                _sb_node_ids.append(int(nid))
                _sb_node_x.append(float(xy[0]))
                _sb_node_y.append(float(xy[1]))
                _sb_node_a_vals.append(float(step_node_a.get(int(nid), 0.0)))
        _sb_node_offsets.append(len(_sb_node_ids))

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

        # Node-level A from NodesTable (raw FEM primary solution)
        if a_node_mat is not None and not np.all(np.isnan(a_node_mat)):
            n_nd = a_node_mat.shape[1]
            chunk_nd = int(max(1, min(int(chunk_elements), n_nd)))
            a_node_kwargs = {
                "compression": compression,
                "compression_opts": compression_opts,
                "shuffle": True,
                "chunks": (1, chunk_nd),
            }
            fields_g.create_dataset(
                "a_node", data=a_node_mat.astype(dtype, copy=False), **a_node_kwargs,
            )

        # Per-step sliding band mesh (CSR layout)
        if _has_sb:
            sb_g = f.create_group("slideband")
            sb_g.create_dataset("reg_codes", data=np.asarray(sorted(_sb_codes), dtype=np.int32))
            sb_g.create_dataset("offsets", data=np.asarray(_sb_offsets, dtype=np.int64))
            sb_g.create_dataset("tri_index", data=np.asarray(_sb_tri, dtype=np.int32))
            sb_g.create_dataset("node_1", data=np.asarray(_sb_n1, dtype=np.int32))
            sb_g.create_dataset("node_2", data=np.asarray(_sb_n2, dtype=np.int32))
            sb_g.create_dataset("node_3", data=np.asarray(_sb_n3, dtype=np.int32))
            sb_g.create_dataset("reg_code", data=np.asarray(_sb_rc, dtype=np.int32))
            sb_g.create_dataset("bx", data=np.asarray(_sb_bx, dtype=np.float32))
            sb_g.create_dataset("by", data=np.asarray(_sb_by, dtype=np.float32))
            sb_g.create_dataset("b", data=np.asarray(_sb_b, dtype=np.float32))
            sb_g.create_dataset("a", data=np.asarray(_sb_a, dtype=np.float32))
            sb_g.create_dataset("j", data=np.asarray(_sb_j, dtype=np.float32))
            sb_g.create_dataset("je", data=np.asarray(_sb_je, dtype=np.float32))
            # Per-step extra node coordinates (virtual nodes not in ref-step mesh)
            if len(_sb_node_ids) > 0:
                sb_g.create_dataset("node_offsets", data=np.asarray(_sb_node_offsets, dtype=np.int64))
                sb_g.create_dataset("node_id", data=np.asarray(_sb_node_ids, dtype=np.int32))
                sb_g.create_dataset("node_x_mm", data=np.asarray(_sb_node_x, dtype=np.float32))
                sb_g.create_dataset("node_y_mm", data=np.asarray(_sb_node_y, dtype=np.float32))
                sb_g.create_dataset("node_a", data=np.asarray(_sb_node_a_vals, dtype=np.float32))
            f.attrs["has_slideband_per_step"] = True

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


class MagElement:
    """Motor-CAD electromagnetic element data.

    Columns (ElementsTable)
    - TriIndex, Node1, Node2, Node3, RegCode, Bx, By, A, J, Je

    Units
    - Bx, By: [T]
    - B (magnitude): [T] computed as sqrt(Bx^2 + By^2)
    - A: [Wb/m]
    - J: [A/mm^2]
    - Je: [A/mm^2]
    """

    def __init__(
        self,
        tri_index,
        node_1,
        node_2,
        node_3,
        reg_code,
        bx=None,
        by=None,
        a=None,
        j=None,
        je=None,
        b=None,
    ):
        self.tri_index = int(tri_index)
        self.node_1 = int(node_1)
        self.node_2 = int(node_2)
        self.node_3 = int(node_3)
        self.reg_code = int(reg_code)

        if bx is not None and by is not None:
            self.bx = float(bx)
            self.by = float(by)
            self._b = float((self.bx**2 + self.by**2) ** 0.5)
        elif b is not None:
            # Backward compatibility for old exports that provided only B.
            self.bx = None
            self.by = None
            self._b = float(b)
        else:
            raise ValueError("Either (bx, by) or b must be provided")

        self.a = float(a) if a is not None else 0.0
        self.j = float(j) if j is not None else 0.0
        self.je = float(je) if je is not None else 0.0

    @property
    def b(self) -> float:
        """Magnetic flux density magnitude [T]."""
        return self._b

    @classmethod
    def from_csv_row(cls, row):
        # Accept both formats:
        # - Newest: ... RegCode,Bx,By,A,J,Je (len>=10)
        # - New: ... RegCode,Bx,By,A,J (len>=9)
        # - Old: ... RegCode,B,A,J (len>=8)
        if len(row) >= 10:
            return cls(
                tri_index=row[0],
                node_1=row[1],
                node_2=row[2],
                node_3=row[3],
                reg_code=row[4],
                bx=row[5],
                by=row[6],
                a=row[7],
                j=row[8],
                je=row[9],
            )
        if len(row) >= 9:
            return cls(
                tri_index=row[0],
                node_1=row[1],
                node_2=row[2],
                node_3=row[3],
                reg_code=row[4],
                bx=row[5],
                by=row[6],
                a=row[7],
                j=row[8],
            )
        if len(row) >= 8:
            return cls(
                tri_index=row[0],
                node_1=row[1],
                node_2=row[2],
                node_3=row[3],
                reg_code=row[4],
                b=row[5],
                a=row[6],
                j=row[7],
            )
        raise ValueError("Invalid row format for MagElement")

    @staticmethod
    def plot_vector_field_locus(
        bx: "np.ndarray | list[float]",
        by: "np.ndarray | list[float]",
        *,
        ax=None,
        show: bool = True,
        title: str | None = None,
        color_by_time: bool = True,
        cmap: str = "viridis",
        s: float = 10,
        line: bool = True,
        equal_aspect: bool = True,
        mark_start_end: bool = True,
    ):
        """Plot B-vector locus in the (Bx, By) plane.

        Parameters
        ----------
        bx, by:
            Sequences of Bx/By samples (same length). Units typically [T].
        color_by_time:
            If True, scatter points are colored by sample index (time/order).
        """

        bx_arr = np.asarray(bx, dtype=float)
        by_arr = np.asarray(by, dtype=float)
        if bx_arr.shape != by_arr.shape:
            raise ValueError("bx and by must have the same shape")
        if bx_arr.size == 0:
            raise ValueError("Empty bx/by series")

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        if line:
            ax.plot(bx_arr, by_arr, color="0.35", linewidth=1.0, zorder=1)

        if color_by_time:
            t = np.linspace(0.0, 1.0, bx_arr.size)
            sc = ax.scatter(bx_arr, by_arr, c=t, cmap=cmap, s=float(s), zorder=2)
            cb = plt.colorbar(sc, ax=ax)
            cb.set_label("order")
        else:
            ax.scatter(bx_arr, by_arr, s=float(s), zorder=2)

        if mark_start_end and bx_arr.size >= 1:
            ax.scatter([bx_arr[0]], [by_arr[0]], s=float(s) * 3.0, marker="^", color="tab:green", label="start", zorder=3)
            ax.scatter([bx_arr[-1]], [by_arr[-1]], s=float(s) * 3.0, marker="o", color="tab:red", label="end", zorder=3)
            ax.legend(loc="best")

        ax.axhline(0.0, color="0.85", linewidth=0.8)
        ax.axvline(0.0, color="0.85", linewidth=0.8)
        ax.set_xlabel("Bx [T]")
        ax.set_ylabel("By [T]")

        if equal_aspect:
            ax.set_aspect("equal", adjustable="box")

        if title is None:
            title = "B-vector locus"
        ax.set_title(title)

        if show:
            plt.show()

        return ax

    @classmethod
    def extract_bxby_locus_from_timeseries(
        cls,
        ts,
        *,
        tri_index: int,
        reg_code: int | None = None,
        steps: "list[int] | tuple[int, ...] | None" = None,
        drop_missing: bool = True,
    ) -> tuple[np.ndarray, np.ndarray, list[int]]:
        """Extract (Bx,By) across steps for a single element.

        Parameters
        ----------
        ts:
            MagneticRegionsTimeSeries-like object with `.steps` and `.by_step[step]`.
        tri_index:
            Element triangle index.
        reg_code:
            Optional region code to narrow lookup.
        steps:
            Optional list of step keys. Defaults to `ts.steps`.
        drop_missing:
            If True, silently skip steps where the element or bx/by is missing.
            If False, raises an error on the first missing step.
        """

        if steps is None:
            steps_list = list(getattr(ts, "steps"))
        else:
            steps_list = list(steps)

        bx_list: list[float] = []
        by_list: list[float] = []
        used_steps: list[int] = []

        for step in steps_list:
            mr = getattr(ts, "by_step")[step]

            if reg_code is not None:
                if int(reg_code) <= 0:
                    raise ValueError("reg_code must be >= 1")
                regions = getattr(mr, "_regions", [])
                region = regions[int(reg_code) - 1] if int(reg_code) - 1 < len(regions) else None
                elements = [] if region is None else (getattr(region, "elements", []) or [])
            else:
                elements = []
                for region in getattr(mr, "_regions", []) or []:
                    elements.extend(getattr(region, "elements", []) or [])

            el = next((e for e in elements if int(getattr(e, "tri_index")) == int(tri_index)), None)
            if el is None or getattr(el, "bx", None) is None or getattr(el, "by", None) is None:
                if drop_missing:
                    continue
                raise ValueError(f"Missing element bx/by for tri_index={tri_index} at step={step}")

            bx_list.append(float(el.bx))
            by_list.append(float(el.by))
            used_steps.append(int(step))

        if not used_steps:
            raise ValueError(f"No bx/by samples found for tri_index={tri_index} (reg_code={reg_code})")

        return np.asarray(bx_list, dtype=float), np.asarray(by_list, dtype=float), used_steps

    @classmethod
    def plot_b_locus_from_timeseries(
        cls,
        ts,
        *,
        tri_index: int,
        reg_code: int | None = None,
        steps: "list[int] | tuple[int, ...] | None" = None,
        ax=None,
        show: bool = True,
        color_by_time: bool = True,
        cmap: str = "viridis",
        s: float = 10,
    ):
        """Convenience wrapper: extract (Bx,By) locus from `ts` and plot it."""

        bx, by, used_steps = cls.extract_bxby_locus_from_timeseries(
            ts,
            tri_index=int(tri_index),
            reg_code=(int(reg_code) if reg_code is not None else None),
            steps=steps,
        )

        title = f"B locus (tri_index={int(tri_index)}" + (f", reg_code={int(reg_code)}" if reg_code is not None else "") + ")"
        return cls.plot_vector_field_locus(
            bx,
            by,
            ax=ax,
            show=show,
            title=title,
            color_by_time=bool(color_by_time),
            cmap=cmap,
            s=s,
        )

    @classmethod
    def plot_b_locus_field_from_timeseries(
        cls,
        ts,
        *,
        reg_code: int | None = None,
        steps: "list[int] | tuple[int, ...] | None" = None,
        ref_step: int | None = None,
        element_stride: int = 1,
        locus_scale: float = 0.2,
        show_mesh: bool = False,
        mesh_color: str = "k",
        mesh_linewidth: float = 0.2,
        mesh_alpha: float = 0.35,
        ax=None,
        show: bool = True,
        color: str = "0.25",
        alpha: float = 0.35,
        linewidth: float = 0.5,
        mark_start_end: bool = False,
        equal_aspect: bool = True,
        title: str | None = None,
    ):
        """Plot B-locus for many elements as small loops at their centroids.

        This is the Python equivalent of a "vector field locus" plot: for each element
        you draw the trajectory (Bx(t), By(t)) as a small curve located at the element
        centroid in the (x,y) mesh plane.

        Parameters
        ----------
        reg_code:
            Optional region code filter.
        element_stride:
            Downsample elements for speed (e.g., 5 plots ~1/5 of elements).
        locus_scale:
            Scale factor converting Tesla to mm for drawing: (x, y) = (xc, yc) + locus_scale * (Bx, By).
            Increase to make loops bigger; decrease to make them smaller.
        show_mesh:
            If True, overlay the triangular element mesh (edges) on the same axes.
        mesh_color, mesh_linewidth, mesh_alpha:
            Style controls for the mesh overlay.
        """

        if steps is None:
            steps_list = list(getattr(ts, "steps"))
        else:
            steps_list = list(steps)
        if not steps_list:
            raise ValueError("Empty time series")

        if ref_step is None:
            ref_step = int(steps_list[0])
        if int(element_stride) < 1:
            raise ValueError("element_stride must be >= 1")

        mr_ref = getattr(ts, "by_step")[int(ref_step)]
        if not getattr(mr_ref, "node_xy", None):
            raise ValueError("NodesTable coordinates not available (node_xy is empty). Re-export including NodesTable.")

        # Collect reference elements (to get centroid locations + stable tri_index list)
        if reg_code is not None:
            if int(reg_code) <= 0:
                raise ValueError("reg_code must be >= 1")
            regions = getattr(mr_ref, "_regions", [])
            region = regions[int(reg_code) - 1] if int(reg_code) - 1 < len(regions) else None
            ref_elements = [] if region is None else (getattr(region, "elements", []) or [])
        else:
            ref_elements = []
            for region in getattr(mr_ref, "_regions", []) or []:
                ref_elements.extend(getattr(region, "elements", []) or [])

        if not ref_elements:
            raise ValueError("No elements found for the requested reg_code")

        tri_indices: list[int] = [int(getattr(e, "tri_index")) for e in ref_elements]
        centroids: list[tuple[float, float]] = []
        for e in ref_elements:
            c_xy = mr_ref._element_centroid_xy(e)
            if c_xy is None:
                centroids.append((np.nan, np.nan))
            else:
                centroids.append((float(c_xy[0]), float(c_xy[1])))

        index_of_tri = {tri: i for i, tri in enumerate(tri_indices)}

        n_steps = len(steps_list)
        n_el = len(tri_indices)
        bx_mat = np.full((n_steps, n_el), np.nan, dtype=float)
        by_mat = np.full((n_steps, n_el), np.nan, dtype=float)

        # Fill bx/by matrices by scanning each step once
        for si, step in enumerate(steps_list):
            mr = getattr(ts, "by_step")[int(step)]
            if reg_code is not None:
                regions = getattr(mr, "_regions", [])
                region = regions[int(reg_code) - 1] if int(reg_code) - 1 < len(regions) else None
                elements = [] if region is None else (getattr(region, "elements", []) or [])
            else:
                elements = []
                for region in getattr(mr, "_regions", []) or []:
                    elements.extend(getattr(region, "elements", []) or [])

            for e in elements:
                tri = int(getattr(e, "tri_index"))
                idx = index_of_tri.get(tri)
                if idx is None:
                    continue
                bx = getattr(e, "bx", None)
                by = getattr(e, "by", None)
                if bx is None or by is None:
                    continue
                bx_mat[si, idx] = float(bx)
                by_mat[si, idx] = float(by)

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        if bool(show_mesh):
            mr_ref.plot_mesh(
                reg_code=(int(reg_code) if reg_code is not None else None),
                ax=ax,
                show=False,
                color=mesh_color,
                linewidth=float(mesh_linewidth),
                alpha=float(mesh_alpha),
            )

        scale = float(locus_scale)
        stride = int(element_stride)

        # Draw each element's locus as a curve in XY plane
        for ei in range(0, n_el, stride):
            xc, yc = centroids[ei]
            if not np.isfinite(xc) or not np.isfinite(yc):
                continue
            bx = bx_mat[:, ei]
            by = by_mat[:, ei]
            valid = np.isfinite(bx) & np.isfinite(by)
            if valid.sum() < 2:
                continue

            xx = xc + scale * bx[valid]
            yy = yc + scale * by[valid]
            ax.plot(xx, yy, color=color, alpha=float(alpha), linewidth=float(linewidth))

            if mark_start_end:
                ax.scatter([xx[0]], [yy[0]], s=6, marker="^", color="tab:green", alpha=float(alpha))
                ax.scatter([xx[-1]], [yy[-1]], s=6, marker="o", color="tab:red", alpha=float(alpha))

        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")
        if equal_aspect:
            ax.set_aspect("equal", adjustable="box")

        if title is None:
            title = "B-locus field"
            if reg_code is not None:
                title += f" (reg_code={int(reg_code)})"
            title += f" | locus_scale={scale} mm/T | stride={stride}"
        ax.set_title(title)

        if show:
            plt.show()

        return ax


class MagneticRegion:
    """Container for magnetic elements belonging to the same region code."""

    def __init__(self):
        self.region_name = ""
        self.reg_code = 0
        self.elements = []  # list[MagElement]

    def add_element(
        self,
        tri_index,
        node_1,
        node_2,
        node_3,
        reg_code,
        bx=None,
        by=None,
        a=None,
        j=None,
        je=None,
        b=None,
    ):
        self.elements.append(
            MagElement(
                tri_index=tri_index,
                node_1=node_1,
                node_2=node_2,
                node_3=node_3,
                reg_code=reg_code,
                bx=bx,
                by=by,
                a=a,
                j=j,
                je=je,
                b=b,
            )
        )

    def get_b(self):
        """Return B magnitude list [T]."""
        return [el.b for el in self.elements]

    def get_bx(self):
        """Return Bx list [T] (may contain None)."""
        return [el.bx for el in self.elements]

    def get_by(self):
        """Return By list [T] (may contain None)."""
        return [el.by for el in self.elements]

    def get_a(self):
        """Return vector potential A list [Wb/m]."""
        return [el.a for el in self.elements]

    def get_j(self):
        """Return current density J list [A/mm^2]."""
        return [el.j for el in self.elements]

    def get_tri_index(self):
        return [el.tri_index for el in self.elements]

    def get_nodes(self):
        return [(el.node_1, el.node_2, el.node_3) for el in self.elements]


class MagneticRegions:
    """Collection of MagneticRegion objects indexed by region code-1."""

    def __init__(self):
        self._regions = []
        # NodeIndex -> (x_mm, y_mm) from NodesTable
        self.node_xy = {}
        # NodeIndex -> float (node-level A from NodesTable, the raw FEM solution)
        self.node_a = {}

    def __len__(self):
        return len(self._regions)

    def __getitem__(self, region_number):
        return self._regions[region_number]

    def __setitem__(self, region_number, data):
        self._regions[region_number] = data

    def add_region(self):
        self._regions.append(MagneticRegion())

    def ensure_region(self, reg_code: int):
        while reg_code > len(self._regions):
            self.add_region()

    def set_node_xy(self, node_xy):
        """Attach node coordinate map (NodeIndex -> (x_mm, y_mm))."""
        self.node_xy = dict(node_xy)

    def set_node_a(self, node_a):
        """Attach node-level A map (NodeIndex -> float) from NodesTable."""
        self.node_a = dict(node_a)

    def _element_centroid_xy(self, element: MagElement):
        """Return (x,y) centroid for a MagElement based on node coordinates."""
        n1 = self.node_xy.get(element.node_1)
        n2 = self.node_xy.get(element.node_2)
        n3 = self.node_xy.get(element.node_3)
        if n1 is None or n2 is None or n3 is None:
            return None
        x = (n1[0] + n2[0] + n3[0]) / 3.0
        y = (n1[1] + n2[1] + n3[1]) / 3.0
        return x, y

    def plot(
        self,
        reg_code=None,
        quantity="b",
        cmap="jet",
        s=2,
        ax=None,
        show=True,
        mesh=False,
        mesh_kwargs=None,
        vmin=None,
        vmax=None,
    ):
        """Scatter plot magnetic data.

        If NodesTable coordinates are available, plots element centroid (x,y) colored by quantity.
        Otherwise falls back to tri_index vs quantity.
        """

        quantity = str(quantity).lower()
        if quantity not in {"b", "a", "j"}:
            raise ValueError("quantity must be one of: 'b', 'a', 'j'")

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        if mesh:
            self.plot_mesh(reg_code=reg_code, ax=ax, show=False, **(mesh_kwargs or {}))

        xs = []
        ys = []
        cs = []
        used_xy = False

        if reg_code is None:
            regions_to_iterate = [r for r in self._regions if r.elements]
        else:
            if reg_code <= 0:
                raise ValueError("reg_code must be >= 1")
            if reg_code <= len(self._regions):
                regions_to_iterate = [self._regions[reg_code - 1]]
            else:
                regions_to_iterate = []

        for region in regions_to_iterate:
            for el in region.elements:
                v = getattr(el, quantity)
                c_xy = self._element_centroid_xy(el)
                if c_xy is not None:
                    xs.append(c_xy[0])
                    ys.append(c_xy[1])
                    cs.append(v)
                    used_xy = True
                else:
                    xs.append(el.tri_index)
                    ys.append(v)
                    cs.append(v)

        if not xs:
            ax.set_title("No data to plot")
            if show:
                plt.show()
            return ax

        if used_xy:
            sc = ax.scatter(xs, ys, c=cs, s=s, cmap=cmap, marker=".", vmin=vmin, vmax=vmax)
            ax.set_xlabel("X [mm]")
            ax.set_ylabel("Y [mm]")
            cb = ax.figure.colorbar(sc, ax=ax)
            cb.set_label({"b": "|B| [T]", "a": "A [Wb/m]", "j": "J [A/mm^2]"}[quantity])
            title_region = f"reg_code={reg_code}" if reg_code is not None else "all regions"
            ax.set_title(f"Magnetic scatter ({title_region})")
            ax.set_aspect("equal")
        else:
            ax.scatter(xs, ys, s=s, marker=".")
            ax.set_xlabel("TriIndex")
            ax.set_ylabel({"b": "|B| [T]", "a": "A [Wb/m]", "j": "J [A/mm^2]"}[quantity])
            title_region = f"reg_code={reg_code}" if reg_code is not None else "all regions"
            ax.set_title(f"Magnetic scatter (fallback: {title_region})")
            ax.grid(True)

        if show:
            plt.show()
        return ax

    def plot_quiver(
        self,
        reg_code=None,
        normalize=False,
        stride=10,
        cmap="jet",
        ax=None,
        show=True,
        scale=None,
        width=0.002,
        mesh=False,
        mesh_kwargs=None,
        vmin=None,
        vmax=None,
    ):
        """Quiver plot of the magnetic flux density vector (Bx, By)."""

        if stride is None:
            stride = 1
        stride = int(stride)
        if stride <= 0:
            raise ValueError("stride must be >= 1")

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        if mesh:
            self.plot_mesh(reg_code=reg_code, ax=ax, show=False, **(mesh_kwargs or {}))

        xs = []
        ys = []
        us = []
        vs = []
        mags = []

        if reg_code is None:
            regions_to_iterate = [r for r in self._regions if r.elements]
        else:
            if reg_code <= 0:
                raise ValueError("reg_code must be >= 1")
            if reg_code <= len(self._regions):
                regions_to_iterate = [self._regions[reg_code - 1]]
            else:
                regions_to_iterate = []

        idx = 0
        for region in regions_to_iterate:
            for el in region.elements:
                idx += 1
                if (idx - 1) % stride != 0:
                    continue
                c_xy = self._element_centroid_xy(el)
                if c_xy is None:
                    continue
                if el.bx is None or el.by is None:
                    continue
                bx = float(el.bx)
                by = float(el.by)
                mag = float((bx**2 + by**2) ** 0.5)
                if normalize:
                    if mag > 0:
                        u = bx / mag
                        v = by / mag
                    else:
                        u = 0.0
                        v = 0.0
                else:
                    u = bx
                    v = by

                xs.append(c_xy[0])
                ys.append(c_xy[1])
                us.append(u)
                vs.append(v)
                mags.append(mag)

        if not xs:
            raise ValueError(
                "No Bx/By vector data to plot. Export with 'RegCode,Bx,By,A,J' and ensure NodesTable exists."
            )

        q = ax.quiver(
            xs,
            ys,
            us,
            vs,
            mags,
            cmap=cmap,
            angles="xy",
            scale_units="xy",
            scale=scale,
            width=width,
        )
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        ax.set_aspect("equal")
        cb = ax.figure.colorbar(q, ax=ax)
        cb.set_label("|B| [T]")
        title_region = f"reg_code={reg_code}" if reg_code is not None else "all regions"
        ax.set_title(f"B vector quiver ({title_region}, normalize={bool(normalize)}, stride={stride})")

        if show:
            plt.show()
        return ax

    def plot_mesh(self, reg_code=None, ax=None, show=True, color="k", linewidth=0.2, alpha=0.7):
        """Plot element mesh (triangle edges) using NodesTable coordinates."""
        if not self.node_xy:
            raise ValueError("NodesTable coordinates not available (node_xy is empty).")
        try:
            import matplotlib.tri as mtri
        except Exception as e:
            raise RuntimeError(f"matplotlib.tri is required for mesh plotting: {e}")

        if ax is None:
            _, ax = plt.subplots(layout="constrained")

        if reg_code is None:
            regions_to_iterate = [r for r in self._regions if r.elements]
        else:
            if reg_code <= 0:
                raise ValueError("reg_code must be >= 1")
            if reg_code <= len(self._regions):
                regions_to_iterate = [self._regions[reg_code - 1]]
            else:
                regions_to_iterate = []

        node_to_local = {}
        xs = []
        ys = []
        triangles = []

        def _get_local(node_id):
            if node_id in node_to_local:
                return node_to_local[node_id]
            xy = self.node_xy.get(node_id)
            if xy is None:
                return None
            node_to_local[node_id] = len(xs)
            xs.append(float(xy[0]))
            ys.append(float(xy[1]))
            return node_to_local[node_id]

        for region in regions_to_iterate:
            for el in region.elements:
                i1 = _get_local(el.node_1)
                i2 = _get_local(el.node_2)
                i3 = _get_local(el.node_3)
                if i1 is None or i2 is None or i3 is None:
                    continue
                triangles.append((i1, i2, i3))

        if not triangles:
            raise ValueError("No triangles to plot (missing node coords or empty region).")

        tri = mtri.Triangulation(xs, ys, triangles=triangles)
        ax.triplot(tri, color=color, linewidth=linewidth, alpha=alpha)
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        ax.set_aspect("equal")
        title_region = f"reg_code={reg_code}" if reg_code is not None else "all regions"
        ax.set_title(f"Mesh (tri edges, {title_region})")
        ax.grid(False)
        if show:
            plt.show()
        return ax


class MagneticRegionsTimeSeries:
    """Container for transient/step-based magnetic data parsed from a multi-step txt."""

    def __init__(self, by_step=None, meta=None):
        self.by_step = dict(by_step or {})
        self.meta = dict(meta or {})

    @property
    def steps(self):
        return sorted(self.by_step.keys())

    def __len__(self):
        return len(self.by_step)

    def __getitem__(self, step):
        return self.by_step[step]

    def plot(self, step, **kwargs):
        return self.by_step[step].plot(**kwargs)

    def plot_quiver(self, step, **kwargs):
        return self.by_step[step].plot_quiver(**kwargs)

    def plot_mesh(self, step, **kwargs):
        return self.by_step[step].plot_mesh(**kwargs)


# Backward-compatible aliases (notebook code used underscore names)
_mcad_default_export_dir = mcad_default_export_dir
_mcad_make_temp_txt_path = mcad_make_temp_txt_path


def _parse_first_block_magnetic_file(filename) -> MagneticRegions:
    """Parse the first Elements/Nodes/Regions tables found in a Motor-CAD export txt."""

    mag_regions = MagneticRegions()
    node_xy = {}
    node_a = {}
    filename = pathlib.Path(filename)

    def _scan_to_table(in_file, table_name):
        while True:
            line = in_file.readline()
            if not line:
                return None
            if _is_table_header(line, table_name):
                return line

    with _open_mcad_text(filename) as in_file:
        elements_header = _scan_to_table(in_file, "ElementsTable")
        if elements_header is None:
            raise ValueError(f"ElementsTable not found in file: {filename}")

        number_of_elements = int(elements_header.strip().split()[1])
        elem_ci = _read_col_indices(in_file, _ELEM_COL_KEYS)
        ti_i  = elem_ci.get("TriIndex", 0)
        n1_i  = elem_ci.get("Node1",    1)
        n2_i  = elem_ci.get("Node2",    2)
        n3_i  = elem_ci.get("Node3",    3)
        rc_i  = elem_ci.get("RegCode",  4)
        bx_i  = elem_ci.get("Bx",  5)
        by_i  = elem_ci.get("By",  6)
        a_i   = elem_ci.get("A",   7)
        j_i   = elem_ci.get("J",   8)
        je_i  = elem_ci.get("Je")
        # "B" column present in old format (single combined B value)
        b_i   = elem_ci.get("B")

        for _ in range(number_of_elements):
            row = in_file.readline().split(sep=",")
            try:
                reg_code = int(row[rc_i])
            except (ValueError, IndexError):
                continue
            mag_regions.ensure_region(reg_code)
            if b_i is None:
                mag_regions[reg_code - 1].add_element(
                    tri_index=row[ti_i],
                    node_1=row[n1_i],
                    node_2=row[n2_i],
                    node_3=row[n3_i],
                    reg_code=row[rc_i],
                    bx=row[bx_i],
                    by=row[by_i],
                    a=row[a_i],
                    j=row[j_i],
                    je=row[je_i] if je_i is not None else None,
                )
            else:
                mag_regions[reg_code - 1].add_element(
                    tri_index=row[ti_i],
                    node_1=row[n1_i],
                    node_2=row[n2_i],
                    node_3=row[n3_i],
                    reg_code=row[rc_i],
                    b=row[b_i],
                    a=row[a_i],
                    j=row[j_i],
                )

        nodes_header = _scan_to_table(in_file, "NodesTable")
        if nodes_header is not None:
            number_of_nodes = int(nodes_header.strip().split()[1])
            node_ci = _read_col_indices(in_file, _NODE_COL_KEYS)
            ni_i = node_ci.get("NodeIndex", 0)
            x_i  = node_ci.get("X", 1)
            y_i  = node_ci.get("Y", 2)
            a_node_i = node_ci.get("A")
            for _ in range(number_of_nodes):
                row = in_file.readline().split(sep=",")
                try:
                    node_idx = int(row[ni_i])
                    x_mm = float(row[x_i])
                    y_mm = float(row[y_i])
                    node_xy[node_idx] = (x_mm, y_mm)
                    if a_node_i is not None:
                        node_a[node_idx] = float(row[a_node_i])
                except (ValueError, IndexError):
                    pass

        regions_header = _scan_to_table(in_file, "RegionsTable")
        if regions_header is not None:
            number_of_regions = int(regions_header.strip().split()[1])
            region_ci = _read_col_indices(in_file, _REGION_COL_KEYS)
            rc2_i = region_ci.get("RegionCode", 0)
            rn_i  = region_ci.get("RegionName")
            for _ in range(number_of_regions):
                row = in_file.readline().split(sep=",")
                try:
                    reg_code = int(row[rc2_i])
                except (ValueError, IndexError):
                    continue
                if reg_code <= len(mag_regions):
                    mag_regions[reg_code - 1].reg_code = reg_code
                    mag_regions[reg_code - 1].region_name = (
                        row[rn_i].strip() if rn_i is not None and rn_i < len(row)
                        else row[-1].strip()
                    )

    mag_regions.set_node_xy(node_xy)
    mag_regions.set_node_a(node_a)
    return mag_regions


def get_magnetic_data(
    mc,
    first_step=1,
    final_step=1,
    *,
    filename: str | pathlib.Path | None = None,
    clean_up: bool = True,
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
        final_step=int(final_step),
        filename=export_path,
        columns="RegCode,Bx,By,A,J,Je",
        sep=",",
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


def export_magnetic_txt(
    mc,
    *,
    first_step: int = 1,
    final_step: int = 1,
    filename: str | pathlib.Path,
    columns: str = "RegCode,Bx,By,A,J,Je",
    sep: str = ",",
) -> pathlib.Path:
    """Export magnetic FEA data to a txt file (no parsing)."""
    return save_fea_text_export(
        mc,
        filename=filename,
        first_step=int(first_step),
        final_step=int(final_step),
        columns=str(columns),
        sep=str(sep),
    )


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


_MCAD_STEP_HEADER_RE = re.compile(
    r"^\s*(?P<prefix>\d+)\s+Solution\s+(?P<solution>\d+)"
    r"(?:\s+Time\s+index\s+(?P<time_index>-?\d+)\s+Time\s+(?P<time_s>[-+0-9.Ee]+)\s+\[s\])?"
    r"\s+Rotate\s+Step\s+(?P<rotate_step>[-+0-9.Ee]+)\s*$",
    re.IGNORECASE,
)


def _is_table_header(line: str, table_name: str) -> bool:
    tokens = line.strip().split()
    return len(tokens) >= 3 and tokens[1].isdigit() and tokens[2].strip() == table_name


def _read_until_table_header(in_file, table_name: str):
    """Advance until a '<idx> <N> {table_name}' line is found; return that line or None."""

    while True:
        pos = in_file.tell()
        line = in_file.readline()
        if not line:
            return None
        if _is_table_header(line, table_name):
            return line
        if _MCAD_STEP_HEADER_RE.match(line.strip()):
            in_file.seek(pos)
            return None


def _skip_header_lines(in_file, n=4):
    for _ in range(n):
        in_file.readline()


_ELEM_COL_KEYS = frozenset({"TriIndex", "Node1", "Node2", "Node3", "RegCode", "Bx", "By", "A", "J", "Je"})
_NODE_COL_KEYS = frozenset({"NodeIndex", "X", "Y", "A"})
_REGION_COL_KEYS = frozenset({"RegionCode", "RegionName"})


def _read_col_indices(in_file, expected_keys: frozenset) -> dict:
    """Read 4-line preamble and return {column_name: index} for expected_keys.

    MotorCAD TXT preamble after a table section header:
        line 1: blank
        line 2: column names  <- parsed here (previously skipped by _skip_header_lines)
        line 3: units
        line 4: separator (----)
    """
    in_file.readline()            # blank
    col_line = in_file.readline() # column names
    in_file.readline()            # units
    in_file.readline()            # separator
    tokens = [t.strip() for t in col_line.split(",")]
    return {t: i for i, t in enumerate(tokens) if t in expected_keys}


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
            # Represent snapshot as a single-step time series for convenience.
            mr = _magnetic_regions_from_snapshot_h5(filename)
            ts1 = MagneticRegionsTimeSeries(by_step={1: mr}, meta={1: {"solution": None, "time_index": 1}})
            return ts1
        raise ValueError(f"Unrecognized magnetic h5 format: {fmt}")

    ts = MagneticRegionsTimeSeries()

    with _open_mcad_text(filename) as in_file:
        while True:
            line = in_file.readline()
            if not line:
                break

            m = _MCAD_STEP_HEADER_RE.match(line.strip())
            if not m:
                continue

            meta = {
                "raw_header": line.strip(),
                "solution": int(m.group("solution")),
                "time_index": int(m.group("time_index")) if m.group("time_index") is not None else None,
                "time_s": float(m.group("time_s")) if m.group("time_s") is not None else None,
                "rotate_step": float(m.group("rotate_step")) if m.group("rotate_step") is not None else None,
            }

            if key == "time_index":
                if meta["time_index"] is not None:
                    step_key = meta["time_index"]
                else:
                    step_key = 0 if 0 not in ts.by_step else meta["solution"]
            elif key == "solution":
                step_key = meta["solution"]
            else:
                step_key = meta["solution"]

            elements_header = _read_until_table_header(in_file, "ElementsTable")
            if elements_header is None:
                if verbose:
                    print("No ElementsTable after:", meta["raw_header"])
                continue

            n_elements = int(elements_header.strip().split()[1])
            elem_ci = _read_col_indices(in_file, _ELEM_COL_KEYS)
            ti_i  = elem_ci.get("TriIndex", 0)
            n1_i  = elem_ci.get("Node1",    1)
            n2_i  = elem_ci.get("Node2",    2)
            n3_i  = elem_ci.get("Node3",    3)
            rc_i  = elem_ci.get("RegCode",  4)
            bx_i  = elem_ci.get("Bx",  5)
            by_i  = elem_ci.get("By",  6)
            a_i   = elem_ci.get("A",   7)
            j_i   = elem_ci.get("J",   8)
            je_i  = elem_ci.get("Je")
            b_i   = elem_ci.get("B")

            mag_regions = MagneticRegions()
            for _ in range(n_elements):
                row = in_file.readline().split(sep=",")
                try:
                    reg_code = int(row[rc_i])
                except (ValueError, IndexError):
                    continue
                mag_regions.ensure_region(reg_code)
                if b_i is None:
                    mag_regions[reg_code - 1].add_element(
                        tri_index=row[ti_i],
                        node_1=row[n1_i],
                        node_2=row[n2_i],
                        node_3=row[n3_i],
                        reg_code=row[rc_i],
                        bx=row[bx_i],
                        by=row[by_i],
                        a=row[a_i],
                        j=row[j_i],
                        je=row[je_i] if je_i is not None else None,
                    )
                else:
                    mag_regions[reg_code - 1].add_element(
                        tri_index=row[ti_i],
                        node_1=row[n1_i],
                        node_2=row[n2_i],
                        node_3=row[n3_i],
                        reg_code=row[rc_i],
                        b=row[b_i],
                        a=row[a_i],
                        j=row[j_i],
                    )

            node_xy = {}
            node_a = {}
            nodes_header = _read_until_table_header(in_file, "NodesTable")
            if nodes_header is not None:
                n_nodes = int(nodes_header.strip().split()[1])
                node_ci = _read_col_indices(in_file, _NODE_COL_KEYS)
                ni_i = node_ci.get("NodeIndex", 0)
                x_i  = node_ci.get("X", 1)
                y_i  = node_ci.get("Y", 2)
                a_node_i = node_ci.get("A")
                for _ in range(n_nodes):
                    row = in_file.readline().split(sep=",")
                    try:
                        node_idx = int(row[ni_i])
                        x_mm = float(row[x_i])
                        y_mm = float(row[y_i])
                        node_xy[node_idx] = (x_mm, y_mm)
                        if a_node_i is not None:
                            node_a[node_idx] = float(row[a_node_i])
                    except (ValueError, IndexError):
                        pass
            mag_regions.set_node_xy(node_xy)
            mag_regions.set_node_a(node_a)

            regions_header = _read_until_table_header(in_file, "RegionsTable")
            if regions_header is not None:
                n_regions = int(regions_header.strip().split()[1])
                region_ci = _read_col_indices(in_file, _REGION_COL_KEYS)
                rc2_i = region_ci.get("RegionCode", 0)
                rn_i  = region_ci.get("RegionName")
                for _ in range(n_regions):
                    row = in_file.readline().split(sep=",")
                    try:
                        reg_code = int(row[rc2_i])
                    except (ValueError, IndexError):
                        continue
                    if reg_code <= len(mag_regions):
                        mag_regions[reg_code - 1].reg_code = reg_code
                        mag_regions[reg_code - 1].region_name = (
                            row[rn_i].strip() if rn_i is not None and rn_i < len(row)
                            else row[-1].strip()
                        )

            ts.by_step[step_key] = mag_regions
            ts.meta[step_key] = meta

            if verbose:
                print(f"Parsed block key={step_key}: elements={n_elements}, nodes={len(node_xy)}")

            if max_blocks is not None and len(ts) >= int(max_blocks):
                break

    if clean_up:
        try:
            filename.unlink()
        except FileNotFoundError:
            pass

    return ts


# -------- Interactive plotting helpers (optional dependency: ipywidgets) --------
try:
    import ipywidgets as widgets
    from IPython.display import display
except Exception:
    widgets = None
    display = None


def interactive_magnetic_plot(ts: MagneticRegionsTimeSeries, initial_step=None, quantity="b", reg_code=None, s=2, cmap="jet"):
    """Interactive step toggle plot for MagneticRegionsTimeSeries."""

    if widgets is None or display is None:
        raise RuntimeError("ipywidgets is required for interactive plotting")
    if len(ts) == 0:
        raise ValueError("Empty time series.")

    steps = ts.steps
    if initial_step is None:
        initial_step = steps[0]

    step_slider = widgets.SelectionSlider(
        options=steps,
        value=initial_step,
        description="step",
        continuous_update=False,
        layout=widgets.Layout(width="650px"),
    )
    qty_dd = widgets.Dropdown(
        options=[("B", "b"), ("A", "a"), ("J", "j")],
        value=str(quantity).lower(),
        description="qty",
    )
    mesh_chk = widgets.Checkbox(value=False, description="mesh", indent=False)

    def _region_options_for_step(step):
        mr = ts.by_step[int(step)]
        options = [("all", None)]
        regions = getattr(mr, "_regions", [])
        for idx, region in enumerate(regions):
            if not getattr(region, "elements", None):
                continue
            code = getattr(region, "reg_code", 0) or (idx + 1)
            name = (getattr(region, "region_name", "") or "").strip()
            label = f"{int(code)}: {name}" if name else str(int(code))
            options.append((label, int(code)))
        return options

    reg_dd = widgets.Dropdown(
        options=_region_options_for_step(step_slider.value),
        value=(None if reg_code is None else int(reg_code)),
        description="reg_code",
    )
    if reg_dd.value not in [v for (_, v) in reg_dd.options]:
        reg_dd.value = None

    size_slider = widgets.FloatSlider(
        value=float(s),
        min=0.1,
        max=20.0,
        step=0.1,
        description="size",
        continuous_update=False,
        readout_format=".1f",
    )
    out = widgets.Output()

    # Keep track of the last figure so ipympl/widget backends don't leave stale canvases.
    _last_fig = {"fig": None}

    def _sync_reg_options(*_):
        current = reg_dd.value
        new_options = _region_options_for_step(step_slider.value)
        reg_dd.options = new_options
        values = [v for (_, v) in new_options]
        reg_dd.value = current if current in values else None

    def _draw(*_):
        with out:
            out.clear_output(wait=True)
            try:
                if _last_fig["fig"] is not None:
                    plt.close(_last_fig["fig"])
            except Exception:
                pass
            fig, ax = plt.subplots(layout="constrained")
            _last_fig["fig"] = fig
            step = int(step_slider.value)
            qty = str(qty_dd.value).lower()
            rc = reg_dd.value
            ax = ts.by_step[step].plot(
                reg_code=rc,
                quantity=qty,
                s=size_slider.value,
                cmap=cmap,
                ax=ax,
                show=False,
                mesh=bool(mesh_chk.value),
            )
            header = ts.meta.get(step, {}).get("raw_header")
            if header:
                ax.set_title(f"{ax.get_title()}\n{header}")
            plt.show()
            # In widget backends, keep the figure open (it's the displayed canvas).
            # For non-interactive inline/agg backends, close to avoid duplicated static images.
            backend = str(matplotlib.get_backend()).lower()
            if "inline" in backend or backend.endswith("agg") or "agg" in backend:
                plt.close(fig)
            return ax

    step_slider.observe(_sync_reg_options, names="value")
    step_slider.observe(_draw, names="value")
    qty_dd.observe(_draw, names="value")
    mesh_chk.observe(_draw, names="value")
    reg_dd.observe(_draw, names="value")
    size_slider.observe(_draw, names="value")

    display(widgets.VBox([widgets.HBox([step_slider, qty_dd, mesh_chk]), widgets.HBox([reg_dd, size_slider]), out]))
    _draw()


def interactive_magnetic_quiver(
    ts: MagneticRegionsTimeSeries,
    initial_step=None,
    reg_code=None,
    normalize=False,
    stride=20,
    scale=None,
    width=0.002,
    cmap="jet",
    layout_width="650px",
):
    """Interactive step toggle quiver plot for MagneticRegionsTimeSeries."""

    if widgets is None or display is None:
        raise RuntimeError("ipywidgets is required for interactive plotting")
    if len(ts) == 0:
        raise ValueError("Empty time series.")

    steps = ts.steps
    if initial_step is None:
        initial_step = steps[0]

    step_slider = widgets.SelectionSlider(
        options=steps,
        value=initial_step,
        description="step",
        continuous_update=False,
        layout=widgets.Layout(width=layout_width),
    )
    normalize_chk = widgets.Checkbox(value=bool(normalize), description="normalize", indent=False)
    mesh_chk = widgets.Checkbox(value=False, description="mesh", indent=False)
    stride_slider = widgets.IntSlider(
        value=int(stride),
        min=1,
        max=200,
        step=1,
        description="stride",
        continuous_update=False,
    )
    scale_text = widgets.Text(value="" if scale is None else str(scale), description="scale", placeholder="(blank=None)")
    width_text = widgets.FloatText(value=float(width), description="width")
    out = widgets.Output()

    # Keep track of the last figure so ipympl/widget backends don't leave stale canvases.
    _last_fig = {"fig": None}

    def _parse_scale(text):
        t = str(text).strip()
        if t == "":
            return None
        return float(t)

    def _region_options_for_step(step):
        mr = ts.by_step[int(step)]
        options = [("all", None)]
        regions = getattr(mr, "_regions", [])
        for idx, region in enumerate(regions):
            if not getattr(region, "elements", None):
                continue
            code = getattr(region, "reg_code", 0) or (idx + 1)
            name = (getattr(region, "region_name", "") or "").strip()
            label = f"{code}: {name}" if name else str(code)
            options.append((label, int(code)))
        return options

    reg_dd = widgets.Dropdown(options=_region_options_for_step(step_slider.value), value=(None if reg_code is None else int(reg_code)), description="reg_code")
    if reg_dd.value not in [v for (_, v) in reg_dd.options]:
        reg_dd.value = None

    def _sync_reg_options(*_):
        current = reg_dd.value
        new_options = _region_options_for_step(step_slider.value)
        reg_dd.options = new_options
        values = [v for (_, v) in new_options]
        reg_dd.value = current if current in values else None

    def _draw(*_):
        with out:
            out.clear_output(wait=True)
            try:
                if _last_fig["fig"] is not None:
                    plt.close(_last_fig["fig"])
            except Exception:
                pass
            fig, ax = plt.subplots(layout="constrained")
            _last_fig["fig"] = fig
            step = int(step_slider.value)
            sc = _parse_scale(scale_text.value)
            ax = ts.by_step[step].plot_quiver(
                reg_code=reg_dd.value,
                normalize=bool(normalize_chk.value),
                stride=int(stride_slider.value),
                cmap=cmap,
                ax=ax,
                show=False,
                scale=sc,
                width=float(width_text.value),
                mesh=bool(mesh_chk.value),
            )
            header = ts.meta.get(step, {}).get("raw_header")
            if header:
                ax.set_title(f"{ax.get_title()}\n{header}")
            plt.show()
            backend = str(matplotlib.get_backend()).lower()
            if "inline" in backend or backend.endswith("agg") or "agg" in backend:
                plt.close(fig)
            return ax

    step_slider.observe(_sync_reg_options, names="value")
    step_slider.observe(_draw, names="value")
    reg_dd.observe(_draw, names="value")
    normalize_chk.observe(_draw, names="value")
    mesh_chk.observe(_draw, names="value")
    stride_slider.observe(_draw, names="value")
    scale_text.observe(_draw, names="value")
    width_text.observe(_draw, names="value")

    display(
        widgets.VBox(
            [
                widgets.HBox([step_slider]),
                widgets.HBox([reg_dd, normalize_chk, mesh_chk]),
                widgets.HBox([stride_slider, scale_text, width_text]),
                out,
            ]
        )
    )
    _sync_reg_options()
    _draw()
