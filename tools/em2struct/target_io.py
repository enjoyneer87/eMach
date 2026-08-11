# -*- coding: utf-8 -*-
"""em2struct.target_io — 구조 솔버 메시 → TargetMesh (타깃 절점 로더).

맵핑의 타깃(하중을 실을 구조 절점)을 여러 소스에서 읽는다:
  read_mapdl_nblock : ANSYS/MAPDL CDB 의 NBLOCK 을 직접 파싱(경량, MAPDL 런치 불필요).
  target_from_arrays: numpy 배열에서 바로.

CDB 의 재료·표면 선택(예: 스테이터 보어만)은 MAPDL 세션이 필요하므로 별도
드라이버(예: examples/extract_e10_bore_nodes.py)에서 수행하고, 그 산출 좌표를
target_from_arrays 로 넘긴다. 이 모듈은 '전체 절점' 경량 파싱만 담당.
"""
from __future__ import annotations

import re
from typing import Optional

import numpy as np

from .core import TargetMesh


def read_mapdl_nblock(cdb_path: str, max_nodes: Optional[int] = None) -> TargetMesh:
    """CDB(.cdb) 텍스트에서 NBLOCK(절점 id·좌표)만 파싱 → TargetMesh.

    MAPDL 을 띄우지 않고 노드 좌표를 얻는다. 대용량(수백 MB)도 스트리밍 파싱.
    NBLOCK 포맷: 헤더 ``NBLOCK,6,SOLID,...`` + 포맷 ``(3i9,6e21.13e3)`` 뒤에
    각 행 = nodeID, (solid), (line), x, y, z (뒤 회전 DOF 생략 가능).

    Parameters
    ----------
    cdb_path  : .cdb 경로.
    max_nodes : 디버그용 상한(None=전체).
    """
    ids, xs, ys, zs = [], [], [], []
    in_block = False
    fieldw = None  # 좌표 필드 폭(고정폭 파싱용)
    ncoord_start = None
    with open(cdb_path, "r", errors="ignore") as fh:
        for line in fh:
            up = line.upper()
            if not in_block:
                if up.startswith("NBLOCK"):
                    in_block = True
                    fmt = None
                continue
            # 블록 진입 후 첫 (…) 포맷 라인
            if line.lstrip().startswith("("):
                # 예: (3i9,6e21.13e3) → 정수 3개 폭9, 실수 폭21
                m = re.match(r"\((\d+)i(\d+),\s*\d+e(\d+)", line.strip(), re.I)
                if m:
                    n_int, iw, ew = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    fieldw = (n_int, iw, ew)
                continue
            # 블록 종료 표식
            s = line.rstrip("\n")
            if s.strip().startswith("-1") or s.strip() == "" or s.upper().startswith("N,R") \
               or s.upper().startswith("EBLOCK") or s.upper().startswith("CMBLOCK"):
                break
            try:
                if fieldw is not None:
                    n_int, iw, ew = fieldw
                    nid = int(s[:iw])
                    base = n_int * iw
                    x = float(s[base:base+ew])
                    y = float(s[base+ew:base+2*ew])
                    ztxt = s[base+2*ew:base+3*ew].strip()
                    z = float(ztxt) if ztxt else 0.0
                else:  # 자유형 폴백
                    parts = s.split()
                    nid = int(parts[0]); x, y, z = map(float, parts[-3:])
            except Exception:
                continue
            ids.append(nid); xs.append(x); ys.append(y); zs.append(z)
            if max_nodes and len(ids) >= max_nodes:
                break
    if not ids:
        raise ValueError(f"NBLOCK 을 찾지 못했거나 비었습니다: {cdb_path}")
    nodes = np.column_stack([xs, ys, zs])
    return TargetMesh(nodes=nodes, node_ids=np.array(ids, dtype=np.int64))


def target_from_arrays(nodes, node_ids=None, areas=None) -> TargetMesh:
    """numpy 배열(예: MAPDL 세션에서 추출한 선택 절점)에서 TargetMesh 생성."""
    return TargetMesh(nodes=np.asarray(nodes, float),
                      node_ids=(None if node_ids is None else np.asarray(node_ids)),
                      areas=(None if areas is None else np.asarray(areas, float)))
