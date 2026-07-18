"""HalfSC 690 A (=1.5x460, B-preserving rated) tier — missing sweep.

Runs Hybrid + FullFEA at every (speed, phase) combo that the existing
460.0 A tier has, appends records to the HalfSC map summary JSON with
the same schema as run_single_fea_point.py, saving incrementally after
each point (crash-safe). Expected wall time: overnight (22 combos x
(MS-hybrid + TS)).
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EMACH_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(EMACH_ROOT))

MOT_PATH = r'D:\KangDH\Thesis\e10\SLFEA_Half\e10Turn6V261SLFEA_Half.mot'
JSON_PATH = (SCRIPT_DIR / 'map_exports' / 'e10' / 'HalfSC'
             / 'JEET_ACLoss_HalfSC_Map_Summary.json')
CURRENT = 690.0
TAG = '690tier'


def load_db():
    with open(JSON_PATH, encoding='utf-8') as fh:
        return json.load(fh)


def save_db(db):
    with open(JSON_PATH, 'w', encoding='utf-8') as fh:
        json.dump(db, fh, indent=2, ensure_ascii=False)


def main() -> None:
    import ansys.motorcad.core as pymotorcad
    from tools.motorCAD.pyMCAD import calc_dc_loss_kw

    db = load_db()
    recs = db if isinstance(db, list) else db.get('records', [])
    combos = sorted({(r['speed'], r['phase']) for r in recs
                     if abs(r.get('current', 0) - 460.0) < 0.5})
    done = {(r['speed'], r['phase'], r['mode']) for r in recs
            if abs(r.get('current', 0) - CURRENT) < 0.5}
    print(f'combos from 460A tier: {len(combos)}, already done: {len(done)}')

    ts0 = datetime.now().isoformat(timespec='seconds')
    bak = JSON_PATH.with_suffix(f".bak_{ts0.replace(':', '-')}_690pre.json")
    shutil.copy2(JSON_PATH, bak)
    print('backup:', bak.name)

    mc = pymotorcad.MotorCAD(enable_success_variable=False)
    try:
        mc.set_variable('MessageDisplayState', 2)
    except Exception:
        pass
    mc.load_from_file(MOT_PATH)
    print('loaded:', MOT_PATH, flush=True)

    # DC split resistances (once)
    try:
        mc.set_motorlab_context()
        r_total = float(mc.get_variable('Resistance_MotorLAB'))
        r_end = float(mc.get_variable('EndWindingResistance_Lab'))
        r_active = r_total - r_end
        mc.show_magnetic_context()
    except Exception as exc:
        print('[warn] R split failed:', exc)
        r_active = r_end = 0.0
    print(f'R_active={r_active:.6f}  R_end={r_end:.6f}')

    for k, (spd, ph) in enumerate(combos, 1):
        for mode in ('Hybrid', 'FullFEA'):
            if (spd, ph, mode) in done:
                print(f'[skip] {spd}/{ph} {mode}')
                continue
            print(f'--- [{k}/{len(combos)}] {spd} rpm / {CURRENT} A / '
                  f'{ph} deg  ({mode})', flush=True)
            mc.set_variable('ProximityLossModel',
                            1 if mode == 'Hybrid' else 3)
            mc.set_variable('ShaftSpeed', spd)
            mc.set_variable('RMSCurrent', CURRENT)
            mc.set_variable('PhaseAdvance', ph)
            mc.do_magnetic_calculation()

            ts = datetime.now().isoformat(timespec='seconds')
            base = dict(speed=spd, current=CURRENT, phase=ph,
                        rerun_ts=ts, rerun_reason=TAG,
                        backup_dir=(r'D:\KDH\simVary\e10_6TSweep\SLFEA_Half'
                                    r'\ACLossCalcExport_Map'
                                    f'\\{mode}_Speed_{spd:.0f}RPM_'
                                    f'{CURRENT}A_{ph}deg_{TAG}'))
            if mode == 'Hybrid':
                rec = dict(base, mode='Hybrid', proximity_model=1,
                           hybrid_total_kW=float(mc.get_variable(
                               'ACLoss_Hybrid_Total')) / 1e3,
                           hybrid_prox_kW=float(mc.get_variable(
                               'ACLoss_Hybrid_Prox_Total')) / 1e3,
                           hybrid_skin_kW=float(mc.get_variable(
                               'ACLoss_Hybrid_SkinEffect_Total')) / 1e3)
            else:
                try:
                    per = mc.get_variable('ACLoss_FEA_OnLoad_PerTurn')
                    per_w = ([float(x) for x in per.split(':')]
                             if isinstance(per, str) else list(per))
                    per_sum = sum(per_w) / 1e3
                    total = float(mc.get_variable(
                        'ACLoss_FEA_OnLoad_Total')) / 1e3
                except Exception as exc:
                    print('  [WARN] FEA loss read fail:', exc)
                    per, per_sum, total = '', 0.0, 0.0
                dc_a = calc_dc_loss_kw(r_active, CURRENT)
                dc_e = calc_dc_loss_kw(r_end, CURRENT)
                rec = dict(base, mode='FullFEA', proximity_model=3,
                           fea_per_turn_raw=per,
                           fea_per_turn_sum_kW=per_sum,
                           fea_total_ac_kW=total,
                           ts_dc_active_kW=dc_a, ts_dc_end_kW=dc_e,
                           ts_ac_active_only_kW=per_sum - dc_a)
            recs.append(rec)
            if isinstance(db, dict):
                db['records'] = recs
            save_db(db)
            key = ('hybrid_total_kW' if mode == 'Hybrid'
                   else 'ts_ac_active_only_kW')
            print(f'    saved ({key} = {rec.get(key, 0):.3f} kW)',
                  flush=True)

    mc.quit()
    print('done - 690 A tier complete')


if __name__ == '__main__':
    main()
