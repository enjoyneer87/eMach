from pathlib import Path
import re
from typing import Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageOps


def validate_settings(
    patterns: Sequence[str],
    output_gifs: Sequence[Path],
    gif_titles: Sequence[str],
    expected_count: Optional[int] = None,
) -> None:
    if expected_count is not None and len(patterns) != expected_count:
        raise ValueError(f"PATTERNS must contain exactly {expected_count} patterns.")
    if len(output_gifs) != len(patterns):
        raise ValueError("OUTPUT_GIFS must have same length as PATTERNS.")
    if len(gif_titles) != len(patterns):
        raise ValueError("GIF_TITLES must have same length as PATTERNS.")


def extract_design_index(path: Path) -> int:
    m = re.search(r"Design(\d+)", path.as_posix(), re.IGNORECASE)
    return int(m.group(1)) if m else 10**12


def in_design_range(path: Path, design_min: Optional[int], design_max: Optional[int]) -> bool:
    idx = extract_design_index(path)
    if design_min is not None and idx < design_min:
        return False
    if design_max is not None and idx > design_max:
        return False
    return True


def collect_png_files(
    base_dir: Path,
    pattern: str,
    design_min: Optional[int] = None,
    design_max: Optional[int] = None,
) -> List[Path]:
    files = [p for p in base_dir.rglob(pattern) if in_design_range(p, design_min, design_max)]
    return sorted(files, key=lambda p: (extract_design_index(p), p.name.lower()))


def collect_png_files_by_patterns(
    base_dir: Path,
    patterns: Sequence[str],
    design_min: Optional[int] = None,
    design_max: Optional[int] = None,
    preview_limit: int = 20,
) -> List[List[Path]]:
    if not base_dir.exists():
        raise FileNotFoundError(f"Base folder not found: {base_dir}")

    files_by_pattern: List[List[Path]] = []
    for pattern in patterns:
        png_files = collect_png_files(base_dir, pattern, design_min=design_min, design_max=design_max)
        print(f"[{pattern}] Found {len(png_files)} radial PNG files.")
        for p in png_files[:preview_limit]:
            print(" -", p)
        if not png_files:
            raise RuntimeError(f"No matching PNG files found for pattern: {pattern}")
        files_by_pattern.append(png_files)
    return files_by_pattern


def build_gif(
    png_files: Sequence[Path],
    output_gif: Path,
    duration_ms: int = 500,
    loop: int = 0,
    add_reverse: bool = False,
    resize_to: Optional[Tuple[int, int]] = None,
    background_color: Tuple[int, int, int] = (255, 255, 255),
) -> Tuple[int, Tuple[int, int]]:
    images = []
    for p in png_files:
        with Image.open(p) as src:
            images.append(src.convert("RGB"))

    # Resize if requested
    if resize_to is not None:
        images = [img.resize(resize_to, Image.Resampling.LANCZOS) for img in images]

    # Normalize size by padding to max width/height
    max_w = max(img.width for img in images)
    max_h = max(img.height for img in images)
    target_size = (max_w, max_h)

    norm_images = []
    for img in images:
        if img.size != target_size:
            img = ImageOps.pad(
                img,
                target_size,
                color=background_color,
                method=Image.Resampling.LANCZOS,
            )
        norm_images.append(img)

    if add_reverse and len(norm_images) > 1:
        sequence = norm_images + norm_images[-2:0:-1]
    else:
        sequence = norm_images

    output_gif.parent.mkdir(parents=True, exist_ok=True)
    sequence[0].save(
        output_gif,
        save_all=True,
        append_images=sequence[1:],
        duration=duration_ms,
        loop=loop,
        optimize=False,
    )

    # PIL 이미지 리소스 정리
    for img in images:
        img.close()
    for img in norm_images:
        if img not in images:
            img.close()

    return len(sequence), target_size


def build_gifs(
    png_files_by_pattern: Sequence[Sequence[Path]],
    output_gifs: Sequence[Path],
    duration_ms: int = 500,
    loop: int = 0,
    add_reverse: bool = False,
    resize_to: Optional[Tuple[int, int]] = None,
    background_color: Tuple[int, int, int] = (255, 255, 255),
) -> List[Tuple[Path, int, Tuple[int, int]]]:
    if len(png_files_by_pattern) != len(output_gifs):
        raise ValueError("png_files_by_pattern and output_gifs must have the same length.")

    gif_infos: List[Tuple[Path, int, Tuple[int, int]]] = []
    for png_files, output_gif in zip(png_files_by_pattern, output_gifs):
        frame_count, frame_size = build_gif(
            png_files=png_files,
            output_gif=output_gif,
            duration_ms=duration_ms,
            loop=loop,
            add_reverse=add_reverse,
            resize_to=resize_to,
            background_color=background_color,
        )
        gif_infos.append((output_gif, frame_count, frame_size))
    return gif_infos
