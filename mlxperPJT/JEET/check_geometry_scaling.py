# -*- coding: utf-8 -*-
"""Audit every geometry parameter of the scaled variants against SCL-M.

SCL-M asks one thing of the geometry: every radial dimension of the 2-D
cross-section is multiplied by k_r, and everything dimensionless -- angles,
counts, ratios -- is left alone. If a dimension is missed, the variant is
not the machine the scaling law describes, and the Adjustment Factor
fitted on it absorbs the geometry error along with the physics it is meant
to carry.

The audit reads the Motor-CAD .mot files directly (INI text) and compares
every numeric key of the geometry sections, so nothing depends on which
parameters anyone remembered to check.

    python check_geometry_scaling.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

# 기하가 사는 절: 두 모델에 다 있는 절만 비교한다.
GEOM_SECTIONS = (
    'Dimensions', 'Winding_Design', 'Magnetics', 'Design_Options',
)
# 길이가 아닌 것들 — k_r 이 아니라 1 이어야 한다.
DIMENSIONLESS = re.compile(
    r'(angle|_deg|ratio|number|num_|poles|slots|turns|layers|'
    r'fraction|percent|factor|count|paths|phases|_pu$|offset_ratio)', re.I)
# 판단하지 않는 것들: 스위치·인덱스·상태값.
SKIP = re.compile(r'(type|option|enable|_id$|index|colour|color|version|'
                  r'name|date|path|file)', re.I)


def read_mot(path):
    """Section -> {key: raw string} for one .mot file."""
    out, sec = {}, None
    with open(path, encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                sec = line[1:-1]
                out.setdefault(sec, {})
            elif sec and '=' in line:
                k, v = line.split('=', 1)
                out[sec][k.strip()] = v.strip()
    return out


def as_float(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def audit(ref_path, var_path, k_r, tol_pct=0.5, sections=GEOM_SECTIONS):
    """Compare one variant against the reference.

    Returns (rows, summary). A row is flagged when the observed ratio is
    neither k_r (a length that scaled) nor 1 (a quantity that should not),
    or when it is 1 where k_r was expected.
    """
    A, B = read_mot(ref_path), read_mot(var_path)
    rows = []
    for sec in sections:
        if sec not in A or sec not in B:
            continue
        for key in sorted(set(A[sec]) & set(B[sec])):
            if SKIP.search(key):
                continue
            a, b = as_float(A[sec][key]), as_float(B[sec][key])
            if a is None or b is None or a == 0.0:
                continue
            ratio = b / a
            expect = 1.0 if DIMENSIONLESS.search(key) else k_r
            # k_r 도 1 도 아닌 값은 어느 쪽으로도 설명되지 않는다.
            near_kr = abs(ratio - k_r) / k_r * 100 <= tol_pct
            near_one = abs(ratio - 1.0) * 100 <= tol_pct
            ok = (near_kr if expect == k_r else near_one)
            if ok:
                continue
            rows.append({
                'section': sec, 'key': key, 'ref': a, 'variant': b,
                'ratio': ratio, 'expected': expect,
                'verdict': ('not scaled' if near_one and expect == k_r
                            else 'scaled but should not be' if near_kr
                            else 'neither'),
                'err_pct': 100 * (ratio - expect) / expect,
            })
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=r'D:\KangDH\Thesis\e10')
    ap.add_argument('--json')
    ap.add_argument('--tol-pct', type=float, default=0.5)
    a = ap.parse_args(argv)

    ref = os.path.join(a.root, 'refModel', 'e10Turn6V261.mot')
    variants = [
        ('HalfSC', os.path.join(a.root, 'SLFEA_Half',
                                'e10Turn6V261SLFEA_Half.mot'), 1.5),
        ('SC', os.path.join(a.root, 'SLFEA', 'e10Turn6V261SLFEA.mot'), 2.0),
    ]
    missing = [p for p in [ref] + [v[1] for v in variants]
               if not os.path.isfile(p)]
    if missing:
        for p in missing:
            print(f'[missing] {p}')
        return 1

    report, bad = {}, 0
    for name, path, k_r in variants:
        rows = audit(ref, path, k_r, a.tol_pct)
        report[name] = {'k_r': k_r, 'path': path, 'findings': rows}
        bad += len(rows)
        print(f'=== {name}  (k_r = {k_r})   {len(rows)} parameter(s) off')
        for r in sorted(rows, key=lambda r: -abs(r['err_pct'])):
            print(f"    {r['section']:>16s}.{r['key']:<34s} "
                  f"{r['ref']:>12.5g} -> {r['variant']:<12.5g} "
                  f"ratio {r['ratio']:7.4f} (expected {r['expected']:.4g}, "
                  f"{r['err_pct']:+7.2f} %)  {r['verdict']}")
        print()

    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump(report, fh, indent=2)
        print('wrote', a.json)
    print('PASS: every geometry parameter scales as SCL-M requires'
          if bad == 0 else f'FAIL: {bad} parameter(s) do not follow SCL-M')
    return 0 if bad == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
