"""
pyMotorGeo.pyleecan_bridge
===========================

Bridge module for exporting motor geometry to Pyleecan simulation framework.

This module converts motor topology information extracted from CAD (DXF) geometry 
into Pyleecan machine objects (MachineSIPMSM, MachineIPMSM, MachineSyRM, etc.). 
Enables seamless integration with the Pyleecan multiphysics simulation platform 
for electromagnetics, thermal, and mechanical analysis.

**Workflow**:

1. Extract geometry information from CAD using pyMotorGeo analysis modules
2. Use this bridge to convert geometry ↔ Pyleecan objects
3. Run Pyleecan simulations (FEA, loss calculation, performance prediction)
4. Export results back to CAD or reports

**Key Conversions**:

- Slot geometry → Pyleecan slot types (SlotW11, SlotW22, SlotM10, SlotM11, HoleM50)
- Magnet layout → Pyleecan Lamination with holes and magnets
- Winding topology (if applicable) → Pyleecan Winding objects
- Complete motor structure → Pyleecan Machine objects (SIPMMS, IPMSM, SyRM)

**Supported Motor Types**:

- **SIPMM** (Surface IPM) / **SPMSM**: Surface-mounted permanent magnets on rotor
- **IPMSM**: Interior permanent magnets embedded in rotor core with air barriers
- **SyRM**: Synchronous reluctance motor (flux barriers, no permanent magnets)
- **Wound Motors**: Stator with coil windings (optional, time-permitting implementation)

**Dependencies**:

- pyleecan: Optional; if unavailable, bridge functions return empty or error messages
  Install: `pip install pyleecan`
- numpy, math: Numerical utilities
- pyMotorGeo core modules (core, topology_rotor, topology_stator, region_closing)

**Limitations & Future Work**:

- Currently focused on rotor/stator lamination geometry
- Winding definition (coil winding, slot connections) is partial/not implemented
- Bearing, shaft details extracted but with minimal validation
- Thermal/mechanical parameters set to defaults; not extracted from CAD
"""

import math
import numpy as np
from typing import Dict, Optional, Tuple

# pyleecan은 선택적 import
_HAS_PYLEECAN = False
try:
    from pyleecan.Classes.MachineSIPMSM import MachineSIPMSM
    from pyleecan.Classes.MachineIPMSM import MachineIPMSM
    from pyleecan.Classes.MachineSyRM import MachineSyRM
    from pyleecan.Classes.LamSlotWind import LamSlotWind
    from pyleecan.Classes.LamSlotMag import LamSlotMag
    from pyleecan.Classes.LamHole import LamHole
    from pyleecan.Classes.SlotW11 import SlotW11
    from pyleecan.Classes.SlotW22 import SlotW22
    from pyleecan.Classes.SlotM11 import SlotM11
    from pyleecan.Classes.SlotM10 import SlotM10
    from pyleecan.Classes.HoleM50 import HoleM50
    from pyleecan.Classes.Magnet import Magnet
    from pyleecan.Classes.Winding import Winding
    from pyleecan.Classes.Shaft import Shaft
    _HAS_PYLEECAN = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════
# 기하 파라미터 추출 (DXF 분석 결과 → 치수)
# ═══════════════════════════════════════════════════════════════

def extract_dimensions_from_dxf(
    split_result: Dict,
    n_poles: int,
    n_slots: int,
    rotor_topo: Dict = None,
    stator_topo: Dict = None,
    origin: Tuple[float, float] = (0.0, 0.0),
    stack_length_mm: float = 100.0,
) -> Dict:
    """
    DXF 분석 결과로부터 pyleecan에 필요한 기하 치수를 추출합니다.

    Parameters
    ----------
    split_result : split_stator_rotor_by_arc_span() 결과
    n_poles, n_slots : 극수, 슬롯수
    rotor_topo : classify_rotor_entities() 결과
    stator_topo : classify_stator_entities() 결과
    origin : 원점
    stack_length_mm : 적층 길이 [mm]

    Returns
    -------
    Dict : 치수 정보 (mm 단위)
        rotor_Rint, rotor_Rext, stator_Rint, stator_Rext,
        airgap, pole_pitch_deg, slot_pitch_deg,
        magnet_thickness, magnet_arc_deg, ...
    """
    ox, oy = origin
    airgap_r_inner = split_result['airgap_r_inner']
    airgap_r_outer = split_result['airgap_r_outer']
    stator_ents = split_result['stator']
    rotor_ents = split_result['rotor']

    # 스테이터/로터 반경 범위
    stator_radii = []
    for ei in stator_ents:
        stator_radii.extend([np.hypot(p[0] - ox, p[1] - oy) for p in ei.points])
    rotor_radii = []
    for ei in rotor_ents:
        rotor_radii.extend([np.hypot(p[0] - ox, p[1] - oy) for p in ei.points])

    stator_Rext = max(stator_radii) if stator_radii else airgap_r_outer + 30
    stator_Rint = airgap_r_outer  # inner rotor → 에어갭 외측 = 스테이터 내경
    rotor_Rext = airgap_r_inner   # inner rotor → 에어갭 내측 = 로터 외경
    rotor_Rint = min(rotor_radii) if rotor_radii else rotor_Rext * 0.3

    airgap = airgap_r_outer - airgap_r_inner
    pole_pitch_deg = 360.0 / n_poles
    slot_pitch_deg = 360.0 / n_slots

    # 자석 치수 추정 (로터 토폴로지에서)
    magnet_thickness = 0.0
    magnet_arc_deg = 0.0
    if rotor_topo and rotor_topo.get('magnets'):
        mag_radii_all = []
        mag_angles_all = []
        for item in rotor_topo['magnets']:
            ei = item['entity']
            rs = [np.hypot(p[0] - ox, p[1] - oy) for p in ei.points]
            mag_radii_all.extend(rs)
            angs = [np.degrees(np.arctan2(p[1] - oy, p[0] - ox)) % 360
                    for p in ei.points]
            mag_angles_all.extend(angs)
        if mag_radii_all:
            magnet_thickness = max(mag_radii_all) - min(mag_radii_all)
        if mag_angles_all:
            # 한 극 내 자석의 각도 범위
            magnet_arc_deg = max(mag_angles_all) - min(mag_angles_all)
            if magnet_arc_deg > pole_pitch_deg:
                magnet_arc_deg = pole_pitch_deg * 0.8  # 보정

    dims = {
        'rotor_Rint_mm': rotor_Rint,
        'rotor_Rext_mm': rotor_Rext,
        'stator_Rint_mm': stator_Rint,
        'stator_Rext_mm': stator_Rext,
        'airgap_mm': airgap,
        'n_poles': n_poles,
        'n_slots': n_slots,
        'p': n_poles // 2,
        'pole_pitch_deg': pole_pitch_deg,
        'slot_pitch_deg': slot_pitch_deg,
        'magnet_thickness_mm': magnet_thickness,
        'magnet_arc_deg': magnet_arc_deg,
        'stack_length_mm': stack_length_mm,
        'topology': rotor_topo.get('topology', 'UNKNOWN') if rotor_topo else 'UNKNOWN',
    }
    return dims


# ═══════════════════════════════════════════════════════════════
# pyleecan Machine 생성
# ═══════════════════════════════════════════════════════════════

def create_pyleecan_machine(
    dims: Dict,
    machine_name: str = "DXF_Motor",
) -> object:
    """
    추출 치수로부터 pyleecan Machine 객체를 생성합니다.

    Parameters
    ----------
    dims : extract_dimensions_from_dxf() 결과
    machine_name : 모터 이름

    Returns
    -------
    pyleecan Machine 인스턴스 (MachineSIPMSM, MachineIPMSM, MachineSyRM 중 하나)
    None if pyleecan not installed
    """
    if not _HAS_PYLEECAN:
        print("[pyleecan_bridge] pyleecan이 설치되어 있지 않습니다.")
        print("  → pip install pyleecan")
        return None

    mm = 1e-3  # mm → m 변환
    topology = dims.get('topology', 'UNKNOWN')
    n_poles = dims['n_poles']
    n_slots = dims['n_slots']
    p = dims['p']

    # ── 스테이터 (공통) ──
    stator = LamSlotWind(
        Rint=dims['stator_Rint_mm'] * mm,
        Rext=dims['stator_Rext_mm'] * mm,
        L1=dims['stack_length_mm'] * mm,
        Kf1=0.95,
        is_internal=False,
        is_stator=True,
        slot=SlotW22(
            W0=math.radians(dims['slot_pitch_deg'] * 0.3),  # 슬롯 오프닝 각도
            H0=1.0 * mm,    # 슬롯 오프닝 깊이
            H2=10.0 * mm,   # 슬롯 깊이 (기본)
            W2=math.radians(dims['slot_pitch_deg'] * 0.5),  # 슬롯 폭 각도
            Zs=n_slots,
        ),
        winding=Winding(
            Nlayer=2,
            Ntcoil=1,
            coil_pitch=1,
            p=p,
        ),
    )

    # ── 로터 (토폴로지별) ──
    shaft_r = dims['rotor_Rint_mm']

    if topology == 'SPM':
        mag_thickness = dims.get('magnet_thickness_mm', 3.0)
        mag_arc = dims.get('magnet_arc_deg', dims['pole_pitch_deg'] * 0.8)

        rotor = LamSlotMag(
            Rint=shaft_r * mm,
            Rext=dims['rotor_Rext_mm'] * mm,
            L1=dims['stack_length_mm'] * mm,
            Kf1=0.95,
            is_internal=True,
            is_stator=False,
            slot=SlotM11(
                W0=math.radians(mag_arc),
                H0=0,
                W1=math.radians(mag_arc),
                H1=mag_thickness * mm,
                Zs=n_poles,
            ),
            magnet=Magnet(
                Lmag=dims['stack_length_mm'] * mm,
                type_magnetization=0,  # 0=radial
            ),
        )
        machine = MachineSIPMSM(
            name=machine_name,
            rotor=rotor,
            stator=stator,
            shaft=Shaft(Drsh=shaft_r * 2 * mm),
        )

    elif topology in ('IPM', 'PMa-SynRM'):
        rotor = LamHole(
            Rint=shaft_r * mm,
            Rext=dims['rotor_Rext_mm'] * mm,
            L1=dims['stack_length_mm'] * mm,
            Kf1=0.95,
            is_internal=True,
            is_stator=False,
            hole=[
                HoleM50(
                    W0=math.radians(dims['pole_pitch_deg'] * 0.6),
                    H0=0,
                    H1=3.0 * mm,
                    W1=10.0 * mm,
                    W2=0,
                    W3=5.0 * mm,
                    W4=10.0 * mm,
                    H2=2.0 * mm,
                    H3=5.0 * mm,
                    Zh=n_poles,
                ),
            ],
        )
        machine = MachineIPMSM(
            name=machine_name,
            rotor=rotor,
            stator=stator,
            shaft=Shaft(Drsh=shaft_r * 2 * mm),
        )

    elif topology == 'SynRM':
        rotor = LamHole(
            Rint=shaft_r * mm,
            Rext=dims['rotor_Rext_mm'] * mm,
            L1=dims['stack_length_mm'] * mm,
            Kf1=0.95,
            is_internal=True,
            is_stator=False,
            hole=[],
        )
        machine = MachineSyRM(
            name=machine_name,
            rotor=rotor,
            stator=stator,
            shaft=Shaft(Drsh=shaft_r * 2 * mm),
        )

    else:
        # UNKNOWN → SPM fallback
        rotor = LamSlotMag(
            Rint=shaft_r * mm,
            Rext=dims['rotor_Rext_mm'] * mm,
            L1=dims['stack_length_mm'] * mm,
            Kf1=0.95,
            is_internal=True,
            is_stator=False,
            slot=SlotM11(
                W0=math.radians(dims['pole_pitch_deg'] * 0.8),
                H0=0,
                W1=math.radians(dims['pole_pitch_deg'] * 0.8),
                H1=3.0 * mm,
                Zs=n_poles,
            ),
            magnet=Magnet(
                Lmag=dims['stack_length_mm'] * mm,
                type_magnetization=0,
            ),
        )
        machine = MachineSIPMSM(
            name=machine_name,
            rotor=rotor,
            stator=stator,
            shaft=Shaft(Drsh=shaft_r * 2 * mm),
        )

    return machine


def dims_to_summary(dims: Dict) -> str:
    """치수 딕셔너리를 사람이 읽기 좋은 요약으로 변환."""
    lines = [
        f"Motor Dimensions (from DXF)",
        f"{'='*40}",
        f"  Topology    : {dims.get('topology', 'UNKNOWN')}",
        f"  Poles       : {dims['n_poles']}",
        f"  Slots       : {dims['n_slots']}",
        f"  p (pairs)   : {dims['p']}",
        f"  Rotor  Rint : {dims['rotor_Rint_mm']:.2f} mm",
        f"  Rotor  Rext : {dims['rotor_Rext_mm']:.2f} mm",
        f"  Stator Rint : {dims['stator_Rint_mm']:.2f} mm",
        f"  Stator Rext : {dims['stator_Rext_mm']:.2f} mm",
        f"  Airgap      : {dims['airgap_mm']:.3f} mm",
        f"  Pole pitch  : {dims['pole_pitch_deg']:.2f}°",
        f"  Slot pitch  : {dims['slot_pitch_deg']:.2f}°",
    ]
    if dims.get('magnet_thickness_mm', 0) > 0:
        lines.append(f"  Mag thick.  : {dims['magnet_thickness_mm']:.2f} mm")
        lines.append(f"  Mag arc     : {dims['magnet_arc_deg']:.2f}°")
    return '\n'.join(lines)


def check_pyleecan_available() -> bool:
    """pyleecan이 설치되어 있는지 확인."""
    return _HAS_PYLEECAN


# ═══════════════════════════════════════════════════════════════
# Face 기반 변환 (SurfLine / SlotUD / HoleUD)
# ═══════════════════════════════════════════════════════════════

def faces_to_surf_dict(faces: list) -> dict:
    """
    face 리스트 → pyleecan DXFImport.surf_dict 호환 딕셔너리.

    형식: { complex(interior_x, interior_y): label_string }
    interior_point은 find_best_region(BanGeoCode) 결과.
    """
    from region_closing import REGION_NAMES
    result = {}
    for f in faces:
        ix, iy = f.get('interior_point', f['centroid'])
        label = REGION_NAMES.get(f.get('name', 'unknown'), f.get('name', 'Unknown'))
        result[complex(ix * 1e-3, iy * 1e-3)] = label   # mm → m
    return result


def face_to_surfline(face: dict, label: str = None):
    """
    face dict → pyleecan SurfLine.

    SurfLine.line_list : vertices → Segment 리스트 (mm→m 변환)
    SurfLine.point_ref : complex(interior_x, interior_y) in m
    SurfLine.label     : 영역 이름
    """
    if not _HAS_PYLEECAN:
        return None
    try:
        from pyleecan.Classes.SurfLine import SurfLine
        from pyleecan.Classes.Segment import Segment
    except ImportError:
        return None

    verts = face.get('vertices', [])
    if len(verts) < 3:
        return None

    ix, iy = face.get('interior_point', face['centroid'])
    lbl = label or face.get('name', 'unknown')
    mm = 1e-3

    coords = verts[:-1] if (verts[0] == verts[-1]) else verts
    n = len(coords)
    line_list = [
        Segment(begin=complex(coords[i][0] * mm, coords[i][1] * mm),
                end=complex(coords[(i + 1) % n][0] * mm,
                            coords[(i + 1) % n][1] * mm))
        for i in range(n)
    ]
    return SurfLine(
        line_list=line_list,
        point_ref=complex(ix * mm, iy * mm),
        label=lbl,
    )


def build_rotor_from_faces(
    rotor_faces: list,
    r_shaft_mm: float,
    r_rotor_outer_mm: float,
    n_poles: int,
    stack_length_mm: float = 100.0,
):
    """
    1극 face 리스트 → pyleecan LamHole (HoleUD 방식).

    magnet  face → HoleUD SurfLine (label='Magnet')
    air_barrier → HoleUD SurfLine (label='Air')
    """
    if not _HAS_PYLEECAN:
        return None
    try:
        from pyleecan.Classes.LamHole import LamHole
        from pyleecan.Classes.HoleUD import HoleUD
    except ImportError:
        return None

    mm = 1e-3
    surf_list = []
    for f in rotor_faces:
        name = f.get('name', '')
        if name == 'magnet':
            sl = face_to_surfline(f, label='Magnet')
        elif name == 'air_barrier':
            sl = face_to_surfline(f, label='Air')
        else:
            continue
        if sl:
            surf_list.append(sl)

    holes = [HoleUD(surf_list=surf_list, Zh=n_poles)] if surf_list else []
    return LamHole(
        Rint=r_shaft_mm * mm,
        Rext=r_rotor_outer_mm * mm,
        L1=stack_length_mm * mm,
        Kf1=0.95,
        is_internal=True,
        is_stator=False,
        hole=holes,
    )


def build_stator_from_faces(
    stator_faces: list,
    r_stator_inner_mm: float,
    r_stator_outer_mm: float,
    n_slots: int,
    stack_length_mm: float = 100.0,
):
    """
    1슬롯 face 리스트 → pyleecan LamSlotWind (SlotUD 방식).

    slot / slot_opening face → SlotUD line_list
    """
    if not _HAS_PYLEECAN:
        return None
    try:
        from pyleecan.Classes.LamSlotWind import LamSlotWind
        from pyleecan.Classes.SlotUD import SlotUD
        from pyleecan.Classes.Winding import Winding
        from pyleecan.Classes.Segment import Segment
    except ImportError:
        return None

    mm = 1e-3
    line_list = []
    for f in stator_faces:
        if f.get('name') not in ('slot', 'slot_opening'):
            continue
        verts = f.get('vertices', [])
        coords = verts[:-1] if (verts and verts[0] == verts[-1]) else verts
        n = len(coords)
        for i in range(n):
            line_list.append(
                Segment(begin=complex(coords[i][0] * mm, coords[i][1] * mm),
                        end=complex(coords[(i + 1) % n][0] * mm,
                                    coords[(i + 1) % n][1] * mm))
            )

    slot = SlotUD(line_list=line_list, Zs=n_slots) if line_list else None
    return LamSlotWind(
        Rint=r_stator_inner_mm * mm,
        Rext=r_stator_outer_mm * mm,
        L1=stack_length_mm * mm,
        Kf1=0.95,
        is_internal=False,
        is_stator=True,
        slot=slot,
        winding=Winding(Nlayer=2, Ntcoil=1, coil_pitch=1, p=n_slots // 2),
    )


def build_machine_from_faces(
    rotor_faces: list,
    stator_faces: list,
    dims: dict,
    machine_name: str = "DXF_Motor",
):
    """
    face 리스트 + dims → pyleecan Machine (HoleUD/SlotUD 방식).

    analyze_dxf_v2() + auto_name_faces_v2() 이후 호출하는 권장 경로.
    """
    if not _HAS_PYLEECAN:
        print("[pyleecan_bridge] pyleecan 미설치 → None 반환")
        return None

    topology = dims.get('topology', 'UNKNOWN')
    n_poles  = dims['n_poles']
    n_slots  = dims['n_slots']
    mm       = 1e-3

    try:
        from pyleecan.Classes.Shaft import Shaft

        rotor = build_rotor_from_faces(
            rotor_faces,
            r_shaft_mm=dims['r_shaft_mm'],
            r_rotor_outer_mm=dims['r_rotor_outer_mm'],
            n_poles=n_poles,
            stack_length_mm=dims.get('stack_length_mm', 100.0),
        )
        stator = build_stator_from_faces(
            stator_faces,
            r_stator_inner_mm=dims['r_stator_inner_mm'],
            r_stator_outer_mm=dims['r_stator_outer_mm'],
            n_slots=n_slots,
            stack_length_mm=dims.get('stack_length_mm', 100.0),
        )
        if rotor is None or stator is None:
            return None

        shaft = Shaft(Drsh=dims['r_shaft_mm'] * 2 * mm)

        if topology == 'SynRM':
            from pyleecan.Classes.MachineSyRM import MachineSyRM
            return MachineSyRM(name=machine_name, rotor=rotor,
                               stator=stator, shaft=shaft)
        elif topology in ('IPM', 'PMa-SynRM'):
            from pyleecan.Classes.MachineIPMSM import MachineIPMSM
            return MachineIPMSM(name=machine_name, rotor=rotor,
                                stator=stator, shaft=shaft)
        else:
            from pyleecan.Classes.MachineSIPMSM import MachineSIPMSM
            return MachineSIPMSM(name=machine_name, rotor=rotor,
                                 stator=stator, shaft=shaft)
    except Exception as e:
        print(f"[pyleecan_bridge] build_machine_from_faces 오류: {e}")
        return None
