# 📅 Phase 1 - Month 2: Streamlit 3D 대시보드

**기간:** 2026-05-01 ~ 2026-05-31  
**목표:** 메쉬별 결과를 웹에서 인터랙티브하게 확인하는 대시보드 완성  
**키워드:** `stpyvista` `Streamlit` `컨투어` `단면` `WebSocket` `PhysicsNeMo` `MeshGraphNet`

---

## ✅ 월간 완료 기준

- [ ] Streamlit에서 h5 업로드 → 자속밀도 컬러맵 3D 표시
- [ ] 단면(Clipping), 시간 스텝 슬라이더 동작
- [ ] MGN(PhysicsNeMo) 추론 결과와 Motor-CAD 결과 나란히 비교 뷰
- [ ] 로컬 네트워크에서 팀원이 접속 가능한 배포 구성

---

## 📆 Week 5 (May 4–8): Streamlit 핵심 기능

> [!info]- 🎯 Week 5 목표
> stpyvista 연동 및 Streamlit 앱의 핵심 3D 인터랙션 구현

### Day 21 · 2026-05-04 (월)

> [!todo]- 🤖 Agent A 임무
> - [ ] stpyvista 고급 사용: 다수 mesh 레이어 동시 표시
> - [ ] 스테이터/로터/권선 별도 레이어로 분리 렌더링

> [!todo]- 🤖 Agent B 임무
> - [ ] Streamlit multi-page 앱 구조 설계 (Overview, Detail, Compare 페이지)
> - [ ] 공통 네비게이션 사이드바 컴포넌트

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Streamlit multi-page app 공식 문서 읽기
> - [ ] 내 대시보드에서 필요한 페이지 목록을 직접 기획서로 작성

---

### Day 22 · 2026-05-05 (화)

> [!todo]- 🤖 Agent A 임무
> - [ ] 실시간 업데이트: 슬라이더 변경 시 3D 뷰 자동 갱신 (`st.rerun`)
> - [ ] 물리량 범위 필터: 특정 값 이상/이하 하이라이트 기능

> [!todo]- 🤖 Agent B 임무
> - [ ] `st.metric()` 카드: 최대/최소/평균 물리량 표시
> - [ ] Plotly 2D 그래프: 특정 라인을 따른 물리량 분포

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 내가 설계할 때 가장 많이 보는 2D 그래프 종류 파악
> - [ ] `st.rerun()` vs `st.experimental_rerun()` 차이 이해

---

### Day 23 · 2026-05-06 (수)

> [!todo]- 🤖 Agent A 임무
> - [ ] 비교 뷰: MGN 추론 결과 vs Motor-CAD 정답 2분할 표시
> - [ ] 오차 맵(Error Map): `|MGN - Ground Truth|` 컬러맵

> [!todo]- 🤖 Agent B 임무
> - [ ] 비교 데이터 로더: 같은 케이스에서 GT와 MGN 결과 분리 로드
> - [ ] 오차 통계 테이블: MAE, RMSE, Max Error
> - [ ] 체크포인트 메타데이터 표시: 학습 스텝, 입력 경로, 모델 버전

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] MGN 모델의 예측 정확도를 공간적으로 어떻게 해석할 것인가?
> - [ ] 오차가 큰 영역의 물리적 의미: 포화? 경계 조건?

---

### Day 24 · 2026-05-07 (목)

> [!todo]- 🤖 Agent A 임무
> - [ ] 모터 회전 애니메이션: 시간 스텝별 연속 재생 버튼
> - [ ] 재생 속도 조절 슬라이더 (FPS 설정)

> [!todo]- 🤖 Agent B 임무
> - [ ] GIF/MP4 자동 생성: 시간 스텝 결과를 영상으로 저장
> - [ ] `imageio` 또는 `pyvista.Movie` 활용

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 모터 회전에 따른 자기장 변화: 어떤 현상이 중요한가?
> - [ ] 코깅 토크(Cogging Torque)와 자기장 분포의 관계

---

### Day 25 · 2026-05-08 (금)

> [!todo]- 🤖 Agent A 임무
> - [ ] Week 5 통합 테스트
> - [ ] UX 피드백: UI가 직관적인지 직접 5분 사용해보고 개선점 도출
> - [ ] MGN 비교 페이지에서 기준 지표(|B| MAE, Bx/By MAE) 노출 검증

> [!todo]- 🤖 Agent B 임무
> - [ ] 성능 프로파일링: `cProfile`로 병목 구간 파악
> - [ ] 메모리 사용량 모니터링 (`tracemalloc`)
> - [ ] 추론/시각화 병목 분리 계측 (모델 추론 시간 vs 렌더링 시간)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Week 5 회고
> - [ ] 이 대시보드를 동료에게 보여주면 어떤 반응이 나올지 상상해보기

---

## 📆 Week 6 (May 11–15): 데이터 파이프라인 고도화

> [!info]- 🎯 Week 6 목표
> 여러 해석 케이스를 쉽게 비교하고 배치 처리하는 파이프라인 구축

### Day 26 · 2026-05-11 (월)

> [!todo]- 🤖 Agent A 임무
> - [ ] 배치 변환: 폴더 내 모든 h5 파일 → vtu 일괄 변환
> - [ ] 진행률 표시: `tqdm` 또는 `st.progress()`
> - [ ] 배치 추론: 케이스 목록에 대해 MGN 추론 결과 캐시 생성

> [!todo]- 🤖 Agent B 임무
> - [ ] 케이스 관리: 해석 케이스별 폴더 구조 설계
> - [ ] SQLite 기반 간단한 케이스 레지스트리 (케이스 이름, 날짜, 설명)
> - [ ] 레지스트리에 ML 메타컬럼 추가 (checkpoint, inference_time, MAE)

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] SQLite 기초: 파이썬에서 db 파일 만들고 쿼리하기
> - [ ] 내가 운용할 모터 케이스 수는 어느 정도인지 예상해보기

---

### Day 27 · 2026-05-12 (화)

> [!todo]- 🤖 Agent A 임무
> - [ ] 파라미터 스윕 결과 비교: N개 케이스 오버레이 그래프
> - [ ] 설계 파라미터(예: 슬롯 폭) vs 물리량(최대 B) scatter plot
> - [ ] 설계 파라미터 vs MGN 오차 지표 산점도 추가

> [!todo]- 🤖 Agent B 임무
> - [ ] Pandas DataFrame으로 케이스 비교 테이블 생성
> - [ ] Excel 내보내기 기능 (`openpyxl`)
> - [ ] 비교 테이블에 GT/MGN 편차 컬럼 자동 생성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] 내 MGN/FNO 모델의 입력 파라미터 공간 정의하기
> - [ ] 파라미터 스윕 계획: 어떤 변수를 얼마나 변화시킬 것인가?

---

### Day 28–30 · 2026-05-13~15

> [!todo]- 🤖 Agent A 임무
> - [ ] 검색 기능: 케이스 이름, 날짜로 검색
> - [ ] 즐겨찾기: 중요 케이스 북마크 기능

> [!todo]- 🤖 Agent B 임무
> - [ ] Week 6 테스트 및 문서화
> - [ ] 배포 준비: `requirements.txt` 최종화, `CHANGELOG.md` 작성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Week 6 회고
> - [ ] 다음 달(Month 3) Babylon.js 개발 환경 미리 탐색

---

## 📆 Week 7–8 (May 18–31): 안정화 & Phase 2 준비

> [!info]- 🎯 Week 7-8 목표
> Streamlit 앱 안정화 및 Phase 2(Babylon.js)를 위한 기술 조사

### Day 31–35 · 2026-05-18~22

> [!todo]- 🤖 Agent A 임무
> - [ ] 버그 수정 및 안정성 개선
> - [ ] 로딩 속도 최적화 (목표: 10MB h5 → 10초 이내)
> - [ ] 모바일/태블릿 반응형 레이아웃
> - [ ] MGN 체크포인트 미존재/버전불일치 시 fallback UI 처리

> [!todo]- 🤖 Agent B 임무
> - [ ] 로컬 네트워크 배포: `--server.address 0.0.0.0` 설정
> - [ ] 사용자 인증 기초: Streamlit-Authenticator 적용
> - [ ] MGN 추론 비활성 모드 플래그(`inference=false`) 배포 옵션 추가

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Node.js 설치 및 `npm` 기초 명령어 익히기
> - [ ] TypeScript란 무엇인가? 왜 JavaScript 대신 쓰나?

---

### Day 36–40 · 2026-05-25~29

> [!todo]- 🤖 Agent A 임무
> - [ ] Month 2 최종 통합 테스트
> - [ ] 사용자 매뉴얼 초안 작성 (엔지니어용)

> [!todo]- 🤖 Agent B 임무
> - [ ] `v0.2.0` 릴리즈 태깅 및 GitHub Release 노트
> - [ ] 테스트 커버리지 리포트 생성

> [!abstract]- 📚 내 공부/개발 (천천히)
> - [ ] Month 2 KPT 회고
> - [ ] Babylon.js 공식 Playground에서 기본 3D Scene 실험: https://playground.babylonjs.com
> - [ ] Three.js vs Babylon.js: CAE 목적에 맞는 선택 이유 정리

---

*← [[Phase1_Month1_DataAdapter]] | → [[Phase1_Month3_BabylonJS]]*
