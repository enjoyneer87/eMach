"""
Maxwell FLD 파일을 HDF5 형식으로 변환하는 스크립트
"""
import numpy as np
import pandas as pd
from pathlib import Path
import csv


def parse_fld_file(fld_file_path, header_lines=2):
    """
    FLD 파일을 파싱하여 데이터를 추출합니다.
    
    Parameters
    ----------
    fld_file_path : str or Path
        FLD 파일 경로
    header_lines : int
        건너뛸 헤더 라인 수 (기본값: 2)
        - 샘플 포인트 파일 사용 시: 1
        - 일반 export 시: 2
    
    Returns
    -------
    pandas.DataFrame
        파싱된 데이터
    """
    fld_path = Path(fld_file_path)
    
    if not fld_path.exists():
        raise FileNotFoundError(f"FLD 파일을 찾을 수 없습니다: {fld_file_path}")
    
    # FLD 파일 읽기
    with open(fld_path, "r") as file:
        # 헤더 스킵
        for _ in range(header_lines):
            file.readline()
        
        # 데이터 파싱
        data_rows = []
        for line in file:
            # 공백 또는 탭으로 구분된 값 파싱
            tmp = line.strip().split()
            # 빈 탭 제거
            tmp = [element.replace("\t\t", "") for element in tmp if element]
            
            if len(tmp) > 1:  # 유효한 데이터 행만 추가
                data_rows.append(tmp)
    
    # NumPy 배열로 변환
    data_array = np.array(data_rows, dtype=float)
    
    # DataFrame 생성 (일반적으로 X, Y, Z, Field 값)
    if data_array.shape[1] == 4:
        # 스칼라 필드 (X, Y, Z, Field)
        columns = ['X', 'Y', 'Z', 'Field']
    elif data_array.shape[1] == 6:
        # 벡터 필드 (X, Y, Z, Fx, Fy, Fz)
        columns = ['X', 'Y', 'Z', 'Field_X', 'Field_Y', 'Field_Z']
    else:
        # 일반적인 경우
        columns = [f'Column_{i}' for i in range(data_array.shape[1])]
    
    df = pd.DataFrame(data_array, columns=columns)
    
    return df


def fld_to_h5(fld_file_path, output_h5_path=None, metadata=None, header_lines=2):
    """
    FLD 파일을 HDF5 형식으로 변환합니다.
    
    Parameters
    ----------
    fld_file_path : str or Path
        입력 FLD 파일 경로
    output_h5_path : str or Path, optional
        출력 HDF5 파일 경로 (None이면 자동 생성)
    metadata : dict, optional
        저장할 메타데이터 딕셔너리
    header_lines : int
        건너뛸 헤더 라인 수
    
    Returns
    -------
    Path
        생성된 HDF5 파일 경로
    """
    fld_path = Path(fld_file_path)
    
    # 출력 파일 경로 설정
    if output_h5_path is None:
        output_h5_path = fld_path.with_suffix('.h5')
    else:
        output_h5_path = Path(output_h5_path)
    
    # FLD 파일 파싱
    print(f"FLD 파일 읽는 중: {fld_path}")
    df = parse_fld_file(fld_path, header_lines=header_lines)
    
    print(f"데이터 형태: {df.shape}")
    print(f"컬럼: {list(df.columns)}")
    
    # HDF5로 저장
    print(f"HDF5로 저장 중: {output_h5_path}")
    df.to_hdf(
        output_h5_path,
        key='field_data',
        mode='w',
        complevel=9,  # 압축 레벨 (0-9)
        complib='zlib'  # 압축 라이브러리
    )
    
    # 메타데이터가 있으면 별도로 저장
    if metadata:
        import json
        metadata_path = output_h5_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        print(f"메타데이터 저장됨: {metadata_path}")
    
    print(f"✓ 변환 완료!")
    return output_h5_path


def read_h5_field_data(h5_file_path):
    """
    HDF5 파일에서 필드 데이터를 읽습니다.
    
    Parameters
    ----------
    h5_file_path : str or Path
        HDF5 파일 경로
    
    Returns
    -------
    pandas.DataFrame
        필드 데이터
    """
    df = pd.read_hdf(h5_file_path, key='field_data')
    return df


# ==================== 사용 예제 ====================

if __name__ == "__main__":
    # 예제 1: 기본 변환
    fld_file = "field_export.fld"
    
    # 메타데이터 설정 (선택 사항)
    metadata = {
        "source": "Maxwell 3D",
        "quantity": "Mag_B",
        "solution": "Setup1 : LastAdaptive",
        "units": "Tesla",
        "coordinate_system": "Global",
        "date": "2025-01-07"
    }
    
    # FLD → H5 변환
    h5_file = fld_to_h5(
        fld_file_path=fld_file,
        metadata=metadata,
        header_lines=2  # 일반 export는 2, sample points 사용 시 1
    )
    
    # 변환된 파일 읽기
    df = read_h5_field_data(h5_file)
    print("\n=== 데이터 미리보기 ===")
    print(df.head())
    print(f"\n데이터 통계:")
    print(df.describe())