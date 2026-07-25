# -*- coding: utf-8 -*-
"""도체 이방성(폭방향 확산)이 근접손실에 미치는 영향을 정량화한다.

두 가지 근접손실(proximity loss) 계산법을 비교한다.

  (A) CURRENT / single-g  (논문 eq (3)):
        하나의 커널 g 를 두 성분(B_r, B_theta)에 공통으로 적용한다.
            P_A = sum_m g(eta_hc) * l_a * (B_r,m^2 + B_theta,m^2)
        여기서 eta_hc = h_c/delta 이고 h_c 는 **큰** 도체 치수(=접선 확장
        t_t) 하나만 쓴다. 즉 확산 차원 d_perp = t_t, d_par = t_r.

  (B) COMPONENT-SPECIFIC (이방성/폭방향 확산 포함, 엄밀형):
            P_B = sum_m [ g(eta_tr) * B_theta,m^2 + g(eta_tt) * B_r,m^2 ]
        각 성분이 **자기** 수직 차원으로 확산한다.

성분<->차원 짝짓기 (벡터퍼텐셜 J_z ∝ omega*A_z 로 1차원리 검증):
  · B_theta (접선장) -> A_z = -B_theta * u(반경좌표) -> 와전류가 반경으로
    분포 -> 반경 확장 t_r 을 가로질러 확산.  eta_tr = t_r/delta,
    g 의 d_perp = t_r, d_par = t_t.
  · B_r (반경장) -> A_z = +B_r * v(접선좌표) -> 접선 확장 t_t 를 가로질러
    확산.  eta_tt = t_t/delta,  g 의 d_perp = t_t, d_par = t_r.

커널 (논문 eq:g_kernel, MATLAB calcProxyEffFun/eqHyperbolic 와 동일):
    g(eta) = (d_par / (d_perp * sigma * mu0^2)) * eta * K(eta)
    K(eta) = (sinh(eta) - sin(eta)) / (cosh(eta) + cos(eta))
    delta  = 1 / sqrt(pi * f * mu0 * sigma)          # = 1/sqrt(0.5*w*mu0*sigma)

핵심 관찰: 헤어핀 도체는 반경으로 얇고(t_r) 접선으로 넓다(t_t). 지배적인
슬롯누설장은 접선(B_theta)이라 실제로는 **얇은** 반경 차원으로 확산하는데,
방법 A 는 이를 **큰** 접선 차원(h_c=t_t)으로 확산한다고 보아 저속에서
과대평가한다. 두 커널의 대소는 주파수에 따라 뒤집혀(저주파 G_t>G_r,
고주파 G_r>G_t) 비율 R=P_A/P_B 이 속도에 따라 1 을 가로지른다.

사용 예:
    from jeet_acloss_rbf.proximity_anisotropy import (
        conductor_geometry, energy_split, compare_over_speed)
    geo = conductor_geometry(ts_path, slot_id=1)     # 순동(TS-FEA) 치수
    fth = energy_split(hybrid_path)['f_theta']        # 접선 에너지 분율
    res = compare_over_speed(geo['t_r_m'], geo['t_t_m'], fth)
"""
from __future__ import annotations

import os
from typing import Dict, Optional, Sequence

import numpy as np

from .field_metrics import parse_mes_txt, slot_conductor_codes, _tangential_b

__all__ = ["kernel_K", "skin_depth", "g_kernel", "kernel_factor",
           "conductor_geometry", "energy_split", "compare_over_speed",
           "SIGMA_CU_20C", "MU0", "POLE_PAIRS"]

# 상수 (과제 지정): 20 degC 구리
SIGMA_CU_20C = 1.0 / 1.724e-8            # ~5.80e7 S/m
MU0 = 4.0e-7 * np.pi                      # H/m
POLE_PAIRS = 4


def kernel_K(eta: np.ndarray) -> np.ndarray:
    """Dowell/Ferreira 근접 커널 K(eta)=(sinh-sin)/(cosh+cos).

    저 eta 극한 K ~ eta^3/6 (손실 ~ f^2), 고 eta 극한 K -> 1.
    """
    eta = np.asarray(eta, float)
    return (np.sinh(eta) - np.sin(eta)) / (np.cosh(eta) + np.cos(eta))


def skin_depth(freq_hz: float, sigma: float = SIGMA_CU_20C,
               mu0: float = MU0) -> float:
    """표피 깊이 delta = 1/sqrt(pi f mu0 sigma) [m] (=1/sqrt(0.5 w mu0 sigma))."""
    return 1.0 / np.sqrt(np.pi * freq_hz * mu0 * sigma)


def g_kernel(eta: np.ndarray, d_perp_m: float, d_par_m: float,
             sigma: float = SIGMA_CU_20C, mu0: float = MU0) -> np.ndarray:
    """전체 커널 g(eta) = (d_par/(d_perp sigma mu0^2)) eta K(eta).

    d_perp : 확산(수직) 차원 [m], d_par : 나머지(평행) 차원 [m].
    반환은 B^2 을 곱하면 단위길이당 손실 밀도가 되는 물리 계수.
    비율 R 만 필요하면 공통 상수(1/(sigma mu0^2))는 상쇄되므로
    ``kernel_factor`` 를 쓰면 된다.
    """
    return (d_par_m / (d_perp_m * sigma * mu0 ** 2)) * eta * kernel_K(eta)


def kernel_factor(d_perp_m: float, d_par_m: float, freq_hz: float,
                  sigma: float = SIGMA_CU_20C, mu0: float = MU0) -> float:
    """비율 계산용 무차원 커널 계수 (d_par/d_perp) * eta * K(eta).

    공통 상수 1/(sigma mu0^2) 를 뺀 형태 --- R=P_A/P_B 에서 상쇄된다.
    eta = d_perp/delta.
    """
    eta = d_perp_m / skin_depth(freq_hz, sigma, mu0)
    return (d_par_m / d_perp_m) * eta * kernel_K(eta)


def conductor_geometry(path: str, slot_id: int = 1) -> dict:
    """한 슬롯 도체들의 평균 반경/접선 확장(t_r, t_t)을 메시에서 뽑는다.

    **순동 치수가 필요하므로 TS-FEA(``Turn_*``) 파일을 넘길 것.** MS-FEA
    (``ArmatureSlot*``) 셀은 함침을 포함해 약 25% 크다(field_metrics 참조).
    와전류는 구리에서만 흐르므로 커널 차원은 순동 치수여야 한다.

    Returns ``{'t_r_mm','t_t_mm','t_r_m','t_t_m','h_c_mm','n_bars'}``.
    t_r = 반경(작은) 확장, t_t = 접선(큰) 확장, h_c = max(t_r,t_t) = 논문 단일치수.
    """
    from .field_metrics import slot_bar_geometry
    p = parse_mes_txt(path)
    bars = slot_bar_geometry(p, slot_id)
    if not bars:
        raise ValueError('슬롯 %d 도체를 찾지 못함: %s' % (slot_id, path))
    t_r = float(np.mean([b['h_mm'] for b in bars]))   # local x = 반경
    t_t = float(np.mean([b['w_mm'] for b in bars]))   # local y = 접선
    return {'t_r_mm': t_r, 't_t_mm': t_t,
            't_r_m': t_r * 1e-3, 't_t_m': t_t * 1e-3,
            'h_c_mm': max(t_r, t_t), 'n_bars': len(bars),
            'source': os.path.basename(path)}


def energy_split(path: str, slots: Sequence[int] = range(1, 7),
                 per_conductor: bool = True) -> dict:
    """슬롯 도체에서 접선/반경 자속밀도 에너지 분율을 계산한다.

    **MS-FEA(Hybrid) 파일을 넘길 것** --- 도체에 와전류가 없어 내부 B 가
    곧 근접 구동장이다. f_theta = sum(B_theta^2)/sum(B_r^2+B_theta^2).

    ``per_conductor=True``: 도체별 면적가중 평균장을 먼저 구하고 그
    제곱을 도체에 걸쳐 합한다(논문 sum_m 형태). False 면 요소별
    면적가중 제곱합.

    Returns ``{'f_theta','f_r','S_theta','S_r','n_cond', ...}``.
    """
    p = parse_mes_txt(path)
    x, y = p['x_mm'], p['y_mm']
    r = np.hypot(x, y)
    br = (p['bx'] * x + p['by'] * y) / r          # 반경 성분 (부호 있음)
    bt = _tangential_b(p)                          # 접선 성분 (부호 있음)
    area = p['area_mm2']

    codes = set()
    for s in slots:
        codes |= slot_conductor_codes(p, s)
    codes = sorted(codes)

    if per_conductor:
        Br, Bt = [], []
        for c in codes:
            m = p['reg'] == c
            if not m.any():
                continue
            w = area[m]
            Br.append(np.sum(w * br[m]) / np.sum(w))
            Bt.append(np.sum(w * bt[m]) / np.sum(w))
        Br = np.asarray(Br); Bt = np.asarray(Bt)
        S_r = float(np.sum(Br ** 2)); S_t = float(np.sum(Bt ** 2))
        n = len(Br)
        br_rms = float(np.sqrt(np.mean(Br ** 2)))
        bt_rms = float(np.sqrt(np.mean(Bt ** 2)))
    else:
        m = np.isin(p['reg'], codes)
        S_r = float(np.sum(area[m] * br[m] ** 2))
        S_t = float(np.sum(area[m] * bt[m] ** 2))
        n = int(m.sum())
        br_rms = float(np.sqrt(np.sum(area[m] * br[m] ** 2) / np.sum(area[m])))
        bt_rms = float(np.sqrt(np.sum(area[m] * bt[m] ** 2) / np.sum(area[m])))

    tot = S_r + S_t
    return {'f_theta': S_t / tot, 'f_r': S_r / tot,
            'S_theta': S_t, 'S_r': S_r, 'n_cond': n,
            'br_rms_T': br_rms, 'bt_rms_T': bt_rms,
            'per_conductor': per_conductor,
            'source': os.path.basename(path)}


def compare_over_speed(t_r_m: float, t_t_m: float, f_theta: float,
                       rpm: Optional[Sequence[float]] = None,
                       pole_pairs: int = POLE_PAIRS,
                       sigma: float = SIGMA_CU_20C, mu0: float = MU0) -> dict:
    """속도 스윕에 대해 방법 A vs B 를 비교한다.

    입력은 순동 치수(t_r=반경, t_t=접선), 접선 에너지 분율 f_theta.
    도체 기하가 모두 같다고 보면(같은 슬롯의 동일 바) 비율 R 은 커널비와
    에너지 분율만으로 결정된다:

        G_r(f) = (t_t/t_r) * eta_r * K(eta_r),  eta_r = t_r/delta   # B_theta
        G_t(f) = (t_r/t_t) * eta_t * K(eta_t),  eta_t = t_t/delta   # B_r
        P_A ∝ G_t * (S_theta + S_r)      # 단일 h_c=t_t 커널을 양쪽에
        P_B ∝ G_r * S_theta + G_t * S_r  # 성분별 커널
        R = P_A/P_B = G_t / (G_r*f_theta + G_t*f_r)

    (공통 상수 1/(sigma mu0^2), l_a, sum(B^2) 는 상쇄.) 반환 dict 의
    ``pct_diff`` = (R-1)*100 = 방법 A 가 B 대비 과대(+)/과소(-)평가율.
    """
    if rpm is None:
        rpm = np.arange(1000, 20001, 500, dtype=float)
    rpm = np.asarray(rpm, float)
    f_e = rpm / 60.0 * pole_pairs
    f_r_frac = 1.0 - f_theta

    G_r = np.array([kernel_factor(t_r_m, t_t_m, f, sigma, mu0) for f in f_e])
    G_t = np.array([kernel_factor(t_t_m, t_r_m, f, sigma, mu0) for f in f_e])
    delta = np.array([skin_depth(f, sigma, mu0) for f in f_e])
    eta_r = t_r_m / delta
    eta_t = t_t_m / delta

    P_A = G_t * 1.0                          # * S_tot (=1 정규화)
    P_B = G_r * f_theta + G_t * f_r_frac
    R = P_A / P_B
    pct = (R - 1.0) * 100.0

    return {'rpm': rpm, 'f_e_hz': f_e, 'delta_mm': delta * 1e3,
            'eta_r': eta_r, 'eta_t': eta_t, 'G_r': G_r, 'G_t': G_t,
            'R': R, 'pct_diff': pct, 'f_theta': f_theta,
            't_r_mm': t_r_m * 1e3, 't_t_mm': t_t_m * 1e3}


def _fmt_worstcase(res: dict) -> str:
    i = int(np.argmax(np.abs(res['pct_diff'])))
    return ("worst |A-B| at %.0f RPM (f_e=%.0f Hz): R=%.3f, %+.1f%%"
            % (res['rpm'][i], res['f_e_hz'][i], res['R'][i],
               res['pct_diff'][i]))
