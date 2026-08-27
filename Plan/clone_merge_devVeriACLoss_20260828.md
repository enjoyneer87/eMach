# devVeriACLoss 클론 화해 계획 (2026-08-28)

> 두 로컬 클론이 같은 브랜치 이름으로 갈라져 있던 것을 병합해 하나로 만든다.
> 분석은 EveryMotor 클론에 `emlab` 로컬 원격을 추가해 수행했다.

## 1. 분기 실측

| | |
|---|---|
| 분기점 | `aa1b3dd` 2026-04-02 "Add pyMCAD-to-PyVista pipeline notebook…" |
| EveryMotor 쪽 | **+248 커밋** (JEET 논문 파이프라인 전체, kturn, paper2 등) |
| Emlab 쪽 | **+1 커밋** (`5a57fe9` 2026-07-26, 14파일 — pyMotorGeo 브리지, WBS 문서, KETI 노트북, `policy_sync_runner.ps1`) |
| 양쪽 공통 변경(충돌 후보) | **2파일뿐** — `Plan/MotorAI/WBS/00_WBS_Master.md`, `mlxperPJT/KETI/pyMCAD4SolverX.ipynb` |
| JEET 메인 mlx | EveryMotor `3cd1cd7`(06-01)이 154파일과 함께 삭제. Emlab 은 분기 전 상태 그대로 추적(수정 없음) |

**함정**: Emlab 의 유일 커밋이 JEET mlx 를 안 건드렸으므로, 평범한 병합은
**삭제를 조용히 유지**한다. 메인 mlx 복원은 병합과 별도의 명시적 단계여야 한다.

## 2. 안전 조치 — 완료

- [x] `origin/devVeriACLoss-emlab-backup` ← Emlab 의 5a57fe9 푸시 (2026-08-28).
      Emlab 기계가 죽어도 커밋은 안전하다.

## 3. 병합 절차 (EveryMotor 클론에서 실행)

```bash
cd D:\KangDH\EveryMotor\eMach
git merge emlab/devVeriACLoss -m "Merge the Emlab clone's July work back into the line"
# 예상 충돌 2건:
#   Plan/MotorAI/WBS/00_WBS_Master.md   --- 문서, 수동 병합 (양쪽 다 문서 갱신)
#   mlxperPJT/KETI/pyMCAD4SolverX.ipynb --- Emlab 쪽 +4줄뿐. 셀 충돌이면
#       Emlab 판 채택 후 EveryMotor 쪽 변경 재적용이 빠름
```

## 4. JEET 메인 mlx 복원 (병합 후 별도 커밋)

3cd1cd7 삭제분 중 **계보 가치가 있는 것만** 선별 복원한다:

```bash
git checkout emlab/devVeriACLoss -- \
  mlxperPJT/JEET/JEETResult_rev1.mlx \
  mlxperPJT/JEET/JEETResult_rev1_v1.mlx \
  mlxperPJT/JEET/JEETResult_rev1_v1.m \
  mlxperPJT/JEET/JEETResult_MCADHybridmlx.mlx \
  mlxperPJT/JEET/JEETResult_summary.mlx \
  mlxperPJT/JEET/JEETResult_summary_rev1.mlx \
  mlxperPJT/JEET/rpACLossdqSurf.mlx \
  mlxperPJT/JEET/noteveriFatami_eq3NTahaexpressionXi.mlx
```

- `.fig` 140여 개는 복원하지 않는다 — 산출물이고 emlab-backup 브랜치에서
  언제든 꺼낼 수 있다.
- 복원 위치를 `mlxperPJT/JEET/legacy2024/` 로 옮길지는 저자 취향 — 옮기면
  현행 파이프라인과 구분이 명확해진다 (권장).

## 5. Emlab 클론 정리 (병합 푸시 후)

```bash
cd D:\KangDH\Emlab_emach
git fetch origin
git status                        # 더러운 파일 확인 (현재 ?? 1개: *_case_map.csv)
git checkout devVeriACLoss
git merge --ff-only origin/devVeriACLoss   # fast-forward 로 정렬
```

이후 두 클론은 같은 커밋. **역할 분담을 정해 두면 재발을 막는다** — 제안:
EveryMotor = JEET/논문 트랙 주 클론, Emlab = pyMotorGeo/MotorAI 트랙 주 클론,
양쪽 다 **작업 후 즉시 push** 규율.

## 6. 미실행 항목

- [ ] 3절 병합 (충돌 2건 수동 해소 필요 — 실행 승인 대기)
- [ ] 4절 mlx 복원 + 배치 결정 (legacy2024/ 여부)
- [ ] 5절 Emlab ff 정렬
- [ ] From38100/ 대용량 결과(추적 여부 혼재)의 처분 — Zenodo/백업 정책과 함께
