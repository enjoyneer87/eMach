# -*- coding: utf-8 -*-
"""preflight.py -- "오늘 밤 배치를 시작해도 되는가?" 30초 환경 게이트 (moa 전용).

D1/D2/D3/D6 배치를 돌리기 전에 **한 번** 실행해서, 실제로 막힐 것들을 미리
전부 드러낸다.  각 항목은 PASS / WARN / FAIL / INFO 와 **조치 문장**을 함께 낸다.

    python preflight.py --repo C:\\Users\\moa\\eMach
    python preflight.py --repo ... --cdb D:\\KDH\\simVary\\Ansys_Thermal\\ff_e10_mesh_v2.cdb
    python preflight.py --repo ... --json preflight.json --fix

종료코드
    0 : FAIL 없음 -> 배치 시작 가능 (WARN 은 진행을 막지 않는다)
    1 : FAIL 하나 이상 -> 그대로 돌리면 시간만 버린다

검사 항목
    1  python 버전과 PyMotorEnv_310 venv 여부 (sys.executable 보고)
    2  import 프로브: numpy / matplotlib(+버전) / pyvista / ansys.mapdl.core /
       ansys.mapdl.reader / ansys.motorcad.core / ansys.dpf.core(없는 게 정상)
    3  matplotlib 폰트 목록에 Malgun Gothic 존재
    4  ★ CDB 존재 (확장자 유무 양쪽 시도) -- 1순위 블로커
    5  JEET 맵 로드 + phase 36 격자 16셀 존재 + 정격셀 수치 대조
    6  킷 모듈(jeet_map_loader / icont / thesis_style) import
    7  git: 브랜치 / 워킹트리 / ls-remote 도달 / user.name·user.email
    8  git check-ignore 4종 (PNG 는 .gitignore:39 '*.png' 에 걸린다) + negation 패치문
    9  CDB 드라이브·실행 드라이브 여유 공간
    10 thesis_out 존재 (--fix 로 생성)
    11 AWP_ROOT261 환경변수

py3.10 안전(match / X|Y 어노테이션 / 3.11+ stdlib 없음).  같은 디렉터리의
jeet_map_loader.py / icont.py / thesis_style.py 외에는 아무것도 import 하지 않고,
그 셋조차 **없어도 죽지 않는다**(해당 항목만 FAIL 로 보고).
"""

import argparse
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


# =========================================================================== #
#  상수                                                                       #
# =========================================================================== #

#: HANDOFF §3 / §11-4: moa 로컬 디스크에만 있고 git 에는 없다 (260 MB).
DEFAULT_CDB = r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2.cdb"
CDB_EXPECT_MB = 260.0
CDB_MIN_MB = 100.0

VENV_MARK = "PyMotorEnv_310"
VENV_PY = r"C:\Users\moa\.ansys_python_venvs\PyMotorEnv_310\Scripts\python.exe"

BRANCH = "freeflow-e10-model"
MAP_REL = "mlxperPJT/JEET/map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary.json"
OUT_REL = "mlxperPJT/thermal/thesis_out"

#: 계획서가 커밋하라고 한 산출물 4종.  .png 두 개가 .gitignore:39 에 걸린다.
ARTEFACTS = ("e10_cont_rating.json", "cont_rating_Tw_vs_I.png",
             "c67_stress.json", "htc_backout_horizontal.json")

GITIGNORE_PATCH = (
    "# --- thesis_out 산출물은 *.png / *.csv 규칙에서 제외 (계획서 8행) ---\n"
    "!mlxperPJT/thermal/thesis_out/*.png\n"
    "!mlxperPJT/thermal/thesis_out/*.csv\n")

SPEEDS = (2000, 4000, 8000, 16000)
D1_CURRENTS = (115.075, 230.05, 345.025, 460.0)
PHASE = 36.0
#: 정격셀 16000/460.0/36 의 확정 수치 [W] (킷 전체가 이 값에 걸려 있다).
RATED_W = (31412.035361502007, 18459.4553196349, 37171.8430714458)
RATED_TOL = 1e-6

#: 여유 공간 기준 [GiB].  1.11M 절점 정상상태 솔브가 rst/rth/esav 로 쓴다.
RUN_FREE_FAIL_GB = 10.0
RUN_FREE_WARN_GB = 25.0
CDB_FREE_WARN_GB = 5.0

REQUIRED_IMPORTS = ("numpy", "matplotlib", "pyvista",
                    "ansys.mapdl.core", "ansys.mapdl.reader")
OPTIONAL_IMPORTS = ("ansys.motorcad.core",)
#: HANDOFF §9 venv 목록에 없고 레포 전체 사용례 0건.  없는 게 정상이다.
EXPECTED_ABSENT = ("ansys.dpf.core",)

PASS, WARN, FAIL, INFO = "PASS", "WARN", "FAIL", "INFO"


# =========================================================================== #
#  기록기                                                                     #
# =========================================================================== #

class Report(object):
    """검사 결과 수집 + 사람용 출력 + 기계용 JSON."""

    def __init__(self, stream, logfile=None):
        self.rows = []
        self.stream = stream
        self.fh = None
        if logfile:
            d = os.path.dirname(os.path.abspath(logfile))
            if d and not os.path.isdir(d):
                os.makedirs(d, exist_ok=True)
            self.fh = io.open(logfile, "a", encoding="utf-8")
            self.fh.write("\n==== preflight.py %s ====\n"
                          % time.strftime("%Y-%m-%d %H:%M:%S"))

    def echo(self, msg=""):
        s = msg if isinstance(msg, str) else str(msg)
        try:
            self.stream.write(s + "\n")
            self.stream.flush()
        except Exception:                                # pragma: no cover
            pass
        if self.fh is not None:
            self.fh.write(s + "\n")
            self.fh.flush()

    def add(self, cid, name, status, detail, remedy=None, data=None):
        row = {"id": cid, "name": name, "status": status, "detail": detail,
               "remedy": remedy, "data": data if data is not None else {}}
        self.rows.append(row)
        self.echo("  %-4s  %-26s %s" % (status, cid, detail))
        if remedy and status in (FAIL, WARN):
            for line in str(remedy).split("\n"):
                self.echo("        %s -> %s" % (" " * 26, line))
        return row

    def counts(self):
        c = {PASS: 0, WARN: 0, FAIL: 0, INFO: 0}
        for r in self.rows:
            c[r["status"]] = c.get(r["status"], 0) + 1
        return c

    def close(self):
        if self.fh is not None:
            try:
                self.fh.close()
            except Exception:                            # pragma: no cover
                pass
            self.fh = None


def _utf8(stream):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _mtime(path):
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S",
                             time.localtime(os.path.getmtime(path)))
    except OSError:                                      # pragma: no cover
        return "?"


def _git(repo, args, timeout=25):
    """(rc, stdout, stderr).  git 자체가 없으면 rc=-1."""
    cmd = ["git", "-C", repo] + list(args)
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout)
    except FileNotFoundError:
        return -1, "", "git 실행 파일을 찾을 수 없다"
    except subprocess.TimeoutExpired:
        return -2, "", "git 이 %g 초 안에 응답하지 않았다: %s" % (timeout, " ".join(args))
    except Exception as exc:                             # pragma: no cover
        return -3, "", "%s: %s" % (type(exc).__name__, exc)
    dec = lambda b: b.decode("utf-8", "replace").strip()
    return p.returncode, dec(p.stdout), dec(p.stderr)


def _free_gb(path):
    """(free_GiB, total_GiB) 또는 None.  드라이브가 없으면 total==0 로 온다."""
    try:
        u = shutil.disk_usage(path)
    except Exception:
        return None
    return (u.free / float(1 << 30), u.total / float(1 << 30))


def _drive_of(path):
    d = os.path.splitdrive(os.path.abspath(path))[0]
    return (d + os.sep) if d else os.path.abspath(os.sep)


def _modver(mod, name):
    v = getattr(mod, "__version__", None)
    if v:
        return str(v)
    try:
        import importlib.metadata as md
        return str(md.version(name.replace(".", "-")))
    except Exception:
        return "?"


# =========================================================================== #
#  개별 검사                                                                  #
# =========================================================================== #

def check_python(rep):
    vi = sys.version_info
    ver = "%d.%d.%d" % (vi[0], vi[1], vi[2])
    rep.add("python.exe", "인터프리터", INFO, sys.executable,
            data={"executable": sys.executable, "version": ver,
                  "platform": platform.platform(),
                  "machine": platform.machine()})
    if (vi[0], vi[1]) == (3, 10):
        rep.add("python.version", "python 버전", PASS, "python %s (킷 목표)" % ver,
                data={"version": ver})
    elif vi[0] == 3 and vi[1] >= 7:
        rep.add("python.version", "python 버전", WARN,
                "python %s -- 킷은 3.10 을 목표로 작성됐다" % ver,
                "moa 배치는 반드시 venv 의 3.10 으로 돌릴 것:\n%s" % VENV_PY,
                {"version": ver})
    else:
        rep.add("python.version", "python 버전", FAIL,
                "python %s 는 너무 낮다" % ver, "%s 를 쓸 것" % VENV_PY,
                {"version": ver})

    if VENV_MARK.lower() in sys.executable.lower():
        rep.add("python.venv", "PyMotorEnv_310 venv", PASS,
                "venv 안에서 실행 중")
    else:
        rep.add("python.venv", "PyMotorEnv_310 venv", FAIL,
                "%s 가 아니다 (sys.executable 위 참조)" % VENV_MARK,
                "Ansys/pyvista 는 이 venv 에만 있다. 다음으로 다시 실행:\n"
                "  \"%s\" %s" % (VENV_PY, os.path.basename(__file__)))


def check_imports(rep):
    import importlib
    found = {}

    def probe(name):
        t0 = time.time()
        try:
            m = importlib.import_module(name)
        except ImportError as exc:
            return None, "%s" % exc, time.time() - t0
        except Exception as exc:            # DLL/라이선스 등 ImportError 가 아닌 실패
            return None, "%s: %s" % (type(exc).__name__, exc), time.time() - t0
        return m, None, time.time() - t0

    for name in REQUIRED_IMPORTS:
        m, err, dt = probe(name)
        cid = "import." + name
        if m is None:
            rep.add(cid, name, FAIL, "import 실패 -- %s" % err,
                    "venv 에 설치할 것:\n  \"%s\" -m pip install %s"
                    % (VENV_PY, _pipname(name)), {"error": err})
            continue
        v = _modver(m, name)
        found[name] = v
        rep.add(cid, name, PASS, "%s  (%.2f s)" % (v, dt), None, {"version": v})

    mv = found.get("matplotlib")
    if mv:
        try:
            major_minor = tuple(int(x) for x in mv.split(".")[:2])
        except ValueError:                               # pragma: no cover
            major_minor = (0, 0)
        if major_minor >= (3, 9):
            rep.add("mpl.get_cmap", "matplotlib >= 3.9", WARN,
                    "matplotlib %s -- thermal_viz.py:456 의 matplotlib.cm.get_cmap "
                    "가 제거된 버전이다" % mv,
                    "회로 오버레이 경로(circuit_3d_png / circuit_3d_gif / "
                    "full_dashboard_gif)만 AttributeError 로 죽는다.\n"
                    "contour_png / cut3d_png / component_png 는 안전하니 그쪽만 쓸 것.\n"
                    "고치려면 thermal_viz.py:456 을 matplotlib.colormaps[CMAP] 로.",
                    {"version": mv})
        else:
            rep.add("mpl.get_cmap", "matplotlib >= 3.9", PASS,
                    "matplotlib %s -- cm.get_cmap 가 아직 있다" % mv,
                    None, {"version": mv})

    for name in OPTIONAL_IMPORTS:
        m, err, dt = probe(name)
        if m is None:
            rep.add("import." + name, name, WARN, "없음 -- %s" % err,
                    "D6 의 Motor-CAD 예비 경로(.mot 로 원심 스윕)에만 필요하다. "
                    "rst/재솔브 경로를 쓸 거면 무시해도 된다.", {"error": err})
        else:
            rep.add("import." + name, name, PASS, _modver(m, name))

    for name in EXPECTED_ABSENT:
        m, err, dt = probe(name)
        if m is None:
            rep.add("import." + name, name, INFO,
                    "없음 (정상 -- 킷은 DPF 를 쓰지 않는다)", None, {"error": err})
        else:
            rep.add("import." + name, name, INFO,
                    "있음 %s (킷은 쓰지 않지만 D6 대체 리더로 쓸 수는 있다)"
                    % _modver(m, name))
    return found


def _pipname(mod):
    return {"ansys.mapdl.core": "ansys-mapdl-core",
            "ansys.mapdl.reader": "ansys-mapdl-reader",
            "ansys.motorcad.core": "ansys-motorcad-core",
            "ansys.dpf.core": "ansys-dpf-core"}.get(mod, mod)


def check_font(rep, have_mpl):
    if not have_mpl:
        rep.add("font.malgun", "Malgun Gothic", FAIL,
                "matplotlib 이 없어 확인 불가", "위의 import.matplotlib 을 먼저 해결할 것")
        return
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.font_manager as fm
        fams = set(f.name for f in fm.fontManager.ttflist)
    except Exception as exc:
        rep.add("font.malgun", "Malgun Gothic", FAIL,
                "폰트 목록을 읽지 못했다: %s: %s" % (type(exc).__name__, exc),
                "matplotlib 캐시를 지우고 재시도: "
                "%%LOCALAPPDATA%%\\matplotlib 삭제")
        return
    if "Malgun Gothic" in fams:
        rep.add("font.malgun", "Malgun Gothic", PASS,
                "matplotlib 폰트 목록에 있음 (총 %d 종)" % len(fams),
                None, {"n_families": len(fams)})
    else:
        exists = os.path.isfile(r"C:\Windows\Fonts\malgun.ttf")
        rep.add("font.malgun", "Malgun Gothic", FAIL,
                "matplotlib 폰트 목록에 없음 (malgun.ttf %s)"
                % ("는 있음 -> 캐시 문제" if exists else "도 없음"),
                ("캐시 문제다. 다음 중 하나:\n"
                 "  python -c \"import matplotlib.font_manager as fm; "
                 "fm.fontManager.addfont(r'C:/Windows/Fonts/malgun.ttf')\"\n"
                 "  또는 %LOCALAPPDATA%\\matplotlib 캐시 폴더를 지우고 재실행\n"
                 "(thesis_style.apply() 가 자동 복구를 시도하지만 한글이 네모로 "
                 "나오면 그림을 다시 그려야 한다.)")
                if exists else
                "Malgun Gothic 이 설치돼 있지 않다. 한글 라벨이 네모로 나온다.",
                {"n_families": len(fams)})

    # 실제 적용까지 되는지 (킷이 쓰는 경로 그대로)
    try:
        import thesis_style as ts
        ts.apply()
        act = ts.active_font()
        rep.add("font.applied", "thesis_style.apply()",
                PASS if act == "Malgun Gothic" else WARN,
                "적용된 폰트 = %s" % act,
                None if act == "Malgun Gothic"
                else "그림의 한글이 네모로 나온다. font.malgun 항목을 먼저 해결할 것.",
                {"font": act})
    except Exception as exc:
        rep.add("font.applied", "thesis_style.apply()", WARN,
                "%s: %s" % (type(exc).__name__, exc),
                "킷 모듈 항목(kit.modules)을 확인할 것")


def check_cdb(rep, cdb_arg):
    """04_mapdl_thermal.py 는 cdread 에 확장자 없는 경로를 넘긴다 -> 양쪽 다 본다."""
    cand = []
    base = cdb_arg
    if base.lower().endswith(".cdb"):
        cand = [base, base[:-4]]
    else:
        cand = [base + ".cdb", base]
    hit = None
    for c in cand:
        if os.path.isfile(c):
            hit = c
            break
    stem = cand[0][:-4] if cand[0].lower().endswith(".cdb") else cand[0]
    if hit is None:
        rep.add("cdb", "ff_e10_mesh_v2.cdb", FAIL,
                "없음 -- 확인한 경로: %s" % " | ".join(cand),
                "이게 1순위 블로커다. git 에 없는 260 MB 로컬 파일이다.\n"
                "  1) moa 로컬 %s 에서 복사하거나 --cdb 로 실제 경로를 지정\n"
                "  2) 없으면 재생성: 02c_maxwell_geom_extract.py -> e10_geom.json\n"
                "     -> 03_stl_to_cdb.py -> 03b_rotor_from_maxwell.py (수 시간, AEDT 필요)\n"
                "  CDB 없이는 D1/D2 를 시작할 수 없다."
                % os.path.dirname(DEFAULT_CDB),
                {"candidates": cand, "found": None})
        return None
    mb = os.path.getsize(hit) / (1024.0 * 1024.0)
    data = {"path": hit, "stem_for_cdread": stem, "size_MB": round(mb, 1),
            "mtime": _mtime(hit)}
    if mb < CDB_MIN_MB:
        rep.add("cdb", "ff_e10_mesh_v2.cdb", WARN,
                "%s  %.1f MB (%s) -- 기대 ~%.0f MB 보다 작다"
                % (hit, mb, data["mtime"], CDB_EXPECT_MB),
                "v1(544k 절점) 메시이거나 잘린 파일일 수 있다. "
                "절점 수를 cdread 후 확인할 것 (v2 = 1,113,924 절점 / "
                "737,265 tet10 SOLID87).", data)
    else:
        rep.add("cdb", "ff_e10_mesh_v2.cdb", PASS,
                "%s  %.1f MB (%s)" % (hit, mb, data["mtime"]), None, data)
    rep.add("cdb.stem", "cdread 용 확장자 없는 경로", INFO, stem,
            None, {"stem": stem})
    return hit


def check_map(rep, repo):
    path = os.path.normpath(os.path.join(repo, *MAP_REL.split("/")))
    try:
        import jeet_map_loader as jm
    except Exception as exc:
        rep.add("jeet_map", "JEET 손실 맵", FAIL,
                "jeet_map_loader import 실패: %s: %s" % (type(exc).__name__, exc),
                "킷 디렉터리(%s)에 jeet_map_loader.py 가 있어야 한다." % _HERE)
        return
    if not os.path.isfile(path):
        rep.add("jeet_map", "JEET 손실 맵", FAIL, "없음: %s" % path,
                "이 파일은 git 에 커밋돼 있다. 체크아웃이 불완전하다:\n"
                "  git -C %s pull   (브랜치 %s)" % (repo, BRANCH),
                {"path": path})
        return
    try:
        recs = jm.load_map(path)
    except Exception as exc:
        rep.add("jeet_map", "JEET 손실 맵", FAIL,
                "로드 실패: %s: %s" % (type(exc).__name__, exc),
                "파일이 손상됐다. git checkout -- %s" % MAP_REL, {"path": path})
        return

    missing = []
    for sp in SPEEDS:
        for cur in D1_CURRENTS:
            try:
                jm.get_record(recs, sp, cur, PHASE)
            except Exception:
                missing.append("%d/%.3f" % (sp, cur))
    n = len(SPEEDS) * len(D1_CURRENTS)
    data = {"path": path, "n_records": len(recs), "n_cells": n - len(missing),
            "missing": missing}
    if missing:
        rep.add("jeet_map", "JEET 손실 맵", FAIL,
                "%d 레코드, phase %g 격자 %d/%d 셀 -- 누락 %s"
                % (len(recs), PHASE, n - len(missing), n, ", ".join(missing)),
                "맵 파일이 기대한 격자를 담고 있지 않다. D1 을 시작하면 안 된다.\n"
                "  python jeet_map_loader.py --self-test --repo %s" % repo, data)
        return

    # 정격셀 수치 대조 -- 킷 전체가 이 세 값에 걸려 있다.
    try:
        P = jm.losses_for(recs, 16000, 460.0, PHASE, "AC")
        got = (P["cu_slot"], P["cu_end"], P["ac_slot"])
        ok = all(abs(a - b) <= RATED_TOL * max(1.0, abs(b))
                 for a, b in zip(got, RATED_W))
    except Exception as exc:
        got, ok = (None, None, None), False
        rep.add("jeet_map.rated", "정격셀 16000/460/36", FAIL,
                "%s: %s" % (type(exc).__name__, exc), None, data)
        return
    data["rated_W"] = {"cu_slot": got[0], "cu_end": got[1], "ac_slot": got[2]}
    rep.add("jeet_map", "JEET 손실 맵", PASS,
            "%d 레코드, phase %g 격자 %d/%d 셀" % (len(recs), PHASE, n, n),
            None, data)
    rep.add("jeet_map.rated", "정격셀 16000/460/36", PASS if ok else FAIL,
            "cu_slot %.3f / cu_end %.3f / ac_slot %.3f W" % got,
            None if ok else
            "기대값 %.6f / %.6f / %.6f 와 다르다. 맵이 바뀌었다면 킷의 "
            "K_DC_SLOT / K_DC_END 상수부터 다시 확인할 것." % RATED_W,
            {"expected_W": list(RATED_W), "got_W": list(got)})


def _capture(fn, *a, **kw):
    """모듈 self-test 는 stdout 에 수십 줄을 직접 찍는다.

    그대로 두면 (1) 보고서가 지저분해지고 (2) `--json -` 일 때 stdout 의 JSON 을
    깨뜨린다.  캡처해서 Report 를 통해서만 내보낸다.
    """
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        out = fn(*a, **kw)
    finally:
        sys.stdout = old
    return out, buf.getvalue()


def check_kit_modules(rep, deep, repo):
    import importlib
    names = ("jeet_map_loader", "icont", "thesis_style")
    mods = {}
    bad = []
    for n in names:
        try:
            mods[n] = importlib.import_module(n)
        except Exception as exc:
            bad.append("%s (%s: %s)" % (n, type(exc).__name__, exc))
    if bad:
        rep.add("kit.modules", "킷 모듈", FAIL, "import 실패: %s" % "; ".join(bad),
                "이 스크립트와 같은 폴더(%s)에 세 파일이 모두 있어야 한다.\n"
                "freeflow/scripts/ 로 승격했다면 세 파일을 함께 옮겼는지 확인할 것."
                % _HERE, {"failed": bad})
        return mods
    rep.add("kit.modules", "킷 모듈", PASS, "jeet_map_loader / icont / thesis_style")

    if not deep:
        return mods

    def _tail(text, n=3):
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        lines = [l for l in lines if set(l) - set("=-_ ")]   # 장식줄 제거
        return "; ".join(lines[-n:]) if lines else "(출력 없음)"

    try:
        ok, text = _capture(mods["icont"]._self_test)
        ok = bool(ok)
    except Exception as exc:
        rep.add("kit.icont_selftest", "icont --self-test", FAIL,
                "%s: %s" % (type(exc).__name__, exc),
                "python icont.py --self-test 로 상세 출력 확인")
    else:
        rep.add("kit.icont_selftest", "icont --self-test", PASS if ok else FAIL,
                _tail(text, 2) if ok else "실패",
                None if ok else
                "상세:\n" + text.strip() + "\npython icont.py --self-test 재현")

    mp = os.path.normpath(os.path.join(repo, *MAP_REL.split("/")))
    if os.path.isfile(mp):
        try:
            rc, text = _capture(mods["jeet_map_loader"]._self_test, mp)
            ok = (int(rc) == 0)
        except Exception as exc:
            rep.add("kit.map_selftest", "jeet_map_loader --self-test", FAIL,
                    "%s: %s" % (type(exc).__name__, exc),
                    "python jeet_map_loader.py --self-test --repo %s" % repo)
        else:
            rep.add("kit.map_selftest", "jeet_map_loader --self-test",
                    PASS if ok else FAIL, _tail(text, 1) if ok else "실패",
                    None if ok else
                    "상세:\n" + text.strip()
                    + "\npython jeet_map_loader.py --self-test --repo %s 재현" % repo)
    return mods


def check_git(rep, repo):
    rc, out, err = _git(repo, ["rev-parse", "--is-inside-work-tree"])
    if rc != 0:
        rep.add("git.repo", "git 저장소", FAIL,
                "git 저장소가 아니거나 git 이 없다: %s" % (err or out),
                "--repo 가 레포 루트를 가리키는지 확인할 것 (현재 %s)" % repo)
        return
    rc, br, _ = _git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    rc2, head, _ = _git(repo, ["rev-parse", "HEAD"])
    if br == BRANCH:
        rep.add("git.branch", "브랜치", PASS, "%s @ %s" % (br, head[:8]),
                None, {"branch": br, "head": head})
    else:
        rep.add("git.branch", "브랜치", FAIL, "%s (기대 %s) @ %s" % (br, BRANCH, head[:8]),
                "git -C %s checkout %s && git -C %s pull" % (repo, BRANCH, repo),
                {"branch": br, "head": head})

    rc, st, _ = _git(repo, ["status", "--porcelain"])
    lines = [l for l in st.split("\n") if l.strip()]
    if not lines:
        rep.add("git.worktree", "워킹트리", PASS, "clean")
    else:
        rep.add("git.worktree", "워킹트리", WARN,
                "%d 개 변경/미추적 항목" % len(lines),
                "결과 커밋 전에 정리할 것. 첫 5개:\n  " + "\n  ".join(lines[:5]),
                {"n_dirty": len(lines), "head5": lines[:5]})

    name = _git(repo, ["config", "user.name"])[1]
    mail = _git(repo, ["config", "user.email"])[1]
    if name and mail:
        rep.add("git.identity", "커밋 identity", PASS, "%s <%s>" % (name, mail),
                None, {"user.name": name, "user.email": mail})
    else:
        rep.add("git.identity", "커밋 identity", FAIL,
                "user.name=%r user.email=%r" % (name, mail),
                "설정 없이는 git commit 이 exit 128 로 그냥 실패한다:\n"
                "  git -C %s config user.name \"enjoyneer87\"\n"
                "  git -C %s config user.email \"enjoyneer87@naver.com\""
                % (repo, repo), {"user.name": name, "user.email": mail})

    rc, out, err = _git(repo, ["ls-remote", "origin", "refs/heads/" + BRANCH],
                        timeout=40)
    if rc == 0:
        sha = out.split()[0] if out.split() else "(원격에 브랜치 없음)"
        same = (sha == head)
        rep.add("git.remote", "origin 도달", PASS,
                "origin/%s = %s%s" % (BRANCH, sha[:8],
                                      "  (로컬과 동일)" if same else "  (로컬과 다름)"),
                None, {"remote_sha": sha, "in_sync": same})
    else:
        rep.add("git.remote", "origin 도달", WARN,
                "ls-remote 실패 (rc=%s): %s" % (rc, err or out),
                "네트워크/자격증명 문제. push 는 지연이 잦으니 완료 후 반드시 확인:\n"
                "  git -C %s ls-remote origin refs/heads/%s" % (repo, BRANCH))


def check_gitignore(rep, repo):
    ignored, clean, unknown = [], [], []
    for a in ARTEFACTS:
        rel = OUT_REL + "/" + a
        # 판정은 -v 없이. -v 를 붙이면 negation(!) 매칭에도 exit 0 이 나와서
        # 커밋 가능한 PNG 를 '무시됨' 으로 오독한다 (moa 2026-09-07 실측).
        rc, _o, err = _git(repo, ["check-ignore", "--", rel])
        if rc == 0:
            _rc2, out, _e2 = _git(repo, ["check-ignore", "-v", "--", rel])
            ignored.append((rel, out))
        elif rc == 1:
            clean.append(rel)
        else:
            unknown.append((rel, err or out))
    data = {"ignored": [i[0] for i in ignored], "clean": clean,
            "rules": [i[1] for i in ignored], "patch": GITIGNORE_PATCH}
    if unknown:
        rep.add("gitignore", "thesis_out 커밋 가능성", WARN,
                "check-ignore 를 실행하지 못했다: %s" % unknown[0][1],
                "git 이 정상인지 확인할 것", data)
        return
    if not ignored:
        rep.add("gitignore", "thesis_out 커밋 가능성", PASS,
                "산출물 %d 종 모두 커밋된다" % len(clean), None, data)
        return
    rep.add("gitignore", "thesis_out 커밋 가능성", WARN,
            "%d/%d 종이 .gitignore 에 걸린다: %s"
            % (len(ignored), len(ARTEFACTS),
               ", ".join(os.path.basename(i[0]) for i in ignored)),
            "솔브는 돌아가지만 **커밋 단계에서 조용히 빠진다**.\n"
            + "\n".join("  %s" % r for r in data["rules"]) + "\n"
            "조치 (둘 중 하나):\n"
            "  (a) 루트 .gitignore 맨 끝에 다음을 덧붙인다 -- 정식 해법:\n"
            + "".join("      %s\n" % l for l in GITIGNORE_PATCH.rstrip().split("\n"))
            + "  (b) 임시로 git add -f mlxperPJT/thermal/thesis_out/\n"
            "(.gitignore 는 plans/ 밖이라 학위논문 세션은 못 고친다 -- moa 가 한다.)",
            data)


def check_disk(rep, cdb_path, run_dir):
    for cid, label, path, fail_gb, warn_gb in (
            ("disk.cdb", "CDB 드라이브", cdb_path, None, CDB_FREE_WARN_GB),
            ("disk.run", "실행 드라이브", run_dir, RUN_FREE_FAIL_GB, RUN_FREE_WARN_GB)):
        if not path:
            continue
        drive = _drive_of(path)
        u = _free_gb(drive)
        if u is None or u[1] <= 0.0:
            rep.add(cid, label, FAIL, "%s 를 읽을 수 없다 (드라이브 없음?)" % drive,
                    "해당 드라이브가 연결돼 있는지 확인할 것", {"drive": drive})
            continue
        free, total = u
        d = {"drive": drive, "free_GiB": round(free, 2), "total_GiB": round(total, 2)}
        fmt = "%.2f" if min(free, total) < 10.0 else "%.1f"
        msg = ("%s  여유 " + fmt + " / " + fmt + " GiB") % (drive, free, total)
        if total < 1.0:
            # 존재하지 않거나 마운트되지 않은 드라이브가 이렇게 보인다
            # (예: 이 학위논문 PC 의 D: 는 총 0.05 GiB 짜리 유령 볼륨이다).
            rep.add(cid, label, FAIL, msg + "  <- 드라이브가 없거나 마운트되지 않았다",
                    "경로의 드라이브 문자를 확인할 것. CDB 는 %s 에 있어야 한다."
                    % os.path.dirname(DEFAULT_CDB), d)
            continue
        if fail_gb is not None and free < fail_gb:
            rep.add(cid, label, FAIL, msg,
                    "1.11M 절점 정상상태 솔브가 rst/rth/esav 로 수 GB 를 쓴다. "
                    "최소 %g GiB 는 비워 둘 것." % fail_gb, d)
        elif free < warn_gb:
            rep.add(cid, label, WARN, msg,
                    "여유가 빠듯하다 (%g GiB 권장)." % warn_gb, d)
        else:
            rep.add(cid, label, PASS, msg, None, d)


def check_out_dir(rep, repo, fix):
    out = os.path.normpath(os.path.join(repo, *OUT_REL.split("/")))
    if os.path.isdir(out):
        n = len(os.listdir(out))
        rep.add("thesis_out", "thesis_out 디렉터리", PASS,
                "%s (항목 %d 개)" % (out, n), None, {"path": out, "n_items": n})
        return out
    if fix:
        try:
            os.makedirs(out, exist_ok=True)
        except OSError as exc:
            rep.add("thesis_out", "thesis_out 디렉터리", FAIL,
                    "생성 실패: %s" % exc, None, {"path": out})
            return out
        rep.add("thesis_out", "thesis_out 디렉터리", PASS,
                "--fix 로 생성함: %s" % out, None, {"path": out, "created": True})
        return out
    rep.add("thesis_out", "thesis_out 디렉터리", WARN, "없음: %s" % out,
            "--fix 로 자동 생성하거나 직접 만들 것:\n  mkdir \"%s\"" % out,
            {"path": out})
    return out


def check_ansys_env(rep):
    keys = [k for k in os.environ if k.upper().startswith("AWP_ROOT")]
    if "AWP_ROOT261" in os.environ:
        rep.add("env.awp", "AWP_ROOT261", PASS,
                os.environ["AWP_ROOT261"], None,
                {"AWP_ROOT261": os.environ["AWP_ROOT261"]})
    elif keys:
        rep.add("env.awp", "AWP_ROOT261", WARN,
                "v261 은 없고 %s 만 있다" % ", ".join(sorted(keys)),
                "launch_mapdl 이 다른 버전을 잡을 수 있다. "
                "exec_file 을 명시하거나 v261 을 설치할 것.",
                dict((k, os.environ[k]) for k in keys))
    else:
        rep.add("env.awp", "AWP_ROOT261", WARN, "AWP_ROOT* 환경변수가 없다",
                "pymapdl 이 레지스트리에서 찾을 수도 있으니 치명적이진 않다. "
                "실패하면 launch_mapdl(exec_file=r'...\\ANSYS Inc\\v261\\ansys\\bin"
                "\\winx64\\ANSYS261.exe') 로 직접 지정할 것.")


# =========================================================================== #
#  드라이버                                                                   #
# =========================================================================== #

def run(args, rep):
    rep.echo("=" * 74)
    rep.echo("preflight.py  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    rep.echo("repo = %s" % args.repo)
    rep.echo("cdb  = %s" % args.cdb)
    rep.echo("=" * 74)

    rep.echo("")
    rep.echo("[1] python / venv")
    check_python(rep)

    rep.echo("")
    rep.echo("[2] import 프로브 (pyvista / pymapdl 은 몇 초 걸린다)")
    found = check_imports(rep)

    rep.echo("")
    rep.echo("[3] 킷 모듈")
    check_kit_modules(rep, args.deep, args.repo)

    rep.echo("")
    rep.echo("[4] 한글 폰트")
    check_font(rep, "matplotlib" in found)

    rep.echo("")
    rep.echo("[5] 메시 CDB  <-- 1순위 블로커")
    cdb = check_cdb(rep, args.cdb)

    rep.echo("")
    rep.echo("[6] JEET 손실 맵")
    check_map(rep, args.repo)

    rep.echo("")
    rep.echo("[7] git")
    check_git(rep, args.repo)

    rep.echo("")
    rep.echo("[8] .gitignore vs thesis_out 산출물")
    check_gitignore(rep, args.repo)

    rep.echo("")
    rep.echo("[9] 디스크 여유")
    check_disk(rep, cdb or args.cdb, args.repo)

    rep.echo("")
    rep.echo("[10] 출력 디렉터리 / Ansys 환경")
    check_out_dir(rep, args.repo, args.fix)
    check_ansys_env(rep)

    c = rep.counts()
    rc = 1 if c[FAIL] else 0
    rep.echo("")
    rep.echo("=" * 74)
    rep.echo("PASS %d · WARN %d · FAIL %d · INFO %d"
             % (c[PASS], c[WARN], c[FAIL], c[INFO]))
    if c[FAIL]:
        rep.echo("FAIL 항목:")
        for r in rep.rows:
            if r["status"] == FAIL:
                rep.echo("  - %-26s %s" % (r["id"], r["detail"]))
        rep.echo("-> 이 상태로 배치를 돌리면 시간만 버린다. 위 조치부터 할 것.")
    else:
        rep.echo("-> FAIL 없음. 배치를 시작해도 된다."
                 + (" (WARN %d 건은 읽어볼 것)" % c[WARN] if c[WARN] else ""))
    rep.echo("exit %d" % rc)
    return rc


def build_parser():
    repo_default = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir,
                                                os.pardir, os.pardir))
    p = argparse.ArgumentParser(
        prog="preflight.py",
        description="moa 배치 시작 전 30초 환경 게이트. FAIL 이 없으면 exit 0.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--repo", default=repo_default, help="레포 루트")
    p.add_argument("--cdb", default=DEFAULT_CDB,
                   help="ff_e10_mesh_v2 메시 경로 (확장자는 있어도 없어도 된다)")
    p.add_argument("--json", nargs="?", const="-", default=None, metavar="PATH",
                   help="기계용 JSON 출력. 경로 없이 주면 stdout 으로 내보내고 "
                        "사람용 보고는 stderr 로 간다.")
    p.add_argument("--log", default=None, help="사람용 보고를 파일에도 기록")
    p.add_argument("--fix", action="store_true",
                   help="고칠 수 있는 것만 고친다 (지금은 thesis_out 생성뿐). "
                        ".gitignore 는 건드리지 않고 패치문만 출력한다.")
    p.add_argument("--deep", action="store_true",
                   help="킷 모듈의 self-test 까지 돌린다 (몇 초 더)")
    return p


def main(argv=None):
    # parse_args 보다 먼저 해야 --help 의 한글이 cp949 콘솔에서 깨지지 않는다.
    _utf8(sys.stdout)
    _utf8(sys.stderr)
    args = build_parser().parse_args(argv)
    args.repo = os.path.abspath(args.repo)
    json_to_stdout = (args.json == "-")
    stream = sys.stderr if json_to_stdout else sys.stdout

    rep = Report(stream, args.log)
    try:
        rc = run(args, rep)
        if args.json:
            c = rep.counts()
            blob = {
                "_tool": "preflight.py",
                "_generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "repo": args.repo, "cdb_arg": args.cdb,
                "host": {"node": platform.node(),
                         "platform": platform.platform(),
                         "python": sys.version.split()[0],
                         "executable": sys.executable},
                "summary": {"pass": c[PASS], "warn": c[WARN],
                            "fail": c[FAIL], "info": c[INFO]},
                "exit": rc,
                "gitignore_patch": GITIGNORE_PATCH,
                "checks": rep.rows,
            }
            text = json.dumps(blob, ensure_ascii=False, indent=1)
            if json_to_stdout:
                sys.stdout.write(text + "\n")
            else:
                d = os.path.dirname(os.path.abspath(args.json))
                if d and not os.path.isdir(d):
                    os.makedirs(d, exist_ok=True)
                with io.open(args.json, "w", encoding="utf-8") as fh:
                    fh.write(text + "\n")
                rep.echo("JSON: %s (%d B)"
                         % (args.json, os.path.getsize(args.json)))
        return rc
    finally:
        rep.close()


if __name__ == "__main__":
    sys.exit(main())
