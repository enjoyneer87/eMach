# plans/ — 학위논문 세션 → 열해석 머신 계획 주입 폴더

- **쓰기 주체**: 학위논문 세션(레포 `Thesis_SKKU`, PC `user`)만 이 폴더를 쓴다. 열해석 머신(moa)은 읽기만.
- **답신**: moa는 `../HANDOFF_<날짜>.md` 또는 `../CONTEXT_*.md`에 진행·완료를 덧붙인다(이 폴더를 고치지 않는다).
- **결과 위치**: `../thesis_out/` — JSON(`_loss_source`·`_htc`·`_soltype` 필수) + PNG ≤ 300 KB. GIF·대용량은 GitHub Release 또는 로컬 디스크.
- **학위논문 쪽 소비**: `Thesis_SKKU/Assets/Data/thermal/pull_from_emach.py`가 `origin/freeflow-e10-model:mlxperPJT/thermal/thesis_out/*`를 복사.
- 최신 계획: `PLAN_20260906_thesis_thermal.md`. Drive `Prius_thermal_viz/_context/`의 사본은 보조(정본 아님).
