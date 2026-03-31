"""
Interactive PUML flow dashboard (Plotly + Dash).

Features:
- Dark theme UI
- Glow-style highlighting for active edge/node
- Stage camera zoom by phase/time
- Time-axis filter (phase-based playback)
- Node click drilldown

Run:
    python puml_flow_dashboard.py \
        --workflow d:/KangDH/Emlab_emach/Class/pyMotorGeo_Workflow.puml \
        --dependency d:/KangDH/Emlab_emach/Class/pyMotorGeo_Dependencies.puml \
        --port 8057
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html


@dataclass
class Edge:
    src: str
    dst: str
    label: str
    phase: str
    idx: int


def _clean_line(line: str) -> str:
    line = line.strip()
    if "'" in line:
        line = line.split("'", 1)[0].strip()
    return line


def _short_name(name: str, max_len: int = 18) -> str:
    name = name.replace(".py", "")
    if len(name) <= max_len:
        return name
    out: List[str] = []
    cur = ""
    for chunk in re.split(r"([_/])", name):
        if len(cur) + len(chunk) > max_len and cur:
            out.append(cur)
            cur = chunk
        else:
            cur += chunk
    if cur:
        out.append(cur)
    return "<br>".join(out)


def parse_sequence(text: str) -> Tuple[List[str], List[Edge], List[str]]:
    nodes: List[str] = []
    aliases: Dict[str, str] = {}
    phases: List[str] = []
    edges: List[Edge] = []

    node_re = re.compile(r'^(actor|participant|database)\s+"([^"]+)"\s+as\s+([A-Za-z_][\w]*)$')
    node_simple_re = re.compile(r'^(actor|participant|database)\s+([A-Za-z_][\w]*)$')
    phase_re = re.compile(r'^==\s*(.+?)\s*==$')
    edge_re = re.compile(r'^([A-Za-z_][\w]*)\s*[-.]*>\s*([A-Za-z_][\w]*)\s*:\s*(.*)$')

    phase = "Uncategorized"
    idx = 0

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

        m = phase_re.match(line)
        if m:
            phase = m.group(1).strip()
            if phase not in phases:
                phases.append(phase)
            continue

        m = edge_re.match(line)
        if m:
            src_a, dst_a, label = m.group(1), m.group(2), m.group(3).strip()
            src = aliases.get(src_a, src_a)
            dst = aliases.get(dst_a, dst_a)
            if src not in nodes:
                nodes.append(src)
            if dst not in nodes:
                nodes.append(dst)
            if phase not in phases:
                phases.append(phase)
            idx += 1
            edges.append(Edge(src=src, dst=dst, label=label, phase=phase, idx=idx))

    if not phases:
        phases = ["Uncategorized"]

    return nodes, edges, phases


def parse_dependency(text: str) -> Tuple[List[str], List[Edge], List[str]]:
    nodes: List[str] = []
    edges: List[Edge] = []
    phases: List[str] = ["All"]

    obj_re = re.compile(r'^object\s+([A-Za-z_][\w]*)$')
    edge_re = re.compile(r'^([A-Za-z_][\w]*)\s*[-.]*>\s*([A-Za-z_][\w]*)(?:\s*:\s*(.*))?$')

    idx = 0
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
            idx += 1
            edges.append(Edge(src=src, dst=dst, label=label, phase="All", idx=idx))

    return nodes, edges, phases


def is_sequence_like(text: str) -> bool:
    return any(k in text for k in ("participant", "actor", "database"))


def make_dependency_layout(nodes: List[str]) -> Dict[str, Tuple[float, float]]:
    n = max(1, len(nodes))
    r = 1.0
    return {
        node: (r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n))
        for i, node in enumerate(nodes)
    }


def _to_serializable(nodes: List[str], edges: List[Edge], phases: List[str], mode: str) -> Dict:
    return {
        "mode": mode,
        "nodes": nodes,
        "phases": phases,
        "edges": [
            {
                "src": e.src,
                "dst": e.dst,
                "label": e.label,
                "phase": e.phase,
                "idx": e.idx,
            }
            for e in edges
        ],
    }


def build_figure(data: Dict, selected_phases: List[str], step: int, auto_zoom: bool = True, glow: bool = True) -> go.Figure:
    nodes: List[str] = data["nodes"]
    mode: str = data["mode"]
    edges = data["edges"]

    phase_set = set(selected_phases) if selected_phases else set(data["phases"])
    filtered = [e for e in edges if e["phase"] in phase_set]

    if not filtered:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", title="No edges in selected phase filter")
        return fig

    capped_step = max(1, min(step, len(filtered)))
    active_idx = capped_step - 1
    active = filtered[active_idx]

    fig = go.Figure()

    if mode == "sequence":
        x_map = {n: i for i, n in enumerate(nodes)}
        y_top = 0.0

        # Lifelines and nodes
        for n in nodes:
            x = x_map[n]
            fig.add_trace(
                go.Scatter(
                    x=[x, x],
                    y=[y_top, len(filtered) + 1],
                    mode="lines",
                    line=dict(color="rgba(160,160,160,0.35)", width=1, dash="dash"),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        nx = [x_map[n] for n in nodes]
        ny = [y_top for _ in nodes]
        labels = [_short_name(n) for n in nodes]

        if glow:
            fig.add_trace(
                go.Scatter(
                    x=nx,
                    y=ny,
                    mode="markers",
                    marker=dict(size=38, color="rgba(0,220,255,0.18)", line=dict(width=0)),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        fig.add_trace(
            go.Scatter(
                x=nx,
                y=ny,
                mode="markers+text",
                marker=dict(size=22, color="#1f2a3a", line=dict(color="#58a6ff", width=2)),
                text=labels,
                textposition="top center",
                textfont=dict(size=13, color="#E6EDF3"),
                customdata=nodes,
                hovertemplate="Node: %{customdata}<extra></extra>",
                showlegend=False,
            )
        )

        # Draw all selected edges
        for i, e in enumerate(filtered, start=1):
            x0, x1 = x_map[e["src"]], x_map[e["dst"]]
            y = float(i)
            color = "rgba(120,130,150,0.35)"
            width = 1.4

            if i <= capped_step:
                color = "rgba(110,220,255,0.55)"
                width = 2.0

            fig.add_trace(
                go.Scatter(
                    x=[x0, x1],
                    y=[y, y],
                    mode="lines",
                    line=dict(color=color, width=width),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            if i == capped_step:
                # Glow edge layers
                if glow:
                    for w, c in [
                        (13, "rgba(0, 255, 255, 0.12)"),
                        (8, "rgba(0, 255, 255, 0.22)"),
                    ]:
                        fig.add_trace(
                            go.Scatter(
                                x=[x0, x1],
                                y=[y, y],
                                mode="lines",
                                line=dict(color=c, width=w),
                                hoverinfo="skip",
                                showlegend=False,
                            )
                        )

                fig.add_annotation(
                    x=x1,
                    y=y,
                    ax=x0,
                    ay=y,
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1,
                    arrowwidth=3,
                    arrowcolor="#00E5FF",
                    text=e["label"] or "",
                    font=dict(color="#C9F7FF", size=11),
                    bgcolor="rgba(0,0,0,0.35)",
                    bordercolor="rgba(0,229,255,0.35)",
                )

        y_range = [len(filtered) + 1.2, -0.8]
        if auto_zoom:
            phase_of_active = active["phase"]
            phase_edges = [e for e in filtered if e["phase"] == phase_of_active]
            if phase_edges:
                start = phase_edges[0]["idx"]
                end = phase_edges[-1]["idx"]
                y_range = [min(len(filtered) + 1.2, end + 1.2), max(-0.8, start - 1.2)]

        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, range=y_range)
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b1220",
            plot_bgcolor="#0b1220",
            margin=dict(l=30, r=30, t=70, b=40),
            title=f"Call Flow - Step {capped_step}/{len(filtered)} | Phase: {active['phase']}",
            height=800,
        )

    else:
        pos = make_dependency_layout(nodes)

        # Base nodes
        nx = [pos[n][0] for n in nodes]
        ny = [pos[n][1] for n in nodes]

        if glow:
            fig.add_trace(
                go.Scatter(
                    x=nx,
                    y=ny,
                    mode="markers",
                    marker=dict(size=44, color="rgba(0,255,255,0.1)", line=dict(width=0)),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        # Edges up to step
        for i, e in enumerate(filtered, start=1):
            x0, y0 = pos[e["src"]]
            x1, y1 = pos[e["dst"]]
            col = "rgba(120,130,150,0.2)"
            width = 1.2
            if i <= capped_step:
                col = "rgba(110,220,255,0.45)"
                width = 2.0

            fig.add_trace(
                go.Scatter(
                    x=[x0, x1],
                    y=[y0, y1],
                    mode="lines",
                    line=dict(color=col, width=width),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            if i == capped_step:
                if glow:
                    for w, c in [
                        (14, "rgba(0,255,255,0.10)"),
                        (9, "rgba(0,255,255,0.18)"),
                    ]:
                        fig.add_trace(
                            go.Scatter(
                                x=[x0, x1],
                                y=[y0, y1],
                                mode="lines",
                                line=dict(color=c, width=w),
                                hoverinfo="skip",
                                showlegend=False,
                            )
                        )

                fig.add_annotation(
                    x=x1,
                    y=y1,
                    ax=x0,
                    ay=y0,
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1,
                    arrowwidth=3,
                    arrowcolor="#00E5FF",
                    text=active["label"] or "",
                    font=dict(color="#C9F7FF", size=10),
                    bgcolor="rgba(0,0,0,0.35)",
                    bordercolor="rgba(0,229,255,0.35)",
                )

        fig.add_trace(
            go.Scatter(
                x=nx,
                y=ny,
                mode="markers+text",
                marker=dict(size=24, color="#172336", line=dict(color="#58a6ff", width=2)),
                text=[_short_name(n, max_len=12) for n in nodes],
                textposition="middle center",
                textfont=dict(size=11, color="#E6EDF3"),
                customdata=nodes,
                hovertemplate="Node: %{customdata}<extra></extra>",
                showlegend=False,
            )
        )

        x_range = [-1.35, 1.35]
        y_range = [-1.35, 1.35]
        if auto_zoom:
            sx, sy = pos[active["src"]]
            dx, dy = pos[active["dst"]]
            cx, cy = (sx + dx) / 2.0, (sy + dy) / 2.0
            span = 0.75
            x_range = [cx - span, cx + span]
            y_range = [cy - span, cy + span]

        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, range=x_range)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, range=y_range)
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b1220",
            plot_bgcolor="#0b1220",
            margin=dict(l=20, r=20, t=70, b=40),
            title=f"Data Flow - Step {capped_step}/{len(filtered)}",
            height=850,
        )

    return fig


def node_drilldown(data: Dict, node: str) -> str:
    edges = data["edges"]
    incoming = [e for e in edges if e["dst"] == node]
    outgoing = [e for e in edges if e["src"] == node]

    lines = [f"### Node: {node}", "", f"- Incoming: {len(incoming)}", f"- Outgoing: {len(outgoing)}", ""]

    if outgoing:
        lines.append("#### Outgoing Calls")
        for e in outgoing[:20]:
            tail = f" ({e['label']})" if e["label"] else ""
            lines.append(f"- [{e['phase']}] {e['src']} -> {e['dst']}{tail}")
        lines.append("")

    if incoming:
        lines.append("#### Incoming Calls")
        for e in incoming[:20]:
            tail = f" ({e['label']})" if e["label"] else ""
            lines.append(f"- [{e['phase']}] {e['src']} -> {e['dst']}{tail}")

    return "\n".join(lines)


def read_puml(path: Path, mode: str) -> Dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if mode == "auto":
        mode = "sequence" if is_sequence_like(text) else "dependency"

    if mode == "sequence":
        nodes, edges, phases = parse_sequence(text)
    else:
        nodes, edges, phases = parse_dependency(text)

    return _to_serializable(nodes, edges, phases, mode)


def make_app(workflow_path: Path, dependency_path: Path) -> Dash:
    app = Dash(__name__)

    workflow_data = read_puml(workflow_path, "sequence")
    dependency_data = read_puml(dependency_path, "dependency")

    app.layout = html.Div(
        style={"backgroundColor": "#070b14", "color": "#dce7f5", "minHeight": "100vh", "padding": "14px"},
        children=[
            html.H2("pyMotorGeo PUML Interactive Flow Dashboard", style={"margin": "8px 0 10px 0"}),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "12px"},
                children=[
                    html.Div(
                        style={"background": "#0b1220", "padding": "10px", "border": "1px solid #1e2b40", "borderRadius": "10px"},
                        children=[
                            html.Div(
                                style={"display": "flex", "gap": "10px", "alignItems": "center", "flexWrap": "wrap"},
                                children=[
                                    html.Label("Diagram:"),
                                    dcc.Dropdown(
                                        id="diagram-kind",
                                        options=[
                                            {"label": "Workflow (Call Flow)", "value": "workflow"},
                                            {"label": "Dependencies (Data Flow)", "value": "dependency"},
                                        ],
                                        value="workflow",
                                        clearable=False,
                                        style={"width": "280px", "color": "#111"},
                                    ),
                                    html.Label("Phase Filter:"),
                                    dcc.Dropdown(id="phase-filter", multi=True, style={"width": "420px", "color": "#111"}),
                                    html.Button("Play / Pause", id="play-toggle", n_clicks=0),
                                ],
                            ),
                            html.Div(
                                style={"display": "flex", "gap": "14px", "alignItems": "center", "marginTop": "8px"},
                                children=[
                                    html.Label("Step:"),
                                    dcc.Slider(id="step-slider", min=1, max=1, value=1, step=1, marks=None, tooltip={"always_visible": True}),
                                    dcc.Checklist(
                                        id="viz-options",
                                        options=[
                                            {"label": " Auto Zoom", "value": "zoom"},
                                            {"label": " Glow", "value": "glow"},
                                        ],
                                        value=["zoom", "glow"],
                                        inline=True,
                                    ),
                                ],
                            ),
                            dcc.Graph(id="flow-graph", style={"height": "82vh"}),
                            dcc.Interval(id="play-interval", interval=1000, n_intervals=0, disabled=True),
                        ],
                    ),
                    html.Div(
                        style={"background": "#0b1220", "padding": "10px", "border": "1px solid #1e2b40", "borderRadius": "10px"},
                        children=[
                            html.H4("Node Drilldown"),
                            dcc.Markdown(id="drilldown", style={"whiteSpace": "pre-wrap"}),
                        ],
                    ),
                ],
            ),
            dcc.Store(id="workflow-store", data=workflow_data),
            dcc.Store(id="dependency-store", data=dependency_data),
        ],
    )

    @app.callback(
        Output("phase-filter", "options"),
        Output("phase-filter", "value"),
        Input("diagram-kind", "value"),
        State("workflow-store", "data"),
        State("dependency-store", "data"),
    )
    def update_phase_options(kind: str, wf: Dict, dep: Dict):
        data = wf if kind == "workflow" else dep
        phases = data["phases"]
        options = [{"label": p, "value": p} for p in phases]
        return options, phases

    @app.callback(
        Output("step-slider", "max"),
        Output("step-slider", "value"),
        Input("diagram-kind", "value"),
        Input("phase-filter", "value"),
        State("workflow-store", "data"),
        State("dependency-store", "data"),
    )
    def update_step_range(kind: str, selected_phases: List[str], wf: Dict, dep: Dict):
        data = wf if kind == "workflow" else dep
        edges = data["edges"]
        if selected_phases:
            edges = [e for e in edges if e["phase"] in set(selected_phases)]
        total = max(1, len(edges))
        return total, 1

    @app.callback(
        Output("play-interval", "disabled"),
        Input("play-toggle", "n_clicks"),
    )
    def toggle_play(n_clicks: int):
        return n_clicks % 2 == 0

    @app.callback(
        Output("step-slider", "value", allow_duplicate=True),
        Input("play-interval", "n_intervals"),
        State("step-slider", "value"),
        State("step-slider", "max"),
        prevent_initial_call=True,
    )
    def play_tick(_n: int, val: int, maxv: int):
        if maxv <= 1:
            return 1
        nxt = (val or 1) + 1
        return 1 if nxt > maxv else nxt

    @app.callback(
        Output("flow-graph", "figure"),
        Input("diagram-kind", "value"),
        Input("phase-filter", "value"),
        Input("step-slider", "value"),
        Input("viz-options", "value"),
        State("workflow-store", "data"),
        State("dependency-store", "data"),
    )
    def render_graph(kind: str, selected_phases: List[str], step: int, opts: List[str], wf: Dict, dep: Dict):
        data = wf if kind == "workflow" else dep
        auto_zoom = "zoom" in (opts or [])
        glow = "glow" in (opts or [])
        return build_figure(data, selected_phases or data["phases"], step or 1, auto_zoom=auto_zoom, glow=glow)

    @app.callback(
        Output("drilldown", "children"),
        Input("flow-graph", "clickData"),
        Input("diagram-kind", "value"),
        State("workflow-store", "data"),
        State("dependency-store", "data"),
    )
    def update_drilldown(click_data: Dict, kind: str, wf: Dict, dep: Dict):
        data = wf if kind == "workflow" else dep
        if not click_data or "points" not in click_data or not click_data["points"]:
            return "노드를 클릭하면 호출/의존 관계를 상세 표시합니다."

        point = click_data["points"][0]
        node = point.get("customdata")
        if not node:
            return "노드 점(marker)을 클릭해 주세요."

        return node_drilldown(data, node)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive PUML flow dashboard")
    parser.add_argument("--workflow", required=True, help="Workflow .puml path")
    parser.add_argument("--dependency", required=True, help="Dependency .puml path")
    parser.add_argument("--host", default="127.0.0.1", help="Dash host")
    parser.add_argument("--port", type=int, default=8057, help="Dash port")
    args = parser.parse_args()

    app = make_app(Path(args.workflow), Path(args.dependency))
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
