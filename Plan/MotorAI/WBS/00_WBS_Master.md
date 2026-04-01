# 📋 WBS Master Index - Motor AI Solution

**프로젝트:** Web-native 모터 물리 AI 솔루션  
**기간:** 2026-04-01 ~ 2027-03-31 (12개월)  
**전략:** CAD 교환 안정화 + SciML(MGN) 데이터/학습 파이프라인 병행 → 시각화/솔버 확장

---

## 📐 일과 구성 원칙

| 구분 | 역할 | 특징 |
|------|------|------|
| 🤖 **Agent A** | 코드 생성, 기능 구현 | 자율적으로 에이전트에게 위임 |
| 🤖 **Agent B** | 인프라, 테스트, 문서 | 자율적으로 에이전트에게 위임 |
| 📚 **내 공부** | 학습, 개념 이해, 설계 고민 | 천천히, 직접, 깊게 |

---

## 🗂️ 월별 파일 목록

### Phase 1: 기반 구축 (Apr ~ Jun 2026)
- [[Phase1_Month1_DataAdapter]] - `.h5` → VTK 어댑터 구축 ⭐ 상세 일별 WBS
- [[Phase1_Month2_Streamlit]] - Streamlit 3D 대시보드
- [[Phase1_Month3_BabylonJS]] - Babylon.js 입문 & 3D 렌더링
- [[01_ExecutionPlan_CADInterchange_and_UML_KO]] - CAD 교환 우선 + UML 기반 실행계획
- [[02_DevPlan_eMach_Compatibility_KO]] - eMach 중심 패키지 호환 개발 플랜 (Pyleecan/SyR-e + PhysicsNeMo MGN)
- [[03_DevPlan_eMach_Advanced_KO]] - eMach 전체 개발플랜 고도화안 (Program/Workstream/Gate 기반)

### Phase 2: 고성능 시각화 (Jul ~ Sep 2026)
- [[Phase2_Month4_FastAPI]] - FastAPI 바이너리 스트리밍
- [[Phase2_Month5_Shaders]] - GLSL Custom Shader & 컬러맵
- [[Phase2_Month6_InteractiveUI]] - 인터랙티브 UI (Clip/Tooltip)

### Phase 3: AI & 솔버 통합 (Oct ~ Dec 2026)
- [[Phase3_Month7_Warp]] - NVIDIA Warp GPU 커널
- [[Phase3_Month8_FNO]] - MGN/FNO 추론 서버 연동
- [[Phase3_Month9_DiffPhysics]] - 미분가능 시뮬레이션 (역설계)

### Phase 4: 최적화 & 패키징 (Jan ~ Mar 2027)
- [[Phase4_Month10_WASM]] - WebAssembly 적용
- [[Phase4_Month11_WebGPU]] - WebGPU 전환 검토
- [[Phase4_Month12_Deploy]] - Docker 배포 & IP 문서화

---

## 📊 전체 진행률

### Phase 1
- [ ] Month 1: 데이터 어댑터 (0/20일)
- [ ] Month 2: Streamlit 대시보드 (0/20일)
- [ ] Month 3: Babylon.js 입문 (0/20일)

### Phase 2
- [ ] Month 4: FastAPI 스트리밍 (0/20일)
- [ ] Month 5: GLSL Shader (0/20일)
- [ ] Month 6: Interactive UI (0/20일)

### Phase 3
- [ ] Month 7: NVIDIA Warp (0/20일)
- [ ] Month 8: FNO/MGN 연동 (0/20일)
- [ ] Month 9: Diff Physics (0/20일)

### Phase 4
- [ ] Month 10: WebAssembly (0/20일)
- [ ] Month 11: WebGPU (0/20일)
- [ ] Month 12: 최종 배포 (0/20일)

---

## 🔗 관련 파일
- [[00_Architecture]] - 전체 기술 아키텍처 다이어그램
- [[Daily_Log]] - 일별 개발 일지
