import json
import numpy as np
from pathlib import Path
from ..model.RbfModelParams import RbfModelParams

class RbfJsonReader:
    @staticmethod
    def read(filepath: str, use_separable: bool = True) -> RbfModelParams:
        """
        Reads RBF parameters from JSON and returns RbfModelParams.
        
        Args:
            filepath: Path to the JSON configuration file containing trained model parameters.
            use_separable: If True, loads Separable 1D x 2D RBF model. Otherwise, loads 3D TPS RBF model.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        ls = data.get("length_scales", {})
        ls_s = ls.get("LS_S_kRPM", 1.0)
        ls_i = ls.get("LS_I_A", 1.0)
        ls_p = ls.get("LS_P_deg", 1.0)
        
        # Determine mapping based on the configuration of original saved keys
        # We find them in "separable_model" and "3D_model"
        if use_separable and "separable_model" in data:
            model_info = data["separable_model"]
            weights = np.array(model_info["base_weights"], dtype=float)
            p_coeffs = np.array(model_info["speed_poly_coeffs"], dtype=float)
            # exponent-separable extension AF = f(s) * g**p(s); optional
            q_raw = model_info.get("spread_poly_coeffs")
            q_coeffs = (np.array(q_raw, dtype=float)
                        if q_raw is not None else None)

            # New-style exports store the base-kernel centers explicitly
            # (anchor-speed agnostic); prefer them when present.
            if "base_centers_i" in model_info:
                return RbfModelParams(
                    model_type='Separable_1D_2D_RBF',
                    weights=weights,
                    centers_i=np.array(model_info["base_centers_i"], float),
                    centers_p=np.array(model_info["base_centers_p"], float),
                    ls_i=model_info.get("ls_i", ls_i),
                    ls_p=model_info.get("ls_p", ls_p),
                    p_coeffs=p_coeffs,
                    q_coeffs=q_coeffs
                )

            # The centers of the base model (typically at 2kRPM)
            # We can extract them from the list of af_points that have speed_kRPM == 2.0
            af_pts = data.get("af_points", [])
            base_pts = [p for p in af_pts if np.isclose(p["speed_kRPM"], 2.0, atol=0.1)]
            
            # Subsample base centers to match base_weights size if subsampled,
            # or default to original sorted order (which corresponds to base_pts centers)
            # Wait, how does rebuild_sep_rbf or subsampling work?
            # They subsample with seed=42 using choice. Let's make sure we match the indices.
            # Wait, in the export JSON:
            # "separable_model": {
            #     "model": "Separable_1D_2D_RBF",
            #     "n_base_centers": 30,
            #     "base_weights": model_sep_eval.w_g.tolist(),
            #     "speed_poly_coeffs": model_sep_eval.p_coeffs.tolist(),
            #     ...
            # }
            # Wait, how do we get the centers of these 30 points?
            # Ah! If they are subsampled, we need to know WHICH points were selected!
            # Let's check how the JSON is constructed. Is there a list of selected indices?
            # No, the export has "af_points".
            # Wait, let's write the loader to handle this robustly. If the user doesn't have centers stored,
            # we can reconstruct them using the same seed=42 selection from the base_idx in the dataset.
            # But to make it format-agnostic and robust, we can reconstruct the exact choice using the seed
            # or look for "base_centers_i" in the JSON.
            # Let's check if the JSON saves base centers.
            # Wait, in the notebook Cell 25:
            # "separable_model": {
            #     "model": "Separable_1D_2D_RBF",
            #     "n_base_centers": int(_n_base),
            #     "base_weights": model_sep_eval.w_g.tolist(),
            #     "speed_poly_coeffs": model_sep_eval.p_coeffs.tolist(),
            #     ...
            # }
            # It doesn't save the selected center coordinates directly in "separable_model".
            # But the notebook rebuilds them using:
            # base_idx = np.where(np.abs(dataset.speeds_k - 2.0) < 0.1)[0]
            # RNG with seed 42 selects choice(base_idx, _n_base, replace=False).
            # So if we read the af_points, reconstruct the dataset, we can get the EXACT same centers!
            # Let's write this exact logic. It's incredibly elegant and matches the notebook perfectly.
            
            # Reconstruct centers
            speeds_k = np.array([p["speed_kRPM"] for p in af_pts], dtype=float)
            irms_arr = np.array([p["current_rms"] for p in af_pts], dtype=float)
            phase_arr = np.array([p["phase_deg"] for p in af_pts], dtype=float)
            
            base_idx = np.where(np.abs(speeds_k - 2.0) < 0.1)[0]
            n_base = model_info["n_base_centers"]
            
            # Selection matches _rebuild_sep_rbf:
            rng = np.random.RandomState(42) # default seed in notebook
            nb_ = min(n_base, len(base_idx))
            bsel = rng.choice(base_idx, nb_, replace=False)
            
            centers_i = irms_arr[bsel]
            centers_p = phase_arr[bsel]
            
            return RbfModelParams(
                model_type='Separable_1D_2D_RBF',
                weights=weights,
                centers_i=centers_i,
                centers_p=centers_p,
                ls_i=ls_i,
                ls_p=ls_p,
                p_coeffs=p_coeffs
            )
            
        else:
            # 3D TPS RBF
            model_info = data.get("3D_model", data)
            weights = np.array(model_info["weights"], dtype=float)
            
            # For 3D TPS RBF, all af_points are centers.
            af_pts = data.get("af_points", [])
            centers_s = np.array([p["speed_kRPM"] for p in af_pts], dtype=float)
            centers_i = np.array([p["current_rms"] for p in af_pts], dtype=float)
            centers_p = np.array([p["phase_deg"] for p in af_pts], dtype=float)
            
            return RbfModelParams(
                model_type='3D_TPS_RBF',
                weights=weights,
                centers_i=centers_i,
                centers_p=centers_p,
                ls_i=ls_i,
                ls_p=ls_p,
                centers_s=centers_s,
                ls_s=ls_s
            )
