# 📅 Phase 3 - Month 7: NVIDIA Warp 도입

**기간:** 2026-10-01 ~ 2026-10-31  
**목표:** Warp 기반 GPU 커널로 실시간 물리 계산 경로의 가능성 검증  
**키워드:** `NVIDIA Warp` `GPU Kernel` `Physics` `Acceleration`

---

## ✅ 월간 완료 기준

- [ ] Warp 개발 환경 구성 및 재현 스크립트 확정
- [ ] 핵심 물리 연산 1종 이상 GPU 커널 구현
- [ ] Python 기준 구현 대비 정확도/속도 비교 리포트 작성
- [ ] FastAPI 또는 내부 파이프라인과 커널 연계 성공
- [ ] Month 8 추론 연동을 위한 인터페이스 정리

---

## 📆 Week 25 (Oct 1-2): 환경/벤치 준비

> [!info]- 🎯 Week 25 목표
> Warp 실험의 재현 가능한 환경과 기준선 수립

### Day 121-123

> [!todo]- 🤖 Agent A 임무
> - [ ] Warp 설치/기동 검증 스크립트 작성
> - [ ] 기준 물리 연산 Python 버전 baseline 확정

> [!todo]- 🤖 Agent B 임무
> - [ ] GPU/드라이버/CUDA 버전 매트릭스 문서화
> - [ ] 벤치마크 입력셋(소/중/대) 고정

---

## 📆 Week 26 (Oct 5-9): 커널 구현 1차

> [!info]- 🎯 Week 26 목표
> 최소 동작 커널(MVP) 확보

### Day 124-128

> [!todo]- 🤖 Agent A 임무
> - [ ] 전자기 관련 기초 연산 커널 구현
> - [ ] 커널 입력/출력 텐서 계약 정의

> [!todo]- 🤖 Agent B 임무
> - [ ] 정확도 검증 테스트(허용오차) 작성
> - [ ] 실패 케이스 로깅 체계 구성

---

## 📆 Week 27 (Oct 12-16): 성능 최적화

> [!info]- 🎯 Week 27 목표
> 실행속도 개선 및 병목 파악

### Day 129-134

> [!todo]- 🤖 Agent A 임무
> - [ ] 메모리 접근 패턴 최적화
> - [ ] 커널 실행 프로파일링 기반 튜닝

> [!todo]- 🤖 Agent B 임무
> - [ ] 속도/정확도 비교 대시보드 작성
> - [ ] 케이스별 성능 리포트 자동 생성

---

## 📆 Week 28 (Oct 19-31): 파이프라인 연계

> [!info]- 🎯 Week 28 목표
> Warp 결과를 서비스/시각화 흐름에 연결

### Day 135-140

> [!todo]- 🤖 Agent A 임무
> - [ ] FastAPI 내부 호출 또는 배치 실행 연계
> - [ ] UI에 Warp 결과 레이어 노출 시범 구현

> [!todo]- 🤖 Agent B 임무
> - [ ] 릴리즈 노트(`v0.7.0-warp-prototype`) 작성
> - [ ] Month 8(MGN/FNO 통합) 인계 체크리스트 작성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Warp 미분 가능 연산 개념 학습
> - [ ] Month 8에서 결합할 모델/물리 경계 재정의

---

*← [[Phase2_Month6_InteractiveUI]] | → [[Phase3_Month8_FNO]]*