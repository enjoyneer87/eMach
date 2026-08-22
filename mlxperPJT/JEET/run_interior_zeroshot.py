# -*- coding: utf-8 -*-
"""내부 변형체(HalfSC)를 자체 Full-FEA 0점으로 예측한다.

결론이 "A variant between two calibrated ends of the k_r axis is predicted
with no Full-FEA of its own to about 4.5% full-map wMAE" 라고 적는 그 값이다.
도너는 Ref(k_r=1)와 SC(k_r=2), 목표는 HalfSC(k_r=1.5).  상사 사상은
AF_target(w, I, b) = AF_donor((k_d/k_t)^2 w, (k_t/k_d) I, b).
"""
import contextlib
import io
import sys

sys.path.insert(0, r'D:\KangDH\EveryMotor\_wt_jeet_repro\tools')
import numpy as np
import matplotlib
matplotlib.use('Agg')

from jeet_acloss_rbf.pipeline import AcLossPipeline

pl = AcLossPipeline()
KR = pl.cfg['k_r']
SPEEDS = (2.0, 4.0, 8.0, 16.0)


def wmae(f, pred, sel=None):
    if sel is None:
        sel = np.ones(len(f), bool)
    e = np.abs(pred - f)
    return float(100 * e[sel].sum() / f[sel].sum())


with contextlib.redirect_stdout(io.StringIO()):
    dt = pl.load_dataset('HalfSC')
    models = {s: pl.build_model(s) for s in ('Ref', 'SC')}

kt = KR['HalfSC']
f = dt.f_ac_arr
print(f'HalfSC 96점, 무보정 {wmae(f, dt.h_ac_arr):.2f}%\n')
print(f'  {"donor":18s} {"wMAE":>7s}  ' + '  '.join(f'{s:g}k' for s in SPEEDS))

preds = {}
for donor in ('Ref', 'SC'):
    kd = KR[donor]
    k = kt / kd                     # 목표/도너 — AF_t(w,I,b) = AF_d(k^2 w, I/k, b)
    af = models[donor].predict(dt.speeds_k * 1000.0 * k**2,
                               dt.irms_arr / k, dt.phase_arr)
    preds[donor] = dt.h_ac_arr * af
    row = '  '.join(f'{wmae(f, preds[donor], np.abs(dt.speeds_k-s)<0.1):5.2f}'
                    for s in SPEEDS)
    print(f'  {donor + " only":18s} {wmae(f, preds[donor]):6.2f}%  {row}')

# 혼합: 사상된 질의 속도가 도너의 스윕(2~16 kRPM) 안에 드는 쪽을 쓴다.
q_ref = dt.speeds_k * (kt / KR['Ref'])**2      # x2.25
q_sc = dt.speeds_k * (kt / KR['SC'])**2        # x0.5625
mix = np.where((q_ref >= 2.0 - 1e-6) & (q_ref <= 16.0 + 1e-6),
               preds['Ref'], preds['SC'])
print('  사상 질의:  Ref<-', np.unique(np.round(q_ref, 3)),
      ' SC<-', np.unique(np.round(q_sc, 3)))
row = '  '.join(f'{wmae(f, mix, np.abs(dt.speeds_k-s)<0.1):5.2f}'
                for s in SPEEDS)
print(f'  {"mixed":18s} {wmae(f, mix):6.2f}%  {row}')
print(f'  {"geometric mean":18s} '
      f'{wmae(f, np.sqrt(preds["Ref"] * preds["SC"])):6.2f}%')
