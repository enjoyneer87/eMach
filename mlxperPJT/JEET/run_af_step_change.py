# -*- coding: utf-8 -*-
"""표본 증분에 대한 AF 표면 변화량(하이브리드 가중 |dAF|) 곡선.

진리값 없이 수렴을 판정할 수 있는가를 보이는 그림이다. 지표는

    D(n) = sum_i w_i |AF_n(i) - AF_{n-2}(i)| / sum_i w_i ,   w_i = 하이브리드 손실

로, 전 맵 96점에서 평가하되 **Full-FEA 진리값을 쓰지 않는다** --- 두 보정
표면의 차이만 본다. 비교를 위해 진리값이 필요한 wMAE 를 같은 축에 겹친다.
두 곡선이 같은 지점에서 정체하면, 실무자는 진리값 없이도 예산이 충분함을
알 수 있다.

표본 좌표는 Fig 6 과 동일한 결정론 배치(앵커 maximin + kappa-스팬)를 쓴다.
앵커 단계는 중첩 순서지만 kappa-스팬 단계는 학습된 kappa 에 의존하므로
완전 중첩은 아니다. 그 겹침 비율도 함께 출력한다.

  python run_af_step_change.py
"""
import contextlib
import io
import json
import os
import sys

import numpy as np

_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "tools")))   # 워크트리의 tools 를 쓴다

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.pipeline import AcLossPipeline
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder
from jeet_acloss_rbf.manuscript_figs import _journal_rc

SCALES = ("Ref", "HalfSC", "SC")
KR = {"Ref": 1.0, "HalfSC": 1.5, "SC": 2.0}
NSPD = {"Ref": 4, "HalfSC": 3, "SC": 4}
ADOPTED = 24
NBASE = tuple(range(6, 26, 2))


def _fit(ds, nb, ns, base_speed):
    """결정론 배치로 nb 점 적합. (AF 전 맵 예측, 학습 인덱스) 반환."""
    with contextlib.redirect_stdout(io.StringIO()):
        plan = RbfModelBuilder.plan_sampling_indices(
            ds, n_base=nb, n_spd=ns, base_speed=base_speed,
            placement='structured', seed=0)
        m = RbfModelBuilder.build_separable_rbf(
            ds, base_speed=base_speed, exponent=True, index_plan=plan)
    af = m.predict(ds.speeds_k * 1000.0, ds.irms_arr, ds.phase_arr)
    idx = getattr(RbfModelBuilder, 'last_train_idx', None)
    return np.asarray(af, dtype=float), (set(idx) if idx is not None else None)


def main():
    pl = AcLossPipeline()
    pl.cfg["plan"]["HalfSC"]["seed"] = 3
    base_speed = pl.cfg['base_speed']

    plt = _journal_rc()
    fig, axes = plt.subplots(1, len(SCALES),
                             figsize=(2.12 * len(SCALES), 2.12),
                             layout='constrained', sharey=True)
    out = {}

    for k, (ax, scale) in enumerate(zip(axes, SCALES)):
        with contextlib.redirect_stdout(io.StringIO()):
            ds = pl.load_dataset(scale)
        ns = NSPD[scale]
        pool = int(np.sum(np.abs(ds.speeds_k - base_speed) < 0.1))
        nbs = sorted({min(n, pool) for n in NBASE})
        w = np.asarray(ds.f_ac_arr, dtype=float)   # 와트 가중은 하이브리드 손실
        wh = np.asarray(ds.h_ac_arr, dtype=float)

        afs, wmaes, keep = {}, {}, {}
        for nb in nbs:
            try:
                af, idx = _fit(ds, nb, ns, base_speed)
            except np.linalg.LinAlgError:
                continue
            afs[nb] = af
            keep[nb] = idx
            pred = wh * af
            e = np.abs((pred - w) / (w + 1e-12) * 100.0)
            wmaes[nb] = float(np.sum(w * e) / np.sum(w))

        ok = [n for n in nbs if n in afs]
        steps, dvals, nest = [], [], []
        for a, b in zip(ok[:-1], ok[1:]):
            d = np.abs(afs[b] - afs[a])
            dvals.append(float(np.sum(wh * d) / np.sum(wh)))
            steps.append(b)
            if keep[a] and keep[b]:
                nest.append(len(keep[a] & keep[b]) / float(len(keep[a])))

        ax.plot(steps, dvals, lw=1.2, ms=4.2, marker='o', ls='-',
                color='#e65100', label=r'$|\Delta AF|$ (no truth)')
        ax2 = ax.twinx()
        ax2.plot(ok, [wmaes[n] for n in ok], lw=1.0, ms=3.4, marker='s',
                 ls='--', color='#5b6b7a', label='wMAE (needs truth)')
        ax2.set_yscale('log')
        ax2.set_ylim(0.5, 30.0)   # 세 패널 공통 --- 안 그러면 비교가 거짓이 된다
        if k == len(SCALES) - 1:
            ax2.set_ylabel(r'wMAE [\%] (log)')
        else:
            ax2.set_yticklabels([])

        if ADOPTED in steps:
            ax.plot([ADOPTED], [dvals[steps.index(ADOPTED)]], marker='*',
                    ms=10, ls='none', color='#e65100', mec='#4d2600',
                    mew=0.5, zorder=5, label=r'adopted $n_{base}$')
        ax.set_yscale('log')
        ax.set_xticks(list(nbs))
        ax.set_xlabel(r'$n_{base}$ (16-kRPM base points)')
        if k == 0:
            ax.set_ylabel(r'weighted $|\Delta AF|$ (log)')
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, fontsize=7.2, loc='lower left',
                      frameon=True, framealpha=0.85, edgecolor='none',
                      handlelength=1.7, labelspacing=0.3, borderpad=0.3)
        ax.grid(True, which='both', ls=':', lw=0.4, color='#dddddd')
        ax.set_axisbelow(True)
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)

        out[scale] = {
            'k_r': KR[scale], 'pool': pool, 'n_spd': ns,
            'n_base': ok,
            'wmae': [round(wmaes[n], 4) for n in ok],
            'step_at': steps,
            'dAF': [round(v, 5) for v in dvals],
            'nesting_mean': round(float(np.mean(nest)), 3) if nest else None,
        }
        tail = "  ".join(f"{n}:{v:.4f}" for n, v in zip(steps, dvals))
        print(f"[{scale}] pool={pool} n_spd={ns}")
        print(f"  |dAF| {tail}")
        print("  wMAE  " + "  ".join(f"{n}:{wmaes[n]:.2f}%" for n in ok))
        if nest:
            print(f"  표본 중첩률 평균 {np.mean(nest):.3f}")

    os.makedirs(_FIGDIR, exist_ok=True)
    pdf = os.path.join(_FIGDIR, "af_step_change.pdf")
    png = os.path.join(_FIGDIR, "af_step_change.png")
    fig.savefig(pdf)
    fig.savefig(png, dpi=220)
    plt.close(fig)
    print("\n저장:", pdf)
    print("저장:", png)

    js = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "af_step_change.json")
    with open(js, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print("저장:", js)


if __name__ == "__main__":
    main()
