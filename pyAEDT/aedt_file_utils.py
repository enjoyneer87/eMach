"""
AEDT File Management Utilities

이 모듈은 AEDT 프로젝트 파일 및 lock 파일을 관리하는 유틸리티 함수를 제공합니다.
"""

import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Union


def find_aedt_files(root_dir: str, recursive: bool = True) -> List[Dict[str, str]]:
    """
    특정 디렉토리 하위에서 모든 .aedt 파일을 찾습니다.
    
    Parameters
    ----------
    root_dir : str
        검색을 시작할 루트 디렉토리 경로
    recursive : bool, optional
        하위 디렉토리까지 재귀적으로 검색할지 여부 (기본값: True)
    
    Returns
    -------
    List[Dict[str, str]]
        발견된 .aedt 파일 정보를 담은 딕셔너리 리스트
        각 딕셔너리는 다음 키를 포함:
        - 'full_path': 전체 경로
        - 'filename': 파일명
        - 'directory': 디렉토리 경로
        - 'size_mb': 파일 크기 (MB)
        - 'modified': 마지막 수정 시간
    
    Examples
    --------
    >>> aedt_files = find_aedt_files(r"E:\KDH\e10\e10_DOE\e10_DOE.opd\AMOP")
    >>> for file_info in aedt_files:
    ...     print(file_info['full_path'])
    """
    aedt_files = []
    root_path = Path(root_dir)
    
    if not root_path.exists():
        print(f"❌ 경로가 존재하지 않습니다: {root_dir}")
        return aedt_files
    
    # 검색 패턴 설정
    pattern = "**/*.aedt" if recursive else "*.aedt"
    
    print("=" * 70)
    print(f"🔍 AEDT 파일 검색 중...")
    print(f"📂 경로: {root_dir}")
    print(f"🔄 재귀 검색: {'예' if recursive else '아니오'}")
    print("=" * 70)
    
    # .aedt 파일 검색
    for aedt_file in root_path.glob(pattern):
        if aedt_file.is_file():
            try:
                # 파일 정보 수집
                file_stat = aedt_file.stat()
                file_info = {
                    'full_path': str(aedt_file.absolute()),
                    'filename': aedt_file.name,
                    'directory': str(aedt_file.parent),
                    'size_mb': file_stat.st_size / (1024 * 1024),  # 바이트를 MB로 변환
                    'modified': pd.Timestamp.fromtimestamp(file_stat.st_mtime)
                }
                aedt_files.append(file_info)
            except Exception as e:
                print(f"⚠️ 파일 정보 읽기 실패: {aedt_file.name} - {e}")
    
    # 결과 출력
    print(f"\n✅ 총 {len(aedt_files)}개의 .aedt 파일 발견")
    
    if aedt_files:
        print("\n📋 발견된 파일 목록:")
        for i, file_info in enumerate(aedt_files, 1):
            print(f"\n  {i}. {file_info['filename']}")
            print(f"     전체 경로: {file_info['full_path']}")
            print(f"     크기: {file_info['size_mb']:.2f} MB")
            print(f"     수정: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("=" * 70)
    
    return aedt_files


def find_lock_files(aedt_path: Union[str, Path]) -> List[Path]:
    """
    AEDT 프로젝트 경로에서 .lock 파일을 찾습니다.
    
    Parameters
    ----------
    aedt_path : Union[str, Path]
        .aedt 파일 경로 또는 프로젝트 디렉토리 경로
    
    Returns
    -------
    List[Path]
        발견된 .lock 파일 경로 리스트
    
    Examples
    --------
    >>> # 단일 AEDT 파일의 lock 파일 찾기
    >>> lock_files = find_lock_files(r"E:\project\model.aedt")
    >>> for lock in lock_files:
    ...     print(lock)
    
    >>> # 디렉토리 전체에서 lock 파일 찾기
    >>> lock_files = find_lock_files(r"E:\project")
    """
    aedt_path = Path(aedt_path)
    
    # .aedt 파일인 경우 해당 디렉토리 기준으로 검색
    if aedt_path.is_file() and aedt_path.suffix == '.aedt':
        search_dir = aedt_path.parent
    elif aedt_path.is_dir():
        search_dir = aedt_path
    else:
        print(f"❌ 유효하지 않은 경로: {aedt_path}")
        return []
    
    # .lock 파일 패턴들
    lock_patterns = [
        '*.lock',
        '*.lock.lock',
        '.*.lock'
    ]
    
    lock_files = []
    for pattern in lock_patterns:
        lock_files.extend(search_dir.glob(pattern))
        # 하위 디렉토리도 검색 (.aedtresults 등)
        lock_files.extend(search_dir.glob(f'**/{pattern}'))
    
    # 중복 제거
    lock_files = list(set(lock_files))
    
    return lock_files


def remove_lock_files(lock_files: List[Path], verbose: bool = True) -> Dict[str, any]:
    """
    찾은 .lock 파일들을 삭제합니다.
    
    Parameters
    ----------
    lock_files : List[Path]
        삭제할 .lock 파일 경로 리스트
    verbose : bool, optional
        상세 출력 여부 (기본값: True)
    
    Returns
    -------
    Dict[str, any]
        삭제 결과 정보:
        - 'success': 성공 여부 (bool)
        - 'deleted_files': 삭제된 파일 리스트 (List[str])
        - 'failed_files': 삭제 실패한 파일 리스트 (List[str])
        - 'message': 결과 메시지 (str)
    
    Examples
    --------
    >>> lock_files = find_lock_files(r"E:\project\model.aedt")
    >>> result = remove_lock_files(lock_files)
    >>> print(result['message'])
    """
    deleted_files = []
    failed_files = []
    
    if not lock_files:
        return {
            'success': True,
            'deleted_files': [],
            'failed_files': [],
            'message': 'ℹ️  삭제할 Lock 파일이 없습니다.'
        }
    
    # Lock 파일 삭제
    for lock_file in lock_files:
        try:
            lock_file.unlink()
            deleted_files.append(str(lock_file))
            if verbose:
                print(f"  ✅ 삭제: {lock_file.name}")
        except PermissionError:
            failed_files.append(str(lock_file))
            if verbose:
                print(f"  ⚠️ 권한 없음: {lock_file.name}")
        except Exception as e:
            failed_files.append(str(lock_file))
            if verbose:
                print(f"  ❌ 실패: {lock_file.name} - {e}")
    
    # 결과 요약
    success = len(failed_files) == 0
    if success:
        message = f'✅ {len(deleted_files)}개 Lock 파일 삭제 완료'
    else:
        message = f'⚠️ {len(deleted_files)}개 삭제, {len(failed_files)}개 실패'
    
    return {
        'success': success,
        'deleted_files': deleted_files,
        'failed_files': failed_files,
        'message': message
    }


def validate_parametric_results(
    csv_path: Union[str, Path], 
    expected_ipeak_steps: int, 
    expected_phase_steps: int,
    verbose: bool = True
) -> Dict[str, any]:
    """
    Parametric Sweep CSV 결과 파일을 검증합니다.
    
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
        검증 결과 정보:
        - 'is_complete': 완전한 결과 여부 (bool)
        - 'expected_count': 예상 결과 개수 (int)
        - 'actual_count': 실제 결과 개수 (int)
        - 'completion_rate': 완료율 (%) (float)
        - 'missing_count': 누락된 결과 개수 (int)
        - 'message': 결과 메시지 (str)
        - 'csv_exists': CSV 파일 존재 여부 (bool)
    
    Examples
    --------
    >>> # IPeak 5단계 × PhaseAdvance 6단계 = 30 결과 검증
    >>> result = validate_parametric_results(
    ...     "e10_DOE_ParametricSetup1_Result.csv",
    ...     expected_ipeak_steps=5,
    ...     expected_phase_steps=6
    ... )
    >>> print(result['message'])
    >>> if not result['is_complete']:
    ...     print(f"누락: {result['missing_count']}개")
    """
    csv_path = Path(csv_path)
    
    # CSV 파일 존재 확인
    if not csv_path.exists():
        return {
            'is_complete': False,
            'expected_count': expected_ipeak_steps * expected_phase_steps,
            'actual_count': 0,
            'completion_rate': 0.0,
            'missing_count': expected_ipeak_steps * expected_phase_steps,
            'message': f'❌ CSV 파일을 찾을 수 없습니다: {csv_path}',
            'csv_exists': False
        }
    
    try:
        # CSV 파일 읽기
        df_results = pd.read_csv(csv_path)
        
        # 예상 결과 개수 계산
        expected_count = expected_ipeak_steps * expected_phase_steps
        actual_count = len(df_results)
        
        # 완료율 계산
        completion_rate = (actual_count / expected_count) * 100 if expected_count > 0 else 0.0
        is_complete = actual_count == expected_count
        missing_count = expected_count - actual_count if actual_count < expected_count else 0
        
        # 결과 메시지
        if is_complete:
            message = f'✅ Parametric 결과 완전 ({actual_count}/{expected_count})'
        elif actual_count > expected_count:
            message = f'⚠️ 예상보다 많은 결과 ({actual_count}/{expected_count})'
        else:
            message = f'⚠️ 불완전한 결과 ({actual_count}/{expected_count}, {completion_rate:.1f}%)'
        
        # 상세 출력
        if verbose:
            print("\n" + "=" * 70)
            print("📊 Parametric Sweep 결과 검증")
            print("=" * 70)
            print(f"📁 CSV 파일: {csv_path.name}")
            print(f"📂 경로: {csv_path.parent}")
            print(f"\n🔢 변수 설정:")
            print(f"  - IPeak 스텝: {expected_ipeak_steps}개")
            print(f"  - PhaseAdvance 스텝: {expected_phase_steps}개")
            print(f"  - 예상 결과: {expected_count}개")
            print(f"\n📈 검증 결과:")
            print(f"  - 실제 결과: {actual_count}개")
            print(f"  - 완료율: {completion_rate:.1f}%")
            
            if not is_complete:
                print(f"  - 누락: {missing_count}개")
                print(f"\n  {message}")
            else:
                print(f"\n  {message}")
            
            # DataFrame 컬럼 정보
            print(f"\n📋 데이터 컬럼 ({len(df_results.columns)}개):")
            for i, col in enumerate(df_results.columns[:10], 1):  # 처음 10개만 표시
                print(f"  {i:2d}. {col}")
            if len(df_results.columns) > 10:
                print(f"  ... (외 {len(df_results.columns) - 10}개)")
            
            print("=" * 70)
        
        return {
            'is_complete': is_complete,
            'expected_count': expected_count,
            'actual_count': actual_count,
            'completion_rate': completion_rate,
            'missing_count': missing_count,
            'message': message,
            'csv_exists': True
        }
        
    except Exception as e:
        error_msg = f'❌ CSV 파일 읽기 실패: {e}'
        if verbose:
            print(error_msg)
        
        return {
            'is_complete': False,
            'expected_count': expected_ipeak_steps * expected_phase_steps,
            'actual_count': 0,
            'completion_rate': 0.0,
            'missing_count': expected_ipeak_steps * expected_phase_steps,
            'message': error_msg,
            'csv_exists': True
        }


def find(obj_dir, search_term: str) -> list:
    """
    객체의 dir() 결과에서 특정 문자열을 포함하는 속성/메서드를 검색합니다.
    
    Parameters
    ----------
    obj_dir : list or object
        검색할 객체의 dir() 결과 또는 객체 자체
    search_term : str
        검색할 문자열 (대소문자 구분 없음)
    
    Returns
    -------
    list
        검색어를 포함하는 속성/메서드 이름 리스트
    
    Examples
    --------
    >>> # dir() 결과에서 검색
    >>> find(dir(m2d), "winding")
    
    >>> # 객체에서 직접 검색
    >>> find(m2d, "boundary")
    """
    # obj_dir이 객체인 경우 dir() 호출
    if not isinstance(obj_dir, list):
        obj_dir = dir(obj_dir)
    
    # 검색어를 소문자로 변환
    search_lower = search_term.lower()
    
    # 검색 수행
    results = [item for item in obj_dir if search_lower in item.lower()]
    
    # 결과 출력
    if results:
        print(f"🔍 '{search_term}' 검색 결과 ({len(results)}개):")
        print("=" * 60)
        for i, item in enumerate(results, 1):
            print(f"  {i:2d}. {item}")
        print("=" * 60)
    else:
        print(f"❌ '{search_term}'을 포함하는 항목을 찾을 수 없습니다.")
    
    return results


if __name__ == "__main__":
    print("✅ AEDT 파일 관리 유틸리티 로드 완료")
    print("\n💡 사용 가능한 함수:")
    print("  - find_aedt_files(root_dir): AEDT 파일 검색")
    print("  - find_lock_files(aedt_path): Lock 파일 검색")
    print("  - remove_lock_files(lock_files): Lock 파일 삭제")
    print("  - validate_parametric_results(csv_path, ipeak_steps, phase_steps): CSV 결과 검증")
    print("  - find(obj, search_term): 객체 속성/메서드 검색")
