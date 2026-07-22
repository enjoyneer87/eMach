# -*- coding: utf-8 -*-
"""Project_thermal.freeflow(열설정 완료본) 로드 -> 밀도도 ATF로 교정(결과 이미 없어 안전)
-> 짧은 검증구간(TARGET_S초) 솔브 -> 저장. 벽시계 안전상한 CAP_S 도달시 강제중단."""
import os, time, traceback

SP = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
PRJ = r"D:\KDH\simVary\simFreeFlow\20251226\FreeFlow\FreeFlowProject\Project_thermal.freeflow"
LOG = os.path.join(SP, "ff_thermal_shortrun.txt")
TARGET_S = 0.40     # 목표 물리시간(검증구간)
CAP_S = 45 * 60      # 벽시계 안전상한 45분 - 도달시 StopSimulation() 후 저장

_l = open(LOG, "w", encoding="utf-8")
def W(*a):
    _l.write(" ".join(str(x) for x in a) + "\n"); _l.flush()

try:
    app.OpenProject(PRJ)
    model = app.GetCurrentModel()
    W("opened:", PRJ, "HasResults:", model.HasResults())
    if model.HasResults():
        model.DeleteResults()
        W("이전 킬된런 잔여결과 삭제. HasResults now:", model.HasResults())

    mats = model.GetMaterialCollection()
    fluid = mats.GetDefaultFluidMaterial()
    W("fluid BEFORE density fix: rho=%.1f cp=%.1f k=%.4f" % (
        fluid.GetDensity(), fluid.GetSpecificHeat(), fluid.GetThermalConductivity()))
    fluid.SetDensity(825.0)   # 결과 없는 상태라 이제 안전(무효화 대상 없음)
    W("fluid AFTER: rho=%.1f" % fluid.GetDensity())

    # 근본원인 발견: Fluid Inlet(주입 오일) 자체 온도가 0.0 이었음(벽만 뜨겁게 해봐야
    # 유입되는 오일이 계속 0으로 들어오면 벌크가 안 데워짐) -> OIL 공급온도 70C로 설정.
    inout = model.GetInletsOutletsCollection()
    finlet = [it for it in inout if "Fluid Inlet" in (it.GetName() or "")][0]
    W("FluidInlet T BEFORE:", finlet.GetTemperature())
    finlet.SetTemperature(70.0)
    W("FluidInlet T AFTER:", finlet.GetTemperature())

    try:
        model.ExtendSimulation(extension_amount=TARGET_S)
        W(f"ExtendSimulation({TARGET_S}s) 성공")
    except Exception as e:
        W("ExtendSimulation 실패(직접 duration 없이 진행):", repr(e)[:200])

    app.SaveProject()
    W("설정 저장 완료. 솔브 시작 (non_blocking) ...")

    t0 = time.time()
    ok = model.StartSimulation(skip_summary=True, delete_results=False, non_blocking=True)
    W("StartSimulation launched:", ok)
    last_log = -999.0
    stopped_early = False
    while model.IsSimulating():
        time.sleep(4.0)
        el = time.time() - t0
        if el - last_log >= 15.0:
            prog = model.GetProgress()
            W(f"  ... wall={el:.0f}s progress={prog}")
            last_log = el
        if el >= CAP_S:
            W(f"안전상한 {CAP_S}s 도달 -> StopSimulation()")
            model.StopSimulation()
            stopped_early = True
            break
    # StopSimulation 후에도 IsSimulating 이 잠시 True일 수 있어 짧게 대기
    for _ in range(30):
        if not model.IsSimulating():
            break
        time.sleep(2.0)
    t_solve = time.time() - t0
    W(f"종료. wall-clock={t_solve:.1f}s stopped_early={stopped_early}")
    W("final status:", model.GetStatus())
    W("HasResults:", model.HasResults())

    ts = model.GetTimeSet()
    if ts is not None:
        vals = ts.GetValues()
        W("timeset n:", len(vals), "last t:", vals[-1] if len(vals) else None)
    else:
        W("timeset: None")

    app.SaveProject()
    W("결과 저장 완료:", PRJ)
    W("DONE-OK")
except Exception:
    W("EXC:", traceback.format_exc())
finally:
    _l.close()
    os._exit(0)
