# -*- coding: utf-8 -*-
"""PWM 파일럿 P3 — REF vs SCL 캐리어 대역 프로파일 비교 (2026-08-28).

REF 는 e10MS_ConductorModel_REF_Periodic16k 프로젝트 안에서 과도 스터디를
Frequency2D 로 복제해 만든 캐리어 스윕 (저대역 없음, 5주파수 × 30케이스).
SCL 은 run_pwm_pilot_score.py 가 만든 병합 데이터 (9주파수).

판정: 두 기계의 정규화 프로파일 P(f)/P(anchor) 와 f_T 가 일치하는가.
도체 기하가 같으므로(슬롯당 4와이어 동일) 일치 = 캐리어 커널의 기계 불변성.
"""
import csv
import io
import json
import os

import numpy as np

from run_pwm_pilot_score import parse_wide_totals, SRC, HERE

CSV_REF = os.path.join(
    SRC, 'e10MS_ConductorModel_REF_Periodic16k_REF_Fq_PWMPilot_carrier.csv')
SCL_JSON = os.path.join(HERE, 'pwm_pilot_score.json')
ANCHOR = 1066.67


def main():
    ref = parse_wide_totals(CSV_REF)
    scl = json.load(io.open(SCL_JSON, encoding='utf-8'))['cases']
    cases = sorted(set(ref) & set(int(c) for c in scl))
    print('common cases:', len(cases))

    rows = []
    for c in cases:
        fr = np.array(sorted(ref[c]))
        pr = np.array([ref[c][f] for f in fr])
        ia = list(fr).index(ANCHOR)
        prof_r = pr / pr[ia]
        d = scl[str(c)]
        fs = np.array(d['f']); ps = np.array(d['P'])
        keep = np.isin(fs, fr)
        prof_s = ps[keep] / ps[fs == ANCHOR][0]
        # 국소 지수와 f_T (5점 캐리어 격자에서)
        def ft_of(f, p):
            lnf, lnp = np.log(f), np.log(p)
            e = np.diff(lnp) / np.diff(lnf)
            fm = np.sqrt(f[:-1] * f[1:])
            for k in range(len(e) - 1):
                if e[k] >= 1.0 >= e[k + 1]:
                    t = (e[k] - 1.0) / (e[k] - e[k + 1])
                    return float(np.exp(np.log(fm[k]) +
                                        t * (np.log(fm[k + 1]) - np.log(fm[k]))))
            return None
        rows.append(dict(
            case=c, fT_ref=ft_of(fr, pr), fT_scl=ft_of(fr, ps[keep]),
            prof_ref=[float(x) for x in prof_r],
            prof_scl=[float(x) for x in prof_s],
            P_ref=[float(x) for x in pr],
            P_scl=[float(x) for x in ps[keep]],
            ratio_anchor=float(ps[fs == ANCHOR][0] / pr[ia])))

    fTr = [r['fT_ref'] for r in rows if r['fT_ref']]
    fTs = [r['fT_scl'] for r in rows if r['fT_scl']]
    prof_dev = [max(abs(np.array(r['prof_ref']) / np.array(r['prof_scl']) - 1))
                for r in rows]
    out = dict(
        freqs=[float(x) for x in sorted(ref[cases[0]])],
        fT_ref=dict(min=min(fTr), median=float(np.median(fTr)), max=max(fTr)),
        fT_scl_5pt=dict(min=min(fTs), median=float(np.median(fTs)), max=max(fTs)),
        prof_dev_max=float(max(prof_dev)), prof_dev_median=float(np.median(prof_dev)),
        anchor_ratio_scl_over_ref=dict(
            min=float(min(r['ratio_anchor'] for r in rows)),
            max=float(max(r['ratio_anchor'] for r in rows))),
        rows=rows)
    path = os.path.join(HERE, 'pwm_pilot_ref_compare.json')
    with io.open(path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1)
    print('f_T REF   :', out['fT_ref'])
    print('f_T SCL(5pt):', out['fT_scl_5pt'])
    print('profile dev max %.3f%% median %.3f%%' %
          (100 * out['prof_dev_max'], 100 * out['prof_dev_median']))
    print('anchor P_SCL/P_REF:', out['anchor_ratio_scl_over_ref'])
    print('->', path)


if __name__ == '__main__':
    main()
