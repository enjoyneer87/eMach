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


def split_dataset(ds, lut, t_r_m, t_t_m, f_theta, tag, fth_fn=None):
    """단일 g 데이터셋 -> 성분별 분모 데이터셋 (hybrid/AF 치환).

    fth_fn(irms, phase) 가 주어지면 운전점별 f_theta 를 쓰고 (per-OP 모드),
    없으면 상수 f_theta 를 쓴다 (§12.5 근사 모드).
    """
    pts, miss, tolbad = [], 0, 0.0
    fth_used = []
    for i, p in enumerate(ds.points):
        key = (round(p.speed_rpm), round(p.current_rms, 1),
               round(p.phase_deg, 1))
        if key not in lut:
            miss += 1
            pts.append(p)
            continue
        fth = f_theta if fth_fn is None else fth_fn(p.current_rms,
                                                    p.phase_deg)
        fth_used.append(fth)
        R = float(R_of_speed([p.speed_rpm], t_r_m, t_t_m, fth)[0])
        skin, prox = lut[key]
        tolbad = max(tolbad, abs(skin + prox - p.hybrid_ac_kW)
                     / max(p.hybrid_ac_kW, 1e-9))
        h_split = skin + prox / R
        pts.append(replace(p, hybrid_ac_kW=h_split,
                           AF=p.fea_ac_kW / h_split))
    if miss:
        print(f"  [{tag}] 경고: 레코드 매칭 실패 {miss}점 (원본 유지)")
    note = (f"f_th {np.min(fth_used):.3f}~{np.max(fth_used):.3f}"
            if fth_fn is not None and fth_used else f"f_th={f_theta:.3f} 상수")
    print(f"  [{tag}] skin+prox 정합 {tolbad:.1e}  ({note})")
    return AcLossDataset(points=pts)


def load_fth_table(fth_json_path, tag=""):
    """per-OP f_theta JSON -> ((I,b) 셀 -> 속도 평균 f_theta) 조회 함수.

    표는 해당 모델 **자체 전류 좌표**로 키가 잡혀 있다 (백필 Hybrid export
    를 자체 기하에서 스캔한 것 -- 상사 가정 불필요).
    """
    d = json.load(open(fth_json_path, encoding="utf-8"))
    combos = {}
    for v in d.values():
        combos.setdefault((v["irms_A"], v["phase_deg"]),
                          []).append(v["f_theta"])
    keys = np.array(list(combos.keys()))
    vals = np.array([float(np.mean(v)) for v in combos.values()])
    spread = float(np.mean([np.std(v) for v in combos.values()]))
    print(f"  [{tag}] f_theta 표 {len(vals)}셀, 속도 간 산포 {spread:.4f},"
          f"  I {keys[:, 0].min():g}~{keys[:, 0].max():g} A")

    def fn(irms, phase):
        d2 = ((keys[:, 0] - irms) / 100.0) ** 2 + ((keys[:, 1] - phase)
                                                   / 18.0) ** 2
        return float(vals[int(np.argmin(d2))])

    return fn


def make_halfsc_fth(fn_ref, fn_sc):
    """HalfSC(I,b) 의 f_theta = 자체 표가 없으므로 상사 대응 셀의 평균.

    HalfSC (I, b) ~ Ref (I/1.5, b) ~ SC (4I/3, b). Ref/SC 자체 표가 모두
    측정값이므로 두 값의 평균을 쓰고, 그 차가 곧 구현 비상사성 오차 척도.
    """
    def fn(irms, phase):
        return 0.5 * (fn_ref(irms / K_H, phase)
                      + fn_sc(irms * K_S / K_H, phase))
    return fn


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
    pl2 = AcLossPipeline()                       # 성분별, f_theta 상수
    pl3 = None                                   # 성분별, per-OP f_theta
    fth_json = os.path.join(E10, "HalfSC", "fth_per_op.json")
    luts = {}
    print("\n데이터셋 변환:")
    for m in ("Ref", "HalfSC", "SC"):
        ds = pl1.load_dataset(m)
        luts[m] = load_skinprox(m, pl1.cfg["json"][m])
        pl2._datasets[m] = split_dataset(
            ds, luts[m], geo[m]["t_r_m"], geo[m]["t_t_m"], fth[m], m)
    fth_ref_json = os.path.join(E10, "Ref", "fth_per_op_Ref.json")
    fth_sc_json = os.path.join(E10, "SC", "fth_per_op_SC.json")
    if os.path.exists(fth_ref_json) and os.path.exists(fth_sc_json):
        pl3 = AcLossPipeline()
        print("per-OP f_theta (모델별 자체 표, 백필 Hybrid export):")
        fn_ref = load_fth_table(fth_ref_json, "Ref")
        fn_sc = load_fth_table(fth_sc_json, "SC")
        fns = {"Ref": fn_ref, "SC": fn_sc,
               "HalfSC": make_halfsc_fth(fn_ref, fn_sc)}
        # 교차 검증 1: 8블록 아카이브 실측과 표 대응 셀
        print(f"  [QA] Ref(460,36) 표 {fn_ref(460, 36):.4f}"
              f" vs 아카이브 0.7255 | SC(920,36) 표 {fn_sc(920, 36):.4f}"
              f" vs 0.7485")
        # 교차 검증 2: Ref-SC 상사 대응 셀 전수 편차 (구현 비상사성 척도)
        dif = []
        for irms in (115.1, 230.0, 345.0, 460.0):
            for ph in (0.0, 18.0, 36.0, 54.0, 72.0, 90.0):
                dif.append(abs(fn_ref(irms, ph) - fn_sc(2 * irms, ph)))
        print(f"  [QA] Ref vs SC(2I) 대응 24셀 |dF_th|:"
              f" 평균 {np.mean(dif):.4f}, 최대 {np.max(dif):.4f}")
        for m in ("Ref", "HalfSC", "SC"):
            pl3._datasets[m] = split_dataset(
                pl1.load_dataset(m), luts[m], geo[m]["t_r_m"],
                geo[m]["t_t_m"], None, m, fth_fn=fns[m])
    else:
        print("per-OP f_theta 표 미비 --- 2세계만 비교")

    # ── 사다리 비교 ────────────────────────────────────────────────
    res1 = ladder(pl1, "단일 g 분모 (현행)")
    res2 = ladder(pl2, "성분별 분모 (f_theta 상수)")
    res3 = ladder(pl3, "성분별 분모 (per-OP f_theta)") if pl3 else None

    print("\n요약 (wMAE%): 단일 / 성분별-상수 / 성분별-perOP")
    for tag in ("A_uncorrected", "B_own27", "C_zeroshot_SC",
                "E_zeroshot_mixed", "F_zeroshot_plus3"):
        row = f"  {tag:<18} {res1[tag]['wmae_pct']:6.2f}" \
              f" {res2[tag]['wmae_pct']:6.2f}"
        if res3:
            row += f" {res3[tag]['wmae_pct']:6.2f}"
        print(row)

    out = {"single_g": res1, "component_split_constfth": res2,
           "component_split_perop": res3,
           "_meta": {"f_theta_snapshot": fth,
                     "geometry_mm": {m: {"t_r": geo[m]["t_r_mm"],
                                         "t_t": geo[m]["t_t_mm"]}
                                     for m in geo},
                     "sigma": SIGMA,
                     "note": "R 기본파 기준. per-OP 모드: Ref/SC 는 백필 "
                             "Hybrid export 에서 잰 자체 f_theta(I,b) 표, "
                             "HalfSC 는 상사 대응 셀(Ref I/1.5, SC 4I/3) "
                             "평균 -- 두 표의 차가 곧 구현 비상사성."}}
    json.dump(out, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
