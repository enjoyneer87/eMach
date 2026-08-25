# -*- coding: utf-8 -*-
"""Motor-CAD LAB elecdata .mat 어댑터 (2026-08-26).

ShaftMapSolver 가 LAB 에서 빌리는 것들을 한곳에 모은다 --- 운전 격자와
비-AC 손실 북키핑이다.  단위·방향 규약은 2026-08-25/26 실측으로 굳혔다.

  - 격자는 (속도 33행, 토크 151열).  전력 필드는 kW, 손실 필드는 W
  - Efficiency 는 % 로 저장된 판본이 있다 (최대값으로 판별)
  - Id/Iq_RMS 는 크기 저장 --- id 부호는 평균으로 판별해 되살린다
  - 드래그: T_em - T_shaft 가 (P_fe+P_mag+P_mech)/w 와 비 1.003 으로 일치
  - 권선 저항: 스케일 법칙은 활성부만 따르므로 (end-winding 비 1.29,
    원고 §5.2) 효율 북키핑용 R 은 CuDC/(3 I^2) 실측 중앙값을 쓴다
"""
import numpy as np
from scipy.io import loadmat
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator


class LabElecdata:
    """FullFEA/Hybrid LAB 빌드 하나를 감싼다."""

    def __init__(self, mat_path):
        self.F = loadmat(mat_path)

    def g(self, key):
        return np.asarray(self.F[key], float)

    # ── 격자 (솔버 방향: 속도 = 열) ──────────────────────────────────
    @property
    def speeds_rpm(self):
        return self.g("Speed")[:, 0]

    @property
    def shaft_torque(self):
        """(토크 151, 속도 33) --- 솔버의 targets 형상."""
        return self.g("Shaft_Torque").T

    @property
    def efficiency(self):
        e = self.g("Efficiency").T
        return e / 100.0 if np.nanmax(e) > 1.5 else e

    def idq_pk(self):
        """peak dq (부호 복원).  검증 대조용."""
        idr, iqr = self.g("Id_RMS"), self.g("Iq_RMS")
        sign = -1.0 if np.nanmean(idr) > 0 else 1.0
        return idr.T * sign * np.sqrt(2.0), iqr.T * np.sqrt(2.0)

    # ── 북키핑 ───────────────────────────────────────────────────────
    def r_dc_measured(self, i_min=100.0):
        Ir = np.hypot(self.g("Id_RMS"), self.g("Iq_RMS"))
        dc = self.g("Stator_Copper_Loss_DC")
        m = (Ir > i_min) & np.isfinite(dc)
        return float(np.median(dc[m] / (3.0 * Ir[m] ** 2)))

    def aux_tables(self):
        """(속도, 축토크) -> {'fe','mag','mech'} [W] 보간자."""
        sp, ts = self.g("Speed"), self.g("Shaft_Torque")
        m = (sp > 0) & np.isfinite(ts) & (ts > 0)
        pts = np.column_stack([sp[m], ts[m]])
        chans = {}
        for key, name in (("fe", "Iron_Loss"), ("mag", "Magnet_Loss"),
                          ("mech", "Mechanical_Loss")):
            v = self.g(name)[m]
            chans[key] = (LinearNDInterpolator(pts, v),
                          NearestNDInterpolator(pts, v))

        def aux(w, t):
            out = {}
            for key, (lin, nn) in chans.items():
                x = lin(w, t)
                out[key] = float(nn(w, t) if np.isnan(x) else x)
            return out
        return aux
