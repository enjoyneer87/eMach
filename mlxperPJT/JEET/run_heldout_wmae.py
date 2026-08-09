# -*- coding: utf-8 -*-
"""Held-out wMAE — 보정 표본을 제외한 검증 지표 (리뷰어 방어 #8).

논문 각주가 명시하듯 보정용 TS-FEA 표본은 검증 스윕의 부분집합이라, 전 맵
wMAE 에는 학습점(모델별 27~34개)이 포함된다. 기준 속도 커널 점은 TPS 가
정확 보간하므로 잔차 0 으로 지표를 낙관 쪽으로 끌 수 있다 --- 본 스크립트는
학습점을 제외한 held-out wMAE 를 산출해 그 편향을 정량화한다.

학습점 식별 (이중 매커니즘):
  (a) 기준 속도(16k) 커널 점 — 모델이 저장한 커널 중심 좌표
      (base_centers_i/p) 와 (I, beta) 정합으로 결정론 식별.
  (b) 그 외 속도의 (f,p) 회귀 점 — 빌드 중 np.random.RandomState.choice
      호출을 기록해 수집(자체/전달 플랜 공통 코드 경로). 도너(Ref) 모델은
      기록 시작 전에 캐시해 오염을 차단.

실행:  python run_heldout_wmae.py
산출:  map_exports/e10/heldout_wmae.json
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import numpy as np                                    # noqa: E402
from jeet_acloss_rbf.pipeline import AcLossPipeline   # noqa: E402

OUT = os.path.join(HERE, "map_exports", "e10", "heldout_wmae.json")


def wmae(f_ac, pred, mask):
    e = np.abs((pred - f_ac) / (f_ac + 1e-12) * 100.0)
    return float(np.sum(f_ac[mask] * e[mask]) / np.sum(f_ac[mask]))


def train_mask_for(scale: str):
    """(pipeline, model, train_mask) — 학습점 식별은 docstring 의 (a)+(b)."""
    pl = AcLossPipeline()
    if scale != pl.cfg["donor_scale"]:
        pl.build_donor()                       # 기록 밖에서 캐시

    # 채택 시드를 먼저 확정(대표 시드 탐색의 다중 빌드가 기록을 오염하지
    # 않도록 기록 밖에서 수행), 기록은 최종 단일 빌드에만 건다.
    plan = pl.cfg["plan"][scale]
    use_seed = plan["seed"]
    if use_seed is None:
        use_seed = pl.pick_representative_seed(scale)

    picks: list[np.ndarray] = []
    orig_rs = np.random.RandomState

    class RecRS(orig_rs):
        def choice(self, a, *args, **kw):      # noqa: N804
            out = super().choice(a, *args, **kw)
            arr = np.asarray(out)
            if arr.dtype.kind in "iu":         # 인덱스 배열만 기록
                picks.append(arr.ravel())
            return out

    # 결정론 배치는 RNG 를 거치지 않는다. 자체 모델·전달 모델 모두
    # _maximin_indices 를 지나므로 그 반환값을 기록해 학습점을 잡는다.
    from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder as _R
    orig_mm = _R._maximin_indices

    def rec_mm(cand, x, y, k):
        out = orig_mm(cand, x, y, k)
        arr = np.asarray(out)
        if arr.dtype.kind in "iu":
            picks.append(arr.ravel())
        return out

    np.random.RandomState = RecRS
    _R._maximin_indices = staticmethod(rec_mm)
    try:
        model = pl.build_model(scale, seed=use_seed)
    finally:
        np.random.RandomState = orig_rs
        _R._maximin_indices = staticmethod(orig_mm)

    ds = pl.load_dataset(scale)
    n = len(ds)
    mask = np.zeros(n, dtype=bool)

    # (a) 기준 속도 커널 중심 좌표 정합
    base_speed = pl.cfg["base_speed"]
    ci, cp = np.asarray(model.base_centers_i), np.asarray(model.base_centers_p)
    at_base = np.abs(ds.speeds_k - base_speed) < 0.1
    for k in range(n):
        if at_base[k] and np.any(
                (np.abs(ci - ds.irms_arr[k]) < 1e-6)
                & (np.abs(cp - ds.phase_arr[k]) < 1e-6)):
            mask[k] = True
    n_base_matched = int(mask.sum())

    # (b) 빌더가 남긴 '자체 진리값을 쓴 학습점' 인덱스.
    #     결정론 배치의 kappa-스팬은 순위 분위수 선택이라 RNG 를 거치지
    #     않으므로, RNG 기록만으로는 나머지 속도의 학습점을 놓친다.
    n_rec = 0
    rec = getattr(_R, "last_train_idx", None)
    src = [np.asarray(rec)] if rec is not None else picks
    for arr in src:
        for v in np.asarray(arr).ravel():
            if 0 <= v < n:
                if not mask[v]:
                    n_rec += 1
                mask[v] = True

    return pl, model, ds, mask, n_base_matched, n_rec


def main() -> int:
    res = {}
    print(f"{'model':<8}{'N':>5}{'train':>7}{'held':>6}"
          f"{'wMAE_full':>11}{'wMAE_held':>11}{'delta':>8}")
    print("-" * 56)
    for scale in ("Ref", "HalfSC", "SC"):
        pl, model, ds, mask, n_b, n_r = train_mask_for(scale)
        f_ac, h_ac = ds.f_ac_arr, ds.h_ac_arr
        pred = h_ac * model.predict(ds.speeds_k * 1000.0,
                                    ds.irms_arr, ds.phase_arr)
        full = wmae(f_ac, pred, np.ones(len(ds), bool))
        held = wmae(f_ac, pred, ~mask)
        bysp = {}
        for spd in sorted(set(np.round(ds.speeds_k, 3))):
            m_s = np.abs(ds.speeds_k - spd) < 0.1
            m_h = m_s & ~mask
            bysp[f"{spd:g}k"] = {
                "n": int(m_s.sum()), "n_held": int(m_h.sum()),
                "wmae_full": round(wmae(f_ac, pred, m_s), 3),
                "wmae_held": (round(wmae(f_ac, pred, m_h), 3)
                              if m_h.any() else None),
            }
        res[scale] = {
            "n_points": int(len(ds)),
            "n_train_identified": int(mask.sum()),
            "n_train_base_coord": n_b,
            "n_train_other_speed": n_r,
            "n_heldout": int((~mask).sum()),
            "wmae_full_pct": round(full, 3),
            "wmae_heldout_pct": round(held, 3),
            "delta_pp": round(held - full, 3),
            "by_speed": bysp,
        }
        print(f"{scale:<8}{len(ds):>5}{int(mask.sum()):>7}"
              f"{int((~mask).sum()):>6}{full:>11.2f}{held:>11.2f}"
              f"{held - full:>8.2f}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
