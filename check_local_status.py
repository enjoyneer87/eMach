"""check_local_status.py – Report local development environment status.

Run this script from the repo root to get a quick overview of what is
present and available on the local machine for eMach development.

Usage::

    python check_local_status.py
"""
from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(label: str, detail: str = "") -> None:
    suffix = f"  ({detail})" if detail else ""
    print(f"  [OK]  {label}{suffix}")


def _warn(label: str, detail: str = "") -> None:
    suffix = f"  ({detail})" if detail else ""
    print(f"  [--]  {label}{suffix}")


def _check_import(package: str, import_name: str | None = None) -> bool:
    name = import_name or package
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", "?")
        _ok(package, version)
        return True
    except ImportError:
        _warn(package, "not installed")
        return False


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def check_python() -> None:
    print("\n[Python environment]")
    _ok("Python", platform.python_version())
    _ok("Platform", platform.platform())


def check_python_packages() -> None:
    print("\n[Python packages]")
    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("matplotlib", "matplotlib"),
        ("pandas", "pandas"),
        ("nbformat", "nbformat"),
        ("jupyter", "jupyter_core"),
    ]
    for label, import_name in packages:
        _check_import(label, import_name)


def check_repo_structure(root: Path) -> None:
    print("\n[Repository structure]")
    key_dirs = [
        "Class",
        "tools",
        "tool",
        "tests",
        "examples",
        "pyAEDT",
        "pyMCAD",
    ]
    key_files = [
        "README.md",
        "addpwd.m",
        "Discovery.py",
        "tools/pyutils/__init__.py",
    ]
    for d in key_dirs:
        path = root / d
        if path.is_dir():
            _ok(d + "/")
        else:
            _warn(d + "/", "not found")
    for f in key_files:
        path = root / f
        if path.is_file():
            _ok(f)
        else:
            _warn(f, "not found")


def check_matlab_files(root: Path) -> None:
    print("\n[MATLAB files (.m)]")
    m_files = list(root.rglob("*.m"))
    class_files = [p for p in m_files if "Class" in p.parts]
    test_files = [p for p in m_files if "tests" in p.parts]
    tool_files = [p for p in m_files if "tools" in p.parts or "tool" in p.parts]
    _ok("Total .m files found", str(len(m_files)))
    _ok("Class/ .m files", str(len(class_files)))
    _ok("tests/ .m files", str(len(test_files)))
    _ok("tools/ .m files", str(len(tool_files)))


def check_simulation_results(root: Path) -> None:
    print("\n[Simulation result files]")
    extensions = {
        ".mat": "MATLAB workspace files",
        ".json": "JSON data files",
        ".mot": "Motor-CAD files",
        ".jmag": "JMAG project files",
    }
    for ext, label in extensions.items():
        files = list(root.rglob(f"*{ext}"))
        if files:
            _ok(label, f"{len(files)} file(s)")
        else:
            _warn(label, "none found")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    root = Path(__file__).resolve().parent
    print("=" * 50)
    print("  eMach local status check")
    print(f"  Root: {root}")
    print("=" * 50)

    check_python()
    check_python_packages()
    check_repo_structure(root)
    check_matlab_files(root)
    check_simulation_results(root)

    print("\n" + "=" * 50)
    print("  Status check complete.")
    print("=" * 50)


if __name__ == "__main__":
    main()
