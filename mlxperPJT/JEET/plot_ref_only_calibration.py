"""Plot the SC Ref-only result from an audited pipeline JSON, without refitting."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True, help='Output stem, without suffix')
    args = ap.parse_args()
    data = json.loads(args.results.read_text(encoding='utf-8'))
    result = data['cases']['ref_only_public_hybrid']['SC']
    truth = np.asarray(result['truth_kW'])
    prediction = np.asarray(result['prediction_kW'])
    hybrid = np.asarray(result['hybrid_kW'])
    own = np.isin(np.arange(len(truth)), result['own_train_indices'])
    speed = np.array([r['target_speed_rpm']/1000 for r in data['source_mapping']['SC']])
    error = (prediction/truth-1)*100
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.65), constrained_layout=True)
    ax = axes[0]
    upper = max(truth.max(), prediction.max(), hybrid.max())*1.05
    ax.plot([0, upper], [0, upper], color='#6c7884', lw=.8, ls='--')
    ax.scatter(truth, hybrid, marker='x', c='#919ba5', s=15, lw=.8, label='Uncorrected')
    ax.scatter(truth[own], prediction[own], c='#276997', s=21, label='Calibration points')
    ax.scatter(truth[~own], prediction[~own], marker='s', facecolors='none',
               edgecolors='#be692c', s=24, label='Own-withheld points')
    ax.set(xlabel='Full-FEA AC winding loss [kW]', ylabel='Predicted AC winding loss [kW]',
           xlim=(0, upper), ylim=(0, upper))
    ax.legend(frameon=False, fontsize=8, loc='upper left')
    ax.grid(alpha=.15)
    ax = axes[1]
    for mask, color, marker, label in [(own, '#276997', 'o', 'Calibration points'),
                                      (~own, '#be692c', 's', 'Own-withheld points')]:
        # All points plotted at their actual speed, with no invented jitter.
        ax.scatter(speed[mask], error[mask], c=color, s=17, marker=marker, alpha=.65,
                   label=label)
    ax.axhline(0, color='#6c7884', lw=.8, ls='--')
    ax.set(xlabel='Speed [kRPM]', ylabel='Relative prediction error [%]',
           xticks=[2, 4, 8, 16], xlim=(1, 17))
    ax.grid(alpha=.15)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ('.pdf', '.png'):
        fig.savefig(args.out.with_suffix(suffix), dpi=220)
    plt.close(fig)


if __name__ == '__main__':
    main()
