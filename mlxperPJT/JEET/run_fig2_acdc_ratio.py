# -*- coding: utf-8 -*-
"""Fig 2 (fig:prox_comparison, AC/DC 비) — 사례 운전점 마커판.

draw_figures.ipynb 셀 6의 스크립트판 + 저자 제안(2026-07-27):
사례 연구 그림들이 쓰는 운전점을 원(○)으로 표시해 그림 간 내비게이션 제공
  - Ref@16k  : Fig 1(전류 쏠림)·Fig 3(필드 검증) 공용  -> "Figs. 1, 3"
  - SC @16k  : Fig 1                                 -> "Fig. 1"
  - SC @ 4k  : Fig 3 (상사 대응 운전점)               -> "Fig. 3"
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.io import loadmat

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAT_PATH = (r"D:\KangDH\EveryMotor\eMach\mlxperPJT"
            r"\JEET_ACLoss_Comparison_20260609_223109.mat")
OUT = r"E:\KDH\Overleaf\JEET-2024_rev1\fig\ACDC_ratio_scaling.png"

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
# 사례 운전점 (모델, 속도 kRPM) — 그림 번호는 원고마다 달라 캡션이 설명
# (10p: crowding=Fig1/field=Fig3, rev5: Fig2/Fig11) -> 그림엔 원만.
CASE_MARKS = [("Ref", 16), ("SC", 16), ("SC", 4)]


def main() -> int:
    MAT = loadmat(MAT_PATH)
    spd = MAT["speeds_RPM"].ravel()
    acdc = {
        "Ref": MAT["ref_AC_DC_ratio_TS"].ravel(),
        "HalfSC": (MAT["halfsc_ts_ActiveOnly_kW"].ravel()
                   / MAT["halfsc_ts_DC_Active_kW"].ravel()[0]),
        "SC": MAT["sc_AC_DC_ratio_TS"].ravel(),
    }

    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    fig.subplots_adjust(left=0.13, right=0.97, top=0.96, bottom=0.16)

    for m, r in acdc.items():
        st = MODEL_STYLE[m]
        ax.plot(spd / 1000, r, "-", color=st["color"], marker=st["marker"],
                ms=4.5, lw=1.2, label=st["label"], zorder=4)
        ax.annotate(f"{r[-1]:.2f}", xy=(spd[-1] / 1000, r[-1]),
                    xytext=(-4, 5), textcoords="offset points",
                    fontsize=6.5, color=st["color"], ha="right",
                    fontweight="bold")

    # 사례 운전점 마커 (대응 그림은 각 원고 캡션이 \ref 로 설명)
    for m, sk in CASE_MARKS:
        i = int((spd / 1000 == sk).nonzero()[0][0])
        y = acdc[m][i]
        ax.plot([sk], [y], "o", ms=9.5, mfc="none", mec="#111111",
                mew=1.1, zorder=6)

    ax.axhline(1.0, color=GRAY_M, lw=0.8, ls="--", zorder=2)
    ax.text(6.6, 1.13, r"$P_{AC} = P_{DC}$", fontsize=6.5, color=GRAY_M,
            style="italic", va="bottom")
    ax.set_xlabel("Speed [kRPM]")
    ax.set_ylabel(r"AC/DC loss ratio  $P_{AC}\,/\,P_{DC}$")
    ax.set_xlim(1.5, 16.8)
    ax.set_ylim(0, 10.2)
    ax.set_xticks([2, 4, 8, 16])
    ax.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", fontsize=7, frameon=False)

    fig.savefig(OUT, dpi=300)
    plt.close(fig)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
