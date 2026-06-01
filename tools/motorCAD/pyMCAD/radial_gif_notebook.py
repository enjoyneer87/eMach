import base64
from pathlib import Path
from typing import Sequence, Tuple

from IPython.display import HTML, display


def to_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/gif;base64,{encoded}"


def render_gifs_side_by_side_html(
    gif_titles: Sequence[str],
    gif_infos: Sequence[Tuple[Path, int, Tuple[int, int]]],
) -> str:
    cards = []
    for title, (gif_path, frame_count, frame_size) in zip(gif_titles, gif_infos):
        cards.append(
            f"""
            <div style='flex:1; min-width:320px;'>
                <div style='font-weight:600; margin-bottom:8px;'>{title}</div>
                <img src='{to_data_uri(gif_path)}' style='max-width:100%; height:auto; border:1px solid #ddd;' />
                <div style='font-size:12px; color:#666; margin-top:6px;'>
                    {gif_path.name} | {frame_count} frames | {frame_size[0]}x{frame_size[1]}
                </div>
            </div>
            """
        )
    return (
        "<div style='display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;'>"
        + "".join(cards)
        + "</div>"
    )


def display_gifs_side_by_side(
    gif_titles: Sequence[str],
    gif_infos: Sequence[Tuple[Path, int, Tuple[int, int]]],
) -> None:
    html = render_gifs_side_by_side_html(gif_titles, gif_infos)
    display(HTML(html))
