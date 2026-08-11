# -*- coding: utf-8 -*-
"""e10 ERP(등가방사음향파워) — 하모닉 OD 응답 → 소음 지표.

ERP = ½ · ρ₀c₀ · σ_rad · Σᵢ Aᵢ |v_n,i|²,   v_n = iω·u_r  (법선=반경)
σ_rad = 1 가정(표준 ERP 관례 — 실제 방사효율 상한, 링 모드는 고주파에서 1에 접근).
음향파워레벨 L_W = 10·log10(ERP / 1 pW) [dB].

입력: data/e10_harmonic_result.npz (차수별 OD 복소변위)
산출: data/e10_erp.json + data/e10_erp.png (차수별 ERP·dB 막대)
"""
from __future__ import annotations

import json
import os
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
NPZ = os.path.join(HERE, "data", "e10_harmonic_result.npz")
OUT_JSON = os.path.join(HERE, "data", "e10_erp.json")
OUT_PNG = os.path.join(HERE, "data", "e10_erp.png")

RHO0, C0 = 1.204, 343.0          # 공기 20°C
R_OD, STACK = 0.0990, 0.150
P_REF = 1e-12                     # 1 pW


def erp_for_order(xyz, U, freq):
    """OD 절점 복소변위 → ERP [W]. 원통면 절점만(끝단 가장자리 제외) 사용."""
    th = np.arctan2(xyz[:, 1], xyz[:, 0])
    ur = U[:, 0] * np.cos(th) + U[:, 1] * np.sin(th)     # 복소 반경변위
    # 원통면 절점 균등 면적 근사(반경밴드 추출이라 대부분 원통면)
    A_cyl = 2 * np.pi * R_OD * STACK
    Ai = A_cyl / len(ur)
    om = 2 * np.pi * freq
    v2 = (om * np.abs(ur)) ** 2                          # |v_n|² (피크)
    # 시간평균 ½|v_pk|² → ERP = ½ ρc Σ A |v|²
    erp = 0.5 * RHO0 * C0 * np.sum(Ai * v2)
    return float(erp), float(np.sqrt(v2.max()) )


def main():
    d = np.load(NPZ)
    orders = sorted(int(k) for k in d["orders"])
    f_elec = float(d["f_elec"]); rpm = float(d["rpm"])
    rows = []
    for k in orders:
        freq = float(d[f"k{k}_freq"])
        erp, vmax = erp_for_order(d[f"k{k}_xyz"], d[f"k{k}_U"], freq)
        lw = 10 * np.log10(max(erp, 1e-30) / P_REF)
        rows.append(dict(k=k, freq_Hz=freq, ERP_W=erp, Lw_dB=lw, vmax_mms=vmax * 1e3))
        print(f"k={k:3d} @ {freq:7.0f} Hz : ERP={erp:.3e} W  Lw={lw:5.1f} dB  "
              f"v_max={vmax*1e3:.3f} mm/s")
    total = sum(r["ERP_W"] for r in rows)
    lw_tot = 10 * np.log10(total / P_REF)
    print(f"TOTAL(∑orders)      : ERP={total:.3e} W  Lw={lw_tot:.1f} dB")

    json.dump(dict(rpm=rpm, f_elec=f_elec, sigma_rad=1.0,
                   rho0=RHO0, c0=C0, orders=rows,
                   total_ERP_W=total, total_Lw_dB=lw_tot),
              open(OUT_JSON, "w", encoding="utf-8"), indent=2)

    # ---- 그림 ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6))
    fig.suptitle(f"e10 stator ERP — tooth force orders @ {rpm:.0f} rpm "
                 f"(σ_rad=1, free-free stator core)", fontsize=12.5, fontweight="bold")
    labels = [f"k={r['k']}\n{r['freq_Hz']:.0f}Hz" for r in rows]
    lws = [r["Lw_dB"] for r in rows]
    x = np.arange(len(rows))
    b = ax1.bar(x, lws, 0.55, color="#d0342c")
    ax1.bar(len(rows), lw_tot, 0.55, color="#7f3f98")
    for xi, v in zip(list(x) + [len(rows)], lws + [lw_tot]):
        ax1.text(xi, v + 0.5, f"{v:.1f}", ha="center", fontsize=9.5, fontweight="bold")
    ax1.set_xticks(list(x) + [len(rows)])
    ax1.set_xticklabels(labels + ["TOTAL"], fontsize=9)
    ax1.set_ylabel("sound power level $L_W$ [dB re 1 pW]")
    ax1.set_ylim(0, max(lws + [lw_tot]) * 1.15)
    ax1.set_title("ERP per force order"); ax1.grid(axis="y", alpha=0.3)

    vm = [r["vmax_mms"] for r in rows]
    ax2.bar(x, vm, 0.55, color="#2c7fb8")
    for xi, v in zip(x, vm):
        ax2.text(xi, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9.5)
    ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel("max surface normal velocity [mm/s]")
    ax2.set_title("OD vibration velocity"); ax2.grid(axis="y", alpha=0.3)

    fig.text(0.5, -0.02, "ERP = ½ρ₀c₀·ΣA|iωu_r|² on stator OD (σ_rad=1 upper bound). "
             "Housing not included — absolute dB is indicative; use for order ranking.",
             ha="center", fontsize=8, color="#555")
    fig.tight_layout(rect=[0, 0.02, 1, 0.93])
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
    print("saved", OUT_PNG, "|", OUT_JSON)


if __name__ == "__main__":
    main()
