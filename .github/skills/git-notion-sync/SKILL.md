---
name: git-notion-sync
description: "Use when: syncing eMach Git commit evidence with Notion task fields and correcting inconsistent task states."
---

# Git Notion Sync

## Purpose
Synchronize task status with Git evidence and correct inconsistent Notion rows.

## Inputs
- Notion token and database ID
- Optional task key
- Optional commit hash and note

## Workflow
1. Ensure Notion metadata baseline is populated:
   - ./sync_notion_fields.ps1 -Token <token> -DatabaseId <db>
2. Heartbeat update for in-progress rows:
   - ./notion_task_update.ps1 -Token <token> -DatabaseId <db> -Mode heartbeat
3. Completion update when evidence exists:
   - ./notion_task_update.ps1 -Token <token> -DatabaseId <db> -Mode done -TaskKey <key> -CommitHash <hash> -Note <summary>
4. Hold update on blocker:
   - ./notion_task_update.ps1 -Token <token> -DatabaseId <db> -Mode hold -TaskKey <key> -Note <blocker>

## Validation checklist
- done rows include commit hash or evidence URL
- blocked rows include blocker notes
- sync date and server ID are set

## Output
- Updated row count
- Failed row count
- Actionable list of inconsistent rows
