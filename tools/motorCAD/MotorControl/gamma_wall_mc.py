# -*- coding: utf-8 -*-
"""0단계 — 각도 오차 몬테카를로로 "실무의 진각 상한"을 재현한다 (Simulink 없이).

이미 뽑아 둔 Lab 격자 T(I, γ), V(I, γ) 위에서 지령 진각 γ_cmd 에 오차를 뿌리고
  · 토크 평균·표준편차
  · 토크 부호가 뒤집힐 확률(제동으로 넘어감)
  · 상전압 한계를 넘길 확률(전류 제어 상실)
를 센다. 오차원은 레졸버 오프셋(균일 ±a), 지연 보상 잔차(정규 σ), 자석 온도에 따른
λm 드리프트(플럭스 스케일 → 같은 전류에서 토크·전압이 함께 움직임)로 본다.

  python gamma_wall_mc.py --current 135 --out NEW.csv [--speed 16000] [--n 20000]
"""
import argparse
import csv
import io
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
from scipy.interpolate import RegularGridInterpolator

W = r"D:\KangDH\Thesis\e10\work_lab_pc1\existing"
# Historical final correction (session record 1433): 285.1 V phase RMS.
# Rounded 720*0.97/sqrt(3)/sqrt(2), not the earlier mistaken 415.7 V RMS.
# Voltage exceedance is a sampled threshold event, not a closed-loop stability test.
# Flux drift scales torque and voltage together; this is a rough surrogate.
VLIM = 285.1


def load(speed, source_dir=W):
    path = source_dir + r"\gammagrid_ref_hyb_fine%d.json" % speed
    rows = json.load(io.open(path, encoding="utf-8"))["rows"]
    Is = np.array(sorted({r["demand_current_rms"] for r in rows}))
    gs = np.array(sorted({r["demand_phase"] for r in rows}))
    T = np.full((len(Is), len(gs)), np.nan)
    V = np.full((len(Is), len(gs)), np.nan)
    for r in rows:
        i = np.where(Is == r["demand_current_rms"])[0][0]
        j = np.where(gs == r["demand_phase"])[0][0]
        T[i, j] = r.get("ShaftTorque", np.nan)
        V[i, j] = r.get("Voltage_Phase_RMS", np.nan)
    fT = RegularGridInterpolator((Is, gs), T, bounds_error=False, fill_value=None)
    fV = RegularGridInterpolator((Is, gs), V, bounds_error=False, fill_value=None)
    return fT, fV, Is, gs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=int, default=16000)
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--current", type=float, default=138.0, help="유지하는 전류 [A rms]")
    ap.add_argument("--out", required=True, help="New output CSV; keep archived results intact")
    ap.add_argument("--source-dir", default=W)
    a = ap.parse_args()
    from pathlib import Path
    if Path(a.out).exists():
        ap.error("Output already exists; choose a new path")
    fT, fV, Is, gs = load(a.speed, a.source_dir)
    rng = np.random.default_rng(20260917)

    # 오차원 3종 — (이름, 레졸버 오프셋 균일 ±deg, 지연 잔차 σ deg, λm 드리프트 σ)
    CASES = (("정밀 (오프셋 ±0.5°, 지연잔차 1°)", 0.5, 1.0, 0.00),
             ("보통 (±1.5°, 2°)", 1.5, 2.0, 0.02),
             ("거침 (±3°, 4°)", 3.0, 4.0, 0.05))
    gam_cmds = (80.0, 84.0, 86.0, 88.0, 89.0, 89.5, 89.7)
    rows = []
    print("기준기 %d rpm, 전류 %.0f A rms 유지, 시행 %d 회. 전압 한계 %.1f V rms."
          % (a.speed, a.current, a.n, VLIM))
    for name, off, sig, lam in CASES:
        print("")
        print("### 오차 %s" % name)
        print("%8s | %9s %9s %9s | %8s %8s | %9s"
              % ("γ_cmd", "T 평균", "T 표준편차", "T 변동%", "부호반전%", "전압초과%", "T(무오차)"))
        for g in gam_cmds:
            e = rng.uniform(-off, off, a.n) + rng.normal(0.0, sig, a.n)
            ga = np.clip(g + e, gs[0], 93.0)  # historical linear extrapolation to 93 deg
            cur = np.full(a.n, a.current)
            T = fT(np.stack([cur, ga], axis=-1))
            V = fV(np.stack([cur, ga], axis=-1))
            # λm 드리프트: 자속이 s 배면 같은 전류에서 토크·전압이 대략 s 배로 움직인다
            s = 1.0 + rng.normal(0.0, lam, a.n) if lam > 0 else 1.0
            T, V = T * s, V * s
            T0 = float(fT([[a.current, g]])[0])
            rows.append(dict(speed=a.speed, case=name, gamma_cmd=g, T0=T0, T_mean=float(T.mean()),
                             T_std=float(T.std()), flip_pct=float((T < 0).mean() * 100),
                             vlim_pct=float((V > VLIM).mean() * 100), current=a.current))
            print("%8.1f | %9.2f %9.2f %9.1f | %8.2f %8.2f | %9.2f"
                  % (g, T.mean(), T.std(), 100 * T.std() / max(abs(T.mean()), 1e-6),
                     (T < 0).mean() * 100, (V > VLIM).mean() * 100, T0))
    with io.open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("")
    print("-> %s" % a.out)


if __name__ == "__main__":
    main()
