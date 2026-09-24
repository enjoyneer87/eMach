# -*- coding: utf-8 -*-
"""Slot harmonics in the quasi-static solver: harmonic balance of the current regulator with a clamp.

The Simscape runs (stage 2d, variant D) showed that the slot harmonics do not change the mean torque at a given
mean current, but move the operating point the regulator reaches. This module computes that point without a
time-domain simulation:

1. Harmonic currents (flux constancy). The inverter applies (almost) only the fundamental, so in steady state the
   dq flux stays at its mean and the current carries the harmonics:  psi(i0 + di(x), x) = psi_bar(i0)  for every
   rotor position x  ->  di(x) ~ -L_inc^-1 (psi(i0, x) - psi_bar(i0)),  from the position-resolved FEA map.
2. Command ripple. The regulator passes di through its proportional gain and (if it decouples with measured
   currents) the decoupling term:  dv(x) = (-Kp + D) di(x),  D = [[0, -we Lq], [we Ld, 0]]  (0 with reference-
   current decoupling). Sampling does not matter for what follows: 20 kHz samples at 19.2 deg per sample cover
   all rotor positions uniformly, so averages over samples are averages over x.
3. Clamp. The command v = V + dv(x) is clipped to |v| <= Vmax. Mean clipped excess  d(V) = mean_x[v - clamp(v)]
   (a Fourier average over one electrical period; the dual-input describing function idea: the DC output of a
   saturation driven by a bias plus a periodic signal).
4. Anti-windup equilibrium. With back-calculation (Ki e + Kaw (v_clamp - v)), the integrator input averages to
   zero:  i_ref - i0 = (Kaw/Ki) d(V)  (= d / 8.5 Ohm on both axes for this regulator).
5. Plant mean:  V - d(V) = R i0 + we J psi_bar(i0) + dv_deadtime(i0).
   Unknowns V (2) and i0 (2); four equations.

Output per case: realized mean (id, iq), gamma, shaft torque (mean map, loss convention), fraction of samples
clipped, and the torque with the harmonic currents (mean over x of the position-resolved torque).

python qs_harmonic_hb.py            -> compares with the Simscape stage 2d runs, fea_pos\\qs_harmonic_hb.json
"""
import csv
import json
import os
import sys

import numpy as np
from scipy.interpolate import RegularGridInterpolator as RGI
from scipy.optimize import fsolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fea_posmap_analyze as FA  # noqa: E402
import qs_opsolver as QS  # noqa: E402

DRV = r"D:\KangDH\Thesis\e10\work_lab_pc1\drive"
# regulator of the Simscape model (build_e10_stage2c.m)
CTRL = dict(Ld=0.85e-3, Lq=1.6e-3, Kpd=8.5, Kpq=16.0, Rc=0.0786, Vmax=285.1*np.sqrt(2))
CTRL["Kaw_Ki"] = np.array([1/CTRL["Kpd"], CTRL["Lq"]/(CTRL["Ld"]*CTRL["Kpq"])])   # Kaw/Kid, Kaw/Kiq
R_MODEL = 0.12843                                      # plant resistance of variants B-D (R_dc + R_ac,eff)
VDC, FPWM = 720.0, 1e4
DELTA_DEG = 59.97                                      # theta_d = x + delta (fea_posmap_analyze.alignment)
R_AC16 = R_MODEL - FA.R_DC                             # AC part of the series resistance at 16 krpm (~f^2)


def set_speed(rpm):
    """Operating speed for the calculator: omega_e, and R = R_dc + R_ac,eff(16 krpm) (rpm/16000)^2."""
    global R_MODEL
    FA.set_speed(rpm)
    R_MODEL = FA.R_DC + R_AC16*(rpm/16000.0)**2


def thc():
    return FA.WE*1.5*50e-6                             # delay-compensation angle of the regulator


def window(we, Ts=50e-6, kmax=60):
    """samples spanning a (nearly) whole number of electrical periods: 16 krpm -> 75 samples = 4 periods"""
    n1 = 2*np.pi/(we*Ts)
    k = min(range(1, kmax + 1), key=lambda k: abs(k*n1 - round(k*n1)) + 1e-3*k)
    return int(round(k*n1))
FW = dict(Kfw=200.0, Kleak=2.0)                        # voltage-feedback flux weakening of run_e10_stage2e


class PosMap:
    """Position-resolved FEA band map: psi_d, psi_q, T_em over (id, iq, x); x = rotor position, elec. deg."""

    def __init__(self):
        F = FA.load_fea("band")
        x = np.asarray(F["pos"], float)                 # 0..360 inclusive
        self.x = x[:-1]
        g = (F["id"], F["iq"], x)
        self.fd = RGI(g, F[FA.ANG[0]], bounds_error=False, fill_value=None)
        self.fq = RGI(g, F[FA.ANG[1]], bounds_error=False, fill_value=None)
        self.T = RGI(g, F[FA.ANG[2]], bounds_error=False, fill_value=None)
        self.M = QS.Maps("fea", rac=False)              # mean maps + losses (loss-convention shaft torque)

    def psi(self, i, q, x):
        p = np.stack(np.broadcast_arrays(i, q, np.mod(x, 360.0)), axis=-1)
        return self.fd(p), self.fq(p)

    def psi_bar(self, i, q):
        return (float(self.M.vals("Flux_Linkage_D", i, q)), float(self.M.vals("Flux_Linkage_Q", i, q)))

    def L_inc(self, i, q, h=1.0):
        a = np.array(self.psi_bar(i + h, q)) - np.array(self.psi_bar(i - h, q))
        b = np.array(self.psi_bar(i, q + h)) - np.array(self.psi_bar(i, q - h))
        return np.column_stack([a, b])/(2*h)

    def harmonic_currents(self, i0, q0, iters=3):
        """di(x) that keeps the flux at psi_bar(i0) for every position (chord iterations with L_inc)."""
        Li = np.linalg.inv(self.L_inc(i0, q0))
        tgt = np.array(self.psi_bar(i0, q0))[:, None]
        di = np.zeros((2, len(self.x)))
        for _ in range(iters):
            fd, fq = self.psi(i0 + di[0], q0 + di[1], self.x)
            di = di - Li @ (np.vstack([fd, fq]) - tgt)
        di -= di.mean(axis=1, keepdims=True)
        return di


def sampled_harmonic_currents(PM, i0, q0, ref_decoupling, Ts=50e-6, nsub=16, periods=40, return_x=False,
                              notch=None, delta_deg=DELTA_DEG, full=False):
    """Harmonic currents at the regulator's sampling instants, with the regulator's own reaction.

    Linear, periodic model around (i0, q0):  psi = psi_bar + L (i - i0) + dpsi_slot(x)
      d(dpsi_tot)/dt = dv_applied - R di - we J dpsi_tot,   di = L^-1 (dpsi_tot - dpsi_slot(x))
    The regulator samples di every Ts, computes dv = (-Kp + D) di (proportional path and, with measured-current
    decoupling, D di) and applies it one sample later, held for Ts (the delay compensation rotates the fundamental;
    the ripple is applied as is). The 12th harmonic (12.8 kHz) is above the 10 kHz Nyquist rate and is aliased
    exactly as in the discrete regulator. 16 krpm: 75 samples = 4 electrical periods -> run to periodic steady state
    and return the last 75 samples."""
    we = FA.WE
    L = PM.L_inc(i0, q0)
    Li = np.linalg.inv(L)
    fd, fq = PM.psi(i0, q0, PM.x)
    ds = np.vstack([fd, fq]) - np.array(PM.psi_bar(i0, q0))[:, None]
    C = np.fft.rfft(ds, axis=1)/len(PM.x)                       # Fourier coefficients over x (elec.)
    ks = np.arange(C.shape[1])

    def slot(xdeg):
        ph = np.exp(1j*np.outer(ks, np.radians(xdeg)))
        w = np.where(ks == 0, 1.0, 2.0)[:, None]
        return np.real((C[:, :, None]*w[None]*ph[None]).sum(axis=1))
    J = np.array([[0.0, -1.0], [1.0, 0.0]])
    A = -(R_MODEL*Li + we*J)
    h = Ts/nsub
    from scipy.linalg import expm
    Ad = expm(A*h)
    Bd = np.linalg.solve(A, (Ad - np.eye(2)))                    # exact ZOH for piecewise-constant input
    D = np.zeros((2, 2)) if ref_decoupling else np.array([[0.0, -we*CTRL["Lq"]], [we*CTRL["Ld"], 0.0]])
    G = -np.diag([CTRL["Kpd"], CTRL["Kpq"]]) + D
    nper = window(we, Ts)                                       # 75 at 16 krpm
    N = nper*max(periods*75//nper, 12)
    t_sub = (np.arange(N*nsub) + 0.5)*h
    slot_sub = slot(np.degrees(we*t_sub) - delta_deg)            # Motor-CAD position x = theta_d - delta
    u_slot = R_MODEL*(Li @ slot_sub)                             # forcing from  -R di = -R L^-1 (dpsi - slot)
    x = np.zeros(2)
    pending = np.zeros(2)                                        # command applied in the current interval
    di_s = np.zeros((2, N))
    di_f = np.zeros((2, N))
    zs = np.zeros((2, 4))                                        # notch states per axis
    for n in range(N):
        tn = n*Ts
        di_n = Li @ (x - slot(np.array([np.degrees(we*tn) - delta_deg]))[:, 0])
        di_s[:, n] = di_n
        if notch is not None:                                    # the regulator sees filtered currents
            di_n = np.array([biq2(di_n[a], zs[a], *notch) for a in range(2)])
        di_f[:, n] = di_n
        cmd = G @ di_n
        for k in range(nsub):
            x = Ad @ x + Bd @ (pending + u_slot[:, n*nsub + k])
        pending = cmd
    th = np.mod(np.degrees(we*Ts*np.arange(N - nper, N)), 360.0)  # rotor angle theta_d of each sample
    if full:
        return di_s[:, -nper:], di_f[:, -nper:], th
    if return_x:
        return di_s[:, -nper:], th
    return di_s[:, -nper:]


def biq2(x, z, b1, a1, b2, a2):
    """two biquads in series (direct form II transposed), z = [s1a, s2a, s1b, s2b] updated in place"""
    y1 = b1[0]*x + z[0]
    z[0] = b1[1]*x - a1[1]*y1 + z[1]
    z[1] = b1[2]*x - a1[2]*y1
    y = b2[0]*y1 + z[2]
    z[2] = b2[1]*y1 - a2[1]*y + z[3]
    z[3] = b2[2]*y1 - a2[2]*y
    return y


def notch_coeffs(Ts=50e-6, r=0.9):
    """6th and aliased 12th harmonic notches of run_e10_stage2e (16 krpm)"""
    we = FA.WE
    w1 = np.mod(6*we*Ts, 2*np.pi)
    w12 = np.mod(12*we*Ts, 2*np.pi)
    w2 = min(w12, 2*np.pi - w12)
    out = []
    for w0 in (w1, w2):
        b = np.array([1.0, -2*np.cos(w0), 1.0])
        a = np.array([1.0, -2*r*np.cos(w0), r*r])
        out += [b*a.sum()/b.sum(), a]
    return tuple(out)


def clip_excess(V, dv, vmax, theta=None, khex=None, extra=False):
    """mean clipped excess (vector), clipped fraction; circle |v| <= vmax, or with khex the hexagon (over-
    modulation) at the voltage-vector angle theta_d + thc + angle(v) in the stationary frame"""
    v = V[:, None] + dv
    m = np.hypot(v[0], v[1])
    if khex is not None:
        ph = np.radians(theta) + thc() + np.arctan2(v[1], v[0])
        lim = khex*VDC/np.sqrt(3)/np.cos(np.mod(ph, np.pi/3) - np.pi/6)
    else:
        lim = vmax
    s = np.minimum(1.0, lim/np.maximum(m, 1e-9))
    d, f = (v*(1 - s)).mean(axis=1), float(np.mean(m > lim))
    if extra:
        return d, f, float(np.mean(np.maximum(m - lim, 0.0)))
    return d, f


def solve_case(PM, i_ref, q_ref, td=0.0, harmonics=True, ref_decoupling=False, V0=None, feedback=True,
               notch=False, hexk=None, fw=False):
    """Mean operating point with slot harmonics. Remedies (run_e10_stage2e): notch = 6th/aliased-12th notches in
    the fed-back currents, hexk = hexagon limit factor (over-modulation, e.g. 0.97), fw = voltage-feedback flux
    weakening (extra unknown idfw: Kfw mean((|v| - lim)+) + Kleak idfw = 0)."""
    we = FA.WE
    D = np.zeros((2, 2)) if ref_decoupling else np.array([[0.0, -we*CTRL["Lq"]], [we*CTRL["Ld"], 0.0]])
    G = -np.diag([CTRL["Kpd"], CTRL["Kpq"]]) + D
    dvt = (4/np.pi)*VDC*td*FPWM

    def ripple(i, q):
        nper = window(we)
        if not harmonics:
            return np.zeros((2, nper)), np.zeros((2, nper)), np.mod(np.degrees(we*50e-6)*np.arange(nper), 360.0)
        if not feedback:
            di = PM.harmonic_currents(i, q)
            return di, G @ di, None
        di, dif, th = sampled_harmonic_currents(PM, i, q, ref_decoupling, full=True,
                                                notch=notch_coeffs() if notch else None)
        return di, G @ dif, th

    def v_ss(i, q):
        fd, fq = PM.psi_bar(i, q)
        v = np.array([R_MODEL*i - we*fq, R_MODEL*q + we*fd])
        I = np.hypot(i, q)
        return v + dvt*np.array([i, q])/I

    def solve(dv, th, u0):
        def F(u):
            V, i0 = u[:2], u[2:4]
            idfw = u[4] if fw else 0.0
            d, _, ex = clip_excess(V, dv, CTRL["Vmax"], th, hexk, extra=True)
            r = [V - d - v_ss(*i0), np.array([i_ref + idfw, q_ref]) - i0 - CTRL["Kaw_Ki"]*d]
            if fw:
                r.append([(FW["Kfw"]*ex + FW["Kleak"]*idfw)/FW["Kleak"]])
            return np.concatenate(r)
        return fsolve(F, u0, full_output=True, xtol=1e-10)

    di, dv, th = ripple(i_ref, q_ref)
    u0 = np.concatenate([v_ss(i_ref, q_ref) if V0 is None else V0, [i_ref, q_ref]] + ([[0.0]] if fw else []))
    u, info, ier, msg = solve(dv, th, u0)
    if fw and abs(u[4]) > 0.5:                     # the loop moved i_d: recompute the ripple there and solve again
        di, dv, th = ripple(i_ref + u[4], q_ref)
        u, info, ier, msg = solve(dv, th, u)
    V, (i0, q0) = u[:2], u[2:4]
    idfw = float(u[4]) if fw else 0.0
    d, sat = clip_excess(V, dv, CTRL["Vmax"], th, hexk)
    p = PM.M.point(i0, q0)
    # torque with the harmonic currents (position-resolved map) - mean-map torque
    dih = PM.harmonic_currents(i0, q0) if harmonics else np.zeros((2, len(PM.x)))
    Tx = PM.T(np.stack([i0 + dih[0], q0 + dih[1], PM.x], axis=-1))
    Tsin = PM.T(np.stack([np.full_like(PM.x, i0), np.full_like(PM.x, q0), PM.x], axis=-1))
    return dict(id=float(i0), iq=float(q0), gamma=float(np.degrees(np.arctan2(-i0, q0))),
                I_rms=float(np.hypot(i0, q0)/np.sqrt(2)), T_shaft=p["T_shaft"], sat=100*sat,
                clip_d=float(d[0]), clip_q=float(d[1]), V_cmd=float(np.hypot(*V)), V_d=float(V[0]), V_q=float(V[1]),
                dv_pk=float(np.max(np.hypot(dv[0], dv[1]))), di_pk=float(np.max(np.hypot(di[0], di[1]))),
                T_harm_mean_shift=float(Tx.mean() - p["T_em"]), T_ripple_pp=float(np.ptp(Tx)),
                T_ripple_pp_sin=float(np.ptp(Tsin)), idfw=idfw, converged=bool(ier == 1))


def ref_point(table, T):
    if table.startswith("QS"):
        from scipy.io import loadmat
        q = loadmat(os.path.join(DRV, "qs_tables.mat"), squeeze_me=True, struct_as_record=False)[table.replace(" ", "")]
        return float(np.interp(T, q.Tv, q.idRef)), float(np.interp(T, q.Tv, q.iqRef))
    for r in csv.DictReader(open(os.path.join(DRV, "stage2b_results.csv"))):
        if r["table"] == table and float(r["T_ref"]) == T and float(r["td_us"]) == 0 and float(r["dt_comp"]) == 0:
            return float(r["id_ref"]), float(r["iq_ref"])


def main():
    PM = PosMap()
    rows = []
    for fn in ("stage2d_results.csv", "stage2d_results_mbc90.csv", "stage2d_results_qs.csv",
               "stage2d_results_qs2.csv", "stage2d_results_qs3.csv"):
        rows += list(csv.DictReader(open(os.path.join(DRV, fn))))
    out = []
    for r in rows:
        if r["variant"] not in ("fea_avg", "fea_pos", "fea_pos_ff"):
            continue
        T, td = float(r["T_ref"]), float(r["td_us"])*1e-6
        i_ref, q_ref = ref_point(r["table"], T)
        s = solve_case(PM, i_ref, q_ref, td, harmonics=r["variant"] != "fea_avg",
                       ref_decoupling=r["variant"] == "fea_pos_ff")
        x = dict(variant=r["variant"], table=r["table"], T_ref=T, td_us=td*1e6, sim_T=float(r["T"]),
                 sim_gamma=float(r["gamma"]), sim_sat=float(r["sat_pct"]), sim_ripple=float(r["T_ripple_pp"]),
                 gamma_ref=float(np.degrees(np.arctan2(-i_ref, q_ref))), **s)
        out.append(x)
        print("%-10s %-6s T*%3g td%g | sim T %7.2f g %6.2f sat %3.0f | HB T %7.2f g %6.2f sat %3.0f | dv %5.0f V di %4.1f A %s"
              % (x["variant"], x["table"], T, td*1e6, x["sim_T"], x["sim_gamma"], x["sim_sat"], x["T_shaft"],
                 x["gamma"], x["sat"], x["dv_pk"], x["di_pk"], "" if x["converged"] else "(not converged)"))
    json.dump(out, open(os.path.join(FA.WORK, "qs_harmonic_hb.json"), "w"), indent=1)


REMEDIES = {"base": {}, "notch": dict(notch=True), "hex": dict(hexk=0.97), "fw": dict(fw=True),
            "ffref": dict(ref_decoupling=True), "notch+hex": dict(notch=True, hexk=0.97),
            "hex+fw": dict(hexk=0.97, fw=True), "notch+fw": dict(notch=True, fw=True)}


def remedies_main(tables=("QS 95", "QS 85"), cases=((5, 0.0), (20, 0.0), (60, 0.0), (20, 3e-6)), names=None):
    """Harmonic-balance predictions for the stage 2e remedies -> fea_pos\\qs_hb_remedies.json"""
    PM = PosMap()
    out = []
    for tb in tables:
        for T, td in cases:
            i_ref, q_ref = ref_point(tb, T)
            for nm in (names or REMEDIES):
                s = solve_case(PM, i_ref, q_ref, td, **REMEDIES[nm])
                out.append(dict(remedy=nm, table=tb, T_ref=T, td_us=td*1e6, **s))
                print("%-10s %-6s T*%3g td%g: T %6.2f (%+6.1f %%) gamma %.2f I %.1f sat %3.0f idfw %6.2f %s"
                      % (nm, tb, T, td*1e6, s["T_shaft"], 100*(s["T_shaft"]/T - 1), s["gamma"], s["I_rms"], s["sat"],
                         s["idfw"], "" if s["converged"] else "(nc)"))
    json.dump(out, open(os.path.join(FA.WORK, "qs_hb_remedies.json"), "w"), indent=1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "remedies":
        remedies_main()
    else:
        main()
