# -*- coding: utf-8 -*-
"""e10 로터측 전자계 가진력 → 로터 메시 원격힘(Remote Force).

Motor-CAD rotorExcitation(8극, forceX/Y) → e10 MAPDL **로터 OD 절점**에:
  (주) 극별 **원격힘**(pilot + RBE3) MAPDL export — 8극을 표면섹터에 분산결합.
  (QA) 분산 LSQ 맵핑으로 8극 힘장·보존 시각화.

선행: extract_e10_bore_nodes.py (rotorOD_ids/xyz 포함 npz).
"""
from __future__ import annotations

import os, sys
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..", "tools")))

from em2struct import (EMStructMapper, read_motorcad_multiforce,
                       write_ansys_remote_force)
from em2struct.target_io import target_from_arrays
from em2struct.viz import plot_mapping

DATA = os.path.join(_HERE, "data")
NODES_NPZ = os.path.join(DATA, "e10_target_nodes.npz")
MF_JSON = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\data\e10_multiforce.json"
Z_ST0, Z_ST1 = -0.2075, -0.0575
LOAD_POINT = int(os.environ.get("MF_LOADPOINT", "0"))


def main():
    nz = np.load(NODES_NPZ)
    if "rotorOD_ids" not in nz:
        raise SystemExit("rotorOD 절점 없음 — extract_e10_bore_nodes.py 재실행 필요.")
    rod_xyz, rod_ids = nz["rotorOD_xyz"], nz["rotorOD_ids"]
    print(f"[target] 로터 OD 절점 {len(rod_ids)}개 "
          f"(r≈{np.hypot(rod_xyz[:,0],rod_xyz[:,1]).mean():.4f} m, "
          f"z=[{rod_xyz[:,2].min():.3f},{rod_xyz[:,2].max():.3f}])")
    tgt = target_from_arrays(rod_xyz, rod_ids)

    src = read_motorcad_multiforce(MF_JSON, load_point=LOAD_POINT, part="rotor")
    print(f"[source] 로터 {src.n}극 × {src.ncols}스텝, "
          f"{src.meta.get('speed_rpm')}rpm, 극당|F|max≈"
          f"{np.linalg.norm(src.values,axis=1).max():.0f}N")

    # (주) 원격힘 export — 8극 → 표면 각도섹터에 RBE3 결합
    rf = write_ansys_remote_force(
        src, tgt, os.path.join(DATA, "e10_rotor_remote_force.inp"),
        scope="nearest", coupling="rbe3")
    print("[remote force] MAPDL export →", rf)

    # (QA) 분산 LSQ 맵핑(축방향 분배 후)로 8극 힘장·보존 시각화
    z_stations = np.linspace(Z_ST0, Z_ST1, 20)
    pipe = (EMStructMapper(verbose=False)
            .load_source(src).set_target(tgt)
            .extrude(z_stations=z_stations)
            .map("lsq", k=6).report())
    fig = plot_mapping(pipe.source, pipe.result,
                       os.path.join(DATA, "e10_rotor_qa.png"),
                       col=0, plane="xy",
                       title="e10 rotor excitation (8-pole) → rotor OD nodes")
    print("[QA]", fig)
    print("ROTOR-OK")


if __name__ == "__main__":
    main()
