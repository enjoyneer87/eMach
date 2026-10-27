---
name: motor-thermal-hybrid
description: 모터 열해석(JAC279식 MAPDL 3D FEM+열등가회로 하이브리드, Prius·e10 모델, FreeFlow SPH 오일냉각 1-way 커플링, Icepak/IcepakFEA, Fluent CHT·오일스프레이, Motor-CAD 손실·D1~D6 학위논문 킷, thermal_viz 표준 시각화)를 eMach 레포(freeflow-e10-model 브랜치)에서 실행·수정·검증할 때 사용. MAPDL/pymapdl·SURF152·COMBIN14·MASS71·CDB 메시·gmsh·pyaedt Icepak·FreeFlow API·rclone/gdrive 산출물·moa(iso) 원격 실행이 언급되면 먼저 읽을 것.
---

# 모터 하이브리드 열해석 (eMach / moa)

검증된 파이프라인을 **재발견 없이** 돌리기 위한 스킬. 코드는 레포에 있고, 이 문서는
"무엇을 어떤 순서로, 무엇을 피해서" 만 담는다. 세부는 `references/` 를 필요할 때만 읽는다.

## 0. 토큰 운영 규칙 (가장 먼저 지킬 것)

과거 세션(298544ad, 10일·API 2,365회)의 맥락 토큰 12.3억 중 **30%가 솔브 대기 폴링**,
**호출당 평균 52만 토큰**이었다. 원인은 세션 하나를 계속 이어 쓴 것과 반복 확인이다.

1. **작업 단위로 새 세션**을 연다 (예: "e10 D1 재실행", "Prius viz 재생성"). 이전 세션의
   맥락이 필요하면 레포의 `HANDOFF_*.md` 를 읽는다 — 대화 이력을 끌고 다니지 않는다.
2. **솔브를 기다리며 폴링하지 않는다.** `scripts/run_detached.ps1` 로 띄우고,
   `scripts/wait_done.ps1` 을 **백그라운드 Bash/PowerShell 한 번**으로 실행해 완료 알림을 받는다.
   `sleep`+`tail` 반복, Monitor 짧은 주기, ScheduleWakeup 짧은 간격 금지.
3. 결과는 **요약 JSON 한 개**만 읽는다 (`<run>\summary.json`, 로그는 실패 시 꼬리만).
   이미지 육안 확인은 최종 1장, 축소본으로.
4. git·rclone 동기화는 `scripts/sync_out.ps1` 한 번. push 후 ls-remote 반복 확인 금지.
5. ANSYS 프로세스 정리는 `scripts/ansys_clean.ps1` (MAPDL 솔버만 대상, Motor-CAD·AEDT·
   라이선스 클라이언트 `ansyscl` 은 절대 종료하지 않음).

## 1. 어디에 무엇이 있나

| 항목 | 위치 |
|---|---|
| 레포 (moa) | `D:\KDH\NvidiaNemo\eMach` 브랜치 `freeflow-e10-model` → `mlxperPJT\thermal\` |
| 접속 | 게이트웨이에서 `ssh iso` (사내망 moa 계정, 원격 셸 = Windows PowerShell 5.1) |
| **파이프라인 CLI** | `mlxperPJT\thermal\pipeline.py` — 단계 레지스트리(e10·prius·mech·fluent·thesis 40여 단계). `list`/`show`/`check`/`init`/`run` |
| venv | `C:\Users\moa\.ansys_python_venvs\PyMotorEnv_310\Scripts\python.exe` |
| Ansys | v261(AEDT·Fluent·FreeFlow·Motor-CAD·MAPDL) / v252 MAPDL(PC1은 v252만 MAPDL 있음) |
| 큰 원본(git 밖) | `D:\KDH\simVary\Ansys_Thermal\` — `ff_e10_mesh_v2.cdb`(260MB), `prius_motor_mesh.cdb`, `e10_icepak_hybrid.aedt`, Fluent `Prius_work\*.h5` |
| FreeFlow 프로젝트 | `D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\` (`Project.freeflow`=유동 원본 보존, `Project_thermal.freeflow`, `Project_2way.freeflow`) |
| 산출물 | gdrive `Prius_thermal_viz/{prius,e10}/` (rclone `D:\KDH\NvidiaNemo\tools\bin\rclone.exe`, 리모트 `gdrive:`) |
| 전달 | **moa는 GitHub 접근 불가** → `git bundle` 로 주고받음. 대용량 입력은 사내 NAS `N:\_thermal_to_pc1_20260910` (공개 레포 금지) |
| 1차 문서 | `HANDOFF_20260721.md`(Prius) → `_20260722.md`(e10/FreeFlow) → `_20260907.md`(D1~D6 완료·정정) |

## 2. 파이프라인 지도 (번호순 스크립트, 모두 레포 내)

**먼저 `pipeline.py` 를 쓴다** — 스크립트를 직접 찾거나 읽지 말 것:

```powershell
cd D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal
python pipeline.py list --chain e10          # 단계 목록 (e10 | prius | mech | fluent | thesis)
python pipeline.py show e10.mapdl_hybrid     # 입출력·선행단계·주의 (한 줄 JSON)
python pipeline.py check e10                 # 입력 파일·모듈 사전점검 → problems 만 보면 됨
python pipeline.py init                      # C:\work\thermal_scratch 하위 폴더 준비 (최초 1회)
python pipeline.py run e10.mapdl_hybrid --detached --scheduled-task   # 이후 wait_done 1회
```
스크립트들의 로그·중간파일 위치는 `C:\work\thermal_scratch` 로 통일돼 있다(과거 세션 임시폴더에서 이전).

**결과 보고는 `thermal_report.py`** — 결과 JSON·그림을 한 파일 HTML(판정 카드·SVG 차트·그림 내장)로 만든다.
결과를 사람에게 보여줄 때 이미지·JSON 을 하나씩 읽어 요약하지 말고 이 리포트를 생성해 경로를 전달한다:
`python thermal_report.py --viz-root "G:\내 드라이브\Prius_thermal_viz"` → `C:\work\thermal_scratch\reports\`.
출력의 `gates` (pass/warn/fail) 만 확인하면 된다.

**Prius (실제 Toyota Prius, OD269/83.8mm, 8극48슬롯)** — `prius\scripts\`
01 Maxwell 손실 추출 → 02 STEP→gmsh→CDB → 03 MAPDL 하이브리드(JAC279 회로) →
08 **워터재킷 교차검증 버전**(Fluent 조건 정합) → 05~07·09 Fluent 추출/재솔브 → 10 검증 매트릭스.
드라이버: `python scripts\render_prius_viz.py all`. Icepak은 `prius\icepak\00~07`.

**e10 (FreeFlow 오일냉각 모터, OD198/150mm, 48슬롯8극 더블V, 16000rpm/460A)** — `freeflow\scripts\`
01 Motor-CAD 손실 → 02c Maxwell 2D 로터·자석·샤프트 추출 → 03b gmsh OCC 병합 메시(v2) →
**04 MAPDL 하이브리드**(OIL→JACKET/SPRAY/GAP_S/GAP_R/SHF) → 10 대시보드 viz →
11~14 FreeFlow 1-way 커플드(MAPDL 벽온도→오일) → 19 MAPDL vs Icepak 비교.

**학위논문 킷 D1~D6** — `plans\PLAN_20260906_assets\` (읽기전용 레퍼런스):
`preflight.py --deep` → `d1_cont_rating.py --mode super`(중첩, 정본) / d2 턴별 AC / d3 HTC 역산 /
d6 C67 원심응력 → `make_thesis_figs.py`. 산출 `thesis_out\`. 사용법은 `plans\README_PC1_SETUP.md`.

**Fluent 오일스프레이** — `fluent_spray\` : 메시는 **Fluent Meshing GUI 필수**, 이후 `oil_spray_cht_recipe.py`.

**시각화** — `thermal_viz.py <file.rth> <out_dir> [label] [clim_lo]` → 표준 GIF/PNG 세트
(`references/viz-standard.md`).

## 3. 도구 선택 요약

| 질문 | 도구 | 이유 |
|---|---|---|
| 손실 넣은 고체 온도장 + 냉각계 | **MAPDL 하이브리드** | 3D 전도 FEM + 회로(SURF152 온도의존 HTC). 냉각 도면 없이 성능값으로 가능 |
| 정답지(유동 포함 CHT) | Fluent | 조건 정합 시 MAPDL과 코일 1°C 이내 |
| AEDT 안에서 전도만 | IcepakFEA(AEDT Mechanical Thermal) | 대류는 고정 HTC 경계 |
| 오일 자유표면 유동 | FreeFlow(SPH, GPU) | **단독 CHT 불가**(벽=표면망, 열원 주입 없음) → MAPDL과 1-way/2-way |
| 엔드턴 스프레이+막+고체 CHT 한 솔버 | Fluent DPM+EWF | 메시만 GUI |

## 4. 꼭 지킬 함정 Top 10 (전체는 `references/gotchas.md`)

1. `SURF152` 는 **`KEYOPT(8)=2`** 없으면 대류가 조용히 무시된다.
2. `ESURF` 전에 전용 `R`/`REAL` 을 잡지 않으면 "Real constant referenced by types 3 and 2".
3. CDB EBLOCK tet10: `(19i10)` 에서 **11헤더+8노드 / 나머지 2노드 줄바꿈**. 한 줄이면 요소 0개(무증상).
4. 다중 하중단계: `ANTYPE` 은 **첫 회만**, `D,OIL,TEMP` 는 **매 하중단계 재지정** (안 하면 8.6e10 K 발산).
5. 실패한 이전 MAPDL 인스턴스에 재연결 금지 → `ansys_clean.ps1` 후 새 `run_location`.
   `PYMAPDL_START_INSTANCE`/`PYMAPDL_PORT` 잔존 시 attach 시도함.
6. FreeFlow: **Fluid Inlet 온도 기본 0°C** → `SetTemperature(70)`. 물리설정 하나라도 바꾸면
   결과셋 전체 무효(`DeleteResults()` 후 t=0). 원본 `Project.freeflow` 는 덮어쓰지 말 것.
7. Icepak: Network 경계는 전도-only에서 solver input 생성 실패 → **대류벽(HTC)** 사용,
   공기 Region 제거. imported 다물체는 비컨포멀 → 권선은 **네이티브 카브 균질체**로.
8. pyvista 연결성: tet10 CDB가 `VTK_TETRA` 로 보고되고 `cells_dict` 행순서가 어긋남 →
   체적·무게중심은 반드시 `compute_cell_sizes()`/`cell_centers()`.
9. matplotlib 3.10: `cm.get_cmap` 제거 → `thermal_viz` 회로 오버레이만 실패. `matplotlib.colormaps[...]`.
10. `.gitignore` 의 `*.png` 가 산출물을 삼킴 → `thesis_out` negation 유지. 산출 이미지는 gdrive.

## 5. 결과 판정 (요약 JSON을 이 값과 대조 — `references/results.md`)

- Prius 동일조건: 코일 max MAPDL 88.3/119.2 vs Fluent 88.3/118.2 °C (저부하/250A).
- e10 하이브리드 과도 900s: 권선 152.2 / 스테이터 126.0 / 자석 86.9 °C, JACKET 84.4 / SPRAY 91.9.
- e10 Icepak V1(균질+대류벽): 권선 136.5 °C (MAPDL 대비 10% 이내).
- 에너지 수지: MAPDL OIL 반력열 = 주입 손실 (rel < 1e-6). 어긋나면 BC 상실 의심.
- 값이 수천 °C 또는 5000 K → 물리 결과 아님(BC 상실·비컨포멀·Region 단락). 보고 전에 원인부터.

## 6. 스크립트 사용법 (moa: `C:\Users\moa\.claude\skills\motor-thermal-hybrid\scripts\`)

PowerShell 5.1 기준. 모두 한 줄 압축 JSON만 출력한다.

```powershell
$K = "C:\Users\moa\.claude\skills\motor-thermal-hybrid\scripts"
# 0) 솔브 전 정리 (기본 dry-run; MAPDL 솔버만 종료, Motor-CAD·ansyscl 보호)
powershell -File "$K\ansys_clean.ps1" -Kill -NewRunLocation C:\work\mapdl_runs
# 1) 긴 작업 실행 → 즉시 RUN_DIR=... 반환. ssh 로 원격 실행이면 -ScheduledTask (세션 끊겨도 생존)
powershell -File "$K\run_detached.ps1" -Script <레포>\freeflow\scripts\04_mapdl_thermal.py -Name e10_hybrid -ScheduledTask
# 2) 완료 대기: 백그라운드 명령으로 "한 번만" 실행 → 끝나면 done.json(+요약 JSON) 출력
powershell -File "$K\wait_done.ps1" -RunDir <RUN_DIR> -TimeoutMin 240 -SummaryJson <작업이 쓰는 요약 json>
# 3) 산출물 동기화: gdrive 업로드 + git push(가능 시) 또는 git bundle(GitHub 불가 시)
powershell -File "$K\sync_out.ps1" -VizDir <viz 폴더> -GdriveDest gdrive:Prius_thermal_viz/e10/viz
```

- 잡 스크립트는 환경변수 `RUN_DIR` 를 받으므로, 결과 요약을 `$RUN_DIR\summary.json` 에 쓰게 하면
  에이전트는 그 파일만 읽으면 된다.
- 게이트웨이에서 원격 실행 시: `ssh iso 'powershell -NoProfile -File ...'` (원격 셸은 PowerShell,
  인자는 작은따옴표 블록). wait 도 같은 방식으로 백그라운드 1회.

## 7. 데이터 공유 규칙

공개 포크 `enjoyneer87/eMach` 에는 사용자가 승인한 Prius·e10 콘텐츠만. **HMC 과제 수치,
`.cdb`/`.mot`/`.mdb` 원본, NAS 전달 자산은 공개 레포·gdrive 공개 폴더 금지.** 새 민감 데이터는 재확인.
