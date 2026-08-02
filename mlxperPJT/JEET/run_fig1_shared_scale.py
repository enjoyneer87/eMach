# -*- coding: utf-8 -*-
"""Fig 1 (fig2_<model>_ts_vs_2d.png) 만 Ref/SC 공통 색 스케일로 재생성.

run_kernel_dim_study.figures() 는 논문에 안 쓰는 4패널 진단 PNG와
J: 드라이브 GIF 까지 함께 만든다. 여기서는 2패널 논문 그림만 뽑는다.
색 스케일은 두 모델 중 큰 vlim(SC)으로 통일한다.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import time

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SHARED_VLIM = 250.484633015896      # A/mm^2 — SC 의 98퍼센타일(둘 중 큰 값)
FIGDIR = _FIGDIR


def main() -> int:
    from jeet_acloss_rbf.manuscript_figs import plot_fig2_kernel_comparison

    spec = importlib.util.spec_from_file_location(
        "kds", os.path.join(HERE, "run_kernel_dim_study.py"))
    kds = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kds)

    # 캡션이 (a),(b)=Ref / (c),(d)=SC 로 부르므로 패널 라벨도 그렇게 준다
    LABELS = {"Ref": ("(a)", "(b)"), "SC": ("(c)", "(d)")}
    for model in ("Ref", "SC"):
        ts, hy, tag, freq, cu_w, cu_h = kds.SOURCES[model]
        out = os.path.join(FIGDIR, "fig2_%s_ts_vs_2d.png" % tag)
        t0 = time.time()
        print("=== %s  vlim=%.1f A/mm^2  ->  %s" % (model, SHARED_VLIM, out))
        plot_fig2_kernel_comparison(
            ts, hy, out, slot_id=kds.SLOT, freq_hz=freq, every=kds.EVERY,
            copper_w_mm=cu_w, copper_h_mm=cu_h, panels=("ts", "2d"),
            panel_labels=LABELS[model], vlim=SHARED_VLIM,
            radial_axis_mm=True)
        print("    %.0f s" % (time.time() - t0))
    print("DONE — Ref/SC 공통 스케일 %.1f A/mm^2" % SHARED_VLIM)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
