# JEET Phase 3 — Kturn 통합 파이프라인 커밋 가이드

다른 서버에서 **`.mot` 생성 + AC 손실 맵 생성**을 한 줄로 자동 실행하는
파이프라인(`run_kturn_pipeline.py`)을 추가했습니다. 이 문서는 무엇을 커밋할지,
무엇을 커밋에서 제외할지 정리합니다.

---

## 1. 한 줄 실행 (목표)

```bash
# pyMotorEnv_310 (Python 3.10) 활성화 후, eMach/mlxperPJT/JEET 에서:
python run_kturn_pipeline.py --base-mot e10Turn6V261.mot --turns 4 6 8 --output-dir ./kturn_results

# 최소 예시 (요구사항 명세):
python run_kturn_pipeline.py --base-mot e10Turn6V261.mot --turns 4 8
```

- **Stage 1**: 기준 `.mot`(6턴) → 각 턴수로 `WindingLayers` 변경 + 점적율 보존
  copper 사이징(`calc_conductor_size`) → `e10Turn<N>V261.mot` 저장
- **Stage 2**: 각 `.mot` 에 대해 `(proximity_model × speed × current × phase)` sweep
  → eMach `+mcad/loadAcLossJson.m` 호환 JSON(`{"_meta",...},"records":[...]}`) 저장

AC 손실 계산은 검증된 `_mcad_parallel_worker.run_sweep_point` 를 그대로 호출하므로
노트북과 동일한 레코드 포맷/수식을 보장합니다.

유용한 옵션: `--sessions N`(병렬 세션), `--skip-gen`/`--skip-sweep`(단계 분리),
`--currents/--phases/--speeds`(격자 지정), `--force-resweep 3`(캐시 무시 재계산).
resume 지원: 기존 JSON 의 완료점은 건너뜁니다.

---

## 2. 커밋 대상 파일

### 2.1 신규 생성 (이번 Phase 3)
| 파일 | 설명 |
|------|------|
| `mlxperPJT/JEET/run_kturn_pipeline.py` | **메인 파이프라인** (Stage1+Stage2 통합 CLI) |
| `mlxperPJT/JEET/requirements_kturn.txt` | 서버 실행용 패키지 목록 (pyMotorEnv_310 기준) |
| `mlxperPJT/JEET/PHASE3_COMMIT.md` | (본 문서) |

### 2.2 수정됨 (이전 세션 버그 수정 포함)
| 파일 | 설명 |
|------|------|
| `mlxperPJT/JEET/figures/gen_e10_hairpin_turns.py` | 턴수별 `.mot` 생성 로직 — `calc_conductor_size` 를 파이프라인이 재사용 |
| `mlxperPJT/JEET/pyMotorCAD_Hybrid_AClossCode_Template.ipynb` | AC 손실 sweep 템플릿 — 파이프라인 Stage2 의 출처 |

### 2.3 의존(이미 repo 존재, 변경 없음 — 참고)
- `mlxperPJT/JEET/_mcad_parallel_worker.py` — `run_sweep_point` 등 (Stage2 재사용)
- `tools/motorCAD/pyMCAD/__init__.py`, `mqs_runner.py` — `calc_dc_loss_kw`, `get_fea_src_dir`
- `+mcad/loadAcLossJson.m` — JSON 소비측(호환 대상)

> 같은 작업 트리에 함께 떠 있는 다른 변경분
> (`test_syre_efficiency_map.m`, `tools/motorCAD/buildMotorModelForSyre.m`,
> `figures/run_gen_kturn.m`, `verify_af_data_quality.py`, `test_phase1_verify.m`,
> `map_exports/e10/SC/AF_infill_schedule_SC.json`)은 **Phase 3 파이프라인과 별개**입니다.
> 같은 커밋에 묶지 말고 별도로 분리 커밋하는 것을 권장합니다.

### 권장 커밋 명령
```bash
git add mlxperPJT/JEET/run_kturn_pipeline.py \
        mlxperPJT/JEET/requirements_kturn.txt \
        mlxperPJT/JEET/PHASE3_COMMIT.md \
        mlxperPJT/JEET/figures/gen_e10_hairpin_turns.py \
        mlxperPJT/JEET/pyMotorCAD_Hybrid_AClossCode_Template.ipynb
git commit -m "feat(JEET): Phase3 Kturn 통합 파이프라인 (.mot 생성 + AC 손실 맵)"
```

---

## 3. 커밋 제외(주의)

### 3.1 대용량/런타임 산출물 — 커밋 금지
- **`.mot` 파일** (`e10Turn*.mot`, `kturn_results/**/*.mot`)
  - 모델당 수백 KB~MB. 기준 `.mot` 만 원본 저장소에 두고 **생성물은 제외**.
  - ⚠️ 현재 `.gitignore` 는 `*.moto` 만 무시하고 **`.mot` 은 추적될 수 있음** → 아래 규칙 추가 권장.
- **`kturn_results/` 출력 디렉토리 전체**
  - `ACLossCalcExport_kturn*/` (FEA 결과 백업), `*.mat`, 중간 `.txt` 포함.
- **FEA 결과** (`FEResultsData/`, `FEResultData`) — 이미 `.gitignore` 에 있음.
- **`.mat` 요약** — `mlxperPJT/JEET/**/*.mat` 이미 `.gitignore` 에 있음.

### 3.2 요약 JSON 의 선택적 커밋
- `JEET_ACLoss_kturn<N>_Map_Summary.json` 은 분석 결과로서 의미가 있으나
  크기가 커질 수 있음(레코드 수에 비례). **소형(요약)일 때만** 선택 커밋,
  대형이면 산출물로 간주하여 제외.

### 3.3 권장 `.gitignore` 추가
`mlxperPJT/JEET/.gitignore` (또는 루트 `.gitignore`)에 추가:
```gitignore
# JEET Kturn 파이프라인 런타임 산출물
mlxperPJT/JEET/kturn_results/
mlxperPJT/JEET/**/e10Turn*.mot
mlxperPJT/JEET/**/ACLossCalcExport_*/
```

---

## 4. 서버 사전 점검 체크리스트

- [ ] Ansys **Motor-CAD** 설치 + 라이선스 (v261 변수셋: `WindingLayers`, `ACLoss_Hybrid_Total` 등)
- [ ] **pyMotorEnv_310** venv: `pip install -r requirements_kturn.txt`
      (`ansys-motorcad`, `pywin32`, `numpy`, `scipy`)
- [ ] 기준 `.mot`(예: `e10Turn6V261.mot`) 경로 확인 → `--base-mot` 로 전달
- [ ] 출력 디스크 여유 (턴수 × sweep점 × FEA 백업)
- [ ] 병렬 사용 시(`--sessions N`) Motor-CAD 동시 세션 수 = 코어/라이선스 한도 내

### 헤드리스 검증 상태
- 본 파이프라인은 pyMotorEnv_310 에서 **import/CLI/격자생성/사이징 수식**까지 검증 완료.
- Motor-CAD 라이브 호출(.mot 저장, FEA sweep)은 **워크스테이션에서 실행 시 확인** 필요.
