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

    mcApp = pymotorcad.MotorCAD(open_new_instance=True, enable_success_variable=False)
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
            point_data["hybrid_total_kW"] = float(mcApp.get_variable("ACLoss_Hybrid_Total")) / 1000.0
            point_data["hybrid_prox_kW"]  = float(mcApp.get_variable("ACLoss_Hybrid_Prox_Total")) / 1000.0
            point_data["hybrid_skin_kW"]  = float(mcApp.get_variable("ACLoss_Hybrid_SkinEffect_Total")) / 1000.0
        else:
            # FullFEA — per-turn losses + DC subtraction (Map notebook approach)
            try:
                per_turn_str = mcApp.get_variable("ACLoss_FEA_OnLoad_PerTurn")
                if isinstance(per_turn_str, str):
                    per_turn_w = [float(x) for x in per_turn_str.split(":")]
                else:
                    per_turn_w = list(per_turn_str)
                per_turn_sum_kw = sum(per_turn_w) / 1000.0
                total_kw = float(mcApp.get_variable("ACLoss_FEA_OnLoad_Total")) / 1000.0
            except Exception as _e:
                per_turn_str = ""
                per_turn_w = []
                per_turn_sum_kw, total_kw = 0.0, 0.0
                print(f"  [WARN] TS loss read failed: {_e}", flush=True)

            try:
                mcApp.set_motorlab_context()
                _R_total  = float(mcApp.get_variable("Resistance_MotorLAB"))
                _R_end    = float(mcApp.get_variable("EndWindingResistance_Lab"))
                _R_active = _R_total - _R_end
                mcApp.show_magnetic_context()
            except Exception:
                _R_active, _R_end = 0.0, 0.0

            dc_active_kw      = calc_dc_loss_kw(_R_active, current)
            dc_end_kw         = calc_dc_loss_kw(_R_end, current)
            ac_active_only_kw = per_turn_sum_kw - dc_active_kw

            point_data["fea_per_turn_raw"]     = per_turn_str
            point_data["fea_per_turn_sum_kW"]  = per_turn_sum_kw
            point_data["fea_total_ac_kW"]      = total_kw
            point_data["ts_dc_active_kW"]      = dc_active_kw
            point_data["ts_dc_end_kW"]         = dc_end_kw
            point_data["ts_ac_active_only_kW"] = ac_active_only_kw
            print(f"  → TS: PerTurnSum={per_turn_sum_kw:.3f} kW, "
                  f"AC Active Only={ac_active_only_kw:.3f} kW, "
                  f"Total={total_kw:.3f} kW", flush=True)

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
