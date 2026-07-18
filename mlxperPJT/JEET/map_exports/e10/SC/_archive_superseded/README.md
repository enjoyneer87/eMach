# Superseded SC AC-loss summaries — DO NOT USE

이 폴더의 파일들은 **낡은(pre-rerun) SC 데이터**로, 정본이 아닙니다.
정본은 `../JEET_ACLoss_SC_Map_Summary.json` (240 records, 16k/690A/90° AF **1.068**).

## 왜 보관하는가

2026-07-17 SC (16{,}000 RPM, 690 A, β=90°) 운전점이 이웃 일관성 검사에서
**AF 불연속(−55%)** 이상치로 검출됨 → Motor-CAD TS-FEA 재실행으로 **미수렴
확진** → 수렴값으로 대체(AF **0.474 → 1.068**). 인접 (460A, 90°)도 인필.
데이터셋 87 → 89 유효점. (논문 rev4/rev5 Sec 4.1에 서술됨.)

## 파일별 상태

| 파일 | 16k/690/90 AF | 상태 |
|---|---|---|
| `SC_Map_Summary_PRE-rerun_AF690-90_0.474.json` | 0.474 | ❌ 재실행 이전 백업 (15:23:49) |
| `SC_Map_Summary_POST-rerun_AF690-90_1.068.json` | 1.068 | 재실행 직후 백업 (15:37:06), 정본과 동일값 |
| `SC_Map_Summary_e10level_STALE_239rec_0.474.json` | 0.474 | ❌ 상위 e10 폴더에 있던 고아 중복본(239 rec) |

## 혼동 방지

Claude Desktop 등 다른 세션이 `AF=0.474`, `LOO 61%`, `Phase 2 infill 필요`를
보고한다면 그것은 **이 폴더의 pre-rerun 스냅샷**을 읽은 것이다. 현재 코너는
230→460→690→920 A에서 AF 0.96→1.04→**1.07**→1.11로 매끄러운 단조 증가이며
추가 infill은 불필요(이미 완료). 활성 코드(pipeline, run_single_fea_point.py,
verify_af_data_quality.py 등)는 전부 상위 정본 SC json만 읽는다.
