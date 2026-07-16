# -*- coding: utf-8 -*-
"""STEP(1/8 섹터, half-axial) -> gmsh 컨포멀 메시 -> x8 회전 + z미러 -> SOLID87 CDB."""
import os
import math
import traceback
import numpy as np

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
STEP_DIR = r"D:\KDH\simVary\Ansys_Thermal\step_export_icepakfea"
OUT_CDB = r"D:\KDH\simVary\Ansys_Thermal\real_motor_mesh.cdb"
log = open(os.path.join(SP, "gmsh_mesh.txt"), "w", encoding="utf-8")
def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

# 재료군 -> MAPDL mat 번호 (노트북 관례)
GROUPS = [("stator_lam", 1), ("magnets", 2), ("coils", 3),
          ("shaft", 4), ("rotor_lam", 5)]
MESH_MAX, MESH_MIN = 8.0, 2.5          # mm
N_SECTOR, SEC_ANG = 8, 45.0

try:
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    occ = gmsh.model.occ

    # ── 1) STEP 임포트 + 그룹 추적 ──────────────────────────────────────
    vol_group = {}                      # dimtag -> mat
    all_vols = []
    for name, mat in GROUPS:
        f = os.path.join(STEP_DIR, f"{name}.step")
        tags = occ.importShapes(f)
        vols = [t for t in tags if t[0] == 3]
        for t in vols:
            vol_group[t] = mat
        all_vols += vols
        P(f"import {name}: {len(vols)} volumes")
    occ.synchronize()

    # ── 1b) 코일엔드 절단 (JAC279: 코일엔드는 회로로) ────────────────────
    STACK_HALF_MM = 80.0
    coil_vols = [t for t, m in vol_group.items() if m == 3]
    if coil_vols:
        box = occ.addBox(-200, -200, -1, 400, 400, STACK_HALF_MM + 1)
        kept, _ = occ.intersect(coil_vols, [(3, box)],
                                removeObject=True, removeTool=True)
        for t in coil_vols:
            vol_group.pop(t, None)
        all_vols = [t for t in all_vols if t not in coil_vols]
        for t in kept:
            if t[0] == 3:
                vol_group[t] = 3
                all_vols.append(t)
        occ.synchronize()
        P(f"coil trimmed at z<= {STACK_HALF_MM}mm: {len(kept)} volumes")

    # ── 2) fragment (계면 컨포멀) + 그룹 매핑 유지 ──────────────────────
    out, out_map = occ.fragment(all_vols, [])
    occ.synchronize()
    new_group = {}
    for src, frags in zip(all_vols, out_map):
        for fr in frags:
            if fr[0] == 3:
                new_group[fr] = vol_group[src]
    P("after fragment:", len(new_group), "volumes")

    # ── 3) 절단면(주기면) 탐지 + periodic 메시 ───────────────────────────
    # z축을 포함하는 평면 면들을 각도별로 분류
    gmsh.model.occ.synchronize()
    plane_faces = {}                    # round(angle,3) -> [face tags]
    for (dim, tag) in gmsh.model.getEntities(2):
        try:
            ntype = gmsh.model.getType(dim, tag)
            if ntype != "Plane":
                continue
            # 면의 법선(파라미터 중앙)
            uv = gmsh.model.getParametrizationBounds(dim, tag)
            u = (uv[0][0] + uv[1][0]) / 2
            v = (uv[0][1] + uv[1][1]) / 2
            n = gmsh.model.getNormal(tag, [u, v])
            # z성분 ~0 이고 원점을 지나는 평면 = 섹터 절단면 후보
            if abs(n[2]) > 1e-6:
                continue
            com = gmsh.model.occ.getCenterOfMass(dim, tag)
            d = n[0] * com[0] + n[1] * com[1]      # 원점거리(법선방향)
            if abs(d) > 1e-4:
                continue
            ang = math.degrees(math.atan2(com[1], com[0]))
            plane_faces.setdefault(round(ang, 2), []).append(tag)
        except Exception:
            continue
    P("cut-plane candidates:", {k: len(v) for k, v in plane_faces.items()})
    angs = sorted(plane_faces.keys())
    per_ok = 0
    cuts = [a for a in angs if any(abs(abs(a - b) - SEC_ANG) < 1.0
                                   for b in angs)]
    if len(cuts) >= 2:
        a0, a1 = min(cuts), max(cuts)
        th = math.radians(SEC_ANG)
        c, s = math.cos(th), math.sin(th)
        aff = [c, -s, 0, 0,  s, c, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1]
        # 면별 1:1 페어링: a0면 센트로이드를 +45도 회전 -> 최근접 a1면
        import numpy as _np
        def com(tag):
            x = gmsh.model.occ.getCenterOfMass(2, tag)
            return _np.array(x)
        R = _np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        f1 = {t: com(t) for t in plane_faces[a1]}
        for t0 in plane_faces[a0]:
            target = R @ com(t0)
            best, bd = None, 1e9
            for t1, c1 in f1.items():
                d = _np.linalg.norm(c1 - target)
                if d < bd:
                    best, bd = t1, d
            if bd < 0.5:               # 0.5mm 이내면 동일 면
                try:
                    gmsh.model.mesh.setPeriodic(2, [best], [t0], aff)
                    per_ok += 1
                except Exception as e:
                    P(f"  pair fail {t0}->{best}: {str(e)[:100]}")
            else:
                P(f"  no partner for face {t0} (min {bd:.2f}mm)")
        P(f"periodic pairs set: {per_ok}/{len(plane_faces[a0])} "
          f"({a0}deg -> {a1}deg)")
    if not per_ok:
        P("[warn] periodic 미설정 - 절단면 스티칭은 tol 병합에 의존")

    # ── 4) 메시 ─────────────────────────────────────────────────────────
    gmsh.option.setNumber("Mesh.MeshSizeMax", MESH_MAX)
    gmsh.option.setNumber("Mesh.MeshSizeMin", MESH_MIN)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.model.mesh.generate(3)
    ntag, ncoord, _ = gmsh.model.mesh.getNodes()
    P("sector mesh nodes:", len(ntag))

    # 노드 좌표 테이블 (mm)
    idx_of = {int(t): i for i, t in enumerate(ntag)}
    XYZ = np.array(ncoord, float).reshape(-1, 3)

    # 볼륨별 10절점 사면체 수집 (+mat)
    conns, mats = [], []
    for (dim, tag), mat in new_group.items():
        etypes, etags, enodes = gmsh.model.mesh.getElements(3, tag)
        for et, en in zip(etypes, enodes):
            if et != 11:                # 11 = 10-node tetrahedron
                continue
            c = np.array(en, dtype=np.int64).reshape(-1, 10)
            conns.append(c)
            mats.append(np.full(len(c), mat, dtype=np.int32))
    CONN = np.vstack(conns)             # gmsh node tags
    MAT = np.concatenate(mats)
    P("sector tets:", len(CONN), "| mats:", {m: int((MAT == m).sum())
                                             for m in sorted(set(MAT))})
    gmsh.finalize()

    # gmsh tag -> 0-based index
    CONN0 = np.vectorize(idx_of.get)(CONN)

    # gmsh(11) 노드순서 -> ANSYS SOLID87 (I J K L, M(IJ) N(JK) O(KI) P(IL) Q(JL) R(KL))
    # gmsh tet10: 0-3 corners, 4:e01, 5:e12, 6:e02, 7:e03, 8:e13(?), 9:e23  (gmsh 문서 기준
    #             edges: 4=01, 5=12, 6=02, 7=03, 8=23, 9=13)
    GM2AN = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
    CONN0 = CONN0[:, GM2AN]

    # ── 5) 패턴: z-미러(x2) 후 회전(x8) ────────────────────────────────
    def merge(nodes, conn):
        key = np.round(nodes, 4)        # 1e-4 mm 병합 허용오차
        _, uidx, inv = np.unique(key, axis=0, return_index=True,
                                 return_inverse=True)
        return nodes[uidx], inv[conn]

    # z-미러 (섹터가 z>=0 half-axial 이라고 가정; z범위 확인)
    zmin, zmax = XYZ[:, 2].min(), XYZ[:, 2].max()
    P(f"z range: {zmin:.2f} ~ {zmax:.2f} mm")
    MIRROR_PERM = [1, 0, 2, 3, 4, 6, 5, 8, 7, 9]   # I<->J 스왑(자코비안 복원)
    if zmin > -1.0:                     # half-axial 확정
        Xm = XYZ.copy(); Xm[:, 2] *= -1
        nodes = np.vstack([XYZ, Xm])
        conn2 = CONN0[:, MIRROR_PERM] + len(XYZ)
        conn = np.vstack([CONN0, conn2])
        mat = np.concatenate([MAT, MAT])
        nodes, conn = merge(nodes, conn)
        P("after z-mirror:", len(nodes), "nodes,", len(conn), "tets")
    else:
        nodes, conn, mat = XYZ, CONN0, MAT

    # 회전 x8
    NN, NC = [], []
    for k in range(N_SECTOR):
        th = math.radians(SEC_ANG * k)
        c, s = math.cos(th), math.sin(th)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        NN.append(nodes @ R.T)
        NC.append(conn + k * len(nodes))
    nodes8 = np.vstack(NN)
    conn8 = np.vstack(NC)
    mat8 = np.tile(mat, N_SECTOR)
    nodes8, conn8 = merge(nodes8, conn8)
    P("full 360:", len(nodes8), "nodes,", len(conn8), "tets")

    # ── 6) CDB 작성 (m 단위) ────────────────────────────────────────────
    nodes_m = nodes8 / 1000.0
    with open(OUT_CDB, "w") as f:
        f.write("/PREP7\nET,1,87\n")
        f.write(f"NBLOCK,6,SOLID,{len(nodes_m)},{len(nodes_m)}\n")
        f.write("(3i9,6e21.13e3)\n")
        for i, (x, y, z) in enumerate(nodes_m, start=1):
            f.write(f"{i:9d}{0:9d}{0:9d}{x:21.13E}{y:21.13E}{z:21.13E}\n")
        f.write("N,R5.3,LOC,-1,\n")
        f.write(f"EBLOCK,19,SOLID,{len(conn8)},{len(conn8)}\n")
        f.write("(19i10)\n")
        for eid, (nc, m) in enumerate(zip(conn8 + 1, mat8), start=1):
            l1 = [int(m), 1, 1, 0, 0, 0, 0, 0, 10, 0, eid] + [int(v) for v in nc[:8]]
            f.write("".join(f"{v:10d}" for v in l1) + "\n")
            f.write("".join(f"{int(v):10d}" for v in nc[8:]) + "\n")
        f.write("-1\n")
    sz = os.path.getsize(OUT_CDB) / 1e6
    P(f"CDB written: {OUT_CDB} ({sz:.1f} MB)")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
