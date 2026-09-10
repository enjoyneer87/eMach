"""Load an internal D1 response only after hash and full-field round-trip checks."""
import hashlib
import json
from pathlib import Path
import numpy as np
import d1_cont_rating as d1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_verified_response(reference):
    ref = json.loads(Path(reference).read_text(encoding="utf-8"))
    info = ref["_field_cache"]
    h = info["hset"]
    if (ref["_dry_run"] or ref["_aborted"] or info["schema"] != 1
            or info["oil_T_C"] != d1.OIL_T or ref["_htc_sets"] != d1.HTC_SETS
            or set(ref["I_cont_Arms"]) != {h}):
        raise ValueError("Unverified or incompatible thermal reference")
    check = ref["_superposition_check"]
    if not check["ok"] or len(check["points"]) != 2 or any(
            not np.isfinite(p["field_max_err_K"]) or p["field_max_err_K"] > 0.05
            for p in check["points"]):
        raise ValueError("Reference field verification failed")
    if sha(info["path"]) != info["sha256"]:
        raise ValueError("Nodal cache hash mismatch")
    with np.load(info["path"], allow_pickle=False) as saved:
        nnum = saved["nnum"]
        parts = {p: saved["part_" + p] for p in d1.PARTS}
        circuits = {p: int(saved["circuit_" + p]) for p in d1.CIRCUIT_NODES}
        gmap = {s: saved["G_" + s] for s in d1.SOURCES}
    size = len(nnum)
    if len(np.unique(nnum)) != size or any(
            v.shape != (size,) or not np.isfinite(v).all() for v in gmap.values()):
        raise ValueError("Invalid node/response arrays")
    for idx in list(parts.values()) + [np.array(list(circuits.values()))]:
        if not len(idx) or idx.min() < 0 or idx.max() >= size:
            raise ValueError("Invalid node indices")
    error = 0.0
    if not ref["runs"]:
        raise ValueError("Missing reference run table")
    for row in ref["runs"]:
        field = d1.reconstruct_field(gmap, row["P_W"])
        values, circuit, _ = d1.monitored_from_field(field, parts, circuits)
        error = max(error, *(abs(d1.plan_t_c(values)[k] - v) for k, v in row["T_C"].items()),
                    *(abs(circuit[k] - v) for k, v in row["circuit_T"].items()))
    if not np.isfinite(error) or error > 1e-8:
        raise ValueError("Cache does not reproduce reference aggregates")
    audit = {"reference_sha256": sha(reference), "cache_sha256": info["sha256"],
             "reference_run_count": len(ref["runs"]), "aggregate_roundtrip_K": error,
             "direct_field_checks": check["points"]}
    return ref, nnum, parts, circuits, gmap, audit
