# -*- coding: utf-8 -*-
"""D2 -- 슬롯 내 AC 동손 분포 주입: 균일(uniform) vs 턴별(turnwise) 비교.

계획서 `PLAN_20260906_thesis_thermal.md` §D2 의 실행 스크립트.
16,000 rpm 에서 {230.05, 460.0} A x {uniform, turnwise} = **4 런**, 전부 정상상태
(steady), h 세트는 base 고정, 나머지 조건은 완전히 동일하게 두어 "슬롯 내 분포"
하나만 변수로 남긴다.

핵심 설계
---------
1. **턴 인덱스는 메시에 없다.**  `03_stl_to_cdb.py` 는 NBLOCK/EBLOCK 만 쓰고
   컴포넌트를 만들지 않으므로 mat 3 의 유일한 식별자는 `MAT=3` 뿐이다.  따라서
   턴 인덱스를 **반경 밴딩으로 복원**한다.  밴드는 하드코딩하지 않고 **메시에서
   실측**한다(체적가중 0.5 / 99.5 % 분위수).
2. **부분체적(fractional) 비닝.**  메시가 층 피치(약 2.13 mm)에 비해 성기므로
   (`03_stl_to_cdb.py` 의 MESH_MIN/MAX = 1.8 / 5.0 mm) 요소 중심 하드 비닝은 빈
   밴드와 체적 편차를 낳는다.  각 tet 내부를 S 개 표본점으로 나눠 밴드별 체적
   분율 `frac[e,k]` 을 구하고
       V_k = sum_e frac[e,k] * vol_e ,   q_e = sum_k frac[e,k] * P_k / V_k
   로 요소마다 다른 HGEN 을 준다.  이러면
       sum_e q_e * vol_e == sum_k P_k
   가 **구성상 정확히** 성립한다(메시 성김과 무관).
3. **주입은 요소별 BFE 매크로**(`BFE,<eid>,HGEN,1,<q>`) + `mapdl.input()`.
   q 가 요소마다 다르므로 mat 3 에 blanket `bfe("ALL", ...)` 는 쓰지 않는다.
4. uniform 런은 **동일한 마스크·동일한 체적**에 `q = sum(P_turn)/V_active` 를
   준다.  코드 경로가 한 줄만 다르므로 비교가 오염되지 않는다.
5. 주입값은 `fea_per_turn_raw` **그대로**다.  이 값은 AC 만이 아니라 **DC+AC 합,
   활성길이 전용**이며(ActiveXParametersMotorCADv261.txt:3307), 6턴 1병렬 동일
   단면이라 DC 성분은 턴별로 정확히 같다.  즉 (균일 DC + 턴별 AC) == (턴별 DC+AC).
   엔드부는 `ts_dc_end_kW*1000` 을 별도로 엔드 영역에 준다.

물리적 경고 (JSON `_physical_warning` 에도 들어간다)
----------------------------------------------------
460 A 정격점의 총 동손은 68.6 + 18.5 = **87 kW** 로, 검증된 하이브리드 런(3.35 kW,
권선 152.2 °C)의 26 배다.  절대 온도는 수백~수천 °C 의 **비물리 값**이 나온다.
그러나 모델이 완전 선형(k 상수, h 상수, OIL 70 °C 단일 Dirichlet)이므로 중첩이
정확히 성립하고, uniform 대 turnwise 의 차이는 총량에 정확히 비례한다.  따라서
JSON 은 절대온도와 함께 **정규화 K/kW 민감도**를 반드시 같이 낸다.

사용법
------
    python d2_ac_turnwise.py --dry-run              # Ansys 없이 전 경로 검증
    python d2_ac_turnwise.py --cdb D:\\KDH\\simVary\\Ansys_Thermal\\ff_e10_mesh_v2

python 3.10 문법만 사용한다 (match / X|Y 어노테이션 / 3.11+ stdlib 금지).
같은 디렉터리의 `jeet_map_loader.py`, `thesis_style.py` 만 import 한다.
`ansys.dpf.core` 는 절대 import 하지 않는다.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import traceback

import numpy as np

import jeet_map_loader as jm

# =========================================================================== #
#  1. 상수 -- 전부 04_mapdl_thermal.py 에서 그대로 가져온 실측/검증값            #
# =========================================================================== #

# --- 재료 번호 (04_mapdl_thermal.py:35) ---
M_ST, M_MG, M_CO, M_SH, M_RO = 1, 2, 3, 4, 5
MAT_NAMES = {M_ST: "stator", M_MG: "magnet", M_CO: "winding",
             M_SH: "shaft", M_RO: "rotor"}

# --- 기하 (04_mapdl_thermal.py:36-41).  단위 m.  z=0 은 스택 중심이 아니다. ---
R_STA_OUT = 0.0990
R_STA_IN = 0.0713
R_ROT_OUT = 0.07027
R_SHAFT = 0.023455
Z_ST0, Z_ST1 = -0.2075, -0.0575
STACK = Z_ST1 - Z_ST0                    # 0.150
ZC = 0.5 * (Z_ST0 + Z_ST1)               # -0.1325  <- 스택 중심

# --- 재료 물성 (04:43-47) : (KXX, C, DENS) ---
MATS = {M_ST: (25.0, 460.0, 7650.0),
        M_MG: (9.0, 460.0, 7500.0),
        M_CO: (5.0, 385.0, 4480.0),      # 균질화 슬롯체 (fill 0.5)
        M_SH: (52.0, 460.0, 7870.0),
        M_RO: (25.0, 460.0, 7650.0)}

# --- 오일 회로 (04:48-67).  HTC_BIG 은 수치 장치이므로 절대 바꾸지 않는다. ---
OIL_T = 70.0
RHO_OIL, CP_OIL = 825.0, 2000.0
MDOT_OIL = 0.11
HTC_BIG = 1e4
K_AIR, GAP_G = 0.03, 0.0007
G_JKT_OIL = 0.60 * MDOT_OIL * CP_OIL     # 132.0 W/K
G_SPRAY_OIL = 0.40 * MDOT_OIL * CP_OIL   # 88.0 W/K
G_SHF_OIL = 40.0                         # W/K
A_GAP = 2.0 * math.pi * R_STA_IN * STACK
G_GAP = K_AIR * A_GAP / GAP_G            # 2.880 W/K
C_JKT = 0.20e-3 * RHO_OIL * CP_OIL
C_SPRAY = 0.15e-3 * RHO_OIL * CP_OIL
C_SHF = 200.0
TOL = 1e-5
RT = 8e-4

# --- h 세트.  계획 D1 스펙(라인 35/40)은 sph = 190/190/250 이라 적혀 있고,
#     실측 htc_backout.json 은 192.8/186.3 이다.  스펙대로 190/190 을 돌리고
#     실측값은 JSON 메타데이터에 남긴다(계획 라인 17 과의 불일치 기록). ---
HTC_SETS = {"base": {"jkt": 1000.0, "spray": 2000.0, "splash": 250.0},
            "sph": {"jkt": 190.0, "spray": 190.0, "splash": 250.0}}
HTC_MEASURED = {"jkt": 192.8, "spray": 186.3,
                "source": "freeflow/data/htc_backout.json (SPH near-wall gradient)",
                "note": ("plan line 17 says 193/186, plan D1 spec lines 35/40 say "
                         "190/190; this run uses the D1 spec value and records the "
                         "measurement here")}

# --- D2 고유 기본값 ---
DEF_SPEED = 16000
DEF_CURRENTS = (230.05, 460.0)
DEF_NTURNS = 6
DEF_SAMPLES = 64
DEF_SEED = 20260907
DEF_MODES = ("uniform", "turnwise")

# --- 예측 밴드(검증용 창).  D2 조사보고 §1.2: 72.267 ~ 85.067 mm.
#     Icepak 카브는 71.2 ~ 91 mm(여유 애뉼러스).  실측이 이 창을 벗어나면 경고. ---
BAND_EXPECT_M = (0.0723, 0.0851)
BAND_WINDOW_M = (0.0715, 0.0880)

# --- sanity 판정 기준 (스펙) ---
VOL_BALANCE_TOL = 0.25       # 밴드 체적이 1/K 의 +-25 % 안
STRADDLE_MAX_FRAC = 0.20     # 전이층 체적 / V_active < 20 %
INV_REL_TOL = 1e-9           # sum(q*V) == sum(P) 상대 허용오차
MIN_ELEM_PER_BAND_SOFT = 100

# --- 물리 경고 문구 ---
PHYS_WARNING = (
    "Absolute temperatures at these operating points are NON-PHYSICAL. At 16 krpm / "
    "460 A the total copper loss is 87.0 kW versus 3.35 kW in the validated hybrid "
    "run (winding 152.2 degC), a factor of 26. The model is exactly linear "
    "(constant k, constant h, single Dirichlet OIL node at 70 degC), so the "
    "uniform-vs-turnwise DIFFERENCE scales exactly with the injected total and the "
    "comparison remains valid. Cite the normalized K/kW sensitivities and the "
    "temperature-rise ratio, not the absolute degC.")

LOSS_SOURCE = ("JEET_ACLoss_Ref_Map_Summary.json phase36 FullFEA -- fea_per_turn_raw "
               "(DC+AC per turn, active length only) for the slot region, "
               "ts_dc_end_kW for the end region, speed-scaled iron/magnet")

LOSS_CAVEAT = (
    "Iron and magnet losses use the plan's speed-only rule fe_s=1856*(n/15000)^1.5, "
    "fe_r=74*(n/15000)^1.5, pm=3385*0.17*(n/15000)^2 -- current independent. At "
    "16 krpm / 460 A the plan section 2 R1 values are fe_s 2619 W (rule is 22 % low), "
    "fe_r 89 W, pm 1382 W (rule is 53 % low). At these copper loss levels fe+pm is "
    "under 4 % of the total so the D2 comparison is insensitive to it, but the "
    "absolute temperatures inherit the bias.")


# =========================================================================== #
#  2. 로깅 -- stdout 과 --log 파일에 동시에.  moa 는 무인 실행한다.             #
# =========================================================================== #

class Logger(object):
    """stdout + 파일 동시 출력.  cp949 콘솔에서도 죽지 않는다."""

    def __init__(self, path=None):
        self.path = path
        self.fh = None
        self.t0 = time.time()
        if path:
            d = os.path.dirname(os.path.abspath(path))
            if d and not os.path.isdir(d):
                os.makedirs(d)
            self.fh = open(path, "w", encoding="utf-8")
        try:                                   # 한글이 섞여도 콘솔에서 안 죽게
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    def __call__(self, *args):
        msg = " ".join(str(a) for a in args)
        line = "[%7.1fs] %s" % (time.time() - self.t0, msg)
        try:
            print(line)
        except Exception:
            enc = getattr(sys.stdout, "encoding", None) or "ascii"
            print(line.encode(enc, "replace").decode(enc, "replace"))
        try:
            sys.stdout.flush()
        except Exception:
            pass
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()

    def raw(self, text):
        """타임스탬프 없이 (sanity 표 등)."""
        try:
            print(text)
        except Exception:
            enc = getattr(sys.stdout, "encoding", None) or "ascii"
            print(text.encode(enc, "replace").decode(enc, "replace"))
        if self.fh:
            self.fh.write(text + "\n")
            self.fh.flush()

    def close(self):
        if self.fh:
            try:
                self.fh.close()
            except Exception:
                pass
            self.fh = None


# =========================================================================== #
#  3. 순수 numpy 메시/비닝 수학 -- MAPDL 없이 단독으로 시험 가능한 부분          #
# =========================================================================== #

def tet_corner_volumes(corners):
    """(Ne,4,3) 코너 좌표 -> (Ne,) 체적 [m^3].

    03/03b 가 tet10 중간절점을 직선화해 두었으므로(`03_stl_to_cdb.py:69-72`,
    `03b_rotor_from_maxwell.py:103 SecondOrderLinear=1`) 코너 4점 사면체 체적이
    정확하다.
    """
    c = np.asarray(corners, dtype=np.float64)
    a = c[:, 1] - c[:, 0]
    b = c[:, 2] - c[:, 0]
    d = c[:, 3] - c[:, 0]
    return np.abs(np.einsum("ij,ij->i", np.cross(a, b), d)) / 6.0


def tet_samples(n_samples=DEF_SAMPLES, seed=DEF_SEED):
    """사면체 내부 균일 표본의 무게중심 좌표 (S,4).  Dirichlet(1,1,1,1)."""
    rng = np.random.default_rng(int(seed))
    e = rng.exponential(size=(int(n_samples), 4))
    return e / e.sum(axis=1, keepdims=True)


def sample_radii(corners, lam, chunk=20000):
    """(Ne,4,3) 코너 + (S,4) 무게중심 -> (Ne,S) 표본 반경 [m]."""
    corners = np.asarray(corners, dtype=np.float64)
    n = corners.shape[0]
    out = np.empty((n, lam.shape[0]), dtype=np.float64)
    for i in range(0, n, chunk):
        c = corners[i:i + chunk]
        p = np.einsum("sk,nkd->nsd", lam, c)          # (n,S,3)
        out[i:i + chunk] = np.hypot(p[:, :, 0], p[:, :, 1])
    return out


def _vol_weighted_quantiles(values, weights, qs):
    """체적가중 분위수.  잡요소 몇 개에 밴드가 끌려가지 않게 한다."""
    v = np.asarray(values, dtype=np.float64).ravel()
    w = np.asarray(weights, dtype=np.float64).ravel()
    order = np.argsort(v, kind="stable")
    vs = v[order]
    cw = np.cumsum(w[order])
    tot = float(cw[-1])
    out = []
    for q in qs:
        idx = int(np.searchsorted(cw, q * tot, side="left"))
        if idx < 0:
            idx = 0
        if idx > len(vs) - 1:
            idx = len(vs) - 1
        out.append(float(vs[idx]))
    return out


def band_from_mesh(r_s, vol_act, qlo=0.005, qhi=0.995):
    """(Ne,S) 표본반경 + (Ne,) 체적 -> (r_lo, r_hi) [m], 메시 실측 밴드.

    무게중심 하드 비닝에서는 요소당 반경이 하나뿐이라 (Ne,) 1차원이 들어온다.
    S=1 인 (Ne,1) 로 보고 그대로 처리한다.
    """
    r_s = np.asarray(r_s, dtype=np.float64)
    if r_s.ndim == 1:
        r_s = r_s[:, None]
    S = r_s.shape[1]
    w = np.repeat(np.asarray(vol_act, dtype=np.float64) / float(S), S)
    lo, hi = _vol_weighted_quantiles(r_s, w, (qlo, qhi))
    if not (hi > lo):
        raise ValueError("degenerate radial band from mesh: r_lo=%.6g r_hi=%.6g "
                         "-- material 3 has no radial extent inside the stack"
                         % (lo, hi))
    return float(lo), float(hi)


def equal_volume_edges(r_s, vol_act, nturns):
    """체적을 균등 분할하는 반경 경계 (등간격이 아니라 등체적).

    헤어핀 6 층은 도체 단면이 서로 같으므로 **각 층이 구리 체적의 정확히 1/6** 을
    차지한다. 따라서 물리적 층 경계에 대응하는 것은 등간격 반경이 아니라 등체적이다.
    메시 무게중심이 특정 반경에 뭉치면 등간격 분할은 밴드 체적이 0.12~0.20 으로
    벌어지고(moa 실측, 편차 28 %), 그러면 밴드마다 발열 밀도가 최대 1.4 배까지
    틀어져 T1 대 T6 비교 자체가 오염된다.
    """
    r_s = np.asarray(r_s, dtype=np.float64)
    if r_s.ndim == 1:
        r_s = r_s[:, None]
    S = r_s.shape[1]
    w = np.repeat(np.asarray(vol_act, dtype=np.float64) / float(S), S)
    q = np.linspace(0.0, 1.0, int(nturns) + 1)
    return np.asarray(_vol_weighted_quantiles(r_s, w, q), dtype=np.float64)


def turn_fractions(r_s, edges):
    """(Ne,S) 표본반경 -> (Ne,K) 밴드별 체적 분율.  행합 = 1.

    밴드 밖 표본은 끝 밴드로 흡수한다(clip).  손실이 사라지지 않게 하려면
    반드시 완전 분할이어야 한다.
    """
    edges = np.asarray(edges, dtype=np.float64)
    K = len(edges) - 1
    r = np.clip(r_s, edges[0], edges[-1])
    k = np.searchsorted(edges, r, side="right") - 1
    k = np.clip(k, 0, K - 1)
    S = float(r_s.shape[1])
    frac = np.empty((r_s.shape[0], K), dtype=np.float64)
    for kk in range(K):
        frac[:, kk] = (k == kk).sum(axis=1) / S
    rs = frac.sum(axis=1, keepdims=True)
    rs[rs <= 0.0] = 1.0
    return frac / rs


def hard_fractions(r_cen, edges):
    """계획서 문자 그대로의 요소중심 하드 비닝 (Ne,K), 행마다 1개만 1.0."""
    edges = np.asarray(edges, dtype=np.float64)
    K = len(edges) - 1
    r = np.clip(np.asarray(r_cen, dtype=np.float64), edges[0], edges[-1])
    k = np.clip(np.searchsorted(edges, r, side="right") - 1, 0, K - 1)
    frac = np.zeros((len(r), K), dtype=np.float64)
    frac[np.arange(len(r)), k] = 1.0
    return frac


def band_volumes(frac, vol_act):
    """(Ne,K) x (Ne,) -> (K,) 밴드 체적 [m^3]."""
    return (frac * np.asarray(vol_act, dtype=np.float64)[:, None]).sum(axis=0)


def q_turnwise(frac, V_k, P_turn):
    """요소별 발열밀도 [W/m^3].  sum_e q_e*V_e == sum_k P_k 가 정확히 성립."""
    V_k = np.asarray(V_k, dtype=np.float64)
    P_turn = np.asarray(P_turn, dtype=np.float64)
    if len(P_turn) != len(V_k):
        raise ValueError(
            "turn-wise injection needs one loss value per radial band: the map gives "
            "%d per-turn values (fea_per_turn_raw) but the mesh was banded into %d "
            "bands. Set --nturns %d, or run --modes uniform only."
            % (len(P_turn), len(V_k), len(P_turn)))
    if np.any(V_k <= 0.0):
        bad = [int(i) for i in np.where(V_k <= 0.0)[0]]
        raise ValueError("empty radial band(s) %s -- cannot build a turn-wise "
                         "heat generation vector. Re-run with --binning fractional "
                         "and/or more --samples, or check the measured band."
                         % (bad,))
    return frac.dot(P_turn / V_k)


def q_uniform(n_elem, P_total, V_active):
    """균일 주입.  turnwise 와 동일한 마스크/체적을 쓰므로 총량이 정확히 같다."""
    if V_active <= 0.0:
        raise ValueError("V_active <= 0 -- material 3 has no volume inside the stack")
    return np.full(int(n_elem), float(P_total) / float(V_active), dtype=np.float64)


def straddle_volume(corners, vol, z_lo, z_hi):
    """스택 경계면(z_lo / z_hi)을 가로지르는 요소들의 체적 합 [m^3].

    이 값이 크면 요소가 스택면을 크게 걸친다 = 메시가 성기다는 뜻.  총량 보존은
    여전히 정확하지만 축방향 공간분해능 신뢰도가 떨어지므로 반드시 보고한다.
    """
    z = np.asarray(corners, dtype=np.float64)[:, :, 2]
    zmin = z.min(axis=1)
    zmax = z.max(axis=1)
    cross = ((zmin < z_lo) & (zmax > z_lo)) | ((zmin < z_hi) & (zmax > z_hi))
    return float(np.asarray(vol, dtype=np.float64)[cross].sum()), int(cross.sum())


# =========================================================================== #
#  4. 밴딩 조립 + sanity 리포트                                                 #
# =========================================================================== #

def build_binning(tab, nturns, samples, seed, binning, log, band_edges="width"):
    """요소표 -> 밴딩 결과 dict.  MAPDL 을 쓰지 않는다(드라이런 공용)."""
    emat = tab["emat"]
    cen = tab["cen"]
    vol = tab["vol"]
    corners = tab["corners"]

    is_co = (emat == M_CO)
    zc_e = cen[:, 2]
    act = is_co & (zc_e >= Z_ST0) & (zc_e <= Z_ST1)
    end = is_co & ~act                       # 완전 분할: 체적 누락 0

    n_act = int(act.sum())
    n_end = int(end.sum())
    if n_act == 0:
        raise RuntimeError(
            "no material-3 elements with centroid inside the stack z-band "
            "[%.4f, %.4f] m. Check Z_ST0/Z_ST1 and the CDB." % (Z_ST0, Z_ST1))

    vol_act = vol[act]
    vol_end = vol[end]
    V_act = float(vol_act.sum())
    V_end = float(vol_end.sum())

    # Fractional binning samples points INSIDE each tet, so it needs per-element corner
    # coordinates. On this CDB the cells_dict connectivity does not line up with
    # enum/material_type (see element_table), so corners[act] would be other elements'
    # corners and both the band window and the fractions would be garbage -- observed as
    # a measured radius span of 0.04 .. 98.97 mm where the winding band is 72 .. 85 mm.
    # Fall back to centroid binning, which only needs pyvista's cell_centers().
    trust = bool(tab.get("conn_trustworthy", True))
    if binning != "hard" and not trust:
        log("  [warn] connectivity is not trustworthy on this mesh -> forcing "
            "--binning hard (centroid). Fractional sampling needs per-element corners.")
        binning = "hard"

    r_cen = np.hypot(cen[act, 0], cen[act, 1])
    if binning == "hard":
        # one "sample" per element = its centroid, so every downstream reporting path
        # (band window, measured radius range) keeps working unchanged.
        r_s = r_cen[:, None]
        r_lo, r_hi = band_from_mesh(r_s, vol_act)
        edges = (equal_volume_edges(r_s, vol_act, nturns) if band_edges == "volume"
                 else np.linspace(r_lo, r_hi, int(nturns) + 1))
        frac = hard_fractions(r_cen, edges)
        binning_tag = ("hard-centroid" + ("" if trust else " (forced: untrusted conn)")
                       + ("/equal-volume-edges" if band_edges == "volume" else ""))
    else:
        mb = n_act * int(samples) * 8 / 1e6
        log("binning: %d active elements x %d samples = %.0f MB of sample radii "
            "(lower --samples if memory is tight)" % (n_act, int(samples), mb))
        lam = tet_samples(samples, seed)
        r_s = sample_radii(corners[act], lam)
        r_lo, r_hi = band_from_mesh(r_s, vol_act)
        edges = (equal_volume_edges(r_s, vol_act, nturns) if band_edges == "volume"
                 else np.linspace(r_lo, r_hi, int(nturns) + 1))
        frac = turn_fractions(r_s, edges)
        binning_tag = ("fractional-S%d" % int(samples)
                       + ("/equal-volume-edges" if band_edges == "volume" else ""))

    V_k = band_volumes(frac, vol_act)
    n_k = [int((frac[:, k] > 0.0).sum()) for k in range(int(nturns))]

    r_min = float(r_s.min())
    r_max = float(r_s.max())
    strad_V, strad_n = straddle_volume(corners[is_co], vol[is_co], Z_ST0, Z_ST1)

    out = {
        "act": act, "end": end, "frac": frac,
        "vol_act": vol_act, "vol_end": vol_end,
        "V_act": V_act, "V_end": V_end, "V_k": V_k,
        "n_act": n_act, "n_end": n_end, "n_k": n_k,
        "edges": edges, "r_lo": r_lo, "r_hi": r_hi,
        "r_min": r_min, "r_max": r_max,
        # S comes from r_s, NOT from --samples: hard/centroid binning has S=1 regardless
        # of what --samples says, and np.histogram needs weights shaped like the data.
        "r_s_hist": np.histogram(r_s.ravel(),
                                 bins=32, range=(r_lo, r_hi),
                                 weights=np.repeat(vol_act / float(r_s.shape[1]),
                                                   int(r_s.shape[1])))[0],
        "binning": binning_tag, "samples": int(r_s.shape[1]), "seed": int(seed),
        "nturns": int(nturns),
        "straddle_V": strad_V, "straddle_n": strad_n,
        "n_mat3": int(is_co.sum()),
        "V_mat3": float(vol[is_co].sum()),
    }
    del r_s
    return out


def sanity_report(binf, tab, log):
    """moa 가 10 초에 판정할 수 있는 블록을 stdout 에 찍고 판정 dict 를 돌려준다."""
    K = binf["nturns"]
    V_act = binf["V_act"]
    V_k = binf["V_k"]
    edges = binf["edges"]
    cm3 = 1e6

    log.raw("")
    log.raw("=" * 78)
    log.raw(" D2 MESH / BINNING SANITY BLOCK  (read this in 10 seconds)")
    log.raw("=" * 78)
    log.raw("[mesh ] elements total = %d   (mat3 = %d, V = %.1f cm3)"
            % (tab["n_elem"], binf["n_mat3"], binf["V_mat3"] * cm3))
    log.raw("[mesh ] active (z in [%.4f, %.4f])  n=%d   V=%.1f cm3"
            % (Z_ST0, Z_ST1, binf["n_act"], V_act * cm3))
    log.raw("[mesh ] end    (z outside)          n=%d   V=%.1f cm3   V_end/V_act=%.3f"
            % (binf["n_end"], binf["V_end"] * cm3,
               (binf["V_end"] / V_act) if V_act > 0 else float("nan")))
    log.raw("[band ] measured r: min=%.3f  p0.5=%.3f  p99.5=%.3f  max=%.3f mm "
            "(expect %.1f .. %.1f)"
            % (binf["r_min"] * 1e3, binf["r_lo"] * 1e3, binf["r_hi"] * 1e3,
               binf["r_max"] * 1e3,
               BAND_EXPECT_M[0] * 1e3, BAND_EXPECT_M[1] * 1e3))
    log.raw("[band ] bin width = %.4f mm  (expect ~2.133)   binning = %s"
            % ((binf["r_hi"] - binf["r_lo"]) / K * 1e3, binf["binning"]))

    # 체적-반경 히스토그램 (ASCII)
    h = binf["r_s_hist"]
    hmax = float(h.max()) if h.size and h.max() > 0 else 1.0
    log.raw("[hist ] volume vs r over [%.3f, %.3f] mm, 32 bins:"
            % (binf["r_lo"] * 1e3, binf["r_hi"] * 1e3))
    for i in range(0, len(h), 1):
        r0 = binf["r_lo"] + (binf["r_hi"] - binf["r_lo"]) * i / float(len(h))
        nbar = int(round(40.0 * h[i] / hmax))
        log.raw("         %7.3f mm | %s" % (r0 * 1e3, "#" * nbar))

    log.raw("[zchk ] elements straddling z=%.4f or %.4f : n=%d  V=%.1f cm3 "
            "(%.1f %% of V_active)"
            % (Z_ST0, Z_ST1, binf["straddle_n"], binf["straddle_V"] * cm3,
               100.0 * binf["straddle_V"] / V_act if V_act > 0 else float("nan")))
    log.raw("")
    log.raw("  bin   r_lo[mm]  r_hi[mm]   n_elem     V[cm3]   V/Vact")
    for k in range(K):
        log.raw("   T%-2d  %8.3f  %8.3f  %8d  %9.3f   %6.4f"
                % (k + 1, edges[k] * 1e3, edges[k + 1] * 1e3, binf["n_k"][k],
                   V_k[k] * cm3, V_k[k] / V_act if V_act > 0 else float("nan")))
    log.raw("   SUM                      %8d  %9.3f   %6.4f"
            % (binf["n_act"], V_k.sum() * cm3,
               V_k.sum() / V_act if V_act > 0 else float("nan")))

    # ---- 판정 ----
    checks = []

    def _add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    target = 1.0 / float(K)
    ratios = [float(V_k[k] / V_act) if V_act > 0 else 0.0 for k in range(K)]
    worst = max(abs(r - target) / target for r in ratios)
    _add("band_volume_balance", worst <= VOL_BALANCE_TOL,
         "max deviation from 1/%d is %.1f %% (limit %.0f %%); ratios %s"
         % (K, 100.0 * worst, 100.0 * VOL_BALANCE_TOL,
            ["%.4f" % r for r in ratios]))

    empty = [k + 1 for k in range(K) if V_k[k] <= 0.0 or binf["n_k"][k] == 0]
    _add("no_empty_band", not empty,
         "empty bands: %s" % (empty if empty else "none"))

    sfrac = binf["straddle_V"] / V_act if V_act > 0 else 1.0
    _add("transition_layer", sfrac < STRADDLE_MAX_FRAC,
         "straddling volume is %.1f %% of V_active (limit %.0f %%)"
         % (100.0 * sfrac, 100.0 * STRADDLE_MAX_FRAC))

    inwin = (BAND_WINDOW_M[0] <= binf["r_lo"] <= BAND_WINDOW_M[1] and
             BAND_WINDOW_M[0] <= binf["r_hi"] <= BAND_WINDOW_M[1])
    _add("band_within_window", inwin,
         "measured band %.3f .. %.3f mm vs allowed window %.1f .. %.1f mm"
         % (binf["r_lo"] * 1e3, binf["r_hi"] * 1e3,
            BAND_WINDOW_M[0] * 1e3, BAND_WINDOW_M[1] * 1e3))

    minn = min(binf["n_k"]) if binf["n_k"] else 0
    _add("band_population_soft", minn >= MIN_ELEM_PER_BAND_SOFT,
         "smallest band holds %d elements (soft floor %d)"
         % (minn, MIN_ELEM_PER_BAND_SOFT))

    hard_ok = all(c["ok"] for c in checks
                  if c["check"] in ("band_volume_balance", "no_empty_band",
                                    "transition_layer"))
    verdict = "PASS" if hard_ok else "WARN"
    log.raw("")
    for c in checks:
        log.raw("  [%s] %-22s %s" % ("ok  " if c["ok"] else "WARN", c["check"],
                                     c["detail"]))
    log.raw("  ==> VERDICT: %s" % verdict)
    log.raw("=" * 78)
    log.raw("")
    return {"verdict": verdict, "checks": checks,
            "band_volume_ratios": ratios,
            "straddle_frac_of_active": float(sfrac)}


# =========================================================================== #
#  5. 손실 조립                                                                 #
# =========================================================================== #

def losses_for_point(records, speed, current, phase):
    """D2 한 운전점의 손실 세트.  전부 W."""
    rec = jm.get_record(records, speed, current, phase, mode="FullFEA")
    P_turn = jm.per_turn_raw(records, speed, current, phase)
    P_act = math.fsum(P_turn)
    dc_act = float(rec["ts_dc_active_only_kW"]) * 1000.0
    ac_tot = float(rec["fea_total_ac_kW"]) * 1000.0
    P_end = float(rec["ts_dc_end_kW"]) * 1000.0
    im = jm.iron_magnet(speed)

    # (III) 소스 무결성: raw 합 == dc_active + ac_total
    ref = dc_act + ac_tot
    rel = abs(P_act - ref) / (abs(ref) if ref else 1.0)
    if rel > 1e-6:
        raise AssertionError(
            "fea_per_turn_raw sum (%.6f W) disagrees with "
            "ts_dc_active_only+fea_total_ac (%.6f W), rel %.3e -- the map cell is "
            "inconsistent (speed=%r current=%r phase=%r)"
            % (P_act, ref, rel, speed, current, phase))

    return {"P_turn": [float(v) for v in P_turn],
            "P_active": float(P_act),
            "P_end": float(P_end),
            "P_dc_active": float(dc_act),
            "P_ac_total": float(ac_tot),
            "fe_s": float(im["fe_s"]), "fe_r": float(im["fe_r"]),
            "pm": float(im["pm"]),
            "P_total": float(P_act + P_end + im["fe_s"] + im["fe_r"] + im["pm"]),
            "raw_sum_rel_err": float(rel)}


def build_q_vectors(binf, mode, loss, log):
    """요소별 HGEN [W/m^3] 과 불변량 검사."""
    P_turn = np.asarray(loss["P_turn"], dtype=np.float64)
    if mode == "turnwise":
        q_act = q_turnwise(binf["frac"], binf["V_k"], P_turn)
    elif mode == "uniform":
        q_act = q_uniform(binf["n_act"], loss["P_active"], binf["V_act"])
    else:
        raise ValueError("mode must be 'uniform' or 'turnwise', got %r" % (mode,))

    if binf["V_end"] <= 0.0:
        raise RuntimeError("no material-3 elements outside the stack z-band: the "
                           "end-winding loss %.1f W has nowhere to go. Check "
                           "Z_ST0/Z_ST1 against the CDB." % loss["P_end"])
    q_end = np.full(binf["n_end"], loss["P_end"] / binf["V_end"], dtype=np.float64)

    inj_act = float((q_act * binf["vol_act"]).sum())
    inj_end = float((q_end * binf["vol_end"]).sum())
    rel_act = abs(inj_act - loss["P_active"]) / loss["P_active"]
    rel_end = abs(inj_end - loss["P_end"]) / (loss["P_end"] if loss["P_end"] else 1.0)
    if rel_act > INV_REL_TOL:
        raise AssertionError("active injection invariant violated: injected %.9f W "
                             "vs P_active %.9f W (rel %.3e > %.0e) -- DO NOT SOLVE"
                             % (inj_act, loss["P_active"], rel_act, INV_REL_TOL))
    if rel_end > INV_REL_TOL:
        raise AssertionError("end injection invariant violated: injected %.9f W vs "
                             "P_end %.9f W (rel %.3e > %.0e) -- DO NOT SOLVE"
                             % (inj_end, loss["P_end"], rel_end, INV_REL_TOL))
    log("  [inv ] %-8s active sum(q*V)=%.6f W vs %.6f W  rel=%.2e"
        % (mode, inj_act, loss["P_active"], rel_act))
    log("  [inv ] %-8s end    sum(q*V)=%.6f W vs %.6f W  rel=%.2e"
        % (mode, inj_end, loss["P_end"], rel_end, ))
    return {"q_act": q_act, "q_end": q_end,
            "injected_active_W": inj_act, "injected_end_W": inj_end,
            "rel_err_active": rel_act, "rel_err_end": rel_end}


# =========================================================================== #
#  6. MAPDL -- 모델 구성 (04_mapdl_thermal.py 를 그대로 옮김)                    #
# =========================================================================== #

def element_table(mapdl, log):
    """SOLID87 요소표를 1회 취득.  회로/SURF152 를 만들기 **전에** 부른다."""
    mapdl.allsel("ALL")
    grid = mapdl.mesh.grid
    enum = np.asarray(mapdl.mesh.enum, dtype=np.int64)
    emat = np.asarray(mapdl.mesh.material_type, dtype=np.int32)
    nnum = np.asarray(mapdl.mesh.nnum, dtype=np.int64)
    cd = grid.cells_dict
    types = sorted(int(t) for t in cd.keys())
    # ff_e10_mesh_v2.cdb IS a tet10 SOLID87 mesh, but pymapdl's pyvista grid reports it
    # as VTK_TETRA (10), i.e. corner-only connectivity -- observed on moa 2026-09-07,
    # and d1_cont_rating.py hits the same thing ("[warn] mixed cell types [10]").
    # A tetrahedron is fully determined by its 4 corners, so volumes, centroids and the
    # fractional-volume turn binning are unaffected. The one consequence: node sets built
    # from `conn` then hold CORNER nodes only, so winding statistics are corner-node
    # statistics. That is consistent between the uniform and turn-wise runs, which is
    # what D2's comparison rests on.
    if 24 in cd:
        conn = np.asarray(cd[24], dtype=np.int64)
        cell_kind = "VTK_QUADRATIC_TETRA (24)"
    elif 10 in cd:
        conn = np.asarray(cd[10], dtype=np.int64)
        cell_kind = "VTK_TETRA (10) -- corner-only view of a tet10 mesh"
    else:
        raise RuntimeError("no tetrahedral cells in the CDB: got cell types %s -- the "
                           "mesh is not the expected tet10 SOLID87 mesh" % (types,))
    if len(types) > 1:
        log("  [warn] mixed cell types %s; using %s" % (types, cell_kind))
    n = grid.n_cells
    if not (len(conn) == len(enum) == len(emat) == n):
        raise RuntimeError("element table length mismatch: conn=%d enum=%d emat=%d "
                           "cells=%d" % (len(conn), len(enum), len(emat), n))
    pts = np.asarray(grid.points, dtype=np.float64)
    if len(pts) != len(nnum):
        raise RuntimeError("point/node-number length mismatch: %d vs %d"
                           % (len(pts), len(nnum)))
    corners = pts[conn[:, :4]]
    vol_corner = tet_corner_volumes(corners)

    # ** pyvista is authoritative for volume and centroid, not the corner formula. **
    # Measured on moa 2026-09-07 with this CDB: element COUNTS from cells_dict match
    # mapdl.mesh.enum/material_type exactly (winding 109300 both ways), but the corner
    # volumes come out 62x-223x too large and the ratio differs per material -- so it is
    # not a unit error, the conn rows do not line up with enum/emat. d1_cont_rating.py
    # uses grid.compute_cell_sizes()/cell_centers() on the same mesh and reproduces the
    # gmsh reference (winding 900.39 vs 900.7 cm3), so those are the trustworthy source.
    vol = np.abs(np.asarray(
        grid.compute_cell_sizes(length=False, area=False, volume=True)
            .cell_data["Volume"], dtype=np.float64))
    cen = np.asarray(grid.cell_centers().points, dtype=np.float64)
    tot_c, tot_p = float(vol_corner.sum()), float(vol.sum())
    rel = abs(tot_c - tot_p) / max(tot_p, 1e-30)
    conn_trustworthy = rel <= 0.02
    if not conn_trustworthy:
        log("  [warn] corner-formula volume disagrees with pyvista by %.3e "
            "(%.1f vs %.1f cm3 total) -> the cells_dict connectivity does not line up "
            "with enum/material_type on this mesh. Using pyvista volumes and centroids; "
            "per-element corner sampling (fractional binning) is NOT usable."
            % (rel, tot_c * 1e6, tot_p * 1e6))
    tab = {"grid": grid, "points": pts, "conn": conn, "enum": enum, "emat": emat,
           "nnum": nnum, "corners": corners, "vol": vol, "vol_corner": vol_corner,
           "conn_trustworthy": bool(conn_trustworthy),
           "cen": cen, "n_elem": int(n), "n_node": int(len(pts))}
    tab["cell_kind"] = cell_kind
    log("mesh: %d nodes / %d tet elements  [%s]"
        % (tab["n_node"], tab["n_elem"], cell_kind))
    for m in sorted(set(int(x) for x in emat)):
        sel = (emat == m)
        log("  mat %d (%-7s): n=%7d  V=%9.2f cm3"
            % (m, MAT_NAMES.get(m, "?"), int(sel.sum()), vol[sel].sum() * 1e6))
    # pyvista 체적과 교차검증 (직선화된 tet10 이면 일치해야 한다)
    try:
        pv_vol = np.abs(np.asarray(
            grid.compute_cell_sizes(length=False, area=False,
                                    volume=True).cell_data["Volume"]))
        num = float(np.abs(pv_vol - vol).sum())
        den = float(vol.sum())
        rel = num / den if den else float("nan")
        log("  volume cross-check: corner formula vs pyvista compute_cell_sizes "
            "rel diff %.3e (pyvista is used)" % rel)
        if not (rel < 1e-3):
            log("  [WARN] pyvista and the straight-edge corner formula disagree. The "
                "corner formula is authoritative here (03/03b straighten the tet10 "
                "mid-nodes), but a large gap means the mid-nodes are NOT straight and "
                "the band volumes carry that error.")
    except Exception as exc:
        log("  volume cross-check skipped: %r" % (exc,))
    return tab


def build_model(mapdl, cdb, htc_set, log):
    """CDB 로드 + 재료 + 오일회로 + SURF152.  요소표를 함께 돌려준다."""
    h = HTC_SETS[htc_set]
    mapdl.clear()
    mapdl.prep7()
    mapdl.units("SI")
    log("cdread: %s.cdb" % cdb)
    mapdl.cdread("DB", cdb, "cdb")
    mapdl.shpp("off")
    mapdl.et(1, "SOLID87")
    for m, (k, c, r) in MATS.items():
        mapdl.mp("KXX", m, k)
        mapdl.mp("C", m, c)
        mapdl.mp("DENS", m, r)

    tab = element_table(mapdl, log)          # <- 회로 요소를 만들기 전에

    mapdl.et(2, "SURF152")
    mapdl.keyopt(2, 5, 1)
    mapdl.keyopt(2, 8, 2)
    mapdl.et(3, "COMBIN14")
    mapdl.keyopt(3, 2, 8)
    mapdl.et(4, "MASS71")
    mapdl.keyopt(4, 3, 1)

    nmax = int(mapdl.get_value("NODE", 0, "NUM", "MAXD"))

    def net_node(i):
        n = nmax + i
        mapdl.csys(0)
        mapdl.n(n, 0.5 + 0.02 * i, 0, 0)
        return n

    N = {}
    for i, nm in enumerate(["OIL", "JACKET", "SPRAY", "GAP_S", "GAP_R", "SHF"]):
        N[nm] = net_node(i + 1)

    rid = [100]

    def add_R(n1, n2, g):
        rid[0] += 1
        mapdl.type(3)
        mapdl.real(rid[0])
        mapdl.r(rid[0], g)
        mapdl.e(n1, n2)

    # MASS71 은 [C] 에만 기여하므로 정상상태에서는 무기여 -> 생성하지 않는다.
    # JACKET/SPRAY/SHF 는 각각 COMBIN14 로 OIL 에 묶여 있으므로 뜨지 않는다.
    add_R(N["JACKET"], N["OIL"], G_JKT_OIL)
    add_R(N["SPRAY"], N["OIL"], G_SPRAY_OIL)
    add_R(N["GAP_S"], N["GAP_R"], G_GAP)
    add_R(N["SHF"], N["OIL"], G_SHF_OIL)
    mapdl.d(N["OIL"], "TEMP", OIL_T)
    log("circuit: G_jkt=%.0f G_spray=%.0f G_gap=%.3f G_shf=%.0f W/K, D(OIL)=%.1f degC"
        % (G_JKT_OIL, G_SPRAY_OIL, G_GAP, G_SHF_OIL, OIL_T))

    mapdl.r(1)

    def make_surf(sel_fn, xnode, htc, name):
        mapdl.allsel("ALL")
        sel_fn()
        nsel = mapdl.mesh.n_node
        if nsel == 0:
            log("  [warn] %s: empty node selection" % name)
            mapdl.allsel("ALL")
            return 0
        e0 = int(mapdl.get_value("ELEM", 0, "NUM", "MAXD"))
        mapdl.esln("S", 0)
        mapdl.esel("R", "TYPE", "", 1)
        mapdl.nsel("A", "NODE", "", xnode)
        mapdl.type(2)
        mapdl.real(1)
        mapdl.esurf(xnode)
        e1 = int(mapdl.get_value("ELEM", 0, "NUM", "MAXD"))
        if e1 <= e0:
            log("  [warn] %s: %d nodes but no SURF152 created" % (name, nsel))
            mapdl.allsel("ALL")
            return 0
        mapdl.esel("S", "ELEM", "", e0 + 1, e1)
        mapdl.sfe("ALL", 1, "CONV", "", htc)
        mapdl.allsel("ALL")
        log("  [surf] %-22s %6d elems (%d nodes) h=%.0f" % (name, e1 - e0, nsel, htc))
        return e1 - e0

    def sel_matradz(mat, rlo=None, rhi=None, zlo=None, zhi=None, ext=True):
        def _fn():
            mapdl.allsel("ALL")
            mapdl.esel("S", "MAT", "", mat)
            mapdl.nsle("S")
            if ext:
                mapdl.nsel("R", "EXT")
            mapdl.csys(1)
            mapdl.seltol(TOL)
            if rlo is not None:
                mapdl.nsel("R", "LOC", "X", rlo, rhi)
            if zlo is not None:
                mapdl.nsel("R", "LOC", "Z", zlo, zhi)
            mapdl.seltol(0)
            mapdl.csys(0)
        return _fn

    nsurf = 0
    nsurf += make_surf(sel_matradz(M_ST, rlo=R_STA_OUT - RT, rhi=R_STA_OUT + RT),
                       N["JACKET"], h["jkt"], "statorOD->JACKET")
    nsurf += make_surf(sel_matradz(M_ST, rlo=R_STA_IN - RT, rhi=R_STA_IN + RT),
                       N["GAP_S"], HTC_BIG, "statorBore->GAP_S")
    nsurf += make_surf(sel_matradz(M_CO, zhi=Z_ST0 + 2e-4, zlo=-1.0),
                       N["SPRAY"], h["spray"], "windEnd_lo->SPRAY")
    nsurf += make_surf(sel_matradz(M_CO, zlo=Z_ST1 - 2e-4, zhi=1.0),
                       N["SPRAY"], h["spray"], "windEnd_hi->SPRAY")
    nsurf += make_surf(sel_matradz(M_RO, rlo=R_ROT_OUT - RT, rhi=R_ROT_OUT + RT),
                       N["GAP_R"], HTC_BIG, "rotorOD->GAP_R")
    nsurf += make_surf(sel_matradz(M_RO, zhi=Z_ST0 + 2e-4, zlo=-1.0),
                       N["OIL"], h["splash"], "rotorEnd_lo->OIL")
    nsurf += make_surf(sel_matradz(M_RO, zlo=Z_ST1 - 2e-4, zhi=1.0),
                       N["OIL"], h["splash"], "rotorEnd_hi->OIL")
    nsurf += make_surf(sel_matradz(M_SH, zhi=Z_ST0 + 2e-4, zlo=-1.0),
                       N["SHF"], h["splash"], "shaftEnd_lo->SHF")
    nsurf += make_surf(sel_matradz(M_SH, zlo=Z_ST1 - 2e-4, zhi=1.0),
                       N["SHF"], h["splash"], "shaftEnd_hi->SHF")
    if nsurf == 0:
        raise RuntimeError("no SURF152 convection elements were created -- the model "
                           "has no path to the oil and cannot be solved")
    mapdl.allsel("ALL")
    return tab, N


def write_hgen_macro(path, enum_act, q_act, enum_end, q_end, other, log):
    """요소별 BFE 매크로 파일.  mat 1/2/5 는 재료별 균일 q 를 같은 파일에 넣는다.

    `BFE,<eid>,HGEN,1,<q>` 한 줄이 요소 하나.  STLOC=1 에 값 하나만 주면 나머지
    코너 값은 VAL1 로 채워진다(04_mapdl_thermal.py:158 이 이미 쓰는 형식).
    mat 3 에는 blanket `bfe("ALL", ...)` 를 절대 걸지 않는다 -- 순서 실수 하나로
    조용히 균일주입이 되기 때문이다.
    """
    n = 0
    with open(path, "w", encoding="ascii", newline="\n") as fh:
        fh.write("! d2_ac_turnwise per-element heat generation (HGEN, W/m^3)\n")
        for e, q in zip(enum_act.tolist(), q_act.tolist()):
            fh.write("BFE,%d,HGEN,1,%.12E\n" % (e, q))
            n += 1
        for e, q in zip(enum_end.tolist(), q_end.tolist()):
            fh.write("BFE,%d,HGEN,1,%.12E\n" % (e, q))
            n += 1
        for eids, q in other:
            for e in eids.tolist():
                fh.write("BFE,%d,HGEN,1,%.12E\n" % (e, q))
                n += 1
    log("  [bfe ] macro %s : %d lines (%.1f MB)"
        % (os.path.basename(path), n, os.path.getsize(path) / 1e6))
    return n


def read_hgen_macro(path):
    """매크로를 되읽어 {eid: q} 로.  드라이런의 왕복 검증에 쓴다."""
    out = {}
    with open(path, "r", encoding="ascii") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            f = line.split(",")
            if len(f) != 5 or f[0].upper() != "BFE" or f[2].upper() != "HGEN":
                raise ValueError("unexpected macro line: %r" % line)
            out[int(f[1])] = float(f[4])
    return out


def _input_macro(mapdl, run_dir, mac_name, mac_path, log):
    """`mapdl.input()` 의 경로 처리 차이를 흡수한다.  세 가지를 순서대로 시도."""
    errs = []
    for how, fn in (
            ("input(full_path)", lambda: mapdl.input(mac_path)),
            ("input(name, 'mac')", lambda: mapdl.input(mac_name, "mac")),
            ("/INPUT,name,mac,dir",
             lambda: mapdl.run("/INPUT,'%s','mac','%s'"
                               % (mac_name, run_dir.replace("\\", "/")))),
    ):
        try:
            fn()
            log("  [bfe ] injected via %s" % how)
            return how
        except Exception as exc:
            errs.append("%s -> %r" % (how, exc))
    raise RuntimeError("could not feed the BFE macro to MAPDL:\n  %s"
                       % "\n  ".join(errs))


def apply_loads(mapdl, run_dir, tag, tab, binf, qv, loss, log):
    """HGEN 을 걸고 총 주입량을 로그로 남긴다."""
    emat = tab["emat"]
    enum = tab["enum"]
    vol = tab["vol"]

    other = []
    for mat, W in ((M_ST, loss["fe_s"]), (M_MG, loss["pm"]), (M_RO, loss["fe_r"])):
        sel = (emat == mat)
        v = float(vol[sel].sum())
        if v <= 0.0:
            raise RuntimeError("material %d (%s) has zero volume -- cannot inject "
                               "%.1f W" % (mat, MAT_NAMES.get(mat, "?"), W))
        other.append((enum[sel], W / v))
        log("  [hgen] mat%d %-7s V=%8.2f cm3  q=%.4e W/m3  (%.1f W)"
            % (mat, MAT_NAMES.get(mat, "?"), v * 1e6, W / v, W))

    mac_name = "hgen_%s" % tag
    mac_path = os.path.join(run_dir, mac_name + ".mac")
    write_hgen_macro(mac_path, enum[binf["act"]], qv["q_act"],
                     enum[binf["end"]], qv["q_end"], other, log)

    mapdl.finish()
    mapdl.prep7()
    mapdl.allsel("ALL")
    mapdl.run("BFEDELE,ALL,HGEN")             # 이전 런의 잔여 하중 제거
    t0 = time.time()
    _input_macro(mapdl, run_dir, mac_name, mac_path, log)
    mapdl.allsel("ALL")
    log("  [bfe ] input() took %.1f s" % (time.time() - t0))

    inj = (qv["injected_active_W"] + qv["injected_end_W"]
           + loss["fe_s"] + loss["fe_r"] + loss["pm"])
    log("  [hgen] total injected = %.3f W  (expected %.3f W)" % (inj, loss["P_total"]))
    return inj


def solve_steady(mapdl, load_index, log, oil_node=None):
    """계획 스펙의 정상상태 전환.  SOLVE 직전 allsel 은 필수다.

    하중단계 2 이후에 필요한 두 가지 (moa 2026-09-07 실측, d1_cont_rating.py 와 동일):

    1) ANTYPE 은 **첫 회에만** 발행한다. 재발행은 Status=NEW 로 해석돼 하중 상태를
       초기화하고 결과파일을 되감는다.
    2) 디리클레(D,OIL,TEMP)를 **매 하중단계 다시 건다.** 회로 구성 때 한 번 건 것이
       2번째 SOLVE 에서 유효하지 않았고, MAPDL 이 OIL 절점에서 음의 피벗과
       "no temperature constraints or convections applied" 를 내며 2.28e12 K 로 발산했다.
       D 는 멱등이라 다시 거는 비용이 없다.
    """
    mapdl.finish()
    mapdl.slashsolu()
    if int(load_index) <= 1:
        mapdl.antype("STATIC")
        mapdl.kbc(1)
    if oil_node is not None:
        mapdl.d(int(oil_node), "TEMP", OIL_T)
    mapdl.nsubst(1)
    mapdl.time(float(load_index))
    mapdl.outres("ERASE")
    mapdl.outres("ALL", "NONE")
    mapdl.outres("NSOL", "ALL")
    # RSOL is REQUIRED for energy_balance(): *GET,,NODE,n,RF,HEAT reads the reaction
    # heat flow at the OIL Dirichlet, and with OUTRES,ALL,NONE it is never written.
    # Without this the check silently reports a stale number -- observed on moa as
    # "OIL reaction heat = 81.482 W vs injected 89824.250 W" where 81.482 was just the
    # SHF node temperature, i.e. a 99.91 % false alarm on a perfectly good solve.
    mapdl.outres("RSOL", "ALL")
    mapdl.allsel("ALL")                       # <- SOLVE 는 '선택된' 것만 푼다
    t0 = time.time()
    mapdl.solve()
    dt = time.time() - t0
    mapdl.finish()
    log("  [solve] %.1f s" % dt)
    return dt


# =========================================================================== #
#  7. POST1 -- 온도 추출                                                        #
# =========================================================================== #

def read_nodal_temperature(mapdl, tab, log):
    """grid.points 순서의 절점온도 배열.  정렬을 assert 로 못박는다."""
    mapdl.finish()
    mapdl.post1()
    nsets = int(mapdl.get_value("ACTIVE", 0, "SET", "NSET"))
    mapdl.set("LAST")
    mapdl.allsel("ALL")
    mapdl.esel("S", "TYPE", "", 1)
    mapdl.nsle("S")
    nnum = np.asarray(mapdl.mesh.nnum, dtype=np.int64)
    if not np.array_equal(nnum, tab["nnum"]):
        raise RuntimeError(
            "POST1 node selection (%d nodes) does not match the element-table node "
            "ordering (%d nodes) -- temperature/point alignment is not safe"
            % (len(nnum), len(tab["nnum"])))
    T = np.asarray(mapdl.post_processing.nodal_temperature(), dtype=np.float64)
    if len(T) != tab["n_node"]:
        raise RuntimeError("nodal_temperature returned %d values for %d nodes"
                           % (len(T), tab["n_node"]))
    mapdl.allsel("ALL")
    log("  [post ] nsets=%d  T range %.2f .. %.2f degC"
        % (nsets, float(np.nanmin(T)), float(np.nanmax(T))))
    return T, nsets


def assert_physical(T, log, max_nodes=50, max_frac=0.30, mean_rel_tol=1e-4):
    """단일 Dirichlet OIL=70 degC + 전부 양의 발열 -> 모든 절점 T >= 70.

    다만 최대원리는 편미분방정식의 엄밀해에 성립하지, 2차 사면체(SOLID87) 보간함수의
    절점값에는 성립하지 않는다.  이 메시에는 **고정된 불량 절점 2개**(id 67651, 99303,
    권선)가 있어 국소 구배에 비례하는 언더슈트를 낸다 -- D1 실측에서 슬롯동손 주입 때
    -7.54 K, 엔드동손 주입 때 -16.3 K 로 **같은 절점이 하중에 따라 다른 크기**를 보였다.
    따라서 판정을 크기가 아니라 **개수와 보고값 영향**으로 한다.
    반환값은 (관용된 경우) 기록용 dict, 아니면 None.
    """
    tmin = float(np.nanmin(T))
    if tmin >= 69.99:
        log("  [check] min nodal T = %.3f degC >= %.2f  OK" % (tmin, OIL_T))
        return None

    # 판정은 전부 **상대량**으로 한다. 언더슈트도 평균 오염도도 하중에 비례해 커지므로
    # 절대 임계값을 쓰면 하중만 키워도 반드시 걸린다(D1 에서 두 번 겪었다).
    cold = np.where(np.nan_to_num(T, nan=1e9) < 69.99)[0]
    n_cold = int(cold.size)
    good = T[np.nan_to_num(T, nan=1e9) >= 69.99]
    bad = T[np.nan_to_num(T, nan=-1e9) < 69.99]
    tmax = float(np.nanmax(T))
    rise = max(tmax - OIL_T, 1e-9)
    frac = (OIL_T - tmin) / rise
    if good.size:
        gmean = float(np.nanmean(good))
        contam = float(np.sum(np.abs(bad - gmean))) / float(T.size)
        rel = contam / max(1.0, gmean - OIL_T)
    else:
        contam, rel = float("inf"), float("inf")
    ok = (n_cold <= int(max_nodes) and frac <= float(max_frac)
          and rel <= float(mean_rel_tol))
    if not ok:
        raise AssertionError(
            "steady solution is invalid: minimum nodal temperature is %.4f degC but "
            "the only Dirichlet condition is OIL = %.1f degC with strictly positive "
            "heat generation, so every node must be >= %.1f degC. %d node(s) violate it, "
            "the undershoot is %.1f%% of the field range and the mean contamination is "
            "%.2e relative -- beyond the tolerated envelope (<= %d nodes, <= %.0f%% of "
            "range, <= %.1e relative). Check the circuit, the HGEN signs, and that "
            "ALLSEL preceded SOLVE."
            % (tmin, OIL_T, OIL_T, n_cold, 100*frac, rel, max_nodes,
               100*max_frac, mean_rel_tol))
    ids = cold[:20].tolist()
    log("  [check] min nodal T = %.4f degC at %d node(s) (index %s); undershoot %.1f%% of "
        "range, mean contamination %.2e rel -- tolerated as fixed bad-element undershoot, "
        "no reported quantity affected" % (tmin, n_cold, ids, 100*frac, rel))
    return {"n_nodes_below": n_cold, "t_min_C": tmin, "undershoot_K": OIL_T - tmin,
            "node_index": ids, "undershoot_frac_of_range": frac,
            "mean_contamination_K": contam, "mean_contamination_rel": rel,
            "verdict": "tolerated (fixed bad-element SOLID87 undershoot)",
            "limits": {"max_nodes": int(max_nodes), "max_frac_of_range": float(max_frac),
                       "max_mean_contamination_rel": float(mean_rel_tol)}}


def extract_run(T, tab, binf, loss, log):
    """한 런의 온도 결과 dict (JSON 에 그대로 들어간다)."""
    conn = tab["conn"]
    emat = tab["emat"]
    vol = tab["vol"]
    Te_mean = T[conn].mean(axis=1)
    Te_max = T[conn].max(axis=1)

    out = {}
    per_part = {}
    for m, nm in MAT_NAMES.items():
        sel = (emat == m)
        if not sel.any():
            continue
        nodes = np.unique(conn[sel])
        v = T[nodes]
        w = vol[sel]
        per_part[nm] = {
            "max": float(np.nanmax(v)),
            "min": float(np.nanmin(v)),
            "mean_nodal": float(np.nanmean(v)),
            "mean_volwt": float((Te_mean[sel] * w).sum() / w.sum()),
        }
    out["per_part_T_C"] = per_part

    act = binf["act"]
    frac = binf["frac"]
    va = binf["vol_act"]
    K = binf["nturns"]
    Te_mean_act = Te_mean[act]
    Te_max_act = Te_max[act]
    band_mean = []
    band_max = []
    for k in range(K):
        w = frac[:, k] * va
        sw = float(w.sum())
        band_mean.append(float((w * Te_mean_act).sum() / sw) if sw > 0 else float("nan"))
        hit = frac[:, k] > 0.0
        band_max.append(float(Te_max_act[hit].max()) if hit.any() else float("nan"))
    out["turn_T_C"] = {
        "mean": band_mean, "max": band_max,
        "labels": ["T%d" % (k + 1) for k in range(K)],
        "note": ("T1 = airgap side (smallest radius), T%d = yoke side. 'mean' is the "
                 "fractional-volume-weighted element mean and is the quantity to "
                 "quote; 'max' is the hottest node of ANY element that overlaps the "
                 "band, so adjacent bands can share a hotspot element and report "
                 "nearly equal maxima." % K)}

    wnodes = np.unique(conn[emat == M_CO])
    anodes = np.unique(conn[act])
    out["T_C"] = {
        "winding_max": float(np.nanmax(T[wnodes])),
        "winding_mean_nodal": float(np.nanmean(T[wnodes])),
        "winding_mean_volwt": float((Te_mean[emat == M_CO] * vol[emat == M_CO]).sum()
                                    / vol[emat == M_CO].sum()),
        "winding_active_max": float(np.nanmax(T[anodes])),
        "winding_active_mean_volwt": float((Te_mean_act * va).sum() / va.sum()),
        "stator_max": per_part.get("stator", {}).get("max"),
        "magnet_max": per_part.get("magnet", {}).get("max"),
        "rotor_max": per_part.get("rotor", {}).get("max"),
        "shaft_max": per_part.get("shaft", {}).get("max"),
        "global_min": float(np.nanmin(T)),
    }
    out["airgap_side_vs_yoke_side_K"] = float(band_mean[0] - band_mean[K - 1])
    out["airgap_side_vs_yoke_side_max_K"] = float(band_max[0] - band_max[K - 1])

    kw = loss["P_total"] / 1000.0
    kwa = loss["P_active"] / 1000.0
    out["K_per_kW"] = {
        "winding_max_per_kW_total": (out["T_C"]["winding_max"] - OIL_T) / kw,
        "winding_max_per_kW_active": (out["T_C"]["winding_max"] - OIL_T) / kwa,
        "turn_mean_per_kW_active": [(v - OIL_T) / kwa for v in band_mean],
        "magnet_max_per_kW_total": ((out["T_C"]["magnet_max"] - OIL_T) / kw
                                    if out["T_C"]["magnet_max"] is not None else None),
    }
    log("  [T    ] winding max=%.1f mean=%.1f | T1=%.1f T%d=%.1f | dT(T1-T%d)=%+.2f K"
        % (out["T_C"]["winding_max"], out["T_C"]["winding_mean_nodal"],
           band_mean[0], K, band_mean[K - 1], K,
           out["airgap_side_vs_yoke_side_K"]))
    return out


def read_circuit(mapdl, N, log):
    out = {}
    for nm, n in N.items():
        try:
            out[nm] = round(float(mapdl.get_value("NODE", n, "TEMP")), 3)
        except Exception as exc:
            out[nm] = None
            log("  [warn] circuit node %s: %r" % (nm, exc))
    log("  [circ] %s" % out)
    return out


def energy_balance(mapdl, oil_node, total_W, log):
    """정상상태 에너지 보존: OIL 절점의 반력 열유량 == -(총 주입량).

    HGEN 이 실제로 걸렸는지 MAPDL 쪽에서 확인하는 유일한 전역 검사다.
    """
    try:
        rf = float(mapdl.get_value("NODE", oil_node, "RF", "HEAT"))
    except Exception as exc:
        log("  [ebal] skipped (%r)" % (exc,))
        return None
    rel = abs(abs(rf) - total_W) / (total_W if total_W else 1.0)
    log("  [ebal] OIL reaction heat = %.3f W vs injected %.3f W  rel=%.3e"
        % (rf, total_W, rel))
    if rel > 1e-3:
        log("  [WARN] energy balance off by %.2f %% -- the injected heat is not what "
            "the solver saw. Inspect the BFE macro." % (100.0 * rel))
    return {"oil_reaction_W": rf, "injected_W": total_W, "rel_err": rel}


# =========================================================================== #
#  8. 그림 -- ThermalViz.contour_png() + thesis_style.png_from_pyvista          #
# =========================================================================== #

def _read_png_rgb(path):
    """PNG -> (H,W,3) uint8.  PIL 이 없으면 matplotlib 으로 읽고 스케일한다."""
    try:
        from PIL import Image
        return np.asarray(Image.open(path).convert("RGB"))
    except Exception:
        pass
    import matplotlib.image as mpimg
    arr = np.asarray(mpimg.imread(path))
    if arr.ndim == 2:
        arr = np.repeat(arr[:, :, None], 3, axis=2)
    arr = arr[..., :3]
    if arr.dtype != np.uint8:
        arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return arr


def _zcut_fallback(tv, out_png, clim):
    """contour_png() 의 자동 z 슬라이스가 스택 밖으로 떨어질 때만 쓰는 대체 렌더."""
    import pyvista as pv
    tv.solid.point_data["Temperature (degC)"] = tv.Tend[tv.opid]
    sl = tv.solid.slice(normal="z", origin=(0.0, 0.0, ZC))
    pl = pv.Plotter(off_screen=True, window_size=(1000, 950))
    pl.set_background("white")
    pl.add_mesh(sl, scalars="Temperature (degC)", cmap="inferno", clim=list(clim),
                n_colors=14, lighting=False,
                scalar_bar_args=dict(title="Temperature (degC)", n_labels=6,
                                     fmt="%.0f", color="black",
                                     title_font_size=14, label_font_size=12))
    try:
        tv._add_mat_outlines(pl, (0.0, 0.0, ZC),
                             roles=("coil", "magnet", "shaft", "rotor"))
    except Exception:
        pass
    pl.view_xy()
    pl.camera.zoom(1.15)
    pl.screenshot(out_png)
    pl.close()
    return out_png


def render_contours(panels, out_dir, work_dir, log):
    """panels: [{'rth','mode','current','title'}, ...] -> 최종 PNG 경로 목록.

    두 장은 반드시 **같은 clim** 으로 그린다.  ThermalViz.__init__ 은 파일마다
    clim 을 새로 계산하므로(thermal_viz.py:106-109) 생성 후 덮어써야 한다.
    """
    import thesis_style as ts
    # thermal_viz.py is the repo's designated viz module and lives in
    # mlxperPJT/thermal/, i.e. two levels above this kit directory
    # (<thermal>/plans/PLAN_20260906_assets/). The kit imports only from its own
    # directory by design, so add that one path here rather than at module import.
    _thermal_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _thermal_dir not in sys.path:
        sys.path.insert(0, _thermal_dir)
    try:
        from thermal_viz import ThermalViz
    except ImportError as exc:
        raise ImportError(
            "thermal_viz not importable from %s -- the contour panels need the repo's "
            "viz module. Check that <repo>/mlxperPJT/thermal/thermal_viz.py exists, or "
            "run with --no-png. (%s)" % (_thermal_dir, exc))

    ts.apply()
    built = []
    for p in panels:
        if not p.get("rth") or not os.path.isfile(p["rth"]):
            log("  [png ] skip %s %.2f A: rth not found (%s)"
                % (p["mode"], p["current"], p.get("rth")))
            continue
        sub = os.path.join(work_dir, "viz_%s_%s" % (p["mode"],
                                                    ("%.0f" % p["current"])))
        tv = ThermalViz(p["rth"], sub, label="%s %.1f A" % (p["mode"], p["current"]),
                        clim_lo=OIL_T,
                        mats=dict(stator=M_ST, magnet=M_MG, coil=M_CO,
                                  shaft=M_SH, rotor=M_RO))
        built.append((p, tv, sub))
    if not built:
        return []

    hi = max(float(np.nanmax(tv.Tend[tv.opid])) for _, tv, _ in built)
    clim = [OIL_T, hi]
    log("  [png ] shared clim = [%.1f, %.1f] degC" % (clim[0], clim[1]))

    outs = []
    for p, tv, sub in built:
        tv.clim = list(clim)                  # <- 반드시 생성 후 덮어쓴다
        cz = float(tv.solid.center[2])
        use_fallback = abs(cz - ZC) > 0.5 * STACK
        src = None
        try:
            paths = tv.contour_png()          # contour_iso.png + contour_z0.png
            for q in paths:
                if os.path.basename(q) == "contour_z0.png":
                    src = q
            if src is None and paths:
                src = paths[-1]
        except Exception as exc:
            log("  [png ] contour_png failed (%r) -- using the ZC fallback" % (exc,))
            use_fallback = True
        if use_fallback:
            log("  [png ] ThermalViz auto z-slice at z=%.4f m is outside the stack "
                "[%.4f, %.4f]; rendering the fallback slice at ZC=%.4f"
                % (cz, Z_ST0, Z_ST1, ZC))
            src = _zcut_fallback(tv, os.path.join(sub, "contour_zc.png"), clim)
        img = _read_png_rgb(src)
        dst = os.path.join(out_dir, "e10_ac_turnwise_zcut_%s_%dA.png"
                           % (p["mode"], int(round(p["current"]))))
        # 원본 스크린샷이 1150x950 이므로 200 dpi 면 거의 1:1 (5.6 in x 200 = 1120 px).
        # 300 dpi 는 업스케일일 뿐이라 용량만 늘린다.
        res = ts.png_from_pyvista(img, p["title"], dst, dpi=200,
                                  subtitle=("cross-section at the stack mid-plane, "
                                            "shared colour scale %.0f - %.0f degC"
                                            % (clim[0], clim[1])))
        log("  [png ] %s  %d bytes  dpi=%.0f  ok=%s"
            % (os.path.basename(dst), res["bytes"], res["dpi"], res["ok"]))
        if not res["ok"]:
            log("  [WARN] %s exceeds %d bytes" % (dst, ts.PNG_MAX_BYTES))
        outs.append({"path": dst, "bytes": res["bytes"], "mode": p["mode"],
                     "current": p["current"], "source_render": os.path.basename(src),
                     "clim_C": clim, "ok": bool(res["ok"])})
    return outs


# =========================================================================== #
#  8b. .gitignore 자체 점검 -- thesis_out PNG 가 조용히 삼켜지는 것을 막는다      #
# =========================================================================== #

GITIGNORE_PATCH = "!mlxperPJT/thermal/thesis_out/*.png"
GITIGNORE_HELP = (
    "The repository root .gitignore has `*.png` (line 39) and `*.csv` (line 183), so "
    "the figures written to mlxperPJT/thermal/thesis_out/ are silently untracked. "
    "JSON and .py pass. Fix: append this single line to the END of the root "
    ".gitignore (a later negation wins), then `git add -f` is not needed:\n"
    "    " + GITIGNORE_PATCH + "\n"
    ".gitignore lives outside plans/, so the thesis-side session cannot write it -- "
    "moa applies this patch and commits it.")


def _git(repo, args, timeout=30):
    """git 을 조용히 실행하고 (rc, stdout) 를 돌려준다.  실패는 예외로 올린다."""
    pr = subprocess.run(["git", "-C", repo] + list(args),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        timeout=timeout)
    return pr.returncode, pr.stdout.decode("utf-8", "replace")


def git_ignore_check(repo, paths, log):
    """`git check-ignore` 로 산출 PNG 가 무시되는지 확인하고 크게 경고한다.

    ★ 판정은 **-v 없는** `git check-ignore` 로 한다.  `-v` 는 마지막으로 매치된
    규칙이 부정규칙(`!...`)이어도 그 줄을 찍기 때문에, `-v` 출력의 유무로
    판정하면 패치를 적용한 뒤에 오히려 오탐이 난다.  옵션 없는 형태는 **정말로
    무시되는 경로만** 나열한다(이 동작은 임시 레포로 실측 확인함).
    """
    res = {"ran": False, "ignored": [], "detail": [], "patch": GITIGNORE_PATCH,
           "help": GITIGNORE_HELP}
    rels = []
    for p in paths:
        try:
            rels.append(os.path.relpath(p, repo).replace("\\", "/"))
        except Exception:
            pass
    if not rels:
        return res
    try:
        rc, out = _git(repo, ["check-ignore", "--"] + rels)
        res["ran"] = True
    except Exception as exc:
        log("  [git ] check-ignore skipped (%r)" % (exc,))
        return res
    ignored = [ln.strip() for ln in out.splitlines() if ln.strip()]
    res["ignored"] = ignored
    if not ignored:
        log("  [git ] check-ignore: the %d output figure(s) are trackable, good"
            % len(rels))
        return res
    try:
        _, det = _git(repo, ["check-ignore", "-v", "--"] + ignored)
        res["detail"] = [ln.strip() for ln in det.splitlines() if ln.strip()]
    except Exception:
        pass
    log("  [git ] !! %d output figure(s) are IGNORED by .gitignore and will NOT be "
        "committed:" % len(ignored))
    for ln in (res["detail"] or ignored):
        log("  [git ]    %s" % ln)
    for ln in GITIGNORE_HELP.splitlines():
        log("  [git ] %s" % ln)
    return res


# =========================================================================== #
#  9. 결과 조립                                                                 #
# =========================================================================== #

def build_comparison(runs, K):
    """전류별 uniform vs turnwise 비교 + 정규화 민감도."""
    by = {}
    for r in runs:
        by.setdefault("%.6g" % r["current"], {})[r["mode"]] = r
    cmp_out = {}
    for key in sorted(by.keys(), key=float):
        pair = by[key]
        if "uniform" not in pair or "turnwise" not in pair:
            continue
        u, t = pair["uniform"], pair["turnwise"]
        Pa = u["P_W"]["cu_active_total"]
        Pt = u["P_W"]["total"]
        kwa = Pa / 1000.0
        kwt = Pt / 1000.0
        du = u["T_C"]["winding_max"] - OIL_T
        dt = t["T_C"]["winding_max"] - OIL_T
        cmp_out[key] = {
            "current_Arms": u["current"],
            "P_active_W": Pa, "P_end_W": u["P_W"]["cu_end"], "P_total_W": Pt,
            "winding_max_C": {"uniform": u["T_C"]["winding_max"],
                              "turnwise": t["T_C"]["winding_max"]},
            "delta_winding_max_K": t["T_C"]["winding_max"] - u["T_C"]["winding_max"],
            "T_rise_ratio_max": (dt / du) if du else None,
            "delta_winding_mean_volwt_K": (t["T_C"]["winding_mean_volwt"]
                                           - u["T_C"]["winding_mean_volwt"]),
            "turn_mean_C": {"uniform": u["turn_T_C"]["mean"],
                            "turnwise": t["turn_T_C"]["mean"]},
            "delta_turn_mean_K": [t["turn_T_C"]["mean"][k] - u["turn_T_C"]["mean"][k]
                                  for k in range(K)],
            "airgap_side_vs_yoke_side_K": {
                "uniform": u["airgap_side_vs_yoke_side_K"],
                "turnwise": t["airgap_side_vs_yoke_side_K"]},
            "K_per_kW_active": {
                "uniform_winding_max": du / kwa,
                "turnwise_winding_max": dt / kwa,
                "delta_winding_max": (dt - du) / kwa,
                "uniform_turn_mean": [(v - OIL_T) / kwa
                                      for v in u["turn_T_C"]["mean"]],
                "turnwise_turn_mean": [(v - OIL_T) / kwa
                                       for v in t["turn_T_C"]["mean"]],
                "delta_turn_mean": [(t["turn_T_C"]["mean"][k]
                                     - u["turn_T_C"]["mean"][k]) / kwa
                                    for k in range(K)]},
            "K_per_kW_total": {
                "uniform_winding_max": du / kwt,
                "turnwise_winding_max": dt / kwt,
                "delta_winding_max": (dt - du) / kwt},
            "headline": ("uniform injection under-predicts the winding hotspot by "
                         "%.2f K (%.3f K/kW of active copper loss); the airgap-side "
                         "turn T1 runs %.2f K hotter than the yoke-side turn T%d "
                         "under turn-wise injection versus %.2f K under uniform"
                         % (t["T_C"]["winding_max"] - u["T_C"]["winding_max"],
                            (dt - du) / kwa,
                            t["airgap_side_vs_yoke_side_K"], K,
                            u["airgap_side_vs_yoke_side_K"])),
        }
    return cmp_out


def assemble_json(args, binf, sanity, runs, pngs, meta):
    K = binf["nturns"]
    doc = {
        "_model": ("JAC279 hybrid steady (3D FEM + oil circuit), per-element HGEN "
                   "from radial banding of material 3"),
        "_loss_source": LOSS_SOURCE,
        "_soltype": "steady",
        "_htc": dict(HTC_SETS[args.htc_set]),
        "_htc_set": args.htc_set,
        "_htc_measured": dict(HTC_MEASURED),
        "_loss_model_caveat": LOSS_CAVEAT,
        "_physical_warning": PHYS_WARNING,
        "_operating": {"speed_rpm": args.speed, "phase_deg": args.phase,
                       "currents_Arms": list(args.currents),
                       "modes": list(args.modes), "n_turns": K,
                       "case": "AC (fea_per_turn_raw already contains DC+AC)"},
        "_binning": binf["binning"],
        "_binning_note": (
            "turn index is recovered by radial banding of material-3 elements inside "
            "the stack z-band; there is no turn identity in the mesh (03_stl_to_cdb.py "
            "writes only NBLOCK/EBLOCK). Bands are 6 equal-width annular shells "
            "between the volume-weighted 0.5 / 99.5 percentile radii MEASURED from "
            "the mesh. T1 = smallest radius = airgap side, T%d = yoke side." % K),
        "_band_mm": {"r_lo": binf["r_lo"] * 1e3, "r_hi": binf["r_hi"] * 1e3,
                     "r_min_sample": binf["r_min"] * 1e3,
                     "r_max_sample": binf["r_max"] * 1e3,
                     "edges": [float(e) * 1e3 for e in binf["edges"]],
                     "bin_width": (binf["r_hi"] - binf["r_lo"]) / K * 1e3,
                     "expected_mm": [BAND_EXPECT_M[0] * 1e3, BAND_EXPECT_M[1] * 1e3]},
        "_V_cm3": {"mat3_total": binf["V_mat3"] * 1e6,
                   "active": binf["V_act"] * 1e6,
                   "end": binf["V_end"] * 1e6,
                   "end_over_active": binf["V_end"] / binf["V_act"],
                   "per_bin": [float(v) * 1e6 for v in binf["V_k"]],
                   "per_bin_frac": [float(v / binf["V_act"]) for v in binf["V_k"]]},
        "_mesh": {"n_elem_total": meta.get("n_elem_total"),
                  "n_node_total": meta.get("n_node_total"),
                  "n_elem_mat3": binf["n_mat3"],
                  "n_elem_active": binf["n_act"],
                  "n_elem_end": binf["n_end"],
                  "n_elem_per_bin": binf["n_k"],
                  "straddle_n_elem": binf["straddle_n"],
                  "straddle_V_cm3": binf["straddle_V"] * 1e6,
                  "straddle_frac_of_active": sanity["straddle_frac_of_active"],
                  "samples_per_tet": binf["samples"], "sample_seed": binf["seed"],
                  "cdb": meta.get("cdb")},
        "_sanity": sanity,
        "_geometry_m": {"R_STA_OUT": R_STA_OUT, "R_STA_IN": R_STA_IN,
                        "R_ROT_OUT": R_ROT_OUT, "R_SHAFT": R_SHAFT,
                        "Z_ST0": Z_ST0, "Z_ST1": Z_ST1, "STACK": STACK, "ZC": ZC},
        "runs": runs,
        "comparison": build_comparison(runs, K),
        "figures": pngs,
        "_provenance": meta,
    }
    return doc


# =========================================================================== #
#  10. 드라이런 -- 합성 tet 메시로 전 경로를 Ansys 없이 돌린다                    #
# =========================================================================== #

_KUHN = ((0, 1, 3, 7), (0, 1, 5, 7), (0, 2, 3, 7),
         (0, 2, 6, 7), (0, 4, 5, 7), (0, 4, 6, 7))


def _hex_grid_tets(pts_fn, na, nb, nc):
    """(na,nb,nc) 육면체 격자를 Kuhn 6-tet 분할해 (Ne,4) 코너 인덱스를 만든다.

    pts_fn(i,j,k) -> (x,y,z).  격자점은 (na+1)*(nb+1)*(nc+1) 개.
    """
    P = np.empty(((na + 1) * (nb + 1) * (nc + 1), 3), dtype=np.float64)

    def pid(i, j, k):
        return (i * (nb + 1) + j) * (nc + 1) + k

    for i in range(na + 1):
        for j in range(nb + 1):
            for k in range(nc + 1):
                P[pid(i, j, k)] = pts_fn(i, j, k)
    cells = []
    for i in range(na):
        for j in range(nb):
            for k in range(nc):
                c = [pid(i + (v & 1), j + ((v >> 1) & 1), k + ((v >> 2) & 1))
                     for v in range(8)]
                for t in _KUHN:
                    cells.append([c[t[0]], c[t[1]], c[t[2]], c[t[3]]])
    return P, np.asarray(cells, dtype=np.int64)


def synthetic_table(n_slots=8, n_tan=3, n_rad=10, r_lo=0.0723, r_hi=0.0851,
                    slot_w=0.0046333, z_pad=0.025, n_stack=5, seed=DEF_SEED,
                    z_shift=0.0):
    """평행 슬롯 근사의 합성 tet 메시.  실제 메시 코드경로를 그대로 태운다.

    - mat 3 : 8 개 평행 슬롯 채널 (반경 r_lo..r_hi, 접선폭 slot_w),
              축방향으로 [Z_ST0 - z_pad, Z_ST1 + z_pad] (엔드턴 포함).
              z 분할은 Z_ST0/Z_ST1 에 정확히 맞춘다 -> 전이층 0.
    - mat 1/2/5/4 : 철손/자석손/샤프트 주입 경로를 살리기 위한 굵은 블록.
    z_shift 를 주면 스택면을 일부러 가로지르게 만들어 전이층 검출기를 시험한다.
    """
    blocks = []
    zs = [Z_ST0 - z_pad] + list(np.linspace(Z_ST0, Z_ST1, n_stack + 1)) \
        + [Z_ST1 + z_pad]
    zs = np.asarray(sorted(set(float(v) for v in zs)), dtype=np.float64) + z_shift
    nz = len(zs) - 1

    for s in range(n_slots):
        th = 2.0 * math.pi * s / float(n_slots)
        ct, st = math.cos(th), math.sin(th)

        def _pts(i, j, k, ct=ct, st=st):
            r = r_lo + (r_hi - r_lo) * i / float(n_rad)
            x = -0.5 * slot_w + slot_w * j / float(n_tan)
            z = zs[k]
            return (r * ct - x * st, r * st + x * ct, z)

        P, C = _hex_grid_tets(_pts, n_rad, n_tan, nz)
        blocks.append((P, C, M_CO))

    def _ring(rin, rout, z0, z1, nr, nt, nzz, mat):
        def _pts(i, j, k):
            r = rin + (rout - rin) * i / float(nr)
            a = 2.0 * math.pi * j / float(nt)
            z = z0 + (z1 - z0) * k / float(nzz)
            return (r * math.cos(a), r * math.sin(a), z)
        # 각도 방향은 닫지 않는다(격자를 단순하게 유지; 체적은 조금 작지만
        # 균일 주입 경로 검증에는 충분하다).
        P, C = _hex_grid_tets(_pts, nr, nt, nzz)
        blocks.append((P, C, mat))

    _ring(0.0870, 0.0990, Z_ST0, Z_ST1, 2, 12, 2, M_ST)      # 스테이터 요크
    _ring(0.0560, 0.0660, Z_ST0, Z_ST1, 1, 12, 2, M_MG)      # 자석
    _ring(0.0300, 0.0700, Z_ST0, Z_ST1, 2, 12, 2, M_RO)      # 로터
    _ring(0.0100, 0.0234, Z_ST0 - 0.02, Z_ST1 + 0.02, 1, 8, 2, M_SH)   # 샤프트

    pts = []
    conn = []
    emat = []
    off = 0
    for P, C, m in blocks:
        pts.append(P)
        conn.append(C + off)
        emat.append(np.full(len(C), m, dtype=np.int32))
        off += len(P)
    pts = np.vstack(pts)
    conn = np.vstack(conn)
    emat = np.concatenate(emat)
    corners = pts[conn[:, :4]]
    vol = tet_corner_volumes(corners)
    keep = vol > 0.0
    conn, emat, corners, vol = conn[keep], emat[keep], corners[keep], vol[keep]
    enum = np.arange(1, len(conn) + 1, dtype=np.int64)
    return {"points": pts, "conn": conn, "enum": enum, "emat": emat,
            "nnum": np.arange(1, len(pts) + 1, dtype=np.int64),
            "corners": corners, "vol": vol, "cen": corners.mean(axis=1),
            "n_elem": int(len(conn)), "n_node": int(len(pts)), "grid": None}


def synthetic_temperatures(tab, q_all, k_eff=5.0, L=0.00213, G_global=320.0,
                           P_total=0.0):
    """드라이런 전용 합성 온도장.  절대 물리값이 아니라 코드경로 검증용이다.

    T_node = 70 + P_total/G_global + <국소 q * L^2 / (2 k)>_(체적가중, 인접요소)

    L 은 층 반경 피치(2.13 mm), k_eff 는 균질화 권선의 5 W/mK, G_global 은
    검증된 하이브리드 런(3.35 kW -> 권선 152.2 °C)에서 역산한 전역 열컨덕턴스
    수준의 값이다.  이 함수는 MAPDL 을 대체하지 않는다 -- 후처리/비교/JSON 경로가
    실제 배열 모양으로 도는지 확인하는 용도다.
    """
    conn = tab["conn"]
    vol = tab["vol"]
    dT_e = np.asarray(q_all, dtype=np.float64) * (L * L) / (2.0 * k_eff)
    num = np.zeros(tab["n_node"], dtype=np.float64)
    den = np.zeros(tab["n_node"], dtype=np.float64)
    for j in range(conn.shape[1]):
        np.add.at(num, conn[:, j], dT_e * vol)
        np.add.at(den, conn[:, j], vol)
    loc = np.zeros(tab["n_node"], dtype=np.float64)
    nz = den > 0.0
    loc[nz] = num[nz] / den[nz]
    return OIL_T + float(P_total) / float(G_global) + loc


def dry_run(args, log):
    """MAPDL 없이: 손실 조회 -> 합성 메시 비닝 -> 불변량 -> 온도 -> JSON."""
    log("DRY RUN -- no MAPDL, no CDB, no rst. Exercising every non-Ansys path.")
    records = jm.load_map(args.map)
    log("map: %s (%d records)" % (args.map, len(records)))

    tab = synthetic_table(seed=args.seed)
    log("synthetic mesh: %d nodes / %d tets (mat3 = %d)"
        % (tab["n_node"], tab["n_elem"], int((tab["emat"] == M_CO).sum())))
    for m in sorted(set(int(x) for x in tab["emat"])):
        sel = tab["emat"] == m
        log("  mat %d (%-7s): n=%6d  V=%8.2f cm3"
            % (m, MAT_NAMES.get(m, "?"), int(sel.sum()), tab["vol"][sel].sum() * 1e6))

    binf = build_binning(tab, args.nturns, args.samples, args.seed, args.binning,
                         log, args.band_edges)
    sanity = sanity_report(binf, tab, log)

    # 전이층 검출기가 실제로 발화하는지 확인 (z 를 1 mm 밀어 일부러 걸치게)
    shifted = synthetic_table(seed=args.seed, z_shift=0.001)
    sV, sn = straddle_volume(shifted["corners"][shifted["emat"] == M_CO],
                             shifted["vol"][shifted["emat"] == M_CO], Z_ST0, Z_ST1)
    if not (sn > 0 and sV > 0.0):
        raise AssertionError("straddle detector did not fire on a deliberately "
                             "z-shifted mesh -- the transition-layer check is dead")
    log("straddle detector self-check: shifting z by 1 mm gives n=%d V=%.2f cm3 "
        "(fires correctly)" % (sn, sV * 1e6))

    runs = []
    invariants = {}
    for I in args.currents:
        loss = losses_for_point(records, args.speed, I, args.phase)
        log("losses @ %d rpm / %.6g A / %.1f deg :" % (args.speed, I, args.phase))
        log("  P_turn  = %s W" % ["%.3f" % v for v in loss["P_turn"]])
        log("  active  = %.4f W (dc %.4f + ac %.4f), end = %.4f W"
            % (loss["P_active"], loss["P_dc_active"], loss["P_ac_total"],
               loss["P_end"]))
        log("  fe_s=%.1f fe_r=%.1f pm=%.1f -> total %.1f W"
            % (loss["fe_s"], loss["fe_r"], loss["pm"], loss["P_total"]))
        qs = {}
        for mode in args.modes:
            qv = build_q_vectors(binf, mode, loss, log)
            qs[mode] = qv
        if len(qs) == 2:
            a = qs["uniform"]["injected_active_W"]
            b = qs["turnwise"]["injected_active_W"]
            rel = abs(a - b) / a
            if rel > 1e-12:
                raise AssertionError("uniform and turn-wise inject different totals: "
                                     "%.9f vs %.9f W (rel %.3e)" % (a, b, rel))
            log("  [inv ] uniform vs turnwise injected totals agree to rel %.2e" % rel)
        invariants["%.6g" % I] = {
            m: {"injected_active_W": qs[m]["injected_active_W"],
                "injected_end_W": qs[m]["injected_end_W"],
                "rel_err_active": qs[m]["rel_err_active"],
                "rel_err_end": qs[m]["rel_err_end"]} for m in qs}

        for mode in args.modes:
            qv = qs[mode]
            q_all = np.zeros(tab["n_elem"], dtype=np.float64)
            q_all[binf["act"]] = qv["q_act"]
            q_all[binf["end"]] = qv["q_end"]
            other = []
            for mat, W in ((M_ST, loss["fe_s"]), (M_MG, loss["pm"]),
                           (M_RO, loss["fe_r"])):
                sel = tab["emat"] == mat
                q_all[sel] = W / float(tab["vol"][sel].sum())
                other.append((tab["enum"][sel], W / float(tab["vol"][sel].sum())))

            # --- BFE 매크로 왕복 검증: moa 가 MAPDL 에 먹일 '그 텍스트' 그대로 ---
            mac = os.path.join(args.out, "hgen_%s_%dA.DRYRUN.mac"
                               % (mode, int(round(I))))
            nlines = write_hgen_macro(mac, tab["enum"][binf["act"]], qv["q_act"],
                                      tab["enum"][binf["end"]], qv["q_end"],
                                      other, log)
            back = read_hgen_macro(mac)
            if len(back) != nlines:
                raise AssertionError("BFE macro has %d lines but %d unique element "
                                     "ids -- an element is written twice"
                                     % (nlines, len(back)))
            vol_by_eid = dict(zip(tab["enum"].tolist(), tab["vol"].tolist()))
            re_inj = math.fsum(q * vol_by_eid[e] for e, q in back.items())
            rel = abs(re_inj - loss["P_total"]) / loss["P_total"]
            if rel > 1e-9:
                raise AssertionError("BFE macro round-trip lost power: the file "
                                     "injects %.6f W but the loss set is %.6f W "
                                     "(rel %.3e)" % (re_inj, loss["P_total"], rel))
            log("  [bfe ] round-trip: %d elements, sum(q*V)=%.6f W vs total %.6f W "
                "rel=%.2e" % (len(back), re_inj, loss["P_total"], rel))

            T = synthetic_temperatures(tab, q_all, P_total=loss["P_total"])
            _us = assert_physical(T, log)
            r = extract_run(T, tab, binf, loss, log)
            if _us:
                r["_undershoot"] = _us
            r.update({"speed": args.speed, "current": float(I),
                      "phase": args.phase, "mode": mode, "htc": args.htc_set,
                      "case": "AC",
                      "P_W": {"cu_active_total": loss["P_active"],
                              "cu_active_dc": loss["P_dc_active"],
                              "cu_active_ac": loss["P_ac_total"],
                              "cu_end": loss["P_end"],
                              "fe_s": loss["fe_s"], "fe_r": loss["fe_r"],
                              "pm": loss["pm"], "total": loss["P_total"]},
                      "P_turn_W": loss["P_turn"],
                      "injected_W": {"active": qv["injected_active_W"],
                                     "end": qv["injected_end_W"]},
                      "circuit_T": None, "energy_balance": None,
                      "rth": None, "solve_s": None,
                      "_synthetic_temperatures": True})
            runs.append(r)

    # 산출 PNG 가 .gitignore 에 삼켜지는지 미리 확인 (blocker: root .gitignore:39 *.png)
    gitchk = None
    if not args.no_git_check:
        would = [os.path.join(args.repo, "mlxperPJT", "thermal", "thesis_out",
                              "e10_ac_turnwise_zcut_%s_%dA.png"
                              % (m, int(round(args.png_current))))
                 for m in args.modes]
        gitchk = git_ignore_check(args.repo, would, log)

    meta = {"dry_run": True, "cdb": None, "run_dir": None, "git_check": gitchk,
            "n_elem_total": tab["n_elem"], "n_node_total": tab["n_node"],
            "map": args.map, "host": os.environ.get("COMPUTERNAME", ""),
            "python": sys.version.split()[0], "numpy": np.__version__,
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "note": ("DRY RUN: the mesh is a synthetic parallel-slot tet mesh and the "
                     "temperatures come from a local conduction proxy, NOT from "
                     "MAPDL. Only the loss lookup, the binning maths, the invariants "
                     "and the JSON schema are meaningful here.")}
    doc = assemble_json(args, binf, sanity, runs, [], meta)
    doc["_invariant_W"] = invariants
    doc["_dry_run"] = True
    return doc


# =========================================================================== #
#  11. 실행 (MAPDL)                                                             #
# =========================================================================== #

def real_run(args, log):
    from ansys.mapdl.core import launch_mapdl
    from ansys.mapdl.core.errors import MapdlRuntimeError

    cdb_file = args.cdb if args.cdb.lower().endswith(".cdb") else args.cdb + ".cdb"
    if not os.path.isfile(cdb_file):
        raise FileNotFoundError(
            "CDB not found: %s\n"
            "  ff_e10_mesh_v2.cdb is 260 MB and is NOT in git -- it lives only on moa "
            "at D:\\KDH\\simVary\\Ansys_Thermal\\ff_e10_mesh_v2.cdb.\n"
            "  If it is gone, the regeneration chain is 02c -> e10_geom.json -> 03 -> "
            "03b and takes hours. Pass --cdb explicitly if it moved." % cdb_file)
    log("cdb: %s (%.1f MB)" % (cdb_file, os.path.getsize(cdb_file) / 1e6))

    records = jm.load_map(args.map)
    log("map: %s (%d records)" % (args.map, len(records)))

    losses = {}
    for I in args.currents:
        losses[I] = losses_for_point(records, args.speed, I, args.phase)
        L = losses[I]
        log("losses @ %d rpm / %.6g A / %.1f deg : active %.3f W (dc %.3f + ac %.3f), "
            "end %.3f W, fe_s %.1f fe_r %.1f pm %.1f -> total %.1f W"
            % (args.speed, I, args.phase, L["P_active"], L["P_dc_active"],
               L["P_ac_total"], L["P_end"], L["fe_s"], L["fe_r"], L["pm"],
               L["P_total"]))
        log("  P_turn = %s W" % ["%.3f" % v for v in L["P_turn"]])

    if not os.path.isdir(args.run_dir):
        os.makedirs(args.run_dir)

    mapdl = None
    runs = []
    invariants = {}
    panels = []
    try:
        log("launching MAPDL (nproc=%d, run_location=%s)" % (args.nproc, args.run_dir))
        kw = {}
        if args.additional_switches:
            kw["additional_switches"] = args.additional_switches
        mapdl = launch_mapdl(run_location=args.run_dir, override=True,
                             nproc=args.nproc, loglevel="ERROR", **kw)
        log("MAPDL %s" % mapdl.version)

        tab, N = build_model(mapdl, args.cdb, args.htc_set, log)
        binf = build_binning(tab, args.nturns, args.samples, args.seed,
                             args.binning, log, args.band_edges)
        sanity = sanity_report(binf, tab, log)
        if sanity["verdict"] != "PASS" and not args.force:
            raise RuntimeError(
                "mesh/binning sanity verdict is %s -- refusing to burn solver time. "
                "Read the sanity block above, fix the cause, or re-run with --force "
                "if you accept it." % sanity["verdict"])

        idx = 0
        for I in args.currents:
            loss = losses[I]
            qs = {}
            for mode in args.modes:
                qs[mode] = build_q_vectors(binf, mode, loss, log)
            if len(qs) == 2:
                a = qs["uniform"]["injected_active_W"]
                b = qs["turnwise"]["injected_active_W"]
                rel = abs(a - b) / a
                if rel > 1e-12:
                    raise AssertionError("uniform and turn-wise inject different "
                                         "totals: %.9f vs %.9f W (rel %.3e)"
                                         % (a, b, rel))
                log("  [inv ] uniform vs turnwise injected totals agree to rel %.2e"
                    % rel)
            invariants["%.6g" % I] = {
                m: {"injected_active_W": qs[m]["injected_active_W"],
                    "injected_end_W": qs[m]["injected_end_W"],
                    "rel_err_active": qs[m]["rel_err_active"],
                    "rel_err_end": qs[m]["rel_err_end"]} for m in qs}

            for mode in args.modes:
                idx += 1
                tag = "%s_%dA" % (mode, int(round(I)))
                log("---- run %d/%d : %d rpm, %.6g A, %s, h=%s ----"
                    % (idx, len(args.currents) * len(args.modes), args.speed, I,
                       mode, args.htc_set))
                rth_name = "d2_%s" % tag
                rth_path = os.path.join(args.run_dir, rth_name + ".rth")
                try:
                    mapdl.finish()
                    mapdl.run("/ASSIGN,RTH,%s,rth" % rth_name)
                except MapdlRuntimeError as exc:
                    log("  [warn] /ASSIGN,RTH failed (%r); results go to file.rth"
                        % (exc,))
                    rth_path = os.path.join(args.run_dir, "file.rth")

                inj = apply_loads(mapdl, args.run_dir, tag, tab, binf, qs[mode],
                                  loss, log)
                dt = solve_steady(mapdl, idx, log, oil_node=N["OIL"])
                T, nsets = read_nodal_temperature(mapdl, tab, log)
                _us = assert_physical(T, log)
                circ = read_circuit(mapdl, N, log)
                ebal = energy_balance(mapdl, N["OIL"], inj, log)

                r = extract_run(T, tab, binf, loss, log)
                if _us:
                    r["_undershoot"] = _us
                r.update({"speed": args.speed, "current": float(I),
                          "phase": args.phase, "mode": mode, "htc": args.htc_set,
                          "case": "AC",
                          "P_W": {"cu_active_total": loss["P_active"],
                                  "cu_active_dc": loss["P_dc_active"],
                                  "cu_active_ac": loss["P_ac_total"],
                                  "cu_end": loss["P_end"],
                                  "fe_s": loss["fe_s"], "fe_r": loss["fe_r"],
                                  "pm": loss["pm"], "total": loss["P_total"]},
                          "P_turn_W": loss["P_turn"],
                          "injected_W": {"active": qs[mode]["injected_active_W"],
                                         "end": qs[mode]["injected_end_W"],
                                         "grand_total": inj},
                          "circuit_T": circ, "energy_balance": ebal,
                          "nsets": nsets, "solve_s": round(dt, 1),
                          "rth": rth_path if os.path.isfile(rth_path) else None})
                if r["rth"] is None:
                    log("  [warn] expected results file %s was not written -- "
                        "/ASSIGN,RTH did not take effect, so this run has no contour "
                        "figure (the JSON numbers above are still authoritative, they "
                        "were read in POST1 before the next run overwrote anything)."
                        % rth_path)
                else:
                    log("  [rth  ] %s (%.1f MB)"
                        % (r["rth"], os.path.getsize(r["rth"]) / 1e6))
                runs.append(r)
                if abs(I - args.png_current) <= 1e-6:
                    panels.append({"rth": r["rth"], "mode": mode, "current": float(I),
                                   "title": _panel_title(mode, args.speed, I,
                                                         r["T_C"]["winding_max"])})
        try:
            mapdl.finish()
            mapdl.run("/ASSIGN,RTH")
        except Exception:
            pass
    finally:
        if mapdl is not None:
            try:
                mapdl.exit()
            except Exception:
                pass
            log("MAPDL closed")

    pngs = []
    if not args.no_png and panels:
        try:
            pngs = render_contours(panels, args.out, args.run_dir, log)
        except Exception:
            log("figure generation failed:\n%s" % traceback.format_exc())
    elif args.no_png:
        log("figures skipped (--no-png)")

    gitchk = None
    if not args.no_git_check:
        gitchk = git_ignore_check(args.repo, [f["path"] for f in pngs], log)

    meta = {"dry_run": False, "cdb": cdb_file, "run_dir": args.run_dir,
            "git_check": gitchk,
            "n_elem_total": tab["n_elem"], "n_node_total": tab["n_node"],
            "map": args.map, "host": os.environ.get("COMPUTERNAME", ""),
            "python": sys.version.split()[0], "numpy": np.__version__,
            "nproc": args.nproc,
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S")}
    doc = assemble_json(args, binf, sanity, runs, pngs, meta)
    doc["_invariant_W"] = invariants
    doc["_dry_run"] = False
    return doc


def _panel_title(mode, speed, current, tmax):
    kr = {"uniform": "균일 주입", "turnwise": "턴별 주입 (T1 공극측 - T6 요크측)"}
    return ("%s - %s rpm %.6g A (권선 최고 %.0f °C)"
            % (kr.get(mode, mode), "{:,}".format(int(speed)), current, tmax))


# =========================================================================== #
#  12. CLI                                                                      #
# =========================================================================== #

def default_repo_root():
    """kit dir = <repo>/mlxperPJT/thermal/plans/PLAN_20260906_assets -> 4단계 위."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir, os.pardir,
                                        os.pardir))


def _currents(s):
    out = []
    for tok in str(s).replace(";", ",").split(","):
        tok = tok.strip()
        if tok:
            out.append(float(tok))
    if not out:
        raise argparse.ArgumentTypeError("--currents needs at least one value")
    return out


def _modes(s):
    out = []
    for tok in str(s).replace(";", ",").split(","):
        tok = tok.strip().lower()
        if not tok:
            continue
        if tok not in ("uniform", "turnwise"):
            raise argparse.ArgumentTypeError("mode must be uniform or turnwise, "
                                             "got %r" % tok)
        if tok not in out:
            out.append(tok)
    if not out:
        raise argparse.ArgumentTypeError("--modes needs at least one value")
    return out


def build_parser():
    p = argparse.ArgumentParser(
        prog="d2_ac_turnwise.py",
        description="D2 -- turn-wise vs uniform AC loss injection into the e10 "
                    "winding (steady, oil-circuit hybrid).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Dry run (no Ansys):  python d2_ac_turnwise.py --dry-run")
    p.add_argument("--repo", default=default_repo_root(),
                   help="repository root (default: resolved from this file)")
    p.add_argument("--map", default=None,
                   help="JEET AC loss map JSON (default: <repo>/%s)" % jm.MAP_REL)
    p.add_argument("--cdb", default=r"D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2",
                   help="CDB path, with or without the .cdb extension "
                        "(moa local only, 260 MB, not in git)")
    p.add_argument("--out", default=None,
                   help="output directory (default: <repo>/mlxperPJT/thermal/"
                        "thesis_out, or a temp dir for --dry-run)")
    p.add_argument("--out-name", dest="out_name", default=None,
                   help="output JSON name (default: e10_ac_turnwise_hotspot.json, "
                        "or ...DRYRUN.json with --dry-run)")
    p.add_argument("--run-dir", default=None, dest="run_dir",
                   help="MAPDL run_location (default: <tempdir>/d2_ac_turnwise_run)")
    p.add_argument("--log", default=None,
                   help="log file (default: <out>/d2_ac_turnwise.log)")
    p.add_argument("--nproc", type=int, default=4, help="MAPDL processors")
    p.add_argument("--phase", type=float, default=jm.PHASE_DEFAULT,
                   help="current phase advance in degrees (map convention)")
    p.add_argument("--speed", type=int, default=DEF_SPEED, help="rpm")
    p.add_argument("--currents", type=_currents, default=list(DEF_CURRENTS),
                   help="comma separated A_rms (default 230.05,460.0)")
    p.add_argument("--nturns", type=int, default=DEF_NTURNS,
                   help="number of radial turn bands (default 6)")
    p.add_argument("--modes", type=_modes, default=list(DEF_MODES),
                   help="comma separated: uniform,turnwise")
    p.add_argument("--htc-set", dest="htc_set", default="base",
                   choices=sorted(HTC_SETS.keys()),
                   help="convection set (D2 spec: base)")
    p.add_argument("--band-edges", default="width", choices=("width", "volume"),
                   help="radial band edges: 'width' = equal radial width (plan-literal), "
                        "'volume' = equal copper volume per band. The 6 hairpin layers "
                        "share one conductor cross-section, so equal VOLUME is what "
                        "actually corresponds to a layer; use it when width-based bands "
                        "come out unbalanced (moa: 0.12-0.20 vs the ideal 0.167).")
    p.add_argument("--binning", default="fractional",
                   choices=("fractional", "hard"),
                   help="fractional volume binning (default) or plan-literal "
                        "centroid hard binning")
    p.add_argument("--samples", type=int, default=DEF_SAMPLES,
                   help="uniform sample points per tetrahedron (default 64)")
    p.add_argument("--seed", type=int, default=DEF_SEED, help="sampling seed")
    p.add_argument("--png-current", dest="png_current", type=float, default=None,
                   help="current for the two contour panels (default: the largest "
                        "of --currents)")
    p.add_argument("--no-png", dest="no_png", action="store_true",
                   help="skip figure generation")
    p.add_argument("--force", action="store_true",
                   help="solve even if the mesh sanity verdict is WARN")
    p.add_argument("--additional-switches", dest="additional_switches", default="",
                   help="extra MAPDL launch switches passed to launch_mapdl")
    p.add_argument("--no-git-check", dest="no_git_check", action="store_true",
                   help="skip the `git check-ignore` self-check on the output PNGs")
    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   help="no MAPDL: synthetic mesh, loss lookup, binning, "
                        "invariants and JSON only")
    return p


def resolve_args(argv=None):
    args = build_parser().parse_args(argv)
    args.repo = os.path.abspath(args.repo)
    if args.map is None:
        args.map = jm.default_map_path(args.repo)
    args.map = os.path.abspath(args.map)
    if args.out is None:
        if args.dry_run:
            # 채널 규칙: 이 PC 는 plans/ 밖의 레포를 건드리지 않는다.
            args.out = os.path.join(tempfile.gettempdir(), "d2_ac_turnwise_dryrun")
        else:
            args.out = os.path.join(args.repo, "mlxperPJT", "thermal", "thesis_out")
    args.out = os.path.abspath(args.out)
    if args.run_dir is None:
        args.run_dir = os.path.join(tempfile.gettempdir(), "d2_ac_turnwise_run")
    args.run_dir = os.path.abspath(args.run_dir)
    if args.log is None:
        args.log = os.path.join(args.out, "d2_ac_turnwise.log")
    args.log = os.path.abspath(args.log)
    if args.png_current is None:
        args.png_current = max(args.currents)
    if args.nturns < 2:
        raise SystemExit("--nturns must be >= 2")
    if "turnwise" in args.modes and args.nturns != jm.N_TURNS:
        raise SystemExit(
            "--nturns %d conflicts with the map: fea_per_turn_raw carries exactly %d "
            "per-turn values, so turn-wise injection needs --nturns %d. Use "
            "--modes uniform if you only want to sweep the band count."
            % (args.nturns, jm.N_TURNS, jm.N_TURNS))
    if args.samples < 4:
        raise SystemExit("--samples must be >= 4")
    return args


def main(argv=None):
    args = resolve_args(argv)
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    log = Logger(args.log)
    rc = 0
    try:
        log("d2_ac_turnwise.py  --  D2 turn-wise vs uniform AC loss injection")
        log("repo     = %s" % args.repo)
        log("out      = %s" % args.out)
        log("run-dir  = %s" % args.run_dir)
        log("log      = %s" % args.log)
        log("speed    = %d rpm   phase = %.1f deg   nturns = %d"
            % (args.speed, args.phase, args.nturns))
        log("currents = %s A   modes = %s   htc = %s   binning = %s"
            % (args.currents, args.modes, args.htc_set, args.binning))
        log("python   = %s   numpy = %s" % (sys.version.split()[0], np.__version__))

        if args.dry_run:
            doc = dry_run(args, log)
            name = args.out_name or "e10_ac_turnwise_hotspot.DRYRUN.json"
        else:
            doc = real_run(args, log)
            name = args.out_name or "e10_ac_turnwise_hotspot.json"

        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
        log("saved %s (%.1f kB)" % (path, os.path.getsize(path) / 1e3))

        log("")
        log("HEADLINE")
        for key in sorted(doc.get("comparison", {}).keys(), key=float):
            c = doc["comparison"][key]
            log("  %s A : %s" % (key, c["headline"]))
        for f in doc.get("figures", []):
            log("  figure %s (%d bytes)" % (f["path"], f["bytes"]))
        log("sanity verdict: %s" % doc["_sanity"]["verdict"])
        log("DONE-OK")
    except Exception:
        log("FAILED:\n%s" % traceback.format_exc())
        rc = 1
    finally:
        log.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
