"""Fig 2 눈금 통일 두 안 비교 렌더 (세미나 6, 저자 지침 2026-08-21).

A안: Ref/SC 모두 40 mm 간격 — 눈금 숫자 집합을 통일한다.
B안: Ref 40 mm / SC 80 mm — x 축의 기존 관습대로 눈금이 종이 위 같은
     자리에 오고, 숫자 비가 k_r=2 를 그대로 보여 준다.

둘 다 패널 태그는 하단 배치. 임시 폴더에 뽑아 눈으로 고른 뒤 채택본만
fig/ 로 보낸다.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

from jeet_acloss_rbf import plot_field_panels  # noqa: E402

_DATA = os.environ.get("JEET_DATA_ROOT",
                       os.path.join(HERE, "map_exports", "e10"))
FIELDS = os.path.join(_DATA, "fields")
OUTDIR = os.environ.get("JEET_VARIANT_DIR", HERE)

CASES = [
    ("fields_Ref_Hybrid_16k_36deg_OnLoadTorque.npz", "Hybrid", 1.0),
    ("fields_Ref_16k_36deg_OnLoadTorque.npz",        "Full-FEA", 1.0),
    ("fields_SC_Hybrid_4k_36deg_OnLoadTorque.npz",   "Hybrid", 2.0),
    ("fields_SC_4k_36deg_OnLoadTorque.npz",          "Full-FEA", 2.0),
]

VARIANTS = {
    "A_step40_both": [40.0, 40.0, 40.0, 40.0],
    "B_step40_80":   [40.0, 40.0, 80.0, 80.0],
}


def main() -> int:
    cases, k_r = [], []
    for fname, title, kr in CASES:
        p = os.path.join(FIELDS, fname)
        if not os.path.exists(p):
            print(f"[오류] 필드 데이터 없음: {p}")
            return 1
        cases.append((p, title))
        k_r.append(kr)

    for tag, steps in VARIANTS.items():
        out = os.path.join(OUTDIR, f"fig2_{tag}.png")
        plot_field_panels(
            cases, out,
            k_r=k_r,
            show_axes=True,
            compact_labels=True,
            group_labels=["Ref", "SC"],
            tick_step=steps,
            tag_pos="bottom",
        )
        print(f"저장: {out}  ({os.path.getsize(out) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
