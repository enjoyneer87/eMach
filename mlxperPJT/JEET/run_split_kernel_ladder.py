# -*- coding: utf-8 -*-
"""성분별(이방성) 커널 분모 기준 AF 로 제로샷 사다리 재실행 — 분모 선택이
상사 전달·내삽에 유리한지 판정.

가설 (저자 질문): SC 의 AF 를 처음부터 성분별 근접 커널
    P_B = sum_m [ g(eta_tr) B_theta,m^2 + g(eta_tt) B_r,m^2 ]
기준으로 떠놨다면, k_r=2 -> 1.5 제로샷 내삽이 단일 g 기준보다 유리한가.

방법: 운전점별 B 분해(backup_dir)는 소실되어 근사 경로를 쓴다 —
  1) Map_Summary 레코드의 운전점별 skin/prox 분해 (존재 ✓)
  2) R_M(w) = P_prox_single/P_prox_split
            = G_t / (G_r f_theta + G_t (1-f_theta))   [proximity_anisotropy]
     여기서 f_theta 는 모델당 상수 (MS 스냅샷에서 추출 — MS 자계는 속도
     무관이므로 속도축은 정확, (I,beta) 변화는 미반영 = 한계로 명시)
  3) P_hyb_split(OP) = skin + prox / R_M(w),  AF_split = fea / P_hyb_split
  4) 세 모델 데이터셋을 split 기준으로 변환해 파이프라인 캐시에 주입,
     채택 플랜 그대로 재빌드 -> 사다리 A/B/C/E/F 재실행.

R 은 기본파 기준(proximity_anisotropy 관습). sigma 는 생산 파이프라인의
4.709e7 (약 55 degC) 로 통일.

실행:  python run_split_kernel_ladder.py
산출:  map_exports/e10/HalfSC/split_kernel_ladder.json
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
from jeet_acloss_rbf.proximity_anisotropy import (          # noqa: E402
    conductor_geometry, energy_split, kernel_factor)

SIGMA = 4.709e7                       # 생산 파이프라인 온도 기준
POLE_PAIRS = 4
K_H, K_S = 1.5, 2.0
E10 = os.path.join(HERE, "map_exports", "e10")
FLD = os.path.join(E10, "fields")
OUT = os.path.join(E10, "HalfSC", "split_kernel_ladder.json")

# 기하 추출용 TS 스냅샷(순동 치수), f_theta 용 MS 스냅샷
TS_SNAP = {
    "Ref":    "Magnetic_Ref_16k_36deg_OnLoadTorque.txt",
    "HalfSC": "Magnetic_HalfSC_16k_36deg_OnLoadTorque.txt",
    "SC":     "Magnetic_SC_16k_36deg_OnLoadTorque.txt",
}
MS_SNAP = {
    "Ref": "Magnetic_Ref_Hybrid_ARCHIVE_460A_36deg_full_OnLoadTorque.txt",
    "SC":  "Magnetic_SC_Hybrid_OP920A_36deg_OnLoadTorque.txt",
    # HalfSC: MS export 없음 -> SC 의 f_theta 재사용 (상사 논거)
}


def R_of_speed(rpm, t_r_m, t_t_m, f_theta):
    """R(w) = P_single/P_split (기본파 기준, 벡터화)."""
    rpm = np.asarray(rpm, float)
    out = np.empty_like(rpm)
    for i, r in enumerate(rpm):
        f_e = r / 60.0 * POLE_PAIRS
        G_r = kernel_factor(t_r_m, t_t_m, f_e, SIGMA)
        G_t = kernel_factor(t_t_m, t_r_m, f_e, SIGMA)
        out[i] = G_t / (G_r * f_theta + G_t * (1.0 - f_theta))
    return out


def load_skinprox(scale, json_rel):
    """Map_Summary 에서 (speed, I, phase) -> (skin, prox) 조회표.

    포맷 2종: dict{'records': [...]} (신) / list[...] (구, Ref).
    """
    d = json.load(open(os.path.join(E10, json_rel), encoding="utf-8"))
    records = d["records"] if isinstance(d, dict) else d
    lut, nokey = {}, 0
    for r in records:
        if r.get("mode") != "Hybrid":
            continue
        if "hybrid_skin_kW" not in r or "hybrid_prox_kW" not in r:
            nokey += 1
            continue
        key = (round(float(r["speed"])), round(float(r["current"]), 1),
               round(float(r["phase"]), 1))
        lut[key] = (float(r["hybrid_skin_kW"]), float(r["hybrid_prox_kW"]))
    if nokey:
        print(f"  [{scale}] 경고: skin/prox 키 없는 Hybrid 레코드 {nokey}건")
    return lut


def split_dataset(ds, lut, t_r_m, t_t_m, f_theta, tag):
    """단일 g 데이터셋 -> 성분별 분모 데이터셋 (hybrid/AF 치환)."""
    R = R_of_speed(ds.speeds_k * 1000.0, t_r_m, t_t_m, f_theta)
    pts, miss, tolbad = [], 0, 0.0
    for i, p in enumerate(ds.points):
        key = (round(p.speed_rpm), round(p.current_rms, 1),
               round(p.phase_deg, 1))
        if key not in lut:
            miss += 1
            pts.append(p)
            continue
        skin, prox = lut[key]
        tolbad = max(tolbad, abs(skin + prox - p.hybrid_ac_kW)
                     / max(p.hybrid_ac_kW, 1e-9))
        h_split = skin + prox / R[i]
        pts.append(replace(p, hybrid_ac_kW=h_split,
                           AF=p.fea_ac_kW / h_split))
    if miss:
        print(f"  [{tag}] 경고: 레코드 매칭 실패 {miss}점 (원본 유지)")
    print(f"  [{tag}] skin+prox 대 hybrid 총량 최대 상대편차 {tolbad:.2e}")
    return AcLossDataset(points=pts)


def err_stats(f_ac, pred):
    e = np.abs((pred - f_ac) / (f_ac + 1e-12) * 100.0)
    return {"mae_pct": float(e.mean()),
            "wmae_pct": float(np.sum(f_ac * e) / np.sum(f_ac)),
            "p95_pct": float(np.percentile(e, 95)),
            "max_pct": float(e.max())}


def ladder(pl, label):
    """run_halfsc_zeroshot 의 A/B/C/E/F 를 주어진 파이프라인으로 실행."""
    ds = pl.load_dataset("HalfSC")
    f_ac, h_ac = ds.f_ac_arr, ds.h_ac_arr        # h_ac = 해당 분모 기준
    w = ds.speeds_k * 1000.0
    res = {}

    pred_A = h_ac.copy()
    m_half = pl.build_model("HalfSC")
    pred_B = h_ac * m_half.predict(w, ds.irms_arr, ds.phase_arr)
    m_sc = pl.build_model("SC")
    af_C = m_sc.predict(w * (K_H / K_S) ** 2, ds.irms_arr * (K_S / K_H),
                        ds.phase_arr)
    m_ref = pl.build_model("Ref")
    af_D = m_ref.predict(w * K_H ** 2, ds.irms_arr / K_H, ds.phase_arr)
    hi = ds.speeds_k > 8.5
    pred_E = h_ac * np.where(hi, af_C, af_D)

    idx16 = np.where(hi)[0]
    af_zs = af_C[idx16]
    order = np.argsort(af_zs)
    pick = [order[0], order[len(order) // 2], order[-1]]
    x = np.log(np.clip(af_zs[pick], 1e-3, None))
    y = np.log(np.clip(ds.af_arr[idx16][pick], 1e-3, None))
    p_c, logf_c = np.polyfit(x, y, 1)
    af_F = np.where(hi, np.exp(logf_c) * np.clip(af_C, 1e-3, None) ** p_c,
                    af_D)
    pred_F = h_ac * af_F

    for tag, pred in (("A_uncorrected", pred_A), ("B_own27", pred_B),
                      ("C_zeroshot_SC", h_ac * af_C),
                      ("E_zeroshot_mixed", pred_E),
                      ("F_zeroshot_plus3", pred_F)):
        res[tag] = err_stats(f_ac, pred)
    res["_anchor"] = {"f_c": float(np.exp(logf_c)), "p_c": float(p_c)}
    print(f"\n=== {label} ===")
    print(f"{'변형':<18}{'wMAE%':>8}{'MAE%':>8}{'p95%':>8}{'max%':>8}")
    for tag in ("A_uncorrected", "B_own27", "C_zeroshot_SC",
                "E_zeroshot_mixed", "F_zeroshot_plus3"):
        o = res[tag]
        print(f"{tag:<18}{o['wmae_pct']:>8.2f}{o['mae_pct']:>8.2f}"
              f"{o['p95_pct']:>8.2f}{o['max_pct']:>8.2f}")
    print(f"  (재앵커 f_c={res['_anchor']['f_c']:.4f},"
          f" p_c={res['_anchor']['p_c']:.4f})")
    return res


def main() -> int:
    # ── 기하·f_theta ────────────────────────────────────────────────
    geo, fth = {}, {}
    for m, fn in TS_SNAP.items():
        g = conductor_geometry(os.path.join(FLD, fn))
        geo[m] = g
        print(f"[{m}] t_r={g['t_r_mm']:.3f}  t_t={g['t_t_mm']:.3f} mm"
              f"  (도체 {g['n_bars']}개)")
    for m, fn in MS_SNAP.items():
        e = energy_split(os.path.join(FLD, fn))
        fth[m] = e["f_theta"]
        print(f"[{m}] f_theta={e['f_theta']:.3f}  (B_t rms {e['bt_rms_T']:.3f}"
              f" / B_r rms {e['br_rms_T']:.3f} T)")
    fth["HalfSC"] = fth["SC"]
    print(f"[HalfSC] f_theta={fth['HalfSC']:.3f}  (SC 재사용 — MS export 없음)")

    # R(w) 프로파일 출력 (사상 대역 포함)
    spds = np.array([1125, 2000, 4000, 4500, 8000, 9000, 16000], float)
    print("\nR(w) = P_single/P_split  (기본파):")
    print("  rpm   " + "".join(f"{int(s):>7}" for s in spds))
    for m in ("Ref", "HalfSC", "SC"):
        Rv = R_of_speed(spds, geo[m]["t_r_m"], geo[m]["t_t_m"], fth[m])
        print(f"  {m:<6}" + "".join(f"{r:>7.3f}" for r in Rv))

    # ── 데이터셋 변환 + 주입 ────────────────────────────────────────
    pl1 = AcLossPipeline()                       # 단일 g (원본)
    pl2 = AcLossPipeline()                       # 성분별 분모
    print("\n데이터셋 변환:")
    for m in ("Ref", "HalfSC", "SC"):
        ds = pl1.load_dataset(m)
        lut = load_skinprox(m, pl1.cfg["json"][m])
        pl2._datasets[m] = split_dataset(
            ds, lut, geo[m]["t_r_m"], geo[m]["t_t_m"], fth[m], m)

    # ── 사다리 비교 ────────────────────────────────────────────────
    res1 = ladder(pl1, "단일 g 분모 (현행)")
    res2 = ladder(pl2, "성분별 커널 분모 (가설)")

    print("\n요약 (wMAE%, 단일 -> 성분별):")
    for tag in ("A_uncorrected", "B_own27", "C_zeroshot_SC",
                "E_zeroshot_mixed", "F_zeroshot_plus3"):
        a, b = res1[tag]["wmae_pct"], res2[tag]["wmae_pct"]
        print(f"  {tag:<18} {a:6.2f} -> {b:6.2f}  ({b - a:+.2f})")

    out = {"single_g": res1, "component_split": res2,
           "_meta": {"f_theta": fth,
                     "geometry_mm": {m: {"t_r": geo[m]["t_r_mm"],
                                         "t_t": geo[m]["t_t_mm"]}
                                     for m in geo},
                     "sigma": SIGMA,
                     "note": "R 기본파 기준·f_theta 모델당 상수 (MS 스냅샷). "
                             "(I,beta) 의존 미반영 = 근사 한계."}}
    json.dump(out, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
