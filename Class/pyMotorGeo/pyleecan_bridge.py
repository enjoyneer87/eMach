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
from typing import Any, Dict, Optional, Tuple

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
    def _num(v, default=None):
        if v is None:
            return default
        try:
            return float(v)
        except Exception:
            return default

    n_poles = int(dims.get('n_poles', 0) or 0)
    n_slots = int(dims.get('n_slots', 0) or 0)
    p_pairs = dims.get('p')
    if p_pairs is None and n_poles:
        p_pairs = n_poles // 2

    rotor_rint = _num(dims.get('rotor_Rint_mm', dims.get('r_shaft_mm')))
    rotor_rext = _num(dims.get('rotor_Rext_mm', dims.get('r_rotor_outer_mm')))
    stator_rint = _num(dims.get('stator_Rint_mm', dims.get('r_stator_inner_mm')))
    stator_rext = _num(dims.get('stator_Rext_mm', dims.get('r_stator_outer_mm')))
    airgap = _num(dims.get('airgap_mm'))
    if airgap is None and rotor_rext is not None and stator_rint is not None:
        airgap = stator_rint - rotor_rext

    pole_pitch = _num(dims.get('pole_pitch_deg'))
    if pole_pitch is None and n_poles:
        pole_pitch = 360.0 / n_poles
    slot_pitch = _num(dims.get('slot_pitch_deg'))
    if slot_pitch is None and n_slots:
        slot_pitch = 360.0 / n_slots

    lines = [
        f"Motor Dimensions (from DXF)",
        f"{'='*40}",
        f"  Topology    : {dims.get('topology', 'UNKNOWN')}",
        f"  Poles       : {n_poles if n_poles else 'N/A'}",
        f"  Slots       : {n_slots if n_slots else 'N/A'}",
        f"  p (pairs)   : {p_pairs if p_pairs is not None else 'N/A'}",
        f"  Rotor  Rint : {rotor_rint:.2f} mm" if rotor_rint is not None else "  Rotor  Rint : N/A",
        f"  Rotor  Rext : {rotor_rext:.2f} mm" if rotor_rext is not None else "  Rotor  Rext : N/A",
        f"  Stator Rint : {stator_rint:.2f} mm" if stator_rint is not None else "  Stator Rint : N/A",
        f"  Stator Rext : {stator_rext:.2f} mm" if stator_rext is not None else "  Stator Rext : N/A",
        f"  Airgap      : {airgap:.3f} mm" if airgap is not None else "  Airgap      : N/A",
        f"  Pole pitch  : {pole_pitch:.2f}°" if pole_pitch is not None else "  Pole pitch  : N/A",
        f"  Slot pitch  : {slot_pitch:.2f}°" if slot_pitch is not None else "  Slot pitch  : N/A",
    ]
    if dims.get('magnet_thickness_mm', 0) > 0:
        lines.append(f"  Mag thick.  : {dims['magnet_thickness_mm']:.2f} mm")
        lines.append(f"  Mag arc     : {dims['magnet_arc_deg']:.2f}°")
    return '\n'.join(lines)


def check_pyleecan_available() -> bool:
    """pyleecan이 설치되어 있는지 확인."""
    return _HAS_PYLEECAN


def is_geometry_payload_json(payload: dict) -> bool:
    """입력 JSON이 GeometryPayload(v1 유사)인지 판별."""
    if not isinstance(payload, dict):
        return False
    entities = payload.get("entities")
    return isinstance(entities, list) and payload.get("contract_version") is not None


def is_pyleecan_machine_json(payload: dict) -> bool:
    """입력 JSON이 pyleecan Machine 직렬화 포맷인지 판별."""
    if not isinstance(payload, dict):
        return False
    cls_name = str(payload.get("__class__", ""))
    if not cls_name.startswith("Machine"):
        return False
    return isinstance(payload.get("rotor"), dict) and isinstance(payload.get("stator"), dict)


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _to_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _m_to_mm(value: Any) -> Optional[float]:
    num = _to_float(value)
    if num is None:
        return None
    return num * 1e3


def _topology_from_machine_class(class_name: str) -> str:
    mapping = {
        "MachineIPMSM": "IPM",
        "MachineSIPMSM": "SPM",
        "MachineSPMSM": "SPM",
        "MachineSyRM": "SynRM",
    }
    return mapping.get(class_name, "UNKNOWN")


def _extract_pole_count(machine_json: dict) -> Optional[int]:
    rotor = machine_json.get("rotor", {})
    holes = rotor.get("hole")
    if isinstance(holes, list) and holes:
        for hole in holes:
            if isinstance(hole, dict) and hole.get("Zh") is not None:
                poles = _to_int(hole.get("Zh"))
                if poles and poles > 0:
                    return poles

    slot = rotor.get("slot")
    if isinstance(slot, dict):
        poles = _to_int(slot.get("Zs"))
        if poles and poles > 0:
            return poles
    return None


def _extract_slot_count(machine_json: dict) -> Optional[int]:
    stator = machine_json.get("stator", {})
    slot = stator.get("slot")
    if isinstance(slot, dict):
        slots = _to_int(slot.get("Zs"))
        if slots and slots > 0:
            return slots
    return None


def _extract_rotor_hole_pack(machine_json: dict) -> list:
    rotor = machine_json.get("rotor", {})
    holes = rotor.get("hole")
    if not isinstance(holes, list):
        return []

    numeric_keys = ("W0", "W1", "W2", "W3", "W4", "H0", "H1", "H2", "H3")
    pack = []
    for idx, hole in enumerate(holes):
        if not isinstance(hole, dict):
            continue
        item = {
            "index": idx,
            "class": hole.get("__class__"),
            "Zh": _to_int(hole.get("Zh")),
        }
        for key in numeric_keys:
            raw_val = _to_float(hole.get(key))
            if raw_val is None:
                continue
            item[key] = raw_val
            if abs(raw_val) <= 1.0:
                item[f"{key}_mm"] = raw_val * 1e3
        pack.append(item)
    return pack


def _extract_slot_pack(machine_json: dict) -> dict:
    stator = machine_json.get("stator", {})
    slot = stator.get("slot", {})
    if not isinstance(slot, dict):
        return {}

    out = {
        "class": slot.get("__class__"),
        "Zs": _to_int(slot.get("Zs")),
    }
    for key in ("H0", "H1", "H2", "H3", "W0", "W1", "W2", "W3", "W4"):
        val = _to_float(slot.get(key))
        if val is None:
            continue
        out[key] = val
        if abs(val) <= 1.0:
            out[f"{key}_mm"] = val * 1e3
    return out


def _extract_material_brief(mat: dict) -> dict:
    if not isinstance(mat, dict):
        return {}

    mag = mat.get("mag", {}) if isinstance(mat.get("mag"), dict) else {}
    elec = mat.get("elec", {}) if isinstance(mat.get("elec"), dict) else {}
    struct = mat.get("struct", {}) if isinstance(mat.get("struct"), dict) else {}

    bh_value = None
    bh_curve = mag.get("BH_curve")
    if isinstance(bh_curve, dict):
        value = bh_curve.get("value")
        if isinstance(value, list):
            bh_value = value

    return {
        "name": mat.get("name"),
        "desc": mat.get("desc"),
        "rho_ohm_m": _to_float(elec.get("rho")),
        "mur_lin": _to_float(mag.get("mur_lin")),
        "Brm20_T": _to_float(mag.get("Brm20")),
        "Wlam_mm": (_to_float(mag.get("Wlam")) or 0.0) * 1e3,
        "density_kg_m3": _to_float(struct.get("rho")),
        "BH_curve": bh_value,
    }


def _extract_winding_pack(machine_json: dict) -> dict:
    stator = machine_json.get("stator", {})
    winding = stator.get("winding")
    if not isinstance(winding, dict):
        return {}

    out = {
        "class": winding.get("__class__"),
        "Lewout_mm": _m_to_mm(winding.get("Lewout")),
        "Nlayer": _to_int(winding.get("Nlayer")),
        "Npcp": _to_int(winding.get("Npcp")),
        "Ntcoil": _to_int(winding.get("Ntcoil")),
        "coil_pitch": _to_int(winding.get("coil_pitch")),
        "p": _to_int(winding.get("p")),
        "qs": _to_int(winding.get("qs")),
    }

    conductor = winding.get("conductor")
    if isinstance(conductor, dict):
        out["conductor"] = {
            "class": conductor.get("__class__"),
            "Nwppc": _to_int(conductor.get("Nwppc")),
            "Wins_cond_mm": _m_to_mm(conductor.get("Wins_cond")),
            "Wins_wire_mm": _m_to_mm(conductor.get("Wins_wire")),
            "Wwire_mm": _m_to_mm(conductor.get("Wwire")),
            "cond_mat": _extract_material_brief(conductor.get("cond_mat")),
            "ins_mat": _extract_material_brief(conductor.get("ins_mat")),
        }

    return out


def extract_dims_from_pyleecan_machine_json(
    machine_json: dict,
    stack_length_mm: Optional[float] = None,
) -> dict:
    """pyleecan Machine JSON에서 dims 요약을 생성 (m -> mm 변환)."""
    if not is_pyleecan_machine_json(machine_json):
        raise ValueError("Invalid pyleecan machine JSON payload")

    rotor = machine_json.get("rotor", {})
    stator = machine_json.get("stator", {})
    winding = stator.get("winding") if isinstance(stator.get("winding"), dict) else {}

    n_poles = _extract_pole_count(machine_json)
    n_slots = _extract_slot_count(machine_json)
    p_pair = _to_int(winding.get("p")) if isinstance(winding, dict) else None
    if p_pair is None and n_poles:
        p_pair = n_poles // 2

    rotor_rint = _m_to_mm(rotor.get("Rint"))
    rotor_rext = _m_to_mm(rotor.get("Rext"))
    stator_rint = _m_to_mm(stator.get("Rint"))
    stator_rext = _m_to_mm(stator.get("Rext"))

    airgap = None
    if rotor_rext is not None and stator_rint is not None:
        airgap = stator_rint - rotor_rext

    pole_pitch_deg = 360.0 / n_poles if n_poles else None
    slot_pitch_deg = 360.0 / n_slots if n_slots else None

    holes = rotor.get("hole") if isinstance(rotor.get("hole"), list) else []
    first_hole = holes[0] if holes and isinstance(holes[0], dict) else {}
    magnet_thickness_mm = None
    magnet_arc_deg = None
    if isinstance(first_hole, dict):
        h2 = _to_float(first_hole.get("H2"))
        if h2 is not None:
            magnet_thickness_mm = h2 * 1e3 if abs(h2) <= 1.0 else h2
        w0 = _to_float(first_hole.get("W0"))
        if w0 is not None:
            magnet_arc_deg = w0

    inferred_stack = _m_to_mm(stator.get("L1"))
    if inferred_stack is None:
        inferred_stack = _m_to_mm(rotor.get("L1"))
    final_stack = float(stack_length_mm) if stack_length_mm is not None else (inferred_stack or 100.0)

    class_name = str(machine_json.get("__class__", ""))
    dims = {
        "rotor_Rint_mm": rotor_rint,
        "rotor_Rext_mm": rotor_rext,
        "stator_Rint_mm": stator_rint,
        "stator_Rext_mm": stator_rext,
        "airgap_mm": airgap,
        "n_poles": n_poles,
        "n_slots": n_slots,
        "p": p_pair,
        "pole_pitch_deg": pole_pitch_deg,
        "slot_pitch_deg": slot_pitch_deg,
        "magnet_thickness_mm": magnet_thickness_mm,
        "magnet_arc_deg": magnet_arc_deg,
        "stack_length_mm": final_stack,
        "topology": _topology_from_machine_class(class_name),
    }

    # 다른 경로와의 호환을 위한 별칭 키
    if rotor_rint is not None:
        dims["r_shaft_mm"] = rotor_rint
    if rotor_rext is not None:
        dims["r_rotor_outer_mm"] = rotor_rext
    if stator_rint is not None:
        dims["r_stator_inner_mm"] = stator_rint
    if stator_rext is not None:
        dims["r_stator_outer_mm"] = stator_rext

    return {k: v for k, v in dims.items() if v is not None}


def build_export_bundle_from_machine_json(
    machine_json: dict,
    source_name: str = "machine.json",
    stack_length_mm: Optional[float] = None,
) -> dict:
    """pyleecan Machine JSON을 app/runner 공용 bundle 포맷으로 변환."""
    dims = extract_dims_from_pyleecan_machine_json(
        machine_json=machine_json,
        stack_length_mm=stack_length_mm,
    )

    rotor = machine_json.get("rotor", {}) if isinstance(machine_json.get("rotor"), dict) else {}
    stator = machine_json.get("stator", {}) if isinstance(machine_json.get("stator"), dict) else {}

    warnings = []
    if "n_poles" not in dims:
        warnings.append("n_poles missing from machine JSON")
    if "n_slots" not in dims:
        warnings.append("n_slots missing from machine JSON")

    return {
        "bridge_version": "v1",
        "source": {
            "filename": source_name,
            "pipeline": "machine_json_import",
            "machine_json_class": machine_json.get("__class__"),
            "machine_json_version": machine_json.get("__version__"),
        },
        "dims": dims,
        "faces": {
            "rotor_count": 0,
            "stator_count": 0,
            "rotor_labels": [],
            "stator_labels": [],
        },
        "machine": {
            "pyleecan_available": bool(_HAS_PYLEECAN),
            "machine_class": machine_json.get("__class__"),
            "machine_name": machine_json.get("name"),
            "from_machine_json": True,
        },
        "rotor_holes": _extract_rotor_hole_pack(machine_json),
        "slot_config": _extract_slot_pack(machine_json),
        "winding_config": _extract_winding_pack(machine_json),
        "materials": {
            "rotor": _extract_material_brief(rotor.get("mat_type")),
            "stator": _extract_material_brief(stator.get("mat_type")),
        },
        "warnings": warnings,
    }


def validate_pyleecan_machine_json_for_gui(machine_json: dict) -> dict:
    """GUI import 관점의 최소 구조/단위 sanity 검증."""
    errors = []
    warnings = []

    if not isinstance(machine_json, dict):
        return {
            "ok": False,
            "errors": ["machine_json payload must be a dict"],
            "warnings": [],
        }

    required_root = ("__class__", "rotor", "stator", "shaft")
    for key in required_root:
        if key not in machine_json:
            errors.append(f"missing root key: {key}")

    rotor = machine_json.get("rotor") if isinstance(machine_json.get("rotor"), dict) else None
    stator = machine_json.get("stator") if isinstance(machine_json.get("stator"), dict) else None

    if rotor is None:
        errors.append("rotor must be an object")
    if stator is None:
        errors.append("stator must be an object")

    if stator is not None:
        if not isinstance(stator.get("slot"), dict):
            errors.append("stator.slot must be an object")
        if not isinstance(stator.get("winding"), dict):
            warnings.append("stator.winding is missing or not an object")

    def _sanity_meter(val, name):
        num = _to_float(val)
        if num is None:
            errors.append(f"{name} missing or invalid")
            return None
        if num <= 0:
            errors.append(f"{name} must be > 0")
            return None
        if num > 2:
            warnings.append(f"{name}={num} looks too large for meter unit")
        return num

    if rotor is not None and stator is not None:
        rint = _sanity_meter(rotor.get("Rint"), "rotor.Rint")
        rext = _sanity_meter(rotor.get("Rext"), "rotor.Rext")
        sint = _sanity_meter(stator.get("Rint"), "stator.Rint")
        sext = _sanity_meter(stator.get("Rext"), "stator.Rext")
        l1 = _sanity_meter(stator.get("L1"), "stator.L1")

        if rint is not None and rext is not None and not (rint < rext):
            errors.append("rotor.Rint must be smaller than rotor.Rext")
        if sint is not None and sext is not None and not (sint < sext):
            errors.append("stator.Rint must be smaller than stator.Rext")
        if rext is not None and sint is not None and not (rext < sint):
            warnings.append("rotor.Rext should be smaller than stator.Rint")
        if l1 is not None and l1 < 1e-4:
            warnings.append("stator.L1 is very small; check meter/mm unit conversion")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


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


def build_machine_and_dims_from_dxf(
    dxf_path: str,
    machine_name: str = "DXF_Motor",
    origin: Tuple[float, float] = (0.0, 0.0),
    n_poles: Optional[int] = None,
    n_slots: Optional[int] = None,
    stack_length_mm: float = 100.0,
    enable_radius_fallback: bool = True,
    verbose: bool = False,
) -> Tuple[object, dict, dict]:
    """
    DXF 파일을 분석해 pyleecan Machine 객체와 치수 정보를 함께 생성합니다.

    Returns
    -------
    tuple
        (machine, dims, analysis_result)
    """
    from pipeline import analyze_dxf_v2

    analysis_result = analyze_dxf_v2(
        dxf_path=dxf_path,
        origin=origin,
        n_poles=n_poles,
        n_slots=n_slots,
        enable_radius_fallback=enable_radius_fallback,
        verbose=verbose,
    )

    dims = dict(analysis_result.get("dims", {}))
    if "p" not in dims and dims.get("n_poles"):
        dims["p"] = int(dims["n_poles"]) // 2

    # 상위 호환: 다른 경로에서 사용하는 키 별칭을 함께 채움
    if "rotor_Rint_mm" not in dims and "r_shaft_mm" in dims:
        dims["rotor_Rint_mm"] = dims["r_shaft_mm"]
    if "rotor_Rext_mm" not in dims and "r_rotor_outer_mm" in dims:
        dims["rotor_Rext_mm"] = dims["r_rotor_outer_mm"]
    if "stator_Rint_mm" not in dims and "r_stator_inner_mm" in dims:
        dims["stator_Rint_mm"] = dims["r_stator_inner_mm"]
    if "stator_Rext_mm" not in dims and "r_stator_outer_mm" in dims:
        dims["stator_Rext_mm"] = dims["r_stator_outer_mm"]

    dims["stack_length_mm"] = float(stack_length_mm)

    machine = build_machine_from_faces(
        rotor_faces=analysis_result.get("rotor_faces", []),
        stator_faces=analysis_result.get("stator_faces", []),
        dims=dims,
        machine_name=machine_name,
    )
    return machine, dims, analysis_result


def build_export_bundle_from_analysis(
    dxf_filename: str,
    dims: dict,
    analysis_result: dict,
    machine: object = None,
) -> dict:
    """UI/CLI 다운로드용 직렬화 가능한 Pyleecan 입력 번들을 생성합니다."""
    rotor_faces = analysis_result.get("rotor_faces", [])
    stator_faces = analysis_result.get("stator_faces", [])

    return {
        "bridge_version": "v1",
        "source": {
            "filename": dxf_filename,
            "pipeline": "analyze_dxf_v2",
        },
        "dims": dims,
        "faces": {
            "rotor_count": len(rotor_faces),
            "stator_count": len(stator_faces),
            "rotor_labels": sorted({f.get("name", "unknown") for f in rotor_faces}),
            "stator_labels": sorted({f.get("name", "unknown") for f in stator_faces}),
        },
        "machine": {
            "pyleecan_available": bool(_HAS_PYLEECAN),
            "machine_class": type(machine).__name__ if machine is not None else None,
        },
    }
