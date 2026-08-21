# -*- coding: utf-8 -*-
"""The similarity transfer inside the winding, with nothing in between.

Comparing fields solved on two meshes normally needs a transfer -- an
interpolation, an L2 projection onto a common refinement, a mortar
coupling -- and each puts its own error into the answer. Inside the
winding of this family none is needed. Motor-CAD lays the same
structured mesh in every conductor regardless of machine size, so the
similarity map carries the reference conductor mesh onto the variant's
element for element: 64 elements in both, and after scaling by k_r the
centroids land within a few percent of one element of each other.

The two solutions can therefore be subtracted directly. This script
does that and reports the residual, which is the transfer error of the
scaling law itself with no numerical transfer error underneath it.

The pairing is verified rather than assumed: a run that cannot pair the
elements one-to-one says so and stops, because the whole point is that
nothing was interpolated.

    python check_winding_transfer_exact.py --level Full
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS_DEFAULT = os.path.join(HERE, 'map_exports', 'e10', 'fields')


def load(fields, tag):
    d = np.load(os.path.join(fields, f'fieldvec_{tag}.npz'))
    names = {int(c): str(t) for c, t in zip(d['name_codes'], d['name_texts'])}
    return d, names


def pair_conductors(fields, level, k_r, tol_frac=0.25):
    """One-to-one element pairing per conductor, or an explanation why not."""
    from scipy.spatial import cKDTree
    dr, nr = load(fields, f'{level}_Ref')
    ds, ns = load(fields, f'{level}_SC')
    by_name = {ns[int(c)]: int(c) for c in ds['conductor_codes']}
    out, failed = [], []
    for c in sorted(int(x) for x in dr['conductor_codes']):
        nm = nr[c]
        if nm not in by_name:
            failed.append((nm, 'no counterpart by name'))
            continue
        mr = dr['reg'].astype(int) == c
        ms = ds['reg'].astype(int) == by_name[nm]
        xr = np.column_stack([dr['x_mm'][mr], dr['y_mm'][mr]]) * k_r
        xs = np.column_stack([ds['x_mm'][ms], ds['y_mm'][ms]])
        if mr.sum() != ms.sum():
            failed.append((nm, f'{mr.sum()} vs {ms.sum()} elements'))
            continue
        dist, idx = cKDTree(xs).query(xr)
        h = float(np.sqrt(ds['area_mm2'][ms].mean()))
        if len(np.unique(idx)) != len(idx):
            failed.append((nm, 'pairing not one-to-one'))
            continue
        if dist.max() > tol_frac * h:
            failed.append((nm, f'residual {dist.max():.4f} mm exceeds '
                               f'{tol_frac:.2f} of an element ({h:.4f} mm)'))
            continue
        out.append({
            'name': nm, 'n': int(mr.sum()),
            'residual_mm': float(dist.max()), 'elem_mm': h,
            # 상사 규칙: B 불변, 면적은 k_r^2.
            'bx_ref': dr['bx_T'][mr], 'by_ref': dr['by_T'][mr],
            'bx_sc': ds['bx_T'][ms][idx], 'by_sc': ds['by_T'][ms][idx],
            'area_mm2': ds['area_mm2'][ms][idx],
        })
    return out, failed


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--fields', default=FIELDS_DEFAULT)
    ap.add_argument('--level', default='Full', choices=('MS', 'Full'))
    ap.add_argument('--k-r', type=float, default=2.0)
    ap.add_argument('--json')
    a = ap.parse_args(argv)

    paired, failed = pair_conductors(a.fields, a.level, a.k_r)
    print(f'{a.level}-FEA, k_r = {a.k_r}: '
          f'{len(paired)} conductors paired element for element, '
          f'{len(failed)} not')
    for nm, why in failed[:6]:
        print(f'   [unpaired] {nm}: {why}')
    if not paired:
        print('\nNothing to report without a pairing. The meshes of this '
              'level do not correspond, so any number here would be a '
              'transfer artefact -- use check_region_field_transfer.py, '
              'whose region integrals need no pairing.')
        return 2
    if failed:
        print('   (unpaired conductors are left out rather than '
              'interpolated)')

    rows = []
    for p in paired:
        dbx = p['bx_sc'] - p['bx_ref']
        dby = p['by_sc'] - p['by_ref']
        w = p['area_mm2']
        d2 = np.dot(dbx ** 2 + dby ** 2, w) / w.sum()
        b2 = np.dot(p['bx_ref'] ** 2 + p['by_ref'] ** 2, w) / w.sum()
        rows.append({'name': p['name'], 'n': p['n'],
                     'residual_frac_elem': p['residual_mm'] / p['elem_mm'],
                     'dB_rms_T': float(np.sqrt(d2)),
                     'B_rms_T': float(np.sqrt(b2)),
                     'dB_L2_pct': float(100 * np.sqrt(d2 / b2)),
                     'dB_max_T': float(np.hypot(dbx, dby).max())})

    L2 = np.array([r['dB_L2_pct'] for r in rows])
    d2 = np.array([r['dB_rms_T'] ** 2 for r in rows])
    b2 = np.array([r['B_rms_T'] ** 2 for r in rows])
    res = np.array([r['residual_frac_elem'] for r in rows])
    print(f'\n   {"conductor":<16s} {"n":>4s} {"|B| rms":>9s} '
          f'{"|dB| rms":>9s} {"L2 %":>7s} {"|dB| max":>9s}')
    for r in sorted(rows, key=lambda r: -r['dB_L2_pct'])[:8]:
        print(f'   {r["name"]:<16s} {r["n"]:4d} {r["B_rms_T"]:9.4f} '
              f'{r["dB_rms_T"]:9.5f} {r["dB_L2_pct"]:7.3f} '
              f'{r["dB_max_T"]:9.5f}')
    print(f'   ... {len(rows)} conductors total')
    print(f'\n   pairing residual: max {res.max()*100:.1f} % of one element')
    print(f'   winding as a whole  ||dB||/||B|| '
          f'{100*np.sqrt(d2.sum()/b2.sum()):.3f} %')
    print(f'   per conductor       mean {L2.mean():.3f} %, '
          f'median {np.median(L2):.3f} %, max {L2.max():.3f} %')
    print('\n   No interpolation, no projection, no common grid: the two '
          'solutions were subtracted where both meshes place the same '
          'element.')

    if a.json:
        p = a.json if os.path.isabs(a.json) else os.path.join(HERE, a.json)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as fh:
            json.dump({'level': a.level, 'k_r': a.k_r,
                       'winding_L2_pct': float(100*np.sqrt(d2.sum()/b2.sum())),
                       'conductors': rows}, fh, indent=2)
        print('wrote', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
