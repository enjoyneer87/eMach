# -*- coding: utf-8 -*-
"""How much voltage do the slot harmonics take from the current regulator? — the Simscape stage 2d runs
seen through the quasi-static solver.

The residual check (fea_posmap_analyze / 2d) showed that the mean torque of the harmonic runs (variant D,
position-resolved FEA map) equals the mean-map torque at the realized mean (I, gamma). So D differs from
C only by where the regulator ends up, and where it ends up is set by the voltage it has left for the
fundamental. That remainder is read off directly:

  m_eq = 1 - V_ss(realized mean point) / V_clamp       V_ss with the mean FEA map, R_dc + R_ac, deadtime term

For C (no harmonics) m_eq is the unused table margin (or ~0 when saturated). For D it is the margin the
harmonic currents took, through the regulator (PI proportional path and decoupling). If m_eq is a property
of the machine + regulator at a torque level rather than of the table, then the quasi-static solver with
V_eff = V_clamp (1 - m_h) predicts the harmonic runs of another table. Check: calibrate m_h on MBC 95 %,
predict MCB and MBC 90 %.

python qs_harmonic_margin.py   ->  fea_pos\\qs_harmonic_margin.json
"""
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qs_opsolver as QS  # noqa: E402
import fea_posmap_analyze as FA  # noqa: E402

DRV = r"D:\KangDH\Thesis\e10\work_lab_pc1\drive"


def load_rows():
    rows = []
    for fn in ("stage2d_results.csv", "stage2d_results_mbc90.csv"):
        rows += list(csv.DictReader(open(os.path.join(DRV, fn))))
    return rows


def refs():
    out = {}
    for r in csv.DictReader(open(os.path.join(DRV, "stage2b_results.csv"))):
        if float(r["td_us"]) == 0 and float(r["dt_comp"]) == 0:
            out[(r["table"], float(r["T_ref"]))] = (float(r["id_ref"]), float(r["iq_ref"]))
    return out


def margin_cost(M):
    """16 krpm losses of the QS table points (drive\\qs_tables.mat) at each margin: what a margin costs."""
    from scipy.io import loadmat
    Q = loadmat(os.path.join(DRV, "qs_tables.mat"), squeeze_me=True, struct_as_record=False)
    out = []
    for name in sorted((k for k in Q if k.startswith("QS")), key=lambda k: -int(k[2:])):
        q = Q[name]
        for T, i, iq in zip(np.atleast_1d(q.Tv), np.atleast_1d(q.idRef), np.atleast_1d(q.iqRef)):
            v = {k: float(M.vals(k, i, iq)) for k in QS.KEYS}
            I = float(np.hypot(i, iq))
            parts = dict(P_cu_dc=1.5*FA.R_DC*I*I, P_cu_ac=v["Stator_Copper_Loss_AC"], P_fe_s=v["Iron_Loss_Stator"],
                         P_fe_r=v["Iron_Loss_Rotor"], P_mag=v["Magnet_Loss"], P_mech=FA.P_MECH)
            out.append(dict(table=name, margin=100 - int(name[2:]), T=float(T), id=float(i), iq=float(iq),
                            I_rms=I/np.sqrt(2), gamma=float(np.degrees(np.arctan2(-i, iq))), P_loss=sum(parts.values()),
                            **parts))
    json.dump(out, open(os.path.join(FA.WORK, "qs_margin_cost.json"), "w"), indent=1)
    return out


def main():
    M = QS.Maps("fea", rac=True)
    margin_cost(M)
    R = refs()
    rows = [r for r in load_rows() if r["variant"] in ("fea_avg", "fea_pos", "fea_pos_ff")]
    res = []
    for r in rows:
        T, td = float(r["T_ref"]), float(r["td_us"])*1e-6
        I, g = np.sqrt(2)*float(r["I_rms"]), np.radians(float(r["gamma"]))
        p = M.point(-I*np.sin(g), I*np.cos(g), td)
        i0, q0 = R[(r["table"], T)]
        pr = M.point(i0, q0, td)
        res.append(dict(variant=r["variant"], table=r["table"], T_ref=T, td_us=td*1e6, T_sim=float(r["T"]),
                        gamma_sim=float(r["gamma"]), sat=float(r["sat_pct"]), T_map=p["T_shaft"], V_ss=p["V"],
                        m_eq=1 - p["V"]/QS.VCTRL, gamma_ref=float(np.degrees(np.arctan2(-i0, q0))),
                        m_table=1 - pr["V"]/QS.VCTRL))
    # calibrate on MBC 95, predict the other tables
    for x in res:
        cal = [y for y in res if y["variant"] == x["variant"] and y["table"] == "MBC 95" and y["T_ref"] == x["T_ref"]
               and y["td_us"] == x["td_us"]]
        if not cal or x["variant"] == "fea_avg":
            continue
        mh = max(cal[0]["m_eq"], 0.0)
        i0, q0 = R[(x["table"], x["T_ref"])]
        h = QS.held_point(M, i0, q0, QS.VCTRL*(1 - mh), x["td_us"]*1e-6)
        x.update(m_h_cal=mh, gamma_pred=h["gamma"], T_pred=h["T_shaft"])
    print("%-11s %-7s %4s %3s | %8s %8s %6s | %7s %7s %6s | %7s %7s" % (
        "variant", "table", "T*", "td", "T_sim", "T_map", "sat%", "g_ref", "g_sim", "m_eq%", "g_pred", "T_pred"))
    for x in sorted(res, key=lambda x: (x["variant"], x["td_us"], x["T_ref"], x["table"])):
        print("%-11s %-7s %4g %3g | %8.2f %8.2f %6.1f | %7.2f %7.2f %6.1f | %7s %7s" % (
            x["variant"], x["table"], x["T_ref"], x["td_us"], x["T_sim"], x["T_map"], x["sat"], x["gamma_ref"],
            x["gamma_sim"], 100*x["m_eq"], "%.2f" % x["gamma_pred"] if "gamma_pred" in x else "-",
            "%.2f" % x["T_pred"] if "T_pred" in x else "-"))
    json.dump(res, open(os.path.join(FA.WORK, "qs_harmonic_margin.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
