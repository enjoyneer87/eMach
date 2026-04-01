# eMach pyMotorGeo 배포 및 이식성 확보 계획 (Deployment & Portability Plan)

본 문서는 로컬 PC에서 개발 중인 **pyMotorGeo UI 및 브릿지 모듈**을 다른 팀원 컴퓨터로 원활하게 이식(전이)하고, 향후 완제품 형태로 배포하기 위한 3단계 전략을 정의합니다.

## 1. 개발 진행 단계 유지보수 (Dev / Sync 환경)
- **목적:** 현재 소스코드를 Git으로 공유하며 여러 명의 작업자가 동일한 환경을 바로 복원.
- **방식:** 
  - `requirements.txt` (또는 `environment.yml`) 동기화.
  - 저장소를 클론(`git clone`)한 후 `pip install -r Class/pyMotorGeo/ui/requirements.txt` 한 줄로 의존성(Streamlit, ezdxf, 등) 완벽 복원.
- **특징:** 개발 과정에서 가장 가볍고 직관적인 방식. 변경 사항 테스트에 유리함.

## 2. 데스크탑 개발자용 완제품 배포 (Local Package 배포)
- **목적:** 팀 외의 Ansys / Pyleecan 사용자나 엔지니어가 코드 수정 없이 UI 툴만 설치해서 사용할 수 있도록 제공.
- **방식:**
  - `pyMotorGeo` 폴더를 파이썬 공식 패키지 모듈 구조로 래핑 (`setup.py` 또는 `pyproject.toml` 작성).
  - 로컬 또는 사내 PyPI 망에 배포하여 사용자는 `pip install pymotorgeo` 명령어 실행.
  - 패키지 설치 후 터미널에 `pymotorgeo-ui`와 같은 간편 명령어(CLI)를 입력하면 내장된 Streamlit 서버가 자동으로 띄워지도록 Entrypoint 설정.
- **효과:** 소스코드 경로를 신경 쓰지 않고, 윈도우/맥/리눅스 어디서나 즉시 구동.

## 3. 클라우드 및 사내 인트라넷용 (Docker Container 배포)
- **목적:** OS, C++ 의존성 패키지, 시스템 PATH 등에 구애받지 않는 단일 통합 협업 포털 제공.
- **방식:**
  - Streamlit 대시보드와 파서 핵심 로직을 우분투 베이스 이미지에 세팅하는 `Dockerfile` 작성.
  - 사내 서버에 도커 이미지를 띄우고(`docker run -p 8501:8501 emach-viewer`), 엔지니어들은 웹 브라우저 링크만으로 접속하여 모터 도면의 검증 및 SciML 연동 수행.
- **효과:** 버전 충돌 원천 차단. GPU(TensorRT/Warp) 연동이 확정되는 Phase 3 시점에 필수적인 컨테이너화 작업 뼈대로 활용 가능.
