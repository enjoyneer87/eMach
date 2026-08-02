# -*- coding: utf-8 -*-
"""부록 Fig B.1 — 하이브리드 평가 변형 비교 (Ref, 16 kRPM, 460 A).

각 변형은 근접 커널·샘플링만 다르고 표피 성분은 공통이므로, 공통 표피를 더해
**총량**으로 맞추면 TS-FEA 진리값과 같은 축에서 비교된다. 그러면 각 분모가
함의하는 AF( = TS / 변형총량 )까지 한 장에서 읽힌다 — 분모 상대성의 직접 증거.

그림 내부 텍스트 최소화 규칙: 제목 없음, 식별은 범례만.
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "map_exports", "e10", "Ref")
SRC = os.path.join(REF, "line_sampled_hybrid_Ref_80C.json")
SRC_TS = os.path.join(REF, "meshb_hybrid_losses_Ref.json")
OUT = os.path.join(_FIGDIR, 'hybrid_variants_compare.pdf')
SPD = 16000

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
    ("line_msq_P24c6_translim",
     "Line-sampled /24 c6 + transition cap (emulation)", "#2e7d32",
     "-", "s"),
    ("line_msq_P24_cuboid6", "Line-sampled /24, cuboid-6", "#b71c1c",
     "--", "s"),
    ("full_P24_cuboid6", "Full-area /24, cuboid-6", "#e65100", ":", "d"),
    ("line_msq_Volpe_G2p", "Line-sampled G$_2'$", "#1a3a5c", "--", "^"),
    ("full_Volpe_G2p", "Full-area $\\langle B^2\\rangle$ G$_2'$",
     "#2c6fad", ":", "v"),
]


def main() -> int:
    rows = json.load(open(SRC, encoding="utf-8"))["rows"]
    mb = json.load(open(SRC_TS, encoding="utf-8"))
    if isinstance(mb, dict):
        mb = mb.get("records", mb.get("rows"))

    cur = max(r["current_A"] for r in rows)
    sel = sorted((r for r in rows if abs(r["current_A"] - cur) < 1e-6),
                 key=lambda r: r["phase_deg"])
    beta = np.array([r["phase_deg"] for r in sel])

    def mb_get(b, key):
        m = [r for r in mb if int(r["speed_rpm"]) == SPD
             and abs(r["current_A"] - cur) < 0.5
             and abs(r["phase_deg"] - b) < 0.5]
        return float(m[0][key]) if m else np.nan

    skin = np.array([mb_get(b, "mcad_skin_W") for b in beta]) / 1e3
    ts = np.array([mb_get(b, "ts_ac_W") for b in beta]) / 1e3
    print("OP: %g A, %d kRPM, beta %s" % (cur, SPD / 1000, beta))
    print("공통 표피 %.3f kW (β 무관), TS 총 AC %.1f~%.1f kW"
          % (skin[0], ts.min(), ts.max()))

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    # TS 진리값 — 굵은 회색 밴드로 배경에 먼저
    ax.plot(beta, ts, "-", color="#888888", lw=2.6, alpha=0.55, zorder=1,
            label="TS-FEA (truth)")
    tot = {}
    for key, lbl, col, ls, mk in SERIES:
        y = np.array([r.get(key) or np.nan for r in sel]) / 1e3 + skin
        tot[key] = y
        ax.plot(beta, y, ls, color=col, marker=mk, ms=3.0, label=lbl,
                zorder=2)
        print("  %-26s %s" % (key, np.round(y, 2)))
    ax.set_xlabel(r"Current phase angle $\beta$ [deg]")
    ax.set_ylabel("Machine AC winding loss [kW]")
    ax.set_xticks(beta)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=5.6, frameon=False, loc="upper center",
              bbox_to_anchor=(0.48, -0.16), ncol=2, columnspacing=1.0,
              handlelength=2.2)
    fig.savefig(OUT)
    print("저장:", OUT)

    # 부록 본문 인용용 — 근접 비(종전 사다리)와 함의 AF
    mc = np.array([r["mcad_prox_W"] for r in sel])
    print("\n[근접 비 = 변형/해석-FEA]")
    for key, lbl, *_ in SERIES[1:]:
        v = np.array([r.get(key) or np.nan for r in sel]) / mc
        print("  %-26s mean %.3f [%.3f~%.3f]"
              % (key, np.nanmean(v), np.nanmin(v), np.nanmax(v)))
    print("\n[함의 AF = TS / 변형총량]")
    for key, lbl, *_ in SERIES:
        af = ts / tot[key]
        print("  %-26s %.2f~%.2f  (스윙 %.1f배)"
              % (key, af.min(), af.max(), af.max() / af.min()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
