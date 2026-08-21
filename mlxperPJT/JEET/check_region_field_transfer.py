# -*- coding: utf-8 -*-
"""Measure the similarity transfer error with no interpolation at all.

Comparing two fields solved on different meshes normally calls for a
mesh-to-mesh map -- consistent interpolation at the target nodes, an L2
projection onto a common refinement, an RBF or mortar coupling -- and
every one of them puts its own error into the answer. None is needed
here. SCL-M maps region onto region, the two models carry the same
regions, and the quantities the loss model consumes are region averages.
So each average is formed on its own mesh, area-weighted over that
mesh's own elements, and only the two numbers are compared.

Reported per region: the area-weighted mean field vector, the mean of
|B|^2 that the proximity term integrates, and their ratios after the
transform. B is invariant under SCL-M, so every ratio should be 1.

    python check_region_field_transfer.py --level Full
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_meshed_geometry import AIRGAP_RE, match  # noqa: E402

FIELDS_DEFAULT = os.path.join(HERE, 'map_exports', 'e10', 'fields')
CONDUCTOR_RE = re.compile(r'^(Turn_\d+_\d+|ArmatureSlot[A-Za-z]+\d+)$')


def region_fields(npz):
    """Area-weighted field averages per region, on that region's own mesh."""
    d = np.load(npz)
    reg = d['reg'].astype(int)
    a = d['area_mm2']
    bx, by = d['bx_T'], d['by_T']
    x, y = d['x_mm'], d['y_mm']
    names = {int(c): str(t) for c, t in zip(d['name_codes'], d['name_texts'])}
    # 공극층은 모델마다 겹 수가 달라 층끼리 짝지으면 안 된다 — 한 덩어리로.
    gap = sorted(c for c, n in names.items() if AIRGAP_RE.match(n))
    key = np.where(np.isin(reg, gap), gap[0], reg) if gap else reg
    label = {gap[0]: f'airgap ({len(gap)} layers)'} if gap else {}

    rows = {}
    for c in np.unique(key):
        m = key == c
        w = a[m]
        tot = w.sum()
        cx, cy = np.average(x[m], weights=w), np.average(y[m], weights=w)
        rows[int(c)] = {
            'name': label.get(int(c), names.get(int(c), f'reg {c}')),
            'area_mm2': float(tot),
            'r_mm': float(np.hypot(cx, cy)),
            'th_deg': float(np.degrees(np.arctan2(cy, cx))),
            'bx_T': float(np.dot(bx[m], w) / tot),
            'by_T': float(np.dot(by[m], w) / tot),
            # 근접손 항이 적분하는 양. 평균의 제곱이 아니라 제곱의 평균이다.
            'b2_T2': float(np.dot(bx[m] ** 2 + by[m] ** 2, w) / tot),
            'is_conductor': bool(CONDUCTOR_RE.match(
                names.get(int(c), ''))),
        }
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--fields', default=FIELDS_DEFAULT)
    ap.add_argument('--level', default='Full', choices=('MS', 'Full'))
    ap.add_argument('--k-r', type=float, default=2.0)
    ap.add_argument('--json')
    a = ap.parse_args(argv)

    ref_p = os.path.join(a.fields, f'fieldvec_{a.level}_Ref.npz')
    sc_p = os.path.join(a.fields, f'fieldvec_{a.level}_SC.npz')
    for p in (ref_p, sc_p):
        if not os.path.isfile(p):
            print(f'[missing] {p}')
            return 1
    ref, sc = region_fields(ref_p), region_fields(sc_p)

    rows = []
    for c, c2, A, B, _ in match(ref, sc, a.k_r):
        if B is None:
            continue
        dbx, dby = B['bx_T'] - A['bx_T'], B['by_T'] - A['by_T']
        b_ref = np.hypot(A['bx_T'], A['by_T'])
        rows.append({
            'name': A['name'], 'is_conductor': A['is_conductor'],
            'area_mm2': A['area_mm2'], 'r_mm': A['r_mm'],
            'Bbar_ref_T': float(b_ref),
            'dBbar_T': float(np.hypot(dbx, dby)),
            'dBbar_rel_pct': float(100 * np.hypot(dbx, dby) / max(b_ref, 1e-12)),
            'b2_ratio': float(B['b2_T2'] / A['b2_T2']) if A['b2_T2'] else np.nan,
            'b2_err_pct': float(100 * (B['b2_T2'] / A['b2_T2'] - 1))
            if A['b2_T2'] else np.nan,
        })

    print(f'{a.level}-FEA   k_r = {a.k_r}   {len(rows)} matched regions'
          f'   (no interpolation: each average taken on its own mesh)')
    print(f'\n   {"region":<22s} {"area mm2":>10s} {"|B| ref":>8s}'
          f' {"|dB|":>8s} {"rel %":>7s} {"<B2> ratio":>11s} {"err %":>7s}')
    for r in sorted(rows, key=lambda r: -abs(r['dBbar_rel_pct'])):
        print(f'   {r["name"][:22]:<22s} {r["area_mm2"]:10.4f} '
              f'{r["Bbar_ref_T"]:8.4f} {r["dBbar_T"]:8.5f} '
              f'{r["dBbar_rel_pct"]:7.3f} {r["b2_ratio"]:11.5f} '
              f'{r["b2_err_pct"]:+7.3f}')

    def summary(sel, title):
        s = [r for r in rows if sel(r)]
        if not s:
            return
        d = np.array([r['dBbar_T'] for r in s])
        b = np.array([r['Bbar_ref_T'] for r in s])
        e2 = np.array([r['b2_err_pct'] for r in s])
        print(f'\n   {title} ({len(s)} regions)')
        print(f'      ||d<B>||/||<B>||  {100*np.sqrt((d**2).sum()/(b**2).sum()):6.3f} %'
              f'   per-region rel: mean {100*np.mean(d/b):5.2f} %,'
              f' max {100*np.max(d/b):5.2f} %')
        print(f'      <|B|^2> error:    mean {np.mean(e2):+6.3f} %,'
              f'  rms {np.sqrt(np.mean(e2**2)):6.3f} %,'
              f'  max |{np.max(np.abs(e2)):.3f}| %')

    summary(lambda r: r['is_conductor'], 'conductors -- what the loss model reads')
    summary(lambda r: not r['is_conductor'], 'everything else')
    summary(lambda r: True, 'all regions')

    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump(rows, fh, indent=2)
        print('\nwrote', a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
