"""
run_efficiency_map.py
---------------------
Ref / HalfSC / SC 3모델 효율맵 비교 계산 스크립트.

출력: efficiency_map_results.mat
  - eta_pct       (n_torque, n_speed, 3)  효율 [%]
  - speed_rpm     (n_speed,)              속도 축
  - torque_nm     (n_torque,)             토크 축
  - beta_deg      (n_torque, n_speed, 3)  최적 전류위상각 [deg]
  - loss_cu_dc_kW (n_torque, n_speed, 3)  DC 구리손 [kW]
  - loss_cu_ac_kW (n_torque, n_speed, 3)  AC 구리손 [kW]
  - loss_fe_kW    (n_torque, n_speed, 3)  철손 [kW]
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
MODELS   = ['Ref', 'HalfSC', 'SC']          # 비교 모델 이름 (순서 = mat 3번째 축)
POLE_PAIRS = 4
V_DC     = 720.0                             # DC 버스 전압 [V]
I_RMS_MAX = 460.0                            # 최대 상전류 RMS [A]
V_MAX    = V_DC / np.sqrt(3.0)              # 최대 상전압 피크 [V_pk]
I_MAX    = I_RMS_MAX * np.sqrt(2.0)         # 최대 상전류 피크 [A_pk]
K_R, K_A = 1.0, 1.0                         # 스케일링 계수 (동일 모터)

# 그리드 해상도 (태스크 요구사항)
N_SPEED  = 17                               # 0 ~ 16000 RPM
N_TORQUE = 21                               # 0 ~ T_MAX_NM
T_MAX_NM = 500.0                            # 토크 최대값 [Nm]

SPEED_RPM  = np.linspace(0.0, 16000.0, N_SPEED)
TORQUE_NM  = np.linspace(0.0, T_MAX_NM,  N_TORQUE)

# ── 파일 경로 ─────────────────────────────────────────────────────────────
SAT_MAP_PATH = emach_root / "tools" / "SystemSimulationModel" / "SatuMap.mat"
MAP_EXPORT   = current_dir / "map_exports" / "e10"
OUTPUT_PATH  = current_dir / "efficiency_map_results.mat"

# ── 기반 모터맵 로드 (SatuMap.mat) ────────────────────────────────────────
def load_base_motor_map(mat_path: Path) -> BaseMotorMap:
    data = loadmat(str(mat_path))

    def sq(key):
        return np.squeeze(data[key])

    id_grid  = sq('Id_Peak')
    iq_grid  = sq('Iq_Peak')
    lambda_d = sq('Flux_Linkage_D')
    lambda_q = sq('Flux_Linkage_Q')
    p_fe     = sq('Iron_Loss') / 1000.0              # W → kW
    p_cu_ac  = sq('Stator_Copper_Loss_AC') / 1000.0  # W → kW
    r_dc     = float(sq('Phase_Resistance_DC_at_20C'))

    return BaseMotorMap(
        id_grid=id_grid,
        iq_grid=iq_grid,
        lambda_d=lambda_d,
        lambda_q=lambda_q,
        r_dc=r_dc,
        p_fe_grid=p_fe,
        p_cu_ac_hybrid=p_cu_ac,
        pole_pairs=POLE_PAIRS,
    )


def run():
    print("=" * 60)
    print("효율맵 계산  (Ref / HalfSC / SC)")
    print(f"  속도: {N_SPEED} pts  [{SPEED_RPM[0]:.0f} ~ {SPEED_RPM[-1]:.0f} RPM]")
    print(f"  토크: {N_TORQUE} pts  [{TORQUE_NM[0]:.0f} ~ {TORQUE_NM[-1]:.0f} Nm]")
    print(f"  총 포인트/모델: {N_SPEED * N_TORQUE}")
    print("=" * 60)

    # 1. 기반 모터맵 로드
    print(f"\n[1/2] SatuMap 로드: {SAT_MAP_PATH}")
    base_map = load_base_motor_map(SAT_MAP_PATH)
    print(f"      R_dc={base_map.r_dc:.6f} Ω,  grid {base_map.id_grid.shape}")

    # 2. 모델별 효율맵 생성
    eta_all      = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    beta_all     = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    loss_dc_all  = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    loss_ac_all  = np.full((N_TORQUE, N_SPEED, 3), np.nan)
    loss_fe_all  = np.full((N_TORQUE, N_SPEED, 3), np.nan)

    # 속도 그리드에서 0 RPM 점은 EEC 계산이 불가하므로 최솟값으로 대체
    # (생성기에서 success_mask=False 처리되면 NaN 유지)
    speed_for_solver = SPEED_RPM.copy()
    speed_for_solver[speed_for_solver < 1.0] = 1.0  # 0 RPM → 1 RPM (손실 0과 동일)

    print(f"\n[2/2] 효율맵 계산 시작 …")
    t_start_all = time.time()

    for m_idx, model_name in enumerate(MODELS):
        rbf_path = MAP_EXPORT / model_name / f"AF_RBF_model_{model_name}.json"
        if not rbf_path.exists():
            raise FileNotFoundError(f"RBF 모델 파일 없음: {rbf_path}")

        print(f"\n  [{m_idx+1}/{len(MODELS)}] {model_name}")
        print(f"        RBF: {rbf_path.name}")

        rbf_params = RbfJsonReader.read(str(rbf_path), use_separable=True)
        print(f"        타입={rbf_params.model_type},  "
              f"기저 가중치 수={len(rbf_params.weights)}")

        t0 = time.time()
        eff_map = generate_efficiency_map(
            base_map=base_map,
            k_r=K_R,
            k_a=K_A,
            rbf_model=rbf_params,
            speeds_rpm=speed_for_solver,
            torques_ref=TORQUE_NM,
            v_max=V_MAX,
            i_max=I_MAX,
        )
        elapsed = time.time() - t0
        n_ok = eff_map.success_mask.sum()
        print(f"        완료 ({elapsed:.1f}s),  "
              f"수렴 {n_ok}/{N_SPEED * N_TORQUE} pts")

        eta_all[:, :, m_idx]     = eff_map.efficiency
        beta_all[:, :, m_idx]    = eff_map.phase_deg
        loss_dc_all[:, :, m_idx] = eff_map.loss_cu_dc
        loss_ac_all[:, :, m_idx] = eff_map.loss_cu_ac
        loss_fe_all[:, :, m_idx] = eff_map.loss_fe

        # 0 RPM 열 → 효율 0으로 덮어쓰기
        if SPEED_RPM[0] < 1.0:
            eta_all[:, 0, m_idx] = 0.0

    total_elapsed = time.time() - t_start_all
    print(f"\n  전체 계산 완료: {total_elapsed:.1f}s")

    # 3. 결과 저장
    savemat(
        str(OUTPUT_PATH),
        {
            'eta_pct':       eta_all,
            'speed_rpm':     SPEED_RPM,
            'torque_nm':     TORQUE_NM,
            'beta_deg':      beta_all,
            'loss_cu_dc_kW': loss_dc_all,
            'loss_cu_ac_kW': loss_ac_all,
            'loss_fe_kW':    loss_fe_all,
            'model_names':   np.array(MODELS, dtype=object),
            'v_max_V':       V_MAX,
            'i_max_A':       I_MAX,
        },
        do_compression=True,
    )
    print(f"\n결과 저장 완료: {OUTPUT_PATH}")
    print(f"  변수 형상: eta_pct={eta_all.shape}, "
          f"beta_deg={beta_all.shape}")

    # 4. 요약 출력
    print("\n── 효율 요약 (토크=250 Nm 기준) ──")
    t_idx_mid = int(N_TORQUE * 0.5)
    for m_idx, model_name in enumerate(MODELS):
        etas = eta_all[t_idx_mid, :, m_idx]
        print(f"  {model_name:7s}: max={np.nanmax(etas):.2f}%  "
              f"@ {SPEED_RPM[np.nanargmax(etas)]:.0f} RPM")

    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == '__main__':
    run()
