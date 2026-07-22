# -*- coding: utf-8 -*-
"""Fluent 오일스프레이 CHT 레시피 (pyfluent 0.40, Fluent v261).

엔드턴 오일 스프레이 냉각을 Fluent 단독 CHT로 해석하는 셋업:
  고체존(코일/철심, 손실=체적발열) + 공기 캐비티(유체존) + DPM 오일방울 분사(스프레이)
  + Eulerian Wall Film(막) + 켤레열전달(coupled walls) → 벽온도.

★ 검증됨 (Prius CHT 메시에서 pyfluent API 실행 확인):
  energy ON, ATF 오일재료 생성, DPM injection 객체 생성, solid source(발열) 경로,
  Eulerian Wall Film(TUI). 아래 경로는 pyfluent 0.40에서 조사한 실제 child 구조 기반.

★ 메시 주의: 스프레이엔 '공기 캐비티(유체존) + 엔드턴 노출면'이 있는 메시가 필요.
  gmsh→meshio→Fluent(.msh)는 Fluent 리더가 거부(존/면포맷 불완전) → 실패 확인.
  → 캐비티 메시는 **Fluent Meshing**(watertight/wrap) 또는 ANSYS Meshing 으로 생성 권장.
  (Prius 기존 CHT 메시는 재킷냉각이라 스프레이 캐비티 없음.)

실행:  python oil_spray_cht_recipe.py <case_or_mesh.(cas.h5|msh.h5)>
"""
import os, sys, traceback


def build(case_path, out_dir):
    import ansys.fluent.core as pf
    solver = pf.launch_fluent(mode="solver", precision="double", processor_count=4,
                              ui_mode="no_gui_or_graphics", start_timeout=300)
    s = solver.settings
    tui = solver.scheme_eval.scheme_eval
    if case_path.endswith((".msh", ".msh.h5")):
        s.file.read_mesh(file_name=case_path)
    else:
        s.file.read_case(file_name=case_path)

    # 1) 에너지(CHT)
    s.setup.models.energy.enabled = True

    # 2) 오일(ATF) 재료
    s.setup.materials.fluid["atf-oil"] = {}
    o = s.setup.materials.fluid["atf-oil"]
    o.density.value = 825.0
    o.specific_heat.value = 2000.0
    o.thermal_conductivity.value = 0.135
    o.viscosity.value = 0.02

    # 3) DPM 활성화 + 2-way 커플(입자↔유체 열/운동량)
    dp = s.setup.models.discrete_phase
    #   coupling/heat-mass 교환은 physical_models 하위 (버전별 상이시 TUI 폴백)
    try:
        dp.physical_models.two_way_coupling.enabled = True
    except Exception:
        tui('(ti-menu-load-string "define models dpm interaction coupled-calculations yes")')
    try:
        dp.tracking.max_num_steps = 50000
    except Exception:
        pass

    # 4) 오일 분사(스프레이) — 엔드턴 위 노즐, 콘 스프레이
    inj = dp.injections
    inj["oil_spray"] = {}
    j = inj["oil_spray"]
    j.material = "atf-oil"
    #   injection_type/초기값은 initial_values 하위(위치·방향·유량·입경·온도·속도).
    #   콘 스프레이 값 형식은 GUI/TUI 로 1회 확정 후 아래 세팅(버전별 스키마 상이).
    #   TUI 폴백(가장 이식성 높음):
    tui('(ti-menu-load-string "define models dpm injections create-injection oil_spray '
        'no no solid-cone no no atf-oil no 0.06 0.06 0.08 0 0 -1 5 0.05 343.15 2e-4 45 0.5")')
    #   (위 인자: 위치xyz, 방향xyz, 속도, 유량kg/s, 온도K, 입경m, 콘각deg, 반경)

    # 5) Eulerian Wall Film — 엔드턴 벽에 막(스프레이 냉각 핵심)
    tui('(ti-menu-load-string "define models eulerian-wall-film yes")')
    #   막을 받는 벽(예: hot_wall/end-winding)에 film BC 지정은 boundary_conditions/wall

    # 6) 고체 발열원(손실) — 예: 코일 존에 구리손 밀도(W/m3)
    #    e10: 구리 3350W / 코일체적 ≈ 3.7e6 W/m3
    for zname, qdens in (("phase", 3.7e6),):   # 존명은 실제 케이스에 맞게
        try:
            z = s.setup.cell_zone_conditions.solid[zname]
            z.sources.enable = True
            z.sources.terms = {"energy": [{"value": qdens}]}
        except Exception as e:
            print("heat source", zname, "fail:", repr(e)[:120])

    # 7) 솔브(예: 정상 or 비정상 DPM). 여기선 초기화만.
    try:
        s.solution.initialization.hybrid_initialize()
    except Exception:
        pass
    os.makedirs(out_dir, exist_ok=True)
    s.file.write_case(file_name=os.path.join(out_dir, "oil_spray_cht_setup.cas.h5"))
    solver.exit()


if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else None
    out = os.path.join(os.path.dirname(__file__), "out")
    if not case:
        print("usage: python oil_spray_cht_recipe.py <case_or_mesh>")
        sys.exit(0)
    try:
        build(case, out); print("DONE")
    except Exception:
        traceback.print_exc()
    os._exit(0)
