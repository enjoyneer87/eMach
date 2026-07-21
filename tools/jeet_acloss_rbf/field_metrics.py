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

__all__ = ["parse_mes_txt", "iter_mes_blocks", "region_summary",
           "loading_metrics", "compare_models", "hybrid_je_reference",
           "hybrid_je_at_points", "slot_conductor_codes"]

_AIRGAP_RE = re.compile(r"^a\d+$", re.I)
# Motor-CAD 명명은 Turn_<층>_<슬롯> 이다. 첫 인덱스가 반경방향 층으로,
# 층 1이 슬롯 개구부(공극)에 가장 가깝고 층 N이 슬롯 바닥이다. 같은 층의
# 슬롯들은 반경이 동일하고 상(phase)만 다르다.
_TURN_RE = re.compile(r"^Turn_(\d+)_(\d+)$", re.I)
_LAYER_GROUP = 1
# 실시간 COM export 는 대신 'ArmatureSlot<슬롯문자><층번호>' 를 쓴다
# (아카이브된 .mes 는 Turn_<층>_<슬롯>). 층 순서도 반대다: 여기서는
# 문자가 층이고 숫자가 슬롯이며, 실측 확인 결과 문자 A(최대 r, 슬롯
# 바닥) -> F(최소 r, 슬롯 개구부)로 Turn_ 표기의 층6->층1과 반대 순.
_TURN_RE2 = re.compile(r"^ArmatureSlot([A-Za-z]+)(\d+)$", re.I)


def _is_conductor_region(name: str) -> bool:
    return bool(_TURN_RE.match(name) or _TURN_RE2.match(name))


def slot_conductor_codes(p: dict, slot_id: int):
    """지정 슬롯(slot_id) 하나의 도체 RegCode 집합을 두 명명 규칙 모두에서 찾는다.

    아카이브 .mes(``Turn_<층>_<슬롯>``)와 실시간 COM export
    (``ArmatureSlot<층문자><슬롯>``) 양쪽 다 두 번째 그룹이 슬롯번호이다.
    """
    codes = set()
    for code, name in p['names'].items():
        for rx in (_TURN_RE, _TURN_RE2):
            m = rx.match(name)
            if m and int(m.group(2)) == slot_id:
                codes.add(code)
                break
    return codes


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


def _locate_blocks(lines):
    """파일 전체를 한 번 훑어 Solution 블록별 표 위치를 색인한다.

    반환: [{'rotate_deg':.., 'tables': {'ElementsTable': (start,n), ...}}, ...]
    RegionsTable 은 보통 최초 블록에만 있으므로 전역으로 한 번만 찾는다.
    """
    blocks = []
    cur = None
    regions_tbl = None
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*\d+\s+Solution\s+\d+(.*)$", ln)
        if m:
            if cur is not None:
                blocks.append(cur)
            deg_m = re.search(r"Rotate Step\s*(-?[0-9.]+)", m.group(1))
            cur = {'rotate_deg': float(deg_m.group(1)) if deg_m else 0.0,
                   'tables': {}}
            continue
        mt = re.match(r"^\s*\d+\s+(\d+)\s+(\w+Table)", ln)
        if mt:
            n, name = int(mt.group(1)), mt.group(2)
            if cur is not None and name not in cur['tables']:
                cur['tables'][name] = (i + 1, n)
            if name == 'RegionsTable' and regions_tbl is None:
                regions_tbl = (i + 1, n)
    if cur is not None:
        blocks.append(cur)
    return blocks, regions_tbl


def _parse_regions(lines, regions_tbl):
    names: Dict[int, str] = {}
    jval: Dict[int, float] = {}
    sigma: Dict[int, float] = {}
    if not regions_tbl:
        return names, jval, sigma
    rs, n_rg = regions_tbl
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
    return names, jval, sigma


def _build_block_dict(lines, block, names, jval, sigma, path,
                      n_solution_blocks):
    el_start, n_el = block['tables']['ElementsTable']
    nd_start, n_nd = block['tables']['NodesTable']
    elems, _ = _rows(lines, el_start, n_el)
    nodes, _ = _rows(lines, nd_start, n_nd)
    E = np.asarray(elems, float)
    N = np.asarray(nodes, float)

    node_xy = np.full((int(N[:, 0].max()) + 1, 2), np.nan)
    node_xy[N[:, 0].astype(int)] = N[:, 1:3]

    tri = E[:, 1:4].astype(int)
    P = node_xy[tri]                                   # (n_el, 3, 2)
    cx, cy = P[:, :, 0].mean(1), P[:, :, 1].mean(1)
    area = 0.5 * np.abs(
        (P[:, 1, 0] - P[:, 0, 0]) * (P[:, 2, 1] - P[:, 0, 1])
        - (P[:, 2, 0] - P[:, 0, 0]) * (P[:, 1, 1] - P[:, 0, 1]))

    has_je = E.shape[1] > 9
    return {
        'reg': E[:, 4].astype(int), 'bx': E[:, 5], 'by': E[:, 6],
        'a_wbm': E[:, 7], 'j_am2': E[:, 8],
        'je_am2': E[:, 9] if has_je else np.zeros(len(E)),
        'x_mm': cx, 'y_mm': cy, 'area_mm2': area,
        'b_T': np.hypot(E[:, 5], E[:, 6]),
        'names': names, 'jval': jval, 'sigma': sigma, 'path': path,
        'n_solution_blocks': n_solution_blocks,
        'rotate_deg': block['rotate_deg'],
        'tri': tri, 'node_xy': node_xy,          # 메시 연결정보(등고선용)
    }


def parse_mes_txt(path: str, block: int = 1) -> dict:
    """세 표를 모두 읽어 요소 중심좌표·면적까지 계산해 돌려준다.

    ``block`` (1-based) 로 특정 Solution 블록을 선택한다. 전 주기 export
    (128 블록)에서 블록 1 = Rotate Step 0 은 와전류가 아직 발달하지 않아
    Je 가 항상 0이다 --- 실제 유도 전류 분포가 필요하면 block>=2 를 쓸 것.
    """
    with open(path, encoding='utf-8', errors='ignore') as fh:
        lines = fh.readlines()
    blocks, regions_tbl = _locate_blocks(lines)
    blk = blocks[block - 1]
    # 블록마다 자기 RegionsTable 을 쓴다 --- 첫 블록 것을 재사용하면
    # jval/sigma 가 블록 1 값에 고정된다(회전각마다 상전류가 달라지므로
    # 128블록 중 절반에서 부호까지 틀어진다).
    names, jval, sigma = _parse_regions(
        lines, blk['tables'].get('RegionsTable', regions_tbl))
    return _build_block_dict(lines, blk, names, jval, sigma,
                             path, len(blocks))


def iter_mes_blocks(path: str):
    """전 주기 export 의 Solution 블록을 순서대로 순회한다.

    ``for step, p in iter_mes_blocks(path):`` 형태로 쓰며, ``p`` 는
    ``parse_mes_txt`` 와 동일한 구조(1-based ``step`` 이 곧 블록 번호).
    큰 파일(전 주기 export 시 수백 MB)을 한 번만 읽고 블록별로 지연 파싱한다.
    """
    with open(path, encoding='utf-8', errors='ignore') as fh:
        lines = fh.readlines()
    blocks, regions_tbl = _locate_blocks(lines)
    for i, blk in enumerate(blocks):
        names, jval, sigma = _parse_regions(
            lines, blk['tables'].get('RegionsTable', regions_tbl))
        yield i + 1, _build_block_dict(lines, blk, names, jval, sigma,
                                       path, len(blocks))


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


def maxwell_torque(p: dict, l_stack_mm: float = 150.0,
                   n_sectors: Optional[int] = None) -> dict:
    """공극 Maxwell 응력 적분으로 전자기 토크를 산출한다.

    반경 r 의 원통면에 대한 응력 토크를 공극 두께에 걸쳐 평균한 형태

        T = l / (mu0 * dr) * \\int_A r * B_r * B_theta dA

    를 쓴다. 단일 원주만 쓰는 것보다 메시 이산화에 둔감하다. ``n_sectors``
    는 전체 원주 대비 모델 배수로, 생략하면 고정자 영역의 각도 범위에서
    자동 추정한다(예: 45도 섹터 -> 8).
    """
    MU0 = 4e-7 * np.pi
    x, y = p['x_mm'], p['y_mm']
    r = np.hypot(x, y)
    gap = [c for c, n in p['names'].items() if _AIRGAP_RE.match(n)]
    m = np.isin(p['reg'], gap)
    if not m.any():
        return {'torque_Nm': float('nan')}

    if n_sectors is None:
        st = [c for c, n in p['names'].items()
              if n.strip().lower() == 'stator']
        span = 360.0
        if st:
            ms = p['reg'] == st[0]
            th = np.degrees(np.arctan2(y[ms], x[ms]))
            span = float(th.max() - th.min())
        n_sectors = int(round(360.0 / span)) if span > 0 else 1

    # 공극은 여러 개의 얇은 층(a1..aN)으로 나뉘고 층마다 정렬 기준(고정자/
    # 회전자)이 달라, 층 하나하나가 독립적인 토크 추정치를 준다. 층의
    # 반경 두께는 요소 중심 퍼짐이 아니라 면적/(각도폭*반경)으로 구해야
    # 한다 --- 중심 퍼짐은 요소 크기만큼 과소평가되어 토크를 부풀린다.
    per_layer, torques = {}, []
    for code in gap:
        ml = p['reg'] == code
        if ml.sum() < 3:
            continue
        rl = r[ml]
        ct, st_ = x[ml] / rl, y[ml] / rl
        br = p['bx'][ml] * ct + p['by'][ml] * st_
        bt = -p['bx'][ml] * st_ + p['by'][ml] * ct
        area = p['area_mm2'][ml] * 1e-6
        span = np.radians(float(np.ptp(np.degrees(
            np.arctan2(y[ml], x[ml])))))
        rmean = float(rl.mean()) * 1e-3
        if span <= 0 or rmean <= 0:
            continue
        h_eff = float(area.sum()) / (span * rmean)      # 층 두께 [m]
        t = (n_sectors * (l_stack_mm * 1e-3) / (MU0 * h_eff)
             * float(np.sum(rl * 1e-3 * br * bt * area)))
        per_layer[p['names'][code]] = {'torque_Nm': t,
                                       'h_eff_mm': h_eff * 1e3}
        torques.append(t)

    if not torques:
        return {'torque_Nm': float('nan')}
    t = float(np.mean(torques))
    spread = (float(np.ptp(torques)) / abs(t) * 100.0) if t else float('nan')
    return {'torque_Nm': t, 'layer_spread_pct': spread,
            'per_layer': per_layer, 'n_sectors': int(n_sectors),
            'annulus_r_mm': [float(r[m].min()), float(r[m].max())],
            'l_stack_mm': float(l_stack_mm)}


_MOT_KEYS = ('WindingLayers', 'ParallelPaths', 'RMSCurrent',
             'RMSCurrentDensity', 'Copper_Width', 'Copper_Height',
             'Resistance_MotorLAB', 'EndWindingResistance_Lab',
             'Stator_Lam_Dia', 'Stator_Lam_Length', 'Pole_Number',
             'Slot_Number', 'ArmatureConductor_Temperature', 'DCBusVoltage')


def read_mot(path: str, keys=_MOT_KEYS) -> dict:
    """Motor-CAD ``.mot`` (INI 형식 텍스트)에서 권선·저항 값을 읽는다.

    Motor-CAD 를 띄우지 않고 파일만으로 읽으므로 COM 이 필요 없다.
    ``ResistanceActivePart`` 는 Motor-CAD 자체 정의와 같이 전체 상저항에서
    엔드와인딩 몫을 뺀 값이다(getMcadMachineDataFromMotFile.m 와 동일).

    주의: 파생 출력(``RMSCurrentDensity``, ``Resistance_MotorLAB``)은
    Motor-CAD 가 재계산할 때만 갱신되므로, 턴수만 바꾸고 재계산하지 않은
    파일에서는 옛 값이 남아 있을 수 있다. 도체 면적으로 교차 확인할 것.
    """
    with open(path, encoding='latin-1', errors='ignore') as fh:
        txt = fh.read()
    out: Dict[str, object] = {'path': path}
    for k in keys:
        m = re.search(rf'^\s*{k}\s*=\s*(.+)$', txt, re.M | re.I)
        if not m:
            continue
        v = m.group(1).strip()
        try:
            out[k] = float(v)
        except ValueError:
            out[k] = v
    rt = out.get('Resistance_MotorLAB')
    re_ = out.get('EndWindingResistance_Lab')
    if isinstance(rt, float) and isinstance(re_, float):
        out['ResistanceActivePart'] = rt - re_
        out['R_active_mOhm'] = (rt - re_) * 1e3
        out['R_end_mOhm'] = re_ * 1e3
        out['R_total_mOhm'] = rt * 1e3
    w, h = out.get('Copper_Width'), out.get('Copper_Height')
    if isinstance(w, float) and isinstance(h, float):
        out['A_conductor_mm2_rect'] = w * h
    return out


def winding_losses(mot: dict, i_rms_a: Optional[float] = None) -> dict:
    """3상 DC 동손 P = 3 I^2 R (활성부/엔드/합계)."""
    i = float(i_rms_a if i_rms_a is not None
              else mot.get('RMSCurrent', float('nan')))
    r_a = mot.get('ResistanceActivePart')
    r_e = mot.get('EndWindingResistance_Lab')
    r_t = mot.get('Resistance_MotorLAB')
    f = 3.0 * i * i
    return {'i_rms_a': i,
            'p_active_kW': f * r_a / 1e3 if r_a else float('nan'),
            'p_end_kW': f * r_e / 1e3 if r_e else float('nan'),
            'p_total_kW': f * r_t / 1e3 if r_t else float('nan')}


def _tangential_b(p: dict) -> np.ndarray:
    """슬롯 확산 문제를 구동하는 **부호 있는** 접선(원주방향) B 성분.

    ``|B|`` 를 쓰면 안 된다 --- 슬롯 누설 접선장은 스택을 가로지르며
    부호가 바뀌므로(공극쪽 음, 슬롯바닥쪽 양) 크기만 취하면 층별 기울기
    dH/dx 의 부호와 크기가 모두 틀어진다. 또한 슬롯바닥에서는 배후철심
    때문에 반경 성분이 커서 ``|B|`` 가 크게 부풀려진다.
    """
    r = np.hypot(p['x_mm'], p['y_mm'])
    return (-p['y_mm'] * p['bx'] + p['x_mm'] * p['by']) / r


def _conductor_layers(p: dict, codes, mu0: float,
                      face_frac: float = 0.2,
                      thickness_mm: Optional[float] = None) -> list:
    """도체층별 1-D 경계값 문제의 기하·경계 H 를 모은다.

    경계 H 는 각 면에서 두께의 ``face_frac`` 이내 요소들의 평균으로
    잡는다 --- 반경 최소/최대 **단일 요소**를 쓰면 슬롯바닥 층에서
    철심에 접한 요소 하나가 B 를 2배 이상으로 끌어올려 그 층에만 거대한
    가짜 기울기가 생긴다(실제로 겪음).

    층의 반경 범위는 **절점(node) 좌표**로 잡는다. 요소 중심 퍼짐을 쓰면
    바깥 요소 반개씩이 빠져 두께가 16% 과소평가된다(TS-FEA 기준 1.416 mm
    vs 절점 1.699 mm, `.mot` 의 Copper_Height 1.686 mm 가 정답).
    이는 공극 층에서 이미 겪은 것과 같은 함정이다(REPRODUCE.md 주의 3).

    ``thickness_mm`` 을 주면 확산 두께를 그 값으로 강제한다. **MS-FEA 의
    `ArmatureSlot*` 영역은 도체와 함침을 합친 셀**이라(면적 9.685 vs
    TS 6.180 mm^2) 절점 범위조차 2.127 mm 로 실제 구리 1.686 mm 보다
    26% 크다. 와전류는 구리에서만 흐르므로 MS 를 소스로 쓸 땐 `.mot` 의
    Copper_Height 를 넘겨 주는 편이 옳다.
    """
    nd = p['node_xy']
    r_node = np.hypot(nd[:, 0], nd[:, 1])
    r = np.hypot(p['x_mm'], p['y_mm'])
    btan = _tangential_b(p)
    layers = []
    for code in codes:
        m = p['reg'] == code
        if m.sum() < 3:
            continue
        ids = np.unique(p['tri'][m].ravel())
        r_lo, r_hi = float(r_node[ids].min()), float(r_node[ids].max())
        if r_hi <= r_lo:
            continue
        span = r_hi - r_lo
        t = (span if thickness_mm is None else float(thickness_mm)) * 1e-3
        rr, bb = r[m], btan[m]
        near_lo = rr <= r_lo + face_frac * span
        near_hi = rr >= r_hi - face_frac * span
        if not near_lo.any() or not near_hi.any():
            continue
        layers.append({'code': code, 'r_lo': r_lo, 'r_hi': r_hi, 't': t,
                       'span_mm': span,
                       'h0': float(bb[near_lo].mean()) / mu0,
                       'ht': float(bb[near_hi].mean()) / mu0})
    layers.sort(key=lambda d: d['r_lo'])
    return layers


def _layer_je(layer: dict, xl: np.ndarray, k: complex,
              signed: bool) -> np.ndarray:
    """한 층의 국소좌표 ``xl`` [m] 에서 **유도** 와전류밀도를 평가.

    닫힌형 해 J(x)=dH/dx 는 수송(균일) 성분까지 포함한다 --- 그 층 평균
    ``(Ht-H0)/t`` 가 곧 바에 흐르는 전송 전류밀도다. TS-FEA 의 ``Je``
    열은 유도 성분만 담고 있어 층 평균이 0 이므로(실측 확인), 비교
    가능하도록 같은 평균을 빼서 돌려준다.
    """
    t, h0, ht = layer['t'], layer['h0'], layer['ht']
    j = k * (-h0 * np.cosh(k * (t - xl))
             + ht * np.cosh(k * xl)) / np.sinh(k * t)
    j = j - (ht - h0) / t
    return j.real if signed else np.abs(j)


def hybrid_je_reference(p: dict, freq_hz: float, sigma: float = 4.709e7,
                        mu0: float = 4e-7 * np.pi,
                        signed: bool = False,
                        thickness_mm: Optional[float] = None) -> np.ndarray:
    """Hybrid(MS-FEA) 요소별 B 로부터 \"참고용\" 근접 와전류밀도 Je 를 재구성.

    **주의**: TS-FEA 의 Je 는 실제로 풀린 값이고, 이 함수가 만드는 값은
    Hybrid 방법이 가정하는 1-D Dowell/Ferreira 근접 확산해(Appendix,
    eq. diffusion/P_rect)를 각 도체에 적용해 \"만약 국소적으로 이
    닫힌형 해가 성립한다면\"이라는 가정 하에 역산한 근사값이다 --- 실제
    FEA 출력이 아니라 이론적 참고선(reference)이다.

    각 도체(층)의 두 경계면에서 측정된 MS-FEA **접선** B 를 그 경계의 H 로
    삼아 1-D 확산 방정식의 경계값 문제를 풀고 (Appendix 식 (diffusion)의
    일반해에 두 면 경계조건을 대입),

        H(x) = [H0 sinh(k(t-x)) + Ht sinh(kx)] / sinh(kt)
        J(x) = dH/dx,   k = (1+j)/delta,  delta = 1/sqrt(0.5 w mu0 sigma)

    도체 내 각 요소의 국소 좌표 x(0=안쪽 경계, t=바깥쪽 경계, t=도체
    반경방향 두께)에서 J(x) 를 평가하고, 층 평균(=수송 전류 성분)을 빼서
    **유도 성분만** 요소별로 돌려준다 --- TS-FEA 의 Je 열과 같은 정의라
    그대로 비교할 수 있다. 경계 H 와 평균 제거의 근거는
    ``_tangential_b`` / ``_conductor_layers`` / ``_layer_je`` 참조.

    ``signed=False``(기본): 크기 |J(x)| 반환(총손실 비교용).
    ``signed=True``: 등고선 시각화(Fig 2 style)용으로 특정 기준 위상
    (t=0, 즉 Re[J(x)])에서의 부호 있는 값을 반환 --- 위상 기준이 임의라는
    점에서 이 자체가 "참고용" 재구성임을 다시 한 번 유의할 것.
    """
    reg = p['reg']
    r = np.hypot(p['x_mm'], p['y_mm'])

    omega = 2.0 * np.pi * freq_hz
    delta = 1.0 / np.sqrt(0.5 * omega * mu0 * sigma)          # [m]
    k = (1.0 + 1.0j) / delta

    codes = [c for c, name in p['names'].items()
             if _is_conductor_region(name)]
    je = np.zeros(len(reg))
    for layer in _conductor_layers(p, codes, mu0,
                                   thickness_mm=thickness_mm):
        m = reg == layer['code']
        # 영역 내 반경 위치를 비율로 잡아 확산 두께에 대응시킨다
        frac = np.clip((r[m] - layer['r_lo']) / layer['span_mm'], 0.0, 1.0)
        je[m] = _layer_je(layer, frac * layer['t'], k, signed)
    return je


def hybrid_je_at_points(p_source: dict, query_xy: np.ndarray,
                        freq_hz: float, slot_id: Optional[int] = None,
                        sigma: float = 4.709e7,
                        mu0: float = 4e-7 * np.pi,
                        signed: bool = False,
                        thickness_mm: Optional[float] = None) -> np.ndarray:
    """Hybrid B 로부터, **임의의 좌표**에서 참고용 근접 Je 를 평가한다.

    ``hybrid_je_reference`` 와 **같은 층별(도체별) 1-D 경계값 문제**를
    풀되, 해를 ``p_source`` 자신의 요소가 아니라 ``query_xy`` 로 주어진
    임의의 좌표에서 평가한다. 예를 들어 다른 데이터셋(예: TS-FEA)의 도체
    요소 좌표를 넘기면, Hybrid 의 B 로 재구성한 값을 TS-FEA 의 실제(더
    촘촘하거나 비이상화된) 메시 형상 위에 그대로 겹쳐 그릴 수 있다.

    각 질의점은 반경으로 소속 도체층을 찾고(밴드 포함 우선, 층간 절연
    간극이나 밴드 밖이면 가장 가까운 층 중심), 그 층의 국소 좌표
    x(0=층의 안쪽 면, t=바깥쪽 면)에서 J(x) 를 평가한다.

    **층별로 푸는 이유**: 도체는 서로 절연되어 있어 와전류가 각 바
    내부에서 순환한다. 스택 전체(여기서는 약 11.6 mm = 5delta)를 하나의
    슬랩으로 잡으면 양쪽 끝면에만 부호가 반대인 큰 J 가 생기고 가운데가
    0 이 되어, 공극쪽 쏠림이 아니라 "위아래가 뒤집힌" 그림이 나온다
    (실제로 겪음 --- REPRODUCE.md 주의사항 12).

    ``p_source`` : 경계 B 를 제공하는 Hybrid(MS-FEA) 블록 딕셔너리
        (``parse_mes_txt``/``iter_mes_blocks`` 반환값).
    ``query_xy`` : (N, 2) 배열, [mm], ``p_source`` 와 같은 전역 좌표계.
        원점 기준 반경(r)만 쓰므로 어느 데이터셋에서 왔는지는 무관하다.
    ``slot_id`` : 경계 B 를 구할 슬롯 번호(``slot_conductor_codes`` 로
        선택). 두 데이터셋의 슬롯 번호가 물리적으로 같은 위치인지는
        미리 각도로 확인해 둘 것(REPRODUCE.md 참조).

    Returns ``query_xy`` 와 같은 길이의 배열.
    """
    reg = p_source['reg']
    if slot_id is not None:
        codes = sorted(slot_conductor_codes(p_source, slot_id))
    else:
        names = p_source['names']
        codes = sorted(c for c in np.unique(reg)
                       if _is_conductor_region(names.get(c, '')))
    if not codes:
        raise ValueError('p_source 에서 도체 요소를 찾지 못함'
                         ' (slot_id 확인)')

    layers = _conductor_layers(p_source, codes, mu0,
                               thickness_mm=thickness_mm)
    if not layers:
        raise ValueError('유효한 도체층이 없음 (요소 수/두께 확인)')

    omega = 2.0 * np.pi * freq_hz
    delta = 1.0 / np.sqrt(0.5 * omega * mu0 * sigma)
    k = (1.0 + 1.0j) / delta

    centers = np.array([0.5 * (d['r_lo'] + d['r_hi']) for d in layers])
    r_q = np.hypot(np.asarray(query_xy)[:, 0], np.asarray(query_xy)[:, 1])
    # 밴드 포함 우선, 간극·밴드 밖은 가장 가까운 층 중심으로 배정
    owner = np.argmin(np.abs(r_q[:, None] - centers[None, :]), axis=1)
    for i, d in enumerate(layers):
        owner[(r_q >= d['r_lo']) & (r_q <= d['r_hi'])] = i

    out = np.zeros(len(r_q))
    for i, d in enumerate(layers):
        sel = owner == i
        if not sel.any():
            continue
        frac = np.clip((r_q[sel] - d['r_lo']) / d['span_mm'], 0.0, 1.0)
        out[sel] = _layer_je(d, frac * d['t'], k, signed)
    return out


def block_angles(path: str) -> dict:
    """블록별 **누적** 회전각 [deg] 과 시각 [s] 을 뽑는다 (가볍다).

    주의: 헤더의 ``Rotate Step`` 은 누적각이 아니라 **스텝당 증분**이며
    모든 블록에서 같은 값이다(예: Ref/SC TS -0.7031, SC Hybrid -2.0000).
    이걸 누적각으로 오해하면 두 파일의 각도 격자를 잘못 비교하게 된다
    (실제로 겪음). 누적각 = (블록번호-1) x 증분 으로 만든다. ``Time`` 이
    있으면 그대로 쓰며, 이쪽이 더 신뢰할 만하다.

    Returns ``{'deg': ndarray, 'sec': ndarray, 'step_deg': float}``.
    """
    steps, times = [], []
    with open(path, encoding='utf-8', errors='ignore') as fh:
        for ln in fh:
            m = re.match(r"^\s*\d+\s+Solution\s+\d+(.*)$", ln)
            if not m:
                continue
            body = m.group(1)
            d = re.search(r"Rotate Step\s*(-?[0-9.eE+]+)", body)
            t = re.search(r"Time\s+(-?[0-9.eE+]+)\s*\[s\]", body)
            steps.append(float(d.group(1)) if d else 0.0)
            times.append(float(t.group(1)) if t else np.nan)
    steps = np.asarray(steps, float)
    times = np.asarray(times, float)
    # 증분은 블록 2 이후가 대표값 (블록 1 은 0)
    inc = float(steps[1]) if steps.size > 1 else 0.0
    deg = np.arange(steps.size) * inc
    if np.isfinite(times[1:]).all() and times.size > 1:
        dt = float(times[1])
        sec = np.arange(times.size) * dt
    else:
        sec = np.full(steps.size, np.nan)
    return {'deg': deg, 'sec': sec, 'step_deg': inc}


def match_blocks_by_angle(path_a: str, path_b: str,
                          tol_deg: float = 0.05):
    """두 export 의 블록을 **누적 회전각**으로 짝짓는다.

    두 해석이 같은 스텝 격자로 풀렸다는 보장이 없다 --- 실제로 SC 의
    속도스윕 백업본은 TS 가 0.7031 deg/step(128블록), Hybrid 가
    2.0 deg/step(47블록)이라 0 deg 외에는 겹치는 각도가 없었다. 그대로
    ``zip`` 하면 다른 회전자 위치를 짝지어 조용히 틀린 비교가 된다
    (주의사항 7의 변종).

    각 b 블록에 대해 누적각이 가장 가까운 a 블록을 찾고, 차이가
    ``tol_deg`` 이내인 쌍만 돌려준다. 격자가 같으면 전부 정확히 매칭된다.

    Returns ``[(ia, ib, deg_a, deg_b), ...]`` (1-based 블록 번호).
    """
    A, B = block_angles(path_a), block_angles(path_b)
    aa, ab = A['deg'], B['deg']
    pairs = []
    for jb, angb in enumerate(ab):
        ja = int(np.argmin(np.abs(aa - angb)))
        if abs(aa[ja] - angb) <= tol_deg:
            pairs.append((ja + 1, jb + 1, float(aa[ja]), float(angb)))
    return pairs


def slot_mean_angle(p: dict, slot_id: int) -> float:
    """슬롯 도체 전체의 평균 각도 [rad] --- 막대별 로컬 프레임의 공통 기준.

    ``conductor_je_2d`` / ``conductor_je_strips`` 에 ``angle_rad`` 로
    넘기면 모든 막대가 같은 방향으로 정렬돼 슬롯 축과 어긋나지 않는다.
    """
    codes = list(slot_conductor_codes(p, slot_id))
    m = np.isin(p['reg'], codes)
    return float(np.arctan2(p['y_mm'][m].mean(), p['x_mm'][m].mean()))


def conductor_je_strips(p_source: dict, code: int, freq_hz: float,
                        width_mm: float, height_mm: float,
                        n_strips: int = 20, n_radial: int = 26,
                        sigma: float = 4.709e7,
                        mu0: float = 4e-7 * np.pi,
                        angle_rad: Optional[float] = None) -> dict:
    """도체를 접선 방향 **스트립**으로 나눠 스트립마다 1-D 확산을 푼다.

    Motor-CAD 의 FEA Paths 화면을 보면 슬롯 영역에 막대당 ~20개의
    샘플링 라인이 그어져 있다 --- 실제 하이브리드는 막대 하나에서 B 를
    한 쌍이 아니라 **여러 위치에서** 뽑아 쓴다. 이 함수는 그 방식을
    흉내 낸다: 각 스트립의 안/바깥 반경면에서 접선 B 를 보간해 그
    스트립만의 1-D 경계값 문제를 풀고, 반경 방향으로 쌓는다.

    ``hybrid_je_at_points`` (막대당 경계 2점) 와 ``conductor_je_2d``
    (완전 2-D) 사이의 중간 단계다. 셋을 나란히 놓으면 크기 과소평가가
    **커널 차원수** 때문인지 **샘플링 밀도** 때문인지 분리할 수 있다.

    수송 성분은 스트립별이 아니라 **막대 전체 평균**으로 뺀다 ---
    TS-FEA 의 ``Je`` 열이 막대 단위로 평균 0 이기 때문.

    Returns ``conductor_je_2d`` 와 같은 형식 ``{'je', 'x_mm', 'y_mm'}``
    (je 는 (n_radial, n_strips) 복소 배열).
    """
    from scipy.interpolate import griddata as _griddata

    m = p_source['reg'] == code
    if not m.any():
        raise ValueError('region code %r 없음' % code)
    x, y = p_source['x_mm'][m], p_source['y_mm'][m]
    # 막대마다 자기 무게중심 각도를 쓰면 슬롯 축과 어긋나 사각형이 각자
    # 기울어진다(공극쪽 바는 개구부에 잘려 무게중심이 밀림 --- 실측
    # 편차 0.138 deg = r 84 mm 에서 0.2 mm). 슬롯 공통 각도를 넘길 것.
    ang = (np.arctan2(y.mean(), x.mean()) if angle_rad is None
           else float(angle_rad))
    c, s = np.cos(-ang), np.sin(-ang)
    R = np.array([[c, -s], [s, c]])
    # 격자는 막대의 **로컬 좌표 실제 중심**에 놓아야 한다. 접선 0(슬롯
    # 중심선)에 고정하면 중심선에서 벗어난 막대가 통째로 어긋난다 ---
    # 공극쪽 바는 개구부에 잘려 접선 중심이 -0.119 mm 다(실제로 겪음).
    xy_loc = np.column_stack([x, y]) @ R.T
    r_c = float(xy_loc[:, 0].mean())
    t_c = float(xy_loc[:, 1].mean())

    rr_off = np.linspace(-height_mm / 2, height_mm / 2, n_radial)
    tt_c = np.linspace(-width_mm / 2, width_mm / 2, n_strips)
    RR, TT = np.meshgrid(rr_off, tt_c, indexing='ij')
    loc = np.column_stack([(RR + r_c).ravel(),
                           (TT + t_c).ravel()])
    glob = loc @ R

    # 스트립 양 면(안/바깥 반경)에서 접선 B 를 보간
    face_lo = np.column_stack([np.full(n_strips, r_c - height_mm / 2),
                               tt_c + t_c]) @ R
    face_hi = np.column_stack([np.full(n_strips, r_c + height_mm / 2),
                               tt_c + t_c]) @ R
    near = np.hypot(p_source['x_mm'] - glob[:, 0].mean(),
                    p_source['y_mm'] - glob[:, 1].mean()) < 6.0
    pts = np.column_stack([p_source['x_mm'][near], p_source['y_mm'][near]])
    btan = _tangential_b(p_source)[near]

    def samp(q):
        v = _griddata(pts, btan, q, method='linear')
        if np.isnan(v).any():
            v = np.where(np.isnan(v),
                         _griddata(pts, btan, q, method='nearest'), v)
        return v

    h0 = samp(face_lo) / mu0
    ht = samp(face_hi) / mu0

    omega = 2.0 * np.pi * freq_hz
    delta = 1.0 / np.sqrt(0.5 * omega * mu0 * sigma)
    k = (1.0 + 1.0j) / delta
    t = height_mm * 1e-3
    xl = (rr_off + height_mm / 2) * 1e-3            # 0..t
    skt = np.sinh(k * t)
    # (n_radial, n_strips)
    j = (k * (-h0[None, :] * np.cosh(k * (t - xl[:, None]))
              + ht[None, :] * np.cosh(k * xl[:, None])) / skt)
    j = j - j.mean()                                # 막대 전체 수송 제거
    return {'je': j,
            'x_mm': glob[:, 0].reshape(RR.shape),
            'y_mm': glob[:, 1].reshape(RR.shape),
            'n_strips': n_strips}


def conductor_je_2d(p_source: dict, code: int, freq_hz: float,
                    width_mm: float, height_mm: float,
                    i_net_a: Optional[float] = None,
                    sigma: float = 4.709e7, mu0: float = 4e-7 * np.pi,
                    nx: int = 40, ny: int = 26,
                    angle_rad: Optional[float] = None) -> dict:
    """도체 단면 하나를 **2-D** 확산 방정식으로 풀어 유도 Je 를 구한다.

    ``hybrid_je_at_points`` 의 1-D 커널(반경 방향만)과 달리 접선 방향까지
    포함한다. 여기(excitation)는 동일하게 **와전류가 없는 MS-FEA 의
    벡터 퍼텐셜** ``a_wbm`` 을 막대 경계에 Dirichlet 조건으로 주므로,
    1-D 대 2-D 를 같은 입력·같은 기준에서 비교할 수 있다:

        (lap - j w mu sigma) A = -mu sigma E0,    A|_bd = A_MS|_bd
        J_z = sigma(-j w A + E0)

    ``E0`` (= V/l, 균일 구동 전계)는 순전류 ``i_net_a`` 를 맞추도록
    결정한다. 선형이므로 동차해와 특수해를 각각 풀어 중첩한다.
    반환 ``je`` 는 층 평균을 뺀 **유도 성분**이라 TS-FEA 의 ``Je`` 열과
    같은 정의다(``_layer_je`` 주석 참조).

    이 함수의 요점(실측): 같은 MS-FEA 여기를 주어도 1-D 는 손실 대리
    지표에서 TS-FEA 보다 약 14배 낮은 반면, 2-D 는 거의 일치한다 --- 즉
    하이브리드의 크기 과소평가는 여기 자계가 틀려서가 아니라 **커널이
    1-D 라서** 생긴다. 자세한 수치는 REPRODUCE.md 주의사항 20.

    Returns ``{'je': (nx,ny) 복소 유도 전류밀도 [A/m^2], 'xy_local',
    'e0'}``.
    """
    import scipy.sparse as _sp
    import scipy.sparse.linalg as _spl
    from scipy.interpolate import griddata as _griddata

    m = p_source['reg'] == code
    if not m.any():
        raise ValueError('region code %r 없음' % code)
    x, y = p_source['x_mm'][m], p_source['y_mm'][m]
    # 막대마다 자기 무게중심 각도를 쓰면 슬롯 축과 어긋나 사각형이 각자
    # 기울어진다(공극쪽 바는 개구부에 잘려 무게중심이 밀림 --- 실측
    # 편차 0.138 deg = r 84 mm 에서 0.2 mm). 슬롯 공통 각도를 넘길 것.
    ang = (np.arctan2(y.mean(), x.mean()) if angle_rad is None
           else float(angle_rad))
    c, s = np.cos(-ang), np.sin(-ang)
    R = np.array([[c, -s], [s, c]])                 # 전역 -> 로컬
    # 격자는 막대의 **로컬 좌표 실제 중심**에 놓아야 한다. 접선 0(슬롯
    # 중심선)에 고정하면 중심선에서 벗어난 막대가 통째로 어긋난다 ---
    # 공극쪽 바는 개구부에 잘려 접선 중심이 -0.119 mm 다(실제로 겪음).
    xy_loc = np.column_stack([x, y]) @ R.T
    r_c = float(xy_loc[:, 0].mean())
    t_c = float(xy_loc[:, 1].mean())

    # 로컬 x = 반경 방향(두께 height_mm), 로컬 y = 접선 방향(폭 width_mm).
    # 두 축을 바꿔 넣으면 막대를 90도 눕힌 채 푸는 셈이 되어 확산 해가
    # 완전히 달라진다(실제로 겪음 --- 얇은 쪽이 delta 를 결정한다).
    rr_off = np.linspace(-height_mm / 2, height_mm / 2, ny)   # 반경
    tt_off = np.linspace(-width_mm / 2, width_mm / 2, nx)     # 접선
    RR, TT = np.meshgrid(rr_off, tt_off, indexing='ij')
    XX, YY = RR, TT
    loc = np.column_stack([(RR + r_c).ravel(),
                           (TT + t_c).ravel()])
    glob = loc @ R                                   # 로컬 -> 전역
    nx, ny = RR.shape                                # (반경, 접선)

    near = np.hypot(p_source['x_mm'] - glob[:, 0].mean(),
                    p_source['y_mm'] - glob[:, 1].mean()) < 6.0
    pts = np.column_stack([p_source['x_mm'][near], p_source['y_mm'][near]])
    a_bc = _griddata(pts, p_source['a_wbm'][near], glob, method='linear')
    if np.isnan(a_bc).any():
        a_bc = np.where(np.isnan(a_bc),
                        _griddata(pts, p_source['a_wbm'][near], glob,
                                  method='nearest'), a_bc)
    a_bc = a_bc.reshape(nx, ny)

    dx = (rr_off[1] - rr_off[0]) * 1e-3          # 반경 방향 간격
    dy = (tt_off[1] - tt_off[0]) * 1e-3          # 접선 방향 간격
    omega = 2.0 * np.pi * freq_hz
    k2 = 1j * omega * mu0 * sigma
    n = nx * ny
    idx = np.arange(n).reshape(nx, ny)
    rows, cols, vals = [], [], []
    rhs_h = np.zeros(n, dtype=complex)
    rhs_p = np.zeros(n, dtype=complex)
    for i in range(nx):
        for j in range(ny):
            q = idx[i, j]
            if i in (0, nx - 1) or j in (0, ny - 1):
                rows.append(q)
                cols.append(q)
                vals.append(1.0)
                rhs_h[q] = a_bc[i, j]
                continue
            rows += [q] * 5
            cols += [q, idx[i - 1, j], idx[i + 1, j],
                     idx[i, j - 1], idx[i, j + 1]]
            vals += [-2 / dx ** 2 - 2 / dy ** 2 - k2,
                     1 / dx ** 2, 1 / dx ** 2, 1 / dy ** 2, 1 / dy ** 2]
            rhs_p[q] = -mu0 * sigma
    M = _sp.csr_matrix((vals, (rows, cols)), shape=(n, n), dtype=complex)
    lu = _spl.splu(M.tocsc())
    a_h = lu.solve(rhs_h).reshape(nx, ny)
    a_p = lu.solve(rhs_p).reshape(nx, ny)

    if i_net_a is None:
        jv = p_source.get('jval', {}).get(code)
        i_net_a = (0.0 if jv is None
                   else float(jv) * width_mm * height_mm * 1e-6)
    cell = dx * dy
    s1 = (-1j * omega * sigma * a_h).sum() * cell
    s2 = (sigma * (1.0 - 1j * omega * a_p)).sum() * cell
    e0 = (i_net_a - s1) / s2
    j_tot = sigma * (-1j * omega * (a_h + e0 * a_p) + e0)
    return {'je': j_tot - j_tot.mean(), 'xy_local': (XX, YY), 'e0': e0,
            'x_mm': glob[:, 0].reshape(nx, ny),
            'y_mm': glob[:, 1].reshape(nx, ny)}


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
