# -*- coding: utf-8 -*-
"""Fig 12 교체 3패널 (저자 지정 구성 2026-08-26).

  (a) 보정 하이브리드 효율맵 eta_cal
  (b) 무보정 하이브리드 - Full-FEA 잔차
  (c) 보정 하이브리드 - Full-FEA 잔차

데이터는 run_effmap_shaft.py --full 의 자체 연산 결과다.  세 손실 모델이
각자 자기 궤적을 풀었고, 비-AC 손실 북키핑은 공유한다.

  python run_effmap_cal_fig.py
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
                   "effmap_shaft_SC.npz")
CLIP = 1.5


def _parula():
    """MATLAB parula 근사 LUT --- 기존 Fig 12 의 Δη 패널과 색을 맞춘다.

    matplotlib 에는 parula 가 없다.  9개 앵커 선형 보간이면 지면에서
    구분이 안 되는 수준이다."""
    from matplotlib.colors import LinearSegmentedColormap
    anchors = [(0.2422, 0.1504, 0.6603), (0.2810, 0.3228, 0.9579),
               (0.1786, 0.5289, 0.9682), (0.0689, 0.6948, 0.8394),
               (0.2161, 0.7843, 0.5923), (0.6720, 0.7793, 0.2227),
               (0.9970, 0.7659, 0.2199), (0.9769, 0.9839, 0.0805),
               (0.9763, 0.9831, 0.0538)]
    return LinearSegmentedColormap.from_list("parula", anchors, N=256)


def main() -> int:
    plt = _journal_rc()
    D = np.load(NPZ)
    sp = D["speeds"] / 1e3                    # (n_s,)
    TQ = D["targets"]                         # (n_t, n_s)
    X = np.broadcast_to(sp, TQ.shape)
    eC, eH, eT = D["cal_eta"], D["hybrid_eta"], D["truth_eta"]
    dH = np.where(np.isfinite(eH) & np.isfinite(eT), (eH - eT) * 100, np.nan)
    dC = np.where(np.isfinite(eC) & np.isfinite(eT), (eC - eT) * 100, np.nan)

    fig, axes = plt.subplots(1, 3, figsize=(6.9, 2.15), sharey=True)

    # 컬러맵·등고선 규약은 기존 Fig 12(plotFig15Effmaps.m)를 따른다 ---
    # 효율 jet + 등고선 [80 84 88 90 92..98], 라벨은 92/94/97 만.
    lv = [80, 84, 88, 90, 92, 93, 94, 95, 96, 97, 98]
    a0 = axes[0].pcolormesh(X, TQ, np.where(np.isfinite(eC), eC, np.nan)
                            * 100, cmap="jet", vmin=80, vmax=98,
                            shading="gouraud")
    cs = axes[0].contour(X, TQ, eC * 100, levels=lv, colors="k",
                         linewidths=0.4)
    axes[0].clabel(cs, levels=[92, 94, 97], fontsize=6, fmt="%g")
    # 컬러바는 상단, 라벨은 바 옆 --- Fig 12 MATLAB 판의 저자 규약
    # (2026-08-21)을 따른다.  위에 두면 세로 한 줄을 통째로 먹는다.
    cb0 = fig.colorbar(a0, ax=axes[0], location="top", pad=0.04,
                       fraction=0.09, aspect=18)
    cb0.ax.tick_params(labelsize=6.5)
    cb0.ax.text(-0.04, 0.5, r"$\eta_{cal}$ [%]", transform=cb0.ax.transAxes,
                ha="right", va="center", fontsize=7.5)

    tp = None
    for ax, d, lab in ((axes[1], dH, "uncalibrated"),
                       (axes[2], dC, "calibrated")):
        tp = ax.pcolormesh(X, TQ, np.clip(d, -CLIP, CLIP), cmap=_parula(),
                           vmin=-CLIP, vmax=CLIP, shading="gouraud")
        ax.text(0.97, 0.94, "mean $|\\Delta\\eta|$ = %.2f %%p"
                % np.nanmean(np.abs(d)), transform=ax.transAxes,
                ha="right", va="top", fontsize=7,
                bbox=dict(boxstyle="round,pad=0.25", fc="w", ec="0.6",
                          lw=0.5, alpha=0.9))
    cb = fig.colorbar(tp, ax=[axes[1], axes[2]], location="top", pad=0.04,
                      fraction=0.09, aspect=36, extend="both")
    cb.ax.tick_params(labelsize=6.5)
    cb.ax.text(1.02, 0.5, r"$\Delta\eta$ [%p]", transform=cb.ax.transAxes,
               ha="left", va="center", fontsize=7.5)

    for ax, tag in zip(axes, "abc"):
        ax.set_xlabel("speed [kRPM]", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_xlim(0.5, 16)
        ax.text(0.5, -0.34, "(%s)" % tag, transform=ax.transAxes,
                ha="center", va="top", fontsize=8)
    axes[0].set_ylabel("shaft torque [Nm]", fontsize=8)

    os.makedirs(fig_dir(), exist_ok=True)
    out = os.path.join(fig_dir(), "effmap_cal_compare.pdf")
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out[:-4] + ".png", dpi=200, bbox_inches="tight")
    print("저장:", out)
    for lab, d in (("uncal", dH), ("cal", dC)):
        print("  %-6s mean|d| %.3f  signed %+.3f  p95 %.3f [%%p]"
              % (lab, np.nanmean(np.abs(d)), np.nanmean(d),
                 np.nanpercentile(np.abs(d), 95)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
