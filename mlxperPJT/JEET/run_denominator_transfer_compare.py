# -*- coding: utf-8 -*-
"""Three denominators for eq. (8), under the numerator transfer rule.

The transfer now carries P_TS alone and divides by the variant's own
hybrid, so the denominator is a free choice. This scores the adopted
27-point SC plan with three of them:

  hybrid   the 1-D single-kernel hybrid analytical-FEA of Section 2,
           as deposited (the manuscript's denominator);
  fullG2   the element-resolved <B^2> G2' proximity term plus the
           skin excess, from the deposited line-sampled sweep;
  translim the line-sampled P24 cuboid-6 kernel with the transition
           cap, plus skin excess (the open implementation of Appendix B).

Each swap keeps everything else -- plan, seed, placement, donor -- and
only the AF the variant is fitted to changes, so the wMAE differences
are the denominator's alone. The donor keeps its own denominator in all
three, since P_TS, not AF, is what crosses over.

    python run_denominator_transfer_compare.py
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from dataclasses import replace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'tools')))

from jeet_acloss_rbf.pipeline import AcLossPipeline          # noqa: E402
from jeet_acloss_rbf.AcLossDataset import AcLossDataset      # noqa: E402
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder  # noqa: E402

E10 = os.environ.get('JEET_DATA_ROOT', os.path.join(HERE, 'map_exports', 'e10'))
SRC = os.path.join(E10, 'SC', 'line_sampled_hybrid_SC_80C.json')
SPEEDS = (2.0, 4.0, 8.0, 16.0)

DENOMS = {
    'hybrid': None,
    'fullG2': lambda r: r['full_G2_solid'] + r['skin_excess_W'],
    'translim': lambda r: r['line_msq_P24c6_translim'] + r['skin_excess_W'],
}


def swapped_dataset(ds, lut):
    pts = []
    for p in ds.points:
        key = (round(p.speed_rpm), round(p.current_rms, 1),
               round(p.phase_deg, 1))
        h = lut.get(key)
        if h is None or h <= 0:
            continue
        pts.append(replace(p, hybrid_ac_kW=h, AF=p.fea_ac_kW / h))
    return AcLossDataset(pts)


def per_speed(ds, m):
    pred = np.asarray(m.predict(ds.speeds_k * 1000.0, ds.irms_arr,
                                ds.phase_arr), float) * ds.h_ac_arr
    out = {}
    for s in SPEEDS:
        sel = (np.abs(ds.speeds_k - s) < 0.1) & (ds.irms_arr > 1.0)
        f = ds.f_ac_arr[sel]
        out[f'{s:g}k'] = float(100 * np.abs(pred[sel] - f).sum() / f.sum())
    return out


def score(pl, ds, scale='SC'):
    cfg, plan = pl.cfg, pl.cfg['plan'][scale]
    with contextlib.redirect_stdout(io.StringIO()):
        m = RbfModelBuilder.build_separable_rbf_transfer(
            ds, pl.build_donor(), cfg['k_r'][scale],
            plan['n_base'], plan['n_spd'], plan['seed'],
            base_speed=cfg['base_speed'],
            n_probe_transfer=cfg['n_probe_transfer'],
            exponent=cfg['exponent'], placement='structured',
            donor_dataset=pl.load_dataset(cfg['donor_scale']))
    pred = np.asarray(m.predict(ds.speeds_k * 1000.0, ds.irms_arr,
                                ds.phase_arr), float) * ds.h_ac_arr
    loaded = ds.irms_arr > 1.0
    e = np.abs(pred - ds.f_ac_arr) / (ds.f_ac_arr + 1e-12)
    wmae = 100 * np.sum(np.abs(pred - ds.f_ac_arr)[loaded]) \
        / np.sum(ds.f_ac_arr[loaded])
    unc = 100 * np.sum(np.abs(ds.h_ac_arr - ds.f_ac_arr)[loaded]) \
        / np.sum(ds.f_ac_arr[loaded])
    q = [float(np.polyval(m.q_coeffs, s)) for s in (2.0, 4.0, 8.0)]
    return {'wmae_pct': float(wmae), 'mae_pct': float(100 * e[loaded].mean()),
            'uncorrected_wmae_pct': float(unc), 'per_speed': per_speed(ds, m),
            'p_exponent': dict(zip(('2k', '4k', '8k'), q)), 'n': int(len(ds))}


def main():
    rows = json.load(io.open(SRC, encoding='utf-8'))['rows']
    pl = AcLossPipeline()
    with contextlib.redirect_stdout(io.StringIO()):
        base = pl.load_dataset('SC')
    print(f'SC, adopted plan, transfer rule {RbfModelBuilder.TRANSFER_RULE}')
    print(f'\n   {"denominator":12s} {"n":>4s} {"uncorr.":>8s} {"wMAE":>7s} '
          f'{"MAE":>7s}   ' + '  '.join(f'{s:g}k' for s in SPEEDS)
          + '   p(2k) p(4k) p(8k)')
    out = {}
    for name, fn in DENOMS.items():
        if fn is None:
            ds = base
        else:
            lut = {}
            for r in rows:
                try:
                    v = fn(r)
                except (KeyError, TypeError):
                    continue
                if v is not None:
                    lut[(round(r['speed_rpm']), round(r['current_A'], 1),
                         round(r['phase_deg'], 1))] = v / 1e3
            ds = swapped_dataset(base, lut)
        s = score(pl, ds)
        out[name] = s
        ps = s['per_speed']
        print(f'   {name:12s} {s["n"]:4d} {s["uncorrected_wmae_pct"]:7.1f}% '
              f'{s["wmae_pct"]:6.2f}% {s["mae_pct"]:6.2f}%   '
              + '  '.join(f'{ps[f"{sp:g}k"]:5.2f}' for sp in SPEEDS)
              + '   ' + ' '.join(f'{v:5.2f}' for v in s['p_exponent'].values()))
    p = os.path.join(HERE, 'checks', 'denominator_transfer_compare.json')
    json.dump(out, io.open(p, 'w', encoding='utf-8'), indent=2)
    print('\n   wrote', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
