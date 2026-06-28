# %%[markdown]
# # [1] Imports & Setup (Dual Run Modes)
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [1] Setup & Imports
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import glob
import json
import shutil
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.io import savemat

# Repo root on path
repo_root = Path.cwd().resolve()
while repo_root.name and repo_root.name not in ("EveryMotor", "NvidiaNemo"):
    repo_root = repo_root.parent
emach_root = repo_root / "eMach"
if str(emach_root) not in sys.path:
    sys.path.insert(0, str(emach_root))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(f"Repository Root: {repo_root}")
print(f"eMach Root: {emach_root}")


# %%[markdown]
# # [2] 모터 모델 및 실행 모드 설정
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [2] Configuration: Model Scale & Run Mode Selection
# ─────────────────────────────────────────────────────────────────────────────
# Define motor file paths for each local/remote configuration
# (Update these paths to match your local folders on different machines)
MOTOR_FILES = {
    'Ref': r"D:\KDH\simVary\e10_6TSweep\refModel\e10Turn6V261.mot",
    'HalfSC': r"D:\KDH\simVary\e10_6TSweep\SLFEA_Half\e10Turn6V261SLFEA_Half.mot",
    'SC': r"D:\KDH\simVary\e10_6TSweep\SLFEA\e10Turn6V261SLFEA.mot"
}

out_dir = Path("map_exports")
out_dir.mkdir(parents=True, exist_ok=True)

# ── 1. Path existence check for all Model Scales ─────────────────────────────
print("=== [Data & Model Path Existence Check] ===")
for scale in ['Ref', 'HalfSC', 'SC']:
    mot_p = MOTOR_FILES.get(scale)
    json_p = out_dir / f"JEET_ACLoss_{scale}_Map_Summary.json"
    
    mot_exists = Path(mot_p).exists() if mot_p else False
    json_exists = json_p.exists()
    
    print(f"[{scale}]")
    print(f"  - .mot file path: {mot_p}")
    print(f"    -> Exists? {'[YES]' if mot_exists else '[NO]'}")
    print(f"  - JSON summary:  {json_p}")
    print(f"    -> Exists? {'[YES]' if json_exists else '[NO]'}")
print("===========================================\n")

MODEL_SCALE = 'Ref'  # Options: 'Ref' (k_Radial=1.0), 'HalfSC' (k_Radial=1.5), 'SC' (k_Radial=2.0)
RUN_FEA_SWEEP = True    # True: Run FEA inside Motor-CAD. False: Bypasses connection, loads JSON map only.

mot_file_path = MOTOR_FILES.get(MODEL_SCALE)
print(f"Selected Model Scale: {MODEL_SCALE}")
print(f"Target Motor File: {mot_file_path}")
print(f"FEA Sweep Execution: {'ENABLED' if RUN_FEA_SWEEP else 'DISABLED (Offline Mode)'}")

# Output summary paths
json_summary_path = out_dir / f"JEET_ACLoss_{MODEL_SCALE}_Map_Summary.json"
mat_summary_path = out_dir / f"JEET_ACLoss_{MODEL_SCALE}_Map_Summary.mat"
rbf_model_path = out_dir / f"AF_RBF_model_{MODEL_SCALE}.json"

# Convert to SI units (will be updated dynamically if connected, else uses fallbacks)
COND_WIDTH_MM, COND_HEIGHT_MM, ACTIVE_LENGTH_MM = 2.5, 2.5, 150.0

mcad = None
if RUN_FEA_SWEEP:
    print("Connecting to Motor-CAD instance...")
    try:
        import ansys.motorcad.core as pymotorcad
        mcad = pymotorcad.MotorCAD(open_new_instance=False)
        if Path(mot_file_path).exists():
            print(f"Loading selected model: {mot_file_path}")
            mcad.load_from_file(mot_file_path)
        else:
            print(f"[WARN] Motor-CAD file not found at: {mot_file_path}")
            print("Will attempt to proceed with the currently active Motor-CAD model.")
        COND_WIDTH_MM = float(mcad.get_variable("Copper_Width"))
        COND_HEIGHT_MM = float(mcad.get_variable("Copper_Height"))
        ACTIVE_LENGTH_MM = float(mcad.get_variable("Stator_Lam_Length"))
        print(f"✓ Read parameters: Width={COND_WIDTH_MM:.2f}mm, Height={COND_HEIGHT_MM:.2f}mm, Length={ACTIVE_LENGTH_MM:.1f}mm")
    except Exception as e:
        print(f"[WARN] Motor-CAD connection/read failed: {e}")
else:
    print("[Offline Mode] Motor-CAD connection bypassed.")
    print(f"Using default fallback parameters: Width={COND_WIDTH_MM}mm, Height={COND_HEIGHT_MM}mm, Length={ACTIVE_LENGTH_MM}mm")

b_m = COND_WIDTH_MM * 1e-3
h_m = COND_HEIGHT_MM * 1e-3
L_a = ACTIVE_LENGTH_MM * 1e-3

# Electrical frequency helper
POLE_PAIRS = 4
def speed_to_fe(speed_rpm, pole_pairs=POLE_PAIRS):
    return pole_pairs * speed_rpm / 60.0

# ── JSON 현황 (기존 sweep 범위 + 완료 상태) ─────────────────────────────────
import json as _json
from collections import Counter as _Counter
if json_summary_path.exists():
    try:
        with open(json_summary_path, 'r', encoding='utf-8') as _f:
            _loaded = _json.load(_f)
        _records  = _loaded.get('records', _loaded) if isinstance(_loaded, dict) else _loaded
        _meta     = _loaded.get('_meta', {})        if isinstance(_loaded, dict) else {}
        print(f"[JSON 현황: {MODEL_SCALE}]  총 {len(_records)}개 레코드")
        if _meta:
            print(f"  저장된 sweep 범위:")
            print(f"    PROXIMITY_MODELS  : {_meta.get('proximity_models','?')}")
            print(f"    SPEEDS            : {_meta.get('speeds','?')}")
            print(f"    CURRENT_GRID 크기 : {_meta.get('n_curr_design','?')} pts  ({_meta.get('design_2d_strategy','?')})")
            print(f"    PHASE_GRID 크기   : {_meta.get('n_phase_design','?')} pts")
            print(f"    총 스케줄 포인트   : {_meta.get('total_schedule','?')}")
            print(f"    마지막 갱신       : {_meta.get('last_updated','?')}")
        if _records:
            _cnt = _Counter((r.get('proximity_model'), r.get('speed')) for r in _records)
            _labels = {1: 'Hybrid', 3: 'FullFEA'}
            print("  완료 현황 (모델 x 속도):")
            for (pm, spd), n in sorted(_cnt.items()):
                _has_result = sum(
                    1 for r in _records
                    if r.get('proximity_model') == pm and r.get('speed') == spd
                    and (('hybrid_total_kW' in r) if pm == 1 else ('fea_total_ac_kW' in r))
                )
                print(f"    [{_labels.get(pm, pm)}] {spd}RPM : {_has_result}/{n} 유효")
    except Exception as _e:
        print(f"  [WARN] JSON 파싱 실패: {_e}")


# %%[markdown]
# # [3] 통합 FEA Sweep 및 중복 방지 Resume 로직
#

# %%
# 이 셀은 오프라인 모드와 온라인 모드 모두에서 실행 가능한 헬퍼 기능들을 정의합니다.
SIGMA_CU = 5.8e7
MU_0 = 4.0 * np.pi * 1e-7


# %%[markdown]
# # [3.1] 통합 Sweep Loop 실행
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [3] Robust FEA Sweep with Automatic Resume/Skip Logic
# ─────────────────────────────────────────────────────────────────────────────
if RUN_FEA_SWEEP:
    from tools.motorCAD.pyMCAD import get_fea_src_dir
    
    # ── 1. Define Sweep Range ─────────────────────────────────────────────────
    CURRENT_GRID = np.linspace(0.1, 460.0*2, 5)   # [0.1, 115.1, 230.1, 345.1, 460.0] A
    PHASE_GRID = np.linspace(0.0, 90.0, 6)      # [0.0, 18.0, 36.0, 54.0, 72.0, 90.0] deg
    PROXIMITY_MODELS = [3, 1]                  # 1: Hybrid, 3: FullFEA
    
    FIRST_STEP = 1
    EXPORT_COLUMNS = "RegCode,Bx,By,A,J,Je,Hx,Hy,Mur"
    N_SESSIONS = 8                           # Motor-CAD parallel instances
    FORCE_RESWEEP_MODELS = []              # e.g. [3] to force re-run FullFEA; [] = use JSON cache
    
    # ── 1D x 2D Separable Sweep Design ──────────────────────────────────────────
    # AF(s, I, gamma) = F_1D(s) x F_2D(I, gamma) 분리형 구조를 올바르게 추정하려면
    # 모든 속도(1D 축)에서 동일한 (I, gamma) 설계점(2D 축)을 사용해야 한다.
    # 속도별로 다른 subset을 쓰면 1D/2D 축이 교란되어 분리 추정이 불가능해진다.
    #
    # DESIGN_2D_STRATEGY 선택:
    #   "full"   - 전체 격자 CURRENT_GRID x PHASE_GRID  (가장 높은 정확도)
    #   "tensor" - 균일 축소 격자 N_CURR_DESIGN x N_PHASE_DESIGN  (균형)
    #   "lhs"    - Latin Hypercube, 격자점에 스냅  (공간 충전 효율)
    SPEEDS = [2000, 4000, 8000, 16000]
    DESIGN_2D_STRATEGY = "tensor"    # <- "full" / "tensor" / "lhs"
    N_CURR_DESIGN  = 5             # tensor/lhs 전류 레벨 수
    N_PHASE_DESIGN = 6             # tensor/lhs 위상각 레벨 수

    def _build_2d_design(strategy, curr_grid, phase_grid, n_curr, n_phase):
        """Return list of (current, phase) pairs for the 2D base design."""
        if strategy == "full":
            return [(I, g) for I in curr_grid for g in phase_grid]

        elif strategy == "tensor":
            # Reduced uniform tensor product; boundaries always included.
            # Snap to nearest reference grid values.
            I_raw = np.linspace(curr_grid[0],  curr_grid[-1],  n_curr)
            g_raw = np.linspace(phase_grid[0], phase_grid[-1], n_phase)
            I_snp = np.unique([curr_grid[np.argmin(np.abs(curr_grid  - v))] for v in I_raw])
            g_snp = np.unique([phase_grid[np.argmin(np.abs(phase_grid - v))] for v in g_raw])
            return [(I, g) for I in I_snp for g in g_snp]

        elif strategy == "lhs":
            # Latin Hypercube Sampling in 2D, snapped to reference grid
            from scipy.stats import qmc
            sampler = qmc.LatinHypercube(d=2, seed=42)
            raw = sampler.random(n=n_curr * n_phase)
            scaled = qmc.scale(raw,
                               [curr_grid[0],  phase_grid[0]],
                               [curr_grid[-1], phase_grid[-1]])
            seen, pairs = set(), []
            for I_s, g_s in scaled:
                I = curr_grid[np.argmin(np.abs(curr_grid   - I_s))]
                g = phase_grid[np.argmin(np.abs(phase_grid - g_s))]
                key = (float(I), float(g))
                if key not in seen:
                    seen.add(key)
                    pairs.append((I, g))
            return pairs

        else:
            raise ValueError(f"Unknown DESIGN_2D_STRATEGY: {strategy!r}")

    # 2D 기준 설계점 — 모든 속도에 동일하게 적용 (분리형 구조의 핵심)
    base_2d = _build_2d_design(
        DESIGN_2D_STRATEGY, CURRENT_GRID, PHASE_GRID,
        N_CURR_DESIGN, N_PHASE_DESIGN,
    )
    n_2d = len(base_2d)
    n_est = len(PROXIMITY_MODELS) * len(SPEEDS) * n_2d
    print(f"2D design: {n_2d} pts ({DESIGN_2D_STRATEGY}),  "
          f"{len(PROXIMITY_MODELS)} models x {len(SPEEDS)} speeds -> {n_est} total")

    sweep_schedule = [
        {"proximity_model": prox_model, "speed": speed,
         "current": current, "phase": phase}
        for prox_model in PROXIMITY_MODELS
        for speed in SPEEDS
        for (current, phase) in base_2d
    ]
    print(f"Sweep schedule: {len(sweep_schedule)} points total")

    _sweep_meta = {
        "proximity_models":   PROXIMITY_MODELS,
        "speeds":             SPEEDS,
        "current_grid":       CURRENT_GRID.tolist(),
        "phase_grid":         PHASE_GRID.tolist(),
        "design_2d_strategy": DESIGN_2D_STRATEGY,
        "n_curr_design":      N_CURR_DESIGN,
        "n_phase_design":     N_PHASE_DESIGN,
        "total_schedule":     len(sweep_schedule),
        "last_updated":       datetime.now().isoformat(),
    }
    
    # ── 2. Load Existing Progress to Avoid Duplicate Sweeps ────────────────────
    sweep_results = []
    if json_summary_path.exists():
        try:
            with open(json_summary_path, "r", encoding="utf-8") as f:
                _loaded = json.load(f)
                if isinstance(_loaded, dict):
                    sweep_results = _loaded.get("records", [])
                    _sweep_meta.update(_loaded.get("_meta", {}))
                else:
                    sweep_results = _loaded  # legacy flat-list format
            print(f"✓ Loaded existing summary file: {json_summary_path}")
            print(f"  Existing records: {len(sweep_results)} points.")
        except Exception as e:
            print(f"[WARN] Failed to load existing JSON: {e}. Starting fresh.")
            sweep_results = []
            
    _REQUIRED_KEYS = {1: {"hybrid_total_kW"}, 3: {"fea_total_ac_kW"}}

    def is_point_existing(p_model, spd, curr, ph):
        if p_model in FORCE_RESWEEP_MODELS:
            return False
        required = _REQUIRED_KEYS.get(p_model, set())
        for record in sweep_results:
            if (record.get("proximity_model") == p_model and
                    record.get("speed") == spd and
                    np.isclose(record.get("current", -1), curr, atol=1e-2) and
                    np.isclose(record.get("phase", -1), ph, atol=1e-2) and
                    required.issubset(record.keys())):
                return True
        return False
        
    # Setup folders
    mot_path = Path(MOTOR_FILES[MODEL_SCALE])
    out_root = mot_path.parent
    backup_root = out_root / f"ACLossCalcExport_{MODEL_SCALE}"
    backup_root.mkdir(parents=True, exist_ok=True)
    

    # Helper to find the most recently modified .mes after an FEA run.
    # Checks live FEResultsData/ first, then falls back to the full model
    # directory tree (catches backup subdirs like FEResultsData_backup/...).
    def find_latest_mes(mcad_inst):
        fe_dir = get_fea_src_dir(mcad_inst)  # {mot_dir}/{mot_stem}/FEResultsData
        candidates = list(fe_dir.glob("*.mes"))
        if not candidates:
            model_dir = fe_dir.parent  # {mot_dir}/{mot_stem}/
            candidates = list(model_dir.rglob("*.mes"))
        if not candidates:
            raise FileNotFoundError(f"No .mes files found under {fe_dir.parent}")
    # ── 3. Parallel FEA Sweep (multiprocessing.Pool) ────────────────────────
    # Worker functions are defined in _mcad_parallel_worker.py so that
    # Windows multiprocessing 'spawn' can import them without re-running the
    # notebook. This follows the official Motor-CAD parallel scripting pattern.
    import sys
    from multiprocessing import Pool
    from _mcad_parallel_worker import initialise_mcad, run_sweep_point, close_mcad

    pending = [
        (idx, pt) for idx, pt in enumerate(sweep_schedule)
        if not is_point_existing(pt["proximity_model"], pt["speed"],
                                 pt["current"], pt["phase"])
    ]
    n_workers = min(N_SESSIONS, max(len(pending), 1))
    print(f"Pending: {len(pending)} / {len(sweep_schedule)} points. "
          f"Launching {n_workers} Motor-CAD session(s)...")

    if not pending:
        print("All scheduled points already present. No new sweeps executed.")
    else:
        # Build per-point argument dicts (must be picklable for subprocess transport)
        args_list = [
            {
                "prox_model":    pt["proximity_model"],
                "speed":         pt["speed"],
                "current":       pt["current"],
                "phase":         pt["phase"],
                "backup_root":   str(backup_root),
                "first_step":    FIRST_STEP,
                "export_columns": EXPORT_COLUMNS,
                "idx":           idx,
                "total_pts":     len(sweep_schedule),
            }
            for idx, pt in pending
        ]

        # Pool: each worker process runs initialise_mcad() once, then
        # receives sweep points via imap_unordered (returns results as they
        # complete, enabling incremental JSON saves for crash recovery).
        pool = Pool(
            processes=n_workers,
            initializer=initialise_mcad,
            initargs=(str(mot_path), sys.path[:]),
        )
        n_done = 0
        try:
            for result in pool.imap_unordered(run_sweep_point, args_list):
                n_done += 1
                if result is not None:
                    sweep_results.append(result)
                    with open(json_summary_path, "w", encoding="utf-8") as _f:
                        json.dump({"_meta": _sweep_meta, "records": sweep_results}, _f, ensure_ascii=False, indent=2)
                    mode  = result.get("mode", "?")
                    speed = result.get("speed", "?")
                    curr  = result.get("current", 0.0)
                    phase = result.get("phase", 0.0)
                    print(f"  [{n_done}/{len(pending)}] ok {mode} {speed}RPM {curr:.1f}A {phase:.1f}deg")
                else:
                    print(f"  [{n_done}/{len(pending)}] FAILED (see worker stderr)")
        finally:
            # Close Motor-CAD in each worker, then shut down the pool
            it = pool.imap(close_mcad, range(n_workers))
            for _ in range(n_workers):
                next(it)
            pool.close()
            pool.join()

        mat_data = {"sweep_results": sweep_results}
        savemat(str(mat_summary_path), mat_data, do_compression=True)
        print(f"\nSweep complete -- {len(sweep_results)} total records in summary.")
        print(f"  JSON: {json_summary_path}")
        print(f"  MAT:  {mat_summary_path}")
else:
    print("[Offline Mode] Bypassing FEA Sweep calculation loop.")


# %%[markdown]
# # [3-DEBUG] 독립 워커 진단 셀 — 셀1~8 없이 단독 실행 가능
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [3-DEBUG] 독립 워커 진단 셀 — 셀1~8 없이 단독 실행 가능
#
# 목적: _mcad_parallel_worker.py 함수들을 현재 프로세스(subprocess 없이)에서
#        직접 호출해 실제 에러 메시지와 traceback을 Jupyter 출력에 표시.
#
# 사용법:
#   - 이 셀만 단독으로 실행 가능 (셀1~8 안 돌려도 됨)
#   - 필요 시 아래 수동 설정 블록의 경로만 확인/수정
# ─────────────────────────────────────────────────────────────────────────────
import sys
import traceback
from pathlib import Path

# ── 수동 설정 (셀 1~8이 이미 실행됐다면 자동으로 해당 변수 재사용) ────────────
_mot_path   = str(globals().get('mot_path',
    Path(r'D:\KDH\simVary\e10_6TSweep\refModel\e10Turn6V261.mot')
))
_backup_root = str(globals().get('backup_root',
    Path(_mot_path).parent / 'ACLossCalcExport_Ref'
))
_R_active   = float(globals().get('R_active', 0.0))
_n_turns    = int(globals().get('n_turns',   6))
_n_parallel = int(globals().get('n_parallel', 1))

_TEST_POINT = {
    'prox_model':     3,          # 3=FullFEA, 1=Hybrid
    'speed':          2000,
    'current':        0.1,
    'phase':          0.0,
    'backup_root':    _backup_root,
    'first_step':     1,
    'export_columns': 'RegCode,Bx,By,A,J,Je,Hx,Hy,Mur',
    'n_turns':        _n_turns,
    'n_parallel':     _n_parallel,
    'R_active':       _R_active,
    'idx':            0,
    'total_pts':      1,
}

# ── sys.path 설정 (emach root 포함) ─────────────────────────────────────────
_repo_root = Path.cwd().resolve()
while _repo_root.name and _repo_root.name not in ('EveryMotor', 'NvidiaNemo'):
    _repo_root = _repo_root.parent
_emach_root = _repo_root / 'eMach'
_jeet_dir   = Path.cwd()
for _p in [str(_emach_root), str(_repo_root), str(_jeet_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

print(f'mot_path   : {_mot_path}')
print(f'backup_root: {_backup_root}')
print(f'.mot exists: {Path(_mot_path).exists()}')
print()

# ── Step 1: initialise_mcad ──────────────────────────────────────────────────
print('=' * 60)
print('Step 1: initialise_mcad')
print('=' * 60)
try:
    import importlib
    if '_mcad_parallel_worker' in sys.modules:
        importlib.reload(sys.modules['_mcad_parallel_worker'])
    from _mcad_parallel_worker import initialise_mcad, run_sweep_point
    initialise_mcad(_mot_path, sys.path[:])
    print('  -> initialise_mcad 성공')
except Exception:
    print('  [ERROR] initialise_mcad 실패 — traceback:')
    traceback.print_exc()
    raise SystemExit('initialise_mcad 실패로 Step 2 중단')

# ── Step 2: run_sweep_point ──────────────────────────────────────────────────
print()
print('=' * 60)
print('Step 2: run_sweep_point (테스트 포인트 1개)')
print('=' * 60)
print(f'  prox_model={_TEST_POINT["prox_model"]},  speed={_TEST_POINT["speed"]},  '
      f'current={_TEST_POINT["current"]},  phase={_TEST_POINT["phase"]}')
print()
try:
    result = run_sweep_point(_TEST_POINT)
    if result is None:
        print('  -> None 반환 (worker 내부 예외 -> 위 [ERROR] 줄 확인)')
    else:
        print('  -> 성공! 결과:')
        for k, v in result.items():
            print(f'    {k}: {v}')
except Exception:
    print('  [ERROR] run_sweep_point 예외:')
    traceback.print_exc()


# %%[markdown]
# # [3-POSTPROC] ts_ac_active_only_kW 후처리 — 기존 JSON 재계산
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [3-POSTPROC] 기존 JSON FullFEA 레코드 후처리
#
# 목적: 이미 저장된 JSON에서 FullFEA(proximity_model=3) 레코드의
#        ts_ac_active_only_kW 등을 _mcad_parallel_worker.py 최신 방식으로 재계산.
#        FEA 재실행 없이 현재 mcad 세션에서 R_active/R_end 읽어 DC 차감 적용.
# ─────────────────────────────────────────────────────────────────────────────
import json as _json
from tools.motorCAD.pyMCAD import calc_dc_loss_kw

# ── R_active, R_end 읽기 (MotorLAB context) ──────────────────────────────────
try:
    mcad.set_motorlab_context()
    _R_total  = float(mcad.get_variable('Resistance_MotorLAB'))
    _R_end    = float(mcad.get_variable('EndWindingResistance_Lab'))
    _R_active = _R_total - _R_end
    mcad.show_magnetic_context()
    print(f'R_total={_R_total:.6f} Ohm,  R_end={_R_end:.6f} Ohm,  R_active={_R_active:.6f} Ohm')
except Exception as _e:
    _R_active, _R_end = 0.0, 0.0
    print(f'[WARN] R read failed: {_e}  -> R_active=0 (no DC subtraction)')

# ── JSON 로드 ─────────────────────────────────────────────────────────────────
with open(json_summary_path, 'r', encoding='utf-8') as _f:
    _data = _json.load(_f)
_records = _data.get('records', _data) if isinstance(_data, dict) else _data
_meta    = _data.get('_meta', {})      if isinstance(_data, dict) else {}

# ── FullFEA 레코드 재계산 ─────────────────────────────────────────────────────
# 워커(_mcad_parallel_worker.py)와 동일한 계산식:
#   per_turn_sum_kw      = sum(ACLoss_FEA_OnLoad_PerTurn 파싱값) / 1000
#   dc_active_kw         = calc_dc_loss_kw(R_active, I)  # 3 x R_active x I^2 / 1000
#   ts_ac_active_only_kW = per_turn_sum_kw - dc_active_kw
_n_fixed = 0
for _r in _records:
    if _r.get('proximity_model') != 3:
        continue
    if _r.get('ts_ac_active_only_kW', 0.0) != 0.0:
        continue  # 이미 정상 값 -> 스킵

    _raw = _r.get('fea_per_turn_raw', '')
    try:
        _per_turn_w = [float(x) for x in (str(_raw).split(':') if isinstance(_raw, str) else list(_raw))]
        _per_turn_sum_kw = sum(_per_turn_w) / 1000.0
    except Exception:
        _per_turn_sum_kw = 0.0

    _current      = float(_r.get('current', 0.0))
    _dc_active_kw = calc_dc_loss_kw(_R_active, _current)
    _dc_end_kw    = calc_dc_loss_kw(_R_end,    _current)

    _r['fea_per_turn_sum_kW']  = _per_turn_sum_kw
    _r['ts_dc_active_kW']      = _dc_active_kw
    _r['ts_dc_end_kW']         = _dc_end_kw
    _r['ts_ac_active_only_kW'] = _per_turn_sum_kw - _dc_active_kw
    _n_fixed += 1

print(f'Fixed {_n_fixed} records  (R_active={_R_active:.6f} Ohm)')
if _n_fixed > 0:
    _s = next(r for r in _records if r.get('proximity_model') == 3)
    print(f'  sample: per_turn_sum={_s["fea_per_turn_sum_kW"]:.4f} kW,'
          f' fea_total={_s["fea_total_ac_kW"]:.4f} kW,'
          f' dc_act={_s["ts_dc_active_kW"]:.4f} kW,'
          f' ts_ac_only={_s["ts_ac_active_only_kW"]:.4f} kW')

# # ── 저장 ─────────────────────────────────────────────────────────────────────
_out = {'_meta': _meta, 'records': _records} if isinstance(_data, dict) else _records
with open(json_summary_path, 'w', encoding='utf-8') as _f:
    _json.dump(_out, _f, ensure_ascii=False, indent=2)
print(f'Saved -> {json_summary_path}')


# %%[markdown]
# # [3c] 비활성화된 보완 스윕 셀 (Cell 7로 통합)
#

# %%
# 이 셀은 통합 버전 스케줄러(Cell 7)로 합병되어 사용하지 않습니다.
print("통합 스케줄러 Cell 7이 사용됩니다.")


# %%[markdown]
# # [4] id-iq 평면 AC Active Only 손실 Surface 플롯 (속도별)
#
# ProximityLossModel = 1(Hybrid) 및 3(FullFEA/TS) 각각에 대해 속도별로 $I_d, I_q$ 평면에서의 AC Active Only 손실 Surface 플롯을 시각화합니다.

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [4] id-iq 평면 AC Active Only 손실 Surface 플롯 (대화형 비교)
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as mpatches

if json_summary_path.exists():
    with open(json_summary_path, "r", encoding="utf-8") as f:
        sweep_results = json.load(f)
    
    hybrid_data = [p for p in sweep_results if p["proximity_model"] == 1]
    ts_data = [p for p in sweep_results if p["proximity_model"] == 3]
    
    def process_pts(pts, is_hybrid):
        speeds = np.array([p["speed"] for p in pts])
        currents = np.array([p["current"] for p in pts])
        phases = np.array([p["phase"] for p in pts])
        
        amplitude = currents * np.sqrt(2)
        phase_rad = (phases + 90) * np.pi / 180.0
        id_vals = amplitude * np.cos(phase_rad)
        iq_vals = amplitude * np.sin(phase_rad)
        
        if is_hybrid:
            losses = np.array([p["hybrid_total_kW"] for p in pts])
        else:
            losses = np.array([p["ts_ac_active_only_kW"] for p in pts])
            
        return speeds, id_vals, iq_vals, losses, pts

    speed_colors = {2000: 'cyan', 4000: 'limegreen', 8000: 'orange', 16000: 'tomato'}
    default_colors = ['cyan', 'limegreen', 'orange', 'tomato']
    
    def create_interactive_comparison_plot(pts_hybrid, pts_ts):
        speeds_h, id_h, iq_h, losses_h, raw_h = process_pts(pts_hybrid, is_hybrid=True)
        speeds_f, id_f, iq_f, losses_f, raw_f = process_pts(pts_ts, is_hybrid=False)
        
        currents_h = np.array([p["current"] for p in raw_h])
        phases_h = np.array([p["phase"] for p in raw_h])
        currents_f = np.array([p["current"] for p in raw_f])
        phases_f = np.array([p['phase'] for p in raw_f])
        
        unique_speeds = sorted(list(set(speeds_h)))
        
        fig = plt.figure(figsize=(18, 5.5))
        fig.suptitle(f"AC Loss Comparison Map ({MODEL_SCALE}): Hybrid vs FullFEA", fontsize=13, fontweight='bold')
        
        ax_left = fig.add_subplot(131, projection='3d')
        ax_left.set_title("Hybrid (ProximityLossModel = 1)", fontsize=11, fontweight='bold')
        ax_mid = fig.add_subplot(132, projection='3d')
        ax_mid.set_title("FullFEA (ProximityLossModel = 3)", fontsize=11, fontweight='bold')
        
        legend_patches_h = []
        legend_patches_f = []
        
        for i, spd in enumerate(unique_speeds):
            color = speed_colors.get(spd, default_colors[i % len(default_colors)])
            idx_h = (speeds_h == spd)
            if np.any(idx_h) and np.sum(idx_h) >= 3:
                ax_left.plot_trisurf(id_h[idx_h], iq_h[idx_h], losses_h[idx_h], color=color, edgecolor='none', alpha=0.35)
                legend_patches_h.append(mpatches.Patch(color=color, alpha=0.35, label=f"{spd} RPM"))
            idx_f = (speeds_f == spd)
            if np.any(idx_f) and np.sum(idx_f) >= 3:
                ax_mid.plot_trisurf(id_f[idx_f], iq_f[idx_f], losses_f[idx_f], color=color, edgecolor='none', alpha=0.35)
                legend_patches_f.append(mpatches.Patch(color=color, alpha=0.35, label=f"{spd} RPM"))
                
        sc_h = ax_left.scatter(id_h, iq_h, losses_h, c='grey', s=25, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
        sc_f = ax_mid.scatter(id_f, iq_f, losses_f, c='grey', s=25, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
        scatters = [sc_h, sc_f]
        
        for ax, lp in [(ax_left, legend_patches_h), (ax_mid, legend_patches_f)]:

            ax.set_xlabel("I_d [A]", fontsize=8, labelpad=7)
            ax.set_ylabel("I_q [A]", fontsize=8, labelpad=7)
            ax.set_zlabel("AC Loss [kW]", fontsize=8, labelpad=7)
            ax.legend(handles=lp, fontsize=8, loc="upper right")
            
        ax_right = fig.add_subplot(133)
        ax_right.text(0.5, 0.5, "3D 플롯에서 임의의 점을 클릭한 후\nSpacebar를 누르면 속도별 비교 곡선이 출력됩니다.", 
                     ha="center", va="center", fontsize=10, color="gray")
        ax_right.set_xlabel("Speed [RPM]", fontsize=9)
        ax_right.set_ylabel("AC Loss [kW]", fontsize=9)
        ax_right.grid(True, linestyle="--", alpha=0.5)
        
        selected_pt = {"current": None, "phase": None, "id": None, "iq": None}
        highlights_h = []
        highlights_f = []
        
        annotation_h = ax_left.text2D(0.02, 0.95, "", transform=ax_left.transAxes, 
                                      bbox=dict(boxstyle="round", fc="w", alpha=0.8), fontsize=8)
        annotation_f = ax_mid.text2D(0.02, 0.95, "", transform=ax_mid.transAxes, 
                                     bbox=dict(boxstyle="round", fc="w", alpha=0.8), fontsize=8)
        annotation_h.set_visible(False)
        annotation_f.set_visible(False)
        
        def on_pick(event):
            if event.artist not in scatters:
                return
            idx = event.ind[0]
            if event.artist == sc_h:
                curr, ph = raw_h[idx]["current"], raw_h[idx]["phase"]
            else:
                curr, ph = raw_f[idx]["current"], raw_f[idx]["phase"]
            selected_pt["current"] = curr
            selected_pt["phase"] = ph
            amp = curr * np.sqrt(2)
            phase_rad = (ph + 90) * np.pi / 180.0
            selected_pt["id"] = amp * np.cos(phase_rad)
            selected_pt["iq"] = amp * np.sin(phase_rad)
            for h in highlights_h + highlights_f:
                h.remove()
            highlights_h.clear()
            highlights_f.clear()
            same_h_idx = (currents_h == curr) & (phases_h == ph)
            hh = ax_left.scatter(id_h[same_h_idx], iq_h[same_h_idx], losses_h[same_h_idx], 
                                 color='red', s=70, edgecolors='black', linewidths=1.8, zorder=10)
            highlights_h.append(hh)
            same_f_idx = (currents_f == curr) & (phases_f == ph)
            hf = ax_mid.scatter(id_f[same_f_idx], iq_f[same_f_idx], losses_f[same_f_idx], 

                                color='red', s=70, edgecolors='black', linewidths=1.8, zorder=10)
            highlights_f.append(hf)
            msg = (f"Selected: I_rms={curr:.1f}A, Phase={ph:.1f}°\n"

                   f"Id={selected_pt['id']:.1f}A, Iq={selected_pt['iq']:.1f}A\n→ Press 'Space'")
            for annot in [annotation_h, annotation_f]:
                annot.set_text(msg)
                annot.set_visible(True)
            fig.canvas.draw_idle()
            
        def on_key(event):
            if event.key != ' ' or selected_pt["current"] is None:
                return
            ax_right.clear()
            curr, ph = selected_pt["current"], selected_pt["phase"]
            curve_speeds, curve_losses_h, curve_losses_f = [], [], []
            for spd in unique_speeds:
                match_h = [p for p in raw_h if p["speed"] == spd and np.isclose(p["current"], curr) and np.isclose(p["phase"], ph)]
                match_f = [p for p in raw_f if p["speed"] == spd and np.isclose(p["current"], curr) and np.isclose(p["phase"], ph)]
                if match_h and match_f:
                    curve_speeds.append(spd)
                    curve_losses_h.append(match_h[0]["hybrid_total_kW"])
                    curve_losses_f.append(match_f[0]["ts_ac_active_only_kW"])
            ax_right.plot(curve_speeds, curve_losses_h, marker='o', linestyle='-', color='dodgerblue', linewidth=2, label="Hybrid AC Total")
            ax_right.plot(curve_speeds, curve_losses_f, marker='*', linestyle='--', color='crimson', linewidth=2, label="FullFEA AC Active Only")
            for xs, yh, yf in zip(curve_speeds, curve_losses_h, curve_losses_f):
                ax_right.annotate(f"{yh:.2f}", xy=(xs, yh), xytext=(4, 4), textcoords="offset points", fontsize=8, color="dodgerblue")
                ax_right.annotate(f"{yf:.2f}", xy=(xs, yf), xytext=(4, -12), textcoords="offset points", fontsize=8, color="crimson")
            ax_right.set_title(f"AC Loss vs Speed\n(I_rms={curr:.1f}A, Phase={ph:.1f}°)", fontsize=11, fontweight='bold')
            ax_right.set_xlabel("Speed [RPM]", fontsize=9)
            ax_right.set_ylabel("AC Loss [kW]", fontsize=9)
            ax_right.grid(True, linestyle="--", alpha=0.5)
            ax_right.legend(fontsize=9, loc="upper left")
            fig.canvas.draw_idle()
            
        fig.canvas.mpl_connect('pick_event', on_pick)
        fig.canvas.mpl_connect('key_press_event', on_key)
        plt.tight_layout()
        plt.show()
        
    if len(hybrid_data) > 0 and len(ts_data) > 0:
        create_interactive_comparison_plot(hybrid_data, ts_data)
    else:
        print("Error: Need both Hybrid and FullFEA data.")
else:
    print("JSON summary map file not found. Bypassing map surface plotting cell.")


# %%


# %%[markdown]
# # [5] Adjustment Factor (AF) 모델링
#
# `AF = FullFEA_AC_active_only / Hybrid_AC_total`을 **(speed, Irms, phase)** 기반으로 모델링합니다.
#
# **AF에 영향을 주는 물리적 인자:**
# - **Skin effect**: 고속(고주파수) 영역에서 주파수 자승 비선형성이 꺾이는 와전류 차폐(Back-reaction) 경향을 보정합니다.
# - **Proximity effect**: 고정자 전류 크기($I_{rms}$) 및 고정자 전류와 회전자 극 간의 상대 위상각($\theta$)에 의한 AC 손실 비선형 곡면을 피팅합니다.
# - **Id-Iq 결합**:MTPA 운전 궤적 및 field-weakening 영역에서의 AC 손실 거동을 전류 크기와 위상각을 통해 정합시킵니다.
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [5] Adjustment Factor (AF) 데이터 로드 및 정렬 (RBF 입력용)
#
# 목적:
#   Hybrid 해석 결과(proximity_model=1)와 FullFEA 결과(proximity_model=3)를
#   (speed, current, phase) 좌표로 매칭한 뒤,
#   AF = FullFEA_AC / Hybrid_AC 를 계산하여 RBF 보간 입력 데이터(af_points)를 구성
# ─────────────────────────────────────────────────────────────────────────────

# ── Step 1: JSON 로드 ─────────────────────────────────────────────────────────
# sweep_results: [{"proximity_model": 1or3, "speed":..., "current":..., ...}, ...]
if json_summary_path.exists():
    print(f"[데이터 로드] {json_summary_path}")
    with open(json_summary_path, "r", encoding="utf-8") as f:
        sweep_results = json.load(f)

    # ── Step 2: 모델 일치 검증 ──────────────────────────────────────────────────
    # backup_dir 경로에 MODEL_SCALE 키워드가 있는지 확인
    # 다른 스케일 결과가 섞여 있으면 AF 계산이 잘못될 수 있음
    model_keywords = {
        'Ref':    ['refModel', 'ref'],
        'HalfSC': ['SLFEA_Half', 'HalfSC'],
        'SC':     ['SLFEA', 'SC']
    }
    kws = model_keywords.get(MODEL_SCALE, [])
    _non_matching = [p for p in sweep_results
                     if "backup_dir" in p and not any(kw in p["backup_dir"] for kw in kws)]
    if _non_matching:
        print(f"  [WARNING] {len(_non_matching)}개 포인트가 {MODEL_SCALE} 모형이 아닐 수 있습니다!")
        print(f"  예: {_non_matching[0]['backup_dir']}")
    else:
        print(f"  [OK] 전체 {len(sweep_results)}포인트 {MODEL_SCALE} 모형 일치성 확인")

    _speeds = sorted(set(p["speed"] for p in sweep_results))
    print(f"  속도: {_speeds} RPM, 총 {len(sweep_results)}포인트")
else:
    raise RuntimeError(
        f"[ERROR] JSON 파일을 찾을 수 없습니다: {json_summary_path}\n"
    )

# ── Step 3: Hybrid / FullFEA 분리 ─────────────────────────────────────────────
# proximity_model=1 : Hybrid (빠른 해석, 근접 효과 분리 불가)
# proximity_model=3 : FullFEA Transient (느리지만 실제 AC 손실 기준)
hybrid_data = [p for p in sweep_results if p["proximity_model"] == 1]
ts_data     = [p for p in sweep_results if p["proximity_model"] == 3]
print(f"Hybrid: {len(hybrid_data)}개,  FullFEA: {len(ts_data)}개")

# ── Step 4: (speed, current, phase) 매칭 및 AF 계산 ──────────────────────────
# AF(s, I, γ) = FullFEA_AC_kW / Hybrid_AC_kW
#   - FullFEA 가 기준(truth), Hybrid 를 보정하는 factor
#   - AF > 1 : Hybrid 가 실제보다 과소평가
#   - AF < 1 : Hybrid 가 실제보다 과대평가
af_points = []
for ts_pt in ts_data:
    spd  = ts_pt["speed"]    # [RPM]
    curr = ts_pt["current"]  # [A rms]
    ph   = ts_pt["phase"]    # [deg] Motor-CAD PhaseAdvance (q축 기준 전류 진각)

    # 동일 운전점의 Hybrid 레코드 검색 (전류/위상은 부동소수 비교)
    matches = [p for p in hybrid_data
               if p["speed"] == spd
               and np.isclose(p["current"], curr, atol=1e-2)
               and np.isclose(p["phase"],   ph,   atol=1e-2)]
    if not matches:
        continue           # Hybrid 결과 없으면 이 포인트 건너뜀
    h_pt = matches[0]

    h_ac = h_pt["hybrid_total_kW"]       # Hybrid 전체 AC 손실 [kW]
    f_ac = ts_pt["ts_ac_active_only_kW"] # FullFEA Active 부위 AC 손실 [kW]
                                          # (DC 차감 + 엔드와인딩 제외)
    if h_ac < 1e-4:
        continue  # Hybrid 값이 0에 가까우면 AF가 발산 → 스킵

    af = f_ac / h_ac  # Adjustment Factor (무차원)

    # ── Step 5: dq 좌표 변환 ─────────────────────────────────────────────────
    # Motor-CAD PhaseAdvance(γ)는 q축으로부터의 전류 진각 [deg]
    # d축 기준 각도 = γ + 90°  →  id = I√2 · cos(γ+90°), iq = I√2 · sin(γ+90°)
    # 결과: id = -I√2 · sin(γ)  (field weakening 시 음수),  iq = I√2 · cos(γ)
    amp    = curr * np.sqrt(2)                        # 피크 전류 [A]
    ph_rad = (ph + 90.0) * np.pi / 180.0             # q축 → d축 기준 변환
    id_a   = amp * np.cos(ph_rad)                    # d축 전류 [A, 피크]
    iq_a   = amp * np.sin(ph_rad)                    # q축 전류 [A, 피크]

    af_points.append({
        "speed_rpm":    spd,
        "speed_kRPM":   spd / 1000.0,
        "current_rms":  curr,
        "phase_deg":    ph,
        "id_A":         id_a,
        "iq_A":         iq_a,
        "hybrid_ac_kW": h_ac,
        "fea_ac_kW":    f_ac,
        "AF":           af,
    })

print(f"AF 매칭 계산 완료: {len(af_points)}개 운전점")
print(f"AF 범위: min={min(p['AF'] for p in af_points):.4f},  "
      f"max={max(p['AF'] for p in af_points):.4f},  "
      f"mean={np.mean([p['AF'] for p in af_points]):.4f}")


# %%[markdown]
# # [5.5] 방법 B: RBF 모델 비교 (3D TPS RBF vs. 1D x 2D 차원 분리형 RBF)
#
# 이 단계에서는 두 가지 유형의 글로벌 Thin-Plate Spline (TPS) RBF 대리 모델을 동시 수립합니다:
#
# 1. **3D TPS RBF 모델 (Full Interpolation)**:
#    - 속도, 전류, 위상각 3차원 입력에 대해 106개 데이터 포인트를 모두 RBF 센터로 삼아 완벽히 매칭하는 모델입니다. 
#    - 훈련 오차는 0%에 수렴하지만, Motor-CAD Lab 식의 길이가 다소 길어집니다 (~28k 캐릭터).
#
# 2. **1D x 2D 차원 분리형 스케일링 모델 (Separable Scaling Model)**:
#    - 단일 속도(2.0 kRPM)의 30개 점으로 2D TPS RBF인 $g(I, \theta)$ 형상을 먼저 피팅하고, 속도 증가에 따른 스케일링 배율 $f(speed)$을 다른 속도 영역의 12개 대표 점으로 평균/2차 다항식 피팅하는 모델입니다.
#    - 수식이 30개 항으로 압축되어 매우 슬림하고 (~5.5k 캐릭터), 데이터 공백에서의 과적합 없이 안정적으로 동작합니다.
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [5.5] 방법 B: 두 가지 RBF 모델 동시 수립 (3D TPS RBF 및 1D x 2D Separable RBF)
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np

# ── 데이터 준비 ──────────────────────────────────────────────────────────────
speeds_k  = np.array([p["speed_kRPM"]  for p in af_points])
irms_arr  = np.array([p["current_rms"] for p in af_points])   # Irms [A]
phase_arr = np.array([p["phase_deg"]   for p in af_points])   # phase advance [deg]
af_arr    = np.array([p["AF"]          for p in af_points])
id_arr    = np.array([p["id_A"]        for p in af_points])
iq_arr    = np.array([p["iq_A"]        for p in af_points])
curr_arr  = irms_arr.copy()
X_data    = np.column_stack([speeds_k, irms_arr, phase_arr])

# ── ARD 길이 스케일 (변수별 표준편차) ────────────────────────────────────────
LS_S = float(speeds_k.std())
LS_I = float(irms_arr.std())
LS_P = float(phase_arr.std())
print(f"  길이 스케일: ls_s={LS_S:.3f} kRPM | ls_I={LS_I:.1f} A | ls_P={LS_P:.2f} deg")

LAM = 1e-6

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 1: 3D TPS RBF 모델 피팅 (106개 전체 센터)
# ─────────────────────────────────────────────────────────────────────────────
def _rbf_k_3d(s, irms, ph, s_c, i_c, p_c):
    r2 = (s - s_c)**2 / LS_S**2 + (irms - i_c)**2 / LS_I**2 + (ph - p_c)**2 / LS_P**2
    r = np.sqrt(r2)
    return r2 * np.log(r + 1e-12)

n = len(af_arr)
Phi_3d = np.zeros((n, n))
for j in range(n):
    Phi_3d[:, j] = _rbf_k_3d(speeds_k, irms_arr, phase_arr,
                             speeds_k[j], irms_arr[j], phase_arr[j])

rbf_weights_3d = np.linalg.solve(Phi_3d + LAM * np.eye(n), af_arr)

def af_from_rbf_3d(speed_rpm, irms_a, phase_deg):
    s   = np.asarray(speed_rpm, float) / 1000.0
    irm = np.asarray(irms_a,    float)
    ph  = np.asarray(phase_deg, float)
    s, irm, ph = np.broadcast_arrays(s, irm, ph)
    orig = s.shape
    sv, irmv, phv = s.ravel()[:, None], irm.ravel()[:, None], ph.ravel()[:, None]
    
    r2 = (sv - speeds_k)**2 / LS_S**2 + (irmv - irms_arr)**2 / LS_I**2 + (phv - phase_arr)**2 / LS_P**2
    r = np.sqrt(r2)
    K = r2 * np.log(r + 1e-12)
    result = K @ rbf_weights_3d
    return result.reshape(orig) if orig else float(result[0])

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 2: 1D x 2D Separable RBF 모델 피팅
# ─────────────────────────────────────────────────────────────────────────────
base_idx = np.where(np.abs(speeds_k - 2.0) < 0.1)[0]
speeds_k_base = speeds_k[base_idx]
irms_arr_base = irms_arr[base_idx]
phase_arr_base = phase_arr[base_idx]
af_arr_base = af_arr[base_idx]

def _rbf_2d_k(irms, ph, i_c, p_c):
    r2 = (irms - i_c)**2 / LS_I**2 + (ph - p_c)**2 / LS_P**2
    r = np.sqrt(r2)
    return r2 * np.log(r + 1e-12)

n_base = len(base_idx)
Phi_g = np.zeros((n_base, n_base))
for j in range(n_base):
    Phi_g[:, j] = _rbf_2d_k(irms_arr_base, phase_arr_base,
                            irms_arr_base[j], phase_arr_base[j])

w_g = np.linalg.solve(Phi_g + LAM * np.eye(n_base), af_arr_base)

def predict_g(I, theta):
    I = np.asarray(I, float)
    theta = np.asarray(theta, float)
    I, theta = np.broadcast_arrays(I, theta)
    orig = I.shape
    Iv, thv = I.ravel()[:, None], theta.ravel()[:, None]
    
    r2 = (Iv - irms_arr_base)**2 / LS_I**2 + (thv - phase_arr_base)**2 / LS_P**2
    r = np.sqrt(r2)
    K = r2 * np.log(r + 1e-12)
    result = K @ w_g
    return result.reshape(orig) if orig else float(result[0])

# 1D 속도 배율 f(speed) 구하기 (4k, 8k, 16k RPM의 속도별 4점 사용)
other_speeds = [4.0, 8.0, 16.0]
target_currents = [115.0, 230.0, 345.0, 460.0]
selected_other_idx = []
for spd in other_speeds:
    spd_idx = np.where(np.abs(speeds_k - spd) < 0.1)[0]
    for i_val in target_currents:
        diffs = (irms_arr[spd_idx] - i_val)**2
        best_idx = spd_idx[np.argmin(diffs)]
        selected_other_idx.append(best_idx)
selected_other_idx = np.unique(selected_other_idx)

f_vals = []
for idx in selected_other_idx:
    spd = speeds_k[idx]
    I_val = irms_arr[idx]
    th_val = phase_arr[idx]
    af_actual = af_arr[idx]
    g_val = predict_g(I_val, th_val)
    f_val = af_actual / (g_val + 1e-12)
    f_vals.append((spd, f_val))

f_by_speed = {2.0: [1.0]}
for spd, f_val in f_vals:
    if spd not in f_by_speed:
        f_by_speed[spd] = []
    f_by_speed[spd].append(f_val)

speed_coords = []
f_coords = []
for spd in sorted(f_by_speed.keys()):
    speed_coords.append(spd)
    f_coords.append(np.mean(f_by_speed[spd]))

p_coeffs = np.polyfit(speed_coords, f_coords, 2)
p_func = np.poly1d(p_coeffs)

def af_from_rbf_separable(speed_rpm, irms_a, phase_deg):
    s = np.asarray(speed_rpm, float) / 1000.0
    irm = np.asarray(irms_a, float)
    ph = np.asarray(phase_deg, float)
    s, irm, ph = np.broadcast_arrays(s, irm, ph)
    orig = s.shape
    sv, irmv, phv = s.ravel(), irm.ravel(), ph.ravel()
    
    g_vals = predict_g(irmv, phv)
    f_vals = p_func(sv)
    result = f_vals * g_vals
    return result.reshape(orig) if orig else float(result[0])

# ── 기본 보정 함수 설정 (Separable 방식을 기본으로 사용) ──────────────────
def af_from_rbf(speed_rpm, irms_a, phase_deg):
    return af_from_rbf_separable(speed_rpm, irms_a, phase_deg)

# 다운스트림 호환용
def af_from_poly3d(speed_rpm, id_peak_a, iq_peak_a):
    idv = np.asarray(id_peak_a, float)
    iqv = np.asarray(iq_peak_a, float)
    irms  = np.sqrt(idv**2 + iqv**2) / np.sqrt(2)
    phase = np.degrees(np.arctan2(iqv, idv)) - 90.0
    return af_from_rbf(speed_rpm, irms, phase)

print("  af_from_rbf_3d() 및 af_from_rbf_separable() 수립 완료 (Separable 기본 활성화)")

# ── 3. Motor-CAD Lab 수식 포맷 ───────────────────────────────────────────────
# (1) 3D RBF 식 (106개 센터)
terms_3d = []
for j in range(n):
    w, s_c, i_c, p_c = rbf_weights_3d[j], speeds_k[j], irms_arr[j], phase_arr[j]
    r2_expr = f"((Speed/1000-{s_c:.4f})**2/{LS_S**2:.4f}+(Stator_Current_Phase_RMS-{i_c:.4f})**2/{LS_I**2:.4f}+(Phase_Advance-{p_c:.4f})**2/{LS_P**2:.4f})"
    term = f"({w:+.6f})*({r2_expr})*log({r2_expr}**0.5+1e-12)"
    terms_3d.append(term)
rbf_formula_3d = "Stator_Copper_Loss_AC * (\n  " + "\n  + ".join(terms_3d) + "\n) - Stator_Copper_Loss_AC"

# (2) Separable 식 (30개 센터)
terms_g = []
for j in range(n_base):
    w, i_c, p_c = w_g[j], irms_arr_base[j], phase_arr_base[j]
    r2_expr = f"((Stator_Current_Phase_RMS-{i_c:.4f})**2/{LS_I**2:.4f}+(Phase_Advance-{p_c:.4f})**2/{LS_P**2:.4f})"
    term = f"({w:+.6f})*({r2_expr})*log({r2_expr}**0.5+1e-12)"
    terms_g.append(term)
g_expr = " + ".join(terms_g)
f_expr = f"({p_coeffs[0]:+.6f}*(Speed/1000)**2{p_coeffs[1]:+.6f}*(Speed/1000){p_coeffs[2]:+.6f})"
rbf_formula_separable = "Stator_Copper_Loss_AC * (\n  " + f"({f_expr}) * (\n    {g_expr}\n  )" + "\n) - Stator_Copper_Loss_AC"

rbf_formula = rbf_formula_separable


# %%
# ─────────────────────────────────────────────────────────────────────────────
# [6] 방법 A: AF(speed) 속도만 2차 다항식 + AF vs Speed 시각화
# ─────────────────────────────────────────────────────────────────────────────
try:
    get_ipython().run_line_magic('matplotlib', 'inline')
except Exception:
    pass

import numpy as np
import matplotlib.pyplot as plt

# ── 방법 A 피팅: 최대 전류에서 속도만의 2차 다항식 ──────────────────────────
max_curr     = curr_arr.max()
mask_maxcurr = np.isclose(curr_arr, max_curr, rtol=0.01)
spd_mc, af_mc = speeds_k[mask_maxcurr], af_arr[mask_maxcurr]

sort_idx = np.argsort(spd_mc)
spd_mc, af_mc = spd_mc[sort_idx], af_mc[sort_idx]

coeffs_A = np.polyfit(spd_mc, af_mc, deg=2)
af_A_fit = np.polyval(coeffs_A, spd_mc)
a2, a1, a0 = coeffs_A
_coeff_A = coeffs_A.copy()

def af_from_speed_only(speed_rpm):
    return np.polyval(_coeff_A, np.asarray(speed_rpm, float) / 1000.0)

lab_formula_extra = (
    f"(({a2:.6f}*(Speed/1000)^2 + {a1:.6f}*(Speed/1000) + {a0:.6f}) - 1)"
    f" * Stator_Copper_Loss_AC"
)

print("=== 방법 A: 속도만의 2차 다항식 (최대 전류 기준) ===")
print(f"  I_rms = {max_curr:.1f} A 기준")
print(f"  AF(s) = {a2:.6f}\u00b7s\u00b2 + {a1:.6f}\u00b7s + {a0:.6f}   (s: kRPM)\n")
for s, ref, fit in zip(spd_mc, af_mc, af_A_fit):
    print(f"    {s:.0f} kRPM: AF_ref={ref:.3f}, AF_fit={fit:.3f}, \u0394={fit-ref:+.3f}")
print(f"\n  [Motor-CAD Lab \uc218\uc2dd]\n  {lab_formula_extra}")

# ── AF vs Speed 시각화 ──────────────────────────────────────────────────────
unique_currents_s = sorted(set(round(p["current_rms"], 0) for p in af_points))
unique_phases_s   = sorted(set(round(p["phase_deg"],   0) for p in af_points))
unique_speeds_s   = sorted(set(p["speed_rpm"] for p in af_points))

n_curr_s  = len(unique_currents_s)
colors_s  = [plt.cm.plasma(i / max(1, n_curr_s - 1)) for i in range(n_curr_s)]
lstyles_s = ['-', '--', '-.', ':', (0, (3, 1, 1, 1)), (0, (5, 5))]

fig, ax = plt.subplots(figsize=(11, 6))
ax.set_title("Adjustment Factor  AF = FullFEA_AC / Hybrid_AC  vs Speed (\uc6b4\uc804\uc810\ubcc4)",
             fontsize=12, fontweight='bold')

for ki, curr in enumerate(unique_currents_s):
    for li, ph in enumerate(unique_phases_s):
        pts = sorted(
            [p for p in af_points
             if np.isclose(p["current_rms"], curr, atol=0.6)
             and np.isclose(p["phase_deg"],  ph,   atol=0.6)],
            key=lambda x: x["speed_rpm"]
        )
        if len(pts) < 2:
            continue
        spds = [p["speed_rpm"] for p in pts]
        afs  = [p["AF"]        for p in pts]
        ax.plot(spds, afs,
                marker='o', markersize=5,
                linestyle=lstyles_s[li % len(lstyles_s)],
                color=colors_s[ki], linewidth=1.5,
                label=f"I={curr:.0f} A, \u03c6={ph:.0f}\u00b0")

spd_fit  = np.linspace(min(unique_speeds_s) * 0.9, max(unique_speeds_s) * 1.05, 300)
af_fit_A = af_from_speed_only(spd_fit)
eq_str = f"y = {a2:.4f}\u00b7x\u00b2 {a1:+.4f}\u00b7x {a0:+.4f}  (x: kRPM)"
ax.plot(spd_fit, af_fit_A, 'k--', linewidth=2.5,
        label=f"Poly-A fit (I_max={max_curr:.0f} A)")
ax.text(0.97, 0.97, eq_str, transform=ax.transAxes, fontsize=9,
        va='top', ha='right', bbox=dict(boxstyle='round', fc='white', alpha=0.85))

ax.axhline(y=1.0, color='green', linestyle=':', linewidth=1.5, alpha=0.7, label="AF = 1")
ax.set_xlabel("Speed [RPM]", fontsize=11)
ax.set_ylabel("Adjustment factor [-]", fontsize=11)
ax.legend(fontsize=7.5, loc='upper right', ncol=2, framealpha=0.9)
ax.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig("map_exports/AF_vs_speed_curves.png", dpi=150, bbox_inches='tight')
plt.show()
print("\uc800\uc7a5: map_exports/AF_vs_speed_curves.png")


# %%[markdown]
# # [6.5] 방법 B 시각화: id-iq 평면 AF 분포 (분리형 RBF)
#
# 속도별 id-iq 평면에서의 AF 예측 거동 및 분리형 RBF 곡면을 시각화합니다.
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [6.5] 방법 B 시각화: id-iq 평면 AF 맵 (속도별)
# ─────────────────────────────────────────────────────────────────────────────
try:
    get_ipython().run_line_magic('matplotlib', 'inline')
except Exception:
    pass

import numpy as np
import matplotlib.pyplot as plt

unique_speeds_v = sorted(set(p["speed_rpm"] for p in af_points))
n_spd_v = len(unique_speeds_v)

fig, axes = plt.subplots(1, n_spd_v, figsize=(5.2 * n_spd_v, 4.8))
if n_spd_v == 1:
    axes = [axes]
fig.suptitle("Adjustment Factor  AF = FullFEA_AC / Hybrid_AC  (id-iq 평면)",
             fontsize=13, fontweight='bold')

af_vals_all = np.array([p["AF"] for p in af_points])
vmin_af = max(0.5, af_vals_all.min() - 0.1)
vmax_af = af_vals_all.max() + 0.1

for ax, spd in zip(axes, unique_speeds_v):
    pts  = [p for p in af_points if p["speed_rpm"] == spd]
    id_v = np.array([p["id_A"] for p in pts])
    iq_v = np.array([p["iq_A"] for p in pts])
    af_v = np.array([p["AF"]   for p in pts])

    sc = ax.scatter(id_v, iq_v, c=af_v, cmap='plasma', s=90,
                    edgecolors='k', linewidths=0.6,
                    vmin=vmin_af, vmax=vmax_af, zorder=3)
    for x, y, a in zip(id_v, iq_v, af_v):
        ax.annotate(f"{a:.2f}", (x, y), textcoords="offset points",
                    xytext=(5, 4), fontsize=7.5, color='black')

    pad = 80
    id_g = np.linspace(id_v.min() - pad, id_v.max() + pad, 50)
    iq_g = np.linspace(max(0, iq_v.min() - pad), iq_v.max() + pad, 50)
    ID, IQ = np.meshgrid(id_g, iq_g)
    AF_fit = af_from_poly3d(spd, ID.ravel(), IQ.ravel()).reshape(ID.shape)
    ct = ax.contour(ID, IQ, AF_fit, levels=8, cmap='coolwarm', alpha=0.65, linewidths=0.9)
    ax.clabel(ct, fmt="%.2f", fontsize=7.5)

    plt.colorbar(sc, ax=ax, label="AF [-]", shrink=0.85)
    ax.set_xlabel("$I_d$ [A, peak]", fontsize=9)
    ax.set_ylabel("$I_q$ [A, peak]", fontsize=9)
    ax.set_title(f"{spd/1000:.0f} kRPM", fontsize=11, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig("map_exports/AF_map_visualization.png", dpi=150, bbox_inches='tight')
plt.show()
print("저장 완료: map_exports/AF_map_visualization.png")


# %%
# ─────────────────────────────────────────────────────────────────────────────
# [6.6] 방법 B 3D 표면 시각화: AF(id, iq) 곡면 (속도별)
# ─────────────────────────────────────────────────────────────────────────────
try:
    get_ipython().run_line_magic("matplotlib", "inline")
except Exception:
    pass

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

unique_speeds_v = sorted(set(p["speed_rpm"] for p in af_points))
n_spd_v = len(unique_speeds_v)

fig = plt.figure(figsize=(5.5 * n_spd_v, 5.0))
fig.suptitle("AF Surface: AF(Id, Iq) 방법 B 3D 곡면 (속도별)", fontsize=13, fontweight="bold")

for k, spd in enumerate(unique_speeds_v):
    ax = fig.add_subplot(1, n_spd_v, k + 1, projection="3d")

    pts  = [p for p in af_points if p["speed_rpm"] == spd]
    id_v = np.array([p["id_A"] for p in pts])
    iq_v = np.array([p["iq_A"] for p in pts])
    af_v = np.array([p["AF"]   for p in pts])

    pad = 80
    id_g = np.linspace(id_v.min() - pad, id_v.max() + pad, 50)
    iq_g = np.linspace(max(0, iq_v.min() - pad), iq_v.max() + pad, 50)
    ID, IQ = np.meshgrid(id_g, iq_g)
    AF_fit = af_from_poly3d(spd, ID, IQ)

    surf = ax.plot_surface(ID, IQ, AF_fit, cmap="plasma", alpha=0.75,
                           linewidth=0, antialiased=True)
    ax.scatter(id_v, iq_v, af_v, c="red", s=60,
               edgecolors="k", linewidths=0.6, zorder=5, label="FEA data")

    fig.colorbar(surf, ax=ax, shrink=0.55, label="AF [-]")
    ax.set_xlabel("Id [A]", fontsize=8)
    ax.set_ylabel("Iq [A]", fontsize=8)
    ax.set_zlabel("AF [-]", fontsize=8)
    ax.set_title(f"{spd/1000:.0f} kRPM", fontsize=11, fontweight="bold")
    ax.view_init(elev=25, azim=-60)

plt.tight_layout()
plt.savefig("map_exports/AF_3D_surface.png", dpi=150, bbox_inches="tight")
plt.show()
print("저장 완료: map_exports/AF_3D_surface.png")


# %%[markdown]
# # [7] 대리 모델 성능 비교 및 시각화
#
# - 3D TPS RBF 모델과 1D x 2D Separable RBF 모델의 예측 오차(Train MAE 및 Leave-One-Out CV 오차)를 직접 비교합니다.
# - 두 모델의 예측 데이터 Parity Plot 및 3-way Boxplot을 생성하여 비교 시각화하고 최종 JSON 데이터를 내보냅니다.
#

# %%
# ─────────────────────────────────────────────────────────────────────────────
# [7] RBF 모델 비교 검증: 3D TPS RBF vs. 1D x 2D Separable RBF vs. FullFEA
# ─────────────────────────────────────────────────────────────────────────────
try:
    get_ipython().run_line_magic('matplotlib', 'inline')
except Exception:
    pass

import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path

print(f"=== RBF 보정 오차 검증 및 비교: 3D RBF vs Separable vs FullFEA ({MODEL_SCALE}) ===\n")

h_ac_arr = np.array([p["hybrid_ac_kW"] for p in af_points])
f_ac_arr = np.array([p["fea_ac_kW"] for p in af_points])

# ── 훈련 세트 오차 계산
err_raw, err_3d, err_sep = [], [], []
rows = []
for p in af_points:
    spd   = p["speed_rpm"]
    irms  = p["current_rms"]
    phase = p["phase_deg"]
    h_ac  = p["hybrid_ac_kW"]
    f_ac  = p["fea_ac_kW"]
    
    af_3d  = float(af_from_rbf_3d(spd, irms, phase))
    af_sep = float(af_from_rbf_separable(spd, irms, phase))
    
    corr_3d  = h_ac * af_3d
    corr_sep = h_ac * af_sep
    
    e_raw = (h_ac - f_ac) / (f_ac + 1e-12) * 100
    e_3d  = (corr_3d - f_ac) / (f_ac + 1e-12) * 100
    e_sep = (corr_sep - f_ac) / (f_ac + 1e-12) * 100
    
    err_raw.append(e_raw)
    err_3d.append(e_3d)
    err_sep.append(e_sep)
    rows.append((spd, irms, phase, h_ac, f_ac, corr_3d, corr_sep, e_raw, e_3d, e_sep))

ea = np.array(err_raw)
e3 = np.array(err_3d)
es = np.array(err_sep)

# ── LOOCV 계산
print("  LOOCV 계산 중 (약 1.5초 소요)... ")
loocv_errors_3d = []
for i in range(n):
    X_tr = np.delete(X_data, i, axis=0)
    y_tr = np.delete(af_arr, i, axis=0)
    Phi_tr = np.zeros((n-1, n-1))
    for j in range(n-1):
        Phi_tr[:, j] = _rbf_k_3d(X_tr[:, 0], X_tr[:, 1], X_tr[:, 2],
                                 X_tr[j, 0], X_tr[j, 1], X_tr[j, 2])
    w_tr = np.linalg.solve(Phi_tr + LAM * np.eye(n-1), y_tr)
    
    r2 = (X_data[i, 0] - X_tr[:, 0])**2 / LS_S**2        + (X_data[i, 1] - X_tr[:, 1])**2 / LS_I**2        + (X_data[i, 2] - X_tr[:, 2])**2 / LS_P**2
    r = np.sqrt(r2)
    K = r2 * np.log(r + 1e-12)
    y_pred = K @ w_tr
    corr_val = h_ac_arr[i] * y_pred
    loocv_errors_3d.append(abs((corr_val - f_ac_arr[i]) / f_ac_arr[i] * 100))
mae_loocv_3d = np.mean(loocv_errors_3d)

loocv_errors_sep = []
for i in range(n):
    base_train_idx = [idx for idx in base_idx if idx != i]
    X_base_tr = X_data[base_train_idx, 1:3]
    y_base_tr = af_arr[base_train_idx]
    
    Phi_g_tr = np.zeros((len(base_train_idx), len(base_train_idx)))
    for j in range(len(base_train_idx)):
        Phi_g_tr[:, j] = _rbf_2d_k(X_base_tr[:, 0], X_base_tr[:, 1],
                                    X_base_tr[j, 0], X_base_tr[j, 1])
    w_g_tr = np.linalg.solve(Phi_g_tr + LAM * np.eye(len(base_train_idx)), y_base_tr)
    
    def predict_g_tr(I, theta):
        I = np.asarray(I, float)
        theta = np.asarray(theta, float)
        I, theta = np.broadcast_arrays(I, theta)
        orig = I.shape

        Iv, thv = I.ravel()[:, None], theta.ravel()[:, None]
        r2 = (Iv - X_base_tr[:, 0])**2 / LS_I**2 + (thv - X_base_tr[:, 1])**2 / LS_P**2
        r = np.sqrt(r2)
        K = r2 * np.log(r + 1e-12)
        result = K @ w_g_tr
        return result.reshape(orig) if orig else float(result[0])
        
    cal_train_idx = [idx for idx in selected_other_idx if idx != i]
    f_vals_tr = []
    for idx in cal_train_idx:
        spd = speeds_k[idx]
        I_val = irms_arr[idx]
        th_val = phase_arr[idx]
        af_actual = af_arr[idx]
        g_val = predict_g_tr(I_val, th_val)
        f_val = af_actual / (g_val + 1e-12)
        f_vals_tr.append((spd, f_val))
        
    f_by_speed_tr = {2.0: [1.0]}
    for spd, f_val in f_vals_tr:
        if spd not in f_by_speed_tr:
            f_by_speed_tr[spd] = []
        f_by_speed_tr[spd].append(f_val)
        
    speed_coords_tr = []
    f_coords_tr = []
    for spd in sorted(f_by_speed_tr.keys()):
        speed_coords_tr.append(spd)
        f_coords_tr.append(np.mean(f_by_speed_tr[spd]))
        
    p_coeffs_tr = np.polyfit(speed_coords_tr, f_coords_tr, 2)
    p_func_tr = np.poly1d(p_coeffs_tr)
    
    g_val_i = predict_g_tr(X_data[i, 1], X_data[i, 2])
    f_val_i = p_func_tr(X_data[i, 0])
    y_pred_i = f_val_i * g_val_i
    corr_val = h_ac_arr[i] * y_pred_i
    loocv_errors_sep.append(abs((corr_val - f_ac_arr[i]) / f_ac_arr[i] * 100))
mae_loocv_sep = np.mean(loocv_errors_sep)

print("=== RBF 보정 오차 최종 비교 결과 ===")
print(f"  1) Hybrid (보정 전):        Train MAE={np.abs(ea).mean():.2f}% | MaxAE={np.abs(ea).max():.2f}%")
print(f"  2) 3D TPS RBF:             Train MAE={np.abs(e3).mean():.2f}% | MaxAE={np.abs(e3).max():.2f}% | LOOCV MAE={mae_loocv_3d:.2f}%")
print(f"  3) Separable (분리형 RBF):   Train MAE={np.abs(es).mean():.2f}% | MaxAE={np.abs(es).max():.2f}% | LOOCV MAE={mae_loocv_sep:.2f}%")

# ── 시각화 및 그림 저장
fea_all   = np.array([r[4] for r in rows])
hybr_all  = np.array([r[3] for r in rows])
corr_3d   = np.array([r[5] for r in rows])
corr_sep  = np.array([r[6] for r in rows])

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle(f"RBF Model Comparison ({MODEL_SCALE}): 3D RBF vs Separable vs FullFEA", fontsize=12, fontweight='bold')

ax = axes[0]
lim = [min(fea_all.min(), hybr_all.min(), corr_3d.min(), corr_sep.min()) * 0.9,
       max(fea_all.max(), hybr_all.max(), corr_3d.max(), corr_sep.max()) * 1.05]
ax.plot(lim, lim, 'k--', linewidth=1.2, label='Perfect fit')
ax.scatter(fea_all, hybr_all, c='grey',      s=30, alpha=0.5, label='Hybrid (보정 전)', zorder=2)
ax.scatter(fea_all, corr_3d,  c='steelblue', s=45, alpha=0.7, label=f'3D RBF (LOOCV: {mae_loocv_3d:.2f}%)', zorder=3)
ax.scatter(fea_all, corr_sep, c='tomato',    s=45, alpha=0.8, label=f'Separable (LOOCV: {mae_loocv_sep:.2f}%)', zorder=4)
ax.set_xlabel("FullFEA AC Loss [kW]", fontsize=10)
ax.set_ylabel("Predicted AC Loss [kW]", fontsize=10)
ax.set_title("Parity Plot", fontsize=11)
ax.legend(fontsize=9); ax.grid(True, linestyle='--', alpha=0.4)
ax.set_xlim(lim); ax.set_ylim(lim)

ax2 = axes[1]
bp = ax2.boxplot([ea, e3, es], labels=['Hybrid (보정 전)', '3D RBF', 'Separable RBF'], patch_artist=True, widths=0.4)
bp['boxes'][0].set_facecolor('grey');       bp['boxes'][0].set_alpha(0.4)
bp['boxes'][1].set_facecolor('steelblue');  bp['boxes'][1].set_alpha(0.6)
bp['boxes'][2].set_facecolor('tomato');     bp['boxes'][2].set_alpha(0.6)
ax2.axhline(0, color='k', linestyle='--', linewidth=1)
ax2.set_ylabel("오차 [%]", fontsize=10)
ax2.set_title("Error Distribution Comparison", fontsize=11)
ax2.grid(True, linestyle='--', alpha=0.4)
for i, (arr, x) in enumerate([(ea, 1), (e3, 2), (es, 3)]):
    ax2.text(x, arr.max() + 0.5, f"MAE={np.abs(arr).mean():.1f}%", ha='center', fontsize=8.5, color='black')

plt.tight_layout()
val_plot_path = out_dir / f"RBF_correction_validation_{MODEL_SCALE}.png"
plt.savefig(val_plot_path, dpi=150, bbox_inches='tight')
plt.show()
print(f"그림 저장 완료: {val_plot_path}")

# ── 모델 내보내기
export = {
    "model_type": f"RBF_{MODEL_SCALE}",
    "3D_model": {
        "model": "3D_TPS_RBF",
        "n_centers": int(n),
        "weights": rbf_weights_3d.tolist(),
        "validation": {
            "Train_MAE_pct": float(np.abs(e3).mean()),
            "LOOCV_MAE_pct": float(mae_loocv_3d),
        },
        "mcad_formula": rbf_formula_3d
    },
    "separable_model": {
        "model": "Separable_1D_2D_RBF",
        "n_base_centers": int(n_base),
        "base_weights": w_g.tolist(),
        "speed_poly_coeffs": p_coeffs.tolist(),
        "validation": {
            "Train_MAE_pct": float(np.abs(es).mean()),
            "LOOCV_MAE_pct": float(mae_loocv_sep),
        },
        "mcad_formula": rbf_formula_separable
    },
    "mcad_formula_full": rbf_formula_3d,
    "mcad_formula_reduced_30": rbf_formula_separable,
    "mcad_formula_top20": rbf_formula_separable,
    "length_scales": {"LS_S_kRPM": float(LS_S), "LS_I_A": float(LS_I), "LS_P_deg": float(LS_P)},
    "af_points": af_points
}
with open(rbf_model_path, "w", encoding="utf-8") as f:
    json.dump(export, f, ensure_ascii=False, indent=2)
print(f"JSON 모델 저장 완료: {rbf_model_path}")

# ── [대화형 4-Way 비교 플롯 구현] ───────────────────────────────────────────
try:
    import IPython
    shell = IPython.get_ipython()
    if shell is not None:
        import os, sys
        has_vscode_env = any(k.startswith('VSCODE_') for k in os.environ.keys())
        has_vscode_modules = any('vscode' in m.lower() for m in sys.modules.keys())
        selected_backend = 'widget' if (has_vscode_env and has_vscode_modules) else 'inline'
        if selected_backend == 'widget':
            shell.run_line_magic('matplotlib', 'widget')
        else:
            shell.run_line_magic('matplotlib', 'inline')
except Exception:
    pass

import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D

print("\n  대화형 4-Way 비교 플롯 로딩...")
speeds = np.array([p["speed_rpm"] for p in af_points])
irms = np.array([p["current_rms"] for p in af_points])
phases = np.array([p["phase_deg"] for p in af_points])
id_vals = np.array([p["id_A"] for p in af_points])
iq_vals = np.array([p["iq_A"] for p in af_points])

loss_hyb = np.array([p["hybrid_ac_kW"] for p in af_points])
loss_fea = np.array([p["fea_ac_kW"] for p in af_points])
loss_3d  = np.array([float(af_from_rbf_3d(p["speed_rpm"], p["current_rms"], p["phase_deg"])) * p["hybrid_ac_kW"] for p in af_points])
loss_sep = np.array([float(af_from_rbf_separable(p["speed_rpm"], p["current_rms"], p["phase_deg"])) * p["hybrid_ac_kW"] for p in af_points])

fig_int = plt.figure(figsize=(17, 8.5))
fig_int.suptitle(f"AC Loss 3D Map & Speed Curve Comparison ({MODEL_SCALE}): Hybrid vs 3D RBF vs Separable RBF vs FullFEA", fontsize=13, fontweight='bold')

ax_hyb = fig_int.add_subplot(2, 3, 1, projection='3d')
ax_3d  = fig_int.add_subplot(2, 3, 2, projection='3d')
ax_sep = fig_int.add_subplot(2, 3, 4, projection='3d')
ax_fea = fig_int.add_subplot(2, 3, 5, projection='3d')
ax_curve = fig_int.add_subplot(2, 3, (3, 6))

ax_hyb.set_title("1) Hybrid (보정 전)", fontsize=11, fontweight='bold')
ax_3d.set_title("2) 3D TPS RBF (보정 후)", fontsize=11, fontweight='bold')
ax_sep.set_title("3) Separable RBF (보정 후)", fontsize=11, fontweight='bold')
ax_fea.set_title("4) FullFEA (참조값)", fontsize=11, fontweight='bold')

unique_speeds = sorted(list(set(speeds)))
speed_colors = {2000: 'cyan', 4000: 'limegreen', 8000: 'orange', 16000: 'tomato'}
default_colors = ['cyan', 'limegreen', 'orange', 'tomato']
axes_3d = [ax_hyb, ax_3d, ax_sep, ax_fea]
losses_list = [loss_hyb, loss_3d, loss_sep, loss_fea]

legend_patches = []
for i, spd in enumerate(unique_speeds):
    color = speed_colors.get(spd, default_colors[i % len(default_colors)])
    legend_patches.append(mpatches.Patch(color=color, alpha=0.35, label=f"{spd} RPM"))
    idx_spd = (speeds == spd)
    if np.any(idx_spd) and np.sum(idx_spd) >= 3:
        for ax, loss_val in zip(axes_3d, losses_list):
            ax.plot_trisurf(id_vals[idx_spd], iq_vals[idx_spd], loss_val[idx_spd], color=color, edgecolor='none', alpha=0.2)

sc_hyb = ax_hyb.scatter(id_vals, iq_vals, loss_hyb, c='grey', s=20, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
sc_3d  = ax_3d.scatter(id_vals, iq_vals, loss_3d,   c='grey', s=20, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
sc_sep = ax_sep.scatter(id_vals, iq_vals, loss_sep, c='grey', s=20, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
sc_fea = ax_fea.scatter(id_vals, iq_vals, loss_fea, c='grey', s=20, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
scatters = [sc_hyb, sc_3d, sc_sep, sc_fea]

for ax in axes_3d:
    ax.set_xlabel("I_d [A]", fontsize=8, labelpad=5)
    ax.set_ylabel("I_q [A]", fontsize=8, labelpad=5)
    ax.set_zlabel("AC Loss [kW]", fontsize=8, labelpad=5)
    ax.legend(handles=legend_patches, fontsize=8)

ax_curve.text(0.5, 0.5, "3D 플롯에서 임의의 점을 클릭한 후\nSpacebar를 누르거나 클릭하면 우측에 속도별 비교 곡선이 출력됩니다.", 
             ha="center", va="center", fontsize=10, color="gray")
ax_curve.set_xlabel("Speed [RPM]", fontsize=9)
ax_curve.set_ylabel("AC Loss [kW]", fontsize=9)
ax_curve.grid(True, linestyle="--", alpha=0.5)

selected_pt = {"current_rms": None, "phase_deg": None, "id_A": None, "iq_A": None}
highlights = []
annots = []
for ax in axes_3d:
    annot = ax.text2D(0.02, 0.95, "", transform=ax.transAxes, bbox=dict(boxstyle="round", fc="w", alpha=0.8), fontsize=8)
    annot.set_visible(False)
    annots.append(annot)

def update_2d_curve(curr, ph):
    ax_curve.clear()
    match_pts = [p for p in af_points if np.isclose(p["current_rms"], curr) and np.isclose(p["phase_deg"], ph)]
    match_pts = sorted(match_pts, key=lambda x: x["speed_rpm"])
    
    curve_speeds = [p["speed_rpm"] for p in match_pts]
    c_loss_hyb = [p["hybrid_ac_kW"] for p in match_pts]
    c_loss_fea = [p["fea_ac_kW"] for p in match_pts]
    c_loss_3d  = [float(af_from_rbf_3d(p["speed_rpm"], p["current_rms"], p["phase_deg"])) * p["hybrid_ac_kW"] for p in match_pts]
    c_loss_sep = [float(af_from_rbf_separable(p["speed_rpm"], p["current_rms"], p["phase_deg"])) * p["hybrid_ac_kW"] for p in match_pts]
    
    ax_curve.plot(curve_speeds, c_loss_hyb, marker='o', linestyle='-',  color='grey',      linewidth=1.5, label="1) Hybrid (보정 전)")
    ax_curve.plot(curve_speeds, c_loss_3d,  marker='s', linestyle='-',  color='steelblue', linewidth=2,   label="2) 3D RBF (보정 후)")
    ax_curve.plot(curve_speeds, c_loss_sep, marker='^', linestyle='-',  color='tomato',    linewidth=2,   label="3) Separable (보정 후)")
    ax_curve.plot(curve_speeds, c_loss_fea, marker='*', linestyle='--', color='black',     linewidth=2,   label="4) FullFEA Reference")
    
    for xs, yh, y3, ys, yf in zip(curve_speeds, c_loss_hyb, c_loss_3d, c_loss_sep, c_loss_fea):
        ax_curve.annotate(f"{yh:.2f}", xy=(xs, yh), xytext=(4, 8),   textcoords="offset points", fontsize=8, color="grey")
        ax_curve.annotate(f"{y3:.2f}", xy=(xs, y3), xytext=(4, 0),   textcoords="offset points", fontsize=8, color="steelblue")
        ax_curve.annotate(f"{ys:.2f}", xy=(xs, ys), xytext=(4, -8),  textcoords="offset points", fontsize=8, color="tomato")
        ax_curve.annotate(f"{yf:.2f}", xy=(xs, yf), xytext=(4, -16), textcoords="offset points", fontsize=8, color="black")
        
    ax_curve.set_title(f"AC Loss vs Speed Comparison\n(I_rms={curr:.1f}A, Phase={ph:.1f}°)", fontsize=11, fontweight='bold')
    ax_curve.set_xlabel("Speed [RPM]", fontsize=9)
    ax_curve.set_ylabel("AC Loss [kW]", fontsize=9)
    ax_curve.grid(True, linestyle="--", alpha=0.5)
    ax_curve.legend(fontsize=9, loc="upper left")

def on_pick(event):
    if event.artist not in scatters:
        return
    idx = event.ind[0]
    p_sel = af_points[idx]
    curr = p_sel["current_rms"]
    ph = p_sel["phase_deg"]
    
    selected_pt["current_rms"] = curr
    selected_pt["phase_deg"] = ph
    selected_pt["id_A"] = p_sel["id_A"]
    selected_pt["iq_A"] = p_sel["iq_A"]
    
    for h in highlights:
        h.remove()
    highlights.clear()
    
    same_pt_idx = np.where((irms == curr) & (phases == ph))[0]
    for ax, loss_val in zip(axes_3d, losses_list):
        h = ax.scatter(id_vals[same_pt_idx], iq_vals[same_pt_idx], loss_val[same_pt_idx], color='red', s=60, edgecolors='black', linewidths=1.5, zorder=10)
        highlights.append(h)
        
    msg = f"Selected: I_rms={curr:.1f}A, Phase={ph:.1f}°\nId={selected_pt['id_A']:.1f}A, Iq={selected_pt['iq_A']:.1f}A"
    for annot in annots:
        annot.set_text(msg)
        annot.set_visible(True)
        
    update_2d_curve(curr, ph)
    fig_int.canvas.draw_idle()

def on_key(event):
    if event.key != ' ' or selected_pt["current_rms"] is None:
        return
    update_2d_curve(selected_pt["current_rms"], selected_pt["phase_deg"])
    fig_int.canvas.draw_idle()

fig_int.canvas.mpl_connect('pick_event', on_pick)
fig_int.canvas.mpl_connect('key_press_event', on_key)
plt.tight_layout()
plt.show()

