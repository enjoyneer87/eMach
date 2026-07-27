"""Fig 11 (fig:mvp_field_validation) — 필드 수준 스케일링 검증 그림 재생성.

세미나2 대응:
  1) 축 박스 + mm 눈금 복원 (rev1 의 ``*_Box.pdf`` 스타일).
     좌표는 이미 mm 이고, 눈금이 있으면 Ref(≈99 mm) 와 SC(≈198 mm) 의
     크기 비 k_r=2 가 축에서 바로 읽힌다.
  2) 행 2 를 ``A/k_r`` 공통 스케일로 정규화.
     SCL-M 은 A -> k_a k_r A 를 예측하므로 정규화하면 두 모델 패널이
     동일해야 한다 --- 색이 같다는 사실 자체가 스케일링 성립의 근거다.
     (기존: Ref ±0.02 / SC ±0.04 로 컬러바가 갈려 관계가 오히려 가려짐)

반작용 자계(current crowding)는 이 그림에서 다루지 않는다. |B| 전역 맵은
철심 포화가 지배해 도체 내부가 뭉개지므로 원리상 보이지 않으며, 정량 근거는
Fig 2 (단일 슬롯 J_e, TS-FEA vs 2-D 재구성)가 담당한다.

실행:
    python run_fig11_mvp_field.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

from jeet_acloss_rbf import plot_field_panels  # noqa: E402

FIELDS = os.path.join(HERE, "map_exports", "e10", "fields")
OUT = r"E:\KDH\Overleaf\JEET-2024_rev1\fig\Bfield_MVP_mesh.pdf"

# (npz, 패널 제목, k_r)  — 열 순서 = Ref 쌍, SC 쌍
# 모델(Ref/SC) 식별은 그룹 헤더가 담당, 열 제목은 기법만 (compact 규칙)
# SC 는 4 kRPM = Ref 16 kRPM 의 상사 대응 운전점 (ω ∝ 1/k_r²) — 두 열이
# 진짜 상사쌍이 되어 A/k_r 공통 스케일 일치가 법칙의 직접 검증이 된다.
CASES = [
    ("fields_Ref_Hybrid_16k_36deg_OnLoadTorque.npz", "Hybrid", 1.0),
    ("fields_Ref_16k_36deg_OnLoadTorque.npz",        "Full-FEA", 1.0),
    ("fields_SC_Hybrid_4k_36deg_OnLoadTorque.npz",   "Hybrid", 2.0),
    ("fields_SC_4k_36deg_OnLoadTorque.npz",          "Full-FEA", 2.0),
]


def main() -> int:
    cases, k_r = [], []
    for fname, title, kr in CASES:
        p = os.path.join(FIELDS, fname)
        if not os.path.exists(p):
            print(f"[오류] 필드 데이터 없음: {p}")
            return 1
        cases.append((p, title))
        k_r.append(kr)

    out = plot_field_panels(
        cases, OUT,
        k_r=k_r,          # A/k_r 공통 스케일
        show_axes=True,   # mm 눈금 박스
        compact_labels=True,          # 행 식별 최좌측 1회, 열 제목 1줄
        group_labels=["Ref", "SC"],   # 모델 식별 = 그룹 헤더 (유지)
    )
    print(f"저장: {out}")
    print(f"  크기: {os.path.getsize(out) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
