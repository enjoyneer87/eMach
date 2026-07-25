# -*- coding: utf-8 -*-
"""운전점별 .mes -> FEA_data.txt 일괄 복원 (Ref/SC no_txt 트리 백필).

Cleanup 때 Ref/SC 의 평문 FEA_data.txt 는 삭제됐지만 바이너리
FEResultsData/OnLoadTorque_result_1.mes 는 전 운전점에 남아 있다.
Motor-CAD COM 세션 하나로 .mot 를 로드한 뒤, 각 OP 의 .mes 를
prepare_fea_export_session + get_magnetic_data 로 재해석 없이 텍스트로
내보내고, 즉시 gzip 해 원문을 지운다 (원문 총 ~220 GB 는 로컬 여유 초과,
gzip 후 ~25 GB). 이후 rclone 으로 Drive 에 보존한다.

사용:
  python run_mes_txt_backfill.py --validate            # HalfSC 1점 비트 대조
  python run_mes_txt_backfill.py --model Ref           # Ref 240 OP 백필
  python run_mes_txt_backfill.py --model SC --limit 5  # 시험 가동

산출: D:\KangDH\Thesis\e10\_txt_backfill\<model>\<OP>\FEA_data.txt.gz
재시작 안전: 이미 .gz 있는 OP 는 건너뜀.
"""
from __future__ import annotations

import argparse
import gzip
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")
sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools\motorCAD")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

E10 = Path(r"D:\KangDH\Thesis\e10")
STAGE = E10 / "_txt_backfill"
MODELS = {
    "Ref": (E10 / r"refModel\e10Turn6V261.mot",
            E10 / "ACLossCalcExport_Ref_no_txt"),
    "SC": (E10 / r"SLFEA\e10Turn6V261SLFEA.mot",
           E10 / "ACLossCalcExport_SC_no_txt"),
    "HalfSC": (E10 / r"SLFEA_Half\e10Turn6V261SLFEA_Half.mot",
               E10 / r"SLFEA_Half\ACLossCalcExport_Map"),
}


def find_mes(op_dir: Path):
    m = op_dir / "FEResultsData" / "OnLoadTorque_result_1.mes"
    if m.exists():
        return m
    cand = sorted((op_dir / "FEResultsData").glob("OnLoadTorque_result_*.mes"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    return cand[0] if cand else None


def gzip_file(src: Path, dst: Path, level: int = 4):
    with open(src, "rb") as fi, gzip.open(dst, "wb",
                                          compresslevel=level) as fo:
        shutil.copyfileobj(fi, fo, 1 << 22)


def open_session(mot: Path):
    import ansys.motorcad.core as pymotorcad
    mc = pymotorcad.MotorCAD(open_new_instance=True,
                             enable_success_variable=False)
    try:
        mc.set_variable("MessageDisplayState", 2)
    except Exception:
        pass
    mc.load_from_file(str(mot))
    print(f"loaded: {mot}", flush=True)
    return mc


# 원 캠페인(_mcad_parallel_worker)과 동일한 컬럼·시그니처 — 비트 동일 재현용
EXPORT_COLUMNS = "RegCode,Bx,By,A,J,Je,Hx,Hy,Mur"


def export_one(mc, mes: Path, out_txt: Path):
    from pyMCAD.fea_workflow import prepare_fea_export_session
    prepare_fea_export_session(mc, mes_path=mes)
    torque_points = int(mc.get_variable("TorquePointsPerCycle"))
    mc.save_fea_data(str(out_txt), 1, torque_points, EXPORT_COLUMNS,
                     "", ",")


def validate():
    """HalfSC 원본 txt 보유 OP 1점: .mes 재export 와 원본 비트 대조."""
    mot, root = MODELS["HalfSC"]
    op = None
    for d in sorted(root.glob("Hybrid_Speed_*")):
        if (d / "FEA_data.txt").exists() and find_mes(d):
            op = d
            break
    assert op, "검증용 OP 없음"
    ref_txt = op / "FEA_data.txt"
    out_txt = STAGE / "_validate" / "FEA_data.txt"
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    print(f"검증 OP: {op.name}")
    mc = open_session(mot)
    try:
        t0 = time.time()
        export_one(mc, find_mes(op), out_txt)
        print(f"export {time.time() - t0:.0f}s  "
              f"원본 {ref_txt.stat().st_size / 1e6:.1f} MB vs "
              f"재추출 {out_txt.stat().st_size / 1e6:.1f} MB", flush=True)
    finally:
        try:
            mc.quit()
        except Exception:
            pass
    import filecmp
    same = filecmp.cmp(str(ref_txt), str(out_txt), shallow=False)
    print(f"비트 동일: {same}")
    if not same:
        with open(ref_txt, encoding="utf-8", errors="ignore") as f1, \
                open(out_txt, encoding="utf-8", errors="ignore") as f2:
            for i in range(5):
                a, b = f1.readline().rstrip(), f2.readline().rstrip()
                mark = " " if a == b else "≠"
                print(f" {mark} 원본: {a[:70]}")
                if a != b:
                    print(f"   재출: {b[:70]}")
    return 0 if same else 2


def backfill(model: str, limit=None, mode_filter=None):
    mot, root = MODELS[model]
    ops = sorted([d for d in root.iterdir() if d.is_dir()
                  and (d.name.startswith("Hybrid_")
                       or d.name.startswith("FullFEA_"))])
    if mode_filter:
        ops = [d for d in ops if d.name.startswith(mode_filter)]
    if limit:
        ops = ops[:limit]
    stage_root = STAGE / model
    done = skip = fail = 0
    t0 = time.time()
    print(f"[{model}] 대상 {len(ops)} OP", flush=True)
    mc = open_session(mot)
    try:
        for i, op in enumerate(ops):
            dst = stage_root / op.name / "FEA_data.txt.gz"
            if dst.exists() and dst.stat().st_size > 1e6:
                skip += 1
                continue
            mes = find_mes(op)
            if mes is None:
                print(f"  [{i + 1}/{len(ops)}] {op.name}: .mes 없음", flush=True)
                fail += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp_txt = dst.parent / "FEA_data.txt"
            try:
                t1 = time.time()
                export_one(mc, mes, tmp_txt)
                sz = tmp_txt.stat().st_size / 1e6
                gzip_file(tmp_txt, dst)
                gz = dst.stat().st_size / 1e6
                tmp_txt.unlink()
                done += 1
                el = time.time() - t0
                eta = el / max(done, 1) * (len(ops) - i - 1) / 60
                print(f"  [{i + 1}/{len(ops)}] {op.name}: {sz:.0f}->"
                      f"{gz:.0f} MB  {time.time() - t1:.0f}s"
                      f"  (ETA {eta:.0f}min)", flush=True)
            except Exception as ex:
                fail += 1
                print(f"  [{i + 1}/{len(ops)}] {op.name}: 실패 {ex}",
                      flush=True)
                if tmp_txt.exists():
                    tmp_txt.unlink()
    finally:
        try:
            mc.quit()
        except Exception:
            pass
    print(f"[{model}] 완료 {done} / 건너뜀 {skip} / 실패 {fail}"
          f"  ({(time.time() - t0) / 60:.0f}min)", flush=True)
    return 0 if fail == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--model", choices=sorted(MODELS))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--mode", choices=["Hybrid", "FullFEA"])
    a = ap.parse_args()
    if a.validate:
        return validate()
    if not a.model:
        ap.error("--model 또는 --validate 필요")
    return backfill(a.model, a.limit, a.mode)


if __name__ == "__main__":
    raise SystemExit(main())
