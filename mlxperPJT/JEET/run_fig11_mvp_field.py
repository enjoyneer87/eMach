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

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools')))
from jeet_acloss_rbf.repro_env import fig_dir
_FIGDIR = fig_dir()

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))

from jeet_acloss_rbf import plot_field_panels_split  # noqa: E402

# 데이터 루트는 JEET_DATA_ROOT 로 덮어쓸 수 있다 (배포 레포/CI 용).
# 이 그림이 읽는 것은 아래 CASES 의 npz 네 개(합 1.2 MB)뿐이다.
_DATA = os.environ.get("JEET_DATA_ROOT",
                       os.path.join(HERE, "map_exports", "e10"))
FIELDS = os.path.join(_DATA, "fields")
OUT = os.path.join(_FIGDIR, 'Bfield_MVP_mesh.pdf')

# (npz, 패널 제목, k_r)  — 열 순서 = Ref 쌍, SC 쌍
# 모델(Ref/SC) 식별은 그룹 헤더가 담당, 열 제목은 기법만 (compact 규칙)
# SC 는 4 kRPM = Ref 16 kRPM 의 상사 대응 운전점 (ω ∝ 1/k_r²) — 두 열이
# 진짜 상사쌍이 되어 A/k_r 공통 스케일 일치가 법칙의 직접 검증이 된다.
# 저자 결정 2026-08-24 — 요소를 면으로 칠하려면 메시 연결 정보가 필요하다.
# fieldvec_* 가 그것을 담고 있고 스텝 65(정착 구간)라, 스텝 1(정적 선해석,
# 와전류 미발달)을 쓰던 fields_*_OnLoadTorque 보다 Full-FEA 패널이 옳고
# Fig. 9 와 같은 순간이 된다.  두 export 는 회전자가 정확히 64스텝(-45 deg)
# 어긋나 있었다.
CASES = [
    ("fieldvec_MS_Ref.npz",   "Hybrid", 1.0),
    ("fieldvec_Full_Ref.npz", "Full-FEA", 1.0),
    ("fieldvec_MS_SC.npz",    "Hybrid", 2.0),
    ("fieldvec_Full_SC.npz",  "Full-FEA", 2.0),
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

    # 저자 지시 2026-08-24 — 좌 4 = |B|, 우 4 = A/k_r.  물리량이 열 묶음을,
    # 모델이 행을 잡는다.  패널 내용은 그대로고 컬러바와 Ref/SC 라벨만 이동.
    out = plot_field_panels_split(
        cases, OUT,
        k_r=k_r,                      # A/k_r 공통 스케일
        group_labels=["Ref", "SC"],   # 모델 식별 = 행 라벨
        # 세미나 6: Ref 20 mm / SC 50 mm 로 갈리던 눈금을 한 규칙으로.
        # 저자 결정 2026-08-21 — Ref 50 / SC 100, 곧 k_r 배. 두 모델의 눈금이
        # 종이 위 같은 자리에 오고 x 축의 기존 눈금과도 일치한다.
        tick_step=[50.0, 50.0, 100.0, 100.0],
        # 메시는 |B| 패널에만 겹친다 (저자 결정 2026-08-24).  A/k_r 은
        # 대부분이 0 근처의 옅은 색이라 검은 선이 필드보다 강해진다.
        mesh_lw=0.04,
    )
    print(f"저장: {out}")
    print(f"  크기: {os.path.getsize(out) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
