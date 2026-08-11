# -*- coding: utf-8 -*-
"""em2struct.writers — 맵핑 절점력 → 구조 솔버별 하중 파일.

지원:
  write_ansys_mechanical : MAPDL F 커맨드(.inp) + External Data CSV.
  write_lsdyna           : *LOAD_NODE_POINT + *DEFINE_CURVE (시간이력).
  write_ansys_motion     : Motion 외부 절점하중 CSV.

모든 라이터는 MappingResult(타깃 절점력 [N])를 받는다. 시간/하모닉 다열이면
솔버별 관례에 맞춰 시간이력 곡선 또는 스텝별 파일로 내보낸다.
"""
from __future__ import annotations

import os
from typing import Optional, Sequence

import numpy as np

from .core import MappingResult


def _times(result: MappingResult):
    if result.times is not None and len(result.times) == result.ncols:
        return np.asarray(result.times, float)
    return np.arange(result.ncols, dtype=float)


# ============================================================ ANSYS Mechanical
def write_ansys_mechanical(
    result: MappingResult,
    path: str,
    mode: str = "apdl",
    col: Optional[int] = None,
    tol: float = 0.0,
) -> list:
    """ANSYS Mechanical/MAPDL 절점 하중 내보내기.

    mode='apdl'     : F 커맨드 스크립트(.inp). col 지정 시 그 스텝만, 아니면
                      *DIM 테이블 + 시간이력(_LSTEP)로 전 스텝. 단일열이면 정적 F.
    mode='external' : Mechanical External Data 용 CSV(Node,X,Y,Z,FX,FY,FZ[,TIME]).
                      다열이면 시간열 포함 long-format.

    tol : |F| 가 이 값 이하인 절점은 생략(파일 축소).
    반환: 생성된 파일 경로 리스트.
    """
    F = result.forces
    ids = result.target.node_ids
    xyz = result.target.nodes
    t = _times(result)
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    if mode == "external":
        return [_write_mech_external(path, ids, xyz, F, t, tol)]
    if mode != "apdl":
        raise ValueError("mode must be 'apdl' or 'external'")

    written = []
    if result.ncols == 1 or col is not None:
        c = 0 if result.ncols == 1 else col
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("! em2struct → MAPDL 절점 하중 (단일 스텝)\n")
            fh.write(f"! mapper={result.mapper}  col={c}  t={t[c]:.6g}\n/prep7\n")
            _apdl_f_block(fh, ids, F[:, :, c], tol)
            fh.write("finish\n")
        written.append(path)
    else:
        # 시간이력: 각 절점·성분별 테이블배열 + 스텝루프
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("! em2struct → MAPDL 절점 하중 시간이력\n")
            fh.write(f"! mapper={result.mapper}  nsteps={result.ncols}\n")
            fh.write("! 사용법: transient/harmonic 해석의 각 하중스텝에서 아래 배열 참조\n")
            fh.write("/prep7\nfinish\n/solu\nantype,trans\n")
            fh.write(f"*dim,EM_T,array,{result.ncols}\n")
            for k in range(result.ncols):
                fh.write(f"EM_T({k+1})={t[k]:.8g}\n")
            comp = ("FX", "FY", "FZ")
            for k in range(result.ncols):
                fh.write(f"\n! ---- load step {k+1}, time={t[k]:.6g} ----\n")
                fh.write(f"time,{t[k]:.8g}\n")
                _apdl_f_block(fh, ids, F[:, :, k], tol)
                fh.write("solve\n")
            fh.write("finish\n")
        written.append(path)
    return written


def _apdl_f_block(fh, ids, F2d, tol):
    comp = ("FX", "FY", "FZ")
    mag = np.linalg.norm(F2d, axis=1)
    for i, nid in enumerate(ids):
        if mag[i] <= tol:
            continue
        for j in range(3):
            v = F2d[i, j]
            if v != 0.0:
                fh.write(f"f,{int(nid)},{comp[j]},{v:.8e}\n")


def _write_mech_external(path, ids, xyz, F, t, tol):
    single = F.shape[2] == 1
    with open(path, "w", encoding="utf-8") as fh:
        if single:
            fh.write("Node,X,Y,Z,FX,FY,FZ\n")
            for i, nid in enumerate(ids):
                if np.linalg.norm(F[i, :, 0]) <= tol:
                    continue
                fh.write(f"{int(nid)},{xyz[i,0]:.8e},{xyz[i,1]:.8e},{xyz[i,2]:.8e},"
                         f"{F[i,0,0]:.8e},{F[i,1,0]:.8e},{F[i,2,0]:.8e}\n")
        else:
            fh.write("Node,X,Y,Z,TIME,FX,FY,FZ\n")
            for k in range(F.shape[2]):
                for i, nid in enumerate(ids):
                    if np.linalg.norm(F[i, :, k]) <= tol:
                        continue
                    fh.write(f"{int(nid)},{xyz[i,0]:.8e},{xyz[i,1]:.8e},{xyz[i,2]:.8e},"
                             f"{t[k]:.8e},{F[i,0,k]:.8e},{F[i,1,k]:.8e},{F[i,2,k]:.8e}\n")
    return path


# ============================================================ LS-DYNA
def write_lsdyna(
    result: MappingResult,
    path: str,
    dof_curve: bool = True,
    tol: float = 0.0,
    curve_id0: int = 1000,
) -> str:
    """LS-DYNA 절점 하중 키워드 파일(.k).

    다열(시간이력)이면 절점·성분마다 *DEFINE_CURVE(시간 vs 힘) 를 만들고
    *LOAD_NODE_POINT 에서 scale=1 로 참조한다. 단일열이면 상수 곡선 1개.

    dof_curve=True : 성분별 곡선(권장, 임의 파형).
    tol            : |F|max 가 이 값 이하인 절점 생략.
    curve_id0      : 곡선 ID 시작값.
    """
    F = result.forces
    ids = result.target.node_ids
    t = _times(result)
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    fmax = np.linalg.norm(F, axis=1).max(axis=1)   # 절점별 시간최대 크기
    keep = np.where(fmax > tol)[0]
    cid = curve_id0
    dof_map = (1, 2, 3)  # LS-DYNA DOF: 1=x,2=y,3=z

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("$ em2struct → LS-DYNA 절점 하중\n")
        fh.write(f"$ mapper={result.mapper}  nodes={len(keep)}  steps={result.ncols}\n")
        fh.write("*KEYWORD\n")
        curves = []  # (node, dof, curve_id)
        # 곡선 정의
        for i in keep:
            for j in range(3):
                series = F[i, j, :]
                if np.all(series == 0):
                    continue
                fh.write("*DEFINE_CURVE\n")
                fh.write(f"{cid},0,1.0,1.0,0.0,0.0\n")
                if result.ncols == 1:
                    # 상수: 두 점으로 표현(t=0, t=1)
                    fh.write(f"{0.0:20.8e}{series[0]:20.8e}\n")
                    fh.write(f"{1.0:20.8e}{series[0]:20.8e}\n")
                else:
                    for k in range(result.ncols):
                        fh.write(f"{t[k]:20.8e}{series[k]:20.8e}\n")
                curves.append((int(ids[i]), dof_map[j], cid))
                cid += 1
        # 하중 카드
        fh.write("*LOAD_NODE_POINT\n")
        fh.write("$    node       dof      lcid        sf\n")
        for node, dof, lcid in curves:
            fh.write(f"{node:10d}{dof:10d}{lcid:10d}{1.0:10.4f}\n")
        fh.write("*END\n")
    return path


# ============================================================ Ansys Motion
def write_ansys_motion(
    result: MappingResult,
    path: str,
    col: Optional[int] = None,
    tol: float = 0.0,
) -> str:
    """Ansys Motion 외부 절점하중 CSV.

    Motion 플렉시블 바디에 절점력을 임포트하는 long-format:
        NodeID, Time, Fx, Fy, Fz
    단일열이면 Time=0. 시간이력이면 전 스텝.
    """
    F = result.forces
    ids = result.target.node_ids
    t = _times(result)
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# em2struct → Ansys Motion nodal force import\n")
        fh.write("# NodeID,Time,Fx,Fy,Fz  (SI: N, s)\n")
        cols = [col] if col is not None else range(result.ncols)
        for k in cols:
            for i, nid in enumerate(ids):
                if np.linalg.norm(F[i, :, k]) <= tol:
                    continue
                fh.write(f"{int(nid)},{t[k]:.8e},{F[i,0,k]:.8e},"
                         f"{F[i,1,k]:.8e},{F[i,2,k]:.8e}\n")
    return path


WRITERS = {
    "ansys_mechanical": write_ansys_mechanical,
    "mapdl": write_ansys_mechanical,
    "lsdyna": write_lsdyna,
    "ansys_motion": write_ansys_motion,
    "motion": write_ansys_motion,
}
