# -*- coding: utf-8 -*-
"""회로 수준 검증 — 요소 전류밀도를 도체 단면으로 합산해 도체 전류 파형 복원.

저자 제안: 요소별 밀도 파형 말고 상(회로) 기준 전류 파형도 확인 가능하지
않은가. 결선 정보 없이도 각 도체의 I_c(t) = sum_e J_e^total A_e 를 만들면
파형의 위상으로 상 그룹이 드러나고, RMS 가 알려진 상전류(460/920 A)와
일치하는지로 export·파싱의 회로 정합을 검증한다.

또한 도체별 유도(와전류) 손실 파형 P_c(t) = sum_e Je^2 A_e / sigma 의
주기 평균도 도체(층)별로 보고한다 --- Motor-CAD 상별 손실 그래프의
export 판 대응물.

실행:  python check_conductor_currents.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from jeet_acloss_rbf.field_metrics import (                 # noqa: E402
    iter_mes_blocks, slot_conductor_codes)

F = os.path.join(HERE, "map_exports", "e10", "fields")
SLOT = 1
SIGMA = 4.709e7
POLE_PAIRS = 4

CASES = {
    "Ref_16k": ("Magnetic_Ref_ARCHIVE_460A_36deg_OnLoadTorque.txt", 460.0),
    "SC_16k":  ("Magnetic_SC_OP920A_36deg_OnLoadTorque.txt", 920.0),
}


def main() -> int:
    for tag, (fn, i_rms_exp) in CASES.items():
        path = os.path.join(F, fn)
        if not os.path.exists(path):
            print(f"[{tag}] 파일 없음 --- 건너뜀")
            continue
        codes = None
        idx, I, PL = [], [], []                    # 블록, I_c(t), P_c(t)
        step_deg = None
        for bi, p in iter_mes_blocks(path):
            if codes is None:
                codes = sorted(slot_conductor_codes(p, SLOT),
                               key=lambda c: np.hypot(
                                   p['x_mm'][p['reg'] == c],
                                   p['y_mm'][p['reg'] == c]).mean())
                masks = [(p['reg'] == c) for c in codes]
                areas = [p['area_mm2'][m] * 1e-6 for m in masks]
            if step_deg is None and p['rotate_deg']:
                step_deg = abs(p['rotate_deg'])
            I.append([float(np.sum(p['j_am2'][m] * a))
                      for m, a in zip(masks, areas)])
            PL.append([float(np.sum(p['je_am2'][m] ** 2 * a) / SIGMA)
                       for m, a in zip(masks, areas)])
            idx.append(bi - 1)
        I = np.asarray(I)                          # (nt, 6)
        PL = np.asarray(PL)
        th_e = np.deg2rad(np.asarray(idx, float) * step_deg) * POLE_PAIRS

        # 기본파 위상·진폭 (LSQ), 전 고조파 RMS
        A = np.column_stack([np.ones_like(th_e), np.cos(th_e), np.sin(th_e)])
        coef, *_ = np.linalg.lstsq(A, I, rcond=None)
        amp1 = np.hypot(coef[1], coef[2])
        ph1 = np.rad2deg(np.arctan2(-coef[2], coef[1]))
        rms = np.sqrt((I ** 2).mean(axis=0))
        thd = np.sqrt(np.maximum(rms ** 2 - amp1 ** 2 / 2, 0)) / (amp1 / np.sqrt(2))

        print(f"\n[{tag}]  기대 상전류 {i_rms_exp:g} A_rms  (도체 = 층 순서:"
              f" 공극측 -> 슬롯바닥)")
        print(f"{'층':>3} {'I_rms[A]':>9} {'기본파[A_rms]':>12} {'위상[deg]':>10}"
              f" {'왜곡율%':>8} {'P_eddy_avg[W/m]':>15}")
        for L in range(I.shape[1]):
            print(f"{L + 1:>3} {rms[L]:>9.1f} {amp1[L] / np.sqrt(2):>12.1f}"
                  f" {ph1[L]:>10.1f} {100 * thd[L]:>8.2f}"
                  f" {PL[:, L].mean():>15.1f}")
        print(f"  합(슬롯1 유도손실): {PL.sum(axis=1).mean():.1f} W/m"
              f"   상전류 대비 편차: "
              f"{100 * (rms.mean() / i_rms_exp - 1):+.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
