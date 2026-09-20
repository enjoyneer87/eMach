"""Freeze native cap/RBF predictions for the author-approved M2 four points.

No solver is launched. Exclusive output creation prevents silent re-freezing.
"""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import asdict
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess

import numpy as np

from run_evaluator_robustness import datasets_for, fixed_plans, fit_one, SCALES
from run_ref_only_field_pipeline import (
    AcLossPipeline, DEFAULT_CONFIG, checksum, evaluate_hybrid, ref_row_for,
    mask_truth, predict, record_result,
)


def serial(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('data', 'spectra', 'comparison', 'ref_mot', 'sc_mot', 'out'):
        ap.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        print('Refusing to overwrite freeze:', a.out)
        return 2
    source = json.loads(a.spectra.read_text())
    comparison = json.loads(a.comparison.read_text())
    assert checksum(a.spectra) == comparison['source_spectra_sha256']
    with contextlib.redirect_stdout(io.StringIO()):
        pipe = AcLossPipeline({'data_root': str(a.data)})
        deposited = {s: pipe.load_dataset(s) for s in SCALES}
        data = datasets_for(deposited, source['rows'], 'capped_P24c6')
        plans = fixed_plans(data)
    models, records, masked_models, frozen = {}, {}, {}, {}
    for s in SCALES:
        with contextlib.redirect_stdout(io.StringIO()):
            m, idx, admission = fit_one(s, data[s], models.get('Ref'), data['Ref'], plans[s])
        record, error = record_result(data[s], m, idx)
        assert not error, error
        np.testing.assert_allclose(record['prediction_kW'], comparison['fixed_grid']['bare'][s]['prediction_kW'], atol=1e-9, rtol=0)
        assert checksum(a.data / DEFAULT_CONFIG['json'][s]) == comparison['input_sha256'][s]
        models[s], records[s] = m, record
        frozen[s] = {'model': asdict(m), 'plan': plans[s], 'admitted_pairs': admission,
                     'training_indices': idx, 'training_coordinates': record['own_train_coordinates'],
                     'full_wmae_pct': record['full']['wmae_pct'],
                     'heldout_wmae_pct': record['heldout_own_only']['wmae_pct']}
    masked_data = {s: mask_truth(data[s], records[s]['own_train_indices']) for s in SCALES}
    for s in SCALES:
        with contextlib.redirect_stdout(io.StringIO()):
            m, idx, _ = fit_one(s, masked_data[s], masked_models.get('Ref'), masked_data['Ref'], plans[s])
        delta = float(np.max(np.abs(predict(m, data[s]) - predict(models[s], data[s]))))
        assert delta == 0
        masked_models[s] = m
        frozen[s]['truth_mask_max_delta_kW'] = delta
    points = []
    for s in ('Ref', 'SC'):
        kr = DEFAULT_CONFIG['k_r'][s]
        for speed, beta in ((6000, 36), (12000, 72)):
            current = 460 * kr
            row, error = ref_row_for(source['rows'], current, beta, kr)
            assert not error, error
            h = evaluate_hybrid(row, current, speed, kr)
            af = float(models[s].predict(speed, current, beta))
            assert np.isfinite(af) and af > 0
            points.append({'id': f'{s}_{speed}rpm_{current:g}A_{beta}deg', 'motor': s,
                           'speed_rpm': speed, 'current_A_rms': current, 'beta_deg': beta,
                           'hybrid_kW': h['hybrid_kW'], 'predicted_AF': af,
                           'prediction_kW': h['hybrid_kW'] * af, 'hybrid_details': h,
                           'ref_field_raw_sha256': row['raw_sha256']})
    here = Path(__file__).resolve().parent
    repo = here.parent.parent
    code = [here / n for n in ('freeze_m2_stage_a.py', 'run_m2_stage_a.py',
                               'run_tps_workflow_comparison.py', 'run_ref_only_field_pipeline.py',
                               'run_evaluator_robustness.py')]
    code += list((repo / 'tools' / 'jeet_acloss_rbf').glob('*.py'))
    kernel_root = here / 'acloss_ref_methods'
    assert (kernel_root / 'volpe_hybrid_acloss.py').is_file()
    code += list(kernel_root.glob('*.py'))
    payload = {'schema': 'm2-stage-a-freeze-v1', 'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
               'author_decision': {'question': 'Q24', 'answer': '1번부터해쥐',
                                   'execution_authorized': True, 'stage': 'A', 'stage_B_authorized': False},
               'model_decision': 'Retain native bare RBF per Q18; TPS whole-grid difference is small. No M2 truth used.',
               'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
               'git_status': subprocess.check_output(['git', 'status', '--short'], cwd=repo, text=True),
               'code_sha256': {str(p.relative_to(repo)): checksum(p) for p in code},
               'input_sha256': comparison['input_sha256'], 'spectra_sha256': checksum(a.spectra),
               'comparison_sha256': checksum(a.comparison), 'models': frozen, 'points': points,
               'mot_sources': {s: {'path': str(p.resolve()), 'sha256': checksum(p)}
                               for s, p in [('Ref', a.ref_mot), ('SC', a.sc_mot)]},
               'solver_protocol': {'TorqueNumberCycles': 1, 'TorquePointsPerCycle': 128,
                                   'ProximityLossModel': 3, 'ArmatureConductor_Temperature': 80,
                                   'StatorConductor_Temperature': 80,
                                   'ArmatureConductor_ResistivityAt20C': 1.724e-8},
               'loss_definition': 'Active AC excess = sum(ACLoss_FEA_OnLoad_PerTurn)/1000 - 3*(Resistance_MotorLAB-EndWindingResistance_Lab)*Irms^2/1000 kW',
               'limitations': ['Four prescribed-current speed-interpolation points only.',
                               'No independent HalfSC or new 16 kRPM current/phase validation.',
                               'Same one-cycle/128-step protocol as existing truth; numerical convergence is M3.',
                               'No training updates are permitted from these four truths.']}
    assert not payload['git_status'].strip(), 'Commit the experiment code before freezing'
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, default=serial)
        stream.write('\n')
    print('FROZEN', a.out, checksum(a.out))
    for p in points:
        print(p['id'], 'prediction_kW', p['prediction_kW'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
