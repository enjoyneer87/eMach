"""
verify_af_data_quality.py
=========================
AF (FEA/Hybrid) 학습 데이터의 품질을 점검하고, RBF 서로게이트의 LOOCV 오차를
'어디서' 만드는지 진단한 뒤, 채워야 할 보강 FEA 운전점을 제안한다.

JEET Phase 2 "데이터 보강 우선" 워크플로 도구.
SC 모델 재학습 전, 다음 세 가지를 자동으로 잡아낸다.
  1) 불량 FEA 점     : (speed, phase) 라인의 전류-손실 추세를 깨는 AF 이상치
  2) 그리드 구멍     : 스케줄됐지만 FEA 미완료(매칭 실패)인 셀
  3) 과소샘플링 코너 : LOOCV 잔차가 집중되는 (speed, phase) 영역 → 보강 대상

사용:
    python verify_af_data_quality.py SC
    python verify_af_data_quality.py SC --json <경로> --loo-thr 15 --emit-infill

재평가 루프:
    보강 FEA를 Motor-CAD로 돌려 JSON에 추가 → 본 스크립트 재실행 →
    "전체 LOOCV"와 "이상치 제거 후 LOOCV"가 수렴하면 모델 확정 단계로 이동.
"""
import sys, json, argparse
import numpy as np
from pathlib import Path

EMACH = Path(__file__).resolve().parents[2]          # ...\eMach
for cand in (EMACH / "tools", EMACH / "mlxperPJT" / "JEET"):
    if str(cand) not in sys.path:
        sys.path.insert(0, str(cand))
from jeet_acloss_rbf import AcLossJsonReader, RbfModelBuilder  # noqa: E402

DEFAULT_JSON = {
    "SC":     EMACH / "mlxperPJT/JEET/map_exports/e10/SC/JEET_ACLoss_SC_Map_Summary.json",
    "HalfSC": EMACH / "mlxperPJT/JEET/map_exports/e10/HalfSC/JEET_ACLoss_HalfSC_Map_Summary.json",
    "Ref":    EMACH / "mlxperPJT/JEET/map_exports/e10/Ref/JEET_ACLoss_Ref_Map_Summary.json",
}


def _tps(A, B, ls):
    An, Bn = A / ls, B / ls
    d2 = np.sum((An[:, None, :] - Bn[None, :, :]) ** 2, axis=2)
    return d2 * np.log(np.sqrt(d2) + 1e-12)


def loocv_residuals(X, af, hac, fac, ls, lam=1e-4):
    """3D TPS-RBF leave-one-out 잔차 [%] (보정 손실 hac*AF vs fac 기준)."""
    n = len(af)
    err = np.full(n, np.nan)
    for i in range(n):
        tr = np.arange(n) != i
        try:
            w = np.linalg.solve(_tps(X[tr], X[tr], ls) + lam * np.eye(n - 1), af[tr])
        except np.linalg.LinAlgError:
            continue
        pred = (_tps(X[i:i + 1], X[tr], ls) @ w)[0]
        err[i] = abs((hac[i] * pred - fac[i]) / (fac[i] + 1e-12) * 100.0)
    return err


def detect_line_outliers(speeds, currs, phases, af, fac, mad_k=3.5, min_fea_kW=1.0):
    """
    각 (speed, phase) 라인에서 전류 대비 FEA 손실의 매끈함을 점검.
    FEA 손실은 전류에 대해 단조 증가해야 하므로, log(fea)-log(I) 기울기가
    이웃과 크게 어긋나거나 AF가 라인 중앙값에서 robust-z > mad_k 이면 이상치로 본다.
    손실이 min_fea_kW 미만인 미소손실 점은 AF가 본래 noise이므로 제외한다.
    """
    flags = []
    key = np.round(np.column_stack([speeds, phases]), 1)
    seen = set()
    for sp, ph in map(tuple, key):
        if (sp, ph) in seen:
            continue
        seen.add((sp, ph))
        m = (np.abs(speeds - sp) < 1e-3) & (np.abs(phases - ph) < 1e-3)
        idx = np.where(m)[0]
        if len(idx) < 3:
            continue
        o = idx[np.argsort(currs[idx])]
        a = af[o]
        med = np.median(a)
        mad = np.median(np.abs(a - med)) + 1e-9
        z = 0.6745 * (a - med) / mad
        # 단조성: fea가 전류 증가에도 직전보다 떨어지면 의심
        f = fac[o]
        for k, gi in enumerate(o):
            if fac[gi] < min_fea_kW:          # 미소손실 → AF noise, 건너뜀
                continue
            non_mono = (k > 0 and f[k] < f[k - 1] * 0.9)
            if abs(z[k]) > mad_k or non_mono:
                flags.append(dict(speed=sp, current=currs[gi], phase=ph,
                                  af=af[gi], fea=fac[gi],
                                  robust_z=float(z[k]), non_monotonic=bool(non_mono)))
    return flags


def grid_holes(meta, recs, speeds, currs, phases):
    """
    스케줄(current_grid×phase_grid×speeds) 셀을 세 부류로 분류:
      - 'missing' : FullFEA(proximity_model=3) raw 레코드 자체가 없음 → 진짜 보강 대상
      - 'filtered': FEA는 있으나 AF 필터로 학습 제외 (저속·미소손실 등, 보강 불필요)
      - 'ok'      : 학습에 포함
    'missing'만 반환한다.
    """
    cg, pg, sg = meta.get("current_grid", []), meta.get("phase_grid", []), meta.get("speeds", [])
    fea = [(r["speed"], r["current"], r["phase"]) for r in recs
           if r.get("proximity_model") == 3 and "fea_total_ac_kW" in r]
    holes = []
    for s in sg:
        for c in cg:
            if c < 50:           # 저전류는 AF 정의가 약해 의도적 제외
                continue
            for p in pg:
                in_train = np.any((np.abs(speeds * 1000 - s) < 1) &
                                  (np.abs(currs - c) < 5) & (np.abs(phases - p) < 1))
                if in_train:
                    continue
                has_fea = any(abs(fs - s) < 1 and abs(fc - c) < 5 and abs(fp - p) < 1
                              for fs, fc, fp in fea)
                if not has_fea:                       # FEA 자체가 없음 → 진짜 구멍
                    holes.append((int(s), float(c), float(p)))
    return holes


def propose_infill(speeds, phases, loo, cg, thr_pct):
    """LOOCV 잔차가 thr_pct 이상으로 집중되는 (speed, phase) 열에 전류 중점을 제안."""
    proposals = []
    key = sorted({(round(s), round(p)) for s, p in zip(speeds, phases)})
    cg = sorted(cg)
    mids = [round((cg[i] + cg[i + 1]) / 2) for i in range(len(cg) - 1) if cg[i] >= 50]
    for sp, ph in key:
        m = (np.abs(speeds - sp) < 0.1) & (np.abs(phases - ph) < 1)
        e = loo[m]
        e = e[~np.isnan(e)]
        if len(e) and e.mean() >= thr_pct:
            proposals.append(dict(speed=int(sp * 1000), phase=int(ph),
                                  mean_loo=float(e.mean()), add_currents=mids))
    return proposals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scale", choices=["SC", "HalfSC", "Ref"])
    ap.add_argument("--json", default=None)
    ap.add_argument("--loo-thr", type=float, default=8.0, help="보강 제안 트리거 LOOCV[%]")
    ap.add_argument("--emit-infill", action="store_true", help="제안 sweep을 JSON으로 저장")
    args = ap.parse_args()

    jpath = Path(args.json) if args.json else DEFAULT_JSON[args.scale]
    raw = json.load(open(jpath, encoding="utf-8"))
    recs, meta = (raw["records"], raw.get("_meta", {})) if isinstance(raw, dict) else (raw, {})
    ds = RbfModelBuilder.match_records_and_create_dataset(recs)
    n = len(ds)
    s, I, P = ds.speeds_k, ds.irms_arr, ds.phase_arr
    af, hac, fac = ds.af_arr, ds.h_ac_arr, ds.f_ac_arr
    X = np.column_stack([s, I, P])
    ls = np.array([ds.LS_S, ds.LS_I, ds.LS_P])

    print(f"\n{'='*64}\n[{args.scale}] 데이터 품질 진단   (n={n} 운전점)\n{'='*64}")

    loo = loocv_residuals(X, af, hac, fac, ls)
    valid = ~np.isnan(loo)
    print(f"\n● 3D TPS RBF LOOCV (전체)          : {loo[valid].mean():5.2f}%")

    # 1) 불량 FEA 이상치 : 라인 추세 위반 OR LOOCV 잔차 폭주
    outliers = detect_line_outliers(s, I, P, af, fac)
    out_keys = set()
    rows = []
    for o in outliers:
        k = (round(o["speed"]), round(o["current"]), round(o["phase"]))
        out_keys.add(k)
        tag = "비단조" if o["non_monotonic"] else f"z={o['robust_z']:+.1f}"
        rows.append((abs(o["robust_z"]), o["speed"], o["current"], o["phase"], o["af"], o["fea"], tag))
    # LOO 잔차가 임계 이상이면 데이터 신뢰 불가 → 이상치로 합류
    LOO_OUTLIER = 25.0
    for i in range(n):
        if valid[i] and loo[i] >= LOO_OUTLIER:
            k = (round(s[i] * 1000), round(I[i]), round(P[i]))
            if k not in out_keys:
                out_keys.add(k)
                rows.append((loo[i], s[i], I[i], P[i], af[i], fac[i], f"LOO={loo[i]:.0f}%"))
    print(f"\n● [1] AF 이상치 (라인 추세 위반 OR LOOCV≥{LOO_OUTLIER:.0f}%) : {len(out_keys)}건")
    for _, sp, cu, ph, a, fe, tag in sorted(rows, key=lambda r: -r[0]):
        print(f"    s={sp*1000:5.0f}rpm I={cu:4.0f}A th={ph:4.0f}deg  "
              f"AF={a:.3f} fea={fe:7.2f}kW  [{tag}]")
    # 이상치 제거 후 LOOCV
    if out_keys:
        keep = np.array([(round(s[i]*1000), round(I[i]), round(P[i])) not in out_keys
                         for i in range(n)])
        if keep.sum() > 10:
            loo2 = loocv_residuals(X[keep], af[keep], hac[keep], fac[keep], ls)
            print(f"    → 이상치 {len(out_keys)}건 제거 후 LOOCV : "
                  f"{np.nanmean(loo2):5.2f}%  (전체 대비 Δ{np.nanmean(loo2)-loo[valid].mean():+.2f}%p)")

    # 2) 그리드 구멍
    holes = grid_holes(meta, recs, s, I, P) if meta else []
    print(f"\n● [2] 진짜 그리드 구멍 (FullFEA 레코드 자체 없음): {len(holes)}건")
    for h in holes:
        print(f"    s={h[0]:5d}rpm I={h[1]:4.0f}A th={h[2]:4.0f}deg")

    # 3) 오차 집중 영역
    print(f"\n● [3] LOOCV 잔차 집중 (속도/위상)")
    for sp in sorted(set(np.round(s).astype(int))):
        e = loo[(np.abs(s - sp) < 0.1) & valid]
        if len(e):
            print(f"    s={sp:2d}k : {e.mean():5.2f}%  (n={len(e)})")
    for lo, hi in [(0, 30), (30, 60), (60, 95)]:
        e = loo[(P >= lo) & (P < hi) & valid]
        if len(e):
            print(f"    th[{lo:2d},{hi:2d}): {e.mean():5.2f}%  (n={len(e)})")

    # 4) 보강 제안
    props = propose_infill(s, P, loo, meta.get("current_grid", []), args.loo_thr)
    print(f"\n● [4] 보강 FEA 제안  (LOOCV ≥ {args.loo_thr:.0f}% 열에 전류 중점 삽입)")
    infill = []
    for h in holes:                       # 누락 셀은 최우선
        infill.append(dict(speed=h[0], current=h[1], phase=h[2], reason="grid_hole"))
    for k in out_keys:                    # 불량 점은 재계산 (k[0]은 이미 RPM)
        infill.append(dict(speed=int(k[0]), current=float(k[1]), phase=float(k[2]),
                           reason="rerun_outlier"))
    for p in props:
        for c in p["add_currents"]:
            infill.append(dict(speed=p["speed"], current=float(c), phase=p["phase"],
                               reason=f"densify_loo{p['mean_loo']:.0f}pct"))
        print(f"    s={p['speed']:5d}rpm th={p['phase']:3d}deg (LOO {p['mean_loo']:.1f}%) "
              f"→ 추가 전류 {p['add_currents']} A")
    # 중복 제거
    uniq, seen = [], set()
    for it in infill:
        kk = (it["speed"], round(it["current"]), round(it["phase"]))
        if kk not in seen:
            seen.add(kk); uniq.append(it)
    print(f"\n  ▶ 제안 보강점 합계: {len(uniq)}건 "
          f"(구멍 {len(holes)} + 불량 {len(out_keys)} + densify {len(uniq)-len(holes)-len(out_keys)})")

    if args.emit_infill:
        op = jpath.parent / f"AF_infill_schedule_{args.scale}.json"
        json.dump({"scale": args.scale, "source": str(jpath), "points": uniq},
                  open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  저장: {op}")
    print()


if __name__ == "__main__":
    main()
