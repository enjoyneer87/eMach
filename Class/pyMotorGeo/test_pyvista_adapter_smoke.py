"""Smoke test for MotorH5Adapter.

This test uses a synthetic H5 file so it can run without proprietary data.
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import numpy as np

from motorcad_h5_adapter import MotorH5Adapter


def run_smoke_test() -> bool:
    try:
        import h5py  # type: ignore
        import pyvista as pv
    except ImportError as exc:
        print(f"SKIP: missing dependency ({exc})")
        return True

    _ = pv.__version__

    with tempfile.TemporaryDirectory() as td:
        h5_path = Path(td) / "synthetic.h5"
        out_vtu = Path(td) / "synthetic.vtu"

        points = np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [1.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [1.0, 0.0, 1.0],
                [1.0, 1.0, 1.0],
                [0.0, 1.0, 1.0],
            ],
            dtype=np.float64,
        )
        cells = np.array([[0, 1, 2, 3, 4, 5, 6, 7]], dtype=np.int64)

        with h5py.File(h5_path, "w") as f:
            f.create_dataset("mesh/points", data=points)
            f.create_dataset("mesh/connectivity", data=cells)
            f.create_dataset(
                "fields/B_mag", data=np.linspace(0.1, 0.8, len(points))
            )

        adp = MotorH5Adapter()
        adp.load_h5(h5_path)
        layout = adp.dataset_layout()
        assert any("mesh/points" in row for row in layout)
        grid = adp.to_unstructured_grid()

        assert grid.n_points == 8
        assert grid.n_cells == 1

        adp.add_point_data("B_mag", adp.datasets["fields/B_mag"])
        clipped = adp.clip(normal="z", origin=(0.0, 0.0, 0.5), invert=False)
        assert clipped.n_points > 0

        saved = adp.save_vtu(out_vtu)
        assert saved.exists()
        print("PASS: MotorH5Adapter smoke test")
        return True


if __name__ == "__main__":
    ok = run_smoke_test()
    raise SystemExit(0 if ok else 1)
