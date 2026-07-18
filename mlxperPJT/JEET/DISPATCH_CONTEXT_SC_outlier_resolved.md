# Desktop 디스패치 컨텍스트 — SC 16k/90° 이상치는 이미 해결됨

> 작성: 2026-07-18 (로컬 Claude Code 세션) · 대상: Claude Desktop 디스패치/모바일
> 목적: SC AF 모델의 "16k/690A/90° AF=0.474 이상치, Phase 2 infill 필요"
> 라는 인식이 **낡은 데이터 기준**임을 알리고 최신 상태를 전달.

## TL;DR

**SC (16{,}000 RPM, 690 A, β=90°)의 AF=0.474 이상치는 2026-07-17 15:37에
재실행·대체 완료되어 지금은 AF=1.068입니다. 추가 infill 불필요.**

"690A: AF=0.474 ← 이상치 / LOO 61% / Phase 2 infill 필요"는 **15:23 이전
스냅샷**의 정확한 서술이지만, 14분 뒤 해결되어 무효가 되었습니다.

## 현재 정본 상태 (검증됨)

정본: `eMach/mlxperPJT/JEET/map_exports/e10/SC/JEET_ACLoss_SC_Map_Summary.json`
(240 records; Drive 미러: `EveryMotor_JEET_data/map_exports/e10/SC/...`)

16k/90° 코너 AF (= TS-FEA / Hybrid), 모두 매끄러운 단조 증가:

| 전류 | AF | 비고 |
|---|---|---|
| 230.1 A | 0.962 | |
| 460.1 A | 1.040 | 인필(outlier_recheck) |
| 690.0 A | **1.068** | **재실행 대체** (구 0.474) |
| 920.0 A | 1.111 | |

16k/72° 코너: 1.02~1.04 전부 정상.
데이터셋: 89 유효점, 재스캔 추가 이상점 0.

## 해결 이력 (이미 완료된 것)

1. 이웃 일관성 전수 스캔(3모델 249pts)에서 690A/90°가 유일 이상치로 검출.
2. `run_single_fea_point.py`로 Motor-CAD TS-FEA 재실행 → 미수렴 확진.
3. 수렴값으로 대체: AF 0.474 → 1.068. 인접 (460A,90°) 인필: AF 1.040.
4. `AF_infill_schedule_SC.json`의 `rerun_outlier`·`densify_loo61pct` 항목은
   **실행 완료된 계획**이지 미결 작업이 아님.
5. 논문 rev4/rev5 Sec 4.1에 "AF 0.47→1.07" 서술 반영됨.

## 낡은 값을 보게 되는 원인 (정리 완료)

pre-rerun 스냅샷 3개가 혼동 원인이었고, 2026-07-18에 아카이브 이동함:
`map_exports/e10/SC/_archive_superseded/` (README 포함)
- `SC_Map_Summary_PRE-rerun_AF690-90_0.474.json` (구 백업)
- `SC_Map_Summary_e10level_STALE_239rec_0.474.json` (상위 e10 폴더 고아 중복)
- `SC_Map_Summary_POST-rerun_AF690-90_1.068.json` (정본과 동일)

활성 코드(pipeline / run_single_fea_point / verify_af_data_quality /
mesh_b_vs_mcad)는 전부 상위 정본 SC json만 참조 (검증됨).

## 관련 최신 진행 (이 세션, 참고)

- 논문: **JEET_KDH_rev5.tex**가 활성 (rev4에서 A/C/D 삭감 + 캡션 10개 트림,
  본문 −10.6%). Fig5 두여자원 개념도·Fig6 v2 스윔레인·Fig14 효율맵 반영.
- HalfSC 690A(=1.5×460, B-보존 정격) 티어 44점 추가 → 256 records
  (⚠ Ref/SC 240과 그리드 구조 불일치, 정규화 방향 사용자 결정 대기).
- Lab custom-loss AF 주입 효율맵: 시도했으나 Lab의 speed-only 제약·음수클리핑
  으로 효과 미미(부정적 결과, notes §11). Fig14는 현행 4패널 유지 권장.
- HalfSC 정규화(SC 구조 mirror): 목표 5티어 [0.1/172.5/345/517.5/690] × 4속도
  × 6위상 = 240 records로 재구성 중(신규 116점 FEA, run_halfsc_normalize.py).
  목표 밖 기존 티어 115.1/230/460은 완료 후 별도 보관 예정. Fig14는 SC 단독 확정.

## 남은 작업 2건 — 툴체인·데이터 소스 구분 (혼동 주의)

두 작업은 **데이터 소스도 실행 환경도 완전히 분리**된다. 서로 파일을 섞지 말 것.

### ① JMAG MS SC → devSurfInterp4HYBMS.m  (JMAG 계열, MATLAB)

- 툴체인: **JMAG Designer**(MS 정자기 해석) → MATLAB.
- 입력 데이터: `D:\KangDH\Emlab_emach\mlxperPJT\JEET\e10MS_ConductorModel_SCL_Load~13_Case{1..30}_MagB_wireTable[DenseFitwithDT].mat`
  (JMAG 추출, ~2.4GB). 스크립트가 'wire'+'MS'+'SCL'+'MagB' 필터로 읽음.
- 처리: `devSurfInterp4HYBMS.m`(`eMach\mlxperPJT\JEET\Other\` + Emlab 사본)이
  wireTable sub-line B(t)로 HYB 손실 곡면 생성.
- **데이터 확보 이미 완료**: 파일·케이스맵(6전류×5위상, Case25=γ90°/368.1A,
  `e10MS_ConductorModel_SCL_Load13_case_map.csv`)·기하판정(wireTable 반경
  176~179mm = **SCL k_r=2**) 전부 확인됨. 실행(곡면 생성)만 남음.
- ⚠ **"Z:\Simulation"은 옛 NAS 경로(언마운트)** — 실제 JMAG 원본은
  `E:\KDH\e10\MSConductorModel\...\e10MS_ConductorModel_SCL_Load~13\Case*\`.
  상세: 메모리 `reference-jmag-e10-mesh-mats`.

### ② Phase 3 LAB / run_kturn_pipeline.py  (Motor-CAD 계열, Python)

- 툴체인: **Motor-CAD** COM/RPC (`pyMotorEnv_310` venv). **JMAG 무관.**
- 입력: 기준 `.mot`(e10Turn6V261) — JMAG 결과 불필요.
- 처리: 턴수(WindingLayers) sweep 4/6/8 → `.mot` 자체 생성 → 점적율 보존
  copper 사이징 → (proximity_model × speed × current × phase) 격자 sweep
  (`_mcad_parallel_worker.run_sweep_point`, Hybrid/FullFEA) →
  `+mcad/loadAcLossJson.m` 호환 JSON. 실행 중인 HalfSC 정규화·690A 배치와
  동일 Motor-CAD 계열.
- 즉 이 작업에 **JMAG wireTable을 연결하면 오인**. 새 `.mot`을 Motor-CAD로
  만들어 자체 sweep하는 구조.
