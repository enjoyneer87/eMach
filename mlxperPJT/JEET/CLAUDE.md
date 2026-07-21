# JEET AC Winding Loss — Claude Code Context

> 최종 업데이트: 2026-07-17  
> 연구자: 강도현 (phareal87@gmail.com)  
> 목적: JEET 논문 — Hairpin 권선 AC 손실 스케일링 검증

---

## 프로젝트 개요

e10 Hairpin 모터의 **AC 권선 손실** 계산 방법론을 비교·검증하는 연구.
Motor-CAD Hybrid, FullFEA(TS), 해석적 방법(Volpe G2p, El-Hajji, Kim KDE)을 상호 비교.

**핵심 주제**: Motor-CAD Hybrid `/24` 공식이 왜 TS-FEA보다 과소평가하는가? → AF(Adjustment Factor) 정의 및 보정.

---

## Python 환경

```
가상환경: pyMotorEnv_310  (일반 venv, conda 아님)
Python: 3.10
필수 패키지: ansys-motorcad, ansys.motorcad.core (pymotorcad)
Motor-CAD COM 제어: pyMotorCAD / win32com
```

Motor-CAD COM이 필요한 스크립트는 반드시 이 환경에서 실행해야 함.

---

## 모터 파라미터 (e10, SC 모델)

| 항목 | 값 |
|---|---|
| .mot 경로 | `D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot` |
| 극쌍수 | p = 4 (8극) |
| 슬롯 | 48S / 8P |
| 권선 | 6턴 Hairpin (Single Conductor) |
| 최대 전류 | 460 A RMS (SC), 920 A RMS (SC 2병렬) |
| 활성 길이 | L_active = 0.150 m |
| 섹터 | 1/8 모델 (6 of 48 slots) |

### 도체 치수

| 모델 | w (접선) | h (반경) |
|---|---|---|
| HalfSC (k_r=1.5) | 5.5665 mm | 2.529 mm |
| SC | 7.422 mm | 3.372 mm |

---

## B 소스 구분 — 핵심 개념

> **반드시 구분해야 하는 두 가지 B 소스:**

| 구분 | 설명 | 폴더/파일 |
|---|---|---|
| **MS B** (σ=0) | 도체 무전도성 정자기해석 → Hybrid 공식의 입력 B | `elhajji_b_data/` (HalfSC), `sc_b_data_hybrid/` (SC, 추출 중) |
| **TS B** (σ≠0) | 과도 FEA, 와전류 반응 포함 | `sc_b_data/` (SC, FullFEA_Speed_*) |

Motor-CAD Hybrid `/24` 복제 시 반드시 MS B 사용. TS B로 Volpe G2p 계산 = 오류.

### B 샘플링 불일치

FEA 요소 면적 평균 B² → 1D/24 → MCAD 대비 **2.3~3.1×** 과대.
이유: Motor-CAD는 슬롯 암페어 모델(slot Ampere model) B를 사용 (훨씬 낮은 값).
→ AF로 이 차이를 흡수함. 코드 버그 아님.

---

## 핵심 파일 맵

### `acloss_ref_methods/`

| 파일 | 역할 |
|---|---|
| `mesh_b_vs_mcad.py` | **메인 비교 스크립트** — FEA 요소 B로 각 방법 계산 vs MCAD/TS |
| `volpe_hybrid_acloss.py` | Volpe G2p, El-Hajji 1D/24, 2D G2 공식 구현 |
| `kim_acloss.py` | Kim KDE 방법 구현 |
| `elhajji_2d_acloss.py` | HalfSC 해석 (MS B, `elhajji_b_data/`) |
| `elhajji_2d_fea_extract.py` | HalfSC B 추출 (Motor-CAD COM 필요) |
| `extract_sc_b_hybrid.py` | **SC MS B 추출** (Motor-CAD COM, `pyMotorEnv_310` 필요) |
| `extract_sc_b.py` | SC TS B 추출 (FullFEA_Speed_*) |
| `run_extract_sc_b_hybrid.bat` | Windows 실행 배치 파일 |

### B 데이터 폴더

| 폴더 | 내용 | 상태 |
|---|---|---|
| `elhajji_b_data/` | HalfSC MS B JSON (460A, 각 속도/위상) | ✅ 완료 |
| `sc_b_data/` | SC TS B JSON (FullFEA_Speed_*, 128스텝) | ✅ 있음 (TS B, Hybrid 복제에 부적합) |
| `sc_b_data_hybrid/` | SC MS B JSON (Hybrid_Speed_*, 6 cases) | ✅ 완료 |

### map_exports/e10/

| 경로 | 내용 |
|---|---|
| `SC/JEET_ACLoss_SC_Map_Summary.json` | SC Hybrid/FullFEA 스윕 결과 |
| `HalfSC/JEET_ACLoss_HalfSC_Map_Summary.json` | HalfSC 결과 |
| `SC/AF_RBF_model_SC.json` | AF RBF 모델 + Motor-CAD Lab 수식 |
| `SC/lab_af/AF_LabBase_poly10_formula.txt` | Lab 런타임 기반 재피팅 수식 (검증됨) |

---

## 현재 진행 상황 (2026-07-17)

### ✅ 완료 (2026-07-17)

- HalfSC 분석 (MS B): Vlp/TS = 1.12~1.63, AF = 1.3~2.7 → `halfsc_method_comparison_fig4.png`
- SC TS B 분석 (참고용): Vlp/TS = 0.70~1.12
- **SC MS B 추출 완료** (`sc_b_data_hybrid/`, 6 cases: 2k/4k/8k/16k × 920A)
- **SC MS B 분석 완료** (`mesh_b_vs_mcad.py sc_hybrid`):
  - Vlp/TS: 1.29(2k) → 1.17(4k) → 1.03(8k) → 0.88(16k, 36°) / 1.01(16k, 54°)
  - AF=TS/MCAD: 2.91 → 2.43 → 1.94 → 1.78 (속도 증가할수록 감소)
- **SC Figure 4 생성** → `figures/sc_hybrid_method_comparison_fig4.png`
- AF RBF 모델 구축 (SC): LOOCV MAE 4.69%
- B 샘플링 불일치 정량화: FEA 면적평균 B²는 MCAD 대비 2.25~3.11×
- CLAUDE.md 정비 (eMach, ACloss_Ref, JEET-2024_rev1, acloss_ref_methods)

### 🔜 남은 작업

- HalfSC 그리드 정규화 (VS Code에서 진행 중): `run_halfsc_normalize.py` — 5티어 [0.1/172.5/345/517.5/690A] × 4속도 × 6위상 = 240 records 재구성 (신규 116점 FEA)
- **JMAG MS SC → `devSurfInterp4HYBMS.m`** (MATLAB 실행만 남음):
  - 데이터 확보 완료: `E:\KDH\e10\MSConductorModel\...\e10MS_ConductorModel_SCL_Load~13\Case*\` (~2.4GB, 30 cases)
  - ⚠️ `Z:\Simulation`은 옛 NAS 경로 (언마운트) — 사용 금지
  - 케이스맵: `e10MS_ConductorModel_SCL_Load13_case_map.csv` (6전류×5위상, Case25=γ90°/368.1A)
  - wireTable 반경 176~179mm = SCL k_r=2 확인됨
  - 스크립트 위치: `eMach\mlxperPJT\JEET\Other\devSurfInterp4HYBMS.m`
- **Phase 3 Kturn** (`run_kturn_pipeline.py`, Motor-CAD 계열 — JMAG 무관):
  - 6턴·8턴 Motor-CAD LAB 시뮬레이션 실행
  - 8턴 ConductorHeight=1.173mm 클램핑 확인 필요

### ✅ 완료 확인 (2026-07-18)

- 논문 notation 수정 완료 (`JEET_KDH_rev5.tex`): 식 5 `[t]` 제거, subscript `0`, 식 2 `η_m`, PWM 한계 Conclusion 반영
- Motor-CAD Lab Custom Loss AF 입력 완료 (`lab_af/AF_LabBase_poly10_formula.txt`, `MotorLAB_elecdata_AF_poly10.mat`)
- **SC 16k/690A/90° 이상치 해결** (AF 0.474→1.068, 2026-07-17 15:37): `run_infill_group1.bat` 실행 완료, LOOCV 2.31%
- **Phase 2 infill 완료**: Group 1 + Group 2 모두 불필요 확인. `JEET_ACLoss_SC_Map_Summary.json` 240 records.
- **Phase 3 파이프라인 생성**: `run_kturn_pipeline.py` (Stage 1 .mot 생성 + Stage 2 AC 손실 sweep)
- **Lab AF 주입 효율맵**: 시도했으나 speed-only 제약·음수클리핑으로 효과 미미 → Fig14 현행 4패널 유지
- **HalfSC 690A 256 records** 추가됨 (그리드 정규화 방향 미결정, 사용자 결정 대기)

---

## 실행 방법

```bash
# HalfSC 분석 (이미 데이터 있음)
python mesh_b_vs_mcad.py halfsc

# SC TS B 분석 (참고용, B 소스 부적합)
python mesh_b_vs_mcad.py sc

# SC MS B 분석 (sc_b_data_hybrid/ 완성 후)
python mesh_b_vs_mcad.py sc_hybrid

# HalfSC 해석식 비교 (elhajji_2d_acloss.py)
python elhajji_2d_acloss.py
```

---

## AF 핵심 수치

| 모델 | 운전점 | Vlp/MCAD | Vlp/TS | AF(TS/MCAD) |
|---|---|---|---|---|
| HalfSC | 2k rpm, 36° | ~1.12 | ~1.12 | ~1.3 |
| HalfSC | 16k rpm, 36° | ~1.63 | ~1.63 | ~2.7 |

> **AF = TS / MCAD** — 다음을 포함:
> 1. TS B vs MS B 차이 (고속에서 커짐)
> 2. FEA 면적평균 B² vs MCAD 슬롯 암페어 모델 (~2.5×)
> 3. 기타 수치 오차

---

## 관련 문서

- `notes/CONTEXT_GUIDE.md` — Morisco 10-Step, Volpe/El-Hajji 방법 수식 정리
- `notes/PLAN_Enhanced_Hybrid_ACLoss_Validation.md` — 검증 플랜
- `AC_Loss_Correction_Context.md` — AF 방법론 A/B, Motor-CAD Lab Custom Loss
- `AF_MCAD_CONTEXT.md` — AF RBF 모델, 파일 맵, Lab 입력 현황
