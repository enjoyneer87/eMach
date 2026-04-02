"""Motor-CAD H5 to PyVista adapter utilities.

This module is intentionally self-contained so that Month1 data-adapter work
can proceed independently from the DXF pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

try:
    import h5py  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    h5py = None

try:
    import pyvista as pv  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pv = None


CELLTYPE_BY_NODES = {
    3: 5,    # VTK_TRIANGLE
    4: 10,   # VTK_TETRA
    6: 13,   # VTK_WEDGE
    8: 12,   # VTK_HEXAHEDRON
}


@dataclass
class AdapterState:
    h5_path: Optional[Path] = None
    points_key: Optional[str] = None
    cells_key: Optional[str] = None


class MotorH5Adapter:
    """Adapter for converting Motor-CAD style H5 data into PyVista grids."""

    def __init__(self) -> None:
        self.datasets: Dict[str, np.ndarray] = {}
        self.state = AdapterState()
        self.grid = None

    def _require_h5py(self) -> None:
        if h5py is None:
            raise RuntimeError("h5py is required: pip install h5py")

    def _require_pyvista(self) -> None:
        if pv is None:
            raise RuntimeError("pyvista is required: pip install pyvista")

    def load_h5(self, h5_path: str | Path) -> Dict[str, np.ndarray]:
        """Load all numeric datasets from an H5 file into a flat dictionary."""
        self._require_h5py()

        path = Path(h5_path)
        if not path.exists():
            raise FileNotFoundError(path)

        out: Dict[str, np.ndarray] = {}

        def _visit(name: str, obj) -> None:
            if isinstance(obj, h5py.Dataset):
                try:
                    arr = np.asarray(obj[...])
                except (TypeError, ValueError, OSError):
                    return
                if arr.size > 0:
                    out[name] = arr

        with h5py.File(path, "r") as f:
            f.visititems(_visit)

        self.datasets = out
        self.state.h5_path = path
        return out

    def dataset_layout(self, max_rows: int = 200) -> List[str]:
        """Return a compact list of dataset paths, shapes, and dtypes."""
        if not self.datasets:
            return []

        rows: List[str] = []
        for key in sorted(self.datasets.keys()):
            arr = self.datasets[key]
            rows.append(
                f"{key} | shape={tuple(arr.shape)} | dtype={arr.dtype}"
            )

        return rows[:max_rows]

    def infer_points_key(self) -> str:
        """Infer a point-coordinate dataset key from loaded H5 datasets."""
        if not self.datasets:
            raise ValueError("No datasets loaded. Call load_h5 first.")

        ranked = []
        for key, arr in self.datasets.items():
            if arr.ndim != 2:
                continue
            if arr.shape[1] != 3:
                continue
            score = 0
            low = key.lower()
            if "point" in low:
                score += 3
            if "coord" in low:
                score += 3
            if "node" in low:
                score += 2
            if np.issubdtype(arr.dtype, np.floating):
                score += 2
            ranked.append((score, key))

        if not ranked:
            preview = "\n".join(self.dataset_layout(max_rows=30))
            raise KeyError(
                "No candidate point dataset (N,3) found. "
                "Use explicit points_key or inspect dataset_layout().\n"
                f"Known datasets:\n{preview}"
            )

        ranked.sort(reverse=True)
        self.state.points_key = ranked[0][1]
        return ranked[0][1]

    def infer_cells_key(self) -> str:
        """Infer element-connectivity dataset key from loaded H5 datasets."""
        if not self.datasets:
            raise ValueError("No datasets loaded. Call load_h5 first.")

        ranked = []
        for key, arr in self.datasets.items():
            if arr.ndim != 2:
                continue
            if arr.shape[1] < 3:
                continue
            score = 0
            low = key.lower()
            if "connect" in low:
                score += 4
            if "cell" in low:
                score += 3
            if "elem" in low:
                score += 3
            if "topo" in low:
                score += 2
            if np.issubdtype(arr.dtype, np.integer):
                score += 2
            ranked.append((score, key))

        if not ranked:
            preview = "\n".join(self.dataset_layout(max_rows=30))
            raise KeyError(
                "No candidate connectivity dataset (M,K) found. "
                "Use explicit cells_key or inspect dataset_layout().\n"
                f"Known datasets:\n{preview}"
            )

        ranked.sort(reverse=True)
        self.state.cells_key = ranked[0][1]
        return ranked[0][1]

    def to_unstructured_grid(
        self,
        points_key: Optional[str] = None,
        cells_key: Optional[str] = None,
    ):
        """Build a PyVista UnstructuredGrid from loaded datasets."""
        self._require_pyvista()

        p_key = points_key or self.state.points_key or self.infer_points_key()
        c_key = cells_key or self.state.cells_key or self.infer_cells_key()

        points = np.asarray(self.datasets[p_key], dtype=np.float64)
        conn = np.asarray(self.datasets[c_key], dtype=np.int64)

        if conn.min() == 1:
            # Some exports use 1-based indexing.
            conn = conn - 1

        n_per_cell = int(conn.shape[1])
        celltype = CELLTYPE_BY_NODES.get(n_per_cell)
        if celltype is None:
            raise ValueError(f"Unsupported cell size: {n_per_cell}")

        n_cells = int(conn.shape[0])
        cells = np.hstack(
            [
                np.full((n_cells, 1), n_per_cell, dtype=np.int64),
                conn,
            ]
        ).reshape(-1)
        celltypes = np.full(n_cells, celltype, dtype=np.uint8)

        self.grid = pv.UnstructuredGrid(cells, celltypes, points)
        self.state.points_key = p_key
        self.state.cells_key = c_key
        return self.grid

    def add_point_data(self, name: str, values: np.ndarray) -> None:
        """Attach point data to the current grid."""
        if self.grid is None:
            raise ValueError(
                "Grid not built. Call to_unstructured_grid first."
            )

        arr = np.asarray(values)
        if arr.shape[0] != self.grid.n_points:
            raise ValueError(
                "Point data length mismatch: "
                f"{arr.shape[0]} vs {self.grid.n_points}"
            )
        self.grid.point_data[name] = arr

    def add_cell_data(self, name: str, values: np.ndarray) -> None:
        """Attach cell data to the current grid."""
        if self.grid is None:
            raise ValueError(
                "Grid not built. Call to_unstructured_grid first."
            )

        arr = np.asarray(values)
        if arr.shape[0] != self.grid.n_cells:
            raise ValueError(
                "Cell data length mismatch: "
                f"{arr.shape[0]} vs {self.grid.n_cells}"
            )
        self.grid.cell_data[name] = arr

    def clip(self, normal: str = "x", origin=None, invert: bool = False):
        """Return clipped grid from current grid."""
        self._require_pyvista()
        if self.grid is None:
            raise ValueError(
                "Grid not built. Call to_unstructured_grid first."
            )

        return self.grid.clip(normal=normal, origin=origin, invert=invert)

    def save_vtu(self, output_path: str | Path) -> Path:
        """Save current grid as VTU file."""
        if self.grid is None:
            raise ValueError(
                "Grid not built. Call to_unstructured_grid first."
            )

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.grid.save(str(out))
        return out


def build_grid_from_h5(h5_path: str | Path):
    """Convenience helper: H5 -> UnstructuredGrid."""
    adapter = MotorH5Adapter()
    adapter.load_h5(h5_path)
    return adapter.to_unstructured_grid()


def inspect_h5_layout(h5_path: str | Path, max_rows: int = 200) -> List[str]:
    """Convenience helper: H5 -> dataset layout summary lines."""
    adapter = MotorH5Adapter()
    adapter.load_h5(h5_path)
    return adapter.dataset_layout(max_rows=max_rows)


def build_adapter_mesh_h5_from_pymcad_h5(
    source_h5_path: str | Path,
    output_h5_path: str | Path,
    step_index: int = 0,
) -> Path:
    """Convert pyMCAD magnetic H5 layout into adapter-friendly mesh H5.

    Expected pyMCAD datasets include:
    - mesh/node_id, mesh/node_x_mm, mesh/node_y_mm
    - mesh/node_1, mesh/node_2, mesh/node_3
    - optional fields/bx, fields/by, fields/b with shape [n_steps, n_elements]

    Output datasets are standardized as:
    - mesh/points: [n_nodes, 3] float64 (z=0)
    - mesh/connectivity: [n_elements, 3] int64 (0-based)
    - fields/B_mag_cell: [n_elements] float32 (if available)
    """
    if h5py is None:
        raise RuntimeError("h5py is required: pip install h5py")

    src = Path(source_h5_path)
    if not src.exists():
        raise FileNotFoundError(src)

    dst = Path(output_h5_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(src, "r") as fsrc:
        def _req(name: str) -> np.ndarray:
            if name not in fsrc:
                raise KeyError(f"Required dataset missing: {name}")
            return np.asarray(fsrc[name][...])

        node_id = np.asarray(_req("mesh/node_id"), dtype=np.int64)
        node_x = np.asarray(_req("mesh/node_x_mm"), dtype=np.float64)
        node_y = np.asarray(_req("mesh/node_y_mm"), dtype=np.float64)

        if node_id.ndim != 1 or node_x.ndim != 1 or node_y.ndim != 1:
            raise ValueError("mesh/node_id,node_x_mm,node_y_mm must be 1D")
        if not (node_id.size == node_x.size == node_y.size):
            raise ValueError("mesh/node_* size mismatch")

        points = np.column_stack(
            [
                node_x,
                node_y,
                np.zeros_like(node_x, dtype=np.float64),
            ]
        )

        n1 = np.asarray(_req("mesh/node_1"), dtype=np.int64)
        n2 = np.asarray(_req("mesh/node_2"), dtype=np.int64)
        n3 = np.asarray(_req("mesh/node_3"), dtype=np.int64)
        if not (n1.ndim == n2.ndim == n3.ndim == 1):
            raise ValueError("mesh/node_1,node_2,node_3 must be 1D")
        if not (n1.size == n2.size == n3.size):
            raise ValueError("mesh/node_1..3 size mismatch")

        node_pos = {int(nid): int(i) for i, nid in enumerate(node_id.tolist())}
        connectivity = np.empty((n1.size, 3), dtype=np.int64)
        for i in range(n1.size):
            try:
                connectivity[i, 0] = node_pos[int(n1[i])]
                connectivity[i, 1] = node_pos[int(n2[i])]
                connectivity[i, 2] = node_pos[int(n3[i])]
            except KeyError as exc:
                raise KeyError(
                    "Connectivity references unknown node id"
                ) from exc

        b_mag = None
        if "fields/b" in fsrc:
            b_all = np.asarray(fsrc["fields/b"][...], dtype=np.float32)
            if b_all.ndim == 2 and b_all.shape[1] == connectivity.shape[0]:
                b_mag = b_all[step_index]
        elif "fields/bx" in fsrc and "fields/by" in fsrc:
            bx_all = np.asarray(fsrc["fields/bx"][...], dtype=np.float32)
            by_all = np.asarray(fsrc["fields/by"][...], dtype=np.float32)
            if (
                bx_all.ndim == 2
                and by_all.ndim == 2
                and bx_all.shape == by_all.shape
                and bx_all.shape[1] == connectivity.shape[0]
            ):
                b_mag = np.sqrt(
                    bx_all[step_index] ** 2 + by_all[step_index] ** 2
                )

    with h5py.File(dst, "w") as fdst:
        fdst.create_dataset("mesh/points", data=points)
        fdst.create_dataset("mesh/connectivity", data=connectivity)
        if b_mag is not None:
            fdst.create_dataset("fields/B_mag_cell", data=b_mag)

    return dst
