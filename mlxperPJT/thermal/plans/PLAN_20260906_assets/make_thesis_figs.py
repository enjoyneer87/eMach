# -*- coding: utf-8 -*-
"""make_thesis_figs.py -- thesis_out 의 JSON 을 학위논문 그림(PNG)으로 굽는다.

계획서 PLAN_20260906_thesis_thermal.md 가 요구하는 4장:

    D1  cont_rating_Tw_vs_I.png     <- e10_cont_rating.json
    D1  cont_rating_Icont_vs_n.png  <- e10_cont_rating.json
    D2  ac_turnwise_hotspot.png     <- e10_ac_turnwise_hotspot.json
    D6  c67_stress_sweep.png        <- c67_stress.json

**Ansys 를 전혀 쓰지 않는다.**  matplotlib + thesis_style 만 쓰므로 논문 PC 에서도
그대로 돌아간다.  moa 는 솔브가 끝난 뒤 이 스크립트만 다시 돌리면 된다.

핵심 성질
---------
* **부분 실행이 정상 동작이다.**  JSON 이 없으면 그 그림만 `SKIP` 하고 나머지를
  계속 굽는다.  D2 가 아직 안 돌았어도 D1 그림은 나온다.  (`--strict` 로 SKIP 을
  실패로 승격할 수 있다.)
* 모든 PNG 는 `thesis_style.savefig_guarded()` 를 통과하므로 **300 KB 이하가 보장**
  되고, 그래도 넘으면 명시적으로 실패한다(조용히 큰 파일을 남기지 않는다).
* 모든 라벨은 `thesis_style.check_label()` 을 통과한다 -> U+2212 MINUS SIGN 이
  섞이면 저장 전에 ValueError.  라벨의 음수 부호는 반드시 ASCII '-' 를 쓸 것.
* stdout 과 `--log` 파일에 동시에 기록한다(무인 배치 실행 대비).

사용법
------
    python make_thesis_figs.py --repo E:/Code_Rep/Thesis_emach
    python make_thesis_figs.py --out .../thesis_out --which d1
    python make_thesis_figs.py --out .../thesis_out --yscale clip --clip-hi 300

종료코드: 0 = 실패 없음, 1 = 하나 이상 실패(또는 --strict 에서 SKIP 발생).

py3.10 안전(match / X|Y 어노테이션 / 3.11+ stdlib 없음).  같은 디렉터리의
thesis_style.py 만 import 한다 -- 레포 상대 sys.path 조작 없음.
"""

import argparse
import io
import json
import math
import os
import sys
import time

# --- 같은 디렉터리 모듈 import (킷은 자기 폴더 안에서 자족한다) --------------
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import thesis_style as ts                       # noqa: E402
import matplotlib.pyplot as plt                 # noqa: E402  (ts 가 Agg 를 이미 설정)
from matplotlib.lines import Line2D             # noqa: E402
from matplotlib.ticker import FuncFormatter, NullFormatter   # noqa: E402


# =========================================================================== #
#  상수                                                                       #
# =========================================================================== #

#: kit dir = <repo>/mlxperPJT/thermal/plans/PLAN_20260906_assets  -> 4단계 위.
#: (moa 가 freeflow/scripts/ 로 승격하면 깊이가 달라진다 -> --repo 가 정본.)
def default_repo_root():
    return os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir,
                                        os.pardir, os.pardir))


OUT_REL = os.path.join("mlxperPJT", "thermal", "thesis_out")

D1_JSON = "e10_cont_rating.json"
D2_JSON = "e10_ac_turnwise_hotspot.json"
D6_JSON = "c67_stress.json"

FIG_D1_TW = "cont_rating_Tw_vs_I.png"
FIG_D1_IC = "cont_rating_Icont_vs_n.png"
FIG_D2 = "ac_turnwise_hotspot.png"
FIG_D6 = "c67_stress_sweep.png"

CASE_ORDER = ("DC", "AC", "AC+")
HSET_ORDER = ("base", "sph")

T_OIL = 70.0                     # degC, 유일한 Dirichlet 노드 (04_mapdl_thermal.py)
GRID_I_LO, GRID_I_HI = 115.075, 460.0     # 계획서 전류 격자의 하/상한

# --- y축 결정 규칙 (계획서가 요구한 '선택하고 주석으로 설명하라') ------------
#
# 16 krpm/460 A 의 동손은 87 kW 로 검증런(3.35 kW)의 26배다.  모델이 온도무관
# 상수물성 선형이라 T_w 가 수백~수천 degC 로 나온다 -- 버그가 아니라 '이 점은
# 연속운전 불가' 라는 결론 그 자체다.  그대로 선형축에 그리면 4개 곡선이 전부
# 천장에 붙어 180 degC 교점(= 그림의 존재 이유)이 안 보인다.
#
# 선택: **auto = 데이터가 요구할 때만 로그축**.
#   - 전 구간 최대가 AUTO_LOG_ABOVE_C 이하면 선형축(읽기 쉬움).
#   - 넘으면 y 로그축.  값이 전부 양수이고 물리적 하한이 오일 70 degC 라서
#     로그축이 잘 정의된다.  70~4000 degC 는 1.76 decade 뿐이라 압축이 과하지
#     않고, 눈금을 70/100/150/180/... 로 직접 박아 온도축처럼 읽힌다.
#     무엇보다 **어떤 값도 잘리지 않는다** -- clip 은 정보를 버린다.
#   - `--yscale clip` 은 계획서가 언급한 대안(180 degC 근방 선형 확대 + 화면
#     밖 최대값을 패널 구석에 주석)으로, 5장 본문 그림용으로 남겨 둔다.
AUTO_LOG_ABOVE_C = 300.0
CLIP_HI_DEFAULT = 260.0
#: 로그축에서 실제로 찍을 눈금 후보(범위 안의 것만 사용).  150(자석 한계)과
#: 180(권선 한계)은 반드시 남기고, 그 사이에 다른 눈금을 넣지 않는다.
YTICKS_LOG = (70, 90, 120, 150, 180, 250, 350, 500, 700, 1000,
              1500, 2200, 3200, 5000, 8000, 12000, 20000)

#: T_w-I 그림의 figsize.  thesis_style.FIGSIZE["grid2x2"]=(6.2,5.0) 은 곡선만 있는
#: 기준 측정치(267 KB)다.  이 그림에는 suptitle + 하단 범례 + I_cont 마커가 더 붙어
#: 같은 크기에서 293 KB(여유 7 KB)까지 올라갔다 -> 줄여서 여유를 확보한다.
#: 실측(합성 64런, dpi 300): (5.9, 4.75) -> 285 KB.  라벨이 더 길어져 300 KB 를
#: 넘더라도 savefig_guarded 가 **dpi 300 을 유지한 채** 팔레트 256 으로 떨어뜨린다
#: (선화라 시각적 손실 없음).  로그의 method=palette 는 실패가 아니다.
FIGSIZE_TW = (5.9, 4.75)

TURN_LABELS = ("T1", "T2", "T3", "T4", "T5", "T6")


# =========================================================================== #
#  유틸                                                                       #
# =========================================================================== #

class Log(object):
    """stdout(또는 stderr) + 파일 동시 기록.  무인 배치용."""

    def __init__(self, path=None, stream=None):
        self.path = path
        self.stream = stream if stream is not None else sys.stdout
        self.fh = None
        if path:
            d = os.path.dirname(os.path.abspath(path))
            if d and not os.path.isdir(d):
                os.makedirs(d, exist_ok=True)
            self.fh = io.open(path, "a", encoding="utf-8")
            self.fh.write("\n==== make_thesis_figs.py %s ====\n"
                          % time.strftime("%Y-%m-%d %H:%M:%S"))

    def __call__(self, msg=""):
        s = msg if isinstance(msg, str) else str(msg)
        try:
            self.stream.write(s + "\n")
            self.stream.flush()
        except Exception:                                # pragma: no cover
            pass
        if self.fh is not None:
            self.fh.write(s + "\n")
            self.fh.flush()

    def close(self):
        if self.fh is not None:
            try:
                self.fh.close()
            except Exception:                            # pragma: no cover
                pass
            self.fh = None


def _utf8_streams():
    """cp949 콘솔에서도 한글이 깨지지 않게."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _finite(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return not (math.isnan(v) or math.isinf(v))


def _fnum(v):
    """축 눈금용 숫자 포맷 (ASCII 만)."""
    a = abs(float(v))
    if a >= 1000:
        return format(int(round(v)), ",")
    if a >= 10:
        return "%d" % int(round(v))
    if a >= 1:
        return "%.0f" % v
    return "%.1f" % v


def _load_json(path):
    """-> (data, why, missing).

    missing=True  : 파일이 없다.  아직 안 돌린 것이니 SKIP (정상 부분 실행).
    missing=False : 파일은 있는데 못 읽는다.  이건 진짜 문제이니 FAIL.
    """
    if not os.path.isfile(path):
        return None, "파일 없음: %s" % path, True
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError as exc:
        return None, "JSON 파싱 실패 (%s): %s" % (exc, path), False
    except (IOError, OSError) as exc:
        return None, "읽기 실패 (%s): %s" % (exc, path), False
    if not isinstance(data, dict):
        return (None, "최상위가 dict 가 아님 (%s): %s" % (type(data).__name__, path),
                False)
    return data, None, False


def _order(present, canonical):
    """canonical 순서를 우선하고, 모르는 값은 정렬해서 뒤에 붙인다."""
    known = [k for k in canonical if k in present]
    extra = sorted([k for k in present if k not in canonical])
    return known + extra


def _speed_key(mapping, speed):
    """I_cont_Arms 의 속도 키는 계획서상 문자열이지만 int 로 올 수도 있다."""
    if not isinstance(mapping, dict):
        return None
    for k in (str(int(round(speed))), str(speed), int(round(speed)), float(speed)):
        if k in mapping:
            return k
    for k in mapping:
        try:
            if abs(float(k) - float(speed)) < 0.5:
                return k
        except (TypeError, ValueError):
            continue
    return None


def _nested3(root, hset, case, speed):
    """root[hset][case][<speed key>] 을 관대하게 읽는다.  없으면 None."""
    if not isinstance(root, dict):
        return None
    a = root.get(hset)
    if not isinstance(a, dict):
        return None
    b = a.get(case)
    if not isinstance(b, dict):
        return None
    k = _speed_key(b, speed)
    return None if k is None else b.get(k)


def _save(fig, path, log, results, dpi, max_bytes):
    """savefig_guarded + 300 KB 검증.  실패하면 RuntimeError."""
    res = ts.savefig_guarded(fig, path, dpi=dpi, max_bytes=max_bytes)
    plt.close(fig)
    kb = res["bytes"] / 1024.0
    log("  저장 %s  %d B (%.1f KB)  dpi=%g  method=%s%s"
        % (os.path.basename(path), res["bytes"], kb, res["dpi"], res["method"],
           "" if res.get("colors") is None else "  palette=%d" % res["colors"]))
    results.append(res)
    if not res["ok"] or res["bytes"] > max_bytes:
        raise RuntimeError(
            "PNG 가 상한을 넘었다: %s = %d B > %d B (attempts: %s). "
            "figsize 를 줄이거나 --dpi 를 낮출 것."
            % (path, res["bytes"], max_bytes, "; ".join(res.get("attempts", []))))
    return res


# =========================================================================== #
#  D1-1  cont_rating_Tw_vs_I.png                                              #
# =========================================================================== #

def fig_d1_tw(data, out_dir, args, log, results):
    """속도별 T_w-I 곡선 2x2.  색=케이스, 선종류=h세트, 180 degC 한계선."""
    runs = data.get("runs")
    if not isinstance(runs, list) or not runs:
        log("  SKIP  'runs' 가 비어 있거나 list 가 아니다 -> %s" % FIG_D1_TW)
        return "skip"

    series = {}            # (speed, case, hset) -> [(I, T), ...]
    n_bad = 0
    for r in runs:
        if not isinstance(r, dict):
            n_bad += 1
            continue
        try:
            sp = int(round(float(r["speed"])))
            cur = float(r["current"])
        except (KeyError, TypeError, ValueError):
            n_bad += 1
            continue
        case = str(r.get("case", "DC"))
        hset = str(r.get("htc", r.get("hset", "base")))
        tc = r.get("T_C")
        if not isinstance(tc, dict):
            n_bad += 1
            continue
        tw = None
        for key in (args.tw_metric, "winding_max", "winding_mean"):
            if _finite(tc.get(key)):
                tw = float(tc[key])
                break
        if tw is None:
            n_bad += 1
            continue
        series.setdefault((sp, case, hset), []).append((cur, tw))
    if n_bad:
        log("  WARN  %d 개 run 을 건너뛰었다 (speed/current/T_C 결측)." % n_bad)
    if not series:
        log("  SKIP  쓸 수 있는 run 이 없다 -> %s" % FIG_D1_TW)
        return "skip"

    speeds = sorted(set(k[0] for k in series))
    cases = _order(set(k[1] for k in series), CASE_ORDER)
    hsets = _order(set(k[2] for k in series), HSET_ORDER)
    cases = [c for c in cases if c in ts.CASE_COLORS] or ["DC"]
    hsets = [h for h in hsets if h in ts.HSET_STYLES] or ["base"]
    dropped = ([c for c in _order(set(k[1] for k in series), CASE_ORDER)
                if c not in ts.CASE_COLORS]
               + [h for h in _order(set(k[2] for k in series), HSET_ORDER)
                  if h not in ts.HSET_STYLES])
    if dropped:
        log("  WARN  규약에 없는 case/h-set 을 무시한다: %s" % sorted(set(dropped)))

    all_I = sorted(set(i for pts in series.values() for (i, _t) in pts))
    all_T = [t for pts in series.values() for (_i, t) in pts]
    tmax, tmin = max(all_T), min(all_T)

    mode = args.yscale
    if mode == "auto":
        mode = "log" if tmax > AUTO_LOG_ABOVE_C else "linear"
    log("  y축 = %s (요청 %s; T_w 범위 %.1f ~ %.1f degC)"
        % (mode, args.yscale, tmin, tmax))

    ncol = 2 if len(speeds) > 1 else 1
    nrow = int(math.ceil(len(speeds) / float(ncol)))
    fig, _axes = plt.subplots(nrow, ncol, figsize=FIGSIZE_TW,
                              sharex=True, sharey=True)
    axs = list(fig.axes)

    icont_root = data.get("I_cont_Arms")
    drew_icont = False

    for idx, sp in enumerate(speeds):
        ax = axs[idx]
        over = []
        for case in cases:
            for hset in hsets:
                pts = series.get((sp, case, hset))
                if not pts:
                    continue
                pts = sorted(pts)
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                ax.plot(xs, ys, zorder=3, **ts.case_style(case, hset))
                if mode == "clip" and max(ys) > args.clip_hi:
                    over.append("%s/%s %s" % (case, hset, _fnum(max(ys))))
                # 180 degC 교점(I_cont)을 한계선 위에 작은 삼각형으로 표시 ->
                # 그림 1 과 그림 2 가 같은 숫자를 가리킨다는 것을 눈으로 확인.
                v = _nested3(icont_root, hset, case, sp)
                if _finite(v) and min(all_I) <= float(v) <= max(all_I):
                    ax.plot([float(v)], [ts.T_LIMIT_WINDING], marker="v",
                            markersize=5.0, linestyle="none", zorder=5,
                            color=ts.CASE_COLORS[case],
                            markerfacecolor=ts.CASE_COLORS[case],
                            markeredgecolor="white", markeredgewidth=0.6)
                    drew_icont = True

        # annotate=False: thesis_style 의 기본 위치(x=0.02)는 곡선이 지나가는
        # 자리다.  라벨은 곡선이 이미 한계선보다 훨씬 위에 있는 오른쪽 끝에 붙인다.
        ts.limit_lines(ax, winding=True, magnet=False, annotate=False)
        if idx == 0:
            ax.text(0.985, ts.T_LIMIT_WINDING,
                    ts.check_label("권선 절연 한계 180 degC"),
                    transform=ax.get_yaxis_transform(), ha="right", va="bottom",
                    fontsize=6.8, color=ts.LIMIT_COLOR, zorder=6)
        ax.grid(True, which="major", color=ts.GRIDC, linewidth=0.5, zorder=0)
        ax.set_title(ts.check_label("%s rpm" % format(int(sp), ",")), pad=4)
        ax.set_xticks(list(all_I))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: _fnum(v)))
        span = max(all_I) - min(all_I)
        ax.set_xlim(min(all_I) - 0.06 * span, max(all_I) + 0.06 * span)

        if mode == "log":
            ax.set_yscale("log")
            ax.set_ylim(max(60.0, tmin * 0.90), tmax * 1.30)
            lo, hi = ax.get_ylim()
            ax.set_yticks([t for t in YTICKS_LOG if lo <= t <= hi])
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: _fnum(v)))
            ax.yaxis.set_minor_formatter(NullFormatter())
        elif mode == "clip":
            ax.set_ylim(T_OIL - 2.0, args.clip_hi)
            if over:
                ax.text(0.975, 0.965,
                        ts.check_label("축 밖 최대 [degC]\n" + "\n".join(over[:4])),
                        transform=ax.transAxes, ha="right", va="top",
                        fontsize=6.0, color=ts.INK2, linespacing=1.25)
        else:
            ax.set_ylim(min(T_OIL - 2.0, tmin - 5.0),
                        max(tmax * 1.08, ts.T_LIMIT_WINDING + 15.0))

    for ax in axs[len(speeds):]:
        ax.set_visible(False)

    # 축 라벨은 바깥쪽 패널에만 (sharex/sharey 라 안쪽은 중복).
    for i, ax in enumerate(axs[:len(speeds)]):
        if i % ncol == 0:
            ax.set_ylabel(ts.check_label("권선 최고온도 T_w [degC]"))
        if i >= len(speeds) - ncol:
            ax.set_xlabel(ts.check_label("상전류 I [A_rms]"))

    handles = ts.legend_handles(cases=cases, hsets=hsets, limit_line=True)
    if drew_icont:
        handles.append(Line2D([], [], color=ts.INK2, marker="v", linestyle="none",
                              markersize=5.0,
                              label=ts.check_label("I_cont (180 degC 교점)")))
    fig.tight_layout(rect=(0.0, 0.115, 1.0, 0.955))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0),
               ncol=2, frameon=False, fontsize=7.2, handlelength=2.6,
               columnspacing=1.4, labelspacing=0.35)
    sub = "%s · %s 축" % (args.tw_metric, {"log": "로그", "clip": "선형(절단)",
                                            "linear": "선형"}.get(mode, mode))
    fig.suptitle(ts.check_label("e10 연속정격 -- 속도별 권선온도 T_w vs 전류  (%s)" % sub),
                 fontsize=10.0, y=0.995)

    return _save(fig, os.path.join(out_dir, FIG_D1_TW), log, results,
                 args.dpi, args.max_bytes)


# =========================================================================== #
#  D1-2  cont_rating_Icont_vs_n.png                                           #
# =========================================================================== #

def fig_d1_icont(data, out_dir, args, log, results):
    """I_cont vs 속도.  x 는 log2(2k/4k/8k/16k 가 정확히 옥타브)."""
    root = data.get("I_cont_Arms")
    if not isinstance(root, dict) or not root:
        log("  SKIP  'I_cont_Arms' 없음 -> %s" % FIG_D1_IC)
        return "skip"
    st_root = data.get("I_cont_status")
    lim_root = data.get("I_cont_limited_by")

    hsets = _order(set(root.keys()), HSET_ORDER)
    hsets = [h for h in hsets if h in ts.HSET_STYLES]
    cases = set()
    speeds = set()
    for h in hsets:
        for c, per_speed in (root.get(h) or {}).items():
            if not isinstance(per_speed, dict):
                continue
            cases.add(c)
            for k in per_speed:
                try:
                    speeds.add(int(round(float(k))))
                except (TypeError, ValueError):
                    continue
    cases = [c for c in _order(cases, CASE_ORDER) if c in ts.CASE_COLORS]
    speeds = sorted(speeds)
    if not (hsets and cases and speeds):
        log("  SKIP  I_cont_Arms 구조를 해석하지 못했다 -> %s" % FIG_D1_IC)
        return "skip"

    fig, ax = plt.subplots(figsize=ts.FIGSIZE["single"])

    allv = []
    n_flag = 0
    sidx = -1
    last_sp = max(speeds)
    for case in cases:
        for hset in hsets:
            sidx += 1
            xs, ys = [], []
            for sp in speeds:
                v = _nested3(root, hset, case, sp)
                if not _finite(v):
                    log("  WARN  I_cont[%s][%s][%s] 가 없거나 유한하지 않다 -> 점 생략"
                        % (hset, case, sp))
                    continue
                xs.append(sp)
                ys.append(float(v))
            if not xs:
                continue
            allv.extend(ys)
            ax.plot(xs, ys, zorder=3, **ts.case_style(case, hset))
            for sp, v in zip(xs, ys):
                stat = _nested3(st_root, hset, case, sp)
                if stat is None or str(stat) == "ok":
                    continue
                n_flag += 1
                # 겹침 회피 3종: (1) 오른쪽 끝 점은 라벨이 축 밖으로 나가므로
                # 왼쪽에 붙인다, (2) extrap_low 는 점 아래(그 아래가 빈 공간),
                # 그 외는 점 위에, (3) 계열마다 세로로 어긋나게 준다.
                right = (sp == last_sp)
                low = "low" in str(stat)
                dy = 5.0 + 6.5 * (sidx % 3)
                ax.annotate(
                    ts.check_label(str(stat)), xy=(sp, v),
                    xytext=(-5 if right else 5, -dy if low else dy),
                    textcoords="offset points",
                    ha="right" if right else "left",
                    va="top" if low else "bottom", fontsize=6.2,
                    color=ts.CASE_COLORS[case], zorder=6, annotation_clip=False)

    if not allv:
        plt.close(fig)
        log("  SKIP  유한한 I_cont 값이 하나도 없다 -> %s" % FIG_D1_IC)
        return "skip"

    ts.speed_axis(ax, speeds=tuple(speeds),
                  xlim=(min(speeds) / 1.18, max(speeds) * 1.18))
    # y 범위는 데이터가 정한다.  계획서 격자(115-460 A)를 음영으로 깔면 데이터가
    # 아래 20 %에 몰려버리므로, 격자 경계는 '선 + 인라인 라벨' 로만 표시한다.
    lo = min(allv) * 0.88
    hi = max(allv) * 1.30
    for bound, txt in ((GRID_I_LO, "계획서 전류 격자 하한 115.075 A"),
                       (GRID_I_HI, "계획서 전류 격자 상한 460 A")):
        if lo <= bound <= hi:
            ax.axhline(bound, color=ts.INK2, lw=0.8, ls=(0, (5, 4)), zorder=1)
            # 왼쪽에 붙인다 -- 오른쪽 끝은 status 주석이 쓰는 자리다.
            ax.text(0.015, bound, ts.check_label(txt),
                    transform=ax.get_yaxis_transform(), ha="left", va="bottom",
                    fontsize=6.4, color=ts.INK2, zorder=6)
    ax.set_ylim(max(0.0, lo), hi)
    ax.grid(True, which="major", color=ts.GRIDC, linewidth=0.5, zorder=0)
    ax.set_xlabel(ts.check_label("회전속도 n [rpm]  (log2 축)"))
    ax.set_ylabel(ts.check_label("연속 전류 I_cont [A_rms]"))
    ax.set_title(ts.check_label(
        "e10 연속 정격 전류 -- 권선 180 degC / 자석 150 degC 중 낮은 쪽"), pad=6)

    handles = ts.legend_handles(cases=cases, hsets=hsets, limit_line=False)
    ax.legend(handles=handles, loc="upper left", fontsize=7.0, frameon=False,
              handlelength=2.6, labelspacing=0.35)

    if n_flag:
        log("  주의  status != 'ok' 인 점 %d 개를 그림에 표기했다 "
            "(격자 밖 외삽 등)." % n_flag)
    lb = []
    for hset in hsets:
        for case in cases:
            for sp in speeds:
                w = _nested3(lim_root, hset, case, sp)
                if w:
                    lb.append(str(w))
    if lb:
        uniq = sorted(set(lb))
        log("  limited_by 분포: %s"
            % ", ".join("%s x%d" % (u, lb.count(u)) for u in uniq))

    return _save(fig, os.path.join(out_dir, FIG_D1_IC), log, results,
                 args.dpi, args.max_bytes)


# =========================================================================== #
#  D2  ac_turnwise_hotspot.png                                                #
# =========================================================================== #

def fig_d2(data, out_dir, args, log, results):
    """턴별(T1 공극측 ... T6 요크측) 온도, 균일 주입 vs 턴별 주입, 전류 2점."""
    runs = data.get("runs")
    if not isinstance(runs, list) or not runs:
        log("  SKIP  'runs' 없음 -> %s" % FIG_D2)
        return "skip"

    by_cur = {}           # current -> {mode -> run}
    for r in runs:
        if not isinstance(r, dict):
            continue
        try:
            cur = float(r["current"])
        except (KeyError, TypeError, ValueError):
            continue
        mode = str(r.get("mode", r.get("injection", "turnwise"))).lower()
        if mode not in ("uniform", "turnwise"):
            continue
        by_cur.setdefault(round(cur, 6), {})[mode] = r

    def _turns(run):
        tt = run.get("turn_T_C")
        if not isinstance(tt, dict):
            return None
        v = tt.get(args.turn_metric)
        if v is None:
            for alt in ("mean", "max"):
                if isinstance(tt.get(alt), list):
                    v = tt[alt]
                    break
        if not isinstance(v, list) or not v:
            return None
        out = []
        for x in v:
            if not _finite(x):
                return None
            out.append(float(x))
        return out

    cols = []
    for cur in sorted(by_cur):
        pair = by_cur[cur]
        u = _turns(pair["uniform"]) if "uniform" in pair else None
        t = _turns(pair["turnwise"]) if "turnwise" in pair else None
        if u is None or t is None or len(u) != len(t):
            log("  WARN  %.3f A: uniform/turnwise 의 turn_T_C[%s] 쌍이 없다 -> 패널 생략"
                % (cur, args.turn_metric))
            continue
        cols.append((cur, pair, u, t))
    if not cols:
        log("  SKIP  균일/턴별 쌍이 하나도 없다 -> %s" % FIG_D2)
        return "skip"

    n = len(cols)
    figsize = ts.FIGSIZE["wide2panel"] if n >= 2 else ts.FIGSIZE["single"]
    fig, _axes = plt.subplots(1, n, figsize=figsize)
    axs = list(fig.axes)

    c_uni = ts.CASE_COLORS["DC"]        # 회색 = 균일(기존 관행)
    c_tw = ts.CASE_COLORS["AC"]         # 파랑 = 턴별(제안 기법)

    for ax, (cur, pair, u, t) in zip(axs, cols):
        nt = len(u)
        labels = [TURN_LABELS[i] if i < len(TURN_LABELS) else "T%d" % (i + 1)
                  for i in range(nt)]
        xs = list(range(nt))
        w = 0.38
        # 막대 밑변을 오일 70 degC 로 두면 막대 높이가 그대로 '온도 상승' 이다.
        ax.bar([x - w / 2.0 for x in xs], [v - T_OIL for v in u], width=w,
               bottom=T_OIL, color=c_uni, edgecolor=ts.INK, linewidth=0.5,
               label=ts.check_label("균일 주입"), zorder=3)
        ax.bar([x + w / 2.0 for x in xs], [v - T_OIL for v in t], width=w,
               bottom=T_OIL, color=c_tw, edgecolor=ts.INK, linewidth=0.5,
               label=ts.check_label("턴별 주입"), zorder=3)

        d1 = t[0] - u[0]
        ax.annotate(ts.check_label("핫스팟 누락\n%s%.0f K" % ("+" if d1 >= 0 else "-",
                                                              abs(d1))),
                    xy=(0 + w / 2.0, t[0]), xytext=(0.30, 0.93),
                    textcoords="axes fraction", ha="left", va="top",
                    fontsize=7.2, color=ts.CASE_COLORS["AC+"], linespacing=1.2,
                    arrowprops=dict(arrowstyle="-|>", lw=0.9,
                                    color=ts.CASE_COLORS["AC+"],
                                    shrinkA=1.0, shrinkB=2.0))

        ts.limit_lines(ax, winding=True, magnet=False, annotate=False)
        ax.set_xticks(xs)
        ax.set_xticklabels([ts.check_label(s) for s in labels])
        ax.grid(True, axis="y", color=ts.GRIDC, linewidth=0.5, zorder=0)
        top = max(max(u), max(t), ts.T_LIMIT_WINDING)
        ax.set_ylim(T_OIL, T_OIL + (top - T_OIL) * 1.30)
        ax.set_xlabel(ts.check_label("턴 인덱스  T1 = 공극측 -> T6 = 요크측"))

        # 권선 최고온도는 패널 안 텍스트로 두면 막대와 겹친다 -> 제목 둘째 줄.
        wm = []
        for mode, key in (("균일", "uniform"), ("턴별", "turnwise")):
            tc = pair[key].get("T_C")
            v = tc.get("winding_max") if isinstance(tc, dict) else None
            if _finite(v):
                wm.append("%s %s" % (mode, _fnum(v)))
        title = "%s A_rms" % _fnum(cur)
        if wm:
            title += "\n권선 최고 [degC]  " + " / ".join(wm)
        ax.set_title(ts.check_label(title), pad=4, fontsize=9.0)

    axs[0].set_ylabel(ts.check_label(
        "턴 %s 온도 [degC]" % ("평균" if args.turn_metric == "mean" else "최고")))
    axs[0].legend(loc="upper right", fontsize=7.0, frameon=False)
    for ax in axs[len(cols):]:
        ax.set_visible(False)
    fig.suptitle(ts.check_label(
        "e10 슬롯 내 AC 동손 분포 -- 균일 주입은 공극측 핫스팟을 놓친다"
        "   (막대 밑변 = 오일 70 degC)"), fontsize=9.5, y=0.995)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.955))

    return _save(fig, os.path.join(out_dir, FIG_D2), log, results,
                 args.dpi, args.max_bytes)


# =========================================================================== #
#  D6  c67_stress_sweep.png                                                   #
# =========================================================================== #

_SVM_KEYS = ("max_von_mises_MPa", "max_svm_MPa", "von_mises_MPa")
_UR_KEYS = ("max_radial_disp_mm", "max_ur_mm", "delta_r_mm", "radial_disp_mm")
#: d6_c67_stress.py 는 _model_meta.yield_MPa 로 쓰고, D6 조사보고서 스키마는
#: yield_stress_MPa 로 적어 두었다.  둘 다 받는다 (없으면 항복선을 안 그린다).
_YIELD_KEYS = ("yield_stress_MPa", "yield_MPa")


def _pick(d, keys):
    for k in keys:
        if isinstance(d, dict) and _finite(d.get(k)):
            return float(d[k])
    return None


def fig_d6(data, out_dir, args, log, results):
    """rpm 스윕의 최대 von Mises 와 반경변위 delta_r 을 쌍축으로."""
    sweep = data.get("sweep")
    pts = sweep.get("points") if isinstance(sweep, dict) else None
    rows = []
    if isinstance(pts, list):
        for p in pts:
            if not isinstance(p, dict) or not _finite(p.get("rpm")):
                continue
            s = _pick(p, _SVM_KEYS)
            u = _pick(p, _UR_KEYS)
            if s is None and u is None:
                continue
            rows.append((float(p["rpm"]), s, u, p.get("safety_factor")))
    if len(rows) < 2:
        log("  SKIP  sweep.points 에 유효한 점이 2개 미만이다 -> %s" % FIG_D6)
        return "skip"
    rows.sort()

    rpm = [r[0] for r in rows]
    svm = [r[1] for r in rows]
    ur = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=ts.FIGSIZE["single"])
    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)      # apply() 가 껐던 것을 되살린다

    c_s = ts.CASE_COLORS["AC"]
    c_u = ts.CASE_COLORS["AC+"]
    h = []
    # 두 축 모두 0 에서 시작시킨다.  (a) sigma 와 delta_r 은 원심하중에서 n^2 에
    # 비례하므로 0 기준이라야 2차 곡률이 보인다.  (b) _method='scale' 스윕에서는
    # 두 계열이 정확히 같은 비율로 커져서, 축을 각자 자동스케일하면 두 곡선이
    # 완전히 포개진다 -- 위쪽 여유(1.18 vs 1.45)를 다르게 줘서 분리한다.
    top_s = top_u = None
    if any(v is not None for v in svm):
        xs = [x for x, v in zip(rpm, svm) if v is not None]
        ys = [v for v in svm if v is not None]
        ax.plot(xs, ys, color=c_s, linestyle="-", marker="o", markersize=4.2,
                markerfacecolor="white", markeredgecolor=c_s, zorder=3)
        h.append(Line2D([], [], color=c_s, linestyle="-", marker="o",
                        markersize=4.2, markerfacecolor="white",
                        label=ts.check_label("최대 von Mises [MPa]")))
        top_s = max(ys) * 1.18
    if any(v is not None for v in ur):
        xs = [x for x, v in zip(rpm, ur) if v is not None]
        ys = [v for v in ur if v is not None]
        ax2.plot(xs, ys, color=c_u, linestyle="--", marker="s", markersize=4.0,
                 markerfacecolor="none", markeredgecolor=c_u, zorder=3)
        h.append(Line2D([], [], color=c_u, linestyle="--", marker="s",
                        markersize=4.0, markerfacecolor="none",
                        label=ts.check_label("최대 반경변위 delta_r [mm]")))
        top_u = max(ys) * 1.45

    meta = data.get("_model_meta")
    ysd = _pick(meta, _YIELD_KEYS)
    if ysd is None:
        ysd = _pick(data, _YIELD_KEYS)
    if _finite(ysd):
        # 한계선을 thesis_style.LIMIT_COLOR(빨강)로 두면 delta_r 계열(AC+ 빨강)과
        # 색이 겹친다.  구조 그림에는 케이스 색 규약이 적용되지 않으므로 한계선은
        # 먹색 점선으로 뽑는다 -- 흑백에서도 파랑/빨강/먹 3단 분리가 유지된다.
        ax.axhline(float(ysd), color=ts.INK, lw=1.2, ls=":", zorder=2)
        h.append(Line2D([], [], color=ts.INK, lw=1.2, ls=":",
                        label=ts.check_label("항복강도 %s MPa" % _fnum(ysd))))
        if top_s is not None:
            top_s = max(top_s, float(ysd) * 1.12)
        cross = [r[0] for r in rows if r[1] is not None and r[1] >= float(ysd)]
        if cross:
            log("  주의  von Mises 가 항복강도 %s MPa 를 넘는 속도: %s rpm"
                % (_fnum(ysd), ", ".join(_fnum(c) for c in cross)))
    else:
        log("  주의  _model_meta 의 항복강도(%s)가 null 이다 "
            "(20PN1150F 데이터시트 값은 논문 쪽에서 채운다) -> 항복선 생략."
            % " / ".join(_YIELD_KEYS))

    rated = data.get("at_rated")
    rr = rated.get("rpm") if isinstance(rated, dict) else None
    if _finite(rr) and min(rpm) <= float(rr) <= max(rpm):
        ax.axvline(float(rr), color=ts.INK2, lw=0.8, ls="-.", zorder=1)
        ax.annotate(ts.check_label("정격 %s rpm" % format(int(round(rr)), ",")),
                    xy=(float(rr), 1.0), xycoords=ax.get_xaxis_transform(),
                    xytext=(3, -10), textcoords="offset points",
                    fontsize=6.6, color=ts.INK2, ha="left", va="top")

    if top_s is not None:
        ax.set_ylim(0.0, top_s)
    if top_u is not None:
        ax2.set_ylim(0.0, top_u)
    ax.grid(True, which="major", color=ts.GRIDC, linewidth=0.5, zorder=0)
    ax.set_xlabel(ts.check_label("회전속도 n [rpm]"))
    ax.set_ylabel(ts.check_label("최대 von Mises 응력 [MPa]"), color=c_s)
    ax2.set_ylabel(ts.check_label("최대 반경변위 delta_r [mm]"), color=c_u)
    ax.tick_params(axis="y", colors=c_s)
    ax2.tick_params(axis="y", colors=c_u)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: _fnum(v)))
    ax.set_xticks(rpm)
    span = max(rpm) - min(rpm)
    ax.set_xlim(min(rpm) - 0.08 * span, max(rpm) + 0.08 * span)
    ax.set_title(ts.check_label("C67 회전자 원심 해석 -- 속도 스윕"), pad=6)
    ax.legend(handles=h, loc="upper left", fontsize=7.0, frameon=False,
              handlelength=2.6)

    method = sweep.get("_method") if isinstance(sweep, dict) else None
    if method:
        ax.text(0.985, 0.02, ts.check_label("sweep _method = %s" % method),
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=6.2, color=ts.INK2)
        if "scal" in str(method).lower():
            log("  주의  스윕이 omega^2 해석 스케일링이다 -- 선형탄성/bonded/NLGEOM off "
                "전제에서만 정확하고, Neuber/Glinka 소성보정값에는 적용 불가.")
    fig.tight_layout()

    return _save(fig, os.path.join(out_dir, FIG_D6), log, results,
                 args.dpi, args.max_bytes)


# =========================================================================== #
#  드라이버                                                                   #
# =========================================================================== #

def _meta_line(data, log):
    """계획서 §3 필수키를 확인하고 찍는다 -- '손실 출처 불명' 재발 방지."""
    miss = [k for k in ("_loss_source", "_htc", "_soltype") if k not in data]
    for k in ("_soltype", "_loss_source", "_htc", "_model"):
        if k in data:
            v = data[k]
            s = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) \
                else str(v)
            if len(s) > 160:
                s = s[:157] + "..."
            log("  %-13s %s" % (k, s))
    if miss:
        log("  WARN  계획서 §3 필수키 누락: %s" % ", ".join(miss))
    if "_loss_model_caveat" in data:
        log("  caveat        %s" % str(data["_loss_model_caveat"])[:200])
    sup = data.get("_superposition_check")
    if isinstance(sup, dict):
        log("  superposition ok=%s  max_abs_err_K=%s"
            % (sup.get("ok"), sup.get("max_abs_err_K")))


def build(args, log):
    """요청된 그림을 굽는다.  반환 (n_ok, n_skip, n_fail, results)."""
    ts.apply()
    log("폰트: %s" % ts.active_font())
    if ts.active_font() != "Malgun Gothic":
        log("WARN  Malgun Gothic 이 아니다 -- 한글이 네모로 나올 수 있다. "
            "moa 에서는 반드시 Malgun Gothic 이어야 한다.")

    out_dir = args.out
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        log("생성: %s" % out_dir)
    log("출력 디렉터리: %s" % out_dir)

    want = args.which
    jobs = []
    if want in ("all", "d1"):
        jobs.append(("D1", D1_JSON, (fig_d1_tw, fig_d1_icont)))
    if want in ("all", "d2"):
        jobs.append(("D2", D2_JSON, (fig_d2,)))
    if want in ("all", "d6"):
        jobs.append(("D6", D6_JSON, (fig_d6,)))

    results = []
    n_ok = n_skip = n_fail = 0
    for tag, jname, fns in jobs:
        path = os.path.join(out_dir, jname)
        log("")
        log("[%s] %s" % (tag, jname))
        data, why, missing = _load_json(path)
        if data is None and missing:
            log("  SKIP  %s" % why)
            log("        -> moa 가 아직 %s 산출물을 만들지 않았거나 --out 경로가 "
                "틀렸다. 나머지 그림은 계속 굽는다." % tag)
            n_skip += len(fns)
            continue
        if data is None:
            # 파일은 있는데 못 읽는다 -> 러너가 중간에 죽었거나 손상됐다.  실패다.
            log("  FAIL  %s" % why)
            log("        -> %s 러너를 다시 돌려 JSON 을 새로 쓸 것. "
                "(부분 기록된 파일일 가능성이 높다.)" % tag)
            n_fail += len(fns)
            continue
        _meta_line(data, log)
        for fn in fns:
            try:
                r = fn(data, out_dir, args, log, results)
            except Exception as exc:                     # 한 그림의 실패가 배치를 죽이지 않게
                n_fail += 1
                log("  FAIL  %s: %s: %s" % (fn.__name__, type(exc).__name__, exc))
                if args.traceback:
                    import traceback
                    traceback.print_exc()
                continue
            if r == "skip":
                n_skip += 1
            else:
                n_ok += 1
    return n_ok, n_skip, n_fail, results


def build_parser():
    repo = default_repo_root()
    p = argparse.ArgumentParser(
        prog="make_thesis_figs.py",
        description="thesis_out JSON -> 학위논문 그림 PNG (D1/D2/D6). Ansys 불필요.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--repo", default=repo,
                   help="레포 루트 (--out 의 기본값 계산에만 쓴다)")
    p.add_argument("--out", default=None,
                   help="thesis_out 디렉터리 (기본: <repo>/%s)" % OUT_REL.replace("\\", "/"))
    p.add_argument("--which", default="all", choices=("all", "d1", "d2", "d6"),
                   help="어떤 산출물의 그림을 그릴지")
    p.add_argument("--log", default=None, help="로그 파일 (stdout 과 동시 기록)")
    p.add_argument("--dpi", type=float, default=300.0, help="저장 dpi (상한 초과 시 자동 하향)")
    p.add_argument("--max-bytes", type=int, default=ts.PNG_MAX_BYTES,
                   dest="max_bytes", help="PNG 크기 상한 [byte]")
    p.add_argument("--yscale", default="auto", choices=("auto", "log", "linear", "clip"),
                   help="T_w-I 그림의 y축. auto = 최대 %g degC 초과면 log" % AUTO_LOG_ABOVE_C)
    p.add_argument("--clip-hi", type=float, default=CLIP_HI_DEFAULT, dest="clip_hi",
                   help="--yscale clip 일 때 y 상한 [degC]")
    p.add_argument("--tw-metric", default="winding_max",
                   choices=("winding_max", "winding_mean"), dest="tw_metric",
                   help="T_w-I 그림에 쓸 T_C 키")
    p.add_argument("--turn-metric", default="mean", choices=("mean", "max"),
                   dest="turn_metric", help="D2 턴별 온도로 쓸 turn_T_C 키")
    p.add_argument("--strict", action="store_true",
                   help="JSON 결측(SKIP)도 실패로 취급해 종료코드 1")
    p.add_argument("--traceback", action="store_true", help="실패 시 트레이스백 출력")
    return p


def main(argv=None):
    _utf8_streams()
    args = build_parser().parse_args(argv)
    if args.out is None:
        args.out = os.path.join(args.repo, OUT_REL)
    args.out = os.path.abspath(args.out)

    log = Log(args.log)
    try:
        log("make_thesis_figs.py  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log("python %s" % sys.version.split()[0])
        log("repo   %s" % args.repo)
        n_ok, n_skip, n_fail, results = build(args, log)

        log("")
        log("=" * 66)
        log("생성 %d · 건너뜀 %d · 실패 %d" % (n_ok, n_skip, n_fail))
        for r in results:
            log("  %-28s %8d B  (%5.1f KB)  dpi=%-5g %s"
                % (os.path.basename(r["path"]), r["bytes"], r["bytes"] / 1024.0,
                   r["dpi"], "OK" if r["ok"] else "OVER"))
        if n_skip and not args.strict:
            log("SKIP 은 실패가 아니다 -- 해당 JSON 이 생기면 이 스크립트를 다시 돌리면 된다.")
        rc = 1 if (n_fail or (args.strict and n_skip)) else 0
        log("exit %d" % rc)
        return rc
    finally:
        log.close()


if __name__ == "__main__":
    sys.exit(main())
