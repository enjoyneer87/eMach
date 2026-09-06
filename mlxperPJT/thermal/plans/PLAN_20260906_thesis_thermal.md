# 학위논문용 열해석 실행 계획 — 2026-09-06 (GitHub 채널 주입본)

> **누가 읽나**: 열해석 머신(`C:\Users\moa`, Ansys v261 MAPDL·FreeFlow·Icepak·Fluent)의 Claude 세션.
> **읽는 순서**: `../HANDOFF_20260722.md`(§11 이어받기 절차) → `../freeflow/README_freeflow.md` → `../icepak_e10/README_icepak_e10.md`
> → **이 문서**. Drive `Prius_thermal_viz/_context/`에 같은 문서의 사본이 있으나 **정본은 이 브랜치(`freeflow-e10-model`)**다.
> **작성 주체**: 학위논문 세션(레포 `Thesis_SKKU`, 본심 2026-11 말). 학위논문이 열해석 쪽에 요구하는 산출물을 정의한다.
> **채널 규칙**: 이 PC(학위논문)는 `mlxperPJT/thermal/plans/`만 쓴다. moa는 `mlxperPJT/thermal/**` 나머지를 쓴다.
> 결과는 **`mlxperPJT/thermal/thesis_out/`**(JSON + PNG ≤ 300 KB)에 커밋·push하고, 완료 보고는 `HANDOFF_*.md`에 덧붙인다.
> GIF·대용량은 GitHub Release(`thermal-e10-YYYYMMDD`) 또는 moa 디스크. 학위논문 쪽은 `Thesis_SKKU/Assets/Data/thermal/pull_from_emach.py`로
> `thesis_out/`을 당겨 간다 — 논문 레포를 moa에 둘 필요 없다.

## 0. 학위논문이 지금까지 가져간 것 (2026-09-06, Thesis_SKKU 1aa447e·797078f)

5장에 반영 완료 — 손대지 말 것:
- MAPDL 하이브리드(JAC279, 과도 900 s) 권선 152.2 / 고정자 126.0 / 자석 86.9 °C, 오일 회로 70→84.4/91.9/122.3 °C.
- 오일 70 °C 고정 대류 BC(정상상태) 권선 95.6 °C → 회로 결합 시 +56.6 K. (`freeflow/data/ff_mapdl_temps.json` vs `ff_mapdl_hybrid_temps.json`)
- SPH 근벽 온도구배 역산 h = 193(재킷)/186(스프레이) W/m²K vs 가정 1000/2000 → 1/5~1/11. (`freeflow/data/htc_backout.json`)
- Prius: Fluent CHT 저부하/250 A, Icepak(프레임 고정 BC), 웨비나 deck 슬라이드 11의 정합 비교(코일 Δ0.0/1.0 °C).
- **손실 출처 정정**: e10 열해석 손실은 Prius 250 A/3000 rpm 이식(동손 3,350 = 2,312+1,039 W). 5장은 이를
  "연속 정격 수준 부하의 방법 실증"으로 쓴다. e10 정격점(16 krpm/460 A) 동손은 직류 31.4 + 엔드 18.5 + 교류 37.2 kW.
- Icepak e10: `9719537` 결론(V1 균질 권선 136.5 °C ≈ MAPDL 152.2, −10 %; V2 discrete 바 비컨포멀 폭주)을 5장 "접촉 열저항"
  절의 사례로 인용할 예정. **추가 작업 불필요.**

## 1. 요청 산출물 (우선순위 순)

### D1. e10 연속 정격 곡선 — 권선 온도 T_w(속도, 전류) 표  ★ 최우선 (5장 tab:continuous_rating_acloss, 7장 고속 연속 정격 제약)
**방법**: `freeflow/scripts/04_mapdl_thermal.py`의 하이브리드 모델을 **정상상태**(13.5 s/런)로, 손실만 바꿔 돌린다.
**손실 입력**: e10 자신의 손실 — JEET Ref 맵 `mlxperPJT/JEET/map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary.json`
(이 브랜치에도 있음. 리스트 240행; `mode` FullFEA/Hybrid, `speed` {2000,4000,8000,16000}, `current` {0.1,115.075,230.05,345.025,460} A_rms, `phase` 6점).
- 격자: 속도 4 × 전류 {115, 230, 345, 460} 4 = 16점, phase는 **36°**(JEET 레코드 규약) 고정.
- 동손 [W] = (`ts_dc_active_only_kW` + `ts_dc_end_kW`) × 1000 → 슬롯부/엔드부로 **분리 주입**(엔드는 스프레이 노드에 접한 엔드턴 체적).
  - AC 동손 [W] = `fea_total_ac_kW` × 1000 → **Case AC**에서만 슬롯부에 추가(Case DC는 0). 두 케이스 다 돌린다 → 32런.
- 철손: 정확한 맵이 없으므로 기준값을 속도로 스케일: 고정자 1,856 W·(n/15000)^1.5, 회전자 74 W·(n/15000)^1.5
  (R1 파이프라인, 15 krpm/250 A). 자석손: 정적 추정 3,385 W×**0.17**(과도 척도 보정) = 575 W·(n/15000)^2.
- 냉각: 기준 h(1000/2000/250)와 **SPH 역산 h(190/190/250)** 두 벌 → 총 64런 ≈ 15분.
- 온도 한계: 권선 180 °C, 자석 150 °C. 각 (속도, h세트, 케이스)에서 전류 4점을 보간해 **연속 전류 I_cont(n)** 산출.
**출력**: `thesis_out/e10_cont_rating.json`
```json
{"_model":"JAC279 hybrid steady","_loss_source":"JEET_ACLoss_Ref_Map_Summary.json phase36","_soltype":"steady",
 "_htc_sets":{"base":{"jkt":1000,"spray":2000,"splash":250},"sph":{"jkt":190,"spray":190,"splash":250}},
 "runs":[{"speed":16000,"current":230.05,"case":"AC","htc":"base",
          "P_W":{"cu_slot":..,"cu_end":..,"ac_slot":..,"fe_s":..,"fe_r":..,"pm":..},
          "T_C":{"winding_max":..,"winding_mean":..,"stator_max":..,"magnet_max":..,"rotor_max":..},
          "circuit_T":{"OIL":70,"JACKET":..,"SPRAY":..,"GAP_S":..,"GAP_R":..,"SHF":..}}],
 "I_cont_Arms":{"base":{"DC":{"2000":..,"4000":..,"8000":..,"16000":..},"AC":{...}},"sph":{...}}}
```
그림: `thesis_out/cont_rating_Tw_vs_I.png`(속도별 T_w–I 곡선, 180 °C 선, Case DC/AC, h 두 벌), `thesis_out/cont_rating_Icont_vs_n.png`.
연속 토크로의 환산은 학위논문 쪽에서 토크맵으로 한다(전류→토크). **04 스크립트의 `LOSSJSON` 하드코딩 경로는 CLI 인자로 빼 줄 것.**

### D2. 교류 동손의 슬롯 내 분포 주입 — 균일 vs 턴별 사다리 (5장 §고도화 LPTN "슬롯 상단·하단 도체 분리" 주장의 실증)
JEET 맵 FullFEA 행의 `fea_per_turn_raw`(턴별 AC 손실, T1=공극측…T6=요크측)를 헤어핀 도체 144개에 턴 인덱스로 매핑해 주입.
16 krpm/230 A(연속 정격 근방)와 16 krpm/460 A(정격) 2점 × {균일, 턴별} = 4런. 출력 `thesis_out/e10_ac_turnwise_hotspot.json`
(권선 max/mean, 공극측 턴 온도 vs 요크측 턴 온도) + 단면 컨투어 2장. 기대: 균일 주입이 핫스팟을 놓친다는 정량.

### D3. 중력 방향 수정 후 FreeFlow 8 s 재실행 → HTC 역산 갱신 (HANDOFF §10-4 미결)
중력을 축에 수직(반경 방향)으로 고쳐 fresh solve(GPU ~5 h). 갱신본을 `thesis_out/htc_backout_horizontal.json`으로.
5장은 "자릿수 대조"까지만 인용하므로 결론이 뒤집힐 가능성은 낮지만, 중력 오류를 안 고친 채 인용하는 상태는 끝내야 한다.

### D4. (선택) e10 손실 JSON 정본화
`01_e10_motorcad_losses.py`가 0을 반환한 원인(운전점 설정 후 `do_magnetic_calculation` 미호출로 추정)을 고치거나, D1처럼 JEET 맵에서
직접 뽑는 함수로 대체. `freeflow/data/e10_losses.json`의 `_loss_source`를 "JEET Ref map"으로.

### D5. Icepak — 추가 작업 없음.

## 2. 학위논문 쪽에서 주는 값 (필요 시 참조)
- e10 기준 손실(R1 파이프라인, kfe 0.97, Br 80 °C=1.2157 T): 15 krpm/250 A: DC 9,279 · AC(하이브리드) 15,204 · 철손 1,856+74 · 자석(정적) 3,385 W.
  16 krpm/460 A/36°: DC 31,416 · AC(하이브리드) 54,730 · 철손 2,619+89 · 자석(정적) 8,132 W. 자석은 ×0.17 하면 과도 FEA/Motor-CAD와 만난다.
- e10 정격점 Full-FEA(Motor-CAD 레코드): AC 37,172 W(TorqueNumberCycles=1 규약), 자석 1,335 W.
- 제원: 외경 198 / 보어 142.54 / 공극 1.0 / 회전자 140.54 / 적층 150 mm, 6턴 1병렬, 720 V, 460 A_rms/16 krpm.

## 3. 규약
- 결과 JSON에는 반드시 `_loss_source`, `_htc`, `_soltype`(steady/transient+시간)을 넣는다 — "손실 출처 불명" 재발 방지.
- steady끼리·transient끼리만 비교(README_icepak_e10 §4).
- 그림은 학위논문 규약(폰트 Malgun Gothic, 축 라벨 한글, 케이스 색 DC 회색/AC 파랑/AC+ 빨강)이면 그대로 5·7장에 들어간다.
- 완료 시 `HANDOFF_<날짜>.md`에 "D1 완료: 파일 경로·핵심 수치 3줄"을 덧붙이고 push(지연 주의: `git ls-remote`로 확인).

## 4. 이 문서를 읽은 세션의 첫 행동
1. `git pull` (브랜치 `freeflow-e10-model`) → HANDOFF §11 절차로 로컬 전용 파일(cdb·freeflow 프로젝트) 상태 확인.
2. D1 준비: JEET 맵 로더 + 04 스크립트 손실 인자화 → 1런 검증(16 krpm/230 A, Case DC, base h) → 64런 배치 → `thesis_out/` JSON/그림 → 커밋·push.
3. 완료 보고를 HANDOFF에 남기면 학위논문 세션이 `pull_from_emach.py`로 당겨 5장 표와 7장 절을 채운다.
