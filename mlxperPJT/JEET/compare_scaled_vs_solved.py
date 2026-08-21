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
from acloss_ref_methods.mesh_b_vs_mcad import (             # noqa: E402
    prox_g2_volpe_prime, SECTORS)
from scan_fth_per_op import fth_of_file                     # noqa: E402

from jeet_acloss_rbf.repro_env import data_root             # noqa: E402

_FEA = os.environ.get("JEET_FEA_ROOT", "")
SCALED = os.path.join(_FEA, "_txt_backfill", "HalfSC_scaledSC")
CAMPAIGN = os.path.join(_FEA, "_txt_backfill", "HalfSC_campaign")
SWEEP = os.path.join(_FEA, "SLFEA_Half", "ACLossCalcExport_Map")
OUT = os.path.join(data_root(), "HalfSC",
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


def analyze_file(path):
    """파일 1회 파싱으로 전 지표 산출 (재파싱 6회 -> 1회 최적화).

    반환 dict: amp1_r/amp1_t (도체별 기본파), b2sum (도체별 조화합),
    volpe_W (기계 근접손실), f_theta, brms (요소별 주기 RMS |B|), meta.
    """
    from acloss_ref_methods.mesh_b_vs_mcad import POLE_PAIRS as _PP
    meta, BX, BY = load_series(path)
    n = BX.shape[0]
    f_m = np.arange(1, n // 2 + 1) * F_E_16K
    out_r, out_t, b2sum = [], [], []
    volpe = 0.0
    S_t = S_r = 0.0
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
        volpe += prox_g2_volpe_prime(f_m, b2_t, b2_r, W_C, H_C)
        # f_theta: 도체 평균장 시계열 에너지 분율 (scan_fth 관습)
        br_c = wn @ b_rad
        bt_c = wn @ b_tan
        S_r += float(np.sum(br_c**2))
        S_t += float(np.sum(bt_c**2))
    brms = np.sqrt(np.mean(BX**2 + BY**2, axis=0))
    return {"amp1_r": np.array(out_r), "amp1_t": np.array(out_t),
            "b2sum": np.array(b2sum), "volpe_W": volpe * SECTORS,
            "f_theta": S_t / (S_t + S_r), "brms": brms, "meta": meta}


def field_level_delta(a_s, a_v):
    """요소 수준 비교 — 실해석 필드를 스케일 메시 요소중심에 최근접 보간.

    스케일 메시는 상사 변환된 유효 HalfSC 이산화이므로(형상 동일), 남는
    차이는 (i) MS 구현 비상사성 + (ii) 최근접-요소 보간 오차 O(h) 뿐이다.
    주기 RMS |B| 로 비교한다 (B 는 요소 상수량). 입력은 analyze_file 산출.
    """
    from scipy.spatial import cKDTree
    ms, mv = a_s["meta"], a_v["meta"]
    tree = cKDTree(np.column_stack([mv["x"], mv["y"]]))
    d, j = tree.query(np.column_stack([ms["x"], ms["y"]]), k=1)
    dv = a_s["brms"] - a_v["brms"][j]
    rel = np.abs(dv) / np.maximum(a_v["brms"][j], 1e-4)
    return {
        "n_elem": int(len(dv)),
        "match_dist_mm_p95": float(np.percentile(d, 95)),
        "dBrms_T_rms": float(np.sqrt(np.mean(dv**2))),
        "dBrms_rel_mean": float(rel.mean()),
        "dBrms_rel_p95": float(np.percentile(rel, 95)),
    }


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
            a_s = analyze_file(sp)
            a_v = analyze_file(vp)
            r_s, t_s, b2_s = a_s["amp1_r"], a_s["amp1_t"], a_s["b2sum"]
            r_v, t_v, b2_v = a_v["amp1_r"], a_v["amp1_t"], a_v["b2sum"]
            e_r = np.abs(r_s - r_v) / np.maximum(np.abs(r_v), 1e-6)
            e_t = np.abs(t_s - t_v) / np.maximum(np.abs(t_v), 1e-6)
            e_b2 = abs(b2_s.sum() - b2_v.sum()) / max(b2_v.sum(), 1e-12)
            fth_s, fth_v = a_s["f_theta"], a_v["f_theta"]
            vol_s, vol_v = a_s["volpe_W"], a_v["volpe_W"]
            fld = field_level_delta(a_s, a_v)
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
                "field_level": fld,
            })
            print(f"  {cur}A/{ph} [{tag}]: amp1_t 평균차"
                  f" {e_t.mean()*100:.2f}%  ΣB² {e_b2*100:.2f}%"
                  f"  f_th {fth_s:.4f}/{fth_v:.4f}"
                  f"  Volpe {vol_s/1e3:.2f}/{vol_v/1e3:.2f} kW"
                  f" ({(vol_s/vol_v-1)*100:+.2f}%)"
                  f"  ΔBrms rel {fld['dBrms_rel_mean']*100:.2f}%"
                  f"/p95 {fld['dBrms_rel_p95']*100:.2f}%", flush=True)
    if rows:
        agg = {}
        for k in ("amp1_tan_meanrel", "sumB2_rel", "volpe_rel"):
            v = np.array([r[k] for r in rows])
            agg[k] = {"mean": float(v.mean()), "max": float(v.max())}
        v = np.array([r["field_level"]["dBrms_rel_mean"] for r in rows])
        agg["field_dBrms_rel"] = {"mean": float(v.mean()),
                                  "max": float(v.max())}
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
