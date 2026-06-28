import json
import os
from typing import List, Dict, Tuple, Optional

class AcLossJsonReader:
    @staticmethod
    def read(json_path: str, model_scale: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Reads simulation summary records from a JSON file and validates them.
        Returns:
            (records, error_code)
            Where:
                records: List of raw dictionaries representing each simulation record, or None if failed.
                error_code: String representation of the failure code (e.g. E-IO-001, E-IO-002), or None if successful.
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
        
        # Verify model scale keywords in backup_dir paths
        model_keywords = {
            'Ref':    ['refModel', 'ref'],
            'HalfSC': ['SLFEA_Half', 'HalfSC'],
            'SC':     ['SLFEA', 'SC']
        }
        kws = model_keywords.get(model_scale, [])
        non_matching_count = 0
        example_non_matching = None
        
        for p in records:
            backup_dir = p.get("backup_dir", "")
            if backup_dir and not any(kw in backup_dir for kw in kws):
                non_matching_count += 1
                if example_non_matching is None:
                    example_non_matching = backup_dir
                    
        if non_matching_count > 0:
            print(f"  [WARNING] {non_matching_count} records may not belong to the {model_scale} model!")
            print(f"  Example: {example_non_matching}")
        else:
            print(f"  [OK] Model scale check: verified all {len(records)} records belong to {model_scale}")

        return records, None
