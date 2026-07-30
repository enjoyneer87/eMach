# -*- coding: utf-8 -*-
"""전 운전점 mesh-B 기반 하이브리드 AC 손실 재계산 -> JSON.

동기 (저자 요청): AF 분모(hybrid)는 지금까지 Motor-CAD 가 내부 평균한
AC 손실을 그대로 추출한 값이다. 백필로 전 운전점의 슬롯 B(MS Hybrid
export)가 텍스트로 확보되었으므로, 분모를 필드에서 직접 재계산해
운전점별 JSON 으로 만든다 --- acloss_ref_methods/mesh_b_vs_mcad.py 의
검증된 수식(P24 solid / P24 cuboid6 / G2 solid / Volpe G2':MCAD 내부
방식)을 그대로 재사용하되, 사전 추출 B JSON 단계를 생략하고 백필 gz 를
스트리밍 파싱한다.

이전 스팟 비교(mesh_b_vs_mcad_sc*.json)의 확장판이며, 당시 SC 는 MS
export 소실로 TS .mes 의 B(와전류 반작용 포함)를 쓰던 한계가 있었다 ---
본 실행은 세 모델 모두 백필된 순수 MS Hybrid B 를 사용한다.

산출 행: 운전점 + 4개 prox 방법(기계 전체 W) + skin(기본파, Dowell M)
+ MCAD 추출 prox/skin + TS-FEA AC 총손실 + 주요 비율.

실행:  python run_meshb_hybrid_all.py --model Ref [--shard K --nshards N]
산출:  map_exports/e10/<Model>/meshb_hybrid_losses_<Model>[_sK].json
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
sys.path.insert(0, os.path.join(HERE, "acloss_ref_methods"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from jeet_acloss_rbf.field_metrics import (                 # noqa: E402
    _locate_blocks, _parse_regions, _build_block_dict,
    slot_conductor_codes)
from mesh_b_vs_mcad import (                                # noqa: E402
    prox_24, prox_g2, prox_g2_volpe_prime, mcad_reference,
    L_ACTIVE, POLE_PAIRS, SECTORS)
from volpe_hybrid_acloss import calc_skin_loss              # noqa: E402

BACKFILL = r"D:\KangDH\Thesis\e10\_txt_backfill"
E10 = os.path.join(HERE, "map_exports", "e10")
SLOTS = range(1, 7)                     # 1섹터 = 6슬롯 x 6도체 = 36도체
_DIR_RE = re.compile(r"Hybrid_Speed_(\d+)RPM_([\d.]+)A_([\d.]+)deg$")

# 도체 순동 치수 [m] (mesh_b_vs_mcad MODELS 와 동일 계열, Ref = SC/2)
DIMS = {"Ref": (3.711e-3, 1.686e-3),
        "HalfSC": (5.5665e-3, 2.529e-3),
        "SC": (7.422e-3, 3.372e-3)}
MCAD_JSON = {"Ref": os.path.join(E10, "Ref", "JEET_ACLoss_Ref_Map_Summary.json"),
             "HalfSC": os.path.join(E10, "HalfSC", "JEET_ACLoss_HalfSC_Map_Summary.json"),
             "SC": os.path.join(E10, "SC", "JEET_ACLoss_SC_Map_Summary.json")}
N_COND_MACHINE = 48 * 6                 # skin: 기계 전체 도체 수
N_PARALLEL = 1                          # 병렬 회로 수 (.mot ParallelPaths=1 실측,
                                        # 저자 확인 2026-07-31 — 구값 2는 오류:
                                        # skin_excess_W 열이 4배 과소였음)


def load_series(path):
    """gz FEA txt -> 슬롯1~6 도체 요소의 Bx,By 시계열 + 면적/영역."""
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()
    blocks, regions_tbl = _locate_blocks(lines)
    BX = BY = None
    meta = None
    for bi, blk in enumerate(blocks):
        names, jval, sigma = _parse_regions(
            lines, blk["tables"].get("RegionsTable", regions_tbl))
        p = _build_block_dict(lines, blk, names, jval, sigma, path,
                              len(blocks))
        if meta is None:
            codes = set()
            for s in SLOTS:
                codes |= slot_conductor_codes(p, s)
            codes = sorted(codes)
            mask = np.isin(p["reg"], codes)
            meta = {
                "mask": mask,
                "reg": p["reg"][mask],
                "codes": codes,
                "area": p["area_mm2"][mask],
                "x": p["x_mm"][mask], "y": p["y_mm"][mask],
            }
            BX = np.empty((len(blocks), int(mask.sum())))
            BY = np.empty_like(BX)
        BX[bi] = p["bx"][meta["mask"]]
        BY[bi] = p["by"][meta["mask"]]
    return meta, BX, BY


def losses_of_op(path, w_c, h_c, f_e):
    meta, BX, BY = load_series(path)
    n = BX.shape[0]
    f_m = np.arange(1, n // 2 + 1) * f_e
    p24 = p24c = g2 = volpe = 0.0
    for c in meta["codes"]:
        m = meta["reg"] == c
        wgt = meta["area"][m]
        x = float(np.average(meta["x"][m], weights=wgt))
        y = float(np.average(meta["y"][m], weights=wgt))
        th = np.arctan2(y, x)
        b_rad = (np.cos(th) * BX[:, m] + np.sin(th) * BY[:, m]).T
        b_tan = (-np.sin(th) * BX[:, m] + np.cos(th) * BY[:, m]).T
        amp_r = 2.0 * np.abs(np.fft.rfft(b_rad, axis=1))[:, 1:] / n
        amp_t = 2.0 * np.abs(np.fft.rfft(b_tan, axis=1))[:, 1:] / n
        wn = wgt / wgt.sum()
        b2_rad = wn @ amp_r**2
        b2_tan = wn @ amp_t**2
        p24 += prox_24(f_m, b2_tan, b2_rad, w_c, h_c)
        p24c += prox_24(f_m, b2_tan, b2_rad, w_c, h_c, n_cuboids=6)
        g2 += prox_g2(f_m, b2_tan, b2_rad, w_c, h_c)
        volpe += prox_g2_volpe_prime(f_m, b2_tan, b2_rad, w_c, h_c)
    return (p24 * SECTORS, p24c * SECTORS, g2 * SECTORS, volpe * SECTORS,
            int(BX.shape[1]), n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(DIMS))
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    w_c, h_c = DIMS[a.model]

    dirs = sorted(glob.glob(os.path.join(BACKFILL, a.model,
                                         "Hybrid_Speed_*")))
    if a.nshards > 1:
        dirs = dirs[a.shard::a.nshards]
    if a.limit:
        dirs = dirs[:a.limit]
    suffix = f"_s{a.shard}" if a.nshards > 1 else ""
    out_path = os.path.join(E10, a.model,
                            f"meshb_hybrid_losses_{a.model}{suffix}.json")
    print(f"[{a.model}] {len(dirs)} OP, 도체 {w_c*1e3:.3f}x{h_c*1e3:.3f} mm",
          flush=True)

    refs = {}   # current -> mcad_reference dict
    rows, t0 = [], time.time()
    for i, d in enumerate(dirs):
        m = _DIR_RE.search(os.path.basename(d))
        if not m:
            continue
        spd, cur, ph = int(m.group(1)), float(m.group(2)), float(m.group(3))
        f = os.path.join(d, "FEA_data.txt.gz")
        if not os.path.exists(f):
            print(f"  누락: {os.path.basename(d)}", flush=True)
            continue
        f_e = spd * POLE_PAIRS / 60.0
        try:
            p24, p24c, g2, volpe, n_el, n_st = losses_of_op(f, w_c, h_c, f_e)
        except Exception as ex:
            print(f"  [{i+1}/{len(dirs)}] {os.path.basename(d)}: 실패 {ex}",
                  flush=True)
            continue
        sk = calc_skin_loss(w_c, h_c, f_e, L_ACTIVE,
                            cur / N_PARALLEL)
        skin_mach = sk["P_excess_W"] * N_COND_MACHINE
        if cur not in refs:
            from pathlib import Path
            refs[cur] = mcad_reference(Path(MCAD_JSON[a.model]), cur)
        e = refs[cur].get((spd, ph), {})
        rows.append({
            "speed_rpm": spd, "current_A": cur, "phase_deg": ph,
            "P24_solid_W": p24, "P24_cuboid6_W": p24c,
            "G2_solid_W": g2, "Volpe_G2p_W": volpe,
            "skin_excess_W": skin_mach,
            "meshb_total_volpe_W": volpe + skin_mach,
            "mcad_prox_W": e.get("prox_W"),
            "mcad_skin_W": e.get("skin_W"),
            "mcad_total_W": e.get("total_W"),
            "ts_ac_W": e.get("ts_W"),
            "n_elems": n_el, "n_steps": n_st,
        })
        el = time.time() - t0
        eta = el / (len(rows)) * (len(dirs) - i - 1) / 60
        print(f"  [{i+1}/{len(dirs)}] {spd:>5d}/{cur:g}/{ph:g}: "
              f"Vlp {volpe/1e3:7.2f} kW  MCADpx "
              f"{(e.get('prox_W') or 0)/1e3:7.2f}  TS "
              f"{(e.get('ts_W') or float('nan'))/1e3:7.2f}"
              f"  ({time.time()-t0-el+el:.0f}s, ETA {eta:.0f}min)",
              flush=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump({"rows": rows,
               "_meta": {"model": a.model, "conductor_m": [w_c, h_c],
                         "L_active_m": L_ACTIVE, "sectors": SECTORS,
                         "b_source": "backfilled Hybrid MS FEA_data.txt.gz",
                         "methods": ["P24_solid", "P24_cuboid6", "G2_solid",
                                     "Volpe_G2p(MCAD internal)"],
                         "skin": "Dowell M(xi), fundamental, I/2 per cond",
                         "note": "prox = slot1~6 x 8 sectors; FFT one-sided "
                                 "peak; per-element series, area-weighted "
                                 "<B_m^2> per conductor"}},
              open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"저장: {out_path}  ({len(rows)}행)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
