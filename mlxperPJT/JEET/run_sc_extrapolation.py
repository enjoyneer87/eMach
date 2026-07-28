# -*- coding: utf-8 -*-
"""외삽 방향 사다리 — 도너 {Ref(k=1), HalfSC(k=1.5)}로 SC(k=2) 제로샷 예측.

동기 (2026-07-28, 리뷰어 선제 방어 #7): 논문의 정확도-예산 사다리
(run_halfsc_zeroshot.py)는 SC(2.0) → HalfSC(1.5), 즉 도너 범위 **안쪽**의
중간 변형체를 예측한다 — 전달 문제로는 가장 쉬운 배치다. 본 실험은 반대로
k_r 격자의 **가장자리**(SC)를 안쪽 도너들로부터 외삽 예측해 사다리 서사의
방향 편향을 정량화한다.

상사 사상 (k_a=1, 쌍별 일반형 AF_A(w,I,b) = AF_B((kA/kB)^2 w, I*kB/kA, b)):
    via HalfSC: AF_SC(w,I,b) = AF_Half((4/3)^2 w, 0.75 I, b) = AF_Half(1.7778w, 0.75I, b)
    via Ref   : AF_SC(w,I,b) = AF_Ref(4w, 0.5 I, b)

커버리지 구조 (HalfSC 사다리와의 결정적 차이):
    via HalfSC — SC 2~16k → HalfSC 좌표 3.56~28.4k: 9k 초과분(SC 16k)은 도너
                 보정 대역(<=16k) 밖 → f/p 다항 외삽.
    via Ref    — SC 2~16k → Ref 좌표 8~64k: SC 4k 까지만 대역 내.
    즉 SC 16k 는 어느 도너로도 상사 도달 불가 — 비대칭 플랜이 고속 대역
    (k_r^2 w > w_max)을 자체 샘플링하는 이유의 직접 실측이 된다.

평가 (SC 검증 전수, run_halfsc_zeroshot 과 동일 지표):
  A. 무보정 Hybrid (AF=1)
  B. SC 채택 플랜 (자체 27점 = 24+3, Ref 저속 전달)          ← 논문 값 1.24%
  C. HalfSC 경유 제로샷 (SC 자체 TS-FEA 0점; 16k 는 외삽)
  D. Ref 경유 제로샷 (4k 까지만 대역 내; 8/16k 외삽)
  E. 혼합 도너 제로샷 (2~4k Ref, 8k HalfSC 대역 내 / 16k HalfSC 외삽)
  F. E + 자체 3점 재앵커 (16k, κ-스팬) — 외삽 대역 구제 여부
  In-band(<=8k) / out-of-band(16k) 분리는 by_speed 로 판독.

실행:  python run_sc_extrapolation.py
산출:  map_exports/e10/SC/sc_extrapolation_eval.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import numpy as np                                    # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline   # noqa: E402

K_H, K_S = 1.5, 2.0
OUT = os.path.join(HERE, "map_exports", "e10", "SC",
                   "sc_extrapolation_eval.json")


def err_stats(f_ac, pred):
    e = np.abs((pred - f_ac) / (f_ac + 1e-12) * 100.0)
    return {
        "mae_pct": float(e.mean()),
        "wmae_pct": float(np.sum(f_ac * e) / np.sum(f_ac)),
        "p95_pct": float(np.percentile(e, 95)),
        "max_pct": float(e.max()),
    }


def by_speed(ds, f_ac, pred):
    out = {}
    for spd in sorted(set(np.round(ds.speeds_k, 3))):
        m = np.abs(ds.speeds_k - spd) < 0.1
        out[f"{spd:g}k"] = err_stats(f_ac[m], pred[m])
    return out


def main() -> int:
    pl = AcLossPipeline()
    ds = pl.load_dataset("SC")
    f_ac, h_ac = ds.f_ac_arr, ds.h_ac_arr
    w_rpm = ds.speeds_k * 1000.0
    print(f"SC 검증점 {len(ds)}개, 속도 {sorted(set(ds.speeds_k))} kRPM")

    # A. 무보정
    pred_A = h_ac.copy()

    # B. 채택 플랜 (자체 27점)
    m_sc = pl.build_model("SC")
    pred_B = h_ac * m_sc.predict(w_rpm, ds.irms_arr, ds.phase_arr)

    # C. HalfSC 경유 제로샷: AF_Half(1.7778 w, 0.75 I, b)
    m_half = pl.build_model("HalfSC")
    r_h = (K_S / K_H) ** 2                   # 1.7778
    af_C = m_half.predict(w_rpm * r_h, ds.irms_arr * (K_H / K_S),
                          ds.phase_arr)
    pred_C = h_ac * af_C

    # D. Ref 경유 제로샷: AF_Ref(4 w, I/2, b)
    m_ref = pl.build_model("Ref")
    af_D = m_ref.predict(w_rpm * K_S**2, ds.irms_arr / K_S, ds.phase_arr)
    pred_D = h_ac * af_D

    # E. 혼합 도너: 대역 내 사상 우선 — 2~4k Ref(8~16k), 8k HalfSC(14.2k),
    #    16k 는 불가피하게 HalfSC 외삽(28.4k; 초과율 1.78, Ref 4.0 보다 완만)
    lo = ds.speeds_k < 6.0                   # 2, 4k
    af_E = np.where(lo, af_D, af_C)
    pred_E = h_ac * af_E

    # F. E + 16k 자체 3점 재앵커 (κ-스팬: log AF_zs 의 min/med/max)
    hi = ds.speeds_k > 12.0                  # 16k = 외삽 대역
    idx16 = np.where(hi)[0]
    af_true_16 = ds.af_arr[idx16]
    af_zs_16 = af_C[idx16]
    order = np.argsort(af_zs_16)
    pick = [order[0], order[len(order) // 2], order[-1]]
    anchor_idx = idx16[pick]
    x = np.log(np.clip(af_zs_16[pick], 1e-3, None))
    y = np.log(np.clip(af_true_16[pick], 1e-3, None))
    p_c, logf_c = np.polyfit(x, y, 1)
    f_c = float(np.exp(logf_c))
    af_F = np.where(hi, f_c * np.clip(af_C, 1e-3, None) ** p_c, af_E)
    pred_F = h_ac * af_F
    print(f"\n[F] 16k 앵커 3점(κ-스팬): "
          f"{[(round(ds.irms_arr[i],1), round(ds.phase_arr[i],1)) for i in anchor_idx]}"
          f"  → f_c={f_c:.4f}, p_c={p_c:.4f}")

    res = {}
    for tag, pred, note in (
        ("A_uncorrected", pred_A, "AF=1"),
        ("B_own27", pred_B, "채택 플랜 24+3 (Ref 저속 전달) — 논문 기준값"),
        ("C_zeroshot_via_HalfSC", pred_C,
         "SC TS-FEA 0점; HalfSC 좌표 3.56~28.4k — 16k 는 1.78배 초과 외삽"),
        ("D_zeroshot_via_Ref", pred_D,
         "Ref 좌표 8~64k — 4k 까지만 대역 내, 8/16k 는 2~4배 초과 외삽"),
        ("E_zeroshot_mixed", pred_E,
         "TS-FEA 0점 최적 조합: 2~4k Ref + 8k HalfSC(대역 내) + 16k HalfSC 외삽"),
        ("F_zeroshot_plus3", pred_F,
         "자체 TS-FEA 3점(16k, κ-스팬) 재앵커 — 외삽 대역 구제 검증"),
    ):
        res[tag] = {"note": note,
                    "overall": err_stats(f_ac, pred),
                    "by_speed": by_speed(ds, f_ac, pred)}

    # in-band(<=8k) / out-band(16k) 분리 집계
    inb = ~hi
    for tag, pred in (("C_zeroshot_via_HalfSC", pred_C),
                      ("E_zeroshot_mixed", pred_E),
                      ("F_zeroshot_plus3", pred_F)):
        res[tag]["in_band_le8k"] = err_stats(f_ac[inb], pred[inb])
        res[tag]["out_band_16k"] = err_stats(f_ac[hi], pred[hi])

    print(f"\n{'예측자':<24}{'wMAE%':>8}{'MAE%':>8}{'p95%':>8}{'max%':>8}")
    print("-" * 58)
    for tag in res:
        o = res[tag]["overall"]
        print(f"{tag:<24}{o['wmae_pct']:>8.2f}{o['mae_pct']:>8.2f}"
              f"{o['p95_pct']:>8.2f}{o['max_pct']:>8.2f}")
    print("\n속도별 wMAE%:")
    spds = list(res["A_uncorrected"]["by_speed"].keys())
    hdr = "  ".join(f"{t.split('_')[0]:>6}" for t in res)
    print(f"  {'spd':>4}: {hdr}")
    for sp in spds:
        row = "  ".join(f"{res[t]['by_speed'][sp]['wmae_pct']:6.2f}"
                        for t in res)
        print(f"  {sp:>4}: {row}")

    res["_meta"] = {
        "mapping_via_HalfSC": "AF_SC(w,I,b) = AF_Half(1.7778*w, 0.75*I, b)",
        "mapping_via_Ref": "AF_SC(w,I,b) = AF_Ref(4*w, 0.5*I, b)",
        "coverage": "SC<=4k: Ref 대역 내 / SC 8k: HalfSC 대역 내 / "
                    "SC 16k: 도달 불가(최근접 HalfSC 1.78배 외삽)",
        "n_points": int(len(ds)),
        "anchor_ops_16k": [
            [float(ds.irms_arr[i]), float(ds.phase_arr[i])]
            for i in anchor_idx],
        "f_c": f_c, "p_c": float(p_c),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
