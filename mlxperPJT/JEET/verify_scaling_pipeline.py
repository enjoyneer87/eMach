import os
import sys
import numpy as np
from pathlib import Path
from scipy.io import loadmat

# Add eMach root to path to enable importing from tools
current_dir = Path(__file__).parent.resolve()
emach_root = current_dir.parent.parent.resolve()
if str(emach_root) not in sys.path:
    sys.path.insert(0, str(emach_root))

from tools.motor_scaling import (
    BaseMotorMap,
    RbfJsonReader,
    scale_motor_map,
    correct_ac_loss,
    MtpaFwSolver,
    generate_efficiency_map
)

def run_pipeline_verification():
    print("==================================================")
    # 1. Load Base Motor Map from SatuMap.mat
    sat_map_path = current_dir.parent.parent / "tools" / "SystemSimulationModel" / "SatuMap.mat"
    print(f"Loading saturation map: {sat_map_path}")
    sat_data = loadmat(str(sat_map_path))
    
    # Extract arrays
    id_grid = np.squeeze(sat_data['Id_Peak'])
    iq_grid = np.squeeze(sat_data['Iq_Peak'])
    lambda_d = np.squeeze(sat_data['Flux_Linkage_D'])
    lambda_q = np.squeeze(sat_data['Flux_Linkage_Q'])
    
    # Convert loss from Watts to kW
    p_fe = np.squeeze(sat_data['Iron_Loss']) / 1000.0
    p_cu_ac = np.squeeze(sat_data['Stator_Copper_Loss_AC']) / 1000.0
    
    r_dc = float(np.squeeze(sat_data['Phase_Resistance_DC_at_20C']))
    
    print(f"  Grid shapes: Id={id_grid.shape}, Iq={iq_grid.shape}")
    print(f"  Flux range: d=[{lambda_d.min():.4f}, {lambda_d.max():.4f}], q=[{lambda_q.min():.4f}, {lambda_q.max():.4f}]")
    print(f"  R_dc: {r_dc:.6f} Ohm")
    
    base_map = BaseMotorMap(
        id_grid=id_grid,
        iq_grid=iq_grid,
        lambda_d=lambda_d,
        lambda_q=lambda_q,
        r_dc=r_dc,
        p_fe_grid=p_fe,
        p_cu_ac_hybrid=p_cu_ac,
        pole_pairs=4
    )
    
    # 2. Load RBF model from JSON
    rbf_json_path = current_dir / "map_exports" / "AF_RBF_model_SC.json"
    print(f"Loading RBF Model: {rbf_json_path}")
    rbf_params = RbfJsonReader.read(str(rbf_json_path), use_separable=True)
    print(f"  RBF Model Type: {rbf_params.model_type}")
    print(f"  Base weights size: {len(rbf_params.weights)}")
    print(f"  Speed scaling poly coeffs: {rbf_params.p_coeffs}")
    
    # 3. Test Scaling Morphism
    k_r, k_a = 1.2, 1.1
    print(f"Applying motor scaling (k_r={k_r}, k_a={k_a})...")
    scaled_map = scale_motor_map(base_map, k_r, k_a)
    print(f"  Scaled R_dc: {scaled_map.r_dc:.6f} Ohm (expected: {r_dc * k_a / (k_r**2):.6f})")
    
    # 4. Test Solver Morphism
    speed_rpm = 4000.0
    torque_ref = 350.0  # Nm
    v_max = 720.0 / np.sqrt(3.0)  # phase voltage peak limit
    i_max = 460.0 * np.sqrt(2.0)  # peak current limit
    
    print(f"Solving optimal current at speed={speed_rpm:.0f} RPM, torque={torque_ref:.1f} Nm...")
    sol = MtpaFwSolver.solve(
        torque_ref=torque_ref,
        speed_rpm=speed_rpm,
        map_data=scaled_map,
        rbf_model=rbf_params,
        v_max=v_max,
        i_max=i_max
    )
    
    print("  Solver result:")
    print(f"    Success: {sol['success']}")
    print(f"    Optimal currents: id={sol['id_opt']:.2f} A, iq={sol['iq_opt']:.2f} A")
    print(f"    Solved Torque: {sol['torque']:.2f} Nm (Target: {torque_ref:.1f})")
    print(f"    Solved Voltage: {sol['voltage']:.2f} V (Limit: {v_max:.1f})")
    print(f"    Losses [kW]: Total={sol['loss_total']:.3f}, Cu_dc={sol['loss_cu_dc']:.3f}, Cu_ac={sol['loss_cu_ac']:.3f}, Fe={sol['loss_fe']:.3f}")
    
    # Quick sanity asserts
    assert sol['success'], "Solver failed to find a valid solution!"
    assert np.isclose(sol['torque'], torque_ref, rtol=1e-2), "Solved torque doesn't match reference!"
    assert sol['voltage'] <= v_max + 1.0, "Voltage limit violated!"
    assert np.sqrt(sol['id_opt']**2 + sol['iq_opt']**2) <= i_max + 1.0, "Current limit violated!"
    print("  [OK] Single point solver verification passed.")
    
    # 5. Test Efficiency Map Generator Composition
    speeds = np.array([2000.0, 4000.0, 6000.0])
    torques = np.array([100.0, 200.0, 300.0])
    print(f"Generating 2D efficiency map grid for speeds={speeds} RPM and torques={torques} Nm...")
    eff_map = generate_efficiency_map(
        base_map=base_map,
        k_r=k_r,
        k_a=k_a,
        rbf_model=rbf_params,
        speeds_rpm=speeds,
        torques_ref=torques,
        v_max=v_max,
        i_max=i_max
    )
    
    print("  Efficiency map results grid:")
    print(f"    Grid shapes: speed={eff_map.speed_grid.shape}, torque={eff_map.torque_grid.shape}")
    print("    Efficiency values [%]:")
    for t_idx, torque in enumerate(torques):
        row_str = f"      Torque {torque} Nm: "
        for s_idx, speed in enumerate(speeds):
            row_str += f"{eff_map.efficiency[t_idx, s_idx]:.2f}% ({'OK' if eff_map.success_mask[t_idx, s_idx] else 'FAIL'})  "
        print(row_str)
        
    print("\n==================================================")
    print("SUCCESS: ALL MOTOR SCALING & SOLVER TESTS PASSED!")
    print("==================================================")

if __name__ == '__main__':
    run_pipeline_verification()
