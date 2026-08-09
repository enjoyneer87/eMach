import numpy as np
from typing import List, Dict, Tuple, Optional
from .AcLossPoint import AcLossPoint
from .AcLossDataset import AcLossDataset
from .RbfModel3D import RbfModel3D
from .SeparableRbfModel import SeparableRbfModel

class RbfModelBuilder:
    #: 마지막 빌드에서 '자체 진리값'을 쓴 데이터셋 인덱스.
    #: held-out 판정이 이걸 읽는다 (결정론 배치는 RNG 기록이 없다).
    last_train_idx = None

    @staticmethod
    def match_records_and_create_dataset(
        records: List[Dict],
        irms_min: float = 50.0,
        af_min: float = 0.3,
        af_max: float = 3.0,
        exclude_points: Optional[List[Tuple[float, float, float]]] = None
    ) -> AcLossDataset:
        """
        Processes raw simulation records, matches Hybrid and FullFEA points,
        runs validation filters, performs coordinate transformations, and creates
        an AcLossDataset.

        exclude_points: list of (speed_rpm, current_rms, phase_deg) tuples to
        drop as known-bad TS-FEA runs (e.g. non-converged transients detected
        by the AF neighbor-consistency check). Each exclusion is logged.
        """
        hybrid_data = [p for p in records if p.get("proximity_model") == 1]
        ts_data     = [p for p in records if p.get("proximity_model") == 3]

        excl = [tuple(map(float, e)) for e in (exclude_points or [])]

        af_points = []
        for ts_pt in ts_data:
            spd = ts_pt["speed"]
            curr = ts_pt["current"]
            ph = ts_pt["phase"]

            # Known-bad TS-FEA runs (data-quality exclusion)
            if any(abs(spd - es) < 1.0 and abs(curr - ec) < 1.0
                   and abs(ph - ep) < 1.0 for es, ec, ep in excl):
                print(f"  [EXCLUDE] known-bad TS-FEA point dropped: "
                      f"{spd:.0f} RPM, {curr:.1f} A, {ph:.1f} deg")
                continue

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
            f_ac = ts_pt.get("ts_ac_active_only_kW") or 0.0

            # Older exports (identified by the legacy key ts_dc_active_only_kW)
            # left ts_ac_active_only_kW unpopulated at 0.0 while carrying the
            # same quantity in fea_total_ac_kW. Where both are present the two
            # agree to <2e-14 relative, so fall back rather than drop the point.
            if f_ac <= 1e-9:
                legacy = ts_pt.get("fea_total_ac_kW")
                if legacy is not None and legacy > 1e-6:
                    f_ac = legacy

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
    def _fit_speed_scaling(
        samples_by_speed: Dict[float, List[Tuple[float, float]]],
        base_speed: float,
        exponent: bool,
        verbose: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Fits the speed polynomials from per-speed (AF, g) sample pairs.

        scalar mode  : f_s = mean(AF / g)                        (p = 1)
        exponent mode: log AF = log f_s + p_s * log g  (per-speed linear
                       regression), so the spread of the base-speed shape
                       becomes speed-adjustable. Falls back to the scalar
                       fit when a speed has < 2 usable pairs or no spread
                       in log g (regression would be degenerate).

        Returns (p_coeffs, q_coeffs): quadratic polynomials of f(s) and
        p(s) over speed [kRPM], anchored at f(base)=1, p(base)=1.
        q_coeffs is None in scalar mode.
        """
        speed_coords, f_coords, p_exps = [base_speed], [1.0], [1.0]
        for spd in sorted(samples_by_speed.keys()):
            pairs = [(a, g) for a, g in samples_by_speed[spd]
                     if a > 0.0 and g > 0.0]
            if not pairs:
                continue
            ratios = [a / g for a, g in pairs]
            la = np.log([a for a, _ in pairs])
            lg = np.log([g for _, g in pairs])
            if exponent and len(pairs) >= 2 and float(np.ptp(lg)) > 1e-3:
                p_s, logf_s = np.polyfit(lg, la, 1)
                f_s = float(np.exp(logf_s))
            else:
                p_s, f_s = 1.0, float(np.mean(ratios))
            if verbose:
                extra = f'  p={p_s:.3f}' if exponent else ''
                print(f'  f({int(spd * 1000):5d} RPM): n={len(pairs)}  '
                      f'mean={np.mean(ratios):.4f}  '
                      f'range=[{min(ratios):.4f}, {max(ratios):.4f}]{extra}')
            speed_coords.append(spd)
            f_coords.append(f_s)
            p_exps.append(float(p_s))

        order = np.argsort(speed_coords)
        s_arr = np.asarray(speed_coords)[order]
        p_coeffs = np.polyfit(s_arr, np.asarray(f_coords)[order], 2)
        q_coeffs = (np.polyfit(s_arr, np.asarray(p_exps)[order], 2)
                    if exponent else None)
        return p_coeffs, q_coeffs

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
    def _maximin_indices(cand, x, y, k) -> np.ndarray:
        """Deterministic farthest-point (maximin) subset of ``cand``.

        Seeds at the candidate closest to the centroid and then repeatedly
        adds the candidate farthest from everything already chosen, so the
        result covers the plane without depending on a random seed.
        """
        cand = np.asarray(cand)
        if k >= len(cand):
            return cand
        X = np.column_stack([np.asarray(x, float), np.asarray(y, float)])
        picked = [int(np.argmin(((X - X.mean(0)) ** 2).sum(1)))]
        d = np.sqrt(((X - X[picked[0]]) ** 2).sum(1))
        for _ in range(int(k) - 1):
            nxt = int(np.argmax(d))
            picked.append(nxt)
            d = np.minimum(d, np.sqrt(((X - X[nxt]) ** 2).sum(1)))
        return cand[picked]

    @staticmethod
    def plan_sampling_indices(
        dataset: AcLossDataset,
        n_base: int,
        n_spd: int,
        base_speed: float = 16.0,
        placement: str = "random",
        seed: int = 42,
        lam: float = 1e-6
    ) -> dict:
        """Chooses which operating points to run TS-FEA at.

        ``placement='random'`` reproduces the seeded draw used for the
        convergence study.  ``placement='structured'`` is a deterministic,
        transferable rule with two stages:

          1. base speed  -- maximin coverage of the (I_rms, beta) plane,
             which is what the shape kernel kappa has to interpolate;
          2. other speeds -- *kappa-span* selection.  Because kappa is
             already identified at stage 1, it can be evaluated on every
             candidate before any further TS-FEA is spent; picking points
             at even quantiles of log kappa maximises the lever arm of the
             per-speed log-space regression log AF = log f + p log kappa.
             Short lever arms are exactly what destabilises p when only a
             few calibration points are available.

        Returns ``{'base', 'by_speed', 'all', 'placement', 'log_kappa_span'}``
        so the same point set can be handed to any calibration form.
        """
        speeds_k, I, P = dataset.speeds_k, dataset.irms_arr, dataset.phase_arr
        LS_I, LS_P = dataset.LS_I, dataset.LS_P
        base_idx = np.where(np.abs(speeds_k - base_speed) < 0.1)[0]
        others = [s for s in sorted(set(np.round(speeds_k, 3)))
                  if abs(s - base_speed) >= 0.1]
        rng = np.random.RandomState(seed)

        if placement == "structured":
            bsel = RbfModelBuilder._maximin_indices(
                base_idx, I[base_idx] / LS_I, P[base_idx] / LS_P, n_base)
        elif placement == "random":
            bsel = rng.choice(base_idx, min(n_base, len(base_idx)),
                              replace=False)
        else:
            raise ValueError(f"unknown placement: {placement!r}")

        # kappa on the chosen base points (needed for the structured rule)
        kappa = None
        if placement == "structured":
            ib, pb = I[bsel], P[bsel]
            nb = len(bsel)
            Phi = np.zeros((nb, nb))
            for j in range(nb):
                r2 = ((ib - ib[j]) ** 2 / LS_I ** 2
                      + (pb - pb[j]) ** 2 / LS_P ** 2)
                Phi[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
            w = np.linalg.solve(Phi + lam * np.eye(nb), dataset.af_arr[bsel])

            def kappa(iv, pv):                              # noqa: F811
                r2 = ((np.asarray(iv, float).ravel()[:, None] - ib) ** 2
                      / LS_I ** 2
                      + (np.asarray(pv, float).ravel()[:, None] - pb) ** 2
                      / LS_P ** 2)
                return (r2 * np.log(np.sqrt(r2) + 1e-12)) @ w

        by_speed, spans = {}, {}
        for spd in others:
            grp = np.where(np.abs(speeds_k - spd) < 0.1)[0]
            k = min(int(n_spd), len(grp))
            if placement == "random":
                sel = rng.choice(grp, k, replace=False)
            else:
                g = np.asarray(kappa(I[grp], P[grp]), float).ravel()
                ok = grp[g > 0]
                if len(ok) < k:                    # kernel degenerate here
                    sel = RbfModelBuilder._maximin_indices(
                        grp, I[grp] / LS_I, P[grp] / LS_P, k)
                else:
                    lg = np.log(np.asarray(kappa(I[ok], P[ok]),
                                           float).ravel())
                    order = ok[np.argsort(lg)]
                    q = (np.linspace(0.0, 1.0, k) * (len(order) - 1)
                         ).round().astype(int)
                    sel = order[np.unique(q)]
            by_speed[float(spd)] = np.asarray(sel)
            if kappa is not None and len(sel):
                lg = np.log(np.clip(np.asarray(kappa(I[sel], P[sel]),
                                               float).ravel(), 1e-12, None))
                spans[float(spd)] = float(np.ptp(lg))

        all_idx = np.concatenate([np.asarray(bsel)]
                                 + [v for v in by_speed.values() if len(v)])
        return {"base": np.asarray(bsel), "by_speed": by_speed,
                "all": np.unique(all_idx), "placement": placement,
                "log_kappa_span": spans}

    @staticmethod
    def build_separable_rbf(
        dataset: AcLossDataset,
        n_base: Optional[int] = None,
        n_spd: Optional[int] = None,
        seed: int = 42,
        lam: float = 1e-6,
        base_speed: float = 2.0,
        exponent: bool = False,
        index_plan: Optional[dict] = None
    ) -> SeparableRbfModel:
        """
        Fits a 1D x 2D Separable RBF model.
        If n_base or n_spd is specified, it uses random subsampling with the given seed (CUSTOM behavior).
        Otherwise, it uses the default parameters and target currents selection (DEFAULT behavior).
        base_speed [kRPM] selects where the 2D kernel g(I, beta) is learned
        (f(base_speed) = 1 anchor). Learning at the maximum speed puts the
        separability residual at low speed, where absolute losses are small.
        exponent=True fits AF = f(s) * g(I, beta)**p(s) — the per-speed
        (f, p) pair comes from a log-space linear regression, which needs
        >= 2 (robustly 3) calibration points per non-base speed.
        """
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr

        LS_I, LS_P = dataset.LS_I, dataset.LS_P

        # 1. Base speed selection
        base_idx = np.where(np.abs(speeds_k - base_speed) < 0.1)[0]
        
        # Subsampling for n_base if specified
        if index_plan is not None:
            selected_base_idx = np.asarray(index_plan["base"])
        elif n_base is not None:
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

        samples_by_speed: Dict[float, List[Tuple[float, float]]] = {}

        _tr = [int(v) for v in np.asarray(selected_base_idx).ravel()]

        def admit(spd, idx):
            _tr.append(int(idx))
            I_val = irms_arr[idx]
            th_val = phase_arr[idx]
            af_actual = af_arr[idx]
            g_val = float(predict_g_local(I_val, th_val))
            f_val = af_actual / (g_val + 1e-12)
            if not (0.3 <= f_val <= 3.0):
                return
            samples_by_speed.setdefault(spd, []).append((float(af_actual),
                                                         g_val))

        if index_plan is not None:
            # EXPLICIT mode: caller supplied the sampling plan
            for spd, idxs in index_plan["by_speed"].items():
                for idx in np.asarray(idxs):
                    admit(spd, idx)
        elif n_base is None and n_spd is None:
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
                admit(speeds_k[idx], idx)
        else:
            # CUSTOM mode: select randomly from the speed groups
            rng = np.random.RandomState(seed)
            n_s = n_spd if n_spd is not None else 4  # default to 4 points if not specified
            for spd in other_speeds:
                spd_idx = np.where(np.abs(speeds_k - spd) < 0.1)[0]
                n_sel = min(n_s, len(spd_idx))
                for idx in rng.choice(spd_idx, n_sel, replace=False):
                    admit(spd, idx)

        RbfModelBuilder.last_train_idx = np.unique(
            np.asarray(_tr, dtype=int))
        p_coeffs, q_coeffs = RbfModelBuilder._fit_speed_scaling(
            samples_by_speed, base_speed, exponent)

        return SeparableRbfModel(
            w_g=w_g,
            base_centers_i=irms_arr_base,
            base_centers_p=phase_arr_base,
            ls_i=LS_I,
            ls_p=LS_P,
            p_coeffs=p_coeffs,
            q_coeffs=q_coeffs
        )

    @staticmethod
    def build_separable_rbf_transfer(
        dataset: AcLossDataset,
        donor_model: SeparableRbfModel,
        k_r: float,
        n_base: int,
        n_spd: int,
        seed: int = 42,
        lam: float = 1e-6,
        base_speed: float = 16.0,
        max_donor_speed: float = 16.0,
        n_probe_transfer: int = 4,
        exponent: bool = False,
        placement: str = "random"
    ) -> SeparableRbfModel:
        """
        Builds a Separable RBF for a scaled variant using SCL-M similarity
        transfer: AF_scaled(w, I, beta) = AF_ref(k_r^2 * w, I / k_r, beta).

        The 2D kernel and the calibration points in the *untransferable*
        high band (mapped speed k_r^2 * w > max_donor_speed) use the scaled
        model's own TS-FEA samples; low-band f-values are evaluated from the
        donor (reference) model instead, so no low-speed TS-FEA of the
        scaled variant is required.

        exponent=True fits AF = f(s) * g(I, beta)**p(s) per speed via
        log-space regression (needs n_spd >= 3 own points in the high band
        for a stable fit; transferred probes are free, use >= 6).
        """
        speeds_k = dataset.speeds_k
        irms_arr = dataset.irms_arr
        phase_arr = dataset.phase_arr
        af_arr = dataset.af_arr
        LS_I, LS_P = dataset.LS_I, dataset.LS_P

        rng = np.random.RandomState(seed)

        _trt = []
        # 2D kernel at the scaled model's own base speed
        base_idx = np.where(np.abs(speeds_k - base_speed) < 0.1)[0]
        if placement == "structured":
            bsel = RbfModelBuilder._maximin_indices(
                base_idx, irms_arr[base_idx] / LS_I,
                phase_arr[base_idx] / LS_P, n_base)
        else:
            bsel = rng.choice(base_idx, min(n_base, len(base_idx)),
                              replace=False)
        ib, pb, yb = irms_arr[bsel], phase_arr[bsel], af_arr[bsel]
        nb = len(bsel)
        Phi_g = np.zeros((nb, nb))
        for j in range(nb):
            r2 = (ib - ib[j])**2 / LS_I**2 + (pb - pb[j])**2 / LS_P**2
            Phi_g[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
        w_g = np.linalg.solve(Phi_g + lam * np.eye(nb), yb)

        def g_local(I, th):
            Iv = np.asarray(I, float).ravel()[:, None]
            thv = np.asarray(th, float).ravel()[:, None]
            r2 = (Iv - ib)**2 / LS_I**2 + (thv - pb)**2 / LS_P**2
            return (r2 * np.log(np.sqrt(r2) + 1e-12)) @ w_g

        unique_speeds = sorted(set(np.round(speeds_k, 3)))
        other_speeds = [s for s in unique_speeds
                        if abs(s - base_speed) >= 0.1]

        samples_by_speed: Dict[float, List[Tuple[float, float]]] = {}
        for spd in other_speeds:
            grp = np.where(np.abs(speeds_k - spd) < 0.1)[0]
            transferable = (spd * k_r**2) <= max_donor_speed + 0.1
            # transferred probes cost no TS-FEA -> use a richer probe set
            n_pick = n_probe_transfer if transferable else n_spd
            if placement == "structured":
                g = np.asarray(g_local(irms_arr[grp], phase_arr[grp]),
                               float).ravel()
                ok = grp[g > 0]
                k = min(n_pick, len(grp))
                if len(ok) < k:
                    pick = RbfModelBuilder._maximin_indices(
                        grp, irms_arr[grp] / LS_I, phase_arr[grp] / LS_P, k)
                else:
                    lg = np.log(np.asarray(
                        g_local(irms_arr[ok], phase_arr[ok]), float).ravel())
                    order = ok[np.argsort(lg)]
                    q = (np.linspace(0.0, 1.0, k)
                         * (len(order) - 1)).round().astype(int)
                    pick = order[np.unique(q)]
            else:
                pick = rng.choice(grp, min(n_pick, len(grp)), replace=False)
            for idx in pick:
                if not transferable:
                    _trt.append(int(idx))
                I_val, th_val = irms_arr[idx], phase_arr[idx]
                if transferable:
                    # AF from the donor model via similarity mapping
                    af_val = float(donor_model.predict(
                        spd * k_r**2 * 1000.0, I_val / k_r, th_val))
                else:
                    af_val = af_arr[idx]      # own TS-FEA sample
                g_val = float(g_local(I_val, th_val)[0])
                f_val = af_val / (g_val + 1e-12)
                if 0.3 <= f_val <= 3.0:
                    samples_by_speed.setdefault(spd, []).append(
                        (float(af_val), g_val))

        RbfModelBuilder.last_train_idx = np.unique(
            np.concatenate([np.asarray(bsel, dtype=int).ravel(),
                            np.asarray(_trt, dtype=int)]))
        p_coeffs, q_coeffs = RbfModelBuilder._fit_speed_scaling(
            samples_by_speed, base_speed, exponent, verbose=False)

        return SeparableRbfModel(
            w_g=w_g,
            base_centers_i=ib,
            base_centers_p=pb,
            ls_i=LS_I,
            ls_p=LS_P,
            p_coeffs=p_coeffs,
            q_coeffs=q_coeffs
        )
