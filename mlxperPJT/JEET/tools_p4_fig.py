# -*- coding: utf-8 -*-
"""P4 판정 그림: (a) 과도 손실 시계열 A/B, (b) 증분 vs 커널 예측."""
import io
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(HERE, 'pwm_pilot_p4_run.json'), encoding='utf-8'))
tA = np.array(d['runA']['t_series']) * 1e3
pA = np.array(d['runA']['P_series']) / 1e3
tB = np.array(d['runB']['t_series']) * 1e3
pB = np.array(d['runB']['P_series']) / 1e3
v = d['verdict']

fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.2),
                         gridspec_kw={'width_ratios': [2.2, 1]})
ax = axes[0]
ax.plot(tA, pA, lw=0.8, color='tab:blue', label='fundamental only')
ax.plot(tB, pB, lw=0.8, color='tab:red', alpha=0.75, label='+10% tone at $4f_1$')
ax.axvspan(tA[len(tA) // 2], tA[-1], color='0.92', zorder=0)
ax.set_xlabel('time (ms)')
ax.set_ylabel('winding loss (kW)')
ax.legend(fontsize=7, loc='upper right')
ax = axes[1]
ax.bar([0, 1], [v['dP_period2'], v['dP_kernel']],
       color=['tab:red', 'tab:gray'], width=0.6)
ax.set_xticks([0, 1])
ax.set_xticklabels(['transient\n$\\Delta P$',
                    'kernel\n$P_{Fq}(4f_1)\\,(\\Delta I/I)^2$'], fontsize=7)
ax.set_ylabel('loss increment (W)')
ax.text(0, v['dP_period2'] + 12, '%.0f' % v['dP_period2'], ha='center', fontsize=8)
ax.text(1, v['dP_kernel'] + 12, '%.0f' % v['dP_kernel'], ha='center', fontsize=8)
ax.set_ylim(0, 1400)
ax.text(0.5, 0.94, 'ratio %.3f' % v['ratio_period2'], transform=ax.transAxes,
        ha='center', fontsize=9)
for ax, tag in zip(axes, 'ab'):
    ax.text(0.5, -0.30, '(%s)' % tag, transform=ax.transAxes, ha='center', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'fig', 'pwm_pilot_p4.png'), dpi=200,
            bbox_inches='tight')
print('fig saved')
