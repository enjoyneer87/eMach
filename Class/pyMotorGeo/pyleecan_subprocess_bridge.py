import json
import os
import subprocess
import tempfile
from pathlib import Path


def default_pyleecan_python() -> str:
    return os.environ.get(
        "EMACH_PYLEECAN_PYTHON",
        r"C:\Users\user\.ansys_python_venvs\pyMotorEnv_Pyleecan\Scripts\python.exe",
    )


def run_external_pyleecan_bridge(
    input_path: str,
    input_type: str,
    source_name: str,
    machine_name: str,
    stack_length_mm: float,
    pyleecan_python: str | None = None,
    timeout_sec: int = 240,
) -> dict:
    runner_path = Path(__file__).resolve().parent / "pyleecan_env_runner.py"
    py_exe = pyleecan_python or default_pyleecan_python()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        output_path = tmp.name

    cmd = [
        py_exe,
        str(runner_path),
        "--source-name",
        source_name,
        "--machine-name",
        machine_name,
        "--stack-length-mm",
        str(float(stack_length_mm)),
        "--output-json",
        output_path,
    ]

    if input_type == "dxf":
        cmd.extend(["--dxf-path", str(input_path)])
    elif input_type == "json":
        cmd.extend(["--bundle-json", str(input_path)])
    else:
        raise ValueError(f"Unsupported input_type: {input_type}")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )

        payload = {
            "ok": False,
            "error": "No runner output produced",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "python_executable": py_exe,
        }

        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            payload["stdout"] = proc.stdout
            payload["stderr"] = proc.stderr
            payload["returncode"] = proc.returncode
            payload["python_executable"] = py_exe

        return payload
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"TimeoutExpired: {exc}",
            "stdout": exc.stdout,
            "stderr": exc.stderr,
            "returncode": None,
            "python_executable": py_exe,
        }
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
