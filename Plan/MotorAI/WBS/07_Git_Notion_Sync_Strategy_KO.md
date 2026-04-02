# eMach Git 커밋 - Notion 실시간 동기화 및 플랜 수정 전략 (SSOT)
> Migrated: Active policy/workflow split is in [eMach/.github/instructions/git-notion-sync.instructions.md](eMach/.github/instructions/git-notion-sync.instructions.md) and [eMach/.github/skills/git-notion-sync/SKILL.md](eMach/.github/skills/git-notion-sync/SKILL.md).

본 문서는 통합 개발 환경(여러 대의 서버 및 에이전트)에서 **Plan 문서의 변경 이력을 투명하게 관리**하고, 에이전트 채팅 문맥상의 추정(Context)뿐만 아니라 **실제 코드 커밋(Git)을 기준으로 노션 대시보드를 갱신**하기 위한 파이프라인 전략을 정의합니다.

## 1. Plan 문서 수정 및 삭제(취소선) 정책
계획은 수시로 변경될 수 있으나, 과거의 맥락을 잃어버리지 않기 위해 다음과 같은 규칙을 따릅니다.

*   **마크다운 규칙**: 기존 계획을 지우지 않고 `~~취소선~~`을 적용합니다. 변경된 내용은 우측에 추가하고 반드시 `(Modified by Server: 포트번호)` 형식의 꼬리표를 붙입니다.
    *   *예시:* `~~기존 솔버 연동 방식 우선~~ -> 표준 Contract Payload v1 설계 우선 (Modified by Server: 38100)`
*   **노션(Notion) 동기화 규칙**: `agent_sync_logger.py` 안에 `log_plan_change()` 함수를 도입하여, 노션 API의 `strikethrough: True` 속성을 활용해 줄이 그어진 텍스트 블록과 새 텍스트 블록을 동시에 렌더링합니다.

## 2. 수동 커밋(Git)과 Agent 노션 연동 전략 (3가지 제안)

현재 에이전트와의 채팅만으로 체크박스가 달성 처리되는 것은 "잠정적 완료"입니다. 실제 코드가 저장소에 박제(Commit)되는 시점에 노션을 "최종 검증 완료"로 만들기 위한 3가지 연계 방식입니다.

### 💡 전략 A: Git Hook 자동화 (가장 강력한 엔지니어링 접근)
*   **개념**: 저장소의 `.git/hooks/post-commit` 스크립트에 `agent_sync_logger.py`를 물려놓습니다.
*   **작동 방식**: 
    *   개발자가 직접 터미널에서 `git commit -m "Fix: pyMCAD h5/txt 파싱 모듈 구현 (Action 3)"` 라고 타이핑합니다.
    *   엔터키를 누르는 순간, Git Hook이 커밋 메시지 안의 `Action 3`라는 키워드를 감지하고 백그라운드에서 노션 API를 호출해 해당 작업을 `Checked: True`로 변경합니다.
*   **장점**: 개발자가 평소대로 커밋만 하면 노션이 알아서 업데이트되므로 컨텍스트 누락이 전혀 없습니다.

### 💡 전략 B: Agent-Assisted Commit (채팅 주도 커밋)
*   **개념**: 개발자가 수동으로 `git add/commit`을 치는 대신, 이 채팅창에서 에이전트에게 커밋을 위임합니다.
*   **작동 방식**:
    *   사용자: *"방금 짠 Pyleecan 브릿지 코드 커밋해주고, 노션 Action 5번 완료 처리해 줘."*
    *   에이전트: `git add .` -> `git commit -m "..."` 커맨드를 실행하고 성공 여부를 판독한 뒤, 노션 API를 호출해 체크박스와 서버 포트번호(38100)를 업데이트합니다.
*   **장점**: 설정할 파일이 필요 없고 매우 직관적입니다. 코딩과 커밋, 문서화가 한 문맥(채팅)에서 깔끔하게 떨어집니다.

### 💡 전략 C: Commit Sync CLI 도구 배치 (배치 동기화)
*   **개념**: 코드 작업이 한창일 때는 커밋만 마음대로 하고, 퇴근 전이나 주기적으로 `python sync_notion_from_git.py`라는 유틸리티를 돌립니다.
*   **작동 방식**: 스크립트가 최근 10개의 Git 커밋 로그를 읽어온 뒤, 노션의 체크리스트를 대조하여 아직 체크되지 않은 작업을 스캔해 한꺼번에 일괄 업데이트(Bulk Update)합니다.

## 3. 추천 도입 방안 및 Next Step
*   당장의 빠른 협업을 위해서는 **전략 B (에이전트 주도 커밋)**를 사용하여 에이전트와 대화하며 코딩-커밋-노션 업데이트를 하나의 호흡으로 묶는 것이 가장 좋습니다.
*   장기적으로 다른 사람들도 참여할 때는 레포지토리 단에 **전략 A (Git Hook)**를 덧씌워 수동 커밋마저도 누락 없이 추적하도록 구성하는 것을 권장합니다.