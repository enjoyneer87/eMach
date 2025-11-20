"""
Maxwell 2D 유틸리티

Maxwell 2D 디자인 연결 및 작업을 위한 함수들
"""

from ansys.aedt.core import Desktop, Maxwell2d


def getRunningMaxwell2d(aedt_version="2025.2", non_graphical=False):
    """
    현재 실행 중인 AEDT Desktop 세션에 연결하여 활성 Maxwell 2D 디자인의 Maxwell2d 객체를 반환합니다.

    동작 순서:
    1) 기존 Desktop 세션에 연결 (새 세션 생성하지 않음)
    2) 활성 프로젝트/디자인 조회
    3) 활성 디자인이 Maxwell 2D가 아니면, 프로젝트의 디자인 목록에서 Maxwell 2D를 탐색
    4) 찾은 프로젝트/디자인 이름으로 Maxwell2d 객체 attach

    Parameters
    ----------
    aedt_version : str, optional
        AEDT 버전 문자열 (예: "2025.2"). 기본값 "2025.2"
    non_graphical : bool, optional
        비그래픽 모드 여부. 기존 실행 세션에 attach할 때는 보통 False 권장. 기본값 False

    Returns
    -------
    ansys.aedt.core.Maxwell2d or None
        연결된 Maxwell2d 객체. 찾지 못하면 None 반환.
        
    Examples
    --------
    >>> m2d = getRunningMaxwell2d()
    >>> if m2d:
    ...     print(f"Design: {m2d.design_name}")
    ...     print(f"Variables: {list(m2d.variable_manager.variables.keys())}")
    
    >>> # 특정 버전 지정
    >>> m2d = getRunningMaxwell2d(aedt_version="2024.2")
    """
    try:
        from ansys.aedt.core import Desktop, Maxwell2d
    except Exception as e:
        print(f"❌ PyAEDT import 실패: {e}")
        return None

    desktop = None
    try:
        # 기존 세션에 붙기 (새 세션 X)
        desktop = Desktop(
            specified_version=aedt_version,
            new_desktop_session=False,
            non_graphical=non_graphical
        )
        
    except Exception as e:
        print(f"❌ 기존 Desktop 연결 실패: {e}")
        return None

    # 활성 프로젝트/디자인 가져오기
    try:
        active_proj = desktop.active_project()
        if not active_proj:
            projs = desktop.project_list()
            if not projs:
                print("❌ 열린 프로젝트가 없습니다.")
                return None
            # 첫 프로젝트 활성화
            proj_name = projs[0]
            active_proj = desktop.open_project(proj_name)
        else:
            proj_name = active_proj.GetName()
    except Exception as e:
        print(f"❌ 프로젝트 정보 획득 실패: {e}")
        return None

    # 활성 디자인 확인 → Maxwell 2D인지 확인
    try:
        active_design = desktop.active_design()
        design_name = None
        design_type = None
        if active_design:
            design_name = active_design.GetName()
            design_type = active_design.GetDesignType()

        if not active_design or (design_type and "Maxwell" not in design_type) or (design_type and "2D" not in design_type):
            # 프로젝트의 디자인 목록에서 Maxwell 2D 탐색
            try:
                design_list = active_proj.GetTopDesignList()
            except Exception:
                design_list = []
            maxwell2d_name = None
            for dn in design_list:
                try:
                    d = active_proj.SetActiveDesign(dn)
                    # SetActiveDesign 반환이 None일 수 있으므로 다시 active_design 가져오기
                    ad = desktop.active_design()
                    if ad and "Maxwell" in ad.GetDesignType() and "2D" in ad.GetDesignType():
                        maxwell2d_name = ad.GetName()
                        break
                except Exception:
                    continue
            if not maxwell2d_name:
                print("❌ Maxwell 2D 디자인을 찾지 못했습니다.")
                return None
            design_name = maxwell2d_name
    except Exception as e:
        print(f"❌ 디자인 정보 획득 실패: {e}")
        return None

    # Maxwell2d 객체 attach
    try:
        m2d_attached = Maxwell2d(
            project=proj_name,
            design=design_name,
            version=aedt_version,
            new_desktop=False,
            non_graphical=non_graphical
        )
        print(f"✅ 연결 성공: Project='{proj_name}', Design='{design_name}'")
        return m2d_attached
    except Exception as e:
        print(f"❌ Maxwell2d attach 실패: {e}")
        return None
