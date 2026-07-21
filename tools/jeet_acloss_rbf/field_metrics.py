# -*- coding: utf-8 -*-
"""Motor-CAD ``.mes`` 요소 테이블에서 전자기 부하 지표를 산출한다.

Motor-CAD 가 내보낸 ``Magnetic_*.txt`` 는 세 개의 표를 담는다.

  ElementsTable : TriIndex, Node1..3, RegCode, Bx, By, A, J, Je
  NodesTable    : NodeIndex, X, Y, A
  RegionsTable  : RegionCode, ..., Jval, ..., Sigma, ..., RegionName

영역 *이름*이 있으므로 공극(``a1``..``aN``)과 도체(``Turn_<층>_<슬롯>``)
를 추측 없이 특정할 수 있고, 삼각형 면적으로 가중해 평균을 낸다 ---
메시가 도체 주변에서 조밀하므로 단순 산술평균은 편향된다.

  from jeet_acloss_rbf.field_metrics import parse_mes_txt, loading_metrics
  m = loading_metrics(parse_mes_txt(path))
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Optional

import numpy as np

__all__ = ["parse_mes_txt", "region_summary", "loading_metrics",
           "compare_models"]

_AIRGAP_RE = re.compile(r"^a\d+$", re.I)
# Motor-CAD 명명은 Turn_<층>_<슬롯> 이다. 첫 인덱스가 반경방향 층으로,
# 층 1이 슬롯 개구부(공극)에 가장 가깝고 층 N이 슬롯 바닥이다. 같은 층의
# 슬롯들은 반경이 동일하고 상(phase)만 다르다.
_TURN_RE = re.compile(r"^Turn_(\d+)_(\d+)$", re.I)
_LAYER_GROUP = 1


def _rows(lines, start, n):
    """수치 행 n개를 파싱한다 (헤더/단위/구분선 건너뜀)."""
    out, i = [], start
    while i < len(lines) and len(out) < n:
        parts = [s.strip() for s in lines[i].split(',')]
        i += 1
        if len(parts) < 4 or not parts[0]:
            continue
        try:
            out.append([float(v) if v not in ('', '-') else np.nan
                        for v in parts])
        except ValueError:
            continue                      # 헤더/단위 줄
    return out, i


def parse_mes_txt(path: str) -> dict:
    """세 표를 모두 읽어 요소 중심좌표·면적까지 계산해 돌려준다."""
    with open(path, encoding='utf-8', errors='ignore') as fh:
        lines = fh.readlines()

    idx = {}
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*\d+\s+(\d+)\s+(\w+Table)", ln)
        if m:
            idx[m.group(2)] = (i + 1, int(m.group(1)))

    el_start, n_el = idx['ElementsTable']
    nd_start, n_nd = idx['NodesTable']
    elems, _ = _rows(lines, el_start, n_el)
    nodes, _ = _rows(lines, nd_start, n_nd)

    E = np.asarray(elems, float)
    N = np.asarray(nodes, float)

    # 지역 이름 (RegionsTable 은 이름이 문자열이라 따로 처리)
    names: Dict[int, str] = {}
    jval: Dict[int, float] = {}
    sigma: Dict[int, float] = {}
    if 'RegionsTable' in idx:
        rs, n_rg = idx['RegionsTable']
        got = 0
        for ln in lines[rs:]:
            parts = [s.strip() for s in ln.split(',')]
            if len(parts) < 11:
                continue
            try:
                code = int(float(parts[0]))
            except ValueError:
                continue
            names[code] = parts[10]
            try:
                jval[code] = float(parts[3])
                sigma[code] = float(parts[8])
            except ValueError:
                pass
            got += 1
            if got >= n_rg:
                break

    node_xy = np.full((int(N[:, 0].max()) + 1, 2), np.nan)
    node_xy[N[:, 0].astype(int)] = N[:, 1:3]

    tri = E[:, 1:4].astype(int)
    P = node_xy[tri]                                   # (n_el, 3, 2)
    cx, cy = P[:, :, 0].mean(1), P[:, :, 1].mean(1)
    area = 0.5 * np.abs(
        (P[:, 1, 0] - P[:, 0, 0]) * (P[:, 2, 1] - P[:, 0, 1])
        - (P[:, 2, 0] - P[:, 0, 0]) * (P[:, 1, 1] - P[:, 0, 1]))

    return {
        'reg': E[:, 4].astype(int), 'bx': E[:, 5], 'by': E[:, 6],
        'a_wbm': E[:, 7], 'j_am2': E[:, 8],
        'x_mm': cx, 'y_mm': cy, 'area_mm2': area,
        'b_T': np.hypot(E[:, 5], E[:, 6]),
        'names': names, 'jval': jval, 'sigma': sigma, 'path': path,
    }


def _wstat(v, w):
    """면적 가중 평균과 최댓값."""
    if v.size == 0 or np.sum(w) <= 0:
        return float('nan'), float('nan')
    return float(np.sum(w * v) / np.sum(w)), float(np.max(v))


def region_summary(p: dict) -> Dict[str, dict]:
    """영역 이름별 면적가중 |B| 요약."""
    out = {}
    for code, name in p['names'].items():
        m = p['reg'] == code
        if not m.any():
            continue
        mean, mx = _wstat(p['b_T'][m], p['area_mm2'][m])
        r = np.hypot(p['x_mm'][m], p['y_mm'][m])
        out[name] = {'code': int(code), 'n_elem': int(m.sum()),
                     'area_mm2': float(p['area_mm2'][m].sum()),
                     'b_mean_T': mean, 'b_max_T': mx,
                     'r_min_mm': float(r.min()), 'r_max_mm': float(r.max()),
                     'j_a_mm2': float(p['jval'].get(code, 0.0)) / 1e6}
    return out


def loading_metrics(p: dict) -> dict:
    """공극/도체 자속밀도와 도체별 전류밀도.

    B_g   : 공극 영역(a1..a4)의 반경방향 성분 peak 및 면적가중 |B| 평균
    B_Cu  : 반경방향 층(Turn_k_*)별 면적가중 |B| --- 층 1이 슬롯 개구부에
            가장 가까워 누설자속이 크고, 층 번호가 커질수록(슬롯 바닥)
            작아진다. 같은 층의 여러 슬롯은 상만 다르므로 평균한다.
    """
    reg, b, w = p['reg'], p['b_T'], p['area_mm2']
    x, y = p['x_mm'], p['y_mm']

    gap_codes = [c for c, n in p['names'].items() if _AIRGAP_RE.match(n)]
    gm = np.isin(reg, gap_codes)
    br = (p['bx'] * x + p['by'] * y) / np.hypot(x, y)     # 반경 성분
    g_mean, g_max = _wstat(b[gm], w[gm])
    airgap = {'regions': [p['names'][c] for c in gap_codes],
              'n_elem': int(gm.sum()),
              'r_min_mm': float(np.hypot(x, y)[gm].min()),
              'r_max_mm': float(np.hypot(x, y)[gm].max()),
              'b_mean_T': g_mean, 'b_max_T': g_max,
              'br_peak_T': float(np.max(np.abs(br[gm]))) if gm.any()
              else float('nan')}

    turns: Dict[str, dict] = {}
    n_turn = 0
    for code, name in p['names'].items():
        mt = _TURN_RE.match(name)
        if not mt:
            continue
        k = int(mt.group(_LAYER_GROUP))
        n_turn = max(n_turn, k)
        m = reg == code
        if not m.any():
            continue
        mean, mx = _wstat(b[m], w[m])
        d = turns.setdefault(str(k), {'b_mean_T': [], 'b_max_T': [],
                                      'area_mm2': [], 'j_a_mm2': [],
                                      'r_mm': []})
        d['b_mean_T'].append(mean)
        d['b_max_T'].append(mx)
        d['area_mm2'].append(float(w[m].sum()))
        d['j_a_mm2'].append(abs(float(p['jval'].get(code, 0.0))) / 1e6)
        d['r_mm'].append(float(np.hypot(x[m], y[m]).mean()))

    per_turn = {k: {'b_mean_T': float(np.mean(v['b_mean_T'])),
                    'b_max_T': float(np.max(v['b_max_T'])),
                    'area_mm2': float(np.mean(v['area_mm2'])),
                    'j_a_mm2': float(np.mean(v['j_a_mm2'])),
                    'r_mean_mm': float(np.mean(v['r_mm'])),
                    'n_slots': len(v['b_mean_T'])}
                for k, v in sorted(turns.items(), key=lambda t: int(t[0]))}

    b_cu = [v['b_mean_T'] for v in per_turn.values()]
    return {
        'source': os.path.basename(p['path']),
        'n_turns': int(n_turn),
        'airgap': airgap,
        'per_turn': per_turn,
        'b_cu_mean_T': float(np.mean(b_cu)) if b_cu else float('nan'),
        'b_cu_max_turn_T': float(np.max(b_cu)) if b_cu else float('nan'),
        'j_phase_a_mm2': sorted({round(abs(v) / 1e6, 2)
                                 for c, v in p['jval'].items()
                                 if _TURN_RE.match(p['names'].get(c, ''))
                                 and abs(v) > 0}),
    }


def compare_models(paths: Dict[str, str],
                   out_json: Optional[str] = None) -> dict:
    """모델별 지표를 모아 비율까지 계산한다 (Ref 기준)."""
    res = {k: loading_metrics(parse_mes_txt(v)) for k, v in paths.items()}
    out = {'models': res}
    if 'Ref' in res:
        ref = res['Ref']
        out['ratio_to_ref'] = {
            k: {'b_g': v['airgap']['b_mean_T'] / ref['airgap']['b_mean_T'],
                'b_cu': v['b_cu_mean_T'] / ref['b_cu_mean_T']}
            for k, v in res.items()}
    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
        with open(out_json, 'w', encoding='utf-8') as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
    return out
