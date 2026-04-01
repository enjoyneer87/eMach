## Plan: Airgap 복원 및 문서 정합성 회복

CAD 인식 저하의 직접 원인인 analysis_airgap 문법 붕괴와 임포트 경로 불일치를 먼저 복구하고, 그 다음 리팩토링 문서와 PUML을 현재 코드 기준으로 정합화한다. 기능 복구를 최우선으로 두고, 문서/다이어그램은 코드 기준 단일 진실원칙으로 맞춘다.

**Steps**
1. Phase 1: Airgap 모듈 복원
2. [Class/pyMotorGeo/analysis_airgap.py](Class/pyMotorGeo/analysis_airgap.py)에서 stray docstring 경계와 깨진 블록을 정리해 파싱 가능 상태로 복구한다.
3. [Class/pyMotorGeo/analysis_airgap.py](Class/pyMotorGeo/analysis_airgap.py)의 import 스타일을 패키지 전체 관례와 통일한다. 필요 시 from .core / from core 양쪽 실행 경로를 지원하는 방식을 택한다.
4. Phase 2: 기능 회귀 검증
5. py_compile 및 최소 임포트 체인을 검증하고, 에어갭 추정 핵심 함수 find_airgap_radius, find_airgap_by_arc_span, split_stator_rotor_by_arc_span를 실제 DXF 입력 흐름으로 재검증한다. depends on 1.
6. [Class/pyMotorGeo/test_refactoring_notebook.ipynb](Class/pyMotorGeo/test_refactoring_notebook.ipynb)와 [mlxperPJT/pyMotorGeo_v1.ipynb](mlxperPJT/pyMotorGeo_v1.ipynb)의 airgap 관련 셀을 재실행해 CAD 분리 정확도와 후속 단계 연동을 확인한다. depends on 5.
7. Phase 3: Markdown 정합화
8. 조사 결과 기준으로 리팩토링 문서의 모순을 수정한다: 완료율/단계 상태, 링크, 오타, 중복 설명. parallel with 6.
9. 우선 수정 파일: [REFACTORING_PROGRESS.md](REFACTORING_PROGRESS.md), [README_REFACTORING_COMPLETE.md](README_REFACTORING_COMPLETE.md), [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md), [REFACTORING_COMPLETION_REPORT.md](REFACTORING_COMPLETION_REPORT.md).
10. Phase 4: PUML 정합화
11. 클래스명 및 함수명 불일치를 현재 코드 기준으로 교정한다. 특히 함수형 모듈을 클래스처럼 그린 부분을 명확히 정리한다. depends on 1.
12. 우선 수정 파일: [Class/pyMotorGeo_Architecture.puml](Class/pyMotorGeo_Architecture.puml), [Class/pyMotorGeo_CompletionStatus.puml](Class/pyMotorGeo_CompletionStatus.puml). 이후 [Class/pyMotorGeo_Dependencies.puml](Class/pyMotorGeo_Dependencies.puml), [Class/pyMotorGeo_Workflow.puml](Class/pyMotorGeo_Workflow.puml), [Class/pyMotorGeo_DataTransform.puml](Class/pyMotorGeo_DataTransform.puml) 순으로 정렬한다.
13. Phase 5: 최종 검증 및 리포트
14. Python 문법/임포트 검증, 노트북 핵심 셀 재실행, 문서 링크/용어 일관성, PUML 렌더링 가능성을 최종 점검한다. depends on 8 and 11.
15. 결과를 기존 실행 보고서에 델타 형태로 반영하거나 별도 점검 보고서로 요약한다.

**Relevant files**
- [Class/pyMotorGeo/analysis_airgap.py](Class/pyMotorGeo/analysis_airgap.py) — 공극 탐지 및 분리 핵심 로직 복원 대상
- [Class/pyMotorGeo/analysis.py](Class/pyMotorGeo/analysis.py) — analysis_airgap 재수출/호출 체인 확인
- [Class/pyMotorGeo/__init__.py](Class/pyMotorGeo/__init__.py) — 패키지 임포트 체인 확인
- [Class/pyMotorGeo/test_refactoring_notebook.ipynb](Class/pyMotorGeo/test_refactoring_notebook.ipynb) — 리팩토링 검증 노트북
- [mlxperPJT/pyMotorGeo_v1.ipynb](mlxperPJT/pyMotorGeo_v1.ipynb) — 실제 CAD 분석 워크플로 노트북
- [REFACTORING_PROGRESS.md](REFACTORING_PROGRESS.md) — 상태 모순 정리 1순위
- [README_REFACTORING_COMPLETE.md](README_REFACTORING_COMPLETE.md) — 링크/문구 정리
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) — 오타/깨진 표기 정리
- [REFACTORING_COMPLETION_REPORT.md](REFACTORING_COMPLETION_REPORT.md) — 중복/정합화
- [Class/pyMotorGeo_Architecture.puml](Class/pyMotorGeo_Architecture.puml) — 클래스/함수 불일치 교정 핵심
- [Class/pyMotorGeo_CompletionStatus.puml](Class/pyMotorGeo_CompletionStatus.puml) — 단계 상태 정합화
- [Class/pyMotorGeo_Dependencies.puml](Class/pyMotorGeo_Dependencies.puml) — 의존성 관계 검증
- [Class/pyMotorGeo_Workflow.puml](Class/pyMotorGeo_Workflow.puml) — 파이프라인 명칭 정합화
- [Class/pyMotorGeo_DataTransform.puml](Class/pyMotorGeo_DataTransform.puml) — 데이터 흐름 타입 정합화

**Verification**
1. python -m py_compile [Class/pyMotorGeo/analysis_airgap.py](Class/pyMotorGeo/analysis_airgap.py) 성공 확인
2. 패키지 임포트 체인 검증: pyMotorGeo import 및 analysis_airgap 함수 호출 smoke test
3. 두 노트북에서 airgap/분리/토폴로지 핵심 셀 재실행 후 예외 0건 확인
4. Markdown 상호 참조 링크 점검 및 상태 수치 일치 확인
5. PUML 파일 렌더 문법 점검 및 클래스/함수 명칭 정합성 체크리스트 통과

**Decisions**
- 포함 범위: airgap 복원, markdown 정합화, puml 정합화
- 제외 범위: 새로운 분석 알고리즘 설계, UI 재디자인, 성능 최적화 대공사
- 우선순위: 실행 가능성 회복 analysis_airgap > 노트북 회귀 검증 > 문서/다이어그램 정합화

**Further Considerations**
1. import 정책 고정 필요: 패키지 실행 우선(relative) vs 노트북 직접 실행 우선(absolute). 권장: 양쪽 호환 래퍼 방식.
2. 문서 단일 진실원칙: 진행 문서 1개를 기준으로 하고 나머지는 요약/링크 중심으로 축소 권장.
3. PUML 유지 전략: 아키텍처 다이어그램은 클래스/함수 혼합 표기를 명시해 향후 회귀 방지.