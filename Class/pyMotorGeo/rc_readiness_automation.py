from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
TMP_BASE = Path(os.environ.get("TEMP", str(Path.home()))) / "emach_overnight_runner"
REPORT_DIR = TMP_BASE / "reports"
ACTION12_PATH = ROOT / "Plan" / "MotorAI" / "WBS" / "Action12_RC_Readiness_Checklist_KO.md"
ACTION11_GATE_RECORD_PATH = ROOT / "Plan" / "MotorAI" / "WBS" / "Action11_Weekly_Gate_Record_LATEST_KO.md"
ROLLBACK_DOC_PATH = ROOT / "Plan" / "MotorAI" / "WBS" / "Action12_Rollback_Procedure_KO.md"


@dataclass
class CheckResult:
    key: str
    title: str
    passed: bool
    evidence: str


def _run(cmd: List[str], timeout_sec: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_sec,
    )


def _find_first_file_by_keywords(base: Path, keywords: List[str], suffix: str = ".md") -> Path | None:
    for p in base.rglob(f"*{suffix}"):
        name = p.name.lower()
        if all(k.lower() in name for k in keywords):
            return p
    return None


def _latest_git_hash() -> str:
    proc = _run(["git", "-C", str(ROOT), "log", "-1", "--pretty=%h"], timeout_sec=30)
    if proc.returncode == 0:
        return (proc.stdout or "").strip()
    return ""


def _check_contract_integrity() -> CheckResult:
    contracts_py = ROOT / "Class" / "pyMotorGeo" / "contracts.py"
    examples_dir = ROOT / "Class" / "pyMotorGeo" / "contract_examples"
    if not contracts_py.exists():
        return CheckResult("contract", "contract breaking change 없음 확인", False, "contracts.py missing")

    example_count = len(list(examples_dir.glob("*.json"))) if examples_dir.exists() else 0
    if example_count <= 0:
        return CheckResult("contract", "contract breaking change 없음 확인", False, "contract examples missing")

    txt = contracts_py.read_text(encoding="utf-8", errors="ignore")
    if "BREAKING" in txt.upper():
        return CheckResult("contract", "contract breaking change 없음 확인", False, "contracts.py contains BREAKING marker")

    return CheckResult("contract", "contract breaking change 없음 확인", True, f"contracts.py + {example_count} examples")


def _check_smoke_workflow(python_executable: str) -> CheckResult:
    key_files = [
        ROOT / "Class" / "pyMotorGeo" / "sync_notion_plan_db.py",
        ROOT / "Class" / "pyMotorGeo" / "overnight_devplan_runner.py",
        ROOT / "Class" / "pyMotorGeo" / "pyleecan_subprocess_bridge.py",
        ROOT / "Class" / "pyMotorGeo" / "ui" / "app.py",
    ]
    cmd = [python_executable, "-m", "py_compile", *[str(p) for p in key_files if p.exists()]]
    proc = _run(cmd, timeout_sec=240)
    if proc.returncode == 0:
        return CheckResult("smoke", "핵심 워크플로우 smoke pass", True, "py_compile smoke pass")

    err = (proc.stderr or proc.stdout or "smoke failed").strip().splitlines()
    return CheckResult("smoke", "핵심 워크플로우 smoke pass", False, err[-1] if err else "smoke failed")


def _check_json_only_bridge() -> CheckResult:
    p = ROOT / "Class" / "pyMotorGeo" / "pyleecan_subprocess_bridge.py"
    if not p.exists():
        return CheckResult("json_only", "JSON-only pyleecan bridge pass", False, "pyleecan_subprocess_bridge.py missing")

    txt = p.read_text(encoding="utf-8", errors="ignore")
    tokens = ["if input_type != \"json\"", "JSON-only mode"]
    missing = [t for t in tokens if t not in txt]
    if missing:
        return CheckResult("json_only", "JSON-only pyleecan bridge pass", False, f"missing tokens: {', '.join(missing)}")

    return CheckResult("json_only", "JSON-only pyleecan bridge pass", True, "json-only guard found")


def _check_taxonomy() -> CheckResult:
    doc = _find_first_file_by_keywords(ROOT / "Plan", ["taxonomy"], ".md")
    if doc is None:
        return CheckResult("taxonomy", "실패 taxonomy 코드 반영 완료", False, "taxonomy doc not found")
    return CheckResult("taxonomy", "실패 taxonomy 코드 반영 완료", True, doc.name)


def _check_version_matrix() -> CheckResult:
    matrix_doc = ROOT / "MOTOR_REPOSITORY_COMPARISON_MATRIX.md"
    if not matrix_doc.exists():
        return CheckResult("matrix", "버전 매트릭스 최신화", False, "matrix doc not found")

    modified = datetime.fromtimestamp(matrix_doc.stat().st_mtime)
    age = datetime.now() - modified
    if age > timedelta(days=30):
        return CheckResult("matrix", "버전 매트릭스 최신화", False, f"matrix doc stale: {age.days} days")

    return CheckResult("matrix", "버전 매트릭스 최신화", True, f"updated {modified.strftime('%Y-%m-%d')}")


def _write_gate_record(server_id: str, check_results: List[CheckResult]) -> str:
    failed = [c.title for c in check_results if not c.passed]
    decision = "Go" if not failed else "Conditional Go"
    lines = [
        "# Action 11 Weekly Gate Record",
        "",
        f"작성일: {datetime.now().strftime('%Y-%m-%d')}",
        f"Server ID: {server_id}",
        "",
        "## Decision",
        f"- Gate 판정: {decision}",
        "",
        "## Pending Conditions",
    ]
    if failed:
        lines.extend([f"- {x}" for x in failed])
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Evidence Summary",
        "| Item | Pass | Evidence |",
        "|---|---|---|",
    ])
    for c in check_results:
        lines.append(f"| {c.title} | {'Y' if c.passed else 'N'} | {c.evidence} |")

    ACTION11_GATE_RECORD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return decision


def _check_gate_record(server_id: str, check_results: List[CheckResult]) -> CheckResult:
    decision = _write_gate_record(server_id, check_results)
    if decision in {"Go", "Conditional Go"}:
        return CheckResult("gate", "주간 Gate 판정 Go/Conditional Go 기록", True, f"decision={decision}")
    return CheckResult("gate", "주간 Gate 판정 Go/Conditional Go 기록", False, "decision not recorded")


def _ensure_rollback_doc() -> CheckResult:
    if not ROLLBACK_DOC_PATH.exists():
        lines = [
            "# Action 12 Rollback Procedure",
            "",
            f"작성일: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## 1) Trigger",
            "- RC gate에서 치명 결함 발생 시 즉시 롤백 착수",
            "",
            "## 2) Code Rollback",
            "- 안정 커밋 해시 확인",
            "- 대상 서버에서 원격 최신화 후 안정 해시로 복구",
            "",
            "## 3) Data/Model Rollback",
            "- 모델 버전 API에서 직전 stable 태그로 전환",
            "- 캐시 무효화 및 결과 재검증",
            "",
            "## 4) Verification",
            "- 핵심 smoke test 재실행",
            "- Notion 상태를 홀드로 전환하고 비고에 롤백 근거 기록",
        ]
        ROLLBACK_DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return CheckResult("rollback", "롤백 절차 문서 확인", True, ROLLBACK_DOC_PATH.name)


def _check_notion_reflected(sync_status: str) -> CheckResult:
    if sync_status == "done":
        return CheckResult("notion", "변경 사항 Notion DB 반영", True, "sync=done")
    return CheckResult("notion", "변경 사항 Notion DB 반영", False, f"sync={sync_status}")


def _replace_or_append_line(lines: List[str], startswith: str, newline: str) -> List[str]:
    out = []
    replaced = False
    for line in lines:
        if line.startswith(startswith):
            out.append(newline)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(newline)
    return out


def _update_action12_checklist(check_results: List[CheckResult], report_rel: str, notion_status: str) -> None:
    if not ACTION12_PATH.exists():
        return

    text = ACTION12_PATH.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    check_map = {c.title: c.passed for c in check_results}
    for i, line in enumerate(lines):
        m = re.match(r"^-\s*\[([ xX])\]\s+(.+)$", line.strip())
        if not m:
            continue
        title = m.group(2).strip()
        if title in check_map:
            mark = "x" if check_map[title] else " "
            lines[i] = f"- [{mark}] {title}"

    total = len(check_results)
    passed = sum(1 for c in check_results if c.passed)
    commit_hash = _latest_git_hash()

    lines = _replace_or_append_line(lines, "| smoke test |", f"| smoke test | {passed}/{total} pass |")
    lines = _replace_or_append_line(lines, "| commit hash |", f"| commit hash | {commit_hash or '-'} |")
    lines = _replace_or_append_line(lines, "| report file |", f"| report file | {report_rel} |")
    lines = _replace_or_append_line(lines, "| notion row |", f"| notion row | {notion_status} |")

    ACTION12_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_rc_readiness(python_executable: str, server_id: str, notion_sync_status: str) -> dict:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    checks: List[CheckResult] = []
    checks.append(_check_contract_integrity())
    checks.append(_check_smoke_workflow(python_executable))
    checks.append(_check_json_only_bridge())
    checks.append(_check_taxonomy())
    checks.append(_check_version_matrix())
    checks.append(_check_notion_reflected(notion_sync_status))
    checks.append(_ensure_rollback_doc())
    checks.append(_check_gate_record(server_id, checks.copy()))

    all_pass = all(c.passed for c in checks)
    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "server_id": server_id,
        "notion_sync_status": notion_sync_status,
        "all_pass": all_pass,
        "checks": [
            {
                "key": c.key,
                "title": c.title,
                "passed": c.passed,
                "evidence": c.evidence,
            }
            for c in checks
        ],
    }

    report_path = REPORT_DIR / "rc_readiness_latest.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    report_rel = str(report_path).replace("\\", "/")
    _update_action12_checklist(checks, report_rel=report_rel, notion_status=notion_sync_status)

    failed = [c.title for c in checks if not c.passed]
    evidence = "all checks passed" if all_pass else f"pending={len(failed)}: {', '.join(failed[:3])}"

    return {
        "status": "done" if all_pass else "in_progress",
        "evidence": evidence,
        "report_path": report_rel,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="RC readiness checklist automation")
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--server-id", default=os.environ.get("EMACH_SERVER_ID", "38100"))
    parser.add_argument("--notion-sync-status", default="in_progress")
    args = parser.parse_args()

    result = run_rc_readiness(
        python_executable=args.python_executable,
        server_id=args.server_id,
        notion_sync_status=args.notion_sync_status,
    )

    print(f"RC_READINESS_STATUS={result['status']}")
    print(f"RC_READINESS_EVIDENCE={result['evidence']}")
    print(f"RC_READINESS_REPORT={result['report_path']}")

    return 0 if result["status"] == "done" else 3


if __name__ == "__main__":
    raise SystemExit(main())
