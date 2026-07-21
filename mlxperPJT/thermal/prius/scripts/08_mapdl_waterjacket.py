# -*- coding: utf-8 -*-
"""실형상(권선 포함) 360° CDB + JAC279 열등가회로 - end-to-end + 시각화."""
import os
import math
import csv
import time
import traceback

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
OUT = os.path.join(SP, "viz_prius_wj")
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(SP, "run_prius_wj.txt"), "w", encoding="utf-8")
def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

try:
    # ── 기하/재료/회로 파라미터 (실측) ───────────────────────────────────
    # Prius 실측 (prius_motor_mesh.cdb 에서 추출) - OD269 / 스택83.8
    R_SHAFT, R_ROT_OUT = 0.0553, 0.0802
    R_STA_IN, R_STA_OUT = 0.0809, 0.1346
    STACK, ROT_STACK = 0.0838, 0.0838
    R_COIL_IN, R_COIL_OUT = 0.0809, 0.1155
    Z_SHAFT_END = 0.150
    M_CS, M_MG, M_CO, M_SH, M_CR = 1, 2, 3, 4, 5
    K_CORE, CP_CORE, RHO_CORE = 23.0, 460.0, 7650.0
    K_MAG, CP_MAG, RHO_MAG = 9.0, 460.0, 7500.0
    # 권선 직교이방성 (2023 Ansys "Anisotropic Thermal Conductivity for
    # Coil-Windings"): 슬롯 소선은 축(z)방향 -> 축 k 高(구리 지배),
    # 횡 k 低(절연/함침 지배). 코일엔드는 잘라내 회로화했으므로 소선이
    # 전부 글로벌 z -> ESYS 회전 불요, SOLID87 KXX/KYY/KZZ 직접 사용.
    K_COIL_TRANS = 2.5      # 횡(x,y) [W/mK]  (논문 권장값)
    K_COIL_AXIAL = 250.0    # 축(z)  [W/mK]  (논문값; fill 0.45 스케일시 ~180)
    CP_COIL, RHO_COIL = 380.0, 8960.0 * 0.45
    K_SHAFT, CP_SHAFT, RHO_SHAFT = 52.0, 460.0, 7870.0
    # ── 워터재킷 냉각 + 손실밀도(W/m3) 모드 ─────────────────────────────
    # LOAD='low' : Fluent 매핑 손실 -> 기존 Fluent 결과와 비교
    # LOAD='high': 250A 고부하 손실 -> 250A Fluent(신규)와 비교
    LOAD = os.environ.get("PRIUS_LOAD", "low")
    Q_LOW = dict(stator=188657.0, rotor=74731.0, magnet=83655.0, coil=2.0e6)
    Q_HIGH = dict(stator=265900.0, rotor=93400.0, magnet=171200.0, coil=3223000.0)
    QD = Q_LOW if LOAD == "low" else Q_HIGH
    F_END = 0.449
    COOLANT_T = 27.0
    HTC_JACKET = 3000.0
    T_INIT, HTC_AIR, HTC_ATF, HTC_BIG = 70.0, 10.0, 300.0, 10000.0
    TC_AIR = 0.03
    H_CONTACT = TC_AIR / 10e-6
    TCC_SLOT = 2000.0        # 슬롯 라이너 열접촉 (JAC279: 절연 0.076mm)
    C_SHAFT_V, R_SHAFT_TH = 3771.231, 5.3759
    C_HOUSING, R_HOUS_AMB, R_HOUS_AXIAL = 12759.55, 0.3430063, 2.294125
    WJ_V, WJ_W, WJ_H, WJ_NT, WJ_R = 4.0, 0.010, 0.007, 3, 0.111
    RHO_W, MU_W, K_W, CP_W = 978.0, 4.04e-4, 0.662, 4190.0
    DH = 2 * WJ_W * WJ_H / (WJ_W + WJ_H)
    RE = RHO_W * WJ_V * DH / MU_W
    PR = MU_W * CP_W / K_W
    HTC_WJ = 0.023 * RE**0.8 * PR**0.4 * K_W / DH
    G_WJ = HTC_WJ * WJ_NT * 2 * (WJ_W + WJ_H) * (math.pi / 2 * WJ_R)
    T_END, DT = 900.0, 45.0
    TOL = 1e-5
    RT_OD = 6e-4             # 곡면 선택 반경 허용오차 (메시 8mm 기준 sagitta)
    TH_WJ = [(45.0, 135.0)]
    TH_ATF = [(-135.0, -45.0)]
    TH_REST = [(-45.0, 45.0), (135.0, 180.0), (-180.0, -135.0)]

    from ansys.mapdl.core import launch_mapdl
    mapdl = None
    mapdl = launch_mapdl(run_location=os.path.join(SP, f"real_{os.getpid()}"),
                         override=True, loglevel="ERROR")
    P("launched", mapdl.version)
    mapdl.clear(); mapdl.prep7(); mapdl.units("SI")

    # ── 메시 임포트 ──────────────────────────────────────────────────────
    mapdl.cdread("DB", r"D:\KDH\simVary\Ansys_Thermal\prius_motor_mesh", "cdb")
    P("mesh:", mapdl.mesh.n_node, mapdl.mesh.n_elem)

    # 요소타입/재료 (CDB 의 ET,1,87 유지)
    mapdl.et(2, "SURF152"); mapdl.keyopt(2, 5, 1); mapdl.keyopt(2, 8, 2)
    mapdl.et(3, "COMBIN14"); mapdl.keyopt(3, 2, 8)
    mapdl.et(4, "MASS71"); mapdl.keyopt(4, 3, 1)
    for n, k, c, r in ((M_CS, K_CORE, CP_CORE, RHO_CORE),
                       (M_MG, K_MAG, CP_MAG, RHO_MAG),
                       (M_SH, K_SHAFT, CP_SHAFT, RHO_SHAFT),
                       (M_CR, K_CORE, CP_CORE, RHO_CORE)):
        mapdl.mp("KXX", n, k); mapdl.mp("C", n, c); mapdl.mp("DENS", n, r)
    # 코일: 직교이방성 (KZZ=축=구리 지배, KXX=KYY=횡=절연 지배)
    mapdl.mp("KXX", M_CO, K_COIL_TRANS); mapdl.mp("KYY", M_CO, K_COIL_TRANS)
    mapdl.mp("KZZ", M_CO, K_COIL_AXIAL)
    mapdl.mp("C", M_CO, CP_COIL); mapdl.mp("DENS", M_CO, RHO_COIL)
    P(f"coil orthotropic: k_trans={K_COIL_TRANS} k_axial={K_COIL_AXIAL} W/mK")

    # ── 열등가회로 (링 러너와 동일 구조) ─────────────────────────────────
    nmax = int(mapdl.get_value("NODE", 0, "NUM", "MAXD"))
    def net_node(i):
        n = nmax + i; mapdl.csys(0); mapdl.n(n, 0.5 + 0.02 * i, 0, 0); return n
    N = {nm: net_node(i + 1) for i, nm in enumerate(
        ["COOL", "AIR", "SHF", "GAP_S", "GAP_R", "CEND"])}
    _rid = [100]
    def add_C(node, c):
        _rid[0] += 1; mapdl.type(4); mapdl.real(_rid[0])
        mapdl.r(_rid[0], c); mapdl.e(node)
    def add_R(n1, n2, g):
        _rid[0] += 1; mapdl.type(3); mapdl.real(_rid[0])
        mapdl.r(_rid[0], g); mapdl.e(n1, n2)
    add_C(N["SHF"], C_SHAFT_V); add_C(N["AIR"], 10.0); add_C(N["CEND"], 50.0)
    A_GAP = 2 * math.pi * ((R_ROT_OUT + R_STA_IN) / 2) * STACK
    edges = [
        ("GAP_S", "GAP_R", TC_AIR * A_GAP / 0.00075),
        ("SHF", "AIR", 1 / R_SHAFT_TH),
        ("AIR", "COOL", HTC_AIR * 2 * math.pi * R_STA_OUT * 0.4),
        ("SHF", "COOL", 1 / (R_SHAFT_TH * 3)),
        ("CEND", "AIR", 5.0),
        ("CEND", "COOL", 8.0),
    ]
    for a, b, g in edges:
        add_R(N[a], N[b], g)
    mapdl.d(N["COOL"], "TEMP", COOLANT_T)
    P(f"water-jacket circuit (LOAD={LOAD} coolant={COOLANT_T}C HTC={HTC_JACKET})")

    # ── SURF152 경계 ─────────────────────────────────────────────────────
    mapdl.r(1)
    def make_surf(fn, xnode, htc, name=""):
        mapdl.allsel(); fn()
        nsel = mapdl.mesh.n_node
        if nsel == 0:
            P(f"  [warn] {name}: empty"); return
        e0 = int(mapdl.get_value("ELEM", 0, "NUM", "MAXD"))
        mapdl.esln("S", 0); mapdl.esel("R", "TYPE", "", 1)
        mapdl.nsel("A", "NODE", "", xnode)
        mapdl.type(2); mapdl.real(1)
        mapdl.esurf(xnode)
        e1 = int(mapdl.get_value("ELEM", 0, "NUM", "MAXD"))
        if e1 <= e0:
            P(f"  [warn] {name}: {nsel} nodes no SURF"); mapdl.allsel(); return
        mapdl.esel("S", "ELEM", "", e0 + 1, e1)
        mapdl.sfe("ALL", 1, "CONV", "", htc); mapdl.allsel()
        P(f"  [surf] {name}: {e1-e0} elems ({nsel} nodes)")
    def sel_cyl(radius=None, th_ranges=None, z_range=None, mat=None, rt=None):
        def _fn():
            mapdl.csys(0)
            if mat is not None:
                mapdl.esel("S", "MAT", "", mat); mapdl.nsle("S")
            else:
                mapdl.allsel()
            mapdl.csys(1); mapdl.seltol(TOL)
            rtol = rt if rt else RT_OD
            first = True
            for (a, b) in (th_ranges or [(-180.0, 180.0)]):
                key = "S" if first else "A"
                sel = "R" if mat is not None and first else key
                if first:
                    if radius is not None:
                        mapdl.nsel("R" if mat is not None else "S",
                                   "LOC", "X", radius - rtol, radius + rtol)
                        mapdl.nsel("R", "LOC", "Y", a, b)
                    else:
                        mapdl.nsel("R" if mat is not None else "S",
                                   "LOC", "Y", a, b)
                    if z_range is not None:
                        mapdl.nsel("R", "LOC", "Z",
                                   z_range[0] - TOL, z_range[1] + TOL)
                    mapdl.cm("_TSEL", "NODE")
                    first = False
                else:
                    mapdl.allsel()
                    if mat is not None:
                        mapdl.esel("S", "MAT", "", mat); mapdl.nsle("S")
                    mapdl.csys(1)
                    if radius is not None:
                        mapdl.nsel("R" if mat is not None else "S",
                                   "LOC", "X", radius - rtol, radius + rtol)
                        mapdl.nsel("R", "LOC", "Y", a, b)
                    else:
                        mapdl.nsel("R" if mat is not None else "S",
                                   "LOC", "Y", a, b)
                    if z_range is not None:
                        mapdl.nsel("R", "LOC", "Z",
                                   z_range[0] - TOL, z_range[1] + TOL)
                    mapdl.cmsel("A", "_TSEL"); mapdl.cm("_TSEL", "NODE")
            mapdl.cmsel("S", "_TSEL"); mapdl.seltol(0)
        return _fn
    # 스테이터 외경 3분할
    make_surf(sel_cyl(R_STA_OUT, mat=M_CS), N["COOL"], HTC_JACKET, "statorOD-jacket")
    # 공극 양면
    make_surf(sel_cyl(R_STA_IN, mat=M_CS), N["GAP_S"], HTC_BIG, "gap-stator")
    make_surf(sel_cyl(R_ROT_OUT, mat=M_CR), N["GAP_R"], HTC_BIG, "gap-rotor")
    # 샤프트 돌출부 -> SHF (베어링/하우징 경로)
    def sel_shaft_ext():
        mapdl.allsel()
        mapdl.esel("S", "MAT", "", M_SH); mapdl.nsle("S")
        mapdl.csys(1); mapdl.seltol(TOL)
        mapdl.nsel("U", "LOC", "Z", -ROT_STACK / 2 + 1e-4, ROT_STACK / 2 - 1e-4)
        mapdl.seltol(0)
    make_surf(sel_shaft_ext, N["SHF"], HTC_BIG, "shaft-ext")
    # 로터 축방향 단면 -> AIR
    for z in (-ROT_STACK / 2, ROT_STACK / 2):
        make_surf(sel_cyl(z_range=(z, z), mat=M_CR), N["AIR"], HTC_AIR,
                  f"rotor-end z={z:+.3f}")
    # 코일 z단면(절단면) -> 코일엔드 lumped 노드 (구리 전도 등가 h)
    H_CU_END = K_COIL_AXIAL / 0.055   # 축방향 k / 엔드경로 ~55mm (이방성 일관)
    def sel_coilcut(th_ranges):
        def _fn():
            mapdl.allsel()
            mapdl.esel("S", "MAT", "", M_CO); mapdl.nsle("S")
            mapdl.csys(1); mapdl.seltol(TOL)
            mapdl.nsel("R", "LOC", "Z", STACK / 2 - 2e-4, STACK / 2 + 2e-4)
            mapdl.cm("_CC1", "NODE")
            mapdl.allsel()
            mapdl.esel("S", "MAT", "", M_CO); mapdl.nsle("S")
            mapdl.csys(1)
            mapdl.nsel("R", "LOC", "Z", -STACK / 2 - 2e-4, -STACK / 2 + 2e-4)
            mapdl.cmsel("A", "_CC1"); mapdl.cm("_CC1", "NODE")
            mapdl.cmsel("S", "_CC1")
            first = True
            for (a, b) in th_ranges:
                mapdl.cmsel("S", "_CC1") if first else None
                mapdl.nsel("R", "LOC", "Y", a, b) if first else None
                if first:
                    mapdl.cm("_CC2", "NODE"); first = False
                else:
                    mapdl.cmsel("S", "_CC1"); mapdl.nsel("R", "LOC", "Y", a, b)
                    mapdl.cmsel("A", "_CC2"); mapdl.cm("_CC2", "NODE")
            mapdl.cmsel("S", "_CC2"); mapdl.seltol(0)
        return _fn
    make_surf(sel_coilcut(TH_ATF), N["CEND"], H_CU_END, "coilcut-ATF")
    make_surf(sel_coilcut(TH_WJ + TH_REST), N["CEND"], H_CU_END, "coilcut-rest")

    # ── 슬롯 코일<->코어: SURF152 정션노드 결합 (16각도 x 4z, 직렬 2xTCC) ──
    TCC_SLOT = 2000.0
    jn_id = [int(mapdl.get_value("NODE", 0, "NUM", "MAXD"))]
    njn = 0
    for ib in range(16):
        th0 = -180.0 + ib * 22.5
        for jb in range(4):
            z0 = -STACK / 2 + jb * (STACK / 4)
            z1 = min(z0 + STACK / 4, STACK / 2 - 1e-3)
            jn_id[0] += 1
            thc = math.radians(th0 + 11.25)
            mapdl.csys(0)
            mapdl.n(jn_id[0], 0.075 * math.cos(thc), 0.075 * math.sin(thc),
                    z0 + STACK / 8)
            jn = jn_id[0]
            def sel_side(mat, rband):
                def _fn():
                    mapdl.allsel()
                    mapdl.esel("S", "MAT", "", mat); mapdl.nsle("S")
                    mapdl.csys(1); mapdl.seltol(TOL)
                    if rband:
                        mapdl.nsel("R", "LOC", "X", rband[0], rband[1])
                    mapdl.nsel("R", "LOC", "Y", th0, th0 + 22.5)
                    mapdl.nsel("R", "LOC", "Z", z0 + 2e-4, z1 - 2e-4)
                    mapdl.seltol(0)
                return _fn
            e0 = int(mapdl.get_value("ELEM", 0, "NUM", "MAXD"))
            for mat, rband in ((M_CO, None),
                               (M_CS, (R_COIL_IN - 0.005, R_COIL_OUT + 0.005))):
                sel_side(mat, rband)()
                if mapdl.mesh.n_node == 0:
                    continue
                mapdl.esln("S", 0); mapdl.esel("R", "TYPE", "", 1)
                mapdl.nsel("A", "NODE", "", jn)
                mapdl.type(2); mapdl.real(1)
                mapdl.esurf(jn)
            e1 = int(mapdl.get_value("ELEM", 0, "NUM", "MAXD"))
            if e1 > e0:
                mapdl.esel("S", "ELEM", "", e0 + 1, e1)
                mapdl.sfe("ALL", 1, "CONV", "", 2 * TCC_SLOT)
                njn += 1
            mapdl.allsel()
    P(f"slot junction coupling: {njn}/64 bins active")
    # 스테이터 적층 단면 -> AIR
    for z in (-STACK / 2, STACK / 2):
        make_surf(sel_cyl(z_range=(z, z), mat=M_CS), N["AIR"], HTC_AIR,
                  f"stator-end z={z:+.3f}")

    # ── 발열 (BFE, 요소기반) - 체적은 pyvista 로 계산 (ETABLE 은 POST1 전용) ──
    import numpy as np
    mapdl.allsel(); mapdl.esel("S", "TYPE", "", 1); mapdl.nsle("S")
    _grid = mapdl.mesh.grid
    _vols = _grid.compute_cell_sizes(length=False, area=False,
                                     volume=True).cell_data["Volume"]
    _mats = np.asarray(mapdl.mesh.material_type)
    P("vol arrays:", len(_vols), len(_mats))
    V_slot = float(np.abs(_vols[_mats == M_CO]).sum())
    for mat, key in ((M_CS, "stator"), (M_CR, "rotor"), (M_MG, "magnet"),
                     (M_CO, "coil")):
        q = QD[key]
        mapdl.allsel(); mapdl.esel("S", "MAT", "", mat)
        mapdl.esel("R", "TYPE", "", 1); mapdl.bfe("ALL", "HGEN", 1, q)
        vol = float(np.abs(_vols[_mats == mat]).sum())
        P(f"  mat {mat} {key}: q={q:.3e} W/m3 (V={vol*1e6:.1f}cm3 -> {q*vol:.0f}W)")
    Q_slot = QD["coil"] * V_slot
    Q_end = Q_slot * F_END
    P(f"coil: slot {Q_slot:.0f} W (FEM), end {Q_end:.0f} W (circuit)")
    mapdl.allsel()
    # 코일엔드 회로: 열용량(rho c V_end) + 손실 주입 (ATF 25% / 나머지 75%)
    V_end = V_slot * F_END
    C_end = 8960.0 * 0.45 * 385.0 * V_end
    mapdl.f(N["CEND"], "HEAT", Q_end)
    P(f"coil-end circuit: C={C_end:.0f} J/K, F_heat={Q_end*0.25:.0f}/{Q_end*0.75:.0f} W")

    # ── 과도해석 ─────────────────────────────────────────────────────────
    mapdl.slashsolu(); mapdl.antype(4); mapdl.trnopt("FULL"); mapdl.timint(1)
    mapdl.ic("ALL", "TEMP", T_INIT); mapdl.kbc(1)
    mapdl.deltim(DT, DT / 3, DT); mapdl.time(T_END)
    mapdl.outres("NSOL", "ALL")
    mapdl.ignore_errors = True
    t0 = time.time()
    out = mapdl.run("SOLVE")
    P(f"SOLVE elapsed {(time.time()-t0)/60:.1f} min, tail:")
    P(str(out)[-600:])
    mapdl.ignore_errors = False
    mapdl.finish()

    # ── 후처리 ───────────────────────────────────────────────────────────
    mapdl.post1()
    nsets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
    P("result sets:", nsets)
    if nsets == 0:
        raise RuntimeError("no results")
    mapdl.set("LAST")
    t_last = mapdl.get_value("ACTIVE", 0, "SET", "TIME")
    node_T = {nm: mapdl.get_value("NODE", n, "TEMP") for nm, n in N.items()}
    P("circuit T:", {k: round(v, 1) for k, v in node_T.items()})
    reg_T = {}
    for nm, mat in (("StatorCore", M_CS), ("RotorCore", M_CR),
                    ("Magnet", M_MG), ("Coil", M_CO), ("Shaft", M_SH)):
        mapdl.allsel(); mapdl.esel("S", "MAT", "", mat)
        mapdl.esel("R", "TYPE", "", 1); mapdl.nsle("S")
        arr = mapdl.post_processing.nodal_temperature()
        arr = arr[~np.isnan(arr)]
        if arr.size:
            reg_T[nm] = (float(arr.mean()), float(arr.max()))
    mapdl.allsel()
    P("region T:", {k: (round(a, 1), round(b, 1)) for k, (a, b) in reg_T.items()})

    # 코일 4점 이력
    mapdl.esel("S", "MAT", "", M_CO); mapdl.nsle("S")
    r_eval = (R_COIL_IN + R_COIL_OUT) / 2
    z_tip = 0.9 * STACK / 2   # 슬롯 끝단(코일엔드 제외됨)
    mapdl.csys(0)
    pts = {"Center_WJ": (0, r_eval, 0), "Center_ATF": (0, -r_eval, 0),
           "Tip_WJ": (0, r_eval, z_tip), "Tip_ATF": (0, -r_eval, z_tip)}
    ev = {k: int(mapdl.queries.node(*xyz)) for k, xyz in pts.items()}
    mapdl.allsel()
    hist = []
    for i in range(1, nsets + 1):
        mapdl.set(1, i)
        row = {"time_s": mapdl.get_value("ACTIVE", 0, "SET", "TIME")}
        for k, n in ev.items():
            row[k] = mapdl.get_value("NODE", n, "TEMP")
        hist.append(row)
    with open(os.path.join(OUT, "real_coil_temp.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0].keys()))
        w.writeheader(); w.writerows(hist)
    P("final:", {k: round(hist[-1][k], 1) for k in pts})

    # 컨투어 (뷰별 clim)
    import pyvista as pv
    pv.OFF_SCREEN = True
    mapdl.set("LAST")
    mapdl.esel("S", "TYPE", "", 1); mapdl.nsle("S")
    grid = mapdl.mesh.grid
    temps = mapdl.post_processing.nodal_temperature().astype(float)
    grid.point_data["Temperature (degC)"] = temps
    mapdl.allsel()
    sb = dict(title="Temperature (degC)", title_font_size=16,
              label_font_size=13, n_labels=6, fmt="%.1f", color="black")
    views = [
        ("real_contour_iso.png", grid, ("view_isometric",), True),
        ("real_contour_slice_x0.png", grid.slice(normal="x"),
         ("view_vector", (1, 0, 0), dict(viewup=(0, 1, 0))), False),
        ("real_contour_slice_z0.png", grid.slice(normal="z"), ("view_xy",),
         False),
    ]
    for fname, mesh, view, lit in views:
        tv = mesh.point_data["Temperature (degC)"]
        kw = dict(cmap="inferno", scalar_bar_args=sb,
                  clim=[float(np.nanmin(tv)), float(np.nanmax(tv))])
        if lit:
            kw.update(smooth_shading=True, ambient=0.6, diffuse=0.4,
                      specular=0.0)
        else:
            kw.update(lighting=False)
        p = pv.Plotter(off_screen=True, window_size=(1280, 960))
        p.set_background("white")
        p.add_mesh(mesh, **kw)
        p.add_text(f"REAL geometry @ t={t_last:.0f}s", font_size=12,
                   color="black")
        getattr(p, view[0])(*view[1:2], **(view[2] if len(view) > 2 else {}))
        p.screenshot(os.path.join(OUT, fname))
        p.close()
        P("saved", fname)
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    try:
        if mapdl is not None:
            mapdl.exit(); P("mapdl exited")
    except Exception:
        pass
    log.close(); os._exit(0)
