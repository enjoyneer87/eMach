# -*- coding: utf-8 -*-
"""운전점별 f_theta 스캔 — HalfSC Hybrid FEA_data.txt 106개에서 추출.

f_theta(I,beta) = sum B_theta^2 / sum (B_r^2 + B_theta^2)  (도체 평균장,
슬롯 1..6, 선택 블록들의 B^2 합 = 주기 평균 근사).

정자기량이므로 속도 무관 -> (I,beta) 조합별로 속도 간 평균·산포 보고.
세 모델 전류 격자가 상사 정렬(Ref x1.5 = HalfSC, SC x0.75 = HalfSC)이라
HalfSC 표 하나로 Ref/SC 의 f_theta 도 좌표 재척도로 얻는다 (f_theta 는
상사 불변 — 검증: Ref/SC 스냅샷 0.712/0.736 과 대응 셀 비교).

실행:  python scan_fth_per_op.py [--limit N]
산출:  map_exports/e10/HalfSC/fth_per_op.json
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from jeet_acloss_rbf.field_metrics import (                 # noqa: E402
    _locate_blocks, _parse_regions, _build_block_dict,
    slot_conductor_codes, _tangential_b)

ROOT = r"D:\KangDH\Thesis\e10\SLFEA_Half\ACLossCalcExport_Map"
OUT = os.path.join(HERE, "map_exports", "e10", "HalfSC", "fth_per_op.json")
BLOCK_PICK = [1, 17, 33, 49, 65, 81, 97, 113]     # 128 중 8개 등간격
SLOTS = range(1, 7)                               # energy_split 관습
_DIR_RE = re.compile(
    r"Hybrid_Speed_(\d+)RPM_([\d.]+)A_([\d.]+)deg$")


def fth_of_file(path: str) -> dict:
    """선택 블록들에서 도체 평균장 기반 f_theta (.txt 또는 .txt.gz)."""
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()
    blocks, regions_tbl = _locate_blocks(lines)
    S_t = S_r = 0.0
    used = 0
    for bi in BLOCK_PICK:
        if bi > len(blocks):
            continue
        blk = blocks[bi - 1]
        names, jval, sigma = _parse_regions(
            lines, blk['tables'].get('RegionsTable', regions_tbl))
        p = _build_block_dict(lines, blk, names, jval, sigma, path,
                              len(blocks))
        x, y = p['x_mm'], p['y_mm']
        r = np.hypot(x, y)
        br = (p['bx'] * x + p['by'] * y) / r
        bt = _tangential_b(p)
        area = p['area_mm2']
        codes = set()
        for s in SLOTS:
            codes |= slot_conductor_codes(p, s)
        for c in sorted(codes):
            m = p['reg'] == c
            if not m.any():
                continue
            w = area[m]
            Br = np.sum(w * br[m]) / np.sum(w)
            Bt = np.sum(w * bt[m]) / np.sum(w)
            S_r += Br ** 2
            S_t += Bt ** 2
        used += 1
    tot = S_r + S_t
    return {"f_theta": S_t / tot if tot > 0 else float("nan"),
            "n_blocks": used, "n_total_blocks": len(blocks)}


def main() -> int:
    limit = None
    root, out_path = ROOT, OUT
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if "--root" in sys.argv:
        root = sys.argv[sys.argv.index("--root") + 1]
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    globals()["OUT"] = out_path
    dirs = sorted(glob.glob(os.path.join(root, "Hybrid_Speed_*")))
    if limit:
        dirs = dirs[:limit]
    print(f"Hybrid 폴더 {len(dirs)}개 스캔 (블록 {BLOCK_PICK})  root={root}")
    out, t0 = {}, time.time()
    for i, d in enumerate(dirs):
        m = _DIR_RE.search(os.path.basename(d))
        if not m:
            continue
        spd, irms, ph = int(m.group(1)), float(m.group(2)), float(m.group(3))
        f = os.path.join(d, "FEA_data.txt")
        if not os.path.exists(f):
            f = os.path.join(d, "FEA_data.txt.gz")
        if not os.path.exists(f):
            print(f"  누락: {os.path.basename(d)}")
            continue
        r = fth_of_file(f)
        key = f"{spd}|{irms:g}|{ph:g}"
        out[key] = {"speed_rpm": spd, "irms_A": irms, "phase_deg": ph,
                    **r}
        el = time.time() - t0
        print(f"  [{i + 1}/{len(dirs)}] {os.path.basename(d):>44s}"
              f"  f_th={r['f_theta']:.4f}  ({el:5.0f}s)")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}  ({len(out)}개 OP)")

    # (I,beta) 조합별 속도 간 산포 QA
    combos = {}
    for v in out.values():
        combos.setdefault((v["irms_A"], v["phase_deg"]),
                          []).append(v["f_theta"])
    print("\n(I,beta) 조합별 f_theta  [속도 평균 ± 속도 간 산포]:")
    for (irms, ph) in sorted(combos):
        vs = np.array(combos[(irms, ph)])
        print(f"  I={irms:7.1f}A  b={ph:4.0f}deg :"
              f"  {vs.mean():.4f} ± {vs.std():.4f}  (n={len(vs)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
