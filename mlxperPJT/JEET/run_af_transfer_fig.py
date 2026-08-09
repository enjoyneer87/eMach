# -*- coding: utf-8 -*-
"""AF 표면 + 표본 배치 + 상사 전달을 한 장으로 (Fig 5 대체안 시제품).

현행 Fig 5 는 SC 한 대의 AF 등고선과 표본만 속도별로 보인다. 비대칭 플랜은
말로만 있다 --- 변형체가 저속 대역에 자체 표본을 하나도 쓰지 않는다는 것이
논문 §4.4 의 핵심인데 그림이 없다.

윗줄 Ref, 아랫줄 SC 로 같은 네 속도를 놓고 각 평면에 후보점과 실제 학습점을
찍으면, SC 의 2/4 kRPM 패널이 비어 있는 것 자체가 주장이 된다. 상사 사상
(w -> w/k_r^2, I -> k_r I) 을 화살표로 이으면 그 빈 자리를 무엇이 채우는지도
같이 읽힌다. 무부하 후보가 배제되는 것도 원점 표시로 드러나므로 Table 2 의
허용 규칙 각주가 짧아진다.

  python run_af_transfer_fig.py
"""
import argparse
import contextlib
import io
import os
import sys

import numpy as np

_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools")))

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.pipeline import AcLossPipeline
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder
from jeet_acloss_rbf.manuscript_figs import _journal_rc

SPEEDS = (2.0, 4.0, 8.0, 16.0)
ROWS = (("Ref", 1.0), ("SC", 2.0))
# 상사 사상: 기증자 속도 w 는 변형체에서 w / k_r^2 에 대응한다 (k_r = 2 -> /4).
TRANSFER = ((8.0, 2.0), (16.0, 4.0))
PAIR_COLOR = {8.0: '#2c6fad', 16.0: '#7b1fa2'}


def dq(irms, phase_deg):
    """(I_rms, beta) -> (i_d, i_q) 진폭. beta 는 진각이라 q 축에서 잰다."""
    b = np.deg2rad(np.asarray(phase_deg, float))
    a = np.sqrt(2.0) * np.asarray(irms, float)
    return -a * np.sin(b), a * np.cos(b)


def build(pl, scale):
    """채택 플랜 그대로 적합하고 (데이터셋, 모델, 학습 인덱스) 를 준다."""
    cfg = pl.cfg
    plan = cfg['plan'][scale]
    with contextlib.redirect_stdout(io.StringIO()):
        ds = pl.load_dataset(scale)
        if plan['mode'] == 'own':
            ip = RbfModelBuilder.plan_sampling_indices(
                ds, n_base=plan['n_base'], n_spd=plan['n_spd'],
                base_speed=cfg['base_speed'], placement='structured', seed=0)
            m = RbfModelBuilder.build_separable_rbf(
                ds, base_speed=cfg['base_speed'], exponent=cfg['exponent'],
                index_plan=ip)
        else:
            m = pl.build_model(scale)
    idx = getattr(RbfModelBuilder, 'last_train_idx', None)
    if idx is None:
        idx = []
    return ds, m, set(int(i) for i in np.asarray(idx).ravel())


def main_3d(pl, plt, built):
    """같은 데이터의 3-D 판. 평면판과 나란히 놓고 고르기 위한 것."""
    fig = plt.figure(figsize=(7.1, 3.9), layout='constrained')
    vmin = min(built[s][0].af_arr.min() for s, _ in ROWS)
    vmax = max(built[s][0].af_arr.max() for s, _ in ROWS)
    from matplotlib import cm
    from matplotlib.colors import Normalize
    norm = Normalize(vmin, vmax)

    for r, (scale, _k) in enumerate(ROWS):
        ds, m, tr = built[scale]
        for c, spd in enumerate(SPEEDS):
            ax = fig.add_subplot(len(ROWS), len(SPEEDS),
                                 r * len(SPEEDS) + c + 1, projection='3d')
            sel = np.abs(np.asarray(ds.speeds_k) - spd) < 0.1
            cand = np.where(sel)[0]
            ii = np.asarray(ds.irms_arr)[cand]
            pp = np.asarray(ds.phase_arr)[cand]
            gi = np.linspace(ii.min(), ii.max(), 40)
            gp = np.linspace(pp.min(), pp.max(), 40)
            GI, GP = np.meshgrid(gi, gp)
            Z = np.asarray(m.predict(np.full(GI.size, spd * 1000.0),
                                     GI.ravel(), GP.ravel()),
                           float).reshape(GI.shape)
            X, Y = dq(GI, GP)
            ax.plot_surface(X, Y, Z, facecolors=cm.viridis(norm(Z)),
                            rstride=1, cstride=1, linewidth=0,
                            antialiased=True, shade=False, alpha=0.9)
            tsel = sorted(tr & set(cand.tolist()))
            if tsel:
                xt, yt = dq(np.asarray(ds.irms_arr)[tsel],
                            np.asarray(ds.phase_arr)[tsel])
                ax.scatter(xt, yt, np.asarray(ds.af_arr)[tsel],
                           s=13, c='#e65100', edgecolors='#3b1a00',
                           linewidths=0.4, depthshade=False, zorder=6)
            ax.set_zlim(vmin, vmax)
            ax.view_init(elev=22, azim=-58)
            ax.tick_params(labelsize=5.2, pad=-2)
            ax.set_title('%g kRPM' % spd if r == 0 else '',
                         fontsize=8.0, pad=-4)
            if c == 0:
                ax.set_zlabel('%s   $AF$' % scale, fontsize=7.0, labelpad=-6)
            ax.set_xlabel('$i_d$', fontsize=6.6, labelpad=-8)
            ax.set_ylabel('$i_q$', fontsize=6.6, labelpad=-8)

    out = os.path.join(_FIGDIR, 'af_transfer_map_3d')
    fig.savefig(out + '.pdf')
    fig.savefig(out + '.png', dpi=220)
    plt.close(fig)
    print('저장:', out + '.pdf')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='both', choices=('flat', '3d', 'both'))
    args = ap.parse_args()
    pl = AcLossPipeline()
    pl.cfg['plan']['HalfSC']['seed'] = 3
    plt = _journal_rc()
    from matplotlib.patches import ConnectionPatch

    built = {}
    for scale, _ in ROWS:
        built[scale] = build(pl, scale)
        ds, _, tr = built[scale]
        per = {s: sum(1 for i in tr
                      if abs(ds.speeds_k[i] - s) < 0.1) for s in SPEEDS}
        print("%-4s 학습점 %2d  속도별 %s" % (scale, len(tr), per))

    if args.mode in ('3d', 'both'):
        main_3d(pl, plt, built)
    if args.mode == '3d':
        return

    fig, axes = plt.subplots(len(ROWS), len(SPEEDS),
                             figsize=(7.1, 3.6), layout='constrained')
    vmin = min(built[s][0].af_arr.min() for s, _ in ROWS)
    vmax = max(built[s][0].af_arr.max() for s, _ in ROWS)
    levels = np.linspace(vmin, vmax, 11)
    cf = None

    for r, (scale, k_r) in enumerate(ROWS):
        ds, m, tr = built[scale]
        adm = np.asarray(ds.irms_arr) >= 50.0
        for c, spd in enumerate(SPEEDS):
            ax = axes[r, c]
            sel = (np.abs(np.asarray(ds.speeds_k) - spd) < 0.1)
            cand = np.where(sel & adm)[0]
            excl = np.where(sel & ~adm)[0]

            ii = np.asarray(ds.irms_arr)[cand]
            pp = np.asarray(ds.phase_arr)[cand]
            gi = np.linspace(ii.min(), ii.max(), 44)
            gp = np.linspace(pp.min(), pp.max(), 44)
            GI, GP = np.meshgrid(gi, gp)
            af = m.predict(np.full(GI.size, spd * 1000.0),
                           GI.ravel(), GP.ravel())
            X, Y = dq(GI.ravel(), GP.ravel())
            cf = ax.tricontourf(X, Y, np.asarray(af, float).ravel(),
                                levels=levels, cmap='viridis', extend='both')

            xd, yq = dq(ii, pp)
            ax.plot(xd, yq, 'o', ms=2.6, mfc='none', mec='#ffffff',
                    mew=0.7, ls='none', zorder=3)
            xt, yt = dq(np.asarray(ds.irms_arr)[list(tr & set(cand))],
                        np.asarray(ds.phase_arr)[list(tr & set(cand))])
            # 표본이 없는 패널은 비워 둔다. 그림 안에 글자를 넣지 않는 것이
            # 이 프로젝트 규칙이고, 빈 패널 자체가 주장이다.
            if len(xt):
                ax.plot(xt, yt, 'o', ms=4.6, mfc='#e65100', mec='#3b1a00',
                        mew=0.6, ls='none', zorder=5)

            # 전달 쌍은 테두리 색으로 묶는다 (화살표만으로는 어느 패널이
            # 어느 패널을 받는지 시선이 흔들린다).
            pair = dict(TRANSFER).get(spd) if r == 1 else None
            src = spd if r == 0 and spd in dict(TRANSFER) else None
            hue = None
            if r == 0 and src is not None:
                hue = PAIR_COLOR[src]
            if r == 1:
                for s_, d_ in TRANSFER:
                    if abs(d_ - spd) < 1e-9:
                        hue = PAIR_COLOR[s_]
            if hue:
                for sp in ax.spines.values():
                    sp.set_color(hue)
                    sp.set_linewidth(1.6)

            ax.set_xlim(-1.05 * np.sqrt(2) * ii.max(), 0.06 * ii.max())
            ax.set_ylim(-0.04 * ii.max(), 1.10 * np.sqrt(2) * ii.max())
            ax.tick_params(labelsize=6.4)
            if r == 0:
                # 윗줄 x 눈금은 지운다 --- 전달 화살표가 지날 띠를 비운다.
                ax.tick_params(labelbottom=False)
                ax.set_title('%g kRPM' % spd, fontsize=8.4, pad=2)
            if c == 0:
                ax.set_ylabel('%s\n$i_q$ [A, pk]' % scale, fontsize=7.6)
            if r == len(ROWS) - 1:
                ax.set_xlabel('$i_d$ [A, pk]', fontsize=7.6)

    for src, dst in TRANSFER:
        a0 = axes[0, SPEEDS.index(src)]
        a1 = axes[1, SPEEDS.index(dst)]
        con = ConnectionPatch(xyA=(0.5, -0.03), coordsA=a0.transAxes,
                              xyB=(0.5, 1.03), coordsB=a1.transAxes,
                              arrowstyle='-|>', mutation_scale=8,
                              lw=1.2, color=PAIR_COLOR[src], zorder=9,
                              connectionstyle='arc3,rad=0.16')
        fig.add_artist(con)

    cb = fig.colorbar(cf, ax=axes, pad=0.012, fraction=0.03)
    cb.set_label('$AF$ [-]', fontsize=7.6)
    cb.ax.tick_params(labelsize=6.4)

    os.makedirs(_FIGDIR, exist_ok=True)
    pdf = os.path.join(_FIGDIR, 'af_transfer_map.pdf')
    png = os.path.join(_FIGDIR, 'af_transfer_map.png')
    fig.savefig(pdf)
    fig.savefig(png, dpi=220)
    plt.close(fig)
    print('저장:', pdf)


if __name__ == '__main__':
    main()
