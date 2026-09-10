"""Strict, non-extrapolating reader for the measured D4 magnetic loss maps."""
import bisect
import hashlib
import json
import math
from pathlib import Path

KEYS = ("fe_s", "fe_r", "pm")
CONDITION_KEYS = (
    "StatorIronLossBuildFactor", "RotorIronLossBuildFactor", "MagnetLossBuildFactor",
    "ArmatureConductor_Temperature", "Magnet_Temperature", "StatorLam_Temperature",
    "RotorLam_Temperature", "IronLossCalculationType", "OnLoadLossCalculation",
)


class MagneticLossMap:
    def __init__(self, paths, phase=36.0):
        self.rows = {}
        self.files = []
        self.conditions = None
        self.model_hash = None
        self.phase = float(phase)
        self.basis = None
        for path in paths:
            path = Path(path)
            raw = path.read_bytes()
            doc = json.loads(raw)
            if doc.get("_dry_run") is not False or doc.get("_gates_ok") is not True:
                raise ValueError("Incomplete, rejected or synthetic map: %s" % path)
            model_hash = doc.get("_mot_sha256")
            if not model_hash or (self.model_hash and model_hash != self.model_hash):
                raise ValueError("Model hashes missing or inconsistent")
            self.model_hash = model_hash
            expected = {(float(s), float(c)) for s in doc["_grid"]["speeds"]
                        for c in doc["_grid"]["currents"]}
            actual = [(float(p["speed"]), float(p["current"])) for p in doc["points"]]
            if set(actual) != expected or len(actual) != len(expected):
                raise ValueError("File grid is incomplete or duplicated")
            basis = doc.get("_loss_variables")
            if not basis or (self.basis and basis != self.basis):
                raise ValueError("Loss variable definitions missing or inconsistent")
            self.basis = basis
            for point in doc["points"]:
                speed, current = float(point["speed"]), float(point["current"])
                if not math.isfinite(speed) or not math.isfinite(current) or current < 0:
                    raise ValueError("Invalid operating point")
                if point["phase"] != self.phase or point["op_readback"] != {
                    "ShaftSpeed": speed, "RMSCurrent": current, "PhaseAdvance": self.phase
                }:
                    raise ValueError("Operating-point readback mismatch")
                context = {k: point["model_context"][k] for k in CONDITION_KEYS}
                context["DCBusVoltage"] = point["dc_bus_voltage_V"]
                if context["OnLoadLossCalculation"] is not True:
                    raise ValueError("On-load losses were not enabled")
                if self.conditions is not None and context != self.conditions:
                    raise ValueError("Model conditions differ between points")
                self.conditions = context
                values = {k: float(point["P_W"][k]) for k in KEYS}
                if not all(math.isfinite(v) and v >= 0 for v in values.values()):
                    raise ValueError("Nonfinite or negative magnetic loss")
                row = self.rows.setdefault(speed, {})
                if current in row:
                    raise ValueError("Duplicate speed/current point: %s" % ((speed, current),))
                row[current] = values
            self.files.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
        if not self.rows or any(len(row) < 2 for row in self.rows.values()):
            raise ValueError("At least two measured currents per speed are required")

    def bounds(self, speed):
        row = self.rows[float(speed)]
        return min(row), max(row)

    def at(self, speed, current, method="linear"):
        row = self.rows[float(speed)]
        current = float(current)
        knots = sorted(row)
        if not math.isfinite(current) or not knots[0] <= current <= knots[-1]:
            raise ValueError("Current %.6g outside measured range %s" % (current, self.bounds(speed)))
        if current in row:
            return dict(row[current])
        hi = bisect.bisect_right(knots, current)
        a, b = knots[hi - 1], knots[hi]
        if method == "linear":
            weight = (current - a) / (b - a)
        elif method == "linear_i2":
            weight = (current ** 2 - a ** 2) / (b ** 2 - a ** 2)
        else:
            raise ValueError("Unknown magnetic interpolation: " + method)
        return {key: (1 - weight) * row[a][key] + weight * row[b][key] for key in KEYS}

    def metadata(self, method):
        return {"files": self.files, "model_sha256": self.model_hash,
                "conditions": self.conditions, "loss_variables": self.basis,
                "interpolation": method, "extrapolation": "forbidden",
                "bounds_A": {str(int(s)): list(self.bounds(s)) for s in self.rows},
                "scope": "Conditional fixed-temperature, fixed-phase thermal study; voltage feasibility is not imposed."}
