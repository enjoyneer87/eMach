# -*- coding: utf-8 -*-
"""FreeFlow(e10) 최종 메시: STL(Stator/Winding)+Rotor(cyl) -> 병합 -> 병합 후 퇴화필터
   -> 중간노드 직선화 -> SOLID87 CDB. (병합 전 필터는 병합유발 퇴화를 못잡는 버그였음)"""
import os, traceback, numpy as np
GEO=r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry"
OUT_CDB=r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh.cdb"
L=open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_mesh_final.txt","w")
def P(*a): L.write(" ".join(str(x) for x in a)+"\n"); L.flush()
MESH_MAX,MESH_MIN=0.005,0.0018
ROT=dict(r=0.0714, z0=-0.207, z1=-0.057)
MIDPAIRS=[(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)]
def mesh_part_from_stl(part):
    import gmsh
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
    gmsh.merge(os.path.join(GEO,part+".stl"))
    gmsh.model.mesh.classifySurfaces(40*np.pi/180,True,True,40*np.pi/180)
    gmsh.model.mesh.createGeometry()
    surfs=[s[1] for s in gmsh.model.getEntities(2)]
    sl=gmsh.model.geo.addSurfaceLoop(surfs); vol=gmsh.model.geo.addVolume([sl])
    gmsh.model.geo.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax",MESH_MAX); gmsh.option.setNumber("Mesh.MeshSizeMin",MESH_MIN)
    gmsh.option.setNumber("Mesh.ElementOrder",2); gmsh.option.setNumber("Mesh.Optimize",1)
    gmsh.model.mesh.generate(3)
    return _extract(gmsh,vol)
def mesh_cylinder():
    import gmsh
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
    gmsh.model.occ.addCylinder(0,0,ROT["z0"], 0,0,ROT["z1"]-ROT["z0"], ROT["r"])
    gmsh.model.occ.synchronize()
    vol=gmsh.model.getEntities(3)[0][1]
    gmsh.option.setNumber("Mesh.MeshSizeMax",MESH_MAX); gmsh.option.setNumber("Mesh.MeshSizeMin",MESH_MIN)
    gmsh.option.setNumber("Mesh.ElementOrder",2); gmsh.model.mesh.generate(3)
    return _extract(gmsh,vol)
def _extract(gmsh,vol):
    ntag,ncoord,_=gmsh.model.mesh.getNodes(); idx={int(t):i for i,t in enumerate(ntag)}
    XYZ=np.array(ncoord,float).reshape(-1,3)
    et,el,en=gmsh.model.mesh.getElements(3,vol); conns=[]
    for e,nn in zip(et,en):
        if e==11: conns.append(np.array(nn,np.int64).reshape(-1,10))
    C=np.vstack(conns); C0=np.vectorize(idx.get)(C)[:,[0,1,2,3,4,5,6,7,9,8]]
    gmsh.finalize()
    return XYZ,C0   # (병합 전 필터링 안 함 -> merge 후 일괄 필터)
def corner_vol(nodes, C0):
    p=nodes[C0[:,:4]]
    return np.einsum('ij,ij->i', np.cross(p[:,1]-p[:,0], p[:,2]-p[:,0]), p[:,3]-p[:,0])/6.0
try:
    alln=[]; allc=[]; allm=[]
    for part,mat,fn in [("Stator",1,mesh_part_from_stl),("Winding",3,mesh_part_from_stl),("Rotor",5,mesh_cylinder)]:
        if fn is mesh_part_from_stl: XYZ,C0=fn(part)
        else: XYZ,C0=fn()
        base=sum(len(n) for n in alln)
        alln.append(XYZ); allc.append(C0+base); allm.append(np.full(len(C0),mat))
        P(f"{part}(mat{mat}): nodes={len(XYZ)} tet10={len(C0)} (pre-merge, unfiltered)")
    nodes=np.vstack(alln); conn=np.vstack(allc); mats=np.concatenate(allm)
    # 병합
    key=np.round(nodes,6); _,ui,inv=np.unique(key,axis=0,return_index=True,return_inverse=True)
    nodes2=nodes[ui]; conn2=inv[conn]
    P(f"merged: nodes={len(nodes2)} tet10(raw)={len(conn2)}")
    # 병합 후 퇴화(코너 중복/근접) 필터 -- 여기가 핵심 수정
    dup = (conn2[:,0]==conn2[:,1])|(conn2[:,0]==conn2[:,2])|(conn2[:,0]==conn2[:,3]) \
        | (conn2[:,1]==conn2[:,2])|(conn2[:,1]==conn2[:,3])|(conn2[:,2]==conn2[:,3])
    v=corner_vol(nodes2, conn2)
    med=np.median(np.abs(v))
    good = (~dup) & (np.abs(v) > 1e-2*med)
    P(f"POST-MERGE filter: total={len(conn2)} dup_corner={int(dup.sum())} "
      f"small_vol={int((~good & ~dup).sum())} -> keep {int(good.sum())} drop {int((~good).sum())}")
    conn2=conn2[good]; mats2=mats[good]
    # 중간노드 직선화(자코비안 안전) - 최종 connectivity 기준
    for col,(a,b) in zip(range(4,10), MIDPAIRS):
        mids=conn2[:,col]
        nodes2[mids] = 0.5*(nodes2[conn2[:,a]] + nodes2[conn2[:,b]])
    P("midside nodes straightened")
    P(f"final: nodes={len(nodes2)} tet10={len(conn2)} mats={dict(zip(*[x.tolist() for x in np.unique(mats2,return_counts=True)]))}")
    with open(OUT_CDB,"w") as f:
        f.write("/PREP7\nET,1,87\n"); f.write(f"NBLOCK,6,SOLID,{len(nodes2)},{len(nodes2)}\n(3i9,6e21.13e3)\n")
        for i,(x,y,z) in enumerate(nodes2,1): f.write(f"{i:9d}{0:9d}{0:9d}{x:21.13E}{y:21.13E}{z:21.13E}\n")
        f.write("N,R5.3,LOC,-1,\n"); f.write(f"EBLOCK,19,SOLID,{len(conn2)},{len(conn2)}\n(19i10)\n")
        for eid,(nc,m) in enumerate(zip(conn2+1,mats2),1):
            l1=[int(m),1,1,0,0,0,0,0,10,0,eid]+[int(v) for v in nc[:8]]
            f.write("".join(f"{v:10d}" for v in l1)+"\n"); f.write("".join(f"{int(v):10d}" for v in nc[8:])+"\n")
        f.write("-1\n")
    P(f"CDB: {OUT_CDB} ({os.path.getsize(OUT_CDB)/1e6:.1f}MB)"); P("DONE-OK")
except Exception:
    P("EXC:",traceback.format_exc())
    try:
        import gmsh; gmsh.finalize()
    except Exception: pass
L.close(); os._exit(0)
