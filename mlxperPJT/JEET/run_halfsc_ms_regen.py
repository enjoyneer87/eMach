# -*- coding: utf-8 -*-
"""HalfSC 캠페인 Hybrid(MS) 120 운전점 재생성 -> FEA_data.txt.gz (+.mes 보존).

배경: HalfSC 의 캠페인 per-OP export(전류 172.5~690 A)는 소실되었고,
ACLossCalcExport_Map 에는 예비 스윕(115~460 A, 106개)만 남았다. AF 분모의
필드 기반 재계산(360 = 120x3)을 완성하려면 캠페인 격자의 MS 해를 다시
푼다 --- 정자기라 TS 대비 저렴하고, 결과는 Map_Summary 의 hybrid 값과
대조 가능하다.

운전점 목록: JEET_ACLoss_HalfSC_Map_Summary.json 의 Hybrid 레코드 120개.
세팅: ProximityLossModel=1, ShaftSpeed/RMSCurrent/PhaseAdvance --- 원
캠페인 워커(_mcad_parallel_worker)와 동일. export 컬럼·시그니처는
run_mes_txt_backfill 과 동일(A/m^2 전정밀).

사용:  <pyMotorEnv_310 python> run_halfsc_ms_regen.py [--shard K --nshards N]
산출:  D:\KangDH\Thesis\e10\_txt_backfill\HalfSC_campaign\<OP>\FEA_data.txt.gz
       + FEResultsData\*.mes 사본 (바이너리 보존)
재시작 안전: .gz 존재 시 건너뜀.
"""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "tools")))  # 이 체크아웃의 tools
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "tools", "motorCAD")))  # 이 체크아웃의 tools
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MOT = Path(r"D:\KangDH\Thesis\e10\SLFEA_Half\e10Turn6V261SLFEA_Half.mot")
SUMMARY = Path(r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports"
               r"\e10\HalfSC\JEET_ACLoss_HalfSC_Map_Summary.json")
STAGE = Path(r"D:\KangDH\Thesis\e10\_txt_backfill\HalfSC_campaign")
EXPORT_COLUMNS = "RegCode,Bx,By,A,J,Je,Hx,Hy,Mur"


def gzip_file(src: Path, dst: Path, level: int = 4):
    with open(src, "rb") as fi, gzip.open(dst, "wb",
                                          compresslevel=level) as fo:
        shutil.copyfileobj(fi, fo, 1 << 22)


def op_list():
    """MS 는 속도 무관 -> 필드 미확보 링의 (I,beta) 조합만, 16k 에서 1회.

    (스윕 트리가 345.0/0.1 A 링을 전 beta 커버 -> 제외. 172.5/517.5/690 링
    은 스칼라 레코드만 있고 필드가 없다 -- run_halfsc_normalize/690_tier 는
    save_fea_data 를 호출하지 않았음.)
    """
    ops = [(16000, cur, ph)
           for cur in (172.5, 517.5, 690.0)
           for ph in (0.0, 18.0, 36.0, 54.0, 72.0, 90.0)]
    return ops


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()

    ops = op_list()
    if a.nshards > 1:
        ops = ops[a.shard::a.nshards]
    if a.limit:
        ops = ops[:a.limit]
    print(f"HalfSC 캠페인 MS 재생성: {len(ops)} OP", flush=True)

    import ansys.motorcad.core as pymotorcad
    from pyMCAD.fea_workflow import prepare_fea_export_session  # noqa: F401
    mc = pymotorcad.MotorCAD(open_new_instance=True,
                             enable_success_variable=False)
    done = skip = fail = 0
    t0 = time.time()
    try:
        try:
            mc.set_variable("MessageDisplayState", 2)
        except Exception:
            pass
        mc.load_from_file(str(MOT))
        print(f"loaded: {MOT}", flush=True)
        fe_dir = MOT.parent / MOT.stem / "FEResultsData"

        for i, (spd, cur, ph) in enumerate(ops):
            name = f"Hybrid_Speed_{spd}RPM_{cur:.1f}A_{ph:.1f}deg"
            dst_dir = STAGE / name
            dst_gz = dst_dir / "FEA_data.txt.gz"
            if dst_gz.exists() and dst_gz.stat().st_size > 1e6:
                skip += 1
                continue
            try:
                t1 = time.time()
                mc.set_variable("ProximityLossModel", 1)
                mc.set_variable("ShaftSpeed", spd)
                mc.set_variable("RMSCurrent", cur)
                mc.set_variable("PhaseAdvance", ph)
                mc.do_magnetic_calculation()
                t_solve = time.time() - t1

                mes = fe_dir / "OnLoadTorque_result_1.mes"
                if not mes.exists():
                    cand = sorted(fe_dir.glob("OnLoadTorque_result_*.mes"),
                                  key=lambda p: p.stat().st_mtime,
                                  reverse=True)
                    if not cand:
                        raise FileNotFoundError("OnLoadTorque .mes 없음")
                    mes = cand[0]

                dst_dir.mkdir(parents=True, exist_ok=True)
                tmp_txt = dst_dir / "FEA_data.txt"
                tp = int(mc.get_variable("TorquePointsPerCycle"))
                mc.save_fea_data(str(tmp_txt), 1, tp, EXPORT_COLUMNS,
                                 "", ",")
                sz = tmp_txt.stat().st_size / 1e6
                gzip_file(tmp_txt, dst_gz)
                tmp_txt.unlink()
                dst_res = dst_dir / "FEResultsData"
                if dst_res.exists():
                    shutil.rmtree(dst_res)
                shutil.copytree(fe_dir, dst_res)
                done += 1
                el = time.time() - t0
                eta = el / done * (len(ops) - i - 1) / 60
                print(f"  [{i+1}/{len(ops)}] {name}: solve {t_solve:.0f}s"
                      f" txt {sz:.0f} MB -> gz"
                      f"  (ETA {eta:.0f}min)", flush=True)
            except Exception as ex:
                fail += 1
                print(f"  [{i+1}/{len(ops)}] {name}: 실패 {ex}", flush=True)
    finally:
        try:
            mc.quit()
        except Exception:
            pass
    print(f"완료 {done} / 건너뜀 {skip} / 실패 {fail}"
          f"  ({(time.time()-t0)/60:.0f}min)", flush=True)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
