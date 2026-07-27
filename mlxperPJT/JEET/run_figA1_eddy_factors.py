# -*- coding: utf-8 -*-
"""Fig A.1 (fig:eddy_factors) — 속도축 판 + η 정보 (저자 제안 2026-07-27).

기존(속도축, Ref/SC 인자 + SC/Ref 비 적축) 구조를 유지하면서:
  - 초록 점선 = 대응 η(s) 곡선. η 는 두 인자의 **대각 점근선 그 자체**이므로
    곡선 하나가 "η 정보"와 "점근선" 역할을 겸한다.
  - (b)에 소각(f²) 점근 η⁴/6 병기 — 저속 멱법칙과 전환 이탈이 함께 보인다.
  - 상단 보조 x축 = η_Ref 눈금 (η_SC = 2 η_Ref).
  - 사례 운전점 도트: Ref@16k(η=2.06), SC@4k(η=2.06), SC@16k(η=4.12).
  - 적축(우) = SC/Ref 비, 가이드라인 k_r⁴=16(저속)·k_r=2(고속 극한).

η 앵커: 본문 수치 η_Ref(16 kRPM)=2.06 -> η_Ref(s)=2.06·√(s/16), η_SC=2η_Ref.
그림 내부 텍스트 규칙: 태그 (a),(b)만, 식별은 범례·캡션.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = r"E:\KDH\Overleaf\JEET-2024_rev1\fig\eddy_factors_eta.pdf"
ETA_REF_16K = 2.06

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.linewidth": 0.6, "lines.linewidth": 0.9,
    "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03, "mathtext.fontset": "stix",
})
NAVY, ORANGE, GREEN_D, RED_D, GRAY_M = ("#1a3a5c", "#e65100", "#2e7d32",
                                        "#b71c1c", "#777777")


def phi(e):
    return e * (np.sinh(2 * e) + np.sin(2 * e)) \
        / (np.cosh(2 * e) - np.cos(2 * e))


def etaK(e):
    return e * (np.sinh(e) - np.sin(e)) / (np.cosh(e) + np.cos(e))


def main() -> int:
    s = np.linspace(0.3, 20.0, 600)                    # kRPM
    er = ETA_REF_16K * np.sqrt(s / 16.0)               # η_Ref(s)
    es = 2.0 * er                                       # η_SC(s)

    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.7))
    fig.subplots_adjust(left=0.07, right=0.93, top=0.82, bottom=0.17,
                        wspace=0.42)

    cases = [("(a)", phi, (0, 6.2), "skin factor $\\varphi$"),
             ("(b)", etaK, (0, 6.2), "proximity kernel $\\eta K(\\eta)$")]
    for ax, (tag, fn, ylim, ylab) in zip(axs, cases):
        yr, ys = fn(er), fn(es)
        ax.plot(s, yr, "-", color=NAVY, lw=1.3, label="Ref ($k_r{=}1$)")
        ax.plot(s, ys, "-.", color=NAVY, lw=1.3, label="SC ($k_r{=}2$)")
        # η 곡선 = 대각 점근선 겸용
        ax.plot(s, er, ":", color=GREEN_D, lw=1.1,
                label=r"$\eta$ (large-$\eta$ asym.)")
        ax.plot(s, es, ":", color=GREEN_D, lw=1.1)
        if tag == "(b)":
            ax.plot(s, er**4 / 6, "--", color=ORANGE, lw=0.9,
                    label=r"small-$\eta$: $\eta^4/6$ ($\propto f^2$)")
            ax.plot(s, es**4 / 6, "--", color=ORANGE, lw=0.9)
        # 사례 운전점 도트
        for e0, sk, lbl, off in ((ETA_REF_16K, 16, "Ref 16k", (-2, 7)),
                                 (ETA_REF_16K, 4, "SC 4k", (8, -11)),
                                 (2 * ETA_REF_16K, 16, "SC 16k", (-14, 6))):
            y0 = fn(np.array([e0]))[0]
            ax.plot([sk], [y0], "o", ms=7.5, mfc="none", mec="#111111",
                    mew=1.0, zorder=6)
            ax.annotate(lbl, xy=(sk, y0), xytext=off,
                        textcoords="offset points", fontsize=6.0,
                        style="italic", ha="center", zorder=6)
        ax.set_xlim(0, 20)
        ax.set_ylim(*ylim)
        ax.set_xlabel("Rotational speed [kRPM]")
        ax.set_ylabel(ylab)
        ax.set_title(tag, fontsize=8.5, pad=3)
        ax.yaxis.grid(True, linestyle=":", linewidth=0.45, color="#cccccc")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)

        # 우측 적축: SC/Ref 비 + k_r⁴/k_r 가이드
        ax2 = ax.twinx()
        ax2.plot(s, ys / yr, color=RED_D, lw=1.0)
        ax2.axhline(16, color=RED_D, lw=0.6, ls=":", alpha=0.7)
        ax2.axhline(2, color=RED_D, lw=0.6, ls=":", alpha=0.7)
        ax2.set_ylim(0, 17.5)
        ax2.set_ylabel("SC / Ref ratio", color=RED_D, fontsize=7.5)
        ax2.tick_params(axis="y", colors=RED_D, labelsize=7)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_color(RED_D)
        if tag == "(b)":
            ax2.annotate(r"$k_r^4{=}16$", xy=(19.6, 16), xytext=(0, 3),
                         textcoords="offset points", fontsize=6.0,
                         color=RED_D, ha="right")
            ax2.annotate(r"$k_r{=}2$", xy=(19.6, 2), xytext=(0, 3),
                         textcoords="offset points", fontsize=6.0,
                         color=RED_D, ha="right")

        # 상단 보조축: η_Ref 눈금
        sec = ax.secondary_xaxis(
            "top",
            functions=(lambda x: ETA_REF_16K * np.sqrt(np.maximum(x, 0)
                                                       / 16.0),
                       lambda e: 16.0 * (e / ETA_REF_16K) ** 2))
        sec.set_xticks([0.5, 1.0, 1.5, 2.0])
        sec.set_xlabel(r"$\eta_{Ref}$  ($\eta_{SC}=2\,\eta_{Ref}$)",
                       fontsize=7.2)
        sec.tick_params(labelsize=6.8)

        if tag == "(a)":
            ax.legend(fontsize=6.2, frameon=False, loc="upper left")
        else:
            ax.legend(fontsize=6.2, frameon=False, loc="upper left")

    fig.savefig(OUT)
    plt.close(fig)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
