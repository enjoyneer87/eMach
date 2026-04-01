# Emlab_emach Agent Operating Instructions

## Core Intent
- Prioritize real code development tasks from the Dev Plan over frequent Notion polling.
- Use Notion as workflow/state tracking, not as the main work loop.
- This workspace is non-ML-training mode overnight. Do not start or queue heavy model training jobs.

## Nightly Development Routine
1. Read current Dev Plan items and pick the next actionable coding task.
2. Set task state to `진행 중` when work starts.
3. Implement code changes in this repository.
4. Run minimal validation (lint/smoke/syntax/tests relevant to touched files).
5. Record evidence (file paths, test result summary, and if available commit hash).
6. On task end:
- `완료` when acceptance conditions are met.
- `홀드` when interrupted, blocked, or unfinished.

## Notion DB Update Policy
- Use environment variables only: `NOTION_TOKEN`, `NOTION_DATABASE_ID`, `EMACH_SERVER_ID`.
- Keep state transitions deterministic:
- Start: `진행 중`
- Success: `완료`
- Interrupted/Unfinished: `홀드`
- Update row metadata when possible:
- `커밋해시`: latest relevant commit short hash
- `검증완료`: true only when task is truly done
- `동기화일`: current date
- `비고`: short routine note + evidence

## Commit and Evidence Policy
- Prefer small, focused commits for each completed task.
- Commit message should include action context (e.g., Action number/title).
- If no commit was made, write explicit reason in note/evidence.

## Safety and Scope
- Do not run ML training workloads in overnight automation for this workspace.
- Avoid destructive git operations.
- Do not revert unrelated user changes.
- Keep edits minimal and tied to active plan items.

## Priority Order
1. Unblocked code tasks that improve the running product/workflow.
2. Validation and regression prevention for touched areas.
3. Notion status/evidence sync.
4. Documentation updates tied to completed code work.
