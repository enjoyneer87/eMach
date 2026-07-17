import numpy as np
import sys
sys.path.insert(0, r'D:\KangDH\Thesis\ACloss_Ref\ACloss')
from ju_hybrid_acloss import xi_nu, _dowell_M, _dowell_Q, skin_depth_nu

SIGMA = 5.8e7
H_REF = 2.0e-3
H_SC  = H_REF * 2
H_HSC = H_REF * 1.5
SPEEDS = [2000, 4000, 8000, 16000]
POLES = 4
F_LIST = [s * POLES / 60.0 for s in SPEEDS]
I_REF = 460.0; I_SC = 920.0; I_HSC = 690.0
N_L = 6; W_SLOT = 6.0e-3; MU0 = 4*np.pi*1e-7

print("=" * 75)
print("  스킨 깊이 및 xi = h/delta 분석 (속도별, 모델별)")
print("=" * 75)
print("{:>12} {:>10} {:>8} {:>8} {:>8} {:>8}".format("속도[RPM]","f_e[Hz]","delta[mm]","xi_Ref","xi_HSC","xi_SC"))
print("-" * 75)
for spd, f in zip(SPEEDS, F_LIST):
    delta = skin_depth_nu(f, 1, SIGMA)
    xi_ref = H_REF / delta
    xi_hsc = H_HSC / delta
    xi_sc  = H_SC  / delta
    print("{:>12} {:>10.2f} {:>8.3f} {:>8.4f} {:>8.4f} {:>8.4f}".format(
        spd, f, delta*1e3, xi_ref, xi_hsc, xi_sc))

print()
print("=" * 75)
print("  kR(m, xi) = M(xi) + (2m-1)^2/3 * Q(xi) -- 속도 & 모델별")
print("=" * 75)
for spd, f in zip(SPEEDS, F_LIST):
    delta = skin_depth_nu(f, 1, SIGMA)
    print("\n  [%d RPM, f=%.2f Hz]" % (spd, f))
    for label, h in [('Ref', H_REF), ('HSC', H_HSC), ('SC', H_SC)]:
        xi_val = h / delta
        kR_by_layer = []
        for m in range(1, N_L + 1):
            kR_m = _dowell_M(xi_val) + ((2.0*m - 1.0)**2 / 3.0) * _dowell_Q(xi_val)
            kR_by_layer.append(kR_m)
        avg_kR = np.mean(kR_by_layer)
        vals_str = ", ".join("%.2f" % k for k in kR_by_layer)
        print("    %-4s (xi=%.3f): L1~L6 kR = [%s]  avg=%.3f" % (label, xi_val, vals_str, avg_kR))

print()
print("=" * 75)
print("  근접손실 P_prox 스케일링 비교")
print("=" * 75)
print("{:>12} {:>8} {:>12} {:>12} {:>12} {:>8} {:>9}".format(
    "속도[RPM]","f_e[Hz]","Prox_Ref[W]","Prox_HSC[W]","Prox_SC[W]","SC/Ref","HSC/Ref"))
print("-" * 75)
for spd, f in zip(SPEEDS, F_LIST):
    omega = 2 * np.pi * f
    P_list = []
    for label, I, h in [('Ref', I_REF, H_REF), ('HSC', I_HSC, H_HSC), ('SC', I_SC, H_SC)]:
        delta = skin_depth_nu(f, 1, SIGMA)
        xi_val = h / delta
        F_prox = _dowell_Q(xi_val) * 3.0 / xi_val**3 if xi_val > 1e-4 else 1.0
        P_tot = 0.0
        for m in range(1, N_L + 1):
            B_m = MU0 * m * np.sqrt(2.0) * I / W_SLOT
            p_m = SIGMA * omega**2 * B_m**2 * W_SLOT * h**3 / 24.0 * F_prox
            P_tot += p_m
        P_list.append(P_tot)
    ratio_sc  = P_list[2] / P_list[0]
    ratio_hsc = P_list[1] / P_list[0]
    print("{:>12} {:>8.2f} {:>12.4f} {:>12.4f} {:>12.4f} {:>8.3f} {:>9.3f}".format(
        spd, f, P_list[0], P_list[1], P_list[2], ratio_sc, ratio_hsc))

print()
print("  [이론 thin-conductor] P_prox ~ I^2 * h^3 * f^2")
print("  P_prox_SC/P_prox_Ref = (I_SC/I_Ref)^2 * (h_SC/h_Ref)^3 = k^2 * k^3 = k^5")
print("    k=2.0: k^5 = %.1f" % (2.0**5))
print("    k=1.5: k^5 = %.4f" % (1.5**5))
print()
print("  고주파에서 F_prox(xi) 감소 -> SC/Ref 비율이 이론치보다 작아짐 (인덕턴스 제한)")

print()
print("=" * 75)
print("  Hybrid vs TS 괴리 원인: TS/Hybrid 비율 경향 예측")
print("=" * 75)
print("  Hybrid = Dowell 해석 공식 (1D 평면파 가정)")
print("  TS     = 완전 FEA (도체 내부 와전류 back-reaction 포함)")
print()
for spd, f in zip(SPEEDS, F_LIST):
    delta = skin_depth_nu(f, 1, SIGMA)
    for label, h in [('Ref', H_REF), ('HSC', H_HSC), ('SC', H_SC)]:
        xi_val = h / delta
        F_prox = _dowell_Q(xi_val) * 3.0 / xi_val**3 if xi_val > 1e-4 else 1.0
        print("  [%d RPM] %-4s xi=%.3f -> F_prox=%.4f (Hybrid 과대예측 배율: 1/F=%.2fx)" % (
            spd, label, xi_val, F_prox, 1.0/F_prox if F_prox > 0 else 99))
print()
print("  xi>>1 일수록 F_prox<<1, 즉 Dowell thin-cond 공식이 실제보다 크게 예측")
print("  => TS/Hybrid < 1 경향 (FEA가 더 정확히 낮은 손실 계산)")
print("  단, 로터 PM 자기장은 TS만 포착 => 저속 일부에서 TS/Hybrid > 1 가능")
