# -*- coding: utf-8 -*-
"""Quasi-static operating-point solver with an effective voltage limit (no time-domain simulation).

The time-domain drive models (sim_e10_stage2, Simscape stage 2c/2d) show that at 16 krpm an operating point
is lost when the voltage the current regulator must produce exceeds its clamp (403.2 V pk), and that
deadtime, input-side losses and angle errors eat into that clamp. This solver puts the same effects into a
steady-state calculation so operating points can be found in milliseconds:

  T_shaft(id, iq) = T*                          loss convention (loss_torque_convention.html):
                                                  T_em - (P_mech + P_fe,rotor + P_magnet + P_fe,s,NL + P_ac,NL)/w_m
  |v_ss + dv_dt| <= V_ctrl (1 - margin)         v_ss = (R_dc + R_ac(i)) i + j w_e psi(i)
                                                  R_ac(i) = (P_ac - P_ac,NL)/(1.5 |i|^2)  (input-side AC copper)
                                                  dv_dt = +(4/pi) V_dc t_d f_pwm i/|i|   (uncompensated deadtime:
                                                  the inverter delivers v_cmd - dv i/|i|, so the command must be
                                                  v_ss + dv i/|i|; dv = fundamental of the per-phase square wave)
  |i| <= I_max

Two questions are answered for each torque demand:
  best   the minimum-current feasible point (what a calibration with this effective limit would choose);
  held   for a given reference point (id*, iq*) that violates the limit, the point with the same current
         magnitude on the effective limit contour (how the saturated regulator ends up, compared with the
         Simscape runs).
Maps: 'lab' = Lab export (Interpolate Lab Model); 'fea' = direct FEA band, position-averaged (fea_posmap).

python qs_opsolver.py [--map lab|fea] [--td 3e-6] [--margin 0.0]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fea_posmap_analyze as FA  # noqa: E402

VDC, FPWM, VCTRL, IMAX = 720.0, 1e4, 285.1*np.sqrt(2), 460*np.sqrt(2)
MCB = [(5, -190.9, 2.2), (20, -195.7, 6.8), (40, -203.7, 12.8), (60, -221.4, 18.3), (80, -242.9, 22.8)]


KEYS = ("Flux_Linkage_D", "Flux_Linkage_Q", "Electromagnetic_Torque", "Iron_Loss_Stator", "Iron_Loss_Rotor",
        "Magnet_Loss", "Stator_Copper_Loss_AC")
ODD = ("Flux_Linkage_Q", "Electromagnetic_Torque")          # odd in iq (Lab export covers iq >= 0 only)


class Maps:
    """psi_d, psi_q, T_em and 16 krpm losses as functions of (id, iq) peak A (arrays welcome)."""

    def __init__(self, kind, rac=True):
        from scipy.interpolate import RegularGridInterpolator as RGI
        self.kind = kind
        self.rac = rac
        if kind == "lab":
            idg, iqg, g = FA.load_lab()
            src, grid, self.sym = {k: g[k] for k in KEYS}, (idg, iqg), True
            self.i_max = 600.0
        else:
            F = FA.load_fea("band")
            avg = {k: F[k][:, :, :-1].mean(axis=2) for k in FA.ANG[:3]}
            src = {"Flux_Linkage_D": avg[FA.ANG[0]], "Flux_Linkage_Q": avg[FA.ANG[1]],
                   "Electromagnetic_Torque": avg[FA.ANG[2]]}
            for k in KEYS[3:]:
                src[k] = F[k]
            grid, self.sym = (F["id"], F["iq"]), False
            self.i_max = float(-np.min(F["id"]))                  # stay inside the FEA band
        self.g = {k: RGI(grid, v, bounds_error=False, fill_value=None) for k, v in src.items()}
        self.nl_fes = float(self.vals("Iron_Loss_Stator", 0.0, 0.0))
        self.nl_ac = float(self.vals("Stator_Copper_Loss_AC", 0.0, 0.0))

    def vals(self, key, i, q):
        i, q = np.broadcast_arrays(np.asarray(i, float), np.asarray(q, float))
        sgn = np.ones(i.shape)
        if self.sym:
            if key in ODD:
                sgn = np.where(q < 0, -1.0, 1.0)
            q = np.abs(q)
        return sgn*self.g[key](np.stack([i.ravel(), q.ravel()], axis=-1)).reshape(i.shape)

    def points(self, i, q, td=0.0, rac=None):
        rac = self.rac if rac is None else rac
        v = {k: self.vals(k, i, q) for k in KEYS}
        i, q = np.broadcast_arrays(np.asarray(i, float), np.asarray(q, float))
        brake = FA.P_MECH + v["Iron_Loss_Rotor"] + v["Magnet_Loss"] + self.nl_fes + self.nl_ac
        I = np.hypot(i, q)
        Is = np.maximum(I, 1.0)
        R = FA.R_DC + (np.where(I > 1, np.maximum(v["Stator_Copper_Loss_AC"] - self.nl_ac, 0.0)/(1.5*Is*Is), 0.0)
                       if rac else 0.0)
        vd, vq = R*i - FA.WE*v["Flux_Linkage_Q"], R*q + FA.WE*v["Flux_Linkage_D"]
        if td > 0:
            dv = np.where(I > 1, (4/np.pi)*VDC*td*FPWM, 0.0)
            vd, vq = vd + dv*i/Is, vq + dv*q/Is
        Tem = v["Electromagnetic_Torque"]
        return dict(T_shaft=Tem - brake/FA.WM, T_em=Tem, V=np.hypot(vd, vq), R=R*np.ones(I.shape), I=I)

    def point(self, i, q, td=0.0, rac=None):
        return {k: float(v) for k, v in self.points(i, q, td, rac).items()}


def best_point(M, Tstar, Veff, td, did=0.25, diq=0.02, iq_max=60.0):
    """Minimum-current feasible point for torque Tstar.

    Searched on an (id, iq) grid, not over (I, gamma): near 90 deg the current that meets a small torque
    changes by tens of amperes per 0.01 deg, so an angle grid misses the minimum. For every id the
    torque T_shaft rises monotonically with iq; its crossing of T* is interpolated, and the smallest current
    whose voltage fits is kept. The grid (T_shaft, V over id x iq) is cached per deadtime."""
    key = (td, did, diq, iq_max)
    cache = M.__dict__.setdefault("_grid", {})
    if key not in cache:
        ids = np.arange(-M.i_max, -60.0, did)
        iqs = np.arange(0.0, iq_max, diq)
        P = M.points(ids[:, None], iqs[None, :], td)
        cache[key] = (ids, iqs, P["T_shaft"], P["V"])
    ids, iqs, T, V = cache[key]
    up = (T[:, :-1] < Tstar) & (T[:, 1:] >= Tstar)
    has = up.any(axis=1)
    if not has.any():
        return None
    j = np.argmax(up, axis=1)
    r = np.arange(len(ids))
    f = (Tstar - T[r, j])/np.where(has, T[r, j + 1] - T[r, j], 1.0)
    q = iqs[j] + f*diq
    v = V[r, j] + f*(V[r, j + 1] - V[r, j])
    I = np.hypot(ids, q)
    ok = has & (v <= Veff)
    if not ok.any():
        return None
    k = int(np.argmin(np.where(ok, I, np.inf)))
    p = M.point(ids[k], q[k], td)
    return dict(p, gamma=float(np.degrees(np.arctan2(-ids[k], q[k]))), id=float(ids[k]), iq=float(q[k]))


def held_point(M, i0, q0, Veff, td):
    """Same current magnitude, moved along the circle towards larger gamma until the voltage fits.

    At constant current the voltage falls with gamma up to about 90 deg and rises again, so first find the
    voltage minimum above the reference angle; if even that does not fit, the point stays at the minimum
    (the regulator cannot hold this current)."""
    I = np.hypot(i0, q0)
    g0 = np.degrees(np.arctan2(-i0, q0))
    at = lambda g: M.point(-I*np.sin(np.radians(g)), I*np.cos(np.radians(g)), td)
    p0 = M.point(i0, q0, td)
    if p0["V"] <= Veff:
        return dict(p0, gamma=float(g0), id=i0, iq=q0, feasible=True, note="fits")
    gs = np.arange(g0, 96.0, 0.01)
    V = M.points(-I*np.sin(np.radians(gs)), I*np.cos(np.radians(gs)), td)["V"]
    kmin = int(np.argmin(V))
    if V[kmin] > Veff:
        g = gs[kmin]
        return dict(at(g), gamma=float(g), id=-I*np.sin(np.radians(g)), iq=I*np.cos(np.radians(g)),
                    feasible=False, note="no angle fits at this current")
    k = int(np.argmax(V[:kmin + 1] <= Veff))
    g = gs[k]
    return dict(at(g), gamma=float(g), id=-I*np.sin(np.radians(g)), iq=I*np.cos(np.radians(g)), feasible=False,
                note="moved to the limit")


TGRID = (0, 2.5, 5, 7.5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80)


def ref_tables(M, margins, Tgrid=TGRID, td=0.0):
    """16 krpm reference tables (torque -> id*, iq*) at given voltage margins, for run_e10_stage2d ('QS 85' etc.).

    Each point is best_point (minimum current meeting T_shaft = T* with |v| <= V_clamp (1 - margin)); the table
    stops at the first torque that no angle can reach."""
    out = {}
    for m in margins:
        Tv, idr, iqr = [], [], []
        for T in Tgrid:
            b = best_point(M, T, VCTRL*(1 - m), td)
            if b is None:
                break
            Tv.append(float(T))
            idr.append(b["id"])
            iqr.append(b["iq"])
            print("margin %4.1f %%  T %5.1f  id %7.2f  iq %6.2f  gamma %.2f  V %.1f" % (100*m, T, b["id"], b["iq"],
                                                                                   b["gamma"], b["V"]))
        out["QS%d" % round(100*(1 - m))] = dict(Tv=np.array(Tv), idRef=np.array(idr), iqRef=np.array(iqr),
                                                  margin=m, map=M.kind, rac=M.rac)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default="lab", choices=["lab", "fea"])
    ap.add_argument("--td", type=float, default=0.0, help="uncompensated deadtime [s]")
    ap.add_argument("--margin", type=float, default=0.0, help="voltage margin fraction below the clamp")
    ap.add_argument("--norac", action="store_true", help="leave the input-side AC copper out of the voltage")
    ap.add_argument("--tables", default="", help="comma-separated margins, e.g. 0.10,0.15,0.20: write "
                                                 "drive\\qs_tables.mat (reference tables for run_e10_stage2d)")
    a = ap.parse_args()
    M = Maps(a.map, rac=not a.norac)
    if a.tables:
        from scipy.io import savemat
        tabs = ref_tables(M, [float(x) for x in a.tables.split(",")])
        fn = os.path.join(os.path.dirname(FA.WORK), "drive", "qs_tables.mat")
        savemat(fn, tabs, oned_as="column")
        print("->", fn)
        return
    Veff = VCTRL*(1 - a.margin)
    out = dict(map=a.map, td=a.td, margin=a.margin, Veff=Veff, rac=not a.norac, rows=[])
    print("map %s  td %.1f us  margin %.1f %%  V_eff %.1f V pk  R_ac %s" % (a.map, a.td*1e6, 100*a.margin, Veff,
                                                                          "on" if not a.norac else "off"))
    for T, i0, q0 in MCB:
        b = best_point(M, T, Veff, a.td)
        h = held_point(M, i0, q0, Veff, a.td)
        out["rows"].append(dict(T=T, best=b, held_MCB=h))
        print("T*=%3d  best: gamma %s I %s V %s | MCB point (%.1f, %.1f): V %.1f -> held gamma %.2f T %.2f (%s)"
              % (T, "%.2f" % b["gamma"] if b else "-", "%.1f" % (b["I"]/np.sqrt(2)) if b else "-",
                 "%.1f" % b["V"] if b else "-", i0, q0, M.point(i0, q0, a.td)["V"], h["gamma"], h["T_shaft"],
                 "feasible" if h["feasible"] else "limited"))
    fn = os.path.join(FA.WORK, "qs_%s_td%g_m%g%s.json" % (a.map, a.td*1e6, a.margin, "_norac" if a.norac else ""))
    json.dump(out, open(fn, "w"), indent=1)


if __name__ == "__main__":
    main()
