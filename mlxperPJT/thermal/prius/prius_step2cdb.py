# -*- coding: utf-8 -*-
"""PriusMotor_3D45degree STEP -> active part 분류 -> 컨포멀 메시 -> 45°×8 회전 -> CDB.
   45° 섹터, 활성스택 z=±41.9mm(full axial, z미러 없음). 코일엔드는 별도볼륨->제외+손실비율.
"""
import os
import math
import traceback
import numpy as np

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
STP = (r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019"
       r"\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.stp")
OUT_CDB = r"D:\KDH\simVary\Ansys_Thermal\prius_motor_mesh.cdb"
log = open(os.path.join(SP, "prius_mesh.txt"), "w", encoding="utf-8")
def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

# MAPDL mat 번호 (기존 관례): 1 스테이터 2 자석 3 코일 4 샤프트 5 로터
N_SECTOR, SEC_ANG = 8, 45.0
ZSTK = 41.91                 # 활성스택 반길이(mm)
MESH_MAX, MESH_MIN = 6.0, 1.8   # mm
INCLUDE_SHAFT = True

try:
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    occ = gmsh.model.occ
    occ.importShapes(STP)
    occ.synchronize()

    # ── 1) 볼륨 분류 (바운딩박스 특성) ──────────────────────────────────
    def vinfo(tag):
        xmn, ymn, zmn, xmx, ymx, zmx = gmsh.model.getBoundingBox(3, tag)
        V = occ.getMass(3, tag) / 1e3          # cm3
        rmax = max(math.hypot(xmn, ymn), math.hypot(xmx, ymx),
                   math.hypot(xmn, ymx), math.hypot(xmx, ymn))
        return V, rmax, zmn, zmx
    vol_group = {}                             # dimtag -> mat
    coilend_vols = []
    for (dim, tag) in gmsh.model.getEntities(3):
        V, rmax, zmn, zmx = vinfo(tag)
        active = abs(zmn + ZSTK) < 2 and abs(zmx - ZSTK) < 2   # z=±41.9
        end = (zmx > ZSTK + 5) or (zmn < -ZSTK - 5)            # 축방향 돌출
        if active:
            if V > 200 and rmax > 140:      mat = 1   # stator lam
            elif 60 < V < 130 and 85 < rmax < 110: mat = 5   # rotor lam
            elif 10 < V < 25 and 100 < rmax < 135: mat = 3   # coil slot
            elif 5 < V < 15 and 60 < rmax < 90:    mat = 2   # magnet
            else:
                P(f"  [?] active vol{tag} V={V:.1f} r={rmax:.1f} -> skip"); continue
            vol_group[(3, tag)] = mat
        elif INCLUDE_SHAFT and rmax < 75 and abs(zmn) > 100:
            vol_group[(3, tag)] = 4          # shaft (긴 중심축)
        elif end and 100 < rmax < 135 and V < 12:
            coilend_vols.append(tag)         # 코일엔드
        else:
            P(f"  [excl] vol{tag} V={V:.1f} r={rmax:.1f} z=[{zmn:.0f},{zmx:.0f}]")
    from collections import Counter
    P("active mats:", dict(Counter(vol_group.values())))
    P("coil-end vols:", len(coilend_vols))
    V_slot = sum(occ.getMass(3, t)/1e3 for (d, t), m in vol_group.items() if m == 3)
    V_end = sum(occ.getMass(3, t)/1e3 for t in coilend_vols)
    P(f"V_coil_slot={V_slot:.1f}cm3  V_coil_end={V_end:.1f}cm3  "
      f"end/slot ratio={V_end/V_slot:.3f}")

    # ── 2) active 볼륨만 남기고 fragment (컨포멀) ───────────────────────
    active_tags = list(vol_group.keys())
    all_tags = [t for (d, t) in gmsh.model.getEntities(3)]
    keep = [t for (d, t) in active_tags]
    remove = [(3, t) for t in all_tags if t not in keep]
    if remove:
        occ.remove(remove, recursive=True)
        occ.synchronize()
    out, omap = occ.fragment(active_tags, [])
    occ.synchronize()
    new_group = {}
    for src, frags in zip(active_tags, omap):
        for fr in frags:
            if fr[0] == 3:
                new_group[fr] = vol_group[src]
    P("after fragment:", len(new_group), "volumes")

    # ── 3) 주기면(0°/45°) 페어링 ─────────────────────────────────────────
    plane_faces = {}
    for (dim, tag) in gmsh.model.getEntities(2):
        try:
            if gmsh.model.getType(dim, tag) != "Plane":
                continue
            uv = gmsh.model.getParametrizationBounds(dim, tag)
            n = gmsh.model.getNormal(tag, [(uv[0][0]+uv[1][0])/2,
                                           (uv[0][1]+uv[1][1])/2])
            if abs(n[2]) > 1e-6:
                continue
            com = occ.getCenterOfMass(dim, tag)
            if abs(n[0]*com[0] + n[1]*com[1]) > 1e-3:
                continue
            ang = math.degrees(math.atan2(com[1], com[0]))
            plane_faces.setdefault(round(ang, 1), []).append(tag)
        except Exception:
            continue
    P("cut-plane angles:", {k: len(v) for k, v in plane_faces.items()})
    angs = sorted(plane_faces.keys())
    cuts = [a for a in angs if any(abs(abs(a-b) - SEC_ANG) < 1.5 for b in angs)]
    per_ok = 0
    if len(cuts) >= 2:
        a0, a1 = min(cuts), max(cuts)
        th = math.radians(SEC_ANG); c, s = math.cos(th), math.sin(th)
        aff = [c, -s, 0, 0, s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        f1 = {t: np.array(occ.getCenterOfMass(2, t)) for t in plane_faces[a1]}
        for t0 in plane_faces[a0]:
            tgt = R @ np.array(occ.getCenterOfMass(2, t0))
            best, bd = None, 1e9
            for t1, c1 in f1.items():
                dd = np.linalg.norm(c1 - tgt)
                if dd < bd:
                    best, bd = t1, dd
            if bd < 1.0:
                try:
                    gmsh.model.mesh.setPeriodic(2, [best], [t0], aff)
                    per_ok += 1
                except Exception:
                    pass
    P(f"periodic pairs: {per_ok}")

    # ── 4) 메시 ─────────────────────────────────────────────────────────
    gmsh.option.setNumber("Mesh.MeshSizeMax", MESH_MAX)
    gmsh.option.setNumber("Mesh.MeshSizeMin", MESH_MIN)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.model.mesh.generate(3)
    ntag, ncoord, _ = gmsh.model.mesh.getNodes()
    idx = {int(t): i for i, t in enumerate(ntag)}
    XYZ = np.array(ncoord, float).reshape(-1, 3) / 1000.0   # mm->m
    conns, mats = [], []
    for (dim, tag), mat in new_group.items():
        et, el, en = gmsh.model.mesh.getElements(3, tag)
        for e, nn in zip(et, en):
            if e != 11:
                continue
            conns.append(np.array(nn, np.int64).reshape(-1, 10))
            mats.append(np.full(len(conns[-1]), mat, np.int32))
    CONN = np.vstack(conns); MAT = np.concatenate(mats)
    CONN0 = np.vectorize(idx.get)(CONN)[:, [0,1,2,3,4,5,6,7,9,8]]  # gmsh->ANSYS
    P("sector tets:", len(CONN0), "| mats:",
      {m: int((MAT == m).sum()) for m in sorted(set(MAT))})
    P("sector z(m):", round(XYZ[:,2].min(),4), "~", round(XYZ[:,2].max(),4))
    gmsh.finalize()

    # ── 5) ×8 회전 패턴 (full axial, z미러 없음) + 병합 ─────────────────
    def merge(nodes, conn):
        key = np.round(nodes, 6)
        _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
        return nodes[ui], inv[conn]
    NN, NC = [], []
    for k in range(N_SECTOR):
        th = math.radians(SEC_ANG * k); c, s = math.cos(th), math.sin(th)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        NN.append(XYZ @ R.T); NC.append(CONN0 + k * len(XYZ))
    nodes8 = np.vstack(NN); conn8 = np.vstack(NC); mat8 = np.tile(MAT, N_SECTOR)
    nodes8, conn8 = merge(nodes8, conn8)
    P("full 360:", len(nodes8), "nodes,", len(conn8), "tets")

    # ── 6) CDB ───────────────────────────────────────────────────────────
    with open(OUT_CDB, "w") as f:
        f.write("/PREP7\nET,1,87\n")
        f.write(f"NBLOCK,6,SOLID,{len(nodes8)},{len(nodes8)}\n(3i9,6e21.13e3)\n")
        for i, (x, y, z) in enumerate(nodes8, 1):
            f.write(f"{i:9d}{0:9d}{0:9d}{x:21.13E}{y:21.13E}{z:21.13E}\n")
        f.write("N,R5.3,LOC,-1,\n")
        f.write(f"EBLOCK,19,SOLID,{len(conn8)},{len(conn8)}\n(19i10)\n")
        for eid, (nc, m) in enumerate(zip(conn8 + 1, mat8), 1):
            l1 = [int(m), 1, 1, 0, 0, 0, 0, 0, 10, 0, eid] + [int(v) for v in nc[:8]]
            f.write("".join(f"{v:10d}" for v in l1) + "\n")
            f.write("".join(f"{int(v):10d}" for v in nc[8:]) + "\n")
        f.write("-1\n")
    P(f"CDB: {OUT_CDB} ({os.path.getsize(OUT_CDB)/1e6:.1f} MB)")
    # 손실비율 메모
    import json
    jp = r"D:\KDH\simVary\Ansys_Thermal\prius_losses.json"
    d = json.load(open(jp, encoding="utf-8"))
    d["_V_coil_slot_cm3"] = round(V_slot, 1)
    d["_V_coil_end_cm3"] = round(V_end, 1)
    d["P_copper_end"] = round(d["StrandedLoss"] * V_end / V_slot, 1)
    json.dump(d, open(jp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    P(f"P_copper_end = {d['P_copper_end']} W (slot {d['StrandedLoss']:.0f} × {V_end/V_slot:.3f})")
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    log.close(); os._exit(0)
