import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT=os.path.join(SP:=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad","viz_prius")
os.makedirs(OUT,exist_ok=True)
fz=json.load(open(r"D:\KDH\simVary\Ansys_Thermal\fluent_prius_zone_temps.json",encoding="utf-8"))
INK,GRIDC="#333333","#e5e5e0"
# ── 1) Fluent 존별 온도 바 (min-mean-max) ─────────────────────────
order=["coil","insulation","airgap","rotor","magnet","stator","shaft","cover","frame","fluid_jacket"]
COLS={"coil":"#2a78d6","insulation":"#7bbf6a","airgap":"#c3c2b7","rotor":"#1baf7a",
      "magnet":"#e34948","stator":"#eda100","shaft":"#e87ba4","cover":"#9085e9",
      "frame":"#8a8878","fluid_jacket":"#3987e5"}
fig,ax=plt.subplots(figsize=(11,5.5))
xs=np.arange(len(order))
for i,z in enumerate(order):
    d=fz[z]
    ax.plot([i,i],[d["min"],d["max"]],color=COLS[z],lw=6,alpha=0.35,solid_capstyle="round")
    ax.plot(i,d["mean"],"o",color=COLS[z],ms=9)
    ax.annotate(f"{d['max']:.0f}",(i,d["max"]),xytext=(0,4),textcoords="offset points",ha="center",fontsize=8,color=INK)
ax.set_xticks(xs); ax.set_xticklabels(order,rotation=35,ha="right",fontsize=9)
ax.set_ylabel("Temperature, degC",color=INK)
ax.set_title("Fluent CFD (PriusMotor_3D45degree) - zone temperatures  [bar=min~max, dot=mean]",fontsize=12,color=INK)
ax.grid(True,axis="y",color=GRIDC,lw=0.8)
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fluent_zone_temps.png"),dpi=150); plt.close(fig)
print("saved fluent_zone_temps.png")
# ── 2) Fluent vs MAPDL 비교 (동일 부품, 운전점 다름 명시) ──────────
mapdl={"coil":185.6,"stator":181.8,"rotor":166.0,"magnet":161.6,"shaft":133.0}  # max
comp=["coil","stator","rotor","magnet","shaft"]
fmax=[fz[c]["max"] for c in comp]; mmax=[mapdl[c] for c in comp]
x=np.arange(len(comp)); w=0.38
fig,ax=plt.subplots(figsize=(9.5,5.5))
b1=ax.bar(x-w/2,fmax,w,color="#3987e5",label="Fluent CFD (water-jacket, own op-point)")
b2=ax.bar(x+w/2,mmax,w,color="#eb6834",label="MAPDL hybrid (JAC279 cooling, 250A high-load)")
for b,v in list(zip(b1,fmax))+list(zip(b2,mmax)):
    ax.annotate(f"{v:.0f}",(b.get_x()+b.get_width()/2,v),xytext=(0,3),textcoords="offset points",ha="center",fontsize=8,color=INK)
ax.set_xticks(x); ax.set_xticklabels([c.capitalize() for c in comp])
ax.set_ylabel("Max temperature, degC",color=INK)
ax.set_title("Prius 부품 최고온: Fluent CFD vs MAPDL hybrid\n(주의: 손실·냉각 조건이 달라 절대값 직접비교 불가 — 경향/방법 대조용)",fontsize=11,color=INK)
ax.grid(True,axis="y",color=GRIDC,lw=0.8); ax.legend(frameon=False,fontsize=9)
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fluent_vs_mapdl.png"),dpi=150); plt.close(fig)
print("saved fluent_vs_mapdl.png")
