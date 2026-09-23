# -*- coding: utf-8 -*-
"""Figures for stage 2 (switching inverter, 10 kHz SVPWM, deadtime) at 16 000 rpm.

python plot_stage2.py [drive_dir] [out_dir]
Reads stage2_results.csv and stage2_traces.mat; writes stage2_summary.png, stage2_currents.png and
stage2_thd.json (phase-current THD over the last two electrical periods).
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import loadmat

DRV = sys.argv[1] if len(sys.argv) > 1 else r"D:\KangDH\Thesis\e10\work_lab_pc1\drive"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"D:\KangDH\EveryMotor\eMach\tools\motorCAD\MotorControl"
df = pd.read_csv(os.path.join(DRV, "stage2_results.csv"))
plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9})

fig, axs = plt.subplots(2, 2, figsize=(11, 7.4), constrained_layout=True)
# (a) deadtime and its compensation
ax = axs[0, 0]
d = df[df.kind == "deadtime"]
cm = plt.cm.copper(np.linspace(0.15, 0.85, 4))
for c, td in zip(cm, (0, 1, 2, 3)):
    s = d[d.td_us == td].sort_values("T_ref")
    ax.plot(s.T_ref, s["T"], "-o", color=c, ms=4, label="td %d µs, no comp." % td)
dc = df[df.kind == "dt_comp"]
for ls, td in (("--", 2), (":", 3)):
    s = dc[dc.td_us == td].sort_values("T_ref")
    ax.plot(s.T_ref, s["T"], ls, marker="s", color="#2f6f8f", ms=4, label="td %d µs, deadtime comp." % td)
ax.plot([0, 90], [0, 90], color="0.6", lw=0.8)
ax.set(xlabel="torque reference [N·m]", ylabel="realized shaft torque [N·m]",
       title="(a) Deadtime: realized torque at 16 000 rpm (delay 1 sample, compensated)")
ax.legend(fontsize=7)
# (b) resolver offset x computation delay
ax = axs[0, 1]
o = df[df.kind == "offset_delay"]
w = 0.26
for j, T in enumerate((20, 60)):
    for i, th in enumerate((0, 1, 2)):
        s = o[(o.T_ref == T) & (o.offset_deg == th)].sort_values("delay_samples")
        x = np.arange(3) + (i - 1)*w + 3.6*j
        ax.bar(x, s.err_pct, w*0.95, color=plt.cm.Blues(0.35 + 0.25*i),
               label=("offset %d°" % th) if j == 0 else None)
    ax.text(3.6*j + 1, 12, "%d N·m" % T, ha="center")
ax.set_xticks(list(np.arange(3)) + list(np.arange(3) + 3.6), ["0", "1", "2"]*2)
ax.axhline(0, color="k", lw=0.6)
ax.set(xlabel="computation delay [samples of 50 µs] (compensated)", ylabel="torque error [%]", ylim=(-125, 20),
       title="(b) Resolver offset × delay (td 2 µs): offset matters, delay does not")
ax.legend(fontsize=7, loc="lower left")
# (c) torque ceiling and realized gamma
ax = axs[1, 0]
c = df[df.kind == "ceiling"]
for td, col in ((0, "#b8753f"), (2, "#2f6f8f")):
    s = c[c.td_us == td].sort_values("T_ref")
    ax.plot(s.T_ref, s["T"], "-o", color=col, ms=4, label="realized T, td %d µs" % td)
ax.plot([0, 100], [0, 100], color="0.6", lw=0.8)
ax.set(xlabel="torque reference [N·m]", ylabel="realized torque [N·m]",
       title="(c) Closed-loop ceiling; labels = realized phase advance γ (td 0)")
s0 = c[c.td_us == 0].sort_values("T_ref")
for _, r in s0.iterrows():
    if r.T_ref in (5, 20, 40, 60, 80, 100):
        ax.annotate("%.1f°" % r.gamma, (r.T_ref, r["T"]), textcoords="offset points", xytext=(-4, 7),
                    ha="right", fontsize=7)
ax.legend(fontsize=7, loc="upper left")
# (d) delay compensation on/off
ax = axs[1, 1]
dl = df[df.kind == "delay_comp"]
lab, val, col = [], [], []
for td in (0, 2):
    for T in (20, 60):
        for dcm in (1, 0):
            r = dl[(dl.td_us == td) & (dl.T_ref == T) & (dl.delay_comp == dcm)].iloc[0]
            lab.append("%d N·m\ntd %d\n%s" % (T, td, "comp" if dcm else "none"))
            val.append(r.err_pct)
            col.append("#2f6f8f" if dcm else "#aa3333")
ax.bar(range(len(val)), val, color=col)
for i, v in enumerate(val):
    ax.text(i, v + (4 if v > -60 else -30), "%.0f" % v, ha="center", fontsize=7,
            color="k" if v > -60 else "w")
ax.set_xticks(range(len(val)), lab, fontsize=7)
ax.axhline(0, color="k", lw=0.6)
ax.set(ylabel="torque error [%]", ylim=(-700, 30),
       title="(d) Delay compensation ωe(n+½)Ts on/off (1-sample delay)")
fig.suptitle("Stage 2 — switching inverter (10 kHz SVPWM, double update, deadtime) on Lab flux maps, e10 at 16 000 rpm",
             fontsize=10)
fig.savefig(os.path.join(OUT, "stage2_summary.png"), dpi=150)

# ---- phase currents and THD
m = loadmat(os.path.join(DRV, "stage2_traces.mat"), squeeze_me=True, struct_as_record=False)
cases = np.atleast_1d(m["cases"])
fe = 16000/60*4        # 4 pole pairs -> 1066.7 Hz
thd = []
fig, axs = plt.subplots(1, 3, figsize=(12, 3.6), constrained_layout=True, sharey=False)
for j, T in enumerate((5, 20, 60)):
    for cs in cases:
        if cs.T_ref != T:
            continue
        tr = cs.trace
        t = np.asarray(tr.t, float)
        ia = np.asarray(tr.ia, float)
        t, iu = np.unique(t, return_index=True)
        ia = ia[iu]
        n = 4096
        tu = np.linspace(t[-1] - 2/fe, t[-1], n, endpoint=False)
        iu_ = np.interp(tu, t, ia)
        X = np.abs(np.fft.rfft(iu_))/n*2
        h1 = X[2]                                  # two periods in the window -> fundamental at bin 2
        h = np.sqrt(np.sum(X[3:]**2))
        thd.append(dict(T_ref=float(T), td_us=float(cs.td_us), I1_pk=float(h1), THD_pct=float(100*h/h1)))
        axs[j].plot((tu - tu[0])*1e3, iu_, lw=0.9, label="td %g µs, THD %.1f %%" % (cs.td_us, 100*h/h1),
                    color="#b8753f" if cs.td_us == 0 else "#2f6f8f")
    axs[j].set(title="%d N·m reference" % T, xlabel="time [ms] (2 electrical periods)", ylabel="phase-a current [A]")
    axs[j].legend(fontsize=7)
fig.suptitle("Stage 2 — phase current at 16 000 rpm, 10 kHz carrier (≈ 9.4 carrier periods per electrical period)",
             fontsize=10)
fig.savefig(os.path.join(OUT, "stage2_currents.png"), dpi=150)
json.dump(thd, open(os.path.join(OUT, "stage2_thd.json"), "w"), indent=1)
for r in thd:
    print(r)
