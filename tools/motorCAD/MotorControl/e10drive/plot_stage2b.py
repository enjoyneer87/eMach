# -*- coding: utf-8 -*-
"""Figure for stage 2b: calibration voltage margin (MCB vs MBC VsMax 100/95/90 %) in the switching model,
with the Lab FMU loss of each reference point (stage 3(c)).

python plot_stage2b.py [drive_dir] [lab_stage3c.json] [out.png]
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DRV = sys.argv[1] if len(sys.argv) > 1 else r"D:\KangDH\Thesis\e10\work_lab_pc1\drive"
J3C = sys.argv[2] if len(sys.argv) > 2 else r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\lab_stage3c.json"
OUT = sys.argv[3] if len(sys.argv) > 3 else r"D:\KangDH\EveryMotor\eMach\tools\motorCAD\MotorControl\stage2b_margin.png"
rows = list(csv.DictReader(open(os.path.join(DRV, "stage2b_results.csv"))))
for r in rows:
    for k in r:
        if k != "table":
            r[k] = float(r[k])
loss = {p["tag"]: p for p in json.load(open(J3C))["points"]} if os.path.exists(J3C) else {}
TABLES = ["MCB", "MBC 100", "MBC 95", "MBC 90"]
TDS = ((0, 0, "td 0"), (2, 0, "td 2 µs"), (3, 0, "td 3 µs"), (3, 1, "td 3 µs + comp."))
COL = ["#1f2328", "#b8753f", "#e0a36e", "#2f6f8f"]


def get(tb, T, td, dc):
    return [r for r in rows if r["table"] == tb and r["T_ref"] == T and r["td_us"] == td and r["dt_comp"] == dc][0]


plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9})
fig, axs = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
w = 0.2
for ax, T, lo in ((axs[0], 5, -120), (axs[1], 20, -50)):
    for i, (td, dc, lab) in enumerate(TDS):
        v = [get(tb, T, td, dc)["err_pct"] for tb in TABLES]
        x = np.arange(4) + (i - 1.5)*w
        ax.bar(x, np.maximum(v, lo), w*0.95, color=COL[i], label=lab)
        for xx, vv in zip(x, v):
            if vv < lo:
                ax.text(xx, lo + 2, "%.0f" % vv, rotation=90, ha="center", va="bottom", fontsize=6.5, color="w")
    ax.axhspan(-5, 5, color="0.9", zorder=0)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(range(4), ["MCB\n(margin ≈ 0)", "MBC\nVsMax 100 %", "MBC\nVsMax 95 %", "MBC\nVsMax 90 %"])
    ax.set(ylabel="torque error [%]", ylim=(lo, 12), title="(%s) %d N·m at 16 000 rpm" % ("a" if T == 5 else "b", T))
axs[0].legend(fontsize=7, loc="lower right")
ax = axs[2]
for j, tb in enumerate(TABLES):
    ys = []
    for T in (5, 20, 40, 60):
        p = loss.get("s2bref|%s|T%g" % (tb, T))
        ys.append(100*(p["P_loss"]/p["opt_P_loss"] - 1) if p and p.get("opt_P_loss") else np.nan)
    ax.plot((5, 20, 40, 60), ys, "-o", ms=4, color=["#1f2328", "#b8753f", "#2f6f8f", "#5a9e6f"][j], label=tb)
ax.axhline(0, color="k", lw=0.6)
ax.set(xlabel="torque reference [N·m]", ylabel="Lab loss vs Lab optimum at same torque [%]",
       title="(c) Price of the margin (Lab FMU at the table point)")
ax.legend(fontsize=7)
fig.suptitle("Stage 2b — calibration voltage margin in the switching model (MCB table vs MBC calibratepmsm), "
             "e10 at 16 000 rpm", fontsize=10)
fig.savefig(OUT, dpi=150)
print("wrote", OUT)
