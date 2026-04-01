# 38100 서버용 서브모듈 커밋 체크리스트 (EveryMotor + eMach)

목적: 38100(도면 인식/UI) 서버에서 eMach 서브모듈 작업 시 커밋 누락/포인터 누락/브랜치 실수를 방지한다.

## 1. 작업 시작 전 (30초)

- [ ] 상위 저장소 위치 확인: `D:/KangDH/EveryMotor`
- [ ] 상위 브랜치 확인: `git branch --show-current` (권장: `main`)
- [ ] 서브모듈 동기화: `git submodule update --init --recursive`

## 2. eMach 서브모듈 진입 후

- [ ] 경로 이동: `cd D:/KangDH/EveryMotor/eMach`
- [ ] detached HEAD 아님 확인: `git branch --show-current`
- [ ] 작업 브랜치 고정: `git checkout devVeriACLoss`
- [ ] 최신화: `git pull origin devVeriACLoss`

## 3. 구현/검증

- [ ] 코드 수정
- [ ] 최소 검증: `python -m py_compile <변경파일들>` 또는 테스트
- [ ] Streamlit UI 변경 시 실행 확인

## 4. 커밋 1차 (서브모듈 내부)

- [ ] `git add <파일>`
- [ ] `git commit -m "[Action-N][38100] <요약>"`
- [ ] `git push origin devVeriACLoss`
- [ ] 커밋 해시 기록 (Notion `커밋해시` 필드)

## 5. 커밋 2차 (상위 EveryMotor 포인터)

- [ ] 상위 저장소로 이동: `cd D:/KangDH/EveryMotor`
- [ ] 변경 확인: `git status --short` (eMach 포인터 변경 표시 확인)
- [ ] `git add eMach`
- [ ] `git commit -m "chore: bump eMach submodule (<short-hash>)"`
- [ ] `git push origin <상위브랜치>`

## 6. Notion 동기화

- [ ] 해당 작업 row의 `상태` 업데이트 (`진행 중` 또는 `완료 🙌`)
- [ ] `서버ID=38100`, `작업키`, `커밋해시`, `완료근거(URL)` 입력
- [ ] 리뷰 전이면 `검증완료`는 체크하지 않음

## 7. 자주 발생하는 실수

- [ ] 실수1: eMach에서 커밋/푸시했지만 상위 EveryMotor 포인터 커밋 누락
- [ ] 실수2: detached HEAD 상태에서 커밋
- [ ] 실수3: 커밋 메시지에 작업키(Action-N) 누락
- [ ] 실수4: Notion 상태만 완료로 바꾸고 커밋 근거 URL 누락

## 8. 38100용 빠른 실행 템플릿

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned; & C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\Activate.ps1; cd D:\KangDH\EveryMotor; git pull --recurse-submodules; git submodule update --init --recursive; cd eMach; git checkout devVeriACLoss; git pull origin devVeriACLoss
```
