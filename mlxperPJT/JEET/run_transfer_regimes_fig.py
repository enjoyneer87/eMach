# -*- coding: utf-8 -*-
"""부록 B "Direction of transfer" 를 위한 그림 (저자 지적 2026-08-25).

표 B.2 는 플랜 이름과 wMAE 를 나열할 뿐이라, 문단이 실제로 주장하는 것이
표에 안 보인다.  그 문단의 변수는 하나다 --- 사상된 목표 속도가 도너의
상사 도달 구간 안이냐 밖이냐.  그러면 축도 그거 하나면 된다.

가족의 (도너 -> 목표, 속도) 16 쌍을 전부 찍는다.  x 는 도달 구간 대비
초과율

    ratio = max(w / hi,  lo / w),      [lo, hi] = 목표 좌표의 도달 구간

이고 1 이 경계다.  y 는 그 대역의 wMAE.

읽히는 것 세 가지.
  - 도달 안쪽 10 쌍이 1.1~5.3 % 에 모인다.  도너도 목표도 상관없다
  - 위로 크게 나가면 무너진다.  2 배에서 28 %, 4 배에서 117 %
  - 같은 1.78 배라도 위로는 53 %, 아래로는 4.9 %.  방향이 11 배를 가른다

원고의 "separates the two regimes cleanly" 는 큰 초과에서만 참이다.
1.125 배 초과가 3.81 % 로 안쪽 밴드에 겹치므로, 경계 자체가 아니라 위쪽
초과의 크기가 문제라는 것이 이 그림의 정직한 진술이다.

  python run_transfer_regimes_fig.py
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
PAIRS = (("sc", ("ref", "halfsc")), ("halfsc", ("ref", "sc")))
NAME = {"ref": "Ref", "halfsc": "HalfSC", "sc": "SC"}
COL = {"sc": "#2c6fad", "halfsc": "#00897b"}


def wmae(af, af_true, watt):
    e = np.abs((af - af_true) / af_true) * 100.0
    return float(np.sum(watt * e) / np.sum(watt))


def collect(D):
    out = []
    for p, donors in PAIRS:
        t, f = D[p + "_af_true"], D[p + "_f_ac"]
        for d in donors:
            lo, hi = D["%s_reach_%s" % (p, d)]
            af = D["%s_af_from_%s" % (p, d)]
            for spd in SPEEDS:
                m = np.abs(D[p + "_speeds_k"] - spd) < 0.1
                ratio = max(spd / hi, lo / spd)
                kind = ("inside" if ratio <= 1 + 1e-9
                        else "above" if spd > hi else "below")
                out.append(dict(tgt=p, dnr=d, spd=spd, ratio=ratio,
                                kind=kind, err=wmae(af[m], t[m], f[m])))
    return out


def main() -> int:
    plt = _journal_rc()
    D = dict(np.load(NPZ))
    pts = collect(D)

    fig, ax = plt.subplots(figsize=(3.45, 2.85))
    ax.set_xscale("log")
    ax.set_yscale("log")

    # 경계 오른쪽이 외삽 영역.  "실패" 라고 칠하지는 않는다 --- 1.125 배는
    # 밖인데도 3.8 % 다.
    ax.axvspan(1.0, 6.0, color="0.92", zorder=0)
    ax.axvline(1.0, color="0.45", lw=0.8, zorder=1)

    for p, lab in (("sc", "SC"), ("halfsc", "HalfSC")):
        e_unc = wmae(np.ones_like(D[p + "_af_true"]), D[p + "_af_true"],
                     D[p + "_f_ac"])
        ax.axhline(e_unc, color=COL[p], lw=0.7, ls=(0, (5, 3)), zorder=1)
        # 왼쪽 위는 비어 있다.  오른쪽에 두면 16 k 주석과 부딪힌다.
        ax.text(0.36, e_unc * 1.05, "%s uncorrected" % lab, fontsize=6,
                color=COL[p], ha="left", va="bottom")

    mk = {"inside": ("o", 20), "above": ("^", 26), "below": ("v", 26)}
    for k in ("inside", "above", "below"):
        for p in ("sc", "halfsc"):
            s = [q for q in pts if q["kind"] == k and q["tgt"] == p]
            if not s:
                continue
            ax.scatter([q["ratio"] for q in s], [q["err"] for q in s],
                       marker=mk[k][0], s=mk[k][1], c=COL[p],
                       edgecolors="w", linewidths=0.4, zorder=4)

    # 세 개만 이름을 단다.  방향이 가르는 쌍과 최악값이다.  전부 점 옆에
    # 붙여 지시선을 없앤다 --- x=1.78 에는 회수 화살표가 지나간다.
    tag = {("sc", "halfsc", 16.0): ("SC 16 k from HalfSC", 0.88, "right"),
           ("sc", "ref", 16.0): ("SC 16 k from Ref", 0.92, "right"),
           ("halfsc", "sc", 2.0): ("HalfSC 2 k from SC,\ndownward",
                                   1.16, "left")}
    for q in pts:
        k = (q["tgt"], q["dnr"], q["spd"])
        if k in tag:
            txt, dx, ha = tag[k]
            ax.text(q["ratio"] * dx, q["err"], txt, fontsize=6,
                    color=COL[q["tgt"]], ha=ha, va="center")

    # 자체 3 점이 그 칸을 어디로 되돌리는지.  문단의 결론이 이 화살표다.
    r16 = [q for q in pts if (q["tgt"], q["dnr"], q["spd"])
           == ("sc", "halfsc", 16.0)][0]
    m16 = np.abs(D["sc_speeds_k"] - 16.0) < 0.1
    e3 = wmae(np.load(NPZ_SC)["af_plus3"][m16], D["sc_af_true"][m16],
              D["sc_f_ac"][m16])
    ax.annotate("", (r16["ratio"], e3 * 1.15), (r16["ratio"],
                                                r16["err"] * 0.88),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="#2e7d32"))
    ax.scatter([r16["ratio"]], [e3], marker="*", s=52, c="#2e7d32",
               edgecolors="w", linewidths=0.4, zorder=5)
    ax.text(r16["ratio"] * 0.88, e3, "$+\\,3$ $\\kappa$-span pts", fontsize=6,
            color="#2e7d32", ha="right", va="center")

    ax.set_xlim(0.34, 6.0)
    ax.set_ylim(0.7, 220)
    ax.set_xticks([0.5, 1, 2, 4])
    ax.set_xticklabels(["0.5", "1", "2", "4"])
    ax.set_yticks([1, 10, 100])
    ax.set_yticklabels(["1", "10", "100"])
    ax.set_xlabel("mapped speed / donor reach", fontsize=8)
    ax.set_ylabel("zero-shot wMAE [%]", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.text(0.985, 210, "beyond reach", fontsize=6.4, color="0.4",
            ha="left", va="top")

    h = [plt.Line2D([], [], ls="", marker=m, ms=4, mfc="0.45", mec="w",
                    mew=0.4, label=t)
         for m, t in (("o", "inside reach"), ("^", "above reach"),
                      ("v", "below reach"))]
    h += [plt.Line2D([], [], ls="", marker="s", ms=4, mfc=COL[p], mec="w",
                     mew=0.4, label=n)
          for p, n in (("sc", "target SC"), ("halfsc", "target HalfSC"))]
    ax.legend(handles=h, fontsize=6, loc="lower right", frameon=True,
              framealpha=0.9, borderpad=0.3, handletextpad=0.3,
              labelspacing=0.25)

    os.makedirs(fig_dir(), exist_ok=True)
    out = os.path.join(fig_dir(), "transfer_regimes.pdf")
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out[:-4] + ".png", dpi=220, bbox_inches="tight")
    print("저장:", out)
    for q in sorted(pts, key=lambda z: z["ratio"]):
        print("  %-7s from %-7s %5g k  ratio %5.3f  %-7s %7.2f%%"
              % (NAME[q["tgt"]], NAME[q["dnr"]], q["spd"], q["ratio"],
                 q["kind"], q["err"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
