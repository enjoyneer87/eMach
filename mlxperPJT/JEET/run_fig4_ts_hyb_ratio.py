# -*- coding: utf-8 -*-
"""Fig 4 (fig:ts_hyb_ratio) — draw_figures.ipynb 셀 7의 스크립트판.

변경(2026-07-27, 그림 내부 텍스트 규칙): 패널 제목의 열거 설명을 제거하고
'(a)', '(b)' 태그만 남긴다 — 식별 설명은 tex 캡션이 담당.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAT_PATH = (r"D:\KangDH\EveryMotor\eMach\mlxperPJT"
            r"\JEET_ACLoss_Comparison_20260609_223109.mat")
OUT = r"E:\KDH\Overleaf\JEET-2024_rev1\fig\TS_Hybrid_ratio.png"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.linewidth": 0.6, "lines.linewidth": 0.9,
    "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03, "mathtext.fontset": "stix",
})
NAVY, GREEN_D, RED_D, GRAY_M = "#1a3a5c", "#2e7d32", "#b71c1c", "#777777"
MODEL_STYLE = {
    "Ref":    dict(color=NAVY, marker="o", label=r"Ref  ($k_r{=}1$)"),
    "HalfSC": dict(color=GREEN_D, marker="^", label=r"HalfSC  ($k_r{=}1.5$)"),
    "SC":     dict(color=RED_D, marker="s", label=r"SC  ($k_r{=}2$)"),
}


def main() -> int:
    MAT = loadmat(MAT_PATH)
    spd = MAT["speeds_RPM"].ravel()
    loss = {
        "Ref": (MAT["ref_ts_ActiveOnly_kW"].ravel(),
                MAT["ref_hybrid_Total_kW"].ravel()),
        "HalfSC": (MAT["halfsc_ts_ActiveOnly_kW"].ravel(),
                   MAT["halfsc_hybrid_Total_kW"].ravel()),
        "SC": (MAT["sc_ts_ActiveOnly_kW"].ravel(),
               MAT["sc_hybrid_Total_kW"].ravel()),
    }

    figB, (axL, axR) = plt.subplots(1, 2, figsize=(7.0, 2.8))
    figB.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.16,
                         wspace=0.28)

    for m, (ts, hyb) in loss.items():
        st = MODEL_STYLE[m]
        axL.plot(spd / 1000, ts, "-", color=st["color"], marker=st["marker"],
                 ms=4.5, lw=1.2, zorder=4, label=f"{m} TS-FEA")
        axL.plot(spd / 1000, hyb, "--", color=st["color"],
                 marker=st["marker"], ms=4.5, lw=1.0, mfc="white",
                 zorder=3, label=f"{m} Hybrid")
    axL.set_yscale("log")
    axL.set_xlabel("Speed [kRPM]")
    axL.set_ylabel(r"AC winding loss $P_{AC}$ [kW]")
    axL.set_xlim(1.5, 16.8)
    axL.set_xticks([2, 4, 8, 16])
    axL.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
    axL.set_axisbelow(True)
    axL.spines[["top", "right"]].set_visible(False)
    axL.legend(loc="lower right", fontsize=5.8, frameon=False, ncol=1,
               handlelength=2.2, labelspacing=0.25)
    axL.set_title("(a)", fontsize=8.5, pad=4)

    for m, (ts, hyb) in loss.items():
        st = MODEL_STYLE[m]
        ratio = ts / hyb
        axR.plot(spd / 1000, ratio, "-", color=st["color"],
                 marker=st["marker"], ms=4.5, lw=1.2, label=st["label"],
                 zorder=4)
        for x, v in zip(spd / 1000, ratio):
            axR.annotate(f"{v:.2f}", xy=(x, v), xytext=(0, 5),
                         textcoords="offset points", fontsize=6.0,
                         color=st["color"], ha="center")
    axR.axhline(1.0, color=GRAY_M, lw=0.8, ls="--", zorder=2)
    axR.text(15.8, 1.06, "ratio = 1 (no underestimation)", fontsize=6.0,
             color=GRAY_M, style="italic", ha="right", va="bottom")
    axR.set_xlabel("Speed [kRPM]")
    axR.set_ylabel(r"TS-FEA / Hybrid loss ratio  $P_{AC}^{TS}\,/\,P_{AC}^{HYB}$")
    axR.set_xlim(1.5, 16.8)
    axR.set_ylim(0.9, 3.1)
    axR.set_xticks([2, 4, 8, 16])
    axR.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
    axR.set_axisbelow(True)
    axR.spines[["top", "right"]].set_visible(False)
    axR.legend(loc="upper right", fontsize=7, frameon=False)
    axR.set_title("(b)", fontsize=8.5, pad=4)

    figB.savefig(OUT, dpi=300)
    plt.close(figB)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
