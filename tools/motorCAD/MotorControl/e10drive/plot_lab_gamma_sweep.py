# -*- coding: utf-8 -*-
"""Figure for stage 3(a): Lab FMU constant-torque gamma sweeps (loss and voltage vs phase advance)."""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = sys.argv[1] if len(sys.argv) > 1 else r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\lab_gamma_sweep.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"D:\KangDH\EveryMotor\eMach\tools\motorCAD\MotorControl\stage3_lab_gamma_sweep.png"
d = json.load(open(SRC))
vlim = d["V_limit_rms"]
plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9})
fig, axs = plt.subplots(2, 3, figsize=(12, 6.2), constrained_layout=True, sharex="col")
cols = {20.0: "#b8753f", 60.0: "#2f6f8f"}
for j, rpm in enumerate((4000.0, 8000.0, 16000.0)):
    for T in (20.0, 60.0):
        pts = [p for p in d["sweep"] if p["rpm"] == rpm and p["T_req"] == T and p["status"] == "ok"]
        g = [p["gamma"] for p in pts]
        L = [p["P_loss"]/1e3 for p in pts]
        V = [p["Phase_Voltage_RMS"] for p in pts]
        feas = [p["V_feasible"] for p in pts]
        o = [x for x in d["optimum"] if x["rpm"] == rpm and x["T_req"] == T][0]
        c = cols[T]
        axs[0, j].plot(g, L, "-", color=c, lw=1.0, alpha=0.6)
        axs[0, j].plot([a for a, f in zip(g, feas) if f], [b for b, f in zip(L, feas) if f], "o", color=c, ms=4,
                       label="%d N·m, voltage-feasible" % T)
        axs[0, j].plot([a for a, f in zip(g, feas) if not f], [b for b, f in zip(L, feas) if not f], "x", color=c,
                       ms=4, label="%d N·m, exceeds voltage" % T)
        axs[0, j].plot(o["Phase_Advance"], o["P_loss"]/1e3, "*", color="k", ms=10)
        axs[0, j].annotate("Lab opt %.1f°" % o["Phase_Advance"], (o["Phase_Advance"], o["P_loss"]/1e3),
                           textcoords="offset points", fontsize=7,
                           xytext=((8 if o["Phase_Advance"] < 40 else -78), (-12 if T == 20 else 8)))
        axs[1, j].plot(g, V, "-o", color=c, ms=3, label="%d N·m" % T)
    axs[1, j].axhline(vlim, color="k", lw=0.8, ls="--", label="limit %.1f V rms" % vlim)
    axs[1, j].axvline(80, color="#aa3333", lw=0.8, ls=":")
    axs[0, j].axvline(80, color="#aa3333", lw=0.8, ls=":")
    axs[0, j].set_yscale("log")
    axs[0, j].set(title="%d rpm: total loss on constant-torque line" % rpm, ylabel="loss [kW]")
    axs[1, j].set(xlabel="phase advance γ [deg] (red: 80°)", ylabel="phase voltage [V rms]", ylim=(0, 1100))
    axs[0, j].legend(fontsize=6.5, loc="upper left")
    axs[1, j].legend(fontsize=6.5, loc="upper right")
fig.suptitle("Stage 3 — Motor-CAD Lab FMU (e10, 720 V, 80 °C): forced phase advance, current solved for the torque", fontsize=10)
fig.savefig(OUT, dpi=150)
print("wrote", OUT)
