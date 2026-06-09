"""Magnetic FEA text file parsing infrastructure.

Parsers for Motor-CAD electromagnetic export .txt files.
"""
from __future__ import annotations

import io
import pathlib
import re
from contextlib import contextmanager

from .magnetic_model import MagElement, MagneticRegion, MagneticRegions, MagneticRegionsTimeSeries


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
_NODE_COL_KEYS = frozenset({"NodeIndex", "X", "Y"})
_REGION_COL_KEYS = frozenset({"RegionCode", "RegionName"})


def _read_col_indices(in_file, expected_keys: frozenset) -> dict:
    """Read 4-line preamble and return {column_name: index} for expected_keys.

    MotorCAD TXT preamble after a table section header:
        line 1: blank
        line 2: column names  <- parsed here
        line 3: units
        line 4: separator (----)
    """
    in_file.readline()            # blank
    col_line = in_file.readline() # column names
    in_file.readline()            # units
    in_file.readline()            # separator
    tokens = [t.strip() for t in col_line.split(",")]
    return {t: i for i, t in enumerate(tokens) if t in expected_keys}


def _parse_first_block_magnetic_file(filename) -> MagneticRegions:
    """Parse the first Elements/Nodes/Regions tables found in a Motor-CAD export txt."""

    mag_regions = MagneticRegions()
    node_xy = {}
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
            for _ in range(number_of_nodes):
                row = in_file.readline().split(sep=",")
                try:
                    node_idx = int(row[ni_i])
                    x_mm = float(row[x_i])
                    y_mm = float(row[y_i])
                    node_xy[node_idx] = (x_mm, y_mm)
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
    return mag_regions


def _parse_magnetic_timeseries_txt(
    filename,
    key="time_index",
    max_blocks=None,
    verbose=False,
) -> MagneticRegionsTimeSeries:
    """Parse a Motor-CAD multi-step electromagnetic txt into MagneticRegionsTimeSeries (txt only)."""

    filename = pathlib.Path(filename)
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
            nodes_header = _read_until_table_header(in_file, "NodesTable")
            if nodes_header is not None:
                n_nodes = int(nodes_header.strip().split()[1])
                node_ci = _read_col_indices(in_file, _NODE_COL_KEYS)
                ni_i = node_ci.get("NodeIndex", 0)
                x_i  = node_ci.get("X", 1)
                y_i  = node_ci.get("Y", 2)
                for _ in range(n_nodes):
                    row = in_file.readline().split(sep=",")
                    try:
                        node_idx = int(row[ni_i])
                        x_mm = float(row[x_i])
                        y_mm = float(row[y_i])
                        node_xy[node_idx] = (x_mm, y_mm)
                    except (ValueError, IndexError):
                        pass
            mag_regions.set_node_xy(node_xy)

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

    return ts
