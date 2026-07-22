# -*- coding: utf-8 -*-
"""e10 오일스프레이 CHT 챔버 메시: 공기 캐비티(유체) + 엔드턴 링(고체, 구리손).
gmsh OCC 2볼륨 컨포멀 -> CGNS(존/BC 네이밍) + meshio CGNS/Nastran 폴백 export.
Fluent 직접 import 대상."""
import os, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
LOG = os.path.join(SP, "ff_spray_geom.txt")
_l = open(LOG, "w", encoding="utf-8")
def W(*a): _l.write(" ".join(str(x) for x in a) + "\n"); _l.flush()

# e10 스케일(mm->m). 엔드턴 링: bore측 반경~72, 바깥~88, 축방향 링 두께 50mm.
R_HOUS = 0.100          # 하우징 내부(공기 캐비티)
Z0, Z1 = 0.0, 0.12      # 캐비티 축범위
R_WIN_IN, R_WIN_OUT = 0.072, 0.088
ZW0, ZW1 = 0.02, 0.07   # 엔드턴 링 축범위
MSIZE = 0.005
try:
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    occ = gmsh.model.occ
    cyl = occ.addCylinder(0, 0, Z0, 0, 0, Z1 - Z0, R_HOUS)
    ro = occ.addCylinder(0, 0, ZW0, 0, 0, ZW1 - ZW0, R_WIN_OUT)
    ri = occ.addCylinder(0, 0, ZW0, 0, 0, ZW1 - ZW0, R_WIN_IN)
    ring, _ = occ.cut([(3, ro)], [(3, ri)], removeObject=True, removeTool=True)
    ring_tag = ring[0][1]
    # fluid = cyl - ring (ring 보존)
    fl, _ = occ.cut([(3, cyl)], [(3, ring_tag)], removeObject=True, removeTool=False)
    fluid_tag = fl[0][1]
    occ.fragment([(3, fluid_tag), (3, ring_tag)], [])
    occ.synchronize()

    vols = gmsh.model.getEntities(3)
    W("volumes:", vols)
    # 분류: 링(고체)= com이 ZW 중앙, r_com off-axis? 링은 환형이라 com 축상. bbox로.
    fluid_v, solid_v = [], []
    for (d, t) in vols:
        bb = gmsh.model.getBoundingBox(3, t)
        zc = 0.5 * (bb[2] + bb[5]); zext = bb[5] - bb[2]
        # 링은 z범위 좁고(0.05) 반경 큰영역 빔; fluid는 z 전체(0.12)
        if abs(zext - (Z1 - Z0)) < 1e-4:
            fluid_v.append(t)
        else:
            solid_v.append(t)
    W("fluid_v:", fluid_v, "solid_v:", solid_v)
    gmsh.model.addPhysicalGroup(3, fluid_v, name="fluid_air")
    gmsh.model.addPhysicalGroup(3, solid_v, name="solid_winding")

    # 경계면 분류: top(nozzle), bottom(drain), lateral(housing), 링표면(interface)
    surfs = gmsh.model.getEntities(2)
    nozzle, drain, housing, interface = [], [], [], []
    for (d, t) in surfs:
        bb = gmsh.model.getBoundingBox(2, t)  # xmin,ymin,zmin,xmax,ymax,zmax
        rmax = max(abs(bb[0]), abs(bb[3]), abs(bb[1]), abs(bb[4]))
        zmin, zmax = bb[2], bb[5]
        if abs(zmin - Z1) < 1e-4 and abs(zmax - Z1) < 1e-4:
            nozzle.append(t)          # 상단 디스크
        elif abs(zmin - Z0) < 1e-4 and abs(zmax - Z0) < 1e-4:
            drain.append(t)           # 하단 디스크
        elif rmax > R_HOUS - 1e-3:
            housing.append(t)         # 측면 외벽(bbox 반경 ~R_HOUS)
        else:
            interface.append(t)       # 링(엔드턴) 표면 = 스프레이 충돌/CHT 계면
    gmsh.model.addPhysicalGroup(2, nozzle, name="nozzle")
    gmsh.model.addPhysicalGroup(2, drain, name="drain")
    gmsh.model.addPhysicalGroup(2, housing, name="housing")
    gmsh.model.addPhysicalGroup(2, interface, name="winding_surf")
    W(f"faces nozzle={nozzle} drain={drain} housing(n={len(housing)}) interface(n={len(interface)})")

    gmsh.option.setNumber("Mesh.MeshSizeMin", MSIZE)
    gmsh.option.setNumber("Mesh.MeshSizeMax", MSIZE)
    gmsh.model.mesh.generate(3)
    ntag, _, _ = gmsh.model.mesh.getNodes()
    W("nodes:", len(ntag))

    CGNS = os.path.join(SP, "spray_e10.cgns")
    gmsh.write(CGNS)
    W("gmsh CGNS written:", os.path.getsize(CGNS) if os.path.exists(CGNS) else "FAIL")
    gmsh.write(os.path.join(SP, "spray_e10_gmsh.msh"))  # meshio 폴백용(2.2)
    gmsh.finalize()

    # meshio 폴백: CGNS / Nastran
    try:
        import meshio
        m = meshio.read(os.path.join(SP, "spray_e10_gmsh.msh"), file_format="gmsh")
        meshio.write(os.path.join(SP, "spray_e10_meshio.cgns"), m)
        W("meshio CGNS ok")
    except Exception as e:
        W("meshio CGNS fail:", repr(e)[:150])
    W("DONE-OK")
except Exception:
    W("EXC:", traceback.format_exc())
    try: gmsh.finalize()
    except Exception: pass
finally:
    _l.close()
os._exit(0)
