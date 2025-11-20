"""
AEDT 파일 병렬 처리 모듈
ProcessPoolExecutor에서 사용 가능하도록 별도 파일로 분리
"""

import ansys.aedt.core
import time


def process_aedt_file(aedt_path: str, aedt_version: str = "2025.2") -> dict:
    """
    단일 AEDT 파일을 열고 Excitation 설정 및 Parametric Sweep을 적용합니다.
    
    Parameters
    ----------
    aedt_path : str
        AEDT 파일 경로
    aedt_version : str
        AEDT 버전
        
    Returns
    -------
    dict
        처리 결과 정보
    """
    result = {
        'file': aedt_path,
        'success': False,
        'message': '',
        'start_time': time.time()
    }
    
    try:
        print(f"\n{'='*70}")
        print(f"🔧 처리 시작: {aedt_path}")
        print(f"{'='*70}")
        
        # 1. Maxwell 2D 열기 (새 Desktop 세션)
        m2d = ansys.aedt.core.Maxwell2d(
            project=aedt_path,
            version=aedt_version,
            new_desktop=True,  # 각 파일마다 독립적인 Desktop 세션
            non_graphical=False
        )
        print(f"✅ 프로젝트 열기 완료 (Desktop 세션: {m2d.desktop_class.port})")
        
        # 2. Excitation Objects 설정
        try:
            excitObj = m2d.excitation_objects
            
            if 'WG_Ph1_P1' in excitObj and 'WG_Ph2_P1' in excitObj and 'WG_Ph3_P1' in excitObj:
                Ph1Obj = excitObj['WG_Ph1_P1']
                Ph2Obj = excitObj['WG_Ph2_P1']
                Ph3Obj = excitObj['WG_Ph3_P1']
                
                ph1Current = 'IPeak  * sin(MachineRPM/1rpm*NumPoles/60*pi*time+PhaseAdvance-0deg+0)'
                ph2Current = 'IPeak  * sin(MachineRPM/1rpm*NumPoles/60*pi*time+PhaseAdvance-240deg+0)'
                ph3Current = 'IPeak  * sin(MachineRPM/1rpm*NumPoles/60*pi*time+PhaseAdvance-120deg+0)'
                
                Ph1Obj.update_property(prop_name='Current', prop_value=ph1Current)
                Ph2Obj.update_property(prop_name='Current', prop_value=ph2Current)
                Ph3Obj.update_property(prop_name='Current', prop_value=ph3Current)
                
                print(f"✅ Excitation 설정 완료")
            else:
                print(f"⚠️ Winding Group을 찾을 수 없습니다.")
        
        except Exception as e:
            print(f"⚠️ Excitation 설정 실패: {e}")
        
        # 3. Parametric Sweep 추가
        try:
            param = m2d.parametrics
            oModule = param.optimodule
           

            oModule.InsertSetup("OptiParametric", 
                [
                    "NAME:ParametricSetup1",
                    "IsEnabled:=", True,
                    [
                        "NAME:ProdOptiSetupDataV2",
                        "SaveFields:=", True,
                        "CopyMesh:=", False,
                        "SolveWithCopiedMeshOnly:=", False
                    ],
                    "InterpolationPoints:=", 0,
                    [
                        "NAME:StartingPoint"
                    ],
                    "Sim. Setups:=", ["Setup1"],
                    [
                        "NAME:Sweeps",
                        [
                            "NAME:SweepDefinition",
                            "Variable:=", "IPeak",
                            "Data:=", "LINC 10A 650.53A 5",
                            "OffsetF1:=", False,
                            "Synchronize:=", 0
                        ],
                        [
                            "NAME:SweepDefinition",
                            "Variable:=", "PhaseAdvance",
                            "Data:=", "LINC 0deg 90deg 6",
                            "OffsetF1:=", False,
                            "Synchronize:=", 0
                        ]
                    ],
                    [
                        "NAME:Sweep Operations",
                        "del:=", ["0A","90deg"],
                        "del:=", ["0A","72deg"],
                        "del:=", ["0A","54deg"],
                        "del:=", ["0A","36deg"],
                        "del:=", ["0A","18deg"]
                    ],
                    [
                        "NAME:Goals"
                    ]
                ]
            )
            print(f"✅ Parametric Sweep 생성 완료")
        
        except Exception as e:
            print(f"⚠️ Parametric Sweep 생성 실패: {e}")
        
        # 4. 저장 및 닫기
        m2d.save_project()
        print(f"💾 프로젝트 저장 완료")
        
        m2d.close_project()
        print(f"🚪 프로젝트 닫기 완료")
        
        # Desktop 세션은 열어둠 (모든 파일 처리 후 수동 종료)
        
        result['success'] = True
        result['message'] = '처리 완료'
        
    except Exception as e:
        result['message'] = f'오류: {str(e)}'
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        result['end_time'] = time.time()
        result['duration'] = result['end_time'] - result['start_time']
        print(f"\n⏱️ 소요 시간: {result['duration']:.2f}초")
        print(f"{'='*70}\n")
    
    return result
