from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def default_venv_dir() -> Path:
    env_path = os.environ.get("EMACH_PYMOTORENV_DIR", "").strip()
    if env_path:
        return Path(env_path)

    home = Path.home()
    return home / ".ansys_python_venvs" / "pyMotorEnv_310"


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _choose_seed_python() -> list[str]:
    if os.name == "nt":
        probe = _run(["py", "-3.10", "-c", "import sys; print(sys.version)"])
        if probe.returncode == 0:
            return ["py", "-3.10"]
    return [sys.executable]


def ensure_env(venv_dir: Path, requirements_file: Path) -> tuple[bool, str, Path]:
    py_path = venv_python(venv_dir)
    created = False

    if not py_path.exists():
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        seed_python = _choose_seed_python()
        create_cmd = [*seed_python, "-m", "venv", str(venv_dir)]
        create = _run(create_cmd)
        if create.returncode != 0:
            msg = (create.stderr or create.stdout or "venv creation failed").strip()
            return False, f"env-create-failed: {msg}", py_path
        created = True

    pip_upgrade = _run([str(py_path), "-m", "pip", "install", "--upgrade", "pip"])
    if pip_upgrade.returncode != 0:
        msg = (pip_upgrade.stderr or pip_upgrade.stdout or "pip upgrade failed").strip()
        return False, f"pip-upgrade-failed: {msg}", py_path

    install = _run([str(py_path), "-m", "pip", "install", "-r", str(requirements_file)])
    if install.returncode != 0:
        msg = (install.stderr or install.stdout or "requirements install failed").strip()
        return False, f"requirements-install-failed: {msg}", py_path

    if created:
        return True, "created-and-synced", py_path
    return True, "already-exists-synced", py_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap pyMotorEnv_310 if missing")
    parser.add_argument("--venv-dir", default=str(default_venv_dir()))
    parser.add_argument(
        "--requirements",
        default=str(Path(__file__).resolve().parent / "requirements_pyMotorEnv_310.txt"),
    )
    args = parser.parse_args()

    venv_dir = Path(args.venv_dir).expanduser().resolve()
    requirements_file = Path(args.requirements).expanduser().resolve()

    if not requirements_file.exists():
        print(f"status=error ; reason=requirements-file-missing ; path={requirements_file}")
        return 2

    ok, reason, py_path = ensure_env(venv_dir, requirements_file)
    if not ok:
        print(f"status=error ; reason={reason}")
        return 1

    print(f"status=ok ; reason={reason} ; python={py_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
