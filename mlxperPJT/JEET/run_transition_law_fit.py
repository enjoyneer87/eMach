# -*- coding: utf-8 -*-
"""상용 전환 규약 최종 판별 — 기계별 f_t,eff 적합 + 치수 지수 회귀 + h-vs-w.

입력: 스펙트럼 저장 JSON 4종 (b2t/b2r_msq_sum + mcad_prox_W):
  e4a (전 티어), {Ref,HalfSC,SC}_rated (정격 460 A 티어, 전 속도)
기계별로 캡 스케일 s를 자유화한 translim P24c6 를 재구성해
  J(s) = Σ_OP (log P_s − log mcad_prox)^2
최소화 → f_t,eff = s*·f_t(h). 이후
  (1) log f_t,eff ~ log h 지수 b (4기계),
  (2) k_r 패밀리(종횡비 2.20 공유) 적합으로 e4a 예측 — h-기준 vs w-기준
      (e4a 종횡비 1.15가 축퇴를 깸) 중 측정값에 가까운 쪽 판별.

산출: map_exports/e10/transition_law_fit.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "acloss_ref_methods"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
import mesh_b_vs_mcad as _mb                                # noqa: E402

_mb.SIGMA /= 1.2358          # 80°C 정합 (스펙트럼 실행과 동일)
_mb._SIGMA_V /= 1.2358

E10 = os.path.join(HERE, "map_exports", "e10")
MACHINES = {   # tag -> (line_json, h_radial_m, w_tan_m, summary_json)
    "Ref": (os.path.join(E10, "Ref_rated",
                         "line_sampled_hybrid_Ref_rated_80C.json"),
            3.711e-3, 1.686e-3,
            os.path.join(E10, "Ref", "JEET_ACLoss_Ref_Map_Summary.json")),
    "HalfSC": (os.path.join(E10, "HalfSC_rated",
                            "line_sampled_hybrid_HalfSC_rated_80C.json"),
               5.5665e-3, 2.529e-3,
               os.path.join(E10, "HalfSC",
                            "JEET_ACLoss_HalfSC_Map_Summary.json")),
    "SC": (os.path.join(E10, "SC_rated",
                        "line_sampled_hybrid_SC_rated_80C.json"),
           7.422e-3, 3.372e-3,
           os.path.join(E10, "SC", "JEET_ACLoss_SC_Map_Summary.json")),
    "e4a": (os.path.join(E10, "e4a", "line_sampled_hybrid_e4a_80C.json"),
            3.551e-3, 3.079e-3,
            r"D:\KangDH\Thesis\e4a\newfam_results\kturn4"
            r"\JEET_ACLoss_kturn4_Map_Summary.json"),
}


def load_mcad_prox(path):
    """요약 JSON(list 또는 {'records':...})에서 (speed, current, phase)->prox_W."""
    d = json.load(open(path, encoding="utf-8"))
    recs = d if isinstance(d, list) else (d.get("records") or d.get("rows"))
    lut = {}
    for r in recs:
        if r.get("proximity_model", r.get("prox_model")) != 1:
            continue
        pw = r.get("hybrid_prox_W")
        if pw is None and r.get("hybrid_prox_kW") is not None:
            pw = r["hybrid_prox_kW"] * 1e3
        if pw is None:
            continue
        lut[(round(float(r["speed"])), round(float(r["current"]), 1),
             round(float(r["phase"]), 1))] = pw
    return lut
POLE_PAIRS = 4
MU0 = 4e-7 * np.pi
OUT = os.path.join(E10, "transition_law_fit.json")


def f_t_of(dim_m):
    return 1.0 / (np.pi * MU0 * _mb.SIGMA * dim_m ** 2)


def main() -> int:
    res = {}
    for tag, (path, h, w, summary) in MACHINES.items():
        if not os.path.exists(path):
            print(f"[{tag}] JSON 없음 — 건너뜀: {path}")
            continue
        d = json.load(open(path, encoding="utf-8"))
        mcad = load_mcad_prox(summary) if os.path.exists(summary) else {}
        ops = []
        for r in d["rows"]:
            if r["current_A"] <= 1 or not r.get("b2t_msq_sum"):
                continue
            pw = r.get("mcad_prox_W") or mcad.get(
                (round(r["speed_rpm"]), round(r["current_A"], 1),
                 round(r["phase_deg"], 1)))
            if pw:
                ops.append({**r, "mcad_prox_W": pw})
        ft0 = f_t_of(h)
        svals = np.exp(np.linspace(np.log(0.2), np.log(20.0), 55))
        if len(ops) < 6:
            print(f"[{tag}] 매칭 {len(ops)}건 — 적합 제외")
            continue
        best = None
        for s in svals:
            errs = []
            for r in ops:
                f_e = r["speed_rpm"] * POLE_PAIRS / 60.0
                b2t = np.array(r["b2t_msq_sum"])
                b2r = np.array(r["b2r_msq_sum"])
                f_m = np.arange(1, len(b2t) + 1) * f_e
                cap = np.minimum(1.0, s * ft0 / f_m)
                p = _mb.prox_24(f_m * np.sqrt(cap), b2t, b2r, w_c := h,
                                h_c := w, n_cuboids=6) * _mb.SECTORS
                errs.append(np.log(p) - np.log(r["mcad_prox_W"]))
            j = float(np.mean(np.square(errs)))
            if best is None or j < best[1]:
                best = (float(s), j)
        s_star, j_star = best
        fte = s_star * ft0
        # s* 에서의 잔차 통계
        rat = []
        for r in ops:
            f_e = r["speed_rpm"] * POLE_PAIRS / 60.0
            b2t = np.array(r["b2t_msq_sum"])
            b2r = np.array(r["b2r_msq_sum"])
            f_m = np.arange(1, len(b2t) + 1) * f_e
            cap = np.minimum(1.0, s_star * ft0 / f_m)
            p = _mb.prox_24(f_m * np.sqrt(cap), b2t, b2r, h, w,
                            n_cuboids=6) * _mb.SECTORS
            rat.append(p / r["mcad_prox_W"])
        rat = np.array(rat)
        res[tag] = {"n_ops": len(ops), "f_t_h_Hz": round(ft0, 1),
                    "s_star": round(s_star, 3),
                    "f_t_eff_Hz": round(fte, 1),
                    "ratio_at_fit": [round(float(rat.mean()), 3),
                                     round(float(rat.std()), 3)],
                    "h_mm": h * 1e3, "w_mm": w * 1e3}
        print(f"[{tag}] f_t(h)={ft0:.0f} Hz, s*={s_star:.3f} -> "
              f"f_t,eff={fte:.0f} Hz  (비 {rat.mean():.3f}±{rat.std():.3f}, "
              f"n={len(ops)})")

    fam = [t for t in ("Ref", "HalfSC", "SC") if t in res]
    if len(fam) == 3 and "e4a" in res:
        lh = np.log([res[t]["h_mm"] for t in fam])
        lf = np.log([res[t]["f_t_eff_Hz"] for t in fam])
        b, a = np.polyfit(lh, lf, 1)
        print(f"\nk_r 패밀리 지수: f_t,eff ∝ h^({b:.2f})")
        pred_h = float(np.exp(a + b * np.log(res["e4a"]["h_mm"])))
        pred_w = float(np.exp(a + b * np.log(
            res["e4a"]["w_mm"] * (res["Ref"]["h_mm"] / res["Ref"]["w_mm"]))))
        meas = res["e4a"]["f_t_eff_Hz"]
        print(f"e4a 예측: h-기준 {pred_h:.0f} Hz / w-기준 {pred_w:.0f} Hz "
              f"vs 측정 {meas:.0f} Hz")
        verdict = "h" if abs(np.log(meas / pred_h)) < \
            abs(np.log(meas / pred_w)) else "w"
        print(f"→ 기준 치수 판별: {verdict}-기준이 측정에 근접")
        res["_regression"] = {"exponent_b": round(float(b), 3),
                              "e4a_pred_h_Hz": round(pred_h, 1),
                              "e4a_pred_w_Hz": round(pred_w, 1),
                              "e4a_meas_Hz": meas, "verdict": verdict}

    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
