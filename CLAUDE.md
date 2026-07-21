# eMach — Claude Code Context

> 이 레포지토리는 전기모터 설계 프레임워크 (eMach).  
> 연구자: 강도현 | 작업 갈래: `mlxperPJT/thermal/` (열해석, **현재 활성**) · `mlxperPJT/JEET/` (AC 손실 논문)

---

## 레포 구조

```
eMach/
├── +mcad/              Motor-CAD MATLAB 인터페이스 함수들
├── tools/
│   └── motorCAD/pyMCAD/  Python Motor-CAD 유틸리티 (fea_workflow, magnetic 등)
├── mlxperPJT/
│   ├── thermal/        ★ 현재 활성 → thermal/HANDOFF_20260721.md 참조
│   └── JEET/           AC 손실 JEET 논문 → JEET/CLAUDE.md 참조
└── Class/              모터 설계 클래스
```

## 현재 주 작업 — 모터 열해석 (2026-07-21 기준)

→ **`mlxperPJT/thermal/HANDOFF_20260721.md`** 가 전체 핸드오프다. 먼저 읽을 것.

JAC279 방식 하이브리드 열해석(3D FEM 능동부 + 열등가회로 냉각계)을 PyMAPDL 로
재현. **대상은 실제 Toyota Prius 모터**(OD 269 / 적층 83.8mm / 8극48슬롯 V-IPM).

- ✅ **MAPDL ↔ Fluent 교차검증 통과** — 코일 온도 1°C 이내 일치
  (저부하 88.3/88.3, 고부하 250A 119.2/118.2°C). 로터·자석은 MAPDL이 13~20°C 높은데
  에어갭을 순수 전도로 봐서 회전 유동 강화가 빠진 것 — 알려진 한계, 버그 아님.
- ✅ 표준 viz 패키지 `thermal_viz.py` + `prius/scripts/render_prius_viz.py`
- ⏳ **Icepak 3-way 비교 미완** — 발산 원인까지 규명(유체 Region이 HTC벽을 단락),
  고정온도 경계로 수렴(coil 176°C). 냉각 경계 다듬고 마무리하면 됨.
- 🚨 **viz 21MB Google Drive 업로드가 도중에 끊겼다.** 검증 전 `git rm` 금지 — 핸드오프 §5b.

⚠️ 모터가 둘이다: `Electric_Motor_IcepakFEA_AEDT_3D_part1`(Ansys 워크샵 템플릿)과
Prius 는 **서로 다른 모터**다. 초기 커밋 결과를 Prius 결과로 읽지 말 것.

## ★ 열해석 코드 재사용 원칙 (필수)

**새 모델(MAPDL/Icepak/Fluent/FreeFlow)을 처음부터 다시 짜지 말 것.** 아래 패키지된
코드를 재사용·확장하고, 공통 로직은 함수/모듈로 뽑아 중복을 줄인다. scratchpad 에서
임시로 만들었으면 검증 후 반드시 `mlxperPJT/thermal/` 하위로 패키지화한다.

| 용도 | 재사용 모듈/패키지 |
|---|---|
| 결과 시각화(GIF/PNG 표준세트, 3d_cut·circuit·대시보드) | `thermal/thermal_viz.py` (`ThermalViz`, `render_standard_viz`) |
| Prius MAPDL+Fluent 파이프라인 | `thermal/prius/scripts/` (01 손실→02 메시→03 MAPDL→05~07 Fluent, 08 워터재킷) |
| Prius Icepak(전도+재킷 대류) | `thermal/prius/icepak/` |
| FreeFlow/e10 (오일냉각) | `thermal/freeflow/scripts/` (01 Motor-CAD손실→03 STL→CDB→04 MAPDL열, 05~07 viz) |
| STL(watertight)→gmsh 체적메시→SOLID87 CDB | `freeflow/scripts/03_stl_to_cdb.py` |
| Maxwell/Motor-CAD 손실 추출 | Prius 01 / freeflow 01 (Motor-CAD 파라미터는 **ActiveXParametersMotorCADv261.txt** 참조) |

- 같은 패턴(STL→메시, SOLID87+대류 열해석, 손실추출)이 반복되면 공통 함수로 승격.
- 새 스크립트는 기존 번호체계·네이밍·경로 규약을 따를 것.

## 다른 갈래

→ **`mlxperPJT/JEET/CLAUDE.md`** (AC 손실 검증, SC Hybrid MS B 추출)

## Python 환경

```
가상환경: pyMotorEnv_310  (일반 venv, conda 아님)
Motor-CAD COM: ansys.motorcad.core (ansys-motorcad 패키지)
pyMCAD 경로:  eMach/tools/motorCAD/
```

⚠️ **Motor-CAD `get_variable`/`set_variable` 파라미터명은 반드시
`eMach/ActiveXParametersMotorCADv261.txt` 를 참조해 정확히 쓸 것** (임의 추측 금지).
- 손실(PM 동기기, 카테고리 "Loss and Injected Power Values"):
  구리 `Armature_Winding_Loss_Total`, 고정자철손 `Loss_[Stator_Back_Iron]`+`Loss_[Stator_Tooth]`,
  회전자철손 `Loss_[Rotor_Back_Iron]`+`Loss_[Rotor_Tooth]`, 자석 `Loss_[Magnet]`.
- 그 txt는 Number,Input/Output,**Automation Name**,Category,Units,... 컬럼 CSV. Automation
  Name 이 곧 get_variable 인자. (IM* 은 유도기 전용이니 PM 모터에 쓰지 말 것.)

## 주요 MATLAB 함수 (+mcad/)

| 함수 | 역할 |
|---|---|
| `loadAcLossJson.m` | AC 손실 JSON → MATLAB 구조체 |
| `buildAcLossFactor.m` | AC 손실 → SyRE용 kAC(freq) 변환 |
| `getMCADLabDataFromMotFile.m` | .mot → Lab 맵 데이터 |
| `saveSyreFluxMap.m` | SyRE 플럭스맵 저장 |
