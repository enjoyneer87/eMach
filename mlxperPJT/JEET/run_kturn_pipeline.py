#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_kturn_pipeline.py
=====================
헤어핀 턴수(WindingLayers) sweep용 **헤드리스 통합 파이프라인**.

서버에서 Jupyter 없이 한 줄로 전체 파이프라인을 실행한다:

    python run_kturn_pipeline.py --base-mot e10Turn6V261.mot --turns 4 6 8 --output-dir ./kturn_results

수행 단계
---------
[Stage 1] .mot 생성  (gen_e10_hairpin_turns.py 로직 재사용)
    기준(예: 6턴) .mot 을 열어, 지정한 각 턴수마다
      - WindingLayers 변경 → 형상 재계산
      - 점적율 보존 copper 사이징 (calcConductorSize.m 이식 = calc_conductor_size)
      - e10Turn<N>V261.mot 로 저장

[Stage 2] AC 손실 맵 sweep  (pyMotorCAD_Hybrid_AClossCode_Template.ipynb 로직 재사용)
    각 .mot 에 대해 (proximity_model x speed x current x phase) 격자를 sweep.
      - Hybrid(1)  : ACLoss_Hybrid_Total/Prox/Skin
      - FullFEA(3) : per-turn 합 - DC 차감 = ts_ac_active_only_kW
    → eMach `+mcad/loadAcLossJson.m` 호환 JSON 으로 저장
      ({"_meta": {...}, "records": [...]}, 레코드에 hybrid_total_kW 등 포함)

AC 손실 계산 자체는 검증된 `_mcad_parallel_worker.run_sweep_point` 를 그대로
호출하므로 노트북 결과와 동일한 레코드 포맷/수식을 보장한다.

환경
----
- Motor-CAD 설치 + COM/RPC 사용 가능
- pyMotorEnv_310 venv (ansys-motorcad, pywin32, numpy, scipy)
  자세한 패키지는 requirements_kturn.txt 참조

출력 레이아웃 (예: --output-dir ./kturn_results)
-----------------------------------------------
    kturn_results/
      e10Turn4V261.mot                       # Stage1 생성물
      e10Turn8V261.mot
      kturn4/
        JEET_ACLoss_kturn4_Map_Summary.json  # eMach loadAcLossJson 호환
        JEET_ACLoss_kturn4_Map_Summary.mat
        ACLossCalcExport_kturn4/...           # FEA 결과 백업
      kturn8/
        ...
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# 경로 설정: eMach repo root 를 sys.path 에 추가
#   - tools.motorCAD.pyMCAD (calc_dc_loss_kw, get_fea_src_dir) import
#   - _mcad_parallel_worker (run_sweep_point) import (이 파일과 같은 JEET 폴더)
# ──────────────────────────────────────────────────────────────────────────────
_THIS_DIR = Path(__file__).resolve().parent              # .../eMach/mlxperPJT/JEET
_EMACH_ROOT = _THIS_DIR.parents[1]                       # .../eMach
_FIGURES_DIR = _THIS_DIR / "figures"
for _p in (str(_EMACH_ROOT), str(_THIS_DIR), str(_FIGURES_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 의존성: 점적율 보존 copper 사이징
#   gen_e10_hairpin_turns.calc_conductor_size 를 우선 재사용(DRY).
#   win32com 미설치 등으로 import 실패 시 동일 로직의 로컬 사본으로 폴백.
#   (로컬 사본은 gen_e10_hairpin_turns.py / SkkuEMLabProject\calcConductorSize.m 의
#    '교정판' 공식과 동일하게 유지할 것.)
# ──────────────────────────────────────────────────────────────────────────────
try:
    from gen_e10_hairpin_turns import calc_conductor_size  # type: ignore
    _CALC_SRC = "gen_e10_hairpin_turns.calc_conductor_size"
except Exception as _imp_err:  # pragma: no cover - 폴백 경로
    _CALC_SRC = f"local fallback (import 실패: {_imp_err})"

    def calc_conductor_size(geom, new_N, target_ff_pct):
        """점적율 보존 copper 치수 계산 (gen_e10_hairpin_turns.py 이식 폴백)."""
        Area_Slot = geom["Area_Slot"]
        Area_WdgL = geom["Area_Wdg_Liner"]
        Slot_Width = geom["Slot_Width"]
        Wdg_Depth = geom["Winding_Depth"]
        Liner = geom["Liner"]
        Insul = geom["Insul"]
        Sep = geom["Separation"]

        effective_ff = Area_Slot * target_ff_pct / Area_WdgL
        eff_slot_area = Area_WdgL * (effective_ff / 100.0)
        turn_area = eff_slot_area / new_N

        Copper_W = Slot_Width - 2 * Liner - 2 * Insul - 2 * Sep
        Copper_H = turn_area / Copper_W

        max_H = (Wdg_Depth - 2 * new_N * Insul - (new_N + 1) * Sep) / new_N
        clamped = False
        if Copper_H > max_H:
            Copper_H = max_H
            clamped = True

        return {
            "Copper_W": Copper_W,
            "Copper_H": Copper_H,
            "turn_area": turn_area,
            "effective_ff": effective_ff,
            "max_H": max_H,
            "clamped": clamped,
        }


# ══════════════════════════════════════════════════════════════════════════════
# Motor-CAD I/O 어댑터 (ansys.motorcad.core, snake_case API)
#   gen 스크립트는 win32com COM(PascalCase) 을 쓰지만, 본 파이프라인은
#   노트북/워커와 동일한 ansys.motorcad.core 를 사용해 일관성을 유지한다.
# ══════════════════════════════════════════════════════════════════════════════

def _get_num(mc, name, default=None):
    """숫자 변수 읽기 (실패 시 default)."""
    try:
        v = mc.get_variable(name)
        if isinstance(v, (list, tuple)):
            v = v[-1]
        return float(v)
    except Exception:
        return default


def _recompute_geometry(mc):
    """형상 재계산/검증 (슬롯 면적 등 출력변수 갱신). 메서드명 호환 처리."""
    for meth in ("check_if_geometry_is_valid",):
        fn = getattr(mc, meth, None)
        if fn is not None:
            try:
                return fn(1)
            except Exception as e:
                print(f"  [warn] {meth} 실패: {e}")
                return None
    return None


def _read_geom(mc):
    """헤어핀 권선/슬롯 형상 파라미터 읽기 (v261 변수명)."""
    return {
        "Ncond": int(_get_num(mc, "WindingLayers", 0) or 0),
        "Copper_W": _get_num(mc, "Copper_Width"),
        "Copper_H": _get_num(mc, "Copper_Height"),
        "Slot_Width": _get_num(mc, "Slot_Width"),
        "Liner": _get_num(mc, "Liner_Thickness", 0.0) or 0.0,
        "Insul": _get_num(mc, "Insulation_Thickness", 0.0) or 0.0,
        "Separation": _get_num(mc, "ConductorSeparation", 0.0) or 0.0,
        "Area_Slot": _get_num(mc, "Area_Slot"),
        "Area_Wdg_Liner": _get_num(mc, "Area_Winding_With_Liner"),
        "Winding_Depth": _get_num(mc, "Winding_Depth"),
        "GrossFill": _get_num(mc, "GrossSlotFillFactor"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Stage 1 : 턴수별 .mot 생성
# ══════════════════════════════════════════════════════════════════════════════

def generate_turn_mots(base_mot: Path, turns, base_turns: int, out_dir: Path,
                       name_template: str = "e10Turn{N}V261.mot"):
    """
    기준 .mot 에서 각 턴수(WindingLayers)로 변환된 .mot 파일을 생성한다.

    Returns: dict {turn -> Path(.mot)}  (생성 성공한 것만)
    """
    import ansys.motorcad.core as pymotorcad

    print("=" * 70)
    print("  [Stage 1] 턴수별 .mot 생성")
    print(f"    기준 파일 : {base_mot}  (기준 {base_turns}턴)")
    print(f"    대상 턴수 : {list(turns)}")
    print(f"    사이징    : 점적율 보존 ({_CALC_SRC})")
    print("=" * 70)

    if not base_mot.exists():
        raise FileNotFoundError(f"기준 .mot 파일이 없습니다: {base_mot}")

    out_dir.mkdir(parents=True, exist_ok=True)

    mc = pymotorcad.MotorCAD(open_new_instance=True, enable_success_variable=False)
    try:
        mc.set_variable("MessageDisplayState", 2)  # 헤드리스: GUI 팝업 억제
    except Exception:
        pass

    generated: dict[int, Path] = {}
    try:
        # 기준 모델로부터 목표 점적율 산출
        mc.load_from_file(str(base_mot))
        _recompute_geometry(mc)
        base = _read_geom(mc)

        required = ["Slot_Width", "Area_Slot", "Area_Wdg_Liner",
                    "Winding_Depth", "GrossFill"]
        missing = [k for k in required if base.get(k) in (None, 0)]
        if missing:
            raise RuntimeError(
                f"기준 모델에서 필수 변수를 읽지 못했습니다: {missing} "
                f"(변수명/형상 유효성 확인 필요)")

        gross = base["GrossFill"]
        target_ff_pct = gross * 100.0 if gross <= 1.0 else gross
        print(f"  목표 copper 점적율(고정): {target_ff_pct:.3f} %  (기준 모델값)\n")

        for new_N in turns:
            out_path = out_dir / name_template.format(N=new_N)

            # 기준 == 대상 턴수: 사이징 없이 그대로 복사 (기준점 보존)
            if int(new_N) == int(base_turns):
                shutil.copy2(str(base_mot), str(out_path))
                print(f"  [턴 {new_N}] 기준과 동일 → 복사: {out_path.name}")
                generated[int(new_N)] = out_path
                continue

            print(f"  [턴 {new_N}] 변환 중...")
            mc.load_from_file(str(base_mot))           # 매번 기준에서 재시작
            mc.set_variable("WindingLayers", int(new_N))
            _recompute_geometry(mc)

            applied = _get_num(mc, "WindingLayers")
            if applied is None or int(applied) != int(new_N):
                print(f"    [오류] WindingLayers 적용 실패 (={applied}) → 건너뜀")
                continue

            geom = _read_geom(mc)
            r = calc_conductor_size(geom, int(new_N), target_ff_pct)
            print(f"    Copper_W : {geom['Copper_W']:.4f} → {r['Copper_W']:.4f} mm")
            print(f"    Copper_H : {geom['Copper_H']:.4f} → {r['Copper_H']:.4f} mm")
            if r["clamped"]:
                print(f"    [주의] 높이가 Winding_Depth 상한({r['max_H']:.4f} mm)으로 클램프 "
                      f"→ 목표 점적율 미달 가능")

            mc.set_variable("Copper_Width", float(r["Copper_W"]))
            mc.set_variable("Copper_Height", float(r["Copper_H"]))
            _recompute_geometry(mc)

            new_fill = _get_num(mc, "GrossSlotFillFactor")
            print(f"    실제 점적율 : {new_fill}  (목표 {target_ff_pct / 100:.4f})")

            mc.save_to_file(str(out_path))
            if out_path.exists():
                kb = out_path.stat().st_size / 1024
                print(f"    ✓ 저장: {out_path}  ({kb:.1f} KB)")
                generated[int(new_N)] = out_path
            else:
                print(f"    [오류] 저장 실패: {out_path}")
    finally:
        try:
            mc.quit()
        except Exception:
            pass

    print(f"\n  [Stage 1 완료] 생성 {len(generated)}/{len(list(turns))}개")
    return generated


# ══════════════════════════════════════════════════════════════════════════════
# Stage 2 : .mot 별 AC 손실 sweep
# ══════════════════════════════════════════════════════════════════════════════

def _build_schedule(proximity_models, speeds, currents, phases):
    """(proximity_model x speed x current x phase) 전체 스케줄 생성."""
    base_2d = [(float(I), float(g)) for I in currents for g in phases]
    schedule = [
        {"proximity_model": pm, "speed": int(s), "current": I, "phase": g}
        for pm in proximity_models
        for s in speeds
        for (I, g) in base_2d
    ]
    return schedule, base_2d


def _make_meta(proximity_models, speeds, currents, phases, n_schedule):
    return {
        "proximity_models": list(proximity_models),
        "speeds": list(speeds),
        "current_grid": [float(x) for x in currents],
        "phase_grid": [float(x) for x in phases],
        "design_2d_strategy": "full",
        "n_curr_design": len(currents),
        "n_phase_design": len(phases),
        "total_schedule": n_schedule,
        "last_updated": datetime.now().isoformat(),
    }


def _is_point_existing(records, p_model, spd, curr, ph, force_resweep):
    """이미 유효 결과가 있는 운전점인지 (resume용)."""
    if p_model in force_resweep:
        return False
    required = {1: {"hybrid_total_kW"}, 3: {"fea_total_ac_kW"}}.get(p_model, set())
    for r in records:
        if (r.get("proximity_model") == p_model
                and r.get("speed") == spd
                and np.isclose(r.get("current", -1), curr, atol=1e-2)
                and np.isclose(r.get("phase", -1), ph, atol=1e-2)
                and required.issubset(r.keys())):
            return True
    return False


def sweep_one_mot(mot_path: Path, turn: int, out_dir: Path,
                  proximity_models, speeds, currents, phases,
                  sessions: int = 1, force_resweep=(), first_step: int = 1,
                  export_columns: str = "RegCode,Bx,By,A,J,Je,Hx,Hy,Mur"):
    """
    하나의 .mot 에 대해 AC 손실 sweep 실행 → eMach 호환 JSON 저장.

    Returns: Path(json_summary)
    """
    from scipy.io import savemat

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"JEET_ACLoss_kturn{turn}_Map_Summary.json"
    mat_path = out_dir / f"JEET_ACLoss_kturn{turn}_Map_Summary.mat"
    backup_root = out_dir / f"ACLossCalcExport_kturn{turn}"
    backup_root.mkdir(parents=True, exist_ok=True)

    schedule, _ = _build_schedule(proximity_models, speeds, currents, phases)
    meta = _make_meta(proximity_models, speeds, currents, phases, len(schedule))

    print("\n" + "=" * 70)
    print(f"  [Stage 2] AC 손실 sweep — 턴 {turn}")
    print(f"    .mot   : {mot_path}")
    print(f"    출력   : {json_path}")
    print(f"    스케줄 : {len(schedule)}점 "
          f"({len(proximity_models)} models x {len(speeds)} speeds x "
          f"{len(currents)} curr x {len(phases)} phase)")
    print("=" * 70)

    # ── 기존 진행분 로드 (resume) ─────────────────────────────────────────────
    records: list[dict] = []
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            records = loaded.get("records", []) if isinstance(loaded, dict) else loaded
            meta.update(loaded.get("_meta", {}) if isinstance(loaded, dict) else {})
            print(f"  기존 레코드 {len(records)}개 로드 → resume")
        except Exception as e:
            print(f"  [warn] 기존 JSON 로드 실패({e}) → 새로 시작")
            records = []

    pending = [
        (idx, pt) for idx, pt in enumerate(schedule)
        if not _is_point_existing(records, pt["proximity_model"], pt["speed"],
                                  pt["current"], pt["phase"], force_resweep)
    ]
    print(f"  대기(pending): {len(pending)}/{len(schedule)}점")
    if not pending:
        print("  → 모든 점 완료됨. 새 계산 없음.")
        _save_summary(json_path, mat_path, meta, records, savemat)
        return json_path

    args_list = [
        {
            "prox_model": pt["proximity_model"],
            "speed": pt["speed"],
            "current": pt["current"],
            "phase": pt["phase"],
            "backup_root": str(backup_root),
            "first_step": first_step,
            "export_columns": export_columns,
            "idx": idx,
            "total_pts": len(schedule),
        }
        for idx, pt in pending
    ]

    if sessions and sessions > 1:
        _sweep_parallel(mot_path, args_list, records, meta,
                        json_path, mat_path, sessions, savemat)
    else:
        _sweep_sequential(mot_path, args_list, records, meta,
                          json_path, mat_path, savemat)

    print(f"\n  [턴 {turn} 완료] 총 {len(records)}개 레코드")
    print(f"    JSON: {json_path}")
    print(f"    MAT : {mat_path}")
    return json_path


def _save_summary(json_path, mat_path, meta, records, savemat):
    meta["last_updated"] = datetime.now().isoformat()
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"_meta": meta, "records": records}, f,
                  ensure_ascii=False, indent=2)
    try:
        savemat(str(mat_path), {"sweep_results": records}, do_compression=True)
    except Exception as e:
        print(f"  [warn] .mat 저장 실패: {e}")


def _sweep_sequential(mot_path, args_list, records, meta,
                      json_path, mat_path, savemat):
    """단일 인스턴스 순차 sweep (in-process). 검증된 워커 함수 재사용."""
    import _mcad_parallel_worker as worker

    worker.initialise_mcad(str(mot_path), sys.path[:])
    try:
        for n, args in enumerate(args_list, 1):
            result = worker.run_sweep_point(args)
            if result is not None:
                records.append(result)
                _save_summary(json_path, mat_path, meta, records, savemat)  # 증분 저장
                print(f"    [{n}/{len(args_list)}] ok "
                      f"{result.get('mode')} {result.get('speed')}RPM "
                      f"{result.get('current', 0):.1f}A {result.get('phase', 0):.1f}deg")
            else:
                print(f"    [{n}/{len(args_list)}] FAILED (worker stderr 참조)")
    finally:
        try:
            worker.close_mcad(0)
        except Exception:
            pass


def _sweep_parallel(mot_path, args_list, records, meta,
                    json_path, mat_path, sessions, savemat):
    """다중 Motor-CAD 인스턴스 병렬 sweep (노트북 Cell 7 패턴)."""
    from multiprocessing import Pool
    import _mcad_parallel_worker as worker  # noqa: F401  (import 가능성 확인)

    n_workers = min(sessions, max(len(args_list), 1))
    print(f"  병렬 모드: {n_workers} Motor-CAD 세션")

    pool = Pool(
        processes=n_workers,
        initializer=_pool_initializer,
        initargs=(str(mot_path), sys.path[:]),
    )
    n_done = 0
    try:
        for result in pool.imap_unordered(_pool_run_point, args_list):
            n_done += 1
            if result is not None:
                records.append(result)
                _save_summary(json_path, mat_path, meta, records, savemat)
                print(f"    [{n_done}/{len(args_list)}] ok "
                      f"{result.get('mode')} {result.get('speed')}RPM "
                      f"{result.get('current', 0):.1f}A {result.get('phase', 0):.1f}deg")
            else:
                print(f"    [{n_done}/{len(args_list)}] FAILED (worker stderr 참조)")
    finally:
        it = pool.imap(_pool_close, range(n_workers))
        for _ in range(n_workers):
            try:
                next(it)
            except Exception:
                pass
        pool.close()
        pool.join()


# multiprocessing 'spawn' 이 import 가능하도록 모듈 최상위 래퍼 정의
def _pool_initializer(base_mot, paths):
    from _mcad_parallel_worker import initialise_mcad
    initialise_mcad(base_mot, paths)


def _pool_run_point(args):
    from _mcad_parallel_worker import run_sweep_point
    return run_sweep_point(args)


def _pool_close(dummy):
    from _mcad_parallel_worker import close_mcad
    return close_mcad(dummy)


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def _parse_args(argv=None):
    pa = argparse.ArgumentParser(
        description="헤어핀 턴수 sweep: .mot 생성 + AC 손실 맵 헤드리스 파이프라인",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    pa.add_argument("--base-mot", required=True,
                    help="기준 .mot 파일 경로 (예: e10Turn6V261.mot)")
    pa.add_argument("--base-turns", type=int, default=6,
                    help="기준 .mot 의 턴수(WindingLayers)")
    pa.add_argument("--turns", type=int, nargs="+", required=True,
                    help="생성/계산할 대상 턴수 목록 (예: --turns 4 6 8)")
    pa.add_argument("--output-dir", default="./kturn_results",
                    help="출력 루트 디렉토리")
    pa.add_argument("--name-template", default="e10Turn{N}V261.mot",
                    help="생성 .mot 파일명 템플릿 ({N}=턴수)")

    # sweep 격자
    pa.add_argument("--speeds", type=int, nargs="+",
                    default=[2000, 4000, 8000, 16000], help="속도 목록 [RPM]")
    pa.add_argument("--currents", type=float, nargs="+", default=None,
                    help="RMS 전류 목록 [A]. 미지정 시 --current-max/--n-currents 로 생성")
    pa.add_argument("--current-max", type=float, default=250.0,
                    help="--currents 미지정 시 전류 격자 최대값 [A]")
    pa.add_argument("--current-min", type=float, default=0.1,
                    help="--currents 미지정 시 전류 격자 최소값 [A]")
    pa.add_argument("--n-currents", type=int, default=5,
                    help="--currents 미지정 시 전류 격자 점 수")
    pa.add_argument("--phases", type=float, nargs="+", default=None,
                    help="위상각(PhaseAdvance) 목록 [deg]. 미지정 시 --n-phases 로 0~90 생성")
    pa.add_argument("--n-phases", type=int, default=6,
                    help="--phases 미지정 시 0~90deg 격자 점 수")
    pa.add_argument("--proximity-models", type=int, nargs="+", default=[3, 1],
                    help="ProximityLossModel 목록 (1=Hybrid, 3=FullFEA)")
    pa.add_argument("--force-resweep", type=int, nargs="*", default=[],
                    help="JSON 캐시 무시하고 재계산할 proximity_model (예: 3)")

    # 실행 제어
    pa.add_argument("--sessions", type=int, default=1,
                    help="병렬 Motor-CAD 세션 수 (1=순차 in-process, >1=multiprocessing Pool)")
    pa.add_argument("--skip-gen", action="store_true",
                    help="Stage 1(.mot 생성) 건너뛰기 (기존 .mot 사용)")
    pa.add_argument("--skip-sweep", action="store_true",
                    help="Stage 2(AC 손실 sweep) 건너뛰기 (.mot 만 생성)")
    return pa.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)

    base_mot = Path(args.base_mot).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()

    # 전류/위상 격자 구성
    if args.currents is not None:
        currents = [float(x) for x in args.currents]
    else:
        currents = [float(x) for x in
                    np.linspace(args.current_min, args.current_max, args.n_currents)]
    if args.phases is not None:
        phases = [float(x) for x in args.phases]
    else:
        phases = [float(x) for x in np.linspace(0.0, 90.0, args.n_phases)]

    print("#" * 70)
    print("#  JEET Kturn 통합 파이프라인")
    print(f"#  기준 .mot   : {base_mot}  ({args.base_turns}턴)")
    print(f"#  대상 턴수   : {args.turns}")
    print(f"#  출력        : {out_dir}")
    print(f"#  speeds      : {args.speeds}")
    print(f"#  currents    : {currents}")
    print(f"#  phases      : {phases}")
    print(f"#  prox models : {args.proximity_models}")
    print(f"#  sessions    : {args.sessions}")
    print(f"#  skip-gen={args.skip_gen}  skip-sweep={args.skip_sweep}")
    print("#" * 70)

    # ── Stage 1: .mot 생성 (또는 기존 파일 매핑) ─────────────────────────────
    if args.skip_gen:
        mot_map: dict[int, Path] = {}
        for t in args.turns:
            p = out_dir / args.name_template.format(N=t)
            if p.exists():
                mot_map[int(t)] = p
            else:
                print(f"[skip-gen] .mot 없음 → 턴 {t} 제외: {p}")
        if not mot_map:
            print("[오류] --skip-gen 인데 사용할 .mot 이 없습니다.")
            return 1
    else:
        mot_map = generate_turn_mots(
            base_mot, args.turns, args.base_turns, out_dir,
            name_template=args.name_template)
        if not mot_map:
            print("[오류] 생성된 .mot 이 없습니다. Stage 2 중단.")
            return 1

    # ── Stage 2: AC 손실 sweep ────────────────────────────────────────────────
    if args.skip_sweep:
        print("\n[skip-sweep] AC 손실 sweep 건너뜀. .mot 생성만 수행했습니다.")
        for t, p in sorted(mot_map.items()):
            print(f"  턴 {t}: {p}")
        return 0

    summaries = {}
    for t in sorted(mot_map):
        json_path = sweep_one_mot(
            mot_map[t], t, out_dir / f"kturn{t}",
            proximity_models=args.proximity_models,
            speeds=args.speeds, currents=currents, phases=phases,
            sessions=args.sessions, force_resweep=args.force_resweep,
        )
        summaries[t] = json_path

    print("\n" + "#" * 70)
    print("#  파이프라인 완료 — eMach loadAcLossJson 호환 요약 JSON:")
    for t, jp in sorted(summaries.items()):
        print(f"#    턴 {t}: {jp}")
    print("#" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
