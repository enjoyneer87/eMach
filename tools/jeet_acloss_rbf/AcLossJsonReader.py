import json
import os
from collections import Counter
from typing import List, Dict, Tuple, Optional

class AcLossJsonReader:

    @staticmethod
    def classify_backup_dir(backup_dir: str) -> Optional[str]:
        """
        Infers the motor model scale from a record's backup_dir path.
        Priority matters: 'SLFEA_Half' must be checked before 'SLFEA'
        (substring), and 'refModel' identifies the reference model.
        Returns 'Ref' | 'HalfSC' | 'SC' | None (undetermined).
        """
        if not backup_dir:
            return None
        b = backup_dir.replace('/', '\\')
        if 'SLFEA_Half' in b or 'HalfSC' in b:
            return 'HalfSC'
        if 'refModel' in b or 'ACLossCalcExport_Ref' in b:
            return 'Ref'
        if 'SLFEA' in b or 'ACLossCalcExport_SC' in b:
            return 'SC'
        return None

    @classmethod
    def detect_model_scale(cls, records: List[Dict]) -> Tuple[Optional[str], Counter]:
        """
        Classifies every record by backup_dir and returns
        (majority_scale, per-scale record counts).
        """
        tags = Counter(cls.classify_backup_dir(p.get("backup_dir", "")) for p in records)
        tags.pop(None, None)
        majority = tags.most_common(1)[0][0] if tags else None
        return majority, tags

    @classmethod
    def read(cls, json_path: str, model_scale: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Reads simulation summary records from a JSON file and validates them.
        The model scale of the file is auto-detected from the records'
        backup_dir paths (e.g. ...\\e10_6TSweep\\refModel\\... -> 'Ref') and
        compared against the requested model_scale.
        Returns:
            (records, error_code)
            Where:
                records: List of raw dictionaries representing each simulation record, or None if failed.
                error_code: String representation of the failure code, or None if successful.
                    E-IO-001: file not found
                    E-IO-002: JSON decode failed
                    E-IO-003: dataset belongs to a different model scale
                    E-IO-999: generic read failure
        """
        if not os.path.exists(json_path):
            return None, "E-IO-001"  # File not found

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError:
            return None, "E-IO-002"  # JSON decode failed
        except Exception:
            return None, "E-IO-999"  # Generic read failure

        records = raw_data.get('records', raw_data) if isinstance(raw_data, dict) else raw_data

        detected, tags = cls.detect_model_scale(records)
        if detected is None:
            print(f"  [WARNING] Could not infer model scale from backup_dir "
                  f"paths; proceeding as requested '{model_scale}'.")
        elif detected != model_scale:
            print(f"  [ERROR] Dataset model mismatch: requested '{model_scale}' "
                  f"but backup_dir indicates '{detected}' (counts: {dict(tags)})")
            return None, "E-IO-003"  # Wrong model dataset
        else:
            mixed = {k: v for k, v in tags.items() if k != detected}
            if mixed:
                print(f"  [WARNING] {sum(mixed.values())} of {len(records)} "
                      f"records look like other models: {mixed}")
            print(f"  [OK] Model scale check: backup_dir confirms all "
                  f"{len(records)} records belong to {detected}")

        return records, None
