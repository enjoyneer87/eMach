# -*- coding: utf-8 -*-
"""노드/메시 수준 SCL-M 상사 필드 스케일링 — FEA export(txt/gz) 변환기.

B-보존 기하 스케일링(반경 s = k_r'/k_r)을 Motor-CAD FEA 텍스트 export 에
직접 적용한다. 대응 규칙 (본문 eq (6)~(7), Table 1):

    좌표 x, y      ->  s * x, s * y          (반경 치수)
    B_x, B_y       ->  불변                   (B 보존)
    A (MVP)        ->  s * A                  (A ∝ k_a k_r, k_a=1)
    J, Je          ->  J / s                  (J ∝ 1/k_r)
    H_x, H_y       ->  불변                   (H = ν B)
    Mur, ν, σ, Brem->  불변                   (재료)
    RegionsTable J ->  J / s

포맷은 콤마 구분(다운스트림 파서는 split(',') — 고정폭 아님)이며, 각
수치는 원 토큰의 소수 자릿수·폭을 유지해 재기록한다. Solution 블록 구조
(회전자 위치 스텝)는 그대로 통과한다.

정밀도 주의: 원 export 의 B 는 소수 3자리(±0.0005 T 양자화)라, 스케일본과
실해석본의 비교 분해능 바닥은 저 |B| 셀에서 ~0.5% 수준이다.
"""
from __future__ import annotations

import gzip
from typing import IO

__all__ = ["scale_fea_txt"]

# 테이블별 (스케일 규칙) — 열 인덱스: 0-기점
#   ElementsTable: TriIndex,N1,N2,N3,RegCode, Bx,By, A, J, Je, Hx,Hy, Mur
#   NodesTable:    NodeIndex, x, y, A
#   RegionsTable:  RegionCode,BhCode, nu, Jval, BremX,Y,R,T, Sigma,Density,Name
_RULES = {
    "ElementsTable": {7: "s", 8: "inv", 9: "inv"},
    "NodesTable": {1: "s", 2: "s", 3: "s"},
    "RegionsTable": {3: "inv"},
}


def _scale_token(tok: str, factor: float) -> str:
    """토큰 하나를 스케일하되 소수 자릿수·최소 폭을 보존한다."""
    st = tok.strip()
    if not st or st in ("-",):
        return tok
    try:
        v = float(st)
    except ValueError:
        return tok
    dec = len(st.split(".")[1]) if "." in st else 0
    out = f"{v * factor:.{dec}f}"
    return out.rjust(len(tok))


def _open(path: str, mode: str) -> IO:
    if str(path).endswith(".gz"):
        return gzip.open(path, mode + "t", encoding="utf-8",
                         errors="ignore", compresslevel=4)
    return open(path, mode, encoding="utf-8", errors="ignore")


def scale_fea_txt(src: str, dst: str, s: float,
                  progress: bool = False) -> dict:
    """src(txt|txt.gz) 를 반경 배율 s 로 상사 변환해 dst 에 쓴다.

    반환: {'n_lines', 'n_scaled_rows', 'tables': {이름: 행수}} 통계.
    """
    inv = 1.0 / s
    stats = {"n_lines": 0, "n_scaled_rows": 0, "tables": {}}
    mode = None          # 현재 테이블 이름
    remain = 0           # 남은 데이터 행 수
    rules = {}

    with _open(src, "r") as fi, _open(dst, "w") as fo:
        for line in fi:
            stats["n_lines"] += 1
            if remain <= 0:
                mode = None
            if mode is None:
                parts = line.split()
                if (len(parts) >= 3 and parts[-1].endswith("Table")
                        and parts[-2].isdigit()):
                    mode = parts[-1]
                    remain = int(parts[-2])
                    rules = _RULES.get(mode, {})
                    stats["tables"][mode] = stats["tables"].get(mode, 0) \
                        + remain
                fo.write(line)
                continue
            # 테이블 구간: 데이터 행인지 판별 (헤더/단위/구분선 통과)
            toks = line.rstrip("\n").split(",")
            first = toks[0].strip()
            if not first or not first.lstrip("-").isdigit():
                fo.write(line)
                continue
            remain -= 1
            if rules:
                for idx, kind in rules.items():
                    if idx < len(toks):
                        toks[idx] = _scale_token(
                            toks[idx], s if kind == "s" else inv)
                stats["n_scaled_rows"] += 1
                fo.write(",".join(toks) + "\n")
            else:
                fo.write(line)
    return stats
