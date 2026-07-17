"""SC Hybrid MS B — Figure 4 style method comparison plot."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

HERE = Path(__file__).resolve().parent
DATA = json.load(open(HERE / 'mesh_b_vs_mcad_sc_hybrid.json', encoding='utf-8'))
OUT = HERE.parents[0] / 'figures' / 'sc_hybrid_method_comparison_fig4.png'

# 920 A / 36 deg speed sweep (the 460 A and 54 deg cases are separate
# operating points, not part of this line)
rows36 = [r for r in DATA if r['phase'] == 36.0 and r['current'] == 920.0]
rows36.sort(key=lambda r: r['speed'])

speeds = np.array([r['speed'] for r in rows36])

def kw(key): return np.array([r[key] / 1e3 for r in rows36])

ts    = kw('ts_ac_W')
vlp   = kw('Volpe_G2p_W')
kim   = kw('Kim_KDE_W')
p24s  = kw('P24_solid_W')
p24c  = kw('P24_cuboid6_W')
mcad  = kw('mcad_prox_W')

fig, ax = plt.subplots(1, 1, figsize=(7, 5))

kw_opts = dict(linewidth=2, markersize=7)
ax.loglog(speeds, ts,   'b-o',  label='TS-FEA (Motor-CAD FullFEA)', **kw_opts)
ax.loglog(speeds, vlp,  'r--s', label='Volpe G2p (FEA elem B, MS)', **kw_opts)
ax.loglog(speeds, kim,  'C1-^', label='Kim KDE', **kw_opts)
ax.loglog(speeds, p24s, 'm:v',  label='P24 solid (/24 full)', **kw_opts, alpha=0.7)
ax.loglog(speeds, p24c, 'brown', label='P24 cub×6', linestyle=':', marker='D', **kw_opts, alpha=0.7)
ax.loglog(speeds, mcad, 'g-*',  label='MCAD Hybrid (eMag)', linewidth=2, markersize=10)

# Annotate Vlp/TS ratios
for spd, v, t in zip(speeds, vlp, ts):
    ax.annotate(f'Vlp/TS={v/t:.2f}', xy=(spd, v),
                xytext=(spd*1.05, v*1.15), fontsize=7.5, color='red')

ax.set_xlabel('Speed (rpm)', fontsize=12)
ax.set_ylabel('Proximity Loss (kW)', fontsize=12)
ax.set_title('SC AC Proximity Loss — Method Comparison\n(MS B source, 920 A, Phase=36°)', fontsize=12)
ax.legend(fontsize=8.5, loc='upper left')
ax.grid(True, which='both', alpha=0.3)
ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
ax.set_xticks(speeds)
ax.set_xticklabels([f'{s//1000}k' for s in speeds])

# AF table annotation
af_vals = [t/m for t, m in zip(ts, mcad)]
info = '\n'.join([f'{s//1000}k rpm: AF={af:.2f}' for s, af in zip(speeds, af_vals)])
ax.text(0.98, 0.05, f'AF = TS/MCAD\n{info}',
        transform=ax.transAxes, fontsize=8, ha='right', va='bottom',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

fig.tight_layout()
fig.savefig(OUT, dpi=150)
print('saved:', OUT)
plt.close()
