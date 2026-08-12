# -*- coding: utf-8 -*-
"""e10 NVH 논문용 그림 패키지 — 3D 모델 시각화 포함, 일관 스타일 틀.

산출(figs/):
  fig01_model3d.png       3D 모델·하중 개요: 스테이터 보어/OD 표면(실제 절점),
                          하우징(반투명), 로터 OD, 48 pilot + 치 힘 벡터
  fig02_excitation.png    전자계 가진: 치 힘 시간이력 + 시공간 스펙트럼(2D FFT)
  fig03_ods3d.png         3D ODS: 차수별 스테이터 OD 변형(워프+|u_r| 컬러)
  fig04_modal_compare.png 모달 비교표(단독 vs +하우징) + 가진차수 오버레이
  fig05_response_erp.png  응답·ERP 종합(차수별, 단독 vs 하우징)
  README_figs.md          그림별 영문 캡션 초안(논문 삽입용)

스타일: serif, 300dpi, colorblind-safe. 3D 는 PyVista off-screen.
"""
from __future__ import annotations

import json
import os
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FIGS = os.path.join(HERE, "figs")
os.makedirs(FIGS, exist_ok=True)

NPZ_S = os.path.join(DATA, "e10_harmonic_result.npz")
NPZ_H = os.path.join(DATA, "e10_housing_result.npz")
NODES = os.path.join(DATA, "e10_target_nodes.npz")
MF_JSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_multiforce.json"

R_BORE, R_OD = 0.0713, 0.0990
Z_ST0, Z_ST1 = -0.2075, -0.0575
STACK = Z_ST1 - Z_ST0
RHO0, C0, P_REF = 1.204, 343.0, 1e-12

plt.rcParams.update({
    "font.family": "serif", "font.size": 10,
    "axes.titlesize": 11, "axes.labelsize": 10,
    "figure.dpi": 100, "savefig.dpi": 300,
})
# colorblind-safe (Okabe-Ito)
C_BLUE, C_ORANGE, C_GREEN, C_RED = "#0072B2", "#E69F00", "#009E73", "#D55E00"
C_GRAY = "#999999"


def _save(fig, name):
    p = os.path.join(FIGS, name)
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", p)
    return p


def radial_amp(xyz, U):
    th = np.arctan2(xyz[:, 1], xyz[:, 0])
    return th, U[:, 0] * np.cos(th) + U[:, 1] * np.sin(th)


# ============================================================ fig01: 3D model
def fig01_model3d():
    import pyvista as pv
    pv.OFF_SCREEN = True
    nz = np.load(NODES)
    d = json.load(open(MF_JSON, encoding="utf-8"))
    lp = d["loadPointDefinition"][4]
    se = lp["excitationData"]["statorExcitation"]
    tnode = {n["nodeID"]: n for n in d["statorNodeLocations"]["statorNodes"]}

    pl = pv.Plotter(off_screen=True, window_size=(1800, 1300))
    pl.set_background("white")

    def cloud(key, color, size=2.0, opacity=1.0, half=True):
        pts = nz[key]
        if half:                       # 하프 컷(y<0 제거) → 내부 구조 노출
            pts = pts[pts[:, 1] <= 0.002]
        pl.add_points(pv.PolyData(pts), color=color, point_size=size,
                      render_points_as_spheres=True, opacity=opacity)

    cloud("bore_xyz", "#CC3311", 3.0)              # 스테이터 보어(하중면)
    cloud("statorOD_xyz", "#0072B2", 3.0)          # 스테이터 OD
    cloud("rotorOD_xyz", "#666666", 2.2, 0.85)     # 로터 OD(참고)
    # 하우징: 반투명 하프 원통 셸(θ ∈ [180°, 360°])
    tg = np.linspace(np.pi, 2 * np.pi, 61)
    zg = np.linspace(Z_ST0 - 0.02, Z_ST1 + 0.02, 13)
    TH, ZZ = np.meshgrid(tg, zg, indexing="ij")
    for rr, op in ((R_OD + 0.0005, 0.30), (R_OD + 0.008, 0.30)):
        X = rr * np.cos(TH); Y = rr * np.sin(TH)
        pl.add_mesh(pv.StructuredGrid(X, Y, ZZ), color="#88CCEE",
                    opacity=op, show_edges=False, smooth_shading=True)

    # 48 pilot + t0 치 힘 벡터
    zc = 0.5 * (Z_ST0 + Z_ST1)
    pts, vecs = [], []
    for e in se:
        r_mm, th_deg = tnode[e["nodeID"]]["nodeCoord"]
        th = np.deg2rad(th_deg)
        p = [R_BORE * np.cos(th), R_BORE * np.sin(th), zc]
        fr, ft = e["forceRValues"][0], e["forceTValues"][0]
        fx = np.cos(th) * fr - np.sin(th) * ft
        fy = np.sin(th) * fr + np.cos(th) * ft
        pts.append(p); vecs.append([fx, fy, 0.0])
    pts = np.array(pts); vecs = np.array(vecs)
    vmag = np.linalg.norm(vecs, axis=1)
    pl.add_points(pv.PolyData(pts), color="black", point_size=9,
                  render_points_as_spheres=True)
    arrows = pv.PolyData(pts)
    arrows["vec"] = vecs / vmag.max() * 0.035      # 길이 정규화(도면 스케일)
    arrows["mag"] = vmag
    glyph = arrows.glyph(orient="vec", scale="vec", factor=1.0)
    pl.add_mesh(glyph, scalars=None, color="#CC3311")

    pl.camera_position = [(0.34, -0.42, 0.20), (0, 0, zc), (0, 0, 1)]
    pl.camera.zoom(1.25)
    pl.add_text("e10 IPMSM 48s/8p — stator surfaces, housing (half-cut), "
                "per-tooth pilots & forces (t=0)",
                font_size=13, color="black", position="upper_left")
    img = os.path.join(FIGS, "fig01_model3d.png")
    pl.screenshot(img)
    pl.close()
    print("saved", img)


# ============================================================ fig02: excitation
def fig02_excitation():
    d = json.load(open(MF_JSON, encoding="utf-8"))
    lp = d["loadPointDefinition"][4]
    f_elec = lp["speedPoint"] / 60 * 4
    se = lp["excitationData"]["statorExcitation"]
    Fr = np.array([e["forceRValues"] for e in se])   # (48,128)
    Ft = np.array([e["forceTValues"] for e in se])
    N = Fr.shape[1]
    t = np.arange(N) / N / f_elec * 1e3              # ms

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.6))
    ax = axes[0]
    ax.plot(t, Fr[0], color=C_BLUE, lw=1.2, label="$F_r$")
    ax.plot(t, Ft[0], color=C_ORANGE, lw=1.2, label="$F_t$")
    ax.set_xlabel("time [ms]"); ax.set_ylabel("tooth force [N]")
    ax.set_title("(a) tooth #1 force, one elec. period")
    ax.legend(frameon=False); ax.grid(alpha=0.3)

    ax = axes[1]
    k = np.arange(1, N // 2)
    Ak = np.abs(np.fft.fft(Fr[0]))[1:N // 2] / N * 2
    ax.stem(k[:20], Ak[:20], basefmt=" ", linefmt=C_BLUE, markerfmt="o")
    ax.set_xlabel("temporal order $k$ (× $f_e$)"); ax.set_ylabel("$|F_r|$ [N]")
    ax.set_title("(b) temporal spectrum (tooth #1)")
    ax.grid(alpha=0.3)

    ax = axes[2]
    # 시공간 2D FFT: 공간(48치)×시간(128)
    F2 = np.fft.fft2(Fr) / Fr.size
    mag = np.abs(np.fft.fftshift(F2))
    ax.imshow(np.log10(mag + 1e-3), aspect="auto", origin="lower",
              extent=[-N // 2, N // 2, -24, 24], cmap="viridis")
    ax.set_xlim(-16, 16); ax.set_ylim(-16, 16)
    ax.set_xlabel("temporal order $k$"); ax.set_ylabel("spatial order $n$")
    ax.set_title("(c) space–time spectrum $\\log_{10}|F_r(n,k)|$")
    fig.suptitle(f"Electromagnetic excitation — Motor-CAD multiforce, "
                 f"{lp['speedPoint']} rpm ($f_e$={f_elec:.0f} Hz)", y=1.04,
                 fontsize=12)
    fig.tight_layout()
    _save(fig, "fig02_excitation.png")


# ============================================================ fig03: 3D ODS
def fig03_ods3d():
    import pyvista as pv
    pv.OFF_SCREEN = True
    ds = np.load(NPZ_S)
    orders = [int(k) for k in ds["orders"]]
    f_elec = float(ds["f_elec"])
    sel = orders[:3] if len(orders) <= 3 else [2, 6, 10]

    pl = pv.Plotter(shape=(1, len(sel)), off_screen=True,
                    window_size=(560 * len(sel), 640))
    pl.set_background("white")
    for i, k in enumerate(sel):
        xyz = ds[f"k{k}_xyz"]; U = ds[f"k{k}_U"]
        th, ur = radial_amp(xyz, U)
        # (θ,z) 규칙격자 보간 → 원통 표면 + 반경 워프.
        # 각도 주기성: 소스를 ±2π 복제해 seam(θ=±π 경계 결손) 제거.
        tg = np.linspace(-np.pi, np.pi, 181)
        zg = np.linspace(xyz[:, 2].min(), xyz[:, 2].max(), 61)
        TH, ZZ = np.meshgrid(tg, zg, indexing="ij")
        from scipy.interpolate import griddata
        th3 = np.concatenate([th - 2 * np.pi, th, th + 2 * np.pi])
        z3 = np.tile(xyz[:, 2], 3)
        ur3 = np.tile(ur, 3)
        pts2 = np.column_stack([th3, z3])
        amp = griddata(pts2, np.abs(ur3), (TH, ZZ), method="linear")
        pha = griddata(pts2, np.angle(ur3), (TH, ZZ), method="nearest")
        amp = np.nan_to_num(amp, nan=0.0)
        scale = 0.006 / max(np.abs(ur).max(), 1e-12)     # 최대 6mm 워프
        Rw = R_OD + scale * amp * np.cos(pha)
        X = Rw * np.cos(TH); Y = Rw * np.sin(TH)
        grid = pv.StructuredGrid(X, Y, ZZ)
        sname = f"|u_r| [µm]  (k={k})"          # 패널별 스칼라명 → 개별 컬러바
        grid[sname] = (amp * 1e6).ravel(order="F")
        pl.subplot(0, i)
        pl.add_mesh(grid, scalars=sname, cmap="inferno",
                    smooth_shading=True, show_scalar_bar=True,
                    scalar_bar_args=dict(title=sname, fmt="%.2f",
                                         label_font_size=12, title_font_size=13,
                                         position_x=0.25, position_y=0.02,
                                         width=0.5, height=0.07))
        pl.add_text(f"k={k}  ({k*f_elec/1000:.0f} kHz)", font_size=12, color="black")
        pl.camera_position = [(0.30, -0.28, 0.10),
                              (0, 0, 0.5 * (Z_ST0 + Z_ST1)), (0, 0, 1)]
    img = os.path.join(FIGS, "fig03_ods3d.png")
    pl.screenshot(img); pl.close()
    print("saved", img)


# ============================================================ fig04: modal
def fig04_modal():
    ds = np.load(NPZ_S)
    fs = ds["freqs_modal"]; es = fs[fs > 1]
    f_elec = float(ds["f_elec"])
    orders_all = [int(k) for k in ds["orders"]]
    try:
        dh = np.load(NPZ_H)
        eh = dh["freqs_modal"][dh["freqs_modal"] > 1]
    except Exception:
        eh = np.array([])

    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.vlines(es, 1.15, 1.85, color=C_BLUE, lw=1.6)
    if len(eh):
        ax.vlines(eh, 0.15, 0.85, color=C_GREEN, lw=1.6)
    for k in orders_all:
        ax.axvline(k * f_elec, color=C_RED, ls="--", lw=1.1, alpha=0.85)
        ax.text(k * f_elec, 1.97, f"k={k}", color=C_RED, ha="center", fontsize=9)
    ax.set_yticks([0.5, 1.5])
    ax.set_yticklabels(["stator + housing", "stator only"])
    ax.set_ylim(0, 2.1)
    ax.set_xlabel("frequency [Hz]")
    ax.set_title("Free–free elastic modes vs excitation orders "
                 f"({float(ds['rpm']):.0f} rpm, $f_e$={f_elec:.0f} Hz)")
    ax.grid(axis="x", alpha=0.25)
    _save(fig, "fig04_modal_compare.png")


# ============================================================ fig05: response/ERP
def fig05_response_erp():
    ds = np.load(NPZ_S)
    f_elec = float(ds["f_elec"])
    orders = sorted(int(k) for k in ds["orders"])
    try:
        dh = np.load(NPZ_H)
        h_orders = [int(k) for k in dh["orders"]]
        R_hout = float(dh["R_hout"]); oh = float(dh["hous_oh"])
    except Exception:
        dh, h_orders = None, []

    def erp_of(xyz, U, freq, radius, length):
        _, ur = radial_amp(xyz, U)
        Ai = 2 * np.pi * radius * length / len(ur)
        om = 2 * np.pi * freq
        return 0.5 * RHO0 * C0 * np.sum(Ai * (om * np.abs(ur)) ** 2)

    umax_s, lw_s, umax_h, lw_h = [], [], [], []
    for k in orders:
        f = k * f_elec
        _, ur = radial_amp(ds[f"k{k}_xyz"], ds[f"k{k}_U"])
        umax_s.append(np.abs(ur).max() * 1e6)
        lw_s.append(10 * np.log10(erp_of(ds[f"k{k}_xyz"], ds[f"k{k}_U"], f,
                                         R_OD, STACK) / P_REF))
        if dh is not None and k in h_orders:
            _, urh = radial_amp(dh[f"k{k}_h_xyz"], dh[f"k{k}_h_U"])
            umax_h.append(np.abs(urh).max() * 1e6)
            lw_h.append(10 * np.log10(erp_of(dh[f"k{k}_h_xyz"], dh[f"k{k}_h_U"], f,
                                             R_hout, STACK + 2 * oh) / P_REF))
        else:
            umax_h.append(np.nan); lw_h.append(np.nan)

    x = np.arange(len(orders))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.0))
    ax1.bar(x - 0.2, umax_s, 0.4, color=C_BLUE, label="stator OD (stator-only)")
    ax1.bar(x + 0.2, umax_h, 0.4, color=C_GREEN, label="housing outer (+housing)")
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"k={k}\n{k*f_elec/1000:.0f} kHz" for k in orders])
    ax1.set_ylabel("max $|u_r|$ [µm]")
    ax1.set_title("(a) radial response amplitude")
    ax1.legend(frameon=False, fontsize=8.5); ax1.grid(axis="y", alpha=0.3)

    ax2.bar(x - 0.2, lw_s, 0.4, color=C_BLUE, label="stator-only")
    ax2.bar(x + 0.2, lw_h, 0.4, color=C_GREEN, label="+housing")
    for xi, (a, b) in enumerate(zip(lw_s, lw_h)):
        ax2.text(xi - 0.2, a + 0.4, f"{a:.1f}", ha="center", fontsize=8)
        if not np.isnan(b):
            ax2.text(xi + 0.2, b + 0.4, f"{b:.1f}", ha="center", fontsize=8)
    ax2.set_xticks(x); ax2.set_xticklabels([f"k={k}" for k in orders])
    ax2.set_ylabel("$L_W$ [dB re 1 pW]  ($\\sigma_{rad}$=1)")
    ax2.set_title("(b) equivalent radiated power")
    ax2.legend(frameon=False, fontsize=8.5); ax2.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    _save(fig, "fig05_response_erp.png")


# ============================================================ fig06: Campbell
def _load_exp_overlay():
    """실험 오버레이 데이터 로더(틀). exp_data/*.csv:
        order_level 스키마: rpm, k, freq_Hz, Lw_dB   (차수추출 레벨)
    파일이 없으면 None — 그림은 시뮬레이션만으로 그려진다."""
    import glob, csv
    rows = []
    for p in glob.glob(os.path.join(HERE, "exp_data", "*.csv")):
        with open(p, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                try:
                    rows.append((float(r["rpm"]), float(r["freq_Hz"]),
                                 float(r.get("Lw_dB", "nan"))))
                except Exception:
                    continue
    return np.array(rows) if rows else None


def fig06_campbell():
    dc = np.load(os.path.join(DATA, "e10_campbell.npz"))
    rows = dc["rows"]                      # (rpm, k, freq, umax, umean, erp)
    fs = dc["freqs_modal"]; es = fs[fs > 1]
    try:
        eh = np.load(NPZ_H)["freqs_modal"]
        eh = eh[eh > 1]
    except Exception:
        eh = np.array([])

    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    rpm_max = 16000
    # 모드 수평선
    for f in es:
        ax.axhline(f, color=C_BLUE, lw=0.8, alpha=0.55)
    for f in eh:
        ax.axhline(f, color=C_GREEN, lw=0.8, ls=":", alpha=0.6)
    # 차수선 f = k·rpm/15
    rr = np.linspace(0, rpm_max, 50)
    for k in sorted(set(int(x) for x in rows[:, 1])):
        ax.plot(rr, k * rr / 15.0, color=C_GRAY, lw=0.9, ls="--")
        ax.text(rpm_max * 1.005, k * rpm_max / 15.0, f"k={k}",
                fontsize=8.5, color="#555", va="center")
    # 응답 버블(Lw)
    lw = 10 * np.log10(np.maximum(rows[:, 5], 1e-30) / P_REF)
    sc = ax.scatter(rows[:, 0], rows[:, 2], s=np.clip((lw - 30) * 4, 8, 260),
                    c=lw, cmap="inferno", vmin=40, vmax=95,
                    edgecolors="k", linewidths=0.4, zorder=5)
    cb = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("$L_W$ [dB re 1 pW] ($\\sigma_{rad}$=1)")
    # 실험 오버레이(있을 때만)
    exp = _load_exp_overlay()
    if exp is not None:
        ax.scatter(exp[:, 0], exp[:, 1], marker="*", s=140, c="k", zorder=6,
                   label="measured")
        ax.legend(frameon=False, loc="upper left")
    ax.set_xlim(0, rpm_max * 1.06); ax.set_ylim(0, 13000)
    ax.set_xlabel("speed [rpm]"); ax.set_ylabel("frequency [Hz]")
    ax.set_title("Campbell diagram — force orders vs stator modes "
                 "(bubbles: simulated ERP at 5 load points)")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=C_BLUE, lw=1.2, label="stator-only modes"),
               Line2D([], [], color=C_GREEN, lw=1.2, ls=":", label="+housing modes"),
               Line2D([], [], color=C_GRAY, lw=1, ls="--", label="order lines $k f_e$")]
    if exp is not None:
        handles.append(Line2D([], [], marker="*", color="k", lw=0, ms=12,
                              label="measured"))
    ax.legend(handles=handles, frameon=False, fontsize=8.5, loc="upper left")
    _save(fig, "fig06_campbell.png")


# ============================================================ fig07: mode shapes
def fig07_mode_shapes(n_show=6):
    import pyvista as pv
    from scipy.interpolate import griddata
    pv.OFF_SCREEN = True
    dm = np.load(os.path.join(DATA, "e10_mode_shapes.npz"))
    mf = dm["mode_freqs"]; MU = dm["mode_U"]; xyz = dm["xyz"]
    th = np.arctan2(xyz[:, 1], xyz[:, 0])
    zmid = np.abs(xyz[:, 2] - 0.5 * (Z_ST0 + Z_ST1)) < 0.008

    # 이중근 쌍 제거(주파수 0.5% 이내는 같은 모드) 후 앞에서 n_show개
    sel, last = [], -1e9
    for i, f in enumerate(mf):
        if f > last * 1.005:
            sel.append(i); last = f
        if len(sel) >= n_show:
            break

    ncol = 3; nrow = int(np.ceil(len(sel) / ncol))
    pl = pv.Plotter(shape=(nrow, ncol), off_screen=True,
                    window_size=(520 * ncol, 560 * nrow))
    pl.set_background("white")
    tg = np.linspace(-np.pi, np.pi, 181)
    zg = np.linspace(xyz[:, 2].min(), xyz[:, 2].max(), 61)
    TH, ZZ = np.meshgrid(tg, zg, indexing="ij")
    th3 = np.concatenate([th - 2 * np.pi, th, th + 2 * np.pi])
    z3 = np.tile(xyz[:, 2], 3)
    for j, i in enumerate(sel):
        U = MU[i]                                   # (Nod,3) 실수 고유벡터
        ur = U[:, 0] * np.cos(th) + U[:, 1] * np.sin(th)
        # 원주차수 추정: 축방향 절선 회피 — 신호가 가장 큰 z-밴드에서 FFT
        tgm = np.linspace(-np.pi, np.pi, 256, endpoint=False)
        best_spec, best_pw = None, -1.0
        for zc_band in np.linspace(xyz[:, 2].min() + 0.01,
                                   xyz[:, 2].max() - 0.01, 5):
            m = np.abs(xyz[:, 2] - zc_band) < 0.008
            if m.sum() < 50:
                continue
            o = np.argsort(th[m])
            ug = np.interp(tgm, th[m][o], ur[m][o], period=2 * np.pi)
            pw = np.sum((ug - ug.mean()) ** 2)
            if pw > best_pw:
                best_pw = pw
                best_spec = np.abs(np.fft.rfft(ug - ug.mean()))
        n_circ = int(np.argmax(best_spec[1:11]) + 1)   # n≤10 (물리적 상한)
        # 축방향 차수(0/1) 간이판별: 상·하단 θ-프로파일 내적 부호(반대위상 → m=1)
        def _prof(mask):
            o = np.argsort(th[mask])
            return np.interp(tgm, th[mask][o], ur[mask][o], period=2 * np.pi)
        zmin, zmax = xyz[:, 2].min(), xyz[:, 2].max()
        p_lo = _prof(np.abs(xyz[:, 2] - (zmin + 0.015)) < 0.01)
        p_hi = _prof(np.abs(xyz[:, 2] - (zmax - 0.015)) < 0.01)
        m_ax = 1 if np.dot(p_lo - p_lo.mean(), p_hi - p_hi.mean()) < 0 else 0
        # 형상 보간·워프
        ur3 = np.tile(ur, 3)
        amp = np.nan_to_num(griddata(np.column_stack([th3, z3]), ur3,
                                     (TH, ZZ), method="linear"), nan=0.0)
        scale = 0.007 / max(np.abs(ur).max(), 1e-12)
        Rw = R_OD + scale * amp
        grid = pv.StructuredGrid(Rw * np.cos(TH), Rw * np.sin(TH), ZZ)
        sname = f"u_r (mode {j+1})"
        grid[sname] = amp.ravel(order="F") / max(np.abs(ur).max(), 1e-12)
        pl.subplot(j // ncol, j % ncol)
        pl.add_mesh(grid, scalars=sname, cmap="RdBu_r", clim=[-1, 1],
                    smooth_shading=True, show_scalar_bar=False)
        pl.add_text(f"({n_circ},{m_ax})  {mf[i]:.0f} Hz", font_size=12, color="black")
        pl.camera_position = [(0.30, -0.28, 0.10),
                              (0, 0, 0.5 * (Z_ST0 + Z_ST1)), (0, 0, 1)]
    img = os.path.join(FIGS, "fig07_mode_shapes.png")
    pl.screenshot(img); pl.close()
    print("saved", img)


# ============================================================ captions
CAPTIONS = """# e10 NVH — paper figure set (draft captions)

*Generated by `e10_paper_figs.py`. 300 dpi, serif, Okabe–Ito colours. Update
numbers after final runs.*

**Fig. 1 (fig01_model3d.png).** Three-dimensional overview of the e10 IPMSM
(48 slots / 8 poles) electromagnetic-to-structural coupling model: stator bore
(red) and outer-diameter (blue) surface nodes extracted from the structural
mesh (1.11 M nodes, SOLID187), rotor OD nodes (grey), parametric aluminium
housing (translucent), and the 48 per-tooth pilot nodes (black) carrying the
Motor-CAD tooth-force resultants (red arrows, t = 0) via RBE3 distributed
coupling.

**Fig. 2 (fig02_excitation.png).** Electromagnetic excitation at 15 000 rpm
(f_e = 1 kHz), from the Motor-CAD multiforce export (128 samples / electrical
period): (a) radial and tangential force on one tooth; (b) temporal spectrum,
dominated by even orders k = 2, 4, 6 with slot-interaction content at k = 10,
12; (c) space–time spectrum over the 48 teeth.

**Fig. 3 (fig03_ods3d.png).** Operating deflection shapes of the stator outer
surface at the dominant force orders (full harmonic solution, free–free
stator): radial displacement magnitude (colour) with radial warp exaggerated
for visualisation.

**Fig. 4 (fig04_modal_compare.png).** Free–free elastic modes of the stator
core alone (top) and with the bonded aluminium housing (bottom), against the
excitation orders (dashed). The housing raises all wall-bending modes by
30–44 %, relocating resonances relative to the fixed excitation grid.

**Fig. 5 (fig05_response_erp.png).** Harmonic response and equivalent
radiated power per force order: (a) maximum radial displacement on the
emitting surface; (b) ERP (σ_rad = 1). The housing attenuates all orders
(−1.4 to −6.7 dB) while k = 6 remains dominant.

**Fig. 6 (fig06_campbell.png).** Campbell diagram: excitation order lines
(k = 2–12, dashed) against the free–free stator modes (solid) and
stator-plus-housing modes (dotted); bubbles show the simulated ERP at the
5 × 5 load-point/order grid (250–15 000 rpm). The critical point is **not**
at rated speed: at 8 900 rpm the k = 12 order crosses the 7.1 kHz mode
cluster (114.5 dB, undamped upper bound — 25 dB above the rated-speed
maximum). Harmonic solutions are undamped, so on-resonance levels are upper
bounds; off-resonance values are damping-insensitive. Measured order levels,
when available in `exp_data/*.csv`, are overlaid automatically (star markers).

**Fig. 7 (fig07_mode_shapes.png).** Representative free–free stator mode
shapes (outer-surface radial displacement, normalised, warp exaggerated),
labelled by circumferential order n and natural frequency.

## Reproduction
```
python mlxperPJT/nvh/e10_harmonic_response.py     # stator-only harmonics
ORDERS=2,6,10 python mlxperPJT/nvh/e10_housing_harmonic.py
python mlxperPJT/nvh/e10_campbell_modes.py        # Campbell sweep + mode shapes
python mlxperPJT/nvh/e10_paper_figs.py
```

## Experimental overlay
No e10 NVH measurements exist yet. Drop order-tracked CSVs into
`exp_data/` (schema in `exp_data/README_exp.md`) and re-run
`e10_paper_figs.py` — Fig. 6 gains measured star markers automatically.
Compare order ranking and rpm trends first (σ_rad = 1 caveat for absolute dB).
"""


def main():
    fig02_excitation()
    fig04_modal()
    fig05_response_erp()
    try:
        fig01_model3d()
    except Exception as e:
        print("[warn] fig01 3D:", repr(e)[:200])
    try:
        fig03_ods3d()
    except Exception as e:
        print("[warn] fig03 3D:", repr(e)[:200])
    # fig06/07 은 e10_campbell_modes.py 산출이 있을 때만
    if os.path.exists(os.path.join(DATA, "e10_campbell.npz")):
        try:
            fig06_campbell()
        except Exception as e:
            print("[warn] fig06:", repr(e)[:200])
    if os.path.exists(os.path.join(DATA, "e10_mode_shapes.npz")):
        try:
            fig07_mode_shapes()
        except Exception as e:
            print("[warn] fig07:", repr(e)[:200])
    open(os.path.join(FIGS, "README_figs.md"), "w", encoding="utf-8").write(CAPTIONS)
    print("saved", os.path.join(FIGS, "README_figs.md"))


if __name__ == "__main__":
    main()
