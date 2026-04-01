# Action 09 Execution Failure Taxonomy (Draft)

작성일: 2026-04-01
목적: 실행 실패를 표준 코드로 분류하여 자동 재시도/리포트 체계를 단순화한다.

## 코드 체계
- 접두어: E (Error), W (Warning)
- 범주: IO, PARSE, CONTRACT, ENV, SOLVER, BRIDGE, API, UI

## 표준 코드표
| Code | Category | Description | Retry Policy | Owner |
|---|---|---|---|---|
| E-IO-001 | IO | 입력 파일 없음/경로 오류 | no retry | IMPLEMENTER |
| E-PARSE-001 | PARSE | DXF/JSON 파싱 실패 | retry once after sanitize | IMPLEMENTER |
| E-CONTRACT-001 | CONTRACT | contract_version 불일치 | no retry | PM-TRIAGE |
| E-ENV-001 | ENV | 필수 env var 누락 | no retry | INTEGRATOR |
| E-SOLVER-001 | SOLVER | 외부 해석기 실행 실패 | retry once | IMPLEMENTER |
| E-BRIDGE-001 | BRIDGE | pyleecan bridge object 생성 실패 | retry once with fallback | IMPLEMENTER |
| E-API-001 | API | FastAPI endpoint 예외 | retry with backoff | INTEGRATOR |
| E-UI-001 | UI | Streamlit 렌더링 예외 | no retry | IMPLEMENTER |
| W-CONTRACT-001 | CONTRACT | optional field 누락 | continue | REVIEWER |
| W-BRIDGE-001 | BRIDGE | fallback path 사용됨 | continue | REVIEWER |

## 운영 규칙
- 신규 실패는 기존 코드 재사용을 우선한다.
- 신규 코드 추가 시 원인/재현/대응을 한 줄로 남긴다.
- 노션 DB 비고 필드에 코드와 commit hash를 같이 기록한다.

## 변경 이력
- 2026-04-01: 초안 생성 (AUTO-NONML)
