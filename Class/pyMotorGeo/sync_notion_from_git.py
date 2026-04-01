import argparse
import re
import subprocess
from pathlib import Path

from agent_sync_logger import AgentSyncLogger


def _run_git(repo: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _get_latest_commit(repo: Path) -> tuple[str, str]:
    commit_hash = _run_git(repo, ["log", "-1", "--pretty=%H"])
    subject = _run_git(repo, ["log", "-1", "--pretty=%s"])
    return commit_hash, subject


def _infer_action_id(subject: str) -> str | None:
    m = re.search(r"action\s*([0-9]+)", subject, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync latest git commit proof to Notion todo logs"
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Git repository path (default: current directory)",
    )
    parser.add_argument(
        "--action-id",
        default=None,
        help="Action ID (e.g., 6). If omitted, inferred from commit subject.",
    )
    parser.add_argument(
        "--task-name",
        required=True,
        help="Action task display name for Notion",
    )

    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    commit_hash, subject = _get_latest_commit(repo)
    action_id = args.action_id or _infer_action_id(subject)
    if not action_id:
        raise ValueError(
            "Action ID를 찾을 수 없습니다. --action-id로 명시하거나 커밋 제목에 'Action N'을 포함하세요."
        )

    logger = AgentSyncLogger()
    logger.log_commit_verification(
        action_id=action_id,
        task_name=args.task_name,
        commit_hash=commit_hash,
        commit_subject=subject,
    )

    print(f"Notion sync completed for Action {action_id}")
    print(f"Commit: {commit_hash[:8]} - {subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
