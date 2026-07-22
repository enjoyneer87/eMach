# -*- coding: utf-8 -*-
"""e10 FreeFlow 오일냉각 = JAC279식 하이브리드 열해석.
3D FEM(스테이터/권선(엔드턴포함)/로터) + 열등가회로(오일 스파이럴자켓 + 엔드턴 스프레이).
Prius 03_mapdl_thermal.py(JAC279) 구조를 FreeFlow 오일냉각 토폴로지로 이식.
과도해석 -> file.rth -> thermal_viz dashboard.
"""
import os, math, csv, time, json, traceback
SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
CDB = r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2"   # .cdb (자석/샤프트 포함)
LOSSJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_losses.json"
OUTJSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\ff_mapdl_hybrid_temps.json"
RUN = os.path.join(SP, "ff_hybrid_v2_run2")
log = open(os.path.join(SP, "ff_hybrid.txt"), "w", encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()

try:
    import numpy as np
    # ── 손실 로드 (실측 운전점 + Prius추정 분포) ──
    Pcu = Pfe_s = Pfe_r = Pmag = 0.0
    try:
        d = json.load(open(LOSSJSON, encoding="utf-8"))
        s = d.get("_summary_W", d.get("losses_W", {}))
        Pcu = float(s.get("copper", 0)); Pfe_s = float(s.get("stator_iron", 0))
        Pfe_r = float(s.get("rotor_iron", 0)); Pmag = float(s.get("magnet", 0))
    except Exception as e:
        P("loss json:", repr(e)[:80])
    if Pcu < 1:  # Prius 추정 폴백
        Pcu, Pfe_s, Pfe_r, Pmag = 3350.0, 585.0, 65.0, 24.0
        LOSS_SRC = "Prius-estimate"
    else:
        LOSS_SRC = "e10 losses.json"
    P(f"losses[W] cu={Pcu:.0f} fe_s={Pfe_s:.0f} fe_r={Pfe_r:.0f} mag={Pmag:.0f} src={LOSS_SRC}")

    # ── e10 기하(메시 실측) ──
    M_ST, M_MG, M_CO, M_SH, M_RO = 1, 2, 3, 4, 5
    R_STA_OUT = 0.0990; R_STA_IN = 0.0713
    R_ROT_OUT = 0.07027                        # Maxwell 2D 로터 OD
    R_SHAFT = 0.023455
    Z_ST0, Z_ST1 = -0.2075, -0.0575          # 스테이터 스택
    STACK = Z_ST1 - Z_ST0                     # 0.150
    ZC = 0.5 * (Z_ST0 + Z_ST1)                # 스택 중심 -0.1325
    # ── 재료 (열전도율/비열/밀도) ──
    MATS = {M_ST: (25.0, 460.0, 7650.0),      # stator lam
            M_MG: (9.0, 460.0, 7500.0),       # NdFeB 자석
            M_CO: (5.0, 385.0, 4480.0),       # 구리 등가(fill 0.5)
            M_SH: (52.0, 460.0, 7870.0),      # 샤프트 강
            M_RO: (25.0, 460.0, 7650.0)}      # rotor lam
    # ── 오일(ATF) 물성 & 냉각 파라미터 ──
    OIL_T = 70.0
    RHO_OIL, CP_OIL = 825.0, 2000.0
    MDOT_OIL = 0.11                            # kg/s (~8 LPM)
    HTC_JKT = 1000.0        # 스파이럴 자켓 오일(스테이터 OD)
    HTC_SPRAY = 2000.0      # 엔드턴 오일 스프레이
    HTC_SPLASH = 250.0      # 로터 단면 오일 미스트
    HTC_BIG = 1e4           # gap 인터페이스(저항은 gap 노드가)
    K_AIR = 0.03; GAP_G = 0.0007
    # 오일 유량 분배 -> 유동 열컨덕턴스 (mdot*cp)
    G_JKT_OIL = 0.60 * MDOT_OIL * CP_OIL      # 132 W/K
    G_SPRAY_OIL = 0.40 * MDOT_OIL * CP_OIL    # 88 W/K
    # 오일 열용량(채널/필름)
    C_JKT = 0.20e-3 * RHO_OIL * CP_OIL        # ~330 J/K
    C_SPRAY = 0.15e-3 * RHO_OIL * CP_OIL      # ~248 J/K
    # gap 공기 컨덕턴스
    A_GAP = 2 * math.pi * R_STA_IN * STACK
    G_GAP = K_AIR * A_GAP / GAP_G
    T_INIT = OIL_T; T_END, DT = 900.0, 45.0
    TOL = 1e-5; RT = 8e-4

    from ansys.mapdl.core import launch_mapdl
    mapdl = None
    mapdl = launch_mapdl(run_location=RUN, override=True, nproc=4, loglevel="ERROR")
    P("mapdl", mapdl.version)
    mapdl.clear(); mapdl.prep7(); mapdl.units("SI")
    mapdl.cdread("DB", CDB, "cdb")
    mapdl.shpp("off")
    P("mesh", mapdl.mesh.n_node, mapdl.mesh.n_elem)
    mapdl.et(1, "SOLID87")
    mapdl.et(2, "SURF152"); mapdl.keyopt(2, 5, 1); mapdl.keyopt(2, 8, 2)
    mapdl.et(3, "COMBIN14"); mapdl.keyopt(3, 2, 8)
    mapdl.et(4, "MASS71"); mapdl.keyopt(4, 3, 1)
    for m, (k, c, r) in MATS.items():
        mapdl.mp("KXX", m, k); mapdl.mp("C", m, c); mapdl.mp("DENS", m, r)

    # ── 열등가회로 (FreeFlow 오일냉각) ──
    nmax = int(mapdl.get_value("NODE", 0, "NUM", "MAXD"))
    def net_node(i):
        n = nmax + i; mapdl.csys(0); mapdl.n(n, 0.5 + 0.02 * i, 0, 0); return n
    N = {nm: net_node(i + 1) for i, nm in enumerate(
        ["OIL", "JACKET", "SPRAY", "GAP_S", "GAP_R", "SHF"])}
    _rid = [100]
    def add_C(node, c):
        _rid[0] += 1; mapdl.type(4); mapdl.real(_rid[0]); mapdl.r(_rid[0], c); mapdl.e(node)
    def add_R(n1, n2, g):
        _rid[0] += 1; mapdl.type(3); mapdl.real(_rid[0]); mapdl.r(_rid[0], g); mapdl.e(n1, n2)
    add_C(N["JACKET"], C_JKT); add_C(N["SPRAY"], C_SPRAY)
    add_C(N["SHF"], 200.0)                     # 샤프트/베어링 열용량
    add_R(N["JACKET"], N["OIL"], G_JKT_OIL)
    add_R(N["SPRAY"], N["OIL"], G_SPRAY_OIL)
    add_R(N["GAP_S"], N["GAP_R"], G_GAP)
    add_R(N["SHF"], N["OIL"], 40.0)           # 샤프트->베어링/오일 경로
    mapdl.d(N["OIL"], "TEMP", OIL_T)          # 오일 공급 고정
    P(f"circuit: G_jkt={G_JKT_OIL:.0f} G_spray={G_SPRAY_OIL:.0f} G_gap={G_GAP:.2f} "
      f"C_jkt={C_JKT:.0f} C_spray={C_SPRAY:.0f} W/K,J/K")

    # ── SURF152 경계 (FEM 표면 -> 회로 노드) ──
    mapdl.r(1)
    def make_surf(sel_fn, xnode, htc, name):
        mapdl.allsel(); sel_fn()
        nsel = mapdl.mesh.n_node
        if nsel == 0: P(f"  [warn] {name}: empty"); mapdl.allsel(); return
        e0 = int(mapdl.get_value("ELEM", 0, "NUM", "MAXD"))
        mapdl.esln("S", 0); mapdl.esel("R", "TYPE", "", 1)
        mapdl.nsel("A", "NODE", "", xnode)
        mapdl.type(2); mapdl.real(1); mapdl.esurf(xnode)
        e1 = int(mapdl.get_value("ELEM", 0, "NUM", "MAXD"))
        if e1 <= e0: P(f"  [warn] {name}: {nsel}n noSURF"); mapdl.allsel(); return
        mapdl.esel("S", "ELEM", "", e0 + 1, e1)
        mapdl.sfe("ALL", 1, "CONV", "", htc); mapdl.allsel()
        P(f"  [surf] {name}: {e1-e0} elems ({nsel}n)")
    def sel_matradz(mat, rlo=None, rhi=None, zlo=None, zhi=None, ext=True):
        def _fn():
            mapdl.allsel(); mapdl.esel("S", "MAT", "", mat); mapdl.nsle("S")
            if ext:  # 외곽면만
                mapdl.nsel("R", "EXT")
            mapdl.csys(1); mapdl.seltol(TOL)
            if rlo is not None: mapdl.nsel("R", "LOC", "X", rlo, rhi)
            if zlo is not None: mapdl.nsel("R", "LOC", "Z", zlo, zhi)
            mapdl.seltol(0); mapdl.csys(0)
        return _fn
    # 스테이터 OD -> JACKET(스파이럴 자켓)
    make_surf(sel_matradz(M_ST, rlo=R_STA_OUT - RT, rhi=R_STA_OUT + RT), N["JACKET"], HTC_JKT, "statorOD->JACKET")
    # 스테이터 bore -> GAP_S
    make_surf(sel_matradz(M_ST, rlo=R_STA_IN - RT, rhi=R_STA_IN + RT), N["GAP_S"], HTC_BIG, "statorBore->GAP_S")
    # 권선 엔드턴(스택 밖 z) 외곽 -> SPRAY
    make_surf(sel_matradz(M_CO, zhi=Z_ST0 + 2e-4, zlo=-1.0), N["SPRAY"], HTC_SPRAY, "windEnd_lo->SPRAY")
    make_surf(sel_matradz(M_CO, zlo=Z_ST1 - 2e-4, zhi=1.0), N["SPRAY"], HTC_SPRAY, "windEnd_hi->SPRAY")
    # 로터 OD -> GAP_R
    make_surf(sel_matradz(M_RO, rlo=R_ROT_OUT - RT, rhi=R_ROT_OUT + RT), N["GAP_R"], HTC_BIG, "rotorOD->GAP_R")
    # 로터 축단면 -> OIL(스플래시)
    make_surf(sel_matradz(M_RO, zhi=Z_ST0 + 2e-4, zlo=-1.0), N["OIL"], HTC_SPLASH, "rotorEnd_lo->OIL")
    make_surf(sel_matradz(M_RO, zlo=Z_ST1 - 2e-4, zhi=1.0), N["OIL"], HTC_SPLASH, "rotorEnd_hi->OIL")
    # 샤프트 축단면 -> SHF(베어링/오일 경로)
    make_surf(sel_matradz(M_SH, zhi=Z_ST0 + 2e-4, zlo=-1.0), N["SHF"], HTC_SPLASH, "shaftEnd_lo->SHF")
    make_surf(sel_matradz(M_SH, zlo=Z_ST1 - 2e-4, zhi=1.0), N["SHF"], HTC_SPLASH, "shaftEnd_hi->SHF")

    # ── 발열 HGEN (요소체적으로 밀도화) ──
    mapdl.allsel(); mapdl.esel("S", "TYPE", "", 1); mapdl.nsle("S")
    grid = mapdl.mesh.grid
    vols = grid.compute_cell_sizes(length=False, area=False, volume=True).cell_data["Volume"]
    emats = np.asarray(mapdl.mesh.material_type)
    P("vol arrays", len(vols), len(emats))
    # 자석/로터철손 분리(v2), 샤프트 무손실
    LOSS = {M_ST: Pfe_s, M_MG: Pmag, M_CO: Pcu, M_RO: Pfe_r}
    for mat, W in LOSS.items():
        vol = float(np.abs(vols[emats == mat]).sum())
        q = W / vol if vol > 0 else 0.0
        mapdl.allsel(); mapdl.esel("S", "MAT", "", mat); mapdl.esel("R", "TYPE", "", 1)
        mapdl.bfe("ALL", "HGEN", 1, q)
        P(f"  mat{mat}: V={vol*1e6:.0f}cm3 q={q:.3e} W/m3 ({W:.0f}W)")
    mapdl.allsel()

    # ── 과도해석 ──
    mapdl.slashsolu(); mapdl.antype(4); mapdl.trnopt("FULL"); mapdl.timint(1)
    mapdl.ic("ALL", "TEMP", T_INIT); mapdl.kbc(1)
    mapdl.deltim(DT, DT / 3, DT); mapdl.time(T_END)
    mapdl.outres("NSOL", "ALL")
    mapdl.ignore_errors = True
    t0 = time.time(); mapdl.run("SOLVE"); t_solve = time.time() - t0
    mapdl.ignore_errors = False; mapdl.finish()
    P(f"SOLVE {t_solve/60:.1f} min")

    # ── 후처리 ──
    mapdl.post1()
    nsets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
    P("nsets", nsets)
    mapdl.set("LAST")
    node_T = {nm: float(mapdl.get_value("NODE", n, "TEMP")) for nm, n in N.items()}
    P("circuit T:", {k: round(v, 1) for k, v in node_T.items()})
    names = {M_ST: "stator", M_MG: "magnet", M_CO: "winding", M_SH: "shaft", M_RO: "rotor"}
    per = {}
    for m, nm in names.items():
        mapdl.allsel(); mapdl.esel("S", "MAT", "", m); mapdl.esel("R", "TYPE", "", 1); mapdl.nsle("S")
        arr = mapdl.post_processing.nodal_temperature()
        arr = arr[~np.isnan(arr)]
        per[nm] = dict(max=float(arr.max()), min=float(arr.min()), mean=float(arr.mean()))
        P(f"  {nm}: max={per[nm]['max']:.1f} mean={per[nm]['mean']:.1f} C")
    mapdl.allsel()
    res = {"_model": "JAC279-hybrid FEM+oil-circuit", "_loss_source": LOSS_SRC,
           "_timing": {"solve_time_s": round(t_solve, 1), "nsets": nsets},
           "_oil": {"T": OIL_T, "mdot": MDOT_OIL, "htc_jkt": HTC_JKT, "htc_spray": HTC_SPRAY},
           "circuit_T": {k: round(v, 1) for k, v in node_T.items()},
           "losses_W": {"copper": Pcu, "stator_iron": Pfe_s, "rotor_iron": Pfe_r, "magnet": Pmag},
           "per_part": per, "rth": os.path.join(RUN, "file.rth")}
    os.makedirs(os.path.dirname(OUTJSON), exist_ok=True)
    json.dump(res, open(OUTJSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    P("saved", OUTJSON)
    P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    try:
        if mapdl is not None: mapdl.exit()
    except Exception: pass
    log.close(); os._exit(0)
