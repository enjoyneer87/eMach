# -*- coding: utf-8 -*-
"""§5.4 궤적 수준 AF 검증 — Lab 효율맵 쌍(Hybrid vs FullFEA)과 보정 모델 대조.

본문 §5.4의 세 주장을 데이터로 산출·아카이브한다 (2026-07-30 수치 감사에서
'산출물 미보관(UNVERIFIABLE)' 1순위로 지적된 corr 0.99·AF 프로파일·궤적 오차):
  (1) 궤적상 AF 프로파일: 저속 MTPA ~1.7 -> 심층 약자속 회랑 0.94--1.05 감쇠
  (2) 두 맵의 AC 손실비 F/H 가 보정 모델 AF 프로파일을 상관 ~0.99로 추적
  (3) 궤적상 보정 AC 손실 오차(AF x P_hyb vs P_FullFEA) < 1%

궤적 = 효율맵 전부하 포락선(속도별 유효 최대 토크 행). 참고로 전 맵(유효 셀
전체) 상관도 병기한다. 입력 elecdata 는 run_lab30_effmaps.py 산출(구본과 동일
파일명) — 스크립트는 격자 정의에 무관하게 동작한다.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                     # noqa: E402
from scipy.io import loadmat                           # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline    # noqa: E402

EFF = os.path.join(HERE, "map_exports", "e10", "effmaps")
OUT = os.path.join(HERE, "map_exports", "e10", "SC",
                   "effmap_traj_af_check.json")


def main() -> int:
    H = loadmat(os.path.join(EFF, "MotorLAB_elecdata_SC_hyb.mat"))
    F = loadmat(os.path.join(EFF, "MotorLAB_elecdata_SC_fullfea.mat"))

    spd = np.asarray(F["Speed"], float)
    trq = np.asarray(F["Shaft_Torque"], float)
    cuH = np.asarray(H["Stator_Copper_Loss_AC"], float)
    cuF = np.asarray(F["Stator_Copper_Loss_AC"], float)
    irms = np.asarray(F["Stator_Current_Line_RMS"], float)
    beta = np.asarray(F["Phase_Advance"], float)
    eta_h = np.asarray(H["Efficiency"], float)
    eta_f = np.asarray(F["Efficiency"], float)

    pl = AcLossPipeline()
    model = pl.build_model("SC")

    valid = (np.isfinite(cuH) & np.isfinite(cuF) & (cuH > 1.0)
             & (cuF > 1.0) & np.isfinite(irms) & (irms > 1.0)
             & (spd > 100.0))

    # ── 전부하 포락선(궤적): 각 속도 열에서 유효 최대 토크 셀 ──────────
    # Speed 배열의 축 방향을 자동 판별 (열/행 어느 쪽이 속도 축인지)
    if np.allclose(spd[0, :], spd[0, 0]):          # 열이 등속도
        spd_axis = 0                                # 행 = 속도 변화 축?
    # 속도가 변하는 축 탐지
    ax_var0 = np.nanstd(spd, axis=0).mean()
    ax_var1 = np.nanstd(spd, axis=1).mean()
    spd_axis = 1 if ax_var1 > ax_var0 else 0        # 속도가 변하는 축

    if spd_axis == 0:                               # (speed, torque) 배치로 통일
        pass
    else:
        spd, trq, cuH, cuF, irms, beta = (a.T for a in
                                          (spd, trq, cuH, cuF, irms, beta))
        eta_h, eta_f = eta_h.T, eta_f.T
        valid = valid.T

    n_spd = spd.shape[0]
    env = []                                         # (i_spd, j_trq)
    for i in range(n_spd):
        js = np.where(valid[i])[0]
        if len(js) == 0:
            continue
        j = js[np.nanargmax(trq[i, js])]
        env.append((i, j))
    env = np.array(env)

    def gather(a):
        return np.array([a[i, j] for i, j in env])

    s_e, t_e = gather(spd), gather(trq)
    h_e, f_e = gather(cuH), gather(cuF)
    ir_e, be_e = gather(irms), gather(beta)

    af_pred_e = model.predict(s_e, ir_e, be_e)
    ratio_e = f_e / h_e

    # (1) AF 프로파일
    lo = s_e <= 4000
    fw = s_e >= 10000
    prof = {
        "af_pred_lowspeed_max": float(np.nanmax(af_pred_e[lo])),
        "af_pred_fw_range": [float(np.nanmin(af_pred_e[fw])),
                             float(np.nanmax(af_pred_e[fw]))],
        "ratio_lab_lowspeed_max": float(np.nanmax(ratio_e[lo])),
        "ratio_lab_fw_range": [float(np.nanmin(ratio_e[fw])),
                               float(np.nanmax(ratio_e[fw]))],
    }

    # (2) 상관: 궤적 + 전 맵
    corr_traj = float(np.corrcoef(ratio_e, af_pred_e)[0, 1])
    vi, vj = np.where(valid)
    af_all = model.predict(spd[vi, vj], irms[vi, vj], beta[vi, vj])
    corr_map = float(np.corrcoef(cuF[vi, vj] / cuH[vi, vj], af_all)[0, 1])

    # (3) 궤적상 보정 AC 손실 오차 (와트 가중)
    err = np.abs(af_pred_e * h_e - f_e) / f_e * 100.0
    traj_wmae = float(np.sum(f_e * err) / np.sum(f_e))
    traj_mae = float(np.mean(err))

    # (3b) 파이프라인 세계의 궤적 오차: 보정 하이브리드 vs TS-FEA.
    # AF의 보정 분모는 E-Magnetic 하이브리드이므로 Lab 내부 하이브리드에 곱한
    # (3)은 분모 상대성 위반의 진단치일 뿐이다(§11 Lab 주입 부정적 결과와 동근).
    # 검증 스윕이 존재하는 속도(2/4/8/16k)에서 포락선 운전점의 TS 진리값을
    # (Irms, beta) 박판 스플라인으로 보간해 보정 예측과 대조한다.
    ds = pl.load_dataset("SC")
    traj_pipe = {}
    errs_pipe = []
    for spd_k in sorted(set(np.round(ds.speeds_k, 3))):
        sel = np.abs(ds.speeds_k - spd_k) < 1e-6
        if sel.sum() < 6:
            continue
        s_rpm = spd_k * 1000.0
        i_env = int(np.argmin(np.abs(s_e - s_rpm)))
        if abs(s_e[i_env] - s_rpm) > 260.0:
            continue
        ir0, be0 = ir_e[i_env], be_e[i_env]
        from scipy.interpolate import RBFInterpolator
        pts = np.column_stack([ds.irms_arr[sel] / 920.0,
                               ds.phase_arr[sel] / 90.0])
        q = np.array([[ir0 / 920.0, be0 / 90.0]])
        p_ts = float(RBFInterpolator(
            pts, ds.f_ac_arr[sel], kernel="thin_plate_spline")(q)[0])
        p_hy = float(RBFInterpolator(
            pts, ds.h_ac_arr[sel], kernel="thin_plate_spline")(q)[0])
        p_cal = p_hy * float(model.predict(
            np.array([s_rpm]), np.array([ir0]), np.array([be0]))[0])
        e = abs(p_cal - p_ts) / p_ts * 100.0
        errs_pipe.append((e, p_ts))
        traj_pipe[f"{spd_k:g}k"] = {
            "irms": round(float(ir0), 1), "beta": round(float(be0), 1),
            "p_ts": round(p_ts, 2), "p_cal": round(p_cal, 2),
            "err_pct": round(e, 2)}

    # 참고: 궤적상 효율 편차 (무보정 하이브리드 vs FullFEA)
    deta_e = gather(eta_h) - gather(eta_f)

    out = {
        "n_envelope": int(len(env)),
        "n_valid_cells": int(valid.sum()),
        "profile": prof,
        "corr_trajectory_ratio_vs_af": round(corr_traj, 4),
        "corr_fullmap_ratio_vs_af": round(corr_map, 4),
        "traj_lab_denominator_diag_wmae_pct": round(traj_wmae, 3),
        "traj_lab_denominator_diag_mae_pct": round(traj_mae, 3),
        "traj_pipeline_vs_ts": traj_pipe,
        "traj_pipeline_err_max_pct": (round(max(e for e, _ in errs_pipe), 2)
                                      if errs_pipe else None),
        "traj_pipeline_wmae_pct": (round(
            sum(e * w for e, w in errs_pipe)
            / sum(w for _, w in errs_pipe), 2) if errs_pipe else None),
        "traj_deta_uncorrected_mean_abs_pp": round(
            float(np.nanmean(np.abs(deta_e))), 3),
        "fullmap_deta_mean_abs_pp": round(
            float(np.nanmean(np.abs(eta_h - eta_f)[valid])), 3),
    }
    print(json.dumps(out, indent=1, ensure_ascii=False))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
