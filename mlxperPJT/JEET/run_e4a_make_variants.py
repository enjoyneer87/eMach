# -*- coding: utf-8 -*-
"""e4a 상사 패밀리 변형체 생성 — SLScaleMachine 파이썬 체인으로 k_r=1.5/2.0 .mot.

e10 SLFEA 계보와 동일 규칙: 전 반경 치수 x k_r, k_a=1(적층 불변), k_w=1(턴 불변),
저항·인덕턴스 상사 갱신. 생성 후 읽기 검증(주요 치수 x k_r 확인).
산출: newfam_results/e4a_HalfSC.mot, e4a_SC.mot
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str((HERE / ".." / ".." / "tools" / "motorCAD").resolve()))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

V261 = r"C:\Program Files\ANSYS Inc\v261\motorcad\MotorCAD.exe"
BASE = Path(r"D:\KangDH\Thesis\e4a\newfam_results")
SRC = BASE / "e4a_EMobility_IPM_User.mot"
VARIANTS = [("e4a_HalfSC.mot", 1.5), ("e4a_SC.mot", 2.0)]
CHECK_KEYS = ("Stator_Lam_Dia", "Copper_Width", "Slot_Depth", "Airgap",
              "Stator_Bore", "Magnet_Thickness")


def main() -> int:
    import ansys.motorcad.core as pymotorcad
    from pyMCAD.scaling import (def_scaling_factor, get_mcad_machine_data,
                                sl_scale_machine, apply_scaled_data_to_mcad)

    pymotorcad.set_motorcad_exe(V261)
    for name, kr in VARIANTS:
        dst = BASE / name
        shutil.copyfile(SRC, dst)
        mc = pymotorcad.MotorCAD(open_new_instance=True,
                                 enable_success_variable=False)
        try:
            mc.set_variable("MessageDisplayState", 2)
            mc.load_from_file(str(dst))
            ref_vals = {}
            for k in CHECK_KEYS:
                try:
                    ref_vals[k] = float(mc.get_variable(k))
                except Exception:
                    pass
            geo = get_mcad_machine_data(mc)
            n_c = (geo.MagTurnsConductor if geo.Armature_CoilStyle == 0
                   else geo.WindingLayers)
            factor = def_scaling_factor(kr, 1.0, 3, n_c, geo.ParallelPaths,
                                        geo)
            scaled = sl_scale_machine(factor, geo)
            apply_scaled_data_to_mcad(scaled, mc)
            mc.save_to_file(str(dst))
            print(f"[{name}] k_r={kr} 적용·저장")
            for k, v0 in ref_vals.items():
                try:
                    v1 = float(mc.get_variable(k))
                    ratio = v1 / v0 if v0 else float("nan")
                    print(f"    {k:18s} {v0:9.3f} -> {v1:9.3f}  (x{ratio:.3f})")
                except Exception:
                    pass
        finally:
            try:
                mc.quit()
            except Exception:
                pass
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
