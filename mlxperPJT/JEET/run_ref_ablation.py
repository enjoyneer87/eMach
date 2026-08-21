# -*- coding: utf-8 -*-
"""기준 모델(Ref) 자체 샘플링 예산의 (n_base, n_spd) 감축 맵.

Fig 7 은 변형체의 *전달* 플랜을 훑는다 --- 축이 (앵커 점수, 8 kRPM 점수)
이고, 나머지 속도는 도너에서 무료로 온다. Ref 에는 도너가 없어 네 속도를
모두 자기 점으로 떠받쳐야 하므로 축이 다르다: 앵커 점수 x *비앵커 속도당*
점수이고, 총 Full-FEA 는 n_base + 3*n_spd 다.

Ref 자체 예산 36점은 논문 전체 Full-FEA 63점의 과반인데 원고에 그 배분
근거가 없다. 이 맵이 그것을 채운다.

  python run_ref_ablation.py
"""
import contextlib
import io
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools')))
from jeet_acloss_rbf.repro_env import fig_dir
_FIGDIR = fig_dir()

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "tools")))   # 워크트리의 tools 를 쓴다

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.pipeline import AcLossPipeline
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder
from jeet_acloss_rbf.manuscript_figs import _journal_rc

NBASE = (8, 12, 16, 20, 22, 24)
NSPD = (1, 2, 3, 4, 5)
ADOPTED = (24, 4)


def main():
    pl = AcLossPipeline()
    base_speed = pl.cfg['base_speed']
    with contextlib.redirect_stdout(io.StringIO()):
        ds = pl.load_dataset('Ref')
    w = np.asarray(ds.f_ac_arr, dtype=float)
    wh = np.asarray(ds.h_ac_arr, dtype=float)
    pool = int(np.sum(np.abs(ds.speeds_k - base_speed) < 0.1))

    Z = np.full((len(NBASE), len(NSPD)), np.nan)
    for i, nb in enumerate(NBASE):
        for j, ns in enumerate(NSPD):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    ip = RbfModelBuilder.plan_sampling_indices(
                        ds, n_base=min(nb, pool), n_spd=ns,
                        base_speed=base_speed,
                        placement='structured', seed=0)
                    m = RbfModelBuilder.build_separable_rbf(
                        ds, base_speed=base_speed, exponent=True,
                        index_plan=ip)
            except np.linalg.LinAlgError:
                continue
            pred = wh * m.predict(ds.speeds_k * 1000.0, ds.irms_arr,
                                  ds.phase_arr)
            e = np.abs((pred - w) / (w + 1e-12) * 100.0)
            Z[i, j] = float(np.sum(w * e) / np.sum(w))

    plt = _journal_rc()
    from matplotlib.colors import LogNorm
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(3.1, 2.5), layout='constrained')
    im = ax.imshow(Z, origin='lower', aspect='auto', cmap='viridis_r',
                   norm=LogNorm(vmin=np.nanmin(Z), vmax=np.nanmax(Z)))
    ax.set_xticks(range(len(NSPD)), [str(n) for n in NSPD])
    ax.set_yticks(range(len(NBASE)), [str(n) for n in NBASE])
    ax.set_xlabel(r'$n_{spd}$ (per non-anchor speed)')
    ax.set_ylabel(r'$n_{base}$ (16-kRPM base points)')
    for i in range(len(NBASE)):
        for j in range(len(NSPD)):
            if np.isfinite(Z[i, j]):
                ax.text(j, i, '%.2f' % Z[i, j], ha='center', va='center',
                        fontsize=7.0,
                        color='white' if Z[i, j] > 3 else '#111111')
    ai, aj = NBASE.index(ADOPTED[0]), NSPD.index(ADOPTED[1])
    ax.add_patch(Rectangle((aj - .5, ai - .5), 1, 1, fill=False,
                           ec='#e65100', lw=1.8, zorder=4))
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label(r'full-map wMAE [\%] (log)')

    os.makedirs(_FIGDIR, exist_ok=True)
    pdf = os.path.join(_FIGDIR, "ref_ablation.pdf")
    png = os.path.join(_FIGDIR, "ref_ablation.png")
    fig.savefig(pdf)
    fig.savefig(png, dpi=220)
    plt.close(fig)

    print("Ref 자체 샘플링, 결정론 배치. 전 맵 96점 wMAE [%]")
    print("        " + "".join("%8d" % n for n in NSPD) + "   (n_spd)")
    for i, nb in enumerate(NBASE):
        cells = "".join("   %5.2f" % v if np.isfinite(v) else "     ---"
                        for v in Z[i])
        tot = "".join("  %2d" % (min(nb, pool) + 3 * n) for n in NSPD)
        print("nb %2d %s   | 총 Full-FEA%s" % (nb, cells, tot))
    print("\n채택 (24, 4) = %.3f%%, Full-FEA 36점" % Z[ai, aj])
    print("저장:", pdf)

    js = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "ref_ablation.json")
    with open(js, "w", encoding="utf-8") as fh:
        json.dump({'n_base': list(NBASE), 'n_spd': list(NSPD),
                   'wmae_pct': [[None if not np.isfinite(v) else round(v, 4)
                                 for v in r] for r in Z]},
                  fh, ensure_ascii=False, indent=1)
    print("저장:", js)


if __name__ == "__main__":
    main()
