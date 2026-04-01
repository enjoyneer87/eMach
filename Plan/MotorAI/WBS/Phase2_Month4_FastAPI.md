# 📅 Phase 2 - Month 4: FastAPI 바이너리 스트리밍

**기간:** 2026-07-01 ~ 2026-07-31  
**목표:** eMach/AI 결과를 웹 클라이언트에 저지연으로 전달하는 서비스 계층 구축  
**키워드:** `FastAPI` `Pydantic` `Float32Array` `Binary Streaming` `Inference API`

---

## ✅ 월간 완료 기준

- [ ] Geometry/Result/MLDataset API 스키마 v1 확정
- [ ] 추론 요청/응답 엔드포인트 구현
- [ ] 바이너리 버퍼 전송 경로 구축(메쉬+스칼라)
- [ ] 모델 버전/체크포인트 메타 API 제공
- [ ] Streamlit/Babylon.js 양쪽에서 API 연동 확인

---

## 📆 Week 13 (Jul 1-3): API 설계 동결

> [!info]- 🎯 Week 13 목표
> 서비스 계약(입력/출력/오류코드) 동결 및 골격 구현

### Day 61-63

> [!todo]- 🤖 Agent A 임무
> - [ ] `/health`, `/version`, `/contracts` 기본 엔드포인트 구현
> - [ ] 요청 파라미터 검증(Pydantic model) 작성

> [!todo]- 🤖 Agent B 임무
> - [ ] 오류 taxonomy 표준 코드표 반영
> - [ ] OpenAPI 문서 자동생성 및 예시 요청 추가

---

## 📆 Week 14 (Jul 6-10): 추론 API 구현

> [!info]- 🎯 Week 14 목표
> MGN/FNO 추론 API의 최소 실행 경로 확보

### Day 64-67

> [!todo]- 🤖 Agent A 임무
> - [ ] `/infer/single` 구현(케이스 1건)
> - [ ] `/infer/batch` 구현(복수 케이스)

> [!todo]- 🤖 Agent B 임무
> - [ ] 모델 로딩/캐시 정책(LRU 또는 고정) 구현
> - [ ] 추론 로그(provenance, latency) 저장

### Day 68-70

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] FastAPI 비동기 처리 패턴 학습
> - [ ] 동시 요청 시 병목 포인트 정리

---

## 📆 Week 15 (Jul 13-17): 바이너리 스트리밍 최적화

> [!info]- 🎯 Week 15 목표
> 브라우저 렌더링 최적 형태로 데이터 전송

### Day 71-75

> [!todo]- 🤖 Agent A 임무
> - [ ] 메쉬/스칼라 버퍼를 바이너리 응답으로 직렬화
> - [ ] 압축 옵션(gzip/zstd 후보) A/B 측정

> [!todo]- 🤖 Agent B 임무
> - [ ] 응답시간 SLO 계측 대시보드 구축
> - [ ] 대형 케이스(노드/요소 증가) 부하테스트 시나리오 작성

---

## 📆 Week 16 (Jul 20-31): 클라이언트 통합 검증

> [!info]- 🎯 Week 16 목표
> Streamlit/Babylon.js 양쪽에서 API 연동 완료

### Day 76-80

> [!todo]- 🤖 Agent A 임무
> - [ ] Streamlit 비교뷰 API 연계 완료
> - [ ] Babylon.js mock 교체 및 실데이터 렌더링 확인

> [!todo]- 🤖 Agent B 임무
> - [ ] 운영 가이드(실행, 재시작, 로그수집) 작성
> - [ ] 월말 통합 리포트(`api_integration_report.md`) 발행

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] API 설계 중 재사용 가능한 패턴 정리
> - [ ] Month 5 Shader 입력 형식 요구사항 확정

---

*← [[Phase1_Month3_BabylonJS]] | → [[Phase2_Month5_Shaders]]*