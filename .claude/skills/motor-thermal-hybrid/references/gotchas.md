# 함정 전체 목록 (재발견 비용이 컸던 것)

출처: eMach `mlxperPJT/thermal/` HANDOFF_20260721·0722·0907, README_prius/freeflow/icepak/icepak_e10/
fluent_spray, plans/README_PC1_SETUP·D4_CONTINUATION. 증상 → 원인 → 처방 순.

## MAPDL / pymapdl

| 증상 | 원인 | 처방 |
|---|---|---|
| 대류 경계가 아무 효과 없음 | `SURF152` 기본 KEYOPT | `KEYOPT(8)=2` 필수 (큐브 테스트: extra node 해석해 40.00°C) |
| "Real constant referenced by types 3 and 2" | `ESURF` 가 현재 REAL을 SURF152에 묶음 | ESURF 전 전용 `mapdl.r(n)`/`mapdl.real(n)` |
| 정상해석 다중 하중단계에서 8.6e10 K 발산 / 최대원리 위반 62°C | 2번째 하중단계에서 Dirichlet 상실, ANTYPE 재발행 | `ANTYPE` 첫 회만, `D,OIL,TEMP` 매 단계 재지정 |
| 에너지수지 99.91% 오탐 | `OUTRES,ALL,NONE` 이 RSOL 삭제 | 반력 필요한 항목 OUTRES 유지 |
| 요소 0개인데 노드는 로드됨 | CDB EBLOCK tet10 한 줄 기록 | `(19i10)` 11헤더+8노드 / 2노드 줄바꿈 (`03b` writer) |
| 연결 즉시 깨진 상태(요소 0) | 실패한 이전 run 인스턴스에 attach | MAPDL 솔버 프로세스 완전 종료 + 새 run_location |
| launch 대신 attach 시도 | `PYMAPDL_START_INSTANCE`/`PYMAPDL_PORT` 잔존 | 환경변수 제거 |
| PC1에서 launch 실패 | `ansys.tools.path` 가 v261(MAPDL 없음) 우선 선택 | `change_default_mapdl_path(v252)` 또는 `PYMAPDL_MAPDL_EXEC` |
| 병렬 D1 세션 충돌 | 포트 공유 | 잡마다 별도 포트 (커밋 5e136d1) |
| 이방성 코일 | — | `MP,KZZ=250`(축/구리), `KXX=KYY=2.5`(횡/절연). 슬롯 도선이 global-z면 ESYS 불필요 |
| 코일↔코어 `CONTA174` 실패 | CAD 라이너 갭 0.85~1.4mm | SURF152 정션 노드(각도16×z4 bin, 2×TCC) |
| 코일 엔드 | FEM에서 절단 | 손실은 CEND 노드에 `mapdl.f` HEAT, 엔드/슬롯 체적비 0.449(Prius) |
| 곡면 중간절점 | sagitta | 허용오차 `1.6*ESIZE²/(8R)` |
| 결함 절점 2개 | e10 v2 메시 고정 결함 id 67651, 99303(권선) | 게이트는 개수·회로건전성·평균오염으로 판정, `_undershoot` 기록 |
| 언더슈트 게이트가 하중만 키워도 걸림 | 절대 K 임계 | 장 범위 대비 상대량으로 |
| 64 런 스윕 | 모델이 완전 선형(상수 k·h·G, Dirichlet 1개) | **중첩** `T=70+Σ(P_s·G_s)` — 단위솔브 5회+검증 2회 (`--mode super`) |
| C67 재솔브 응력 4배 | `ds.dat` 에 회전속도 이미 있음 + OMEGA 덧씌움 | rst 사용 또는 OMEGA 제거. 스윕은 ω² 스케일링(선형탄성 한정) |

## 메시 / 지오메트리

- `~SATIN` 설치 결함 → **STEP→gmsh(OCC)→CDB**: importShapes → fragment(컨포멀) → setPeriodic → tet10 → ×8 회전 → NBLOCK/EBLOCK.
- STL→tet10 "Zero volume" 반복: 부품결합 노드병합이 병합 前 퇴화검사 무력화 → 병합 **後** 코너부호체적 필터(2%)+중간노드 직선화.
- FreeFlow `Rotating.stl` 은 자석포켓 non-manifold → 로터·자석·샤프트는 **Maxwell 2D에서 재구축**(02c→03b).
- 메시 단위 = 미터. 샤프트 축방향 돌출 → viz `z_trim=0.045`.
- e10 좌표계: Stator.stl z[-0.207,-0.058] = MAPDL `Z_ST0/Z_ST1` 과 일치. 회전축 Z.

## Maxwell / AEDT / Motor-CAD

- Maxwell 3D "Classic Parallel Recovery"(`CPRIsEnabled`) 베타 옵션 → **GUI에서 해제**만 가능.
- Prius Maxwell 19R2→v261 pyaedt 마이그레이션 실패 → 24R2 재저장.
- `Maxwell3d(...)` 가 동일명 다타입 프로젝트에서 `__init__ should return None, not bool` → `get_pyaedt_app(project, design)`.
- 부품별 철손 추출 3회 실패(`CoreLoss(obj)` 미지원) → 스테이터/로터 **90/10 추정**(한계로 표기).
- Motor-CAD 헤드리스: thermal `Loss_[...]`/injection 이 **0 반환**해도 PASS 처럼 보임 → Magnetics 출력
  `StatorIronLoss_Total_Adj`, `RotorIronLoss_Total_Adj`, `MagnetLoss_Adj`, `ConductorLoss` 를 읽고,
  양의 전류에서 동손 0이면 거부. 파라미터명은 `ActiveXParametersMotorCADv261.txt`.
- Motor-CAD 예약실행: schtasks 경로 공백(`Files\ANSYS`)·`\v261` 이스케이프 오염 → `New-ScheduledTaskAction`
  구조화 인자 + interactive principal. **사용자가 열어 둔 Motor-CAD 모델에 attach 금지**, PID 는 스냅샷.

## Icepak (pyaedt `Icepak`)

- Network 경계(`AssignNetworkBoundary`)는 전도-only에서 "Failed to generate solver input file" → **대류벽**
  `assign_stationary_wall_with_htc(faces, htc, ref_temperature)`.
- 대류벽이 안 먹음 / 5000 K 발산: 유체 Region 이 HTC 벽을 단락 → **Region 제거**(냉각면을 외부면으로).
- 권선 폭주(2000~3000°C): imported 다물체 비컨포멀 → 권선을 **슬롯밴드−스테이터 네이티브 카브 균질체**(k5).
  discrete 구리바(Maxwell import)는 카브해도 비컨포멀 → 폭주(2376°C, 결과 무의미).
- discrete 144바 엔드턴 메시 40분+ 정체 → 엔드턴 z±75 클립.
- 디자인 삭제 후 동일명 재생성 → `modeler is None` → 타임스탬프 유니크명.
- 필드 추출: extremum `Temp`/`Temperature` 둘 다 시도, 코일 리스트 1콜은 None → 바 샘플(~20).
  헤드리스 추출 8종 실패한 경우 GUI Fields Summary (`freeflow/data/ICEPAK_GUI_temp_extraction_guide.md`).
- Icepak 중력 `Gravity Vector Axis='Z'` 는 미확인(FreeFlow 와 별개 모델).

## FreeFlow (Rocky SPH, `FreeFlow.exe --headless --script`)

- 온도 0 K: 벽 기본 `adiabatic`, **Fluid Inlet 온도 0°C** → `RAFluidInlet.SetTemperature(70.0)`.
- 결과셋 all-or-nothing: cp/k/ρ/벽BC/InletT 변경 시 전체 무효 → `DeleteResults()` 후 t=0. resume 불가.
- 초기 충전 오일 온도 설정 API 미발견 → inlet 온도로만 제어.
- 단독 CHT 불가: 벽=표면 삼각망, 열경계 3종(adiabatic/prescribed/cfd_coupled), 열원 주입 없음.
  2-way = FreeFlow↔System Coupling↔MAPDL.
- 중력은 이미 올바름: (-9.81,0,0) 반경 -X, 회전축 Z (HANDOFF_0907 §1 — 0722 §10-4 정정).
- 8 s 유동 솔브 = GPU ~5.1 h (28.8만 입자). 1-way 열 검증은 1.63 s 에 벽시계 2716 s.

## Fluent / pyfluent 0.40

- `.cas.h5/.dat.h5` 는 h5py 로 `SV_T` + cell zone range 직접 읽으면 **라이선스 없이** 온도 추출.
- 오일스프레이 메시: 헤드리스 변환 6종 실패(meshio .msh 거부, CGNS 서버 크래시, Nastran/Abaqus, Meshing TUI,
  watertight Import Geometry 인자) → **Fluent Meshing GUI**.

## 시각화 (pyvista)

- 볼륨 clip → VTK 크래시: 외피 반쪽 clip + 단면 slice 조합.
- `extract_cells` 이중 적용 → `vtkOriginalPointIds` 붕괴로 온도 전부 최댓값 → 원본 인덱스를 `point_data['gid']` 로 운반.
- 축방향 x=0 절단은 코일이 코어를 가림 → z=0 정단면.
- 등온 자석(≈로터) → `_add_mat_outlines` 재료 경계선 오버레이.
- viz 스크립트 10분+ → detach 실행(`run_detached.ps1`).

## git / 동기화 / 원격

- moa 는 GitHub DNS 불가 → `git bundle create` 로 전달, 게이트웨이에서 fetch.
- (7월 당시) 백그라운드 push "완료" 표시 후 원격 미반영 → 동기 `git push --verbose` 재시도 + `ls-remote` 1회 확인.
- `git check-ignore -v` 는 negation 매칭도 exit 0 → 무시 여부 판정에 쓰지 말 것.
- 원격 셸이 PowerShell 5.1: `&&`, `&` 연쇄 불가. ssh 인자는 작은따옴표 PowerShell 블록으로.
- 한글 출력 cp949 깨짐 → 파이썬은 `-X utf8`, 결과는 파일로 받아 읽기.
