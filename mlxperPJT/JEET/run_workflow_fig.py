# -*- coding: utf-8 -*-
"""Fig(workflow) 스윔레인 재작도 v3 — 편집 원본 소실분 대체.

변경점 (세미나3 그림 단계):
  - 우하단 성능 수치 갱신: wMAE 0.6--1.2% -> 0.5--1.2% (헤드라인 B-통일 정합, 2026-07-30)
  - 우하단 성능 수치 재갱신: 0.5--1.2% -> 1.1--1.3% (단일 경로·전 부하점 96 기준, 2026-08-02)
  - 'Proposed' 라벨 통일: 방법 박스 "Proposed: Exponent Separable RBF"
  - 캡션 규칙: 그림 내부 텍스트는 박스 라벨(다이어그램 고유 요소)만.

산출: E:/KDH/Overleaf/JEET-2024_rev1/fig/proposed_framework_v3.pdf
"""
import os
import sys

import matplotlib

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = os.path.join(_FIGDIR, 'proposed_framework_v3.pdf')

LANES = [
    ("1. Reference FEA Build", "#f5f5f5", "#9e9e9e"),
    ("2. Geometric Scaling (SCL-M)", "#edf3fb", "#2c6fad"),
    ("3. Calibration & Performance Map", "#edf7ee", "#2e7d32"),
]
# (lane, row) -> (제목, 부제, 면색, 테두리색, 글자색)
BOXES = {
    (0, 0): ("Reference Model", "MS-FEA  ($k_r{=}1$)",
             "white", "#333333", "#111111"),
    (0, 1): ("Extract Slot Field", "$B_r,\\ B_\\theta$ homogenization",
             "white", "#333333", "#111111"),
    (0, 2): ("1-D Analytical", "Hybrid AC-loss model",
             "white", "#333333", "#111111"),
    (1, 0): ("Scale Geometry & Current", "$k_r = 1,\\ 1.5,\\ 2$",
             "#dbe8f7", "#2c6fad", "#153a5e"),
    (1, 1): ("Scale Fields & Circuits", "scaling law (Table 1)",
             "#dbe8f7", "#2c6fad", "#153a5e"),
    (1, 2): ("Baseline Scaled", "AC winding-loss map",
             "#dbe8f7", "#2c6fad", "#153a5e"),
    (2, 0): ("Sparse TS-FEA Sampling",
             "Ref donor: full band, 34 pts\nvariants: high band only,"
             " 24$+$3 pts",
             "#f6ecf9", "#8e4ba8", "#4d2461"),
    (2, 1): ("Proposed:\nExponent Separable RBF",
             "$AF = f(\\omega)\\,\\kappa(I_{rms},\\beta)^{p(\\omega)}$,"
             " kernel @ $\\omega_{max}$",
             "#e65100", "#a03800", "white"),
    (2, 2): ("Calibrated AC Loss\n& Efficiency Map",
             "wMAE 1.1–1.3%",
             "#2e7d32", "#1b4d1e", "white"),
}

LX = [0.035, 0.365, 0.695]          # 레인 좌측 x
LW = 0.27                            # 레인 폭
BY = [0.70, 0.42, 0.14]             # 행 y (박스 하단)
BH = 0.155


def box_xy(lane, row):
    return LX[lane] + LW / 2, BY[row] + BH / 2


def main() -> int:
    fig, ax = plt.subplots(figsize=(9.8, 4.9))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    for i, (title, bg, edge) in enumerate(LANES):
        ax.add_patch(FancyBboxPatch(
            (LX[i] - 0.012, 0.06), LW + 0.024, 0.86,
            boxstyle="round,pad=0.008,rounding_size=0.015",
            facecolor=bg, edgecolor=edge, linewidth=1.1, zorder=0))
        ax.text(LX[i] + LW / 2, 0.955, title, ha="center", va="center",
                fontsize=9.6, fontweight="bold", color=edge)

    for (lane, row), (t1, t2, fc, ec, tc) in BOXES.items():
        x, y = LX[lane], BY[row]
        ax.add_patch(FancyBboxPatch(
            (x, y), LW, BH,
            boxstyle="round,pad=0.006,rounding_size=0.02",
            facecolor=fc, edgecolor=ec, linewidth=1.4, zorder=2))
        cx = x + LW / 2
        two = "\n" in t1
        ax.text(cx, y + BH * (0.62 if two else 0.66), t1, ha="center",
                va="center", fontsize=9.8, fontweight="bold", color=tc,
                zorder=3, linespacing=1.05)
        ax.text(cx, y + BH * (0.20 if two else 0.28), t2, ha="center",
                va="center", fontsize=8.4, color=tc, zorder=3,
                linespacing=1.1)

    def arrow(p, q, color="#555555", ls="-", lw=1.5, rad=0.0):
        ax.add_patch(FancyArrowPatch(
            p, q, arrowstyle="-|>", mutation_scale=13, linewidth=lw,
            linestyle=ls, color=color, zorder=4,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=2, shrinkB=2))

    # 레인 내 수직 흐름
    for lane, color in ((0, "#333333"), (1, "#2c6fad"), (2, "#666666")):
        for row in (0, 1):
            cx = LX[lane] + LW / 2
            arrow((cx, BY[row]), (cx, BY[row + 1] + BH), color=color)

    # 레인 1 -> 2 (행별 수평)
    for row in range(3):
        arrow((LX[0] + LW, BY[row] + BH / 2),
              (LX[1], BY[row] + BH / 2), color="#2c6fad")
    # 레인 2 상단 -> 레인 3 상단 (TS-FEA 샘플링으로)
    arrow((LX[1] + LW, BY[0] + BH / 2), (LX[2], BY[0] + BH / 2),
          color="#2e7d32")
    # 상사 전달 (파선) : Scale Fields -> Proposed RBF
    arrow((LX[1] + LW, BY[1] + BH * 0.35),
          (LX[2], BY[1] + BH * 0.6), color="#2c6fad", ls="--", rad=0.12)
    ax.text((LX[1] + LW + LX[2]) / 2, BY[1] - 0.015,
            "similarity transfer\n"
            "$AF_{k_r} = AF_{Ref}(k_r^2\\omega,\\ I/k_r,\\ \\beta)$",
            ha="center", va="top", fontsize=8.6, color="#2c6fad",
            style="italic")
    # Baseline map (점선) -> Calibrated map
    arrow((LX[1] + LW, BY[2] + BH * 0.5),
          (LX[2], BY[2] + BH * 0.5), color="#2e7d32", ls=":", rad=-0.05)

    fig.savefig(OUT, bbox_inches="tight")
    plt.close(fig)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
