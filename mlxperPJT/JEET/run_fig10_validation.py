# -*- coding: utf-8 -*-
"""Fig 10 — SC 검증 parity (AcLossPipeline 검증 그림, 전 부하점 평가).

노트북 02 의 검증 셀을 스크립트로 옮긴 것 — 수치·그림 동일.
산출: <JEET_FIGDIR>/RBF_correction_validation_SC.png
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools')))
from jeet_acloss_rbf.repro_env import fig_dir
from jeet_acloss_rbf.pipeline import AcLossPipeline


def main():
    os.makedirs(fig_dir(), exist_ok=True)
    out = os.path.join(fig_dir(), 'RBF_correction_validation_SC.png')
    print(AcLossPipeline().make_validation_figure(
        'SC', out, eval_all_load_points=True))


if __name__ == '__main__':
    main()
