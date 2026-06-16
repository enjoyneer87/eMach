"""Magnetization current extraction from FEA mesh data.

Converts the ferromagnetic element data (Hx, Hy, Bx, By, μr) from
the quasi-static FEA (Motor-CAD Hybrid mode) into equivalent
magnetization line currents for the PEEC model.

Morisco eq. 11:
    i_mag,θ = (k_mag,θ)_z · |s_θ|

where k_mag,θ is the tangential component of the magnetization surface
current density at the boundary between iron and air/conductor regions.
    K_mag = M × n̂  → |K_mag| = ΔM_tangential

The magnetization is:
    M = B/μ₀ - H
    M = (μr - 1)·H   (equivalent)
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass


MU_0 = 4e-7 * np.pi


@dataclass
class MagnetizationCurrent:
    """Equivalent magnetization currents from FEA.

    Attributes:
        positions: (n, 2) edge midpoint positions [m]
        currents: (n,) complex current amplitudes [A]
        edge_normals: (n, 2) outward normal vectors at edges
        source_region: label of the iron region (for debugging)
    """
    positions: np.ndarray
    currents: np.ndarray
    edge_normals: np.ndarray
    source_region: str = ""


def compute_magnetization_field(
    bx: np.ndarray,
    by: np.ndarray,
    hx: np.ndarray,
    hy: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute magnetization M = B/μ₀ - H per element.

    Args:
        bx, by: B-field components [T]
        hx, hy: H-field components [A/m]

    Returns:
        (Mx, My) magnetization components [A/m]
    """
    mx = bx / MU_0 - hx
    my = by / MU_0 - hy
    return mx, my


def compute_magnetization_from_mur(
    hx: np.ndarray,
    hy: np.ndarray,
    mur: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute M = (μr - 1)·H.

    Equivalent to M = B/μ₀ - H when B = μ₀·μr·H.
    """
    mx = (mur - 1.0) * hx
    my = (mur - 1.0) * hy
    return mx, my


@dataclass
class BoundaryEdgeCache:
    """Precomputed boundary edge geometry (constant across time steps).

    Use precompute_boundary_edges() to create, then pass to
    extract_magnetization_currents_fast() for each time step.
    """
    edge_midpoints: np.ndarray    # (n_edges, 2)
    edge_normals: np.ndarray      # (n_edges, 2)
    edge_lengths: np.ndarray      # (n_edges,)
    iron_tri_indices: np.ndarray  # (n_edges,) element index of adjacent iron tri


def _find_boundary_edges(
    node_xy: np.ndarray,
    triangles: np.ndarray,
    iron_mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Find edges at the boundary between iron and non-iron regions.

    An edge is a boundary edge if it belongs to exactly one iron triangle
    (or if one adjacent triangle is iron and the other is not).

    Args:
        node_xy: (n_nodes, 2) node coordinates
        triangles: (n_elem, 3) triangle connectivity (node indices)
        iron_mask: (n_elem,) bool — True if element is ferromagnetic

    Returns:
        edge_midpoints: (n_edges, 2) midpoint positions
        edge_normals: (n_edges, 2) outward unit normal (from iron toward air)
        edge_lengths: (n_edges,) edge lengths
        iron_tri_indices: (n_edges,) iron element index adjacent to each edge
    """
    # Build edge→triangle adjacency
    edge_to_tris: dict[tuple[int, int], list[int]] = {}
    for ti, tri in enumerate(triangles):
        for i in range(3):
            n0 = int(tri[i])
            n1 = int(tri[(i + 1) % 3])
            edge_key = (min(n0, n1), max(n0, n1))
            if edge_key not in edge_to_tris:
                edge_to_tris[edge_key] = []
            edge_to_tris[edge_key].append(ti)

    boundary_edges = []
    normals = []
    lengths = []
    iron_tri_ids = []

    for (n0, n1), tris in edge_to_tris.items():
        # Boundary edge: one iron, one non-iron (or single iron at domain boundary)
        iron_count = sum(1 for t in tris if iron_mask[t])
        if iron_count == 0 or iron_count == len(tris):
            continue  # both sides same type → not a boundary

        p0 = node_xy[n0]
        p1 = node_xy[n1]
        midpoint = 0.5 * (p0 + p1)
        edge_vec = p1 - p0
        edge_len = np.linalg.norm(edge_vec)
        if edge_len < 1e-15:
            continue

        # Normal: perpendicular to edge, pointing outward from iron
        normal = np.array([-edge_vec[1], edge_vec[0]]) / edge_len

        # Ensure normal points from iron to non-iron
        iron_tri_idx = next(t for t in tris if iron_mask[t])
        tri_nodes = triangles[iron_tri_idx]
        tri_centroid = np.mean(node_xy[tri_nodes], axis=0)
        if np.dot(normal, midpoint - tri_centroid) < 0:
            normal = -normal

        boundary_edges.append(midpoint)
        normals.append(normal)
        lengths.append(edge_len)
        iron_tri_ids.append(iron_tri_idx)

    return (
        np.array(boundary_edges) if boundary_edges else np.zeros((0, 2)),
        np.array(normals) if normals else np.zeros((0, 2)),
        np.array(lengths) if lengths else np.zeros(0),
        np.array(iron_tri_ids, dtype=int) if iron_tri_ids else np.zeros(0, dtype=int),
    )


def precompute_boundary_edges(
    node_xy: np.ndarray,
    triangles: np.ndarray,
    iron_mask: np.ndarray,
) -> BoundaryEdgeCache:
    """Precompute boundary edge geometry for repeated time-step calls.

    Call once, then use extract_magnetization_currents_fast() per step.
    Eliminates the O(n²) nearest-neighbor search entirely.
    """
    midpoints, normals, lengths, iron_ids = _find_boundary_edges(
        node_xy, triangles, iron_mask
    )
    return BoundaryEdgeCache(
        edge_midpoints=midpoints,
        edge_normals=normals,
        edge_lengths=lengths,
        iron_tri_indices=iron_ids,
    )


def extract_magnetization_currents(
    node_xy: np.ndarray,
    triangles: np.ndarray,
    bx: np.ndarray,
    by: np.ndarray,
    hx: np.ndarray,
    hy: np.ndarray,
    mur: np.ndarray,
    iron_mask: np.ndarray,
    axial_length: float = 1.0,
    region_label: str = "",
    boundary_cache: BoundaryEdgeCache | None = None,
) -> MagnetizationCurrent:
    """Extract equivalent magnetization currents at iron boundaries.

    The magnetization surface current density at the iron-air interface:
        K_mag = M × n̂  (tangential component)
    Integrated over the edge length gives the line current:
        i_mag = K_mag_tangential · edge_length

    Args:
        node_xy: (n_nodes, 2) mesh node coordinates [m]
        triangles: (n_elem, 3) element connectivity
        bx, by: (n_elem,) B-field per element [T]
        hx, hy: (n_elem,) H-field per element [A/m]
        mur: (n_elem,) relative permeability per element
        iron_mask: (n_elem,) bool array identifying ferromagnetic elements
        axial_length: stack length [m]
        region_label: descriptive label for the region
        boundary_cache: precomputed boundary edges (from precompute_boundary_edges).
            If provided, skips the expensive boundary search (100x faster for
            repeated calls on the same mesh).

    Returns:
        MagnetizationCurrent with positions and current values.
    """
    # Compute magnetization per element
    mx, my = compute_magnetization_field(bx, by, hx, hy)

    # Use cache or compute boundary edges
    if boundary_cache is not None:
        edge_midpoints = boundary_cache.edge_midpoints
        edge_normals = boundary_cache.edge_normals
        edge_lengths = boundary_cache.edge_lengths
        iron_tri_indices = boundary_cache.iron_tri_indices
    else:
        edge_midpoints, edge_normals, edge_lengths, iron_tri_indices = (
            _find_boundary_edges(node_xy, triangles, iron_mask)
        )

    if len(edge_midpoints) == 0:
        return MagnetizationCurrent(
            positions=np.zeros((0, 2)),
            currents=np.zeros(0, dtype=complex),
            edge_normals=np.zeros((0, 2)),
            source_region=region_label,
        )

    # Vectorized: use the known adjacent iron element (no search needed)
    # K_tangential = M_x·n_y - M_y·n_x  [A/m]
    k_tangential = (mx[iron_tri_indices] * edge_normals[:, 1]
                    - my[iron_tri_indices] * edge_normals[:, 0])
    currents = (k_tangential * edge_lengths).astype(complex)

    return MagnetizationCurrent(
        positions=edge_midpoints,
        currents=currents,
        edge_normals=edge_normals,
        source_region=region_label,
    )


def extract_magnetization_fundamental(
    node_xy: np.ndarray,
    triangles: np.ndarray,
    bx_timeseries: np.ndarray,
    by_timeseries: np.ndarray,
    hx_timeseries: np.ndarray,
    hy_timeseries: np.ndarray,
    iron_mask: np.ndarray,
    n_electrical_periods: int = 1,
    axial_length: float = 1.0,
    region_label: str = "",
) -> MagnetizationCurrent:
    """Extract FUNDAMENTAL HARMONIC of magnetization currents via DFT.

    Morisco 2019: Only the time-varying (AC) component of M at the
    electrical frequency contributes to AC winding losses. The DC
    component from permanent magnets does not cause eddy currents.

    This function:
    1. Computes M(t) at each boundary edge for all time steps
    2. Applies DFT to extract the fundamental harmonic amplitude
    3. Returns the complex phasor of magnetization current at f_e

    Args:
        node_xy: (n_nodes, 2) mesh node coordinates [m]
        triangles: (n_elem, 3) element connectivity
        bx_timeseries: (n_steps, n_elem) B_x per step [T]
        by_timeseries: (n_steps, n_elem) B_y per step [T]
        hx_timeseries: (n_steps, n_elem) H_x per step [A/m]
        hy_timeseries: (n_steps, n_elem) H_y per step [A/m]
        iron_mask: (n_elem,) bool array for ferromagnetic elements
        n_electrical_periods: number of electrical periods in data
        axial_length: stack length [m]
        region_label: descriptive label

    Returns:
        MagnetizationCurrent with fundamental-harmonic complex phasors.
    """
    n_steps = bx_timeseries.shape[0]

    # Find boundary edges (geometry is constant across time)
    edge_midpoints, edge_normals, edge_lengths, iron_tri_ids = _find_boundary_edges(
        node_xy, triangles, iron_mask
    )

    if len(edge_midpoints) == 0:
        return MagnetizationCurrent(
            positions=np.zeros((0, 2)),
            currents=np.zeros(0, dtype=complex),
            edge_normals=np.zeros((0, 2)),
            source_region=region_label,
        )

    # Find nearest iron element for each edge (once)
    iron_indices = np.where(iron_mask)[0]
    if len(iron_indices) == 0:
        return MagnetizationCurrent(
            positions=edge_midpoints,
            currents=np.zeros(len(edge_midpoints), dtype=complex),
            edge_normals=edge_normals,
            source_region=region_label,
        )

    # Use precomputed iron triangle indices (exact adjacency, no search)
    nearest_iron_global = iron_tri_ids

    # Compute magnetization current timeseries for each edge
    # i_mag(t) = (M_x·n_y - M_y·n_x) × edge_length
    n_edges = len(edge_midpoints)
    i_mag_t = np.zeros((n_steps, n_edges))

    for si in range(n_steps):
        mx_s = bx_timeseries[si] / MU_0 - hx_timeseries[si]
        my_s = by_timeseries[si] / MU_0 - hy_timeseries[si]

        # k_tangential for all edges at once
        k_tang = (mx_s[nearest_iron_global] * edge_normals[:, 1]
                  - my_s[nearest_iron_global] * edge_normals[:, 0])
        i_mag_t[si, :] = k_tang * edge_lengths

    # DFT to extract fundamental harmonic
    # Fundamental frequency index
    n_samples_per_period = n_steps // n_electrical_periods
    fund_index = n_electrical_periods  # k=1 per period × n_periods

    # Apply FFT along time axis
    I_fft = np.fft.fft(i_mag_t, axis=0)

    # Extract fundamental complex amplitude (2/N for single-sided)
    I_fundamental = (2.0 / n_steps) * I_fft[fund_index, :]

    return MagnetizationCurrent(
        positions=edge_midpoints,
        currents=I_fundamental.astype(complex),
        edge_normals=edge_normals,
        source_region=region_label,
    )
