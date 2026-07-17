import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from typing import List, Dict, Tuple, Optional
from .AcLossDataset import AcLossDataset
from .RbfModel3D import RbfModel3D
from .SeparableRbfModel import SeparableRbfModel

class AcLossPlotter:
    @staticmethod
    def configure_matplotlib_backend(plot_backend: str = 'auto'):
        """Detects environment and sets up interactive backend for VS Code/Jupyter."""
        try:
            import IPython
            shell = IPython.get_ipython()
            if shell is not None:
                has_vscode_env = any(k.startswith('VSCODE_') for k in os.environ.keys())
                has_vscode_modules = any('vscode' in m.lower() for m in sys.modules.keys())
                
                selected_backend = plot_backend
                if selected_backend == 'auto':
                    if has_vscode_env and has_vscode_modules:
                        selected_backend = 'widget'
                    else:
                        selected_backend = 'inline'
                
                print("--- Matplotlib Backend Config ---")
                print(f"  [Selection] '{plot_backend}' -> '{selected_backend}'")
                
                if selected_backend == 'widget':
                    shell.run_line_magic('matplotlib', 'widget')
                elif selected_backend == 'notebook':
                    shell.run_line_magic('matplotlib', 'notebook')
                else:
                    shell.run_line_magic('matplotlib', 'inline')
        except Exception as e:
            print(f"Failed to set matplotlib backend: {e}")

    @staticmethod
    def plot_interactive_comparison(
        records: List[Dict],
        model_scale: str
    ):
        """Generates the interactive 3D plot comparing Hybrid vs FullFEA AC loss map (Cell 7)."""
        hybrid_data = [p for p in records if p["proximity_model"] == 1]
        ts_data = [p for p in records if p["proximity_model"] == 3]
        
        if len(hybrid_data) == 0 or len(ts_data) == 0:
            print("Error: Need both Hybrid and FullFEA data for comparison.")
            return

        def process_pts(pts, is_hybrid):
            speeds = np.array([p["speed"] for p in pts])
            currents = np.array([p["current"] for p in pts])
            phases = np.array([p["phase"] for p in pts])
            
            amplitude = currents * np.sqrt(2)
            phase_rad = (phases + 90.0) * np.pi / 180.0
            id_vals = amplitude * np.cos(phase_rad)
            iq_vals = amplitude * np.sin(phase_rad)
            
            if is_hybrid:
                losses = np.array([p["hybrid_total_kW"] for p in pts])
            else:
                losses = np.array([p["ts_ac_active_only_kW"] for p in pts])
                
            return speeds, id_vals, iq_vals, losses, pts

        speeds_h, id_h, iq_h, losses_h, raw_h = process_pts(hybrid_data, is_hybrid=True)
        speeds_f, id_f, iq_f, losses_f, raw_f = process_pts(ts_data, is_hybrid=False)
        
        currents_h = np.array([p["current"] for p in raw_h])
        phases_h = np.array([p["phase"] for p in raw_h])
        currents_f = np.array([p["current"] for p in raw_f])
        phases_f = np.array([p['phase'] for p in raw_f])
        
        unique_speeds = sorted(list(set(speeds_h)))
        speed_colors = {2000: 'cyan', 4000: 'limegreen', 8000: 'orange', 16000: 'tomato'}
        default_colors = ['cyan', 'limegreen', 'orange', 'tomato']
        
        fig = plt.figure(figsize=(18, 5.5))
        fig.suptitle(f"AC Loss Comparison Map ({model_scale}): Hybrid vs FullFEA", fontsize=13, fontweight='bold')
        
        ax_left = fig.add_subplot(131, projection='3d')
        ax_left.set_title("Hybrid (ProximityLossModel = 1)", fontsize=11, fontweight='bold')
        ax_mid = fig.add_subplot(132, projection='3d')
        ax_mid.set_title("FullFEA (ProximityLossModel = 3)", fontsize=11, fontweight='bold')
        
        legend_patches_h = []
        legend_patches_f = []
        
        for i, spd in enumerate(unique_speeds):
            color = speed_colors.get(spd, default_colors[i % len(default_colors)])
            idx_h = (speeds_h == spd)
            if np.any(idx_h) and np.sum(idx_h) >= 3:
                ax_left.plot_trisurf(id_h[idx_h], iq_h[idx_h], losses_h[idx_h], color=color, edgecolor='none', alpha=0.35)
                legend_patches_h.append(mpatches.Patch(color=color, alpha=0.35, label=f"{spd} RPM"))
            idx_f = (speeds_f == spd)
            if np.any(idx_f) and np.sum(idx_f) >= 3:
                ax_mid.plot_trisurf(id_f[idx_f], iq_f[idx_f], losses_f[idx_f], color=color, edgecolor='none', alpha=0.35)
                legend_patches_f.append(mpatches.Patch(color=color, alpha=0.35, label=f"{spd} RPM"))
                
        sc_h = ax_left.scatter(id_h, iq_h, losses_h, c='grey', s=25, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
        sc_f = ax_mid.scatter(id_f, iq_f, losses_f, c='grey', s=25, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
        scatters = [sc_h, sc_f]
        
        for ax, lp in [(ax_left, legend_patches_h), (ax_mid, legend_patches_f)]:
            ax.set_xlabel("I_d [A]", fontsize=8, labelpad=7)
            ax.set_ylabel("I_q [A]", fontsize=8, labelpad=7)
            ax.set_zlabel("AC Loss [kW]", fontsize=8, labelpad=7)
            ax.legend(handles=lp, fontsize=8, loc="upper right")
            
        ax_right = fig.add_subplot(133)
        ax_right.text(0.5, 0.5, "3D 플롯에서 임의의 점을 클릭한 후\nSpacebar를 누르면 속도별 비교 곡선이 출력됩니다.", 
                     ha="center", va="center", fontsize=10, color="gray")
        ax_right.set_xlabel("Speed [RPM]", fontsize=9)
        ax_right.set_ylabel("AC Loss [kW]", fontsize=9)
        ax_right.grid(True, linestyle="--", alpha=0.5)
        
        selected_pt = {"current": None, "phase": None, "id": None, "iq": None}
        highlights_h = []
        highlights_f = []
        
        annotation_h = ax_left.text2D(0.02, 0.95, "", transform=ax_left.transAxes, 
                                      bbox=dict(boxstyle="round", fc="w", alpha=0.8), fontsize=8)
        annotation_f = ax_mid.text2D(0.02, 0.95, "", transform=ax_mid.transAxes, 
                                     bbox=dict(boxstyle="round", fc="w", alpha=0.8), fontsize=8)
        annotation_h.set_visible(False)
        annotation_f.set_visible(False)
        
        def on_pick(event):
            if event.artist not in scatters:
                return
            idx = event.ind[0]
            if event.artist == sc_h:
                curr, ph = raw_h[idx]["current"], raw_h[idx]["phase"]
            else:
                curr, ph = raw_f[idx]["current"], raw_f[idx]["phase"]
            selected_pt["current"] = curr
            selected_pt["phase"] = ph
            amp = curr * np.sqrt(2)
            phase_rad = (ph + 90.0) * np.pi / 180.0
            selected_pt["id"] = amp * np.cos(phase_rad)
            selected_pt["iq"] = amp * np.sin(phase_rad)
            
            for h in highlights_h + highlights_f:
                h.remove()
            highlights_h.clear()
            highlights_f.clear()
            
            same_h_idx = (currents_h == curr) & (phases_h == ph)
            hh = ax_left.scatter(id_h[same_h_idx], iq_h[same_h_idx], losses_h[same_h_idx], 
                                 color='red', s=70, edgecolors='black', linewidths=1.8, zorder=10)
            highlights_h.append(hh)
            
            same_f_idx = (currents_f == curr) & (phases_f == ph)
            hf = ax_mid.scatter(id_f[same_f_idx], iq_f[same_f_idx], losses_f[same_f_idx], 
                                color='red', s=70, edgecolors='black', linewidths=1.8, zorder=10)
            highlights_f.append(hf)
            
            msg = (f"Selected: I_rms={curr:.1f}A, Phase={ph:.1f}°\n"
                   f"Id={selected_pt['id']:.1f}A, Iq={selected_pt['iq']:.1f}A\n→ Press 'Space'")
            for annot in [annotation_h, annotation_f]:
                annot.set_text(msg)
                annot.set_visible(True)
            fig.canvas.draw_idle()
            
        def on_key(event):
            if event.key != ' ' or selected_pt["current"] is None:
                return
            ax_right.clear()
            curr, ph = selected_pt["current"], selected_pt["phase"]
            curve_speeds, curve_losses_h, curve_losses_f = [], [], []
            for spd in unique_speeds:
                match_h = [p for p in raw_h if p["speed"] == spd and np.isclose(p["current"], curr) and np.isclose(p["phase"], ph)]
                match_f = [p for p in raw_f if p["speed"] == spd and np.isclose(p["current"], curr) and np.isclose(p["phase"], ph)]
                if match_h and match_f:
                    curve_speeds.append(spd)
                    curve_losses_h.append(match_h[0]["hybrid_total_kW"])
                    curve_losses_f.append(match_f[0]["ts_ac_active_only_kW"])
            ax_right.plot(curve_speeds, curve_losses_h, marker='o', linestyle='-', color='dodgerblue', linewidth=2, label="Hybrid AC Total")
            ax_right.plot(curve_speeds, curve_losses_f, marker='*', linestyle='--', color='crimson', linewidth=2, label="FullFEA AC Active Only")
            for xs, yh, yf in zip(curve_speeds, curve_losses_h, curve_losses_f):
                ax_right.annotate(f"{yh:.2f}", xy=(xs, yh), xytext=(4, 4), textcoords="offset points", fontsize=8, color="dodgerblue")
                ax_right.annotate(f"{yf:.2f}", xy=(xs, yf), xytext=(4, -12), textcoords="offset points", fontsize=8, color="crimson")
            ax_right.set_title(f"AC Loss vs Speed\n(I_rms={curr:.1f}A, Phase={ph:.1f}°)", fontsize=11, fontweight='bold')
            ax_right.set_xlabel("Speed [RPM]", fontsize=9)
            ax_right.set_ylabel("AC Loss [kW]", fontsize=9)
            ax_right.grid(True, linestyle="--", alpha=0.5)
            ax_right.legend(fontsize=9, loc="upper left")
            fig.canvas.draw_idle()
            
        fig.canvas.mpl_connect('pick_event', on_pick)
        fig.canvas.mpl_connect('key_press_event', on_key)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_af_vs_speed_curves(
        dataset: AcLossDataset,
        coeffs_A: np.ndarray,
        max_curr: float,
        out_path: str
    ):
        """Plots AF vs Speed Curves and saves to map_exports/AF_vs_speed_curves.png (Cell 14)."""
        unique_currents_s = sorted(set(round(p.current_rms, 0) for p in dataset.points))
        unique_phases_s   = sorted(set(round(p.phase_deg, 0) for p in dataset.points))
        unique_speeds_s   = sorted(set(p.speed_rpm for p in dataset.points))
        
        n_curr_s  = len(unique_currents_s)
        colors_s  = [plt.cm.plasma(i / max(1, n_curr_s - 1)) for i in range(n_curr_s)]
        lstyles_s = ['-', '--', '-.', ':', (0, (3, 1, 1, 1)), (0, (5, 5))]
        
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.set_title("Adjustment Factor  AF = FullFEA_AC / Hybrid_AC  vs Speed (운전점별)",
                     fontsize=12, fontweight='bold')
        
        for ki, curr in enumerate(unique_currents_s):
            for li, ph in enumerate(unique_phases_s):
                pts = sorted(
                    [p for p in dataset.points
                     if np.isclose(p.current_rms, curr, atol=0.6)
                     and np.isclose(p.phase_deg,  ph,   atol=0.6)],
                    key=lambda x: x.speed_rpm
                )
                if len(pts) < 2:
                    continue
                spds = [p.speed_rpm for p in pts]
                afs  = [p.AF for p in pts]
                ax.plot(spds, afs,
                        marker='o', markersize=5,
                        linestyle=lstyles_s[li % len(lstyles_s)],
                        color=colors_s[ki], linewidth=1.5,
                        label=f"I={curr:.0f} A, φ={ph:.0f}°")
        
        spd_fit = np.linspace(min(unique_speeds_s) * 0.9, max(unique_speeds_s) * 1.05, 300)
        af_fit_A = np.polyval(coeffs_A, spd_fit / 1000.0)
        a2, a1, a0 = coeffs_A
        eq_str = f"y = {a2:.4f}·x² {a1:+.4f}·x {a0:+.4f}  (x: kRPM)"
        ax.plot(spd_fit, af_fit_A, 'k--', linewidth=2.5,
                label=f"Poly-A fit (I_max={max_curr:.0f} A)")
        ax.text(0.97, 0.97, eq_str, transform=ax.transAxes, fontsize=9,
                va='top', ha='right', bbox=dict(boxstyle='round', fc='white', alpha=0.85))
        
        ax.axhline(y=1.0, color='green', linestyle=':', linewidth=1.5, alpha=0.7, label="AF = 1")
        ax.set_xlabel("Speed [RPM]", fontsize=11)
        ax.set_ylabel("Adjustment factor [-]", fontsize=11)
        ax.legend(fontsize=7.5, loc='upper right', ncol=2, framealpha=0.9)
        ax.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.show()
        print(f"저장: {out_path}")

    @staticmethod
    def plot_af_map_visualization(
        dataset: AcLossDataset,
        model_sep: SeparableRbfModel,
        out_path: str
    ):
        """Plots AF map visualization on id-iq plane per speed (Cell 16)."""
        unique_speeds_v = sorted(set(p.speed_rpm for p in dataset.points))
        n_spd_v = len(unique_speeds_v)
        
        fig, axes = plt.subplots(1, n_spd_v, figsize=(5.2 * n_spd_v, 4.8))
        if n_spd_v == 1:
            axes = [axes]
        fig.suptitle("Adjustment Factor  AF = FullFEA_AC / Hybrid_AC  (id-iq 평면)",
                     fontsize=13, fontweight='bold')
                     
        vmin_af = max(0.5, dataset.af_arr.min() - 0.1)
        vmax_af = dataset.af_arr.max() + 0.1
        
        for ax, spd in zip(axes, unique_speeds_v):
            pts = [p for p in dataset.points if p.speed_rpm == spd]
            id_v = np.array([p.id_A for p in pts])
            iq_v = np.array([p.iq_A for p in pts])
            af_v = np.array([p.AF for p in pts])
            
            sc = ax.scatter(id_v, iq_v, c=af_v, cmap='plasma', s=90,
                            edgecolors='k', linewidths=0.6,
                            vmin=vmin_af, vmax=vmax_af, zorder=3)
            for x, y, a in zip(id_v, iq_v, af_v):
                ax.annotate(f"{a:.2f}", (x, y), textcoords="offset points",
                            xytext=(5, 4), fontsize=7.5, color='black')
                            
            pad = 80
            id_g = np.linspace(id_v.min() - pad, id_v.max() + pad, 50)
            iq_g = np.linspace(max(0.0, iq_v.min() - pad), iq_v.max() + pad, 50)
            ID, IQ = np.meshgrid(id_g, iq_g)
            
            # evaluate RBF using peak dq formulas
            irms_g = np.sqrt(ID**2 + IQ**2) / np.sqrt(2)
            phase_g = np.degrees(np.arctan2(IQ, ID)) - 90.0
            AF_fit = model_sep.predict(spd, irms_g.ravel(), phase_g.ravel()).reshape(ID.shape)
            
            ct = ax.contour(ID, IQ, AF_fit, levels=8, cmap='coolwarm', alpha=0.65, linewidths=0.9)
            ax.clabel(ct, fmt="%.2f", fontsize=7.5)
            
            plt.colorbar(sc, ax=ax, label="AF [-]", shrink=0.85)
            ax.set_xlabel("$I_d$ [A, peak]", fontsize=9)
            ax.set_ylabel("$I_q$ [A, peak]", fontsize=9)
            ax.set_title(f"{spd/1000:.0f} kRPM", fontsize=11, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.4)
            
        plt.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.show()
        print(f"저장 완료: {out_path}")

    @staticmethod
    def plot_ablation_study(
        dataset: AcLossDataset,
        n_center_list: List[int],
        res_3d_tr_m: np.ndarray,
        res_3d_tr_s: np.ndarray,
        res_3d_te_m: np.ndarray,
        res_3d_te_s: np.ndarray,
        res_sep: np.ndarray,
        n_base_list: List[int],
        n_speed_list: List[int],
        n_base_len: int,
        n_spd_len: int,
        out_path: str,
        base_speed: float = 2.0
    ):
        """Plots ablation study results (Cell 17)."""
        hybrid_baseline = float(np.abs((dataset.h_ac_arr - dataset.f_ac_arr) / (dataset.f_ac_arr + 1e-12) * 100.0).mean())
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
        fig.suptitle("Ablation Study: RBF Model Performance vs. Number of Training Points",
                     fontsize=13, fontweight='bold')
                     
        # (1) 3D TPS RBF: MAE vs n_centers
        ax1 = axes[0]
        ax1.plot(n_center_list, res_3d_tr_m, 'o-', color='steelblue', lw=2, ms=5, label='Train MAE')
        ax1.fill_between(n_center_list, res_3d_tr_m - res_3d_tr_s, res_3d_tr_m + res_3d_tr_s,
                         color='steelblue', alpha=0.18)
        ax1.plot(n_center_list, res_3d_te_m, 's--', color='tomato', lw=2, ms=5, label='Held-out MAE')
        ax1.fill_between(n_center_list, res_3d_te_m - res_3d_te_s, res_3d_te_m + res_3d_te_s,
                         color='tomato', alpha=0.18)
        ax1.axhline(hybrid_baseline, color='grey', ls=':', lw=1.5,
                    label=f'Hybrid uncorrected ({hybrid_baseline:.1f}%)')
        ax1.axvline(len(dataset), color='black', ls=':', lw=1.5, label=f'Full dataset ({len(dataset)} pts)')
        ax1.set_xlabel("n_centers (# FullFEA training points)", fontsize=10)
        ax1.set_ylabel("MAE [%]", fontsize=10)
        ax1.set_title("3D TPS RBF: MAE vs n_centers", fontsize=11, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, ls='--', alpha=0.4)
        ax1.set_xlim([0, len(dataset) + 5])
        
        # (2) Separable RBF Heatmap
        # Degenerate low-count fits (esp. exponent regression on ill-
        # conditioned kernels) explode; cap the display at 10^3 so the
        # usable region stays readable.
        CAP = 1e3
        res_disp = np.where(np.isfinite(res_sep),
                            np.minimum(res_sep, CAP), np.nan)
        ax2 = axes[1]
        vlo = np.nanpercentile(res_disp, 5)
        vhi = np.nanpercentile(res_disp, 95)
        im = ax2.imshow(res_disp, aspect='auto', cmap='RdYlGn_r', origin='lower', vmin=vlo, vmax=vhi)
        ax2.set_xticks(range(len(n_speed_list)))
        ax2.set_xticklabels(n_speed_list)
        ax2.set_yticks(range(len(n_base_list)))
        ax2.set_yticklabels(n_base_list)
        ax2.set_xlabel("n_speed/spd (cal. pts per speed)", fontsize=10)
        ax2.set_ylabel(f"n_base (# {base_speed:g}kRPM base pts)", fontsize=10)
        ax2.set_title("Separable RBF: Full MAE [%] Heatmap", fontsize=11, fontweight='bold')

        for bi2 in range(len(n_base_list)):
            for si2 in range(len(n_speed_list)):
                v = res_sep[bi2, si2]
                if not np.isnan(v):
                    txt = r"$>\!10^3$" if v >= CAP else f"{v:.1f}"
                    ax2.text(si2, bi2, txt, ha='center', va='center', fontsize=7.5,
                             color='white' if min(v, CAP) > (vlo + vhi) / 2 else 'black')

        plt.colorbar(im, ax=ax2, label="MAE [%]", shrink=0.85)
        
        cur_nb_idx = min(range(len(n_base_list)), key=lambda i: abs(n_base_list[i] - n_base_len))
        cur_ns_idx = min(range(len(n_speed_list)), key=lambda i: abs(n_speed_list[i] - n_spd_len))
        ax2.add_patch(plt.Rectangle((cur_ns_idx - 0.5, cur_nb_idx - 0.5), 1, 1,
                      fill=False, edgecolor='dodgerblue', linewidth=2.5, label='Current setting'))
        ax2.legend(fontsize=9, loc='upper right')
        
        # (3) Separable RBF: MAE vs n_base (display capped at 10^3,
        # log scale so the convergence knee stays visible)
        ax3 = axes[2]
        pal = plt.cm.plasma(np.linspace(0.1, 0.9, len(n_speed_list)))
        for si, ns in enumerate(n_speed_list):
            ax3.plot(n_base_list, res_disp[:, si], 'o-', color=pal[si], lw=1.8, ms=5,
                     label=f"n_spd/spd={ns}")
        ax3.axhline(hybrid_baseline, color='grey', ls=':', lw=1.5,
                    label=f'Hybrid baseline ({hybrid_baseline:.1f}%)')
        ax3.axvline(n_base_len, color='dodgerblue', ls=':', lw=1.5,
                    label=f'Current n_base={n_base_len}')
        ax3.set_yscale('log')
        ax3.set_xlabel(f"n_base (# {base_speed:g}kRPM base pts)", fontsize=10)
        ax3.set_ylabel("Full MAE [%] (log, capped at $10^3$)", fontsize=10)
        ax3.set_title("Separable RBF: MAE vs n_base\n(line color = n_speed/spd)", fontsize=11, fontweight='bold')
        ax3.legend(fontsize=8, ncol=2)
        ax3.grid(True, ls='--', alpha=0.4, which='both')
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.show()
        print(f"Saved: {out_path}")

    @staticmethod
    def plot_exhaustive_search(
        dataset: AcLossDataset,
        mae_grid: np.ndarray,
        other_speeds: List[float],
        out_path: str
    ):
        """Plots exhaustive search results (Cell 19)."""
        fig, axes = plt.subplots(2, 2, figsize=(13, 10))
        fig.suptitle("Exhaustive Search: Calibration-Point Effect (n_spd/spd=1, n_base=all)",
                     fontsize=13, fontweight="bold")
                     
        # (a) MAE histogram
        ax = axes[0, 0]
        ax.hist(mae_grid.ravel(), bins=60, color="steelblue", edgecolor="white", linewidth=0.3)
        ax.axvline(np.nanmin(mae_grid),  color="green",  ls="--", lw=1.8, label=f"Best  {np.nanmin(mae_grid):.2f}%")
        ax.axvline(np.nanmean(mae_grid), color="orange", ls="--", lw=1.8, label=f"Mean  {np.nanmean(mae_grid):.2f}%")
        ax.axvline(np.nanmax(mae_grid),  color="red",    ls="--", lw=1.8, label=f"Worst {np.nanmax(mae_grid):.2f}%")
        ax.set_xlabel("Full MAE [%]")
        ax.set_ylabel("count")
        ax.set_title("MAE Distribution (27,000 combos)")
        ax.legend(fontsize=9)
        ax.grid(True, ls="--", alpha=0.4)
        
        # (b)(c)(d) Speed marginal heatmaps
        spd_labels = [f"{int(s*1000)} RPM" for s in other_speeds]
        marginal_axes = [axes[0, 1], axes[1, 0], axes[1, 1]]
        
        # Identify non-base indices grouped by speed
        spd_groups = {s: np.where(np.abs(dataset.speeds_k - s) < 0.01)[0] for s in other_speeds}
        
        for ax_idx, (s_target, ax_p) in enumerate(zip(other_speeds, marginal_axes)):
            if ax_idx == 0:
                mae_marg = mae_grid.mean(axis=(1, 2))
            elif ax_idx == 1:
                mae_marg = mae_grid.mean(axis=(0, 2))
            else:
                mae_marg = mae_grid.mean(axis=(0, 1))
                
            grp = spd_groups[s_target]
            irms_v = dataset.irms_arr[grp]
            phase_v = dataset.phase_arr[grp]
            
            sc_plot = ax_p.scatter(irms_v, phase_v, c=mae_marg, cmap="RdYlGn_r",
                                   s=110, edgecolors="k", linewidths=0.5,
                                   vmin=np.nanpercentile(mae_marg, 5),
                                   vmax=np.nanpercentile(mae_marg, 95))
                                   
            best_i = int(np.nanargmin(mae_marg))
            worst_i = int(np.nanargmax(mae_marg))
            
            ax_p.scatter(irms_v[best_i], phase_v[best_i], s=200, c="lime", edgecolors="k",
                         lw=1.5, marker="*", zorder=5, label=f"Best  {mae_marg[best_i]:.2f}%")
            ax_p.scatter(irms_v[worst_i], phase_v[worst_i], s=200, c="red", edgecolors="k",
                         lw=1.5, marker="X", zorder=5, label=f"Worst {mae_marg[worst_i]:.2f}%")
                         
            plt.colorbar(sc_plot, ax=ax_p, label="Marginal MAE [%]", shrink=0.85)
            ax_p.set_xlabel("Irms [A]")
            ax_p.set_ylabel("Phase advance [deg]")
            ax_p.set_title(f"{spd_labels[ax_idx]}  —  marginal MAE(other speeds averaged)")
            ax_p.legend(fontsize=8, loc="upper right")
            ax_p.grid(True, ls="--", alpha=0.3)
            
        plt.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.show()
        print(f"저장: {out_path}")

    @staticmethod
    def plot_coordinate_comparison(
        dataset: AcLossDataset,
        mae_sep_ip: float, mae_sep_dq: float,
        mae_3d_ip: float, mae_3d_dq: float,
        cv_sep_ip: float, cv_sep_dq: float,
        af_sep_ip: np.ndarray, af_sep_dq: np.ndarray,
        af_3d_ip: np.ndarray, af_3d_dq: np.ndarray,
        n_base: int, n_spd: int,
        out_path: str
    ):
        """Plots coordinate system comparison results (Cell 21)."""
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        fig.suptitle(
            f'Coordinate Comparison: (Irms, phase) vs (Id, Iq)  |  '
            f'Separable n_base={n_base}, n_spd/spd={n_spd}  |  3D RBF: {len(dataset)} centers',
            fontsize=13, fontweight='bold'
        )
        
        # (a) MAE bars
        ax = axes[0]
        labels = ['Sep\n(Irms,ph)', 'Sep\n(Id,Iq)', '3D RBF\n(Irms,ph)', '3D RBF\n(Id,Iq)']
        train = [mae_sep_ip, mae_sep_dq, mae_3d_ip, mae_3d_dq]
        colors = ['steelblue', 'tomato', 'steelblue', 'tomato']
        bars = ax.bar(labels, train, color=colors, edgecolor='k', linewidth=0.6, alpha=0.85)
        ax.scatter([0, 1], [cv_sep_ip, cv_sep_dq], s=80, color='black', zorder=5, marker='D', label='LOOCV MAE')
        for bar, v in zip(bars, train):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.01, f'{v:.2f}%',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.set_ylabel('MAE [%]')
        ax.set_title('Train MAE  (◆ = LOOCV)')
        ax.legend(fontsize=9)
        ax.grid(True, ls='--', alpha=0.4, axis='y')
        ax.set_ylim(0, max(train) * 1.3)
        
        # (b) Separable Parity
        ax = axes[1]
        lim = [dataset.f_ac_arr.min() * 0.92, dataset.f_ac_arr.max() * 1.05]
        ax.scatter(dataset.f_ac_arr, dataset.h_ac_arr * af_sep_ip, s=40, alpha=0.7, marker='o',
                   label=f'(Irms, phase)  {mae_sep_ip:.2f}%')
        ax.scatter(dataset.f_ac_arr, dataset.h_ac_arr * af_sep_dq, s=40, alpha=0.7, marker='^',
                   label=f'(Id, Iq)       {mae_sep_dq:.2f}%')
        ax.plot(lim, lim, 'k--', lw=1.2)
        ax.set_xlabel('FEA AC loss [kW]')
        ax.set_ylabel('Separable RBF corrected [kW]')
        ax.set_title(f'Separable RBF — Parity Plot  [n_base={n_base}, n_spd/spd={n_spd}]')
        ax.legend(fontsize=8)
        ax.grid(True, ls='--', alpha=0.4)
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        
        # (c) 3D RBF Parity
        ax = axes[2]
        ax.scatter(dataset.f_ac_arr, dataset.h_ac_arr * af_3d_ip, s=40, alpha=0.7, marker='o',
                   label=f'(Irms, phase)  {mae_3d_ip:.2f}%')
        ax.scatter(dataset.f_ac_arr, dataset.h_ac_arr * af_3d_dq, s=40, alpha=0.7, marker='^',
                   label=f'(Id, Iq)       {mae_3d_dq:.2f}%')
        ax.plot(lim, lim, 'k--', lw=1.2)
        ax.set_xlabel('FEA AC loss [kW]')
        ax.set_ylabel('3D RBF corrected [kW]')
        ax.set_title('3D TPS RBF — Parity Plot')
        ax.legend(fontsize=8)
        ax.grid(True, ls='--', alpha=0.4)
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.show()
        print(f"저장: {out_path}")

    @staticmethod
    def plot_3d_surface(
        dataset: AcLossDataset,
        model_sep: SeparableRbfModel,
        out_path: str
    ):
        """Plots 3D surfaces of AF(Id, Iq) per speed (Cell 23)."""
        unique_speeds_v = sorted(set(p.speed_rpm for p in dataset.points))
        n_spd_v = len(unique_speeds_v)
        
        fig = plt.figure(figsize=(5.5 * n_spd_v, 5.0))
        fig.suptitle("AF Surface: AF(Id, Iq) 방법 B 3D 곡면 (속도별)", fontsize=13, fontweight="bold")
        
        for k, spd in enumerate(unique_speeds_v):
            ax = fig.add_subplot(1, n_spd_v, k + 1, projection="3d")
            
            pts = [p for p in dataset.points if p.speed_rpm == spd]
            id_v = np.array([p.id_A for p in pts])
            iq_v = np.array([p.iq_A for p in pts])
            af_v = np.array([p.AF for p in pts])
            
            pad = 80
            id_g = np.linspace(id_v.min() - pad, id_v.max() + pad, 50)
            iq_g = np.linspace(max(0.0, iq_v.min() - pad), iq_v.max() + pad, 50)
            ID, IQ = np.meshgrid(id_g, iq_g)
            
            # evaluate RBF using peak dq formulas
            irms_g = np.sqrt(ID**2 + IQ**2) / np.sqrt(2)
            phase_g = np.degrees(np.arctan2(IQ, ID)) - 90.0
            AF_fit = model_sep.predict(spd, irms_g, phase_g)
            
            surf = ax.plot_surface(ID, IQ, AF_fit, cmap="plasma", alpha=0.75,
                                   linewidth=0, antialiased=True)
            ax.scatter(id_v, iq_v, af_v, c="red", s=60,
                       edgecolors="k", linewidths=0.6, zorder=5, label="FEA data")
                       
            fig.colorbar(surf, ax=ax, shrink=0.55, label="AF [-]")
            ax.set_xlabel("Id [A]", fontsize=8)
            ax.set_ylabel("Iq [A]", fontsize=8)
            ax.set_zlabel("AF [-]", fontsize=8)
            ax.set_title(f"{spd/1000:.0f} kRPM", fontsize=11, fontweight="bold")
            ax.view_init(elev=25, azim=-60)
            
        plt.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.show()
        print(f"저장 완료: {out_path}")

    @staticmethod
    def plot_rbf_correction_validation(
        dataset: AcLossDataset,
        ea: np.ndarray, e3: np.ndarray, es: np.ndarray,
        mae_loocv_3d: float, mae_loocv_sep: float,
        n_base: int, n_spd: int,
        model_3d: RbfModel3D,
        model_sep: SeparableRbfModel,
        out_path: str
    ):
        """Plots training error boxplots and parity plots comparing original and corrected losses (Cell 25)."""
        h_ac = dataset.h_ac_arr
        f_ac = dataset.f_ac_arr
        
        af_3d = model_3d.predict(dataset.speeds_k * 1000.0, dataset.irms_arr, dataset.phase_arr)
        af_sep = model_sep.predict(dataset.speeds_k * 1000.0, dataset.irms_arr, dataset.phase_arr)
        
        corr_3d = h_ac * af_3d
        corr_sep = h_ac * af_sep
        
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        fig.suptitle(
            f"RBF Model Comparison  |  Separable: n_base={n_base}, n_spd/spd={n_spd}  |  3D RBF: {len(dataset)} centers",
            fontsize=11, fontweight='bold'
        )
        
        ax = axes[0]
        lim = [min(f_ac.min(), h_ac.min(), corr_3d.min(), corr_sep.min()) * 0.9,
               max(f_ac.max(), h_ac.max(), corr_3d.max(), corr_sep.max()) * 1.05]
        ax.plot(lim, lim, 'k--', linewidth=1.2, label='Perfect fit')
        ax.scatter(f_ac, h_ac, c='grey', s=30, alpha=0.5, label='Hybrid (보정 전)', zorder=2)
        ax.scatter(f_ac, corr_3d, c='steelblue', s=45, alpha=0.7, label=f'3D RBF (LOOCV: {mae_loocv_3d:.2f}%)', zorder=3)
        ax.scatter(f_ac, corr_sep, c='tomato', s=45, alpha=0.8, label=f'Separable [n_base={n_base}, n_spd={n_spd}] (LOOCV: {mae_loocv_sep:.2f}%)', zorder=4)
        ax.set_xlabel("FullFEA AC Loss [kW]", fontsize=10)
        ax.set_ylabel("Predicted AC Loss [kW]", fontsize=10)
        ax.set_title("Parity Plot", fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        
        ax2 = axes[1]
        bp = ax2.boxplot([ea, e3, es], labels=['Hybrid (보정 전)', '3D RBF', 'Separable RBF'], patch_artist=True, widths=0.4)
        bp['boxes'][0].set_facecolor('grey')
        bp['boxes'][0].set_alpha(0.4)
        bp['boxes'][1].set_facecolor('steelblue')
        bp['boxes'][1].set_alpha(0.6)
        bp['boxes'][2].set_facecolor('tomato')
        bp['boxes'][2].set_alpha(0.6)
        ax2.axhline(0, color='k', linestyle='--', linewidth=1)
        ax2.set_ylabel("오차 [%]", fontsize=10)
        ax2.set_title("Error Distribution Comparison", fontsize=11)
        ax2.grid(True, linestyle='--', alpha=0.4)
        
        for i, (arr, x) in enumerate([(ea, 1), (e3, 2), (es, 3)]):
            ax2.text(x, arr.max() + 0.5, f"MAE={np.abs(arr).mean():.1f}%", ha='center', fontsize=8.5, color='black')
            
        plt.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.show()
        print(f"그림 저장 완료: {out_path}")

    @staticmethod
    def plot_interactive_4way_comparison(
        dataset: AcLossDataset,
        model_3d: RbfModel3D,
        model_sep: SeparableRbfModel,
        model_scale: str,
        n_base: int,
        n_spd: int
    ):
        """Generates the interactive 4-way comparison plot (Cell 25)."""
        speeds = dataset.speeds_k * 1000.0
        irms = dataset.irms_arr
        phases = dataset.phase_arr
        id_vals = dataset.id_arr
        iq_vals = dataset.iq_arr
        
        loss_hyb = dataset.h_ac_arr
        loss_fea = dataset.f_ac_arr
        
        af_3d = model_3d.predict(speeds, irms, phases)
        af_sep = model_sep.predict(speeds, irms, phases)
        loss_3d = af_3d * loss_hyb
        loss_sep = af_sep * loss_hyb
        
        fig_int = plt.figure(figsize=(17, 8.5))
        fig_int.suptitle(
            f"AC Loss Comparison ({model_scale})  |  Separable: n_base={n_base}, n_spd/spd={n_spd}  |  3D RBF: {len(dataset)} centers",
            fontsize=12, fontweight='bold'
        )
        
        ax_hyb = fig_int.add_subplot(2, 3, 1, projection='3d')
        ax_3d  = fig_int.add_subplot(2, 3, 2, projection='3d')
        ax_sep = fig_int.add_subplot(2, 3, 4, projection='3d')
        ax_fea = fig_int.add_subplot(2, 3, 5, projection='3d')
        ax_curve = fig_int.add_subplot(2, 3, (3, 6))
        
        ax_hyb.set_title("1) Hybrid (보정 전)", fontsize=11, fontweight='bold')
        ax_3d.set_title("2) 3D TPS RBF (보정 후)", fontsize=11, fontweight='bold')
        ax_sep.set_title("3) Separable RBF (보정 후)", fontsize=11, fontweight='bold')
        ax_fea.set_title("4) FullFEA (참조값)", fontsize=11, fontweight='bold')
        
        unique_speeds = sorted(list(set(speeds)))
        speed_colors = {2000: 'cyan', 4000: 'limegreen', 8000: 'orange', 16000: 'tomato'}
        default_colors = ['cyan', 'limegreen', 'orange', 'tomato']
        axes_3d = [ax_hyb, ax_3d, ax_sep, ax_fea]
        losses_list = [loss_hyb, loss_3d, loss_sep, loss_fea]
        
        legend_patches = []
        for i, spd in enumerate(unique_speeds):
            color = speed_colors.get(spd, default_colors[i % len(default_colors)])
            legend_patches.append(mpatches.Patch(color=color, alpha=0.35, label=f"{spd} RPM"))
            idx_spd = (speeds == spd)
            if np.any(idx_spd) and np.sum(idx_spd) >= 3:
                for ax, loss_val in zip(axes_3d, losses_list):
                    ax.plot_trisurf(id_vals[idx_spd], iq_vals[idx_spd], loss_val[idx_spd], color=color, edgecolor='none', alpha=0.2)
                    
        sc_hyb = ax_hyb.scatter(id_vals, iq_vals, loss_hyb, c='grey', s=20, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
        sc_3d  = ax_3d.scatter(id_vals, iq_vals, loss_3d,   c='grey', s=20, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
        sc_sep = ax_sep.scatter(id_vals, iq_vals, loss_sep, c='grey', s=20, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
        sc_fea = ax_fea.scatter(id_vals, iq_vals, loss_fea, c='grey', s=20, picker=True, pickradius=5, edgecolors='black', alpha=0.6)
        scatters = [sc_hyb, sc_3d, sc_sep, sc_fea]
        
        for ax in axes_3d:
            ax.set_xlabel("I_d [A]", fontsize=8, labelpad=5)
            ax.set_ylabel("I_q [A]", fontsize=8, labelpad=5)
            ax.set_zlabel("AC Loss [kW]", fontsize=8, labelpad=5)
            ax.legend(handles=legend_patches, fontsize=8)
            
        ax_curve.text(0.5, 0.5, "3D 플롯에서 임의의 점을 클릭한 후\nSpacebar를 누르거나 클릭하면 우측에 속도별 비교 곡선이 출력됩니다.", 
                     ha="center", va="center", fontsize=10, color="gray")
        ax_curve.set_xlabel("Speed [RPM]", fontsize=9)
        ax_curve.set_ylabel("AC Loss [kW]", fontsize=9)
        ax_curve.grid(True, linestyle="--", alpha=0.5)
        
        selected_pt = {"current_rms": None, "phase_deg": None, "id_A": None, "iq_A": None}
        highlights = []
        annots = []
        for ax in axes_3d:
            annot = ax.text2D(0.02, 0.95, "", transform=ax.transAxes, bbox=dict(boxstyle="round", fc="w", alpha=0.8), fontsize=8)
            annot.set_visible(False)
            annots.append(annot)
            
        def update_2d_curve(curr, ph):
            ax_curve.clear()
            match_pts = [p for p in dataset.points if np.isclose(p.current_rms, curr) and np.isclose(p.phase_deg, ph)]
            match_pts = sorted(match_pts, key=lambda x: x.speed_rpm)
            
            curve_speeds = [p.speed_rpm for p in match_pts]
            c_loss_hyb = [p.hybrid_ac_kW for p in match_pts]
            c_loss_fea = [p.fea_ac_kW for p in match_pts]
            c_loss_3d  = [float(model_3d.predict(p.speed_rpm, p.current_rms, p.phase_deg)) * p.hybrid_ac_kW for p in match_pts]
            c_loss_sep = [float(model_sep.predict(p.speed_rpm, p.current_rms, p.phase_deg)) * p.hybrid_ac_kW for p in match_pts]
            
            ax_curve.plot(curve_speeds, c_loss_hyb, marker='o', linestyle='-',  color='grey',      linewidth=1.5, label="1) Hybrid (보정 전)")
            ax_curve.plot(curve_speeds, c_loss_3d,  marker='s', linestyle='-',  color='steelblue', linewidth=2,   label="2) 3D RBF (보정 후)")
            ax_curve.plot(curve_speeds, c_loss_sep, marker='^', linestyle='-',  color='tomato',    linewidth=2,   label="3) Separable (보정 후)")
            ax_curve.plot(curve_speeds, c_loss_fea, marker='*', linestyle='--', color='black',     linewidth=2,   label="4) FullFEA Reference")
            
            for xs, yh, y3, ys, yf in zip(curve_speeds, c_loss_hyb, c_loss_3d, c_loss_sep, c_loss_fea):
                ax_curve.annotate(f"{yh:.2f}", xy=(xs, yh), xytext=(4, 8),   textcoords="offset points", fontsize=8, color="grey")
                ax_curve.annotate(f"{y3:.2f}", xy=(xs, y3), xytext=(4, 0),   textcoords="offset points", fontsize=8, color="steelblue")
                ax_curve.annotate(f"{ys:.2f}", xy=(xs, ys), xytext=(4, -8),  textcoords="offset points", fontsize=8, color="tomato")
                ax_curve.annotate(f"{yf:.2f}", xy=(xs, yf), xytext=(4, -16), textcoords="offset points", fontsize=8, color="black")
                
            ax_curve.set_title(f"AC Loss vs Speed Comparison\n(I_rms={curr:.1f}A, Phase={ph:.1f}°)", fontsize=11, fontweight='bold')
            ax_curve.set_xlabel("Speed [RPM]", fontsize=9)
            ax_curve.set_ylabel("AC Loss [kW]", fontsize=9)
            ax_curve.grid(True, linestyle="--", alpha=0.5)
            ax_curve.legend(fontsize=9, loc="upper left")
            
        def on_pick(event):
            if event.artist not in scatters:
                return
            idx = event.ind[0]
            p_sel = dataset.points[idx]
            curr = p_sel.current_rms
            ph = p_sel.phase_deg
            
            selected_pt["current_rms"] = curr
            selected_pt["phase_deg"] = ph
            selected_pt["id_A"] = p_sel.id_A
            selected_pt["iq_A"] = p_sel.iq_A
            
            for h in highlights:
                h.remove()
            highlights.clear()
            
            same_pt_idx = np.where((irms == curr) & (phases == ph))[0]
            for ax_3d_p, loss_val in zip(axes_3d, losses_list):
                h = ax_3d_p.scatter(id_vals[same_pt_idx], iq_vals[same_pt_idx], loss_val[same_pt_idx], color='red', s=60, edgecolors='black', linewidths=1.5, zorder=10)
                highlights.append(h)
                
            msg = f"Selected: I_rms={curr:.1f}A, Phase={ph:.1f}°\nId={selected_pt['id_A']:.1f}A, Iq={selected_pt['iq_A']:.1f}"
            for annot in annots:
                annot.set_text(msg)
                annot.set_visible(True)
                
            update_2d_curve(curr, ph)
            fig_int.canvas.draw_idle()
            
        def on_key(event):
            if event.key != ' ' or selected_pt["current_rms"] is None:
                return
            update_2d_curve(selected_pt["current_rms"], selected_pt["phase_deg"])
            fig_int.canvas.draw_idle()
            
        fig_int.canvas.mpl_connect('pick_event', on_pick)
        fig_int.canvas.mpl_connect('key_press_event', on_key)
        plt.tight_layout()
        plt.show()
