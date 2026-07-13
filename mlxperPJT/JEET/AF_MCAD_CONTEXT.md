# AF Factor → Motor-CAD Lab 입력 작업 컨텍스트

> 작성: 2026-07-12  
> 목적: AF Factor를 Motor-CAD Lab Custom Loss에 입력하기 위한 파일 맵 및 현황 정리

---

## 1. 핵심 발견 — 수식이 이미 JSON에 있음

`map_exports/e10/SC/AF_RBF_model_SC.json` 안에 Motor-CAD 입력용 수식이 이미 추출되어 있음:

| 필드 | 내용 |
|------|------|
| `mcad_formula_full` | 전체 RBF 항 (Method B 3D) — Motor-CAD Custom Loss 직접 입력 가능 |
| `mcad_formula_reduced_30` | 상위 30항으로 축약된 RBF 수식 |
| `mcad_formula_top20` | 상위 20항 수식 |
| `separable_model.mcad_formula` | f(speed) × g(Irms, Phase) 분리 모델 수식 |
| `separable_model.speed_poly_coeffs` | Method A 계수: `[-0.002504, 0.023917, 1.078604]` |

**Method A 수식 (속도 전용 2차 다항식):**
```
AF(s) = -0.002504·s² + 0.023917·s + 1.078604   (s: kRPM)
Motor-CAD Custom Loss = Stator_Copper_Loss_AC * (AF(Speed/1000) - 1)
```

**Model 3종:**
- `map_exports/e10/Ref/AF_RBF_model_Ref.json`
- `map_exports/e10/HalfSC/AF_RBF_model_HalfSC.json`
- `map_exports/e10/SC/AF_RBF_model_SC.json`

---

## 2. e10 AC 손실 데이터 (입력 데이터)

| 파일 | 모델 | 포인트 | 속도 | 비고 |
|------|------|--------|------|------|
| `map_exports/e10/JEET_ACLoss_180Map_Summary_20260620_055628.json` | SC | 180 (Hybrid90+FEA90) | 2k/4k/16k RPM | 메인 데이터 |
| `map_exports/e10/JEET_ACLoss_4Speed_Map_Summary_20260620_204151.json` | SC | 추가 | 8k RPM 보완 | |
| `map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary_e4.json` | Ref | — | — | |
| `map_exports/e10/HalfSC/JEET_ACLoss_HalfSC_Map_Summary.json` | HalfSC | — | — | |
| `map_exports/e10/SC/JEET_ACLoss_SC_Map_Summary.json` | SC | — | — | |
| `map_exports/e10/SC/AF_infill_schedule_SC.json` | SC | 10점 | 16kRPM 보강 | Phase2 보강 대기 |

---

## 3. AF 계산 노트북/파이썬 파일 (핵심)

### Jupyter 노트북 (AF 계산 주체)

| 파일 | 역할 |
|------|------|
| `pyMotorCAD_Hybrid_AClossCode_ReducedRBF_SC.ipynb` | ★ **SC 메인** — Hybrid/FullFEA 스윕, RBF AF 빌드, JSON 출력 |
| `pyMotorCAD_Hybrid_AClossCode_ReducedRBF.ipynb` | Ref 모델용 |
| `pyMotorCAD_Hybrid_AClossCode_ReducedRBF_HalfSC.ipynb` | HalfSC 모델용 |
| `pyMotorCAD_Hybrid_AClossCode_ReducedRBF_SC_Modular.ipynb` | SC Modular 구조 버전 |
| `pyMotorCAD_Hybrid_AClossCode.ipynb` | 기본 스윕 코드 (데이터 수집) |
| `pyMotorCAD_Hybrid_AClossCode_Map.ipynb` | dq 평면 AC 손실 맵 |
| `pyMotorCAD_Hybrid_AClossCode_Template.ipynb` | 스윕 템플릿 |

### Python 파일 (서포트)

| 파일 | 역할 |
|------|------|
| `_mcad_parallel_worker.py` | Motor-CAD API 병렬 스윕 (Hybrid/FullFEA 포인트 실행) |
| `verify_af_data_quality.py` | AF 데이터 LOOCV 검증 도구 |
| `run_kturn_pipeline.py` | Kturn 스윕 파이프라인 (Phase3) |
| `tools/motor_scaling/morphisms/AcLossCorrector.py` | AF RBF 예측 적용 (Python 효율맵용) |
| `tools/motor_scaling/model/RbfModelParams.py` | RBF 모델 파라미터 관리 |

---

## 4. MATLAB 파일 맵

### +mcad 네임스페이스 (함수)

| 파일 | 역할 |
|------|------|
| `+mcad/loadAcLossJson.m` | AC 손실 JSON → MATLAB 구조체 로드 |
| `+mcad/buildAcLossFactor.m` | AC 손실 데이터 → SyRE용 kAC(freq) 변환 (완성) |
| `+mcad/getMCADLabDataFromMotFile.m` | .mot → Lab 맵 데이터 추출 |
| `+mcad/fromMCAD_lab_json.m` | Motor-CAD Lab JSON 파싱 |
| `+mcad/saveSyreFluxMap.m` | SyRE 플럭스맵 저장 |
| `+mcad/fromFitResult.m` | FluxMap_dq 구조체 변환 |

### mlxperPJT/JEET (스크립트)

| 파일 | 역할 |
|------|------|
| `gen_e10_satumap.m` | Motor-CAD ActiveX → e10_SatuMap.mat 생성 |
| `gen_e10_satumap_from_mot.m` | .mot 파싱 → e10_SatuMap.mat 생성 (ActiveX 불필요) |
| `test_phase1_verify.m` | Phase 1 검증 스크립트 |
| `test_mcad_to_syre.m` | MCAD→SyRE 연동 테스트 |

### Calc/MCAD (기존 개발 히스토리 — 참고용)

| 파일 | 내용 |
|------|------|
| `Calc/MCAD/deve10_MCAD_refACLoss.m` | e10 Ref AC 손실 계산 (초기 버전) |
| `Calc/MCAD/deve10_MCAD_refACLoss_v24.m` | v24 업데이트 |
| `Calc/MCAD/deve10_MCAD_SCACLoss.m` | SC AC 손실 계산 |
| `Calc/MCAD/deve10_MCAD_SCACLoss_v24.m` | SC v24 |
| `Calc/MCAD/Comparison_e10MCAD.m` | Ref/SC 비교 |
| `Calc/MCAD/devSurfMCADACLossMap.m` | dq 서피스 맵 개발 |

---

## 5. Motor-CAD Lab Custom Loss 입력 — 현재 미완성

> ⚠️ **[2026-07-12 판명된 스케일 버그]** 아래 Method A 수식은 사용 금지.
> `separable_model.speed_poly_coeffs`는 절대 AF가 아니라 f(s)·g(I,θ) 분해의 **정규화된
> 속도 인자 f(s)**일 뿐이다 (절대 스케일은 g에 있음). 실측 AF 중앙값은 2k=1.74 / 4k=1.53 /
> 8k=1.27 / 16k=1.35인데 이 다항식은 1.12/…/0.82를 줘서 보정이 크게 과소(16k에선 음수)가 된다.
> 실측 검증 및 대체 수식(Lab 런타임 베이스 재피팅 B-poly10, median 4.8%):
> `map_exports/e10/SC/lab_af/AF_LabBase_poly10_formula.txt`,
> 검증 데이터 `map_exports/e10/SC/lab_af/runtime_vs_json_hybrid_full.csv`,
> 스크립트 `verifyLabVsEmag_e10.m` 참조.

### 해야 할 것

Motor-CAD Lab의 **Internal Custom Loss** 필드에 아래 수식을 프로그래매틱하게 입력하는 코드:

```python
# Method A (속도 전용 — 단순, Lab 적용 용이)  ← ⚠️ 위 경고 참조: 스케일 버그, 사용 금지
formula_A = "Stator_Copper_Loss_AC * (-0.002504*(Speed/1000)**2 + 0.023917*(Speed/1000) + 0.078604)"

# Motor-CAD API 예시 (pyMotorCAD)
mcad.SetVariable("InternalLossCalcType", 1)  # Internal Custom Loss 활성화
mcad.SetVariable("InternalLossFormula", formula_A)
mcad.SetVariable("InternalLossElecType", 1)  # Electrical type
```

### 참고: Motor-CAD Lab Custom Loss 관련 변수명 확인 필요

`AC_Loss_Correction_Context.md` §3 참조:
- Loss type: **Internal**, **Electrical**
- 제어 반영 조건: `Speed`, `Id`, `Iq` 기반 Internal Loss만 MTPA 탐색에 반영
- Method B (Id/Iq 포함)는 MTPA 최적점 변화에도 영향

### 다음 작업 목표

1. Motor-CAD Python API (`pythoncom` / `win32com`)로 `.mot` 파일 열기
2. 정확한 Custom Loss 변수명 확인 (`GetVariable("InternalLossFormula")`로 현재값 읽기)
3. Method A 수식 설정 → Lab 빌드 → 효율맵 계산 → 결과 추출
4. (선택) Method B (3D RBF) 수식 설정 → 비교

---

## 6. 현재 검증 수치

| 모델 | LOOCV MAE | Train MAE | 비고 |
|------|-----------|-----------|------|
| Ref | 1.48% | — | ✅ 양호 |
| HalfSC | 2.13% | — | ✅ 양호 |
| SC | 4.69% | — | ⚠️ 16k/90° 코너 문제 → Phase 2 보강 예정 |

> SC JSON 내 `validation.LOOCV_MAE_pct=41.7%`는 **구버전 수치**. 현재 4.69%.

---

## 7. e10 모터 파라미터 (Motor-CAD 설정 기준)

- `.mot` 경로: `D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot`
- 극쌍수: 4 (`p_pairs=4`)
- 최대 전류: 460 A RMS
- DC 버스: 720 V
- 슬롯/극: 48S/8P
- 권선: 6턴 Hairpin (SC 모델)
