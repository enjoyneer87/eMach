# -*- coding: utf-8 -*-
"""도너를 자기 Full-FEA 밖에서 읽는 대가 (저자 지적 2026-08-25).

앞 시안은 도너 대역을 2~16 kRPM 으로 잡았는데, 그것은 검증 스윕이지
제안 방식의 예산이 아니다.  Table 1 이 정하는 자체 Full-FEA 는 이렇다.

  Ref     2 / 4 / 8 / 16 kRPM   (24 + 4x3 = 36 점)   --- 전대역 도너
  SC      8 / 16 kRPM 뿐        (3 + 24 = 27 점)     --- 고속만 자체 표집
  HalfSC  없음                                        --- 공짜로 따라오는 변형체

그러면 논지가 예산에서 유도된다.  SC 의 속도를 Ref 좌표로 옮기면

  SC  2 k -> Ref  8 k   O        SC  8 k -> Ref 32 k   X
  SC  4 k -> Ref 16 k   O        SC 16 k -> Ref 64 k   X

이고, SC 가 자체 표집하는 8 / 16 kRPM 이 정확히 Ref 가 못 닿는 두 속도다.
비대칭 플랜은 여유 마진이 아니라 도너 대역이 정해 준 값이다.

  python run_donor_reach_cost_fig.py
"""
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
KR = {"ref": 1.0, "halfsc": 1.5, "sc": 2.0}
NAME = {"ref": "Ref", "halfsc": "HalfSC", "sc": "SC"}
COL = {"ref": "#8d6e63", "sc": "#2c6fad"}
# 제안 라인업 순서.  Ref 가 먼저 서고, SC 가 자체 고속 표본으로 서고,
# HalfSC 는 그 둘에서 읽어 온다.  HalfSC 는 도너가 아니다 --- 자체
# Full-FEA 가 없다.
PAIRS = (("sc", ("ref",)), ("halfsc", ("ref", "sc")))


def wmae(af, af_true, watt):
    e = np.abs((af - af_true) / af_true) * 100.0
    return float(np.sum(watt * e) / np.sum(watt))


def own_speeds(D, d):
    return np.unique(np.round(D[d + "_train_speeds_k"], 3))


def collect(D):
    by_donor = {d: [] for d in COL}
    for t, donors in PAIRS:
        af_t, f_ac = D[t + "_af_true"], D[t + "_f_ac"]
        for d in donors:
            af = D["%s_af_from_%s" % (t, d)]
            own = own_speeds(D, d)
            for spd in SPEEDS:
                m = np.abs(D[t + "_speeds_k"] - spd) < 0.1
                w_d = spd * (KR[t] / KR[d]) ** 2
                zone = ("above" if w_d > own.max() + 1e-6 else
                        "below" if w_d < own.min() - 1e-6 else "inside")
                by_donor[d].append(dict(w_d=w_d, tgt=t, spd=spd, zone=zone,
                                        err=wmae(af[m], af_t[m], f_ac[m])))
    for d in by_donor:
        by_donor[d].sort(key=lambda q: q["w_d"])
    return by_donor


def main() -> int:
    plt = _journal_rc()
    D = dict(np.load(NPZ))
    by_donor = collect(D)
    top = max(own_speeds(D, d).max() for d in COL)      # 둘 다 16 kRPM

    fig = plt.figure(figsize=(3.45, 3.35))
    ax = fig.add_axes([0.155, 0.335, 0.825, 0.635])
    rug = fig.add_axes([0.155, 0.115, 0.825, 0.170], sharex=ax)

    for a in (ax, rug):
        a.axvspan(top, 80, color="#fbe9e7", zorder=0)
        a.axvline(top, color="#c62828", lw=0.8, zorder=1)

    for d, pts in by_donor.items():
        ax.plot([q["w_d"] for q in pts], [q["err"] for q in pts], lw=0.8,
                ls=(0, (4, 2)), color=COL[d], zorder=3)
        for z, mk, sz in (("inside", "o", 20), ("below", "v", 22),
                          ("above", "D", 20)):
            s = [q for q in pts if q["zone"] == z]
            if s:
                ax.scatter([q["w_d"] for q in s], [q["err"] for q in s],
                           marker=mk, s=sz, c=COL[d], edgecolors="w",
                           linewidths=0.4, zorder=4)
        ax.scatter([], [], marker="s", s=20, c=COL[d], edgecolors="w",
                   linewidths=0.4, label="read %s" % NAME[d])

    # SC 가 자체로 채우는 두 칸.  Ref 를 32 k / 64 k 에서 읽어야 하는 자리다.
    hi = [q for q in by_donor["ref"] if q["tgt"] == "sc"
          and q["zone"] == "above"]
    m16 = np.abs(D["sc_speeds_k"] - 16.0) < 0.1
    e3 = wmae(np.load(NPZ_SC)["af_plus3"][m16], D["sc_af_true"][m16],
              D["sc_f_ac"][m16])
    # 붉은 구역에 놓인 SC 표적 두 칸이 곧 SC 가 자체로 푸는 두 속도다.
    # 8 k 는 3 점, 16 k 는 24 점.  아래 예산 칸과 짝이 맞는다.
    own = {8.0: wmae(D["sc_af_own"][np.abs(D["sc_speeds_k"] - 8.0) < 0.1],
                     D["sc_af_true"][np.abs(D["sc_speeds_k"] - 8.0) < 0.1],
                     D["sc_f_ac"][np.abs(D["sc_speeds_k"] - 8.0) < 0.1]),
           16.0: e3}
    for q in hi:
        if q["spd"] not in own:
            continue
        e_o = own[q["spd"]]
        ax.annotate("", (q["w_d"], e_o * 1.25),
                    (q["w_d"], q["err"] * 0.82),
                    arrowprops=dict(arrowstyle="->", lw=1.0,
                                    color="#2e7d32"))
        ax.scatter([q["w_d"]], [e_o], marker="*", s=54, c="#2e7d32",
                   edgecolors="w", linewidths=0.4, zorder=5)
    ax.text(26, 1.25, "SC solves 8 and 16 k itself", fontsize=6,
            color="#2e7d32", ha="left", va="center")

    ax.text(top * 1.12, 200, "beyond any donor's\nown Full-FEA",
            fontsize=6.4, color="#b71c1c", ha="left", va="top")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(0.7, 260)
    ax.set_yticks([1, 10, 100])
    ax.set_yticklabels(["1", "10", "100"])
    ax.set_ylabel("zero-shot wMAE [%]", fontsize=8)
    ax.tick_params(labelsize=7, labelbottom=False)
    h = [plt.Line2D([], [], ls="", marker=m, ms=4, mfc="0.45", mec="w",
                    mew=0.4, label=t)
         for m, t in (("o", "inside its own"), ("v", "below its own"),
                      ("D", "above its own"))]
    h += [plt.Line2D([], [], ls="", marker="s", ms=4, mfc=COL[d], mec="w",
                     mew=0.4, label="read %s" % NAME[d]) for d in COL]
    # 왼쪽 아래는 SC 곡선이 지난다.  왼쪽 위가 비어 있다.
    ax.legend(handles=h, fontsize=6, loc="upper left", frameon=True,
              framealpha=0.9, borderpad=0.3, handletextpad=0.2,
              labelspacing=0.2)

    # 아래 칸 --- Table 1 의 예산.  누가 무엇을 실제로 풀었나.
    budget = (("ref", 2, "4 speeds, 36 pts"), ("sc", 1, "2 speeds, 27 pts"))
    for d, y, note in budget:
        o = own_speeds(D, d)
        rug.plot([o.min(), o.max()], [y, y], lw=3.2, color=COL[d],
                 alpha=0.30, solid_capstyle="butt", zorder=2)
        rug.scatter(o, [y] * o.size, marker="|", s=46, c=COL[d],
                    linewidths=1.4, zorder=3)
        rug.text(1.02, y, NAME[d], fontsize=6, color=COL[d], ha="left",
                 va="center")
        rug.text(78, y, note, fontsize=6, color=COL[d], ha="right",
                 va="center")
    rug.text(1.02, 0, "HalfSC", fontsize=6, color="0.45", ha="left",
             va="center")
    rug.text(78, 0, "no Full-FEA of its own", fontsize=6, color="0.45",
             ha="right", va="center")
    rug.set_ylim(-0.8, 2.8)
    rug.set_yticks([])
    rug.set_xlim(0.95, 80)
    rug.set_xticks([1, 2, 4, 8, 16, 32, 64])
    rug.set_xticklabels(["1", "2", "4", "8", "16", "32", "64"])
    rug.set_xlabel("speed at which the donor is read [kRPM]", fontsize=8)
    rug.tick_params(labelsize=7)
    for s in ("left", "right", "top"):
        rug.spines[s].set_visible(False)

    os.makedirs(fig_dir(), exist_ok=True)
    out = os.path.join(fig_dir(), "donor_reach_cost.pdf")
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out[:-4] + ".png", dpi=220, bbox_inches="tight")
    print("저장:", out)
    for d, pts in by_donor.items():
        for q in pts:
            print("  read %-4s @%6.2f k  %-6s  (target %-7s %2g k) %7.2f%%"
                  % (NAME[d], q["w_d"], q["zone"], NAME[q["tgt"]], q["spd"],
                     q["err"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
