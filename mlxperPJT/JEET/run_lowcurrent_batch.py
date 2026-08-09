# -*- coding: utf-8 -*-
"""비포화 저전류 행 일괄 해석 (B' 캠페인).

기존 부하 격자의 최저 전류에서 이미 근접 손실 지수가 1.6 이라 포화 영역이다.
그 아래 --- 무부하(0.1 A)와 최저 부하 사이 --- 는 표본이 하나도 없는데,
f_theta 도 AF 의 beta 폭도 그 구간에서 자릿수로 바뀐다. 그 구간을 연다.

전류는 옥타브 사다리로 잡고 상사 잠금을 유지한다 (I_variant = k_r * I_Ref):
    Ref     14.4 / 28.8 / 57.6
    HalfSC  21.6 / 43.2 / 86.4
    SC      28.8 / 57.6 / 115.2

run_infill_export_folder.py 와 같은 이름 규칙·같은 Motor-CAD 호출을 쓰되,
(model, mode) 당 Motor-CAD 를 한 번만 띄우고 18점을 돈다. 점마다 새로 띄우면
기동 오버헤드가 108점에서 한 시간 가까이 된다.

이미 있고 비어 있지 않은 폴더는 건너뛴다 --- 중단 후 재실행해도 안전하다.

  python run_lowcurrent_batch.py --model Ref            # 36점 (2모드)
  python run_lowcurrent_batch.py --model Ref --dry-run
"""
import argparse
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

MOTS = {
    "Ref": r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot",
    "SC": r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot",
}
EXPORT_ROOT = {
    "Ref": r"D:\KangDH\Thesis\e10\ACLossCalcExport_Ref_no_txt",
    "SC": r"D:\KangDH\Thesis\e10\ACLossCalcExport_SC_no_txt",
}
PROX = {"FullFEA": 3, "Hybrid": 1}
CURRENTS = {
    "Ref": [14.4, 28.8, 57.6],
    "HalfSC": [21.6, 43.2, 86.4],
    "SC": [28.8, 57.6, 115.2],
}
PHASES = [0.0, 18.0, 36.0, 54.0, 72.0, 90.0]
SPEED = 16000.0


def log(msg):
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Ref", choices=sorted(CURRENTS))
    ap.add_argument("--modes", default="FullFEA,Hybrid")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.model not in MOTS:
        sys.exit("%s 의 .mot 경로가 등록돼 있지 않다 (MOTS 를 채울 것)"
                 % a.model)
    mot = Path(MOTS[a.model])
    if not mot.exists():
        sys.exit(".mot 없음: %s" % mot)
    src = mot.with_suffix("") / "FEResultsData"
    root = Path(EXPORT_ROOT[a.model])

    plan = []
    for mode in a.modes.split(","):
        for cur in CURRENTS[a.model]:
            for ph in PHASES:
                name = "%s_Speed_%.0fRPM_%gA_%.1fdeg" % (
                    mode, SPEED, cur, ph)
                dest = root / name / "FEResultsData"
                done = dest.exists() and any(dest.iterdir())
                plan.append((mode, cur, ph, dest, done))

    todo = [p for p in plan if not p[4]]
    log("%s: 계획 %d점, 이미 있음 %d점, 실행 %d점"
        % (a.model, len(plan), len(plan) - len(todo), len(todo)))
    for mode, cur, ph, dest, done in plan:
        log("   %-8s %7.1f A %5.1f deg  %s"
            % (mode, cur, ph, "skip" if done else "run"))
    if a.dry_run or not todo:
        log("[dry-run] 종료" if a.dry_run else "할 일 없음")
        return 0

    import ansys.motorcad.core as pymotorcad

    t_all = time.time()
    n = 0
    for mode in a.modes.split(","):
        items = [p for p in todo if p[0] == mode]
        if not items:
            continue
        log("=== %s / %s : Motor-CAD 기동 (%d점)"
            % (a.model, mode, len(items)))
        mc = pymotorcad.MotorCAD(open_new_instance=True,
                                 enable_success_variable=False)
        try:
            try:
                mc.set_variable("MessageDisplayState", 2)
            except Exception:
                pass
            mc.load_from_file(str(mot))
            mc.set_variable("ProximityLossModel", PROX[mode])
            for _, cur, ph, dest, _ in items:
                t0 = time.time()
                mc.set_variable("ShaftSpeed", SPEED)
                mc.set_variable("RMSCurrent", cur)
                mc.set_variable("PhaseAdvance", ph)
                mc.do_magnetic_calculation()
                if not src.exists():
                    log("!! 결과 폴더 없음: %s" % src)
                    return 2
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dest, dirs_exist_ok=True)
                n += 1
                log("  %2d/%d  %-8s %7.1f A %5.1f deg  %5.1f분  (누적 %.1f분)"
                    % (n, len(todo), mode, cur, ph, (time.time() - t0) / 60,
                       (time.time() - t_all) / 60))
        finally:
            try:
                mc.quit()
            except Exception:
                pass
            log("=== %s / %s : Motor-CAD 종료" % (a.model, mode))

    log("완료: %d점, 총 %.1f분" % (n, (time.time() - t_all) / 60))
    return 0


if __name__ == "__main__":
    sys.exit(main())
