import argparse
import json
import traceback
from pathlib import Path
import sys

# Ensure local imports from pyMotorGeo package directory work in external env.
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from pyleecan_bridge import (
    build_export_bundle_from_machine_json,
    build_machine_and_dims_from_dxf,
    build_export_bundle_from_analysis,
    check_pyleecan_available,
    create_pyleecan_machine,
    dims_to_summary,
    is_pyleecan_machine_json,
    validate_pyleecan_machine_json_for_gui,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pyleecan bridge in dedicated Python env")
    parser.add_argument("--dxf-path", default=None)
    parser.add_argument("--bundle-json", default=None)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--machine-name", required=True)
    parser.add_argument("--stack-length-mm", type=float, default=100.0)
    parser.add_argument("--export-machine-json", action="store_true")
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    if not args.dxf_path and not args.bundle_json:
        raise ValueError("Either --dxf-path or --bundle-json must be provided")

    out_path = Path(args.output_json)
    result = {
        "ok": False,
        "error": None,
        "machine_class": None,
        "dims": None,
        "dims_summary": None,
        "bundle": None,
        "machine_json": None,
        "machine_json_validation": None,
        "warnings": [],
        "pyleecan_available": check_pyleecan_available(),
        "pyleecan_version": None,
        "pyleecan_module_path": None,
    }

    try:
        if not result["pyleecan_available"]:
            raise RuntimeError("pyleecan package is not available in this Python environment")

        import pyleecan as _pyleecan
        result["pyleecan_version"] = getattr(_pyleecan, "__version__", None)
        result["pyleecan_module_path"] = getattr(_pyleecan, "__file__", None)

        bundle_input = None

        if args.bundle_json:
            payload = json.loads(Path(args.bundle_json).read_text(encoding="utf-8-sig"))
            if isinstance(payload, dict) and isinstance(payload.get("dims"), dict):
                bundle_input = payload
                dims = dict(payload.get("dims", {}))
            elif is_pyleecan_machine_json(payload):
                bundle_input = build_export_bundle_from_machine_json(
                    machine_json=payload,
                    source_name=args.source_name,
                    stack_length_mm=float(args.stack_length_mm),
                )
                dims = dict(bundle_input.get("dims", {}))
            elif isinstance(payload, dict):
                dims = payload
            else:
                raise ValueError("Invalid bundle JSON: expected object payload")

            if not isinstance(dims, dict):
                raise ValueError("Invalid bundle JSON: 'dims' dictionary is required")

            if "p" not in dims and dims.get("n_poles"):
                dims["p"] = int(dims["n_poles"]) // 2

            machine = create_pyleecan_machine(dims=dims, machine_name=args.machine_name)
            analysis_result = {"rotor_faces": [], "stator_faces": []}
        else:
            machine, dims, analysis_result = build_machine_and_dims_from_dxf(
                dxf_path=args.dxf_path,
                machine_name=args.machine_name,
                stack_length_mm=float(args.stack_length_mm),
                enable_radius_fallback=True,
                verbose=False,
            )

        if machine is None:
            raise RuntimeError("Pyleecan machine creation failed (machine is None)")

        bundle = build_export_bundle_from_analysis(
            dxf_filename=args.source_name,
            dims=dims,
            analysis_result=analysis_result,
            machine=machine,
        )

        if isinstance(bundle_input, dict):
            for key, value in bundle_input.items():
                if key in ("bridge_version", "source", "dims", "faces", "machine"):
                    continue
                bundle[key] = value

            existing_source = bundle_input.get("source") if isinstance(bundle_input.get("source"), dict) else {}
            if existing_source:
                bundle["source"].update(existing_source)

            existing_machine = bundle_input.get("machine") if isinstance(bundle_input.get("machine"), dict) else {}
            if existing_machine:
                merged_machine = dict(existing_machine)
                merged_machine.update(bundle["machine"])
                bundle["machine"] = merged_machine

        result["ok"] = True
        result["machine_class"] = type(machine).__name__
        result["dims"] = dims
        result["dims_summary"] = dims_to_summary(dims)
        result["bundle"] = bundle

        if args.export_machine_json:
            import tempfile

            tmp_machine_json_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_machine_file:
                    tmp_machine_json_path = tmp_machine_file.name

                machine.save(save_path=tmp_machine_json_path)
                machine_json = json.loads(
                    Path(tmp_machine_json_path).read_text(encoding="utf-8-sig")
                )
                result["machine_json"] = machine_json
                result["machine_json_validation"] = validate_pyleecan_machine_json_for_gui(
                    machine_json
                )
            except Exception as exc:
                result["warnings"].append(
                    f"Machine JSON export failed: {type(exc).__name__}: {exc}"
                )
            finally:
                if tmp_machine_json_path and Path(tmp_machine_json_path).exists():
                    Path(tmp_machine_json_path).unlink()
    except Exception as exc:
        err_name = type(exc).__name__
        err_text = str(exc)
        if "DXFStructureError" in err_name or "Invalid header variable" in err_text:
            result["warnings"].append(
                "Input DXF appears corrupted or non-standard. Please re-save/export a valid DXF and retry."
            )
        result["error"] = f"{err_name}: {err_text}"
        result["traceback"] = traceback.format_exc()

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
