# -*- coding: utf-8 -*-
"""빠진 운전점 하나를 재해석해 **원시 export 폴더**만 채운다.

``ACLossCalcExport_<model>_no_txt/`` 는 운전점마다
``FullFEA_Speed_<rpm>RPM_<A>A_<deg>deg/`` 와 ``Hybrid_...`` 가 짝을
이루는데, SC 는 FullFEA 가 하나 비어 있었다
(``Speed_16000RPM_460.1A_90.0deg``). 원래 인필 재실행분은
``D:\\KDH\\simVary\\...`` 에 있었으나 그 폴더가 삭제되어 복사할 원본이
없다 --- 그래서 다시 풀어서 채운다.

**JSON 은 건드리지 않는다.** ``JEET_ACLoss_SC_Map_Summary.json`` 의 해당
레코드(460.05 A 인필)는 이미 검증된 89점 데이터셋의 일부이므로, 폴더를
채우자고 손실 수치를 덮어쓰면 안 된다. 이 스크립트는 순수하게 원시
FEA 결과 폴더만 만든다.

  python run_infill_export_folder.py --dry-run
  python run_infill_export_folder.py
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")
sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools\motorCAD")

MOTS = {
    "SC": r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot",
    "Ref": r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot",
}
EXPORT_ROOT = {
    "SC": r"D:\KangDH\Thesis\e10\ACLossCalcExport_SC_no_txt",
    "Ref": r"D:\KangDH\Thesis\e10\ACLossCalcExport_Ref_no_txt",
}
PROX = {"FullFEA": 3, "Hybrid": 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="SC", choices=sorted(MOTS))
    ap.add_argument("--mode", default="FullFEA", choices=sorted(PROX))
    ap.add_argument("--speed", type=float, default=16000.0)
    ap.add_argument("--current", type=float, default=460.1)
    ap.add_argument("--phase", type=float, default=90.0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    # 기존 폴더와 **문자 그대로 같은** 이름 규칙을 써야 세트로 묶인다
    name = "%s_Speed_%.0fRPM_%gA_%.1fdeg" % (
        a.mode, a.speed, a.current, a.phase)
    dest = Path(EXPORT_ROOT[a.model]) / name / "FEResultsData"
    mot = Path(MOTS[a.model])
    src = mot.with_suffix("") / "FEResultsData"

    print("model   :", a.model)
    print("운전점  : %.0f rpm, %g A, %.1f deg (%s, prox=%d)"
          % (a.speed, a.current, a.phase, a.mode, PROX[a.mode]))
    print("대상    :", dest)
    if dest.exists() and any(dest.iterdir()):
        print("이미 존재하고 비어있지 않음 --- 덮어쓰지 않고 종료.")
        return
    if a.dry_run:
        print("[dry-run] Motor-CAD 실행 없이 종료.")
        return
    if not mot.exists():
        sys.exit(".mot 없음: %s" % mot)

    import ansys.motorcad.core as pymotorcad
    mc = pymotorcad.MotorCAD(open_new_instance=True,
                             enable_success_variable=False)
    try:
        try:
            mc.set_variable("MessageDisplayState", 2)
        except Exception:
            pass
        mc.load_from_file(str(mot))
        mc.set_variable("ProximityLossModel", PROX[a.mode])
        mc.set_variable("ShaftSpeed", a.speed)
        mc.set_variable("RMSCurrent", a.current)
        mc.set_variable("PhaseAdvance", a.phase)
        print("해석 중 ...")
        mc.do_magnetic_calculation()
        print("해석 완료")
    finally:
        try:
            mc.quit()
            print("Motor-CAD 종료 (모델 저장 안 함)")
        except Exception:
            pass

    if not src.exists():
        sys.exit("결과 폴더 없음: %s" % src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True)
    files = sorted(dest.iterdir())
    print("\n복사 완료: %s (%d개 파일)" % (dest, len(files)))
    for f in files:
        print("  %10d  %s" % (f.stat().st_size, f.name))


if __name__ == "__main__":
    main()
