# Legacy notebooks (superseded — 2026-07-16 백업)

`jeet_acloss_rbf` 패키지화 이후 혼선 방지를 위해 이동된 구 노트북들.
**새 작업은 이 파일들을 수정하지 말 것** — 아래 대체물을 사용.

## 대체 관계

| 구 노트북 | 대체 |
|---|---|
| `pyMotorCAD_Hybrid_AClossCode.ipynb` (원본 모놀리식) | `../JEET_AF_Pipeline.ipynb` |
| `pyMotorCAD_Hybrid_AClossCode_ReducedRBF.ipynb` (Ref) | `../JEET_AF_Pipeline.ipynb` (`MODEL_SCALE='Ref'`) |
| `pyMotorCAD_Hybrid_AClossCode_ReducedRBF_HalfSC.ipynb` | `../JEET_AF_Pipeline.ipynb` (`'HalfSC'`) |
| `pyMotorCAD_Hybrid_AClossCode_ReducedRBF_SC.ipynb` | `../JEET_AF_Pipeline.ipynb` (`'SC'`) |
| `pyMotorCAD_Hybrid_AClossCode_ReducedRBF_SC_Modular.ipynb` | `../JEET_AF_Pipeline.ipynb` — 이 노트북에서 `tools/jeet_acloss_rbf` 모듈이 추출됨 |
| `pyMotorCAD_Hybrid_AClossCode_Map.ipynb` | 파이프라인 `predict_af` / `make_af_map_figure` |
| `pyMotorCAD_Hybrid_AClossCode_Template copy.ipynb` | 수동 백업본 — `../pyMotorCAD_Hybrid_AClossCode_Template.ipynb` 사용 |
| `pyMotorCAD_Hybrid_AClossCode_Template_e4a.ipynb` | e4a 구형 모터용 — e10 체계에서 미사용 |

## 현행 워크플로

1. **데이터 생성** (Motor-CAD FEA sweep):
   `../pyMotorCAD_Hybrid_AClossCode_Template.ipynb` → `map_exports/e10/{모델}/JEET_ACLoss_*_Map_Summary.json`
2. **보정·검증·시각화**: `../JEET_AF_Pipeline.ipynb`
   (또는 Python에서 `jeet_acloss_rbf.AcLossPipeline`, MATLAB에서 `../pybridge/`)

## 주의

- 구 노트북들은 **base@2kRPM 커널·구 데이터 경로** 기준이라 현재 채택
  설정(base@16k, 상사 전달, SC 이상점 제외)과 수치가 다르다.
- 참조용으로만 열람할 것 (실행 시 지금은 없는 경로를 참조할 수 있음).
