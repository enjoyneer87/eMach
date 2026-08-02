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

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from jeet_acloss_rbf import plot_flux_torque_scaling_tps   # noqa: E402

# 데이터 루트는 JEET_DATA_ROOT 로 덮어쓸 수 있다 (배포 레포/CI 용).
# 이 그림이 읽는 것은 아래 .mat 하나(2.5 KB)뿐이다 — 모델 하위 폴더가 아니라
# 루트 바로 밑에 있다.
_DATA = os.environ.get("JEET_DATA_ROOT",
                       os.path.join(HERE, "map_exports", "e10"))
MAT = os.path.join(_DATA, "lab_scaling_comparison_e10.mat")
OUT_PDF = os.path.join(_FIGDIR, 'flux_torque_scaling.pdf')
# 지표 JSON 도 데이터 루트 밑에 남긴다 (읽기 전용 루트면 건너뛴다).
OUT_JSON = os.path.join(_DATA, "flux_torque_scaling_metrics.json")


def main() -> int:
    metrics = plot_flux_torque_scaling_tps(MAT, OUT_PDF, k_r=2.0, pole_pairs=4)
    print(json.dumps(metrics, indent=1, ensure_ascii=False, default=float))
    print("저장:", OUT_PDF)
    try:
        with open(OUT_JSON, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=1, ensure_ascii=False, default=float)
        print("저장:", OUT_JSON)
    except OSError as exc:      # 읽기 전용 배포 루트 — 그림은 이미 나왔다
        print(f"[건너뜀] 지표 JSON 미기록 ({OUT_JSON}): {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
