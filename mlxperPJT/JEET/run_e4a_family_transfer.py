# -*- coding: utf-8 -*-
"""e4a 상사 패밀리 전달 검증 — 논문 핵심 파이프라인의 2차 패밀리 재현.

패밀리: e4a-Ref (donor, kturn4 배치) / e4a-SC (k_r=2 변형체, kturn20 배치).
상사 사상 (k_a=1, k_w=1):
    AF_SC(w, I, b) = AF_Ref(k_r^2 w, I/k_r, b) = AF_Ref(4w, I/2, b)
  전류 사상 I/2: SC {125,250,375,500} → Ref {62.5,125,187.5,250} (격자 일치)
  속도 사상 4w: SC {928,1856,3712} → Ref {3712,7424,14848} (인밴드)
               SC {7425,14850} → Ref {29.7k,59.4k} (외삽 대역 — 사다리)

검증 4종 + 불변량 1종:
  A. 무보정 (AF=1)
  C. 제로샷 via Ref donor (SC TS-FEA 0점) — 인밴드/외삽 대역 분리 보고
  F. 제로샷 + 외삽 속도별 +3 재앵커 (κ-스팬 결정론 배치, 논문 패턴)
  B. SC 자체 레시피 (§4.2: base 12 maximin + 저속 κ-스팬 3점씩 = 24점)
  P. 손실 보존 상사쌍: P_TS,SC(w, 2I, b) ≈ P_TS,Ref(4w, I, b) (인밴드 72쌍)
     [SLFEA k_w=1: J x1/2, V_cu x4 → 활성 DC·AC 손실 절대 보존]

산출: map_exports/e10/e4a_family_transfer.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np                                          # noqa: E402
from scipy.interpolate import RBFInterpolator               # noqa: E402

REF_SRC = r"D:\KangDH\Thesis\e4a\newfam_results\kturn4\JEET_ACLoss_kturn4_Map_Summary.json"
SC_SRC = (sys.argv[1] if len(sys.argv) > 1 else
          r"D:\KangDH\Thesis\e4a\newfam_results\kturn20\JEET_ACLoss_kturn20_Map_Summary.json")
OUT = (sys.argv[2] if len(sys.argv) > 2 else
       os.path.join(HERE, "map_exports", "e10", "e4a_family_transfer.json"))
K_R = 2.0
REF_BASE, REF_IMAX, REF_HELD_I = 14850, 250.0, 156.25
SC_BASE = 14850
SC_INBAND = (928, 1856, 3712)


def load_pairs(path):
    d = json.load(open(path, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    hyb = {(r["speed"], r["current"], r["phase"]): r["hybrid_total_kW"]
           for r in recs if r.get("proximity_model") == 1
           and "hybrid_total_kW" in r}
    ts = {(r["speed"], r["current"], r["phase"]): r["ts_ac_active_only_kW"]
          for r in recs if r.get("proximity_model") == 3
          and "ts_ac_active_only_kW" in r}
    keys = sorted(set(hyb) & set(ts))
    return (keys,
            np.array([k[0] for k in keys], float),
            np.array([k[1] for k in keys], float),
            np.array([k[2] for k in keys], float),
            np.array([hyb[k] for k in keys]),
            np.array([ts[k] for k in keys]))


def maximin_order(X):
    picked = [int(np.argmin(((X - X.mean(0)) ** 2).sum(1)))]
    dist = np.sqrt(((X - X[picked[0]]) ** 2).sum(1))
    for _ in range(len(X) - 1):
        nxt = int(np.argmax(dist))
        picked.append(nxt)
        dist = np.minimum(dist, np.sqrt(((X - X[nxt]) ** 2).sum(1)))
    return np.array(picked)


def err_stats(f_ac, pred):
    e = np.abs((pred - f_ac) / (f_ac + 1e-12) * 100.0)
    return {"mae_pct": round(float(e.mean()), 2),
            "wmae_pct": round(float(np.sum(f_ac * e) / np.sum(f_ac)), 2),
            "p95_pct": round(float(np.percentile(e, 95)), 2),
            "max_pct": round(float(e.max()), 2)}


class DonorModel:
    """e4a-Ref 분리형 모델: κ TPS(base) + 속도별 (f,p), log-ω 선형 보간/외삽."""

    def __init__(self, spd, cur, ph, af, base_rpm, i_max, held_i):
        xy = np.column_stack([cur / i_max, ph / 90.0])
        base_m = (spd == base_rpm) & (np.abs(cur - held_i) > 1.0)
        self.kap = RBFInterpolator(xy[base_m], af[base_m],
                                   kernel="thin_plate_spline")
        self.i_max = i_max
        kv = np.clip(self.kap(xy), 1e-6, None)
        fp = {base_rpm: (1.0, 1.0)}
        for s in sorted(set(spd.astype(int))):
            if s == base_rpm:
                continue
            cand = np.where(spd == s)[0]
            A = np.vstack([np.ones(len(cand)), np.log(kv[cand])]).T
            (lf, p_s), *_ = np.linalg.lstsq(A, np.log(af[cand]), rcond=None)
            fp[s] = (float(np.exp(lf)), float(p_s))
        self.fp = fp
        ss = np.array(sorted(fp), float)
        self.logs = np.log(ss)
        self.lf = np.array([np.log(fp[int(s)][0]) for s in ss])
        self.pp = np.array([fp[int(s)][1] for s in ss])

    def _interp(self, logw, ys):
        # log-ω 선형 보간 + 경계 기울기 외삽
        return np.interp(logw, self.logs, ys,
                         left=ys[0] + (logw - self.logs[0])
                         * (ys[1] - ys[0]) / (self.logs[1] - self.logs[0]),
                         right=ys[-1] + (logw - self.logs[-1])
                         * (ys[-1] - ys[-2]) / (self.logs[-1] - self.logs[-2]))

    def _interp_arr(self, logw, ys):
        out = np.interp(logw, self.logs, ys)
        lo = logw < self.logs[0]
        hi = logw > self.logs[-1]
        out[lo] = ys[0] + (logw[lo] - self.logs[0]) \
            * (ys[1] - ys[0]) / (self.logs[1] - self.logs[0])
        out[hi] = ys[-1] + (logw[hi] - self.logs[-1]) \
            * (ys[-1] - ys[-2]) / (self.logs[-1] - self.logs[-2])
        return out

    def predict(self, w_rpm, irms, phase):
        logw = np.log(np.asarray(w_rpm, float))
        xy = np.column_stack([np.asarray(irms, float) / self.i_max,
                              np.asarray(phase, float) / 90.0])
        kv = np.clip(self.kap(xy), 1e-6, None)
        f_w = np.exp(self._interp_arr(logw, self.lf))
        p_w = self._interp_arr(logw, self.pp)
        return f_w * kv ** p_w


def main() -> int:
    kr, kt, kc, kp, rh, rf = load_pairs(REF_SRC)
    print(f"[donor Ref] TS 쌍 {len(kr)}개, 속도 {sorted(set(kt.astype(int)))}")
    if not os.path.exists(SC_SRC):
        print(f"[대기] SC 스윕 요약 없음: {SC_SRC}")
        return 1
    ks, st, sc, sp, sh, sf = load_pairs(SC_SRC)
    n_by_speed = {int(s): int((st == s).sum()) for s in sorted(set(st))}
    print(f"[target SC] TS 쌍 {len(ks)}개, 속도별 {n_by_speed}")
    if len(ks) == 0:
        print("[대기] SC TS 쌍 0개 — 스윕 진행 중")
        return 1

    af_sc = sf / sh
    donor = DonorModel(kt, kc, kp, rf / rh, REF_BASE, REF_IMAX, REF_HELD_I)
    inband = np.isin(st.astype(int), SC_INBAND)

    # A. 무보정
    pred_A = sh.copy()

    # C. 제로샷: AF_Ref(4w, I/2, b)
    af_C = donor.predict(st * K_R**2, sc / K_R, sp)
    pred_C = sh * af_C

    # F. 제로샷 + 외삽 속도별 +3 재앵커 (κ-스팬: log AF_zs min/med/max)
    af_F = af_C.copy()
    anchors = {}
    for s in sorted(set(st.astype(int))):
        if s in SC_INBAND:
            continue
        idx = np.where(st == s)[0]
        if len(idx) < 3:
            continue
        zs = np.clip(af_C[idx], 1e-3, None)
        order = np.argsort(zs)
        pick = [order[0], order[len(order) // 2], order[-1]]
        x = np.log(zs[pick])
        y = np.log(np.clip(af_sc[idx][pick], 1e-3, None))
        p_c, logf_c = np.polyfit(x, y, 1)
        af_F[idx] = float(np.exp(logf_c)) * zs ** p_c
        anchors[str(s)] = {
            "ops": [(float(sc[idx[j]]), float(sp[idx[j]])) for j in pick],
            "f_c": round(float(np.exp(logf_c)), 4),
            "p_c": round(float(p_c), 4)}
    pred_F = sh * af_F

    # B. SC 자체 레시피: base(최고속) maximin 12 + 하위 속도 κ-스팬 3점씩
    xy_sc = np.column_stack([sc / sc.max(), sp / 90.0])
    base_idx = np.where(st == SC_BASE)[0]
    res_B = None
    if len(base_idx) >= 12:
        order = base_idx[maximin_order(xy_sc[base_idx])]
        own = order[:12].tolist()
        kap = RBFInterpolator(xy_sc[own], af_sc[own],
                              kernel="thin_plate_spline")
        kv = np.clip(kap(xy_sc), 1e-6, None)
        fp = {SC_BASE: (1.0, 1.0)}
        used_all = set(own)
        for s in sorted(set(st.astype(int))):
            if s == SC_BASE:
                continue
            cand = np.where(st == s)[0]
            kvv = np.log(kv[cand])
            rk = np.argsort(kvv)
            picks = cand[[rk[0], rk[len(rk) // 2], rk[-1]]]
            used_all |= set(picks.tolist())
            A = np.vstack([np.ones(3), kvv[[rk[0], rk[len(rk) // 2],
                                            rk[-1]]]]).T
            (lf, p_s), *_ = np.linalg.lstsq(
                A, np.log(af_sc[picks]), rcond=None)
            fp[s] = (float(np.exp(lf)), float(p_s))
        pred_B = np.array([fp[int(s)][0] * kv[i] ** fp[int(s)][1]
                           for i, s in enumerate(st)]) * sh
        hold = np.array([i not in used_all for i in range(len(ks))])
        res_B = {"n_used": len(used_all),
                 "overall": err_stats(sf, pred_B),
                 "heldout": err_stats(sf[hold], pred_B[hold])}

    # P. 손실 보존 상사쌍 (인밴드): P_TS,SC(w,2I,b) vs P_TS,Ref(4w,I,b)
    ref_ts = {(int(t), round(c, 2), round(p, 1)): v
              for t, c, p, v in zip(kt, kc, kp, rf)}
    pair_dev, pair_rows = [], []
    for i in np.where(inband)[0]:
        key = (int(st[i] * 4), round(sc[i] / 2.0, 2), round(sp[i], 1))
        # 1856*4=7424 vs Ref 7425 격자 — 근접 키 매칭
        cand = [k for k in ref_ts
                if abs(k[0] - key[0]) <= 2 and abs(k[1] - key[1]) < 0.5
                and abs(k[2] - key[2]) < 0.5]
        if not cand:
            continue
        pv = ref_ts[cand[0]]
        dev = (sf[i] / pv - 1.0) * 100.0
        pair_dev.append(dev)
        pair_rows.append({"sc_op": [int(st[i]), float(sc[i]), float(sp[i])],
                          "ref_op": list(cand[0]),
                          "P_sc_kW": round(float(sf[i]), 4),
                          "P_ref_kW": round(float(pv), 4),
                          "dev_pct": round(float(dev), 2)})
    pair_dev = np.array(pair_dev)

    res = {"_meta": {
        "mapping": "AF_SC(w,I,b) = AF_Ref(4w, I/2, b)",
        "sc_speeds": sorted(set(st.astype(int))),
        "n_sc_pairs": len(ks), "n_by_speed": n_by_speed,
        "inband_speeds": list(SC_INBAND)}}
    for tag, pred, note in (
        ("A_uncorrected", pred_A, "AF=1"),
        ("C_zeroshot_via_Ref", pred_C,
         "SC TS-FEA 0점; 인밴드 donor 3712~14848, 외삽 29.7k/59.4k"),
        ("F_zeroshot_plus_anchor", pred_F,
         "외삽 속도별 자체 3점(κ-스팬) 재앵커")):
        res[tag] = {"note": note,
                    "overall": err_stats(sf, pred),
                    "inband": err_stats(sf[inband], pred[inband]),
                    "outband": (err_stats(sf[~inband], pred[~inband])
                                if (~inband).any() else None),
                    "by_speed": {str(int(s)): err_stats(
                        sf[st == s], pred[st == s])
                        for s in sorted(set(st))}}
    res["F_anchors"] = anchors
    if res_B:
        res["B_own_recipe_24pt"] = res_B
    if len(pair_dev):
        res["P_pair_conservation"] = {
            "note": "P_TS,SC(w,2I,b) vs P_TS,Ref(4w,I,b) — 활성 AC 손실 절대 보존",
            "n_pairs": int(len(pair_dev)),
            "mean_abs_dev_pct": round(float(np.abs(pair_dev).mean()), 2),
            "p95_abs_dev_pct": round(
                float(np.percentile(np.abs(pair_dev), 95)), 2),
            "max_abs_dev_pct": round(float(np.abs(pair_dev).max()), 2),
            "mean_signed_dev_pct": round(float(pair_dev.mean()), 2),
            "rows": pair_rows}

    print(f"\n{'예측자':<26}{'wMAE%':>8}{'인밴드':>8}{'외삽대':>8}")
    print("-" * 52)
    for tag in ("A_uncorrected", "C_zeroshot_via_Ref",
                "F_zeroshot_plus_anchor"):
        o = res[tag]
        ob = o["outband"]["wmae_pct"] if o["outband"] else float("nan")
        print(f"{tag:<26}{o['overall']['wmae_pct']:>8.2f}"
              f"{o['inband']['wmae_pct']:>8.2f}{ob:>8.2f}")
    if res_B:
        print(f"{'B_own_recipe_24pt':<26}"
              f"{res_B['overall']['wmae_pct']:>8.2f}"
              f"  (held-out {res_B['heldout']['wmae_pct']}%)")
    if len(pair_dev):
        pc = res["P_pair_conservation"]
        print(f"\n손실 보존 상사쌍 {pc['n_pairs']}쌍: mean|dev| "
              f"{pc['mean_abs_dev_pct']}%  p95 {pc['p95_abs_dev_pct']}%  "
              f"max {pc['max_abs_dev_pct']}%  (signed mean "
              f"{pc['mean_signed_dev_pct']}%)")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    def _np(o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        return str(o)

    json.dump(res, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=_np)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
