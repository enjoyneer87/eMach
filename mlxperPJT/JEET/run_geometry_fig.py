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

sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.manuscript_figs import plot_motor_geometry_dxf

# e10 Ref 모델(6턴) 2-D 단면. Motor-CAD .mot 에서 export 된 것으로,
# D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot 이 원본 모델이다.
DXF = r"D:\KangDH\Thesis\e10\e10_2d.dxf"
OUT_PDF = r"E:\KDH\Overleaf\JEET-2024_rev1\fig\motor_geometry_e10.pdf"
DRIVE_OUT = (r"J:\내 드라이브\EveryMotor_JEET_data\results"
             r"\geometry_dims_e10.json")

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
    os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("\nJSON 저장:", a.json)


if __name__ == "__main__":
    main()
