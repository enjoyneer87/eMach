import os
import sys
import json
from pathlib import Path
import numpy as np

# Add eMach root to path to enable importing from tools
current_dir = Path(__file__).parent.resolve()
emach_root = current_dir.parent.parent.resolve()
if str(emach_root) not in sys.path:
    sys.path.insert(0, str(emach_root))

from tools.jeet_acloss_rbf import (
    AcLossPoint,
    AcLossDataset,
    RbfModel3D,
    SeparableRbfModel,
    AcLossJsonReader,
    RbfModelBuilder,
    AcLossEvaluator,
    AcLossPlotter
)

# Configuration matching the notebook
MODEL_SCALE = 'SC'
json_summary_path = current_dir / "map_exports" / "e10" / MODEL_SCALE / f"JEET_ACLoss_{MODEL_SCALE}_Map_Summary.json"

print(f"Loading data from: {json_summary_path}")

# ==========================================
# 1. RUN ORIGINAL IMPLEMENTATION
# ==========================================
with open(json_summary_path, "r", encoding="utf-8") as f:
    _raw = json.load(f)
sweep_results = _raw["records"] if isinstance(_raw, dict) and "records" in _raw else _raw

hybrid_data = [p for p in sweep_results if p["proximity_model"] == 1]
ts_data     = [p for p in sweep_results if p["proximity_model"] == 3]

af_points_orig = []
for ts_pt in ts_data:
    spd  = ts_pt["speed"]
    curr = ts_pt["current"]
    ph   = ts_pt["phase"]

    matches = [p for p in hybrid_data
               if p["speed"] == spd
               and np.isclose(p["current"], curr, atol=1e-2)
               and np.isclose(p["phase"],   ph,   atol=1e-2)]
    if not matches:
        continue
    h_pt = matches[0]

    h_ac = h_pt["hybrid_total_kW"]
    f_ac = ts_pt["ts_ac_active_only_kW"]

    if h_ac < 1e-4:
        continue
    if f_ac < 1e-6:
        continue

    af = f_ac / h_ac

    IRMS_MIN = 50.0
    AF_MIN, AF_MAX = 0.3, 3.0
    if curr < IRMS_MIN:
        continue
    if not (AF_MIN <= af <= AF_MAX):
        continue

    amp    = curr * np.sqrt(2)
    ph_rad = (ph + 90.0) * np.pi / 180.0
    id_a   = amp * np.cos(ph_rad)
    iq_a   = amp * np.sin(ph_rad)

    af_points_orig.append({
        "speed_rpm":    spd,
        "speed_kRPM":   spd / 1000.0,
        "current_rms":  curr,
        "phase_deg":    ph,
        "id_A":         id_a,
        "iq_A":         iq_a,
        "hybrid_ac_kW": h_ac,
        "fea_ac_kW":    f_ac,
        "AF":           af,
    })

speeds_k_orig = np.array([p["speed_kRPM"]  for p in af_points_orig])
irms_arr_orig = np.array([p["current_rms"] for p in af_points_orig])
phase_arr_orig = np.array([p["phase_deg"]   for p in af_points_orig])
af_arr_orig    = np.array([p["AF"]          for p in af_points_orig])
id_arr_orig    = np.array([p["id_A"]        for p in af_points_orig])
iq_arr_orig    = np.array([p["iq_A"]        for p in af_points_orig])

LS_S_orig = float(speeds_k_orig.std())
LS_I_orig = float(irms_arr_orig.std())
LS_P_orig = float(phase_arr_orig.std())
LAM = 1e-6

# MODEL 1: 3D TPS RBF model fit
def _rbf_k_3d_orig(s, irms, ph, s_c, i_c, p_c):
    r2 = (s - s_c)**2 / LS_S_orig**2 + (irms - i_c)**2 / LS_I_orig**2 + (ph - p_c)**2 / LS_P_orig**2
    r = np.sqrt(r2)
    return r2 * np.log(r + 1e-12)

n_orig = len(af_arr_orig)
Phi_3d_orig = np.zeros((n_orig, n_orig))
for j in range(n_orig):
    Phi_3d_orig[:, j] = _rbf_k_3d_orig(speeds_k_orig, irms_arr_orig, phase_arr_orig,
                                       speeds_k_orig[j], irms_arr_orig[j], phase_arr_orig[j])

rbf_weights_3d_orig = np.linalg.solve(Phi_3d_orig + LAM * np.eye(n_orig), af_arr_orig)

# MODEL 2: 1D x 2D Separable RBF model fit
base_idx_orig = np.where(np.abs(speeds_k_orig - 2.0) < 0.1)[0]
speeds_k_base_orig = speeds_k_orig[base_idx_orig]
irms_arr_base_orig = irms_arr_orig[base_idx_orig]
phase_arr_base_orig = phase_arr_orig[base_idx_orig]
af_arr_base_orig = af_arr_orig[base_idx_orig]

def _rbf_2d_k_orig(irms, ph, i_c, p_c):
    r2 = (irms - i_c)**2 / LS_I_orig**2 + (ph - p_c)**2 / LS_P_orig**2
    r = np.sqrt(r2)
    return r2 * np.log(r + 1e-12)

n_base_orig = len(base_idx_orig)
Phi_g_orig = np.zeros((n_base_orig, n_base_orig))
for j in range(n_base_orig):
    Phi_g_orig[:, j] = _rbf_2d_k_orig(irms_arr_base_orig, phase_arr_base_orig,
                                      irms_arr_base_orig[j], phase_arr_base_orig[j])

w_g_orig = np.linalg.solve(Phi_g_orig + LAM * np.eye(n_base_orig), af_arr_base_orig)

def predict_g_orig(I, theta):
    Iv, thv = np.asarray(I, float).ravel()[:, None], np.asarray(theta, float).ravel()[:, None]
    r2 = (Iv - irms_arr_base_orig)**2 / LS_I_orig**2 + (thv - phase_arr_base_orig)**2 / LS_P_orig**2
    r = np.sqrt(r2)
    K = r2 * np.log(r + 1e-12)
    result = K @ w_g_orig
    return result.reshape(np.asarray(I).shape) if np.asarray(I).shape else float(result[0])

other_speeds_orig = [4.0, 8.0, 16.0]
target_currents_orig = [115.0, 230.0, 345.0, 460.0]
selected_other_idx_orig = []
for spd in other_speeds_orig:
    spd_idx = np.where(np.abs(speeds_k_orig - spd) < 0.1)[0]
    for i_val in target_currents_orig:
        _phase_mask = phase_arr_orig[spd_idx] < 85.0
        _valid_idx  = spd_idx[_phase_mask] if _phase_mask.any() else spd_idx
        diffs = (irms_arr_orig[_valid_idx] - i_val)**2
        best_idx = _valid_idx[np.argmin(diffs)]
        selected_other_idx_orig.append(best_idx)
selected_other_idx_orig = np.unique(selected_other_idx_orig)

f_vals_orig = []
for idx in selected_other_idx_orig:
    spd = speeds_k_orig[idx]
    I_val = irms_arr_orig[idx]
    th_val = phase_arr_orig[idx]
    af_actual = af_arr_orig[idx]
    g_val = predict_g_orig(I_val, th_val)
    f_val = af_actual / (g_val + 1e-12)
    if not (0.3 <= f_val <= 3.0):
        continue
    f_vals_orig.append((spd, f_val))

f_by_speed_orig = {2.0: [1.0]}
for spd, f_val in f_vals_orig:
    if spd not in f_by_speed_orig:
        f_by_speed_orig[spd] = []
    f_by_speed_orig[spd].append(f_val)

speed_coords_orig = []
f_coords_orig = []
for spd in sorted(f_by_speed_orig.keys()):
    speed_coords_orig.append(spd)
    f_coords_orig.append(np.mean(f_by_speed_orig[spd]))

p_coeffs_orig = np.polyfit(speed_coords_orig, f_coords_orig, 2)


# ==========================================
# 2. RUN MODULAR PACKAGE IMPLEMENTATION
# ==========================================
records_mod, err_code = AcLossJsonReader.read(str(json_summary_path), MODEL_SCALE)
assert err_code is None, f"Reader error: {err_code}"

dataset_mod = RbfModelBuilder.match_records_and_create_dataset(records_mod)
model_3d_mod = RbfModelBuilder.build_3d_rbf(dataset_mod)
model_sep_mod = RbfModelBuilder.build_separable_rbf(dataset_mod)


# ==========================================
# 3. VERIFY IDENTICAL RESULTS
# ==========================================
print("\n--- Verifying Equivalence ---")

# (A) Matched Points Length
assert len(af_points_orig) == len(dataset_mod), f"Point count mismatch: {len(af_points_orig)} vs {len(dataset_mod)}"
print(f"  [OK] Point count matches: {len(dataset_mod)}")

# (B) Values Comparison
for i, (orig, mod) in enumerate(zip(af_points_orig, dataset_mod.points)):
    for field in ["speed_rpm", "speed_kRPM", "current_rms", "phase_deg", "id_A", "iq_A", "hybrid_ac_kW", "fea_ac_kW", "AF"]:
        orig_val = orig[field]
        mod_val = getattr(mod, field)
        assert np.isclose(orig_val, mod_val, atol=1e-12), f"Point {i} field '{field}' mismatch: {orig_val} vs {mod_val}"
print("  [OK] Individual data point fields match exactly.")

# (C) Length Scales
assert np.isclose(LS_S_orig, dataset_mod.LS_S, atol=1e-12)
assert np.isclose(LS_I_orig, dataset_mod.LS_I, atol=1e-12)
assert np.isclose(LS_P_orig, dataset_mod.LS_P, atol=1e-12)
print(f"  [OK] Length scales match: s={dataset_mod.LS_S:.4f}, I={dataset_mod.LS_I:.4f}, P={dataset_mod.LS_P:.4f}")

# (D) 3D Model Weights
assert np.allclose(rbf_weights_3d_orig, model_3d_mod.weights, atol=1e-12), "3D RBF weights mismatch"
print("  [OK] 3D RBF weights match exactly.")

# (E) Separable RBF base weights
assert np.allclose(w_g_orig, model_sep_mod.w_g, atol=1e-12), "Separable base weights mismatch"
print("  [OK] Separable base RBF weights match exactly.")

# (F) Speed Polynomial Coefficients
assert np.allclose(p_coeffs_orig, model_sep_mod.p_coeffs, atol=1e-12), "Speed scaling poly coefficients mismatch"
print(f"  [OK] Speed scaling poly coefficients match: {model_sep_mod.p_coeffs}")

# (G) Predictions
for i, pt in enumerate(dataset_mod.points):
    pred_3d_orig = rbf_weights_3d_orig @ Phi_3d_orig[:, i] # using kernel values
    pred_3d_mod = model_3d_mod.predict(pt.speed_rpm, pt.current_rms, pt.phase_deg)
    assert np.isclose(pred_3d_orig, pred_3d_mod, atol=1e-12), f"Prediction 3D mismatch at {i}: {pred_3d_orig} vs {pred_3d_mod}"

    pred_sep_orig = np.polyval(p_coeffs_orig, pt.speed_kRPM) * predict_g_orig(pt.current_rms, pt.phase_deg)
    pred_sep_mod = model_sep_mod.predict(pt.speed_rpm, pt.current_rms, pt.phase_deg)
    assert np.isclose(pred_sep_orig, pred_sep_mod, atol=1e-12), f"Prediction Sep mismatch at {i}: {pred_sep_orig} vs {pred_sep_mod}"
print("  [OK] Predictions for both 3D TPS RBF and Separable RBF models match exactly across all points.")

# (H) Formula Verification
formula_3d_mod = model_3d_mod.mcad_formula
formula_sep_mod = model_sep_mod.mcad_formula
assert "Stator_Copper_Loss_AC" in formula_3d_mod and "Phase_Advance" in formula_3d_mod
assert "Stator_Current_Phase_RMS" in formula_sep_mod and "Speed/1000" in formula_sep_mod
print("  [OK] Generated Motor-CAD Lab formulas are formatted correctly.")

print("\n==========================================")
print("SUCCESS: ALL PIPELINE VERIFICATIONS PASSED!")
print("==========================================")
