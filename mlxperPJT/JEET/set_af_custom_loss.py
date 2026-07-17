"""set_af_custom_loss.py - AF 보정 수식을 Motor-CAD Lab Internal Custom Loss로 등록 + 효율맵 실행.

runAFCustomLossLab.m (S1/S5~S9)의 Python 포팅. 검증된 워크플로우:
  1. AF 수식 빌드 (poly10 기본 | A | B)
  2. v261 COM 등록 / .mot 버전 가드
  3. Motor-CAD 열기 (pymotorcad)
  4. Internal Custom Loss 관련 변수 탐색 (GetVariable) -> 스냅샷 JSON
  5. (기본) baseline 효율맵
  6. Custom Loss 등록 (기존 동일 이름 교체) + read-back 검증
  7. 운전점 체크포인트: CustomLoss/AC 비율 vs 수식 자체 평가값 (하드 가드)
  8. AF 효율맵 -> MotorLAB_elecdata.mat 복사
  9. 결과 추출 (효율 + 손실 분해) -> CSV / 요약 JSON (baseline 있으면 delta-eta 통계)

실행 (pyMotorEnv_310 필수 - pymotorcad 0.8.4):
  C:\\Users\\user\\.ansys_python_venvs\\pyMotorEnv_310\\Scripts\\python.exe set_af_custom_loss.py --dry-run
  ... set_af_custom_loss.py --skip-map          # 등록+체크포인트까지만
  ... set_af_custom_loss.py                     # 전체 (baseline + AF 효율맵, 수 분 소요)

주의: Method A(speed_poly_coeffs)는 AF_MCAD_CONTEXT.md 2026-07-12 경고에 따라 사용 금지
      (정규화된 f(s)일 뿐 절대 AF 아님). 기본값은 Lab 베이스 재피팅 poly10.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_MOT     = r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_customLoss.mot"
DEFAULT_SRC_MOT = r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot"          # 920A Lab 빌드 원본
DEFAULT_AFONLY_MOT = r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_AFonly.mot"  # Lab 원본 + Custom Loss만
DEFAULT_JSON    = SCRIPT_DIR / "map_exports" / "e10" / "SC" / "AF_RBF_model_SC.json"
DEFAULT_POLY10  = SCRIPT_DIR / "map_exports" / "e10" / "SC" / "lab_af" / "AF_LabBase_poly10_formula.txt"
DEFAULT_OUT     = SCRIPT_DIR / "map_exports" / "e10" / "SC" / "lab_af"
DEFAULT_OUT_AFONLY = SCRIPT_DIR / "map_exports" / "e10" / "SC" / "lab_af_orig"  # AFonly 결과 출력

# 체크포인트 운전점 (runAFCustomLossLab.m S7과 동일)
CHK_SPEED_RPM = 8000
CHK_IRMS_A    = 460.05
CHK_PHASE_DEG = 36.0
CHK_TOL       = 0.02   # |비율 - 기대값| 허용치

METHOD_A_WARNING = """
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! [경고] Method A는 사용 금지 (AF_MCAD_CONTEXT.md, 2026-07-12 판명)     !!
!! speed_poly_coeffs는 f(s)*g(I,phase) 분해의 정규화된 속도 인자일 뿐    !!
!! 절대 AF가 아님. 실측 AF 중앙값 2k=1.74/4k=1.53/8k=1.27/16k=1.35 대비  !!
!! 이 다항식은 1.12/.../0.82를 줘서 보정이 크게 과소 (16k에선 음수).     !!
!! 검증된 대체: --method poly10 (AF_LabBase_poly10_formula.txt)          !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""


# ---------------------------------------------------------------------------
# 1. AF 수식 빌드
# ---------------------------------------------------------------------------

def build_af_formula(method: str, json_path: Path, poly10_path: Path):
    """AF 수식 문자열 + 메타정보 생성.

    Returns dict: formula, method, required_vars, n_chars, expected_ratio(fn|None)
    """
    method = method.upper() if method.lower() != "poly10" else "poly10"

    if method == "poly10":
        if not poly10_path.is_file():
            raise FileNotFoundError(f"poly10 수식 파일 없음: {poly10_path}")
        formula = re.sub(r"\s+", " ", poly10_path.read_text(encoding="utf-8")).strip()
        required = ["Stator_Copper_Loss_AC", "Speed",
                    "Stator_Current_Phase_RMS", "Phase_Advance"]

    elif method == "A":
        print(METHOD_A_WARNING, file=sys.stderr)
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        c = raw["separable_model"]["speed_poly_coeffs"]
        if len(c) != 3:
            raise ValueError(f"speed_poly_coeffs는 3개여야 함 (현재 {len(c)}개)")
        # buildAfCustomLossFormula.m Method A와 동일: (AF(s)-1)*P_AC
        formula = (f"Stator_Copper_Loss_AC * (({c[0]:.9g})*(Speed/1000)**2"
                   f" + ({c[1]:.9g})*(Speed/1000) + ({c[2] - 1:.9g}))")
        required = ["Stator_Copper_Loss_AC", "Speed"]

    elif method == "B":
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        if "mcad_formula_full" not in raw:
            raise KeyError("mcad_formula_full 필드 없음")
        formula = re.sub(r"\s+", " ", raw["mcad_formula_full"]).strip()
        required = ["Stator_Copper_Loss_AC", "Speed",
                    "Stator_Current_Phase_RMS", "Phase_Advance"]

    else:
        raise ValueError(f"--method는 poly10 | A | B (입력: {method})")

    info = {
        "method": method,
        "formula": formula,
        "required_vars": required,
        "n_chars": len(formula),
        "expected_ratio": _make_ratio_fn(formula),
    }
    return info


def _make_ratio_fn(formula: str):
    """수식을 자체 평가해 CustomLoss/Stator_Copper_Loss_AC 비율을 계산하는 함수 생성.

    Custom Loss 수식은 P_AC에 선형이므로 P_AC=1을 대입한 값이 곧 비율.
    Motor-CAD가 수식을 올바르게 파싱했는지 체크포인트에서 대조하는 용도.
    """
    def ratio(speed_rpm: float, irms: float, phase_deg: float) -> float:
        ns = {
            "Stator_Copper_Loss_AC": 1.0,
            "Speed": float(speed_rpm),
            "Stator_Current_Phase_RMS": float(irms),
            "Phase_Advance": float(phase_deg),
            "sqrt": math.sqrt, "log": math.log, "exp": math.exp, "abs": abs,
        }
        return float(eval(formula, {"__builtins__": {}}, ns))  # noqa: S307 - 자체 생성 수식

    try:
        ratio(CHK_SPEED_RPM, CHK_IRMS_A, CHK_PHASE_DEG)  # 평가 가능성 검사
    except Exception as err:
        print(f"[build] 수식 자체 평가 불가 ({err}) -> 체크포인트는 로그만 수행", file=sys.stderr)
        return None
    return ratio


# ---------------------------------------------------------------------------
# 2. 버전 가드 (runAFCustomLossLab.m S1 포팅)
# ---------------------------------------------------------------------------

def check_v261(mot_path: Path) -> None:
    """COM 등록이 v261인지 + .mot Program_Version 확인. 불일치 시 예외."""
    import winreg

    com_exe = ""
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"motorcad.appautomation\CLSID") as k:
            clsid = winreg.QueryValue(k, None)
        for root in (r"SOFTWARE\WOW6432Node\Classes\CLSID", r"SOFTWARE\Classes\CLSID"):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                    rf"{root}\{clsid}\LocalServer32") as k:
                    val, _typ = winreg.QueryValueEx(k, "")   # REG_EXPAND_SZ 가능 (%MOTORCAD_ACTIVEX%)
                    com_exe = winreg.ExpandEnvironmentStrings(val)
                break
            except OSError:
                continue
    except OSError as err:
        print(f"[가드] COM 등록 확인 실패({err}) - 실행 후 버전을 직접 확인할 것", file=sys.stderr)

    print(f"[가드] COM 서버: {com_exe or '(확인 불가)'}")
    if com_exe and "v261" not in com_exe:
        raise RuntimeError(
            f"motorcad.appautomation COM 등록이 v261이 아님!\n  현재: {com_exe}\n"
            "  해결: Motor-CAD 2026R1을 한 번 실행(재등록)하거나 activex.bat 경로 확인")

    m = re.search(r"^\s*Program_Version=([^\r\n]+)", mot_path.read_text(errors="ignore"),
                  re.MULTILINE)
    mot_ver = m.group(1).strip() if m else "(없음)"
    print(f"[가드] .mot Program_Version: {mot_ver}")
    if m and not mot_ver.startswith("2026."):
        print(f"[가드] .mot이 2026.x 포맷이 아님({mot_ver}) - 포맷 변환 주의", file=sys.stderr)


# ---------------------------------------------------------------------------
# 3. Motor-CAD 연결
# ---------------------------------------------------------------------------

def connect_mcad(mot_path: Path):
    """pymotorcad로 Motor-CAD 실행 + .mot 로드 (_mcad_parallel_worker.py 패턴)."""
    import ansys.motorcad.core as pymotorcad

    print(f"[연결] Motor-CAD 실행 중 ... (.mot: {mot_path})")
    mcad = pymotorcad.MotorCAD(enable_success_variable=False)
    try:
        mcad.set_variable("MessageDisplayState", 2)  # 팝업 억제
    except Exception:
        pass
    mcad.load_from_file(str(mot_path))
    built = mcad.get_model_built_lab()
    print(f"[연결] 로드 완료. Lab 모델 빌드 상태: {built}")
    if not built:
        raise RuntimeError(
            "Lab 모델이 빌드되지 않은 .mot - GUI에서 Lab Build 후 저장하거나 "
            "SLFEA customLoss .mot(빌드 완료본)을 사용할 것")
    return mcad


# ---------------------------------------------------------------------------
# 4. Custom Loss 관련 변수 탐색
# ---------------------------------------------------------------------------

def explore_custom_loss_vars(mcad, required_vars: list[str], out_dir: Path) -> dict:
    """Internal Custom Loss 관련 변수 현황을 읽어 출력 + 스냅샷 JSON 저장."""
    mcad.set_motorlab_context()
    snap: dict = {"scalar": {}, "entries": []}

    scalar_vars = [
        "CustomLossVariablesInternal_Lab",   # 수식 허용 변수 목록
        "NumCustomLossesInternal_Lab",
        "NumCustomLossesExternal_Lab",
        "CalcTypeCuLoss_MotorLAB",
        "LabModel_ACLoss_Method",
        "ACLossHighFrequencyScaling_Method",
        "EmagneticCalcType_Lab",
        "DCBusVoltage",
        "ControlStrat_MotorLAB",
        "OperatingMode_Lab",
    ]
    print("\n=== [탐색] Internal Custom Loss / Lab 설정 변수 ===")
    for v in scalar_vars:
        try:
            val = mcad.get_variable(v)
        except Exception as err:
            val = f"(읽기 실패: {err})"
        snap["scalar"][v] = val
        print(f"  {v:44s} = {val}")

    # 허용 변수 목록에 수식 필수 변수가 있는지 검증
    avail = str(snap["scalar"].get("CustomLossVariablesInternal_Lab", ""))
    for rv in required_vars:
        if rv.lower() not in avail.lower():
            print(f"  [경고] 수식 변수 '{rv}'가 허용 목록에 없음! GUI에서 변수명 확인 필요",
                  file=sys.stderr)

    # 기존 등록 항목 순회
    try:
        num = int(snap["scalar"].get("NumCustomLossesInternal_Lab", 0) or 0)
    except (TypeError, ValueError):
        num = 0
    for i in range(num):
        entry = {"index": i}
        for field in ("Name", "Function", "Type", "ThermalNode"):
            try:
                entry[field] = mcad.get_array_variable(f"CustomLoss_{field}_Internal_Lab", i)
            except Exception as err:
                entry[field] = f"(읽기 실패: {err})"
        snap["entries"].append(entry)
        func = str(entry["Function"])
        print(f"  [{i}] {entry['Name']} ({entry['Type']}, node={entry['ThermalNode']}): "
              f"{func[:70]}{'...' if len(func) > 70 else ''}")
    if num == 0:
        print("  (기존 Internal Custom Loss 항목 없음)")

    out_dir.mkdir(parents=True, exist_ok=True)
    snap_path = out_dir / "custom_loss_vars_snapshot.json"
    snap_path.write_text(json.dumps(snap, indent=2, ensure_ascii=False, default=str),
                         encoding="utf-8")
    print(f"  스냅샷 저장: {snap_path}")
    return snap


# ---------------------------------------------------------------------------
# 5. Custom Loss 등록 (addLabInternalCustomLoss.m 미러)
# ---------------------------------------------------------------------------

def register_custom_loss(mcad, name: str, formula: str, mot_path: Path) -> None:
    mcad.set_motorlab_context()
    num = int(mcad.get_variable("NumCustomLossesInternal_Lab") or 0)

    for i in range(num):
        existing = str(mcad.get_array_variable("CustomLoss_Name_Internal_Lab", i)).strip()
        if existing.lower() == name.strip().lower():
            print(f"[등록] 기존 항목 제거 후 재등록: '{name}' (index {i})")
            mcad.remove_internal_custom_loss(existing)
            break
    else:
        print(f"[등록] 신규 등록: '{name}'")

    # pymotorcad 래퍼 add_internal_custom_loss는 thermal_node 존재 검증 때문에
    # -1(미지정)을 거부("Thermal node does not exist") -> raw array variable로 직접 등록
    # (addLabInternalCustomLoss.m과 동일 시퀀스)
    n = int(mcad.get_variable("NumCustomLossesInternal_Lab") or 0)
    mcad.set_variable("NumCustomLossesInternal_Lab", n + 1)
    mcad.set_array_variable("CustomLoss_Name_Internal_Lab", n, name)
    mcad.set_array_variable("CustomLoss_Function_Internal_Lab", n, formula)
    mcad.set_array_variable("CustomLoss_Type_Internal_Lab", n, "Electrical")
    mcad.set_array_variable("CustomLoss_ThermalNode_Internal_Lab", n, -1)

    # read-back 검증 (잘림/문법 문제 검출)
    num2 = int(mcad.get_variable("NumCustomLossesInternal_Lab") or 0)
    idx = next(i for i in range(num2)
               if str(mcad.get_array_variable("CustomLoss_Name_Internal_Lab", i)).strip()
               == name.strip())
    rb_func = str(mcad.get_array_variable("CustomLoss_Function_Internal_Lab", idx))
    rb_type = str(mcad.get_array_variable("CustomLoss_Type_Internal_Lab", idx))
    if rb_func != formula:
        raise RuntimeError(
            "read-back 수식이 입력과 다름 (수식 길이 제한 또는 문법 문제 가능성)\n"
            f"  입력({len(formula)}자): {formula[:80]}...\n"
            f"  read-back({len(rb_func)}자): {rb_func[:80]}...")
    print(f"[등록] read-back 일치 ({len(rb_func)}자, type={rb_type}, index={idx})")

    mcad.save_to_file(str(mot_path))
    print(f"[등록] .mot 저장 완료: {mot_path}")


# ---------------------------------------------------------------------------
# 6. 운전점 체크포인트 (S2 spec 탐색 + S7 하드 가드 포팅)
# ---------------------------------------------------------------------------

def checkpoint_op_point(mcad, expected_ratio) -> None:
    mcad.set_motorlab_context()
    mcad.set_variable("SpeedDemand_MotorLAB", CHK_SPEED_RPM)
    mcad.set_variable("StatorCurrentDemand_RMS_Lab", CHK_IRMS_A)
    mcad.set_variable("PhaseAdvanceDemand_Lab", CHK_PHASE_DEG)

    # OpPointSpec enum 미문서화 -> 후보 순회, read-back으로 달성 spec 탐색
    tried = []
    op_irms = op_phase = None
    for spec in (1, 2, 0, 3, 4):
        try:
            mcad.set_variable("OpPointSpec_MotorLAB", spec)
            mcad.calculate_operating_point_lab()
        except Exception as err:
            tried.append(f"spec={spec}: 계산 실패({err})")
            continue
        op_irms  = float(mcad.get_variable("LabOpPoint_StatorCurrent_Phase_RMS"))
        op_phase = float(mcad.get_variable("LabOpPoint_PhaseAdvance"))
        tried.append(f"spec={spec}: Irms={op_irms:.1f}, PhAdv={op_phase:.1f}")
        if abs(op_irms - CHK_IRMS_A) < 5 and abs(op_phase - CHK_PHASE_DEG) < 2:
            print(f"[체크포인트] OpPointSpec={spec} 채택 "
                  f"(Irms={op_irms:.1f} A, PhAdv={op_phase:.1f} deg)")
            break
    else:
        raise RuntimeError("요구 운전점({:.0f}Arms/{:.0f}deg) 달성 spec 없음:\n  {}".format(
            CHK_IRMS_A, CHK_PHASE_DEG, "\n  ".join(tried)))

    p_ac     = float(mcad.get_variable("LabOpPoint_StatorCopperLoss_AC"))
    p_custom = float(mcad.get_variable("LabOpPoint_CustomLoss_Total_Internal"))
    ratio = p_custom / p_ac if p_ac else float("nan")
    print(f"[체크포인트] {CHK_SPEED_RPM} rpm / {op_irms:.1f} Arms / {op_phase:.1f} deg:")
    print(f"  Stator_Copper_Loss_AC      = {p_ac:.1f} W")
    print(f"  CustomLoss_Total_Internal  = {p_custom:.1f} W  ->  비율 {ratio:.4f}")

    if expected_ratio is None:
        print("  (기대값 함수 없음 - 비율 로그만 수행)")
        return
    # 달성 운전점 기준으로 수식 자체 평가값과 대조
    expected = expected_ratio(CHK_SPEED_RPM, op_irms, op_phase)
    print(f"  기대값(수식 자체 평가)      = {expected:.4f}")
    if abs(ratio - expected) >= CHK_TOL:
        raise RuntimeError(
            f"[체크포인트] Custom Loss 비율({ratio:.4f})이 기대값({expected:.4f})과 불일치 - "
            "수식 문법(** 연산자)/변수명/Speed 단위 문제. "
            "GUI Lab > Losses에서 수식 파싱 상태 확인 필요. 효율맵 진행 중단.")
    print("  비율 일치 OK")


# ---------------------------------------------------------------------------
# 7. 효율맵 실행 (S5/S8 포팅)
# ---------------------------------------------------------------------------

def run_efficiency_map(mcad, tag: str, out_dir: Path) -> Path:
    mcad.set_motorlab_context()
    mcad.set_variable("EmagneticCalcType_Lab", 1)   # 1 = Efficiency Map
    mcad.set_variable("SpeedMin_MotorLAB", 0)
    mcad.set_variable("SpeedMax_MotorLAB", 16000)
    mcad.set_variable("Speedinc_MotorLAB", 500)
    mcad.set_variable("CurrentSpec_MotorLAB", 1)    # RMS 입력
    mcad.set_variable("Imax_RMS_MotorLAB", 920)     # 모터 정격 전류 (FEA sweep 범위와 일치)
    mcad.set_variable("Imin_MotorLAB", 0)
    for v in ("DCBusVoltage", "ControlStrat_MotorLAB", "ModulationIndex_MotorLAB",
              "OperatingMode_Lab"):
        try:
            print(f"  {v} = {mcad.get_variable(v)}")
        except Exception:
            pass

    print(f"[효율맵:{tag}] 계산 시작 (수 분 소요) ...")
    t0 = time.time()
    mcad.calculate_magnetic_lab()
    print(f"[효율맵:{tag}] 완료 ({time.time() - t0:.0f} s)")

    lab_dir = Path(str(mcad.get_variable("ResultsPath_MotorLAB")).strip())
    src_mat = lab_dir / "MotorLAB_elecdata.mat"
    if not src_mat.is_file():
        raise FileNotFoundError(f"Lab 결과 mat 없음: {src_mat}")
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"MotorLAB_elecdata_{tag}.mat"
    shutil.copy2(src_mat, dst)
    print(f"[효율맵:{tag}] 저장: {dst}")
    return dst


# ---------------------------------------------------------------------------
# 8. 결과 추출 (효율 + 손실 분해 -> CSV / 요약 JSON)
# ---------------------------------------------------------------------------

def extract_results(mat_path: Path, tag: str, out_dir: Path,
                    baseline_mat: Path | None = None) -> None:
    import numpy as np
    from scipy.io import loadmat

    data = loadmat(str(mat_path))
    speed  = np.asarray(data["Speed"], dtype=float)
    torque = np.asarray(data["Shaft_Torque"], dtype=float)
    eff    = np.asarray(data["Efficiency"], dtype=float)
    if np.nanmax(eff) <= 1.5:
        eff = eff * 100.0

    # 손실 분해: Speed와 같은 그리드 크기의 *Loss* 키 자동 수집
    loss_keys = sorted(
        k for k, v in data.items()
        if not k.startswith("__") and "loss" in k.lower()
        and hasattr(v, "shape") and v.shape == speed.shape)

    # long-format CSV
    csv_path = out_dir / f"effmap_{tag}.csv"
    cols = ["speed_rpm", "torque_Nm", "efficiency_pct"] + loss_keys
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(cols) + "\n")
        flat = [speed.ravel(), torque.ravel(), eff.ravel()] + \
               [np.asarray(data[k], dtype=float).ravel() for k in loss_keys]
        for row in zip(*flat):
            f.write(",".join(f"{x:.6g}" for x in row) + "\n")
    print(f"[추출:{tag}] CSV 저장: {csv_path} ({speed.size} pts, 손실 {len(loss_keys)}개 컬럼)")

    summary = {
        "tag": tag,
        "mat_file": str(mat_path),
        "grid_shape": list(speed.shape),
        "speed_rpm": {"min": float(np.nanmin(speed)), "max": float(np.nanmax(speed))},
        "torque_Nm": {"min": float(np.nanmin(torque)), "max": float(np.nanmax(torque))},
        "efficiency_pct": {"min": float(np.nanmin(eff)), "max": float(np.nanmax(eff)),
                           "median": float(np.nanmedian(eff))},
        "loss_keys": loss_keys,
    }

    # baseline 대비 delta-eta (S9 포팅)
    if baseline_mat and baseline_mat.is_file():
        base = loadmat(str(baseline_mat))
        eff_b = np.asarray(base["Efficiency"], dtype=float)
        if np.nanmax(eff_b) <= 1.5:
            eff_b = eff_b * 100.0
        if eff_b.shape == eff.shape:
            d = eff - eff_b
            summary["delta_eff_vs_baseline_pctpt"] = {
                "min": float(np.nanmin(d)), "median": float(np.nanmedian(d)),
                "max": float(np.nanmax(d)),
            }
            print(f"[추출:{tag}] delta-eta vs baseline: min {np.nanmin(d):.3f} / "
                  f"median {np.nanmedian(d):.3f} / max {np.nanmax(d):.3f} [%p]")
        else:
            print(f"[추출:{tag}] baseline 그리드 크기 불일치 - delta-eta 생략", file=sys.stderr)

    json_path = out_dir / f"effmap_summary_{tag}.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[추출:{tag}] 요약 JSON 저장: {json_path}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="AF 수식을 Motor-CAD Lab Internal Custom Loss로 등록 + 효율맵 실행")
    ap.add_argument("--method", default="poly10", choices=["poly10", "A", "B", "a", "b"],
                    help="AF 수식 종류 (기본 poly10 - 검증된 Lab 베이스 재피팅. "
                         "A는 스케일 버그로 사용 금지, 비교용만)")
    ap.add_argument("--mot", default=DEFAULT_MOT, help=f".mot 경로 (기본 {DEFAULT_MOT})")
    ap.add_argument("--json", default=str(DEFAULT_JSON), dest="json_path",
                    help="AF_RBF_model JSON 경로 (Method A/B용)")
    ap.add_argument("--poly10-txt", default=str(DEFAULT_POLY10),
                    help="poly10 수식 txt 경로")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="출력 디렉터리")
    ap.add_argument("--name", default=None,
                    help="Custom Loss 등록 이름 (기본 AF_<method>_SC)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Motor-CAD 없이 수식 빌드/경로 확인까지만")
    ap.add_argument("--no-baseline", action="store_true",
                    help="baseline(Custom Loss 미적용) 효율맵 생략")
    ap.add_argument("--skip-map", action="store_true",
                    help="등록 + 체크포인트까지만 (효율맵 생략)")
    ap.add_argument("--keep-open", action="store_true",
                    help="종료 시 Motor-CAD를 닫지 않음 (GUI 육안 확인용)")
    # AFonly 모드: LabLink.txt 미사용, Lab 원본 빌드 그대로 + Custom Loss만 반영
    ap.add_argument("--afonly", action="store_true",
                    help="AFonly 모드: SLFEA.mot 원본(920A Lab 빌드)을 복사 후 Custom Loss만 등록. "
                         "--mot 기본값이 AFonly용 경로로 변경되고 --out도 lab_af_orig로 분리됨")
    ap.add_argument("--copy-src", default=None,
                    help="이 경로의 .mot을 --mot 경로로 복사한 뒤 시작 "
                         "(--afonly 사용 시 기본값: DEFAULT_SRC_MOT)")
    args = ap.parse_args(argv)

    # --afonly 기본값 조정
    if args.afonly:
        if args.mot == DEFAULT_MOT:
            args.mot = DEFAULT_AFONLY_MOT
        if args.out == str(DEFAULT_OUT):
            args.out = str(DEFAULT_OUT_AFONLY)
        if args.copy_src is None:
            args.copy_src = DEFAULT_SRC_MOT

    mot_path    = Path(args.mot)
    json_path   = Path(args.json_path)
    poly10_path = Path(args.poly10_txt)
    out_dir     = Path(args.out)

    # --- 1. 수식 빌드 -------------------------------------------------------
    info = build_af_formula(args.method, json_path, poly10_path)
    loss_name = args.name or f"AF_{info['method']}_SC"
    print(f"=== AF 수식 (Method {info['method']}, {info['n_chars']}자) ===")
    print(info["formula"][:500] + ("..." if info["n_chars"] > 500 else ""))
    if info["expected_ratio"]:
        r = info["expected_ratio"]
        print("\n수식 자체 평가 (CustomLoss/P_AC 비율 = AF-1):")
        for s in (2000, 4000, 8000, 16000):
            print(f"  {s:>6d} rpm / {CHK_IRMS_A:.1f} A / {CHK_PHASE_DEG:.0f} deg : "
                  f"{r(s, CHK_IRMS_A, CHK_PHASE_DEG):+.4f}")

    if args.dry_run:
        print(f"\n[dry-run] 모드: {'AFonly (Lab 원본 빌드 + Custom Loss만)' if args.afonly else '기본 (customLoss.mot)'}")
        if args.copy_src:
            print(f"[dry-run] copy-src: {args.copy_src} → {mot_path}")
        print(f"[dry-run] .mot 경로: {mot_path}")
        print(f"[dry-run] 출력 디렉터리: {out_dir}")
        print("[dry-run] 완료 - Motor-CAD 미실행")
        return 0

    # --copy-src: 소스 .mot → 대상 .mot 복사 (dry-run 이후에 실행)
    if args.copy_src:
        src = Path(args.copy_src)
        if not src.is_file():
            raise FileNotFoundError(f"[copy-src] 소스 .mot 없음: {src}")
        if mot_path.exists():
            print(f"[copy-src] 기존 파일 덮어쓰기: {mot_path}")
        shutil.copy2(src, mot_path)
        print(f"[copy-src] 복사 완료: {src} → {mot_path}")

    if not mot_path.is_file():
        raise FileNotFoundError(f".mot 없음: {mot_path}")

    # --- 2~3. 가드 + 연결 ---------------------------------------------------
    check_v261(mot_path)
    mcad = connect_mcad(mot_path)

    try:
        # --- 4. 변수 탐색 ---------------------------------------------------
        explore_custom_loss_vars(mcad, info["required_vars"], out_dir)

        # --- 5. baseline 효율맵 (Custom Loss 등록 전) -----------------------
        # 재실행 대비: 동일 이름 항목이 이미 .mot에 있으면 baseline이 오염되므로 선제 제거
        baseline_mat = None
        if not args.skip_map and not args.no_baseline:
            num = int(mcad.get_variable("NumCustomLossesInternal_Lab") or 0)
            for i in range(num):
                nm = str(mcad.get_array_variable("CustomLoss_Name_Internal_Lab", i)).strip()
                if nm.lower() == loss_name.strip().lower():
                    print(f"[baseline] 기존 '{nm}' 항목 제거 (baseline 오염 방지)")
                    mcad.remove_internal_custom_loss(nm)
                    break
            num = int(mcad.get_variable("NumCustomLossesInternal_Lab") or 0)
            if num > 0:
                print(f"[baseline] 경고: 다른 Internal Custom Loss {num}개가 남아 있음 - "
                      "baseline에 포함됨", file=sys.stderr)
            baseline_mat = run_efficiency_map(mcad, "baseline", out_dir)
            extract_results(baseline_mat, "baseline", out_dir)

        # --- 6. 등록 + 체크포인트 -------------------------------------------
        register_custom_loss(mcad, loss_name, info["formula"], mot_path)
        checkpoint_op_point(mcad, info["expected_ratio"])

        # --- 7~8. AF 효율맵 + 결과 추출 -------------------------------------
        if not args.skip_map:
            tag = f"AF_{info['method']}"
            af_mat = run_efficiency_map(mcad, tag, out_dir)
            extract_results(af_mat, tag, out_dir, baseline_mat=baseline_mat)
        else:
            print("[main] --skip-map: 효율맵 생략 (등록+체크포인트 완료)")

    finally:
        if args.keep_open:
            print("[main] --keep-open: Motor-CAD 유지 (GUI에서 Lab > Losses 확인 가능)")
        else:
            try:
                mcad.quit()
                print("[main] Motor-CAD 종료")
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
