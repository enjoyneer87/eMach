---
name: emach-ops
description: eMach 저장소의 Git 상태와 최신 여부, 열해석 단계 위치, 저장된 결과 JSON을 짧게 조회한다. Thesis_emach 작업 재개와 상태 확인에 사용하며, 솔버 실행·모델 수정은 기존 motor-thermal-hybrid 지침으로 이어간다.
---

# eMach compact context

현재 작업 대상 checkout을 사용한다. 기본 로컬은 `E:\Code_Rep\Thesis_emach`지만,
사용자가 다른 경로를 지정하면 그 경로를 우선한다. Python 표준 라이브러리만 필요하다.
레포 루트에서 아래 명령 중 질문에 필요한 하나부터 실행한다. 구현 파일을 매번 읽지 않는다.

| 질문 | 명령 |
|---|---|
| 미커밋·브랜치·최신 핸드오프 | `python -B -X utf8 mlxperPJT/thermal/ops.py snapshot` |
| GitHub에 푸시됐나 / 최신인가 | `python -B -X utf8 mlxperPJT/thermal/ops.py snapshot --live` |
| 관련 코드 위치 | `python -B -X utf8 mlxperPJT/thermal/ops.py stages --chain e10 --query mapdl` |
| 단계 입출력·선행조건 | `python -B -X utf8 mlxperPJT/thermal/pipeline.py show e10.mapdl_hybrid` |
| 저장된 결과 파일 목록 | `python -B -X utf8 mlxperPJT/thermal/ops.py artifacts` |
| 결과의 필요한 값 | `python -B -X utf8 mlxperPJT/thermal/ops.py evidence <json-path> --pointer /key` |

- `--repo <path>`는 하위 명령 앞에 둔다. JSON 상대경로도 해당 레포 기준이다.
- 목록은 기본 8개다. `omitted`가 있으면 검색어·체인·JSON pointer로 범위를 좁힌다.
  `--limit`은 최대 25. JSON pointer는 `/parent/key`, 배열은 `/runs/0` 형태다.
- cached upstream은 실시간 GitHub 상태가 아니다. `--live`도 원격 커밋을 로컬에 갖고
  있지 않으면 선후 관계를 `unknown`으로 남긴다. 필요할 때만 fetch 후 재비교한다.
- artifacts는 세 결과 폴더의 JSON 목록이며 전체 작업 현황이 아니다. mtime은 해석 날짜가
  아니다. evidence는 저장값·SHA·출처만 제공하며 실패·0·false를 성공으로 해석하지 않는다.
- 다음 파일은 질문과 관련된 것만 읽는다. 전체 HANDOFF/로그/JSON 일괄 읽기는 피한다.
  최신 핸드오프의 정정 내용과 대상 모델을 확인한다. 특히 `HANDOFF_20260907.md` §1은
  FreeFlow 중력의 옛 설명을 정정하지만 Icepak은 확인 범위 밖이다. 실제 설정 변경 전에는
  대상 프로젝트를 확인한다. 기록된 결과를 현재 호스트에서 재검증된 결과로 표현하지 않는다.
- 솔버 실행·물리 모델 수정에는 기존 `motor-thermal-hybrid` 스킬을 적용한다.
  JEET 작업에는 `mlxperPJT/JEET/AGENTS.md`가 있으면 읽는다. 실제 존재 여부를 확인한다.
- 상태 조회는 solver·SSH·프로세스 정리·Git 동기화를 자동 실행하지 않는다.
  `AGENTS.md`를 보존하고, 커밋 요청 시 eMach의 저장소별 작성자 `enjoyneer87`을 확인한다.

이 스킬 원본은 레포 `.agents/skills/emach-ops/`에 있다. 다른 PC는 이 폴더를
`$CODEX_HOME/skills/emach-ops`(미설정 시 `~/.codex/skills/emach-ops`)로 복사하면 된다.
도구는 해당 checkout의 `mlxperPJT/thermal/ops.py`를 사용한다.
