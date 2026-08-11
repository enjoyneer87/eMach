# -*- coding: utf-8 -*-
"""em2struct — 전자계 가진력 ↔ 구조해석 메시투메시 맵핑 (eMach).

Motor-CAD(Maxwell) 전자계 가진력을 ANSYS Mechanical / Ansys Motion / LS-DYNA
구조 메시로 보존적으로 전달한다. NVH(진동·소음) 커플링용.

빠른 시작
---------
    from em2struct import (read_airgap_mst, TargetMesh, EMStructMapper)

    src = read_airgap_mst(theta, sigma_r, sigma_t, radius=0.071,
                          stack_length=0.150, times=t)
    tgt = TargetMesh(nodes=struct_nodes, node_ids=ids)
    out = (EMStructMapper()
              .load_source(src)
              .set_target(tgt)
              .extrude(z_stations=np.linspace(0, 0.150, 20))  # 2D→3D
              .map("lsq", k=6)          # 합력+모멘트 보존
              .report()
              .export("emforce.inp", solver="ansys_mechanical"))

구성
----
core     : ForceField, TargetMesh, MappingResult, 보존 진단.
readers  : read_maxwell_nodal, read_airgap_mst, read_motorcad_nvh.
mappers  : Nearest / InverseDistance / LeastSquares(권장) / RBF.
writers  : write_ansys_mechanical, write_lsdyna, write_ansys_motion.
axial    : extrude_field (2D 단면 → 3D 축방향 분배, 사구 지원).
pipeline : EMStructMapper(체이닝), map_forces(원샷).
viz      : plot_mapping (QA).
"""
from __future__ import annotations

from .core import (
    ConservationReport,
    ForceField,
    MappingResult,
    Quantity,
    SegmentTarget,
    TargetMesh,
    conservation_report,
    make_segment_target,
)
from .readers import (read_airgap_mst, read_maxwell_nodal, read_motorcad_nvh,
                      read_motorcad_multiforce, read_vwp_force)
from .mappers import (
    BaseMapper,
    InverseDistanceMapper,
    LeastSquaresMapper,
    NearestMapper,
    RBFMapper,
    make_mapper,
)
from .writers import (write_ansys_mechanical, write_ansys_motion, write_lsdyna,
                      write_lsdyna_segment, write_ansys_remote_force)
from .axial import extrude_field
from .pipeline import EMStructMapper, map_forces

__all__ = [
    "Quantity", "ForceField", "TargetMesh", "MappingResult",
    "SegmentTarget", "make_segment_target",
    "ConservationReport", "conservation_report",
    "read_maxwell_nodal", "read_airgap_mst", "read_motorcad_nvh",
    "read_motorcad_multiforce", "read_vwp_force",
    "BaseMapper", "NearestMapper", "InverseDistanceMapper",
    "LeastSquaresMapper", "RBFMapper", "make_mapper",
    "write_ansys_mechanical", "write_lsdyna", "write_lsdyna_segment",
    "write_ansys_motion", "write_ansys_remote_force",
    "extrude_field", "EMStructMapper", "map_forces",
]

__version__ = "0.1.0"
