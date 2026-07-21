import os, json
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\viz_prius_wj"
os.makedirs(OUT,exist_ok=True)
comp=["Coil","Stator","Rotor","Magnet"]
# max 온도 [C]
data={
 "Fluent low (orig)":     [88.3,76.2,70.2,70.0],
 "MAPDL WJ low":          [88.3,86.5,83.7,83.5],
 "Fluent 250A":           [118.2,99.9,89.7,89.4],
 "MAPDL WJ 250A":         [119.2,116.3,110.2,109.0],
 "MAPDL JAC279 250A":     [185.6,181.8,166.0,161.6],
}
COLS={"Fluent low (orig)":"#3987e5","MAPDL WJ low":"#8ec6ff",
      "Fluent 250A":"#c0392b","MAPDL WJ 250A":"#eb6834","MAPDL JAC279 250A":"#8a8878"}
x=np.arange(len(comp)); n=len(data); w=0.16
INK,GRIDC="#333333","#e5e5e0"
fig,ax=plt.subplots(figsize=(12,6.5))
for i,(k,v) in enumerate(data.items()):
    b=ax.bar(x+(i-(n-1)/2)*w, v, w, color=COLS[k], label=k)
    for bar,val in zip(b,v):
        ax.annotate(f"{val:.0f}",(bar.get_x()+bar.get_width()/2,val),xytext=(0,2),textcoords="offset points",ha="center",fontsize=7,color=INK)
ax.axhline(180,color="#c0392b",lw=1,ls=":",alpha=0.6); ax.text(3.3,182,"H-class 180C",fontsize=8,color="#c0392b")
ax.set_xticks(x); ax.set_xticklabels(comp,fontsize=11)
ax.set_ylabel("Max temperature, degC",color=INK)
ax.set_title("Prius cross-validation matrix: MAPDL hybrid vs Fluent CFD (max temp)\n"
             "Coil matches within 1C at both loads when conditions matched; JAC279 (diff cooling) shown for reference",
             fontsize=11,color=INK)
ax.grid(True,axis="y",color=GRIDC,lw=0.8); ax.legend(frameon=False,fontsize=8.5,ncol=2)
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"validation_matrix.png"),dpi=150); plt.close(fig)
print("saved validation_matrix.png")
# 코일 초점 비교 (핵심)
fig,ax=plt.subplots(figsize=(7,5))
cases=["low\n(Fluent cond)","250A\n(high load)"]
mapdl_wj=[88.3,119.2]; fluent=[88.3,118.2]
x=np.arange(2); w=0.35
ax.bar(x-w/2,fluent,w,color="#3987e5",label="Fluent CFD")
ax.bar(x+w/2,mapdl_wj,w,color="#eb6834",label="MAPDL hybrid (water-jacket)")
for xi,(f,m) in enumerate(zip(fluent,mapdl_wj)):
    ax.annotate(f"{f:.1f}",(xi-w/2,f),xytext=(0,2),textcoords="offset points",ha="center",fontsize=9,color=INK)
    ax.annotate(f"{m:.1f}",(xi+w/2,m),xytext=(0,2),textcoords="offset points",ha="center",fontsize=9,color=INK)
ax.set_xticks(x); ax.set_xticklabels(cases); ax.set_ylabel("Coil max temperature, degC",color=INK)
ax.set_title("Coil max: MAPDL hybrid vs Fluent CFD (matched conditions)\nDelta = 0.0C (low), 1.0C (250A)",fontsize=11,color=INK)
ax.grid(True,axis="y",color=GRIDC,lw=0.8); ax.legend(frameon=False,fontsize=9)
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"coil_validation.png"),dpi=150); plt.close(fig)
print("saved coil_validation.png")
