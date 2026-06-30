import numpy as np
from scipy.optimize import minimize
from scipy.interpolate import RegularGridInterpolator
from ..model.ScaledMotorMap import ScaledMotorMap
from ..model.RbfModelParams import RbfModelParams
from .AcLossCorrector import correct_ac_loss

# ---------------------------------------------------------------------------
# 등가회로 모델 비교 (Motor-CAD LAB 기준)
#
# [Mechanical 모델]  Motor-CAD "Iron Loss NOT in Voltage Vector"
#   V = R_dc * Im + j*w*Psi
#   철손/AC손은 손실 합산에만 반영. 전압 제약 낙관적 → FW 오차 발생.
#   (수정 전 방식)
#
# [Electrical EEC 모델]  Motor-CAD "Iron Loss IN Voltage Vector"
#   철손  -> 역기전력 병렬 등가전류  I_fe = (2/3)*P_fe / conj(V_ind)
#   AC손  -> 등가 직렬 저항          R_ac = P_ac / (1.5 * Im^2)
#   V = R_ac * (Im + I_fe) + j*w*Psi
#   전압 제약 보수적(정확) → FW 경계·역률 물리적으로 일치.
#   (SyRE MMM calcTnPoint, 수정 후 방식)
# ---------------------------------------------------------------------------


def _eec_terminal_voltage_sq(
    id_val, iq_val,
    psi_d, psi_q,
    p_fe_kw, p_ac_kw,
    r_dc, omega_e
):
    """Electrical EEC 모델 단자전압 |V|^2, V_d, V_q 반환.

    Parameters
    ----------
    p_fe_kw : float or ndarray  [kW]  철손
    p_ac_kw : float or ndarray  [kW]  RBF 보정 AC 구리손
    r_dc    : float  [Ohm]  DC 저항
    omega_e : float  [rad/s]  전기 각속도

    Returns
    -------
    v_sq : |V_terminal|^2  [V^2]
    v_d  : d축 단자전압 [V]
    v_q  : q축 단자전압 [V]
    """
    # 역기전력 V_ind = j*omega_e * Psi (dq 성분)
    v_d_ind = -omega_e * psi_q
    v_q_ind = omega_e * psi_d
    v_ind_sq = v_d_ind**2 + v_q_ind**2

    # AC 구리손 → 등가 직렬 저항: R_ac = P_ac / (1.5 * Im^2)
    i_sq = id_val**2 + iq_val**2
    is_scalar = np.ndim(i_sq) == 0
    if is_scalar:
        r_ac = (p_ac_kw * 1000.0 / (1.5 * i_sq)) if i_sq > 1e-9 else r_dc
    else:
        r_ac = np.where(
            i_sq > 1e-9,
            p_ac_kw * 1000.0 / np.maximum(1.5 * i_sq, 1e-12),
            r_dc,
        )

    # 철손 → 병렬 등가전류 (V_ind 동위상)
    # I_fe = (2/3)*P_fe / conj(V_ind)
    # 성분: I_fe_d = (2/3)*P_fe*V_d_ind / |V_ind|^2
    p_fe_w = p_fe_kw * 1000.0
    if is_scalar:
        if v_ind_sq > 1e-9:
            ife_d = (2.0 / 3.0) * p_fe_w * v_d_ind / v_ind_sq
            ife_q = (2.0 / 3.0) * p_fe_w * v_q_ind / v_ind_sq
        else:
            ife_d = ife_q = 0.0
    else:
        safe_v = np.maximum(v_ind_sq, 1e-12)
        ife_d = np.where(
            v_ind_sq > 1e-9,
            (2.0 / 3.0) * p_fe_w * v_d_ind / safe_v,
            0.0,
        )
        ife_q = np.where(
            v_ind_sq > 1e-9,
            (2.0 / 3.0) * p_fe_w * v_q_ind / safe_v,
            0.0,
        )

    # 단자 전압: V = R_ac * (Im + I_fe) + V_ind
    v_d = r_ac * (id_val + ife_d) + v_d_ind
    v_q = r_ac * (iq_val + ife_q) + v_q_ind
    return v_d**2 + v_q**2, v_d, v_q


class MtpaFwSolver:
    """MTPA/FW 최적 전류 솔버 (Electrical EEC 전압 모델)."""

    @staticmethod
    def solve(
        torque_ref: float,
        speed_rpm: float,
        map_data: ScaledMotorMap,
        rbf_model: RbfModelParams,
        v_max: float,
        i_max: float,
        r_ac_factor: float = 1.0,
    ) -> dict:
        """총 손실 최소화로 최적 (id, iq) 산출.

        전압 제약은 Electrical EEC 모델 적용:
          - 철손 병렬 등가전류 I_fe 가 Rs 전압강하에 기여
          - AC 구리손 등가 직렬 저항 R_ac 사용
        Motor-CAD LAB "Iron Loss in Voltage Vector" 옵션과 동일.

        Args:
            torque_ref  : 목표 토크 [Nm]
            speed_rpm   : 회전속도 [rpm]
            map_data    : ScaledMotorMap
            rbf_model   : RBF AC 구리손 보정 모델
            v_max       : 최대 상전압 피크 [V_pk]  (예: Vdc/sqrt(3))
            i_max       : 최대 상전류 피크 [A_pk]  (예: Irms*sqrt(2))
            r_ac_factor : AC 손실 보정 배율 (기본 1.0)

        Returns:
            id_opt, iq_opt  : 최적 전류 [A]
            torque          : 달성 토크 [Nm]
            voltage         : 단자전압 크기 [V_pk]  (EEC 모델)
            loss_total      : 총 손실 [kW]
            loss_cu_dc      : DC 구리손 [kW]
            loss_cu_ac      : AC 구리손 [kW]
            loss_fe         : 철손 [kW]
            success         : 수렴 여부
        """
        pole_pairs = map_data.pole_pairs
        omega_e = (speed_rpm * 2 * np.pi / 60.0) * pole_pairs

        # 1. 보간 함수 준비
        id_1d = np.unique(map_data.id_grid)
        iq_1d = np.unique(map_data.iq_grid)
        is_xy = (map_data.id_grid[0, 0] != map_data.id_grid[0, 1])

        def make_interp(grid_values):
            vals = grid_values.T if is_xy else grid_values
            return RegularGridInterpolator(
                (id_1d, iq_1d), vals,
                bounds_error=False, fill_value=None,
            )

        interp_ld = make_interp(map_data.lambda_d)
        interp_lq = make_interp(map_data.lambda_q)
        interp_fe = make_interp(map_data.p_fe_grid)
        p_ac_grid = correct_ac_loss(map_data, rbf_model, speed_rpm)
        interp_ac = make_interp(p_ac_grid)

        # 2. 초기값 탐색 (coarse grid, EEC 전압 필터)
        n_coarse = 60
        id_c = np.linspace(-i_max, 0.0, n_coarse)
        iq_c = np.linspace(0.0, i_max, n_coarse)
        id_m, iq_m = np.meshgrid(id_c, iq_c)
        mask_circle = (id_m**2 + iq_m**2) <= i_max**2
        pts = np.vstack((id_m[mask_circle], iq_m[mask_circle])).T

        ld_pts = interp_ld(pts)
        lq_pts = interp_lq(pts)
        p_fe_pts = interp_fe(pts)
        p_ac_pts = interp_ac(pts) * r_ac_factor
        torque_pts = 1.5 * pole_pairs * (
            ld_pts * pts[:, 1] - lq_pts * pts[:, 0]
        )
        v_sq_pts, _, _ = _eec_terminal_voltage_sq(
            pts[:, 0], pts[:, 1], ld_pts, lq_pts,
            p_fe_pts, p_ac_pts, map_data.r_dc, omega_e,
        )

        valid_mask = v_sq_pts <= v_max**2
        if not np.any(valid_mask):
            valid_mask = np.ones(len(pts), dtype=bool)
        pts_valid = pts[valid_mask]
        torque_valid = torque_pts[valid_mask]
        best_idx = np.argmin(np.abs(torque_valid - torque_ref))
        initial_guess = pts_valid[best_idx]

        # 3. SLSQP 최적화
        def loss_objective(dq):
            i_sq = dq[0]**2 + dq[1]**2
            p_dc = 1.5 * map_data.r_dc * i_sq / 1000.0
            p_fe = float(interp_fe(dq))
            p_ac = float(interp_ac(dq)) * r_ac_factor
            return p_dc + p_fe + p_ac

        def con_current(dq):
            return i_max**2 - (dq[0]**2 + dq[1]**2)

        def con_voltage(dq):
            id_val, iq_val = dq
            psi_d = float(interp_ld(dq))
            psi_q = float(interp_lq(dq))
            p_fe = float(interp_fe(dq))
            p_ac = float(interp_ac(dq)) * r_ac_factor
            v_sq, _, _ = _eec_terminal_voltage_sq(
                id_val, iq_val, psi_d, psi_q,
                p_fe, p_ac, map_data.r_dc, omega_e,
            )
            return v_max**2 - v_sq

        def con_torque(dq):
            id_val, iq_val = dq
            psi_d = float(interp_ld(dq))
            psi_q = float(interp_lq(dq))
            t_calc = 1.5 * pole_pairs * (
                psi_d * iq_val - psi_q * id_val
            )
            return t_calc - torque_ref

        cons = [
            {'type': 'ineq', 'fun': con_current},
            {'type': 'ineq', 'fun': con_voltage},
            {'type': 'eq',   'fun': con_torque},
        ]
        bounds = (
            [(-i_max, 0.0), (0.0, i_max)]
            if torque_ref >= 0
            else [(-i_max, 0.0), (-i_max, 0.0)]
        )

        res = minimize(
            loss_objective, initial_guess,
            method='SLSQP', bounds=bounds, constraints=cons,
            options={'ftol': 1e-6, 'maxiter': 100, 'disp': False},
        )
        id_opt, iq_opt = res.x

        # 4. 최적점 출력값
        psi_d_opt = float(interp_ld(res.x))
        psi_q_opt = float(interp_lq(res.x))
        p_fe_opt = float(interp_fe(res.x))
        p_ac_opt = float(interp_ac(res.x)) * r_ac_factor
        p_dc_opt = 1.5 * map_data.r_dc * (id_opt**2 + iq_opt**2) / 1000.0
        t_opt = 1.5 * pole_pairs * (
            psi_d_opt * iq_opt - psi_q_opt * id_opt
        )
        v_sq_opt, _, _ = _eec_terminal_voltage_sq(
            id_opt, iq_opt, psi_d_opt, psi_q_opt,
            p_fe_opt, p_ac_opt, map_data.r_dc, omega_e,
        )

        v_ok = v_sq_opt <= v_max**2 * (1.0 + 1e-4)

        return {
            'id_opt':     float(id_opt),
            'iq_opt':     float(iq_opt),
            'torque':     float(t_opt),
            'voltage':    float(np.sqrt(v_sq_opt)),
            'loss_total': float(p_dc_opt + p_fe_opt + p_ac_opt),
            'loss_cu_dc': float(p_dc_opt),
            'loss_cu_ac': float(p_ac_opt),
            'loss_fe':    float(p_fe_opt),
            'success':    bool(res.success) and v_ok,
        }
