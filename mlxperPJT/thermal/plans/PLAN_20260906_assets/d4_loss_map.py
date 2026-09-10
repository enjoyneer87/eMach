# -*- coding: utf-8 -*-
# 이 docstring 은 raw 여야 한다: 아래 사용법에 D:\KDH\NvidiaNemo 가 있고,
# 일반 문자열에서 \N 은 named-unicode 이스케이프로 해석돼 SyntaxError 가 난다.
r"""d4_loss_map.py -- 계획서 §1 D4. e10 철손/자석손을 (속도 × 전류) 맵으로 Motor-CAD 에서 뽑는다.

왜 필요한가
-----------
D1 이 쓴 철손/자석손은 계획서 §1 이 지정한 **속도 전용** 규칙이다.

    fe_s = 1856*(n/15000)^1.5    fe_r = 74*(n/15000)^1.5    pm = 3385*0.17*(n/15000)^2

전류항이 없다. 그래서 16 krpm 의 네 전류점에서 fe_s/fe_r/pm 이 **완전히 같은 값**
(2045 / 82 / 655 W) 으로 들어갔고, 최저 전류 115 A 에서 이미 자석이 216.4 degC
(한계 150) 라 보간할 구간 자체가 없어 `I_cont(16000) = 0` 이 나왔다.

즉 그 0 은 물리가 아니라 손실 모델의 산물이다. 자석손이 전류에 의존하지 않으면
전류를 낮춰도 자석 온도가 안 내려간다. 저속에서 안 드러난 이유는 철손이
`(n/15000)^1.5` 로 작아져 권선이 먼저 걸리기 때문이다 -- 그때는 한계를 정하는 것이
전류 의존항인 동손이다. **속도를 올릴수록 전류 비의존 손실이 지배해서 결함이 드러난다.**

킷은 이 한계를 이미 알고 기록해 두었다(`d1_cont_rating.py` LOSS_MODEL_CAVEAT,
`jeet_map_loader.py:iron_magnet` docstring). 이 스크립트가 그 부채를 갚는다.

JEET 맵으로는 안 되는 이유
--------------------------
`JEET_ACLoss_Ref_Map_Summary.json` 240 레코드의 키를 전수 조사하면 **동손뿐**이다:
proximity_model, mode, speed, current, phase, backup_dir, hybrid_{total,prox,skin}_kW,
fea_{total_ac,per_turn_sum}_kW, fea_per_turn_raw, ts_{ac,dc}_active_only_kW,
ts_dc_active_kW, ts_dc_end_kW. 철손도 자석손도 없다. 그래서 새로 계산해야 한다.

`01_e10_motorcad_losses.py` 가 0 을 돌려준 진짜 이유
----------------------------------------------------
계획서 D4 는 "`do_magnetic_calculation` 미호출로 추정"이라고 적었지만, 그 스크립트는
`do_magnetic_thermal_calculation()` 을 부르고 있다. 진짜 원인은 **운전점을 읽기만 하고
쓰지 않는 것**이다 -- `Shaft_Speed_RPM`/`RMSCurrent` 를 `get_variable` 로 가져온 뒤
`set_variable` 없이 바로 계산한다. .mot 에 들어 있던 운전점으로 푼 셈이다.

그래서 이 스크립트는 운전점을 **쓰고, 되읽어 확인한 뒤** 계산한다. 되읽기 검증이
없으면 같은 실패가 조용히 재발한다.

재사용
------
드라이버 패턴은 `tools/motorCAD/pyMCAD/mqs_runner.py` 를 따른다(검증된 구현).
파라미터명은 전부 `ActiveXParametersMotorCADv261.txt` 에서 확인했다 -- CLAUDE.md 가
임의 추측을 금지한다.

    RMSCurrent    3484,i/p,Magnetics,Amps       PhaseAdvance 3508,i/p,Magnetics,EDeg
    ShaftSpeed    8750,i/p,Miscellaneous,rpm    DCBusVoltage 3509,i/p,Magnetics,Volts
    Armature_Winding_Loss_Total  3269,o/p       Loss_[Magnet]           3330,o/p
    Loss_[Stator_Back_Iron] 3324,o/p            Loss_[Stator_Tooth]     3325,o/p
    Loss_[Rotor_Back_Iron]  3320,o/p            Loss_[Rotor_Tooth]      3322,o/p

사용법
------
    # moa 에서
    python d4_loss_map.py --dry-run                       # Motor-CAD 없이 전 경로 점검
    python d4_loss_map.py --repo D:\KDH\NvidiaNemo\eMach  # 16점 실행
    python d4_loss_map.py --repo ... --resume             # 중단된 실행 이어받기
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import time
import traceback

# ---------------------------------------------------------------------------
# 격자 -- D1 과 정확히 같아야 한다. 다르면 맵이 D1 에 안 꽂힌다.
# ---------------------------------------------------------------------------

SPEEDS = (2000, 4000, 8000, 16000)
CURRENTS = (115.075, 230.05, 345.025, 460.0)
PHASE_DEFAULT = 36.0            # JEET 레코드 규약 (계획서 §1 D1)

MOT_DEFAULT = r"D:\KDH\simVary\e10_6TSweep\refModel\e10Turn6V261.mot"
OUT_REL = "mlxperPJT/thermal/thesis_out/e10_loss_map.json"

# Motor-CAD 자동화명 (ActiveXParametersMotorCADv261.txt 확인필)
OP_SPEED = "ShaftSpeed"
OP_CURRENT = "RMSCurrent"
OP_PHASE = "PhaseAdvance"
OP_VOLTAGE = "DCBusVoltage"

LOSS_VARS = {
    "cu_total": "Armature_Winding_Loss_Total",
    "cu_dc": "Power_Armature_Copper_Loss",
    "fe_s_back": "Loss_[Stator_Back_Iron]",
    "fe_s_tooth": "Loss_[Stator_Tooth]",
    "fe_r_back": "Loss_[Rotor_Back_Iron]",
    "fe_r_tooth": "Loss_[Rotor_Tooth]",
    "pm": "Loss_[Magnet]",
}

# 계획서 §2 가 주는 교차검증점. 16 krpm/460 A 의 R1 파이프라인 값 (W).
# pm 은 "정적 추정 8132 × 0.17 = 1382" 이고, Motor-CAD Full-FEA 레코드는 1335 W 다.
# 둘이 3.5 % 차이라 **Motor-CAD 출력에는 ×0.17 을 다시 곱하면 안 된다** -- 이미 그 수준이다.
CROSSCHECK = {
    "speed": 16000, "current": 460.0,
    "fe_s": 2619.0, "fe_r": 89.0, "pm": 1382.0,
    "pm_mcad_record": 1335.0,
    "source": "PLAN_20260906 section 2 (R1 pipeline) + Motor-CAD Full-FEA record",
}

# 계획서 §1 D1 의 속도 전용 규칙 -- 비교용으로만 계산한다 (jeet_map_loader 와 동일 상수)
FE_S_REF, FE_R_REF, PM_REF, PM_SCALE, N_REF = 1856.0, 74.0, 3385.0, 0.17, 15000.0


def speed_only_rule(speed):
    """계획서 §1 D1 의 속도 전용 철손/자석손. 새 맵과 나란히 두어 차이를 보이기 위한 것."""
    r15 = (float(speed) / N_REF) ** 1.5
    r20 = (float(speed) / N_REF) ** 2.0
    return {"fe_s": FE_S_REF * r15, "fe_r": FE_R_REF * r15, "pm": PM_REF * PM_SCALE * r20}


# ---------------------------------------------------------------------------
# 로그
# ---------------------------------------------------------------------------

_LOG_FH = None


def log(msg=""):
    line = str(msg)
    print(line, flush=True)
    if _LOG_FH is not None:
        _LOG_FH.write(line + "\n")
        _LOG_FH.flush()


def default_repo_root():
    """이 파일은 <repo>/mlxperPJT/thermal/plans/PLAN_20260906_assets/ 에 있다."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", "..", ".."))


# ---------------------------------------------------------------------------
# Motor-CAD 세션
# ---------------------------------------------------------------------------

class MotorCADSession(object):
    """Motor-CAD 인스턴스 하나를 열고 .mot 을 로드한다.

    `open_new_instance=True` 를 명시한다. 기본값이 True 이긴 하나, GUI 가 떠 있을 때
    붙어버리면 **화면에 로드된 다른 모델로 계산이 돌아간다.** 그 사고는 로그에
    아무 흔적을 안 남기므로 명시가 값싸다.
    """

    def __init__(self, mot_path, keep_open=False):
        self.mot_path = mot_path
        self.keep_open = bool(keep_open)
        self.mcad = None

    def __enter__(self):
        import ansys.motorcad.core as mc
        log("  Motor-CAD 기동 (open_new_instance=True) ...")
        t0 = time.time()
        self.mcad = mc.MotorCAD(open_new_instance=True)
        log("    기동 %.1f s" % (time.time() - t0))
        log("  로드 %s" % self.mot_path)
        t0 = time.time()
        self.mcad.load_from_file(self.mot_path)
        log("    로드 %.1f s" % (time.time() - t0))
        return self.mcad

    def __exit__(self, exc_type, exc, tb):
        if self.mcad is None or self.keep_open:
            return False
        try:
            self.mcad.quit()
            log("  Motor-CAD 종료")
        except Exception as e:      # 종료 실패로 결과를 잃지 않는다
            log("  [warn] quit 실패: %r" % (e,))
        return False


def set_operating_point(mcad, speed, current, phase, voltage=None, rel_tol=1e-6):
    """운전점을 쓰고 **되읽어 확인**한다.

    되읽기가 이 함수의 존재 이유다. `01_e10_motorcad_losses.py` 는 쓰지 않고 읽기만
    해서 0 을 돌려줬고, 그 사실이 로그에 안 남았다. 여기서는 불일치가 예외로 뜬다.
    """
    wrote = {OP_SPEED: float(speed), OP_CURRENT: float(current), OP_PHASE: float(phase)}
    if voltage is not None:
        wrote[OP_VOLTAGE] = float(voltage)
    for name, val in wrote.items():
        mcad.set_variable(name, val)

    back = {}
    bad = []
    for name, want in wrote.items():
        got = float(mcad.get_variable(name))
        back[name] = got
        scale = max(abs(want), 1.0)         # 상대 판정: 절대 K/A 임계는 규모에 따라 깨진다
        if abs(got - want) / scale > rel_tol:
            bad.append("%s: 요청 %.6g -> 실제 %.6g" % (name, want, got))
    if bad:
        raise RuntimeError("운전점 되읽기 불일치 -- " + "; ".join(bad))
    return back


def read_losses(mcad):
    """손실 스칼라를 읽어 원시값과 집계값을 함께 돌려준다."""
    raw = {}
    missing = []
    for key, var in LOSS_VARS.items():
        try:
            raw[key] = float(mcad.get_variable(var))
        except Exception as e:
            raw[key] = None
            missing.append("%s [%s] %s" % (key, var, repr(e)[:60]))
    if missing:
        raise RuntimeError("손실 변수 읽기 실패 -- " + "; ".join(missing))

    def g(k):
        v = raw.get(k)
        return float(v) if isinstance(v, (int, float)) else 0.0

    agg = {
        "fe_s": g("fe_s_back") + g("fe_s_tooth"),
        "fe_r": g("fe_r_back") + g("fe_r_tooth"),
        "pm": g("pm"),
        "cu_mcad": g("cu_total") or g("cu_dc"),
    }
    return agg, raw


def solve_point(mcad, speed, current, phase, voltage=None):
    """한 운전점: 설정 -> 검증 -> 자기해석 -> 손실 읽기."""
    t0 = time.time()
    back = set_operating_point(mcad, speed, current, phase, voltage)
    mcad.do_magnetic_calculation()
    agg, raw = read_losses(mcad)
    dt = time.time() - t0
    return {
        "speed": float(speed), "current": float(current), "phase": float(phase),
        "P_W": agg, "raw_W": raw, "op_readback": back,
        "solve_s": round(dt, 2),
        "speed_only_rule_W": speed_only_rule(speed),
    }


# ---------------------------------------------------------------------------
# 게이트 -- "운전점이 안 먹었다" 를 잡는 것이 최우선
# ---------------------------------------------------------------------------

def check_map(points, n_expect, rel_spread_min=1e-3):
    """맵이 쓸 만한지 판정한다. 반환 (ok, gates_dict).

    판정량을 무엇으로 나눌지 먼저 정한다 -- 손실은 하중에 비례하므로 절대 W 임계는
    하중만 바꿔도 깨진다(이 세션에서 세 번 반복한 실수).

    1. 개수      : 요청한 점이 전부 있는가 (메시/격자의 성질, 하중 무관 -> 절대 판정 OK)
    2. 유한·양수 : NaN/inf/음수 손실은 물리적으로 불가
    3. **분산**  : 같은 속도에서 전류만 바꿨을 때 pm 이 변하는가.
                   변하지 않으면 = 운전점이 안 먹은 것 = 우리가 고치려던 바로 그 결함.
                   상대 분산 (max-min)/max 로 잰다.
    4. 단조      : 같은 전류에서 속도가 오르면 fe_s 가 오르는가 (철손의 기본 성질)
    """
    gates = {}
    ok = True

    gates["count"] = {"got": len(points), "want": n_expect,
                      "ok": len(points) == n_expect}
    ok = ok and gates["count"]["ok"]

    bad_vals = []
    for p in points:
        for k, v in p["P_W"].items():
            if not (isinstance(v, (int, float)) and math.isfinite(v)) or v < 0.0:
                bad_vals.append("%d rpm / %.3f A : %s = %r" % (p["speed"], p["current"], k, v))
    gates["finite_nonneg"] = {"violations": bad_vals, "ok": not bad_vals}
    ok = ok and gates["finite_nonneg"]["ok"]

    # 3. 전류 의존성 -- D4 의 존재 이유이므로 가장 엄하게 본다
    spread = {}
    flat = []
    for s in sorted(set(p["speed"] for p in points)):
        row = [p for p in points if p["speed"] == s]
        if len(row) < 2:
            continue
        for key in ("pm", "fe_s"):
            vals = [p["P_W"][key] for p in row]
            hi, lo = max(vals), min(vals)
            rel = (hi - lo) / hi if hi > 0 else 0.0
            spread["%d/%s" % (int(s), key)] = round(rel, 6)
            if key == "pm" and rel < rel_spread_min:
                flat.append("%d rpm 에서 pm 의 전류 의존 상대분산 %.2e < %.0e "
                            "-- 운전점이 안 먹었을 가능성" % (int(s), rel, rel_spread_min))
    gates["current_dependence"] = {"rel_spread": spread, "flat": flat,
                                   "min_required": rel_spread_min, "ok": not flat}
    ok = ok and gates["current_dependence"]["ok"]

    # 4. 속도 단조 (철손)
    nonmono = []
    for c in sorted(set(p["current"] for p in points)):
        col = sorted((p for p in points if p["current"] == c), key=lambda p: p["speed"])
        for a, b in zip(col, col[1:]):
            if b["P_W"]["fe_s"] < a["P_W"]["fe_s"]:
                nonmono.append("%.3f A: %d rpm %.1f W -> %d rpm %.1f W (감소)"
                               % (c, a["speed"], a["P_W"]["fe_s"],
                                  b["speed"], b["P_W"]["fe_s"]))
    gates["fe_s_monotonic_in_speed"] = {"violations": nonmono, "ok": not nonmono}
    ok = ok and gates["fe_s_monotonic_in_speed"]["ok"]

    return ok, gates


def crosscheck(points):
    """계획서 §2 의 16 krpm/460 A 값과 대조한다. 게이트가 아니라 기록용이다."""
    hit = [p for p in points
           if int(p["speed"]) == CROSSCHECK["speed"]
           and abs(p["current"] - CROSSCHECK["current"]) < 1e-6]
    if not hit:
        return {"available": False, "why": "16 krpm / 460 A 점이 맵에 없다"}
    p = hit[0]
    out = {"available": True, "reference": dict(CROSSCHECK), "measured": {}, "rel_err": {}}
    for k in ("fe_s", "fe_r", "pm"):
        got = float(p["P_W"][k])
        ref = float(CROSSCHECK[k])
        out["measured"][k] = round(got, 2)
        out["rel_err"][k] = round((got - ref) / ref, 4) if ref else None
    ref_mcad = CROSSCHECK["pm_mcad_record"]
    out["pm_vs_mcad_record"] = round((float(p["P_W"]["pm"]) - ref_mcad) / ref_mcad, 4)
    out["note"] = ("Motor-CAD 출력에 ×0.17 을 다시 곱하지 말 것. 계획서 §2 의 "
                   "'정적 추정 ×0.17' 은 Motor-CAD Full-FEA 레코드(1335 W)와 맞추기 "
                   "위한 보정이고, 이 맵은 그 Motor-CAD 계산 자체다.")
    return out


# ---------------------------------------------------------------------------
# 드라이런 -- Motor-CAD 없이 전 경로를 태운다
# ---------------------------------------------------------------------------

def fake_point(speed, current, phase):
    """물리적으로 그럴듯한 가짜 점. 게이트가 통과하는지 확인하는 용도.

    철손 ~ n^1.5 에 전류로 약한 포화 의존, 자석손 ~ n^2 에 전류 제곱 의존을 넣는다.
    """
    r15 = (speed / N_REF) ** 1.5
    r20 = (speed / N_REF) ** 2.0
    i_rel = current / 460.0
    fe_s = FE_S_REF * r15 * (0.80 + 0.30 * i_rel)
    fe_r = FE_R_REF * r15 * (0.85 + 0.20 * i_rel)
    pm = PM_REF * PM_SCALE * r20 * (0.10 + 0.90 * i_rel ** 2)
    return {
        "speed": float(speed), "current": float(current), "phase": float(phase),
        "P_W": {"fe_s": fe_s, "fe_r": fe_r, "pm": pm, "cu_mcad": 0.1485 * current ** 2},
        "raw_W": {"_dry_run": True},
        "op_readback": {OP_SPEED: float(speed), OP_CURRENT: float(current),
                        OP_PHASE: float(phase)},
        "solve_s": 0.0,
        "speed_only_rule_W": speed_only_rule(speed),
    }


# ---------------------------------------------------------------------------
# 입출력
# ---------------------------------------------------------------------------

def build_document(points, args, mot_used, gates, ok):
    doc = {
        "_model": "e10 Motor-CAD magnetic (per operating point)",
        "_loss_source": "Motor-CAD %s do_magnetic_calculation" % os.path.basename(mot_used),
        "_soltype": "magnetic steady, one solve per (speed, current)",
        "_param_ref": "ActiveXParametersMotorCADv261.txt",
        "_purpose": ("계획서 §1 D1 의 속도 전용 철손/자석손 규칙을 (속도 × 전류) 맵으로 "
                     "대체한다. 그 규칙이 16 krpm 의 I_cont 를 0 으로 만들었다."),
        "_grid": {"speeds": list(SPEEDS), "currents": list(CURRENTS),
                  "phase_advance_edeg": args.phase},
        "_mot": mot_used,
        "_dry_run": bool(args.dry_run),
        "_gates": gates,
        "_gates_ok": bool(ok),
        "_crosscheck": crosscheck(points),
        "_replaces": ("jeet_map_loader.iron_magnet(speed) -- 속도 전용 규칙. "
                      "각 점의 speed_only_rule_W 에 그 값을 같이 남겨 차이를 볼 수 있다."),
        "points": points,
    }
    return doc


def write_document(doc, out_path, indent=1):
    d = os.path.dirname(os.path.abspath(out_path))
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=indent)
    if os.path.exists(out_path):
        os.remove(out_path)
    os.rename(tmp, out_path)
    return os.path.getsize(out_path)


def load_existing(out_path):
    if not os.path.isfile(out_path):
        return []
    try:
        with open(out_path, encoding="utf-8") as f:
            doc = json.load(f)
        pts = doc.get("points") or []
        return [p for p in pts if not (p.get("raw_W") or {}).get("_dry_run")]
    except Exception as e:
        log("[warn] 기존 결과를 못 읽었다 (%r) -- 처음부터 돈다" % (e,))
        return []


def prepare_mot(mot_src, work_dir, in_place):
    """.mot 을 작업 사본으로 복사한다.

    `do_magnetic_calculation` 은 모델 폴더의 FEResultsData 를 덮어쓴다. refModel 은
    JEET 논문 데이터의 출처이므로 기본적으로 건드리지 않는다.
    """
    if in_place:
        return mot_src
    os.makedirs(work_dir, exist_ok=True)
    dst = os.path.join(work_dir, os.path.basename(mot_src))
    if not os.path.isfile(dst) or os.path.getmtime(dst) < os.path.getmtime(mot_src):
        shutil.copy2(mot_src, dst)
        log("  refModel 보호: .mot 을 작업 사본으로 복사 -> %s" % dst)
    else:
        log("  작업 사본 재사용 -> %s" % dst)
    return dst


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="D4: e10 철손/자석손 (속도 x 전류) 맵을 Motor-CAD 에서 뽑는다")
    p.add_argument("--repo", default=None, help="eMach 레포 루트 (기본: 이 파일 기준 유도)")
    p.add_argument("--mot", default=MOT_DEFAULT, help="e10 .mot 경로")
    p.add_argument("--out", default=None, help="출력 JSON (기본: <repo>/%s)" % OUT_REL)
    p.add_argument("--log", default=None, help="로그 파일")
    p.add_argument("--speeds", default=",".join(str(s) for s in SPEEDS))
    p.add_argument("--currents", default=",".join(repr(c) for c in CURRENTS))
    p.add_argument("--phase", type=float, default=PHASE_DEFAULT)
    p.add_argument("--voltage", type=float, default=None,
                   help="DCBusVoltage 도 설정한다 (기본: 건드리지 않고 .mot 값 사용)")
    p.add_argument("--work-dir", default=r"D:\KDH\simVary\e10_6TSweep\_d4_lossmap",
                   help="refModel 을 안 건드리기 위한 .mot 작업 사본 위치")
    p.add_argument("--in-place", action="store_true",
                   help="사본 없이 원본 .mot 에서 바로 돈다 (refModel 의 FEResultsData 를 덮어쓴다)")
    p.add_argument("--resume", action="store_true",
                   help="기존 출력에 있는 점은 건너뛴다")
    p.add_argument("--keep-open", action="store_true", help="끝나도 Motor-CAD 를 안 닫는다")
    p.add_argument("--dry-run", action="store_true",
                   help="Motor-CAD 없이 격자/게이트/입출력 경로만 태운다")
    p.add_argument("--json-indent", type=int, default=1)
    p.add_argument("--spread-min", type=float, default=1e-3,
                   help="같은 속도에서 pm 의 전류 의존 상대분산 최소치 (이하면 실패)")
    return p


def main(argv=None):
    global _LOG_FH
    args = build_parser().parse_args(argv)

    repo = os.path.abspath(args.repo) if args.repo else default_repo_root()
    out_path = args.out or os.path.join(repo, *OUT_REL.split("/"))
    if args.log:
        _LOG_FH = open(args.log, "w", encoding="utf-8")

    speeds = [int(float(x)) for x in args.speeds.split(",") if x.strip()]
    currents = [float(x) for x in args.currents.split(",") if x.strip()]
    grid = [(s, c) for s in speeds for c in currents]

    log("=" * 72)
    log("D4  e10 철손/자석손 (속도 x 전류) 맵")
    log("=" * 72)
    log("repo      %s" % repo)
    log("out       %s" % out_path)
    log("격자      속도 %s x 전류 %s  = %d 점"
        % (speeds, [round(c, 3) for c in currents], len(grid)))
    log("위상      %.1f EDeg" % args.phase)
    log("모드      %s" % ("DRY-RUN (Motor-CAD 미기동)" if args.dry_run else "실행"))
    log("")

    done = load_existing(out_path) if (args.resume and not args.dry_run) else []
    have = set((int(p["speed"]), round(float(p["current"]), 6)) for p in done)
    if done:
        log("resume: 기존 %d 점을 재사용한다" % len(done))

    points = list(done)
    t_all = time.time()

    if args.dry_run:
        for s, c in grid:
            points.append(fake_point(s, c, args.phase))
        log("드라이런: 가짜 점 %d 개 생성 (물리적으로 그럴듯한 값)" % len(grid))
        mot_used = args.mot
    else:
        if not os.path.isfile(args.mot):
            log("[FAIL] .mot 이 없다: %s" % args.mot)
            return 2
        mot_used = prepare_mot(args.mot, args.work_dir, args.in_place)
        todo = [(s, c) for (s, c) in grid if (int(s), round(c, 6)) not in have]
        if not todo:
            log("모든 점이 이미 있다 -- 계산 생략")
        else:
            log("풀 점 %d 개" % len(todo))
            try:
                with MotorCADSession(mot_used, keep_open=args.keep_open) as mcad:
                    for i, (s, c) in enumerate(todo, 1):
                        log("  [%2d/%2d] %5d rpm  %8.3f A ..." % (i, len(todo), s, c))
                        try:
                            pt = solve_point(mcad, s, c, args.phase, args.voltage)
                        except Exception as e:
                            log("    [FAIL] %r" % (e,))
                            log(traceback.format_exc())
                            break
                        points.append(pt)
                        P = pt["P_W"]
                        log("          fe_s %8.1f  fe_r %6.1f  pm %8.1f  cu %9.1f W "
                            "(%.1f s)" % (P["fe_s"], P["fe_r"], P["pm"], P["cu_mcad"],
                                          pt["solve_s"]))
                        # 매 점마다 저장: 16 솔브 중 실패해도 앞의 것을 잃지 않는다
                        write_document(build_document(points, args, mot_used, {}, False),
                                       out_path, args.json_indent)
            except Exception as e:
                log("[FAIL] Motor-CAD 세션: %r" % (e,))
                log(traceback.format_exc())

    points.sort(key=lambda p: (p["speed"], p["current"]))
    ok, gates = check_map(points, len(grid), args.spread_min)
    doc = build_document(points, args, mot_used, gates, ok)
    size = write_document(doc, out_path, args.json_indent)

    log("")
    log("-" * 72)
    log("결과 표 (W)")
    log("  %6s %9s %9s %8s %9s %9s" % ("rpm", "A", "fe_s", "fe_r", "pm", "pm(규칙)"))
    for p in points:
        log("  %6d %9.3f %9.1f %8.1f %9.1f %9.1f"
            % (p["speed"], p["current"], p["P_W"]["fe_s"], p["P_W"]["fe_r"],
               p["P_W"]["pm"], p["speed_only_rule_W"]["pm"]))
    log("-" * 72)

    log("게이트:")
    for name, g in gates.items():
        mark = "PASS" if g.get("ok") else "FAIL"
        log("  [%s] %s" % (mark, name))
        if not g.get("ok"):
            for v in (g.get("violations") or g.get("flat") or [])[:6]:
                log("        %s" % v)
    cc = doc["_crosscheck"]
    if cc.get("available"):
        log("교차검증 (계획서 §2, 16 krpm/460 A):")
        for k in ("fe_s", "fe_r", "pm"):
            log("  %-5s 측정 %8.1f  기준 %8.1f  상대오차 %+.1f %%"
                % (k, cc["measured"][k], cc["reference"][k], 100.0 * cc["rel_err"][k]))

    log("")
    log("wrote %s (%.1f KB, %d 점, 총 %.1f s)"
        % (out_path, size / 1024.0, len(points), time.time() - t_all))
    log("판정: %s" % ("PASS" if ok else "FAIL"))

    if _LOG_FH is not None:
        _LOG_FH.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
