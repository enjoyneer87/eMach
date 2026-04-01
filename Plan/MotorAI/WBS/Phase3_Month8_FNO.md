# 📅 Phase 3 - Month 8: MGN/FNO 추론 서버 통합

**기간:** 2026-11-01 ~ 2026-11-30  
**목표:** PhysicsNeMo MGN 중심으로 FNO 트랙을 병행하여 실시간 추론-시각화 루프 완성  
**키워드:** `PhysicsNeMo` `MGN` `FNO` `Inference` `Model Serving`

---

## ✅ 월간 완료 기준

- [ ] MGN 기본 서비스 경로를 FastAPI에 통합
- [ ] FNO 병행 실험 경로를 옵션으로 제공
- [ ] 모델 버전/체크포인트/지표 메타데이터 노출
- [ ] 실시간 파라미터 변경 -> 추론 -> 시각화 루프 동작
- [ ] Month 9 미분 가능 최적화 입력 포맷 동결

---

## 📆 Week 29 (Nov 2-6): 모델 서비스 아키텍처

> [!info]- 🎯 Week 29 목표
> 다모델(MGN/FNO) 라우팅과 버전관리 체계 고정

### Day 141-145

> [!todo]- 🤖 Agent A 임무
> - [ ] 모델 레지스트리 구조(MGN default, FNO optional) 구현
> - [ ] infer 요청에 model selector 파라미터 추가

> [!todo]- 🤖 Agent B 임무
> - [ ] 체크포인트 메타 스키마(version, data lineage) 정의
> - [ ] 모델 교체/롤백 운영 절차 문서화

---

## 📆 Week 30 (Nov 9-13): 실시간 루프 완성

> [!info]- 🎯 Week 30 목표
> UI와 서버 간 즉시 추론 체인 완성

### Day 146-150

> [!todo]- 🤖 Agent A 임무
> - [ ] 파라미터 입력 시 infer 호출 자동 트리거
> - [ ] 결과 지연 최소화를 위한 캐시 전략 적용

> [!todo]- 🤖 Agent B 임무
> - [ ] API latency/throughput 모니터링 구축
> - [ ] 실패 시 fallback(최근 성공 결과) 정책 구현

---

## 📆 Week 31 (Nov 16-20): 정확도/품질 검증

> [!info]- 🎯 Week 31 목표
> 모델 품질 지표를 운영 수준으로 표준화

### Day 151-155

> [!todo]- 🤖 Agent A 임무
> - [ ] |B| MAE, Bx/By MAE 계산 파이프라인 연결
> - [ ] 케이스별 오차 히트맵 자동 생성

> [!todo]- 🤖 Agent B 임무
> - [ ] 품질 리포트(`mgn_fno_validation_report.md`) 자동화
> - [ ] 지표 기준선 미달 시 경고 플래그 추가

---

## 📆 Week 32 (Nov 23-30): Month 9 인계

> [!info]- 🎯 Week 32 목표
> Differentiable Physics를 위한 입출력 계약 고정

### Day 156-160

> [!todo]- 🤖 Agent A 임무
> - [ ] 목표함수 입력 포맷(토크/손실/온도) 정리
> - [ ] Gradient-friendly 데이터 구조 초안 작성

> [!todo]- 🤖 Agent B 임무
> - [ ] 릴리즈 노트(`v0.8.0-mgn-fno-serving`) 작성
> - [ ] Month 9 테스트셋/시나리오 인계

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] MGN/FNO 역할 분담 기준 정리
> - [ ] 역설계 단계에서 필요한 제약조건 목록화

---

*← [[Phase3_Month7_Warp]] | → [[Phase3_Month9_DiffPhysics]]*