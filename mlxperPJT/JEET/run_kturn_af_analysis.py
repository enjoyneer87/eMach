# -*- coding: utf-8 -*-
"""Kturn(턴수 4/8) AC 손실 맵 1차 분석 — AF 데이터셋 + 턴-상사 제로샷.

데이터 (2026-07-20~22 헤드리스 sweep, G:):
    G:/KangDH/JEET/kturn_results/kturn{4,8}/JEET_ACLoss_kturn{N}_Map_Summary.json
    각 240 레코드 = 2 모델(1 Hybrid / 3 FullFEA) x 4 속도 x 5 전류 x 6 위상.
    전류 격자가 턴-상사 설계: 4t max 690 A(=460x6/4), 8t max 345 A(=460x6/8).

턴-상사 가설 (기하 동일, 도체 분할만 변경 — B-보존이 자명한 축):
    eta 정합(속도):  w_6 = k_h^2 w_Nt,  k_h = H_Nt / H_6  (도체 반경방향 두께비)
    MMF 정합(전류):  I_6 = I_Nt * (N_t / 6)               (턴수비 — k_h 와 분리)
    → AF_Nt(w, I, b) ≈ AF_6(k_h^2 w, I*N_t/6, b)
  k_h 두 변형을 병행 평가:
    ideal  = 6/N_t (1.5 / 0.75)         — 점적율 완전 보존 가정
    actual = .mot 실측 (1.4740 / 0.6955) — 8t 는 절연 오버헤드 클램프로 -7%
  실측 도체 치수 (radial H x tangential W, mm):
    6t 1.686x3.711 (A_c 6.257, slot 37.54) / 4t 2.48505x3.73 (9.269, 37.08)
    / 8t 1.17268x3.73 (4.374, 34.99 = 6t 대비 93.2% — 클램프 실측)

점검 항목: (i) 속도별 AF 범위/평균, (ii) 8t AF<1 운전점(특히 16k) 목록,
(iii) 제로샷 wMAE(손실 가중) — donor 대역(2~16k) 사상 가능 여부 주석.

실행:  python run_kturn_af_analysis.py
산출:  map_exports/e10/kturn/kturn_af_analysis.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import numpy as np                                    # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline   # noqa: E402

KTURN_ROOT = r"G:\KangDH\JEET\kturn_results"
OUT = os.path.join(HERE, "map_exports", "e10", "kturn",
                   "kturn_af_analysis.json")

H6 = 1.686
DIMS = {  # turn -> (H_radial, W_tangential)
    4: (2.48505, 3.73),
    8: (1.17268, 3.73),
}
DONOR_BAND_K = (2.0, 16.0)   # Ref 보정 대역 [kRPM]


def load_pairs(turn: int):
    """(speed, I, beta) 로 Hybrid/FullFEA 레코드를 짝지어 배열로 반환."""
    p = os.path.join(KTURN_ROOT, f"kturn{turn}",
                     f"JEET_ACLoss_kturn{turn}_Map_Summary.json")
    d = json.load(open(p, encoding="utf-8"))
    recs = d["records"]
    hyb = {(r["speed"], round(r["current"], 2), round(r["phase"], 1)): r
           for r in recs if r["proximity_model"] == 1}
    fea = {(r["speed"], round(r["current"], 2), round(r["phase"], 1)): r
           for r in recs if r["proximity_model"] == 3}
    keys = sorted(set(hyb) & set(fea))
    rows = []
    for k in keys:
        h, f = hyb[k], fea[k]
        rows.append({
            "speed_k": k[0] / 1000.0, "irms": k[1], "beta": k[2],
            "hyb_kW": float(h.get("hybrid_total_kW") or 0.0),
            "fea_kW": float(f.get("ts_ac_active_only_kW") or 0.0),
            "dc_kW": float(f.get("ts_dc_active_kW") or 0.0),
        })
    return rows, len(recs), len(keys)


def main() -> int:
    pl = AcLossPipeline()
    m_ref = pl.build_model("Ref")

    res = {"_meta": {
        "H6_mm": H6,
        "dims_mm": {str(t): {"H": DIMS[t][0], "W": DIMS[t][1]} for t in DIMS},
        "k_h": {str(t): {"ideal": 6.0 / t, "actual": DIMS[t][0] / H6}
                for t in DIMS},
        "mapping": "AF_Nt(w,I,b)=AF_6(k_h^2 w, I*Nt/6, b); "
                   "speed=eta match(k_h), current=MMF match(turn ratio)",
        "donor_band_kRPM": list(DONOR_BAND_K),
    }}

    for turn in (4, 8):
        rows, n_rec, n_pair = load_pairs(turn)
        v = [r for r in rows
             if r["irms"] > 1.0 and r["hyb_kW"] > 0 and r["fea_kW"] > 0]
        spd = np.array([r["speed_k"] for r in v])
        irms = np.array([r["irms"] for r in v])
        beta = np.array([r["beta"] for r in v])
        hyb = np.array([r["hyb_kW"] for r in v])
        fea = np.array([r["fea_kW"] for r in v])
        dc = np.array([r["dc_kW"] for r in v])
        af = fea / hyb

        entry = {"n_records": n_rec, "n_paired": n_pair, "n_valid": len(v)}

        # (i) 속도별 AF/ACDC 통계 + 무보정 하이브리드 오차
        stats = {}
        for s in sorted(set(spd)):
            m = spd == s
            e = np.abs(hyb[m] - fea[m]) / fea[m] * 100.0
            stats[f"{s:g}k"] = {
                "n": int(m.sum()),
                "AF_min": round(float(af[m].min()), 3),
                "AF_mean": round(float(af[m].mean()), 3),
                "AF_max": round(float(af[m].max()), 3),
                "ACDC_max": round(float((fea[m] / dc[m]).max()), 2),
                "uncorr_wmae_pct": round(
                    float(np.sum(fea[m] * e) / np.sum(fea[m])), 2),
            }
        entry["by_speed"] = stats

        # (ii) AF < 1 운전점
        m_lt1 = af < 1.0
        entry["af_lt1"] = [
            {"speed_k": float(spd[i]), "irms": float(irms[i]),
             "beta": float(beta[i]), "AF": round(float(af[i]), 3)}
            for i in np.where(m_lt1)[0]]

        # (iii) 턴-상사 제로샷 (donor = Ref 채택 모델)
        zs = {}
        for tag, k_h in (("ideal", 6.0 / turn), ("actual", DIMS[turn][0] / H6)):
            w6 = spd * k_h ** 2                 # kRPM
            i6 = irms * (turn / 6.0)
            af_pred = m_ref.predict(w6 * 1000.0, i6, beta)
            pred = hyb * af_pred
            e = np.abs(pred - fea) / fea * 100.0
            inb = (w6 >= DONOR_BAND_K[0]) & (w6 <= DONOR_BAND_K[1])
            per_spd = {}
            for s in sorted(set(spd)):
                m = spd == s
                per_spd[f"{s:g}k"] = {
                    "wmae_pct": round(
                        float(np.sum(fea[m] * e[m]) / np.sum(fea[m])), 2),
                    "mapped_to_kRPM": round(float(s * k_h ** 2), 2),
                    "in_band": bool(inb[m].all()),
                }
            zs[tag] = {
                "k_h": round(k_h, 4),
                "wmae_all_pct": round(float(np.sum(fea * e) / np.sum(fea)), 2),
                "wmae_inband_pct": (round(float(
                    np.sum(fea[inb] * e[inb]) / np.sum(fea[inb])), 2)
                    if inb.any() else None),
                "n_inband": int(inb.sum()),
                "by_speed": per_spd,
            }
        entry["zeroshot_via_Ref"] = zs

        # (iv) actual-k 제로샷 + 16k 자체 3점 재앵커 (κ-스팬: 예측 AF 의
        #     min/med/max) — 잔차가 레벨 오프셋인지 형상 불일치인지 판별
        k_h = DIMS[turn][0] / H6
        af_zs = m_ref.predict(spd * k_h ** 2 * 1000.0,
                              irms * (turn / 6.0), beta)
        hi = spd > 12.0
        idx16 = np.where(hi)[0]
        order = np.argsort(af_zs[idx16])
        pick = idx16[[order[0], order[len(order) // 2], order[-1]]]
        x = np.log(np.clip(af_zs[pick], 1e-3, None))
        y = np.log(np.clip(af[pick], 1e-3, None))
        p_c, logf_c = np.polyfit(x, y, 1)
        f_c = float(np.exp(logf_c))
        af_re = f_c * np.clip(af_zs, 1e-3, None) ** p_c   # 전 속도 일괄 보정
        e_re = np.abs(hyb * af_re - fea) / fea * 100.0
        per_spd_re = {
            f"{s:g}k": round(float(np.sum(fea[spd == s] * e_re[spd == s])
                                   / np.sum(fea[spd == s])), 2)
            for s in sorted(set(spd))}
        entry["reanchor_plus3_16k"] = {
            "f_c": round(f_c, 4), "p_c": round(float(p_c), 4),
            "anchor_ops": [[float(irms[i]), float(beta[i])] for i in pick],
            "wmae_all_pct": round(
                float(np.sum(fea * e_re) / np.sum(fea)), 2),
            "by_speed_wmae": per_spd_re,
        }
        print(f"  +3 재앵커(16k κ-스팬): f_c={f_c:.3f}, p_c={p_c:.3f} → "
              f"전체 wMAE {entry['reanchor_plus3_16k']['wmae_all_pct']}%  "
              f"속도별 {per_spd_re}")
        res[f"kturn{turn}"] = entry

        print(f"\n== kturn{turn}: pairs {n_pair}, valid {len(v)}, "
              f"AF<1: {int(m_lt1.sum())}점")
        print(f"  {'spd':>4} {'n':>3} {'AF range':>16} {'ACDC_max':>9} "
              f"{'uncorr%':>8} | zs-ideal% | zs-actual% (→kRPM)")
        for s in sorted(set(spd)):
            st = stats[f"{s:g}k"]
            zi = zs["ideal"]["by_speed"][f"{s:g}k"]
            za = zs["actual"]["by_speed"][f"{s:g}k"]
            print(f"  {s:>3g}k {st['n']:>3} "
                  f"{st['AF_min']:>6.2f}~{st['AF_max']:<6.2f} "
                  f"{st['ACDC_max']:>9.2f} {st['uncorr_wmae_pct']:>8.2f} | "
                  f"{zi['wmae_pct']:>8.2f}  | {za['wmae_pct']:>8.2f} "
                  f"(→{za['mapped_to_kRPM']:g}{'' if za['in_band'] else ' 외삽'})")
        print(f"  전체 zs wMAE: ideal {zs['ideal']['wmae_all_pct']}% / "
              f"actual {zs['actual']['wmae_all_pct']}%  "
              f"(in-band: {zs['ideal']['wmae_inband_pct']} / "
              f"{zs['actual']['wmae_inband_pct']})")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
