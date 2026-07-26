# 📌 Phase 1 - 데이터 어댑터 실행 베이스라인 (단계형)

**목적:** 과적재된 일정 표현을 단계 중심으로 재정렬해, 검증 가능한 산출물을 순차적으로 확정한다.  
**원칙:** 제품 필수 경로 우선(입력/변환/시각화/검증), 연구 확장(MGN 학습/배포)은 다음 단계로 이관.

---

## ✅ Phase 1 필수 완료 항목 (8개)

- [x] `.h5` -> `pyvista.UnstructuredGrid` 변환 성공
- [ ] 자속밀도 B 컬러맵 시각화 (로컬 PyVista)
- [ ] 단면 절단(Clipping) 기능 동작
- [ ] `.vtu` 저장 및 ParaView 검증
- [x] graph 어댑터 스켈레톤(`x`, `edge_index`, `edge_attr`, `y`) 구현
- [ ] dataset contract validator 초안(필수 키/shape 검사)
- [ ] `.h5`/`.txt` -> graph 1케이스 스모크 테스트 통과
- [ ] pytest 단위 테스트 5개 이상 통과

---

## 🧭 단계별 실행 계획

### Stage 1: 데이터 구조/계약 고정
- [ ] `.h5` 키 맵 인벤토리 + 필수 필드 테이블 작성
- [ ] 시간 스텝 정렬 규칙 고정 (`time_index` 우선, 없으면 `solution`)
- [ ] MGN 타깃 필드(Bx, By) 기준 키 매핑 초안

### Stage 2: 어댑터 코어 구현
- [ ] `MotorH5Adapter` 핵심 메서드 구현 (`load_h5`, `to_unstructured_grid`, `save_vtu`)
- [ ] 좌표/셀 타입 변환 규칙 코드화
- [ ] `.vtu` 내보내기 성공

### Stage 3: 시각화 + 그래프 스켈레톤
- [ ] PyVista 컬러맵/클리핑 검증
- [ ] graph feature 추출 스켈레톤 구현
- [ ] validator 초안 추가

### Stage 4: 통합 검증/테스트
- [ ] 1케이스 E2E 스모크 (`h5 -> vtu`, `h5/txt -> graph`)
- [ ] pytest 5개 이상 통과
- [ ] 다음 단계 인계 노트 작성

---

## 🚦 게이트 (Go/No-Go)

### Gate A (Stage 2 종료)
- Grid 변환/저장 성공 여부
- 실패 시: 시각화/ML 작업 신규 착수 금지

### Gate B (Stage 3 종료)
- 컬러맵/클리핑 + graph 스켈레톤 동시 검증
- 실패 시: 배포/문서화 항목 이연

### Gate C (Stage 4 종료)
- pytest/스모크 테스트 통과
- 다음 단계 착수 승인

---

## 📦 다음 단계 이관 백로그

- Streamlit h5 업로드 -> 3D 뷰 완성형 연동
- `physicsnemo_train_from_pyMCAD.ipynb` 실행 전제조건/입력경로 문서 고도화
- E2E 통합 테스트(학습 입력 검증 포함)
- Docker/README 운영 문서 완성
- MGN 데이터셋 품질 리포트 자동화
- SciML CPU/GPU 프로파일 분리안 구체화

---

## 🧾 증빙 규칙

- 코드 증빙: 변경 파일 경로 + 핵심 함수명
- 검증 증빙: 테스트 명령 + pass/fail 요약
- 상태 반영: Notion `상태`(또는 `상태_작업`)는 게이트 기준으로 업데이트
