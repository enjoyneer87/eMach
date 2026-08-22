# -*- coding: utf-8 -*-
"""비용--정확도 파레토 분석 (cost vs accuracy sweep).

"자체 TS-FEA 점을 몇 개 쓰면 wMAE가 얼마인가"를 계획 변형별로 쓸어
파레토 전선을 구한다. 축은 세 가지다.

  mode      : ``own``      모든 속도를 자체 샘플링
              ``transfer`` 상사 전달 불가 대역(고속)만 자체 샘플링
  placement : ``random``   시드 평균 (기존 방식)
              ``structured`` maximin + kappa-스팬 결정론 배치
  budget    : 총 자체 TS-FEA 점수 B = n_base + n_spd * n_own_speeds

각 B에서 가능한 (n_base, n_spd) 배분을 모두 시도하고 최소 wMAE를
취하므로, 결과는 "이 예산에서 도달 가능한 최선"이다.

결과는 JSON으로 보존한다 (``sweep_cost_accuracy(..., out_json=...)``).
"""
from __future__ import annotations

import contextlib
import io
import json
import os
from typing import Dict, List, Optional, Sequence

import numpy as np

__all__ = ["sweep_cost_accuracy", "pareto_front"]


def _wmae(ds, model) -> float:
    """와트 가중 MAE [%] (효율맵 총손실 오차를 대표하는 지표)."""
    pred = ds.h_ac_arr * np.asarray(
        model.predict(ds.speeds_k * 1000.0, ds.irms_arr, ds.phase_arr), float)
    e = np.abs((pred - ds.f_ac_arr) / (ds.f_ac_arr + 1e-12) * 100.0)
    return float(np.sum(ds.f_ac_arr * e) / np.sum(ds.f_ac_arr))


def pareto_front(points: Sequence[dict]) -> List[dict]:
    """비용 오름차순으로 훑으며 wMAE가 갱신되는 점만 남긴다."""
    front, best = [], float("inf")
    for p in sorted(points, key=lambda d: (d["budget"], d["wmae"])):
        if p["wmae"] < best - 1e-9:
            best = p["wmae"]
            front.append(p)
    return front


def sweep_cost_accuracy(pipeline,
                        scales: Sequence[str] = ("HalfSC", "SC"),
                        budgets: Optional[Sequence[int]] = None,
                        n_spd_list: Sequence[int] = (1, 2, 3, 4),
                        modes: Sequence[str] = ("own", "transfer"),
                        placements: Sequence[str] = ("random", "structured"),
                        n_seeds: int = 6,
                        n_base_min: int = 6,
                        out_json: Optional[str] = None) -> dict:
    """계획 변형별 비용--정확도 곡선을 산출한다.

    Returns a JSON-serialisable dict; also writes it to ``out_json``.
    """
    from .RbfModelBuilder import RbfModelBuilder

    budgets = list(budgets or range(9, 37, 3))
    base_speed = pipeline.cfg["base_speed"]
    donor = pipeline.build_donor()

    result = {
        "meta": {
            "budgets": budgets, "n_spd_list": list(n_spd_list),
            "modes": list(modes), "placements": list(placements),
            "n_seeds": n_seeds, "base_speed_kRPM": base_speed,
            "n_base_min": n_base_min,
            "note": "wMAE %% on the full dq plane. budget = own TS-FEA "
                    "points only (transferred probes are free). At each "
                    "budget the best (n_base, n_spd) split is reported. "
                    "'structured' is deterministic (single run).",
        },
        "scales": {},
    }

    for scale in scales:
        with contextlib.redirect_stdout(io.StringIO()):
            ds = pipeline.load_dataset(scale)
        pool = int(np.sum(np.abs(ds.speeds_k - base_speed) < 0.1))
        others = [s for s in sorted(set(np.round(ds.speeds_k, 3)))
                  if abs(s - base_speed) >= 0.1]
        k_r = pipeline.cfg["k_r"][scale]
        # 상사 전달 불가(고속) 대역: 사상 속도가 donor 상한을 넘는 속도
        n_own_spd = {"own": len(others),
                     "transfer": sum(1 for s in others
                                     if s * k_r ** 2 > base_speed + 0.1)}

        runs: List[dict] = []
        for mode in modes:
            n_sp_speeds = n_own_spd[mode]
            if n_sp_speeds == 0:
                continue
            for placement in placements:
                seeds = range(n_seeds) if placement == "random" else [0]
                for B in budgets:
                    for n_spd in n_spd_list:
                        n_base = B - n_spd * n_sp_speeds
                        if n_base < n_base_min or n_base > pool:
                            continue
                        ws = []
                        for seed in seeds:
                            try:
                                with contextlib.redirect_stdout(
                                        io.StringIO()):
                                    if mode == "own":
                                        plan = RbfModelBuilder.\
                                            plan_sampling_indices(
                                                ds, n_base=n_base,
                                                n_spd=n_spd,
                                                base_speed=base_speed,
                                                placement=placement,
                                                seed=seed)
                                        m = RbfModelBuilder.\
                                            build_separable_rbf(
                                                ds, base_speed=base_speed,
                                                exponent=True,
                                                index_plan=plan)
                                    else:
                                        m = RbfModelBuilder.\
                                            build_separable_rbf_transfer(
                                                ds, donor, k_r, n_base,
                                                n_spd, seed,
                                                base_speed=base_speed,
                                                n_probe_transfer=pipeline.cfg[
                                                    "n_probe_transfer"],
                                                exponent=True,
                                                placement=placement,
                                                donor_dataset=pipeline.
                                                load_dataset(pipeline.cfg[
                                                    "donor_scale"]))
                                ws.append(_wmae(ds, m))
                            except Exception:
                                continue
                        if not ws:
                            continue
                        runs.append({
                            "mode": mode, "placement": placement,
                            "budget": int(B), "n_base": int(n_base),
                            "n_spd": int(n_spd),
                            "wmae": float(np.mean(ws)),
                            "wmae_worst": float(np.max(ws)),
                            "n_runs": len(ws),
                        })

        # 계획 변형별 최선 + 전체 파레토
        best_by_variant: Dict[str, List[dict]] = {}
        for mode in modes:
            for placement in placements:
                sub = [r for r in runs
                       if r["mode"] == mode and r["placement"] == placement]
                if sub:
                    best_by_variant[f"{mode}/{placement}"] = pareto_front(sub)

        result["scales"][scale] = {
            "base_pool": pool, "n_points": int(len(ds.af_arr)),
            "k_r": float(k_r), "n_own_speeds": n_own_spd,
            "hybrid_wmae": _wmae(ds, _Unit()),
            "runs": runs,
            "pareto_by_variant": best_by_variant,
            "pareto_overall": pareto_front(runs),
        }

    if out_json:
        os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
    return result


class _Unit:
    """AF == 1 (무보정 Hybrid) 을 model 인터페이스로 감싼 것."""

    @staticmethod
    def predict(sp, ii, ph):
        return np.ones(np.asarray(ii, float).size)
