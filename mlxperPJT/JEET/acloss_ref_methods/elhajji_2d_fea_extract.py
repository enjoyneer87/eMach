"""
El-Hajji step (B) - stage 1: extract per-conductor B(t) from Motor-CAD
FEA_data.txt mesh exports (Hybrid magnetostatic sweep, e10 SLFEA_Half model).

Input : D:/KangDH/Thesis/e10/SLFEA_Half/ACLossCalcExport_Map/
          Hybrid_Speed_{rpm}RPM_460.0A_{phase}deg/FEA_data.txt   (~435 MB each)
        Multi-step Motor-CAD magnetic export:
          "<pfx> Solution <n> [Time index <i> Time <t> [s]] Rotate Step <deg>"
          ElementsTable (TriIndex,Node1..3,RegCode,Bx,By,A,J,Je,Hx,Hy,Mur)
          NodesTable (NodeIndex,X,Y [mm]) / RegionsTable (RegionCode,RegionName)

Model facts (verified):
  - 1/8 machine sector: 6 slots (A..F) x 6 conductors = 36 regions
    named 'ArmatureSlot<slot><layer>'; full machine factor = 8.
  - 128 time steps x 0.7031 deg mech = 90 deg mech = 360 deg elec (1 cycle).

Output: elhajji_b_data/<case>.json with, per copper region:
  reg_code, name, centroid_xy [mm], area_mm2, Bx[t], By[t]  (area-weighted mean)

Performance trick: element row order is identical in every block, so copper
row ordinals are located once in block 1 and only those rows are parsed in
subsequent blocks (~1.5 k of 18.7 k rows per block).  TriIndex is verified on
every parsed row; a mismatch aborts loudly rather than corrupting data.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

BASE = Path(r"D:\KangDH\Thesis\e10\SLFEA_Half\ACLossCalcExport_Map")
OUT_DIR = Path(__file__).resolve().parent / "elhajji_b_data"
COPPER_RE = re.compile(r"^ArmatureSlot[A-F]\d$")

# speed -> phase list bracketing 43.33 deg (8000 rpm grid has no 36 deg)
CASES = {
    2000: [36.0, 54.0],
    4000: [36.0, 54.0],
    8000: [18.0, 54.0],
    16000: [36.0, 54.0],
}
CURRENT_A = 460.0

_STEP_RE = re.compile(
    r"^\s*\d+\s+Solution\s+(?P<sol>\d+)"
    r"(?:\s+Time\s+index\s+(?P<ti>-?\d+)\s+Time\s+(?P<t>[-+0-9.Ee]+)\s+\[s\])?"
    r"\s+Rotate\s+Step\s+(?P<rot>[-+0-9.Ee]+)\s*$")


def _is_table(line: str, name: str) -> int | None:
    tok = line.split()
    if len(tok) >= 3 and tok[1].isdigit() and tok[2] == name:
        return int(tok[1])
    return None


def _read_preamble_cols(f) -> list[str]:
    """blank / column names / units / dashes -> return column names."""
    f.readline()
    cols = [t.strip() for t in f.readline().split(",")]
    f.readline()
    f.readline()
    return cols


def _tri_area_centroid(node_xy, n1, n2, n3):
    p1, p2, p3 = node_xy[n1], node_xy[n2], node_xy[n3]
    area = 0.5 * abs(p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1])
                     + p3[0] * (p1[1] - p2[1]))
    cx = (p1[0] + p2[0] + p3[0]) / 3.0
    cy = (p1[1] + p2[1] + p3[1]) / 3.0
    return area, cx, cy


def extract_case(fea_path: Path) -> dict:
    t0 = time.time()
    with open(fea_path, "r", encoding="utf-8", errors="replace") as f:
        # ---- block 1: topology -------------------------------------------
        step_meta = []
        line = f.readline()
        while line and _STEP_RE.match(line.strip()) is None:
            line = f.readline()
        if not line:
            raise ValueError(f"no step header in {fea_path}")
        step_meta.append(_STEP_RE.match(line.strip()).groupdict())

        while True:
            line = f.readline()
            n_el = _is_table(line, "ElementsTable")
            if n_el is not None:
                break
        cols = _read_preamble_cols(f)
        ci = {c: i for i, c in enumerate(cols)}
        ti_i, rc_i = ci["TriIndex"], ci["RegCode"]
        n1_i, n2_i, n3_i = ci["Node1"], ci["Node2"], ci["Node3"]
        bx_i, by_i = ci["Bx"], ci["By"]

        elems = []  # (tri, n1, n2, n3, rc) in row order
        b0 = []     # (bx, by) of block 1 in row order
        for _ in range(n_el):
            row = f.readline().split(",")
            elems.append((int(row[ti_i]), int(row[n1_i]), int(row[n2_i]),
                          int(row[n3_i]), int(row[rc_i])))
            b0.append((float(row[bx_i]), float(row[by_i])))

        while True:
            line = f.readline()
            n_nodes = _is_table(line, "NodesTable")
            if n_nodes is not None:
                break
        _read_preamble_cols(f)
        node_xy = {}
        for _ in range(n_nodes):
            row = f.readline().split(",")
            node_xy[int(row[0])] = (float(row[1]), float(row[2]))

        while True:
            line = f.readline()
            n_reg = _is_table(line, "RegionsTable")
            if n_reg is not None:
                break
        _read_preamble_cols(f)
        reg_names = {}
        for _ in range(n_reg):
            row = f.readline().split(",")
            reg_names[int(row[0])] = row[-1].strip()

        copper_rc = {rc for rc, nm in reg_names.items() if COPPER_RE.match(nm)}
        if not copper_rc:
            raise ValueError(f"no copper regions matched in {fea_path}")

        # copper row ordinals + per-element weights, per-region aggregates
        cop_pos = []          # (ordinal, tri, rc, weight)
        reg_area = {rc: 0.0 for rc in copper_rc}
        reg_cx = {rc: 0.0 for rc in copper_rc}
        reg_cy = {rc: 0.0 for rc in copper_rc}
        for ordinal, (tri, n1, n2, n3, rc) in enumerate(elems):
            if rc not in copper_rc:
                continue
            a, cx, cy = _tri_area_centroid(node_xy, n1, n2, n3)
            cop_pos.append((ordinal, tri, rc, a))
            reg_area[rc] += a
            reg_cx[rc] += cx * a
            reg_cy[rc] += cy * a
        for rc in copper_rc:
            reg_cx[rc] /= reg_area[rc]
            reg_cy[rc] /= reg_area[rc]

        # block-1 B accumulation (region means + per-element series)
        rc_list = sorted(copper_rc)
        rc_idx = {rc: i for i, rc in enumerate(rc_list)}
        el_bx = [[] for _ in cop_pos]   # per copper element time series
        el_by = [[] for _ in cop_pos]
        sums = [[0.0, 0.0] for _ in rc_list]
        for j, (ordinal, tri, rc, w) in enumerate(cop_pos):
            bx, by = b0[ordinal]
            el_bx[j].append(bx)
            el_by[j].append(by)
            sums[rc_idx[rc]][0] += bx * w
            sums[rc_idx[rc]][1] += by * w
        bx_series = [[s[0] / reg_area[rc_list[i]]] for i, s in enumerate(sums)]
        by_series = [[s[1] / reg_area[rc_list[i]]] for i, s in enumerate(sums)]

        # ---- remaining blocks: parse only copper ordinals -----------------
        pending_meta = None
        while True:
            line = f.readline()
            if not line:
                break
            m = _STEP_RE.match(line.strip())
            if m:
                pending_meta = m.groupdict()
                continue
            n_el2 = _is_table(line, "ElementsTable")
            if n_el2 is None:
                continue
            if n_el2 != n_el:
                raise ValueError(f"element count changed: {n_el} -> {n_el2}")
            _read_preamble_cols(f)
            sums = [[0.0, 0.0] for _ in rc_list]
            pos_iter = iter(enumerate(cop_pos))
            j_nxt = next(pos_iter, None)
            for ordinal in range(n_el):
                row_line = f.readline()
                if j_nxt is None or ordinal != j_nxt[1][0]:
                    continue
                j, nxt = j_nxt
                row = row_line.split(",")
                tri = int(row[ti_i])
                if tri != nxt[1]:
                    raise ValueError(
                        f"TriIndex mismatch at ordinal {ordinal}: "
                        f"{tri} != {nxt[1]} (mesh changed between steps?)")
                i = rc_idx[nxt[2]]
                w = nxt[3]
                bx = float(row[bx_i])
                by = float(row[by_i])
                el_bx[j].append(bx)
                el_by[j].append(by)
                sums[i][0] += bx * w
                sums[i][1] += by * w
                j_nxt = next(pos_iter, None)
            step_meta.append(pending_meta or {})
            pending_meta = None
            for i, rc in enumerate(rc_list):
                bx_series[i].append(sums[i][0] / reg_area[rc])
                by_series[i].append(sums[i][1] / reg_area[rc])

    regions = []
    for i, rc in enumerate(rc_list):
        elements = []
        for j, (ordinal, tri, rc_e, w) in enumerate(cop_pos):
            if rc_e != rc:
                continue
            elements.append({
                "tri": tri,
                "w_mm2": round(w, 5),
                "Bx_T": [round(v, 4) for v in el_bx[j]],
                "By_T": [round(v, 4) for v in el_by[j]],
            })
        regions.append({
            "reg_code": rc,
            "name": reg_names[rc],
            "centroid_xy_mm": [round(reg_cx[rc], 4), round(reg_cy[rc], 4)],
            "area_mm2": round(reg_area[rc], 5),
            "Bx_T": [round(v, 6) for v in bx_series[i]],
            "By_T": [round(v, 6) for v in by_series[i]],
            "elements": elements,
        })
    out = {
        "version": 2,
        "source": str(fea_path),
        "n_steps_total": len(step_meta),
        "step_meta": step_meta,
        "n_elements": n_el,
        "regions": regions,
        "elapsed_s": round(time.time() - t0, 1),
    }
    return out


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for speed, phases in CASES.items():
        for ph in phases:
            case = f"Hybrid_Speed_{speed}RPM_{CURRENT_A:.1f}A_{ph}deg"
            src = BASE / case / "FEA_data.txt"
            dst = OUT_DIR / f"{case}.json"
            if dst.exists():
                print(f"[skip] {dst.name} already extracted")
                continue
            if not src.exists():
                print(f"[MISS] {src}")
                continue
            print(f"[extract] {case} ...", flush=True)
            data = extract_case(src)
            data["speed_rpm"] = speed
            data["phase_deg"] = ph
            data["current_A"] = CURRENT_A
            with open(dst, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            print(f"    -> {dst.name}: {len(data['regions'])} regions, "
                  f"{data['n_steps_total']} steps, {data['elapsed_s']} s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
