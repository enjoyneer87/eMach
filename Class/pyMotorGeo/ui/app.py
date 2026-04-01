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
    build_machine_and_dims_from_dxf,
    build_export_bundle_from_analysis,
    check_pyleecan_available,
    dims_to_summary,
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
    try:
        tmp_path = _write_uploaded_to_temp(uploaded_file)
        data = GeometryBridge.convert_to_payload(tmp_path)
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

    if uploaded_file.name.lower().endswith(".dxf"):
        st.caption("DXF 입력일 때만 Pyleecan 브릿지를 실행할 수 있습니다.")

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

        if st.button("Run Pyleecan Bridge"):
            tmp_dxf_path = None
            try:
                tmp_dxf_path = _write_uploaded_to_temp(uploaded_file)
                machine, dims, analysis_result = build_machine_and_dims_from_dxf(
                    dxf_path=tmp_dxf_path,
                    machine_name=machine_name,
                    stack_length_mm=float(stack_length_mm),
                    enable_radius_fallback=True,
                    verbose=False,
                )

                st.session_state["pyleecan_dims"] = dims
                st.session_state["pyleecan_bundle"] = build_export_bundle_from_analysis(
                    dxf_filename=uploaded_file.name,
                    dims=dims,
                    analysis_result=analysis_result,
                    machine=machine,
                )
                st.session_state["pyleecan_machine_class"] = (
                    type(machine).__name__ if machine is not None else None
                )
                st.success("Pyleecan 브릿지 분석 완료")
            except Exception as e:
                st.error(f"Pyleecan 브릿지 실행 실패: {e}")
            finally:
                if tmp_dxf_path and os.path.exists(tmp_dxf_path):
                    os.remove(tmp_dxf_path)

        if "pyleecan_dims" in st.session_state and "pyleecan_bundle" in st.session_state:
            st.text(dims_to_summary(st.session_state["pyleecan_dims"]))

            bundle_json = json.dumps(
                st.session_state["pyleecan_bundle"],
                ensure_ascii=False,
                indent=2,
            )
            bundle_name = f"{Path(uploaded_file.name).stem}_pyleecan_bundle.json"
            st.download_button(
                "Download Pyleecan Bundle",
                data=bundle_json,
                file_name=bundle_name,
                mime="application/json",
            )

            if check_pyleecan_available():
                if st.session_state.get("pyleecan_machine_class"):
                    st.info(
                        f"Pyleecan Machine 생성됨: {st.session_state['pyleecan_machine_class']}"
                    )
                else:
                    st.warning(
                        "pyleecan은 설치되어 있으나 Machine 객체 생성에 실패했습니다. "
                        "DXF 품질/토폴로지 라벨을 확인해 주세요."
                    )
            else:
                st.info(
                    "pyleecan 패키지가 설치되어 있지 않아 Machine 객체는 생성되지 않았습니다. "
                    "대신 치수/라벨 번들은 정상 다운로드 가능합니다."
                )

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
        pts = ent.get("points", [])
        layer = ent.get("layer", "default")
        color = layer_colors.get(layer, layer_colors["default"])
        
        label = layer if layer not in drawn_layers else None
        drawn_layers.add(layer)
        
        # 1. LINE 및 POLYLINE (연속 선분)
        if ent_type in ['line', 'lwpolyline', 'polyline'] and pts:
            # 점 데이터를 풀어서 플로팅
            xs, ys = zip(*pts)
            ax.plot(xs, ys, color=color, linewidth=1.5, label=label)
            
        # 2. ARC (호)
        elif ent_type == 'arc' and ent.get("center") and ent.get("radius"):
            # pyMotorGeo의 notebook 6번/9번 셀 플로팅 방식과 동일하게 패치
            cx, cy = ent.get("center")
            r = ent.get("radius")
            sa = ent.get("start_angle", 0)
            ea = ent.get("end_angle", 360)
            # Matplotlib Arc는 width=2*r, height=2*r를 받음
            ax.add_patch(Arc((cx, cy), 2*r, 2*r, theta1=sa, theta2=ea, color=color, linewidth=1.5, label=label))
            
        # 3. CIRCLE (닫힌 원)
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
    
st.markdown("---")
with st.expander("Show Raw Payload JSON"):
    st.json(data if 'data' in locals() else {})
