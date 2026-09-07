# PLAN_20260906_assets — moa 실행 킷 (D1 / D2 / D3 / D6)

> **이 문서를 먼저 읽는 사람**: 브랜치 `freeflow-e10-model` 을 `git pull` 한 직후의 moa 세션.
> **정본 계획서**: `../PLAN_20260906_thesis_thermal.md` (같은 `plans/` 폴더). 이 README 는 그 계획서를
> **오늘 밤 바로 돌릴 수 있는 명령어**로 옮겨 놓은 것이다. 숫자·경로는 전부 실측·실행 확인했다.
> **60초 요약**: `preflight.py` → `d1_cont_rating.py --dry-run` → `d1_cont_rating.py` (실솔브) →
> `make_thesis_figs.py` → 커밋. 나머지는 이 순서를 못 지킬 때 읽으면 된다.

---

## 1. 이게 뭔가 — 그리고 채널 규칙 (먼저 읽을 것)

### 1-1. 채널 규칙

`plans/README.md:3-4` 와 계획서 7행이 정한 규칙이다. **어기면 두 세션이 서로의 커밋을 밟는다.**

| 폴더 | 쓰는 주체 | moa 의 권한 |
|---|---|---|
| `mlxperPJT/thermal/plans/**` (이 폴더 포함) | 학위논문 세션 (레포 `Thesis_SKKU`, PC `user`) | **읽기 전용. 절대 고치지 말 것** |
| `mlxperPJT/thermal/**` 나머지 전부 | **moa** | 자유롭게 씀 |
| 루트 `.gitignore` | **moa** (plans/ 밖이므로 학위논문 세션은 못 고침) | moa 가 고쳐야 함 (§5-2) |

따라서 이 디렉터리의 `.py` 파일들은 **읽기 전용 참조 구현(reference implementation)** 이다.
moa 는 이것을 **`mlxperPJT/thermal/freeflow/scripts/` 로 복사(promote)** 하고,
레포의 번호 규약대로 이름을 바꾼 뒤 **그 승격 커밋을 직접** 한다.

### 1-2. 승격(promotion) 명령 — 그대로 복사해서 실행

```powershell
# --- 먼저 이 두 줄만 자기 환경에 맞게 고친다 -------------------------------
$PY   = "C:\Users\moa\.ansys_python_venvs\PyMotorEnv_310\Scripts\python.exe"
$REPO = "C:\Users\moa\eMach"          # <- moa 의 eMach 클론 실제 경로로 교체
# ---------------------------------------------------------------------------
$KIT  = "$REPO\mlxperPJT\thermal\plans\PLAN_20260906_assets"
$SCR  = "$REPO\mlxperPJT\thermal\freeflow\scripts"
$OUT  = "$REPO\mlxperPJT\thermal\thesis_out"

git -C $REPO pull
```

승격은 **솔브가 다 끝난 뒤** 결과 커밋과 함께 하는 것이 깔끔하다(먼저 해도 무방).

```powershell
# 공유 모듈 3개 - 이름 그대로
Copy-Item "$KIT\jeet_map_loader.py","$KIT\icont.py","$KIT\thesis_style.py" $SCR -Force

# 러너 - 레포 번호 규약으로 개명
Copy-Item "$KIT\d1_cont_rating.py"          "$SCR\20_d1_cont_rating.py"          -Force
Copy-Item "$KIT\d2_ac_turnwise.py"          "$SCR\21_d2_ac_turnwise.py"          -Force
Copy-Item "$KIT\d6_c67_stress.py"           "$SCR\22_d6_c67_stress.py"           -Force
Copy-Item "$KIT\d3_htc_backout.py"          "$SCR\23_d3_htc_backout.py"          -Force
Copy-Item "$KIT\d3_freeflow_gravity_fix.py" "$SCR\24_d3_freeflow_gravity_fix.py" -Force

# 도구 2개 - 번호 규약 대상이 아니므로 이름 유지 (선택이지만 권장)
Copy-Item "$KIT\make_thesis_figs.py","$KIT\preflight.py" $SCR -Force
```

> **깊이(depth) 확인 완료**: `plans/PLAN_20260906_assets/` 와 `freeflow/scripts/` 는 **둘 다 레포 루트에서
> 4단계 아래**다. 모든 스크립트가 `--repo` 기본값을 `__file__` 에서 `os.pardir` 4번으로 뽑으므로
> **승격 전후 모두 기본값이 맞다.** 그래도 `--repo` 를 명시하면 cwd 와 무관하게 확실하다.
> 스크립트끼리는 **같은 디렉터리 안에서만** import 한다(`import jeet_map_loader` 등) — 그래서 킷을
> 통째로 복사하기만 하면 동작한다. `ansys.dpf.core` 는 **어디서도 import 하지 않는다.**

---

## 2. Preflight — 무조건 먼저

30초짜리 환경 게이트. **CDB 없음, venv 틀림, 디스크 부족** 같은 것을 배치 전에 전부 드러낸다.

```powershell
& $PY "$KIT\preflight.py" --repo $REPO `
      --cdb D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2.cdb `
      --deep --fix --json "$OUT\preflight.json" --log "$OUT\preflight.log"
```

* `--deep` : 킷 모듈의 self-test(`icont`, `jeet_map_loader`)까지 돌린다 (몇 초 추가).
* `--fix`  : 고칠 수 있는 것만 고친다 — 현재는 `thesis_out` 디렉터리 생성뿐. **`.gitignore` 는 건드리지 않고 패치문만 출력**한다.
* **종료코드 `0` = 진행 가능** (WARN 은 막지 않는다) / **`1` = FAIL 있음 → 배치 시작하지 말 것.**

### FAIL 행별 의미와 조치

| FAIL id | 의미 | 조치 |
|---|---|---|
| `python.venv` / `python.version` | `PyMotorEnv_310` 이 아닌 인터프리터로 돌렸다 | `$PY` 로 다시 실행. Ansys/pyvista 는 그 venv 에만 있다 |
| `import.numpy` / `import.matplotlib` | 필수 패키지 없음 | `& $PY -m pip install numpy matplotlib` |
| `import.ansys.mapdl.core` | **D1/D2 실솔브 불가** | `& $PY -m pip install ansys-mapdl-core` |
| `import.ansys.mapdl.reader` | D2 컨투어 / D6 rst 리더 불가 | `& $PY -m pip install ansys-mapdl-reader` |
| `import.pyvista` | D2 zcut PNG, D6 3D 컨투어 불가 (D6 는 matplotlib 산점도로 자동 강등) | `& $PY -m pip install pyvista` |
| `font.malgun` | Malgun Gothic 없음 → 그림 한글 깨짐 | 폰트 설치 후 `matplotlib` 캐시 삭제 |
| **`cdb`** | **1순위 블로커.** `ff_e10_mesh_v2.cdb` 없음 | §5-1 참조. **없으면 D1/D2 는 시작조차 못 한다** |
| `jeet_map` / `jeet_map.rated` | 손실 맵이 없거나 정격셀 수치가 다르다 | `git pull` 이 제대로 됐는지 확인. 맵은 git 에 있다 |
| `kit.modules` / `kit.icont_selftest` / `kit.map_selftest` | 킷 파일 누락·손상 | `git checkout -- mlxperPJT/thermal/plans/` |
| `git.repo` / `git.branch` | 레포가 아니거나 브랜치가 `freeflow-e10-model` 이 아니다 | `git checkout freeflow-e10-model` |
| `git.identity` | `user.name` / `user.email` 미설정 → 커밋 실패 | `git config user.name ...` / `user.email ...` |
| `disk.cdb` / `disk.run` | 여유 < 10 GiB (1.11 M 절점 정상해석 기준의 공학적 판단값, 실측 아님) | 정리하거나 `--run-dir` 를 여유 있는 드라이브로 |

`WARN` 중 **반드시 눈으로 확인할 것 두 가지**:

* `gitignore` — PNG 가 `.gitignore:39 *.png` 에 걸린다. **솔브는 되지만 커밋 단계에서 조용히 빠진다.** → §5-2
* `mpl.get_cmap` — `matplotlib >= 3.9` 에서 `thermal_viz.py:456` 의 `matplotlib.cm.get_cmap` 이 제거됐다.
  **회로 오버레이 경로(`circuit_3d_png` / `circuit_3d_gif` / `full_dashboard_gif`)만** 죽는다.
  킷은 `contour_png` / `cut3d_png` / `component_png` 만 쓰므로 영향 없다.

### 배치 직전 항상 하는 것 (stale MAPDL 트랩)

```powershell
Get-Process ANSYS*,MAPDL* -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 3. 작업 순서 — D1 → D2 → (D3 / D6)

계획서 §1 의 우선순위 그대로. **D1 이 최우선**이고, D1 이 끝나야 5장 표가 채워진다.
D3 와 D6 는 서로 독립이며 D1/D2 와도 독립이라 순서를 바꿔도 된다(D3 는 GPU 5시간이라 밤에 걸어두기 좋다).

모든 러너는 **stdout 과 `--log` 파일에 동시에** 기록한다(무인 배치 대비).

---

### D1 — e10 연속 정격 곡선 ★최우선

**산출물**: `thesis_out/e10_cont_rating.json` (`runs` 64엔트리 + `I_cont_Arms`)
→ 그림은 `make_thesis_figs.py` 가 굽는다: `cont_rating_Tw_vs_I.png`, `cont_rating_Icont_vs_n.png`

#### 3-1-1. 드라이런 (Ansys 불필요, 약 1초)

```powershell
& $PY "$KIT\d1_cont_rating.py" --dry-run --repo $REPO --out $OUT
```

`e10_cont_rating_dryrun.json` (약 127 KB) 이 생기고 `exit code 0` 이 찍히면 통과.
**눈으로 확인할 숫자** (이 PC 에서 실측한 값과 정확히 같아야 한다 — 손실은 드라이런에서도 진짜다):

```
JEET map: 240 records
run table: 64 entries (4 speeds x 4 currents x 2 cases x 2 h-sets)
rated cell 16000 rpm / 460 A / AC: cu_slot 31412.0  cu_end 18459.5  ac_slot 37171.8
                                   fe_s 2044.7  fe_r 81.5  pm 654.7 W  (total 89.8 kW)
superposition: worst error 1.137e-13 K vs tol 0.05 K -> PASS
```

> 드라이런의 **온도는 합성(synthetic) 영향행렬로 만든 가짜**다. 검증 대상은 (a) 맵 로딩,
> (b) 64엔트리 손실표, (c) 중첩 재구성 수학, (d) I_cont 근찾기, (e) JSON 스키마 — 이 다섯이다.

#### 3-1-2. 실솔브

```powershell
Get-Process ANSYS*,MAPDL* -ErrorAction SilentlyContinue | Stop-Process -Force

& $PY "$KIT\d1_cont_rating.py" --repo $REPO `
      --cdb D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2 `
      --out $OUT --nproc 4 --log "$OUT\d1_cont_rating.log"
```

* **예상 시간**: 셋업(1.11 M 절점 `CDREAD` + 회로 빌드) 5~15분 + **12솔브** 10~15분 ≈ **20~40분**.
  (솔브당 40~60초 추정. 계획서의 "13.5 s/런" 은 544 k 절점 v1 메시·회로 없음 기준이라 적용 불가.
  `_timing.solves` 에 솔브별 실측 시간이 남으므로 1회차 이후로는 추정이 아니라 기록이 된다.)
* **종료코드**: `0` 정상 / `2` 중첩 검증 실패 + `--on-superposition-fail stop` / `4` MAPDL·셋업 실패(메시지가 실패한 단계와 런을 지목) / `5` 맵 셀 없음 / `130` Ctrl-C.

**로그에서 눈으로 확인할 것**

1. `superposition: worst error <값> K vs tol 0.05 K -> PASS` ← **이게 FAIL 이면 아래 §4-3**
2. 매 솔브 뒤 최소 절점온도 ≥ 69.99 °C (양의 발열 + OIL 70 °C 단일 Dirichlet 이면 물리적으로 당연)
3. `I_cont` 블록. **16 krpm 에서 `status=extrap_low` 가 나오는 것이 정상**이고 그게 결론이다
   (최저 격자전류 115.075 A 에서도 이미 한계 초과 → 계획서의 4점 보간이었다면 순수 외삽이 됐을 자리).
4. 손실이 클수록 절대온도가 수백~수천 °C 로 나온다 — **버그 아니라 발견**이다. §5-5.

#### 3-1-3. (선택) 계획서 문자 그대로의 64 직접솔브 교차검증

시간이 남으면 돌린다. §3-1-2 결과와 일치하면 **그 자체가 논문급 선형성 증거**다.

```powershell
& $PY "$KIT\d1_cont_rating.py" --repo $REPO `
      --cdb D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2 `
      --out $OUT --mode brute --out-name e10_cont_rating_brute.json `
      --log "$OUT\d1_cont_rating_brute.log"
```

예상 45~70분 + 셋업.

#### 3-1-4. 그림

```powershell
& $PY "$KIT\make_thesis_figs.py" --repo $REPO --which d1 --log "$OUT\make_figs.log"
```

실측 크기(합성 데이터 기준): `cont_rating_Tw_vs_I.png` 280.6 KB · `cont_rating_Icont_vs_n.png` 168.5 KB
— 둘 다 300 KB 한도 안. 온도가 수천 °C 라 y축은 자동으로 `log` 가 선택된다.
5장 본문용으로 선형 클립 버전이 필요하면:

```powershell
& $PY "$KIT\make_thesis_figs.py" --repo $REPO --which d1 --yscale clip --clip-hi 300
```

---

### D2 — 슬롯 내 AC 동손 분포: 균일 vs 턴별

**산출물**: `thesis_out/e10_ac_turnwise_hotspot.json`
+ `e10_ac_turnwise_zcut_uniform_460A.png` / `e10_ac_turnwise_zcut_turnwise_460A.png`
+ (`make_thesis_figs.py` 가 굽는) `ac_turnwise_hotspot.png`

#### ★ 실행 전 반드시: PYTHONPATH

D2 의 컨투어 단계는 `from thermal_viz import ThermalViz` 를 한다. `thermal_viz.py` 는
`$REPO\mlxperPJT\thermal\thermal_viz.py` 에 있고 **킷 디렉터리에도 `freeflow\scripts` 에도 없다.**
(레포의 기존 스크립트는 `10_mapdl_dashboard_viz.py:7` 처럼 죽은 절대경로를 `sys.path` 에 꽂았다 — 킷은 그 짓을 안 한다.)

```powershell
$env:PYTHONPATH = "$REPO\mlxperPJT\thermal"
```

**안 걸어도 JSON 은 정상으로 나온다.** 실패는 `try/except` 로 잡혀 로그에
`figure generation failed:` 로만 남고 zcut PNG 2장만 빠진다. 다만 그 PNG 를 되살리려면 **재솔브가 필요**하니
(패널이 그 런의 `.rth` 를 참조한다) 시작 전에 걸어두는 편이 훨씬 싸다.
논문 그림 `ac_turnwise_hotspot.png` 는 JSON 만 보고 그리므로 pyvista/thermal_viz 없이도 나온다.

#### 3-2-1. 드라이런 (약 1초, Ansys 불필요)

```powershell
& $PY "$KIT\d2_ac_turnwise.py" --dry-run --repo $REPO --out $OUT
```

**`VERDICT: PASS` 와 `DONE-OK` 가 둘 다 찍히기 전에는 솔버 시간을 쓰지 말 것.**
확인할 숫자 (손실은 드라이런에서도 진짜다):

```
losses @ 16000 rpm / 460 A / 36.0 deg :
  P_turn = [22168.641, 12658.991, 9844.569, 8426.752, 7776.733, 7708.192] W   (T1=공극측 ... T6=요크측)
  active = 68583.8784 W (dc 31412.0354 + ac 37171.8431), end = 18459.4553 W
  [inv ] turnwise active sum(q*V)=68583.878433 W vs 68583.878433 W  rel=9.12e-15
  [inv ] uniform vs turnwise injected totals agree to rel 9.12e-15
```

마지막 두 줄이 핵심 불변량이다: **균일과 턴별이 완전히 같은 총량을 넣는다** — 그래야 비교가 오염되지 않는다.

#### 3-2-2. (선택) 1솔브 스모크 테스트, 5~10분

`cdread` + 회로 + BFE 매크로 + 정상해석이 실메시에서 도는지만 본다.

```powershell
& $PY "$KIT\d2_ac_turnwise.py" --repo $REPO `
      --cdb D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2 `
      --run-dir D:\KDH\simVary\Ansys_Thermal\d2_run `
      --nproc 8 --modes uniform --currents 460.0 --no-png --out $OUT
```

#### 3-2-3. 실행 (4솔브)

```powershell
$env:PYTHONPATH = "$REPO\mlxperPJT\thermal"
Get-Process ANSYS*,MAPDL* -ErrorAction SilentlyContinue | Stop-Process -Force

& $PY "$KIT\d2_ac_turnwise.py" --repo $REPO `
      --cdb D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2 `
      --run-dir D:\KDH\simVary\Ansys_Thermal\d2_run `
      --nproc 8 --out $OUT --log "$OUT\d2_ac_turnwise.log"
```

* 16,000 rpm × {230.05, 460.0} A × {uniform, turnwise} = **4 솔브**, 전부 정상해석, h 는 `base` 고정.
* **예상 시간**: 셋업 5~15분 + 4솔브 ≈ **20~40분**.
* **종료코드**: `0` 정상 / `1` 실패(로그에 트레이스백).
* **눈으로 확인**: `sanity verdict: PASS`, `DONE-OK`, 그리고 `HEADLINE` 두 줄.
  기대 형태 — *"uniform injection under-predicts the winding hotspot by <N> K … 공극측 T1 이 요크측 T6 보다 <M> K 뜨겁다"*.
  균일 주입에서 `dT(T1-T6)` 이 **정확히 0.00 K** 이어야 한다(같은 q 를 주므로). 0 이 아니면 비닝이 깨진 것.
* **주의(JSON 에도 적혀 있음)**: `turn_T_C['max']` 는 밴드에 걸친 요소의 최고절점을 잡으므로
  경계를 가로지르는 요소 때문에 이웃 밴드가 거의 같은 max 를 낼 수 있다. **인용할 값은 `turn_T_C['mean']`**
  (체적분율 가중)이다. 드라이런에서 실제로 T1 max 1160.3 vs T2 max 1154.6 인데 mean 은 1075.4 vs 865.6 이었다.

---

### D6 — C67 회전자 원심 응력 (3장용, 소)

**산출물**: `thesis_out/c67_stress.json` + `c67_stress_vonmises.png` + `c67_stress_ur.png` + `c67_stress_vs_speed.png`

#### 3-3-1. 드라이런 (약 4.5초, Ansys 불필요)

```powershell
& $PY "$KIT\d6_c67_stress.py" --dry-run --repo $REPO --out "$OUT\d6_dryrun"
```

확인할 숫자 (해석해 게이트, 이 PC 실측):

```
analytic annulus @18000 rpm : hoop(bore) 131.96 MPa, hoop(rim) 54.23 MPa, u_r(rim) 21.13 um
expected FE band            : von Mises [263.9, 527.9] MPa, delta_r [0.0200, 0.0500] mm
SANITY GATE: PASS
```

이 게이트는 **실행 때마다 자동으로 돈다.** 실측 FE 값이 밴드를 벗어나면 `WARN` 만 찍고 죽지는 않는다
(밴드 밖 결과는 버그가 아니라 발견일 수 있으므로).

#### 3-3-2. 실행

먼저 **MECH 폴더 통째로** 가져온다. `file.rst` 하나만으로는 `--sweep-method resolve` 가 불가능하다(§5-3).

```powershell
robocopy "<학위논문PC공유>\KDH\251114_C67_test\C67_stress_files\dp0\SYS-5\MECH" "D:\KDH\C67\MECH" /E

& $PY "$KIT\d6_c67_stress.py" --repo $REPO --mech-dir D:\KDH\C67\MECH `
      --rpm 18000 --sweep 12000,15000,18000,21000 --sweep-method scale `
      --out $OUT --log "$OUT\d6_c67_stress.log"
```

`scale` 은 ω² 해석 스케일링이다 — 선형탄성 + bonded 접촉 + NLGEOM off 전제에서 **정확**하고,
마찰접촉이나 Neuber/Glinka 소성보정에는 **무효**다. 로그에 `ds.dat` / `file.db` / `.cdb` 가
보인다고 찍히면 그때만 실제 재솔브 스윕을 돌린다(4점 × 약 13초):

```powershell
& $PY "$KIT\d6_c67_stress.py" --repo $REPO --mech-dir D:\KDH\C67\MECH `
      --sweep-method resolve --out $OUT
```

* **종료코드**: `0` 정상 / `1` 치명적 실패(로그에 트레이스백).
* `--yield-MPa` 를 주지 않으면 JSON 의 `yield_MPa` / `safety_factor` 가 **`null`** 로 나간다.
  **의도된 것**이다 — 20PN1150F 항복강도는 논문 쪽에서 데이터시트로 채운다.
  Motor-CAD 의 305 MPa 는 프로그램 기본값이지 실측이 아니므로 **넣지 말 것.**
* 재료·요소 파라미터(E 192.5 GPa, ν 0.3, ρ 7650, μ 0.2, bonded, 요소 0.3 mm)는 `.rst` 에서 읽을 수 없다.
  CLI 인자로 받아 `_model_meta` 에 그대로 기록하고 `_meta_caveat` 에 "읽은 게 아니라 받은 값"이라고 적는다.

---

### D3 — 중력 수정 후 FreeFlow 재솔브 → HTC 역산 갱신

**산출물**: `thesis_out/htc_backout_horizontal.json` (기존 `freeflow/data/htc_backout.json` 과 같은 스키마)

D3 는 **GPU 약 5시간**이 드는 유일한 항목이다. 밤에 걸어두는 것을 권한다.
`d3_freeflow_gravity_fix.py` 는 **솔브를 시작하지 않는다** — 설정만 하고 새 파일로 저장한 뒤 끝난다.

#### 3-4-1. 수식 재현성 확인 (2초, Ansys 불필요)

```powershell
& $PY "$KIT\d3_htc_backout.py" --self-test
& $PY "$KIT\d3_htc_backout.py" --verify-legacy --repo $REPO
```

`SELF-TEST PASSED`, `checks: 28 total, 0 failed`, `VERIFY-LEGACY PASSED` 가 나와야 한다.
이게 통과한다는 것은 이 모듈의 4개 식이 기존 `htc_backout.json` 을 **그 파일 자신의 저장값으로부터**
재현한다는 뜻이다 (원본 역산 스크립트는 옛 scratchpad 와 함께 소실됐다).
`h_grad` Stator **192.9** / Winding **186.3** W/m²K, 역산된 delta Stator **0.743074** / Winding **0.740323** mm
(둘 다 프로파일 1번 칸 `[0.5, 1.0) mm` 안, 공칭 중심 0.75 mm 에서 −0.9 % / −1.3 %).

#### 3-4-2. 중력 API 탐색 패스 (30초, 아무것도 안 바꾼다)

FreeFlow 중력 setter 이름은 **레포 어디에도 쓰인 적이 없다.** 추측하지 말고 먼저 본다.

```cmd
set FF=C:\Program Files\ANSYS Inc\v261\FreeFlow\bin\FreeFlow.exe
set D3_PROBE_ONLY=1
set D3_ORIG_PRJ=D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project_thermal.freeflow
set D3_LOG=D:\KDH\simVary\d3_gravity_probe.txt
"%FF%" --headless --script "%KIT%\d3_freeflow_gravity_fix.py"
type D:\KDH\simVary\d3_gravity_probe.txt
```

로그의 **GRAVITY-LIKE** 줄을 반드시 눈으로 읽고 다음 단계로 간다.

#### 3-4-3. 중력 수정 적용 (원본은 건드리지 않는다)

```cmd
set D3_PROBE_ONLY=0
set D3_LOG=D:\KDH\simVary\d3_gravity_fix.txt
"%FF%" --headless --script "%KIT%\d3_freeflow_gravity_fix.py"
type D:\KDH\simVary\d3_gravity_fix.txt
```

`Project_thermal_horizontal.freeflow` 로 **새로 저장**한다.
**종료코드**: `0` 저장 완료 / `3` 중력 setter 가 하나도 안 먹었거나 읽어보니 여전히 축방향 /
`4` 벽 BC 읽기검증 실패 / `5` Fluid Inlet 이 70 °C 가 아님. **3·4·5 는 아무것도 저장하지 않는다.**

> 왜 4·5 가 치명적인가: `DeleteResults()` 는 벽 BC 와 inlet 온도를 날린다. 그리고
> `12_freeflow_thermal_solve.py:35-40` 의 과거 최대 실책이 **Fluid Inlet 0 °C** 였다 —
> 벽만 데워도 유입오일이 계속 0 °C 라 벌크가 안 데워졌다. 이걸 못 잡으면 5시간을 통째로 버린다.

#### 3-4-4. 솔브 (GPU 약 5시간) → 역산

`12_freeflow_thermal_solve.py` 패턴의 러너를 `PRJ = Project_thermal_horizontal.freeflow`,
`TARGET_S = 8.0`, `CAP_S` 상향으로 돌린다. **resume 금지** — 물리설정 변경은 결과셋을 all-or-nothing 으로
무효화한다(HANDOFF §6). t=0 부터다.

```powershell
& $PY "$KIT\d3_htc_backout.py" --repo $REPO `
      --sph "D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project_thermal_horizontal.freeflow.files\simulation\<마지막>.sph" `
      --geom-dir "D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Geometry" `
      --t-reached 8.0 --log "$OUT\d3_backout.log"
```

* **종료코드**: `0` 정상 / `1` self-test·verify-legacy 실패 / `2` 입력 부족(`--sph`/`--particles` 없음,
  **`--t-reached` 없음**, wall-temps 없음, `dist`/`region` 도 `--geom-dir` 도 없음) / `3` 어느 벽에 입자가 0개.
* **`--t-reached` 는 추측하지 않는다.** 실제 도달한 물리시간을 반드시 넣어라 — 그대로 `_soltype` 에 `"transient+8.0s"` 로 들어간다.
* `--t-bulk` 를 주지 않으면 **전체 입자의 평균온도**를 벌크로 쓴다. 익스포트가 근벽 슬랩만 담고 있으면
  이 가정이 틀린다. 선택한 값은 로그와 `_provenance.notes` 에 남으니 확인할 것. **moa 판단이 가장 필요한 지점이다.**
* 벽면거리 계산은 `--geom-dir` 의 STL 로 pyvista `compute_implicit_distance` 를 쓴다.
  이 경로는 이 PC 에 pyvista 가 없어 **미검증**이다 — 실패하면 조용히 넘어가지 않고 명시적으로 죽는다.
  대안은 `dist` / `region` 열을 이미 담은 `--particles` CSV/NPZ (pyvista·h5py 불필요).

---

## 4. ★ moa 가 반드시 이해해야 할 설계 결정 — 중첩(superposition)

### 4-1. 계획서의 문자와 다르다 (그리고 왜 그래도 되는가)

계획서 §1 D1 은 **"총 64런"** 을 쓰라고 적혀 있다. 킷의 기본 경로(`--mode super`)는 **12솔브**만 돈다.
**출력 스키마는 계획서가 지정한 그대로**이고(`runs` 64엔트리, `I_cont_Arms` 중첩 dict, `_loss_source`·`_htc`·`_soltype`),
64엔트리는 하나도 빠짐없이 채워진다. 계획서의 **의도**(64격자점의 T_w 표 + I_cont(n))는 100 % 만족하고,
**글자**(64회 직접 솔브)만 다르다. 이 편차를 그대로 밝히고 시작하는 것이 이 절의 목적이다.

### 4-2. 왜 수학적으로 정확한가

정상해석 모델은 **정확히 선형**이다:

* 상수 열전도율 (`04_mapdl_thermal.py:43-47`)
* 상수 대류계수 (SURF152 `SFE ... CONV`)
* 상수 회로 컨덕턴스 (COMBIN14)
* 복사 없음
* Dirichlet 이 **정확히 하나** (`D,OIL,TEMP,70`)

따라서 모든 절점온도는 손실벡터의 **아핀 함수**다:

```
T_node(P) = 70 + Σ_s ( P_s · G[node][s] ),   s ∈ {cu_slot, cu_end, ac_slot, fe_s, fe_r, pm}
```

h세트당 **단위솔브 5회**(한 번에 한 소스에만 1 kW, 나머지 0)로 영향행렬 `G` 전체가 나온다.
`ac_slot` 은 D1 에서 `cu_slot` 과 **같은 요소집합**에 균일 주입되므로 `G[:,ac_slot] ≡ G[:,cu_slot]` 이라
별도 솔브가 필요 없다 (`icont.solve_influence` 가 이 aliasing 을 한다).
→ **2 h세트 × 5 = 10 단위솔브 + 2 검증솔브 = 12솔브.**

**부수효과가 사실은 본론이다**: I_cont 가 4개 격자전류 사이의 보간이 아니라 **연속 근찾기**가 된다.
16 krpm 에서는 최저 격자전류 115.075 A 에서도 이미 권선이 180 °C 를 넘으므로,
계획서의 4점 보간이었다면 그 자리는 **순수 외삽**이었다. 지금은 `I_cont` 값 + `status=extrap_low` 로
정직하게 보고된다.

**"권선 최대온도"는 아핀이 아니다** (절점에 대한 max 는 볼록함수라 argmax 절점이 손실비율에 따라 움직인다).
그래서 킷은 권선을 스칼라 영향행 하나로 줄이지 않는다. **절점별로** `G` 를 보관하고(1.11 M × 5 float64 = 45 MB),
64개 손실벡터 각각에 대해 **전체 절점장을 재구성**한 뒤 부품 절점집합에서 max 를 취한다 — 정확하다.
I_cont 는 argmax → 근찾기 → argmax 를 반복하는 고정점으로 풀고, 반복과 절점 id 를 전부 JSON 에 기록한다.

### 4-3. 검증 게이트 — 가정하지 않고 확인한다

러너는 **직접 전부하 솔브 2회**를 추가로 돈다:

* 8000 rpm / 230.05 A / Case AC / base h
* 2000 rpm / 460.0 A / Case DC / base h

그리고 재구성값과 직접해를 **0.05 K** 기준으로 비교한다. 여기에 5소스 단위솔브 아핀 왕복시험까지 더한다.
결과는 전부 `_superposition_check` 에 기록된다.

**실패하면** 큰 배너가 뜨고, 기본 동작은 **같은 MAPDL 세션 안에서 계획서 문자 그대로의 64 직접솔브로 자동 폴백**한다
(메시와 회로는 이미 만들어져 있으므로 셋업 비용이 없다). 동작은 `--on-superposition-fail` 로 고른다:

| 값 | 동작 | 종료코드 |
|---|---|---|
| `brute` (기본) | 배너 + 같은 세션에서 64 직접솔브로 완주 | `0` |
| `stop` | 배너 + 영향계수(진단용)만 남기고 중단 | **`2`** |
| `continue` | 배너 + 재구성값을 그대로 씀 (**의심스러운 값**) | `0` |

수동 폴백은 `--mode brute` 다 (§3-1-3). 두 경로의 출력 스키마는 동일하다.

---

## 5. 블로커와 대처

### 5-1. `ff_e10_mesh_v2.cdb` 가 없을 수 있다 — 1순위 블로커

* 1,113,924 절점 / 737,265 tet10 SOLID87, **260 MB**, **git 에 없다**(moa 로컬 전용).
* 기대 경로: `D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2.cdb`
* **없으면 D1 과 D2 는 시작조차 못 한다.** D3 와 D6 는 메시가 필요 없으니 그쪽부터 돌려라.

```powershell
Test-Path D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2.cdb   # True 여야 한다
```

**재생성 사슬(수 시간, AEDT 필요)**:
`02c_maxwell_geom_extract.py` → `e10_geom.json` → `03_stl_to_cdb.py` → `03b_rotor_from_maxwell.py`.
문제는 중간 산출물 `e10_geom.json` 이 **이미 삭제된 scratchpad 에 있었다**는 점이다.
즉 재생성은 02c 부터 다시 돌려야 하고 AEDT 가 필요하다. **먼저 로컬 디스크를 뒤져라. 재생성은 최후수단이다.**

### 5-2. `.gitignore:39 *.png` 가 thesis_out PNG 를 조용히 삼킨다

이 PC 에서 실측 확인:

```
$ git check-ignore -v -- mlxperPJT/thermal/thesis_out/cont_rating_Tw_vs_I.png
.gitignore:39:*.png	mlxperPJT/thermal/thesis_out/cont_rating_Tw_vs_I.png
```

`.json` 과 `.py` 는 통과한다. `.csv` 는 `.gitignore:183` 에 걸린다.
**솔브는 정상이고 커밋 단계에서만 조용히 빠지므로**, 이 항목은 preflight 에서 `FAIL` 이 아니라 `WARN` 이다
(배치를 막으면 안 되므로). 러너들도 실행 끝에 `git check-ignore` 자가점검을 돌려 알려준다.

**조치 — 루트 `.gitignore` 파일 맨 끝에 아래 3줄을 덧붙인다. `.gitignore` 는 `plans/` 밖이므로 학위논문 세션은
못 고친다. moa 가 해야 한다.**

```gitignore
# --- thesis_out 산출물은 *.png / *.csv 규칙에서 제외 (PLAN_20260906 8행) ---
!mlxperPJT/thermal/thesis_out/*.png
!mlxperPJT/thermal/thesis_out/*.csv
```

적용 확인 (**아무것도 안 찍히고 exit 1 이어야 정상**):

```powershell
git -C $REPO check-ignore -v -- "mlxperPJT/thermal/thesis_out/cont_rating_Tw_vs_I.png"
git -C $REPO ls-files mlxperPJT/thermal/thesis_out/    # add 후 PNG 가 실제로 스테이징됐는지
```

임시방편은 `git add -f mlxperPJT/thermal/thesis_out/` 지만, 다음 사람이 또 밟으므로 정식 해법을 권한다.

### 5-3. C67 `.rst` 가 이 킷을 만든 PC(학위논문 PC)에 있고 moa 에는 없다

원본: `E:\KDH\251114_C67_test\C67_stress_files\dp0\SYS-5\MECH\file.rst` (34.8 MB).
**세 갈래 중 하나를 고른다:**

1. **MECH 폴더 통째로 복사** (권장). `file.rst` 하나만 오면 안 된다 — MAPDL `/POST1` 은 DB(절점/요소)가
   메모리에 올라와 있어야 `PRNSOL` 이 동작하고, Workbench 는 기본적으로 `file.db` 를 저장하지 않는다
   (Analysis Settings "Save MAPDL db = No"). `ds.dat` / `file.db` / `.cdb` 가 같이 와야 `--sweep-method resolve` 가 가능하다.
   `ansys.mapdl.reader.read_binary` 는 rst 단독으로도 읽으므로, rst 만 와도 `--sweep-method scale` 경로는 산다.
2. **moa 에서 `C67_stress.wbpj` 재솔브** (약 13초).
3. **Motor-CAD 2D 예비안** — 이 레포에 **이미 패키지·검증된 원심해석 경로**가 있다:
   `tools/motorCAD/pyMCAD/stress.py` (859행: `get_stress_data` / `StressRegions` / `plot_mesh_stress_fields` /
   Neuber·Glinka 보정), 사용 예는 `mlxperPJT/KETI/RotorStress_e10.ipynb`.
   `.mot` 파일 하나만 있으면 `mc.set_variable("ShaftSpeed", 18000)` → `mc.do_mechanical_calculation()` →
   `get_stress_data(mc)` 로 `MaxStress_RotorLam` / `MaxDisplacement_RotorLam` / **`SafetyFactor_RotorLam`** 까지 바로 나온다.
   단 **2D 평면응력**이므로 `_soltype` 을 그에 맞게 적어야 한다.

> **시간낭비 방지**: 레포 루트의 `251114_C67_test_Moa_Max3D.py` (22,191행)는 **구조해석이 아니라**
> Motor-CAD 가 자동생성한 Maxwell 3D Transient **전자계** 빌드 스크립트다(운전점도 5600 rpm/630 A 로 다르다).
> `.rst` 를 만들 수 없고 만들 의도도 없다. **여기에 1시간도 쓰지 말 것.**

### 5-4. h세트 값이 세 군데서 다르다 (190/190 vs 193/186 vs 실측 192.8/186.3)

| 출처 | 값 (jacket / spray) |
|---|---|
| 계획서 17행 (§0 요약) | 193 / 186 |
| **계획서 §1 D1 사양 (35행·40행, 출력 스키마 포함)** | **190 / 190** |
| 실측 `freeflow/data/htc_backout.json` `h_grad` | 192.8 / 186.3 |

**킷은 190/190 으로 돌린다.** 이유: 계획서의 D1 사양과 그 출력 JSON 스켈레톤이 둘 다 190/190 이고,
그 스켈레톤이 논문 표로 그대로 들어가기 때문이다. 실측값은 버리지 않고 JSON `_htc_meta` 에 남긴다:

```json
{"sph_source": "freeflow/data/htc_backout.json h_grad",
 "jkt_backout": 192.8, "spray_backout": 186.3, "rounded_to": 190.0,
 "plan_line17_says": "193 (jacket) / 186 (spray)",
 "plan_D1_spec_says": "190 / 190 (plan lines 35 and 40)",
 "decision": "...", "warning": "..."}
```

> **`sph` h세트 자체에 붙는 경고**: 그 역산은 **중력이 축방향(-Z)으로 잘못 들어간** 6.53 s 런에서 나왔다
> (HANDOFF §10-4). D3 가 이것을 교체한다. 그때까지 `sph` 세트는 **자릿수 진술**이지 교정된 수치가 아니다.
> D3 가 끝나면 D1 을 갱신된 h 로 다시 돌리는 것이 이상적이다(12솔브라 싸다).

`splash = 250 W/m²K` 는 두 세트에서 동일하고, 보어→GAP_S / 로터OD→GAP_R 의 `h = 1e4` 는
**수치적 장치**(실제 갭 저항은 GAP_S–GAP_R 사이의 COMBIN14)이므로 h세트에 속하지 않고 스윕 대상도 아니다.
**절대 바꾸지 말 것.**

### 5-5. 계획서 운전점의 절대온도는 비물리적이다 — 그게 결론이다

16 krpm / 460 A 총 동손은 **87 kW** 로, 검증된 하이브리드 런(3.35 kW, 권선 152.2 °C)의 **26배**다.
따라서 권선 최대온도가 수백~수천 °C 로 나온다. **버그가 아니라 "이 점은 연속운전이 불가능하다"는 발견이다.**

대처는 세 가지이고 킷이 이미 다 한다:

1. **정규화 K/kW 민감도**를 절대온도와 함께 항상 낸다 (`influence_coeffs.K_per_kW`).
   이 영향계수 자체가 논문급 결과다(부품별 K/kW 감도표).
2. 그림 y축을 자동으로 `log` 로 바꾼다 (`--yscale clip --clip-hi 300` 으로 선형 클립 버전도 가능).
3. `I_cont` 에 `status` 를 붙여 격자 밖 값을 정직하게 표시한다
   (`ok` / `extrap_low` / `extrap_high` / `non_monotonic`).
   `sph` + 16 krpm 처럼 **전류 0 A 에서도 이미 한계 초과**인 셀은 `I_cont = 0 A` 와 함께
   "이 속도는 연속운전 자체가 불가능하다"는 문장을 로그에 찍는다.

철손·자석손 한계도 JSON `_loss_model_caveat` 에 명시된다: 계획서 §1 의 속도전용 규칙
(`fe_s = 1856·(n/15000)^1.5`, `fe_r = 74·(n/15000)^1.5`, `pm = 3385·0.17·(n/15000)^2`)은 **전류 의존이 없다.**
계획서 §2 의 R1 값과 비교하면 16 krpm/460 A 에서 `fe_s` 약 22 % 낮고 `pm` 약 53 % 낮다.
그 점에서는 철+자석이 총발열의 ~3 % 라 T_w 영향은 작지만, 16 krpm/115 A 에서는 ~32 % 라
그 자리의 I_cont 가 오차를 물려받는다. **동손(cu_slot/cu_end/ac_slot)은 JEET 맵에서 직독하므로 이 가정이 없다.**

> 참고: 계획서 §2 의 54,730 W / 15,204 W 는 **이 맵에 존재하지 않는다**(±2 % 스캔 결과 0건).
> Thesis_SKKU 의 R1 파이프라인 값이다. **여기서 찾지 말 것.**

### 5-6. `ansys.dpf.core` 는 아마 없다 — 그리고 킷은 필요로 하지 않는다

레포 전체에 등장 횟수 **0회**이고 moa venv 인벤토리(HANDOFF §9)에도 없다.
킷은 `ansys.mapdl.core` (확실히 있음)와 `ansys.mapdl.reader` (`thermal_viz.py:60` 이 쓰므로 있음)만 쓴다.
DPF 는 `d6_c67_stress.py` 의 **리더 프로브 안 `try/except ImportError`** 에서만 언급되고,
없으면 `ansys.mapdl.reader` 로 자동 전환하며 무엇을 찾았는지 `_source.probe` 에 기록한다.
**preflight 가 `import.ansys.dpf.core` 를 `INFO 없음(정상)` 으로 찍는 것이 기대 동작이다.**

### 5-7. 기타 두 가지

* **죽은 하드코딩 경로**: `04_mapdl_thermal.py:8` 의 scratchpad GUID 경로와
  `04:10-11` / `10_mapdl_dashboard_viz.py:7` 의 `D:\KDH\NvidiaNemo\eMach\...` 는 **더 이상 존재하지 않는다.**
  킷은 이것을 하나도 물려받지 않았다 — 모든 외부경로가 CLI 인자다. 승격 후에도 그대로 두라.
* **`freeflow/data/e10_losses.json` 을 읽지 말 것.** `_summary_W` 가 전부 0 이라
  `04:27` 의 Prius 폴백(3350/585/65/24 W)을 조용히 발동시킨다. 기존 결과의
  `_loss_source: "Prius-estimate"` 가 바로 그 버그다. 킷은 JEET 맵만 읽는다.

---

## 6. 보고 규약 (계획서 §3 · `plans/README.md`)

1. **결과 위치**: `mlxperPJT/thermal/thesis_out/`
   **JSON + PNG ≤ 300 KB.** GIF·대용량은 GitHub Release(`thermal-e10-YYYYMMDD`) 또는 moa 로컬 디스크.
2. **모든 결과 JSON 에 `_loss_source` · `_htc` · `_soltype` 이 반드시 들어간다** — "손실 출처 불명" 재발 방지.
   킷이 자동으로 넣는다. 값은 다음과 같아야 한다:

   | 산출물 | `_soltype` | `_loss_source` |
   |---|---|---|
   | D1 `e10_cont_rating.json` | `steady` | `JEET_ACLoss_Ref_Map_Summary.json phase36` |
   | D2 `e10_ac_turnwise_hotspot.json` | `steady` | `... phase36 FullFEA -- fea_per_turn_raw ...` |
   | D3 `htc_backout_horizontal.json` | `transient+<실제 도달시간>s` | (유동해석) |
   | D6 `c67_stress.json` | `static` | `n/a (structural, centrifugal body load only)` |
3. **비교 규약**: steady 끼리, transient 끼리만 비교한다 (`README_icepak_e10 §4`).
4. **완료 보고**: `mlxperPJT/thermal/HANDOFF_<날짜>.md` 에 **"D1 완료: 파일 경로·핵심 수치 3줄"** 을 덧붙인다.
   현재 최신은 `HANDOFF_20260722.md` 다. 날짜가 바뀌었으면 `HANDOFF_20260907.md` 를 새로 만들어도 되고
   기존 파일에 이어 붙여도 된다 — **`plans/` 는 절대 고치지 않는다**는 것만 지키면 된다.

   예시:

   ```markdown
   ## D1 완료 (2026-09-07)
   - 파일: mlxperPJT/thermal/thesis_out/e10_cont_rating.json,
           cont_rating_Tw_vs_I.png, cont_rating_Icont_vs_n.png
   - 방법: 정상해석(ANTYPE,STATIC) + 중첩. 단위솔브 10 + 검증솔브 2 = 12솔브,
           중첩검증 최대오차 <값> K (허용 0.05 K) PASS. 64엔트리 전부 폐형 재구성.
   - 핵심: I_cont(base/AC) = <..>/<..>/<..>/<..> A @ 2/4/8/16 krpm.
           16 krpm 은 magnet 한계·status=extrap_low → 해당 속도 연속운전 불가가 결론.
   ```
5. 학위논문 세션이 `Thesis_SKKU/Assets/Data/thermal/pull_from_emach.py` 로
   `origin/freeflow-e10-model:mlxperPJT/thermal/thesis_out/*` 를 당겨 간다.
   **따라서 push 가 실제로 올라갔는지 확인하는 것이 §7 이다.**

### 커밋 예시

```powershell
git -C $REPO add mlxperPJT/thermal/thesis_out/ `
                 mlxperPJT/thermal/freeflow/scripts/ `
                 mlxperPJT/thermal/HANDOFF_20260907.md `
                 .gitignore
git -C $REPO ls-files mlxperPJT/thermal/thesis_out/     # PNG 가 실제로 스테이징됐는지 확인
git -C $REPO commit -m "D1: e10 continuous rating (steady, superposition) + kit promotion"
git -C $REPO push
```

---

## 7. push 검증 — `git status` 의 ahead/behind 는 거짓말을 한다

HANDOFF §9: 백그라운드 push 가 **조용히 실패**한 적이 있다. `git status` 는 로컬 remote-tracking ref 만
보므로 이걸 잡지 못한다. **원격에 직접 물어봐야 한다.**

```powershell
$L = (git -C $REPO rev-parse HEAD).Trim()
$R = ((git -C $REPO ls-remote origin refs/heads/freeflow-e10-model) -split "`t")[0].Trim()
if ($L -eq $R) { "PUSH-OK    $L" } else { "PUSH-STALE local=$L remote=$R" }
```

`PUSH-STALE` 이면 다시 push 하고 다시 확인한다. `PUSH-OK` 가 뜬 뒤에야 완료 보고를 남긴다.

한 줄 버전 (PowerShell 5.1 에는 삼항연산자·`&&`·`||` 가 없으므로 `;` 와 `if` 를 쓴다):

```powershell
$L=(git -C $REPO rev-parse HEAD).Trim(); $R=((git -C $REPO ls-remote origin refs/heads/freeflow-e10-model) -split "`t")[0].Trim(); if($L -eq $R){"PUSH-OK $L"}else{"PUSH-STALE L=$L R=$R"}
```

---

## 8. 파일 인덱스

| 파일 | 한 줄 설명 |
|---|---|
| `README.md` | **이 문서.** moa 가 아침에 가장 먼저 읽는 실행 가이드 |
| `preflight.py` | 30초 환경 게이트 11항목(venv·import·폰트·**CDB**·맵·킷모듈·git·gitignore·디스크·thesis_out·AWP_ROOT). 종료 `0`=진행 / `1`=FAIL |
| `jeet_map_loader.py` | JEET Ref 맵(240 레코드) 리더. **stdlib only, numpy 도 안 씀.** 부동소수 허용오차 매칭 필수(맵에 `115.07499999999999` 로 저장), 격자 밖 셀은 근사하지 않고 `MapCellMissing` 을 던진다. `--self-test` / `--table` |
| `icont.py` | I_cont 순수 수학 — 중첩 재구성, 이분법 근찾기, 계획서식 4점 브래킷 보간(**I² 선형**), `status` 어휘. **stdlib only, side-effect 없음.** `--self-test` |
| `thesis_style.py` | 논문 그림 규약: Malgun Gothic + `unicode_minus=False`, 케이스 색(DC `#9C9C9C` / AC `#0B3D91` / AC+ `#E03131`, 흑백 휘도 사다리 확보), h세트는 선종류(base 실선 / sph 파선)로만 구분, `savefig_guarded()` 가 **300 KB 를 보장**(dpi 사다리 → 팔레트 256 양자화), `check_label()` 이 U+2212 를 막는다. `--self-test` |
| `d1_cont_rating.py` | **D1 러너.** 정상해석 + 오일회로. 기본 `--mode super`(단위솔브 10 + 검증솔브 2), `--mode brute` 는 계획서 문자 그대로 64솔브. `--dry-run` 은 Ansys 없이 전 경로 검증. → `e10_cont_rating.json` |
| `d2_ac_turnwise.py` | **D2 러너.** mat 3 을 **반경 밴딩으로 실측**해 턴 인덱스를 복원하고(밴드 하드코딩 없음), 부분체적 비닝 + 요소별 `BFE,HGEN` 매크로로 균일 vs 턴별을 주입. 4솔브. → `e10_ac_turnwise_hotspot.json` + zcut PNG 2장 |
| `d6_c67_stress.py` | **D6 러너.** C67 회전자 원심 응력 추출(리더 자동 프로브 dpf→mapdl_reader→mapdl, 단위계 런타임 자동 판별, 회전 원환 해석해 게이트, ω² 또는 재솔브 스윕). → `c67_stress.json` + PNG 3장 |
| `d3_htc_backout.py` | **D3 후처리.** SPH 근벽 온도구배로 h 역산(원본 스크립트 소실 → 저장값에서 역설계, `--verify-legacy` 28검사로 재현 확인 완료). `--sph` HDF5 직독 또는 `--particles` CSV/NPZ. → `htc_backout_horizontal.json` |
| `d3_freeflow_gravity_fix.py` | **D3 전처리.** FreeFlow 중력을 축방향(-Z)→반경방향(-Y)으로 수정. **API 이름을 모르므로 먼저 probe**(`D3_PROBE_ONLY=1`), setter 성공 후 **읽기검증**, 벽 BC·Fluid Inlet 70 °C 재적용·읽기검증. **솔브는 시작하지 않고** 새 파일로만 저장. `FreeFlow.exe --headless --script` 로 실행 |
| `make_thesis_figs.py` | thesis_out JSON → 논문 PNG 4장(`cont_rating_Tw_vs_I` / `cont_rating_Icont_vs_n` / `ac_turnwise_hotspot` / `c67_stress_sweep`). **Ansys 전혀 불필요.** JSON 이 없으면 그 그림만 `SKIP` 하고 계속 — D1 뒤에 한 번, D2 뒤에 또 한 번 돌려도 된다 |
| `__pycache__/` | 파이썬 캐시. `.gitignore:120 __pycache__/` 에 이미 걸리므로 신경 쓸 것 없다. 승격 시 복사하지 말 것 |

### 킷 전체가 지키는 불변 규칙 (승격 후에도 유지할 것)

* **python 3.10 문법만** — `match` 없음, `X | Y` 어노테이션 없음, 3.11+ stdlib 없음.
  (이 PC 에서는 3.14 로 테스트했지만 `ast.parse(feature_version=(3,10))` 로 별도 검증했다.)
* **같은 디렉터리 안에서만 import** — 레포 상대 `sys.path` 조작 없음. 유일한 예외가 D2 의
  `from thermal_viz import ThermalViz` 이고, 그건 `PYTHONPATH` 로 푼다(§3-2).
* **`ansys.dpf.core` 를 요구하지 않는다.**
* **모든 외부경로가 CLI 인자**이고 기본값은 `__file__` 에서 유도하거나 moa 로컬 경로다.
* **`mapdl.ignore_errors = True` 를 쓰지 않는다** — `MapdlRuntimeError` 를 잡고 assert 한다.
* **모든 SOLVE 직전에 `mapdl.allsel("ALL")`** — SOLVE 는 현재 선택된 요소만 풀고 POST1 은 선택을 남긴다.
* 매 솔브 뒤 **최대원리 자가검사**: 양의 발열 + OIL 70 °C 단일 Dirichlet → 모든 절점온도 ≥ 69.99 °C.
  깨지면 원인 3가지(떠 있는 요소섬 / SOLVE 시 부분선택 / stale 세션)를 지목하고, 복구옵션 `--ground-guard`
  (외부 절점에 h=1e-3 W/m²K, 상대섭동 ~4e-6)를 안내한다.
* stdout 과 `--log` 파일에 **동시 기록**.
