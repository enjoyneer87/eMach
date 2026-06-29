import sys
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
EMACH_ROOT = SCRIPT_DIR.parent.parent.resolve()
sys.path.insert(0, str(EMACH_ROOT / "tools" / "varyToolCompatibility" / "toSyreFluxMap"))

import fromMCAD_lab_json as flj

mot_path = "D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn6V261.mot"
json_path = "D:\\KangDH\\EveryMotor\\eMach\\mlxperPJT\\JEET\\map_exports\\e10\\Ref\\JEET_ACLoss_Ref_Map_Summary.json"
out_mat = "D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn6V261_FluxMap_Py.mat"

print("Starting Python offline runner...")
result = flj.run_offline(
    mot_path=mot_path,
    json_path=json_path,
    out_mat=out_mat,
    p=4,
    plot=False
)
print("Successfully verified Python offline runner!")
