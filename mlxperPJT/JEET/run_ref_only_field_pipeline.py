"""M1: frozen Ref MS fields -> public hybrid -> sparse AF -> target loss.

The public line-sampled capped kernel is an explicit evaluation variant,
not an exact implementation of a proprietary hybrid. All main target
denominators consume Ref spectra only. Target own-field data is optional
comparison evidence; it is never used to construct the Ref-only case.
"""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
from jeet_acloss_rbf.AcLossDataset import AcLossDataset
from jeet_acloss_rbf.pipeline import AcLossPipeline, DEFAULT_CONFIG
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder as Builder
from acloss_ref_methods.volpe_hybrid_acloss import calc_skin_loss

SIGMA_80 = (1 / 1.724e-8) / (1 + 3.93e-3 * 60)
MU0 = 4e-7 * np.pi
CURRENT_TOL_REF_A = 0.2


def checksum(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def evaluate_hybrid(row, current_A, speed_rpm, kr, ka=1.0):
    """Existing public /24, six-subdivision radial term, common cap, skin.

    B is invariant under this k_w=1 similarity. Line-sampling weights are
    normalized areas, and radial dilation preserves the sampled spectra.
    Re-evaluate the frequency kernel at scaled dimensions; do not apply
    kr**4 blindly through the transition cap.
    """
    w, h, length = 3.711e-3 * kr, 1.686e-3 * kr, 0.150 * ka
    bt = np.asarray(row["b2t_msq_sum"], dtype=float)
    br = np.asarray(row["b2r_msq_sum"], dtype=float)
    fundamental = speed_rpm * 4 / 60
    fm = np.arange(1, len(bt) + 1) * fundamental
    ft = 1 / (np.pi * MU0 * SIGMA_80 * h ** 2)
    omega2_capped = (2 * np.pi * fm) ** 2 * np.minimum(1, ft / fm)
    prox_W = float(8 * SIGMA_80 * length / 24 * np.sum(
        omega2_capped * (w * h ** 3 * bt + h * w ** 3 * br / 36)))
    skin_W = float(calc_skin_loss(w, h, fundamental, length, current_A,
                                 sigma=SIGMA_80)["P_excess_W"] * 48 * 6)
    return {"proximity_W": prox_W, "skin_excess_W": skin_W,
            "hybrid_kW": (prox_W + skin_W) / 1000}


def ref_row_for(rows, current_A, phase_deg, kr):
    found = [row for row in rows
             if abs(row["current_A"] - current_A / kr) <= CURRENT_TOL_REF_A
             and abs(row["phase_deg"] - phase_deg) < 1e-6]
    if len(found) != 1:
        return None, f"Ref field match count {len(found)} at {current_A}/{kr}, {phase_deg}"
    return found[0], None


def transferred_dataset(base, rows, kr):
    points, mapping = [], []
    for i, point in enumerate(base.points):
        row, error = ref_row_for(rows, point.current_rms, point.phase_deg, kr)
        if error:
            return None, None, error
        h = evaluate_hybrid(row, point.current_rms, point.speed_rpm, kr)
        points.append(replace(point, hybrid_ac_kW=h["hybrid_kW"],
                              AF=point.fea_ac_kW / h["hybrid_kW"]))
        mapping.append({"index": i, "target_speed_rpm": point.speed_rpm,
                        "target_current_A": point.current_rms,
                        "phase_deg": point.phase_deg,
                        "source_current_A": row["current_A"],
                        "current_delta_ref_A": row["current_A"] - point.current_rms / kr,
                        "raw_sha256": row["raw_sha256"], **h})
    return AcLossDataset(points), mapping, None


def cached_own_dataset(base, rows):
    points, missing = [], []
    for i, point in enumerate(base.points):
        hits = [row for row in rows
                if row["speed_rpm"] == point.speed_rpm
                and abs(row["current_A"] - point.current_rms) < 0.2
                and abs(row["phase_deg"] - point.phase_deg) < 1e-6]
        if len(hits) != 1:
            missing.append(i)
            continue
        row = hits[0]
        h = (row["line_msq_P24c6_translim"] + row["skin_excess_W"]) / 1000
        points.append(replace(point, hybrid_ac_kW=h, AF=point.fea_ac_kW / h))
    if missing:
        return None, {"status": "unavailable", "missing_target_indices": missing,
                      "reason": "own-field cache does not cover the current 96-point dataset"}
    return AcLossDataset(points), {"status": "complete", "n": len(points)}


def fit_donor(dataset):
    plan = DEFAULT_CONFIG["plan"]["Ref"]
    indices = Builder.plan_sampling_indices(
        dataset, n_base=24, n_spd=4, base_speed=16,
        placement="structured", seed=plan["seed"])
    model = Builder.build_separable_rbf(dataset, base_speed=16,
                                       exponent=True, index_plan=indices)
    return model, Builder.last_train_idx.copy()


def fit_target(dataset, donor, donor_dataset, scale):
    plan = DEFAULT_CONFIG["plan"][scale]
    model = Builder.build_separable_rbf_transfer(
        dataset, donor, DEFAULT_CONFIG["k_r"][scale],
        n_base=24, n_spd=3, seed=plan["seed"], base_speed=16,
        n_probe_transfer=6, exponent=True, placement="structured",
        donor_dataset=donor_dataset, rule="predicted_loss")
    return model, Builder.last_train_idx.copy()


def predict(model, dataset):
    return dataset.h_ac_arr * model.predict(dataset.speeds_k * 1000,
                                            dataset.irms_arr, dataset.phase_arr)


def mask_truth(dataset, admitted):
    indices = set(int(i) for i in admitted)
    return AcLossDataset([point if i in indices else replace(
        point, fea_ac_kW=float("nan"), AF=float("nan"))
        for i, point in enumerate(dataset.points)])


def metric(truth, predicted, mask):
    if not np.any(mask):
        return {"n": 0, "wmae_pct": None, "loss_weight": 0.0}
    error = np.abs(predicted[mask] - truth[mask])
    relative = error / truth[mask] * 100
    return {"n": int(np.sum(mask)),
            "wmae_pct": float(error.sum() / truth[mask].sum() * 100),
            "mean_abs_W": float(error.mean() * 1000),
            "p95_relative_pct": float(np.percentile(relative, 95)),
            "max_relative_pct": float(relative.max()),
            "loss_weight": float(truth[mask].sum() / truth.sum())}


def record_result(dataset, model, train):
    pred = np.asarray(predict(model, dataset))
    if not np.all(np.isfinite(pred)) or np.any(pred <= 0):
        return None, "nonpositive/nonfinite calibrated prediction"
    all_points = np.ones(len(dataset), dtype=bool)
    heldout = ~np.isin(np.arange(len(dataset)), train)
    record = {
        "n": len(dataset), "own_training_count": len(train),
        "own_train_indices": train.tolist(),
        "own_train_coordinates": [[float(dataset.speeds_k[i] * 1000),
                                    float(dataset.irms_arr[i]),
                                    float(dataset.phase_arr[i])] for i in train],
        "uncorrected": metric(dataset.f_ac_arr, dataset.h_ac_arr, all_points),
        "full": metric(dataset.f_ac_arr, pred, all_points),
        "heldout_own_only": metric(dataset.f_ac_arr, pred, heldout),
        "per_speed": {str(s): {
            "full": metric(dataset.f_ac_arr, pred, dataset.speeds_k == s),
            "heldout": metric(dataset.f_ac_arr, pred, (dataset.speeds_k == s) & heldout)}
            for s in np.unique(dataset.speeds_k)},
        "prediction_kW": pred.tolist(), "hybrid_kW": dataset.h_ac_arr.tolist(),
        "truth_kW": dataset.f_ac_arr.tolist(),
    }
    return record, None


def score_case(donor_dataset, targets, check_budget=True):
    with contextlib.redirect_stdout(io.StringIO()):
        donor, donor_idx = fit_donor(donor_dataset)
        ref_result, err = record_result(donor_dataset, donor, donor_idx)
        if err:
            return None, err
        result = {"Ref": ref_result}
        if len(donor_idx) != 36:
            return None, f"Ref training count is {len(donor_idx)}, expected 36"
        masked_donor = mask_truth(donor_dataset, donor_idx)
        rebuilt_donor, rebuilt_donor_idx = fit_donor(masked_donor)
        if not np.array_equal(donor_idx, rebuilt_donor_idx):
            return None, "masked Ref truth changed sampling"
        for scale, dataset in targets.items():
            model, idx = fit_target(dataset, donor, donor_dataset, scale)
            record, err = record_result(dataset, model, idx)
            if err:
                return None, err
            if len(idx) != 27:
                return None, f"{scale} training count is {len(idx)}, expected 27"
            if check_budget:
                masked_target = mask_truth(dataset, idx)
                rebuilt, idx2 = fit_target(masked_target, rebuilt_donor, masked_donor, scale)
                difference = float(np.max(np.abs(predict(rebuilt, dataset) - predict(model, dataset))))
                record["withheld_truth_mask_check"] = {
                    "donor_truth_masked": len(donor_dataset) - len(donor_idx),
                    "target_truth_masked": len(dataset) - len(idx),
                    "same_training_indices": bool(np.array_equal(idx, idx2)),
                    "max_prediction_delta_kW": difference,
                }
                if difference > 1e-10 or not np.array_equal(idx, idx2):
                    return None, f"non-training truth affected {scale} prediction"
            result[scale] = record
    return result, None


def reference_speed_check(path):
    rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    differences = []
    for row in rows:
        ref = next(r for r in rows if r["speed_rpm"] == 16000
                   and r["phase_deg"] == row["phase_deg"])
        differences.append(max(float(np.max(np.abs(np.asarray(row[key])
                                                  - np.asarray(ref[key]))))
                               for key in ("b2t_msq_sum", "b2r_msq_sum")))
    return {"source": str(path), "sha256": checksum(path), "n": len(rows),
            "max_abs_spectrum_delta_T2": max(differences),
            "scope": "existing rated-current Ref spectra, all phases/speeds"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spectra", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    source = json.loads(args.spectra.read_text(encoding="utf-8"))
    if source.get("schema") != "ref-ms-line-spectra-v1" or len(source["rows"]) != 30:
        print("Incomplete or unsupported Ref spectrum inputs")
        return 2
    with contextlib.redirect_stdout(io.StringIO()):
        pipeline = AcLossPipeline({"data_root": str(args.data)})
        deposited = {scale: pipeline.load_dataset(scale) for scale in ("Ref", "HalfSC", "SC")}
    transferred, maps = {}, {}
    for scale, base in deposited.items():
        ds, mapping, err = transferred_dataset(base, source["rows"], DEFAULT_CONFIG["k_r"][scale])
        if err or len(ds) != 96:
            print(err or "Incomplete target coverage")
            return 2
        transferred[scale], maps[scale] = ds, mapping
    own, own_status = {}, {}
    for scale in ("HalfSC", "SC"):
        path = args.data / scale / f"line_sampled_hybrid_{scale}_80C.json"
        if path.exists():
            ds, status = cached_own_dataset(deposited[scale], json.loads(path.read_text())["rows"])
            status.update(path=str(path), sha256=checksum(path))
            own_status[scale] = status
            if ds is not None:
                own[scale] = ds
    cases = {
        "deposited_hybrid": (deposited["Ref"], {s: deposited[s] for s in ("HalfSC", "SC")}),
        "ref_only_public_hybrid": (transferred["Ref"], {s: transferred[s] for s in ("HalfSC", "SC")}),
        "ref_only_target_deposited_donor": (deposited["Ref"], {s: transferred[s] for s in ("HalfSC", "SC")}),
    }
    if own:
        cases["own_field_public_target_deposited_donor"] = (deposited["Ref"], own)
        cases["own_field_public_target_public_donor"] = (transferred["Ref"], own)
    results = {}
    for name, (donor, targets) in cases.items():
        result, err = score_case(donor, targets)
        if err:
            print(f"{name}: {err}")
            return 2
        results[name] = result
        for scale, r in result.items():
            print(f"{name:43s} {scale:7s} n={r['n']} train={r['own_training_count']} "
                  f"full={r['full']['wmae_pct']:.6f}% heldout={r['heldout_own_only']['wmae_pct']:.6f}%")
    comparison = {}
    for scale, ds in own.items():
        ratio = transferred[scale].h_ac_arr / ds.h_ac_arr
        comparison[scale] = {"n": len(ds), "mean_ratio": float(ratio.mean()),
                             "min_ratio": float(ratio.min()), "max_ratio": float(ratio.max())}
    output = {
        "status": "existing-field pipeline recomputed; not independent new FEA",
        "definition": "line-sampled P24c6 common transition cap + skin excess, 80 C, k_a=k_w=1",
        "sigma_S_per_m": SIGMA_80, "source_spectrum": str(args.spectra),
        "source_spectrum_sha256": checksum(args.spectra),
        "input_summary_sha256": {s: checksum(args.data / DEFAULT_CONFIG["json"][s]) for s in deposited},
        "source_code_sha256": {"runner": checksum(Path(__file__)),
                               "builder": checksum(HERE.parent.parent / "tools/jeet_acloss_rbf/RbfModelBuilder.py")},
        "conditions": {"Ref_MS_field_count": 30, "target_MS_fields_in_ref_only_case": 0,
                       "new_FEA_solves": 0, "current_matching_tolerance_ref_A": CURRENT_TOL_REF_A,
                       "Ref_Full_FEA_training_count": 36, "target_Full_FEA_training_count_each": 27},
        "source_mapping": maps, "cases": results, "own_field_comparison_coverage": own_status,
        "transferred_to_own_public_hybrid_ratio": comparison,
        "Ref_speed_independence_cached_check": reference_speed_check(
            args.data / "Ref_rated/line_sampled_hybrid_Ref_rated_80C.json"),
        "limitations": [
            "Public sampled hybrid differs from the deposited commercial hybrid; no parameter tuning performed.",
            "Full-map metrics include calibration points; own-held-out is not an independent external test.",
            "Sampling policy and budgets fixed; selected low-speed coordinates can change with the denominator.",
            "Current matching permits only recorded rounding offsets; missing points are fatal, never dropped.",
            "MS spectra use the inherited line sampling, FFT and six-digit spectrum serialization.",
            "Full-FEA reference values and their original time-average convention are unchanged.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
