"""Extract the existing line-sampled B spectra from 30 Ref MS field exports.

No Full-FEA or target-machine fields are consumed. Geometry dilation is
checked against the same sampling operator. The inherited 128-sample FFT
and area-weighted line convention are retained, not reinterpreted as a
new reference-loss quadrature or a mesh-convergence result.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np

from run_meshb_hybrid_all import load_series
from run_line_sampled_hybrid import op_line_losses

HERE = Path(__file__).resolve().parent
OP_PATTERN = re.compile(r"Hybrid_Speed_16000RPM_([\d.]+)A_([\d.]+)deg$")
SCHEMA = "ref-ms-line-spectra-v1"


def file_sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def code_hashes():
    paths = [HERE / "run_meshb_hybrid_all.py",
             HERE / "run_line_sampled_hybrid.py",
             HERE.parent.parent / "tools/jeet_acloss_rbf/field_metrics.py"]
    return {path.name: file_sha256(path) for path in paths}


def field_header(path):
    """Capture source format without printing or hashing unrelated inputs."""
    lines = []
    with gzip.open(path, "rt", encoding="utf-8", errors="strict") as stream:
        for _ in range(16):
            line = stream.readline()
            if not line:
                break
            lines.append(line.rstrip())
    return lines


def extract_one(job):
    path_text, out_text, hashes = job
    path, out = Path(path_text), Path(out_text)
    checksum = file_sha256(path)
    if out.exists():
        cached = json.loads(out.read_text(encoding="utf-8"))
        if (cached.get("schema") == SCHEMA
                and cached.get("raw_sha256") == checksum
                and cached.get("code_hashes") == hashes):
            return {"name": path.parent.name, "cached": True, "row": cached}
    started = time.monotonic()
    matched = OP_PATTERN.fullmatch(path.parent.name)
    if matched is None:
        return {"error": f"invalid Ref MS path: {path}"}
    meta, bx, by = load_series(str(path))
    if bx.shape[0] != 128 or len(set(meta["reg"])) != 36:
        return {"error": f"unexpected time/conductor coverage: {path}"}
    base = op_line_losses(meta, bx, by, 16000 * 4 / 60,
                          3.711e-3, 1.686e-3, 25, 1.12)
    dilation = {}
    for scale in (1.5, 2.0):
        scaled_meta = dict(meta, x=meta["x"] * scale,
                           y=meta["y"] * scale,
                           area=meta["area"] * scale ** 2)
        other = op_line_losses(scaled_meta, bx, by, 16000 * 4 / 60,
                               3.711e-3 * scale, 1.686e-3 * scale,
                               25, 1.12)
        delta = max(float(np.max(np.abs(np.asarray(base[key])
                                         - np.asarray(other[key]))))
                    for key in ("b2t_msq_sum", "b2r_msq_sum"))
        dilation[str(scale)] = delta
        if delta > 1e-10:
            return {"error": f"line sampling changed under dilation: {path}, {delta}"}
    row = {
        "schema": SCHEMA, "raw_path": str(path.resolve()),
        "raw_sha256": checksum, "raw_bytes": path.stat().st_size,
        "code_hashes": hashes, "header": field_header(path),
        "source_model": "Ref", "source_mode": "Hybrid_MS",
        "source_speed_rpm": 16000, "current_A": float(matched.group(1)),
        "phase_deg": float(matched.group(2)),
        "n_steps": bx.shape[0], "n_elements": bx.shape[1],
        "n_conductors_per_sector": len(set(meta["reg"])),
        "b2t_msq_sum": base["b2t_msq_sum"],
        "b2r_msq_sum": base["b2r_msq_sum"],
        "spectrum_serialization": "6 significant digits, existing exporter convention",
        "geometry_dilation_max_abs_T2": dilation,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, indent=2), encoding="utf-8")
    return {"name": path.parent.name, "cached": False,
            "elapsed_s": time.monotonic() - started, "row": row}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref-fields", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args(argv)
    paths = sorted(args.ref_fields.glob("Hybrid_Speed_16000RPM_*/FEA_data.txt.gz"))
    if len(paths) != 30:
        print(f"Expected 30 Ref MS fields, found {len(paths)}", flush=True)
        return 2
    hashes = code_hashes()
    jobs = [(str(path), str(args.out / "points" / (path.parent.name + ".json")), hashes)
            for path in paths]
    rows = []
    with ProcessPoolExecutor(max_workers=max(1, min(args.workers, 2))) as pool:
        for result in pool.map(extract_one, jobs):
            if "error" in result:
                print(result["error"], flush=True)
                return 2
            rows.append(result["row"])
            print(f"[{len(rows):02d}/30] {result['name']} "
                  f"{'cached' if result['cached'] else str(round(result['elapsed_s'], 1)) + ' s'}",
                  flush=True)
    artifact = {
        "schema": SCHEMA, "rows": rows,
        "metadata": {
            "input_count": 30, "field_solve_mode": "magnetostatic rotor-stepped",
            "n_lines": 25, "line_ratio": 1.12,
            "field_units": "T", "geometry_units": "mm",
            "FFT": "existing 2*abs(rfft)/128, DC omitted, 64 bins",
            "scope": "existing sampled hybrid, no Je-squared Full-FEA integration",
            "target_MS_field_count": 0, "new_FEA_solves": 0,
        },
    }
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.out / "ref_ms_spectra.json"
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"Wrote {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
