# -*- coding: utf-8 -*-
"""em2struct.viz — 맵핑 QA 시각화(matplotlib, Agg).

plot_mapping : 소스 vs 타깃 힘 화살표 + 크기 산점 + 보존 막대. 맵핑이 물리적으로
               타당한지(위치·크기·합력 보존) 한눈에 검수.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .core import ForceField, MappingResult, conservation_report


def plot_mapping(
    source: ForceField,
    result: MappingResult,
    path: str,
    col: int = 0,
    plane: str = "xy",
    title: str = "em2struct mapping QA",
    quiver_scale: Optional[float] = None,
    dpi: int = 150,
):
    """소스/타깃 힘장 비교도 저장.

    col   : 표시할 시간스텝/하모닉 열.
    plane : 투영면 'xy'|'xz'|'yz'.
    """
    ax_idx = {"xy": (0, 1), "xz": (0, 2), "yz": (1, 2)}[plane]
    a, b = ax_idx
    sp = source.points
    sf = source.as_nodal_forces()[:, :, col]
    tp = result.target.nodes
    tf = result.forces[:, :, col]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    # (1) 화살표: 소스(회색) vs 타깃(빨강).
    # ⚠️ 두 quiver 에 **공통 스케일**을 강제해야 길이 비교가 성립한다(각각
    #    오토스케일하면 서로 다른 배율이 걸려 시각적으로 오해를 준다).
    ax = axes[0]
    if quiver_scale is None:
        span = max(np.ptp(sp[:, a]), np.ptp(sp[:, b]), 1e-12)
        fmax = max(np.abs(np.hypot(sf[:, a], sf[:, b])).max(),
                   np.abs(np.hypot(tf[:, a], tf[:, b])).max(), 1e-30)
        quiver_scale = fmax / (0.15 * span)   # 최대 화살표 ≈ 도면폭의 15%
    ax.quiver(sp[:, a], sp[:, b], sf[:, a], sf[:, b], color="#888",
              angles="xy", scale_units="xy", scale=quiver_scale, width=0.004,
              label=f"source ({source.quantity.value})")
    ax.quiver(tp[:, a], tp[:, b], tf[:, a], tf[:, b], color="#d0342c",
              angles="xy", scale_units="xy", scale=quiver_scale, width=0.003,
              alpha=0.75, label="target nodal force")
    ax.set_aspect("equal"); ax.set_title(f"force vectors ({plane}, col={col})")
    ax.set_xlabel(plane[0]); ax.set_ylabel(plane[1]); ax.legend(fontsize=8)

    # (2) 크기 산점(위치별)
    ax = axes[1]
    smag = np.linalg.norm(sf, axis=1)
    tmag = np.linalg.norm(tf, axis=1)
    s1 = ax.scatter(sp[:, a], sp[:, b], c=smag, cmap="Greys", s=14, label="source")
    s2 = ax.scatter(tp[:, a], tp[:, b], c=tmag, cmap="Reds", s=22, marker="s",
                    edgecolors="k", linewidths=0.2, label="target")
    ax.set_aspect("equal"); ax.set_title("force magnitude")
    ax.set_xlabel(plane[0]); ax.set_ylabel(plane[1])
    fig.colorbar(s2, ax=ax, fraction=0.046, label="|F| target [N]")

    # (3) 보존 막대
    ax = axes[2]
    rep = conservation_report(source, result)
    labels = ["Fx", "Fy", "Fz"]
    x = np.arange(3); w = 0.35
    ax.bar(x - w/2, rep.src_force[:, col], w, label="source", color="#888")
    ax.bar(x + w/2, rep.tgt_force[:, col], w, label="target", color="#d0342c")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("total force [N]")
    ax.set_title(f"conservation\nΣF rel.err={rep.force_rel_err:.2e}  "
                 f"ΣM rel.err={rep.moment_rel_err:.2e}")
    ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path
