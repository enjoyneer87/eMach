# -*- coding: utf-8 -*-
r"""턴 축 AF 재활용 --- 6t 보정 + MS 슬롯 필드로 4t/8t 예측 (2026-08-27).

저자 방안: 6t 에서 27점 Full-FEA 보정이 있고 MS-FEA 는 슬롯 전체 B 를
들고 있으니, 턴이 바뀌면 B 를 쓸 면적·위치(분할 창)만 다시 고르면 새
턴수의 하이브리드 분모가 공짜고, 보정(반작용 몫)은 6t 것을 쓰면 된다.

인수분해:
    P_TS^Nt(w,I,b)  =  AF_el^6t(k_h^2 w, I·Nt/6, b)  x  P_el^Nt(w,I,b)
                       (6t 보정의 반작용 몫,             (슬롯 스펙트럼 +
                        ξ-정합 속도 log-log 보간)         prox_g2 천이 커널)

입력: map_exports/e10/kturn/kturn_spectrum.json
      (run_kturn_spectrum_extract.py --- 16k 24운전점 x 3모델의 방향 분리
       슬롯 조화 스펙트럼 + Jensen 면.  추출 약 1시간이라 결과를 리포지토리에
       둔다)

채점 결과 (2026-08-27, 96 운전점 와트 가중):
  A. 필드 불변성 --- MMF 재색인은 근사다.  슬롯 MMF 계단(4/6/8단) 차이로
     조화 진폭이 4t 13.6% / 8t 5.5% 어긋난다 (12.11 "기하 비스케일" 첫 실측).
  B. 커널 --- prox_g2 조화합 + 전역 상수 1개로 full_G2_solid 재현 잔차
     평균 2.0% / 최대 4.1%.
  C. 순수 0 TS-FEA: 4t 28.9% / 8t 10.6% (6t 필드 재사용).
     + 전역 스칼라 f_c 하나(실무 TS 1~3점): 4t 4.77% / 8t 3.98% ---
     기존 Tier1 재앵커(4t 8.57% 대역한정 / 8t 5.17%)를 전 대역 일괄로
     이긴다.  잔차가 곱셈 오프셋 하나에 압축된다는 뜻.
     f_c = 4t 0.777 / 6t 1 / 8t 1.117 (k_h 에 단조).  스펙트럼 원천을
     자체 MS 로 바꿔도 f_c 0.79/1.14 로 거의 불변 --- 계단 비불변성도
     대부분 f_c 로 접히므로 턴별 MS 재해석이 불필요하다.

실행:  python run_kturn_af_reuse.py
산출:  map_exports/e10/kturn/kturn_af_reuse.json
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
from acloss_ref_methods.mesh_b_vs_mcad import prox_g2  # noqa: E402

KT = os.path.join(HERE, "map_exports", "e10", "kturn")
SPEC = json.load(io.open(os.path.join(KT, "kturn_spectrum.json"),
                         encoding="utf-8"))
POLE_PAIRS = 4
# 반경 h x 접선 w [m], 도체 면적 [mm^2] --- 요소 중심·면적 실측 (2026-08-27)
DIMS = {4: (2.485e-3, 3.73e-3, 14.528),
        6: (1.686e-3, 3.711e-3, 9.686),
        8: (1.173e-3, 3.73e-3, 7.264)}
K_H2 = {t: (DIMS[t][0] / DIMS[6][0]) ** 2 for t in DIMS}
TAG = {4: "4t", 6: "6t", 8: "8t"}


def fe(speed_k):
    return speed_k * 1000 * POLE_PAIRS / 60.0


S = {}
for tag in ("6t", "4t", "8t"):
    S[tag] = {(r["current_A"], r["phase_deg"]):
              (np.array(r["S_t"]), np.array(r["S_r"]))
              for r in SPEC[tag]}
I_LV = {tag: sorted({k[0] for k in S[tag]}) for tag in S}


def snap(tag, i):
    lv = min(I_LV[tag], key=lambda x: abs(x - i))
    return lv if abs(lv - i) / lv < 0.02 else None


def prox_raw(nt, speed_k, st, sr):
    """조화별 prox_g2 합 [상수 미정].  b2 = 슬롯합/도체면적."""
    h, w, a_c = DIMS[nt]
    f1 = fe(speed_k)
    return sum(prox_g2(m * f1, st[m] / a_c, sr[m] / a_c, w, h)
               for m in range(1, len(st)))


def main() -> int:
    out = {}

    # ── A. 필드 불변성 (MMF 짝의 조화 진폭 대조) ───────────────────────
    print("=== A. 필드 불변성 (S_m 기본파+3고조파, MMF 짝) ===")
    for tag, nt in (("4t", 4), ("8t", 8)):
        devs = []
        for (i, b), (st, sr) in S[tag].items():
            i6 = snap("6t", i * nt / 6.0)
            if i6 is None:
                continue
            st6, sr6 = S["6t"][(i6, b)]
            for m in (1, 3):
                if st6[m] > 1e-9:
                    devs.append(st[m] / st6[m] - 1)
                if sr6[m] > 1e-9:
                    devs.append(sr[m] / sr6[m] - 1)
        d = 100 * np.array(devs)
        out.setdefault("invariance", {})[tag] = {
            "mean_pct": round(float(d.mean()), 2),
            "mad_pct": round(float(np.abs(d).mean()), 2),
            "p95_pct": round(float(np.percentile(np.abs(d), 95)), 2)}
        print("  %s vs 6t : 평균 %+.2f%%  |편차| 평균 %.2f%%  p95 %.2f%%"
              % (tag, d.mean(), np.abs(d).mean(),
                 np.percentile(np.abs(d), 95)))

    # ── B. 전역 상수 캘리브레이션 (6t, 16k, full_G2_solid) ─────────────
    rows6 = json.load(io.open(os.path.join(
        HERE, "map_exports", "e10", "Ref",
        "line_sampled_hybrid_Ref_80C.json"), encoding="utf-8"))["rows"]
    g2ref = {(r["current_A"], r["phase_deg"]): r["full_G2_solid"]
             for r in rows6 if r["current_A"] > 1.0}
    num = den = 0.0
    pairs = []
    for (i, b), g2 in g2ref.items():
        st, sr = S["6t"][(snap("6t", i), b)]
        raw = prox_raw(6, 16.0, st, sr)
        pairs.append((g2, raw))
        num += g2 * raw
        den += raw * raw
    cal = num / den
    resid = 100 * np.array([abs(cal * r - g) / g for g, r in pairs])
    out["kernel_cal"] = {"value": round(cal, 4),
                         "recon_mae_pct": round(float(resid.mean()), 2),
                         "recon_max_pct": round(float(resid.max()), 2)}
    print("\n=== B. 커널 상수 ===  CAL %.4g  재현 잔차 %.2f%% (최대 %.2f%%)"
          % (cal, resid.mean(), resid.max()))

    def p_el(nt, speed_k, i_own, beta, src):
        if src == TAG[nt]:
            key = (snap(src, i_own), beta)
        else:                               # MMF 재색인
            key = (snap(src, i_own * nt / 6.0), beta)
        st, sr = S[src][key]
        h, w, _ = DIMS[nt]
        sk = calc_skin_loss(w, h, fe(speed_k), L_ACTIVE,
                            i_own / N_PARALLEL)
        return cal * prox_raw(nt, speed_k, st, sr) \
            + sk["P_excess_W"] * 48 * nt

    # ── 6t 의 AF_el 격자 + 속도 보간 ───────────────────────────────────
    pl = AcLossPipeline()
    ds = pl.load_dataset("Ref")
    arr = {}
    for s_k, i, b, f_kw in zip(np.asarray(ds.speeds_k),
                               np.asarray(ds.irms_arr),
                               np.asarray(ds.phase_arr),
                               np.asarray(ds.f_ac_arr)):
        if i <= 1.0:
            continue
        af = f_kw * 1e3 / p_el(6, float(s_k), float(i), float(b), "6t")
        arr.setdefault((snap("6t", i), float(b)), []).append(
            (float(s_k), af))
    af6 = {}
    for k, v in arr.items():
        v.sort()
        af6[k] = (np.log([x[0] for x in v]), np.log([x[1] for x in v]))

    def af_el_6(speed_k, i6, beta):
        ls, la = af6[(i6, beta)]
        x = np.log(speed_k)
        if x <= ls[0]:
            sl = (la[1] - la[0]) / (ls[1] - ls[0])
            return float(np.exp(la[0] + sl * (x - ls[0])))
        if x >= ls[-1]:
            sl = (la[-1] - la[-2]) / (ls[-1] - ls[-2])
            return float(np.exp(la[-1] + sl * (x - ls[-1])))
        return float(np.exp(np.interp(x, ls, la)))

    # ── C. 본 채점: 순수 0점 + 전역 f_c ────────────────────────────────
    print("\n=== C. 예측 wMAE (96 운전점, 와트 가중) ===")
    base = {"4t": 15.83, "8t": 11.18}      # 12.11 도체평균 사상 제로샷
    for nt in (4, 8):
        tag = TAG[nt]
        rows, _, _ = load_pairs(nt)
        v = [r for r in rows if r["irms"] > 1.0 and r["hyb_kW"] > 0
             and r["fea_kW"] > 0]
        res = {"baseline_condavg_mapped_pct": base[tag]}
        for src_name, src in (("reuse6t", "6t"), ("ownMS", tag)):
            pred, true, spd = [], [], []
            for r in v:
                i6 = snap("6t", r["irms"] * nt / 6.0)
                pred.append(af_el_6(r["speed_k"] * K_H2[nt], i6, r["beta"])
                            * p_el(nt, r["speed_k"], r["irms"],
                                   r["beta"], src))
                true.append(r["fea_kW"] * 1e3)
                spd.append(r["speed_k"])
            pred, true = np.array(pred), np.array(true)
            spd = np.array(spd)

            def wm(p):
                e = np.abs(p - true) / true * 100
                by = {"%gk" % s: round(float(
                    np.sum(true[spd == s] * e[spd == s])
                    / np.sum(true[spd == s])), 2)
                    for s in sorted(set(spd))}
                return float(np.sum(true * e) / np.sum(true)), by

            w0, by0 = wm(pred)
            off = np.sum(true * np.log(true / pred)) / np.sum(true)
            w1, by1 = wm(pred * np.exp(off))
            res[src_name] = {
                "zero_wmae_pct": round(w0, 2), "zero_by_speed": by0,
                "fc": round(float(np.exp(off)), 3),
                "fc_wmae_pct": round(w1, 2), "fc_by_speed": by1}
            print("  %s %-8s 순수 %6.2f%%   +f_c(%.3f) %6.2f%%   %s"
                  % (tag, src_name, w0, np.exp(off), w1, by1))
        print("  %s baseline %6.2f%%  (도체평균 사상 제로샷)"
              % (tag, base[tag]))
        out[tag] = res

    io.open(os.path.join(KT, "kturn_af_reuse.json"), "w",
            encoding="utf-8").write(
        json.dumps(out, indent=1, ensure_ascii=False))
    print("저장:", os.path.join(KT, "kturn_af_reuse.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
