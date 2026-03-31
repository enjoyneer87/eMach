"""
pyMotorGeo.analysis
===================
모터 DXF 분석 함수 — 리-익스포트 허브.

실제 구현은 아래 서브모듈에 있습니다:
  - analysis_airgap   : 공극 탐지, 동심원, 원점, 내/외전형, 분리
  - analysis_rotor    : 극수 추정 (ARC 분포 / 닫힌 영역 / FFT)
  - analysis_stator   : 슬롯수 추정, 컨덕터 탐지

기존 ``from pyMotorGeo.analysis import ...`` 호환성을 유지합니다.
"""

# ?? analysis_airgap ??
from analysis_airgap import (          # noqa: F401
    find_origin_candidates,
    find_concentric_radii,
    _group_radii,
    find_closed_regions,
    analyze_closed_regions_for_motor_type,
    classify_inner_outer_rotor,
    find_airgap_radius,
    find_airgap_by_arc_span,
    split_by_layer,
    split_by_radius,
    split_stator_rotor,
    split_stator_rotor_by_arc_span,
)

# ?? analysis_rotor ??
from analysis_rotor import (           # noqa: F401
    count_poles,
    count_poles_by_regions,
    estimate_poles_robust,
)

# ?? analysis_stator ??
from analysis_stator import (          # noqa: F401
    count_slots,
    count_slots_by_regions,
    estimate_slots_robust,
    detect_slot_conductors,
)

