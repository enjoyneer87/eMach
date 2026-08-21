# -*- coding: utf-8 -*-
"""HalfSC 캠페인 격자 mesh-B 손실 120행 완성 (360 = 120x3 목표의 마지막 조각).

필드 소스 우선순위 (자체 기하 실해석 우선, 상사 가정 불사용):
  1) 재생성 캠페인 트리 (172.5/517.5/690 링, 16k MS)
  2) 스윕 트리 (345.0/0.1 링; 16k 우선, 없으면 다른 속도 — MS 는 속도 무관)

핵심: FFT 스펙트럼은 회전각 기준이므로 (I,b)당 파일 1회 파싱으로
4개 속도의 손실을 모두 평가한다 (f_m = n * f_e 만 속도별로 변경).

산출: map_exports/e10/HalfSC/meshb_hybrid_losses_HalfSC_campaign.json
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
sys.path.insert(0, HERE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from run_meshb_hybrid_all import (                          # noqa: E402
    load_series, DIMS, MCAD_JSON, N_COND_MACHINE, N_PARALLEL)
from acloss_ref_methods.mesh_b_vs_mcad import (             # noqa: E402
    prox_24, prox_g2, prox_g2_volpe_prime, mcad_reference,
    L_ACTIVE, POLE_PAIRS, SECTORS)
from acloss_ref_methods.volpe_hybrid_acloss import (        # noqa: E402
    calc_skin_loss)

from jeet_acloss_rbf.repro_env import data_root             # noqa: E402

_FEA = os.environ.get("JEET_FEA_ROOT", "")
CAMPAIGN = os.path.join(_FEA, "_txt_backfill", "HalfSC_campaign")
SWEEP = os.path.join(_FEA, "SLFEA_Half", "ACLossCalcExport_Map")
OUT = os.path.join(data_root(), "HalfSC",
                   "meshb_hybrid_losses_HalfSC_campaign.json")
W_C, H_C = DIMS["HalfSC"]
SPEEDS = [2000, 4000, 8000, 16000]
CURRENTS = ["0.1", "172.5", "345.0", "517.5", "690.0"]
PHASES = ["0.0", "18.0", "36.0", "54.0", "72.0", "90.0"]


def field_file(cur, ph):
    p = os.path.join(CAMPAIGN, f"Hybrid_Speed_16000RPM_{cur}A_{ph}deg",
                     "FEA_data.txt.gz")
    if os.path.exists(p):
        return p, "campaign16k"
    for spd in (16000, 8000, 4000, 2000):
        q = glob.glob(os.path.join(
            SWEEP, f"Hybrid_Speed_{spd}RPM_{cur}A_{ph}deg", "FEA_data.txt*"))
        if q:
            return q[0], f"sweep{spd//1000}k"
    return None, None


def spectra_of(path):
    """(I,b) 파일 1회 파싱 -> 도체별 b2_r/b2_t 조화 배열 (속도 무관)."""
    meta, BX, BY = load_series(path)
    n = BX.shape[0]
    out = []
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
        out.append((wn @ amp_t**2, wn @ amp_r**2))
    return out, n, int(BX.shape[1])


def main() -> int:
    refs = {}
    rows, t0 = [], time.time()
    combos = [(c, p) for c in CURRENTS for p in PHASES]
    for i, (cur, ph) in enumerate(combos):
        f, tag = field_file(cur, ph)
        if f is None:
            print(f"  [{i+1}/{len(combos)}] {cur}A/{ph}: 필드 없음", flush=True)
            continue
        spec, n_steps, n_el = spectra_of(f)
        if float(cur) not in refs:
            refs[float(cur)] = mcad_reference(Path(MCAD_JSON["HalfSC"]),
                                              float(cur))
        for spd in SPEEDS:
            f_e = spd * POLE_PAIRS / 60.0
            f_m = np.arange(1, n_steps // 2 + 1) * f_e
            p24 = p24c = g2 = volpe = 0.0
            for b2_t, b2_r in spec:
                p24 += prox_24(f_m, b2_t, b2_r, W_C, H_C)
                p24c += prox_24(f_m, b2_t, b2_r, W_C, H_C, n_cuboids=6)
                g2 += prox_g2(f_m, b2_t, b2_r, W_C, H_C)
                volpe += prox_g2_volpe_prime(f_m, b2_t, b2_r, W_C, H_C)
            sk = calc_skin_loss(W_C, H_C, f_e, L_ACTIVE,
                                float(cur) / N_PARALLEL)
            skin_mach = sk["P_excess_W"] * N_COND_MACHINE
            e = refs[float(cur)].get((spd, float(ph)), {})
            rows.append({
                "speed_rpm": spd, "current_A": float(cur),
                "phase_deg": float(ph), "b_source": tag,
                "P24_solid_W": p24 * SECTORS,
                "P24_cuboid6_W": p24c * SECTORS,
                "G2_solid_W": g2 * SECTORS,
                "Volpe_G2p_W": volpe * SECTORS,
                "skin_excess_W": skin_mach,
                "meshb_total_volpe_W": volpe * SECTORS + skin_mach,
                "mcad_prox_W": e.get("prox_W"),
                "mcad_skin_W": e.get("skin_W"),
                "ts_ac_W": e.get("ts_W"),
                "n_elems": n_el, "n_steps": n_steps,
            })
        el = time.time() - t0
        print(f"  [{i+1}/{len(combos)}] {cur}A/{ph} [{tag}]: 4속도 평가"
              f"  (경과 {el/60:.0f}min)", flush=True)
    rows.sort(key=lambda r: (r["speed_rpm"], r["current_A"],
                             r["phase_deg"]))
    json.dump({"rows": rows,
               "_meta": {"model": "HalfSC", "grid": "campaign",
                         "conductor_m": [W_C, H_C],
                         "b_source_policy": "own-geometry solves only "
                         "(campaign regen 16k > sweep); MS fields are "
                         "speed-invariant, spectra evaluated at 4 speeds",
                         "sectors": SECTORS}},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    # 요약
    sel = [r for r in rows if r["current_A"] > 1 and r.get("ts_ac_W")
           and r.get("mcad_prox_W") is not None]
    if sel:
        ts = np.array([r["ts_ac_W"] for r in sel])
        mc = np.array([r["mcad_prox_W"] + r["mcad_skin_W"] for r in sel])
        vt = np.array([r["meshb_total_volpe_W"] for r in sel])
        print(f"AF(TS/MCAD): {np.mean(ts/mc):.3f}"
              f" [{np.min(ts/mc):.2f}~{np.max(ts/mc):.2f}]"
              f"  AF(TS/meshB): {np.mean(ts/vt):.3f}"
              f" [{np.min(ts/vt):.2f}~{np.max(ts/vt):.2f}]"
              f"  (유효 {len(sel)}/{len(rows)}행)", flush=True)
    print(f"저장: {OUT}  ({len(rows)}행, {(time.time()-t0)/60:.0f}min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
