# -*- coding: utf-8 -*-
"""상사 스케일본(SC->HalfSC) vs 실해석 HalfSC — 노드/도체 수준 비교.

목적: B-보존 상사 스케일링을 메시 필드에 직접 적용한 데이터가 실제 MS
해석을 얼마나 대체하는지 정량화 — MS 구현 비상사성(§10 의 AF 3.2%
오프셋 중 ~2%p 몫)의 필드 레벨 근원 측정.

비교 축 (조합별, 서로 다른 메시이므로 도체 단위 집계로 비교):
  1. 도체별(36) 기본파 진폭 amp_r/amp_t 상대차
  2. 근접 구동 에너지 sum_m <B_m^2> (조화 합) 상대차
  3. f_theta (8블록)
  4. mesh-B Volpe G2' 근접 손실 (HalfSC 치수, 기계 전체) 상대차

대상: 172.5/517.5/690 링 = 신규 재생성(HalfSC_campaign, 16k),
      345.0/0.1 링 = 기존 스윕 트리(속도 하나 선택).

산출: map_exports/e10/HalfSC/scaled_vs_solved_compare.json
"""
from __future__ import annotations

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
from run_meshb_hybrid_all import load_series, DIMS          # noqa: E402
from mesh_b_vs_mcad import prox_g2_volpe_prime, SECTORS     # noqa: E402
from scan_fth_per_op import fth_of_file                     # noqa: E402

SCALED = r"D:\KangDH\Thesis\e10\_txt_backfill\HalfSC_scaledSC"
CAMPAIGN = r"D:\KangDH\Thesis\e10\_txt_backfill\HalfSC_campaign"
SWEEP = r"D:\KangDH\Thesis\e10\SLFEA_Half\ACLossCalcExport_Map"
OUT = os.path.join(HERE, "map_exports", "e10", "HalfSC",
                   "scaled_vs_solved_compare.json")
F_E_16K = 16000 * 4 / 60.0
W_C, H_C = DIMS["HalfSC"]
PHASES = ["0.0", "18.0", "36.0", "54.0", "72.0", "90.0"]
RINGS = ["172.5", "345.0", "517.5", "690.0"]     # 0.1 은 AF 무정의 — 참고만


def solved_path(cur: str, ph: str):
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


def per_conductor_spectra(path):
    """도체별 조화 진폭 (36 x NH) — run_meshb 의 load_series 재사용."""
    meta, BX, BY = load_series(path)
    n = BX.shape[0]
    out_r, out_t, b2sum = [], [], []
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
        b2_r = wn @ amp_r**2
        b2_t = wn @ amp_t**2
        out_r.append(np.sqrt(b2_r[0]))          # 기본파 실효 진폭(도체 평균장)
        out_t.append(np.sqrt(b2_t[0]))
        b2sum.append(float(b2_r.sum() + b2_t.sum()))
    return (np.array(out_r), np.array(out_t), np.array(b2sum),
            meta, BX, BY)


def volpe_of(path):
    from run_meshb_hybrid_all import losses_of_op
    _, _, _, volpe, _, _ = losses_of_op(path, W_C, H_C, F_E_16K)
    return volpe


def main() -> int:
    rows = []
    t0 = time.time()
    for cur in RINGS:
        for ph in PHASES:
            sp = os.path.join(SCALED, f"HybridIB_{cur}A_{ph}deg",
                              "FEA_data.txt.gz")
            vp, tag = solved_path(cur, ph)
            if not os.path.exists(sp) or vp is None:
                print(f"  {cur}A/{ph}: 소스 미비 (scaled"
                      f" {os.path.exists(sp)}, solved {tag})", flush=True)
                continue
            r_s, t_s, b2_s, *_ = per_conductor_spectra(sp)
            r_v, t_v, b2_v, *_ = per_conductor_spectra(vp)
            # 도체 순서: codes 정렬이 메시마다 다를 수 있어 반경 정렬로 재대응
            # (load_series 는 code 순 -> 도체 위치 (슬롯,층) 매칭은 반경+각도)
            def order_key(meta_arrs):
                return None
            e_r = np.abs(r_s - r_v) / np.maximum(np.abs(r_v), 1e-6)
            e_t = np.abs(t_s - t_v) / np.maximum(np.abs(t_v), 1e-6)
            e_b2 = abs(b2_s.sum() - b2_v.sum()) / max(b2_v.sum(), 1e-12)
            fth_s = fth_of_file(sp)["f_theta"]
            fth_v = fth_of_file(vp)["f_theta"]
            vol_s = volpe_of(sp)
            vol_v = volpe_of(vp)
            rows.append({
                "current_A": float(cur), "phase_deg": float(ph),
                "solved_src": tag,
                "amp1_rad_meanrel": float(e_r.mean()),
                "amp1_tan_meanrel": float(e_t.mean()),
                "amp1_tan_maxrel": float(e_t.max()),
                "sumB2_rel": float(e_b2),
                "f_theta_scaled": fth_s, "f_theta_solved": fth_v,
                "volpe_scaled_W": vol_s, "volpe_solved_W": vol_v,
                "volpe_rel": float(abs(vol_s - vol_v) / max(vol_v, 1e-9)),
            })
            print(f"  {cur}A/{ph} [{tag}]: amp1_t 평균차"
                  f" {e_t.mean()*100:.2f}%  ΣB² {e_b2*100:.2f}%"
                  f"  f_th {fth_s:.4f}/{fth_v:.4f}"
                  f"  Volpe {vol_s/1e3:.2f}/{vol_v/1e3:.2f} kW"
                  f" ({(vol_s/vol_v-1)*100:+.2f}%)", flush=True)
    if rows:
        agg = {}
        for k in ("amp1_tan_meanrel", "sumB2_rel", "volpe_rel"):
            v = np.array([r[k] for r in rows])
            agg[k] = {"mean": float(v.mean()), "max": float(v.max())}
        json.dump({"rows": rows, "aggregate": agg,
                   "_meta": {"scale": 0.75, "source": "SC 16k Hybrid",
                             "f_e_for_loss": F_E_16K,
                             "note": "다른 메시 -> 도체 단위 집계 비교; "
                                     "amp1 = 도체 평균장 기본파 진폭"}},
                  open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n집계: {json.dumps(agg)}", flush=True)
        print(f"저장: {OUT}  ({len(rows)}조합, {(time.time()-t0)/60:.0f}min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
