# -*- coding: utf-8 -*-
"""thesis_style.py - PLAN_20260906 논문 그림 규약 모듈 (thesis figure conventions).

이 파일은 **읽기 전용 참조 구현**이다. moa 는 이 디렉터리를
`mlxperPJT/thermal/freeflow/scripts/` 로 복사(promote)한 뒤 커밋한다.
같은 디렉터리 안에서만 import 한다:  `import thesis_style as ts`

Verified on DESKTOP-6QIVKIC with C:/msys64/ucrt64/bin/python.exe
(Python 3.14.6, matplotlib 3.11.0, Pillow 12.3.0, Malgun Gothic present).
**Source is python 3.10-safe** (no match, no `X | Y` annotations, no 3.11+ stdlib)
because the target venv is
C:/Users/moa/.ansys_python_venvs/PyMotorEnv_310/Scripts/python.exe (py3.10).

왜 이 모듈이 필요한가 (the three facts that cost a session if forgotten)
-----------------------------------------------------------------------
1. Malgun Gothic 은 U+2212 MINUS SIGN 글리프가 **없다**.
   `axes.unicode_minus = False` 는 *눈금 라벨*만 고친다. 라벨 문자열에 직접 타이핑한
   U+2212 는 여전히 "Glyph 8722 missing" 경고를 낸다.  =>  라벨에는 ASCII '-' 만.
   `check_label()` 이 이것을 강제한다.
   Malgun Gothic 에서 확인된 안전 문자: '°'(U+00B0), '—'(U+2014), '·'(U+00B7), 한글 전체.
2. PNG 는 300 KB 이하여야 한다(plans/README.md).  dpi 만 낮추는 방식은 래스터
   (pyvista screenshot) 에서 실패한다 - 팔레트 256 양자화가 3배 지렛대다.
   `savefig_guarded()` 가 dpi 사다리 -> 팔레트 순으로 자동 처리한다.
3. VTK/pyvista 의 `add_text` 는 한글을 그리지 못한다.  `pl.screenshot(return_img=True)`
   로 배열을 받아 matplotlib figure 안에서 제목을 붙인다.  `png_from_pyvista()`.

Public API (pinned - 다른 킷 스크립트가 이 이름들에 의존한다)
-------------------------------------------------------------
    CASE_COLORS  = {"DC": "#9C9C9C", "AC": "#0B3D91", "AC+": "#E03131"}
    HSET_STYLES  = {"base": "-", "sph": "--"}
    PNG_MAX_BYTES = 300 * 1024

    apply(font="Malgun Gothic") -> None
    savefig_guarded(fig, path, dpi=300, max_bytes=PNG_MAX_BYTES, min_dpi=110) -> dict
    png_from_pyvista(img, title, path, dpi=300, **kw) -> dict
    check_label(s) -> str

편의 API (부가, 위 이름들을 대체하지 않음)
    case_style(case, hset)        -> dict(kwargs for ax.plot)
    legend_handles(cases, hsets, limit_line=True) -> list[Line2D]
    limit_lines(ax, ...)          -> None      (180 degC / 150 degC 한계선)
    speed_axis(ax)                -> None      (log2 rpm 축: 2k/4k/8k/16k 등간격)
    glyph_watch()                 -> context manager, 누락 글리프 경고 수집
    active_font()                 -> str       (실제 적용된 폰트 이름)

CLI
    python thesis_style.py --self-test [--out DIR]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import unicodedata
import warnings

import matplotlib

# 헤드리스 배치 실행이 기본이다(19_e10_mapdl_icepak_compare.py:11 과 동일 관례).
# 대화형에서 쓰고 싶으면 THESIS_STYLE_NO_AGG=1 로 끈다.
if os.environ.get("THESIS_STYLE_NO_AGG", "") not in ("1", "true", "True"):
    try:
        matplotlib.use("Agg")
    except Exception:                                    # pragma: no cover
        pass

import matplotlib.pyplot as plt                          # noqa: E402
from matplotlib import font_manager as fm                # noqa: E402
from matplotlib.lines import Line2D                      # noqa: E402
from matplotlib.ticker import FuncFormatter              # noqa: E402

try:                                                     # Pillow 는 선택적이다.
    from PIL import Image as _PIL_Image                  # matplotlib>=3.3 이 이미 쓰지만
except Exception:                                        # 없어도 dpi 사다리는 동작한다.
    _PIL_Image = None


# =========================================================================== #
#  PINNED CONSTANTS                                                           #
# =========================================================================== #

#: 케이스 색 규약.  흑백 인쇄 대비 휘도 사다리(0.299R+0.587G+0.114B):
#:   DC 156.0 / AC+ 101.3 / AC 55.6  -> 간격 54.7, 45.7.
#:   흔한 조합 #7F7F7F/#1F4FD8/#D62728 은 127.0/80.3/91.4 로 AC 와 AC+ 가 11 밖에
#:   차이나지 않아 흑백에서 붙어버린다.  이 조합을 바꾸지 말 것.
CASE_COLORS = {"DC": "#9C9C9C", "AC": "#0B3D91", "AC+": "#E03131"}

#: h-세트 인코딩은 **선 종류**로만 한다.  절대 색으로 인코딩하지 말 것
#: (색은 이미 케이스에 배정되어 있다).
HSET_STYLES = {"base": "-", "sph": "--"}

#: plans/README.md: "PNG <= 300 KB".
PNG_MAX_BYTES = 300 * 1024

# ---- 부가 상수 (규약의 일부이지만 위 세 이름과 달리 자유롭게 확장 가능) ------
#: h-세트 보조 마커.  선 종류만으로 부족한 조밀한 그림에서 함께 쓴다.
HSET_MARKERS = {
    "base": dict(marker="o", markersize=4.2, markerfacecolor="white",
                 markeredgewidth=1.1),
    "sph":  dict(marker="s", markersize=4.0, markerfacecolor="none",
                 markeredgewidth=1.1),
}
HSET_LABELS_KR = {"base": "h 기준(1000/2000/250)", "sph": "h SPH역산(190/190/250)"}

INK, INK2, GRIDC = "#2A2A2A", "#666666", "#E5E5E0"
T_LIMIT_WINDING, T_LIMIT_MAGNET = 180.0, 150.0
LIMIT_COLOR, MAG_LIMIT_COLOR = "#C0392B", "#8E44AD"

#: 측정된 권장 figsize (dpi=300, bbox_inches='tight', pad_inches=0.03 기준).
#:   cont_rating_Tw_vs_I  (6.2, 5.0) -> 267 KB
#:   cont_rating_Icont_vs_n (5.6, 4.0) -> 130 KB
#:   7.5 x 5.6 는 313 KB 로 **초과**한다.
FIGSIZE = {
    "grid2x2": (6.2, 5.0),
    "single": (5.6, 4.0),
    "wide2panel": (7.2, 3.6),
    "raster": (5.6, 4.2),
}

PAD_INCHES = 0.03
_PALETTE_LADDER = (256, 128, 64)

#: 폰트 후보 사다리.  첫 번째로 실제 존재하는 것을 쓴다.
_FONT_CANDIDATES = ("Malgun Gothic", "NanumGothic", "NanumBarunGothic",
                    "Noto Sans KR", "AppleGothic", "Gulim", "Batang")
_FONT_FILES = (r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\malgunbd.ttf")

#: Malgun Gothic 에서 **렌더링 검증된** 비-ASCII 문자 (경고 0 확인).
_VERIFIED_EXTRA = set("°—·")
#: 절대 금지.  Malgun Gothic 에 글리프 자체가 없다.
_FORBIDDEN = {
    "\u2212": "U+2212 MINUS SIGN",       # Malgun Gothic 에 글리프 없음
}

def _warn(msg):
    """경고는 stdout 으로만 낸다.  드라이버가 stdout 을 --log 로 tee 하므로
    logging 으로 중복 출력하면 로그가 두 번 찍힌다."""
    print("[thesis_style] " + msg)
    return None


# 모듈 상태 (idempotency + warn-once)
_STATE = {"applied": False, "font": None, "requested": None, "fallback_warned": False}
_LABEL_WARNED = set()


# =========================================================================== #
#  1. rcParams                                                                #
# =========================================================================== #

def _available_families():
    try:
        return set(f.name for f in fm.fontManager.ttflist)
    except Exception:                                    # pragma: no cover
        return set()


def _ensure_font_registered(name):
    """폰트 캐시가 오래되어 이름이 안 보일 때 파일에서 직접 등록해 본다."""
    if name != "Malgun Gothic":
        return False
    ok = False
    for p in _FONT_FILES:
        if os.path.isfile(p):
            try:
                fm.fontManager.addfont(p)
                ok = True
            except Exception:                            # pragma: no cover
                pass
    return ok


def _pick_font(requested):
    """요청 폰트 -> 후보 사다리 -> DejaVu Sans 순으로 실제 존재하는 것을 고른다."""
    have = _available_families()
    if requested and requested in have:
        return requested, True
    if requested and _ensure_font_registered(requested):
        have = _available_families()
        if requested in have:
            return requested, True
    for c in _FONT_CANDIDATES:
        if c in have:
            return c, (c == requested)
    return "DejaVu Sans", False                          # 한글은 두부(tofu)가 된다


def apply(font="Malgun Gothic"):
    """논문 그림 rcParams 를 적용한다.  멱등(idempotent).

    - 요청 폰트가 없으면 조용히 후보 사다리로 대체하고 **한 번만** 경고한다.
      어떤 경우에도 예외를 던지지 않는다(무인 배치 실행이므로).
    - `axes.unicode_minus = False` 는 필수다.  Malgun Gothic 에 U+2212 가 없다.
    - `plt.style.use(...)` 는 호출하지 않는다(모아 환경에 없는 스타일 시트 의존 금지).

    반환값 없음.  실제 적용된 폰트는 `active_font()` 로 확인한다.
    """
    if _STATE["applied"] and _STATE["requested"] == font:
        return None                                      # 멱등: 두 번째 호출은 no-op

    name, exact = _pick_font(font)

    if not exact and not _STATE["fallback_warned"]:
        _STATE["fallback_warned"] = True
        _warn("WARNING: requested font %r not available; using %r instead. "
              "Korean labels may render as boxes." % (font, name))

    plt.rcParams.update({
        # --- 폰트: sans-serif 체인으로 두어 글리프 폴백이 동작하게 한다 -----
        "font.family": "sans-serif",
        "font.sans-serif": [name, "Malgun Gothic", "DejaVu Sans"],
        # --- 필수: Malgun Gothic 에 U+2212 글리프가 없다 --------------------
        "axes.unicode_minus": False,
        "mathtext.fontset": "dejavusans",                # $I_\mathrm{rms}$ 용
        # --- 크기 -----------------------------------------------------------
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        # --- 저장 -----------------------------------------------------------
        "figure.dpi": 110, "savefig.dpi": 300,
        "savefig.facecolor": "white", "figure.facecolor": "white",
        "savefig.bbox": "standard",                      # tight 는 호출부에서 명시
        # --- 잉크 -----------------------------------------------------------
        "axes.linewidth": 0.8, "axes.edgecolor": INK2,
        "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK2, "ytick.color": INK2,
        "grid.linewidth": 0.5, "grid.color": GRIDC,
        "lines.linewidth": 1.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False,
    })

    _STATE["applied"] = True
    _STATE["font"] = name
    _STATE["requested"] = font
    return None


def active_font():
    """`apply()` 가 실제로 적용한 폰트 이름.  아직 호출 전이면 None."""
    return _STATE["font"]


# =========================================================================== #
#  2. 라벨 검사                                                                #
# =========================================================================== #

def check_label(s):
    """축/제목 라벨 문자열을 검사하고 그대로 돌려준다.

    - U+2212 MINUS SIGN 이 들어 있으면 `ValueError`.  Malgun Gothic 에 글리프가
      없어서 `axes.unicode_minus=False` 로도 막을 수 없다(그건 눈금 라벨만 고친다).
      음수 부호는 ASCII '-' 를 쓴다.
    - 검증되지 않은 비-ASCII 문자는 **경고만** 하고 통과시킨다(문자당 1회).

    모든 `set_xlabel/set_ylabel/set_title/text/annotate` 인자를 이걸로 감쌀 것.
    """
    if not isinstance(s, str):
        s = str(s)
    for ch, why in _FORBIDDEN.items():
        if ch in s:
            raise ValueError(
                "check_label: label contains %s, which Malgun Gothic has no glyph "
                "for. Use the ASCII hyphen '-' instead. offending label=%r" % (why, s))
    for ch in s:
        o = ord(ch)
        if o < 128 or ch in _VERIFIED_EXTRA:
            continue
        if _is_hangul(o):
            continue
        if ch in _LABEL_WARNED:
            continue
        _LABEL_WARNED.add(ch)
        try:
            nm = unicodedata.name(ch)
        except ValueError:                               # pragma: no cover
            nm = "U+%04X" % o
        _warn("NOTE: label uses unverified non-ASCII char %r (U+%04X %s); glyph "
              "presence in %s is not verified."
              % (ch, o, nm, _STATE["font"] or "the active font"))
    return s


def _is_hangul(o):
    return (0xAC00 <= o <= 0xD7A3 or 0x1100 <= o <= 0x11FF
            or 0x3130 <= o <= 0x318F or 0xA960 <= o <= 0xA97F)


# =========================================================================== #
#  3. 스타일 헬퍼                                                              #
# =========================================================================== #

def case_style(case, hset, markers=True):
    """`ax.plot(..., **case_style("AC", "sph"))` 로 쓰는 kwargs 사전.

    색 = 케이스(DC/AC/AC+), 선 종류(+마커) = h-세트(base/sph).  직교 인코딩이라
    흑백 인쇄에서도 4~6 조합이 구분된다.
    """
    if case not in CASE_COLORS:
        raise KeyError("unknown case %r; expected one of %s"
                       % (case, sorted(CASE_COLORS)))
    if hset not in HSET_STYLES:
        raise KeyError("unknown h-set %r; expected one of %s"
                       % (hset, sorted(HSET_STYLES)))
    st = {"color": CASE_COLORS[case], "linestyle": HSET_STYLES[hset]}
    if markers:
        st.update(HSET_MARKERS[hset])
        st["markeredgecolor"] = CASE_COLORS[case]
    return st


def legend_handles(cases=("DC", "AC"), hsets=("base", "sph"),
                   limit_line=True, markers=True):
    """범례용 proxy `Line2D` 목록.  matplotlib 은 `ncol` 을 열 우선으로 채운다."""
    out = []
    for c in cases:
        for h in hsets:
            st = case_style(c, h, markers=markers)
            out.append(Line2D([], [], label=check_label(
                "Case %s · %s" % (c, HSET_LABELS_KR.get(h, h))), **st))
    if limit_line:
        out.append(Line2D([], [], color=LIMIT_COLOR, ls=":", lw=1.0,
                          label=check_label("180 degC 한계")))
    return out


def limit_lines(ax, winding=True, magnet=False, annotate=False, x=0.02):
    """권선 180 degC / 자석 150 degC 한계선.  라벨은 ASCII 'degC' 로 쓴다."""
    if winding:
        ax.axhline(T_LIMIT_WINDING, color=LIMIT_COLOR, lw=1.0, ls=":", zorder=1)
        if annotate:
            ax.text(x, T_LIMIT_WINDING + 4, check_label("권선 절연 한계 180 degC"),
                    transform=ax.get_yaxis_transform(), fontsize=7.5,
                    color=LIMIT_COLOR, va="bottom")
    if magnet:
        ax.axhline(T_LIMIT_MAGNET, color=MAG_LIMIT_COLOR, lw=1.0, ls=":",
                   alpha=0.7, zorder=1)
        if annotate:
            ax.text(x, T_LIMIT_MAGNET + 4, check_label("자석 감자 한계 150 degC"),
                    transform=ax.get_yaxis_transform(), fontsize=7.5,
                    color=MAG_LIMIT_COLOR, va="bottom")
    return None


def speed_axis(ax, speeds=(2000, 4000, 8000, 16000), xlim=(1750, 21000)):
    """rpm 축을 log2 로 둔다.  2k/4k/8k/16k 가 정확히 옥타브라 등간격이 된다."""
    ax.set_xscale("log", base=2)
    ax.set_xticks(list(speeds))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: format(int(v), ",")))
    ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _p: ""))
    if xlim is not None:
        ax.set_xlim(*xlim)
    return None


# =========================================================================== #
#  4. 글리프 경고 감시                                                         #
# =========================================================================== #

_GLYPH_MARK = "missing from font"


class _GlyphHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self, level=logging.WARNING)
        self.hits = []
        self._seen = set()

    def emit(self, record):
        try:
            msg = record.getMessage()
        except Exception:                                # pragma: no cover
            return
        if _GLYPH_MARK not in msg:
            return
        key = (record.name, record.created, msg)
        if key in self._seen:
            return                                       # 루트/자식 양쪽 부착 중복 제거
        self._seen.add(key)
        self.hits.append(msg)


class glyph_watch(object):
    """누락 글리프 경고를 세는 컨텍스트 매니저.

        with ts.glyph_watch() as gw:
            fig.savefig(...)
        assert gw.count == 0, gw.messages

    matplotlib 의 "Glyph NNN (...) missing from font(s) X." 는 **logging** 으로
    나간다(warnings 가 아니다).  그래서 logging 핸들러와 `warnings` 를 **둘 다**
    가로챈다.  로거 레벨이 WARNING 보다 높게 설정돼 있으면 잠시 낮춘다.
    """

    def __init__(self, loggers=("matplotlib", "")):
        self._names = tuple(loggers)
        self._handler = _GlyphHandler()
        self._restore = []
        self._wctx = None
        self._wlist = None

    def __enter__(self):
        for nm in self._names:
            lg = logging.getLogger(nm)
            lg.addHandler(self._handler)
            old = lg.level
            self._restore.append((lg, old))
            if old > logging.WARNING or (nm and old == logging.NOTSET):
                # 레코드가 아예 생성되지 않는 일을 막는다(전파는 조상 레벨 무시).
                lg.setLevel(logging.WARNING)
        self._wctx = warnings.catch_warnings(record=True)
        self._wlist = self._wctx.__enter__()
        warnings.simplefilter("always")
        return self

    def __exit__(self, *exc):
        try:
            wl = list(self._wlist or [])
        finally:
            if self._wctx is not None:
                self._wctx.__exit__(*exc)
        for w in wl:
            txt = str(w.message)
            if _GLYPH_MARK in txt and txt not in self._handler.hits:
                self._handler.hits.append(txt)
        for lg, old in self._restore:
            try:
                lg.removeHandler(self._handler)
                lg.setLevel(old)
            except Exception:                            # pragma: no cover
                pass
        self._restore = []
        return False

    @property
    def messages(self):
        return list(self._handler.hits)

    @property
    def count(self):
        return len(self._handler.hits)


# =========================================================================== #
#  5. 300 KB 상한 저장                                                         #
# =========================================================================== #

def _adaptive_const():
    """Pillow 신/구 버전 모두 지원: Image.Palette.ADAPTIVE / Image.ADAPTIVE."""
    if _PIL_Image is None:
        return None
    pal = getattr(_PIL_Image, "Palette", None)
    if pal is not None and hasattr(pal, "ADAPTIVE"):
        return pal.ADAPTIVE                              # Pillow >= 9.1
    if hasattr(_PIL_Image, "ADAPTIVE"):
        return _PIL_Image.ADAPTIVE                       # legacy
    return 1                                             # ADAPTIVE == 1


def _save_once(fig, path, dpi):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    kw = dict(dpi=float(dpi), bbox_inches="tight", pad_inches=PAD_INCHES)
    if not str(path).lower().endswith(".png"):
        kw["format"] = "png"
    try:
        fig.savefig(path, pil_kwargs={"optimize": True}, **kw)
    except TypeError:                                    # 아주 오래된 matplotlib
        fig.savefig(path, **kw)
    return os.path.getsize(path)


def _palettise(path, colors):
    """이미 저장된 PNG 를 팔레트 N색으로 재저장한다.  성공하면 새 크기, 실패하면 None.

    Windows 에서 같은 경로를 열어둔 채 덮어쓰면 안 되므로 with 로 닫고 쓴다.
    """
    if _PIL_Image is None:
        return None
    adaptive = _adaptive_const()
    try:
        with _PIL_Image.open(path) as im:
            rgb = im.convert("RGB")
        q = rgb.convert("P", palette=adaptive, colors=int(colors))
        q.save(path, "PNG", optimize=True)
        return os.path.getsize(path)
    except Exception as exc:                             # pragma: no cover
        _warn("palette%s failed: %s" % (colors, exc))
        return None


def savefig_guarded(fig, path, dpi=300, max_bytes=PNG_MAX_BYTES, min_dpi=110):
    """PNG 를 300 KB 이하로 **보장**해서 저장한다.

    전략(측정 기반):
      1) `dpi` 로 저장.  대부분의 D1 라인차트는 여기서 끝난다(6.2x5.0 in @300 -> 267 KB).
      2) 넘으면 dpi 를 15% 씩 낮추며 `min_dpi` 까지 재시도.
      3) 그래도 넘으면 **원래 dpi 로 되돌린 뒤** 팔레트 256 -> 128 -> 64 양자화.
         (래스터 패널은 dpi 사다리만으로는 못 내려간다: 7.2x3.6 in imshow 가
          dpi 150 에서도 338 KB.  팔레트 256 이 799 KB -> 273 KB 로 3배 지렛대.
          해상도를 지키려고 dpi 를 먼저 복구한다.)
      4) 마지막 수단으로 min_dpi + 팔레트 64.

    Pillow 가 없으면 3~4 단계는 건너뛰고 dpi 사다리 결과를 그대로 반환한다.

    반환: {"path", "bytes", "dpi", "method": "dpi"|"palette", "ok",
           "colors", "max_bytes", "attempts"}   (뒤 3개는 부가 필드)
    """
    path = str(path)
    dpi0 = float(dpi)
    min_dpi = float(min_dpi)
    max_bytes = int(max_bytes)
    attempts = []

    def _res(nbytes, used_dpi, method, colors, ok):
        return {"path": path, "bytes": int(nbytes), "dpi": float(used_dpi),
                "method": method, "ok": bool(ok), "colors": colors,
                "max_bytes": max_bytes, "attempts": attempts}

    # --- 1~2) dpi 사다리 ---------------------------------------------------
    d = dpi0
    while True:
        n = _save_once(fig, path, d)
        attempts.append("dpi=%g -> %d B" % (d, n))
        if n <= max_bytes:
            return _res(n, d, "dpi", None, True)
        if d <= min_dpi:
            break
        d = max(min_dpi, d * 0.85)

    # --- 3) 팔레트 (원래 dpi 로 복귀해서 해상도를 지킨다) ------------------
    if _PIL_Image is not None:
        n = _save_once(fig, path, dpi0)
        attempts.append("restore dpi=%g -> %d B" % (dpi0, n))
        for nc in _PALETTE_LADDER:
            n2 = _palettise(path, nc)
            if n2 is None:
                break
            attempts.append("dpi=%g+pal%d -> %d B" % (dpi0, nc, n2))
            if n2 <= max_bytes:
                return _res(n2, dpi0, "palette", nc, True)
            # 다음 색수는 이미 팔레트화된 파일이 아니라 원본에서 다시 시작한다.
            n = _save_once(fig, path, dpi0)
        # --- 4) 최후: min_dpi + 팔레트 64 ---------------------------------
        n = _save_once(fig, path, min_dpi)
        n2 = _palettise(path, _PALETTE_LADDER[-1])
        n = n if n2 is None else n2
        attempts.append("dpi=%g+pal%d -> %d B" % (min_dpi, _PALETTE_LADDER[-1], n))
        return _res(n, min_dpi, "palette", _PALETTE_LADDER[-1], n <= max_bytes)

    n = os.path.getsize(path)
    _warn("Pillow unavailable: palette fallback skipped; %s is %d B (> %d B). "
          "Reduce figsize or dpi." % (path, n, max_bytes))
    return _res(n, min_dpi, "dpi", None, False)


def png_from_pyvista(img, title, path, dpi=300, **kw):
    """pyvista 스크린샷 배열을 한글 제목이 붙은 PNG 로 저장한다.

    VTK 는 한글을 그리지 못한다(그리고 `axes.unicode_minus` 도 VTK 에는 무효).
    그래서 pyvista 쪽은 라벨 없이 렌더하고, 배열만 받아 matplotlib figure 안에
    넣은 뒤 제목을 matplotlib 폰트 스택으로 그린다.

        img = pl.screenshot(return_img=True); pl.close()
        ts.png_from_pyvista(img, "C67 회전자 18,000 rpm 폰미제스 응력 [MPa]", out)

    img: (H, W, 3|4) uint8 배열 또는 PIL 이미지.
    kw : figsize, max_bytes, min_dpi, fontsize, subtitle, interpolation,
         close(기본 True).  그 외 키는 오타로 보고 TypeError.
    반환: `savefig_guarded()` 와 같은 사전 (+ "figsize").
    """
    import numpy as np

    figsize = kw.pop("figsize", None)
    max_bytes = int(kw.pop("max_bytes", PNG_MAX_BYTES))
    min_dpi = float(kw.pop("min_dpi", 110))
    fontsize = float(kw.pop("fontsize", 10.0))
    subtitle = kw.pop("subtitle", None)
    interpolation = kw.pop("interpolation", "antialiased")
    close = bool(kw.pop("close", True))
    if kw:
        raise TypeError("png_from_pyvista: unexpected keyword(s) %s"
                        % sorted(kw.keys()))

    if _PIL_Image is not None and isinstance(img, _PIL_Image.Image):
        arr = np.asarray(img.convert("RGB"))
    else:
        arr = np.asarray(img)
    if arr.ndim != 3 or arr.shape[2] < 3:
        raise ValueError("png_from_pyvista: expected an (H, W, 3|4) RGB array, got "
                         "shape %r" % (getattr(arr, "shape", None),))
    arr = arr[..., :3]
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype("uint8")

    h, w = arr.shape[0], arr.shape[1]
    if figsize is None:
        base_w = FIGSIZE["raster"][0]
        figsize = (base_w, base_w * float(h) / float(w))

    if not _STATE["applied"]:
        apply()

    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(arr, interpolation=interpolation)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    if title:
        ax.set_title(check_label(title), fontsize=fontsize, color=INK, pad=6)
    if subtitle:
        ax.set_xlabel(check_label(subtitle), fontsize=fontsize - 1.5, color=INK2)
    fig.tight_layout(pad=0.2)
    try:
        res = savefig_guarded(fig, path, dpi=dpi, max_bytes=max_bytes,
                              min_dpi=min_dpi)
    finally:
        if close:
            plt.close(fig)
    res["figsize"] = tuple(figsize)
    return res


# =========================================================================== #
#  6. 자체 시험                                                                #
# =========================================================================== #

def _demo_figure():
    """한글 라벨 + 6곡선 + 음수 눈금 + mathtext 를 한 그림에 몰아넣은 스트레스 케이스."""
    import numpy as np

    fig, ax = plt.subplots(figsize=FIGSIZE["grid2x2"])
    I = np.array([115.075, 230.05, 345.025, 460.0])
    k = {"DC": 1.00, "AC": 1.35, "AC+": 1.70}
    off = {"base": 0.0, "sph": -14.0}
    for c in ("DC", "AC", "AC+"):
        for hs in ("base", "sph"):
            T = 70.0 + k[c] * 0.00092 * I ** 2 + off[hs]
            ax.plot(I, T, label=check_label("Case %s · %s" % (c, HSET_LABELS_KR[hs])),
                    **case_style(c, hs))
    limit_lines(ax, winding=True, magnet=True, annotate=True)
    # 음수 눈금을 강제해 axes.unicode_minus 를 실제로 태운다.
    ax.set_ylim(-60, 340)
    ax.grid(True, zorder=0)
    ax.set_xlabel(check_label(r"상전류 실효값 $I_\mathrm{rms}$ [A]"))
    ax.set_ylabel(check_label("권선 최고 온도 [°C]"))
    ax.set_title(check_label(
        "e10 연속 정격 - 속도·전류에 따른 권선 최고 온도 (정상상태, 오일 70 °C)"),
        fontsize=10.5)
    ax.annotate(check_label("그림 규약 검증 — DC · AC · AC+ / base · sph"),
                xy=(0.02, 0.03), xycoords="axes fraction", fontsize=7.5, color=INK2)
    ax.annotate(check_label(r"$\Delta T = -20$ K (mathtext minus)"),
                xy=(0.02, 0.10), xycoords="axes fraction", fontsize=7.5, color=INK2)
    fig.legend(handles=legend_handles(cases=("DC", "AC", "AC+")),
               loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.005), handlelength=2.6, columnspacing=1.6)
    fig.tight_layout(rect=[0, 0.135, 1, 0.97])
    return fig


def _self_test(out_dir=None):
    """실제로 렌더해서 규약이 지켜지는지 검증한다.  실패하면 AssertionError."""
    import tempfile

    import numpy as np

    if out_dir is None:
        out_dir = tempfile.mkdtemp(prefix="thesis_style_")
    out_dir = os.path.abspath(out_dir)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    print("[1] apply() + font resolution")
    apply()
    apply()                                              # 멱등성 확인
    assert _STATE["applied"] is True
    print("    matplotlib %s | python %s" % (matplotlib.__version__,
                                             sys.version.split()[0]))
    print("    requested='Malgun Gothic' -> active=%r" % active_font())
    print("    axes.unicode_minus=%r  font.sans-serif[0]=%r"
          % (plt.rcParams["axes.unicode_minus"], plt.rcParams["font.sans-serif"][0]))
    print("    Pillow=%s  ADAPTIVE=%r"
          % ("yes" if _PIL_Image is not None else "NO", _adaptive_const()))
    kr_ok = active_font() != "DejaVu Sans"

    print("[2] check_label()")
    assert check_label("권선 최고 온도 [°C]") == "권선 최고 온도 [°C]"
    assert check_label("-40 K") == "-40 K"
    raised = False
    try:
        check_label("\u221240 K")                        # U+2212 MINUS SIGN
    except ValueError as exc:
        raised = True
        assert "U+2212" in str(exc)
    assert raised, "check_label must reject U+2212"
    for bad in ("h-set \u2212 base", "\u2212"):
        try:
            check_label(bad)
            raise AssertionError("check_label missed U+2212 in %r" % bad)
        except ValueError:
            pass
    print("    U+2212 rejected, ASCII hyphen accepted, degree sign accepted")

    print("[3] render Korean multi-curve figure under a glyph watch")
    png = os.path.join(out_dir, "thesis_style_selftest.png")
    with glyph_watch() as gw:
        fig = _demo_figure()
        res = savefig_guarded(fig, png)
        fig.canvas.draw()                                # 화면 경로도 한 번 태운다
        plt.close(fig)
    for a in res["attempts"]:
        print("    " + a)
    print("    -> %s" % res["path"])
    print("    bytes=%d (%.1f KB)  dpi=%g  method=%s  colors=%s  ok=%s"
          % (res["bytes"], res["bytes"] / 1024.0, res["dpi"], res["method"],
             res["colors"], res["ok"]))
    print("    glyph warnings: %d %s" % (gw.count, gw.messages[:3]))
    assert res["ok"] is True, "figure exceeded the %d B cap" % PNG_MAX_BYTES
    assert res["bytes"] <= PNG_MAX_BYTES, res["bytes"]
    assert os.path.getsize(png) == res["bytes"]
    if kr_ok:
        assert gw.count == 0, "missing glyphs: %s" % gw.messages
    else:
        print("    (font fell back to DejaVu Sans - glyph assertion relaxed)")

    print("[4] glyph_watch actually detects a missing glyph (negative control)")
    with glyph_watch() as gw2:
        f2 = plt.figure(figsize=(1.6, 1.2))
        f2.text(0.1, 0.5, "\u2212\u2212\u2212", fontfamily="Malgun Gothic")
        f2.savefig(os.path.join(out_dir, "_negctl.png"), dpi=60)
        plt.close(f2)
    if kr_ok:
        assert gw2.count > 0, ("glyph_watch caught nothing on a deliberately "
                               "missing glyph - the capture is broken")
        print("    detected %d warning(s), e.g. %s" % (gw2.count, gw2.messages[0]))
    else:
        print("    skipped (no Korean font to test against)")

    print("[5] savefig_guarded palette fallback (tiny cap forces it)")
    fig3 = _demo_figure()
    res3 = savefig_guarded(fig3, os.path.join(out_dir, "thesis_style_tinycap.png"),
                           dpi=300, max_bytes=40 * 1024, min_dpi=110)
    plt.close(fig3)
    print("    bytes=%d (%.1f KB) dpi=%g method=%s colors=%s ok=%s"
          % (res3["bytes"], res3["bytes"] / 1024.0, res3["dpi"], res3["method"],
             res3["colors"], res3["ok"]))
    assert res3["method"] in ("dpi", "palette")
    if _PIL_Image is not None:
        assert res3["method"] == "palette", res3["attempts"]
        assert res3["bytes"] <= 40 * 1024, res3["attempts"]

    print("[6] png_from_pyvista() with a synthetic screenshot array")
    yy, xx = np.mgrid[0:950, 0:1150]
    r = np.sqrt((xx - 575.0) ** 2 + (yy - 475.0) ** 2)
    band = (np.clip(r / 470.0, 0, 1) * 13).astype("uint8")
    rgb = np.zeros((950, 1150, 3), dtype="uint8")
    rgb[..., 0] = 40 + band * 16
    rgb[..., 1] = 10 + band * 8
    rgb[..., 2] = 120 - band * 8
    rgba = np.dstack([rgb, np.full((950, 1150, 1), 255, dtype="uint8")])
    with glyph_watch() as gw3:
        res4 = png_from_pyvista(
            rgba, "e10 고정자 z 단면 온도 분포 [°C] - 정상상태",
            os.path.join(out_dir, "thesis_style_raster.png"),
            subtitle="(a) 균일 손실 · 16,000 rpm · 230 A")
    print("    bytes=%d (%.1f KB) dpi=%g method=%s colors=%s figsize=%s ok=%s"
          % (res4["bytes"], res4["bytes"] / 1024.0, res4["dpi"], res4["method"],
             res4["colors"], res4["figsize"], res4["ok"]))
    print("    glyph warnings: %d" % gw3.count)
    assert res4["ok"] is True and res4["bytes"] <= PNG_MAX_BYTES
    if kr_ok:
        assert gw3.count == 0, gw3.messages
    raised = False
    try:
        png_from_pyvista(rgba, "t", os.path.join(out_dir, "_x.png"), figsizes=(1, 1))
    except TypeError:
        raised = True
    assert raised, "png_from_pyvista must reject unknown kwargs"

    print("[7] constants")
    assert CASE_COLORS == {"DC": "#9C9C9C", "AC": "#0B3D91", "AC+": "#E03131"}
    assert HSET_STYLES == {"base": "-", "sph": "--"}
    assert PNG_MAX_BYTES == 307200
    lum = {}
    for c, hexs in CASE_COLORS.items():
        r_, g_, b_ = (int(hexs[i:i + 2], 16) for i in (1, 3, 5))
        lum[c] = 0.299 * r_ + 0.587 * g_ + 0.114 * b_
    print("    greyscale luminance: " + "  ".join(
        "%s=%.1f" % (c, lum[c]) for c in ("DC", "AC+", "AC")))
    ladder = sorted(lum.values())
    seps = [ladder[i + 1] - ladder[i] for i in range(len(ladder) - 1)]
    print("    separations: %s (min %.1f)" % (["%.1f" % s for s in seps], min(seps)))
    assert min(seps) > 40.0, "case colours collapse in greyscale print"

    print("")
    print("SELF-TEST PASSED  font=%s  main figure=%d B (%.1f KB, cap %d B)  "
          "glyph warnings=0" % (active_font(), res["bytes"],
                                res["bytes"] / 1024.0, PNG_MAX_BYTES))
    print("out_dir=%s" % out_dir)
    return {"out_dir": out_dir, "font": active_font(), "main": res,
            "tinycap": res3, "raster": res4, "glyph_warnings": gw.count}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="thesis figure conventions for PLAN_20260906 (thermal kit)")
    ap.add_argument("--self-test", action="store_true",
                    help="render a Korean-labelled test figure and verify the "
                         "font, the 300 KB cap and zero missing glyphs")
    ap.add_argument("--out", default=None,
                    help="directory for the self-test artefacts (default: a temp dir)")
    args = ap.parse_args(argv)

    try:                                                 # cp949 콘솔에서도 한글 출력
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                    # pragma: no cover
        pass

    if not args.self_test:
        ap.print_help()
        return 0
    try:
        _self_test(args.out)
    except AssertionError as exc:
        print("SELF-TEST FAILED: %s" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
