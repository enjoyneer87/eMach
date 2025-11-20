# AEDT Utilities

PyAEDT를 사용한 ANSYS Electronics Desktop 자동화 유틸리티 패키지

## 설치

```bash
# 패키지 디렉토리에서
pip install -e .
```

또는 직접 import:

```python
import sys
sys.path.append(r'd:\KangDH\Emlab_emach\pyAEDT')
from aedt_utils import smartAedtConnector, getRunningMaxwell2d
```

## 기능

### 1. Connection 유틸리티

AEDT Desktop 연결 관리:

```python
from aedt_utils import smartAedtConnector, quickConnect

# 스마트 연결 (자동으로 최선의 방법 선택)
desktop = smartAedtConnector()

# 빠른 연결 (기존 세션만)
desktop = quickConnect()
```

### 2. Maxwell 유틸리티

Maxwell 2D 디자인 자동 연결:

```python
from aedt_utils import getRunningMaxwell2d

# 현재 실행 중인 Maxwell 2D 연결
m2d = getRunningMaxwell2d()
if m2d:
    print(f"Design: {m2d.design_name}")
    print(f"Variables: {list(m2d.variable_manager.variables.keys())}")
```

## 모듈 구조

```
aedt_utils/
├── __init__.py          # 패키지 초기화 및 공개 API
├── connection.py        # Desktop 연결 유틸리티
├── maxwell.py           # Maxwell 관련 유틸리티
└── README.md           # 문서 (이 파일)
```

## API 레퍼런스

### Connection 모듈

- `getAedtProcessesDetailed()`: 실행 중인 AEDT 프로세스 상세 정보
- `tryConnectToExistingDesktop()`: 기존 Desktop 세션 연결 시도
- `tryConnectWithPorts(port_list)`: 특정 포트로 연결 시도
- `getDesktopConnection()`: 다양한 방법으로 Desktop 연결 시도
- `checkCurrentDesktopStatus(desktop)`: Desktop 상태 확인 및 출력
- `smartAedtConnector()`: 스마트 연결 (권장)
- `quickConnect()`: 빠른 연결 (기존 세션만)
- `forceNewSession()`: 강제로 새 세션 생성

### Maxwell 모듈

- `getRunningMaxwell2d(aedt_version, non_graphical)`: 실행 중인 Maxwell 2D 연결

## 사용 예시

### 예시 1: 기본 연결

```python
from aedt_utils import smartAedtConnector

# Desktop 연결
desktop = smartAedtConnector()

if desktop:
    # 프로젝트 열기
    project = desktop.open_project(r"C:\path\to\project.aedt")
    
    # 디자인 리스트 확인
    designs = project.GetTopDesignList()
    print(f"디자인 목록: {designs}")
```

### 예시 2: Maxwell 2D 작업

```python
from aedt_utils import getRunningMaxwell2d

# Maxwell 2D 연결
m2d = getRunningMaxwell2d()

if m2d:
    # Post-processing
    all_objects = m2d.modeler.object_names
    
    # Field plot
    plot = m2d.post.plot_field(
        quantity="Mag_B",
        assignment=all_objects,
        plot_type="Surface",
        show=False,
        mesh_on_fields=True,
        file_format="case"
    )
```

### 예시 3: 프로세스 정보 확인

```python
from aedt_utils import getAedtProcessesDetailed

# 실행 중인 AEDT 프로세스 확인
processes = getAedtProcessesDetailed()

for proc in processes:
    print(f"PID: {proc['pid']}, Ports: {proc['ports']}")
```

## 설정

기본 설정은 `connection.py`에서 변경 가능:

```python
AEDT_VERSION = "2025.2"  # AEDT 버전
NUM_CORES = 8             # 사용할 코어 수
NG_MODE = False          # 비그래픽 모드 (False = GUI 표시)
```

## 요구사항

- Python 3.8+
- PyAEDT
- psutil
- ANSYS Electronics Desktop 2024.2 이상

## 라이선스

MIT License

## 작성자

KangDH
