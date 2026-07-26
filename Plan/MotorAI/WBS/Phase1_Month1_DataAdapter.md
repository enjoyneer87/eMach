# 📅 Phase 1 - Month 1: 데이터 어댑터 구축

**기간:** 2026-04-01 ~ 2026-04-30  
**목표:** Motor-CAD `.h5` 데이터 → PyVista/VTK 변환 어댑터 완성  
**키워드:** `h5py` `pyvista` `UnstructuredGrid` `stpyvista` `Streamlit` `PhysicsNeMo` `MeshGraphNet`

> [!important]
> 현재 실행은 상세 일별 목록 전체가 아니라 리베이스된 실행 기준으로 진행합니다.
> - 실행 기준: [[Phase1_Month1_DataAdapter_Baseline_KO]]
> - 핵심: 필수 8개 항목 + Gate A/B/C 통과 중심
> - 학습 고도화/배포 문서화는 Month 2+ 백로그로 이관

---

## ✅ 월간 완료 기준

- [ ] `.h5` → `pyvista.UnstructuredGrid` 변환 성공
- [ ] 자속밀도 B 컬러맵 시각화 (로컬 PyVista)
- [ ] 단면 절단(Clipping) 기능 동작
- [ ] `.vtu` 저장 및 ParaView 검증
- [ ] Streamlit에서 h5 업로드 → 3D 뷰 표시
- [ ] MGN 학습용 graph dataset(`x`, `edge_index`, `edge_attr`, `y`) 추출 성공
- [ ] `physicsnemo_train_from_pyMCAD.ipynb` 입력 규격과 데이터 계약 일치 확인
- [ ] pytest 단위 테스트 5개 이상 통과
- [ ] README.md 및 Docker 실행 문서

---

## 📆 Week 1 (Apr 1–5): 환경 설정 & 데이터 구조 파악

> [!info]- 🎯 Week 1 목표
> Motor-CAD `.h5` 파일의 내부 구조를 완전히 파악하고 PyVista 개발 환경을 구축한다.

### Day 1 · 2026-04-01 (수)

> [!todo]- 🤖 Agent A 임무
> - [ ] `h5py`로 .h5 파일 모든 키/계층 자동 출력 탐색 스크립트 작성
> - [ ] Point 데이터(x,y,z 좌표)와 Cell 데이터(connectivity) 키 이름 식별
> - [ ] 물리량 키 목록 추출 (자속밀도 B, 전류밀도 J, 온도 T 등)

> [!todo]- 🤖 Agent B 임무
> - [ ] Python 가상환경 + `requirements.txt` 작성 (`pyvista`, `h5py`, `numpy`, `streamlit`)
> - [ ] GitHub 레포 초기화 및 `.gitignore` (.h5 파일 제외)
> - [ ] 프로젝트 폴더 구조 생성 (`src/`, `tests/`, `data/`, `notebooks/`)
- [ ] MGN 타깃 필드(Bx, By)와 선택 필드(A, J) 후보 키 매핑표 작성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] PyVista 공식 문서 홈 훑기: https://docs.pyvista.org
> - [ ] `UnstructuredGrid` vs `PolyData` 개념 차이 머릿속에 넣기
> - [ ] 내 `.h5` 파일 직접 열어서 어떤 키가 있는지 확인

---

### Day 2 · 2026-04-02 (목)

> [!todo]- 🤖 Agent A 임무
> - [ ] PyVista `UnstructuredGrid` 최소 예제 (6노드 육면체)
> - [ ] VTK 셀 타입 참조표 정리 (HEXAHEDRON, TETRA, WEDGE 등)
> - [ ] Motor-CAD element type → VTK cell type 매핑 테이블 초안
- [ ] SciML 실행 환경 분리안 정의 (`torch`, `torch-geometric`, `physicsnemo` 버전 고정)

> [!todo]- 🤖 Agent B 임무
> - [ ] `h5py`로 읽기 → numpy 배열 추출 → dict 반환 함수 작성
> - [ ] 데이터 shape/dtype 자동 검사 & 로그 출력 함수
- [ ] 시간 스텝 정렬 규칙(`time_index` 우선, 없으면 `solution`)을 데이터 계약으로 문서화
> - [ ] 단위계 메타데이터 추출 (mm, T, A/m² 등)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] VTK 데이터 모델: `PointData`(노드 기반) vs `CellData`(요소 기반) 개념
> - [ ] 내 FNO 모델이 예측하는 물리량이 PointData인지 CellData인지 확인
> - [ ] PyVista 예제 코드 1개 직접 실행 (pip install 후 첫 플롯)

---

### Day 3 · 2026-04-03 (금)

> [!todo]- 🤖 Agent A 임무
> - [ ] 원통 좌표계(r, θ, z) → 직교 좌표계(x, y, z) 변환 공식 구현
> - [ ] 변환된 좌표를 `np.float32` 타입으로 정규화 (웹 전송용 최적화)
- [ ] 그래프 변환 어댑터 초안: node feature/edge feature 추출 함수 스켈레톤
> - [ ] 좌표 변환 단위 테스트: 기준 점 3개로 검증

> [!todo]- 🤖 Agent B 임무
> - [ ] `MotorDataConfig` dataclass 설계 (파일 경로, 좌표계, 물리량 키 목록)
> - [ ] CLI 초안: `python main.py --h5 data.h5 --output result.vtu`
- [ ] `.h5`/`.txt` -> graph 변환 스모크 테스트(1케이스) 실행
> - [ ] 프로젝트 디렉토리 구조 Python 패키지 초기화 (`__init__.py`)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Motor-CAD 설명서에서 좌표계 정의 부분 확인
> - [ ] 내 h5의 좌표가 원통계인지 직교계인지 확인
> - [ ] NumPy 브로드캐스팅으로 벡터 연산 최적화 개념 복습

---

### Day 4 · 2026-04-07 (월)

> [!todo]- 🤖 Agent A 임무
> - [ ] `MotorH5Adapter` 클래스 뼈대 설계 (메서드 시그니처만)
>   - `load_h5()`, `to_unstructured_grid()`, `save_vtu()`, `get_scalar_names()`
- [ ] dataset contract validator 초안(필수 키/shape 검사) 추가
> - [ ] 클래스 docstring 및 type hints (Google docstring 형식)
> - [ ] 에러 처리 패턴 설계 (FileNotFoundError, KeyError 등)

> [!todo]- 🤖 Agent B 임무
> - [ ] `UnstructuredGrid` 생성 전체 플로우 코드
>   - `points(N×3)`, `cells(connectivity)`, `celltypes` 배열
> - [ ] `pv.CellType.HEXAHEDRON` 등 상수 활용 셀 정의 예제

- [ ] MGN 학습 입력 품질 점검 항목 추가 (고립 노드/에지 누락/타깃 결측)
> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 객체지향 단일 책임 원칙(SRP) 적용 방법 찾아보기
> - [ ] 내 FNO 코드의 `__getitem__` 메서드가 어떻게 동작하는지 리뷰
> - [ ] scikit-learn Estimator 패턴 보고 클래스 설계 영감 얻기

---

### Day 5 · 2026-04-08 (화)

> [!todo]- 🤖 Agent A 임무
> - [ ] 실제 .h5 노드 좌표 → PyVista `points` 배열 매핑 구현
> - [ ] 실제 .h5 element connectivity → PyVista `cells` 배열 매핑
- [ ] `physicsnemo_train_from_pyMCAD.ipynb` 실행 전제조건/입력경로 가이드 추가
> - [ ] 인덱싱 주의: 0-indexed vs 1-indexed 변환 처리

> [!todo]- 🤖 Agent B 임무
> - [ ] `pytest` 기반 단위 테스트 파일 (`test_adapter.py`)
>   - 좌표 변환 정확도, 셀 수, 포인트 수 검증
- [ ] End-to-End 통합 테스트: `Mag_*.h5` -> graph dataset -> MGN 학습 입력 검증
> - [ ] GitHub Actions CI 워크플로우 초안

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] pytest 기초 사용법 익히기 (assert, fixtures)
> - [ ] 내 모터의 메쉬 규모 파악: 노드/요소 수, 요소 타입
> - [ ] Week 1 회고: 배운 것, 막힌 것, 내일 할 것 메모

---

## 📆 Week 2 (Apr 6–10): 어댑터 클래스 핵심 구현

> [!info]- 🎯 Week 2 목표
> `MotorH5Adapter` 핵심 기능 구현 + 실제 h5 데이터로 첫 `.vtu` 파일 생성

### Day 6 · 2026-04-09 (수)

> [!todo]- 🤖 Agent A 임무
> - [ ] `add_point_data()`: PointData 노드별 물리량 매핑
>   - 자속밀도 Bx, By, Bz → 벡터 필드
- [ ] SciML 학습용 선택 프로파일(옵션) 정의: CPU/GPU 실행 분리
>   - `|B|` 크기 → 스칼라 필드
> - [ ] `grid.point_data["B_magnitude"] = ...` 형식으로 추가

> [!todo]- 🤖 Agent B 임무
> - [ ] `add_cell_data()`: CellData 요소별 물리량 매핑
>   - 전류밀도 Jz, 동손(Copper Loss), 철손(Iron Loss)
- [ ] MGN 데이터셋 품질 리포트(필드 커버리지/누락률) 추가
> - [ ] `PolyData` ↔ `UnstructuredGrid` 간 변환 헬퍼 함수

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 자기 해석에서 B 벡터는 Point vs Cell 중 어디에 정의되나?
> - [ ] PyVista Plotting 기초: `plotter.add_mesh(cmap='rainbow')` 실습
> - [ ] 물리적으로 의미있는 컬러맵 찾기 (jet vs RdBu vs viridis)

---

### Day 7 · 2026-04-10 (목)

> [!todo]- 🤖 Agent A 임무
> - [ ] `batch_add_fields()`: 다중 물리량 일괄 처리
> - [ ] 물리량 이름 매핑 딕셔너리: h5 키 → 표준 이름
- [ ] Month 2용 MGN baseline 실행 체크리스트(학습/추론/평가) 인계
> - [ ] 단위 변환 지원: T(테슬라), A/m², °C

> [!todo]- 🤖 Agent B 임무
> - [ ] `save_vtu()`: `.vtu` 파일로 저장
> - [ ] `save_vtk()`: 레거시 `.vtk` 파일 저장 옵션
> - [ ] 파일 크기 추정 함수 (저장 전 메모리 사용량 경고)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] `.vtu`(UnstructuredGrid XML) vs `.vtk`(레거시) 파일 형식 차이
> - [ ] ParaView 설치하기 (아직 안 했다면)
> - [ ] 첫 번째 .vtu 파일을 ParaView에서 열어보기 시도

---

### Day 8 · 2026-04-13 (월)

> [!todo]- 🤖 Agent A 임무
> - [ ] 시간 스텝 처리: 과도 해석 결과 시퀀스 (t=0, t=1, ...)
> - [ ] `pv.MultiBlock` 으로 멀티 스텝 관리

> [!todo]- 🤖 Agent B 임무
> - [ ] 대용량 h5 청크(chunk) 단위 로딩 구현
> - [ ] lazy loading 패턴: 필요한 물리량만 선택적 로드

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 내 Motor-CAD 해석: 정상 상태 vs 과도 해석 파악
> - [ ] `h5py` chunked dataset 개념 이해
> - [ ] 포스트프로세싱에서 가장 중요한 물리량 Top 5 직접 리스트업

---

### Day 9 · 2026-04-14 (화)

> [!todo]- 🤖 Agent A 임무
> - [ ] 어댑터 전체 통합 테스트: `.h5` → `.vtu` 파이프라인 실행
> - [ ] 처리 시간 측정 및 로그 (노드 수, 요소 수, 소요 시간)

> [!todo]- 🤖 Agent B 임무
> - [ ] 에러 케이스 단위 테스트 (잘못된 h5 구조, 누락 키 등)
> - [ ] 테스트용 더미 h5 파일 생성 스크립트

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Python `logging` 모듈 심화: 핸들러, 포매터, 레벨 설정
> - [ ] 파이프라인 실행 결과 직접 검토 및 이상한 부분 메모
> - [ ] 통합 테스트 결과 스크린샷 남기기

---

### Day 10 · 2026-04-15 (수)

> [!todo]- 🤖 Agent A 임무
> - [ ] `DataQualityChecker` 클래스
>   - NaN/Inf 값 감지
>   - 물리량이 예상 범위 벗어나면 경고
>   - 메쉬 비정상 요소 감지

> [!todo]- 🤖 Agent B 임무
> - [ ] `README.md` 작성: 어댑터 사용법 및 예제
> - [ ] API 문서 자동 생성 (`pdoc3` 또는 `mkdocs`)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 내 모터에서 자속밀도 포화 영역(2T 이상)이 어디인지 파악
> - [ ] PyVista `clip()`, `slice()`, `threshold()` 각각 실행해보기
> - [ ] Week 2 회고 및 Week 3 계획

---

## 📆 Week 3 (Apr 13–17): 시각화 검증 & PyVista 플로팅

> [!info]- 🎯 Week 3 목표
> 변환된 `.vtu` 데이터를 PyVista/ParaView로 검증하고 로컬 3D 시각화 완성

### Day 11 · 2026-04-16 (목)

> [!todo]- 🤖 Agent A 임무
> - [ ] 자속밀도 |B| 컬러맵 시각화 (jet/rainbow/RdBu)
> - [ ] 스칼라 바(Scalar Bar) 및 레이블 설정
> - [ ] 카메라 preset: 정면/측면/상단 뷰 저장

> [!todo]- 🤖 Agent B 임무
> - [ ] 벡터 화살표(Arrow Glyph): B 벡터 방향 시각화
> - [ ] 화살표 밀도 서브샘플링 로직 (너무 빽빽하지 않게)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 직접 PyVista로 자속밀도 그려보기
> - [ ] 예상한 위치에 높은 B 값이 나오나? 물리적으로 검증
> - [ ] ANSYS Maxwell 결과와 눈으로 비교

---

### Day 12 · 2026-04-17 (금)

> [!todo]- 🤖 Agent A 임무
> - [ ] `clip_with_plane()`: XZ/YZ/XY 단면 시각화
> - [ ] `slice_along_axis()`: 축 방향 슬라이스 뷰
> - [ ] 단면 위치 인터랙티브 슬라이더 위젯 (PyVista GUI)

> [!todo]- 🤖 Agent B 임무
> - [ ] Isosurface 추출: `mesh.contour(isosurfaces=5)`
> - [ ] 등치면 렌더링 최적화 (5개 이하로 제한)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Isosurface vs Contour vs Slice 개념 차이
> - [ ] 모터 설계에서 주로 보는 단면: 어느 평면이 중요한가?
> - [ ] SolverX 같은 CAE 툴이 어떤 인터랙션을 제공하는지 리서치

---

### Day 13 · 2026-04-20 (월)

> [!todo]- 🤖 Agent A 임무
> - [ ] 복수 물리량 비교 뷰: 2분할 화면 (B vs J 동시 표시)
> - [ ] 특정 노드/요소 선택 시 수치 출력 (Pick 기능)

> [!todo]- 🤖 Agent B 임무
> - [ ] 결과 이미지 자동 저장: `plotter.screenshot("result_B.png")`
> - [ ] HTML 보고서 자동 생성: 스크린샷 + 수치 테이블

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 내 모터에서 가장 관심있는 물리량 Top 5 직접 선정
> - [ ] 어떤 단면에서 어떤 물리량을 볼 때 설계 결정이 쉽나?
> - [ ] 실무에 필요한 최소한의 뷰 목록 만들기

---

### Day 14 · 2026-04-21 (화)

> [!todo]- 🤖 Agent A 임무
> - [ ] 성능 벤치마크: 노드 1만/10만/100만 규모별 렌더링 시간
> - [ ] 대용량 데이터 경량화: `mesh.decimate_pro(0.5)`

> [!todo]- 🤖 Agent B 임무
> - [ ] `UnstructuredGrid` → Three.js `BufferGeometry` JSON 변환 함수 (Phase 2 준비)
> - [ ] 좌표 + 인덱스 + 스칼라 → `Float32Array` 출력 함수

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Mesh Decimation이 물리량 정확도에 어떤 영향을 주는지
> - [ ] Three.js `BufferGeometry` 공식 문서 개념만 읽어보기
> - [ ] Phase 2에서 Babylon.js로 넘어갈 때 필요한 데이터 형식 파악

---

### Day 15 · 2026-04-22 (수)

> [!todo]- 🤖 Agent A 임무
> - [ ] 엣지 케이스 처리: 빈 데이터, single element, 2D 메쉬
> - [ ] 다양한 Motor-CAD 모델 타입 테스트 (IPMSM, SPMSM, IM)

> [!todo]- 🤖 Agent B 임무
> - [ ] Week 3 통합 테스트 보고서 작성
> - [ ] 알려진 이슈 GitHub Issues 등록

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Week 3 회고 작성
> - [ ] FNO 모델 예측 물리량과 어댑터 출력의 호환성 확인
> - [ ] Month 1 목표 4가지 중 현재 달성도 자체 평가

---

## 📆 Week 4 (Apr 20–30): Streamlit 연동 & Month 1 마무리

> [!info]- 🎯 Week 4 목표
> 구현된 어댑터를 Streamlit과 연동하고 Month 1 결과물 정리

### Day 16 · 2026-04-23 (목)

> [!todo]- 🤖 Agent A 임무
> - [ ] `stpyvista` 설치 및 기본 예제 실행
> - [ ] PyVista plotter → Streamlit embedding 기본 패턴

> [!todo]- 🤖 Agent B 임무
> - [ ] Streamlit 앱 기본 구조: 파일 업로드 → 변환 → 표시
> - [ ] `st.file_uploader(type=["h5"])` → 어댑터 연동 플로우

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Streamlit 공식 튜토리얼 30분 훑기
> - [ ] stpyvista GitHub 예제 페이지 보기
> - [ ] 모터 엔지니어에게 가장 직관적인 UI 손그림으로 스케치

---

### Day 17 · 2026-04-24 (금)

> [!todo]- 🤖 Agent A 임무
> - [ ] 사이드바: 물리량 선택 드롭다운, 컬러맵 선택
> - [ ] 슬라이더: 시간 스텝 선택 (과도 해석)
> - [ ] 버튼: "단면 보기", "벡터 보기" 토글

> [!todo]- 🤖 Agent B 임무
> - [ ] 세션 상태 관리: `st.session_state` 활용 (파일 재로드 방지)
> - [ ] 캐싱: `@st.cache_data`로 변환 결과 캐싱

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Streamlit `session_state` 개념 이해
> - [ ] 캐싱 없으면 뭐가 느려지는지 직접 체험
> - [ ] UI 첫인상: 동료 엔지니어가 보면 바로 이해 가능한가?

---

### Day 18 · 2026-04-27 (월)

> [!todo]- 🤖 Agent A 임무
> - [ ] 수치 정보 패널: 선택 노드/요소 물리량 표 (`st.dataframe`)
> - [ ] 상단 KPI 카드: 최대 B, 최대 J, 최대 온도, 토크

> [!todo]- 🤖 Agent B 임무
> - [ ] 데이터 내보내기: 현재 뷰 데이터 → CSV 다운로드
> - [ ] 스크린샷 버튼: 현재 3D 뷰 → PNG 저장

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 매일 Motor-CAD에서 보는 수치 → KPI 카드 구성
> - [ ] Plotly 간단 차트 (`st.plotly_chart`) 사용해보기
> - [ ] Streamlit 배포 옵션 알아보기 (Cloud, 로컬 서버)

---

### Day 19 · 2026-04-28 (화)

> [!todo]- 🤖 Agent A 임무
> - [ ] End-to-End 통합 테스트: 실제 Motor-CAD 데이터
> - [ ] 로딩 속도 목표: 1MB h5 → 5초 이내 렌더링

> [!todo]- 🤖 Agent B 임무
> - [ ] Docker 컨테이너화: `Dockerfile` 작성
> - [ ] `docker-compose.yml` (앱 + 볼륨 마운트)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Docker 기초: 이미지, 컨테이너, 볼륨 차이
> - [ ] `docker run` vs `streamlit run` 차이 체험
> - [ ] Month 2 배울 것들 미리 훑어보기 (Babylon.js, TypeScript)

---

### Day 20 · 2026-04-29 (수) — 🏁 Monthly Review

> [!todo]- 🤖 Agent A 임무
> - [ ] Month 1 완성 기능 목록 문서화 (마크다운)
> - [ ] 알려진 이슈 및 한계 정리 / GitHub Issues 업데이트

> [!todo]- 🤖 Agent B 임무
> - [ ] 코드 품질 점검: `pylint`, `mypy` 실행 및 리포트
> - [ ] 전체 소스코드 정리 및 최종 커밋 (태그: `v0.1.0`)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Month 1 회고 (KPT: Keep / Problem / Try)
> - [ ] 다음 달 스택 미리 설치: Node.js, TypeScript, Babylon.js
> - [ ] 오늘 만든 것이 처음 아이디어 대비 얼마나 나아졌나 자체 평가

---

*→ 다음: [[Phase1_Month2_Streamlit]]*
