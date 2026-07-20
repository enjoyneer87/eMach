"""HalfSC 데이터셋을 SC 구조로 정규화.

목표: 정격 690 A의 균등 5티어 [0.1, 172.5, 345, 517.5, 690] × 4속도 × 6위상
      × (Hybrid, FullFEA) = 240 records, SC와 동일 구조.

동작: 목표 격자의 각 점 중 아직 없는 것만 Motor-CAD로 해석해 HalfSC 요약
      JSON에 증분 append (crash-safe). 목표 밖 기존 티어(115.1/230/460)는
      건드리지 않음 --- 정규화 완료 후 별도 스크립트로 분리 보관.

참고: run_halfsc_690_tier.py의 검증된 패턴을 일반화.
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

RATED = 690.0
TARGET_CURRENTS = [0.1, round(0.25 * RATED, 1), round(0.5 * RATED, 1),
                   round(0.75 * RATED, 1), RATED]     # 0.1/172.5/345/517.5/690
SPEEDS = [2000, 4000, 8000, 16000]
PHASES = [0.0, 18.0, 36.0, 54.0, 72.0, 90.0]
TAG = 'normalize_SCstruct'


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
    have = {(int(r['speed']), round(r['current'], 1),
             round(r['phase'], 1), r['mode']) for r in recs}

    todo = []
    for cur in TARGET_CURRENTS:
        for spd in SPEEDS:
            for ph in PHASES:
                for mode in ('Hybrid', 'FullFEA'):
                    hit = any(s == spd and abs(c - cur) < 1.5
                              and abs(p - ph) < 0.6 and m == mode
                              for (s, c, p, m) in have)
                    if not hit:
                        todo.append((cur, spd, ph, mode))
    print(f'target tiers {TARGET_CURRENTS}')
    print(f'points to run: {len(todo)}', flush=True)
    if not todo:
        print('nothing to do')
        return

    ts0 = datetime.now().isoformat(timespec='seconds')
    bak = JSON_PATH.with_suffix(f".bak_{ts0.replace(':', '-')}_prenorm.json")
    shutil.copy2(JSON_PATH, bak)
    print('backup:', bak.name)

    mc = pymotorcad.MotorCAD(enable_success_variable=False)
    try:
        mc.set_variable('MessageDisplayState', 2)
    except Exception:
        pass
    mc.load_from_file(MOT_PATH)
    print('loaded:', MOT_PATH, flush=True)

    try:
        mc.set_motorlab_context()
        r_total = float(mc.get_variable('Resistance_MotorLAB'))
        r_end = float(mc.get_variable('EndWindingResistance_Lab'))
        r_active = r_total - r_end
        mc.show_magnetic_context()
    except Exception as exc:
        print('[warn] R split failed:', exc)
        r_active = r_end = 0.0
    print(f'R_active={r_active:.6f}  R_end={r_end:.6f}', flush=True)

    for k, (cur, spd, ph, mode) in enumerate(todo, 1):
        print(f'--- [{k}/{len(todo)}] {spd} rpm / {cur} A / {ph} deg '
              f'({mode})', flush=True)
        mc.set_variable('ProximityLossModel', 1 if mode == 'Hybrid' else 3)
        mc.set_variable('ShaftSpeed', spd)
        mc.set_variable('RMSCurrent', cur)
        mc.set_variable('PhaseAdvance', ph)
        mc.do_magnetic_calculation()

        ts = datetime.now().isoformat(timespec='seconds')
        base = dict(speed=spd, current=cur, phase=ph, rerun_ts=ts,
                    rerun_reason=TAG,
                    backup_dir=(r'D:\KDH\simVary\e10_6TSweep\SLFEA_Half'
                                r'\ACLossCalcExport_Map'
                                f'\\{mode}_Speed_{spd:.0f}RPM_'
                                f'{cur}A_{ph}deg_{TAG}'))
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
            dc_a = calc_dc_loss_kw(r_active, cur)
            dc_e = calc_dc_loss_kw(r_end, cur)
            rec = dict(base, mode='FullFEA', proximity_model=3,
                       fea_per_turn_raw=per, fea_per_turn_sum_kW=per_sum,
                       fea_total_ac_kW=total, ts_dc_active_kW=dc_a,
                       ts_dc_end_kW=dc_e, ts_ac_active_only_kW=per_sum - dc_a)
        recs.append(rec)
        if isinstance(db, dict):
            db['records'] = recs
        save_db(db)
        key = ('hybrid_total_kW' if mode == 'Hybrid'
               else 'ts_ac_active_only_kW')
        print(f'    saved ({key} = {rec.get(key, 0):.3f} kW)', flush=True)

    mc.quit()
    print('done - HalfSC normalization complete')


if __name__ == '__main__':
    main()
