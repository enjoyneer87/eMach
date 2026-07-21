# DISPATCH CONTEXT — 후속 논문2 (map-based MIL 전력수지) Phase A/B 착수

_생성: 2026-07-19 · 소스: Claude Code 세션 (d--KangDH-EveryMotor)_
_대상: Claude Desktop 디스패치가 이 작업 맥락을 인식하도록_

---

## 무엇인가

JEET 논문1(AC손실 SCL-M 스케일링 + 멱지수 분리 RBF 보정)의 **후속 논문2**를 착수했다.
**Thesis**: 표준 map-based(LUT) 기계모델은 MIL에서 순시 전력수지를 (1) 비가역 자속맵의
공에너지 생성/소멸, (2) 사이클평균 손실맵의 순시 이중계상 두 이유로 위반한다. 논문2는
λ맵 가역성 투영 + 손실을 임피던스 소자(AF-보정 R_AC 직렬 + 철손 R_c 병렬)로 삽입해
매 timestep `P_elec = dW_m/dt + T_e·ω + ΣP_loss` 폐합을 보장한다.

**전체 계획**: `PLAN_paper2_mapMIL_powerbalance.md` (Phase A~F, 마일스톤 M1=A+B+C /
M2=D+E+F). **이미 구축**: MtpaFwSolver.py가 정상상태 EEC(R_ac 직렬 + 철손 I_fe 병렬)
구현 완료 = 논문2 "손실=회로소자"의 씨앗.

---

## 이번에 실행 (A1·A2·B1 완료)

산출물: `map_exports/e10/paper2_phaseA/` (그림 3 + 리포트 2)
스크립트: `run_efficiency_map.py`(갱신) · `compare_effmap_vs_lab.py`(신규) ·
`reciprocity_check.py`(신규) · `AF_model_{Ref,HalfSC,SC}_exponent.json`(생성)

### 결과 요약 (map − Lab, 권선 80°C R 보정 후)
- **검증됨**: 80°C 온도보정으로 Cu_DC·효율 대폭 개선(Ref eta_iso +0.78%, MAE 1.29%);
  I_rms parity Ref 대각선 밀착 → **SatuMap λ + MTPA/FW EEC 솔버 자체는 유효**;
  Ref 효율맵(iso)이 Lab과 시각적 일치.
- **구조적 결함(→Phase C 최우선)**: **AC동손·철손이 map≈0**. 효율맵의 AC base가
  e10_SatuMap 단일조건 값(Ref ~26W)을 k_a/k_r² 스케일한 것이라 AF(비율~1-3)만으론
  주파수 스케일링(∝f²)·SC 후막도체 근접효과 절대크기가 빠짐 → Lab AC동손 최대 60kW(SC)
  vs map ~0. 철손도 동일(Lab 최대 16kW vs map ~0).
- **가역성(B1)**: e10_SatuMap 상대잔차 중앙값 30.6%, 스퓨리어스 공에너지 2.43J →
  비보존장 확인(Phase B 정당화, 저해상도 이산화오차 포함).

### 다음 스텝 (Phase C 우선)
- C1: 속도분해 hybrid AC동손 맵 재구성 (모델별 물리 hybrid base × AF).
- C2: Lab 철손 LUT 또는 에디/히스테리시스 분해 속도맵.
- (Phase B 우선순위 하향: 정상상태 개선폭 작음, 과도 MIL 에너지폐합 보증용으로만 유지.)

---

## 인접 작업 (혼동 방지)

- **논문1(rev5.tex)**: Overleaf 편집은 사용자가 일단 중단, Claude Code가 주 편집자.
  이 논문2는 별개 후속작 — rev5 본문에 아직 반영 안 함.
- **백그라운드 배치(무관, 계속 진행 가능)**: HalfSC 정규화(bgydrd72s) + kturn 시퀀서.
  HalfSC 멱지수 모델 wMAE가 11.3%로 높은데, 정규화 진행 중이라 그런 것.
  **논문2 effmap 비교는 Ref/SC만 사용**하므로 무영향.
- **두 툴체인 분리**: JMAG MS SC → devSurfInterp4HYBMS.m (MATLAB) / kturn pipe →
  Motor-CAD (Python). 논문2 Phase A~C는 Python(pyMotorEnv_310)·기존 데이터.

## 파일 포인터
| 항목 | 경로 |
|---|---|
| 계획 | `mlxperPJT/JEET/PLAN_paper2_mapMIL_powerbalance.md` |
| Phase A/B 산출 | `mlxperPJT/JEET/map_exports/e10/paper2_phaseA/` |
| 효율맵 스크립트 | `mlxperPJT/JEET/run_efficiency_map.py` |
| Lab 대조 | `mlxperPJT/JEET/compare_effmap_vs_lab.py` |
| 가역성 | `mlxperPJT/JEET/reciprocity_check.py` |
| EEC 솔버(기구축) | `tools/motor_scaling/morphisms/MtpaFwSolver.py` |
| SatuMap | `tools/SystemSimulationModel/e10_SatuMap.mat` |
