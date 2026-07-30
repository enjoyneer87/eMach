# -*- coding: utf-8 -*-
"""Fig 9 (fig:global_circuit_validation) 러너 — TPS 재구성 + 지표 JSON 아카이브.

extractLabScalingComparison_e10.m 이 만든 lab_scaling_comparison_e10.mat 을 읽어
fig/flux_torque_scaling.pdf 를 그리고, 본문 §5.2 인용 지표(토크 정규화 편차 등)를
map_exports/e10/flux_torque_scaling_metrics.json 에 보존한다.
(2026-07-30 수치 감사에서 '평균 0.23% 산출물 미보관'으로 지적된 갭을 닫는 러너 —
이전에는 함수 호출이 세션 임시로만 수행되어 커밋되지 않았다.)
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from jeet_acloss_rbf import plot_flux_torque_scaling_tps   # noqa: E402

MAT = os.path.join(HERE, "map_exports", "e10", "lab_scaling_comparison_e10.mat")
OUT_PDF = r"E:\KDH\Overleaf\JEET-2024_rev1\fig\flux_torque_scaling.pdf"
OUT_JSON = os.path.join(HERE, "map_exports", "e10",
                        "flux_torque_scaling_metrics.json")


def main() -> int:
    metrics = plot_flux_torque_scaling_tps(MAT, OUT_PDF, k_r=2.0, pole_pairs=4)
    print(json.dumps(metrics, indent=1, ensure_ascii=False, default=float))
    json.dump(metrics, open(OUT_JSON, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False, default=float)
    print("저장:", OUT_PDF)
    print("저장:", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
