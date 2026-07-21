# -*- coding: utf-8 -*-
import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import numpy as np, os
OUT=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\viz"
data = {
    "MAPDL\n(e10 oil-cooled\nsteady conduction)": dict(t=13.5, note="544k nodes/317k tet10, static"),
    "Icepak\n(Prius fixed-T\nconduction+jacket)": dict(t=94.0, note="250A, conduction+convection"),
    "FreeFlow\n(Rocky SPH\noil-fill flow)": dict(t=18313.0, note="288k particles, 8s physical time, GPU"),
}
labels=list(data.keys()); times=[data[k]["t"] for k in labels]
INK="#333333"
fig,ax=plt.subplots(figsize=(9,6))
colors=["#1baf7a","#eb6834","#3987e5"]
bars=ax.bar(labels, times, color=colors)
ax.set_yscale("log")
ax.set_ylabel("Wall-clock solve time, s (log scale)", color=INK)
ax.set_title("Solve time comparison: MAPDL vs Icepak vs FreeFlow\n(다른 물리/스코프 - 참고용)", color=INK, fontsize=12)
for b,t in zip(bars,times):
    lbl = f"{t:.1f}s" if t<3600 else f"{t/3600:.2f}h ({t:.0f}s)"
    ax.annotate(lbl, xy=(b.get_x()+b.get_width()/2, t), xytext=(0,6),
                textcoords="offset points", ha="center", fontsize=10, color=INK, fontweight="bold")
ax.grid(True, axis="y", which="both", color="#e5e5e0", lw=0.7)
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout()
os.makedirs(OUT, exist_ok=True)
fig.savefig(os.path.join(OUT,"timing_comparison.png"), dpi=150)
json.dump(data, open(r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\timing_comparison.json","w"), indent=2, ensure_ascii=False)
print("saved timing_comparison.png + json")
