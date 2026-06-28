"""Temporary post-processing: divide hybrid loss fields by 1000 (W -> kW fix).

Motor-CAD returns Watts, but the worker stored them without /1000.0 conversion.
This script corrects all existing JSON summary files in-place.
"""
import json
from pathlib import Path

MAP_DIR = Path(__file__).parent / "map_exports"
TARGETS = [
    "JEET_ACLoss_Ref_Map_Summary.json",
    "JEET_ACLoss_HalfSC_Map_Summary.json",
    "JEET_ACLoss_SC_Map_Summary.json",
]
FIELDS = ["hybrid_total_kW", "hybrid_prox_kW", "hybrid_skin_kW"]

for fname in TARGETS:
    fpath = MAP_DIR / fname
    if not fpath.exists():
        print(f"[SKIP] {fname} not found")
        continue

    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for rec in data:
        if rec.get("proximity_model") == 1:
            for key in FIELDS:
                if key in rec:
                    rec[key] = rec[key] / 1000.0
            count += 1

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[DONE] {fname}: corrected {count} Hybrid records")
