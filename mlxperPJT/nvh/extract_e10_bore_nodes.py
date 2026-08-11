# -*- coding: utf-8 -*-
"""e10 MAPDL 메시(ff_e10_mesh_v2.cdb)에서 NVH 하중용 타깃 절점 추출.

전자계 에어갭 가진력을 실을 곳 = **스테이터 보어 표면 절점**(mat=stator, 반경≈
R_STA_IN). 부수적으로 스테이터 OD·권선 엔드턴 절점도 뽑아 npz 로 저장.

선택 방법: 재료(MAT)로 element 선택 → nsle 로 절점 선택 → **선택 절점 좌표를
파이썬으로 받아 반경/z 를 직접 필터**(csys/nwrite 파싱 이슈 회피).

산출: mlxperPJT/nvh/data/e10_target_nodes.npz
  bore_ids/bore_xyz, statorOD_ids/statorOD_xyz, windEnd_ids/windEnd_xyz
"""
from __future__ import annotations

import os, tempfile, traceback
import numpy as np

CDB = r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2"
M_ST, M_MG, M_CO, M_SH, M_RO = 1, 2, 3, 4, 5
R_STA_OUT, R_STA_IN = 0.0990, 0.0713
Z_ST0, Z_ST1 = -0.2075, -0.0575
RT = 1.2e-3                      # 반경밴드(보어 표면 1층 tet10 포함 위해 약간 넉넉)
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
LOG = os.path.join(os.environ.get("SP", tempfile.gettempdir()), "e10_bore_extract.txt")
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush(); print(*a, flush=True)


def sel_node_coords(mapdl):
    """현재 선택된 절점의 (ids, xyz[cartesian]) — 선택 존중 확인 후 반환."""
    ids = np.asarray(mapdl.mesh.nnum)      # 선택 절점 번호
    xyz = np.asarray(mapdl.mesh.nodes)     # 선택 절점 좌표
    if len(ids) != len(xyz):
        # 혹시 mesh.nodes 가 전체를 주면 nnum 으로 매칭
        allids = np.asarray(mapdl.mesh.nnum_all) if hasattr(mapdl.mesh, "nnum_all") else None
        raise RuntimeError(f"nnum({len(ids)})!=nodes({len(xyz)}) 선택 불일치")
    return ids, xyz


def pick_ring(mapdl, mat, r_lo, r_hi, z_lo=None, z_hi=None, tag=""):
    mapdl.allsel()
    mapdl.esel("S", "MAT", "", mat)
    ne = mapdl.mesh.n_elem
    mapdl.nsle("S")
    ids, xyz = sel_node_coords(mapdl)
    r = np.hypot(xyz[:, 0], xyz[:, 1]); z = xyz[:, 2]
    m = (r >= r_lo) & (r <= r_hi)
    if z_lo is not None: m &= (z >= z_lo)
    if z_hi is not None: m &= (z <= z_hi)
    P(f"[{tag}] MAT{mat} elems={ne} selNodes={len(ids)} → ring={m.sum()} "
      f"(r∈[{r_lo:.4f},{r_hi:.4f}])")
    return ids[m], xyz[m]


def main():
    from ansys.mapdl.core import launch_mapdl
    os.makedirs(OUTDIR, exist_ok=True)
    wd = tempfile.mkdtemp(prefix="e10bore_")
    P("launch MAPDL", wd)
    mapdl = launch_mapdl(run_location=wd, override=True, nproc=4, additional_switches="-smp")
    try:
        mapdl.clear(); mapdl.prep7(); mapdl.cdread("DB", CDB, "cdb")
        P("nodes total:", mapdl.mesh.n_node, "elems:", mapdl.mesh.n_elem)
        # 선택 존중 확인
        mapdl.allsel(); mapdl.esel("S", "MAT", "", M_ST); mapdl.nsle("S")
        P("sanity: MAT1 n_node(sel)=", mapdl.mesh.n_node,
          "len(mesh.nodes)=", len(mapdl.mesh.nodes))

        out = {}
        bore_ids, bore_xyz = pick_ring(mapdl, M_ST, R_STA_IN - RT, R_STA_IN + RT,
                                       Z_ST0 - 1e-3, Z_ST1 + 1e-3, "bore")
        out["bore_ids"], out["bore_xyz"] = bore_ids, bore_xyz
        od_ids, od_xyz = pick_ring(mapdl, M_ST, R_STA_OUT - RT, R_STA_OUT + RT,
                                   Z_ST0 - 1e-3, Z_ST1 + 1e-3, "statorOD")
        out["statorOD_ids"], out["statorOD_xyz"] = od_ids, od_xyz
        # 권선 엔드턴(축 hi 끝, 스택 밖)
        we_ids, we_xyz = pick_ring(mapdl, M_CO, 0.0, 1.0, Z_ST1 - 1e-4, 1.0, "windEnd_hi")
        out["windEnd_ids"], out["windEnd_xyz"] = we_ids, we_xyz

        if len(bore_ids) < 50:
            P(f"[WARN] 보어 절점 {len(bore_ids)}개 — 예상보다 적음. 반경밴드/재료 확인 필요.")
        outnpz = os.path.join(OUTDIR, "e10_target_nodes.npz")
        np.savez(outnpz, **out)
        P(f"saved {outnpz}: bore={len(bore_ids)} OD={len(od_ids)} windEnd={len(we_ids)}")
        if len(bore_ids):
            rr = np.hypot(bore_xyz[:,0], bore_xyz[:,1])
            P(f"  bore r=[{rr.min():.4f},{rr.max():.4f}] "
              f"z=[{bore_xyz[:,2].min():.4f},{bore_xyz[:,2].max():.4f}]")
        P("EXTRACT-OK")
    finally:
        try: mapdl.exit()
        except Exception: pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        P("FATAL\n" + traceback.format_exc()[:2000])
    finally:
        log.close()
