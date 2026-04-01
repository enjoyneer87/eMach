"""
pyMotorGeo - DXF Motor Geometry Analysis Package
================================================

DXF 파일에서 회전기 기하구조를 자동으로 분석하고,
Motor-CAD Adaptive Geometry 또는 ANSYS Maxwell으로 내보내는 패키지.

주요 기능:
- DXF 엔티티 읽기 및 원점 탐지
- 내전형/외전형 판별, 고정자/회전자 분리
- 극수/슬롯수 추론
- 닫힌 영역(Closed Region) 탐지
- Motor-CAD Region 변환 및 DXF 내보내기

사용 예시:
    from pyMotorGeo import read_entity_list, classify_inner_outer_rotor
    
    entities, doc = read_entity_list("motor.dxf", expand_inserts=True)
    motor_type = classify_inner_outer_rotor(entities)
"""

__version__ = "1.5.1"
__author__ = "EMLab"

# v1.5.1 파이프라인 (권장)
from pipeline import analyze_dxf_v2, export_result_json

# Core data structures
from core import (
    EntityInfo,
    StatorRotorSplit,
    rotate_point,
    mirror_point,
    transform_entity,
    rotate_entity,
    mirror_entity,
    endpoint_key,
    entity_angle,
)

# DXF reading functions
from reader import (
    SKIP_ENTITY_TYPES,
    EXPANDABLE_ENTITY_TYPES,
    transform_point,
    explode_insert,
    read_entity_list,
    manual_parse_dxf_entities,
)

# Motor analysis functions
from analysis import (
    find_origin_candidates,
    find_concentric_radii,
    find_closed_regions,
    analyze_closed_regions_for_motor_type,
    classify_inner_outer_rotor,
    count_poles,
    count_slots,
    # 에어갭 + 분리
    find_airgap_radius,
    find_airgap_by_arc_span,
    split_stator_rotor_by_arc_span,
    split_by_layer,
    split_by_radius,
    split_stator_rotor,
    # 로터 분석 (닫힌 영역 기반)
    count_poles_by_regions,
    estimate_poles_robust,
    # 스테이터 분석 (닫힌 영역 + 컨덕터)
    count_slots_by_regions,
    estimate_slots_robust,
    detect_slot_conductors,
)

# Rotor topology analysis (legacy — still re-exported)
from topology import (
    PoleRegionInfo,
    detect_circular_array_pattern,
    extract_single_pole_entities,
    extract_single_slot_entities,
    classify_pole_topology,
    analyze_rotor_topology,
)
from half_unit import (
    extract_half_pole_entities,
    extract_half_slot_entities,
    reconstruct_from_half,
)

# ── v1.3 신규: 분리된 토폴로지 모듈 ──
from topology_rotor import (
    classify_rotor_entities,
    classify_rotor_entities_with_closing_compare,
    reassign_rotor_region,
    get_rotor_region_summary,
    ROTOR_REGION_NAMES,
    ROTOR_REGION_COLORS,
)
from topology_stator import (
    classify_stator_entities,
    classify_stator_entities_with_closing_compare,
    reassign_stator_region,
    get_stator_region_summary,
    STATOR_REGION_NAMES,
    STATOR_REGION_COLORS,
)

# ── pyleecan 브릿지 ──
from pyleecan_bridge import (
    check_pyleecan_available,
    extract_dimensions_from_dxf,
    create_pyleecan_machine,
    dims_to_summary,
    # v1.6 face 기반 변환
    faces_to_surf_dict,
    face_to_surfline,
    build_rotor_from_faces,
    build_stator_from_faces,
    build_machine_from_faces,
)

# ── v1.5 신규: 닫힌 영역(face) 기반 GUI + face 탐지/자동이름 ──
from gui_region import (
    FaceRegionGUI,
    FaceRegionGUILite,
)
from plotting import HalfUnitPlotter, HalfPoleView, OnePoleView
from region_closing import (
    create_radial_line,
    create_arc_boundary,
    close_rotor_period,
    close_stator_period,
    close_period_model,
    # v1.5.1: 1극/1슬롯 단위 close (권장)
    close_one_pole,
    close_one_slot,
    detect_closed_faces,
    auto_name_faces,
    auto_name_faces_v2,
    get_face_summary,
    plot_faces_static,
    REGION_NAMES as FACE_REGION_NAMES,
    REGION_COLORS as FACE_REGION_COLORS,
)

# ── v1.6: face_detection (BanGeoCode shapely 이식) ──
from face_detection import (
    detect_closed_faces_v2,
    find_interior_point,
    entities_to_polygons,
    check_polygon_feasibility,
)

__all__ = [
    # Version
    "__version__",
    # v1.5.1 pipeline
    "analyze_dxf_v2",
    "export_result_json",
    # v1.6 face_detection (BanGeoCode shapely 이식)
    "detect_closed_faces_v2",
    "find_interior_point",
    "entities_to_polygons",
    "check_polygon_feasibility",
    # Core
    "EntityInfo",
    "StatorRotorSplit",
    "rotate_point",
    "mirror_point",
    "transform_entity",
    "rotate_entity",
    "mirror_entity",
    "endpoint_key",
    "entity_angle",
    # Reader
    "SKIP_ENTITY_TYPES",
    "EXPANDABLE_ENTITY_TYPES",
    "transform_point",
    "explode_insert",
    "read_entity_list",
    "manual_parse_dxf_entities",
    # Analysis
    "find_origin_candidates",
    "find_concentric_radii",
    "find_closed_regions",
    "analyze_closed_regions_for_motor_type",
    "classify_inner_outer_rotor",
    "count_poles",
    "count_slots",
    "find_airgap_radius",
    "find_airgap_by_arc_span",
    "split_stator_rotor_by_arc_span",
    "split_by_layer",
    "split_by_radius",
    "split_stator_rotor",
    "count_poles_by_regions",
    "estimate_poles_robust",
    "count_slots_by_regions",
    "estimate_slots_robust",
    "detect_slot_conductors",
    # Topology (legacy)
    "PoleRegionInfo",
    "detect_circular_array_pattern",
    "extract_single_pole_entities",
    "extract_single_slot_entities",
    "extract_half_pole_entities",
    "extract_half_slot_entities",
    "reconstruct_from_half",
    "classify_pole_topology",
    "analyze_rotor_topology",
    # v1.3: 분리 토폴로지
    "classify_rotor_entities",
    "classify_rotor_entities_with_closing_compare",
    "reassign_rotor_region",
    "get_rotor_region_summary",
    "ROTOR_REGION_NAMES",
    "ROTOR_REGION_COLORS",
    "classify_stator_entities",
    "classify_stator_entities_with_closing_compare",
    "reassign_stator_region",
    "get_stator_region_summary",
    "STATOR_REGION_NAMES",
    "STATOR_REGION_COLORS",
    # pyleecan bridge
    "check_pyleecan_available",
    "extract_dimensions_from_dxf",
    "create_pyleecan_machine",
    "dims_to_summary",
    # v1.6 face 기반 변환
    "faces_to_surf_dict",
    "face_to_surfline",
    "build_rotor_from_faces",
    "build_stator_from_faces",
    "build_machine_from_faces",
    # v1.5: face-based region GUI + face detection
    "FaceRegionGUI",
    "FaceRegionGUILite",
    "detect_closed_faces",
    "auto_name_faces",
    "auto_name_faces_v2",
    "get_face_summary",
    "plot_faces_static",
    "FACE_REGION_NAMES",
    "FACE_REGION_COLORS",
    "create_radial_line",
    "create_arc_boundary",
    "close_rotor_period",
    "close_stator_period",
    "close_period_model",
    # v1.5.1: 1극/1슬롯 단위 close
    "close_one_pole",
    "close_one_slot",
    "HalfUnitPlotter",
    "HalfPoleView",
    "OnePoleView",
]
