# -*- coding: utf-8 -*-
"""e4a 변형체 보정 + 물리 게이트.

1) e10 Ref↔SC diff 그라운드 트루스 대비 누락 키를 x k_r 보정:
   Airgap, Conductors{Horizontal,SlotBase,SlotTooth,Vertical},
   Copper_Corner_Radius, Copper_Diameter, Wire_Diameter,
   CornerRoundingRadius_{Magnets,Rotor}, MinBackIronThickness(존재 시).
2) 물리 게이트: 무부하 BackEMF 계산으로 기본파 쇄교자속 λ_1 비교 —
   B-보존 스케일링이면 λ_SC/λ_ref = k_w·k_r·k_a = k_r (±1%).
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
FIX_KEYS = ("Airgap", "ConductorsHorizontal", "ConductorsSlotBase",
            "ConductorsSlotTooth", "ConductorsVertical",
            "Copper_Corner_Radius", "Copper_Diameter", "Wire_Diameter",
            "CornerRoundingRadius_Magnets", "CornerRoundingRadius_Rotor",
            "MinBackIronThickness",
            # 회전자 Interior_VShape 절대 mm 입력 (e4a는 e10과 달리 활성)
            "Magnet_Thickness", "Web_Thickness", "Web_Length",
            "Bridge_Thickness")
FIX_ARRAYS = ("BridgeThickness_Array", "MagnetThickness_Array",
              "WebThickness_Array", "WebLength_Array",
              # V자 포스트·클리어런스 (미스케일 시 포스트 포화→자속 과다,
              # 파생 MagnetBarWidth 과대) — scan_e4a_dims.py 색출분
              "VShapeMagnetPost_Array", "VShapeMagnetClearance_Array",
              "VShape_Magnet_ClearanceInner")
EMF_SPEED = 1000.0


def oc_flux(mc):
    """무부하 BackEMF 계산 → 기본파 선간/상 EMF에서 λ_1 산출."""
    mc.set_variable("BackEMFCalculation", True)
    mc.set_variable("TorqueCalculation", False)
    mc.set_variable("ShaftSpeed", EMF_SPEED)
    mc.do_magnetic_calculation()
    for key in ("FundamentalBackEMFLine_RMS", "RMSBackEMFLine",
                "BackEMFConstant", "FundamentalBackEMFPhase_RMS"):
        try:
            v = float(mc.get_variable(key))
            if v:
                return key, v
        except Exception:
            continue
    return None, None


def main() -> int:
    import ansys.motorcad.core as pymotorcad
    pymotorcad.set_motorcad_exe(V261)

    # 기준 λ
    mc = pymotorcad.MotorCAD(open_new_instance=True,
                             enable_success_variable=False)
    try:
        mc.set_variable("MessageDisplayState", 2)
        mc.load_from_file(str(REF))
        k0, v0 = oc_flux(mc)
        print(f"[ref] {k0} = {v0:.4f} @ {EMF_SPEED:g} rpm")
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
            print(f"[{name}] 키 보정 (x{kr}):")
            for key in FIX_KEYS:
                try:
                    cur = float(mc.get_variable(key))
                except Exception:
                    continue
                tgt = None
                # 이미 스케일됐는지 원본 대비로 판정하지 않고, 변형 파일의
                # 현재값이 원본과 같으면 미적용으로 간주해 kr배 한다.
                mc2 = None
                try:
                    import re as _re
                    import io as _io
                    s0 = _io.open(REF, encoding="latin-1").read()
                    m = _re.search(r"^%s=(-?[\d.eE+-]+)" % key, s0, _re.M)
                    ref_v = float(m.group(1)) if m else None
                except Exception:
                    ref_v = None
                if ref_v is None or ref_v == 0:
                    continue
                ratio = cur / ref_v
                if abs(ratio - 1.0) < 0.005:
                    tgt = ref_v * kr
                elif abs(ratio - kr) < 0.02:
                    print(f"    {key:30s} 이미 적용 (x{ratio:.3f})")
                    continue
                else:
                    print(f"    {key:30s} 비정형 x{ratio:.3f} — 건너뜀")
                    continue
                mc.set_variable(key, tgt)
                print(f"    {key:30s} {cur:9.4g} -> {tgt:9.4g}")
            # 레이어 배열 키 (원본 .mot의 값 x kr)
            import re as _re
            import io as _io
            s0 = _io.open(REF, encoding="latin-1").read()
            for fam in FIX_ARRAYS:
                for m in _re.finditer(r"^%s\[(\d+)\]=(-?[\d.eE+-]+)" % fam,
                                      s0, _re.M):
                    idx, v0a = int(m.group(1)), float(m.group(2))
                    if v0a == 0:
                        continue
                    try:
                        cur_a = float(mc.get_array_variable(fam, idx))
                    except Exception:
                        continue
                    if abs(cur_a / v0a - 1.0) < 0.005:
                        mc.set_array_variable(fam, idx, v0a * kr)
                        print(f"    {fam}[{idx}]{'':16s} {v0a:9.4g} -> "
                              f"{v0a * kr:9.4g}")
            mc.save_to_file(str(dst))
            k1, v1 = oc_flux(mc)
            r = v1 / v0 if (v0 and v1) else float("nan")
            print(f"[{name}] {k1} = {v1:.4f}  → 비 {r:.4f} (기대 {kr})"
                  f"  {'PASS' if abs(r / kr - 1) < 0.015 else '** FAIL'}")
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
