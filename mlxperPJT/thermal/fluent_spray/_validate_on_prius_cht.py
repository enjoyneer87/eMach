# -*- coding: utf-8 -*-
"""Fluent 오일스프레이 CHT 레시피 검증: 실제 Prius CHT 메시(유효)에 pyfluent로
DPM(오일 방울 분사) + Eulerian Wall Film + 오일재료 + 발열원 API를 단계별로 실행/검증.
각 단계 성공여부를 로그로 남겨 '작동하는 레시피' 확보. (물리적 스프레이는 e10 캐비티
메시 필요 - 여기선 API 워크플로우 검증이 목적.)"""
import os, traceback
LOG = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\flu_spray_recipe.txt"
def W(*a):
    with open(LOG, "a", encoding="utf-8") as f: f.write(" ".join(str(x) for x in a) + "\n")
open(LOG, "w").close()
def step(name, fn):
    try:
        r = fn(); W(f"[OK] {name}", "" if r is None else f"-> {r}"); return r
    except Exception as e:
        W(f"[FAIL] {name}: {repr(e)[:200]}"); return None
try:
    import ansys.fluent.core as pf
    solver = pf.launch_fluent(mode="solver", precision="double", processor_count=4,
                              ui_mode="no_gui_or_graphics", start_timeout=300)
    W("launched", pf.__version__)
    CASE = r"D:\KDH\simVary\Ansys_Thermal\Prius_work\PriusMotor_250A.cas.h5"
    solver.settings.file.read_case(file_name=CASE)
    W("case read")
    s = solver.settings
    tui = solver.scheme_eval.scheme_eval  # scheme fallback

    # 1) 에너지 ON (CHT 필수)
    step("energy on", lambda: setattr(s.setup.models.energy, "enabled", True))
    W("  energy:", s.setup.models.energy.enabled())

    # 2) 오일(ATF) 재료 생성/설정
    def mk_oil():
        s.setup.materials.fluid["atf-oil"] = {}
        o = s.setup.materials.fluid["atf-oil"]
        o.density.value = 825.0
        o.specific_heat.value = 2000.0
        o.thermal_conductivity.value = 0.135
        o.viscosity.value = 0.02
        return "atf-oil created"
    step("oil material", mk_oil)

    # 3) DPM(이산상) 활성화 - 비정상 추적 + 2-way 열/운동량 커플
    def dpm_on():
        dp = s.setup.models.discrete_phase
        dp.interaction.coupled_calculations = True             # 2-way(입자<->유체)
        dp.interaction.update_dpm_sources_every_flow_iteration = True
        dp.unsteady_tracking.enabled = True
        return "DPM interaction/unsteady enabled"
    step("dpm enable", dpm_on)

    # 4) 오일 분사(injection) 정의 - 콘 스프레이 (엔드턴 위 노즐)
    def mk_inj():
        inj = s.setup.models.discrete_phase.injections
        inj["oil_spray"] = {}
        j = inj["oil_spray"]
        # 콘/솔리드콘 스프레이: 위치, 방향(-z), 유량, 온도, 입경, 속도
        j.injection_type = "solid-cone"
        j.material = "atf-oil"
        j.temperature = 343.15          # 70C 오일
        j.total_flow_rate = 0.05        # kg/s (스프레이바)
        j.diameter = 2.0e-4             # 200um 방울
        return "oil_spray injection defined"
    step("injection", mk_inj)

    # 5) Eulerian Wall Film(EWF) - 방울이 벽에 막 형성(엔드턴 냉각)
    def ewf_on():
        # pyfluent settings 경로가 버전별 상이 -> TUI로 활성화
        tui('(ti-menu-load-string "define models eulerian-wall-film yes")')
        return "EWF via TUI attempted"
    step("eulerian wall film", ewf_on)

    # 6) 고체 발열원(손실) - 예: 코일(phase) 존에 구리손 밀도 (W/m3)
    def heat_src():
        cz = s.setup.cell_zone_conditions.solid
        # phase(코일)에 체적발열 (e10 구리손 3350W / 코일체적 ~ 예시밀도)
        cz["phase"].source_terms = {"energy": [{"option": "value", "value": 3.7e6}]}
        return "coil heat source set (3.7e6 W/m3)"
    step("solid heat source", heat_src)

    # 상태 요약
    W("=== 요약 ===")
    W("energy:", s.setup.models.energy.enabled())
    try: W("injections:", list(s.setup.models.discrete_phase.injections.keys()))
    except Exception as e: W("inj list fail:", repr(e)[:120])
    try: W("materials fluid:", list(s.setup.materials.fluid.keys()))
    except Exception as e: W("mat list fail:", repr(e)[:120])

    solver.exit()
    W("DONE-OK")
except Exception:
    W("EXC:", traceback.format_exc())
os._exit(0)
