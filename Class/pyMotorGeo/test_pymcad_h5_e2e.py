"""E2E test for pyMCAD-style H5 -> adapter mesh H5 -> VTU/clip workflow."""

from __future__ import annotations

from pathlib import Path
import tempfile

import numpy as np


def run_e2e_test() -> bool:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from motorcad_h5_adapter import (  # pylint: disable=import-error
        MotorH5Adapter,
        build_adapter_mesh_h5_from_pymcad_h5,
    )

    try:
        import h5py  # type: ignore
        import pyvista as pv
    except ImportError as exc:
        print(f"SKIP: missing dependency ({exc})")
        return True

    _ = pv.__version__

    with tempfile.TemporaryDirectory() as td:
        src_h5 = Path(td) / "pymcad_like.h5"
        mesh_h5 = Path(td) / "mesh_sample.h5"
        out_vtu = Path(td) / "mesh_sample.vtu"

        node_id = np.array([1, 2, 3, 4], dtype=np.int32)
        node_x = np.array([0.0, 1.0, 1.0, 0.0], dtype=np.float32)
        node_y = np.array([0.0, 0.0, 1.0, 1.0], dtype=np.float32)

        # 1-based connectivity in pyMCAD style.
        node_1 = np.array([1, 1], dtype=np.int32)
        node_2 = np.array([2, 3], dtype=np.int32)
        node_3 = np.array([3, 4], dtype=np.int32)

        bx = np.array([[0.1, 0.2]], dtype=np.float32)
        by = np.array([[0.3, 0.4]], dtype=np.float32)

        with h5py.File(src_h5, "w") as f:
            f.create_dataset("mesh/node_id", data=node_id)
            f.create_dataset("mesh/node_x_mm", data=node_x)
            f.create_dataset("mesh/node_y_mm", data=node_y)
            f.create_dataset("mesh/node_1", data=node_1)
            f.create_dataset("mesh/node_2", data=node_2)
            f.create_dataset("mesh/node_3", data=node_3)
            f.create_dataset("fields/bx", data=bx)
            f.create_dataset("fields/by", data=by)

        build_adapter_mesh_h5_from_pymcad_h5(src_h5, mesh_h5, step_index=0)

        adp = MotorH5Adapter()
        adp.load_h5(mesh_h5)

        grid = adp.to_unstructured_grid(
            points_key="mesh/points",
            cells_key="mesh/connectivity",
        )
        assert grid.n_points == 4
        assert grid.n_cells == 2

        adp.add_cell_data("B_mag_cell", adp.datasets["fields/B_mag_cell"])
        clipped = adp.clip(normal="x", origin=(0.5, 0.0, 0.0), invert=False)
        assert clipped.n_points > 0

        saved = adp.save_vtu(out_vtu)
        assert saved.exists()

        print("PASS: pyMCAD H5 E2E test")
        return True


if __name__ == "__main__":
    ok = run_e2e_test()
    raise SystemExit(0 if ok else 1)
