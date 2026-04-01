# 자동 생성된 UML 다이어그램 정리

작성일: 2026-04-01  
상태: ✅ **자동 생성 완료**  
방법: Python AST 분석 (자동 코드 추출)

---

## 📊 생성된 UML 파일

### 1. **Auto_Pyleecan_AllClasses_UML.puml** ⭐ (추천)
- **265개 모든 Pyleecan 클래스** 자동 추출
- **2400줄** PlantUML 코드
- 그룹화된 구조:
  - Machine Types (12개): SCIM, DFIM, IPMSM, SyRM, etc.
  - Lamination (적층 구조)
  - Slot Types (50+): W-series, M-series, etc.
  - Bore Geometries (회전자 표면)
  - Geometric Primitives (Arc, Line, Circle, Surface)
  - Other Classes (200+)
- **상속 관계** 자동으로 표시

### 2. **Auto_Pyleecan_Classes_UML_generated.puml**
- 초기 생성 버전
- 6개 핵심 클래스 (Machine, Lamination, Output, etc.)
- 빠른 참조용

### 3. 수동 작성 UML (이전 버전)
- 02_Pyleecan_Architecture_UML.puml (수정됨)
- 06_eMach_pyMotorGeo_Real_Architecture.puml (신규)
- 04_MotorAI_Integration_UML.puml (수정됨)

---

## 🔍 분석 결과

### Pyleecan 클래스 계층

**추출된 상속 관계:**
```
Machine (root)
  ├── MachineAsync (비동기 모터)
  │   ├── MachineSCIM
  │   ├── MachineDFIM
  │   └── ...
  ├── MachineSync (동기식 모터)
  │   ├── MachineIPMSM
  │   ├── MachineSyRM
  │   ├── MachineLSPM
  │   ├── MachineSRM
  │   ├── MachineSIPMSM
  │   └── ...
  └── MachineUD (사용자정의)

Lamination (적층)
  ├── LamSlot (슬롯 적층)
  ├── LamHole (자석 구멍)
  └── LamSquirrelCage (cage rotor)

Slot (기본 슬롯)
  ├── SlotCirc
  ├── SlotW* (W10~W30: 유도 모터)
  ├── SlotM* (M10~M63: PM 회전자)
  └── SlotUD (사용자정의)

Bore (회전자 표면 형상)
  ├── BoreFlower
  ├── BoreLSRPM
  ├── BoreSinePole
  └── BoreUD
```

**기하학 프리미티브:**
```
Arc (기본) → Arc1, Arc2, Arc3
Circle
Line
Surface → SurfLine, SurfRing
```

---

## ✅ 자동 생성의 장점

1. **정확성**: 실제 코드에서 직접 추출
2. **완성도**: 265개 모든 클래스 포함
3. **최신성**: 코드 변경 시 자동 업데이트 가능
4. **상속관계**: 자동으로 --|> 표기

---

## 🚀 사용 방법

### 온라인 PlantUML 렌더러로 보기:
1. [PlantUML Online Editor](http://www.plantuml.com/plantuml/uml/) 방문
2. Auto_Pyleecan_AllClasses_UML.puml 내용 copy-paste
3. 다이어그램 렌더링 확인

### VS Code에서 보기:
1. PlantUML 확장 설치: `PlantUML` (jebbs)
2. .puml 파일 오른쪽 클릭 → "Preview Current Diagram"
3. 또는 Alt+D

### PNG/SVG로 export:
```bash
# PlantUML CLI 필요 (Java 필요)
plantuml Auto_Pyleecan_AllClasses_UML.puml -o output_folder
```

---

## 📋 eMach 자동 UML 생성

동일한 방식으로 eMach/pyMotorGeo도 생성 가능:

```bash
python generate_uml_comprehensive.py  # Pyleecan용
```

eMach용으로 수정하면:
```python
classes_dir = r'd:\KangDH\Emlab_emach\Class\pyMotorGeo'
```

---

## 🔧 다음 단계

1. **Auto_Pyleecan_AllClasses_UML.puml** 사용 (메인 문서)
2. 필요에 따라 클래스 필터링 (예: Machine + Lamination만)
3. eMach도 동일 스크립트로 생성
4. PlantUML 직접 수정 필요시 minimal 버전 만들기

---

## 📝 생성 스크립트

**generate_uml_comprehensive.py** - 모든 클래스 자동 분석:
- 272개 .py 파일 스캔
- AST (Abstract Syntax Tree) 분석
- 클래스/상속/메서드 추출
- PlantUML 코드 생성

**특징:**
- 오류 처리 (파서 실패 시 skip)
- 카테고리별 그룹화 (자동 패키지)
- 상속 관계 자동 추출
- 최대 5개 메서드/속성만 표시 (복잡도 제어)

---

## 📊 통계

| 메트릭 | 값 |
|-------|-----|
| 분석된 Python 파일 | 271개 |
| 추출된 클래스 | 265개 |
| 생성된 PlantUML 줄 | 2400줄 |
| 머신 타입 | 12개 (SCIM, IPMSM, etc.) |
| 슬롯 타입 | 50+ (W, M 시리즈) |
| 상속 관계 | 자동 추출됨 |

---

## 💡 권장사항

✅ **사용하세요:**
- Auto_Pyleecan_AllClasses_UML.puml (265개 클래스, 완전)

⚠️  **주의:**
- PlantUML 온라인 에디터는 큰 다이어그램 렌더링이 느릴 수 있음
- 필요시 클래스를 필터링하여 부분 UML 생성

❌ **하지 않아도 됨:**
- 수동으로 UML 작성 (자동 생성 버전 사용)
- 코드 변경 시마다 수동 업데이트 (자동 스크립트 재실행)

