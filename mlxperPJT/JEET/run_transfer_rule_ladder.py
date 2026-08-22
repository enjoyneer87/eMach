# -*- coding: utf-8 -*-
"""사다리 세 단을 두 전달 규칙에서 나란히 잰다 (e4a Ref -> SC).

`run_e4a_family_transfer.py` 는 제로샷을 `P_hybrid,SC x AF_Ref` 로 만든다 —
도너의 **비**를 나르는 ratio 경로다.  원고 식 (8)은 도너의 **손실**을 나르고
변형체 자신의 하이브리드로 나눈다(numerator).  두 경로의 사다리를 같은
데이터·같은 절차로 재서 §4.3 이 인쇄하는 두 단을 재현 가능하게 만든다.

    python run_transfer_rule_ladder.py

scipy >= 1.7 필요 (`RBFInterpolator`).  JMAG 번들 파이썬(1.5)에는 없다 —
`C:\\Users\\user\\.ansys_python_venvs\\pyMotorEnv_310` 을 쓸 것.
"""
from __future__ import annotations

import json
import os

import numpy as np

from run_e4a_family_transfer import (DonorModel, K_R, OUT, REF_BASE,
                                     REF_HELD_I, REF_IMAX, REF_SRC,
                                     SC_INBAND, SC_SRC, err_stats, load_pairs)

# 축 길이비.  e4a 패밀리는 적층장을 유지하므로 1 이고, 상사 대응점에서
# 손실은 k_a 배다 (k_r^4 k_a 가 아니다 — 그건 같은 f, J 에서의 비교다).
K_A = 1.0
OUT_CMP = os.path.join(os.path.dirname(OUT), 'transfer_rule_ladder.json')


def rungs(af_zs, af_true, sh, sf, st, inband):
    """제로샷 AF 에서 사다리 두 단(C, F)을 만든다."""
    out = {}
    out['C'] = sh * af_zs
    af_F = af_zs.copy()
    anchors = {}
    for s in sorted(set(st.astype(int))):
        if s in SC_INBAND:
            continue
        idx = np.where(st == s)[0]
        if len(idx) < 3:
            continue
        zs = np.clip(af_zs[idx], 1e-3, None)
        order = np.argsort(zs)
        pick = [order[0], order[len(order) // 2], order[-1]]
        x = np.log(zs[pick])
        y = np.log(np.clip(af_true[idx][pick], 1e-3, None))
        p_c, logf_c = np.polyfit(x, y, 1)
        af_F[idx] = float(np.exp(logf_c)) * zs ** p_c
        anchors[str(s)] = {'f_c': round(float(np.exp(logf_c)), 4),
                           'p_c': round(float(p_c), 4)}
    out['F'] = sh * af_F
    out['anchors'] = anchors
    return out


def main() -> int:
    kr, kt, kc, kp, rh, rf = load_pairs(REF_SRC)
    ks, st, sc, sp, sh, sf = load_pairs(SC_SRC)
    if len(ks) == 0:
        print('[대기] SC TS 쌍 0개')
        return 1
    print(f'[donor Ref] {len(kr)}쌍  [target SC] {len(ks)}쌍')

    af_true = sf / sh
    inband = np.isin(st.astype(int), SC_INBAND)

    # ratio 경로: 도너의 AF 면을 상사점에서 읽는다.
    d_af = DonorModel(kt, kc, kp, rf / rh, REF_BASE, REF_IMAX, REF_HELD_I)
    af_ratio = d_af.predict(st * K_R**2, sc / K_R, sp)

    # numerator 경로: 파이프라인과 같게, 도너의 **측정** 손실을 상사점에서
    # 격자 매칭으로 찾아 온다.  매칭이 없는 외삽대만 적합 면으로 메운다.
    ref_ts = {(int(t), round(c, 2), round(p, 1)): v
              for t, c, p, v in zip(kt, kc, kp, rf)}
    d_p = DonorModel(kt, kc, kp, rf, REF_BASE, REF_IMAX, REF_HELD_I)
    p_surf = d_p.predict(st * K_R**2, sc / K_R, sp)
    p_donor = p_surf.copy()
    n_hit = 0
    for i in range(len(ks)):
        key = (int(st[i] * K_R**2), round(sc[i] / K_R, 2), round(sp[i], 1))
        cand = [k for k in ref_ts
                if abs(k[0] - key[0]) <= 2 and abs(k[1] - key[1]) < 0.5
                and abs(k[2] - key[2]) < 0.5]
        if cand:
            p_donor[i] = ref_ts[cand[0]]
            n_hit += 1
    print(f'  도너 측정값 격자 매칭 {n_hit}/{len(ks)}점 '
          f'(나머지는 적합 면)')
    af_num = K_A * p_donor / sh

    res = {'_meta': {'k_a': K_A, 'k_r': K_R,
                     'inband_speeds': list(SC_INBAND),
                     'n_ops': int(len(ks))}}
    print(f"\n{'규칙':<12}{'단':<26}{'wMAE%':>8}{'인밴드':>8}{'외삽대':>8}")
    print('-' * 62)
    print(f"{'-':<12}{'A_uncorrected':<26}"
          f"{err_stats(sf, sh)['wmae_pct']:>8.2f}"
          f"{err_stats(sf[inband], sh[inband])['wmae_pct']:>8.2f}"
          f"{err_stats(sf[~inband], sh[~inband])['wmae_pct']:>8.2f}")
    for rule, af_zs in (('ratio', af_ratio), ('numerator', af_num)):
        r = rungs(af_zs, af_true, sh, sf, st, inband)
        res[rule] = {'anchors': r['anchors']}
        for tag, key in (('C_zeroshot', 'C'), ('F_zeroshot_plus3', 'F')):
            pred = r[key]
            res[rule][tag] = {
                'overall': err_stats(sf, pred),
                'inband': err_stats(sf[inband], pred[inband]),
                'outband': err_stats(sf[~inband], pred[~inband])}
            o = res[rule][tag]
            print(f'{rule:<12}{tag:<26}{o["overall"]["wmae_pct"]:>8.2f}'
                  f'{o["inband"]["wmae_pct"]:>8.2f}'
                  f'{o["outband"]["wmae_pct"]:>8.2f}')

    # 도너 손실의 상사 충실도 — numerator 경로가 인밴드에서 넘을 수 없는 바닥.
    d_in = np.abs(K_A * p_donor[inband] / sf[inband] - 1.0) * 100
    res['donor_loss_surface_inband'] = {
        'mean_abs_pct': round(float(d_in.mean()), 2),
        'p95_abs_pct': round(float(np.percentile(d_in, 95)), 2)}
    print(f'\n도너 손실 면 인밴드 충실도: mean|dev| '
          f'{d_in.mean():.2f}%  p95 {np.percentile(d_in, 95):.2f}%')

    os.makedirs(os.path.dirname(OUT_CMP), exist_ok=True)
    json.dump(res, open(OUT_CMP, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n저장:', OUT_CMP)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
