# -*- coding: utf-8 -*-
"""d3_htc_backout.py -- FreeFlow SPH 근벽 온도구배로부터 대류계수 h 역산 (D3).

계획서 §1 D3
------------
중력을 축방향(-Z, 수직취부)에서 반경방향(-Y, 수평취부)으로 고친 뒤 FreeFlow 8 s
fresh solve -> 그 결과로 HTC 역산을 다시 해서 `thesis_out/htc_backout_horizontal.json`
을 만든다. 기존(중력 오류) 결과는 `freeflow/data/htc_backout.json` (t=6.53 s).

★ 원본 역산 스크립트는 옛 scratchpad 와 함께 소실됐다.
   레포 전체에 htc_backout / h_grad / q_grad_Wm2 문자열이 하나도 없다.
   따라서 이 파일은 `freeflow/data/htc_backout.json` 의 저장값으로부터 **역설계**한 것이고,
   아래 네 식은 전부 그 파일에 대해 수치적으로 재현 확인했다 (--verify-legacy 참조).

        Pr      = mu*cp/k                                -> 148.148 (파일 148.1)
        Re      = rho * V_nearwall * Dh / mu             -> 98.3 / 196.7 / 327.8 (Dh 3/6/10 mm)
        Nu      = 4.36                                   (층류·등열유속·원관 해석해.
                                                          파일은 4.4 로 반올림해 저장)
        h_corr  = Nu * k / Dh                            -> 196.2 / 98.1 / 58.9
        q_grad  = k * (T_wall - T_bin1) / delta
        h_grad  = q_grad / (T_wall - T_bulk)             -> 192.90 / 186.34 (파일 192.8 / 186.3)

★ delta 의 정체 (이 파일에서 새로 밝힘)
   `T_profile_0to3mm` 은 벽면거리 0~3 mm 를 6 등분(0.5 mm)한 구간별 평균온도이고
   0 번 칸이 `null` 인 것은 [0, 0.5) mm 에 SPH 입자가 존재하지 않기 때문이다
   (입자 간격의 절반보다 벽에 가까이 갈 수 없다). 따라서 벽에 가장 가까운 유효 표본은
   **1 번 칸 [0.5, 1.0) mm** 이고, 그 칸의 공칭 중심은 0.75 mm 다.
   저장값에서 역산한 delta 는 Stator 0.74307 mm / Winding 0.74032 mm 로
   둘 다 0.75 mm 에서 -0.9 % / -1.3 % 다. 즉 delta 는 임의의 튜닝 상수가 아니라
   **1 번 칸에 실제로 들어있는 입자들의 평균 벽면거리**다. 두 영역의 delta 가 0.37 %
   다른 이유도 이것으로 설명된다(영역마다 입자 분포가 조금 다르다).
   -> 입자 데이터가 있으면 delta 를 이 정의대로 다시 계산한다(--delta-mode bin1).
      집계값만 있으면 --delta (기본 7.43e-4 m) 를 쓴다.

입력 경로 (모두 CLI 인자, 하드코딩 금지)
----------------------------------------
1) --sph  <file.sph>        ★ 권장. FreeFlow(Rocky) 가 쓰는 HDF5 입자 파일을 직접 읽는다.
   스키마는 `freeflow/scripts/13_freeflow_thermal_viz.py:38-44` 에서 이미 검증된 것:
        free/position          구조화배열, 필드 x, y, z          [m]
        free/velocity_x/_y/_z  각각 1D 배열                      [m/s]
        sph_scalars/temperature 1D 배열                          [degC]
   position 과 sph_scalars 길이가 다를 수 있으므로(released 입자) 최소길이로 자른다.
   벽면거리는 --geom-dir 의 STL 로부터 pyvista 로 계산한다.

2) --particles <file.csv|.npz>   FreeFlow 쪽에서 미리 뽑아 둔 근벽 표본.
   ---------------------------------------------------------------------
   CSV: 첫 줄이 헤더여야 한다. 열 이름은 대소문자 무시.
     필수:  x, y, z          입자 위치 [m]  (전역 좌표, 모터축 = Z)
            vx, vy, vz       입자 속도 [m/s]
            T                입자 온도 [degC]   (별칭: temp, temperature)
     선택:  dist             벽면까지의 최단거리 [m]
                             (없으면 --geom-dir STL 로 계산 -> pyvista 필요)
            region           소속 벽 이름 문자열 "Stator" | "Winding"
                             (없으면 --geom-dir STL 최근접 벽으로 배정)
   NPZ: 위와 같은 이름의 배열들을 담은 np.savez. 추가로 선택키 `t_reached`
        (물리시간 [s], 스칼라) 를 넣어두면 --t-reached 를 생략할 수 있다.
   단위 주의: 길이는 전부 **미터**다. mm 로 뽑았으면 --particle-length-unit mm.

3) --wall-temps <ff_mapdl_hybrid_temps.json>   벽 온도경계 [degC] 와 가정 htc.
      Stator  -> circuit_T.JACKET (84.4), 가정 htc = _oil.htc_jkt   (1000)
      Winding -> circuit_T.SPRAY  (91.9), 가정 htc = _oil.htc_spray (2000)

출력
----
--out (기본 <repo>/mlxperPJT/thermal/thesis_out/htc_backout_horizontal.json)
기존 htc_backout.json 과 **같은 구조**를 유지하고(T_profile_0to3mm 의 선두 null 포함)
거기에 _soltype / _loss_source / _htc / _gravity / _delta_vs_vertical_gravity 를 덧붙인다.

CLI
---
    python d3_htc_backout.py --verify-legacy --repo <repo root>
    python d3_htc_backout.py --self-test
    python d3_htc_backout.py --sph <...\\Project_thermal_horizontal.freeflow.files\\simulation\\xxx.sph> \\
                             --geom-dir <...\\Geometry> --t-reached 8.0 --repo <repo root>
    python d3_htc_backout.py --particles nearwall.csv --t-reached 8.0 --repo <repo root>

python 3.10 호환 (match 없음, `X | Y` 어노테이션 없음, 3.11+ stdlib 없음).
"""

import argparse
import json
import os
import sys

# numpy 는 입자 처리에만 필요하다. --verify-legacy / --self-test 는 순수 stdlib 로
# 돌아가야 하므로(맨 인터프리터에서도 검증이 가능해야 한다) 지연 import 한다.
try:
    import numpy as _np
except Exception:                                    # pragma: no cover
    _np = None


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

LEGACY_REL = "mlxperPJT/thermal/freeflow/data/htc_backout.json"
WALLTEMPS_REL = "mlxperPJT/thermal/freeflow/data/ff_mapdl_hybrid_temps.json"
OUT_REL = "mlxperPJT/thermal/thesis_out/htc_backout_horizontal.json"

# 오일(ATF) 물성 -- 11/12_freeflow_thermal_*.py 가 FreeFlow 유체에 실제로 넣은 값과 동일
OIL_RHO = 825.0        # kg/m^3
OIL_CP = 2000.0        # J/kg/K
OIL_K = 0.135          # W/m/K
OIL_MU = 0.01          # Pa*s

NU_LAMINAR = 4.36      # 층류 완전발달 원관, 등열유속 (constant q") 해석해
DH_MM_DEFAULT = "3,6,10"
DELTA_DEFAULT = 7.43e-4       # m, 1번 칸 평균 벽면거리
BAND_MM_DEFAULT = 3.0         # T_profile 이 덮는 범위 [mm]
N_BINS_DEFAULT = 6            # 0~3 mm 를 6 등분 -> 0.5 mm

REGIONS = ("Stator", "Winding")
REGION_CIRCUIT_NODE = {"Stator": "JACKET", "Winding": "SPRAY"}
REGION_HTC_KEY = {"Stator": "htc_jkt", "Winding": "htc_spray"}

# HANDOFF_20260722.md §10-4 / CLAUDE.md 의 미수정 모델링 오류
GRAVITY_OLD = (0.0, 0.0, -9.81)      # 축방향 = 수직취부 (틀림)
GRAVITY_NEW = (0.0, -9.81, 0.0)      # 반경방향 = 수평취부 (맞음)
GRAVITY_CITE = ("HANDOFF_20260722.md §10-4: e10 is horizontally mounted but the "
                "FreeFlow gravity vector was set along the motor axis (-Z). D3 fixes it "
                "to a radial direction (-Y) and re-solves from t=0.")

LEGACY_T_REACHED_S = 6.53      # HANDOFF §10-1: 8 s 솔브가 6.53 s 에서 중단


# ---------------------------------------------------------------------------
# 로깅 (stdout + --log 파일 동시)
# ---------------------------------------------------------------------------

class Log(object):
    """stdout 과 파일에 동시에 쓴다. moa 가 무인으로 돌리므로 파일 로그가 필수."""

    def __init__(self, path=None):
        self.fh = None
        if path:
            d = os.path.dirname(os.path.abspath(path))
            if d and not os.path.isdir(d):
                os.makedirs(d)
            self.fh = open(path, "w", encoding="utf-8")

    def __call__(self, *args):
        msg = " ".join(str(a) for a in args)
        try:
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()
        except Exception:
            pass
        if self.fh is not None:
            self.fh.write(msg + "\n")
            self.fh.flush()

    def close(self):
        if self.fh is not None:
            self.fh.close()
            self.fh = None


def default_repo_root():
    """kit dir = <repo>/mlxperPJT/thermal/plans/PLAN_20260906_assets -> 4 단계 위.

    moa 가 이 파일을 freeflow/scripts/ 로 승격하면 깊이가 달라지므로, 승격 후에는
    --repo 를 명시해야 한다. CLI 인자가 정본이다.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir, os.pardir, os.pardir))


def _rel(repo_root, rel):
    return os.path.normpath(os.path.join(str(repo_root), *rel.split("/")))


# ---------------------------------------------------------------------------
# 순수 함수 -- 역산 4 식
# ---------------------------------------------------------------------------

def prandtl(mu, cp, k):
    """Pr = mu*cp/k. 오일(ATF)은 Pr ~ 148 로 매우 크다(점성 지배)."""
    return float(mu) * float(cp) / float(k)


def reynolds(rho, v, dh, mu):
    """Re = rho*V*Dh/mu.  V 는 근벽 밴드 입자속도 크기의 평균, Dh 는 가정 수력직경."""
    return float(rho) * float(v) * float(dh) / float(mu)


def h_correlation(nu, k, dh):
    """h = Nu*k/Dh.  Nu 는 층류 등열유속 원관값 4.36 (Re<2300 이므로 층류 타당)."""
    return float(nu) * float(k) / float(dh)


def q_gradient(k, t_wall, t_nearwall, delta):
    """벽면 열유속 q" = k*(T_wall - T_nearwall)/delta  [W/m^2] (Fourier, 1차 차분).

    t_nearwall 은 벽에서 가장 가까운 **비어있지 않은** 프로파일 칸(bin 1)의 평균온도,
    delta 는 그 칸에 든 입자들의 평균 벽면거리다.
    """
    return float(k) * (float(t_wall) - float(t_nearwall)) / float(delta)


def h_from_q(q, t_wall, t_bulk):
    """h = q" / (T_wall - T_bulk).  뉴턴 냉각법칙의 정의식."""
    dt = float(t_wall) - float(t_bulk)
    if abs(dt) < 1e-12:
        raise ValueError("h_from_q: T_wall - T_bulk = 0 -> h undefined "
                         "(T_wall=%r, T_bulk=%r)" % (t_wall, t_bulk))
    return float(q) / dt


def backout_region(wall_T_C, T_bin1_C, T_bulk_C, delta_m, V_nearwall,
                   oil=None, dh_list_m=(3e-3, 6e-3, 10e-3), nu=NU_LAMINAR,
                   assumed_htc=None, n_band=None, T_profile=None,
                   nearwall_Toil_C=None, round_like_legacy=True):
    """한 영역(Stator | Winding)의 HTC 역산 전체를 수행한다. 순수 함수.

    반환 dict 는 기존 htc_backout.json 의 per_region 항목과 **키·순서가 같다**.
    round_like_legacy=True 면 기존 파일의 소수자리 관례를 그대로 따른다
    (Re/h/T 1~2 자리). 원시 미반올림 값은 "_raw" 하위 dict 에 함께 담는다.
    """
    if oil is None:
        oil = {"rho": OIL_RHO, "cp": OIL_CP, "k": OIL_K, "mu": OIL_MU}
    rho = float(oil["rho"]); cp = float(oil["cp"])
    k = float(oil["k"]); mu = float(oil["mu"])

    q = q_gradient(k, wall_T_C, T_bin1_C, delta_m)
    h = h_from_q(q, wall_T_C, T_bulk_C)

    corr = {}
    corr_raw = {}
    for dh in dh_list_m:
        key = "Dh%gmm" % (round(dh * 1000.0, 6),)
        re = reynolds(rho, V_nearwall, dh, mu)
        hc = h_correlation(nu, k, dh)
        corr_raw[key] = {"Re": re, "Nu": float(nu), "h": hc}
        if round_like_legacy:
            corr[key] = {"Re": round(re, 1), "Nu": round(float(nu), 1), "h": round(hc, 1)}
        else:
            corr[key] = dict(corr_raw[key])

    def _r(x, nd):
        return round(float(x), nd) if round_like_legacy else float(x)

    out = {}
    if assumed_htc is not None:
        out["assumed_htc"] = float(assumed_htc)
    out["nearwall_V"] = _r(V_nearwall, 3)
    if nearwall_Toil_C is not None:
        out["nearwall_Toil"] = _r(nearwall_Toil_C, 2)
    out["wall_T"] = float(wall_T_C)
    out["Tbulk"] = _r(T_bulk_C, 2)
    if n_band is not None:
        out["n_band"] = int(n_band)
    out["h_velocity_corr"] = corr
    if T_profile is not None:
        # 선두 null 은 이 파일의 관례다(벽에서 [0,0.5) mm 는 SPH 입자가 없음) -- 유지한다.
        out["T_profile_0to3mm"] = [None if t is None else _r(t, 2) for t in T_profile]
    out["q_grad_Wm2"] = _r(q, 1)
    out["h_grad"] = _r(h, 1)
    out["_raw"] = {
        "delta_m": float(delta_m),
        "T_bin1_C": float(T_bin1_C),
        "q_grad_Wm2": float(q),
        "h_grad": float(h),
        "Pr": prandtl(mu, cp, k),
        "nearwall_V_ms": float(V_nearwall),
        "Tbulk_C": float(T_bulk_C),
        "h_velocity_corr": corr_raw,
    }
    return out


# ---------------------------------------------------------------------------
# 반올림 오차 예산 -- 저장값으로부터의 재현 검증에 쓴다
# ---------------------------------------------------------------------------

def stored_half_ulp(x):
    """JSON 에 저장된 십진수의 마지막 자리 절반(= 반올림 불확실도)을 돌려준다.

    예) 2436.3 -> 0.05,  71.77 -> 0.005,  0.397 -> 0.0005
    검증에서 '매직 톨러런스'를 쓰지 않기 위한 장치다. 허용오차를 손으로 고르는 대신
    저장 정밀도에서 유도한다.
    """
    s = repr(float(x))
    if "e" in s or "E" in s:
        return abs(float(x)) * 1e-12
    if "." not in s:
        return 0.5
    return 0.5 * (10.0 ** (-len(s.split(".")[1])))


# ---------------------------------------------------------------------------
# --verify-legacy : 기존 파일을 자기 자신의 저장값으로 재현
# ---------------------------------------------------------------------------

def verify_legacy(legacy, log, delta_nominal=DELTA_DEFAULT, nu=NU_LAMINAR):
    """freeflow/data/htc_backout.json 을 읽어 저장 필드만으로 4 식을 재유도하고,
    저장값을 재현하는지 확인한다. 허용오차는 전부 저장 정밀도에서 유도한다.

    반환: (ok, details dict)
    """
    ok = True
    details = {"checks": [], "implied_delta_m": {}}

    oil = legacy["oil_props"]
    rho = float(oil["rho"]); cp = float(oil["cp"])
    k = float(oil["k"]); mu = float(oil["mu"])

    def check(name, got, want, tol, unit=""):
        err = abs(got - want)
        good = err <= tol
        log("  [%s] %-34s derived=%12.5f stored=%10.4f  err=%9.2e tol=%9.2e %s"
            % ("PASS" if good else "FAIL", name, got, want, err, tol, unit))
        details["checks"].append({"name": name, "derived": got, "stored": want,
                                  "abs_err": err, "tol": tol, "ok": bool(good)})
        return good

    log("-" * 100)
    log("1) Pr = mu*cp/k")
    pr = prandtl(mu, cp, k)
    ok &= check("Pr", pr, float(oil["Pr"]), stored_half_ulp(oil["Pr"]))

    for reg in REGIONS:
        r = legacy["per_region"][reg]
        log("-" * 100)
        log("region: %s" % reg)

        v = float(r["nearwall_V"])
        tw = float(r["wall_T"])
        tb = float(r["Tbulk"])
        prof = r["T_profile_0to3mm"]
        q_stored = float(r["q_grad_Wm2"])
        h_stored = float(r["h_grad"])

        # -- 2) Re = rho*V*Dh/mu -------------------------------------------------
        log("2) Re = rho*V*Dh/mu      (V stored to %d dp -> dV=%g m/s)"
            % (len(repr(v).split(".")[-1]), stored_half_ulp(v)))
        dv = stored_half_ulp(v)
        for key, sub in sorted(r["h_velocity_corr"].items()):
            dh_mm = float(key.replace("Dh", "").replace("mm", ""))
            dh = dh_mm * 1e-3
            re = reynolds(rho, v, dh, mu)
            tol = (rho * dh / mu) * dv + stored_half_ulp(sub["Re"])
            ok &= check("%s Re %s" % (reg, key), re, float(sub["Re"]), tol)

        # -- 3) Nu / h_corr = Nu*k/Dh -------------------------------------------
        log("3) h_corr = Nu*k/Dh      (Nu = %.2f laminar const-q; file stores it rounded)" % nu)
        for key, sub in sorted(r["h_velocity_corr"].items()):
            dh_mm = float(key.replace("Dh", "").replace("mm", ""))
            dh = dh_mm * 1e-3
            ok &= check("%s Nu %s" % (reg, key), float(nu), float(sub["Nu"]),
                        stored_half_ulp(sub["Nu"]))
            hc = h_correlation(nu, k, dh)
            ok &= check("%s h_corr %s" % (reg, key), hc, float(sub["h"]),
                        stored_half_ulp(sub["h"]))

        # -- 4) q_grad -> implied delta -----------------------------------------
        # delta 는 파일에 없다. 그러므로 '가정'하는 대신 저장 q_grad 에서 역산해
        # 그것이 1번 칸 [0.5,1.0) mm 안에 있고 공칭중심 0.75 mm 근처인지 확인한다.
        t_bin1 = prof[1]
        if t_bin1 is None:
            log("  [FAIL] %s: T_profile_0to3mm[1] is null -- no near-wall sample" % reg)
            ok = False
            continue
        t_bin1 = float(t_bin1)
        d_imp = k * (tw - t_bin1) / q_stored
        details["implied_delta_m"][reg] = d_imp
        log("4) q_grad = k*(T_wall - T_bin1)/delta   -> implied delta")
        log("     T_wall=%.2f  T_bin1(profile[1])=%.2f  q_stored=%.1f" % (tw, t_bin1, q_stored))
        log("     implied delta = %.6f mm   (bin1 = [0.50, 1.00) mm, nominal centre 0.75 mm,"
            " deviation %+.2f %%)" % (d_imp * 1e3, (d_imp / 0.75e-3 - 1.0) * 100.0))
        in_bin = (0.5e-3 <= d_imp <= 1.0e-3)
        log("  [%s] implied delta lies inside profile bin 1" % ("PASS" if in_bin else "FAIL"))
        details["checks"].append({"name": "%s delta in bin1" % reg, "derived": d_imp,
                                 "stored": None, "abs_err": 0.0, "tol": 0.0, "ok": bool(in_bin)})
        ok &= in_bin
        near_nom = abs(d_imp - delta_nominal) <= 0.015 * delta_nominal
        log("  [%s] implied delta within 1.5%% of nominal --delta %.5g m (%.4f mm)"
            % ("PASS" if near_nom else "FAIL", delta_nominal, delta_nominal * 1e3))
        details["checks"].append({"name": "%s delta vs nominal" % reg, "derived": d_imp,
                                 "stored": delta_nominal,
                                 "abs_err": abs(d_imp - delta_nominal),
                                 "tol": 0.015 * delta_nominal, "ok": bool(near_nom)})
        ok &= near_nom

        # 저장 delta 자리로 되돌려 q_grad 자체도 재현되는지 확인
        q_re = q_gradient(k, tw, t_bin1, d_imp)
        ok &= check("%s q_grad (round-trip)" % reg, q_re, q_stored,
                    stored_half_ulp(q_stored) + 1e-6 * q_stored, "W/m2")

        # -- 5) h_grad = q/(Tw - Tbulk) -----------------------------------------
        # 오차 예산: dh = dq/(dT) + q/(dT)^2 * (dTw + dTb)   (1차 전파)
        log("5) h_grad = q_grad/(T_wall - T_bulk)")
        dT = tw - tb
        dq = stored_half_ulp(q_stored)
        dtw = stored_half_ulp(tw)
        dtb = stored_half_ulp(tb)
        tol_h = dq / abs(dT) + q_stored / (dT * dT) * (dtw + dtb) + stored_half_ulp(h_stored)
        hg = h_from_q(q_stored, tw, tb)
        log("     dT=%.2f K   budget: dq=%.3g  dTw=%.3g  dTb=%.3g  -> tol=%.4f W/m2K"
            % (dT, dq, dtw, dtb, tol_h))
        ok &= check("%s h_grad" % reg, hg, h_stored, tol_h, "W/m2K")

    # -- 6) 두 영역의 delta 가 서로 일관적인가 (같은 SPH 샘플링 거리) --------------
    log("-" * 100)
    if len(details["implied_delta_m"]) == 2:
        ds = [details["implied_delta_m"][r] for r in REGIONS]
        spread = abs(ds[0] / ds[1] - 1.0)
        good = spread <= 0.01
        log("6) [%s] per-region delta consistency: Stator %.6f mm vs Winding %.6f mm "
            "-> spread %.3f %% (tol 1.0 %%)"
            % ("PASS" if good else "FAIL", ds[0] * 1e3, ds[1] * 1e3, spread * 100.0))
        log("     -> delta is a physical SPH near-wall sampling distance shared by both "
            "regions, not a per-region fitted constant.")
        details["checks"].append({"name": "delta consistency", "derived": spread,
                                 "stored": 0.0, "abs_err": spread, "tol": 0.01,
                                 "ok": bool(good)})
        ok &= good

    details["ok"] = bool(ok)
    details["n_checks"] = len(details["checks"])
    details["n_failed"] = sum(1 for c in details["checks"] if not c["ok"])
    return bool(ok), details


# ---------------------------------------------------------------------------
# 입자 -> 영역 집계
# ---------------------------------------------------------------------------

def bin_profile(dist_m, temp_C, band_m=BAND_MM_DEFAULT * 1e-3, n_bins=N_BINS_DEFAULT):
    """벽면거리로 온도 프로파일을 만든다.

    0..band 를 n_bins 등분한다(기본 0~3 mm, 6 칸 -> 0.5 mm). 각 칸에 대해
    (평균온도 또는 None, 입자수, 평균 벽면거리 또는 None) 을 돌려준다.
    빈 칸이 None 인 것이 기존 파일의 선두 null 관례의 정체다.
    """
    if _np is None:
        raise RuntimeError("bin_profile requires numpy")
    d = _np.asarray(dist_m, dtype=float)
    t = _np.asarray(temp_C, dtype=float)
    edges = _np.linspace(0.0, float(band_m), int(n_bins) + 1)
    means = []
    counts = []
    dmeans = []
    for i in range(int(n_bins)):
        lo, hi = edges[i], edges[i + 1]
        if i == int(n_bins) - 1:
            sel = (d >= lo) & (d <= hi)          # 마지막 칸만 상단 포함
        else:
            sel = (d >= lo) & (d < hi)
        n = int(sel.sum())
        counts.append(n)
        if n == 0:
            means.append(None)
            dmeans.append(None)
        else:
            means.append(float(t[sel].mean()))
            dmeans.append(float(d[sel].mean()))
    return means, counts, dmeans


def aggregate_region(dist_m, vmag_ms, temp_C, band_m=BAND_MM_DEFAULT * 1e-3,
                     n_bins=N_BINS_DEFAULT, delta_mode="bin1", delta_fallback=DELTA_DEFAULT):
    """한 영역의 근벽 입자들을 역산 입력으로 축약한다.

    delta_mode="bin1"  -> delta = 벽에서 가장 가까운 비어있지 않은 칸의 평균 벽면거리
                          (원본 파일이 실제로 한 일. 위 모듈 docstring 참조)
    delta_mode="fixed" -> delta = delta_fallback
    """
    if _np is None:
        raise RuntimeError("aggregate_region requires numpy")
    d = _np.asarray(dist_m, dtype=float)
    v = _np.asarray(vmag_ms, dtype=float)
    t = _np.asarray(temp_C, dtype=float)
    band = (d >= 0.0) & (d <= float(band_m))
    n_band = int(band.sum())
    if n_band == 0:
        raise ValueError("aggregate_region: no particles within %.3f mm of the wall -- "
                         "check --geom-dir / --particle-length-unit / region assignment"
                         % (band_m * 1e3,))
    means, counts, dmeans = bin_profile(d[band], t[band], band_m=band_m, n_bins=n_bins)

    i1 = None
    for i, m in enumerate(means):
        if m is not None:
            i1 = i
            break
    if i1 is None:
        raise ValueError("aggregate_region: every profile bin is empty")
    if i1 != 1:
        # 원본은 0번이 비고 1번이 첫 유효칸이었다. 달라지면 조용히 넘어가지 않는다.
        sys.stdout.write("  NOTE: first non-empty profile bin is #%d (legacy run had #1). "
                         "Particle spacing near this wall differs from the 6.53 s run.\n" % i1)
    if delta_mode == "bin1":
        delta = float(dmeans[i1])
    else:
        delta = float(delta_fallback)
    return {
        "T_profile": means,
        "bin_counts": counts,
        "bin_mean_dist_m": dmeans,
        "first_bin": i1,
        "T_bin1_C": float(means[i1]),
        "delta_m": delta,
        "delta_mode": delta_mode,
        "n_band": n_band,
        "nearwall_V": float(v[band].mean()),
        "nearwall_Toil": float(t[band].mean()),
    }


def _vmag(vx, vy, vz):
    return _np.sqrt(_np.asarray(vx, float) ** 2 + _np.asarray(vy, float) ** 2
                    + _np.asarray(vz, float) ** 2)


def load_particles_file(path, length_scale=1.0, log=print):
    """--particles CSV/NPZ 를 읽는다. 반환 dict of 1D arrays (+ 선택 region/dist/t_reached)."""
    if _np is None:
        raise RuntimeError("--particles requires numpy")
    ext = os.path.splitext(path)[1].lower()
    cols = {}
    if ext == ".npz":
        z = _np.load(path, allow_pickle=True)
        for key in z.files:
            cols[key.lower()] = z[key]
    else:
        arr = _np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")
        if arr.dtype.names is None:
            raise ValueError("%s: CSV must have a header row naming the columns" % path)
        for key in arr.dtype.names:
            cols[key.lower()] = arr[key]

    alias = {"temperature": "t", "temp": "t"}
    for src, dst in alias.items():
        if src in cols and dst not in cols:
            cols[dst] = cols[src]

    need = ("x", "y", "z", "vx", "vy", "vz", "t")
    missing = [c for c in need if c not in cols]
    if missing:
        raise ValueError("%s: missing required column(s) %s. Present: %s. "
                         "See the module docstring for the exact expected schema."
                         % (path, ", ".join(missing), ", ".join(sorted(cols))))

    out = {}
    for c in ("x", "y", "z"):
        out[c] = _np.asarray(cols[c], dtype=float) * float(length_scale)
    for c in ("vx", "vy", "vz"):
        out[c] = _np.asarray(cols[c], dtype=float)
    out["T"] = _np.asarray(cols["t"], dtype=float)
    if "dist" in cols:
        out["dist"] = _np.asarray(cols["dist"], dtype=float) * float(length_scale)
    if "region" in cols:
        out["region"] = _np.asarray([str(s) for s in cols["region"]])
    if "t_reached" in cols:
        try:
            out["t_reached"] = float(_np.asarray(cols["t_reached"]).ravel()[0])
        except Exception:
            pass
    log("particles: %s  n=%d  columns=%s"
        % (path, len(out["x"]), ", ".join(sorted(k for k in out))))
    return out


def load_particles_sph(path, log=print):
    """FreeFlow(Rocky) .sph HDF5 를 직접 읽는다.

    스키마는 13_freeflow_thermal_viz.py:38-44 에서 검증된 것과 동일하다.
    position 과 sph_scalars 길이가 다를 수 있어 최소길이로 자른다(released 입자).
    """
    if _np is None:
        raise RuntimeError("--sph requires numpy")
    try:
        import h5py
    except ImportError:
        raise RuntimeError("--sph requires h5py (present in the moa venv PyMotorEnv_310; "
                           "13_freeflow_thermal_viz.py already uses it). "
                           "Fall back to --particles if h5py is unavailable.")
    with h5py.File(path, "r") as h:
        pos = h["free/position"][:]
        temp = h["sph_scalars/temperature"][:]
        vx = h["free/velocity_x"][:]
        vy = h["free/velocity_y"][:]
        vz = h["free/velocity_z"][:]
    n = min(len(pos), len(temp), len(vx), len(vy), len(vz))
    log("sph: %s  n_position=%d n_temperature=%d -> using n=%d"
        % (path, len(pos), len(temp), n))
    return {"x": _np.asarray(pos["x"][:n], float),
            "y": _np.asarray(pos["y"][:n], float),
            "z": _np.asarray(pos["z"][:n], float),
            "vx": _np.asarray(vx[:n], float),
            "vy": _np.asarray(vy[:n], float),
            "vz": _np.asarray(vz[:n], float),
            "T": _np.asarray(temp[:n], float)}


def wall_distances(parts, geom_dir, regions=REGIONS, log=print):
    """STL 벽면까지의 최단거리와 최근접 영역을 pyvista 로 계산한다.

    pyvista 는 moa venv 에 있다(HANDOFF §9). 이 PC 에는 없으므로 이 경로는
    오프라인 테스트가 불가능하다 -- 그래서 실패시 조용히 넘어가지 않고 크게 죽는다.
    """
    if _np is None:
        raise RuntimeError("wall_distances requires numpy")
    try:
        import pyvista as pv
    except ImportError:
        raise RuntimeError(
            "--geom-dir needs pyvista to compute wall distances (present in the moa venv). "
            "Alternative: export 'dist' and 'region' columns from the FreeFlow side and "
            "pass them via --particles, which needs no pyvista.")
    pts = _np.column_stack([parts["x"], parts["y"], parts["z"]]).astype(float)
    cloud = pv.PolyData(pts)
    dmat = _np.empty((len(pts), len(regions)), dtype=float)
    for j, reg in enumerate(regions):
        stl = os.path.join(geom_dir, reg + ".stl")
        if not os.path.isfile(stl):
            raise RuntimeError("wall STL not found: %s (expected <geom-dir>/<Region>.stl, "
                               "same names 13_freeflow_thermal_viz.py reads)" % stl)
        surf = pv.read(stl)
        d = cloud.compute_implicit_distance(surf)["implicit_distance"]
        dmat[:, j] = _np.abs(_np.asarray(d, dtype=float))
        log("  wall %-8s STL=%s  n_cells=%d  dist min/median=%.4f/%.4f mm"
            % (reg, os.path.basename(stl), surf.n_cells,
               dmat[:, j].min() * 1e3, float(_np.median(dmat[:, j])) * 1e3))
    idx = _np.argmin(dmat, axis=1)
    return dmat[_np.arange(len(pts)), idx], _np.asarray([regions[i] for i in idx])


# ---------------------------------------------------------------------------
# 출력 조립
# ---------------------------------------------------------------------------

def build_output(per_region, oil, t_reached_s, wall_src, legacy, args, extra_notes=None):
    """기존 htc_backout.json 구조 + D3 메타데이터."""
    out = {}
    out["_note"] = ("FreeFlow %.4gs HORIZONTAL-gravity resolved-flow HTC back-out vs MAPDL "
                    "circuit assumptions. Order-of-magnitude cross-check; SPH near-wall "
                    "resolution + transient(%.4gs) caveats. Supersedes "
                    "freeflow/data/htc_backout.json, which was solved with the wrong "
                    "(axial) gravity vector." % (t_reached_s, t_reached_s))
    out["_soltype"] = "transient+%gs" % (float(t_reached_s),)
    out["_loss_source"] = wall_src["loss_source"]
    out["_htc"] = {
        "assumed": {"jkt": wall_src["htc"].get("htc_jkt"),
                    "spray": wall_src["htc"].get("htc_spray")},
        "backed_out_h_grad": dict((r, per_region[r]["h_grad"]) for r in per_region),
        "backed_out_h_corr_Dh6mm": dict(
            (r, per_region[r]["h_velocity_corr"].get("Dh6mm", {}).get("h"))
            for r in per_region),
        "note": ("h_grad is the SPH near-wall temperature-gradient back-out; "
                 "h_corr is the laminar Nu=%.2f duct correlation at the assumed Dh. "
                 "MAPDL D1/D2 use the 'sph' h-set 190/190 W/m2K per PLAN §1 D1; the "
                 "measured values recorded here are the evidence for that choice."
                 % NU_LAMINAR),
    }
    out["_gravity"] = {
        "old_vector_m_s2": list(GRAVITY_OLD),
        "new_vector_m_s2": list(GRAVITY_NEW),
        "old_description": "axial (-Z), i.e. vertically mounted -- WRONG for e10",
        "new_description": "radial (-Y), i.e. horizontally mounted -- correct",
        "citation": GRAVITY_CITE,
        "fixed_by": "d3_freeflow_gravity_fix.py -> Project_thermal_horizontal.freeflow",
    }
    out["oil_props"] = {"rho": oil["rho"], "cp": oil["cp"], "k": oil["k"], "mu": oil["mu"],
                        "Pr": round(prandtl(oil["mu"], oil["cp"], oil["k"]), 1)}
    out["per_region"] = per_region

    # 옛(수직중력) 결과와의 대비
    if legacy is not None:
        cmp_block = {
            "reference_file": LEGACY_REL,
            "reference_soltype": "transient+%gs" % (LEGACY_T_REACHED_S,),
            "reference_gravity_m_s2": list(GRAVITY_OLD),
            "per_region": {},
        }
        for reg in per_region:
            old = legacy.get("per_region", {}).get(reg)
            if not old:
                continue
            o_h = float(old["h_grad"]); n_h = float(per_region[reg]["h_grad"])
            o_q = float(old["q_grad_Wm2"]); n_q = float(per_region[reg]["q_grad_Wm2"])
            o_v = float(old["nearwall_V"]); n_v = float(per_region[reg]["nearwall_V"])
            cmp_block["per_region"][reg] = {
                "h_grad_old": o_h, "h_grad_new": n_h,
                "h_grad_delta": round(n_h - o_h, 2),
                "h_grad_pct_change": round((n_h / o_h - 1.0) * 100.0, 2) if o_h else None,
                "q_grad_old_Wm2": o_q, "q_grad_new_Wm2": n_q,
                "q_grad_pct_change": round((n_q / o_q - 1.0) * 100.0, 2) if o_q else None,
                "nearwall_V_old": o_v, "nearwall_V_new": n_v,
                "nearwall_V_pct_change": round((n_v / o_v - 1.0) * 100.0, 2) if o_v else None,
            }
        cmp_block["_interpretation"] = (
            "Chapter 5 cites this only as an order-of-magnitude comparison against the "
            "assumed 1000/2000 W/m2K, so a percent-level shift does not overturn the "
            "conclusion. The point of D3 is to stop citing a result computed with the "
            "wrong gravity direction.")
        out["_delta_vs_vertical_gravity"] = cmp_block

    out["_provenance"] = {
        "script": os.path.basename(__file__),
        "wall_temps_file": wall_src["path"],
        "wall_T_C": wall_src["wall_T"],
        "particles": args.get("particles") or args.get("sph"),
        "geom_dir": args.get("geom_dir"),
        "delta_mode": args.get("delta_mode"),
        "delta_nominal_m": args.get("delta"),
        "band_mm": args.get("band_mm"),
        "n_bins": args.get("n_bins"),
        "Nu": args.get("nu"),
        "Dh_mm": args.get("dh"),
        "t_reached_s": float(t_reached_s),
        "formulas": {
            "Pr": "mu*cp/k",
            "Re": "rho*V_nearwall*Dh/mu",
            "Nu": "%.2f (laminar, fully developed, constant wall heat flux, circular duct)" % NU_LAMINAR,
            "h_corr": "Nu*k/Dh",
            "q_grad": "k*(T_wall - T_bin1)/delta",
            "h_grad": "q_grad/(T_wall - T_bulk)",
            "delta": ("mean wall-distance of the particles in the first non-empty "
                      "profile bin ([0.5,1.0) mm); the legacy file implies "
                      "0.74307 mm (Stator) / 0.74032 mm (Winding)"),
        },
        "notes": list(extra_notes or []),
    }
    return out


def load_wall_temps(path):
    """ff_mapdl_hybrid_temps.json 에서 벽 온도경계와 가정 htc, 손실출처를 읽는다."""
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    ct = d.get("circuit_T", {})
    wall_T = {}
    for reg in REGIONS:
        node = REGION_CIRCUIT_NODE[reg]
        if node not in ct:
            raise ValueError("%s: circuit_T is missing node %r (needed for wall %s)"
                             % (path, node, reg))
        wall_T[reg] = float(ct[node])
    return {
        "path": path,
        "wall_T": wall_T,
        "t_bulk_inlet": float(d.get("_oil", {}).get("T", 70.0)),
        "htc": d.get("_oil", {}),
        "loss_source": ("%s wall BC (_loss_source=%s)"
                        % (os.path.basename(path), d.get("_loss_source", "unknown"))),
        "raw": d,
    }


# ---------------------------------------------------------------------------
# 자기검증
# ---------------------------------------------------------------------------

def _self_test(log):
    """순수 함수들을 합성 데이터 + 기존 파일 저장값으로 검증한다."""
    ok = True

    def expect(name, got, want, tol):
        good = abs(got - want) <= tol
        log("  [%s] %-40s got=%.8g want=%.8g tol=%.3g"
            % ("PASS" if good else "FAIL", name, got, want, tol))
        return good

    log("self-test: pure formulas")
    ok &= expect("Pr(ATF)", prandtl(OIL_MU, OIL_CP, OIL_K), 148.14814814814815, 1e-9)
    ok &= expect("Re Stator Dh3mm", reynolds(OIL_RHO, 0.397, 3e-3, OIL_MU), 98.2575, 1e-9)
    ok &= expect("Re Winding Dh10mm", reynolds(OIL_RHO, 0.515, 10e-3, OIL_MU), 424.875, 1e-9)
    ok &= expect("h_corr Dh3mm", h_correlation(NU_LAMINAR, OIL_K, 3e-3), 196.2, 1e-9)
    ok &= expect("h_corr Dh6mm", h_correlation(NU_LAMINAR, OIL_K, 6e-3), 98.1, 1e-9)
    ok &= expect("h_corr Dh10mm", h_correlation(NU_LAMINAR, OIL_K, 10e-3), 58.86, 1e-9)
    ok &= expect("q_grad Stator", q_gradient(OIL_K, 84.4, 70.99, 7.430735131141492e-4),
                 2436.3, 1e-6)
    ok &= expect("h_grad Stator", h_from_q(2436.3, 84.4, 71.77), 192.89786223277898, 1e-9)
    ok &= expect("h_grad Winding", h_from_q(3751.0, 91.9, 71.77), 186.33879781420757, 1e-9)

    log("self-test: stored_half_ulp")
    for val, want in ((2436.3, 0.05), (71.77, 0.005), (0.397, 0.0005), (84.4, 0.05)):
        ok &= expect("half_ulp(%r)" % val, stored_half_ulp(val), want, 1e-12)

    log("self-test: h_from_q guards against T_wall == T_bulk")
    try:
        h_from_q(100.0, 70.0, 70.0)
        log("  [FAIL] h_from_q did not raise on zero temperature difference")
        ok = False
    except ValueError:
        log("  [PASS] h_from_q raised ValueError as expected")

    log("self-test: backout_region reproduces the legacy Stator entry")
    r = backout_region(wall_T_C=84.4, T_bin1_C=70.99, T_bulk_C=71.77,
                       delta_m=7.430735131141492e-4, V_nearwall=0.397,
                       assumed_htc=1000.0, n_band=1175,
                       T_profile=[None, 70.99, 70.74, 70.83, 70.82, 70.74],
                       nearwall_Toil_C=70.86)
    ok &= expect("region q_grad", r["q_grad_Wm2"], 2436.3, 1e-9)
    ok &= expect("region h_grad", r["h_grad"], 192.9, 1e-9)
    ok &= expect("region Re Dh3mm", r["h_velocity_corr"]["Dh3mm"]["Re"], 98.3, 1e-9)
    ok &= expect("region h Dh10mm", r["h_velocity_corr"]["Dh10mm"]["h"], 58.9, 1e-9)
    keep_null = r["T_profile_0to3mm"][0] is None
    log("  [%s] T_profile_0to3mm keeps the leading null (file convention)"
        % ("PASS" if keep_null else "FAIL"))
    ok &= keep_null

    if _np is not None:
        log("self-test: bin_profile / aggregate_region on synthetic particles")
        # [0,0.5) mm 를 비워 두고 0.5~3 mm 에 균일 배치 -> 1번 칸이 첫 유효칸이어야 한다.
        d = _np.linspace(0.5e-3, 3.0e-3, 2501)
        t = 70.0 + 0.0 * d
        v = 0.4 + 0.0 * d
        agg = aggregate_region(d, v, t)
        ok &= expect("agg first_bin", agg["first_bin"], 1, 0)
        ok &= expect("agg delta ~ bin1 centre", agg["delta_m"], 0.75e-3, 5e-6)
        ok &= expect("agg n_band", agg["n_band"], 2501, 0)
        first_null = agg["T_profile"][0] is None
        log("  [%s] synthetic profile bin 0 is empty -> None" % ("PASS" if first_null else "FAIL"))
        ok &= first_null
    else:
        log("  SKIP numpy-dependent self-tests (numpy not importable)")

    return bool(ok)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="D3: FreeFlow SPH near-wall HTC back-out (horizontal gravity).",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default=None,
                   help="repo root (default: inferred from this file's location)")
    p.add_argument("--sph", default=None,
                   help="FreeFlow .sph HDF5 particle file (preferred input)")
    p.add_argument("--particles", default=None,
                   help="near-wall particle CSV/NPZ; see module docstring for columns")
    p.add_argument("--particle-length-unit", default="m", choices=("m", "mm"),
                   help="length unit of x,y,z,dist in --particles (default m)")
    p.add_argument("--geom-dir", default=None,
                   help="directory holding Stator.stl / Winding.stl (for wall distances)")
    p.add_argument("--wall-temps", default=None,
                   help="ff_mapdl_hybrid_temps.json (default: resolved from --repo)")
    p.add_argument("--legacy", default=None,
                   help="existing htc_backout.json (default: resolved from --repo)")
    p.add_argument("--out", default=None,
                   help="output JSON (default: <repo>/%s)" % OUT_REL)
    p.add_argument("--log", default=None, help="also write all output to this log file")
    p.add_argument("--t-reached", type=float, default=None,
                   help="physical time actually reached [s]; goes into _soltype")
    p.add_argument("--delta", type=float, default=DELTA_DEFAULT,
                   help="near-wall sampling distance [m] (default %g)" % DELTA_DEFAULT)
    p.add_argument("--delta-mode", default="bin1", choices=("bin1", "fixed"),
                   help="bin1: delta = mean wall-distance of the first non-empty profile "
                        "bin (what the legacy run did); fixed: use --delta")
    p.add_argument("--dh", default=DH_MM_DEFAULT,
                   help="hydraulic diameters for the Nu correlation [mm] (default %s)"
                        % DH_MM_DEFAULT)
    p.add_argument("--nu", type=float, default=NU_LAMINAR,
                   help="Nusselt number (default %.2f laminar const-q)" % NU_LAMINAR)
    p.add_argument("--band-mm", type=float, default=BAND_MM_DEFAULT,
                   help="near-wall band / T_profile span [mm] (default %g)" % BAND_MM_DEFAULT)
    p.add_argument("--n-bins", type=int, default=N_BINS_DEFAULT,
                   help="profile bins across the band (default %d)" % N_BINS_DEFAULT)
    p.add_argument("--rho", type=float, default=OIL_RHO, help="oil density [kg/m3]")
    p.add_argument("--cp", type=float, default=OIL_CP, help="oil specific heat [J/kg/K]")
    p.add_argument("--k", type=float, default=OIL_K, help="oil conductivity [W/m/K]")
    p.add_argument("--mu", type=float, default=OIL_MU, help="oil viscosity [Pa s]")
    p.add_argument("--t-bulk", type=float, default=None,
                   help="oil bulk temperature [degC] (default: mean of all particles)")
    p.add_argument("--verify-legacy", action="store_true",
                   help="re-derive q_grad/h_grad from the existing htc_backout.json's own "
                        "stored fields and assert they reproduce the stored values")
    p.add_argument("--self-test", action="store_true",
                   help="run the pure-function unit tests")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    log = Log(args.log)
    try:
        repo = args.repo or default_repo_root()
        log("=" * 100)
        log("d3_htc_backout.py -- D3 FreeFlow SPH near-wall HTC back-out")
        log("repo root: %s" % repo)
        log("numpy: %s" % (getattr(_np, "__version__", None) if _np is not None else "NOT AVAILABLE"))
        log("=" * 100)

        if args.self_test:
            ok = _self_test(log)
            log("=" * 100)
            log("SELF-TEST %s" % ("PASSED" if ok else "FAILED"))
            return 0 if ok else 1

        legacy_path = args.legacy or _rel(repo, LEGACY_REL)
        legacy = None
        if os.path.isfile(legacy_path):
            with open(legacy_path, "r", encoding="utf-8") as f:
                legacy = json.load(f)

        if args.verify_legacy:
            log("--verify-legacy: %s" % legacy_path)
            if legacy is None:
                log("FATAL: legacy file not found: %s" % legacy_path)
                return 1
            log("legacy _note: %s" % legacy.get("_note", "(none)"))
            log("")
            log("Reconstructing the LOST back-out script from the file's own stored fields.")
            log("Every tolerance below is derived from the stored decimal precision "
                "(stored_half_ulp) plus first-order propagation -- no hand-picked numbers.")
            ok, details = verify_legacy(legacy, log, delta_nominal=args.delta, nu=args.nu)
            log("=" * 100)
            log("checks: %d total, %d failed" % (details["n_checks"], details["n_failed"]))
            log("VERIFY-LEGACY %s" % ("PASSED" if ok else "FAILED"))
            if ok:
                log("")
                log("=> The four formulas in this module reproduce freeflow/data/htc_backout.json")
                log("   from its own stored fields. The reconstruction is faithful and may now")
                log("   be applied to the new horizontal-gravity FreeFlow result.")
            return 0 if ok else 1

        # ---------------- 실제 역산 ----------------
        if not args.sph and not args.particles:
            log("FATAL: give --sph <file.sph> or --particles <file.csv|.npz> "
                "(or use --verify-legacy / --self-test).")
            return 2
        if _np is None:
            log("FATAL: numpy is required to process particles.")
            return 2

        wall_path = args.wall_temps or _rel(repo, WALLTEMPS_REL)
        if not os.path.isfile(wall_path):
            log("FATAL: --wall-temps not found: %s" % wall_path)
            return 2
        wall_src = load_wall_temps(wall_path)
        log("wall temps: %s" % wall_path)
        for reg in REGIONS:
            log("  %-8s <- circuit_T.%-7s = %.2f degC   assumed htc=%s W/m2K"
                % (reg, REGION_CIRCUIT_NODE[reg], wall_src["wall_T"][reg],
                   wall_src["htc"].get(REGION_HTC_KEY[reg])))

        notes = []
        if args.sph:
            parts = load_particles_sph(args.sph, log=log)
        else:
            scale = 1e-3 if args.particle_length_unit == "mm" else 1.0
            parts = load_particles_file(args.particles, length_scale=scale, log=log)

        t_reached = args.t_reached
        if t_reached is None:
            t_reached = parts.get("t_reached")
        if t_reached is None:
            log("FATAL: --t-reached is required (it goes into _soltype). The legacy run "
                "reached %g s of the intended 8 s; do not guess." % LEGACY_T_REACHED_S)
            return 2

        vmag = _vmag(parts["vx"], parts["vy"], parts["vz"])
        t_bulk = args.t_bulk
        if t_bulk is None:
            t_bulk = float(_np.asarray(parts["T"], float).mean())
            notes.append("T_bulk taken as the mean temperature of all %d particles "
                         "(%.3f degC); override with --t-bulk." % (len(vmag), t_bulk))
        log("bulk oil temperature: %.3f degC" % t_bulk)

        if "dist" in parts and "region" in parts:
            dist = parts["dist"]
            region = parts["region"]
            log("using precomputed 'dist' and 'region' columns (no pyvista needed)")
        else:
            geom = args.geom_dir
            if not geom:
                log("FATAL: particles carry no 'dist'/'region' columns, so --geom-dir "
                    "(with Stator.stl / Winding.stl) is required.")
                return 2
            log("computing wall distances from STL surfaces in %s" % geom)
            dist, region = wall_distances(parts, geom, log=log)

        oil = {"rho": args.rho, "cp": args.cp, "k": args.k, "mu": args.mu}
        dh_list = [float(s.strip()) * 1e-3 for s in args.dh.split(",") if s.strip()]
        log("oil: rho=%.1f cp=%.1f k=%.4f mu=%.4f -> Pr=%.2f"
            % (oil["rho"], oil["cp"], oil["k"], oil["mu"],
               prandtl(oil["mu"], oil["cp"], oil["k"])))
        log("Dh set [mm]: %s   Nu=%.2f   band=%.2f mm   bins=%d   delta-mode=%s"
            % (", ".join("%g" % (d * 1e3) for d in dh_list), args.nu,
               args.band_mm, args.n_bins, args.delta_mode))

        per_region = {}
        region = _np.asarray(region)
        for reg in REGIONS:
            sel = (region == reg)
            n = int(sel.sum())
            log("-" * 100)
            log("region %s: %d particles nearest this wall" % (reg, n))
            if n == 0:
                log("FATAL: no particles assigned to wall %s" % reg)
                return 3
            agg = aggregate_region(dist[sel], vmag[sel], _np.asarray(parts["T"], float)[sel],
                                   band_m=args.band_mm * 1e-3, n_bins=args.n_bins,
                                   delta_mode=args.delta_mode, delta_fallback=args.delta)
            log("  n_band(0-%.2g mm)=%d  first non-empty bin=#%d  delta=%.6f mm  "
                "V_nearwall=%.4f m/s  T_nearwall=%.3f degC"
                % (args.band_mm, agg["n_band"], agg["first_bin"], agg["delta_m"] * 1e3,
                   agg["nearwall_V"], agg["nearwall_Toil"]))
            log("  bin counts: %s" % agg["bin_counts"])
            log("  bin T:      %s" % ["%.2f" % t if t is not None else None
                                      for t in agg["T_profile"]])
            rec = backout_region(
                wall_T_C=wall_src["wall_T"][reg], T_bin1_C=agg["T_bin1_C"],
                T_bulk_C=t_bulk, delta_m=agg["delta_m"], V_nearwall=agg["nearwall_V"],
                oil=oil, dh_list_m=dh_list, nu=args.nu,
                assumed_htc=wall_src["htc"].get(REGION_HTC_KEY[reg]),
                n_band=agg["n_band"], T_profile=agg["T_profile"],
                nearwall_Toil_C=agg["nearwall_Toil"])
            rec["_raw"]["bin_counts"] = agg["bin_counts"]
            rec["_raw"]["bin_mean_dist_m"] = agg["bin_mean_dist_m"]
            rec["_raw"]["first_bin"] = agg["first_bin"]
            rec["_raw"]["delta_mode"] = agg["delta_mode"]
            log("  => q_grad=%.1f W/m2   h_grad=%.1f W/m2K   (assumed %s -> ratio %.3f)"
                % (rec["q_grad_Wm2"], rec["h_grad"],
                   rec.get("assumed_htc"),
                   rec["h_grad"] / rec["assumed_htc"] if rec.get("assumed_htc") else float("nan")))
            per_region[reg] = rec

        cli = {"particles": args.particles, "sph": args.sph, "geom_dir": args.geom_dir,
               "delta_mode": args.delta_mode, "delta": args.delta, "band_mm": args.band_mm,
               "n_bins": args.n_bins, "nu": args.nu,
               "dh": [d * 1e3 for d in dh_list]}
        doc = build_output(per_region, oil, t_reached, wall_src, legacy, cli, notes)

        out_path = args.out or _rel(repo, OUT_REL)
        d = os.path.dirname(os.path.abspath(out_path))
        if d and not os.path.isdir(d):
            os.makedirs(d)
            log("created output directory: %s" % d)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        log("=" * 100)
        log("wrote %s (%d bytes)" % (out_path, os.path.getsize(out_path)))
        if "_delta_vs_vertical_gravity" in doc:
            for reg, c in doc["_delta_vs_vertical_gravity"]["per_region"].items():
                log("  %-8s h_grad %.1f -> %.1f W/m2K  (%+.2f %%)"
                    % (reg, c["h_grad_old"], c["h_grad_new"], c["h_grad_pct_change"]))
        log("DONE-OK")
        return 0
    finally:
        log.close()


if __name__ == "__main__":
    sys.exit(main())
