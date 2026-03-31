# Palantir-Style Flow Visualization Workspace

This folder isolates the flow-visualization prototype so it can be evolved later without touching core pyMotorGeo modules.

## Structure

- `src/puml_flow_dashboard.py`: Plotly/Dash interactive dashboard
- `src/puml_flow_animator.py`: GIF animation generator
- `output/`: generated GIF files
- `docs/`: development notes and roadmap

## Quick Start

### 1) Install dependencies (once)

```powershell
c:/Users/user/.ansys_python_venvs/pyMotorEnv_310/Scripts/python.exe -m pip install dash plotly
```

### 2) Run interactive dashboard

```powershell
c:/Users/user/.ansys_python_venvs/pyMotorEnv_310/Scripts/python.exe d:/KangDH/Emlab_emach/Class/pyMotorGeo/palantir_viz/src/puml_flow_dashboard.py --workflow d:/KangDH/Emlab_emach/Class/pyMotorGeo_Workflow.puml --dependency d:/KangDH/Emlab_emach/Class/pyMotorGeo_Dependencies.puml --host 127.0.0.1 --port 8057
```

Open: `http://127.0.0.1:8057`

### 3) Regenerate GIF animations

```powershell
c:/Users/user/.ansys_python_venvs/pyMotorEnv_310/Scripts/python.exe d:/KangDH/Emlab_emach/Class/pyMotorGeo/palantir_viz/src/puml_flow_animator.py --input d:/KangDH/Emlab_emach/Class/pyMotorGeo_Workflow.puml --output d:/KangDH/Emlab_emach/Class/pyMotorGeo/palantir_viz/output/pyMotorGeo_Workflow_callflow.gif --mode sequence --fps 2

c:/Users/user/.ansys_python_venvs/pyMotorEnv_310/Scripts/python.exe d:/KangDH/Emlab_emach/Class/pyMotorGeo/palantir_viz/src/puml_flow_animator.py --input d:/KangDH/Emlab_emach/Class/pyMotorGeo_Dependencies.puml --output d:/KangDH/Emlab_emach/Class/pyMotorGeo/palantir_viz/output/pyMotorGeo_Dependencies_flow.gif --mode dependency --fps 2
```

## Notes

- Dashboard is a prototype, not production-hardened.
- Keep UI experiments in this folder first, then promote stable parts to main package.
