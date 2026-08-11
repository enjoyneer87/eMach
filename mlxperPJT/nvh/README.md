# mlxperPJT/nvh — e10 전자계→구조 NVH 하중 (em2struct 실적용)

`tools/em2struct/` 프레임워크를 **e10 실모델**에 적용하는 프로젝트 갈래.
Motor-CAD(Maxwell) 에어갭 가진력을 e10 MAPDL 구조 메시로 맵핑·export 한다.

## 스크립트

| 파일 | 역할 |
|---|---|
| `extract_e10_bore_nodes.py` | e10 MAPDL 메시(`ff_e10_mesh_v2.cdb`, 1.11M절점)에서 **스테이터 보어 표면 절점**(mat=1, r≈0.0713, z=스택) 추출 → `data/e10_target_nodes.npz`. 스테이터 OD·권선엔드도 함께. |
| `e10_emforce_pipeline.py` | 보어절점을 타깃으로 에어갭 가진력 LSQ 맵핑 → MAPDL/LS-DYNA/Motion export + QA. 실 Motor-CAD 멀티포스 파일 있으면 사용, 없으면 e10 파라미터 에어갭 MST. |

## 실행

```bash
# 1) 타깃 절점 추출(MAPDL 런치, 260MB CDB, 수 분)
python mlxperPJT/nvh/extract_e10_bore_nodes.py
# 2) 맵핑 + export
PYTHONIOENCODING=utf-8 python mlxperPJT/nvh/e10_emforce_pipeline.py
```

## 검증된 결과 (2026-08-11)

- 타깃: 스테이터 보어 **48,439절점**(r∈[0.0713,0.0725], z=[-0.2075,-0.0575]).
- 소스: e10 에어갭 Maxwell 응력(8극 회전파 + 48슬롯 하모닉, 16000rpm, 24 시간스텝).
- 맵핑: LSQ, **합력 3e-15 · 모멘트 9e-15 보존**(기계정밀).
- export: `e10_emforce_mapdl.inp`(F 시간이력) · `_external.csv`(Mechanical External Data)
  · `_lsdyna.k`(*LOAD_NODE_POINT+*DEFINE_CURVE) · `_motion.csv`. 모두 **실제 MAPDL
  노드 ID** 사용. QA: `e10_emforce_qa.png`.

> 대용량 하중파일(.inp/.k/.csv)은 `.gitignore` — 재생성 가능. `data/e10_target_nodes.npz`
> (타깃 절점)만 버전관리.

## Motor-CAD 실 멀티포스 연동

`e10_emforce_pipeline.py` 는 아래 경로에 실 Motor-CAD 멀티포스 export 가 있으면
자동 사용한다(우선). 생성: Motor-CAD API `do_multi_force_calculation()` +
`export_multi_force_data(file)`. → `tools/em2struct` `read_motorcad_nvh` 로 파싱
(export 헤더에 맞춰 `col_map` 조정).

```
mlxperPJT/thermal/freeflow/data/e10_multiforce.csv  (또는 .txt)
```

## 관련

- 프레임워크: [`tools/em2struct/README.md`](../../tools/em2struct/README.md)
- e10 열해석(같은 MAPDL 메시): `mlxperPJT/thermal/freeflow/`
