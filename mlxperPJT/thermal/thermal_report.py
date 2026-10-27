# -*- coding: utf-8 -*-
"""열해석 결과 HTML 리포트 — 결과 JSON + 표준 그림을 한 파일짜리 HTML 로.

    python thermal_report.py                                   # 기본: viz = gdrive 동기화 폴더
    python thermal_report.py --viz-root "G:\\내 드라이브\\Prius_thermal_viz" --out report.html
    python thermal_report.py --chains e10 --gifs               # 과도 GIF 포함(파일 커짐)

- 차트는 인라인 SVG, 그림은 base64 내장 → 외부 의존·네트워크 없이 열린다(메일·OneDrive 공유용).
- 판정(gate): 교차검증 허용오차, 기준값 회귀, 비물리값(>NONPHYS °C)을 자동 표시.
- 의존: 표준 라이브러리 (+ Pillow 있으면 그림 축소). Python 3.10+.
"""
import argparse
import base64
import datetime as dt
import html
import io
import json
import math
import os
import subprocess
from pathlib import Path

THERMAL = Path(__file__).resolve().parent
DATA_E10 = THERMAL / "freeflow" / "data"
DATA_PRIUS = THERMAL / "prius" / "data"
DEFAULT_VIZ = Path(os.environ.get("THERMAL_VIZ_ROOT", r"G:\내 드라이브\Prius_thermal_viz"))
NONPHYS = 300.0          # °C — 이 이상은 비물리(발산·BC 상실·비컨포멀) 신호로 본다
PARTS = ["coil", "stator", "rotor", "magnet", "shaft"]
PART_KO = {"coil": "권선", "stator": "스테이터", "rotor": "로터", "magnet": "자석", "shaft": "샤프트"}

# MAPDL 워터재킷(조건 정합) 값은 JSON 이 없고 prius/scripts/10_validation_matrix.py 에 상수로만 있다.
PRIUS_MAPDL_REF = {
    "MAPDL 워터재킷 저부하": {"coil": 88.3, "stator": 86.5, "rotor": 83.7, "magnet": 83.5},
    "MAPDL 워터재킷 250A": {"coil": 119.2, "stator": 116.3, "rotor": 110.2, "magnet": 109.0},
    "MAPDL JAC279 250A (조건 상이)": {"coil": 185.6, "stator": 181.8, "rotor": 166.0, "magnet": 161.6},
}
E10_REF_WINDING = 152.2


# ───────────────────────── 데이터 ─────────────────────────
def load_json(p: Path):
    if not p.exists():
        return None
    raw = p.read_bytes()
    for enc in ("utf-8", "cp949"):
        try:
            return json.loads(raw.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def pick_max(d, *keys):
    """{'coil': {'max':..}} / {'coil': 118.2} / at_900s 형식을 모두 max 값으로."""
    for k in keys:
        v = d.get(k) if isinstance(d, dict) else None
        if isinstance(v, dict):
            v = v.get("max")
        if isinstance(v, (int, float)):
            return float(v)
    return None


def prius_data():
    fl_low = load_json(DATA_PRIUS / "fluent_prius_zone_temps.json") or {}
    fl_hi = load_json(DATA_PRIUS / "fluent_prius_250A_zone_temps.json") or {}
    ipk = load_json(DATA_PRIUS / "icepak_prius_250A_temps.json") or {}
    loss = load_json(DATA_PRIUS / "prius_losses.json") or {}
    series = {
        "Fluent CHT 저부하": {p: pick_max(fl_low, p, "phase" if p == "coil" else p) for p in PARTS[:4]},
        "Fluent CHT 250A": {p: pick_max(fl_hi, p, "phase" if p == "coil" else p) for p in PARTS[:4]},
    }
    series.update(PRIUS_MAPDL_REF)
    roles = ipk.get("per_role", {})
    series["Icepak 고정온도 250A"] = {p: pick_max(roles, p) for p in PARTS[:4]}
    losses = {"슬롯 동손": loss.get("StrandedLoss"), "자석": loss.get("SolidLoss"),
              "스테이터 철손": loss.get("CoreLoss_Stator"), "로터 철손": loss.get("CoreLoss_Rotor")}
    cond = loss.get("_model", "")
    return series, losses, cond


def e10_data():
    mh = load_json(DATA_E10 / "ff_mapdl_hybrid_temps.json") or {}
    v1 = load_json(DATA_E10 / "e10_icepak_v1_homog.json") or {}
    v2 = load_json(DATA_E10 / "e10_icepak_v2_bars.json") or {}
    pp = mh.get("per_part", {})
    series = {
        "MAPDL 하이브리드 (과도 900s)": {p: pick_max(pp, "winding" if p == "coil" else p) for p in PARTS},
        "Icepak V1 균질+대류벽 (900s)": {p: pick_max(v1.get("at_900s", {}), "winding" if p == "coil" else p) for p in PARTS},
        "Icepak V2 discrete 바": {p: pick_max(v2.get("at_900s", {}), p) for p in PARTS},
    }
    return series, mh, load_json(DATA_E10 / "ff_coupled_validation.json") or {}


def run_inventory():
    rows = []
    for folder in (DATA_E10, DATA_PRIUS):
        for p in sorted(folder.glob("*.json")):
            if p.stat().st_size > 200_000:          # 가진력 등 대용량 원자료는 제외
                continue
            d = load_json(p)
            if d is None:
                rows.append((p, "읽기 실패", None, ""))
                continue
            nums = []

            def walk(o, key=""):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if not str(k).startswith("_"):
                            walk(v, k)
                elif isinstance(o, list):
                    for v in o:
                        walk(v, key)
                elif isinstance(o, (int, float)) and not isinstance(o, bool) and key in ("max", "mean") + tuple(PARTS) + ("winding", "coil_max"):
                    nums.append(float(o))
            walk(d)
            note = d.get("_model") or d.get("_note") or d.get("load") or "" if isinstance(d, dict) else ""
            tmax = max(nums) if nums else None
            rows.append((p, "비물리" if tmax and tmax > NONPHYS else ("정상" if tmax else "값 없음"), tmax, str(note)))
    return rows


# ───────────────────────── 판정 ─────────────────────────
def gate(name, ok, detail, warn=False):
    return {"name": name, "state": "pass" if ok else ("warn" if warn else "fail"), "detail": detail}


def gates(prius, e10, ffv):
    out = []
    ps = prius[0]
    for label, fl, ma in (("저부하", "Fluent CHT 저부하", "MAPDL 워터재킷 저부하"),
                          ("250A", "Fluent CHT 250A", "MAPDL 워터재킷 250A")):
        f, m = ps.get(fl, {}).get("coil"), ps.get(ma, {}).get("coil")
        if f is not None and m is not None:
            out.append(gate(f"Prius {label}: MAPDL ↔ Fluent 코일", abs(m - f) <= 2.0,
                            f"MAPDL {m:.1f} / Fluent {f:.1f} °C · Δ {m - f:+.1f} (허용 ±2.0)"))
    es = e10[0]
    w = es.get("MAPDL 하이브리드 (과도 900s)", {}).get("coil")
    if w is not None:
        out.append(gate("e10 MAPDL 하이브리드 권선 회귀", abs(w - E10_REF_WINDING) <= 1.0,
                        f"{w:.1f} °C (기준 {E10_REF_WINDING}, 허용 ±1.0)"))
    iv = es.get("Icepak V1 균질+대류벽 (900s)", {}).get("coil")
    if w and iv:
        rel = (iv - w) / w
        out.append(gate("e10 Icepak V1 ↔ MAPDL 권선", abs(rel) <= 0.15,
                        f"Icepak {iv:.1f} / MAPDL {w:.1f} °C · {rel:+.0%} (허용 ±15%)", warn=abs(rel) <= 0.25))
    r = (ffv or {}).get("result", {})
    if r:
        oil, walls = r.get("oil_T_C", {}), (ffv.get("wall_BC_C") or {}).values()
        ok = oil.get("max", 0) > ffv.get("oil_inlet_C", 0) and oil.get("max", 1e9) < max(walls or [0])
        out.append(gate("FreeFlow 1-way 오일 승온 일관성", ok,
                        f"유입 {ffv.get('oil_inlet_C')} → 평균 {oil.get('mean')} / 최대 {oil.get('max')} °C "
                        f"(t={r.get('physical_time_s')} s, 벽 최고 {max(walls or [0])} °C 미만이어야 함)"))
    bad = [n for n, s in es.items() for p, v in s.items() if v and v > NONPHYS]
    out.append(gate("e10 비물리값 격리", True if not bad else False,
                    "없음" if not bad else f"{', '.join(sorted(set(bad)))} — {NONPHYS:.0f} °C 초과 → 비교에서 제외",
                    warn=True))
    return out


# ───────────────────────── 렌더 ─────────────────────────
PALETTE = ["#2F6F8F", "#E8960B", "#D9481B", "#3F7D4E", "#7A5C99", "#8C7F6F"]


def svg_grouped(series, parts, title, ref_line=None, cap=NONPHYS):
    names = [n for n in series if any(series[n].get(p) for p in parts)]
    vals = [v for n in names for p in parts for v in [series[n].get(p)] if v and v <= cap]
    if not vals:
        return "<p class='muted'>데이터 없음</p>"
    vmax = max(vals + ([ref_line[0]] if ref_line else [])) * 1.12
    W, H, L, B, T = 760, 300, 44, 34, 16
    gw = (W - L - 10) / len(parts)
    bw = min(22.0, (gw - 16) / max(len(names), 1))
    y = lambda v: T + (H - T - B) * (1 - v / vmax)
    s = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='{html.escape(title)}'>"]
    for k in range(6):
        v = vmax * k / 5
        s.append(f"<line x1='{L}' x2='{W-10}' y1='{y(v):.1f}' y2='{y(v):.1f}' class='grid'/>"
                 f"<text x='{L-6}' y='{y(v)+4:.1f}' class='ax' text-anchor='end'>{v:.0f}</text>")
    for i, p in enumerate(parts):
        gx = L + i * gw + (gw - bw * len(names)) / 2
        s.append(f"<text x='{L+i*gw+gw/2:.1f}' y='{H-12}' class='ax' text-anchor='middle'>{PART_KO[p]}</text>")
        for j, n in enumerate(names):
            v = series[n].get(p)
            x = gx + j * bw
            if v is None:
                continue
            if v > cap:
                s.append(f"<text x='{x+bw/2:.1f}' y='{T+10}' class='bad' text-anchor='middle'>✕</text>"
                         f"<title>{html.escape(n)} {PART_KO[p]}: {v:.0f} °C (비물리)</title>")
                continue
            s.append(f"<rect x='{x:.1f}' y='{y(v):.1f}' width='{bw-2:.1f}' height='{y(0)-y(v):.1f}' "
                     f"fill='{PALETTE[j % len(PALETTE)]}' rx='2'><title>{html.escape(n)} · {PART_KO[p]}: {v:.1f} °C</title></rect>")
            if bw >= 18:
                s.append(f"<text x='{x+bw/2-1:.1f}' y='{y(v)-3:.1f}' class='val' text-anchor='middle'>{v:.0f}</text>")
    if ref_line:
        s.append(f"<line x1='{L}' x2='{W-10}' y1='{y(ref_line[0]):.1f}' y2='{y(ref_line[0]):.1f}' class='ref'/>"
                 f"<text x='{L+4}' y='{y(ref_line[0])-4:.1f}' class='ref-t'>{html.escape(ref_line[1])}</text>")
    s.append("</svg>")
    leg = "".join(f"<span><i style='background:{PALETTE[j % len(PALETTE)]}'></i>{html.escape(n)}</span>"
                  for j, n in enumerate(names))
    return f"<figure class='chart'>{''.join(s)}<figcaption class='legend'>{leg}</figcaption></figure>"


def svg_timing(items):
    W, H, L = 760, 40 + 34 * len(items), 250
    lo, hi = math.log10(5), math.log10(max(v for _, v, _ in items) * 2)
    x = lambda v: L + (W - L - 90) * (math.log10(v) - lo) / (hi - lo)
    s = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='계산 시간'>"]
    for d in range(1, 6):
        v = 10 ** d
        if lo <= d <= hi:
            s.append(f"<line x1='{x(v):.1f}' x2='{x(v):.1f}' y1='8' y2='{H-24}' class='grid'/>"
                     f"<text x='{x(v):.1f}' y='{H-8}' class='ax' text-anchor='middle'>{'1e%d s' % d}</text>")
    for i, (name, v, note) in enumerate(items):
        yy = 14 + i * 34
        s.append(f"<text x='{L-8}' y='{yy+15}' class='ax' text-anchor='end'>{html.escape(name)}</text>"
                 f"<rect x='{L}' y='{yy}' width='{x(v)-L:.1f}' height='20' rx='3' fill='{PALETTE[i % len(PALETTE)]}'>"
                 f"<title>{html.escape(note)}</title></rect>"
                 f"<text x='{x(v)+6:.1f}' y='{yy+15}' class='val'>{fmt_time(v)}</text>")
    s.append("</svg>")
    return "".join(s)


def fmt_time(s):
    return f"{s:.1f} 초" if s < 120 else (f"{s/60:.1f} 분" if s < 7200 else f"{s/3600:.1f} 시간")


def table(series, parts):
    head = "".join(f"<th>{PART_KO[p]}</th>" for p in parts)
    body = []
    for n, d in series.items():
        cells = []
        for p in parts:
            v = d.get(p)
            cls = " class='bad'" if v and v > NONPHYS else ""
            cells.append(f"<td{cls}>{'—' if v is None else f'{v:.1f}'}</td>")
        body.append(f"<tr><th scope='row'>{html.escape(n)}</th>{''.join(cells)}</tr>")
    return f"<table><thead><tr><th>최고온도 °C</th>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def embed_image(path: Path, max_w=1100):
    data, mime = path.read_bytes(), "image/png"
    if path.suffix.lower() == ".gif":
        mime = "image/gif"
    else:
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(data))
            if im.width > max_w:
                im = im.resize((max_w, int(im.height * max_w / im.width)))
            buf = io.BytesIO()
            if im.mode in ("RGBA", "P") and len(data) < 400_000:
                im.save(buf, "PNG", optimize=True)
            else:
                im.convert("RGB").save(buf, "JPEG", quality=85)
                mime = "image/jpeg"
            data = buf.getvalue()
        except Exception:
            pass
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


GALLERY = {
    "prius": [("prius/viz/comparison/validation_matrix.png", "교차검증 매트릭스 — MAPDL vs Fluent (원본 차트)"),
              ("prius/viz/waterjacket_high/cut_3d.png", "MAPDL 워터재킷 250A — 3D 반단면"),
              ("prius/viz/waterjacket_high/contour_z0.png", "z=0 정단면 온도"),
              ("prius/viz/waterjacket_high/component_history.png", "부품별 온도 이력"),
              ("prius/viz/waterjacket_high/transient_dashboard.gif", "과도 대시보드 (온도장+회로+이력)")],
    "e10": [("e10/viz/mapdl/cut_3d.png", "MAPDL 하이브리드 — 3D 반단면"),
            ("e10/viz/mapdl/circuit_3d.png", "FEM 위 오일 열등가회로 (노드색=온도)"),
            ("e10/viz/mapdl/contour_z0.png", "z=0 정단면 (재료 경계선)"),
            ("e10/viz/mapdl/component_history.png", "부품별 온도 이력"),
            ("e10/viz/ff_oil_iso.png", "FreeFlow SPH 오일 유동 (속도)"),
            ("e10/viz/mapdl/ff_thermal_oil_iso.png", "1-way 커플드 — 오일 온도장"),
            ("e10/viz/mapdl/transient_dashboard.gif", "과도 대시보드")],
}


def gallery(viz_root: Path, chain, gifs):
    figs = []
    for rel, cap in GALLERY[chain]:
        p = viz_root / rel
        if not p.exists() or (p.suffix == ".gif" and not gifs):
            continue
        figs.append(f"<figure><img loading='lazy' src='{embed_image(p)}' alt='{html.escape(cap)}'>"
                    f"<figcaption>{html.escape(cap)}</figcaption></figure>")
    return f"<div class='gallery'>{''.join(figs)}</div>" if figs else \
        f"<p class='muted'>그림 없음 — <code>{html.escape(str(viz_root))}</code> 확인 (--viz-root)</p>"


CSS = """
:root{--bg:#fbfaf7;--card:#fff;--ink:#211c16;--muted:#6b6258;--line:#e4dccf;--grid:#ece6dc;
--pass:#3f7d4e;--warn:#b9760a;--fail:#c0392b;--accent:#2f6f8f}
@media (prefers-color-scheme:dark){:root{--bg:#161412;--card:#1f1c19;--ink:#ece6dc;--muted:#a59b8f;
--line:#3a342d;--grid:#2c2722;--pass:#6fbf82;--warn:#e8b04a;--fail:#e5735f;--accent:#6fb1d1}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 "Malgun Gothic","Pretendard",system-ui,sans-serif}
main{max-width:1060px;margin:0 auto;padding:28px 16px 60px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:20px;margin:40px 0 10px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:15px;margin:22px 0 8px;color:var(--muted)}.muted{color:var(--muted)}code{font-size:13px}
.meta{color:var(--muted);font-size:13px}
.gates{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px;margin-top:14px}
.gate{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--muted);border-radius:8px;padding:10px 12px}
.gate.pass{border-left-color:var(--pass)}.gate.warn{border-left-color:var(--warn)}.gate.fail{border-left-color:var(--fail)}
.gate b{display:block}.gate .st{font-size:12px;font-weight:700;letter-spacing:.04em}
.pass .st{color:var(--pass)}.warn .st{color:var(--warn)}.fail .st{color:var(--fail)}.gate span{font-size:13px;color:var(--muted)}
table{border-collapse:collapse;width:100%;background:var(--card);font-size:14px;margin:6px 0;display:block;overflow-x:auto}
th,td{border-bottom:1px solid var(--line);padding:6px 10px;text-align:right;white-space:nowrap}
th[scope=row],thead th:first-child{text-align:left}thead th{color:var(--muted);font-weight:600}
td.bad{color:var(--fail);font-weight:700}
.chart{margin:8px 0;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}
svg{width:100%;height:auto;display:block}svg .grid{stroke:var(--grid)}svg .ax{fill:var(--muted);font-size:12px}
svg .val{fill:var(--ink);font-size:11px}svg .bad{fill:var(--fail);font-size:14px;font-weight:700}
svg .ref{stroke:var(--fail);stroke-dasharray:4 4}svg .ref-t{fill:var(--fail);font-size:11px}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12.5px;color:var(--muted);margin-top:6px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.gallery figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px}
.gallery img{width:100%;height:auto;border-radius:4px;background:#fff}
figcaption{font-size:13px;color:var(--muted);margin-top:4px}
.kv{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px}
.kv div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.kv b{display:block;font-size:18px}.kv span{font-size:12.5px;color:var(--muted)}
.state-정상{color:var(--pass)}.state-비물리{color:var(--fail);font-weight:700}
"""


def git_rev():
    try:
        return subprocess.run(["git", "-C", str(THERMAL), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or "?"
    except Exception:
        return "?"


def build(viz_root: Path, chains, gifs):
    prius, e10 = prius_data(), e10_data()
    gs = gates(prius, e10, e10[2])
    npass = sum(g["state"] == "pass" for g in gs)
    out = [f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
           f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>모터 열해석 리포트</title>"
           f"<style>{CSS}</style></head><body><main>",
           "<h1>모터 열해석 결과 리포트</h1>",
           f"<p class='meta'>생성 {dt.datetime.now():%Y-%m-%d %H:%M} · eMach <code>{git_rev()}</code> · "
           f"그림 <code>{html.escape(str(viz_root))}</code></p>",
           f"<h2>판정 요약 — {npass}/{len(gs)} 통과</h2><div class='gates'>"]
    label = {"pass": "통과", "warn": "주의", "fail": "불합격"}
    for g in gs:
        out.append(f"<div class='gate {g['state']}'><span class='st'>{label[g['state']]}</span>"
                   f"<b>{html.escape(g['name'])}</b><span>{html.escape(g['detail'])}</span></div>")
    out.append("</div>")

    if "prius" in chains:
        series, losses, cond = prius
        out.append("<h2>Prius — MAPDL 하이브리드 ↔ Fluent CHT ↔ Icepak</h2>"
                   f"<p class='muted'>{html.escape(cond)}. 조건 정합 = Fluent 손실 + 워터재킷(27 °C, 유효 HTC 3000). "
                   "JAC279 회로·Icepak 고정온도는 냉각 조건이 달라 참고용.</p>")
        out.append("<div class='kv'>" + "".join(
            f"<div><b>{v:.1f} W</b><span>{k}</span></div>" for k, v in losses.items() if v) + "</div>")
        out.append(svg_grouped(series, PARTS[:4], "Prius 최고온도", ref_line=(180, "H종 180 °C")))
        out.append(table(series, PARTS[:4]))
        out.append("<p class='muted'>MAPDL 워터재킷 값은 결과 JSON 이 없어 <code>prius/scripts/10_validation_matrix.py</code> 상수를 사용.</p>")
        out.append("<h3>그림</h3>" + gallery(viz_root, "prius", gifs))

    if "e10" in chains:
        series, mh, ffv = e10
        lw = mh.get("losses_W", {})
        op = (load_json(DATA_E10 / "e10_losses.json") or {}).get("_operating_point", {})
        out.append("<h2>e10 — FreeFlow 오일냉각 모터 (MAPDL ⇄ FreeFlow, Icepak)</h2>"
                   f"<p class='muted'>운전점 {op.get('ShaftSpeed', '?')} rpm / {op.get('RMSCurrent', '?')} A rms "
                   f"(Motor-CAD .mot 실측) · 오일 {mh.get('_oil', {}).get('T', '?')} °C. 손실 분포는 "
                   f"<b>{html.escape(str(mh.get('_loss_source', '')))}</b> (Motor-CAD 헤드리스 손실 0 이슈로 Prius 250A 이식).</p>")
        out.append("<div class='kv'>" + "".join(
            f"<div><b>{v:.0f} W</b><span>{k}</span></div>" for k, v in lw.items()) +
            "".join(f"<div><b>{v:.1f} °C</b><span>회로 {k}</span></div>" for k, v in mh.get("circuit_T", {}).items()) + "</div>")
        out.append(svg_grouped(series, PARTS, "e10 최고온도", ref_line=(150, "자석 150 °C")))
        out.append(table(series, PARTS))
        out.append(f"<p class='muted'>✕ / 빨간 값 = {NONPHYS:.0f} °C 초과 비물리 결과(Icepak V2 비컨포멀 discrete 바) — "
                   "실패 자체를 기록으로 남김.</p>")
        r = ffv.get("result", {})
        if r:
            out.append("<h3>FreeFlow 1-way 커플드 (MAPDL 벽온도 → 오일)</h3><div class='kv'>" + "".join(
                f"<div><b>{v} °C</b><span>벽 {k}</span></div>" for k, v in ffv.get("wall_BC_C", {}).items()) +
                f"<div><b>{r['oil_T_C']['mean']} / {r['oil_T_C']['max']} °C</b><span>오일 평균/최대</span></div>"
                f"<div><b>{r['physical_time_s']} s</b><span>물리시간 (벽시계 {fmt_time(r['wall_clock_s'])})</span></div></div>")
        tm = load_json(DATA_E10 / "timing_comparison.json") or {}
        items = [(k.split("\n")[0] + " " + " ".join(k.split("\n")[1:2]).strip("()"), v["t"], v.get("note", ""))
                 for k, v in tm.items()]
        if mh.get("_timing"):
            items.insert(1, ("MAPDL 하이브리드 과도 900s", float(mh["_timing"]["solve_time_s"]), "1.1M 절점, 22 스텝"))
        if items:
            out.append("<h3>계산 시간 (물리·스코프 상이 — 스케일 참고)</h3><div class='chart'>" + svg_timing(items) + "</div>")
        out.append("<h3>그림</h3>" + gallery(viz_root, "e10", gifs))

    out.append("<h2>결과 파일 목록</h2><table><thead><tr><th>파일</th><th>판정</th><th>최고값 °C</th><th>모델 메모</th></tr></thead><tbody>")
    for p, state, tmax, note in run_inventory():
        rel = p.relative_to(THERMAL).as_posix()
        out.append(f"<tr><th scope='row'><code>{html.escape(rel)}</code></th>"
                   f"<td class='state-{state}'>{state}</td><td>{'—' if tmax is None else f'{tmax:.1f}'}</td>"
                   f"<td style='text-align:left;white-space:normal'>{html.escape(note[:110])}</td></tr>")
    out.append("</tbody></table>")
    out.append("<p class='meta'>생성기: <code>mlxperPJT/thermal/thermal_report.py</code> · 기준값·함정: "
               "<code>.claude/skills/motor-thermal-hybrid</code></p></main></body></html>")
    return "".join(out), gs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--viz-root", type=Path, default=DEFAULT_VIZ)
    ap.add_argument("--out", type=Path,
                    default=Path(os.environ.get("THERMAL_SCRATCH", r"C:\work\thermal_scratch")) / "reports"
                    / f"thermal_report_{dt.date.today():%Y%m%d}.html")
    ap.add_argument("--chains", nargs="+", default=["prius", "e10"], choices=["prius", "e10"])
    ap.add_argument("--gifs", action="store_true", help="과도 GIF 내장 (파일이 수 MB 커짐)")
    a = ap.parse_args()
    doc, gs = build(a.viz_root, a.chains, a.gifs)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(doc, encoding="utf-8")
    print(json.dumps({"out": str(a.out), "bytes": a.out.stat().st_size,
                      "gates": {g["name"]: g["state"] for g in gs}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
