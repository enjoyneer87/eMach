# -*- coding: utf-8 -*-
"""Where is the slot-harmonic notch needed, and where is it safe? — 6–16 krpm with the harmonic-balance calculator.

For each speed n and torque T (fixed 16 krpm shaft-torque map, see fea_posmap_analyze.set_speed):
  reference point = minimum current with |R(n) i + j w_e psi| <= 0.95 Vmax (5 % margin table at that speed),
                    R(n) = R_dc + R_ac,eff(16 krpm) (n/16000)^2
  harmonic balance (qs_harmonic_hb.solve_case) with the standard regulator, without and with the notches
  (6th and the 12th folded into [0, fs/2]).
Notch side of the trade: phase the two notches add at the current-loop crossover (Kp/L = 1e4 rad/s, 1.59 kHz),
and how close the 6th harmonic sits to that crossover (6 f_e / f_c).
All operating points lie inside the position-resolved FEA band (i_q <= 52 A).

python notch_speed_range.py   -> fea_pos\\notch_speed_range.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fea_posmap_analyze as FA  # noqa: E402
import qs_harmonic_hb as HB  # noqa: E402

SPEEDS = (6000, 8000, 10000, 12000, 14000, 16000)
TORQUES = (20, 60, 100, 150)
TS, WC = 50e-6, 1e4


def ref_point(PM, T, margin=0.05, did=0.25, diq=0.02):
    """minimum-current point of the fixed torque map T16 at this speed with |v| <= Vmax (1 - margin)"""
    M = PM.M
    ids = np.arange(-float(-min(PM.M.g["Flux_Linkage_D"].grid[0])), -40.0, did)
    iqs = np.arange(0.0, 52.0, diq)
    I, Q = ids[:, None], iqs[None, :]
    P = M.points(I, Q, 0.0, rac=False)                 # T_shaft with 16 krpm braking losses (fixed map)
    fd, fq = M.vals("Flux_Linkage_D", I, Q), M.vals("Flux_Linkage_Q", I, Q)
    V = np.hypot(HB.R_MODEL*I - FA.WE*fq, HB.R_MODEL*Q + FA.WE*fd)
    Tm = P["T_shaft"]
    up = (Tm[:, :-1] < T) & (Tm[:, 1:] >= T)
    has = up.any(axis=1)
    if not has.any():
        return None
    j = np.argmax(up, axis=1)
    r = np.arange(len(ids))
    f = (T - Tm[r, j])/np.where(has, Tm[r, j + 1] - Tm[r, j], 1.0)
    q = iqs[j] + f*diq
    v = V[r, j] + f*(V[r, j + 1] - V[r, j])
    ok = has & (v <= HB.CTRL["Vmax"]*(1 - margin))
    if not ok.any():
        return None
    k = int(np.argmin(np.where(ok, np.hypot(ids, q), np.inf)))
    return float(ids[k]), float(q[k])


TGRID = (0, 2.5, 5, 7.5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 100, 120, 150)


def speed_tables(PM, speeds=SPEEDS, margin=0.05):
    """5 % margin reference tables at each speed (fixed torque map) -> drive\\qs_speed_tables.mat, fields N6000 ..."""
    from scipy.io import savemat
    out = {}
    for n in speeds:
        HB.set_speed(n)
        Tv, idr, iqr = [], [], []
        for T in TGRID:
            rp = ref_point(PM, T, margin) if T > 0 else ref_point(PM, 0.01, margin)
            if rp is None:
                break
            Tv.append(float(T))
            idr.append(rp[0])
            iqr.append(rp[1])
        out["N%d" % n] = dict(Tv=np.array(Tv), idRef=np.array(idr), iqRef=np.array(iqr), rpm=float(n), margin=margin,
                              R=HB.R_MODEL)
        print("N%d: %d points up to %g N·m" % (n, len(Tv), Tv[-1]))
    HB.set_speed(16000)
    savemat(os.path.join(os.path.dirname(FA.WORK), "drive", "qs_speed_tables.mat"), out, oned_as="column")


def notch_phase():
    """phase [deg] and gain of the two notches at the current-loop crossover, at the present speed"""
    b1, a1, b2, a2 = HB.notch_coeffs()
    w = WC*TS
    z = np.exp(-1j*w*np.arange(3))
    h = (b1 @ z)/(a1 @ z)*(b2 @ z)/(a2 @ z)
    return float(np.degrees(np.angle(h))), float(abs(h))


def main():
    PM = HB.PosMap()
    out = []
    for n in SPEEDS:
        HB.set_speed(n)
        fe = FA.WE/(2*np.pi)
        ph, g = notch_phase()
        f12 = 12*fe % (1/TS)
        f12 = min(f12, 1/TS - f12)
        for T in TORQUES:
            rp = ref_point(PM, T)
            if rp is None:
                continue
            i_ref, q_ref = rp
            row = dict(rpm=n, T=T, id_ref=i_ref, iq_ref=q_ref, f6=6*fe, f12_seen=f12, notch_phase_fc=ph,
                       notch_gain_fc=g, ratio_6fe_fc=6*fe/(WC/2/np.pi), R=HB.R_MODEL)
            for tag, kw in (("base", {}), ("notch", dict(notch=True))):
                s = HB.solve_case(PM, i_ref, q_ref, 0.0, **kw)
                row[tag] = dict(T=s["T_shaft"], err=100*(s["T_shaft"]/T - 1), gamma=s["gamma"], sat=s["sat"],
                                dv_pk=s["dv_pk"], di_pk=s["di_pk"], converged=s["converged"])
            out.append(row)
            print("%5d rpm %3d N·m ref (%6.1f, %5.1f) | base %+7.1f %% sat %3.0f %% dv %4.0f V | notch %+6.1f %% sat %3.0f %%"
                  " | 6fe %.1f kHz (%.1f x fc), notch at fc %+.1f deg" % (
                      n, T, i_ref, q_ref, row["base"]["err"], row["base"]["sat"], row["base"]["dv_pk"],
                      row["notch"]["err"], row["notch"]["sat"], 6*fe/1e3, row["ratio_6fe_fc"], ph))
    json.dump(out, open(os.path.join(FA.WORK, "notch_speed_range.json"), "w"), indent=1)
    HB.set_speed(16000)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tables":
        speed_tables(HB.PosMap())
    else:
        main()
