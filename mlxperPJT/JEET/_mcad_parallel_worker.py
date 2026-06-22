"""Motor-CAD parallel sweep worker functions.

Defined in a standalone module (not in the notebook) so that Windows
multiprocessing 'spawn' can import this without re-executing notebook cells.

Usage (from notebook cell):
    from _mcad_parallel_worker import initialise_mcad, run_sweep_point, close_mcad
"""
from __future__ import annotations

import sys
from multiprocessing import current_process
from pathlib import Path

import numpy as np

mcApp = None  # one per subprocess; set by initialise_mcad()


def initialise_mcad(base_mot_path: str, extra_sys_paths: list[str]) -> None:
    """Called once per Pool worker process to launch a Motor-CAD session.

    Loads the base .mot, then saves a process-unique copy so each session
    writes FEA results to its own directory (avoids file-lock conflicts).
    """
    global mcApp
    import ansys.motorcad.core as pymotorcad

    for p in reversed(extra_sys_paths):
        if p not in sys.path:
            sys.path.insert(0, p)

    import shutil
    p = current_process()
    base = Path(base_mot_path)
    unique_path = base.parent / f"{base.stem}_{p.name}{base.suffix}"
    shutil.copy2(base_mot_path, str(unique_path))

    mcApp = pymotorcad.MotorCAD(enable_success_variable=False)
    try:
        mcApp.set_variable("MessageDisplayState", 2)  # suppress all GUI popups (headless batch)
    except Exception:
        pass
    mcApp.load_from_file(str(unique_path))
    print(f"[{p.name}] Ready -> {unique_path.name}", flush=True)


def run_sweep_point(args: dict) -> dict | None:
    """Run one FEA sweep point.  Returns point_data dict, or None on error."""
    global mcApp
    import shutil
    from tools.motorCAD.pyMCAD import calc_dc_loss_kw, get_fea_src_dir

    p_proc = current_process()
    prox_model  = args["prox_model"]
    speed       = args["speed"]
    current     = args["current"]
    phase       = args["phase"]
    backup_root = Path(args["backup_root"])
    first_step  = args["first_step"]
    export_cols = args["export_columns"]
    n_turns     = args["n_turns"]
    n_parallel  = args["n_parallel"]
    R_active    = args["R_active"]
    idx         = args["idx"]
    total_pts   = args["total_pts"]

    mode_label = "Hybrid" if prox_model == 1 else "FullFEA"
    tag = f"[{idx + 1}/{total_pts}][{p_proc.name}]"

    try:
        mcApp.set_variable("ProximityLossModel", prox_model)
        mcApp.set_variable("ShaftSpeed", speed)
        mcApp.set_variable("RMSCurrent", current)
        mcApp.set_variable("PhaseAdvance", phase)
        mcApp.do_magnetic_calculation()
        torque_points = int(mcApp.get_variable("TorquePointsPerCycle"))

        # Locate .mes (live dir first, then fall back to any subdirectory)
        fe_dir = get_fea_src_dir(mcApp)
        candidates = list(fe_dir.glob("*.mes"))
        if not candidates:
            candidates = list(fe_dir.parent.rglob("*.mes"))
        if not candidates:
            raise FileNotFoundError(f"No .mes files found under {fe_dir.parent}")
        active_results_dir = max(candidates, key=lambda f: f.stat().st_mtime).parent

        # Copy FEA results to backup
        point_folder = f"{mode_label}_Speed_{speed}RPM_{current:.1f}A_{phase:.1f}deg"
        dest_point_dir   = backup_root / point_folder
        dest_results_dir = dest_point_dir / "FEResultsData"
        if dest_results_dir.exists():
            shutil.rmtree(dest_results_dir)
        shutil.copytree(active_results_dir, dest_results_dir)

        # Export B-field TXT
        txt_path = dest_point_dir / "FEA_data.txt"
        mcApp.save_fea_data(str(txt_path), first_step, torque_points,
                            export_cols, "", ",")

        point_data: dict = {
            "proximity_model": prox_model,
            "mode":    mode_label,
            "speed":   speed,
            "current": current,
            "phase":   phase,
            "backup_dir": str(dest_point_dir),
        }

        if prox_model == 1:
            point_data["hybrid_total_kW"] = float(mcApp.get_variable("ACLoss_Hybrid_Total"))
            point_data["hybrid_prox_kW"]  = float(mcApp.get_variable("ACLoss_Hybrid_Prox_Total"))
            point_data["hybrid_skin_kW"]  = float(mcApp.get_variable("ACLoss_Hybrid_SkinEffect_Total"))
        else:
            raw_pt_str = mcApp.get_variable("ACLoss_FEA_OnLoad_PerTurn")
            point_data["fea_per_turn_raw"] = raw_pt_str
            point_data["fea_total_ac_kW"]  = float(mcApp.get_variable("ACLoss_FEA_OnLoad_Total")) / 1000.0

            try:
                losses_raw    = [float(x) for x in raw_pt_str.split(",") if x.strip()]
                loss_per_turn = np.array(losses_raw)
            except Exception:
                loss_per_turn = np.zeros(n_turns * n_parallel)

            R_dc_per_turn = R_active / float(n_turns)
            dc_loss_act   = calc_dc_loss_kw(R_dc_per_turn, current)

            loss_active_only = loss_per_turn.copy()
            for _t in range(n_turns):
                for _p in range(n_parallel):
                    t_idx = _t * n_parallel + _p
                    if loss_active_only[t_idx] > dc_loss_act:
                        loss_active_only[t_idx] -= dc_loss_act
                    else:
                        loss_active_only[t_idx] = 0.0

            point_data["ts_ac_active_only_kW"] = float(np.sum(loss_active_only))
            point_data["ts_dc_active_only_kW"] = float(dc_loss_act * n_turns * n_parallel)

        print(f"  ok {tag} {point_folder}", flush=True)
        return point_data

    except Exception as err:
        print(f"  [ERROR] {tag} {err}", flush=True)
        return None


def close_mcad(dummy) -> None:
    """Terminate the Motor-CAD instance for this worker process."""
    global mcApp
    p = current_process()
    try:
        mcApp.quit()
    except Exception:
        pass
    print(f"[{p.name}] Motor-CAD closed.", flush=True)
