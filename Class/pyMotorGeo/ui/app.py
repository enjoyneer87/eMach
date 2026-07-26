import streamlit as st
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import tempfile
from pathlib import Path
import sys

# 프로젝트 루트를 PATH에 추가하여 contracts 모듈 및 geometry_bridge 등에 접근 가능하도록 함
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from geometry_bridge import GeometryBridge
from pyleecan_bridge import (
    build_export_bundle_from_machine_json,
    build_export_bundle_from_analysis,
    build_machine_and_dims_from_dxf,
    is_geometry_payload_json,
    is_pyleecan_machine_json,
    validate_pyleecan_machine_json_for_gui,
)
from pyleecan_subprocess_bridge import (
    default_pyleecan_python,
    run_external_pyleecan_bridge,
)


def _write_uploaded_to_temp(uploaded_file) -> str:
    ext_suffix = f".{uploaded_file.name.split('.')[-1]}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext_suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name

# Streamlit 설정
st.set_page_config(page_title="eMach Geometry Visualizer", layout="wide")

st.title("⚡ eMach 2D Geometry Dashboard (Local Prototype)")
st.markdown("""
**WS-A & WS-D 연동 UI**: `pyMotorGeo`에서 파싱된 2D 도면 데이터(형상 Contract Payload)를 웹브라우저에서 직접 시각화하고 검증합니다.
업로드한 형상 파일(.dxf, .json)이 내부적으로 `GeometryPayload` 규격(v1)으로 변환되는지 체크합니다.
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📂 Data Import")
    uploaded_file = st.file_uploader("Upload Geometry Payload (.json, .dxf)", type=["json", "dxf"])
    
    if uploaded_file is None:
        st.info("좌측 영역에 .json 또는 .dxf 형태의 모터 도면 파일을 업로드해보세요.")
        st.stop()
        
    tmp_path = None
    input_kind = "unknown"
    local_bundle_preview = None
    local_machine_json_preview = None
    try:
        tmp_path = _write_uploaded_to_temp(uploaded_file)

        if uploaded_file.name.lower().endswith(".json"):
            with open(tmp_path, "r", encoding="utf-8-sig") as f:
                raw_json = json.load(f)

            if is_pyleecan_machine_json(raw_json):
                input_kind = "pyleecan_machine_json"
                local_bundle_preview = build_export_bundle_from_machine_json(
                    machine_json=raw_json,
                    source_name=uploaded_file.name,
                )
                local_machine_json_preview = raw_json
                # machine JSON은 엔티티 기반 시각화 대상이 아니므로 빈 payload로 처리
                data = {
                    "contract_version": "machine-json",
                    "unit": "mm",
                    "entities": [],
                    "provenance": {"source_file": uploaded_file.name},
                }
                st.success("Pyleecan Machine JSON 로드 성공!")
            else:
                data = GeometryBridge.convert_to_payload(tmp_path)
                if isinstance(data, dict) and isinstance(data.get("dims"), dict):
                    input_kind = "bundle_json"
                    local_bundle_preview = data
                    st.success("Pyleecan Bundle JSON 로드 성공!")
                elif is_geometry_payload_json(data):
                    input_kind = "geometry_payload_json"
                    st.success("GeometryPayload JSON 로드 성공!")
                else:
                    input_kind = "json_unknown"
                    st.warning("JSON 형식을 인식하지 못했습니다. GeometryPayload/Pyleecan bundle/Machine JSON만 지원합니다.")
        else:
            data = GeometryBridge.convert_to_payload(tmp_path)
            input_kind = "dxf"
            st.success("도면 파싱 및 Payload 로드 성공!")
    except Exception as e:
        st.error(f"파싱 에러: {e}")
        st.stop()
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        
    st.subheader("Payload Health Check")
    version = data.get("contract_version", "unknown")
    st.write(f"- **Contract Version**: `{version}`")
    st.write(f"- **Unit**: `{data.get('unit', 'unknown')}`")
    st.write(f"- **Input Type**: `{input_kind}`")
    
    entities = data.get("entities", [])
    st.write(f"- **Total Entities**: `{len(entities)}`")
    
    layer_counts = {}
    for ent in entities:
        layer = ent.get("layer", "unknown")
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
        
    st.write("- **Elements per Layer**:")
    for l, c in layer_counts.items():
        st.write(f"  - `{l}` : {c} ea")

    st.subheader("🔁 Bridge Export")
    payload_json = json.dumps(data, ensure_ascii=False, indent=2)
    payload_name = f"{Path(uploaded_file.name).stem}_geometry_payload_v1.json"
    st.download_button(
        "Download GeometryPayload JSON",
        data=payload_json,
        file_name=payload_name,
        mime="application/json",
    )

    if local_bundle_preview is not None:
        preview_name = f"{Path(uploaded_file.name).stem}_pyleecan_bundle.json"
        preview_json = json.dumps(local_bundle_preview, ensure_ascii=False, indent=2)
        st.download_button(
            "Download Pyleecan Bundle (for bridge)",
            data=preview_json,
            file_name=preview_name,
            mime="application/json",
        )

    if local_machine_json_preview is not None:
        machine_preview_name = f"{Path(uploaded_file.name).stem}_pyleecan_machine_gui.json"
        machine_preview_json = json.dumps(local_machine_json_preview, ensure_ascii=False, indent=2)
        st.download_button(
            "Download Pyleecan Machine JSON (for GUI)",
            data=machine_preview_json,
            file_name=machine_preview_name,
            mime="application/json",
        )

        local_validation = validate_pyleecan_machine_json_for_gui(local_machine_json_preview)
        if local_validation.get("ok"):
            st.success("GUI import용 Machine JSON 최소 구조 검증 통과")
        else:
            st.warning("GUI import용 Machine JSON 검증 이슈가 있습니다.")
        for err in local_validation.get("errors", []):
            st.write(f"- error: {err}")
        for warn in local_validation.get("warnings", []):
            st.write(f"- warning: {warn}")

    if uploaded_file.name.lower().endswith(".dxf") or uploaded_file.name.lower().endswith(".json"):
        st.caption("외부 pyleecan env는 JSON-only 모드로 실행됩니다. 내부 브릿지용은 Bundle JSON, GUI Import용은 Machine JSON을 사용하세요.")

        machine_name = st.text_input(
            "Machine Name",
            value=Path(uploaded_file.name).stem,
            help="Pyleecan Machine 객체 이름",
        )
        stack_length_mm = st.number_input(
            "Stack Length (mm)",
            min_value=1.0,
            value=100.0,
            step=1.0,
        )
        pyleecan_python = st.text_input(
            "Pyleecan Python Executable",
            value=default_pyleecan_python(),
            help="pyleecan이 설치된 별도 가상환경의 python.exe 경로",
        )

        if st.button("Run Pyleecan Bridge"):
            tmp_input_path = None
            tmp_bundle_path = None
            try:
                tmp_input_path = _write_uploaded_to_temp(uploaded_file)
                bridge_input_path = tmp_input_path

                # JSON-only: DXF/기계 JSON은 UI env에서 먼저 bundle JSON으로 변환한다.
                if uploaded_file.name.lower().endswith(".dxf"):
                    machine_from_dxf, dims, analysis_result = build_machine_and_dims_from_dxf(
                        dxf_path=tmp_input_path,
                        machine_name=machine_name,
                        stack_length_mm=float(stack_length_mm),
                        enable_radius_fallback=True,
                        verbose=False,
                    )
                    bundle = build_export_bundle_from_analysis(
                        dxf_filename=uploaded_file.name,
                        dims=dims,
                        analysis_result=analysis_result,
                        machine=machine_from_dxf,
                    )
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_bundle_file:
                        tmp_bundle_file.write(json.dumps(bundle, ensure_ascii=False).encode("utf-8"))
                        tmp_bundle_path = tmp_bundle_file.name
                    bridge_input_path = tmp_bundle_path
                elif input_kind == "pyleecan_machine_json":
                    with open(tmp_input_path, "r", encoding="utf-8-sig") as f:
                        machine_json = json.load(f)
                    bundle = build_export_bundle_from_machine_json(
                        machine_json=machine_json,
                        source_name=uploaded_file.name,
                        stack_length_mm=float(stack_length_mm),
                    )
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_bundle_file:
                        tmp_bundle_file.write(json.dumps(bundle, ensure_ascii=False).encode("utf-8"))
                        tmp_bundle_path = tmp_bundle_file.name
                    bridge_input_path = tmp_bundle_path
                elif input_kind == "geometry_payload_json":
                    raise ValueError(
                        "GeometryPayload JSON은 pyleecan bundle 입력이 아닙니다. DXF 또는 Pyleecan bundle/machine JSON을 사용해 주세요."
                    )
                elif input_kind == "json_unknown":
                    raise ValueError(
                        "지원하지 않는 JSON 형식입니다. GeometryPayload/Pyleecan bundle/Machine JSON만 지원합니다."
                    )

                external_result = run_external_pyleecan_bridge(
                    input_path=bridge_input_path,
                    input_type="json",
                    source_name=uploaded_file.name,
                    machine_name=machine_name,
                    stack_length_mm=float(stack_length_mm),
                    pyleecan_python=pyleecan_python,
                    export_machine_json=True,
                )
                st.session_state["pyleecan_external_result"] = external_result

                if external_result.get("ok"):
                    st.success("Pyleecan 외부 env 브릿지 분석 완료")
                else:
                    st.error(
                        f"Pyleecan 브릿지 실행 실패: {external_result.get('error', 'unknown')}"
                    )
            except Exception as e:
                st.error(f"Pyleecan 브릿지 실행 실패: {e}")
            finally:
                if tmp_input_path and os.path.exists(tmp_input_path):
                    os.remove(tmp_input_path)
                if tmp_bundle_path and os.path.exists(tmp_bundle_path):
                    os.remove(tmp_bundle_path)

        if "pyleecan_external_result" in st.session_state:
            ext = st.session_state["pyleecan_external_result"]
            st.write(f"- **Runner Python**: `{ext.get('python_executable', 'unknown')}`")
            st.write(f"- **Return Code**: `{ext.get('returncode', 'N/A')}`")
            st.write(f"- **Pyleecan Version**: `{ext.get('pyleecan_version', 'unknown')}`")
            st.write(f"- **Pyleecan Module**: `{ext.get('pyleecan_module_path', 'unknown')}`")

            if ext.get("ok"):
                st.text(ext.get("dims_summary", ""))

                bundle_json = json.dumps(
                    ext.get("bundle", {}),
                    ensure_ascii=False,
                    indent=2,
                )
                bundle_name = f"{Path(uploaded_file.name).stem}_pyleecan_bundle.json"
                st.download_button(
                    "Download Pyleecan Bundle (for bridge)",
                    data=bundle_json,
                    file_name=bundle_name,
                    mime="application/json",
                )

                machine_json_payload = ext.get("machine_json")
                if isinstance(machine_json_payload, dict):
                    machine_json_text = json.dumps(machine_json_payload, ensure_ascii=False, indent=2)
                    machine_json_name = f"{Path(uploaded_file.name).stem}_pyleecan_machine_gui.json"
                    st.download_button(
                        "Download Pyleecan Machine JSON (for GUI)",
                        data=machine_json_text,
                        file_name=machine_json_name,
                        mime="application/json",
                    )

                    validation = ext.get("machine_json_validation") or {}
                    if validation.get("ok"):
                        st.success("Runner 생성 Machine JSON은 GUI import 최소 검증을 통과했습니다.")
                    else:
                        st.warning("Runner 생성 Machine JSON 검증에서 이슈가 감지되었습니다.")
                    for err in validation.get("errors", []):
                        st.write(f"- error: {err}")
                    for warn in validation.get("warnings", []):
                        st.write(f"- warning: {warn}")

                for warn in ext.get("warnings", []):
                    st.warning(warn)

                st.info(f"Pyleecan Machine 생성됨: {ext.get('machine_class', 'unknown')}")
            else:
                st.warning(
                    "외부 pyleecan env에서 객체 생성이 실패했습니다. "
                    "오류 로그를 확인해 주세요."
                )

            with st.expander("Runner Logs"):
                st.text(ext.get("stdout", ""))
                st.text(ext.get("stderr", ""))

with col2:
    st.header("🎨 Geometry Visualization")
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_aspect("equal")
    
    from matplotlib.patches import Arc, Circle
    
    # 레이어별 색상 정의
    layer_colors = {
        "rotor": "#1f77b4",  # Blue
        "stator": "#ff7f0e", # Orange
        "magnet": "#2ca02c", # Green
        "airgap": "#17becf",
        "default": "#7f7f7f"
    }
    
    drawn_layers = set()
    
    for ent in entities:
        ent_type = ent.get("entity_type", "unknown").lower()
        pts = ent.get("render_points") or ent.get("points", [])
        layer = ent.get("layer", "default")
        color = layer_colors.get(layer, layer_colors["default"])
        
        label = layer if layer not in drawn_layers else None
        drawn_layers.add(layer)
        
        # 1. LINE/POLYLINE/ARC/CIRCLE 모두 샘플 포인트 우선 렌더링
        if ent_type in ['line', 'lwpolyline', 'polyline', 'arc', 'circle'] and pts:
            # 점 데이터를 풀어서 플로팅
            xs, ys = zip(*pts)
            ax.plot(xs, ys, color=color, linewidth=1.5, label=label)
            
        # 2. ARC (fallback: 샘플 포인트가 없을 때)
        elif ent_type == 'arc' and ent.get("center") and ent.get("radius"):
            # pyMotorGeo의 notebook 6번/9번 셀 플로팅 방식과 동일하게 패치
            cx, cy = ent.get("center")
            r = ent.get("radius")
            sa = ent.get("start_angle", 0)
            ea = ent.get("end_angle", 360)
            # Matplotlib Arc는 width=2*r, height=2*r를 받음
            ax.add_patch(Arc((cx, cy), 2*r, 2*r, theta1=sa, theta2=ea, color=color, linewidth=1.5, label=label))
            
        # 3. CIRCLE (fallback: 샘플 포인트가 없을 때)
        elif ent_type == 'circle' and ent.get("center") and ent.get("radius"):
            cx, cy = ent.get("center")
            r = ent.get("radius")
            ax.add_patch(Circle((cx, cy), r, fill=False, color=color, linewidth=1.5, label=label))

            
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title("2D Geometry Entity Viewer")
    ax.set_xlabel(f"X ({data.get('unit', 'mm')})")
    ax.set_ylabel(f"Y ({data.get('unit', 'mm')})")
    
    if drawn_layers:
        ax.legend()
        
    st.pyplot(fig)

    st.subheader("🔍 Compare View (Minimum)")
    current_snapshot = {
        "entity_count": len(entities),
        "layer_counts": layer_counts,
    }
    previous_snapshot = st.session_state.get("previous_payload_snapshot")

    if previous_snapshot:
        prev_count = int(previous_snapshot.get("entity_count", 0))
        curr_count = int(current_snapshot["entity_count"])
        delta = curr_count - prev_count
        st.write(f"- Previous Entities: {prev_count}")
        st.write(f"- Current Entities: {curr_count}")
        st.write(f"- Delta: {delta:+d}")
    else:
        st.caption("이전 업로드 스냅샷이 없어 비교 기준이 없습니다.")

    if st.button("Set Current As Compare Baseline"):
        st.session_state["previous_payload_snapshot"] = current_snapshot
        st.success("현재 payload를 Compare 기준으로 저장했습니다.")
    
st.markdown("---")
with st.expander("Show Raw Payload JSON"):
    st.json(data if 'data' in locals() else {})
