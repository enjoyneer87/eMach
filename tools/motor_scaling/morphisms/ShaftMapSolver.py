# -*- coding: utf-8 -*-
"""축 토크 목표 효율맵 솔버 --- 격자 사전계산 + 등고선 교차 (2026-08-26).

MtpaFwSolver(점별 SLSQP)를 대체하는 벡터화 솔버다.  점별 최적화는 병렬로
빨라질 뿐 포락선 경계의 수렴 실패와 초기값 민감성이 남는다.  여기서는
(id, iq) 격자에 모든 양을 한 번에 계산해 두고, 토크 목표마다 각 id 행에서
T = T* 등고선을 지나는 iq 를 선형 교차로 찾은 뒤 교차점 비용의 행 방향
argmin 을 취한다.  달성 토크는 구성상 목표와 일치한다 --- 밴드+argmin
방식은 저손실 가장자리를 골라 격자 반폭(~12 Nm)의 계통 오프셋을 남겼다.

자속맵 입력은 원고의 30점 포화맵(6 Is x 5 gamma 극좌표, Fig 9/10 의
lab_scaling_comparison_e10.mat)이다.  구세대 e10_SatuMap.mat 의 48점 직교
격자가 아니다 --- §12.15 에서 저자가 잡았던 48 대 30 혼선을 코드가
되풀이하지 않기 위한 선택이다.

토크 규약 (LAB elecdata 로 실측 검증, 2026-08-26):
    T_shaft = T_em - T_drag,   T_drag*w = P_fe + P_mag + P_mech  (비 1.003)
    P_cu(DC/AC) 는 드래그가 아니라 전기 쪽 --- 효율 분모와 목적함수,
    그리고 등가 직렬저항으로 전압 제한에만 들어간다.

전압 모델은 MtpaFwSolver 의 EEC 를 따르되 결함 하나를 고쳤다 --- 종전
식은 저항 강하에 R_ac,eq 만 쓰고 R_dc 를 빠뜨렸다.  여기서는
R = R_dc + P_ac/(1.5 |i|^2) 를 쓴다.

단위 규약: dq 와 Is 는 peak, V_max 는 상전압 peak, 손실은 W.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict

import numpy as np
from scipy.interpolate import RegularGridInterpolator


def polar_flux_tables(is_pk, gamma_deg, psi_d, psi_q):
    """산포 30점 (Is, gamma) -> 정규 격자 보간자 두 개."""
    is_pk = np.asarray(is_pk, float).ravel()
    ga = np.asarray(gamma_deg, float).ravel()
    ia, gaa = np.unique(is_pk), np.unique(ga)
    D = np.full((ia.size, gaa.size), np.nan)
    Q = np.full_like(D, np.nan)
    for s, g, d, q in zip(is_pk, ga, np.ravel(psi_d), np.ravel(psi_q)):
        D[np.searchsorted(ia, s), np.searchsorted(gaa, g)] = d
        Q[np.searchsorted(ia, s), np.searchsorted(gaa, g)] = q
    assert not np.isnan(D).any(), "포화맵 격자에 구멍"
    fd = RegularGridInterpolator((ia, gaa), D, bounds_error=False,
                                 fill_value=None)
    fq = RegularGridInterpolator((ia, gaa), Q, bounds_error=False,
                                 fill_value=None)
    return fd, fq, float(ia.max())


@dataclass
class ShaftMapSolver:
    """축 토크 목표의 효율맵을 등고선 교차로 푼다.

    cu_ac(w_rpm, I_rms, beta_deg) -> W   : AC 동손 모델 (벡터화 필수)
    aux(w_rpm, T_shaft_Nm) -> dict       : {'fe','mag','mech'} [W].  같은
        토크 등고선 위에서 상수라 궤적 선택에는 영향이 없고, 드래그와
        효율에만 쓰인다
    """
    flux_d: Callable          # (Is_pk, gamma_deg) -> psi_d [Vs pk]
    flux_q: Callable
    r_dc: float               # 운전 온도 보정 후 [Ohm]
    pole_pairs: int
    v_max: float              # 상전압 peak [V]
    i_max_pk: float
    cu_ac: Callable
    aux: Callable
    n_grid: int = 481
    _g: Dict = field(default_factory=dict, repr=False)

    def _build(self):
        idv = np.linspace(-self.i_max_pk, 0.0, self.n_grid)
        iqv = np.linspace(0.0, self.i_max_pk, self.n_grid)
        ID, IQ = np.meshgrid(idv, iqv, indexing="ij")
        ISQ = ID ** 2 + IQ ** 2
        ISPK = np.sqrt(ISQ)
        BETA = np.degrees(np.arctan2(-ID, np.maximum(IQ, 1e-9)))
        q = np.column_stack([ISPK.ravel(), BETA.ravel()])
        PSD = np.asarray(self.flux_d(q), float).reshape(ID.shape)
        PSQ = np.asarray(self.flux_q(q), float).reshape(ID.shape)
        TEM = 1.5 * self.pole_pairs * (PSD * IQ - PSQ * ID)
        self._g.update(
            ID=ID, IQ=IQ, PSD=PSD, PSQ=PSQ, TEM=TEM, ISQ=ISQ,
            ok=ISQ <= self.i_max_pk ** 2,
            IRMS=ISPK / np.sqrt(2.0), BETA=BETA,
            PDC=1.5 * self.r_dc * ISQ)
        return self._g

    def _pac_column(self, w_rpm):
        """이 속도의 AC 동손을 (I,beta) 극좌표에서 평가해 셀로 옮긴다.

        손실은 (w, I, beta) 만의 함수라 극좌표 1.5 만 점 평가면 충분하고,
        셀마다 모델을 부르면 보간 호출이 격자 크기(23 만)만큼 나간다."""
        g = self._g or self._build()
        Iax = np.linspace(0.0, self.i_max_pk / np.sqrt(2.0), 160)
        Bax = np.linspace(0.0, 90.0, 91)
        II, BB = np.meshgrid(Iax, Bax, indexing="ij")
        P = np.asarray(self.cu_ac(np.full(II.size, w_rpm), II.ravel(),
                                  BB.ravel()), float).reshape(II.shape)
        itp = RegularGridInterpolator((Iax, Bax), P, bounds_error=False,
                                      fill_value=None)
        return itp(np.column_stack([g["IRMS"].ravel(),
                                    g["BETA"].ravel()])).reshape(
            g["IRMS"].shape)

    def solve(self, speeds_rpm, t_shaft_targets):
        """targets 가 2-D (n_t, n_s) 면 열마다 다른 목표(LAB 격자 재현)."""
        g = self._g or self._build()
        speeds_rpm = np.asarray(speeds_rpm, float)
        tt = np.asarray(t_shaft_targets, float)
        if tt.ndim == 1:
            tt = np.repeat(tt[:, None], speeds_rpm.size, 1)
        n_t, n_s = tt.shape
        out = {k: np.full((n_t, n_s), np.nan) for k in
               ("id", "iq", "eta", "t_shaft", "p_cu_ac", "p_cu_dc",
                "p_fe", "p_mag", "p_mech", "v_pk")}
        rows = np.arange(self.n_grid)

        for j, w in enumerate(speeds_rpm):
            if w <= 0:
                continue
            we = w * np.pi / 30.0 * self.pole_pairs
            wm = w * np.pi / 30.0
            PAC = self._pac_column(w)
            RT = self.r_dc + PAC / np.maximum(1.5 * g["ISQ"], 1e-9)
            VD = RT * g["ID"] - we * g["PSQ"]
            VQ = RT * g["IQ"] + we * g["PSD"]
            feas = g["ok"] & (VD ** 2 + VQ ** 2 <= self.v_max ** 2)
            if not feas.any():
                continue
            cost = g["PDC"] + PAC

            for i in range(n_t):
                ts = tt[i, j]
                if not np.isfinite(ts) or ts <= 0:
                    continue
                a = self.aux(w, ts)
                p_aux = a["fe"] + a["mag"] + a["mech"]
                t_em = ts + p_aux / wm

                # 행별 첫 교차: TEM[i,:] 가 t_em 을 처음 넘는 열.  행 방향
                # (고정 id, iq 증가)으로 T 는 단조 증가가 사실상 보장된다.
                above = g["TEM"] >= t_em
                has = above.any(axis=1)
                j0 = np.argmax(above, axis=1)
                valid = has & (j0 > 0)
                if not valid.any():
                    continue
                r = rows[valid]
                jr = j0[valid]
                t1 = g["TEM"][r, jr - 1]
                t2 = g["TEM"][r, jr]
                f = np.clip((t_em - t1) / np.maximum(t2 - t1, 1e-9), 0, 1)
                okc = feas[r, jr - 1] & feas[r, jr]

                def lerp(A):
                    return (1 - f) * A[r, jr - 1] + f * A[r, jr]
                c = np.where(okc, lerp(cost), np.inf)
                if not np.isfinite(c).any():
                    continue
                kk = int(np.argmin(c))
                p_ac = float(lerp(PAC)[kk])
                p_dc = float(lerp(g["PDC"])[kk])
                p_sh = ts * wm
                out["id"][i, j] = g["ID"][r[kk], 0]
                out["iq"][i, j] = float(lerp(g["IQ"])[kk])
                out["t_shaft"][i, j] = ts
                out["p_cu_ac"][i, j], out["p_cu_dc"][i, j] = p_ac, p_dc
                out["p_fe"][i, j], out["p_mag"][i, j] = a["fe"], a["mag"]
                out["p_mech"][i, j] = a["mech"]
                out["v_pk"][i, j] = float(np.hypot(lerp(VD), lerp(VQ))[kk])
                out["eta"][i, j] = p_sh / (p_sh + p_dc + p_ac + p_aux)
        return out
