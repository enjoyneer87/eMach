# -*- coding: utf-8 -*-
"""표본선(skewed line distribution) 하이브리드 재현 vs MCAD 내부 hybrid AC loss.

MCAD 설명서(저자 제공): 근접 손실용 자속은 도체 단면을 가로지르는 표본선에서
추출되며, 선 분포는 슬롯 개구부 쪽으로 밀도를 높이고("taking more points but
attributing proportionally less weight") 각 선은 자기가 대표하는 면적으로
가중된다. 본 스크립트는 백필 MS Hybrid 필드에서 이 표본화를 재현해
기존 전면적 요소 평균(run_meshb_hybrid_all)과 MCAD 추출값 사이에 놓는다.

축 분해 실험 설계 — 커널은 고정(기존 4종 재사용), 표본만 교체:
  full-area   : 요소 전면적 가중 <B_m^2>            (기존 meshb 컬럼과 동일)
  line-sq     : 표본선 위 제곱-후-평균 (선상 <B^2>)  -> 표본 커버리지 효과만
  line-msq    : 표본선 위 평균-후-제곱 (<B>^2)       -> + 선 수준 Jensen 몫
표본선: 도체 국소 반경축(개구부=보어 쪽이 ξmin)을 따라 n_lines개 스테이션,
개구부 쪽 기하급수 간격(비 r). 선상 B = 접선 폭을 가로지르는 요소들의
면적 가중. 가중치 = 대표 반경 두께 x 도체 폭 (면적 비례).

실행: python run_line_sampled_hybrid.py --model Ref --speed 16000
산출: map_exports/e10/<M>/line_sampled_hybrid_<M>.json + 요약 표 stdout
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
sys.path.insert(0, os.path.join(HERE, "acloss_ref_methods"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from mesh_b_vs_mcad import (                                # noqa: E402
    prox_24, prox_g2, prox_g2_volpe_prime, mcad_reference,
    POLE_PAIRS, SECTORS)
from run_meshb_hybrid_all import (                          # noqa: E402
    load_series, DIMS, MCAD_JSON, BACKFILL, _DIR_RE)

KERNELS = {
    "P24_solid": lambda f, bt, br, w, h: prox_24(f, bt, br, w, h),
    "P24_cuboid6": lambda f, bt, br, w, h: prox_24(f, bt, br, w, h,
                                                   n_cuboids=6),
    "G2_solid": prox_g2,
    "Volpe_G2p": prox_g2_volpe_prime,
}


def station_bands(n_lines: int, ratio: float):
    """개구부(0) 쪽 조밀 기하급수 밴드 경계 [0,1] — 폭_j ∝ ratio^j."""
    wj = ratio ** np.arange(n_lines)
    wj = wj / wj.sum()
    edges = np.concatenate([[0.0], np.cumsum(wj)])
    mids = 0.5 * (edges[:-1] + edges[1:])
    return mids, wj


def op_line_losses(meta, BX, BY, f_e, w_c, h_c, n_lines, ratio):
    """한 OP: 표본선 두 축약(sq/msq) x 커널 4종 + full-area 4종 [기계 W]."""
    n = BX.shape[0]
    f_m = np.arange(1, n // 2 + 1) * f_e
    acc = {f"line_sq_{k}": 0.0 for k in KERNELS}
    acc.update({f"line_msq_{k}": 0.0 for k in KERNELS})
    acc.update({f"full_{k}": 0.0 for k in KERNELS})

    for c in np.unique(meta["reg"]):
        m = meta["reg"] == c
        wgt = meta["area"][m]
        x, y = meta["x"][m], meta["y"][m]
        x0 = float(np.average(x, weights=wgt))
        y0 = float(np.average(y, weights=wgt))
        th = np.arctan2(y0, x0)
        # 국소 좌표: xi = 반경(+바깥), eta = 접선. 개구부(보어) = xi 최소.
        xi = (x - x0) * np.cos(th) + (y - y0) * np.sin(th)
        b_rad = (np.cos(th) * BX[:, m] + np.sin(th) * BY[:, m]).T
        b_tan = (-np.sin(th) * BX[:, m] + np.cos(th) * BY[:, m]).T
        # 요소 조화 진폭 (기존 losses_of_op 규약: 편측 피크)
        amp_r = 2.0 * np.abs(np.fft.rfft(b_rad, axis=1))[:, 1:] / n
        amp_t = 2.0 * np.abs(np.fft.rfft(b_tan, axis=1))[:, 1:] / n
        cplx_r = 2.0 * np.fft.rfft(b_rad, axis=1)[:, 1:] / n
        cplx_t = 2.0 * np.fft.rfft(b_tan, axis=1)[:, 1:] / n

        # full-area 기준 (검증용 — 기존 컬럼과 일치해야 함)
        wn = wgt / wgt.sum()
        b2r_full = wn @ amp_r ** 2
        b2t_full = wn @ amp_t ** 2
        for k, fn in KERNELS.items():
            acc[f"full_{k}"] += fn(f_m, b2t_full, b2r_full, w_c, h_c)

        # 표본선: xi 스테이션별로 폭 전체를 가로지르는 요소 집합
        lo, hi = float(xi.min()), float(xi.max())
        mids, wj = station_bands(n_lines, ratio)
        edges = np.concatenate([[0.0], np.cumsum(wj)]) * (hi - lo) + lo
        b2r_sq = np.zeros_like(f_m, dtype=float)
        b2t_sq = np.zeros_like(b2r_sq)
        b2r_msq = np.zeros_like(b2r_sq)
        b2t_msq = np.zeros_like(b2r_sq)
        for j in range(n_lines):
            centre = lo + mids[j] * (hi - lo)
            # 선 = 스테이션에 가장 가까운 요소들의 접선 단면 (폭 전체)
            d = np.abs(xi - centre)
            band = d <= max((edges[j + 1] - edges[j]) * 0.6,
                            np.partition(d, min(4, len(d) - 1))[
                                min(4, len(d) - 1)])
            wl = wgt[band] / wgt[band].sum()
            # 제곱-후-평균 (선상 <B^2>)
            b2r_sq += wj[j] * (wl @ amp_r[band] ** 2)
            b2t_sq += wj[j] * (wl @ amp_t[band] ** 2)
            # 평균-후-제곱 (선상 <B>^2, 복소 평균의 모듈러스)
            b2r_msq += wj[j] * np.abs(wl @ cplx_r[band]) ** 2
            b2t_msq += wj[j] * np.abs(wl @ cplx_t[band]) ** 2
        for k, fn in KERNELS.items():
            acc[f"line_sq_{k}"] += fn(f_m, b2t_sq, b2r_sq, w_c, h_c)
            acc[f"line_msq_{k}"] += fn(f_m, b2t_msq, b2r_msq, w_c, h_c)

    return {k: v * SECTORS for k, v in acc.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Ref", choices=sorted(DIMS))
    ap.add_argument("--speed", type=int, default=16000)
    ap.add_argument("--n-lines", type=int, default=25)
    ap.add_argument("--ratio", type=float, default=1.12)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--temp", type=float, default=20.0,
                    help="구리 온도 [C] — MCAD 스윕(80C 등온)과 정합시키려면 80")
    ap.add_argument("--subtract-noload", action="store_true",
                    help="0.1A(≈무부하) 파형을 요소 정합해 공제 — 전기자 기여만 평가"
                         " (MCAD 내부가 no-load 공제라는 가설 검정)")
    a = ap.parse_args()
    w_c, h_c = DIMS[a.model]

    if abs(a.temp - 20.0) > 0.1:
        import mesh_b_vs_mcad as _mb
        scale = 1.0 / (1.0 + 3.93e-3 * (a.temp - 20.0))
        _mb.SIGMA *= scale
        _mb._SIGMA_V *= scale
        print(f"σ(Cu) {a.temp:g}C 적용: x{scale:.4f}", flush=True)

    dirs = []
    for d in sorted(glob.glob(os.path.join(BACKFILL, a.model,
                                           "Hybrid_Speed_*"))):
        m = _DIR_RE.search(os.path.basename(d))
        if m and int(m.group(1)) == a.speed:
            dirs.append((d, float(m.group(2)), float(m.group(3))))
    if a.limit:
        dirs = dirs[:a.limit]
    print(f"[{a.model}] {a.speed} RPM, OP {len(dirs)}개, "
          f"표본선 {a.n_lines}개 (r={a.ratio})", flush=True)

    from pathlib import Path
    refs = {}
    f_e = a.speed * POLE_PAIRS / 60.0
    rows, t0 = [], time.time()

    noload = {}          # phase_deg -> (tree, BX0, BY0, n_steps)
    if a.subtract_noload:
        from scipy.spatial import cKDTree
        for d, cur, ph in dirs:
            if cur < 1.0:
                f0 = os.path.join(d, "FEA_data.txt.gz")
                if os.path.exists(f0):
                    m0, bx0, by0 = load_series(f0)
                    tree = cKDTree(np.column_stack([m0["x"], m0["y"]]))
                    noload[ph] = (tree, bx0, by0)
        assert noload, "무부하(0.1A) 수출 없음"
        print(f"무부하 기준 파형: {sorted(noload)} deg", flush=True)

    for i, (d, cur, ph) in enumerate(dirs):
        f = os.path.join(d, "FEA_data.txt.gz")
        if not os.path.exists(f):
            continue
        if a.subtract_noload and cur < 1.0:
            continue
        meta, BX, BY = load_series(f)
        if a.subtract_noload:
            tree, bx0, by0 = noload.get(ph) or noload[sorted(noload)[0]]
            _, idx = tree.query(np.column_stack([meta["x"], meta["y"]]))
            n_min = min(BX.shape[0], bx0.shape[0])
            BX = BX[:n_min] - bx0[:n_min][:, idx]
            BY = BY[:n_min] - by0[:n_min][:, idx]
        acc = op_line_losses(meta, BX, BY, f_e, w_c, h_c,
                             a.n_lines, a.ratio)
        if cur not in refs:
            refs[cur] = mcad_reference(Path(MCAD_JSON[a.model]), cur)
        e = refs[cur].get((a.speed, ph), {})
        row = {"speed_rpm": a.speed, "current_A": cur, "phase_deg": ph,
               "mcad_prox_W": e.get("prox_W"), **acc}
        rows.append(row)
        mc = e.get("prox_W") or float("nan")
        print(f"  [{i+1}/{len(dirs)}] {cur:g}A/{ph:g}deg  "
              f"MCADpx {mc/1e3:6.2f} kW | lineV "
              f"{acc['line_msq_Volpe_G2p']/1e3:6.2f} | "
              f"full V {acc['full_Volpe_G2p']/1e3:6.2f} | "
              f"line24c {acc['line_msq_P24_cuboid6']/1e3:6.2f}",
              flush=True)

    suf = f"_{a.temp:g}C" if abs(a.temp - 20.0) > 0.1 else ""
    if a.subtract_noload:
        suf += "_armOnly"
    out = os.path.join(HERE, "map_exports", "e10", a.model,
                       f"line_sampled_hybrid_{a.model}{suf}.json")
    json.dump({"rows": rows,
               "_meta": {"speed": a.speed, "n_lines": a.n_lines,
                         "ratio": a.ratio, "temp_C": a.temp,
                         "kernels": list(KERNELS)}},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out)

    # 요약: MCAD prox 대비 비율 (0.1 A 링 제외)
    sel = [r for r in rows if r["current_A"] > 1 and r["mcad_prox_W"]]
    if sel:
        mc = np.array([r["mcad_prox_W"] for r in sel])
        print("\n=== MCAD prox 대비 비율 (평균 [min~max]) ===")
        for k in sorted(sel[0]):
            if k.startswith(("line_", "full_")):
                v = np.array([r[k] for r in sel]) / mc
                print(f"  {k:24s} {v.mean():6.3f}  "
                      f"[{v.min():5.3f} ~ {v.max():5.3f}]")
    print(f"({(time.time()-t0)/60:.1f}분)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
