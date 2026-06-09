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


def interactive_magnetic_plot(ts: MagneticRegionsTimeSeries, initial_step=None, quantity="b", reg_code=None, s=2, cmap="jet"):
    """Interactive step toggle plot for MagneticRegionsTimeSeries."""

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
        layout=widgets.Layout(width="650px"),
    )
    qty_dd = widgets.Dropdown(
        options=[("B", "b"), ("A", "a"), ("J", "j")],
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

    reg_dd = widgets.Dropdown(
        options=_region_options_for_step(step_slider.value),
        value=(None if reg_code is None else int(reg_code)),
        description="reg_code",
    )
    if reg_dd.value not in [v for (_, v) in reg_dd.options]:
        reg_dd.value = None

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

    # Keep track of the last figure so ipympl/widget backends don't leave stale canvases.
    _last_fig = {"fig": None}

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
            qty = str(qty_dd.value).lower()
            rc = reg_dd.value
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
    reg_dd.observe(_draw, names="value")
    size_slider.observe(_draw, names="value")

    display(widgets.VBox([widgets.HBox([step_slider, qty_dd, mesh_chk]), widgets.HBox([reg_dd, size_slider]), out]))
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
