# -*- coding: utf-8 -*-
"""Fig 2 (fig:prox_comparison, AC/DC 비) — 사례 운전점 마커판.

draw_figures.ipynb 셀 6의 스크립트판 + 저자 제안(2026-07-27):
사례 연구 그림들이 쓰는 운전점을 원(○)으로 표시해 그림 간 내비게이션 제공.

저자 결정(2026-08-15, Drive 댓글): sec23 재편으로 전류 쏠림 그림이 빠지면서
필드 검증(현 Fig 2, 구 Fig 3)의 상사쌍 운전점만 남긴다
  - Ref@16k : Fig 2 (필드 검증, 기준 모델)   -> "Fig. 2"
  - SC @ 4k : Fig 2 (상사 대응 운전점)       -> "Fig. 2"
"""
import os
import sys

import matplotlib

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.io import loadmat

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
# 데이터 루트는 JEET_DATA_ROOT 로 덮어쓸 수 있다 (배포 레포/CI 용).
_DATA = os.environ.get('JEET_DATA_ROOT',
                       os.path.join(HERE, 'map_exports', 'e10'))
# 이 .mat 은 e10 트리가 아니라 그 부모(배포 레포의 data/)에 놓인다.
MAT_NAME = 'JEET_ACLoss_Comparison_20260609_223109.mat'
_MAT_CAND = os.path.join(os.path.dirname(os.path.abspath(_DATA)), MAT_NAME)
MAT_PATH = _MAT_CAND if os.path.exists(_MAT_CAND) else (
    r"D:\KangDH\EveryMotor\eMach\mlxperPJT"
    r"\JEET_ACLoss_Comparison_20260609_223109.mat")
OUT = os.path.join(_FIGDIR, 'ACDC_ratio_scaling.png')

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
# 사례 운전점 (모델, 속도 kRPM, 라벨, 정렬, 오프셋 pt).
#
# ⚠️ 라벨의 그림 번호는 **원고마다 다르다.** 아래는 10p(KO/EN) 기준이며,
#    rev5 는 같은 그림이 Fig 2(전류 쏠림)·Fig 11(필드 검증)이다. rev5 용으로
#    다시 뽑을 때는 JEET_FIG2_LABELS 로 덮어쓸 것 —
#      set JEET_FIG2_LABELS=Figs. 2, 11|Fig. 2|Fig. 11
#    빈 문자열을 주면 라벨 없이 원만 그린다(종전 동작).
# 전류 집중 그림이 EN 에 복원되면서(세미나 6) 필드 검증 그림이 Fig 3 이 되었다.
# KO 는 그 그림을 지운 적이 없어 원래부터 Fig 3 이었다 — 이제 두 원고가 같다.
_DEF_LABELS = ("Fig. 3", "Fig. 3")
_lab = os.environ.get("JEET_FIG2_LABELS")
LABELS = tuple(_lab.split("|")) if _lab is not None else _DEF_LABELS

# ha 는 텍스트의 어느 끝을 오프셋 지점에 고정할지다 — 오른쪽으로 뻗게 하려면
# 'left'(왼쪽 끝 고정), 왼쪽으로 뻗게 하려면 'right'.
CASE_MARKS = [
    # Ref@16k 와 SC@4k 는 상사쌍이라 비가 1.14 / 1.16 으로 겹친다.
    ("Ref", 16, "left", (9, 6)),      # +6pt: P_AC=P_DC 점선을 비켜 간다
    ("SC", 4, "right", (-9, 6)),
]


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

    # 사례 운전점 마커 + 대응 그림 라벨
    for (m, sk, side, off), lab in zip(CASE_MARKS, LABELS):
        i = int((spd / 1000 == sk).nonzero()[0][0])
        y = acdc[m][i]
        ax.plot([sk], [y], "o", ms=9.5, mfc="none", mec="#111111",
                mew=1.1, zorder=6)
        if lab:
            ax.annotate(lab, xy=(sk, y), xytext=off,
                        textcoords="offset points", fontsize=6.5,
                        color="#111111", ha=side, va="center", zorder=7)

    ax.axhline(1.0, color=GRAY_M, lw=0.8, ls="--", zorder=2)
    ax.text(6.6, 1.13, r"$P_{AC} = P_{DC}$", fontsize=6.5, color=GRAY_M,
            style="italic", va="bottom")
    ax.set_xlabel("Speed [kRPM]")
    ax.set_ylabel(r"AC/DC loss ratio  $P_{AC}\,/\,P_{DC}$")
    ax.set_xlim(1.5, 18.6)   # 16 kRPM 라벨 자리
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
