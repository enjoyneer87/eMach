"""
AEDT Utilities Package

PyAEDT를 사용한 ANSYS Electronics Desktop 자동화 유틸리티 모음
"""

__version__ = "0.1.0"
__author__ = "KangDH"

from .connection import (
    getAedtProcessesDetailed,
    tryConnectToExistingDesktop,
    tryConnectWithPorts,
    getDesktopConnection,
    checkCurrentDesktopStatus,
    smartAedtConnector,
    quickConnect,
    forceNewSession,
)

from .maxwell import (
    getRunningMaxwell2d,
)

__all__ = [
    # Connection utilities
    "getAedtProcessesDetailed",
    "tryConnectToExistingDesktop",
    "tryConnectWithPorts",
    "getDesktopConnection",
    "checkCurrentDesktopStatus",
    "smartAedtConnector",
    "quickConnect",
    "forceNewSession",
    # Maxwell utilities
    "getRunningMaxwell2d",
]
