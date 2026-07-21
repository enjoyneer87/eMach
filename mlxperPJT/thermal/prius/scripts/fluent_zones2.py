import h5py, re
import numpy as np
CAS=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.cas.h5"
c=h5py.File(CAS,"r")
s=c["settings/Thread Variables"][()][0].decode("latin-1","ignore")
cell_ids=[979,982,991,1000,1003,1018,1024,1030,1033,1039]
# 각 id 주변 컨텍스트에서 이름 추출: 보통 (id (type name ...)) 또는 name 근처
print("=== cell zone id -> name (정밀) ===")
for cid in cell_ids:
    # id 뒤 200자 안에서 첫 단어형 이름
    m=re.search(re.escape(str(cid))+r'\b(.{0,120})', s)
    ctx=m.group(1) if m else ""
    nm=re.findall(r'(stator[a-z_0-9]*|rotor[a-z_0-9]*|magnet[a-z_0-9]*|shaft[a-z_0-9]*|coil[a-z_0-9]*|winding[a-z_0-9]*|air[a-z_0-9]*|housing[a-z_0-9]*)', ctx, re.I)
    print(f"  {cid}: {nm[:2]}  ctx='{ctx[:60].strip()}'")
# faces 구조
print("\n=== faces structure ===")
fg=c["meshes/1/faces"]
for k in fg.keys():
    it=fg[k]
    if isinstance(it,h5py.Group):
        print(k+"/", {kk:(fg[k][kk].shape if hasattr(fg[k][kk],'shape') else '') for kk in list(it.keys())[:6]})
    else: print(k, getattr(it,'shape',''))
print("nodes/coords/1037 shape:", c["meshes/1/nodes/coords/1037"].shape)
c.close()
