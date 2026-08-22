# -*- coding: utf-8 -*-
"""Headline numbers under the two transfer rules, side by side.

Records wMAE / MAE of the adopted plan for every machine, the per-speed
wMAE, and the speed exponents, so the manuscript numbers can be compared
before and after the transfer rule changes.

    python run_transfer_mode_compare.py --tag before
    python run_transfer_mode_compare.py --tag after
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'tools')))

from jeet_acloss_rbf.pipeline import AcLossPipeline          # noqa: E402
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder  # noqa: E402

SPEEDS = (2.0, 4.0, 8.0, 16.0)


def per_speed_wmae(ds, m):
    out = {}
    pred = np.asarray(m.predict(ds.speeds_k * 1000.0, ds.irms_arr,
                                ds.phase_arr), float) * ds.h_ac_arr
    for s in SPEEDS:
        sel = (np.abs(ds.speeds_k - s) < 0.1) & (ds.irms_arr > 1.0)
        if not sel.any():
            continue
        f = ds.f_ac_arr[sel]
        e = np.abs(pred[sel] - f)
        out[f'{s:g}k'] = float(100 * e.sum() / f.sum())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    a = ap.parse_args(argv)

    pl = AcLossPipeline()
    rep = {'tag': a.tag, 'transfer_rule': getattr(
        RbfModelBuilder, 'TRANSFER_RULE', 'ratio')}
    print(f'[{a.tag}] transfer rule: {rep["transfer_rule"]}')
    print(f'\n   {"machine":8s} {"mode":9s} {"own":>4s} {"wMAE":>7s} {"MAE":>7s}  '
          + '  '.join(f'{s:g}k' for s in SPEEDS) + '   p(2k) p(4k) p(8k)')
    for scale in ('Ref', 'HalfSC', 'SC'):
        with contextlib.redirect_stdout(io.StringIO()):
            ds = pl.load_dataset(scale)
            m = pl.build_model(scale)
            met = pl.metrics(scale)
        ps = per_speed_wmae(ds, m)
        q = [float(np.polyval(m.q_coeffs, s)) for s in (2.0, 4.0, 8.0)] \
            if m.q_coeffs is not None else [1.0] * 3
        rep[scale] = {'wmae_pct': met['wmae_pct'], 'mae_pct': met['mae_pct'],
                      'hybrid_wmae_pct': met['hybrid_wmae_pct'],
                      'n_own': met['n_own_samples'], 'per_speed': ps,
                      'p_exponent': dict(zip(('2k', '4k', '8k'), q))}
        print(f'   {scale:8s} {pl.cfg["plan"][scale]["mode"]:9s} '
              f'{int(met["n_own_samples"]):4d} {met["wmae_pct"]:6.2f}% '
              f'{met["mae_pct"]:6.2f}%  '
              + '  '.join(f'{ps.get(f"{s:g}k", float("nan")):5.2f}' for s in SPEEDS)
              + '   ' + ' '.join(f'{v:5.2f}' for v in q))

    out = os.path.join(HERE, 'checks', f'transfer_mode_{a.tag}.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rep, io.open(out, 'w', encoding='utf-8'), indent=2)
    print('\n   wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
