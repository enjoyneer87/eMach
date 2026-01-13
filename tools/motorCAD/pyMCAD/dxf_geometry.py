from __future__ import annotations

"""DXF -> PyMotorCAD geometry helpers.

This module contains utilities for taking a DXF export (often from Motor-CAD or CAD tools)
and converting it into PyMotorCAD geometry objects like ``EntityList`` and ``Region``.

Important note about "closed regions"
-------------------------------------
DXF content often arrives as *primitive segments* (LINE/ARC) rather than a single closed
polyline loop. In that case, conversion will naturally produce open geometry unless you:
- export closed LWPOLYLINE/POLYLINE loops, or
- post-process by stitching segments into closed loops.

The helpers here focus on safe, best-effort conversion. They do not attempt full
geometric stitching by default.
"""

from dataclasses import dataclass
from math import atan2, degrees, hypot
from typing import Any, Iterable, Literal


@dataclass(frozen=True)
class DxfPrimitive:
    """Solver-neutral primitive extracted from DXF.

    Notes
    -----
    - Coordinates are stored in DXF units.
    - For arcs, ``dir`` follows DXF's CCW convention:
      ``dir=+1`` means CCW from ``start`` to ``end``.
      ``dir=-1`` means CW (i.e., reversed direction).
    """

    kind: Literal["LINE", "ARC"]
    layer: str
    start: tuple[float, float]
    end: tuple[float, float]
    centre: tuple[float, float] | None = None
    radius: float | None = None
    dir: int = +1
    source: str | None = None


@dataclass(frozen=True)
class DxfLoop:
    """Closed loop expressed as an ordered list of primitive indices and flips."""

    primitive_indices: tuple[int, ...]
    flipped: tuple[bool, ...]
    layer: str | None = None


def _pt_key(x: float, y: float, tol: float) -> tuple[int, int]:
    if tol <= 0:
        raise ValueError("tol must be > 0")
    return (int(round(float(x) / tol)), int(round(float(y) / tol)))


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def _angle_deg(x: float, y: float) -> float:
    return float((degrees(atan2(float(y), float(x))) + 360.0) % 360.0)


def _segment_dir_at_node(p: DxfPrimitive, *, at_start: bool) -> tuple[float, float]:
    """Approximate outgoing direction at a node using chord direction.

    This is intentionally lightweight (no arc tangents) but works well for
    most DXF exports that consist of simple piecewise LINE/ARC boundaries.
    """

    if at_start:
        x0, y0 = p.start
        x1, y1 = p.end
    else:
        x0, y0 = p.end
        x1, y1 = p.start

    dx = float(x1) - float(x0)
    dy = float(y1) - float(y0)
    n = hypot(dx, dy)
    if n == 0:
        return (0.0, 0.0)
    return (dx / n, dy / n)


def _turn_angle(prev_dir: tuple[float, float], next_dir: tuple[float, float]) -> float:
    """Return signed turn angle in [0, 360). Smaller is "straighter"."""

    px, py = prev_dir
    nx, ny = next_dir
    # atan2(cross, dot)
    cross = px * ny - py * nx
    dot = px * nx + py * ny
    ang = degrees(atan2(cross, dot))
    return float((ang + 360.0) % 360.0)


def primitives_from_dxf(
    dxf_path: str,
    *,
    include_layers: list[str] | tuple[str, ...] | None = None,
    include_entity_types: list[str] | tuple[str, ...] = ("LWPOLYLINE", "POLYLINE", "LINE", "ARC"),
    explode_polylines: bool = True,
) -> list[DxfPrimitive]:
    """Parse DXF and return a flat list of primitives (LINE/ARC).

    This function is intended to feed higher-level logic:
    - stitching primitives into closed loops
    - mapping layers to semantic tags
    - exporting to solver-specific geometry APIs
    """

    import ezdxf

    include_types = {t.upper() for t in include_entity_types}
    include_layers_set = None if include_layers is None else {str(x) for x in include_layers}

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    out: list[DxfPrimitive] = []

    for e in msp:
        dxftype = e.dxftype().upper()
        if dxftype not in include_types:
            continue

        try:
            layer = str(e.dxf.layer)
        except Exception:
            layer = "0"
        if include_layers_set is not None and layer not in include_layers_set:
            continue

        if dxftype == "LINE":
            s = (float(e.dxf.start.x), float(e.dxf.start.y))
            t = (float(e.dxf.end.x), float(e.dxf.end.y))
            out.append(DxfPrimitive(kind="LINE", layer=layer, start=s, end=t, source="DXF:LINE"))
            continue

        if dxftype == "ARC":
            c = (float(e.dxf.center.x), float(e.dxf.center.y))
            r = float(e.dxf.radius)
            # ezdxf expresses ARC with CCW sweep from start_angle to end_angle.
            # We store CCW as dir=+1.
            a0 = float(e.dxf.start_angle)
            a1 = float(e.dxf.end_angle)
            from math import cos, radians, sin

            s = (c[0] + abs(r) * cos(radians(a0)), c[1] + abs(r) * sin(radians(a0)))
            t = (c[0] + abs(r) * cos(radians(a1)), c[1] + abs(r) * sin(radians(a1)))
            out.append(
                DxfPrimitive(
                    kind="ARC",
                    layer=layer,
                    start=(float(s[0]), float(s[1])),
                    end=(float(t[0]), float(t[1])),
                    centre=(float(c[0]), float(c[1])),
                    radius=float(abs(r)),
                    dir=+1,
                    source="DXF:ARC",
                )
            )
            continue

        if dxftype in ("LWPOLYLINE", "POLYLINE"):
            pts, closed = _dxf_polyline_points(e)
            if len(pts) < 2:
                continue
            if closed and pts[0] != pts[-1]:
                pts = list(pts) + [pts[0]]

            if not explode_polylines:
                # Keep as many LINE segments as possible; bulge-based arcs are ignored here.
                # (We prefer explicit ARC entities if exact arcs are required.)
                pass

            for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
                out.append(
                    DxfPrimitive(
                        kind="LINE",
                        layer=layer,
                        start=(float(x0), float(y0)),
                        end=(float(x1), float(y1)),
                        source=f"DXF:{dxftype}",
                    )
                )
            continue

    return out


def stitch_primitives_to_loops(
    primitives: list[DxfPrimitive],
    *,
    tol: float = 1e-4,
    by_layer: bool = True,
    max_steps: int = 20000,
) -> list[DxfLoop]:
    """Stitch unordered primitives into closed loops.

    Strategy
    --------
    Build an endpoint graph (snapped by tolerance) and perform a greedy walk.
    At each junction, choose the next unused edge with the smallest left-turn
    from the previous direction. This tends to trace exterior boundaries and
    works well on typical Motor-CAD/SYRE-like DXF exports.
    """

    if not primitives:
        return []

    # Cluster endpoints into node IDs
    node_id_by_key: dict[tuple[int, int], int] = {}
    node_xy: list[tuple[float, float]] = []

    def get_node_id(pt: tuple[float, float]) -> int:
        k = _pt_key(pt[0], pt[1], tol)
        if k in node_id_by_key:
            return node_id_by_key[k]
        node_id = len(node_xy)
        node_id_by_key[k] = node_id
        node_xy.append((float(pt[0]), float(pt[1])))
        return node_id

    edge_nodes: list[tuple[int, int]] = []
    for p in primitives:
        u = get_node_id(p.start)
        v = get_node_id(p.end)
        edge_nodes.append((u, v))

    # adjacency: node -> list of edge indices
    adj: dict[int, list[int]] = {}
    for ei, (u, v) in enumerate(edge_nodes):
        adj.setdefault(u, []).append(ei)
        adj.setdefault(v, []).append(ei)

    unused: set[int] = set(range(len(primitives)))
    loops: list[DxfLoop] = []

    def same_group(a: DxfPrimitive, b: DxfPrimitive) -> bool:
        return (a.layer == b.layer) if by_layer else True

    # Pre-group edges by layer to avoid accidental cross-layer stitching
    edges_by_layer: dict[str, list[int]] = {}
    if by_layer:
        for i, p in enumerate(primitives):
            edges_by_layer.setdefault(p.layer, []).append(i)

    layer_order = list(edges_by_layer.keys()) if by_layer else ["__all__"]
    for layer in layer_order:
        layer_edges = set(edges_by_layer.get(layer, [])) if by_layer else unused

        while True:
            candidates = list(unused.intersection(layer_edges))
            if not candidates:
                break

            start_edge = candidates[0]
            p0 = primitives[start_edge]
            u0, v0 = edge_nodes[start_edge]

            # Choose an orientation that starts from the smaller radius (often inside-out)
            ru = hypot(*node_xy[u0])
            rv = hypot(*node_xy[v0])
            cur_edge = start_edge
            if rv < ru:
                prev_node, cur_node = v0, u0
                flipped0 = True
            else:
                prev_node, cur_node = u0, v0
                flipped0 = False

            start_node = prev_node

            loop_edges: list[int] = [cur_edge]
            loop_flips: list[bool] = [flipped0]
            unused.remove(cur_edge)

            prev_dir = _segment_dir_at_node(p0, at_start=flipped0)  # from prev_node to cur_node
            steps = 0
            ok = False

            while steps < max_steps:
                steps += 1
                if cur_node == start_node and steps > 1:
                    ok = True
                    break

                next_edges = [ei for ei in adj.get(cur_node, []) if ei in unused and ei in layer_edges]
                if not next_edges:
                    break

                best_ei: int | None = None
                best_flip = False
                best_next_node: int | None = None
                best_turn = None

                for ei in next_edges:
                    pu = primitives[ei]
                    if not same_group(p0, pu):
                        continue
                    a, b = edge_nodes[ei]
                    if a == cur_node:
                        flip = False
                        next_node = b
                    elif b == cur_node:
                        flip = True
                        next_node = a
                    else:
                        continue

                    cand_dir = _segment_dir_at_node(pu, at_start=flip)
                    turn = _turn_angle(prev_dir, cand_dir)
                    if best_turn is None or turn < best_turn:
                        best_turn = turn
                        best_ei = ei
                        best_flip = flip
                        best_next_node = next_node

                if best_ei is None:
                    break

                unused.remove(best_ei)
                loop_edges.append(best_ei)
                loop_flips.append(best_flip)

                # advance
                pe = primitives[best_ei]
                prev_node = cur_node
                cur_node = int(best_next_node) if best_next_node is not None else prev_node
                prev_dir = _segment_dir_at_node(pe, at_start=best_flip)

            if ok and len(loop_edges) >= 2:
                loops.append(DxfLoop(tuple(loop_edges), tuple(loop_flips), layer=layer if by_layer else None))
            # If not ok, we just drop the partial walk; remaining edges may still form other loops.

    return loops


def dxf_to_ir(
    dxf_path: str,
    *,
    include_layers: list[str] | tuple[str, ...] | None = None,
    include_entity_types: list[str] | tuple[str, ...] = ("LWPOLYLINE", "POLYLINE", "LINE", "ARC"),
    stitch: bool = True,
    stitch_tol: float = 1e-4,
    stitch_by_layer: bool = True,
    estimate_periodicity: bool = True,
) -> dict[str, Any]:
    """Build a solver-neutral intermediate representation (IR) from DXF.

    Returns a dict with keys:
    - ``primitives``: list[DxfPrimitive]
    - ``loops``: list[DxfLoop] (if stitch=True)
    - ``meta``: dict with best-effort metadata (layer list, basic periodicity hints)

    The metadata estimation is inspired by utilities in ``tools/jmag`` (e.g.
    `checkInnerOuterMotor`, `findStatorOneSlotAngle`, `findRotorOnePoleAngle`).
    """

    primitives = primitives_from_dxf(
        dxf_path,
        include_layers=include_layers,
        include_entity_types=include_entity_types,
        explode_polylines=True,
    )

    loops: list[DxfLoop] = []
    if stitch:
        loops = stitch_primitives_to_loops(primitives, tol=float(stitch_tol), by_layer=bool(stitch_by_layer))

    layers = sorted({p.layer for p in primitives})
    meta: dict[str, Any] = {
        "dxf_path": str(dxf_path),
        "layers": layers,
        "n_primitives": int(len(primitives)),
        "n_loops": int(len(loops)),
    }

    if estimate_periodicity and primitives:
        # Runner type: compare stator vs rotor radii if layer naming/IDs allow it.
        # Common patterns:
        # - SYRE-like numeric layers: stator=1, rotor=2
        stator_layers = {"1", "stator", "Stator"}
        rotor_layers = {"2", "rotor", "Rotor"}

        def radii_for(layer_set: set[str]) -> list[float]:
            rs: list[float] = []
            for p in primitives:
                if p.layer in layer_set:
                    rs.append(hypot(p.start[0], p.start[1]))
                    rs.append(hypot(p.end[0], p.end[1]))
            return rs

        sr = radii_for(stator_layers)
        rr = radii_for(rotor_layers)
        if sr and rr:
            stator_max = max(sr)
            stator_min = min(sr)
            rotor_max = max(rr)
            rotor_min = min(rr)
            if stator_max < rotor_min:
                meta["runner_type"] = "OuterRotor"
            elif rotor_max < stator_min:
                meta["runner_type"] = "InnerRotor"

        # One-slot / one-pole angle heuristics: look at endpoint angles in first quadrant.
        # This mimics the intent of tools/jmag/GeomApp/findStatorOneSlotAngle.m and
        # findRotorOnePoleAngle.m (but computed directly from DXF endpoints).
        def max_theta_under_90(layer_set: set[str]) -> float | None:
            thetas: list[float] = []
            for p in primitives:
                if p.layer not in layer_set:
                    continue
                for (x, y) in (p.start, p.end):
                    th = _angle_deg(x, y)
                    if th <= 90.0:
                        thetas.append(th)
            if not thetas:
                return None
            return float(max(thetas))

        stator_slot = max_theta_under_90(stator_layers)
        rotor_pole = max_theta_under_90(rotor_layers)
        if stator_slot is not None:
            meta["stator_one_slot_angle_deg"] = stator_slot
            if stator_slot > 0:
                meta["Qs_est"] = 360.0 / stator_slot
        if rotor_pole is not None:
            meta["rotor_one_pole_angle_deg"] = rotor_pole
            if rotor_pole > 0:
                meta["PoleNumber_est"] = 360.0 / rotor_pole

    return {"primitives": primitives, "loops": loops, "meta": meta}


def force_black_white(ax):
    """Force a Matplotlib axes to a black-on-white DXF-like appearance."""

    ax.set_facecolor("white")
    ax.figure.set_facecolor("white")

    for ln in getattr(ax, "lines", []):
        try:
            ln.set_color("black")
        except Exception:
            pass
    for p in getattr(ax, "patches", []):
        try:
            p.set_edgecolor("black")
            p.set_facecolor("none")
        except Exception:
            pass
    for c in getattr(ax, "collections", []):
        try:
            c.set_edgecolor("black")
        except Exception:
            pass
        try:
            c.set_facecolor("none")
        except Exception:
            pass

    ax.axis("off")


def plot_dxf_black_white(dxf_path: str, title: str | None = None):
    import matplotlib.pyplot as plt
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=True)

    force_black_white(ax)
    if title:
        ax.set_title(title, fontsize=14, pad=10)
    plt.show()


def plot_dxf_layers_black_white(
    dxf_path: str,
    *,
    layers: list[str] | tuple[str, ...],
    title: str | None = None,
):
    """Plot only selected layers from a DXF (black/white)."""

    import matplotlib.pyplot as plt
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    keep = {str(l) for l in layers}
    doc = ezdxf.readfile(dxf_path)

    # Turn off all non-selected layers in-memory before drawing.
    try:
        for layer in doc.layers:
            if layer.dxf.name not in keep:
                try:
                    layer.off()
                except Exception:
                    pass
    except Exception:
        pass

    msp = doc.modelspace()

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=True)

    force_black_white(ax)
    if title:
        ax.set_title(title, fontsize=14, pad=10)
    plt.show()


def _dxf_xy_to_coordinate(xy):
    from ansys.motorcad.core.geometry import Coordinate

    x, y = xy
    return Coordinate(float(x), float(y))


def _dxf_arc_to_motorcad_arc(entity):
    """Convert an ezdxf ARC to ansys.motorcad.core.geometry.Arc."""

    from math import cos, radians, sin

    from ansys.motorcad.core.geometry import Arc, Coordinate

    c = entity.dxf.center
    r = float(entity.dxf.radius)
    a0 = float(entity.dxf.start_angle)
    a1 = float(entity.dxf.end_angle)

    centre = Coordinate(float(c.x), float(c.y))
    start = Coordinate(centre.x + r * cos(radians(a0)), centre.y + r * sin(radians(a0)))
    end = Coordinate(centre.x + r * cos(radians(a1)), centre.y + r * sin(radians(a1)))

    # DXF arc direction is CCW from start_angle to end_angle.
    # In PyMotorCAD, Arc.reverse() flips the sign of radius.
    # We store the DXF-native direction as positive-radius (CCW).
    return Arc(start, end, centre=centre, radius=abs(r))


def _primitive_to_entity(p: DxfPrimitive, *, flipped: bool):
    from ansys.motorcad.core.geometry import Arc, Line

    if p.kind == "LINE":
        x0, y0 = p.end if flipped else p.start
        x1, y1 = p.start if flipped else p.end
        from ansys.motorcad.core.geometry import Coordinate

        return Line(Coordinate(x0, y0), Coordinate(x1, y1))

    if p.kind == "ARC":
        if p.centre is None or p.radius is None:
            raise ValueError("ARC primitive missing centre/radius")
        from ansys.motorcad.core.geometry import Coordinate

        s = p.end if flipped else p.start
        t = p.start if flipped else p.end
        c = p.centre
        arc = Arc(Coordinate(s[0], s[1]), Coordinate(t[0], t[1]), centre=Coordinate(c[0], c[1]), radius=abs(p.radius))
        if flipped:
            arc.reverse()
        return arc

    raise ValueError(f"Unsupported primitive kind: {p.kind}")


def ir_to_motorcad_regions(
    ir: dict[str, Any],
    *,
    default_region_type: str = "dxf_import",
    layer_region_type_map: dict[str, object] | None = None,
    layer_region_type_patterns: dict[str, object] | None = None,
    name_prefix: str = "DXF",
):
    """Convert IR (from dxf_to_ir) into Motor-CAD Regions.

    Uses stitched loops if present; falls back to entity-per-primitive behavior
    if ``loops`` is empty.
    """

    from ansys.motorcad.core.geometry import EntityList, Region

    primitives: list[DxfPrimitive] = list(ir.get("primitives") or [])
    loops: list[DxfLoop] = list(ir.get("loops") or [])

    regions: list[Region] = []

    if loops:
        for i, lp in enumerate(loops):
            layer = lp.layer or "0"
            if layer_region_type_map and layer in layer_region_type_map:
                region_type = layer_region_type_map[layer]
            else:
                region_type = infer_region_type_from_layer_name(
                    layer,
                    default=default_region_type,
                    mapping=layer_region_type_patterns,
                )

            ent = EntityList()
            for prim_idx, flipped in zip(lp.primitive_indices, lp.flipped):
                ent.append(_primitive_to_entity(primitives[int(prim_idx)], flipped=bool(flipped)))

            r = Region(region_type=region_type)
            r.name = f"{name_prefix}_{layer}_loop_{i}"
            r.entities = ent
            regions.append(r)

        return regions

    # Fallback: mimic old behavior (one region per DXF entity)
    # Note: we intentionally keep this behavior so existing notebooks don't break.
    entitylists_by_group = {}
    for p in primitives:
        entitylists_by_group.setdefault(p.layer, []).append(p)

    for layer, plist in entitylists_by_group.items():
        if layer_region_type_map and layer in layer_region_type_map:
            region_type = layer_region_type_map[layer]
        else:
            region_type = infer_region_type_from_layer_name(
                layer,
                default=default_region_type,
                mapping=layer_region_type_patterns,
            )
        for j, prim in enumerate(plist):
            ent = EntityList([_primitive_to_entity(prim, flipped=False)])
            r = Region(region_type=region_type)
            r.name = f"{name_prefix}_{layer}_{j}"
            r.entities = ent
            regions.append(r)

    return regions


def _dxf_polyline_points(entity) -> tuple[list[tuple[float, float]], bool]:
    """Extract (x,y) points and closed flag from POLYLINE/LWPOLYLINE."""

    dxftype = entity.dxftype()
    if dxftype == "LWPOLYLINE":
        pts = [(float(x), float(y)) for x, y in entity.get_points("xy")]
        closed = bool(getattr(entity, "closed", False))
        return pts, closed

    # POLYLINE (2D)
    pts = []
    try:
        for v in entity.vertices():
            loc = v.dxf.location
            pts.append((float(loc.x), float(loc.y)))
    except Exception:
        pass
    closed = bool(getattr(entity, "is_closed", False))
    return pts, closed


def dxf_to_entitylists(
    dxf_path: str,
    *,
    by_layer: bool = True,
    include_layers: list[str] | tuple[str, ...] | None = None,
    include_entity_types: list[str] | tuple[str, ...] = ("LWPOLYLINE", "POLYLINE", "LINE", "ARC"),
    fit_polylines: bool = True,
    line_tolerance: float = 1e-4,
    arc_tolerance: float = 1e-4,
    group_strategy: str = "entity",
):
    """Convert DXF geometry to PyMotorCAD geometry EntityList objects.

    Parameters
    ----------
    group_strategy:
        - ``"entity"`` (default): one EntityList per DXF entity
        - ``"layer"``: one combined EntityList per layer (all segments appended)

    Returns
    -------
    dict[str, list[EntityList]]
    """

    import ezdxf

    from ansys.motorcad.core.geometry import EntityList, Line
    from ansys.motorcad.core.geometry_fitting import return_entity_list

    include_types = {t.upper() for t in include_entity_types}
    include_layers_set = None if include_layers is None else {str(x) for x in include_layers}

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    out: dict[str, list[EntityList]] = {}

    def key_for(e) -> str:
        if not by_layer:
            return "all"
        try:
            return str(e.dxf.layer)
        except Exception:
            return "0"

    def _append_entitylist(group: str, ent: EntityList):
        if group not in out:
            out[group] = []
        if group_strategy == "layer":
            if not out[group]:
                out[group].append(EntityList())
            out[group][0].extend(ent)
        else:
            out[group].append(ent)

    for e in msp:
        dxftype = e.dxftype().upper()
        if dxftype not in include_types:
            continue

        k = key_for(e)
        if include_layers_set is not None and k not in include_layers_set:
            continue

        if dxftype in ("LWPOLYLINE", "POLYLINE"):
            pts, closed = _dxf_polyline_points(e)
            if len(pts) < 2:
                continue

            # Ensure closure for closed polylines
            if closed and pts[0] != pts[-1]:
                pts = list(pts) + [pts[0]]

            coords = [_dxf_xy_to_coordinate(xy) for xy in pts]

            if fit_polylines:
                ent = return_entity_list(coords, float(line_tolerance), float(arc_tolerance))
            else:
                ent = EntityList()
                for p0, p1 in zip(coords[:-1], coords[1:]):
                    ent.append(Line(p0, p1))

            _append_entitylist(k, ent)
            continue

        if dxftype == "LINE":
            start = _dxf_xy_to_coordinate((e.dxf.start.x, e.dxf.start.y))
            end = _dxf_xy_to_coordinate((e.dxf.end.x, e.dxf.end.y))
            _append_entitylist(k, EntityList([Line(start, end)]))
            continue

        if dxftype == "ARC":
            arc = _dxf_arc_to_motorcad_arc(e)
            _append_entitylist(k, EntityList([arc]))
            continue

    return out


def dxf_entitylists_to_regions(
    entitylists_by_group: dict[str, list],
    *,
    region_type: str = "dxf_import",
    name_prefix: str = "DXF",
):
    """Create PyMotorCAD Region objects from EntityLists."""

    from ansys.motorcad.core.geometry import Region

    regions = []
    for group, lists in entitylists_by_group.items():
        for i, ent in enumerate(lists):
            r = Region(region_type=region_type)
            r.name = f"{name_prefix}_{group}_{i}" if group else f"{name_prefix}_{i}"
            r.entities = ent
            regions.append(r)
    return regions


def infer_region_type_from_layer_name(
    layer_name: str,
    *,
    default: str = "dxf_import",
    mapping: dict[str, object] | None = None,
):
    """Infer a Motor-CAD RegionType name from a DXF layer name."""

    import re

    from ansys.motorcad.core.geometry import RegionType

    name = str(layer_name or "").strip()
    lower = name.lower()

    def _to_region_type(value):
        if isinstance(value, RegionType):
            return value
        if isinstance(value, str):
            return getattr(RegionType, value)
        return value

    if mapping:
        for pattern, value in mapping.items():
            pat = str(pattern)
            if pat.startswith("re:"):
                if re.search(pat[3:], name, flags=re.IGNORECASE):
                    return _to_region_type(value)
            else:
                if pat.lower() in lower:
                    return _to_region_type(value)

    if "mag" in lower or "pm" in lower or "magnet" in lower:
        return RegionType.magnet
    if "stator" in lower:
        return RegionType.stator
    if "rotor" in lower:
        return RegionType.rotor
    if "airgap" in lower or "air_gap" in lower:
        return RegionType.airgap
    if "shaft" in lower:
        return RegionType.shaft
    if "housing" in lower:
        return RegionType.housing

    return getattr(RegionType, default)


def dxf_to_regions(
    dxf_path: str,
    *,
    by_layer: bool = True,
    include_layers: list[str] | tuple[str, ...] | None = None,
    include_entity_types: list[str] | tuple[str, ...] = ("LWPOLYLINE", "POLYLINE", "LINE", "ARC"),
    fit_polylines: bool = True,
    line_tolerance: float = 1e-4,
    arc_tolerance: float = 1e-4,
    default_region_type: str = "dxf_import",
    layer_region_type_map: dict[str, object] | None = None,
    layer_region_type_patterns: dict[str, object] | None = None,
    name_prefix: str = "DXF",
    group_strategy: str = "entity",
    stitch: bool = False,
    stitch_tol: float = 1e-4,
    stitch_by_layer: bool = True,
):
    from ansys.motorcad.core.geometry import Region

    if stitch:
        ir = dxf_to_ir(
            dxf_path,
            include_layers=include_layers,
            include_entity_types=include_entity_types,
            stitch=True,
            stitch_tol=float(stitch_tol),
            stitch_by_layer=bool(stitch_by_layer),
            estimate_periodicity=True,
        )
        return ir_to_motorcad_regions(
            ir,
            default_region_type=default_region_type,
            layer_region_type_map=layer_region_type_map,
            layer_region_type_patterns=layer_region_type_patterns,
            name_prefix=name_prefix,
        )

    entitylists_by_group = dxf_to_entitylists(
        dxf_path,
        by_layer=by_layer,
        include_layers=include_layers,
        include_entity_types=include_entity_types,
        fit_polylines=fit_polylines,
        line_tolerance=line_tolerance,
        arc_tolerance=arc_tolerance,
        group_strategy=group_strategy,
    )

    regions = []
    for group, lists in entitylists_by_group.items():
        for i, ent in enumerate(lists):
            if layer_region_type_map and group in layer_region_type_map:
                region_type = layer_region_type_map[group]
            else:
                region_type = infer_region_type_from_layer_name(
                    group,
                    default=default_region_type,
                    mapping=layer_region_type_patterns,
                )

            r = Region(region_type=region_type)
            r.name = f"{name_prefix}_{group}_{i}" if group else f"{name_prefix}_{i}"
            r.entities = ent
            regions.append(r)

    return regions


def regions_summary_df(
    regions: list,
    *,
    sort_by: str | None = "area",
    ascending: bool = False,
):
    """Summarize Region objects (name/type/area/centroid) into a pandas DataFrame."""

    import pandas as pd

    def _region_type_str(r):
        rt = getattr(r, "region_type", None)
        return getattr(rt, "name", None) or getattr(rt, "value", None) or ("" if rt is None else str(rt))

    def _coord_xy(coord):
        if coord is None:
            return None, None
        return getattr(coord, "x", None), getattr(coord, "y", None)

    rows = []
    for i, r in enumerate(regions or []):
        name = getattr(r, "name", "")
        rt = _region_type_str(r)

        try:
            is_closed = bool(getattr(r, "is_closed"))
        except Exception:
            is_closed = None

        try:
            area = getattr(r, "area")
        except Exception:
            area = None

        try:
            centroid = getattr(r, "centroid")
        except Exception:
            centroid = None

        cx, cy = _coord_xy(centroid)

        try:
            entity_count = len(getattr(r, "entities", []) or [])
        except Exception:
            entity_count = None

        rows.append(
            {
                "idx": i,
                "name": name,
                "region_type": rt,
                "is_closed": is_closed,
                "area": area,
                "centroid_x": cx,
                "centroid_y": cy,
                "n_entities": entity_count,
            }
        )

    df = pd.DataFrame(rows)
    if sort_by and sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=bool(ascending), na_position="last").reset_index(drop=True)
    return df


def interactive_regions_viewer(
    regions: list,
    *,
    label_regions: bool = True,
    full_geometry: bool = False,
    legend: bool | None = None,
    title: str | None = None,
):
    """Interactively view all regions or a selected region (Jupyter)."""

    try:
        import ipywidgets as widgets
        from IPython.display import display
    except Exception as e:
        raise ImportError("interactive_regions_viewer requires ipywidgets") from e

    from ansys.motorcad.core.geometry_drawing import draw_objects

    regions = list(regions or [])
    options = [(f"[{i}] {getattr(r, 'name', '')}", i) for i, r in enumerate(regions)]
    if not options:
        raise ValueError("regions is empty")

    dropdown = widgets.Dropdown(options=options, description="Region")
    show_mode = widgets.ToggleButtons(
        options=[("All", "all"), ("Selected", "one")],
        value="one",
        description="Show",
    )

    def _draw(*_):
        if show_mode.value == "all":
            objects = regions
            t = title or "All regions"
        else:
            objects = [regions[int(dropdown.value)]]
            t = title or f"Region {dropdown.value}: {getattr(objects[0], 'name', '')}"

        draw_objects(
            objects,
            label_regions=label_regions,
            full_geometry=full_geometry,
            legend=legend,
            title=t,
        )

    ui = widgets.HBox([show_mode, dropdown])
    out = widgets.Output()

    def _refresh(*_, _source: str | None = None):
        # Important perf guard:
        # - When showing "All", changing the dropdown should NOT redraw everything.
        if _source == "dropdown" and show_mode.value != "one":
            return
        with out:
            out.clear_output(wait=True)
            _draw()

    dropdown.observe(lambda *_: _refresh(_source="dropdown"), names="value")
    show_mode.observe(lambda *_: _refresh(_source="mode"), names="value")

    display(ui, out)
    _refresh()
    return {"ui": ui, "out": out, "dropdown": dropdown, "mode": show_mode}


def get_dxf_layer_summary(dxf_path: str):
    """Summarize a DXF by layer and entity type."""

    import pandas as pd
    import ezdxf

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    rows: list[dict] = []
    for e in msp:
        try:
            layer = str(getattr(e.dxf, "layer", "0"))
        except Exception:
            layer = "0"
        try:
            etype = str(getattr(e, "dxftype", lambda: "UNKNOWN")())
        except Exception:
            etype = "UNKNOWN"
        rows.append({"layer": layer, "entity_type": etype})

    if not rows:
        return pd.DataFrame(columns=["layer", "entity_type", "count"])

    df = pd.DataFrame(rows)
    out = df.value_counts(["layer", "entity_type"]).rename("count").reset_index()
    return out.sort_values(["layer", "entity_type"]).reset_index(drop=True)


def guess_dxf_regions_from_layer_names(layer_names: list[str] | tuple[str, ...]):
    """Best-effort region grouping based on layer name keywords."""

    def norm(s: str) -> str:
        return str(s).strip().lower().replace(" ", "_")

    buckets: dict[str, list[str]] = {
        "rotor": [],
        "stator": [],
        "magnet": [],
        "winding": [],
        "slot": [],
        "shaft": [],
        "airgap": [],
        "housing": [],
        "other": [],
    }

    for ln in layer_names:
        n = norm(ln)
        if any(k in n for k in ["rotor", "rot"]):
            buckets["rotor"].append(ln)
        elif any(k in n for k in ["stator", "stat", "yoke"]):
            buckets["stator"].append(ln)
        elif any(k in n for k in ["magnet", "pm", "mag"]):
            buckets["magnet"].append(ln)
        elif any(k in n for k in ["winding", "coil", "conductor", "wire"]):
            buckets["winding"].append(ln)
        elif "slot" in n:
            buckets["slot"].append(ln)
        elif "shaft" in n:
            buckets["shaft"].append(ln)
        elif any(k in n for k in ["airgap", "air_gap", "gap"]):
            buckets["airgap"].append(ln)
        elif any(k in n for k in ["housing", "case", "frame"]):
            buckets["housing"].append(ln)
        else:
            buckets["other"].append(ln)

    return {k: v for k, v in buckets.items() if v}


def get_dxf_region_layer_map(dxf_path: str):
    """Convenience: read DXF -> list layers -> guess region grouping."""

    import ezdxf

    doc = ezdxf.readfile(dxf_path)
    layer_names = [layer.dxf.name for layer in doc.layers]
    return guess_dxf_regions_from_layer_names(layer_names)


__all__ = [
    "force_black_white",
    "plot_dxf_black_white",
    "plot_dxf_layers_black_white",
    "dxf_to_entitylists",
    "dxf_entitylists_to_regions",
    "infer_region_type_from_layer_name",
    "dxf_to_regions",
    "regions_summary_df",
    "interactive_regions_viewer",
    "get_dxf_layer_summary",
    "guess_dxf_regions_from_layer_names",
    "get_dxf_region_layer_map",
]
