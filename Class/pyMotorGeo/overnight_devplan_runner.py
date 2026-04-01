import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
TMP_BASE = Path(os.environ.get("TEMP", str(Path.home()))) / "emach_overnight_runner"
STATE_PATH = TMP_BASE / "overnight_nonml_state.json"
REPORT_DIR = TMP_BASE / "reports"
DEFAULT_DEV_ENV_DIR = Path.home() / ".ansys_python_venvs" / "pyMotorEnv_310"

ACTION12 = {
    1: "benchmark 10-case ID/location freeze",
    2: "Contract v1 schema/examples fixed",
    3: "pyMCAD h5/txt path standardization",
    4: "MLDataset validator minimum implementation",
    5: "MGN training runner draft",
    6: "MGN metrics calculator",
    7: "FastAPI inference endpoint minimum",
    8: "Streamlit Compare View minimum",
    9: "Execution failure taxonomy codes",
    10: "Version matrix draft",
    11: "Weekly gate review template",
    12: "RC readiness checklist",
}

ML_BLOCKED_ACTIONS = {5, 6}

ROUTINE_STEPS = [
    "plan_read_and_scope_lock",
    "set_action_status_in_progress",
    "implement_code_changes",
    "run_smoke_validation",
    "commit_or_collect_evidence",
    "update_notion_row_fields",
    "finalize_to_done_or_hold",
]

ENTITY_TASK_L2 = "TASK_L2"


@dataclass
class ActionState:
    status: str
    evidence: str


@dataclass
class GitSyncResult:
    status: str
    evidence: str
    commit_hash: str
    commit_subject: str


def _notion_headers() -> Optional[dict]:
    token = os.environ.get("NOTION_TOKEN", "")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _notion_request(url: str, method: str = "GET", payload: Optional[dict] = None) -> dict:
    import urllib.request

    headers = _notion_headers()
    if headers is None:
        raise RuntimeError("NOTION_TOKEN not set")

    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))


def _ensure_hold_status_option() -> None:
    database_id = os.environ.get("NOTION_DATABASE_ID", "")
    if not database_id:
        return
    try:
        db = _notion_request(f"https://api.notion.com/v1/databases/{database_id}", "GET")
        props = db.get("properties", {})
        status_prop = props.get("상태", {})
        if status_prop.get("type") != "status":
            return

        options = status_prop.get("status", {}).get("options", [])
        existing_by_name = {
            o.get("name", ""): {
                "name": o.get("name", ""),
                "color": o.get("color", "default"),
            }
            for o in options
            if o.get("name")
        }

        required = [
            ("시작 전", "default"),
            ("진행 중", "blue"),
            ("완료", "green"),
            ("홀드", "yellow"),
        ]
        merged = []
        for name, color in required:
            merged.append(existing_by_name.get(name, {"name": name, "color": color}))

        current_names = {o.get("name", "") for o in options}
        if current_names == {m["name"] for m in merged}:
            return

        _notion_request(
            f"https://api.notion.com/v1/databases/{database_id}",
            "PATCH",
            {
                "properties": {
                    "상태": {
                        "status": {
                            "options": merged,
                        }
                    }
                }
            },
        )
    except Exception:
        return


def _query_action_rows() -> List[dict]:
    database_id = os.environ.get("NOTION_DATABASE_ID", "")
    if not database_id or _notion_headers() is None:
        return []

    rows: List[dict] = []
    payload = {
        "filter": {
            "property": "List",
            "title": {"contains": "PLANDB | L2 | Plan/MotorAI/WBS/Action"},
        },
        "page_size": 100,
    }

    while True:
        resp = _notion_request(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            "POST",
            payload,
        )
        rows.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        payload["start_cursor"] = resp.get("next_cursor")
    return rows


def _get_notion_property_types() -> Dict[str, str]:
    database_id = os.environ.get("NOTION_DATABASE_ID", "")
    if not database_id or _notion_headers() is None:
        return {}
    try:
        db = _notion_request(f"https://api.notion.com/v1/databases/{database_id}", "GET")
        props = db.get("properties", {})
        return {k: v.get("type", "") for k, v in props.items()}
    except Exception:
        return {}


def _status_for_action(action_state: str, finalizing: bool) -> str:
    if action_state == "done":
        return "완료"
    if action_state == "in_progress":
        return "홀드" if finalizing else "진행 중"
    if action_state == "skipped":
        return "홀드"
    return "시작 전"


def _sync_action_status_to_notion(
    action_states: Dict[int, ActionState],
    finalizing: bool = False,
    server_id: str = "",
    git_commit_hash: str = "",
    git_commit_subject: str = "",
    sync_note: str = "",
) -> None:
    if _notion_headers() is None:
        return

    _ensure_hold_status_option()
    prop_types = _get_notion_property_types()
    rows = _query_action_rows()

    def set_status_property(properties: Dict[str, dict], prop_name: str, status_name: str) -> None:
        ptype = prop_types.get(prop_name)
        if ptype == "status":
            properties[prop_name] = {"status": {"name": status_name}}
        elif ptype == "select":
            properties[prop_name] = {"select": {"name": status_name}}

    for row in rows:
        title_parts = row.get("properties", {}).get("List", {}).get("title", [])
        title = "".join(x.get("plain_text", "") for x in title_parts)
        m = re.search(r"Action(\d+)_", title)
        if not m:
            continue

        action_id = int(m.group(1))
        if action_id not in action_states:
            continue

        target = _status_for_action(action_states[action_id].status, finalizing=finalizing)
        page_id = row.get("id")
        if not page_id:
            continue

        properties: Dict[str, dict] = {}

        set_status_property(properties, "상태_작업", target)
        set_status_property(properties, "상태", target)

        if prop_types.get("엔티티구분") == "select":
            properties["엔티티구분"] = {"select": {"name": ENTITY_TASK_L2}}

        if server_id and prop_types.get("서버ID") == "rich_text":
            properties["서버ID"] = {
                "rich_text": [{"type": "text", "text": {"content": server_id}}]
            }

        if prop_types.get("동기화일") == "date":
            properties["동기화일"] = {"date": {"start": _now_iso()}}

        if git_commit_hash and prop_types.get("커밋해시") == "rich_text":
            short_hash = git_commit_hash[:8]
            properties["커밋해시"] = {
                "rich_text": [{"type": "text", "text": {"content": short_hash}}]
            }

        if prop_types.get("검증완료") == "checkbox":
            properties["검증완료"] = {"checkbox": (target == "완료")}

        if prop_types.get("비고") == "rich_text":
            phase = "finalize" if finalizing else "running"
            note = f"routine={phase}"
            if git_commit_subject:
                note += f" ; commit={git_commit_subject[:120]}"
            if sync_note:
                note += f" ; {sync_note[:280]}"
            properties["비고"] = {
                "rich_text": [{"type": "text", "text": {"content": note}}]
            }

        if not properties:
            continue

        try:
            _notion_request(
                f"https://api.notion.com/v1/pages/{page_id}",
                "PATCH",
                {"properties": properties},
            )
        except Exception:
            continue


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _parse_until(until_hhmm: str) -> datetime:
    now = datetime.now()
    hh, mm = until_hhmm.split(":")
    target = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return target


def _run(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_sec: Optional[int] = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_sec,
    )


def _default_dev_python() -> str:
    from_env = os.environ.get("EMACH_DEV_PYTHON", "").strip()
    if from_env:
        return from_env
    return str(DEFAULT_DEV_ENV_DIR / "Scripts" / "python.exe")


def _ensure_dev_python(bootstrap_enabled: bool = True) -> str:
    dev_python = Path(_default_dev_python())
    if dev_python.exists():
        return str(dev_python)

    if not bootstrap_enabled:
        return sys.executable

    bootstrap_script = Path(__file__).resolve().parent / "bootstrap_pyMotorEnv_310.py"
    if not bootstrap_script.exists():
        return sys.executable

    venv_dir = dev_python.parent.parent
    req_file = Path(__file__).resolve().parent / "requirements_pyMotorEnv_310.txt"

    proc = _run(
        [
            sys.executable,
            str(bootstrap_script),
            "--venv-dir",
            str(venv_dir),
            "--requirements",
            str(req_file),
        ],
        cwd=ROOT,
        timeout_sec=900,
    )

    if proc.returncode == 0 and dev_python.exists():
        return str(dev_python)
    return sys.executable


def _latest_git_commit() -> tuple[str, str]:
    try:
        h = _run(["git", "-C", str(ROOT), "log", "-1", "--pretty=%H"], timeout_sec=30)
        s = _run(["git", "-C", str(ROOT), "log", "-1", "--pretty=%s"], timeout_sec=30)
        if h.returncode == 0 and s.returncode == 0:
            return (h.stdout.strip(), s.stdout.strip())
    except Exception:
        pass
    return ("", "")


def _git_worktree_dirty() -> bool:
    proc = _run(["git", "-C", str(ROOT), "status", "--porcelain"], timeout_sec=30)
    if proc.returncode != 0:
        return False
    return bool((proc.stdout or "").strip())


def _git_current_branch() -> str:
    proc = _run(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"], timeout_sec=30)
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def _git_auto_commit_and_push(server_id: str, push_enabled: bool = True) -> GitSyncResult:
    if not _git_worktree_dirty():
        h, s = _latest_git_commit()
        return GitSyncResult("done", "working tree clean; auto-commit skipped", h, s)

    add = _run(["git", "-C", str(ROOT), "add", "-A"], timeout_sec=120)
    if add.returncode != 0:
        err = (add.stderr or add.stdout or "git add failed").strip().splitlines()
        return GitSyncResult("in_progress", f"git add failed: {err[-1] if err else 'unknown'}", "", "")

    commit_msg = f"[auto-sync][server:{server_id}] finalize {_now_str()}"
    commit = _run(["git", "-C", str(ROOT), "commit", "-m", commit_msg], timeout_sec=120)
    commit_log = f"{commit.stdout or ''}\n{commit.stderr or ''}".lower()
    if commit.returncode != 0 and "nothing to commit" not in commit_log:
        err = (commit.stderr or commit.stdout or "git commit failed").strip().splitlines()
        return GitSyncResult("in_progress", f"git commit failed: {err[-1] if err else 'unknown'}", "", "")

    commit_hash, commit_subject = _latest_git_commit()
    short_hash = commit_hash[:8] if commit_hash else "unknown"

    if not push_enabled:
        return GitSyncResult(
            "done",
            f"auto-commit created {short_hash}; push disabled",
            commit_hash,
            commit_subject,
        )

    branch = _git_current_branch()
    if not branch or branch == "HEAD":
        return GitSyncResult(
            "in_progress",
            f"auto-commit created {short_hash}; push skipped (detached HEAD)",
            commit_hash,
            commit_subject,
        )

    push = _run(["git", "-C", str(ROOT), "push", "origin", branch], timeout_sec=180)
    if push.returncode != 0:
        err = (push.stderr or push.stdout or "git push failed").strip().splitlines()
        return GitSyncResult(
            "in_progress",
            f"auto-commit created {short_hash}; push failed: {err[-1] if err else 'unknown'}",
            commit_hash,
            commit_subject,
        )

    return GitSyncResult(
        "done",
        f"auto-commit+push ok: {short_hash} -> origin/{branch}",
        commit_hash,
        commit_subject,
    )


def _find_first_file_by_keywords(base: Path, keywords: List[str], suffix: str = ".md") -> Optional[Path]:
    for p in base.rglob(f"*{suffix}"):
        name = p.name.lower()
        if all(k.lower() in name for k in keywords):
            return p
    return None


def _has_fastapi_code(base: Path) -> bool:
    for p in base.rglob("*.py"):
        if "venv" in str(p).lower():
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "FastAPI(" in txt or "from fastapi import" in txt:
            return True
    return False


def _check_fastapi_service_minimum() -> ActionState:
    service_path = ROOT / "Class" / "pyMotorGeo" / "fastapi_inference_service.py"
    if not service_path.exists():
        return ActionState("in_progress", "fastapi_inference_service.py not found")

    try:
        src = service_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ActionState("in_progress", "failed to read fastapi service source")

    static_tokens = [
        '@app.get("/health")',
        '@app.post("/infer/pyleecan-bundle")',
        "class PyleecanBundleRequest",
        "dry_run:",
    ]
    missing_tokens = [t for t in static_tokens if t not in src]
    if missing_tokens:
        return ActionState(
            "in_progress",
            f"FastAPI static markers missing: {', '.join(missing_tokens)}",
        )

    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("fastapi_inference_service", str(service_path))
        if spec is None or spec.loader is None:
            return ActionState("in_progress", "failed to load FastAPI service module")

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        app = getattr(mod, "app", None)
        if app is None:
            return ActionState("in_progress", "FastAPI app object missing")

        routes = getattr(app, "routes", [])
        route_paths = sorted(
            {
                getattr(r, "path", "")
                for r in routes
                if getattr(r, "path", "")
            }
        )
        required = {"/health", "/infer/pyleecan-bundle"}
        missing = sorted(list(required - set(route_paths)))
        if missing:
            return ActionState("in_progress", f"FastAPI routes missing: {', '.join(missing)}")

        req_model = getattr(mod, "PyleecanBundleRequest", None)
        has_dry_run = hasattr(req_model, "model_fields") and "dry_run" in req_model.model_fields
        if not has_dry_run:
            return ActionState("in_progress", "PyleecanBundleRequest.dry_run missing")

        return ActionState("done", "FastAPI routes + dry-run request model pass")
    except ModuleNotFoundError:
        return ActionState("done", "FastAPI static route markers + dry_run field pass")
    except Exception as exc:
        return ActionState("in_progress", f"FastAPI smoke failed: {type(exc).__name__}")


def _check_validator_smoke() -> ActionState:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from validation.ml_dataset_validator import validate_ml_dataset_payload

        sample = {
            "contract_version": "v1",
            "source": {"source_type": "h5", "path": "D:/dummy/sample.h5"},
            "graph": {
                "node_features": ["x", "y"],
                "edge_features": ["dist"],
                "target_fields": ["Bx", "By"],
            },
            "split": {"train": 0.8, "val": 0.1, "test": 0.1},
            "normalization": "train_stat",
            "metadata": {"smoke": True},
        }
        ok, errors = validate_ml_dataset_payload(sample, check_source_path=False)
        if ok:
            return ActionState("done", "validator import+smoke pass")
        return ActionState("in_progress", f"validator errors={len(errors)}")
    except Exception as exc:
        return ActionState("in_progress", f"validator smoke failed: {type(exc).__name__}")


def evaluate_actions() -> Dict[int, ActionState]:
    action_map: Dict[int, ActionState] = {}

    # 1) benchmark freeze artifact check
    benchmark_file = _find_first_file_by_keywords(ROOT / "Plan", ["benchmark", "case"], ".md")
    if benchmark_file is not None:
        action_map[1] = ActionState("done", f"found benchmark doc: {benchmark_file.name}")
    else:
        action_map[1] = ActionState("in_progress", "benchmark registry artifact not found")

    # 2) contract v1 schema/examples
    contracts_py = ROOT / "Class" / "pyMotorGeo" / "contracts.py"
    examples_dir = ROOT / "Class" / "pyMotorGeo" / "contract_examples"
    example_count = len(list(examples_dir.glob("*.json"))) if examples_dir.exists() else 0
    if contracts_py.exists() and example_count > 0:
        action_map[2] = ActionState("done", f"contracts.py + {example_count} examples")
    else:
        action_map[2] = ActionState("in_progress", "contract schema/examples incomplete")

    # 3) pyMCAD path standardization
    has_pymcad = (ROOT / "pyMCAD").exists()
    has_exports = (ROOT / "_mcad_exports").exists()
    if has_pymcad and has_exports:
        action_map[3] = ActionState("done", "pyMCAD and _mcad_exports detected")
    else:
        action_map[3] = ActionState("in_progress", "pyMCAD path artifacts incomplete")

    # 4) dataset validator minimum
    action_map[4] = _check_validator_smoke()

    # 5,6) ML actions are explicitly skipped in this environment
    action_map[5] = ActionState("skipped", "ML training unavailable in this environment")
    action_map[6] = ActionState("skipped", "ML training unavailable in this environment")

    # 7) FastAPI endpoint minimum
    action_map[7] = _check_fastapi_service_minimum()

    # 8) Streamlit compare view minimum
    streamlit_app = ROOT / "Class" / "pyMotorGeo" / "ui" / "app.py"
    if streamlit_app.exists():
        txt = streamlit_app.read_text(encoding="utf-8", errors="ignore")
        if "compare" in txt.lower():
            action_map[8] = ActionState("done", "compare keyword found in Streamlit app")
        else:
            action_map[8] = ActionState("in_progress", "Streamlit app exists; compare flow partial")
    else:
        action_map[8] = ActionState("in_progress", "Streamlit app missing")

    # 9) taxonomy doc
    tax_doc = _find_first_file_by_keywords(ROOT / "Plan", ["taxonomy"], ".md")
    if tax_doc is not None:
        action_map[9] = ActionState("done", f"taxonomy doc found: {tax_doc.name}")
    else:
        action_map[9] = ActionState("in_progress", "taxonomy doc not found")

    # 10) version matrix doc
    vm_doc = _find_first_file_by_keywords(ROOT, ["matrix"], ".md")
    if vm_doc is not None:
        action_map[10] = ActionState("done", f"matrix doc found: {vm_doc.name}")
    else:
        action_map[10] = ActionState("in_progress", "version matrix doc not found")

    # 11) weekly gate template
    gate_doc = _find_first_file_by_keywords(ROOT / "Plan", ["gate", "template"], ".md")
    if gate_doc is not None:
        action_map[11] = ActionState("done", f"gate template found: {gate_doc.name}")
    else:
        action_map[11] = ActionState("in_progress", "weekly gate template not found")

    # 12) rc checklist
    rc_doc = _find_first_file_by_keywords(ROOT / "Plan", ["rc", "checklist"], ".md")
    if rc_doc is not None:
        try:
            rc_text = rc_doc.read_text(encoding="utf-8", errors="ignore")
            if "- [ ]" in rc_text:
                action_map[12] = ActionState("in_progress", f"RC checklist pending items: {rc_doc.name}")
            else:
                action_map[12] = ActionState("done", f"RC checklist completed: {rc_doc.name}")
        except Exception:
            action_map[12] = ActionState("in_progress", f"RC checklist read warning: {rc_doc.name}")
    else:
        action_map[12] = ActionState("in_progress", "RC checklist not found")

    return action_map


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(data: dict) -> None:
    STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _emit_logger(message: str, heading: bool = False) -> None:
    token = os.environ.get("NOTION_TOKEN", "")
    page_id = os.environ.get("NOTION_PAGE_ID", "")
    if not token or not page_id:
        return
    try:
        from agent_sync_logger import AgentSyncLogger

        logger = AgentSyncLogger(token=token, page_id=page_id)
        if heading:
            logger.log_event(message, block_type="heading_3")
        else:
            logger.log_event(message, block_type="paragraph")
    except Exception:
        return


def run_plan_db_sync(server_id: str, python_executable: str) -> ActionState:
    token = os.environ.get("NOTION_TOKEN", "")
    database_id = os.environ.get("NOTION_DATABASE_ID", "")
    if not token or not database_id:
        return ActionState("in_progress", "NOTION_TOKEN/NOTION_DATABASE_ID not set")

    cmd = [
        python_executable,
        str(Path(__file__).resolve().parent / "sync_notion_plan_db.py"),
        "--server-id",
        server_id,
    ]
    try:
        proc = _run(cmd, cwd=ROOT, timeout_sec=300)
    except subprocess.TimeoutExpired:
        return ActionState("in_progress", "sync timeout (300s)")
    if proc.returncode == 0:
        msg = (proc.stdout or "").strip().splitlines()
        tail = msg[-1] if msg else "sync ok"
        return ActionState("done", tail)

    err = (proc.stderr or proc.stdout or "sync failed").strip().splitlines()
    return ActionState("in_progress", err[-1] if err else "sync failed")


def run_cycle(server_id: str, python_executable: str) -> dict:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    started = _now_str()

    sync_state = run_plan_db_sync(server_id, python_executable=python_executable)
    action_states = evaluate_actions()
    git_hash, git_subject = _latest_git_commit()
    _sync_action_status_to_notion(
        action_states,
        finalizing=False,
        server_id=server_id,
        git_commit_hash=git_hash,
        git_commit_subject=git_subject,
    )

    done_ids = [aid for aid, st in action_states.items() if st.status == "done"]
    skip_ids = [aid for aid, st in action_states.items() if st.status == "skipped"]
    progress_ids = [aid for aid, st in action_states.items() if st.status == "in_progress"]

    summary = {
        "timestamp": started,
        "server_id": server_id,
        "sync": {"status": sync_state.status, "evidence": sync_state.evidence},
        "counts": {
            "done": len(done_ids),
            "in_progress": len(progress_ids),
            "skipped": len(skip_ids),
        },
        "actions": {
            str(aid): {
                "title": ACTION12[aid],
                "status": action_states[aid].status,
                "evidence": action_states[aid].evidence,
            }
            for aid in sorted(ACTION12.keys())
        },
        "ml_blocked": sorted(list(ML_BLOCKED_ACTIONS)),
        "git": {
            "latest_hash": git_hash,
            "latest_subject": git_subject,
        },
        "routine": {
            "steps": ROUTINE_STEPS,
            "phase": "running",
        },
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = REPORT_DIR / f"overnight_nonml_{stamp}.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return summary


def _log_summary(summary: dict, state_before: dict) -> None:
    sync_state = summary["sync"]
    counts = summary["counts"]
    msg_head = (
        f"[AUTO-NONML] {summary['timestamp']} | "
        f"sync={sync_state['status']} | done={counts['done']} "
        f"in_progress={counts['in_progress']} skipped={counts['skipped']}"
    )
    print(msg_head)
    _emit_logger(msg_head, heading=True)

    prev_actions = state_before.get("actions", {}) if isinstance(state_before, dict) else {}

    for aid in sorted(ACTION12.keys()):
        action = summary["actions"][str(aid)]
        prev = prev_actions.get(str(aid), {})
        if action.get("status") != prev.get("status") or action.get("evidence") != prev.get("evidence"):
            line = f"Action {aid} | {action['status']} | {action['title']} | {action['evidence']}"
            print(line)
            _emit_logger(line)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Overnight DevPlan automation runner (non-ML mode)"
    )
    parser.add_argument("--server-id", default=os.environ.get("EMACH_SERVER_ID", "38100"))
    parser.add_argument("--interval-sec", type=int, default=1800)
    parser.add_argument("--until", default="08:30", help="HH:MM local time")
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--disable-env-bootstrap",
        action="store_true",
        help="Do not create pyMotorEnv_310 automatically when missing",
    )
    parser.add_argument(
        "--disable-auto-commit",
        action="store_true",
        help="Skip automatic git commit at shutdown",
    )
    parser.add_argument(
        "--disable-auto-push",
        action="store_true",
        help="Skip automatic git push even if auto-commit runs",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("Overnight DevPlan runner started (non-ML mode)")
    print(f"Time: {_now_str()}")
    print(f"Server: {args.server_id}")
    print(f"ML blocked actions: {sorted(list(ML_BLOCKED_ACTIONS))}")
    print(f"Auto commit on shutdown: {not args.disable_auto_commit}")
    print(f"Auto push on shutdown: {not args.disable_auto_push}")

    dev_python = _ensure_dev_python(bootstrap_enabled=(not args.disable_env_bootstrap))
    os.environ["EMACH_DEV_PYTHON"] = dev_python
    print(f"Dev python: {dev_python}")
    print("=" * 72)

    deadline = _parse_until(args.until)
    latest_summary: Optional[dict] = None

    try:
        while True:
            prev_state = _load_state()
            summary = run_cycle(args.server_id, python_executable=dev_python)
            latest_summary = summary
            _log_summary(summary, prev_state)
            _save_state(summary)

            if args.once:
                break

            if datetime.now() >= deadline:
                print(f"Reached deadline: {deadline.strftime('%Y-%m-%d %H:%M:%S')}")
                break

            time.sleep(max(60, int(args.interval_sec)))
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        git_sync_result: Optional[GitSyncResult] = None
        if not args.disable_auto_commit:
            git_sync_result = _git_auto_commit_and_push(
                args.server_id,
                push_enabled=(not args.disable_auto_push),
            )
            print(f"[GIT-SYNC] {git_sync_result.status} | {git_sync_result.evidence}")
        else:
            print("[GIT-SYNC] skipped (auto-commit disabled)")

        if latest_summary is not None:
            action_states: Dict[int, ActionState] = {}
            for aid_str, item in latest_summary.get("actions", {}).items():
                try:
                    aid = int(aid_str)
                except Exception:
                    continue
                action_states[aid] = ActionState(
                    status=item.get("status", "in_progress"),
                    evidence=item.get("evidence", ""),
                )

            git_info = latest_summary.get("git", {}) if isinstance(latest_summary, dict) else {}
            if git_sync_result is not None:
                if git_sync_result.commit_hash:
                    git_info["latest_hash"] = git_sync_result.commit_hash
                if git_sync_result.commit_subject:
                    git_info["latest_subject"] = git_sync_result.commit_subject
                git_info["sync_status"] = git_sync_result.status
                git_info["sync_evidence"] = git_sync_result.evidence

            _sync_action_status_to_notion(
                action_states,
                finalizing=True,
                server_id=args.server_id,
                git_commit_hash=git_info.get("latest_hash", ""),
                git_commit_subject=git_info.get("latest_subject", ""),
                sync_note=git_info.get("sync_evidence", ""),
            )

    print("Overnight DevPlan runner finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
