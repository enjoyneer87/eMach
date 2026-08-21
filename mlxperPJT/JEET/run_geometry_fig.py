# -*- coding: utf-8 -*-
"""Fig 9 (motor cross-section, fig:motor_geometry) 생성기.

DXF 원본 경로를 여기에 고정해 둔다 --- 이 경로가 코드 밖에만 있으면
그림을 재생성할 수 없게 된다(실제로 한 번 유실된 적 있음).

측정 치수는 JSON 으로 Drive 에 보존하며, tab:Radial 의 값과 대조하는
근거가 된다.

  python run_geometry_fig.py [--dxf <path>] [--out <pdf>]
"""
import argparse
import json
import os
import sys

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools')))
from jeet_acloss_rbf.repro_env import fig_dir, results_dir
_FIGDIR = fig_dir()

HERE = os.path.dirname(os.path.abspath(__file__))
# 데이터 루트는 JEET_DATA_ROOT 로 덮어쓸 수 있다 (배포 레포/CI 용).
_DATA = os.environ.get('JEET_DATA_ROOT',
                       os.path.join(HERE, 'map_exports', 'e10'))

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "tools")))  # 이 체크아웃의 tools

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.manuscript_figs import plot_motor_geometry_dxf

# e10 Ref 모델(6턴) 2-D 단면. Motor-CAD .mot 에서 export 된 것으로,
# 원본 모델은 저자 아카이브의 Motor-CAD .mot (e10Turn6V261SLFEA) 이다.
# 배포 레포에선 데이터 루트(또는 그 부모 data/)에 두면 --dxf 없이 찾는다.
DXF_NAME = 'e10_2d.dxf'
DXF = next((p for p in (os.path.join(_DATA, DXF_NAME),
                        os.path.join(os.path.dirname(os.path.abspath(_DATA)),
                                     DXF_NAME))
            if os.path.exists(p)), os.path.join(_DATA, DXF_NAME))
OUT_PDF = os.path.join(_FIGDIR, 'motor_geometry_e10.pdf')
DRIVE_OUT = os.path.join(results_dir(), 'geometry_dims_e10.json')


def _mounted(path: str) -> bool:
    """드라이브가 안 붙어 있으면(배포 레포/CI) JSON 쓰기를 건너뛴다."""
    drv = os.path.splitdrive(os.path.abspath(path))[0]
    return not drv or os.path.isdir(drv + os.sep)


# tab:Radial 에 실린 값 (대조용)
TABLE = {"Ds_mm": 198.0, "Dr_mm": 141.5, "g_mm": 0.5,
         "w_mm": 1.7, "h_mm": 3.7}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", default=DXF)
    ap.add_argument("--out", default=OUT_PDF)
    ap.add_argument("--json", default=DRIVE_OUT)
    a = ap.parse_args()

    if not os.path.exists(a.dxf):
        sys.exit(f"DXF 없음: {a.dxf}\n"
                 f"  .mot 에서 DXF export 로 재생성할 수 있다.")

    dims = plot_motor_geometry_dxf(a.dxf, a.out)
    print("Fig9:", a.out)

    print(f"\n{'량':>8}{'DXF 실측':>12}{'표(tab:Radial)':>16}{'차이':>10}")
    for k, v in dims.items():
        if k in TABLE:
            d = v - TABLE[k]
            flag = "" if abs(d) < 0.05 else "   <-- 확인"
            print(f"{k:>8}{v:>12.3f}{TABLE[k]:>16.1f}{d:>10.3f}{flag}")
        else:
            print(f"{k:>8}{v:>12.3f}{'-':>16}{'-':>10}")

    rec = {"dxf": a.dxf, "measured_mm": dims, "table_mm": TABLE,
           "symbols": {"w_mm": "w_c (conductor radial thickness)",
                       "h_mm": "h_c (conductor tangential width)",
                       "g_mm": "l_g (airgap length)"}}
    if not a.json or not _mounted(a.json):
        print("\nJSON 생략 (경로 미마운트):", a.json or "-")
        return
    os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("\nJSON 저장:", a.json)


if __name__ == "__main__":
    main()
