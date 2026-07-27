# -*- coding: utf-8 -*-
"""Fig A.1 (fig:eddy_factors) — η축 재작도 (본문·캡션 정합판).

기존 eddy_factors_eta.pdf 는 속도축·점근선 없음으로 A.1 본문("η에 대한
표피·근접 인자와 두 점근선, 음영 η≈2–4")과 불일치했다. 본문 서술대로:

  (a) 표피 인자  φ(η) = η(sinh2η+sin2η)/(cosh2η−cos2η)
      + 소각 점근 1+(4/45)η⁴, 대각 점근 η
  (b) 무차원 근접 커널  ηK(η), K=(sinhη−sinη)/(coshη+cosη)
      + 소각 점근 η⁴/6, 대각 점근 η   (log-y)

그림 내부 텍스트 규칙: 패널 태그 '(a)','(b)'만, 식별은 범례·tex 캡션.
음영 = 헤어핀 실용 운전 범위 η ≈ 2–4.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = r"E:\KDH\Overleaf\JEET-2024_rev1\fig\eddy_factors_eta.pdf"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.linewidth": 0.6, "lines.linewidth": 0.9,
    "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03, "mathtext.fontset": "stix",
})
NAVY, ORANGE, GREEN_D, GRAY_M = "#1a3a5c", "#e65100", "#2e7d32", "#777777"


def main() -> int:
    eta = np.linspace(0.02, 5.0, 800)
    phi = eta * (np.sinh(2 * eta) + np.sin(2 * eta)) \
        / (np.cosh(2 * eta) - np.cos(2 * eta))
    etaK = eta * (np.sinh(eta) - np.sin(eta)) / (np.cosh(eta) + np.cos(eta))

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(7.0, 2.6))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.9, bottom=0.17,
                        wspace=0.26)

    for ax in (axA, axB):
        ax.axvspan(2, 4, color="#fff3d6", zorder=0)
        ax.set_xlim(0, 5)
        ax.set_xlabel(r"$\eta = h_c/\delta$")
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
        ax.set_axisbelow(True)

    # (a) 표피 인자
    axA.plot(eta, phi, "-", color=NAVY, lw=1.4, label=r"exact $\varphi(\eta)$")
    axA.plot(eta, 1 + 4 * eta**4 / 45, "--", color=ORANGE, lw=1.1,
             label=r"small-$\eta$: $1+\frac{4}{45}\eta^4$")
    axA.plot(eta, eta, ":", color=GREEN_D, lw=1.2,
             label=r"large-$\eta$: $\eta$")
    axA.set_ylim(0, 6)
    axA.set_ylabel(r"skin factor $\varphi(\eta)$")
    axA.legend(fontsize=6.8, frameon=False, loc="upper left")
    axA.set_title("(a)", fontsize=8.5, pad=3)
    axA.text(3.0, 0.35, r"hairpin range", fontsize=6.6, color="#8a6d1a",
             ha="center", style="italic")

    # (b) 무차원 근접 커널 (log-y)
    axB.plot(eta, etaK, "-", color=NAVY, lw=1.4,
             label=r"exact $\eta K(\eta)$")
    axB.plot(eta, eta**4 / 6, "--", color=ORANGE, lw=1.1,
             label=r"small-$\eta$: $\eta^4/6$")
    axB.plot(eta, eta, ":", color=GREEN_D, lw=1.2,
             label=r"large-$\eta$: $\eta$")
    axB.set_yscale("log")
    axB.set_ylim(1e-3, 2e2)
    axB.set_ylabel(r"proximity kernel $\eta\,K(\eta)$")
    axB.legend(fontsize=6.8, frameon=False, loc="upper left")
    axB.set_title("(b)", fontsize=8.5, pad=3)
    axB.text(3.0, 2.2e-3, r"hairpin range", fontsize=6.6, color="#8a6d1a",
             ha="center", style="italic")

    fig.savefig(OUT)
    plt.close(fig)
    # 본문 수치 검증: 점근 과대평가율
    for e0 in (1.05, 2.06, 4.10):
        i = np.argmin(np.abs(eta - e0))
        ov = (eta[i]**4 / 6) / etaK[i] - 1
        print(f"  η={e0}: 소각 점근 과대 {ov*100:+.0f}%")
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
