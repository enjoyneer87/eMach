# -*- coding: utf-8 -*-
"""오프라인 효율맵 잔차 2패널 --- 무보정 대 보정 (run_effmap_offline 후속).

  python run_effmap_offline_fig.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import numpy as np                                       # noqa: E402
import matplotlib                                        # noqa: E402
matplotlib.use("Agg")

from jeet_acloss_rbf.manuscript_figs import _journal_rc   # noqa: E402
from jeet_acloss_rbf.repro_env import fig_dir             # noqa: E402

NPZ = os.path.join(HERE, "map_exports", "e10", "effmaps",
                   "effmap_offline_SC.npz")
CLIP = 1.5


def main() -> int:
    plt = _journal_rc()
    D = np.load(NPZ)
    spd, tq, m = D["spd"] / 1e3, D["torque"], D["mask"]
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.5), sharey=True)
    tp = None
    for ax, key, lab in ((axes[0], "dH", "uncalibrated"),
                         (axes[1], "dC", "calibrated")):
        d = np.where(m, D[key], np.nan)
        tp = ax.pcolormesh(spd, tq, np.clip(d, -CLIP, CLIP), cmap="RdBu_r",
                           vmin=-CLIP, vmax=CLIP, shading="gouraud")
        ax.set_xlabel("speed [kRPM]", fontsize=8)
        ax.text(0.03, 0.94, "%s\nmean $|\\Delta\\eta|$ = %.2f %%p"
                % (lab, np.nanmean(np.abs(d))), transform=ax.transAxes,
                ha="left", va="top", fontsize=7,
                bbox=dict(boxstyle="round,pad=0.25", fc="w", ec="0.6",
                          lw=0.5, alpha=0.9))
        ax.tick_params(labelsize=7)
    axes[0].set_ylabel("torque [Nm]", fontsize=8)
    cb = fig.colorbar(tp, ax=axes, pad=0.015, extend="both")
    cb.set_label(r"$\eta_{model}-\eta_{Full\mathrm{-}FEA}$ [%p]", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    os.makedirs(fig_dir(), exist_ok=True)
    out = os.path.join(fig_dir(), "effmap_offline_dEta.pdf")
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out[:-4] + ".png", dpi=200, bbox_inches="tight")
    print("저장:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
