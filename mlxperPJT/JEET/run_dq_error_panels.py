# -*- coding: utf-8 -*-
"""부록 B — dq 평면 위의 상사 전달 오차 패널 (저자 요청 2026-08-25).

표 B.2 는 플랜별 wMAE 를 한 숫자로만 준다.  그 숫자가 어디서 오는지가
보이지 않아 저자가 두 번 막혔다 — 무보정 26.9 % 와 제로샷 53 % 가 같은
집계가 아니라는 것, 그리고 실패가 16 kRPM 한 속도에만 국한된다는 것.

여기서는 Fig. 6 과 같은 dq 평면 격자에 오차장을 직접 칠한다.  칸마다 찍는
wMAE 배지는 바로 그 장의 와트가중 평균이므로, 집계 숫자와 그 근원이 한
그림 안에 같이 있다.  도너를 행으로 갈라 놓았다 — 혼합 제로샷은 속도마다
다른 도너에서 받는데, 한 행으로 묶으면 어느 쪽에서 받았는지 알 수 없다.

행 구성 (목표 한 대당)
  1  truth      Full-FEA 로 잰 AF.  속도마다 한 번만 싣는다
  2  uncorrected  AF = 1, 아무것도 보정하지 않았을 때
  3  from <도너1>  제로샷, 자체 Full-FEA 0 점
  4  from <도너2>  같음

입력은 run_dq_error_data.py 가 만든다.

  python run_dq_error_panels.py --target sc
  python run_dq_error_panels.py --target halfsc
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import numpy as np                                       # noqa: E402
import matplotlib                                        # noqa: E402
matplotlib.use("Agg")

from jeet_acloss_rbf.manuscript_figs import _journal_rc   # noqa: E402
from jeet_acloss_rbf.repro_env import fig_dir             # noqa: E402

NPZ = os.path.join(HERE, "map_exports", "e10", "dq_error_panels.npz")
NPZ_SC = os.path.join(HERE, "map_exports", "e10", "SC",
                      "sc_extrapolation_points.npz")
SPEEDS = (2.0, 4.0, 8.0, 16.0)
DONORS = {"halfsc": ("ref", "sc"), "sc": ("ref", "halfsc")}
NAME = {"ref": "Ref", "halfsc": "HalfSC", "sc": "SC"}
KR = {"ref": 1.0, "halfsc": 1.5, "sc": 2.0}

# 색 눈금 상한.  117 % 까지 선형으로 늘리면 대역 내 패널이 전부 백지가 되어
# 구조가 사라진다.  60 % 에서 자르고 넘치는 쪽은 extend 로 표시한다.
ERR_CLIP = 60.0


def dq(irms, phase_deg):
    """(I_rms, beta) -> (i_d, i_q) 진폭.  beta 는 진각이라 q 축에서 잰다.

    run_af_transfer_fig.dq 와 같은 정의다 (Fig. 6 과 같은 평면)."""
    b = np.deg2rad(np.asarray(phase_deg, float))
    a = np.sqrt(2.0) * np.asarray(irms, float)
    return -a * np.sin(b), a * np.cos(b)


def wmae(af_pred, af_true, watt):
    """와트가중 평균 절대 상대오차 [%].

    손실 예측이 P = P_hyb * AF 이므로 손실의 상대오차와 AF 의 상대오차가
    같다.  따라서 이 값이 표 B.2 의 wMAE 와 같은 양이다."""
    e = np.abs((af_pred - af_true) / af_true) * 100.0
    return float(np.sum(watt * e) / np.sum(watt))


def panel_err(ax, x, y, err, norm):
    """오차장 한 칸.  24 점 삼각분할이라 보간을 지어내지 않는다.

    빈 원은 목표 기계의 평가 격자다.  도너의 학습 표본과 혼동하면 안 되므로
    채운 점을 쓰지 않는다 (도너 표본은 donor_overlay 가 주황으로 얹는다)."""
    tp = ax.tricontourf(x, y, err, levels=np.linspace(-ERR_CLIP, ERR_CLIP, 25),
                        cmap="RdBu_r", norm=norm, extend="both")
    ax.scatter(x, y, s=3.2, facecolors="none", edgecolors="0.35",
               linewidths=0.35, zorder=3)
    return tp


def donor_overlay(ax, x, y):
    """도너가 그 속도에 실제로 가진 자체 Full-FEA 표본.

    상사 사상이 도너 속도를 패널 속도로 정확히 옮겨 주는 경우에만 있다.
    개수가 곧 그 칸 예측의 근거다 --- 4 점과 24 점은 다른 이야기다."""
    ax.scatter(x, y, s=9, c="#e65100", edgecolors="#3b1a00", linewidths=0.3,
               zorder=4)


def panel_af(ax, x, y, af, levels):
    """레벨을 열 사이에 공유한다.  levels 를 개수로 주면 패널마다 다른
    눈금을 골라서 색이 서로 비교 불가능해지고 컬러바도 거짓이 된다."""
    tp = ax.tricontourf(x, y, af, levels=levels, cmap="viridis")
    ax.scatter(x, y, s=1.6, c="w", linewidths=0, zorder=3)
    return tp


def style(ax, lim, framed):
    ax.set_xlim(-lim, 0.0)
    ax.set_ylim(0.0, lim)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_linewidth(1.1 if framed else 0.5)
        s.set_color("#c62828" if framed else "0.4")


def axis_key(ax):
    """축 이름은 한 패널에만.  전류원 바깥 왼쪽 쐐기가 비어 있다."""
    ax.set_xlabel("$i_d$", fontsize=7, labelpad=1)
    ax.text(0.04, 0.55, "$i_q$", transform=ax.transAxes, ha="left",
            va="center", fontsize=7)


SEVERE = 10.0     # 배지를 붉게 칠하는 오차 문턱 [%]


def badge(ax, txt, severe):
    """배지 색은 오차 크기, 테두리는 도달 여부.  둘을 한 채널로 묶으면
    도달 밖인데 정확한 칸(아래쪽 외삽)이 나쁜 칸으로 읽힌다."""
    ax.text(0.05, 0.94, txt, transform=ax.transAxes, ha="left", va="top",
            fontsize=6.6, color="#b71c1c" if severe else "0.15",
            bbox=dict(boxstyle="round,pad=0.22", fc="w",
                      ec="#c62828" if severe else "0.6", lw=0.5, alpha=0.9))


def build(D, plt, tgt):
    from matplotlib.colors import TwoSlopeNorm

    p = tgt
    spd_all = D[p + "_speeds_k"]
    af_true, f_ac = D[p + "_af_true"], D[p + "_f_ac"]
    d1, d2 = DONORS[tgt]
    rows = [("$AF$, Full-FEA", None, None, None), ("uncorrected", None, None,
                                                   None)]
    for d in (d1, d2):
        lo, hi = D["%s_reach_%s" % (p, d)]
        n_d = D[d + "_train_speeds_k"].size
        rows.append(("from %s, %d pts\nreach %.1f–%.0f k"
                     % (NAME[d], n_d, lo, hi),
                     D["%s_af_from_%s" % (p, d)], (lo, hi), d))

    plus3 = None
    if tgt == "sc" and os.path.exists(NPZ_SC):
        plus3 = np.load(NPZ_SC)["af_plus3"]

    # VG·MB 는 패널 아래 도너 각주가 들어갈 자리까지 잡는다.
    FW, ML, MR, MT, MB, HG, VG = 7.1, 1.34, 0.86, 0.26, 0.46, 0.10, 0.22
    PW = (FW - ML - MR - HG * 3) / 4
    FH = MT + PW * 4 + VG * 3 + MB
    fig = plt.figure(figsize=(FW, FH))
    norm = TwoSlopeNorm(vmin=-ERR_CLIP, vcenter=0.0, vmax=ERR_CLIP)
    af_lv = np.linspace(af_true.min(), af_true.max(), 13)
    tp = tpa = None

    for r, (lab, af_p, reach, dnr) in enumerate(rows):
        for c, spd in enumerate(SPEEDS):
            m = np.abs(spd_all - spd) < 0.1
            x, y = dq(D[p + "_irms"][m], D[p + "_phase"][m])
            ax = fig.add_axes([(ML + c * (PW + HG)) / FW,
                               (FH - MT - (r + 1) * PW - r * VG) / FH,
                               PW / FW, PW / FH])
            lim = 1.07 * np.sqrt(2.0) * D[p + "_irms"][m].max()

            if r == 0:
                tpa = panel_af(ax, x, y, af_true[m], af_lv)
                style(ax, lim, False)
                ax.set_title("%g kRPM" % spd, fontsize=8, pad=3)
            else:
                v = np.ones(int(m.sum())) if af_p is None else af_p[m]
                framed = reach is not None and not (
                    reach[0] - 1e-6 <= spd <= reach[1] + 1e-6)
                tp = panel_err(ax, x, y,
                               (v - af_true[m]) / af_true[m] * 100.0, norm)
                style(ax, lim, framed)
                e_w = wmae(v, af_true[m], f_ac[m])
                badge(ax, "%.1f%%" % e_w, e_w > SEVERE)
                if dnr is not None:
                    # 이 칸이 도너의 어느 속도에서 오는가.  거기에 도너의
                    # 자체 표본이 실제로 있으면 목표 전류로 환산해 얹는다.
                    w_d = spd * (KR[tgt] / KR[dnr]) ** 2
                    td = np.abs(D[dnr + "_train_speeds_k"] - w_d) < 0.1
                    n_at = int(td.sum())
                    if n_at:
                        donor_overlay(ax, *dq(
                            D[dnr + "_train_irms"][td] * KR[tgt] / KR[dnr],
                            D[dnr + "_train_phase"][td]))
                    # 표본이 그 속도에 정확히 있는지, 없으면 도너 표본
                    # 속도들의 사이인지 바깥인지.  "없음" 이라고만 쓰면
                    # 데이터가 없다는 뜻으로 읽힌다 --- 도너 모델은 연속면
                    # 이라 사이에서는 보간해 읽는다.
                    tsp = D[dnr + "_train_speeds_k"]
                    if n_at:
                        note = "%d pts" % n_at
                    elif w_d < tsp.min():
                        note = "below samples"
                    elif w_d > tsp.max():
                        note = "past samples"
                    else:
                        note = "between samples"
                    # 도너 이름은 행 라벨에 있으니 여기서는 뺀다.  넣으면
                    # 각주가 패널 폭을 넘어 옆 칸과 붙는다.
                    ax.text(0.5, -0.05, "%.3g k, %s" % (w_d, note),
                            transform=ax.transAxes, ha="center", va="top",
                            fontsize=6.0, color="0.35")
                # +3 은 16 k 에만 자체 점을 넣는다.  장이 거의 백지라
                # 패널을 더 쓰지 않고 그 칸에 숫자로만 적는다.
                if plus3 is not None and framed and spd == 16.0 \
                        and r == len(rows) - 1:
                    ax.text(0.05, 0.06, "$+\\,3$ pts $\\rightarrow$ %.1f%%"
                            % wmae(plus3[m], af_true[m], f_ac[m]),
                            transform=ax.transAxes, fontsize=6.4,
                            color="#1b5e20",
                            bbox=dict(boxstyle="round,pad=0.2", fc="w",
                                      ec="#2e7d32", lw=0.5, alpha=0.9))
            if c == 0:
                ax.set_ylabel(lab, fontsize=7.4, labelpad=3)
            # 축 이름은 도너 각주가 없는 행에 둔다.  마지막 행에 두면
            # 각주와 겹친다.
            if c == 0 and r == 1:
                axis_key(ax)

    xb = (FW - MR + 0.12) / FW
    cb = fig.colorbar(tpa, cax=fig.add_axes(
        [xb, (MB + PW * 3 + VG * 3) / FH, 0.14 / FW, PW / FH]))
    cb.set_label("$AF$", fontsize=8)
    cb.ax.tick_params(labelsize=7)
    cb2 = fig.colorbar(tp, extend="both", cax=fig.add_axes(
        [xb, MB / FH, 0.14 / FW, (PW * 3 + VG * 2) / FH]))
    cb2.set_label("prediction error [%]", fontsize=8)
    cb2.ax.tick_params(labelsize=7)
    return fig


def build_chain(D, plt):
    """§4.3 의 세 단계 노력을 그대로 행으로 (저자 지적 2026-08-25).

    앞선 판본들은 도너의 AF 비를 사상점에서 그대로 읽어 왔다.  그것은
    §4.3 이 말하는 세 단계 중 첫 단계(screening)일 뿐이고, 정작 제안하는
    보정은 어느 행에도 없었다.  제안 플랜은 전달량이 비가 아니라 손실이고,
    변형체가 제 하이브리드로 나눠 제 kappa 에 회귀시킨다.

      1  SC 의 truth AF.  자체 27 점(16 k 에 24, 8 k 에 3)을 얹어 kappa 를
         어디서 배우는지를 같이 보인다
      2  무보정 --- 보정이 걷어내야 할 오차
      3  screening (자체 0 점) --- Ref 표본 너머에서 무너진다.  그래서
         변형체가 고속을 자체 표집해야 한다
      4  제안 플랜 (자체 27 점) --- 전맵 0.79 %
    """
    from matplotlib.colors import TwoSlopeNorm

    rows = (("SC\n$AF$, Full-FEA", "sc", None, None),
            ("SC\nuncorrected", "sc", None, None),
            ("SC\nscreening from Ref", "sc", "af_from_ref", "ref"),
            ("SC\nproposed plan, 27 pts", "sc", "af_own", None))
    FW, ML, MR, MT, MB, HG, VG = 7.1, 1.34, 0.86, 0.26, 0.46, 0.10, 0.22
    PW = (FW - ML - MR - HG * 3) / 4
    FH = MT + PW * 4 + VG * 3 + MB
    fig = plt.figure(figsize=(FW, FH))
    norm = TwoSlopeNorm(vmin=-ERR_CLIP, vcenter=0.0, vmax=ERR_CLIP)
    af_lv = np.linspace(D["sc_af_true"].min(), D["sc_af_true"].max(), 13)
    tp = tpa = None

    for r, (lab, p, key, dnr) in enumerate(rows):
        af_true, f_ac = D[p + "_af_true"], D[p + "_f_ac"]
        for c, spd in enumerate(SPEEDS):
            m = np.abs(D[p + "_speeds_k"] - spd) < 0.1
            x, y = dq(D[p + "_irms"][m], D[p + "_phase"][m])
            ax = fig.add_axes([(ML + c * (PW + HG)) / FW,
                               (FH - MT - (r + 1) * PW - r * VG) / FH,
                               PW / FW, PW / FH])
            lim = 1.07 * np.sqrt(2.0) * D[p + "_irms"][m].max()

            if r == 0:
                tpa = panel_af(ax, x, y, af_true[m], af_lv)
                style(ax, lim, False)
                ax.set_title("%g kRPM" % spd, fontsize=8, pad=3)
                own = np.abs(D["sc_train_speeds_k"] - spd) < 0.1
                if own.any():
                    donor_overlay(ax, *dq(D["sc_train_irms"][own],
                                          D["sc_train_phase"][own]))
                    ax.text(0.5, -0.05, "%d own pts" % int(own.sum()),
                            transform=ax.transAxes, ha="center", va="top",
                            fontsize=6.0, color="#bf360c")
            else:
                v = (np.ones(int(m.sum())) if key is None
                     else D["%s_%s" % (p, key)][m])
                framed = False
                if dnr is not None:
                    lo, hi = D["%s_reach_%s" % (p, dnr)]
                    framed = not (lo - 1e-6 <= spd <= hi + 1e-6)
                tp = panel_err(ax, x, y,
                               (v - af_true[m]) / af_true[m] * 100.0, norm)
                style(ax, lim, framed)
                e_w = wmae(v, af_true[m], f_ac[m])
                badge(ax, "%.1f%%" % e_w, e_w > SEVERE)
                if dnr is not None:
                    w_d = spd * (KR[p] / KR[dnr]) ** 2
                    td = np.abs(D[dnr + "_train_speeds_k"] - w_d) < 0.1
                    if td.any():
                        donor_overlay(ax, *dq(
                            D[dnr + "_train_irms"][td] * KR[p] / KR[dnr],
                            D[dnr + "_train_phase"][td]))
                    tsp = D[dnr + "_train_speeds_k"]
                    note = ("%d pts" % int(td.sum()) if td.any() else
                            "below samples" if w_d < tsp.min() else
                            "past samples" if w_d > tsp.max() else
                            "between samples")
                    ax.text(0.5, -0.05, "%.3g k, %s" % (w_d, note),
                            transform=ax.transAxes, ha="center", va="top",
                            fontsize=6.0, color="0.35")
            if c == 0:
                ax.set_ylabel(lab, fontsize=7.4, labelpad=3)
            if c == 0 and r == 1:
                axis_key(ax)

    xb = (FW - MR + 0.12) / FW
    cb = fig.colorbar(tpa, cax=fig.add_axes(
        [xb, (MB + PW * 3 + VG * 3) / FH, 0.14 / FW, PW / FH]))
    cb.set_label("$AF$", fontsize=8)
    cb.ax.tick_params(labelsize=7)
    cb2 = fig.colorbar(tp, extend="both", cax=fig.add_axes(
        [xb, MB / FH, 0.14 / FW, (PW * 3 + VG * 2) / FH]))
    cb2.set_label("prediction error [%]", fontsize=8)
    cb2.ax.tick_params(labelsize=7)
    return fig


def build_lineup(D, plt):
    """라인업 사슬을 절대 dq 축으로 (저자 지적 2026-08-25).

    행마다 목표가 바뀌는데 패널을 각자 최대전류로 정규화하면 920 A 기계와
    690 A 기계가 같은 크기로 보인다.  캡션으로 설명할 일이 아니라 배치로
    드러날 일이다 --- 축을 공유하면 원호 반경이 곧 k_r 이 되어 SCL-M 의
    I \\propto k_r 이 그림의 기하가 된다.  목표가 바뀌는 자리에는 구분선을
    긋는다.
    """
    from matplotlib.colors import TwoSlopeNorm

    # truth AF 행은 싣지 않는다 (저자 결정 2026-08-25).  같은 평면의 AF
    # 면은 Fig. 6 이 이미 그린다.  SC 자체 표본의 위치는 proposed 행에
    # 얹는다 --- 그 행이 그 점들로 적합된 행이라 그게 논리적 자리다.
    blocks = ((r"target SC  ($k_r{=}2$),  27 own Full-FEA points",
               (("uncorrected", "sc", None, None),
                ("screening from Ref", "sc", "af_from_ref", "ref"),
                ("proposed plan, 27 pts", "sc", "af_own", "own"))),
              (r"target HalfSC  ($k_r{=}1.5$),  no Full-FEA of its own",
               (("screening, nearest donor", "halfsc", "af_mixed",
                 "mixed"),)))
    rows = [(lab, p, k, d) for _, rs in blocks for lab, p, k, d in rs]
    n_r = len(rows)
    # 블록 머리글이 들어갈 자리.  행 사이 간격보다 넉넉해야 구분이 산다.
    BG = 0.30
    # VG 는 눈금 라벨 + 축 이름 + 도너 각주가 다 들어갈 만큼 준다.
    FW, ML, MR, MT, MB, HG, VG = 7.1, 1.34, 0.86, 0.42, 0.46, 0.10, 0.32
    PW = (FW - ML - MR - HG * 3) / 4
    FH = MT + PW * n_r + VG * (n_r - 1) + BG + MB
    fig = plt.figure(figsize=(FW, FH))
    norm = TwoSlopeNorm(vmin=-ERR_CLIP, vcenter=0.0, vmax=ERR_CLIP)
    # 모든 패널이 쓰는 하나의 절대 축.  가장 큰 기계에 맞춘다.
    glim = 1.07 * np.sqrt(2.0) * max(D[p + "_irms"].max()
                                     for _, p, _, _ in rows)
    tp = None
    r = 0

    for b, (btitle, brows) in enumerate(blocks):
        y_head = FH - MT - r * (PW + VG) - b * BG
        fig.text(ML / FW, (y_head + 0.10) / FH, btitle, fontsize=8,
                 ha="left", va="bottom", color="0.2")
        if b:
            fig.add_artist(plt.Line2D(
                [(ML - 0.30) / FW, (FW - MR) / FW],
                [(y_head + 0.06) / FH] * 2, color="0.55", lw=0.8))
        for j, (lab, p, key, dnr) in enumerate(brows):
            af_true, f_ac = D[p + "_af_true"], D[p + "_f_ac"]
            y0 = y_head - PW - j * (PW + VG)
            for c, spd in enumerate(SPEEDS):
                m = np.abs(D[p + "_speeds_k"] - spd) < 0.1
                x, y = dq(D[p + "_irms"][m], D[p + "_phase"][m])
                ax = fig.add_axes([(ML + c * (PW + HG)) / FW,
                                   y0 / FH, PW / FW, PW / FH])
                if True:
                    v = (np.ones(int(m.sum())) if key is None
                         else D["%s_%s" % (p, key)][m])
                    # 혼합 행은 속도마다 도너가 다르다.  그걸 각주에
                    # 적어야 어느 기계에서 받았는지 알 수 있다.
                    dn = dnr
                    if dnr == "mixed":
                        dn = str(D[p + "_mixed_donor"][c])
                    elif dnr == "own":
                        dn = None
                        own = np.abs(D[p + "_train_speeds_k"] - spd) < 0.1
                        if own.any():
                            donor_overlay(ax_own_pts := ax, *dq(
                                D[p + "_train_irms"][own],
                                D[p + "_train_phase"][own]))
                            ax.text(0.5, -0.05,
                                    "%d own pts" % int(own.sum()),
                                    transform=ax.transAxes, ha="center",
                                    va="top", fontsize=6.0, color="#bf360c")
                    framed = False
                    if dn is not None:
                        lo, hi = D["%s_reach_%s" % (p, dn)]
                        framed = not (lo - 1e-6 <= spd <= hi + 1e-6)
                    tp = panel_err(ax, x, y,
                                   (v - af_true[m]) / af_true[m] * 100.0,
                                   norm)
                    style(ax, glim, framed)
                    e_w = wmae(v, af_true[m], f_ac[m])
                    badge(ax, "%.1f%%" % e_w, e_w > SEVERE)
                    if dn is not None:
                        w_d = spd * (KR[p] / KR[dn]) ** 2
                        tsp = D[dn + "_train_speeds_k"]
                        td = np.abs(tsp - w_d) < 0.1
                        if td.any():
                            donor_overlay(ax, *dq(
                                D[dn + "_train_irms"][td] * KR[p] / KR[dn],
                                D[dn + "_train_phase"][td]))
                        note = ("%d pts" % int(td.sum()) if td.any() else
                                "below samples" if w_d < tsp.min() else
                                "past samples" if w_d > tsp.max() else
                                "between samples")
                        pre = "%s " % NAME[dn] if dnr == "mixed" else ""
                        ax.text(0.5, -0.05, "%s%.3g k, %s" % (pre, w_d, note),
                                transform=ax.transAxes, ha="center",
                                va="top", fontsize=6.0, color="0.35")
                if r == 0:
                    ax.set_title("%g kRPM" % spd, fontsize=8, pad=3)
                if c == 0:
                    ax.set_ylabel(lab, fontsize=7.4, labelpad=3)
                    if r == 0:
                        # 절대 축이라는 것을 눈금 하나로 못박는다.  이게
                        # 없으면 원호 크기 차이가 우연으로 읽힌다.
                        pk = -np.sqrt(2.0) * D["sc_irms"].max()
                        axis_key(ax)
                        ax.set_xticks([pk, 0.0])
                        ax.set_xticklabels(["%.0f A" % pk, "0"], fontsize=6)
            r += 1

    # AF 행이 빠졌으니 컬러바도 오차 하나뿐이다.
    cb2 = fig.colorbar(tp, extend="both", cax=fig.add_axes(
        [(FW - MR + 0.12) / FW, MB / FH, 0.14 / FW,
         (FH - MT - MB) / FH]))
    cb2.set_label("prediction error [%]", fontsize=8)
    cb2.ax.tick_params(labelsize=7)
    return fig


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target",
                    choices=("halfsc", "sc", "chain", "lineup"),
                    default="sc")
    a = ap.parse_args()
    plt = _journal_rc()
    D = dict(np.load(NPZ))

    fig = ({"chain": build_chain, "lineup": build_lineup}[a.target](D, plt)
           if a.target in ("chain", "lineup") else build(D, plt, a.target))
    os.makedirs(fig_dir(), exist_ok=True)
    out = os.path.join(fig_dir(), "dq_error_panels_%s.pdf" % a.target)
    fig.savefig(out)
    fig.savefig(out[:-4] + ".png", dpi=200)
    print("저장:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
