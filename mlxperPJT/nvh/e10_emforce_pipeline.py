# -*- coding: utf-8 -*-
"""e10 전자계 가진력 → MAPDL 스테이터 보어 절점 하중 (em2struct 실적용).

작업3: extract_e10_bore_nodes.py 가 뽑은 **실제 MAPDL 절점**을 타깃으로, 에어갭
가진력을 LSQ 로 맵핑하고 MAPDL/LS-DYNA/Motion/segment 로 export + QA.

소스 힘:
  - 실 Motor-CAD 멀티포스(e10_multiforce.csv/.txt) 있으면 그걸 사용(read_motorcad_nvh),
  - 없으면 e10 파라미터 기반 에어갭 Maxwell 응력(현실적 대체)으로 진행.
"""
from __future__ import annotations

import os, sys, glob
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..", "tools")))

from em2struct import (EMStructMapper, read_airgap_mst, read_motorcad_nvh,
                       read_motorcad_multiforce, make_segment_target, write_lsdyna_segment)
from em2struct.target_io import target_from_arrays
from em2struct.viz import plot_mapping

DATA = os.path.join(_HERE, "data")
NODES_NPZ = os.path.join(DATA, "e10_target_nodes.npz")
FFDATA = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data"
# 실 Motor-CAD 멀티포스 export(네이티브 JSON 우선, 구형 CSV/TXT 폴백)
MF_JSON = os.path.join(FFDATA, "e10_multiforce.json")
MF_CSV = [os.path.join(FFDATA, "e10_multiforce.csv"),
          os.path.join(FFDATA, "e10_multiforce.txt")]
LOAD_POINT = int(os.environ.get("MF_LOADPOINT", "0"))

# e10 파라미터
R_AG = 0.0713
Z_ST0, Z_ST1 = -0.2075, -0.0575
STACK = Z_ST1 - Z_ST0
POLES, SLOTS = 8, 48
F_ELEC = 16000 / 60 * (POLES / 2)


def build_source(times):
    """실 Motor-CAD 멀티포스 있으면 로드, 없으면 에어갭 MST 현실값."""
    # (우선) 네이티브 JSON — 실제 e10 export 포맷
    if os.path.exists(MF_JSON) and os.path.getsize(MF_JSON) > 0:
        print(f"[source] 실 Motor-CAD 멀티포스 JSON 사용: {MF_JSON} (loadPoint={LOAD_POINT})")
        try:
            src = read_motorcad_multiforce(MF_JSON, load_point=LOAD_POINT, part="stator")
            print(f"  {src.n}치 × {src.ncols}스텝, "
                  f"{src.meta.get('speed_rpm')}rpm/{src.meta.get('poles')}극, "
                  f"f_elec={src.meta.get('f_elec_Hz'):.1f}Hz")
            return src, "motorcad_multiforce_json"
        except Exception as e:
            print(f"  [warn] JSON 파싱 실패({repr(e)[:100]}) → CSV/에어갭 대체")
    for mf in MF_CSV:
        if os.path.exists(mf) and os.path.getsize(mf) > 0:
            print(f"[source] Motor-CAD 멀티포스 CSV 사용: {mf}")
            try:
                return read_motorcad_nvh(mf, representation="polar"), "motorcad_nvh_csv"
            except Exception as e:
                print(f"  [warn] CSV 파싱 실패({repr(e)[:80]}) → 에어갭 MST 대체")
            break
    print("[source] 실 파일 없음 → e10 파라미터 에어갭 Maxwell 응력(대체)")
    n_theta = 360
    theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    TH, TT = np.meshgrid(theta, times, indexing="ij")
    sigma_r = (120e3 * np.cos(POLES * TH - 2 * np.pi * F_ELEC * TT)
               + 40e3 * np.cos(SLOTS * TH - 2 * np.pi * F_ELEC * TT))
    sigma_t = 25e3 * np.sin(POLES * TH - 2 * np.pi * F_ELEC * TT)
    # 스택 중심 z 로 배치(2D 단면) → extrude 로 축분배
    src = read_airgap_mst(theta, sigma_r, sigma_t, radius=R_AG,
                          stack_length=STACK, times=times,
                          axial_z=0.5 * (Z_ST0 + Z_ST1))
    return src, "airgap_mst"


def main():
    if not os.path.exists(NODES_NPZ):
        raise SystemExit(f"타깃 절점 없음: {NODES_NPZ}\n"
                         "먼저 extract_e10_bore_nodes.py 를 실행하세요.")
    nz = np.load(NODES_NPZ)
    bore_xyz, bore_ids = nz["bore_xyz"], nz["bore_ids"]
    print(f"[target] 스테이터 보어 절점 {len(bore_ids)}개 "
          f"(r≈{np.hypot(bore_xyz[:,0],bore_xyz[:,1]).mean():.4f} m, "
          f"z=[{bore_xyz[:,2].min():.3f},{bore_xyz[:,2].max():.3f}])")
    tgt = target_from_arrays(bore_xyz, bore_ids)

    times = np.linspace(0, 1.0 / F_ELEC, 24, endpoint=False)
    src, src_tag = build_source(times)

    # 축방향 스테이션 = 타깃 절점의 실제 z 분포에 맞춤
    z_stations = np.linspace(Z_ST0, Z_ST1, 20)
    pipe = (EMStructMapper()
            .load_source(src)
            .set_target(tgt))
    # 2D 소스(단일 축슬라이스)면 스택 길이에 걸쳐 축방향 분배
    if src.dim == 2 or np.allclose(src.points[:, 2], src.points[0, 2]):
        pipe.extrude(z_stations=z_stations)   # 2D 단면 → 3D
    pipe.map("lsq", k=6).report()

    # export 3종 + QA
    outs = {}
    outs["mapdl"] = pipe.export(os.path.join(DATA, "e10_emforce_mapdl.inp"),
                                solver="ansys_mechanical")
    outs["mapdl_ext"] = pipe.export(os.path.join(DATA, "e10_emforce_external.csv"),
                                    solver="ansys_mechanical", mode="external")
    outs["lsdyna"] = pipe.export(os.path.join(DATA, "e10_emforce_lsdyna.k"),
                                 solver="lsdyna")
    outs["motion"] = pipe.export(os.path.join(DATA, "e10_emforce_motion.csv"),
                                 solver="ansys_motion")
    fig = plot_mapping(pipe.source, pipe.result,
                       os.path.join(DATA, "e10_emforce_qa.png"),
                       col=0, plane="xy",
                       title=f"e10 EM force → MAPDL stator bore nodes (LSQ, src={src_tag})")
    print("exports:", {k: (v if isinstance(v, str) else v) for k, v in outs.items()})
    print("QA:", fig)
    print("PIPELINE-OK")


if __name__ == "__main__":
    main()
