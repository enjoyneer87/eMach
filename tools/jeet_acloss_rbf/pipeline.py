"""High-level pipeline for the JEET AC-loss calibration workflow.

Wraps the full session workflow — dataset loading (with data-quality
exclusions), base@16k Separable RBF fitting, SCL-M similarity transfer,
metrics, and journal-style figures — behind one object so it can be driven
from Python scripts, notebooks, or MATLAB (via the ``py.`` interface).

MATLAB-friendliness rules used throughout:
  * public methods accept/return plain floats, lists, and dicts of 1-D
    numpy arrays (convert with ``double(...)`` / ``np2mat`` on the MATLAB
    side);
  * no method requires keyword-only arguments.

Typical use::

    from jeet_acloss_rbf import AcLossPipeline
    pl = AcLossPipeline()                 # default e10 config
    d  = pl.dataset_struct('SC')          # dict of arrays for inspection
    pl.build_model('SC')                  # transfer model (donor = Ref)
    af = pl.predict_af('SC', 16000.0, 690.0, 36.0)
    m  = pl.metrics('SC')                 # {'mae': ..., 'wmae': ...}
    pl.make_validation_figure('SC', 'out/validation_SC.png')
"""
import os
from typing import Dict, List, Optional, Tuple

import numpy as np

from .AcLossJsonReader import AcLossJsonReader
from .RbfModelBuilder import RbfModelBuilder
from .AcLossEvaluator import AcLossEvaluator
from .SeparableRbfModel import SeparableRbfModel

_E10 = r'D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10'

#: Adopted configuration of the paper (rev3): base kernel at 16 kRPM,
#: exponent separable model AF = f(w) * g(I, beta)**p(w), Ref = donor with
#: own sampling at all speeds, scaled variants use the SCL-M similarity
#: transfer and own samples (3 pts for the (f, p) regression) only in the
#: high band.
DEFAULT_CONFIG = {
    'data_root': _E10,
    'base_speed': 16.0,          # kRPM, 2D-kernel anchor (f = 1, p = 1)
    'exponent': True,            # AF = f * g**p (False -> scalar f * g)
    'json': {
        'Ref':    r'Ref\JEET_ACLoss_Ref_Map_Summary.json',
        'HalfSC': r'HalfSC\JEET_ACLoss_HalfSC_Map_Summary.json',
        'SC':     r'SC\JEET_ACLoss_SC_Map_Summary.json',
    },
    # known-bad TS-FEA runs (AF neighbor-consistency scan). The single SC
    # outlier (16 kRPM, 690 A, 90 deg; AF 0.47) was re-run in Motor-CAD on
    # 2026-07-17 and replaced with the converged result (AF 1.068), and the
    # missing (460 A, 90 deg) point was infilled (AF 1.040) -> no exclusions.
    'exclude': {},
    'k_r': {'Ref': 1.0, 'HalfSC': 1.5, 'SC': 2.0},
    # sampling plan: mode 'own' (donor) or 'transfer' (similarity);
    # seeds are the representative draws (wMAE closest to the 10-seed mean)
    'plan': {
        'Ref':    {'mode': 'own',      'n_base': 22, 'n_spd': 4, 'seed': 9},
        'HalfSC': {'mode': 'transfer', 'n_base': 24, 'n_spd': 3, 'seed': 9},
        'SC':     {'mode': 'transfer', 'n_base': 24, 'n_spd': 3, 'seed': 6},
    },
    'donor_scale': 'Ref',
    'n_probe_transfer': 6,       # donor probes per transferred speed (free)
    'n_seeds_pick': 10,          # seeds scanned when seed is None
}


class AcLossPipeline:
    """End-to-end driver for dataset -> model -> metrics -> figures."""

    def __init__(self, config: Optional[dict] = None):
        self.cfg = dict(DEFAULT_CONFIG)
        if config:
            self.cfg.update(config)
        self._datasets: Dict[str, object] = {}
        self._models: Dict[str, SeparableRbfModel] = {}
        self._donor: Optional[SeparableRbfModel] = None

    # ── data ───────────────────────────────────────────────────────────
    def load_dataset(self, scale: str):
        """Loads (and caches) the AcLossDataset for a model scale."""
        if scale not in self._datasets:
            path = os.path.join(self.cfg['data_root'],
                                self.cfg['json'][scale])
            records, err = AcLossJsonReader.read(path, scale)
            if err is not None:
                raise IOError(f'{scale}: dataset read failed ({err}): {path}')
            self._datasets[scale] = \
                RbfModelBuilder.match_records_and_create_dataset(
                    records,
                    exclude_points=self.cfg['exclude'].get(scale))
        return self._datasets[scale]

    def dataset_struct(self, scale: str) -> Dict[str, np.ndarray]:
        """Dataset as a dict of 1-D arrays (MATLAB: fields of a struct)."""
        ds = self.load_dataset(scale)
        return {
            'speed_rpm': ds.speeds_k * 1000.0,
            'irms_A': ds.irms_arr,
            'phase_deg': ds.phase_arr,
            'af': ds.af_arr,
            'hybrid_kW': ds.h_ac_arr,
            'tsfea_kW': ds.f_ac_arr,
        }

    def scan_outliers(self, scale: str, tol: float = 0.25) -> List[dict]:
        """AF neighbor-consistency scan along the beta and current axes.

        Returns a list of dicts describing points whose AF deviates more
        than `tol` (relative) from the linear interpolation of neighbors.
        """
        ds = self.load_dataset(scale)
        flags = {}

        def scan(group_keys, axis_vals):
            gk = np.stack(group_keys, axis=1)
            for row in np.unique(np.round(gk, 1), axis=0):
                m = np.all(np.abs(gk - row) < 0.5, axis=1)
                idx = np.where(m)[0]
                if len(idx) < 3:
                    continue
                order = idx[np.argsort(axis_vals[idx])]
                x, af = axis_vals[order], ds.af_arr[order]
                for k in range(1, len(order) - 1):
                    interp = af[k - 1] + (af[k + 1] - af[k - 1]) \
                        * (x[k] - x[k - 1]) / (x[k + 1] - x[k - 1] + 1e-12)
                    dev = (af[k] - interp) / (abs(interp) + 1e-12)
                    if abs(dev) > tol:
                        i = order[k]
                        flags[(round(float(ds.speeds_k[i]), 2),
                               round(float(ds.irms_arr[i]), 1),
                               round(float(ds.phase_arr[i]), 1))] = {
                            'speed_rpm': float(ds.speeds_k[i] * 1000),
                            'irms_A': float(ds.irms_arr[i]),
                            'phase_deg': float(ds.phase_arr[i]),
                            'af': float(ds.af_arr[i]),
                            'af_expected': float(interp),
                            'dev_pct': float(dev * 100.0),
                        }

        scan([ds.speeds_k * 10, ds.irms_arr], ds.phase_arr)
        scan([ds.speeds_k * 10, ds.phase_arr], ds.irms_arr)
        return list(flags.values())

    # ── models ─────────────────────────────────────────────────────────
    def build_donor(self) -> SeparableRbfModel:
        """Builds (and caches) the donor model (Ref, own sampling)."""
        if self._donor is None:
            scale = self.cfg['donor_scale']
            self._donor = self.build_model(scale)
        return self._donor

    def build_model(self, scale: str,
                    seed: Optional[int] = None) -> SeparableRbfModel:
        """Builds (and caches) the adopted model for `scale`.

        seed=None uses the configured seed; if that is also None, the
        representative seed (single-draw wMAE closest to the multi-seed
        mean) is selected automatically.
        """
        if scale in self._models and seed is None:
            return self._models[scale]
        plan = self.cfg['plan'][scale]
        use_seed = seed if seed is not None else plan['seed']
        if use_seed is None:
            use_seed = self.pick_representative_seed(scale)
        model = self._build_with_seed(scale, use_seed)
        if seed is None:
            self._models[scale] = model
        return model

    def _build_with_seed(self, scale: str, seed: int,
                         exponent: Optional[bool] = None
                         ) -> SeparableRbfModel:
        plan = self.cfg['plan'][scale]
        ds = self.load_dataset(scale)
        expo = (bool(self.cfg.get('exponent', False))
                if exponent is None else bool(exponent))
        if plan['mode'] == 'own':
            return AcLossEvaluator.rebuild_sep_model_with_subsampling(
                ds, plan['n_base'], plan['n_spd'], seed,
                base_speed=self.cfg['base_speed'], exponent=expo)
        return RbfModelBuilder.build_separable_rbf_transfer(
            ds, self.build_donor(), self.cfg['k_r'][scale],
            plan['n_base'], plan['n_spd'], seed,
            base_speed=self.cfg['base_speed'],
            n_probe_transfer=self.cfg['n_probe_transfer'],
            exponent=expo)

    def pick_representative_seed(self, scale: str) -> int:
        """Seed in [0, n_seeds_pick) whose wMAE is closest to the mean."""
        wm = {s: self._metrics_of(scale, self._build_with_seed(scale, s))[1]
              for s in range(self.cfg['n_seeds_pick'])}
        mean_w = float(np.mean(list(wm.values())))
        return min(wm, key=lambda s: abs(wm[s] - mean_w))

    # ── prediction & metrics ───────────────────────────────────────────
    def predict_af(self, scale: str, speed_rpm, irms_A, phase_deg):
        """AF prediction; scalar in -> float out, array in -> ndarray."""
        model = self.build_model(scale)
        out = model.predict(np.asarray(speed_rpm, float),
                            np.asarray(irms_A, float),
                            np.asarray(phase_deg, float))
        return float(out) if np.ndim(out) == 0 else out

    def predict_loss_kW(self, scale: str, speed_rpm, irms_A, phase_deg,
                        hybrid_kW):
        """Calibrated AC loss = AF * hybrid loss."""
        af = self.predict_af(scale, speed_rpm, irms_A, phase_deg)
        return np.asarray(hybrid_kW, float) * af

    def _metrics_of(self, scale: str,
                    model: SeparableRbfModel) -> Tuple[float, float]:
        ds = self.load_dataset(scale)
        pred = ds.h_ac_arr * model.predict(
            ds.speeds_k * 1000.0, ds.irms_arr, ds.phase_arr)
        e = np.abs((pred - ds.f_ac_arr) / (ds.f_ac_arr + 1e-12) * 100.0)
        wmae = float(np.sum(ds.f_ac_arr * e) / np.sum(ds.f_ac_arr))
        return float(e.mean()), wmae

    def metrics(self, scale: str) -> Dict[str, float]:
        """MAE / wMAE of the adopted model and of the uncorrected Hybrid."""
        ds = self.load_dataset(scale)
        mae, wmae = self._metrics_of(scale, self.build_model(scale))
        eh = np.abs((ds.h_ac_arr - ds.f_ac_arr)
                    / (ds.f_ac_arr + 1e-12) * 100.0)
        plan = self.cfg['plan'][scale]
        n_own = plan['n_base'] + (
            plan['n_spd'] * 3 if plan['mode'] == 'own' else plan['n_spd'])
        return {
            'mae_pct': mae,
            'wmae_pct': wmae,
            'hybrid_mae_pct': float(eh.mean()),
            'hybrid_wmae_pct': float(np.sum(ds.f_ac_arr * eh)
                                     / np.sum(ds.f_ac_arr)),
            'n_points': float(len(ds)),
            'n_own_samples': float(n_own),
        }

    def similarity_pairs(self, scale: str = 'SC') -> Dict[str, np.ndarray]:
        """SCL-M similarity check: variant low-band points vs mapped Ref.

        Only exact grid matches are compared (k_r^2 must map onto Ref
        speeds), so this is meaningful for SC (k_r = 2).
        """
        kr = self.cfg['k_r'][scale]
        ref = self.load_dataset(self.cfg['donor_scale'])
        var = self.load_dataset(scale)
        cols = {k: [] for k in ('speed_rpm', 'irms_A', 'phase_deg',
                                'af_variant', 'af_ref_mapped', 'dev_pct')}
        for i in range(len(var)):
            tgt_spd = var.speeds_k[i] * kr**2
            if tgt_spd > ref.speeds_k.max() + 0.1:
                continue
            m = np.where((np.abs(ref.speeds_k - tgt_spd) < 0.1)
                         & (np.abs(ref.irms_arr - var.irms_arr[i] / kr) < 2.0)
                         & (np.abs(ref.phase_arr - var.phase_arr[i]) < 1.0))[0]
            if len(m) == 0:
                continue
            j = m[0]
            cols['speed_rpm'].append(var.speeds_k[i] * 1000.0)
            cols['irms_A'].append(var.irms_arr[i])
            cols['phase_deg'].append(var.phase_arr[i])
            cols['af_variant'].append(var.af_arr[i])
            cols['af_ref_mapped'].append(ref.af_arr[j])
            cols['dev_pct'].append((var.af_arr[i] - ref.af_arr[j])
                                   / ref.af_arr[j] * 100.0)
        return {k: np.asarray(v, float) for k, v in cols.items()}

    # ── figures (journal style, English, Times New Roman) ──────────────
    @staticmethod
    def _journal_rc():
        import matplotlib.pyplot as plt
        plt.rcParams.update({
            'font.family': 'serif',
            'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
            'font.size': 8, 'axes.titlesize': 8.5, 'axes.labelsize': 8,
            'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
            'axes.linewidth': 0.6, 'savefig.dpi': 300,
            'savefig.bbox': 'tight', 'savefig.pad_inches': 0.03,
            'mathtext.fontset': 'stix',
        })
        return plt

    def make_validation_figure(self, scale: str, out_path: str) -> str:
        """Parity plot + error boxplot (Fig 14 style). Returns out_path.

        Four series against TS-FEA: uncorrected Hybrid, non-separable
        3-D TPS RBF (all points, reference), scalar separable f*g and
        the adopted exponent separable f*g**p — both separable forms use
        the identical sampling plan/seed, isolating the model form.
        """
        plt = self._journal_rc()
        ds = self.load_dataset(scale)
        model = self.build_model(scale)
        model_3d = RbfModelBuilder.build_3d_rbf(ds)
        plan = self.cfg['plan'][scale]
        model_sc = self._build_with_seed(scale, plan['seed'],
                                         exponent=False)
        ea, e3, es = AcLossEvaluator.evaluate_errors(ds, model_3d, model)
        _, _, e_sc = AcLossEvaluator.evaluate_errors(ds, model_3d, model_sc)
        _, wmae = self._metrics_of(scale, model)
        _, wmae_sc = self._metrics_of(scale, model_sc)
        n_own = plan['n_base'] + (
            plan['n_spd'] * 3 if plan['mode'] == 'own' else plan['n_spd'])
        tag = (f'{n_own} pts' if plan['mode'] == 'own'
               else f'{n_own} own pts + transfer')

        h_ac, f_ac = ds.h_ac_arr, ds.f_ac_arr
        corr_3d = h_ac * model_3d.predict(ds.speeds_k * 1000.0,
                                          ds.irms_arr, ds.phase_arr)
        corr_sep = h_ac * model.predict(ds.speeds_k * 1000.0,
                                        ds.irms_arr, ds.phase_arr)
        corr_sc = h_ac * model_sc.predict(ds.speeds_k * 1000.0,
                                          ds.irms_arr, ds.phase_arr)

        fig, (ax, ax2) = plt.subplots(
            1, 2, figsize=(7.0, 2.9),
            gridspec_kw={'width_ratios': [1.15, 1]})
        fig.subplots_adjust(left=0.09, right=0.98, top=0.92, bottom=0.17,
                            wspace=0.30)
        lim = [0, max(f_ac.max(), corr_3d.max(), corr_sep.max(),
                      corr_sc.max()) * 1.06]
        ax.plot(lim, lim, 'k--', lw=0.9, label='Perfect fit')
        ax.scatter(f_ac, h_ac, c='#999999', s=14, alpha=0.55, zorder=2,
                   label=f'Hybrid, uncorrected (MAE {np.abs(ea).mean():.1f}%)')
        ax.scatter(f_ac, corr_3d, c='#2c6fad', s=20, alpha=0.7, marker='D',
                   zorder=3, label=f'3D TPS RBF, {len(ds)} pts')
        ax.scatter(f_ac, corr_sc, c='#2e7d32', s=22, alpha=0.75, marker='^',
                   zorder=4,
                   label=f'Scalar separable (wMAE {wmae_sc:.1f}%)')
        ax.scatter(f_ac, corr_sep, c='#e65100', s=26, alpha=0.85, marker='o',
                   zorder=5,
                   label=f'Exponent separable, {tag} (wMAE {wmae:.1f}%)')
        ax.set_xlabel('TS-FEA AC loss [kW]')
        ax.set_ylabel('Predicted AC loss [kW]')
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.grid(True, ls=':', lw=0.45, color='#cccccc')
        ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(fontsize=6.3, frameon=False, loc='upper left')

        bp = ax2.boxplot([ea, e3, e_sc, es],
                         tick_labels=['Hybrid\n(uncorr.)', '3D TPS\nRBF',
                                      'Scalar\nseparable',
                                      'Exponent\nseparable'],
                         patch_artist=True, widths=0.45,
                         medianprops={'color': 'black', 'lw': 0.9},
                         flierprops={'marker': 'o', 'ms': 2.5, 'mfc': 'none',
                                     'mec': '#888888', 'mew': 0.5})
        for box, c, a in zip(bp['boxes'],
                             ['#999999', '#2c6fad', '#2e7d32', '#e65100'],
                             [0.45, 0.6, 0.6, 0.65]):
            box.set_facecolor(c)
            box.set_alpha(a)
        ax2.axhline(0, color='k', ls='--', lw=0.8)
        ax2.set_ylabel('Relative error [%]')
        ax2.grid(True, axis='y', ls=':', lw=0.45, color='#cccccc')
        ax2.set_axisbelow(True)
        ax2.spines[['top', 'right']].set_visible(False)
        for x, arr in zip([1, 2, 3, 4], [ea, e3, e_sc, es]):
            ax2.text(x, np.max(arr) + 3, f'MAE {np.abs(arr).mean():.1f}%',
                     ha='center', fontsize=6.5, fontweight='bold')

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def transfer_ablation_grid(self, scale: str,
                               n_base_list: Optional[List[int]] = None,
                               n_spd_list: Optional[List[int]] = None,
                               n_seeds: int = 10) -> Dict[str, np.ndarray]:
        """wMAE grid of the transfer plan over (n_base, n_spd8)."""
        n_base_list = n_base_list or [8, 10, 12, 16, 20, 24]
        n_spd_list = n_spd_list or [0, 1, 2, 3, 4]
        ds = self.load_dataset(scale)
        kr = self.cfg['k_r'][scale]
        G = np.full((len(n_base_list), len(n_spd_list)), np.nan)
        for bi, nb in enumerate(n_base_list):
            for si, ns in enumerate(n_spd_list):
                ws = []
                for seed in range(n_seeds):
                    try:
                        m = RbfModelBuilder.build_separable_rbf_transfer(
                            ds, self.build_donor(), kr, nb, ns, seed,
                            base_speed=self.cfg['base_speed'],
                            n_probe_transfer=self.cfg['n_probe_transfer'],
                            exponent=bool(self.cfg.get('exponent', False)))
                    except np.linalg.LinAlgError:
                        continue
                    ws.append(self._metrics_of(scale, m)[1])
                if ws:
                    G[bi, si] = float(np.mean(ws))
        return {'n_base': np.asarray(n_base_list, float),
                'n_spd8': np.asarray(n_spd_list, float),
                'wmae_pct': G}

    def export_model_json(self, scale: str, out_path: str) -> str:
        """Writes the adopted model as a motor_scaling-compatible JSON.

        New-style 'separable_model' block with explicit base centers and
        the spread-exponent polynomial; consumed by
        tools.motor_scaling.adapters.RbfJsonReader -> RbfModelParams
        (q_coeffs-aware), e.g. for the MTPA/FW efficiency-map stage.
        """
        import json
        m = self.build_model(scale)
        plan = self.cfg['plan'][scale]
        data = {
            '_meta': {
                'scale': scale,
                'exponent': m.q_coeffs is not None,
                'base_speed_kRPM': self.cfg['base_speed'],
                'plan': {k: plan[k] for k in
                         ('mode', 'n_base', 'n_spd', 'seed')},
            },
            'length_scales': {'LS_I_A': float(m.ls_i),
                              'LS_P_deg': float(m.ls_p)},
            'separable_model': {
                'model': 'Separable_1D_2D_RBF',
                'n_base_centers': int(len(m.w_g)),
                'base_weights': np.asarray(m.w_g, float).tolist(),
                'base_centers_i':
                    np.asarray(m.base_centers_i, float).tolist(),
                'base_centers_p':
                    np.asarray(m.base_centers_p, float).tolist(),
                'ls_i': float(m.ls_i),
                'ls_p': float(m.ls_p),
                'speed_poly_coeffs':
                    np.asarray(m.p_coeffs, float).tolist(),
                'spread_poly_coeffs':
                    (np.asarray(m.q_coeffs, float).tolist()
                     if m.q_coeffs is not None else None),
            },
        }
        os.makedirs(os.path.dirname(os.path.abspath(out_path)),
                    exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return out_path

    def make_af_map_figure(self, scale: str, out_path: str) -> str:
        """AF contour map on the id-iq plane, one panel per speed."""
        from .AcLossPlotter import AcLossPlotter
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        AcLossPlotter.plot_af_map_visualization(
            self.load_dataset(scale), self.build_model(scale), out_path)
        return out_path

    def make_af_surface_figure(self, scale: str, out_path: str) -> str:
        """3-D AF(id, iq) surfaces, one panel per speed."""
        from .AcLossPlotter import AcLossPlotter
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        AcLossPlotter.plot_3d_surface(
            self.load_dataset(scale), self.build_model(scale), out_path)
        return out_path

    def make_all_figures(self, out_dir: str) -> List[str]:
        """Regenerates the validation figures for Ref and SC."""
        outs = []
        for scale in ('Ref', 'SC'):
            outs.append(self.make_validation_figure(
                scale, os.path.join(out_dir,
                                    f'RBF_correction_validation_{scale}.png')))
        return outs
