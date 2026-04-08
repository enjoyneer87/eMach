"""Winding auto-adjust helpers for Motor-CAD workflows.

This module encapsulates winding/conductor size updates that should run
after geometry-related variable changes.
"""
from __future__ import annotations

from typing import Dict


def auto_resize_copper_after_geometry_update(
    mc,
    *,
    all_vars: Dict[str, object],
    verbose: bool = True,
) -> None:
    """Auto-adjust Copper_Width/Height after geometry ratio updates.

    Triggered only when geometry-driving variables include at least one of:
    ``Ratio_Bore`` or ``Ratio_SlotDepth_ParallelSlot``.

    Formula follows ``SkkuEMLabProject/calcConductorSize.m``. Because DOE
    flow does not pass ``temp_fillfactor`` explicitly, this helper infers
    current copper fill factor from existing Motor-CAD values and preserves
    it while recomputing copper width/height for the updated slot geometry.
    """
    from .melec_req_check import get_mcad_variables, set_mcad_variables

    trigger_names = {
        "Ratio_Bore",
        "Ratio_SlotDepth_ParallelSlot",
    }
    if not (set(all_vars.keys()) & trigger_names):
        return

    needed = [
        "Area_Slot",
        "Area_Winding_With_Liner",
        "Slot_Width",
        "Winding_Depth",
        "WindingLayers",
        "Insulation_Thickness",
        "Liner_Thickness",
        "ConductorSeparation",
        "Copper_Width",
        "Copper_Height",
    ]
    raw = get_mcad_variables(mc, needed, strict=False, verbose=False)

    try:
        area_slot = float(raw["Area_Slot"])
        area_winding = float(raw["Area_Winding_With_Liner"])
        slot_width = float(raw["Slot_Width"])
        winding_depth = float(raw["Winding_Depth"])
        winding_layers = float(raw["WindingLayers"])
        insulation_t = float(raw["Insulation_Thickness"])
        liner_t = float(raw["Liner_Thickness"])
        conductor_sep = float(raw["ConductorSeparation"])
        copper_w_old = float(raw["Copper_Width"])
        copper_h_old = float(raw["Copper_Height"])
    except Exception as exc:
        if verbose:
            print(f"  [WARN] copper auto-resize skipped (missing vars): {exc}")
        return

    if area_slot <= 0 or area_winding <= 0 or winding_layers <= 0:
        if verbose:
            print("  [WARN] copper auto-resize skipped (invalid areas/layers)")
        return

    fill_factor_pct = (
        copper_w_old
        * copper_h_old
        * winding_layers
        / area_slot
    ) * 100.0
    effective_fill_factor = area_slot * fill_factor_pct / area_winding
    effective_slot_area = area_winding * (effective_fill_factor / 100.0)
    turn_per_area = effective_slot_area / winding_layers

    copper_w_new = (
        slot_width
        - 2 * liner_t
        - 2 * insulation_t
        - 2 * conductor_sep
    )
    if copper_w_new <= 0:
        if verbose:
            print("  [WARN] copper auto-resize skipped (computed width <= 0)")
        return

    copper_h_new = turn_per_area / copper_w_new

    max_copper_h = (
        winding_depth
        - liner_t
        - 10 * 2 * insulation_t
        - 11 * conductor_sep
    ) / 10
    if max_copper_h <= 0:
        if verbose:
            print("  [WARN] copper auto-resize skipped (height limit <= 0)")
        return
    if copper_h_new > max_copper_h:
        copper_h_new = max_copper_h

    set_mcad_variables(
        mc,
        {
            "Copper_Width": float(copper_w_new),
            "Copper_Height": float(copper_h_new),
        },
        verbose=False,
    )
    if verbose:
        print(
            "  [auto-copper] "
            f"Copper_Width={copper_w_new:.6f}, "
            f"Copper_Height={copper_h_new:.6f}"
        )


__all__ = [
    "auto_resize_copper_after_geometry_update",
]
