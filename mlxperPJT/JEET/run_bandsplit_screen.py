# -*- coding: utf-8 -*-
r"""PWM 대역분할 0단계 선별 --- 신규 시뮬레이션 없이 가설 H1/H2 를 거른다.

paper2/PWM_BANDSPLIT_PLAN.md 의 3절.  정현파 조화 꼬리(홀수 n=9~23,
16k 기본파 1.067 kHz -> 9.6~24.5 kHz)는 캐리어 대역과 같은 주파수를 이미
덮는다.  §12.4 의 조화별 AF 실측(ts_harmonic_af.json)에 캡 분모를 적용해

  H1  AF_cap,n = af_n · max(1, f_n/f_t)  가 홀수 꼬리에서 평탄한가
  H2  그 수준이 Ref 와 SC 에서 어떻게 스케일되는가 (k_r 의존)

를 본다.  f_t = 1/(π μ0 σ h²), 80°C σ=4.694e7, h = 도체 반경 치수
(Ref 1.686 / SC 3.372 mm) -> f_t = 1898 / 475 Hz (§12.28 실측과 일치).

짝수 n 은 분모(MS 필드)가 대칭상 0이라 잡음 --- 제외.

실행:  python run_bandsplit_screen.py
산출:  map_exports/e10/checks/bandsplit_screen.json
"""
from __future__ import annotations

import io
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "map_exports", "e10", "checks",
                   "ts_harmonic_af.json")
OUT = os.path.join(HERE, "map_exports", "e10", "checks",
                   "bandsplit_screen.json")

MU0 = 4e-7 * np.pi
SIGMA_80C = 4.694e7
H_RAD = {"Ref": 1.686e-3, "SC": 3.372e-3}
POLE_PAIRS = 4


def f_t(model):
    return 1.0 / (np.pi * MU0 * SIGMA_80C * H_RAD[model] ** 2)


def main() -> int:
    d = json.load(io.open(SRC, encoding="utf-8"))
    out = {"f_t_Hz": {m: round(f_t(m), 1) for m in H_RAD}}
    print("f_t [Hz]:", out["f_t_Hz"])

    for key in ("Ref_16k", "SC_16k", "Ref_8k", "SC_8k"):
        model, spd = key.split("_")
        f1 = float(spd[:-1]) * 1000 * POLE_PAIRS / 60.0
        g = d[key]
        n = np.array(g["n"], int)
        af = np.array(g["af_n"], float)
        pts = np.array(g["p_ts_Wpm"], float)
        odd = (n % 2 == 1)
        tail = odd & (n >= 9)
        fn = n * f1
        cap = np.maximum(1.0, fn / f_t(model))
        af_cap = af * cap

        lo_share = pts[odd & (n <= 7)].sum() / pts.sum()
        r = {
            "f1_Hz": round(f1, 1),
            "tail_n": [int(x) for x in n[tail]],
            "af_raw_tail": [round(float(x), 2) for x in af[tail]],
            "af_cap_tail": [round(float(x), 2) for x in af_cap[tail]],
            "cap_factor_tail": [round(float(x), 2) for x in cap[tail]],
            "tail_watt_share_pct": round(
                float(100 * pts[tail].sum() / pts.sum()), 2),
            "low_band_watt_share_pct": round(float(100 * lo_share), 2),
            # 평탄도: 와트 가중 로그 표준편차 (작을수록 상수에 가깝다)
            "flatness_raw_logstd": round(float(np.std(
                np.log(af[tail]))), 3),
            "flatness_cap_logstd": round(float(np.std(
                np.log(af_cap[tail]))), 3),
            "af_cap_tail_wmean": round(float(
                np.sum(pts[tail] * af_cap[tail]) / pts[tail].sum()), 3),
        }
        out[key] = r
        print("\n=== %s  (f1 %.0f Hz, 꼬리 와트 %.1f%%)" %
              (key, f1, r["tail_watt_share_pct"]))
        print("  n        :", r["tail_n"])
        print("  AF 원래  :", r["af_raw_tail"])
        print("  AF 캡분모:", r["af_cap_tail"])
        print("  평탄도 logstd  원래 %.3f -> 캡 %.3f   캡 가중평균 %.3f"
              % (r["flatness_raw_logstd"], r["flatness_cap_logstd"],
                 r["af_cap_tail_wmean"]))

    # H2: 같은 물리 주파수에서 Ref vs SC 의 캡 AF 수준 비교
    print("\n=== H2: 16k 캡 AF 가중평균  Ref %.3f  vs  SC %.3f  (비 %.2f)"
          % (out["Ref_16k"]["af_cap_tail_wmean"],
             out["SC_16k"]["af_cap_tail_wmean"],
             out["SC_16k"]["af_cap_tail_wmean"]
             / out["Ref_16k"]["af_cap_tail_wmean"]))

    io.open(OUT, "w", encoding="utf-8").write(
        json.dumps(out, indent=1, ensure_ascii=False))
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
