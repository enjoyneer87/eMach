"""
plot_efficiency_map.py
----------------------
run_efficiency_map.py 가 생성한 efficiency_map_results.mat 을 읽어
논문용 그래프 4종을 생성한다.

생성 그래프:
  Fig 1  — 효율맵 3종 비교  (Ref / HalfSC / SC)  [eta_comparison]
  Fig 2  — β_opt 맵 3종 비교  (전류위상각)        [beta_comparison]
  Fig 3  — 손실 분해 맵  3×3  (모델 × 손실종류)   [loss_decomposition]
  Fig 4  — Calibration 효과 Δη = SC − Ref          [delta_eta]

저장 경로: mlxperPJT/JEET/figures/ (없으면 자동 생성)
"""

import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path
from scipy.io import loadmat

# ── 경로 설정 ───────────────────────────────────────────────────────────────
current_dir = Path(__file__).parent.resolve()
emach_root  = current_dir.parent.parent.resolve()

INPUT_PATH  = current_dir / "efficiency_map_results.mat"
FIGURE_DIR  = current_dir / "figures"

# ── 논문용 matplotlib 전역 설정 ─────────────────────────────────────────────
mpl.rcParams.update({
    "font.family":        "DejaVu Sans",
    "font.size":          9,
    "axes.labelsize":     9,
    "axes.titlesize":     10,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "legend.fontsize":    8,
    "figure.dpi":         150,          # 화면 표시용 (저장은 300 dpi)
    "savefig.dpi":        300,
    "axes.linewidth":     0.8,
    "grid.linewidth":     0.5,
    "lines.linewidth":    1.0,
    "patch.linewidth":    0.6,
    "xtick.direction":    "in",
    "ytick.direction":    "in",
    "xtick.major.width":  0.8,
    "ytick.major.width":  0.8,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
})

# 컬러맵 모음
CMAP_ETA   = "jet"          # 효율맵: 고대비 일반 컬러맵
CMAP_BETA  = "plasma"       # β_opt: 단조 증가
CMAP_LOSS  = "hot_r"        # 손실: 낮을수록 밝음 (역전)
CMAP_DELTA = "RdBu_r"       # 차이맵: 발산형 (양수=적색)

MODELS        = ['Ref', 'HalfSC', 'SC']
MODEL_LABELS  = ['Ref', 'HalfSC', 'SC']
LOSS_KEYS     = ['loss_cu_dc_kW', 'loss_cu_ac_kW', 'loss_fe_kW']
LOSS_LABELS   = [r'$P_{\mathrm{Cu,DC}}$ [kW]',
                 r'$P_{\mathrm{Cu,AC}}$ [kW]',
                 r'$P_{\mathrm{Fe}}$ [kW]']
LOSS_TITLES   = ['Cu DC Loss', 'Cu AC Loss', 'Iron Loss']


# ────────────────────────────────────────────────────────────────────────────
# 유틸리티
# ────────────────────────────────────────────────────────────────────────────
def _save(fig: plt.Figure, stem: str) -> None:
    """figures/ 폴더에 PNG 저장."""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURE_DIR / f"{stem}.png"
    fig.savefig(str(out), bbox_inches="tight", dpi=300)
    print(f"  → 저장: {out.relative_to(current_dir)}")


def _add_colorbar(fig, ax, mappable, label: str, pad: float = 0.03) -> None:
    cb = fig.colorbar(mappable, ax=ax, pad=pad, aspect=20, shrink=0.85)
    cb.set_label(label, labelpad=4)
    cb.ax.tick_params(labelsize=7)


def _speed_km(speed_rpm: np.ndarray) -> np.ndarray:
    """RPM 축 레이블을 1000 RPM 단위로 변환."""
    return speed_rpm / 1000.0


def _mark_max_eta(ax, X, Y, eta_2d: np.ndarray, color: str = "gold") -> None:
    """최대 효율점을 ☆ 마커로 표시한다."""
    flat_idx = np.nanargmax(eta_2d)
    ti, si   = np.unravel_index(flat_idx, eta_2d.shape)
    ax.plot(X[si], Y[ti],
            marker="*", markersize=10, color=color,
            markeredgecolor="k", markeredgewidth=0.6,
            zorder=10, linestyle="none",
            label=f"Max η = {eta_2d[ti, si]:.2f}%")


def _contourf_eta(ax, X, Y, eta_2d: np.ndarray, **kwargs) -> mpl.contour.QuadContourSet:
    """효율 contourf + 경계선 겹쳐 그리기."""
    levels_f = np.linspace(np.nanpercentile(eta_2d, 2),
                           np.nanpercentile(eta_2d, 99), 40)
    cf = ax.contourf(X, Y, eta_2d, levels=levels_f,
                     cmap=CMAP_ETA, **kwargs)
    # 주요 효율 등고선 (85, 90, 93, 95, 96, 97%)
    iso_vals = [v for v in [85, 88, 90, 92, 93, 94, 95, 96, 97, 98]
                if np.nanmin(eta_2d) < v < np.nanmax(eta_2d)]
    if iso_vals:
        cs = ax.contour(X, Y, eta_2d, levels=iso_vals,
                        colors="white", linewidths=0.5, alpha=0.7)
        ax.clabel(cs, fmt="%d%%", fontsize=7, inline=True, inline_spacing=2)
    return cf


def _apply_xy_labels(ax, xlabel: bool = True, ylabel: bool = True) -> None:
    if xlabel:
        ax.set_xlabel("Speed [×10³ RPM]")
    if ylabel:
        ax.set_ylabel("Torque [Nm]")


# ────────────────────────────────────────────────────────────────────────────
# 데이터 로드
# ────────────────────────────────────────────────────────────────────────────
def load_data(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"결과 파일을 찾을 수 없습니다: {path}\n"
            "  → 먼저 run_efficiency_map.py 를 실행하세요."
        )
    raw = loadmat(str(path))
    d = {
        "eta_pct":       np.squeeze(raw["eta_pct"]),        # (n_T, n_S, 3)
        "speed_rpm":     np.squeeze(raw["speed_rpm"]),      # (n_S,)
        "torque_nm":     np.squeeze(raw["torque_nm"]),      # (n_T,)
        "beta_deg":      np.squeeze(raw["beta_deg"]),       # (n_T, n_S, 3)
        "loss_cu_dc_kW": np.squeeze(raw["loss_cu_dc_kW"]), # (n_T, n_S, 3)
        "loss_cu_ac_kW": np.squeeze(raw["loss_cu_ac_kW"]), # (n_T, n_S, 3)
        "loss_fe_kW":    np.squeeze(raw["loss_fe_kW"]),    # (n_T, n_S, 3)
    }
    # 속도를 ×10³ RPM 단위로 변환 (레이블 전용)
    d["speed_k"] = d["speed_rpm"] / 1000.0
    # 0 RPM 점 마스킹 (contourf 경계 처리)
    d["speed_k"][d["speed_rpm"] < 1.0] = 0.0
    return d


# ────────────────────────────────────────────────────────────────────────────
# Fig 1 — 효율맵 3종 비교
# ────────────────────────────────────────────────────────────────────────────
def plot_eta_comparison(d: dict) -> None:
    print("[Fig 1] 효율맵 3종 비교 …")
    X = d["speed_k"]
    Y = d["torque_nm"]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    fig.suptitle("Efficiency Map Comparison: Ref / HalfSC / SC",
                 fontsize=11, fontweight="bold", y=1.01)

    vmin = np.nanpercentile(d["eta_pct"], 2)
    vmax = np.nanpercentile(d["eta_pct"], 99)

    for col, (ax, label) in enumerate(zip(axes, MODEL_LABELS)):
        eta = d["eta_pct"][:, :, col]

        levels_f = np.linspace(vmin, vmax, 40)
        cf = ax.contourf(X, Y, eta, levels=levels_f,
                         cmap=CMAP_ETA, vmin=vmin, vmax=vmax)

        iso_vals = [v for v in [85, 88, 90, 92, 93, 94, 95, 96, 97, 98]
                    if vmin < v < vmax]
        if iso_vals:
            cs = ax.contour(X, Y, eta, levels=iso_vals,
                            colors="white", linewidths=0.5, alpha=0.8)
            ax.clabel(cs, fmt="%d%%", fontsize=7, inline=True, inline_spacing=2)

        _mark_max_eta(ax, X, Y, eta)
        ax.legend(loc="upper right", fontsize=7,
                  framealpha=0.7, handlelength=0.8)

        ax.set_title(label, fontweight="bold")
        _apply_xy_labels(ax, ylabel=(col == 0))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))

        _add_colorbar(fig, ax, cf, r"$\eta$ [%]")

    fig.tight_layout()
    _save(fig, "eta_comparison")
    plt.close(fig)


# ────────────────────────────────────────────────────────────────────────────
# Fig 2 — β_opt 맵 3종 비교
# ────────────────────────────────────────────────────────────────────────────
def plot_beta_comparison(d: dict) -> None:
    print("[Fig 2] β_opt 맵 3종 비교 …")
    X = d["speed_k"]
    Y = d["torque_nm"]
    beta = d["beta_deg"]

    vmin = np.nanpercentile(beta, 1)
    vmax = np.nanpercentile(beta, 99)
    levels_f = np.linspace(vmin, vmax, 40)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    fig.suptitle(r"Optimal Current Phase Angle $\beta_{\rm opt}$ [deg]: Ref / HalfSC / SC",
                 fontsize=11, fontweight="bold", y=1.01)

    for col, (ax, label) in enumerate(zip(axes, MODEL_LABELS)):
        cf = ax.contourf(X, Y, beta[:, :, col],
                         levels=levels_f, cmap=CMAP_BETA,
                         vmin=vmin, vmax=vmax)
        # 등고선 (10° 간격)
        iso_vals = np.arange(
            np.ceil(vmin / 10) * 10,
            np.floor(vmax / 10) * 10 + 10,
            10.0
        )
        iso_vals = iso_vals[(iso_vals > vmin) & (iso_vals < vmax)]
        if len(iso_vals):
            cs = ax.contour(X, Y, beta[:, :, col],
                            levels=iso_vals, colors="white",
                            linewidths=0.5, alpha=0.7)
            ax.clabel(cs, fmt="%d°", fontsize=7, inline=True, inline_spacing=2)

        ax.set_title(label, fontweight="bold")
        _apply_xy_labels(ax, ylabel=(col == 0))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
        _add_colorbar(fig, ax, cf, r"$\beta_{\rm opt}$ [deg]")

    fig.tight_layout()
    _save(fig, "beta_comparison")
    plt.close(fig)


# ────────────────────────────────────────────────────────────────────────────
# Fig 3 — 손실 분해 맵  (3 모델 × 3 손실 종류 = 3×3)
# ────────────────────────────────────────────────────────────────────────────
def plot_loss_decomposition(d: dict) -> None:
    print("[Fig 3] 손실 분해 맵 (3×3) …")
    X = d["speed_k"]
    Y = d["torque_nm"]

    loss_arrays = [d[k] for k in LOSS_KEYS]   # each: (n_T, n_S, 3)

    # 손실 종류별 공통 범위 결정
    ranges = []
    for arr in loss_arrays:
        vmin = 0.0
        vmax = float(np.nanpercentile(arr, 99))
        if vmax <= vmin:
            vmax = vmin + 1.0  # Ensure vmax is strictly greater than vmin
        ranges.append((vmin, vmax))

    fig, axes = plt.subplots(3, 3, figsize=(13, 11), sharey="row")
    fig.suptitle("Loss Decomposition Map: Ref / HalfSC / SC",
                 fontsize=12, fontweight="bold", y=1.005)

    for row, (loss_arr, loss_lbl, loss_title, (vmin, vmax)) in enumerate(
            zip(loss_arrays, LOSS_LABELS, LOSS_TITLES, ranges)):
        levels_f = np.linspace(vmin, vmax, 40)
        for col, (model_lbl) in enumerate(MODEL_LABELS):
            ax = axes[row, col]
            cf = ax.contourf(X, Y, loss_arr[:, :, col],
                             levels=levels_f, cmap=CMAP_LOSS,
                             vmin=vmin, vmax=vmax)
            # 등고선
            n_iso = 5
            iso_vals = np.linspace(vmin + (vmax - vmin) * 0.15,
                                   vmax * 0.85, n_iso)
            if iso_vals.size:
                cs = ax.contour(X, Y, loss_arr[:, :, col],
                                levels=iso_vals, colors="grey",
                                linewidths=0.4, alpha=0.6)
                ax.clabel(cs, fmt="%.1f", fontsize=6,
                          inline=True, inline_spacing=1)

            # 행 제목 (왼쪽 첫 열만)
            if col == 0:
                ax.set_ylabel(f"{loss_title}\nTorque [Nm]", fontsize=8)
            else:
                ax.set_ylabel("")

            # 열 제목 (첫 행만)
            if row == 0:
                ax.set_title(model_lbl, fontweight="bold")

            # x 레이블 (마지막 행만)
            if row == 2:
                ax.set_xlabel("Speed [×10³ RPM]")

            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))

            # 개별 컬러바 (각 열 마지막 열에만)
            if col == 2:
                cb = fig.colorbar(cf, ax=axes[row, :], pad=0.02,
                                  aspect=30, shrink=0.85,
                                  fraction=0.015)
                cb.set_label(loss_lbl, labelpad=4)
                cb.ax.tick_params(labelsize=7)

    fig.tight_layout()
    _save(fig, "loss_decomposition")
    plt.close(fig)


# ────────────────────────────────────────────────────────────────────────────
# Fig 4 — Calibration 효과 Δη = SC − Ref
# ────────────────────────────────────────────────────────────────────────────
def plot_delta_eta(d: dict) -> None:
    print("[Fig 4] Calibration 효과 Δη = SC - Ref ...")
    X = d["speed_k"]
    Y = d["torque_nm"]

    eta_ref = d["eta_pct"][:, :, 0]   # Ref
    eta_sc  = d["eta_pct"][:, :, 2]   # SC
    delta   = eta_sc - eta_ref         # Δη [%]

    abs_max = np.nanpercentile(np.abs(delta), 99)
    abs_max = max(abs_max, 0.1)        # 최소 0.1% 범위 보장

    norm = TwoSlopeNorm(vmin=-abs_max, vcenter=0.0, vmax=abs_max)
    levels_f = np.linspace(-abs_max, abs_max, 41)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5),
                             gridspec_kw={"width_ratios": [1.6, 1]})
    fig.suptitle(r"Calibration Effect: $\Delta\eta = \eta_{\mathrm{SC}} - \eta_{\mathrm{Ref}}$ [%]",
                 fontsize=11, fontweight="bold")

    # ── 왼쪽: 차이 컬러맵 ──────────────────────────────────────────────────
    ax = axes[0]
    cf = ax.contourf(X, Y, delta, levels=levels_f,
                     cmap=CMAP_DELTA, norm=norm)
    # 0% 선 강조
    ax.contour(X, Y, delta, levels=[0.0],
               colors="black", linewidths=1.0, linestyles="--")
    # ±0.5%, ±1%, ±2% 등고선
    iso_vals_pos = [v for v in [0.5, 1.0, 2.0, 3.0] if v < abs_max]
    iso_vals_neg = [-v for v in iso_vals_pos]
    if iso_vals_pos:
        cs_p = ax.contour(X, Y, delta, levels=iso_vals_pos,
                          colors="firebrick", linewidths=0.6, alpha=0.8)
        ax.clabel(cs_p, fmt="%+.1f%%", fontsize=7, inline=True)
    if iso_vals_neg:
        cs_n = ax.contour(X, Y, delta, levels=iso_vals_neg,
                          colors="steelblue", linewidths=0.6, alpha=0.8)
        ax.clabel(cs_n, fmt="%+.1f%%", fontsize=7, inline=True)

    cb = fig.colorbar(cf, ax=ax, pad=0.03, aspect=20, shrink=0.9)
    cb.set_label(r"$\Delta\eta$ [%]", labelpad=4)
    cb.ax.tick_params(labelsize=7)

    _apply_xy_labels(ax)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
    ax.set_title("Spatial Distribution of Δη", fontsize=10)

    # ── 오른쪽: 속도별 평균 Δη 프로파일 ────────────────────────────────────
    ax2 = axes[1]
    # 토크 > 0 영역만 평균
    t_mask = Y > 10.0
    mean_by_speed = np.nanmean(delta[t_mask, :], axis=0)
    std_by_speed  = np.nanstd(delta[t_mask, :],  axis=0)

    ax2.fill_between(X, mean_by_speed - std_by_speed,
                      mean_by_speed + std_by_speed,
                      alpha=0.25, color="steelblue", label="±1σ")
    ax2.plot(X, mean_by_speed, color="steelblue",
             linewidth=1.5, marker="o", markersize=4, label="Mean Δη")
    ax2.axhline(0.0, color="k", linewidth=0.8, linestyle="--")

    ax2.set_xlabel("Speed [×10³ RPM]")
    ax2.set_ylabel(r"$\Delta\eta$ [%]")
    ax2.set_title("Speed-Averaged Δη\n(Torque > 10 Nm)", fontsize=10)
    ax2.legend(fontsize=8)
    ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%+.2f"))

    # 전체 평균 표기
    global_mean = float(np.nanmean(delta[t_mask, :]))
    ax2.text(0.97, 0.05,
             f"Global mean: {global_mean:+.3f}%",
             ha="right", va="bottom",
             transform=ax2.transAxes,
             fontsize=8, color="steelblue",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor="steelblue", alpha=0.8))

    fig.tight_layout()
    _save(fig, "delta_eta")
    plt.close(fig)


# ────────────────────────────────────────────────────────────────────────────
# 메인
# ────────────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("효율맵 그래프 생성")
    print(f"  입력: {INPUT_PATH}")
    print(f"  출력: {FIGURE_DIR}/")
    print("=" * 60)

    d = load_data(INPUT_PATH)
    print(f"  데이터 로드 완료: eta_pct {d['eta_pct'].shape}, "
          f"speed {d['speed_rpm'].shape}, torque {d['torque_nm'].shape}\n")

    plot_eta_comparison(d)
    plot_beta_comparison(d)
    plot_loss_decomposition(d)
    plot_delta_eta(d)

    print("\n" + "=" * 60)
    print("DONE - 4개 PNG 저장 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
