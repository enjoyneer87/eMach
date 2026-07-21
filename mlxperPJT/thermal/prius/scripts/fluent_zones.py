import h5py, re
import numpy as np
CAS=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.cas.h5"
DAT=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.dat.h5"
c=h5py.File(CAS,"r")
zt=c["meshes/1/cells/zoneTopology"]
ids=zt["id"][()]; mn=zt["minId"][()]; mx=zt["maxId"][()]
print("cell zones (id, cellrange):")
for i,m,x in zip(ids,mn,mx): print(f"  id={i}: cells {m}..{x} ({x-m+1})")
# 존 이름: Thread Variables 문자열에서 (name id ...) 파싱
for key in ("Thread Variables","TGrid Variables","Rampant Variables"):
    try:
        s=c["settings/"+key][()][0].decode("latin-1","ignore")
    except Exception: continue
    # zone id -> name: 패턴 (id (name . "type")) 또는 (name id
    found=re.findall(r'\b(\d{3,5})\b[^\n]{0,40}?(stator|rotor|magnet|coil|shaft|air|winding|end|middle|housing|yoke)[a-z_0-9]*', s, re.I)
    if found:
        print(f"\n[{key}] id->name hints:")
        for fid,nm in found[:40]: print(f"  {fid}: ...{nm}...")
        break
# 좌표 노드존
ncoord=c["meshes/1/nodes/coords"]
print("\nnode coord zones:", list(ncoord.keys()))
for k in list(ncoord.keys())[:5]:
    print("  ",k, ncoord[k].shape)
c.close()
# SV_T
d=h5py.File(DAT,"r")
T=d["results/1/phase-1/cells/SV_T/1"][()]
print("\nSV_T shape:", T.shape, "range(K):", float(T.min()), float(T.max()), "=> C:", float(T.min()-273.15), float(T.max()-273.15))
d.close()
