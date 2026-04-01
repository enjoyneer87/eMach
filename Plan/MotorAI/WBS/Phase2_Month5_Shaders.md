# 📅 Phase 2 - Month 5: GLSL Shader & 컬러맵 고도화

**기간:** 2026-08-01 ~ 2026-08-31  
**목표:** CAE 해석 결과를 GPU 셰이더에서 실시간 컨투어로 표현하는 시각화 엔진 완성  
**키워드:** `GLSL` `Babylon.js` `Contour` `ColorMap` `Render Optimization`

---

## ✅ 월간 완료 기준

- [ ] 스칼라 필드 기반 커스텀 컨투어 셰이더 구현
- [ ] 동적 컬러맵/범위 변경 실시간 반영
- [ ] 단면/투명도/강조 표현 셰이더 옵션 제공
- [ ] 렌더링 성능 최적화(FPS 기준선 달성)
- [ ] Month 6 인터랙티브 UI 기능과 호환되는 셰이더 API 고정

---

## 📆 Week 17 (Aug 3-7): 셰이더 기반 구축

> [!info]- 🎯 Week 17 목표
> 셰이더 파이프라인과 데이터 바인딩 확정

### Day 81-85

> [!todo]- 🤖 Agent A 임무
> - [ ] vertex/fragment 셰이더 기본 골격 작성
> - [ ] 스칼라값 -> 컬러맵 텍스처 샘플링 구현

> [!todo]- 🤖 Agent B 임무
> - [ ] 셰이더 파라미터 스펙 문서화
> - [ ] 브라우저별 렌더링 호환성 점검표 작성

---

## 📆 Week 18 (Aug 10-14): 컨투어/오차맵 고도화

> [!info]- 🎯 Week 18 목표
> GT/MGN/FNO 비교에 필요한 시각화 기능 확보

### Day 86-90

> [!todo]- 🤖 Agent A 임무
> - [ ] 오차맵 전용 컬러 스케일(절대오차/상대오차) 추가
> - [ ] threshold 강조 및 등고선 라인 옵션 구현

> [!todo]- 🤖 Agent B 임무
> - [ ] 컬러맵 표준 프리셋(viridis/turbo/RdBu) 구성
> - [ ] 사용자 설정 저장(local storage 또는 설정 API) 구현

---

## 📆 Week 19 (Aug 17-21): 성능/품질 튜닝

> [!info]- 🎯 Week 19 목표
> 고해상도 메쉬에서도 실시간 상호작용 유지

### Day 91-95

> [!todo]- 🤖 Agent A 임무
> - [ ] LOD/decimation 렌더링 경로 적용
> - [ ] draw call 최소화 및 shader branching 최적화

> [!todo]- 🤖 Agent B 임무
> - [ ] FPS/메모리/로드시간 계측 자동화
> - [ ] 성능 기준선 리포트 작성

---

## 📆 Week 20 (Aug 24-31): Month 6 연계 준비

> [!info]- 🎯 Week 20 목표
> 인터랙티브 UI 기능 통합을 위한 인터페이스 마감

### Day 96-100

> [!todo]- 🤖 Agent A 임무
> - [ ] clip/tooltip/scalar bar 연동용 셰이더 hook 제공
> - [ ] 월말 데모 씬 정리

> [!todo]- 🤖 Agent B 임무
> - [ ] 릴리즈 노트(`v0.5.0-shader-core`) 작성
> - [ ] Month 6 통합 테스트 케이스 초안 작성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 컬러맵이 해석 판단에 미치는 영향 정리
> - [ ] Month 6 UX 요구사항 재검토

---

*← [[Phase2_Month4_FastAPI]] | → [[Phase2_Month6_InteractiveUI]]*