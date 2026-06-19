import sys; sys.path.insert(0, r"d:\KangDH\EveryMotor")
from eMach.tools.motorCAD.pyMCAD.magnetic import get_magnetic_timeseries_from_file

fea_path = r"D:\KangDH\Thesis\e10\refModel\Hybrid_ACloss_Export\halfsc\Hybrid_halfsc_16000RPM.txt"
ts = get_magnetic_timeseries_from_file(fea_path, key="time_index", verbose=False)
s0 = ts[ts.steps[0]]
print("type:", type(s0).__name__)

# It's MagneticRegions - iterate regions
if hasattr(s0, 'regions'):
    regions = s0.regions if isinstance(s0.regions, dict) else {}
else:
    regions = {}
    for attr in dir(s0):
        if not attr.startswith("_"):
            val = getattr(s0, attr)
            if hasattr(val, '__iter__') and not callable(val):
                print(f"  attr {attr}: type={type(val).__name__}")

# Try direct access
print("Has node_xy:", hasattr(s0, 'node_xy'))
nxy = s0.node_xy
if nxy is not None:
    print(f"  node_xy shape: {nxy.shape}, range: x=[{nxy[:,0].min():.1f},{nxy[:,0].max():.1f}] mm")

# Check how notebook accesses elements
# It iterates regions
import inspect
print("\nMagneticRegions source attrs:")
for a in dir(s0):
    if not a.startswith("_") and not callable(getattr(s0, a, None)):
        print(f"  .{a} = {type(getattr(s0, a)).__name__}")

