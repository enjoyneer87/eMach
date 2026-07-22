# -*- coding: utf-8 -*-
"""Fluent Meshing watertight 워크플로우: multi-solid STL -> 볼륨메시 -> 솔버메시."""
import os, traceback
LOG=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\flu_wtm.txt"
def W(*a):
    with open(LOG,"a",encoding="utf-8") as f: f.write(" ".join(str(x) for x in a)+"\n")
open(LOG,"w").close()
STL=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\spray_e10_multisolid.stl"
OUT=r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\spray_e10_solver.msh.h5"
try:
    import ansys.fluent.core as pf
    meshing = pf.launch_fluent(mode="meshing", precision="double", processor_count=4,
                               ui_mode="no_gui_or_graphics", start_timeout=300)
    W("launched", pf.__version__)
    wf = meshing.workflow
    wf.InitializeWorkflow(WorkflowType="Watertight Geometry")
    W("workflow initialized; tasks:", [t for t in wf.TaskObject.get_object_names()] if hasattr(wf.TaskObject,"get_object_names") else "?")

    # 1) Import Geometry (STL=faceted surface mesh -> FileFormat "Mesh", 인자 FileNames)
    ig = wf.TaskObject["Import Geometry"]
    ig.Arguments.set_state({"FileFormat": "Mesh", "FileNames": STL,
                            "LengthUnit": "m"})
    W("ImportGeometry args set:", ig.Arguments.get_state())
    ig.Execute()
    W("[ok] Import Geometry executed")

    # 2) surface mesh (STL이면 이미 표면메시 - 태스크 있으면 실행)
    for tn in ("Generate the Surface Mesh","Improve Surface Mesh"):
        try:
            t=wf.TaskObject[tn]; t.Execute(); W(f"[ok] {tn}")
        except Exception as e: W(f"[skip] {tn}: {repr(e)[:100]}")

    # 3) Describe Geometry (유체+고체 존재)
    try:
        dg=wf.TaskObject["Describe Geometry"]
        dg.Arguments.set_state({"SetupType":"The geometry consists of both fluid and solid regions and/or voids"})
        dg.Execute(); W("[ok] Describe Geometry (fluid+solid)")
    except Exception as e: W("[skip] Describe:", repr(e)[:120])

    # 4) Update Regions / Boundaries
    for tn in ("Update Boundaries","Update Regions"):
        try:
            t=wf.TaskObject[tn]; t.Execute(); W(f"[ok] {tn}")
        except Exception as e: W(f"[skip] {tn}: {repr(e)[:100]}")

    # 5) Volume Mesh
    for tn in ("Add Boundary Layers","Generate the Volume Mesh"):
        try:
            t=wf.TaskObject[tn]; t.Execute(); W(f"[ok] {tn}")
        except Exception as e: W(f"[skip] {tn}: {repr(e)[:100]}")

    # 솔버로 전환 + 메시 저장
    try:
        meshing.tui.mesh.check_mesh()
    except Exception: pass
    try:
        meshing.meshing.File.WriteMesh(FileName=OUT)  # 신 API
        W("[ok] mesh written(new API):", OUT)
    except Exception as e:
        W("[try] WriteMesh new fail:", repr(e)[:100])
        try:
            meshing.scheme_eval.scheme_eval(f'(ti-menu-load-string "/file/write-mesh \\"{OUT}\\"")')
            W("[ok] mesh written(TUI):", OUT)
        except Exception as e2: W("write TUI fail:", repr(e2)[:120])
    W("exists:", os.path.exists(OUT), os.path.getsize(OUT) if os.path.exists(OUT) else 0)
    W("DONE-OK")
    meshing.exit()
except Exception:
    W("EXC:", traceback.format_exc())
os._exit(0)
