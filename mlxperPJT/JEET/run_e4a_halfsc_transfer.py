# -*- coding: utf-8 -*-
"""e4a-HalfSC 이중 도너 상사 전달 검증 — 3기계 패밀리 완결편.

target: e4a-HalfSC (k_r=1.5, kturn15). 도너 2종:
  Ref (kturn4):  AF_Half(w,I,b) = AF_Ref(2.25w, I/1.5, b)
                 인밴드 {1650,3300,6600} → Ref {3712.5,7425,14850}
                 외삽   {7425,14850} → Ref {16706,33413}
  SC  (kturn20): AF_Half(w,I,b) = AF_SC(0.5625w, 4I/3, b)
                 전 대역 인밴드: {928,1856,3712,4177,8353} ⊂ [928,14850]
예측자: A 무보정 / C_ref / C_sc / E 혼합(저대역 Ref + 고대역 SC)
        / F C_ref+외삽 재앵커 / B 자체 레시피 24점
불변량: P_Half(w,1.5I,b)=P_Ref(2.25w,I,b) 72쌍
        P_Half(w,I,b)=P_SC(0.5625w,4I/3,b) 72쌍 (저대역 3속도)

산출: map_exports/e10/e4a_halfsc_transfer.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from scipy.interpolate import RBFInterpolator               # noqa: E402

from run_e4a_family_transfer import (load_pairs, maximin_order,   # noqa: E402
                                     err_stats, DonorModel)

REF_SRC = r"D:\KangDH\Thesis\e4a\newfam_results\kturn4\JEET_ACLoss_kturn4_Map_Summary.json"
SC_SRC = r"D:\KangDH\Thesis\e4a\newfam_results\kturn20\JEET_ACLoss_kturn20_Map_Summary.json"
H_SRC = (sys.argv[1] if len(sys.argv) > 1 else
         r"D:\KangDH\Thesis\e4a\newfam_results\kturn15\JEET_ACLoss_kturn15_Map_Summary.json")
OUT = (sys.argv[2] if len(sys.argv) > 2 else
       os.path.join(HERE, "map_exports", "e10", "e4a_halfsc_transfer.json"))
K_H, K_S = 1.5, 2.0
H_INBAND_REF = (1650, 3300, 6600)      # Ref 도너 인밴드
H_BASE = 14850


def pair_check(st, sc_, sp, sf, donor_ts, w_mult, i_mult, speeds):
    rows, devs = [], []
    for i in range(len(st)):
        if int(st[i]) not in speeds:
            continue
        tgt = (st[i] * w_mult, sc_[i] * i_mult, round(sp[i], 1))
        cand = [k for k in donor_ts
                if abs(k[0] - tgt[0]) <= 2.5 and abs(k[1] - tgt[1]) < 0.7
                and abs(k[2] - tgt[2]) < 0.5]
        if not cand:
            continue
        pv = donor_ts[cand[0]]
        dev = (sf[i] / pv - 1.0) * 100.0
        devs.append(dev)
        rows.append({"half_op": [int(st[i]), float(sc_[i]), float(sp[i])],
                     "donor_op": [float(x) for x in cand[0]],
                     "dev_pct": round(float(dev), 2)})
    devs = np.array(devs)
    if not len(devs):
        return None
    return {"n_pairs": int(len(devs)),
            "mean_abs_dev_pct": round(float(np.abs(devs).mean()), 2),
            "p95_abs_dev_pct": round(float(np.percentile(np.abs(devs), 95)), 2),
            "max_abs_dev_pct": round(float(np.abs(devs).max()), 2),
            "mean_signed_dev_pct": round(float(devs.mean()), 2),
            "rows": rows}


def main() -> int:
    kr, kt, kc, kp, rh, rf = load_pairs(REF_SRC)
    ks2, st2, sc2, sp2, sh2, sf2 = load_pairs(SC_SRC)
    print(f"[donor Ref] TS 쌍 {len(kr)}개 / [donor SC] {len(ks2)}개")
    if not os.path.exists(H_SRC):
        print(f"[대기] HalfSC 요약 없음: {H_SRC}")
        return 1
    kh, ht, hc, hp, hh, hf = load_pairs(H_SRC)
    n_by = {int(s): int((ht == s).sum()) for s in sorted(set(ht))}
    print(f"[target HalfSC] TS 쌍 {len(kh)}개, 속도별 {n_by}")
    if len(kh) == 0:
        print("[대기] HalfSC TS 쌍 0개 — 스윕 진행 중")
        return 1

    af_h = hf / hh
    m_ref = DonorModel(kt, kc, kp, rf / rh, 14850, 250.0, 156.25)
    m_sc = DonorModel(st2, sc2, sp2, sf2 / sh2, 14850, 500.0, -999.0)
    inband_ref = np.isin(ht.astype(int), H_INBAND_REF)

    # A. 무보정
    pred_A = hh.copy()

    # C_ref: AF_Ref(2.25w, I/1.5, b)
    af_Cr = m_ref.predict(ht * K_H**2, hc / K_H, hp)
    pred_Cr = hh * af_Cr

    # C_sc: AF_SC(0.5625w, 4I/3, b) — 전 대역 인밴드
    af_Cs = m_sc.predict(ht * (K_H / K_S) ** 2, hc * (K_S / K_H), hp)
    pred_Cs = hh * af_Cs

    # E. 혼합: 저대역 Ref 사상, 고대역 SC 사상
    af_E = np.where(inband_ref, af_Cr, af_Cs)
    pred_E = hh * af_E

    # F. C_ref + 외삽 속도 재앵커 (+3/속도)
    af_F = af_Cr.copy()
    anchors = {}
    for s in sorted(set(ht.astype(int))):
        if s in H_INBAND_REF:
            continue
        idx = np.where(ht == s)[0]
        if len(idx) < 3:
            continue
        zs = np.clip(af_Cr[idx], 1e-3, None)
        order = np.argsort(zs)
        pick = [order[0], order[len(order) // 2], order[-1]]
        x = np.log(zs[pick])
        y = np.log(np.clip(af_h[idx][pick], 1e-3, None))
        p_c, logf_c = np.polyfit(x, y, 1)
        af_F[idx] = float(np.exp(logf_c)) * zs ** p_c
        anchors[str(s)] = {"f_c": round(float(np.exp(logf_c)), 4),
                           "p_c": round(float(p_c), 4)}
    pred_F = hh * af_F

    # B. 자체 레시피 24점 (base 14850 maximin 12 + 하위 4속도 κ-스팬 3점)
    xy_h = np.column_stack([hc / hc.max(), hp / 90.0])
    base_idx = np.where(ht == H_BASE)[0]
    res_B = None
    if len(base_idx) >= 12:
        order = base_idx[maximin_order(xy_h[base_idx])]
        own = order[:12].tolist()
        kap = RBFInterpolator(xy_h[own], af_h[own],
                              kernel="thin_plate_spline")
        kv = np.clip(kap(xy_h), 1e-6, None)
        fp = {H_BASE: (1.0, 1.0)}
        used_all = set(own)
        for s in sorted(set(ht.astype(int))):
            if s == H_BASE:
                continue
            cand = np.where(ht == s)[0]
            kvv = np.log(kv[cand])
            rk = np.argsort(kvv)
            picks = cand[[rk[0], rk[len(rk) // 2], rk[-1]]]
            used_all |= set(picks.tolist())
            A = np.vstack([np.ones(3), kvv[[rk[0], rk[len(rk) // 2],
                                            rk[-1]]]]).T
            (lf, p_s), *_ = np.linalg.lstsq(
                A, np.log(af_h[picks]), rcond=None)
            fp[s] = (float(np.exp(lf)), float(p_s))
        pred_B = np.array([fp[int(s)][0] * kv[i] ** fp[int(s)][1]
                           for i, s in enumerate(ht)]) * hh
        hold = np.array([i not in used_all for i in range(len(kh))])
        res_B = {"n_used": len(used_all),
                 "overall": err_stats(hf, pred_B),
                 "heldout": err_stats(hf[hold], pred_B[hold])}

    # P. 손실 보존쌍
    ref_ts = {(float(t), float(c), round(float(p), 1)): v
              for t, c, p, v in zip(kt, kc, kp, rf)}
    sc_ts = {(float(t), float(c), round(float(p), 1)): v
             for t, c, p, v in zip(st2, sc2, sp2, sf2)}
    pairs_ref = pair_check(ht, hc, hp, hf, ref_ts, K_H**2, 1.0 / K_H,
                           set(H_INBAND_REF))
    pairs_sc = pair_check(ht, hc, hp, hf, sc_ts, (K_H / K_S) ** 2,
                          K_S / K_H, set(H_INBAND_REF))

    res = {"_meta": {
        "mapping_ref": "AF_Half(w,I,b) = AF_Ref(2.25w, I/1.5, b)",
        "mapping_sc": "AF_Half(w,I,b) = AF_SC(0.5625w, 4I/3, b)",
        "half_speeds": sorted(set(ht.astype(int))),
        "n_half_pairs": len(kh), "n_by_speed": n_by,
        "inband_ref_speeds": list(H_INBAND_REF)}}
    for tag, pred, note in (
        ("A_uncorrected", pred_A, "AF=1"),
        ("C_zeroshot_via_Ref", pred_Cr,
         "인밴드 {1650,3300,6600}, 외삽 {7425,14850}→Ref 16.7k/33.4k"),
        ("C_zeroshot_via_SC", pred_Cs,
         "전 대역 SC 인밴드 (0.5625w ∈ 928~8353)"),
        ("E_zeroshot_mixed", pred_E, "저대역 Ref + 고대역 SC — TS-FEA 0점"),
        ("F_ref_plus_anchor", pred_F, "Ref 도너 + 외삽 속도 +3점 재앵커")):
        res[tag] = {"note": note,
                    "overall": err_stats(hf, pred),
                    "inband_ref": err_stats(hf[inband_ref], pred[inband_ref]),
                    "outband_ref": (err_stats(hf[~inband_ref],
                                              pred[~inband_ref])
                                    if (~inband_ref).any() else None),
                    "by_speed": {str(int(s)): err_stats(
                        hf[ht == s], pred[ht == s])
                        for s in sorted(set(ht))}}
    res["F_anchors"] = anchors
    if res_B:
        res["B_own_recipe_24pt"] = res_B
    if pairs_ref:
        res["P_pairs_vs_Ref"] = {**pairs_ref,
                                 "note": "P_Half(w,1.5I,b)=P_Ref(2.25w,I,b)"}
    if pairs_sc:
        res["P_pairs_vs_SC"] = {**pairs_sc,
                                "note": "P_Half(w,I,b)=P_SC(0.5625w,4I/3,b)"}

    print(f"\n{'예측자':<24}{'전맵':>8}{'Ref인밴드':>10}{'Ref외삽':>9}")
    print("-" * 54)
    for tag in ("A_uncorrected", "C_zeroshot_via_Ref", "C_zeroshot_via_SC",
                "E_zeroshot_mixed", "F_ref_plus_anchor"):
        o = res[tag]
        ob = (o["outband_ref"]["wmae_pct"] if o["outband_ref"]
              else float("nan"))
        print(f"{tag:<24}{o['overall']['wmae_pct']:>8.2f}"
              f"{o['inband_ref']['wmae_pct']:>10.2f}{ob:>9.2f}")
    if res_B:
        print(f"{'B_own_recipe_24pt':<24}"
              f"{res_B['overall']['wmae_pct']:>8.2f}"
              f"  (held-out {res_B['heldout']['wmae_pct']}%)")
    for lbl, p in (("vs Ref", pairs_ref), ("vs SC", pairs_sc)):
        if p:
            print(f"보존쌍 {lbl} {p['n_pairs']}쌍: mean|dev| "
                  f"{p['mean_abs_dev_pct']}%  p95 {p['p95_abs_dev_pct']}%  "
                  f"max {p['max_abs_dev_pct']}%  (signed "
                  f"{p['mean_signed_dev_pct']}%)")

    def _np(o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        return str(o)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=_np)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
