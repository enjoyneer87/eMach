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
    names, jval, sigma = _parse_regions(lines, regions_tbl)
    return _build_block_dict(lines, blocks[block - 1], names, jval, sigma,
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
    names, jval, sigma = _parse_regions(lines, regions_tbl)
    for i, blk in enumerate(blocks):
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


def hybrid_je_reference(p: dict, freq_hz: float, sigma: float = 4.709e7,
                        mu0: float = 4e-7 * np.pi,
                        signed: bool = False) -> np.ndarray:
    """Hybrid(MS-FEA) 요소별 B 로부터 \"참고용\" 근접 와전류밀도 Je 를 재구성.

    **주의**: TS-FEA 의 Je 는 실제로 풀린 값이고, 이 함수가 만드는 값은
    Hybrid 방법이 가정하는 1-D Dowell/Ferreira 근접 확산해(Appendix,
    eq. diffusion/P_rect)를 각 도체에 적용해 \"만약 국소적으로 이
    닫힌형 해가 성립한다면\"이라는 가정 하에 역산한 근사값이다 --- 실제
    FEA 출력이 아니라 이론적 참고선(reference)이다.

    각 도체(층)의 두 경계면(도체 내 r 최소/최대 요소)에서 측정된 MS-FEA
    B 를 그 경계의 접선 H 로 삼아 1-D 확산 방정식의 경계값 문제를 풀고
    (Appendix 식 (diffusion)의 일반해에 두 면 경계조건을 대입),

        H(x) = [H0 sinh(k(t-x)) + Ht sinh(kx)] / sinh(kt)
        J(x) = dH/dx,   k = (1+j)/delta,  delta = 1/sqrt(0.5 w mu0 sigma)

    도체 내 각 요소의 국소 좌표 x(0=안쪽 경계, t=바깥쪽 경계, t=도체
    반경방향 두께)에서 J(x) 를 평가해 요소별로 돌려준다. Hybrid 는
    도체 내부 전류밀도가 균일하다고 가정하므로(이 배열의 DC 성분),
    반환값은 그 위에 얹히는 유도(induced) 성분만을 뜻하며 TS-FEA 의
    Je 열과 같은 정의로 비교할 수 있다.

    ``signed=False``(기본): 크기 |J(x)| 반환(총손실 비교용).
    ``signed=True``: 등고선 시각화(Fig 2 style)용으로 특정 기준 위상
    (t=0, 즉 Re[J(x)])에서의 부호 있는 값을 반환 --- 위상 기준이 임의라는
    점에서 이 자체가 "참고용" 재구성임을 다시 한 번 유의할 것.
    """
    reg, x, y = p['reg'], p['x_mm'], p['y_mm']
    r = np.hypot(x, y)
    bt = np.hypot(p['bx'], p['by'])          # 국소 |B| (경계 접선 성분 근사)

    omega = 2.0 * np.pi * freq_hz
    delta = 1.0 / np.sqrt(0.5 * omega * mu0 * sigma)          # [m]
    k = (1.0 + 1.0j) / delta

    je = np.zeros(len(reg))
    for code, name in p['names'].items():
        if not _is_conductor_region(name):
            continue
        m = reg == code
        if m.sum() < 3:
            continue
        rr = r[m]
        i_lo, i_hi = np.argmin(rr), np.argmax(rr)
        t = (rr.max() - rr.min()) * 1e-3                       # [m]
        if t <= 0:
            continue
        h0 = bt[m][i_lo] / mu0                                  # H = B/mu0
        ht = bt[m][i_hi] / mu0
        xl = (rr - rr.min()) * 1e-3                             # [m], 0..t

        skt = np.sinh(k * t)
        h_of_x = (h0 * np.sinh(k * (t - xl)) + ht * np.sinh(k * xl)) / skt
        # dH/dx (해석적 미분)
        j_of_x = k * (-h0 * np.cosh(k * (t - xl))
                      + ht * np.cosh(k * xl)) / skt
        je[m] = j_of_x.real if signed else np.abs(j_of_x)
    return je


def hybrid_je_at_points(p_source: dict, query_xy: np.ndarray,
                        freq_hz: float, slot_id: Optional[int] = None,
                        sigma: float = 4.709e7,
                        mu0: float = 4e-7 * np.pi,
                        signed: bool = False) -> np.ndarray:
    """Hybrid B 로부터, **임의의 좌표**에서 참고용 근접 Je 를 평가한다.

    ``hybrid_je_reference`` 는 도체 층마다 독립된 얇은 1-D 경계값 문제를
    풀어 *그 데이터셋 자신의* 요소에서만 평가했다. 이 함수는 대신 한
    슬롯의 도체 스택 **전체 반경 두께**를 하나의 확산 슬랩으로 취급해
    경계 조건(안쪽 r_min = 공극쪽, 바깥쪽 r_max = 슬롯바닥쪽)만
    ``p_source`` 에서 구하고, 그 닫힌형 해 J(x) 를 ``query_xy`` 로 주어진
    임의의 좌표에서 평가한다 --- 그 좌표가 ``p_source`` 자신의 요소일
    필요가 없다. 예를 들어 다른 데이터셋(예: TS-FEA)의 도체 요소 좌표를
    넘기면, Hybrid 의 B 로 재구성한 값을 TS-FEA 의 실제(더 촘촘하거나
    비이상화된) 메시 형상 위에 그대로 겹쳐 그릴 수 있다.

    ``p_source`` : 경계 B 를 제공하는 Hybrid(MS-FEA) 블록 딕셔너리
        (``parse_mes_txt``/``iter_mes_blocks`` 반환값). B 는 이 슬롯의
        전체 도체 영역에서 가져오며(``slot_id`` 로 특정 슬롯 한정,
        생략 시 데이터셋에 있는 모든 도체 요소 사용).
    ``query_xy`` : (N, 2) 배열, [mm], ``p_source`` 와 같은 전역 좌표계.
        원점 기준 반경(r)만 쓰므로 어느 데이터셋에서 왔는지는 무관하다.
    ``slot_id`` : 경계 B 를 구할 슬롯 번호(``slot_conductor_codes`` 로
        선택). 두 데이터셋의 슬롯 번호가 물리적으로 같은 위치인지는
        미리 각도로 확인해 둘 것(REPRODUCE.md 참조).

    Returns ``query_xy`` 와 같은 길이의 배열. 경계 밖(r_min~r_max 밖)의
    질의점은 경계값으로 클램프한다(외삽은 cosh 발산 위험이 있어 하지
    않는다).
    """
    reg = p_source['reg']
    x, y = p_source['x_mm'], p_source['y_mm']
    bt = np.hypot(p_source['bx'], p_source['by'])

    if slot_id is not None:
        src_mask = np.isin(reg, list(slot_conductor_codes(p_source, slot_id)))
    else:
        names = p_source['names']
        src_mask = np.array([_is_conductor_region(names.get(c, ''))
                             for c in reg])
    if not src_mask.any():
        raise ValueError('p_source 에서 도체 요소를 찾지 못함'
                         ' (slot_id 확인)')

    r_src = np.hypot(x[src_mask], y[src_mask])
    i_lo, i_hi = np.argmin(r_src), np.argmax(r_src)
    r0, r1 = float(r_src[i_lo]), float(r_src[i_hi])
    t = (r1 - r0) * 1e-3                                    # [m]
    if t <= 0:
        raise ValueError('반경 방향 두께가 0 이하 (r1<=r0)')
    h0 = bt[src_mask][i_lo] / mu0
    ht = bt[src_mask][i_hi] / mu0

    omega = 2.0 * np.pi * freq_hz
    delta = 1.0 / np.sqrt(0.5 * omega * mu0 * sigma)
    k = (1.0 + 1.0j) / delta
    skt = np.sinh(k * t)

    r_q = np.hypot(np.asarray(query_xy)[:, 0], np.asarray(query_xy)[:, 1])
    xl = np.clip((r_q - r0) * 1e-3, 0.0, t)                  # [m], 0..t

    j_of_x = k * (-h0 * np.cosh(k * (t - xl)) + ht * np.cosh(k * xl)) / skt
    return j_of_x.real if signed else np.abs(j_of_x)


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
