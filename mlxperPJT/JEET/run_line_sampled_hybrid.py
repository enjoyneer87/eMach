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
sys.path.insert(0, HERE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from acloss_ref_methods.mesh_b_vs_mcad import (             # noqa: E402
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
        # 기본파 한정 변형 (m=1) — 고조파 m^2 가중 몫의 분해용
        for k in ("P24_cuboid6", "G2_solid", "Volpe_G2p"):
            acc.setdefault(f"line_msq_fund_{k}", 0.0)
            acc[f"line_msq_fund_{k}"] += KERNELS[k](
                f_m[:1], b2t_msq[:1], b2r_msq[:1], w_c, h_c)
        # 전환-캡 /24 (Volpe 2019 III-C 재현): delta(f_t)=h_c 위에서 f^2 -> f_t*f
        from acloss_ref_methods import mesh_b_vs_mcad as _mb
        f_t = 1.0 / (np.pi * 4e-7 * np.pi * _mb.SIGMA * h_c ** 2)
        cap = np.minimum(1.0, f_t / f_m)
        acc.setdefault("line_msq_P24c6_translim", 0.0)
        acc["line_msq_P24c6_translim"] += KERNELS["P24_cuboid6"](
            f_m * np.sqrt(cap), b2t_msq, b2r_msq, w_c, h_c)
        # 접선 고조파 함량 진단: sum(m^2 B_m^2)/(1 B_1^2) (도체 면적 가중 합산)
        acc.setdefault("_harm_num", 0.0)
        acc.setdefault("_harm_den", 0.0)
        mm2 = (np.arange(1, len(b2t_msq) + 1)) ** 2
        acc["_harm_num"] += float(np.sum(mm2 * b2t_msq)) * wgt.sum()
        acc["_harm_den"] += float(b2t_msq[0]) * wgt.sum()
        # 도체 합 스펙트럼 (커널이 b2에 선형이라 합으로 기계 총량 재구성 가능)
        acc.setdefault("_b2t_sum", np.zeros(len(f_m)))
        acc.setdefault("_b2r_sum", np.zeros(len(f_m)))
        acc["_b2t_sum"] = acc["_b2t_sum"] + b2t_msq
        acc["_b2r_sum"] = acc["_b2r_sum"] + b2r_msq

    out = {k: v * SECTORS for k, v in acc.items() if not k.startswith("_")}
    out["harm_weight_factor_tan"] = acc["_harm_num"] / max(acc["_harm_den"],
                                                           1e-30)
    out["b2t_msq_sum"] = [float(f"{v:.6g}") for v in acc["_b2t_sum"]]
    out["b2r_msq_sum"] = [float(f"{v:.6g}") for v in acc["_b2r_sum"]]
    return out


SWEEP_CONFIGS = [(15, 1.0), (15, 1.12), (25, 1.0), (25, 1.12), (25, 1.25),
                 (40, 1.0), (40, 1.12), (40, 1.25), (60, 1.12), (100, 1.12)]


def op_sweep_losses(meta, BX, BY, f_e, w_c, h_c, configs):
    """한 OP: (n_lines, ratio) 구성별 translim P24c6 [기계 W] — 파싱 1회 공유."""
    from acloss_ref_methods import mesh_b_vs_mcad as _mb
    n = BX.shape[0]
    f_m = np.arange(1, n // 2 + 1) * f_e
    f_t = 1.0 / (np.pi * 4e-7 * np.pi * _mb.SIGMA * h_c ** 2)
    cap = np.sqrt(np.minimum(1.0, f_t / f_m))
    acc = {f"n{nl}_r{r:g}": 0.0 for nl, r in configs}
    for c in np.unique(meta["reg"]):
        m = meta["reg"] == c
        wgt = meta["area"][m]
        x, y = meta["x"][m], meta["y"][m]
        x0 = float(np.average(x, weights=wgt))
        y0 = float(np.average(y, weights=wgt))
        th = np.arctan2(y0, x0)
        xi = (x - x0) * np.cos(th) + (y - y0) * np.sin(th)
        b_rad = (np.cos(th) * BX[:, m] + np.sin(th) * BY[:, m]).T
        b_tan = (-np.sin(th) * BX[:, m] + np.cos(th) * BY[:, m]).T
        cplx_r = 2.0 * np.fft.rfft(b_rad, axis=1)[:, 1:] / n
        cplx_t = 2.0 * np.fft.rfft(b_tan, axis=1)[:, 1:] / n
        lo, hi = float(xi.min()), float(xi.max())
        for nl, r in configs:
            mids, wj = station_bands(nl, r)
            edges = np.concatenate([[0.0], np.cumsum(wj)]) * (hi - lo) + lo
            b2r = np.zeros(len(f_m))
            b2t = np.zeros(len(f_m))
            for j in range(nl):
                centre = lo + mids[j] * (hi - lo)
                d = np.abs(xi - centre)
                band = d <= max((edges[j + 1] - edges[j]) * 0.6,
                                np.partition(d, min(4, len(d) - 1))[
                                    min(4, len(d) - 1)])
                wl = wgt[band] / wgt[band].sum()
                b2r += wj[j] * np.abs(wl @ cplx_r[band]) ** 2
                b2t += wj[j] * np.abs(wl @ cplx_t[band]) ** 2
            acc[f"n{nl}_r{r:g}"] += KERNELS["P24_cuboid6"](
                f_m * cap, b2t, b2r, w_c, h_c)
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
    ap.add_argument("--sweep", action="store_true",
                    help="(n_lines, ratio) 구성 스윕 — translim P24c6만, 파싱 공유")
    ap.add_argument("--fields-dir", default=None,
                    help="필드 수출 루트 재지정 (기본: BACKFILL/<model>) — "
                         "e4a 등 외부 기계용")
    ap.add_argument("--w-mm", type=float, default=None,
                    help="도체 반경 치수 재지정 [mm] (DIMS 첫 값 규약)")
    ap.add_argument("--h-mm", type=float, default=None,
                    help="도체 접선 치수 재지정 [mm] (DIMS 둘째 값 규약)")
    ap.add_argument("--mcad-json", default=None,
                    help="MCAD 요약 JSON 재지정 (kturn 포맷 호환)")
    ap.add_argument("--tag", default=None,
                    help="출력 파일 태그 재지정 (기본: model)")
    ap.add_argument("--tier", type=float, default=None,
                    help="이 전류 티어만 처리 [A] (허용오차 ±1)")
    ap.add_argument("--subtract-noload", action="store_true",
                    help="0.1A(≈무부하) 파형을 요소 정합해 공제 — 전기자 기여만 평가"
                         " (MCAD 내부가 no-load 공제라는 가설 검정)")
    a = ap.parse_args()
    w_c, h_c = DIMS[a.model]
    if a.w_mm:
        w_c = a.w_mm * 1e-3
    if a.h_mm:
        h_c = a.h_mm * 1e-3
    tag = a.tag or a.model

    if abs(a.temp - 20.0) > 0.1:
        from acloss_ref_methods import mesh_b_vs_mcad as _mb
        scale = 1.0 / (1.0 + 3.93e-3 * (a.temp - 20.0))
        _mb.SIGMA *= scale
        _mb._SIGMA_V *= scale
        print(f"σ(Cu) {a.temp:g}C 적용: x{scale:.4f}", flush=True)

    field_root = a.fields_dir or os.path.join(BACKFILL, a.model)
    dirs = []
    for d in sorted(glob.glob(os.path.join(field_root, "Hybrid_Speed_*"))):
        m = _DIR_RE.search(os.path.basename(d))
        if m and (a.speed == 0 or int(m.group(1)) == a.speed):
            if a.tier is not None and abs(float(m.group(2)) - a.tier) > 1.0:
                continue
            dirs.append((d, int(m.group(1)), float(m.group(2)),
                         float(m.group(3))))
    if a.limit:
        dirs = dirs[:a.limit]
    print(f"[{a.model}] {'전속도' if a.speed == 0 else a.speed} RPM, "
          f"OP {len(dirs)}개, 표본선 {a.n_lines}개 (r={a.ratio})", flush=True)

    from pathlib import Path
    from acloss_ref_methods.volpe_hybrid_acloss import calc_skin_loss
    from acloss_ref_methods import mesh_b_vs_mcad as _mb
    refs = {}
    rows, t0 = [], time.time()

    noload = {}          # (spd, phase) -> (tree, BX0, BY0)
    if a.subtract_noload:
        from scipy.spatial import cKDTree
        for d, spd, cur, ph in dirs:
            if cur < 1.0:
                f0 = os.path.join(d, "FEA_data.txt.gz")
                if os.path.exists(f0):
                    m0, bx0, by0 = load_series(f0)
                    tree = cKDTree(np.column_stack([m0["x"], m0["y"]]))
                    noload[(spd, ph)] = (tree, bx0, by0)
        assert noload, "무부하(0.1A) 수출 없음"
        print(f"무부하 기준 파형: {len(noload)}개", flush=True)

    for i, (d, spd, cur, ph) in enumerate(dirs):
        f = os.path.join(d, "FEA_data.txt.gz")
        if not os.path.exists(f):
            f = os.path.join(d, "FEA_data.txt")
        if not os.path.exists(f):
            continue
        if a.subtract_noload and cur < 1.0:
            continue
        f_e = spd * POLE_PAIRS / 60.0
        meta, BX, BY = load_series(f)
        if a.sweep:
            acc = op_sweep_losses(meta, BX, BY, f_e, w_c, h_c,
                                  SWEEP_CONFIGS)
            if cur not in refs:
                refs[cur] = mcad_reference(Path(MCAD_JSON[a.model]), cur)
            e = refs[cur].get((spd, ph), {})
            rows.append({"speed_rpm": spd, "current_A": cur,
                         "phase_deg": ph,
                         "mcad_prox_W": e.get("prox_W"), **acc})
            print(f"  [{i+1}/{len(dirs)}] {spd}/{cur:g}A/{ph:g}deg sweep OK",
                  flush=True)
            continue
        if a.subtract_noload:
            key = (spd, ph)
            tree, bx0, by0 = noload.get(key) or noload[sorted(noload)[0]]
            _, idx = tree.query(np.column_stack([meta["x"], meta["y"]]))
            n_min = min(BX.shape[0], bx0.shape[0])
            BX = BX[:n_min] - bx0[:n_min][:, idx]
            BY = BY[:n_min] - by0[:n_min][:, idx]
        acc = op_line_losses(meta, BX, BY, f_e, w_c, h_c,
                             a.n_lines, a.ratio)
        # skin 초과분 (병렬 1경로, 온도 반영 σ) — 공개 분모 총량용
        try:
            sk = calc_skin_loss(w_c, h_c, f_e, _mb.L_ACTIVE, cur,
                                sigma=_mb.SIGMA)
        except TypeError:
            sk = calc_skin_loss(w_c, h_c, f_e, _mb.L_ACTIVE, cur)
        acc["skin_excess_W"] = sk["P_excess_W"] * 48 * 6
        if cur not in refs:
            try:
                refs[cur] = mcad_reference(
                    Path(a.mcad_json or MCAD_JSON[a.model]), cur)
            except Exception:
                refs[cur] = {}
        e = refs[cur].get((spd, ph), {})
        row = {"speed_rpm": spd, "current_A": cur, "phase_deg": ph,
               "mcad_prox_W": e.get("prox_W"),
               "mcad_skin_W": e.get("skin_W"),
               "ts_ac_W": e.get("ts_W"), **acc}
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
    if a.sweep:
        suf += "_sweep"
    out_dir = os.path.join(HERE, "map_exports", "e10", tag)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"line_sampled_hybrid_{tag}{suf}.json")
    json.dump({"rows": rows,
               "_meta": {"speed": a.speed, "n_lines": a.n_lines,
                         "ratio": a.ratio, "temp_C": a.temp,
                         "kernels": list(KERNELS)}},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out)

    # 요약: MCAD prox 대비 비율 (0.1 A 링 제외)
    sel = [r for r in rows if r["current_A"] > 1 and r["mcad_prox_W"]]
    if sel and a.sweep:
        mc = np.array([r["mcad_prox_W"] for r in sel])
        print("\n=== 스윕: translim P24c6 / 해석-FEA 기준 (평균, [min~max], corr) ===")
        for nl, r0 in SWEEP_CONFIGS:
            k = f"n{nl}_r{r0:g}"
            v = np.array([r[k] for r in sel])
            rr = v / mc
            corr = float(np.corrcoef(v, mc)[0, 1])
            print(f"  {k:12s} {rr.mean():6.3f} [{rr.min():5.3f}~{rr.max():5.3f}]"
                  f"  corr {corr:.4f}")
        sel = []
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
