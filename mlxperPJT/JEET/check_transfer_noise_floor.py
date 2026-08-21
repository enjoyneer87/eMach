# -*- coding: utf-8 -*-
"""What does a mesh-to-mesh comparison cost when there is nothing to find?

Any statement of the form "the transformed and the directly solved
fields differ by x %" is only meaningful against the error the transfer
itself introduces. On first-order elements B is element-wise constant,
so a pointwise comparison of two different meshes carries an O(h) floor
everywhere and an O(1) jump wherever a material boundary falls inside an
element of one mesh but not the other. That floor is not a property of
the scaling law and must not be attributed to it.

The floor is measurable. The same machine at the same instant is solved
on two different meshes -- the MS-FEA export (14792 elements) and the
Full-FEA export (19616) -- and at the static first block neither carries
eddy currents, so the two fields are the same physical field. Whatever
separates them is the transfer, not the physics.

Reported for the same three layers the similarity check uses, so each
similarity number can be read against its own floor:
  * pointwise on a common raster (what the difference map draws),
  * pointwise restricted to material interiors,
  * region integrals (what the loss model consumes).

    python check_transfer_noise_floor.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'tools')))

from jeet_acloss_rbf.field_metrics import (mesh_element_to_raster,   # noqa
                                           mesh_field_to_raster)
from check_meshed_geometry import match                              # noqa
from check_region_field_transfer import region_fields                # noqa

FIELDS_DEFAULT = os.path.join(HERE, 'map_exports', 'e10', 'fields')


def raster_floor(a_npz, b_npz, n_r=400, n_t=600, window_deg=(-66.7, -21.8)):
    """Pointwise disagreement of two meshes carrying the same field."""
    da, db = np.load(a_npz), np.load(b_npz)
    ra = np.hypot(da['x_mm'], da['y_mm'])
    rb = np.hypot(db['x_mm'], db['y_mm'])
    r0, r1 = max(ra.min(), rb.min()), min(ra.max(), rb.max())
    R, T = np.meshgrid(np.linspace(r0, r1, n_r),
                       np.radians(np.linspace(*window_deg, n_t)),
                       indexing='ij')
    X, Y = R * np.cos(T), R * np.sin(T)

    def on(d):
        bx = mesh_field_to_raster(d['node_xy'], d['tri'], d['bx_T'], X, Y,
                                  d['area_mm2'], region=d['reg'])
        by = mesh_field_to_raster(d['node_xy'], d['tri'], d['by_T'], X, Y,
                                  d['area_mm2'], region=d['reg'])
        reg = mesh_element_to_raster(d['node_xy'], d['tri'], d['reg'], X, Y)
        return bx, by, reg

    ax, ay, areg = on(da)
    bx, by, breg = on(db)
    dB = np.hypot(ax - bx, ay - by)
    B = np.hypot(bx, by)
    ok = np.isfinite(dB) & np.isfinite(B)
    edge = np.zeros_like(ok)
    for arr in (areg, breg):
        edge[1:, :] |= arr[1:, :] != arr[:-1, :]
        edge[:-1, :] |= arr[1:, :] != arr[:-1, :]
        edge[:, 1:] |= arr[:, 1:] != arr[:, :-1]
        edge[:, :-1] |= arr[:, 1:] != arr[:, :-1]

    def blk(m):
        return {
            'n': int(m.sum()),
            'dB_L2_pct': float(100 * np.sqrt(np.nanmean(dB[m] ** 2))
                               / np.sqrt(np.nanmean(B[m] ** 2))),
            'dB_mean_T': float(np.nanmean(dB[m])),
            'dB_p95_T': float(np.nanpercentile(dB[m], 95)),
        }

    return {'all': blk(ok), 'interior': blk(ok & ~edge),
            'interface': blk(ok & edge)}


def region_floor(a_npz, b_npz):
    """Region-integral disagreement -- no interpolation anywhere."""
    A, B = region_fields(a_npz), region_fields(b_npz)
    rows = []
    for c, c2, x, y, _ in match(A, B, 1.0):
        if y is None:
            continue
        d = float(np.hypot(y['bx_T'] - x['bx_T'], y['by_T'] - x['by_T']))
        b = float(np.hypot(x['bx_T'], x['by_T']))
        rows.append((x['is_conductor'], d, b,
                     100 * (y['b2_T2'] / x['b2_T2'] - 1) if x['b2_T2'] else 0.0))
    out = {}
    for name, want in (('conductors', True), ('other', False), ('all', None)):
        s = [r for r in rows if want is None or r[0] == want]
        if not s:
            continue
        d = np.array([r[1] for r in s])
        b = np.array([r[2] for r in s])
        e = np.array([r[3] for r in s])
        out[name] = {
            'n': len(s),
            'dB_L2_pct': float(100 * np.sqrt((d ** 2).sum() / (b ** 2).sum())),
            'b2_err_mean_pct': float(np.mean(e)),
            'b2_err_rms_pct': float(np.sqrt(np.mean(e ** 2))),
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--fields', default=FIELDS_DEFAULT)
    ap.add_argument('--json')
    a = ap.parse_args(argv)

    report = {}
    for model in ('Ref', 'SC'):
        pa = os.path.join(a.fields, f'fieldvec_b1_MS_{model}.npz')
        pb = os.path.join(a.fields, f'fieldvec_b1_Full_{model}.npz')
        for p in (pa, pb):
            if not os.path.isfile(p):
                print(f'[missing] {p}')
                return 1
        na, nb = (len(np.load(p)['x_mm']) for p in (pa, pb))
        print(f'=== {model}: MS mesh {na} elements vs Full mesh {nb}, '
              f'same instant, same physics')
        r = raster_floor(pa, pb)
        for k, v in r.items():
            print(f'    raster {k:10s} n {v["n"]:6d}  '
                  f'||dB||/||B|| {v["dB_L2_pct"]:6.2f} %   '
                  f'mean {v["dB_mean_T"]:.4f} T   p95 {v["dB_p95_T"]:.4f} T')
        g = region_floor(pa, pb)
        for k, v in g.items():
            print(f'    region {k:10s} n {v["n"]:6d}  '
                  f'||d<B>||/||<B>|| {v["dB_L2_pct"]:6.3f} %   '
                  f'<B2> mean {v["b2_err_mean_pct"]:+6.3f} % '
                  f'rms {v["b2_err_rms_pct"]:6.3f} %')
        report[model] = {'n_elem_MS': na, 'n_elem_Full': nb,
                         'raster': r, 'region': g}
        print()

    print('Read every similarity number against the matching row above: '
          'anything at or below it is the meshes, not the scaling law.')
    if a.json:
        p = a.json if os.path.isabs(a.json) else os.path.join(HERE, a.json)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as fh:
            json.dump(report, fh, indent=2)
        print('wrote', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
