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
import json
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
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # eMach 루트

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


def harvest(mc, mode, speed, cur, ph, dest, r_active, r_end):
    """운전점 하나의 손실을 요약 JSON 과 같은 스키마로 뽑는다.

    필드만 복사하면 AF 를 만들 수 없다 (1차 실행이 그 상태였다). 키 이름은
    map_exports 의 Map_Summary JSON 과 맞춰 두어 그대로 병합할 수 있게 한다.
    """
    from tools.motorCAD.pyMCAD import calc_dc_loss_kw

    rec = {"proximity_model": PROX[mode], "mode": mode, "speed": speed,
           "current": cur, "phase": ph, "backup_dir": str(dest.parent)}
    if mode == "Hybrid":
        rec.update({
            "hybrid_total_kW":
                float(mc.get_variable("ACLoss_Hybrid_Total")) / 1000.0,
            "hybrid_prox_kW":
                float(mc.get_variable("ACLoss_Hybrid_Prox_Total")) / 1000.0,
            "hybrid_skin_kW":
                float(mc.get_variable("ACLoss_Hybrid_SkinEffect_Total"))
                / 1000.0,
        })
        return rec

    raw = mc.get_variable("ACLoss_FEA_OnLoad_PerTurn")
    per_turn = ([float(x) for x in raw.split(":")]
                if isinstance(raw, str) else list(raw))
    sum_kw = sum(per_turn) / 1000.0
    dc_act = calc_dc_loss_kw(r_active, cur)
    rec.update({
        "fea_per_turn_raw": raw if isinstance(raw, str) else "",
        "fea_per_turn_sum_kW": sum_kw,
        "fea_total_ac_kW":
            float(mc.get_variable("ACLoss_FEA_OnLoad_Total")) / 1000.0,
        "ts_dc_active_kW": dc_act,
        "ts_dc_end_kW": calc_dc_loss_kw(r_end, cur),
        "ts_ac_active_only_kW": sum_kw - dc_act,
    })
    return rec


def read_resistances(mc):
    """R_active / R_end 는 온도·형상만의 함수라 모드당 한 번만 읽는다."""
    try:
        mc.set_motorlab_context()
        rt = float(mc.get_variable("Resistance_MotorLAB"))
        re_ = float(mc.get_variable("EndWindingResistance_Lab"))
        mc.show_magnetic_context()
        return rt - re_, re_
    except Exception as exc:
        log("!! 저항 읽기 실패 (%s) --- DC 분리는 0 으로 둔다" % exc)
        return 0.0, 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Ref", choices=sorted(CURRENTS))
    ap.add_argument("--modes", default="FullFEA,Hybrid")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--redo", action="store_true",
                    help="폴더가 이미 있어도 다시 풀어 손실을 수집한다")
    ap.add_argument("--limit", type=int, default=0,
                    help="앞에서 N 점만 (0 = 전부). 시험 가동용")
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

    out_json = Path(__file__).with_name("lowcurrent_%s.json" % a.model)
    have = {}
    if out_json.exists():
        for r in json.loads(out_json.read_text(encoding="utf-8")):
            have[(r["mode"], round(r["current"], 3),
                  round(r["phase"], 1))] = r
        log("기존 손실 레코드 %d개: %s" % (len(have), out_json.name))

    # 손실이 없는 점은 폴더가 있어도 다시 풀어야 한다 (1차 실행이 필드만 뽑음).
    def missing(mode, cur, ph):
        return (mode, round(cur, 3), round(ph, 1)) not in have

    todo = [p for p in plan
            if (not p[4]) or a.redo or missing(p[0], p[1], p[2])]
    if a.limit:
        todo = todo[:a.limit]
    log("%s: 계획 %d점, 이미 있음 %d점, 실행 %d점"
        % (a.model, len(plan), len(plan) - len(todo), len(todo)))
    run_set = {(p[0], p[1], p[2]) for p in todo}
    for mode, cur, ph, dest, done in plan:
        log("   %-8s %7.1f A %5.1f deg  %s"
            % (mode, cur, ph,
               "run" if (mode, cur, ph) in run_set else "skip"))
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
            r_act, r_end = read_resistances(mc)
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
                rec = harvest(mc, mode, SPEED, cur, ph, dest, r_act, r_end)
                have[(mode, round(cur, 3), round(ph, 1))] = rec
                out_json.write_text(
                    json.dumps(sorted(have.values(),
                                      key=lambda r: (r["mode"], r["current"],
                                                     r["phase"])),
                               ensure_ascii=False, indent=1),
                    encoding="utf-8")
                w = (rec.get("hybrid_total_kW")
                     or rec.get("fea_total_ac_kW") or 0.0) * 1000.0
                n += 1
                log("  %2d/%d  %-8s %7.1f A %5.1f deg  %8.2f W  %4.1f분"
                    "  (누적 %.1f분)"
                    % (n, len(todo), mode, cur, ph, w,
                       (time.time() - t0) / 60, (time.time() - t_all) / 60))
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
