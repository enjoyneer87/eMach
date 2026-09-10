"""Screen measured current/phase points against voltage, torque and frozen D1 limits.

Run on moa. Input MOT/CDB and the nodal cache stay internal; output is scalar only.
The separate thesis audit must verify Motor-CAD logs before publication.
"""
import argparse
import datetime
import json
import math
from pathlib import Path
import numpy as np
import d1_cont_rating as d1
from cached_thermal import load_verified_response, sha


def dc_bound(nnum, parts, gmap, limits):
    slot, end = d1.jm.p_dc(1.0)
    alpha = gmap["cu_slot"] * slot + gmap["cu_end"] * end
    out = {}
    for part in ("winding", "magnet"):
        idx = parts[part]
        j = int(idx[np.argmax(alpha[idx])])
        other = {s: float(gmap[s][j]) for s in ("fe_s", "fe_r", "pm", "ac_slot")}
        if alpha[j] <= 0 or any(v < 0 for v in other.values()):
            raise ValueError("Cannot certify DC-only necessary bound")
        out[part] = {"node_id": int(nnum[j]), "K_per_A2": float(alpha[j]),
                     "other_source_G_K_per_W": other,
                     "I_upper_Arms": float(np.sqrt((limits[part] - d1.OIL_T) / alpha[j]))}
    return {"limiting_nodes": out,
            "necessary_current_limit_Arms": min(v["I_upper_Arms"] for v in out.values())}


def run(args):
    if args.out.exists():
        raise ValueError("Output exists; preserve previous screening")
    rows = []
    for path in args.point_map:
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc["_dry_run"] or not doc["_gates_ok"] or not doc["points"]:
            raise ValueError("Incomplete/synthetic map: " + str(path))
        for p in doc["points"]:
            voltage = p["voltage_V"]
            outputs = p["operating_outputs"]
            required, available = voltage["RmsPhaseDriveVoltage"], voltage["PhaseVoltage"]
            torque = outputs["AvTorqueMsVw"]
            if not all(math.isfinite(v) for v in [required, available, torque]) or min(required, available) <= 0:
                raise ValueError("Invalid operating outputs")
            rows.append({"source": path.name, "source_sha256": sha(path),
                         "speed_rpm": p["speed"], "current_Arms": p["current"], "phase_edeg": p["phase"],
                         "required_phase_Vrms": required, "available_phase_Vrms": available,
                         "voltage_ratio": required / available, "voltage_pass": required <= available,
                         "average_em_torque_Nm": torque, "shaft_torque_Nm": outputs["ShaftTorque"],
                         "positive_torque": torque > args.min_torque and outputs["ShaftTorque"] > args.min_torque,
                         "zero_q_diagnostic": abs(p["phase"] - 90) < 1e-8,
                         "magnetic_loss_W": {k: p["P_W"][k] for k in ("fe_s", "fe_r", "pm")},
                         "thermal": {}})
    keys = [(p["speed_rpm"], p["current_Arms"], p["phase_edeg"]) for p in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate operating points")
    audit, bounds = {}, {}
    for reference in args.reference:
        ref, nnum, parts, circuits, gmap, verification = load_verified_response(reference)
        h = ref["_field_cache"]["hset"]
        if h in audit:
            raise ValueError("Duplicate h-set")
        audit[h] = verification
        bounds[h] = dc_bound(nnum, parts, gmap, ref["_limits_C"])
        # Parser defaults retain the previously calibrated undershoot gates.
        cfg = d1.build_parser().parse_args([])
        backend = d1.BackendBase(cfg, lambda *a: None)
        backend.nnum, backend.part_idx, backend.circ_pos = nnum, parts, circuits
        backend.mesh_info, backend.undershoot = ref["_mesh"], []
        records = d1.jm.load_map(ref["_map"])
        for row in rows:
            current, phase, speed = row["current_Arms"], row["phase_edeg"], row["speed_rpm"]
            slot, end = d1.jm.p_dc(current)
            base = dict(row["magnetic_loss_W"], cu_slot=slot, cu_end=end, ac_slot=0.0)
            result = {"dc_bound_exceeded": current > bounds[h]["necessary_current_limit_Arms"] + 1e-8}
            for case in ("DC", "AC"):
                losses = dict(base)
                if case == "AC":
                    # Only measured JEET phases are supported; never substitute phase36.
                    if phase not in (0, 18, 36, 54, 72, 90):
                        result[case] = {"status": "unavailable: no exact-phase JEET copper map"}
                        continue
                    ac, status = d1.jm.p_ac_continuous_ex(records, speed, current, phase)
                    if status != "ok":
                        raise ValueError("AC copper would be clamped/extrapolated")
                    losses["ac_slot"] = ac
                if not all(math.isfinite(v) and v >= 0 for v in losses.values()):
                    raise ValueError("Invalid source loss")
                field = d1.reconstruct_field(gmap, losses)
                backend.check_field(field, "fw-%s-%s-%s-%s" % (current, phase, h, case))
                values, circuit, positions = d1.monitored_from_field(field, parts, circuits)
                thermal_ok = all(values[p + "_max"] <= ref["_limits_C"][p] for p in ("winding", "magnet"))
                result[case] = {"status": "evaluated", "P_W": losses, "T_C": d1.plan_t_c(values),
                                "oil_T_C": circuit["OIL"], "thermal_pass": thermal_ok,
                                "hot_nodes": {p: int(nnum[positions[p]]) for p in ("winding", "magnet")},
                                "joint_pass": bool(thermal_ok and row["voltage_pass"] and
                                                   row["positive_torque"] and not row["zero_q_diagnostic"])}
            row["thermal"][h] = result
        audit[h]["undershoot_records"] = backend.undershoot
    output = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Measured points only; fixed thermal response and material temperatures. No optimized envelope or demagnetization validation.",
              "min_positive_torque_Nm": args.min_torque, "dc_bound_scope": "Necessary bound from DC copper alone; nonnegative omitted losses cannot relax the bound at the selected nodes.",
              "dc_bounds": bounds, "response_audit": audit,
              "JEET_map_sha256": sha(ref["_map"]),
              "points": sorted(rows, key=lambda p: (p["current_Arms"], p["phase_edeg"]))}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"points": len(rows), "out": str(args.out), "aggregate_roundtrip_K":
                      {h: v["aggregate_roundtrip_K"] for h, v in audit.items()}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, action="append", required=True)
    parser.add_argument("--point-map", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-torque", type=float, default=0.1)
    run(parser.parse_args())
