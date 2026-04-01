# Action 01 Benchmark Case Registry (Draft)

작성일: 2026-04-01
목적: benchmark 10-case의 ID, 데이터 위치, 입력 규격을 고정한다.

## 규칙
- 케이스 ID는 B001~B010으로 고정한다.
- 경로 변경 시 노션 Dev Plan DB와 동시에 갱신한다.
- 원본/전처리/결과 경로를 분리 기록한다.

## Registry
| Case ID | Source Type | Source Path | Payload Path | Note |
|---|---|---|---|---|
| B001 | DXF | _mcad_exports/case01/model.dxf | Class/pyMotorGeo/contract_examples/case01_geometry_payload_v1.json | draft |
| B002 | DXF | _mcad_exports/case02/model.dxf | Class/pyMotorGeo/contract_examples/case02_geometry_payload_v1.json | draft |
| B003 | DXF | _mcad_exports/case03/model.dxf | Class/pyMotorGeo/contract_examples/case03_geometry_payload_v1.json | draft |
| B004 | DXF | _mcad_exports/case04/model.dxf | Class/pyMotorGeo/contract_examples/case04_geometry_payload_v1.json | draft |
| B005 | DXF | _mcad_exports/case05/model.dxf | Class/pyMotorGeo/contract_examples/case05_geometry_payload_v1.json | draft |
| B006 | H5/TXT | pyMCAD/case06 | Class/pyMotorGeo/contract_examples/case06_ml_dataset_payload_v1.json | draft |
| B007 | H5/TXT | pyMCAD/case07 | Class/pyMotorGeo/contract_examples/case07_ml_dataset_payload_v1.json | draft |
| B008 | DXF | _mcad_exports/case08/model.dxf | Class/pyMotorGeo/contract_examples/case08_geometry_payload_v1.json | draft |
| B009 | DXF | _mcad_exports/case09/model.dxf | Class/pyMotorGeo/contract_examples/case09_geometry_payload_v1.json | draft |
| B010 | DXF | _mcad_exports/case10/model.dxf | Class/pyMotorGeo/contract_examples/case10_geometry_payload_v1.json | draft |

## 변경 이력
- 2026-04-01: 초안 생성 (AUTO-NONML)
