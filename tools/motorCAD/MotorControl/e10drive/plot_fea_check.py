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
