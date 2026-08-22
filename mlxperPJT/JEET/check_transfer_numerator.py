# -*- coding: utf-8 -*-
"""Transfer the ratio, or transfer the loss? Scored against the variant's own truth.

The similarity transfer carries AF itself: AF_var(w, I, b) = AF_ref(k_r^2 w,
I/k_r, b). The alternative is to carry the numerator and divide by the
variant's own hybrid, AF_var = k_a P_TS,ref / P_hyb,var.

The factor is k_a, not k_r^4 k_a. The k_r^4 of the scaling law is for the
same frequency and current density; at the similarity-corresponding point
the current density is divided by k_r and the frequency by k_r^2, the loss
density falls as 1/k_r^2, the volume grows as k_r^2 k_a, and the total
scales as k_a. With k_a = 1 the loss maps across unchanged, which is what
Section 5.2 reports as absolute Full-FEA loss agreeing within 1.6 percent.

The two differ by exactly one thing, whether the hybrid denominator is
similar. If the variant's hybrid were itself computed from the scaled
reference field, numerator and denominator would carry the same factor and
the two routes would be algebraically identical. They are not: the
deposited hybrid is Motor-CAD's own run on the variant, so the routes
differ by however far that run departs from similarity.

Nothing has to be re-solved to decide this. The current grids map onto
each other exactly -- SC 2 and 4 kRPM against Ref 8 and 16 kRPM, SC
currents at twice Ref's -- and the exhaustive sweep holds the variant's
own Full-FEA at every one of those points, so both routes can be scored
against the truth they are trying to predict.

    python check_transfer_numerator.py
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'map_exports', 'e10')
JSON = {'Ref': r'Ref/JEET_ACLoss_Ref_Map_Summary.json',
        'HalfSC': r'HalfSC/JEET_ACLoss_HalfSC_Map_Summary.json',
        'SC': r'SC/JEET_ACLoss_SC_Map_Summary.json'}


def load(scale, root):
    d = json.load(io.open(os.path.join(root, JSON[scale]), encoding='utf-8'))
    # 두 형태가 섞여 있다: Ref 는 레코드 배열, 변형체는 {_meta, records}.
    recs = d if isinstance(d, list) else d['records']
    hyb, fea = {}, {}
    for r in recs:
        key = (round(r['speed']), round(r['current'], 2), round(r['phase'], 1))
        if r['mode'] == 'Hybrid':
            hyb[key] = float(r['hybrid_total_kW'])
        else:
            fea[key] = float(r.get('ts_ac_active_only_kW',
                                   r.get('fea_total_ac_kW', np.nan)))
    return hyb, fea


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=DATA)
    ap.add_argument('--variant', default='SC', choices=('SC', 'HalfSC'))
    ap.add_argument('--k-a', type=float, default=1.0)
    ap.add_argument('--json')
    a = ap.parse_args(argv)

    k_r = {'SC': 2.0, 'HalfSC': 1.5}[a.variant]
    fac = a.k_a                         # 상사 대응점에서는 손실이 k_a 배
    hyb_r, fea_r = load('Ref', a.root)
    hyb_v, fea_v = load(a.variant, a.root)

    print(f'{a.variant}: k_r = {k_r}, k_a = {a.k_a}, '
          f'loss factor at the similarity point = k_a = {fac:g}')
    rows = []
    for (spd, cur, ph), Pv in sorted(fea_v.items()):
        if cur < 1.0:                       # 무부하는 AF 가 뜻이 없다
            continue
        donor = (round(spd * k_r ** 2), round(cur / k_r, 2), ph)
        # 격자가 맞물리는지 반올림 오차 안에서 확인한다.
        cand = [k for k in fea_r
                if k[0] == donor[0] and abs(k[1] - donor[1]) < 0.2
                and abs(k[2] - donor[2]) < 0.1]
        if not cand or (spd, cur, ph) not in hyb_v:
            continue
        dk = cand[0]
        if dk not in hyb_r:
            continue
        Pr, Hr, Hv = fea_r[dk], hyb_r[dk], hyb_v[(spd, cur, ph)]
        if min(Pv, Pr, Hr, Hv) <= 0:
            continue
        rows.append({
            'speed': spd, 'current': cur, 'phase': ph,
            'donor_speed': dk[0], 'donor_current': dk[1],
            'af_true': Pv / Hv,             # 변형체 자신의 진리
            'af_A': Pr / Hr,                # 비를 옮긴다
            'af_B1': fac * Pr / Hv,         # 분자만 옮기고 자기 분모로 나눈다
            'num_err_pct': 100 * (Pv / (fac * Pr) - 1),
            'den_err_pct': 100 * (Hv / (fac * Hr) - 1),
            'watt': Pv,
        })
    if not rows:
        print('no paired points')
        return 1

    n = np.array([r['num_err_pct'] for r in rows])
    d = np.array([r['den_err_pct'] for r in rows])
    t = np.array([r['af_true'] for r in rows])
    A = np.array([r['af_A'] for r in rows])
    B = np.array([r['af_B1'] for r in rows])
    w = np.array([r['watt'] for r in rows])

    print(f'\n   {len(rows)} paired points at '
          f'{sorted(set(r["speed"] for r in rows))} RPM\n')
    print('   similarity of each part, variant against scaled donor')
    print(f'      numerator  P_TS   mean {n.mean():+6.2f} %   '
          f'rms {np.sqrt((n**2).mean()):5.2f} %   max |{np.abs(n).max():.2f}| %')
    print(f'      denominator P_hyb  mean {d.mean():+6.2f} %   '
          f'rms {np.sqrt((d**2).mean()):5.2f} %   max |{np.abs(d).max():.2f}| %')

    print('\n   B2, numerator and denominator both from the scaled donor, is')
    print('   A by algebra, the two factors cancelling. What separates it')
    print('   from B1 is the denominator row above.')

    print('\n   AF error against the variant\'s own truth')
    for name, v in (('A / B2  transfer the ratio', A),
                    ('B1      transfer the numerator', B)):
        e = 100 * (v / t - 1)
        we = 100 * np.sum(np.abs(v - t) * w) / np.sum(t * w)
        print(f'      {name:26s} mean {e.mean():+6.2f} %   '
              f'rms {np.sqrt((e**2).mean()):5.2f} %   '
              f'watt-weighted MAE {we:5.2f} %')

    if a.json:
        p = a.json if os.path.isabs(a.json) else os.path.join(HERE, a.json)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(rows, io.open(p, 'w', encoding='utf-8'), indent=2)
        print('\n   wrote', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
