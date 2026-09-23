# -*- coding: utf-8 -*-
"""Figure for stage 3(c): Lab FMU losses at the operating points the switching drive reaches (16 000 rpm).

python plot_stage3c.py [lab_stage3c.json] [out.png]
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = sys.argv[1] if len(sys.argv) > 1 else r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\lab_stage3c.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"D:\KangDH\EveryMotor\eMach\tools\motorCAD\MotorControl\stage3c_losses.png"
d = json.load(open(SRC))
pts = d["points"]


def parse(tag):
    f = tag.split("|")
    out = dict(src=f[0], kind=f[1])
    for x in f[2:]:
        for k in ("T", "td", "dc", "off", "nd"):
            if x.startswith(k) and x[len(k):].replace(".", "").replace("-", "").isdigit():
                out[k] = float(x[len(k):])
    return out


plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9})
fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.3), constrained_layout=True)
opt = sorted([(p["opt_T"], p["opt_P_loss"]/1e3) for p in pts if "opt_T" in p])
ax = axs[0]
ax.plot([o[0] for o in opt], [o[1] for o in opt], "-", color="0.4", lw=1.2, label="Lab optimum (mode 0) at that torque")
sty = {("deadtime", 0): ("#1f2328", "o"), ("deadtime", 1): ("#7a4a22", "o"), ("deadtime", 2): ("#b8753f", "o"),
       ("deadtime", 3): ("#e0a36e", "o")}
done = set()
for p in pts:
    q = parse(p["tag"])
    if q["src"] != "s2":
        continue
    if q["kind"] == "deadtime":
        c, m = sty[("deadtime", int(q["td"]))]
        lab = "td %d µs, no comp." % q["td"]
    elif q["kind"] == "dt_comp":
        c, m, lab = "#2f6f8f", "s", "deadtime comp."
    elif q["kind"] == "offset_delay" and q["off"] > 0 and q["nd"] == 1:
        c, m, lab = "#aa3333", "^", "resolver offset 1–2° (td 2 µs)"
    else:
        continue
    ax.plot(p["Shaft_Torque"], p["P_loss"]/1e3, m, color=c, ms=5, mfc="none" if m == "^" else c,
            label=None if lab in done else lab)
    done.add(lab)
    ax.annotate("", xy=(p["Shaft_Torque"], p["P_loss"]/1e3), xytext=(q["T"], p["P_loss"]/1e3),
                arrowprops=dict(arrowstyle="->", color=c, lw=0.6, alpha=0.5))
ax.set(xlabel="shaft torque delivered (FMU at realized I, γ) [N·m]", ylabel="total loss [kW]",
       title="(a) Errors cost torque, not loss: arrows run from the commanded to the delivered torque", xlim=(-20, 90))
ax.legend(fontsize=7, loc="upper left")
ax = axs[1]
rows = []
for p in pts:
    q = parse(p["tag"])
    if q["src"] == "s2" and q["kind"] in ("deadtime", "dt_comp") and q["T"] in (20, 60, 85):
        rows.append((q, p))
for j, T in enumerate((20, 60, 85)):
    base = [p for q, p in rows if q["T"] == T and q["kind"] == "deadtime" and q["td"] == 0][0]
    xs, eff = [], []
    for k, (kind, td) in enumerate((("deadtime", 0), ("deadtime", 1), ("deadtime", 2), ("deadtime", 3),
                                    ("dt_comp", 2), ("dt_comp", 3))):
        p = [p for q, p in rows if q["T"] == T and q["kind"] == kind and q["td"] == td][0]
        wpt = p["P_loss"]/max(p["Shaft_Torque"], 1e-3)
        ax.bar(j*7.5 + k, wpt, color=("#2f6f8f" if kind == "dt_comp" else sty[("deadtime", td)][0]),
               label=(("td %d µs" % td) if kind == "deadtime" else ("td %d µs + comp." % td)) if j == 0 else None)
    ax.text(j*7.5 + 2.5, -12, "%d N·m" % T, ha="center", va="top", fontsize=8)
ax.set_xticks([])
ax.set(ylabel="loss per delivered torque [W/(N·m)]",
       title="(b) Loss per delivered N·m at 16 000 rpm (commanded 20/60/85 N·m)")
ax.legend(fontsize=7)
fig.suptitle("Stage 3(c) — Motor-CAD Lab FMU evaluated at the stage-2 realized operating points, 16 000 rpm", fontsize=10)
fig.savefig(OUT, dpi=150)
print("wrote", OUT)
