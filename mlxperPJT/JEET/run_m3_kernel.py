# -*- coding: utf-8 -*-
"""M3 A블록 채점 — 캐리어 커널의 운전점 불변성과 k_r²ω 컬랩스 (2026-09-05).

입력 (mlxperPJT/M3/From38100/):
  A1  SCL FP    8 f × 30 케이스
  A2  SCL noFP  8 f × 30
  A3  REF FP   10 f × 30  (+연장 40/80 kHz)
  A4  REF noFP 10 f × 30

산출:
  1) 기계별 커널 — 앵커 정규화 프로파일의 케이스간 산포, 국소 지수, 전이
     주파수 f_T (지수=1 교차)
  2) 규약 델타 — FP vs noFP 를 형상·레벨로 분리
  3) k_r²ω 컬랩스 — SC 프로파일을 k_r²=4 배 하고 REF 실측과 대조
  4) I-보정 — 레벨의 전류 의존 (P/I² 드리프트)

  python run_m3_kernel.py
"""
import io
import json
import os

import numpy as np

from run_pwm_pilot_score import parse_wide_totals, HERE

SRC = os.path.join(HERE, '..', 'M3', 'From38100')
PJT_REF = 'REF_e10_WTPM_PatternD_R1_FqMap_MSFp_'
PJT_SCL = 'SCL_e10_WTPM_PatternD_R1_FqMap_MSFp_'
BLOCKS = {
    'A1_SCL_FP':   PJT_SCL + 'SC_Fq_M3_A1_FP.csv',
    'A2_SCL_noFP': PJT_SCL + 'SC_Fq_M3_A2_noFP.csv',
    'A3_REF_FP':   PJT_REF + 'REF_Fq_M3_A3_FP.csv',
    'A4_REF_noFP': PJT_REF + 'REF_Fq_M3_A4_noFP.csv',
}
ANCHOR = 1066.67
KR2 = 4.0          # SC 는 REF 의 k_r=2 파생 → 주파수 사상 인자
OPMAP = os.path.join(HERE, 'pwm_pilot_opmap.csv')


def load(tag):
    p = os.path.join(SRC, BLOCKS[tag])
    if not os.path.exists(p):
        return None
    d = parse_wide_totals(p)
    # 손실이 전부 0 인 케이스(미실행)는 버린다
    return {c: v for c, v in d.items() if sum(abs(x) for x in v.values()) > 0}


def profile(d):
    """{case: {f: W}} → (freqs, 정규화 프로파일 행렬, 국소 지수 행렬, f_T 벡터)"""
    cases = sorted(d)
    fs = np.array(sorted(d[cases[0]]))
    ia = int(np.argmin(np.abs(fs - ANCHOR)))
    P, E, T = [], [], []
    keep = []
    for c in cases:
        if sorted(d[c]) != list(fs):
            continue
        p = np.array([d[c][f] for f in fs])
        if p[ia] <= 0:
            continue
        keep.append(c)
        P.append(p / p[ia])
        e = np.diff(np.log(p)) / np.diff(np.log(fs))
        E.append(e)
        fm = np.sqrt(fs[:-1] * fs[1:])
        ft = np.nan
        for k in range(len(e) - 1):
            if e[k] >= 1.0 >= e[k + 1]:
                t = (e[k] - 1.0) / (e[k] - e[k + 1])
                ft = float(np.exp(np.log(fm[k]) + t * (np.log(fm[k + 1]) - np.log(fm[k]))))
                break
        T.append(ft)
    return fs, np.array(P), np.array(E), np.array(T), keep


def main():
    ops = {}
    if os.path.exists(OPMAP):
        import csv
        for r in csv.DictReader(io.open(OPMAP, encoding='utf-8')):
            ops[int(r['case'])] = dict(speed=float(r['speed']), beta=float(r['beta']),
                                       irms=float(r['irms']))

    out = {'anchor_Hz': ANCHOR, 'kr2': KR2, 'blocks': {}}
    prof = {}
    for tag in BLOCKS:
        d = load(tag)
        if d is None:
            print('%-12s 파일 없음 (건너뜀)' % tag)
            continue
        fs, P, E, T, keep = profile(d)
        prof[tag] = (fs, P, E, T, keep, d)
        ft = T[~np.isnan(T)]
        # 산포: 주파수별 케이스간 (max/min − 1)
        spread = 100 * (P.max(axis=0) / P.min(axis=0) - 1)
        out['blocks'][tag] = dict(
            n_cases=len(keep), freqs=[float(x) for x in fs],
            spread_pct=[float(x) for x in spread],
            spread_top=float(spread[-1]),
            f_T=dict(n=int(ft.size), median=float(np.median(ft)) if ft.size else None,
                     min=float(ft.min()) if ft.size else None,
                     max=float(ft.max()) if ft.size else None),
            expo_median=[float(x) for x in np.median(E, axis=0)])
        print('%-12s %2d케이스 · 산포 상단 %5.2f%% · f_T 중앙 %s Hz'
              % (tag, len(keep), spread[-1],
                 ('%.0f' % np.median(ft)) if ft.size else '—'))

    # --- 규약 델타 (FP vs noFP), 기계별
    out['convention_delta'] = {}
    for mach, fp, nofp in (('SCL', 'A1_SCL_FP', 'A2_SCL_noFP'),
                           ('REF', 'A3_REF_FP', 'A4_REF_noFP')):
        if fp not in prof or nofp not in prof:
            continue
        fs1, P1, _, _, k1, d1 = prof[fp]
        fs2, P2, _, _, k2, d2 = prof[nofp]
        common = [c for c in k1 if c in k2]
        ia = int(np.argmin(np.abs(fs1 - ANCHOR)))
        shape, level = [], []
        for c in common:
            p1 = np.array([d1[c][f] for f in fs1])
            p2 = np.array([d2[c].get(f, np.nan) for f in fs1])
            if np.isnan(p2).any() or p2[ia] <= 0:
                continue
            shape.append(100 * np.max(np.abs((p2 / p2[ia]) / (p1 / p1[ia]) - 1)))
            level.append(100 * (p2[ia] / p1[ia] - 1))
        if shape:
            out['convention_delta'][mach] = dict(
                n=len(shape), shape_median=float(np.median(shape)),
                shape_max=float(np.max(shape)), level_median=float(np.median(level)),
                level_min=float(np.min(level)), level_max=float(np.max(level)))
            print('규약 델타 %s: 형상 중앙 %.2f%% 최대 %.2f%% · 레벨 중앙 %+.2f%%'
                  % (mach, np.median(shape), np.max(shape), np.median(level)))

    # --- k_r²ω 컬랩스: SC 프로파일을 KR2 배 축으로 옮겨 REF 와 대조
    if 'A1_SCL_FP' in prof and 'A3_REF_FP' in prof:
        fs_s, _, E_s, T_s, _, _ = prof['A1_SCL_FP']
        fs_r, _, E_r, T_r, _, _ = prof['A3_REF_FP']
        fm_s, fm_r = np.sqrt(fs_s[:-1] * fs_s[1:]), np.sqrt(fs_r[:-1] * fs_r[1:])
        es, er = np.median(E_s, axis=0), np.median(E_r, axis=0)
        ei = np.interp(np.log(fm_r), np.log(fm_s * KR2), es)
        m = (fm_r >= fm_s[0] * KR2) & (fm_r <= fm_s[-1] * KR2)
        ts, tr = np.median(T_s[~np.isnan(T_s)]), np.median(T_r[~np.isnan(T_r)])
        out['collapse'] = dict(
            n_overlap=int(m.sum()),
            dexpo_median=float(np.median(np.abs(er - ei)[m])),
            dexpo_max=float(np.max(np.abs(er - ei)[m])),
            fT_SCL=float(ts), fT_REF=float(tr), fT_ratio=float(tr / ts),
            fT_ratio_vs_kr2=float(tr / ts / KR2))
        print('컬랩스: 겹침 %d점 |Δ지수| 중앙 %.3f 최대 %.3f · f_T 비 %.2f (k_r²=%.0f, 오차 %.1f%%)'
              % (m.sum(), out['collapse']['dexpo_median'], out['collapse']['dexpo_max'],
                 tr / ts, KR2, 100 * abs(tr / ts / KR2 - 1)))

    # --- I-보정: 레벨(상단 주파수 손실)의 전류 의존
    out['current_trend'] = {}
    for tag in ('A1_SCL_FP', 'A3_REF_FP'):
        if tag not in prof or not ops:
            continue
        fs, _, _, _, keep, d = prof[tag]
        rows = []
        for c in keep:
            o = ops.get(c)
            if not o or o['irms'] < 1 or o['beta'] != 0:
                continue
            rows.append((o['irms'], d[c][fs[-1]] / o['irms'] ** 2))
        if len(rows) > 2:
            rows.sort()
            I = np.array([r[0] for r in rows]); y = np.array([r[1] for r in rows])
            out['current_trend'][tag] = dict(
                irms=[float(x) for x in I], P_over_I2=[float(x) for x in y],
                drift_pct=float(100 * (y[-1] / y[0] - 1)))
            print('I-보정 %s (β=0, %.0f Hz): P/I² 드리프트 %+.1f%% (%.0f→%.0f A)'
                  % (tag, fs[-1], out['current_trend'][tag]['drift_pct'], I[0], I[-1]))

    path = os.path.join(HERE, 'map_exports', 'e10', 'checks', 'm3_kernel.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1)
    print('->', path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
