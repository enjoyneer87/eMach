# -*- coding: utf-8 -*-
"""(b) 공개 분모 데모 — SC의 AF를 표본선+전환 캡 분모로 재적합.

분모 스왑: hybrid <- line_msq_P24c6_translim + skin_excess (자유 파라미터 0의
공개 구현 \\cite{kang2026emachacloss}; run_line_sampled_hybrid.py --speed 0 산출).
채택 플랜(24+3) 그대로 재적합해 전 맵 wMAE를 구 분모(해석-FEA 추출)와 비교하고,
속도별 분모 비(공개/해석-FEA)로 f_t 오차 vs 표본 B 편향을 판별한다:
  - f_t 오차라면: 저속(기본파 비캡)과 16k(전캡)의 비가 구조적으로 갈림
  - B 편향이라면: 전 속도 평탄

산출: map_exports/e10/SC/open_denominator_refit.json
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import replace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline         # noqa: E402
from jeet_acloss_rbf.AcLossDataset import AcLossDataset     # noqa: E402

# 데이터 루트는 JEET_DATA_ROOT 로 덮어쓸 수 있다 (배포 레포/CI 용).
E10 = os.environ.get("JEET_DATA_ROOT",
                     os.path.join(HERE, "map_exports", "e10"))
SRC = os.path.join(E10, "SC", "line_sampled_hybrid_SC_80C.json")
OUT = os.path.join(E10, "SC", "open_denominator_refit.json")


def main() -> int:
    d = json.load(open(SRC, encoding="utf-8"))
    lut, ratio_rows = {}, []
    for r in d["rows"]:
        prox = r.get("line_msq_P24c6_translim")
        skin = r.get("skin_excess_W")
        if prox is None or skin is None:
            continue
        key = (round(r["speed_rpm"]), round(r["current_A"], 1),
               round(r["phase_deg"], 1))
        lut[key] = (prox + skin) / 1e3                      # kW
        if r.get("mcad_prox_W") and r.get("mcad_skin_W"):
            ratio_rows.append(
                (r["speed_rpm"],
                 (prox + skin) / (r["mcad_prox_W"] + r["mcad_skin_W"])))

    # 속도별 분모 비 → f_t vs B 편향 판별
    by_spd = {}
    for spd, rr in ratio_rows:
        by_spd.setdefault(spd, []).append(rr)
    print("=== 속도별 공개/해석-FEA 분모 비 (평균±표준편차) ===")
    spd_ratio = {}
    for spd in sorted(by_spd):
        v = np.array(by_spd[spd])
        spd_ratio[str(spd)] = [round(float(v.mean()), 3),
                               round(float(v.std()), 3)]
        print(f"  {spd:>6d} RPM: {v.mean():.3f} ± {v.std():.3f}  (n={len(v)})")

    pl_old = AcLossPipeline()
    pl_new = AcLossPipeline()
    ds = pl_old.load_dataset("SC")
    pts, miss = [], 0
    for p in ds.points:
        key = (round(p.speed_rpm), round(p.current_rms, 1),
               round(p.phase_deg, 1))
        h_new = lut.get(key)
        if h_new is None or h_new <= 0:
            miss += 1
            continue
        pts.append(replace(p, hybrid_ac_kW=h_new, AF=p.fea_ac_kW / h_new))
    print(f"\n데이터셋 스왑: {len(ds.points)} -> {len(pts)}점 (미매칭 {miss})")
    pl_new._datasets["SC"] = AcLossDataset(points=pts)
    af = pl_new._datasets["SC"].af_arr
    print(f"공개 분모 AF 범위 {af.min():.3f}~{af.max():.3f} 평균 {af.mean():.3f}")

    out = {"per_speed_denominator_ratio": spd_ratio}
    for tag, pl in (("old", pl_old), ("new", pl_new)):
        dsx = pl.load_dataset("SC")
        mdl = pl.build_model("SC")
        pred = dsx.h_ac_arr * mdl.predict(dsx.speeds_k * 1000.0,
                                          dsx.irms_arr, dsx.phase_arr)
        e = np.abs((pred - dsx.f_ac_arr) / (dsx.f_ac_arr + 1e-12) * 100.0)
        wmae = float(np.sum(dsx.f_ac_arr * e) / np.sum(dsx.f_ac_arr))
        unc = np.abs((dsx.h_ac_arr - dsx.f_ac_arr)
                     / (dsx.f_ac_arr + 1e-12) * 100.0)
        wmae0 = float(np.sum(dsx.f_ac_arr * unc) / np.sum(dsx.f_ac_arr))
        out[tag] = {"uncorrected_wmae_pct": round(wmae0, 2),
                    "adopted_wmae_pct": round(wmae, 2)}
        print(f"[{tag}] 무보정 {wmae0:.2f}% -> 채택 플랜 {wmae:.2f}%")

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print("저장:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
