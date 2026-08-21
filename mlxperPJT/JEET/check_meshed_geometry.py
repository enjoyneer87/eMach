# -*- coding: utf-8 -*-
"""Check the geometry that was actually solved, not the geometry that was asked for.

check_geometry_scaling.py reads the .mot parameters, which is what the
author set. Motor-CAD then recomputes the dependent dimensions of the
V-shape rotor under its own constraints, so what reaches the mesh can
differ from what was typed. The mesh is the last word, and the exports
carry it: every element's region code, centroid and area.

For SCL-M the test is simple. Scale the reference cross-section by k_r
and every region must land on its counterpart: areas in the ratio k_r^2,
centroid radii in the ratio k_r. Regions are matched between the two
models by position rather than by code, since the two exports number
them differently.

    python check_meshed_geometry.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools')))

FIELDS_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'map_exports', 'e10', 'fields')


# 공극층은 이름이 a1, a2, ... 이고 개수가 모델마다 다르다 -- Motor-CAD 가
# 공극을 몇 겹으로 쪼갤지는 크기와 무관하게 정해서, e10 은 Ref 4 겹 / SC 6 겹이다.
# 층끼리 짝지으면 면적비가 4/6 = 0.667 로 나와 스케일링이 깨진 것처럼 보인다.
# 물리적으로 하나인 영역이므로 비교 전에 묶는다.
AIRGAP_RE = re.compile(r'^a\d+$')


def region_table(npz, group_airgap=True):
    """area, centroid radius and angle for every region of one export."""
    d = np.load(npz)
    reg, a = d['reg'].astype(int), d['area_mm2']
    x, y = d['x_mm'], d['y_mm']
    names = {}
    if 'name_codes' in d.files:
        names = {int(c): str(t) for c, t in zip(d['name_codes'],
                                                d['name_texts'])}
    key = reg.copy()
    label = {}
    if group_airgap and names:
        gap = sorted(c for c, n in names.items() if AIRGAP_RE.match(n))
        if gap:
            key = np.where(np.isin(reg, gap), gap[0], reg)
            label[gap[0]] = f'airgap ({len(gap)} layers)'
    rows = {}
    for c in np.unique(key):
        m = key == c
        w = a[m]
        cx, cy = np.average(x[m], weights=w), np.average(y[m], weights=w)
        rows[int(c)] = {
            'area_mm2': float(w.sum()),
            'r_mm': float(np.hypot(cx, cy)),
            'th_deg': float(np.degrees(np.arctan2(cy, cx))),
            'n_elem': int(m.sum()),
            'name': label.get(int(c), names.get(int(c), f'reg {c}')),
        }
    return rows


def match(ref, sc, k_r, tol_mm=1.5):
    """Pair regions by scaled position; unmatched regions are reported."""
    pairs, used = [], set()
    # 묶인 공극은 회전자쪽·고정자쪽 층이 서로 다른 각도에 있고 층 수도
    # 달라서 무게중심 각이 모델마다 다르다 -- 위치가 아니라 이름으로 짝짓는다.
    by_name = {b['name']: c2 for c2, b in sc.items()}
    for c, a in sorted(ref.items()):
        if a['name'].startswith('airgap') :
            c2 = next((v for k, v in by_name.items()
                       if k.startswith('airgap')), None)
            if c2 is not None:
                used.add(c2)
                pairs.append((c, c2, a, sc[c2], 0.0))
                continue
        rr, tt = a['r_mm'] * k_r, a['th_deg']
        best, bd = None, 1e9
        for c2, b in sc.items():
            if c2 in used:
                continue
            # 회전자는 두 모델에서 같은 각도에 있으므로 반경과 각을 함께 본다.
            d = np.hypot(rr - b['r_mm'], np.radians(tt - b['th_deg']) * rr)
            if d < bd:
                best, bd = c2, d
        if best is None or bd > tol_mm * k_r:
            pairs.append((c, None, a, None, bd))
            continue
        used.add(best)
        pairs.append((c, best, a, sc[best], bd))
    return pairs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--fields', default=FIELDS_DEFAULT)
    ap.add_argument('--level', default='MS', choices=('MS', 'Full'))
    ap.add_argument('--k-r', type=float, default=2.0)
    ap.add_argument('--tol-pct', type=float, default=0.5)
    ap.add_argument('--json')
    a = ap.parse_args(argv)

    ref_p = os.path.join(a.fields, f'fieldvec_{a.level}_Ref.npz')
    sc_p = os.path.join(a.fields, f'fieldvec_{a.level}_SC.npz')
    for p in (ref_p, sc_p):
        if not os.path.isfile(p):
            print(f'[missing] {p}')
            return 1

    ref, sc = region_table(ref_p), region_table(sc_p)
    print(f'{a.level}-FEA   Ref {len(ref)} regions, SC {len(sc)} regions, '
          f'k_r = {a.k_r}')
    rows, bad = [], 0
    for c, c2, A, B, dist in match(ref, sc, a.k_r):
        if B is None:
            print(f'   reg {c:4d}  no counterpart within tolerance '
                  f'(nearest {dist:.2f} mm)')
            bad += 1
            continue
        ar = B['area_mm2'] / (A['area_mm2'] * a.k_r ** 2)
        rr = B['r_mm'] / (A['r_mm'] * a.k_r)
        rows.append({'ref_code': c, 'sc_code': c2, 'name': A['name'],
                     'area_ratio': ar, 'radius_ratio': rr,
                     'area_err_pct': 100 * (ar - 1),
                     'radius_err_pct': 100 * (rr - 1),
                     'ref_area_mm2': A['area_mm2'], 'ref_r_mm': A['r_mm']})
    rows.sort(key=lambda r: -abs(r['area_err_pct']))
    print(f'\n   {"region":<22s} {"area mm2":>10s} {"r mm":>8s}'
          f' {"area/k^2":>9s} {"err %":>8s} {"r/k":>8s} {"err %":>8s}')
    for r in rows:
        flag = ' ' if abs(r['area_err_pct']) <= a.tol_pct else '<'
        if flag == '<':
            bad += 1
        print(f'{flag}  {r["name"][:22]:<22s} '
              f'{r["ref_area_mm2"]:10.4f} {r["ref_r_mm"]:8.3f} '
              f'{r["area_ratio"]:9.5f} {r["area_err_pct"]:+8.3f} '
              f'{r["radius_ratio"]:8.5f} {r["radius_err_pct"]:+8.3f}')

    e = np.array([r['area_err_pct'] for r in rows])
    print(f'\n   area error: mean {e.mean():+.3f} %, '
          f'rms {np.sqrt((e ** 2).mean()):.3f} %, max |{np.abs(e).max():.3f}| %'
          f'   ({(np.abs(e) > a.tol_pct).sum()} of {len(e)} beyond '
          f'{a.tol_pct} %)')
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump(rows, fh, indent=2)
        print('wrote', a.json)
    return 0 if bad == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
