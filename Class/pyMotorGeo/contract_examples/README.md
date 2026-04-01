# Contract Examples

This folder stores contract example payloads used by the devplan.

## Files

- geometry_payload_v1.json: Geometry contract sample
- ml_dataset_payload_v1.json: SciML dataset contract sample

## Quick Validation Example

Use the validator in validation/ml_dataset_validator.py:

python
from contracts import load_payload_json
from validation.ml_dataset_validator import validate_ml_dataset_payload

payload = load_payload_json("contract_examples/ml_dataset_payload_v1.json")
ok, errors = validate_ml_dataset_payload(payload)
print(ok, errors)
