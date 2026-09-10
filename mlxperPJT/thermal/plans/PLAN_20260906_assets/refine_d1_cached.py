"""Re-evaluate loss maps using an internally saved, verified D1 nodal response.

No MAPDL process is launched. The thermal model is frozen to the reference JSON.
The NPZ never leaves the internal execution machine. Scalar results may be shared.
"""
import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import d1_cont_rating as d1
from motorcad_loss_map import MagneticLossMap


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evaluate(args):
    start = time.time()
    if args.out.exists():
        raise ValueError("Refusing to overwrite an existing result")
    ref = json.loads(args.reference.read_text(encoding="utf-8"))
    info = ref["_field_cache"]
    h = info["hset"]
    if ref["_dry_run"] or ref["_aborted"] or info["schema"] != 1 or info["oil_T_C"] != d1.OIL_T:
        raise ValueError("Unverified or incompatible reference")
    if ref["_htc_sets"] != d1.HTC_SETS or set(ref["I_cont_Arms"]) != {h}:
        raise ValueError("Thermal model settings differ")
    check = ref["_superposition_check"]
    if not check["ok"] or len(check["points"]) != 2 or any(
        p["field_max_err_K"] > 0.05 for p in check["points"]):
        raise ValueError("Reference field verification failed")
    if sha(info["path"]) != info["sha256"]:
        raise ValueError("Nodal cache hash mismatch")
    argv = ["--repo", ref["_repo"], "--map", ref["_map"], "--htc-set", h,
            "--phase", str(ref["_phase_deg"]), "--out", str(args.out.parent),
            "--run-dir", str(args.out.parent), "--limit-winding", str(ref["_limits_C"]["winding"]),
            "--limit-magnet", str(ref["_limits_C"]["magnet"]), "--no-git-check"]
    for f in args.loss_map:
        argv += ["--loss-map", str(f)]
    cfg = d1.finish_args(d1.build_parser().parse_args(argv))
    log = d1.Log(str(args.out.with_suffix(".log")))
    backend = d1.BackendBase(cfg, log)
    backend.undershoot = []
    with np.load(info["path"], allow_pickle=False) as saved:
        backend.nnum = saved["nnum"]
        backend.part_idx = {p: saved["part_" + p] for p in d1.PARTS}
        backend.circ_pos = {p: int(saved["circuit_" + p]) for p in d1.CIRCUIT_NODES}
        gmap = {s: saved["G_" + s] for s in d1.SOURCES}
    size = len(backend.nnum)
    if len(np.unique(backend.nnum)) != size or any(v.shape != (size,) or not np.isfinite(v).all()
                                                 for v in gmap.values()):
        raise ValueError("Invalid node/response arrays")
    for idx in list(backend.part_idx.values()) + [np.array(list(backend.circ_pos.values()))]:
        if not len(idx) or idx.min() < 0 or idx.max() >= size:
            raise ValueError("Invalid node indices")
    backend.mesh_info = ref["_mesh"]
    records = d1.jm.load_map(cfg.map)

    # Reproduce the original full-field aggregates and roots before changing losses.
    original_cfg = argparse.Namespace(**vars(cfg))
    original_cfg._magnetic_map = MagneticLossMap([f["path"] for f in ref["_magnetic_loss_map"]["files"]])
    aggregate_error = 0.0
    for row in ref["runs"]:
        field = d1.reconstruct_field(gmap, row["P_W"])
        values, circuit, _ = d1.monitored_from_field(field, backend.part_idx, backend.circ_pos)
        aggregate_error = max(aggregate_error, *(abs(d1.plan_t_c(values)[k] - v) for k, v in row["T_C"].items()),
                              *(abs(circuit[k] - v) for k, v in row["circuit_T"].items()))
    root_error = 0.0
    for case in d1.CASES:
        for speed in cfg.speeds:
            old = d1.icont_super(gmap, backend, records, speed, case, original_cfg, log, "cache-roundtrip")
            value = ref["I_cont_Arms"][h][case][str(speed)]
            if old["I_cont_Arms"] is None or value is None:
                if old["I_cont_Arms"] != value:
                    raise ValueError("Original root status changed")
            else:
                root_error = max(root_error, abs(old["I_cont_Arms"] - value))
    if aggregate_error > 1e-8 or root_error > 1e-8:
        raise ValueError("Cache does not reproduce reference fields/roots")

    out = copy.deepcopy(ref)
    for row in out["runs"]:
        previous_losses = row["P_W"]
        row["P_W"] = d1.losses_for_run(records, row["speed"], row["current"], cfg.phase, row["case"], cfg)
        field = d1.reconstruct_field(gmap, row["P_W"])
        backend.check_field(field, "refined-grid-%s-%s-%s" % (row["speed"], row["current"], row["case"]))
        values, circuit, positions = d1.monitored_from_field(field, backend.part_idx, backend.circ_pos)
        row.update(T_C=d1.plan_t_c(values), circuit_T=circuit,
                   P_total_W=sum(row["P_W"].values()), _source="cached full-field reconstruction",
                   _argmax_nodes={p: int(backend.nnum[positions[p]]) for p in d1.PARTS})
        if row["P_W"] != previous_losses:
            row.pop("_direct_check_C", None)
            row.pop("_direct_check_max_err_K", None)
    keys = (("I_cont_Arms", "I_cont_Arms"), ("I_cont_winding_Arms", "I_cont_winding_Arms"),
            ("I_cont_magnet_Arms", "I_cont_magnet_Arms"), ("I_cont_limited_by", "limited_by"),
            ("I_cont_status", "status"))
    for case in d1.CASES:
        for speed in cfg.speeds:
            results = {}
            for method in ("linear", "linear_i2"):
                method_cfg = argparse.Namespace(**vars(cfg)); method_cfg.iron_interpolation = method
                res = d1.icont_super(gmap, backend, records, speed, case, method_cfg, log, "refined-root")
                value = res["I_cont_Arms"]
                if value is not None:
                    if not res.get("_hot_node_converged"):
                        raise ValueError("Refined hot-node iteration failed")
                    field = d1.reconstruct_field(gmap, res["P_W_at_I_cont"])
                    backend.check_field(field, "refined-root-%s-%s-%s" % (speed, case, method))
                    values, _, _ = d1.monitored_from_field(field, backend.part_idx, backend.circ_pos)
                    res["_full_field_at_root_C"] = {"winding": values["winding_max"], "magnet": values["magnet_max"]}
                    if values["winding_max"] > cfg.limit_winding + 0.001 or values["magnet_max"] > cfg.limit_magnet + 0.001:
                        raise ValueError("Reconstructed root exceeds thermal limit")
                    # Each magnetic component is monotone WITHIN one interpolation
                    # segment, even if the complete map is not monotone. DC and
                    # the monotone JEET AC interpolation have endpoint bounds too.
                    # This bounds every node over the whole interval below the root,
                    # including negative coefficients, without assuming monotone T.
                    knots = sorted({cfg._magnetic_map.bounds(speed)[0], value} |
                                   {i for i in cfg._magnetic_map.rows[float(speed)] if i < value})
                    upper_max = {"winding": -float("inf"), "magnet": -float("inf")}
                    for left, right in zip(knots, knots[1:]):
                        pa = d1.losses_for_run(records, speed, left, cfg.phase, case, method_cfg)
                        pb = d1.losses_for_run(records, speed, right, cfg.phase, case, method_cfg)
                        upper = np.full(size, d1.OIL_T)
                        for source in d1.SOURCES:
                            upper += np.maximum(gmap[source] * pa[source], gmap[source] * pb[source])
                        for part in upper_max:
                            upper_max[part] = max(upper_max[part], float(upper[backend.part_idx[part]].max()))
                    if upper_max["winding"] > cfg.limit_winding + 0.001 or upper_max["magnet"] > cfg.limit_magnet + 0.001:
                        raise ValueError("Interval bound cannot certify thermal feasibility below root")
                    res["_safe_below_root"] = {"method": "component endpoint bounds on each magnetic interpolation interval",
                        "interval_count": len(knots) - 1, "upper_bound_C": upper_max}
                results[method] = res
            primary, alternate = results["linear"], results["linear_i2"]
            value, other = primary["I_cont_Arms"], alternate["I_cont_Arms"]
            primary["_interpolation_sensitivity"] = {"alternate_method": "linear_i2",
                "alternate_I_cont_Arms": other, "alternate_status": alternate["status"],
                "alternate_hot_node_converged": alternate.get("_hot_node_converged"),
                "alternate_full_field_at_root_C": alternate.get("_full_field_at_root_C"),
                "delta_Arms": None if value is None or other is None else other - value}
            for target, source in keys:
                out[target][h][case][str(speed)] = primary.get(source)
            out["I_cont_detail"][h][case][str(speed)] = primary
    out["influence_coeffs"] = d1.build_influence_json({h: gmap}, backend, records, cfg)
    out["_magnetic_loss_map"] = cfg._magnetic_map.metadata("linear")
    out["_generated"] = datetime.datetime.now().isoformat()
    out["_mode"] = "cached-superposition"
    out["_script"] = "refine_d1_cached.py"
    out["_reference_verification"] = {"path": str(args.reference), "sha256": sha(args.reference),
        "max_aggregate_roundtrip_K": aggregate_error, "max_root_roundtrip_A": root_error}
    out["_superposition_check"]["performed_this_pass"] = False
    out["_superposition_check"]["note"] = "Inherited direct verification of the SAME full nodal response; no new FEA in this pass."
    out["_timing"] = {"n_solves": 0, "total_s": time.time() - start, "response_build": ref["_timing"]}
    out["_rth"] = None
    out["_undershoot"] = ref.get("_undershoot", []) + backend.undershoot
    out["_notes"].insert(0, "Updated loss map, unchanged verified thermal response. Internal NPZ is hash-checked and reproduces every reference aggregate and current root.")
    args.out.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    log("WROTE", args.out, out["I_cont_Arms"])
    log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--loss-map", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    evaluate(parser.parse_args())
