# [로컬 PC 전용] 통합 eMach 인터페이스 및 도면 시각화 작업 플랜

**목표:** 다양한 모터 설계 툴(DXF, JMAG, Motor-CAD 등)의 형상 데이터를 `pyMotorGeo`를 통해 완벽히 Import하고, 이를 표준화된 Contract(Payload)로 변환하여 웹 브라우저(Streamlit)에서 시각적으로 검증한다. (본 작업은 SciML 연동과 별개로 로컬 PC 환경에 집중하여 진행함)

## Phase 1: 형상 Import 및 표준화 브릿지 연동 (WS-A 기반)
- **Step 1-1. DXF/JSON Import 테스트 및 안정화:** `pyMotorGeo`의 기존 Reader 모듈을 테스트하여 회전자(Rotor), 고정자(Stator) 도면 노드/자성체 영역이 정상적으로 로드되는지 확인.
- **Step 1-2. 형상 Payload 변환 모듈 작성:** 파싱된 도면 데이터를 지난번에 작성한 표준 규격인 `GeometryPayload` (in `contracts.py`)로 완벽하게 매핑하는 브릿지 코드(`geometry_bridge.py`) 개발.

## Phase 2: Streamlit 기반 Geometry 검증 UI 구축 (WS-D 기반)
- **Step 2-1. 기본 대시보드 구조 개발 (`app.py`):** 사이드바(Sidebar)에서 파일(dxf, json 등)을 업로드할 수 있는 웹 기반 엔트리포인트 생성.
- **Step 2-2. 2D 형상 플로팅 인터페이스 구현:** 업로드된 도면이 `pyMotorGeo` 파서를 거쳐 해석된 결과를 Streamlit 화면 중앙에 Matplotlib 또는 PyVista를 이용해 렌더링 (Rotor / Stator 색상 구분 및 노드 표시).
- **Step 2-3. 표준 Contract 검증 뷰어:** 파싱된 형상이 `GeometryPayload` 요건을 100% 충족하는지(누락된 선분이나 영역이 없는지) JSON 형태로 검증해 주는 Health Check 패널 추가.

## Phase 3: 5대 패키지 확장성 확보 (이후 단계)
- **Step 3-1. Pyleecan/pyMCAD 형식 Export(추출) UI:** 시각화 결과가 문제없는 도면(Payload)을 Pyleecan이나 Motor-CAD가 읽을 수 있는 형태로 바로 내보낼 수 있는 버튼/로직 추가.
