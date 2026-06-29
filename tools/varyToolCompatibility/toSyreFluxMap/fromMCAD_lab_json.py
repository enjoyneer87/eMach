"""
fromMCAD_lab_json.py
Motor-CAD Lab (flux linkage) + JSON AC loss (Hybrid FEA) → SyRE FluxMap_dq

Sources:
  - Flux linkage : Motor-CAD Lab model via pymotorcad (PsiDModel_Lab / PsiQModel_Lab)
  - AC loss      : JEET_ACLoss_*_Map_Summary.json  (proximity_model == 1, Hybrid)

Output (.mat):
  FluxMap_dq  : SyRE MMM-compatible struct
  raw         : both source grids preserved before interpolation
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from scipy.interpolate import griddata
from scipy.io import savemat


# ─────────────────────────────────────────────────────────────────────────────
# 1. Raw extraction helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_mcad_array_string(s: str) -> np.ndarray:
    """Parse Motor-CAD colon-separated or newline-separated numeric string."""
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(s))
    return np.array([float(v) for v in nums])


def extract_lab_psi(mcad, verbose: bool = True) -> dict:
    """
    Extract flux linkage saturation map from a running Motor-CAD Lab instance.

    Parameters
    ----------
    mcad : pymotorcad.MotorCAD
        Connected Motor-CAD instance (Lab calc already done).
    verbose : bool
        Print grid info.

    Returns
    -------
    dict with keys:
        Is_peak   [nI]        peak stator current (A)
        gamma     [nG]        phase advance angle (deg)
        PsiD      [nI, nG]    d-axis flux linkage (Wb)  — rows=current, cols=angle
        PsiQ      [nI, nG]    q-axis flux linkage (Wb)
        Id_peak   [nI, nG]    d-axis current, peak (A)
        Iq_peak   [nI, nG]    q-axis current, peak (A)
    """
    mcad.set_motorlab_context()

    nI = int(mcad.get_variable("ModelBuildPoints_Current_Lab"))
    nG = int(mcad.get_variable("ModelBuildPoints_Gamma_Lab"))
    I_max = float(mcad.get_variable("PeakCurrentAmplitude"))

    # Current and gamma vectors  (Motor-CAD default: linear from 0)
    Is_vec    = np.linspace(0.0, I_max, nI)       # A peak
    gamma_vec = np.linspace(0.0, 90.0, nG)        # deg  (phase advance)

    raw_psiD = _parse_mcad_array_string(mcad.get_variable("PsiDModel_Lab"))
    raw_psiQ = _parse_mcad_array_string(mcad.get_variable("PsiQModel_Lab"))

    PsiD = raw_psiD.reshape(nI, nG)   # [nI, nG]  Wb
    PsiQ = raw_psiQ.reshape(nI, nG)

    # (Is, gamma) → (Id, Iq) peak, using pkgamma2dq convention:
    #   gamma is Motor-CAD Phase Advance (q-axis reference)
    #   id = Is * cos(gamma + 90°),  iq = Is * sin(gamma + 90°)
    GAMMA, IS = np.meshgrid(gamma_vec, Is_vec)          # both [nI, nG]
    rad = np.deg2rad(GAMMA + 90.0)
    Id_peak = IS * np.cos(rad)
    Iq_peak = IS * np.sin(rad)

    mcad.show_magnetic_context()   # restore emag context

    if verbose:
        print(f"Lab grid  : {nI} currents × {nG} angles")
        print(f"Is range  : {Is_vec[0]:.1f} – {Is_vec[-1]:.1f} A peak")
        print(f"PsiD range: {PsiD.min():.4f} – {PsiD.max():.4f} Wb")
        print(f"PsiQ range: {PsiQ.min():.4f} – {PsiQ.max():.4f} Wb")

    res = {
        "Is_peak": Is_vec,
        "gamma":   gamma_vec,
        "PsiD":    PsiD,
        "PsiQ":    PsiQ,
        "Id_peak": Id_peak,
        "Iq_peak": Iq_peak,
        "has_losses": False
    }

    try:
        n0 = float(mcad.get_variable("FEALossMap_RefSpeed_Lab"))
        backIronHy = _parse_mcad_array_string(mcad.get_variable("FeLossBackIronHy_MotorLAB"))
        toothHy = _parse_mcad_array_string(mcad.get_variable("FeLossToothHy_MotorLAB"))
        backIronEd = _parse_mcad_array_string(mcad.get_variable("FeLossBackIronEd_MotorLAB"))
        toothEd = _parse_mcad_array_string(mcad.get_variable("FeLossToothEd_MotorLAB"))
        rotorHy = _parse_mcad_array_string(mcad.get_variable("FeLossRotorHy_MotorLAB"))
        rotorPoleHy = _parse_mcad_array_string(mcad.get_variable("FeLossRotorPoleHy_MotorLAB"))
        rotorEd = _parse_mcad_array_string(mcad.get_variable("FeLossRotorEd_MotorLAB"))
        rotorPoleEd = _parse_mcad_array_string(mcad.get_variable("FeLossRotorPoleEd_MotorLAB"))
        magLoss = _parse_mcad_array_string(mcad.get_variable("MagLossArray_MotorLAB"))
        
        Pfes_h_flat = backIronHy + toothHy
        Pfes_c_flat = backIronEd + toothEd
        Pfer_h_flat = rotorHy + rotorPoleHy
        Pfer_c_flat = rotorEd + rotorPoleEd
        Ppm_flat = magLoss
        
        res["FEALossMap_RefSpeed_Lab"] = n0
        res["Pfes_h"] = Pfes_h_flat.reshape(nI, nG)
        res["Pfes_c"] = Pfes_c_flat.reshape(nI, nG)
        res["Pfer_h"] = Pfer_h_flat.reshape(nI, nG)
        res["Pfer_c"] = Pfer_c_flat.reshape(nI, nG)
        res["Ppm"] = Ppm_flat.reshape(nI, nG)
        res["has_losses"] = True
    except Exception as e:
        # Ignore loss extraction failures gracefully
        pass

    return res


def load_acloss_json(json_path: str | Path, proximity_model: int = 1) -> dict:
    """
    Load AC loss records from JEET_ACLoss_*_Map_Summary.json.

    Parameters
    ----------
    json_path       : path to JSON summary file
    proximity_model : 1 = Hybrid FEA (default), 3 = FullFEA

    Returns
    -------
    dict with keys:
        Is_peak       [N]   peak stator current (A)
        gamma         [N]   phase advance (deg)
        speed         [N]   speed (rpm)
        Pac_total_kW  [N]
        Pac_prox_kW   [N]
        Pac_skin_kW   [N]
        speed_vec     [nS]  unique sorted speeds
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("records", data) if isinstance(data, dict) else data
    sel = [r for r in records if r.get("proximity_model") == proximity_model
           and "hybrid_total_kW" in r]

    if not sel:
        raise ValueError(f"No records with proximity_model={proximity_model} found in {json_path}")

    Is_peak      = np.array([r["current"] for r in sel], dtype=float)
    gamma        = np.array([r["phase"]   for r in sel], dtype=float)
    speed        = np.array([r["speed"]   for r in sel], dtype=float)
    Pac_total_kW = np.array([r["hybrid_total_kW"] for r in sel], dtype=float)
    Pac_prox_kW  = np.array([r["hybrid_prox_kW"]  for r in sel], dtype=float)
    Pac_skin_kW  = np.array([r["hybrid_skin_kW"]  for r in sel], dtype=float)
    speed_vec    = np.sort(np.unique(speed))

    print(f"AC loss records: {len(sel)}  "
          f"({len(np.unique(Is_peak))} currents × "
          f"{len(np.unique(gamma))} angles × "
          f"{len(speed_vec)} speeds)")

    return {
        "Is_peak":      Is_peak,
        "gamma":        gamma,
        "speed":        speed,
        "Pac_total_kW": Pac_total_kW,
        "Pac_prox_kW":  Pac_prox_kW,
        "Pac_skin_kW":  Pac_skin_kW,
        "speed_vec":    speed_vec,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Grid builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_common_grid(raw_psi: dict) -> tuple[np.ndarray, np.ndarray]:
    """
    Build regular (Id, Iq) RMS meshgrid from Lab flux linkage grid.
    Grid axes are taken from the Lab model (richer resolution source).
    Peak → RMS : /√2
    """
    Id_rms_flat = (raw_psi["Id_peak"] / np.sqrt(2)).ravel()
    Iq_rms_flat = (raw_psi["Iq_peak"] / np.sqrt(2)).ravel()

    id_vec = np.sort(np.unique(np.round(Id_rms_flat, 4)))
    iq_vec = np.sort(np.unique(np.round(Iq_rms_flat, 4)))

    Id, Iq = np.meshgrid(id_vec, iq_vec)   # [nIq, nId]
    return Id, Iq


def _interp2d(src_x, src_y, src_z, tgt_x, tgt_y, method="cubic"):
    """Scatter → regular grid interpolation, NaN outside convex hull."""
    pts  = np.column_stack([src_x.ravel(), src_y.ravel()])
    vals = src_z.ravel()
    return griddata(pts, vals, (tgt_x, tgt_y), method=method)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Main combiner
# ─────────────────────────────────────────────────────────────────────────────

def build_syre_fluxmap(raw_psi: dict, raw_ac: dict, p: int) -> dict:
    """
    Combine flux linkage and AC loss onto a common (Id, Iq) RMS meshgrid
    and assemble SyRE FluxMap_dq struct.

    Parameters
    ----------
    raw_psi : output of extract_lab_psi()
    raw_ac  : output of load_acloss_json()
    p       : number of pole pairs

    Returns
    -------
    dict with:
        FluxMap_dq  : SyRE-compatible struct (dict)
        raw         : { psi: raw_psi, acloss: raw_ac }  (preserved originals)
    """
    Id, Iq = _build_common_grid(raw_psi)

    # ── flux linkage ──────────────────────────────────────────────────────────
    Id_rms_psi = (raw_psi["Id_peak"] / np.sqrt(2)).ravel()
    Iq_rms_psi = (raw_psi["Iq_peak"] / np.sqrt(2)).ravel()

    Fd = _interp2d(Id_rms_psi, Iq_rms_psi, raw_psi["PsiD"].ravel(), Id, Iq)
    Fq = _interp2d(Id_rms_psi, Iq_rms_psi, raw_psi["PsiQ"].ravel(), Id, Iq)

    T    = 1.5 * p * (Fd * Iq - Fq * Id)
    dT   = np.full_like(T, np.nan)
    dTpp = np.full_like(T, np.nan)

    # ── AC loss per speed ─────────────────────────────────────────────────────
    # AC loss JSON uses peak current; convert to RMS for matching
    rad_ac   = np.deg2rad(raw_ac["gamma"] + 90.0)
    Id_rms_ac = raw_ac["Is_peak"] * np.cos(rad_ac) / np.sqrt(2)
    Iq_rms_ac = raw_ac["Is_peak"] * np.sin(rad_ac) / np.sqrt(2)

    speed_vec = raw_ac["speed_vec"]
    nS = len(speed_vec)
    sh = Id.shape + (nS,)

    Pac_total = np.full(sh, np.nan)
    Pac_prox  = np.full(sh, np.nan)
    Pac_skin  = np.full(sh, np.nan)

    for k, spd in enumerate(speed_vec):
        mask = raw_ac["speed"] == spd
        Pac_total[..., k] = _interp2d(
            Id_rms_ac[mask], Iq_rms_ac[mask], raw_ac["Pac_total_kW"][mask], Id, Iq)
        Pac_prox[..., k]  = _interp2d(
            Id_rms_ac[mask], Iq_rms_ac[mask], raw_ac["Pac_prox_kW"][mask],  Id, Iq)
        Pac_skin[..., k]  = _interp2d(
            Id_rms_ac[mask], Iq_rms_ac[mask], raw_ac["Pac_skin_kW"][mask],  Id, Iq)

    FluxMap_dq = {
        "Id":           Id,          # [nIq, nId]  RMS A
        "Iq":           Iq,          # [nIq, nId]  RMS A
        "Fd":           Fd,          # [nIq, nId]  Wb
        "Fq":           Fq,          # [nIq, nId]  Wb
        "T":            T,           # [nIq, nId]  Nm
        "dT":           dT,          # NaN
        "dTpp":         dTpp,        # NaN
        "Pac_total_kW": Pac_total,   # [nIq, nId, nSpeed]  kW
        "Pac_prox_kW":  Pac_prox,
        "Pac_skin_kW":  Pac_skin,
        "speed_vec":    speed_vec,   # [nSpeed]  rpm
    }

    res_dict = {
        "FluxMap_dq": FluxMap_dq,
        "raw": {"psi": raw_psi, "acloss": raw_ac},
    }

    if raw_psi.get("has_losses", False):
        Pfes_h = _interp2d(Id_rms_psi, Iq_rms_psi, raw_psi["Pfes_h"].ravel(), Id, Iq)
        Pfes_c = _interp2d(Id_rms_psi, Iq_rms_psi, raw_psi["Pfes_c"].ravel(), Id, Iq)
        Pfer_h = _interp2d(Id_rms_psi, Iq_rms_psi, raw_psi["Pfer_h"].ravel(), Id, Iq)
        Pfer_c = _interp2d(Id_rms_psi, Iq_rms_psi, raw_psi["Pfer_c"].ravel(), Id, Iq)
        Ppm    = _interp2d(Id_rms_psi, Iq_rms_psi, raw_psi["Ppm"].ravel(), Id, Iq)
        
        n0 = raw_psi["FEALossMap_RefSpeed_Lab"]
        
        res_dict["IronPMLossMap_dq"] = {
            "type":   "map",
            "Id":     Id,
            "Iq":     Iq,
            "Pfes_h": Pfes_h,
            "Pfes_c": Pfes_c,
            "Pfer_h": Pfer_h,
            "Pfer_c": Pfer_c,
            "Ppm":    Ppm,
            "n0":     n0,
            "f0":     n0 * p / 60.0,
            "expH":   raw_psi["expH"],
            "expC":   raw_psi["expH"], # apply the same iron loss scaling
            "expPM":  raw_psi["expPM"],
            "segPM":  1.0,
        }

    return res_dict


# ─────────────────────────────────────────────────────────────────────────────
# 4. Save to .mat (SyRE-compatible)
# ─────────────────────────────────────────────────────────────────────────────

def save_syre_mat(result: dict, out_path: str | Path) -> None:
    """
    Save FluxMap_dq + raw to .mat file for SyRE MMM.

    Usage in MATLAB after loading:
        motorModel.FluxMap_dq = mat.FluxMap_dq;
        save(matPath, 'motorModel', '-append')
    """
    out_path = Path(out_path)
    fmap = result["FluxMap_dq"]
    raw  = result["raw"]

    mat_dict = {
        # SyRE MMM primary fields
        "FluxMap_dq": {
            "Id":           fmap["Id"],
            "Iq":           fmap["Iq"],
            "Fd":           fmap["Fd"],
            "Fq":           fmap["Fq"],
            "T":            fmap["T"],
            "dT":           fmap["dT"],
            "dTpp":         fmap["dTpp"],
            "Pac_total_kW": fmap["Pac_total_kW"],
            "Pac_prox_kW":  fmap["Pac_prox_kW"],
            "Pac_skin_kW":  fmap["Pac_skin_kW"],
            "speed_vec":    fmap["speed_vec"],
        },
        # Raw data preserved
        "raw_psi": {
            "Is_peak": raw["psi"]["Is_peak"],
            "gamma":   raw["psi"]["gamma"],
            "PsiD":    raw["psi"]["PsiD"],
            "PsiQ":    raw["psi"]["PsiQ"],
            "Id_peak": raw["psi"]["Id_peak"],
            "Iq_peak": raw["psi"]["Iq_peak"],
        },
        "raw_acloss": {
            "Is_peak":      raw["acloss"]["Is_peak"],
            "gamma":        raw["acloss"]["gamma"],
            "speed":        raw["acloss"]["speed"],
            "Pac_total_kW": raw["acloss"]["Pac_total_kW"],
            "Pac_prox_kW":  raw["acloss"]["Pac_prox_kW"],
            "Pac_skin_kW":  raw["acloss"]["Pac_skin_kW"],
            "speed_vec":    raw["acloss"]["speed_vec"],
        },
    }
    if "IronPMLossMap_dq" in result:
        mat_dict["IronPMLossMap_dq"] = result["IronPMLossMap_dq"]
        
    savemat(str(out_path), mat_dict)
    print(f"Saved → {out_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Quick plot for verification
# ─────────────────────────────────────────────────────────────────────────────

def plot_fluxmap(result: dict) -> None:
    """Verify output: PsiD surface + torque contour + AC loss at first speed."""
    import matplotlib.pyplot as plt

    fmap = result["FluxMap_dq"]
    Id, Iq, Fd, T = fmap["Id"], fmap["Iq"], fmap["Fd"], fmap["T"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # PsiD
    ax = axes[0]
    cf = ax.contourf(Id, Iq, Fd, levels=20)
    fig.colorbar(cf, ax=ax)
    ax.set(title="Fd (Wb) — interpolated", xlabel="Id RMS (A)", ylabel="Iq RMS (A)")

    # Torque
    ax = axes[1]
    cf = ax.contourf(Id, Iq, T, levels=20)
    fig.colorbar(cf, ax=ax)
    ax.set(title="Torque (Nm)", xlabel="Id RMS (A)", ylabel="Iq RMS (A)")

    # AC loss at first speed
    ax = axes[2]
    spd0 = fmap["speed_vec"][0]
    cf = ax.contourf(Id, Iq, fmap["Pac_total_kW"][..., 0], levels=20)
    fig.colorbar(cf, ax=ax)
    ax.set(title=f"AC Loss total (kW) @ {spd0:.0f} rpm",
           xlabel="Id RMS (A)", ylabel="Iq RMS (A)")

    # Raw scatter overlay
    raw_psi = result["raw"]["psi"]
    axes[0].scatter(
        raw_psi["Id_peak"].ravel() / np.sqrt(2),
        raw_psi["Iq_peak"].ravel() / np.sqrt(2),
        s=10, c="w", alpha=0.5, label="Lab grid pts")
    axes[0].legend(fontsize=7)

    plt.tight_layout()
    plt.show()


# ─────────────────────────────────────────────────────────────────────────────
# 6. Top-level runner (call after Lab calculation finishes)
# ─────────────────────────────────────────────────────────────────────────────

def run(mcad,
        json_path: str | Path,
        out_mat:   str | Path,
        p:         int = 4,
        plot:      bool = True) -> dict:
    """
    Full pipeline: Motor-CAD Lab + JSON → SyRE .mat

    Parameters
    ----------
    mcad      : connected pymotorcad.MotorCAD instance (Lab calc done)
    json_path : JEET_ACLoss_*_Map_Summary.json path
    out_mat   : output .mat file path
    p         : pole pairs
    plot      : show verification plots

    Example
    -------
    import pymotorcad
    import fromMCAD_lab_json as flj

    mcad = pymotorcad.MotorCAD()
    mcad.load_from_file(r"D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn6V261.mot")
    # ... wait for Lab calc ...

    result = flj.run(
        mcad,
        json_path = r"D:\\KangDH\\EveryMotor\\eMach\\mlxperPJT\\JEET\\map_exports\\e10\\Ref\\JEET_ACLoss_Ref_Map_Summary.json",
        out_mat   = r"D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn6V261_FluxMap.mat",
        p=4,
    )
    """
    print("── Step 1: Extract Lab flux linkage ────────────────────────────────")
    raw_psi = extract_lab_psi(mcad)

    print("\n── Step 2: Load JSON AC loss ────────────────────────────────────────")
    raw_ac = load_acloss_json(json_path)

    print("\n── Step 3: Build SyRE FluxMap_dq ───────────────────────────────────")
    result = build_syre_fluxmap(raw_psi, raw_ac, p)

    fmap = result["FluxMap_dq"]
    print(f"  Grid     : {fmap['Id'].shape[1]} Id × {fmap['Id'].shape[0]} Iq  (RMS)")
    print(f"  Torque   : {fmap['T'].min():.1f} – {fmap['T'].max():.1f} Nm")
    print(f"  Speeds   : {fmap['speed_vec']}")

    print("\n── Step 4: Save .mat ───────────────────────────────────────────────")
    save_syre_mat(result, out_mat)

    if plot:
        plot_fluxmap(result)

    return result


def extract_lab_psi_offline(mot_path: str | Path, verbose: bool = True) -> dict:
    """Extract flux linkage saturation map directly from .mot file text (offline)."""
    mot_path = Path(mot_path)
    if not mot_path.exists():
        raise FileNotFoundError(f"File not found: {mot_path}")

    data = {}
    with open(mot_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                continue
            elif "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Handle array indices like Var[0]
                match = re.match(r"([^\[]+)\[(\d+)\]", key)
                if match:
                    base_key = match.group(1)
                    idx = int(match.group(2))
                    if base_key not in data:
                        data[base_key] = {}
                    data[base_key][idx] = val
                else:
                    data[key] = val

    # Post-process arrays
    processed = {}
    for k, v in data.items():
        if isinstance(v, dict):
            # Sort by index and join with ':'
            sorted_indices = sorted(v.keys())
            vals = [v[idx] for idx in sorted_indices]
            processed[k] = ":".join(vals)
        else:
            processed[k] = v

    Is_flat = _parse_mcad_array_string(processed.get("SatModel_Is_Lab", ""))
    gam_flat = _parse_mcad_array_string(processed.get("SatModel_Gamma_Lab", ""))

    Is_vec = np.sort(np.unique(np.round(Is_flat, 4)))
    gamma_vec = np.sort(np.unique(np.round(gam_flat, 4)))

    nI = len(Is_vec)
    nG = len(gamma_vec)

    if nI == 0 or nG == 0:
        raise ValueError("Failed to parse SatModel_Is_Lab or SatModel_Gamma_Lab from .mot file")

    raw_psiD = _parse_mcad_array_string(processed.get("PsiDModel_Lab", ""))
    raw_psiQ = _parse_mcad_array_string(processed.get("PsiQModel_Lab", ""))

    # Motor-CAD serialises as [nI x nG] -> reshape -> [nI x nG]
    PsiD = raw_psiD.reshape(nI, nG)   # [nI, nG]  Wb
    PsiQ = raw_psiQ.reshape(nI, nG)

    # Current and gamma vectors
    GAMMA, IS = np.meshgrid(gamma_vec, Is_vec)          # both [nI, nG]
    rad = np.deg2rad(GAMMA + 90.0)
    Id_peak = IS * np.cos(rad)
    Iq_peak = IS * np.sin(rad)

    if verbose:
        print(f"Lab grid  : {nI} currents x {nG} angles (Offline)")
        print(f"Is range  : {Is_vec[0]:.1f} - {Is_vec[-1]:.1f} A peak")
        print(f"PsiD range: {PsiD.min():.4f} - {PsiD.max():.4f} Wb")
        print(f"PsiQ range: {PsiQ.min():.4f} - {PsiQ.max():.4f} Wb")

    res = {
        "Is_peak": Is_vec,
        "gamma":   gamma_vec,
        "PsiD":    PsiD,
        "PsiQ":    PsiQ,
        "Id_peak": Id_peak,
        "Iq_peak": Iq_peak,
        "has_losses": False
    }

    try:
        n0 = float(processed.get("FEALossMap_RefSpeed_Lab", 0.0))
        expH = float(processed.get("Speed_Coeff_-_Stator_Iron_Loss_[Back_Iron]", 1.5))
        expPM = float(processed.get("Speed_Coeff_-_Magnet_Iron_Loss", 2.0))
        backIronHy = _parse_mcad_array_string(processed.get("FeLossBackIronHy_MotorLAB", "0"))
        toothHy = _parse_mcad_array_string(processed.get("FeLossToothHy_MotorLAB", "0"))
        backIronEd = _parse_mcad_array_string(processed.get("FeLossBackIronEd_MotorLAB", "0"))
        toothEd = _parse_mcad_array_string(processed.get("FeLossToothEd_MotorLAB", "0"))
        rotorHy = _parse_mcad_array_string(processed.get("FeLossRotorHy_MotorLAB", "0"))
        rotorPoleHy = _parse_mcad_array_string(processed.get("FeLossRotorPoleHy_MotorLAB", "0"))
        rotorEd = _parse_mcad_array_string(processed.get("FeLossRotorEd_MotorLAB", "0"))
        rotorPoleEd = _parse_mcad_array_string(processed.get("FeLossRotorPoleEd_MotorLAB", "0"))
        magLoss = _parse_mcad_array_string(processed.get("MagLossArray_MotorLAB", "0"))
        
        Pfes_h_flat = backIronHy + toothHy
        Pfes_c_flat = backIronEd + toothEd
        Pfer_h_flat = rotorHy + rotorPoleHy
        Pfer_c_flat = rotorEd + rotorPoleEd
        Ppm_flat = magLoss
        
        if len(Pfes_h_flat) == nI * nG:
            res["FEALossMap_RefSpeed_Lab"] = n0
            res["expH"] = expH
            res["expPM"] = expPM
            res["Pfes_h"] = Pfes_h_flat.reshape(nI, nG)
            res["Pfes_c"] = Pfes_c_flat.reshape(nI, nG)
            res["Pfer_h"] = Pfer_h_flat.reshape(nI, nG)
            res["Pfer_c"] = Pfer_c_flat.reshape(nI, nG)
            res["Ppm"] = Ppm_flat.reshape(nI, nG)
            res["has_losses"] = True
    except Exception as e:
        # Ignore loss extraction failures gracefully
        res["expH"] = 1.5
        res["expPM"] = 2.0
        res["has_losses"] = False

    return res


def run_offline(mot_path: str | Path,
                json_path: str | Path,
                out_mat:   str | Path,
                p:         int = 4,
                plot:      bool = True) -> dict:
    """Offline pipeline: direct .mot parsing + JSON -> SyRE .mat"""
    print("── Step 1: Extract Lab flux linkage (Offline) ────────────────────────")
    raw_psi = extract_lab_psi_offline(mot_path)

    print("\n── Step 2: Load JSON AC loss ────────────────────────────────────────")
    raw_ac = load_acloss_json(json_path)

    print("\n── Step 3: Build SyRE FluxMap_dq ───────────────────────────────────")
    result = build_syre_fluxmap(raw_psi, raw_ac, p)

    fmap = result["FluxMap_dq"]
    print(f"  Grid     : {fmap['Id'].shape[1]} Id x {fmap['Id'].shape[0]} Iq  (RMS)")
    print(f"  Torque   : {np.nanmin(fmap['T']):.1f} - {np.nanmax(fmap['T']):.1f} Nm")
    print(f"  Speeds   : {fmap['speed_vec']}")

    print("\n── Step 4: Save .mat ───────────────────────────────────────────────")
    save_syre_mat(result, out_mat)

    if plot:
        plot_fluxmap(result)

    return result

