# -*- coding: utf-8 -*-
"""PWM 파일럿 채점 — FP-Fq 캐리어 대역 스윕의 P(f) 구조 분석 (2026-08-28).

입력: exportJMAGAllCaseTables 가 만든 와이드 CSV 두 장
  - til18k  : 기본파 대역 {266.67, 533.33, 800, 1066.67, 1200} Hz (2024 결과)
  - carrier : {1066.67(앵커), 2000, 5000, 10000, 20000} Hz (2026-08-28 신규,
              til18k 복제 스터디 — 같은 메시·같은 FP 참조, 앵커 상대차 8e-8 확인)

산출:
  1) 케이스별 P(f) 병합 곡선 (30 케이스 × 9 주파수)
  2) 국소 지수 d ln P / d ln f 프로파일 — f² 저항 극한 → √f 표피 극한 전이
  3) 지수=1 교차점 f_T 추정 → 캡 커널 f_t = 1/(π μ0 σ w²) 의 치수·온도 후보와 대조
     (§12.16 의 390 Hz vs 1.5 kHz 모호성 판정 데이터)
  4) f_T 의 운전점(I, β) 의존성 — 대역분할 가설(캐리어 대역 AF 는 OP 무관)의 1차 검증

출력: pwm_pilot_score.json + fig/pwm_pilot_score.png
"""
import csv
import io
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'PWMPilot', 'From38100')
CSV_LOW = os.path.join(
    SRC, 'SCL_e10_WTPM_PatternD_R1_FqMap_MSFp_'
    'SC_e10_WirePeriodic_Load_FqWithShiftAvgDiffMu_til18k.csv')
CSV_HI = os.path.join(
    SRC, 'SCL_e10_WTPM_PatternD_R1_FqMap_MSFp_'
    'SC_e10_WirePeriodic_Load_Fq_PWMPilot_carrier.csv')
OPMAP = os.path.join(HERE, 'pwm_pilot_opmap.csv')  # case,speed,beta,Irms (COM 덤프)

MU0 = 4e-7 * math.pi
SIGMA_20C = 5.8e7
SIGMA_80C = 4.694e7
DIM_RADIAL = 3.711e-3   # 도체 반경 방향 치수 (스크립트 DIMS 첫 값)
DIM_TANGENT = 1.686e-3  # 접선 치수 (원고 표기 w_c 1.7 mm)


def parse_wide_totals(path, item='Joule Loss'):
    """와이드 케이스 CSV 에서 item 섹션의 케이스별 Total 열을 {case: {f: W}} 로."""
    rows = list(csv.reader(io.open(path, encoding='utf-8-sig')))
    out = {}
    i = 0
    while i < len(rows):
        r = rows[i]
        if r and r[0].startswith(item):
            case_row = rows[i + 1]
            hdr = rows[i + 2]
            starts = {}
            for j, v in enumerate(case_row):
                if v.strip().isdigit():
                    starts[int(v.strip())] = j
            order = sorted(starts)
            for k, case in enumerate(order):
                s = starts[case]
                e = starts[order[k + 1]] if k + 1 < len(order) else len(hdr)
                tot = None
                for j in range(s, e):
                    if j < len(hdr) and hdr[j].strip() == 'Total':
                        tot = j
                if tot is None:
                    continue
                d = out.setdefault(case, {})
                for rr in rows[i + 3:]:
                    if not rr or not rr[0].strip():
                        break
                    try:
                        f = float(rr[0])
                        d[round(f, 2)] = float(rr[tot])
                    except (ValueError, IndexError):
                        break
            i += 3
        i += 1
    return out


def main():
    low = parse_wide_totals(CSV_LOW)
    hi = parse_wide_totals(CSV_HI)
    cases = sorted(set(low) & set(hi))
    if not cases:
        raise SystemExit('no common cases: low=%d hi=%d' % (len(low), len(hi)))

    opmap = {}
    if os.path.exists(OPMAP):
        for r in csv.DictReader(io.open(OPMAP, encoding='utf-8')):
            opmap[int(r['case'])] = dict(speed=float(r['speed']),
                                         beta=float(r['beta']),
                                         irms=float(r['irms']))

    anchor_key = 1066.67
    res = {'cases': {}, 'anchor_rel_err': {}, 'f_T': {}}
    for c in cases:
        merged = dict(low[c])
        a_low = low[c].get(anchor_key)
        a_hi = hi[c].get(anchor_key)
        if a_low and a_hi:
            res['anchor_rel_err'][c] = abs(a_hi - a_low) / a_low
        merged.update(hi[c])  # 앵커는 carrier 값으로 덮음 (동일해야 정상)
        fs = np.array(sorted(merged))
        ps = np.array([merged[f] for f in fs])
        lnf, lnp = np.log(fs), np.log(ps)
        expo = np.diff(lnp) / np.diff(lnf)      # 구간 국소 지수
        fmid = np.sqrt(fs[:-1] * fs[1:])
        # 지수=1 교차 (감소 구간에서 선형 보간)
        fT = None
        for k in range(len(expo) - 1):
            if expo[k] >= 1.0 >= expo[k + 1]:
                t = (expo[k] - 1.0) / (expo[k] - expo[k + 1])
                fT = float(np.exp(np.log(fmid[k]) +
                                  t * (np.log(fmid[k + 1]) - np.log(fmid[k]))))
                break
        res['f_T'][c] = fT
        res['cases'][c] = dict(
            f=[float(x) for x in fs], P=[float(x) for x in ps],
            exponent=[float(x) for x in expo], f_mid=[float(x) for x in fmid],
            op=opmap.get(c))

    # 캡 커널 후보 f_t
    def ft(dim, sigma):
        return 1.0 / (math.pi * MU0 * sigma * dim * dim)
    res['ft_candidates'] = {
        'radial_80C': ft(DIM_RADIAL, SIGMA_80C),
        'radial_20C': ft(DIM_RADIAL, SIGMA_20C),
        'tangential_80C': ft(DIM_TANGENT, SIGMA_80C),
        'tangential_20C': ft(DIM_TANGENT, SIGMA_20C),
    }
    fTs = [v for v in res['f_T'].values() if v]
    res['f_T_summary'] = dict(
        n=len(fTs), min=min(fTs) if fTs else None,
        median=float(np.median(fTs)) if fTs else None,
        max=max(fTs) if fTs else None)

    out = os.path.join(HERE, 'pwm_pilot_score.json')
    with io.open(out, 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=1)
    print('cases merged:', len(cases))
    if res['anchor_rel_err']:
        errs = list(res['anchor_rel_err'].values())
        print('anchor rel err: max %.2e' % max(errs))
    print('f_T summary:', res['f_T_summary'])
    print('f_t candidates:', {k: round(v, 1)
                              for k, v in res['ft_candidates'].items()})
    print('->', out)

    # ---- 그림: (a) P(f) 30 케이스, (b) 국소 지수 프로파일 + f_t 후보선
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4))
    for c in cases:
        d = res['cases'][c]
        axes[0].loglog(d['f'], np.array(d['P']) / 1e3, '-', lw=0.7, alpha=0.6)
        axes[1].semilogx(d['f_mid'], d['exponent'], '-', lw=0.7, alpha=0.6)
    axes[0].set_xlabel('f (Hz)')
    axes[0].set_ylabel('winding loss (kW)')
    axes[1].set_xlabel('f (Hz)')
    axes[1].set_ylabel(r'local exponent $d\ln P/d\ln f$')
    axes[1].axhline(2, color='0.6', lw=0.6, ls=':')
    axes[1].axhline(0.5, color='0.6', lw=0.6, ls=':')
    axes[1].axhline(1, color='0.4', lw=0.6, ls='--')
    colors = dict(radial_80C='tab:red', radial_20C='tab:orange',
                  tangential_80C='tab:blue', tangential_20C='tab:cyan')
    for k, v in res['ft_candidates'].items():
        axes[1].axvline(v, color=colors[k], lw=0.8, ls='-.', label=k)
    axes[1].legend(fontsize=6, loc='upper right')
    for ax, tag in zip(axes, 'ab'):
        ax.text(0.5, -0.28, '(%s)' % tag, transform=ax.transAxes,
                ha='center', fontsize=9)
    fig.tight_layout()
    figpath = os.path.join(HERE, 'fig', 'pwm_pilot_score.png')
    os.makedirs(os.path.dirname(figpath), exist_ok=True)
    fig.savefig(figpath, dpi=200, bbox_inches='tight')
    print('->', figpath)


if __name__ == '__main__':
    main()
