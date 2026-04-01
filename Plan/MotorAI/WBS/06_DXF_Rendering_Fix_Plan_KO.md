# [이슈 트래킹] 로컬 Web UI `dxf` 파일 렌더링 문제 해결 계획
**대상 파일:** `TestCAD1.dxf`
**문제 요약:** 현재 Streamlit 환경(`app.py` & `geometry_bridge.py`)에서는 해당 DXF 파일을 업로드해도 형상(Line/Arc 등)이 노트북 환경 6번, 9번 셀처럼 선명하게 렌더링되지 않음. 반면, 데이터 파싱 자체는 가능하나 Arc 좌표 변환과 객체 렌더링 방식의 누락/부실로 인해 브라우저상에서 정상출력 안 됨.

## 1. 근본 원인 분석
1. **현재 `GeometryBridge`의 구현 한계:**
   - 현재 브릿지에서는 `DXF`의 `start`, `end`, `center`, `radius` 속성만 단순 추출하여 넘기고 있음.
   - 복잡한 호(Arc)나 원(Circle) 데이터, 또는 도면의 중심축(Offset)을 다루는 로직이 누락되어 있음 (현재 `pts`를 `[[0, 0], [0, 0]]`과 같이 임시 목업 처리하여 렌더링 불가능).

2. **`pyMotorGeo_v1.ipynb` 6번, 9번 셀의 작동 방식:**
   - 노트북 환경에서는 ezdxf 파서를 좀 더 고도화하거나, 파싱된 Entities(EntityInfo)들을 Matplotlib/PyVista 축(axes)에 정확하게 `plot`하는 전용 렌더링 코드가 작성되어 있음. 
   - 예를 들어, `np.linspace`를 이용한 Arc 보간, 회전/이동 변환(Transform)이 반영되어 렌더링에 적합한 좌표계 배열을 내뱉고 있음.

## 2. 개선 및 동기화 계획 (Phase 1.5)
- [ ] **Step 1: 렌더링 보간 로직(Arc / Circle) 강화**
  - **`geometry_bridge.py` 수정:** 노트북 6번 셀에서 사용하는 ezdxf `arc` 해석 로직을 브릿지에 반영. (시작점/종점 각도에 따라 점들을 촘촘하게 배열로 찍어내는 로직 추가).
  
- [ ] **Step 2: Streamlit `app.py` 시각화 로직 튜닝**
  - `GeometryBridge`에서 올라온 객체(`entities`)의 세부 정보 형식을 확인하여, Matplotlib에 그려질 때 노트북 9번 셀과 동일한 형태의 색상 및 해상도로 플로팅되도록 플롯 코드 개편.
  
- [ ] **Step 3: 영역 인식(Region Detection) 대응 준비 (예비)**
  - 현재 10번 셀부터 영역 인식이 안 되는 문제가 있다고 언급하셨음. 이는 단순 Line/Arc 렌더링을 넘어서 닫힌 폐곡면(Closed loop)을 추출하는 알고리즘(예: `pyMotorGeo`의 `extract_faces`나 `topology`) 문제로 판단됨.
  - 우선 기초적인 Edge(선분) 렌더링을 6/9번 셀과 동일하게 정상화한 뒤, 폐곡면 렌더링으로 확장할 것을 계획.

## 3. 다음 액션 방향
- 사용 중인 노트북 (`pyMotorGeo_v1.ipynb`) 6번, 9번 셀의 `plot` 및 `파싱` 로직 코드를 구체적으로 확인하여, 해당 라인들을 추출해 `geometry_bridge.py`와 `app.py`의 `st.pyplot` 부분에 이식하는 코딩 작업을 바로 이어가겠습니다.
