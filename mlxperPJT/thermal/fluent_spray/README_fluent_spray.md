# Fluent 오일스프레이 CHT (엔드턴 오일 분사냉각)

FreeFlow가 못 하는 **고체 손실주입+전도까지 한 솔버 CHT**를, Fluent의 DPM 스프레이 +
Eulerian Wall Film 로 구현하는 경로. e10(FreeFlow 모터) 엔드턴 오일 스프레이 냉각 대상.

## 결론: Fluent는 오일스프레이 CHT가 **된다** (검증)
pyfluent 0.40 + Fluent v261, 실제 Prius CHT 메시에서 API 실행 검증:

| 요소 | Fluent 지원 | 검증 |
|---|---|---|
| 에너지/켤레열전달(CHT) | ✅ solid zone 전도 + fluid | Prius 케이스 energy ON ✅ |
| 고체 손실주입(발열원) | ✅ `cell_zone.sources.enable/terms` | 경로 확인 ✅ |
| 오일(ATF) 재료 | ✅ | `materials.fluid["atf-oil"]` 생성 ✅ |
| **DPM 스프레이(방울분사)** | ✅ solid-cone/atomizer | injection 객체 생성 ✅ |
| **Eulerian Wall Film(막)** | ✅ (`dpm_film`, `sg_film`) | 모델 존재 ✅ |
| 2-way 입자↔유체 열/운동량 | ✅ `discrete_phase.physical_models` | 경로 확인 ✅ |
| System Coupling 참가자 | ✅ `models.system_coupling` | 확인 ✅ |

→ **FreeFlow(고체 손실주입 불가) 대비 Fluent의 강점**: 구리손·철손을 고체존에 직접
넣고(발열원), DPM 스프레이+월필름으로 엔드턴을 냉각하며, 계면 CHT까지 한 솔버서 완결.

## 물리 모델 (오일스프레이 냉각)
1. **DPM(이산상) 분사**: 노즐/스프레이바에서 오일 방울을 라그랑지안 입자로 분사
   (solid-cone: 위치·방향·콘각·유량·입경·온도·속도).
2. **Eulerian Wall Film(EWF)**: 방울이 엔드턴 벽 충돌 → 막 형성(두께·속도·온도),
   막이 벽 따라 흐르며 열교환(스프레이 냉각의 핵심).
3. **CHT**: 고체존(코일/철심, 손실=체적발열)↔유체(공기)↔막, 계면 coupled walls.

## 레시피 (`oil_spray_cht_recipe.py`)
검증된 pyfluent 0.40 경로:
- `setup.models.energy.enabled=True`
- `setup.materials.fluid["atf-oil"]` (ρ825/cp2000/k0.135/μ0.02)
- `setup.models.discrete_phase.physical_models.two_way_coupling` (또는 TUI 폴백)
- `discrete_phase.injections["oil_spray"]` (+ TUI `create-injection` 로 콘 파라미터)
- `define models eulerian-wall-film yes` (TUI)
- `cell_zone_conditions.solid[z].sources.enable/terms` (발열원)

## ⚠️ 메시 생성 (헤드리스 파일변환 6종 실패 → GUI 권장)
스프레이엔 **공기 캐비티(유체존) + 엔드턴 노출면(고체)** 볼륨메시 필요. e10 스케일
스프레이 챔버 형상을 **gmsh로 구축 완료**(`geometry/build_spray_chamber.py`: 공기
캐비티 실린더 + 엔드턴 링 고체, 2볼륨 컨포멀, 명명경계 nozzle/drain/housing/
winding_surf). 이 gmsh 메시를 **Fluent로 넣는 파일변환을 6가지 시도 → 전부 실패**:

| 경로 | 결과 |
|---|---|
| gmsh→meshio(ansys)→Fluent .msh (binary/ASCII) | Fluent 리더 거부 ("Error reading msh") |
| gmsh→CGNS→Fluent `read_mesh` | **Fluent 서버 크래시** (비호환 CGNS) |
| gmsh→meshio→Nastran | meshio export 실패(AssertionError) |
| gmsh→meshio→Abaqus(.inp)→Fluent import | import TUI 오류 |
| Fluent Meshing STL TUI (`/file/import/stl-cad`) | 메뉴 경로 부재 |
| Fluent Meshing **watertight 워크플로우 API** | 초기화·태스크나열 OK, Import Geometry의
  datamodel 인자("File Names")를 헤드리스에서 못 넘김 |

→ **결론: 이 메시 단계는 실무 표준대로 Fluent Meshing GUI(대화형)에서 수행 권장.**
헤드리스 pyfluent 파일변환은 이 환경에서 신뢰성 있게 안 됨(포맷 브릿지 한계).

### GUI로 메시 완성하는 법 (준비된 자산으로 즉시 가능)
1. Fluent Meshing 실행 → Watertight Geometry Workflow.
2. **Import Geometry**: `geometry/spray_chamber_multisolid.stl` (4 named solid:
   nozzle/drain/housing/winding_surf 자동 인식) 또는 `geometry/*.stl` 4개 개별 import.
3. Generate Surface Mesh → Describe Geometry(**fluid+solid**) → Create/Update Regions
   (유체=공기캐비티, 고체=엔드턴 링 자동 검출) → Generate Volume Mesh.
4. Switch to Solution → `oil_spray_cht_recipe.py` 적용(발열원·오일·DPM·EWF·CHT) → 솔브.

(참고 스크립트: `_fluent_meshing_watertight.py` — 워크플로우 태스크 순서. Import
Geometry 인자만 GUI/버전맞는 datamodel로 넘기면 이후 자동화 가능.)

## e10 적용 계획 (메시 확보 시)
1. e10 형상(스테이터+권선 STL, 로터/자석/샤프트) + 엔드턴 주위 **공기 캐비티** 정의.
2. Fluent Meshing 볼륨메시(유체+고체존, 명명경계).
3. 손실: 구리 3350 / 철손(스테이터585·로터65) / 자석24 W → 고체존 발열원(W/m³).
4. DPM 오일 스프레이(엔드턴 위 노즐, 70°C, ~0.05 kg/s) + EWF.
5. 정상/비정상 CHT 솔브 → 엔드턴·코일 온도. MAPDL 하이브리드(winding 152°C)와 대조.

## 비교 (오일냉각 3경로)
| 방법 | 자유표면 처닝 | 스프레이→막→냉각 | 고체 CHT(손실) |
|---|---|---|---|
| FreeFlow(SPH/GPU) | ★ | 제한적 | ✗(외부 SC 필요) |
| Fluent VOF | 격자(비쌈) | △ | ✅ |
| **Fluent DPM+EWF** | ✗ | ★ | ✅ |
| MAPDL 하이브리드(회로) | — | 회로근사 | ✅(FEM+회로) |
