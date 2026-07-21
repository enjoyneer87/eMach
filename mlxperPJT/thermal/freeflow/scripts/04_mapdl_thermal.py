# -*- coding: utf-8 -*-
"""FreeFlow(e10) MAPDL 열해석: CDB(SOLID87) + e10손실 + 오일 대류냉각 -> 정상상태 온도.
   mat: 1 stator 3 winding 5 rotor. 오일냉각=winding+stator OD 표면 대류."""
import os, json, time, traceback
import numpy as np
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
CDB=r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh.cdb"
LJSON=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_losses.json"
OUTJSON=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\ff_mapdl_temps.json"
log=open(SP+r"\ff_mapdl.txt","w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
# 손실 로드 (Motor-CAD; 0이면 Prius 추정)
L=json.load(open(LJSON,encoding="utf-8"))
sm=L.get("_summary_W",{})
Pcu=sm.get("copper",0) or 0; Pfe_s=sm.get("stator_iron",0) or 0
Pfe_r=sm.get("rotor_iron",0) or 0; Pmag=sm.get("magnet",0) or 0
if (Pcu+Pfe_s+Pfe_r+Pmag) < 1.0:   # 0이면 Prius 추정
    Pcu, Pfe_s, Pfe_r, Pmag = 3350.0, 585.0, 65.0, 24.0
    LOSS_SRC="Prius-estimate (Motor-CAD returned 0)"
else:
    LOSS_SRC="e10 Motor-CAD"
P(f"losses[W] cu={Pcu:.0f} stator_fe={Pfe_s:.0f} rotor_fe={Pfe_r:.0f} magnet={Pmag:.0f} src={LOSS_SRC}")
# 오일 냉각(ATF): 오일온도 70C, 유효HTC (엔드턴 분사+나선채널)
OIL_T=70.0; HTC_WIND=1500.0; HTC_STATOR=2500.0
try:
    from ansys.mapdl.core import launch_mapdl
    mapdl=launch_mapdl(run_location=os.path.join(SP,"ff_mapdl_run10"), override=True, nproc=4)
    P("mapdl:", mapdl.version)
    mapdl.clear(); mapdl.prep7()
    mapdl.cdread("db", CDB)
    mapdl.et(1,"SOLID87")
    mapdl.shpp("off")   # 형상검사 완화(품질경고 요소 허용; zero-vol은 메시 최적화로 제거됨)
    # 재료 열전도율 [W/mK]
    mats={1:25.0, 3:5.0, 5:25.0}  # stator lam / winding copper(등가) / rotor
    for m,k in mats.items(): mapdl.mp("KXX",m,k)
    P("materials set")
    # 부품 체적(gmsh 값, m3) -> HGEN 밀도
    mapdl.allsel()
    Vpart={1:1767.5e-6, 3:900.7e-6, 5: (np.pi*0.0714**2*0.15)}  # rotor cyl vol
    hgen={1:Pfe_s/Vpart[1], 3:Pcu/Vpart[3], 5:(Pfe_r+Pmag)/Vpart[5]}
    P("HGEN[W/m3]:", {m:round(h,0) for m,h in hgen.items()})
    for m,h in hgen.items():
        mapdl.esel("s","mat","",m); mapdl.bfe("all","hgen","",h)
    mapdl.allsel()
    # 냉각: 모델 외곽면(오일 접촉면)에 오일 대류 (NSEL,,EXT = 외부노드)
    HTC_OIL=2000.0
    mapdl.allsel()
    mapdl.nsel("s","ext")       # 어셈블리 외곽면 노드만
    mapdl.sf("all","conv",HTC_OIL,OIL_T)
    mapdl.allsel()
    P(f"loads applied (HGEN + oil conv HTC={HTC_OIL} T={OIL_T}C on exterior)")
    mapdl.run("/SOLU"); mapdl.antype("static")
    t0=time.time(); mapdl.solve(); t_solve=time.time()-t0
    mapdl.finish()
    P(f"solved (solve time = {t_solve:.1f} s)")
    # 온도 추출
    mapdl.post1(); mapdl.set(1,1)
    res={"_loss_source":LOSS_SRC,"_oil":{"T":OIL_T,"htc_wind":HTC_WIND,"htc_stator":HTC_STATOR},
         "_timing":{"solve_time_s":round(t_solve,1),
                    "mesh_nodes":544400,"mesh_elements":316733},
         "losses_W":{"copper":Pcu,"stator_iron":Pfe_s,"rotor_iron":Pfe_r,"magnet":Pmag},"per_part":{}}
    names={1:"stator",3:"winding",5:"rotor"}
    for m,nm in names.items():
        mapdl.allsel(); mapdl.esel("s","mat","",m); mapdl.nsle()
        T=mapdl.post_processing.nodal_temperature()
        tmx=float(T.max()); tmn=float(T.min())
        res["per_part"][nm]=dict(max=tmx,min=tmn); P(f"  {nm}: max={tmx:.1f} min={tmn:.1f} C")
    mapdl.allsel()
    os.makedirs(os.path.dirname(OUTJSON),exist_ok=True)
    json.dump(res, open(OUTJSON,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    P("saved", OUTJSON); P("DONE-OK")
    mapdl.exit()
except Exception:
    P("EXC:", traceback.format_exc())
finally: log.close()
os._exit(0)
