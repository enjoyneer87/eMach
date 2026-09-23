# -*- coding: utf-8 -*-
"""Analyse the rotor-position FEA map of e10 (fea_posmap.py) around the 16 krpm operating band.

(a) Lab check: position-averaged FEA psi_d, psi_q, T_em and 16 krpm losses against the Lab export
    (Interpolate Lab Model, 48 FEA build points) at the same grid points and at the table operating points.
(b) Harmonics: spectra of psi_d, psi_q and torque over rotor position, torque ripple, and the 16 krpm
    phase-voltage waveform with sinusoidal currents (peak of the alpha-beta voltage vs its fundamental).
(c) Loss convention (loss_torque_convention.html): braking = P_mech + P_fe,rotor + P_magnet + P_fe,stator,NL
    + P_cu,ac,NL (NL = no load, id = iq = 0 at 16 krpm); input side = AC copper load part + stator iron
    armature part. Motor-CAD Lab instead brakes with all stator iron loss (FMU fit, 96 points, 2.4 W).
(d) Tables for the Simscape fem_motor_dq0 block -> stage2d_tables.mat (v7), variants
    B lab_conv  Lab maps, convention torque, Rs = R_dc + R_ac,eff (input-side AC copper as series resistance)
    C fea_avg   as B, but FEA position-averaged psi/T inside the FEA band
    D fea_pos   as C, but FEA position-resolved (slot harmonics, cogging) inside the band
    (variant A = the stage 2c model as built: Lab maps replicated over angle, Lab shaft-torque definition).

python fea_posmap_analyze.py [--tag band]
"""
import argparse
import glob
import json
import os

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.io import loadmat, savemat

WORK = r"D:\KangDH\Thesis\e10\work_lab_pc1\fea_pos"
DRV = r"D:\KangDH\Thesis\e10\work_lab_pc1\drive"
LAB16 = os.path.join(DRV, "e10_satloss_16000.mat")
RPM, P_POLE, R_DC = 16000.0, 4, 0.0786
WM = RPM*2*np.pi/60
WE = P_POLE*WM
P_MECH = 159.73                    # Lab FMU windage at 16 krpm (friction 0)
VMAX = 285.1*np.sqrt(2)
OPS = [(5, -190.9, 2.2), (20, -195.7, 6.8), (40, -203.7, 12.8), (60, -221.4, 18.3), (80, -242.9, 22.8)]
SCAL = ["Flux_Linkage_D", "Flux_Linkage_Q", "Electromagnetic_Torque", "Torque_Ripple_Peak_to_Peak",
        "Iron_Loss_Stator", "Iron_Loss_Rotor", "Magnet_Loss", "Stator_Copper_Loss_AC", "Stator_Copper_Loss_DC"]
ANG = ["Angular_Flux_Linkage_D", "Angular_Flux_Linkage_Q", "Angular_Electromagnetic_Torque",
       "Angular_Flux_Linkage_Phase_1", "Angular_Flux_Linkage_Phase_2", "Angular_Flux_Linkage_Phase_3"]


# ------------------------------------------------------------------ loading
def load_fea(tag):
    files = sorted(glob.glob(os.path.join(WORK, "posmap_%s_[0-9][0-9].mat" % tag)))
    if not files:
        raise SystemExit("no posmap_%s_NN.mat in %s" % (tag, WORK))
    parts = [loadmat(f, squeeze_me=False) for f in files]
    ids = np.asarray(parts[0]["Id_Peak"], float)[:, 0]
    iq_list, S, A = [], {k: [] for k in SCAL}, {k: [] for k in ANG}
    for p in parts:
        idp = np.asarray(p["Id_Peak"], float)
        iqp = np.asarray(p["Iq_Peak"], float)
        assert np.allclose(idp[:, 0], ids), "id grids differ between chunks"
        iq_list.append(iqp[0, :])
        for k in SCAL:
            S[k].append(np.asarray(p[k], float))
        for k in ANG:
            A[k].append(np.asarray(p[k], float))
    iqs = np.concatenate(iq_list)
    order = np.argsort(iqs)
    out = dict(id=ids, iq=iqs[order], pos=np.asarray(parts[0]["Angular_Rotor_Position"], float)[0, 0, :],
               files=files)
    for k in SCAL:
        out[k] = np.concatenate(S[k], axis=1)[:, order]
    for k in ANG:
        out[k] = np.concatenate(A[k], axis=1)[:, order, :]
    return out


def load_lab():
    """Lab export on its own grid, oriented as (id, iq) with ascending axes. The export is 51 x 51, so the
    orientation cannot be read from the shape (a transposed square map fails silently): use Id_Peak."""
    m = loadmat(LAB16, squeeze_me=True)
    Idp = np.asarray(m["Id_Peak"], float)
    tr = np.ptp(Idp[:, 0]) < 1e-9                      # id constant down a column -> id varies along axis 1
    def orient(v):
        v = np.asarray(v, float)
        return v.T if tr else v
    Idp, Iqp = orient(m["Id_Peak"]), orient(m["Iq_Peak"])
    idg, iqg = Idp[:, 0], Iqp[0, :]
    oi, oq = np.argsort(idg), np.argsort(iqg)
    grid = {}
    for k in SCAL[:3] + SCAL[4:] + ["Voltage_Phase_Peak", "Torque_Ripple_Peak_to_Peak"]:
        grid[k] = orient(m[k])[np.ix_(oi, oq)]
    return idg[oi], iqg[oq], grid


def lab_at(lab, key, i, q):
    idg, iqg, g = lab
    sgn = 1.0
    if q < 0:                                          # symmetric extension (psi_d, losses even; psi_q, T odd)
        q = -q
        if key in ("Flux_Linkage_Q", "Electromagnetic_Torque"):
            sgn = -1.0
    f = RegularGridInterpolator((idg, iqg), g[key], bounds_error=False, fill_value=None)
    return sgn*float(f([[i, q]])[0])


# ------------------------------------------------------------------ geometry of the rotor angle
def alignment(F):
    """theta_d(x) = s*x + delta (elec. rad): angle from phase A to the d-axis at Motor-CAD position x."""
    i0 = int(np.argmin(np.abs(F["id"])))
    j0 = int(np.argmin(np.abs(F["iq"])))
    x = np.radians(F["pos"][:-1])
    c = [np.sum(F[k][i0, j0, :-1]*np.exp(-1j*x)) for k in ANG[3:]]
    d1, d2 = np.angle(c[0]), np.angle(c[1])
    s = +1 if np.cos((d2 - d1) + 2*np.pi/3) > 0.5 else -1           # phase 2 lags phase 1 by 120 deg
    delta = d1 if s == +1 else -d1
    return s, delta


def park(pa, pb, pc, th):
    k = 2*np.pi/3
    d = (2/3)*(pa*np.cos(th) + pb*np.cos(th - k) + pc*np.cos(th + k))
    q = -(2/3)*(pa*np.sin(th) + pb*np.sin(th - k) + pc*np.sin(th + k))
    return d, q


def at_point(F, key, i, q):
    """Interpolate an angular array (id, iq, pos) at a current point -> waveform over positions."""
    f = RegularGridInterpolator((F["id"], F["iq"]), F[key], bounds_error=False, fill_value=None)
    return f([[i, q]])[0]


def scal_at(F, key, i, q):
    f = RegularGridInterpolator((F["id"], F["iq"]), F[key], bounds_error=False, fill_value=None)
    return float(f([[i, q]])[0])


def spectrum(y):
    y = np.asarray(y[:-1], float)
    c = np.fft.rfft(y)/len(y)
    amp = 2*np.abs(c)
    amp[0] = abs(c[0])
    return amp                                          # amp[h] = amplitude of harmonic h (per electrical cycle)


def dtheta(y):
    """d y / d theta_e (rad) of a periodic waveform sampled on [0, 360) (endpoint dropped)."""
    y = np.asarray(y[:-1], float)
    n = len(y)
    k = np.fft.rfftfreq(n, d=1.0/n)
    return np.fft.irfft(1j*k*np.fft.rfft(y), n)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="band")
    a = ap.parse_args()
    F = load_fea(a.tag)
    lab = load_lab()
    s, delta = alignment(F)
    x = np.radians(F["pos"])
    th = s*x + delta
    i0 = int(np.argmin(np.abs(F["id"])))
    j0 = int(np.argmin(np.abs(F["iq"])))
    nl = {k: float(F[k][i0, j0]) for k in ("Iron_Loss_Stator", "Stator_Copper_Loss_AC", "Iron_Loss_Rotor", "Magnet_Loss")}
    lab_nl = {k: lab_at(lab, k, 0.0, 0.0) for k in ("Iron_Loss_Stator", "Stator_Copper_Loss_AC")}
    res = dict(files=F["files"], grid=dict(id=F["id"].tolist(), iq=F["iq"].tolist(), npos=len(F["pos"])),
               alignment=dict(direction=s, delta_deg=float(np.degrees(delta) % 360)), noload_fea=nl, noload_lab=lab_nl)

    # dq check: Motor-CAD psi_d/psi_q vs our Park of the phase fluxes with theta_d(x)
    jq = int(np.argmin(np.abs(F["iq"] - 13.0)))
    ii = int(np.argmin(np.abs(F["id"] + 195.0)))
    pd, pq = park(F[ANG[3]][ii, jq], F[ANG[4]][ii, jq], F[ANG[5]][ii, jq], th)
    res["park_check_max_abs_Wb"] = dict(d=float(np.max(np.abs(pd - F[ANG[0]][ii, jq]))),
                                        q=float(np.max(np.abs(pq - F[ANG[1]][ii, jq]))))

    # (a) grid-point comparison in the band
    band = []
    for i, idv in enumerate(F["id"]):
        for j, iqv in enumerate(F["iq"]):
            row = dict(id=float(idv), iq=float(iqv))
            for k in ("Flux_Linkage_D", "Flux_Linkage_Q", "Electromagnetic_Torque", "Iron_Loss_Stator",
                      "Iron_Loss_Rotor", "Magnet_Loss", "Stator_Copper_Loss_AC", "Torque_Ripple_Peak_to_Peak"):
                row[k + "_fea"] = float(F[k][i, j])
                row[k + "_lab"] = lab_at(lab, k, idv, iqv)
            band.append(row)
    res["band_points"] = band

    # operating points: torque, voltage, losses, convention, harmonics
    ops = []
    for Tref, i, q in OPS:
        r = dict(T_ref=Tref, id=i, iq=q, gamma=float(np.degrees(np.arctan2(-i, q))))
        fd, fq = scal_at(F, "Flux_Linkage_D", i, q), scal_at(F, "Flux_Linkage_Q", i, q)
        ld, lq = lab_at(lab, "Flux_Linkage_D", i, q), lab_at(lab, "Flux_Linkage_Q", i, q)
        V = lambda d, qq, R=R_DC: float(np.hypot(R*i - WE*qq, R*q + WE*d))
        r.update(psi_d_fea=fd, psi_q_fea=fq, psi_d_lab=ld, psi_q_lab=lq,
                 V_fea=V(fd, fq), V_lab=V(ld, lq), V_lab_export=lab_at(lab, "Voltage_Phase_Peak", i, q))
        L = {k: scal_at(F, k, i, q) for k in ("Iron_Loss_Stator", "Iron_Loss_Rotor", "Magnet_Loss",
                                              "Stator_Copper_Loss_AC", "Stator_Copper_Loss_DC")}
        Ll = {k: lab_at(lab, k, i, q) for k in L}
        Tem, Tem_l = scal_at(F, "Electromagnetic_Torque", i, q), lab_at(lab, "Electromagnetic_Torque", i, q)
        brake = P_MECH + L["Iron_Loss_Rotor"] + L["Magnet_Loss"] + nl["Iron_Loss_Stator"] + nl["Stator_Copper_Loss_AC"]
        brake_l = P_MECH + Ll["Iron_Loss_Rotor"] + Ll["Magnet_Loss"] + lab_nl["Iron_Loss_Stator"] + lab_nl["Stator_Copper_Loss_AC"]
        labdef = L["Iron_Loss_Stator"] + L["Iron_Loss_Rotor"] + L["Magnet_Loss"] + P_MECH
        I2 = i*i + q*q
        r.update(losses_fea=L, losses_lab=Ll, T_em_fea=Tem, T_em_lab=Tem_l,
                 T_conv_fea=Tem - brake/WM, T_conv_lab=Tem_l - brake_l/WM, T_labdef_fea=Tem - labdef/WM,
                 input_side_fea=dict(ac=L["Stator_Copper_Loss_AC"] - nl["Stator_Copper_Loss_AC"],
                                     fe=L["Iron_Loss_Stator"] - nl["Iron_Loss_Stator"]),
                 R_ac_eff_fea=(L["Stator_Copper_Loss_AC"] - nl["Stator_Copper_Loss_AC"])/(1.5*I2),
                 R_ac_eff_lab=(Ll["Stator_Copper_Loss_AC"] - lab_nl["Stator_Copper_Loss_AC"])/(1.5*I2))
        r["V_fea_Rac"] = V(fd, fq, R_DC + r["R_ac_eff_fea"])
        # sensitivity dT/dgamma at constant current (FEA mean torque vs Lab)
        I = np.hypot(i, q)
        g = np.radians(r["gamma"])
        dg = np.radians(0.25)
        Tf = [scal_at(F, "Electromagnetic_Torque", -I*np.sin(g + e), I*np.cos(g + e)) for e in (-dg, dg)]
        Tl = [lab_at(lab, "Electromagnetic_Torque", -I*np.sin(g + e), I*np.cos(g + e)) for e in (-dg, dg)]
        r["dTdg_fea"] = (Tf[1] - Tf[0])/0.5
        r["dTdg_lab"] = (Tl[1] - Tl[0])/0.5
        # waveforms (sinusoidal currents imposed by the FEA): torque ripple, harmonics, voltage peak
        Tw = at_point(F, ANG[2], i, q)
        dw, qw = at_point(F, ANG[0], i, q), at_point(F, ANG[1], i, q)
        r["T_ripple_pp_fea"] = float(np.ptp(Tw))
        r["T_ripple_pp_lab"] = lab_at(lab, "Torque_Ripple_Peak_to_Peak", i, q)
        sp = dict(psi_d=spectrum(dw), psi_q=spectrum(qw), T=spectrum(Tw))
        r["harmonics"] = {k: {int(h): float(v[h]) for h in range(1, 49) if v[h] > 0.01*max(v[1:].max(), 1e-12)}
                          for k, v in sp.items()}
        pa, pb, pc = (at_point(F, k, i, q) for k in ANG[3:])
        ia = i*np.cos(th) - q*np.sin(th)
        ib = i*np.cos(th - 2*np.pi/3) - q*np.sin(th - 2*np.pi/3)
        ic = i*np.cos(th + 2*np.pi/3) - q*np.sin(th + 2*np.pi/3)
        va = R_DC*ia[:-1] + WE*s*dtheta(pa)
        vb = R_DC*ib[:-1] + WE*s*dtheta(pb)
        vc = R_DC*ic[:-1] + WE*s*dtheta(pc)
        valpha, vbeta = va, (vb - vc)/np.sqrt(3)
        vmag = np.hypot(valpha, vbeta)
        V1 = spectrum(np.append(va, va[0]))[1]
        r.update(V1_wave=float(V1), Vpk_vector=float(vmag.max()), Vpk_phase=float(np.abs(va).max()),
                 Vpk_lineline=float(np.abs(va - vb).max()), V_excess_pct=float(100*(vmag.max()/V1 - 1)),
                 vmag_wave=vmag.tolist(), T_wave=Tw.tolist(), psi_d_wave=dw.tolist(), psi_q_wave=qw.tolist())
        ops.append(r)
    res["ops"] = ops
    json.dump(res, open(os.path.join(WORK, "posmap_%s_analysis.json" % a.tag), "w"), indent=1)

    # (d) Simscape tables
    build_tables(F, lab, s, delta, nl, lab_nl, ops)
    for r in ops:
        print("%3d N.m: psi_d %.4f/%.4f psi_q %.4f/%.4f  T_em %.2f/%.2f  T_conv %.2f/%.2f  V %.1f/%.1f (Lab export %.1f)"
              "  dT/dg %.1f/%.1f  ripple %.1f/%.1f  Vexcess %.1f%%  R_ac %.4f/%.4f"
              % (r["T_ref"], r["psi_d_fea"], r["psi_d_lab"], r["psi_q_fea"], r["psi_q_lab"], r["T_em_fea"], r["T_em_lab"],
                 r["T_conv_fea"], r["T_conv_lab"], r["V_fea"], r["V_lab"], r["V_lab_export"], r["dTdg_fea"],
                 r["dTdg_lab"], r["T_ripple_pp_fea"], r["T_ripple_pp_lab"], r["V_excess_pct"], r["R_ac_eff_fea"],
                 r["R_ac_eff_lab"]))
    print("alignment: direction %+d, delta %.1f deg; park check %s" % (s, np.degrees(delta) % 360, res["park_check_max_abs_Wb"]))


def build_tables(F, lab, s, delta, nl, lab_nl, ops):
    idg, iqg, g = lab
    neg = [-650, -585, -520, -455, -390, -377] + list(np.round(F["id"], 6))
    neg = sorted(set(float(v) for v in neg))
    ID = np.array(neg + [-v for v in reversed(neg) if v < 0])
    iq_extra = [-650, -520, -390, -260, -195, -130, -104, -78, -52, -39, -26, 65, 78, 91, 104, 130, 195, 260, 390, 520, 650]
    pos = sorted(set(abs(float(v)) for v in iq_extra + list(np.round(F["iq"], 6)) if abs(v) > 0))
    IQ = np.array([-v for v in reversed(pos)] + [0.0] + pos)       # block: iq grid must be symmetric and contain 0
    def lab_val(key, i, q):
        if i <= 0:
            return lab_at(lab, key, i, q)
        if key == "Flux_Linkage_D":                      # linear extrapolation beyond id = 0 (as build_e10_stage2c)
            d0, d1 = lab_at(lab, key, 0.0, q), lab_at(lab, key, -13.0, q)
            return d0 + (d0 - d1)*i/13.0
        return lab_at(lab, key, 0.0, q)                  # psi_q, torque, losses: hold the id = 0 value
    base = {}
    for key in ("Flux_Linkage_D", "Flux_Linkage_Q", "Electromagnetic_Torque", "Iron_Loss_Rotor", "Magnet_Loss"):
        base[key] = np.array([[lab_val(key, i, q) for q in IQ] for i in ID])
    brake_lab = P_MECH + base["Iron_Loss_Rotor"] + base["Magnet_Loss"] + lab_nl["Iron_Loss_Stator"] + lab_nl["Stator_Copper_Loss_AC"]
    Tconv_lab = base["Electromagnetic_Torque"] - brake_lab/WM
    in_band = np.zeros((len(ID), len(IQ)), bool)
    fi = {round(v, 6): k for k, v in enumerate(F["id"])}
    fj = {round(v, 6): k for k, v in enumerate(F["iq"])}
    for a_, i in enumerate(ID):
        for b_, q in enumerate(IQ):
            in_band[a_, b_] = round(i, 6) in fi and round(q, 6) in fj
    # FEA arrays on the block angle: theta_d = 0..360 elec (3 deg) -> block x = theta_d/N mech deg
    npos = len(F["pos"]) - 1
    thd = np.arange(npos + 1)*360.0/npos
    xsrc = ((thd - np.degrees(delta))/s) % 360.0                   # Motor-CAD position (elec deg) for each theta_d
    def resample(w):                                                  # periodic linear resample of one waveform
        return np.interp(xsrc, F["pos"], w, period=360.0)
    rac = {r["T_ref"]: r for r in ops}[20]
    variants = []
    for name, src, nx in (("lab_conv", "lab", 5), ("fea_avg", "avg", 5), ("fea_pos", "pos", npos + 1)):  # block needs >= 4 angles
        X = np.linspace(0.0, 90.0, nx)
        fd = np.repeat(base["Flux_Linkage_D"][:, :, None], nx, axis=2)
        fq = np.repeat(base["Flux_Linkage_Q"][:, :, None], nx, axis=2)
        T = np.repeat(Tconv_lab[:, :, None], nx, axis=2)
        if src != "lab":
            for a_, i in enumerate(ID):
                for b_, q in enumerate(IQ):
                    if not in_band[a_, b_]:
                        continue
                    ii, jj = fi[round(i, 6)], fj[round(q, 6)]
                    brake = (P_MECH + F["Iron_Loss_Rotor"][ii, jj] + F["Magnet_Loss"][ii, jj] + nl["Iron_Loss_Stator"]
                             + nl["Stator_Copper_Loss_AC"])/WM
                    wd, wq, wt = (F[k][ii, jj] for k in ANG[:3])
                    if src == "avg":
                        fd[a_, b_, :], fq[a_, b_, :] = wd[:-1].mean(), wq[:-1].mean()
                        T[a_, b_, :] = wt[:-1].mean() - brake
                    else:
                        fd[a_, b_, :], fq[a_, b_, :] = resample(wd), resample(wq)
                        T[a_, b_, :] = resample(wt) - brake
        Rs = R_DC + (rac["R_ac_eff_lab"] if src == "lab" else rac["R_ac_eff_fea"])
        variants.append(dict(name=name, id=ID, iq=IQ, x=X, fd=fd, fq=fq, f0=np.zeros_like(fd), T=T, Rs=Rs,
                             in_band_points=int(in_band.sum())))
    out = os.path.join(DRV, "stage2d_tables.mat")
    savemat(out, {"V_%s" % v["name"]: v for v in variants}, do_compression=True)
    print("-> %s (%s)" % (out, ", ".join("%s %s Rs %.4f" % (v["name"], v["fd"].shape, v["Rs"]) for v in variants)))


if __name__ == "__main__":
    main()
