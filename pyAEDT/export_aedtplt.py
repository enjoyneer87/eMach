"""
AEDTPLT Export Utilities for Maxwell 2D

이 모듈은 AEDT Maxwell 2D 해석 결과를 .aedtplt 형식으로 export하는 유틸리티를 제공합니다.

주요 기능:
- Parametric Sweep 결과 추출
- Time Step 추출
- 단일 파일 AEDTPLT export
- 일괄 파일 AEDTPLT export

Author: KangDH
Date: 2024
"""

import pandas as pd
import re
from pathlib import Path


def get_parametric_sweep_table(m2d_obj, setup_name=None, auto_export=True):
    """
    Parametric Sweep 결과에서 IPeak, PhaseAdvance 값을 추출합니다.
    CSV가 없으면 자동으로 Optimetrics에서 Export합니다.
    
    Parameters:
    -----------
    m2d_obj : Maxwell2d object
        AEDT Maxwell 2D 객체
    setup_name : str, optional
        Parametric Setup 이름 (None이면 자동 감지)
    auto_export : bool
        CSV가 없을 때 자동으로 Export 수행 여부 (default: True)
    
    Returns:
    --------
    pd.DataFrame : IPeak, PhaseAdvance 값을 포함한 DataFrame
    """
    try:
        # Parametrics 모듈 가져오기
        param = m2d_obj.parametrics
        oModule = param.optimodule
        
        # Setup 이름 자동 감지
        existing_setups = oModule.GetChildNames()
        
        if setup_name is None:
            # 자동 감지: OptiParametric 타입의 Setup 찾기
            if not existing_setups:
                print(f"  ❌ Parametric Setup이 존재하지 않습니다.")
                return None
            
            # 첫 번째 Setup 사용 (보통 ParametricSetup1)
            setup_name = existing_setups[0]
            print(f"  🔍 Parametric Setup 자동 감지: '{setup_name}'")
        else:
            # Setup 존재 확인
            if setup_name not in existing_setups:
                print(f"  ❌ Parametric Setup '{setup_name}'이 존재하지 않습니다.")
                print(f"  📋 존재하는 Setup: {existing_setups}")
                return None
        
        # CSV 파일 경로 생성
        aedt_path = Path(m2d_obj.project_path)
        aedt_dir = aedt_path.parent
        aedt_filename = aedt_path.stem
        csv_filename = f"{aedt_filename}_{setup_name}_Result.csv"
        csv_path = aedt_dir / csv_filename
        
        # CSV 파일이 있으면 읽기
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            
            # IPeak, PhaseAdvance 컬럼이 있는지 확인
            required_cols = ['IPeak', 'PhaseAdvance']
            if all(col in df.columns for col in required_cols):
                print(f"  ✅ CSV 파일에서 {len(df)}개 행 읽기 완료")
                return df[required_cols].drop_duplicates().reset_index(drop=True)
            else:
                print(f"  ⚠️ CSV 파일에 필요한 컬럼이 없습니다: {required_cols}")
                print(f"  ℹ️  CSV 재생성 시도...")
                # CSV 삭제 후 재생성
                csv_path.unlink()
        
        # CSV 파일이 없거나 컬럼이 없는 경우
        if not auto_export:
            print(f"  ⚠️ CSV 파일이 없고 auto_export=False입니다.")
            return None
        
        print(f"  📤 Optimetrics 결과 Export 시도 중...")
        
        # CSV Export 실행
        try:
            print(f"  💾 CSV Export 실행: {csv_filename}")
            oModule.ExportOptimetricsResult(setup_name, str(csv_path), False)
            print(f"  ✅ CSV Export 완료")
            
            # Export된 CSV 읽기
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                
                # IPeak, PhaseAdvance 컬럼 확인
                required_cols = ['IPeak', 'PhaseAdvance']
                if all(col in df.columns for col in required_cols):
                    print(f"  ✅ CSV에서 {len(df)}개 행 읽기 완료")
                    return df[required_cols].drop_duplicates().reset_index(drop=True)
                else:
                    print(f"  ⚠️ Export된 CSV에 필요한 컬럼이 없습니다: {required_cols}")
                    print(f"  📋 실제 컬럼: {list(df.columns)}")
                    return None
            else:
                print(f"  ❌ CSV Export 후에도 파일이 없습니다: {csv_path}")
                return None
                
        except Exception as e_export:
            print(f"  ❌ CSV Export 실패: {e_export}")
            return None
            
    except Exception as e:
        print(f"  ❌ Parametric Table 추출 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_time_steps(m2d_obj, *_, **__):
    """Transient 해석 Time sweep을 가장 단순한 방식으로 반환합니다.

    외부 셀에서 검증된 패턴만 사용합니다. 추가 인자는 무시하여
    기존 호출부(`get_time_steps(m2d_obj, setup_name)`)와의 호환성을 유지합니다.

    Returns
    -------
    list[str]
        Time 값 문자열 리스트 (숫자에는 단위 's' 자동 부여).
    """
    try:
        sol = m2d_obj.post.get_solution_data(
            expressions='Moving1.Torque',
            primary_sweep_variable='Time',
            domain='Sweep'
        )
        if sol is None:
            print("  ❌ get_solution_data 반환값이 None")
            return []
        vals = getattr(sol, 'primary_sweep_values', [])
        # 리스트화
        vals_list = list(vals)
        out = []
        for v in vals_list:
            if isinstance(v, (int, float)):
                out.append(f"{v}"+sol.units_sweeps['Time'])
            else:
                s = str(v)
                # 숫자 문자열인데 단위 없으면 붙이기
                if re.match(r'^[0-9.eE+-]+$', s) and not s.endswith('s'):
                    s += 's'
                out.append(s)
        print(f"  ✅ Time Step 추출: {len(out)}개 (simple)")
        return out
    except Exception as e:
        print(f"  ❌ Time Step 단순 추출 실패: {e}")
        return []

# def export_aedtplt(
#     m2d_obj,
#     output_dir,
#     setup_name="Setup1",
#     parametric_setup_name="ParametricSetup1",
#     quantity="A_Vector",
#     plot_name="A_Vector1",
#     create_plot_if_missing=True,
#     variation_index=None
# ):
#     """
#     단일 AEDT 파일에 대해 Sweep별, Time별로 AEDTPLT 파일을 export합니다.
    
#     Parameters:
#     -----------
#     m2d_obj : Maxwell2d object
#         AEDT Maxwell 2D 객체
#     output_dir : str or Path
#         Export 파일을 저장할 디렉토리
#     setup_name : str
#         Setup 이름 (default: "Setup1")
#     parametric_setup_name : str
#         Parametric Setup 이름 (default: "ParametricSetup1")
#     quantity : str
#         Export할 필드 물리량 (default: "A_Vector")
#     plot_name : str
#         Field plot 이름 (default: "A_Vector1")
#     create_plot_if_missing : bool
#         Plot이 없을 경우 자동 생성 여부 (default: True)
#     variation_index : int, optional
#         특정 Variation 하나만 Export할 때 사용 (0-based index).
#         None이면 모든 Variation 처리.
    
#     Returns:
#     --------
#     dict : 처리 결과
#         - 'success': bool - 성공 여부
#         - 'exported_count': int - Export된 파일 수
#         - 'expected_count': int - 예상 파일 수
#         - 'error': str - 오류 메시지 (실패 시)
#     """
    
#     from pathlib import Path
    
#     result = {
#         'success': False,
#         'exported_count': 0,
#         'expected_count': 0,
#         'error': None
#     }
    
#     try:
#         # ===== 1. Parametric Table 추출 =====
#         print(f"\n📊 Parametric Sweep 데이터 추출...")
#         parametric_table = get_parametric_sweep_table(m2d_obj, parametric_setup_name)
        
#         if parametric_table is None or parametric_table.empty:
#             result['error'] = "Parametric Table이 없음"
#             print(f"  ⚠️ {result['error']}")
#             return result
        
#         print(f"  ✅ {len(parametric_table)}개 Variation 발견")

#         # ===== Variation 선택 (단일 처리 모드) =====
#         if variation_index is not None:
#             if not isinstance(variation_index, int):
#                 result['error'] = f"variation_index는 int여야 합니다: {variation_index}"
#                 print(f"  ⚠️ {result['error']}")
#                 return result
#             if variation_index < 0 or variation_index >= len(parametric_table):
#                 result['error'] = (
#                     f"variation_index 범위 오류 (0~{len(parametric_table)-1}): {variation_index}"
#                 )
#                 print(f"  ⚠️ {result['error']}")
#                 return result
#             print(f"  🎯 단일 Variation 선택: index={variation_index} (1-based={variation_index+1})")
#             parametric_table = parametric_table.iloc[[variation_index]].reset_index(drop=True)
        
#         # ===== 2. Time Steps 추출 =====
#         print(f"\n⏱️  Time Step 추출...")
#         time_steps = get_time_steps(m2d_obj, setup_name)
        
#         if not time_steps:
#             result['error'] = "Time Step이 없음"
#             print(f"  ⚠️ {result['error']}")
#             return result
        
#         print(f"  ✅ {len(time_steps)}개 Time Step 발견")
        
#         # 예상 파일 수 (단일 Variation 모드 반영됨)
#         result['expected_count'] = len(parametric_table) * len(time_steps)
        
#         # ===== 3. Field Plot 확인/생성 =====
#         print(f"\n🎨 Field Plot 확인...")
#         oDesign = m2d_obj.odesign
#         oModule = oDesign.GetModule("FieldsReporter")
        
#         # 기존 Plot 목록 확인
#         existing_plots = oModule.GetFieldPlotNames()
        
#         if plot_name not in existing_plots:
#             if create_plot_if_missing:
#                 print(f"  📝 Field Plot 생성: {plot_name}")
#                 try:
#                     # 모든 오브젝트 이름 가져오기
#                     all_object_names = m2d_obj.modeler.object_names
#                     num_objects = len(all_object_names)
                    
#                     # PlotGeomInfo 구성
#                     plot_geom_info = [1, "Surface", "FacesList", num_objects] + all_object_names
                    
#                     # Field Plot 생성
#                     oModule.CreateFieldPlot(
#                         [
#                             "NAME:" + plot_name,
#                             "SolutionName:=", f"{setup_name} : Transient",
#                             "UserSpecifyName:=", 1,
#                             "UserSpecifyFolder:=", 1,
#                             "QuantityName:=", quantity,
#                             "PlotFolder:=", "A",
#                             "StreamlinePlot:=", False,
#                             "AdjacentSidePlot:=", False,
#                             "FullModelPlot:=", False,
#                             "IntrinsicVar:=", "Time='0s'",
#                             "PlotGeomInfo:=", plot_geom_info,
#                             "FilterBoxes:=", [0],
#                             		[
#                                 "NAME:PlotOnLineSettings",
#                                 [
#                                     "NAME:LineSettingsID",
#                                     "Width:="		, 4,
#                                     "Style:="		, "Cylinder"
#                                 ],
#                                 "ShadingType:="		, 0,
#                                 "IsoValType:="		, "Tone",
#                                 "ArrowUniform:="	, False,
#                                 "NumofArrow:="		, 100,
#                                 "Refinement:="		, 0
#                             ],
#                             [
#                                 "NAME:PlotOnSurfaceSettings",
#                                 "ShadingType:=", 0,
#                                 "Filled:=", False,
#                                 "IsoValType:=", "Tone",
#                                 "AddGrid:=", False,
#                                 "MapTransparency:=", True,
#                                 "Refinement:=", 0,
#                                 "Transparency:=", 0,
#                                 "SmoothingLevel:=", 0,
#                                 [
#                                     "NAME:Arrow3DSpacingSettings",
#                                     "ArrowUniform:=", True,
#                                     "ArrowSpacing:=", 0,
#                                     "MinArrowSpacing:=", 0,
#                                     "MaxArrowSpacing:=", 0
#                                 ],
#                                 "GridColor:=", [255, 255, 255]
#                             ],
#                             "EnableGaussianSmoothing:=", False,
#                             "SurfaceOnly:=", False
#                         ],
#                         "Field"
#                     )
#                     print(f"  ✅ Field Plot 생성 완료 ({num_objects}개 오브젝트)")
#                 except Exception as e:
#                     print(f"  ⚠️ Field Plot 생성 실패: {e}")
#                     if existing_plots:
#                         plot_name = existing_plots[0]
#                         print(f"  📌 기존 Plot 사용: {plot_name}")
#                     else:
#                         result['error'] = f"Field Plot 생성/사용 불가: {e}"
#                         return result
#             else:
#                 result['error'] = "Field Plot이 없음"
#                 print(f"  ⚠️ {result['error']}")
#                 return result
#         else:
#             print(f"  ✅ Field Plot 존재: {plot_name}")
        
#         # ===== 4. Export 디렉토리 생성 =====
#         export_dir = Path(output_dir)
#         export_dir.mkdir(parents=True, exist_ok=True)
        
#         print(f"\n💾 Export 디렉토리: {export_dir}")
        
#         # ===== 5. AEDTPLT Export =====
#         print(f"\n🚀 AEDTPLT Export 시작...")
#         print(f"  - Variations 처리: {len(parametric_table)} (variation_index={'ALL' if variation_index is None else variation_index})")
#         print(f"  - Time steps: {len(time_steps)}")
#         print(f"  - Expected files: {result['expected_count']}")
        
#         exported_count = 0
        
#         # 프로젝트 파일명 (파일명 생성에 사용)
#         aedt_stem = Path(m2d_obj.project_path).stem
        
#         for var_idx, row in parametric_table.iterrows():
#             ipeak_val = row['IPeak']
#             phase_val = row['PhaseAdvance']
            
#             # IPeak, PhaseAdvance 설정
#             try:
#                 oDesign.ChangeProperty(
#                     [
#                         "NAME:AllTabs",
#                         [
#                             "NAME:LocalVariableTab",
#                             [
#                                 "NAME:PropServers", 
#                                 "LocalVariables"
#                             ],
#                             [
#                                 "NAME:ChangedProps",
#                                 [
#                                     "NAME:IPeak",
#                                     "Value:=", str(ipeak_val)
#                                 ],
#                                 [
#                                     "NAME:PhaseAdvance",
#                                     "Value:=", str(phase_val)
#                                 ]
#                             ]
#                         ]
#                     ])
#             except Exception as e:
#                 print(f"  ⚠️ Variable 설정 실패 (IPeak={ipeak_val}, Phase={phase_val}): {e}")
#                 continue
            
#             # 각 Time Step에 대해 Export
#             for time_idx, time_value in enumerate(time_steps):
#                 try:
#                     # Time 문자열 생성
#                     time_str = f"Time='{time_value}'"
                    
#                     # 파일명 생성
#                     file_name_export = (
#                         f"{aedt_stem}_"
#                         f"IPeak{ipeak_val}_"
#                         f"Phase{phase_val}_"
#                         f"Time{time_idx:03d}.aedtplt"
#                     )
#                     file_path_export = export_dir / file_name_export
                    
#                     # Solution context 설정
#                     oModule.SetPlotsViewSolutionContext(
#                         [plot_name], 
#                         f"{setup_name} : Transient", 
#                         time_str
#                     )
                    
#                     # Plot 업데이트
#                     try:
#                         oModule.UpdateAllFieldPlots()
#                     except:
#                         pass  # 업데이트 실패해도 계속 진행
                    
#                     # Field plot export
#                     oModule.ExportFieldPlot(plot_name, False, str(file_path_export))
                    
#                     exported_count += 1
                    
#                     if exported_count % 10 == 0:
#                         print(f"  📦 [{exported_count}/{result['expected_count']}] Exported...")
                    
#                 except Exception as e:
#                     print(f"  ❌ Export 실패 (Var{var_idx+1}, Time{time_idx}): {e}")
        
#         print(f"\n✅ Export 완료: {exported_count}개 파일")
        
#         result['success'] = True
#         result['exported_count'] = exported_count
        
#     except Exception as e:
#         result['error'] = str(e)
#         print(f"\n❌ Export 실패: {e}")
#         import traceback
#         traceback.print_exc()
    
#     return result


def export_field(
    m2d_obj,
    output_dir,
    setup_name="Setup1",
    parametric_setup_name="ParametricSetup1",
    field_quantity="A",
    target_object="Stator_Lamination_Primitive",
    variation_index=None,
    time_index=None,
    batch_size=20,
    save_wait_time=3,
    export_delay=0.2
):
    """
    단일 AEDT 파일에 대해 Variation별, Time별로 Field 데이터를 .fld 파일로 export합니다.
    pyAEDT 공식 패턴 기반으로 안정적인 메모리 관리를 수행합니다.
    
    Parameters:
    -----------
    m2d_obj : Maxwell2d object
        AEDT Maxwell 2D 객체
    output_dir : str or Path
        Export 파일을 저장할 디렉토리
    setup_name : str
        Setup 이름 (default: "Setup1")
    parametric_setup_name : str
        Parametric Setup 이름 (default: "ParametricSetup1")
    field_quantity : str
        Export할 필드 물리량 (default: "A", 옵션: "B", "E", "D", "H")
    target_object : str
        Field를 추출할 오브젝트 이름 (default: "Stator_Lamination_Primitive")
    variation_index : int, optional
        특정 Variation 하나만 Export할 때 사용 (0-based index).
        None이면 모든 Variation 처리.
    time_index : int, optional
        특정 Time Step 하나만 Export할 때 사용 (0-based index).
        None이면 모든 Time Step 처리.
    batch_size : int
        몇 개 파일마다 Design 저장으로 메모리 정리할지 (default: 20)
    save_wait_time : float
        Design 저장 후 대기 시간(초) (default: 3)
    export_delay : float
        각 export 후 짧은 대기 시간(초) (default: 0.2)
    
    Returns:
    --------
    dict : 처리 결과
        - 'success': bool - 성공 여부
        - 'exported_count': int - Export된 파일 수
        - 'expected_count': int - 예상 파일 수
        - 'error': str - 오류 메시지 (실패 시)
    
    Examples:
    ---------
    # 단일 variation, 단일 time step
    >>> result = export_field(m2d, output_dir, variation_index=0, time_index=0)
    
    # 단일 variation, 모든 time steps
    >>> result = export_field(m2d, output_dir, variation_index=0)
    
    # 모든 variations, 모든 time steps (배치 처리)
    >>> result = export_field(m2d, output_dir, batch_size=15, save_wait_time=5)
    """
    
    from pathlib import Path
    import time as time_module
    
    result = {
        'success': False,
        'exported_count': 0,
        'expected_count': 0,
        'error': None
    }
    
    try:
        # ===== 1. Parametric Table 추출 =====
        print(f"\n📊 Parametric Sweep 데이터 추출...")
        parametric_table = get_parametric_sweep_table(m2d_obj, parametric_setup_name)
        
        if parametric_table is None or parametric_table.empty:
            result['error'] = "Parametric Table이 없음"
            print(f"  ⚠️ {result['error']}")
            return result
        
        print(f"  ✅ {len(parametric_table)}개 Variation 발견")

        # ===== Variation 선택 (단일 처리 모드) =====
        if variation_index is not None:
            if not isinstance(variation_index, int):
                result['error'] = f"variation_index는 int여야 합니다: {variation_index}"
                print(f"  ⚠️ {result['error']}")
                return result
            if variation_index < 0 or variation_index >= len(parametric_table):
                result['error'] = (
                    f"variation_index 범위 오류 (0~{len(parametric_table)-1}): {variation_index}"
                )
                print(f"  ⚠️ {result['error']}")
                return result
            print(f"  🎯 단일 Variation 선택: index={variation_index} (1-based={variation_index+1})")
            parametric_table = parametric_table.iloc[[variation_index]].reset_index(drop=True)
        
        # ===== 2. Time Steps 추출 =====
        print(f"\n⏱️  Time Step 추출...")
        time_steps = get_time_steps(m2d_obj, setup_name)
        
        if not time_steps:
            result['error'] = "Time Step이 없음"
            print(f"  ⚠️ {result['error']}")
            return result
        
        print(f"  ✅ {len(time_steps)}개 Time Step 발견")
        
        # ===== Time Step 선택 (단일 처리 모드) =====
        if time_index is not None:
            if not isinstance(time_index, int):
                result['error'] = f"time_index는 int여야 합니다: {time_index}"
                print(f"  ⚠️ {result['error']}")
                return result
            if time_index < 0 or time_index >= len(time_steps):
                result['error'] = (
                    f"time_index 범위 오류 (0~{len(time_steps)-1}): {time_index}"
                )
                print(f"  ⚠️ {result['error']}")
                return result
            print(f"  🎯 단일 Time Step 선택: index={time_index} (Time={time_steps[time_index]})")
            time_steps = [time_steps[time_index]]
        
        # 예상 파일 수
        result['expected_count'] = len(parametric_table) * len(time_steps)
        
        # ===== 3. Export 디렉토리 생성 =====
        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n💾 Export 디렉토리: {export_dir}")
        
        # ===== 4. Fields Reporter 모듈 가져오기 =====
        oDesign = m2d_obj.odesign
        oModule = oDesign.GetModule("FieldsReporter")
        
        # ===== 5. FLD Export =====
        print(f"\n🚀 FLD Export 시작...")
        print(f"  - Variations: {len(parametric_table)} (variation_index={'ALL' if variation_index is None else variation_index})")
        print(f"  - Time steps: {len(time_steps)} (time_index={'ALL' if time_index is None else time_index})")
        print(f"  - Expected files: {result['expected_count']}")
        print(f"  - Batch size: {batch_size} (save every {batch_size} files)")
        print(f"  - Save wait: {save_wait_time}s, Export delay: {export_delay}s")
        
        exported_count = 0
        error_count = 0
        
        # 프로젝트 파일명 (파일명 생성에 사용)
        aedt_stem = Path(m2d_obj.project_path).stem
        
        # Design variables 추출 (pyAEDT 공식 패턴)
        design_variables = {}
        if hasattr(m2d_obj, "variable_manager") and hasattr(m2d_obj.variable_manager, "variables"):
            design_variables = m2d_obj.variable_manager.variables
        
        for var_idx, row in parametric_table.iterrows():
            ipeak_val = row['IPeak']
            phase_val = row['PhaseAdvance']
            
            # 각 Time Step에 대해 Export
            for time_idx, time_value in enumerate(time_steps):
                try:
                    # 파일명 생성
                    file_name_export = (
                        f"{aedt_stem}_"
                        f"IPeak{ipeak_val}_"
                        f"Phase{phase_val}_"
                        f"Time{time_idx:03d}.fld"
                    )
                    file_path_export = export_dir / file_name_export
                    
                    # pyAEDT 공식 패턴: 스택 초기화 → 식 설정 → Export → 스택 정리
                    oModule.CalcStack("clear")
                    
                    # Field Calculator 스택 설정
                    oModule.EnterQty(field_quantity)
                    oModule.CalcOp("Smooth")
                    oModule.EnterVol(target_object)
                    oModule.CalcOp("Value")
                    
                    # CalculatorWrite 인자 준비 (pyAEDT 공식 패턴)
                    args = []
                    
                    # Design variables 추가
                    for k, v in design_variables.items():
                        args.append(f"{k}:=")
                        args.append(str(v))
                    
                    # Intrinsics 추가 (Time, IPeak, PhaseAdvance)
                    args.extend([
                        "Time:=", time_value,
                        "IPeak:=", str(ipeak_val),
                        "PhaseAdvance:=", str(phase_val)
                    ])
                    
                    # Field data export (use safe wrapper to handle format/COM issues)
                    def safe_calculator_write(oModule, filepath, solution, args_list, sleep_after=0.2):
                        """Attempt CalculatorWrite with a couple of common argument formats.

                        Returns dict: {'ok': bool, 'error': str or None}
                        """
                        import time as _time
                        # candidate 1: flat list (most common)
                        try:
                            oModule.CalculatorWrite(str(filepath), ["Solution:=", solution], args_list)
                            _time.sleep(sleep_after)
                            return {'ok': True, 'error': None}
                        except Exception as _e1:
                            err1 = _e1
                        # candidate 2: ensure args are flat strings (already likely), try again
                        try:
                            flat = []
                            for a in args_list:
                                if isinstance(a, (list, tuple)) and len(a) == 2:
                                    flat.extend([str(a[0]), str(a[1])])
                                else:
                                    flat.append(str(a))
                            oModule.CalculatorWrite(str(filepath), ["Solution:=", solution], flat)
                            _time.sleep(sleep_after)
                            return {'ok': True, 'error': None}
                        except Exception as _e2:
                            err2 = _e2
                        # failed both attempts
                        return {'ok': False, 'error': f"try1: {err1}; try2: {err2}"}

                    res_write = safe_calculator_write(oModule, file_path_export, f"{setup_name} : Transient", args, sleep_after=export_delay)
                    if not res_write.get('ok'):
                        raise RuntimeError(f"CalculatorWrite failed: {res_write.get('error')}")
                    
                    # ⭐ Calculator 스택 정리 (중요!)
                    oModule.CalcStack("clear")
                    
                    exported_count += 1
                    
                    # 각 export 후 짧은 대기
                    if export_delay > 0:
                        time_module.sleep(export_delay)
                    
                    # 진행상황 출력
                    if exported_count % 10 == 0:
                        print(f"  📦 [{exported_count}/{result['expected_count']}] Exported...")
                    
                    # ⭐ 배치마다 Design 저장으로 메모리 정리
                    if batch_size > 0 and exported_count % batch_size == 0:
                        batch_num = exported_count // batch_size
                        print(f"  💾 [배치 {batch_num}] 저장+대기 {save_wait_time}초...", end="", flush=True)
                        oDesign.Save()
                        time_module.sleep(save_wait_time)
                        print(" ✅")
                    
                except Exception as e:
                    error_count += 1
                    print(f"  ❌ Export 실패 (Var{var_idx+1}, Time{time_idx}): {e}")
                    # 에러 발생 시에도 스택 정리
                    try:
                        oModule.CalcStack("clear")
                    except:
                        pass
                    # 에러 후 대기
                    time_module.sleep(1)
        
        # 마지막 배치 저장
        if batch_size > 0 and exported_count % batch_size != 0:
            print(f"\n💾 최종 저장 중...", end="", flush=True)
            oDesign.Save()
            time_module.sleep(save_wait_time)
            print(" ✅")
        
        print(f"\n✅ Export 완료: {exported_count}개 파일 (실패: {error_count}개)")
        
        result['success'] = True
        result['exported_count'] = exported_count
        
    except Exception as e:
        result['error'] = str(e)
        print(f"\n❌ Export 실패: {e}")
        import traceback
        traceback.print_exc()
    
    return result
