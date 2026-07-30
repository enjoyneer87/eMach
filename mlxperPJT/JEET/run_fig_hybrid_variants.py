# -*- coding: utf-8 -*-
"""부록 Fig B.1 — 하이브리드 근접 손실 평가 변형 비교 (Ref, 16 kRPM, 460 A).

line_sampled_hybrid_Ref.json (run_line_sampled_hybrid.py 산출)에서
정격 전류의 beta 스윕을 뽑아 한 장으로 비교한다:
  MCAD 내부 hybrid (추출값) / 표본선 재현(line) / 전면적 커널 4종.
그림 내부 텍스트 최소화 규칙: 제목 없음, 식별은 범례만.
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "map_exports", "e10", "Ref",
                   "line_sampled_hybrid_Ref_80C.json")
OUT = r"E:\KDH\Overleaf\JEET-2024_rev1\fig\hybrid_variants_compare.pdf"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5, "axes.linewidth": 0.6,
    "lines.linewidth": 1.0, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    "mathtext.fontset": "stix",
})

SERIES = [  # (key, label, color, style, marker)
    ("mcad_prox_W", "Hybrid analytical-FEA (Volpe et al.)", "#111111",
     "-", "o"),
    ("line_msq_P24_cuboid6", "Line-sampled /24, cuboid-6", "#b71c1c",
     "--", "s"),
    ("full_P24_cuboid6", "Full-area /24, cuboid-6", "#e65100", ":", "d"),
    ("line_msq_Volpe_G2p", "Line-sampled G$_2'$", "#1a3a5c", "--", "^"),
    ("full_Volpe_G2p", "Full-area $\\langle B^2\\rangle$ G$_2'$",
     "#2c6fad", ":", "v"),
    ("line_msq_P24c6_translim",
     "Line-sampled /24 c6 + transition cap (emulation)", "#2e7d32",
     "-", "s"),
]


def main() -> int:
    rows = json.load(open(SRC, encoding="utf-8"))["rows"]
    cur = max(r["current_A"] for r in rows)
    sel = sorted((r for r in rows if abs(r["current_A"] - cur) < 1e-6),
                 key=lambda r: r["phase_deg"])
    beta = np.array([r["phase_deg"] for r in sel])
    print(f"OP: {cur:g} A, beta {beta}")

    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for key, lbl, col, ls, mk in SERIES:
        y = np.array([r.get(key) or np.nan for r in sel]) / 1e3
        ax.plot(beta, y, ls, color=col, marker=mk, ms=3.2, label=lbl)
        print(f"  {key:22s} {np.round(y, 2)}")
    ax.set_xlabel(r"Current phase angle $\beta$ [deg]")
    ax.set_ylabel("Machine proximity loss [kW]")
    ax.set_xticks(beta)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=6.0, frameon=False, loc="best")
    fig.savefig(OUT)
    print("저장:", OUT)

    # 요약 비율 (부록 본문 인용용)
    mc = np.array([r["mcad_prox_W"] for r in sel])
    for key, lbl, *_ in SERIES[1:]:
        v = np.array([r.get(key) or np.nan for r in sel]) / mc
        print(f"  ratio {key:22s} mean {np.nanmean(v):.3f} "
              f"[{np.nanmin(v):.3f}~{np.nanmax(v):.3f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
