# -*- coding: utf-8 -*-
"""e10 하우징 포함 vs 스테이터 단독 비교 viz.

패널:
  (1) 모달 스펙트럼 비교: 스테이터 단독 vs +하우징 (모드 시프트/신규 모드)
  (2) 차수별 응답: 스테이터OD(단독) vs 스테이터OD(+하우징) vs 하우징 외면
  (3) 하우징 외면 ERP vs 단독 스테이터 ERP (dB)
"""
from __future__ import annotations

import os
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
NPZ_S = os.path.join(HERE, "data", "e10_harmonic_result.npz")   # 스테이터 단독
NPZ_H = os.path.join(HERE, "data", "e10_housing_result.npz")    # +하우징
OUT = os.path.join(HERE, "data", "e10_housing_compare.png")
RHO0, C0 = 1.204, 343.0
STACK = 0.150
P_REF = 1e-12


def radial_amp(xyz, U):
    th = np.arctan2(xyz[:, 1], xyz[:, 0])
    return np.abs(U[:, 0] * np.cos(th) + U[:, 1] * np.sin(th))


def erp(xyz, U, freq, radius, length):
    ur = radial_amp(xyz, U)
    Ai = 2 * np.pi * radius * length / len(ur)
    om = 2 * np.pi * freq
    return 0.5 * RHO0 * C0 * np.sum(Ai * (om * ur) ** 2)


def main():
    ds = np.load(NPZ_S); dh = np.load(NPZ_H)
    fs = ds["freqs_modal"]; fh = dh["freqs_modal"]
    f_elec = float(dh["f_elec"]); rpm = float(dh["rpm"])
    R_hout = float(dh["R_hout"]); hous_t = float(dh["hous_t"])
    oh = float(dh["hous_oh"])
    orders = [int(k) for k in dh["orders"]]

    fig = plt.figure(figsize=(16.5, 5.4))
    fig.suptitle(f"e10 — stator-only vs +aluminum housing (t={hous_t*1e3:.0f} mm), "
                 f"{rpm:.0f} rpm", fontsize=13.5, fontweight="bold")

    # (1) 모달 비교
    ax1 = fig.add_subplot(1, 3, 1)
    es = fs[fs > 1]; eh = fh[fh > 1]
    ax1.vlines(es, 0.55, 0.95, color="#7f9fb8", lw=1.4)
    ax1.vlines(eh, 0.05, 0.45, color="#2c7f5e", lw=1.4)
    ax1.text(0.02, 0.97, "stator only", transform=ax1.transAxes, fontsize=9,
             color="#7f9fb8", va="top")
    ax1.text(0.02, 0.47, "+housing", transform=ax1.transAxes, fontsize=9,
             color="#2c7f5e", va="top")
    for k in orders:
        ax1.axvline(k * f_elec, color="#d0342c", lw=1.2, ls="--", alpha=0.8)
    ax1.set_ylim(0, 1); ax1.set_yticks([])
    ax1.set_xlabel("frequency [Hz]")
    ax1.set_title("modal spectrum shift (red dashes = excitations)")

    # (2) 응답 비교
    ax2 = fig.add_subplot(1, 3, 2)
    x = np.arange(len(orders)); w = 0.27
    a_solo, a_stat, a_hous = [], [], []
    for k in orders:
        a_solo.append(radial_amp(ds[f"k{k}_xyz"], ds[f"k{k}_U"]).max() * 1e6)
        a_stat.append(radial_amp(dh[f"k{k}_s_xyz"], dh[f"k{k}_s_U"]).max() * 1e6)
        a_hous.append(radial_amp(dh[f"k{k}_h_xyz"], dh[f"k{k}_h_U"]).max() * 1e6)
    ax2.bar(x - w, a_solo, w, color="#7f9fb8", label="stator OD (solo)")
    ax2.bar(x, a_stat, w, color="#2c7f5e", label="stator OD (+housing)")
    ax2.bar(x + w, a_hous, w, color="#d0342c", label="housing outer")
    for xs, vals in ((x - w, a_solo), (x, a_stat), (x + w, a_hous)):
        for xi, v in zip(xs, vals):
            ax2.text(xi, v, f"{v:.2g}", ha="center", va="bottom", fontsize=7.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"k={k}\n{k*f_elec:.0f}Hz" for k in orders], fontsize=9)
    ax2.set_ylabel("max |u_r| [µm]")
    ax2.set_title("radial response"); ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3)

    # (3) ERP 비교
    ax3 = fig.add_subplot(1, 3, 3)
    lw_solo, lw_hous = [], []
    for k in orders:
        f = float(dh[f"k{k}_freq"])
        e_solo = erp(ds[f"k{k}_xyz"], ds[f"k{k}_U"], f, 0.099, STACK)
        e_hous = erp(dh[f"k{k}_h_xyz"], dh[f"k{k}_h_U"], f, R_hout, STACK + 2 * oh)
        lw_solo.append(10 * np.log10(max(e_solo, 1e-30) / P_REF))
        lw_hous.append(10 * np.log10(max(e_hous, 1e-30) / P_REF))
    ax3.bar(x - 0.18, lw_solo, 0.36, color="#7f9fb8", label="stator OD (solo)")
    ax3.bar(x + 0.18, lw_hous, 0.36, color="#d0342c", label="housing outer")
    for xs, vals in ((x - 0.18, lw_solo), (x + 0.18, lw_hous)):
        for xi, v in zip(xs, vals):
            ax3.text(xi, v + 0.4, f"{v:.1f}", ha="center", fontsize=8, fontweight="bold")
    ax3.set_xticks(x)
    ax3.set_xticklabels([f"k={k}" for k in orders], fontsize=9.5)
    ax3.set_ylabel("$L_W$ [dB re 1 pW] (σ_rad=1)")
    ax3.set_title("radiated power: emitting surface")
    ax3.legend(fontsize=8); ax3.grid(axis="y", alpha=0.3)

    fig.text(0.5, -0.02,
             "Housing: parametric Al cylinder bonded (MPC) to stator OD — minimal extension per Chauvicourt's "
             "missing rotor-housing-coupled-mode lesson. Rotor/endcaps/feet still absent.",
             ha="center", fontsize=8, color="#555")
    fig.tight_layout(rect=[0, 0.02, 1, 0.93])
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    print("saved", OUT)
    for k, ls, lh in zip(orders, lw_solo, lw_hous):
        print(f"  k={k}: Lw stator-solo {ls:.1f} dB → housing-outer {lh:.1f} dB "
              f"({lh-ls:+.1f} dB)")


if __name__ == "__main__":
    main()
