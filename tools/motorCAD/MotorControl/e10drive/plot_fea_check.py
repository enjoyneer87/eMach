# -*- coding: utf-8 -*-
"""Figures for the comprehensive check (direct FEA map, harmonics, loss convention, Simscape A-D, QS solver).

python plot_fea_check.py
  fea_lab_check.png    FEA (position-averaged) vs Lab interpolation over the band and at the table points
  fea_harmonics.png    torque and flux over rotor position, spectra (16 krpm table points)
  stage2d_variants.png Simscape variants A-D x tables (MCB, MBC 95 %) x torque x deadtime
  qs_vs_td.png         quasi-static solver vs the time-domain models (realized gamma and torque)
Colours: reference categorical slots (#2a78d6, #eb6834, #1baf7a, #eda100), neutral greys.
"""
import csv
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

WORK = r"D:\KangDH\Thesis\e10\work_lab_pc1\fea_pos"
DRV = r"D:\KangDH\Thesis\e10\work_lab_pc1\drive"
OUT = r"D:\KangDH\EveryMotor\eMach\tools\motorCAD\MotorControl"
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d3"
plt.rcParams.update({"font.family": ["Malgun Gothic", "DejaVu Sans"], "axes.unicode_minus": False, "font.size": 9,
                     "axes.titlesize": 10, "axes.edgecolor": INK2, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "lines.linewidth": 2.0, "legend.frameon": False, "savefig.dpi": 150})
WE = 4*16000*2*np.pi/60


def fig_lab_check(A):
    B = A["band"] if "band" in A else A["band_points"]
    ids = sorted(set(r["id"] for r in B))
    iqs = [q for q in sorted(set(r["iq"] for r in B)) if q >= 0]
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
    for k, q in enumerate(iqs[:4]):
        rows = sorted([r for r in B if r["iq"] == q and r["id"] <= -130], key=lambda r: r["id"])
        x = [r["id"] for r in rows]
        dT = [r["Electromagnetic_Torque_fea"] - r["Electromagnetic_Torque_lab"] for r in rows]
        dV = []
        for r in rows:
            vf = np.hypot(0.0786*r["id"] - WE*r["Flux_Linkage_Q_fea"], 0.0786*r["iq"] + WE*r["Flux_Linkage_D_fea"])
            vl = np.hypot(0.0786*r["id"] - WE*r["Flux_Linkage_Q_lab"], 0.0786*r["iq"] + WE*r["Flux_Linkage_D_lab"])
            dV.append(vf - vl)
        axs[0].plot(x, dT, "-o", ms=3, color=C[k], label="i$_q$ = %g A" % q)
        axs[1].plot(x, dV, "-o", ms=3, color=C[k], label="i$_q$ = %g A" % q)
    for ax in axs[:2]:
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axvspan(-290, -190, color="#f0efec", zorder=0)
        ax.set_xlabel("i$_d$ [A 첨두]  (음영: 16 krpm 기준표 운전 영역)")
        ax.legend(fontsize=8)
    axs[0].set(ylabel="T$_{em}$ FEA - Lab [N·m]", title="(a) 전자기 토크 차이 (위치 평균 FEA − Lab 보간)")
    axs[1].set(ylabel="16 krpm 필요 전압 차이 [V 첨두]", title="(b) |R i + jω$_e$ψ| 차이 (FEA 자속 - Lab 자속, 한계 403 V)")
    ops = A["ops"]
    T = [o["T_ref"] for o in ops]
    w = 0.38
    x = np.arange(len(T))
    ax = axs[2]
    ax.bar(x - w/2, [o["dTdg_lab"] for o in ops], w*0.95, color=C[0], label="Lab 보간")
    ax.bar(x + w/2, [o["dTdg_fea"] for o in ops], w*0.95, color=C[1], label="직접 FEA")
    ax.set_xticks(x, ["%d N·m" % t for t in T])
    ax.set(ylabel="dT/dγ [N·m/°]", title="(c) 기준표 운전점의 진각 민감도")
    ax.legend(fontsize=8, loc="lower left")
    fig.suptitle("직접 FEA(위치 평균) 대 Lab 보간 — 16 krpm 운전 영역", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "fea_lab_check.png"))
    plt.close(fig)


def fig_harmonics(A):
    ops = {o["T_ref"]: o for o in A["ops"]}
    th = np.linspace(0, 360, len(ops[20]["T_wave"]))
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.0), constrained_layout=True)
    for k, T in enumerate((20, 60)):
        o = ops[T]
        axs[0].plot(th, o["T_wave"], color=C[k], lw=1.4, label="%d N·m점 (p-p %.0f N·m)" % (T, np.ptp(o["T_wave"])))
        axs[0].axhline(np.mean(o["T_wave"][:-1]), color=C[k], lw=0.8, ls="--")
    axs[0].axhline(0, color=INK2, lw=0.8)
    axs[0].set(xlabel="d축 전기각 θ$_d$ [deg]", ylabel="전자기 토크 [N·m]", xlim=(0, 360),
               title="(a) 정현 전류에서 토크 — 평균(점선)보다 리플이 크다")
    axs[0].set_ylim(-10, 118)
    axs[0].legend(fontsize=8, loc="upper right", ncol=2)
    o = ops[20]
    orders = [6, 12, 18, 24, 30, 36]
    w = 0.26
    x = np.arange(len(orders))
    for k, key, lab in ((0, "psi_d", "ψ$_d$"), (1, "psi_q", "ψ$_q$")):
        v = [1e3*o["harmonics"][key].get(str(h), o["harmonics"][key].get(h, 0.0)) for h in orders]
        axs[1].bar(x + (k - 0.5)*w, v, w*0.95, color=C[k], label=lab)
    axs[1].set_xticks(x, [str(h) for h in orders])
    axs[1].set(xlabel="고조파 차수 (d축 전기 한 주기 기준)", ylabel="진폭 [mWb]", title="(b) 20 N·m점 dq 자속 고조파")
    axs[1].legend(fontsize=8)
    vT = [o["harmonics"]["T"].get(str(h), o["harmonics"]["T"].get(h, 0.0)) for h in orders]
    axs[2].bar(x, vT, 0.6, color=C[2])
    axs[2].set_xticks(x, [str(h) for h in orders])
    axs[2].set(xlabel="고조파 차수", ylabel="진폭 [N·m]",
               title="(c) 20 N·m점 토크 고조파 (6차 6.4 kHz, 12차 12.8 kHz)")
    fig.suptitle("회전자 위치별 FEA (e10, 16 krpm 기준표 운전점, 정현 전류)", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "fea_harmonics.png"))
    plt.close(fig)


def fig_variants(rows):
    if not rows:
        return
    names = [("lab_rep", "A Lab·기존"), ("lab_conv", "B +손실 규약·R$_{ac}$"), ("fea_avg", "C +직접 FEA 평균"),
             ("fea_pos", "D +FEA 위치별(고조파)")]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.4), constrained_layout=True, sharey=True)
    for ax, tb in zip(axs, ("MCB", "MBC 95")):
        cases = sorted(set((float(r["T_ref"]), float(r["td_us"])) for r in rows if r["table"] == tb))
        x = np.arange(len(cases))
        w = 0.2
        for k, (vn, lab) in enumerate(names):
            v = []
            for T, td in cases:
                m = [r for r in rows if r["table"] == tb and r["variant"] == vn and float(r["T_ref"]) == T
                     and float(r["td_us"]) == td]
                v.append(float(m[0]["err_pct"]) if m else np.nan)
            ax.bar(x + (k - 1.5)*w, np.clip(v, -60, 20), w*0.95, color=C[k], label=lab)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axhspan(-5, 5, color="#f0efec", zorder=0)
        ax.set_xticks(x, ["%g N·m\nt$_d$ %g µs" % c for c in cases], fontsize=8)
        ax.set(title="기준표 %s" % ("MCB (여유 0)" if tb == "MCB" else "MBC VsMax 95 %"), ylim=(-60, 15))
        ax.legend(fontsize=7.5, loc="lower left", ncol=2)
    axs[0].set_ylabel("토크 오차 [%] (−60 % 아래는 잘림)")
    fig.suptitle("Simscape 단계 2d — 전동기 표를 한 요인씩 바꿔 넣은 결과 (16 krpm, 데드타임 보상 없음)", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "stage2d_variants.png"))
    plt.close(fig)


def fig_margin(rows_qs, hm):
    """Torque error vs voltage margin of the reference table: C (mean FEA map) vs D (position-resolved map)
    with the standard regulator and with reference-current decoupling. Lines: QS tables placed exactly at
    5/10/15/20 % below the clamp (FEA mean map + R_ac). Hollow markers: the MCB / MBC 95 / MBC 90 tables at
    their actual margin in the same model (qs_harmonic_margin.json, m_table)."""
    if not rows_qs:
        return
    ser = [("fea_avg", "C 평균 맵 (고조파 없음)", C[2], "-", "o"),
           ("fea_pos", "D 위치별 맵 · 기본 제어기", C[3], "-", "s"),
           ("fea_pos_ff", "D 위치별 맵 · 기준 전류 디커플링", C[3], "--", "D")]
    panels = [(5, 0.0), (20, 0.0), (60, 0.0), (20, 3.0)]
    fig, axs = plt.subplots(1, 4, figsize=(14, 4.2), constrained_layout=True, sharey=True)
    for ax, (T, td) in zip(axs, panels):
        for vn, lab, col, ls, mk in ser:
            pts = sorted((100 - float(r["table"].split()[1]), float(r["err_pct"])) for r in rows_qs
                         if r["variant"] == vn and float(r["T_ref"]) == T and float(r["td_us"]) == td)
            if pts:
                x, y = zip(*pts)
                ax.plot(x, np.clip(y, -100, 20), ls=ls, marker=mk, ms=6, color=col, mec=INK, mew=0.7, label=lab)
            old = [(100*h["m_table"], h["T_sim"]/T*100 - 100) for h in hm
                   if h["variant"] == vn and h["T_ref"] == T and h["td_us"] == td]
            if old:
                x, y = zip(*old)
                ax.plot(x, np.clip(y, -100, 20), ls="none", marker=mk, ms=7, mfc="none", mec=col, mew=1.3)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axhspan(-5, 5, color="#f0efec", zorder=0)
        ax.set(title="%g N·m, t$_d$ %g µs" % (T, td), xlabel="기준표 전압 여유 [%]", xlim=(-1, 31), ylim=(-102, 15))
    axs[0].set_ylabel("토크 오차 [%] (−100 % 아래는 잘림)")
    axs[2].legend(fontsize=7.5, loc="lower right")
    axs[2].text(0.98, 0.30, "속 찬 점: QS 표 (여유를 정확히 둔 표)\n빈 점: MCB·MBC 95·MBC 90 표", transform=axs[2].transAxes,
                ha="right", va="bottom", fontsize=7.5, color=INK2)
    fig.suptitle("슬롯 고조파를 견디는 데 필요한 전압 여유 — Simscape 단계 2d, 16 krpm (회색 띠 ±5 %)", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "stage2d_margin.png"))
    plt.close(fig)


def fig_hb(hb):
    """Harmonic-balance quasi-static calculation (qs_harmonic_hb.py) vs Simscape stage 2d."""
    if not hb:
        return
    ser = [("fea_avg", "C 평균 맵", C[2], "-", "o"), ("fea_pos", "D 위치별 맵 · 기본 제어기", C[3], "-", "s"),
           ("fea_pos_ff", "D 위치별 맵 · 기준 전류 디커플링", C[3], "--", "D")]
    fig, axs = plt.subplots(1, 4, figsize=(14.5, 4.1), constrained_layout=True)
    ax = axs[0]
    for vn, lab, col, ls, mk in ser:
        r = [x for x in hb if x["variant"] == vn]
        ax.plot([x["sim_T"] for x in r], [x["T_shaft"] for x in r], mk, ms=5, color=col, mec=INK, mew=0.5, ls="none",
                label=lab)
    ax.plot([-35, 65], [-35, 65], color=INK2, lw=0.8)
    h = [x for x in hb if x["variant"] != "fea_avg" and x["table"].startswith("QS")]
    rms = np.sqrt(np.mean([(x["T_shaft"] - x["sim_T"])**2 for x in h]))
    rmsg = np.sqrt(np.mean([(x["gamma"] - x["sim_gamma"])**2 for x in h]))
    ax.set(xlabel="Simscape 실현 축 토크 [N·m]", ylabel="조화균형 계산 [N·m]", xlim=(-35, 65), ylim=(-35, 65),
           title="(a) 전 경우 %d건" % len(hb))
    ax.text(0.97, 0.04, "여유 둔 QS 표, 고조파 %d건:\nRMS %.1f N·m · %.2f°\n왼쪽 아래 이탈: 여유 0 MCB 표 5 N·m\n(90°를 넘어 역토크로 무너진 점)"
            % (len(h), rms, rmsg), transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5, color=INK2)
    ax.legend(fontsize=7.5, loc="upper left")
    for ax, T in zip(axs[1:], (5, 20, 60)):
        for vn, lab, col, ls, mk in ser:
            r = sorted((x for x in hb if x["variant"] == vn and x["T_ref"] == T and x["td_us"] == 0
                        and x["table"].startswith("QS")), key=lambda x: -int(x["table"].split()[1]))
            if not r:
                continue
            m = [100 - int(x["table"].split()[1]) for x in r]
            ax.plot(m, [np.clip(100*(x["sim_T"]/T - 1), -100, 20) for x in r], mk, ms=6, color=col, mec=INK,
                    mew=0.6, ls="none")
            ax.plot(m, [np.clip(100*(x["T_shaft"]/T - 1), -100, 20) for x in r], ls=ls, color=col, lw=1.8)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axhspan(-5, 5, color="#f0efec", zorder=0)
        ax.set(title="(%s) %d N·m, t$_d$ 0" % ("bcd"[(5, 20, 60).index(T)], T), xlabel="기준표 전압 여유 [%]",
               xlim=(3, 32), ylim=(-102, 12))
    axs[1].set_ylabel("토크 오차 [%] (−100 % 아래는 잘림)")
    axs[3].text(0.97, 0.05, "점: Simscape (경우당 약 15 s)\n선: 조화균형 계산 (경우당 약 0.4 s)", transform=axs[3].transAxes,
                ha="right", va="bottom", fontsize=7.5, color=INK2)
    fig.suptitle("슬롯 고조파를 정상상태 계산기에 넣기 — 조화균형(고조파 전류·제어기 반응·클램프 평균·안티와인드업 평형) 대 Simscape 단계 2d",
                 fontsize=10.5)
    fig.savefig(os.path.join(OUT, "qs_hb_vs_simscape.png"))
    plt.close(fig)
    print("HB vs Simscape (harmonic cases): RMS dT %.2f N·m, RMS dgamma %.3f deg, n=%d" % (rms, rmsg, len(h)))


def fig_clamp():
    """Anatomy of the regulator clamp at 16 krpm, 20 N·m (QS tables, variant D, standard regulator)."""
    import qs_harmonic_hb as HBm
    PM = HBm.PosMap()
    we, vmax = WE, HBm.CTRL["Vmax"]
    G = -np.diag([HBm.CTRL["Kpd"], HBm.CTRL["Kpq"]]) + np.array([[0, -we*HBm.CTRL["Lq"]], [we*HBm.CTRL["Ld"], 0]])
    cases = {}
    for tb in ("QS 95", "QS 90", "QS 85", "QS 80", "QS 75", "QS 70"):
        i_ref, q_ref = HBm.ref_point(tb, 20)
        s = HBm.solve_case(PM, i_ref, q_ref, 0.0, True, False)
        di, x = HBm.sampled_harmonic_currents(PM, i_ref, q_ref, False, return_x=True)
        cases[tb] = dict(s=s, dv=G @ di, x=x, V=np.array([s["V_d"], s["V_q"]]))
    fig, axs = plt.subplots(1, 3, figsize=(14.5, 4.6), constrained_layout=True)
    # (a) voltage plane
    ax = axs[0]
    c = cases["QS 95"]
    v = c["V"][:, None] + c["dv"]
    o = np.argsort(c["x"])
    m = np.hypot(*v)
    out = m > vmax
    ph = np.linspace(np.radians(76), np.radians(132), 300)
    ax.plot(vmax*np.cos(ph), vmax*np.sin(ph), color=INK, lw=1.6, label="클램프 |v| = 403.2 V")
    ax.plot(415.7*np.cos(ph), 415.7*np.sin(ph), color=INK2, lw=1.0, ls="--", label="선형 SVPWM 한계 415.7 V")
    ax.plot(np.append(v[0, o], v[0, o[0]]), np.append(v[1, o], v[1, o[0]]), color=GRID, lw=1.0, zorder=1)
    ax.plot(v[0, ~out], v[1, ~out], "o", ms=4, color=INK2, label="명령 샘플 (통과)")
    ax.plot(v[0, out], v[1, out], "o", ms=5, color=C[1], mec=INK, mew=0.4, label="명령 샘플 (잘림 %d %%)" % round(100*out.mean()))
    vs = v[:, out]*vmax/m[out]
    ax.plot(vs[0], vs[1], ".", ms=4, color=C[1])
    for k in np.nonzero(out)[0]:                                  # what the clamp removes from each sample
        ax.plot([v[0, k], v[0, k]*vmax/m[k]], [v[1, k], v[1, k]*vmax/m[k]], color=C[1], lw=0.6)
    d = np.array([c["s"]["clip_d"], c["s"]["clip_q"]])
    ax.plot(*c["V"], "D", ms=8, color=C[0], mec=INK, label="평균 명령 V̄ (%.0f V)" % np.hypot(*c["V"]))
    ax.annotate("", xy=c["V"] - d, xytext=c["V"], arrowprops=dict(arrowstyle="->", color=C[0], lw=1.8))
    ax.text(c["V"][0] - d[0] + 6, c["V"][1] - d[1] - 10, "평균 인가 V̄ − δ\nδ = (%.1f, %.1f) V" % (d[0], d[1]),
            fontsize=8, color=INK)
    ax.set(xlabel="v$_d$ [V]", ylabel="v$_q$ [V]", title="(a) 전압 평면: 여유 5 % 표, 20 N·m", aspect="equal",
           xlim=(-260, 80), ylim=(235, 540))
    ax.legend(fontsize=7, loc="upper left")
    # (b) |v| over one electrical period
    ax = axs[1]
    for tb, col in (("QS 95", C[1]), ("QS 75", C[0])):
        c = cases[tb]
        v = c["V"][:, None] + c["dv"]
        o = np.argsort(c["x"])
        mm = np.hypot(*v)[o]
        ax.plot(c["x"][o], mm, "-o", ms=2.5, lw=1.4, color=col,
                label="여유 %d %% 표: 잘림 %d %%, δ %.1f V" % (100 - int(tb.split()[1]), round(100*np.mean(mm > vmax)),
                                                     np.hypot(c["s"]["clip_d"], c["s"]["clip_q"])))
        if tb == "QS 95":
            ax.fill_between(c["x"][o], vmax, mm, where=mm > vmax, color=C[1], alpha=0.35, lw=0)
        ax.axhline(np.hypot(*c["V"]), color=col, lw=0.8, ls=":")
    ax.axhline(vmax, color=INK, lw=1.4)
    ax.text(3, vmax + 4, "클램프 403.2 V", fontsize=8)
    ax.set(xlabel="회전자 위치 (전기각) [deg]", ylabel="명령 전압 크기 |v| [V 첨두]", xlim=(0, 360), ylim=(80, 530),
           title="(b) 한 주기 동안의 명령 크기 (점선: 평균 명령)")
    ax.legend(fontsize=7.5, loc="lower center")
    # (c) mean clipped excess vs gap
    ax = axs[2]
    c = cases["QS 95"]
    u = c["V"]/np.hypot(*c["V"])
    A = float(np.max(u @ c["dv"]))
    g = np.linspace(0, 150, 151)
    dm = [np.hypot(*HBm.clip_excess(u*(vmax - gg), c["dv"], vmax)[0]) for gg in g]
    ax.plot(g, dm, color=INK2, lw=1.8, label="이 리플로 계산 (평균 명령 크기만 바꿈)")
    r = np.clip(g/A, 0, 1)
    p0 = np.arccos(r)
    ax.plot(g, (A/np.pi)*(np.sin(p0) - r*p0), color=INK2, lw=1.2, ls="--",
            label="단일 정현 근사, 진폭 A = %.0f V" % A)
    sim = {"QS 95": -54, "QS 90": -31, "QS 85": -17, "QS 80": -9, "QS 75": -3.2, "QS 70": -0.4}
    for tb, cc in cases.items():
        gg = vmax - np.hypot(*cc["V"])
        dd = np.hypot(cc["s"]["clip_d"], cc["s"]["clip_q"])
        ax.plot(gg, dd, "s", ms=7, color=C[3], mec=INK, mew=0.6)
        e = ("%.0f" if abs(sim[tb]) >= 1 else "%.1f") % sim[tb]
        ax.annotate("%d %% 표\n토크 %s %%" % (100 - int(tb.split()[1]), e.replace("-", "−")), (gg, dd),
                    textcoords="offset points", xytext=(6, 4), fontsize=7.2)
    ax.set(xlabel="틈 = 403.2 V − |평균 명령| [V]", ylabel="평균 잘린 전압 |δ| [V]", xlim=(0, 150),
           title="(c) 틈이 리플 봉우리보다 커야 잘림이 사라진다")
    ax.legend(fontsize=7.5, loc="upper right")
    fig.suptitle("조절기 클램프 해부 — 16 krpm, 20 N·m, 슬롯 고조파(위치별 맵), 기본 제어기 (조화균형 계산)", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "clamp_anatomy.png"))
    plt.close(fig)


REM = [("base", "대책 없음", "#9a9892"), ("notch", "③ 노치 (6·12차)", C[0]), ("pr6", "③ 6차 PR 억누르기", C[1]),
       ("hex", "④ 과변조 (육각형)", C[2]), ("fw", "⑤ 전압 피드백 약자속", C[3])]


def loss_at(M, I_rms, gamma):
    """16 krpm total loss [W] at a realized mean point, FEA band loss maps (same terms as qs_margin_cost)"""
    import fea_posmap_analyze as FA
    i, q = -np.sqrt(2)*I_rms*np.sin(np.radians(gamma)), np.sqrt(2)*I_rms*np.cos(np.radians(gamma))
    v = {k: float(M.vals(k, i, q)) for k in ("Stator_Copper_Loss_AC", "Iron_Loss_Stator", "Iron_Loss_Rotor", "Magnet_Loss")}
    return 1.5*FA.R_DC*(i*i + q*q) + sum(v.values()) + FA.P_MECH


def fig_remedies(rows, hb):
    """Simscape stage 2e: slot-harmonic remedies (D, position-resolved map), with harmonic-balance predictions"""
    if not rows:
        return
    import qs_opsolver as QS
    M = QS.Maps("fea", rac=True)
    cases = [(5, 0.0), (20, 0.0), (60, 0.0), (20, 3.0)]
    fig, axs = plt.subplots(1, 3, figsize=(14.5, 4.4), constrained_layout=True)
    w = 0.16
    x = np.arange(len(cases))
    for ax, tb in zip(axs[:2], ("QS 95", "QS 85")):
        for k, (rn, lab, col) in enumerate(REM):
            v = []
            for T, td in cases:
                m = [r for r in rows if r["remedy"] == rn and r["variant"] == "fea_pos" and r["table"] == tb
                     and float(r["T_ref"]) == T and float(r["td_us"]) == td]
                v.append(float(m[0]["err_pct"]) if m else np.nan)
            ax.bar(x + (k - 2)*w, np.clip(v, -100, 15), w*0.92, color=col, label=lab)
            p = [h for h in hb if h["remedy"] == rn and h["table"] == tb]
            if p and rn != "pr6":
                hv = []
                for T, td in cases:
                    m = [h for h in p if h["T_ref"] == T and h["td_us"] == td]
                    hv.append(100*(m[0]["T_shaft"]/T - 1) if m else np.nan)
                ax.plot(x + (k - 2)*w, np.clip(hv, -100, 15), "D", ms=4, color=INK, mfc="white", mew=1.0,
                        label="조화균형 계산" if k == 0 else None)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axhspan(-5, 5, color="#f0efec", zorder=0)
        ax.set_xticks(x, ["%g N·m\nt$_d$ %g µs" % c for c in cases], fontsize=8)
        ax.set(title="기준표 여유 %d %% (%s)" % (100 - int(tb.split()[1]), tb), ylim=(-102, 15))
    axs[0].set_ylabel("토크 오차 [%] (−100 % 아래는 잘림)")
    # (c) loss at the realized point relative to the table point, for the remedies that deliver the torque
    ax = axs[2]
    from qs_harmonic_hb import ref_point
    cs2 = [(5, 0.0), (20, 0.0), (60, 0.0)]
    x2 = np.arange(len(cs2))
    base_loss = {}
    for T, td in cs2:
        i_ref, q_ref = ref_point("QS 95", T)
        base_loss[T] = loss_at(M, np.hypot(i_ref, q_ref)/np.sqrt(2), np.degrees(np.arctan2(-i_ref, q_ref)))
    shapes = {5: "o", 20: "s", 60: "^"}
    for rn, lab, col in REM:
        for T, td in cs2:
            m = [r for r in rows if r["remedy"] == rn and r["variant"] == "fea_pos" and r["table"] == "QS 95"
                 and float(r["T_ref"]) == T and float(r["td_us"]) == td]
            if not m:
                continue
            dl = 100*(loss_at(M, float(m[0]["I_rms"]), float(m[0]["gamma"]))/base_loss[T] - 1)
            ax.plot(max(float(m[0]["err_pct"]), -100), dl, shapes[T], ms=8, color=col, mec=INK, mew=0.6)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.axvspan(-5, 5, color="#f0efec", zorder=0)
    ax.set(xlim=(-104, 10), ylim=(-4, 36), xlabel="토크 오차 [%] (−100 % 아래는 −100에)",
           ylabel="16 krpm 전체 손실 변화 [%] (기준표 점 대비)", title="여유 5 % 표: 정확도 대 손실 (원점이 이상적)")
    hs = [plt.Rectangle((0, 0), 1, 1, color=col) for _, _, col in REM] + \
         [plt.Line2D([], [], ls="none", marker="D", ms=4, color=INK, mfc="white", mew=1.0)] + \
         [plt.Line2D([], [], ls="none", marker=mk, ms=6, color="#ffffff", mec=INK) for mk in shapes.values()]
    ax.legend(hs, [lab for _, lab, _ in REM] + ["조화균형 계산 (왼쪽 두 그림)"] + ["%d N·m" % t for t in shapes],
              fontsize=7.2, loc="upper left", ncol=2)
    fig.suptitle("슬롯 고조파 대책 시험 — Simscape 단계 2e, 16 krpm, 위치별 FEA 맵 (막대: Simscape, 흰 마름모: 조화균형 계산)",
                 fontsize=10.5)
    fig.savefig(os.path.join(OUT, "stage2e_remedies.png"))
    plt.close(fig)


def fig_qs(qsfiles, s2):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), constrained_layout=True)
    for k, (fn, lab, td) in enumerate(qsfiles):
        if not os.path.exists(fn):
            continue
        q = json.load(open(fn))
        T = [r["T"] for r in q["rows"]]
        axs[0].plot(T, [r["held_MCB"]["gamma"] for r in q["rows"]], "-o", ms=4, color=C[k], label="정상상태 " + lab)
        axs[1].plot(T, [r["held_MCB"]["T_shaft"] for r in q["rows"]], "-o", ms=4, color=C[k], label="정상상태 " + lab)
        sim = [r for r in s2 if r["kind"] == "ceiling" and float(r["td_us"]) == td] or \
              [r for r in s2 if r["kind"] == "deadtime" and float(r["td_us"]) == td]
        sim = sorted(sim, key=lambda r: float(r["T_ref"]))
        axs[0].plot([float(r["T_ref"]) for r in sim], [float(r["gamma"]) for r in sim], "s", mfc="none", ms=7,
                    color=C[k], label="시간영역 " + lab)
        axs[1].plot([float(r["T_ref"]) for r in sim], [float(r["T"]) for r in sim], "s", mfc="none", ms=7,
                    color=C[k], label="시간영역 " + lab)
    axs[1].plot([0, 90], [0, 90], color=INK2, lw=0.8)
    axs[0].set(xlabel="토크 지령 [N·m]", ylabel="실현 진각 γ [deg]", title="(a) MCB 기준표의 실현 진각", xlim=(0, 90))
    axs[1].set(xlabel="토크 지령 [N·m]", ylabel="실현 축 토크 [N·m]", title="(b) 실현 토크", xlim=(0, 90))
    for ax in axs:
        ax.legend(fontsize=7.5)
    fig.suptitle("정상상태 운전점 계산기(유효 전압한계) 대 시간영역 스위칭 모델 — Lab 맵, 교류 저항 제외", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "qs_vs_td.png"))
    plt.close(fig)


def fig_same_current(hm):
    """D(위치별 맵)의 토크 결손은 같은 전류의 토크가 아니라 운전점(진각)이 옮겨진 탓 — 현상, 같은 전류, 원인"""
    MK = {"MCB": "o", "MBC 95": "s", "MBC 90": "^"}
    get = {(x["variant"], x["table"], x["T_ref"], x["td_us"]): x for x in hm}
    fig, axs = plt.subplots(1, 3, figsize=(12.6, 4.0), constrained_layout=True)
    ax = axs[0]
    for vn, lab, col in (("fea_avg", "C 평균 맵", C[2]), ("fea_pos", "D 위치별 맵", C[3])):
        for tb, mk in MK.items():
            pts = [(x["T_ref"], x["T_sim"]) for k, x in get.items() if k[0] == vn and k[1] == tb and k[3] == 0]
            if pts:
                t, s = np.array(pts).T
                ax.plot(t, s, mk, color=col, mec=INK2, mew=0.6, ms=7, ls="none",
                        label="%s · %s" % (lab, tb))
    ax.plot([-25, 65], [-25, 65], "--", color=INK2, lw=1)
    ax.set(xlim=(-2, 65), ylim=(-25, 65), xlabel="지령 토크 [N·m]", ylabel="실현 평균 토크 [N·m]",
           title="(a) 현상: 위치별 맵에서 토크가 모자란다")
    ax.legend(fontsize=7, loc="upper left")
    ax = axs[1]
    for vn, lab, fc in (("fea_pos", "D", C[3]), ("fea_pos_ff", "D$_{ff}$ (기준 전류 디커플링)", "white")):
        for tb, mk in MK.items():
            pts = [(x["T_map"], x["T_sim"]) for k, x in get.items() if k[0] == vn and k[1] == tb]
            if pts:
                m, s = np.array(pts).T
                ax.plot(m, s, mk, color=fc, mec=INK2, mew=0.8, ms=7, ls="none", label="%s · %s" % (lab, tb))
    ax.plot([-25, 65], [-25, 65], "--", color=INK2, lw=1)
    r0 = max(abs(x["T_sim"] - x["T_map"]) for x in hm if x["td_us"] == 0)
    r3 = max(abs(x["T_sim"] - x["T_map"]) for x in hm if x["td_us"] == 3)
    ax.text(0.97, 0.04, "최대 차 %.1f N·m (데드타임 3 µs 포함 %.1f)" % (r0, r3), transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, color=INK2)
    ax.set(xlim=(-25, 65), ylim=(-25, 65), xlabel="평균 맵 토크 @ D가 도달한 평균 (I, γ) [N·m]",
           ylabel="D 실현 평균 토크 [N·m]", title="(b) 같은 평균 전류: 평균 토크는 그대로")
    ax.legend(fontsize=7, loc="upper left")
    ax = axs[2]
    for vn, lab, fc in (("fea_pos", "D", C[3]), ("fea_pos_ff", "D$_{ff}$", "white")):
        for tb, mk in MK.items():
            pts = []
            for k, x in get.items():
                c = get.get(("fea_avg", k[1], k[2], k[3]))
                if k[0] == vn and k[1] == tb and k[3] == 0 and c is not None:
                    pts.append((x["gamma_sim"] - c["gamma_sim"], c["T_sim"] - x["T_sim"]))
            if pts:
                g, d = np.array(pts).T
                ax.plot(g, d, mk, color=fc, mec=INK2, mew=0.8, ms=7, ls="none", label="%s · %s" % (lab, tb))
    gg = np.array([0, 2])
    ax.plot(gg, 11*gg, "--", color=INK2, lw=1)
    ax.text(1.55, 11*1.55 + 1.2, "|dT/dγ| = 11 N·m/°", rotation=0, fontsize=8, color=INK2, ha="right")
    ax.set(xlim=(0, 2), ylim=(0, 22), xlabel=r"실현 진각 이동 $\gamma_D - \gamma_C$ [°]", ylabel=r"토크 결손 $T_C - T_D$ [N·m]",
           title="(c) 원인: 진각 이동 × 진각 민감도")
    ax.legend(fontsize=7, loc="upper left")
    fig.suptitle("슬롯 고조파는 같은 전류의 평균 토크를 바꾸지 않고 제어기가 도달하는 진각을 옮긴다 "
                 "(Simscape 단계 2d, 16 krpm, 데드타임 0)", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "sh_same_current.png"))
    plt.close(fig)


def notch_pair(rpm, Ts=50e-6, r=0.9):
    """run_e10_stage2e.m 과 같은 노치 둘(6차, 샘플링에 접힌 12차): [(b, a), (b, a)], f6, f12_seen [Hz]"""
    we = 4*rpm*2*np.pi/60
    out = []
    w1 = (6*we*Ts) % (2*np.pi)
    w12 = (12*we*Ts) % (2*np.pi)
    w2 = min(w12, 2*np.pi - w12)
    for w0 in (w1, w2):
        b = np.array([1.0, -2*np.cos(w0), 1.0])
        a = np.array([1.0, -2*r*np.cos(w0), r*r])
        out.append((b*a.sum()/b.sum(), a))
    return out, w1/(2*np.pi*Ts), w2/(2*np.pi*Ts)


def fig_notch():
    """노치란 무엇인가 — 주파수 응답(깎는 곳과 남기는 곳), 교차 주파수의 위상 지연(대가), 제어기가 보는 전류(효과)"""
    from scipy.signal import lfilter
    Ts, fc = 50e-6, 1e4/(2*np.pi)
    f = np.linspace(1, 1/(2*Ts), 4000)
    w = 2*np.pi*f*Ts
    z = np.exp(-1j*np.outer(w, np.arange(3)))
    fig, axs = plt.subplots(1, 3, figsize=(13.4, 4.1), constrained_layout=True)
    for rpm, col, off in ((6000, C[1], (8, -4)), (10000, C[3], (8, -13)), (16000, C[0], (8, 5))):
        pair, f6, f12 = notch_pair(rpm)
        h = np.ones_like(w, dtype=complex)
        for b, a in pair:
            h *= (z @ b)/(z @ a)
        lab = "%d krpm (6차 %.1f kHz, 12차 → %.1f kHz)" % (rpm/1000, f6/1e3, f12/1e3)
        axs[0].plot(f/1e3, 20*np.log10(np.abs(h) + 1e-6), color=col, lw=1.6, label=lab)
        ph = np.degrees(np.unwrap(np.angle(h)))
        axs[1].plot(f/1e3, ph, color=col, lw=1.6, label="%d krpm" % (rpm/1000))
        wc = 2*np.pi*fc*Ts
        hc = np.prod([(np.exp(-1j*wc*np.arange(3)) @ b)/(np.exp(-1j*wc*np.arange(3)) @ a) for b, a in pair])
        axs[1].plot(fc/1e3, np.degrees(np.angle(hc)), "o", color=col, ms=7, mec=INK2)
        axs[1].annotate("%.1f°" % np.degrees(np.angle(hc)), (fc/1e3, np.degrees(np.angle(hc))), xytext=off,
                        textcoords="offset points", fontsize=8, color=col)
    for ax in axs[:2]:
        ax.axvline(fc/1e3, color=INK2, ls="--", lw=1)
        ax.set_xlabel("주파수 [kHz] (나이퀴스트 10 kHz)")
    axs[0].text(fc/1e3 + 0.1, -38, "전류 루프\n교차 1.6 kHz", fontsize=8, color=INK2)
    axs[0].set(ylabel="이득 [dB]", ylim=(-42, 4), xlim=(0, 10), title="(a) 한 주파수만 깊게 깎고 나머지는 통과(직류 이득 1)")
    axs[0].legend(fontsize=7, loc="lower right")
    axs[1].set(ylabel="위상 [°]", xlim=(0, 10), ylim=(-100, 100), title="(b) 대가: 홈 아래쪽의 위상 지연 — 교차에서 ●")
    axs[1].legend(fontsize=7.5, loc="lower right")
    ax = axs[2]
    rpm = 16000
    we = 4*rpm*2*np.pi/60
    t = np.arange(0, 0.012, Ts)
    th = we*t
    iq = 6.8 + 5.0*np.cos(6*th) + 6.0*np.cos(12*th + 0.7)
    y = iq.copy()
    pair, _, _ = notch_pair(rpm)
    for b, a in pair:
        y = lfilter(b, a, y)
    n0 = len(t) - int(4*2*np.pi/we/Ts)
    tt = (t[n0:] - t[n0])*1e3
    tf = np.linspace(t[n0], t[-1], 3000)
    thf = we*tf
    ax.plot((tf - t[n0])*1e3, 6.8 + 5.0*np.cos(6*thf) + 6.0*np.cos(12*thf + 0.7), color=C[1], lw=0.8, alpha=0.45,
            label="실제 i$_q$ (평균 + 6·12차)")
    ax.plot(tt, iq[n0:], ".", color=C[1], ms=4, label="샘플 (20 kHz)")
    ax.plot(tt, y[n0:], color=C[0], lw=2.0, label="노치를 지난 샘플 (제어기가 보는 값)")
    ax.axhline(6.8, color=INK2, ls=":", lw=1)
    ax.set(xlabel="시간 [ms] (16 krpm, 전기 4주기)", ylabel="i$_q$ [A]", title="(c) 효과: 제어기는 평균만 본다")
    ax.legend(fontsize=7.5, loc="lower right")
    fig.suptitle("노치 필터 — 측정 dq 전류의 6차와 접힌 12차만 지우는 대역 저지 필터 (r = 0.9, 샘플 20 kHz)", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "notch_explained.png"))
    plt.close(fig)


def fig_phase_margin():
    """위상 여유란 — q축 전류 루프(K_p 16 Ω, L_q 1.6 mH, 연산 지연 1샘플 + 영차 유지)의 개루프 보드 선도와 계단 응답,
    노치 없음 / 16 krpm 노치 / 6 krpm 노치. 노치는 측정 전류(피드백 경로)에 둔다."""
    Ts, L, R, Kp = 50e-6, 1.597e-3, 0.0786, 16.0
    f = np.logspace(2, np.log10(0.5/Ts), 3000)
    w = 2*np.pi*f
    base = Kp/(1j*w*L)*np.exp(-1j*w*1.5*Ts)                   # PI 영점이 플랜트 극점을 지움: K_p/(sL) · 지연
    cases = [("노치 없음", None, INK2), ("노치 16 krpm", 16000, C[0]), ("노치 6 krpm", 6000, C[1])]
    fig, axs = plt.subplots(1, 3, figsize=(13.4, 4.1), constrained_layout=True)
    zz = np.exp(-1j*np.outer(w*Ts, np.arange(3)))
    for lab, rpm, col in cases:
        Lw = base.copy()
        if rpm:
            for b, a in notch_pair(rpm)[0]:
                Lw *= (zz @ b)/(zz @ a)
        mag = 20*np.log10(np.abs(Lw))
        ph = np.degrees(np.unwrap(np.angle(Lw)))
        k = int(np.argmax(mag < 0))                             # 첫 0 dB 교차 (위에서 아래로)
        fr = mag[k - 1]/(mag[k - 1] - mag[k])
        fx = f[k - 1] + fr*(f[k] - f[k - 1])
        pk = ph[k - 1] + fr*(ph[k] - ph[k - 1])
        pm = 180 + pk
        axs[0].semilogx(f, mag, color=col, lw=1.6, label=lab)
        axs[1].semilogx(f, ph, color=col, lw=1.6, label="%s: 위상 여유 %.0f°" % (lab, pm))
        axs[1].plot(fx, pk, "o", color=col, ms=6, mec=INK2)
        # 계단 응답 (이산): i[k+1] = a i + b v, v = 지연된 PI 출력, 피드백은 노치를 지난 측정 전류
        a_ = np.exp(-R*Ts/L)
        b_ = (1 - a_)/R
        n = int(3e-3/Ts)
        i = np.zeros(n + 1)
        x = 0.0
        vprev = 0.0
        filt = [(bb, aa, np.zeros(2), np.zeros(2)) for bb, aa in (notch_pair(rpm)[0] if rpm else [])]
        for kk in range(n):
            y = i[kk]
            for bb, aa, xs, ys in filt:
                out = bb[0]*y + bb[1]*xs[0] + bb[2]*xs[1] - aa[1]*ys[0] - aa[2]*ys[1]
                xs[1], xs[0] = xs[0], y
                ys[1], ys[0] = ys[0], out
                y = out
            e = 1.0 - y
            vc = Kp*e + x
            x += Kp*R/L*Ts*e
            i[kk + 1] = a_*i[kk] + b_*vprev
            vprev = vc
        t = np.arange(n + 1)*Ts*1e3
        axs[2].plot(t, i, color=col, lw=1.6, label="%s (최대 %.2f)" % (lab, i.max()))
    axs[0].axhline(0, color=INK2, lw=0.8)
    axs[0].axvline(1e4/(2*np.pi), color=INK2, ls="--", lw=1)
    axs[0].set(xlabel="주파수 [Hz]", ylabel="개루프 이득 [dB]", ylim=(-40, 40),
               title="(a) 교차 주파수: 개루프 이득이 0 dB가 되는 곳 (1.6 kHz)")
    axs[0].legend(fontsize=7.5, loc="lower left")
    axs[1].axhline(-180, color=INK, ls=":", lw=1)
    axs[1].axvline(1e4/(2*np.pi), color=INK2, ls="--", lw=1)
    axs[1].set(xlabel="주파수 [Hz]", ylabel="개루프 위상 [°]", ylim=(-300, -60),
               title="(b) 위상 여유 = 교차에서 −180°까지 남은 각")
    axs[1].legend(fontsize=7.5, loc="lower left")
    axs[2].axhline(1, color=INK2, ls=":", lw=1)
    axs[2].set(xlabel="시간 [ms]", ylabel="q축 전류 (지령 1 A 계단)", xlim=(0, 3),
               title="(c) 여유가 줄면 계단 응답이 더 튀고 흔들린다")
    axs[2].legend(fontsize=7.5, loc="lower right")
    fig.suptitle("위상 여유와 노치의 대가 — q축 전류 루프 (K$_p$ 16 Ω, L$_q$ 1.6 mH, 샘플 20 kHz, 연산 지연 1샘플)",
                 fontsize=10.5)
    fig.savefig(os.path.join(OUT, "phase_margin_notch.png"))
    plt.close(fig)


def fig_g_vs_A(hb, rem):
    """잘림을 없애는 두 길: 평균 명령을 내려 틈 g를 키우거나(여유, 전압 피드백 약자속) 명령 리플 A를 없앤다(노치).
    16 krpm 20 N·m, 데드타임 0, 조화균형 계산. 막대 = 평균 명령 ± 리플 진폭, 한계 위 몫이 잘린다."""
    VL = 403.2
    def rget(name):
        return next(x for x in rem if x["remedy"] == name and x["table"] == "QS 95" and x["T_ref"] == 20)
    m25 = next(x for x in hb if x["variant"] == "fea_pos" and x["table"] == "QS 75" and x["T_ref"] == 20 and x["td_us"] == 0)
    cases = [("대책 없음\n(여유 5 % 표)", rget("base")), ("여유 25 % 표", m25),
             ("전압 피드백 약자속\n(여유 5 % 표)", rget("fw")), ("노치\n(여유 5 % 표)", rget("notch"))]
    fig, ax = plt.subplots(figsize=(8.6, 4.6), constrained_layout=True)
    for k, (lab, x) in enumerate(cases):
        V, A = x["V_cmd"], x["dv_pk"]
        lo, hi = V - A, V + A
        ax.plot([k, k], [lo, min(hi, VL)], color=C[0], lw=14, solid_capstyle="butt", alpha=0.35)
        if hi > VL:
            ax.plot([k, k], [VL, hi], color=C[1], lw=14, solid_capstyle="butt", alpha=0.85)
        ax.plot(k, V, "o", color=INK, ms=6, zorder=5)
        ax.annotate("", xy=(k + 0.22, VL), xytext=(k + 0.22, V), arrowprops=dict(arrowstyle="<->", color=INK2, lw=1))
        ax.text(k + 0.27, (V + VL)/2, "g %.0f V" % (VL - V), fontsize=8, va="center", color=INK2)
        ax.text(k - 0.27, V + A/2, "A %.0f V" % A, fontsize=8, va="center", ha="right", color=INK2)
        T = x.get("T_shaft", 20.0)
        ax.text(k, 548, "잘림 %.0f %%\nT %.1f N·m" % (x["sat"] if x["sat"] > 1 else 100*x["sat"], T), ha="center",
                va="bottom", fontsize=8.5, color=INK)
    ax.axhline(VL, color=INK, ls="--", lw=1.2)
    ax.text(3.45, VL + 4, "한계 403 V", fontsize=8, ha="right", va="bottom")
    ax.set_xticks(range(len(cases)), [c[0] for c in cases], fontsize=8.5)
    ax.set(xlim=(-0.6, 3.6), ylim=(120, 600), ylabel="명령 전압 크기 [V 첨두]")
    ax.text(0.01, 0.01, "막대 = 평균 명령 ± 리플 진폭 A, 주황 = 한계 위(잘리는 몫). 16 krpm, 20 N·m, 조화균형 계산.",
            transform=ax.transAxes, fontsize=7.5, color=INK2, va="bottom")
    fig.suptitle("잘림을 없애는 두 길 — 평균을 내려 틈 g를 키우거나(여유, 약자속), 리플 A를 없앤다(노치)", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "g_vs_A.png"))
    plt.close(fig)


def fig_margin_vs_speed(hb, nsr, sims):
    """여유를 늘리는 것과 속도를 낮추는 것은 다른 손잡이다 (20 N·m), 그리고 노치의 속도 범위.
    hb: qs_harmonic_hb.json, nsr: notch_speed_range.json, sims: stage2e_speed_*.csv 행들"""
    VL = 403.2
    fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.1), constrained_layout=True)
    ax = axs[0]
    h = sorted([x for x in hb if x["variant"] == "fea_pos" and x["T_ref"] == 20 and x["td_us"] == 0
                and str(x["table"]).startswith("QS")], key=lambda x: -float(x["table"].split()[1]))
    m = np.array([100 - float(x["table"].split()[1]) for x in h])
    A = np.array([x["dv_pk"] for x in h])
    g = np.array([VL - x["V_cmd"] for x in h])
    ax.plot(m, A, "o-", color=C[1], label="리플 진폭 A (명령 전압)")
    ax.plot(m, g, "s-", color=C[0], label="틈 g = 한계 − 평균 명령")
    for mi, ai, x in zip(m, A, h):
        ax.annotate("잘림 %.0f %%" % x["sat"], (mi, ai + 6), ha="center", fontsize=7.5, color=INK2)
    ax.set(xlabel="교정표 전압 여유 [%]", ylabel="[V]", ylim=(0, 180),
           title="(a) 16 krpm에서 여유를 늘리면: g가 커진다")
    ax.text(0.03, 0.97, "기준 진각 %.2f° → %.2f°" % (h[0]["gamma_ref"], h[-1]["gamma_ref"]), transform=ax.transAxes,
            va="top", fontsize=8, color=INK2)
    ax.legend(fontsize=7.5, loc="center left")
    ax = axs[1]
    r20 = sorted([r for r in nsr if r["T"] == 20], key=lambda r: r["rpm"])
    n = np.array([r["rpm"] for r in r20])/1000
    A2 = np.array([r["base"]["dv_pk"] for r in r20])
    ax.plot(n, A2, "o-", color=C[1], label="리플 진폭 A")
    ax.axhline(0.05*VL, color=C[0], ls="--", lw=1.5, label="표의 여유 5 % (약 20 V)")
    for ni, ai, r in zip(n, A2, r20):
        eps = 90 - np.degrees(np.arctan2(-r["id_ref"], r["iq_ref"]))
        ax.annotate("ε %.1f°" % eps, (ni, ai + 6), ha="center", fontsize=7.5, color=INK2)
    ax.set(xlabel="속도 [krpm]", ylabel="[V]", ylim=(0, 180), xlim=(5, 17),
           title="(b) 속도를 낮추면: A가 줄고 90°에서 멀어진다")
    ax.legend(fontsize=7.5, loc="center right")
    ax = axs[2]
    for T, mk in ((20, "o"), (60, "s")):
        for rem, col, lab in (("base", C[1], "대책 없음"), ("notch", C[2], "노치")):
            pts = sorted((float(s["rpm"])/1000, float(s["err_pct"])) for s in sims
                         if s["remedy"] == rem and float(s["T_ref"]) == T)
            if pts:
                x, y = np.array(pts).T
                ax.plot(x, y, mk + "-", color=col, mfc=col if T == 20 else "white", mec=col, lw=1.4,
                        label="%s %d N·m (Simscape)" % (lab, T))
        hh = sorted([(r["rpm"]/1000, r["base"]["err"]) for r in nsr if r["T"] == T])
        if T == 20 and hh:
            x, y = np.array(hh).T
            ax.plot(x, y, ":", color=INK2, lw=1.2, label="대책 없음 20 N·m (HB)")
    ax.axhspan(-5, 5, color=GRID, alpha=0.5, lw=0)
    ax.set(xlabel="속도 [krpm]", ylabel="토크 오차 [%]", ylim=(-62, 8), xlim=(5, 17),
           title="(c) 노치의 속도 범위 (속도별 여유 5 % 표)")
    ax.legend(fontsize=7, loc="lower left")
    fig.suptitle("여유와 속도는 다른 손잡이다 — 여유는 틈 g를, 속도는 리플 A와 남은 각 ε를 바꾼다 "
                 "(20 N·m, 위치별 맵, 표준 제어기)", fontsize=10.5)
    fig.savefig(os.path.join(OUT, "margin_vs_speed.png"))
    plt.close(fig)


if __name__ == "__main__":
    A = json.load(open(os.path.join(WORK, "posmap_band_analysis.json")))
    fig_lab_check(A)
    fig_harmonics(A)
    p2d = os.path.join(DRV, "stage2d_results.csv")
    rows2d = list(csv.DictReader(open(p2d))) if os.path.exists(p2d) else []
    fig_variants(rows2d)
    rows_qs = []
    for n in ("stage2d_results_qs.csv", "stage2d_results_qs2.csv", "stage2d_results_qs3.csv"):
        if os.path.exists(os.path.join(DRV, n)):
            rows_qs += list(csv.DictReader(open(os.path.join(DRV, n))))
    phm = os.path.join(WORK, "qs_harmonic_margin.json")
    if rows_qs and os.path.exists(phm):
        fig_margin(rows_qs, json.load(open(phm)))
    if os.path.exists(phm):
        fig_same_current(json.load(open(phm)))
    phb = os.path.join(WORK, "qs_harmonic_hb.json")
    if os.path.exists(phb):
        fig_hb(json.load(open(phb)))
        fig_clamp()
    pe, pr = os.path.join(DRV, "stage2e_results_D.csv"), os.path.join(WORK, "qs_hb_remedies.json")
    if os.path.exists(pe) and os.path.exists(pr):
        fig_remedies(list(csv.DictReader(open(pe))), json.load(open(pr)))
    s2 = list(csv.DictReader(open(os.path.join(DRV, "stage2_results.csv"))))
    fig_qs([(os.path.join(WORK, "qs_lab_td0_m0_norac.json"), "t$_d$ 0", 0.0),
            (os.path.join(WORK, "qs_lab_td3_m0_norac.json"), "t$_d$ 3 µs", 3.0)], s2)
    print("figures written to", OUT)
