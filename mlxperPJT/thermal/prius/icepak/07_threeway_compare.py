# -*- coding: utf-8 -*-
"""3-way 비교(Fluent CFD / MAPDL 하이브리드 / Icepak) 250A 고부하 - Icepak 수치는 런타임 로드."""
import os, json
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\viz\comparison"
os.makedirs(OUT,exist_ok=True)
IPK=json.load(open(r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\prius\data\icepak_prius_250A_temps.json",encoding="utf-8"))
pr=IPK["per_role"]
def g(role): 
    v=pr.get(role,{}).get("max"); return round(v,1) if v else None
parts=["coil","stator","rotor","magnet"]
icepak=[g("coil"),g("stator"),g("rotor"),g("magnet")]
fluent=[118.2,99.9,89.7,89.4]
mapdl =[119.2,116.3,110.2,109.0]
INK="#333"; x=np.arange(len(parts)); w=0.26
fig,ax=plt.subplots(figsize=(10,6))
ax.bar(x-w,fluent,w,color="#3987e5",label="Fluent CFD (CHT)")
ax.bar(x  ,mapdl ,w,color="#eb6834",label="MAPDL hybrid (water-jacket)")
ax.bar(x+w,icepak,w,color="#1baf7a",label="Icepak (conduction+jacket)")
for xi,(a,b,c) in enumerate(zip(fluent,mapdl,icepak)):
    for dx,val in ((-w,a),(0,b),(w,c)):
        if val is not None: ax.annotate(f"{val:.0f}",xy=(xi+dx,val),ha="center",va="bottom",fontsize=8,color=INK)
ax.set_xticks(x); ax.set_xticklabels([p.capitalize() for p in parts])
ax.set_ylabel("Max temperature, degC",color=INK)
ax.set_title("Prius 250A high-load: 3-way thermal comparison (max temp per component)",color=INK,fontsize=12)
ax.grid(True,axis="y",color="#e5e5e0"); 
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False,fontsize=10,labelcolor=INK)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"threeway_250A.png"),dpi=150); plt.close(fig)
print("saved threeway_250A.png  icepak=",icepak)
