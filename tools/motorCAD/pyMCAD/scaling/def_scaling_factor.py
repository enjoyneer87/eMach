"""
def_scaling_factor.py — MATLAB defScalingFactor 대응

사용 예 (JEET):
    defScalingFactor(2, 1, 2, 6, 2, 6, 2)
    → def_scaling_factor(2, 1, 2, 6, 2, 6, 2)
"""
from .models import ScalingFactor, MotorCADGeo


def def_scaling_factor(
    k_radial: float,
    k_axial: float,
    define_type: int,
    *args,
) -> ScalingFactor:
    """스케일링 팩터 구조체를 생성한다.

    Parameters
    ----------
    k_radial    : 반경 방향 스케일 비율
    k_axial     : 축 방향 스케일 비율
    define_type : 0 ~ 3

    define_type=0  args = (k_winding,)
    define_type=1  args = (turns_per_coil, a_p)
                   k_winding은 미결정 — 이후 n_c_ref/a_p_ref로 별도 설정 필요
    define_type=2  args = (turns_per_coil, a_p, n_c_ref, a_p_ref)
                   k_winding = (turns_per_coil/a_p) / (n_c_ref/a_p_ref)
    define_type=3  args = (turns_per_coil, a_p, geo: MotorCADGeo)
                   n_c_ref / a_p_ref 를 geo에서 자동 취득

    Returns
    -------
    ScalingFactor
    """
    factor = ScalingFactor(k_radial=float(k_radial), k_axial=float(k_axial))

    if define_type == 0:
        if len(args) < 1:
            raise ValueError("define_type=0: args에 k_winding 필요")
        factor.k_winding = float(args[0])

    elif define_type == 1:
        if len(args) < 2:
            raise ValueError("define_type=1: args에 (turns_per_coil, a_p) 필요")
        factor.n_c = float(args[0])
        factor.a_p = float(args[1])
        # k_winding 미결정 — 호출자가 ref 정보와 함께 설정해야 함

    elif define_type == 2:
        if len(args) < 4:
            raise ValueError("define_type=2: args에 (turns_per_coil, a_p, n_c_ref, a_p_ref) 필요")
        turns_per_coil = float(args[0])
        a_p            = float(args[1])
        n_c_ref        = float(args[2])
        a_p_ref        = float(args[3])
        factor.n_c       = turns_per_coil
        factor.a_p       = a_p
        factor.k_winding = (turns_per_coil / a_p) / (n_c_ref / a_p_ref)

    elif define_type == 3:
        if len(args) < 3:
            raise ValueError("define_type=3: args에 (turns_per_coil, a_p, geo: MotorCADGeo) 필요")
        turns_per_coil = float(args[0])
        a_p            = float(args[1])
        geo: MotorCADGeo = args[2]
        n_c_ref = (geo.MagTurnsConductor if geo.Armature_CoilStyle == 0
                   else geo.WindingLayers)
        a_p_ref          = geo.ParallelPaths
        factor.n_c       = turns_per_coil
        factor.a_p       = a_p
        factor.k_winding = (turns_per_coil / a_p) / (n_c_ref / a_p_ref)

    else:
        raise ValueError(f"define_type은 0~3이어야 합니다. 입력값: {define_type}")

    return factor
