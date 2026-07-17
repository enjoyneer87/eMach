"""1D/2D Hybrid AC copper-loss calculation (Motor-CAD Hybrid method, Python port).

MATLAB 원본 (eMach) 1:1 포팅:
    tools/loss/ACLOSS/calcSkinDepth.m          — 고전 skin depth (MATLAB은 mm 반환, 여기는 m)
    tools/loss/ACLOSS/skin/calcSkinDepthModi.m — 사각도체 이방성 보정 skin depth
    tools/loss/ACLOSS/eqHyperbolic.m           — 하이퍼볼릭 커널 (originx/new1term/new2term)
    tools/loss/ACLOSS/calcSkinEffFun.m         — skin-effect factor phi(xi)
    tools/loss/ACLOSS/calcProxyEffFun.m        — proximity-effect factor psi(xi)
    tools/loss/ACLOSS/AnaProx/calcProxg1.m     — g1 (저주파 근사 계수)
    tools/loss/ACLOSS/AnaProx/calcProxg2.m     — g2 (광대역 하이퍼볼릭 계수)
    tools/loss/ACLOSS/AnaProx/calcProx2DG2Prime.m — 2D (radial/tangential) g2' 계수
    tools/loss/ACLOSS/calcHybridACLossWave.m:60-64 — 2D 결합식
    tools/loss/ACLOSS/MCAD/calcHybridProx1DMCAD.m,
    tools/loss/ACLOSS/MCAD/devCalcMCADHybridACLoss.m:131-139 — MCAD 1D /24 공식
    mlxperPJT/JEET/Calc/calcACLossHybridFromPDF.m — 하모닉 로지스틱 블렌드 (옵션)

수식 요약 (SI, B는 peak 진폭):
    delta  = sqrt(2/(omega*mu0*mu_r*sigma))                       [m]
    gamma  = dim/delta                                            [-]
    g1(gw,gh) = gw*gh^3 / (6*pi^2*mu^2*sigma)                     [W/(m*T^2)]
    g2(gw,gh) = (gw/(sigma*mu^2)) * (sinh gh - sin gh)/(cosh gh + cos gh)
    2D:  P = L*[ g2(gw',gh')*Br^2 + g2(gh',gw')*Bt^2 ]            [W]
    1D(MCAD): P = L*w*h^3*sigma*(omega*B)^2 / 24  (round: pi*d^4*.../128)
    skin: P_skin = P_dc * phi(xi),  phi = xi*(sinh2xi+sin2xi)/(cosh2xi-cos2xi)

핵심 항등성 (테스트로 고정): g2의 저주파 극한 == MCAD /24 공식 (정확히 일치),
g1은 그보다 1/pi^2 작음 (원 논문 정규화 차이).

메시 파싱은 tools/motorCAD/pyMCAD/magnetic_parse.py를 재사용한다 (중복 구현 없음).
"""
from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Section 0 — 물리 상수 (MATLAB 원본과 동일 값)
# ---------------------------------------------------------------------------
RHO_CU_20C = 1.724e-8          # [Ohm*m]  구리 비저항 @20C (calcProxg2.m 등)
SIGMA_CU_20C = 1.0 / RHO_CU_20C  # [S/m]
MU0 = 4.0 * math.pi * 1e-7     # [H/m]
MU_C = MU0                     # 도체 투자율 = mu0 가정 (MATLAB mu_c)
ALPHA_CU = 3.93e-3             # [1/K] 구리 저항 온도계수 (온도보정 옵션용)

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Section 1 — 파라미터 구조
# ---------------------------------------------------------------------------
@dataclass
class ConductorParams:
    """도체 형상/재질. 치수는 mm 입력(_mm 접미사), 내부 계산은 SI(m)."""

    width_mm: float = 3.7          # 도체 폭 w [mm]  (round이면 지름 d)
    height_mm: float = 1.6         # 도체 높이 h [mm]
    active_length_mm: float = 150.0  # 활성(적층) 길이 [mm]
    sigma: float = SIGMA_CU_20C    # 전기전도도 [S/m]
    mu_r: float = 1.0              # 비투자율
    shape: str = "rect"            # 'rect' | 'round'
    temperature_C: float | None = None  # 지정 시 sigma 온도보정
    ref_temperature_C: float = 20.0
    alpha_cu: float = ALPHA_CU

    @property
    def w(self) -> float:
        """폭 [m]"""
        return self.width_mm * 1e-3

    @property
    def h(self) -> float:
        """높이 [m]"""
        return self.height_mm * 1e-3

    @property
    def lactive(self) -> float:
        """활성 길이 [m]"""
        return self.active_length_mm * 1e-3

    @property
    def area(self) -> float:
        """단면적 [m^2]"""
        if self.shape == "round":
            return math.pi * self.w**2 / 4.0
        return self.w * self.h

    @property
    def sigma_eff(self) -> float:
        """온도 보정된 전도도 [S/m]"""
        if self.temperature_C is None:
            return self.sigma
        return self.sigma / (1.0 + self.alpha_cu * (self.temperature_C - self.ref_temperature_C))


@dataclass
class OperatingPoint:
    """운전점. freq_elec_Hz 또는 (speed_rpm, pole_pairs) 중 하나 필수."""

    freq_elec_Hz: float | None = None
    speed_rpm: float | None = None
    pole_pairs: int | None = None
    I_rms_A: float | None = None       # 도체 1개 기준 상전류 RMS [A]
    J_rms_A_per_mm2: float | None = None  # 전류밀도 RMS [A/mm^2]
    B_cuboids_T: np.ndarray | None = None  # 큐보이드(도체)별 peak |B| [T]
    B_peak_T: float | None = None      # 단일 대표 peak |B| [T]

    @property
    def freq(self) -> float:
        if self.freq_elec_Hz is not None:
            return float(self.freq_elec_Hz)
        if self.speed_rpm is not None and self.pole_pairs is not None:
            return speed_to_freq(self.speed_rpm, self.pole_pairs)
        raise ValueError("freq_elec_Hz 또는 (speed_rpm, pole_pairs)가 필요합니다.")


@dataclass
class MotorParams:
    """모터 수준 파라미터: 도체 + 개수/영역 선택 정보."""

    conductor: ConductorParams = field(default_factory=ConductorParams)
    n_conductors: int = 1          # 총 도체(큐보이드) 수
    parallel_paths: int = 1        # 병렬 회로 수 (전류 분배)
    copper_region_pattern: str = r"(?i)copper|conduct|wind|coil|armature|slot"
    copper_reg_codes: tuple[int, ...] | None = None  # 명시적 RegCode 목록 (있으면 우선)


def speed_to_freq(speed_rpm: float, pole_pairs: int) -> float:
    """기계 속도 [rpm] → 전기 주파수 [Hz]"""
    return float(speed_rpm) * float(pole_pairs) / 60.0


def _as_conductor(params) -> ConductorParams:
    if isinstance(params, ConductorParams):
        return params
    if isinstance(params, dict):
        return ConductorParams(**params)
    raise TypeError(f"ConductorParams 또는 dict가 필요합니다: {type(params)}")


def _as_motor(params) -> MotorParams:
    if isinstance(params, MotorParams):
        return params
    if isinstance(params, dict):
        p = dict(params)
        if "conductor" in p and isinstance(p["conductor"], dict):
            p["conductor"] = ConductorParams(**p["conductor"])
        return MotorParams(**p)
    raise TypeError(f"MotorParams 또는 dict가 필요합니다: {type(params)}")


def _as_op(op) -> OperatingPoint:
    if isinstance(op, OperatingPoint):
        return op
    if isinstance(op, dict):
        return OperatingPoint(**op)
    raise TypeError(f"OperatingPoint 또는 dict가 필요합니다: {type(op)}")


# ---------------------------------------------------------------------------
# Section 2 — 커널 함수 (MATLAB 1:1)
# ---------------------------------------------------------------------------
def calc_skin_depth(freq_Hz, sigma: float = SIGMA_CU_20C, mu_r: float = 1.0):
    """고전 skin depth delta = sqrt(2/(omega*mu0*mu_r*sigma)) [m].

    주의: MATLAB calcSkinDepth.m은 **mm**를 반환하지만 이 함수는 **m**를 반환한다.
    """
    omega = 2.0 * math.pi * np.asarray(freq_Hz, dtype=float)
    omega = np.maximum(omega, 1e-30)  # f=0 방어
    return np.sqrt(2.0 / (omega * MU0 * mu_r * sigma))


def calc_skin_depth_modified(dim1_m, dim2_m, freq_Hz, sigma: float = SIGMA_CU_20C,
                             mu_r: float = 1.0):
    """사각도체 이방성 보정 skin depth (calcSkinDepthModi.m).

    delta' = delta * sqrt((dim1 + dim2) / (2*dim2))   [m]
    """
    delta = calc_skin_depth(freq_Hz, sigma, mu_r)
    return delta * math.sqrt((dim1_m + dim2_m) / (2.0 * dim2_m))


def calc_gamma(dim_m, delta_m):
    """무차원 형상 파라미터 gamma = dim/delta (calcNonDimParaGamma.m)."""
    return np.asarray(dim_m, dtype=float) / np.asarray(delta_m, dtype=float)


def eq_hyperbolic(x):
    """하이퍼볼릭 커널 3종 (eqHyperbolic.m).

    originx  = (sinh 2x + sin 2x)/(cosh 2x - cos 2x)
    new1term = 1/2*(sinh x + sin x)/(cosh x - cos x)
    new2term = 1/2*(sinh x - sin x)/(cosh x + cos x)

    수치 안정화: x<1e-2 급수 근사(new2term≈x^3/12 등), x>20 점근값(1, 1/2, 1/2).
    """
    x = np.asarray(x, dtype=float)
    scalar = x.ndim == 0
    x = np.atleast_1d(x)

    small = x < 1e-2
    large = x > 20.0
    mid = ~(small | large)

    originx = np.empty_like(x)
    new1 = np.empty_like(x)
    new2 = np.empty_like(x)

    # 중간 영역: 직접 계산
    xm = x[mid]
    originx[mid] = (np.sinh(2 * xm) + np.sin(2 * xm)) / (np.cosh(2 * xm) - np.cos(2 * xm))
    new1[mid] = 0.5 * (np.sinh(xm) + np.sin(xm)) / (np.cosh(xm) - np.cos(xm))
    new2[mid] = 0.5 * (np.sinh(xm) - np.sin(xm)) / (np.cosh(xm) + np.cos(xm))

    # 소 x: 급수 (상쇄오차 방지). originx ≈ (1/x)(1 + (2x)^4/180)
    xs = np.maximum(x[small], 1e-30)
    originx[small] = (1.0 / xs) * (1.0 + (2.0 * xs) ** 4 / 180.0)
    new1[small] = (1.0 / xs) * (1.0 + xs**4 / 180.0)
    new2[small] = xs**3 / 12.0

    # 대 x: 점근값 (overflow 방지)
    originx[large] = 1.0
    new1[large] = 0.5
    new2[large] = 0.5

    if scalar:
        return float(originx[0]), float(new1[0]), float(new2[0])
    return originx, new1, new2


def skin_effect_factor(xi):
    """skin-effect AC 저항 계수 phi(xi) = xi*originx(xi) (calcSkinEffFun.m).

    저주파 전개: phi ≈ 1 + 4*xi^4/45,  고주파 점근: phi → xi.
    """
    originx, _, _ = eq_hyperbolic(xi)
    return np.asarray(xi, dtype=float) * originx if np.ndim(xi) else float(xi) * originx


def proximity_effect_factor(xi):
    """proximity-effect 계수 psi(xi) = 4*xi*new2term(xi) (calcProxyEffFun.m)."""
    _, _, new2 = eq_hyperbolic(xi)
    return 4.0 * (np.asarray(xi, dtype=float) * new2 if np.ndim(xi) else float(xi) * new2)


# ---------------------------------------------------------------------------
# Section 3 — proximity 계수 (g1 / g2 / f1 / 2D prime)
# ---------------------------------------------------------------------------
def prox_coeff_g1(gamma_w, gamma_h, sigma: float = SIGMA_CU_20C, mu: float = MU_C):
    """g1 = gw*gh^3/(6*mu^2*sigma) — 저주파 근사 (calcProxg1.m, 버그 수정판).

    [FIX 2026-07-14] MATLAB 원본의 분모 6*pi^2는 pi^2(~9.87배) 과소추정 버그였음
    (calcProxg1.m도 동일하게 수정됨). 수정 후 g2 저주파 극한 및 MCAD /24와 항등:
    gw*gh^3/(6*mu^2*sigma) = sigma*omega^2*w*h^3/24.
    """
    return np.asarray(gamma_w, dtype=float) * np.asarray(gamma_h, dtype=float) ** 3 / (
        6.0 * mu**2 * sigma)


def prox_coeff_g2(gamma_w, gamma_h, sigma: float = SIGMA_CU_20C, mu: float = MU_C):
    """g2 = (gw/(sigma*mu^2))*(sinh gh - sin gh)/(cosh gh + cos gh) (calcProxg2.m).

    저주파 극한에서 정확히 w*h^3*sigma*omega^2/24 가 된다 (MCAD /24 공식과 항등).
    """
    _, _, new2 = eq_hyperbolic(gamma_h)
    return (np.asarray(gamma_w, dtype=float) / (sigma * mu**2)) * new2 * 2.0


def prox_coeff_f1(gamma, sigma: float = SIGMA_CU_20C, mu: float = MU_C):
    """f1 = gamma^4/(8*pi*sigma*mu^2) (calcProxf1.m)."""
    return np.asarray(gamma, dtype=float) ** 4 / (8.0 * math.pi * sigma * mu**2)


def calc_prox_2d_g2_prime(width_mm: float, height_mm: float, freq_Hz,
                          sigma: float = SIGMA_CU_20C, mu_r: float = 1.0,
                          use_prime: bool = True):
    """2D proximity 계수 (coeff_radial, coeff_theta) — calcProx2DG2Prime.m 포팅.

    coeff_radial = g2(gw', gh')  — Br^2에 곱함
    coeff_theta  = g2(gh', gw')  — Btheta^2에 곱함
    use_prime=False이면 보정 없는 gamma 사용 (calcProx2DG2.m 동작).
    반환 단위: [W/(m*T^2)] (활성길이 곱하기 전).
    """
    w = width_mm * 1e-3
    h = height_mm * 1e-3
    mu = MU0 * mu_r
    if use_prime:
        delta_w = calc_skin_depth_modified(w, h, freq_Hz, sigma, mu_r)
        delta_h = calc_skin_depth_modified(h, w, freq_Hz, sigma, mu_r)
    else:
        delta_w = calc_skin_depth(freq_Hz, sigma, mu_r)
        delta_h = delta_w
    gamma_w = calc_gamma(w, delta_w)
    gamma_h = calc_gamma(h, delta_h)
    coeff_radial = prox_coeff_g2(gamma_w, gamma_h, sigma, mu)
    coeff_theta = prox_coeff_g2(gamma_h, gamma_w, sigma, mu)
    return coeff_radial, coeff_theta


# ---------------------------------------------------------------------------
# Section 4 — 요구 API 4종
# ---------------------------------------------------------------------------
def calc_skin_effect_1D(freq, J_rms, conductor_params, xi_dim: str = "h") -> float:
    """1D skin effect AC loss (analytical) — 도체 1개 기준 [W].

    P_skin = P_dc * phi(xi),  xi = h/delta (기본; xi_dim='h/2'로 반높이 규약 전환)
    P_dc   = rho * L / A * I_rms^2,  I_rms = J_rms * A

    Parameters
    ----------
    freq : 전기 주파수 [Hz]
    J_rms : 전류밀도 RMS [A/mm^2]
    conductor_params : ConductorParams 또는 dict
    xi_dim : 'h' (기본) | 'h/2' — skin factor의 특성치수 규약
    """
    c = _as_conductor(conductor_params)
    sigma = c.sigma_eff
    delta = float(calc_skin_depth(freq, sigma, c.mu_r))
    dim = c.h if xi_dim == "h" else c.h / 2.0
    xi = dim / delta

    J_si = float(J_rms) * 1e6            # [A/mm^2] → [A/m^2]
    I_rms = J_si * c.area                # [A]
    R_dc = c.lactive / (sigma * c.area)  # [Ohm]
    P_dc = R_dc * I_rms**2
    phi = float(skin_effect_factor(xi))
    return P_dc * phi


def calc_skin_effect_1D_detail(freq, J_rms, conductor_params, xi_dim: str = "h") -> dict:
    """calc_skin_effect_1D의 상세 버전 — 중간량 포함 dict 반환."""
    c = _as_conductor(conductor_params)
    sigma = c.sigma_eff
    delta = float(calc_skin_depth(freq, sigma, c.mu_r))
    dim = c.h if xi_dim == "h" else c.h / 2.0
    xi = dim / delta
    J_si = float(J_rms) * 1e6
    I_rms = J_si * c.area
    R_dc = c.lactive / (sigma * c.area)
    P_dc = R_dc * I_rms**2
    phi = float(skin_effect_factor(xi))
    return {
        "P_total_W": P_dc * phi,
        "P_dc_W": P_dc,
        "P_excess_W": P_dc * (phi - 1.0),
        "phi": phi,
        "xi": xi,
        "skin_depth_m": delta,
        "I_rms_A": I_rms,
        "R_dc_Ohm": R_dc,
    }


def calc_proximity_effect_2D(freq, B_peak, conductor_params,
                             method: str = "g2", use_prime: bool = True) -> float:
    """2D proximity effect AC loss — 도체 1개 기준 [W].

    B_peak가 스칼라면 |B| 크기로 취급: P = L * g2(gw',gh') * B^2
    B_peak가 (Br, Btheta) 튜플이면 2D 결합식 (calcHybridACLossWave.m:63):
        P = L * [ g2(gw',gh')*Br^2 + g2(gh',gw')*Btheta^2 ]

    method : 'g2' (기본, 광대역) | 'g1' (저주파 근사) | 'mcad24' (MCAD /24 공식)
    """
    c = _as_conductor(conductor_params)
    sigma = c.sigma_eff
    mu = MU0 * c.mu_r
    freq = float(freq)

    if isinstance(B_peak, (tuple, list)) and len(B_peak) == 2:
        Br, Bt = float(B_peak[0]), float(B_peak[1])
    else:
        Br, Bt = float(B_peak), 0.0

    if method == "mcad24":
        # MCAD 1D식: Bm = sqrt(Br^2+Bt^2), 방향 구분 없음
        omega = 2.0 * math.pi * freq
        Bm2 = Br**2 + Bt**2
        if c.shape == "round":
            return c.lactive * math.pi * c.w**4 * sigma * omega**2 * Bm2 / 128.0
        return c.lactive * c.w * c.h**3 * sigma * omega**2 * Bm2 / 24.0

    if method == "g1":
        if use_prime:
            delta_w = calc_skin_depth_modified(c.w, c.h, freq, sigma, c.mu_r)
            delta_h = calc_skin_depth_modified(c.h, c.w, freq, sigma, c.mu_r)
        else:
            delta_w = delta_h = calc_skin_depth(freq, sigma, c.mu_r)
        gw = calc_gamma(c.w, delta_w)
        gh = calc_gamma(c.h, delta_h)
        cr = prox_coeff_g1(gw, gh, sigma, mu)
        ct = prox_coeff_g1(gh, gw, sigma, mu)
        return float(c.lactive * (cr * Br**2 + ct * Bt**2))

    if method == "g2":
        cr, ct = calc_prox_2d_g2_prime(c.width_mm, c.height_mm, freq,
                                       sigma, c.mu_r, use_prime=use_prime)
        return float(c.lactive * (cr * Br**2 + ct * Bt**2))

    raise ValueError(f"지원하지 않는 method: {method!r} ('g2'|'g1'|'mcad24')")


def calc_hybrid_ac_loss_1D(motor_params, operating_point, xi_dim: str = "h") -> dict:
    """Motor-CAD Hybrid 모드 1D 방식 — 도체 형상 + 전류밀도 기반.

    P_skin  = n_conductors * P_dc(도체당) * phi(xi)     (skin effect, 전류 기반)
    P_prox  = sum_i L*w*h^3*sigma*(omega*B_i)^2/24      (큐보이드별, MCAD /24 공식)
              (round 도체: pi*d^4*sigma*(omega*B_i)^2/128)

    operating_point에 B_cuboids_T(배열) 또는 B_peak_T(스칼라, 전 도체 동일 가정)를
    주면 proximity 항을 계산하고, 없으면 P_prox=0 (skin만).

    Returns dict: P_skin_W, P_prox_W, P_ac_total_W, P_dc_W, skin_depth_m, xi,
                  phi, freq_Hz, per_cuboid_W
    """
    m = _as_motor(motor_params)
    op = _as_op(operating_point)
    c = m.conductor
    sigma = c.sigma_eff
    freq = op.freq
    omega = 2.0 * math.pi * freq

    # --- skin effect (전류 기반) -------------------------------------------
    if op.J_rms_A_per_mm2 is not None:
        J_rms = float(op.J_rms_A_per_mm2)
    elif op.I_rms_A is not None:
        J_rms = float(op.I_rms_A) / float(m.parallel_paths) / (c.area * 1e6)
    else:
        J_rms = 0.0

    delta = float(calc_skin_depth(freq, sigma, c.mu_r))
    dim = c.h if xi_dim == "h" else c.h / 2.0
    xi = dim / delta
    phi = float(skin_effect_factor(xi))

    J_si = J_rms * 1e6
    I_cond = J_si * c.area
    R_dc = c.lactive / (sigma * c.area)
    P_dc_per = R_dc * I_cond**2
    P_dc = m.n_conductors * P_dc_per
    P_skin = P_dc * phi

    # --- proximity (큐보이드별 /24 공식) ------------------------------------
    if op.B_cuboids_T is not None:
        B = np.asarray(op.B_cuboids_T, dtype=float)
    elif op.B_peak_T is not None:
        B = np.full(m.n_conductors, float(op.B_peak_T))
    else:
        B = np.zeros(0)

    if c.shape == "round":
        per_cuboid = c.lactive * math.pi * c.w**4 * sigma * (omega * B) ** 2 / 128.0
    else:
        per_cuboid = c.lactive * c.w * c.h**3 * sigma * (omega * B) ** 2 / 24.0
    P_prox = float(np.sum(per_cuboid))

    return {
        "P_skin_W": P_skin,
        "P_prox_W": P_prox,
        "P_ac_total_W": P_skin + P_prox,
        "P_dc_W": P_dc,
        "P_skin_excess_W": P_dc * (phi - 1.0),
        "phi": phi,
        "xi": xi,
        "skin_depth_m": delta,
        "freq_Hz": freq,
        "per_cuboid_W": per_cuboid,
        "method": "MCAD_hybrid_1D(/24)" if c.shape != "round" else "MCAD_hybrid_1D(/128)",
    }


def calc_hybrid_ac_loss_2D(motor_params, operating_point,
                           mesh=None, mesh_file=None,
                           mode: str = "peak",
                           method: str = "g2", use_prime: bool = True,
                           field_frame: str = "radial",
                           b_is_rms: bool = False,
                           cycle_fraction: float = 1.0,
                           apply_pdf_blend: bool = False,
                           pdf_blend_opts: dict | None = None) -> dict:
    """Motor-CAD Hybrid 모드 2D 방식 — 메시 데이터 기반.

    파이프라인:
      1. 메시 파싱 (mesh_file 경로 또는 파싱된 mesh 객체)
      2. copper_region_pattern / copper_reg_codes로 구리(도체) 영역 선택
      3. 영역별 면적가중 평균 (Bx, By)
      4. field_frame='radial'이면 도체 중심각 기준 (Br, Btheta)로 회전
      5. mode='peak' : 단일 스냅샷 B를 f_elec 정현파 peak로 가정 (MCAD Hybrid 가정)
         mode='fft'  : rotate-step 시계열 rFFT → 하모닉별 g2' 계수 적용 후 합산
      6. P = L * sum[ cr(f)*Br^2 + ct(f)*Bt^2 ]  (도체별 합산)

    Parameters
    ----------
    mesh : MagneticRegions(단일) | MagneticRegionsTimeSeries(시계열) | None
    mesh_file : Motor-CAD 내보내기 txt 경로 (mesh 미지정 시 파싱)
    mode : 'peak' | 'fft'
    cycle_fraction : 시계열이 전기 1주기의 몇 배를 커버하는지 (예: 60도 모델=1/6)
    b_is_rms : 메시 B가 RMS이면 True (peak로 환산 x sqrt(2))
    apply_pdf_blend : calcACLossHybridFromPDF.m의 로지스틱 블렌드+HF gain 적용

    Returns dict: P_prox_total_W, per_conductor, freq_Hz, coeff_radial, coeff_theta,
                  (fft 모드) harmonics
    """
    m = _as_motor(motor_params)
    op = _as_op(operating_point)
    c = m.conductor
    sigma = c.sigma_eff
    freq = op.freq

    # --- 1. 메시 확보 -------------------------------------------------------
    if mesh is None:
        if mesh_file is None:
            raise ValueError("mesh 또는 mesh_file 중 하나가 필요합니다.")
        if mode == "fft":
            mesh = parse_magnetic_timeseries(mesh_file)
        else:
            mesh = parse_magnetic_snapshot(mesh_file)

    is_timeseries = hasattr(mesh, "by_step")
    if mode == "fft" and not is_timeseries:
        raise ValueError("mode='fft'에는 시계열 메시(MagneticRegionsTimeSeries)가 필요합니다.")

    b_scale = math.sqrt(2.0) if b_is_rms else 1.0

    # --- 2~4. 도체별 (Br, Bt) 추출 -----------------------------------------
    if is_timeseries:
        steps = list(mesh.steps)
        snap0 = mesh.by_step[steps[0]]
        conductors = _select_conductor_regions(snap0, m)
        # (n_steps, n_cond) 행렬
        br_mat = np.zeros((len(steps), len(conductors)))
        bt_mat = np.zeros((len(steps), len(conductors)))
        for si, s in enumerate(steps):
            snap = mesh.by_step[s]
            for ci, cond in enumerate(conductors):
                bx, by = _region_mean_B(snap, cond["reg_code"])
                br, bt = _to_frame(bx, by, cond["centroid_xy"], field_frame)
                br_mat[si, ci] = br * b_scale
                bt_mat[si, ci] = bt * b_scale
    else:
        conductors = _select_conductor_regions(mesh, m)
        br_mat = np.zeros((1, len(conductors)))
        bt_mat = np.zeros((1, len(conductors)))
        for ci, cond in enumerate(conductors):
            bx, by = _region_mean_B(mesh, cond["reg_code"])
            br, bt = _to_frame(bx, by, cond["centroid_xy"], field_frame)
            br_mat[0, ci] = br * b_scale
            bt_mat[0, ci] = bt * b_scale

    if not conductors:
        raise ValueError(
            "구리 영역을 찾지 못했습니다. copper_region_pattern 또는 copper_reg_codes를 확인하세요.")

    per_conductor = []
    harmonics_out = None

    # --- 5~6. 손실 계산 ------------------------------------------------------
    if mode == "peak":
        cr, ct = _prox_coeff(c, freq, sigma, method, use_prime)
        blend = _pdf_blend_factor(np.array([freq]), c, sigma, pdf_blend_opts)[0] \
            if apply_pdf_blend else 1.0
        for ci, cond in enumerate(conductors):
            Br, Bt = br_mat[-1, ci], bt_mat[-1, ci]
            P = c.lactive * (cr * Br**2 + ct * Bt**2) * blend
            per_conductor.append({**cond, "Br_T": Br, "Bt_T": Bt, "P_W": float(P)})
        coeff_out = (float(cr), float(ct))

    elif mode == "fft":
        n_steps = br_mat.shape[0]
        # rotate-step이 균일 간격으로 cycle_fraction 주기를 커버한다고 가정
        k = np.arange(1, n_steps // 2 + 1)          # DC 제외
        orders = k / float(cycle_fraction)          # 전기 기본파 기준 하모닉 차수
        freq_list = orders * freq
        cr_k, ct_k = _prox_coeff(c, freq_list, sigma, method, use_prime)
        blend_k = _pdf_blend_factor(freq_list, c, sigma, pdf_blend_opts) \
            if apply_pdf_blend else np.ones_like(freq_list)

        harmonics_out = {"orders": orders, "freq_Hz": freq_list,
                         "coeff_radial": cr_k, "coeff_theta": ct_k}
        for ci, cond in enumerate(conductors):
            Br_amp = _fft_peak_amplitudes(br_mat[:, ci])   # 길이 n_steps//2
            Bt_amp = _fft_peak_amplitudes(bt_mat[:, ci])
            P_k = c.lactive * (cr_k * Br_amp**2 + ct_k * Bt_amp**2) * blend_k
            per_conductor.append({**cond,
                                  "Br_harm_T": Br_amp, "Bt_harm_T": Bt_amp,
                                  "P_harm_W": P_k, "P_W": float(np.sum(P_k))})
        coeff_out = (cr_k, ct_k)
    else:
        raise ValueError(f"지원하지 않는 mode: {mode!r} ('peak'|'fft')")

    P_total = float(sum(pc["P_W"] for pc in per_conductor))
    return {
        "P_prox_total_W": P_total,
        "per_conductor": per_conductor,
        "n_conductors_found": len(conductors),
        "freq_Hz": freq,
        "coeff_radial": coeff_out[0],
        "coeff_theta": coeff_out[1],
        "harmonics": harmonics_out,
        "mode": mode,
        "method": method + ("_prime" if use_prime else ""),
    }


# --- 내부 헬퍼 --------------------------------------------------------------
def _prox_coeff(c: ConductorParams, freq, sigma, method, use_prime):
    """(coeff_radial, coeff_theta) 계산 [W/(m*T^2)]."""
    mu = MU0 * c.mu_r
    freq = np.asarray(freq, dtype=float)
    if method == "mcad24":
        omega = 2.0 * math.pi * freq
        if c.shape == "round":
            coef = math.pi * c.w**4 * sigma * omega**2 / 128.0
        else:
            coef = c.w * c.h**3 * sigma * omega**2 / 24.0
        return coef, coef
    if use_prime:
        delta_w = calc_skin_depth_modified(c.w, c.h, freq, sigma, c.mu_r)
        delta_h = calc_skin_depth_modified(c.h, c.w, freq, sigma, c.mu_r)
    else:
        delta_w = delta_h = calc_skin_depth(freq, sigma, c.mu_r)
    gw = calc_gamma(c.w, delta_w)
    gh = calc_gamma(c.h, delta_h)
    fn = prox_coeff_g1 if method == "g1" else prox_coeff_g2
    return fn(gw, gh, sigma, mu), fn(gh, gw, sigma, mu)


def _fft_peak_amplitudes(x: np.ndarray) -> np.ndarray:
    """실수 시계열 → 하모닉 peak 진폭 (DC 제외, 길이 N//2)."""
    n = len(x)
    spec = np.fft.rfft(np.asarray(x, dtype=float))
    amp = 2.0 * np.abs(spec) / n
    if n % 2 == 0:
        amp[-1] = np.abs(spec[-1]) / n  # Nyquist 성분은 2배 금지
    return amp[1:]  # DC 제외


def _pdf_blend_factor(freq_list: np.ndarray, c: ConductorParams, sigma,
                      opts: dict | None) -> np.ndarray:
    """calcACLossHybridFromPDF.m의 로지스틱 블렌드+HF gain 배율.

    factor = (1-alpha) + alpha*hfGain
    fT = 2/(2*pi*mu0*mu_r*sigma*h_bundle^2), tau = sharpness*fT,
    alpha = 1/(1+exp(-(f-fT)/tau)), hfGain = max(1, h_bundle/delta)^exp
    """
    o = dict(opts or {})
    h_bundle = float(o.get("bundle_height_m", c.h))
    exp_ = float(o.get("skin_depth_exp", 1.0))
    sharp = float(o.get("transition_sharpness", 0.20))
    mu = MU0 * c.mu_r

    freq_list = np.asarray(freq_list, dtype=float)
    omega = 2.0 * math.pi * np.maximum(freq_list, 1e-9)
    delta = np.sqrt(2.0 / (omega * mu * sigma))
    fT = 2.0 / (2.0 * math.pi * mu * sigma * h_bundle**2)
    tau = max(sharp * max(fT, 1.0), 1e-9)
    with np.errstate(over="ignore"):
        alpha = 1.0 / (1.0 + np.exp(-(freq_list - fT) / tau))
    hf_gain = np.maximum(1.0, h_bundle / np.maximum(delta, 1e-300)) ** exp_
    return (1.0 - alpha) + alpha * hf_gain


def _select_conductor_regions(mag_regions, m: MotorParams) -> list[dict]:
    """MagneticRegions에서 구리(도체) 영역 목록 추출."""
    out = []
    pattern = re.compile(m.copper_region_pattern)
    for idx in range(len(mag_regions)):
        region = mag_regions[idx]
        if not region.elements:
            continue
        reg_code = region.reg_code or (idx + 1)
        name = region.region_name or ""
        if m.copper_reg_codes is not None:
            if reg_code not in m.copper_reg_codes:
                continue
        elif not pattern.search(name):
            continue
        cx, cy, _ = _region_centroid_area(mag_regions, reg_code)
        out.append({"reg_code": reg_code, "region_name": name, "centroid_xy": (cx, cy)})
    return out


def _tri_area_mm2(mag_regions, el) -> float | None:
    """삼각형 요소 면적 [mm^2] (node 좌표 없으면 None)."""
    n1 = mag_regions.node_xy.get(el.node_1)
    n2 = mag_regions.node_xy.get(el.node_2)
    n3 = mag_regions.node_xy.get(el.node_3)
    if n1 is None or n2 is None or n3 is None:
        return None
    return 0.5 * abs(n1[0] * (n2[1] - n3[1]) + n2[0] * (n3[1] - n1[1]) + n3[0] * (n1[1] - n2[1]))


def _region_mean_B(mag_regions, reg_code: int) -> tuple[float, float]:
    """영역의 면적가중 평균 (Bx, By) [T]. 좌표 없으면 단순 평균."""
    region = mag_regions[reg_code - 1]
    bx_sum = by_sum = w_sum = 0.0
    for el in region.elements:
        if el.bx is None or el.by is None:
            continue
        a = _tri_area_mm2(mag_regions, el)
        w = a if a is not None and a > 0 else 1.0
        bx_sum += el.bx * w
        by_sum += el.by * w
        w_sum += w
    if w_sum == 0.0:
        return 0.0, 0.0
    return bx_sum / w_sum, by_sum / w_sum


def _region_centroid_area(mag_regions, reg_code: int):
    """영역 면적가중 중심 (x_mm, y_mm)과 총면적 [mm^2]."""
    region = mag_regions[reg_code - 1]
    x_sum = y_sum = a_sum = 0.0
    n_fallback = 0
    for el in region.elements:
        c_xy = mag_regions._element_centroid_xy(el)
        if c_xy is None:
            n_fallback += 1
            continue
        a = _tri_area_mm2(mag_regions, el) or 1.0
        x_sum += c_xy[0] * a
        y_sum += c_xy[1] * a
        a_sum += a
    if a_sum == 0.0:
        return 0.0, 0.0, 0.0
    return x_sum / a_sum, y_sum / a_sum, a_sum


def _to_frame(bx: float, by: float, centroid_xy: tuple[float, float],
              field_frame: str) -> tuple[float, float]:
    """(Bx, By) → field_frame 좌표 성분.

    'radial': 도체 중심각 theta 기준 Br = Bx cos + By sin, Bt = -Bx sin + By cos
    'xy'    : 그대로 (Bx→radial 슬롯, By→tangential 취급; 직교라 손실합은 회전불변이
              아님 — g2 계수가 방향별로 다르므로 frame 선택이 결과에 영향)
    """
    if field_frame == "xy":
        return bx, by
    x, y = centroid_xy
    r = math.hypot(x, y)
    if r < 1e-12:
        return bx, by
    ct, st = x / r, y / r
    br = bx * ct + by * st
    bt = -bx * st + by * ct
    return br, bt


# ---------------------------------------------------------------------------
# Section 5 — 메시 텍스트 파일 파싱 (tools/motorCAD/pyMCAD 재사용)
# ---------------------------------------------------------------------------
def _load_pymcad_parsers():
    """magnetic_parse 모듈 로드. 정규 패키지 import 우선, 실패 시 개별 로드 폴백.

    pyMCAD/__init__.py가 h5py 등 무거운 의존성을 즉시 import하므로,
    ImportError 시 magnetic_model + magnetic_parse만 합성 패키지로 로드한다.
    """
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    try:
        from tools.motorCAD.pyMCAD import magnetic_parse as mp  # noqa: PLC0415
        return mp
    except ImportError:
        pass

    # 폴백: 합성 패키지로 필요한 두 모듈만 로드
    import importlib.util
    import types

    pkg_dir = _REPO_ROOT / "tools" / "motorCAD" / "pyMCAD"
    pkg_name = "_acloss_pymcad"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(pkg_dir)]
        sys.modules[pkg_name] = pkg
    for mod_name in ("magnetic_model", "magnetic_parse"):
        full = f"{pkg_name}.{mod_name}"
        if full in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(full, pkg_dir / f"{mod_name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
    return sys.modules[f"{pkg_name}.magnetic_parse"]


def parse_magnetic_snapshot(path):
    """Motor-CAD 내보내기 txt의 첫 블록(Elements/Nodes/Regions) 파싱 → MagneticRegions.

    포맷: 콤마 구분, 'N <count> ElementsTable' 헤더 + 4줄 프리앰블
    (빈줄/컬럼명/단위/구분선), 컬럼 TriIndex,Node1..3,RegCode,Bx,By,A,J[,Je,Hx,Hy,Mur].
    인코딩 자동감지 (UTF-16 BOM / UTF-8-sig / cp949).
    """
    mp = _load_pymcad_parsers()
    return mp._parse_first_block_magnetic_file(path)


def parse_magnetic_timeseries(path, key: str = "time_index", max_blocks=None):
    """다중 스텝 txt 파싱 → MagneticRegionsTimeSeries (rotate step별 블록)."""
    mp = _load_pymcad_parsers()
    return mp._parse_magnetic_timeseries_txt(path, key=key, max_blocks=max_blocks)


def extract_conductor_B(mesh, region_pattern: str | None = None,
                        reg_codes=None, field_frame: str = "radial") -> list[dict]:
    """파싱된 메시에서 도체별 면적가중 평균 B 추출.

    Returns list of dict: reg_code, region_name, centroid_xy, Bx_T, By_T, Br_T, Bt_T
    """
    m = MotorParams()
    if region_pattern is not None:
        m.copper_region_pattern = region_pattern
    if reg_codes is not None:
        m.copper_reg_codes = tuple(reg_codes)
    conductors = _select_conductor_regions(mesh, m)
    out = []
    for cond in conductors:
        bx, by = _region_mean_B(mesh, cond["reg_code"])
        br, bt = _to_frame(bx, by, cond["centroid_xy"], field_frame)
        out.append({**cond, "Bx_T": bx, "By_T": by, "Br_T": br, "Bt_T": bt})
    return out


# ---------------------------------------------------------------------------
# Section 6 — 데모
# ---------------------------------------------------------------------------
def _demo():
    """3.7 x 1.6 mm 도체 주파수 스윕: 1D vs 2D 방법 비교."""
    cond = ConductorParams(width_mm=3.7, height_mm=1.6, active_length_mm=150.0)
    motor = MotorParams(conductor=cond, n_conductors=48)
    B_peak = 0.05  # [T]
    J_rms = 5.0    # [A/mm^2]

    print(f"도체: {cond.width_mm} x {cond.height_mm} mm, L={cond.active_length_mm} mm, "
          f"n={motor.n_conductors}, B_peak={B_peak} T, J_rms={J_rms} A/mm^2")
    print(f"{'f [Hz]':>8} {'delta[mm]':>10} {'phi':>8} {'P_skin[W]':>10} "
          f"{'P_/24[W]':>10} {'P_g2[W]':>10} {'P_g1[W]':>10}")
    for f_e in (50, 200, 500, 1000, 2000, 4000):
        op = OperatingPoint(freq_elec_Hz=f_e, J_rms_A_per_mm2=J_rms, B_peak_T=B_peak)
        r1 = calc_hybrid_ac_loss_1D(motor, op)
        p24 = motor.n_conductors * calc_proximity_effect_2D(f_e, B_peak, cond, method="mcad24")
        pg2 = motor.n_conductors * calc_proximity_effect_2D(f_e, B_peak, cond, method="g2")
        pg1 = motor.n_conductors * calc_proximity_effect_2D(f_e, B_peak, cond, method="g1")
        print(f"{f_e:>8} {r1['skin_depth_m']*1e3:>10.3f} {r1['phi']:>8.4f} "
              f"{r1['P_skin_W']:>10.3f} {p24:>10.3f} {pg2:>10.3f} {pg1:>10.3f}")

    print("\n저주파(1 Hz) g2 vs /24 항등성 확인:")
    pg2_lf = calc_proximity_effect_2D(1.0, B_peak, cond, method="g2", use_prime=False)
    p24_lf = calc_proximity_effect_2D(1.0, B_peak, cond, method="mcad24")
    print(f"  g2(non-prime)={pg2_lf:.6e} W, /24={p24_lf:.6e} W, "
          f"상대오차={abs(pg2_lf - p24_lf)/p24_lf:.3e}")


if __name__ == "__main__":
    _demo()
