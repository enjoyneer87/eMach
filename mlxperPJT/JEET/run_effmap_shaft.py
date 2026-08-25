# -*- coding: utf-8 -*-
"""축 토크 기준 자체 효율맵 --- ShaftMapSolver 검증 러너 (2026-08-26).

자속: 원고의 30점 포화맵 중 scaledS (Ref 를 SCL-M 으로 스케일한 SC 맵).
      변형체가 자체 포화 스윕 없이 배포되는 원고 경로 그대로다.
AC 동손: 원시 스윕 log-손실 보간 (truth / hybrid) + AF 모델 (calibrated).
철손·자석손·기계손: FullFEA-LAB elecdata 를 (속도, 축토크) 로 보간해 셋이
      공유 --- 자체 모델이 없는 채널이라 정직하게 빌려 온다.

검증 순서
  1) truth 모델 궤적 vs LAB Id/Iq  (전류벡터 편차)
  2) 재계산 eta_truth vs LAB Efficiency
  3) hybrid / calibrated 각자 자기 궤적으로 풀어 Δη --- 축 토크 재산정을
     반영한 최종 수치

  python run_effmap_shaft.py            # 성긴 격자 (속도 1/4)
  python run_effmap_shaft.py --full
"""
import argparse
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

import numpy as np                                        # noqa: E402
from scipy.io import loadmat                              # noqa: E402

from tools.motor_scaling import (ShaftMapSolver,          # noqa: E402
                                 polar_flux_tables, LabElecdata)
from run_effmap_offline import loss_interpolants, EFFDIR   # noqa: E402

FLUX_MAT = os.path.join(HERE, "map_exports", "e10",
                        "lab_scaling_comparison_e10.mat")
OUT = os.path.join(HERE, "map_exports", "e10", "effmaps",
                   "effmap_shaft_SC.npz")
POLE_PAIRS = 4
V_MAX = 720.0 / np.sqrt(3.0)
I_MAX_PK = 920.0 * np.sqrt(2.0)
R_DC20_REF = 0.06378
R_TEMP = 1.0 + 0.00393 * (80.0 - 20.0)
R_DC_SC = R_DC20_REF * R_TEMP / 4.0        # k_a/k_r^2, k_r=2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--n-grid", type=int, default=481)
    a = ap.parse_args()

    M = loadmat(FLUX_MAT, squeeze_me=True, struct_as_record=False)
    s = M["scaledS"]
    fd, fq, is_top = polar_flux_tables(s.Is, s.Gamma, s.PsiD, s.PsiQ)
    print("자속맵 scaledS  Is 최대 %.0f A_pk (i_max %.0f)" % (is_top,
                                                              I_MAX_PK))

    lab = LabElecdata(os.path.join(EFFDIR,
                                   "MotorLAB_elecdata_SC_fullfea.mat"))
    sp_ax = lab.speeds_rpm
    TS = lab.shaft_torque
    eta_lab = lab.efficiency
    cols = np.arange(sp_ax.size) if a.full else np.arange(0, sp_ax.size, 4)
    cols = cols[sp_ax[cols] > 0]
    print("속도 열 %d개 (%s)" % (cols.size, "full" if a.full else "coarse"))

    # DC 저항 --- LAB 실측 (스케일 법칙은 활성부만, end-winding 비 1.29)
    r_lab = lab.r_dc_measured()
    # 스케일값/LAB 비 1.28 = 원고 §5.2 의 end-winding 비 1.29 --- 스케일
    # 법칙은 활성부 저항만 따르므로 효율 북키핑은 LAB 실측 R 을 쓴다.
    print("R_dc: 스케일(활성부) %.5f / LAB(총) %.5f Ohm --- LAB 채택"
          % (R_DC_SC, r_lab))
    r_use = float(r_lab)

    h_itp, t_itp = loss_interpolants()
    with contextlib.redirect_stdout(io.StringIO()):
        from jeet_acloss_rbf.pipeline import AcLossPipeline
        model = AcLossPipeline().build_model("SC")

    def cu_truth(w, I, b):
        return t_itp(w, I, b)

    def cu_hyb(w, I, b):
        return h_itp(w, I, b)

    def cu_cal(w, I, b):
        af = np.asarray(model.predict(np.clip(w, 2000.0, 16000.0), I, b),
                        float)
        return h_itp(w, I, b) * af

    aux = lab.aux_tables()
    res = {}
    for tag, cu in (("truth", cu_truth), ("hybrid", cu_hyb),
                    ("cal", cu_cal)):
        solver = ShaftMapSolver(flux_d=fd, flux_q=fq, r_dc=r_use,
                                pole_pairs=POLE_PAIRS, v_max=V_MAX,
                                i_max_pk=I_MAX_PK, cu_ac=cu, aux=aux,
                                n_grid=a.n_grid)
        res[tag] = solver.solve(sp_ax[cols], TS[:, cols])
        print("%-7s 해결 노드 %d" % (tag,
                                     np.isfinite(res[tag]["eta"]).sum()))

    # 검증 1 --- truth 궤적 vs LAB (peak -> RMS 변환)
    idL_all, iqL_all = lab.idq_pk()
    idL, iqL = idL_all[:, cols], iqL_all[:, cols]
    v = np.isfinite(res["truth"]["eta"]) & np.isfinite(eta_lab[:, cols]) \
        & (TS[:, cols] > 10)
    dI = np.hypot(res["truth"]["id"][v] - idL[v],
                  res["truth"]["iq"][v] - iqL[v])
    IL = np.hypot(idL[v], iqL[v])
    print("궤적 vs LAB  |dI|/|I| 중앙 %.2f%%  p95 %.2f%%"
          % (100 * np.median(dI / IL), 100 * np.percentile(dI / IL, 95)))
    # 검증 2 --- eta
    de = (res["truth"]["eta"][v] - eta_lab[:, cols][v]) * 100
    print("eta_truth vs LAB  mean|d| %.3f  p95 %.3f  [%%p]"
          % (np.mean(np.abs(de)), np.percentile(np.abs(de), 95)))
    # 최종 --- 축 토크 재산정 반영 Δη.  세 모델이 같은 목표를 2% 이내로
    # 달성한 노드만 비교한다.  포락선 경계에서는 모델마다 도달 토크가
    # 달라 효율 차가 토크 차를 되받아 적으므로 비교가 아니다.
    tgt = TS[:, cols]
    common = np.isfinite(res["truth"]["eta"])
    for tag in res:
        common &= np.isfinite(res[tag]["eta"])
        common &= np.abs(res[tag]["t_shaft"] - tgt) <= 0.02 * np.abs(tgt)
    common &= tgt > 10
    print("공통 도달 노드 %d / %d" % (common.sum(),
                                      np.isfinite(tgt).sum()))
    for tag in ("hybrid", "cal"):
        d = (res[tag]["eta"] - res["truth"]["eta"]) * 100
        dv = d[common]
        print("%-7s Δη  mean|d| %.3f  signed %+.3f  p95 %.3f  max %.3f [%%p]"
              % (tag, np.mean(np.abs(dv)), np.mean(dv),
                 np.percentile(np.abs(dv), 95), np.max(np.abs(dv))))

    np.savez(OUT, speeds=sp_ax[cols], targets=TS[:, cols],
             **{"%s_%s" % (t, k): res[t][k] for t in res for k in res[t]})
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
