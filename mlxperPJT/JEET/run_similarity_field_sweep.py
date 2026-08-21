# -*- coding: utf-8 -*-
"""Similarity-pair field transfer over the whole loaded grid, interpolation-free.

check_region_field_transfer.py measures one operating point. This walks
the similarity-corresponding pairs -- Ref at the anchor speed against SC
at the anchor speed over k_r^2 with k_r times the current -- and reports
the same region-integral statistics for every one of them, so the claim
the figure makes at the rated point can be stated for the grid.

Every average is formed on its own mesh; nothing is interpolated between
the two. The snapshot is block 65, one pole pitch and half an electrical
period on from the static first block, which puts the rotor where Fig 3
has it with the eddy currents fully developed.

    python run_similarity_field_sweep.py --out checks/similarity_field_sweep.json
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'tools')))

from jeet_acloss_rbf.field_metrics import (parse_mes_txt, block_angles,  # noqa
                                           match_blocks_by_angle,
                                           _is_conductor_region)
from check_meshed_geometry import AIRGAP_RE, match                  # noqa
from check_region_field_transfer import CONDUCTOR_RE                # noqa

BACKFILL = r'D:\KangDH\Thesis\e10\_txt_backfill'
OP_RE = re.compile(r'FullFEA_Speed_(\d+)RPM_([\d.]+)A_([\d.]+)deg$')


def list_ops(model, speed):
    out = []
    root = os.path.join(BACKFILL, model)
    for d in sorted(os.listdir(root)):
        m = OP_RE.match(d)
        if m and int(m.group(1)) == speed:
            out.append((float(m.group(2)), float(m.group(3)), d))
    return out


def region_fields_from_parse(p):
    """Area-weighted per-region averages, straight off one mesh."""
    reg = p['reg'].astype(int)
    a, bx, by = p['area_mm2'], p['bx'], p['by']
    x, y = p['x_mm'], p['y_mm']
    names = p['names']
    gap = sorted(c for c, n in names.items() if AIRGAP_RE.match(n))
    key = np.where(np.isin(reg, gap), gap[0], reg) if gap else reg
    label = {gap[0]: f'airgap ({len(gap)} layers)'} if gap else {}
    rows = {}
    for c in np.unique(key):
        m = key == c
        w = a[m]
        tot = w.sum()
        cx, cy = np.average(x[m], weights=w), np.average(y[m], weights=w)
        nm = label.get(int(c), names.get(int(c), f'reg {c}'))
        rows[int(c)] = {
            'name': nm, 'area_mm2': float(tot),
            'r_mm': float(np.hypot(cx, cy)),
            'th_deg': float(np.degrees(np.arctan2(cy, cx))),
            'bx_T': float(np.dot(bx[m], w) / tot),
            'by_T': float(np.dot(by[m], w) / tot),
            'b2_T2': float(np.dot(bx[m] ** 2 + by[m] ** 2, w) / tot),
            'is_conductor': bool(CONDUCTOR_RE.match(nm)),
        }
    return rows


def gunzip(src, dst):
    if os.path.isfile(dst) and os.path.getsize(dst) > 0:
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with gzip.open(src, 'rb') as fi, open(dst, 'wb') as fo:
        shutil.copyfileobj(fi, fo, length=1 << 22)
    return dst


def load(model, folder, scratch, block):
    gz = os.path.join(BACKFILL, model, folder, 'FEA_data.txt.gz')
    txt = gunzip(gz, os.path.join(scratch, f'{model}_{folder}.txt'))
    try:
        ang = block_angles(txt)
        n = len(ang['deg'])
        blk = block if block <= n else n // 2
        return region_fields_from_parse(parse_mes_txt(txt, block=blk))
    finally:
        try:
            os.remove(txt)
        except OSError:
            pass


def compare(ref, sc, k_r):
    rows = []
    for c, c2, A, B, _ in match(ref, sc, k_r):
        if B is None:
            continue
        d = float(np.hypot(B['bx_T'] - A['bx_T'], B['by_T'] - A['by_T']))
        b = float(np.hypot(A['bx_T'], A['by_T']))
        rows.append({'name': A['name'], 'is_conductor': A['is_conductor'],
                     'dBbar_T': d, 'Bbar_ref_T': b,
                     'b2_err_pct': (100 * (B['b2_T2'] / A['b2_T2'] - 1)
                                    if A['b2_T2'] else float('nan'))})
    return rows


def agg(rows, conductors_only):
    s = [r for r in rows if r['is_conductor'] == conductors_only]
    if not s:
        return None
    d = np.array([r['dBbar_T'] for r in s])
    b = np.array([r['Bbar_ref_T'] for r in s])
    e2 = np.array([r['b2_err_pct'] for r in s])
    return {
        'n': len(s),
        'dB_L2_pct': float(100 * np.sqrt((d ** 2).sum() / (b ** 2).sum())),
        'dB_rel_mean_pct': float(100 * np.mean(d / b)),
        'dB_rel_max_pct': float(100 * np.max(d / b)),
        'b2_err_mean_pct': float(np.mean(e2)),
        'b2_err_rms_pct': float(np.sqrt(np.mean(e2 ** 2))),
        'b2_err_absmax_pct': float(np.max(np.abs(e2))),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--k-r', type=float, default=2.0)
    ap.add_argument('--ref-speed', type=int, default=16000)
    ap.add_argument('--block', type=int, default=65)
    ap.add_argument('--scratch', default=os.path.join(HERE, '_sweep_tmp'))
    ap.add_argument('--out')
    a = ap.parse_args(argv)

    sc_speed = int(round(a.ref_speed / a.k_r ** 2))
    ref_ops = list_ops('Ref', a.ref_speed)
    sc_ops = list_ops('SC', sc_speed)
    sc_by = {(round(i, 1), round(b, 1)): d for i, b, d in sc_ops}

    pairs = []
    for i, b, d in ref_ops:
        if i < 1.0:                       # 무부하는 상사쌍 판정에서 뺀다
            continue
        # I_SC = k_r I_Ref, 반올림 표기(460.0 -> 920.0, 115.1 -> 230.1) 허용
        want = a.k_r * i
        hit = min(sc_by, key=lambda k: abs(k[0] - want) + 100 * abs(k[1] - b))
        if abs(hit[0] - want) > 0.6 or abs(hit[1] - b) > 0.01:
            continue
        pairs.append((i, b, d, sc_by[hit], hit[0]))

    print(f'{len(pairs)} similarity pairs: Ref {a.ref_speed} RPM vs '
          f'SC {sc_speed} RPM, k_r = {a.k_r}, block {a.block}')
    os.makedirs(a.scratch, exist_ok=True)
    out, t0 = [], time.time()
    for n, (i, b, rd, sd, i_sc) in enumerate(pairs, 1):
        ref = load('Ref', rd, a.scratch, a.block)
        sc = load('SC', sd, a.scratch, a.block)
        rows = compare(ref, sc, a.k_r)
        rec = {'I_ref_A': i, 'I_sc_A': i_sc, 'beta_deg': b,
               'conductors': agg(rows, True), 'other': agg(rows, False)}
        out.append(rec)
        c = rec['conductors']
        print(f'  [{n:2d}/{len(pairs)}] {i:6.1f} A / {b:5.1f} deg  '
              f'conductors n {c["n"]:2d}  ||d<B>||/||<B>|| {c["dB_L2_pct"]:6.3f} %'
              f'   <B2> mean {c["b2_err_mean_pct"]:+6.3f} % rms '
              f'{c["b2_err_rms_pct"]:6.3f} %   ({time.time()-t0:.0f} s)')

    L2 = np.array([r['conductors']['dB_L2_pct'] for r in out])
    E2 = np.array([r['conductors']['b2_err_mean_pct'] for r in out])
    E2r = np.array([r['conductors']['b2_err_rms_pct'] for r in out])
    print(f'\nconductor regions over {len(out)} similarity pairs')
    print(f'   ||d<B>||/||<B>||   mean {L2.mean():.3f} %, '
          f'median {np.median(L2):.3f} %, max {L2.max():.3f} %')
    print(f'   <|B|^2> mean err   mean {E2.mean():+.3f} %, '
          f'range {E2.min():+.3f} to {E2.max():+.3f} %')
    print(f'   <|B|^2> rms err    mean {E2r.mean():.3f} %, max {E2r.max():.3f} %')

    if a.out:
        p = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as fh:
            json.dump({'k_r': a.k_r, 'ref_speed_rpm': a.ref_speed,
                       'sc_speed_rpm': sc_speed, 'block': a.block,
                       'pairs': out}, fh, indent=2)
        print('wrote', p)
    try:
        os.rmdir(a.scratch)
    except OSError:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
