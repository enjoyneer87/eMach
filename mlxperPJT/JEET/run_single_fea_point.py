"""run_single_fea_point.py
========================
SC AF 데이터 보강: 단일 운전점 FEA 재계산 및 JSON 업데이트.

기본 타깃:  Speed=16000 rpm / Irms=690 Arms / Phase_Advance=90°
  - AF_infill_schedule_SC.json의 "rerun_outlier" 항목
  - 기존 값 AF=0.47로 LOOCV 상승 원인 → 재계산으로 검증

사용법:
  # 기본 (16k/690A/90° 재계산)
  python run_single_fea_point.py

  # 다른 포인트 지정
  python run_single_fea_point.py --speed 16000 --current 460.05 --phase 90

  # dry-run (Motor-CAD 없이 JSON 구조만 확인)
  python run_single_fea_point.py --dry-run

요구사항:
  - Motor-CAD v261 설치 및 ansys-motorcad (pyMotorCAD) 패키지
  - 대상 .mot 파일 존재: D:\\KangDH\\Thesis\\e10\\SLFEA\\e10Turn6V261SLFEA.mot
  - 실행 전 Motor-CAD를 닫거나 이 스크립트가 새 인스턴스를 열게 해도 됨
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

# ── 경로 설정 ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
EMACH_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(EMACH_ROOT))

MOT_PATH   = r"D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot"
JSON_PATH  = SCRIPT_DIR / "map_exports" / "e10" / "SC" / "JEET_ACLoss_SC_Map_Summary.json"
BACKUP_ROOT = SCRIPT_DIR / "map_exports" / "e10" / "SC" / "rerun_infill"

# FEA export 설정 (기존 병렬 스윕과 동일)
FIRST_STEP = 1
EXPORT_COLS = [
    "Flux_Density_B_Magnitude",
    "Harmonic_B_Radial",
    "Harmonic_B_Tangential",
]


# ── Motor-CAD 단일 포인트 계산 ──────────────────────────────────────────
def run_hybrid(mcad, speed, current, phase) -> dict:
    """Hybrid AC 손실 계산"""
    mcad.set_variable("ProximityLossModel", 1)  # Hybrid
    mcad.set_variable("ShaftSpeed", speed)
    mcad.set_variable("RMSCurrent", current)
    mcad.set_variable("PhaseAdvance", phase)
    mcad.do_magnetic_calculation()

    return {
        "mode": "Hybrid",
        # AcLossJsonReader/RbfModelBuilder가 매칭에 쓰는 키들과 동일 스키마 유지
        "proximity_model": 1,
        "backup_dir": (r"D:\KDH\simVary\e10_6TSweep\SLFEA\ACLossCalcExport_SC"
                       f"\\Hybrid_Speed_{speed:.0f}RPM_{current}A_{phase}deg_rerun"),
        "speed": speed,
        "current": current,
        "phase": phase,
        "hybrid_total_kW": float(mcad.get_variable("ACLoss_Hybrid_Total")) / 1000.0,
        "hybrid_prox_kW":  float(mcad.get_variable("ACLoss_Hybrid_Prox_Total")) / 1000.0,
        "hybrid_skin_kW":  float(mcad.get_variable("ACLoss_Hybrid_SkinEffect_Total")) / 1000.0,
    }


def run_fullfea(mcad, speed, current, phase) -> dict:
    """FullFEA AC 손실 계산"""
    from tools.motorCAD.pyMCAD import calc_dc_loss_kw

    mcad.set_variable("ProximityLossModel", 3)  # FullFEA
    mcad.set_variable("ShaftSpeed", speed)
    mcad.set_variable("RMSCurrent", current)
    mcad.set_variable("PhaseAdvance", phase)
    mcad.do_magnetic_calculation()

    try:
        per_turn_str = mcad.get_variable("ACLoss_FEA_OnLoad_PerTurn")
        if isinstance(per_turn_str, str):
            per_turn_w = [float(x) for x in per_turn_str.split(":")]
        else:
            per_turn_w = list(per_turn_str)
        per_turn_sum_kw = sum(per_turn_w) / 1000.0
        total_kw = float(mcad.get_variable("ACLoss_FEA_OnLoad_Total")) / 1000.0
    except Exception as e:
        print(f"  [WARN] FEA loss read 실패: {e}")
        per_turn_str = ""; per_turn_w = []; per_turn_sum_kw = 0.0; total_kw = 0.0

    # DC 분리 (R_active, R_end)
    try:
        mcad.set_motorlab_context()
        R_total  = float(mcad.get_variable("Resistance_MotorLAB"))
        R_end    = float(mcad.get_variable("EndWindingResistance_Lab"))
        R_active = R_total - R_end
        mcad.show_magnetic_context()
    except Exception:
        R_active = R_end = 0.0

    dc_active_kw      = calc_dc_loss_kw(R_active, current)
    dc_end_kw         = calc_dc_loss_kw(R_end, current)
    ac_active_only_kw = per_turn_sum_kw - dc_active_kw

    return {
        "mode": "FullFEA",
        # AcLossJsonReader/RbfModelBuilder가 매칭에 쓰는 키들과 동일 스키마 유지
        "proximity_model": 3,
        "backup_dir": (r"D:\KDH\simVary\e10_6TSweep\SLFEA\ACLossCalcExport_SC"
                       f"\\FullFEA_Speed_{speed:.0f}RPM_{current}A_{phase}deg_rerun"),
        "speed": speed,
        "current": current,
        "phase": phase,
        "fea_per_turn_raw":     per_turn_str,
        "fea_per_turn_sum_kW":  per_turn_sum_kw,
        "fea_total_ac_kW":      total_kw,
        "ts_dc_active_kW":      dc_active_kw,
        "ts_dc_end_kW":         dc_end_kw,
        "ts_ac_active_only_kW": ac_active_only_kw,
    }


# ── JSON 업데이트 ──────────────────────────────────────────────────────
def update_json(json_path: Path, new_hybrid: dict, new_fea: dict, speed, current, phase):
    """기존 JSON에서 해당 포인트를 교체하거나 추가"""
    with open(json_path) as f:
        db = json.load(f)

    records = db.get("records", db if isinstance(db, list) else [])
    old_hyb = None; old_fea = None

    def matches(r):
        return (abs(r.get("speed",0) - speed) < 1 and
                abs(r.get("current",0) - current) < 1 and
                abs(r.get("phase",0) - phase) < 1)

    # 제거
    kept = []
    for r in records:
        if matches(r):
            if r.get("mode") == "Hybrid": old_hyb = r
            if r.get("mode") == "FullFEA": old_fea = r
        else:
            kept.append(r)

    # 추가 (재계산 메타 포함)
    ts = datetime.now().isoformat(timespec='seconds')
    new_hybrid["rerun_ts"] = ts; new_hybrid["rerun_reason"] = "outlier_recheck"
    new_fea["rerun_ts"]    = ts; new_fea["rerun_reason"]    = "outlier_recheck"
    kept.append(new_hybrid)
    kept.append(new_fea)

    if isinstance(db, list):
        db_out = kept
    else:
        db["records"] = kept
        db_out = db

    # 백업 후 저장
    bak = json_path.with_suffix(f".bak_{ts.replace(':','-')}.json")
    shutil.copy2(json_path, bak)
    with open(json_path, "w") as f:
        json.dump(db_out, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON 업데이트 완료: {json_path}")
    print(f"   백업: {bak.name}")

    if old_hyb:
        new_ratio = new_fea.get("fea_total_ac_kW",0) / new_hybrid.get("hybrid_total_kW",1)
        print(f"\n── AF 변화 ({speed}rpm/{current}A/{phase}°) ──")
        print(f"   이전 Hybrid  = {old_hyb.get('hybrid_total_kW',0)*1000:.1f} W")
        if old_fea:
            old_ratio = old_fea.get("fea_total_ac_kW",0) / old_hyb.get("hybrid_total_kW",1)
            print(f"   이전 FullFEA = {old_fea.get('fea_total_ac_kW',0)*1000:.1f} W  → AF = {old_ratio:.4f}")
        else:
            print("   이전 FullFEA 없음 (신규 인필)")
        print(f"   신규 Hybrid  = {new_hybrid['hybrid_total_kW']*1000:.1f} W")
        print(f"   신규 FullFEA = {new_fea['fea_total_ac_kW']*1000:.1f} W  → AF = {new_ratio:.4f}")
    return old_hyb, old_fea


# ── 메인 ──────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="SC 단일 FEA 포인트 재계산")
    ap.add_argument("--speed",   type=float, default=16000,  help="회전수 [rpm]")
    ap.add_argument("--current", type=float, default=690.0,  help="전류 Irms [Arms]")
    ap.add_argument("--phase",   type=float, default=90.0,   help="위상각 [deg]")
    ap.add_argument("--mot",     default=MOT_PATH,            help=".mot 경로")
    ap.add_argument("--json",    default=str(JSON_PATH),      help="대상 JSON 경로")
    ap.add_argument("--dry-run", action="store_true",         help="Motor-CAD 없이 기존 데이터 확인만")
    args = ap.parse_args()

    speed = args.speed; current = args.current; phase = args.phase

    print(f"=== SC FEA 재계산: {speed:.0f}rpm / {current}Arms / {phase}° ===")
    print(f"    .mot : {args.mot}")
    print(f"    JSON : {args.json}")

    # 기존 데이터 확인
    with open(args.json) as f:
        db = json.load(f)
    records = db.get("records", db) if isinstance(db, dict) else db

    existing = [r for r in records
                if abs(r.get("speed",0)-speed)<1 and
                   abs(r.get("current",0)-current)<1 and
                   abs(r.get("phase",0)-phase)<1]
    if existing:
        print(f"\n기존 레코드 {len(existing)}개:")
        for r in existing:
            mode = r.get("mode","?")
            if mode == "Hybrid":
                print(f"  [Hybrid]  hybrid_total = {r.get('hybrid_total_kW',0)*1000:.2f} W")
            else:
                print(f"  [FullFEA] fea_total_ac = {r.get('fea_total_ac_kW',0)*1000:.2f} W")
        if len(existing) == 2:
            hyb_r = next((r for r in existing if r['mode']=='Hybrid'), None)
            fea_r = next((r for r in existing if r['mode']=='FullFEA'), None)
            if hyb_r and fea_r and hyb_r.get('hybrid_total_kW',0) > 0:
                af = fea_r.get('fea_total_ac_kW',0) / hyb_r['hybrid_total_kW']
                print(f"  AF = FullFEA/Hybrid = {af:.4f}  ← {'⚠️ 이상치!' if af < 0.5 else '정상'}")
    else:
        print("  기존 레코드 없음")

    if args.dry_run:
        print("\n[dry-run] Motor-CAD 실행 없이 종료.")
        return

    if not Path(args.mot).exists():
        print(f"\n❌ .mot 파일 없음: {args.mot}")
        sys.exit(1)

    # Motor-CAD 연결
    print("\nMotor-CAD 연결 중...")
    try:
        import ansys.motorcad.core as pymotorcad
    except ImportError:
        print("❌ ansys-motorcad 패키지 없음. pip install ansys-motorcad 후 재실행.")
        sys.exit(1)

    mcad = pymotorcad.MotorCAD(enable_success_variable=False)
    try:
        mcad.set_variable("MessageDisplayState", 2)
    except Exception:
        pass
    mcad.load_from_file(args.mot)
    print(f"✅ 로드: {args.mot}")

    # 백업 디렉터리
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    # Hybrid 계산
    print(f"\n[1/2] Hybrid 계산 ({speed}rpm/{current}A/{phase}°)...")
    hyb_result = run_hybrid(mcad, speed, current, phase)
    print(f"  → Hybrid AC = {hyb_result['hybrid_total_kW']*1000:.1f} W")

    # FullFEA 계산
    print(f"\n[2/2] FullFEA 계산 ({speed}rpm/{current}A/{phase}°)...")
    fea_result = run_fullfea(mcad, speed, current, phase)
    print(f"  → FullFEA AC = {fea_result['fea_total_ac_kW']*1000:.1f} W")
    af_new = fea_result['fea_total_ac_kW'] / hyb_result['hybrid_total_kW']
    print(f"  → AF_new = {af_new:.4f}")

    mcad.quit()
    print("\nMotor-CAD 종료")

    # JSON 업데이트
    update_json(Path(args.json), hyb_result, fea_result, speed, current, phase)

    print("\n=== 다음 단계 ===")
    print("  python verify_af_data_quality.py  → LOOCV 재확인")
    print("  (SC 4.69% → ~2.3% 개선 예상)")


if __name__ == "__main__":
    main()
