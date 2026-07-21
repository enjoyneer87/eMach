import h5py, json
import numpy as np
CAS=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.cas.h5"
DAT=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.dat.h5"
OUT=r"D:\KDH\simVary\Ansys_Thermal\fluent_prius_zone_temps.json"
ZNAME={979:"stator",982:"airgap",991:"shaft",1000:"rotor",1003:"frame",
       1018:"magnet",1024:"insulation",1030:"coil",1033:"fluid_jacket",1039:"cover"}
c=h5py.File(CAS,"r"); zt=c["meshes/1/cells/zoneTopology"]
ids=zt["id"][()]; mn=zt["minId"][()]; mx=zt["maxId"][()]; c.close()
d=h5py.File(DAT,"r"); T=d["results/1/phase-1/cells/SV_T/1"][()]; d.close()
T=np.asarray(T,float)-273.15   # K->C
print(f"SV_T: {len(T)} cells, {T.min():.1f}~{T.max():.1f} C")
res={}
for i,m,x in zip(ids,mn,mx):
    seg=T[m-1:x]   # 1-based -> 0-based
    nm=ZNAME.get(int(i),f"zone{i}")
    res[nm]={"min":round(float(seg.min()),1),"mean":round(float(seg.mean()),1),
             "max":round(float(seg.max()),1),"cells":int(x-m+1)}
    print(f"  {nm:13s}: mean {res[nm]['mean']:6.1f}  max {res[nm]['max']:6.1f}  min {res[nm]['min']:6.1f}  ({res[nm]['cells']})")
json.dump(res, open(OUT,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
print("saved:", OUT)
