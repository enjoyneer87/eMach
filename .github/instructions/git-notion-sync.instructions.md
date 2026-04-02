---
description: "Use when: working on eMach tasks that require Git evidence and Notion status consistency."
applyTo: "**/*"
---
# eMach Git/Notion Sync Instruction

Apply these rules for eMach task execution.

## Core policy
- Git is source of truth for code state.
- Notion DB is source of truth for task status, assignment, and priority.
- Mark a task as complete only when commit hash or PR URL evidence exists.
- Do not delete prior task history; use status transitions and notes.

## Mandatory metadata updates
- Always keep sync date and server ID updated.
- On completion, include commit hash and evidence URL.
- If blocked, keep verification false and add blocker reason.

## Role handoff baseline
- IMPLEMENTER: code + tests + commit/push
- REVIEWER: regression-risk first review and verification gate
- DOCS-SYNC: align Notion with Git evidence

## Safety
- Never mark done without evidence.
- Keep updates idempotent and append reason in notes when overriding state.
