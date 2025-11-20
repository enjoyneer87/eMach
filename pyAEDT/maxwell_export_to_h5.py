"""
PyAEDT를 사용하여 Maxwell에서 직접 필드를 추출하고 H5로 변환
"""
from ansys.aedt.core import Maxwell3d
import numpy as np
import pandas as pd
from pathlib import Path


def maxwell_field_to_h5(
    project_name,
    design_name,
    quantity="Mag_B",
    setup_name=None,
    assignment="AllObjects",
    output_dir=None
):
    """
    Maxwell 디자인에서 필드를 추출하고 HDF5로 저장합니다.
    """
    # Maxwell 앱 열기
    maxwell = Maxwell3d(projectname=project_name, designname=design_name)
    
    if setup_name is None:
        setup_name = maxwell.existing_analysis_sweeps[0]
    
    # 임시 FLD 파일로 export
    temp_fld = Path(maxwell.working_directory) / "temp_field.fld"
    
    print(f"필드 데이터 export 중: {quantity}")
    field_file = maxwell.post.export_field_file(
        quantity=quantity,
        solution=setup_name,
        output_file=str(temp_fld),
        assignment=assignment,
        objects_type="Vol"  # 또는 "Surf", "Line"
    )
    
    if not field_file:
        raise RuntimeError("필드 export 실패")
    
    # FLD 파일 파싱
    print("FLD 파일 파싱 중...")
    with open(temp_fld, "r") as file:
        # 헤더 스킵 (2줄)
        file.readline()
        file.readline()
        
        data_rows = []
        for line in file:
            tmp = line.strip().split()
            tmp = [element.replace("\t\t", "") for element in tmp if element]
            if len(tmp) > 1:
                data_rows.append(tmp)
    
    # DataFrame 생성
    data_array = np.array(data_rows, dtype=float)
    
    if data_array.shape[1] == 4:
        columns = ['X', 'Y', 'Z', quantity]
    elif data_array.shape[1] == 6:
        columns = ['X', 'Y', 'Z', f'{quantity}_X', f'{quantity}_Y', f'{quantity}_Z']
    else:
        columns = [f'Column_{i}' for i in range(data_array.shape[1])]
    
    df = pd.DataFrame(data_array, columns=columns)
    
    # 출력 경로 설정
    if output_dir is None:
        output_dir = maxwell.working_directory
    
    h5_file = Path(output_dir) / f"{quantity}_{maxwell.design_name}.h5"
    
    # HDF5로 저장
    print(f"HDF5로 저장 중: {h5_file}")
    df.to_hdf(h5_file, key='field_data', mode='w', complevel=9, complib='zlib')
    
    # 메타데이터 저장
    import json
    metadata = {
        "project": project_name,
        "design": design_name,
        "quantity": quantity,
        "setup": setup_name,
        "assignment": assignment,
        "units": maxwell.modeler.model_units,
        "rows": len(df),
        "columns": list(df.columns)
    }
    
    metadata_file = h5_file.with_suffix('.json')
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)
    
    # 임시 파일 삭제
    temp_fld.unlink()
    
    # Maxwell 종료
    maxwell.close_project(save=False)
    
    print(f"✓ 완료! 저장된 파일: {h5_file}")
    return h5_file, df


# ==================== 사용 예제 ====================

if __name__ == "__main__":
    # Maxwell 프로젝트에서 필드 추출 및 H5 변환
    h5_file, df = maxwell_field_to_h5(
        project_name="MyMaxwellProject.aedt",
        design_name="MyDesign",
        quantity="Mag_B",  # 또는 "E", "H", "Mag_H", "Jvol" 등
        setup_name="Setup1 : LastAdaptive",
        assignment="AllObjects",
        output_dir="./output"
    )
    
    print("\n=== 데이터 미리보기 ===")
    print(df.head(10))