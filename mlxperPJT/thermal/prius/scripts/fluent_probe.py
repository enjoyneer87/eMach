import h5py, os
CAS=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.cas.h5"
DAT=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.dat.h5"
def walk(g,pre="",lvl=0,maxlvl=3):
    if lvl>maxlvl: return
    for k in list(g.keys())[:25]:
        it=g[k]
        if isinstance(it,h5py.Group):
            print(pre+k+"/"); walk(it,pre+"  ",lvl+1,maxlvl)
        else:
            print(pre+k, getattr(it,'shape',''), getattr(it,'dtype',''))
for tag,f in [("CAS",CAS),("DAT",DAT)]:
    print(f"\n===== {tag} : exists={os.path.exists(f)} size={os.path.getsize(f)/1e6:.0f}MB =====")
    try:
        h=h5py.File(f,"r"); walk(h); h.close()
    except Exception as e:
        print("ERR:", str(e)[:200])
try:
    import ansys.fluent.core as pf
    print("\npyfluent:", pf.__version__)
except Exception as e:
    print("\npyfluent: NOT available", str(e)[:80])
