# -*- coding: utf-8 -*-
"""e10 하모닉 응답 시각화 — e10_harmonic_response.py 산출(npz) → NVH 요약 그림.

패널:
  (1) 모달 스펙트럼 vs 가진 차수 주파수(수직선) — 공진 근접도 한눈에
  (2) 차수별 OD 최대/평균 반경변위 진폭 막대
  (3) 지배 차수의 OD 운전변형형상(ODS): 미드스팬 링의 |u_r|(θ) 극좌표 + 공간차수 FFT
"""
from __future__ import annotations

import os
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
NPZ = os.path.join(HERE, "data", "e10_harmonic_result.npz")
OUT = os.path.join(HERE, "data", "e10_harmonic_nvh.png")
ZC = 0.5 * (-0.2075 + -0.0575)


def main():
    d = np.load(NPZ, allow_pickle=False)
    freqs = d["freqs_modal"]; orders = list(d["orders"]); f_elec = float(d["f_elec"])
    rpm = float(d["rpm"])
    elastic = freqs[freqs > 1.0]

    fig = plt.figure(figsize=(16.5, 5.6))
    fig.suptitle(f"e10 stator NVH — tooth remote forces (48 pilots+RBE3), "
                 f"{rpm:.0f} rpm, f_elec={f_elec:.0f} Hz", fontsize=13.5,
                 fontweight="bold")

    # (1) 모드 vs 가진
    ax1 = fig.add_subplot(1, 3, 1)
    ax1.vlines(elastic, 0, 1, color="#7f9fb8", lw=1.2, label="stator modes (free-free)")
    for i, k in enumerate(orders):
        fx = k * f_elec
        ax1.vlines(fx, 0, 1, color="#d0342c", lw=2)
        ax1.text(fx, 1.02 + 0.05 * (i % 2), f"k={k}\n{fx:.0f}Hz", color="#d0342c",
                 ha="center", fontsize=8.5)
    ax1.set_xlim(0, max(elastic.max(), max(orders) * f_elec) * 1.05)
    ax1.set_ylim(0, 1.18); ax1.set_yticks([])
    ax1.set_xlabel("frequency [Hz]")
    ax1.set_title("modes vs excitation orders"); ax1.legend(fontsize=8, loc="lower right")

    # (2) 차수별 응답 크기
    ax2 = fig.add_subplot(1, 3, 2)
    umax, umean, labels = [], [], []
    for k in orders:
        xyz = d[f"k{k}_xyz"]; U = d[f"k{k}_U"]
        th = np.arctan2(xyz[:, 1], xyz[:, 0])
        ur = U[:, 0] * np.cos(th) + U[:, 1] * np.sin(th)     # 복소 반경변위
        umax.append(np.abs(ur).max() * 1e6)                  # µm
        umean.append(np.abs(ur).mean() * 1e6)
        labels.append(f"k={k}\n{k*f_elec:.0f}Hz")
    x = np.arange(len(orders))
    ax2.bar(x - 0.18, umax, 0.36, color="#d0342c", label="max |u_r|")
    ax2.bar(x + 0.18, umean, 0.36, color="#e8a09b", label="mean |u_r|")
    for xi, v in zip(x, umax):
        ax2.text(xi - 0.18, v, f"{v:.3g}", ha="center", va="bottom", fontsize=8.5)
    ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel("stator OD radial displacement [µm]")
    ax2.set_title("response per force order"); ax2.legend(fontsize=8.5)
    ax2.grid(axis="y", alpha=0.3)

    # (3) 지배 차수 ODS
    kdom = orders[int(np.argmax(umax))]
    xyz = d[f"k{kdom}_xyz"]; U = d[f"k{kdom}_U"]
    th = np.arctan2(xyz[:, 1], xyz[:, 0])
    ur = U[:, 0] * np.cos(th) + U[:, 1] * np.sin(th)
    mid = np.abs(xyz[:, 2] - ZC) < 0.008
    tm, um = th[mid], np.abs(ur[mid])
    o = np.argsort(tm); tm, um = tm[o], um[o]
    # 공간차수 FFT (균일각 보간)
    tg = np.linspace(-np.pi, np.pi, 256, endpoint=False)
    ug = np.interp(tg, tm, um, period=2 * np.pi)
    spec = np.abs(np.fft.rfft(ug - ug.mean())) / len(ug) * 2
    ax3 = fig.add_subplot(1, 3, 3, projection="polar")
    ax3.plot(tm, um * 1e6, ".", ms=2.5, color="#d0342c")
    n_dom = int(np.argmax(spec[1:20]) + 1)
    ax3.set_title(f"ODS @ k={kdom} ({kdom*f_elec:.0f} Hz), mid-span ring\n"
                  f"dominant circumferential order n={n_dom}", fontsize=10)
    ax3.set_rlabel_position(135)

    fig.text(0.5, -0.02,
             "Stator core only (MAT1), free-free, isotropic E=185 GPa (lamination 1st approx). "
             "Forces: Motor-CAD multiforce tooth harmonics via per-tooth pilot+RBE3 (torsor moments N/A from lumped export).",
             ha="center", fontsize=8, color="#555")
    fig.tight_layout(rect=[0, 0.02, 1, 0.93])
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    print("saved", OUT)
    print(f"dominant: k={kdom} @ {kdom*f_elec:.0f} Hz, max|u_r|={max(umax):.3g} µm, "
          f"circ. order n={n_dom}")


if __name__ == "__main__":
    main()
