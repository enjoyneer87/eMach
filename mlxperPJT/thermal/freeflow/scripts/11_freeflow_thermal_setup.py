# -*- coding: utf-8 -*-
"""FreeFlow 온도장 활성화: MAPDL 하이브리드 결과를 벽 온도경계(prescribed_temperature)로
주입하고, 기존 완료된 8s 유동해석을 소폭(EXT_S초) 확장해 커플드(1-way: solid->fluid)
검증 솔브. 원본 프로젝트는 보존(새 파일명으로 저장).

벽 매핑 근거 (MAPDL v2 하이브리드 회로/부품온도, ff_mapdl_hybrid_temps.json):
  Stator   (오일 스파이럴자켓 접촉면=스테이터OD)      -> JACKET 84.4C
  Winding  (엔드턴 오일스프레이 접촉면)                -> SPRAY  91.9C
  Rotating (로터 스플래시존 단면, HTC_SPLASH로 OIL결합) -> ~80C (OIL70~로터평균85.5 사이 근사)
  Housing  (외피, FEM 미포함 - 자켓오일 인접 박판 근사)  -> ~76C (OIL~JACKET 사이 근사)
"""
import os, json, time, traceback

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
ORIG_PRJ = r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project.freeflow"
NEW_PRJ = r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project_thermal.freeflow"
MAPDL_JSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\ff_mapdl_hybrid_temps.json"
LOG = os.path.join(SP, "ff_thermal_run.txt")
EXT_S = 0.10   # 검증용 확장 시간(초). 유동전용 실적(18313s/8.0s)으로 추정시 ~2-4분 예상.

_l = open(LOG, "w", encoding="utf-8")
def W(*a):
    _l.write(" ".join(str(x) for x in a) + "\n"); _l.flush()

try:
    d = json.load(open(MAPDL_JSON, encoding="utf-8"))
    ct = d["circuit_T"]; pp = d["per_part"]
    WALL_T = {
        "Stator": ct["JACKET"],
        "Winding": ct["SPRAY"],
        "Rotating": 0.3 * ct["OIL"] + 0.7 * 80.0 if False else 80.0,
        "Housing": 76.0,
    }
    W("wall BC 매핑:", WALL_T)

    proj = app.OpenProject(ORIG_PRJ)
    model = app.GetCurrentModel()
    W("project opened:", ORIG_PRJ)

    study = model
    W("HasResults (설정변경 전):", study.HasResults())
    # 실측: cp/k, 벽BC 변경은 전부 "결과 무효화" 대상 -> 기존 8s 유동결과와는
    # 양립 불가(all-or-nothing). 새 파일(NEW_PRJ)에만 영향이 남도록 여기서 명시적으로
    # DeleteResults() 수행(원본 ORIG_PRJ 파일은 아직 저장 전이라 디스크상 안전).
    study.DeleteResults()
    W("HasResults (삭제 후):", study.HasResults())

    phys = model.GetPhysics()
    phys.SetEnableThermalModel(True)
    W("thermal model enabled:", phys.GetEnableThermalModel())

    mats = model.GetMaterialCollection()
    fluid = mats.GetDefaultFluidMaterial()
    W("fluid BEFORE: rho=%.1f cp=%.1f k=%.4f mu=%.4f" % (
        fluid.GetDensity(), fluid.GetSpecificHeat(), fluid.GetThermalConductivity(), fluid.GetViscosity()))
    fluid.SetSpecificHeat(2000.0)
    fluid.SetThermalConductivity(0.135)
    W("fluid cp/k ATF로 교정 완료")
    W("fluid AFTER: rho=%.1f cp=%.1f k=%.4f mu=%.4f" % (
        fluid.GetDensity(), fluid.GetSpecificHeat(), fluid.GetThermalConductivity(), fluid.GetViscosity()))

    geo = model.GetGeometryCollection()
    items = {it.GetName(): it for it in geo}
    for nm, T in WALL_T.items():
        w = items[nm]
        try:
            w.SetThermalBoundaryConditionType("prescribed_temperature")
            w.SetTemperature(T)
            W(f"  wall {nm}: BCtype={w.GetThermalBoundaryConditionType()} T={w.GetTemperature()}")
        except Exception as e:
            W(f"  wall {nm}: 설정 실패:", repr(e)[:200])

    # 결과삭제 후 GetTimeSet()은 None(결과기반 타임셋이라 결과와 함께 사라짐) - 정상.
    W("GetTimeSet (결과삭제후, None 예상):", model.GetTimeSet())
    W("HasResults (저장 직전):", model.HasResults())
    W("CanResumeSimulation:", model.CanResumeSimulation())

    app.SaveProject(NEW_PRJ)
    W("saved as (설정만, 미솔브):", NEW_PRJ)
    W("DRY-RUN-DONE-OK")
except Exception:
    W("EXC:", traceback.format_exc())
finally:
    _l.close()
    os._exit(0)
