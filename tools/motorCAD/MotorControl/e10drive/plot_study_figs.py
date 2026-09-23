# -*- coding: utf-8 -*-
"""Figures for drive_model_study.html (theory of the e10 drive simulation models).

python plot_study_figs.py [study_data.mat] [out_dir]
  study_idiq_plane.png    id-iq plane: current/voltage limits, torque contours, MTPA, 16 krpm tables
  study_pwm_timing.png    centre-aligned carrier, double update, gate, deadtime volt-second error
  study_svpwm.png         voltage hexagon/limits and min-max zero-sequence injection
  study_delay.png         computation delay as a rotor-frame angle error, stage 1 vs stage 2
  study_sensitivity.png   torque and voltage vs phase advance at constant current (16 krpm)
  study_freq_ladder.png   frequencies of the 16 krpm operating point vs the controller
Colours: reference categorical slots 1-3 (#2a78d6, #eb6834, #1baf7a), neutral greys for limits.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.io import loadmat

SRC = sys.argv[1] if len(sys.argv) > 1 else r"D:\KangDH\Thesis\e10\work_lab_pc1\drive\study_data.mat"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"D:\KangDH\EveryMotor\eMach\tools\motorCAD\MotorControl"
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d3"
plt.rcParams.update({"font.family": ["Malgun Gothic", "DejaVu Sans"], "axes.unicode_minus": False, "font.size": 9,
                     "axes.titlesize": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "lines.linewidth": 2.0, "legend.frameon": False, "savefig.dpi": 150})

m = loadmat(SRC, squeeze_me=True)
idv, iqv = m["id_pk"].astype(float), m["iq_pk"].astype(float)
R, p, Vmax, Vdc, we16 = float(m["Rs"]), int(m["p"]), float(m["Vmax_pk"]), float(m["Vdc"]), float(m["we16"])
gFd = RegularGridInterpolator((iqv, idv), m["Fd"], bounds_error=False, fill_value=None)
gFq = RegularGridInterpolator((iqv, idv), m["Fq"], bounds_error=False, fill_value=None)
gT = RegularGridInterpolator((iqv, idv), m["T_shaft"], bounds_error=False, fill_value=None)


def lam(idq, iqq):
    pts = np.stack([np.asarray(iqq, float).ravel(), np.asarray(idq, float).ravel()], -1)
    shp = np.shape(idq)
    return gFd(pts).reshape(shp), gFq(pts).reshape(shp)


def torque(idq, iqq):
    pts = np.stack([np.asarray(iqq, float).ravel(), np.asarray(idq, float).ravel()], -1)
    return gT(pts).reshape(np.shape(idq))


def volt(idq, iqq, we):
    fd, fq = lam(idq, iqq)
    return np.hypot(R*idq - we*fq, R*iqq + we*fd)


def we_of(rpm):
    return p*rpm*2*np.pi/60


def char_current():
    """i_d where lambda_d(i_d, 0) = 0 (centre of the voltage ellipse)."""
    ids = np.linspace(-650, 0, 6501)
    fd, _ = lam(ids, np.zeros_like(ids))
    return float(ids[np.argmin(np.abs(fd))])


def tables():
    mcb = [(t, i, q) for t, i, q in zip(m["mcb_T"], m["mcb_id"], m["mcb_iq"]) if t <= 90]
    mbc = []
    for k in (1, 2, 3):
        mbc.append((float(m["mbc_factor"][k - 1]), m["mbc%d_T" % k], m["mbc%d_id" % k], m["mbc%d_iq" % k]))
    return np.array(mcb), mbc


# ------------------------------------------------------------------ 1. id-iq plane
def fig_idiq():
    fig, axs = plt.subplots(1, 2, figsize=(12.4, 5.4), constrained_layout=True)
    ID, IQ = np.meshgrid(np.linspace(-650, 0, 261), np.linspace(0, 650, 261))
    ax = axs[0]
    th = np.linspace(0, np.pi/2, 200)
    Imax = 460*np.sqrt(2)
    ax.plot(-Imax*np.sin(th), Imax*np.cos(th), "--", color=INK2, lw=1.4, label="전류 한계 460 A rms")
    TT = torque(ID, IQ)
    cs = ax.contour(ID, IQ, TT, levels=[50, 150, 300, 500, 800], colors="#a3a29d", linewidths=0.8)
    ax.clabel(cs, fmt="%d N·m", fontsize=7.5)
    greys = {4000: "#9b9a95", 8000: "#6b6a66", 16000: INK}
    for rpm, col in greys.items():
        V = volt(ID, IQ, we_of(rpm))
        c = ax.contour(ID, IQ, V, levels=[Vmax], colors=col, linewidths=1.8)
        seg = c.allsegs[0]
        if seg:
            s = max(seg, key=len)
            j = int(np.argmax(s[:, 1]))
            ax.annotate("%d rpm" % rpm, s[j], textcoords="offset points", xytext=(-14, 4), fontsize=8, color=col,
                        ha="right" if rpm == 16000 else "left")
        ax.plot([], [], color=col, lw=1.8, label="전압 한계 %d rpm" % rpm)
    # MTPA: 전류 크기마다 토크 최대가 되는 각
    Is = np.linspace(20, Imax, 60)
    g = np.radians(np.linspace(0, 89.5, 360))
    loc = []
    for I in Is:
        t = torque(-I*np.sin(g), I*np.cos(g))
        k = int(np.argmax(t))
        loc.append((-I*np.sin(g[k]), I*np.cos(g[k])))
    loc = np.array(loc)
    ax.plot(loc[:, 0], loc[:, 1], color=C1, label="MTPA (전류당 최대 토크)")
    ich = char_current()
    ax.plot(ich, 0, "X", color=INK, ms=9, clip_on=False, zorder=5, label="특성전류점 λ$_d$ = 0 (%.0f A)" % ich)
    for gam in (80, 85):
        r = np.array([0, 700])
        ax.plot(-r*np.sin(np.radians(gam)), r*np.cos(np.radians(gam)), ":", color=INK2, lw=1)
        ax.text(-560*np.sin(np.radians(gam)), 560*np.cos(np.radians(gam)) + 6, "γ = %d°" % gam, fontsize=8,
                color=INK2, ha="center", va="bottom", rotation=-np.degrees(np.arctan(1/np.tan(np.radians(gam)))))
    ax.set(xlim=(-660, 0), ylim=(0, 660), xlabel="i$_d$ [A 첨두]", ylabel="i$_q$ [A 첨두]", aspect="equal",
           title="(a) 운전 영역 — 속도가 오르면 전압 한계가 특성전류점 쪽으로 오그라든다")
    ax.legend(loc="upper right", fontsize=8, title="회색 가는 선: 토크 등고선 (16 krpm 축 토크맵)",
              title_fontsize=7.5, frameon=True, facecolor="white", edgecolor=GRID, framealpha=0.95)

    ax = axs[1]
    ID, IQ = np.meshgrid(np.linspace(-340, -140, 301), np.linspace(0, 48, 241))
    TT = torque(ID, IQ)
    cs = ax.contour(ID, IQ, TT, levels=[5, 20, 40, 60, 80], colors="#a3a29d", linewidths=0.8)
    ax.clabel(cs, fmt="%d N·m", fontsize=7.5)
    V = volt(ID, IQ, we16)
    for f, ls, lab in ((1.0, "-", "상전압 한계 100 % (403.2 V 첨두)"), (0.95, "--", "한계의 95 %"),
                       (0.90, ":", "한계의 90 %")):
        ax.contour(ID, IQ, V, levels=[f*Vmax], colors=INK, linewidths=1.5, linestyles=ls)
        ax.plot([], [], ls, color=INK, lw=1.5, label=lab)
    mcb, mbc = tables()
    ich = char_current()
    ax.plot(ich, 0, "X", color=INK, ms=9, clip_on=False, zorder=5)
    ax.annotate("특성전류점 (λ$_d$ = 0)\n%.0f A — 타원 중심" % ich, (ich, 0), textcoords="offset points", xytext=(6, 8),
                fontsize=8, color=INK)
    ax.plot(mcb[:, 1], mcb[:, 2], "-o", color=C1, ms=4, lw=1.5, label="MCB 기준표 (여유 ≈ 0)")
    for (f, T, i, q), col in zip(mbc[1:], (C2, C3)):
        ax.plot(i, q, "-s", color=col, ms=4, lw=1.5, label="MBC VsMax %d %%" % round(100*f))
    for gam in (84, 86, 88, 90):
        r = np.array([0, 400])
        ax.plot(-r*np.sin(np.radians(gam)), r*np.cos(np.radians(gam)), ":", color=INK2, lw=0.9)
        xr = -335
        yr = -xr/np.tan(np.radians(gam)) if gam < 90 else 0
        if yr < 47:
            ax.text(xr + 2, yr + 0.6, "%d°" % gam, fontsize=7.5, color=INK2)
    ax.set(xlim=(-340, -140), ylim=(0, 48), xlabel="i$_d$ [A 첨두]", ylabel="i$_q$ [A 첨두]",
           title="(b) 16 krpm 확대 — 모든 토크가 γ 84–90° 좁은 띠 안, 여유는 −d축 전류로 산다")
    ax.legend(loc="upper right", fontsize=8, ncol=2, frameon=True, facecolor="white", edgecolor=GRID,
              framealpha=0.95)
    fig.savefig(OUT + r"\study_idiq_plane.png")
    plt.close(fig)


# ------------------------------------------------------------------ 2. PWM timing & deadtime
def fig_pwm():
    Ts, td = 50.0, 3.0                   # µs
    t = np.arange(0, 200.0001, 0.02)
    k = np.minimum((t // Ts).astype(int), 3)
    tau = np.mod(t, 2*Ts)
    c = np.where(tau < Ts, tau/Ts, 2 - tau/Ts)
    d = np.array([0.60, 0.64, 0.68, 0.72])
    L = 1 - d[k]
    S = (c > L).astype(float)
    Sd = np.interp(t - td, t, S, left=0)
    up = np.minimum(S, Sd)              # i > 0: 켜짐 에지만 td 늦음
    dn = np.maximum(S, Sd)              # i < 0: 꺼짐 에지만 td 늦음
    fig, axs = plt.subplots(4, 1, figsize=(11, 6.6), sharex=True, constrained_layout=True,
                            gridspec_kw=dict(height_ratios=[1.6, 0.8, 0.8, 0.8]))
    ax = axs[0]
    ax.plot(t, c, color=INK2, lw=1.4, label="삼각파 캐리어 (10 kHz, 중앙정렬)")
    for j in range(4):
        ax.plot([j*Ts, (j + 1)*Ts], [L[j*2500 + 1]]*2, color=C1, lw=2)
    ax.plot([], [], color=C1, label="비교값 1 - d$_k$ (반주기마다 갱신 = 양 끝 갱신)")
    for j in range(5):
        ax.plot(j*Ts, 0 if j % 2 == 0 else 1, "^" if j % 2 == 0 else "v", color=C2, ms=9, clip_on=False)
    ax.plot([], [], "^", color=C2, ms=8, label="전류 샘플·듀티 갱신 (골·꼭짓점 = 리플 평균점)")
    for j, txt in enumerate(("상승 반주기", "하강 반주기", "상승 반주기", "하강 반주기")):
        ax.text(j*Ts + Ts/2, 1.07, txt, ha="center", fontsize=8.5, color=INK2)
    ax.annotate("", xy=(Ts + 2, 0.42), xytext=(2, 0.42), arrowprops=dict(arrowstyle="->", color=C1, lw=1))
    ax.text(Ts/2 + 1, 0.45, "샘플 k로 계산 → 반주기 k+1에 인가 (n = 1)", ha="center", fontsize=8, color=C1)
    ax.set(ylim=(-0.05, 1.18), yticks=[0, 0.5, 1], ylabel="캐리어")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=8, ncol=3)
    for ax, y, lab in ((axs[1], S, "게이트 지령 S$_a$"),):
        ax.plot(t, y, color=INK, lw=1.4)
        ax.set(ylim=(-0.2, 1.3), yticks=[0, 1], ylabel=lab)
    ax = axs[2]
    ax.plot(t, up, color=INK, lw=1.4)
    ax.fill_between(t, up, S, where=S > up, color=C2, alpha=0.55, step=None, label="잃는 볼트·초")
    ax.set(ylim=(-0.2, 1.3), yticks=[0, 1], ylabel="폴 전압\ni$_a$ > 0")
    ax.text(3, 1.08, "켜짐 에지만 t$_d$ = 3 µs 늦는다 (하단 다이오드가 도통) → 캐리어 주기마다 V$_{dc}$·t$_d$ 손실",
            fontsize=8, color=INK)
    ax = axs[3]
    ax.plot(t, dn, color=INK, lw=1.4)
    ax.fill_between(t, S, dn, where=dn > S, color=C3, alpha=0.55)
    ax.set(ylim=(-0.2, 1.3), yticks=[0, 1], ylabel="폴 전압\ni$_a$ < 0", xlabel="시간 [µs]  (T$_s$ = 50 µs, T$_{pwm}$ = 100 µs)")
    ax.text(3, 1.08, "꺼짐 에지만 늦는다 (상단 다이오드가 도통) → 캐리어 주기마다 V$_{dc}$·t$_d$ 이득", fontsize=8, color=INK)
    for a in axs:
        a.grid(axis="y", visible=False)
        for j in range(5):
            a.axvline(j*Ts, color=GRID, lw=0.8, zorder=0)
    fig.suptitle("중앙정렬 PWM · 양 끝 갱신 · 데드타임 — 한 상(a)의 두 캐리어 주기", fontsize=10.5)
    fig.savefig(OUT + r"\study_pwm_timing.png")
    plt.close(fig)


# ------------------------------------------------------------------ 3. SVPWM
def fig_svpwm():
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.9), constrained_layout=True,
                            gridspec_kw=dict(width_ratios=[1, 1.35]))
    ax = axs[0]
    Vh = 2*Vdc/3
    ang = np.radians(np.arange(0, 361, 60))
    ax.plot(Vh*np.cos(ang), Vh*np.sin(ang), color=INK2, lw=1.4)
    names = ["100", "110", "010", "011", "001", "101"]
    for a, n in zip(ang[:-1], names):
        ax.plot([0, Vh*np.cos(a)], [0, Vh*np.sin(a)], color=GRID, lw=0.8)
        ax.text(1.1*Vh*np.cos(a), 1.1*Vh*np.sin(a), n, ha="center", va="center", fontsize=8.5, color=INK2)
    ax.text(0, -30, "000 / 111", ha="center", fontsize=8, color=INK2)
    th = np.linspace(0, 2*np.pi, 300)
    for r, ls, col, lab in ((Vdc/np.sqrt(3), "--", INK2, "선형 한계 V$_{dc}$/√3 = 415.7 V"),
                            (Vmax, "-", C1, "제어기 한계 403.2 V (285.1 V rms)"),
                            (Vdc/2, ":", "#a3a29d", "정현파 PWM 한계 V$_{dc}$/2 = 360 V")):
        ax.plot(r*np.cos(th), r*np.sin(th), ls, color=col, lw=1.6 if col == C1 else 1.2, label=lab)
    ax.annotate("", xy=(Vmax*np.cos(1.1), Vmax*np.sin(1.1)), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=C2, lw=2))
    ax.annotate("16 krpm 운전점 전압 |v| ≈ 403 V", xy=(Vmax*np.cos(1.1), Vmax*np.sin(1.1)), xytext=(-545, 520),
                fontsize=8, color=INK, arrowprops=dict(arrowstyle="->", color=INK2, lw=0.8))
    ax.set(aspect="equal", xlim=(-560, 560), ylim=(-560, 560), xlabel="v$_α$ [V]", ylabel="v$_β$ [V]",
           title="(a) 전압 육각형과 한계")
    ax.legend(loc="upper center", fontsize=7.5, bbox_to_anchor=(0.5, -0.13), ncol=1)
    ax = axs[1]
    thd = np.linspace(0, 360, 721)
    thr = np.radians(thd)
    va = Vmax*np.cos(thr)
    vb = Vmax*np.cos(thr - 2*np.pi/3)
    vc = Vmax*np.cos(thr + 2*np.pi/3)
    vzs = -(np.maximum(np.maximum(va, vb), vc) + np.minimum(np.minimum(va, vb), vc))/2
    ax.plot(thd, va, color=C1, label="상 지령 v$_a$* (진폭 403.2 V)")
    ax.plot(thd, vzs, color=C2, label="영상분 v$_{zs}$ = -(max + min)/2")
    ax.plot(thd, va + vzs, color=C3, label="변조 지령 v$_a$* + v$_{zs}$ (폴 기준)")
    for s in (1, -1):
        ax.axhline(s*Vdc/2, color=INK2, lw=1.1, ls="--")
    ax.text(120, Vdc/2 + 12, "±V$_{dc}$/2 = ±360 V (듀티 0·1)", fontsize=8, color=INK2)
    ax.annotate("변조 지령 최대 %.0f V < 360 V" % (Vmax*np.sqrt(3)/2), xy=(30, Vmax*np.sqrt(3)/2), xytext=(100, 250),
                fontsize=8, color=INK, arrowprops=dict(arrowstyle="->", color=INK2, lw=0.8))
    ax.set(xlim=(0, 360), xticks=range(0, 361, 60), ylim=(-470, 470), xlabel="전기각 [deg]", ylabel="전압 [V]",
           title="(b) min-max 영상분 주입 — 정현파 진폭 403 V가 ±360 V 안에 들어간다")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), fontsize=8, ncol=3)
    fig.savefig(OUT + r"\study_svpwm.png")
    plt.close(fig)


# ------------------------------------------------------------------ 4. delay
def fig_delay():
    wTs = np.degrees(we16*50e-6)         # 19.2 deg per sample
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.3), constrained_layout=True)
    ax = axs[0]
    x = np.linspace(1, 2, 50)
    ax.axvspan(1, 2, color="#f0efec", zorder=0)
    ax.plot(x, -wTs*x, color=C1, label="보상 없음: -ω$_e$(t - t$_k$)")
    ax.plot(x, -wTs*x + 1.5*wTs, color=C2, label="보상 ω$_e$(n+½)T$_s$ = +%.1f°" % (1.5*wTs))
    ax.axhline(-1.5*wTs, color=C1, lw=1, ls="--")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.text(2.04, -1.5*wTs + 1, "평균 −%.1f°" % (1.5*wTs), va="bottom", fontsize=8, color=INK)
    ax.text(2.04, 1, "보상 후 평균 0°\n(±%.1f° 리플)" % (wTs/2), va="bottom", fontsize=8, color=INK)
    ax.plot(0, 0, "o", color=INK, ms=6)
    ax.text(0.03, 3, "샘플 k: 전류 읽고\n지령 계산 (각 θ$_k$)", fontsize=8, color=INK)
    ax.text(1.5, 14, "인가 구간 [t$_{k+1}$, t$_{k+2}$]\n정지 좌표계에서 전압 고정", ha="center", fontsize=8, color=INK2)
    ax.set(xlim=(-0.05, 2.6), ylim=(-45, 25), xticks=[0, 1, 2], xticklabels=["t$_k$", "t$_{k+1}$", "t$_{k+2}$"],
           ylabel="회전자 좌표계에서 본 전압 벡터 각 오차 [deg]",
           title="(a) 1샘플 지연(n = 1)의 각 오차 — 16 krpm, 샘플당 %.1f°" % wTs)
    ax.legend(loc="lower left", fontsize=8)
    ax = axs[1]
    n = np.arange(3)
    w = 0.26
    s1 = +(n + 0.5)*wTs
    s2n = -(n + 0.5)*wTs
    s2c = np.zeros(3)
    ax.bar(n - w, s1, w*0.9, color=C1, label="단계 1: dq에서 지연 + 보상 (인공물)")
    ax.bar(n, s2n, w*0.9, color=C2, label="단계 2: αβ 유지, 보상 없음")
    ax.bar(n + w, s2c, w*0.9, color=C3, yerr=wTs/2, capsize=4, ecolor=C3, label="단계 2: αβ 유지 + 보상")
    for xx, v in zip(n - w, s1):
        ax.text(xx, v + 2, "%+.0f°" % v, ha="center", fontsize=8, color=INK)
    for xx, v in zip(n, s2n):
        ax.text(xx, v - 5, "%+.0f°" % v, ha="center", fontsize=8, color=INK)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set(xticks=n, xticklabels=["지연 0샘플", "1샘플", "2샘플"], ylim=(-62, 62), ylabel="평균 각 오차 [deg]",
           title="(b) 모형별 순 각 오차 — 단계 1의 ‘2샘플 붕괴’는 보상각 +48°였다")
    ax.legend(loc="lower left", fontsize=8)
    fig.savefig(OUT + r"\study_delay.png")
    plt.close(fig)


# ------------------------------------------------------------------ 5. sensitivity
def fig_sens():
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.3), constrained_layout=True)
    gam = np.linspace(80, 92, 241)
    mcb, _ = tables()
    for (Tref, col) in ((20, C1), (40, C2), (60, C3)):
        i0 = np.interp(Tref, mcb[:, 0], mcb[:, 1])
        q0 = np.interp(Tref, mcb[:, 0], mcb[:, 2])
        I = np.hypot(i0, q0)
        g0 = np.degrees(np.arctan2(-i0, q0))
        idg, iqg = -I*np.sin(np.radians(gam)), I*np.cos(np.radians(gam))
        T = torque(idg, iqg)
        V = volt(idg, iqg, we16)/np.sqrt(2)
        lab = "%d N·m 기준점 전류 %.0f A rms" % (Tref, I/np.sqrt(2))
        axs[0].plot(gam, T, color=col, label=lab)
        axs[1].plot(gam, V, color=col, label=lab)
        T0 = float(torque(np.array([i0]), np.array([q0]))[0])
        V0 = float(volt(np.array([i0]), np.array([q0]), we16)[0])/np.sqrt(2)
        axs[0].plot(g0, T0, "o", color=col, ms=8, mec="white", mew=1.5)
        axs[1].plot(g0, V0, "o", color=col, ms=8, mec="white", mew=1.5)
        sl = np.gradient(T, gam)[np.argmin(np.abs(gam - g0))]
        axs[0].annotate("γ %.2f°, dT/dγ = %.1f N·m/°" % (g0, sl), (g0, T0), textcoords="offset points",
                        xytext=(-12, -4), ha="right", va="top", fontsize=8, color=INK)
    axs[0].axhline(0, color=INK2, lw=0.8)
    axs[0].set(xlabel="진각 γ [deg]", ylabel="축 토크 [N·m]", ylim=(-60, 140),
               title="(a) 같은 전류에서 진각만 바꿀 때의 토크 — 1°가 10–20 N·m")
    axs[0].legend(loc="upper right", fontsize=8)
    axs[1].axhline(285.1, color=INK, lw=1.2, ls="--")
    axs[1].text(80.2, 290, "상전압 한계 285.1 V rms", fontsize=8, color=INK)
    axs[1].set(xlabel="진각 γ [deg]", ylabel="상전압 [V rms]", ylim=(150, 600),
               title="(b) 같은 전류의 상전압 — 기준점이 모두 한계선에 붙어 있다 (여유 0)")
    axs[1].legend(loc="upper right", fontsize=8)
    fig.suptitle("16 krpm 운전점의 민감도 (Lab 맵, 점 = MCB 기준표 운전점)", fontsize=10.5)
    fig.savefig(OUT + r"\study_sensitivity.png")
    plt.close(fig)


# ------------------------------------------------------------------ 6. frequency ladder
def fig_freq():
    fe = 16000/60*p
    wc = 8.5/0.85e-3
    items = [(fe, "전기 기본파 f$_e$ (16 krpm)"), (wc/2/np.pi, "전류 루프 대역 ω$_c$/2π = K$_p$/(2πL)"),
             (1e4, "캐리어 f$_{pwm}$"), (2e4, "샘플·갱신 1/T$_s$ (양 끝 갱신)"),
             (1/2e-6, "사건 사이 RK4 최대 스텝 1/h$_{max}$")]
    fig, ax = plt.subplots(figsize=(10.5, 2.9), constrained_layout=True)
    for j, (f, lab) in enumerate(items):
        ax.plot(f, 0, "o", color=C1 if j else C2, ms=10, mec="white", mew=1.5, zorder=3)
        ax.annotate("%s\n%s Hz" % (lab, format(round(f), ",")), (f, 0), textcoords="offset points",
                    xytext=(0, 14 if j % 2 == 0 else -40), ha="center", fontsize=8, color=INK)
    ax.plot([items[0][0], items[2][0]], [0.55, 0.55], color=INK2, lw=1)
    ax.text(np.sqrt(items[0][0]*items[2][0]), 0.62, "펄스비 %.1f (전기 한 주기에 캐리어 %.1f주기)" % (1e4/fe, 1e4/fe),
            ha="center", fontsize=8, color=INK2)
    ax.set(xscale="log", xlim=(500, 1e6), ylim=(-1.1, 1.0), yticks=[], xlabel="주파수 [Hz] (로그)",
           title="16 krpm에서 기본파는 전류 루프 대역(1.6 kHz) 바로 아래, 샘플 한 번에 전기각 19.2°")
    ax.grid(axis="y", visible=False)
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    fig.savefig(OUT + r"\study_freq_ladder.png")
    plt.close(fig)


if __name__ == "__main__":
    for f in (fig_idiq, fig_pwm, fig_svpwm, fig_delay, fig_sens, fig_freq):
        f()
        print("ok", f.__name__)
