"""M4-2: evaluator robustness with fixed truth coordinates and Ref-only fields.

No new FEA. Compare sparse refits, not exact invariance. The main experiment
freezes the capped evaluator's Full-FEA samples AND donor probe coordinates.
An adaptive-placement companion distinguishes evaluator and placement effects.
"""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import replace
import io
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from run_ref_only_field_pipeline import (
    AcLossDataset, AcLossPipeline, Builder, DEFAULT_CONFIG, SIGMA_80, MU0,
    evaluate_hybrid, ref_row_for, fit_donor, fit_target, mask_truth,
    record_result, checksum, predict,
)
from acloss_ref_methods.volpe_hybrid_acloss import calc_prox_2D_G2

SCALES = ('Ref', 'HalfSC', 'SC')
KERNELS = ('capped_P24c6', 'uncapped_P24c6', 'G2', 'G2_modified_delta')


def hybrid(row, point, kr, kernel):
    adopted = evaluate_hybrid(row, point.current_rms, point.speed_rpm, kr)
    if kernel == 'capped_P24c6':
        return adopted['hybrid_kW']
    if kernel == 'constant_2p7':
        return adopted['hybrid_kW']*2.7
    w, h, length = 3.711e-3*kr, 1.686e-3*kr, .150
    bt, br = (np.asarray(row[k]) for k in ('b2t_msq_sum', 'b2r_msq_sum'))
    fm = np.arange(1, len(bt)+1) * point.speed_rpm*4/60
    if kernel == 'uncapped_P24c6':
        proximity = 8*SIGMA_80*length/24 * np.sum(
            (2*np.pi*fm)**2 * (w*h**3*bt + h*w**3*br/36))
    elif kernel in ('G2', 'G2_modified_delta'):
        # Match the direction convention of mesh_b_vs_mcad.prox_g2:
        # line-averaged tangential B pairs with gw*kernel(gh).
        proximity = 8*np.sum(calc_prox_2D_G2(
            w, h, fm, length, np.sqrt(bt), np.sqrt(br), SIGMA_80, MU0,
            use_modified_delta=kernel == 'G2_modified_delta'))
    else:
        raise ValueError(kernel)
    return float((proximity+adopted['skin_excess_W'])/1000)


def datasets_for(deposited, spectra, kernel):
    result = {}
    for scale, ds in deposited.items():
        kr = DEFAULT_CONFIG['k_r'][scale]
        points = []
        for point in ds.points:
            row, error = ref_row_for(spectra, point.current_rms, point.phase_deg, kr)
            if error:
                raise ValueError(error)
            h = hybrid(row, point, kr, kernel)
            if not np.isfinite(h) or h <= 0:
                raise ValueError('nonpositive or nonfinite denominator')
            points.append(replace(point, hybrid_ac_kW=h, AF=point.fea_ac_kW/h))
        result[scale] = AcLossDataset(points)
        assert len(points) == 96
        np.testing.assert_array_equal(result[scale].f_ac_arr, ds.f_ac_arr)
    return result


def fixed_plans(baseline):
    plans = {}
    for scale, ds in baseline.items():
        kr = DEFAULT_CONFIG['k_r'][scale]
        plan = DEFAULT_CONFIG['plan'][scale]
        common = dict(dataset=ds, n_base=24, base_speed=16.,
                      placement='structured', seed=plan['seed'])
        if scale == 'Ref':
            plans[scale] = Builder.plan_sampling_indices(n_spd=4, **common)
        else:
            probes = Builder.plan_sampling_indices(n_spd=6, **common)
            own = Builder.plan_sampling_indices(n_spd=3, **common)
            plans[scale] = {'base': probes['base'], 'by_speed': {
                speed: idx if speed*kr**2 <= 16.1 else own['by_speed'][speed]
                for speed, idx in probes['by_speed'].items()}}
    return plans


def fit_one(scale, ds, donor, donor_ds, plan):
    trace = []
    original = Builder._fit_speed_scaling

    def logged(samples, base_speed, exponent, verbose=True):
        trace.append({str(speed): len(values) for speed, values in samples.items()})
        return original(samples, base_speed, exponent, verbose=False)

    with patch.object(Builder, '_fit_speed_scaling', staticmethod(logged)):
        if plan is None:
            model, indices = (fit_donor(ds) if scale == 'Ref' else
                              fit_target(ds, donor, donor_ds, scale))
        else:
            if scale == 'Ref':
                model = Builder.build_separable_rbf(ds, base_speed=16., exponent=True,
                                                    index_plan=plan)
            else:
                model = Builder.build_separable_rbf_transfer(
                    ds, donor, DEFAULT_CONFIG['k_r'][scale], 24, 3,
                    seed=DEFAULT_CONFIG['plan'][scale]['seed'], base_speed=16.,
                    n_probe_transfer=6, exponent=True, placement='structured',
                    donor_dataset=donor_ds, rule='predicted_loss', index_plan=plan)
            indices = Builder.last_train_idx.copy()
    assert len(trace) == 1
    return model, indices, trace[0]


def fit_family(datasets, plans=None, mask_reference=None):
    records, fitted = {}, {}
    data = {s: mask_truth(ds, mask_reference[s]['own_train_indices'])
            if mask_reference else ds for s, ds in datasets.items()}
    with contextlib.redirect_stdout(io.StringIO()):
        for scale in SCALES:
            ds = data[scale]
            model, indices, trace = fit_one(scale, ds, fitted.get('Ref'), data['Ref'],
                                            None if plans is None else plans[scale])
            record, error = record_result(datasets[scale], model, indices)
            if error:
                raise ValueError(error)
            assert len(indices) == (36 if scale == 'Ref' else 27)
            assert abs(np.polyval(model.p_coeffs, 16)-1) < 1e-12
            assert abs(np.polyval(model.q_coeffs, 16)-1) < 1e-12
            record['admitted_pairs_per_speed'] = trace
            record['speed_level_coefficients'] = model.p_coeffs.tolist()
            record['speed_power_coefficients'] = model.q_coeffs.tolist()
            record['g_min_on_grid'] = float(np.min(model.predict_g(ds.irms_arr, ds.phase_arr)))
            records[scale], fitted[scale] = record, model
    return records


def compare(base, result):
    truth = np.asarray(result['truth_kW'])
    a, b = np.asarray(base['prediction_kW']), np.asarray(result['prediction_kW'])
    same = set(base['own_train_indices']) == set(result['own_train_indices'])
    return {'same_own_truth_coordinates': same,
            'changed_truth_coordinates': len(set(base['own_train_indices']) ^ set(result['own_train_indices'])),
            'full_wmae_delta_pp': result['full']['wmae_pct']-base['full']['wmae_pct'],
            'heldout_wmae_delta_pp': result['heldout_own_only']['wmae_pct']-base['heldout_own_only']['wmae_pct'],
            'loss_weighted_prediction_change_pct': float(100*np.abs(a-b).sum()/truth.sum()),
            'max_point_prediction_change_pct': float(100*np.max(np.abs(a-b)/a))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--spectra', type=Path, required=True)
    ap.add_argument('--data', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    source = json.loads(args.spectra.read_text(encoding='utf-8'))
    assert source['schema'] == 'ref-ms-line-spectra-v1' and len(source['rows']) == 30
    with contextlib.redirect_stdout(io.StringIO()):
        pipeline = AcLossPipeline({'data_root': str(args.data)})
        deposited = {s: pipeline.load_dataset(s) for s in SCALES}
        baseline = datasets_for(deposited, source['rows'], KERNELS[0])
        plans = fixed_plans(baseline)
    datasets = {k: datasets_for(deposited, source['rows'], k) for k in (*KERNELS, 'constant_2p7')}
    cases, comparisons = {}, {}
    for mode in ('fixed_coordinates', 'adaptive_placement'):
        cases[mode], comparisons[mode] = {}, {}
        for kernel, family in datasets.items():
            records = fit_family(family, plans if mode == 'fixed_coordinates' else None)
            masked = fit_family(family, plans if mode == 'fixed_coordinates' else None, records)
            for s in SCALES:
                np.testing.assert_array_equal(records[s]['own_train_indices'], masked[s]['own_train_indices'])
                delta = float(np.max(np.abs(np.array(records[s]['prediction_kW'])-masked[s]['prediction_kW'])))
                assert delta == 0
                records[s]['truth_mask_max_prediction_delta_kW'] = delta
            cases[mode][kernel] = records
            comparisons[mode][kernel] = {s: compare(cases[mode][KERNELS[0]][s], records[s]) for s in SCALES}
            for s in SCALES:
                if mode == 'fixed_coordinates':
                    assert comparisons[mode][kernel][s]['same_own_truth_coordinates']
                rec = records[s]
                print(f"{mode:20s} {kernel:19s} {s:6s} unc={rec['uncorrected']['wmae_pct']:.4f} "
                      f"full={rec['full']['wmae_pct']:.6f} held={rec['heldout_own_only']['wmae_pct']:.6f} "
                      f"admitted={rec['admitted_pairs_per_speed']}")
    for s in SCALES:
        np.testing.assert_allclose(cases['fixed_coordinates'][KERNELS[0]][s]['prediction_kW'],
                                   cases['adaptive_placement'][KERNELS[0]][s]['prediction_kW'], rtol=1e-12)
    output = {'status': 'PASS; empirical robustness comparison, not invariance proof',
              'conditions': {'new_FEA_solves': 0, 'Ref_MS_fields': 30, 'own_truth_budgets': [36, 27, 27],
                             'sigma_S_per_m': SIGMA_80, 'anchor': 'exact f(16)=p(16)=1',
                             'field_sampling': 'same Ref line-averaged complex-harmonic spectra for every kernel',
                             'skin_term': 'same excess-skin evaluation for every physical kernel',
                             'transfer_rule': 'predicted_loss', 'primary_comparison': 'fixed_coordinates'},
              'source_spectrum_sha256': checksum(args.spectra),
              'input_summary_sha256': {s: checksum(args.data/DEFAULT_CONFIG['json'][s]) for s in SCALES},
              'source_code_sha256': {str(p.name): checksum(p) for p in [Path(__file__),
                   Path(__file__).parents[2]/'tools/jeet_acloss_rbf/RbfModelBuilder.py',
                   Path(__file__).with_name('run_ref_only_field_pipeline.py'),
                   Path(__file__).parent/'acloss_ref_methods/volpe_hybrid_acloss.py']},
              'plans': {s: {'base': p['base'].tolist(), 'by_speed': {str(k): v.tolist() for k,v in p['by_speed'].items()}}
                        for s,p in plans.items()}, 'cases': cases, 'relative_to_capped': comparisons,
              'limitations': ['Own-held-out is not independent prospective validation and has no 16 kRPM points.',
                              'Only the listed physical kernels on fixed line-sampled Ref spectra are tested.',
                              'constant_2p7 is a numerical sensitivity diagnostic, not a separate physical evaluator.',
                              'The existing 0.3 <= AF/g <= 3 admission rule is preserved; admitted counts are reported.',
                              'No universal robustness threshold is imposed after seeing the result.']}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
