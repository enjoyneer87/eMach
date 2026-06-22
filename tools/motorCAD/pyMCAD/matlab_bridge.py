from __future__ import annotations

import argparse
import json
import pathlib
import tempfile
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BridgeResult:
    ok: bool
    payload: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    return float(v)


def _serialize_magnetic_region(mr: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    elements: list[dict[str, Any]] = []
    for region in (getattr(mr, "_regions", []) or []):
        for e in (getattr(region, "elements", []) or []):
            bx = getattr(e, "bx", None)
            by = getattr(e, "by", None)
            b = getattr(e, "b", None)
            if b is None and bx is not None and by is not None:
                b = (float(bx) ** 2 + float(by) ** 2) ** 0.5
            elements.append(
                {
                    "tri_index": int(getattr(e, "tri_index")),
                    "node_1": int(getattr(e, "node_1")),
                    "node_2": int(getattr(e, "node_2")),
                    "node_3": int(getattr(e, "node_3")),
                    "reg_code": int(getattr(e, "reg_code")),
                    "bx": _to_float(bx),
                    "by": _to_float(by),
                    "b": _to_float(b),
                    "a": float(getattr(e, "a", 0.0) or 0.0),
                    "j": float(getattr(e, "j", 0.0) or 0.0),
                }
            )

    node_xy = dict(getattr(mr, "node_xy", {}) or {})
    nodes: list[dict[str, Any]] = []
    for nid in sorted(node_xy.keys()):
        xy = node_xy[nid]
        nodes.append({"node_index": int(nid), "x_mm": float(xy[0]), "y_mm": float(xy[1])})

    return elements, nodes


def _serialize_step_payload(ts: Any, step: int) -> dict[str, Any]:
    mr = ts.by_step[int(step)]
    meta = ts.meta.get(int(step), {}) if hasattr(ts, "meta") else {}
    elements, nodes = _serialize_magnetic_region(mr)
    return {
        "step": int(step),
        "meta": meta,
        "elements": elements,
        "nodes": nodes,
    }


def _pick_step(steps: list[int], step_arg: str) -> tuple[int | None, str | None]:
    if not steps:
        return None, "E-DATA-EMPTY-STEPS"
    if step_arg.lower() == "none":
        return int(steps[0]), None

    use_step = int(float(step_arg))
    if use_step not in steps:
        return None, f"E-ARG-STEP-NOT-FOUND:{use_step}"
    return use_step, None


def _load_magnetic_from_file(path: pathlib.Path, step_arg: str, all_steps: bool = False) -> BridgeResult:
    from tools.motorCAD.pyMCAD import get_magnetic_data_from_file, get_magnetic_timeseries_from_file

    ts = None
    steps: list[int] = []
    try:
        ts = get_magnetic_timeseries_from_file(path, key="time_index", clean_up=False)
        steps = sorted([int(s) for s in ts.steps])
    except Exception:
        ts = None
        steps = []

    if steps:
        if bool(all_steps):
            by_steps = [_serialize_step_payload(ts, s) for s in steps]
            first_payload = by_steps[0]
            payload = {
                "steps": steps,
                "used_step": int(first_payload["step"]),
                "meta": first_payload.get("meta", {}),
                "source_mode": "direct_file_parse",
                "bridge_notes": "all_steps",
                "elements": first_payload["elements"],
                "nodes": first_payload["nodes"],
                "by_steps": by_steps,
            }
            return BridgeResult(ok=True, payload=payload)

        used_step, err = _pick_step(steps, step_arg)
        if err is not None or used_step is None:
            return BridgeResult(ok=False, payload={}, error_code=err, error_message="Invalid step request")

        step_payload = _serialize_step_payload(ts, int(used_step))
        payload = {
            "steps": steps,
            "used_step": int(step_payload["step"]),
            "meta": step_payload["meta"],
            "source_mode": "direct_file_parse",
            "bridge_notes": "",
            "elements": step_payload["elements"],
            "nodes": step_payload["nodes"],
        }
        return BridgeResult(ok=True, payload=payload)

    # timeseries parse failed — try single-snapshot
    # When all_steps=True, we must NOT accept a snapshot as success: the Motor-CAD
    # fallback must be triggered so that all time steps are exported properly.
    if bool(all_steps):
        return BridgeResult(
            ok=False,
            payload={},
            error_code="E-PARSE-NO-TIMESERIES",
            error_message="Timeseries parse yielded no steps; Motor-CAD fallback required for all_steps mode.",
        )

    try:
        mr = get_magnetic_data_from_file(path, clean_up=False)
        elements, nodes = _serialize_magnetic_region(mr)
        payload = {
            "steps": [1],
            "used_step": 1,
            "meta": {"mode": "snapshot_fallback"},
            "source_mode": "direct_file_parse",
            "bridge_notes": "snapshot_fallback",
            "elements": elements,
            "nodes": nodes,
        }
        return BridgeResult(ok=True, payload=payload)
    except Exception as exc:
        return BridgeResult(
            ok=False,
            payload={},
            error_code="E-PARSE-DIRECT",
            error_message=f"Direct parse failed: {exc}",
        )


def _infer_mot_path(mes_path: pathlib.Path) -> pathlib.Path | None:
    search_roots = [mes_path.parent, mes_path.parent.parent, mes_path.parent.parent.parent]
    for root in search_roots:
        if root is None or not root.exists():
            continue
        cands = sorted(root.glob("*.mot"))
        if cands:
            return cands[0]
    return None


def _magnetic_from_file_with_fallback(
    input_path: pathlib.Path,
    mot_arg: str,
    step_arg: str,
    first_step: int,
    final_step: int,
    all_steps: bool,
) -> BridgeResult:
    direct = _load_magnetic_from_file(input_path, step_arg, all_steps=bool(all_steps))
    if direct.ok:
        return direct

    direct_error = direct.error_message or "direct parse failed"

    mot_path = pathlib.Path(mot_arg).resolve() if mot_arg.lower() != "none" else _infer_mot_path(input_path)
    if mot_path is None or not mot_path.exists():
        return BridgeResult(
            ok=False,
            payload={},
            error_code="E-FALLBACK-NO-MOT",
            error_message="Direct parse failed and .mot path not available for fallback.",
        )

    try:
        import ansys.motorcad.core as pymotorcad
    except Exception as exc:
        return BridgeResult(
            ok=False,
            payload={},
            error_code="E-IMPORT-MOTORCAD",
            error_message=f"Motor-CAD fallback import failed: {exc}",
        )

    out_dir = pathlib.Path(tempfile.mkdtemp(prefix="mes_bridge_"))
    export_txt = out_dir / f"{input_path.stem}_fs{first_step}_fe{final_step}.txt"

    try:
        mc = pymotorcad.MotorCAD(open_new_instance=True)
        mc.set_variable("MessageDisplayState", 2)
        mc.load_from_file(str(mot_path))
        mc.load_fea_result(str(input_path), 1)
        try:
            solver_method = int(mc.get_variable("MagneticSolverMethod"))
        except Exception:
            solver_method = -1
        mag_columns = "RegCode,Bx,By,A,J,Je" if solver_method == 0 else "RegCode,Bx,By,A,J"
        save_ok = False
        for fs, fe in [(int(first_step), int(final_step)), (1, int(final_step)), (1, 1)]:
            try:
                mc.save_fea_data(
                    str(export_txt),
                    fs,
                    fe,
                    mag_columns,
                    "",
                    ",",
                )
                if export_txt.exists():
                    save_ok = True
                    break
            except Exception:
                continue

        if not export_txt.exists():
            return BridgeResult(
                ok=False,
                payload={},
                error_code="E-FALLBACK-NO-EXPORT",
                error_message="Fallback export failed: save_fea_data did not create txt",
            )

        loaded = _load_magnetic_from_file(export_txt, step_arg, all_steps=bool(all_steps))
        if not loaded.ok:
            return loaded

        payload = dict(loaded.payload)
        payload["source_mode"] = "motorcad_export_fallback"
        meta = dict(payload.get("meta", {}) or {})
        meta["fallback_mot_path"] = str(mot_path)
        meta["fallback_export_txt"] = str(export_txt)
        meta["fallback_mag_columns"] = mag_columns
        meta["fallback_solver_method"] = solver_method
        payload["meta"] = meta
        payload["bridge_notes"] = f"direct_parse_failed_then_motorcad_export: {direct_error}"
        return BridgeResult(ok=True, payload=payload)
    except Exception as exc:
        return BridgeResult(
            ok=False,
            payload={},
            error_code="E-FALLBACK-EXEC",
            error_message=str(exc),
        )


def _write_result(out_json: pathlib.Path, result: BridgeResult) -> int:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out: dict[str, Any] = dict(result.payload)
    out["ok"] = result.ok
    if not result.ok:
        out["error_code"] = result.error_code
        out["error_message"] = result.error_message

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    return 0 if result.ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="MATLAB bridge for pyMCAD functions")
    sub = parser.add_subparsers(dest="action", required=True)

    p_mag = sub.add_parser("magnetic_from_file", help="Parse .mes/.txt/.h5 magnetic data")
    p_mag.add_argument("--repo-root", required=True)
    p_mag.add_argument("--input", required=True)
    p_mag.add_argument("--out-json", required=True)
    p_mag.add_argument("--mot-path", default="None")
    p_mag.add_argument("--step", default="None")
    p_mag.add_argument("--first-step", type=int, default=1)
    p_mag.add_argument("--final-step", type=int, default=45)
    p_mag.add_argument("--all-steps", type=int, default=0)

    args = parser.parse_args()

    repo_root = pathlib.Path(args.repo_root).resolve()
    if str(repo_root) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(repo_root))
    emach_root = repo_root / "eMach"
    if str(emach_root) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(emach_root))

    if args.action == "magnetic_from_file":
        result = _magnetic_from_file_with_fallback(
            input_path=pathlib.Path(args.input).resolve(),
            mot_arg=str(args.mot_path),
            step_arg=str(args.step),
            first_step=int(args.first_step),
            final_step=int(args.final_step),
            all_steps=bool(int(args.all_steps)),
        )
        return _write_result(pathlib.Path(args.out_json).resolve(), result)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
