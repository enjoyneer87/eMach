# -*- coding: utf-8 -*-
"""보정 효율맵을 Motor-CAD LAB 없이 자체 연산으로 (저자 승인 2026-08-26).

§11 의 LAB custom-loss AF 주입은 채널 결함 셋으로 무효했다 --- speed 단독
파라미터화, 음수 보정 클리핑, LAB 자체 북키핑.  여기서는 LAB 를 계산에서
빼고 다음만 빌린다.

  - 운전 궤적: FullFEA-LAB elecdata 의 (Speed, Id_RMS, Iq_RMS) 격자.
    MTPA/FW 전류맵 결정은 원고 스코프 밖이라 그대로 쓴다
  - 비-AC 손실 북키핑: 같은 mat 의 Total_Loss - Stator_Copper_Loss_AC.
    세 효율맵이 공유하므로 AC 손실 모델만 갈린다

AC 손실 셋은 전부 원시 스윕(120점)에서 자체 평가한다.

  hybrid      h(w,I,b)   3-D log-손실 보간
  truth       t(w,I,b)   3-D log-손실 보간 (Full-FEA)
  calibrated  c(w,I,b) = h(w,I,b) * AF_model(w,I,b)   (제안 27점 모델)

log-손실을 보간하는 이유 --- f_ac ~ f^2*AF 는 log w 에 대해 볼록해 값의
선형 보간이 과대평가한다 (첫 실행 실측: truth 가 LAB 대비 중앙 +14%).
log 손실은 순수 f^2 에서 정확히 선형이다.  하이브리드도 커널이 xi 와 함께
전이하므로 f^2 가정을 쓰지 않는다 (첫 실행 실측: 편차 최대 50%).

효율은 eta_X = Shaft / (Shaft + other + CuAC_X), other 에 CuDC 포함.
재계산 eta 가 LAB Efficiency 필드(%)와 일치하는지가 북키핑 검증이다.

  python run_effmap_offline.py
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import numpy as np                                       # noqa: E402
from scipy.io import loadmat                             # noqa: E402
from scipy.interpolate import (LinearNDInterpolator,     # noqa: E402
                               NearestNDInterpolator)

EFFDIR = r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10\effmaps"
SC_JSON = os.path.join(HERE, "map_exports", "e10", "SC",
                       "JEET_ACLoss_SC_Map_Summary.json")
OUT = os.path.join(HERE, "map_exports", "e10", "effmaps",
                   "effmap_offline_SC.json")
W0 = 16000.0


def loss_interpolants():
    rec = json.load(open(SC_JSON, encoding="utf-8"))["records"]
    hyb = {(r["speed"], r["current"], r["phase"]): r["hybrid_total_kW"] * 1e3
           for r in rec if r["mode"] == "Hybrid"}
    fea = {(r["speed"], r["current"], r["phase"]): r["fea_total_ac_kW"] * 1e3
           for r in rec if r["mode"] == "FullFEA"}
    keys = sorted(set(hyb) & set(fea))
    assert len(keys) == 120, len(keys)
    pts = np.array([[np.log(s), c, p] for (s, c, p) in keys])

    def make(vals):
        lv = np.log(np.maximum(np.asarray(vals, float), 1e-9))
        lin = LinearNDInterpolator(pts, lv)
        nn = NearestNDInterpolator(pts, lv)

        def f(w, I, b):
            q = np.column_stack([np.log(np.clip(np.ravel(w), 2000.0, W0)),
                                 np.clip(np.ravel(I), 0.1, 920.0),
                                 np.clip(np.ravel(b), 0.0, 90.0)])
            v = lin(q)
            v = np.where(np.isnan(v), nn(q), v)
            return np.exp(v).reshape(np.shape(w))
        return f

    return make([hyb[k] for k in keys]), make([fea[k] for k in keys])


def main() -> int:
    F = loadmat(os.path.join(EFFDIR, "MotorLAB_elecdata_SC_fullfea.mat"))
    spd = np.asarray(F["Speed"], float)
    shaft_kW = np.asarray(F["Shaft_Power"], float)
    id_r = np.asarray(F["Id_RMS"], float)
    iq_r = np.asarray(F["Iq_RMS"], float)
    cuac_F = np.asarray(F["Stator_Copper_Loss_AC"], float)
    total = np.asarray(F["Total_Loss"], float)
    eta_lab = np.asarray(F["Efficiency"], float)
    eta_lab = eta_lab / 100.0 if np.nanmax(eta_lab) > 1.5 else eta_lab

    Irms = np.hypot(id_r, iq_r)
    beta = np.degrees(np.arctan2(-id_r, np.maximum(iq_r, 1e-9)))
    print("맵 격자 %s  I_rms %.0f~%.0f A  beta %.1f~%.1f deg"
          % (spd.shape, np.nanmin(Irms), np.nanmax(Irms),
             np.nanmin(beta), np.nanmax(beta)))

    h_itp, t_itp = loss_interpolants()

    m = (spd > 1e-6) & (shaft_kW > 1e-6) & np.isfinite(eta_lab) \
        & (eta_lab > 0)
    w = np.where(m, spd, W0)
    Ic, bc = np.clip(Irms, 0.1, 920.0), np.clip(beta, 0.0, 90.0)

    # 2 kRPM 아래는 2k 값의 f^2 축소판 --- 저속은 저항 지배라 f^2 가
    # 성립하고 와트 자체가 작다
    scale_low = np.where(w < 2000.0, (w / 2000.0) ** 2, 1.0)
    h = h_itp(w, Ic, bc) * scale_low
    t = t_itp(w, Ic, bc) * scale_low

    with contextlib.redirect_stdout(io.StringIO()):
        from jeet_acloss_rbf.pipeline import AcLossPipeline
        model = AcLossPipeline().build_model("SC")
    af_m = np.asarray(model.predict(
        np.clip(w, 2000.0, W0).ravel(), Ic.ravel(), bc.ravel()),
        float).reshape(w.shape)
    c = h * af_m

    other = total - cuac_F                     # 비-AC 손실 (공유 북키핑)

    def eta(cuac):
        return shaft_kW / (shaft_kW + (other + cuac) / 1e3)

    eta_F = np.where(m, eta(t), np.nan)
    eta_H = np.where(m, eta(h), np.nan)
    eta_C = np.where(m, eta(c), np.nan)

    # 검증 1 --- LAB 자신의 CuAC 로 재계산한 eta 대 LAB Efficiency
    eta_chk = np.where(m, eta(cuac_F), np.nan)
    print("북키핑 검증 |Δeta| max %.4f %%p"
          % (100.0 * np.nanmax(np.abs(eta_chk - eta_lab))))
    # 검증 2 --- 자체 truth 대 LAB CuAC (같은 스윕 원천이니 근접해야 한다)
    sel = m & (cuac_F > 10)
    r = t[sel] / cuac_F[sel]
    print("자체 truth / LAB-CuAC  중앙 %.3f  p5 %.3f  p95 %.3f"
          % (np.median(r), np.percentile(r, 5), np.percentile(r, 95)))

    dH = (eta_H - eta_F) * 100.0
    dC = (eta_C - eta_F) * 100.0
    res = {}
    for tag, d in (("uncalibrated", dH), ("calibrated", dC)):
        res[tag] = {
            "mean_abs_pp": float(np.nanmean(np.abs(d))),
            "mean_signed_pp": float(np.nanmean(d)),
            "p95_abs_pp": float(np.nanpercentile(np.abs(d), 95)),
            "max_abs_pp": float(np.nanmax(np.abs(d))),
        }
        print("%-12s mean|d| %.3f  signed %+.3f  p95 %.3f  max %.3f  [%%p]"
              % (tag, res[tag]["mean_abs_pp"], res[tag]["mean_signed_pp"],
                 res[tag]["p95_abs_pp"], res[tag]["max_abs_pp"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"meta": {"grid": list(spd.shape), "n_valid": int(m.sum()),
                        "trajectory": "FullFEA-LAB elecdata",
                        "bookkeeping": "Total_Loss - CuAC (shared)",
                        "interp": "3-D linear on log-loss over 120 pts"},
               "delta_eta": res}, open(OUT, "w"), indent=1)
    np.savez(OUT.replace(".json", ".npz"), spd=spd, shaft_kW=shaft_kW,
             mask=m, eta_F=eta_F, eta_H=eta_H, eta_C=eta_C, dH=dH, dC=dC,
             Irms=Irms, beta=beta, af_m=af_m, torque=np.asarray(
                 F["Shaft_Torque"], float))
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
