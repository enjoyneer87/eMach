# -*- coding: utf-8 -*-
"""e10 Campbell 스윕 + 모드형상 추출 (단일 MAPDL 세션).

Phase A  모델: ff_e10_mesh_v2 스테이터(MAT1) ETCHG→SOLID187 + 48 pilot/RBE3/MASS21
Phase B  모달(자유-자유 LANB 40) + **모드형상 OD 표면 추출** → e10_mode_shapes.npz
Phase C  Campbell: 5 loadPoint(250~15000rpm) × 5 차수(k=2,4,6,10,12) FULL 하모닉
         → 각 점의 OD max|u_r|·ERP → e10_campbell.npz

주의(이 레포에서 확인된 함정): CDB MAT2=자석 — 새 재료는 MAT6+ / pilot 은 MASS21
필수 / 각 solve 전 선택셋 복원 / NERR 상향.
"""
from __future__ import annotations

import json
import os
import tempfile
import traceback

import numpy as np

CDB = r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2"
MF_JSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_multiforce.json"
HERE = os.path.dirname(os.path.abspath(__file__))
NPZ_MODES = os.path.join(HERE, "data", "e10_mode_shapes.npz")
NPZ_CAMP = os.path.join(HERE, "data", "e10_campbell.npz")

ORDERS = [2, 4, 6, 10, 12]
LOAD_POINTS = [0, 1, 2, 3, 4]
N_MODES = 40
FREQ_MAX = 13000.0            # k=12 @15000rpm = 12kHz 커버
R_BORE, R_OD = 0.0713, 0.0990
RT = 1.0e-3
Z_ST0, Z_ST1 = -0.2075, -0.0575
RHO0, C0 = 1.204, 343.0

LOG = os.path.join(os.environ.get("SP", tempfile.gettempdir()), "e10_campbell.txt")
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush(); print(*a, flush=True)


def load_all_forces():
    """전 loadPoint 치 힘 하모닉: {lp: (rpm, f_elec, {k: (48,2)복소})}."""
    d = json.load(open(MF_JSON, encoding="utf-8"))
    tnode = {n["nodeID"]: n for n in d["statorNodeLocations"]["statorNodes"]}
    ang = np.array([np.deg2rad(tnode[e["nodeID"]]["nodeCoord"][1])
                    for e in d["loadPointDefinition"][0]["excitationData"]["statorExcitation"]])
    out = {}
    for lp_i, lp in enumerate(d["loadPointDefinition"]):
        f_elec = lp["speedPoint"] / 60.0 * 4
        se = lp["excitationData"]["statorExcitation"]
        Fx, Fy = [], []
        for e in se:
            th = np.deg2rad(tnode[e["nodeID"]]["nodeCoord"][1])
            fr = np.asarray(e["forceRValues"]); ft = np.asarray(e["forceTValues"])
            Fx.append(np.cos(th) * fr - np.sin(th) * ft)
            Fy.append(np.sin(th) * fr + np.cos(th) * ft)
        Fx = np.array(Fx); Fy = np.array(Fy); N = Fx.shape[1]
        FXk = np.fft.fft(Fx, axis=1) / N; FYk = np.fft.fft(Fy, axis=1) / N
        hk = {k: np.stack([2 * FXk[:, k], 2 * FYk[:, k]], axis=1) for k in ORDERS}
        out[lp_i] = (lp["speedPoint"], f_elec, hk)
    return ang, out


def od_band(mapdl):
    mapdl.esel("S", "MAT", "", 1); mapdl.nsle("S")
    mapdl.nsel("R", "EXT")
    mapdl.csys(1); mapdl.nsel("R", "LOC", "X", R_OD - RT, R_OD + RT); mapdl.csys(0)
    return np.asarray(mapdl.mesh.nnum), np.asarray(mapdl.mesh.nodes)


def get_disp(mapdl):
    return np.stack([mapdl.post_processing.nodal_displacement("X"),
                     mapdl.post_processing.nodal_displacement("Y"),
                     mapdl.post_processing.nodal_displacement("Z")], axis=1)


def solve_sel(mapdl):
    mapdl.esel("S", "MAT", "", 1)
    mapdl.esel("A", "TYPE", "", 9990)
    mapdl.nsle("S")


def main():
    ang, forces = load_all_forces()
    from ansys.mapdl.core import launch_mapdl
    wd = tempfile.mkdtemp(prefix="e10cb_")
    P("launch MAPDL @", wd)
    mapdl = launch_mapdl(run_location=wd, override=True, nproc=8,
                         additional_switches="-smp", memory=32768)
    try:
        # ---- A. 모델 -------------------------------------------------------
        mapdl.clear(); mapdl.prep7()
        mapdl.cdread("DB", CDB, "cdb")
        mapdl.shpp("WARN"); mapdl.etchg("TTS"); mapdl.nerr("", 9999999)
        mapdl.mp("EX", 1, 185e9); mapdl.mp("PRXY", 1, 0.3); mapdl.mp("DENS", 1, 7650)
        mapdl.et(9990, "MASS21", "", "", 0)
        mapdl.r(9990, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12)
        mapdl.type(9990); mapdl.real(9990)
        zc = 0.5 * (Z_ST0 + Z_ST1); pitch = 360.0 / 48
        pilots = []
        for s in range(48):
            pid = 9000001 + s
            mapdl.n(pid, R_BORE * np.cos(ang[s]), R_BORE * np.sin(ang[s]), zc)
            mapdl.e(pid)
            mapdl.esel("S", "MAT", "", 1); mapdl.nsle("S"); mapdl.nsel("R", "EXT")
            mapdl.csys(1)
            mapdl.nsel("R", "LOC", "X", R_BORE - RT, R_BORE + 8e-4)
            th_deg = np.degrees(ang[s])
            mapdl.nsel("R", "LOC", "Y", th_deg - pitch / 2, th_deg + pitch / 2)
            mapdl.csys(0)
            mapdl.cm(f"TSEC{s}", "NODE")
            mapdl.rbe3(pid, "ALL", f"TSEC{s}")
            pilots.append(pid)
        P("model ready (48 pilots)")
        solve_sel(mapdl); mapdl.finish()

        # ---- B. 모달 + 모드형상 --------------------------------------------
        P("modal ...")
        mapdl.slashsolu()
        mapdl.antype("MODAL")
        mapdl.modopt("LANB", N_MODES, 0, FREQ_MAX)
        mapdl.mxpand(N_MODES)
        mapdl.solve(); mapdl.finish()
        mapdl.post1()
        nsets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
        freqs, shapes = [], []
        nn = xyz = None
        for i in range(1, nsets + 1):
            mapdl.set(1, i)
            f = float(mapdl.get_value("MODE", i, "FREQ"))
            freqs.append(f)
            if f > 1.0:                       # 탄성모드만 형상 저장
                solve_sel(mapdl)              # 선택 복원 후 OD 밴드
                nn_i, xyz_i = od_band(mapdl)
                if nn is None:
                    nn, xyz = nn_i, xyz_i
                shapes.append((f, get_disp(mapdl)))
        mapdl.finish()
        P(f"modal: {len(freqs)} sets, elastic shapes: {len(shapes)}")
        os.makedirs(os.path.dirname(NPZ_MODES), exist_ok=True)
        np.savez(NPZ_MODES,
                 freqs_all=np.array(freqs),
                 mode_freqs=np.array([s[0] for s in shapes]),
                 mode_U=np.stack([s[1] for s in shapes]),   # (M, Nod, 3) 실수
                 nnum=nn, xyz=xyz)
        P("saved", NPZ_MODES)

        # ---- C. Campbell 스윕 ----------------------------------------------
        rows = []      # (rpm, k, freq, umax, umean, erp)
        A_cyl = 2 * np.pi * R_OD * (Z_ST1 - Z_ST0)
        total = len(LOAD_POINTS) * len(ORDERS)
        done = 0
        for lp_i in LOAD_POINTS:
            rpm, f_elec, hk = forces[lp_i]
            for k in ORDERS:
                fexc = k * f_elec
                done += 1
                P(f"[{done}/{total}] lp{lp_i} {rpm:.0f}rpm k={k} f={fexc:.0f}Hz ...")
                solve_sel(mapdl)
                mapdl.slashsolu()
                mapdl.antype("HARMIC"); mapdl.hropt("FULL")
                mapdl.kbc(1); mapdl.harfrq(fexc); mapdl.nsubst(1)
                mapdl.fdele("ALL", "ALL")
                for s, pid in enumerate(pilots):
                    Fx_c, Fy_c = hk[k][s]
                    mapdl.f(pid, "FX", float(Fx_c.real), float(Fx_c.imag))
                    mapdl.f(pid, "FY", float(Fy_c.real), float(Fy_c.imag))
                mapdl.solve(); mapdl.finish()
                mapdl.post1()
                solve_sel(mapdl)
                nn_i, xyz_i = od_band(mapdl)
                mapdl.set(1, 1, "", 0); Ur = get_disp(mapdl)
                mapdl.set(1, 1, "", 1); Ui = get_disp(mapdl)
                U = Ur + 1j * Ui
                th = np.arctan2(xyz_i[:, 1], xyz_i[:, 0])
                ur = U[:, 0] * np.cos(th) + U[:, 1] * np.sin(th)
                om = 2 * np.pi * fexc
                erp = 0.5 * RHO0 * C0 * np.sum(
                    A_cyl / len(ur) * (om * np.abs(ur)) ** 2)
                rows.append((rpm, k, fexc, np.abs(ur).max(), np.abs(ur).mean(), erp))
                P(f"   max|u_r|={np.abs(ur).max()*1e6:.3f}um  "
                  f"Lw={10*np.log10(max(erp,1e-30)/1e-12):.1f}dB")
                mapdl.finish()
                # 중간 저장(크래시 대비)
                np.savez(NPZ_CAMP, rows=np.array(rows),
                         orders=np.array(ORDERS),
                         freqs_modal=np.array(freqs))
        P("saved", NPZ_CAMP)
        P("CAMPBELL-OK")
    finally:
        try: mapdl.exit()
        except Exception: pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        P("FATAL\n" + traceback.format_exc()[:3000])
    finally:
        log.close()
