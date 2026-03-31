# PlantUML 설정 체크리스트 & 다음 단계

## ✅ 자동 설정 완료 사항

- [x] `.vscode/settings.json` — PlantUML 설정 추가
- [x] `.vscode/extensions.json` — jebbs.plantuml 권장 플러그인 등록
- [x] `.vscode/keybindings.json` — 단축키 설정 (Alt+D, Alt+E 등)
- [x] `emlab_emach.code-workspace` — 워크스페이스 레벨 설정
- [x] `./Class/diagrams/` — 내보내기 폴더 생성
- [x] `PLANTUML_SETUP_GUIDE.md` — 상세 가이드 문서
- [x] `.vscode/plantuml_config_alternatives.json` — 대체 설정 옵션

---

## 🚀 다음 단계 (5단계)

### **Step 1: VS Code 재로드** (1분)

VS Code를 **완전히 종료**하고 다시 열기:
```
Ctrl + Shift + P → "Developer: Reload Window"
또는
VS Code 완전 종료 → 다시 열기
```

### **Step 2: PlantUML 플러그인 확인** (1분)

1. **좌측 확장 탭** 열기 (또는 Ctrl+Shift+X)
2. "plantuml" 검색
3. **jebbs.plantuml** 설치 확인
   - 설치됨: "Disable" 버튼 표시
   - 미설치: "Install" 누르기

### **Step 3: 설정 확인** (1분)

VS Code 설정 열기 (Ctrl+,):
```
"plantuml" 검색 → 아래 항목 확인:
✓ Render: PlantUMLServer
✓ Server: https://www.plantuml.com/plantuml
✓ Export Format: png
✓ Export Out Dir: ./Class/diagrams
✓ Preview Auto Update: 체크됨
```

### **Step 4: 테스트** (2분)

1. 아래 파일 중 하나 열기:
   ```
   d:\KangDH\Emlab_emach\Class\pyMotorGeo_Architecture.puml
   ```

2. **Alt + D** 누르기
   - ✅ 우측에 다이어그램 나타나야 함
   - ❌ 비어있음 → "문제 해결" 섹션 참고

3. **Alt + E** 눌러 PNG 내보내기
   - ✅ `./Class/diagrams/` 폴더에 이미지 생성되어야 함

### **Step 5: 앞으로 사용** (계속)

```
각 .puml 파일에서:
➊ Alt + D        → 빠른 미리보기 (개발 중)
➋ Alt + E        → PNG 내보내기 (보고서)
➌ Ctrl+Shift+Alt+E → 전체 내보내기 (배치)
```

---

## ❓ 확인 질문

### **Q1: PlantUML 플러그인이 설치되어 있나요?**

```powershell
# VS Code 확장 탭에서 "jebbs.plantuml" 검색
# "Install" 또는 "Disable" 버튼 보이나?
```

- ✅ 보임 → 설치됨 (Step 2 완료)
- ❌ 안 보임 → Step 2에서 설치

### **Q2: 파일이 plaintext 언어로 감지되나요?**

파일을 열었을 때 우측 상태바 확인:
```
[plaintext]  또는  [Plain Text]  표시되나?
```

- ✅ 표시됨 → 정상
- ❌ 다른 언어 표시 → 파일 우클릭 → "언어 모드 선택" → "plaintext"

### **Q3: Alt + D를 눌렀을 때 미리보기가 나오나?**

```
우측에 "PlantUML Preview" 패널이 나타나고
다이어그램이 보이나?
```

- ✅ 보임 → 완벽! 🎉
- ❌ 안 보임 → "🛠️ 문제 해결" 섹션 참고

---

## 🛠️ 문제 해결

### **상황 1: 미리보기가 비어있음**

**원인:**
1. 인터넷 연결 끊김
2. 방화벽/프록시 차단
3. PlantUML 서버 다운

**해결책:**
```json
// .vscode/settings.json에서 다른 서버 시도:
"plantuml.server": "https://kroki.io"
```

또는 Reload Window (Ctrl+Shift+P → Reload):
```
Ctrl + Shift + P → "Reload Window"
```

### **상황 2: 플러그인이 안 보임**

**원인:** jebbs.plantuml 설치 안 됨

**해결책:**
```
Ctrl + Shift + X → "jebbs.plantuml" 검색 → Install
```

### **상황 3: Alt + D 단축키가 안 먹힘**

**원인:**
- 다른 플러그인이 같은 단축키 사용
- keybindings.json 설정 미적용

**해결책:**
```
Ctrl + Shift + P → "Keyboard Shortcuts" 검색
→ "plantuml preview" 검색 → 단축키 재설정
또는
Ctrl + Shift + P → "Reload Window"
```

### **상황 4: 느린 렌더링**

**원인:** PlantUML 공식 서버 혼잡

**해결책:**
```json
// .vscode/settings.json:
"plantuml.server": "https://kroki.io"
```

---

## 📋 최종 체크리스트

모두 ✅ 되면 완료!

- [ ] VS Code 재로드됨 (Reload Window)
- [ ] jebbs.plantuml 플러그인 설치됨
- [ ] `plantuml.puml` 파일 열 수 있음
- [ ] Alt + D로 미리보기 실행됨
- [ ] 우측에 다이어그램 표시됨
- [ ] Alt + E로 PNG 내보내기 됨
- [ ] `./Class/diagrams/` 폴더에 이미지 저장됨

---

## 🎉 완료!

모두 ✅ 되었다면 축하합니다! 🎊

이제 8개의 UML 다이어그램을 자유롭게 볼 수 있습니다:

```
pyMotorGeo_Architecture.puml       → Alt + D로 미리보기
pyMotorGeo_Workflow.puml           → Alt + D로 미리보기
pyMotorGeo_Dependencies.puml       → Alt + D로 미리보기
pyMotorGeo_DataTransform.puml      → Alt + D로 미리보기
pyMotorGeo_RotorTopologies.puml    → Alt + D로 미리보기
pyMotorGeo_StatorTopologies.puml   → Alt + D로 미리보기
pyMotorGeo_Refactoring_Plan.puml   → Alt + D로 미리보기
pyMotorGeo_CompletionStatus.puml   → Alt + D로 미리보기
```

---

## 📚 참고 자료

- 📖 **PLANTUML_SETUP_GUIDE.md** — 상세 가이드 및 팁
- ⚙️ **.vscode/plantuml_config_alternatives.json** — 대체 설정 옵션
- 🌐 **PlantUML 공식**: https://plantuml.com/
- 📝 **문법 가이드**: https://plantuml.com/guide

---

**설정 완료! Happy Diagramming! 🎨**
