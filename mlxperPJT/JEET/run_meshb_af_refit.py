# -*- coding: utf-8 -*-
"""신규(mesh-B Volpe) 분모로 AF 재적합 + 제로샷 사다리 재실행.

분모 스왑: hybrid <- meshb_total_volpe (자체 필드 계산: Volpe G2' 근접 +
Dowell 표피, 순수 MS B), AF <- TS / meshb. 세 모델 데이터셋을 변환해
파이프라인 캐시에 주입하고, 채택 플랜 그대로 재적합한 뒤 HalfSC 사다리
(A/B/C/E/F)를 구 분모와 나란히 비교한다.

입력: meshb_hybrid_losses_{Ref,SC}.json + _HalfSC_campaign.json (360행).
산출: map_exports/e10/HalfSC/meshb_af_refit_ladder.json
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

E10 = os.path.join(HERE, "map_exports", "e10")
MESHB = {
    "Ref": os.path.join(E10, "Ref", "meshb_hybrid_losses_Ref.json"),
    "HalfSC": os.path.join(E10, "HalfSC",
                           "meshb_hybrid_losses_HalfSC_campaign.json"),
    "SC": os.path.join(E10, "SC", "meshb_hybrid_losses_SC.json"),
}
OUT = os.path.join(E10, "HalfSC", "meshb_af_refit_ladder.json")


def meshb_lut(path):
    d = json.load(open(path, encoding="utf-8"))
    lut = {}
    for r in d["rows"]:
        key = (round(r["speed_rpm"]), round(r["current_A"], 1),
               round(r["phase_deg"], 1))
        lut[key] = r["meshb_total_volpe_W"] / 1e3        # kW
    return lut


def swap_dataset(ds, lut, tag):
    pts, miss = [], 0
    for p in ds.points:
        key = (round(p.speed_rpm), round(p.current_rms, 1),
               round(p.phase_deg, 1))
        h_new = lut.get(key)
        if h_new is None or h_new <= 0:
            miss += 1
            continue                       # 신규 분모 없는 점은 제외
        pts.append(replace(p, hybrid_ac_kW=h_new,
                           AF=p.fea_ac_kW / h_new))
    print(f"  [{tag}] {len(ds.points)} -> {len(pts)}점"
          f" (미매칭 제외 {miss})", flush=True)
    return AcLossDataset(points=pts)


def main() -> int:
    pl1 = AcLossPipeline()                 # 구 분모 (MCAD 추출)
    pl2 = AcLossPipeline()                 # 신규 분모 (mesh-B)
    print("데이터셋 분모 스왑:")
    for m in ("Ref", "HalfSC", "SC"):
        ds = pl1.load_dataset(m)
        pl2._datasets[m] = swap_dataset(ds, meshb_lut(MESHB[m]), m)
        af = pl2._datasets[m].af_arr
        print(f"      신규 AF 범위 {af.min():.3f}~{af.max():.3f}"
              f"  평균 {af.mean():.3f}", flush=True)

    res1 = ladder(pl1, "구 분모 (MCAD 추출)")
    res2 = ladder(pl2, "신규 분모 (mesh-B Volpe)")

    print("\n요약 (wMAE%, 구 -> 신):")
    for tag in ("A_uncorrected", "B_own27", "C_zeroshot_SC",
                "E_zeroshot_mixed", "F_zeroshot_plus3"):
        a, b = res1[tag]["wmae_pct"], res2[tag]["wmae_pct"]
        print(f"  {tag:<18} {a:6.2f} -> {b:6.2f}  ({b - a:+.2f})")

    # Ref/SC 자체(채택 플랜) 정확도도 병기
    own = {}
    for m in ("Ref", "SC"):
        for pl, k in ((pl1, "old"), (pl2, "new")):
            ds = pl.load_dataset(m)
            mdl = pl.build_model(m)
            pred = ds.h_ac_arr * mdl.predict(
                ds.speeds_k * 1000.0, ds.irms_arr, ds.phase_arr)
            e = np.abs((pred - ds.f_ac_arr)
                       / (ds.f_ac_arr + 1e-12) * 100.0)
            own[f"{m}_{k}"] = float(np.sum(ds.f_ac_arr * e)
                                    / np.sum(ds.f_ac_arr))
    print(f"\n자체 플랜 wMAE%: Ref {own['Ref_old']:.2f}->{own['Ref_new']:.2f}"
          f"  SC {own['SC_old']:.2f}->{own['SC_new']:.2f}")

    json.dump({"old_denominator": res1, "new_denominator": res2,
               "own_plan_wmae": own,
               "_meta": {"denominator": "meshb_total_volpe (Volpe G2' prox"
                                        " + Dowell skin, own MS fields)",
                         "note": "HalfSC = campaign-grid own-field rows"}},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
