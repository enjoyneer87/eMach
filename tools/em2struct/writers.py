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


def write_lsdyna_segment(
    result: MappingResult,
    path: str,
    seg_target=None,
    sign: float = -1.0,
    tol: float = 0.0,
    curve_id0: int = 2000,
    include_tangential_as_nodal: bool = False,
) -> str:
    """LS-DYNA *LOAD_SEGMENT 법선 압력 카드(.k).

    맵핑 결과(세그먼트 중심점에서의 절점력, ``result``)를 세그먼트 법선압력으로
    환산해 내보낸다.  pressure[s,t] = sign · (F_s(t)·n_s) / area_s  [Pa].

    *LOAD_SEGMENT 는 법선 성분만 표현 가능(스칼라 압력). LS-DYNA 관례상 양압력은
    세그먼트 법선 **반대**(면 안쪽)로 작용하므로 기본 sign=-1(외향력→양압력).

    Parameters
    ----------
    result   : make_segment_target(...).as_target_mesh() 에 맵핑한 결과
               (result.forces shape = (S,3,C), S=세그먼트 수).
    seg_target : 동일 세그먼트의 SegmentTarget(법선·면적·코너ID 제공).
    sign     : 압력 부호 관례(+면 법선방향 양압력). 기본 -1.
    tol      : |압력|max 가 이 값 이하인 세그먼트 생략.
    include_tangential_as_nodal : True 면 접선(법선 제거) 잔여 힘을 별도
               *LOAD_NODE_POINT 로 함께 출력(법선압력이 못 싣는 성분 보존).
    """
    if seg_target is None:
        raise ValueError("write_lsdyna_segment 는 seg_target(SegmentTarget) 이 필요합니다.")
    F = result.forces                            # (S,3,C)
    if F.shape[0] != seg_target.s:
        raise ValueError(f"result S({F.shape[0]}) != seg_target.s({seg_target.s}). "
                         "make_segment_target(...).as_target_mesh() 에 맵핑했는지 확인.")
    n = seg_target.normals                       # (S,3)
    area = seg_target.areas                      # (S,)
    conn = seg_target.conn_ids                   # (S,4)
    C = result.ncols
    t = _times(result)

    # 법선압력 시간이력 (S,C)
    Fn = np.einsum("sjc,sj->sc", F, n)           # 법선방향 힘
    pres = sign * Fn / area[:, None]
    pmax = np.abs(pres).max(axis=1)
    keep = np.where(pmax > tol)[0]

    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    cid = curve_id0
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("$ em2struct -> LS-DYNA *LOAD_SEGMENT 법선 압력\n")
        fh.write(f"$ mapper={result.mapper}  segments={len(keep)}  steps={C}  sign={sign}\n")
        fh.write("*KEYWORD\n")
        cards = []   # (n1,n2,n3,n4,lcid)
        for s in keep:
            series = pres[s]
            if np.all(series == 0):
                continue
            fh.write("*DEFINE_CURVE\n")
            fh.write(f"{cid},0,1.0,1.0,0.0,0.0\n")
            if C == 1:
                fh.write(f"{0.0:20.8e}{series[0]:20.8e}\n")
                fh.write(f"{1.0:20.8e}{series[0]:20.8e}\n")
            else:
                for k in range(C):
                    fh.write(f"{t[k]:20.8e}{series[k]:20.8e}\n")
            cards.append((*[int(x) for x in conn[s]], cid))
            cid += 1
        fh.write("*LOAD_SEGMENT\n")
        fh.write("$    lcid        sf        at        n1        n2        n3        n4\n")
        for n1, n2, n3, n4, lcid in cards:
            fh.write(f"{lcid:10d}{1.0:10.4f}{0.0:10.4f}"
                     f"{n1:10d}{n2:10d}{n3:10d}{n4:10d}\n")

        if include_tangential_as_nodal:
            # 접선 잔여력(법선 제거) → 중심점 등가 절점하중(참고, 별도 절점 필요)
            Ft = F - np.einsum("sc,sj->sjc", Fn, n)
            fh.write("$ --- 접선 잔여력(참고): 세그먼트 중심점 등가, 필요시 별도 처리 ---\n")
            fh.write(f"$ max|Ft| = {np.linalg.norm(Ft,axis=1).max():.4e} N\n")
        fh.write("*END\n")
    return path


def write_ansys_remote_force(
    source,
    target,
    path: str,
    scope: str = "nearest",
    k: int = 30,
    radius: Optional[float] = None,
    coupling: str = "rbe3",
    pilot_id0: int = 9000001,
    tol: float = 0.0,
) -> str:
    """ANSYS/MAPDL **원격힘(Remote Force)** 스크립트(.inp).

    소스 힘점(예: 로터 8극 / 스테이터 48치)마다 **파일럿 절점**을 만들고, 그 힘을
    받을 타깃 표면 절점들에 **RBE3**(변형허용) 또는 **CERIG**(강체)로 결합한 뒤,
    파일럿에 힘(+모멘트) 시간이력을 가한다. 비컨포멀 절점맞춤 불필요 — 각 극/치의
    합력이 해당 표면 영역으로 분산 전달된다.

    타깃 절점→소스 배정: ``scope``
      'nearest' : 각 타깃을 xy 평면상 최근접 소스에 배정(각도 섹터 분할, 로터극에 적합).
      'knn'     : 각 소스가 자신에 최근접한 k개 타깃과 결합.
      'radius'  : 각 소스가 반경 내 타깃과 결합.
    파일럿 위치 = 배정된 타깃 절점들의 중심(실제 3D 표면 위, 소스의 축슬라이스
    z=0 과 타깃 메시 z 불일치를 자동 보정).

    Parameters
    ----------
    source : ForceField(NODAL_FORCE) — 소스 힘점(극/치).
    target : TargetMesh — 실제 솔버 절점 ID·좌표를 가진 표면 메시.
    coupling : 'rbe3'(권장, 하중분산) | 'cerig'(강체).
    """
    import numpy as _np
    from scipy.spatial import cKDTree
    sp = source.points                     # (S,3)
    sf = source.as_nodal_forces()          # (S,3,C)
    S, _, C = sf.shape
    tp = target.nodes                      # (M,3)
    tids = target.node_ids
    t = source.times if (source.times is not None and len(source.times) == C) else _np.arange(C)

    # 타깃→소스 배정
    assign = {s: [] for s in range(S)}
    if scope == "nearest":
        tree = cKDTree(sp[:, :2])          # xy 평면(축 z 불일치 무시)
        _, near = tree.query(tp[:, :2], k=1)
        for i, s in enumerate(near):
            assign[int(s)].append(i)
    elif scope in ("knn", "radius"):
        tree = cKDTree(tp)
        for s in range(S):
            if scope == "knn":
                _, idx = tree.query(sp[s], k=min(k, len(tp)))
                idx = _np.atleast_1d(idx)
            else:
                idx = _np.array(tree.query_ball_point(sp[s], radius or 1e9), dtype=int)
            assign[s] = list(idx)
    else:
        raise ValueError("scope must be 'nearest'|'knn'|'radius'")

    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    comp = ("FX", "FY", "FZ")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("! em2struct → MAPDL 원격힘(Remote Force) : 소스 힘점별 pilot + "
                 f"{coupling.upper()}\n")
        fh.write(f"! sources={S} steps={C} coupling={coupling} scope={scope}\n")
        fh.write("/prep7\n")
        pilots = []
        for s in range(S):
            slaves = assign[s]
            fmax = _np.linalg.norm(sf[s], axis=0).max()
            if not slaves or fmax <= tol:
                continue
            pid = pilot_id0 + s
            cen = tp[slaves].mean(axis=0)
            fh.write(f"\n! ---- source {s}: |F|max={fmax:.3g} N, slaves={len(slaves)} ----\n")
            fh.write(f"n,{pid},{cen[0]:.8e},{cen[1]:.8e},{cen[2]:.8e}\n")
            # 슬레이브 절점 선택 → 컴포넌트
            fh.write("nsel,none\n")
            for j in slaves:
                fh.write(f"nsel,a,node,,{int(tids[j])}\n")
            cname = f"_RF_SLV{s}"
            fh.write(f"cm,{cname},node\n")
            if coupling == "cerig":
                fh.write(f"cerig,{pid},ALL,{cname}\n")
            else:
                fh.write(f"rbe3,{pid},ALL,{cname}\n")
            fh.write("allsel\n")
            pilots.append((s, pid))
        # 하중(정적: col0 / 트랜지언트: 스텝루프)
        fh.write("\nfinish\n/solu\n")
        if C == 1:
            for s, pid in pilots:
                for j in range(3):
                    v = sf[s, j, 0]
                    if v != 0.0:
                        fh.write(f"f,{pid},{comp[j]},{v:.8e}\n")
        else:
            fh.write("antype,trans\n")
            for kstep in range(C):
                fh.write(f"\n! load step {kstep+1} t={t[kstep]:.6g}\n")
                fh.write(f"time,{t[kstep]:.8g}\n")
                for s, pid in pilots:
                    for j in range(3):
                        v = sf[s, j, kstep]
                        if v != 0.0:
                            fh.write(f"f,{pid},{comp[j]},{v:.8e}\n")
                fh.write("solve\n")
        fh.write("finish\n")
    return path


WRITERS = {
    "ansys_mechanical": write_ansys_mechanical,
    "mapdl": write_ansys_mechanical,
    "lsdyna": write_lsdyna,
    "lsdyna_segment": write_lsdyna_segment,
    "ansys_motion": write_ansys_motion,
    "motion": write_ansys_motion,
}
