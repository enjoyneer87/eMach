# -*- coding: utf-8 -*-
"""The spread exponent p(omega), per speed, for each machine.

The last column of the AF transfer figure draws lines of slope
p(omega) = polyval(q_coeffs, speed). Reading a slope off the rendered
figure is good enough to notice that the variant's lines fan out and the
donor's do not, but not to write a number into the manuscript. This
rebuilds the adopted plans and prints the exponents the figure draws.

At the anchor speed p is 1 by construction rather than by fit, since
kappa is identified there: _fit_speed_scaling seeds its lists with
(base_speed, f=1, p=1). Any statement about the anchor slope has to say
that, not present it as a measurement.

    python check_speed_exponent.py
"""
from __future__ import annotations

import contextlib
import io
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'tools')))

from jeet_acloss_rbf.pipeline import AcLossPipeline          # noqa: E402
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder  # noqa: E402

SPEEDS = (2.0, 4.0, 8.0, 16.0)
ROWS = ('Ref', 'HalfSC', 'SC')
# 상사 사상: 기증자 속도 w 는 변형체에서 w / k_r^2 에 대응한다.
K_R = {'Ref': 1.0, 'HalfSC': 1.5, 'SC': 2.0}


def build(pl, scale):
    """run_af_transfer_fig.build 와 같은 경로로 채택 플랜을 세운다."""
    cfg = pl.cfg
    plan = cfg['plan'][scale]
    with contextlib.redirect_stdout(io.StringIO()):
        ds = pl.load_dataset(scale)
        if plan['mode'] == 'own':
            ip = RbfModelBuilder.plan_sampling_indices(
                ds, n_base=plan['n_base'], n_spd=plan['n_spd'],
                base_speed=cfg['base_speed'], placement='structured', seed=0)
            m = RbfModelBuilder.build_separable_rbf(
                ds, base_speed=cfg['base_speed'], exponent=cfg['exponent'],
                index_plan=ip)
        else:
            m = pl.build_model(scale)
    return ds, m


def main():
    pl = AcLossPipeline()
    base = pl.cfg['base_speed']
    print(f'anchor speed {base:g} kRPM, exponent mode {pl.cfg["exponent"]}')
    print(f'\n   {"machine":8s} {"k_r":>4s}  ' +
          '  '.join(f'{s:g} kRPM' for s in SPEEDS))
    out = {}
    for scale in ROWS:
        try:
            ds, m = build(pl, scale)
        except Exception as e:                                  # noqa: BLE001
            print(f'   {scale:8s} build failed: {e}')
            continue
        if m.q_coeffs is None:
            print(f'   {scale:8s} scalar mode, p = 1 at every speed')
            continue
        ps = [float(np.polyval(m.q_coeffs, s)) for s in SPEEDS]
        out[scale] = ps
        mark = ['*' if abs(s - base) < 1e-9 else ' ' for s in SPEEDS]
        print(f'   {scale:8s} {K_R[scale]:4.1f}  ' +
              '  '.join(f'{p:7.3f}{mk}' for p, mk in zip(ps, mark)))
    print('\n   * anchor speed: p is fixed at 1 by construction, not fitted.')

    if 'Ref' in out and 'SC' in out:
        r, s = out['Ref'], out['SC']
        print(f'\n   spread across 2 to 16 kRPM: '
              f'Ref {max(r)-min(r):+.3f}, SC {max(s)-min(s):+.3f}')
        print('   The donor keeps one exponent across its band; the variant '
              'does not, which is why it re-anchors in house.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
