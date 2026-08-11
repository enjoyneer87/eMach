# mlxperPJT/nvh — e10 전자계→구조 NVH 하중 (em2struct 실적용)

`tools/em2struct/` 프레임워크를 **e10 실모델**에 적용하는 프로젝트 갈래.
Motor-CAD(Maxwell) 에어갭 가진력을 e10 MAPDL 구조 메시로 맵핑·export 한다.

## 스크립트

| 파일 | 역할 |
|---|---|
| `extract_e10_bore_nodes.py` | e10 MAPDL 메시(`ff_e10_mesh_v2.cdb`, 1.11M절점)에서 **스테이터 보어 표면 절점**(mat=1, r≈0.0713, z=스택) 추출 → `data/e10_target_nodes.npz`. 스테이터 OD·권선엔드도 함께. |
| `e10_emforce_pipeline.py` | 보어절점을 타깃으로 에어갭 가진력 LSQ 맵핑 → MAPDL/LS-DYNA/Motion export + QA. 실 Motor-CAD 멀티포스 파일 있으면 사용, 없으면 e10 파라미터 에어갭 MST. |
| `e10_rotor_remote_force.py` | 로터측 rotorExcitation(8극) → 로터 OD 절점 **원격힘**(pilot+RBE3) MAPDL export + QA. |

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
