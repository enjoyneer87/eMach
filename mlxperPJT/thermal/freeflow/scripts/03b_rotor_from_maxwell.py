# -*- coding: utf-8 -*-
"""e10 로터 재구축: Maxwell 2D 45°섹터(샤프트+로터적층+더블V자석) -> gmsh OCC 3D
-> tet10 -> 기존 스테이터+권선 STL 메시(mat1/3)와 병합 -> SOLID87 CDB.
재료: 1 stator, 2 magnet, 3 winding, 4 shaft, 5 rotor."""
import os, json, math, traceback
import numpy as np
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
GEOM = os.path.join(SP, "e10_geom.json")
OLD_CDB = r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh.cdb"     # 기존(mat1/3/5cyl)
OUT_CDB = r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2.cdb"  # 병합(mat1..5)
LOG = os.path.join(SP, "ff_rotor_build.txt")
_l = open(LOG, "w", encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a) + "\n"); _l.flush()

MM = 1e-3
Z0, Z1 = -0.2075, -0.0575          # 스택 축범위(스테이터와 정렬)
R_SHAFT = 23.455 * MM
R_ROTOR = 70.270 * MM
MSIZE = 3.0 * MM

try:
    d = json.load(open(GEOM, encoding="utf-8"))["objects"]
    mag_names = [k for k in d if "Magnet" in k]
    mag_polys = []
    for nm in mag_names:
        vs = [(v[0] * MM, v[1] * MM) for v in d[nm]["verts"]]
        mag_polys.append(vs)
    P(f"magnets in sector: {len(mag_polys)} ({mag_names})")

    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    occ = gmsh.model.occ
    L = Z1 - Z0
    shaft = occ.addCylinder(0, 0, Z0, 0, 0, L, R_SHAFT)
    rout = occ.addCylinder(0, 0, Z0, 0, 0, L, R_ROTOR)

    # 자석 프리즘(섹터 4개) + ×8 회전 = 32개
    def make_prism(poly):
        pts = [occ.addPoint(x, y, Z0) for (x, y) in poly]
        n = len(pts)
        lns = [occ.addLine(pts[i], pts[(i + 1) % n]) for i in range(n)]
        wire = occ.addCurveLoop(lns)
        surf = occ.addPlaneSurface([wire])
        ext = occ.extrude([(2, surf)], 0, 0, L)
        vol = [t for (dim, t) in ext if dim == 3][0]
        return vol
    base_mags = [make_prism(p) for p in mag_polys]
    all_mags = list(base_mags)
    for k in range(1, 8):
        cp = occ.copy([(3, m) for m in base_mags])
        occ.rotate(cp, 0, 0, 0, 0, 0, 1, k * math.pi / 4)
        all_mags += [t for (dim, t) in cp]
    P(f"total magnet prisms: {len(all_mags)}")

    # 로터적층 = rout - shaft - magnets (구멍) ; shaft/magnets 보존
    occ.synchronize()
    tool = [(3, shaft)] + [(3, m) for m in all_mags]
    cutres, _ = occ.cut([(3, rout)], tool, removeObject=True, removeTool=False)
    rotor_vols = [t for (dim, t) in cutres if dim == 3]
    P(f"rotor lamination volumes after cut: {len(rotor_vols)}")
    # 컨포멀 인터페이스: 전체 fragment
    allv = [(3, shaft)] + [(3, m) for m in all_mags] + [(3, v) for v in rotor_vols]
    occ.fragment(allv, [])
    occ.synchronize()

    # 자석 중심(32개) 계산 -> 분류용
    mag_cen = []
    for poly in mag_polys:
        cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
        mag_cen.append((cx, cy))
    mag_cen_all = []
    for k in range(8):
        a = k * math.pi / 4
        for (cx, cy) in mag_cen:
            mag_cen_all.append((cx * math.cos(a) - cy * math.sin(a),
                                cx * math.sin(a) + cy * math.cos(a)))

    # 볼륨 분류: com 반경/자석중심 근접
    vols = gmsh.model.getEntities(3)
    grp = {2: [], 4: [], 5: []}
    for (dim, tag) in vols:
        com = occ.getCenterOfMass(3, tag)
        rcom = math.hypot(com[0], com[1])
        bb = gmsh.model.getBoundingBox(3, tag)   # xmin,ymin,zmin,xmax,ymax,zmax
        # 실린더 bbox는 정사각형 -> 대각선 아닌 좌표 최대절대값(=R)으로 판정
        rmax = max(abs(bb[0]), abs(bb[3]), abs(bb[1]), abs(bb[4]))
        # 자석중심 최근접
        dmin = min(math.hypot(com[0] - mx, com[1] - my) for (mx, my) in mag_cen_all)
        if rmax < R_SHAFT + 1.0 * MM:
            grp[4].append(tag)          # shaft (작은 bbox)
        elif rcom > 10 * MM and dmin < 3.0 * MM:
            grp[2].append(tag)          # magnet (축밖 com, 자석중심 근접)
        else:
            grp[5].append(tag)          # rotor lam (환형: com 축, 큰 bbox)
    P(f"classify: shaft={len(grp[4])} magnet={len(grp[2])} rotor={len(grp[5])}")
    for mat, tags in grp.items():
        if tags: gmsh.model.addPhysicalGroup(3, tags, mat)

    gmsh.option.setNumber("Mesh.MeshSizeMin", MSIZE)
    gmsh.option.setNumber("Mesh.MeshSizeMax", MSIZE)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)   # tet10
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.model.mesh.generate(3)
    P("gmsh mesh done")

    # 노드/요소 추출
    ntags, ncoords, _ = gmsh.model.mesh.getNodes()
    ncoords = ncoords.reshape(-1, 3)
    nid_map = {int(t): i for i, t in enumerate(ntags)}
    nodes = ncoords.copy()
    # tet10: gmsh type 11
    conn = []; mats = []
    for mat in (2, 4, 5):
        egroups = gmsh.model.getEntitiesForPhysicalGroup(3, mat) if grp[mat] else []
        for ent in egroups:
            etypes, etags, enodes = gmsh.model.mesh.getElements(3, ent)
            for et, ets, ens in zip(etypes, etags, enodes):
                if et != 11:  # tet10
                    continue
                ens = ens.reshape(-1, 10)
                for row in ens:
                    conn.append([nid_map[int(x)] for x in row])
                    mats.append(mat)
    conn = np.array(conn, dtype=int); mats = np.array(mats, dtype=int)
    P(f"rotor mesh: {len(nodes)} nodes, {len(conn)} tet10  "
      f"(mat2={np.sum(mats==2)} mat4={np.sum(mats==4)} mat5={np.sum(mats==5)})")
    gmsh.finalize()

    # gmsh tet10 -> ANSYS 노드순서 [0,1,2,3,4,5,6,7,9,8]
    REORD = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
    conn = conn[:, REORD]

    # ── 기존 CDB에서 스테이터(1)+권선(3) 노드/요소 읽기 ──
    from ansys.mapdl.reader import Archive
    arch = Archive(OLD_CDB)
    old_nodes = arch.nodes                     # (N,3) m
    old_nnum = arch.nnum                        # 노드번호
    grid = arch.grid
    old_mats = np.asarray(grid.cell_data["ansys_material_type"])
    # tet10 연결(그리드 셀 -> 노드번호). Archive.elem 사용
    # ansys-reader: arch.elem 각 행 [.., node ids...]; 대신 grid 사용
    cells = grid.cells_dict  # {celltype: (M,10)}
    import pyvista as pv
    # VTK_QUADRATIC_TETRA = 24
    quad = cells.get(24)
    P(f"old grid tet10 cells: {None if quad is None else len(quad)}")
    # grid.points 인덱스 -> old node number
    # 유지: mat 1,3만
    keep = np.isin(old_mats, [1, 3])
    quad_keep = quad[keep]; mats_keep = old_mats[keep]
    P(f"keep stator+winding elems: {len(quad_keep)} (mat1={np.sum(mats_keep==1)} mat3={np.sum(mats_keep==3)})")
    # 사용되는 point 인덱스만 추림
    used = np.unique(quad_keep)
    old_pts = grid.points[used]
    old_remap = {int(p): i for i, p in enumerate(used)}
    quad_keep2 = np.vectorize(lambda x: old_remap[int(x)])(quad_keep)

    # ── 병합: 노드 concat (오프셋), 요소 concat ──
    n_old = len(old_pts)
    all_nodes = np.vstack([old_pts, nodes])
    rotor_conn = conn + n_old
    all_conn = np.vstack([quad_keep2, rotor_conn])
    all_mats = np.concatenate([mats_keep, mats])
    P(f"MERGED: {len(all_nodes)} nodes, {len(all_conn)} tet10  "
      f"mats {[int(m) for m in np.unique(all_mats)]}")

    # ── CDB(NBLOCK/EBLOCK) 작성 (SOLID87) ──
    def write_cdb(path, nodes, conn, mats):
        # 03_stl_to_cdb.py 와 동일한 SOLID87 EBLOCK 포맷(tet10: 8노드+2노드 줄바꿈)
        with open(path, "w") as f:
            f.write("/PREP7\nET,1,87\n")
            f.write(f"NBLOCK,6,SOLID,{len(nodes)},{len(nodes)}\n(3i9,6e21.13e3)\n")
            for i, (x, y, z) in enumerate(nodes, 1):
                f.write(f"{i:9d}{0:9d}{0:9d}{x:21.13e}{y:21.13e}{z:21.13e}\n")
            f.write("N,R5.3,LOC,-1,\n")
            f.write(f"EBLOCK,19,SOLID,{len(conn)},{len(conn)}\n(19i10)\n")
            for i, (row, m) in enumerate(zip(conn, mats), 1):
                nn = [int(x) + 1 for x in row]   # 1-based
                l1 = [int(m), 1, 1, 0, 0, 0, 0, 0, 10, 0, i] + nn[:8]
                f.write("".join(f"{v:10d}" for v in l1) + "\n")
                f.write("".join(f"{v:10d}" for v in nn[8:]) + "\n")
            f.write("-1\n/EOF\n")
    write_cdb(OUT_CDB, all_nodes, all_conn, all_mats)
    P(f"saved {OUT_CDB}")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
    try: gmsh.finalize()
    except Exception: pass
finally:
    _l.close(); os._exit(0)
