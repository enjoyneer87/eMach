# -*- coding: utf-8 -*-
"""e4a_SC의 남은 V-shape 키 프로브 + 보정 + 게이트.

1) VShape_Magnet_ClearanceInner 접근명 시도 (배열/스칼라/대체 철자)
2) Pole_Surface_Radius 활성 여부 추정 (rotor dia 대비) 후 x k_r
3) 두 변형체 보정·저장 후 BackEMF 게이트 재실행
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

CI_NAMES = ("VShape_Magnet_ClearanceInner", "VShapeMagnetClearanceInner",
            "VShape_Magnet_Clearance_Inner", "VShapeMagnetClearanceInner_Array")


def probe_read(mc, label):
    print(f"  -- {label} --")
    for nm in CI_NAMES:
        for how in ("arr", "var"):
            try:
                if how == "arr":
                    v = mc.get_array_variable(nm, 0)
                else:
                    v = mc.get_variable(nm)
                print(f"    {how}:{nm} = {v!r}")
            except Exception as e:
                msg = str(e).splitlines()[0][:60]
                print(f"    {how}:{nm} XX {msg}")
    for nm in ("Pole_Surface_Radius", "Stator_Bore", "Airgap", "Shaft_Dia",
               "VSimple_Positioning_Method", "PoleVAngle_Array"):
        try:
            if nm.endswith("_Array"):
                v = mc.get_array_variable(nm, 0)
            else:
                v = mc.get_variable(nm)
            print(f"    {nm} = {v!r}")
        except Exception as e:
            print(f"    {nm} XX {str(e).splitlines()[0][:60]}")


def oc_emf(mc):
    mc.set_variable("BackEMFCalculation", True)
    mc.set_variable("TorqueCalculation", False)
    mc.set_variable("ShaftSpeed", EMF_SPEED)
    mc.do_magnetic_calculation()
    return float(mc.get_variable("RMSBackEMFLine"))


def main() -> int:
    import ansys.motorcad.core as pymotorcad
    pymotorcad.set_motorcad_exe(V261)

    mc = pymotorcad.MotorCAD(open_new_instance=True,
                             enable_success_variable=False)
    ref_ci = ref_psr = None
    try:
        mc.set_variable("MessageDisplayState", 2)
        mc.load_from_file(str(REF))
        probe_read(mc, "ref")
        for nm in CI_NAMES:
            try:
                ref_ci = (nm, float(mc.get_array_variable(nm, 0)))
                break
            except Exception:
                continue
        try:
            ref_psr = float(mc.get_variable("Pole_Surface_Radius"))
        except Exception:
            pass
        v0 = oc_emf(mc)
        print(f"[ref] RMSBackEMFLine = {v0:.4f}")
    finally:
        try:
            mc.quit()
        except Exception:
            pass

    for name, kr in VARIANTS:
        dst = BASE / name
        mc = pymotorcad.MotorCAD(open_new_instance=True,
                                 enable_success_variable=False)
        try:
            mc.set_variable("MessageDisplayState", 2)
            mc.load_from_file(str(dst))
            if ref_ci is not None:
                nm, v = ref_ci
                cur = float(mc.get_array_variable(nm, 0))
                if abs(cur / v - 1.0) < 0.005:
                    mc.set_array_variable(nm, 0, v * kr)
                    print(f"[{name}] {nm}[0] {cur:g} -> {v * kr:g}")
            if ref_psr:
                cur = float(mc.get_variable("Pole_Surface_Radius"))
                if abs(cur / ref_psr - 1.0) < 0.005:
                    mc.set_variable("Pole_Surface_Radius", ref_psr * kr)
                    print(f"[{name}] Pole_Surface_Radius {cur:g} -> "
                          f"{ref_psr * kr:g}")
            mc.save_to_file(str(dst))
            v1 = oc_emf(mc)
            r = v1 / v0
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
