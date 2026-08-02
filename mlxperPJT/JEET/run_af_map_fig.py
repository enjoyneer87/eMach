# -*- coding: utf-8 -*-
"""Fig 11 (AF 맵 + 3-D 곡면) 재생성기.

채택 모델(SC, transfer 플랜)의 AF 를 id--iq 평면 등고선과 3-D 곡면으로
그린다. 두 패널 모두 그림 안에 제목/주석을 넣지 않는 저널 판본
(manuscript_figs)을 쓴다 --- 서브캡션 (a)/(b) 는 tex 에서 단다.

입력은 Map_Summary JSON 두 개뿐이다 (SC + 도너 Ref: transfer 모드가
Ref 를 도너로 세운다). 데이터 루트는 JEET_DATA_ROOT 로 옮길 수 있다.

  python run_af_map_fig.py [--scale SC]
"""
import argparse
import os
import sys

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.pipeline import AcLossPipeline          # noqa: E402
from jeet_acloss_rbf.manuscript_figs import (plot_af_map_dq,  # noqa: E402
                                             plot_af_surface_3d)

FIGDIR = _FIGDIR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", default="SC",
                    help="모델 스케일 (기본 SC — 원고 Fig 11)")
    a = ap.parse_args()

    pl = AcLossPipeline()
    ds = pl.load_dataset(a.scale)
    md = pl.build_model(a.scale)

    # (a) id--iq 평면 AF 등고선 + 표본 산점
    out = os.path.join(FIGDIR, "AF_map_visualization.pdf")
    plot_af_map_dq(ds, md, out)
    print("Fig11a:", out)

    # (b) 같은 모델의 3-D AF 곡면
    out = os.path.join(FIGDIR, "AF_3D_surface.pdf")
    plot_af_surface_3d(ds, md, out)
    print("Fig11b:", out)


if __name__ == "__main__":
    main()
