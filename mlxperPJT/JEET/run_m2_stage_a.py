"""Run four frozen M2 points using isolated copies and owned Motor-CAD sessions.

Never writes training summaries or source .mot files. One fresh instance per
point, with durable start/result/error records and no automatic solver retries.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time
import traceback

import numpy as np
import psutil


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_new(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def inventory():
    return [p.info for p in psutil.process_iter(['pid', 'name', 'create_time'])
            if (p.info['name'] or '').lower() == 'motorcad.exe']


def loss_record(per_turn, total_W, r_total, r_end, current):
    """Pure checked conversion using the existing three-phase loss contract."""
    values = [float(v) for v in per_turn.split(':') if v.strip()] if isinstance(per_turn, str) else list(map(float, per_turn))
    if len(values) != 6 or not np.all(np.isfinite(values)) or min(values) <= 0:
        return None, 'Invalid six-turn winding loss'
    if not np.isfinite(r_total + r_end) or not 0 < r_end < r_total:
        return None, 'Invalid active/end resistance'
    dc = 3 * (r_total-r_end) * current**2 / 1000
    excess = sum(values)/1000-dc
    if not np.isfinite(excess) or excess <= 0:
        return None, 'Nonpositive/nonfinite active AC excess'
    # Existing Full-FEA total is independently reported active AC excess.
    if not np.isfinite(total_W) or abs(excess-total_W/1000) > max(1e-5, excess*1e-5):
        return None, 'Per-turn/DC and reported active AC excess disagree'
    return {'per_turn_W': values, 'per_turn_sum_kW': sum(values)/1000,
            'Resistance_MotorLAB_ohm': r_total, 'EndWindingResistance_Lab_ohm': r_end,
            'active_resistance_ohm': r_total-r_end, 'dc_active_kW': dc,
            'dc_end_kW': 3*r_end*current**2/1000,
            'reported_ACLoss_FEA_OnLoad_Total_W': total_W, 'truth_ac_excess_kW': excess}, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--freeze', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--exe', type=Path, required=True)
    a = ap.parse_args()
    f = json.loads(a.freeze.read_text(encoding='utf-8'))
    assert f['schema'] == 'm2-stage-a-freeze-v1' and f['author_decision']['execution_authorized']
    assert len(f['points']) == 4 and not f['author_decision']['stage_B_authorized']
    repo = Path(__file__).resolve().parents[2]
    for rel, digest in f['code_sha256'].items():
        assert sha(repo/rel) == digest, f'Frozen code changed: {rel}'
    for source in f['mot_sources'].values():
        assert sha(source['path']) == source['sha256'], 'Source model changed'
    assert a.exe.is_file()
    # Refuse all reuse, including failed campaigns. Resume must be explicit.
    a.out.mkdir(parents=True, exist_ok=False)
    freeze_sha = sha(a.freeze)
    write_new(a.out/'campaign_start.json', {'started_at_utc': utc(), 'freeze_sha256': freeze_sha,
                                            'preserved_motorcad_processes': inventory(), 'executable': str(a.exe)})
    import ansys.motorcad.core as mcapi
    mcapi.set_motorcad_exe(str(a.exe))
    for point in f['points']:
        d = a.out/point['id']
        d.mkdir()
        source = f['mot_sources'][point['motor']]
        mot = d/'model.mot'
        shutil.copy2(source['path'], mot)
        assert sha(mot) == source['sha256']
        before = inventory()
        mc, owned_pid = None, None
        start = time.perf_counter()
        try:
            print(utc(), 'OPEN', point['id'], flush=True)
            mc = mcapi.MotorCAD(open_new_instance=True, reuse_parallel_instances=False,
                                keep_instance_open=False, enable_exceptions=True)
            owned_pid = int(mc.get_variable('MotorCADprocessID'))
            assert owned_pid not in {p['pid'] for p in before}
            write_new(d/'instance.json', {'created_at_utc': utc(), 'owned_pid': owned_pid,
                                         'owned_create_time': psutil.Process(owned_pid).create_time(),
                                         'preserved_processes': before, 'api_version': mcapi.__version__})
            mc.set_visible(False)
            mc.set_variable('MessageDisplayState', 2)
            mc.load_from_file(str(mot.resolve()))
            mc.show_magnetic_context()
            for key, value in {'ProximityLossModel': 3, 'ShaftSpeed': point['speed_rpm'],
                               'RMSCurrent': point['current_A_rms'], 'PhaseAdvance': point['beta_deg']}.items():
                mc.set_variable(key, value)
            settings = {key: mc.get_variable(key) for key in [*f['solver_protocol'], 'ShaftSpeed', 'RMSCurrent',
                        'PhaseAdvance', 'Airgap', 'RotorDiameter', 'Stator_Lam_Length', 'MagnetMeshLength',
                        'StatorSlotMeshLength', 'ConductorMeshControl']}
            for key, expected in f['solver_protocol'].items():
                assert np.isclose(float(settings[key]), expected, rtol=1e-9, atol=1e-12), (key, settings[key], expected)
            for key, val in [('ShaftSpeed', point['speed_rpm']), ('RMSCurrent', point['current_A_rms']), ('PhaseAdvance', point['beta_deg'])]:
                assert abs(float(settings[key])-val) < 1e-6
            mc.set_motorlab_context()
            rt = float(mc.get_variable('Resistance_MotorLAB'))
            re = float(mc.get_variable('EndWindingResistance_Lab'))
            assert 0 < re < rt
            mc.show_magnetic_context()
            mc.save_to_file(str(mot.resolve()))
            write_new(d/'solve_start.json', {'started_at_utc': utc(), 'freeze_sha256': freeze_sha,
                                            'point': point, 'settings': settings, 'owned_pid': owned_pid,
                                            'input_mot_sha256': sha(mot), 'resistance_before': [rt,re]})
            print(utc(), 'SOLVE', point['id'], 'PID', owned_pid, flush=True)
            solve_start = time.perf_counter()
            mc.do_magnetic_calculation()
            solve_seconds = time.perf_counter()-solve_start
            per_turn = mc.get_variable('ACLoss_FEA_OnLoad_PerTurn')
            total = float(mc.get_variable('ACLoss_FEA_OnLoad_Total'))
            mc.set_motorlab_context()
            rt_after = float(mc.get_variable('Resistance_MotorLAB'))
            re_after = float(mc.get_variable('EndWindingResistance_Lab'))
            np.testing.assert_allclose([rt_after,re_after], [rt,re], rtol=1e-9, atol=1e-12)
            mc.show_magnetic_context()
            # Raw results are recorded before scientific validation, including failures.
            write_new(d/'raw_outputs.json', {'read_at_utc': utc(), 'per_turn': per_turn,
                                             'reported_total_W': total, 'resistance_after': [rt_after,re_after],
                                             'solver_seconds': solve_seconds})
            loss, error = loss_record(per_turn, total, rt_after, re_after, point['current_A_rms'])
            assert not error, error
            mc.save_to_file(str(mot.resolve()))
            exports = mot.with_suffix('')/'FEResultsData'
            assert exports.is_dir() and any(exports.iterdir()), 'Missing raw solver outputs'
            files = [{'path': str(p.relative_to(d)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
                     for p in sorted(exports.rglob('*')) if p.is_file()]
            truth = loss['truth_ac_excess_kW']
            delta = point['prediction_kW']-truth
            result = {'status': 'complete', 'completed_at_utc': utc(), 'freeze_sha256': freeze_sha,
                      'point': point, 'loss': loss, 'error_W': delta*1000,
                      'relative_error_pct': delta/truth*100, 'solver_seconds': solve_seconds,
                      'elapsed_seconds': time.perf_counter()-start, 'raw_files': files}
            write_new(d/'result.json', result)
            print(utc(), 'DONE', point['id'], 'truth_kW', truth, 'error_pct', delta/truth*100, flush=True)
        except Exception:
            error = traceback.format_exc()
            write_new(d/'error.json', {'failed_at_utc': utc(), 'owned_pid': owned_pid, 'error': error})
            print(error, flush=True)
            return 2
        finally:
            if mc is not None and owned_pid is not None and owned_pid not in {p['pid'] for p in before}:
                try:
                    mc.quit()
                except Exception as exc:
                    write_new(d/'quit_error.json', {'error': str(exc), 'owned_pid': owned_pid})
    assert sha(a.freeze) == freeze_sha
    for source in f['mot_sources'].values():
        assert sha(source['path']) == source['sha256']
    write_new(a.out/'campaign_complete.json', {'completed_at_utc': utc(), 'freeze_sha256': freeze_sha,
                                               'n_complete': 4, 'remaining_motorcad_processes': inventory()})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
