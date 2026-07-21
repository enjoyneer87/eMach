"""
run_efficiency_map.py
---------------------
Ref / HalfSC / SC 3모델 map-based 효율맵 계산 스크립트.

논문2(power-consistent map-based MIL)의 Phase A 산출물.
SCL-M 기하 스케일링(k_r)을 각 모델에 적용하고, 멱지수 분리형 AF 모델
(AF = f(w)·g(I,β)^p(w))로 AC 구리손을 보정한 뒤 MTPA/FW EEC 솔버로
효율맵을 생성한다.

■ 2026-07-19 갱신 (paper2 Phase A):
  - 구 AF_RBF_model_{m}.json(base@2k scalar) → AF_model_{m}_exponent.json
    (base@16k, 멱지수 분리형) 로 교체.
  - 모델별 k_r/I_max/토크축을 물리적으로 부여 (기존 K_R=1 하드코딩 수정):
      Ref  k_r=1.0  I_rms=460A  T∈[0,900]
      Half k_r=1.5  I_rms=690A  T∈[0,2025]
      SC   k_r=2.0  I_rms=920A  T∈[0,3600]
    → Lab 효율맵(effmaps/MotorLAB_elecdata_{Ref,SC})과 동일 운전영역.

■ 알려진 한계 (paper2 Phase C 대상):
  e10_SatuMap.mat의 Iron_Loss는 단일 조건 값(속도 스케일링 없음).
  고속 철손이 과소평가되므로 효율은 낙관적. Lab 대조는
  compare_effmap_vs_lab.py 에서 철손 채널을 분리해 정직하게 보고.

출력: efficiency_map_results.mat
  - eta_pct       (n_torque, n_speed, 3)  효율 [%]
  - speed_rpm     (n_speed,)              속도 축
  - torque_nm     (n_torque, 3)           모델별 토크 축 [Nm]
  - beta_deg      (n_torque, n_speed, 3)  최적 전류위상각 [deg]
  - loss_cu_dc_kW (n_torque, n_speed, 3)  DC 구리손 [kW]
  - loss_cu_ac_kW (n_torque, n_speed, 3)  AC 구리손 [kW]
  - loss_fe_kW    (n_torque, n_speed, 3)  철손 [kW]
  - k_r_all, i_max_rms_all                모델별 스케일/전류한계
"""

import sys
import time
import numpy as np
from pathlib import Path
from scipy.io import loadmat, savemat

# ── 경로 설정 ──────────────────────────────────────────────────────────────
current_dir = Path(__file__).parent.resolve()
emach_root  = current_dir.parent.parent.resolve()
if str(emach_root) not in sys.path:
    sys.path.insert(0, str(emach_root))

from tools.motor_scaling import (
    BaseMotorMap,
    RbfJsonReader,
    generate_efficiency_map,
)

# ── 설계 상수 ──────────────────────────────────────────────────────────────
POLE_PAIRS = 4
V_DC     = 720.0                             # DC 버스 전압 [V]
V_MAX    = V_DC / np.sqrt(3.0)               # 최대 상전압 피크 [V_pk]
K_A      = 1.0                               # 축방향 스케일 (미적용)

# 권선 온도 보정: Lab 효율맵은 80°C(Stator_Winding_Temp_Average)에서 계산되므로
# SatuMap의 20°C DC 저항을 동일 온도로 스케일해 DC 동손을 정합시킨다.
WINDING_TEMP_C = 80.0
ALPHA_CU = 0.00393                           # 구리 저항온도계수 [1/°C]
R_TEMP_FACTOR = 1.0 + ALPHA_CU * (WINDING_TEMP_C - 20.0)

# 모델별 SCL-M 스케일 / 전류한계 / 토크범위
#   I_rms_max = 460·k_r  (B-보존 스케일링),  T_max = 900·k_r²  (T ∝ k_r²·k_a)
T_MAX_REF = 900.0                            # Ref 토크 상한 [Nm] (Lab peak≈862)
MODELS_CFG = {
    'Ref':    {'k_r': 1.0, 'i_rms_max': 460.0},
    'HalfSC': {'k_r': 1.5, 'i_rms_max': 690.0},
    'SC':     {'k_r': 2.0, 'i_rms_max': 920.0},
}
MODELS = list(MODELS_CFG.keys())             # 순서 = mat 3번째 축

# 그리드 해상도
N_SPEED  = 33                                # 0 ~ 16000 RPM (500 RPM 간격, Lab와 정합)
N_TORQUE = 25                                # 0 ~ T_max
SPEED_RPM = np.linspace(0.0, 16000.0, N_SPEED)

# ── 파일 경로 ─────────────────────────────────────────────────────────────
SAT_MAP_PATH = emach_root / "tools" / "SystemSimulationModel" / "e10_SatuMap.mat"
MAP_EXPORT   = current_dir / "map_exports" / "e10"
OUTPUT_PATH  = current_dir / "efficiency_map_results.mat"


# ── 기반 모터맵 로드 (SatuMap.mat) ────────────────────────────────────────
def load_base_motor_map(mat_path: Path) -> BaseMotorMap:
    data = loadmat(str(mat_path))

    def sq(key):
        return np.squeeze(data[key])

    r_dc_20 = float(sq('Phase_Resistance_DC_at_20C'))
    return BaseMotorMap(
        id_grid=sq('Id_Peak'),
        iq_grid=sq('Iq_Peak'),
        lambda_d=sq('Flux_Linkage_D'),
        lambda_q=sq('Flux_Linkage_Q'),
        r_dc=r_dc_20 * R_TEMP_FACTOR,                     # 20°C → 80°C 정합
        p_fe_grid=sq('Iron_Loss') / 1000.0,               # W → kW
        p_cu_ac_hybrid=sq('Stator_Copper_Loss_AC') / 1000.0,  # W → kW
        pole_pairs=POLE_PAIRS,
    )


def load_af_model(model_name: str):
    """멱지수 분리형 AF 모델(AF_model_{m}_exponent.json)을 우선 로드.

    없으면 구 scalar 모델(AF_RBF_model_{m}.json)로 폴백.
    """
    exp_path = MAP_EXPORT / model_name / f"AF_model_{model_name}_exponent.json"
    if exp_path.exists():
        return RbfJsonReader.read(str(exp_path), use_separable=True), exp_path
    legacy = MAP_EXPORT / model_name / f"AF_RBF_model_{model_name}.json"
    if legacy.exists():
        return RbfJsonReader.read(str(legacy), use_separable=True), legacy
    raise FileNotFoundError(
        f"AF 모델 없음: {exp_path} (또는 {legacy})")


def run():
    print("=" * 64)
    print("map-based 효율맵 계산  (Ref / HalfSC / SC)  - paper2 Phase A")
    print(f"  속도: {N_SPEED} pts  [0 ~ 16000 RPM]")
    print(f"  토크: {N_TORQUE} pts  [모델별 0 ~ 900·k_r²]")
    print(f"  V_max={V_MAX:.1f} V_pk")
    print("=" * 64)

    base_map = load_base_motor_map(SAT_MAP_PATH)
    print(f"\nSatuMap: R_dc={base_map.r_dc:.6f} Ω, grid {base_map.id_grid.shape}")

    eta_all     = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    beta_all    = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    iamp_all    = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    loss_dc_all = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    loss_ac_all = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    loss_fe_all = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    torque_all  = np.full((N_TORQUE, 3), np.nan)
    k_r_all     = np.array([MODELS_CFG[m]['k_r'] for m in MODELS], float)
    imax_all    = np.array([MODELS_CFG[m]['i_rms_max'] for m in MODELS], float)

    # 0 RPM → 1 RPM (EEC solver 회피, 결과는 η=0으로 덮어씀)
    speed_for_solver = SPEED_RPM.copy()
    speed_for_solver[speed_for_solver < 1.0] = 1.0

    t_start = time.time()
    for m_idx, model_name in enumerate(MODELS):
        cfg = MODELS_CFG[model_name]
        k_r = cfg['k_r']
        i_max_pk = cfg['i_rms_max'] * np.sqrt(2.0)
        torque_axis = np.linspace(0.0, T_MAX_REF * k_r**2, N_TORQUE)
        torque_all[:, m_idx] = torque_axis

        rbf_params, rbf_path = load_af_model(model_name)
        print(f"\n  [{m_idx+1}/3] {model_name}  k_r={k_r}  "
              f"I_rms_max={cfg['i_rms_max']:.0f}A  T_max={torque_axis[-1]:.0f}Nm")
        print(f"        AF: {rbf_path.name}  ({rbf_params.model_type}, "
              f"exponent={'yes' if rbf_params.q_coeffs is not None else 'no'})")

        t0 = time.time()
        eff_map = generate_efficiency_map(
            base_map=base_map,
            k_r=k_r,
            k_a=K_A,
            rbf_model=rbf_params,
            speeds_rpm=speed_for_solver,
            torques_ref=torque_axis,
            v_max=V_MAX,
            i_max=i_max_pk,
        )
        n_ok = eff_map.success_mask.sum()
        print(f"        완료 ({time.time()-t0:.1f}s), "
              f"수렴 {n_ok}/{N_SPEED*N_TORQUE}")

        eta_all[:, :, m_idx]     = eff_map.efficiency
        beta_all[:, :, m_idx]    = eff_map.phase_deg
        iamp_all[:, :, m_idx]    = eff_map.i_amp
        loss_dc_all[:, :, m_idx] = eff_map.loss_cu_dc
        loss_ac_all[:, :, m_idx] = eff_map.loss_cu_ac
        loss_fe_all[:, :, m_idx] = eff_map.loss_fe
        if SPEED_RPM[0] < 1.0:
            eta_all[:, 0, m_idx] = 0.0

    print(f"\n전체 계산 완료: {time.time()-t_start:.1f}s")

    savemat(
        str(OUTPUT_PATH),
        {
            'eta_pct':       eta_all,
            'speed_rpm':     SPEED_RPM,
            'torque_nm':     torque_all,
            'beta_deg':      beta_all,
            'i_amp_pk':      iamp_all,
            'winding_temp_C': WINDING_TEMP_C,
            'loss_cu_dc_kW': loss_dc_all,
            'loss_cu_ac_kW': loss_ac_all,
            'loss_fe_kW':    loss_fe_all,
            'model_names':   np.array(MODELS, dtype=object),
            'k_r_all':       k_r_all,
            'i_max_rms_all': imax_all,
            'v_max_V':       V_MAX,
        },
        do_compression=True,
    )
    print(f"결과 저장: {OUTPUT_PATH}")

    print("\n── 효율 요약 (각 모델 토크축 중간값 기준) ──")
    for m_idx, model_name in enumerate(MODELS):
        t_mid = N_TORQUE // 2
        etas = eta_all[t_mid, :, m_idx]
        if np.any(~np.isnan(etas)):
            print(f"  {model_name:7s} T={torque_all[t_mid, m_idx]:6.0f}Nm: "
                  f"max η={np.nanmax(etas):.2f}% @ "
                  f"{SPEED_RPM[np.nanargmax(etas)]:.0f} RPM")
    print("=" * 64)


if __name__ == '__main__':
    run()
