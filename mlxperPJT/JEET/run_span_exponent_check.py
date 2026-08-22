# -*- coding: utf-8 -*-
"""앵커 속도의 AF 스팬을 p 제곱하면 저속 스팬이 되는가."""
import contextlib
import io
import sys

sys.path.insert(0, r'D:\KangDH\EveryMotor\_wt_jeet_repro\tools')
import numpy as np
import matplotlib
matplotlib.use('Agg')

from jeet_acloss_rbf.pipeline import AcLossPipeline

pl = AcLossPipeline()
print('  %-8s %8s %8s %7s   %s'
      % ('scale', 'span16k', 'span2k', 'p(2k)', 'span16k^p  vs  span2k'))
for s in ('Ref', 'HalfSC', 'SC'):
    with contextlib.redirect_stdout(io.StringIO()):
        ds = pl.load_dataset(s)
        m = pl.build_model(s)
    af = ds.f_ac_arr / ds.h_ac_arr

    def span(v):
        sel = (np.abs(ds.speeds_k - v) < .1) & (ds.irms_arr >= 50)
        return af[sel].max() / af[sel].min()

    s16, s2 = span(16.), span(2.)
    p2 = float(np.polyval(m.q_coeffs, 2.0))
    print('  %-8s %8.2f %8.2f %7.2f   %8.2f  vs %6.2f'
          % (s, s16, s2, p2, s16 ** p2, s2))
