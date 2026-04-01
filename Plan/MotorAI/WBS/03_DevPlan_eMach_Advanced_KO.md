# eMach 전체 개발플랜 고도화안 v1.0

작성일: 2026-04-01  
대상 저장소: Emlab_emach  
기준 문서:
- Plan/MotorAI/motor_ai_roadmap_bygemini.md
- Plan/MotorAI/WBS/02_DevPlan_eMach_Compatibility_KO.md
- Plan/MotorAI/WBS/Phase1_Month1_DataAdapter.md
- Plan/MotorAI/WBS/Phase1_Month2_Streamlit.md

---

## 1. 고도화 목적

본 문서는 기존 로드맵의 큰 방향(웹 네이티브 CAE + AI)을 유지하면서, eMach 중심의 실제 실행 체계로 고도화한다.
핵심은 아래 3가지를 하나의 프로그램으로 묶는 것이다.

1. 다중 패키지 호환 허브(eMach <-> Pyleecan/SyR-e/PyMotorCAD/PyAEDT)
2. SciML 학습/추론 루프(PhysicsNeMo MeshGraphNet 중심, FNO 병행 가능)
3. 웹 시각화/실시간 인터랙션(FastAPI + Streamlit/Babylon.js)

---

## 2. 북극성 목표와 단계별 성과

### 2.1 북극성 목표 (12개월)

- Geometry -> Solver -> AI -> Web까지 단일 파이프라인으로 연결
- 설계 변경 후 10분 이내에 "재해석 또는 surrogate 추론 + 시각화" 결과 확인
- 핵심 벤치마크 10케이스 기준, 호환성/정확도/성능 KPI 동시 충족

### 2.2 단계별 성과 목표

- Stage A (Q1): 데이터 계약/브리지/검증 자동화 고정
- Stage B (Q2): 시각화 및 서비스 API 성능 확보
- Stage C (Q3): Warp + SciML 결합 기반의 실시간 물리 연산 루프
- Stage D (Q4): 패키징/배포/운영 기준 확립

---

## 3. 타깃 아키텍처 (실행 관점)

### 3.1 레이어별 책임

1. Data Source Layer
- SyR-e, Pyleecan, Motor-CAD, Maxwell 원천 데이터 수집
- 표준 입력: DXF, mot/aedt, Mag_*.h5, MagTransient*.txt

2. Interchange Layer (eMach Core)
- GeometryPayload/SemanticPayload/ExecutionPayload/MLDatasetPayload 관리
- 파서/정규화/브리지/검증 책임 집중

3. Compute Layer (AI + Solver)
- PhysicsNeMo MGN 학습 및 추론
- FNO 병행 실험 트랙
- NVIDIA Warp 기반 가속 연산 및 미분 가능 실험

4. Service Layer
- FastAPI 추론 및 결과 API
- 실행 상태/오류 taxonomy/리포트 API

5. Visualization Layer
- 내부: Streamlit + stpyvista
- 외부 확장: Babylon.js + Shader + (후속) WebAssembly/WebGPU

### 3.2 필수 계약(Contract) 세트

- Geometry Contract v1
- Semantic Contract v1 (optional, non-blocking)
- Execution Contract v1
- Result Contract v1
- MLDataset Contract v1

---

## 4. 프로그램 구조 (Workstream)

### WS-A. Interoperability Core (eMach 중심)

목적:
- 5패키지 간 데이터 왕복 호환의 기준선을 고정

핵심 산출물:
- contracts.py
- pyleecan_bridge.py, motorcad_bridge.py, aedt_bridge.py
- round-trip validator + benchmark 리포트

완료 기준:
- 10 benchmark 중 9개 이상 호환성 통과
- geometry drift 평균 5% 이하

### WS-B. CAE Automation

목적:
- PyMotorCAD/PyAEDT 실행 자동화와 실패 복구 체계 구축

핵심 산출물:
- execution adapter
- run profile(standard/high_accuracy/fast_debug)
- 실패 taxonomy + 재시도 정책

완료 기준:
- 필수 케이스 자동 실행 성공률 90% 이상

### WS-C. SciML Data & Training (PhysicsNeMo MGN)

목적:
- pyMCAD 산출을 그래프 데이터로 표준화하고 MGN 학습 경로를 제품화

핵심 산출물:
- ml_dataset_adapter
- mgn training runner (physicsnemo_train_from_pyMCAD 기반)
- checkpoint + metrics + provenance

완료 기준:
- 재현 성공률 90% 이상
- |B| MAE, Bx/By MAE 기준 충족

### WS-D. Surrogate Serving

목적:
- 학습 모델을 API로 서비스하고 시각화 클라이언트와 연결

핵심 산출물:
- inference API (sync/async)
- batch inference endpoint
- 결과 캐시 + 모델 버전 API

완료 기준:
- 단일 케이스 추론 응답시간 SLO 달성

### WS-E. Visualization Productization

목적:
- 내부 분석 UX(Streamlit)에서 외부 확장 UX(Babylon.js)로 이관 가능 구조 확보

핵심 산출물:
- Compare View(GT vs MGN/FNO)
- 오차 맵, 단면, 애니메이션, KPI 카드
- Float32Array 기반 데이터 전달 스펙

완료 기준:
- 엔지니어 사용 시나리오 5개 이상 통과

### WS-F. Warp & Differentiable Physics

목적:
- 실시간 물리 연산/민감도 기반 설계 가이드 프로토타입 확보

핵심 산출물:
- Warp kernel prototype
- differentiable objective demo
- inverse guidance PoC

완료 기준:
- 기준 사례에서 미분 가능 루프 1개 이상 안정 실행

### WS-G. Quality, MLOps, DevOps

목적:
- 재현성/신뢰성/배포성을 보장하는 운영 기반 구축

핵심 산출물:
- 버전 매트릭스(Python/torch/physicsnemo/solver)
- 테스트 파이프라인(unit/contract/integration/regression/sciml)
- Docker 배포 프로파일

완료 기준:
- 릴리즈 후보(RC)에서 치명 이슈 0건

---

## 5. 통합 일정 (12개월)

## Q1. 기반 고정 (M1-M3)

M1:
- 계약 동결(Geometry/Semantic/Execution/Result/MLDataset)
- pyMCAD h5/txt -> graph dataset 변환 경로 확정
- vtu exporter 및 품질 검사기 정식화

M2:
- Streamlit 대시보드 핵심 UX 완성
- GT vs MGN 비교 뷰, 오차 통계(MAE/RMSE) 표준화
- 케이스 레지스트리/배치 처리 도입

M3:
- Babylon.js 기술검증 시작
- FastAPI 연동을 고려한 데이터 전송 스펙(typed array) 동결

Gate-Q1:
- 호환성 80% 이상, MGN baseline 재현 성공, 내부 대시보드 운영 가능

## Q2. 서비스/시각화 성능화 (M4-M6)

M4:
- FastAPI 바이너리 스트리밍 경로 구축
- 추론 API 및 모델 버전 관리 API 구현

M5:
- Shader 기반 컨투어/컬러맵 고도화
- 대규모 메쉬 렌더링 성능 튜닝

M6:
- 인터랙티브 UI(clip, tooltip, scalar bar) 완성
- 사용자 시나리오 기반 UX 검증

Gate-Q2:
- API + 시각화 일체형 데모 안정화

## Q3. AI/솔버 심화 통합 (M7-M9)

M7:
- NVIDIA Warp 커널 초안 + GPU 가속 검증

M8:
- MGN/FNO 추론 서버 통합
- 실시간 파라미터 변경 -> 즉시 추론 -> 즉시 시각화 루프 구축

M9:
- Differentiable physics PoC
- 목표 성능 기반 형상 가이드 기능 실험

Gate-Q3:
- 실시간 디지털 트윈형 분석 루프 초도 완성

## Q4. 최적화/제품화 준비 (M10-M12)

M10:
- 전처리 고비용 경로 Wasm 후보 도출 및 1차 이식

M11:
- WebGPU 적용성 검토, 병목 구간 선택 튜닝

M12:
- Docker 패키징, 운영 문서, 성능 벤치마크, IP 문서화

Gate-Q4:
- 배포 가능한 RC와 운영문서 세트 완성

---

## 6. 즉시 실행 플랜 (다음 10주)

Week 1-2:
- Contract v1 동결 + benchmark 확정

Week 3-4:
- 브리지 안정화 + dataset export 안정화

Week 5-6:
- round-trip validation + 자동 리포트

Week 7-8:
- MGN baseline 학습/추론 검증 + 지표 리포트

Week 9:
- Motor-CAD/Maxwell/TwinBuilder 실사용 호환 점검

Week 10:
- RC hardening + 버전 매트릭스 + 릴리즈 문서

---

## 7. KPI/품질 게이트

### 7.1 기술 KPI

- 호환성 성공률 >= 90%
- geometry drift 평균 <= 5%
- 자동 실행 성공률 >= 90%
- MGN 학습 재현 성공률 >= 90%
- 추론 품질: |B| MAE, Bx/By MAE 기준선 충족

### 7.2 서비스 KPI

- 추론 API 응답시간 SLO(케이스 크기별) 충족
- 대시보드 주요 액션(로드/슬라이스/비교) 체감 지연 허용범위 내

### 7.3 운영 KPI

- 필수 테스트 pass rate >= 95%
- contract breaking change 0건
- RC 기준 치명 결함 0건

---

## 8. 리스크와 선제 대응

1. 데이터 형식 편차(솔버/버전/해석조건)
- 대응: Contract validator + 샘플 누적 + 스키마 버전 고정

2. SciML 환경 충돌(torch-geometric/physicsnemo)
- 대응: 전용 venv, 버전 pinning, 재현 스크립트 고정

3. 토폴로지 자동화 불안정
- 대응: optional 모드 유지, fallback 메시지 표준화

4. 웹 렌더링 성능 한계
- 대응: LOD/decimation/typed array/후속 WebGPU 트랙 병행

5. 인력/시간 제약(1인 중심)
- 대응: Workstream별 최소 실행 단위(MVP) 정의, Gate 기반 우선순위 운용

---

## 9. 운영 규칙 (Program Governance)

1. Contract-first: 데이터 계약 변경은 구현 전에 승인
2. Evidence-first: 리포트/지표 없는 기능 완료 선언 금지
3. Non-blocking optional: topology/face 실패는 파이프라인 중단 금지
4. Reproducible ML: seed, split, checkpoint schema 고정
5. Release gate: Q별 게이트 기준 미충족 시 기능 확장보다 안정화 우선

---

## 10. 최종 산출물

1. eMach Interoperability SDK v1
- parser + contracts + bridge + validator

2. SciML Baseline Pack v1
- MGN 학습/추론 실행 경로 + checkpoint + metrics report

3. Visualization/Service Pack v1
- Streamlit 운영 대시보드 + FastAPI inference 서비스

4. Integration Report Pack
- 5패키지 호환 매트릭스 + 성능/품질 벤치마크 + 리스크 로그

5. Release & Ops Docs
- 설치/실행/트러블슈팅/마이그레이션/버전 매트릭스

---

## 11. 바로 실행할 Action 12

1. benchmark 10케이스 ID와 데이터 위치 동결
2. Contract v1 스키마 파일 분리 및 예시 데이터 확정
3. pyMCAD h5/txt 입력 표준 경로 정리
4. MLDataset validator 최소 버전 구현
5. MGN 학습 러너(노트북 -> 스크립트) 초안 작성
6. MGN 기준 지표 계산기 구현
7. FastAPI 추론 엔드포인트 최소 구현
8. Streamlit Compare View 최소 기능 연결
9. 실행 실패 taxonomy 표준 코드표 정의
10. 버전 매트릭스 초안(Python/torch/physicsnemo/solver) 작성
11. 주간 Gate 점검 템플릿 도입
12. RC 준비 체크리스트 생성
