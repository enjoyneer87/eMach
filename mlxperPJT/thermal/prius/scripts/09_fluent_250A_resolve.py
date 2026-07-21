# -*- coding: utf-8 -*-
"""Fluent 250A 재솔브: 존 소스항을 250A 손실밀도로 교체 후 CHT 재해석."""
import os, json, traceback
log=open(r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad\fluent_250A.txt","w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
CAS=r"D:\KDH\simVary\Ansys_Thermal\Flu_MacTherm_EN_ILT_2019\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\2019R2\PriusMotor_3D45degree.cas.h5"
SAVE=r"D:\KDH\simVary\Ansys_Thermal\Prius_work\PriusMotor_250A"
OUT_JSON=r"D:\KDH\simVary\Ansys_Thermal\fluent_prius_250A_zone_temps.json"
# 250A 손실밀도 [W/m3] (동일형상 CDB 체적 기준)
Q250=dict(stator=265900.0, rotor=93400.0, magnet=171200.0, phase=3077000.0)
sv=None
try:
    import ansys.fluent.core as pf
    os.makedirs(os.path.dirname(SAVE),exist_ok=True)
    sv=pf.launch_fluent(mode="solver", processor_count=4, ui_mode="no_gui")
    sv.settings.file.read_case_data(file_name=CAS)
    P("read case+data (기존 저부하 해)")
    czc=sv.settings.setup.cell_zone_conditions
    # 소스항 교체
    for z,q in Q250.items():
        try:
            s=czc.solid[z]
            s.sources.enable=True
            s.sources.terms["energy"]=[{"option":"value","value":q}]
            P(f"  {z}: energy source -> {q:.3e} W/m3")
        except Exception as e:
            P(f"  {z} set fail: {str(e)[:120]}")
    # 재솔브 (steady, 이전해에서 이어서)
    try:
        sv.settings.solution.run_calculation.iterate(iter_count=600)
        P("iterated 600")
    except Exception as e:
        P("iterate fail:", str(e)[:150])
    # 저장
    try:
        sv.settings.file.write_case_data(file_name=SAVE)
        P("saved:", SAVE)
    except Exception as e: P("save fail:", str(e)[:100])
    # 존별 온도 추출 (report volume 안되면 나중 h5py)
    sv.exit(); P("DONE-OK")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    try:
        if sv is not None: sv.exit()
    except: pass
    log.close(); os._exit(0)
