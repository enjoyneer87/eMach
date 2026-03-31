"""
PlantUML flow animator for pyMotorGeo documentation.

This script reads a PlantUML file and creates an animated GIF to make
call/data flow easier to understand.

Supported diagrams:
- Sequence-like flow (actor/participant/database + ordered arrows)
- Dependency/dataflow graph (object + arrows)

Example:
    python puml_flow_animator.py \
        --input d:/KangDH/Emlab_emach/Class/pyMotorGeo_Workflow.puml \
        --output d:/KangDH/Emlab_emach/Class/pyMotorGeo_Workflow.gif

    python puml_flow_animator.py \
        --input d:/KangDH/Emlab_emach/Class/pyMotorGeo_Dependencies.puml \
        --output d:/KangDH/Emlab_emach/Class/pyMotorGeo_Dependencies.gif
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter


@dataclass
class FlowEdge:
    src: str
    dst: str
    label: str = ""


def _format_node_label(name: str, max_chars: int = 16) -> str:
    """Make long node labels easier to read in static GIF frames."""
    text = name.replace(".py", "")
    text = text.replace(" / ", "\n/\n")
    text = text.replace(" ", "\n") if len(text) > max_chars and " / " not in name else text

    if len(text) <= max_chars:
        return text

    # Fallback wrap when separators are not enough.
    chunks: List[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + max_chars])
        start += max_chars
    return "\n".join(chunks)


def _clean_line(line: str) -> str:
    line = line.strip()
    if "'" in line:
        line = line.split("'", 1)[0].strip()
    return line


def parse_sequence_puml(text: str) -> Tuple[List[str], List[FlowEdge]]:
    nodes: List[str] = []
    aliases: Dict[str, str] = {}
    edges: List[FlowEdge] = []

    node_re = re.compile(r'^(actor|participant|database)\s+"([^"]+)"\s+as\s+([A-Za-z_][\w]*)$')
    node_simple_re = re.compile(r'^(actor|participant|database)\s+([A-Za-z_][\w]*)$')
    edge_re = re.compile(r'^([A-Za-z_][\w]*)\s*[-.]*>\s*([A-Za-z_][\w]*)\s*:\s*(.*)$')

    for raw in text.splitlines():
        line = _clean_line(raw)
        if not line:
            continue

        m = node_re.match(line)
        if m:
            display_name = m.group(2)
            alias = m.group(3)
            aliases[alias] = display_name
            if display_name not in nodes:
                nodes.append(display_name)
            continue

        m = node_simple_re.match(line)
        if m:
            alias = m.group(2)
            aliases[alias] = alias
            if alias not in nodes:
                nodes.append(alias)
            continue

        m = edge_re.match(line)
        if m:
            src_alias, dst_alias, label = m.group(1), m.group(2), m.group(3)
            src = aliases.get(src_alias, src_alias)
            dst = aliases.get(dst_alias, dst_alias)
            if src not in nodes:
                nodes.append(src)
            if dst not in nodes:
                nodes.append(dst)
            edges.append(FlowEdge(src=src, dst=dst, label=label.strip()))

    return nodes, edges


def parse_dependency_puml(text: str) -> Tuple[List[str], List[FlowEdge]]:
    nodes: List[str] = []
    edges: List[FlowEdge] = []

    obj_re = re.compile(r'^object\s+([A-Za-z_][\w]*)$')
    edge_re = re.compile(r'^([A-Za-z_][\w]*)\s*[-.]*>\s*([A-Za-z_][\w]*)(?:\s*:\s*(.*))?$')

    for raw in text.splitlines():
        line = _clean_line(raw)
        if not line:
            continue

        m = obj_re.match(line)
        if m:
            name = m.group(1)
            if name not in nodes:
                nodes.append(name)
            continue

        m = edge_re.match(line)
        if m:
            src, dst = m.group(1), m.group(2)
            label = (m.group(3) or "").strip()
            if src not in nodes:
                nodes.append(src)
            if dst not in nodes:
                nodes.append(dst)
            edges.append(FlowEdge(src=src, dst=dst, label=label))

    return nodes, edges


def is_sequence_like(text: str) -> bool:
    markers = ("participant", "actor", "database")
    return any(m in text for m in markers)


def animate_sequence(nodes: List[str], edges: List[FlowEdge], out_path: Path, fps: int = 2) -> None:
    if not nodes or not edges:
        raise ValueError("No nodes or edges parsed from PUML sequence.")

    fig_w = max(16, 2.0 * len(nodes))
    fig, ax = plt.subplots(figsize=(fig_w, 9))
    x_map = {name: i for i, name in enumerate(nodes)}
    y_top = 1
    y_bottom = len(edges) + 2
    node_font = 11 if len(nodes) <= 8 else 10 if len(nodes) <= 12 else 9

    def draw_base() -> None:
        ax.clear()
        ax.set_xlim(-0.5, len(nodes) - 0.5)
        ax.set_ylim(y_bottom + 1, 0)
        ax.axis("off")

        for name, x in x_map.items():
            ax.text(
                x,
                y_top - 0.45,
                _format_node_label(name),
                ha="center",
                va="center",
                fontsize=node_font,
                weight="bold",
                linespacing=1.1,
            )
            ax.plot([x, x], [y_top, y_bottom], color="#B0B0B0", linewidth=1, linestyle="--")

    def draw_edge(edge: FlowEdge, y: float, active: bool = False) -> None:
        x0 = x_map[edge.src]
        x1 = x_map[edge.dst]
        color = "#D62728" if active else "#4C78A8"
        lw = 2.8 if active else 1.6

        ax.annotate(
            "",
            xy=(x1, y),
            xytext=(x0, y),
            arrowprops=dict(arrowstyle="->", color=color, lw=lw, shrinkA=3, shrinkB=3),
        )
        if edge.label:
            ax.text((x0 + x1) / 2, y - 0.18, edge.label, ha="center", va="bottom", fontsize=9, color=color)

    def update(frame: int):
        draw_base()
        ax.set_title("Call Flow Animation", fontsize=16, weight="bold")

        for i, edge in enumerate(edges[: frame + 1], start=1):
            draw_edge(edge, y=i + 1, active=(i - 1 == frame))

        if 0 <= frame < len(edges):
            e = edges[frame]
            ax.text(
                0.5 * (len(nodes) - 1),
                y_bottom + 0.5,
                f"Step {frame + 1}/{len(edges)}: {e.src} -> {e.dst}",
                ha="center",
                va="center",
                fontsize=11,
                color="#333333",
            )

    ani = FuncAnimation(fig, update, frames=len(edges), interval=1000 / max(1, fps), repeat=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ani.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)


def _circle_layout(nodes: List[str], radius: float = 1.0) -> Dict[str, Tuple[float, float]]:
    n = len(nodes)
    return {
        node: (
            radius * math.cos(2 * math.pi * i / n),
            radius * math.sin(2 * math.pi * i / n),
        )
        for i, node in enumerate(nodes)
    }


def animate_dependency(nodes: List[str], edges: List[FlowEdge], out_path: Path, fps: int = 2) -> None:
    if not nodes or not edges:
        raise ValueError("No nodes or edges parsed from PUML dependency graph.")

    pos = _circle_layout(nodes, radius=1.0)
    fig_size = max(12, 0.6 * len(nodes))
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))

    def draw_base() -> None:
        ax.clear()
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)
        ax.axis("off")
        ax.set_title("Data Flow Animation", fontsize=16, weight="bold")

        for name, (x, y) in pos.items():
            ax.scatter([x], [y], s=900, color="#E8EEF7", edgecolors="#4C78A8", linewidths=1.5)
            ax.text(x, y, _format_node_label(name, max_chars=12), ha="center", va="center", fontsize=9, weight="bold")

    def draw_edge(edge: FlowEdge, active: bool = False) -> None:
        x0, y0 = pos[edge.src]
        x1, y1 = pos[edge.dst]
        color = "#D62728" if active else "#9AA0A6"
        lw = 2.5 if active else 1.2
        alpha = 1.0 if active else 0.45

        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(arrowstyle="->", color=color, lw=lw, alpha=alpha, shrinkA=18, shrinkB=18),
        )
        if active and edge.label:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, edge.label, fontsize=8, color=color)

    def update(frame: int):
        draw_base()
        for i, edge in enumerate(edges[: frame + 1]):
            draw_edge(edge, active=(i == frame))

        e = edges[frame]
        ax.text(0.0, -1.28, f"Step {frame + 1}/{len(edges)}: {e.src} -> {e.dst}", ha="center", va="center")

    ani = FuncAnimation(fig, update, frames=len(edges), interval=1000 / max(1, fps), repeat=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ani.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate PlantUML call/data flow to GIF")
    parser.add_argument("--input", required=True, help="Input .puml file path")
    parser.add_argument("--output", required=True, help="Output .gif file path")
    parser.add_argument(
        "--mode",
        choices=["auto", "sequence", "dependency"],
        default="auto",
        help="Animation mode",
    )
    parser.add_argument("--fps", type=int, default=2, help="Frames per second")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    text = in_path.read_text(encoding="utf-8", errors="ignore")

    mode = args.mode
    if mode == "auto":
        mode = "sequence" if is_sequence_like(text) else "dependency"

    if mode == "sequence":
        nodes, edges = parse_sequence_puml(text)
        animate_sequence(nodes, edges, out_path, fps=args.fps)
    else:
        nodes, edges = parse_dependency_puml(text)
        animate_dependency(nodes, edges, out_path, fps=args.fps)

    print(f"Saved animation: {out_path}")
    print(f"Mode: {mode}, nodes={len(nodes)}, edges={len(edges)}")


if __name__ == "__main__":
    main()
