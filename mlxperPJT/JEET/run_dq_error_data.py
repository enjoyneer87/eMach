# -*- coding: utf-8 -*-
"""부록 B 패널 그림의 입력 — 두 전달 방향을 같은 형식으로 뽑는다.

`run_sc_extrapolation.py` 는 SC 한 대만 다룬다.  부록 문단의 제목이
"Direction of transfer" 인데 표는 외삽 방향만 싣고 있어 대비가 없다.

  - 목표 HalfSC (k_r 1.5) = 보간 방향.  도너가 Ref(1) 와 SC(2) 양쪽에 있다
  - 목표 SC     (k_r 2.0) = 외삽 방향.  도너가 안쪽에만 있다

상사 사상은 목표 t, 도너 d 에 대해
      AF_t(w, I, b) = AF_d( (k_t/k_d)^2 w,  (k_d/k_t) I,  b )
이고, 도너가 2~16 kRPM 을 스윕하므로 목표 좌표의 도달 구간은
      w_t in [2 / r,  16 / r],   r = (k_t/k_d)^2
가 된다.  이 구간 밖이 외삽이고, 표 B.2 의 큰 오차가 전부 거기서 난다.

  python run_dq_error_data.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import contextlib                                      # noqa: E402
import io                                              # noqa: E402

import numpy as np                                     # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline    # noqa: E402
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder  # noqa: E402

K = {"Ref": 1.0, "HalfSC": 1.5, "SC": 2.0}
SWEPT = (2.0, 16.0)                       # 모든 기계가 도는 속도 대역 [kRPM]
TARGETS = ("HalfSC", "SC")
OUT = os.path.join(HERE, "map_exports", "e10", "dq_error_panels.npz")


def main() -> int:
    pl = AcLossPipeline()
    models, out = {}, {}

    # 도너의 자체 Full-FEA 표본.  몇 개를 어디에 두었는지가 예측의 근거라,
    # 평가 격자와 구분해서 실어 둔다.  Ref 는 own 모드라 비앵커 속도마다
    # 4 점, 변형체는 transfer 라 8 kRPM 에 3 점뿐이다.
    for s in K:
        with contextlib.redirect_stdout(io.StringIO()):
            ds_d = pl.load_dataset(s)
            models[s] = pl.build_model(s)
        idx = np.asarray(getattr(RbfModelBuilder, "last_train_idx", []),
                         dtype=int).ravel()
        q = s.lower()
        out[q + "_train_speeds_k"] = np.asarray(ds_d.speeds_k, float)[idx]
        out[q + "_train_irms"] = np.asarray(ds_d.irms_arr, float)[idx]
        out[q + "_train_phase"] = np.asarray(ds_d.phase_arr, float)[idx]
        print("도너 %-7s 자체 표본 %d 점" % (s, idx.size), end="  ")
        for spd in sorted(set(np.round(np.asarray(ds_d.speeds_k)[idx], 3))):
            n = int(np.sum(np.abs(
                np.asarray(ds_d.speeds_k)[idx] - spd) < 0.1))
            print("%gk:%d" % (spd, n), end="  ")
        print()

    for tgt in TARGETS:
        ds = pl.load_dataset(tgt)
        w = np.asarray(ds.speeds_k, float) * 1000.0
        irms = np.asarray(ds.irms_arr, float)
        beta = np.asarray(ds.phase_arr, float)
        p = tgt.lower()
        out[p + "_speeds_k"] = np.asarray(ds.speeds_k, float)
        out[p + "_irms"] = irms
        out[p + "_phase"] = beta
        out[p + "_f_ac"] = np.asarray(ds.f_ac_arr, float)
        out[p + "_af_true"] = np.asarray(ds.af_arr, float)
        # 제안 플랜 그대로 적합한 AF (§4.1 4 단계, Table 1 의 예산).
        # 도너의 AF 비를 읽어 오는 screening 과 다르다 --- 변형체가 자체
        # 앵커 표본으로 제 kappa 를 배우고, 저속 (f,p) 만 도너의 손실을
        # 받아 제 하이브리드로 나눈 값에서 얻는다 (§4.3).
        out[p + "_af_own"] = np.asarray(
            models[tgt].predict(w, irms, beta), float)
        e_o = np.abs((out[p + "_af_own"] - out[p + "_af_true"])
                     / out[p + "_af_true"]) * 100.0
        f_o = out[p + "_f_ac"]
        print("\n목표 %s (k_r %.1f), %d 점   제안 플랜 전맵 wMAE %.2f%%"
              % (tgt, K[tgt], len(ds), np.sum(f_o * e_o) / np.sum(f_o)))

        for dnr in K:
            if dnr == tgt:
                continue
            r = (K[tgt] / K[dnr]) ** 2
            af = np.asarray(models[dnr].predict(
                w * r, irms * (K[dnr] / K[tgt]), beta), float)
            out["%s_af_from_%s" % (p, dnr.lower())] = af
            # 도달 구간은 검증 스윕(2~16 k)이 아니라 그 도너가 실제로
            # Full-FEA 를 가진 속도다 (Table 1 예산).  Ref 는 2/4/8/16 k 라
            # 둘이 우연히 같지만, SC 는 8/16 k 뿐이라 크게 다르다.
            own = np.unique(np.round(out[dnr.lower() + "_train_speeds_k"], 3))
            lo, hi = own.min() / r, own.max() / r
            out["%s_reach_%s" % (p, dnr.lower())] = np.array([lo, hi])

            e = np.abs((af - out[p + "_af_true"]) / out[p + "_af_true"]) * 100
            f = out[p + "_f_ac"]
            print("  from %-7s r=%.4f  도달 %.2f~%.2f kRPM" % (dnr, r, lo, hi))
            for spd in sorted(set(np.round(ds.speeds_k, 3))):
                m = np.abs(ds.speeds_k - spd) < 0.1
                inb = lo - 1e-6 <= spd <= hi + 1e-6
                print("     %5gk  wMAE %7.2f%%   %s"
                      % (spd, np.sum(f[m] * e[m]) / np.sum(f[m]),
                         "대역 내" if inb else "외삽"))

    # 혼합 screening --- 속도마다 도달 안쪽 도너를 쓰고, 둘 다 밖이면 나은
    # 쪽을 쓴다.  HalfSC 의 라인업 주장(자체 해석 0 회)이 이 조합이다.
    for tgt, donors in (("HalfSC", ("Ref", "SC")), ("SC", ("Ref", "HalfSC"))):
        p = tgt.lower()
        t, f, s = out[p + "_af_true"], out[p + "_f_ac"], out[p + "_speeds_k"]
        mix = np.empty_like(t)
        who = []
        for spd in sorted(set(np.round(s, 3))):
            m = np.abs(s - spd) < 0.1
            best, bd = None, None
            for d in donors:
                q = d.lower()
                lo, hi = out["%s_reach_%s" % (p, q)]
                af = out["%s_af_from_%s" % (p, q)]
                e = np.sum(f[m] * np.abs((af[m] - t[m]) / t[m])) / np.sum(f[m])
                # 도달 안쪽을 우선하고, 동률이면 오차가 작은 쪽
                key = (0 if lo - 1e-6 <= spd <= hi + 1e-6 else 1, e)
                if best is None or key < best:
                    best, bd = key, q
            mix[m] = out["%s_af_from_%s" % (p, bd)][m]
            who.append(bd)
        out[p + "_af_mixed"] = mix
        out[p + "_mixed_donor"] = np.array(who)
        e = np.abs((mix - t) / t) * 100.0
        print("%s 혼합 screening %s  전맵 wMAE %.2f%%"
              % (tgt, "/".join(who), np.sum(f * e) / np.sum(f)))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez(OUT, **out)
    print("\n저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
