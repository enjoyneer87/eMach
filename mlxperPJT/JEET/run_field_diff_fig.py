# -*- coding: utf-8 -*-
"""Section 5.2 figure: the similarity transfer as a field.

Fig 9 shows the circuit-level comparison directly -- the scaled curve
laid over the directly solved one. The field level had no counterpart,
and Fig 3 is two sections away and quantifies nothing. This draws the
same comparison for the field at the rated similarity pair: Ref at
16 kRPM and 460 A against SC at 4 kRPM and 920 A, the pair Fig 3
already uses, one row per solver level.

The snapshot is block 65. Sixty-four steps of 0.703125 degrees is one
pole pitch and half an electrical period, so folding it back by the pole
pitch puts the rotor exactly where Fig 3 has it while the eddy currents
stay fully developed -- which the static first block cannot offer.

    python run_field_diff_fig.py

The numbers the caption quotes come from the same call, and the
interpolation-free version of them is in check_region_field_transfer.py.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'tools')))

from jeet_acloss_rbf.repro_env import fig_dir                    # noqa: E402
from jeet_acloss_rbf.manuscript_figs import plot_field_diff_panels  # noqa

_DATA = os.environ.get('JEET_DATA_ROOT',
                       os.path.join(HERE, 'map_exports', 'e10'))
FIELDS = os.path.join(_DATA, 'fields')

# (행 이름, Ref npz, SC npz, k_r) — 행 = 솔버 수준
ROWS = [
    ('MS-FEA', 'fieldvec_MS_Ref.npz', 'fieldvec_MS_SC.npz', 2.0),
    ('Full-FEA', 'fieldvec_Full_Ref.npz', 'fieldvec_Full_SC.npz', 2.0),
]


def main() -> int:
    rows = []
    for label, ref, sc, k_r in ROWS:
        pr, ps = os.path.join(FIELDS, ref), os.path.join(FIELDS, sc)
        for p in (pr, ps):
            if not os.path.exists(p):
                print(f'[오류] 필드 데이터 없음: {p}')
                return 1
        rows.append((label, pr, ps, k_r))

    out = os.path.join(fig_dir(), 'similarity_field_error.pdf')
    stats = plot_field_diff_panels(rows, out)

    js = os.path.join(HERE, 'checks', 'similarity_field_error.json')
    os.makedirs(os.path.dirname(js), exist_ok=True)
    with open(js, 'w', encoding='utf-8') as fh:
        json.dump(stats, fh, indent=2)
    print(f'저장: {out}  ({os.path.getsize(out) / 1024:.0f} KB)')
    print(f'수치: {js}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
