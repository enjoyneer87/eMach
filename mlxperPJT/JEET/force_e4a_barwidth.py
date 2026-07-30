# -*- coding: utf-8 -*-
"""e4a 변형체 정밀 마감: 파생 드리프트 키 강제 설정 시험 + 게이트.

1) 변형체의 CI(VShape_Magnet_ClearanceInner)·bar width·web 배열 현재값 출력
2) MagnetBarWidth_Array[0]를 ref x k_r 정확값으로 set → readback으로
   입력 오버라이드 가능 여부 판정 (revert면 파생 확정, 건너뜀)
3) CI를 ref x k_r 정확값으로 set
4) BackEMF 게이트 재실행
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

V261 = r"C:\Program Files\ANSYS Inc\v261\motorcad\MotorCAD.exe"
BASE = Path(r"D:\KangDH\Thesis\e4a\newfam_results")
REF = BASE / "e4a_EMobility_IPM_User.mot"
VARIANTS = [("e4a_HalfSC.mot", 1.5), ("e4a_SC.mot", 2.0)]
EMF_SPEED = 1000.0
REF_VALS = {"VShape_Magnet_ClearanceInner": 0.2,
            "MagnetBarWidth_Array": 15.76,
            "WebThickness_Array": 6.736,
            "WebLength_Array": 2.208,
            "MagnetThickness_Array": 4.808,
            "BridgeThickness_Array": 0.7017,
            "VShapeMagnetPost_Array": 2.769,
            "VShapeMagnetClearance_Array": 0.2}
V0_EMF = 53.6233


def oc_emf(mc):
    mc.set_variable("BackEMFCalculation", True)
    mc.set_variable("TorqueCalculation", False)
    mc.set_variable("ShaftSpeed", EMF_SPEED)
    mc.do_magnetic_calculation()
    return float(mc.get_variable("RMSBackEMFLine"))


def main() -> int:
    import ansys.motorcad.core as pymotorcad
    pymotorcad.set_motorcad_exe(V261)

    for name, kr in VARIANTS:
        dst = BASE / name
        mc = pymotorcad.MotorCAD(open_new_instance=True,
                                 enable_success_variable=False)
        try:
            mc.set_variable("MessageDisplayState", 2)
            mc.load_from_file(str(dst))
            print(f"[{name}] k_r={kr} 현재 배열 상태:")
            for nm, v0 in REF_VALS.items():
                try:
                    cur = float(mc.get_array_variable(nm, 0))
                    print(f"    {nm:32s} {cur:9.4f}  (x{cur / v0:.4f}, "
                          f"목표 x{kr})")
                except Exception as e:
                    print(f"    {nm:32s} XX {str(e).splitlines()[0][:50]}")
            # CI 정확값
            try:
                mc.set_array_variable("VShape_Magnet_ClearanceInner", 0,
                                      0.2 * kr)
                rb = float(mc.get_array_variable(
                    "VShape_Magnet_ClearanceInner", 0))
                print(f"    CI set 0.2->{0.2 * kr:g}, readback {rb:g}")
            except Exception as e:
                print(f"    CI set XX {str(e).splitlines()[0][:60]}")
            # bar width 강제 설정 시험
            tgt = REF_VALS["MagnetBarWidth_Array"] * kr
            try:
                mc.set_array_variable("MagnetBarWidth_Array", 0, tgt)
                rb = float(mc.get_array_variable("MagnetBarWidth_Array", 0))
                ok = abs(rb / tgt - 1.0) < 1e-4
                print(f"    barwidth set {tgt:g}, readback {rb:g} "
                      f"{'(입력 오버라이드 성립)' if ok else '(revert — 파생 확정)'}")
                for nm in ("WebThickness_Array", "WebLength_Array"):
                    v = float(mc.get_array_variable(nm, 0))
                    print(f"      -> {nm} = {v:.4f} "
                          f"(x{v / REF_VALS[nm]:.4f})")
            except Exception as e:
                print(f"    barwidth set XX {str(e).splitlines()[0][:60]}")
            mc.save_to_file(str(dst))
            v1 = oc_emf(mc)
            r = v1 / V0_EMF
            print(f"[{name}] RMSBackEMFLine = {v1:.4f}  → 비 {r:.4f} "
                  f"(기대 {kr})  "
                  f"{'PASS' if abs(r / kr - 1) < 0.015 else '** FAIL'}")
            mc.save_to_file(str(dst))
        finally:
            try:
                mc.quit()
            except Exception:
                pass
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
