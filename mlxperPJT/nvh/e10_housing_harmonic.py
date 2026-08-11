# -*- coding: utf-8 -*-
"""e10 하우징 포함 NVH — 파라메트릭 Al 원통 하우징 + MPC 본딩 + 모달/하모닉.

Chauvicourt(2018)의 교훈: 스테이터 단독 모델은 로터-하우징 커플드(RHC) 모드를
통째로 놓쳐 534Hz 고음압 피크를 예측 못했다(그의 Ch.4 동기). 여기서는 최소
확장으로 **하우징만** 추가해 (a) 모드 시프트, (b) 하우징 외면 응답/ERP 를 본다.

모델
----
- 스테이터: ff_e10_mesh_v2 MAT1 (ETCHG→SOLID187, E=185GPa 등방).
- 하우징: 내경=스테이터OD(0.198m, 억지끼움 0갭), 두께 HOUS_T(기본 8mm),
  길이=스택+양측 HOUS_OH(기본 20mm) 알루미늄 원통. CYLIND+VMESH(SOLID187).
- 결합: 스테이터 OD(CONTA174, MPC) ↔ 하우징 내면(TARGE170) bonded-always.
- 해석: 자유-자유 모달(LANB) → 지배 힘차수 k=2,6 FULL 하모닉(치 pilot+RBE3).
- 추출: 하우징 외면 복소변위(ERP용) + 스테이터 OD(비교용).

산출: data/e10_housing_result.npz
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
OUT_NPZ = os.path.join(HERE, "data", "e10_housing_result.npz")

LOAD_POINT = int(os.environ.get("MF_LOADPOINT", "4"))
ORDERS = [int(x) for x in os.environ.get("ORDERS", "2,6").split(",")]
N_MODES = 40
FREQ_MAX = 9000.0
R_BORE, R_OD = 0.0713, 0.0990
RT = 1.0e-3
Z_ST0, Z_ST1 = -0.2075, -0.0575
HOUS_T = float(os.environ.get("HOUS_T", "0.008"))    # 하우징 두께 [m]
HOUS_OH = float(os.environ.get("HOUS_OH", "0.020"))  # 축방향 오버행 [m]
R_HOUT = R_OD + HOUS_T
ESIZE_H = 0.008

LOG = os.path.join(os.environ.get("SP", tempfile.gettempdir()), "e10_housing.txt")
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush(); print(*a, flush=True)


def tooth_force_harmonics():
    d = json.load(open(MF_JSON, encoding="utf-8"))
    lp = d["loadPointDefinition"][LOAD_POINT]
    f_elec = lp["speedPoint"] / 60.0 * 4
    se = lp["excitationData"]["statorExcitation"]
    nodes = {n["nodeID"]: n for n in d["statorNodeLocations"]["statorNodes"]}
    ang, FxT, FyT = [], [], []
    for e in se:
        th = np.deg2rad(nodes[e["nodeID"]]["nodeCoord"][1])
        fr = np.asarray(e["forceRValues"]); ft = np.asarray(e["forceTValues"])
        ang.append(th)
        FxT.append(np.cos(th) * fr - np.sin(th) * ft)
        FyT.append(np.sin(th) * fr + np.cos(th) * ft)
    ang = np.array(ang); Fx = np.array(FxT); Fy = np.array(FyT)
    N = Fx.shape[1]
    FXk = np.fft.fft(Fx, axis=1) / N; FYk = np.fft.fft(Fy, axis=1) / N
    hk = {k: np.stack([2 * FXk[:, k], 2 * FYk[:, k]], axis=1) for k in range(1, N // 2)}
    return ang, hk, f_elec, lp["speedPoint"]


def extract_band(mapdl, mat, r_lo, r_hi):
    """mat 요소 외표면 ∩ 반경밴드의 (nnum, xyz, U복소)."""
    mapdl.esel("S", "MAT", "", mat); mapdl.nsle("S")
    mapdl.nsel("R", "EXT")
    mapdl.csys(1); mapdl.nsel("R", "LOC", "X", r_lo, r_hi); mapdl.csys(0)
    nn = np.asarray(mapdl.mesh.nnum)
    xyz = np.asarray(mapdl.mesh.nodes)
    mapdl.set(1, 1, "", 0)
    ur = mapdl.post_processing.nodal_displacement("X")
    vr = mapdl.post_processing.nodal_displacement("Y")
    wr = mapdl.post_processing.nodal_displacement("Z")
    mapdl.set(1, 1, "", 1)
    ui = mapdl.post_processing.nodal_displacement("X")
    vi = mapdl.post_processing.nodal_displacement("Y")
    wi = mapdl.post_processing.nodal_displacement("Z")
    U = np.stack([ur + 1j * ui, vr + 1j * vi, wr + 1j * wi], axis=1)
    return nn, xyz, U


def solve_selection(mapdl):
    """솔브 선택셋: 스테이터+하우징+접촉/타깃+MASS21."""
    mapdl.esel("S", "MAT", "", 1)
    mapdl.esel("A", "MAT", "", 2)
    mapdl.esel("A", "TYPE", "", 9990)
    mapdl.esel("A", "TYPE", "", 20)
    mapdl.esel("A", "TYPE", "", 21)
    mapdl.nsle("S")


def main():
    ang, hk, f_elec, rpm = tooth_force_harmonics()
    from ansys.mapdl.core import launch_mapdl
    wd = tempfile.mkdtemp(prefix="e10hous_")
    P("launch MAPDL @", wd)
    mapdl = launch_mapdl(run_location=wd, override=True, nproc=8,
                         additional_switches="-smp", memory=32768)
    try:
        # ---- A. 스테이터 ---------------------------------------------------
        mapdl.clear(); mapdl.prep7()
        mapdl.cdread("DB", CDB, "cdb")
        mapdl.shpp("WARN")
        mapdl.etchg("TTS")
        mapdl.nerr("", 9999999)
        mapdl.mp("EX", 1, 185e9); mapdl.mp("PRXY", 1, 0.3); mapdl.mp("DENS", 1, 7650)
        P("stator ready:", mapdl.mesh.n_node, "nodes")

        # ---- B. 하우징 볼륨 + 메시 ----------------------------------------
        mapdl.mp("EX", 2, 70e9); mapdl.mp("PRXY", 2, 0.33); mapdl.mp("DENS", 2, 2700)
        etmax = 30
        mapdl.et(etmax, "SOLID187")
        mapdl.type(etmax); mapdl.mat(2)
        mapdl.csys(0)
        mapdl.cylind(R_OD, R_HOUT, Z_ST0 - HOUS_OH, Z_ST1 + HOUS_OH)
        mapdl.esize(ESIZE_H)
        mapdl.vmesh("ALL")                  # 유일 볼륨(방금 만든 원통)
        mapdl.esel("S", "MAT", "", 2)
        P("housing meshed:", mapdl.mesh.n_elem, "elems")

        # ---- C. MPC 본딩 접촉 (스테이터OD ↔ 하우징내면) --------------------
        mapdl.et(20, "TARGE170")
        mapdl.et(21, "CONTA174")
        mapdl.keyopt(21, 2, 2)     # MPC
        mapdl.keyopt(21, 12, 5)    # bonded always
        mapdl.r(20)
        # 타깃 = 하우징 내면
        mapdl.esel("S", "MAT", "", 2); mapdl.nsle("S")
        mapdl.nsel("R", "EXT")
        mapdl.csys(1); mapdl.nsel("R", "LOC", "X", R_OD - RT, R_OD + RT); mapdl.csys(0)
        mapdl.type(20); mapdl.real(20); mapdl.mat(2)
        mapdl.esurf()
        nt = mapdl.mesh.n_elem
        # 접촉 = 스테이터 OD
        mapdl.esel("S", "MAT", "", 1); mapdl.nsle("S")
        mapdl.nsel("R", "EXT")
        mapdl.csys(1); mapdl.nsel("R", "LOC", "X", R_OD - RT, R_OD + RT); mapdl.csys(0)
        mapdl.type(21); mapdl.real(20); mapdl.mat(1)
        mapdl.esurf()
        mapdl.allsel()
        P("contact pair created")

        # ---- D. 치별 pilot + RBE3 (보어) ----------------------------------
        mapdl.et(9990, "MASS21", "", "", 0)
        mapdl.r(9990, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12)
        mapdl.type(9990); mapdl.real(9990)
        zc = 0.5 * (Z_ST0 + Z_ST1); pitch = 360.0 / 48
        pilots = []
        for s in range(48):
            th_deg = np.degrees(ang[s]); pid = 9000001 + s
            mapdl.n(pid, R_BORE * np.cos(ang[s]), R_BORE * np.sin(ang[s]), zc)
            mapdl.e(pid)
            mapdl.esel("S", "MAT", "", 1); mapdl.nsle("S")
            mapdl.nsel("R", "EXT")
            mapdl.csys(1)
            mapdl.nsel("R", "LOC", "X", R_BORE - RT, R_BORE + 8e-4)
            mapdl.nsel("R", "LOC", "Y", th_deg - pitch / 2, th_deg + pitch / 2)
            mapdl.csys(0)
            mapdl.cm(f"TSEC{s}", "NODE")
            mapdl.rbe3(pid, "ALL", f"TSEC{s}")
            pilots.append(pid)
        P("48 pilots+RBE3 done")
        solve_selection(mapdl)
        P("solve set:", mapdl.mesh.n_elem, "elems /", mapdl.mesh.n_node, "nodes")
        mapdl.finish()

        # ---- E. 모달 -------------------------------------------------------
        P("modal (stator+housing) ...")
        mapdl.slashsolu()
        mapdl.antype("MODAL")
        mapdl.modopt("LANB", N_MODES, 0, FREQ_MAX)
        mapdl.mxpand(N_MODES)
        mapdl.solve(); mapdl.finish()
        mapdl.post1()
        nsets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
        freqs = []
        for i in range(1, nsets + 1):
            mapdl.set(1, i)
            freqs.append(float(mapdl.get_value("MODE", i, "FREQ")))
        mapdl.finish()
        P(f"modal done: elastic(>1Hz):", [round(f, 1) for f in freqs if f > 1][:20])

        # ---- F. 하모닉 ------------------------------------------------------
        results = {}
        for k in ORDERS:
            fexc = k * f_elec
            P(f"harmonic k={k} f={fexc:.1f} Hz ...")
            solve_selection(mapdl)
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
            hn, hxyz, hU = extract_band(mapdl, 2, R_HOUT - RT, R_HOUT + RT)  # 하우징 외면
            sn, sxyz, sU = extract_band(mapdl, 1, R_OD - RT, R_OD + RT)      # 스테이터 OD
            results[k] = dict(freq=fexc, h_xyz=hxyz, h_U=hU, s_xyz=sxyz, s_U=sU)
            P(f"  k={k}: housing outer max|Uxy|={np.abs(hU[:,:2]).max():.3e} m "
              f"(nodes {len(hn)}) / statorOD max={np.abs(sU[:,:2]).max():.3e}")
            mapdl.finish()

        # ---- 저장 ----------------------------------------------------------
        save = {"freqs_modal": np.array(freqs), "orders": np.array(ORDERS),
                "f_elec": f_elec, "rpm": rpm,
                "R_hout": R_HOUT, "hous_t": HOUS_T, "hous_oh": HOUS_OH}
        for k, r in results.items():
            for key in ("h_xyz", "h_U", "s_xyz", "s_U"):
                save[f"k{k}_{key}"] = r[key]
            save[f"k{k}_freq"] = r["freq"]
        np.savez(OUT_NPZ, **save)
        P("saved", OUT_NPZ)
        P("HOUSING-OK")
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
