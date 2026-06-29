from ..model.BaseMotorMap import BaseMotorMap
from ..model.ScaledMotorMap import ScaledMotorMap

def scale_motor_map(base: BaseMotorMap, k_r: float, k_a: float) -> ScaledMotorMap:
    """
    Applies SCL-M scaling laws to a base motor map.
    """
    # 1. Currents scale by k_r (radial scaling factor)
    id_scaled = base.id_grid * k_r
    iq_scaled = base.iq_grid * k_r
    
    # 2. Flux linkages scale by k_a * k_r
    lambda_d_scaled = base.lambda_d * (k_a * k_r)
    lambda_q_scaled = base.lambda_q * (k_a * k_r)
    
    # 3. DC Winding resistance scales by k_a / k_r^2
    r_dc_scaled = base.r_dc * (k_a / (k_r ** 2))
    
    # 4. Iron loss scales by k_a * k_r^2 (volume scaling)
    p_fe_scaled = base.p_fe_grid * (k_a * (k_r ** 2))
    
    # 5. Hybrid AC copper loss grid scales by k_a / k_r^2 (same scaling as DC resistance)
    p_cu_ac_scaled = base.p_cu_ac_hybrid * (k_a / (k_r ** 2))
    
    return ScaledMotorMap(
        id_grid=id_scaled,
        iq_grid=iq_scaled,
        lambda_d=lambda_d_scaled,
        lambda_q=lambda_q_scaled,
        r_dc=r_dc_scaled,
        p_fe_grid=p_fe_scaled,
        p_cu_ac_hybrid=p_cu_ac_scaled,
        k_r=k_r,
        k_a=k_a,
        pole_pairs=base.pole_pairs
    )
