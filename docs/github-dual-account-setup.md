# GitHub 계정 두 개 설정 가이드 (VS Code)

> Copilot 라이선스 계정과 커밋 계정을 분리해서 사용하는 설정 방법

---

## 개요

VS Code에서는 두 레이어가 **완전히 별개**로 동작합니다.

| 역할 | 계정 | 사용처 |
|------|------|--------|
| **Copilot / PR / Issues** | GitHub OAuth 계정 | VS Code 로그인, Copilot 라이선스, PR 확장 |
| **Git 커밋 author** | `user.name` / `user.email` | `git commit` 시 author 정보 |
| **Push 인증** | Personal Access Token (PAT) | `git push` 시 credential |

---

## 1. Git 커밋 계정 설정 (전역)

```bash
git config --global user.name "enjoyneer87"
git config --global user.email "enjoyneer87@naver.com"
git config --global credential.helper store
```

> `credential.helper store` : 최초 push 시 입력한 토큰을 `~/.git-credentials`에 저장

---

## 2. GitHub Personal Access Token (Push 인증용)

1. [github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens) 접속
2. **Generate new token (classic)** 클릭
3. 권한: `repo` 체크
4. 생성된 토큰 복사 (한 번만 표시됨)
5. 처음 `git push` 할 때:
   - username → GitHub 아이디
   - password → **위에서 복사한 PAT 토큰**

이후부터는 `~/.git-credentials`에 저장되어 자동 인증됩니다.

---

## 3. VS Code Copilot 계정 (별도 GitHub 계정)

1. VS Code 설치
2. 좌하단 **계정 아이콘** 클릭
3. "GitHub으로 로그인" 선택
4. **Copilot 라이선스가 있는 계정**으로 로그인
5. 커밋용 계정과 달라도 무관 — OAuth 계정과 git credential은 독립적

---

## 4. 리포지토리별 커밋 계정 개별 설정 (선택)

특정 리포지토리만 다른 계정으로 커밋하고 싶을 때:

```bash
# 해당 리포지토리 폴더 안에서 실행
git config user.name "다른이름"
git config user.email "다른이메일@example.com"
```

로컬 `.git/config`에 저장되어 전역 설정보다 우선 적용됩니다.

---

## 5. 설정 확인

```bash
# 전역 설정 확인
git config --list --global

# 현재 리포 설정 확인 (로컬 + 전역 모두)
git config --list --show-origin
```

---

## 체크리스트

- [x] `git config --global user.name` 설정 → `enjoyneer87`
- [x] `git config --global user.email` 설정 → `enjoyneer87@naver.com`
- [x] `git config --global credential.helper store` 설정
- [ ] GitHub PAT 토큰 생성 (repo 권한)
- [ ] 최초 `git push` 로 토큰 등록
- [ ] VS Code → 계정 아이콘 → Copilot 계정으로 GitHub 로그인
