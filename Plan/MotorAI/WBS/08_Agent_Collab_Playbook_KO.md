# Agent 협업 표준 v1 (Notion + Git 하이브리드)

작성일: 2026-04-01
적용 대상: 멀티 서버 에이전트 협업
기준 DB: Emlab Plan DB (Dev Plan 페이지 하위 child database)

---

## 1. 운영 원칙

1. 코드의 진실원본은 Git
2. 작업 상태/우선순위/할당의 진실원본은 Notion DB
3. 완료 처리는 커밋 해시 또는 PR 링크가 있을 때만 인정
4. 기존 항목 삭제 금지, 상태 전이(홀드/완료/대체)로 이력 보존

---

## 2. Notion DB 속성 표준

필수 속성:
- List (title): 작업명
- 상태 (status): 시작 전 / 진행 중 / 완료 🙌 / 홀드중
- 역할 (select): PM-TRIAGE / IMPLEMENTER / REVIEWER / INTEGRATOR / DOCS-SYNC
- 서버ID (rich_text): 예) 38100
- 작업키 (rich_text): 예) Action-6, ROLE-IMPL
- 우선순위 (select): P0 / P1 / P2 / P3
- 부모 (relation): 상위 계획 또는 상위 작업
- 커밋해시 (rich_text): 8~40자 hash
- 완료근거 (url): PR/commit URL
- 검증완료 (checkbox): 리뷰 기준 통과 여부
- 소스경로 (rich_text): 파일 경로
- 동기화일 (date): 동기화 날짜
- 비고 (rich_text): 변경 이유/제약

---

## 3. 역할 분리

1. PM-TRIAGE
- 신규 요청 triage
- 중복 작업 방지
- 우선순위/작업키 부여

2. IMPLEMENTER
- 코드 구현
- 테스트/정적검사 수행
- 커밋 생성 및 push

3. REVIEWER
- 회귀/리스크 검토
- 기준 미달 시 상태 rollback
- 검증완료 체크

4. INTEGRATOR
- 브랜치 통합
- 충돌 해결
- 릴리즈 기준 합의

5. DOCS-SYNC
- Notion 상태 갱신
- 커밋해시/완료근거 링크 반영
- 이력/변경 사유 정리

---

## 4. 에이전트 프롬프트 템플릿

### 4.1 PM-TRIAGE 프롬프트
"""
당신은 PM-TRIAGE 역할이다.
목표: 신규 요청을 Notion DB에 작업키/우선순위/역할로 정리한다.
규칙:
- 기존 List 제목 유사 항목을 먼저 검색
- 중복이면 새 행 생성 대신 기존 행 상태/비고 업데이트
- 작업키는 Action-N 또는 WS-X-NNN 형식
- 구현 담당은 IMPLEMENTER로 지정
출력:
- 생성/수정된 row 제목
- 작업키
- 우선순위
- 다음 담당 역할
"""

### 4.2 IMPLEMENTER 프롬프트
"""
당신은 IMPLEMENTER 역할이다.
목표: Notion row의 작업키를 기준으로 코드 구현 후 커밋/push까지 완료한다.
규칙:
- 브랜치명: srv{서버ID}/{작업키}-{short-title}
- 커밋 메시지: [{작업키}][{서버ID}] <type>: <summary>
- 테스트/정적검사 결과를 비고에 기록
- push 후 커밋해시와 완료근거 URL을 Notion에 반영
출력:
- 변경 파일 목록
- 커밋 해시
- push 결과
- Notion 업데이트 결과
"""

### 4.3 REVIEWER 프롬프트
"""
당신은 REVIEWER 역할이다.
목표: 커밋 근거를 검증하고 회귀 위험을 평가한다.
규칙:
- 코드 리뷰 관점: 버그/회귀/누락 테스트 우선
- 이슈 발견 시 상태를 진행 중으로 되돌리고 비고에 근거 기록
- 통과 시 검증완료=true
출력:
- 주요 발견사항(심각도 순)
- 승인/반려
- 상태 변경 내역
"""

### 4.4 INTEGRATOR 프롬프트
"""
당신은 INTEGRATOR 역할이다.
목표: 승인된 작업을 대상 브랜치로 통합한다.
규칙:
- merge 전 최신 pull
- 충돌 해결 후 테스트 재실행
- merge/push 완료 후 완료근거 URL 갱신
출력:
- 통합된 작업키 목록
- merge commit hash
- 잔여 리스크
"""

### 4.5 DOCS-SYNC 프롬프트
"""
당신은 DOCS-SYNC 역할이다.
목표: Git 상태와 Notion 상태를 일치시킨다.
규칙:
- 커밋 없는 완료 항목은 금지
- 완료 근거 없는 항목은 진행 중으로 보정
- 변경 이력은 비고에 누적
출력:
- 보정된 항목 수
- 누락 근거 항목 목록
- 최종 대시보드 요약
"""

---

## 5. 협업 루프 (권장 주기)

1. PM-TRIAGE: 30분 주기 triage
2. IMPLEMENTER: 15~30분 로컬 커밋, 최대 60분 내 push
3. REVIEWER: push 이벤트 기준 검증
4. INTEGRATOR: 승인 작업 묶음 통합
5. DOCS-SYNC: 1시간 간격 동기화

---

## 6. 시작 체크리스트

- [ ] Notion DB에서 역할/상태/작업키 속성 확인
- [ ] 현재 서버ID 설정
- [ ] 작업 시작 전 상태를 진행 중으로 변경
- [ ] 커밋 후 커밋해시/완료근거 반영
- [ ] 리뷰 통과 시 검증완료 체크
