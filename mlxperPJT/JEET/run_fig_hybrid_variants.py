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
# 데이터 루트는 JEET_DATA_ROOT 로 덮어쓸 수 있다 (배포 레포/CI 용).
# 이 그림은 필드 아카이브가 아니라 아래 요약 JSON 두 개(합 87 KB)만 읽는다.
_DATA = os.environ.get("JEET_DATA_ROOT",
                       os.path.join(HERE, "map_exports", "e10"))
REF = os.path.join(_DATA, "Ref")
SRC = os.path.join(REF, "line_sampled_hybrid_Ref_80C.json")
SRC_TS = os.path.join(REF, "meshb_hybrid_losses_Ref.json")
# 2-D 자기 확산 BVP (식 (4)). bvp_ac_W 는 이미 AC 전량이므로
# 다른 계열과 달리 공통 표피를 더하지 않는다.
SRC_BVP = os.path.join(REF, "bvp_denominator_Ref.json")
BVP_STYLE = dict(color="#111111", ls="-.", marker="D", ms=2.8,
                 lw=1.1, zorder=3,
                 label="2-D frequency-domain BVP")
OUT = os.path.join(_FIGDIR, 'hybrid_variants_compare.pdf')
# 속도 패널 (b=36deg 고정, 2/4/8/16k) — subfloat (a) 용 별도 PDF
SRC_SPD = os.path.join(os.path.dirname(REF), 'Ref_spdsweep',
                       'line_sampled_hybrid_Ref_spdsweep_80C.json')
OUT_SPD = os.path.join(_FIGDIR, 'hybrid_variants_speed.pdf')
BETA_FIX = 36.0
SPD = 16000

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0, "axes.linewidth": 0.6,
    "lines.linewidth": 1.0, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    "mathtext.fontset": "stix",
})

# 범례는 자속 축약 방식을 반드시 함께 표기한다: 표본선 계열은 평균 후 제곱
# <B>^2 (생산 추출 모사), 전면적 계열은 제곱 후 평균 <B^2>. 둘은 같은 커널에서도
# 16~19% 벌어지므로, 표기가 없으면 "제곱 후 평균은 전면적분과 1.5% 이내"라는
# 부록 B 본문과 그림이 모순으로 읽힌다. (저자 지시 2026-08-02)
_MSQ = r"$\langle B\rangle^{2}$"     # 평균 후 제곱 — 표본선
_SQM = r"$\langle B^{2}\rangle$"     # 제곱 후 평균 — 전면적

SERIES = [  # (key, label, color, style, marker)
    ("mcad_prox_W", "Hybrid analytical-FEA (Volpe et al.)", "#111111",
     "-", "o"),
    ("line_msq_P24c6_translim",
     "Line-sampled " + _MSQ + " /24 c6 + transition cap (emulation)",
     "#2e7d32", "-", "s"),
    ("line_msq_P24_cuboid6", "Line-sampled " + _MSQ + " /24, cuboid-6",
     "#b71c1c", "--", "s"),
    ("full_P24_cuboid6", "Full-area " + _SQM + " /24, cuboid-6",
     "#e65100", ":", "d"),
    ("line_msq_Volpe_G2p", "Line-sampled " + _MSQ + " G$_2'$",
     "#1a3a5c", "--", "^"),
    ("full_Volpe_G2p", "Full-area " + _SQM + " G$_2'$",
     "#2c6fad", ":", "v"),
]


def _bvp_rows():
    if not os.path.exists(SRC_BVP):
        return None
    return json.load(open(SRC_BVP, encoding="utf-8"))["rows"]


def _bvp_at(br, spd, cur, ph):
    """2-D BVP 의 AC 전량 [kW]. 없으면 nan."""
    if br is None:
        return float("nan")
    m = [r for r in br if int(r["speed_rpm"]) == int(spd)
         and abs(r["current_A"] - cur) < 0.5
         and abs(r["phase_deg"] - ph) < 0.5]
    return float(m[0]["bvp_ac_W"]) / 1e3 if m else float("nan")


def main() -> int:
    rows = json.load(open(SRC, encoding="utf-8"))["rows"]
    brows = _bvp_rows()
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
    y_bvp = np.array([_bvp_at(brows, SPD, cur, b) for b in beta])
    if not np.all(np.isnan(y_bvp)):
        ax.plot(beta, y_bvp, **BVP_STYLE)
        print("  %-26s %s" % ("bvp_ac (2-D)", np.round(y_bvp, 2)))
        print("  %-26s %.2f~%.2f"
              % ("함의 AF (2-D BVP)", (ts / y_bvp).min(),
                 (ts / y_bvp).max()))
    ax.set_xlabel(r"Current phase angle $\beta$ [deg]")
    ax.set_ylabel("Machine AC winding loss [kW]")
    ax.set_xticks(beta)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=6.0, frameon=False, loc="upper center",
              bbox_to_anchor=(0.48, -0.16), ncol=2, columnspacing=0.5,
              handlelength=1.3)
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

    # ── (a) 속도 패널: b=36deg 고정, 변형별 총량 vs 속도 ────────────────
    if os.path.exists(SRC_SPD):
        rs = json.load(open(SRC_SPD, encoding="utf-8"))["rows"]
        rs = [r for r in rs if abs(r["phase_deg"] - BETA_FIX) < 0.5
              and abs(r["current_A"] - cur) < 1e-6]
        rs.sort(key=lambda r: r["speed_rpm"])
        spds = [r["speed_rpm"] for r in rs]

        def g2(spd, key):
            m = [x for x in mb if int(x["speed_rpm"]) == spd
                 and abs(x["current_A"] - cur) < 0.5
                 and abs(x["phase_deg"] - BETA_FIX) < 0.5]
            return float(m[0][key]) if m else np.nan

        sk2 = np.array([g2(s_, "mcad_skin_W") for s_ in spds]) / 1e3
        ts2 = np.array([g2(s_, "ts_ac_W") for s_ in spds]) / 1e3
        xs = np.array(spds) / 1000.0

        fig2, ax2 = plt.subplots(figsize=(3.5, 2.6))
        ax2.plot(xs, ts2, "-", color="#888888", lw=2.6, alpha=0.55,
                 zorder=1, label="TS-FEA (truth)")
        for key, lbl, col, ls, mk in SERIES:
            y = np.array([r.get(key) or np.nan for r in rs]) / 1e3 + sk2
            ax2.plot(xs, y, ls, color=col, marker=mk, ms=3.0, zorder=2)
        yb2 = np.array([_bvp_at(brows, s_, cur, BETA_FIX)
                        for s_ in spds])
        if not np.all(np.isnan(yb2)):
            ax2.plot(xs, yb2, **BVP_STYLE)
        ax2.set_xscale("log")
        ax2.set_yscale("log")
        ax2.set_xticks([2, 4, 8, 16])
        ax2.set_xticklabels(["2", "4", "8", "16"])
        ax2.minorticks_off()
        ax2.set_xlabel("Speed [kRPM]")
        ax2.set_ylabel("Machine AC winding loss [kW]")
        ax2.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
        ax2.set_axisbelow(True)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        fig2.savefig(OUT_SPD)
        plt.close(fig2)
        print("저장:", OUT_SPD)
    else:
        print("(속도 스윕 JSON 없음 — (a) 패널 생략:", SRC_SPD, ")")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
