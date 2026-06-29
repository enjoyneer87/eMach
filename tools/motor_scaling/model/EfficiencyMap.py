from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class EfficiencyMap:
    speeds_rpm: np.ndarray      # 1D array of speeds [rpm]
    torques_ref: np.ndarray     # 1D array of reference torques [Nm]
    speed_grid: np.ndarray      # 2D grid of speeds [rpm]
    torque_grid: np.ndarray     # 2D grid of torques [Nm]
    id_opt: np.ndarray          # 2D grid of optimal d-axis currents [A]
    iq_opt: np.ndarray          # 2D grid of optimal q-axis currents [A]
    voltage: np.ndarray         # 2D grid of phase voltage peak [V]
    loss_total: np.ndarray      # 2D grid of total loss [kW]
    loss_cu_dc: np.ndarray      # 2D grid of DC copper loss [kW]
    loss_cu_ac: np.ndarray      # 2D grid of AC copper loss [kW]
    loss_fe: np.ndarray         # 2D grid of iron loss [kW]
    efficiency: np.ndarray      # 2D grid of efficiency [%]
    success_mask: np.ndarray    # 2D mask of solver success status
    k_r: float
    k_a: float

    @property
    def phase_deg(self) -> np.ndarray:
        """최적 전류위상각 β_opt [deg], shape=(n_torque, n_speed).

        Motor-CAD gamma 규약: β = arctan2(iq_opt, id_opt)*180/π − 90.
        solver 수렴 실패 포인트(success_mask=False)는 NaN으로 반환.
        """
        beta = np.arctan2(self.iq_opt, self.id_opt) * 180.0 / np.pi - 90.0
        beta = np.where(self.success_mask, beta, np.nan)
        return beta

    @property
    def i_amp(self) -> np.ndarray:
        """전류 진폭 |I| [A_pk], shape=(n_torque, n_speed).

        solver 수렴 실패 포인트는 NaN으로 반환.
        """
        amp = np.sqrt(self.id_opt**2 + self.iq_opt**2)
        return np.where(self.success_mask, amp, np.nan)
