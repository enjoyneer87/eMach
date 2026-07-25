# -*- coding: utf-8 -*-
"""e10 오일냉각 모터 — MAPDL(FEM) vs Icepak(FVM) 열해석 3-way 비교.
같은 모델·조건(동일 손실 4024W·동일 오일회로 계수)·같은 시간스케일(transient@900s, max)에서
FEM 솔리드+열등가회로(MAPDL) 와 FVM 솔리드+대류벽 오일회로(Icepak) 를 비교.
- V1 = homog winding k5 (MAPDL 미러, 스테이터 컨포멀)
- V2 = discrete 구리바 k387 (실제 하이핀 형상, 컨포멀)
둘 다 냉각 = MAPDL 오일노드온도(JACKET84.4/SPRAY91.9/GAP_S122.3/GAP_R87/SHF70.3) ref 대류벽.
데이터는 런타임 로드 → V2 완료 후 재실행만.
"""
import os, json
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
try:
    plt.rcParams["font.family"]="Malgun Gothic"; plt.rcParams["axes.unicode_minus"]=False
except Exception: pass
D=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data"
OUT=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\viz\comparison"
os.makedirs(OUT,exist_ok=True)
def jload(f):
    try: return json.load(open(os.path.join(D,f),encoding="utf-8"))
    except Exception: return {}
parts=["winding","stator","rotor","magnet","shaft"]
# MAPDL per_part max
M=jload("ff_mapdl_hybrid_temps.json").get("per_part",{})
mapdl=[round(M.get(p,{}).get("max"),1) if M.get(p,{}).get("max") is not None else None for p in parts]
# Icepak V1 (homog) at_900s max
V1=jload("e10_icepak_v1_homog.json").get("at_900s",{})
def gv1(p):
    d=V1.get("coil" if p=="winding" else p) or V1.get(p,{})
    v=d.get("max") if isinstance(d,dict) else None
    return round(v,1) if v is not None else None
v1=[gv1(p) for p in parts]
# Icepak V2 (discrete) at_900s max — coil==winding
V2=jload("e10_icepak_v2_bars.json").get("at_900s",{})
def gv2(p):
    key="coil" if p=="winding" else p
    d=V2.get(key,{})
    v=d.get("max") if isinstance(d,dict) else None
    return round(v,1) if v is not None else None
v2=[gv2(p) for p in parts]
has_v2=any(x is not None for x in v2) and (v2[0] is None or v2[0]<800)

INK="#2a2a2a"; x=np.arange(len(parts))
fig,ax=plt.subplots(figsize=(11,6.2))
if has_v2:
    w=0.26
    ax.bar(x-w,mapdl,w,color="#eb6834",label="MAPDL (FEM solid + 열등가회로)")
    ax.bar(x   ,v1  ,w,color="#1baf7a",label="Icepak V1 (FVM, homog k5, 대류벽 오일회로)")
    ax.bar(x+w,v2   ,w,color="#3987e5",label="Icepak V2 (FVM, discrete 구리바 k387)")
    series=[(-w,mapdl),(0,v1),(w,v2)]
else:
    w=0.36
    ax.bar(x-w/2,mapdl,w,color="#eb6834",label="MAPDL (FEM solid + 열등가회로)")
    ax.bar(x+w/2,v1   ,w,color="#1baf7a",label="Icepak V1 (FVM, homog k5, 대류벽 오일회로)")
    series=[(-w/2,mapdl),(w/2,v1)]
for dx,vals in series:
    for xi,val in enumerate(vals):
        if val is not None: ax.annotate(f"{val:.0f}",xy=(xi+dx,val),ha="center",va="bottom",fontsize=8.5,color=INK)
ax.set_xticks(x); ax.set_xticklabels([p.capitalize() for p in parts],fontsize=11)
ax.set_ylabel("최대 온도 [°C]",color=INK,fontsize=11)
ax.set_title("e10 오일냉각 모터 — MAPDL vs Icepak 열해석 (transient @900s, 부품별 최대온도)",
             color=INK,fontsize=13,pad=12)
ax.grid(True,axis="y",color="#e8e8e3",zorder=0)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False,fontsize=9.5,labelcolor=INK,loc="upper right")
note=("동일 손실 4024W · 동일 오일냉각 계수(JACKET84/SPRAY92/GAP122·87/SHF70) · IC70°C→900s.  "
      "V1(균질 k5, 밴드-스테이터 네이티브 카브 → 스테이터 컨포멀): 권선 %s°C ~ MAPDL 152 (Δ%s°C).  "
      "V2(discrete 구리바 k387, Maxwell import): 폭주 2376°C·비물리 → imported 바디는 함침 carve로도 비컨포멀.\n"
      "결론: Icepak 슬롯측 유효화는 '네이티브 균질화'로만 가능(MAPDL 병합 컨포멀메시를 재현하는 셈).  "
      "로터/자석이 MAPDL보다 높은 것도 magnet↔rotor imported 계면 비컨포멀 때문(V1은 권선만 컨포멀화)."
      %(v1[0] if v1[0] else "-", (round(v1[0]-152.2,1) if v1[0] else "-")))
fig.text(0.012,-0.02,note,fontsize=8.4,color="#555",ha="left",va="top",wrap=True)
fig.tight_layout(rect=[0,0.04,1,1])
p1=os.path.join(OUT,"e10_mapdl_icepak_3way.png")
fig.savefig(p1,dpi=150,bbox_inches="tight"); plt.close(fig)
print("saved",p1)
print("mapdl",mapdl); print("v1",v1); print("v2",v2,"has_v2",has_v2)
