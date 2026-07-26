# -*- coding: utf-8 -*-
"""SC Hybrid(MS) 필드 export -> HalfSC 캠페인 격자 상사 스케일본 생성.

사상 (MS 는 속도 무관 -> (I, beta) 조합만):
    HalfSC(I, b) ~ SC(4I/3, b),  좌표 배율 s = 1.5/2 = 0.75
    SC 전류 {0.1, 230.1, 460.1, 690, 920} -> HalfSC 라벨
             {0.1, 172.5, 345.0, 517.5, 690.0}   (캠페인 격자)

소스: 백필 SC Hybrid 16000RPM (필드는 속도 무관이므로 한 속도면 충분).
산출: D:\KangDH\Thesis\e10\_txt_backfill\HalfSC_scaledSC\
        HybridIB_{label}A_{ph}deg\FEA_data.txt.gz   (30조합)

검증(각 파일): 파싱 재확인 + 슬롯 도체 면적 합 == s^2 배 + f_theta 산출.

사용:  python run_scale_sc_to_halfsc.py [--shard K --nshards N] [--limit N]
"""
from __future__ import annotations

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from jeet_acloss_rbf.similarity_field_scale import scale_fea_txt  # noqa: E402

SRC_ROOT = r"D:\KangDH\Thesis\e10\_txt_backfill\SC"
DST_ROOT = r"D:\KangDH\Thesis\e10\_txt_backfill\HalfSC_scaledSC"
S = 1.5 / 2.0
SRC_SPEED = 16000
CUR_MAP = {"0.1": "0.1", "230.1": "172.5", "460.1": "345.0",
           "690.0": "517.5", "920.0": "690.0"}
PHASES = ["0.0", "18.0", "36.0", "54.0", "72.0", "90.0"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()

    combos = [(sc, hb, ph) for sc, hb in CUR_MAP.items() for ph in PHASES]
    if a.nshards > 1:
        combos = combos[a.shard::a.nshards]
    if a.limit:
        combos = combos[:a.limit]
    print(f"SC->HalfSC 상사 스케일: {len(combos)}조합 (s={S})", flush=True)

    t0, done, fail = time.time(), 0, 0
    for i, (sc_cur, hb_cur, ph) in enumerate(combos):
        src = os.path.join(
            SRC_ROOT, f"Hybrid_Speed_{SRC_SPEED}RPM_{sc_cur}A_{ph}deg",
            "FEA_data.txt.gz")
        dst_dir = os.path.join(DST_ROOT, f"HybridIB_{hb_cur}A_{ph}deg")
        dst = os.path.join(dst_dir, "FEA_data.txt.gz")
        if os.path.exists(dst) and os.path.getsize(dst) > 1e6:
            print(f"  [{i+1}/{len(combos)}] {hb_cur}A/{ph}: 스킵", flush=True)
            done += 1
            continue
        if not os.path.exists(src):
            print(f"  [{i+1}/{len(combos)}] 소스 없음: {src}", flush=True)
            fail += 1
            continue
        os.makedirs(dst_dir, exist_ok=True)
        try:
            t1 = time.time()
            st = scale_fea_txt(src, dst, S)
            done += 1
            el = time.time() - t0
            eta = el / done * (len(combos) - i - 1) / 60
            print(f"  [{i+1}/{len(combos)}] SC {sc_cur}A -> HalfSC {hb_cur}A"
                  f"/{ph}: {st['n_scaled_rows']}행 스케일,"
                  f" {time.time()-t1:.0f}s (ETA {eta:.0f}min)", flush=True)
        except Exception as ex:
            fail += 1
            print(f"  [{i+1}/{len(combos)}] 실패 {ex}", flush=True)
    print(f"완료 {done} / 실패 {fail}  ({(time.time()-t0)/60:.0f}min)",
          flush=True)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
