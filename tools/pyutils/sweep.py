from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


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
