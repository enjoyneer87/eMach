"""Magnetic FEA visualization and interactive plotting.

GIF/SVG export and ipywidgets-based interactive plots for magnetic data.
"""
from __future__ import annotations

import pathlib
import tempfile
from typing import Dict, Sequence

import matplotlib
import matplotlib.pyplot as plt

from ._export import safe_stem as _safe_stem, unique_path as _unique_path
from .magnetic_model import MagneticRegionsTimeSeries


def export_magnetic_timeseries_gif(
    ts,
    gif_path: str | pathlib.Path,
    *,
    quantity: str = "b",
    reg_code: int | None = None,
    s: float = 2,
    cmap: str = "jet",
    mesh: bool = False,
    fps: int = 6,
    max_frames: int | None = None,
) -> pathlib.Path:
    """Export a simple GIF by rendering each time/step frame (non-interactive).

    Requires Pillow (`pip install pillow`).
    """

    from PIL import Image  # type: ignore

    gif_path = pathlib.Path(gif_path)
    gif_path.parent.mkdir(parents=True, exist_ok=True)

    steps = list(getattr(ts, "steps", []))
    if not steps:
        raise ValueError("Empty time series")

    if max_frames is not None:
        steps = steps[: int(max_frames)]

    frames: list[Image.Image] = []
    tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="mcad_gif_"))

    for step in steps:
        fig, ax = plt.subplots(layout="constrained")
        mr = ts.by_step[int(step)]
        mr.plot(reg_code=reg_code, quantity=quantity, cmap=cmap, s=s, ax=ax, show=False, mesh=mesh)
        ax.set_title(f"{str(quantity).upper()} step={step}")
        png_path = tmp_dir / f"frame_{int(step):06d}.png"
        fig.savefig(png_path, dpi=140)
        plt.close(fig)
        frames.append(Image.open(png_path).convert("P"))

    duration_ms = int(1000 / max(1, int(fps)))
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
    )
    return gif_path


def export_magnetic_snapshot_svgs(
    mr,
    *,
    out_dir: str | pathlib.Path,
    stem: str,
    quantities: Sequence[str] = ("b", "a", "j"),
    cmap: str = "jet",
    point_size: float = 2,
    dpi: int = 140,
) -> Dict[str, pathlib.Path]:
    """Export snapshot magnetic fields to separate SVGs for each quantity."""

    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    exported: Dict[str, pathlib.Path] = {}
    for q in tuple(quantities):
        q_s = str(q).lower().strip()
        fig, ax = plt.subplots(layout="constrained")
        mr.plot(quantity=q_s, cmap=cmap, s=float(point_size), ax=ax, show=False)
        ax.set_title(f"Magnetic snapshot {q_s} ({stem})")
        svg_path = _unique_path(out_dir / f"Mag_{q_s}_{_safe_stem(stem)}.svg")
        fig.savefig(svg_path, dpi=int(dpi))
        plt.close(fig)
        exported[q_s] = svg_path

    return exported



try:
    import ipywidgets as widgets
    from IPython.display import display
except Exception:
    widgets = None
    display = None


def _extract_element_timeseries(ts, elem_id, quantity):
    """Extract field value of a specific element (by tri_index) across all steps."""
    import numpy as np

    quantity = str(quantity).lower()
    steps = sorted(ts.by_step.keys())
    values = []
    for step in steps:
        mr = ts.by_step[step]
        found = False
        for region in mr._regions:
            for el in region.elements:
                if getattr(el, "tri_index", -1) == elem_id:
                    v = getattr(el, quantity, None)
                    values.append(float(v) if v is not None else 0.0)
                    found = True
                    break
            if found:
                break
        if not found:
            values.append(0.0)
    return np.array(steps, dtype=float), np.array(values, dtype=float)


def _attach_dblclick(fig, ax, hover_data, ts, out_right):
    """Attach double-click handler to show waveform + FFT in out_right widget."""
    import numpy as np

    def _on_dblclick(event):
        if event.inaxes != ax or not event.dblclick:
            return
        mx, my = event.xdata, event.ydata
        if mx is None or my is None:
            return

        tree = hover_data["tree"]
        coords = hover_data["coords"]
        if tree is not None:
            dist, idx = tree.query([mx, my])
        else:
            dists = np.sum((coords - np.array([mx, my])) ** 2, axis=1)
            idx = int(np.argmin(dists))
            dist = float(np.sqrt(dists[idx]))

        x_range = ax.get_xlim()
        threshold = (x_range[1] - x_range[0]) * 0.03
        if dist > threshold:
            return

        elem_id = hover_data["elem_ids"][idx]
        x_pt, y_pt = coords[idx]
        qty = ax._hover_qty if hasattr(ax, "_hover_qty") else "b"

        steps_arr, vals_arr = _extract_element_timeseries(ts, elem_id, qty)

        with out_right:
            out_right.clear_output(wait=True)
            fig_r, (ax_wave, ax_fft) = plt.subplots(2, 1, figsize=(4, 5))

            # Waveform
            ax_wave.plot(steps_arr, vals_arr, "b.-", markersize=3, linewidth=0.8)
            ax_wave.set_xlabel("Step")
            ax_wave.set_ylabel(qty.upper())
            ax_wave.set_title(
                f"elem={elem_id} ({x_pt:.2f},{y_pt:.2f})mm",
                fontsize=8,
            )
            ax_wave.grid(True, alpha=0.3)

            # FFT
            n = len(vals_arr)
            if n > 1:
                fft_vals = np.abs(np.fft.rfft(vals_arr - vals_arr.mean()))
                freqs = np.fft.rfftfreq(n, d=1.0)  # normalized freq (per step)
                ax_fft.stem(
                    freqs[1:], fft_vals[1:],
                    linefmt="r-", markerfmt="ro", basefmt="k-",
                )
                ax_fft.set_xlabel("Freq [1/step]")
                ax_fft.set_ylabel(f"|FFT({qty.upper()})|")
                ax_fft.set_title("FFT (DC removed)", fontsize=8)
                ax_fft.grid(True, alpha=0.3)

            fig_r.tight_layout()
            plt.show()
            plt.close(fig_r)

    fig.canvas.mpl_connect("button_press_event", _on_dblclick)


def _build_hover_data(mr, reg_code, quantity):
    """Collect element positions, field values, and indices for hover lookup."""
    import numpy as np

    quantity = str(quantity).lower()
    if reg_code is None:
        regions = [r for r in mr._regions if r.elements]
    elif isinstance(reg_code, (list, tuple, set)):
        regions = [
            mr._regions[int(rc) - 1]
            for rc in reg_code
            if 0 < int(rc) <= len(mr._regions)
        ]
    else:
        if 0 < int(reg_code) <= len(mr._regions):
            regions = [mr._regions[int(reg_code) - 1]]
        else:
            regions = []

    xs, ys, vals, elem_ids, node_ids_list = [], [], [], [], []
    for region in regions:
        for el in region.elements:
            v = getattr(el, quantity, None)
            if v is None:
                continue
            c_xy = mr._element_centroid_xy(el)
            if c_xy is None:
                continue
            xs.append(c_xy[0])
            ys.append(c_xy[1])
            vals.append(v)
            elem_ids.append(getattr(el, "tri_index", -1))
            node_ids_list.append((el.node_1, el.node_2, el.node_3))

    if not xs:
        return None

    coords = np.column_stack([xs, ys])
    try:
        from scipy.spatial import cKDTree
        tree = cKDTree(coords)
    except ImportError:
        tree = None

    return {
        "coords": coords,
        "vals": np.asarray(vals),
        "elem_ids": elem_ids,
        "node_ids": node_ids_list,
        "tree": tree,
    }


def _attach_hover(fig, ax, hover_data, quantity, state):
    """Attach a motion_notify_event handler that shows hover annotation.
    Updates state['last_idx'] with the nearest element index on hover.
    """
    import numpy as np

    annot = ax.annotate(
        "", xy=(0, 0), xytext=(12, 12),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", alpha=0.9),
        fontsize=7,
        arrowprops=dict(arrowstyle="->", color="gray"),
        annotation_clip=True,
    )
    annot.set_visible(False)

    def _on_move(event):
        if event.inaxes != ax:
            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return

        mx, my = event.xdata, event.ydata
        if mx is None or my is None:
            return

        tree = hover_data["tree"]
        coords = hover_data["coords"]
        if tree is not None:
            dist, idx = tree.query([mx, my])
        else:
            dists = np.sum((coords - np.array([mx, my])) ** 2, axis=1)
            idx = int(np.argmin(dists))
            dist = float(np.sqrt(dists[idx]))

        # Only show if cursor is reasonably close (within 2% of axis range)
        x_range = ax.get_xlim()
        threshold = (x_range[1] - x_range[0]) * 0.02
        if dist > threshold:
            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return

        # Track last hovered element
        state["last_idx"] = int(idx)

        x_pt, y_pt = coords[idx]
        val = hover_data["vals"][idx]
        elem_id = hover_data["elem_ids"][idx]
        n1, n2, n3 = hover_data["node_ids"][idx]

        text = (
            f"x={x_pt:.3f}, y={y_pt:.3f} mm\n"
            f"{quantity}={val:.4g}\n"
            f"elem={elem_id}, nodes=({n1},{n2},{n3})"
        )
        annot.xy = (x_pt, y_pt)
        annot.set_text(text)
        annot.set_visible(True)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", _on_move)


def interactive_magnetic_plot(ts: MagneticRegionsTimeSeries, initial_step=None, quantity="b", reg_code=None, s=2, cmap="jet", n_fund=None):
    """Interactive step toggle plot for MagneticRegionsTimeSeries.

    Parameters
    ----------
    n_fund : int or None
        Steps per fundamental electrical cycle.
        If None (default), auto-detects from total number of steps in the time series.
        Used to convert FFT x-axis to harmonic order.
    """

    # Auto-detect: total steps = one electrical cycle
    if n_fund is None:
        n_fund = len(ts.steps) if len(ts.steps) > 0 else 128

    def _enable_widget_backend():
        try:
            from IPython import get_ipython
        except Exception:
            return False

        ip = get_ipython()
        if ip is None:
            return False

        try:
            ip.run_line_magic("matplotlib", "widget")
            return True
        except Exception:
            return False

    if widgets is None or display is None:
        raise RuntimeError("ipywidgets is required for interactive plotting")
    if len(ts) == 0:
        raise ValueError("Empty time series.")

    _zoom_enabled = _enable_widget_backend()

    steps = ts.steps
    if initial_step is None:
        initial_step = steps[0]

    step_slider = widgets.SelectionSlider(
        options=steps,
        value=initial_step,
        description="step",
        continuous_update=False,
        layout=widgets.Layout(width="650px"),
    )
    qty_dd = widgets.Dropdown(
        options=[("B", "b"), ("Bx", "bx"), ("By", "by"), ("A", "a"), ("J", "j"), ("Je", "je"),
                 ("H", "h"), ("Hx", "hx"), ("Hy", "hy"), ("μr", "mur")],
        value=str(quantity).lower(),
        description="qty",
    )
    mesh_chk = widgets.Checkbox(value=False, description="mesh", indent=False)

    def _region_options_for_step(step):
        mr = ts.by_step[int(step)]
        options = [("all", None)]
        regions = getattr(mr, "_regions", [])
        for idx, region in enumerate(regions):
            if not getattr(region, "elements", None):
                continue
            code = getattr(region, "reg_code", 0) or (idx + 1)
            name = (getattr(region, "region_name", "") or "").strip()
            label = f"{int(code)}: {name}" if name else str(int(code))
            options.append((label, int(code)))
        return options

    reg_sel = widgets.SelectMultiple(
        options=_region_options_for_step(step_slider.value),
        value=(None,) if reg_code is None else (int(reg_code),),
        description="reg_code",
        rows=min(8, len(_region_options_for_step(step_slider.value))),
        layout=widgets.Layout(width="250px"),
    )
    # ensure initial value valid
    _valid = [v for (_, v) in reg_sel.options]
    if not all(v in _valid for v in reg_sel.value):
        reg_sel.value = (None,)

    size_slider = widgets.FloatSlider(
        value=float(s),
        min=0.1,
        max=20.0,
        step=0.1,
        description="size",
        continuous_update=False,
        readout_format=".1f",
    )
    out = widgets.Output()
    out_right = widgets.Output(layout=widgets.Layout(width="350px", overflow_y="auto"))

    # Shared state for hover → button workflow
    _state = {
        "last_idx": None, "hover_data": None, "qty": str(quantity).lower(),
        "multi_traces": [],  # list of (elem_id, x, y, steps, vals) for multi mode
        "n_fund": int(n_fund),  # steps per fundamental cycle
    }

    wave_mode = widgets.ToggleButtons(
        options=["Single", "Multi"],
        value="Single",
        description="",
        tooltips=["매번 새로 그림", "여러 element 파형을 겹쳐 그림"],
        layout=widgets.Layout(width="160px"),
    )

    wave_btn = widgets.Button(
        description="📊 Waveform",
        tooltip="호버 중인 element의 시간파형+FFT를 우측에 표시 (Space로도 가능)",
        layout=widgets.Layout(width="120px"),
    )

    clear_btn = widgets.Button(
        description="🗑 Clear",
        tooltip="Multi 모드에서 쌓인 파형 초기화",
        layout=widgets.Layout(width="80px"),
    )

    def _render_waveform():
        import numpy as np
        import io
        from IPython.display import display as ipy_display, Image as IPyImage

        idx = _state.get("last_idx")
        hd = _state.get("hover_data")
        qty = _state.get("qty", "b")
        if idx is None or hd is None:
            with out_right:
                out_right.clear_output(wait=True)
                print("⚠️ element 위에 마우스를 먼저 올려주세요")
            return

        elem_id = hd["elem_ids"][idx]
        x_pt, y_pt = hd["coords"][idx]
        steps_arr, vals_arr = _extract_element_timeseries(ts, elem_id, qty)

        is_multi = (wave_mode.value == "Multi")

        if is_multi:
            # Avoid duplicates
            existing_ids = [t[0] for t in _state["multi_traces"]]
            if elem_id not in existing_ids:
                _state["multi_traces"].append((elem_id, x_pt, y_pt, steps_arr, vals_arr))
        else:
            _state["multi_traces"] = [(elem_id, x_pt, y_pt, steps_arr, vals_arr)]

        traces = _state["multi_traces"]

        # Render
        fig_r, (ax_wave, ax_fft) = plt.subplots(2, 1, figsize=(4, 5))
        colors = plt.cm.tab10(np.linspace(0, 1, max(len(traces), 1)))

        # Fundamental period in steps (default 120 for one electrical cycle)
        n_fund = _state.get("n_fund", 120)

        for i, (eid, xp, yp, s_arr, v_arr) in enumerate(traces):
            c = colors[i % len(colors)]
            label = f"e{eid}({xp:.1f},{yp:.1f})"
            ax_wave.plot(s_arr, v_arr, ".-", markersize=2, linewidth=0.8, color=c, label=label)

            # FFT — bar chart at integer harmonic orders, skip negligible
            n = len(v_arr)
            if n > 1:
                fft_v = np.abs(np.fft.rfft(v_arr - v_arr.mean()))
                freqs = np.fft.rfftfreq(n, d=1.0)  # in [1/step]
                orders = freqs * n_fund  # convert to order (1 = 1/n_fund)

                # Only keep values at (near-)integer orders above threshold
                fft_max = fft_v[1:].max() if len(fft_v) > 1 else 1.0
                threshold = fft_max * 0.01  # 1% of peak
                int_ord = []
                int_val = []
                for k in range(1, len(orders)):
                    o = orders[k]
                    # Only integer or near-integer orders
                    if abs(o - round(o)) < 0.05 and fft_v[k] > threshold:
                        int_ord.append(round(o))
                        int_val.append(fft_v[k])

                n_traces = len(traces)
                bar_width = 0.8 / max(n_traces, 1)
                offset = (i - (n_traces - 1) / 2) * bar_width
                ax_fft.bar(
                    np.array(int_ord) + offset, int_val,
                    width=bar_width, color=c, alpha=0.7, label=label,
                )

        ax_wave.set_xlabel("Step")
        ax_wave.set_ylabel(qty.upper())
        title = f"{len(traces)} elem(s)" if is_multi else f"elem={traces[0][0]}"
        ax_wave.set_title(title, fontsize=8)
        ax_wave.grid(True, alpha=0.3)
        if len(traces) <= 8:
            ax_wave.legend(fontsize=6, loc="upper right")

        ax_fft.set_xlabel("Order (1=fundamental)")
        ax_fft.set_ylabel(f"|FFT({qty.upper()})|")
        ax_fft.set_title(f"FFT (DC removed, fund={n_fund} steps)", fontsize=8)
        ax_fft.grid(True, alpha=0.3, axis="y")
        if len(traces) <= 8:
            ax_fft.legend(fontsize=6, loc="upper right")

        fig_r.tight_layout()

        buf = io.BytesIO()
        fig_r.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig_r)
        buf.seek(0)

        with out_right:
            out_right.clear_output(wait=True)
            ipy_display(IPyImage(data=buf.getvalue()))

    def _on_wave_btn_click(_btn):
        _render_waveform()

    def _on_clear_btn_click(_btn):
        _state["multi_traces"] = []
        with out_right:
            out_right.clear_output(wait=True)
            print("🗑 파형 초기화됨")

    wave_btn.on_click(_on_wave_btn_click)
    clear_btn.on_click(_on_clear_btn_click)

    # Keep track of the last figure so ipympl/widget backends don't leave stale canvases.
    _last_fig = {"fig": None}

    def _sync_reg_options(*_):
        current = reg_sel.value
        new_options = _region_options_for_step(step_slider.value)
        reg_sel.options = new_options
        values = [v for (_, v) in new_options]
        kept = tuple(v for v in current if v in values)
        reg_sel.value = kept if kept else (None,)

    def _draw(*_):
        with out:
            out.clear_output(wait=True)
            try:
                if _last_fig["fig"] is not None:
                    plt.close(_last_fig["fig"])
            except Exception:
                pass
            fig, ax = plt.subplots()
            _last_fig["fig"] = fig
            step = int(step_slider.value)
            qty = str(qty_dd.value).lower()
            _state["qty"] = qty
            # Multi-select: None means all, single value as int, multiple as list
            selected = reg_sel.value
            if len(selected) == 1:
                rc = selected[0]  # None or single int
            else:
                rc = [v for v in selected if v is not None] or None
            ax = ts.by_step[step].plot(
                reg_code=rc,
                quantity=qty,
                s=size_slider.value,
                cmap=cmap,
                ax=ax,
                show=False,
                mesh=bool(mesh_chk.value),
            )
            header = ts.meta.get(step, {}).get("raw_header")
            if header:
                ax.set_title(f"{ax.get_title()}\n{header}")
            if not _zoom_enabled:
                ax.set_title(
                    ax.get_title()
                    + "\n(팁: `%matplotlib widget` 또는 ipympl이 있어야 드래그 줌 가능)"
                )

            fig.tight_layout()
            # Freeze layout so hover annotation won't trigger resize
            fig.set_layout_engine('none')

            # --- Hover annotation (nearest element info) ---
            _hover_data = _build_hover_data(ts.by_step[step], rc, qty)
            _state["hover_data"] = _hover_data
            _state["last_idx"] = None
            if _hover_data is not None:
                _attach_hover(fig, ax, _hover_data, qty, _state)

            # --- Space key: waveform + FFT for hovered element ---
            def _on_key(event, _s=_state):
                if event.key != ' ':
                    return
                _render_waveform()

            fig.canvas.mpl_connect("key_press_event", _on_key)

            plt.show()
            # In widget backends, keep the figure open (it's the displayed canvas).
            # For non-interactive inline/agg backends, close to avoid duplicated static images.
            backend = str(matplotlib.get_backend()).lower()
            if "inline" in backend or backend.endswith("agg") or "agg" in backend:
                plt.close(fig)
            return ax

    step_slider.observe(_sync_reg_options, names="value")
    step_slider.observe(_draw, names="value")
    qty_dd.observe(_draw, names="value")
    mesh_chk.observe(_draw, names="value")
    reg_sel.observe(_draw, names="value")
    size_slider.observe(_draw, names="value")

    display(widgets.VBox([
        widgets.HBox([step_slider, qty_dd, mesh_chk]),
        widgets.HBox([reg_sel, size_slider, wave_mode, wave_btn, clear_btn]),
        widgets.HBox([out, out_right]),
    ]))
    _draw()


def interactive_magnetic_quiver(
    ts: MagneticRegionsTimeSeries,
    initial_step=None,
    reg_code=None,
    normalize=False,
    stride=20,
    scale=None,
    width=0.002,
    cmap="jet",
    layout_width="650px",
):
    """Interactive step toggle quiver plot for MagneticRegionsTimeSeries."""

    if widgets is None or display is None:
        raise RuntimeError("ipywidgets is required for interactive plotting")
    if len(ts) == 0:
        raise ValueError("Empty time series.")

    steps = ts.steps
    if initial_step is None:
        initial_step = steps[0]

    step_slider = widgets.SelectionSlider(
        options=steps,
        value=initial_step,
        description="step",
        continuous_update=False,
        layout=widgets.Layout(width=layout_width),
    )
    normalize_chk = widgets.Checkbox(value=bool(normalize), description="normalize", indent=False)
    mesh_chk = widgets.Checkbox(value=False, description="mesh", indent=False)
    stride_slider = widgets.IntSlider(
        value=int(stride),
        min=1,
        max=200,
        step=1,
        description="stride",
        continuous_update=False,
    )
    scale_text = widgets.Text(value="" if scale is None else str(scale), description="scale", placeholder="(blank=None)")
    width_text = widgets.FloatText(value=float(width), description="width")
    out = widgets.Output()

    # Keep track of the last figure so ipympl/widget backends don't leave stale canvases.
    _last_fig = {"fig": None}

    def _parse_scale(text):
        t = str(text).strip()
        if t == "":
            return None
        return float(t)

    def _region_options_for_step(step):
        mr = ts.by_step[int(step)]
        options = [("all", None)]
        regions = getattr(mr, "_regions", [])
        for idx, region in enumerate(regions):
            if not getattr(region, "elements", None):
                continue
            code = getattr(region, "reg_code", 0) or (idx + 1)
            name = (getattr(region, "region_name", "") or "").strip()
            label = f"{code}: {name}" if name else str(code)
            options.append((label, int(code)))
        return options

    reg_dd = widgets.Dropdown(options=_region_options_for_step(step_slider.value), value=(None if reg_code is None else int(reg_code)), description="reg_code")
    if reg_dd.value not in [v for (_, v) in reg_dd.options]:
        reg_dd.value = None

    def _sync_reg_options(*_):
        current = reg_dd.value
        new_options = _region_options_for_step(step_slider.value)
        reg_dd.options = new_options
        values = [v for (_, v) in new_options]
        reg_dd.value = current if current in values else None

    def _draw(*_):
        with out:
            out.clear_output(wait=True)
            try:
                if _last_fig["fig"] is not None:
                    plt.close(_last_fig["fig"])
            except Exception:
                pass
            fig, ax = plt.subplots(layout="constrained")
            _last_fig["fig"] = fig
            step = int(step_slider.value)
            sc = _parse_scale(scale_text.value)
            ax = ts.by_step[step].plot_quiver(
                reg_code=reg_dd.value,
                normalize=bool(normalize_chk.value),
                stride=int(stride_slider.value),
                cmap=cmap,
                ax=ax,
                show=False,
                scale=sc,
                width=float(width_text.value),
                mesh=bool(mesh_chk.value),
            )
            header = ts.meta.get(step, {}).get("raw_header")
            if header:
                ax.set_title(f"{ax.get_title()}\n{header}")
            plt.show()
            backend = str(matplotlib.get_backend()).lower()
            if "inline" in backend or backend.endswith("agg") or "agg" in backend:
                plt.close(fig)
            return ax

    step_slider.observe(_sync_reg_options, names="value")
    step_slider.observe(_draw, names="value")
    reg_dd.observe(_draw, names="value")
    normalize_chk.observe(_draw, names="value")
    mesh_chk.observe(_draw, names="value")
    stride_slider.observe(_draw, names="value")
    scale_text.observe(_draw, names="value")
    width_text.observe(_draw, names="value")

    display(
        widgets.VBox(
            [
                widgets.HBox([step_slider]),
                widgets.HBox([reg_dd, normalize_chk, mesh_chk]),
                widgets.HBox([stride_slider, scale_text, width_text]),
                out,
            ]
        )
    )
    _sync_reg_options()
    _draw()
