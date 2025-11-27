"""Parametric Batch Processor for Maxwell 2D

강건한 AEDT 파일 일괄 처리 루프를 함수화한 모듈.

주요 기능:
    - 여러 프로젝트(.aedt) 순회
    - 필요한 Excitation 존재/설정 확인
    - Parametric Setup 검증/생성/재생성
    - 결과 CSV 검증 및 불완전 시 재실행
    - 처리 결과 요약 반환 (list 또는 DataFrame)

사용 예시:
    from parametric_batch_processor import process_parametric_projects
    results = process_parametric_projects(
        m2d_obj=m2d,
        file_paths=file_paths,
        setup_name="ParametricSetup1",
        ipeak_steps=5,
        phase_steps=6,
        limit=10,
        recreate_incomplete=True,
        verbose=True
    )

주의:
    - Excitation 이름 'WG_Ph1_P1', 'WG_Ph2_P1', 'WG_Ph3_P1' 에 맞춰짐.
    - Parametric Sweep 변수 IPeak, PhaseAdvance 고정 패턴.
    - CSV 파일명 규칙: <project>_<setup_name>_Result.csv

Author: KangDH (refactored by Copilot)
Date: 2025-11-25
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pandas as pd  # Optional; results DataFrame 용
except ImportError:  # pragma: no cover
    pd = None


def _validate_csv(m2d_obj, setup_name: str, ipeak_steps: int, phase_steps: int, verbose: bool):
    """Wrapper for external validator if available; fallback to minimal check."""
    try:
        from aedt_csv_validator import validate_and_display_csv  # type: ignore
        return validate_and_display_csv(
            m2d_obj=m2d_obj,
            setup_name=setup_name,
            expected_ipeak_steps=ipeak_steps,
            expected_phase_steps=phase_steps,
            verbose=verbose,
        )
    except Exception:
        # Fallback: just check file existence.
        aedt_path = Path(m2d_obj.project_path)
        csv_path = aedt_path.parent / f"{aedt_path.stem}_{setup_name}_Result.csv"
        return {
            "csv_exists": csv_path.exists(),
            "is_complete": False,
            "actual_count": 0,
            "expected_count": ipeak_steps * phase_steps,
            "completion_rate": 0.0,
            "path": str(csv_path),
        }


def _ensure_parametric_setup(oModule, setup_name: str, ipeak_steps: int, phase_steps: int, verbose: bool) -> None:
    """Create or validate parametric setup; recreate if mismatch."""
    existing_setups = oModule.GetChildNames()
    expected_config = {
        "IPeak": f"LINC 10A 650.53A {ipeak_steps}",
        "PhaseAdvance": f"LINC 0deg 90deg {phase_steps}",
    }
    if setup_name not in existing_setups:
        if verbose:
            print(f"  📝 Parametric Setup 생성: {setup_name}")
        _insert_parametric(oModule, setup_name, expected_config, verbose)
        return

    # validate existing
    try:
        cursimul = oModule.GetChildObject(setup_name)
        sweep_vars = cursimul.GetSweepVariables()
        mismatch = False
        if set(sweep_vars) != set(expected_config.keys()):
            mismatch = True
        else:
            for var in sweep_vars:
                data = cursimul.GetSweepData(var).replace(" ", "").upper()
                exp = expected_config[var].replace(" ", "").upper()
                if data != exp:
                    mismatch = True
                    break
        if mismatch:
            if verbose:
                print("  ⚠️ Setup 불일치 → 재생성")
            oModule.DeleteSetups([setup_name])
            _insert_parametric(oModule, setup_name, expected_config, verbose)
        else:
            if verbose:
                print("  ✅ Parametric Setup 설정 검증 통과")
    except Exception as e:  # recreate on unexpected failure
        if verbose:
            print(f"  ⚠️ 검증 실패, 재생성 시도: {e}")
        try:
            oModule.DeleteSetups([setup_name])
        except Exception:
            pass
        _insert_parametric(oModule, setup_name, expected_config, verbose)


def _insert_parametric(oModule, setup_name: str, config: Dict[str, str], verbose: bool) -> None:
    sweeps = []
    for var, data in config.items():
        sweeps.append([
            "NAME:SweepDefinition",
            "Variable:=", var,
            "Data:=", data,
            "OffsetF1:=", False,
            "Synchronize:=", 0,
        ])
    oModule.InsertSetup("OptiParametric",
        [
            f"NAME:{setup_name}",
            "IsEnabled:=", True,
            ["NAME:ProdOptiSetupDataV2", "SaveFields:=", True, "CopyMesh:=", False, "SolveWithCopiedMeshOnly:=", False],
            "InterpolationPoints:=", 0,
            ["NAME:StartingPoint"],
            "Sim. Setups:=", ["Setup1"],
            ["NAME:Sweeps"] + sweeps,
            ["NAME:Sweep Operations"],
            ["NAME:Goals"],
        ])
    if verbose:
        print("  ✅ Parametric Setup 생성/재생성 완료")


def _configure_excitations(m2d_obj, verbose: bool) -> None:
    required = ['WG_Ph1_P1', 'WG_Ph2_P1', 'WG_Ph3_P1']
    excits = m2d_obj.excitation_objects
    missing = [n for n in required if n not in excits]
    if missing:
        raise KeyError(f"필수 Excitation 누락: {missing}")
    ph1 = excits['WG_Ph1_P1']
    ph2 = excits['WG_Ph2_P1']
    ph3 = excits['WG_Ph3_P1']
    ph_currents = {
        ph1: 'IPeak  * sin(MachineRPM/1rpm*NumPoles/60*pi*time+PhaseAdvance-0deg+0)',
        ph2: 'IPeak  * sin(MachineRPM/1rpm*NumPoles/60*pi*time+PhaseAdvance-120deg+0)',
        ph3: 'IPeak  * sin(MachineRPM/1rpm*NumPoles/60*pi*time+PhaseAdvance-240deg+0)',
    }
    for obj, expr in ph_currents.items():
        obj.update_property(prop_name='Current', prop_value=expr)
    if verbose:
        print("  ✅ Excitation 설정 완료 (3-phase)")


def _export_csv(oModule, setup_name: str, m2d_obj, verbose: bool) -> Path:
    aedt_path = Path(m2d_obj.project_path)
    csv_path = aedt_path.parent / f"{aedt_path.stem}_{setup_name}_Result.csv"
    oModule.ExportOptimetricsResult(setup_name, str(csv_path), False)
    if verbose:
        print(f"  ✅ CSV Export 완료: {csv_path.name}")
    return csv_path


def process_parametric_projects(
    m2d_obj,
    file_paths: List[str],
    setup_name: str = "ParametricSetup1",
    ipeak_steps: int = 5,
    phase_steps: int = 6,
    recreate_incomplete: bool = True,
    limit: Optional[int] = None,
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    """Process multiple AEDT projects ensuring parametric results completeness.

    Parameters
    ----------
    m2d_obj : Maxwell2d
        Active Maxwell2d object (will be reused and project switched).
    file_paths : list[str]
        AEDT file paths.
    setup_name : str
        Parametric setup name (default 'ParametricSetup1').
    ipeak_steps : int
        Expected IPeak sweep steps.
    phase_steps : int
        Expected PhaseAdvance sweep steps.
    recreate_incomplete : bool
        If True, incomplete CSV triggers setup deletion + rerun.
    limit : int | None
        Optional max number of files to process.
    verbose : bool
        Print progress.

    Returns
    -------
    list[dict]
        Per-file processing summary.
    """
    results = []
    total = len(file_paths) if limit is None else min(len(file_paths), limit)
    for idx, fpath in enumerate(file_paths[:total], 1):
        fname = Path(fpath).name
        if verbose:
            print("\n" + "=" * 80)
            print(f"[{idx}/{total}] 📁 {fname}")
            print("=" * 80)
        try:
            # Switch project if different
            current = Path(m2d_obj.project_path).resolve()
            target = Path(fpath).resolve()
            if current != target:
                if verbose:
                    print("  📂 프로젝트 전환 중...")
                try:
                    m2d_obj.close_project()
                except Exception:
                    pass
                m2d_obj.load_project(str(target))
                if verbose:
                    print("  ✅ 프로젝트 로드 완료")
            else:
                if verbose:
                    print("  ✅ 이미 올바른 프로젝트 열림")

            # Excitations
            if verbose:
                print("\n⚡ Excitation 확인/설정")
            _configure_excitations(m2d_obj, verbose)

            # Parametric setup ensure
            if verbose:
                print("\n🔧 Parametric Setup 검증")
            param = m2d_obj.parametrics
            oModule = param.optimodule
            _ensure_parametric_setup(oModule, setup_name, ipeak_steps, phase_steps, verbose)

            # CSV validation
            if verbose:
                print("\n📊 CSV 결과 검증")
            val = _validate_csv(m2d_obj, setup_name, ipeak_steps, phase_steps, verbose=False)
            csv_exists = val.get("csv_exists", False)
            is_complete = val.get("is_complete", False)
            completion_rate = val.get("completion_rate", 0.0)

            if verbose:
                print(f"  - CSV 존재: {'✅' if csv_exists else '❌'} / 완성도: {completion_rate:.1f}%")

            # Incomplete handling
            if (not is_complete) and recreate_incomplete:
                if verbose:
                    print("\n🔄 불완전 결과 재실행 준비")
                # Delete setup & recreate (already validated earlier, but ensure fresh run)
                try:
                    oModule.DeleteSetups([setup_name])
                except Exception:
                    pass
                _ensure_parametric_setup(oModule, setup_name, ipeak_steps, phase_steps, verbose)
                if verbose:
                    print("  ▶ Sweep 실행 시작 (시간 소요) ...")
                cursimul = oModule.GetChildObject(setup_name)
                cursimul.StartAnalyze()
                if verbose:
                    print("  ✅ Sweep 실행 완료")
                csv_path = _export_csv(oModule, setup_name, m2d_obj, verbose)
                # Re-validate
                val2 = _validate_csv(m2d_obj, setup_name, ipeak_steps, phase_steps, verbose=False)
                is_complete = val2.get("is_complete", False)
                completion_rate = val2.get("completion_rate", 0.0)
            else:
                if not is_complete and verbose:
                    print("  ℹ️ 재실행 비활성화(recreate_incomplete=False)")

            results.append({
                "file": fname,
                "path": str(fpath),
                "csv_exists": csv_exists,
                "is_complete": is_complete,
                "completion_rate": completion_rate,
            })
        except Exception as e:
            if verbose:
                print(f"\n❌ 처리 실패: {e}")
            results.append({
                "file": fname,
                "path": str(fpath),
                "error": str(e),
                "is_complete": False,
                "completion_rate": 0.0,
            })
            continue

    if pd and results:
        try:
            df = pd.DataFrame(results)
            if verbose:
                print("\n" + "=" * 80)
                print("📊 처리 결과 요약 (DataFrame)")
                print("=" * 80)
                print(df.head())
        except Exception:
            pass
    return results


__all__ = ["process_parametric_projects"]
