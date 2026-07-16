import numpy as np
from typing import List, Dict, Tuple, Optional
from .AcLossPoint import AcLossPoint
from .AcLossDataset import AcLossDataset
from .RbfModel3D import RbfModel3D
from .SeparableRbfModel import SeparableRbfModel

class RbfModelBuilder:
    @staticmethod
    def match_records_and_create_dataset(
        records: List[Dict],
        irms_min: float = 50.0,
        af_min: float = 0.3,
        af_max: float = 3.0
    ) -> AcLossDataset:
        """
        Processes raw simulation records, matches Hybrid and FullFEA points,
        runs validation filters, performs coordinate transformations, and creates
        an AcLossDataset.
        """
        hybrid_data = [p for p in records if p.get("proximity_model") == 1]
        ts_data     = [p for p in records if p.get("proximity_model") == 3]
        
        af_points = []
        for ts_pt in ts_data:
            spd = ts_pt["speed"]
            curr = ts_pt["current"]
            ph = ts_pt["phase"]
            
            # Find matching hybrid record
            matches = [
                h for h in hybrid_data
                if h["speed"] == spd
                and np.isclose(h["current"], curr, atol=1e-2)
                and np.isclose(h["phase"], ph, atol=1e-2)
            ]
            if not matches:
                continue
                
            h_pt = matches[0]
            h_ac = h_pt["hybrid_total_kW"]
            f_ac = ts_pt["ts_ac_active_only_kW"]
            
            if h_ac < 1e-4 or f_ac < 1e-6:
                continue
                
            af = f_ac / h_ac
            
            # Filter
            if curr < irms_min:
                continue
            if not (af_min <= af <= af_max):
                continue
                
            # Coordinate transformation
            amp = curr * np.sqrt(2)
            ph_rad = (ph + 90.0) * np.pi / 180.0
            id_a = amp * np.cos(ph_rad)
            iq_a = amp * np.sin(ph_rad)
            
            af_points.append(AcLossPoint(
                speed_rpm=float(spd),
                speed_kRPM=float(spd / 1000.0),
                current_rms=float(curr),
                phase_deg=float(ph),
                id_A=float(id_a),
                iq_A=float(iq_a),
                hybrid_ac_kW=float(h_ac),
                fea_ac_kW=float(f_ac),
                AF=float(af)
            ))
            
        # Diagnostics
        unique_speeds = sorted(set(p.speed_rpm for p in af_points))
        print("\n[누락 포인트 진단]")
        for spd_val in sorted(set(p["speed"] for p in hybrid_data)):
            _h = {(round(p['current'], 1), round(p['phase'], 1)) for p in hybrid_data if p['speed'] == spd_val}
            _f = {(round(p['current'], 1), round(p['phase'], 1)) for p in ts_data if p['speed'] == spd_val}
            _m = {(round(p.current_rms, 1), round(p.phase_deg, 1)) for p in af_points if p.speed_rpm == spd_val}
            
            missing_fea = _h - _f
            filtered_af = _f - _m
            if missing_fea:
                print(f"  {int(spd_val)}RPM  FEA 미완료 {len(missing_fea)}건: {sorted(missing_fea)}")
            if filtered_af:
                print(f"  {int(spd_val)}RPM  AF 필터 제거 {len(filtered_af)}건: {sorted(filtered_af)}")
            if not missing_fea and not filtered_af:
                print(f"  {int(spd_val)}RPM  누락 없음 ({len(_m)}개 전부 유효)")
                
        print(f"AF 매칭 계산 완료: {len(af_points)}개 운전점")
        if af_points:
            afs = [p.AF for p in af_points]
            print(f"AF 범위: min={min(afs):.4f},  max={max(afs):.4f},  mean={np.mean(afs):.4f}")
            
        return AcLossDataset(af_points)

    @staticmethod
    def build_3d_rbf(dataset: AcLossDataset, lam: float = 1e-6) -> RbfModel3D:
        """Fits a 3D TPS RBF model on the dataset."""
        n = len(dataset)
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr
        
        LS_S, LS_I, LS_P = dataset.LS_S, dataset.LS_I, dataset.LS_P
        
        Phi_3d = np.zeros((n, n))
        for j in range(n):
            r2 = (speeds_k - speeds_k[j])**2 / LS_S**2 + \
                 (irms_arr - irms_arr[j])**2 / LS_I**2 + \
                 (phase_arr - phase_arr[j])**2 / LS_P**2
            r = np.sqrt(r2)
            Phi_3d[:, j] = r2 * np.log(r + 1e-12)
            
        rbf_weights_3d = np.linalg.solve(Phi_3d + lam * np.eye(n), af_arr)
        
        return RbfModel3D(
            weights=rbf_weights_3d,
            centers_s=speeds_k,
            centers_i=irms_arr,
            centers_p=phase_arr,
            ls_s=LS_S,
            ls_i=LS_I,
            ls_p=LS_P
        )

    @staticmethod
    def build_separable_rbf(
        dataset: AcLossDataset,
        n_base: Optional[int] = None,
        n_spd: Optional[int] = None,
        seed: int = 42,
        lam: float = 1e-6,
        base_speed: float = 2.0
    ) -> SeparableRbfModel:
        """
        Fits a 1D x 2D Separable RBF model.
        If n_base or n_spd is specified, it uses random subsampling with the given seed (CUSTOM behavior).
        Otherwise, it uses the default parameters and target currents selection (DEFAULT behavior).
        base_speed [kRPM] selects where the 2D kernel g(I, beta) is learned
        (f(base_speed) = 1 anchor). Learning at the maximum speed puts the
        separability residual at low speed, where absolute losses are small.
        """
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr

        LS_I, LS_P = dataset.LS_I, dataset.LS_P

        # 1. Base speed selection
        base_idx = np.where(np.abs(speeds_k - base_speed) < 0.1)[0]
        
        # Subsampling for n_base if specified
        if n_base is not None:
            rng = np.random.RandomState(seed)
            nb_sel = min(n_base, len(base_idx))
            selected_base_idx = rng.choice(base_idx, nb_sel, replace=False)
        else:
            selected_base_idx = base_idx
            
        irms_arr_base = irms_arr[selected_base_idx]
        phase_arr_base = phase_arr[selected_base_idx]
        af_arr_base = af_arr[selected_base_idx]
        
        # Fit 2D TPS RBF g(I, theta) at base speed
        nb = len(selected_base_idx)
        Phi_g = np.zeros((nb, nb))
        for j in range(nb):
            r2 = (irms_arr_base - irms_arr_base[j])**2 / LS_I**2 + \
                 (phase_arr_base - phase_arr_base[j])**2 / LS_P**2
            r = np.sqrt(r2)
            Phi_g[:, j] = r2 * np.log(r + 1e-12)
            
        w_g = np.linalg.solve(Phi_g + lam * np.eye(nb), af_arr_base)
        
        def predict_g_local(I, theta):
            I_arr = np.asarray(I, float)
            theta_arr = np.asarray(theta, float)
            I_arr, theta_arr = np.broadcast_arrays(I_arr, theta_arr)
            orig = I_arr.shape
            Iv = I_arr.ravel()[:, None]
            thv = theta_arr.ravel()[:, None]
            
            r2 = (Iv - irms_arr_base)**2 / LS_I**2 + \
                 (thv - phase_arr_base)**2 / LS_P**2
            r = np.sqrt(r2)
            K = r2 * np.log(r + 1e-12)
            result = K @ w_g
            return result.reshape(orig) if orig else float(result[0])
            
        # 2. Fit 1D speed polynomial f(speed)
        unique_speeds = sorted(set(np.round(speeds_k, 3)))
        other_speeds = [s for s in unique_speeds
                        if abs(s - base_speed) >= 0.1]

        f_by_speed = {base_speed: [1.0]}
        
        if n_base is None and n_spd is None:
            # DEFAULT mode: select using specific target currents
            target_currents = [115.0, 230.0, 345.0, 460.0]
            selected_other_idx = []
            for spd in other_speeds:
                spd_idx = np.where(np.abs(speeds_k - spd) < 0.1)[0]
                for i_val in target_currents:
                    _phase_mask = phase_arr[spd_idx] < 85.0
                    _valid_idx = spd_idx[_phase_mask] if _phase_mask.any() else spd_idx
                    diffs = (irms_arr[_valid_idx] - i_val)**2
                    best_idx = _valid_idx[np.argmin(diffs)]
                    selected_other_idx.append(best_idx)
            selected_other_idx = np.unique(selected_other_idx)
            
            for idx in selected_other_idx:
                spd = speeds_k[idx]
                I_val = irms_arr[idx]
                th_val = phase_arr[idx]
                af_actual = af_arr[idx]
                g_val = predict_g_local(I_val, th_val)
                f_val = af_actual / (g_val + 1e-12)
                if not (0.3 <= f_val <= 3.0):
                    continue
                f_by_speed.setdefault(spd, []).append(f_val)
        else:
            # CUSTOM mode: select randomly from the speed groups
            rng = np.random.RandomState(seed)
            n_s = n_spd if n_spd is not None else 4  # default to 4 points if not specified
            for spd in other_speeds:
                spd_idx = np.where(np.abs(speeds_k - spd) < 0.1)[0]
                n_sel = min(n_s, len(spd_idx))
                for idx in rng.choice(spd_idx, n_sel, replace=False):
                    I_val = irms_arr[idx]
                    th_val = phase_arr[idx]
                    af_actual = af_arr[idx]
                    g_val = predict_g_local(I_val, th_val)
                    f_val = af_actual / (g_val + 1e-12)
                    if not (0.3 <= f_val <= 3.0):
                        continue
                    f_by_speed.setdefault(spd, []).append(f_val)
                    
        # Diagnose speed scaling values
        for _s, _flist in sorted(f_by_speed.items()):
            print(f'  f({int(_s*1000):5d} RPM): n={len(_flist)}  '
                  f'mean={np.mean(_flist):.4f}  '
                  f'range=[{min(_flist):.4f}, {max(_flist):.4f}]')
                  
        speed_coords = []
        f_coords = []
        for spd in sorted(f_by_speed.keys()):
            speed_coords.append(spd)
            f_coords.append(np.mean(f_by_speed[spd]))
            
        p_coeffs = np.polyfit(speed_coords, f_coords, 2)
        
        return SeparableRbfModel(
            w_g=w_g,
            base_centers_i=irms_arr_base,
            base_centers_p=phase_arr_base,
            ls_i=LS_I,
            ls_p=LS_P,
            p_coeffs=p_coeffs
        )
