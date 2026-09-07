# -*- coding: utf-8 -*-
"""jeet_map_loader.py -- JEET AC-loss map reader for the e10 thermal study (D1/D2).

역할
----
`mlxperPJT/JEET/map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary.json` (240 records,
repo 안에 커밋되어 있음) 을 읽어 D1/D2 MAPDL 드라이버가 필요로 하는 손실 벡터를 만든다.

설계 원칙
---------
1. **stdlib only** (json, os, math, argparse, bisect, sys). numpy 도 쓰지 않는다.
   -> MAPDL 드라이버가 어느 인터프리터에서든 import 할 수 있어야 하기 때문.
2. **하드코딩 금지.** 손실 숫자는 전부 맵에서 읽는다. 이 파일 안의 숫자 리터럴은
   (a) 자기검증용 기대값과 (b) 계획서가 지정한 철손/자석손 스케일 계수뿐이다.
3. **부동소수 매칭 필수.** 맵에 저장된 전류는 115.07499999999999 / 230.04999999999998
   이다. `==` 는 4개 D1 전류 중 2개에서 조용히 실패한다. 반드시 허용오차 비교.
4. **최근접 이웃 대체 금지.** 격자에 없는 셀(예: 15000 rpm, 250 A)은 조용히 근사하지
   않고 `MapCellMissing` 을 던진다. 메시지에 요청 셀과 사용 가능한 격자를 모두 찍는다.

python 3.10 호환 (match 문 없음, `X | Y` 어노테이션 없음, 3.11+ stdlib 없음).

CLI
---
    python jeet_map_loader.py --self-test --repo <repo root>
    python jeet_map_loader.py --table     --repo <repo root>
    python jeet_map_loader.py --table     --map  <path to map json>
"""

import argparse
import bisect
import json
import math
import os
import sys

# ---------------------------------------------------------------------------
# 공개 상수 (다른 모듈이 이 이름으로 import 한다 -- 이름/값 변경 금지)
# ---------------------------------------------------------------------------

MAP_REL = "mlxperPJT/JEET/map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary.json"

SPEEDS = (2000, 4000, 8000, 16000)
CURRENTS = (0.1, 115.075, 230.05, 345.025, 460.0)
PHASE_DEFAULT = 36.0

# DC 동손은 맵 전체(120 FullFEA 레코드)에서 정확히 k*I^2 이며 속도/위상과 무관하다.
# 검증: ts_dc_active_only_kW*1000/I^2 의 서로 다른 값이 상대오차 2.7e-16 이내로 1개.
K_DC_SLOT = 0.1484500725968904      # W/A^2, exact
K_DC_END = 0.08723750151056191      # W/A^2, exact
K_DC_RATIO = 0.5876554991485352     # K_DC_END / K_DC_SLOT, 120개 레코드 모두 동일

N_TURNS = 6

# losses_for / loss_vector 가 돌려주는 키 (정확히 이 6개, 그 이상도 이하도 아님).
# 드라이버가 dict 를 그대로 순회하며 HGEN 주입에 쓰므로 메타데이터 키를 섞지 않는다.
# 프로브넌스(backup_dir 등)가 필요하면 get_record() 로 원본 레코드를 따로 받아라.
LOSS_KEYS = ("cu_slot", "cu_end", "ac_slot", "fe_s", "fe_r", "pm")

# 계획서 §1 D1 이 지정한 철손/자석손 속도 스케일링 기준값
FE_S_REF = 1856.0       # W  @ n_ref
FE_R_REF = 74.0         # W  @ n_ref
PM_REF = 3385.0         # W  @ n_ref (자석 전체 손실)
PM_SCALE = 0.17         # 자석부 배분 계수
N_REF = 15000.0         # rpm

# 매칭 허용오차
ITOL = 1e-3             # A. 격자 간격 115 A -> 1e5 배 안전
PTOL = 1e-6             # deg. 격자 간격 18 deg
PT_NEG_TOL = 1e-9       # W. per-turn AC 음수 판정 여유 (실측 최소값 +1.93e-4 W)
PT_REL_TOL = 1e-6       # per-turn AC 합 == fea_total_ac 상대 허용오차

# p_ac_continuous 의 마지막 호출 상태. "ok" | "clamped_low" | "clamped_high".
# 시그니처가 float 반환으로 고정되어 있어 플래그를 여기에 남긴다.
# 스레드 안전하지 않다 -- 정확한 상태가 필요하면 p_ac_continuous_ex() 를 써라.
LAST_PAC_STATUS = "ok"


class MapCellMissing(Exception):
    """요청한 (speed, current, phase, mode) 셀이 맵 격자에 없을 때."""
    pass


# ---------------------------------------------------------------------------
# 경로 / 로딩
# ---------------------------------------------------------------------------

def default_repo_root():
    """이 파일 위치에서 레포 루트를 역산한다.

    kit dir = <repo>/mlxperPJT/thermal/plans/PLAN_20260906_assets  이므로 4단계 위.
    (moa 가 이 파일을 freeflow/scripts/ 로 승격하면 깊이가 달라지므로, 승격 후에는
     반드시 --repo 를 명시하거나 default 를 다시 계산해야 한다. CLI 인자가 정본이다.)
    """
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir, os.pardir, os.pardir))


def default_map_path(repo_root):
    """레포 루트를 받아 맵 JSON 의 절대경로를 돌려준다."""
    if repo_root is None:
        repo_root = default_repo_root()
    return os.path.normpath(os.path.join(str(repo_root), *MAP_REL.split("/")))


def load_map(path):
    """맵 JSON 을 읽어 레코드 list 를 그대로 돌려준다 (인덱싱/변환 없음).

    Raises
    ------
    FileNotFoundError : 경로가 없을 때 (원인 안내 메시지 포함)
    ValueError        : 최상위가 비어있지 않은 list 가 아닐 때
    """
    path = str(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            "JEET map not found: %s\n"
            "  This file IS committed in the repo (%s).\n"
            "  If it is missing, the checkout is incomplete -- run `git pull` "
            "on branch freeflow-e10-model, or pass --map explicitly." % (path, MAP_REL))
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list) or not data:
        raise ValueError("map JSON top level must be a non-empty list, got %r (%s)"
                         % (type(data).__name__, path))
    for i, rec in enumerate(data):
        if not isinstance(rec, dict):
            raise ValueError("map record %d is %r, expected dict (%s)"
                             % (i, type(rec).__name__, path))
    return data


# ---------------------------------------------------------------------------
# 셀 조회
# ---------------------------------------------------------------------------

def _grid_of(records, mode):
    """해당 mode 레코드들이 실제로 담고 있는 격자를 (speeds, currents, phases) 로."""
    sp = sorted(set(int(round(float(r["speed"]))) for r in records
                    if str(r.get("mode", "")) == mode))
    cu = sorted(set(float(r["current"]) for r in records
                    if str(r.get("mode", "")) == mode))
    ph = sorted(set(float(r["phase"]) for r in records
                    if str(r.get("mode", "")) == mode))
    return sp, cu, ph


def get_record(records, speed, current, phase=PHASE_DEFAULT, mode="FullFEA"):
    """정확히 하나의 맵 레코드를 돌려준다.

    부동소수 허용오차 매칭 (spec):
        speed   : int(round(...)) 동등 비교
        current : abs diff <= ITOL (1e-3 A)
        phase   : abs diff <= PTOL (1e-6 deg)

    없으면 `MapCellMissing` -- 최근접 이웃으로 조용히 대체하지 않는다.
    """
    mode = str(mode)
    try:
        s_want = int(round(float(speed)))
        i_want = float(current)
        p_want = float(phase)
    except (TypeError, ValueError):
        raise MapCellMissing("bad cell request: speed=%r current=%r phase=%r"
                             % (speed, current, phase))

    hits = []
    for rec in records:
        if str(rec.get("mode", "")) != mode:
            continue
        try:
            if int(round(float(rec["speed"]))) != s_want:
                continue
            if abs(float(rec["current"]) - i_want) > ITOL:
                continue
            if abs(float(rec["phase"]) - p_want) > PTOL:
                continue
        except (KeyError, TypeError, ValueError):
            continue
        hits.append(rec)

    if len(hits) == 1:
        return hits[0]

    sp, cu, ph = _grid_of(records, mode)
    where = ("mode=%s speed=%r current=%r phase=%r" % (mode, speed, current, phase))
    grid = ("available grid for mode=%s -> speed%s current%s phase%s"
            % (mode, sp, cu, ph))
    if not hits:
        raise MapCellMissing(
            "map cell not found: %s\n  %s\n"
            "  (no nearest-neighbour fallback by design -- fix the request or the map)"
            % (where, grid))
    raise MapCellMissing(
        "map cell ambiguous: %s matched %d records\n  %s" % (where, len(hits), grid))


# ---------------------------------------------------------------------------
# 손실 -- 격자점 위 (맵에서 직접)
# ---------------------------------------------------------------------------

def iron_magnet(speed, fe_s_ref=FE_S_REF, fe_r_ref=FE_R_REF,
                pm_ref=PM_REF, pm_scale=PM_SCALE, n_ref=N_REF):
    """계획서 §1 D1 의 속도 전용 철손/자석손 스케일링. 단위 W.

        fe_s = fe_s_ref * (n/n_ref)**1.5
        fe_r = fe_r_ref * (n/n_ref)**1.5
        pm   = pm_ref * pm_scale * (n/n_ref)**2

    !! 한계 !! 이 규칙은 전류에 무관하다. 계획서 §2 의 R1 값(16 krpm/460 A 기준)과
    비교하면 fe_s 는 약 22 % 낮고 pm 은 약 53 % 낮다. 16 krpm/460 A 에서는 fe+pm 이
    전체 발열의 3 % 라 영향이 제한적이지만, 16 krpm/115 A 에서는 32 % 라 중요하다.
    이 사실을 결과 JSON 의 `_loss_model_caveat` 에 반드시 남길 것.
    """
    n = float(speed)
    r15 = (n / float(n_ref)) ** 1.5
    r20 = (n / float(n_ref)) ** 2.0
    return {"fe_s": float(fe_s_ref) * r15,
            "fe_r": float(fe_r_ref) * r15,
            "pm": float(pm_ref) * float(pm_scale) * r20}


def losses_for(records, speed, current, phase=PHASE_DEFAULT, case="DC"):
    """격자점 (speed, current, phase) 의 손실 벡터. 전부 W (float).

    반환 키는 정확히 LOSS_KEYS 6개:
        cu_slot : ts_dc_active_only_kW * 1000      (DC, 활성부)
        cu_end  : ts_dc_end_kW         * 1000      (DC, 엔드부)
        ac_slot : case='AC' 이면 fea_total_ac_kW*1000, case='DC' 이면 0.0
        fe_s, fe_r, pm : iron_magnet(speed)

    case 는 대소문자 무시. 'DC'/'AC' 외에는 ValueError.
    """
    c = str(case).strip().upper()
    if c not in ("DC", "AC"):
        raise ValueError("case must be 'DC' or 'AC', got %r" % (case,))
    rec = get_record(records, speed, current, phase, mode="FullFEA")
    im = iron_magnet(speed)
    return {
        "cu_slot": float(rec["ts_dc_active_only_kW"]) * 1000.0,
        "cu_end": float(rec["ts_dc_end_kW"]) * 1000.0,
        "ac_slot": (float(rec["fea_total_ac_kW"]) * 1000.0) if c == "AC" else 0.0,
        "fe_s": im["fe_s"],
        "fe_r": im["fe_r"],
        "pm": im["pm"],
    }


def per_turn_raw(records, speed, current, phase=PHASE_DEFAULT):
    """`fea_per_turn_raw` 를 파싱해 6개 float (W) 로.

    !! 이 값은 DC+AC 합산이다 (AC 만이 아니다). 활성부 전용이며 엔드 손실은 없다.
    검증: sum(raw) == (ts_dc_active_only_kW + fea_total_ac_kW)*1000, 상대오차 2.2e-13.
    ActiveXParametersMotorCADv261.txt:3307 -- "Conductor losses (DC + AC) per turn
    (active length only)".
    T1 = 에어갭 쪽(손실 최대), T6 = 요크 쪽.
    """
    rec = get_record(records, speed, current, phase, mode="FullFEA")
    raw = rec.get("fea_per_turn_raw")
    if not isinstance(raw, str):
        raise ValueError("fea_per_turn_raw is %r, expected str (speed=%r current=%r "
                         "phase=%r)" % (type(raw).__name__, speed, current, phase))
    parts = [p for p in raw.split(":")]
    if len(parts) != N_TURNS:
        raise ValueError("fea_per_turn_raw must split into exactly %d fields, got %d: %r"
                         % (N_TURNS, len(parts), raw))
    return [float(p) for p in parts]


def per_turn_ac(records, speed, current, phase=PHASE_DEFAULT):
    """턴별 AC 손실 6개 (W).

        ac[i] = raw[i] - cu_slot/6

    DC 를 6턴에 균등 분배하는 것이 옳은 근거: 6턴 1병렬(모든 턴이 동일 전류),
    단일 헤어핀 바 단면(7.422 x 3.372 mm)으로 전 층이 동일, 그리고 raw 가 활성부
    전용이라 층별 엔드 연장 차이가 애초에 배열 밖에 있다.

    검증: 모든 항목 >= 0, 합 == fea_total_ac_kW*1000 (상대 PT_REL_TOL).
    """
    rec = get_record(records, speed, current, phase, mode="FullFEA")
    raw = per_turn_raw(records, speed, current, phase)
    dc_share = float(rec["ts_dc_active_only_kW"]) * 1000.0 / float(N_TURNS)
    ac = [v - dc_share for v in raw]

    worst = min(ac)
    if worst < -PT_NEG_TOL:
        raise AssertionError(
            "per_turn_ac produced a negative entry (%.6e W) at speed=%r current=%r "
            "phase=%r -- the uniform DC/6 split is violated for this cell: %r"
            % (worst, speed, current, phase, ac))
    ac = [0.0 if (v < 0.0) else v for v in ac]

    total = float(rec["fea_total_ac_kW"]) * 1000.0
    s = math.fsum(ac)
    denom = abs(total) if abs(total) > 0.0 else 1.0
    rel = abs(s - total) / denom
    if rel > PT_REL_TOL:
        raise AssertionError(
            "per_turn_ac sum mismatch at speed=%r current=%r phase=%r: "
            "sum=%.12g W vs fea_total_ac_kW*1000=%.12g W (rel %.3e > %.0e)"
            % (speed, current, phase, s, total, rel, PT_REL_TOL))
    return ac


# ---------------------------------------------------------------------------
# 손실 -- 임의 전류 (연속 I_cont 근찾기용)
# ---------------------------------------------------------------------------

def p_dc(current):
    """임의 전류의 DC 동손 (cu_slot, cu_end) [W].

    맵에서 유도된 정확한 상수를 쓴다 (피팅이 아니라 항등식):
        cu_slot = K_DC_SLOT * I^2
        cu_end  = K_DC_END  * I^2
    속도/위상 무관 -- 맵 120 레코드 전체에서 비트 단위로 동일함이 확인되었다.
    """
    i2 = float(current) ** 2
    return (K_DC_SLOT * i2, K_DC_END * i2)


def _pchip_slopes(xs, ys):
    """Fritsch-Carlson monotone cubic Hermite 의 노드 기울기. scipy 없이 구현.

    단조 데이터에 대해 오버슈트 없는 단조 보간을 보장한다 (Fritsch & Carlson 1980).
    """
    n = len(xs)
    if n < 2:
        return [0.0] * n
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    if n == 2:
        return [d[0], d[0]]

    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0.0:
            m[i] = 0.0                              # 국소 극값 -> 평평하게
        else:
            w1 = 2.0 * h[i] + h[i - 1]
            w2 = h[i] + 2.0 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])   # 가중 조화평균

    # 끝점: 3점 편차식 + 단조성 클램프
    m[0] = _pchip_edge(h[0], h[1], d[0], d[1])
    m[n - 1] = _pchip_edge(h[n - 2], h[n - 3], d[n - 2], d[n - 3])
    return m


def _pchip_edge(h0, h1, d0, d1):
    """끝점 기울기 (Fritsch-Carlson edge case)."""
    m = ((2.0 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if m * d0 <= 0.0:
        return 0.0
    if (d0 * d1 <= 0.0) and (abs(m) > abs(3.0 * d0)):
        return 3.0 * d0
    return m


def _pchip_eval(xs, ys, ms, x):
    """구간 [xs[i], xs[i+1]] 에서 3차 Hermite 평가. 노드에서는 정확히 ys[i]."""
    n = len(xs)
    i = bisect.bisect_right(xs, x) - 1
    if i < 0:
        i = 0
    if i > n - 2:
        i = n - 2
    h = xs[i + 1] - xs[i]
    t = (x - xs[i]) / h
    t2 = t * t
    t3 = t2 * t
    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2
    return h00 * ys[i] + h * h10 * ms[i] + h01 * ys[i + 1] + h * h11 * ms[i + 1]


def ac_grid(records, speed, phase=PHASE_DEFAULT):
    """해당 속도/위상의 AC 격자를 (I list, I^2 list, P_ac list [W]) 로 (전류 오름차순)."""
    rows = []
    for cur in CURRENTS:
        rec = get_record(records, speed, cur, phase, mode="FullFEA")
        rows.append((float(rec["current"]), float(rec["fea_total_ac_kW"]) * 1000.0))
    rows.sort(key=lambda t: t[0])
    ii = [r[0] for r in rows]
    xx = [r[0] ** 2 for r in rows]
    yy = [r[1] for r in rows]
    return ii, xx, yy


def p_ac_continuous_ex(records, speed, current, phase=PHASE_DEFAULT, method="pchip"):
    """p_ac_continuous 의 상태 포함 버전. (value_W, status) 를 돌려준다.

    status: "ok" | "clamped_low" | "clamped_high"
    """
    ii, xx, yy = ac_grid(records, speed, phase)
    x = float(current) ** 2

    if x <= xx[0]:
        return (yy[0], "ok" if abs(x - xx[0]) <= 1e-9 * max(1.0, xx[0]) else "clamped_low")
    if x >= xx[-1]:
        return (yy[-1], "ok" if abs(x - xx[-1]) <= 1e-9 * max(1.0, xx[-1]) else "clamped_high")

    m = str(method).strip().lower()
    if m == "linear":
        j = bisect.bisect_right(xx, x) - 1
        if j > len(xx) - 2:
            j = len(xx) - 2
        t = (x - xx[j]) / (xx[j + 1] - xx[j])
        return (yy[j] + t * (yy[j + 1] - yy[j]), "ok")
    if m != "pchip":
        raise ValueError("method must be 'pchip' or 'linear', got %r" % (method,))

    ms = _pchip_slopes(xx, yy)
    return (_pchip_eval(xx, yy, ms, x), "ok")


def p_ac_continuous(records, speed, current, phase=PHASE_DEFAULT, method="pchip"):
    """임의 전류에서의 AC 슬롯 손실 [W].

    보간 스킴 (선택 근거 포함)
    -------------------------
    * 독립변수는 **I^2**, 종속변수는 **P_ac [W]** 이다. DC 동손이 정확히 I^2 에
      비례하고 선형 열모델에서 온도가 손실의 아핀 범함수이므로, I^2 축에서 보간하면
      DC 항이 정확히 직선이 되고 AC 의 포화 편차만 곡선으로 남는다. I 축 보간은
      최저 브래킷(115-230 A)에서 최대 5.7 % 저평가 편향을 낳는다.
    * 스킴은 **Fritsch-Carlson monotone cubic Hermite (PCHIP)** -- scipy 없이 순수
      stdlib 구현. 선택 이유:
        (a) 5개 격자점을 정확히 통과한다 (노드에서 오차 0).
        (b) 데이터가 단조이면 결과도 단조임이 보장된다 (오버슈트/링잉 없음).
            AC 는 4속도 모두에서 전류에 대해 단조 증가하므로 조건이 성립한다.
        (c) C1 연속이라 I_cont 이분법 근찾기가 매끄럽다. 자연 3차 스플라인은
            단조성을 보장하지 않고, 순수 선형(I^2)은 꺾임점에서 미분이 튄다.
      `method="linear"` 로 (I^2, P_ac) 구간선형 대안을 쓸 수 있다 (비교/감도용).
    * **격자 밖은 클램프하고 플래그한다.** I < 0.1 A -> P_ac(0.1), I > 460 A ->
      P_ac(460). 상태는 모듈 전역 `LAST_PAC_STATUS` 와 `p_ac_continuous_ex()` 로
      노출된다. 460 A 위는 자기포화 때문에 외삽 신뢰도가 없으므로 클램프가
      의도적으로 보수적이지 않은(=온도를 과소평가하는) 쪽임을 호출자가 알아야 한다.
      -> I_cont 결과가 460 A 를 넘으면 status `extrap_high` 를 반드시 붙일 것.
    """
    global LAST_PAC_STATUS
    val, status = p_ac_continuous_ex(records, speed, current, phase, method)
    LAST_PAC_STATUS = status
    return val


def loss_vector(records, speed, current, phase=PHASE_DEFAULT, case="DC"):
    """임의 전류에서 유효한 손실 벡터. 키는 losses_for 와 동일(LOSS_KEYS 6개), 단위 W.

        cu_slot, cu_end : p_dc(I)  -- 정확한 k*I^2
        ac_slot         : case='AC' 이면 p_ac_continuous(...), 'DC' 이면 0.0
        fe_s, fe_r, pm  : iron_magnet(speed)  -- 전류 무관

    격자 전류에서는 losses_for 와 기계정밀도로 일치한다 (자기검증에서 확인).
    """
    c = str(case).strip().upper()
    if c not in ("DC", "AC"):
        raise ValueError("case must be 'DC' or 'AC', got %r" % (case,))
    cu_slot, cu_end = p_dc(current)
    im = iron_magnet(speed)
    ac = p_ac_continuous(records, speed, current, phase) if c == "AC" else 0.0
    return {"cu_slot": cu_slot, "cu_end": cu_end, "ac_slot": ac,
            "fe_s": im["fe_s"], "fe_r": im["fe_r"], "pm": im["pm"]}


# ---------------------------------------------------------------------------
# 자기검증
# ---------------------------------------------------------------------------

def _rel(a, b):
    d = max(abs(a), abs(b), 1.0)
    return abs(a - b) / d


def _check(ok, msg):
    if not ok:
        raise AssertionError(msg)
    print("  PASS  %s" % msg)


def _self_test(map_path):
    """스펙에 인용된 모든 숫자를 실제 파일에 대고 검증한다. 실패하면 AssertionError."""
    print("jeet_map_loader self-test")
    print("  map: %s" % map_path)
    recs = load_map(map_path)
    print("")

    # -- 1. 파일 형상 --------------------------------------------------------
    print("[1] file shape")
    _check(len(recs) == 240, "record count == 240 (got %d)" % len(recs))
    ff = [r for r in recs if r.get("mode") == "FullFEA"]
    hy = [r for r in recs if r.get("mode") == "Hybrid"]
    _check(len(ff) == 120 and len(hy) == 120,
           "mode split FullFEA=120 / Hybrid=120 (got %d / %d)" % (len(ff), len(hy)))
    _check(all(int(r["proximity_model"]) == 3 for r in ff),
           "every FullFEA record has proximity_model == 3")
    sp, cu, ph = _grid_of(recs, "FullFEA")
    _check(tuple(sp) == SPEEDS, "SPEEDS == %r matches file (%r)" % (SPEEDS, tuple(sp)))
    _check(len(cu) == len(CURRENTS)
           and all(abs(a - b) <= ITOL for a, b in zip(cu, CURRENTS)),
           "CURRENTS %r match file %r within %g A" % (CURRENTS, tuple(cu), ITOL))
    _check(ph == [0.0, 18.0, 36.0, 54.0, 72.0, 90.0],
           "phases == [0, 18, 36, 54, 72, 90] (got %r)" % (ph,))
    print("")

    # -- 2. 부동소수 매칭이 정말 필요한가 -------------------------------------
    print("[2] float tolerance is mandatory")
    stored = sorted(set(float(r["current"]) for r in ff))
    _check(115.075 not in stored,
           "literal 115.075 is NOT in the file (stored as %.17g) -> `==` would fail"
           % stored[1])
    _check(230.05 not in stored,
           "literal 230.05 is NOT in the file (stored as %.17g) -> `==` would fail"
           % stored[2])
    r = get_record(recs, 16000, 115.075, 36.0)
    _check(abs(float(r["current"]) - 115.075) <= ITOL,
           "get_record(16000, 115.075) resolves via tolerance match")
    r = get_record(recs, 16000, 230.05, 36.0)
    _check(abs(float(r["current"]) - 230.05) <= ITOL,
           "get_record(16000, 230.05) resolves via tolerance match")
    print("")

    # -- 3. MapCellMissing (근접 대체 금지) -----------------------------------
    print("[3] missing cells raise MapCellMissing, never nearest-neighbour")
    for bad in ((15000, 460.0), (16000, 250.0), (3000, 460.0)):
        raised = False
        try:
            get_record(recs, bad[0], bad[1], 36.0)
        except MapCellMissing as exc:
            raised = True
            txt = str(exc)
            _check("%r" % bad[0] in txt or str(bad[0]) in txt,
                   "MapCellMissing for %r names the requested cell" % (bad,))
            _check("2000" in txt and "460.0" in txt,
                   "MapCellMissing for %r lists the available grid" % (bad,))
        _check(raised, "get_record%r raises MapCellMissing" % (bad,))
    print("")

    # -- 4. 정격 셀 16000 / 460.0 / 36 ---------------------------------------
    print("[4] rated cell 16000 rpm / 460.0 A / 36 deg (FullFEA)")
    L = losses_for(recs, 16000, 460.0, 36.0, case="AC")
    _check(_rel(L["cu_slot"], 31412.035361502007) < 1e-12,
           "cu_slot == 31412.035361502007 W (got %.12f)" % L["cu_slot"])
    _check(_rel(L["cu_end"], 18459.4553196349) < 1e-12,
           "cu_end  == 18459.4553196349 W (got %.12f)" % L["cu_end"])
    _check(_rel(L["ac_slot"], 37171.8430714458) < 1e-12,
           "ac_slot == 37171.8430714458 W (got %.12f)" % L["ac_slot"])
    D = losses_for(recs, 16000, 460.0, 36.0, case="DC")
    _check(D["ac_slot"] == 0.0, "case='DC' forces ac_slot == 0.0")
    _check(tuple(sorted(L.keys())) == tuple(sorted(LOSS_KEYS)),
           "losses_for returns exactly LOSS_KEYS %r" % (LOSS_KEYS,))
    bad_case = False
    try:
        losses_for(recs, 16000, 460.0, 36.0, case="AC+")
    except ValueError:
        bad_case = True
    _check(bad_case, "losses_for rejects an unknown case with ValueError")
    print("")

    # -- 5. DC 는 정확히 k*I^2, 속도/위상 무관 --------------------------------
    print("[5] DC quadratic constants (all 120 FullFEA records)")
    worst_s = 0.0
    worst_e = 0.0
    worst_r = 0.0
    for rec in ff:
        i2 = float(rec["current"]) ** 2
        worst_s = max(worst_s, _rel(float(rec["ts_dc_active_only_kW"]) * 1000.0,
                                    K_DC_SLOT * i2))
        worst_e = max(worst_e, _rel(float(rec["ts_dc_end_kW"]) * 1000.0,
                                    K_DC_END * i2))
        worst_r = max(worst_r, _rel(float(rec["ts_dc_end_kW"])
                                    / float(rec["ts_dc_active_only_kW"]), K_DC_RATIO))
    _check(worst_s < 1e-12,
           "K_DC_SLOT = %.16g W/A^2 exact over 120 records (worst rel %.3e)"
           % (K_DC_SLOT, worst_s))
    _check(worst_e < 1e-12,
           "K_DC_END  = %.16g W/A^2 exact over 120 records (worst rel %.3e)"
           % (K_DC_END, worst_e))
    _check(worst_r < 1e-12,
           "K_DC_END/K_DC_SLOT = %.16g over 120 records (worst rel %.3e)"
           % (K_DC_RATIO, worst_r))
    s0, e0 = p_dc(460.0)
    _check(_rel(s0, 31412.035361502007) < 1e-12 and _rel(e0, 18459.4553196349) < 1e-12,
           "p_dc(460.0) reproduces the rated DC pair (%.9f, %.9f)" % (s0, e0))
    s1, e1 = p_dc(250.0)
    _check(abs(s1 - 9278.129537305650) < 1e-6,
           "p_dc(250.0) slot = %.6f W (plan 2 quotes 9279 W -> 0.0094 %% apart)" % s1)
    print("")

    # -- 6. per-turn 항등식 ---------------------------------------------------
    print("[6] per-turn identity over all 120 FullFEA records")
    worst_id = 0.0
    worst_neg = float("inf")
    worst_ac = 0.0
    for rec in ff:
        sp_ = int(rec["speed"])
        cu_ = float(rec["current"])
        ph_ = float(rec["phase"])
        raw = per_turn_raw(recs, sp_, cu_, ph_)
        tot = (float(rec["ts_dc_active_only_kW"]) + float(rec["fea_total_ac_kW"])) * 1000.0
        worst_id = max(worst_id, abs(math.fsum(raw) - tot) / tot)
        ac = per_turn_ac(recs, sp_, cu_, ph_)
        worst_neg = min(worst_neg, min(ac))
        tac = float(rec["fea_total_ac_kW"]) * 1000.0
        worst_ac = max(worst_ac, abs(math.fsum(ac) - tac) / tac)
    _check(worst_id < 1e-9,
           "sum(per_turn_raw) == (dc_slot + ac)*1000 (worst rel %.3e)" % worst_id)
    _check(worst_neg >= 0.0,
           "per_turn_ac has no negative entry (min %.6e W)" % worst_neg)
    _check(worst_ac < PT_REL_TOL,
           "sum(per_turn_ac) == fea_total_ac_kW*1000 (worst rel %.3e)" % worst_ac)

    raw460 = per_turn_raw(recs, 16000, 460.0, 36.0)
    _check(len(raw460) == 6, "per_turn_raw returns exactly 6 fields")
    _check(_rel(raw460[0], 22168.6409191256) < 1e-12 and
           _rel(raw460[5], 7708.19249552215) < 1e-12,
           "rated per-turn raw T1 = 22168.6409191256 W, T6 = 7708.19249552215 W")
    ac460 = per_turn_ac(recs, 16000, 460.0, 36.0)
    _check(_rel(ac460[0], 16933.3016922086) < 1e-9 and
           _rel(ac460[5], 2472.8532686051494) < 1e-9,
           "rated per-turn AC   T1 = 16933.3016922086 W, T6 = 2472.85326860515 W")
    _check(_rel(math.fsum(ac460), 37171.8430714458) < 1e-9,
           "rated per-turn AC sums to 37171.8430714458 W")
    print("")

    # -- 7. 16셀 완전성 -------------------------------------------------------
    print("[7] D1 16-cell completeness (4 speeds x 4 currents, phase 36, FullFEA)")
    seen = 0
    for spd in SPEEDS:
        for cur in CURRENTS[1:]:
            L = losses_for(recs, spd, cur, PHASE_DEFAULT, case="AC")
            for k in LOSS_KEYS:
                if not (isinstance(L[k], float) and L[k] >= 0.0
                        and L[k] == L[k] and L[k] < float("inf")):
                    raise AssertionError("cell %d/%g key %s is %r" % (spd, cur, k, L[k]))
            seen += 1
    _check(seen == 16, "all 16 D1 cells present and finite (got %d)" % seen)
    _check(len([r for r in ff if abs(float(r["phase"]) - 36.0) <= PTOL]) == 20,
           "phase 36 FullFEA slice has 20 records (5 currents x 4 speeds)")
    print("")

    # -- 8. 철손/자석손 -------------------------------------------------------
    print("[8] iron / magnet, speed-only rule")
    im = iron_magnet(16000)
    _check(_rel(im["fe_s"], 2044.6597946484526) < 1e-12,
           "iron_magnet(16000) fe_s = 2044.6597946484526 W (got %.10f)" % im["fe_s"])
    _check(_rel(im["fe_r"], 81.52199612283701) < 1e-12,
           "iron_magnet(16000) fe_r = 81.52199612283701 W  (got %.10f)" % im["fe_r"])
    _check(_rel(im["pm"], 654.7342222222222) < 1e-12,
           "iron_magnet(16000) pm   = 654.7342222222222 W  (got %.10f)" % im["pm"])
    _check(abs(im["fe_s"] - 2044.7) < 0.05 and abs(im["fe_r"] - 81.5) < 0.05
           and abs(im["pm"] - 654.7) < 0.05,
           "iron_magnet(16000) rounds to 2044.7 / 81.5 / 654.7 W as quoted")
    im15 = iron_magnet(15000)
    _check(_rel(im15["fe_s"], FE_S_REF) < 1e-12 and _rel(im15["fe_r"], FE_R_REF) < 1e-12
           and _rel(im15["pm"], PM_REF * PM_SCALE) < 1e-12,
           "iron_magnet(n_ref=15000) returns the reference values exactly")
    _check(iron_magnet(16000)["fe_s"] == iron_magnet(16000)["fe_s"],
           "iron/magnet rule is current-independent BY CONSTRUCTION "
           "(see docstring caveat: fe_s ~22 % low, pm ~53 % low at 16 krpm/460 A)")
    print("")

    # -- 9. p_ac_continuous ---------------------------------------------------
    print("[9] p_ac_continuous -- PCHIP on (I^2, P_ac)")
    for spd in SPEEDS:
        for cur in CURRENTS:
            grid_v = float(get_record(recs, spd, cur, 36.0)["fea_total_ac_kW"]) * 1000.0
            got = p_ac_continuous(recs, spd, cur, 36.0)
            if _rel(got, grid_v) > 1e-12:
                raise AssertionError("p_ac_continuous(%d, %g) = %.12g, grid = %.12g"
                                     % (spd, cur, got, grid_v))
    _check(True, "exact at all 20 grid points (4 speeds x 5 currents), rel < 1e-12")

    for spd in SPEEDS:
        prev = -1.0
        steps = 400
        for j in range(steps + 1):
            cur = 0.1 + (460.0 - 0.1) * j / float(steps)
            v = p_ac_continuous(recs, spd, cur, 36.0)
            if v < prev - 1e-9:
                raise AssertionError("p_ac_continuous non-monotone at %d rpm, I=%.4f "
                                     "(%.6f < %.6f)" % (spd, cur, v, prev))
            prev = v
    _check(True, "monotone non-decreasing over I in [0.1, 460] at all 4 speeds "
                 "(401 samples each)")

    v, st = p_ac_continuous_ex(recs, 16000, 600.0, 36.0)
    _check(st == "clamped_high" and _rel(v, 37171.8430714458) < 1e-12,
           "I=600 A clamps to P_ac(460) and flags 'clamped_high'")
    v, st = p_ac_continuous_ex(recs, 16000, 0.0, 36.0)
    _check(st == "clamped_low", "I=0 A clamps to P_ac(0.1) and flags 'clamped_low'")
    p_ac_continuous(recs, 16000, 300.0, 36.0)
    _check(LAST_PAC_STATUS == "ok",
           "LAST_PAC_STATUS == 'ok' for an in-range interpolation")

    # 격자 사이에서 PCHIP 과 선형(I^2)이 서로 몇 % 떨어져 있는지 -- 정보성 확인
    a = p_ac_continuous(recs, 16000, 172.5, 36.0, method="pchip")
    b = p_ac_continuous(recs, 16000, 172.5, 36.0, method="linear")
    _check(abs(a - b) / b < 0.20,
           "pchip vs linear(I^2) at 16 krpm/172.5 A: %.2f vs %.2f W (%.2f %% apart)"
           % (a, b, 100.0 * abs(a - b) / b))
    print("")

    # -- 10. loss_vector 일관성 ----------------------------------------------
    print("[10] loss_vector == losses_for at grid currents")
    worst = 0.0
    for spd in SPEEDS:
        for cur in CURRENTS[1:]:
            for case in ("DC", "AC"):
                A = losses_for(recs, spd, cur, 36.0, case=case)
                B = loss_vector(recs, spd, cur, 36.0, case=case)
                if tuple(sorted(B.keys())) != tuple(sorted(LOSS_KEYS)):
                    raise AssertionError("loss_vector keys %r" % (sorted(B.keys()),))
                for k in LOSS_KEYS:
                    worst = max(worst, _rel(A[k], B[k]))
    _check(worst < 1e-9,
           "32 grid comparisons agree to machine precision (worst rel %.3e)" % worst)
    Bmid = loss_vector(recs, 16000, 172.5, 36.0, case="AC")
    _check(Bmid["ac_slot"] > 0.0 and Bmid["cu_slot"] > 0.0,
           "loss_vector works off-grid: 16 krpm/172.5 A -> cu_slot %.1f W, ac_slot %.1f W"
           % (Bmid["cu_slot"], Bmid["ac_slot"]))
    print("")

    print("ALL SELF-TESTS PASSED")
    return 0


# ---------------------------------------------------------------------------
# --table
# ---------------------------------------------------------------------------

def _print_table(map_path, phase=PHASE_DEFAULT):
    """D1 16셀 (speed x current) 손실 표를 정렬된 텍스트로 출력."""
    recs = load_map(map_path)
    print("D1 loss table -- JEET_ACLoss_Ref_Map_Summary.json, mode=FullFEA, "
          "phase=%.0f deg" % phase)
    print("map: %s" % map_path)
    print("cu_slot = ts_dc_active_only_kW*1000 | cu_end = ts_dc_end_kW*1000 | "
          "ac_slot = fea_total_ac_kW*1000 (Case AC only)")
    print("fe_s = 1856*(n/15000)^1.5 | fe_r = 74*(n/15000)^1.5 | "
          "pm = 3385*0.17*(n/15000)^2   [speed-only, current-independent]")
    print("")
    hdr = ("%7s %9s %10s %10s %10s %9s %8s %9s %11s %11s"
           % ("speed", "I_Arms", "cu_slot", "cu_end", "ac_slot",
              "fe_s", "fe_r", "pm", "TOT_DC", "TOT_AC"))
    print(hdr)
    print("-" * len(hdr))
    for spd in SPEEDS:
        for cur in CURRENTS[1:]:
            dc = losses_for(recs, spd, cur, phase, case="DC")
            ac = losses_for(recs, spd, cur, phase, case="AC")
            tot_dc = math.fsum(dc[k] for k in LOSS_KEYS)
            tot_ac = math.fsum(ac[k] for k in LOSS_KEYS)
            print("%7d %9.3f %10.1f %10.1f %10.1f %9.1f %8.1f %9.1f %11.1f %11.1f"
                  % (spd, cur, ac["cu_slot"], ac["cu_end"], ac["ac_slot"],
                     ac["fe_s"], ac["fe_r"], ac["pm"], tot_dc, tot_ac))
        print("-" * len(hdr))
    print("")
    print("CAVEAT -- fe_s / fe_r / pm come from the plan's speed-only rule and are")
    print("  current-independent. Against the plan section 2 R1 values at 16 krpm/460 A")
    print("  (fe_s 2619, fe_r 89, pm 1382 W) the rule is ~22 % low on stator iron and")
    print("  ~53 % low on magnet loss, so I_cont at high current is OPTIMISTIC.")
    print("  Copy this into the result JSON as `_loss_model_caveat`.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(
        prog="jeet_map_loader.py",
        description="JEET AC-loss map reader for the e10 thermal study (D1/D2).")
    p.add_argument("--repo", default=default_repo_root(),
                   help="repo root; the map is resolved as <repo>/%s (default: %%(default)s)"
                        % MAP_REL)
    p.add_argument("--map", default=None,
                   help="explicit path to JEET_ACLoss_Ref_Map_Summary.json "
                        "(overrides --repo)")
    p.add_argument("--phase", type=float, default=PHASE_DEFAULT,
                   help="phase advance in deg (default: %(default)s)")
    p.add_argument("--self-test", action="store_true",
                   help="run the assert-based self-test against the real map file")
    p.add_argument("--table", action="store_true",
                   help="print the 16-cell (speed x current) D1 loss table")
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    map_path = args.map if args.map else default_map_path(args.repo)
    if not args.self_test and not args.table:
        _build_parser().print_help()
        print("")
        print("resolved map path: %s" % map_path)
        print("exists: %s" % os.path.isfile(map_path))
        return 0
    rc = 0
    if args.self_test:
        rc |= _self_test(map_path)
        if args.table:
            print("")
    if args.table:
        rc |= _print_table(map_path, args.phase)
    return rc


if __name__ == "__main__":
    sys.exit(main())
