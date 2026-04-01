# 📅 Phase 3 - Month 9: Differentiable Physics & 역설계 PoC

**기간:** 2026-12-01 ~ 2026-12-31  
**목표:** Warp + MGN/FNO 결합으로 성능 목표 기반 형상 가이드 PoC 구현  
**키워드:** `Differentiable Physics` `Optimization` `Inverse Design` `Warp`

---

## ✅ 월간 완료 기준

- [ ] 목표함수(토크/손실 등) 미분 가능 계산 경로 1개 이상 구현
- [ ] 제약조건 포함 설계 업데이트 루프 PoC 완성
- [ ] 역설계 후보 형상 제안 결과 리포트 생성
- [ ] 안전장치(발산 방지/범위 제한) 적용
- [ ] Phase 4 제품화 이전의 기술 리스크 정리

---

## 📆 Week 33 (Dec 1-4): 목적함수 정식화

> [!info]- 🎯 Week 33 목표
> 역설계에서 사용할 목적함수/제약조건 고정

### Day 161-164

> [!todo]- 🤖 Agent A 임무
> - [ ] 토크 최대화/손실 최소화 목적함수 코드화
> - [ ] 제약조건(기하, 전류, 열) 적용 구조 구현

> [!todo]- 🤖 Agent B 임무
> - [ ] 목적함수 검증 케이스셋 준비
> - [ ] 발산/불안정 감지 규칙 정의

---

## 📆 Week 34 (Dec 7-11): 미분 루프 구현

> [!info]- 🎯 Week 34 목표
> gradient 기반 업데이트 루프의 최소 동작 확보

### Day 165-170

> [!todo]- 🤖 Agent A 임무
> - [ ] gradient 계산 -> 파라미터 업데이트 루프 구현
> - [ ] step size/regularization 실험

> [!todo]- 🤖 Agent B 임무
> - [ ] 수렴 로그/체크포인트 저장 체계 구축
> - [ ] 실패 케이스 자동 저장 및 재현 스크립트 작성

---

## 📆 Week 35 (Dec 14-18): 결과 해석 및 안정화

> [!info]- 🎯 Week 35 목표
> 역설계 결과의 공학적 타당성 점검

### Day 171-175

> [!todo]- 🤖 Agent A 임무
> - [ ] 제안 형상에 대한 surrogate/solver 교차 검증
> - [ ] 성능 개선량(기준 대비) 자동 계산

> [!todo]- 🤖 Agent B 임무
> - [ ] 결과 대시보드(목표 달성률, 제약 위반률) 작성
> - [ ] 역설계 보고서 템플릿 정리

---

## 📆 Week 36 (Dec 21-31): Phase 4 인계

> [!info]- 🎯 Week 36 목표
> 제품화/배포 관점으로 기술 부채 정리

### Day 176-180

> [!todo]- 🤖 Agent A 임무
> - [ ] PoC 코드 리팩터링 및 모듈 경계 정리
> - [ ] 운영 모드/실험 모드 분리

> [!todo]- 🤖 Agent B 임무
> - [ ] 릴리즈 노트(`v0.9.0-diff-physics-poc`) 작성
> - [ ] Phase 4 착수 문서(배포/최적화 요구사항) 작성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 역설계 결과를 실제 설계 의사결정에 쓰는 기준 정리
> - [ ] Phase 4에서 유지할 기능과 실험기능 구분

---

*← [[Phase3_Month8_FNO]] | → [[Phase4_Month10_WASM]]*