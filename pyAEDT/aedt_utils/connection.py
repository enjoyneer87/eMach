"""
AEDT 연결 유틸리티

ANSYS Electronics Desktop에 연결하고 상태를 확인하는 함수들
"""

import os
import time
import psutil
from ansys.aedt.core import Desktop

# 기본 설정
AEDT_VERSION = "2025.2"
NUM_CORES = 8
NG_MODE = False  # Open AEDT UI when it is launched.


def getAedtProcessesDetailed():
    """
    실행 중인 AEDT 프로세스를 상세히 확인합니다.
    
    Returns
    -------
    list
        AEDT 프로세스 정보 리스트. 각 항목은 다음 키를 포함하는 딕셔너리:
        - pid: 프로세스 ID
        - name: 프로세스 이름
        - cmdline: 명령줄 인자
        - create_time: 생성 시간
        - ports: 열린 포트 리스트
    
    Examples
    --------
    >>> processes = getAedtProcessesDetailed()
    >>> print(f"발견된 AEDT 프로세스: {len(processes)}개")
    """
    print("🔍 실행 중인 AEDT 프로세스 검색...")
    
    aedt_processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                pinfo = proc.info
                process_name = pinfo['name'] if pinfo['name'] else ""
                
                # AEDT 관련 프로세스 필터링
                if any(keyword in process_name.lower() for keyword in ['ansysedt', 'aedt']):
                    # 포트 정보 추출 시도
                    ports = []
                    try:
                        connections = proc.connections()
                        for conn in connections:
                            if conn.status == 'LISTEN':
                                ports.append(conn.laddr.port)
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass
                    
                    aedt_processes.append({
                        'pid': pinfo['pid'],
                        'name': process_name,
                        'cmdline': pinfo['cmdline'] if pinfo['cmdline'] else [],
                        'create_time': time.ctime(pinfo['create_time']),
                        'ports': ports
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
        if aedt_processes:
            print(f"✅ {len(aedt_processes)}개의 AEDT 프로세스 발견:")
            for i, proc in enumerate(aedt_processes):
                print(f"\n📋 프로세스 {i+1}:")
                print(f"   PID: {proc['pid']}")
                print(f"   이름: {proc['name']}")
                print(f"   생성시간: {proc['create_time']}")
                if proc['ports']:
                    print(f"   열린 포트: {proc['ports']}")
                else:
                    print(f"   열린 포트: 없음")
        else:
            print("❌ AEDT 프로세스가 없습니다.")
            
        return aedt_processes
        
    except Exception as e:
        print(f"❌ 프로세스 검색 중 오류: {e}")
        return []


def tryConnectToExistingDesktop(aedt_version=None, non_graphical=None):
    """
    기존 AEDT Desktop에 연결을 시도합니다.
    
    Parameters
    ----------
    aedt_version : str, optional
        AEDT 버전. None이면 모듈 기본값(AEDT_VERSION) 사용
    non_graphical : bool, optional
        비그래픽 모드 여부. None이면 모듈 기본값(NG_MODE) 사용
    
    Returns
    -------
    Desktop or None
        연결된 Desktop 객체 또는 None
    
    Examples
    --------
    >>> desktop = tryConnectToExistingDesktop()
    >>> if desktop:
    ...     print("연결 성공!")
    """
    if aedt_version is None:
        aedt_version = AEDT_VERSION
    if non_graphical is None:
        non_graphical = NG_MODE
        
    print("🔗 기존 AEDT Desktop 연결 시도...")
    
    try:
        desktop = Desktop(
            specified_version=aedt_version,
            new_desktop_session=False,
            non_graphical=non_graphical
        )
        print("✅ 기존 AEDT Desktop에 성공적으로 연결되었습니다!")
        return desktop
        
    except Exception as e:
        print(f"❌ 기존 Desktop 연결 실패: {e}")
        return None


def tryConnectWithPorts(port_list, aedt_version='251', non_graphical=False):
    """
    특정 포트들을 시도해서 AEDT에 연결합니다.
    
    Parameters
    ----------
    port_list : list
        시도할 포트 번호 리스트
    aedt_version : str, optional
        AEDT 버전. 기본값 '251'
    non_graphical : bool, optional
        비그래픽 모드 여부. 기본값 False
        
    Returns
    -------
    Desktop or None
        연결된 Desktop 객체 또는 None
    
    Examples
    --------
    >>> desktop = tryConnectWithPorts([56800, 56801, 56802])
    >>> if desktop:
    ...     print("포트 연결 성공!")
    """
    for port in port_list:
        try:
            print(f"🔗 포트 {port}로 연결 시도...")
            desktop = Desktop(
                specified_version=aedt_version,
                new_desktop_session=False,
                port=port,
                non_graphical=non_graphical
            )
            print(f"✅ 포트 {port}로 성공적으로 연결되었습니다!")
            return desktop
        except Exception as e:
            print(f"❌ 포트 {port} 연결 실패: {e}")
            continue
    
    return None


def getDesktopConnection(aedt_version=None, non_graphical=None):
    """
    다양한 방법으로 AEDT Desktop 연결을 시도합니다.
    
    연결 시도 순서:
    1. 기존 Desktop 세션에 연결
    2. 실행 중인 프로세스에서 포트를 찾아 연결
    3. 일반적인 AEDT 포트들(56800-56805)로 연결 시도
    4. 새로운 Desktop 세션 생성
    
    Parameters
    ----------
    aedt_version : str, optional
        AEDT 버전. None이면 모듈 기본값 사용
    non_graphical : bool, optional
        비그래픽 모드 여부. None이면 모듈 기본값 사용
    
    Returns
    -------
    Desktop or None
        연결된 Desktop 객체 또는 None
    
    Examples
    --------
    >>> desktop = getDesktopConnection()
    >>> if desktop:
    ...     print("Desktop 연결 성공!")
    """
    if aedt_version is None:
        aedt_version = AEDT_VERSION
    if non_graphical is None:
        non_graphical = NG_MODE
        
    print("=" * 60)
    print("🎯 AEDT Desktop 연결 시도")
    print("=" * 60)
    
    # 1. 기존 Desktop 연결 시도
    desktop = tryConnectToExistingDesktop(aedt_version, non_graphical)
    if desktop:
        return desktop
    
    # 2. 프로세스에서 포트 찾아서 연결 시도
    processes = getAedtProcessesDetailed()
    all_ports = []
    
    for proc in processes:
        all_ports.extend(proc['ports'])
    
    if all_ports:
        desktop = tryConnectWithPorts(all_ports)
        if desktop:
            return desktop
    
    # 3. 일반적인 AEDT 포트들 시도
    common_ports = [56800, 56801, 56802, 56803, 56804, 56805]
    print("\n🔍 일반적인 AEDT 포트들 시도...")
    desktop = tryConnectWithPorts(common_ports)
    if desktop:
        return desktop
    
    # 4. 새로운 Desktop 세션 생성
    print("\n🆕 새로운 AEDT Desktop 세션을 생성합니다...")
    try:
        desktop = Desktop(
            specified_version=aedt_version,
            new_desktop_session=True,
            non_graphical=non_graphical
        )
        print("✅ 새로운 AEDT Desktop이 생성되었습니다!")
        return desktop
    except Exception as e:
        print(f"❌ 새 Desktop 생성 실패: {e}")
        return None


def checkCurrentDesktopStatus(desktop):
    """
    현재 Desktop의 상태를 확인하고 출력합니다.
    
    Parameters
    ----------
    desktop : Desktop
        확인할 Desktop 객체
    
    Examples
    --------
    >>> desktop = getDesktopConnection()
    >>> checkCurrentDesktopStatus(desktop)
    """
    if not desktop:
        print("❌ Desktop 객체가 없습니다.")
        return
    
    try:
        print("\n" + "=" * 40)
        print("📊 현재 Desktop 상태:")
        print("=" * 40)
        
        # 기본 정보
        print(f"AEDT 버전: {desktop.aedt_version_id}")
        print(f"프로세스 ID: {desktop.aedt_process_id}")
        
        # 프로젝트 정보
        try:
            projects = desktop.project_list()
            print(f"\n📁 열린 프로젝트 ({len(projects)}개):")
            for i, proj_name in enumerate(projects, 1):
                print(f"  {i}. {proj_name}")
            
            # 활성 프로젝트
            active_proj = desktop.active_project()
            if active_proj:
                proj_name = active_proj.GetName()
                print(f"\n🎯 활성 프로젝트: {proj_name}")
                
                # 디자인 목록
                try:
                    design_list = active_proj.GetTopDesignList()
                    print(f"📐 디자인 ({len(design_list)}개):")
                    for i, design in enumerate(design_list, 1):
                        print(f"  {i}. {design}")
                        
                    # 활성 디자인
                    active_design = desktop.active_design()
                    if active_design:
                        print(f"🎯 활성 디자인: {active_design.GetName()}")
                        print(f"   디자인 타입: {active_design.GetDesignType()}")
                except:
                    print("디자인 정보 가져오기 실패")
            else:
                print("🎯 활성 프로젝트: 없음")
                
        except Exception as e:
            print(f"프로젝트 정보 가져오기 실패: {e}")
            
    except Exception as e:
        print(f"❌ Desktop 상태 확인 중 오류: {e}")


def smartAedtConnector(aedt_version=None, non_graphical=None):
    """
    스마트 AEDT 연결 함수 - 사용자 친화적 인터페이스
    
    자동으로 Desktop에 연결하고 상태를 확인합니다.
    
    Parameters
    ----------
    aedt_version : str, optional
        AEDT 버전. None이면 모듈 기본값 사용
    non_graphical : bool, optional
        비그래픽 모드 여부. None이면 모듈 기본값 사용
    
    Returns
    -------
    Desktop or None
        연결된 Desktop 객체 또는 None
    
    Examples
    --------
    >>> desktop = smartAedtConnector()
    >>> if desktop:
    ...     project = desktop.open_project(r"C:\\path\\to\\project.aedt")
    """
    print("🚀 스마트 AEDT 연결기를 시작합니다...")
    
    # Desktop 연결 시도
    desktop = getDesktopConnection(aedt_version, non_graphical)
    
    if desktop:
        # 연결 성공 시 상태 확인
        checkCurrentDesktopStatus(desktop)
        
        print("\n" + "=" * 60)
        print("🎉 AEDT Desktop 연결이 완료되었습니다!")
        print("💡 다음과 같이 사용할 수 있습니다:")
        print("=" * 60)
        print("# 프로젝트 열기:")
        print("# project = desktop.open_project(r'C:\\path\\to\\your\\project.aedt')")
        print("#")
        print("# Maxwell 객체 생성:")
        print("# m2d = ansys.aedt.core.Maxwell2d(project=desktop, new_desktop=False)")
        print("# m3d = ansys.aedt.core.Maxwell3d(project=desktop, new_desktop=False)")
        print("=" * 60)
        
        return desktop
    else:
        print("❌ AEDT Desktop 연결에 실패했습니다.")
        print("\n🔍 문제 해결 방법:")
        print("1. Ansys AEDT가 설치되어 있는지 확인")
        print("2. AEDT 라이선스가 사용 가능한지 확인")
        print("3. 수동으로 AEDT를 실행한 후 다시 시도")
        return None


def quickConnect():
    """
    빠른 연결 - 기존 세션 우선
    
    Returns
    -------
    Desktop or None
        연결된 Desktop 객체 또는 None
    
    Examples
    --------
    >>> desktop = quickConnect()
    >>> if desktop:
    ...     print("빠른 연결 성공!")
    """
    return tryConnectToExistingDesktop()


def forceNewSession(aedt_version=None, non_graphical=None):
    """
    강제로 새 Desktop 세션 생성
    
    Parameters
    ----------
    aedt_version : str, optional
        AEDT 버전. None이면 모듈 기본값 사용
    non_graphical : bool, optional
        비그래픽 모드 여부. None이면 모듈 기본값 사용
    
    Returns
    -------
    Desktop or None
        생성된 Desktop 객체 또는 None
    
    Examples
    --------
    >>> desktop = forceNewSession()
    >>> if desktop:
    ...     print("새 세션 생성 성공!")
    """
    if aedt_version is None:
        aedt_version = AEDT_VERSION
    if non_graphical is None:
        non_graphical = NG_MODE
        
    try:
        return Desktop(
            specified_version=aedt_version,
            new_desktop_session=True,
            non_graphical=non_graphical
        )
    except Exception as e:
        print(f"새 세션 생성 실패: {e}")
        return None
