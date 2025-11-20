"""
AEDT Parametric Sweep CSV 검증 함수

이 모듈은 AEDT Parametric Sweep 결과 CSV 파일을 검증하고 
결과를 시각화하는 함수를 제공합니다.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Union, Optional
from IPython.display import display


def validate_and_display_csv(
    m2d_obj,
    setup_name: str = "ParametricSetup1",
    expected_ipeak_steps: int = 5,
    expected_phase_steps: int = 6,
    verbose: bool = True
) -> Dict[str, any]:
    """
    AEDT Maxwell2d 객체로부터 Parametric Sweep CSV 결과를 검증하고 표시합니다.
    
    Parameters
    ----------
    m2d_obj : ansys.aedt.core.maxwell.Maxwell2d
        Maxwell2d 객체 (m2d.project_path를 통해 경로 추출)
    setup_name : str, optional
        Parametric Setup 이름 (기본값: "ParametricSetup1")
    expected_ipeak_steps : int, optional
        IPeak 변수의 예상 스텝 수 (기본값: 5)
    expected_phase_steps : int, optional
        PhaseAdvance 변수의 예상 스텝 수 (기본값: 6)
    verbose : bool, optional
        상세 출력 여부 (기본값: True)
    
    Returns
    -------
    Dict[str, any]
        검증 결과 정보:
        - 'is_complete': 완전한 결과 여부 (bool)
        - 'expected_count': 예상 결과 개수 (int)
        - 'actual_count': 실제 결과 개수 (int)
        - 'completion_rate': 완료율 (%) (float)
        - 'missing_count': 누락된 결과 개수 (int)
        - 'message': 결과 메시지 (str)
        - 'csv_exists': CSV 파일 존재 여부 (bool)
        - 'csv_path': CSV 파일 경로 (str)
        - 'df_result': 결과 DataFrame (pandas.DataFrame, CSV가 존재하는 경우)
    
    Examples
    --------
    >>> # Maxwell2d 객체로부터 검증
    >>> result = validate_and_display_csv(
    ...     m2d_obj=m2d,
    ...     setup_name="ParametricSetup1",
    ...     expected_ipeak_steps=5,
    ...     expected_phase_steps=6
    ... )
    >>> 
    >>> # 결과 확인
    >>> if result['is_complete']:
    ...     print("검증 성공!")
    ...     df = result['df_result']
    """
    from aedt_file_utils import validate_parametric_results
    
    # 현재 AEDT 파일 경로 추출
    current_aedt_path = m2d_obj.project_path
    aedt_dir = Path(current_aedt_path).parent
    aedt_filename = Path(current_aedt_path).stem
    
    # CSV 파일 경로 생성
    csv_filename = f"{aedt_filename}_{setup_name}_Result.csv"
    result_csv = str(aedt_dir / csv_filename)
    
    if verbose:
        print("\n" + "=" * 70)
        print("📊 CSV 파일 검증 시작")
        print("=" * 70)
        print(f"  - AEDT 파일: {Path(current_aedt_path).name}")
        print(f"  - CSV 파일: {csv_filename}")
        print(f"  - 경로: {aedt_dir}")
    
    # 검증 실행
    validation_result = validate_parametric_results(
        csv_path=result_csv,
        expected_ipeak_steps=expected_ipeak_steps,
        expected_phase_steps=expected_phase_steps,
        verbose=verbose
    )
    
    # CSV 경로 추가
    validation_result['csv_path'] = result_csv
    
    # 결과 확인
    if verbose:
        if validation_result['is_complete']:
            print(f"\n✅ {validation_result['message']}")
        else:
            print(f"\n⚠️ {validation_result['message']}")
            if validation_result['csv_exists'] and validation_result['missing_count'] > 0:
                print(f"   누락된 결과: {validation_result['missing_count']}개")
                print(f"   완료율: {validation_result['completion_rate']:.1f}%")
    
    # CSV 파일이 존재하면 미리보기 및 상세 분석
    if validation_result['csv_exists']:
        try:
            df_result = pd.read_csv(result_csv)
            validation_result['df_result'] = df_result
            
            if verbose:
                print(f"\n📄 CSV 파일 미리보기 (처음 5행):")
                display(df_result.head())
                
                # 변수 범위 확인
                if 'IPeak' in df_result.columns:
                    print(f"\n🔍 IPeak 범위:")
                    print(f"  - Min: {df_result['IPeak'].min():.2f}A")
                    print(f"  - Max: {df_result['IPeak'].max():.2f}A")
                    print(f"  - Unique values: {df_result['IPeak'].nunique()}개")
                    print(f"  - Values: {sorted(df_result['IPeak'].unique())}")
                
                if 'PhaseAdvance' in df_result.columns:
                    print(f"\n🔍 PhaseAdvance 범위:")
                    print(f"  - Min: {df_result['PhaseAdvance'].min():.2f}deg")
                    print(f"  - Max: {df_result['PhaseAdvance'].max():.2f}deg")
                    print(f"  - Unique values: {df_result['PhaseAdvance'].nunique()}개")
                    print(f"  - Values: {sorted(df_result['PhaseAdvance'].unique())}")
                
                print("\n" + "=" * 70)
        
        except Exception as e:
            if verbose:
                print(f"\n⚠️ CSV 파일 읽기 오류: {e}")
            validation_result['error'] = str(e)
    
    return validation_result


def validate_csv_from_path(
    csv_path: Union[str, Path],
    expected_ipeak_steps: int,
    expected_phase_steps: int,
    verbose: bool = True
) -> Dict[str, any]:
    """
    CSV 파일 경로로부터 직접 검증합니다.
    
    Parameters
    ----------
    csv_path : Union[str, Path]
        검증할 CSV 파일 경로
    expected_ipeak_steps : int
        IPeak 변수의 예상 스텝 수
    expected_phase_steps : int
        PhaseAdvance 변수의 예상 스텝 수
    verbose : bool, optional
        상세 출력 여부 (기본값: True)
    
    Returns
    -------
    Dict[str, any]
        검증 결과 정보 (validate_and_display_csv와 동일)
    
    Examples
    --------
    >>> # 직접 경로 지정하여 검증
    >>> result = validate_csv_from_path(
    ...     csv_path="E:/KDH/e10/e10_DOE/e10_DOE_ParametricSetup1_Result.csv",
    ...     expected_ipeak_steps=5,
    ...     expected_phase_steps=6
    ... )
    """
    from aedt_file_utils import validate_parametric_results
    
    csv_path = Path(csv_path)
    
    if verbose:
        print("\n" + "=" * 70)
        print("📊 CSV 파일 검증 시작")
        print("=" * 70)
        print(f"  - CSV 파일: {csv_path.name}")
        print(f"  - 경로: {csv_path.parent}")
    
    # 검증 실행
    validation_result = validate_parametric_results(
        csv_path=csv_path,
        expected_ipeak_steps=expected_ipeak_steps,
        expected_phase_steps=expected_phase_steps,
        verbose=verbose
    )
    
    # CSV 경로 추가
    validation_result['csv_path'] = str(csv_path)
    
    # CSV 파일이 존재하면 DataFrame 추가
    if validation_result['csv_exists']:
        try:
            df_result = pd.read_csv(csv_path)
            validation_result['df_result'] = df_result
            
            if verbose:
                print(f"\n📄 CSV 파일 미리보기 (처음 5행):")
                display(df_result.head())
                
                # 변수 범위 확인
                if 'IPeak' in df_result.columns:
                    print(f"\n🔍 IPeak 범위:")
                    print(f"  - Min: {df_result['IPeak'].min():.2f}A")
                    print(f"  - Max: {df_result['IPeak'].max():.2f}A")
                    print(f"  - Unique values: {df_result['IPeak'].nunique()}개")
                
                if 'PhaseAdvance' in df_result.columns:
                    print(f"\n🔍 PhaseAdvance 범위:")
                    print(f"  - Min: {df_result['PhaseAdvance'].min():.2f}deg")
                    print(f"  - Max: {df_result['PhaseAdvance'].max():.2f}deg")
                    print(f"  - Unique values: {df_result['PhaseAdvance'].nunique()}개")
                
                print("\n" + "=" * 70)
        
        except Exception as e:
            if verbose:
                print(f"\n⚠️ CSV 파일 읽기 오류: {e}")
            validation_result['error'] = str(e)
    
    return validation_result


def batch_validate_csv(
    aedt_files: list,
    setup_name: str = "ParametricSetup1",
    expected_ipeak_steps: int = 5,
    expected_phase_steps: int = 6,
    verbose: bool = False
) -> pd.DataFrame:
    """
    여러 AEDT 파일의 CSV 결과를 일괄 검증합니다.
    
    Parameters
    ----------
    aedt_files : list
        AEDT 파일 정보 리스트 (find_aedt_files 함수 반환값)
        각 항목은 'full_path', 'filename', 'directory' 키를 포함해야 함
    setup_name : str, optional
        Parametric Setup 이름 (기본값: "ParametricSetup1")
    expected_ipeak_steps : int, optional
        IPeak 변수의 예상 스텝 수 (기본값: 5)
    expected_phase_steps : int, optional
        PhaseAdvance 변수의 예상 스텝 수 (기본값: 6)
    verbose : bool, optional
        각 파일별 상세 출력 여부 (기본값: False)
    
    Returns
    -------
    pd.DataFrame
        검증 결과를 담은 DataFrame
        컬럼: aedt_file, csv_file, is_complete, expected, actual, 
              completion_rate, missing, status
    
    Examples
    --------
    >>> # 여러 AEDT 파일 일괄 검증
    >>> from aedt_file_utils import find_aedt_files
    >>> aedt_files = find_aedt_files(r"E:\KDH\e10\e10_DOE\e10_DOE.opd\AMOP")
    >>> 
    >>> results_df = batch_validate_csv(
    ...     aedt_files=aedt_files,
    ...     expected_ipeak_steps=5,
    ...     expected_phase_steps=6
    ... )
    >>> 
    >>> # 불완전한 결과만 필터링
    >>> incomplete = results_df[~results_df['is_complete']]
    >>> print(f"불완전한 결과: {len(incomplete)}개")
    """
    from aedt_file_utils import validate_parametric_results
    
    results = []
    
    print("\n" + "=" * 70)
    print(f"📊 일괄 CSV 검증 시작 ({len(aedt_files)}개 파일)")
    print("=" * 70)
    
    for i, file_info in enumerate(aedt_files, 1):
        aedt_path = Path(file_info['full_path'])
        aedt_dir = aedt_path.parent
        aedt_filename = aedt_path.stem
        
        # CSV 파일 경로 생성
        csv_filename = f"{aedt_filename}_{setup_name}_Result.csv"
        csv_path = str(aedt_dir / csv_filename)
        
        if verbose:
            print(f"\n[{i}/{len(aedt_files)}] {aedt_filename}")
        
        # 검증 실행
        validation_result = validate_parametric_results(
            csv_path=csv_path,
            expected_ipeak_steps=expected_ipeak_steps,
            expected_phase_steps=expected_phase_steps,
            verbose=False  # 일괄 처리에서는 개별 verbose 끄기
        )
        
        # 결과 수집
        results.append({
            'aedt_file': aedt_filename,
            'csv_file': csv_filename,
            'is_complete': validation_result['is_complete'],
            'expected': validation_result['expected_count'],
            'actual': validation_result['actual_count'],
            'completion_rate': validation_result['completion_rate'],
            'missing': validation_result['missing_count'],
            'csv_exists': validation_result['csv_exists'],
            'status': '✅ Complete' if validation_result['is_complete'] 
                     else '⚠️ Incomplete' if validation_result['csv_exists']
                     else '❌ No CSV'
        })
        
        if not verbose:
            # 간단한 진행 상황 표시
            status_symbol = '✅' if validation_result['is_complete'] else '⚠️' if validation_result['csv_exists'] else '❌'
            print(f"  [{i:3d}/{len(aedt_files)}] {status_symbol} {aedt_filename}")
    
    # DataFrame으로 변환
    df_results = pd.DataFrame(results)
    
    # 요약 통계
    print("\n" + "=" * 70)
    print("📈 검증 결과 요약")
    print("=" * 70)
    print(f"  총 파일: {len(df_results)}개")
    print(f"  ✅ 완전: {df_results['is_complete'].sum()}개")
    print(f"  ⚠️ 불완전: {(~df_results['is_complete'] & df_results['csv_exists']).sum()}개")
    print(f"  ❌ CSV 없음: {(~df_results['csv_exists']).sum()}개")
    print(f"  평균 완료율: {df_results['completion_rate'].mean():.1f}%")
    print("=" * 70)
    
    return df_results


if __name__ == "__main__":
    print("✅ AEDT CSV 검증 유틸리티 로드 완료")
    print("\n💡 사용 가능한 함수:")
    print("  - validate_and_display_csv(m2d_obj, ...): Maxwell2d 객체로부터 검증")
    print("  - validate_csv_from_path(csv_path, ...): CSV 경로로부터 직접 검증")
    print("  - batch_validate_csv(aedt_files, ...): 여러 파일 일괄 검증")
