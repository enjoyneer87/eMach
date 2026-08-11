# -*- coding: utf-8 -*-
"""e10 스테이터 NVH 하모닉 응답 — 원격힘(치별 pilot+RBE3) 실전 투입.

체인: Motor-CAD 멀티포스(15000rpm, loadPoint4) → 치 힘 FFT(온도차수) →
      MAPDL 스테이터 구조모델(열메시 ETCHG 전환) + 48 pilot/RBE3 →
      모달(자유-자유, LANB) → 상위 힘차수에서 FULL 하모닉 → OD 응답 추출.

산출: data/e10_harmonic_result.npz (모달 주파수, 차수별 OD 변위장) + 로그.
시각화는 별도 스크립트(e10_harmonic_viz.py)에서.

주의
----
- 메시는 열해석용(ff_e10_mesh_v2.cdb, SOLID87) → **ETCHG,TTS** 로 SOLID187 전환.
- 스테이터(MAT1)만 선택 해석(타 바디는 비연결이라 자유모드 오염). Chauvicourt(2018)
  도 스테이터 코어 단독 + 자유-자유로 검증(고유진동수 ±10% 허용).
- 재료: 적층 유효 등방 E=185GPa, ν=0.3, ρ=7650 (1차 근사 — 이방성 미반영).
- pilot 은 MASS21(6DOF) 부착(안 붙이면 RBE3 마스터 DOF 소거로 solve 실패).
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
OUT_NPZ = os.path.join(HERE, "data", "e10_harmonic_result.npz")

LOAD_POINT = int(os.environ.get("MF_LOADPOINT", "4"))   # 15000rpm
N_MODES = 40
FREQ_MAX = 9000.0
N_ORDERS = 3                    # 상위 힘 온도차수 몇 개를 해석할지
R_BORE = 0.0713
R_OD = 0.0990
RT = 1.0e-3
Z_ST0, Z_ST1 = -0.2075, -0.0575

LOG = os.path.join(os.environ.get("SP", tempfile.gettempdir()), "e10_harmonic.txt")
log = open(LOG, "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush(); print(*a, flush=True)


# ---------------------------------------------------------------- 힘 하모닉
def tooth_force_harmonics():
    """멀티포스 JSON → 치별 복소 힘 하모닉. 반환 (angles(48,), Fk[k] = (48,2)복소, f_elec)."""
    d = json.load(open(MF_JSON, encoding="utf-8"))
    lp = d["loadPointDefinition"][LOAD_POINT]
    f_elec = lp["speedPoint"] / 60.0 * 4          # 8극
    se = lp["excitationData"]["statorExcitation"]
    nodes = {n["nodeID"]: n for n in d["statorNodeLocations"]["statorNodes"]}
    ang, FxT, FyT = [], [], []
    for e in se:
        th = np.deg2rad(nodes[e["nodeID"]]["nodeCoord"][1])
        fr = np.asarray(e["forceRValues"]); ft = np.asarray(e["forceTValues"])
        ang.append(th)
        FxT.append(np.cos(th) * fr - np.sin(th) * ft)
        FyT.append(np.sin(th) * fr + np.cos(th) * ft)
    ang = np.array(ang)
    Fx = np.array(FxT); Fy = np.array(FyT)        # (48, 128)
    N = Fx.shape[1]
    # 복소 하모닉 (물리 진폭 규약: f(t) = Re[ F_k e^{i k ω t} ], k>=1 은 2/N 배)
    FXk = np.fft.fft(Fx, axis=1) / N
    FYk = np.fft.fft(Fy, axis=1) / N
    hk = {}
    for k in range(1, N // 2):
        hk[k] = np.stack([2 * FXk[:, k], 2 * FYk[:, k]], axis=1)   # (48,2) complex
    # 차수별 세기
    strength = {k: float(np.abs(v).sum()) for k, v in hk.items()}
    top = sorted(strength, key=strength.get, reverse=True)[:N_ORDERS]
    P("force temporal orders (top10):",
      {k: round(strength[k], 1) for k in sorted(strength, key=strength.get, reverse=True)[:10]})
    P("selected orders:", top, " f_elec=", f_elec, "Hz → freqs=",
      [round(k * f_elec, 1) for k in top])
    return ang, hk, f_elec, top, lp["speedPoint"]


# ---------------------------------------------------------------- MAPDL
def main():
    ang, hk, f_elec, orders, rpm = tooth_force_harmonics()

    from ansys.mapdl.core import launch_mapdl
    wd = tempfile.mkdtemp(prefix="e10harm_")
    P("launch MAPDL @", wd)
    mapdl = launch_mapdl(run_location=wd, override=True, nproc=8,
                         additional_switches="-smp", memory=32768)
    try:
        # ---- A. 모델 준비 -------------------------------------------------
        mapdl.clear(); mapdl.prep7()
        mapdl.cdread("DB", CDB, "cdb")
        P("cdread ok:", mapdl.mesh.n_node, "nodes /", mapdl.mesh.n_elem, "elems")
        # 형상검사 → 경고로(737k 중 3개 sliver tet 가 에러한계 위반, 무시 가능)
        mapdl.shpp("WARN")
        mapdl.etchg("TTS")                       # 열 → 구조 (SOLID87→SOLID187)
        P("ETCHG TTS done")
        mapdl.mp("EX", 1, 185e9); mapdl.mp("PRXY", 1, 0.3); mapdl.mp("DENS", 1, 7650)

        # 스테이터만
        mapdl.esel("S", "MAT", "", 1)
        mapdl.nsle("S")
        P("stator sel:", mapdl.mesh.n_elem, "elems /", mapdl.mesh.n_node, "nodes")

        # pilot 더미질량 정의
        mapdl.et(9990, "MASS21", "", "", 0)
        mapdl.r(9990, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12)
        mapdl.type(9990); mapdl.real(9990)

        # 치별 pilot + RBE3 (보어 외표면 절점을 각도 섹터로)
        zc = 0.5 * (Z_ST0 + Z_ST1)
        pitch = 360.0 / 48
        pilots = []
        for s in range(48):
            th_deg = np.degrees(ang[s])
            pid = 9000001 + s
            px, py = R_BORE * np.cos(ang[s]), R_BORE * np.sin(ang[s])
            mapdl.n(pid, px, py, zc)
            mapdl.e(pid)                          # MASS21 부착(DOF)
            # 섹터 절점 선택: mat1 요소 외표면 ∩ 보어반경밴드 ∩ 각도밴드
            mapdl.esel("S", "MAT", "", 1); mapdl.nsle("S")
            mapdl.nsel("R", "EXT")
            mapdl.csys(1)
            mapdl.nsel("R", "LOC", "X", R_BORE - RT, R_BORE + 8e-4)
            lo, hi = th_deg - pitch / 2, th_deg + pitch / 2
            mapdl.nsel("R", "LOC", "Y", lo, hi)
            nsec = mapdl.mesh.n_node
            mapdl.csys(0)
            cname = f"TSEC{s}"
            mapdl.cm(cname, "NODE")
            mapdl.rbe3(pid, "ALL", cname)
            pilots.append(pid)
            if s % 12 == 0:
                P(f"  tooth {s}: pilot {pid} slaves={nsec}")
        mapdl.allsel()
        # 해석 선택: 스테이터 + MASS21
        mapdl.esel("S", "MAT", "", 1)
        mapdl.esel("A", "TYPE", "", 9990)
        mapdl.nsle("S")
        P("solve set:", mapdl.mesh.n_elem, "elems /", mapdl.mesh.n_node, "nodes")
        mapdl.finish()

        # ---- B. 모달 (자유-자유) ------------------------------------------
        P("modal solve ...")
        mapdl.slashsolu()
        mapdl.antype("MODAL")
        mapdl.modopt("LANB", N_MODES, 0, FREQ_MAX)
        mapdl.mxpand(N_MODES)
        out = mapdl.solve()
        mapdl.finish()
        freqs = []
        mapdl.post1()
        nsets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
        for i in range(1, nsets + 1):
            mapdl.set(1, i)
            freqs.append(float(mapdl.get_value("MODE", i, "FREQ")))
        mapdl.finish()
        P(f"modal done: {len(freqs)} modes; elastic modes(>1Hz):",
          [round(f, 1) for f in freqs if f > 1][:20])

        # ---- C. FULL 하모닉 (상위 차수별) ---------------------------------
        results = {}
        mapdl.nerr("", 9999999)          # 경고 1만건 초과로 런 종료되는 것 방지
        for k in orders:
            fexc = k * f_elec
            P(f"harmonic k={k} f={fexc:.1f} Hz ...")
            # ⚠️ 직전 후처리가 OD 절점만 남겨두므로 솔브 선택셋을 반드시 복원
            #    (안 하면 '요소의 절점 미선택' 경고 폭주 → NERR 한도로 런 종료)
            mapdl.esel("S", "MAT", "", 1)
            mapdl.esel("A", "TYPE", "", 9990)
            mapdl.nsle("S")
            mapdl.slashsolu()
            mapdl.antype("HARMIC")
            mapdl.hropt("FULL")
            mapdl.kbc(1)
            mapdl.harfrq(fexc)
            mapdl.nsubst(1)
            mapdl.fdele("ALL", "ALL")
            for s, pid in enumerate(pilots):
                Fx_c, Fy_c = hk[k][s]
                mapdl.f(pid, "FX", float(Fx_c.real), float(Fx_c.imag))
                mapdl.f(pid, "FY", float(Fy_c.real), float(Fy_c.imag))
            mapdl.solve()
            mapdl.finish()

            # OD 외표면 응답 추출 (실부+허부)
            mapdl.post1()
            mapdl.esel("S", "MAT", "", 1); mapdl.nsle("S")
            mapdl.nsel("R", "EXT")
            mapdl.csys(1)
            mapdl.nsel("R", "LOC", "X", R_OD - RT, R_OD + RT)
            mapdl.csys(0)
            nn = np.asarray(mapdl.mesh.nnum)
            xyz = np.asarray(mapdl.mesh.nodes)
            mapdl.set(1, 1, "", 0)               # 실부
            ur = mapdl.post_processing.nodal_displacement("X")
            vr = mapdl.post_processing.nodal_displacement("Y")
            wr = mapdl.post_processing.nodal_displacement("Z")
            mapdl.set(1, 1, "", 1)               # 허부
            ui = mapdl.post_processing.nodal_displacement("X")
            vi = mapdl.post_processing.nodal_displacement("Y")
            wi = mapdl.post_processing.nodal_displacement("Z")
            U = np.stack([ur + 1j * ui, vr + 1j * vi, wr + 1j * wi], axis=1)  # (M,3) complex
            results[k] = dict(freq=fexc, nnum=nn, xyz=xyz, U=U)
            amp = np.abs(U[:, :2]).max()
            P(f"  k={k}: OD nodes={len(nn)}, max|Uxy|={amp:.3e} m")
            mapdl.finish()

        # ---- 저장 ---------------------------------------------------------
        os.makedirs(os.path.dirname(OUT_NPZ), exist_ok=True)
        save = {"freqs_modal": np.array(freqs), "orders": np.array(orders),
                "f_elec": f_elec, "rpm": rpm}
        for k, r in results.items():
            save[f"k{k}_freq"] = r["freq"]
            save[f"k{k}_nnum"] = r["nnum"]
            save[f"k{k}_xyz"] = r["xyz"]
            save[f"k{k}_U"] = r["U"]
        np.savez(OUT_NPZ, **save)
        P("saved", OUT_NPZ)
        P("HARMONIC-OK")
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
