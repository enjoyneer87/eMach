from __future__ import annotations

from typing import Optional, Sequence

import matplotlib
import matplotlib.pyplot as plt

from .magnetic import MagElement, MagneticRegionsTimeSeries


def interactive_b_locus_field_plot(
    ts: MagneticRegionsTimeSeries,
    *,
    steps: Optional[Sequence[int]] = None,
    reg_code: Optional[int] = None,
    ref_step: Optional[int] = None,
    element_stride: int = 2,
    locus_scale: float = 0.2,
    plot_mode: str = "both",
    mesh_alpha: float = 0.35,
    mesh_linewidth: float = 0.2,
    alpha: float = 0.85,
    linewidth: float = 1.0,
    mark_start_end: bool = False,
    equal_aspect: bool = True,
):
    """Interactive B-locus (Bx,By) field plot over the mesh.

    This wraps :meth:`MagElement.plot_b_locus_field_from_timeseries` with ipywidgets controls.

    Parameters
    ----------
    ts:
        Magnetic time-series parsed via `get_magnetic_timeseries_from_file`.
    steps:
        Steps to use for locus loops. Defaults to `ts.steps`.
    reg_code:
        Region code to filter. None means all.
    ref_step:
        Reference step used for mesh/centroids. Defaults to first step.
    plot_mode:
        One of: "both" (locus+mesh), "locus", "mesh".

    Returns
    -------
    If ipywidgets is available, returns (ui, out). Otherwise returns (fig, ax).
    """

    steps_all = list(steps) if steps is not None else list(getattr(ts, "steps", []) or [])
    if not steps_all:
        raise ValueError("No steps found in ts")

    if ref_step is None:
        ref_step = int(steps_all[0])

    try:
        import ipywidgets as widgets
        from IPython.display import display
    except Exception:
        widgets = None
        display = None

    def _region_options_from_step(step: int):
        mr0 = ts.by_step[int(step)]
        regions0 = list(getattr(mr0, "_regions", []) or [])
        options = [("all", None)]
        for idx, region in enumerate(regions0):
            if not getattr(region, "elements", None):
                continue
            code = int(getattr(region, "reg_code", 0) or (idx + 1))
            name = (getattr(region, "region_name", "") or "").strip()
            label = f"{code}: {name}" if name else str(code)
            options.append((label, int(code)))
        return options

    if widgets is None or display is None:
        # Non-interactive fallback
        if plot_mode == "mesh":
            ts.plot_mesh(step=int(ref_step), reg_code=reg_code, color="k", linewidth=float(mesh_linewidth), alpha=float(mesh_alpha), show=True)
            return None

        ax = MagElement.plot_b_locus_field_from_timeseries(
            ts,
            steps=steps_all,
            reg_code=reg_code,
            ref_step=int(ref_step),
            element_stride=int(element_stride),
            locus_scale=float(locus_scale),
            show_mesh=(plot_mode == "both"),
            mesh_alpha=float(mesh_alpha),
            mesh_linewidth=float(mesh_linewidth),
            alpha=float(alpha),
            linewidth=float(linewidth),
            mark_start_end=bool(mark_start_end),
            equal_aspect=bool(equal_aspect),
            show=True,
        )
        return ax

    out = widgets.Output()

    reg_dd = widgets.Dropdown(options=_region_options_from_step(ref_step), value=reg_code, description="reg_code")
    if reg_dd.value not in [v for (_, v) in reg_dd.options]:
        reg_dd.value = None

    step_options = [(str(s), int(s)) for s in steps_all]
    ref_step_dd = widgets.Dropdown(options=step_options, value=int(ref_step), description="ref_step")

    element_stride_sl = widgets.IntSlider(value=int(element_stride), min=1, max=20, step=1, description="stride")
    locus_scale_sl = widgets.FloatSlider(value=float(locus_scale), min=0.01, max=1.0, step=0.01, description="scale(mm/T)")

    plot_mode_dd = widgets.Dropdown(
        options=[("locus+mesh", "both"), ("locus only", "locus"), ("mesh only", "mesh")],
        value=str(plot_mode),
        description="mode",
    )

    mesh_alpha_sl = widgets.FloatSlider(value=float(mesh_alpha), min=0.0, max=1.0, step=0.05, description="mesh_alpha")
    mesh_lw_sl = widgets.FloatSlider(value=float(mesh_linewidth), min=0.05, max=1.0, step=0.05, description="mesh_lw")

    def _sync_reg_options(*_):
        current = reg_dd.value
        new_options = _region_options_from_step(int(ref_step_dd.value))
        reg_dd.options = new_options
        values = [v for (_, v) in new_options]
        reg_dd.value = current if current in values else None

    def _update(*_):
        with out:
            out.clear_output(wait=True)

            if plot_mode_dd.value == "mesh":
                ts.plot_mesh(
                    step=int(ref_step_dd.value),
                    reg_code=reg_dd.value,
                    color="k",
                    linewidth=float(mesh_lw_sl.value),
                    alpha=float(mesh_alpha_sl.value),
                    show=True,
                )
                return

            fig, ax = plt.subplots(layout="constrained")
            MagElement.plot_b_locus_field_from_timeseries(
                ts,
                steps=steps_all,
                reg_code=reg_dd.value,
                ref_step=int(ref_step_dd.value),
                element_stride=int(element_stride_sl.value),
                locus_scale=float(locus_scale_sl.value),
                show_mesh=(plot_mode_dd.value == "both"),
                mesh_alpha=float(mesh_alpha_sl.value),
                mesh_linewidth=float(mesh_lw_sl.value),
                alpha=float(alpha),
                linewidth=float(linewidth),
                mark_start_end=bool(mark_start_end),
                equal_aspect=bool(equal_aspect),
                show=False,
                ax=ax,
            )
            plt.show()

            backend = str(matplotlib.get_backend()).lower()
            if "inline" in backend or backend.endswith("agg") or "agg" in backend:
                plt.close(fig)

    ref_step_dd.observe(_sync_reg_options, names="value")

    for w in (reg_dd, ref_step_dd, element_stride_sl, locus_scale_sl, plot_mode_dd, mesh_alpha_sl, mesh_lw_sl):
        w.observe(_update, names="value")

    ui = widgets.VBox(
        [
            widgets.HBox([reg_dd, ref_step_dd, plot_mode_dd]),
            widgets.HBox([element_stride_sl, locus_scale_sl]),
            widgets.HBox([mesh_alpha_sl, mesh_lw_sl]),
        ]
    )

    display(ui, out)
    _sync_reg_options()
    _update()
    return ui, out
