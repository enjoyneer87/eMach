# -*- coding: utf-8 -*-
r"""k_r x k_w 동시 사상 --- 합성 도너로 턴 변형을 예측, Full-FEA 대조 (2026-08-27).

질문 (저자): 12.29 의 필드 재사용 스킴으로 k_r 과 턴수(k_w)를 **동시에**
스케일한 경우를 k_w 관점에서 Full-FEA 와 비교하라.

구성.  목표 = kturn4 (k_w=2/3) / kturn8 (k_w=4/3), 모두 k_r=1.  도너 =
Ref (k_r=1) / HalfSC (1.5) / SC (2), 모두 k_w=1.  Ref 외 도너는 두 축이
동시에 다르므로 사상이 합성된다:

    도너 (k_r^D, k_w=1)  --[k_r 상사, 정확]-->  Ref 등가 (1, 1)
        w_eq = k_rD^2 w_D,  I_eq = I_D / k_rD,  P_TS 불변
    Ref 등가  --[12.29 턴 사상]-->  목표 (1, k_w)
        AF_el(k_h^2 w, I·Nt/6, b) x P_el^Nt(w, I, b)

k_w 관점의 핵심: 도너의 등가 속도 대역이 k_rD^2 만큼 위로 밀린다.
    Ref {2..16}k / HalfSC {4.5..36}k / SC {8..64}k (등가)
목표가 요구하는 대역 = k_h^2 x {2..16}k:
    4t (k_h^2=2.17): {4.3, 8.7, 17.4, 34.8}k --- Ref 는 절반이 심외삽,
        HalfSC 가 거의 전부, SC 가 고속 3개를 인밴드로 덮는다.
    8t (k_h^2=0.48): {1.0, 1.9, 3.9, 7.7}k --- Ref 만 덮는다.
즉 **k_r 도너 사다리가 턴 축의 도달 대역을 확장**한다 --- 12.9 의 "도달
불가 대역은 자체 샘플링 필수" 를 2 축 합성으로 우회하는 실측.

실행:  python run_kturn_kr_kw_compose.py
산출:  map_exports/e10/kturn/kturn_kr_kw_compose.json
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
os.environ.setdefault("JEET_DATA_ROOT",
                      os.path.join(HERE, "map_exports", "e10"))

import numpy as np                                     # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline    # noqa: E402
from run_kturn_af_analysis import load_pairs           # noqa: E402
from run_meshb_hybrid_all import (                     # noqa: E402
    calc_skin_loss, L_ACTIVE, N_PARALLEL)
from run_kturn_af_reuse import (                       # noqa: E402
    S, snap, prox_raw, DIMS, K_H2, TAG, fe)

KT = os.path.join(HERE, "map_exports", "e10", "kturn")
K_R = {"Ref": 1.0, "HalfSC": 1.5, "SC": 2.0}


def main() -> int:
    # ── 커널 상수 (12.29 와 동일 캘리브레이션) ─────────────────────────
    rows6 = json.load(io.open(os.path.join(
        HERE, "map_exports", "e10", "Ref",
        "line_sampled_hybrid_Ref_80C.json"), encoding="utf-8"))["rows"]
    num = den = 0.0
    for r in rows6:
        if r["current_A"] <= 1.0:
            continue
        st, sr = S["6t"][(snap("6t", r["current_A"]), r["phase_deg"])]
        raw = prox_raw(6, 16.0, st, sr)
        num += r["full_G2_solid"] * raw
        den += raw * raw
    cal = num / den

    def p_el(nt, speed_k, i_own, beta):
        """요소 분해 분모 [W] --- Ref 스펙트럼 재사용 (12.29 reuse 경로)."""
        key = ((snap("6t", i_own), beta) if nt == 6
               else (snap("6t", i_own * nt / 6.0), beta))
        st, sr = S["6t"][key]
        h, w, _ = DIMS[nt]
        sk = calc_skin_loss(w, h, fe(speed_k), L_ACTIVE,
                            i_own / N_PARALLEL)
        return cal * prox_raw(nt, speed_k, st, sr) \
            + sk["P_excess_W"] * 48 * nt

    # ── 도너별 Ref-등가 AF_el 표 (k_r 상사로 환산) ─────────────────────
    pl = AcLossPipeline()

    def build_equiv(donor):
        kr = K_R[donor]
        ds = pl.load_dataset(donor)
        arr = {}
        for s_k, i, b, f_kw in zip(np.asarray(ds.speeds_k),
                                   np.asarray(ds.irms_arr),
                                   np.asarray(ds.phase_arr),
                                   np.asarray(ds.f_ac_arr)):
            if i <= 1.0:
                continue
            w_eq = float(s_k) * kr ** 2            # 등가 속도 [kRPM]
            i_eq = float(i) / kr                   # 등가 전류
            af = f_kw * 1e3 / p_el(6, w_eq, i_eq, float(b))
            arr.setdefault((snap("6t", i_eq), float(b)), []).append(
                (w_eq, af))
        tab = {}
        for k, v in arr.items():
            v.sort()
            tab[k] = (np.log([x[0] for x in v]), np.log([x[1] for x in v]))
        return tab

    EQ = {d: build_equiv(d) for d in ("Ref", "HalfSC", "SC")}
    BAND = {d: (2.0 * K_R[d] ** 2, 16.0 * K_R[d] ** 2) for d in EQ}

    def af_query(tab, speed_k, i6, beta):
        """log-log 보간.  (값, 인밴드 여부) 반환."""
        ls, la = tab[(i6, beta)]
        x = np.log(speed_k)
        if x <= ls[0]:
            sl = (la[1] - la[0]) / (ls[1] - ls[0])
            return float(np.exp(la[0] + sl * (x - ls[0]))), x >= ls[0] - 0.05
        if x >= ls[-1]:
            sl = (la[-1] - la[-2]) / (ls[-1] - ls[-2])
            return float(np.exp(la[-1] + sl * (x - ls[-1]))), \
                x <= ls[-1] + 0.05
        return float(np.exp(np.interp(x, ls, la))), True

    def pick_best(speed_k):
        """대역이 덮는 도너 중 로그 중심이 가장 가까운 것."""
        cands = []
        for d, (lo, hi) in BAND.items():
            inb = lo * 0.95 <= speed_k <= hi * 1.05
            cen = abs(np.log(speed_k) - 0.5 * (np.log(lo) + np.log(hi)))
            cands.append((not inb, cen, d))
        cands.sort()
        return cands[0][2], not cands[0][0]

    # ── 채점 ───────────────────────────────────────────────────────────
    out = {"cal": round(cal, 4),
           "bands_eq_kRPM": {d: [round(v, 2) for v in BAND[d]]
                             for d in BAND}}
    print("등가 대역 [kRPM]:",
          {d: out["bands_eq_kRPM"][d] for d in ("Ref", "HalfSC", "SC")})
    for nt in (4, 8):
        tag = TAG[nt]
        rows, _, _ = load_pairs(nt)
        v = [r for r in rows if r["irms"] > 1.0 and r["hyb_kW"] > 0
             and r["fea_kW"] > 0]
        need = sorted({round(r["speed_k"] * K_H2[nt], 2) for r in v})
        print("\n=== 목표 %s (k_w=%d/6)  요구 등가 대역 %s ===" %
              (tag, nt, need))
        res = {"need_eq_kRPM": need}
        for donor in ("Ref", "HalfSC", "SC", "best"):
            pred, true, spd, inb = [], [], [], []
            for r in v:
                w_need = r["speed_k"] * K_H2[nt]
                d = donor
                if donor == "best":
                    d, _ = pick_best(w_need)
                i6 = snap("6t", r["irms"] * nt / 6.0)
                af, ok = af_query(EQ[d], w_need, i6, r["beta"])
                pred.append(af * p_el(nt, r["speed_k"], r["irms"],
                                      r["beta"]))
                true.append(r["fea_kW"] * 1e3)
                spd.append(r["speed_k"])
                inb.append(ok)
            pred, true = np.array(pred), np.array(true)
            spd, inb = np.array(spd), np.array(inb)

            def wm(p, m=None):
                m = np.ones(len(p), bool) if m is None else m
                e = np.abs(p[m] - true[m]) / true[m] * 100
                return float(np.sum(true[m] * e) / np.sum(true[m]))

            w0 = wm(pred)
            off = np.sum(true * np.log(true / pred)) / np.sum(true)
            p1 = pred * np.exp(off)
            w1 = wm(p1)
            by = {"%gk" % s: round(wm(p1, spd == s), 2)
                  for s in sorted(set(spd))}
            res[donor] = {
                "zero_wmae_pct": round(w0, 2),
                "fc": round(float(np.exp(off)), 3),
                "fc_wmae_pct": round(w1, 2),
                "fc_by_speed": by,
                "inband_frac": round(float(inb.mean()), 3),
                # 점별 [speed_k, irms, beta, true_kW, pred_fc_kW] ---
                # kW 수준 패리티·프로파일 그림용
                "points": [[float(r["speed_k"]), float(r["irms"]),
                            float(r["beta"]),
                            round(float(t) / 1e3, 4),
                            round(float(p) / 1e3, 4)]
                           for r, t, p in zip(v, true, p1)]}
            print("  도너 %-7s 순수 %7.2f%%  +f_c(%.3f) %6.2f%%  "
                  "인밴드 %3.0f%%  속도별 %s"
                  % (donor, w0, np.exp(off), w1, 100 * inb.mean(), by))
        out[tag] = res

    io.open(os.path.join(KT, "kturn_kr_kw_compose.json"), "w",
            encoding="utf-8").write(
        json.dumps(out, indent=1, ensure_ascii=False))
    print("\n저장:", os.path.join(KT, "kturn_kr_kw_compose.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
