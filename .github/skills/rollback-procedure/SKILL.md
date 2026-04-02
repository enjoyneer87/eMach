---
name: rollback-procedure
description: "Use when: critical defects require reverting to a known stable code/model state and re-verifying service health."
---

# Rollback Procedure

## Trigger
Start rollback immediately when RC gate identifies critical defects.

## Workflow
1. Code rollback
   - identify stable commit hash
   - fetch latest remote
   - restore to stable hash using approved rollback path
2. Data/model rollback
   - switch model version to previous stable tag
   - invalidate stale cache and re-run validation
3. Verification
   - rerun core smoke tests
   - update Notion status to hold
   - include rollback reason and evidence in notes

## Output
- stable target hash/tag
- rollback execution result
- post-rollback smoke test result
- Notion hold update evidence
