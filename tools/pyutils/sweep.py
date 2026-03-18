from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Dict, List, Optional, Tuple


def _linspace(start: float, stop: float, num: int, *, endpoint: bool = True) -> List[float]:
    if num <= 0:
        raise ValueError("num must be >= 1")
    if num == 1:
        return [float(stop if endpoint else start)]

    start = float(start)
    stop = float(stop)

    if endpoint:
        step = (stop - start) / (num - 1)
        return [start + i * step for i in range(num)]

    step = (stop - start) / num
    return [start + i * step for i in range(num)]


@dataclass(frozen=True)
class SweepPoint:
    ipeak_A: float
    phase_deg: float


def mkIpkPhaseMap(
    ipeak_steps: int,
    phase_steps: int,
    *,
    ipeak_min_A: float = 10.0,
    ipeak_max_A: float = 650.53,
    phase_min_deg: float = 0.0,
    phase_max_deg: float = 90.0,
    endpoint: bool = True,
    order: str = "ipeak-major",
) -> Tuple[List[float], List[float], List[SweepPoint]]:
    """Create Ipeak/phase step vectors and combined sweep points."""
    ipeaks = _linspace(ipeak_min_A, ipeak_max_A, int(ipeak_steps), endpoint=endpoint)
    phases = _linspace(phase_min_deg, phase_max_deg, int(phase_steps), endpoint=endpoint)

    points: List[SweepPoint] = []
    if order == "ipeak-major":
        for i in ipeaks:
            for ph in phases:
                points.append(SweepPoint(ipeak_A=float(i), phase_deg=float(ph)))
    elif order == "phase-major":
        for ph in phases:
            for i in ipeaks:
                points.append(SweepPoint(ipeak_A=float(i), phase_deg=float(ph)))
    else:
        raise ValueError("order must be 'ipeak-major' or 'phase-major'")

    return ipeaks, phases, points


def to_mcad_cases(
    sweep_points: List[SweepPoint],
    *,
    ipeak_key: str = "PeakCurrent",
    phase_key: str = "PhaseAdvance",
) -> List[dict[str, float]]:
    """Convert sweep points into Motor-CAD friendly input dictionaries."""
    return [{ipeak_key: pt.ipeak_A, phase_key: pt.phase_deg} for pt in sweep_points]


# ---------------------------------------------------------------------------
# Generic multi-axis DOE (geometry + electrical)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DOEAxis:
    """One sweep axis: Motor-CAD variable name, min, max, steps."""
    name: str
    min_val: float
    max_val: float
    steps: int
    endpoint: bool = True

    def values(self) -> List[float]:
        return _linspace(self.min_val, self.max_val, self.steps, endpoint=self.endpoint)


@dataclass(frozen=True)
class DOEPoint:
    """A single point in the full DOE grid (geometry + electrical)."""
    geometry: Dict[str, float]
    electrical: Dict[str, float]
    index: int = 0

    def as_mcad_dict(self) -> Dict[str, float]:
        """Merge geometry + electrical into one dict for set_mcad_variables."""
        d: Dict[str, float] = {}
        d.update(self.geometry)
        d.update(self.electrical)
        return d

    @property
    def tag(self) -> str:
        """Short string label (for directory / file naming)."""
        parts = []
        for k, v in self.geometry.items():
            parts.append(f"{k}={v:.4f}")
        for k, v in self.electrical.items():
            parts.append(f"{k}={v:.1f}")
        return "__".join(parts)


def build_doe_grid(
    geometry_axes: List[DOEAxis],
    electrical_axes: Optional[List[DOEAxis]] = None,
    sweep_points: Optional[List[SweepPoint]] = None,
    *,
    ipeak_key: str = "PeakCurrent",
    phase_key: str = "PhaseAdvance",
) -> List[DOEPoint]:
    """Build full-factorial DOE grid from geometry axes × electrical conditions.

    Electrical conditions can come from either *electrical_axes* (generic)
    or from an existing *sweep_points* list produced by ``mkIpkPhaseMap``.
    """
    # Build geometry grid
    geo_names = [ax.name for ax in geometry_axes]
    geo_vals = [ax.values() for ax in geometry_axes]
    geo_grid = [dict(zip(geo_names, combo)) for combo in product(*geo_vals)]

    # Build electrical grid
    if sweep_points is not None:
        elec_grid = [{ipeak_key: pt.ipeak_A, phase_key: pt.phase_deg} for pt in sweep_points]
    elif electrical_axes:
        elec_names = [ax.name for ax in electrical_axes]
        elec_vals = [ax.values() for ax in electrical_axes]
        elec_grid = [dict(zip(elec_names, combo)) for combo in product(*elec_vals)]
    else:
        elec_grid = [{}]

    points: List[DOEPoint] = []
    idx = 0
    for geo in geo_grid:
        for elec in elec_grid:
            points.append(DOEPoint(geometry=geo, electrical=elec, index=idx))
            idx += 1
    return points


# ---------------------------------------------------------------------------
# LHS-based DOE  (space-filling, much fewer points than full-factorial)
# ---------------------------------------------------------------------------

def _lhs_unit(n_samples: int, n_dims: int, *, seed: int = 42) -> "np.ndarray":
    """Classic Latin Hypercube in [0,1]^n_dims  (no scipy dependency).

    Returns shape ``(n_samples, n_dims)``.
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    result = np.empty((n_samples, n_dims), dtype=np.float64)
    for j in range(n_dims):
        perm = rng.permutation(n_samples)
        result[:, j] = (perm + rng.uniform(size=n_samples)) / n_samples
    return result


def build_doe_lhs(
    axes: List[DOEAxis],
    n_samples: int,
    *,
    seed: int = 42,
    criterion: str = "classic",
) -> List[DOEPoint]:
    """Build a Latin-Hypercube DOE over *all* axes (geometry + electrical combined).

    Each ``DOEAxis`` carries ``name``, ``min_val``, ``max_val``.
    (``steps`` is ignored here — ``n_samples`` controls total count.)

    Parameters
    ----------
    axes : list[DOEAxis]
        All dimensions to sample (geometry AND electrical together).
    n_samples : int
        Number of LHS sample points.
    seed : int
        Random seed for reproducibility.
    criterion : str
        ``"classic"`` — plain LHS (built-in, no extra deps).
        ``"maximin"`` — maximise minimum inter-point distance (``scipy`` required).
        ``"scipy"`` — use ``scipy.stats.qmc.LatinHypercube`` if available.

    Returns
    -------
    list[DOEPoint]
        Each point has ``geometry`` and ``electrical`` dicts.
        Geometry keys are those with "Ratio" / "Bore" / "Slot" / "Tooth" /
        "Magnet" / "Stator" / "Housing" in the name; everything else goes
        into ``electrical``.
    """
    import numpy as np

    n_dims = len(axes)
    if n_dims == 0:
        return []

    # --- generate unit hypercube samples ---
    if criterion == "scipy":
        from scipy.stats.qmc import LatinHypercube
        sampler = LatinHypercube(d=n_dims, seed=seed)
        unit = sampler.random(n=n_samples)
    elif criterion == "maximin":
        # generate many LHS candidates and keep the one with largest min-distance
        best, best_score = None, -1.0
        for trial_seed in range(seed, seed + max(20, n_samples)):
            cand = _lhs_unit(n_samples, n_dims, seed=trial_seed)
            dists = np.linalg.norm(cand[:, None, :] - cand[None, :, :], axis=-1)
            np.fill_diagonal(dists, np.inf)
            score = float(dists.min())
            if score > best_score:
                best, best_score = cand, score
        unit = best  # type: ignore[assignment]
    else:  # "classic"
        unit = _lhs_unit(n_samples, n_dims, seed=seed)

    # --- scale to physical ranges ---
    mins = np.array([ax.min_val for ax in axes], dtype=np.float64)
    maxs = np.array([ax.max_val for ax in axes], dtype=np.float64)
    samples = mins + unit * (maxs - mins)  # (n_samples, n_dims)

    # --- classify into geometry / electrical ---
    _GEO_KEYWORDS = {"ratio", "bore", "slot", "tooth", "magnet", "stator",
                      "housing", "shaft", "rotor", "pole", "airgap", "bridge",
                      "lam", "dia", "sleeve"}

    def _is_geometry(name: str) -> bool:
        low = name.lower()
        return any(kw in low for kw in _GEO_KEYWORDS)

    points: List[DOEPoint] = []
    for idx in range(n_samples):
        geo: Dict[str, float] = {}
        elec: Dict[str, float] = {}
        for j, ax in enumerate(axes):
            val = float(round(samples[idx, j], 6))
            if _is_geometry(ax.name):
                geo[ax.name] = val
            else:
                elec[ax.name] = val
        points.append(DOEPoint(geometry=geo, electrical=elec, index=idx))

    return points
