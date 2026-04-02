# Action 12 Rollback Procedure
> Migrated: Active workflow source is [eMach/.github/skills/rollback-procedure/SKILL.md](eMach/.github/skills/rollback-procedure/SKILL.md).

작성일: 2026-04-01

## 1) Trigger
- RC gate에서 치명 결함 발생 시 즉시 롤백 착수

## 2) Code Rollback
- 안정 커밋 해시 확인
- 대상 서버에서 원격 최신화 후 안정 해시로 복구

## 3) Data/Model Rollback
- 모델 버전 API에서 직전 stable 태그로 전환
- 캐시 무효화 및 결과 재검증

## 4) Verification
- 핵심 smoke test 재실행
- Notion 상태를 홀드로 전환하고 비고에 롤백 근거 기록
