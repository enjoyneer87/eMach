"""
verify_phase_angle.py
e10 모터 (8P/48S) — 최적 전류위상각(β_opt) 검증 스크립트

목적:
  - RBF 보정 AC손실 반영 상태에서 MtpaFwSolver (Electrical EEC 모델)로
    속도/토크별 β_opt = arctan2(iq_opt, id_opt)*180/π - 90 계산
  - Ref / HalfSC / SC 3개 모델 비교
  - EEC 전압 모델 (철손 병렬전류 + AC 직렬저항) 동작 확인

사용 데이터:
  - SatuMap.mat        : 자속/철손/AC손 LUT
  - AF_RBF_model_*.json: 모델별 RBF 보정계수
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np
from pathlib import Path
from scipy.io import loadmat, savemat

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
EMACH_ROOT = SCRIPT_DIR.parent.parent.resolve()
if str(EMACH_ROOT) not in sys.path:
    sys.path.insert(0, str(EMACH_ROOT))

from tools.motor_scaling import (
    BaseMotorMap,
    EfficiencyMap,
    RbfJsonReader,
    scale_motor_map,
    MtpaFwSolver,
)

# ---------------------------------------------------------------------------
# e10 모터 스펙
# ---------------------------------------------------------------------------
POLE_PAIRS = 4
V_DC = 720.0                        # [V]
I_RMS_MAX = 460.0                   # [A]
V_MAX = V_DC / np.sqrt(3.0)         # 상전압 피크 한계 [V_pk]
I_MAX = I_RMS_MAX * np.sqrt(2.0)    # 전류 피크 한계 [A_pk]

MAP_ROOT = SCRIPT_DIR / "map_exports" / "e10"
SAT_MAP_PATH = EMACH_ROOT / "tools" / "SystemSimulationModel" / "SatuMap.mat"

MODELS = {
    "Ref":    MAP_ROOT / "Ref"    / "AF_RBF_model_Ref.json",
    "HalfSC": MAP_ROOT / "HalfSC" / "AF_RBF_model_HalfSC.json",
    "SC":     MAP_ROOT / "SC"     / "AF_RBF_model_SC.json",
}

# 검증 운전점
SPEEDS_RPM = [2000, 4000, 8000, 12000, 16000]
TORQUES_NM = [100.0, 200.0, 300.0]


# ---------------------------------------------------------------------------
def load_base_map() -> BaseMotorMap:
    sat = loadmat(str(SAT_MAP_PATH))
    return BaseMotorMap(
        id_grid=np.squeeze(sat["Id_Peak"]),
        iq_grid=np.squeeze(sat["Iq_Peak"]),
        lambda_d=np.squeeze(sat["Flux_Linkage_D"]),
        lambda_q=np.squeeze(sat["Flux_Linkage_Q"]),
        r_dc=float(np.squeeze(sat["Phase_Resistance_DC_at_20C"])),
        p_fe_grid=np.squeeze(sat["Iron_Loss"]) / 1000.0,
        p_cu_ac_hybrid=np.squeeze(sat["Stator_Copper_Loss_AC"]) / 1000.0,
        pole_pairs=POLE_PAIRS,
    )


def phase_deg_from(id_opt: float, iq_opt: float) -> float:
    """β = arctan2(iq, id)*180/π - 90  [deg]"""
    return float(np.degrees(np.arctan2(iq_opt, id_opt)) - 90.0)


# ---------------------------------------------------------------------------
def check_efficiency_map_phase_property() -> bool:
    """EfficiencyMap.phase_deg 프로퍼티 존재 여부 확인 (Task 1-B 선행 체크)."""
    has_prop = hasattr(EfficiencyMap, "phase_deg")
    status = "[OK]     " if has_prop else "[MISSING]"
    print(f"  {status} EfficiencyMap.phase_deg: {'found' if has_prop else 'not implemented'}")
    if not has_prop:
        print("           → Task 1-B: tools/motor_scaling/model/EfficiencyMap.py 에 추가:")
        print("             @property")
        print("             def phase_deg(self) -> np.ndarray:")
        print("                 return np.arctan2(self.iq_opt, self.id_opt) * 180 / np.pi - 90")
    return has_prop


def print_delta_beta(betas_by_speed: dict):
    """Calibration 효과: β_opt 차이 (SC/HalfSC − Ref) 출력."""
    if "Ref" not in betas_by_speed.get(SPEEDS_RPM[0], {}):
        print("  [SKIP] Ref 모델 결과 없음.")
        return
    for other in ["HalfSC", "SC"]:
        if other not in betas_by_speed.get(SPEEDS_RPM[0], {}):
            continue
        print(f"\n  Δβ = {other} − Ref [deg]:")
        for speed in SPEEDS_RPM:
            row = f"    {speed:>6.0f} rpm:"
            for torque in TORQUES_NM:
                b_ref   = betas_by_speed.get(speed, {}).get("Ref",   {}).get(torque)
                b_other = betas_by_speed.get(speed, {}).get(other,   {}).get(torque)
                if b_ref is not None and b_other is not None:
                    row += f"  {torque:.0f}Nm → {b_other - b_ref:+.2f}°"
                else:
                    row += f"  {torque:.0f}Nm → N/A"
            print(row)


# ---------------------------------------------------------------------------
def _beta_grid(betas_by_speed: dict, model: str) -> np.ndarray:
    """betas_by_speed → 2D float array (n_torque × n_speed). None → NaN."""
    arr = np.full((len(TORQUES_NM), len(SPEEDS_RPM)), np.nan)
    for i, trq in enumerate(TORQUES_NM):
        for j, spd in enumerate(SPEEDS_RPM):
            val = betas_by_speed.get(spd, {}).get(model, {}).get(trq)
            if val is not None:
                arr[i, j] = val
    return arr


def save_results_mat(betas_by_speed: dict, out_path: Path):
    """주요 β_opt 결과를 .mat 파일로 저장.

    MATLAB 사용법:
        data = load('verify_phase_angle_results.mat');
        data.beta_sc        % [n_torque × n_speed] β_opt for SC model [deg]
        data.speed_rpm      % [1 × n_speed]
        data.torque_nm      % [1 × n_torque]

    # run_efficiency_map.py에도 동일한 패턴으로 .mat 저장 예정:
    #   efficiency_map_results.mat — eta, beta_deg, loss_total 등 전체 효율맵 격자
    """
    mdict = {
        "beta_ref":    _beta_grid(betas_by_speed, "Ref"),
        "beta_halfsc": _beta_grid(betas_by_speed, "HalfSC"),
        "beta_sc":     _beta_grid(betas_by_speed, "SC"),
        "speed_rpm":   np.array(SPEEDS_RPM, dtype=float).reshape(1, -1),
        "torque_nm":   np.array(TORQUES_NM,  dtype=float).reshape(1, -1),
    }
    savemat(str(out_path), mdict)

    shape_str = str(mdict["beta_ref"].shape)
    print(f"  저장: {out_path}")
    print(f"  beta_* shape : {shape_str}  (axis0=torque, axis1=speed)")
    print(f"  speed_rpm    : {SPEEDS_RPM}")
    print(f"  torque_nm    : {TORQUES_NM}")
    print(f"  MATLAB       : data = load('{out_path.name}'); data.beta_sc")


# ---------------------------------------------------------------------------
def main():
    print("=" * 66)
    print(" verify_phase_angle.py — e10 최적 전류위상각 검증")
    print("=" * 66)

    # 0. EfficiencyMap.phase_deg 프로퍼티 확인 (Task 1-B 선행 체크)
    print("\n[0] EfficiencyMap.phase_deg 프로퍼티 확인")
    check_efficiency_map_phase_property()

    # 1. 기본 모터 맵 로드
    print(f"\n[1] SatuMap 로드: {SAT_MAP_PATH.name}")
    base_map = load_base_map()
    scaled_map = scale_motor_map(base_map, k_r=1.0, k_a=1.0)  # 스케일링 없음
    print(f"    R_dc = {scaled_map.r_dc*1000:.3f} mΩ  |  pole_pairs = {scaled_map.pole_pairs}")

    # 2. 모델별 RBF 로드
    print("\n[2] RBF 모델 로드")
    rbf_models = {}
    for name, path in MODELS.items():
        rbf_models[name] = RbfJsonReader.read(str(path), use_separable=True)
        print(f"    {name:8s}: {rbf_models[name].model_type}  "
              f"centers={len(rbf_models[name].weights)}")

    # 3. 속도×토크 β_opt 테이블
    print("\n[3] 최적 전류위상각 β_opt [deg]")
    print(f"    V_max={V_MAX:.1f} V_pk  |  I_max={I_MAX:.1f} A_pk")

    # betas_by_speed[speed][model][torque] = β or None  (Δβ 계산용)
    betas_by_speed = {spd: {m: {} for m in MODELS} for spd in SPEEDS_RPM}

    for torque in TORQUES_NM:
        print(f"\n  ── T_ref = {torque:.0f} Nm ──")
        header = f"  {'Speed':>8s}" + "".join(
            f"  {n:>10s}" for n in MODELS
        ) + "   [β_SC - β_Ref]"
        print(header)
        print("  " + "-" * (len(header) - 2))

        for speed in SPEEDS_RPM:
            row = f"  {speed:>6.0f} rpm"
            betas = {}
            for name, rbf in rbf_models.items():
                sol = MtpaFwSolver.solve(
                    torque_ref=torque,
                    speed_rpm=float(speed),
                    map_data=scaled_map,
                    rbf_model=rbf,
                    v_max=V_MAX,
                    i_max=I_MAX,
                )
                if sol["success"]:
                    b = phase_deg_from(sol["id_opt"], sol["iq_opt"])
                    betas[name] = b
                    betas_by_speed[speed][name][torque] = b
                    row += f"  {b:>8.2f}°"
                else:
                    betas[name] = None
                    betas_by_speed[speed][name][torque] = None
                    row += f"  {'--':>9s}"

            diff = ""
            if betas.get("SC") is not None and betas.get("Ref") is not None:
                diff = f"   Δβ={betas['SC']-betas['Ref']:+.2f}°"
            print(row + diff)

    # 3-1. Calibration 효과: Δβ 요약
    print("\n[3-1] Calibration 효과 — Δβ (model − Ref) [deg]")
    print_delta_beta(betas_by_speed)

    # 4. EEC 전압 모델 동작 확인 — 고속 운전점
    print("\n[4] EEC 전압 제약 확인 (T=200 Nm, SC 모델)")
    print(f"  {'Speed':>8s}  {'V_terminal':>12s}  {'V_limit':>10s}  "
          f"{'margin':>8s}  {'β_opt':>8s}  OK?")
    print("  " + "-" * 58)
    rbf_sc = rbf_models["SC"]
    for speed in SPEEDS_RPM:
        sol = MtpaFwSolver.solve(
            torque_ref=200.0,
            speed_rpm=float(speed),
            map_data=scaled_map,
            rbf_model=rbf_sc,
            v_max=V_MAX,
            i_max=I_MAX,
        )
        v = sol["voltage"]
        ok = "✓" if (sol["success"] and v <= V_MAX * 1.01) else "✗"
        beta = phase_deg_from(sol["id_opt"], sol["iq_opt"])
        print(f"  {speed:>6.0f} rpm  {v:>10.2f} V  {V_MAX:>10.2f} V  "
              f"{V_MAX-v:>+8.2f} V  {beta:>7.2f}°  {ok}")

    # 5. 손실 분해 (4000 RPM, 200 Nm, 3 모델 비교)
    speed_ref, torque_ref2 = 4000.0, 200.0
    print(f"\n[5] 손실 분해 비교 ({speed_ref:.0f} RPM, {torque_ref2:.0f} Nm)")
    print(f"  {'Model':>8s}  {'β_opt':>7s}  "
          f"{'P_total':>9s}  {'P_cu_dc':>9s}  "
          f"{'P_cu_ac':>9s}  {'P_fe':>9s}  [kW]")
    print("  " + "-" * 62)
    for name, rbf in rbf_models.items():
        sol = MtpaFwSolver.solve(
            torque_ref=torque_ref2,
            speed_rpm=speed_ref,
            map_data=scaled_map,
            rbf_model=rbf,
            v_max=V_MAX,
            i_max=I_MAX,
        )
        beta = phase_deg_from(sol["id_opt"], sol["iq_opt"])
        print(f"  {name:>8s}  {beta:>6.2f}°  "
              f"{sol['loss_total']:>9.3f}  {sol['loss_cu_dc']:>9.3f}  "
              f"{sol['loss_cu_ac']:>9.3f}  {sol['loss_fe']:>9.3f}")

    # 6. 결과 .mat 저장
    print("\n[6] 결과 저장 (.mat)")
    mat_out = SCRIPT_DIR / "verify_phase_angle_results.mat"
    save_results_mat(betas_by_speed, mat_out)

    print("\n" + "=" * 66)
    print(" PASS — verify_phase_angle 완료")
    print("=" * 66)


if __name__ == "__main__":
    main()
