# -*- coding: utf-8 -*-
"""PWM 파일럿 P4 — 과도 2톤 vs 대역분할 예측 (2026-08-28).

과도 스터디 SC_Tr_PWMPilot_2tone (til18k 의 Transient2D 복제, FP 삭제,
회전 16 kRPM, 2 전기주기 × 512 스텝):
  런 A: Ktone=0   — 기본파 460.1 A(rms), 1066.67 Hz 만
  런 B: Ktone=0.1 — + 4·f1 = 4266.67 Hz, 46.01 A(rms) 톤 (병렬 CS2)

판정: ΔP_측정 = P_B − P_A (후반 주기 평균, 권선 도체 합)
      ΔP_커널 = P_Fq(4266.67 Hz, case26) × Ktone²
      초과분 = 대역 혼합(비선형) — 대역분할 가설의 직접 오차.
톤이 f1 의 정수배(4배)라 평균 창에서 교차항은 선형 세계에서 0.
"""
import csv
import io
import json
import os

import numpy as np

from run_pwm_pilot_score import SRC, HERE

CSV_TR = os.path.join(SRC, 'SCL_e10_WTPM_PatternD_R1_FqMap_MSFp_'
                      'SC_Tr_PWMPilot_2tone.csv')
CSV_FQ = os.path.join(SRC, 'SCL_e10_WTPM_PatternD_R1_FqMap_MSFp_'
                      'SC_Fq_PWMPilot_kernel4266.csv')
KTONE = 0.1
F_TONE = 4266.67


def transient_wire_joule(path, case):
    """과도 CSV 에서 case 의 (time, 권선합 Joule) 시계열."""
    rows = list(csv.reader(io.open(path, encoding='utf-8-sig')))
    for i, r in enumerate(rows):
        if r and r[0].startswith('Joule Loss'):
            cr = rows[i + 1]
            hdr = rows[i + 2]
            starts = {}
            for j, v in enumerate(cr):
                if v.strip().isdigit():
                    starts[int(v)] = j
            if case not in starts:
                return None
            s = starts[case]
            e = min([v for v in starts.values() if v > s] + [len(hdr)])
            wcols = [j for j in range(s, e) if 'Wire' in hdr[j]]
            ts, ps = [], []
            for rr in rows[i + 3:]:
                if not rr or not rr[0].strip():
                    break
                try:
                    t = float(rr[0])
                except ValueError:
                    break
                ts.append(t)
                ps.append(sum(float(rr[j]) for j in wcols))
            return np.array(ts), np.array(ps)
    return None


def fq_total(path, case, freq):
    from run_pwm_pilot_score import parse_wide_totals
    d = parse_wide_totals(path)
    if case not in d:
        return None
    for f, p in d[case].items():
        if abs(f - freq) < 1.0:
            return p
    return None


def main():
    tag = os.environ.get('P4_TAG', 'runA')
    suffix = {'runA': '_runA2', 'runB': '_runB2'}.get(tag, '')
    src = CSV_TR.replace('.csv', suffix + '.csv')
    if not os.path.exists(src):
        src = CSV_TR
    print('reading', os.path.basename(src))
    res = transient_wire_joule(src, 26)
    if res is None:
        raise SystemExit('transient case 26 not in CSV')
    t, p = res
    n = len(t)
    half = n // 2
    p_settled = p[half:]
    print('steps=%d  t=[%g, %g] ms' % (n, 1e3 * t[0], 1e3 * t[-1]))
    print('settled-window mean P = %.1f W  (min %.1f max %.1f)' %
          (p_settled.mean(), p_settled.min(), p_settled.max()))
    kern = fq_total(CSV_FQ, 26, F_TONE)
    out = dict(steps=int(n), t_ms=[float(1e3 * t[0]), float(1e3 * t[-1])],
               P_mean_settled=float(p_settled.mean()),
               P_series=[float(x) for x in p],
               t_series=[float(x) for x in t],
               kernel_P_460A=kern,
               kernel_dP_pred=(kern * KTONE ** 2) if kern else None)
    path = os.path.join(HERE, 'pwm_pilot_p4_run.json')
    # 런 A/B 를 구분해 축적: 기존 파일에 append
    store = {}
    if os.path.exists(path):
        store = json.load(io.open(path, encoding='utf-8'))
    store[tag] = out
    with io.open(path, 'w', encoding='utf-8') as fh:
        json.dump(store, fh, indent=1)
    print('kernel P_Fq(%.0f Hz)=%s W -> dP_pred=%s W' %
          (F_TONE, kern, out['kernel_dP_pred']))
    if 'runA' in store and 'runB' in store:
        # 전기 전주기 창 (교차항 f4±f1 이 정확히 소거되는 유일한 창)
        pa = np.array(store['runA']['P_series'])
        pb = np.array(store['runB']['P_series'])
        pred = store['runB']['kernel_dP_pred'] or store['runA']['kernel_dP_pred']
        dp2 = pb[513:1025].mean() - pa[513:1025].mean()
        print('dP (period-2 window) = %.1f W, dP_kernel = %.1f W, ratio = %.3f' %
              (dp2, pred, dp2 / pred))
        store['verdict'] = dict(dP_period2=float(dp2), dP_kernel=float(pred),
                                ratio_period2=float(dp2 / pred))
        with io.open(path, 'w', encoding='utf-8') as fh:
            json.dump(store, fh, indent=1)
    print('->', path, '(tag=%s)' % tag)


if __name__ == '__main__':
    main()
