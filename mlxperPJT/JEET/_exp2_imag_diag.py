"""EXP-2 Quick Diagnostic: i_mag magnitude check.
Load just a few time steps of FEA data, compute i_mag, check scale.
"""
import sys, os, time
sys.path.insert(0, r"d:\KangDH\EveryMotor")
import numpy as np

MU_0 = 4e-7 * np.pi

# --- Minimal TXT parsing (just 2 steps to check magnitude) ---
print("=== EXP-2: i_mag Magnitude Diagnostic ===")
print(f"Loading FEA data (first pass for mesh, then 2 steps)...")

from eMach.tools.motorCAD.pyMCAD.magnetic import get_magnetic_timeseries_from_file

t0 = time.perf_counter()
fea_path = r"D:\KangDH\Thesis\e10\refModel\Hybrid_ACloss_Export\halfsc\Hybrid_halfsc_16000RPM.txt"
ts = get_magnetic_timeseries_from_file(fea_path, key="time_index", verbose=False)
print(f"  Loaded in {time.perf_counter()-t0:.1f}s, {len(ts)} steps")

# Get mesh from first step
step_keys = ts.steps
step0 = ts[step_keys[0]]
node_xy = np.column_stack([
    np.array([n.x for n in step0.nodes]) * 1e-3,  # mm -> m
    np.array([n.y for n in step0.nodes]) * 1e-3,
])
n_nodes = len(step0.nodes)
n_elem = len(step0.elements)
print(f"  Mesh: {n_nodes} nodes, {n_elem} elements")

# Build triangles and iron mask
triangles = []
iron_mask = []
for el in step0.elements:
    triangles.append([el.node1, el.node2, el.node3])
    # iron if has permeability > 1
    mur = getattr(el, 'mur', 1.0) or 1.0
    iron_mask.append(mur > 1.5)

triangles = np.array(triangles)
iron_mask = np.array(iron_mask)
print(f"  Iron elements: {iron_mask.sum()} / {n_elem}")

# Precompute boundary edges
from eMach.tools.loss.ACLOSS.HYB.magnetization import precompute_boundary_edges
bc = precompute_boundary_edges(node_xy, triangles, iron_mask)
n_edges = len(bc.edge_midpoints)
print(f"  Boundary edges: {n_edges}")

# Compute i_mag for step 0
bx0 = np.array([getattr(el, 'bx', 0) or 0 for el in step0.elements])
by0 = np.array([getattr(el, 'by', 0) or 0 for el in step0.elements])
hx0 = np.array([getattr(el, 'hx', 0) or 0 for el in step0.elements])
hy0 = np.array([getattr(el, 'hy', 0) or 0 for el in step0.elements])

# M = B/mu0 - H
mx0 = bx0 / MU_0 - hx0
my0 = by0 / MU_0 - hy0

print(f"\n=== Step 0 Field Values ===")
print(f"  B range: Bx=[{bx0.min():.3f}, {bx0.max():.3f}] T, By=[{by0.min():.3f}, {by0.max():.3f}] T")
print(f"  H range: Hx=[{hx0.min():.0f}, {hx0.max():.0f}] A/m, Hy=[{hy0.min():.0f}, {hy0.max():.0f}] A/m")
print(f"  M range: Mx=[{mx0.min():.0f}, {mx0.max():.0f}] A/m, My=[{my0.min():.0f}, {my0.max():.0f}] A/m")

# Iron elements only
iron_idx = np.where(iron_mask)[0]
mx_iron = mx0[iron_idx]
my_iron = my0[iron_idx]
M_mag_iron = np.sqrt(mx_iron**2 + my_iron**2)
print(f"  |M| in iron: mean={M_mag_iron.mean():.0f}, max={M_mag_iron.max():.0f} A/m")
print(f"  |M|/mu0 check: mean |M|={M_mag_iron.mean():.0f} A/m -> |B_eq|={MU_0*M_mag_iron.mean():.4f} T")

# k_tangential at boundary edges
k_tang = (mx0[bc.iron_tri_indices] * bc.edge_normals[:, 1]
          - my0[bc.iron_tri_indices] * bc.edge_normals[:, 0])
i_mag_step0 = k_tang * bc.edge_lengths

print(f"\n=== i_mag (step 0) ===")
print(f"  K_tang: mean={np.abs(k_tang).mean():.0f}, max={np.abs(k_tang).max():.0f} A/m")
print(f"  edge_lengths: mean={bc.edge_lengths.mean()*1e3:.3f} mm, max={bc.edge_lengths.max()*1e3:.3f} mm")
print(f"  i_mag = K_tang * edge_len:")
print(f"    mean |i_mag| = {np.abs(i_mag_step0).mean():.4f} A")
print(f"    max  |i_mag| = {np.abs(i_mag_step0).max():.4f} A")
print(f"    RMS  i_mag   = {np.sqrt(np.mean(i_mag_step0**2)):.4f} A")

# What Morisco Fig 5.12 shows: ~0.01-0.6 A for his miniature motor
# Our motor is larger, so higher values expected, but 944A fundamental is suspicious
print(f"\n=== Morisco Fig 5.12 comparison ===")
print(f"  Morisco example: i_mag ~ 0.01-0.6 A (miniature motor, r0~5mm, l~100mm)")
print(f"  Our motor: 8P/48S IPM hairpin, R_stator~128mm, L_stack=150mm")
print(f"  Scaling ratio (by R): {128/5:.0f}x -> expected i_mag ~ {0.6*128/5:.0f} A max at boundary")
print(f"  Actual: {np.abs(i_mag_step0).max():.1f} A per edge (single step, not FFT)")

# Check if 1/mu0 factor is needed
print(f"\n=== 1/mu0 factor test ===")
k_tang_with_mu0 = k_tang / MU_0
i_mag_with_mu0 = k_tang_with_mu0 * bc.edge_lengths
print(f"  WITHOUT 1/mu0: max|i_mag| = {np.abs(i_mag_step0).max():.4f} A")
print(f"  WITH    1/mu0: max|i_mag| = {np.abs(i_mag_with_mu0).max():.1f} A")
print(f"  -> 1/mu0 would make it {np.abs(i_mag_with_mu0).max()/np.abs(i_mag_step0).max():.0f}x LARGER, not the fix")
