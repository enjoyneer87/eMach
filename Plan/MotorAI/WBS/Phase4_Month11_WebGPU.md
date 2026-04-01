# 📅 Phase 4 - Month 11: WebGPU 전환 검토

**기간:** 2027-02-01 ~ 2027-02-28  
**목표:** WebGL2 기반 한계를 분석하고 WebGPU 적용 가능성/효용을 검증  
**키워드:** `WebGPU` `GPU Compute` `Rendering` `Compatibility`

---

## ✅ 월간 완료 기준

- [ ] WebGPU 적용 후보 기능 2개 이상 선정
- [ ] PoC 경로 1개 이상 동작 확인
- [ ] WebGL2 대비 성능/복잡도 비교표 작성
- [ ] 브라우저/플랫폼 호환성 리스크 분석
- [ ] Month 12 배포 전략에 반영할 결론 도출

---

## 📆 Week 41 (Feb 1-5): 조사 및 설계

> [!info]- 🎯 Week 41 목표
> WebGPU 전환 범위와 성공 기준 확정

### Day 201-205

> [!todo]- 🤖 Agent A 임무
> - [ ] WebGPU로 옮길 렌더링/컴퓨트 경로 선정
> - [ ] 최소 PoC 아키텍처 다이어그램 작성

> [!todo]- 🤖 Agent B 임무
> - [ ] 브라우저 지원 매트릭스 작성
> - [ ] 폴백(WebGL2) 전략 정의

---

## 📆 Week 42 (Feb 8-12): PoC 구현

> [!info]- 🎯 Week 42 목표
> 핵심 경로 1개 실동작 확보

### Day 206-210

> [!todo]- 🤖 Agent A 임무
> - [ ] WebGPU 파이프라인 초기화 및 버퍼 전송 구현
> - [ ] 컨투어 또는 compute 경로 PoC 실행

> [!todo]- 🤖 Agent B 임무
> - [ ] 디버그 도구/로그 수집 체계 구축
> - [ ] 실패 케이스 재현 시나리오 정리

---

## 📆 Week 43 (Feb 15-19): 비교 평가

> [!info]- 🎯 Week 43 목표
> 전환 타당성을 수치로 판단

### Day 211-215

> [!todo]- 🤖 Agent A 임무
> - [ ] WebGL2 vs WebGPU FPS/latency 비교
> - [ ] 코드 복잡도/유지보수 난이도 평가

> [!todo]- 🤖 Agent B 임무
> - [ ] 의사결정 매트릭스(성능/리스크/개발비용) 작성
> - [ ] Phase 4 최종 전략 초안 작성

---

## 📆 Week 44 (Feb 22-28): 전략 확정

> [!info]- 🎯 Week 44 목표
> 배포 직전의 기술 스택 결론 도출

### Day 216-220

> [!todo]- 🤖 Agent A 임무
> - [ ] 유지 스택(WebGL2 중심 + 선택 WebGPU) 확정
> - [ ] 필요한 코드 정리 및 실험 분리

> [!todo]- 🤖 Agent B 임무
> - [ ] 릴리즈 노트(`v1.1.0-webgpu-eval`) 작성
> - [ ] Month 12 배포 체크리스트 업데이트

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 성능만이 아닌 운영 리스크 관점에서 기술 선택 리뷰
> - [ ] 최종 배포에서 반드시 필요한 기능 우선순위 재정렬

---

*← [[Phase4_Month10_WASM]] | → [[Phase4_Month12_Deploy]]*