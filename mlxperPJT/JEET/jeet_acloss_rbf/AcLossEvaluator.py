import numpy as np
from itertools import product as iproduct
from typing import Tuple, List, Dict, Any, Optional
from .AcLossDataset import AcLossDataset
from .RbfModel3D import RbfModel3D
from .SeparableRbfModel import SeparableRbfModel
from .RbfModelBuilder import RbfModelBuilder

class AcLossEvaluator:
    @staticmethod
    def fit_method_a(dataset: AcLossDataset) -> Tuple[np.ndarray, float]:
        """
        Fits Method A: Speed-only 2nd-degree polynomial at maximum current.
        Returns:
            coeffs: Polynomial coefficients [a2, a1, a0]
            max_curr: The maximum current rms value used as reference.
        """
        max_curr = dataset.irms_arr.max()
        mask_maxcurr = np.isclose(dataset.irms_arr, max_curr, rtol=0.01)
        spd_mc = dataset.speeds_k[mask_maxcurr]
        af_mc = dataset.af_arr[mask_maxcurr]
        
        sort_idx = np.argsort(spd_mc)
        spd_mc = spd_mc[sort_idx]
        af_mc = af_mc[sort_idx]
        
        coeffs = np.polyfit(spd_mc, af_mc, deg=2)
        return coeffs, float(max_curr)

    @staticmethod
    def evaluate_errors(
        dataset: AcLossDataset,
        model_3d: RbfModel3D,
        model_sep: SeparableRbfModel
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes percentage errors for Hybrid (uncorrected), 3D RBF, and Separable RBF models.
        Returns:
            err_raw: Percentage errors for uncorrected hybrid model.
            err_3d: Percentage errors for corrected 3D RBF model.
            err_sep: Percentage errors for corrected Separable RBF model.
        """
        h_ac = dataset.h_ac_arr
        f_ac = dataset.f_ac_arr
        
        af_3d = model_3d.predict(dataset.speeds_k * 1000.0, dataset.irms_arr, dataset.phase_arr)
        af_sep = model_sep.predict(dataset.speeds_k * 1000.0, dataset.irms_arr, dataset.phase_arr)
        
        err_raw = (h_ac - f_ac) / (f_ac + 1e-12) * 100.0
        err_3d = (h_ac * af_3d - f_ac) / (f_ac + 1e-12) * 100.0
        err_sep = (h_ac * af_sep - f_ac) / (f_ac + 1e-12) * 100.0
        
        return err_raw, err_3d, err_sep

    @staticmethod
    def compute_loocv_3d(dataset: AcLossDataset, lam: float = 1e-6) -> float:
        """Computes Leave-One-Out Cross-Validation MAE [%] for the 3D TPS RBF model."""
        n = len(dataset)
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr
        h_ac_arr = dataset.h_ac_arr
        f_ac_arr = dataset.f_ac_arr
        LS_S, LS_I, LS_P = dataset.LS_S, dataset.LS_I, dataset.LS_P
        
        loocv_errors = []
        for i in range(n):
            # Exclude sample i
            s_tr = np.delete(speeds_k, i)
            i_tr = np.delete(irms_arr, i)
            p_tr = np.delete(phase_arr, i)
            y_tr = np.delete(af_arr, i)
            
            nc = n - 1
            Phi_tr = np.zeros((nc, nc))
            for j in range(nc):
                r2 = (s_tr - s_tr[j])**2 / LS_S**2 + \
                     (i_tr - i_tr[j])**2 / LS_I**2 + \
                     (p_tr - p_tr[j])**2 / LS_P**2
                Phi_tr[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
                
            w_tr = np.linalg.solve(Phi_tr + lam * np.eye(nc), y_tr)
            
            # Predict for sample i
            r2_val = (speeds_k[i] - s_tr)**2 / LS_S**2 + \
                     (irms_arr[i] - i_tr)**2 / LS_I**2 + \
                     (phase_arr[i] - p_tr)**2 / LS_P**2
            r_val = np.sqrt(r2_val)
            K_val = r2_val * np.log(r_val + 1e-12)
            y_pred = K_val @ w_tr
            
            corr_val = h_ac_arr[i] * y_pred
            loocv_errors.append(abs((corr_val - f_ac_arr[i]) / (f_ac_arr[i] + 1e-12) * 100.0))
            
        return float(np.mean(loocv_errors))

    @staticmethod
    def compute_loocv_separable(
        dataset: AcLossDataset,
        n_base: int,
        n_spd: int,
        lam: float = 1e-6
    ) -> float:
        """Computes Leave-One-Out Cross-Validation MAE [%] for the Separable RBF model."""
        n = len(dataset)
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr
        h_ac_arr = dataset.h_ac_arr
        f_ac_arr = dataset.f_ac_arr
        LS_I, LS_P = dataset.LS_I, dataset.LS_P
        
        base_idx = np.where(np.abs(speeds_k - 2.0) < 0.1)[0]
        other_speeds = [4.0, 8.0, 16.0]
        spd_grps = {s: np.where(np.abs(speeds_k - s) < 0.1)[0] for s in other_speeds}
        
        # We need a reproducible list of selected non-base indices for the main fold logic
        # For simplicity, we choose a fixed selection mapping based on the builder's logic
        # (with i omitted dynamically if matched)
        loocv_errors = []
        for i in range(n):
            # Base indices excluding i
            base_train_idx = [idx for idx in base_idx if idx != i]
            i_base = irms_arr[base_train_idx]
            p_base = phase_arr[base_train_idx]
            y_base = af_arr[base_train_idx]
            nb_tr = len(base_train_idx)
            
            Phi_g = np.zeros((nb_tr, nb_tr))
            for j in range(nb_tr):
                r2 = (i_base - i_base[j])**2 / LS_I**2 + \
                     (p_base - p_base[j])**2 / LS_P**2
                Phi_g[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
                
            try:
                w_g_tr = np.linalg.solve(Phi_g + lam * np.eye(nb_tr), y_base)
            except np.linalg.LinAlgError:
                continue
                
            def predict_g_tr(I, theta):
                Iv = np.asarray(I, float).ravel()[:, None]
                thv = np.asarray(theta, float).ravel()[:, None]
                r2 = (Iv - i_base)**2 / LS_I**2 + (thv - p_base)**2 / LS_P**2
                return (r2 * np.log(np.sqrt(r2) + 1e-12)) @ w_g_tr
                
            # Non-base speed calibration points excluding i
            f_by_speed_tr = {2.0: [1.0]}
            for spd in other_speeds:
                grp = spd_grps[spd]
                # Filter out validation sample i if present in group
                grp_tr = [idx for idx in grp if idx != i]
                # Default selection logic (mimic rebuild logic but omit sample i)
                rng = np.random.RandomState(42)
                n_sel = min(n_spd, len(grp_tr))
                if n_sel > 0:
                    for idx in rng.choice(grp_tr, n_sel, replace=False):
                        gv = float(predict_g_tr(irms_arr[idx], phase_arr[idx])[0])
                        f_by_speed_tr.setdefault(spd, []).append(af_arr[idx] / (gv + 1e-12))
                        
            sc = sorted(f_by_speed_tr.keys())
            if len(sc) < 2:
                continue
            fc = [np.mean(f_by_speed_tr[s]) for s in sc]
            pf_tr = np.poly1d(np.polyfit(sc, fc, min(2, len(sc) - 1)))
            
            # Predict for validation sample i
            gv_i = float(predict_g_tr(irms_arr[i], phase_arr[i])[0])
            fv_i = pf_tr(speeds_k[i])
            af_pred_i = fv_i * gv_i
            corr_val = h_ac_arr[i] * af_pred_i
            loocv_errors.append(abs((corr_val - f_ac_arr[i]) / (f_ac_arr[i] + 1e-12) * 100.0))
            
        return float(np.mean(loocv_errors)) if loocv_errors else np.nan

    @staticmethod
    def run_ablation_study_3d(
        dataset: AcLossDataset,
        n_center_list: List[int],
        n_seeds: int = 10,
        lam: float = 1e-6
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Runs ablation study for 3D TPS RBF model.
        Returns:
            res_tr_m, res_tr_s, res_te_m, res_te_s: Means and standard deviations of Train and Test MAEs.
        """
        n_total = len(dataset)
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr
        h_ac_arr = dataset.h_ac_arr
        f_ac_arr = dataset.f_ac_arr
        LS_S, LS_I, LS_P = dataset.LS_S, dataset.LS_I, dataset.LS_P
        
        unique_spds = sorted(set(speeds_k))
        spd_groups = {s: np.where(np.abs(speeds_k - s) < 0.01)[0] for s in unique_spds}
        
        def stratified_sampling(nc, seed):
            rng = np.random.RandomState(seed)
            n_spd = len(unique_spds)
            base_n = nc // n_spd
            rem = nc % n_spd
            res = []
            for k, s in enumerate(unique_spds):
                grp = spd_groups[s]
                n_d = min(base_n + (1 if k < rem else 0), len(grp))
                res.extend(rng.choice(grp, n_d, replace=False).tolist())
            return np.sort(res)
            
        res_tr_m, res_tr_s, res_te_m, res_te_s = [], [], [], []
        
        for nc in n_center_list:
            tr_list, te_list = [], []
            for seed in range(n_seeds):
                train_idx = stratified_sampling(nc, seed)
                n_train = len(train_idx)
                
                sk_tr = speeds_k[train_idx]
                ik_tr = irms_arr[train_idx]
                pk_tr = phase_arr[train_idx]
                yk_tr = af_arr[train_idx]
                
                Phi = np.zeros((n_train, n_train))
                for j in range(n_train):
                    r2 = (sk_tr - sk_tr[j])**2 / LS_S**2 + \
                         (ik_tr - ik_tr[j])**2 / LS_I**2 + \
                         (pk_tr - pk_tr[j])**2 / LS_P**2
                    Phi[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
                    
                try:
                    w = np.linalg.solve(Phi + lam * np.eye(n_train), yk_tr)
                except np.linalg.LinAlgError:
                    continue
                    
                # Evaluate on all points
                r2_all = (speeds_k[:, None] - sk_tr)**2 / LS_S**2 + \
                         (irms_arr[:, None] - ik_tr)**2 / LS_I**2 + \
                         (phase_arr[:, None] - pk_tr)**2 / LS_P**2
                af_pred = (r2_all * np.log(np.sqrt(r2_all) + 1e-12)) @ w
                err_pct = np.abs((h_ac_arr * af_pred - f_ac_arr) / (f_ac_arr + 1e-12) * 100.0)
                
                test_idx = np.setdiff1d(np.arange(n_total), train_idx)
                tr_list.append(err_pct[train_idx].mean())
                if len(test_idx) > 0:
                    te_list.append(err_pct[test_idx].mean())
                    
            res_tr_m.append(np.mean(tr_list) if tr_list else np.nan)
            res_tr_s.append(np.std(tr_list) if tr_list else np.nan)
            res_te_m.append(np.mean(te_list) if te_list else np.nan)
            res_te_s.append(np.std(te_list) if te_list else np.nan)
            
        return (np.array(res_tr_m), np.array(res_tr_s),
                np.array(res_te_m), np.array(res_te_s))

    @staticmethod
    def run_ablation_study_separable(
        dataset: AcLossDataset,
        n_base_list: List[int],
        n_speed_list: List[int],
        n_seeds: int = 10,
        lam: float = 1e-6
    ) -> np.ndarray:
        """
        Runs ablation study for Separable RBF model.
        Returns:
            res_sep: 2D array of shape (len(n_base_list), len(n_speed_list)) containing mean MAE values.
        """
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr
        h_ac_arr = dataset.h_ac_arr
        f_ac_arr = dataset.f_ac_arr
        LS_I, LS_P = dataset.LS_I, dataset.LS_P
        
        unique_spds = sorted(set(speeds_k))
        spd_groups = {s: np.where(np.abs(speeds_k - s) < 0.01)[0] for s in unique_spds}
        all_base_idx = spd_groups[2.0]
        other_spds = [s for s in unique_spds if s != 2.0]
        
        res_sep = np.full((len(n_base_list), len(n_speed_list)), np.nan)
        
        for bi, nb in enumerate(n_base_list):
            for si, ns in enumerate(n_speed_list):
                seed_maes = []
                for seed in range(n_seeds):
                    rng = np.random.RandomState(seed)
                    
                    # Subsample base points
                    nb_sel = min(nb, len(all_base_idx))
                    bsel = rng.choice(all_base_idx, nb_sel, replace=False)
                    ib = irms_arr[bsel]
                    pb = phase_arr[bsel]
                    yb = af_arr[bsel]
                    
                    Pg = np.zeros((nb_sel, nb_sel))
                    for j in range(nb_sel):
                        r2 = (ib - ib[j])**2 / LS_I**2 + (pb - pb[j])**2 / LS_P**2
                        Pg[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
                        
                    try:
                        wg = np.linalg.solve(Pg + lam * np.eye(nb_sel), yb)
                    except np.linalg.LinAlgError:
                        continue
                        
                    def _g_local(I, th):
                        Iv = np.asarray(I, float).ravel()[:, None]
                        thv = np.asarray(th, float).ravel()[:, None]
                        r2 = (Iv - ib)**2 / LS_I**2 + (thv - pb)**2 / LS_P**2
                        return (r2 * np.log(np.sqrt(r2) + 1e-12)) @ wg
                        
                    # Cal points per non-base speed
                    f_by = {2.0: [1.0]}
                    for s in other_spds:
                        grp = spd_groups[s]
                        n_d = min(ns, len(grp))
                        if n_d < 1:
                            continue
                        for idx in rng.choice(grp, n_d, replace=False):
                            gv = float(_g_local(irms_arr[idx], phase_arr[idx])[0])
                            f_by.setdefault(s, []).append(af_arr[idx] / (gv + 1e-12))
                            
                    sc = sorted(f_by.keys())
                    fc = [np.mean(f_by[s]) for s in sc]
                    pf = np.poly1d(np.polyfit(sc, fc, min(2, len(sc) - 1)))
                    
                    # Predict on entire dataset
                    g_all = _g_local(irms_arr, phase_arr).ravel()
                    af_pred = pf(speeds_k) * g_all
                    err_pct = np.abs((h_ac_arr * af_pred - f_ac_arr) / (f_ac_arr + 1e-12) * 100.0)
                    seed_maes.append(err_pct.mean())
                    
                if seed_maes:
                    res_sep[bi, si] = np.mean(seed_maes)
                    
        return res_sep

    @staticmethod
    def run_exhaustive_search(
        dataset: AcLossDataset,
        lam: float = 1e-6
    ) -> Tuple[np.ndarray, List[float], Dict[str, Any], Dict[str, Any]]:
        """
        Runs exhaustive calibration search (n_spd/spd = 1, n_base = all).
        Returns:
            mae_grid: 3D array containing MAE for each combination.
            other_speeds: List of non-base speeds in order.
            best_info: Dictionary containing parameters of the best combination.
            worst_info: Dictionary containing parameters of the worst combination.
        """
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr
        h_ac_arr = dataset.h_ac_arr
        f_ac_arr = dataset.f_ac_arr
        LS_I, LS_P = dataset.LS_I, dataset.LS_P
        
        base_idx = np.where(np.abs(speeds_k - 2.0) < 0.1)[0]
        other_speeds = sorted(list(set(speeds_k[speeds_k != 2.0])))
        spd_groups = {s: np.where(np.abs(speeds_k - s) < 0.01)[0] for s in other_speeds}
        
        # Fit Base RBF (using all base points)
        ib_ex = irms_arr[base_idx]
        pb_ex = phase_arr[base_idx]
        yb_ex = af_arr[base_idx]
        nb_ex = len(base_idx)
        
        Pg_ex = np.zeros((nb_ex, nb_ex))
        for j in range(nb_ex):
            r2 = (ib_ex - ib_ex[j])**2 / LS_I**2 + (pb_ex - pb_ex[j])**2 / LS_P**2
            Pg_ex[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
        wg_ex = np.linalg.solve(Pg_ex + lam * np.eye(nb_ex), yb_ex)
        
        def _g_ex(I, th):
            Iv = np.asarray(I, float).ravel()[:, None]
            thv = np.asarray(th, float).ravel()[:, None]
            r2 = (Iv - ib_ex)**2 / LS_I**2 + (thv - pb_ex)**2 / LS_P**2
            return (r2 * np.log(np.sqrt(r2) + 1e-12)) @ wg_ex
            
        g_all_ex = _g_ex(irms_arr, phase_arr).ravel()
        
        # Precompute candidate scaling factors
        f_cand_ex = {}
        for s in other_speeds:
            grp = spd_groups[s]
            f_cand_ex[s] = af_arr[grp] / (g_all_ex[grp] + 1e-12)
            
        sc_ex = [2.0] + other_speeds
        deg_ex = min(2, len(sc_ex) - 1)
        
        n_dims = [len(spd_groups[s]) for s in other_speeds]
        mae_grid = np.zeros(n_dims)
        
        # Grid loop using product
        ranges = [range(n) for n in n_dims]
        for indices in iproduct(*ranges):
            fc = [1.0] + [float(f_cand_ex[other_speeds[d]][indices[d]]) for d in range(len(other_speeds))]
            pf = np.poly1d(np.polyfit(sc_ex, fc, deg_ex))
            af_pred = pf(speeds_k) * g_all_ex
            mae = np.abs((h_ac_arr * af_pred - f_ac_arr) / (f_ac_arr + 1e-12) * 100.0).mean()
            mae_grid[indices] = mae
            
        # Extract best and worst
        min_idx = np.unravel_index(np.argmin(mae_grid), mae_grid.shape)
        max_idx = np.unravel_index(np.argmax(mae_grid), mae_grid.shape)
        
        def get_combo_info(indices):
            details = []
            for d, s in enumerate(other_speeds):
                gi = spd_groups[s][indices[d]]
                details.append({
                    "speed_rpm": float(s * 1000.0),
                    "irms": float(irms_arr[gi]),
                    "phase": float(phase_arr[gi]),
                    "f_scale": float(f_cand_ex[s][indices[d]])
                })
            return {"details": details, "mae": float(mae_grid[indices])}
            
        best_info = get_combo_info(min_idx)
        worst_info = get_combo_info(max_idx)
        
        return mae_grid, other_speeds, best_info, worst_info

    @staticmethod
    def rebuild_sep_model_with_subsampling(
        dataset: AcLossDataset,
        n_base: int,
        n_spd: int,
        seed: int = 42,
        lam: float = 1e-6
    ) -> SeparableRbfModel:
        """Helper to build Separable model with custom subsampling parameters (matches cell 21 rebuild_sep_rbf)."""
        return RbfModelBuilder.build_separable_rbf(
            dataset=dataset,
            n_base=n_base,
            n_spd=n_spd,
            seed=seed,
            lam=lam
        )
