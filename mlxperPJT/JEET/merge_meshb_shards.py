# -*- coding: utf-8 -*-
"""mesh-B 샤드 JSON 병합 + 분모 교체 효과 요약."""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np                                     # noqa: E402

E10 = os.path.join(HERE, "map_exports", "e10")

for model in ("Ref", "HalfSC", "SC"):
    shards = sorted(glob.glob(os.path.join(
        E10, model, f"meshb_hybrid_losses_{model}_s*.json")))
    rows, meta = [], None
    for p in shards:
        d = json.load(open(p, encoding="utf-8"))
        rows += d["rows"]
        meta = meta or d["_meta"]
    rows.sort(key=lambda r: (r["speed_rpm"], r["current_A"],
                             r["phase_deg"]))
    out = os.path.join(E10, model, f"meshb_hybrid_losses_{model}.json")
    meta = dict(meta or {}, merged_from=[os.path.basename(p)
                                         for p in shards])
    json.dump({"rows": rows, "_meta": meta},
              open(out, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)

    # 요약: AF 정의별 분포 (0.1A 링 제외 — AF 무정의)
    # mcad_reference 는 total_W 를 채우지 않으므로 prox+skin 으로 합산
    sel = [r for r in rows if r["current_A"] > 1 and r.get("ts_ac_W")
           and r.get("mcad_prox_W") is not None
           and r.get("mcad_skin_W") is not None]
    ts = np.array([r["ts_ac_W"] for r in sel])
    mc = np.array([r["mcad_prox_W"] + r["mcad_skin_W"] for r in sel])
    vt = np.array([r["meshb_total_volpe_W"] for r in sel])
    af_mc = ts / mc
    af_vt = ts / vt
    print(f"[{model}] {len(rows)}행 병합 -> {os.path.basename(out)}")
    print(f"   AF(TS/MCAD추출): 평균 {af_mc.mean():.3f}"
          f"  범위 {af_mc.min():.2f}~{af_mc.max():.2f}")
    print(f"   AF(TS/meshB Volpe): 평균 {af_vt.mean():.3f}"
          f"  범위 {af_vt.min():.2f}~{af_vt.max():.2f}"
          f"  (유효 {len(sel)}점)")
