import numpy as np
from ..model.BaseMotorMap import BaseMotorMap
from ..model.RbfModelParams import RbfModelParams
from ..model.EfficiencyMap import EfficiencyMap
from .MotorScaler import scale_motor_map
from .MtpaFwSolver import MtpaFwSolver

def generate_efficiency_map(
    base_map: BaseMotorMap,
    k_r: float,
    k_a: float,
    rbf_model: RbfModelParams,
    speeds_rpm: np.ndarray,
    torques_ref: np.ndarray,
    v_max: float,
    i_max: float,
    r_ac_factor: float = 1.0
) -> EfficiencyMap:
    """
    Composes the scaling, AC loss correction, and MTPA/FW solver morphisms
    to generate a complete 2D efficiency map over the given speed and torque ranges.
    """
    # 1. Scale the motor map
    scaled_map = scale_motor_map(base_map, k_r, k_a)
    
    # 2. Initialize grids
    n_speed = len(speeds_rpm)
    n_torque = len(torques_ref)
    
    id_opt_grid = np.zeros((n_torque, n_speed))
    iq_opt_grid = np.zeros((n_torque, n_speed))
    voltage_grid = np.zeros((n_torque, n_speed))
    loss_total_grid = np.zeros((n_torque, n_speed))
    loss_cu_dc_grid = np.zeros((n_torque, n_speed))
    loss_cu_ac_grid = np.zeros((n_torque, n_speed))
    loss_fe_grid = np.zeros((n_torque, n_speed))
    efficiency_grid = np.zeros((n_torque, n_speed))
    success_grid = np.zeros((n_torque, n_speed), dtype=bool)
    
    speed_grid, torque_grid = np.meshgrid(speeds_rpm, torques_ref)
    
    # 3. Sweep speed and torque grids
    for s_idx, speed in enumerate(speeds_rpm):
        for t_idx, torque in enumerate(torques_ref):
            # Run MTPA & FW solver for this point
            sol = MtpaFwSolver.solve(
                torque_ref=torque,
                speed_rpm=speed,
                map_data=scaled_map,
                rbf_model=rbf_model,
                v_max=v_max,
                i_max=i_max,
                r_ac_factor=r_ac_factor
            )
            
            id_opt_grid[t_idx, s_idx] = sol['id_opt']
            iq_opt_grid[t_idx, s_idx] = sol['iq_opt']
            voltage_grid[t_idx, s_idx] = sol['voltage']
            loss_total_grid[t_idx, s_idx] = sol['loss_total']
            loss_cu_dc_grid[t_idx, s_idx] = sol['loss_cu_dc']
            loss_cu_ac_grid[t_idx, s_idx] = sol['loss_cu_ac']
            loss_fe_grid[t_idx, s_idx] = sol['loss_fe']
            success_grid[t_idx, s_idx] = sol['success']
            
            # 4. Calculate Efficiency
            # Mechanical power: P_mech = Torque * omega_mech [kW]
            omega_mech = speed * 2 * np.pi / 60.0
            p_mech = torque * omega_mech / 1000.0
            p_loss = sol['loss_total']
            
            if torque >= 0:  # Motoring
                p_in = p_mech + p_loss
                if p_in > 0:
                    eff = (p_mech / p_in) * 100.0
                else:
                    eff = 0.0
            else:  # Generating
                p_out = p_mech + p_loss  # Note: p_mech is negative, p_loss is positive, p_out is negative
                if p_mech < 0:
                    # Capture efficiency: output power / input mechanical power
                    # Since both are negative, we take absolute or p_out / p_mech
                    eff = (p_out / p_mech) * 100.0
                else:
                    eff = 0.0
                    
            efficiency_grid[t_idx, s_idx] = np.clip(eff, 0.0, 100.0)
            
    return EfficiencyMap(
        speeds_rpm=speeds_rpm,
        torques_ref=torques_ref,
        speed_grid=speed_grid,
        torque_grid=torque_grid,
        id_opt=id_opt_grid,
        iq_opt=iq_opt_grid,
        voltage=voltage_grid,
        loss_total=loss_total_grid,
        loss_cu_dc=loss_cu_dc_grid,
        loss_cu_ac=loss_cu_ac_grid,
        loss_fe=loss_fe_grid,
        efficiency=efficiency_grid,
        success_mask=success_grid,
        k_r=k_r,
        k_a=k_a
    )
