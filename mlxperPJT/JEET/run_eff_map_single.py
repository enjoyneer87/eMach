"""
run_eff_map_single.py
---------------------
Ref 모델 단일 효율맵 검증 스크립트.
3종 비교(run_efficiency_map.py) 전에 로직·경로를 먼저 확인하는 용도.

출력: eff_map_single_ref.mat
  - eta_pct       (21×17)  효율 [%]
  - speed_rpm     (1×17)   속도 축 [RPM]
  - torque_nm     (1×21)   토크 축 [Nm]
  - beta_deg      (21×17)  최적 전류위상각 [deg]
  - i_amp         (21×17)  전류 진폭 [A_pk]
  - loss_cu_dc_kW (21×17)  DC 구리손 [kW]
  - loss_cu_ac_kW (21×17)  AC 구리손 [kW]  (Ref = 0)
  - loss_fe_kW    (21×17)  철손 [kW]
"""

# %% [0] 경로 설정
import sys
import time
import numpy as np
from pathlib import Path
from scipy.io import loadmat, savemat

current_dir = Path(__file__).parent.resolve()
emach_root  = current_dir.parent.parent.resolve()
if str(emach_root) not in sys.path:
    sys.path.insert(0, str(emach_root))

from tools.motor_scaling import (
    BaseMotorMap,
    RbfJsonReader,
    generate_efficiency_map,
)

MODEL      = "Ref"
POLE_PAIRS = 4
V_MAX      = 720.0 / np.sqrt(3.0)   # 최대 상전압 피크 [V_pk]
I_MAX      = 460.0 * np.sqrt(2.0)   # 최대 상전류 피크 [A_pk]
K_R, K_A   = 1.0, 1.0

SPEED_RPM  = np.linspace(0.0, 16000.0, 17)   # (17,)
TORQUE_NM  = np.linspace(0.0, 500.0,  21)    # (21,)

SAT_MAP_PATH = emach_root / "tools" / "SystemSimulationModel" / "e10_SatuMap.mat"
RBF_PATH     = current_dir / "map_exports" / "e10" / MODEL / f"AF_RBF_model_{MODEL}.json"
OUTPUT_PATH  = current_dir / "eff_map_single_ref.mat"

print(f"emach_root : {emach_root}")
print(f"SatuMap    : {SAT_MAP_PATH}")
print(f"RBF JSON   : {RBF_PATH}")
print(f"출력 경로   : {OUTPUT_PATH}")
print(f"V_MAX={V_MAX:.2f} V_pk,  I_MAX={I_MAX:.2f} A_pk")

# %% [1] Ref 효율맵 계산
# ── 기반 모터맵 로드 ──────────────────────────────────────────────────────────
data = loadmat(str(SAT_MAP_PATH))

def _sq(key):
    return np.squeeze(data[key])

base_map = BaseMotorMap(
    id_grid         = _sq('Id_Peak'),
    iq_grid         = _sq('Iq_Peak'),
    lambda_d        = _sq('Flux_Linkage_D'),
    lambda_q        = _sq('Flux_Linkage_Q'),
    r_dc            = float(_sq('Phase_Resistance_DC_at_20C')),
    p_fe_grid       = _sq('Iron_Loss') / 1000.0,               # W → kW
    p_cu_ac_hybrid  = _sq('Stator_Copper_Loss_AC') / 1000.0,   # W → kW
    pole_pairs      = POLE_PAIRS,
)
print(f"\nSatuMap 로드 완료  R_dc={base_map.r_dc:.6f} Ω,  grid={base_map.id_grid.shape}")

# ── RBF 파라미터 로드 ─────────────────────────────────────────────────────────
if not RBF_PATH.exists():
    raise FileNotFoundError(f"RBF 모델 파일 없음: {RBF_PATH}")

rbf_params = RbfJsonReader.read(str(RBF_PATH), use_separable=True)
print(f"RBF 로드 완료  타입={rbf_params.model_type},  "
      f"기저 가중치 수={len(rbf_params.weights)}")

# ── 효율맵 계산 ───────────────────────────────────────────────────────────────
# 0 RPM → 1 RPM 으로 대체 (EEC solver 회피, 결과는 η=0으로 덮어씀)
speed_for_solver = SPEED_RPM.copy()
speed_for_solver[speed_for_solver < 1.0] = 1.0

print(f"\n효율맵 계산 시작 …  {len(TORQUE_NM)}×{len(SPEED_RPM)} = "
      f"{len(TORQUE_NM)*len(SPEED_RPM)} pts")
t0 = time.time()

eff_map = generate_efficiency_map(
    base_map   = base_map,
    k_r        = K_R,
    k_a        = K_A,
    rbf_model  = rbf_params,
    speeds_rpm = speed_for_solver,
    torques_ref= TORQUE_NM,
    v_max      = V_MAX,
    i_max      = I_MAX,
)

elapsed = time.time() - t0
n_ok = eff_map.success_mask.sum()
print(f"계산 완료 ({elapsed:.1f}s),  수렴 {n_ok}/{len(TORQUE_NM)*len(SPEED_RPM)} pts")

# 결과 배열 추출
eta_pct       = eff_map.efficiency.copy()      # (21, 17)
beta_deg      = eff_map.phase_deg              # (21, 17)
i_amp         = eff_map.i_amp                  # (21, 17)
loss_cu_dc_kW = eff_map.loss_cu_dc             # (21, 17)
loss_cu_ac_kW = eff_map.loss_cu_ac             # (21, 17)  Ref → 0         
loss_fe_kW    = eff_map.loss_fe                # (21, 17)

# 0 RPM 열 → 효율 0으로 강제 설정
if SPEED_RPM[0] < 1.0:
    eta_pct[:, 0] = 0.0

# %% [2] 결과 확인 (print)
print("\n── 효율 요약 ──────────────────────────────────────────")
print(f"  전체 최대 효율 : {np.nanmax(eta_pct):.3f}%")
print(f"  유효 포인트 수 : {np.sum(~np.isnan(eta_pct))}/{eta_pct.size}")

# 토크 250 Nm (인덱스 10) 라인
t_idx = 10  # TORQUE_NM[10] ≈ 250 Nm
print(f"\n  [T={TORQUE_NM[t_idx]:.0f} Nm 라인]")
for s_idx, spd in enumerate(SPEED_RPM):
    mark = f"  η={eta_pct[t_idx, s_idx]:.2f}%" if not np.isnan(eta_pct[t_idx, s_idx]) else "  η=NaN"
    print(f"    {spd:6.0f} RPM{mark}")

print(f"\n  loss_cu_ac_kW max (Ref=0 expected): {np.nanmax(loss_cu_ac_kW):.4f} kW")
print(f"  beta_deg range: [{np.nanmin(beta_deg):.1f}, {np.nanmax(beta_deg):.1f}] deg")
print(f"  i_amp   range: [{np.nanmin(i_amp):.1f}, {np.nanmax(i_amp):.1f}] A_pk")

# %% [3] .mat 저장
savemat(
    str(OUTPUT_PATH),
    {
        'eta_pct':       eta_pct,
        'speed_rpm':     SPEED_RPM.reshape(1, -1),   # (1×17)
        'torque_nm':     TORQUE_NM.reshape(1, -1),   # (1×21) — MATLAB row vector
        'beta_deg':      beta_deg,
        'i_amp':         i_amp,
        'loss_cu_dc_kW': loss_cu_dc_kW,
        'loss_cu_ac_kW': loss_cu_ac_kW,
        'loss_fe_kW':    loss_fe_kW,
        'model_name':    MODEL,
        'v_max_V':       V_MAX,
        'i_max_A':       I_MAX,
    },
    do_compression=True,
)
print(f"\n저장 완료: {OUTPUT_PATH}")
print(f"  eta_pct 형상    : {eta_pct.shape}")
print(f"  speed_rpm 형상  : {SPEED_RPM.reshape(1,-1).shape}")
print(f"  torque_nm 형상  : {TORQUE_NM.reshape(1,-1).shape}")
