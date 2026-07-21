# -*- coding: utf-8 -*-
"""e10 Motor-CAD 손실 읽기 - ActiveXParametersMotorCADv261.txt 정확한 파라미터명."""
import os, json, traceback
SP=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad"
MOT=r"D:\KDH\simVary\e10_6TSweep\refModel\e10Turn6V261.mot"
OUTJSON=r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_losses.json"
log=open(SP+r"\e10_mcad2.txt","w",encoding="utf-8")
def P(*a): log.write(" ".join(str(x) for x in a)+"\n"); log.flush()
# ActiveXParametersMotorCADv261.txt (Loss and Injected Power Values) 정확명
LOSS={"copper_total":"Armature_Winding_Loss_Total",
      "copper_dc":"Power_Armature_Copper_Loss",
      "copper_freqcomp":"Power_Armature_Copper_Freq_Comp_Loss",
      "stator_iron_backiron":"Loss_[Stator_Back_Iron]",
      "stator_iron_tooth":"Loss_[Stator_Tooth]",
      "rotor_iron_backiron":"Loss_[Rotor_Back_Iron]",
      "rotor_iron_tooth":"Loss_[Rotor_Tooth]",
      "magnet":"Loss_[Magnet]",
      "rotor_copper":"Loss_[Rotor_Copper]"}
try:
    import ansys.motorcad.core as mc
    P("launch Motor-CAD"); motor=mc.MotorCAD()
    P("load", MOT); motor.load_from_file(MOT); P("loaded OK")
    op={}
    for v in ("Shaft_Speed_RPM","ShaftSpeed","RMSCurrent","PeakCurrent","DCBusVoltage","PhaseAdvance"):
        try: op[v]=motor.get_variable(v)
        except Exception: pass
    P("op:", op)
    try: P("do_magnetic_calculation..."); motor.do_magnetic_thermal_calculation(); P("  mag+thermal done")
    except Exception as e: P("  magcalc:", repr(e)[:150])
    res={"_operating_point":op,"_source":"e10Turn6V261.mot Motor-CAD do_magnetic_calculation",
         "_param_ref":"ActiveXParametersMotorCADv261.txt","losses_W":{}}
    for key,name in LOSS.items():
        try:
            val=motor.get_variable(name); res["losses_W"][key]=val; P(f"  {key} [{name}] = {val}")
        except Exception as e: P(f"  {key} [{name}] FAIL {repr(e)[:80]}")
    # 집계
    lw=res["losses_W"]
    def g(k): 
        v=lw.get(k); 
        try: return float(v)
        except Exception: return 0.0
    res["_summary_W"]={
        "copper": g("copper_total") or g("copper_dc"),
        "stator_iron": g("stator_iron_backiron")+g("stator_iron_tooth"),
        "rotor_iron": g("rotor_iron_backiron")+g("rotor_iron_tooth"),
        "magnet": g("magnet")}
    P("summary:", res["_summary_W"])
    os.makedirs(os.path.dirname(OUTJSON),exist_ok=True)
    json.dump(res, open(OUTJSON,"w",encoding="utf-8"), indent=2, ensure_ascii=False, default=str)
    P("saved", OUTJSON); P("DONE-OK")
    try: motor.quit()
    except Exception: pass
except Exception:
    P("EXC:", traceback.format_exc())
finally: log.close()
os._exit(0)
