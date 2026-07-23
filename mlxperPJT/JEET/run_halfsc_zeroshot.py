# -*- coding: utf-8 -*-
"""HalfSC 무(無)-TS-FEA 옵션 실증 — SC 보정 모델의 상사 사상만으로 HalfSC 예측.

가설 (저자 제안): 중간 스케일 변형체(HalfSC, k_r=1.5)는 자체 TS-FEA 없이
SC(k_r=2)의 보정된 AF 를 상사 사상해 보정할 수 있다.

상사 관계 (k_a=1):
    AF_v(w, I, b) = AF_Ref(k_v^2 w, I/k_v, b)
  → AF_Half(w, I, b) = AF_SC(w * (1.5^2/2^2), I * (2/1.5), b)
                     = AF_SC(0.5625 w, 4I/3, b)

커버리지: HalfSC 전 대역(2~16k)이 SC 좌표 1.125~9k 로 사상되어 SC 의
보정 대역 안에 들어온다 (Ref 단독 donor 는 2.25w<=16k, 즉 7.1k 까지만).

평가: HalfSC 검증 120점(TS-FEA 전수)에서 4개 예측자의 MAE/wMAE 비교
  A. 무보정 Hybrid (AF=1)
  B. HalfSC 채택 플랜 (자체 27점 = 24+3, Ref 저속 전달)      ← 논문 값
  C. SC 경유 제로샷 (HalfSC 자체 TS-FEA 0점)                 ← 검증 대상
  D. Ref 경유 제로샷 (저대역만 유효, 고대역은 다항 외삽)     ← 대조군

실행:  python run_halfsc_zeroshot.py
산출:  map_exports/e10/HalfSC/halfsc_zeroshot_eval.json
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
OUT = os.path.join(HERE, "map_exports", "e10", "HalfSC",
                   "halfsc_zeroshot_eval.json")


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
    ds = pl.load_dataset("HalfSC")
    f_ac, h_ac = ds.f_ac_arr, ds.h_ac_arr
    w_rpm = ds.speeds_k * 1000.0
    print(f"HalfSC 검증점 {len(ds)}개, 속도 {sorted(set(ds.speeds_k))} kRPM")

    # A. 무보정
    pred_A = h_ac.copy()

    # B. 채택 플랜 (자체 27점)
    m_half = pl.build_model("HalfSC")
    pred_B = h_ac * m_half.predict(w_rpm, ds.irms_arr, ds.phase_arr)

    # C. SC 경유 제로샷: AF_SC(0.5625 w, 4I/3, b)
    m_sc = pl.build_model("SC")
    ratio = (K_H / K_S) ** 2                 # 0.5625
    af_C = m_sc.predict(w_rpm * ratio, ds.irms_arr * (K_S / K_H),
                        ds.phase_arr)
    pred_C = h_ac * af_C

    # D. Ref 경유 제로샷: AF_Ref(2.25 w, I/1.5, b)  — 고대역은 외삽
    m_ref = pl.build_model("Ref")
    af_D = m_ref.predict(w_rpm * K_H**2, ds.irms_arr / K_H, ds.phase_arr)
    pred_D = h_ac * af_D

    # E. 혼합 donor 제로샷: 2~8k 는 Ref 사상(대역 내 4.5~18k), 16k 만 SC 사상(9k)
    hi = ds.speeds_k > 8.5
    pred_E = h_ac * np.where(hi, af_C, af_D)

    # F. 제로샷 + 16k 자체 3점 앵커 (κ-스팬 결정론 배치, 논문의 +3 패턴)
    #    16k 대역에서 혼합 제로샷 AF 를 형상으로 두고, 자체 3점의 실측 AF 로
    #    레벨 f_c·스프레드 p_c 를 로그공간 회귀 보정:
    #        AF_F(16k,I,b) = f_c · AF_zs(16k,I,b)^{p_c}
    idx16 = np.where(hi)[0]
    af_true_16 = ds.af_arr[idx16]
    af_zs_16 = af_C[idx16]
    # κ-스팬: log(AF_zs) 의 min / median / max 3점 (간격 최대화)
    order = np.argsort(af_zs_16)
    pick = [order[0], order[len(order) // 2], order[-1]]
    anchor_idx = idx16[pick]
    x = np.log(np.clip(af_zs_16[pick], 1e-3, None))
    y = np.log(np.clip(af_true_16[pick], 1e-3, None))
    p_c, logf_c = np.polyfit(x, y, 1)          # y = p_c·x + log f_c
    f_c = float(np.exp(logf_c))
    af_F = np.where(
        hi, f_c * np.clip(af_C, 1e-3, None) ** p_c, af_D)
    pred_F = h_ac * af_F
    print(f"\n[F] 16k 앵커 3점(κ-스팬): "
          f"{[(round(ds.irms_arr[i],1), round(ds.phase_arr[i],1)) for i in anchor_idx]}"
          f"  → f_c={f_c:.4f}, p_c={p_c:.4f}")

    res = {}
    for tag, pred, note in (
        ("A_uncorrected", pred_A, "AF=1"),
        ("B_own27", pred_B, "채택 플랜 24+3 (Ref 저속 전달)"),
        ("C_zeroshot_via_SC", pred_C,
         "HalfSC TS-FEA 0점; SC 좌표 1.125~9k(2k 이하 약외삽)·전류 상한 920A=경계"),
        ("D_zeroshot_via_Ref", pred_D,
         "Ref 좌표 4.5~36k — 16k 초과 고대역은 f/p 다항 외삽(참고용)"),
        ("E_zeroshot_mixed", pred_E,
         "TS-FEA 0점 최적 조합: 2~8k Ref 사상 + 16k SC 사상 — max 오차 한 자리수"),
        ("F_zeroshot_plus3", pred_F,
         "자체 TS-FEA 3점(16k, κ-스팬)만 추가 — 제로샷 형상 + 레벨/스프레드 재앵커"),
    ):
        res[tag] = {"note": note,
                    "overall": err_stats(f_ac, pred),
                    "by_speed": by_speed(ds, f_ac, pred)}

    # 표 출력
    print(f"\n{'예측자':<22}{'wMAE%':>8}{'MAE%':>8}{'p95%':>8}{'max%':>8}")
    print("-" * 56)
    for tag in res:
        o = res[tag]["overall"]
        print(f"{tag:<22}{o['wmae_pct']:>8.2f}{o['mae_pct']:>8.2f}"
              f"{o['p95_pct']:>8.2f}{o['max_pct']:>8.2f}")
    print("\n속도별 wMAE% (A/B/C/D):")
    spds = list(res["A_uncorrected"]["by_speed"].keys())
    for sp in spds:
        row = "  ".join(f"{res[t]['by_speed'][sp]['wmae_pct']:6.2f}"
                        for t in res)
        print(f"  {sp:>4}: {row}")

    res["_meta"] = {
        "mapping": "AF_Half(w,I,b) = AF_SC(0.5625*w, 4I/3, b)",
        "sc_plan": pl.cfg["plan"]["SC"],
        "half_plan": pl.cfg["plan"]["HalfSC"],
        "n_points": int(len(ds)),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
