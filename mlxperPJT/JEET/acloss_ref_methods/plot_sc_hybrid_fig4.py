"""SC Hybrid MS B — Figure 4 style method comparison plot (all cases)."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

HERE = Path(__file__).resolve().parent
DATA = json.load(open(HERE / 'mesh_b_vs_mcad_sc_hybrid.json', encoding='utf-8'))
OUT = HERE.parents[0] / 'figures' / 'sc_hybrid_method_comparison_fig4.png'

# Split by phase
rows36 = sorted([r for r in DATA if abs(r['phase'] - 36.0) < 0.1 and abs(r['current'] - 920.0) < 1],
                key=lambda r: r['speed'])
rows54 = sorted([r for r in DATA if abs(r['phase'] - 54.0) < 0.1 and abs(r['current'] - 920.0) < 1],
                key=lambda r: r['speed'])

fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)

kw_opts = dict(linewidth=2, markersize=7)
COLORS = dict(ts='b', vlp='r', kim='C1', p24s='m', p24c='brown', mcad='g')

for ax, rows, phase_label in zip(axes, [rows36, rows54], ['36°', '54°']):
    if not rows:
        ax.set_title(f'Phase = {phase_label}\n(no data)')
        continue

    speeds = np.array([r['speed'] for r in rows])
    def kw(key): return np.array([r[key] / 1e3 for r in rows])

    ts   = kw('ts_ac_W')
    vlp  = kw('Volpe_G2p_W')
    kim  = kw('Kim_KDE_W')
    p24s = kw('P24_solid_W')
    p24c = kw('P24_cuboid6_W')
    mcad = kw('mcad_prox_W')

    ax.loglog(speeds, ts,   'b-o',  label='TS-FEA (Motor-CAD FullFEA)', **kw_opts)
    ax.loglog(speeds, vlp,  'r--s', label='Volpe G2p (FEA elem B, MS)', **kw_opts)
    ax.loglog(speeds, kim,  'C1-^', label='Kim KDE', **kw_opts)
    ax.loglog(speeds, p24s, 'm:v',  label='P24 solid (/24 full)', linewidth=1.5, markersize=6, alpha=0.6)
    ax.loglog(speeds, p24c, color='brown', linestyle=':', marker='D',
              label='P24 cub×6', linewidth=1.5, markersize=6, alpha=0.6)
    ax.loglog(speeds, mcad, 'g-*',  label='MCAD Hybrid (eMag)', linewidth=2, markersize=10)

    # Vlp/TS annotation
    for s, v, t in zip(speeds, vlp, ts):
        ax.annotate(f'{v/t:.2f}', xy=(s, v), xytext=(s*1.06, v*1.12),
                    fontsize=7.5, color='darkred')

    # AF box
    af_vals = [t/m for t, m in zip(ts, mcad)]
    info = '\n'.join([f'{int(s)//1000}k: AF={af:.2f}' for s, af in zip(speeds, af_vals)])
    ax.text(0.97, 0.05, f'AF=TS/MCAD\n{info}',
            transform=ax.transAxes, fontsize=7.5, ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_title(f'Phase = {phase_label}', fontsize=12)
    ax.set_xlabel('Speed (rpm)', fontsize=11)
    ax.set_ylabel('Proximity Loss (kW)', fontsize=11)
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, which='both', alpha=0.3)
    ax.set_xticks(speeds)
    ax.set_xticklabels([f'{int(s)//1000}k' for s in speeds])
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

fig.suptitle('SC AC Proximity Loss — Method Comparison (MS B source, 920 A)', fontsize=13, fontweight='bold')
fig.tight_layout()
fig.savefig(OUT, dpi=150)
print('saved:', OUT)
plt.close()
