from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from typing import Any

from .dxf_geometry import (  # noqa: F401
    dxf_entitylists_to_regions,
    dxf_to_ir,
    dxf_to_entitylists,
    dxf_to_regions,
    force_black_white,
    get_dxf_layer_summary,
    get_dxf_region_layer_map,
    guess_dxf_regions_from_layer_names,
    ir_to_motorcad_regions,
    infer_region_type_from_layer_name,
    interactive_regions_viewer,
    plot_dxf_black_white,
    plot_dxf_layers_black_white,
    regions_summary_df,
)


def make_limit_df(rows):
    """Helper to build a normalized dataframe for the speed-torque limit tables."""

    import pandas as pd

    df0 = pd.DataFrame(rows)
    return df0.sort_values(["Speed_RPM_min", "Torque_Nm"], ascending=[True, True]).reset_index(drop=True)


def style_axes(ax):
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_linewidth(2.0)
    ax.tick_params(direction="out", width=2.0, length=6, labelsize=24)
    ax.grid(True, which="both", color="0.85", linewidth=0.8)
    ax.set_xlabel("Speed (RPM) - minimum (>=)", fontsize=24)
    ax.set_ylabel("Torque (Nm)", fontsize=24)


def plot_speed_torque_limit_overlay(ax, df_in, temp_label: str, color: str, label_dy: int):
    """Overlay one temperature's limit points on a speed-torque axes."""

    # Connect points with a line (sorted by speed)
    df_line = df_in.sort_values(["Speed_RPM_min", "Torque_Nm"], ascending=[True, True]).reset_index(drop=True)
    (line,) = ax.plot(
        df_line["Speed_RPM_min"],
        df_line["Torque_Nm"],
        color=color,
        linewidth=2.2,
        alpha=0.9,
        zorder=1,
        label=temp_label,
    )

    # Duration -> marker (so duration can live in the legend)
    marker_by_duration = {1000: "o", 500: "v", 250: "P", 150: "X"}

    def label_offset(speed_rpm: float, torque_nm: float) -> tuple[int, int]:
        # Base offset + per-temperature dy to reduce collisions in overlay
        s = int(round(speed_rpm))
        if s == 1000 and abs(torque_nm - 1.191) < 1e-3:
            return (6, -12 + label_dy)
        return (6, 4 + label_dy)

    # Scatter all points + annotate torque@rpm (duration removed)
    for _, row in df_in.iterrows():
        speed = float(row["Speed_RPM_min"])
        torque = float(row["Torque_Nm"])
        dur = int(row["Duration_ms"])
        mk = marker_by_duration.get(dur, "o")
        size = 10 + (float(row["Iq_A_max"]) / float(df_in["Iq_A_max"].max())) * 60

        ax.scatter(
            speed,
            torque,
            s=size,
            marker=mk,
            color=color,
            edgecolor="black",
            linewidth=0.8,
            alpha=0.95,
            zorder=2,
        )

        _dx, _dy = label_offset(speed, torque)
        # Text annotations intentionally left commented out (matching the notebook)

    return line


def read_csv_with_encoding_autodetect(path: str):
    """Read CSV with BOM-based and common Windows fallbacks."""

    import pandas as pd

    p = Path(path)
    raw = p.read_bytes()
    # BOM-based detection first
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        encodings = ["utf-16"]
    elif raw.startswith(b"\xef\xbb\xbf"):
        encodings = ["utf-8-sig"]
    else:
        # Common fallbacks on Windows / mixed files
        encodings = ["utf-8", "cp949", "latin1"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            return pd.read_csv(p, sep=",", engine="python", encoding=enc)
        except Exception as e:
            last_err = e
    raise last_err  # type: ignore[misc]


def _coerce_value_by_dtype(value, dtype: str | None):
    import numpy as np

    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    dtype_s = (dtype or "").strip().lower()

    # Booleans
    if dtype_s in {"bool", "boolean"}:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, np.integer)):
            return bool(int(value))
        if isinstance(value, str):
            s = value.strip().lower()
            if s in {"true", "t", "1", "yes", "y"}:
                return True
            if s in {"false", "f", "0", "no", "n"}:
                return False
        return bool(value)

    # Integers
    if dtype_s in {"int", "integer"}:
        try:
            return int(value)
        except Exception:
            if isinstance(value, str):
                return int(float(value.strip()))
            raise

    # Floats
    if dtype_s in {"float", "double", "real"}:
        return float(value)

    # Fallback: keep as-is (string, enum-like, etc.)
    return value


def df_to_mcad_variables(
    df,
    *,
    name_col: str = "Automation Name",
    value_col: str = "Current Value",
    dtype_col: str = "Data Type",
    only_io: str | None = None,
) -> dict[str, object]:
    """Convert the DXF ActiveX parameters table to a Motor-CAD variables dict."""

    import pandas as pd

    missing = [c for c in (name_col, value_col) if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in df: {missing}. Available: {list(df.columns)}")

    out: dict[str, object] = {}
    for _, row in df.iterrows():
        if only_io is not None and "Input/Output" in df.columns:
            if str(row.get("Input/Output", "")).strip().lower() != only_io.strip().lower():
                continue
        name = str(row.get(name_col, "")).strip()
        if not name or name.lower() == "nan":
            continue
        value = row.get(value_col)
        dtype = row.get(dtype_col) if dtype_col in df.columns else None
        out[name] = _coerce_value_by_dtype(value, None if pd.isna(dtype) else str(dtype))
    return out


def get_mcad_variables(mc, variable_names, *, strict: bool = False, verbose: bool = True):
    """Read multiple Motor-CAD variables into a dict."""

    values: dict[str, object] = {}
    for var in variable_names:
        name = str(var)
        try:
            values[name] = mc.get_variable(name)
            if verbose:
                print(f"[get] {name} = {values[name]}")
        except Exception as e:
            if strict:
                raise
            values[name] = None
            if verbose:
                print(f"[warn] Failed to get {name}: {e}")
    return values


def _to_python_scalar(value):
    """Best-effort conversion to plain Python scalars for Motor-CAD API calls."""

    if value is None:
        return None

    if isinstance(value, Path):
        return str(value)

    # numpy scalar -> python scalar
    try:
        import numpy as np

        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass

    if isinstance(value, (bool, int, float, str)):
        return value

    if hasattr(value, "__fspath__"):
        try:
            return str(Path(value))
        except Exception:
            return str(value)

    if isinstance(value, (list, tuple)):
        return [_to_python_scalar(v) for v in value]

    return value


def set_mcad_variables(mc, variables: dict, *, strict: bool = False, verbose: bool = True):
    """Set multiple Motor-CAD variables from a dict."""

    if not isinstance(variables, dict):
        raise TypeError("variables must be a dict")

    for key, raw_value in variables.items():
        name = str(key)
        value = _to_python_scalar(raw_value)

        if value is None:
            if verbose:
                print(f"[skip] {name}=None")
            continue

        try:
            mc.set_variable(name, value)
            if verbose:
                print(f"[set] {name} = {value}")
        except Exception as e:
            if strict:
                raise
            if verbose:
                print(f"[warn] Failed to set {name}={raw_value!r}: {e}")


def _results_path_motorlab(mc) -> Path:
    """Best-effort to determine the MotorLAB results directory."""

    try:
        rp = mc.get_variable("ResultsPath_MotorLAB")
        if isinstance(rp, str) and rp.strip():
            return Path(rp)
    except Exception:
        pass

    try:
        mot = mc.get_file_name()
        if mot:
            return Path(mot).parent / "Lab"
    except Exception:
        pass

    raise RuntimeError(
        "Could not determine MotorLAB results path. Try setting ResultsPath_MotorLAB or ensure a .mot file is loaded."
    )


def _pick_default_motorlab_mat(lab_dir: Path) -> Path:
    preferred = lab_dir / "MotorLAB_elecdata.mat"
    if preferred.exists():
        return preferred

    mats = sorted(lab_dir.glob("*.mat"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mats:
        raise FileNotFoundError(f"No .mat files found in {lab_dir}")
    return mats[0]


def _make_motorlab_tag(*, Imax_RMS: int, Iinc: int, SpeedMax: int, Tw: int, Tm: int) -> str:
    return f"Imax{Imax_RMS}_Iinc{Iinc}_S{SpeedMax}_Tw{Tw}_Tm{Tm}"


def _safe_token(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s or "MotorCAD"


def _load_motorlab_mat(mat_path: str | Path) -> dict:
    """Load MotorLAB MAT exported by Motor-CAD. Supports v7 and (best-effort) v7.3."""

    import numpy as np

    mat_path = Path(mat_path)
    try:
        from scipy.io import loadmat  # type: ignore

        data = loadmat(mat_path, squeeze_me=True, struct_as_record=False)
        return data
    except Exception as e:
        msg = str(e).lower()
        if "7.3" not in msg and "hdf" not in msg and "unknown mat file type" not in msg:
            raise

        try:
            import h5py  # type: ignore
        except Exception as ie:
            raise RuntimeError(
                "MAT-file looks like v7.3 (HDF5). Install `h5py` (and optionally `scipy`) to read it."
            ) from ie

        out: dict = {}
        with h5py.File(mat_path, "r") as f:
            for k in f.keys():
                v = f[k]
                if hasattr(v, "shape"):
                    out[k] = np.array(v)
        return out


def _get_mat_var(d: dict, name: str):
    if name in d:
        return d[name]
    for k in d.keys():
        if str(k).strip() == name:
            return d[k]
    raise KeyError(
        f"'{name}' not found in MAT. Keys: {sorted([k for k in d.keys() if not str(k).startswith('__')])[:30]} ..."
    )


def _prepare_grid(speed, torque, eff):
    import numpy as np

    speed = np.asarray(speed)
    torque = np.asarray(torque)
    eff = np.asarray(eff)

    speed = np.squeeze(speed)
    torque = np.squeeze(torque)
    eff = np.squeeze(eff)

    if speed.ndim == 1 and torque.ndim == 1 and eff.ndim == 2:
        if eff.shape == (torque.size, speed.size):
            X, Y = np.meshgrid(speed, torque)
            Z = eff
            return X, Y, Z
        if eff.shape == (speed.size, torque.size):
            X, Y = np.meshgrid(speed, torque)
            Z = eff.T
            return X, Y, Z
        raise ValueError(f"Efficiency shape {eff.shape} not compatible with speed({speed.size}) and torque({torque.size}).")

    if eff.ndim == 3:
        if speed.ndim == 1 and torque.ndim == 1:
            if eff.shape[:2] == (torque.size, speed.size):
                X, Y = np.meshgrid(speed, torque)
                Z = eff[:, :, 0]
                return X, Y, Z
            if eff.shape[:2] == (speed.size, torque.size):
                X, Y = np.meshgrid(speed, torque)
                Z = eff[:, :, 0].T
                return X, Y, Z
        if speed.ndim == 2 and torque.ndim == 2 and eff.shape[:2] == speed.shape:
            return speed, torque, eff[:, :, 0]

    if speed.ndim == 2 and torque.ndim == 2 and eff.ndim == 2:
        return speed, torque, eff

    raise ValueError(f"Unsupported shapes: speed{speed.shape}, torque{torque.shape}, eff{eff.shape}")


def _auto_clim_from_data(Z):
    import numpy as np

    finite = np.asarray(Z, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return (0.0, 100.0)

    lo_raw = float(np.nanpercentile(finite, 2))
    hi_raw = float(np.nanpercentile(finite, 98))

    lo_raw = max(0.0, lo_raw)
    hi_raw = min(100.0, hi_raw)

    lo = np.floor(lo_raw * 4) / 4.0
    hi = np.ceil(hi_raw * 4) / 4.0
    if hi <= lo:
        hi = lo + 0.25
    return (lo, hi)


def _nudge_overlapping_texts(ax, fig, texts, *, pad_px: float = 2.0):
    if not texts:
        return
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    except Exception:
        return

    nudges = [
        (14, 0),
        (-14, 0),
        (0, 14),
        (0, -14),
        (22, 0),
        (-22, 0),
        (0, 22),
        (0, -22),
        (14, 14),
        (-14, 14),
        (14, -14),
        (-14, -14),
        (30, 0),
        (-30, 0),
        (0, 30),
        (0, -30),
    ]

    kept_bboxes = []
    for t in texts:
        for attempt in range(len(nudges) + 1):
            try:
                bb = t.get_window_extent(renderer=renderer).expanded(1.05, 1.15)
            except Exception:
                break
            bb = bb.from_extents(bb.x0 - pad_px, bb.y0 - pad_px, bb.x1 + pad_px, bb.y1 + pad_px)

            overlaps = any(bb.overlaps(kbb) for kbb in kept_bboxes)
            if not overlaps:
                kept_bboxes.append(bb)
                break

            if attempt == len(nudges):
                kept_bboxes.append(bb)
                break

            dx_px, dy_px = nudges[attempt]
            x, y = t.get_position()
            x_disp, y_disp = ax.transData.transform((x, y))
            x2, y2 = ax.transData.inverted().transform((x_disp + dx_px, y_disp + dy_px))
            t.set_position((x2, y2))

        try:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
        except Exception:
            pass


def overlay_speed_torque_limit_points_on_effimap(
    ax,
    df_limits,
    *,
    rated_speed_rpm: float | None = 2300,
    rated_torque_nm: float | None = 0.65,
    line_color: str = "black",
    point_facecolor: str = "white",
    point_edgecolor: str = "black",
):
    """Overlay speed-torque limit points (and rated point) on an existing efficiency-map axes."""

    if df_limits is None:
        return

    df_line = df_limits.sort_values(["Speed_RPM_min", "Torque_Nm"], ascending=[True, True]).reset_index(drop=True)
    ax.plot(
        df_line["Speed_RPM_min"],
        df_line["Torque_Nm"],
        color=line_color,
        linewidth=2.4,
        alpha=0.95,
        zorder=40,
    )

    marker_by_duration = {1000: "o", 500: "v", 250: "P", 150: "X"}
    for _, row in df_limits.iterrows():
        speed = float(row["Speed_RPM_min"])
        torque = float(row["Torque_Nm"])
        dur = int(row["Duration_ms"])
        mk = marker_by_duration.get(dur, "o")
        ax.scatter(
            speed,
            torque,
            s=110,
            marker=mk,
            facecolor=point_facecolor,
            edgecolor=point_edgecolor,
            linewidth=1.4,
            alpha=0.98,
            zorder=41,
        )

    if rated_speed_rpm is not None and rated_torque_nm is not None:
        ax.scatter(
            float(rated_speed_rpm),
            float(rated_torque_nm),
            marker="x",
            s=160,
            color="black",
            linewidth=2.4,
            zorder=42,
        )
        ax.annotate(
            "Rated",
            (float(rated_speed_rpm), float(rated_torque_nm)),
            textcoords="offset points",
            xytext=(8, 8),
            fontsize=14,
            color="black",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=0.6),
            zorder=43,
        )


def extract_max_torque_curve_from_effimap(mat_path, *, eff_threshold: float | None = None):
    """Extract max-torque vs speed curve from a MotorLAB efficiency map MAT."""

    import numpy as np

    data = _load_motorlab_mat(mat_path)
    speed = _get_mat_var(data, "Speed")
    torque = _get_mat_var(data, "Shaft_Torque")
    eff = _get_mat_var(data, "Efficiency")

    X, Y, Z = _prepare_grid(speed, torque, eff)
    Z = np.asarray(Z, dtype=float)
    if np.nanmax(Z) <= 1.5:
        Z = 100.0 * Z

    valid = np.isfinite(Z)
    if eff_threshold is not None:
        valid &= Z >= float(eff_threshold)

    if X.ndim != 2 or Y.ndim != 2 or Z.ndim != 2:
        raise ValueError(f"Expected 2D grids after _prepare_grid; got X{X.shape}, Y{Y.shape}, Z{Z.shape}")

    speed_rpm = np.asarray(X[0, :], dtype=float)
    max_torque_nm = np.full(speed_rpm.shape, np.nan, dtype=float)
    for j in range(speed_rpm.size):
        m = valid[:, j]
        if np.any(m):
            max_torque_nm[j] = float(np.nanmax(Y[m, j]))
    return speed_rpm, max_torque_nm


def estimate_base_rpm_from_max_torque(
    speed_rpm,
    max_torque_nm,
    *,
    low_speed_frac: float = 0.2,
    drop_ratio: float = 0.98,
    min_points: int = 5,
) -> float:
    """Estimate base RPM as the knee where max torque starts dropping."""

    import numpy as np

    s = np.asarray(speed_rpm, dtype=float)
    t = np.asarray(max_torque_nm, dtype=float)
    ok = np.isfinite(s) & np.isfinite(t)
    s, t = s[ok], t[ok]
    if s.size < min_points:
        return float("nan")

    order = np.argsort(s)
    s, t = s[order], t[order]

    n_low = int(np.ceil(low_speed_frac * s.size))
    n_low = max(min_points, min(n_low, s.size))
    plateau_torque = float(np.nanmedian(t[:n_low]))
    if not np.isfinite(plateau_torque) or plateau_torque <= 0:
        return float("nan")

    thresh = drop_ratio * plateau_torque
    drop_idx = np.where(t < thresh)[0]
    if drop_idx.size == 0:
        return float(s[-1])
    return float(s[int(drop_idx[0])])


def calc_motorcad_lab_base_point_from_mat(mat_path):
    """Mirror MATLAB `calcMotorCADLabBasePoint.m` base-point logic on a MotorLAB MAT."""

    import numpy as np

    data = _load_motorlab_mat(mat_path)
    V = np.asarray(_get_mat_var(data, "Voltage_Line_Peak"), dtype=float)
    S = np.asarray(_get_mat_var(data, "Speed"), dtype=float)
    T = np.asarray(_get_mat_var(data, "Shaft_Torque"), dtype=float)
    I = np.asarray(_get_mat_var(data, "Stator_Current_Phase_Peak"), dtype=float)

    if V.ndim != 2 or S.ndim != 2 or T.ndim != 2 or I.ndim != 2:
        raise ValueError(
            "Base point calc expects 2D arrays (nSpeed x nIncrements). "
            f"Got V{V.shape}, S{S.shape}, T{T.shape}, I{I.shape}."
        )
    if V.shape != S.shape or V.shape != T.shape or V.shape != I.shape:
        raise ValueError(
            "Base point calc expects same shape for V/S/T/I. "
            f"Got V{V.shape}, S{S.shape}, T{T.shape}, I{I.shape}."
        )

    n_speed, n_inc = V.shape
    last = n_inc - 1
    if n_speed < 3:
        raise ValueError(f"Not enough speed points for base point calc: n_speed={n_speed}")

    V_last = V[:, last]
    S_last = S[:, last]
    T_last = T[:, last]
    I_last = I[:, last]

    max_voltage = float(np.round(np.nanmax(V_last), 0))
    idxs = np.where(np.round(V_last, 0) == max_voltage)[0]
    if idxs.size == 0:
        raise ValueError("Could not locate BaseSpeedRow where Voltage_Line_Peak reaches MaximumVoltage.")
    base_speed_row = int(np.min(idxs))
    if base_speed_row < 1:
        base_speed_row = 1

    denom_v = S_last[0] - S_last[base_speed_row - 1]
    if denom_v == 0:
        raise ZeroDivisionError("VoltageSlope division by zero (Speed values identical).")
    voltage_slope = (V_last[0] - V_last[base_speed_row - 1]) / denom_v
    base_speed_modified = (max_voltage - V_last[0]) / voltage_slope + S_last[0]

    denom_t = S_last[0] - S_last[base_speed_row - 1]
    if denom_t == 0:
        raise ZeroDivisionError("TorqueSlope division by zero (Speed values identical).")
    torque_slope = (T_last[0] - T_last[base_speed_row - 1]) / denom_t
    base_torque_modified = T_last[0] - base_speed_modified * torque_slope
    maximum_power_modified = base_torque_modified * base_speed_modified / 60.0 * 2.0 * np.pi

    max_current = float(np.round(np.nanmax(I_last), 0))
    idxs_i = np.where(np.round(I_last, 0) == max_current)[0]
    if idxs_i.size == 0:
        raise ValueError("Could not locate rows where Stator_Current_Phase_Peak reaches MaximumCurrent.")
    temp_fw_row = int(np.max(idxs_i))

    r1 = min(temp_fw_row + 1, n_speed - 2)
    r2 = min(temp_fw_row + 2, n_speed - 1)
    if r1 == r2:
        r1 = max(0, r2 - 1)

    denom_i = S_last[r1] - S_last[r2]
    if denom_i == 0:
        raise ZeroDivisionError("FluxWeakeningCurrentSlope division by zero (Speed values identical).")
    fw_current_slope = (I_last[r1] - I_last[r2]) / denom_i
    fw_speed_modified = (max_current - I_last[r1]) / fw_current_slope + S_last[r1]

    denom_fw_t = S_last[r1] - S_last[r2]
    if denom_fw_t == 0:
        raise ZeroDivisionError("FluxWeakeningTorqueSlope division by zero (Speed values identical).")
    fw_torque_slope = (T_last[r1] - T_last[r2]) / denom_fw_t
    fw_torque_modified = fw_torque_slope * (fw_speed_modified - S_last[r1]) + T_last[r1]

    if T_last[-1] > 0:
        maximum_speed = float(np.nanmax(S_last))
    else:
        z = np.where(np.round(T_last, 0) <= 0)[0]
        if z.size == 0:
            maximum_speed = float(np.nanmax(S_last))
        else:
            k = int(np.min(z))
            maximum_speed = float(S_last[max(0, k - 1)])

    return {
        "MaximumPower_modified": float(maximum_power_modified),
        "BaseTorque_modified": float(base_torque_modified),
        "BaseSpeed_modified": float(base_speed_modified),
        "FluxWeakeningTorque_modified": float(fw_torque_modified),
        "FluxWeakeningSpeed_modified": float(fw_speed_modified),
        "MaximumSpeed": float(maximum_speed),
    }


def extract_max_torque_and_base_rpm(
    mat_path,
    *,
    eff_threshold: float | None = None,
    low_speed_frac: float = 0.2,
    drop_ratio: float = 0.98,
):
    import pandas as pd

    speed_rpm, max_torque_nm = extract_max_torque_curve_from_effimap(mat_path, eff_threshold=eff_threshold)
    base_rpm = estimate_base_rpm_from_max_torque(
        speed_rpm, max_torque_nm, low_speed_frac=low_speed_frac, drop_ratio=drop_ratio
    )
    df_curve = pd.DataFrame({"Speed_RPM": speed_rpm, "MaxTorque_Nm": max_torque_nm})
    return {"speed_rpm": speed_rpm, "max_torque_nm": max_torque_nm, "base_rpm": base_rpm, "df": df_curve}


def _motorlab_pick_angle_variable(data: dict, target_shape: tuple[int, int]):
    """Best-effort auto-detect of phase-advance/current-angle variable in MotorLAB MAT."""

    import numpy as np

    n_speed, n_inc = target_shape
    keys = [k for k in data.keys() if not str(k).startswith("__")]
    key_lut = {str(k).lower(): str(k) for k in keys}

    patterns = [
        "phase_advance",
        "phaseadvance",
        "phase adv",
        "current_phase_angle",
        "currentphaseangle",
        "current angle",
        "electrical_angle",
        "elec_angle",
        "beta",
        "beta_deg",
        "phaseangle",
        "phase_angle",
        "gamma",
    ]

    def score_key(k_lower: str) -> int:
        s = 0
        for i, pat in enumerate(patterns):
            if pat.replace(" ", "") in k_lower.replace(" ", ""):
                s += (len(patterns) - i) * 10
        if "speed" in k_lower or "torque" in k_lower or "voltage" in k_lower or "eff" in k_lower:
            s -= 30
        return s

    candidates: list[tuple[int, str]] = []
    for kl, orig in key_lut.items():
        sc = score_key(kl)
        if sc <= 0:
            continue
        try:
            arr = np.asarray(data[orig])
        except Exception:
            continue
        if arr.dtype.kind not in ("i", "u", "f"):
            continue
        candidates.append((sc, orig))

    candidates.sort(key=lambda x: x[0], reverse=True)

    def to_deg(a: Any):
        a = np.asarray(a, dtype=float)
        finite = a[np.isfinite(a)]
        if finite.size == 0:
            return a
        m = float(np.nanmax(np.abs(finite)))
        if m <= (2.0 * np.pi + 0.2):
            return a * (180.0 / np.pi)
        return a

    for _, name in candidates:
        try:
            a = np.asarray(data[name], dtype=float)
        except Exception:
            continue
        a = np.squeeze(a)
        if a.ndim == 2 and a.shape == target_shape:
            return to_deg(a), name
        if a.ndim == 1 and a.size == n_inc:
            a2 = np.tile(a.reshape(1, -1), (n_speed, 1))
            return to_deg(a2), name
        if a.ndim == 1 and a.size == n_speed:
            a2 = np.tile(a.reshape(-1, 1), (1, n_inc))
            return to_deg(a2), name

    return None, None


def calc_motorcad_lab_base_point_spm_phase0_from_mat(
    mat_path,
    *,
    phase_advance_value_deg: float = 0.0,
    tol_deg: float = 0.5,
    increment_index: int | None = None,
):
    """SPM assumption: base point == max RPM achievable at phase advance ~= 0 deg."""

    import numpy as np

    data = _load_motorlab_mat(mat_path)
    S = np.asarray(_get_mat_var(data, "Speed"), dtype=float)
    T = np.asarray(_get_mat_var(data, "Shaft_Torque"), dtype=float)

    if S.ndim != 2 or T.ndim != 2 or S.shape != T.shape:
        raise ValueError(f"Expected Speed/Shaft_Torque as same-shaped 2D arrays; got Speed{S.shape}, Torque{T.shape}.")

    n_speed, n_inc = S.shape

    angle, angle_name = _motorlab_pick_angle_variable(data, (n_speed, n_inc))

    if angle is not None and angle_name is not None:
        mask = np.isfinite(S) & np.isfinite(T) & np.isfinite(angle)
        mask &= np.abs(angle - float(phase_advance_value_deg)) <= float(tol_deg)
        mask &= T > 0
        if not np.any(mask):
            raise ValueError(
                "No points found with phase advance near requested value. "
                + f"Requested {phase_advance_value_deg}±{tol_deg} deg using '{angle_name}'."
            )
        s_masked = np.where(mask, S, -np.inf)
        flat_idx = int(np.nanargmax(s_masked))
        i = flat_idx // n_inc
        j = flat_idx % n_inc
        return {
            "BaseSpeed": float(S[i, j]),
            "BaseTorque": float(T[i, j]),
            "Row": int(i),
            "Col": int(j),
            "AngleName": str(angle_name),
        }

    j0 = 0 if increment_index is None else int(increment_index)
    if not (0 <= j0 < n_inc):
        raise ValueError(f"increment_index out of range: {j0} (n_inc={n_inc})")

    s_col = S[:, j0]
    t_col = T[:, j0]
    ok = np.isfinite(s_col) & np.isfinite(t_col) & (t_col > 0)
    if not np.any(ok):
        raise ValueError(f"No positive-torque points found in increment column {j0}.")

    i = int(np.nanargmax(np.where(ok, s_col, -np.inf)))
    return {"BaseSpeed": float(s_col[i]), "BaseTorque": float(t_col[i]), "Row": int(i), "Col": int(j0), "AngleName": None}


def debug_motorlab_angle_keys(mat_path, *, max_show: int = 40):
    import numpy as np

    data = _load_motorlab_mat(mat_path)
    keys = sorted([k for k in data.keys() if not str(k).startswith("__")], key=lambda x: str(x).lower())

    hits = []
    for k in keys:
        kl = str(k).lower()
        if any(p in kl.replace(" ", "") for p in ["phase", "advance", "beta", "angle", "gamma"]):
            try:
                arr = np.asarray(data[k])
                shp = arr.shape
            except Exception:
                shp = None
            hits.append((str(k), shp))

    print(f"Total keys: {len(keys)}")
    print("Angle-like keys (name, shape):")
    for name, shp in hits[:max_show]:
        print(" -", name, shp)
    if len(hits) > max_show:
        print(f"... ({len(hits)-max_show} more)")


def plotNrunMCADLab(
    mc,
    *,
    run_calc: bool = True,
    plot: bool = True,
    colorbar_top: bool = True,
    clim: tuple[float, float] | None = None,
    y_lim: tuple[float, float] | None = None,
    y_ticks: list[float] | None = None,
    copy_to_tagged_name: bool = True,
):
    """Run MotorLAB e-magnetic calc, choose MAT file, optionally copy/rename, and plot effimap.

    Returns: (mat_path: Path, fig, ax)
    """

    import numpy as np
    import matplotlib.pyplot as plt

    lab_dir = _results_path_motorlab(mc)

    if run_calc:
        mc.calculate_magnetic_lab()

    src_mat = _pick_default_motorlab_mat(lab_dir)
    out_mat = src_mat

    if copy_to_tagged_name:
        try:
            Imax_RMS = int(round(float(mc.get_variable("Imax_RMS_MotorLAB"))))
        except Exception:
            Imax_RMS = int(round(float(mc.get_variable("Imax_MotorLAB"))))
        Iinc = int(round(float(mc.get_variable("Iinc_MotorLAB"))))
        SpeedMax = int(round(float(mc.get_variable("SpeedMax_MotorLAB"))))
        Tw = int(round(float(mc.get_variable("TwindingCalc_MotorLAB"))))
        Tm = int(round(float(mc.get_variable("TmagnetCalc_MotorLAB"))))
        tag = _make_motorlab_tag(Imax_RMS=Imax_RMS, Iinc=Iinc, SpeedMax=SpeedMax, Tw=Tw, Tm=Tm)
        out_mat = src_mat.with_name(f"{src_mat.stem}_{_safe_token(tag)}{src_mat.suffix}")
        if out_mat.resolve() != src_mat.resolve():
            shutil.copy2(src_mat, out_mat)

    if not plot:
        return out_mat, None, None

    data = _load_motorlab_mat(out_mat)
    speed = _get_mat_var(data, "Speed")
    torque = _get_mat_var(data, "Shaft_Torque")
    eff = _get_mat_var(data, "Efficiency")

    X, Y, Z = _prepare_grid(speed, torque, eff)
    Z = np.asarray(Z, dtype=float)
    if np.nanmax(Z) <= 1.5:
        Z = 100.0 * Z

    if clim is None:
        clim = _auto_clim_from_data(Z)

    fig, ax = plt.subplots(figsize=(12.8, 6.3))

    lo, hi = float(clim[0]), float(clim[1])
    levels = np.linspace(lo, hi, 21)
    cf = ax.contourf(X, Y, Z, levels=levels, cmap="viridis", vmin=lo, vmax=hi)

    # Contour lines and labels
    cs = ax.contour(X, Y, Z, levels=levels[::2], colors="k", linewidths=0.4, alpha=0.5)
    texts = ax.clabel(cs, inline=True, fontsize=10, fmt="%.0f")
    _nudge_overlapping_texts(ax, fig, texts)

    ax.set_xlabel("Speed [rpm]")
    ax.set_ylabel("Torque [Nm]")

    if y_lim is not None:
        ax.set_ylim(float(y_lim[0]), float(y_lim[1]))
    if y_ticks is not None:
        ax.set_yticks([float(v) for v in y_ticks])

    # Colorbar
    if colorbar_top:
        try:
            cbar = fig.colorbar(cf, ax=ax, orientation="horizontal", location="top", pad=0.08)
        except Exception:
            cbar = fig.colorbar(cf, ax=ax, orientation="horizontal", pad=0.08)
    else:
        cbar = fig.colorbar(cf, ax=ax)
    cbar.set_label("Efficiency [%]")

    ax.grid(True, which="both", color="0.85", linewidth=0.8)
    ax.set_title("Efficiency map")

    fig.tight_layout()

    return out_mat, fig, ax


def _style_waveform_axes(ax, *, labelsize: int = 22):
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_linewidth(2.0)
    ax.tick_params(direction="out", width=2.0, length=6, labelsize=int(labelsize))
    ax.grid(True, which="both", color="0.85", linewidth=0.8)


def get_back_emf_metrics(mc) -> dict[str, float]:
    """Read common no-load scalar metrics (best-effort).

    Keys are included only if Motor-CAD returns them.
    """

    out: dict[str, float] = {}

    def _try(name: str, key: str | None = None):
        k = name if key is None else key
        try:
            out[k] = float(mc.get_variable(name))
        except Exception:
            pass

    _try("ShaftTorque")
    _try("PeakLineLineVoltage")
    _try("PeakBackEMFLine")
    _try("RMSBackEMFLine")
    _try("PeakBackEMFPhase")
    _try("THDBackEMFLine")
    return out


def plot_back_emf_waveforms(
    mc,
    *,
    figsize: tuple[float, float] = (10, 6),
    linewidth: float = 2.2,
    title: str = "Back-EMF Waveforms",
    xlabel: str = "Rotor Position",
    ylabel: str = "Back-EMF",
    xtick_step_deg: float = 60.0,
    font_family: str | None = "Times New Roman",
):
    """Plot Back-EMF phase waveforms (no-load style)."""

    import numpy as np
    import matplotlib.pyplot as plt

    if font_family:
        plt.rcParams["font.family"] = str(font_family)
        plt.rcParams["svg.fonttype"] = "none"

    rotor_position, emf1 = mc.get_magnetic_graph("BackEMFPh1")
    _rp2, emf2 = mc.get_magnetic_graph("BackEMFPh2")
    _rp3, emf3 = mc.get_magnetic_graph("BackEMFPh3")

    fig, ax = plt.subplots(figsize=tuple(figsize))
    ax.plot(rotor_position, emf1, label="Phase 1", linewidth=float(linewidth))
    ax.plot(rotor_position, emf2, label="Phase 2", linewidth=float(linewidth))
    ax.plot(rotor_position, emf3, label="Phase 3", linewidth=float(linewidth))

    ax.set_title(str(title), fontsize=26, pad=10)
    ax.set_xlabel(str(xlabel), fontsize=24)
    ax.set_ylabel(str(ylabel), fontsize=24)

    x = np.asarray(rotor_position, dtype=float)
    if x.size:
        x_lo = float(np.nanmin(x))
        x_hi = float(np.nanmax(x))
        if float(xtick_step_deg) > 0:
            tick_start = float(xtick_step_deg) * np.floor(x_lo / float(xtick_step_deg))
            tick_end = float(xtick_step_deg) * np.ceil(x_hi / float(xtick_step_deg))
            ax.set_xticks(np.arange(tick_start, tick_end + 0.1, float(xtick_step_deg)))
        ax.set_xlim(x_lo, x_hi)

    _style_waveform_axes(ax, labelsize=22)
    ax.legend(loc="upper right", fontsize=18, frameon=True, facecolor="white", edgecolor="black")
    fig.tight_layout()
    return fig, ax


def plot_cogging_torque_waveform(
    mc,
    *,
    figsize: tuple[float, float] = (10, 6),
    linewidth: float = 2.2,
    title: str = "Cogging Torque",
    xlabel: str = "Rotor Position (Mech Angle, deg)",
    ylabel: str = "Torque (Nm)",
):
    """Plot Cogging torque waveform (no-load)."""

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    x, y = mc.get_magnetic_graph("CoggingTorqueVW")

    fig, ax = plt.subplots(figsize=tuple(figsize))
    ax.plot(np.asarray(x, dtype=float), np.asarray(y, dtype=float), linewidth=float(linewidth), color="black")
    ax.set_title(str(title), fontsize=26, pad=10)
    ax.set_xlabel(str(xlabel), fontsize=24)
    ax.set_ylabel(str(ylabel), fontsize=24)

    ax.xaxis.set_major_locator(MaxNLocator(nbins=7))
    try:
        ax.set_xlim(float(np.nanmin(x)), float(np.nanmax(x)))
    except Exception:
        pass

    _style_waveform_axes(ax, labelsize=22)
    fig.tight_layout()
    return fig, ax


def plot_torque_vw_waveform(
    mc,
    *,
    figsize: tuple[float, float] = (10, 6),
    linewidth: float = 2.2,
    title: str = "Electromagnetic Torque",
    xlabel: str = "Rotor Position",
    ylabel: str = "Electromagnetic Torque [Nm]",
):
    """Plot TorqueVW waveform (load)."""

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    x, y = mc.get_magnetic_graph("TorqueVW")

    fig, ax = plt.subplots(figsize=tuple(figsize))
    ax.plot(np.asarray(x, dtype=float), np.asarray(y, dtype=float), linewidth=float(linewidth), color="black")
    ax.set_title(str(title), fontsize=26, pad=10)
    ax.set_xlabel(str(xlabel), fontsize=24)
    ax.set_ylabel(str(ylabel), fontsize=24)

    ax.xaxis.set_major_locator(MaxNLocator(nbins=7))
    try:
        ax.set_xlim(float(np.nanmin(x)), float(np.nanmax(x)))
    except Exception:
        pass

    _style_waveform_axes(ax, labelsize=22)
    fig.tight_layout()
    return fig, ax


def list_graph_names_from_ini(
    ini_path: str | Path,
    *,
    data_type: str | None = None,
    contains: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    """List available graph names from a Motor-CAD testGraph.ini.

    This treats the INI as a static catalog (name + DataType). Actual waveform data
    should be fetched from Motor-CAD through its API.

    Parameters
    ----------
    ini_path:
        Path to testGraph.ini (or similar).
    data_type:
        Optional filter. Common values: 'MagneticDataSource', 'FEAPathDataSource'.
    contains:
        Optional substring filters (matched against section name and Legend).
    """

    from .graph_catalog import list_graph_names

    return list_graph_names(ini_path, data_type=data_type, contains=contains)


def get_graph_type_map_from_ini(ini_path: str | Path) -> dict[str, str]:
    """Return mapping: graph name -> DataType from a baseline testGraph.ini.

    This is useful when your testGraph.ini is not regenerated each solve. Use it
    only to decide which API to call (magnetic vs FEA path).
    """

    from .graph_catalog import graph_type_map

    return graph_type_map(ini_path)


def get_graph_xy_from_ini(mc, ini_path: str | Path, graph_name: str):
    """Get graph (x,y) using a testGraph.ini entry.

    - MagneticDataSource -> mc.get_magnetic_graph(...)
    - FEAPathDataSource -> mc.get_fea_graph(...)
    """

    from .graph_catalog import get_graph_xy

    return get_graph_xy(mc, graph_name, ini_path=ini_path)


def plot_graph_waveform(
    mc,
    graph_name: str,
    *,
    ini_path: str | Path | None = None,
    data_type: str | None = None,
    figsize: tuple[float, float] = (10, 6),
    linewidth: float = 2.2,
    title: str | None = None,
    xlabel: str = "X",
    ylabel: str = "Y",
):
    """Generic waveform plot for one Motor-CAD graph.

    If ini_path is provided, the DataType is inferred and the correct API is used.
    Otherwise, defaults to magnetic graphs.
    """

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    from .graph_catalog import get_graph_xy

    x, y = get_graph_xy(mc, graph_name, data_type=data_type, ini_path=ini_path)

    fig, ax = plt.subplots(figsize=tuple(figsize))
    ax.plot(np.asarray(x, dtype=float), np.asarray(y, dtype=float), linewidth=float(linewidth), color="black")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=7))

    if title is None:
        title = str(graph_name)

    ax.set_title(str(title), fontsize=26, pad=10)
    ax.set_xlabel(str(xlabel), fontsize=24)
    ax.set_ylabel(str(ylabel), fontsize=24)

    try:
        ax.set_xlim(float(np.nanmin(x)), float(np.nanmax(x)))
    except Exception:
        pass

    _style_waveform_axes(ax, labelsize=22)
    fig.tight_layout()
    return fig, ax


def plot_multi_graph_waveforms(
    mc,
    graph_names: list[str] | tuple[str, ...],
    *,
    ini_path: str | Path | None = None,
    data_type: str | None = None,
    figsize: tuple[float, float] = (10, 6),
    linewidth: float = 2.2,
    title: str | None = None,
    xlabel: str = "X",
    ylabel: str = "Y",
    labels: list[str] | tuple[str, ...] | None = None,
):
    """Plot multiple graphs on the same axes (e.g., 3-phase waveforms)."""

    import numpy as np
    import matplotlib.pyplot as plt

    from .graph_catalog import get_graph_xy

    names = list(graph_names)
    if not names:
        raise ValueError("graph_names is empty")

    if labels is None:
        labels_use = names
    else:
        labels_use = list(labels)
        if len(labels_use) != len(names):
            raise ValueError("labels must match length of graph_names")

    fig, ax = plt.subplots(figsize=tuple(figsize))
    for name, lab in zip(names, labels_use):
        x, y = get_graph_xy(mc, name, data_type=data_type, ini_path=ini_path)
        ax.plot(np.asarray(x, dtype=float), np.asarray(y, dtype=float), linewidth=float(linewidth), label=str(lab))

    if title is None:
        title = "Waveforms"
    ax.set_title(str(title), fontsize=26, pad=10)
    ax.set_xlabel(str(xlabel), fontsize=24)
    ax.set_ylabel(str(ylabel), fontsize=24)
    _style_waveform_axes(ax, labelsize=22)
    ax.legend(loc="best", fontsize=18, frameon=True, facecolor="white", edgecolor="black")
    fig.tight_layout()
    return fig, ax


def plot_currents_waveforms(
    mc,
    *,
    ini_path: str | Path,
    graph_names: list[str] | tuple[str, ...] | None = None,
):
    """Plot current waveforms.

    If graph_names is None, this will try to auto-detect candidates from testGraph.ini
    by searching for 'current'.
    """

    if graph_names is None:
        candidates = list_graph_names_from_ini(ini_path, data_type="MagneticDataSource", contains=["current"])
        if not candidates:
            raise ValueError("No current-like graphs found in ini. Try contains=['CurrentPh'] or inspect the ini.")
        graph_names = candidates[:3]

    return plot_multi_graph_waveforms(
        mc,
        list(graph_names),
        ini_path=ini_path,
        title="Currents",
        xlabel="Rotor Position",
        ylabel="Current",
    )


def plot_terminal_voltage_waveform(
    mc,
    *,
    ini_path: str | Path,
    graph_name: str | None = None,
):
    """Plot a terminal voltage waveform (single trace).

    If graph_name is None, tries to find a candidate containing both 'terminal' and 'voltage'.
    """

    if graph_name is None:
        candidates = list_graph_names_from_ini(
            ini_path,
            data_type="MagneticDataSource",
            contains=["terminal", "voltage"],
        )
        if not candidates:
            raise ValueError("No terminal-voltage-like graphs found in ini. Please pass graph_name explicitly.")
        graph_name = candidates[0]

    return plot_graph_waveform(
        mc,
        str(graph_name),
        ini_path=ini_path,
        title="Terminal Voltage",
        xlabel="Rotor Position",
        ylabel="Voltage",
    )


def plot_flux_linkage_waveforms(
    mc,
    *,
    ini_path: str | Path,
    graph_names: list[str] | tuple[str, ...] | None = None,
):
    """Plot flux linkage waveforms.

    If graph_names is None, tries to auto-detect candidates from testGraph.ini by
    searching for 'flux' and 'link'.
    """

    if graph_names is None:
        candidates = list_graph_names_from_ini(
            ini_path,
            data_type="MagneticDataSource",
            contains=["flux", "link"],
        )
        if not candidates:
            # fallback for common naming
            candidates = list_graph_names_from_ini(ini_path, data_type="MagneticDataSource", contains=["psi"])
        if not candidates:
            raise ValueError("No flux-linkage-like graphs found in ini. Please pass graph_names explicitly.")
        graph_names = candidates[:3]

    return plot_multi_graph_waveforms(
        mc,
        list(graph_names),
        ini_path=ini_path,
        title="Flux Linkage",
        xlabel="Rotor Position",
        ylabel="Flux Linkage",
    )


def plot_fea_path_graph_waveform(
    mc,
    *,
    ini_path: str | Path,
    graph_name: str,
    ylabel: str = "Value",
):
    """Plot an FEAPathDataSource graph using mc.get_fea_graph()."""

    return plot_graph_waveform(
        mc,
        graph_name,
        ini_path=ini_path,
        data_type="FEAPathDataSource",
        title=str(graph_name),
        xlabel="Position",
        ylabel=str(ylabel),
    )


__all__ = [
    "make_limit_df",
    "style_axes",
    "plot_speed_torque_limit_overlay",
    "read_csv_with_encoding_autodetect",
    "df_to_mcad_variables",
    "get_mcad_variables",
    "set_mcad_variables",
    "plot_dxf_black_white",
    "get_dxf_layer_summary",
    "guess_dxf_regions_from_layer_names",
    "get_dxf_region_layer_map",
    "plot_dxf_layers_black_white",
    "dxf_to_entitylists",
    "dxf_entitylists_to_regions",
    "infer_region_type_from_layer_name",
    "dxf_to_regions",
    "regions_summary_df",
    "interactive_regions_viewer",
    "force_black_white",
    "plotNrunMCADLab",
    "get_back_emf_metrics",
    "plot_back_emf_waveforms",
    "plot_cogging_torque_waveform",
    "plot_torque_vw_waveform",
    "list_graph_names_from_ini",
    "get_graph_type_map_from_ini",
    "get_graph_xy_from_ini",
    "plot_graph_waveform",
    "plot_multi_graph_waveforms",
    "plot_currents_waveforms",
    "plot_terminal_voltage_waveform",
    "plot_flux_linkage_waveforms",
    "plot_fea_path_graph_waveform",
    "overlay_speed_torque_limit_points_on_effimap",
    "extract_max_torque_curve_from_effimap",
    "estimate_base_rpm_from_max_torque",
    "extract_max_torque_and_base_rpm",
    "calc_motorcad_lab_base_point_from_mat",
    "calc_motorcad_lab_base_point_spm_phase0_from_mat",
    "debug_motorlab_angle_keys",
]
