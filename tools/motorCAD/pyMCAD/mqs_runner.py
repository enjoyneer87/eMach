from __future__ import annotations

import concurrent.futures
import os
import shutil
from datetime import datetime
from pathlib import Path

def parse_colon_str(value: str | list | tuple) -> list[float]:
    """Convert Motor-CAD colon-separated string or sequence into a list of floats."""
    if isinstance(value, str):
        return [float(x) for x in value.split(":") if x.strip()]
    return [float(x) for x in value]

def calc_dc_loss_kw(resistance_ohm: float, rms_current_a: float) -> float:
    """Calculate 3-phase active DC copper loss in kW: 3 * R * I^2 / 1000."""
    return 3.0 * float(resistance_ohm) * (float(rms_current_a) ** 2) / 1000.0

def get_fea_src_dir(mcad_obj) -> Path:
    """Return the FEResultsData directory path for the current open Motor-CAD model."""
    cur_path = Path(mcad_obj.get_variable("CurrentMotFilePath_MotorLAB"))
    return cur_path.parent / cur_path.stem / "FEResultsData"

def backup_fea_result(fea_src_dir: Path, backup_root: Path, tag: str) -> Path:
    """Copy the active FEA results folder to a timestamped backup directory."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = backup_root / f"{tag}_{ts}"
    dst.mkdir(parents=True, exist_ok=True)
    if fea_src_dir.exists():
        for f in fea_src_dir.glob("*"):
            try:
                shutil.copy2(str(f), str(dst / f.name))
            except Exception:
                pass
    return dst

def _hybrid_one_speed(mcad_obj, speed: int, rms_current: float, phase_advance: float,
                      fea_src: Path, backup_root: Path, label: str) -> tuple[float, float, float]:
    """Solve Hybrid FEA for a single speed point on a single instance and return loss components."""
    mcad_obj.set_variable("ShaftSpeed", speed)
    mcad_obj.do_magnetic_calculation()
    backup_fea_result(fea_src, backup_root, f"Hybrid_{label}_Speed_{speed}RPM")
    total = float(mcad_obj.get_variable("ACLoss_Hybrid_Total"))
    prox  = float(mcad_obj.get_variable("ACLoss_Hybrid_Prox_Total"))
    skin  = float(mcad_obj.get_variable("ACLoss_Hybrid_SkinEffect_Total"))
    return total, prox, skin

def run_hybrid_dual(mcad_ref_obj, mcad_sc_obj, speed_list: list[int] | tuple[int, ...],
                    rms_ref: float, rms_sc: float, phase_advance: float) -> tuple[dict, dict]:
    """
    Run Hybrid calculation dual instances concurrently using ThreadPoolExecutor.
    Returns (ref_res_dict, sc_res_dict) containing loss components in Watts.
    """
    for obj, rms in [(mcad_ref_obj, rms_ref), (mcad_sc_obj, rms_sc)]:
        obj.set_variable("ProximityLossModel", 1)
        obj.set_variable("RMSCurrent",         rms)
        obj.set_variable("PhaseAdvance",        phase_advance)

    fea_ref = get_fea_src_dir(mcad_ref_obj)
    fea_sc  = get_fea_src_dir(mcad_sc_obj)
    bk_ref  = fea_ref.parent / "FEResultsData_backup"
    bk_sc   = fea_sc.parent  / "FEResultsData_backup"

    ref_res = {"ACLoss_Hybrid_Total": [], "ACLoss_Hybrid_Prox_Total": [], "ACLoss_Hybrid_SkinEffect_Total": []}
    sc_res  = {"ACLoss_Hybrid_Total": [], "ACLoss_Hybrid_Prox_Total": [], "ACLoss_Hybrid_SkinEffect_Total": []}

    for speed in speed_list:
        print(f"  [{speed} RPM] Hybrid 동시 계산 시작...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            fut_ref = ex.submit(_hybrid_one_speed,
                                mcad_ref_obj, speed, rms_ref, phase_advance, fea_ref, bk_ref, "Ref")
            fut_sc  = ex.submit(_hybrid_one_speed,
                                mcad_sc_obj,  speed, rms_sc,  phase_advance, fea_sc,  bk_sc,  "SC")
            t_ref, p_ref, s_ref = fut_ref.result()
            t_sc,  p_sc,  s_sc  = fut_sc.result()

        ref_res["ACLoss_Hybrid_Total"].append(t_ref)
        ref_res["ACLoss_Hybrid_Prox_Total"].append(p_ref)
        ref_res["ACLoss_Hybrid_SkinEffect_Total"].append(s_ref)
        
        sc_res["ACLoss_Hybrid_Total"].append(t_sc)
        sc_res["ACLoss_Hybrid_Prox_Total"].append(p_sc)
        sc_res["ACLoss_Hybrid_SkinEffect_Total"].append(s_sc)
        
        print(f"    Ref Total={t_ref/1000:.3f} kW  |  SC Total={t_sc/1000:.3f} kW  ✓")

    return ref_res, sc_res

def run_hybrid_single(mcad_obj, speed_list: list[int] | tuple[int, ...],
                      rms_current: float, phase_advance: float, label: str) -> dict:
    """Run Hybrid calculation sequentially on a single instance and return loss components."""
    mcad_obj.set_variable("ProximityLossModel", 1)
    mcad_obj.set_variable("RMSCurrent",         rms_current)
    mcad_obj.set_variable("PhaseAdvance",        phase_advance)

    fea_src = get_fea_src_dir(mcad_obj)
    backup_root = fea_src.parent / "FEResultsData_backup"

    res = {"ACLoss_Hybrid_Total": [], "ACLoss_Hybrid_Prox_Total": [], "ACLoss_Hybrid_SkinEffect_Total": []}

    for speed in speed_list:
        print(f"  [{label} - {speed} RPM] Hybrid 계산 시작...")
        mcad_obj.set_variable("ShaftSpeed", speed)
        mcad_obj.do_magnetic_calculation()
        backup_fea_result(fea_src, backup_root, f"Hybrid_{label}_Speed_{speed}RPM")
        total = float(mcad_obj.get_variable("ACLoss_Hybrid_Total"))
        prox  = float(mcad_obj.get_variable("ACLoss_Hybrid_Prox_Total"))
        skin  = float(mcad_obj.get_variable("ACLoss_Hybrid_SkinEffect_Total"))
        
        res["ACLoss_Hybrid_Total"].append(total)
        res["ACLoss_Hybrid_Prox_Total"].append(prox)
        res["ACLoss_Hybrid_SkinEffect_Total"].append(skin)
        print(f"    Total={total/1000:.3f} kW  ✓")

    return res

def _ts_one_speed(mcad_obj, speed: int, fea_src: Path, backup_root: Path, label: str) -> tuple[list[float], float, float]:
    """Solve Transient FullFEA for a single speed point on a single instance and return per-turn losses."""
    mcad_obj.set_variable("ShaftSpeed", speed)
    mcad_obj.do_magnetic_calculation()
    backup_fea_result(fea_src, backup_root, f"TS_{label}_Speed_{speed}RPM")

    per_turn_w      = parse_colon_str(mcad_obj.get_variable("ACLoss_FEA_OnLoad_PerTurn"))
    per_turn_sum_kw = sum(per_turn_w) / 1000.0
    total_kw        = float(mcad_obj.get_variable("ACLoss_FEA_OnLoad_Total")) / 1000.0
    return per_turn_w, per_turn_sum_kw, total_kw

def _ts_get_dc(mcad_obj, rms_current: float) -> tuple[float, float]:
    """Retrieve resistance variables from the model and calculate DC losses in kW."""
    R_total  = float(mcad_obj.get_variable("Resistance_MotorLAB"))
    R_end    = float(mcad_obj.get_variable("EndWindingResistance_Lab"))
    R_active = R_total - R_end
    return calc_dc_loss_kw(R_active, rms_current), calc_dc_loss_kw(R_end, rms_current)

def run_ts_dual(mcad_ref_obj, mcad_sc_obj, speed_list: list[int] | tuple[int, ...],
                rms_ref: float, rms_sc: float, phase_advance: float,
                torque_points: int = 128) -> tuple[dict, dict]:
    """
    Run Transient FullFEA calculation concurrently on dual instances using ThreadPoolExecutor.
    Returns (ref_ts_dict, sc_ts_dict) containing active AC-only loss, total loss, and DC components.
    """
    for obj, rms in [(mcad_ref_obj, rms_ref), (mcad_sc_obj, rms_sc)]:
        obj.set_variable("ProximityLossModel",   3)
        obj.set_variable("RMSCurrent",           rms)
        obj.set_variable("PhaseAdvance",         phase_advance)
        obj.set_variable("TorquePointsPerCycle", torque_points)

    fea_ref = get_fea_src_dir(mcad_ref_obj)
    fea_sc  = get_fea_src_dir(mcad_sc_obj)
    bk_ref  = fea_ref.parent / "FEResultsData_backup"
    bk_sc   = fea_sc.parent  / "FEResultsData_backup"

    ref_per_turn_list, ref_per_turnSum_list, ref_total_list = [], [], []
    sc_per_turn_list,  sc_per_turnSum_list,  sc_total_list  = [], [], []

    for speed in speed_list:
        print(f"  [{speed} RPM] TS 동시 계산 시작...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            fut_ref = ex.submit(_ts_one_speed, mcad_ref_obj, speed, fea_ref, bk_ref, "Ref")
            fut_sc  = ex.submit(_ts_one_speed, mcad_sc_obj,  speed, fea_sc,  bk_sc,  "SC")
            pt_ref_w, pt_ref_sum, tot_ref = fut_ref.result()
            pt_sc_w,  pt_sc_sum,  tot_sc  = fut_sc.result()

        ref_per_turn_list.append(pt_ref_w)
        ref_per_turnSum_list.append(pt_ref_sum)
        ref_total_list.append(tot_ref)
        
        sc_per_turn_list.append(pt_sc_w)
        sc_per_turnSum_list.append(pt_sc_sum)
        sc_total_list.append(tot_sc)
        
        print(f"    Ref PerTurnSum={pt_ref_sum:.3f} kW  |  SC PerTurnSum={pt_sc_sum:.3f} kW  ✓")

    dc_ref_active, dc_ref_end = _ts_get_dc(mcad_ref_obj, rms_ref)
    dc_sc_active,  dc_sc_end  = _ts_get_dc(mcad_sc_obj,  rms_sc)
    print(f"\n  [Ref] DC Active={dc_ref_active:.3f} kW  DC End={dc_ref_end:.3f} kW")
    print(f"  [SC]  DC Active={dc_sc_active:.3f} kW  DC End={dc_sc_end:.3f} kW")

    ref_ts = {
        "ACLoss_OnLoad_PerTurn_kW": ref_per_turn_list,
        "ACLoss_OnLoad_PerTurnSum_kW": ref_per_turnSum_list,
        "ACLoss_Active_Only_kW":    [v - dc_ref_active for v in ref_per_turnSum_list],
        "ACLoss_Total_kW":          ref_total_list,
        "DC_Loss_Active_kW":        dc_ref_active,
        "DC_Loss_End_kW":           dc_ref_end,
    }
    sc_ts = {
        "ACLoss_OnLoad_PerTurn_kW": sc_per_turn_list,
        "ACLoss_OnLoad_PerTurnSum_kW": sc_per_turnSum_list,
        "ACLoss_Active_Only_kW":    [v - dc_sc_active for v in sc_per_turnSum_list],
        "ACLoss_Total_kW":          sc_total_list,
        "DC_Loss_Active_kW":        dc_sc_active,
        "DC_Loss_End_kW":           dc_sc_end,
    }
    return ref_ts, sc_ts

def run_ts_single(mcad_obj, speed_list: list[int] | tuple[int, ...],
                  rms_current: float, phase_advance: float, label: str) -> dict:
    """Run Transient FullFEA calculation sequentially on a single instance and return results."""
    mcad_obj.set_variable("ProximityLossModel",   3)
    mcad_obj.set_variable("RMSCurrent",           rms_current)
    mcad_obj.set_variable("PhaseAdvance",         phase_advance)
    mcad_obj.set_variable("TorquePointsPerCycle", 128)

    fea_src = get_fea_src_dir(mcad_obj)
    backup_root = fea_src.parent / "FEResultsData_backup"

    per_turn_list, per_turnSum_list, total_list = [], [], []

    for speed in speed_list:
        print(f"  [{label} - {speed} RPM] TS 계산 시작...")
        mcad_obj.set_variable("ShaftSpeed", speed)
        mcad_obj.do_magnetic_calculation()
        backup_fea_result(fea_src, backup_root, f"TS_{label}_Speed_{speed}RPM")

        per_turn_w      = parse_colon_str(mcad_obj.get_variable("ACLoss_FEA_OnLoad_PerTurn"))
        per_turn_sum_kw = sum(per_turn_w) / 1000.0
        total_kw        = float(mcad_obj.get_variable("ACLoss_FEA_OnLoad_Total")) / 1000.0
        per_turn_list.append(per_turn_sum_kw)
        per_turnSum_list.append(per_turn_sum_kw)
        total_list.append(total_kw)
        print(f"    PerTurnSum={per_turn_sum_kw:.3f} kW  |  Total={total_kw:.3f} kW  ✓")

    R_total  = float(mcad_obj.get_variable("Resistance_MotorLAB"))
    R_end    = float(mcad_obj.get_variable("EndWindingResistance_Lab"))
    R_active = R_total - R_end
    dc_active_kw = calc_dc_loss_kw(R_active, rms_current)
    dc_end_kw    = calc_dc_loss_kw(R_end, rms_current)
    print(f"\n  [DC Loss] Active={dc_active_kw:.3f} kW  End={dc_end_kw:.3f} kW")

    res = {
        "ACLoss_OnLoad_PerTurn_kW": per_turn_list,
        "ACLoss_OnLoad_PerTurnSum_kW": per_turnSum_list,
        "ACLoss_Active_Only_kW":    [v - dc_active_kw for v in per_turnSum_list],
        "ACLoss_Total_kW":          total_list,
        "DC_Loss_Active_kW":        dc_active_kw,
        "DC_Loss_End_kW":           dc_end_kw,
    }
    return res
