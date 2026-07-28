# -*- coding: utf-8 -*-
"""BVP 분모 AF 재적합 — 3-family 사다리 최종 비교 (저자 요청 2026-07-28).

분모 3종을 같은 파이프라인·같은 플랜으로 나란히 재적합한다:
    old   : 큐보이드 평균장 (생산 MCAD 추출)          AF ~ 2.25/1.51
    meshB : 요소 분해 조화 평가 (Volpe G2' + Dowell)  AF ~ 0.60~0.80
    BVP   : 도체별 복소 조화 2-D 확산 경계값 해       AF = 본 실험
입력: bvp_denominator_{Ref,HalfSC,SC}.json (run_bvp_denominator_map.py)
산출: map_exports/e10/HalfSC/bvp_af_refit_ladder.json
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import replace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
sys.path.insert(0, HERE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline         # noqa: E402
from jeet_acloss_rbf.AcLossDataset import AcLossDataset     # noqa: E402
from run_split_kernel_ladder import ladder                  # noqa: E402
from run_meshb_af_refit import meshb_lut, swap_dataset, MESHB  # noqa: E402

E10 = os.path.join(HERE, "map_exports", "e10")
BVP = {m: os.path.join(E10, m, f"bvp_denominator_{m}.json")
       for m in ("Ref", "HalfSC", "SC")}
OUT = os.path.join(E10, "HalfSC", "bvp_af_refit_ladder.json")


def bvp_lut(path):
    d = json.load(open(path, encoding="utf-8"))
    lut = {}
    for r in d["rows"]:
        v = r.get("bvp_ac_W")
        if v and v > 0:
            key = (round(r["speed_rpm"]), round(r["current_A"], 1),
                   round(r["phase_deg"], 1))
            lut[key] = v / 1e3                               # kW
    return lut


def main() -> int:
    pls = {"old": AcLossPipeline(), "meshB": AcLossPipeline(),
           "BVP": AcLossPipeline()}
    print("데이터셋 분모 스왑:")
    for m in ("Ref", "HalfSC", "SC"):
        ds = pls["old"].load_dataset(m)
        pls["meshB"]._datasets[m] = swap_dataset(ds, meshb_lut(MESHB[m]),
                                                 f"meshB/{m}")
        pls["BVP"]._datasets[m] = swap_dataset(ds, bvp_lut(BVP[m]),
                                               f"BVP/{m}")
        for tag in ("meshB", "BVP"):
            af = pls[tag]._datasets[m].af_arr
            print(f"      {tag}/{m} AF {af.min():.3f}~{af.max():.3f}"
                  f" 평균 {af.mean():.3f}", flush=True)

    res = {tag: ladder(pl, f"{tag} 분모") for tag, pl in pls.items()}

    print("\n요약 (HalfSC 사다리 wMAE%, old / meshB / BVP):")
    for t in ("A_uncorrected", "B_own27", "C_zeroshot_SC",
              "E_zeroshot_mixed", "F_zeroshot_plus3"):
        print(f"  {t:<18} " + "  ".join(
            f"{res[k][t]['wmae_pct']:6.2f}" for k in ("old", "meshB", "BVP")))

    own = {}
    for m in ("Ref", "SC"):
        for tag, pl in pls.items():
            ds = pl.load_dataset(m)
            mdl = pl.build_model(m)
            pred = ds.h_ac_arr * mdl.predict(
                ds.speeds_k * 1000.0, ds.irms_arr, ds.phase_arr)
            e = np.abs((pred - ds.f_ac_arr) / (ds.f_ac_arr + 1e-12) * 100.0)
            own[f"{m}_{tag}"] = float(np.sum(ds.f_ac_arr * e)
                                      / np.sum(ds.f_ac_arr))
    print("\n자체 플랜 wMAE% (old/meshB/BVP): "
          + "  ".join(f"{m} " + "/".join(
              f"{own[f'{m}_{t}']:.2f}" for t in ("old", "meshB", "BVP"))
              for m in ("Ref", "SC")))

    json.dump({"ladder": res, "own_plan_wmae": own,
               "_meta": {"families": {
                   "old": "cuboid-averaged production hybrid (MCAD)",
                   "meshB": "element-resolved harmonic (Volpe G2'+Dowell)",
                   "BVP": "per-conductor complex-harmonic 2-D diffusion "
                          "BVP, MS-frozen boundary (total-J minus DC)"}}},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
