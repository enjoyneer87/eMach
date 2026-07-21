# -*- coding: utf-8 -*-
"""
compare_effmap_vs_lab.py  -- paper2 Phase A, task A2
====================================================
map-based 효율맵(run_efficiency_map.py 출력)을 Motor-CAD Lab 효율맵
(effmaps/MotorLAB_elecdata_{Ref,SC_fullfea})과 대조한다.

정직한 채널 분리:
  - Cu_DC, Cu_AC(=AF 보정 대상)는 map-based가 재현해야 하는 핵심 채널.
  - Iron_Loss는 e10_SatuMap이 단일조건 값이라 속도 스케일링이 없다
    (paper2 Phase C 과제). 따라서 효율을 두 가지로 보고:
      * eta_raw : map-based 자체 철손(과소) 사용 -> 고속 과대평가 노출
      * eta_iso : 철손을 Lab에서 취해 동손/AF 충실도만 격리
  - 핵심 검증 = Cu_AC parity (map vs Lab full-FEA).

출력:
  map_exports/e10/paper2_phaseA/effmap_vs_lab_{Ref,SC}.png
  map_exports/e10/paper2_phaseA/PhaseA_effmap_vs_lab_report.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.interpolate import griddata

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
EFF = HERE / "map_exports" / "e10" / "effmaps"
MAP_MAT = HERE / "efficiency_map_results.mat"
OUT_DIR = HERE / "map_exports" / "e10" / "paper2_phaseA"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# model -> (lab elecdata file, index in efficiency_map_results 3rd axis)
COMPARE = {
    "Ref": {"lab": "MotorLAB_elecdata_Ref.mat", "midx": 0},
    "SC":  {"lab": "MotorLAB_elecdata_SC_fullfea.mat", "midx": 2},
}

# 통계에서 제외할 퇴화 영역
SPEED_MIN = 500.0     # RPM
TORQUE_MIN = 20.0     # Nm
ETA_LAB_MIN = 60.0    # % (Lab 실현 영역만)


def load_lab(path: Path) -> dict:
    d = loadmat(str(path))

    def g(k):
        return np.asarray(d[k], float)

    return {
        "speed": g("Speed"),                       # RPM
        "torque": g("Shaft_Torque"),               # Nm
        "eta": g("Efficiency"),                     # %
        "cu_dc": g("Stator_Copper_Loss_DC") / 1e3,  # kW
        "cu_ac": g("Stator_Copper_Loss_AC") / 1e3,  # kW
        "fe": g("Iron_Loss") / 1e3,                # kW
        "irms": g("Stator_Current_Phase_RMS"),     # A
        "phase": g("Phase_Advance"),               # deg (beta)
    }


def interp_lab(lab: dict, key: str, SP: np.ndarray, TQ: np.ndarray) -> np.ndarray:
    pts = np.column_stack([lab["speed"].ravel(), lab["torque"].ravel()])
    val = lab[key].ravel()
    ok = np.isfinite(val)
    return griddata(pts[ok], val[ok], (SP, TQ), method="linear")


def analyse(model: str, cfg: dict, mp: dict) -> dict:
    midx = cfg["midx"]
    speeds = np.squeeze(mp["speed_rpm"]).astype(float)      # (33,)
    torque_axis = np.squeeze(mp["torque_nm"][:, midx]).astype(float)  # (25,)
    eta_map = mp["eta_pct"][:, :, midx]            # (25,33)
    cu_dc_map = mp["loss_cu_dc_kW"][:, :, midx]
    cu_ac_map = mp["loss_cu_ac_kW"][:, :, midx]
    fe_map = mp["loss_fe_kW"][:, :, midx]
    irms_map = mp["i_amp_pk"][:, :, midx] / np.sqrt(2.0)   # A_rms
    beta_map = mp["beta_deg"][:, :, midx]                  # deg

    SP, TQ = np.meshgrid(speeds, torque_axis)      # (25,33)

    lab = load_lab(EFF / cfg["lab"])
    eta_lab = interp_lab(lab, "eta", SP, TQ)
    cu_dc_lab = interp_lab(lab, "cu_dc", SP, TQ)
    cu_ac_lab = interp_lab(lab, "cu_ac", SP, TQ)
    fe_lab = interp_lab(lab, "fe", SP, TQ)
    irms_lab = interp_lab(lab, "irms", SP, TQ)
    beta_lab = interp_lab(lab, "phase", SP, TQ)

    # 격리 효율: 철손을 Lab에서 취함
    p_mech = TQ * (SP * 2 * np.pi / 60.0) / 1e3    # kW
    denom = p_mech + cu_dc_map + cu_ac_map + fe_lab
    eta_iso = np.where(denom > 0, p_mech / denom * 100.0, np.nan)

    valid = (
        np.isfinite(eta_map) & np.isfinite(eta_lab)
        & (SP >= SPEED_MIN) & (TQ >= TORQUE_MIN)
        & (eta_lab >= ETA_LAB_MIN)
        & np.isfinite(cu_ac_lab) & np.isfinite(fe_lab)
        & np.isfinite(irms_lab) & np.isfinite(beta_lab)
    )

    def stat(a, b):
        d = (a - b)[valid]
        d = d[np.isfinite(d)]
        return {
            "mean": float(np.mean(d)), "std": float(np.std(d)),
            "mae": float(np.mean(np.abs(d))), "max": float(np.max(np.abs(d))),
        }

    res = {
        "model": model, "n_valid": int(valid.sum()),
        "eta_raw": stat(eta_map, eta_lab),
        "eta_iso": stat(eta_iso, eta_lab),
        "irms": stat(irms_map, irms_lab),
        "beta": stat(beta_map, beta_lab),
        "cu_dc": stat(cu_dc_map, cu_dc_lab),
        "cu_ac": stat(cu_ac_map, cu_ac_lab),
        "fe": stat(fe_map, fe_lab),
        # arrays for plotting
        "_SP": SP, "_TQ": TQ, "_valid": valid,
        "_eta_map": eta_map, "_eta_lab": eta_lab, "_eta_iso": eta_iso,
        "_irms_map": irms_map, "_irms_lab": irms_lab,
        "_cu_ac_map": cu_ac_map, "_cu_ac_lab": cu_ac_lab,
        "_fe_map": fe_map, "_fe_lab": fe_lab,
        "_speeds": speeds, "_torque": torque_axis,
    }
    return res


def make_figure(res: dict, out_path: Path) -> None:
    plt.rcParams.update({"font.size": 8, "figure.dpi": 130})
    SP, TQ, valid = res["_SP"], res["_TQ"], res["_valid"]
    model = res["model"]

    fig, ax = plt.subplots(2, 3, figsize=(12.5, 7.0))
    fig.suptitle(f"map-based efficiency map vs Motor-CAD Lab  --  {model}",
                 fontsize=11, fontweight="bold")

    def contour(a, Z, title, cmap, lv=None, unit=""):
        Zm = np.where(valid, Z, np.nan)
        cs = a.contourf(SP / 1000.0, TQ, Zm, levels=lv if lv is not None else 14,
                        cmap=cmap)
        fig.colorbar(cs, ax=a, shrink=0.9, label=unit)
        a.set_title(title, fontsize=9)
        a.set_xlabel("Speed [kRPM]")
        a.set_ylabel("Torque [Nm]")

    # Row 0: efficiency
    lv_e = np.linspace(85, 99, 15)
    contour(ax[0, 0], res["_eta_lab"], "Lab efficiency", "viridis", lv_e, "%")
    contour(ax[0, 1], res["_eta_iso"],
            "map-based eff. (iron from Lab, iso)", "viridis", lv_e, "%")
    d_iso = res["_eta_iso"] - res["_eta_lab"]
    contour(ax[0, 2], d_iso, "Δη (iso - Lab)", "RdBu_r",
            np.linspace(-2, 2, 17), "%")

    # Row 1: operating-point + loss-channel parity
    def parity(a, key_lab, key_map, color, title, xl, yl, x0=True):
        x = res[key_lab][valid]
        y = res[key_map][valid]
        m = np.isfinite(x) & np.isfinite(y)
        a.scatter(x[m], y[m], s=10, alpha=0.5, c=color)
        hi = max(np.nanmax(x[m]), np.nanmax(y[m])) * 1.05 + 1e-6
        lo = 0 if x0 else min(np.nanmin(x[m]), np.nanmin(y[m]))
        a.plot([lo, hi], [lo, hi], "k--", lw=0.8)
        a.set_xlim(lo, hi)
        a.set_ylim(lo, hi)
        a.set_title(title, fontsize=9)
        a.set_xlabel(xl)
        a.set_ylabel(yl)

    # I_rms parity: tests torque-per-amp (flux/torque model) consistency
    parity(ax[1, 0], "_irms_lab", "_irms_map", "#6a1b9a",
           f"I_rms parity (torque-per-amp)\nmean Δ {res['irms']['mean']:+.1f} A",
           "Lab I_rms [A]", "map-based I_rms [A]")
    # Cu_AC parity (the calibration target)
    parity(ax[1, 1], "_cu_ac_lab", "_cu_ac_map", "#e65100",
           f"Cu_AC parity (AF calibrated)\nMAE {res['cu_ac']['mae']:.2f} kW",
           "Lab AC copper [kW]", "map-based AC copper [kW]")
    # Fe parity (the known Phase-C gap)
    parity(ax[1, 2], "_fe_lab", "_fe_map", "#2c6fad",
           "Iron-loss parity (Phase C gap)\nmap single-condition, no speed scale",
           "Lab iron loss [kW]", "map-based iron loss [kW]")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path)
    plt.close(fig)


def main() -> None:
    mp = loadmat(str(MAP_MAT))
    results = []
    for model, cfg in COMPARE.items():
        res = analyse(model, cfg, mp)
        results.append(res)
        make_figure(res, OUT_DIR / f"effmap_vs_lab_{model}.png")
        print(f"\n=== {model}  (n_valid={res['n_valid']}) ===")
        for ch in ("eta_raw", "eta_iso", "irms", "beta", "cu_dc", "cu_ac", "fe"):
            s = res[ch]
            print(f"  {ch:8s}  mean={s['mean']:+8.3f}  MAE={s['mae']:8.3f}  "
                  f"max={s['max']:8.3f}")

    # markdown report
    lines = [
        "# Phase A -- map-based 효율맵 vs Motor-CAD Lab (task A2)", "",
        "map-based 효율맵(run_efficiency_map.py, 멱지수 AF + SCL-M k_r)을 "
        "Lab 효율맵과 대조. Δ = map - Lab.", "",
        "**철손 주의**: e10_SatuMap의 Iron_Loss는 단일조건 값(속도 스케일링 "
        "없음) -> `eta_raw`(자체 철손)는 고속 과대평가. `eta_iso`(철손을 Lab에서 "
        "취함)가 동손/AF 충실도의 정직한 지표. Cu_AC parity가 핵심 검증.", "",
    ]
    for res in results:
        lines.append(f"## {res['model']}  (유효 {res['n_valid']}점)")
        lines.append("")
        lines.append("| 채널 | mean Δ | MAE | max|Δ| |")
        lines.append("|---|---|---|---|")
        u = {"eta_raw": "%", "eta_iso": "%", "irms": "A", "beta": "deg",
             "cu_dc": "kW", "cu_ac": "kW", "fe": "kW"}
        nm = {"eta_raw": "η (raw, map 철손)", "eta_iso": "η (iso, Lab 철손)",
              "irms": "**I_rms (토크당전류)**", "beta": "β 위상각",
              "cu_dc": "Cu_DC", "cu_ac": "**Cu_AC (AF 보정)**", "fe": "Iron (gap)"}
        for ch in ("eta_raw", "eta_iso", "irms", "beta",
                   "cu_dc", "cu_ac", "fe"):
            s = res[ch]
            lines.append(f"| {nm[ch]} | {s['mean']:+.3f} {u[ch]} | "
                         f"{s['mae']:.3f} {u[ch]} | {s['max']:.3f} {u[ch]} |")
        lines.append("")
    lines += [
        "## 해석 (Phase B/C 진입점)", "",
        "### 검증된 부분 (map-based 방법의 유효 영역)",
        "- **온도 정합**: Lab 권선 80°C. R_dc 20→80°C(×1.236) 보정 후 Ref Cu_DC "
        "잔차 -2.24→-0.56 kW, eta_iso +2.14→+0.78%. 잔여분이 운전점/λ 기여.",
        "- **I_rms parity(토크당전류)**: Ref는 대각선 밀착(mean Δ -4.5 A) -> "
        "SatuMap λ_d/λ_q + MTPA/FW EEC 솔버가 Lab 운전점을 잘 재현. DC동손·토크는 "
        "정합. **정상상태 EEC 솔버 자체는 유효**함을 확인.",
        "- **효율맵(iso)**: 철손을 Lab에서 취하면 Ref 효율맵이 Lab과 시각적으로 "
        "일치(MAE 1.29%).",
        "",
        "### 구조적 결함 (Phase C가 반드시 해결)",
        "- **AC 동손이 map≈0**: 효율맵의 AC 동손 base는 e10_SatuMap의 "
        "Stator_Copper_Loss_AC(단일조건, Ref 기준 ~26W)를 k_a/k_r²로 스케일한 값. "
        "AF(TS/Hybrid 비, ~1-3)만 곱하므로 **주파수 스케일링(∝f²)과 SC 후막도체 "
        "근접효과의 절대크기가 빠진다**. 결과: Lab AC동손 최대 60 kW(SC) vs map ~0. "
        "논문1은 손실 레벨(h_ac,f_ac 물리값)에서 AF를 검증했지만, 효율맵 파이프라인은 "
        "Ref-SatuMap의 작은 값을 base로 써서 크기를 잃음.",
        "  - **처방**: 속도분해 hybrid AC 맵(모델별 물리 hybrid) × AF 로 재구성. "
        "AF는 비율, base는 반드시 해당 (속도,모델)의 물리 hybrid.",
        "- **철손도 동일**: 단일조건 Iron_Loss → 속도스케일링 부재. map≈0 vs Lab "
        "최대 16 kW(SC). 에디/히스테리시스 분리 속도맵 또는 Lab 철손 LUT 필요.",
        "- 두 채널 모두 **주파수 의존 손실의 base가 단일조건 SatuMap이라는 한 원인**. "
        "Phase C = 속도분해 손실맵 구축 (AC copper + iron).",
        "",
        "### Phase 매핑",
        "- Phase B: 가역성 잔차(B1 결과) + I_rms/β 편차 -> 자속맵 가역성 강제·충실화 "
        "(효과는 Ref 수준에서 이미 작음 → 우선순위 낮음, 정합성 보증용).",
        "- **Phase C(우선)**: 속도분해 AC동손·철손 맵 + 온도모델. 이게 효율맵 정확도의 "
        "지배 요인. 완료 시 SC eta_iso +3.86%의 대부분 해소 예상.",
        "",
    ]
    rep = OUT_DIR / "PhaseA_effmap_vs_lab_report.md"
    rep.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n리포트: {rep}")
    print(f"그림:   {OUT_DIR}\\effmap_vs_lab_{{Ref,SC}}.png")


if __name__ == "__main__":
    main()
