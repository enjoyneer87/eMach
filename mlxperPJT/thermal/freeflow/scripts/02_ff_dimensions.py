import os, traceback, numpy as np
GEO=r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry"
L=open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_dims_out.txt","w",encoding="utf-8")
def P(*a): L.write(" ".join(str(x) for x in a)+"\n"); L.flush()
try:
    import pyvista as pv
    def rd(n): return pv.read(os.path.join(GEO,n+".stl"))
    S,R,W,H=rd("Stator"),rd("Rotating"),rd("Winding"),rd("Housing")
    def rad(m): p=m.points; return np.sqrt(p[:,0]**2+p[:,1]**2)*1000
    P("=== z range [mm] ===")
    for nm,m in [("Stator",S),("Rotating",R),("Winding",W),("Housing",H)]:
        b=m.bounds; P(f"  {nm:9s} z=[{b[4]*1000:.1f},{b[5]*1000:.1f}] len={(b[5]-b[4])*1000:.1f}")
    zc=-0.13
    for nm,m in [("Stator",S),("Rotating",R)]:
        sl=m.slice(normal="z",origin=(0,0,zc)); r=np.sqrt(sl.points[:,0]**2+sl.points[:,1]**2)*1000
        vals=np.sort(np.unique(np.round(r,1)))
        P(f"{nm} @z={zc*1000:.0f}: unique radii[mm]={list(vals)}")
    # 로터 극수: 각도 히스토그램 FFT
    sl=R.slice(normal="z",origin=(0,0,zc)); p=sl.points
    r=np.sqrt(p[:,0]**2+p[:,1]**2)*1000; th=np.degrees(np.arctan2(p[:,1],p[:,0]))%360
    mask=(r>52)&(r<70); hist,_=np.histogram(th[mask],bins=360,range=(0,360))
    F=np.abs(np.fft.rfft(hist-hist.mean()))
    top=sorted(range(1,25), key=lambda k:-F[k])[:8]
    P(f"로터 극수 FFT 상위주기(각360 내 반복수): {top}")
    rS=rad(S); rR=rad(R)
    P("=== 요약 ===")
    P(f"  Stator OD={rS.max():.1f} bore={np.percentile(rS,1):.1f} stack={(S.bounds[5]-S.bounds[4])*1000:.0f}mm")
    P(f"  Rotor OD={rR.max():.1f} shaft={np.percentile(rR,1):.1f}")
    P(f"  airgap~{np.percentile(rS,1)-rR.max():.2f}mm  Winding z=[{W.bounds[4]*1000:.0f},{W.bounds[5]*1000:.0f}]")
    P("DONE-OK")
except Exception:
    P(traceback.format_exc())
L.close()
os._exit(0)
