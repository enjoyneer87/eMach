# -*- coding: utf-8 -*-
r"""d3_freeflow_gravity_fix.py -- FreeFlow 중력벡터를 축방향(-Z)에서 반경방향(-Y)으로 수정 (D3).

실행 방법 (11_freeflow_thermal_setup.py 와 동일한 방식)
------------------------------------------------------
    FreeFlow.exe --headless --script d3_freeflow_gravity_fix.py

전역 `app` 객체가 이미 존재하는 환경에서 돈다. argparse 를 쓸 수 없으므로
모든 설정값은 **환경변수 또는 --key=value 형태의 argv** 로 덮어쓸 수 있게 했다
(_arg() 참조). 하드코딩된 절대경로는 전부 '덮어쓰기 가능한 기본값'일 뿐이다.

    set D3_PROBE_ONLY=1
    set D3_ORIG_PRJ=D:\...\Project_thermal.freeflow
    FreeFlow.exe --headless --script d3_freeflow_gravity_fix.py

무엇을 왜 고치는가 (HANDOFF_20260722.md §10-4, CLAUDE.md)
--------------------------------------------------------
e10 은 **수평(가로) 취부**인데 FreeFlow 중력벡터가 **모터 축방향(-Z, 약 (0,0,-9.81))**
으로 들어가 있다 (`Project_thermal.freeflow` 바이너리에서 -9.81 단일 축값 확인).
오일이 축방향으로 고이므로 스프레이/자켓 근벽 유동, 즉 D3 가 역산하는 h 의 근거가
통째로 틀린 조건에서 계산됐다. -> 중력을 축에 수직인 반경방향(-Y)으로 고친다.

★★ 경고: 이 스크립트는 물리설정을 바꾼다 -> Rocky 결과셋 all-or-nothing 무효화 ★★
    HANDOFF §6: 벽BC·열물성·InletT 등 물리설정을 바꾸면 기존 결과 **전체**가 무효화되고
    resume 이 불가능해진다. DeleteResults() 후 **t=0 부터 재계산**이며 8 s 완주에
    **GPU 약 5 시간**이 든다(유동전용 8 s 실적 18,313 s + 열모델 추가부담).
    따라서 이 스크립트는 **솔브를 시작하지 않는다.** 설정만 하고 저장한 뒤 끝난다.
    솔브는 12_freeflow_thermal_solve.py 패턴의 러너로 따로 돌려라.

★★ 과거 최대 실책 재발방지 ★★
    12_freeflow_thermal_solve.py:35-40 - Fluid Inlet 온도가 **0 °C** 로 들어가 있어서
    벽만 데워도 유입오일이 계속 0 °C 라 벌크가 안 데워졌다. 이걸 못 찾으면 온도장이
    통째로 무의미해진다. DeleteResults() 는 벽 BC 와 inlet 온도를 날리므로
    이 스크립트는 삭제 **후에** 둘 다 다시 넣고, **읽어서 확인(read-back assert)** 한다.
    확인 실패시 저장하지 않고 FATAL 로 죽는다.

동작 순서
---------
    0) 프로젝트 열기
    1) ★ 먼저 관찰(probe): dir(app) / dir(model) / dir(physics) 를 로그에 덤프하고,
       이름에 'grav' 가 든 모든 속성과 그 현재값을 찍는다. **아무것도 바꾸기 전에.**
       중력 설정 API 는 레포 어디에서도 쓰인 적이 없어 이름을 모른다. 추측 전에 본다.
       D3_PROBE_ONLY=1 이면 여기서 끝낸다(30초짜리 탐색 패스).
    2) DeleteResults() (물리설정 변경 전제)
    3) 중력 설정: 그럴듯한 setter 를 순서대로 시도하고 어느 것이 먹었는지 + 읽은 값 기록
    4) 유체 물성(ATF) 재확인, 벽 BC 재적용, Fluid Inlet 70 °C 재적용
    5) read-back assert (특히 inlet 70 °C)
    6) **새 파일** Project_thermal_horizontal.freeflow 로 저장 (원본 절대 안 건드림)

python 3.10 호환.
"""

import os
import sys
import json
import time
import traceback


# ---------------------------------------------------------------------------
# 설정 -- 전부 환경변수 / argv 로 덮어쓸 수 있다
# ---------------------------------------------------------------------------

def _arg(name, default):
    """--name=value (argv) -> D3_NAME (환경변수) -> default 순으로 찾는다.

    FreeFlow --script 가 argv 를 넘겨주는지 확실하지 않으므로 환경변수를 1급으로 지원한다.
    """
    flag = "--" + name.lower().replace("_", "-") + "="
    for a in sys.argv[1:]:
        if a.lower().startswith(flag):
            return a[len(flag):]
    env = os.environ.get("D3_" + name.upper())
    if env is not None:
        return env
    return default


def _flag(name, default=False):
    v = _arg(name, None)
    if v is None:
        return bool(default)
    return str(v).strip().lower() not in ("", "0", "false", "no", "off")


# 원본(수직중력) 열해석 프로젝트 -- moa 로컬. HANDOFF §6.
ORIG_PRJ = _arg("orig_prj",
                r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project_thermal.freeflow")
# 새 파일. 원본은 절대 덮어쓰지 않는다 (11_*.py 의 보존 패턴).
NEW_PRJ = _arg("new_prj",
               r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project_thermal_horizontal.freeflow")
# MAPDL 하이브리드 벽온도 (레포 안, git 으로 전달됨)
MAPDL_JSON = _arg("mapdl_json", "")
LOG_PATH = _arg("log", os.path.join(os.environ.get("TEMP", "."), "d3_ff_gravity_fix.txt"))

PROBE_ONLY = _flag("probe_only", False)

# 새 중력벡터: 모터축(Z)에 수직인 반경방향. 기본 -Y.
G_MAG = float(_arg("g", "9.81"))
GRAVITY_NEW = (float(_arg("gx", "0.0")),
               float(_arg("gy", str(-G_MAG))),
               float(_arg("gz", "0.0")))
GRAVITY_OLD_EXPECTED = (0.0, 0.0, -G_MAG)      # 축방향 = 틀린 설정

# 벽 BC (11_freeflow_thermal_setup.py 와 동일 매핑)
WALL_FALLBACK = {"Stator": 84.4, "Winding": 91.9, "Rotating": 80.0, "Housing": 76.0}
INLET_T = float(_arg("inlet_t", "70.0"))
INLET_T_TOL = 1e-6

# 오일 ATF 물성 (11/12_*.py 가 넣은 값)
OIL_RHO = float(_arg("rho", "825.0"))
OIL_CP = float(_arg("cp", "2000.0"))
OIL_K = float(_arg("k", "0.135"))


def _default_mapdl_json():
    """kit dir = <repo>/mlxperPJT/thermal/plans/PLAN_20260906_assets -> 레포 루트는 4 단계 위."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, os.pardir, os.pardir, os.pardir, os.pardir))
    return os.path.join(repo, "mlxperPJT", "thermal", "freeflow", "data",
                        "ff_mapdl_hybrid_temps.json")


# ---------------------------------------------------------------------------
# 로깅
# ---------------------------------------------------------------------------

_lf = None

# 콘솔이 cp949 면 로그의 비ASCII 문자가 깨진다(로그 파일은 UTF-8 이라 무사).
# 무인 실행에서 인코딩 예외로 죽는 일이 없도록 stdout 을 UTF-8/replace 로 돌린다.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def W(*a):
    msg = " ".join(str(x) for x in a)
    if _lf is not None:
        _lf.write(msg + "\n")
        _lf.flush()
    try:
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()
    except Exception:
        pass


def _safe(fn, *a, **kw):
    """예외를 값으로 바꾼다. 탐색 단계에서 하나 실패했다고 멈추면 안 된다."""
    try:
        return True, fn(*a, **kw)
    except Exception as e:
        return False, "<%s: %s>" % (type(e).__name__, str(e)[:160])


# dir() 에 안 나올 수 있는 동적 멤버까지 두드려 보기 위한 후보 이름표.
GRAVITY_CANDIDATES = (
    "Gravity", "GravityVector", "GravityDirection", "GravityAxis", "GravityMagnitude",
    "GetGravity", "SetGravity",
    "GetGravityVector", "SetGravityVector",
    "GetGravityDirection", "SetGravityDirection",
    "GetGravityAcceleration", "SetGravityAcceleration",
    "GetGravityAxis", "SetGravityAxis",
    "GetGravityMagnitude", "SetGravityMagnitude",
    "GetGravityEnabled", "SetGravityEnabled", "EnableGravity",
)


def _peek(obj, name):
    """obj.name 을 읽고, 호출가능하고 인자가 없어 보이면 호출해서 값까지 본다."""
    ok, v = _safe(getattr, obj, name)
    if not ok:
        return v
    if callable(v):
        low = name.lower()
        # getter 로 보이는 것만 호출한다. Set*/Delete*/Start* 등은 절대 부르지 않는다.
        if low.startswith("get") or low.startswith("is") or low.startswith("has"):
            ok2, v2 = _safe(v)
            return "%s() -> %r" % (name, v2) if ok2 else "%s() %s" % (name, v2)
        return "<callable %s>" % name
    return repr(v)


# ---------------------------------------------------------------------------
# 1) 관찰 -- 아무것도 바꾸기 전에
# ---------------------------------------------------------------------------

def probe(app_obj, model, physics):
    """중력 API 를 찾기 위한 탐색. 레포 어디에도 전례가 없으므로 추측 전에 본다."""
    W("=" * 100)
    W("PROBE (nothing has been modified yet)")
    W("=" * 100)

    targets = [("app", app_obj), ("model", model), ("physics", physics)]

    # 추가로 들여다볼 만한 하위 컬렉션들 (있으면)
    for getter in ("GetSolverSettings", "GetSimulationSettings", "GetDomainSettings",
                   "GetEnvironment", "GetSolver", "GetSettings"):
        ok, sub = _safe(getattr(model, getter)) if hasattr(model, getter) else (False, None)
        if ok and sub is not None:
            targets.append(("model.%s()" % getter, sub))
            W("  extra probe target found: model.%s() -> %r" % (getter, type(sub)))

    found = []
    seen = []
    for label, obj in targets:
        W("-" * 100)
        ok, names = _safe(dir, obj)
        if not ok:
            W("dir(%s) failed: %s" % (label, names))
            names = []
        else:
            W("dir(%s)  [%d names]" % (label, len(names)))
            pub = [n for n in names if not n.startswith("_")]
            # 한 줄에 4 개씩 -- 로그가 세로로 폭발하지 않게
            for i in range(0, len(pub), 4):
                W("    " + "  ".join("%-30s" % n for n in pub[i:i + 4]))
        seen.append((label, obj, names))
        for n in names:
            if "grav" in n.lower():
                val = _peek(obj, n)
                W("  >>> GRAVITY-LIKE (dir)   %s.%s = %s" % (label, n, val))
                found.append((label, obj, n, val))

    # ★ dir() 만 믿으면 안 된다. COM 래퍼는 __getattr__ 로 동적 디스패치하는 경우가 많아
    #   실제로 존재하는 멤버가 dir() 에 안 나온다. 후보 이름을 hasattr 로 직접 두드린다.
    W("-" * 100)
    W("explicit hasattr probe (dir() misses dynamically dispatched COM members)")
    for label, obj, names in seen:
        lower = set(n.lower() for n in names)
        for cand in GRAVITY_CANDIDATES:
            if cand.lower() in lower:
                continue                       # 위에서 이미 찍었다
            ok, has = _safe(hasattr, obj, cand)
            if ok and has:
                val = _peek(obj, cand)
                W("  >>> GRAVITY-LIKE (hasattr) %s.%s = %s" % (label, cand, val))
                found.append((label, obj, cand, val))

    W("-" * 100)
    if found:
        W("gravity-like attributes found: %d" % len(found))
        for label, _o, n, val in found:
            W("    %s.%s = %s" % (label, n, val))
    else:
        W("!! NO gravity-like attribute found on app/model/physics by dir() OR hasattr.")
        W("   Widen the search: look for 'body force', 'acceleration', 'buoyanc', 'field'.")
        for label, obj, names in seen:
            for n in names:
                low = n.lower()
                if any(t in low for t in ("accel", "bodyforce", "body_force", "buoyan")):
                    W("  >>> CANDIDATE  %s.%s = %s" % (label, n, _peek(obj, n)))
    W("=" * 100)
    return found


# ---------------------------------------------------------------------------
# 3) 중력 설정 -- 그럴듯한 setter 를 순서대로
# ---------------------------------------------------------------------------

def read_gravity(model, physics):
    """어떤 형태로든 현재 중력값을 읽어 본다. (성공한 표현, 값) 을 돌려준다."""
    for label, obj in (("physics", physics), ("model", model)):
        if obj is None:
            continue
        for getter in ("GetGravity", "GetGravityVector", "GetGravityDirection",
                       "GetGravityAcceleration"):
            if hasattr(obj, getter):
                ok, v = _safe(getattr(obj, getter))
                if ok:
                    return "%s.%s()" % (label, getter), v
        # 속성 오브젝트형: physics.Gravity.X / .Vector / .Value
        if hasattr(obj, "Gravity"):
            ok, g = _safe(getattr, obj, "Gravity")
            if ok and g is not None and not callable(g):
                for sub in ("Vector", "Value", "Direction"):
                    if hasattr(g, sub):
                        ok2, v = _safe(getattr, g, sub)
                        if ok2:
                            return "%s.Gravity.%s" % (label, sub), v
                comps = []
                for sub in ("X", "Y", "Z"):
                    if hasattr(g, sub):
                        ok2, v = _safe(getattr, g, sub)
                        comps.append(v if ok2 else None)
                if len(comps) == 3:
                    return "%s.Gravity.(X,Y,Z)" % label, tuple(comps)
                return "%s.Gravity" % label, g
    return None, None


def _as_xyz(v):
    """읽어온 값을 (x,y,z) float 튜플로 정규화. 실패하면 None."""
    if v is None:
        return None
    if isinstance(v, (list, tuple)) and len(v) == 3:
        try:
            return (float(v[0]), float(v[1]), float(v[2]))
        except Exception:
            return None
    for attrs in (("X", "Y", "Z"), ("x", "y", "z")):
        if all(hasattr(v, a) for a in attrs):
            try:
                return tuple(float(getattr(v, a)) for a in attrs)
            except Exception:
                return None
    return None


def set_gravity(model, physics, gnew):
    """그럴듯한 setter 를 순서대로 시도한다. 성공한 방법 이름을 돌려준다(없으면 None)."""
    gx, gy, gz = gnew
    attempts = []

    def _try(desc, fn):
        ok, err = _safe(fn)
        attempts.append((desc, ok, "" if ok else err))
        W("    %-52s %s%s" % (desc, "OK" if ok else "failed", "" if ok else "  " + str(err)))
        return ok

    for label, obj in (("physics", physics), ("model", model)):
        if obj is None:
            continue
        W("  trying setters on %s ..." % label)
        # (a) 3 인자 / 튜플 1 인자
        for nm in ("SetGravity", "SetGravityVector", "SetGravityDirection",
                   "SetGravityAcceleration"):
            if not hasattr(obj, nm):
                continue
            f = getattr(obj, nm)
            if _try("%s.%s(x, y, z)" % (label, nm), lambda f=f: f(gx, gy, gz)):
                return "%s.%s(x,y,z)" % (label, nm), attempts
            if _try("%s.%s((x, y, z))" % (label, nm), lambda f=f: f((gx, gy, gz))):
                return "%s.%s(tuple)" % (label, nm), attempts
            if _try("%s.%s([x, y, z])" % (label, nm), lambda f=f: f([gx, gy, gz])):
                return "%s.%s(list)" % (label, nm), attempts
        # (b) 속성 오브젝트: obj.Gravity.X = ...
        if hasattr(obj, "Gravity"):
            ok, g = _safe(getattr, obj, "Gravity")
            if ok and g is not None and not callable(g):
                for sub in ("Vector", "Value", "Direction"):
                    if hasattr(g, sub):
                        if _try("%s.Gravity.%s = (x,y,z)" % (label, sub),
                                lambda g=g, sub=sub: setattr(g, sub, (gx, gy, gz))):
                            return "%s.Gravity.%s" % (label, sub), attempts
                if all(hasattr(g, a) for a in ("X", "Y", "Z")):
                    def _setxyz(g=g):
                        setattr(g, "X", gx); setattr(g, "Y", gy); setattr(g, "Z", gz)
                    if _try("%s.Gravity.X/Y/Z = ..." % label, _setxyz):
                        return "%s.Gravity.X/Y/Z" % label, attempts
        # (c) 축+크기 분리형 (Icepak 의 'Gravity Vector Axis' 와 같은 형태)
        if hasattr(obj, "SetGravityAxis"):
            axis = "Y" if abs(gy) >= max(abs(gx), abs(gz)) else ("X" if abs(gx) >= abs(gz) else "Z")
            f = getattr(obj, "SetGravityAxis")
            if _try("%s.SetGravityAxis(%r)" % (label, axis), lambda f=f, a=axis: f(a)):
                if hasattr(obj, "SetGravityMagnitude"):
                    _safe(getattr(obj, "SetGravityMagnitude"), -G_MAG if gy < 0 else G_MAG)
                return "%s.SetGravityAxis" % label, attempts

    return None, attempts


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def run():
    global MAPDL_JSON
    W("=" * 100)
    W("d3_freeflow_gravity_fix.py -- FreeFlow gravity: axial (-Z) -> radial (-Y)")
    W("HANDOFF_20260722.md §10-4 / CLAUDE.md: e10 is horizontally mounted.")
    W("started:", time.strftime("%Y-%m-%d %H:%M:%S"))
    W("ORIG_PRJ :", ORIG_PRJ)
    W("NEW_PRJ  :", NEW_PRJ)
    W("PROBE_ONLY:", PROBE_ONLY)
    W("gravity target:", GRAVITY_NEW, "(expected current, wrong:", GRAVITY_OLD_EXPECTED, ")")
    W("=" * 100)

    if os.path.abspath(ORIG_PRJ) == os.path.abspath(NEW_PRJ):
        W("FATAL: NEW_PRJ must differ from ORIG_PRJ -- the original must be preserved.")
        return 2
    if not os.path.isfile(ORIG_PRJ):
        W("FATAL: project not found:", ORIG_PRJ)
        W("       override with --orig-prj=<path> or env D3_ORIG_PRJ.")
        return 2

    app_obj = globals().get("app")
    if app_obj is None:
        W("FATAL: no global 'app'. Run this under:  FreeFlow.exe --headless --script <this file>")
        return 2

    app_obj.OpenProject(ORIG_PRJ)
    model = app_obj.GetCurrentModel()
    W("project opened.")
    ok, hr = _safe(model.HasResults)
    W("HasResults (before any change):", hr if ok else hr)
    ok, phys = _safe(model.GetPhysics)
    physics = phys if ok else None
    if physics is None:
        W("WARNING: model.GetPhysics() failed:", phys)

    # ---- 1) 관찰 -------------------------------------------------------------
    probe(app_obj, model, physics)

    expr, gval = read_gravity(model, physics)
    W("current gravity via %s -> %r  (parsed %r)" % (expr, gval, _as_xyz(gval)))
    g_old = _as_xyz(gval)
    if g_old is not None:
        if abs(g_old[2]) > max(abs(g_old[0]), abs(g_old[1])):
            W("CONFIRMED: gravity is dominated by the AXIAL (Z) component -- this is the "
              "HANDOFF §10-4 bug.")
        else:
            W("NOTE: gravity is NOT axially dominated. It may already have been fixed. "
              "Read the value above before assuming.")

    if PROBE_ONLY:
        W("=" * 100)
        W("PROBE-ONLY: nothing was modified, nothing was saved. "
          "Read the dir() dumps above, then re-run without D3_PROBE_ONLY.")
        W("PROBE-DONE-OK")
        return 0

    # ---- 2) 결과 무효화 ------------------------------------------------------
    W("=" * 100)
    W("!! Changing physics invalidates the Rocky result set ALL-OR-NOTHING (HANDOFF §6).")
    W("!! Resume is impossible; this forces a t=0 restart of ~8 s physical time,")
    W("!! roughly 5 h of GPU wall-clock. This script does NOT start that solve.")
    W("=" * 100)
    ok, r = _safe(model.DeleteResults)
    W("DeleteResults():", "OK" if ok else r)
    ok, hr = _safe(model.HasResults)
    W("HasResults (after delete):", hr if ok else hr)

    # ---- 3) 중력 설정 --------------------------------------------------------
    W("-" * 100)
    W("setting gravity to", GRAVITY_NEW)
    method, attempts = set_gravity(model, physics, GRAVITY_NEW)
    if method is None:
        W("FATAL: no gravity setter worked. Attempts:")
        for d, okk, err in attempts:
            W("    %-52s %s %s" % (d, "OK" if okk else "FAIL", err))
        W("       -> run with D3_PROBE_ONLY=1 and read the dir() dump; the API name is")
        W("          not used anywhere in this repo, so it has to be discovered.")
        W("       NOT SAVING. The original project is untouched.")
        return 3
    W("gravity setter that worked:", method)

    expr2, gval2 = read_gravity(model, physics)
    g_new = _as_xyz(gval2)
    W("gravity read back via %s -> %r  (parsed %r)" % (expr2, gval2, g_new))
    if g_new is None:
        W("WARNING: could not parse the read-back gravity. Verify by hand before solving.")
    else:
        radial = max(abs(g_new[0]), abs(g_new[1]))
        if abs(g_new[2]) > radial:
            W("FATAL: gravity is still axially dominated after the set:", g_new)
            W("       NOT SAVING.")
            return 3
        mag = (g_new[0] ** 2 + g_new[1] ** 2 + g_new[2] ** 2) ** 0.5
        if abs(mag - G_MAG) > 0.05:
            W("FATAL: gravity magnitude %.4f != %.4f m/s2 -- refusing to save." % (mag, G_MAG))
            return 3
        W("ASSERT OK: gravity is radial (|axial|=%.4f < radial=%.4f), |g|=%.4f m/s2"
          % (abs(g_new[2]), radial, mag))

    # ---- 4) 물성 / 벽 BC / inlet 재적용 --------------------------------------
    # DeleteResults() 는 벽 BC 와 inlet 온도를 날린다. 반드시 다시 넣는다.
    W("-" * 100)
    ok, mats = _safe(model.GetMaterialCollection)
    if ok:
        ok2, fluid = _safe(mats.GetDefaultFluidMaterial)
        if ok2:
            _safe(fluid.SetDensity, OIL_RHO)
            _safe(fluid.SetSpecificHeat, OIL_CP)
            _safe(fluid.SetThermalConductivity, OIL_K)
            W("fluid (ATF): rho=%s cp=%s k=%s"
              % (_safe(fluid.GetDensity)[1], _safe(fluid.GetSpecificHeat)[1],
                 _safe(fluid.GetThermalConductivity)[1]))
    ok, r = _safe(getattr(physics, "SetEnableThermalModel"), True) if (
        physics is not None and hasattr(physics, "SetEnableThermalModel")) else (False, "n/a")
    if ok:
        W("thermal model enabled:", _safe(physics.GetEnableThermalModel)[1])

    if not MAPDL_JSON:
        MAPDL_JSON = _default_mapdl_json()
    wall_T = dict(WALL_FALLBACK)
    if os.path.isfile(MAPDL_JSON):
        try:
            d = json.load(open(MAPDL_JSON, encoding="utf-8"))
            ct = d["circuit_T"]
            wall_T["Stator"] = float(ct["JACKET"])
            wall_T["Winding"] = float(ct["SPRAY"])
            W("wall BC from %s: %s" % (MAPDL_JSON, wall_T))
        except Exception as e:
            W("WARNING: could not read %s (%s) -- using fallback %s"
              % (MAPDL_JSON, repr(e)[:120], wall_T))
    else:
        W("WARNING: MAPDL_JSON not found (%s) -- using fallback wall BC %s"
          % (MAPDL_JSON, wall_T))

    ok, geo = _safe(model.GetGeometryCollection)
    if not ok:
        W("FATAL: GetGeometryCollection failed:", geo)
        return 4
    items = {}
    for it in geo:
        okn, nm = _safe(it.GetName)
        if okn:
            items[nm] = it
    W("geometry items:", sorted(items))

    wall_ok = True
    for nm, T in sorted(wall_T.items()):
        if nm not in items:
            W("  wall %-9s MISSING from the geometry collection -- cannot set BC" % nm)
            wall_ok = False
            continue
        w = items[nm]
        ok1, e1 = _safe(w.SetThermalBoundaryConditionType, "prescribed_temperature")
        ok2, e2 = _safe(w.SetTemperature, T)
        okr, got = _safe(w.GetTemperature)
        okb, bct = _safe(w.GetThermalBoundaryConditionType)
        good = ok1 and ok2 and okr and (abs(float(got) - T) <= 1e-6)
        W("  wall %-9s BCtype=%s  T set=%.2f read=%s  %s"
          % (nm, bct if okb else "?", T, got, "OK" if good else "MISMATCH"))
        if not good:
            wall_ok = False
            W("      set errors: %s / %s" % (e1 if not ok1 else "-", e2 if not ok2 else "-"))
    if not wall_ok:
        W("FATAL: wall BC read-back failed. DeleteResults() wipes these; if they are not")
        W("       restored the whole 5 h solve is wasted. NOT SAVING.")
        return 4

    # ---- inlet 70 degC : 과거 최대 실책 지점 --------------------------------
    W("-" * 100)
    W("Fluid Inlet temperature -- the single most expensive past mistake "
      "(12_freeflow_thermal_solve.py:35-40 found it at 0 degC).")
    ok, inout = _safe(model.GetInletsOutletsCollection)
    if not ok:
        W("FATAL: GetInletsOutletsCollection failed:", inout)
        return 5
    inlets = []
    for it in inout:
        okn, nm = _safe(it.GetName)
        nm = nm if okn else ""
        W("  inlet/outlet item: %r" % nm)
        if "Fluid Inlet" in (nm or ""):
            inlets.append((nm, it))
    if not inlets:
        W("FATAL: no item whose name contains 'Fluid Inlet'. Names listed above.")
        return 5
    for nm, it in inlets:
        okb, before = _safe(it.GetTemperature)
        _safe(it.SetTemperature, INLET_T)
        oka, after = _safe(it.GetTemperature)
        W("  %-24s T before=%s  after=%s" % (nm, before, after))
        if not oka:
            W("FATAL: could not read back the inlet temperature of %r." % nm)
            return 5
        if abs(float(after) - INLET_T) > INLET_T_TOL:
            W("FATAL: inlet %r reads %s, expected %.3f degC. This is exactly the bug that "
              "made an earlier run meaningless. NOT SAVING." % (nm, after, INLET_T))
            return 5
    W("ASSERT OK: every Fluid Inlet reads %.3f degC." % INLET_T)

    # ---- 6) 새 파일로 저장 ---------------------------------------------------
    W("-" * 100)
    ok, hr = _safe(model.HasResults)
    W("HasResults (before save, expect False):", hr if ok else hr)
    ok, cr = _safe(model.CanResumeSimulation)
    W("CanResumeSimulation:", cr if ok else cr)
    app_obj.SaveProject(NEW_PRJ)
    W("saved (settings only, NOT solved):", NEW_PRJ)
    W("original left untouched:", ORIG_PRJ)
    W("=" * 100)
    W("NEXT: solve %s from t=0 for 8 s (~5 h GPU) using the "
      "12_freeflow_thermal_solve.py runner pattern, then extract near-wall particles and run"
      % os.path.basename(NEW_PRJ))
    W("      d3_htc_backout.py --sph <...>.sph --geom-dir <...\\Geometry> --t-reached <t>")
    W("DONE-OK")
    return 0


if __name__ == "__main__" or True:
    # FreeFlow --script 는 __name__ 이 "__main__" 이 아닐 수 있으므로 무조건 실행한다.
    try:
        d = os.path.dirname(os.path.abspath(LOG_PATH))
        if d and not os.path.isdir(d):
            os.makedirs(d)
        _lf = open(LOG_PATH, "w", encoding="utf-8")
    except Exception:
        _lf = None
    _rc = 1
    try:
        _rc = run()
    except Exception:
        W("EXC:", traceback.format_exc())
        _rc = 9
    finally:
        W("exit code:", _rc)
        if _lf is not None:
            _lf.close()
        # 11/12_*.py 와 동일: FreeFlow 헤드리스는 명시적으로 죽여야 프로세스가 남지 않는다.
        os._exit(_rc)
