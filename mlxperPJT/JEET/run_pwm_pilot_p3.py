# -*- coding: utf-8 -*-
"""PWM 파일럿 P3 — REF vs SCL 캐리어 대역 3각 비교 (2026-08-28).

세 데이터:
  A. SCL FP      : SC_..._Fq_PWMPilot_carrier (30케이스, FP 시프트평균)
  B. SCL noFP    : SC_Fq_PWMPilot_noFP        (부분집합, 비선형 조화)
  C. REF noFP    : REF_Fq_PWMPilot_noFP       (부분집합, 비선형 조화)

  B/A = FP↔비선형조화 규약 델타 (같은 기계)
  C/B = 기계 델타 (같은 규약)  ← P3 의 답
비교 지표: 정규화 프로파일 P(f)/P(anchor) 와 국소 지수 프로파일.

REF 권선 주의: REF 는 병렬 2경로(코일당 전류 절반), SCL 은 직렬 재권선.
절대 레벨 비교는 여자 규약 확인 후에만 — 파일럿 판정은 형상(정규화)만.
"""
import io
import json
import os

import numpy as np

from run_pwm_pilot_score import parse_wide_totals, SRC, HERE

CSV_A = os.path.join(SRC, 'SCL_e10_WTPM_PatternD_R1_FqMap_MSFp_'
                     'SC_e10_WirePeriodic_Load_Fq_PWMPilot_carrier.csv')
CSV_B = os.path.join(SRC, 'SCL_e10_WTPM_PatternD_R1_FqMap_MSFp_'
                     'SC_Fq_PWMPilot_noFP.csv')
CSV_C = os.path.join(SRC, 'REF_e10_WTPM_PatternD_R1_FqMap_MSFp_'
                     'REF_Fq_PWMPilot_noFP.csv')
ANCHOR = 1066.67


def prof(d):
    fs = np.array(sorted(d))
    ps = np.array([d[f] for f in fs])
    ia = list(fs).index(ANCHOR)
    e = np.diff(np.log(ps)) / np.diff(np.log(fs))
    return fs, ps, ps / ps[ia], e


def main():
    A = parse_wide_totals(CSV_A)
    B = parse_wide_totals(CSV_B) if os.path.exists(CSV_B) else {}
    C = parse_wide_totals(CSV_C) if os.path.exists(CSV_C) else {}
    # 결과 있는 케이스만 (P 합 > 0)
    B = {c: v for c, v in B.items() if sum(abs(x) for x in v.values()) > 0}
    C = {c: v for c, v in C.items() if sum(abs(x) for x in v.values()) > 0}
    print('cases A=%d B=%d C=%d' % (len(A), len(B), len(C)))

    out = {'anchor': ANCHOR, 'cases': {}}
    for c in sorted(set(B) | set(C)):
        row = {}
        for tag, D in (('SCL_FP', A), ('SCL_noFP', B), ('REF_noFP', C)):
            if c in D:
                fs, ps, pr, e = prof(D[c])
                row[tag] = dict(f=[float(x) for x in fs],
                                P=[float(x) for x in ps],
                                prof=[float(x) for x in pr],
                                expo=[float(x) for x in e])
        # 델타
        if 'SCL_FP' in row and 'SCL_noFP' in row:
            a = np.array(row['SCL_FP']['prof'])[-5:]  # 캐리어 5점만
            b = np.array(row['SCL_noFP']['prof'])
            row['conv_dev'] = float(np.max(np.abs(b / a - 1)))
        if 'SCL_noFP' in row and 'REF_noFP' in row:
            b = np.array(row['SCL_noFP']['prof'])
            cc = np.array(row['REF_noFP']['prof'])
            row['machine_dev'] = float(np.max(np.abs(cc / b - 1)))
        out['cases'][c] = row

    # SCL_FP 는 9점(저대역 포함) — 캐리어 5점만 비교하도록 위에서 절단.
    # 주의: SCL_FP prof 는 anchor 로 정규화돼 있어 [-5:] 절단은 anchor 부터.
    # ---- k_r^2 주파수 사상 겹침: REF(f) vs SC(f / k_r^2), k_r = 2
    # 패밀리 치수(.mot): Ref (3.711, 1.686) / SC (7.422, 3.372) — 양 치수 k_r 배.
    KR2 = 4.0
    scl_full = json.load(io.open(os.path.join(HERE, 'pwm_pilot_score.json'),
                                 encoding='utf-8'))['cases']
    out['kr2_overlay'] = {}
    for c in sorted(C):
        if str(c) not in scl_full:
            continue
        ref = out['cases'][c].get('REF_noFP')
        if not ref:
            continue
        fm_ref = np.sqrt(np.array(ref['f'][:-1]) * np.array(ref['f'][1:]))
        e_ref = np.array(ref['expo'])
        d = scl_full[str(c)]
        e_sc = np.interp(np.log(fm_ref / KR2),
                         np.log(np.array(d['f_mid'])), np.array(d['exponent']))
        out['kr2_overlay'][c] = dict(
            f_mid_ref=[float(x) for x in fm_ref],
            expo_ref=[float(x) for x in e_ref],
            expo_sc_at_scaled_f=[float(x) for x in e_sc],
            max_abs_dev=float(np.max(np.abs(e_ref - e_sc))))

    path = os.path.join(HERE, 'pwm_pilot_p3.json')
    with io.open(path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1)
    for c, row in out['cases'].items():
        msg = 'case %2d' % c
        if 'conv_dev' in row:
            msg += '  conv_dev %.3f%%' % (100 * row['conv_dev'])
        if 'machine_dev' in row:
            msg += '  machine_dev %.3f%%' % (100 * row['machine_dev'])
        if c in out['kr2_overlay']:
            msg += '  kr2_overlay_dev %.3f' % out['kr2_overlay'][c]['max_abs_dev']
        print(msg)
    print('->', path)

    # ---- 그림: (a) 원 주파수 축 지수 (기계 분리), (b) k_r^2 정규화 축 (겹침)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4))
    for c in sorted(C):
        ref = out['cases'][c].get('REF_noFP')
        if not ref:
            continue
        fm = np.sqrt(np.array(ref['f'][:-1]) * np.array(ref['f'][1:]))
        axes[0].semilogx(fm, ref['expo'], 'o-', ms=3, lw=0.9,
                         color='tab:red', alpha=0.7)
        axes[1].semilogx(fm, ref['expo'], 'o-', ms=3, lw=0.9,
                         color='tab:red', alpha=0.7)
    for c in sorted(set(int(k) for k in scl_full)):
        d = scl_full[str(c)]
        axes[0].semilogx(d['f_mid'], d['exponent'], '-', lw=0.5,
                         color='tab:blue', alpha=0.3)
        axes[1].semilogx(np.array(d['f_mid']) * KR2, d['exponent'], '-',
                         lw=0.5, color='tab:blue', alpha=0.3)
    for ax, xl in zip(axes, ('f (Hz)', r'$k_r^{2}$-scaled f (Hz), SC$\times$4')):
        ax.axhline(1, color='0.4', lw=0.6, ls='--')
        ax.axhline(0.5, color='0.6', lw=0.6, ls=':')
        ax.set_xlabel(xl)
        ax.set_ylabel(r'$d\ln P/d\ln f$')
    axes[0].text(0.05, 0.9, 'REF (red) vs SC (blue)', transform=axes[0].transAxes,
                 fontsize=7)
    for ax, tag in zip(axes, 'ab'):
        ax.text(0.5, -0.28, '(%s)' % tag, transform=ax.transAxes,
                ha='center', fontsize=9)
    fig.tight_layout()
    figpath = os.path.join(HERE, 'fig', 'pwm_pilot_p3.png')
    fig.savefig(figpath, dpi=200, bbox_inches='tight')
    print('->', figpath)


if __name__ == '__main__':
    main()
