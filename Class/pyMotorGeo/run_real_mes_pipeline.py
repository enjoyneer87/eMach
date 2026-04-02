"""Run real Motor-CAD mes pipeline.

Pipeline: txt/h5 -> standard mesh h5 -> vtu -> clip -> pyvista plot.

Usage example:
python Class/pyMotorGeo/run_real_mes_pipeline.py \
    --mot "F:/KDH/Thesis/JEET/e10/refModel/e10_UserRemesh.mot" \
    --mes "F:/KDH/Thesis/JEET/e10/refModel/e10_UserRemesh/FEResultsData/" \
                "OnLoadTorque_result_1.mes" \
    --out-dir "D:/KangDH/Emlab_emach/Class/pyMotorGeo/_tmp_real_mes"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from motorcad_h5_adapter import (
    MotorH5Adapter,
    build_adapter_mesh_h5_from_pymcad_h5,
)


DEFAULT_CONVERT_DIR_NAME = "converted_mesh"


def _find_existing_mag_h5(search_root: Path) -> Optional[Path]:
    candidates = sorted(
        search_root.rglob("*.h5"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        low = path.name.lower()
        if "mag" in low or "onloadtorque" in low:
            return path
    return candidates[0] if candidates else None


def _export_txt_h5_from_mot_mes(
    mot_path: Path,
    mes_path: Path,
    out_dir: Path,
) -> Path:
    import ansys.motorcad.core as pymotorcad

    from tools.motorCAD.pyMCAD.fea_workflow import process_fea_result_from_mes

    mc = pymotorcad.MotorCAD(open_new_instance=True)
    mc.set_variable("MessageDisplayState", 2)
    mc.load_from_file(str(mot_path))

    result = process_fea_result_from_mes(
        mc,
        mes_path=str(mes_path),
        plot_mode="none",
        out_dir=str(out_dir),
        first_step=1,
        final_step=45,
        export_magnetic_h5=True,
        include_magnetic_export=True,
        mag_h5_mesh_coords="static",
    )

    if result.mag_h5_path is None:
        raise RuntimeError(
            "mag_h5_path is None after process_fea_result_from_mes"
        )

    return Path(result.mag_h5_path)


def _build_standard_h5_from_loss_txt(
    loss_txt_path: Path,
    output_h5_path: Path,
    preferred_field: str = "Pt",
) -> Path:
    """Build adapter-ready mesh H5 from pyMCAD element-loss txt export."""
    import h5py  # type: ignore

    from tools.motorCAD.pyMCAD.loss import get_element_loss_fields_from_file

    fields = get_element_loss_fields_from_file(loss_txt_path, clean_up=False)
    if not fields:
        raise ValueError(f"No loss fields parsed from: {loss_txt_path}")

    if preferred_field in fields:
        main_name = preferred_field
    else:
        main_name = sorted(fields.keys())[0]

    main_field = fields[main_name]
    mesh = main_field.mesh
    if not mesh.node_xy or not mesh.elements:
        raise ValueError("Parsed loss mesh is empty")

    node_ids = sorted(mesh.node_xy.keys())
    node_pos = {int(nid): i for i, nid in enumerate(node_ids)}

    points = []
    for nid in node_ids:
        x_mm, y_mm = mesh.node_xy[int(nid)]
        points.append([float(x_mm), float(y_mm), 0.0])

    connectivity = []
    tri_index_order = []
    for el in mesh.elements:
        connectivity.append(
            [
                node_pos[int(el.node_1)],
                node_pos[int(el.node_2)],
                node_pos[int(el.node_3)],
            ]
        )
        tri_index_order.append(int(el.tri_index))

    output_h5_path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(output_h5_path, "w") as f:
        f.create_dataset("mesh/points", data=points)
        f.create_dataset("mesh/connectivity", data=connectivity)

        for name, field in fields.items():
            vals = [
                float(field.values_by_tri.get(ti, 0.0))
                for ti in tri_index_order
            ]
            f.create_dataset(f"fields/loss_{name}_cell", data=vals)

        # Reuse the same default scalar key used in plotting helper.
        default_vals = [
            float(main_field.values_by_tri.get(ti, 0.0))
            for ti in tri_index_order
        ]
        f.create_dataset("fields/B_mag_cell", data=default_vals)

    return output_h5_path


def _resolve_output_dir(
    mot_path: Path,
    out_dir: Optional[Path],
    convert_dir_name: str = DEFAULT_CONVERT_DIR_NAME,
) -> Path:
    """Resolve output dir under mot folder to prevent large repo artifacts."""
    base = mot_path.parent / str(convert_dir_name)

    if out_dir is None:
        return base

    if not out_dir.is_absolute():
        return base / out_dir

    try:
        out_dir.resolve().relative_to(mot_path.parent.resolve())
        return out_dir
    except ValueError:
        return base


def run_pipeline(
    mot_path: Path,
    mes_path: Path,
    out_dir: Optional[Path] = None,
    convert_dir_name: str = DEFAULT_CONVERT_DIR_NAME,
) -> dict:
    out_dir = _resolve_output_dir(
        mot_path=mot_path,
        out_dir=out_dir,
        convert_dir_name=convert_dir_name,
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    source_h5 = None
    loss_txt_path = None
    export_error = None

    try:
        import ansys.motorcad.core as pymotorcad

        from tools.motorCAD.pyMCAD.fea_workflow import (
            process_fea_result_from_mes,
        )

        mc = pymotorcad.MotorCAD(open_new_instance=True)
        mc.set_variable("MessageDisplayState", 2)
        mc.load_from_file(str(mot_path))
        fea_result = process_fea_result_from_mes(
            mc,
            mes_path=str(mes_path),
            plot_mode="none",
            out_dir=str(out_dir),
            first_step=1,
            final_step=45,
            export_magnetic_h5=True,
            include_magnetic_export=True,
            mag_h5_mesh_coords="static",
        )
        if fea_result.mag_h5_path:
            source_h5 = Path(fea_result.mag_h5_path)
        if fea_result.loss_export_path:
            loss_txt_path = Path(fea_result.loss_export_path)
    except Exception as exc:  # pragma: no cover
        export_error = str(exc)

    if source_h5 is None:
        source_h5 = _find_existing_mag_h5(mes_path.parent)

    standard_h5 = out_dir / "standard_mesh_sample.h5"
    vtu_path = out_dir / "standard_mesh_sample.vtu"
    clip_vtu_path = out_dir / "standard_mesh_sample_clip.vtu"
    png_path = out_dir / "standard_mesh_clip.png"

    if source_h5 is not None and source_h5.exists():
        build_adapter_mesh_h5_from_pymcad_h5(
            source_h5,
            standard_h5,
            step_index=0,
        )
    elif loss_txt_path is not None and loss_txt_path.exists():
        _build_standard_h5_from_loss_txt(loss_txt_path, standard_h5)
    else:
        raise FileNotFoundError(
            "No usable source H5 or loss txt found. "
            "Motor-CAD export failed and no fallback exists."
        )

    adp = MotorH5Adapter()
    adp.load_h5(standard_h5)
    adp.to_unstructured_grid(
        points_key="mesh/points",
        cells_key="mesh/connectivity",
    )

    if "fields/B_mag_cell" in adp.datasets:
        adp.add_cell_data("B_mag_cell", adp.datasets["fields/B_mag_cell"])

    adp.save_vtu(vtu_path)
    clipped = adp.clip(normal="x", origin=(0.0, 0.0, 0.0), invert=False)
    clipped.save(str(clip_vtu_path))

    try:
        import pyvista as pv

        plotter = pv.Plotter(off_screen=True)
        if "B_mag_cell" in clipped.cell_data:
            plotter.add_mesh(clipped, scalars="B_mag_cell", show_edges=True)
        else:
            plotter.add_mesh(clipped, color="lightgray", show_edges=True)
        plotter.show(screenshot=str(png_path), auto_close=True)
    except Exception:
        png_path = None

    result = {
        "mot_path": str(mot_path),
        "mes_path": str(mes_path),
        "output_dir": str(out_dir),
        "source_h5": str(source_h5) if source_h5 else None,
        "loss_txt_path": str(loss_txt_path) if loss_txt_path else None,
        "standard_h5": str(standard_h5),
        "vtu_path": str(vtu_path),
        "clip_vtu_path": str(clip_vtu_path),
        "clip_points": int(clipped.n_points),
        "clip_cells": int(clipped.n_cells),
        "plot_png": str(png_path) if png_path else None,
        "export_error": export_error,
    }

    out_json = out_dir / "run_real_mes_pipeline_result.json"
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run real mes->pyvista pipeline"
    )
    parser.add_argument("--mot", required=True)
    parser.add_argument("--mes", required=True)
    parser.add_argument("--out-dir", required=False, default=None)
    parser.add_argument(
        "--convert-dir-name",
        default=DEFAULT_CONVERT_DIR_NAME,
    )
    args = parser.parse_args()

    mot = Path(args.mot)
    mes = Path(args.mes)
    out_dir = Path(args.out_dir) if args.out_dir else None

    if not mot.exists():
        raise FileNotFoundError(mot)
    if not mes.exists():
        raise FileNotFoundError(mes)

    result = run_pipeline(
        mot_path=mot,
        mes_path=mes,
        out_dir=out_dir,
        convert_dir_name=str(args.convert_dir_name),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
