# PyAEDT Doxygen 문서 생성 가이드

## 1. 사전 준비

그래프/클래스/콜 다이어그램 생성을 위해 Graphviz 와 Doxygen 을 설치합니다.

1. Graphviz 설치 (diagrams 필요)
   - <https://graphviz.org/download/> 에서 Windows 설치 파일 다운로드
   - 설치 후 `C:\Program Files\Graphviz\bin` 을 PATH 에 추가
2. Doxygen 설치
   - <https://www.doxygen.nl/download.html> 에서 Windows 설치 파일 다운로드
   - 설치 후 doxygen 실행 파일 경로를 PATH 에 추가

## 2. 실행 방법 (PowerShell)

```powershell
cd d:\KDH\gitEmach\eMach\pyAEDT\docs\doxygen
# 문서 생성
doxygen .\Doxyfile
```

## 3. 출력 위치

- HTML 진입점: `d:\KDH\gitEmach\eMach\pyAEDT\docs\doxygen\build\html\index.html`
- 브라우저에서 `index.html` 열어 탐색

## 4. 설정 주요 포인트

- INPUT: `D:/KDH/gitPyAEDT/pyaedt`
- PRIVATE/PROTECTED/STATIC 모두 추출 (내부 구조 분석 용이)
- Graphviz 기반 클래스/콜 그래프 활성화 (SVG + 인터랙티브)

## 5. 커스터마이징 제안

- 특정 디렉터리 제외: `EXCLUDE` 또는 `EXCLUDE_PATTERNS` 수정
- XML 출력 필요 시: `GENERATE_XML = YES` 로 변경 후 Sphinx + Breathe 연동
- 누락 경고 활성화: `WARN_IF_UNDOCUMENTED = YES`

## 6. 문제 해결

- 다이어그램 미출력: `dot -V` 로 Graphviz 동작 여부 확인
- 속도 저하: `CALL_GRAPH` / `CALLER_GRAPH` 를 `NO` 로 변경
- 경로 문제: Doxyfile 에서 슬래시(`/`) 사용은 Windows에서도 정상 인식

## 7. 다음 단계

- CI 통합: PowerShell 스크립트 또는 GitHub Actions 에서 doxygen 실행 후 `build/html` 아티팩트 업로드

즐거운 문서화 작업 되세요!
