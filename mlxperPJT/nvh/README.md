# mlxperPJT/nvh — e10 전자계→구조 NVH 하중 (em2struct 실적용)

`tools/em2struct/` 프레임워크를 **e10 실모델**에 적용하는 프로젝트 갈래.
Motor-CAD(Maxwell) 에어갭 가진력을 e10 MAPDL 구조 메시로 맵핑·export 한다.

## 스크립트

| 파일 | 역할 |
|---|---|
| `extract_e10_bore_nodes.py` | e10 MAPDL 메시(`ff_e10_mesh_v2.cdb`, 1.11M절점)에서 **스테이터 보어 표면 절점**(mat=1, r≈0.0713, z=스택) 추출 → `data/e10_target_nodes.npz`. 스테이터 OD·권선엔드도 함께. |
| `e10_emforce_pipeline.py` | 보어절점을 타깃으로 에어갭 가진력 LSQ 맵핑 → MAPDL/LS-DYNA/Motion export + QA. 실 Motor-CAD 멀티포스 파일 있으면 사용, 없으면 e10 파라미터 에어갭 MST. |
| `e10_rotor_remote_force.py` | 로터측 rotorExcitation(8극) → 로터 OD 절점 **원격힘**(pilot+RBE3) MAPDL export + QA. |
| `e10_harmonic_response.py` | **NVH 하모닉 응답 실전**: 열메시 ETCHG→SOLID187, 스테이터(MAT1)+48 pilot/RBE3/MASS21, 자유-자유 모달(LANB) → 치 힘 FFT 상위 온도차수에서 FULL 하모닉 → OD 복소변위 추출(npz). 기본 loadPoint4(15000rpm, f_elec=1kHz). |
| `e10_harmonic_viz.py` | 하모닉 결과 시각화: 모드 vs 가진차수 / 차수별 OD 반경변위 / 지배차수 ODS(극좌표)+공간차수 FFT. |
| `e10_campbell_modes.py` | **Campbell 스윕**(5 운전점×5 차수 FULL 하모닉) + **모드형상 OD 추출**(40모드) → e10_campbell.npz / e10_mode_shapes.npz. |
| `e10_paper_figs.py` | 논문용 그림 패키지 figs/(fig01~07, 300dpi): 3D 모델·가진·ODS·모달비교·응답ERP·**Campbell**·**모드형상 3D**. exp_data/*.csv 있으면 fig06에 실측 자동 오버레이. |
| `exp_data/` | 실측 오버레이 인터페이스(스키마 README_exp.md). 현재 실측 없음 — CSV만 넣으면 자동 반영. |

## 실행

```bash
# 1) 타깃 절점 추출(MAPDL 런치, 260MB CDB, 수 분)
python mlxperPJT/nvh/extract_e10_bore_nodes.py
# 2) 맵핑 + export
PYTHONIOENCODING=utf-8 python mlxperPJT/nvh/e10_emforce_pipeline.py
```

## 검증된 결과 (2026-08-11)

- 타깃: 스테이터 보어 **48,439절점** / 로터 OD **66,326절점** / 스테이터 OD 19,554 / 권선엔드 64,006.
- 스테이터 소스: 실 Motor-CAD 멀티포스 48치×128스텝(또는 에어갭 MST 대체).
- 로터 소스: rotorExcitation 8극×128스텝(극당~3463N) → 8 pilot 원격힘(RBE3), 파일 1.5MB.
- 맵핑: LSQ, **합력 ~3e-15 · 모멘트 ~1e-14 보존**(기계정밀). 로터 QA에 8극 클러스터.
- export: `e10_emforce_mapdl.inp`(F 시간이력) · `_external.csv`(Mechanical External Data)
  · `_lsdyna.k`(*LOAD_NODE_POINT+*DEFINE_CURVE) · `_motion.csv`. 모두 **실제 MAPDL
  노드 ID** 사용. QA: `e10_emforce_qa.png`.

> 대용량 하중파일(.inp/.k/.csv)은 `.gitignore` — 재생성 가능. `data/e10_target_nodes.npz`
> (타깃 절점)만 버전관리.

## Motor-CAD 실 멀티포스 연동 (✅ 검증 완료)

`e10_emforce_pipeline.py` 는 실 Motor-CAD 멀티포스 export 가 있으면 우선 사용한다.
생성: Motor-CAD API `do_magnetic_calculation()` → `do_multi_force_calculation()` →
`export_multi_force_data(file)` (네이티브 **JSON** 출력).

```
mlxperPJT/thermal/freeflow/data/e10_multiforce.json   # v2026 네이티브
```

**실 데이터 검증(2026-08-11)**: e10Turn6V261.mot, loadPoint0 = 250rpm/498.8Nm.
48치 × 128스텝, 치당 반경·접선력(~1360N), f_elec 16.7Hz. `read_motorcad_multiforce`
로 파싱 → 보어 48,439절점에 LSQ 맵핑, 보존 4.9e-15/1.1e-14. QA 에 48치 힘 클러스터
뚜렷. 다른 운전점은 `MF_LOADPOINT` 환경변수(0~4)로 선택.

> 헤드리스 주의: `do_multi_force_calculation` 전 `set_variable("MessageDisplayState",2)`
> 로 다이얼로그 억제해야 hang 회피. (첫 시도 `get_magnetic_graph` 호출에서 헤드리스 hang.)

## 관련

- 프레임워크: [`tools/em2struct/README.md`](../../tools/em2struct/README.md)
- e10 열해석(같은 MAPDL 메시): `mlxperPJT/thermal/freeflow/`
