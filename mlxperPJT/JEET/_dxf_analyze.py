"""DXF 슬롯 도면 분석: 도체 영역 식별 + Polygon 생성"""
import ezdxf
import numpy as np
from collections import defaultdict
from matplotlib.path import Path as MplPath

DXF_PATH = r"D:\KangDH\Thesis\e10\SLFEA_Half\e10Turn6V261SLFEA_Half_Slot.dxf"

doc = ezdxf.readfile(DXF_PATH)
msp = doc.modelspace()

# Collect all entities with endpoints
segments = []  # (layer_num, type, start_pt, end_pt, extra)
for e in msp:
    layer_num = int(e.dxf.layer.replace("_MotorCAD", "").replace("_", ""))
    if e.dxftype() == "LINE":
        s = (round(e.dxf.start.x, 6), round(e.dxf.start.y, 6))
        end = (round(e.dxf.end.x, 6), round(e.dxf.end.y, 6))
        segments.append((layer_num, "LINE", s, end, None))
    elif e.dxftype() == "ARC":
        c = (e.dxf.center.x, e.dxf.center.y)
        r = e.dxf.radius
        sa = e.dxf.start_angle
        ea = e.dxf.end_angle
        # Start/end points of arc
        sa_rad = np.radians(sa)
        ea_rad = np.radians(ea)
        s = (round(c[0] + r * np.cos(sa_rad), 6), round(c[1] + r * np.sin(sa_rad), 6))
        end = (round(c[0] + r * np.cos(ea_rad), 6), round(c[1] + r * np.sin(ea_rad), 6))
        segments.append((layer_num, "ARC", s, end, (c, r, sa, ea)))

print(f"Total segments: {len(segments)}")

# Build adjacency: find closed loops by connecting endpoints
# Tolerance for point matching
TOL = 0.01

def pts_close(p1, p2, tol=TOL):
    return abs(p1[0]-p2[0]) < tol and abs(p1[1]-p2[1]) < tol

# Group into connected chains
used = [False] * len(segments)
loops = []

for start_idx in range(len(segments)):
    if used[start_idx]:
        continue
    # Try to build a chain starting from this segment
    chain = [start_idx]
    used[start_idx] = True
    current_end = segments[start_idx][3]  # end point
    chain_start = segments[start_idx][2]  # start point
    
    # Try to extend chain
    changed = True
    while changed:
        changed = False
        for j in range(len(segments)):
            if used[j]:
                continue
            sj = segments[j][2]
            ej = segments[j][3]
            if pts_close(current_end, sj):
                chain.append(j)
                used[j] = True
                current_end = ej
                changed = True
                break
            elif pts_close(current_end, ej):
                chain.append(j)
                used[j] = True
                current_end = sj
                changed = True
                break
    
    # Check if closed
    is_closed = pts_close(current_end, chain_start)
    if is_closed and len(chain) >= 3:
        loops.append(chain)

print(f"\nClosed loops found: {len(loops)}")
print(f"{'Loop':>4} {'Segments':>8} {'Lines':>5} {'Arcs':>4} {'Area_approx':>12}")
print("-" * 50)

# For each loop, compute approximate area and classify
loop_info = []
for li, loop in enumerate(loops):
    n_lines = sum(1 for idx in loop if segments[idx][1] == "LINE")
    n_arcs = sum(1 for idx in loop if segments[idx][1] == "ARC")
    
    # Collect vertices for area estimation (using shoelace on LINE endpoints)
    vertices = []
    for idx in loop:
        vertices.append(segments[idx][2])
    vertices = np.array(vertices)
    
    # Shoelace area (approximate for arcs)
    n = len(vertices)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    area = abs(area) / 2.0
    
    # Bounding box
    xmin, xmax = vertices[:, 0].min(), vertices[:, 0].max()
    ymin, ymax = vertices[:, 1].min(), vertices[:, 1].max()
    bbox_w = xmax - xmin
    bbox_h = ymax - ymin
    
    loop_info.append({
        "idx": li, "n_seg": len(loop), "n_lines": n_lines, "n_arcs": n_arcs,
        "area": area, "bbox_w": bbox_w, "bbox_h": bbox_h,
        "cx": (xmin+xmax)/2, "cy": (ymin+ymax)/2,
        "r_center": np.sqrt(((xmin+xmax)/2)**2 + ((ymin+ymax)/2)**2),
    })
    
    print(f"{li:>4} {len(loop):>8} {n_lines:>5} {n_arcs:>4} {area:>12.3f} mm²  "
          f"bbox={bbox_w:.2f}x{bbox_h:.2f}  r={loop_info[-1]['r_center']:.1f}")

# Identify conductor-like regions: 
# - Area close to b_m * h_m (5.57 * 2.53 = 14.09 mm²)
# - Rectangular-ish (4 lines or 4 lines + arcs for rounding)
b_m_mm = 5.57
h_m_mm = 2.53
cond_area_nominal = b_m_mm * h_m_mm  # 14.09 mm²

print(f"\n\n{'='*60}")
print(f"Conductor identification (nominal area = {cond_area_nominal:.2f} mm²)")
print(f"{'='*60}")
print(f"Loops with area in range [8, 20] mm² (conductor candidates):")
conductors = [li for li in loop_info if 8 < li["area"] < 20]
for c in conductors:
    print(f"  Loop {c['idx']}: area={c['area']:.3f} mm², "
          f"bbox={c['bbox_w']:.2f}x{c['bbox_h']:.2f}, "
          f"segments={c['n_seg']} (L{c['n_lines']}/A{c['n_arcs']}), "
          f"r={c['r_center']:.1f}")

print(f"\nTotal conductor candidates: {len(conductors)}")
print(f"Mean area: {np.mean([c['area'] for c in conductors]):.3f} mm²" if conductors else "None found")

# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Generate proper polygons with arc discretization
# ─────────────────────────────────────────────────────────────────────────────
print("\n\n" + "="*60)
print("Phase 2: Generating conductor polygons (arc-discretized)")
print("="*60)

def arc_to_points(center, radius, start_angle_deg, end_angle_deg, n_pts=16):
    """Arc를 점들로 이산화 (CCW 방향)."""
    sa = np.radians(start_angle_deg)
    ea = np.radians(end_angle_deg)
    if ea < sa:
        ea += 2 * np.pi
    angles = np.linspace(sa, ea, n_pts)
    xs = center[0] + radius * np.cos(angles)
    ys = center[1] + radius * np.sin(angles)
    return list(zip(xs, ys))

# Rebuild loops with proper polygon vertices (arcs → polyline)
conductor_polygons = []  # list of (vertices_array, area, r_center)

for li_info in loop_info:
    li = li_info["idx"]
    if li_info["n_arcs"] == 0:
        continue  # Skip non-arc loops (slot boundary)
    if li_info["area"] < 8 or li_info["area"] > 20:
        continue
    
    loop_indices = loops[li]
    
    # Reconstruct ordered polygon by chaining segments
    ordered_pts = []
    chain = list(loop_indices)
    
    # Start from first segment
    first_seg = segments[chain[0]]
    current_end = first_seg[3]  # end point of first
    
    # Add first segment's points
    if first_seg[1] == "LINE":
        ordered_pts.append(first_seg[2])
    elif first_seg[1] == "ARC":
        c, r, sa, ea = first_seg[4]
        arc_pts = arc_to_points(c, r, sa, ea, 16)
        ordered_pts.extend(arc_pts[:-1])  # exclude last (= next start)
    
    remaining = chain[1:]
    while remaining:
        found = False
        for ri, idx in enumerate(remaining):
            seg = segments[idx]
            s_pt, e_pt = seg[2], seg[3]
            
            if pts_close(current_end, s_pt):
                # Forward direction
                if seg[1] == "LINE":
                    ordered_pts.append(s_pt)
                elif seg[1] == "ARC":
                    c, r, sa, ea = seg[4]
                    arc_pts = arc_to_points(c, r, sa, ea, 16)
                    ordered_pts.extend(arc_pts[:-1])
                current_end = e_pt
                remaining.pop(ri)
                found = True
                break
            elif pts_close(current_end, e_pt):
                # Reverse direction
                if seg[1] == "LINE":
                    ordered_pts.append(e_pt)
                elif seg[1] == "ARC":
                    c, r, sa, ea = seg[4]
                    # Reverse arc
                    arc_pts = arc_to_points(c, r, ea, sa + 360 if sa > ea else sa, 16)
                    arc_pts = list(reversed(arc_to_points(c, r, sa, ea, 16)))
                    ordered_pts.extend(arc_pts[:-1])
                current_end = s_pt
                remaining.pop(ri)
                found = True
                break
        if not found:
            break
    
    # Close polygon
    poly = np.array(ordered_pts)
    
    # Compute proper area via shoelface
    n = len(poly)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += poly[i, 0] * poly[j, 1]
        area -= poly[j, 0] * poly[i, 1]
    area = abs(area) / 2.0
    
    conductor_polygons.append({
        "vertices": poly,
        "area_mm2": area,
        "r_center": li_info["r_center"],
        "cx": poly[:, 0].mean(),
        "cy": poly[:, 1].mean(),
    })

print(f"\nConductor polygons generated: {len(conductor_polygons)}")
print(f"{'#':>3} {'Area[mm²]':>10} {'r_center':>10} {'cx':>8} {'cy':>8} {'n_pts':>6}")
print("-" * 55)
for i, cp in enumerate(conductor_polygons):
    print(f"{i:>3} {cp['area_mm2']:>10.3f} {cp['r_center']:>10.1f} "
          f"{cp['cx']:>8.2f} {cp['cy']:>8.2f} {len(cp['vertices']):>6}")

total_cond_area = sum(cp["area_mm2"] for cp in conductor_polygons)
print(f"\nTotal conductor area (DXF): {total_cond_area:.2f} mm²")
print(f"Expected (6 cond × 14.09): {6*14.09:.2f} mm²")
print(f"Ratio: {total_cond_area / (6*14.09):.3f}")

# Save polygons for notebook use
import pickle
pkl_path = r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\conductor_polygons_dxf.pkl"
with open(pkl_path, "wb") as f:
    pickle.dump(conductor_polygons, f)
print(f"\n✓ Saved: {pkl_path}")

# Quick point-in-polygon test
print("\n\nPhase 3: Point-in-polygon filter validation")
print("="*60)

# Separate inner (copper) vs outer (insulation) polygons
# Same centroid, different area → smaller = copper
# Group by r_center
from itertools import groupby
sorted_polys = sorted(conductor_polygons, key=lambda p: round(p["r_center"], 0))
copper_polygons = []
insulation_polygons = []

radial_groups = {}
for cp in conductor_polygons:
    r_key = round(cp["r_center"], 0)
    if r_key not in radial_groups:
        radial_groups[r_key] = []
    radial_groups[r_key].append(cp)

for r_key, group in sorted(radial_groups.items()):
    if len(group) == 2:
        # Smaller = copper, larger = insulation boundary
        group.sort(key=lambda p: p["area_mm2"])
        copper_polygons.append(group[0])
        insulation_polygons.append(group[1])
    else:
        # Only one → assume copper
        copper_polygons.append(group[0])

print(f"Copper polygons (inner): {len(copper_polygons)}")
print(f"Insulation polygons (outer): {len(insulation_polygons)}")
copper_areas_str = [f"{cp['area_mm2']:.2f}" for cp in copper_polygons]
print(f"Copper areas: {copper_areas_str}")
print(f"Mean copper area: {np.mean([cp['area_mm2'] for cp in copper_polygons]):.3f} mm²")
print(f"  vs nominal (5.57×2.53): {5.57*2.53:.2f} mm²")

# ─────────────────────────────────────────────────────────────────────────────
# Phase 4: Rotate copper polygons for all 6 slots in 1/8 model
# ─────────────────────────────────────────────────────────────────────────────
print("\n\n" + "="*60)
print("Phase 4: Rotate for 6 slots (1/8 periodic model)")
print("="*60)

SLOT_PITCH_DEG = 7.5  # 360/48
N_SLOTS_MODEL = 6

# The DXF slot center angle
# From centroids: cx~110-125, cy~7-8 → angle = arctan(cy/cx) ≈ 3.7° ≈ SLOT_PITCH/2
slot_center_angles = [SLOT_PITCH_DEG * i + SLOT_PITCH_DEG/2 for i in range(N_SLOTS_MODEL)]
# DXF is at slot 0 (angle ≈ 3.75°)
dxf_slot_angle = np.degrees(np.arctan2(copper_polygons[0]["cy"], copper_polygons[0]["cx"]))
print(f"DXF slot angle: {dxf_slot_angle:.2f}° (slot center = {SLOT_PITCH_DEG/2:.2f}°)")

def rotate_polygon(vertices, angle_deg):
    """Rotate polygon around origin by angle_deg."""
    theta = np.radians(angle_deg)
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    rot = np.array([[cos_t, -sin_t], [sin_t, cos_t]])
    return (rot @ vertices.T).T

# ── Mirror: DXF는 반시계(CCW), FEA mesh는 시계(CW) → y좌표 반전 ──
def mirror_y(vertices):
    """y좌표 반전 (x-axis mirror): CCW → CW 변환."""
    mirrored = vertices.copy()
    mirrored[:, 1] *= -1
    return mirrored

# Generate all conductor polygons for 6 slots (mirrored to match FEA mesh)
all_conductor_polygons = []
for slot_idx in range(N_SLOTS_MODEL):
    rotation_angle = -SLOT_PITCH_DEG * slot_idx  # CW rotation (negative angle)
    for cp in copper_polygons:
        # 1) Mirror across x-axis (CCW → CW)
        mirrored = mirror_y(cp["vertices"])
        # 2) Rotate to target slot position (CW direction)
        rotated_verts = rotate_polygon(mirrored, rotation_angle)
        all_conductor_polygons.append({
            "vertices": rotated_verts,
            "area_mm2": cp["area_mm2"],
            "slot_idx": slot_idx,
            "cx": rotated_verts[:, 0].mean(),
            "cy": rotated_verts[:, 1].mean(),
        })

print(f"Total conductor polygons for 6 slots: {len(all_conductor_polygons)}")
print(f"  = {len(copper_polygons)} conductors/slot × {N_SLOTS_MODEL} slots")
print(f"  Total copper area: {sum(cp['area_mm2'] for cp in all_conductor_polygons):.2f} mm²")
print(f"  Mirror: y → -y applied (DXF CCW → FEA CW)")
# Verify angle range
angles = [np.degrees(np.arctan2(cp['cy'], cp['cx'])) for cp in all_conductor_polygons]
print(f"  Angle range: [{min(angles):.1f}°, {max(angles):.1f}°]")

# Create matplotlib Path objects
all_cond_paths = [MplPath(cp["vertices"]) for cp in all_conductor_polygons]

# Save for notebook
import pickle
pkl_path = r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\conductor_polygons_dxf.pkl"
save_data = {
    "copper_polygons_1slot": copper_polygons,
    "insulation_polygons_1slot": insulation_polygons,
    "all_conductor_polygons_6slots": all_conductor_polygons,
    "slot_pitch_deg": SLOT_PITCH_DEG,
    "n_slots_model": N_SLOTS_MODEL,
    "dxf_path": DXF_PATH,
}
with open(pkl_path, "wb") as f:
    pickle.dump(save_data, f)
print(f"\n✓ Saved: {pkl_path}")

# Validation: check how many FEA mesh centroids fall inside copper
# (Will be done in the notebook with actual mesh data)
print("\n\nUsage in notebook:")
print("  import pickle")
print("  from matplotlib.path import Path as MplPath")
print("  with open('conductor_polygons_dxf.pkl', 'rb') as f:")
print("      dxf_data = pickle.load(f)")
print("  cond_paths = [MplPath(cp['vertices']) for cp in dxf_data['all_conductor_polygons_6slots']]")
print("  # Filter: element centroid inside ANY conductor polygon")
print("  is_copper = np.zeros(n_elem, dtype=bool)")
print("  pts = np.column_stack([cx, cy])")
print("  for path in cond_paths:")
print("      is_copper |= path.contains_points(pts)")


