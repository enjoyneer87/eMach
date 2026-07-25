# -*- coding: utf-8 -*-
"""응답 주파수(전기 차수)별 손실 분해와 차수별 AF — 스칼라 AF의 차수 구조 검증.

동기 (저자 질문): AF = P_TS/P_HYB 는 총량 비지만, TS-FEA 의 Je(t) 파형이
export 되어 있으므로 손실을 응답 주파수별로 분해할 수 있다 (손실은 J 의
제곱량이라 주기 평균에서 교차 주파수 항이 소거 --- Parseval). 그러면
"AF 를 차수별로 정의할 필요가 있는가"를 데이터로 답할 수 있다.

방법 (슬롯 1 도체 6개, 근접(유도) 성분만 --- Je 는 순전류 제외 유도 성분):
  TS 측:  요소별 Je(t) 를 전기 차수 n 의 조화 LSQ 로 적합
          P_n^TS = sum_e A_e |J_n,e|^2 / (2 sigma)          [W/m]
  HYB 측: MS export 의 도체별 면적가중 평균 B(t) 를 같은 방법으로 적합
          P_n^HYB = sum_c g(eta_n) |B_n,c|^2                [W/m]
          g(eta) = w_c/(h_c sigma mu0^2) * eta K(eta)  (본문 eq g_kernel,
          단일 g 를 |B|^2 에 적용 --- 생산 하이브리드와 동일 관습)
  차수별 AF_n = P_n^TS / P_n^HYB.

주의:
  - 블록 1 은 Je=0 (초기조건 아티팩트) --- |Je|_max 로 감지해 제외.
    LSQ 조화 적합은 결측 샘플을 자연스럽게 처리한다 (FFT 대신 LSQ 인 이유).
  - n=0 (DC) 은 g 가 0 이라 AF_n 정의 불가 --- share 로만 보고.
  - 절대 스케일: 슬롯 1 근접 성분만의 대리이므로 총 AF(=FullFEA/Hybrid,
    표피 포함·전슬롯)와 수치가 같을 필요는 없고 같은 자릿수면 정합.

실행:  python run_ts_harmonic_af.py            (Ref/SC x 16k/8k 전 케이스)
산출:  map_exports/e10/fields/ts_harmonic_af.json
"""
from __future__ import annotations

import json
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
OUT = os.path.join(F, "ts_harmonic_af.json")
SLOT = 1
SIGMA = 4.709e7
MU0 = 4e-7 * np.pi
POLE_PAIRS = 4                       # e10: 8극 --- 전기각 = 4 x 기계각
NH = 24                              # 적합 최대 전기 차수

# model -> (TS, HY, f_e[Hz], w_c[mm], h_c[mm])
CASES = {
    "Ref_16k": ("Magnetic_Ref_ARCHIVE_460A_36deg_OnLoadTorque.txt",
                "Magnetic_Ref_Hybrid_ARCHIVE_460A_36deg_full_OnLoadTorque.txt",
                1066.67, 3.711, 1.686),
    "Ref_8k":  ("Magnetic_Ref_OP460A_36deg_8k_OnLoadTorque.txt",
                "Magnetic_Ref_Hybrid_OP460A_36deg_8k_OnLoadTorque.txt",
                533.33, 3.711, 1.686),
    "SC_16k":  ("Magnetic_SC_OP920A_36deg_OnLoadTorque.txt",
                "Magnetic_SC_Hybrid_OP920A_36deg_OnLoadTorque.txt",
                1066.67, 7.422, 3.372),
    "SC_8k":   ("Magnetic_SC_OP920A_36deg_8k_OnLoadTorque.txt",
                "Magnetic_SC_Hybrid_OP920A_36deg_8k_OnLoadTorque.txt",
                533.33, 7.422, 3.372),
}


def harm_fit(theta_e: np.ndarray, Y: np.ndarray, nh: int):
    """조화 LSQ: Y (nt, m) -> (a0 (m,), C (nh, m) 복소 피크 진폭)."""
    cols = [np.ones_like(theta_e)]
    for n in range(1, nh + 1):
        cols += [np.cos(n * theta_e), np.sin(n * theta_e)]
    A = np.column_stack(cols)                       # (nt, 1+2nh)
    coef, *_ = np.linalg.lstsq(A, Y, rcond=None)
    a0 = coef[0]
    C = coef[1::2] + 1j * coef[2::2]                # (nh, m)
    return a0, C


def g_kernel(eta: np.ndarray, w_c_m: float, h_c_m: float) -> np.ndarray:
    """본문 eq (g_kernel): g = w/(h sigma mu0^2) * eta K(eta)  [W/m/T^2]."""
    K = (np.sinh(eta) - np.sin(eta)) / (np.cosh(eta) + np.cos(eta))
    return w_c_m / (h_c_m * SIGMA * MU0 ** 2) * eta * K


def load_series(path: str, want_je: bool):
    """블록 순회 --- 슬롯 도체 요소의 Je(t) 또는 도체별 평균 B(t) 시계열.

    반환: theta_mech_deg (nt,), 그리고
      want_je : JE (nt, n_elem), area_mm2 (n_elem,)
      else    : BX, BY (nt, 6)  (도체 6개, 반경순)
    """
    # 주의: p['rotate_deg'] 는 누적 각도가 아니라 블록당 "Rotate Step"
    # (상수 증분)이다 --- 누적 각도는 (블록번호-1) x |step| 으로 재구성한다.
    thetas, rows = [], []
    codes = mask = None
    area = None
    cond_masks = None
    step_deg = None
    for bi, p in iter_mes_blocks(path):
        if codes is None:
            codes = sorted(slot_conductor_codes(p, SLOT),
                           key=lambda c: np.hypot(
                               p['x_mm'][p['reg'] == c],
                               p['y_mm'][p['reg'] == c]).mean())
            mask = np.isin(p['reg'], codes)
            area = p['area_mm2'][mask]
            cond_masks = [(p['reg'][mask] == c) for c in codes]
            n_ref = len(p['reg'])
        assert len(p['reg']) == n_ref, f"블록 {bi} 메시 불일치"
        if step_deg is None and p['rotate_deg']:
            step_deg = abs(p['rotate_deg'])
        if want_je:
            je = p['je_am2'][mask]
            if np.abs(je).max() < 1.0:              # 블록1 Je=0 아티팩트
                continue
            rows.append(je)
        else:
            w = p['area_mm2'][mask]
            bx, by = p['bx'][mask], p['by'][mask]
            rows.append([
                (np.sum(w[m] * bx[m]) / np.sum(w[m]),
                 np.sum(w[m] * by[m]) / np.sum(w[m])) for m in cond_masks])
        thetas.append(bi - 1)                        # 블록 인덱스(0-기점)
    assert step_deg, f"Rotate Step 미검출: {path}"
    theta = np.asarray(thetas, float) * step_deg
    if want_je:
        return theta, np.asarray(rows), area
    B = np.asarray(rows)                             # (nt, 6, 2)
    return theta, B[:, :, 0], B[:, :, 1]


def run_case(tag, ts_fn, hy_fn, f_e, w_c_mm, h_c_mm):
    ts_path, hy_path = os.path.join(F, ts_fn), os.path.join(F, hy_fn)
    for pth in (ts_path, hy_path):
        if not os.path.exists(pth):
            print(f"[{tag}] 파일 없음: {os.path.basename(pth)} --- 건너뜀")
            return None

    # --- TS: 요소별 Je 조화 분해 -> 차수별 손실 [W/m]
    th, JE, area = load_series(ts_path, want_je=True)
    theta_e = np.deg2rad(th) * POLE_PAIRS
    span = (theta_e.max() - theta_e.min()) / (2 * np.pi)
    _, C = harm_fit(theta_e, JE, NH)                 # (NH, n_elem)
    a_m2 = area * 1e-6
    p_ts = np.array([np.sum(a_m2 * np.abs(C[n - 1]) ** 2) / (2 * SIGMA)
                     for n in range(1, NH + 1)])

    # --- HYB: 도체 평균 B 조화 분해 -> g(eta_n) |B_n|^2 [W/m]
    th_h, BX, BY = load_series(hy_path, want_je=False)
    theta_eh = np.deg2rad(th_h) * POLE_PAIRS
    _, CX = harm_fit(theta_eh, BX, NH)
    _, CY = harm_fit(theta_eh, BY, NH)
    ns = np.arange(1, NH + 1)
    delta = 1.0 / np.sqrt(np.pi * ns * f_e * MU0 * SIGMA)
    eta = (h_c_mm * 1e-3) / delta
    g = g_kernel(eta, w_c_mm * 1e-3, h_c_mm * 1e-3)
    B2 = np.abs(CX) ** 2 + np.abs(CY) ** 2           # (NH, 6) 피크^2
    p_hy = g * B2.sum(axis=1)

    af_n = np.where(p_hy > 0, p_ts / np.maximum(p_hy, 1e-30), np.nan)
    tot_ts, tot_hy = p_ts.sum(), p_hy.sum()

    print(f"\n[{tag}]  TS블록 {len(th)} (span {span:.3f}주기)"
          f"  HY블록 {len(th_h)}  f_e={f_e:g}Hz")
    print(f"{'n':>3} {'eta_n':>6} {'P_TS[W/m]':>11} {'P_HY[W/m]':>11}"
          f" {'shareTS%':>9} {'shareHY%':>9} {'AF_n':>7}")
    for i, n in enumerate(ns):
        if p_ts[i] / tot_ts < 0.002 and p_hy[i] / tot_hy < 0.002:
            continue
        # HY 성분이 사실상 0인 차수는 AF_n 비 자체가 무의미 (0/0 폭주)
        af_s = (f"{af_n[i]:>7.3f}" if p_hy[i] / tot_hy > 1e-3
                else f"{'---':>7}")
        print(f"{n:>3} {eta[i]:>6.2f} {p_ts[i]:>11.4g} {p_hy[i]:>11.4g}"
              f" {100 * p_ts[i] / tot_ts:>9.2f} {100 * p_hy[i] / tot_hy:>9.2f}"
              f" {af_s}")
    print(f"    합계: TS {tot_ts:.4g}  HY {tot_hy:.4g}"
          f"  총비(근접 대리) {tot_ts / tot_hy:.3f}")

    return {
        "n": ns.tolist(), "eta_n": eta.tolist(),
        "p_ts_Wpm": p_ts.tolist(), "p_hy_Wpm": p_hy.tolist(),
        "af_n": af_n.tolist(),
        "total_ratio": float(tot_ts / tot_hy),
        "n_blocks_ts": int(len(th)), "n_blocks_hy": int(len(th_h)),
        "span_periods_ts": float(span),
    }


def main() -> int:
    res = {}
    for tag, (ts_fn, hy_fn, f_e, w_c, h_c) in CASES.items():
        r = run_case(tag, ts_fn, hy_fn, f_e, w_c, h_c)
        if r is not None:
            res[tag] = r
    if not res:
        print("실행된 케이스 없음")
        return 1
    res["_meta"] = {
        "slot": SLOT, "sigma": SIGMA, "pole_pairs": POLE_PAIRS, "nh": NH,
        "note": "P_n = Parseval 응답주파수 분해, 슬롯1 근접(유도) 성분 대리. "
                "HYB 는 단일 g(eta_n)|B_n|^2 (생산 하이브리드 관습).",
    }
    json.dump(res, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
