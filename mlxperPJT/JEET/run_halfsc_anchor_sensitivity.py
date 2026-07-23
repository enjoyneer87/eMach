# -*- coding: utf-8 -*-
"""16k 앵커 3점의 배치 민감도 — 어떤 고정 좌표까지 허용되는가."""
import os, sys
sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
from jeet_acloss_rbf.pipeline import AcLossPipeline

K_H, K_S = 1.5, 2.0
pl = AcLossPipeline()
ds = pl.load_dataset("HalfSC")
f_ac, h_ac = ds.f_ac_arr, ds.h_ac_arr
w = ds.speeds_k * 1000.0
m_sc, m_ref = pl.build_model("SC"), pl.build_model("Ref")
af_C = m_sc.predict(w * (K_H/K_S)**2, ds.irms_arr * K_S/K_H, ds.phase_arr)
af_D = m_ref.predict(w * K_H**2, ds.irms_arr / K_H, ds.phase_arr)
hi = ds.speeds_k > 8.5
idx16 = np.where(hi)[0]

I16, P16 = ds.irms_arr[idx16], ds.phase_arr[idx16]
zs16, tr16 = af_C[idx16], ds.af_arr[idx16]


def eval_with_anchor(pick_local):
    x = np.log(np.clip(zs16[pick_local], 1e-3, None))
    y = np.log(np.clip(tr16[pick_local], 1e-3, None))
    if len(set(np.round(x, 6))) < 2:
        return None, None
    p_c, lf = np.polyfit(x, y, 1)
    af = np.where(hi, np.exp(lf) * np.clip(af_C, 1e-3, None)**p_c, af_D)
    pred = h_ac * af
    e = np.abs((pred - f_ac) / (f_ac + 1e-12) * 100)
    wmae = np.sum(f_ac * e) / np.sum(f_ac)
    m = hi
    w16 = np.sum(f_ac[m] * e[m]) / np.sum(f_ac[m])
    return float(wmae), float(w16)


def nearest(Iq, Pq):
    return int(np.argmin((I16 - Iq)**2 / 100**2 + (P16 - Pq)**2 / 20**2))


order = np.argsort(zs16)
cases = {
    "S1 κ-스팬 (min/med/max)":  [order[0], order[len(order)//2], order[-1]],
    "S2 고정: I_max·β={0,45,90}": [nearest(690, 0), nearest(690, 45), nearest(690, 90)],
    "S3 고정: (I_max,0)(I_max,90)(I_mid,45)": [nearest(690, 0), nearest(690, 90), nearest(345, 45)],
    "S4 저전류만: I_min·β={0,45,90}": [nearest(172.5, 0), nearest(172.5, 45), nearest(172.5, 90)],
    "S5 밀집(중앙 이웃 3점)":  [order[len(order)//2 - 1], order[len(order)//2], order[len(order)//2 + 1]],
    "S6 2점(min/max)":          [order[0], order[-1]],
}
print(f"16k 후보 격자 {len(idx16)}점 · 예측AF 범위 {zs16.min():.2f}~{zs16.max():.2f}")
print(f"\n{'배치':<38}{'전체wMAE%':>10}{'16k wMAE%':>10}")
print("-" * 58)
for name, pk in cases.items():
    pts = [(round(float(I16[i])), round(float(P16[i]))) for i in pk]
    wm, w16 = eval_with_anchor(list(pk))
    if wm is None:
        print(f"{name:<38}{'회귀불능':>10}")
        continue
    print(f"{name:<38}{wm:>10.2f}{w16:>10.2f}   {pts}")
