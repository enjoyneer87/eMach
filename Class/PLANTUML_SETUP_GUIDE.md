# PlantUML VS Code Setup Guide

## 설치 완료 사항

아래 설정이 자동으로 적용되었습니다:

### 1. **VS Code 설정 (.vscode/settings.json)**

```json
"plantuml.render": "PlantUMLServer",
"plantuml.server": "https://www.plantuml.com/plantuml",
"plantuml.exportFormat": "png",
"plantuml.exportOutDir": "./diagrams",
"plantuml.previewAutoUpdate": true,
"files.associations": {
  "*.puml": "plaintext"
}
```

### 2. **권장 플러그인 (.vscode/extensions.json)**

✅ **jebbs.plantuml** — PlantUML 도표 미리보기 & 렌더링  
✅ **ms-python.python** — Python 언어 지원  
✅ **ms-toolsai.jupyter** — Jupyter Notebook 지원  

다른 플러그인도 권장됩니다.

### 3. **키보드 단축키 (.vscode/keybindings.json)**

| 단축키 | 기능 |
|--------|------|
| **Alt + D** | 현재 PlantUML 문서 미리보기 |
| **Alt + E** | 현재 문서를 PNG로 내보내기 |
| **Ctrl + Shift + Alt + E** | 전체 워크스페이스 내보내기 |

### 4. **워크스페이스 설정 (emlab_emach.code-workspace)**

PlantUML 설정이 전체 워크스페이스에 적용되었습니다.

---

## 🚀 사용 방법

### **방법 1: Alt + D로 미리보기 열기**

1. `.puml` 파일을 VS Code에서 열기
2. **Alt + D** 누르기
3. 우측에 PlantUML 다이어그램 미리보기 나타남

### **방법 2: 커맨드 팔레트 사용**

1. **Ctrl + Shift + P** 열기
2. "plantuml" 검색
3. 원하는 명령 선택:
   - **PlantUML: Preview** — 미리보기 (Alt+D)
   - **PlantUML: Export Current Diagram** — PNG 저장 (Alt+E)
   - **PlantUML: Export Workspace** — 전체 내보내기

### **방법 3: 우클릭 컨텍스트 메뉴**

1. `.puml` 파일 우클릭
2. "PlantUML: Preview" 선택

---

## 🔧 설정 설명

### **plantuml.render: "PlantUMLServer"**
- **온라인 서버** 사용 (Java 설치 불필요)
- 인터넷이 있으면 자동 작동
- 권장: ✅ (가장 간단함)

### **plantuml.server: "https://www.plantuml.com/plantuml"**
- 공식 PlantUML 온라인 렌더러
- 무료, 별도 설정 불필요

### **plantuml.exportFormat: "png"**
- 내보내기 형식: PNG (고품질 이미지)
- 대안: "svg" (벡터), "pdf" (문서 삽입 용)

### **plantuml.exportOutDir: "./Class/diagrams"**
- 내보낸 다이어그램이 저장될 디렉토리
- 자동 생성됨

### **plantuml.previewAutoUpdate: true**
- 파일 저장 시 자동으로 미리보기 갱신
- 권장: ✅

---

## ✅ 동작 확인 체크리스트

- [ ] **jebbs.plantuml 플러그인 설치 확인**
  - VS Code 확장 탭 → "plantuml" 검색 → 설치된 상태 확인
  
- [ ] **설정 적용 확인**
  - VS Code 설정 (Ctrl+,) → "plantuml" 검색 → 위 설정 확인
  
- [ ] **파일 연결 확인**
  - `.puml` 파일 열기 → 언어 모드가 "plaintext"로 표시되는지 확인
  
- [ ] **미리보기 테스트**
  - 아래 파일로 테스트:
    ```bash
    d:\KangDH\Emlab_emach\Class\pyMotorGeo_Architecture.puml
    ```
  - Alt + D 누르기 → 우측에 다이어그램 나타나야 함

---

## 🛠️ 문제 해결

### **문제 1: "PlantUML 플러그인을 찾을 수 없음"**

**해결책:**
```powershell
# VS Code 명령 팔레트에서
Ctrl + Shift + P
> "Extensions: Install Extensions"
> "jebbs.plantuml" 검색 및 설치
```

### **문제 2: 미리보기에 아무것도 안 보임**

**원인 & 해결:**

1. **인터넷 연결 확인**
   - PlantUMLServer가 온라인 서버 사용
   - VPN이 차단할 수 있음 → VPN 끄고 시도

2. **설정 재로드**
   ```
   Ctrl + Shift + P → "Reload Window"
   ```

3. **다른 렌더러 시도**
   - 설정에서 `plantuml.render`를 다른 값으로 변경:
   ```json
   "plantuml.render": "PlantUMLServer"  // ← 현재값
   // 대안을 시도하려면 아래 주석 해제
   // "plantuml.render": "Local"  // Java 필요
   ```

### **문제 3: "서버에 접속할 수 없음" 오류**

**가능한 원인:**
- 🌐 인터넷 끊김
- 🔒 방화벽/프록시 차단

**해결책:**
```json
// settings.json에서 다른 서버 시도:
"plantuml.server": "https://kroki.io"  // 대안 서버
```

### **문제 4: 파일이 "plaintext"로 열리지 않음**

**해결책:**
```
파일 우클릭 → "언어 모드 선택" → "plaintext" 선택
또는 파일 확장자가 ".puml"인지 확인
```

---

## 📚 유용한 링크

- **PlantUML 공식 사이트**: https://plantuml.com/
- **PlantUML 문법 가이드**: https://plantuml.com/guide
- **VS Code PlantUML 플러그인**: https://github.com/jebbs/vscode-plantuml
- **PlantUML 온라인 에디터**: https://www.plantuml.com/plantuml/uml/

---

## 📁 제공된 UML 다이어그램

현재 디렉토리에 다음 파일들이 있습니다:

```
./Class/
├── pyMotorGeo_Architecture.puml         (클래스 & 컴포넌트)
├── pyMotorGeo_Workflow.puml            (시퀀스 다이어그램)
├── pyMotorGeo_Dependencies.puml        (모듈 의존성)
├── pyMotorGeo_DataTransform.puml       (데이터 변환)
├── pyMotorGeo_RotorTopologies.puml     (회전자 분류)
├── pyMotorGeo_StatorTopologies.puml    (고정자 분류)
├── pyMotorGeo_Refactoring_Plan.puml    (리팩토링 계획)
├── pyMotorGeo_CompletionStatus.puml    (완성도 맵)
├── diagrams/                            (내보낸 이미지 폴더)
└── UML_AND_ARCHITECTURE.md             (종합 가이드)
```

**각 `.puml` 파일에서:**
- 📌 **Alt + D** → 미리보기
- 📥 **Alt + E** → PNG 저장 (./diagrams에 저장됨)

---

## 💡 최적의 사용법

### **개발 중 (빠른 미리보기)**
```
1. Alt + D로 미리보기 열기
2. 우측 패널에서 실시간 확인
3. 파일 저장하면 자동으로 갱신
```

### **보고서 작성 시 (고품질 이미지)**
```
1. Alt + E로 PNG 내보내기
2. ./diagrams 폴더에서 고해상도 이미지 확인
3. 보고서에 삽입
```

### **발표 자료 시**
```
1. PlantUML 온라인 에디터에 코드 복사
   → https://www.plantuml.com/plantuml/uml/
2. SVG로 내보내기
3. Powerpoint/Keynote에 벡터로 삽입 (크기 조절 가능)
```

---

## ✨ 설정 완료!

모든 설정이 완료되었습니다. 이제 `.puml` 파일을 열고 **Alt + D**를 눌러 미리보기를 확인하세요!

🎉 **행운을 빕니다!**
