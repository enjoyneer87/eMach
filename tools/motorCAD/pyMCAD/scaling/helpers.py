"""
helpers.py — 공통 유틸리티 함수
MATLAB scaleResistancebyTemp / calcCurrentDensity 대응
"""


def scale_resistance_by_temp(
    R_ref: float,
    T_target: float,
    T_ref: float,
    alpha_cu: float = 0.00393,
) -> float:
    """온도 보정 저항 계산 (구리 기준).

    R(T_target) = R_ref * (1 + alpha * (T_target - T_ref))

    Parameters
    ----------
    R_ref     : 기준 저항 [Ω]
    T_target  : 목표 온도 [°C]
    T_ref     : 기준 온도 [°C]
    alpha_cu  : 구리 온도 계수 [1/°C], 기본값 0.00393
    """
    return R_ref * (1.0 + alpha_cu * (T_target - T_ref))


def calc_current_density(
    I_rms: float,
    parallel_paths: float,
    n_strands: float,
    conductor_csa_mm2: float,
) -> float:
    """전류 밀도 [A/mm²].

    Parameters
    ----------
    I_rms            : RMS 전류 [A]
    parallel_paths   : 병렬 경로 수
    n_strands        : 스트랜드 수 (NumberStrandsHand)
    conductor_csa_mm2: 단면적 [mm²]
    """
    if conductor_csa_mm2 <= 0 or parallel_paths <= 0 or n_strands <= 0:
        return 0.0
    return I_rms / (parallel_paths * n_strands * conductor_csa_mm2)


def parse_mcad_colon_str(value) -> list:
    """Motor-CAD 콜론 구분 문자열 또는 수치값 → float 리스트 변환.

    Motor-CAD ActiveX는 배열을 '1.0:2.0:3.0' 형식 문자열로 반환하는 경우가 있음.
    """
    if isinstance(value, str):
        return [float(x) for x in value.split(":") if x.strip()]
    try:
        return list(value)
    except TypeError:
        return [float(value)]
