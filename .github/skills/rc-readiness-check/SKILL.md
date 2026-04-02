---
name: rc-readiness-check
description: "Use when: performing release-candidate readiness checks and collecting evidence before go/no-go decisions."
---

# RC Readiness Check

## Purpose
Run and verify RC checklist items with evidence capture.

## Checklist baseline
- contract breaking change check
- core workflow smoke pass
- bridge pass status
- failure taxonomy reflected
- version matrix updated
- weekly gate decision recorded
- Notion DB synchronized
- rollback procedure verified

## Workflow
1. Execute checklist items and capture results.
2. Record evidence table entries:
   - smoke test summary
   - commit hash
   - report path
   - notion row status
3. If all gates pass, mark verification complete.
4. If any critical gate fails, do not mark done; move to hold and invoke rollback skill.

## Output
- pass/fail per checklist item
- go/conditional go decision
- evidence summary block
