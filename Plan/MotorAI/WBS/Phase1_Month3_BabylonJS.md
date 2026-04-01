# 📅 Phase 1 - Month 3: Babylon.js 입문 & Web 전환 준비

**기간:** 2026-06-01 ~ 2026-06-30  
**목표:** Streamlit 내부 프로토타입을 웹 네이티브 3D 클라이언트(Babylon.js)로 이행하기 위한 기반 완성  
**키워드:** `TypeScript` `Babylon.js` `Mesh` `Float32Array` `FastAPI`

---

## ✅ 월간 완료 기준

- [ ] TypeScript + Babylon.js 프로젝트 템플릿 완성
- [ ] 모터 메쉬 로드(STL/OBJ/VTU 변환산출) 및 카메라 제어
- [ ] FastAPI mock 데이터로 물리량 컬러맵 표시
- [ ] GT vs MGN 결과 비교 뷰 UI 초안 완성
- [ ] Month 4(FastAPI) 연계용 데이터 인터페이스 고정

---

## 📆 Week 9 (Jun 1-5): 프론트엔드 기반 구축

> [!info]- 🎯 Week 9 목표
> Babylon.js 실행 환경과 기본 렌더링 파이프라인 확보

### Day 41-43

> [!todo]- 🤖 Agent A 임무
> - [ ] Vite + TypeScript + Babylon.js 초기 프로젝트 구성
> - [ ] 기본 Scene/Camera/Light/Control 템플릿 구현

> [!todo]- 🤖 Agent B 임무
> - [ ] ESLint/Prettier/빌드 스크립트 표준화
> - [ ] 개발/배포 환경 변수 템플릿(.env.example) 작성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Babylon.js Playground 핵심 예제 3개 실습
> - [ ] WebGL 좌표계/카메라 개념 복습

### Day 44-45

> [!todo]- 🤖 Agent A 임무
> - [ ] STL/OBJ 메쉬 로더 연결 및 기준 모델 렌더링
> - [ ] Orbit/Pan/Zoom UX 튜닝

> [!todo]- 🤖 Agent B 임무
> - [ ] 로딩/오류/빈데이터 상태 UI 컴포넌트 제작
> - [ ] 프론트 성능 측정 베이스라인(FPS, load time) 설정

---

## 📆 Week 10 (Jun 8-12): 데이터 인터페이스 연결

> [!info]- 🎯 Week 10 목표
> 백엔드 연계를 위한 데이터 타입/전송 규격 고정

### Day 46-48

> [!todo]- 🤖 Agent A 임무
> - [ ] Float32Array 기반 vertex/scalar 버퍼 적용
> - [ ] 기본 컬러맵 렌더링(viridis/turbo) 구현

> [!todo]- 🤖 Agent B 임무
> - [ ] 프론트 데이터 계약(TypeScript interface) 정의
> - [ ] mock API 응답 생성기 및 계약 테스트 작성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] TypedArray 메모리 구조 이해
> - [ ] Streamlit vs Babylon.js UX 차이 비교 메모

### Day 49-50

> [!todo]- 🤖 Agent A 임무
> - [ ] 단면(clip plane) 토글 프로토타입 구현
> - [ ] 스칼라바/범례 UI 초안 적용

> [!todo]- 🤖 Agent B 임무
> - [ ] 데이터 스키마 버전 필드(v1) 적용
> - [ ] Month 4 연계를 위한 API 요구사항 문서화

---

## 📆 Week 11-12 (Jun 15-30): 비교 뷰 및 통합 준비

> [!info]- 🎯 Week 11-12 목표
> GT vs MGN 비교 시나리오의 UI 흐름과 성능 한계 확인

### Day 51-55

> [!todo]- 🤖 Agent A 임무
> - [ ] 2-pane 비교 뷰(GT/MGN) 화면 구성
> - [ ] 오차맵(|GT-MGN|) 레이어 표시

> [!todo]- 🤖 Agent B 임무
> - [ ] 케이스 선택/시간스텝 상태관리 스토어 구성
> - [ ] 브라우저 메모리 사용량 및 드롭프레임 계측

### Day 56-60

> [!todo]- 🤖 Agent A 임무
> - [ ] 월말 통합 데모(로컬 mock + UI) 정리
> - [ ] Month 4 이관 체크리스트 작성

> [!todo]- 🤖 Agent B 임무
> - [ ] Known issues 및 기술부채 로그 등록
> - [ ] 릴리즈 노트(`v0.3.0-web-foundation`) 초안

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 실제 엔지니어 사용 흐름으로 10분 시연 리허설
> - [ ] 다음 달 API/스트리밍 우선순위 정리

---

*← [[Phase1_Month2_Streamlit]] | → [[Phase2_Month4_FastAPI]]*