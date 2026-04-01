from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Allow local imports when running this file directly.
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from pyleecan_subprocess_bridge import default_pyleecan_python, run_external_pyleecan_bridge


class PyleecanBundleRequest(BaseModel):
    source_name: str = Field(default="api_bundle.json")
    machine_name: str = Field(default="API_Motor")
    stack_length_mm: float = Field(default=100.0, ge=1.0)
    pyleecan_python: str | None = Field(default=None)
    timeout_sec: int = Field(default=240, ge=10, le=1200)
    dry_run: bool = Field(default=False)
    bundle: dict


app = FastAPI(
    title="pyMotorGeo FastAPI Inference Service",
    version="0.1.0",
    description=(
        "Non-ML inference API for pyMotorGeo. "
        "Uses JSON-only bundle input and runs pyleecan in external environment."
    ),
)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "pyMotorGeo-fastapi",
        "mode": "non-ml",
        "json_only": True,
    }


@app.post("/infer/pyleecan-bundle")
def infer_pyleecan_bundle(req: PyleecanBundleRequest) -> dict:
    if not isinstance(req.bundle, dict):
        raise HTTPException(status_code=400, detail="bundle must be a JSON object")

    bundle_keys = sorted(list(req.bundle.keys()))
    bundle_summary = {
        "top_level_key_count": len(bundle_keys),
        "top_level_keys": bundle_keys,
    }

    if req.dry_run:
        return {
            "ok": True,
            "mode": "dry-run",
            "json_only": True,
            "machine_name": req.machine_name,
            "stack_length_mm": float(req.stack_length_mm),
            "bundle_summary": bundle_summary,
        }

    tmp_bundle_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            tmp_file.write(json.dumps(req.bundle, ensure_ascii=False).encode("utf-8"))
            tmp_bundle_path = tmp_file.name

        result = run_external_pyleecan_bridge(
            input_path=tmp_bundle_path,
            input_type="json",
            source_name=req.source_name,
            machine_name=req.machine_name,
            stack_length_mm=float(req.stack_length_mm),
            pyleecan_python=req.pyleecan_python or default_pyleecan_python(),
            timeout_sec=int(req.timeout_sec),
        )

        if not result.get("ok"):
            raise HTTPException(
                status_code=500,
                detail={
                    "error": result.get("error", "pyleecan bridge failed"),
                    "returncode": result.get("returncode"),
                },
            )

        return {
            "ok": True,
            "mode": "external-pyleecan",
            "machine_class": result.get("machine_class"),
            "dims": result.get("dims"),
            "dims_summary": result.get("dims_summary"),
            "bundle": result.get("bundle"),
            "bundle_summary": bundle_summary,
            "pyleecan_version": result.get("pyleecan_version"),
            "pyleecan_module_path": result.get("pyleecan_module_path"),
            "python_executable": result.get("python_executable"),
        }
    finally:
        if tmp_bundle_path and os.path.exists(tmp_bundle_path):
            os.remove(tmp_bundle_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastapi_inference_service:app",
        host="0.0.0.0",
        port=8010,
        reload=False,
    )
