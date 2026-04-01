# eMach 패키지 통합 호환 개발 플랜 (Pyleecan + SyR-e + eMach + PyMotorCAD + PyAEDT + SciML/PhysicsNeMo)

작성일: 2026-04-01  
기준 문서: UML 및 WBS 분석 결과 반영  
대상: eMach/pyMotorGeo를 중심으로 5개 패키지 + SciML(MGN) 상호 운용 가능한 개발 로드맵

연계 UML:
- `Plan/UML/08_PyAEDT_Architecture_UML.puml`
- `Plan/UML/09_PyMotorCAD_Architecture_UML.puml`
- `Plan/UML/10_5Packages_Integration_UML.puml`

---

## 1. 목표

eMach를 단순 DXF 분석 도구가 아니라, 다음 5개 생태계와 SciML 학습 루프를 연결하는 호환 허브로 만든다.

- 설계 생태계 A: SyR-e (MATLAB parametric 설계 + 최적화)
- 설계 생태계 B: Pyleecan (OOP 머신 모델 + FEA 파이프라인)
- 변환 허브: eMach(pyMotorGeo) (DXF 파싱/분석/계약 정규화)
- 해석 자동화 A: PyMotorCAD (Motor-CAD RPC 자동화)
- 해석 자동화 B: PyAEDT (Maxwell/TwinBuilder/AEDT 자동화)
- SciML 학습/추론: PhysicsNeMo MeshGraphNet(MGN) 기반 surrogate 모델

핵심 성과지표(KPI):
1. 5패키지 왕복 호환 성공률 >= 90% (10개 벤치마크)
2. 극수/슬롯 추출 정확도 >= 95%
3. eMach -> Pyleecan/PyMotorCAD/PyAEDT 변환 후 기하학 핵심 지표 오차 <= 5%
4. PyMotorCAD/PyAEDT 자동 실행 성공률 >= 90% (필수 케이스)
5. 선택형 토폴로지 실패 시에도 메인 파이프라인 100% 비차단 동작
6. PhysicsNeMo MGN 학습 파이프라인 재현 성공률 >= 90% (표준 데이터셋 기준)
7. MGN 추론 결과의 필수 지표(|B| MAE, Bx/By MAE) 기준선 충족

---

## 2. 현재 상태 요약 (문서/UML 반영)

- Pyleecan: 271개 클래스(OOP), Machine/Lamination/Slot 중심 계층 구조
- SyR-e: MATLAB 기반 parametric 설계 + 다중 솔버 export
- eMach(pyMotorGeo): 32개 모듈, 11-step DXF 분석 파이프라인
- PyMotorCAD: RPC 코어 + GeometryTree + Datastore 중심 자동화 패키지
- PyAEDT: Desktop -> Design -> Solver App -> Modeler/Setup/Post 계층 아키텍처
- SciML(PhysicsNeMo): `physicsnemo_train_from_pyMCAD.ipynb` 기반 MeshGraphNet 학습 코드 확인
- 제약: rotor topology 자동분류는 현재 fallback 상태(선택형 경로)
- 전략: Phase 1에서는 CAD interchange 우선, topology/face 고도화는 release-blocking 제외

---

## 3. 호환 아키텍처 목표상

### 3.1 표준 인터페이스 5종

1. Geometry Contract v1 (`GeometryPayload`)
- entities: line/arc/circle/polyline
- coordinate system, unit(mm), origin
- periodicity(full/half/quarter)
- layer mapping(stator/rotor/magnet/barrier/conductor/tooth/yoke)

2. Semantic Contract v1 (`SemanticPayload`, optional)
- topology_type(SPM/IPM/SynRM/Spoke/EESM/Unknown)
- region labels + confidence
- fallback reason code

3. Result Contract v1 (`CommonResult`)
- geometry metrics(area, radii, symmetry score)
- solver KPI(efficiency, torque, losses)
- provenance(source package/version)

4. Solver Execution Contract v1 (`ExecutionPayload`)
- target solver: motorcad / maxwell / twinbuilder
- run profile: setup/sweep/mesh 옵션
- exported artifacts: mot/aedt/rom/json/report
- run status + error taxonomy

5. SciML Dataset Contract v1 (`MLDatasetPayload`)
- source: `Mag_*.h5` / `MagTransient*.txt`
- graph inputs: node(pos, region, optional A/J), edge(edge_index, dxy, dist)
- targets: Bx, By (필수), 확장 타깃(A, J)
- split/normalization: time-order split, train-stat normalization
- metadata: source case id, step index, unit, provenance

### 3.2 패키지별 역할 고정

- SyR-e: parametric generator + optimization source
- eMach: parser/classifier/interchange orchestrator (중앙 허브)
- Pyleecan: OOP machine model + simulation bridge target
- PyMotorCAD: Motor-CAD geometry/parameter/calculation automation target
- PyAEDT: Maxwell/TwinBuilder 기반 검증 자동화 및 보고 target
- PhysicsNeMo(MGN): 그래프 데이터 기반 학습/추론 및 surrogate 검증 target

### 3.3 기준 데이터 흐름 (5패키지)

1. SyR-e/Pyleecan -> eMach
- DXF/파라미터 입력

2. eMach -> Contract v1
- Geometry/Semantic/Execution payload 정규화

3. Contract -> PyMotorCAD/PyAEDT
- 해석 실행, 결과 수집

4. 결과 -> eMach validator
- round-trip/지표 검증, 리포트 생성

5. 결과 데이터 -> MLDatasetPayload -> PhysicsNeMo MGN
- 학습/검증/체크포인트 생성 + 추론 결과를 validator로 재주입

---

## 4. 개발 범위 (eMach 중심)

### 4.1 필수 범위 (Release-blocking)

1. DXF Input Normalizer
- SyR-e/Pyleecan/CAD 원본 DXF를 단일 내부 포맷으로 정규화

2. Stable Analysis Core
- origin/airgap/pole/slot 추정 안정화
- 실패 시 deterministic fallback

3. Export/Bridge Stabilization
- `pyleecan_bridge.py`에서 Machine 생성 경로 고정
- `motorcad_bridge.py`에서 Motor-CAD 입력 규약 고정
- `aedt_bridge.py`(신규)에서 AEDT 입력 규약 고정

4. Validation Harness
- 10개 benchmark 케이스 자동 검사
- round-trip metric 리포트 생성

5. CAE Automation Harness
- PyMotorCAD/PyAEDT 실행 어댑터 추가
- 실행 실패 taxonomy + 재시도 정책 추가

6. SciML Training Harness
- pyMCAD 산출(`Mag_*.h5`, `MagTransient*.txt`) -> 그래프 변환 경로 고정
- PhysicsNeMo `MeshGraphNet` 학습/검증/체크포인트 저장 표준화
- 추론 지표(|B| MAE, Bx/By MAE) 자동 리포트화

### 4.2 선택 범위 (Non-blocking)

1. Rotor topology 고도화
- magnet/barrier 자동 감지 개선
- confidence calibration

2. Face detection 고도화
- 3D 확장용 face adjacency 추가

3. TwinBuilder ROM 흐름 고도화
- MotorCAD ROM -> PyAEDT TwinBuilder 자동 연결

---

## 5. 실행 계획 (10주)

## Week 1-2: Contract Freeze (5패키지 + SciML)

목표:
- Geometry/Semantic/Result/Execution Contract v1 초안 -> 동결

작업:
1. eMach 내부 dataclass 정의 (`contracts.py`)
2. DXF layer naming 규칙 확정
3. optional semantics 실패 코드 체계 정의
4. ExecutionPayload 스키마 정의 (motorcad/maxwell/twinbuilder)
5. MLDatasetPayload 스키마 정의 (graph input/target/metadata)

산출물:
- `contracts.py`
- `contract_examples/*.json`
- contract spec 문서
- `ml_dataset_examples/*.json` 또는 `*.pt` 메타 샘플

완료조건(DoD):
- SyR-e 샘플 2개, Pyleecan 샘플 2개를 contract serialize 가능
- PyMotorCAD/PyAEDT 실행 설정을 ExecutionPayload로 serialize 가능
- pyMCAD 출력 2케이스를 MLDatasetPayload로 serialize 가능

## Week 3-4: Bridge Stabilization

목표:
- eMach -> Pyleecan/PyMotorCAD/PyAEDT 변환 경로 안정화

작업:
1. `pyleecan_bridge.py` 최소 생성 경로 확정
2. `motorcad_bridge.py` 입력 규약 고정
3. `aedt_bridge.py` 신규 추가 (Maxwell 최소 import path)
4. Machine 타입 매핑 테이블 구현
- `SPM -> MachineSIPMSM`
- `IPM -> MachineIPMSM`
- `SynRM -> MachineSyRM`
- `Unknown -> MachineUD`
5. geometry fidelity 검사 함수 추가
6. pyMCAD 출력에서 MGN 학습용 graph dataset export 함수 추가

산출물:
- bridge unit test
- mapping validator
- execution adapter smoke test
- dataset export smoke test

DoD:
- 6/10 케이스에서 Pyleecan 객체 생성 + 기본 검증 통과
- 6/10 케이스에서 PyMotorCAD/PyAEDT 실행 어댑터 기동 성공
- 6/10 케이스에서 그래프 dataset 생성 성공

## Week 5-6: Round-Trip Validation

목표:
- SyR-e -> eMach -> Pyleecan/PyMotorCAD/PyAEDT round-trip 검증

작업:
1. benchmark 10케이스 확정
2. metric 계산기 구현
- pole/slot consistency
- area/radius drift
- symmetry preservation
3. solver run metric 추가
- mesh success
- setup/sweep success
- report artifact 생성 여부
4. 자동 리포트(`validation_report.md`) 생성

산출물:
- benchmark dataset index
- validation scripts
- CI 체크 항목

DoD:
- round-trip 90% 이상 성공
- 평균 기하학 오차 5% 이하
- PyMotorCAD/PyAEDT 실행 성공률 90% 이상

## Week 7-8: SciML(MGN) Baseline Training & Inference Validation

목표:
- PhysicsNeMo MeshGraphNet baseline 학습 파이프라인을 통합 워크플로우에 편입

작업:
1. `physicsnemo_train_from_pyMCAD.ipynb`를 기준 구현으로 정식 등록
2. h5/txt 입력 자동 감지 및 graph 변환 안정화
3. train/val split, normalization, checkpoint schema 표준화
4. 추론 결과를 eMach validator 형식으로 변환
5. 성능 리포트(`mgn_validation_report.md`) 자동 생성

DoD:
- 표준 케이스셋에서 학습 파이프라인 재현 성공률 90% 이상
- 필수 지표(|B| MAE, Bx/By MAE) 기준선 충족
- checkpoint + 메타데이터(provenance) 저장 성공

## Week 9: Motor-CAD/Maxwell/TwinBuilder Interchange Check

목표:
- CAD/CAE 도구 실사용 검증

작업:
1. Motor-CAD 임포트 5케이스
2. Maxwell 임포트 5케이스
3. TwinBuilder ROM 연동 3케이스
4. meshability/fatal error 로그 수집

DoD:
- fatal geometry error 0건(필수 케이스)
- TwinBuilder 링크 필수 케이스 3건 성공

## Week 10: Hardening & Release Candidate

목표:
- non-blocking 모듈 분리 + RC 발행

작업:
1. topology/face 모듈 feature flag 처리
2. fallback message 표준화
3. 릴리즈 노트/마이그레이션 가이드 작성
4. 5패키지 버전 호환 매트릭스 확정
5. SciML 실행환경(Python/torch/torch-geometric/physicsnemo) 버전 매트릭스 확정

DoD:
- topology 실패 상황에서도 main pipeline 성공
- RC 태그 및 문서 배포
- version matrix 기반 재현 가능한 실행 확인

---

## 6. 모듈 백로그 (우선순위)

P0 (이번 분기 필수)
1. `contracts.py` 신설 (Geometry/Semantic/Result/Execution)
2. `reader.py` 정규화 강화
3. `analysis_airgap.py` 안정화
4. `pyleecan_bridge.py` 타입 매핑/검증
5. `motorcad_bridge.py` 실행 경로 고정 (ExecutionPayload 반영)
6. `aedt_bridge.py` 신설 (ExecutionPayload -> PyAEDT)
7. `export.py` 레이어 규격 고정
8. `validation/` 자동화 스크립트
9. `ml_dataset_adapter.py`(또는 동등 모듈) 추가
10. `physicsnemo_mgn_train.py`(또는 notebook runner) 추가
11. `mgn_inference_bridge.py`(예측값 -> validator payload) 추가

P1 (다음 분기)
1. `topology_rotor.py` classifier 개선
2. `topology_stator.py` conductor/tooth labeling 강화
3. `face_detection.py` adjacency/normal 개선
4. `twinbuilder_bridge.py` 신설 (PyMotorCAD ROM -> PyAEDT TwinBuilder)

P2 (Phase 3 연계)
1. Warp/FNO 연동을 위한 tensor-friendly export
2. 실시간 UI용 compact payload
3. MeshGraphNet 다물리 타깃(자계+손실+열) 멀티태스크 확장

---

## 7. 테스트 전략

### 7.1 테스트 유형

1. Unit Test
- parser/entity transform
- pole/slot counting
- contract serialization

2. Contract Test
- SyR-e 출력 DXF가 eMach 입력 규약을 충족하는지 검증
- eMach 출력이 Pyleecan/PyMotorCAD/PyAEDT 입력 규약을 충족하는지 검증

3. Integration Test
- SyR-e -> eMach -> Pyleecan full chain
- eMach -> PyMotorCAD import/run chain
- eMach -> PyAEDT import/run chain
- PyMotorCAD -> PyAEDT(TwinBuilder) ROM chain

4. Regression Test
- benchmark 10케이스 기준 지표 비교

5. SciML Pipeline Test
- h5/txt -> graph 변환 무결성 테스트
- MGN 학습 스모크 테스트(소규모 epoch)
- checkpoint load/inference 재현 테스트

### 7.2 합격 기준

- 필수 테스트 pass rate >= 95%
- contract breaking change 0건
- benchmark drift threshold 초과 케이스 <= 1건
- PyMotorCAD/PyAEDT smoke test fail rate <= 10%
- MGN 학습/추론 스모크 테스트 fail rate <= 10%

---

## 8. 리스크 및 대응

1. 리스크: SyR-e DXF 변형 포맷 다변화
- 대응: normalizer rule set 버전 관리 + 샘플 누적

2. 리스크: Pyleecan 클래스 구조 변경
- 대응: bridge adapter 계층 분리 + 버전 매트릭스 유지

3. 리스크: topology 미완성으로 사용자 혼란
- 대응: optional 플래그 + confidence/fallback 메시지 표준화

4. 리스크: 대형 UML/문서와 구현 불일치
- 대응: 주간 UML regenerate + contract-first 검토

5. 리스크: AEDT/Motor-CAD 실행 환경 의존성(버전/라이선스)
- 대응: 실행 환경 profile 분리 + version matrix + CI smoke fallback

6. 리스크: PyAEDT/PyMotorCAD API 변경
- 대응: adapter 계층에서 semantic version gate 적용

7. 리스크: SciML 학습 데이터 품질 편차(메쉬/스텝/라벨 불일치)
- 대응: dataset contract validation + 전처리 경고 taxonomy + 기준 샘플셋 고정

8. 리스크: PhysicsNeMo/torch-geometric 버전 충돌
- 대응: 독립 venv + 버전 pinning + notebook/스크립트 공통 requirements 유지

---

## 9. 팀 실행 규칙

1. Contract-first: 구현 전에 contract 변경 PR 선행
2. Non-blocking optional: topology/face 실패는 pipeline stop 금지
3. Bench-first release: benchmark 통과 없이는 release 금지
4. Version pinning: SyR-e/Pyleecan/PyMotorCAD/PyAEDT 호환 버전 명시
5. Adapter boundary: 외부 패키지 변경은 bridge 계층에서만 흡수
6. Reproducible ML: 학습 seed, split 정책, checkpoint schema를 변경 시 PR 명시

---

## 10. 즉시 실행 체크리스트

1. `contracts.py` 초안 작성
2. `pyleecan_bridge.py` 타입 매핑 함수 추가
3. `aedt_bridge.py` 골격 생성
4. `motorcad_bridge.py` ExecutionPayload 연계
5. benchmark 10케이스 파일 목록 확정
6. validation 스크립트 골격 생성
7. WBS 보드에 WP-A/WP-B/WP-D 세부 태스크 등록
8. PhysicsNeMo MGN 학습 노트북/스크립트의 표준 실행 경로 확정
9. MGN 추론 결과를 `CommonResult`에 매핑하는 validator 어댑터 초안 작성

---

## 11. 최종 산출물

1. eMach Compatibility SDK v1
- parser + contracts + bridge(pyleecan/motorcad/aedt) + validator

2. 호환성 리포트
- SyR-e, Pyleecan, PyMotorCAD, PyAEDT 대상 pass/fail matrix

3. 운영 문서
- integration guide
- troubleshooting guide
- migration guide

4. 실행 환경 매트릭스
- Python 버전, solver 버전, 패키지 버전, 라이선스 요구사항 명세

5. SciML Baseline Pack
- PhysicsNeMo MGN 학습 실행 노트북/스크립트
- 기준 checkpoint + 학습 로그 + 추론 검증 리포트
