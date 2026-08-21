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

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools')))
from jeet_acloss_rbf.repro_env import fig_dir
_FIGDIR = fig_dir()

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
SPD_COLOR = {2.0: '#8d6e63', 4.0: '#00897b',
             8.0: '#2c6fad', 16.0: '#7b1fa2'}


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


def main_hybrid(pl, plt, built):
    """저속 3열은 평면, 앵커 속도 1열만 3-D.

    저속에서 물어야 하는 것은 '어느 점을 골랐나'(SC 는 '하나도 안 골랐다')라
    위치가 명확해야 한다. 앵커 속도에서는 후보 24점을 전량 쓰므로 위치가
    정보를 덜 담고, 대신 kappa 를 학습하는 곳이라 표면 형상이 정보다.

    배치 규칙 세 가지.
      - 패널은 정사각이고 $i_d$ 와 $i_q$ 의 눈금이 부호만 다르게 일치한다.
        두 축이 같은 물리량이므로 축척이 다르면 전류 원이 타원으로 왜곡된다.
      - 행 사이를 넓게 벌려 직선 화살표가 패널을 침범하지 않게 한다.
      - 좌표는 전부 인치로 계산한다. 혼합 투영에서 constrained 레이아웃은
        3-D 축을 평면 축과 같은 크기로 잡지 못한다.
    """
    from matplotlib import cm
    from matplotlib.colors import Normalize
    from matplotlib.patches import FancyArrowPatch
    from matplotlib.ticker import MaxNLocator

    # ---- 인치 단위 배치 ------------------------------------------------
    FW = 7.1
    ML, MR, MT, MB = 0.56, 0.78, 0.30, 0.44   # 여백
    HG, VG = 0.20, 0.50                        # 열 간격, 행 간격(화살표 자리)
    NC, NR = len(SPEEDS) + 1, len(ROWS)   # 마지막 열은 로그 회귀
    PW = (FW - ML - MR - HG * (NC - 1)) / NC
    PH = PW                                    # 정사각
    FH = MT + PH * NR + VG * (NR - 1) + MB
    # dx = -dw 로 두면 3-D 칸의 오른쪽 끝이 열 경계와 정확히 맞아
    # 옆 회귀 패널의 y 라벨을 침범하지 않는다.
    INF = dict(dx=-0.07, dy=-0.16, dw=0.07, dh=0.22)

    def rect(r, c, is3d):
        x = ML + c * (PW + HG)
        y = FH - MT - (r + 1) * PH - r * VG
        w, h = PW, PH
        if is3d:
            x += INF['dx']; y += INF['dy']
            w += INF['dw']; h += INF['dh']
        return [x / FW, y / FH, w / FW, h / FH]

    fig = plt.figure(figsize=(FW, FH))
    vmin = min(built[s][0].af_arr.min() for s, _ in ROWS)
    vmax = max(built[s][0].af_arr.max() for s, _ in ROWS)
    levels = np.linspace(vmin, vmax, 11)
    norm = Normalize(vmin, vmax)
    cf = None

    for r, (scale, _k) in enumerate(ROWS):
        ds, m, tr = built[scale]
        for c, spd in enumerate(SPEEDS):
            is3d = (spd == 16.0)
            ax = fig.add_axes(rect(r, c, is3d),
                              projection='3d' if is3d else None)
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
            tsel = sorted(tr & set(cand.tolist()))
            if tsel:
                xt, yt = dq(np.asarray(ds.irms_arr)[tsel],
                            np.asarray(ds.phase_arr)[tsel])
            lim = 1.07 * np.sqrt(2.0) * ii.max()
            ticks = [t for t in MaxNLocator(4).tick_values(0, lim)
                     if 0 <= t <= lim]

            if is3d:
                ax.plot_surface(X, Y, Z, facecolors=cm.viridis(norm(Z)),
                                rstride=1, cstride=1, linewidth=0,
                                shade=False, antialiased=True, alpha=0.95)
                if tsel:
                    ax.scatter(xt, yt, np.asarray(ds.af_arr)[tsel], s=10,
                               c='#e65100', edgecolors='#3b1a00',
                               linewidths=0.3, depthshade=False)
                ax.set_xlim(-lim, 0.0)
                ax.set_ylim(0.0, lim)
                ax.set_zlim(vmin, vmax)
                ax.set_xticks([-t for t in ticks][::-1])
                ax.set_yticks(ticks)
                ax.zaxis.set_major_locator(MaxNLocator(3))
                # z 눈금 라벨은 지운다. 컬러바가 같은 축척으로 AF 를
                # 이미 주고, 옆 회귀 패널의 y 라벨과 부딪혔다.
                ax.set_zticklabels([])
                ax.view_init(elev=22, azim=-62)
                ax.set_box_aspect((1.0, 1.0, 0.68), zoom=0.96)
                ax.tick_params(labelsize=5.2, pad=-3)
                ax.set_xlabel('$i_d$', fontsize=6.4, labelpad=-9)
                ax.set_ylabel('$i_q$', fontsize=6.4, labelpad=-9)
                for a_ in (ax.xaxis, ax.yaxis, ax.zaxis):
                    a_.pane.set_alpha(0.22)
            else:
                cf = ax.tricontourf(X.ravel(), Y.ravel(), Z.ravel(),
                                    levels=levels, cmap='viridis',
                                    extend='both')
                xc, yc = dq(ii, pp)
                ax.plot(xc, yc, 'o', ms=2.6, mfc='none', mec='#ffffff',
                        mew=0.7, ls='none', zorder=3)
                if tsel:
                    ax.plot(xt, yt, 'o', ms=4.4, mfc='#e65100',
                            mec='#3b1a00', mew=0.6, ls='none', zorder=5)
                ax.set_xlim(-lim, 0.0)
                ax.set_ylim(0.0, lim)
                ax.set_xticks([-t for t in ticks][::-1])
                ax.set_yticks(ticks)
                ax.set_aspect('equal', adjustable='box')
                ax.tick_params(labelsize=6.2)
                if r == 0:
                    ax.tick_params(labelbottom=False)
                else:
                    ax.set_xlabel('$i_d$ [A, pk]', fontsize=7.2, labelpad=1)
                if c > 0:
                    ax.tick_params(labelleft=False)
                if c == 0:
                    ax.set_ylabel('%s\n$i_q$ [A, pk]' % scale,
                                  fontsize=7.4, labelpad=1)
                hue = None
                if r == 0 and spd in PAIR_COLOR:
                    hue = PAIR_COLOR[spd]
                for s_, d_ in TRANSFER:
                    if r == 1 and abs(d_ - spd) < 1e-9:
                        hue = PAIR_COLOR[s_]
                if hue:
                    for sp in ax.spines.values():
                        sp.set_color(hue)
                        sp.set_linewidth(1.6)

        # ---- 5번째 열: 로그 공간 회귀 --------------------------------
        axr = fig.add_axes(rect(r, len(SPEEDS), False))
        for spd in SPEEDS:
            sel = np.abs(np.asarray(ds.speeds_k) - spd) < 0.1
            cand = np.where(sel)[0]
            kap = np.asarray(m.predict_g(np.asarray(ds.irms_arr)[cand],
                                         np.asarray(ds.phase_arr)[cand]),
                             float)
            kap = np.clip(kap, 1e-3, None)
            lk = np.log10(kap)
            f_s = float(np.polyval(m.p_coeffs, spd))
            p_s = (1.0 if m.q_coeffs is None
                   else float(np.polyval(m.q_coeffs, spd)))
            xs = np.linspace(lk.min(), lk.max(), 20)
            axr.plot(xs, np.log10(max(f_s, 1e-6)) + p_s * xs,
                     '-', lw=1.1, color=SPD_COLOR[spd], zorder=3)
            tsel = sorted(tr & set(cand.tolist()))
            if tsel:
                kt = np.clip(np.asarray(
                    m.predict_g(np.asarray(ds.irms_arr)[tsel],
                                np.asarray(ds.phase_arr)[tsel]), float),
                    1e-3, None)
                axr.plot(np.log10(kt),
                         np.log10(np.asarray(ds.af_arr)[tsel]),
                         'o', ms=3.4, mfc=SPD_COLOR[spd], mec='#222222',
                         mew=0.4, ls='none', zorder=5)
        if r == 0:
            # 열 제목 색이 이미 키를 주지만, 회귀 패널만 떼어 보는 독자를
            # 위해 윗줄에 한 번 범례를 단다 (데이터가 없는 좌상단).
            from matplotlib.lines import Line2D
            axr.legend(handles=[Line2D([], [], color=SPD_COLOR[v], lw=1.2,
                                       label='%g kRPM' % v)
                                for v in SPEEDS],
                       fontsize=5.0, loc='upper left', frameon=False,
                       handlelength=1.0, handletextpad=0.4,
                       labelspacing=0.18, borderpad=0.1)
        axr.tick_params(labelsize=6.2)
        axr.set_xlabel(r'$\log_{10}\kappa$', fontsize=7.2, labelpad=1)
        axr.set_ylabel(r'$\log_{10} AF$', fontsize=7.2, labelpad=1)
        axr.grid(True, ls=':', lw=0.4, color='#dddddd')
        axr.set_axisbelow(True)

    # 각주 마커는 앞에 위첨자로. mathtext 에 \ddagger 가 없어 두 번째
    # 기호는 \S 를 쓰고, tex 쪽 각주 기호도 같은 것으로 맞춘다.
    NOTE = {16.0: r'${}^{\dagger}$'}
    for c, spd in enumerate(SPEEDS):
        fig.text((ML + c * (PW + HG) + PW / 2) / FW,
                 (FH - MT + 0.06) / FH,
                 '%s%g kRPM' % (NOTE.get(spd, ''), spd),
                 ha='center', va='bottom', fontsize=8.6,
                 color=SPD_COLOR[spd])
    fig.text((ML + len(SPEEDS) * (PW + HG) + PW / 2) / FW,
             (FH - MT + 0.06) / FH, r'${}^{\S}$log-space fit',
             ha='center', va='bottom', fontsize=8.6, color='#111111')

    # 직선 화살표. 두 쌍 모두 두 열 왼쪽으로 가므로 서로 평행하다.
    for src, dst in TRANSFER:
        cs, cd = SPEEDS.index(src), SPEEDS.index(dst)
        x0 = (ML + cs * (PW + HG) + PW / 2) / FW
        x1 = (ML + cd * (PW + HG) + PW / 2) / FW
        y0 = (FH - MT - PH - 0.05) / FH
        y1 = (FH - MT - PH - VG + 0.05) / FH
        fig.add_artist(FancyArrowPatch(
            (x0, y0), (x1, y1), transform=fig.transFigure,
            arrowstyle='-|>', mutation_scale=9, lw=1.3,
            color=PAIR_COLOR[src], zorder=9, shrinkA=0, shrinkB=0))

    cax = fig.add_axes([(FW - MR + 0.30) / FW, MB / FH,
                        0.10 / FW, (FH - MT - MB) / FH])
    cb = fig.colorbar(cf, cax=cax)
    cb.set_label('$AF$ [-]', fontsize=7.4)
    cb.ax.tick_params(labelsize=6.2)

    out = os.path.join(_FIGDIR, 'af_transfer_map_hybrid')
    fig.savefig(out + '.pdf')
    fig.savefig(out + '.png', dpi=220)
    plt.close(fig)
    print('저장:', out + '.pdf')


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
    ap.add_argument('--mode', default='both', choices=('flat', '3d', 'hybrid', 'both'))
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
    if args.mode in ('hybrid', 'both'):
        main_hybrid(pl, plt, built)
    if args.mode in ('3d', 'hybrid'):
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
