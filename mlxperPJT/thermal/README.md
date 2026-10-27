# 모터 열해석 자동화 패키지 (`mlxperPJT/thermal`)

Motor-CAD · Maxwell · gmsh · MAPDL · FreeFlow · Icepak/IcepakFEA · Fluent · Mechanical 를 잇는
모터 열해석 자동화 코드. JMAG JAC279 방식의 **3D FEM + 열등가회로 하이브리드(MAPDL)** 를 축으로,
두 모터(실제 Toyota **Prius**, FreeFlow 오일냉각 모터 **e10**)에서 교차검증까지 마쳤다.

- 단계 실행·점검: **[`pipeline.py`](pipeline.py)** (이 README 의 표를 코드로 옮긴 레지스트리)
- Claude Code 스킬: **[`.claude/skills/motor-thermal-hybrid`](../../.claude/skills/motor-thermal-hybrid/SKILL.md)**
  — 함정 목록·기준값·토큰 절약 실행 스크립트(run_detached/wait_done/ansys_clean/sync_out)
- 이력·근거: [`HANDOFF_20260721.md`](HANDOFF_20260721.md) → [`_20260722`](HANDOFF_20260722.md) → [`_20260907`](HANDOFF_20260907.md)

## 짧은 상태 조회 (솔버 실행 없음)

레포 루트에서 Python 표준 라이브러리만으로 실행한다. 조회 결과는 한 줄 JSON이다.

```powershell
python -B -X utf8 mlxperPJT/thermal/ops.py snapshot         # Git·작성자·최신 핸드오프
python -B -X utf8 mlxperPJT/thermal/ops.py snapshot --live  # 원격 tip 조회, fetch 없음
python -B -X utf8 mlxperPJT/thermal/ops.py stages --chain e10 --query mapdl
python -B -X utf8 mlxperPJT/thermal/ops.py artifacts        # 세 결과 폴더의 JSON 목록
python -B -X utf8 mlxperPJT/thermal/ops.py evidence mlxperPJT/thermal/thesis_out/e10_cont_rating.json
```

목록은 기본 8개이며 생략 수를 표시한다. 결과 내용은 `--pointer /key`로 좁혀 읽는다.
원격 커밋이 로컬에 없으면 선후 관계는 `unknown`이다. 캐시된 upstream과 실시간 원격 조회,
저장된 JSON과 현재 솔버 실행 상태를 구별한다. 파일 수정시각은 해석 날짜를 보증하지 않는다.
Codex용 짧은 사용 지침은 레포 루트의
[`.agents/skills/emach-ops/SKILL.md`](../../.agents/skills/emach-ops/SKILL.md)에 있다.

## 도구 체인

```
                    ┌──────────── e10 (FreeFlow 오일냉각) ────────────┐
Motor-CAD (.mot) ──▶│ 손실·운전점                                      │
Maxwell 2D/3D ─────▶│ 로터·자석 단면 / 손실 ─▶ gmsh(OCC) ─▶ CDB v2      │
                    │                         │                        │
                    │              MAPDL 하이브리드 (FEM + 오일 회로)   │──▶ thermal_viz
                    │                ▲ 벽온도      │ 오일노드 온도 ref  │
                    │   FreeFlow SPH ┘ (1-way)     ▼                    │
                    │                     Icepak V1 (대류벽) ─▶ 비교    │
                    └──────────────────────────────────────────────────┘
Prius: Maxwell 손실 ─▶ STEP→CDB ─▶ MAPDL(JAC279 / 워터재킷) ⇄ Fluent CHT ⇄ Icepak  (3-way 검증)
Mechanical: Maxwell → AEDT Mechanical Thermal(IcepakFEA) 빌드 · C67 원심응력 · em2struct(NVH 가진력)
Fluent: 엔드턴 오일 스프레이 CHT (DPM + Wall Film) — 메시는 GUI
```

## 단계 (`python pipeline.py list`)

| 체인 | 단계 | 도구 | 스크립트 |
|---|---|---|---|
| e10 | `mcad_losses` → `maxwell_geom` → `mesh_stl` → `mesh_v2` | Motor-CAD · Maxwell · gmsh | `freeflow/scripts/01, 02c, 03, 03b` |
| e10 | `mapdl_hybrid` → `mapdl_viz` | MAPDL | `freeflow/scripts/04, 10` |
| e10 | `ff_thermal_setup` → `ff_thermal_solve` → `ff_thermal_viz` | FreeFlow (`--headless --script`) | `freeflow/scripts/11, 12, 13` |
| e10 | `icepak_v1_steady` → `icepak_v1_trans` (· `icepak_v2_bars`) → `compare` | Icepak | `icepak_e10/scripts/10, 11, 12` · `freeflow/scripts/19` |
| prius | `maxwell_losses` → `mesh` → `mapdl_jac279` / `mapdl_wj_low` / `mapdl_wj_high` | Maxwell · gmsh · MAPDL | `prius/scripts/01, 02, 03, 08` |
| prius | `fluent_extract` · `fluent_250A` → `validation` · `viz` | Fluent(h5py) | `prius/scripts/05, 09, 10, render_prius_viz` |
| prius | `icepak_import` → `icepak_sources` → `icepak_solve` → `threeway` | Icepak | `prius/icepak/01, 02, 05, 07` |
| mech | `aedt_thermal_build` (노트북) · `c67_stress` · `em2struct` | IcepakFEA · Mechanical | `WS01_2_…ipynb` · `plans/…/d6` · `tools/em2struct` |
| fluent | `spray_geom` → `spray_mesh`(GUI) → `spray_cht` | gmsh · Fluent | `fluent_spray/` |
| thesis | `preflight` → `d1` · `d2` · `d3` · `d4` → `figs` | MAPDL · Motor-CAD | `plans/PLAN_20260906_assets/` (읽기전용) |

## 빠른 시작 (moa)

```powershell
$PY = "C:\Users\moa\.ansys_python_venvs\PyMotorEnv_310\Scripts\python.exe"
cd D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal
& $PY pipeline.py init                       # 스크래치 폴더 준비(최초 1회)
& $PY pipeline.py check e10                  # 빠진 입력·모듈만 출력
& $PY pipeline.py run e10.mapdl_hybrid --dry-run
& $PY pipeline.py run e10.mapdl_hybrid --detached --scheduled-task
```

긴 솔브는 `--detached` 로 띄우고 `.claude/skills/motor-thermal-hybrid/scripts/wait_done.ps1` 을
**한 번** 실행해 완료를 받는다(로그 폴링 금지). 솔브 전 `ansys_clean.ps1 -Kill` 로 잔존 MAPDL 정리.

## 결과 리포트 (HTML)

```powershell
& $PY thermal_report.py --viz-root "G:\내 드라이브\Prius_thermal_viz"
# → C:\work\thermal_scratch\reports\thermal_report_<날짜>.html
```
결과 JSON 과 표준 그림을 **한 파일짜리 HTML**(인라인 SVG 차트, 그림 내장)로 묶는다. 판정 카드:
Prius MAPDL↔Fluent 코일(±2 °C), e10 권선 회귀(152.2±1 °C), Icepak V1↔MAPDL(±15%),
FreeFlow 오일 승온 일관성, 비물리값(>300 °C) 격리. `--gifs` 로 과도 GIF 포함(수 MB).

## 검증된 기준값 (요약)

| 모델 | 비교 | 결과 |
|---|---|---|
| Prius 동일조건 | MAPDL 워터재킷 vs Fluent CHT, 코일 max | 저부하 88.3 = 88.3 °C, 250A 119.2 vs 118.2 °C |
| e10 | MAPDL 하이브리드 과도 900s | 권선 152.2 / 스테이터 126.0 / 자석 86.9 °C |
| e10 | Icepak V1 vs MAPDL, 권선 | 136.5 vs 152.2 °C (10% 이내) |
| e10 | FreeFlow 1-way (1.63 s) | 오일 70.0 → 평균 70.8 / 최대 72.2 °C |

전체 표와 비물리 신호 판정은 스킬의 `references/results.md`.

## 이식성 · 규칙

- 스크립트는 moa 경로를 하드코딩한다: 레포 `D:\KDH\NvidiaNemo\eMach`, 원본 데이터 `D:\KDH\simVary\…`,
  로그·중간파일 **`C:\work\thermal_scratch`**(2026-10 이전 Claude 세션 임시폴더 경로를 일괄 이전).
  다른 PC에서는 `THERMAL_SIMVARY`/`THERMAL_SCRATCH` 로 `check` 만 맞출 수 있고, 실행은 경로 상수 수정이 필요.
- 큰 원본(`*.cdb` 260MB, `.aedt`, `.mot`, `.freeflow`, Fluent `.h5`)과 산출 이미지는 **git 밖**
  (이미지는 gdrive `Prius_thermal_viz/`, 입력 자산은 사내 NAS). 공개 레포에 올리지 않는다.
- `plans/**` 는 학위논문 세션 관할 — 읽기전용 참조 구현. 수정은 `freeflow/scripts/` 로 승격 후.
- moa 는 GitHub 에 닿지 않는다 → 변경은 `git bundle` 로 게이트웨이를 거쳐 push.
