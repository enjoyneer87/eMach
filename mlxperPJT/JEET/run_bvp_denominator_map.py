# -*- coding: utf-8 -*-
"""BVP 분모 전 맵 산출 — 도체별 2-D 확산 경계값 해로 AC 손실 평가.

3-family 분모 비교의 마지막 조각 (저자 요청 2026-07-28):
    큐보이드 평균장(생산 MCAD)  AF ~ 2.25 / 1.51
    요소 분해 조화 평가(mesh-B) AF ~ 0.60 ~ 0.80
    2-D 확산 BVP (본 스크립트)  AF = ?

방법: `field_metrics.conductor_je_2d` 의 정식화를 그대로 옮기되
  (lap - j w mu sigma)A = -mu sigma E0,  A|_bd = A_MS|_bd,  I_net 구속
조화 영역으로 확장한다 — MS 여자(A 시계열)를 요소별 FFT 해 복소 A_m 을
얻고, 각 조화 m 을 각주파수 m*w_e 로 **복소 경계 조건** 그대로 푼다
(선형계가 복소이므로 경계·순전류 위상이 자연히 전달된다). 도체당 손실은
    P = L_active * sum_m sum_cells |J_m|^2 / (2 sigma) * cell
이고, AC 초과분은 수송 기본파의 DC 손실을 빼서 얻는다:
    P_AC = P_total - L_active * |I_1|^2 / (2 sigma A_cu).

원 솔버와의 차이 2가지: ① 반환이 유도 성분(je, 평균 제거)이 아니라
총 J (수송+표피+근접+교차) 손실, ② 실수 스냅숏 1개가 아니라 조화별
복소해 합산. 여자·경계·격자 규약은 동일.

핵심 절감: MS 필드는 속도 불변(§12.6 실증)이므로 (I,beta)당 한 번만
파싱/FFT 하고 4개 속도는 f_e 만 바꿔 푼다. HalfSC 는 캠페인 필드
(HalfSC_campaign, 16k 명명) 우선 + 스윕 폴백 — run_meshb_halfsc_campaign
과 동일 규약.

실행:  python run_bvp_denominator_map.py --model Ref [--workers 8]
산출:  map_exports/e10/{model}/bvp_denominator_{model}.json
"""
from __future__ import annotations

import argparse
import glob as _glob
import gzip
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
sys.path.insert(0, HERE)

from jeet_acloss_rbf.field_metrics import (          # noqa: E402
    _locate_blocks, _parse_regions, _build_block_dict, slot_conductor_codes)
from acloss_ref_methods.mesh_b_vs_mcad import (      # noqa: E402
    mcad_reference, L_ACTIVE, POLE_PAIRS, SECTORS)

from jeet_acloss_rbf.repro_env import data_root      # noqa: E402

BACKFILL = os.path.join(os.environ.get("JEET_FEA_ROOT", ""), "_txt_backfill")
E10 = data_root()
SLOTS = range(1, 7)
SIGMA, MU0 = 4.709e7, 4e-7 * np.pi
SPEEDS = (2000, 4000, 8000, 16000)
DIMS = {"Ref": (3.711e-3, 1.686e-3),      # (폭 w_c[m], 반경 두께 h_c[m])
        "HalfSC": (5.5665e-3, 2.529e-3),
        "SC": (7.422e-3, 3.372e-3)}
MCAD_JSON = {m: os.path.join(E10, m, f"JEET_ACLoss_{m}_Map_Summary.json")
             for m in DIMS}
_DIR_RE = re.compile(r"Hybrid_Speed_(\d+)RPM_([\d.]+)A_([\d.]+)deg$")
NEAR_MM = 6.0                 # 경계 보간에 쓸 이웃 요소 반경 (원 솔버와 동일)
H_CUM, H_CAP = 0.999, 15      # 조화 선택: 에너지 프록시 누적 99.9%, m<=15


# ──────────────────────────────────────────────────────────────────────
# 입력: (I,beta) 필드 파일 한 개 → 도체 기하 + A/I 조화 계수
# ──────────────────────────────────────────────────────────────────────

def parse_op_field(path: str):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()
    blocks, regions_tbl = _locate_blocks(lines)
    meta = None
    Aser = None
    Jser: dict[int, list] = {}
    for bi, blk in enumerate(blocks):
        names, jval, sigma_tbl = _parse_regions(
            lines, blk["tables"].get("RegionsTable", regions_tbl))
        p = _build_block_dict(lines, blk, names, jval, sigma_tbl, path,
                              len(blocks))
        if meta is None:
            codes = []
            for s in SLOTS:
                cs = sorted(slot_conductor_codes(p, s),
                            key=lambda c: np.hypot(
                                p["x_mm"][p["reg"] == c],
                                p["y_mm"][p["reg"] == c]).mean())
                codes.append((s, cs))
            allc = [c for _, cs in codes for c in cs]
            cx = {c: (float(p["x_mm"][p["reg"] == c].mean()),
                      float(p["y_mm"][p["reg"] == c].mean())) for c in allc}
            keep = np.zeros(len(p["x_mm"]), bool)
            for c in allc:
                keep |= (np.hypot(p["x_mm"] - cx[c][0],
                                  p["y_mm"] - cx[c][1]) < NEAR_MM + 1.5)
            area_code = {c: float(p["area_mm2"][p["reg"] == c].sum())
                         for c in allc}
            slot_ang = {}
            for s, cs in codes:
                xs = np.concatenate([p["x_mm"][p["reg"] == c] for c in cs])
                ys = np.concatenate([p["y_mm"][p["reg"] == c] for c in cs])
                for c in cs:
                    slot_ang[c] = float(np.arctan2(ys.mean(), xs.mean()))
            meta = {"x": p["x_mm"][keep], "y": p["y_mm"][keep],
                    "reg": p["reg"][keep], "keep": keep, "codes": allc,
                    "center": cx, "slot_ang": slot_ang,
                    "area_code": area_code}
            Aser = np.empty((len(blocks), int(keep.sum())))
        Aser[bi] = p["a_wbm"][meta["keep"]]
        for c in meta["codes"]:
            Jser.setdefault(c, []).append(float((jval or {}).get(c, 0.0)))
    n = Aser.shape[0]
    Am = 2.0 * np.fft.rfft(Aser, axis=0)[1:] / n          # (nh, nkept) 복소
    Im = {c: 2.0 * np.fft.rfft(np.asarray(v))[1:] / n *
          meta["area_code"][c] * 1e-6                      # [A] 복소 피크
          for c, v in Jser.items()}
    return meta, Am, Im, n


# ──────────────────────────────────────────────────────────────────────
# 도체 하나·조화 하나의 복소 BVP (conductor_je_2d 이식, 총 J 반환)
# ──────────────────────────────────────────────────────────────────────

def solve_bar(meta, a_m, code, w_m_mm, h_m_mm, freq_hz, i_net, nx, ny):
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    from scipy.interpolate import griddata

    ang = meta["slot_ang"][code]
    c, s = np.cos(-ang), np.sin(-ang)
    R = np.array([[c, -s], [s, c]])
    mreg = meta["reg"] == code
    xy_loc = np.column_stack([meta["x"][mreg], meta["y"][mreg]]) @ R.T
    r_c, t_c = float(xy_loc[:, 0].mean()), float(xy_loc[:, 1].mean())

    rr = np.linspace(-h_m_mm / 2, h_m_mm / 2, ny)
    tt = np.linspace(-w_m_mm / 2, w_m_mm / 2, nx)
    RR, TT = np.meshgrid(rr, tt, indexing="ij")
    loc = np.column_stack([(RR + r_c).ravel(), (TT + t_c).ravel()])
    glob_xy = loc @ R

    near = np.hypot(meta["x"] - glob_xy[:, 0].mean(),
                    meta["y"] - glob_xy[:, 1].mean()) < NEAR_MM
    pts = np.column_stack([meta["x"][near], meta["y"][near]])
    a_bc = np.zeros(glob_xy.shape[0], complex)
    for part, sel in ((np.real, 0), (np.imag, 1)):
        v = griddata(pts, part(a_m[near]), glob_xy, method="linear")
        vn = griddata(pts, part(a_m[near]), glob_xy, method="nearest")
        v = np.where(np.isnan(v), vn, v)
        a_bc += v if sel == 0 else 1j * v
    a_bc = a_bc.reshape(ny, nx)

    dx = (rr[1] - rr[0]) * 1e-3
    dy = (tt[1] - tt[0]) * 1e-3
    omega = 2.0 * np.pi * freq_hz
    k2 = 1j * omega * MU0 * SIGMA
    ntot = nx * ny
    idx = np.arange(ntot).reshape(ny, nx)
    rows, cols, vals = [], [], []
    rhs_h = np.zeros(ntot, complex)
    rhs_p = np.zeros(ntot, complex)
    for i in range(ny):
        for j in range(nx):
            q = idx[i, j]
            if i in (0, ny - 1) or j in (0, nx - 1):
                rows.append(q); cols.append(q); vals.append(1.0)
                rhs_h[q] = a_bc[i, j]
                continue
            rows += [q] * 5
            cols += [q, idx[i - 1, j], idx[i + 1, j],
                     idx[i, j - 1], idx[i, j + 1]]
            vals += [-2 / dx ** 2 - 2 / dy ** 2 - k2,
                     1 / dx ** 2, 1 / dx ** 2, 1 / dy ** 2, 1 / dy ** 2]
            rhs_p[q] = -MU0 * SIGMA
    M = sp.csr_matrix((vals, (rows, cols)), shape=(ntot, ntot), dtype=complex)
    lu = spl.splu(M.tocsc())
    a_h = lu.solve(rhs_h)
    a_p = lu.solve(rhs_p)
    # 사다리꼴 노드 가중 — linspace 끝점 포함 격자에서 노드당 dx*dy 를
    # 일괄 곱하면 유효 면적이 (nx/(nx-1))(ny/(ny-1))배 과대해져 순전류
    # 구속·손실이 저평가된다(2 kRPM AC 가 음수로 나온 원인, 실제로 겪음).
    wy = np.ones(ny); wy[0] = wy[-1] = 0.5
    wx = np.ones(nx); wx[0] = wx[-1] = 0.5
    wq = (wy[:, None] * wx[None, :]).ravel() * dx * dy
    s1 = ((-1j * omega * SIGMA * a_h) * wq).sum()
    s2 = ((SIGMA * (1.0 - 1j * omega * a_p)) * wq).sum()
    e0 = (i_net - s1) / s2
    j_tot = SIGMA * (-1j * omega * (a_h + e0 * a_p) + e0)
    return float(((np.abs(j_tot) ** 2) * wq).sum() / (2.0 * SIGMA))  # W/m


# ──────────────────────────────────────────────────────────────────────

def pick_harmonics(meta, Am, code):
    mreg = meta["reg"] == code
    a = Am[:, mreg]
    a = a - a.mean(axis=1, keepdims=True)
    m_idx = np.arange(1, Am.shape[0] + 1)
    w = (m_idx ** 2) * np.mean(np.abs(a) ** 2, axis=1)
    order = np.argsort(w)[::-1]
    csum = np.cumsum(w[order]) / max(w.sum(), 1e-300)
    nkeep = int(np.searchsorted(csum, H_CUM) + 1)
    sel = set(m_idx[order[:nkeep]].tolist()) | {1}
    return sorted(m for m in sel if m <= H_CAP)


def op_worker(args):
    model, cur, ph, field_path = args
    w_c, h_c = DIMS[model]
    ny = max(26, int(np.ceil(h_c * 1e3 / 0.08)))
    nx = max(38, int(np.ceil(w_c * 1e3 / 0.10)))
    try:
        meta, Am, Im, nstep = parse_op_field(field_path)
    except Exception as ex:
        return [{"error": f"{cur}/{ph}: parse {ex}", "current_A": cur,
                 "phase_deg": ph}]
    rows = []
    for spd in SPEEDS:
        f_e = spd * POLE_PAIRS / 60.0
        p_tot = p_dc = 0.0
        n_h = 0
        for code in meta["codes"]:
            sel = pick_harmonics(meta, Am, code)
            n_h = max(n_h, len(sel))
            for m in sel:
                p_tot += solve_bar(meta, Am[m - 1], code,
                                   w_c * 1e3, h_c * 1e3,
                                   m * f_e, Im[code][m - 1], nx, ny)
            p_dc += (np.abs(Im[code][0]) ** 2) / (2.0 * SIGMA * w_c * h_c)
        bvp_total = p_tot * L_ACTIVE * SECTORS
        bvp_dc = p_dc * L_ACTIVE * SECTORS
        rows.append({"speed_rpm": spd, "current_A": cur, "phase_deg": ph,
                     "bvp_total_W": bvp_total, "bvp_dc_W": bvp_dc,
                     "bvp_ac_W": bvp_total - bvp_dc,
                     "n_harm_max": n_h, "n_steps": nstep,
                     "nx_ny": [nx, ny]})
    return rows


def field_file_for(model, cur_s, ph_s):
    """(I,beta) 의 MS 필드 파일 — 16k 우선(속도 불변), HalfSC 는 캠페인 우선.

    cur_s/ph_s 는 디렉토리명에서 정규식으로 추출한 **원문 문자열**이다 ---
    float 재포맷(:g)은 '460.0A' 를 '460A' 로 바꿔 전부 미스한다(실제로 겪음).
    """
    cands = []
    if model == "HalfSC":
        cands.append(os.path.join(
            BACKFILL, "HalfSC_campaign",
            f"Hybrid_Speed_16000RPM_{cur_s}A_{ph_s}deg", "FEA_data.txt.gz"))
    for spd in (16000, 8000, 4000, 2000):
        cands.append(os.path.join(
            BACKFILL, model, f"Hybrid_Speed_{spd}RPM_{cur_s}A_{ph_s}deg",
            "FEA_data.txt.gz"))
    for f in cands:
        if os.path.exists(f):
            return f
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(DIMS))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--only", help="'cur,ph' 한 조합만 (스모크용, 예: 460.0,36.0)")
    a = ap.parse_args()

    src_dirs = _glob.glob(os.path.join(BACKFILL, a.model, "Hybrid_Speed_*"))
    if a.model == "HalfSC":
        src_dirs += _glob.glob(os.path.join(
            BACKFILL, "HalfSC_campaign", "Hybrid_Speed_*"))
    combos = {}
    for d in src_dirs:
        m = _DIR_RE.search(os.path.basename(d))
        if m:
            combos[(float(m.group(2)), float(m.group(3)))] = (
                m.group(2), m.group(3))
    tasks = []
    for (cur, ph), (cur_s, ph_s) in sorted(combos.items()):
        f = field_file_for(a.model, cur_s, ph_s)
        if f:
            tasks.append((a.model, cur, ph, f))
    if a.only:
        oc, op_ = (float(v) for v in a.only.split(","))
        tasks = [t for t in tasks if t[1] == oc and t[2] == op_]
    if a.limit:
        tasks = tasks[:a.limit]
    print(f"[{a.model}] (I,beta) {len(tasks)}개 x {len(SPEEDS)}속도, "
          f"workers={a.workers}", flush=True)

    t0 = time.time()
    all_rows = []
    if a.workers > 1:
        from multiprocessing import Pool
        with Pool(a.workers) as pool:
            for i, rows in enumerate(pool.imap_unordered(op_worker, tasks)):
                all_rows += rows
                r0 = rows[0]
                print(f"  [{i+1}/{len(tasks)}] {r0.get('current_A')}A/"
                      f"{r0.get('phase_deg')}deg done "
                      f"({time.time()-t0:.0f}s)", flush=True)
    else:
        for i, t in enumerate(tasks):
            all_rows += op_worker(t)
            print(f"  [{i+1}/{len(tasks)}] {t[1]}A/{t[2]}deg "
                  f"({time.time()-t0:.0f}s)", flush=True)

    # TS/MCAD 참조 결합
    refs = {}
    ok_rows = [r for r in all_rows if "error" not in r]
    for r in ok_rows:
        cur = r["current_A"]
        if cur not in refs:
            refs[cur] = mcad_reference(Path(MCAD_JSON[a.model]), cur)
        e = refs[cur].get((r["speed_rpm"], r["phase_deg"]), {})
        r["ts_ac_W"] = e.get("ts_W")
        r["mcad_total_W"] = e.get("total_W")
    errs = [r for r in all_rows if "error" in r]

    out = os.path.join(E10, a.model, f"bvp_denominator_{a.model}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"rows": ok_rows, "errors": errs,
               "_meta": {"model": a.model, "conductor_m": list(DIMS[a.model]),
                         "sigma": SIGMA, "L_active_m": L_ACTIVE,
                         "sectors": SECTORS, "h_cum": H_CUM, "h_cap": H_CAP,
                         "formulation": "per-conductor complex-harmonic 2-D "
                                        "diffusion BVP, MS-frozen boundary A"
                                        " (conductor_je_2d port, total J)",
                         "ac_definition": "bvp_total - |I1|^2 R_dc(copper)",
                         "field_reuse": "speed-invariant MS field, one parse"
                                        " per (I,beta)"}},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"저장: {out}  ({len(ok_rows)}행, 오류 {len(errs)})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
