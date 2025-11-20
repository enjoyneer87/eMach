"""
AEDT Utilities 사용 예시

이 스크립트는 aedt_utils 패키지의 주요 기능을 보여줍니다.
"""

# ============================================================================
# 예시 1: 스마트 연결
# ============================================================================
def example_smart_connect():
    """스마트 AEDT 연결 예시"""
    from aedt_utils import smartAedtConnector
    
    print("=" * 70)
    print("예시 1: 스마트 AEDT 연결")
    print("=" * 70)
    
    desktop = smartAedtConnector()
    
    if desktop:
        print("\n✅ 연결 성공!")
        return desktop
    else:
        print("\n❌ 연결 실패")
        return None


# ============================================================================
# 예시 2: 빠른 연결
# ============================================================================
def example_quick_connect():
    """빠른 연결 예시 (기존 세션만)"""
    from aedt_utils import quickConnect
    
    print("\n" + "=" * 70)
    print("예시 2: 빠른 연결 (기존 세션만)")
    print("=" * 70)
    
    desktop = quickConnect()
    
    if desktop:
        print("✅ 기존 세션에 연결됨")
        return desktop
    else:
        print("❌ 기존 세션 없음")
        return None


# ============================================================================
# 예시 3: Maxwell 2D 연결
# ============================================================================
def example_maxwell_connect():
    """Maxwell 2D 자동 연결 예시"""
    from aedt_utils import getRunningMaxwell2d
    
    print("\n" + "=" * 70)
    print("예시 3: Maxwell 2D 연결")
    print("=" * 70)
    
    m2d = getRunningMaxwell2d()
    
    if m2d:
        print(f"\n✅ Maxwell 2D 연결 성공!")
        print(f"📋 Design Name: {m2d.design_name}")
        print(f"📋 Design Type: {m2d.design_type}")
        
        # Variables 확인
        vars_list = list(m2d.variable_manager.variables.keys())
        print(f"\n📊 Variables ({len(vars_list)}개):")
        for i, var in enumerate(vars_list[:10], 1):  # 처음 10개만
            print(f"  {i}. {var}")
        if len(vars_list) > 10:
            print(f"  ... (총 {len(vars_list)}개)")
        
        # Objects 확인
        objects = m2d.modeler.object_names
        print(f"\n📦 Objects ({len(objects)}개):")
        for i, obj in enumerate(objects[:10], 1):  # 처음 10개만
            print(f"  {i}. {obj}")
        if len(objects) > 10:
            print(f"  ... (총 {len(objects)}개)")
        
        return m2d
    else:
        print("❌ Maxwell 2D를 찾을 수 없습니다.")
        return None


# ============================================================================
# 예시 4: 프로세스 정보 확인
# ============================================================================
def example_process_info():
    """AEDT 프로세스 정보 확인 예시"""
    from aedt_utils import getAedtProcessesDetailed
    
    print("\n" + "=" * 70)
    print("예시 4: AEDT 프로세스 정보")
    print("=" * 70)
    
    processes = getAedtProcessesDetailed()
    
    if processes:
        print(f"\n✅ {len(processes)}개의 AEDT 프로세스 발견")
        return processes
    else:
        print("\n❌ AEDT 프로세스가 없습니다.")
        return []


# ============================================================================
# 예시 5: Desktop 상태 확인
# ============================================================================
def example_desktop_status():
    """Desktop 상태 확인 예시"""
    from aedt_utils import quickConnect, checkCurrentDesktopStatus
    
    print("\n" + "=" * 70)
    print("예시 5: Desktop 상태 확인")
    print("=" * 70)
    
    desktop = quickConnect()
    
    if desktop:
        checkCurrentDesktopStatus(desktop)
        return desktop
    else:
        print("❌ Desktop에 연결할 수 없습니다.")
        return None


# ============================================================================
# 예시 6: Field Plot Export
# ============================================================================
def example_field_plot_export():
    """Field Plot Export 예시"""
    from aedt_utils import getRunningMaxwell2d
    
    print("\n" + "=" * 70)
    print("예시 6: Field Plot Export")
    print("=" * 70)
    
    m2d = getRunningMaxwell2d()
    
    if not m2d:
        print("❌ Maxwell 2D 연결 실패")
        return None
    
    try:
        # Post-processing
        all_objects = m2d.modeler.object_names
        
        print(f"\n📊 Field Plot Export 시작...")
        print(f"   대상 객체: {len(all_objects)}개")
        
        # Field plot (case 파일)
        plot = m2d.post.plot_field(
            quantity="Mag_B",
            assignment=all_objects,
            plot_type="Surface",
            show=False,
            mesh_on_fields=True,
            file_format="case"
        )
        
        print(f"\n✅ Export 완료!")
        if hasattr(plot, 'export_file_path'):
            print(f"📁 파일: {plot.export_file_path}")
        
        return plot
        
    except Exception as e:
        print(f"❌ Export 실패: {e}")
        return None


# ============================================================================
# 예시 7: 전체 워크플로우
# ============================================================================
def example_full_workflow():
    """전체 워크플로우 예시"""
    print("\n" + "=" * 70)
    print("예시 7: 전체 워크플로우")
    print("=" * 70)
    
    # 1. Desktop 연결
    print("\n[1/3] Desktop 연결...")
    from aedt_utils import smartAedtConnector
    desktop = smartAedtConnector()
    
    if not desktop:
        print("❌ Desktop 연결 실패")
        return
    
    # 2. Maxwell 2D 연결
    print("\n[2/3] Maxwell 2D 연결...")
    from aedt_utils import getRunningMaxwell2d
    m2d = getRunningMaxwell2d()
    
    if not m2d:
        print("❌ Maxwell 2D 연결 실패")
        return
    
    # 3. 디자인 정보 확인
    print("\n[3/3] 디자인 정보 확인...")
    print(f"✅ Project: {m2d.project_name}")
    print(f"✅ Design: {m2d.design_name}")
    print(f"✅ Design Type: {m2d.design_type}")
    
    # Setups 확인
    try:
        setups = m2d.setups
        print(f"\n📋 Setups ({len(setups)}개):")
        for i, setup in enumerate(setups, 1):
            print(f"  {i}. {setup.name}")
    except Exception as e:
        print(f"Setup 정보 가져오기 실패: {e}")
    
    print("\n" + "=" * 70)
    print("✅ 전체 워크플로우 완료!")
    print("=" * 70)


# ============================================================================
# 메인 실행
# ============================================================================
if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("🚀 AEDT Utilities 예시 스크립트")
    print("=" * 70)
    
    # 사용자 선택
    print("\n실행할 예시를 선택하세요:")
    print("  1. 스마트 연결")
    print("  2. 빠른 연결")
    print("  3. Maxwell 2D 연결")
    print("  4. 프로세스 정보 확인")
    print("  5. Desktop 상태 확인")
    print("  6. Field Plot Export")
    print("  7. 전체 워크플로우")
    print("  0. 모든 예시 실행")
    
    try:
        choice = input("\n선택 (0-7): ").strip()
        
        if choice == "1":
            example_smart_connect()
        elif choice == "2":
            example_quick_connect()
        elif choice == "3":
            example_maxwell_connect()
        elif choice == "4":
            example_process_info()
        elif choice == "5":
            example_desktop_status()
        elif choice == "6":
            example_field_plot_export()
        elif choice == "7":
            example_full_workflow()
        elif choice == "0":
            # 모든 예시 순차 실행
            example_smart_connect()
            example_quick_connect()
            example_maxwell_connect()
            example_process_info()
            example_desktop_status()
            example_field_plot_export()
            example_full_workflow()
        else:
            print("❌ 잘못된 선택입니다.")
            sys.exit(1)
        
        print("\n" + "=" * 70)
        print("✅ 예시 실행 완료!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
