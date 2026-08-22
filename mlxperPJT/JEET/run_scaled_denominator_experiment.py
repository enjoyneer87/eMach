# -*- coding: utf-8 -*-
"""The denominator the manuscript describes, built and scored.

Section 5.4 says the variant's slot field transfers from Ref, and Table 2
books zero MS-FEA for SC on that basis. The deposited SC hybrid is not
that: Motor-CAD ran it on the SC model directly, and it departs from
similarity by 2.5 percent. This builds the described denominator -- Ref
fields scaled by k_r, the hybrid evaluated on them at SC's speeds -- and
scores the adopted 27-point plan on it against SC's own Full-FEA.

The field is magnetostatic and carries no frequency, so the 30 anchor
fields serve all four speeds; the kernel takes its frequency from the
speed it is evaluated at. The same kernel evaluated on SC's own fields
is run alongside, so the effect of scaling the field can be separated
from the effect of the kernel.

Stages, each skipped if its output exists:
  1  scale the 30 Ref anchor fields to SC (scale_fea_txt, s = k_r)
  2  lay them out under the four SC speed names (hard links)
  3  evaluate the line-sampled hybrid on them (translim kernel, 80 C)
  4  fit the adopted plan on each denominator and score

    python run_scaled_denominator_experiment.py
"""
from __future__ import annotations

import contextlib
import glob
import io
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import replace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'tools')))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from jeet_acloss_rbf.similarity_field_scale import scale_fea_txt   # noqa
from jeet_acloss_rbf.pipeline import AcLossPipeline               # noqa
from jeet_acloss_rbf.AcLossDataset import AcLossDataset           # noqa
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder       # noqa

BACKFILL = r'D:\KangDH\Thesis\e10\_txt_backfill'
WORK = os.path.join(BACKFILL, 'SC_from_Ref_scaled')
E10 = os.path.join(HERE, 'map_exports', 'e10')
K_R = 2.0
SC_SPEEDS = (2000, 4000, 8000, 16000)
DIR_RE = re.compile(r'Hybrid_Speed_(\d+)RPM_([\d.]+)A_([\d.]+)deg$')
PY = sys.executable
SPEEDS_K = (2.0, 4.0, 8.0, 16.0)


def stage1_scale():
    """Ref anchor fields -> SC geometry, current relabelled by k_r."""
    src_dirs = sorted(glob.glob(os.path.join(BACKFILL, 'Ref',
                                             'Hybrid_Speed_16000RPM_*')))
    out = os.path.join(WORK, '_scaled16k')
    os.makedirs(out, exist_ok=True)
    done = 0
    for d in src_dirs:
        m = DIR_RE.search(os.path.basename(d))
        if not m:
            continue
        cur, ph = float(m.group(2)), float(m.group(3))
        dst_dir = os.path.join(out, f'Ref16k_{cur:.1f}A_{ph:.1f}deg')
        dst = os.path.join(dst_dir, 'FEA_data.txt.gz')
        if os.path.isfile(dst) and os.path.getsize(dst) > 0:
            done += 1
            continue
        os.makedirs(dst_dir, exist_ok=True)
        t0 = time.time()
        scale_fea_txt(os.path.join(d, 'FEA_data.txt.gz'), dst, K_R)
        print(f'  scaled {os.path.basename(d)}  {time.time()-t0:.0f} s',
              flush=True)
        done += 1
    print(f'stage 1: {done} scaled fields', flush=True)
    return out


def stage2_layout(scaled):
    """One copy of each field per SC speed; the kernel reads the speed
    from the directory name. Hard links, so no extra disk."""
    n = 0
    for d in sorted(glob.glob(os.path.join(scaled, 'Ref16k_*'))):
        m = re.search(r'Ref16k_([\d.]+)A_([\d.]+)deg$', d)
        cur_ref, ph = float(m.group(1)), float(m.group(2))
        cur_sc = cur_ref * K_R                 # I -> k_r I
        for spd in SC_SPEEDS:
            name = f'Hybrid_Speed_{spd}RPM_{cur_sc:.1f}A_{ph:.1f}deg'
            dd = os.path.join(WORK, name)
            dst = os.path.join(dd, 'FEA_data.txt.gz')
            if os.path.isfile(dst):
                n += 1
                continue
            os.makedirs(dd, exist_ok=True)
            try:
                os.link(os.path.join(d, 'FEA_data.txt.gz'), dst)
            except OSError:
                import shutil
                shutil.copyfile(os.path.join(d, 'FEA_data.txt.gz'), dst)
            n += 1
    print(f'stage 2: {n} speed-tagged field directories', flush=True)


def stage3_hybrid(tag):
    """Line-sampled hybrid on the scaled fields, SC conductor size, 80 C."""
    # run_line_sampled_hybrid.py 는 --tag 이름의 폴더에 쓴다 (SC 폴더가 아니다).
    out = os.path.join(E10, tag, f'line_sampled_hybrid_{tag}_80C.json')
    if os.path.isfile(out):
        print(f'stage 3: exists {os.path.basename(out)}', flush=True)
        return out
    cmd = [PY, os.path.join(HERE, 'run_line_sampled_hybrid.py'),
           '--model', 'SC', '--speed', '0', '--temp', '80',
           '--fields-dir', WORK, '--tag', tag]
    print('stage 3:', ' '.join(cmd[1:]), flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    print(r.stdout[-1500:], flush=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], flush=True)
        raise SystemExit('stage 3 failed')
    print(f'stage 3: {time.time()-t0:.0f} s', flush=True)
    return out


def load_rows(path):
    return json.load(io.open(path, encoding='utf-8'))['rows']


def lut_from(rows, key):
    lut = {}
    for r in rows:
        v, sk = r.get(key), r.get('skin_excess_W')
        if v is None or sk is None:
            continue
        lut[(round(r['speed_rpm']), round(r['current_A'], 1),
             round(r['phase_deg'], 1))] = (v + sk) / 1e3
    return lut


def swapped(ds, lut):
    pts = []
    for p in ds.points:
        k = (round(p.speed_rpm), round(p.current_rms, 1), round(p.phase_deg, 1))
        h = lut.get(k)
        if h is None or h <= 0:
            continue
        pts.append(replace(p, hybrid_ac_kW=h, AF=p.fea_ac_kW / h))
    return AcLossDataset(pts)


def score(pl, ds, rule):
    cfg, plan = pl.cfg, pl.cfg['plan']['SC']
    RbfModelBuilder.TRANSFER_RULE = rule
    with contextlib.redirect_stdout(io.StringIO()):
        m = RbfModelBuilder.build_separable_rbf_transfer(
            ds, pl.build_donor(), cfg['k_r']['SC'],
            plan['n_base'], plan['n_spd'], plan['seed'],
            base_speed=cfg['base_speed'],
            n_probe_transfer=cfg['n_probe_transfer'],
            exponent=cfg['exponent'], placement='structured',
            donor_dataset=pl.load_dataset(cfg['donor_scale']))
    pred = np.asarray(m.predict(ds.speeds_k * 1000.0, ds.irms_arr,
                                ds.phase_arr), float) * ds.h_ac_arr
    ld = ds.irms_arr > 1.0
    f = ds.f_ac_arr
    out = {
        'n': int(len(ds)),
        'uncorrected_wmae_pct': float(100 * np.abs(ds.h_ac_arr - f)[ld].sum()
                                      / f[ld].sum()),
        'wmae_pct': float(100 * np.abs(pred - f)[ld].sum() / f[ld].sum()),
        'mae_pct': float(100 * (np.abs(pred - f) / (f + 1e-12))[ld].mean()),
        'per_speed': {},
        'p_exponent': {f'{s:g}k': float(np.polyval(m.q_coeffs, s))
                       for s in (2.0, 4.0, 8.0)},
    }
    for s in SPEEDS_K:
        sel = ld & (np.abs(ds.speeds_k - s) < 0.1)
        out['per_speed'][f'{s:g}k'] = float(
            100 * np.abs(pred - f)[sel].sum() / f[sel].sum())
    return out


def main():
    t_all = time.time()
    scaled = stage1_scale()
    stage2_layout(scaled)
    j_scaled = stage3_hybrid('SC_fromRef')
    j_own = os.path.join(E10, 'SC', 'line_sampled_hybrid_SC_80C.json')

    pl = AcLossPipeline()
    with contextlib.redirect_stdout(io.StringIO()):
        base = pl.load_dataset('SC')
    cases = {
        'hybrid, deposited (Motor-CAD on SC)': (None, None),
        'translim on SC own field': (j_own, 'line_msq_P24c6_translim'),
        'translim on scaled Ref field': (j_scaled, 'line_msq_P24c6_translim'),
        'G2 full-area on SC own field': (j_own, 'full_G2_solid'),
        'G2 full-area on scaled Ref field': (j_scaled, 'full_G2_solid'),
    }
    results = {}
    print(f'\n   {"denominator":36s} {"rule":9s} {"n":>4s} {"uncorr":>7s} '
          f'{"wMAE":>6s} {"MAE":>6s}   ' + '  '.join(f'{s:g}k' for s in SPEEDS_K)
          + '   p(2k)')
    for name, (path, key) in cases.items():
        ds = base if path is None else swapped(base, lut_from(load_rows(path), key))
        for rule in ('ratio', 'numerator'):
            r = score(pl, ds, rule)
            results[f'{name} | {rule}'] = r
            ps = r['per_speed']
            print(f'   {name:36s} {rule:9s} {r["n"]:4d} '
                  f'{r["uncorrected_wmae_pct"]:6.1f}% {r["wmae_pct"]:5.2f}% '
                  f'{r["mae_pct"]:5.2f}%   '
                  + '  '.join(f'{ps[f"{s:g}k"]:5.2f}' for s in SPEEDS_K)
                  + f'   {r["p_exponent"]["2k"]:5.2f}', flush=True)

    # 분모 자체의 상사성: 스케일 필드 분모 / 직접 해석 분모
    r_s, r_o = load_rows(j_scaled), load_rows(j_own)
    ls = lut_from(r_s, 'line_msq_P24c6_translim')
    lo = lut_from(r_o, 'line_msq_P24c6_translim')
    md = {}
    for k, v in ls.items():
        if k in lo and lo[k] > 0:
            md.setdefault(k[0], []).append(v / lo[k])
    print('\n   translim denominator, scaled-Ref-field / SC-own-field, by speed')
    for s in sorted(md):
        v = np.array(md[s])
        print(f'      {s:6d} RPM  {v.mean():.4f} +- {v.std():.4f}  n={len(v)}')
        results[f'denominator_ratio_{s}'] = {'mean': float(v.mean()),
                                             'std': float(v.std()),
                                             'n': int(len(v))}

    out = os.path.join(HERE, 'checks', 'scaled_denominator_experiment.json')
    json.dump(results, io.open(out, 'w', encoding='utf-8'), indent=2)
    print(f'\n   wrote {out}   ({time.time()-t_all:.0f} s total)')
    RbfModelBuilder.TRANSFER_RULE = 'ratio'
    return 0


if __name__ == '__main__':
    sys.exit(main())
