# -*- coding: utf-8 -*-
"""Fig 8 n_spd8=2 폭주 재현: 8kRPM 자체 표본 수에 따른 기울기 p의 분포.

Stage 3(기준커널 kappa) -> Stage 4(속도별 (f,p) 로그회귀) 구간만 떼어
실데이터로 직접 계산한다.
"""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
    "tools")))  # 이 체크아웃의 tools
import matplotlib
matplotlib.use("Agg")
from jeet_acloss_rbf.pipeline import AcLossPipeline

SCALE = "SC"
BASE_SPEED = 16.0      # kRPM
TARGET_SPEED = 8.0     # kRPM (SC는 8*k_r^2=32>16 이라 상사전달 불가 -> 자체표본 필수)
N_BASE = 16            # Fig 8에서 78% 가 나온 행
SEEDS = 300

pl = AcLossPipeline()
ds = pl.load_dataset(SCALE)

spd = np.asarray(ds.speeds_k, float)
irm = np.asarray(ds.irms_arr, float)
pha = np.asarray(ds.phase_arr, float)
af = np.asarray(ds.af_arr, float)
LS_I, LS_P = ds.LS_I, ds.LS_P

print(f"데이터셋 {SCALE}: {len(af)}점, 속도 {sorted(set(np.round(spd,1)))}")
base_idx = np.where(np.abs(spd - BASE_SPEED) < 0.1)[0]
tgt_idx = np.where(np.abs(spd - TARGET_SPEED) < 0.1)[0]
print(f"  16kRPM 풀 {len(base_idx)}점 / 8kRPM 풀 {len(tgt_idx)}점\n")


def fit_kernel(sel):
    ib, pb, yb = irm[sel], pha[sel], af[sel]
    n = len(sel)
    Phi = np.zeros((n, n))
    for j in range(n):
        r2 = (ib - ib[j])**2 / LS_I**2 + (pb - pb[j])**2 / LS_P**2
        Phi[:, j] = r2 * np.log(np.sqrt(r2) + 1e-12)
    w = np.linalg.solve(Phi + 1e-6 * np.eye(n), yb)

    def g(I, th):
        Iv = np.atleast_1d(np.asarray(I, float))[:, None]
        tv = np.atleast_1d(np.asarray(th, float))[:, None]
        r2 = (Iv - ib)**2 / LS_I**2 + (tv - pb)**2 / LS_P**2
        return (r2 * np.log(np.sqrt(r2) + 1e-12)) @ w
    return g


print(f"{'n_spd8':>7} {'유효시행':>8} {'p 중앙':>9} {'p 5%':>9} {'p 95%':>9} "
      f"{'|p|>5 비율':>10}  {'log-kappa 간격 중앙':>18}")
print("-" * 82)

for n_spd in (1, 2, 3, 4):
    ps, gaps, ntry = [], [], 0
    for s in range(SEEDS):
        rng = np.random.default_rng(s)
        bsel = rng.choice(base_idx, min(N_BASE, len(base_idx)), replace=False)
        g_local = fit_kernel(bsel)
        pick = rng.choice(tgt_idx, min(n_spd, len(tgt_idx)), replace=False)
        pairs = []
        for i in pick:
            gv = float(g_local(irm[i], pha[i])[0])
            av = float(af[i])
            if av > 0 and gv > 0 and 0.3 <= av / gv <= 3.0:   # 코드와 동일한 필터
                pairs.append((av, gv))
        if not pairs:
            continue
        ntry += 1
        la = np.log([a for a, _ in pairs])
        lg = np.log([g for _, g in pairs])
        if len(pairs) >= 2 and float(np.ptp(lg)) > 1e-3:
            p_s = float(np.polyfit(lg, la, 1)[0])          # 기울기 적합
            gaps.append(float(np.ptp(lg)))
        else:
            p_s = 1.0                                       # 스칼라 폴백
        ps.append(p_s)
    ps = np.asarray(ps)
    big = float(np.mean(np.abs(ps) > 5.0)) * 100
    gm = np.median(gaps) if gaps else float('nan')
    print(f"{n_spd:>7} {ntry:>8} {np.median(ps):>9.2f} "
          f"{np.percentile(ps,5):>9.2f} {np.percentile(ps,95):>9.2f} "
          f"{big:>9.1f}% {gm:>18.4f}")

print("\n※ p 는 exponent 모델의 속도별 스프레드 지수. 채택 앵커는 p(16k)=1.")
print("  |p|>5 는 사실상 발산으로, p(omega) 2차적합을 통해 전 속도로 전파된다.")
