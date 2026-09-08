# PC1 에서 MAPDL 열해석 킷 이어 돌리기 — 세팅 기록 (2026-09-08)

> 작성: 학위논문 세션(PC1, `E:\KDH\Overleaf\Thesis_SKKU`). `plans/**` 는 학위논문 세션 관할이라 여기에 둔다.
> 목적: moa(격리 PC)에서 돌던 `PLAN_20260906_assets` 킷(D1/D2/D3/D6)을 **PC1 에서도 그대로** 돌릴 수 있게 한다.

## 1. 준비된 것 (전부 확인 완료)

| 항목 | PC1 상태 |
|---|---|
| 워킹트리 | `D:\KangDH\eMach-thermal` = `freeflow-e10-model` @ `612d89b` (clean). 사용자 작업 브랜치 `devVeriACLoss`(`D:\KangDH\EveryMotor\eMach`)와 분리. |
| MAPDL | **v252** (`C:\Program Files\ANSYS Inc\v252\ansys\bin\winx64\ANSYS252.exe`). **v261 에는 MAPDL 이 없다**(AnsysEM·Motor-CAD 만). |
| 기본 경로 고정 | `ansys.tools.path.change_default_mapdl_path(v252)` 로 설정 파일에 저장 → `launch_mapdl()` 을 **인자·환경변수 없이** 호출해도 v252 가 뜬다(23 s). 킷 스크립트는 `exec_file` 을 안 넘기므로 이 고정이 없으면 v261 을 잡고 실패한다. |
| 파이썬 | `C:\Users\user\.ansys_python_venvs\pyMotorEnv_310` — `ansys-mapdl-core 0.73.2`, `ansys-mapdl-reader 0.56.0`(moa 와 동일 판), `ansys-tools-path`, `pyvista 0.47.0` |
| 라이선스 | SOLID87·SURF152 정의까지 확인(열해석 요소 OK) |
| preflight | **PASS 24 · WARN 1 · FAIL 1** — WARN 은 `matplotlib.cm.get_cmap`(회로 오버레이 그림만 영향), FAIL 은 아래 CDB |
| JEET 손실 맵 | `mlxperPJT/JEET/map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary.json` 240 레코드 OK |
| 디스크 | D: 여유 357 GiB |

## 2. 유일한 블로커 — 메시 CDB

`ff_e10_mesh_v2.cdb` (**약 260 MB, git 밖**). moa 의 `D:\KDH\simVary\Ansys_Thermal\` 에만 있다.
PC1 에는 STL 원본(`...\FreeFlowProject\Geometry\*.stl`)도 없어 `03_stl_to_cdb.py` 로 재생성할 수 없다(AEDT + 수 시간).
로컬 D:/E:/J: 전수 검색·GDrive 검색 모두 없음(09-08).

**전달 방법 (하나 고르면 된다)**
1. `ssh iso` / `W:` 가 되는 PC 에서 moa 의 파일을 GDrive `내 드라이브/Thesis_SKKU_sync/inbox_pc1/` 에 넣는다 → PC1 은 `J:\내 드라이브\Thesis_SKKU_sync\inbox_pc1\` 에서 바로 읽는다.
2. moa 가 **git LFS** 로 브랜치에 추가한다(`git lfs track "*.cdb"`; PC1 은 git-lfs 3.0.2 있음. moa 쪽 LFS 설치 여부 확인 필요).
3. USB.

PC1 의 권장 위치: `D:\KangDH\Ansys_Thermal\ff_e10_mesh_v2.cdb` (아래 명령의 `--cdb` 가 이 경로).

## 3. CDB 가 오면 이 순서로 (킷 README §2~§4 와 같다)

```powershell
$PY   = "C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe"
$REPO = "D:\KangDH\eMach-thermal"
$KIT  = "$REPO\mlxperPJT\thermal\plans\PLAN_20260906_assets"
$OUT  = "$REPO\mlxperPJT\thermal\thesis_out"
$CDB  = "D:\KangDH\Ansys_Thermal\ff_e10_mesh_v2.cdb"

& $PY "$KIT\preflight.py" --repo $REPO --cdb $CDB --deep --json "$OUT\preflight_pc1.json" --log "$OUT\preflight_pc1.log"
& $PY "$KIT\d1_cont_rating.py" --repo $REPO --cdb $CDB --dry-run
& $PY "$KIT\d1_cont_rating.py" --repo $REPO --cdb $CDB --mode super --htc-set both --nproc 8
& $PY "$KIT\make_thesis_figs.py" --repo $REPO
```

* `--mode super`(중첩) 가 정본. 계획서 문자 그대로 64 솔브는 `--mode brute`.
* `--nproc`: PC1 은 36 논리코어. 8 로 올려도 되나 **HPC 라이선스 팩 유무**를 먼저 본다(없으면 4).
* 결과는 moa 와 같은 `thesis_out/` 에 떨어지므로 파일명이 겹친다 → PC1 에서 돌린 것은 `--out-name` 으로 접미어를 붙일 것(예 `_pc1`). 정본 판정은 학위논문 세션이 한다.
* 논문 레포로 당기기: `Thesis_SKKU/Assets/Data/thermal/pull_from_emach.py` (그림은 이름 접두어로 장 라우팅: `c67_` → 3장, 나머지 → 5장).

## 4. 왜 PC1 에서도 돌리나

- moa 는 격리 PC 라 세션 접근이 간헐적이다. **전류 의존 철손·자석손 맵**으로 D1 을 다시 풀어야 16 krpm 연속 정격을 인용할 수 있고(5장 각주), 그 재실행을 PC1 이 맡을 수 있다.
- 시스템 확장(인버터·전압 축)에서 슬롯 절연 두께가 바뀌면 열 모델의 슬롯 라이너 물성이 함께 바뀐다 — 그 감도 스윕도 PC1 몫.

## 5. 함정 메모

- `PYMAPDL_START_INSTANCE` / `PYMAPDL_PORT` 가 남아 있으면 `launch_mapdl` 이 기동 대신 attach 를 시도한다(킷 `d1_cont_rating.py:673`). PC1 에는 둘 다 없음(확인).
- `ansys.tools.path` 자동 탐색은 **v261 을 먼저 고른다**(MAPDL 없음). 위 설정 파일 고정이 그 문제를 막는다. 설정을 잃으면 `PYMAPDL_MAPDL_EXEC` 환경변수로 같은 효과를 낼 수 있다.
